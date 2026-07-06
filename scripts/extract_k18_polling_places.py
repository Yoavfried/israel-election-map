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
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber


DEFAULT_PDF = Path("data/raw/archive_knesset18_kalpilist18.pdf")
DEFAULT_OUT = Path("data/processed/k18_polling_places_extracted_prototype.csv")
DEFAULT_RESOLVED_OUT = Path("data/processed/k18_polling_places_resolved.csv")
K18_RESOURCE_ID = "840edb33-90ac-4176-8ad9-4cdcb8e5caa5"

HEBREW_RE = re.compile(r"[\u0590-\u05ff]")

FIELD_LOCALITY_CODE = "\u05e1\u05de\u05dc \u05d9\u05e9\u05d5\u05d1"
FIELD_LOCALITY_NAME = "\u05e9\u05dd \u05d9\u05e9\u05d5\u05d1"
FIELD_KALPI = "\u05e1\u05de\u05dc \u05e7\u05dc\u05e4\u05d9"
FIELD_ELIGIBLE = "\u05d1\u05d6''\u05d1"
FIELD_ACTUAL = "\u05de\u05e6\u05d1\u05d9\u05e2\u05d9\u05dd"
FIELD_VALID = "\u05db\u05e9\u05e8\u05d9\u05dd"
FIELD_INVALID = "\u05e4\u05e1\u05d5\u05dc\u05d9\u05dd"
SPECIAL_NAME_MARKER = "\u05de\u05e2\u05d8\u05e4"
WRAPPED_SERIAL_MAX_GAP = 14

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

RESOLVED_FIELDS = [
    "resolved_status",
    "match_method",
    "match_score",
    "official_row_id",
    "official_locality_code",
    "official_locality_name",
    "official_kalpi",
    "official_eligible",
    "official_actual",
    "official_valid",
    "official_invalid",
    "pdf_page",
    "pdf_serial",
    "pdf_committee_code",
    "pdf_committee_name",
    "pdf_locality_code",
    "pdf_locality_name",
    "pdf_kalpi",
    "pdf_eligible",
    "address",
    "place",
    "note",
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


def int_value(value) -> int:
    if value is None:
        return 0
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+", text)
    return int(match.group(0)) if match else 0


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
        (row["kalpi_clean"] or row["eligible_clean"])
        and (row["locality_code_clean"] or row["locality_name"] or row["serial_clean"])
        and (row["address"] or row["place"])
    )


def has_vote_identity_shape(row: dict) -> bool:
    return bool(
        (row["kalpi_clean"] or row["eligible_clean"])
        and (row["locality_code_clean"] or row["locality_name"] or row["serial_clean"])
    )


def is_serial_prefix(row: dict) -> bool:
    return bool(
        row["serial_clean"]
        and not row["kalpi_clean"]
        and not row["eligible_clean"]
        and (
            row["locality_code_clean"]
            or row["locality_name"]
            or row["address"]
            or row["place"]
        )
    )


