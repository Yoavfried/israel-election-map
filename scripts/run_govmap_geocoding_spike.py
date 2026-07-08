from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyproj import Transformer

from pipeline_common import PROCESSED_DIR, normalize_spaces, write_csv


SAMPLE = PROCESSED_DIR / "geocoding" / "geocoding_spike_sample.csv"
OUT = PROCESSED_DIR / "geocoding" / "govmap_spike_results.csv"
GOVMAP_SEARCH_URL = "https://www.govmap.gov.il/api/search-service/api-search"
GOVMAP_DETAIL_URL = "https://www.govmap.gov.il/api/layers-catalog/api-search-result-data"
ITM_TO_WGS84 = Transformer.from_crs("EPSG:2039", "EPSG:4326", always_xy=True)
POINT_RE = re.compile(r"POINT\s*\(\s*([0-9.+-]+)\s+([0-9.+-]+)\s*\)", re.IGNORECASE)


FIELDS = [
    "geocode_key",
    "geocoding_unit_id",
    "geocoder_query",
    "sample_category",
    "geocoder",
    "geocoder_endpoint",
    "geocode_status",
    "geocode_confidence",
    "review_status",
    "longitude",
    "latitude",
    "x_2039",
    "y_2039",
    "coordinate_crs",
    "matched_text",
    "matched_type",
    "matched_score",
    "matched_id",
    "results_count",
    "raw_result_json",
    "raw_detail_json",
    "geocode_notes",
    "geocoded_at",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_point(value: Any) -> tuple[float, float] | None:
    match = POINT_RE.match(normalize_spaces(value))
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset)
    return json.loads(body) if body else {}


def search_govmap(row: dict[str, str], api_key: str, max_results: int, is_accurate: bool, layers: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    payload: dict[str, Any] = {
        "apiKey": api_key,
        "searchText": row["geocoder_query"],
        "language": "he",
        "maxResults": max_results,
        "isAccurate": is_accurate,
    }
    if layers:
        payload["layers"] = layers

    search_response = post_json(GOVMAP_SEARCH_URL, payload)
    results = search_response.get("results") or []
    if not results:
        return search_response, {}

    top_result = results[0]
    detail_payload = {"searchData": top_result, "apiToken": api_key}
    detail_response = post_json(GOVMAP_DETAIL_URL, detail_payload)
    return search_response, detail_response


def output_row(
    unit: dict[str, str],
    status: str,
    search_response: dict[str, Any] | None = None,
    detail_response: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    search_response = search_response or {}
    detail_response = detail_response or {}
    results = search_response.get("results") or []
    top_result = results[0] if results else {}
    centroid = detail_response.get("centroid") or top_result.get("centroid")
    parsed = parse_point(centroid)

    x_2039 = y_2039 = lon = lat = ""
    coordinate_crs = ""
    if parsed:
        x_2039, y_2039 = parsed
        lon, lat = ITM_TO_WGS84.transform(x_2039, y_2039)
        coordinate_crs = "EPSG:2039"

    if status == "matched" and not parsed:
        status = "matched_no_coordinates"

    return {
        "geocode_key": unit["geocoding_unit_id"],
        "geocoding_unit_id": unit["geocoding_unit_id"],
        "geocoder_query": unit["geocoder_query"],
        "sample_category": unit.get("sample_category", ""),
        "geocoder": "govmap_search",
        "geocoder_endpoint": GOVMAP_SEARCH_URL,
        "geocode_status": status,
        "geocode_confidence": top_result.get("score", ""),
        "review_status": "needs_review",
        "longitude": lon,
        "latitude": lat,
        "x_2039": x_2039,
        "y_2039": y_2039,
        "coordinate_crs": coordinate_crs,
        "matched_text": detail_response.get("text") or top_result.get("text", ""),
        "matched_type": detail_response.get("type") or top_result.get("type", ""),
        "matched_score": top_result.get("score", ""),
        "matched_id": top_result.get("id", ""),
        "results_count": search_response.get("resultsCount", len(results)),
        "raw_result_json": json.dumps(top_result, ensure_ascii=False, sort_keys=True),
        "raw_detail_json": json.dumps(detail_response, ensure_ascii=False, sort_keys=True),
        "geocode_notes": error,
        "geocoded_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=SAMPLE)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all rows")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--sleep-ms", type=int, default=250)
    parser.add_argument("--layers", default="", help="Optional comma-separated GovMap search layers/datatypes")
    parser.add_argument("--api-key-env", default="GOVMAP_API_KEY")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inaccurate", action="store_true", help="Use GovMap isAccurate=false")
    args = parser.parse_args()

    rows = read_csv(args.input)
    if args.limit > 0:
        rows = rows[: args.limit]

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not args.dry_run and not api_key:
        raise SystemExit(f"Set {args.api_key_env} or use --dry-run.")

    layers = [item.strip() for item in args.layers.split(",") if item.strip()]
    output: list[dict[str, Any]] = []

    for index, unit in enumerate(rows, start=1):
        if args.dry_run:
            output.append(output_row(unit, "dry_run"))
            continue
        try:
            search_response, detail_response = search_govmap(
                unit,
                api_key=api_key,
                max_results=args.max_results,
                is_accurate=not args.inaccurate,
                layers=layers,
            )
            results = search_response.get("results") or []
            status = "matched" if results else "no_match"
            output.append(output_row(unit, status, search_response, detail_response))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
            output.append(output_row(unit, "error", error=str(exc)))

        if args.sleep_ms > 0 and index < len(rows):
            time.sleep(args.sleep_ms / 1000)

    write_csv(args.output, output, FIELDS)
    status_counts: dict[str, int] = {}
    for row in output:
        status_counts[row["geocode_status"]] = status_counts.get(row["geocode_status"], 0) + 1

    print(f"input_rows={len(rows)}")
    print(f"output={args.output}")
    for status, count in sorted(status_counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
