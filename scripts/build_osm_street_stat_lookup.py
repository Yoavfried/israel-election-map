from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOCAL_PYTHON = Path(__file__).resolve().parents[1] / ".local" / "python-geo"
if LOCAL_PYTHON.exists():
    sys.path.insert(0, str(LOCAL_PYTHON))

import geopandas as gpd
import pandas as pd
import pyogrio

from pipeline_common import PROCESSED_DIR, ROOT, int_value, normalize_spaces, write_csv, write_json
from address_parsing import parse_street_name
from osm_name_matching import comparable_street_name as comparable_name


DEFAULT_PBF = ROOT / ".local" / "geocoders" / "osm" / "israel-and-palestine-latest.osm.pbf"
DEFAULT_WORK_UNITS = PROCESSED_DIR / "geocoding" / "geocoding_address_work_units.csv"
DEFAULT_STAT_AREAS = PROCESSED_DIR / "geographies" / "statistical_areas_2022.geojson"
DEFAULT_LOCALITIES = PROCESSED_DIR / "geographies" / "localities_2022_dissolved.geojson"
DEFAULT_LOOKUP_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_street_stat_lookup.csv"
DEFAULT_UNIT_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_street_stat_geocoding_units.csv"
DEFAULT_SUMMARY_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_street_stat_summary.json"

ASSIGNABLE_HIGHWAYS = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "living_street",
    "pedestrian",
    "service",
    "road",
    "busway",
}

NAME_TAGS = {
    "name",
    "name:he",
    "alt_name",
    "alt_name:he",
    "official_name",
    "official_name:he",
    "short_name",
    "short_name:he",
    "old_name",
    "old_name:he",
}

WEAK_STREET_NORMS = {"\u05e8\u05d7", "\u05e9\u05db"}  # "רח", "שכ"


def is_usable_street_norm(value: str) -> bool:
    return bool(value) and value not in WEAK_STREET_NORMS and (len(value) > 1 or value.isdigit())

LOOKUP_FIELDS = [
    "target_locality_code",
    "target_locality_name",
    "street_norm",
    "street_name_examples",
    "osm_names",
    "highway_values",
    "osm_line_count",
    "osm_id_count",
    "osm_street_status",
    "osm_street_assignment_method",
    "assigned_stat_area_id",
    "assigned_stat_2022",
    "centerline_stat_count",
    "buffer_stat_count",
    "centerline_length_m",
    "buffer_area_m2",
    "centerline_stats",
    "buffer_stats",
]

UNIT_FIELDS = [
    "geocoding_unit_id",
    "canonical_street_key",
    "geocoder_query",
    "street_name",
    "street_norm",
    "target_locality_code",
    "target_locality_name",
    "osm_street_status",
    "osm_street_assignment_method",
    "assigned_stat_area_id",
    "assigned_stat_2022",
    "centerline_stat_count",
    "buffer_stat_count",
    "centerline_length_m",
    "buffer_area_m2",
    "centerline_stats",
    "buffer_stats",
    "row_count",
    "actual_voters",
    "eligible_voters",
    "elections",
    "example_address",
    "example_place",
]


def split_pipe(value: Any) -> list[str]:
    return [normalize_spaces(part) for part in str(value or "").split("|") if normalize_spaces(part)]


def join_sorted(values: set[Any]) -> str:
    return "|".join(sorted(str(value) for value in values if str(value)))


def other_tag_values(tags: Any) -> list[str]:
    if not tags:
        return []
    values: list[str] = []
    for key, value in re.findall(r'"([^"]+)"=>"([^"]*)"', str(tags)):
        if key in NAME_TAGS:
            values.append(value)
    return values


def significant_parts(values: dict[str, float], absolute_tolerance: float, relative_tolerance: float) -> dict[str, float]:
    total = sum(values.values())
    return {
        key: value
        for key, value in values.items()
        if value > absolute_tolerance and (total <= 0 or value / total > relative_tolerance)
    }


def right_index_column(frame: gpd.GeoDataFrame) -> str:
    for column in ["index_stat", "index_right"]:
        if column in frame.columns:
            return column
    raise ValueError("Spatial join output does not include a right-index column")


