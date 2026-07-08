# Scripts

Data pipeline scripts are Python-based.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the current pipeline:

```bash
python scripts/run_pipeline.py
```

Stages:

- `fetch_election_results.py` fetches K17-K25 official ballot rows through data.gov.il CKAN datastore and writes a source manifest.
- `build_geographies.py` converts the 2022 statistical-area FileGDB to WGS84 GeoJSON, dissolves localities, creates metadata, and writes custom synthetic geographies.
- `normalize_election_results.py` normalizes official ballot rows into a stable row index and per-election wide vote files.
- `normalize_polling_places.py` normalizes available election-specific polling-place address sources.
- `build_assignment_plan.py` applies envelope detection, reviewed locality crosswalks, single-stat shortcuts, custom buckets, and geocode-needed classification.
- `build_geocoding_input.py` joins the assignment plan to polling-place addresses and emits the rows ready for geocoding.
- `build_geocoding_work_units.py` deduplicates geocoding input rows into unique geocoder queries and row mappings.
- `build_geocoding_spike_sample.py` builds a representative sample of geocoding work units for provider testing.
- `export_geocoding_spike_web.py` exports that representative sample to `web/geocode-spike/sample.json` for the domain-approved browser spike.
- `check_geocode_spike_static.py` validates the static browser spike files and exported sample before deployment.
- `run_govmap_geocoding_spike.py` runs a small GovMap search spike when `GOVMAP_API_KEY` is available; outputs are marked `needs_review`.
- `run_arcgis_geocoding_spike.py` runs the same representative sample against ArcGIS `findAddressCandidates`; outputs are marked `needs_review`.
- `build_final_geography_assignments.py` consumes an optional reviewed geocode cache and writes final row-level geography assignments; without a geocode cache it writes explicit pending-geocode diagnostics.
- `build_public_outputs.py` writes statistical-area, locality, custom-geography, contribution, and unmapped CSV outputs for the website and public downloads.

Dependency note:

- `extract_k18_polling_places.py` extracts and reconciles the scanned/OCRed K18 polling-place PDF. Run it with `--validate` if `data/processed/k18_polling_places_resolved.csv` is missing.

Known current input gap:

- `data/processed/geocoding/geocoded_points.csv` does not exist yet, so final outputs are partial until reviewed coordinates are added.
- The GovMap token request is domain-approved for `yoavfried.com`; use `web/geocode-spike/` for live browser testing if direct Python calls are blocked.
- ArcGIS is being tested as a fallback provider. Retained ArcGIS geocodes should use `forStorage=true` and an access token/API key with stored-geocoding privileges.

Source guardrail:

- `normalize_polling_places.py` fails by default if any required K17-K25 polling-place source is missing. Use `--allow-missing` only for research/debug runs where partial coverage is intentional.
