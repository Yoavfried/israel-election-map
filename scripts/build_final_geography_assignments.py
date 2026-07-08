from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from pipeline_common import PROCESSED_DIR, int_value, write_csv, write_json


ASSIGNMENT_PLAN = PROCESSED_DIR / "assignments" / "ballot_assignment_plan.csv"
GEOCODING_INPUT = PROCESSED_DIR / "geocoding" / "geocoding_input.csv"
GEOCODING_WORK_UNIT_ROWS = PROCESSED_DIR / "geocoding" / "geocoding_work_unit_rows.csv"
STAT_AREAS = PROCESSED_DIR / "geographies" / "statistical_areas_2022.geojson"
STAT_AREA_METADATA = PROCESSED_DIR / "geographies" / "statistical_areas_2022.metadata.csv"
OUT_DIR = PROCESSED_DIR / "assignments"



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


def split_locality_codes(value: Any) -> list[str]:
    codes: list[str] = []
    for part in str(value or "").split("|"):
        code = normalize_locality_code(part)
        if code and code not in codes:
            codes.append(code)
    return codes


def point_matches_expected_locality(row: dict[str, str], point: dict[str, Any]) -> bool:
    expected = split_locality_codes(row.get("target_locality_code", ""))
    if not expected:
        return True
    return normalize_locality_code(point.get("locality_code", "")) in expected


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


