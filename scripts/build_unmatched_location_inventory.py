from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from address_parsing import parse_house_number, parse_street_name
from audit_polling_place_address_quality import comparable_text, quality_for
from build_geocoding_input import build_address_indexes, find_address
from osm_name_matching import comparable_street_name
from pipeline_common import PROCESSED_DIR, ROOT, int_value, normalize_spaces, write_csv, write_json


ASSIGNMENT_PLAN = PROCESSED_DIR / "assignments" / "ballot_assignment_plan.csv"
GEOCODING_INPUT = PROCESSED_DIR / "geocoding" / "geocoding_input.csv"
POLLING_PLACE_ADDRESSES = PROCESSED_DIR / "addresses" / "polling_place_addresses.csv"
OSM_ADDRESS_CANONICAL = PROCESSED_DIR / "geocoding" / "osm_address_stat_canonical_addresses.csv"
OSM_MISSING_NUMBER_STREETS = PROCESSED_DIR / "geocoding" / "osm_street_missing_house_number_lookup.csv"

ROW_OUTPUT = PROCESSED_DIR / "geocoding" / "unmatched_location_rows.csv"
UNIT_OUTPUT = PROCESSED_DIR / "geocoding" / "unmatched_location_units.csv"
CATEGORY_OUTPUT = PROCESSED_DIR / "geocoding" / "unmatched_location_category_summary.csv"
ROW_CATEGORY_OUTPUT = PROCESSED_DIR / "geocoding" / "unmatched_location_row_category_summary.csv"
REASON_OUTPUT = PROCESSED_DIR / "geocoding" / "unmatched_location_reason_summary.csv"
SUMMARY_OUTPUT = PROCESSED_DIR / "geocoding" / "unmatched_location_summary.json"

CATEGORY_ORDER = [
    "Locality only",
    "Locality + street",
    "Locality + street + number",
    "Locality + place",
    "Locality + street + place",
    "Locality + street + number + place",
    "Locality + number, but no street",
    "Locality + number + place, but no street",
    "No Geo Data",
]
CATEGORY_RANK = {category: index for index, category in enumerate(CATEGORY_ORDER)}

CANONICAL_REASON_LABELS = {
    "unresolved_street_and_exact_address_missing": "street_and_exact_address_not_found_in_target_locality",
    "unresolved_street_buffer_crosses_stats_exact_address_missing": "street_buffer_crosses_area_boundary_exact_address_missing",
    "unresolved_street_spans_stats_exact_address_missing": "street_spans_multiple_areas_exact_address_missing",
    "unresolved_weak_or_unparsed_address": "weak_or_unparsed_address",
    "unresolved_other": "address_not_resolved_by_current_osm_rules",
}
STREET_REASON_LABELS = {
    "multi_stat_or_boundary_street": "street_spans_multiple_areas",
    "osm_street_not_found_in_target_locality": "osm_street_not_found_in_target_locality",
    "single_stat_centerline_only_buffer_multi_stat": "street_buffer_crosses_area_boundary",
    "target_locality_code_unavailable": "target_locality_code_unavailable",
    "weak_or_unparsed_street": "weak_or_unparsed_street",
}
REASON_PRIORITY = {
    "street_and_exact_address_not_found_in_target_locality": 10,
    "street_buffer_crosses_area_boundary_exact_address_missing": 11,
    "street_spans_multiple_areas_exact_address_missing": 12,
    "osm_street_not_found_in_target_locality": 20,
    "street_buffer_crosses_area_boundary": 21,
    "street_spans_multiple_areas": 22,
    "target_locality_code_unavailable": 23,
    "weak_or_unparsed_address": 30,
    "weak_or_unparsed_street": 31,
    "street_not_in_current_osm_scope": 32,
    "place_matching_not_implemented": 40,
    "number_without_street": 41,
    "locality_only_no_street_number_or_place": 42,
    "source_text_suspicious_not_tested": 50,
    "custom_locality_outside_2022_stat_area_layer": 60,
    "no_geo_data": 70,
    "address_not_resolved_by_current_osm_rules": 90,
    "address_not_in_current_osm_scope": 91,
}

ROW_FIELDS = [
    "source_row_uid",
    "election",
    "source_locality_code",
    "source_locality_name",
    "source_kalpi",
    "target_locality_code",
    "target_locality_name",
    "assignment_method",
    "address",
    "place",
    "parsed_street",
    "house_number",
    "place_for_category",
    "structural_category",
    "location_signature",
    "unmatched_reason",
    "address_quality_category",
    "address_quality_flags",
    "osm_resolution_status",
    "osm_street_status",
    "actual_voters",
    "eligible_voters",
    "address_source_file",
]

