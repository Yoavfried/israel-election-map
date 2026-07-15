from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL_AUDIT_PYTHON = ROOT / ".local" / "python-audit"
if LOCAL_AUDIT_PYTHON.exists():
    sys.path.insert(0, str(LOCAL_AUDIT_PYTHON))

import pandas as pd

from pipeline_common import DATA_DIR, MANUAL_DIR, PROCESSED_DIR, RAW_DIR, int_value, normalize_code, normalize_kalpi, normalize_spaces, read_json, write_csv, write_json
from normalize_polling_places import read_k18_visual_reviews, read_k19_pdf
from address_parsing import has_house_number, parse_street_name


ADDRESS_TABLE = PROCESSED_DIR / "addresses" / "polling_place_addresses.csv"
GEOCODING_ROWS = PROCESSED_DIR / "geocoding" / "geocoding_work_unit_rows.csv"
OUT_DIR = PROCESSED_DIR / "addresses"

SOURCE_AUDIT_OUTPUT = OUT_DIR / "polling_place_address_quality_rows.csv"
GEOCODING_AUDIT_OUTPUT = OUT_DIR / "polling_place_address_quality_geocoding_rows.csv"
UNIT_AUDIT_OUTPUT = OUT_DIR / "polling_place_address_quality_units.csv"
REVIEW_QUEUE_OUTPUT = OUT_DIR / "polling_place_address_quality_review_queue.csv"
VISUAL_REVIEW_QUEUE_OUTPUT = OUT_DIR / "polling_place_address_visual_review_queue.csv"
LOCALITY_ONLY_NO_PLACE_OUTPUT = OUT_DIR / "polling_place_locality_only_no_place_units.csv"
SUMMARY_CSV_OUTPUT = OUT_DIR / "polling_place_address_quality_summary.csv"
SUMMARY_JSON_OUTPUT = OUT_DIR / "polling_place_address_quality_summary.json"

DIGITAL_ADDRESS_SOURCES = {
    "K25": RAW_DIR / "election-25_kalpi-places_kalpies_list_10_7_nagish.xlsx",
    "K24": RAW_DIR / "archive_knesset24_kalpies_report_tofes_b_18_3_21.xlsx",
    "K23": RAW_DIR / "archive_knesset23_kalpies_report_19_1_20_1.xlsx",
    "K22": RAW_DIR / "archive_knesset22_kalpies_report_tofes_b_6th_edition_15_9.xlsx",
    "K21": RAW_DIR / "archive_knesset21_kalpies_full_report.xls",
    "K20": RAW_DIR / "archive_knesset20_tell_the_polls_9_3.xls",
}
K19_PDF = RAW_DIR / "archive_knesset19_all_stations.pdf"
K18_RESOLVED = PROCESSED_DIR / "k18_polling_places_resolved.csv"
K18_PDF = RAW_DIR / "archive_knesset18_kalpilist18.pdf"
K18_VISUAL_REVIEWS = MANUAL_DIR / "manual_k18_address_reviews.csv"
K17_BALLOT_ROWS = PROCESSED_DIR / "normalized" / "ballot_rows.csv"
K17_MANUAL = MANUAL_DIR / "manual_k17_scanned_place_names.csv"
RESULT_MANIFEST = PROCESSED_DIR / "manifest" / "election_result_resources.json"

COL_LOCALITY_CODE = "\u05e1\u05de\u05dc \u05d9\u05e9\u05d5\u05d1 \u05d1\u05d7\u05d9\u05e8\u05d5\u05ea"
COL_LOCALITY_NAME = "\u05e9\u05dd \u05d9\u05e9\u05d5\u05d1 \u05d1\u05d7\u05d9\u05e8\u05d5\u05ea"
COL_KALPI = "\u05e1\u05de\u05dc \u05e7\u05dc\u05e4\u05d9"
COL_ADDRESS = "\u05db\u05ea\u05d5\u05d1\u05ea \u05e7\u05dc\u05e4\u05d9"
COL_PLACE = "\u05de\u05e7\u05d5\u05dd \u05e7\u05dc\u05e4\u05d9"
COL_ELIGIBLE_ACTUAL = "\u05d1\u05d5\u05d7\u05e8\u05d9 \u05db\u05e0\u05e1\u05ea \u05d1\u05e4\u05d5\u05e2\u05dc"
COL_ELIGIBLE = "\u05d1\u05d5\u05d7\u05e8\u05d9 \u05db\u05e0\u05e1\u05ea"

K17_COL_KALPI = "\u05de\u05e1\u05e4\u05e8 \u05e7\u05dc\u05e4\u05d9"
K17_COL_LOCALITY = "\u05e9\u05dd \u05d9\u05e9\u05d5\u05d1"
K17_COL_ADDRESS = "\u05db\u05ea\u05d5\u05d1\u05ea"