def is_serial_only(row: dict) -> bool:
    if not row["serial_clean"]:
        return False

    for field in [
        "eligible",
        "note",
        "place",
        "address",
        "locality_code",
        "kalpi",
    ]:
        value = row.get(field)
        if not value:
            continue
        if field != "serial" and not HEBREW_RE.search(value) and not re.search(r"\d", value):
            continue
        return False

    return True


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
        if is_serial_prefix(current_row) and index + 1 < len(groups):
            next_row = row_from_words(0, groups[index + 1][1])
            if (
                has_vote_identity_shape(next_row)
                and not next_row["serial_clean"]
                and abs(groups[index + 1][0] - groups[index][0]) <= WRAPPED_SERIAL_MAX_GAP
            ):
                current_words.extend(groups[index + 1][1])
                index += 1
        elif has_data_shape(current_row) and not current_row["serial_clean"]:
            if index + 1 < len(groups):
                next_row = row_from_words(0, groups[index + 1][1])
                if (
                    is_serial_only(next_row)
                    and abs(groups[index + 1][0] - groups[index][0]) <= WRAPPED_SERIAL_MAX_GAP
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
                if has_data_shape(row):
                    rows.append(row)
                    count += 1
            page_counts.append((page_number, count))
    repair_rows(rows)
    return rows, page_counts


def repair_rows(rows: list[dict]) -> None:
    """Fill fields that the OCR drops on otherwise valid data rows.

    The embedded OCR occasionally omits a locality name or committee code from a
    single row even though neighboring rows in the same locality are intact. The
    result-key match uses locality code and kalpi, but keeping names repaired
    makes review CSVs much more legible.
    """
    for index, row in enumerate(rows):
        prev_row = rows[index - 1] if index else None
        next_row = rows[index + 1] if index + 1 < len(rows) else None

        if not row["locality_code_clean"]:
            donor = locality_identity_donor(row, prev_row, next_row)
            if donor:
                row["locality_code"] = donor["locality_code"]
                row["locality_code_clean"] = donor["locality_code_clean"]
                row["locality_name"] = row["locality_name"] or donor["locality_name"]

        for neighbor in (prev_row, next_row):
            if not neighbor:
                continue

            same_page = row["pdf_page"] == neighbor["pdf_page"]
            same_locality_code = (
                row["locality_code_clean"]
                and row["locality_code_clean"] == neighbor["locality_code_clean"]
            )

            if same_page and same_locality_code and not row["locality_name"]:
                row["locality_name"] = neighbor["locality_name"]

            if same_page and not row["committee_code_clean"]:
                row["committee_code"] = neighbor["committee_code"]
                row["committee_code_clean"] = neighbor["committee_code_clean"]

            if same_page and not row["committee_name"]:
                row["committee_name"] = neighbor["committee_name"]


def locality_identity_donor(row: dict, prev_row: dict | None, next_row: dict | None) -> dict | None:
    current_kalpi = first_int_kalpi(row)
    current_serial = int_value(row["serial_clean"])

    if (
        prev_row
        and next_row
        and row["pdf_page"] == prev_row["pdf_page"] == next_row["pdf_page"]
        and prev_row["locality_code_clean"]
        and prev_row["locality_code_clean"] == next_row["locality_code_clean"]
    ):
        return prev_row

    if prev_row and row["pdf_page"] == prev_row["pdf_page"] and prev_row["locality_code_clean"]:
        prev_kalpi = first_int_kalpi(prev_row)
        prev_serial = int_value(prev_row["serial_clean"])
        serial_ok = not current_serial or not prev_serial or current_serial == prev_serial + 1
        if current_kalpi is not None and prev_kalpi is not None and current_kalpi == prev_kalpi + 1 and serial_ok:
            return prev_row

    if next_row and row["pdf_page"] == next_row["pdf_page"] and next_row["locality_code_clean"]:
        next_kalpi = first_int_kalpi(next_row)
        if current_kalpi is not None and next_kalpi is not None and next_kalpi == current_kalpi + 1:
            return next_row

    return None


def first_int_kalpi(row: dict) -> int | None:
    for candidate in kalpi_candidates(row["kalpi"]):
        if re.fullmatch(r"\d+", candidate):
            return int(candidate)
    return None


def write_rows(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in OUTPUT_FIELDS} for row in rows])


def write_resolved_rows(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESOLVED_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in RESOLVED_FIELDS} for row in rows])


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


def norm_name(value) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[\s\"'`.,:/(){}\[\]\-_]+", "", text)
    text = text.replace("\u05f3", "").replace("\u05f4", "")
    return text


def code_candidates(raw_value: str) -> list[str]:
    return [code for code, _ in code_candidates_with_penalty(raw_value)]


def code_candidates_with_penalty(raw_value: str) -> list[tuple[str, int]]:
    digits = "".join(re.findall(r"\d+", str(raw_value or "")))
    candidates: list[tuple[str, int]] = []
    if digits:
        exact = str(int(digits))
        candidates.append((exact, 0))
        for length in (4, 3, 2, 1):
            if len(digits) > length:
                for start in range(0, len(digits) - length + 1):
                    part = digits[start : start + length]
                    if part and int(part) > 0:
                        code = str(int(part))
                        if code != exact:
                            candidates.append((code, 450))

    deduped: dict[str, int] = {}
    for code, penalty in candidates:
        deduped[code] = min(penalty, deduped.get(code, penalty))
    return list(deduped.items())


