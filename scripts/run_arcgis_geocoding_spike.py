from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline_common import PROCESSED_DIR, normalize_spaces, write_csv


SAMPLE = PROCESSED_DIR / "geocoding" / "geocoding_spike_sample.csv"
OUT = PROCESSED_DIR / "geocoding" / "arcgis_spike_results.csv"
ARCGIS_FIND_ADDRESS_URL = "https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
LEGACY_ARCGIS_FIND_ADDRESS_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
DEFAULT_SEARCH_EXTENT = "34.1,29.3,35.9,33.6"
DEFAULT_LOCATION = "34.8516,31.0461"
DEFAULT_OUT_FIELDS = ",".join(
    [
        "Match_addr",
        "Addr_type",
        "MatchID",
        "StAddr",
        "City",
        "Region",
        "Country",
        "Score",
        "Type",
        "PlaceName",
    ]
)


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
    "for_storage",
    "arcgis_source_country",
    "arcgis_lang_code",
    "arcgis_location_type",
    "arcgis_fallback_used",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset)
    return json.loads(body) if body else {}


def arcgis_error(response: dict[str, Any]) -> str:
    error = response.get("error") or {}
    if not error:
        return ""
    details = error.get("details") or []
    detail_text = "; ".join(str(item) for item in details if item)
    message = normalize_spaces(error.get("message", ""))
    code = normalize_spaces(error.get("code", ""))
    return " ".join(part for part in [f"ArcGIS error {code}".strip(), message, detail_text] if part)


def search_arcgis(
    row: dict[str, str],
    token: str,
    endpoint: str,
    max_locations: int,
    source_country: str,
    lang_code: str,
    search_extent: str,
    location: str,
    location_type: str,
    out_fields: str,
    for_storage: bool,
    fallback_no_source_country: bool,
) -> tuple[dict[str, Any], bool]:
    base_params: dict[str, Any] = {
        "f": "json",
        "SingleLine": row["geocoder_query"],
        "outFields": out_fields,
        "outSR": 4326,
        "maxLocations": max_locations,
        "forStorage": str(for_storage).lower(),
        "langCode": lang_code,
        "locationType": location_type,
    }
    if token:
        base_params["token"] = token
    if search_extent:
        base_params["searchExtent"] = search_extent
    if location:
        base_params["location"] = location
    if source_country:
        base_params["sourceCountry"] = source_country

    response = get_json(endpoint, base_params)
    if (
        fallback_no_source_country
        and source_country
        and not response.get("error")
        and not response.get("candidates")
    ):
        fallback_params = dict(base_params)
        fallback_params.pop("sourceCountry", None)
        fallback_response = get_json(endpoint, fallback_params)
        if fallback_response.get("candidates") or fallback_response.get("error"):
            return fallback_response, True

    return response, False


