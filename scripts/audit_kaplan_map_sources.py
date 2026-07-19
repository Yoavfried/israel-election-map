from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from geobuf_properties import decode_geobuf_properties
from pipeline_common import (
    PROCESSED_DIR,
    RAW_DIR,
    ensure_dir,
    normalize_code,
    write_csv,
    write_json,
)


OUT_DIR = PROCESSED_DIR / "audits"
MANIFEST_DIR = PROCESSED_DIR / "manifest"
RAW_SOURCE_DIR = RAW_DIR / "kaplan_election_maps"
HISTORICAL_GAPS = OUT_DIR / "historical_assignment_gap_rows.csv"
MUNICIPALITY_AUDIT = OUT_DIR / "historical_municipality_assignment_audit.csv"
WIDE_DIR = PROCESSED_DIR / "normalized" / "ballot_votes_wide"
USER_AGENT = "Mozilla/5.0 israel-election-map source audit"

METRIC_FIELDS = {
    "eligible_voters": "r_\u05d1\u05d6\u05d1",
    "actual_voters": "r_\u05de\u05e6\u05d1\u05d9\u05e2\u05d9\u05dd",
    "valid_votes": "r_\u05db\u05e9\u05e8\u05d9\u05dd",
    "invalid_votes": "r_\u05e4\u05e1\u05d5\u05dc\u05d9\u05dd",
}
METRICS = list(METRIC_FIELDS)


@dataclass(frozen=True)
class Source:
    source_id: str
    election: str
    url: str
    filename: str
    encoding: str
    declared_grain: str

    @property
    def path(self) -> Path:
        return RAW_SOURCE_DIR / self.filename


SOURCES = [
    Source(
        "kaplan_k22_localities",
        "K22",
        "https://elections.kaplanopensource.co.il/setl2013_results_2019b.geojson",
        "k22_locality_results.geojson",
        "geojson",
        "locality_polygon",
    ),
    Source(
        "kaplan_k23_localities",
        "K23",
        "https://elections.kaplanopensource.co.il/2020/_6",
        "k23_locality_results.pbf",
        "geobuf",
        "locality_polygon",
    ),
    Source(
        "kaplan_k24_localities",
        "K24",
        "https://elections.kaplanopensource.co.il/2021/_7",
        "k24_locality_results.pbf",
        "geobuf",
        "locality_polygon",
    ),
    Source(
        "kaplan_k25_localities",
        "K25",
        "https://elections.kaplanopensource.co.il/2022/_7",
        "k25_locality_results.pbf",
        "geobuf",
        "locality_polygon",
    ),
    Source(
        "kaplan_k25_neighborhoods",
        "K25",
        "https://elections.kaplanopensource.co.il/2022/ynet/_9",
        "k25_neighborhood_results.pbf",
        "geobuf",
        "neighborhood_point",
    ),
]


def integer(value: Any) -> int:
    if value in (None, "") or pd.isna(value):
        return 0
    return int(round(float(value)))


def fetch_source(source: Source, overwrite: bool) -> dict[str, Any]:
    ensure_dir(source.path.parent)
    headers: dict[str, str] = {}
    status = "cached"
    if overwrite or not source.path.exists():
        request = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read()
            headers = {key.lower(): value for key, value in response.headers.items()}
        source.path.write_bytes(payload)
        status = "downloaded"
    payload = source.path.read_bytes()
    return {
        "source_id": source.source_id,
        "election": source.election,
        "url": source.url,
        "local_path": str(source.path.relative_to(RAW_DIR.parent)).replace("\\", "/"),
        "encoding": source.encoding,
        "declared_grain": source.declared_grain,
        "status": status,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "etag": headers.get("etag", ""),
        "last_modified": headers.get("last-modified", ""),
    }


def load_features(source: Source) -> list[dict[str, Any]]:
    if source.encoding == "geobuf":
        return decode_geobuf_properties(source.path.read_bytes())
    collection = json.loads(source.path.read_text(encoding="utf-8"))
    return [
        {
            "id": feature.get("id", ""),
            "geometry_type": (feature.get("geometry") or {}).get("type", ""),
            "properties": feature.get("properties") or {},
        }
        for feature in collection.get("features", [])
    ]