def kalpi_candidates(raw_value: str) -> list[str]:
    text = str(raw_value or "").replace(",", ".").strip()
    matches = list(re.finditer(r"\d+(?:\.\d+)?", text))
    candidates: list[str] = []

    for match in matches:
        candidate = match.group(0)
        if "." not in candidate:
            candidates.append(str(int(candidate)))
            continue

        whole, fraction = candidate.split(".", 1)
        whole_int = str(int(whole))
        fraction_int = str(int(fraction)) if fraction and int(fraction) else ""
        candidates.append(whole_int)
        if fraction_int:
            candidates.append(f"{whole_int}.{fraction_int}")

            # OCR sometimes stores right-to-left numeric fragments as "0.2"
            # for "2.0" or "0.311" for "113.0".
            candidates.append(fraction_int)
            reversed_fraction = fraction[::-1]
            if reversed_fraction != fraction_int:
                candidates.append(str(int(reversed_fraction)))

    if "." not in text:
        combined_digits = "".join(re.findall(r"\d+", text))
        if len(combined_digits) > 1 and int(combined_digits):
            candidates.append(str(int(combined_digits)))

    return list(dict.fromkeys(candidates))


def fetch_result_records() -> list[dict]:
    result_records: list[dict] = []
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
            code = norm_code(record.get(FIELD_LOCALITY_CODE))
            kalpi = norm_kalpi(record.get(FIELD_KALPI))
            result_records.append(
                {
                    "official_row_id": record.get("_id", ""),
                    "official_locality_code": code,
                    "official_locality_name": str(record.get(FIELD_LOCALITY_NAME, "") or ""),
                    "official_kalpi": kalpi,
                    "official_eligible": int_value(record.get(FIELD_ELIGIBLE)),
                    "official_actual": int_value(record.get(FIELD_ACTUAL)),
                    "official_valid": int_value(record.get(FIELD_VALID)),
                    "official_invalid": int_value(record.get(FIELD_INVALID)),
                    "official_key": (code, kalpi),
                }
            )

        if len(records) < 5000:
            break
        offset += len(records)

    return result_records


def is_special_record(record: dict) -> bool:
    code = record["official_locality_code"]
    name = record["official_locality_name"]
    return not code or code in {"0", "9999"} or SPECIAL_NAME_MARKER in name


def add_edge(
    edges: list[dict],
    row_index: int,
    key: tuple[str, str],
    method: str,
    score: int,
    official_by_key: dict[tuple[str, str], dict],
) -> None:
    if key in official_by_key:
        edges.append(
            {
                "row_index": row_index,
                "key": key,
                "method": method,
                "score": score,
            }
        )


def build_match_edges(
    rows: list[dict],
    official_records: list[dict],
) -> tuple[list[dict], dict[tuple[str, str], dict]]:
    ordinary_records = [record for record in official_records if not is_special_record(record)]
    official_by_key = {
        record["official_key"]: record
        for record in ordinary_records
    }

    codes_by_name: dict[str, set[str]] = defaultdict(set)
    keys_by_code_eligible: dict[tuple[str, int], list[tuple[str, str]]] = defaultdict(list)
    keys_by_name_eligible: dict[tuple[str, int], list[tuple[str, str]]] = defaultdict(list)
    for record in ordinary_records:
        key = record["official_key"]
        name = norm_name(record["official_locality_name"])
        eligible = record["official_eligible"]
        codes_by_name[name].add(record["official_locality_code"])
        if eligible:
            keys_by_code_eligible[(record["official_locality_code"], eligible)].append(key)
            keys_by_name_eligible[(name, eligible)].append(key)

    edges: list[dict] = []
    for row_index, row in enumerate(rows):
        row_eligible = int_value(row["eligible_clean"])
        row_name = norm_name(row["locality_name"])
        raw_codes_with_penalty = code_candidates_with_penalty(row["locality_code"])
        raw_codes = [code for code, _ in raw_codes_with_penalty]
        exact_raw_codes = [code for code, penalty in raw_codes_with_penalty if penalty == 0]
        name_codes = sorted(codes_by_name.get(row_name, set()))
        kalpis = kalpi_candidates(row["kalpi"])

        for code, penalty in raw_codes_with_penalty:
            for kalpi in kalpis:
                key = (code, kalpi)
                record = official_by_key.get(key)
                if not record:
                    continue
                if row_eligible and row_eligible == record["official_eligible"]:
                    method = "raw_code_kalpi_eligible" if penalty == 0 else "raw_code_fragment_kalpi_eligible"
                    add_edge(edges, row_index, key, method, 1000 - penalty, official_by_key)
                else:
                    method = "raw_code_kalpi" if penalty == 0 else "raw_code_fragment_kalpi"
                    add_edge(edges, row_index, key, method, 850 - penalty, official_by_key)

        for code in name_codes:
            for kalpi in kalpis:
                key = (code, kalpi)
                record = official_by_key.get(key)
                if not record:
                    continue
                if row_eligible and row_eligible == record["official_eligible"]:
                    add_edge(edges, row_index, key, "name_code_kalpi_eligible", 950, official_by_key)
                else:
                    add_edge(edges, row_index, key, "name_code_kalpi", 800, official_by_key)

        if row_eligible:
            for code in exact_raw_codes:
                keys = keys_by_code_eligible.get((code, row_eligible), [])
                if len(keys) == 1:
                    add_edge(edges, row_index, keys[0], "raw_code_unique_eligible", 700, official_by_key)

            name_keys = keys_by_name_eligible.get((row_name, row_eligible), [])
            if len(name_keys) == 1:
                add_edge(edges, row_index, name_keys[0], "name_unique_eligible", 650, official_by_key)

    return edges, official_by_key


