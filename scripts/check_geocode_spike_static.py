from __future__ import annotations

import json
import sys
from pathlib import Path

from pipeline_common import ROOT


SPIKE_DIR = ROOT / "web" / "geocode-spike"
SAMPLE = SPIKE_DIR / "sample.json"
REQUIRED_SAMPLE_FIELDS = [
    "geocoding_unit_id",
    "geocoder_query",
    "sample_category",
    "geocoder_query_quality",
    "actual_voters",
    "target_locality_names",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require_file(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    html = require_file(SPIKE_DIR / "index.html")
    js = require_file(SPIKE_DIR / "app.js")
    require_file(SPIKE_DIR / "styles.css")
    sample_text = require_file(SAMPLE)

    for needle in ["govmap.api.js", "./app.js", "./styles.css", "apiToken", "dryRunCsv"]:
        if needle not in html:
            fail(f"index.html missing {needle}")

    for needle in [
        'APPROVED_ORIGIN = "https://yoavfried.com"',
        "govmap.search",
        "getSearchResultData",
        'review_status: "needs_review"',
        "Download dry-run CSV",
    ]:
        if needle not in js and needle not in html:
            fail(f"browser spike missing {needle}")

    payload = json.loads(sample_text)
    units = payload.get("units")
    if not isinstance(units, list) or not units:
        fail("sample.json has no units")
    if payload.get("row_count") != len(units):
        fail("sample.json row_count does not match units length")

    seen_ids: set[str] = set()
    for index, unit in enumerate(units, start=1):
        for field in REQUIRED_SAMPLE_FIELDS:
            if not unit.get(field):
                fail(f"sample unit {index} missing {field}")
        unit_id = unit["geocoding_unit_id"]
        if unit_id in seen_ids:
            fail(f"duplicate geocoding_unit_id {unit_id}")
        seen_ids.add(unit_id)

    print(f"static_files=ok")
    print(f"sample_rows={len(units)}")
    print(f"approved_origin=https://yoavfried.com")
    print(f"review_status=needs_review")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
