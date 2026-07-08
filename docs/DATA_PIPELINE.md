# Data Pipeline

Last updated: 2026-07-07

## Run

```bash
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
```

The pipeline writes generated files under `data/processed/`, which is intentionally gitignored.

## Current Stages

1. Fetch K17-K25 official ballot rows from data.gov.il CKAN datastore.
2. Build 2022 statistical-area, dissolved-locality, and custom-geometry outputs.
3. Normalize ballot rows and per-election wide vote files.
4. Normalize available polling-place address sources.
5. Build the row-level assignment plan.
6. Build the geocoding input table.
7. Deduplicate geocoding input into unique geocoding work units.
8. Build final row-level geography assignments from reviewed geocodes when available.
9. Build public/download-oriented aggregate CSV outputs.

## Current Outputs

- `data/processed/manifest/election_result_resources.csv`
- `data/processed/geographies/statistical_areas_2022.simplified.geojson`
- `data/processed/geographies/localities_2022_dissolved.simplified.geojson`
- `data/processed/geographies/custom_geographies.geojson`
- `data/processed/normalized/ballot_rows.csv`
- `data/processed/addresses/polling_place_addresses.csv`
- `data/processed/assignments/ballot_assignment_plan.csv`
- `data/processed/geocoding/geocoding_input.csv`
- `data/processed/geocoding/geocoding_input_summary.csv`
- `data/processed/geocoding/geocoding_work_units.csv`
- `data/processed/geocoding/geocoding_work_unit_rows.csv`
- `data/processed/geocoding/geocoding_manual_queue.csv` flags place-name queries, composite-locality queries, suspicious OCR/address prefixes, and rows without a geocoder query.
- `data/processed/assignments/ballot_geography_assignments.csv`
- `data/processed/public/election_summary.csv`
- `data/processed/public/statistical_area_results/*.csv`
- `data/processed/public/locality_results/*.csv`
- `data/processed/public/custom_geography_results/*.csv`
- `data/processed/public/ballot_contributions/*.csv`
- `data/processed/public/unmapped_rows/*.csv`

## Latest Verified Run

Verified with `python scripts/run_pipeline.py` on 2026-07-07.

Geography:

| Metric | Count |
|---|---:|
| Statistical-area features in FileGDB | 3,857 |
| Dissolved locality features | 1,329 |
| Single-stat localities | 1,184 |
| Multi-stat localities | 145 |
| Custom geographies | 4 |

Assignment plan:

| Election | Single-stat rows | Geocode-needed rows | Custom rows | Special rows | Envelope rows | Unresolved rows |
|---|---:|---:|---:|---:|---:|---:|
| K25 | 1,803 | 9,834 | 63 | 7 | 838 | 0 |
| K24 | 1,863 | 10,195 | 62 | 7 | 799 | 0 |
| K23 | 1,603 | 8,967 | 54 | 7 | 548 | 0 |
| K22 | 1,597 | 8,881 | 54 | 7 | 362 | 0 |
| K21 | 1,591 | 8,808 | 54 | 7 | 305 | 0 |
| K20 | 1,544 | 8,519 | 49 | 7 | 295 | 0 |
| K19 | 1,515 | 8,315 | 45 | 6 | 228 | 0 |
| K18 | 1,438 | 7,780 | 41 | 4 | 1 | 0 |
| K17 | 1,241 | 6,995 | 38 | 3 | 149 | 0 |

Geocoding input readiness:

| Election | Ready address rows | Place-only rows | Missing address rows | Missing-address actual voters |
|---|---:|---:|---:|---:|
| K25 | 9,834 | 0 | 0 | 0 |
| K24 | 10,195 | 0 | 0 | 0 |
| K23 | 8,967 | 0 | 0 | 0 |
| K22 | 8,881 | 0 | 0 | 0 |
| K21 | 8,808 | 0 | 0 | 0 |
| K20 | 8,519 | 0 | 0 | 0 |
| K19 | 8,309 | 6 | 0 | 0 |
| K18 | 7,769 | 11 | 0 | 0 |
| K17 | 6,984 | 11 | 0 | 0 |

## Current Blockers

- K17 has 11 place-only geocode-needed rows recovered from targeted review of the scanned polling-place lists.
- K19 has 6 place-only geocode-needed rows from the PDF extraction.
- K18 has 11 place-only geocode-needed rows from the OCR/PDF extraction.
- GovMap geocoding provider terms, caching permission, API key flow, rate limits, and coordinate-system behavior still need a spike before bulk geocoding.

## Geocode Cache Contract

`scripts/build_final_geography_assignments.py` accepts an optional reviewed geocode cache at:

- `data/processed/geocoding/geocoded_points.csv`

Supported key columns:

- `geocode_key` preferred. Use `geocoding_unit_id` values from `data/processed/geocoding/geocoding_work_units.csv` for deduplicated geocoding.
- `source_row_uid` is still accepted for row-specific/manual geocodes.

Supported coordinates:

- WGS84: `longitude`/`latitude`, `lon`/`lat`, or `lng`/`lat`.
- Israel TM: `x_2039`/`y_2039`, `itm_x`/`itm_y`, or `x`/`y`; defaults to `EPSG:2039` unless a single `coordinate_crs` value is present.

Optional provenance columns:

- `geocoder`
- `geocode_status`
- `geocode_confidence`
- `review_status`

Rows with rejected/failed/no-match statuses are not used for map assignment.