def kalpi_int(value: str) -> int | None:
    text = str(value or "")
    if not re.fullmatch(r"\d+", text):
        return None
    return int(text)


def assign_greedy_edges(
    rows: list[dict],
    edges: list[dict],
    official_by_key: dict[tuple[str, str], dict],
) -> dict[tuple[str, str], dict]:
    official_order = {key: index for index, key in enumerate(official_by_key)}
    edges = sorted(
        edges,
        key=lambda edge: (
            -edge["score"],
            edge["row_index"],
            official_order.get(edge["key"], 10**9),
            edge["method"],
        ),
    )

    assignments: dict[tuple[str, str], dict] = {}
    assigned_rows: set[int] = set()
    for edge in edges:
        key = edge["key"]
        row_index = edge["row_index"]
        if key in assignments or row_index in assigned_rows:
            continue
        assignments[key] = {
            "row_index": row_index,
            "method": edge["method"],
            "score": edge["score"],
        }
        assigned_rows.add(row_index)

    assign_neighbor_sequence_matches(rows, official_by_key, assignments, assigned_rows)
    return assignments


def assigned_key_for_row(assignments: dict[tuple[str, str], dict], row_index: int) -> tuple[str, str] | None:
    for key, assignment in assignments.items():
        if assignment["row_index"] == row_index:
            return key
    return None


def nearest_assigned_neighbor(
    rows: list[dict],
    assignments: dict[tuple[str, str], dict],
    row_index: int,
    direction: int,
) -> tuple[int, tuple[str, str]] | None:
    page = rows[row_index]["pdf_page"]
    current = row_index + direction
    stop = row_index + (direction * 8)
    while 0 <= current < len(rows) and ((direction > 0 and current <= stop) or (direction < 0 and current >= stop)):
        if rows[current]["pdf_page"] != page:
            return None
        key = assigned_key_for_row(assignments, current)
        if key:
            return current, key
        current += direction
    return None


def assign_neighbor_sequence_matches(
    rows: list[dict],
    official_by_key: dict[tuple[str, str], dict],
    assignments: dict[tuple[str, str], dict],
    assigned_rows: set[int],
) -> None:
    unmatched_keys = set(official_by_key) - set(assignments)
    for row_index, row in enumerate(rows):
        if row_index in assigned_rows:
            continue

        previous = nearest_assigned_neighbor(rows, assignments, row_index, -1)
        following = nearest_assigned_neighbor(rows, assignments, row_index, 1)
        if not previous or not following:
            continue

        previous_key = previous[1]
        following_key = following[1]
        if previous_key[0] != following_key[0]:
            continue

        previous_kalpi = kalpi_int(previous_key[1])
        following_kalpi = kalpi_int(following_key[1])
        if previous_kalpi is None or following_kalpi is None:
            continue
        if following_kalpi - previous_kalpi != 2:
            continue

        target_key = (previous_key[0], str(previous_kalpi + 1))
        if target_key not in unmatched_keys:
            continue

        row_eligible = int_value(row["eligible_clean"])
        target_record = official_by_key[target_key]
        if row_eligible and row_eligible != target_record["official_eligible"]:
            continue

        assignments[target_key] = {
            "row_index": row_index,
            "method": "neighbor_sequence",
            "score": 600,
        }
        assigned_rows.add(row_index)
        unmatched_keys.remove(target_key)