def source_records(features: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for feature in features:
        properties = feature["properties"]
        code = normalize_code(properties.get("SEMEL_YISHUV", ""))
        if not code:
            continue
        rows.append(
            {
                "locality_code": code,
                "geometry_type": feature["geometry_type"],
                "neighborhood_id": str(properties.get("neighborhood_id", "")),
                **{
                    metric: integer(properties.get(field))
                    for metric, field in METRIC_FIELDS.items()
                },
            }
        )
    return pd.DataFrame(rows)


def official_locality_totals(election: str) -> pd.DataFrame:
    path = WIDE_DIR / f"{election.lower()}_ballot_votes.csv"
    rows = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    rows = rows.loc[~rows["is_envelope"].str.lower().isin({"true", "1", "yes"})].copy()
    rows["locality_code"] = rows["source_locality_code"].map(normalize_code)
    rows = rows.loc[rows["locality_code"] != ""]
    for metric in METRICS:
        rows[metric] = pd.to_numeric(rows[metric], errors="coerce").fillna(0).astype(int)
    return rows.groupby("locality_code", as_index=False)[METRICS].sum()


def target_rows() -> pd.DataFrame:
    municipality = pd.read_csv(
        MUNICIPALITY_AUDIT, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    keys = set(zip(municipality["election"], municipality["locality_code"]))
    gaps = pd.read_csv(HISTORICAL_GAPS, dtype=str, encoding="utf-8-sig").fillna("")
    gaps = gaps.loc[gaps["election"].isin({"K22", "K23", "K24", "K25"})].copy()
    gaps["target_key"] = list(zip(gaps["election"], gaps["effective_locality_code"]))
    gaps = gaps.loc[gaps["target_key"].isin(keys)].copy()
    gaps["is_990"] = gaps["ballot_base"].eq("990")
    for metric in ["eligible_voters", "actual_voters"]:
        gaps[metric] = pd.to_numeric(gaps[metric], errors="coerce").fillna(0).astype(int)
    return gaps


def reconcile(
    source: Source,
    records: pd.DataFrame,
    official: pd.DataFrame,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    source_totals = records.groupby("locality_code", as_index=False)[METRICS].sum()
    merged = source_totals.merge(
        official,
        on="locality_code",
        how="outer",
        suffixes=("_source", "_official"),
        indicator=True,
    )
    for metric in METRICS:
        merged[f"{metric}_source"] = merged[f"{metric}_source"].fillna(0)
        merged[f"{metric}_official"] = merged[f"{metric}_official"].fillna(0)
    output: list[dict[str, Any]] = []
    exact_codes = 0
    turnout_exact_codes = 0
    mismatch_codes = 0
    for _, row in merged.iterrows():
        status = str(row["_merge"])
        exact = status == "both" and all(
            integer(row[f"{metric}_source"]) == integer(row[f"{metric}_official"])
            for metric in METRICS
        )
        turnout_exact = status == "both" and all(
            integer(row[f"{metric}_source"]) == integer(row[f"{metric}_official"])
            for metric in ["eligible_voters", "actual_voters"]
        )
        if exact:
            exact_codes += 1
        elif status == "both":
            mismatch_codes += 1
        if turnout_exact:
            turnout_exact_codes += 1
        output.append(
            {
                "source_id": source.source_id,
                "election": source.election,
                "locality_code": row["locality_code"],
                "coverage_status": status,
                "metrics_exact": exact,
                "turnout_metrics_exact": turnout_exact,
                **{
                    f"{metric}_source": integer(row[f"{metric}_source"])
                    for metric in METRICS
                },
                **{
                    f"{metric}_official": integer(row[f"{metric}_official"])
                    for metric in METRICS
                },
            }
        )
    return output, {
        "matched_codes": int((merged["_merge"] == "both").sum()),
        "exact_metric_codes": exact_codes,
        "turnout_exact_codes": turnout_exact_codes,
        "mismatched_codes": mismatch_codes,
        "source_only_codes": int((merged["_merge"] == "left_only").sum()),
        "official_only_codes": int((merged["_merge"] == "right_only").sum()),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    manifest: list[dict[str, Any]] = []
    for source in SOURCES:
        if args.fetch or args.overwrite:
            manifest.append(fetch_source(source, args.overwrite))
        elif not source.path.exists():
            raise FileNotFoundError(
                f"Missing {source.path}; run this script with --fetch first"
            )
        else:
            manifest.append(fetch_source(source, False))

    write_csv(
        MANIFEST_DIR / "kaplan_map_sources.csv",
        manifest,
        list(manifest[0]),
    )
    write_json(MANIFEST_DIR / "kaplan_map_sources.json", manifest)

    targets = target_rows()
    inventory: list[dict[str, Any]] = []
    reconciliation_rows: list[dict[str, Any]] = []
    target_coverage: list[dict[str, Any]] = []

    for source in SOURCES:
        features = load_features(source)
        records = source_records(features)
        official = official_locality_totals(source.election)
        reconciliation, counts = reconcile(source, records, official)
        reconciliation_rows.extend(reconciliation)
        reconciliation_by_code = {
            row["locality_code"]: row for row in reconciliation
        }

        property_keys = sorted(
            {
                key
                for feature in features
                for key in feature.get("properties", {}).keys()
            }
        )
        has_stat_area_id = any(
            any(hint in key.lower() for hint in ["stat", "ags", "\u05d0\u05d6\u05d5\u05e8"])
            for key in property_keys
        )
        source_codes = set(records["locality_code"])
        election_targets = targets.loc[targets["election"] == source.election]
        target_codes = set(election_targets["effective_locality_code"])
        target_codes_present = target_codes & source_codes
        duplicate_locality_features = len(records) - records["locality_code"].nunique()

        if has_stat_area_id or (
            source.declared_grain == "locality_polygon"
            and duplicate_locality_features != 0
        ):
            raise RuntimeError(
                f"{source.source_id} no longer matches the audited aggregate grain; "
                "review the changed schema before producing assignment candidates"
            )

        if source.declared_grain == "neighborhood_point":
            rejection_reason = (
                "The neighborhood layer is aggregate point data with no statistical-area "
                "identifier or ballot crosswalk. A point cannot prove which ballots contribute "
                "to a neighborhood or which statistical areas that neighborhood spans."
            )
        else:
            rejection_reason = (
                "The layer has exactly one feature per locality and no statistical-area "
                "identifier; it reproduces locality aggregates but cannot partition ballots "
                "among areas."
            )

        inventory.append(
            {
                "source_id": source.source_id,
                "election": source.election,
                "declared_grain": source.declared_grain,
                "feature_count": len(features),
                "features_without_locality_code": len(features) - len(records),
                "unique_locality_codes": records["locality_code"].nunique(),
                "duplicate_locality_features": duplicate_locality_features,
                "geometry_types": "|".join(sorted(set(records["geometry_type"]))),
                "has_stat_area_id": has_stat_area_id,
                "target_locality_codes": len(target_codes),
                "target_locality_codes_present": len(target_codes_present),
                "reconstruction_usable": False,
                "rejection_reason": rejection_reason,
                **counts,
            }
        )

        for locality_code, group in election_targets.groupby("effective_locality_code"):
            source_match = reconciliation_by_code[locality_code]
            target_coverage.append(
                {
                    "source_id": source.source_id,
                    "election": source.election,
                    "locality_code": locality_code,
                    "locality_name": group.iloc[0]["effective_locality_name"],
                    "source_features": int((records["locality_code"] == locality_code).sum()),
                    "source_grain": source.declared_grain,
                    "source_eligible_voters": source_match["eligible_voters_source"],
                    "official_eligible_voters": source_match["eligible_voters_official"],
                    "source_actual_voters": source_match["actual_voters_source"],
                    "official_actual_voters": source_match["actual_voters_official"],
                    "turnout_metrics_exact": source_match["turnout_metrics_exact"],
                    "rows_990": int(group["is_990"].sum()),
                    "voters_990": int(group.loc[group["is_990"], "actual_voters"].sum()),
                    "rows_non990": int((~group["is_990"]).sum()),
                    "voters_non990": int(
                        group.loc[~group["is_990"], "actual_voters"].sum()
                    ),
                    "candidate_possible": False,
                    "reason": rejection_reason,
                }
            )

    inventory_fields = list(inventory[0])
    write_csv(OUT_DIR / "kaplan_map_source_inventory.csv", inventory, inventory_fields)
    reconciliation_fields = list(reconciliation_rows[0])
    write_csv(
        OUT_DIR / "kaplan_map_source_reconciliation.csv",
        reconciliation_rows,
        reconciliation_fields,
    )
    target_fields = list(target_coverage[0])
    write_csv(
        OUT_DIR / "kaplan_map_source_target_coverage.csv",
        target_coverage,
        target_fields,
    )
    candidate_fields = [
        "election",
        "source_row_uid",
        "source_locality_code",
        "source_locality_name",
        "source_kalpi",
        "actual_voters",
        "candidate_stat_area_id",
        "source_id",
        "evidence_method",
        "proof_status",
    ]
    write_csv(
        OUT_DIR / "kaplan_map_assignment_candidates.csv",
        [],
        candidate_fields,
    )

    scope: dict[str, Any] = {}
    for election, group in targets.groupby("election"):
        scope[election] = {
            "rows_990": int(group["is_990"].sum()),
            "voters_990": int(group.loc[group["is_990"], "actual_voters"].sum()),
            "rows_non990": int((~group["is_990"]).sum()),
            "voters_non990": int(
                group.loc[~group["is_990"], "actual_voters"].sum()
            ),
        }
    summary = {
        "status": "complete_no_statistical_area_candidates",
        "source_count": len(SOURCES),
        "assignment_candidates": 0,
        "partition_searches_run": 0,
        "partition_searches_skipped_reason": (
            "No source passed the statistical-area grain gate."
        ),
        "target_scope": scope,
        "conclusion": (
            "The Kaplan locality layers are useful locality-total cross-checks, and the K25 extra "
            "layer contains neighborhood aggregate points. None contains "
            "ballot-to-statistical-area evidence for the remaining K22-K25 rows."
        ),
        "sources": inventory,
    }
    write_json(OUT_DIR / "kaplan_map_source_summary.json", summary)

    print(f"sources={len(SOURCES)}")
    print(f"assignment_candidates=0")
    for row in inventory:
        print(
            f"{row['source_id']}: features={row['feature_count']} "
            f"localities={row['unique_locality_codes']} "
            f"stat_id={row['has_stat_area_id']} usable={row['reconstruction_usable']}"
        )


if __name__ == "__main__":
    main()
