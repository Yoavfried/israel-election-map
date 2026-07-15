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
from address_parsing import normalize_house_number, parse_house_number, parse_street_name
from osm_name_matching import comparable_street_name as comparable_name


DEFAULT_PBF = ROOT / ".local" / "geocoders" / "osm" / "israel-and-palestine-latest.osm.pbf"
DEFAULT_WORK_UNITS = PROCESSED_DIR / "geocoding" / "geocoding_address_work_units.csv"
DEFAULT_SUPPLEMENTAL_UNITS = PROCESSED_DIR / "addresses" / "polling_place_address_quality_units.csv"
DEFAULT_STREET_UNITS = PROCESSED_DIR / "geocoding" / "osm_street_stat_geocoding_units.csv"
DEFAULT_STAT_AREAS = PROCESSED_DIR / "geographies" / "statistical_areas_2022.geojson"
DEFAULT_LOCALITIES = PROCESSED_DIR / "geographies" / "localities_2022_dissolved.geojson"
DEFAULT_UNIT_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_address_stat_geocoding_units.csv"
DEFAULT_CANONICAL_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_address_stat_canonical_addresses.csv"
DEFAULT_MATCH_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_address_stat_matches.csv"
DEFAULT_SUMMARY_OUTPUT = PROCESSED_DIR / "geocoding" / "osm_address_stat_summary.json"
DEFAULT_REVIEW_OVERRIDES = ROOT / "data" / "manual" / "manual_osm_address_stat_reviews.csv"

WEAK_STREET_NORMS = {"\u05e8\u05d7", "\u05e9\u05db"}  # "rh"/"shkh" abbreviations in Hebrew.
TAG_RE = re.compile(r'"([^"]+)"=>"([^"]*)"')


def is_usable_street_norm(value: str) -> bool:
    return bool(value) and value not in WEAK_STREET_NORMS and (len(value) > 1 or value.isdigit())

UNIT_FIELDS = [
    "geocoding_unit_id",
    "canonical_address_key",
    "geocoder_query",
    "street_name",
    "house_number",
    "street_norm",
    "street_norm_variants",
    "house_number_norm",
    "target_locality_code",
    "target_locality_name",
    "osm_address_status",
    "osm_address_assignment_method",
    "assigned_stat_area_id",
    "assigned_stat_2022",
    "matched_osm_feature_count",
    "matched_assigned_feature_count",
    "matched_boundary_feature_count",
    "matched_osm_feature_ids",
    "matched_osm_layers",
    "matched_osm_names",
    "matched_osm_addr_streets",
    "matched_osm_addr_places",
    "matched_osm_addr_housenumbers",
    "matched_stat_area_ids",
    "global_matched_osm_feature_count",
    "global_matched_osm_feature_ids",
    "prior_osm_street_status",
    "prior_osm_street_assignment_method",
    "prior_osm_street_assigned_stat_area_id",
    "prior_osm_street_assigned_stat_2022",
    "row_count",
    "actual_voters",
    "eligible_voters",
    "elections",
    "example_address",
    "example_place",
]

CANONICAL_FIELDS = [
    "canonical_address_key",
    "target_locality_code",
    "target_locality_name",
    "street_norm",
    "house_number_norm",
    "resolution_status",
    "resolution_method",
    "assigned_stat_area_id",
    "assigned_stat_2022",
    "osm_street_status",
    "osm_address_status",
    "exact_address_presence",
    "matched_osm_feature_count",
    "global_matched_osm_feature_count",
    "query_unit_count",
    "geocoding_unit_ids",
    "geocoder_queries",
    "street_name_examples",
    "source_row_count",
    "actual_voters",
    "eligible_voters",
    "elections",
    "example_address",
    "example_place",
]

MATCH_FIELDS = [
    "address_match_key",
    "target_locality_code",
    "target_locality_name",
    "street_norm",
    "house_number_norm",
    "osm_feature_id",
    "osm_layer",
    "osm_id",
    "osm_name",
    "osm_addr_street",
    "osm_addr_place",
    "osm_address_name_source",
    "osm_addr_housenumber",
    "osm_addr_city",
    "geometry_type",
    "match_status",
    "assigned_stat_area_id",
    "assigned_stat_2022",
    "matched_stat_area_ids",
    "matched_stat_2022_values",
    "stat_metric_total",
    "dominant_stat_share",
]


def street_name_variants(value: Any) -> set[str]:
    text = normalize_spaces(value)
    candidates = {text}
    prefixes_to_strip = [
        "\u05e8\u05d7\u05d5\u05d1 ",  # rehob
        "\u05e8\u05d7 ",  # rh
        "\u05e9\u05d3\u05e8\u05d5\u05ea ",  # sderot
        "\u05e9\u05d3 ",  # sd
    ]
    for prefix in prefixes_to_strip:
        if text.startswith(prefix):
            candidates.add(text[len(prefix) :])
    if text.startswith("\u05e9\u05d3 "):
        candidates.add("\u05e9\u05d3\u05e8\u05d5\u05ea " + text[3:])
    if text.startswith("\u05e9\u05d3\u05e8\u05d5\u05ea "):
        candidates.add("\u05e9\u05d3 " + text[6:])
    return {comparable_name(candidate) for candidate in candidates if comparable_name(candidate)}


def house_number_tokens(value: Any) -> set[str]:
    text = normalize_spaces(value)
    tokens = re.split(r"[,;|]", text)
    return {token for token in (normalize_house_number(part) for part in tokens) if token}


