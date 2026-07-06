"""Prototype extractor for the K18 polling-place PDF.

The K18 PDF is scanned, but it contains an embedded OCR text layer with word
coordinates. This script reconstructs table rows from fixed column bands.

Usage:
    python scripts/extract_k18_polling_places.py --validate
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pdfplumber


DEFAULT_PDF = Path("data/raw/archive_knesset18_kalpilist18.pdf")
DEFAULT_OUT = Path("data/processed/k18_polling_places_extracted_prototype.csv")
K18_RESOURCE_ID = "840edb33-90ac-4176-8ad9-4cdcb8e5caa5"

HEBREW_RE = re.compile(r"[\u0590-\u05ff]")

# Column bands are in PDF points, measured on the landscape A4 pages.
COLUMNS = [
    ("eligible", 115, 175),
    ("note", 175, 205),
    ("place", 205, 365),
    ("address", 365, 465),
    ("locality_code", 465, 510),
    ("kalpi", 510, 565),
    ("locality_name", 565, 650),
    ("committee_name", 650, 720),
    ("committee_code", 720, 750),
    ("serial", 750, 795),
]

OUTPUT_FIELDS = [
    "pdf_page",
    "serial",
    "serial_clean",
    "committee_code",
    "committee_code_clean",
    "committee_name",
    "locality_name",
    "kalpi",
    "kalpi_clean",
    "locality_code",
    "locality_code_clean",
    "address",
    "place",
    "note",
    "eligible",
    "eligible_clean",
]


def fix_token(text: str) -> str:
    """Reverse Hebrew tokens because the embedded OCR layer stores them reversed."""
    return text[::-1] if HEBREW_RE.search(text) else text


def cell_text(words: list[dict]) -> str:
    tokens = [
        fix_token(word["text"])
        for word in sorted(words, key=lambda word: word["x0"], reverse=True)
    ]
    return " ".join(tokens).strip()


def clean_digits(value: str) -> str:
    parts = re.findall(r"\d+", value or "")
    return "".join(parts) if parts else ""


def clean_kalpi(value: str) -> str:
    normalized = (value or "").replace(",", ".").replace(" ", "")
    match = re.search(r"\d+(?:\.\d+)?", normalized)
    if not match:
        return ""
    candidate = match.group(0)
    if candidate.endswith(".0"):
        return candidate[:-2]
    return candidate


def row_from_words(page_number: int, words: list[dict]) -> dict:
    row = {"pdf_page": page_number}
    for name, x0, x1 in COLUMNS:
        row[name] = cell_text(
            [
                word
                for word in words
                if x0 <= ((word["x0"] + word["x1"]) / 2) < x1
            ]
        )

    row["serial_clean"] = clean_digits(row["serial"])
    row["committee_code_clean"] = clean_digits(row["committee_code"])
    row["locality_code_clean"] = clean_digits(row["locality_code"])
    row["kalpi_clean"] = clean_kalpi(row["kalpi"])
    row["eligible_clean"] = clean_digits(row["eligible"])
    return row


def has_data_shape(row: dict) -> bool:
    return bool(
        row["committee_code_clean"]
        and row["locality_code_clean"]
        and row["kalpi_clean"]
        and row["locality_name"]
    )


def is_serial_only(row: dict) -> bool:
    nonempty = [
        field
        for field in [
            "eligible",
            "note",
            "place",
            "address",
            "locality_code",
            "kalpi",
            "locality_name",
            "committee_name",
            "committee_code",
            "serial",
        ]
        if row.get(field)
    ]
    return nonempty == ["serial"] and bool(row["serial_clean"])


def page_groups(page) -> list[list[dict]]:
    words = page.extract_words(
        x_tolerance=1,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    body = [word for word in words if 80 <= word["top"] <= 565]

    groups: list[list] = []
    for word in sorted(body, key=lambda item: (item["top"], item["x0"])):
        if not groups or abs(groups[-1][0] - word["top"]) > 4:
            groups.append([word["top"], [word]])
        else:
            groups[-1][1].append(word)

    merged: list[list[dict]] = []
    index = 0
    while index < len(groups):
        current_words = list(groups[index][1])
        current_row = row_from_words(0, current_words)
        if has_data_shape(current_row) and not current_row["serial_clean"]:
            if index + 1 < len(groups):
                next_row = row_from_words(0, groups[index + 1][1])
                if (
                    is_serial_only(next_row)
                    and abs(groups[index + 1][0] - groups[index][0]) <= 8
                ):
                    current_words.extend(groups[index + 1][1])
                    index += 1
        merged.append(current_words)
        index += 1

    return merged


def extract_rows(pdf_path: Path) -> tuple[list[dict], list[tuple[int, int]]]:
    rows: list[dict] = []
    page_counts: list[tuple[int, int]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if page_number in (1, len(pdf.pages)):
                continue

            count = 0
            for group in page_groups(page):
                row = row_from_words(page_number, group)
                if has_data_shape(row) and row["serial_clean"]:
                    rows.append(row)
                    count += 1
            page_counts.append((page_number, count))
    return rows, page_counts


def write_rows(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in OUTPUT_FIELDS} for row in rows])


def norm_code(value) -> str:
    digits = "".join(re.findall(r"\d+", str(value or "")))
    return str(int(digits)) if digits else ""


def norm_kalpi(value) -> str:
    text = str(value or "").replace(",", ".").strip()
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return ""
    candidate = match.group(0)
    try:
        as_float = float(candidate)
    except ValueError:
        return candidate
    if as_float.is_integer():
        return str(int(as_float))
    return candidate.rstrip("0").rstrip(".")


def code_candidates(raw_value: str) -> list[str]:
    digits = "".join(re.findall(r"\d+", str(raw_value or "")))
    candidates: list[str] = []
    if digits:
        candidates.append(str(int(digits)))
        for length in (4, 3, 2, 1):
            if len(digits) > length:
                for start in range(0, len(digits) - length + 1):
                    part = digits[start : start + length]
                    if part and int(part) > 0:
                        candidates.append(str(int(part)))
    return list(dict.fromkeys(candidates))


def kalpi_candidates(raw_value: str) -> list[str]:
    text = str(raw_value or "").replace(",", ".").strip()
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return []
    candidate = match.group(0)
    if "." not in candidate:
        return [str(int(candidate))]

    whole, fraction = candidate.split(".", 1)
    whole_int = str(int(whole))
    candidates = [whole_int]
    if fraction:
        candidates.append(f"{whole_int}.{int(fraction)}")
    return list(dict.fromkeys(candidates))


def fetch_result_keys() -> set[tuple[str, str]]:
    field_code = "\u05e1\u05de\u05dc \u05d9\u05e9\u05d5\u05d1"
    field_kalpi = "\u05e1\u05de\u05dc \u05e7\u05dc\u05e4\u05d9"
    result_keys: set[tuple[str, str]] = set()
    offset = 0

    while True:
        params = {
            "resource_id": K18_RESOURCE_ID,
            "limit": 5000,
            "offset": offset,
        }
        url = "https://data.gov.il/api/3/action/datastore_search?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)

        records = data["result"]["records"]
        for record in records:
            result_keys.add((norm_code(record.get(field_code)), norm_kalpi(record.get(field_kalpi))))

        if len(records) < 5000:
            break
        offset += len(records)

    return result_keys


def validate(rows: list[dict]) -> None:
    result_keys = fetch_result_keys()
    extracted_candidate_keys: set[tuple[str, str]] = set()
    for row in rows:
        for code in code_candidates(row["locality_code"]):
            for kalpi in kalpi_candidates(row["kalpi"]):
                key = (code, kalpi)
                if key in result_keys:
                    extracted_candidate_keys.add(key)

    matched = result_keys & extracted_candidate_keys
    print(f"official_result_keys={len(result_keys)}")
    print(
        "matched_result_keys="
        f"{len(matched)} ({len(matched) / len(result_keys) * 100:.2f}%)"
    )
    print(f"unmatched_result_keys={len(result_keys - extracted_candidate_keys)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate", action="store_true")
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    start = time.time()
    rows, page_counts = extract_rows(args.pdf)
    write_rows(rows, args.out)

    anomalies = [
        (page, count)
        for page, count in page_counts
        if count and (count < 5 or count > 45)
    ]
    print(f"extracted_rows={len(rows)}")
    print(f"pages_with_rows={sum(1 for _, count in page_counts if count)}")
    print(f"output={args.out}")
    print(f"page_count_anomalies={anomalies[:30]}")
    print(f"elapsed_seconds={time.time() - start:.1f}")

    if args.validate:
        validate(rows)


if __name__ == "__main__":
    main()
