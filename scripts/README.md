# Scripts

The data pipeline is Python-based. Install dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

## Source Preparation

The repository does not commit raw downloads. Prepare inputs using the source inventory in `docs/DATA_SOURCES.md`.

```bash
python scripts/fetch_election_results.py
python scripts/fetch_cbs_historical_geography.py
```

`fetch_arcgis_feature_layer.py` can download the reviewed ArcGIS layers used for geometry supplements and display footprints. Those layers never replace official election totals.

Archived polling-place files and the canonical 2022 FileGDB are not yet covered by one automatic fresh-clone bootstrap.

## Production Pipeline

```bash
python scripts/run_pipeline.py
```

Reuse already generated 1995, 2008, 2011, and 2022 geography assets:

```bash
python scripts/run_pipeline.py --skip-geographies
```

The production stages are:

- `fetch_election_results.py` fetches official K17-K25 ballot rows and writes a source manifest.
- `build_geographies.py` builds 2022 statistical/locality geometry, composites, custom geometry, display replacements, and the neutral statistical-mode land backdrop.
- `build_historical_geographies.py` builds canonical and display geometry for 1995, 2008, and 2011 statistical areas.
- `normalize_election_results.py` normalizes official ballot rows and party-vote columns.
- `normalize_polling_places.py` normalizes the separate polling-place address dataset.
- `build_assignment_plan.py` applies envelope handling, locality crosswalks, reviewed custom buckets, and address-research classifications.
- `build_historical_ballot_assignments.py` applies official election-specific ballot-to-area crosswalks and the single-historical-area fallback.
- `build_geocoding_input.py`, `build_geocoding_work_units.py`, and `audit_polling_place_address_quality.py` maintain the separate polling-place-location research dataset.
- `build_final_geography_assignments.py` gives official historical assignment precedence and writes independent locality/statistical fields.
- `build_public_outputs.py` writes statistical-area, locality, custom, envelope, contribution, coverage, and pending outputs.
- `build_public_data_release.py` publishes the curated `public-data/v1` ballot
  CSVs, aggregate tables, full-resolution geography ZIPs, metadata, checksums,
  and release validation.

## Assignment Boundary

Election results are not assigned from polling-place addresses. A polling-place building may serve voters from several residential statistical areas. Missing official crosswalk rows therefore remain pending instead of falling through to OSM, Photon, GovMap, or ArcGIS geocoding.

The current production gaps are documented in `docs/PROJECT_STATUS.md` and `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md`.

## Address and Geocoder Research

The retained OSM/GovMap/ArcGIS/Photon scripts support polling-place search, source QA, and a possible future facility layer:

- `build_osm_street_stat_lookup.py` and `build_osm_address_stat_lookup.py` audit whether address features can be located within 2022 areas.
- `build_unmatched_location_inventory.py` reports unresolved polling-place-location signatures.
- `build_geocoding_spike_sample.py`, `export_geocoding_spike_web.py`, and `check_geocode_spike_static.py` maintain the provider-comparison sample.
- `run_govmap_geocoding_spike.py`, `run_arcgis_geocoding_spike.py`, and `run_photon_geocoding_spike.py` create review candidates only.
- `validate_geocode_candidate_localities.py` checks candidate coordinates against expected locality geometry.

Optional service credentials must be supplied through environment variables and must never be committed. The GovMap browser spike accepts its approved origin as runtime configuration rather than embedding a contributor's domain.

## Validation Notes

- Run `python scripts/extract_k18_polling_places.py --validate` if `data/processed/k18_polling_places_resolved.csv` is missing.
- `normalize_polling_places.py` fails by default when a required source or reviewed K18 overlay is absent; `--allow-missing` is for intentionally partial research runs only.
- Reviewed row-level exceptions belong in `data/manual/`, not generated CSV files.
- `--skip-geographies` still validates that all expected generated geography files exist.
