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
    values = sorted({normalize_spaces(row[field]) for row in rows if normalize_spaces(row[field])})
    return "|".join(values)


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
        enriched = {
            **row,
            "geocoding_unit_id": unit_id,
            "geocoder_query": query,
            "geocoder_query_quality": quality,
            "manual_review_required": manual_review,
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
        manual_review_required = any(str(row["manual_review_required"]) == "True" for row in members)
        units.append(
            {
                "geocoding_unit_id": unit_id,
                "geocoder_query": first["geocoder_query"],
                "geocoder_query_quality": "|".join(f"{key}:{quality_counts[key]}" for key in sorted(quality_counts)),
                "manual_review_required": manual_review_required,
                "row_count": len(members),
                "elections": join_values(members, "election"),
                "source_row_uids": "|".join(row["source_row_uid"] for row in members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
                "address_match_statuses": "|".join(f"{key}:{status_counts[key]}" for key in sorted(status_counts)),
                "target_locality_codes": join_values(members, "target_locality_code"),
                "target_locality_names": join_values(members, "target_locality_name"),
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
        "row_count",
        "elections",
        "source_row_uids",
        "actual_voters",
        "eligible_voters",
        "address_match_statuses",
        "target_locality_codes",
        "target_locality_names",
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
        *list(rows[0].keys()),
    ] if rows else []

    write_csv(OUT_DIR / "geocoding_work_units.csv", units, unit_fields)
    write_csv(OUT_DIR / "geocoding_work_unit_rows.csv", unit_rows, row_fields)
    write_csv(OUT_DIR / "geocoding_manual_queue.csv", [row for row in unit_rows if row["manual_review_required"]] + manual_rows, row_fields)

    summary_rows: list[dict[str, Any]] = []
    for election in sorted({row["election"] for row in rows}, reverse=True):
        election_rows = [row for row in rows if row["election"] == election]
        election_unit_rows = [row for row in unit_rows if row["election"] == election]
        status_counts = Counter(row["address_match_status"] for row in election_rows)
        quality_counts = Counter(row["geocoder_query_quality"] for row in election_unit_rows)
        summary_rows.append(
            {
                "election": election,
                "geocode_needed_rows": len(election_rows),
                "rows_with_geocoder_query": len(election_unit_rows),
                "unique_geocoding_units": len({row["geocoding_unit_id"] for row in election_unit_rows}),
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