def normalize_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def normalize_status(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def load_stat_metadata() -> dict[str, dict[str, str]]:
    return {row["stat_area_id"]: row for row in read_csv(STAT_AREA_METADATA)}


def load_geocoding_input() -> dict[str, dict[str, str]]:
    return {row["source_row_uid"]: row for row in read_csv(GEOCODING_INPUT)}


def load_geocoding_unit_index() -> dict[str, str]:
    rows = read_csv(GEOCODING_WORK_UNIT_ROWS)
    return {row["source_row_uid"]: row["geocoding_unit_id"] for row in rows if row.get("geocoding_unit_id")}


def geocode_is_usable(row: pd.Series) -> bool:
    rejected_values = {
        "reject",
        "rejected",
        "false",
        "failed",
        "failure",
        "no_match",
        "not_found",
        "ambiguous",
        "needs_review",
        "needs_manual_review",
        "pending",
        "unreviewed",
    }
    for column in ["review_status", "geocode_status", "status"]:
        if column in row.index and normalize_status(row[column]) in rejected_values:
            return False
    return True


def load_geocoded_points(path: Path) -> tuple[gpd.GeoDataFrame, set[str]]:
    if not path.exists():
        return gpd.GeoDataFrame(columns=["geocode_key", "geometry"], geometry="geometry", crs="EPSG:4326"), set()

    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    if raw.empty:
        return gpd.GeoDataFrame(columns=["geocode_key", "geometry"], geometry="geometry", crs="EPSG:4326"), set()

    columns = set(raw.columns)
    key_col = first_existing(columns, ["geocode_key", "source_row_uid", "address_uid"])
    if not key_col:
        raise ValueError(f"{path} must include geocode_key or source_row_uid")

    lon_col = first_existing(columns, ["longitude", "lon", "lng", "x_wgs84", "wgs84_lon"])
    lat_col = first_existing(columns, ["latitude", "lat", "y_wgs84", "wgs84_lat"])
    x_col = first_existing(columns, ["x_2039", "itm_x", "israel_tm_x", "x"])
    y_col = first_existing(columns, ["y_2039", "itm_y", "israel_tm_y", "y"])

    usable = raw[raw.apply(geocode_is_usable, axis=1)].copy()
    if lon_col and lat_col:
        usable["_x"] = pd.to_numeric(usable[lon_col], errors="coerce")
        usable["_y"] = pd.to_numeric(usable[lat_col], errors="coerce")
        crs = "EPSG:4326"
    elif x_col and y_col:
        usable["_x"] = pd.to_numeric(usable[x_col], errors="coerce")
        usable["_y"] = pd.to_numeric(usable[y_col], errors="coerce")
        crs_values = sorted({value for value in usable.get("coordinate_crs", pd.Series(dtype=str)).astype(str) if value})
        crs = crs_values[0] if len(crs_values) == 1 else "EPSG:2039"
    else:
        raise ValueError(f"{path} must include WGS84 lon/lat columns or projected x/y columns")

    usable = usable.dropna(subset=["_x", "_y"]).copy()
    usable["geocode_key"] = usable[key_col]
    geocode_keys = set(usable["geocode_key"])
    if usable.empty:
        return gpd.GeoDataFrame(columns=["geocode_key", "geometry"], geometry="geometry", crs="EPSG:4326"), geocode_keys

    points = gpd.GeoDataFrame(
        usable,
        geometry=gpd.points_from_xy(usable["_x"], usable["_y"]),
        crs=crs,
    )
    if str(points.crs).upper() not in {"EPSG:4326", "OGC:CRS84"}:
        points = points.to_crs("EPSG:4326")
    return points, geocode_keys


def load_stat_areas() -> gpd.GeoDataFrame:
    stats = gpd.read_file(STAT_AREAS)
    if stats.crs is None:
        stats = stats.set_crs("EPSG:4326")
    elif str(stats.crs).upper() not in {"EPSG:4326", "OGC:CRS84"}:
        stats = stats.to_crs("EPSG:4326")
    return stats[
        [
            "stat_area_id",
            "yishuv_stat_2022",
            "locality_id",
            "locality_code",
            "locality_name_he",
            "stat_2022",
            "geometry",
        ]
    ].copy()


def spatially_assign_points(points: gpd.GeoDataFrame, stats: gpd.GeoDataFrame) -> tuple[dict[str, dict], set[str]]:
    if points.empty:
        return {}, set()

    joined = gpd.sjoin(points, stats, how="left", predicate="within")
    missing_mask = joined["stat_area_id"].isna()
    if missing_mask.any():
        missing_points = points[points["geocode_key"].isin(joined.loc[missing_mask, "geocode_key"])]
        fallback = gpd.sjoin(missing_points, stats, how="left", predicate="intersects")
        joined = pd.concat([joined.loc[~missing_mask], fallback], ignore_index=True)

    assigned: dict[str, dict] = {}
    outside: set[str] = set()
    for _, row in joined.iterrows():
        key = str(row["geocode_key"])
        if key in assigned:
            continue
        if pd.isna(row.get("stat_area_id")):
            outside.add(key)
            continue
        assigned[key] = {
            "geocode_key": key,
            "geocode_lon": float(row.geometry.x),
            "geocode_lat": float(row.geometry.y),
            "stat_area_id": row["stat_area_id"],
            "yishuv_stat_2022": row["yishuv_stat_2022"],
            "stat_2022": row["stat_2022"],
            "locality_id": row["locality_id"],
            "locality_code": row["locality_code"],
            "locality_name_he": row["locality_name_he"],
            "geocoder": row.get("geocoder", ""),
            "geocode_status": row.get("geocode_status", row.get("status", "")),
            "geocode_confidence": row.get("geocode_confidence", row.get("confidence", "")),
            "review_status": row.get("review_status", ""),
        }
    outside.update(set(points["geocode_key"]) - set(assigned))
    return assigned, outside


def stat_assignment(row: dict[str, str], stat: dict[str, str], status: str, method: str) -> dict[str, Any]:
    return {
        **base_output(row),
        "geography_assignment_status": status,
        "geography_type": "statistical_area",
        "geography_id": stat["stat_area_id"],
        "stat_area_id": stat["stat_area_id"],
        "stat_area_yishuv_stat_2022": stat["yishuv_stat_2022"],
        "stat_area_stat_2022": stat["stat_2022"],
        "locality_id": stat["locality_id"],
        "locality_code": stat["locality_code"],
        "locality_name": stat["locality_name_he"],
        "custom_geography_id": "",
        "is_mapped": True,
        "is_geographic": True,
        "final_assignment_method": method,
        "final_assignment_source": row["assignment_source"],
        "geocode_key": "",
        "geocode_lon": "",
        "geocode_lat": "",
        "geocoder": "",
        "geocode_status": "",
        "geocode_confidence": "",
        "address_match_status": "",
        "address_query": "",
        "unresolved_reason": "",
    }


def base_output(row: dict[str, str]) -> dict[str, Any]:
    return {
        "source_row_uid": row["source_row_uid"],
        "election": row["election"],
        "election_number": row["election_number"],
        "source_row_id": row["source_row_id"],
        "source_locality_code": row["source_locality_code"],
        "source_locality_name": row["source_locality_name"],
        "source_kalpi": row["source_kalpi"],
        "eligible_voters": row["eligible_voters"],
        "actual_voters": row["actual_voters"],
        "assignment_method": row["assignment_method"],
        "assignment_source": row["assignment_source"],
    }


def unmapped(row: dict[str, str], status: str, reason: str, geocoding_row: dict[str, str] | None = None) -> dict[str, Any]:
    geocoding_row = geocoding_row or {}
    return {
        **base_output(row),
        "geography_assignment_status": status,
        "geography_type": row["target_geography_type"] or "unmapped",
        "geography_id": row["custom_geography_id"],
        "stat_area_id": "",
        "stat_area_yishuv_stat_2022": "",
        "stat_area_stat_2022": "",
        "locality_id": "",
        "locality_code": row.get("target_locality_code", ""),
        "locality_name": row.get("target_locality_name", ""),
        "custom_geography_id": row["custom_geography_id"],
        "is_mapped": False,
        "is_geographic": False,
        "final_assignment_method": row["assignment_method"],
        "final_assignment_source": row["assignment_source"],
        "geocode_key": row["source_row_uid"],
        "geocode_lon": "",
        "geocode_lat": "",
        "geocoder": "",
        "geocode_status": status,
        "geocode_confidence": "",
        "address_match_status": geocoding_row.get("address_match_status", ""),
        "address_query": geocoding_row.get("address_query", ""),
        "unresolved_reason": reason,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--geocoded-points",
        type=Path,
        default=PROCESSED_DIR / "geocoding" / "geocoded_points.csv",
        help="Reviewed geocode cache CSV. Optional; pipeline remains partial when absent.",
    )
    args = parser.parse_args()

    assignment_rows = read_csv(ASSIGNMENT_PLAN)
    stat_metadata = load_stat_metadata()
    geocoding_input = load_geocoding_input()
    geocoding_units = load_geocoding_unit_index()
    geocoded_points, geocode_keys = load_geocoded_points(args.geocoded_points)
    stats = load_stat_areas() if not geocoded_points.empty else gpd.GeoDataFrame()
    geocoded_assignments, geocoded_outside = spatially_assign_points(geocoded_points, stats)

    output: list[dict[str, Any]] = []
    point_output: list[dict[str, Any]] = []
    for key, point in geocoded_assignments.items():
        point_output.append(point)

    for row in assignment_rows:
        method = row["assignment_method"]
        uid = row["source_row_uid"]

        if method == "single_stat_locality":
            stat_id = row["target_stat_area_id"].split("|", 1)[0]
            stat = stat_metadata.get(stat_id)
            if stat:
                output.append(stat_assignment(row, stat, "single_stat_assigned", "single_stat_locality"))
            else:
                output.append(unmapped(row, "missing_stat_area_metadata", f"stat area not found: {stat_id}"))
            continue

        if method == "direct_address_geocode_needed":
            geocoding_row = geocoding_input.get(uid, {})
            geocode_lookup_key = geocoding_units.get(uid, uid)
            geocode_match_key = geocode_lookup_key if geocode_lookup_key in geocoded_assignments else uid
            if geocode_match_key in geocoded_assignments:
                point = geocoded_assignments[geocode_match_key]
                if not point_matches_expected_locality(row, point):
                    expected_codes = "|".join(split_locality_codes(row.get("target_locality_code", "")))
                    point_code = normalize_locality_code(point.get("locality_code", ""))
                    output.append(
                        unmapped(
                            row,
                            "geocoded_point_outside_expected_locality",
                            f"geocoded point fell in locality {point_code}, expected {expected_codes}",
                            geocoding_row,
                        )
                    )
                    continue
                output.append(
                    {
                        **base_output(row),
                        "geography_assignment_status": "geocoded_stat_area_assigned",
                        "geography_type": "statistical_area",
                        "geography_id": point["stat_area_id"],
                        "stat_area_id": point["stat_area_id"],
                        "stat_area_yishuv_stat_2022": point["yishuv_stat_2022"],
                        "stat_area_stat_2022": point["stat_2022"],
                        "locality_id": point["locality_id"],
                        "locality_code": point["locality_code"],
                        "locality_name": point["locality_name_he"],
                        "custom_geography_id": "",
                        "is_mapped": True,
                        "is_geographic": True,
                        "final_assignment_method": "geocoded_point_in_polygon",
                        "final_assignment_source": "reviewed_geocode_cache",
                        "geocode_key": geocode_match_key,
                        "geocode_lon": point["geocode_lon"],
                        "geocode_lat": point["geocode_lat"],
                        "geocoder": point["geocoder"],
                        "geocode_status": point["geocode_status"],
                        "geocode_confidence": point["geocode_confidence"],
                        "address_match_status": geocoding_row.get("address_match_status", ""),
                        "address_query": geocoding_row.get("address_query", ""),
                        "unresolved_reason": "",
                    }
                )
            elif geocode_lookup_key in geocoded_outside or uid in geocoded_outside:
                output.append(unmapped(row, "geocoded_point_outside_stat_area", "geocoded point did not fall inside a 2022 statistical area", geocoding_row))
            elif geocode_lookup_key in geocode_keys or uid in geocode_keys:
                output.append(unmapped(row, "geocode_rejected_or_invalid", "geocode cache row was rejected or had invalid coordinates", geocoding_row))
            elif geocoding_row and geocoding_row.get("address_match_status") != "ready":
                status = f"geocoding_input_not_ready:{geocoding_row.get('address_match_status', 'unknown')}"
                output.append(unmapped(row, status, "address source is not ready for geocoding", geocoding_row))
            else:
                output.append(unmapped(row, "missing_geocode", "row needs geocoding and no reviewed geocode cache row exists", geocoding_row))
            continue

        if method == "custom_point_size_polygon":
            output.append(
                {
                    **base_output(row),
                    "geography_assignment_status": "custom_geography_assigned",
                    "geography_type": "custom_geography",
                    "geography_id": row["custom_geography_id"],
                    "stat_area_id": "",
                    "stat_area_yishuv_stat_2022": "",
                    "stat_area_stat_2022": "",
                    "locality_id": "",
                    "locality_code": "",
                    "locality_name": row["target_locality_name"],
                    "custom_geography_id": row["custom_geography_id"],
                    "is_mapped": True,
                    "is_geographic": True,
                    "final_assignment_method": "custom_point_size_polygon",
                    "final_assignment_source": row["assignment_source"],
                    "geocode_key": "",
                    "geocode_lon": "",
                    "geocode_lat": "",
                    "geocoder": "",
                    "geocode_status": "",
                    "geocode_confidence": "",
                    "address_match_status": "",
                    "address_query": "",
                    "unresolved_reason": "",
                }
            )
            continue

        if method in {"special_non_geographic", "official_envelope"}:
            output.append(unmapped(row, method, "non-geographic row is counted but not mapped"))
            continue

        output.append(unmapped(row, "unresolved", row.get("unresolved_reason", "unresolved assignment")))

    fields = [
        "source_row_uid",
        "election",
        "election_number",
        "source_row_id",
        "source_locality_code",
        "source_locality_name",
        "source_kalpi",
        "eligible_voters",
        "actual_voters",
        "assignment_method",
        "assignment_source",
        "geography_assignment_status",
        "geography_type",
        "geography_id",
        "stat_area_id",
        "stat_area_yishuv_stat_2022",
        "stat_area_stat_2022",
        "locality_id",
        "locality_code",
        "locality_name",
        "custom_geography_id",
        "is_mapped",
        "is_geographic",
        "final_assignment_method",
        "final_assignment_source",
        "geocode_key",
        "geocode_lon",
        "geocode_lat",
        "geocoder",
        "geocode_status",
        "geocode_confidence",
        "address_match_status",
        "address_query",
        "unresolved_reason",
    ]
    write_csv(OUT_DIR / "ballot_geography_assignments.csv", output, fields)
    write_csv(
        OUT_DIR / "geocode_point_stat_area_assignments.csv",
        point_output,
        [
            "geocode_key",
            "geocode_lon",
            "geocode_lat",
            "stat_area_id",
            "yishuv_stat_2022",
            "stat_2022",
            "locality_id",
            "locality_code",
            "locality_name_he",
            "geocoder",
            "geocode_status",
            "geocode_confidence",
            "review_status",
        ],
    )

    missing = [row for row in output if row["geography_assignment_status"].startswith("missing_geocode") or row["geography_assignment_status"].startswith("geocoding_input_not_ready") or row["geography_assignment_status"] == "geocoded_point_outside_stat_area" or row["geography_assignment_status"] == "geocoded_point_outside_expected_locality"]
    write_csv(OUT_DIR / "missing_geography_assignment_rows.csv", missing, fields)

    summary: list[dict[str, Any]] = []
    for election in sorted({row["election"] for row in output}, reverse=True):
        rows = [row for row in output if row["election"] == election]
        statuses = Counter(row["geography_assignment_status"] for row in rows)
        mapped_rows = [row for row in rows if normalize_bool(row["is_mapped"])]
        missing_rows = [
            row for row in rows
            if row["geography_assignment_status"].startswith("missing_geocode")
            or row["geography_assignment_status"].startswith("geocoding_input_not_ready")
            or row["geography_assignment_status"] == "geocoded_point_outside_stat_area"
            or row["geography_assignment_status"] == "geocoded_point_outside_expected_locality"
        ]
        summary.append(
            {
                "election": election,
                "rows": len(rows),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in rows),
                "mapped_rows": len(mapped_rows),
                "mapped_actual_voters": sum(int_value(row["actual_voters"]) for row in mapped_rows),
                "stat_area_rows": sum(1 for row in mapped_rows if row["geography_type"] == "statistical_area"),
                "custom_geography_rows": sum(1 for row in mapped_rows if row["geography_type"] == "custom_geography"),
                "pending_or_missing_geocode_rows": len(missing_rows),
                "pending_or_missing_geocode_actual_voters": sum(int_value(row["actual_voters"]) for row in missing_rows),
                "envelope_rows": statuses["official_envelope"],
                "special_non_geographic_rows": statuses["special_non_geographic"],
                "unresolved_rows": statuses["unresolved"],
            }
        )
    write_csv(OUT_DIR / "final_assignment_summary.csv", summary, list(summary[0].keys()) if summary else [])
    write_json(OUT_DIR / "final_assignment_summary.json", summary)

    print(f"final_assignment_rows={len(output)}")
    print(f"geocoded_points_loaded={len(geocoded_points)}")
    print(f"geocoded_points_assigned={len(point_output)}")
    print(f"missing_geography_assignment_rows={len(missing)}")
    for row in summary:
        print(
            f"{row['election']}: mapped={row['mapped_rows']} stat={row['stat_area_rows']} "
            f"custom={row['custom_geography_rows']} pending_geocode={row['pending_or_missing_geocode_rows']}"
        )


if __name__ == "__main__":
    main()
