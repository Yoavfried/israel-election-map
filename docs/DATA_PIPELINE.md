# Data Pipeline

Last updated: 2026-07-15

## Run

```bash
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
```

To reuse existing generated geography files while rebuilding every downstream stage:

```bash
python scripts/run_pipeline.py --skip-geographies
```

The pipeline writes generated files under `data/processed/`, which is intentionally gitignored.

## Current Stages

1. Fetch K17-K25 official ballot rows from data.gov.il CKAN datastore.
2. Build 2022 statistical-area, dissolved-locality, reviewed composite-locality, and custom-geometry outputs.
3. Normalize ballot rows and per-election wide vote files.
4. Normalize available polling-place address sources.
5. Build the row-level assignment plan.
6. Build the geocoding input table.
7. Deduplicate geocoding input into unique geocoding work units.
8. Audit normalized address usability and source fidelity.
9. Build independent row-level locality assignments and statistical-area assignments from reviewed geocodes when available.
10. Build public/download-oriented statistical-area, locality, custom, and envelope aggregate CSV outputs.

Reviewed row-level non-geographic exceptions are stored in `data/manual/polling_place_assignment_overrides.csv`. The current override marks Dimona kalpi 91 at `מחנה עדי` in K22-K25 as envelope votes, so those rows do not enter address geocoding.

Direct K17 polling-place scan transcriptions are stored in `data/manual/manual_k17_scanned_place_names.csv`. Reviewed OSM address/stat-area exceptions are stored in `data/manual/manual_osm_address_stat_reviews.csv`; the address lookup validates each record's expected prior status before applying it.

Reviewed election-specific composite municipalities are stored in `data/manual/composite_localities.csv`.

## Current Outputs

- `data/processed/manifest/election_result_resources.csv`
- `data/processed/geographies/statistical_areas_2022.simplified.geojson`
- `data/processed/geographies/localities_2022_dissolved.simplified.geojson`
- `data/processed/geographies/composite_localities.simplified.geojson`
- `data/processed/geographies/custom_geographies.geojson`
- `data/processed/normalized/ballot_rows.csv`
- `data/processed/addresses/polling_place_addresses.csv`
- `data/processed/addresses/polling_place_address_quality_rows.csv`
- `data/processed/addresses/polling_place_address_quality_geocoding_rows.csv`
- `data/processed/addresses/polling_place_address_quality_units.csv`
- `data/processed/addresses/polling_place_address_quality_review_queue.csv`
- `data/processed/addresses/polling_place_address_visual_review_queue.csv`
- `data/processed/addresses/polling_place_locality_only_no_place_units.csv`
- `data/processed/addresses/polling_place_address_quality_summary.csv`
- `data/processed/addresses/polling_place_address_quality_summary.json`
- `data/processed/assignments/ballot_assignment_plan.csv`
- `data/processed/geocoding/geocoding_input.csv`
- `data/processed/geocoding/geocoding_input_summary.csv`
- `data/processed/geocoding/geocoding_work_units.csv`
- `data/processed/geocoding/geocoding_work_unit_rows.csv`
- `data/processed/geocoding/geocoding_address_work_units.csv` filters to plausible street-number-locality queries for the current multi-stat-locality geocoding scope.
- `data/processed/geocoding/geocoding_address_work_unit_rows.csv`
- `data/processed/geocoding/geocoding_address_scope_excluded.csv`
- `data/processed/geocoding/geocoding_manual_queue.csv` flags place-name queries, composite-locality queries, suspicious OCR/address prefixes, and rows without a geocoder query.
- `data/processed/geocoding/geocoding_spike_sample.csv`
- `data/processed/geocoding/govmap_spike_results.csv`
- `data/processed/geocoding/photon_work_unit_results.csv` local Photon candidate output, ignored by git and not a reviewed cache.
- `data/processed/geocoding/geocode_candidate_locality_validation.csv` locality-polygon validation for candidate geocodes, ignored by git.
- `data/processed/geocoding/geocode_candidate_source_ags_validation.csv` source-AGS/stat-area validation for candidate geocodes, ignored by git.
- `data/processed/geocoding/osm_street_stat_lookup.csv` optional OSM street-to-2022-stat-area classification, ignored by git.
- `data/processed/geocoding/osm_street_stat_geocoding_units.csv` optional per-work-unit OSM street assignment candidates, ignored by git.
- `data/processed/geocoding/osm_street_stat_summary.json` optional OSM street assignment summary, ignored by git.
- `data/processed/geocoding/osm_address_stat_geocoding_units.csv` optional exact OSM address-number assignment candidates, ignored by git.
- `data/processed/geocoding/osm_address_stat_canonical_addresses.csv` optional one-row-per-canonical-address OSM resolution audit, ignored by git.
- `data/processed/geocoding/osm_address_stat_matches.csv` optional exact OSM address feature matches, ignored by git.
- `data/processed/geocoding/osm_address_stat_summary.json` optional exact OSM address-number assignment summary, ignored by git.
- `data/processed/geocoding/osm_street_missing_house_number_lookup.csv` optional no-number locality/street classification, ignored by git.
- `data/processed/geocoding/unmatched_location_units.csv` one row per unresolved location signature, ignored by git.
- `data/processed/geocoding/unmatched_location_category_summary.csv` and `unmatched_location_reason_summary.csv` current residual summaries, ignored by git.
- `data/processed/assignments/ballot_geography_assignments.csv`
- `data/processed/public/election_summary.csv`
- `data/processed/public/statistical_area_results/*.csv`
- `data/processed/public/locality_results/*.csv`
- `data/processed/public/custom_geography_results/*.csv`
- `data/processed/public/envelope_results/*.csv`
- `data/processed/public/ballot_contributions/*.csv`
- `data/processed/public/unmapped_rows/*.csv`