def is_exact_scalar_house_number(value: Any, target: str) -> bool:
    text = normalize_spaces(value)
    return not re.search(r"[,;|]", text) and normalize_house_number(text) == target


def join_sorted(values: set[Any]) -> str:
    return "|".join(sorted(str(value) for value in values if str(value)))


def parse_other_tags(tags: Any) -> dict[str, str]:
    if not tags:
        return {}
    return dict(TAG_RE.findall(str(tags)))


def clean_osm_id(value: Any) -> str:
    text = normalize_spaces(value)
    return "" if text.lower() == "nan" else text


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


def read_work_units(path: Path, street_units_path: Path) -> pd.DataFrame:
    units = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    units["street_name"] = units["example_address"].map(parse_street_name)
    units["house_number_norm"] = units["example_address"].map(parse_house_number)
    units["house_number"] = units["house_number_norm"]
    units["street_norm"] = units["street_name"].map(comparable_name)
    units["street_norm_variants"] = units["street_name"].map(lambda value: sorted(street_name_variants(value)))
    units["target_locality_code"] = units["target_locality_codes"].map(normalize_spaces)
    units["target_locality_name"] = units["target_locality_names"].map(normalize_spaces)
    units["canonical_address_key"] = (
        units["target_locality_code"] + "|" + units["street_norm"] + "|" + units["house_number_norm"]
    )

    if street_units_path.exists():
        street_units = pd.read_csv(street_units_path, dtype=str, encoding="utf-8-sig").fillna("")
        street_units = street_units[
            [
                "geocoding_unit_id",
                "osm_street_status",
                "osm_street_assignment_method",
                "assigned_stat_area_id",
                "assigned_stat_2022",
            ]
        ].rename(
            columns={
                "osm_street_status": "prior_osm_street_status",
                "osm_street_assignment_method": "prior_osm_street_assignment_method",
                "assigned_stat_area_id": "prior_osm_street_assigned_stat_area_id",
                "assigned_stat_2022": "prior_osm_street_assigned_stat_2022",
            }
        )
        units = units.merge(street_units, on="geocoding_unit_id", how="left")
    else:
        units["prior_osm_street_status"] = ""
        units["prior_osm_street_assignment_method"] = ""
        units["prior_osm_street_assigned_stat_area_id"] = ""
        units["prior_osm_street_assigned_stat_2022"] = ""

    return units.fillna("")


