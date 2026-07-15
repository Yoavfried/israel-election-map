from __future__ import annotations

import re
from typing import Any

from pipeline_common import normalize_spaces


NUMBERED_AREA_PREFIXES = {
    "\u05e8\u05d7",  # street abbreviation
    "\u05e8\u05d7\u05d5\u05d1",  # street
    "\u05e9\u05db",  # neighborhood abbreviation
    "\u05e9\u05db\u05d5\u05e0\u05d4",  # neighborhood
}
HOUSE_NUMBER_RE = re.compile(r"(?<!\d)0*(\d{1,4})\s*([\u0590-\u05ff]?)(?!\d)")


def normalize_house_number(value: Any) -> str:
    text = normalize_spaces(value)
    text = text.replace('"', "").replace("'", "").replace("\u05f3", "").replace("\u05f4", "")
    text = re.sub(r"\s+", "", text)
    match = re.fullmatch(r"0*(\d{1,4})([\u0590-\u05ff]?)", text)
    if not match:
        return ""
    return f"{int(match.group(1))}{match.group(2)}"


def parse_address_parts(address: Any) -> tuple[str, str]:
    text = normalize_spaces(address).replace('"', "").replace("'", "")
    if not text:
        return "", ""

    if "," in text:
        street, remainder = text.split(",", 1)
        match = HOUSE_NUMBER_RE.search(normalize_spaces(remainder))
        return normalize_spaces(street), normalize_house_number("".join(match.groups())) if match else ""

    matches = list(HOUSE_NUMBER_RE.finditer(text))
    if not matches:
        return text, ""

    if len(matches) == 1:
        match = matches[0]
        prefix = normalize_spaces(text[: match.start()])
        if prefix in NUMBERED_AREA_PREFIXES:
            return text, ""
    else:
        match = matches[-1]

    street = normalize_spaces(text[: match.start()].rstrip(" ,-"))
    house_number = normalize_house_number("".join(match.groups()))
    return street, house_number


def parse_street_name(address: Any) -> str:
    street, _ = parse_address_parts(address)
    return street


def parse_house_number(address: Any) -> str:
    _, house_number = parse_address_parts(address)
    return house_number


def has_house_number(address: Any) -> bool:
    return bool(parse_house_number(address))