def resolved_row(
    record: dict,
    status: str,
    assignment: dict | None,
    source_row: dict | None,
) -> dict:
    row = {
        "resolved_status": status,
        "match_method": assignment["method"] if assignment else "",
        "match_score": assignment["score"] if assignment else "",
        "official_row_id": record["official_row_id"],
        "official_locality_code": record["official_locality_code"],
        "official_locality_name": record["official_locality_name"],
        "official_kalpi": record["official_kalpi"],
        "official_eligible": record["official_eligible"],
        "official_actual": record["official_actual"],
        "official_valid": record["official_valid"],
        "official_invalid": record["official_invalid"],
    }
    if source_row:
        row.update(
            {
                "pdf_page": source_row["pdf_page"],
                "pdf_serial": source_row["serial_clean"],
                "pdf_committee_code": source_row["committee_code_clean"],
                "pdf_committee_name": source_row["committee_name"],
                "pdf_locality_code": source_row["locality_code_clean"],
                "pdf_locality_name": source_row["locality_name"],
                "pdf_kalpi": source_row["kalpi"],
                "pdf_eligible": source_row["eligible_clean"],
                "address": source_row["address"],
                "place": source_row["place"],
                "note": source_row["note"],
            }
        )
    return row


def reconcile_rows(rows: list[dict], official_records: list[dict]) -> tuple[list[dict], dict]:
    edges, official_by_key = build_match_edges(rows, official_records)
    assignments = assign_greedy_edges(rows, edges, official_by_key)
    resolved: list[dict] = []
    method_counts: Counter[str] = Counter()

    for record in official_records:
        key = record["official_key"]
        if is_special_record(record):
            resolved.append(resolved_row(record, "special_non_geographic", None, None))
            continue

        assignment = assignments.get(key)
        if assignment:
            method_counts[assignment["method"]] += 1
            resolved.append(resolved_row(record, "matched", assignment, rows[assignment["row_index"]]))
        else:
            resolved.append(resolved_row(record, "unmatched", None, None))

    ordinary_rows = [row for row in resolved if row["resolved_status"] != "special_non_geographic"]
    matched_rows = [row for row in ordinary_rows if row["resolved_status"] == "matched"]
    unmatched_rows = [row for row in ordinary_rows if row["resolved_status"] == "unmatched"]
    special_rows = [row for row in resolved if row["resolved_status"] == "special_non_geographic"]
    stats = {
        "official_result_rows": len(official_records),
        "special_non_geographic_rows": len(special_rows),
        "ordinary_result_rows": len(ordinary_rows),
        "matched_ordinary_rows": len(matched_rows),
        "unmatched_ordinary_rows": len(unmatched_rows),
        "unmatched_ordinary_eligible": sum(int_value(row["official_eligible"]) for row in unmatched_rows),
        "unmatched_ordinary_actual": sum(int_value(row["official_actual"]) for row in unmatched_rows),
        "special_actual": sum(int_value(row["official_actual"]) for row in special_rows),
        "method_counts": method_counts,
    }
    return resolved, stats


def validate(rows: list[dict], resolved_out: Path) -> None:
    official_records = fetch_result_records()
    resolved, stats = reconcile_rows(rows, official_records)
    write_resolved_rows(resolved, resolved_out)

    matched = stats["matched_ordinary_rows"]
    ordinary = stats["ordinary_result_rows"]
    print(f"official_result_rows={stats['official_result_rows']}")
    print(f"special_non_geographic_rows={stats['special_non_geographic_rows']}")
    print(f"ordinary_result_rows={ordinary}")
    print(f"matched_ordinary_rows={matched} ({matched / ordinary * 100:.2f}%)")
    print(f"unmatched_ordinary_rows={stats['unmatched_ordinary_rows']}")
    print(f"unmatched_ordinary_eligible={stats['unmatched_ordinary_eligible']}")
    print(f"unmatched_ordinary_actual={stats['unmatched_ordinary_actual']}")
    print(f"special_actual={stats['special_actual']}")
    print(f"resolved_output={resolved_out}")
    print("match_methods=")
    for method, count in stats["method_counts"].most_common():
        print(f"  {method}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--resolved-out", type=Path, default=DEFAULT_RESOLVED_OUT)
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
        validate(rows, args.resolved_out)


if __name__ == "__main__":
    main()
