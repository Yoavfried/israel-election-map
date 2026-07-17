from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from pipeline_common import PROCESSED_DIR, ROOT


STAGES = [
    ["scripts/fetch_election_results.py"],
    ["scripts/build_geographies.py"],
    ["scripts/build_historical_geographies.py"],
    ["scripts/normalize_election_results.py"],
    ["scripts/build_assignment_plan.py"],
    ["scripts/build_historical_ballot_assignments.py"],
    ["scripts/audit_arcgis_assignment_reconstruction.py"],
    ["scripts/build_final_geography_assignments.py"],
    ["scripts/build_public_outputs.py"],
    ["scripts/build_public_data_release.py"],
]

GEOGRAPHY_OUTPUTS = [
    PROCESSED_DIR / "geographies" / "statistical_areas_2022.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2022.metadata.csv",
    PROCESSED_DIR / "geographies" / "localities_2022_dissolved.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2022.display.simplified.geojson",
    PROCESSED_DIR / "geographies" / "localities_2022_dissolved.display.simplified.geojson",
    PROCESSED_DIR / "geographies" / "composite_localities.simplified.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_1995.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2008.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2011.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_1995.display.simplified.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2008.display.simplified.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_2011.display.simplified.geojson",
    PROCESSED_DIR / "geographies" / "statistical_areas_1995.metadata.csv",
    PROCESSED_DIR / "geographies" / "statistical_areas_2008.metadata.csv",
    PROCESSED_DIR / "geographies" / "statistical_areas_2011.metadata.csv",
    PROCESSED_DIR / "geographies" / "statistical_areas_1995.aliases.csv",
    PROCESSED_DIR / "geographies" / "statistical_areas_2008.aliases.csv",
    PROCESSED_DIR / "geographies" / "statistical_areas_2011.aliases.csv",
]


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

    if args.skip_geographies:
        require_existing_geographies()
    for stage in STAGES:
        if args.skip_geographies and stage in (
            ["scripts/build_geographies.py"],
            ["scripts/build_historical_geographies.py"],
        ):
            print(f"\n==> {' '.join(stage)} (reusing existing outputs)", flush=True)
            continue
        print(f"\n==> {' '.join(stage)}", flush=True)
        subprocess.run([sys.executable, *stage], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
