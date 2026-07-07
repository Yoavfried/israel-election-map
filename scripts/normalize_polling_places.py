from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from pipeline_common import PROCESSED_DIR, RAW_DIR, int_value, normalize_code, normalize_kalpi, normalize_spaces, write_csv, write_json


OUT_DIR = PROCESSED_DIR / "addresses"
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")

ADDRESS_SOURCES = {
    "K25": RAW_DIR / "election-25_kalpi-places_kalpies_list_10_7_nagish.xlsx",
    "K21": RAW_DIR / "archive_knesset21_kalpies_full_report.xls",
    "K20": RAW_DIR / "archive_knesset20_tell_the_polls_9_3.xls",
    "K19": RAW_DIR / "archive_knesset19_all_stations.pdf",
    "K18": PROCESSED_DIR / "k18_polling_places_resolved.csv",
    "K17": PROCESSED_DIR / "normalized" / "ballot_rows.csv",
}

FIELDS = [
    "address_uid",
    "election",
    "source_file",
    "source_row_id",
    "source_locality_code",
    "source_locality_name",
    "source_kalpi",
    "source_eligible_voters",
    "address",
    "place",
    "address_query",
    "source_status",
]


def clean(value: Any) -> str:
    return normalize_spaces(value).replace("\u00ad", "-")


def address_query(address: str, locality_name: str, place: str = "") -> str:
    parts = [clean(address), clean(locality_name)]
    query = ", ".join(part for part in parts if part)
    if query:
        return query
    return ", ".join(part for part in [clean(place), clean(locality_name)] if part)


def row(
    election: str,
    source_file: Path,
    source_row_id: Any,
    locality_code: Any,
    locality_name: Any,
    kalpi: Any,
    eligible: Any,
    address: Any,
    place: Any,
    source_status: str = "addressed",
) -> dict[str, Any]:
    code = normalize_code(locality_code)
    name = clean(locality_name)
    kalpi_norm = normalize_kalpi(kalpi)
    address_text = clean(address)
    place_text = clean(place)
    source_id = clean(source_row_id)
    return {
        "address_uid": f"{election}:{source_id}" if source_id else "",
        "election": election,
        "source_file": str(source_file.relative_to(RAW_DIR.parent)).replace("\\", "/"),
        "source_row_id": source_id,
        "source_locality_code": code,
        "source_locality_name": name,
        "source_kalpi": kalpi_norm,
        "source_eligible_voters": int_value(eligible),
        "address": address_text,
        "place": place_text,
        "address_query": address_query(address_text, name, place_text),
        "source_status": source_status,
    }


def read_excel_source(election: str, path: Path) -> list[dict[str, Any]]:
    df = pd.read_excel(path, sheet_name="DataSheet", dtype=str).fillna("")
    rows = []
    for index, source in df.iterrows():
        rows.append(
            row(
                election=election,
                source_file=path,
                source_row_id=index + 1,
                locality_code=source.get("סמל ישוב בחירות", ""),
                locality_name=source.get("שם ישוב בחירות", ""),
                kalpi=source.get("סמל קלפי", ""),
                eligible=source.get("בוחרי כנסת בפועל", source.get("בוחרי כנסת", "")),
                address=source.get("כתובת קלפי", ""),
                place=source.get("מקום קלפי", ""),
            )
        )
    return rows


def fix_rtl_token(token: str) -> str:
    if not HEBREW_RE.search(token):
        return token
    match = re.match(r"^(\d+[א-ת]?),(.*)$", token)
    if match:
        return f"{match.group(2)[::-1]},{match.group(1)}"
    return token[::-1]


def fix_rtl_cell(value: Any) -> str:
    text = clean(value)
    if not HEBREW_RE.search(text):
        return text
    tokens = [fix_rtl_token(token) for token in text.split()]
    return " ".join(reversed(tokens))


