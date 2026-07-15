from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from pipeline_common import PROCESSED_DIR, normalize_spaces, write_csv, write_json


WORK_UNITS = PROCESSED_DIR / "geocoding" / "geocoding_work_units.csv"
WORK_UNIT_ROWS = PROCESSED_DIR / "geocoding" / "geocoding_work_unit_rows.csv"
STAT_AREAS = PROCESSED_DIR / "geographies" / "statistical_areas_2022.geojson"
DEFAULT_INPUT = PROCESSED_DIR / "geocoding" / "photon_work_unit_results.csv"
DEFAULT_OUTPUT = PROCESSED_DIR / "geocoding" / "geocode_candidate_source_ags_validation.csv"
DEFAULT_SUMMARY = PROCESSED_DIR / "geocoding" / "geocode_candidate_source_ags_validation_summary.json"

FIELDS = [
    "geocoding_unit_id",
    "geocoding_scope",
    "geocoder",
    "geocode_status",
    "review_status",
    "longitude",
    "latitude",
    "source_ags_validation_status",
    "source_ags_validation_method",
    "expected_source_ags_values",
    "expected_source_locality_ags_pairs",
    "expected_source_locality_ags_pairs_in_layer",
    "expected_source_row_uids",
    "matched_locality_code",
    "matched_locality_name",
    "matched_stat_ags",
    "matched_stat_area_id",
    "matched_source_locality_ags_pair",
    "target_locality_codes",
    "target_locality_names",
    "geocoder_query",
    "matched_text",
    "geocode_notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def first_existing(columns: set[str], candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return ""


def normalize_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    try:
        number = float(text)
    except ValueError:
        digits = "".join(char for char in text if char.isdigit())
        return str(int(digits)) if digits else ""
    if number.is_integer():
        return str(int(number))
    digits = "".join(char for char in text if char.isdigit())
    return str(int(digits)) if digits else ""


def normalize_status(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def load_work_units(path: Path) -> dict[str, dict[str, str]]:
    return {row["geocoding_unit_id"]: row for row in read_csv(path)}


def load_source_ags_rows(path: Path) -> dict[str, list[dict[str, str]]]:
    by_unit: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(path):
        unit_id = row.get("geocoding_unit_id", "")
        source_ags = normalize_code(row.get("source_ags", ""))
        source_locality_code = normalize_code(row.get("source_locality_code", ""))
        if not unit_id or not source_ags:
            continue
        by_unit[unit_id].append(
            {
                "source_row_uid": row.get("source_row_uid", ""),
                "election": row.get("election", ""),
                "source_locality_code": source_locality_code,
                "source_locality_name": row.get("source_locality_name", ""),
                "source_ags": source_ags,
            }
        )
    return by_unit


def join_sorted(values: set[str]) -> str:
    return "|".join(sorted(value for value in values if value))


def expected_context(source_rows: list[dict[str, str]]) -> dict[str, str]:
    pairs = {
        f"{row['source_locality_code']}:{row['source_ags']}"
        for row in source_rows
        if row.get("source_locality_code") and row.get("source_ags")
    }
    return {
        "expected_source_ags_values": join_sorted({row["source_ags"] for row in source_rows}),
        "expected_source_locality_ags_pairs": join_sorted(pairs),
        "expected_source_row_uids": join_sorted({row["source_row_uid"] for row in source_rows}),
    }


def load_candidates(path: Path) -> tuple[dict[str, dict[str, Any]], gpd.GeoDataFrame]:
    if not path.exists():
        return {}, gpd.GeoDataFrame(columns=["geocoding_unit_id", "geometry"], geometry="geometry", crs="EPSG:4326")

    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    if raw.empty:
        return {}, gpd.GeoDataFrame(columns=["geocoding_unit_id", "geometry"], geometry="geometry", crs="EPSG:4326")

    columns = set(raw.columns)
    key_col = first_existing(columns, ["geocoding_unit_id", "geocode_key", "source_row_uid", "address_uid"])
    lon_col = first_existing(columns, ["longitude", "lon", "lng", "x_wgs84", "wgs84_lon"])
    lat_col = first_existing(columns, ["latitude", "lat", "y_wgs84", "wgs84_lat"])
    if not key_col:
        raise ValueError(f"{path} must include geocoding_unit_id, geocode_key, source_row_uid, or address_uid")
    if not lon_col or not lat_col:
        raise ValueError(f"{path} must include WGS84 longitude/latitude columns")

    raw["geocoding_unit_id"] = raw[key_col]
    candidate_by_key = {str(row["geocoding_unit_id"]): row for row in raw.to_dict("records")}

    raw["_lon"] = pd.to_numeric(raw[lon_col], errors="coerce")
    raw["_lat"] = pd.to_numeric(raw[lat_col], errors="coerce")
    usable = raw.dropna(subset=["_lon", "_lat"]).copy()
    points = gpd.GeoDataFrame(usable, geometry=gpd.points_from_xy(usable["_lon"], usable["_lat"]), crs="EPSG:4326")
    return candidate_by_key, points


def load_stat_areas(path: Path, locality_code_column: str, ags_column: str) -> gpd.GeoDataFrame:
    stats = gpd.read_file(path)
    if stats.crs is None:
        stats = stats.set_crs("EPSG:4326")
    elif str(stats.crs).upper() not in {"EPSG:4326", "OGC:CRS84"}:
        stats = stats.to_crs("EPSG:4326")

    columns = set(stats.columns)
    if locality_code_column not in columns:
        raise ValueError(f"{path} does not include locality code column {locality_code_column!r}")
    if ags_column not in columns:
        raise ValueError(f"{path} does not include AGS/stat column {ags_column!r}")

    name_column = first_existing(columns, ["locality_name_he", "SHEM_YISHUV", "locality_name", "name"])
    stat_area_id_column = first_existing(columns, ["stat_area_id", "yishuv_stat_2022", "YISHUV_STAT_2022", ags_column])

    keep_columns = [locality_code_column, ags_column, stat_area_id_column, "geometry"]
    if name_column:
        keep_columns.append(name_column)
    stats = stats[list(dict.fromkeys(keep_columns))].copy()
    stats["matched_locality_code_norm"] = stats[locality_code_column].map(normalize_code)
    stats["matched_stat_ags_norm"] = stats[ags_column].map(normalize_code)
    stats["matched_source_locality_ags_pair"] = (
        stats["matched_locality_code_norm"] + ":" + stats["matched_stat_ags_norm"]
    )
    stats["matched_locality_name"] = stats[name_column] if name_column else ""
    stats["matched_stat_area_id"] = stats[stat_area_id_column].astype(str)
    return stats


def spatial_join_points(points: gpd.GeoDataFrame, stats: gpd.GeoDataFrame) -> dict[str, dict[str, Any]]:
    if points.empty:
        return {}

    joined = gpd.sjoin(points, stats, how="left", predicate="within")
    missing_mask = joined["matched_stat_ags_norm"].isna()
    if missing_mask.any():
        missing_points = points[points["geocoding_unit_id"].isin(joined.loc[missing_mask, "geocoding_unit_id"])]
        fallback = gpd.sjoin(missing_points, stats, how="left", predicate="intersects")
        joined = pd.concat([joined.loc[~missing_mask], fallback], ignore_index=True)

    matched: dict[str, dict[str, Any]] = {}
    for _, row in joined.iterrows():
        key = str(row["geocoding_unit_id"])
        if key in matched:
            continue
        if pd.isna(row.get("matched_stat_ags_norm")):
            continue
        matched[key] = row.to_dict()
    return matched


def base_output(
    key: str,
    candidate: dict[str, Any],
    work_unit: dict[str, str],
    source_rows: list[dict[str, str]],
    status: str,
    method: str,
    notes: str = "",
) -> dict[str, Any]:
    context = expected_context(source_rows)
    return {
        "geocoding_unit_id": key,
        "geocoding_scope": work_unit.get("geocoding_scope", ""),
        "geocoder": candidate.get("geocoder", ""),
        "geocode_status": candidate.get("geocode_status", candidate.get("status", "")),
        "review_status": candidate.get("review_status", ""),
        "longitude": candidate.get("longitude", candidate.get("lon", candidate.get("lng", ""))),
        "latitude": candidate.get("latitude", candidate.get("lat", "")),
        "source_ags_validation_status": status,
        "source_ags_validation_method": method,
        "expected_source_ags_values": context["expected_source_ags_values"],
        "expected_source_locality_ags_pairs": context["expected_source_locality_ags_pairs"],
        "expected_source_locality_ags_pairs_in_layer": "",
        "expected_source_row_uids": context["expected_source_row_uids"],
        "matched_locality_code": "",
        "matched_locality_name": "",
        "matched_stat_ags": "",
        "matched_stat_area_id": "",
        "matched_source_locality_ags_pair": "",
        "target_locality_codes": work_unit.get("target_locality_codes", ""),
        "target_locality_names": work_unit.get("target_locality_names", ""),
        "geocoder_query": candidate.get("geocoder_query", work_unit.get("geocoder_query", "")),
        "matched_text": candidate.get("matched_text", ""),
        "geocode_notes": notes,
    }


def validate(
    work_units: dict[str, dict[str, str]],
    source_ags_by_unit: dict[str, list[dict[str, str]]],
    candidates_by_key: dict[str, dict[str, Any]],
    spatial_matches: dict[str, dict[str, Any]],
    stat_pairs: set[str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for key, work_unit in work_units.items():
        source_rows = source_ags_by_unit.get(key, [])
        candidate = candidates_by_key.get(key, {"geocoding_unit_id": key})
        if not source_rows:
            output.append(base_output(key, candidate, work_unit, source_rows, "no_source_ags", "not_checked"))
            continue

        status = normalize_status(candidate.get("geocode_status", candidate.get("status", "")))
        if status in {"", "no_match", "not_found", "failed", "failure", "error"}:
            output.append(base_output(key, candidate, work_unit, source_rows, "candidate_not_matched", "not_checked"))
            continue

        expected_pairs = {
            f"{row['source_locality_code']}:{row['source_ags']}"
            for row in source_rows
            if row.get("source_locality_code") and row.get("source_ags")
        }
        expected_pairs_in_layer = expected_pairs & stat_pairs
        match = spatial_matches.get(key)
        is_multi_source_ags = len(expected_pairs) > 1
        if not match:
            status_name = "multi_source_ags_candidate_outside_stat_area" if is_multi_source_ags else "candidate_outside_stat_area"
            row = base_output(key, candidate, work_unit, source_rows, status_name, "point_in_stat_area_layer")
            row["expected_source_locality_ags_pairs_in_layer"] = join_sorted(expected_pairs_in_layer)
            output.append(row)
            continue

        matched_pair = str(match.get("matched_source_locality_ags_pair", ""))
        notes = ""
        if not expected_pairs:
            validation_status = "source_ags_missing_locality_pair"
        elif is_multi_source_ags:
            notes = "multiple source AGS values share this address; do not treat as a single building-AGS pass/fail"
            if not expected_pairs_in_layer:
                validation_status = "multi_source_ags_not_in_stat_layer"
            elif matched_pair in expected_pairs:
                validation_status = "multi_source_ags_candidate_inside_one_expected_ags"
            else:
                validation_status = "multi_source_ags_candidate_outside_expected_ags"
        elif not expected_pairs_in_layer:
            validation_status = "single_source_ags_not_in_stat_layer"
        elif matched_pair in expected_pairs:
            validation_status = "single_source_ags_candidate_inside_expected_ags"
        else:
            validation_status = "single_source_ags_candidate_outside_expected_ags"

        row = base_output(key, candidate, work_unit, source_rows, validation_status, "point_in_stat_area_layer", notes)
        row.update(
            {
                "expected_source_locality_ags_pairs_in_layer": join_sorted(expected_pairs_in_layer),
                "matched_locality_code": match.get("matched_locality_code_norm", ""),
                "matched_locality_name": match.get("matched_locality_name", ""),
                "matched_stat_ags": match.get("matched_stat_ags_norm", ""),
                "matched_stat_area_id": match.get("matched_stat_area_id", ""),
                "matched_source_locality_ags_pair": matched_pair,
            }
        )
        output.append(row)
    return output


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--work-units", type=Path, default=WORK_UNITS)
    parser.add_argument("--work-unit-rows", type=Path, default=WORK_UNIT_ROWS)
    parser.add_argument("--stat-areas", type=Path, default=STAT_AREAS)
    parser.add_argument("--stat-locality-code-column", default="locality_code")
    parser.add_argument("--stat-ags-column", default="stat_2022")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    work_units = load_work_units(args.work_units)
    source_ags_by_unit = load_source_ags_rows(args.work_unit_rows)
    candidates_by_key, candidate_points = load_candidates(args.candidates)
    stat_areas = load_stat_areas(args.stat_areas, args.stat_locality_code_column, args.stat_ags_column)
    stat_pairs = set(stat_areas["matched_source_locality_ags_pair"])
    spatial_matches = spatial_join_points(candidate_points, stat_areas)
    output = validate(work_units, source_ags_by_unit, candidates_by_key, spatial_matches, stat_pairs)
    write_csv(args.output, output, FIELDS)

    counts = Counter(row["source_ags_validation_status"] for row in output)
    by_scope = Counter((row["geocoding_scope"], row["source_ags_validation_status"]) for row in output)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_file": str(args.candidates),
        "work_unit_file": str(args.work_units),
        "work_unit_rows_file": str(args.work_unit_rows),
        "stat_area_file": str(args.stat_areas),
        "stat_locality_code_column": args.stat_locality_code_column,
        "stat_ags_column": args.stat_ags_column,
        "rows": len(output),
        "units_with_source_ags": sum(1 for rows in source_ags_by_unit.values() if rows),
        "validation_status_counts": dict(sorted(counts.items())),
        "by_scope_status_counts": {
            f"{scope}|{status}": count
            for (scope, status), count in sorted(by_scope.items())
        },
    }
    write_json(args.summary, summary)

    print(f"rows={len(output)}")
    print(f"output={args.output}")
    for status, count in sorted(counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
