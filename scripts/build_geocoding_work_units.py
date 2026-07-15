from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pipeline_common import PROCESSED_DIR, int_value, normalize_spaces, write_csv, write_json
from address_parsing import has_house_number, parse_street_name


GEOCODING_INPUT = PROCESSED_DIR / "geocoding" / "geocoding_input.csv"
OUT_DIR = PROCESSED_DIR / "geocoding"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def comparable_text(value: Any) -> str:
    text = normalize_spaces(value)
    text = text.replace("'", "").replace('"', "").replace("״", "").replace("׳", "")
    text = re.sub(r"[\s.,:/(){}\[\]\-_*]+", "", text)
    return text


def canonical_query(value: Any) -> str:
    text = normalize_spaces(value)
    text = text.replace("״", '"').replace("׳", "'")
    text = re.sub(r"\s*,\s*", ", ", text)
    return text


def query_has_suspicious_prefix(value: str) -> bool:
    return bool(re.match(r"^[\s\"'`,._-]+", value))


def address_has_house_number(value: str) -> bool:
    return has_house_number(value)


def address_has_suspicious_ocr_text(value: str) -> bool:
    text = normalize_spaces(value)
    if not text:
        return False
    if re.match(r"^[^\u0590-\u05ff]", text) or re.search(r"[A-Za-z\ufffd]", text) or "\x00" in text:
        return True
    if address_has_house_number(text) and len(comparable_text(parse_street_name(text))) <= 1:
        return True

    street_fragment, separator, remainder = text.partition(",")
    return bool(
        separator
        and address_has_house_number(remainder)
        and re.search(r"[\u0590-\u05ff][01](?=[\u0590-\u05ff\s]|$)|^[01](?=[\u0590-\u05ff])", street_fragment)
    )


def address_format(row: dict[str, str], query_quality: str, query: str) -> tuple[str, str]:
    address = normalize_spaces(row.get("address", ""))
    if query_quality != "address_with_locality":
        return "not_street_address_query", query_quality
    if not address:
        return "missing_address", "address field is empty"
    if address_is_only_locality(row):
        return "address_is_only_locality", "address text equals source or target locality"
    if query_has_suspicious_prefix(query) or address_has_suspicious_ocr_text(address):
        return "suspicious_ocr_or_prefix", "address has an OCR-like prefix, character, or digit substitution"
    if not address_has_house_number(address):
        return "missing_house_number", "address lacks a house number"
    return "street_number_locality", "address has street text, house number, and locality"


def locality_for_query(row: dict[str, str], address: str) -> tuple[str, bool]:
    source_locality = normalize_spaces(row["source_locality_name"])
    target_locality = normalize_spaces(row["target_locality_name"])
    address_comparable = comparable_text(address)

    if "|" not in target_locality:
        return target_locality or source_locality, False

    target_parts = [normalize_spaces(part) for part in target_locality.split("|") if normalize_spaces(part)]
    for part in target_parts:
        if comparable_text(part) and comparable_text(part) in address_comparable:
            return part, True

    return source_locality or target_locality, True


def stable_id(query: str) -> str:
    digest = hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]
    return f"gq:{digest}"


def address_is_only_locality(row: dict[str, str]) -> bool:
    address = comparable_text(row["address"])
    if not address:
        return False
    names = {
        comparable_text(row["source_locality_name"]),
        comparable_text(row["target_locality_name"]),
    }
    return address in names


def preferred_query(row: dict[str, str]) -> tuple[str, str, bool]:
    status = row["address_match_status"]
    address = normalize_spaces(row["address"])
    place = normalize_spaces(row["place"])
    locality, locality_needs_review = locality_for_query(row, address)

    if status == "ready" and address:
        if address_is_only_locality(row) and place:
            query = canonical_query(f"{place}, {locality}")
            return query, "place_with_locality", True
        query = canonical_query(f"{address}, {locality}")
        return query, "address_with_locality", locality_needs_review or query_has_suspicious_prefix(query)

    if status == "place_only" and place:
        query = canonical_query(f"{place}, {locality}")
        return query, "place_only", True

    return "", "missing_query", True


def join_values(rows: list[dict[str, str]], field: str) -> str:
    values = sorted({normalize_spaces(row.get(field, "")) for row in rows if normalize_spaces(row.get(field, ""))})
    return "|".join(values)


def join_source_ags_pairs(rows: list[dict[str, str]]) -> str:
    values = sorted(
        {
            f"{normalize_spaces(row.get('source_locality_code', ''))}:{normalize_spaces(row.get('source_ags', ''))}"
            for row in rows
            if normalize_spaces(row.get("source_locality_code", "")) and normalize_spaces(row.get("source_ags", ""))
        }
    )
    return "|".join(values)