UNIT_FIELDS = [
    "location_signature",
    "structural_category",
    "primary_unmatched_reason",
    "all_unmatched_reasons",
    "ballot_row_count",
    "actual_voters",
    "eligible_voters",
    "elections",
    "source_row_uids",
    "locality_names",
    "street_examples",
    "house_numbers",
    "place_examples",
    "address_examples",
    "quality_categories",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pipe(values: set[Any]) -> str:
    return "|".join(sorted(normalize_spaces(value) for value in values if normalize_spaces(value)))


def locality_parts(row: dict[str, str]) -> list[str]:
    values: list[str] = []
    for field in ["source_locality_name", "target_locality_name"]:
        values.extend(part for part in normalize_spaces(row.get(field, "")).split("|") if normalize_spaces(part))
    return values


def usable_place(address: str, place: str, quality: dict[str, Any], locality_names: list[str]) -> str:
    candidate = normalize_spaces(place)
    flags = set(str(quality["quality_flags"]).split("|"))
    if not candidate and "address_looks_like_place_name" in flags:
        candidate = normalize_spaces(address)
    if comparable_text(candidate) in {"", "0"}:
        return ""
    locality_values = {comparable_text(value) for value in locality_names if comparable_text(value)}
    return "" if comparable_text(candidate) in locality_values else candidate


def parsed_components(
    address: str,
    place: str,
    locality_names: list[str],
) -> tuple[dict[str, Any], str, str, str]:
    quality = quality_for(address, place, locality_names)
    flags = set(str(quality["quality_flags"]).split("|"))
    quality_category = quality["quality_category"]
    place_value = usable_place(address, place, quality, locality_names)
    house_number = parse_house_number(address)
    street = normalize_spaces(parse_street_name(address))

    address_is_place = "address_looks_like_place_name" in flags and not house_number
    if quality_category in {"locality_only_address", "place_only", "missing_address_and_place"}:
        street = ""
        house_number = ""
    elif quality_category == "place_name_in_address_field" or address_is_place:
        if not place_value:
            place_value = normalize_spaces(address)
        street = ""
        house_number = ""
    elif quality_category == "number_only_or_no_street_text":
        street = ""
    elif not any(character.isalpha() for character in street):
        street = ""

    return quality, street, house_number, place_value


def structural_category(
    has_locality: bool,
    street: str,
    house_number: str,
    place: str,
) -> str:
    if not has_locality:
        return "No Geo Data"
    if street and house_number and place:
        return "Locality + street + number + place"
    if street and house_number:
        return "Locality + street + number"
    if street and place:
        return "Locality + street + place"
    if street:
        return "Locality + street"
    if house_number and place:
        return "Locality + number + place, but no street"
    if house_number:
        return "Locality + number, but no street"
    if place:
        return "Locality + place"
    return "Locality only"


def locality_key(row: dict[str, str]) -> str:
    if row["assignment_method"] == "custom_point_size_polygon":
        source_code = normalize_spaces(row.get("source_locality_code", ""))
        source_name = comparable_text(row.get("source_locality_name", ""))
        return f"source:{source_code or source_name}"
    target_code = normalize_spaces(row.get("target_locality_code", ""))
    if target_code:
        return f"target:{target_code}"
    target_name = comparable_text(row.get("target_locality_name", ""))
    source_name = comparable_text(row.get("source_locality_name", ""))
    return f"target-name:{target_name or source_name}" if target_name or source_name else ""


def location_signature(
    row: dict[str, str],
    street: str,
    house_number: str,
    place: str,
) -> str:
    loc = locality_key(row) or "none"
    street_norm = comparable_street_name(street)
    place_norm = comparable_text(place)
    if street_norm and house_number:
        return f"address|{loc}|{street_norm}|{house_number}"
    if street_norm and place_norm:
        return f"street-place|{loc}|{street_norm}|{place_norm}"
    if street_norm:
        return f"street|{loc}|{street_norm}"
    if house_number and place_norm:
        return f"number-place|{loc}|{house_number}|{place_norm}"
    if house_number:
        return f"number|{loc}|{house_number}"
    if place_norm:
        return f"place|{loc}|{place_norm}"
    if loc != "none":
        return f"locality|{loc}"
    address_norm = comparable_text(row.get("address", ""))
    return f"no-geo|{address_norm}|{place_norm}"


def canonical_address_key(row: dict[str, str], street: str, house_number: str) -> str:
    street_norm = comparable_street_name(street)
    target_code = normalize_spaces(row.get("target_locality_code", ""))
    if target_code:
        return f"{target_code}|{street_norm}|{house_number}"
    return f"targets:{normalize_spaces(row.get('target_locality_name', ''))}|{street_norm}|{house_number}"


def street_lookup_key(row: dict[str, str], street: str) -> tuple[str, str, str]:
    target_code = normalize_spaces(row.get("target_locality_code", ""))
    target_name = "" if target_code else normalize_spaces(row.get("target_locality_name", ""))
    return target_code, target_name, comparable_street_name(street)


def index_osm_addresses(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["canonical_address_key"]: row for row in rows}


def index_osm_streets(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    output: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        code = normalize_spaces(row["target_locality_code"])
        name = "" if code else normalize_spaces(row["target_locality_name"])
        key = code, name, row["street_norm"]
        if key in output:
            raise ValueError(f"Duplicate missing-number street lookup key: {key}")
        output[key] = row
    return output


def unmatched_reason(
    row: dict[str, str],
    quality: dict[str, Any],
    street: str,
    house_number: str,
    place: str,
    osm_addresses: dict[str, dict[str, str]],
    osm_streets: dict[tuple[str, str, str], dict[str, str]],
) -> tuple[bool, str, str, str]:
    if row["assignment_method"] == "custom_point_size_polygon":
        return False, "custom_locality_outside_2022_stat_area_layer", "", ""

    category = quality["quality_category"]
    if category == "suspicious_text":
        return False, "source_text_suspicious_not_tested", "", ""
    if street and house_number and category == "street_number":
        osm_row = osm_addresses.get(canonical_address_key(row, street, house_number))
        if osm_row and osm_row["resolution_status"].startswith("resolved_by_"):
            return True, "", osm_row["resolution_status"], osm_row["osm_street_status"]
        if osm_row:
            reason = CANONICAL_REASON_LABELS.get(osm_row["resolution_status"], osm_row["resolution_status"])
            return False, reason, osm_row["resolution_status"], osm_row["osm_street_status"]
        return False, "address_not_in_current_osm_scope", "", ""
    if street and not house_number and category == "missing_house_number":
        osm_row = osm_streets.get(street_lookup_key(row, street))
        if osm_row and osm_row["osm_street_status"] == "single_stat_street_buffer":
            return True, "", "", osm_row["osm_street_status"]
        if osm_row:
            reason = STREET_REASON_LABELS.get(osm_row["osm_street_status"], osm_row["osm_street_status"])
            return False, reason, "", osm_row["osm_street_status"]
        return False, "street_not_in_current_osm_scope", "", ""
    if not locality_key(row):
        return False, "no_geo_data", "", ""
    if not street and house_number:
        return False, "number_without_street", "", ""
    if place:
        return False, "place_matching_not_implemented", "", ""
    if not street and not house_number:
        return False, "locality_only_no_street_number_or_place", "", ""
    return False, "address_not_resolved_by_current_osm_rules", "", ""


def selected_address_rows(
    plan_rows: list[dict[str, str]],
    geocoding_rows: list[dict[str, str]],
    address_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    geocoding_by_uid = {row["source_row_uid"]: row for row in geocoding_rows}
    by_uid, by_exact, by_base = build_address_indexes(address_rows)
    output: list[dict[str, str]] = []
    for plan in plan_rows:
        method = plan["assignment_method"]
        if method == "direct_address_geocode_needed":
            if plan["source_row_uid"] not in geocoding_by_uid:
                raise ValueError(f"Missing geocoding input row: {plan['source_row_uid']}")
            output.append(geocoding_by_uid[plan["source_row_uid"]])
            continue
        if method != "custom_point_size_polygon":
            continue
        address, _ = find_address(plan, by_uid, by_exact, by_base)
        output.append(
            {
                **plan,
                "address": address["address"] if address else "",
                "place": address["place"] if address else "",
                "address_source_file": address["source_file"] if address else "",
            }
        )
    return output


def row_category_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for category in CATEGORY_ORDER:
        members = [row for row in rows if row["structural_category"] == category]
        output.append(
            {
                "structural_category": category,
                "ballot_row_count": len(members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
            }
        )
    return output


def build_units(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["location_signature"]].append(row)

    output: list[dict[str, Any]] = []
    for signature, members in grouped.items():
        first = members[0]
        unit_place = next(
            (
                normalize_spaces(row["place_for_category"])
                for row in members
                if normalize_spaces(row["place_for_category"])
            ),
            "",
        )
        category = structural_category(
            first["structural_category"] != "No Geo Data",
            first["parsed_street"],
            first["house_number"],
            unit_place,
        )
        reasons = {row["unmatched_reason"] for row in members}
        primary_reason = min(reasons, key=lambda reason: (REASON_PRIORITY.get(reason, 999), reason))
        output.append(
            {
                "location_signature": signature,
                "structural_category": category,
                "primary_unmatched_reason": primary_reason,
                "all_unmatched_reasons": pipe(reasons),
                "ballot_row_count": len(members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
                "elections": pipe({row["election"] for row in members}),
                "source_row_uids": pipe({row["source_row_uid"] for row in members}),
                "locality_names": pipe({row["source_locality_name"] for row in members}),
                "street_examples": pipe({row["parsed_street"] for row in members}),
                "house_numbers": pipe({row["house_number"] for row in members}),
                "place_examples": pipe({row["place_for_category"] for row in members}),
                "address_examples": pipe({row["address"] for row in members}),
                "quality_categories": pipe({row["address_quality_category"] for row in members}),
            }
        )
    return sorted(
        output,
        key=lambda row: (
            CATEGORY_RANK[row["structural_category"]],
            row["primary_unmatched_reason"],
            row["location_signature"],
        ),
    )


def unit_category_summary(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for category in CATEGORY_ORDER:
        members = [row for row in units if row["structural_category"] == category]
        output.append(
            {
                "structural_category": category,
                "unmatched_location_signature_count": len(members),
                "ballot_row_count": sum(int_value(row["ballot_row_count"]) for row in members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
            }
        )
    return output


def reason_summary(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        grouped[(unit["structural_category"], unit["primary_unmatched_reason"])].append(unit)
    output = []
    for (category, reason), members in grouped.items():
        output.append(
            {
                "structural_category": category,
                "unmatched_reason": reason,
                "unmatched_location_signature_count": len(members),
                "ballot_row_count": sum(int_value(row["ballot_row_count"]) for row in members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
            }
        )
    return sorted(output, key=lambda row: (CATEGORY_RANK[row["structural_category"]], row["unmatched_reason"]))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    plan_rows = read_csv(ASSIGNMENT_PLAN)
    geocoding_rows = read_csv(GEOCODING_INPUT)
    address_rows = read_csv(POLLING_PLACE_ADDRESSES)
    osm_addresses = index_osm_addresses(read_csv(OSM_ADDRESS_CANONICAL))
    osm_streets = index_osm_streets(read_csv(OSM_MISSING_NUMBER_STREETS))

    official_envelopes = [row for row in plan_rows if row["assignment_method"] == "official_envelope"]
    reviewed_envelope_like = [row for row in plan_rows if row["assignment_method"] == "special_non_geographic"]
    single_stat_rows = [row for row in plan_rows if row["assignment_method"] == "single_stat_locality"]
    custom_geography_rows = [row for row in plan_rows if row["assignment_method"] == "custom_point_size_polygon"]
    candidate_plan_rows = [row for row in plan_rows if row["assignment_method"] == "direct_address_geocode_needed"]
    expected_total = (
        len(official_envelopes)
        + len(reviewed_envelope_like)
        + len(single_stat_rows)
        + len(custom_geography_rows)
        + len(candidate_plan_rows)
    )
    if expected_total != len(plan_rows):
        raise ValueError(f"Assignment plan has unclassified methods: expected {expected_total}, found {len(plan_rows)}")

    selected_rows = selected_address_rows(candidate_plan_rows, geocoding_rows, address_rows)
    unmatched_rows: list[dict[str, Any]] = []
    osm_address_matched = 0
    osm_street_matched = 0
    for row in selected_rows:
        names = locality_parts(row)
        quality, street, house_number, place_value = parsed_components(row.get("address", ""), row.get("place", ""), names)
        has_locality = bool(normalize_spaces(row.get("source_locality_name", "")) or normalize_spaces(row.get("target_locality_name", "")))
        category = structural_category(has_locality, street, house_number, place_value)
        matched, reason, osm_resolution_status, osm_street_status = unmatched_reason(
            row,
            quality,
            street,
            house_number,
            place_value,
            osm_addresses,
            osm_streets,
        )
        if matched:
            if house_number:
                osm_address_matched += 1
            else:
                osm_street_matched += 1
            continue
        unmatched_rows.append(
            {
                "source_row_uid": row["source_row_uid"],
                "election": row["election"],
                "source_locality_code": row.get("source_locality_code", ""),
                "source_locality_name": row.get("source_locality_name", ""),
                "source_kalpi": row.get("source_kalpi", ""),
                "target_locality_code": row.get("target_locality_code", ""),
                "target_locality_name": row.get("target_locality_name", ""),
                "assignment_method": row["assignment_method"],
                "address": row.get("address", ""),
                "place": row.get("place", ""),
                "parsed_street": street,
                "house_number": house_number,
                "place_for_category": place_value,
                "structural_category": category,
                "location_signature": location_signature(row, street, house_number, place_value),
                "unmatched_reason": reason,
                "address_quality_category": quality["quality_category"],
                "address_quality_flags": quality["quality_flags"],
                "osm_resolution_status": osm_resolution_status,
                "osm_street_status": osm_street_status,
                "actual_voters": int_value(row.get("actual_voters", "")),
                "eligible_voters": int_value(row.get("eligible_voters", "")),
                "address_source_file": row.get("address_source_file", ""),
            }
        )

    units = build_units(unmatched_rows)
    category_rows = unit_category_summary(units)
    row_category_rows = row_category_summary(unmatched_rows)
    reason_rows = reason_summary(units)

    unmatched_total = len(unmatched_rows)
    non_envelope_universe = len(single_stat_rows) + len(custom_geography_rows) + len(candidate_plan_rows)
    matched_2022_stat_total = len(single_stat_rows) + osm_address_matched + osm_street_matched
    resolved_total = matched_2022_stat_total + len(custom_geography_rows)
    if resolved_total + unmatched_total != non_envelope_universe:
        raise ValueError(
            f"Non-envelope reconciliation failed: {resolved_total} resolved + {unmatched_total} unmatched "
            f"!= {non_envelope_universe}"
        )

    write_csv(ROW_OUTPUT, unmatched_rows, ROW_FIELDS)
    write_csv(UNIT_OUTPUT, units, UNIT_FIELDS)
    write_csv(CATEGORY_OUTPUT, category_rows, list(category_rows[0]))
    write_csv(ROW_CATEGORY_OUTPUT, row_category_rows, list(row_category_rows[0]))
    write_csv(REASON_OUTPUT, reason_rows, list(reason_rows[0]))

    summary = {
        "generated_at": "2026-07-15",
        "definition": "Non-envelope ballot rows without an accepted geography assignment after the single-stat locality, reviewed custom-geography, and current OSM address/street methods.",
        "assignment_plan_row_count": len(plan_rows),
        "excluded_official_envelope_row_count": len(official_envelopes),
        "excluded_reviewed_envelope_like_row_count": len(reviewed_envelope_like),
        "non_envelope_assignment_universe_row_count": non_envelope_universe,
        "matched_single_stat_locality_row_count": len(single_stat_rows),
        "matched_osm_address_row_count": osm_address_matched,
        "matched_osm_missing_number_street_row_count": osm_street_matched,
        "matched_2022_stat_area_row_count": matched_2022_stat_total,
        "resolved_custom_geography_row_count": len(custom_geography_rows),
        "matched_total_row_count": resolved_total,
        "unmatched_ballot_row_count": unmatched_total,
        "unmatched_location_signature_count": len(units),
        "category_summary": category_rows,
        "row_category_summary": row_category_rows,
        "outputs": {
            "rows": str(ROW_OUTPUT.relative_to(ROOT)),
            "units": str(UNIT_OUTPUT.relative_to(ROOT)),
            "categories": str(CATEGORY_OUTPUT.relative_to(ROOT)),
            "row_categories": str(ROW_CATEGORY_OUTPUT.relative_to(ROOT)),
            "reasons": str(REASON_OUTPUT.relative_to(ROOT)),
        },
    }
    write_json(SUMMARY_OUTPUT, summary)

    print(f"non_envelope_assignment_universe_rows={non_envelope_universe}")
    print(f"matched_single_stat_locality_rows={len(single_stat_rows)}")
    print(f"matched_osm_address_rows={osm_address_matched}")
    print(f"matched_osm_missing_number_street_rows={osm_street_matched}")
    print(f"resolved_custom_geography_rows={len(custom_geography_rows)}")
    print(f"unmatched_ballot_rows={unmatched_total}")
    print(f"unmatched_location_signatures={len(units)}")
    for row in category_rows:
        print(
            f"{row['structural_category']}: signatures={row['unmatched_location_signature_count']} "
            f"rows={row['ballot_row_count']}"
        )


if __name__ == "__main__":
    main()