def read_k19_pdf(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                if not table:
                    continue
                for table_row in table[1:]:
                    if not table_row or len(table_row) < 11:
                        continue
                    eligible = table_row[1]
                    place = table_row[4]
                    address = table_row[5]
                    kalpi = table_row[6]
                    locality_name = table_row[7]
                    locality_code = table_row[8]
                    if not normalize_code(locality_code) or not normalize_kalpi(kalpi):
                        continue
                    rows.append(
                        row(
                            election="K19",
                            source_file=path,
                            source_row_id=f"p{page_number}:{len(rows) + 1}",
                            locality_code=locality_code,
                            locality_name=fix_rtl_cell(locality_name),
                            kalpi=kalpi,
                            eligible=eligible,
                            address=fix_rtl_cell(address),
                            place=fix_rtl_cell(place),
                        )
                    )
    return rows


def read_k18_resolved(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for source in csv.DictReader(handle):
            if source["resolved_status"] != "matched":
                continue
            rows.append(
                row(
                    election="K18",
                    source_file=path,
                    source_row_id=source["official_row_id"],
                    locality_code=source["official_locality_code"],
                    locality_name=source["official_locality_name"],
                    kalpi=source["official_kalpi"],
                    eligible=source["official_eligible"],
                    address=source["address"],
                    place=source["place"],
                )
            )
    return rows


def read_k17_result_addresses(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for source in csv.DictReader(handle):
            if source["election"] != "K17" or not source["source_address"]:
                continue
            rows.append(
                row(
                    election="K17",
                    source_file=path,
                    source_row_id=source["source_row_id"],
                    locality_code=source["source_locality_code"],
                    locality_name=source["source_locality_name"],
                    kalpi=source["source_kalpi"],
                    eligible=source["eligible_voters"],
                    address=source["source_address"],
                    place="",
                )
            )
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    rows: list[dict[str, Any]] = []
    missing_sources: list[dict[str, Any]] = []

    for election in ["K25", "K21", "K20"]:
        path = ADDRESS_SOURCES[election]
        if path.exists():
            rows.extend(read_excel_source(election, path))
        else:
            missing_sources.append({"election": election, "expected_path": str(path), "reason": "missing_file"})

    if ADDRESS_SOURCES["K19"].exists():
        rows.extend(read_k19_pdf(ADDRESS_SOURCES["K19"]))
    else:
        missing_sources.append({"election": "K19", "expected_path": str(ADDRESS_SOURCES["K19"]), "reason": "missing_file"})

    if ADDRESS_SOURCES["K18"].exists():
        rows.extend(read_k18_resolved(ADDRESS_SOURCES["K18"]))
    else:
        missing_sources.append({"election": "K18", "expected_path": str(ADDRESS_SOURCES["K18"]), "reason": "missing_file"})

    if ADDRESS_SOURCES["K17"].exists():
        rows.extend(read_k17_result_addresses(ADDRESS_SOURCES["K17"]))
    else:
        missing_sources.append({"election": "K17", "expected_path": str(ADDRESS_SOURCES["K17"]), "reason": "missing_file"})

    for election in ["K24", "K23", "K22"]:
        missing_sources.append(
            {
                "election": election,
                "expected_path": "",
                "reason": "election_specific_address_file_not_in_raw_data",
            }
        )

    rows.sort(key=lambda item: (item["election"], item["source_locality_code"], item["source_kalpi"], item["source_row_id"]))
    write_csv(OUT_DIR / "polling_place_addresses.csv", rows, FIELDS)
    write_csv(OUT_DIR / "missing_address_sources.csv", missing_sources, ["election", "expected_path", "reason"])

    summary = []
    for election in sorted({row["election"] for row in rows}, reverse=True):
        election_rows = [row for row in rows if row["election"] == election]
        summary.append(
            {
                "election": election,
                "address_rows": len(election_rows),
                "rows_with_address": sum(1 for row in election_rows if row["address"]),
                "rows_place_only": sum(1 for row in election_rows if not row["address"] and row["place"]),
            }
        )
    write_csv(OUT_DIR / "polling_place_address_summary.csv", summary, ["election", "address_rows", "rows_with_address", "rows_place_only"])
    write_json(OUT_DIR / "polling_place_address_summary.json", summary)

    print(f"address_rows={len(rows)}")
    for item in summary:
        print(
            f"{item['election']}: rows={item['address_rows']} "
            f"with_address={item['rows_with_address']} place_only={item['rows_place_only']}"
        )
    if missing_sources:
        print("missing_sources=" + ", ".join(item["election"] for item in missing_sources))


if __name__ == "__main__":
    main()
