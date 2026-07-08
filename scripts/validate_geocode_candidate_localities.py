from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from pipeline_common import PROCESSED_DIR, write_csv, write_json


WORK_UNITS = PROCESSED_DIR / "geocoding" / "geocoding_work_units.csv"
LOCALITIES = PROCESSED_DIR / "geographies" / "localities_2022_dissolved.geojson"
DEFAULT_INPUT = PROCESSED_DIR / "geocoding" / "photon_work_unit_results.csv"
DEFAULT_OUTPUT = PROCESSED_DIR / "geocoding" / "geocode_candidate_locality_validation.csv"
DEFAULT_SUMMARY = PROCESSED_DIR / "geocoding" / "geocode_candidate_locality_validation_summary.json"

FIELDS = [
    "geocoding_unit_id",
    "geocoder",
    "geocode_status",
    "review_status",
    "longitude",
    "latitude",
    "target_locality_codes",
    "target_locality_names",
    "validation_status",
    "validation_method",
    "matched_locality_code",
    "matched_locality_name",
    "matched_locality_id",
    "expected_locality_codes_seen",
    "expected_locality_codes_missing",
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


def normalize_status(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def normalize_locality_code(value: Any) -> str:
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


def split_codes(value: Any) -> list[str]:
    codes: list[str] = []
    for part in str(value or "").split("|"):
        code = normalize_locality_code(part)
        if code and code not in codes:
            codes.append(code)
    return codes


def load_work_units(path: Path) -> dict[str, dict[str, str]]:
    return {row["geocoding_unit_id"]: row for row in read_csv(path)}


def load_candidate_points(path: Path) -> gpd.GeoDataFrame:
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    if raw.empty:
        return gpd.GeoDataFrame(columns=["geocoding_unit_id", "geometry"], geometry="geometry", crs="EPSG:4326")

    columns = set(raw.columns)
    key_col = first_existing(columns, ["geocoding_unit_id", "geocode_key", "source_row_uid", "address_uid"])
    lon_col = first_existing(columns, ["longitude", "lon", "lng", "x_wgs84", "wgs84_lon"])
    lat_col = first_existing(columns, ["latitude", "lat", "y_wgs84", "wgs84_lat"])
    if not key_col:
        raise ValueError(f"{path} must include geocoding_unit_id, geocode_key, source_row_uid, or address_uid")
    if not lon_col or not lat_col:
        raise ValueError(f"{path} must include WGS84 longitude/latitude columns")

    raw["_lon"] = pd.to_numeric(raw[lon_col], errors="coerce")
    raw["_lat"] = pd.to_numeric(raw[lat_col], errors="coerce")
    raw["geocoding_unit_id"] = raw[key_col]
    usable = raw.dropna(subset=["_lon", "_lat"]).copy()
    return gpd.GeoDataFrame(usable, geometry=gpd.points_from_xy(usable["_lon"], usable["_lat"]), crs="EPSG:4326")


def load_localities(path: Path) -> gpd.GeoDataFrame:
    localities = gpd.read_file(path)
    if localities.crs is None:
        localities = localities.set_crs("EPSG:4326")
    elif str(localities.crs).upper() not in {"EPSG:4326", "OGC:CRS84"}:
        localities = localities.to_crs("EPSG:4326")
    localities = localities[["locality_id", "locality_code", "locality_name_he", "geometry"]].copy()
    localities["locality_code_norm"] = localities["locality_code"].map(normalize_locality_code)
    return localities


def base_output(candidate: dict[str, Any], work_unit: dict[str, str], status: str, method: str, notes: str = "") -> dict[str, Any]:
    return {
        "geocoding_unit_id": candidate.get("geocoding_unit_id", ""),
        "geocoder": candidate.get("geocoder", ""),
        "geocode_status": candidate.get("geocode_status", candidate.get("status", "")),
        "review_status": candidate.get("review_status", ""),
        "longitude": candidate.get("longitude", candidate.get("lon", candidate.get("lng", ""))),
        "latitude": candidate.get("latitude", candidate.get("lat", "")),
        "target_locality_codes": work_unit.get("target_locality_codes", ""),
        "target_locality_names": work_unit.get("target_locality_names", ""),
        "validation_status": status,
        "validation_method": method,
        "matched_locality_code": "",
        "matched_locality_name": "",
        "matched_locality_id": "",
        "expected_locality_codes_seen": "",
        "expected_locality_codes_missing": "|".join(split_codes(work_unit.get("target_locality_codes", ""))),
        "geocoder_query": candidate.get("geocoder_query", work_unit.get("geocoder_query", "")),
        "matched_text": candidate.get("matched_text", ""),
        "geocode_notes": notes,
    }


def validate_candidates(candidates: gpd.GeoDataFrame, localities: gpd.GeoDataFrame, work_units: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    candidate_records = candidates.drop(columns="geometry").to_dict("records") if not candidates.empty else []
    candidate_by_key = {str(row["geocoding_unit_id"]): row for row in candidate_records}

    output: list[dict[str, Any]] = []
    if candidates.empty:
        for key, work_unit in work_units.items():
            output.append(base_output({"geocoding_unit_id": key}, work_unit, "no_candidate_coordinates", "not_checked"))
        return output

    joined = gpd.sjoin(candidates, localities, how="left", predicate="within")
    missing_mask = joined["locality_code"].isna()
    if missing_mask.any():
        missing_points = candidates[candidates["geocoding_unit_id"].isin(joined.loc[missing_mask, "geocoding_unit_id"])]
        fallback = gpd.sjoin(missing_points, localities, how="left", predicate="intersects")
        joined = pd.concat([joined.loc[~missing_mask], fallback], ignore_index=True)

    joined_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for _, row in joined.iterrows():
        joined_by_key[str(row["geocoding_unit_id"])].append(row.to_dict())

    for key, work_unit in work_units.items():
        candidate = candidate_by_key.get(key, {"geocoding_unit_id": key})
        status = normalize_status(candidate.get("geocode_status", candidate.get("status", "")))
        if status in {"", "no_match", "not_found", "failed", "failure", "error"}:
            output.append(base_output(candidate, work_unit, "candidate_not_matched", "not_checked"))
            continue

        expected_codes = split_codes(work_unit.get("target_locality_codes", ""))
        if not expected_codes:
            output.append(base_output(candidate, work_unit, "expected_locality_missing", "not_checked"))
            continue

        matches = joined_by_key.get(key, [])
        matched_codes = [normalize_locality_code(row.get("locality_code", "")) for row in matches if normalize_locality_code(row.get("locality_code", ""))]
        seen = [code for code in expected_codes if code in matched_codes]
        missing = [code for code in expected_codes if code not in matched_codes]

        if seen:
            selected = next(row for row in matches if normalize_locality_code(row.get("locality_code", "")) in seen)
            row = base_output(candidate, work_unit, "inside_expected_locality", "point_in_dissolved_2022_locality")
            row.update(
                {
                    "matched_locality_code": normalize_locality_code(selected.get("locality_code", "")),
                    "matched_locality_name": selected.get("locality_name_he", ""),
                    "matched_locality_id": selected.get("locality_id", ""),
                    "expected_locality_codes_seen": "|".join(seen),
                    "expected_locality_codes_missing": "|".join(missing),
                }
            )
            output.append(row)
            continue

        if matched_codes:
            selected = matches[0]
            row = base_output(candidate, work_unit, "outside_expected_locality", "point_in_other_2022_locality")
            row.update(
                {
                    "matched_locality_code": normalize_locality_code(selected.get("locality_code", "")),
                    "matched_locality_name": selected.get("locality_name_he", ""),
                    "matched_locality_id": selected.get("locality_id", ""),
                    "expected_locality_codes_missing": "|".join(missing),
                }
            )
            output.append(row)
        else:
            output.append(base_output(candidate, work_unit, "outside_all_localities", "point_not_in_dissolved_2022_locality"))

    return output


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--work-units", type=Path, default=WORK_UNITS)
    parser.add_argument("--localities", type=Path, default=LOCALITIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    work_units = load_work_units(args.work_units)
    candidates = load_candidate_points(args.candidates)
    localities = load_localities(args.localities)
    output = validate_candidates(candidates, localities, work_units)
    write_csv(args.output, output, FIELDS)

    counts = Counter(row["validation_status"] for row in output)
    by_geocoder = Counter((row["geocoder"], row["validation_status"]) for row in output)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_file": str(args.candidates),
        "work_unit_file": str(args.work_units),
        "locality_file": str(args.localities),
        "rows": len(output),
        "validation_status_counts": dict(sorted(counts.items())),
        "by_geocoder_status_counts": {f"{geocoder}|{status}": count for (geocoder, status), count in sorted(by_geocoder.items())},
    }
    write_json(args.summary, summary)

    print(f"rows={len(output)}")
    print(f"output={args.output}")
    for status, count in sorted(counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
