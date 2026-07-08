from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from pipeline_common import PROCESSED_DIR, int_value, write_csv, write_json


WORK_UNITS = PROCESSED_DIR / "geocoding" / "geocoding_work_units.csv"
OUT_DIR = PROCESSED_DIR / "geocoding"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def has_suspicious_prefix(row: dict[str, str]) -> bool:
    return bool(re.match(r"^[\s\"'`,._-]+", row["geocoder_query"]))


def has_quality(row: dict[str, str], quality: str) -> bool:
    return quality in row["geocoder_query_quality"]


def has_election(row: dict[str, str], election: str) -> bool:
    return election in {item.strip() for item in row["elections"].split("|") if item.strip()}


def is_manual(row: dict[str, str]) -> bool:
    return str(row["manual_review_required"]).lower() == "true"


def choose(rows: list[dict[str, str]], limit: int, sort_key) -> list[dict[str, str]]:
    return sorted(rows, key=sort_key)[:limit]


def add_category(
    selected: dict[str, dict[str, Any]],
    category_counts: dict[str, int],
    category: str,
    reason: str,
    rows: list[dict[str, str]],
) -> None:
    for row in rows:
        unit_id = row["geocoding_unit_id"]
        if unit_id not in selected:
            selected[unit_id] = {**row, "sample_categories": [], "sample_reasons": []}
        selected[unit_id]["sample_categories"].append(category)
        selected[unit_id]["sample_reasons"].append(reason)
        category_counts[category] += 1


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=WORK_UNITS)
    parser.add_argument("--output", type=Path, default=OUT_DIR / "geocoding_spike_sample.csv")
    parser.add_argument("--summary-output", type=Path, default=OUT_DIR / "geocoding_spike_sample_summary.json")
    parser.add_argument("--per-category", type=int, default=8)
    args = parser.parse_args()

    rows = read_csv(args.input)
    selected: dict[str, dict[str, Any]] = {}
    category_counts: dict[str, int] = defaultdict(int)
    per_category = max(args.per_category, 1)

    by_query = lambda row: (row["geocoder_query"], row["geocoding_unit_id"])
    by_voters_desc = lambda row: (-int_value(row["actual_voters"]), row["geocoder_query"], row["geocoding_unit_id"])
    by_rows_desc = lambda row: (-int_value(row["row_count"]), row["geocoder_query"], row["geocoding_unit_id"])

    add_category(
        selected,
        category_counts,
        "clean_full_address",
        "non-manual full address query",
        choose(
            [
                row for row in rows
                if has_quality(row, "address_with_locality") and not is_manual(row) and "|" not in row["target_locality_names"]
            ],
            per_category,
            by_voters_desc,
        ),
    )
    add_category(
        selected,
        category_counts,
        "high_reuse",
        "same geocoder query contributes many ballot rows",
        choose(rows, per_category, by_rows_desc),
    )
    add_category(
        selected,
        category_counts,
        "place_with_locality",
        "address field is effectively only locality, so query uses place plus locality",
        choose([row for row in rows if has_quality(row, "place_with_locality")], per_category, by_voters_desc),
    )
    for election in ["K17", "K18", "K19"]:
        add_category(
            selected,
            category_counts,
            f"place_only_{election.lower()}",
            f"{election} place-only query",
            choose(
                [row for row in rows if has_quality(row, "place_only") and has_election(row, election)],
                per_category,
                by_voters_desc,
            ),
        )
    add_category(
        selected,
        category_counts,
        "composite_locality",
        "historical split/merge target has multiple current localities",
        choose([row for row in rows if "|" in row["target_locality_names"]], per_category, by_voters_desc),
    )
    add_category(
        selected,
        category_counts,
        "suspicious_ocr_prefix",
        "query starts with punctuation or OCR artifact",
        choose([row for row in rows if has_suspicious_prefix(row)], per_category, by_query),
    )
    add_category(
        selected,
        category_counts,
        "manual_review_high_voters",
        "manual-review unit with many actual voters",
        choose([row for row in rows if is_manual(row)], per_category, by_voters_desc),
    )
    add_category(
        selected,
        category_counts,
        "highest_voters",
        "largest actual-voter contribution among all units",
        choose(rows, per_category, by_voters_desc),
    )

    output = []
    for row in selected.values():
        output.append(
            {
                **row,
                "sample_category": "|".join(sorted(set(row["sample_categories"]))),
                "sample_reason": "|".join(sorted(set(row["sample_reasons"]))),
            }
        )
    output.sort(key=lambda row: (row["sample_category"], -int_value(row["actual_voters"]), row["geocoder_query"]))

    fields = [
        "geocoding_unit_id",
        "geocoder_query",
        "geocoder_query_quality",
        "manual_review_required",
        "sample_category",
        "sample_reason",
        "row_count",
        "elections",
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
    write_csv(args.output, [{field: row.get(field, "") for field in fields} for row in output], fields)
    write_json(
        args.summary_output,
        {
            "input": str(args.input),
            "output": str(args.output),
            "per_category": per_category,
            "selected_unique_units": len(output),
            "category_selection_events": dict(sorted(category_counts.items())),
        },
    )

    print(f"selected_unique_units={len(output)}")
    for category, count in sorted(category_counts.items()):
        print(f"{category}={count}")


if __name__ == "__main__":
    main()