def read_work_units(path: Path) -> pd.DataFrame:
    units = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    units["street_name"] = units["example_address"].map(parse_street_name)
    units["street_norm"] = units["street_name"].map(comparable_name)
    units["target_locality_code"] = units["target_locality_codes"].map(normalize_spaces)
    units["target_locality_name"] = units["target_locality_names"].map(normalize_spaces)
    units["street_match_key"] = units["target_locality_code"] + "|" + units["street_norm"]
    units["canonical_street_key"] = units["street_match_key"]
    return units


def read_matching_osm_lines(path: Path, needed_street_norms: set[str]) -> gpd.GeoDataFrame:
    lines = pyogrio.read_dataframe(
        path,
        layer="lines",
        columns=["osm_id", "name", "highway", "other_tags"],
        where="highway IS NOT NULL AND name IS NOT NULL",
    )
    lines = lines[lines["highway"].isin(ASSIGNABLE_HIGHWAYS)].copy()

    records: list[dict[str, Any]] = []
    for index, row in lines.iterrows():
        names = [row.get("name", "")] + other_tag_values(row.get("other_tags", ""))
        normalized_names = sorted({comparable_name(value) for value in names if comparable_name(value) in needed_street_norms})
        display_names = join_sorted({normalize_spaces(value) for value in names if normalize_spaces(value)})
        for normalized_name in normalized_names:
            records.append(
                {
                    "source_index": index,
                    "street_norm": normalized_name,
                    "osm_names": display_names,
                }
            )

    if not records:
        return gpd.GeoDataFrame(columns=["osm_id", "name", "highway", "other_tags", "street_norm", "osm_names", "geometry"], geometry="geometry", crs=lines.crs)

    matches = pd.DataFrame(records)
    matched_lines = lines.loc[matches["source_index"].to_numpy()].reset_index(drop=True).copy()
    matched_lines["street_norm"] = matches["street_norm"].to_numpy()
    matched_lines["osm_names"] = matches["osm_names"].to_numpy()
    return gpd.GeoDataFrame(matched_lines, geometry="geometry", crs=lines.crs)


def load_geographies(stat_areas_path: Path, localities_path: Path, locality_codes: set[str]) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    localities = gpd.read_file(localities_path)
    localities = localities[localities["locality_code"].astype(str).isin(locality_codes)].copy()
    localities = localities[["locality_code", "locality_name_he", "geometry"]].to_crs(2039)
    localities["locality_code"] = localities["locality_code"].astype(str)

    stats = gpd.read_file(stat_areas_path)
    stats = stats[stats["locality_code"].astype(str).isin(locality_codes)].copy()
    stats = stats[["locality_code", "locality_name_he", "stat_area_id", "stat_2022", "geometry"]].to_crs(2039)
    stats["locality_code"] = stats["locality_code"].astype(str)
    stats["stat_area_id"] = stats["stat_area_id"].astype(str)
    stats["stat_2022"] = stats["stat_2022"].map(lambda value: str(int_value(value)))
    return stats, localities


def street_lines_in_target_localities(
    lines: gpd.GeoDataFrame,
    localities: gpd.GeoDataFrame,
    needed_pairs: set[str],
) -> gpd.GeoDataFrame:
    if lines.empty:
        return lines
    joined = gpd.sjoin(lines.to_crs(2039), localities, how="inner", predicate="intersects")
    joined["locality_code"] = joined["locality_code"].astype(str)
    joined["street_match_key"] = joined["locality_code"] + "|" + joined["street_norm"]
    return joined[joined["street_match_key"].isin(needed_pairs)].copy()


