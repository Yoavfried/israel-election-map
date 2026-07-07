from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline_common import DATA_DIR, PROCESSED_DIR, int_value, normalize_code, normalize_kalpi, normalize_spaces, read_json, write_csv, write_json


MANIFEST_PATH = PROCESSED_DIR / "manifest" / "election_result_resources.json"
OUT_DIR = PROCESSED_DIR / "normalized"

LOCALITY_CODE_FIELDS = ["סמל ישוב"]
LOCALITY_NAME_FIELDS = ["שם ישוב"]
KALPI_FIELDS = ["קלפי", "מספר קלפי", "סמל קלפי"]
ELIGIBLE_FIELDS = ["בזב", "בז''ב"]
ACTUAL_FIELDS = ["מצביעים"]
VALID_FIELDS = ["כשרים"]
INVALID_FIELDS = ["פסולים"]
ADDRESS_FIELDS = ["כתובת"]

ADMIN_FIELDS = {
    "_id",
    "סמל ועדה",
    "ברזל",
    "ריכוז",
    "שופט",
}
CORE_FIELD_NAMES = set(
    LOCALITY_CODE_FIELDS
    + LOCALITY_NAME_FIELDS
    + KALPI_FIELDS
    + ELIGIBLE_FIELDS
    + ACTUAL_FIELDS
    + VALID_FIELDS
    + INVALID_FIELDS
    + ADDRESS_FIELDS
) | ADMIN_FIELDS


def first_value(row: pd.Series, fields: list[str]) -> Any:
    for field in fields:
        if field in row.index and pd.notna(row[field]) and str(row[field]).strip() != "":
            return row[field]
    return ""


def source_path(local_path: str) -> Path:
    return DATA_DIR / local_path


def is_envelope(locality_code: str, locality_name: str) -> bool:
    return locality_code in {"0", "9999"} or "מעטפ" in locality_name


def party_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if column not in CORE_FIELD_NAMES]


def normalize_resource(resource: dict) -> tuple[list[dict], list[dict], list[dict]]:
    election = resource["election"]
    election_number = int(resource["election_number"])
    path = source_path(resource["local_path"])
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")

    parties = party_columns(list(df.columns))
    row_index: list[dict] = []
    party_metadata: list[dict] = []
    wide_rows: list[dict] = []

    for order, (_, source_row) in enumerate(df.iterrows(), start=1):
        source_row_id = normalize_spaces(source_row.get("_id", "")) or str(order)
        locality_code = normalize_code(first_value(source_row, LOCALITY_CODE_FIELDS))
        locality_name = normalize_spaces(first_value(source_row, LOCALITY_NAME_FIELDS))
        kalpi = normalize_kalpi(first_value(source_row, KALPI_FIELDS))
        eligible = int_value(first_value(source_row, ELIGIBLE_FIELDS))
        actual = int_value(first_value(source_row, ACTUAL_FIELDS))
        valid = int_value(first_value(source_row, VALID_FIELDS))
        invalid = int_value(first_value(source_row, INVALID_FIELDS))
        if invalid == 0 and actual and valid and actual >= valid:
            invalid = actual - valid
        source_address = normalize_spaces(first_value(source_row, ADDRESS_FIELDS))
        source_row_uid = f"{election}:{source_row_id}"

        core = {
            "source_row_uid": source_row_uid,
            "election": election,
            "election_number": election_number,
            "source_row_id": source_row_id,
            "source_order": order,
            "source_locality_code": locality_code,
            "source_locality_name": locality_name,
            "source_kalpi": kalpi,
            "eligible_voters": eligible,
            "actual_voters": actual,
            "valid_votes": valid,
            "invalid_votes": invalid,
            "source_address": source_address,
            "is_envelope": is_envelope(locality_code, locality_name),
        }
        row_index.append(core)

        wide = dict(core)
        for party in parties:
            wide[party] = int_value(source_row.get(party, ""))
        wide_rows.append(wide)

    for party in parties:
        party_metadata.append(
            {
                "election": election,
                "election_number": election_number,
                "ballot_letter": party,
                "source_column": party,
                "total_votes": int(df[party].map(int_value).sum()),
            }
        )

    wide_path = OUT_DIR / "ballot_votes_wide" / f"{election.lower()}_ballot_votes.csv"
    write_csv(wide_path, wide_rows, list(wide_rows[0].keys()))
    return row_index, party_metadata, [
        {
            "election": election,
            "election_number": election_number,
            "source_path": str(path.relative_to(DATA_DIR.parent)).replace("\\", "/"),
            "rows": len(df),
            "party_columns": len(parties),
            "actual_voters": sum(row["actual_voters"] for row in row_index),
            "valid_votes": sum(row["valid_votes"] for row in row_index),
            "invalid_votes": sum(row["invalid_votes"] for row in row_index),
            "envelope_rows": sum(1 for row in row_index if row["is_envelope"]),
            "envelope_actual_voters": sum(row["actual_voters"] for row in row_index if row["is_envelope"]),
        }
    ]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    manifest = read_json(MANIFEST_PATH)
    all_rows: list[dict] = []
    all_parties: list[dict] = []
    summaries: list[dict] = []

    for resource in sorted(manifest, key=lambda item: int(item["election_number"]), reverse=True):
        rows, parties, summary = normalize_resource(resource)
        all_rows.extend(rows)
        all_parties.extend(parties)
        summaries.extend(summary)

    row_fields = [
        "source_row_uid",
        "election",
        "election_number",
        "source_row_id",
        "source_order",
        "source_locality_code",
        "source_locality_name",
        "source_kalpi",
        "eligible_voters",
        "actual_voters",
        "valid_votes",
        "invalid_votes",
        "source_address",
        "is_envelope",
    ]
    party_fields = ["election", "election_number", "ballot_letter", "source_column", "total_votes"]
    summary_fields = [
        "election",
        "election_number",
        "source_path",
        "rows",
        "party_columns",
        "actual_voters",
        "valid_votes",
        "invalid_votes",
        "envelope_rows",
        "envelope_actual_voters",
    ]

    write_csv(OUT_DIR / "ballot_rows.csv", all_rows, row_fields)
    write_csv(OUT_DIR / "party_columns.csv", all_parties, party_fields)
    write_csv(OUT_DIR / "normalization_summary.csv", summaries, summary_fields)
    write_json(OUT_DIR / "normalization_summary.json", summaries)

    print(f"normalized_rows={len(all_rows)}")
    print(f"party_columns={len(all_parties)}")
    for summary in summaries:
        print(
            f"{summary['election']}: rows={summary['rows']} actual={summary['actual_voters']} "
            f"envelope_rows={summary['envelope_rows']}"
        )


if __name__ == "__main__":
    main()