def output_row(
    unit: dict[str, str],
    status: str,
    endpoint: str,
    for_storage: bool,
    source_country: str,
    lang_code: str,
    location_type: str,
    fallback_used: bool = False,
    response: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    response = response or {}
    candidates = response.get("candidates") or []
    top_candidate = candidates[0] if candidates else {}
    attributes = top_candidate.get("attributes") or {}
    location = top_candidate.get("location") or {}

    lon = location.get("x", "")
    lat = location.get("y", "")
    coordinate_crs = "EPSG:4326" if lon != "" and lat != "" else ""

    if response_error := arcgis_error(response):
        status = "error"
        error = response_error
    elif status == "matched" and not coordinate_crs:
        status = "matched_no_coordinates"

    matched_text = attributes.get("Match_addr") or top_candidate.get("address", "")
    matched_type = attributes.get("Addr_type") or attributes.get("Type", "")
    matched_score = top_candidate.get("score", attributes.get("Score", ""))

    return {
        "geocode_key": unit["geocoding_unit_id"],
        "geocoding_unit_id": unit["geocoding_unit_id"],
        "geocoder_query": unit["geocoder_query"],
        "sample_category": unit.get("sample_category", ""),
        "geocoder": "arcgis_find_address_candidates",
        "geocoder_endpoint": endpoint,
        "geocode_status": status,
        "geocode_confidence": matched_score,
        "review_status": "needs_review",
        "longitude": lon,
        "latitude": lat,
        "x_2039": "",
        "y_2039": "",
        "coordinate_crs": coordinate_crs,
        "matched_text": matched_text,
        "matched_type": matched_type,
        "matched_score": matched_score,
        "matched_id": attributes.get("MatchID", ""),
        "results_count": len(candidates),
        "raw_result_json": json.dumps(top_candidate, ensure_ascii=False, sort_keys=True),
        "raw_detail_json": json.dumps(response, ensure_ascii=False, sort_keys=True),
        "geocode_notes": error,
        "geocoded_at": datetime.now(timezone.utc).isoformat(),
        "for_storage": str(for_storage).lower(),
        "arcgis_source_country": source_country,
        "arcgis_lang_code": lang_code,
        "arcgis_location_type": location_type,
        "arcgis_fallback_used": str(fallback_used).lower(),
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=SAMPLE)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all rows")
    parser.add_argument("--max-locations", type=int, default=3)
    parser.add_argument("--sleep-ms", type=int, default=250)
    parser.add_argument("--api-key-env", default="ARCGIS_ACCESS_TOKEN")
    parser.add_argument("--endpoint", default=ARCGIS_FIND_ADDRESS_URL)
    parser.add_argument("--legacy-endpoint", action="store_true")
    parser.add_argument("--source-country", default="ISR")
    parser.add_argument("--lang-code", default="HE")
    parser.add_argument("--search-extent", default=DEFAULT_SEARCH_EXTENT)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    parser.add_argument("--location-type", default="rooftop", choices=["rooftop", "street"])
    parser.add_argument("--out-fields", default=DEFAULT_OUT_FIELDS)
    parser.add_argument("--no-fallback-no-source-country", action="store_true")
    parser.add_argument("--temporary", action="store_true", help="Use forStorage=false. Do not persist or promote these results.")
    parser.add_argument("--allow-no-token", action="store_true", help="Probe without a token; expected to fail if ArcGIS enforces auth.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = read_csv(args.input)
    if args.limit > 0:
        rows = rows[: args.limit]

    endpoint = LEGACY_ARCGIS_FIND_ADDRESS_URL if args.legacy_endpoint else args.endpoint
    token = os.environ.get(args.api_key_env, "").strip()
    if not args.dry_run and not token and not args.allow_no_token:
        raise SystemExit(f"Set {args.api_key_env}, use --allow-no-token for an auth probe, or use --dry-run.")

    for_storage = not args.temporary
    output: list[dict[str, Any]] = []

    for index, unit in enumerate(rows, start=1):
        if args.dry_run:
            output.append(
                output_row(
                    unit,
                    "dry_run",
                    endpoint=endpoint,
                    for_storage=for_storage,
                    source_country=args.source_country,
                    lang_code=args.lang_code,
                    location_type=args.location_type,
                )
            )
            continue

        try:
            response, fallback_used = search_arcgis(
                unit,
                token=token,
                endpoint=endpoint,
                max_locations=args.max_locations,
                source_country=args.source_country,
                lang_code=args.lang_code,
                search_extent=args.search_extent,
                location=args.location,
                location_type=args.location_type,
                out_fields=args.out_fields,
                for_storage=for_storage,
                fallback_no_source_country=not args.no_fallback_no_source_country,
            )
            candidates = response.get("candidates") or []
            status = "matched" if candidates else "no_match"
            output.append(
                output_row(
                    unit,
                    status,
                    endpoint=endpoint,
                    for_storage=for_storage,
                    source_country="" if fallback_used else args.source_country,
                    lang_code=args.lang_code,
                    location_type=args.location_type,
                    fallback_used=fallback_used,
                    response=response,
                )
            )
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
            output.append(
                output_row(
                    unit,
                    "error",
                    endpoint=endpoint,
                    for_storage=for_storage,
                    source_country=args.source_country,
                    lang_code=args.lang_code,
                    location_type=args.location_type,
                    error=str(exc),
                )
            )

        if args.sleep_ms > 0 and index < len(rows):
            time.sleep(args.sleep_ms / 1000)

    write_csv(args.output, output, FIELDS)
    status_counts: dict[str, int] = {}
    for row in output:
        status_counts[row["geocode_status"]] = status_counts.get(row["geocode_status"], 0) + 1

    print(f"input_rows={len(rows)}")
    print(f"output={args.output}")
    print(f"endpoint={endpoint}")
    print(f"for_storage={str(for_storage).lower()}")
    for status, count in sorted(status_counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