def unit_key_rows(units: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for _, unit in units.iterrows():
        house_number = unit["house_number_norm"]
        if not house_number:
            continue
        for street_norm in unit["street_norm_variants"]:
            if not is_usable_street_norm(street_norm):
                continue
            rows.append(
                {
                    "geocoding_unit_id": unit["geocoding_unit_id"],
                    "address_match_key": f"{unit['target_locality_code']}|{street_norm}|{house_number}",
                    "street_norm_variant": street_norm,
                }
            )
    return pd.DataFrame(rows)


def read_osm_address_features(
    path: Path,
    needed_streets: set[str],
    needed_houses: set[str],
) -> gpd.GeoDataFrame:
    records: list[dict[str, Any]] = []
    geometries = []
    for layer in ["points", "lines", "multipolygons"]:
        columns = ["osm_id", "name", "address", "other_tags"]
        if layer == "multipolygons":
            columns.insert(1, "osm_way_id")
        frame = pyogrio.read_dataframe(path, layer=layer, columns=columns, where="other_tags IS NOT NULL")
        tags_text = frame["other_tags"].fillna("").astype(str)
        frame = frame[
            tags_text.str.contains("addr:housenumber", regex=False)
            & (
                tags_text.str.contains("addr:street", regex=False)
                | tags_text.str.contains("addr:place", regex=False)
            )
        ].copy()

        for _, row in frame.iterrows():
            tags = parse_other_tags(row.get("other_tags", ""))
            street = tags.get("addr:street", "")
            place = tags.get("addr:place", "")
            house_number = tags.get("addr:housenumber", "")
            house_tokens = house_number_tokens(house_number) & needed_houses
            matching_names: dict[str, set[str]] = defaultdict(set)
            for source, value in [("addr:street", street), ("addr:place", place)]:
                for street_norm in street_name_variants(value) & needed_streets:
                    matching_names[street_norm].add(source)
            if not matching_names or not house_tokens:
                continue

            osm_raw_id = clean_osm_id(row.get("osm_id", "")) or clean_osm_id(row.get("osm_way_id", ""))
            feature_id = f"{layer}:{osm_raw_id}"
            for street_norm, name_sources in sorted(matching_names.items()):
                for house_norm in sorted(house_tokens):
                    records.append(
                        {
                            "feature_key_id": f"{feature_id}|{street_norm}|{house_norm}",
                            "osm_feature_id": feature_id,
                            "osm_layer": layer,
                            "osm_id": osm_raw_id,
                            "osm_name": normalize_spaces(row.get("name", "")),
                            "osm_addr_street": street,
                            "osm_addr_place": place,
                            "osm_address_name_source": join_sorted(name_sources),
                            "osm_addr_housenumber": house_number,
                            "osm_addr_city": tags.get("addr:city", ""),
                            "street_norm": street_norm,
                            "house_number_norm": house_norm,
                        }
                    )
                    geometries.append(row.geometry)

    if not records:
        return gpd.GeoDataFrame(records, geometry=[], crs="EPSG:4326")
    return gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4326")


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


def address_features_in_target_localities(
    features: gpd.GeoDataFrame,
    localities: gpd.GeoDataFrame,
    needed_keys: set[str],
) -> gpd.GeoDataFrame:
    if features.empty:
        return features
    joined = gpd.sjoin(features.to_crs(2039), localities, how="inner", predicate="intersects")
    joined["target_locality_code"] = joined["locality_code"].astype(str)
    joined["target_locality_name"] = joined["locality_name_he"].astype(str)
    joined["address_match_key"] = (
        joined["target_locality_code"] + "|" + joined["street_norm"] + "|" + joined["house_number_norm"]
    )
    return joined[joined["address_match_key"].isin(needed_keys)].copy()


def classify_feature_matches(
    features: gpd.GeoDataFrame,
    stats: gpd.GeoDataFrame,
    area_abs_tolerance_m2: float,
    area_rel_tolerance: float,
    dominant_stat_share: float,
) -> list[dict[str, Any]]:
    if features.empty:
        return []

    joined = gpd.sjoin(features, stats, how="inner", predicate="intersects", lsuffix="addr", rsuffix="stat")
    stat_code_column = "locality_code_stat" if "locality_code_stat" in joined.columns else "locality_code"
    joined = joined[joined["target_locality_code"].astype(str) == joined[stat_code_column].astype(str)].copy()

    index_column = right_index_column(joined)
    stat_geometries = stats.geometry
    stat_to_stat_2022 = dict(zip(stats["stat_area_id"], stats["stat_2022"], strict=False))
    by_feature: dict[str, dict[str, Any]] = {}
    stat_values: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for _, row in joined.iterrows():
        feature_key_id = row["feature_key_id"]
        by_feature[feature_key_id] = row.to_dict()
        geometry = row.geometry
        stat_geometry = stat_geometries.loc[row[index_column]]
        if geometry.geom_type in {"Point", "MultiPoint"}:
            value = 1.0
        else:
            intersection = geometry.intersection(stat_geometry)
            value = intersection.area if intersection.area > 0 else intersection.length
        if value > 0:
            stat_values[feature_key_id][row["stat_area_id"]] += float(value)

    records: list[dict[str, Any]] = []
    for feature_key_id, row in by_feature.items():
        values = dict(stat_values[feature_key_id])
        geometry_type = row["geometry"].geom_type
        if geometry_type in {"Point", "MultiPoint"}:
            significant = values
        else:
            significant = significant_parts(values, area_abs_tolerance_m2, area_rel_tolerance)
        total = sum(values.values())
        dominant_stat = ""
        dominant_share = 0.0
        if total > 0 and values:
            dominant_stat, dominant_value = max(values.items(), key=lambda item: item[1])
            dominant_share = dominant_value / total
        if len(significant) == 1:
            status = "osm_exact_address_feature_single_stat"
            assigned_stat = next(iter(significant))
        elif dominant_stat and dominant_share >= dominant_stat_share:
            status = "osm_exact_address_feature_dominant_stat"
            assigned_stat = dominant_stat
        elif significant:
            status = "osm_exact_address_feature_multi_stat_or_boundary"
            assigned_stat = ""
        else:
            status = "osm_exact_address_feature_no_stat_intersection"
            assigned_stat = ""

        records.append(
            {
                "address_match_key": row["address_match_key"],
                "target_locality_code": row["target_locality_code"],
                "target_locality_name": row["target_locality_name"],
                "street_norm": row["street_norm"],
                "house_number_norm": row["house_number_norm"],
                "osm_feature_id": row["osm_feature_id"],
                "osm_layer": row["osm_layer"],
                "osm_id": row["osm_id"],
                "osm_name": row["osm_name"],
                "osm_addr_street": row["osm_addr_street"],
                "osm_addr_place": row["osm_addr_place"],
                "osm_address_name_source": row["osm_address_name_source"],
                "osm_addr_housenumber": row["osm_addr_housenumber"],
                "osm_addr_city": row["osm_addr_city"],
                "geometry_type": geometry_type,
                "match_status": status,
                "assigned_stat_area_id": assigned_stat,
                "assigned_stat_2022": stat_to_stat_2022.get(assigned_stat, ""),
                "matched_stat_area_ids": join_sorted(set(significant)),
                "matched_stat_2022_values": join_sorted({stat_to_stat_2022.get(stat, "") for stat in significant}),
                "stat_metric_total": round(total, 3),
                "dominant_stat_share": round(dominant_share, 4),
            }
        )
    return records


def classify_unit(unit: pd.Series, matches: list[dict[str, Any]]) -> dict[str, Any]:
    if not unit["house_number_norm"] or not is_usable_street_norm(unit["street_norm"]):
        status = "weak_or_unparsed_address"
        method = ""
        assigned_stat = ""
        assigned_stat_2022 = ""
    elif not matches:
        status = "osm_exact_address_not_found_in_target_locality"
        method = ""
        assigned_stat = ""
        assigned_stat_2022 = ""
    else:
        assigned = [
            match
            for match in matches
            if match["match_status"]
            in {
                "osm_exact_address_feature_single_stat",
                "osm_exact_address_feature_dominant_stat",
            }
        ]
        boundary = [
            match
            for match in matches
            if match["match_status"]
            not in {
                "osm_exact_address_feature_single_stat",
                "osm_exact_address_feature_dominant_stat",
            }
        ]
        assigned_stats = {match["assigned_stat_area_id"] for match in assigned if match["assigned_stat_area_id"]}
        has_dominant = any(match["match_status"] == "osm_exact_address_feature_dominant_stat" for match in assigned)
        if len(assigned_stats) == 1 and not boundary and not has_dominant:
            status = "osm_exact_address_single_stat"
            method = "osm_exact_address_single_stat"
            assigned_stat = next(iter(assigned_stats))
            assigned_stat_2022 = next(match["assigned_stat_2022"] for match in assigned if match["assigned_stat_area_id"] == assigned_stat)
        elif len(assigned_stats) == 1 and not boundary:
            status = "osm_exact_address_dominant_stat"
            method = "osm_exact_address_dominant_stat"
            assigned_stat = next(iter(assigned_stats))
            assigned_stat_2022 = next(match["assigned_stat_2022"] for match in assigned if match["assigned_stat_area_id"] == assigned_stat)
        elif len(assigned_stats) == 1 and has_dominant:
            status = "osm_exact_address_dominant_stat_with_boundary_context"
            method = "osm_exact_address_dominant_stat_review"
            assigned_stat = next(iter(assigned_stats))
            assigned_stat_2022 = next(match["assigned_stat_2022"] for match in assigned if match["assigned_stat_area_id"] == assigned_stat)
        elif len(assigned_stats) == 1:
            status = "osm_exact_address_single_stat_with_boundary_context"
            method = "osm_exact_address_single_stat_review"
            assigned_stat = next(iter(assigned_stats))
            assigned_stat_2022 = next(match["assigned_stat_2022"] for match in assigned if match["assigned_stat_area_id"] == assigned_stat)
        elif len(assigned_stats) > 1:
            status = "osm_exact_address_conflicting_stats"
            method = ""
            assigned_stat = ""
            assigned_stat_2022 = ""
        else:
            status = "osm_exact_address_boundary_only"
            method = ""
            assigned_stat = ""
            assigned_stat_2022 = ""

    return {
        "osm_address_status": status,
        "osm_address_assignment_method": method,
        "assigned_stat_area_id": assigned_stat,
        "assigned_stat_2022": assigned_stat_2022,
    }


def build_unit_rows(
    units: pd.DataFrame,
    keys: pd.DataFrame,
    match_records: list[dict[str, Any]],
    global_features: gpd.GeoDataFrame,
) -> list[dict[str, Any]]:
    matches_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in match_records:
        matches_by_key[record["address_match_key"]].append(record)

    global_matches_by_pair: dict[str, set[str]] = defaultdict(set)
    for _, feature in global_features.iterrows():
        pair = f"{feature['street_norm']}|{feature['house_number_norm']}"
        global_matches_by_pair[pair].add(feature["osm_feature_id"])

    unit_keys = keys.groupby("geocoding_unit_id")["address_match_key"].apply(lambda values: sorted(set(values))).to_dict() if not keys.empty else {}
    rows: list[dict[str, Any]] = []
    for _, unit in units.iterrows():
        matches: list[dict[str, Any]] = []
        for key in unit_keys.get(unit["geocoding_unit_id"], []):
            matches.extend(matches_by_key.get(key, []))
        scalar_matches = [
            match
            for match in matches
            if is_exact_scalar_house_number(match["osm_addr_housenumber"], unit["house_number_norm"])
        ]
        if scalar_matches:
            matches = scalar_matches
        # De-duplicate features that matched through multiple street-name variants.
        unique_matches = {match["osm_feature_id"]: match for match in matches}
        matches = list(unique_matches.values())
        global_feature_ids: set[str] = set()
        for street_norm in unit["street_norm_variants"]:
            pair = f"{street_norm}|{unit['house_number_norm']}"
            global_feature_ids.update(global_matches_by_pair.get(pair, set()))

        classification = classify_unit(unit, matches)
        direct_count = sum(
            1
            for match in matches
            if match["match_status"]
            in {
                "osm_exact_address_feature_single_stat",
                "osm_exact_address_feature_dominant_stat",
            }
        )
        boundary_count = len(matches) - direct_count
        rows.append(
            {
                "geocoding_unit_id": unit["geocoding_unit_id"],
                "canonical_address_key": unit["canonical_address_key"],
                "geocoder_query": unit["geocoder_query"],
                "street_name": unit["street_name"],
                "house_number": unit["house_number"],
                "street_norm": unit["street_norm"],
                "street_norm_variants": join_sorted(set(unit["street_norm_variants"])),
                "house_number_norm": unit["house_number_norm"],
                "target_locality_code": unit["target_locality_code"],
                "target_locality_name": unit["target_locality_name"],
                **classification,
                "matched_osm_feature_count": len(matches),
                "matched_assigned_feature_count": direct_count,
                "matched_boundary_feature_count": boundary_count,
                "matched_osm_feature_ids": join_sorted({match["osm_feature_id"] for match in matches}),
                "matched_osm_layers": join_sorted({match["osm_layer"] for match in matches}),
                "matched_osm_names": join_sorted({match["osm_name"] for match in matches}),
                "matched_osm_addr_streets": join_sorted({match["osm_addr_street"] for match in matches}),
                "matched_osm_addr_places": join_sorted({match["osm_addr_place"] for match in matches}),
                "matched_osm_addr_housenumbers": join_sorted({match["osm_addr_housenumber"] for match in matches}),
                "matched_stat_area_ids": join_sorted({stat for match in matches for stat in str(match["matched_stat_area_ids"]).split("|") if stat}),
                "global_matched_osm_feature_count": len(global_feature_ids),
                "global_matched_osm_feature_ids": join_sorted(global_feature_ids),
                "prior_osm_street_status": unit.get("prior_osm_street_status", ""),
                "prior_osm_street_assignment_method": unit.get("prior_osm_street_assignment_method", ""),
                "prior_osm_street_assigned_stat_area_id": unit.get("prior_osm_street_assigned_stat_area_id", ""),
                "prior_osm_street_assigned_stat_2022": unit.get("prior_osm_street_assigned_stat_2022", ""),
                "row_count": int_value(unit.get("row_count", "")),
                "actual_voters": int_value(unit.get("actual_voters", "")),
                "eligible_voters": int_value(unit.get("eligible_voters", "")),
                "elections": unit.get("elections", ""),
                "example_address": unit.get("example_address", ""),
                "example_place": unit.get("example_place", ""),
            }
        )
    return rows


def resolution_for(row: dict[str, Any]) -> tuple[str, str, str, str]:
    street_status = row["prior_osm_street_status"]
    address_status = row["osm_address_status"]
    if street_status == "single_stat_street_buffer":
        return (
            "resolved_by_street_geometry",
            row["prior_osm_street_assignment_method"],
            row["prior_osm_street_assigned_stat_area_id"],
            row["prior_osm_street_assigned_stat_2022"],
        )
    if address_status == "osm_exact_address_single_stat":
        return (
            "resolved_by_exact_house_number",
            row["osm_address_assignment_method"],
            row["assigned_stat_area_id"],
            row["assigned_stat_2022"],
        )
    status_map = {
        "osm_exact_address_dominant_stat": "review_exact_house_number_dominant_stat",
        "osm_exact_address_conflicting_stats": "review_exact_house_number_conflicting_stats",
        "osm_exact_address_boundary_only": "review_exact_house_number_boundary_only",
        "weak_or_unparsed_address": "unresolved_weak_or_unparsed_address",
    }
    if address_status in status_map:
        return (status_map[address_status], "", "", "")
    street_map = {
        "multi_stat_or_boundary_street": "unresolved_street_spans_stats_exact_address_missing",
        "single_stat_centerline_only_buffer_multi_stat": "unresolved_street_buffer_crosses_stats_exact_address_missing",
        "osm_street_not_found_in_target_locality": "unresolved_street_and_exact_address_missing",
    }
    return (street_map.get(street_status, "unresolved_other"), "", "", "")


def joined_pipe_values(rows: list[dict[str, Any]], field: str) -> str:
    values = {
        normalize_spaces(part)
        for row in rows
        for part in str(row.get(field, "")).split("|")
        if normalize_spaces(part)
    }
    return join_sorted(values)


def build_canonical_rows(unit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in unit_rows:
        grouped[row["canonical_address_key"]].append(row)

    output: list[dict[str, Any]] = []
    for canonical_key, rows in sorted(grouped.items()):
        street_statuses = {row["prior_osm_street_status"] for row in rows}
        address_statuses = {row["osm_address_status"] for row in rows}
        address_stats = {row["assigned_stat_area_id"] for row in rows}
        street_stats = {row["prior_osm_street_assigned_stat_area_id"] for row in rows}
        if len(street_statuses) != 1 or len(address_statuses) != 1 or len(address_stats) != 1 or len(street_stats) != 1:
            raise ValueError(f"Canonical address has inconsistent OSM classifications: {canonical_key}")
        first = rows[0]
        resolution_status, resolution_method, assigned_stat, assigned_stat_2022 = resolution_for(first)
        if first["osm_address_status"] == "weak_or_unparsed_address":
            exact_address_presence = "not_testable"
        elif int_value(first["matched_osm_feature_count"]):
            exact_address_presence = "in_target_locality"
        elif int_value(first["global_matched_osm_feature_count"]):
            exact_address_presence = "matching_pair_only_outside_target_locality"
        else:
            exact_address_presence = "explicit_osm_address_pair_absent"
        output.append(
            {
                "canonical_address_key": canonical_key,
                "target_locality_code": first["target_locality_code"],
                "target_locality_name": first["target_locality_name"],
                "street_norm": first["street_norm"],
                "house_number_norm": first["house_number_norm"],
                "resolution_status": resolution_status,
                "resolution_method": resolution_method,
                "assigned_stat_area_id": assigned_stat,
                "assigned_stat_2022": assigned_stat_2022,
                "osm_street_status": first["prior_osm_street_status"],
                "osm_address_status": first["osm_address_status"],
                "exact_address_presence": exact_address_presence,
                "matched_osm_feature_count": max(int_value(row["matched_osm_feature_count"]) for row in rows),
                "global_matched_osm_feature_count": max(int_value(row["global_matched_osm_feature_count"]) for row in rows),
                "query_unit_count": len(rows),
                "geocoding_unit_ids": join_sorted({row["geocoding_unit_id"] for row in rows}),
                "geocoder_queries": join_sorted({row["geocoder_query"] for row in rows}),
                "street_name_examples": join_sorted({row["street_name"] for row in rows}),
                "source_row_count": sum(int_value(row["row_count"]) for row in rows),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in rows),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in rows),
                "elections": joined_pipe_values(rows, "elections"),
                "example_address": first["example_address"],
                "example_place": first["example_place"],
            }
        )
    return output


