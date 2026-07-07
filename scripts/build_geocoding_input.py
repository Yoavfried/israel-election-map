from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pipeline_common import PROCESSED_DIR, int_value, normalize_kalpi, write_csv, write_json


ASSIGNMENT_PLAN = PROCESSED_DIR / "assignments" / "ballot_assignment_plan.csv"
POLLING_PLACE_ADDRESSES = PROCESSED_DIR / "addresses" / "polling_place_addresses.csv"
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


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    assignment_rows = [
        row for row in read_csv(ASSIGNMENT_PLAN)
        if row["assignment_method"] == "direct_address_geocode_needed"
    ]
    address_rows = read_csv(POLLING_PLACE_ADDRESSES)
    by_uid, by_exact, by_base = build_address_indexes(address_rows)

    output: list[dict[str, Any]] = []
    for assignment in assignment_rows:
        address, match_method = find_address(assignment, by_uid, by_exact, by_base)
        status = status_for_address(address)
        output.append(
            {
                "geocode_key": assignment["source_row_uid"],
                **assignment,
                "address_match_status": status,
                "address_match_method": match_method,
                "address": address["address"] if address else "",
                "place": address["place"] if address else "",
                "address_query": address["address_query"] if address else "",
                "address_source_file": address["source_file"] if address else "",
                "address_source_row_id": address["source_row_id"] if address else "",
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
