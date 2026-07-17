from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


CATALOG_FOLDER = (
    "/he/publications/doclib/2022/קטלוג/"
    "1. יישובים וחלוקות גאוגרפיות"
)
CATALOG_API = (
    "https://www.cbs.gov.il/he/publications/_api/web/"
    "GetFolderByServerRelativeUrl('{folder}')/Files"
    "?$select=Name,ServerRelativeUrl,Length&$top=500"
)
CBS_ORIGIN = "https://www.cbs.gov.il"

SELECTED_FILES = {
    "Kalpi2006_stat1995.xls": "k17_ballot_to_stat1995.xls",
    "kalpi2008_stat2008.xlsx": "k18_ballot_to_stat2008.xlsx",
    "kalpi2013_stat2011.xlsx": "k19_ballot_to_stat2011.xlsx",
    "kalpi2015_stat2011.xlsx": "k20_ballot_to_stat2011.xlsx",
    "kalpi_April2019_stat2011.xlsx": "k21_ballot_to_stat2011.xlsx",
    "kalpi_September2019_stat2011.xlsx": "k22_ballot_to_stat2011.xlsx",
    "kalpi_March2020_stat2011.xlsx": "k23_ballot_to_stat2011.xlsx",
    "kalpi_March2021_stat2011.xlsx": "k24_ballot_to_stat2011.xlsx",
    "kalpi_November2022_stat2011.xlsx": "k25_ballot_to_stat2011.xlsx",
    "שכבת אזורים סטטיסטיים 1995.zip": "statistical_areas_1995.zip",
    "statisticalareas_demography2008.gdb.zip": "statisticalareas_demography2008.gdb.zip",
    "statisticalareas_demography2020.gdb.zip": "statisticalareas_2020_demography.gdb.zip",
    "conversionkey1995.xls": "statistical_area_conversion_key_1995.xls",
    "conversionkey2008.xls": "statistical_area_conversion_key_2008.xls",
    "מפתח-מעבר-מאזורים-סטטיסטיים-2008-לאזורים-סטטיסטיים-2011.xlsx": "statistical_area_2008_to_2011.xlsx",
    "מפתח-מעבר-מאזורים-סטטיסטיים-2011-לאזורים-סטטיסטיים-2008.xlsx": "statistical_area_2011_to_2008.xlsx",
    "מפתח מעבר אס 2011 לאס 2022.xlsx": "statistical_area_2011_to_2022.xlsx",
    "מפתח מעבר אס 2022 לאס 2011.xlsx": "statistical_area_2022_to_2011.xlsx",
}


def normalized_name(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFC", value)
        if unicodedata.category(character) != "Cf"
    )


def request_bytes(url: str, accept: str | None = None) -> bytes:
    headers = {"User-Agent": "israel-election-map/1.0"}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} for {url}")
        return response.read()


def catalog_url() -> str:
    encoded_folder = urllib.parse.quote(CATALOG_FOLDER, safe="/")
    return CATALOG_API.format(folder=encoded_folder)


def load_catalog(cache_path: Path | None) -> list[dict[str, Any]]:
    if cache_path and cache_path.exists():
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(
            request_bytes(
                catalog_url(),
                "application/json;odata=nometadata",
            ).decode("utf-8")
        )
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
    rows = payload.get("value")
    if not isinstance(rows, list):
        raise ValueError("CBS catalog response does not contain a value array")
    return rows


def validate_file(path: Path, expected_size: int) -> None:
    data = path.read_bytes()
    if len(data) != expected_size:
        raise ValueError(
            f"{path.name} has {len(data):,} bytes; expected {expected_size:,}"
        )
    if path.suffix.lower() in {".xlsx", ".zip"} and not data.startswith(b"PK"):
        raise ValueError(f"{path.name} is not a ZIP/OpenXML file")
    if path.suffix.lower() == ".xls" and not data.startswith(bytes.fromhex("D0CF11E0")):
        raise ValueError(f"{path.name} is not an OLE Excel file")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/cbs_historical_geography"),
    )
    parser.add_argument(
        "--catalog-cache",
        type=Path,
        default=Path("data/raw/cbs_catalog_geography_files.json"),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    catalog = load_catalog(args.catalog_cache)
    by_name: dict[str, dict[str, Any]] = {}
    for row in catalog:
        name = normalized_name(str(row.get("Name", "")))
        if name in by_name:
            raise ValueError(f"Duplicate normalized CBS filename: {name}")
        by_name[name] = row

    missing = sorted(set(SELECTED_FILES) - set(by_name))
    if missing:
        raise ValueError("CBS catalog is missing expected files: " + ", ".join(missing))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    for source_name, local_name in SELECTED_FILES.items():
        source = by_name[source_name]
        expected_size = int(source["Length"])
        source_path = str(source["ServerRelativeUrl"])
        source_url = CBS_ORIGIN + urllib.parse.quote(source_path, safe="/")
        output_path = args.output_dir / local_name

        if args.force or not output_path.exists():
            print(f"downloading {source_name}")
            output_path.write_bytes(request_bytes(source_url))
        validate_file(output_path, expected_size)
        digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
        manifest_rows.append(
            {
                "source_name": source_name,
                "local_name": local_name,
                "source_url": source_url,
                "bytes": expected_size,
                "sha256": digest,
            }
        )

    manifest = {
        "source": "Israel Central Bureau of Statistics public GIS catalog",
        "catalog_url": catalog_url(),
        "files": manifest_rows,
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"files={len(manifest_rows)}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
