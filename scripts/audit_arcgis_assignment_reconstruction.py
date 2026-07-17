from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline_common import MANUAL_DIR, PROCESSED_DIR, RAW_DIR, ensure_dir, write_json


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENTS = PROCESSED_DIR / "assignments" / "historical_ballot_assignments.csv"
WIDE_DIR = PROCESSED_DIR / "normalized" / "ballot_votes_wide"
GEOGRAPHY_DIR = PROCESSED_DIR / "geographies"
OUT_DIR = PROCESSED_DIR / "audits"
REVIEWS = MANUAL_DIR / "arcgis_assignment_reconstruction_reviews.csv"

PARTITION_METRICS = ["eligible_voters", "actual_voters"]
SECONDARY_METRICS = ["valid_votes", "invalid_votes"]
METRICS = [*PARTITION_METRICS, *SECONDARY_METRICS]
SIGNATURE_FIELDS = ["ballot_count", *PARTITION_METRICS]
MAX_SEARCH_STATES = 1_000_000

CONFIG = {
    "K20": {
        "path": RAW_DIR / "arcgis" / "elections2015_statistical_areas.geojson",
        "area_id": "YeshuvStat",
        "locality_code": "SemelYeshuv",
        "stat_area": "StatZone",
        "ballot_count": "kalpiot_no",
        "eligible_voters": "\u05d1\u05d6\u05d1",
        "actual_voters": "\u05de\u05e6\u05d1\u05d9\u05e2\u05d9\u05dd",
        "valid_votes": "\u05db\u05e9\u05e8\u05d9\u05dd",
        "invalid_votes": "\u05e4\u05e1\u05d5\u05dc\u05d9\u05dd",
    },
    "K21": {
        "path": RAW_DIR / "arcgis" / "elections2019_statistical_areas.geojson",
        "area_id": "CityStat11",
        "locality_code": "CityCode",
        "stat_area": "StatZone11",
        "ballot_count": "NumKalpi",
        "eligible_voters": "Bazab",
        "actual_voters": "Voters",
        "valid_votes": "Ksherim",
        "invalid_votes": "Psulim",
    },
}


class SearchLimitExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class PartitionResult:
    solution_count: int
    area_indexes: tuple[int, ...] | None
    states_visited: int


def number(value: Any) -> int:
    if value in (None, "") or pd.isna(value):
        return 0
    return int(round(float(value)))


def bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def assignment_fingerprint(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(
        f"{row['source_row_uid']}|{row['candidate_stat_area_id']}"
        for row in sorted(rows, key=lambda item: item["source_row_uid"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def signature(row: pd.Series | dict[str, Any], include_count: bool = True) -> tuple[int, ...]:
    values = [number(row[field]) for field in PARTITION_METRICS]
    return ((number(row["ballot_count"]), *values) if include_count else (1, *values))


def solve_partition(
    pending_rows: pd.DataFrame, residual_areas: pd.DataFrame
) -> PartitionResult:
    ordered = pending_rows.sort_values(
        PARTITION_METRICS, ascending=[False] * len(PARTITION_METRICS), kind="stable"
    ).reset_index()
    row_signatures = [signature(row, include_count=False) for _, row in ordered.iterrows()]
    area_signatures = tuple(signature(row) for _, row in residual_areas.iterrows())

    if len(area_signatures) == 1:
        combined = tuple(
            [len(ordered)]
            + [sum(row[index] for row in row_signatures) for index in range(1, len(SIGNATURE_FIELDS))]
        )
        if combined == area_signatures[0]:
            return PartitionResult(1, tuple([0] * len(ordered)), 1)
        return PartitionResult(0, None, 1)

    states_visited = 0

    @lru_cache(maxsize=None)
    def search(
        row_index: int, remaining: tuple[tuple[int, ...], ...]
    ) -> tuple[int, tuple[int, ...] | None]:
        nonlocal states_visited
        states_visited += 1
        if states_visited > MAX_SEARCH_STATES:
            raise SearchLimitExceeded
        if row_index == len(row_signatures):
            return (1, ()) if all(not any(area) for area in remaining) else (0, None)

        row = row_signatures[row_index]
        solution_count = 0
        first_solution: tuple[int, ...] | None = None
        for area_index, area in enumerate(remaining):
            if any(row[value_index] > area[value_index] for value_index in range(len(row))):
                continue
            next_area = tuple(
                area[value_index] - row[value_index] for value_index in range(len(row))
            )
            next_remaining = list(remaining)
            next_remaining[area_index] = next_area
            child_count, child_solution = search(row_index + 1, tuple(next_remaining))
            if child_count and first_solution is None and child_solution is not None:
                first_solution = (area_index, *child_solution)
            solution_count = min(2, solution_count + child_count)
            if solution_count == 2:
                break
        return solution_count, first_solution

    count, sorted_solution = search(0, area_signatures)
    if sorted_solution is None:
        return PartitionResult(count, None, states_visited)

    by_original_index = {
        int(ordered.loc[position, "index"]): area_index
        for position, area_index in enumerate(sorted_solution)
    }
    solution = tuple(by_original_index[index] for index in pending_rows.index)
    return PartitionResult(count, solution, states_visited)


def load_arcgis_areas(election: str, config: dict[str, Any]) -> pd.DataFrame:
    collection = json.loads(Path(config["path"]).read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for feature in collection["features"]:
        properties = feature.get("properties") or {}
        if election == "K21":
            party_fields = [
                field for field in properties if re.fullmatch(r"f\d+", field)
            ]
        else:
            property_fields = list(properties)
            first_party = property_fields.index(config["invalid_votes"]) + 1
            last_party = property_fields.index("Shape__Area")
            party_fields = property_fields[first_party:last_party]
        rows.append(
            {
                "source_area_id": number(properties.get(config["area_id"])),
                "source_locality_code": number(properties.get(config["locality_code"])),
                "source_stat_area_number": number(properties.get(config["stat_area"])),
                "ballot_count": number(properties.get(config["ballot_count"])),
                **{
                    metric: number(properties.get(config[metric]))
                    for metric in METRICS
                },
                "party_vote_sum": sum(number(properties.get(field)) for field in party_fields),
            }
        )
    areas = pd.DataFrame(rows)
    if areas["source_area_id"].duplicated().any():
        duplicates = areas.loc[areas["source_area_id"].duplicated(), "source_area_id"].tolist()
        raise ValueError(f"{election} ArcGIS layer has duplicate area IDs: {duplicates[:10]}")
    return areas


def load_area_identity() -> tuple[dict[int, str], dict[str, dict[str, Any]]]:
    aliases = pd.read_csv(
        GEOGRAPHY_DIR / "statistical_areas_2011.aliases.csv",
        dtype=str,
        encoding="utf-8-sig",
    ).fillna("")
    source_to_canonical = {
        number(row["source_yishuv_stat"]): row["canonical_stat_area_id"]
        for _, row in aliases.iterrows()
    }
    metadata = pd.read_csv(
        GEOGRAPHY_DIR / "statistical_areas_2011.metadata.csv",
        dtype=str,
        encoding="utf-8-sig",
    ).fillna("")
    metadata_by_id = {
        row["stat_area_id"]: row.to_dict() for _, row in metadata.iterrows()
    }
    return source_to_canonical, metadata_by_id


def load_election_rows(election: str) -> pd.DataFrame:
    wide = pd.read_csv(
        WIDE_DIR / f"{election.lower()}_ballot_votes.csv",
        dtype=str,
        encoding="utf-8-sig",
    ).fillna("")
    assignments = pd.read_csv(
        ASSIGNMENTS, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    assignments = assignments[assignments["election"] == election].copy()
    columns = [
        "source_row_uid",
        "stat_area_id",
        "is_historical_stat_mapped",
        "historical_assignment_status",
        "historical_assignment_method",
        "historical_assignment_source",
    ]
    rows = wide.merge(assignments[columns], on="source_row_uid", how="left", validate="one_to_one")
    rows = rows[
        ~rows["is_envelope"].map(bool_value)
        & (rows["historical_assignment_status"] != "not_applicable_non_geographic")
    ].copy()
    rows["source_locality_code"] = rows["source_locality_code"].map(number)
    for metric in METRICS:
        rows[metric] = rows[metric].map(number)
    rows["is_mapped"] = rows["is_historical_stat_mapped"].map(bool_value)
    return rows


def total_signature(rows: pd.DataFrame) -> tuple[int, ...]:
    return (len(rows), *(int(rows[metric].sum()) for metric in PARTITION_METRICS))


def audit_election(
    election: str,
    config: dict[str, Any],
    source_to_canonical: dict[int, str],
    metadata_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = load_election_rows(election)
    arcgis = load_arcgis_areas(election, config)
    arcgis["stat_area_id"] = arcgis["source_area_id"].map(source_to_canonical)
    arcgis["stat_area_id"] = arcgis["stat_area_id"].fillna(
        arcgis["source_area_id"].map(lambda value: f"stat2011:{value}")
    )

    locality_reports: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for locality_code, locality_rows in rows.groupby("source_locality_code", sort=True):
        pending = locality_rows[
            locality_rows["historical_assignment_status"]
            == "no_direct_historical_assignment"
        ].copy().reset_index(drop=True)
        if pending.empty:
            continue
        locality_areas = arcgis[arcgis["source_locality_code"] == locality_code].copy()
        report: dict[str, Any] = {
            "election": election,
            "source_locality_code": locality_code,
            "source_locality_name": locality_rows["source_locality_name"].iloc[0],
            "pending_rows": len(pending),
            "pending_actual_voters": int(pending["actual_voters"].sum()),
            "arcgis_areas": len(locality_areas),
            "candidate_rows": 0,
            "solution_count_capped": 0,
            "search_states": 0,
            "arcgis_minus_official_valid_votes": 0,
            "arcgis_minus_official_invalid_votes": 0,
            "arcgis_party_sum_mismatch_areas": 0,
            "evidence_tier": "",
            "secondary_area_mismatch_count": 0,
            "secondary_area_differences": "",
            "status": "",
            "reason": "",
        }
        if locality_code <= 0:
            report.update(status="no_source_locality_code", reason="Official row has no locality code")
            locality_reports.append(report)
            continue
        if locality_areas.empty:
            report.update(status="no_arcgis_locality", reason="Locality is absent from the ArcGIS layer")
            locality_reports.append(report)
            continue

        arcgis_total = tuple(
            int(locality_areas[field].sum()) for field in SIGNATURE_FIELDS
        )
        official_total = total_signature(locality_rows)
        report["arcgis_minus_official_valid_votes"] = int(
            locality_areas["valid_votes"].sum() - locality_rows["valid_votes"].sum()
        )
        report["arcgis_minus_official_invalid_votes"] = int(
            locality_areas["invalid_votes"].sum() - locality_rows["invalid_votes"].sum()
        )
        report["arcgis_party_sum_mismatch_areas"] = int(
            (locality_areas["party_vote_sum"] != locality_areas["valid_votes"]).sum()
        )
        if arcgis_total != official_total:
            report.update(
                status="source_locality_total_mismatch",
                reason=f"ArcGIS {arcgis_total} != official {official_total}",
            )
            locality_reports.append(report)
            continue

        grouped_areas = (
            locality_areas.groupby("stat_area_id", as_index=False)
            .agg(
                source_area_ids=("source_area_id", lambda values: "|".join(str(value) for value in sorted(values))),
                source_stat_area_number=("source_stat_area_number", "first"),
                **{
                    field: (field, "sum")
                    for field in [*SIGNATURE_FIELDS, *SECONDARY_METRICS]
                },
            )
        )
        assigned = locality_rows[locality_rows["is_mapped"]].copy()
        missing_assigned_ids = sorted(set(assigned["stat_area_id"]) - set(grouped_areas["stat_area_id"]))
        if missing_assigned_ids:
            report.update(
                status="assigned_area_not_in_arcgis",
                reason="Assigned CBS areas absent from locality ArcGIS targets: " + "|".join(missing_assigned_ids),
            )
            locality_reports.append(report)
            continue

        residual = grouped_areas.copy()
        for area_index, area in residual.iterrows():
            assigned_area = assigned[assigned["stat_area_id"] == area["stat_area_id"]]
            residual.at[area_index, "ballot_count"] -= len(assigned_area)
            for metric in METRICS:
                residual.at[area_index, metric] -= int(assigned_area[metric].sum())
        if (residual[SIGNATURE_FIELDS] < 0).any().any():
            report.update(status="negative_residual", reason="Assigned rows exceed an ArcGIS area aggregate")
            locality_reports.append(report)
            continue
        residual = residual[
            residual[SIGNATURE_FIELDS].ne(0).any(axis=1)
        ].copy().reset_index(drop=True)
        residual_total = tuple(int(residual[field].sum()) for field in SIGNATURE_FIELDS)
        pending_total = total_signature(pending)
        if residual_total != pending_total:
            report.update(
                status="residual_total_mismatch",
                reason=f"Residual {residual_total} != pending {pending_total}",
            )
            locality_reports.append(report)
            continue
        if any(area_id not in metadata_by_id for area_id in residual["stat_area_id"]):
            missing = sorted(
                area_id for area_id in residual["stat_area_id"] if area_id not in metadata_by_id
            )
            report.update(
                status="target_geometry_missing",
                reason="Candidate target lacks a published 2011 geometry: " + "|".join(missing),
            )
            locality_reports.append(report)
            continue

        try:
            partition = solve_partition(pending, residual)
        except SearchLimitExceeded:
            report.update(status="search_limit", reason=f"Exceeded {MAX_SEARCH_STATES:,} partition states")
            locality_reports.append(report)
            continue
        report["solution_count_capped"] = partition.solution_count
        report["search_states"] = partition.states_visited
        if partition.solution_count == 0 or partition.area_indexes is None:
            report.update(status="no_exact_partition", reason="No ballot grouping exactly matches every residual area")
            locality_reports.append(report)
            continue
        if partition.solution_count > 1:
            report.update(status="ambiguous_exact_partition", reason="More than one exact ballot partition exists")
            locality_reports.append(report)
            continue

        secondary_differences: list[str] = []
        secondary_mismatch_areas = 0
        for area_index, area in residual.iterrows():
            candidate_indexes = [
                pending_index
                for pending_index, candidate_area_index in enumerate(partition.area_indexes)
                if candidate_area_index == area_index
            ]
            candidate_area = pending.iloc[candidate_indexes]
            deltas = {
                metric: int(area[metric]) - int(candidate_area[metric].sum())
                for metric in SECONDARY_METRICS
            }
            if any(deltas.values()):
                secondary_mismatch_areas += 1
                secondary_differences.append(
                    f"{area['stat_area_id']}:valid{deltas['valid_votes']:+d},"
                    f"invalid{deltas['invalid_votes']:+d}"
                )

        evidence_tier = "A" if not secondary_differences else "B"
        secondary_note = (
            "every residual area also reconciles valid and invalid votes"
            if evidence_tier == "A"
            else "secondary area audit differs: " + "|".join(secondary_differences)
        )
        report.update(
            status="unique_exact_partition",
            evidence_tier=evidence_tier,
            secondary_area_mismatch_count=secondary_mismatch_areas,
            secondary_area_differences="|".join(secondary_differences),
            reason=(
                "Unique exact partition of ballot count, eligible voters, and "
                f"actual voters; {secondary_note}"
            ),
            candidate_rows=len(pending),
        )
        for pending_index, area_index in enumerate(partition.area_indexes):
            row = pending.iloc[pending_index]
            area = residual.iloc[area_index]
            metadata = metadata_by_id[area["stat_area_id"]]
            candidates.append(
                {
                    "election": election,
                    "source_row_uid": row["source_row_uid"],
                    "source_locality_code": locality_code,
                    "source_locality_name": row["source_locality_name"],
                    "source_kalpi": row["source_kalpi"],
                    **{metric: int(row[metric]) for metric in METRICS},
                    "candidate_stat_area_id": area["stat_area_id"],
                    "candidate_yishuv_stat": number(metadata["yishuv_stat"]),
                    "candidate_stat_area_number": number(metadata["stat_area_number"]),
                    "arcgis_source_area_ids": area["source_area_ids"],
                    "proof_status": "unique_exact_partition",
                    "proof_metrics": "ballot_count|eligible_voters|actual_voters",
                    "evidence_tier": evidence_tier,
                    "assignment_applied": False,
                    "source": str(Path(config["path"]).relative_to(ROOT)).replace("\\", "/"),
                }
            )
        locality_reports.append(report)
    return locality_reports, candidates


def write_dataframe(frame: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def attach_reviews(
    report_frame: pd.DataFrame, candidate_frame: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not REVIEWS.exists():
        raise FileNotFoundError(f"Missing ArcGIS reconstruction review table: {REVIEWS}")
    reviews = pd.read_csv(REVIEWS, dtype=str, encoding="utf-8-sig").fillna("")
    key_fields = ["election", "source_locality_code"]
    if reviews.duplicated(key_fields).any():
        raise ValueError("ArcGIS reconstruction review table has duplicate locality decisions")
    reviews["source_locality_code"] = reviews["source_locality_code"].map(number)
    reviews = reviews.rename(
        columns={
            "candidate_rows": "review_candidate_rows",
            "candidate_actual_voters": "review_candidate_actual_voters",
        }
    )
    review_fields = [
        *key_fields,
        "decision",
        "review_candidate_rows",
        "review_candidate_actual_voters",
        "candidate_assignment_sha256",
        "reviewed_on",
        "review_basis",
    ]
    report_frame = report_frame.merge(
        reviews[review_fields], on=key_fields, how="left", validate="one_to_one"
    )
    candidate_frame = candidate_frame.merge(
        reviews[review_fields], on=key_fields, how="left", validate="many_to_one"
    )
    for frame in [report_frame, candidate_frame]:
        frame["decision"] = frame["decision"].fillna("pending")
        for field in ["reviewed_on", "review_basis"]:
            frame[field] = frame[field].fillna("")

    approved_reports = report_frame[report_frame["decision"] == "approved"]
    invalid = approved_reports[
        (approved_reports["status"] != "unique_exact_partition")
        | (approved_reports["evidence_tier"] != "A")
        | (approved_reports["secondary_area_mismatch_count"].map(number) != 0)
        | (
            approved_reports["candidate_rows"].map(number)
            != approved_reports["review_candidate_rows"].map(number)
        )
        | (
            approved_reports["pending_actual_voters"].map(number)
            != approved_reports["review_candidate_actual_voters"].map(number)
        )
    ]
    if not invalid.empty:
        keys = invalid[key_fields].astype(str).agg(":".join, axis=1).tolist()
        raise ValueError(f"Approved ArcGIS reconstruction evidence changed: {keys}")

    for _, report in approved_reports.iterrows():
        locality_candidates = candidate_frame[
            (candidate_frame["election"] == report["election"])
            & (
                candidate_frame["source_locality_code"]
                == report["source_locality_code"]
            )
        ].to_dict("records")
        if assignment_fingerprint(locality_candidates) != report[
            "candidate_assignment_sha256"
        ]:
            raise ValueError(
                "Approved ArcGIS reconstruction mapping changed: "
                f"{report['election']}:{report['source_locality_code']}"
            )

    report_frame = report_frame.rename(columns={"decision": "review_decision"})
    candidate_frame = candidate_frame.rename(columns={"decision": "review_decision"})
    candidate_frame["assignment_applied"] = (
        (candidate_frame["review_decision"] == "approved")
        & (candidate_frame["evidence_tier"] == "A")
    )
    return report_frame, candidate_frame


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Audit unique exact K20/K21 ballot partitions against ArcGIS area aggregates."
    )
    parser.parse_args()

    source_to_canonical, metadata_by_id = load_area_identity()
    all_reports: list[dict[str, Any]] = []
    all_candidates: list[dict[str, Any]] = []
    for election, config in CONFIG.items():
        reports, candidates = audit_election(
            election, config, source_to_canonical, metadata_by_id
        )
        all_reports.extend(reports)
        all_candidates.extend(candidates)

    report_frame = pd.DataFrame(all_reports)
    candidate_frame = pd.DataFrame(all_candidates)
    if not candidate_frame.empty and candidate_frame["source_row_uid"].duplicated().any():
        raise ValueError("ArcGIS reconstruction produced duplicate ballot candidates")
    report_frame, candidate_frame = attach_reviews(report_frame, candidate_frame)

    write_dataframe(
        report_frame,
        OUT_DIR / "arcgis_assignment_reconstruction_localities.csv",
    )
    write_dataframe(
        candidate_frame,
        OUT_DIR / "arcgis_assignment_reconstruction_candidates.csv",
    )

    summary: dict[str, Any] = {
        "status": "tier_a_approved_tier_b_review_only",
        "method": "unique exact partition after subtracting existing historical assignments",
        "matching_metrics": SIGNATURE_FIELDS,
        "secondary_audit_metrics_not_used_for_matching": SECONDARY_METRICS,
        "elections": {},
    }
    for election in CONFIG:
        reports = report_frame[report_frame["election"] == election]
        candidates = candidate_frame[candidate_frame["election"] == election]
        summary["elections"][election] = {
            "pending_localities_tested": len(reports),
            "pending_rows_tested": int(reports["pending_rows"].sum()),
            "unique_exact_localities": int((reports["status"] == "unique_exact_partition").sum()),
            "unique_exact_candidate_rows": len(candidates),
            "unique_exact_candidate_actual_voters": int(candidates["actual_voters"].sum()) if not candidates.empty else 0,
            "approved_localities": int((reports["review_decision"] == "approved").sum()),
            "approved_candidate_rows": int(candidates["assignment_applied"].sum()),
            "approved_candidate_actual_voters": int(
                candidates.loc[candidates["assignment_applied"], "actual_voters"].sum()
            ),
            "evidence_tiers": {
                str(tier): {
                    "localities": int((reports["evidence_tier"] == tier).sum()),
                    "candidate_rows": int((candidates["evidence_tier"] == tier).sum()),
                    "candidate_actual_voters": int(
                        candidates.loc[candidates["evidence_tier"] == tier, "actual_voters"].sum()
                    ),
                }
                for tier in ["A", "B"]
            },
            "status_counts": {
                str(status): int(count)
                for status, count in reports["status"].value_counts().sort_index().items()
            },
        }
    write_json(OUT_DIR / "arcgis_assignment_reconstruction_summary.json", summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
