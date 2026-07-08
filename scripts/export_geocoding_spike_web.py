from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from pipeline_common import PROCESSED_DIR, ROOT, write_json


DEFAULT_INPUT = PROCESSED_DIR / "geocoding" / "geocoding_spike_sample.csv"
DEFAULT_OUTPUT = ROOT / "web" / "geocode-spike" / "sample.json"

KEEP_FIELDS = [
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
    "example_source_row_uid",
    "example_address",
    "example_place",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean_row(row: dict[str, str]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in KEEP_FIELDS}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = [clean_row(row) for row in read_csv(args.input)]
    payload = {
        "generated_at": "",
        "source": str(args.input.relative_to(ROOT) if args.input.is_relative_to(ROOT) else args.input),
        "row_count": len(rows),
        "notes": [
            "Representative GovMap spike sample.",
            "The API token is entered in the browser and is not stored in this file.",
            "Browser output is for review only; successful rows still need explicit approval before production use.",
        ],
        "units": rows,
    }

    write_json(args.output, payload)
    print(f"rows={len(rows)}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
