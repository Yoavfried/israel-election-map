"""Compare K17 locality-only polling-place rows with K18 polling places.

K17 ballot-box identifiers in the digital results are stored at ten times the
printed value (for example, 10 means 1 and 81 means 8.1).  This comparison
keeps that raw identifier and derives a separate printed identifier for the
K18 join.  A same-number K18 match is a review candidate, not proof that the
physical polling place was unchanged between elections.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UNITS = ROOT / "data/processed/addresses/polling_place_locality_only_no_place_units.csv"
DEFAULT_ROWS = ROOT / "data/processed/addresses/polling_place_address_quality_geocoding_rows.csv"
DEFAULT_K18 = ROOT / "data/processed/k18_polling_places_resolved.csv"
DEFAULT_K17_SCAN = ROOT / "data/manual/manual_k17_scanned_place_names.csv"
DEFAULT_DETAIL_OUT = ROOT / "data/processed/addresses/k17_locality_only_k18_candidates.csv"
DEFAULT_SUMMARY_OUT = ROOT / "data/processed/addresses/k17_locality_only_k18_summary.csv"
DEFAULT_GROUP_OUT = ROOT / "data/processed/addresses/k17_locality_only_k18_candidate_groups.csv"


DETAIL_FIELDS = [
    "geocoding_unit_id",
    "k17_source_row_uid",
    "k17_source_locality_name",
    "k17_target_locality_code",
    "k17_target_locality_name",
    "k17_address_field",
    "k17_kalpi_raw",
    "k17_kalpi_printed",
    "k17_actual_voters",
    "comparison_status",
    "comparison_method",
    "candidate_confidence",
    "k18_candidate_count",
    "k18_official_row_ids",
    "k18_locality_codes",
    "k18_locality_names",
    "k18_kalpis",
    "k18_addresses",
    "k18_places",
    "k18_pdf_pages",
    "k18_actual_voters",
    "k17_scan_verified",
    "k17_scan_source",
    "k17_scan_address",
    "k17_scan_place",
    "interpretation",
]

SUMMARY_FIELDS = [
    "geocoding_unit_id",
    "k17_source_locality_names",
    "k17_target_locality_codes",
    "k17_target_locality_names",
    "k17_row_count",
    "k18_exact_station_matches",
    "k18_exact_match_rate",
    "k18_ambiguous_matches",
    "k18_no_exact_station",
    "k18_no_exact_k17_kalpis",
    "k18_matches_with_place",
    "unique_k18_candidate_places",
    "k17_scan_verified_rows",
    "interpretation",
]

GROUP_FIELDS = [
    "geocoding_unit_id",
    "k17_source_locality_name",
    "k17_target_locality_name",
    "comparison_status",
    "candidate_confidence",
    "k18_locality_name",
    "k18_address",
    "k18_place",
    "k17_row_count",
    "k17_kalpis_raw",
    "k17_kalpis_printed",
    "k17_source_row_uids",
    "k18_pdf_pages",
    "interpretation",
]


def clean(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\u00ad", "-").replace("\u200f", "").replace("\u200e", "")
    return re.sub(r"\s+", " ", text).strip()


def normalized_name(value: object) -> str:
    text = clean(value)
    text = text.replace("׳", "'").replace("״", '"')
    text = re.sub(r"[-‐‑–—_]", " ", text)
    text = re.sub(r"[\"'(),.]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalized_code(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        return str(int(Decimal(text)))
    except (InvalidOperation, ValueError):
        return text


def normalized_kalpi(value: object) -> str:
    text = clean(value).replace(",", ".")
    if not text:
        return ""
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text
    rendered = format(number.normalize(), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def k17_printed_kalpi(value: object) -> str:
    text = clean(value).replace(",", ".")
    if not text:
        return ""
    try:
        number = Decimal(text) / Decimal(10)
    except InvalidOperation:
        return ""
    return normalized_kalpi(number)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def joined(values: Iterable[object], separator: str = " | ") -> str:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = clean(value)
        if not text or text == "0" or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return separator.join(result)


def source_result_id(source_row_uid: str) -> str:
    return clean(source_row_uid).partition(":")[2]


def candidate_locality_names(row: dict[str, str]) -> list[str]:
    values: list[str] = []
    address = clean(row.get("address"))
    source_name = clean(row.get("source_locality_name"))
    if address and normalized_name(address) != normalized_name(source_name):
        values.append(address)
    values.extend(part.strip() for part in clean(row.get("target_locality_name")).split("|") if part.strip())
    values.append(source_name)
    return [value for value in values if value]


def build_k18_indexes(rows: list[dict[str, str]]) -> tuple[dict[tuple[str, str], list[dict[str, str]]], dict[tuple[str, str], list[dict[str, str]]]]:
    by_code: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_name: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for row in rows:
        row_id = clean(row.get("official_row_id"))
        if row_id and row_id in seen:
            continue
        if row_id:
            seen.add(row_id)
        kalpi = normalized_kalpi(row.get("official_kalpi"))
        code = normalized_code(row.get("official_locality_code"))
        name = normalized_name(row.get("official_locality_name"))
        if kalpi and code:
            by_code[(code, kalpi)].append(row)
        if kalpi and name:
            by_name[(name, kalpi)].append(row)
    return by_code, by_name


def deduplicate_candidates(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        key = clean(row.get("official_row_id")) or "\x1f".join(
            [
                clean(row.get("official_locality_code")),
                clean(row.get("official_kalpi")),
                clean(row.get("address")),
                clean(row.get("place")),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def compare(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    units = read_csv(args.units)
    unit_by_id = {row["geocoding_unit_id"]: row for row in units}
    unit_ids = set(unit_by_id)
    k17_rows = [
        row
        for row in read_csv(args.rows)
        if row.get("election") == "K17" and row.get("geocoding_unit_id") in unit_ids
    ]
    k18_by_code, k18_by_name = build_k18_indexes(read_csv(args.k18))
    scan_by_result_id = {
        clean(row.get("source_result_row_id")): row
        for row in read_csv(args.k17_scan)
        if row.get("election") == "K17"
    }

    details: list[dict[str, object]] = []
    for row in k17_rows:
        kalpi_printed = k17_printed_kalpi(row.get("source_kalpi"))
        target_code = normalized_code(row.get("target_locality_code"))
        candidates: list[dict[str, str]] = []
        method = ""
        if target_code:
            candidates = list(k18_by_code.get((target_code, kalpi_printed), []))
            if candidates:
                method = "same_target_locality_code_and_scaled_kalpi"
        if not candidates:
            for locality_name in candidate_locality_names(row):
                candidates.extend(k18_by_name.get((normalized_name(locality_name), kalpi_printed), []))
            candidates = deduplicate_candidates(candidates)
            if candidates:
                method = "same_locality_name_and_scaled_kalpi"

        candidates = deduplicate_candidates(candidates)
        scan = scan_by_result_id.get(source_result_id(row.get("source_row_uid", "")))
        scan_verified = bool(scan and (clean(scan.get("place")) not in {"", "0"} or clean(scan.get("scanned_address")) not in {"", "0"}))

        if len(candidates) == 1:
            status = "one_exact_k18_station_candidate"
            confidence = "lead_only"
            interpretation = "Same locality and printed station number in K18; use only to guide K17 scan review because polling places can change."
        elif len(candidates) > 1:
            status = "multiple_exact_k18_station_candidates"
            confidence = "low"
            interpretation = "More than one K18 row fits; do not select a building without K17 scan evidence."
        else:
            status = "no_exact_k18_station_candidate"
            confidence = "none"
            interpretation = "No same-number K18 candidate; inspect the K17 scan or a K16 source."

        if scan_verified:
            confidence = "high"
            interpretation = "Building text is directly transcribed from the original K17 polling-place scan."

        details.append(
            {
                "geocoding_unit_id": row.get("geocoding_unit_id", ""),
                "k17_source_row_uid": row.get("source_row_uid", ""),
                "k17_source_locality_name": row.get("source_locality_name", ""),
                "k17_target_locality_code": row.get("target_locality_code", ""),
                "k17_target_locality_name": row.get("target_locality_name", ""),
                "k17_address_field": row.get("address", ""),
                "k17_kalpi_raw": row.get("source_kalpi", ""),
                "k17_kalpi_printed": kalpi_printed,
                "k17_actual_voters": row.get("actual_voters", ""),
                "comparison_status": status,
                "comparison_method": method,
                "candidate_confidence": confidence,
                "k18_candidate_count": len(candidates),
                "k18_official_row_ids": joined(candidate.get("official_row_id") for candidate in candidates),
                "k18_locality_codes": joined(candidate.get("official_locality_code") for candidate in candidates),
                "k18_locality_names": joined(candidate.get("official_locality_name") for candidate in candidates),
                "k18_kalpis": joined(candidate.get("official_kalpi") for candidate in candidates),
                "k18_addresses": joined((candidate.get("address") for candidate in candidates), separator=" || "),
                "k18_places": joined((candidate.get("place") for candidate in candidates), separator=" || "),
                "k18_pdf_pages": joined(candidate.get("pdf_page") for candidate in candidates),
                "k18_actual_voters": joined(candidate.get("official_actual") for candidate in candidates),
                "k17_scan_verified": str(scan_verified),
                "k17_scan_source": clean(scan.get("pdf_source")) if scan else "",
                "k17_scan_address": clean(scan.get("scanned_address")) if scan and clean(scan.get("scanned_address")) != "0" else "",
                "k17_scan_place": clean(scan.get("place")) if scan and clean(scan.get("place")) != "0" else "",
                "interpretation": interpretation,
            }
        )

    details.sort(
        key=lambda row: (
            normalized_name(row["k17_source_locality_name"]),
            Decimal(clean(row["k17_kalpi_printed"]) or "0"),
            clean(row["k17_source_row_uid"]),
        )
    )

    details_by_unit: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in details:
        details_by_unit[clean(row["geocoding_unit_id"])].append(row)

    summaries: list[dict[str, object]] = []
    for unit_id, unit in unit_by_id.items():
        rows = details_by_unit.get(unit_id, [])
        exact = sum(int(row["k18_candidate_count"]) == 1 for row in rows)
        ambiguous = sum(int(row["k18_candidate_count"]) > 1 for row in rows)
        no_exact = [row for row in rows if int(row["k18_candidate_count"]) == 0]
        with_place = sum(bool(clean(row["k18_places"])) for row in rows if int(row["k18_candidate_count"]) == 1)
        scan_verified = sum(clean(row["k17_scan_verified"]) == "True" for row in rows)
        summaries.append(
            {
                "geocoding_unit_id": unit_id,
                "k17_source_locality_names": unit.get("source_locality_names", ""),
                "k17_target_locality_codes": unit.get("target_locality_codes", ""),
                "k17_target_locality_names": unit.get("target_locality_names", ""),
                "k17_row_count": len(rows),
                "k18_exact_station_matches": exact,
                "k18_exact_match_rate": f"{exact / len(rows):.1%}" if rows else "0.0%",
                "k18_ambiguous_matches": ambiguous,
                "k18_no_exact_station": len(no_exact),
                "k18_no_exact_k17_kalpis": joined(row["k17_kalpi_printed"] for row in no_exact),
                "k18_matches_with_place": with_place,
                "unique_k18_candidate_places": joined((row["k18_places"] for row in rows), separator=" || "),
                "k17_scan_verified_rows": scan_verified,
                "interpretation": "K18 matches are candidates; verify the K17 building in the original scan before assigning coordinates.",
            }
        )

    summaries.sort(key=lambda row: normalized_name(row["k17_source_locality_names"]))
    return details, summaries


def build_groups(details: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in details:
        key = (
            clean(row["geocoding_unit_id"]),
            clean(row["k17_source_locality_name"]),
            clean(row["k17_target_locality_name"]),
            clean(row["comparison_status"]),
            clean(row["candidate_confidence"]),
            clean(row["k18_locality_names"]),
            clean(row["k18_addresses"]),
            clean(row["k18_places"]),
        )
        grouped[key].append(row)

    result: list[dict[str, object]] = []
    for key, rows in grouped.items():
        rows.sort(key=lambda row: Decimal(clean(row["k17_kalpi_printed"]) or "0"))
        result.append(
            {
                "geocoding_unit_id": key[0],
                "k17_source_locality_name": key[1],
                "k17_target_locality_name": key[2],
                "comparison_status": key[3],
                "candidate_confidence": key[4],
                "k18_locality_name": key[5],
                "k18_address": key[6],
                "k18_place": key[7],
                "k17_row_count": len(rows),
                "k17_kalpis_raw": joined(row["k17_kalpi_raw"] for row in rows),
                "k17_kalpis_printed": joined(row["k17_kalpi_printed"] for row in rows),
                "k17_source_row_uids": joined(row["k17_source_row_uid"] for row in rows),
                "k18_pdf_pages": joined(row["k18_pdf_pages"] for row in rows),
                "interpretation": clean(rows[0]["interpretation"]),
            }
        )

    result.sort(
        key=lambda row: (
            normalized_name(row["k17_source_locality_name"]),
            Decimal(clean(row["k17_kalpis_printed"]).split(" | ")[0] or "0"),
        )
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", type=Path, default=DEFAULT_UNITS)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--k18", type=Path, default=DEFAULT_K18)
    parser.add_argument("--k17-scan", type=Path, default=DEFAULT_K17_SCAN)
    parser.add_argument("--detail-out", type=Path, default=DEFAULT_DETAIL_OUT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_OUT)
    parser.add_argument("--group-out", type=Path, default=DEFAULT_GROUP_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    details, summaries = compare(args)
    groups = build_groups(details)
    write_csv(args.detail_out, details, DETAIL_FIELDS)
    write_csv(args.summary_out, summaries, SUMMARY_FIELDS)
    write_csv(args.group_out, groups, GROUP_FIELDS)
    exact = sum(int(row["k18_candidate_count"]) == 1 for row in details)
    ambiguous = sum(int(row["k18_candidate_count"]) > 1 for row in details)
    scan_verified = sum(clean(row["k17_scan_verified"]) == "True" for row in details)
    print(f"K17 rows: {len(details)}")
    print(f"One exact K18 station candidate: {exact}")
    print(f"Multiple exact K18 station candidates: {ambiguous}")
    print(f"No exact K18 station candidate: {len(details) - exact - ambiguous}")
    print(f"Current-scope rows already verified directly in K17 scan: {scan_verified}")
    print(f"Detail: {args.detail_out}")
    print(f"Summary: {args.summary_out}")
    print(f"Candidate groups: {args.group_out}")


if __name__ == "__main__":
    main()
