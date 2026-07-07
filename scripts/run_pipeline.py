from __future__ import annotations

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
    ["scripts/build_final_geography_assignments.py"],
    ["scripts/build_public_outputs.py"],
]


def require_k18_resolved() -> None:
    path = PROCESSED_DIR / "k18_polling_places_resolved.csv"
    if path.exists():
        return
    raise SystemExit(
        "Missing data/processed/k18_polling_places_resolved.csv. "
        "Run: python scripts/extract_k18_polling_places.py --validate"
    )


def main() -> None:
    require_k18_resolved()
    for stage in STAGES:
        print(f"\n==> {' '.join(stage)}", flush=True)
        subprocess.run([sys.executable, *stage], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
