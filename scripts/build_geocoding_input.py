from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pipeline_common import MANUAL_DIR, PROCESSED_DIR, int_value, normalize_kalpi, normalize_spaces, write_csv, write_json


ASSIGNMENT_PLAN = PROCESSED_DIR / "assignments" / "ballot_assignment_plan.csv"
POLLING_PLACE_ADDRESSES = PROCESSED_DIR / "addresses" / "polling_place_addresses.csv"
ROW_OVERRIDES = MANUAL_DIR / "polling_place_assignment_overrides.csv"
OUT_DIR = PROCESSED_DIR / "geocoding"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def base_kalpi(kalpi: str) -> str:
    kalpi = normalize_kalpi(kalpi)
    return kalpi.split(".", 1)[0] if "." in kalpi else kalpi


def build_address_indexes(rows: list[dict[str, str]]):
    by_uid: dict[tuple[str, str], dict] = {}
    by_exact: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    by_base: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for row in rows:
        election = row["election"]
        source_row_id = row["source_row_id"]
        code = row["source_locality_code"]
        kalpi = normalize_kalpi(row["source_kalpi"])
        if source_row_id:
            by_uid[(election, source_row_id)] = row
        if code and kalpi:
            by_exact[(election, code, kalpi)].append(row)
            by_base[(election, code, base_kalpi(kalpi))].append(row)
    return by_uid, by_exact, by_base


def unique_candidate(candidates: list[dict]) -> dict | None:
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        return None
    with_address = [candidate for candidate in candidates if candidate["address"]]
    unique_queries = {candidate["address_query"] for candidate in with_address}
    if len(unique_queries) == 1:
        return with_address[0]
    return None


def find_address(row: dict[str, str], by_uid, by_exact, by_base) -> tuple[dict | None, str]:
    election = row["election"]
    source_row_id = row["source_row_id"]
    code = row["source_locality_code"]
    kalpi = normalize_kalpi(row["source_kalpi"])

    if (election, source_row_id) in by_uid and election in {"K17", "K18"}:
        return by_uid[(election, source_row_id)], "source_row_id"

    exact = unique_candidate(by_exact.get((election, code, kalpi), []))
    if exact:
        return exact, "locality_code_kalpi"

    base = unique_candidate(by_base.get((election, code, base_kalpi(kalpi)), []))
    if base:
        return base, "locality_code_base_kalpi"

    return None, "no_match"


def status_for_address(address: dict | None) -> str:
    if not address:
        return "missing_address_source"
    if address["address"]:
        return "ready"
    if address["place"]:
        return "place_only"
    return "missing_address_value"


def address_handling_overrides(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        handling = normalize_spaces(row.get("address_handling", ""))
        if not handling:
            continue
        if handling not in {"component_locality", "retarget_locality"}:
            raise ValueError(f"Unsupported polling-place address handling: {row}")
        source_row_uid = normalize_spaces(row.get("source_row_uid", ""))
        if not source_row_uid:
            raise ValueError(f"Address handling requires source_row_uid: {row}")
        if source_row_uid in output:
            raise ValueError(f"Duplicate address-handling override: {source_row_uid}")
        output[source_row_uid] = row
    return output


def effective_address_query(address: str, place: str, locality_name: str) -> str:
    address = normalize_spaces(address)
    place = normalize_spaces(place)
    locality_name = normalize_spaces(locality_name)
    if address:
        return ", ".join(value for value in [address, locality_name] if value)
    return ", ".join(value for value in [place, locality_name] if value)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    assignment_rows = [
        row for row in read_csv(ASSIGNMENT_PLAN)
        if row["assignment_method"] == "direct_address_geocode_needed"
    ]
    address_rows = read_csv(POLLING_PLACE_ADDRESSES)
    handling_by_uid = address_handling_overrides(read_csv(ROW_OVERRIDES))
    by_uid, by_exact, by_base = build_address_indexes(address_rows)

    output: list[dict[str, Any]] = []
    for assignment in assignment_rows:
        address, match_method = find_address(assignment, by_uid, by_exact, by_base)
        handling_row = handling_by_uid.get(assignment["source_row_uid"])
        address_handling = normalize_spaces(handling_row.get("address_handling", "")) if handling_row else ""
        source_address = address["address"] if address else ""
        effective_address = "" if address_handling == "component_locality" else source_address
        effective_place = address["place"] if address else ""
        effective = {**address, "address": effective_address, "place": effective_place} if address else None
        status = status_for_address(effective)
        output.append(
            {
                "geocode_key": assignment["source_row_uid"],
                **assignment,
                "address_match_status": status,
                "address_match_method": match_method,
                "address": effective_address,
                "place": effective_place,
                "address_query": (
                    effective_address_query(
                        effective_address,
                        effective_place,
                        assignment["target_locality_name"],
                    )
                    if address_handling
                    else (address["address_query"] if address else "")
                ),
                "source_address_before_handling": source_address if address_handling else "",
                "address_handling": address_handling,
                "address_source_file": address["source_file"] if address else "",
                "address_source_row_id": address["source_row_id"] if address else "",
                "source_concentration_code": address.get("source_concentration_code", "") if address else "",
                "source_ags": address.get("source_ags", "") if address else "",
            }
        )

    fields = list(output[0].keys()) if output else []
    write_csv(OUT_DIR / "geocoding_input.csv", output, fields)

    summary = []
    for election in sorted({row["election"] for row in output}, reverse=True):
        election_rows = [row for row in output if row["election"] == election]
        statuses = Counter(row["address_match_status"] for row in election_rows)
        summary.append(
            {
                "election": election,
                "geocode_needed_rows": len(election_rows),
                "ready_rows": statuses["ready"],
                "place_only_rows": statuses["place_only"],
                "missing_address_rows": statuses["missing_address_source"] + statuses["missing_address_value"],
                "missing_address_actual_voters": sum(
                    int_value(row["actual_voters"])
                    for row in election_rows
                    if row["address_match_status"] in {"missing_address_source", "missing_address_value"}
                ),
                "place_only_actual_voters": sum(
                    int_value(row["actual_voters"])
                    for row in election_rows
                    if row["address_match_status"] == "place_only"
                ),
            }
        )
    write_csv(
        OUT_DIR / "geocoding_input_summary.csv",
        summary,
        [
            "election",
            "geocode_needed_rows",
            "ready_rows",
            "place_only_rows",
            "missing_address_rows",
            "missing_address_actual_voters",
            "place_only_actual_voters",
        ],
    )
    write_json(OUT_DIR / "geocoding_input_summary.json", summary)

    missing = [row for row in output if row["address_match_status"] != "ready"]
    write_csv(OUT_DIR / "geocoding_input_not_ready.csv", missing, fields)

    print(f"geocoding_input_rows={len(output)}")
    for row in summary:
        print(
            f"{row['election']}: ready={row['ready_rows']} place_only={row['place_only_rows']} "
            f"missing={row['missing_address_rows']} missing_actual={row['missing_address_actual_voters']}"
        )


if __name__ == "__main__":
    main()