def values_by_pair_stat(
    geometries: gpd.GeoDataFrame,
    stats: gpd.GeoDataFrame,
    metric: str,
) -> dict[tuple[str, str], float]:
    if geometries.empty:
        return {}

    joined = gpd.sjoin(geometries, stats, how="inner", predicate="intersects", lsuffix="line", rsuffix="stat")
    stat_code_column = "locality_code_stat" if "locality_code_stat" in joined.columns else "locality_code"
    if "locality_code_line" in joined.columns:
        joined = joined[joined["locality_code_line"].astype(str) == joined[stat_code_column].astype(str)].copy()
    elif stat_code_column in joined.columns:
        pair_locality = joined["street_match_key"].str.split("|", n=1, regex=False, expand=True)[0]
        joined = joined[pair_locality == joined[stat_code_column].astype(str)].copy()

    stat_geometries = stats.geometry
    index_column = right_index_column(joined)
    values: dict[tuple[str, str], float] = defaultdict(float)
    for _, row in joined.iterrows():
        intersection = row.geometry.intersection(stat_geometries.loc[row[index_column]])
        value = intersection.length if metric == "length" else intersection.area
        if value > 0:
            values[(row["street_match_key"], row["stat_area_id"])] += float(value)
    return values


def classify_pairs(
    units: pd.DataFrame,
    line_localities: gpd.GeoDataFrame,
    stats: gpd.GeoDataFrame,
    buffer_m: float,
    centerline_abs_tolerance_m: float,
    centerline_rel_tolerance: float,
    buffer_abs_tolerance_m2: float,
    buffer_rel_tolerance: float,
) -> dict[str, dict[str, Any]]:
    line_values = values_by_pair_stat(line_localities, stats, "length")

    buffers = line_localities[["street_match_key", "geometry"]].copy()
    buffers["geometry"] = buffers.geometry.buffer(buffer_m)
    buffer_values = values_by_pair_stat(gpd.GeoDataFrame(buffers, geometry="geometry", crs=line_localities.crs), stats, "area")

    stat_to_stat_2022 = dict(zip(stats["stat_area_id"], stats["stat_2022"], strict=False))
    line_meta = (
        line_localities.groupby("street_match_key")
        .agg(
            osm_line_count=("osm_id", "size"),
            osm_id_count=("osm_id", "nunique"),
            osm_names=("osm_names", lambda values: join_sorted(set(values))),
            highway_values=("highway", lambda values: join_sorted(set(values))),
        )
        .to_dict("index")
        if not line_localities.empty
        else {}
    )

    pair_examples = (
        units.groupby("street_match_key")
        .agg(
            target_locality_code=("target_locality_code", "first"),
            target_locality_name=("target_locality_name", "first"),
            street_norm=("street_norm", "first"),
            street_name_examples=("street_name", lambda values: join_sorted(set(values))),
        )
        .to_dict("index")
    )

    pair_classes: dict[str, dict[str, Any]] = {}
    for pair, examples in pair_examples.items():
        centerline_stats = {
            stat: value
            for (candidate_pair, stat), value in line_values.items()
            if candidate_pair == pair
        }
        buffer_stats = {
            stat: value
            for (candidate_pair, stat), value in buffer_values.items()
            if candidate_pair == pair
        }
        significant_centerline = significant_parts(centerline_stats, centerline_abs_tolerance_m, centerline_rel_tolerance)
        significant_buffer = significant_parts(buffer_stats, buffer_abs_tolerance_m2, buffer_rel_tolerance)

        assigned_stat_area_id = ""
        method = ""
        if len(split_pipe(examples["target_locality_code"])) != 1:
            status = "target_locality_code_unavailable"
        elif not centerline_stats and not buffer_stats:
            status = "osm_street_not_found_in_target_locality"
        elif len(significant_buffer) == 1:
            status = "single_stat_street_buffer"
            assigned_stat_area_id = next(iter(significant_buffer))
            method = f"osm_street_buffer_{buffer_m:g}m_single_stat"
        elif len(significant_centerline) == 1:
            status = "single_stat_centerline_only_buffer_multi_stat"
            assigned_stat_area_id = next(iter(significant_centerline))
            method = "osm_street_centerline_single_stat_review"
        else:
            status = "multi_stat_or_boundary_street"

        meta = line_meta.get(pair, {})
        pair_classes[pair] = {
            **examples,
            "osm_names": meta.get("osm_names", ""),
            "highway_values": meta.get("highway_values", ""),
            "osm_line_count": int(meta.get("osm_line_count", 0) or 0),
            "osm_id_count": int(meta.get("osm_id_count", 0) or 0),
            "osm_street_status": status,
            "osm_street_assignment_method": method,
            "assigned_stat_area_id": assigned_stat_area_id if status == "single_stat_street_buffer" else "",
            "assigned_stat_2022": stat_to_stat_2022.get(assigned_stat_area_id, "") if status == "single_stat_street_buffer" else "",
            "centerline_stat_count": len(significant_centerline),
            "buffer_stat_count": len(significant_buffer),
            "centerline_length_m": round(sum(centerline_stats.values()), 1),
            "buffer_area_m2": round(sum(buffer_stats.values()), 1),
            "centerline_stats": join_sorted(set(significant_centerline)),
            "buffer_stats": join_sorted(set(significant_buffer)),
            "_review_stat_area_id": assigned_stat_area_id,
            "_review_stat_2022": stat_to_stat_2022.get(assigned_stat_area_id, ""),
        }
    return pair_classes