PLACE_KEYWORDS = (
        "\u05d1\u05d9\u05ea \u05e1\u05e4\u05e8",  # school
        "\u05d1\u05d9\u05e1",
        "\u05d1\u05d9\u05d4\u05e1",
        "\u05de\u05ea\u05e0\u05e1",
        "\u05de\u05e8\u05db\u05d6 \u05e7\u05d4\u05d9\u05dc\u05ea\u05d9",
        "\u05de\u05d5\u05e2\u05d3\u05d5\u05df",
        "\u05d0\u05d5\u05dc\u05dd",
        "\u05d2\u05df \u05d9\u05dc\u05d3\u05d9\u05dd",
        "\u05d9\u05e9\u05d9\u05d1\u05d4",
        "\u05ea\u05dc\u05de\u05d5\u05d3 \u05ea\u05d5\u05e8\u05d4",
        "\u05d1\u05d9\u05ea \u05db\u05e0\u05e1\u05ea",
        "\u05e1\u05e4\u05e8\u05d9\u05d4",
        "\u05e1\u05e4\u05e8\u05d9\u05d9\u05d4",
        "\u05d1\u05d9\u05ea \u05d0\u05d1\u05d5\u05ea",
        "\u05de\u05e2\u05d5\u05df",
        "\u05de\u05e7\u05dc\u05d8",
)