def build_supplemental_canonical_rows(
    path: Path,
    existing_keys: set[str],
) -> tuple[list[dict[str, Any]], int]:
    if not path.exists():
        return [], 0
    units = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    if "unit_quality_category" not in units.columns:
        return [], 0
    units = units[
        (units["unit_quality_category"] == "street_number")
        & (units["target_locality_codes"].map(normalize_spaces) == "")
    ].copy()
    if units.empty:
        return [], 0

    units["street_name"] = units["example_address"].map(parse_street_name)
    units["street_norm"] = units["street_name"].map(comparable_name)
    units["house_number_norm"] = units["example_address"].map(parse_house_number)
    units["canonical_address_key"] = units.apply(
        lambda row: (
            f"targets:{normalize_spaces(row['target_locality_names'])}"
            f"|{row['street_norm']}|{row['house_number_norm']}"
        ),
        axis=1,
    )

    output: list[dict[str, Any]] = []
    for canonical_key, members in units.groupby("canonical_address_key", sort=True):
        if canonical_key in existing_keys:
            continue
        first = members.iloc[0]
        output.append(
            {
                "canonical_address_key": canonical_key,
                "target_locality_code": "",
                "target_locality_name": normalize_spaces(first["target_locality_names"]),
                "street_norm": first["street_norm"],
                "house_number_norm": first["house_number_norm"],
                "resolution_status": "target_locality_code_unavailable",
                "resolution_method": "",
                "assigned_stat_area_id": "",
                "assigned_stat_2022": "",
                "osm_street_status": "not_tested_target_locality_code_unavailable",
                "osm_address_status": "not_tested_target_locality_code_unavailable",
                "exact_address_presence": "not_testable",
                "matched_osm_feature_count": 0,
                "global_matched_osm_feature_count": 0,
                "query_unit_count": len(members),
                "geocoding_unit_ids": join_sorted(set(members["geocoding_unit_id"])),
                "geocoder_queries": join_sorted(set(members["geocoder_query"])),
                "street_name_examples": join_sorted(set(members["street_name"])),
                "source_row_count": sum(int_value(value) for value in members["row_count"]),
                "actual_voters": sum(int_value(value) for value in members["actual_voters"]),
                "eligible_voters": sum(int_value(value) for value in members["eligible_voters"]),
                "elections": join_sorted(
                    {
                        normalize_spaces(part)
                        for value in members["elections"]
                        for part in str(value).split("|")
                        if normalize_spaces(part)
                    }
                ),
                "example_address": first["example_address"],
                "example_place": first["example_place"],
            }
        )
    return output, len(units)