def build_unit_rows(units: pd.DataFrame, pair_classes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, unit in units.iterrows():
        street_norm = unit["street_norm"]
        if not is_usable_street_norm(street_norm):
            classification: dict[str, Any] = {
                "osm_street_status": "weak_or_unparsed_street",
                "osm_street_assignment_method": "",
                "assigned_stat_area_id": "",
                "assigned_stat_2022": "",
                "centerline_stat_count": 0,
                "buffer_stat_count": 0,
                "centerline_length_m": 0,
                "buffer_area_m2": 0,
                "centerline_stats": "",
                "buffer_stats": "",
            }
        else:
            classification = pair_classes.get(unit["street_match_key"], {})

        rows.append(
            {
                "geocoding_unit_id": unit["geocoding_unit_id"],
                "canonical_street_key": unit["canonical_street_key"],
                "geocoder_query": unit["geocoder_query"],
                "street_name": unit["street_name"],
                "street_norm": street_norm,
                "target_locality_code": unit["target_locality_code"],
                "target_locality_name": unit["target_locality_name"],
                "osm_street_status": classification.get("osm_street_status", "osm_street_not_found_in_target_locality"),
                "osm_street_assignment_method": classification.get("osm_street_assignment_method", ""),
                "assigned_stat_area_id": classification.get("assigned_stat_area_id", ""),
                "assigned_stat_2022": classification.get("assigned_stat_2022", ""),
                "centerline_stat_count": classification.get("centerline_stat_count", 0),
                "buffer_stat_count": classification.get("buffer_stat_count", 0),
                "centerline_length_m": classification.get("centerline_length_m", 0),
                "buffer_area_m2": classification.get("buffer_area_m2", 0),
                "centerline_stats": classification.get("centerline_stats", ""),
                "buffer_stats": classification.get("buffer_stats", ""),
                "row_count": int_value(unit.get("row_count", "")),
                "actual_voters": int_value(unit.get("actual_voters", "")),
                "eligible_voters": int_value(unit.get("eligible_voters", "")),
                "elections": unit.get("elections", ""),
                "example_address": unit.get("example_address", ""),
                "example_place": unit.get("example_place", ""),
            }
        )
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, default=DEFAULT_PBF)
    parser.add_argument("--work-units", type=Path, default=DEFAULT_WORK_UNITS)
    parser.add_argument(
        "--quality-category",
        action="append",
        default=[],
        help="When the input has unit_quality_category, keep only these categories (repeatable).",
    )
    parser.add_argument("--stat-areas", type=Path, default=DEFAULT_STAT_AREAS)
    parser.add_argument("--localities", type=Path, default=DEFAULT_LOCALITIES)
    parser.add_argument("--lookup-output", type=Path, default=DEFAULT_LOOKUP_OUTPUT)
    parser.add_argument("--unit-output", type=Path, default=DEFAULT_UNIT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--buffer-m", type=float, default=25.0)
    parser.add_argument("--centerline-abs-tolerance-m", type=float, default=5.0)
    parser.add_argument("--centerline-rel-tolerance", type=float, default=0.005)
    parser.add_argument("--buffer-abs-tolerance-m2", type=float, default=100.0)
    parser.add_argument("--buffer-rel-tolerance", type=float, default=0.005)
    args = parser.parse_args()

    if not args.pbf.exists():
        raise SystemExit(f"Missing OSM PBF: {args.pbf}")

    units = read_work_units(args.work_units)
    if args.quality_category:
        if "unit_quality_category" not in units.columns:
            raise SystemExit("--quality-category requires an input with unit_quality_category")
        units = units[units["unit_quality_category"].isin(args.quality_category)].copy()
    valid_units = units[units["street_norm"].map(is_usable_street_norm)].copy()
    needed_street_norms = set(valid_units["street_norm"])
    needed_pairs = set(valid_units["street_match_key"])
    needed_locality_codes = set(valid_units["target_locality_code"]) - {""}

    osm_lines = read_matching_osm_lines(args.pbf, needed_street_norms)
    stats, localities = load_geographies(args.stat_areas, args.localities, needed_locality_codes)
    line_localities = street_lines_in_target_localities(osm_lines, localities, needed_pairs)
    pair_classes = classify_pairs(
        valid_units,
        line_localities,
        stats,
        args.buffer_m,
        args.centerline_abs_tolerance_m,
        args.centerline_rel_tolerance,
        args.buffer_abs_tolerance_m2,
        args.buffer_rel_tolerance,
    )

    lookup_rows = [
        {field: classification.get(field, "") for field in LOOKUP_FIELDS}
        for _, classification in sorted(pair_classes.items(), key=lambda item: (item[1]["target_locality_code"], item[1]["street_norm"]))
    ]
    unit_rows = build_unit_rows(units, pair_classes)

    write_csv(args.lookup_output, lookup_rows, LOOKUP_FIELDS)
    write_csv(args.unit_output, unit_rows, UNIT_FIELDS)

    unit_status_counts = Counter(row["osm_street_status"] for row in unit_rows)
    pair_status_counts = Counter(row["osm_street_status"] for row in lookup_rows)
    assignable_unit_rows = [row for row in unit_rows if row["osm_street_status"] == "single_stat_street_buffer"]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pbf": str(args.pbf),
        "work_units": str(args.work_units),
        "quality_categories": args.quality_category,
        "stat_areas": str(args.stat_areas),
        "localities": str(args.localities),
        "buffer_m": args.buffer_m,
        "centerline_abs_tolerance_m": args.centerline_abs_tolerance_m,
        "centerline_rel_tolerance": args.centerline_rel_tolerance,
        "buffer_abs_tolerance_m2": args.buffer_abs_tolerance_m2,
        "buffer_rel_tolerance": args.buffer_rel_tolerance,
        "work_unit_count": len(units),
        "valid_street_unit_count": len(valid_units),
        "needed_street_count": len(needed_street_norms),
        "needed_locality_street_pair_count": len(needed_pairs),
        "target_locality_count": len(needed_locality_codes),
        "matching_osm_line_name_count": len(osm_lines),
        "same_locality_osm_line_name_count": len(line_localities),
        "matched_locality_street_pair_count": int(line_localities["street_match_key"].nunique()) if not line_localities.empty else 0,
        "lookup_status_counts": dict(sorted(pair_status_counts.items())),
        "unit_status_counts": dict(sorted(unit_status_counts.items())),
        "assignable_unit_count": len(assignable_unit_rows),
        "assignable_source_row_count": sum(int_value(row["row_count"]) for row in assignable_unit_rows),
        "assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in assignable_unit_rows),
        "assignable_eligible_voters": sum(int_value(row["eligible_voters"]) for row in assignable_unit_rows),
    }
    write_json(args.summary_output, summary)

    print(f"work_units={len(units)}")
    print(f"valid_street_units={len(valid_units)}")
    print(f"needed_locality_street_pairs={len(needed_pairs)}")
    print(f"matching_osm_line_names={len(osm_lines)}")
    print(f"same_locality_osm_line_names={len(line_localities)}")
    print(f"assignable_unit_count={summary['assignable_unit_count']}")
    print(f"assignable_source_row_count={summary['assignable_source_row_count']}")
    print(f"assignable_actual_voters={summary['assignable_actual_voters']}")
    print(f"lookup_output={args.lookup_output}")
    print(f"unit_output={args.unit_output}")
    for status, count in sorted(unit_status_counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