## Latest Verified Run

Verified with `python scripts/run_pipeline.py --skip-geographies` on 2026-07-15. The optional OSM address, normal street, missing-number street, and unmatched-inventory stages were then rebuilt from that exact run.

Geography:

| Metric | Count |
|---|---:|
| Statistical-area features in FileGDB | 3,857 |
| Dissolved locality features | 1,329 |
| Single-stat localities | 1,184 |
| Multi-stat localities | 145 |
| Reviewed composite localities | 4 |
| Custom geographies | 4 |

Assignment plan:

| Election | Single-stat rows | Geocode-needed rows | Custom rows | Special rows | Envelope rows | Unresolved rows |
|---|---:|---:|---:|---:|---:|---:|
| K25 | 1,819 | 9,817 | 63 | 8 | 838 | 0 |
| K24 | 1,864 | 10,193 | 62 | 8 | 799 | 0 |
| K23 | 1,605 | 8,964 | 54 | 8 | 548 | 0 |
| K22 | 1,599 | 8,878 | 54 | 8 | 362 | 0 |
| K21 | 1,593 | 8,806 | 54 | 7 | 305 | 0 |
| K20 | 1,547 | 8,516 | 49 | 7 | 295 | 0 |
| K19 | 1,517 | 8,313 | 45 | 6 | 228 | 0 |
| K18 | 1,444 | 7,774 | 41 | 4 | 1 | 0 |
| K17 | 1,250 | 6,986 | 38 | 3 | 149 | 0 |

Locality-mode assignment is independent from the geocode-needed column above. All 92,945 geographic-scope rows, representing 34,783,363 actual voters, are assigned in locality mode. This includes 460 reviewed custom-geography rows and the election-specific composite municipalities. The 3,525 official envelope rows are aggregated separately by election. See `docs/LOCALITY_MODE.md` for the per-election and composite breakdown.

Geocoding input readiness:

| Election | Ready address rows | Place-only rows | Missing address rows | Missing-address actual voters |
|---|---:|---:|---:|---:|
| K25 | 9,817 | 0 | 0 | 0 |
| K24 | 10,193 | 0 | 0 | 0 |
| K23 | 8,964 | 0 | 0 | 0 |
| K22 | 8,878 | 0 | 0 | 0 |
| K21 | 8,806 | 0 | 0 | 0 |
| K20 | 8,516 | 0 | 0 | 0 |
| K19 | 8,307 | 6 | 0 | 0 |
| K18 | 7,739 | 35 | 0 | 0 |
| K17 | 6,530 | 456 | 0 | 0 |