def apply_review_overrides(
    canonical_rows: list[dict[str, Any]],
    path: Path,
    stat_areas_path: Path,
) -> tuple[int, dict[str, int]]:
    if not path.exists():
        return 0, {}

    overrides = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    required = {
        "canonical_address_key",
        "expected_resolution_status",
        "expected_osm_address_status",
        "resolution_status",
        "resolution_method",
        "assigned_stat_area_id",
    }
    missing = required - set(overrides.columns)
    if missing:
        raise ValueError(f"OSM address review overrides are missing columns: {sorted(missing)}")
    duplicate_keys = overrides.loc[
        overrides["canonical_address_key"].duplicated(keep=False), "canonical_address_key"
    ].tolist()
    if duplicate_keys:
        raise ValueError(f"Duplicate OSM address review overrides: {sorted(set(duplicate_keys))}")

    rows_by_key = {row["canonical_address_key"]: row for row in canonical_rows}
    stat_areas = gpd.read_file(stat_areas_path)
    stat_records = stat_areas[["stat_area_id", "stat_2022", "locality_code"]].copy()
    stat_records["stat_area_id"] = stat_records["stat_area_id"].astype(str)
    stat_records["stat_2022"] = stat_records["stat_2022"].map(lambda value: str(int_value(value)))
    stat_records["locality_code"] = stat_records["locality_code"].astype(str)
    stat_2022_by_id = dict(zip(stat_records["stat_area_id"], stat_records["stat_2022"], strict=False))
    locality_by_stat_id = dict(
        zip(stat_records["stat_area_id"], stat_records["locality_code"], strict=False)
    )

    method_counts: Counter[str] = Counter()
    for _, override in overrides.iterrows():
        key = str(override["canonical_address_key"]).strip()
        if key not in rows_by_key:
            raise ValueError(f"OSM address review override does not match a canonical address: {key}")
        row = rows_by_key[key]
        expected_resolution = normalize_spaces(override["expected_resolution_status"])
        expected_osm_status = normalize_spaces(override["expected_osm_address_status"])
        if row["resolution_status"] != expected_resolution:
            raise ValueError(
                f"Stale OSM address review for {key}: expected resolution_status "
                f"{expected_resolution!r}, found {row['resolution_status']!r}"
            )
        if row["osm_address_status"] != expected_osm_status:
            raise ValueError(
                f"Stale OSM address review for {key}: expected osm_address_status "
                f"{expected_osm_status!r}, found {row['osm_address_status']!r}"
            )

        assigned_stat = normalize_spaces(override["assigned_stat_area_id"])
        if assigned_stat not in stat_2022_by_id:
            raise ValueError(f"Unknown reviewed statistical area for {key}: {assigned_stat}")
        target_locality_code = normalize_spaces(row["target_locality_code"])
        if target_locality_code and locality_by_stat_id[assigned_stat] != target_locality_code:
            raise ValueError(
                f"Reviewed statistical area {assigned_stat} is outside target locality "
                f"{target_locality_code} for {key}"
            )

        resolution_status = normalize_spaces(override["resolution_status"])
        resolution_method = normalize_spaces(override["resolution_method"])
        if not resolution_status.startswith("resolved_by_reviewed_") or not resolution_method:
            raise ValueError(f"Invalid reviewed resolution metadata for {key}")
        row["resolution_status"] = resolution_status
        row["resolution_method"] = resolution_method
        row["assigned_stat_area_id"] = assigned_stat
        row["assigned_stat_2022"] = stat_2022_by_id[assigned_stat]
        method_counts[resolution_method] += 1

    return len(overrides), dict(sorted(method_counts.items()))


