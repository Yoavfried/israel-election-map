from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from pipeline_common import ensure_dir, write_json


USER_AGENT = "Mozilla/5.0 israel-election-map data pipeline"


def request_json(url: str, params: dict[str, str] | None = None) -> dict:
    data = urlencode(params).encode("utf-8") if params is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        raise RuntimeError(f"ArcGIS request failed: {payload['error']}")
    return payload


def layer_metadata(layer_url: str) -> dict:
    separator = "&" if "?" in layer_url else "?"
    metadata = request_json(f"{layer_url}{separator}f=pjson")
    if metadata.get("type") != "Feature Layer":
        raise ValueError(f"Expected an ArcGIS Feature Layer, got {metadata.get('type')!r}")
    if not metadata.get("objectIdField"):
        raise ValueError("ArcGIS layer metadata has no object ID field")
    return metadata


def object_ids(layer_url: str, object_id_field: str) -> list[int]:
    payload = request_json(
        f"{layer_url}/query",
        {
            "where": "1=1",
            "returnIdsOnly": "true",
            "returnGeometry": "false",
            "f": "json",
        },
    )
    ids = sorted(int(value) for value in payload.get("objectIds") or [])
    if len(ids) != len(set(ids)):
        raise ValueError(f"ArcGIS layer returned duplicate {object_id_field} values")
    return ids


def fetch_features(
    layer_url: str,
    ids: list[int],
    object_id_field: str,
    batch_size: int,
) -> list[dict]:
    features: list[dict] = []
    for offset in range(0, len(ids), batch_size):
        batch_ids = ids[offset : offset + batch_size]
        payload = request_json(
            f"{layer_url}/query",
            {
                "objectIds": ",".join(str(value) for value in batch_ids),
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": object_id_field,
                "f": "geojson",
            },
        )
        if payload.get("type") != "FeatureCollection":
            raise ValueError("ArcGIS query did not return a GeoJSON FeatureCollection")
        batch_features = payload.get("features") or []
        if len(batch_features) != len(batch_ids):
            raise ValueError(
                f"ArcGIS batch at offset {offset} returned {len(batch_features)} features "
                f"for {len(batch_ids)} requested object IDs"
            )
        features.extend(batch_features)
        print(
            f"downloaded_features={len(features)}/{len(ids)}",
            flush=True,
        )

    downloaded_ids = sorted(
        int(feature["properties"][object_id_field]) for feature in features
    )
    if downloaded_ids != ids:
        raise ValueError("Downloaded ArcGIS object IDs do not match the layer ID inventory")
    return features


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Download a complete public ArcGIS FeatureServer layer as WGS84 GeoJSON."
    )
    parser.add_argument("layer_url", help="FeatureServer layer URL, ending in /FeatureServer/<id>")
    parser.add_argument("output", type=Path, help="Destination .geojson path")
    parser.add_argument("--metadata-output", type=Path)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    layer_url = args.layer_url.rstrip("/")
    output = args.output.resolve()
    metadata_output = (
        args.metadata_output.resolve()
        if args.metadata_output
        else output.with_suffix(".metadata.json")
    )
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"Output already exists; pass --overwrite: {output}")

    metadata = layer_metadata(layer_url)
    object_id_field = metadata["objectIdField"]
    ids = object_ids(layer_url, object_id_field)
    max_record_count = int(metadata.get("maxRecordCount") or 1000)
    batch_size = args.batch_size or max_record_count
    if batch_size < 1 or batch_size > max_record_count:
        raise ValueError(
            f"Batch size must be between 1 and the service limit {max_record_count}"
        )

    print(f"layer={metadata.get('name', '')}")
    print(f"object_ids={len(ids)}")
    print(f"batch_size={batch_size}")
    features = fetch_features(layer_url, ids, object_id_field, batch_size)

    ensure_dir(output.parent)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            {"type": "FeatureCollection", "features": features},
            handle,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        handle.write("\n")

    source_record = {
        "source_url": layer_url,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "layer_name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "copyright_text": metadata.get("copyrightText", ""),
        "geometry_type": metadata.get("geometryType", ""),
        "source_spatial_reference": metadata.get("extent", {}).get(
            "spatialReference", {}
        ),
        "output_spatial_reference": "EPSG:4326",
        "object_id_field": object_id_field,
        "feature_count": len(features),
        "max_record_count": max_record_count,
        "fields": metadata.get("fields", []),
        "geojson_sha256": sha256(output),
    }
    write_json(metadata_output, source_record)

    print(f"features={len(features)}")
    print(f"output={output}")
    print(f"metadata={metadata_output}")


if __name__ == "__main__":
    main()