def scope_for_unit(format_counts: Counter, target_locality_codes: str) -> str:
    if set(format_counts) == {"street_number_locality"}:
        if target_locality_codes:
            return "proper_address"
        return "excluded_missing_target_locality_code"
    return "excluded_" + "|".join(sorted(format_counts))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    rows = read_csv(GEOCODING_INPUT)
    unit_rows: list[dict[str, Any]] = []
    manual_rows: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        query, quality, manual_review = preferred_query(row)
        unit_id = stable_id(query) if query else ""
        format_status, format_notes = address_format(row, quality, query)
        enriched = {
            **row,
            "geocoding_unit_id": unit_id,
            "geocoder_query": query,
            "geocoder_query_quality": quality,
            "manual_review_required": manual_review,
            "address_format_status": format_status,
            "address_format_notes": format_notes,
        }
        if unit_id:
            grouped[unit_id].append(enriched)
            unit_rows.append(enriched)
        else:
            manual_rows.append(enriched)

    units: list[dict[str, Any]] = []
    for unit_id, members in grouped.items():
        first = members[0]
        status_counts = Counter(row["address_match_status"] for row in members)
        quality_counts = Counter(row["geocoder_query_quality"] for row in members)
        format_counts = Counter(row["address_format_status"] for row in members)
        manual_review_required = any(str(row["manual_review_required"]) == "True" for row in members)
        target_locality_codes = join_values(members, "target_locality_code")
        units.append(
            {
                "geocoding_unit_id": unit_id,
                "geocoder_query": first["geocoder_query"],
                "geocoder_query_quality": "|".join(f"{key}:{quality_counts[key]}" for key in sorted(quality_counts)),
                "manual_review_required": manual_review_required,
                "geocoding_scope": scope_for_unit(format_counts, target_locality_codes),
                "address_format_statuses": "|".join(f"{key}:{format_counts[key]}" for key in sorted(format_counts)),
                "row_count": len(members),
                "elections": join_values(members, "election"),
                "source_row_uids": "|".join(row["source_row_uid"] for row in members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
                "address_match_statuses": "|".join(f"{key}:{status_counts[key]}" for key in sorted(status_counts)),
                "target_locality_codes": target_locality_codes,
                "target_locality_names": join_values(members, "target_locality_name"),
                "source_concentration_codes": join_values(members, "source_concentration_code"),
                "source_ags_values": join_values(members, "source_ags"),
                "source_locality_ags_values": join_source_ags_pairs(members),
                "source_ags_elections": "|".join(
                    sorted({row["election"] for row in members if normalize_spaces(row.get("source_ags", ""))})
                ),
                "address_source_files": join_values(members, "address_source_file"),
                "example_source_row_uid": first["source_row_uid"],
                "example_address": first["address"],
                "example_place": first["place"],
            }
        )

    units.sort(key=lambda item: (str(item["manual_review_required"]), item["geocoder_query"], item["geocoding_unit_id"]))
    unit_rows.sort(key=lambda item: (item["geocoding_unit_id"], item["election"], item["source_row_id"]))
    manual_rows.sort(key=lambda item: (item["election"], item["source_row_id"]))

    unit_fields = [
        "geocoding_unit_id",
        "geocoder_query",
        "geocoder_query_quality",
        "manual_review_required",
        "geocoding_scope",
        "address_format_statuses",
        "row_count",
        "elections",
        "source_row_uids",
        "actual_voters",
        "eligible_voters",
        "address_match_statuses",
        "target_locality_codes",
        "target_locality_names",
        "source_concentration_codes",
        "source_ags_values",
        "source_locality_ags_values",
        "source_ags_elections",
        "address_source_files",
        "example_source_row_uid",
        "example_address",
        "example_place",
    ]
    row_fields = [
        "geocoding_unit_id",
        "geocoder_query",
        "geocoder_query_quality",
        "manual_review_required",
        "address_format_status",
        "address_format_notes",
        *list(rows[0].keys()),
    ] if rows else []

    proper_address_units = [unit for unit in units if unit["geocoding_scope"] == "proper_address"]
    proper_address_unit_ids = {unit["geocoding_unit_id"] for unit in proper_address_units}
    proper_address_rows = [row for row in unit_rows if row["geocoding_unit_id"] in proper_address_unit_ids]
    excluded_address_units = [unit for unit in units if unit["geocoding_scope"] != "proper_address"]

    write_csv(OUT_DIR / "geocoding_work_units.csv", units, unit_fields)
    write_csv(OUT_DIR / "geocoding_work_unit_rows.csv", unit_rows, row_fields)
    write_csv(OUT_DIR / "geocoding_manual_queue.csv", [row for row in unit_rows if row["manual_review_required"]] + manual_rows, row_fields)
    write_csv(OUT_DIR / "geocoding_address_work_units.csv", proper_address_units, unit_fields)
    write_csv(OUT_DIR / "geocoding_address_work_unit_rows.csv", proper_address_rows, row_fields)
    write_csv(OUT_DIR / "geocoding_address_scope_excluded.csv", excluded_address_units, unit_fields)

    summary_rows: list[dict[str, Any]] = []
    for election in sorted({row["election"] for row in rows}, reverse=True):
        election_rows = [row for row in rows if row["election"] == election]
        election_unit_rows = [row for row in unit_rows if row["election"] == election]
        status_counts = Counter(row["address_match_status"] for row in election_rows)
        quality_counts = Counter(row["geocoder_query_quality"] for row in election_unit_rows)
        election_proper_address_rows = [
            row for row in election_unit_rows
            if row["geocoding_unit_id"] in proper_address_unit_ids
        ]
        summary_rows.append(
            {
                "election": election,
                "geocode_needed_rows": len(election_rows),
                "rows_with_geocoder_query": len(election_unit_rows),
                "unique_geocoding_units": len({row["geocoding_unit_id"] for row in election_unit_rows}),
                "proper_address_rows": len(election_proper_address_rows),
                "proper_address_units": len({row["geocoding_unit_id"] for row in election_proper_address_rows}),
                "source_ags_rows": sum(1 for row in election_unit_rows if normalize_spaces(row.get("source_ags", ""))),
                "ready_rows": status_counts["ready"],
                "place_only_rows": status_counts["place_only"],
                "missing_address_rows": status_counts["missing_address_source"] + status_counts["missing_address_value"],
                "address_query_rows": quality_counts["address_with_locality"],
                "place_with_locality_rows": quality_counts["place_with_locality"],
                "place_only_query_rows": quality_counts["place_only"],
            }
        )

    overall = {
        "geocode_needed_rows": len(rows),
        "rows_with_geocoder_query": len(unit_rows),
        "unique_geocoding_units": len(units),
        "proper_address_units": len(proper_address_units),
        "proper_address_rows": len(proper_address_rows),
        "excluded_address_units": len(excluded_address_units),
        "address_format_status_counts": dict(sorted(Counter(row["address_format_status"] for row in unit_rows).items())),
        "source_ags_units": sum(1 for unit in units if normalize_spaces(unit.get("source_ags_values", ""))),
        "source_ags_proper_address_units": sum(
            1 for unit in proper_address_units if normalize_spaces(unit.get("source_ags_values", ""))
        ),
        "manual_review_units": sum(1 for unit in units if unit["manual_review_required"]),
        "manual_review_rows": sum(1 for row in unit_rows if row["manual_review_required"]) + len(manual_rows),
        "rows_without_geocoder_query": len(manual_rows),
        "summary_by_election": summary_rows,
    }
    write_csv(
        OUT_DIR / "geocoding_work_unit_summary.csv",
        summary_rows,
        [
            "election",
            "geocode_needed_rows",
            "rows_with_geocoder_query",
            "unique_geocoding_units",
            "proper_address_rows",
            "proper_address_units",
            "source_ags_rows",
            "ready_rows",
            "place_only_rows",
            "missing_address_rows",
            "address_query_rows",
            "place_with_locality_rows",
            "place_only_query_rows",
        ],
    )
    write_json(OUT_DIR / "geocoding_work_unit_summary.json", overall)

    print(f"geocode_needed_rows={overall['geocode_needed_rows']}")
    print(f"rows_with_geocoder_query={overall['rows_with_geocoder_query']}")
    print(f"unique_geocoding_units={overall['unique_geocoding_units']}")
    print(f"proper_address_units={overall['proper_address_units']}")
    print(f"proper_address_rows={overall['proper_address_rows']}")
    print(f"source_ags_units={overall['source_ags_units']}")
    print(f"source_ags_proper_address_units={overall['source_ags_proper_address_units']}")
    print(f"manual_review_units={overall['manual_review_units']}")
    print(f"manual_review_rows={overall['manual_review_rows']}")
    print(f"rows_without_geocoder_query={overall['rows_without_geocoder_query']}")
    for row in summary_rows:
        print(
            f"{row['election']}: rows={row['geocode_needed_rows']} "
            f"units={row['unique_geocoding_units']} ready={row['ready_rows']} "
            f"place_only={row['place_only_rows']} missing={row['missing_address_rows']}"
        )


if __name__ == "__main__":
    main()