def summary_by_prior_status(unit_rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for prior_status in sorted({row["prior_osm_street_status"] for row in unit_rows}):
        rows = [row for row in unit_rows if row["prior_osm_street_status"] == prior_status]
        counts = Counter(row["osm_address_status"] for row in rows)
        output[prior_status or "missing_prior_street_status"] = dict(sorted(counts.items()))
    return output


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, default=DEFAULT_PBF)
    parser.add_argument("--work-units", type=Path, default=DEFAULT_WORK_UNITS)
    parser.add_argument("--supplemental-units", type=Path, default=DEFAULT_SUPPLEMENTAL_UNITS)
    parser.add_argument("--street-units", type=Path, default=DEFAULT_STREET_UNITS)
    parser.add_argument("--stat-areas", type=Path, default=DEFAULT_STAT_AREAS)
    parser.add_argument("--localities", type=Path, default=DEFAULT_LOCALITIES)
    parser.add_argument("--unit-output", type=Path, default=DEFAULT_UNIT_OUTPUT)
    parser.add_argument("--canonical-output", type=Path, default=DEFAULT_CANONICAL_OUTPUT)
    parser.add_argument("--match-output", type=Path, default=DEFAULT_MATCH_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--review-overrides", type=Path, default=DEFAULT_REVIEW_OVERRIDES)
    parser.add_argument("--area-abs-tolerance-m2", type=float, default=5.0)
    parser.add_argument("--area-rel-tolerance", type=float, default=0.005)
    parser.add_argument("--dominant-stat-share", type=float, default=0.9)
    args = parser.parse_args()

    if not args.pbf.exists():
        raise SystemExit(f"Missing OSM PBF: {args.pbf}")

    units = read_work_units(args.work_units, args.street_units)
    keys = unit_key_rows(units)
    needed_keys = set(keys["address_match_key"]) if not keys.empty else set()
    needed_streets = set(keys["street_norm_variant"]) if not keys.empty else set()
    needed_houses = set(units["house_number_norm"]) - {""}
    needed_localities = set(units["target_locality_code"]) - {""}

    osm_features = read_osm_address_features(args.pbf, needed_streets, needed_houses)
    stats, localities = load_geographies(args.stat_areas, args.localities, needed_localities)
    local_osm_features = address_features_in_target_localities(osm_features, localities, needed_keys)
    match_records = classify_feature_matches(
        local_osm_features,
        stats,
        args.area_abs_tolerance_m2,
        args.area_rel_tolerance,
        args.dominant_stat_share,
    )
    unit_rows = build_unit_rows(units, keys, match_records, osm_features)
    canonical_rows = build_canonical_rows(unit_rows)
    supplemental_rows, supplemental_query_unit_count = build_supplemental_canonical_rows(
        args.supplemental_units,
        {row["canonical_address_key"] for row in canonical_rows},
    )
    canonical_rows.extend(supplemental_rows)
    canonical_rows.sort(key=lambda row: row["canonical_address_key"])
    reviewed_override_count, reviewed_override_method_counts = apply_review_overrides(
        canonical_rows,
        args.review_overrides,
        args.stat_areas,
    )

    write_csv(args.match_output, match_records, MATCH_FIELDS)
    write_csv(args.unit_output, unit_rows, UNIT_FIELDS)
    write_csv(args.canonical_output, canonical_rows, CANONICAL_FIELDS)

    status_counts = Counter(row["osm_address_status"] for row in unit_rows)
    canonical_status_counts = Counter(row["resolution_status"] for row in canonical_rows)
    canonical_presence_counts = Counter(row["exact_address_presence"] for row in canonical_rows)
    direct_rows = [row for row in unit_rows if row["osm_address_status"] == "osm_exact_address_single_stat"]
    dominant_rows = [row for row in unit_rows if row["osm_address_status"] == "osm_exact_address_dominant_stat"]
    direct_plus_dominant_rows = [
        row
        for row in unit_rows
        if row["osm_address_status"]
        in {
            "osm_exact_address_single_stat",
            "osm_exact_address_dominant_stat",
        }
    ]
    direct_or_review_rows = [
        row
        for row in unit_rows
        if row["osm_address_status"]
        in {
            "osm_exact_address_single_stat",
            "osm_exact_address_dominant_stat",
            "osm_exact_address_single_stat_with_boundary_context",
            "osm_exact_address_dominant_stat_with_boundary_context",
        }
    ]
    target_prior_statuses = {
        "single_stat_centerline_only_buffer_multi_stat",
        "multi_stat_or_boundary_street",
    }
    target_rows = [row for row in unit_rows if row["prior_osm_street_status"] in target_prior_statuses]
    target_direct_rows = [row for row in target_rows if row["osm_address_status"] == "osm_exact_address_single_stat"]
    target_dominant_rows = [row for row in target_rows if row["osm_address_status"] == "osm_exact_address_dominant_stat"]
    target_direct_plus_dominant_rows = [
        row
        for row in target_rows
        if row["osm_address_status"]
        in {
            "osm_exact_address_single_stat",
            "osm_exact_address_dominant_stat",
        }
    ]
    target_direct_or_review_rows = [
        row
        for row in target_rows
        if row["osm_address_status"]
        in {
            "osm_exact_address_single_stat",
            "osm_exact_address_dominant_stat",
            "osm_exact_address_single_stat_with_boundary_context",
            "osm_exact_address_dominant_stat_with_boundary_context",
        }
    ]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pbf": str(args.pbf),
        "work_units": str(args.work_units),
        "street_units": str(args.street_units),
        "stat_areas": str(args.stat_areas),
        "localities": str(args.localities),
        "review_overrides": str(args.review_overrides),
        "work_unit_count": len(units),
        "supplemental_query_unit_count": supplemental_query_unit_count,
        "canonical_address_count": len(canonical_rows),
        "duplicate_query_unit_count": len(units) + supplemental_query_unit_count - len(canonical_rows),
        "reviewed_override_count": reviewed_override_count,
        "reviewed_override_method_counts": reviewed_override_method_counts,
        "area_abs_tolerance_m2": args.area_abs_tolerance_m2,
        "area_rel_tolerance": args.area_rel_tolerance,
        "dominant_stat_share": args.dominant_stat_share,
        "unit_key_count": len(keys),
        "needed_exact_address_key_count": len(needed_keys),
        "needed_street_variant_count": len(needed_streets),
        "needed_house_number_count": len(needed_houses),
        "matching_osm_address_feature_key_count": len(osm_features),
        "same_locality_osm_address_feature_key_count": len(local_osm_features),
        "match_record_count": len(match_records),
        "unit_status_counts": dict(sorted(status_counts.items())),
        "canonical_resolution_status_counts": dict(sorted(canonical_status_counts.items())),
        "canonical_exact_address_presence_counts": dict(sorted(canonical_presence_counts.items())),
        "unit_status_counts_by_prior_street_status": summary_by_prior_status(unit_rows),
        "direct_assignable_unit_count": len(direct_rows),
        "direct_assignable_source_row_count": sum(int_value(row["row_count"]) for row in direct_rows),
        "direct_assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in direct_rows),
        "dominant_assignable_unit_count": len(dominant_rows),
        "dominant_assignable_source_row_count": sum(int_value(row["row_count"]) for row in dominant_rows),
        "dominant_assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in dominant_rows),
        "direct_plus_dominant_assignable_unit_count": len(direct_plus_dominant_rows),
        "direct_plus_dominant_assignable_source_row_count": sum(int_value(row["row_count"]) for row in direct_plus_dominant_rows),
        "direct_plus_dominant_assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in direct_plus_dominant_rows),
        "direct_or_review_unit_count": len(direct_or_review_rows),
        "target_prior_status_unit_count": len(target_rows),
        "target_prior_status_direct_assignable_unit_count": len(target_direct_rows),
        "target_prior_status_direct_assignable_source_row_count": sum(int_value(row["row_count"]) for row in target_direct_rows),
        "target_prior_status_direct_assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in target_direct_rows),
        "target_prior_status_dominant_assignable_unit_count": len(target_dominant_rows),
        "target_prior_status_dominant_assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in target_dominant_rows),
        "target_prior_status_direct_plus_dominant_assignable_unit_count": len(target_direct_plus_dominant_rows),
        "target_prior_status_direct_plus_dominant_assignable_source_row_count": sum(int_value(row["row_count"]) for row in target_direct_plus_dominant_rows),
        "target_prior_status_direct_plus_dominant_assignable_actual_voters": sum(int_value(row["actual_voters"]) for row in target_direct_plus_dominant_rows),
        "target_prior_status_direct_or_review_unit_count": len(target_direct_or_review_rows),
    }
    write_json(args.summary_output, summary)

    print(f"work_units={len(units)}")
    print(f"supplemental_query_units={supplemental_query_unit_count}")
    print(f"canonical_addresses={len(canonical_rows)}")
    print(f"duplicate_query_units={len(units) + supplemental_query_unit_count - len(canonical_rows)}")
    print(f"reviewed_override_count={reviewed_override_count}")
    print(f"needed_exact_address_keys={len(needed_keys)}")
    print(f"matching_osm_address_feature_keys={len(osm_features)}")
    print(f"same_locality_osm_address_feature_keys={len(local_osm_features)}")
    print(f"direct_assignable_unit_count={summary['direct_assignable_unit_count']}")
    print(f"direct_assignable_source_row_count={summary['direct_assignable_source_row_count']}")
    print(f"direct_assignable_actual_voters={summary['direct_assignable_actual_voters']}")
    print(f"dominant_assignable_unit_count={summary['dominant_assignable_unit_count']}")
    print(f"direct_plus_dominant_assignable_unit_count={summary['direct_plus_dominant_assignable_unit_count']}")
    print(f"target_prior_status_direct_assignable_unit_count={summary['target_prior_status_direct_assignable_unit_count']}")
    print(f"target_prior_status_direct_assignable_actual_voters={summary['target_prior_status_direct_assignable_actual_voters']}")
    print(f"target_prior_status_direct_plus_dominant_assignable_unit_count={summary['target_prior_status_direct_plus_dominant_assignable_unit_count']}")
    print(f"target_prior_status_direct_plus_dominant_assignable_actual_voters={summary['target_prior_status_direct_plus_dominant_assignable_actual_voters']}")
    print(f"unit_output={args.unit_output}")
    print(f"canonical_output={args.canonical_output}")
    print(f"match_output={args.match_output}")
    for status, count in sorted(status_counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