Scoped address work units, refreshed on 2026-07-15:

| Metric | Count |
|---|---:|
| Geocode-needed rows | 78,247 |
| Unique geocoding units | 7,190 |
| Proper street-number-locality address units | 5,663 |
| Proper street-number-locality address rows | 62,506 |
| Units with source AGS metadata | 2,367 |
| Proper address units with source AGS metadata | 2,071 |

The proper-address file is the intended input for the OSM-first address/street pass and any later bulk geocoder fallback:

```bash
python scripts/run_photon_geocoding_spike.py --input data/processed/geocoding/geocoding_address_work_units.csv --output data/processed/geocoding/photon_address_work_unit_results.csv
```

Address-quality audit, refreshed on 2026-07-15:

| Metric | Count |
|---|---:|
| Normalized source rows checked | 93,991 |
| Missing source-evidence links | 0 |
| Normalized/source field mismatches | 0 |
| Address-content review units | 1,525 |
| PDF/OCR units corroborated by a digital election source | 615 |
| PDF/OCR units still requiring visual review | 450 |
| Current locality-only units with no place fallback | 0 |

See `docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md` for definitions and the review-queue contract.

Optional OSM address/street-geometry assignment candidates, refreshed on 2026-07-15:

| Metric | Count |
|---|---:|
| Proper address query units checked | 5,663 |
| Canonical numbered addresses checked | 4,210 |
| OSM `single_stat_street_buffer` query candidates | 1,044 |
| Canonical addresses assigned by the street corridor | 762 |
| Strict exact OSM address-number query candidates | 1,086 |
| Additional query assignments supplied by the house number | 878 |
| Street-buffer or strict exact-address query candidates | 1,922 |
| Canonical addresses assigned by the strict geometry union | 1,346 |
| Reviewed OSM/component-locality assignments | 9 |
| Canonical OSM-first assignments after review | 1,355 |
| Source rows covered by the strict query union | 24,211 |
| Actual voters covered by the strict query union | 9,463,605 |
| Canonical numbered-address residual | 2,855 |

Run with:

```bash
python scripts/build_osm_street_stat_lookup.py
python scripts/build_osm_address_stat_lookup.py
python scripts/build_unmatched_location_inventory.py
```

The resulting analytical inventory assigns 40,048 non-envelope rows to a 2022 statistical area, retains 460 reviewed custom-geography rows, and leaves 4,893 unique unresolved location signatures covering 52,437 ballot rows. These OSM assignments are not yet promoted into the final public output. See `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md` for the category and reason breakdown.

## Current Blockers

- The 450 PDF/OCR-only address-content units without independent digital or reviewed-image corroboration remain a finite visual-decision queue.
- K17 has 456 place-only geocode-needed rows recovered directly from the scanned polling-place lists; the current locality-only/no-place count is zero.
- K19 has 6 place-only geocode-needed rows from the PDF extraction.
- K18 has 35 place-only geocode-needed rows after reviewed OCR corrections moved weak address text into the correct structural category.
- No reviewed production geocode cache exists yet; candidate provider outputs remain `needs_review`.
- GovMap approval/token behavior and coordinate/caching terms still need live verification.
- Photon has a full local candidate run, but candidates must pass point-in-expected-locality validation before promotion. K23 source-AGS/stat-area QA is supplemental diagnostic context only; a polling-place address can serve voters from multiple source AGS values, so even single-source-AGS rows are not a hard building-location truth.
- OSM street-geometry and exact-address-number assignment candidates exist, but they are not yet promoted into `build_final_geography_assignments.py`.
- The official CBS 2008 statistical-area archive must still be obtained to implement historical AGS QA.

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

Rows with rejected/failed/no-match/ambiguous geocode statuses are not used for map assignment. If `review_status` is present, `needs_review`, `pending`, and `unreviewed` are also ignored; use `approved` only after inspection.

See `docs/GEOCODING_SPIKE.md` for provider spikes, candidate validation, and reviewed cache promotion rules.
