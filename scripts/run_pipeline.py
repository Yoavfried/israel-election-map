from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from pipeline_common import PROCESSED_DIR, ROOT


STAGES = [
    ["scripts/fetch_election_results.py"],
    ["scripts/build_geographies.py"],
    ["scripts/normalize_election_results.py"],
    ["scripts/normalize_polling_places.py"],
    ["scripts/build_assignment_plan.py"],
    ["scripts/build_geocoding_input.py"],
    ["scripts/build_geocoding_work_units.py"],
    ["scripts/audit_polling_place_address_quality.py"],
    ["scripts/build_final_geography_assignments.py"],
    ["scripts/build_public_outputs.py"],
]

GEOGRAPHY_OUTPUTS = [
    PROCESSED_DIR / "geographies" / "statistical_areas_2022.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2022.metadata.csv",
    PROCESSED_DIR / "geographies" / "localities_2022_dissolved.geojson",
    PROCESSED_DIR / "geographies" / "composite_localities.simplified.geojson",
]


def require_k18_resolved() -> None:
    path = PROCESSED_DIR / "k18_polling_places_resolved.csv"
    if path.exists():
        return
    raise SystemExit(
        "Missing data/processed/k18_polling_places_resolved.csv. "
        "Run: python scripts/extract_k18_polling_places.py --validate"
    )


def require_existing_geographies() -> None:
    missing = [path for path in GEOGRAPHY_OUTPUTS if not path.exists()]
    if not missing:
        return
    rendered = ", ".join(str(path.relative_to(ROOT)) for path in missing)
    raise SystemExit(
        "--skip-geographies requires existing generated geography files. "
        f"Missing: {rendered}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-geographies",
        action="store_true",
        help="Reuse existing generated geography files instead of running the GeoPandas stage.",
    )
    args = parser.parse_args()

    require_k18_resolved()
    if args.skip_geographies:
        require_existing_geographies()
    for stage in STAGES:
        if args.skip_geographies and stage == ["scripts/build_geographies.py"]:
            print("\n==> scripts/build_geographies.py (reusing existing outputs)", flush=True)
            continue
        print(f"\n==> {' '.join(stage)}", flush=True)
        subprocess.run([sys.executable, *stage], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