CATEGORY_PRIORITY = {
    "missing_address_and_place": 0,
    "place_only": 1,
    "locality_only_address": 2,
    "number_only_or_no_street_text": 3,
    "suspicious_text": 4,
    "place_name_in_address_field": 5,
    "missing_house_number": 6,
    "street_number": 7,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean_source(value: Any) -> str:
    return normalize_spaces(value).replace("\u00ad", "-")


def comparable_text(value: Any) -> str:
    text = normalize_spaces(value).lower()
    text = text.replace("\u05f3", "").replace("\u05f4", "")
    text = text.replace("'", "").replace('"', "")
    return re.sub(r"[\s.,:/(){}\[\]\-_*]+", "", text)


def phrase_text(value: Any) -> str:
    text = normalize_spaces(value).lower()
    text = text.replace("\u05f3", "").replace("\u05f4", "")
    text = text.replace("'", "").replace('"', "")
    return normalize_spaces(re.sub(r"[\s.,:/(){}\[\]\-_*]+", " ", text))


def contains_place_keyword(value: Any) -> bool:
    haystack = f" {phrase_text(value)} "
    return any(f" {phrase_text(keyword)} " in haystack for keyword in PLACE_KEYWORDS)


def source_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def normalized_source_path(path: Path) -> str:
    return str(path.relative_to(DATA_DIR)).replace("\\", "/")


def evidence_key(election: str, normalized_source_file: str, source_row_id: Any) -> tuple[str, str, str]:
    return election, normalize_spaces(normalized_source_file), normalize_spaces(source_row_id)


def add_evidence(index: dict[tuple[str, str, str], dict[str, Any]], record: dict[str, Any]) -> None:
    key = evidence_key(record["election"], record["normalized_source_file"], record["source_row_id"])
    if key in index:
        raise ValueError(f"Duplicate source evidence key: {key}")
    index[key] = record


def make_evidence(
    *,
    election: str,
    normalized_source_file: str,
    source_row_id: Any,
    source_kind: str,
    verification_level: str,
    evidence_source_file: str,
    evidence_locator: str,
    raw_address: Any,
    raw_place: Any,
    expected_address: Any,
    expected_place: Any,
    expected_locality_code: Any,
    expected_locality_name: Any,
    expected_kalpi: Any,
    expected_eligible: Any,
) -> dict[str, Any]:
    return {
        "election": election,
        "normalized_source_file": normalized_source_file,
        "source_row_id": normalize_spaces(source_row_id),
        "source_kind": source_kind,
        "verification_level": verification_level,
        "evidence_source_file": evidence_source_file,
        "evidence_locator": evidence_locator,
        "raw_address": normalize_spaces(raw_address),
        "raw_place": normalize_spaces(raw_place),
        "expected_address": clean_source(expected_address),
        "expected_place": clean_source(expected_place),
        "expected_locality_code": normalize_code(expected_locality_code),
        "expected_locality_name": clean_source(expected_locality_name),
        "expected_kalpi": normalize_kalpi(expected_kalpi),
        "expected_eligible": int_value(expected_eligible),
    }


def build_digital_evidence(index: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    required = {COL_LOCALITY_CODE, COL_LOCALITY_NAME, COL_KALPI, COL_ADDRESS, COL_PLACE}
    for election, path in DIGITAL_ADDRESS_SOURCES.items():
        frame = pd.read_excel(path, sheet_name="DataSheet", dtype=str).fillna("")
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{path} is missing expected columns: {missing}")
        normalized_source_file = normalized_source_path(path)
        for source_row_id, (_, row) in enumerate(frame.iterrows(), start=1):
            eligible = row.get(COL_ELIGIBLE_ACTUAL, row.get(COL_ELIGIBLE, ""))
            add_evidence(
                index,
                make_evidence(
                    election=election,
                    normalized_source_file=normalized_source_file,
                    source_row_id=source_row_id,
                    source_kind="official_digital_spreadsheet",
                    verification_level="raw_digital_cell",
                    evidence_source_file=normalized_source_file,
                    evidence_locator=f"DataSheet source row {source_row_id}",
                    raw_address=row.get(COL_ADDRESS, ""),
                    raw_place=row.get(COL_PLACE, ""),
                    expected_address=row.get(COL_ADDRESS, ""),
                    expected_place=row.get(COL_PLACE, ""),
                    expected_locality_code=row.get(COL_LOCALITY_CODE, ""),
                    expected_locality_name=row.get(COL_LOCALITY_NAME, ""),
                    expected_kalpi=row.get(COL_KALPI, ""),
                    expected_eligible=eligible,
                ),
            )


def build_k19_evidence(index: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    for row in read_k19_pdf(K19_PDF):
        add_evidence(
            index,
            make_evidence(
                election="K19",
                normalized_source_file=row["source_file"],
                source_row_id=row["source_row_id"],
                source_kind="official_text_pdf",
                verification_level="text_pdf_parser_reproduction",
                evidence_source_file=source_path(K19_PDF),
                evidence_locator=row["source_row_id"],
                raw_address=row["address"],
                raw_place=row["place"],
                expected_address=row["address"],
                expected_place=row["place"],
                expected_locality_code=row["source_locality_code"],
                expected_locality_name=row["source_locality_name"],
                expected_kalpi=row["source_kalpi"],
                expected_eligible=row["source_eligible_voters"],
            ),
        )


def build_k18_evidence(index: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    normalized_source_file = normalized_source_path(K18_RESOLVED)
    visual_reviews = read_k18_visual_reviews(K18_VISUAL_REVIEWS)
    for row in read_csv(K18_RESOLVED):
        if row["resolved_status"] != "matched":
            continue
        key = (normalize_code(row["official_locality_code"]), normalize_kalpi(row["official_kalpi"]))
        review = visual_reviews.get(key)
        corrected = bool(review and review["review_status"] == "corrected")
        address = review.get("corrected_address", "") if corrected else ""
        place = review.get("corrected_place", "") if corrected else ""
        address = address or row["address"]
        place = place or row["place"]
        if review:
            locator = f"PDF page {review['pdf_page']}; {review['review_note']}"
            source_kind = "official_scanned_pdf_manual_visual_review"
            verification_level = f"manual_visual_{review['review_status']}"
        else:
            locator = f"PDF page {row['pdf_page']}; match {row['match_method']}"
            source_kind = "official_scanned_pdf_ocr"
            verification_level = "ocr_intermediate_copy"
        add_evidence(
            index,
            make_evidence(
                election="K18",
                normalized_source_file=normalized_source_file,
                source_row_id=row["official_row_id"],
                source_kind=source_kind,
                verification_level=verification_level,
                evidence_source_file=source_path(K18_PDF),
                evidence_locator=locator,
                raw_address=address,
                raw_place=place,
                expected_address=address,
                expected_place=place,
                expected_locality_code=row["official_locality_code"],
                expected_locality_name=row["official_locality_name"],
                expected_kalpi=row["official_kalpi"],
                expected_eligible=row["official_eligible"],
            ),
        )


def k17_result_path() -> Path:
    manifest = read_json(RESULT_MANIFEST)
    resource = next(item for item in manifest if item["election"] == "K17")
    return DATA_DIR / resource["local_path"]


def build_k17_evidence(index: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    raw_path = k17_result_path()
    normalized_source_file = normalized_source_path(K17_BALLOT_ROWS)
    for order, row in enumerate(read_csv(raw_path), start=1):
        address = row.get(K17_COL_ADDRESS, "")
        if not normalize_spaces(address):
            continue
        source_row_id = normalize_spaces(row.get("_id", "")) or str(order)
        add_evidence(
            index,
            make_evidence(
                election="K17",
                normalized_source_file=normalized_source_file,
                source_row_id=source_row_id,
                source_kind="official_digital_result_file",
                verification_level="raw_digital_cell",
                evidence_source_file=source_path(raw_path),
                evidence_locator=f"result row {source_row_id}",
                raw_address=address,
                raw_place="",
                expected_address=address,
                expected_place="",
                expected_locality_code="",
                expected_locality_name=row.get(K17_COL_LOCALITY, ""),
                expected_kalpi=row.get(K17_COL_KALPI, ""),
                expected_eligible="",
            ),
        )

    manual_source_file = normalized_source_path(K17_MANUAL)
    for row in read_csv(K17_MANUAL):
        add_evidence(
            index,
            make_evidence(
                election="K17",
                normalized_source_file=manual_source_file,
                source_row_id=row["source_result_row_id"],
                source_kind="reviewed_manual_scan_transcription",
                verification_level="manual_visual_transcription",
                evidence_source_file=row["pdf_source"],
                evidence_locator=row["pdf_source"],
                raw_address=row["scanned_address"],
                raw_place=row["place"],
                expected_address="",
                expected_place=row["place"],
                expected_locality_code="",
                expected_locality_name=row["source_locality_name"],
                expected_kalpi=row["source_kalpi"],
                expected_eligible="",
            ),
        )


def build_source_evidence() -> dict[tuple[str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    build_digital_evidence(index)
    build_k19_evidence(index)
    build_k18_evidence(index)
    build_k17_evidence(index)
    return index


def quality_for(address: Any, place: Any, locality_names: list[Any]) -> dict[str, Any]:
    address_text = normalize_spaces(address)
    place_text = normalize_spaces(place)
    address_comparable = comparable_text(address_text)
    place_comparable = comparable_text(place_text)
    locality_values = {
        comparable_text(part)
        for name in locality_names
        for part in normalize_spaces(name).split("|")
        if comparable_text(part)
    }
    number = has_house_number(address_text)
    has_letters = any(character.isalpha() for character in address_text)
    locality_only = bool(address_comparable and address_comparable in locality_values)
    address_equals_place = bool(address_comparable and place_comparable and address_comparable == place_comparable)
    looks_like_place = bool(
        address_comparable
        and (address_equals_place or contains_place_keyword(address_text))
    )
    suspicious_prefix = bool(address_text and re.match(r"^[^\u0590-\u05ff]", address_text))
    street_fragment, separator, remainder = address_text.partition(",")
    suspicious_embedded_digit = bool(
        separator
        and has_house_number(remainder)
        and re.search(r"[\u0590-\u05ff][01](?=[\u0590-\u05ff\s]|$)|^[01](?=[\u0590-\u05ff])", street_fragment)
    )
    suspicious_latin = bool(re.search(r"[A-Za-z]", address_text))
    suspicious_replacement = "\ufffd" in address_text or "\x00" in address_text
    parsed_street = comparable_text(parse_street_name(address_text))
    suspicious_short_street = bool(number and has_letters and len(parsed_street) <= 1)

    flags: list[str] = []
    if not address_text:
        flags.append("missing_address")
        flags.append("place_only" if place_text else "missing_place")
    if address_text and not number:
        flags.append("missing_house_number")
    if locality_only:
        flags.append("address_is_only_locality")
    if address_equals_place:
        flags.append("address_equals_place")
    if looks_like_place:
        flags.append("address_looks_like_place_name")
    if address_text and not has_letters:
        flags.append("no_street_letters")
    if suspicious_prefix:
        flags.append("suspicious_prefix")
    if suspicious_embedded_digit:
        flags.append("suspicious_embedded_digit")
    if suspicious_latin:
        flags.append("suspicious_latin_character")
    if suspicious_replacement:
        flags.append("suspicious_replacement_character")
    if suspicious_short_street:
        flags.append("implausibly_short_street_name")

    suspicious = (
        suspicious_prefix
        or suspicious_embedded_digit
        or suspicious_latin
        or suspicious_replacement
        or suspicious_short_street
    )
    if not address_text:
        category = "place_only" if place_text else "missing_address_and_place"
    elif locality_only:
        category = "locality_only_address"
    elif not has_letters:
        category = "number_only_or_no_street_text"
    elif suspicious:
        category = "suspicious_text"
    elif not number and looks_like_place:
        category = "place_name_in_address_field"
    elif not number:
        category = "missing_house_number"
    else:
        category = "street_number"

    return {
        "quality_category": category,
        "quality_flags": "|".join(flags),
        "has_house_number": number,
        "review_required": category != "street_number",
    }


def verification_for(row: dict[str, str], evidence: dict[str, Any] | None) -> dict[str, Any]:
    if evidence is None:
        return {
            "source_kind": "",
            "verification_level": "",
            "verification_status": "source_record_missing",
            "field_mismatches": "",
            "evidence_source_file": "",
            "evidence_locator": "",
            "evidence_address": "",
            "evidence_place": "",
        }

    comparisons = {
        "address": clean_source(row.get("address", "")) == evidence["expected_address"],
        "place": clean_source(row.get("place", "")) == evidence["expected_place"],
        "locality_code": normalize_code(row.get("source_locality_code", "")) == evidence["expected_locality_code"],
        "locality_name": clean_source(row.get("source_locality_name", "")) == evidence["expected_locality_name"],
        "kalpi": normalize_kalpi(row.get("source_kalpi", "")) == evidence["expected_kalpi"],
        "eligible": int_value(row.get("source_eligible_voters", "")) == evidence["expected_eligible"],
    }
    mismatches = [field for field, matches in comparisons.items() if not matches]
    if mismatches:
        status = "pipeline_value_mismatch"
    elif evidence["verification_level"] == "raw_digital_cell":
        status = "verified_against_raw_digital_source"
    elif evidence["verification_level"] == "text_pdf_parser_reproduction":
        status = "parser_reproduced_visual_check_still_needed"
    elif evidence["verification_level"] == "ocr_intermediate_copy":
        status = "copied_from_ocr_intermediate_visual_check_still_needed"
    elif evidence["verification_level"] in {"manual_visual_corrected", "manual_visual_confirmed_source"}:
        status = "verified_against_visual_source"
    else:
        status = "verified_against_reviewed_manual_transcription"

    return {
        "source_kind": evidence["source_kind"],
        "verification_level": evidence["verification_level"],
        "verification_status": status,
        "field_mismatches": "|".join(mismatches),
        "evidence_source_file": evidence["evidence_source_file"],
        "evidence_locator": evidence["evidence_locator"],
        "evidence_address": evidence["raw_address"],
        "evidence_place": evidence["raw_place"],
    }


def origin_assessment(quality_category: str, verification_status: str) -> str:
    if quality_category == "street_number":
        return "usable_address"
    if verification_status == "pipeline_value_mismatch":
        return "possible_pipeline_error"
    if verification_status == "source_record_missing":
        return "unverified_missing_source_record"
    if verification_status == "verified_against_raw_digital_source":
        return "present_in_raw_official_source"
    if verification_status == "verified_against_reviewed_manual_transcription":
        return "present_in_reviewed_manual_transcription"
    if verification_status == "verified_against_visual_source":
        return "visually_verified_or_corrected_from_scanned_source"
    if verification_status == "parser_reproduced_visual_check_still_needed":
        return "pdf_parser_or_source_needs_visual_review"
    return "ocr_or_source_needs_visual_review"


def audit_source_rows(
    rows: list[dict[str, str]],
    evidence_index: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    audited: list[dict[str, Any]] = []
    for row in rows:
        key = evidence_key(row["election"], row["source_file"], row["source_row_id"])
        quality = quality_for(row["address"], row["place"], [row["source_locality_name"]])
        verification = verification_for(row, evidence_index.get(key))
        audited.append(
            {
                **row,
                **quality,
                **verification,
                "origin_assessment": origin_assessment(
                    quality["quality_category"], verification["verification_status"]
                ),
            }
        )
    return audited


def audit_geocoding_rows(
    rows: list[dict[str, str]],
    source_audit_index: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    audited: list[dict[str, Any]] = []
    for row in rows:
        key = evidence_key(row["election"], row["address_source_file"], row["address_source_row_id"])
        source_audit = source_audit_index.get(key)
        quality = quality_for(
            row["address"],
            row["place"],
            [row["source_locality_name"], row["target_locality_name"]],
        )
        verification = {
            field: source_audit.get(field, "") if source_audit else ""
            for field in [
                "source_kind",
                "verification_level",
                "verification_status",
                "field_mismatches",
                "evidence_source_file",
                "evidence_locator",
                "evidence_address",
                "evidence_place",
            ]
        }
        if not source_audit:
            verification["verification_status"] = "source_record_missing"
        audited.append(
            {
                "geocoding_unit_id": row["geocoding_unit_id"],
                "source_row_uid": row["source_row_uid"],
                "election": row["election"],
                "source_locality_code": row["source_locality_code"],
                "source_locality_name": row["source_locality_name"],
                "source_kalpi": row["source_kalpi"],
                "target_locality_code": row["target_locality_code"],
                "target_locality_name": row["target_locality_name"],
                "address": row["address"],
                "place": row["place"],
                "geocoder_query": row["geocoder_query"],
                "address_source_file": row["address_source_file"],
                "address_source_row_id": row["address_source_row_id"],
                "address_match_method": row["address_match_method"],
                "existing_address_format_status": row["address_format_status"],
                "actual_voters": int_value(row["actual_voters"]),
                "eligible_voters": int_value(row["eligible_voters"]),
                **quality,
                **verification,
                "origin_assessment": origin_assessment(
                    quality["quality_category"], verification["verification_status"]
                ),
            }
        )
    return audited


def join_values(rows: list[dict[str, Any]], field: str) -> str:
    return "|".join(sorted({normalize_spaces(row.get(field, "")) for row in rows if normalize_spaces(row.get(field, ""))}))


def worst_category(rows: list[dict[str, Any]]) -> str:
    return min(
        {row["quality_category"] for row in rows},
        key=lambda category: CATEGORY_PRIORITY[category],
    )


def review_priority(rows: list[dict[str, Any]]) -> str:
    statuses = {row["verification_status"] for row in rows}
    if statuses & {"pipeline_value_mismatch", "source_record_missing"}:
        return "1_pipeline_fidelity"
    extraction_statuses = {
        "parser_reproduced_visual_check_still_needed",
        "copied_from_ocr_intermediate_visual_check_still_needed",
    }
    independent_statuses = {
        "verified_against_raw_digital_source",
        "verified_against_reviewed_manual_transcription",
        "verified_against_visual_source",
    }
    if any(row["review_required"] for row in rows) and statuses & extraction_statuses and not statuses & independent_statuses:
        return "2_pdf_or_ocr_visual_review"
    if any(row["review_required"] for row in rows) and statuses & extraction_statuses and statuses & independent_statuses:
        return "3_cross_election_source_corroborated"
    if any(row["review_required"] for row in rows):
        return "4_raw_or_manual_source_content"
    return "5_usable_address"


def corroboration_status(rows: list[dict[str, Any]]) -> str:
    statuses = {row["verification_status"] for row in rows}
    if statuses & {"pipeline_value_mismatch", "source_record_missing"}:
        return "pipeline_fidelity_failure"
    if not any(row["review_required"] for row in rows):
        return "not_required_for_usable_address"

    has_pdf_or_ocr = bool(
        statuses
        & {
            "parser_reproduced_visual_check_still_needed",
            "copied_from_ocr_intermediate_visual_check_still_needed",
        }
    )
    has_raw_digital = "verified_against_raw_digital_source" in statuses
    has_manual = "verified_against_reviewed_manual_transcription" in statuses
    has_visual = "verified_against_visual_source" in statuses
    if has_pdf_or_ocr and has_raw_digital:
        return "pdf_or_ocr_corroborated_by_raw_digital_election"
    if has_pdf_or_ocr and has_manual:
        return "pdf_or_ocr_corroborated_by_manual_scan"
    if has_pdf_or_ocr and has_visual:
        return "pdf_or_ocr_corroborated_by_visual_source"
    if has_pdf_or_ocr:
        return "pdf_or_ocr_requires_visual_check"
    if has_raw_digital:
        return "present_in_raw_digital_source"
    if has_manual:
        return "present_in_reviewed_manual_transcription"
    if has_visual:
        return "present_in_reviewed_visual_source"
    return "source_content_unverified"


def build_units(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["geocoding_unit_id"]].append(row)

    units: list[dict[str, Any]] = []
    for unit_id, members in grouped.items():
        flags = sorted(
            {
                flag
                for row in members
                for flag in normalize_spaces(row["quality_flags"]).split("|")
                if flag
            }
        )
        category = worst_category(members)
        units.append(
            {
                "geocoding_unit_id": unit_id,
                "geocoder_query": members[0]["geocoder_query"],
                "unit_quality_category": category,
                "quality_categories": join_values(members, "quality_category"),
                "quality_flags": "|".join(flags),
                "review_required": any(bool(row["review_required"]) for row in members),
                "review_priority": review_priority(members),
                "corroboration_status": corroboration_status(members),
                "verification_statuses": join_values(members, "verification_status"),
                "origin_assessments": join_values(members, "origin_assessment"),
                "source_kinds": join_values(members, "source_kind"),
                "elections": join_values(members, "election"),
                "target_locality_codes": join_values(members, "target_locality_code"),
                "target_locality_names": join_values(members, "target_locality_name"),
                "address_source_files": join_values(members, "address_source_file"),
                "source_row_uids": join_values(members, "source_row_uid"),
                "row_count": len(members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
                "example_address": members[0]["address"],
                "example_place": members[0]["place"],
                "example_evidence_address": members[0]["evidence_address"],
                "example_evidence_place": members[0]["evidence_place"],
                "example_evidence_locator": members[0]["evidence_locator"],
            }
        )
    return sorted(units, key=lambda row: (row["review_priority"], row["geocoder_query"], row["geocoding_unit_id"]))


def build_locality_only_no_place_units(
    geocoding_rows: list[dict[str, Any]],
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in geocoding_rows:
        rows_by_unit[row["geocoding_unit_id"]].append(row)

    output: list[dict[str, Any]] = []
    for unit in units:
        if unit["unit_quality_category"] != "locality_only_address":
            continue
        members = rows_by_unit[unit["geocoding_unit_id"]]
        if any(normalize_spaces(row["place"]) for row in members):
            continue
        output.append(
            {
                "geocoding_unit_id": unit["geocoding_unit_id"],
                "geocoder_query": unit["geocoder_query"],
                "elections": join_values(members, "election"),
                "source_kinds": join_values(members, "source_kind"),
                "verification_statuses": join_values(members, "verification_status"),
                "source_locality_codes": join_values(members, "source_locality_code"),
                "source_locality_names": join_values(members, "source_locality_name"),
                "target_locality_codes": join_values(members, "target_locality_code"),
                "target_locality_names": join_values(members, "target_locality_name"),
                "source_kalpis": join_values(members, "source_kalpi"),
                "addresses": join_values(members, "address"),
                "places": join_values(members, "place"),
                "source_row_uids": join_values(members, "source_row_uid"),
                "address_source_files": join_values(members, "address_source_file"),
                "evidence_locators": join_values(members, "evidence_locator"),
                "row_count": len(members),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in members),
                "eligible_voters": sum(int_value(row["eligible_voters"]) for row in members),
            }
        )
    return sorted(output, key=lambda row: (row["target_locality_names"], row["geocoder_query"]))


def metric_rows(
    grain: str,
    records: list[dict[str, Any]],
    election: str,
    category_field: str,
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[normalize_spaces(record.get(category_field, "")) or "(missing)"].append(record)
    return [
        {
            "grain": grain,
            "election": election,
            "metric_type": category_field,
            "metric": value,
            "count": len(group),
            "actual_voters": sum(int_value(row.get("actual_voters", "")) for row in group),
            "eligible_voters": sum(int_value(row.get("eligible_voters", "")) for row in group),
        }
        for value, group in sorted(groups.items())
    ]


def flag_metric_rows(grain: str, records: list[dict[str, Any]], election: str) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    actual: Counter[str] = Counter()
    eligible: Counter[str] = Counter()
    for record in records:
        for flag in normalize_spaces(record.get("quality_flags", "")).split("|"):
            if not flag:
                continue
            counts[flag] += 1
            actual[flag] += int_value(record.get("actual_voters", ""))
            eligible[flag] += int_value(record.get("eligible_voters", ""))
    return [
        {
            "grain": grain,
            "election": election,
            "metric_type": "quality_flag",
            "metric": flag,
            "count": counts[flag],
            "actual_voters": actual[flag],
            "eligible_voters": eligible[flag],
        }
        for flag in sorted(counts)
    ]


def build_summary_rows(
    source_rows: list[dict[str, Any]],
    geocoding_rows: list[dict[str, Any]],
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for grain, records, category_field in [
        ("source_row", source_rows, "quality_category"),
        ("geocoding_row", geocoding_rows, "quality_category"),
        ("geocoding_unit", units, "unit_quality_category"),
    ]:
        summary.extend(metric_rows(grain, records, "ALL", category_field))
        summary.extend(flag_metric_rows(grain, records, "ALL"))
        if grain != "geocoding_unit":
            summary.extend(metric_rows(grain, records, "ALL", "verification_status"))

        elections = sorted(
            {
                election
                for record in records
                for election in normalize_spaces(record.get("election" if grain != "geocoding_unit" else "elections", "")).split("|")
                if election
            },
            reverse=True,
        )
        for election in elections:
            if grain == "geocoding_unit":
                election_records = build_units(
                    [record for record in geocoding_rows if record["election"] == election]
                )
            else:
                election_records = [record for record in records if record["election"] == election]
            summary.extend(metric_rows(grain, election_records, election, category_field))
            summary.extend(flag_metric_rows(grain, election_records, election))
            if grain != "geocoding_unit":
                summary.extend(metric_rows(grain, election_records, election, "verification_status"))
    return summary


def counts(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(normalize_spaces(row.get(field, "")) or "(missing)" for row in records).items()))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    address_rows = read_csv(ADDRESS_TABLE)
    evidence_index = build_source_evidence()
    source_audit_rows = audit_source_rows(address_rows, evidence_index)
    source_audit_index = {
        evidence_key(row["election"], row["source_file"], row["source_row_id"]): row
        for row in source_audit_rows
    }

    geocoding_rows = audit_geocoding_rows(read_csv(GEOCODING_ROWS), source_audit_index)
    units = build_units(geocoding_rows)
    locality_only_no_place_units = build_locality_only_no_place_units(geocoding_rows, units)
    review_units = [row for row in units if row["review_required"]]
    visual_review_units = [
        row for row in review_units if row["corroboration_status"] == "pdf_or_ocr_requires_visual_check"
    ]
    summary_rows = build_summary_rows(source_audit_rows, geocoding_rows, units)

    source_fields = list(source_audit_rows[0].keys()) if source_audit_rows else []
    geocoding_fields = list(geocoding_rows[0].keys()) if geocoding_rows else []
    unit_fields = list(units[0].keys()) if units else []
    summary_fields = ["grain", "election", "metric_type", "metric", "count", "actual_voters", "eligible_voters"]
    locality_only_no_place_fields = list(locality_only_no_place_units[0].keys()) if locality_only_no_place_units else []

    write_csv(SOURCE_AUDIT_OUTPUT, source_audit_rows, source_fields)
    write_csv(GEOCODING_AUDIT_OUTPUT, geocoding_rows, geocoding_fields)
    write_csv(UNIT_AUDIT_OUTPUT, units, unit_fields)
    write_csv(REVIEW_QUEUE_OUTPUT, review_units, unit_fields)
    write_csv(VISUAL_REVIEW_QUEUE_OUTPUT, visual_review_units, unit_fields)
    write_csv(LOCALITY_ONLY_NO_PLACE_OUTPUT, locality_only_no_place_units, locality_only_no_place_fields)
    write_csv(SUMMARY_CSV_OUTPUT, summary_rows, summary_fields)

    problematic_source_rows = [row for row in source_audit_rows if row["review_required"]]
    problematic_geocoding_rows = [row for row in geocoding_rows if row["review_required"]]
    source_verification_counts = Counter(row["verification_status"] for row in source_audit_rows)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "address_table": str(ADDRESS_TABLE),
            "geocoding_rows": str(GEOCODING_ROWS),
        },
        "outputs": {
            "source_rows": str(SOURCE_AUDIT_OUTPUT),
            "geocoding_rows": str(GEOCODING_AUDIT_OUTPUT),
            "geocoding_units": str(UNIT_AUDIT_OUTPUT),
            "review_queue": str(REVIEW_QUEUE_OUTPUT),
            "visual_review_queue": str(VISUAL_REVIEW_QUEUE_OUTPUT),
            "locality_only_no_place_units": str(LOCALITY_ONLY_NO_PLACE_OUTPUT),
            "summary_csv": str(SUMMARY_CSV_OUTPUT),
        },
        "source_evidence_record_count": len(evidence_index),
        "source_row_count": len(source_audit_rows),
        "source_row_quality_category_counts": counts(source_audit_rows, "quality_category"),
        "source_row_verification_status_counts": dict(sorted(source_verification_counts.items())),
        "pipeline_value_mismatch_count": source_verification_counts["pipeline_value_mismatch"],
        "source_record_missing_count": source_verification_counts["source_record_missing"],
        "problematic_source_row_count": len(problematic_source_rows),
        "problematic_source_row_origin_counts": counts(problematic_source_rows, "origin_assessment"),
        "geocoding_row_count": len(geocoding_rows),
        "geocoding_row_quality_category_counts": counts(geocoding_rows, "quality_category"),
        "geocoding_row_verification_status_counts": counts(geocoding_rows, "verification_status"),
        "problematic_geocoding_row_count": len(problematic_geocoding_rows),
        "problematic_geocoding_row_origin_counts": counts(problematic_geocoding_rows, "origin_assessment"),
        "geocoding_unit_count": len(units),
        "geocoding_unit_quality_category_counts": counts(units, "unit_quality_category"),
        "review_unit_count": len(review_units),
        "review_unit_priority_counts": counts(review_units, "review_priority"),
        "review_unit_corroboration_counts": counts(review_units, "corroboration_status"),
        "visual_review_unit_count": len(visual_review_units),
        "visual_review_unit_quality_category_counts": counts(visual_review_units, "unit_quality_category"),
        "locality_only_no_place_unit_count": len(locality_only_no_place_units),
        "locality_only_no_place_target_label_count": len(
            {row["target_locality_names"] for row in locality_only_no_place_units}
        ),
        "locality_only_no_place_election_counts": counts(locality_only_no_place_units, "elections"),
        "locality_only_no_place_source_kind_counts": counts(locality_only_no_place_units, "source_kinds"),
    }
    write_json(SUMMARY_JSON_OUTPUT, summary)

    print(f"source_rows={len(source_audit_rows)}")
    print(f"source_evidence_records={len(evidence_index)}")
    print(f"problematic_source_rows={len(problematic_source_rows)}")
    print(f"geocoding_rows={len(geocoding_rows)}")
    print(f"problematic_geocoding_rows={len(problematic_geocoding_rows)}")
    print(f"geocoding_units={len(units)}")
    print(f"review_units={len(review_units)}")
    print(f"visual_review_units={len(visual_review_units)}")
    print(f"locality_only_no_place_units={len(locality_only_no_place_units)}")
    print("source_verification_statuses=" + str(summary["source_row_verification_status_counts"]))
    print("geocoding_unit_categories=" + str(summary["geocoding_unit_quality_category_counts"]))


if __name__ == "__main__":
    main()
