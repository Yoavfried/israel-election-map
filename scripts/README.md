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

If the generated 2022 geography files already exist, reuse them while rebuilding every downstream stage:

```bash
python scripts/run_pipeline.py --skip-geographies
```

Stages:

- `fetch_election_results.py` fetches K17-K25 official ballot rows through data.gov.il CKAN datastore and writes a source manifest.
- `build_geographies.py` converts the 2022 statistical-area FileGDB to WGS84 GeoJSON, dissolves localities, creates metadata, and writes custom synthetic geographies.
- `normalize_election_results.py` normalizes official ballot rows into a stable row index and per-election wide vote files.
- `normalize_polling_places.py` normalizes available election-specific polling-place address sources.
- `build_assignment_plan.py` applies envelope detection, reviewed locality crosswalks, row-level polling-place overrides, single-stat shortcuts, custom buckets, and geocode-needed classification.
- `build_geocoding_input.py` joins the assignment plan to polling-place addresses and emits the rows ready for geocoding.
- `build_geocoding_work_units.py` deduplicates geocoding input rows into query-lineage units and row mappings. Canonical physical-address deduplication happens in the OSM address stage.
- `audit_polling_place_address_quality.py` classifies address usability, verifies normalized values against available source evidence, and emits row-level, review, visual-review, and true locality-only/no-place outputs before OSM matching.
- `build_geocoding_spike_sample.py` builds a representative sample of geocoding work units for provider testing.
- `export_geocoding_spike_web.py` exports that representative sample to `web/geocode-spike/sample.json` for the domain-approved browser spike.
- `check_geocode_spike_static.py` validates the static browser spike files and exported sample before deployment.
- `run_govmap_geocoding_spike.py` runs a small GovMap search spike when `GOVMAP_API_KEY` is available; outputs are marked `needs_review`.
- `run_arcgis_geocoding_spike.py` runs the same representative sample against ArcGIS `findAddressCandidates`; outputs are marked `needs_review`.
- `run_photon_geocoding_spike.py` runs the representative sample against a local Photon server at `127.0.0.1:2322`; outputs are marked `needs_review`.
- `validate_geocode_candidate_localities.py` checks candidate geocode coordinates against expected dissolved 2022 locality polygons before any promotion to the reviewed cache.
- `build_osm_street_stat_lookup.py` reads the local Geofabrik PBF street geometries and classifies canonical locality-street pairs by whether the OSM street corridor stays inside one 2022 statistical area.
- `build_osm_address_stat_lookup.py` reads exact OSM `addr:housenumber` objects with `addr:street` or `addr:place` from points, lines, and multipolygons; exact scalar numbers outrank matching multi-value tags, and reviewed exceptions come from `data/manual/manual_osm_address_stat_reviews.csv` with stale-status validation.
- `build_unmatched_location_inventory.py` reconciles non-envelope rows after single-area locality, reviewed custom-geography, exact-address OSM, and missing-number street matches, then emits unique-signature category and reason summaries.
- `build_final_geography_assignments.py` consumes an optional reviewed geocode cache and writes final row-level geography assignments; without a geocode cache it writes explicit pending-geocode diagnostics.
- `build_public_outputs.py` writes statistical-area, locality, custom-geography, contribution, and unmapped CSV outputs for the website and public downloads.

Dependency note:

- `extract_k18_polling_places.py` extracts and reconciles the scanned/OCRed K18 polling-place PDF. Run it with `--validate` if `data/processed/k18_polling_places_resolved.csv` is missing.
- Raw K20-K21 XLS verification requires `xlrd`; the address audit checks `.local/python-audit` before the active Python environment.
- Geography and OSM stages use the active environment, with `.local/python-geo` as an optional workspace-local dependency overlay. `--skip-geographies` still validates that the previously generated geography files exist.

Known current input gap:

- `data/processed/geocoding/geocoded_points.csv` does not exist yet, so final outputs are partial until reviewed coordinates are added.
- The GovMap token request is domain-approved for `yoavfried.com`; use `web/geocode-spike/` for live browser testing if direct Python calls are blocked.
- ArcGIS is being tested as a fallback provider. Retained ArcGIS geocodes should use `forStorage=true` and an access token/API key with stored-geocoding privileges.
- OSM exact-address and street geometry are the first address-placement layers. Photon is a later local fallback; its results require point-in-expected-locality validation before promotion.

Source guardrail:

- `normalize_polling_places.py` fails by default if any required K17-K25 polling-place source or the reviewed K18 scan-review overlay is missing. Use `--allow-missing` only for research/debug runs where partial coverage is intentional. K18 visual corrections and source confirmations belong in `data/manual/manual_k18_address_reviews.csv`, not in the generated resolved-OCR CSV.
- Direct K17 scan place transcriptions belong in `data/manual/manual_k17_scanned_place_names.csv`; K18 values are review leads only and must not be copied as K17 evidence.
- Reviewed row-level exceptions such as the `מחנה עדי` envelope classification belong in `data/manual/polling_place_assignment_overrides.csv`.

