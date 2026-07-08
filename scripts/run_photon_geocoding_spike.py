from __future__ import annotations

import argparse
import csv
import json
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
OUT = PROCESSED_DIR / "geocoding" / "photon_spike_results.csv"
DEFAULT_ENDPOINT = "http://127.0.0.1:2322/api"
DEFAULT_BBOX = "34.1,29.3,35.9,33.6"
DEFAULT_LAT = "31.0461"
DEFAULT_LON = "34.8516"


FIELDS = [
    "geocode_key",
    "geocoding_unit_id",
    "geocoder_query",
    "sample_category",
    "target_locality_names",
    "photon_locality_match_status",
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
    "photon_countrycode",
    "photon_state",
    "photon_county",
    "photon_city",
    "photon_district",
    "photon_street",
    "photon_osm_key",
    "photon_osm_value",
    "photon_osm_type",
    "photon_osm_id",
    "photon_bbox",
    "photon_bias_lat",
    "photon_bias_lon",
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


def search_photon(
    row: dict[str, str],
    endpoint: str,
    limit: int,
    lang: str,
    bbox: str,
    lat: str,
    lon: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": row["geocoder_query"],
        "limit": limit,
        "lang": lang,
    }
    if bbox:
        params["bbox"] = bbox
    if lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    return get_json(endpoint, params)


def normalize_locality_for_compare(value: Any) -> str:
    text = normalize_spaces(value).replace("\u05be", "-").replace("\u2013", "-")
    for char in [" ", "-", "\'", "\"", ".", ",", "(", ")", "[", "]", "{", "}", "\u05f3", "\u05f4"]:
        text = text.replace(char, "")
    return text.lower()


def locality_match_status(unit: dict[str, str], feature: dict[str, Any]) -> str:
    expected = [item for item in unit.get("target_locality_names", "").split("|") if item]
    if not expected or not feature:
        return "not_checked"

    properties = feature.get("properties") or {}
    candidates = [
        properties.get("city", ""),
        properties.get("district", ""),
        properties.get("county", ""),
        properties.get("state", ""),
        photon_feature_label(feature),
    ]
    expected_norm = [normalize_locality_for_compare(item) for item in expected]
    candidate_norm = [normalize_locality_for_compare(item) for item in candidates if item]

    for expected_item in expected_norm:
        if not expected_item:
            continue
        for candidate_item in candidate_norm:
            if expected_item in candidate_item or candidate_item in expected_item:
                return "expected_locality_seen"
    return "expected_locality_not_seen"


def photon_feature_label(feature: dict[str, Any]) -> str:
    properties = feature.get("properties") or {}
    parts = [
        properties.get("name", ""),
        properties.get("street", ""),
        properties.get("housenumber", ""),
        properties.get("district", ""),
        properties.get("city", ""),
        properties.get("county", ""),
        properties.get("state", ""),
        properties.get("country", ""),
    ]
    seen: set[str] = set()
    clean_parts: list[str] = []
    for part in parts:
        clean = normalize_spaces(part)
        if clean and clean not in seen:
            seen.add(clean)
            clean_parts.append(clean)
    return ", ".join(clean_parts)


def output_row(
    unit: dict[str, str],
    status: str,
    endpoint: str,
    bbox: str,
    lat_bias: str,
    lon_bias: str,
    response: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    response = response or {}
    features = response.get("features") or []
    top_feature = features[0] if features else {}
    properties = top_feature.get("properties") or {}
    geometry = top_feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []

    lon = lat = ""
    if len(coordinates) >= 2:
        lon, lat = coordinates[0], coordinates[1]
    coordinate_crs = "EPSG:4326" if lon != "" and lat != "" else ""

    if status == "matched" and not coordinate_crs:
        status = "matched_no_coordinates"

    osm_type = normalize_spaces(properties.get("osm_type", ""))
    osm_id = normalize_spaces(properties.get("osm_id", ""))
    matched_id = ":".join(part for part in [osm_type, osm_id] if part)

    return {
        "geocode_key": unit["geocoding_unit_id"],
        "geocoding_unit_id": unit["geocoding_unit_id"],
        "geocoder_query": unit["geocoder_query"],
        "sample_category": unit.get("sample_category", ""),
        "target_locality_names": unit.get("target_locality_names", ""),
        "photon_locality_match_status": locality_match_status(unit, top_feature),
        "geocoder": "photon_local",
        "geocoder_endpoint": endpoint,
        "geocode_status": status,
        "geocode_confidence": "",
        "review_status": "needs_review",
        "longitude": lon,
        "latitude": lat,
        "x_2039": "",
        "y_2039": "",
        "coordinate_crs": coordinate_crs,
        "matched_text": photon_feature_label(top_feature),
        "matched_type": properties.get("type", ""),
        "matched_score": "",
        "matched_id": matched_id,
        "results_count": len(features),
        "raw_result_json": json.dumps(top_feature, ensure_ascii=False, sort_keys=True),
        "raw_detail_json": json.dumps(response, ensure_ascii=False, sort_keys=True),
        "geocode_notes": error,
        "geocoded_at": datetime.now(timezone.utc).isoformat(),
        "photon_countrycode": properties.get("countrycode", ""),
        "photon_state": properties.get("state", ""),
        "photon_county": properties.get("county", ""),
        "photon_city": properties.get("city", ""),
        "photon_district": properties.get("district", ""),
        "photon_street": properties.get("street", ""),
        "photon_osm_key": properties.get("osm_key", ""),
        "photon_osm_value": properties.get("osm_value", ""),
        "photon_osm_type": osm_type,
        "photon_osm_id": osm_id,
        "photon_bbox": bbox,
        "photon_bias_lat": lat_bias,
        "photon_bias_lon": lon_bias,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=SAMPLE)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all input rows")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--sleep-ms", type=int, default=0)
    parser.add_argument("--lang", default="he")
    parser.add_argument("--bbox", default=DEFAULT_BBOX, help="Photon bbox: minLon,minLat,maxLon,maxLat. Empty disables bbox.")
    parser.add_argument("--lat", default=DEFAULT_LAT, help="Optional Photon location-bias latitude. Empty disables bias.")
    parser.add_argument("--lon", default=DEFAULT_LON, help="Optional Photon location-bias longitude. Empty disables bias.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = read_csv(args.input)
    if args.limit > 0:
        rows = rows[: args.limit]

    output: list[dict[str, Any]] = []
    for index, unit in enumerate(rows, start=1):
        if args.dry_run:
            output.append(output_row(unit, "dry_run", args.endpoint, args.bbox, args.lat, args.lon))
            continue

        try:
            response = search_photon(
                unit,
                endpoint=args.endpoint,
                limit=args.max_results,
                lang=args.lang,
                bbox=args.bbox,
                lat=args.lat,
                lon=args.lon,
            )
            features = response.get("features") or []
            status = "matched" if features else "no_match"
            output.append(output_row(unit, status, args.endpoint, args.bbox, args.lat, args.lon, response=response))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as exc:
            output.append(output_row(unit, "error", args.endpoint, args.bbox, args.lat, args.lon, error=str(exc)))

        if args.sleep_ms > 0 and index < len(rows):
            time.sleep(args.sleep_ms / 1000)

    write_csv(args.output, output, FIELDS)
    status_counts: dict[str, int] = {}
    for row in output:
        status_counts[row["geocode_status"]] = status_counts.get(row["geocode_status"], 0) + 1

    print(f"input_rows={len(rows)}")
    print(f"output={args.output}")
    print(f"endpoint={args.endpoint}")
    for status, count in sorted(status_counts.items()):
        print(f"{status}={count}")


if __name__ == "__main__":
    main()
