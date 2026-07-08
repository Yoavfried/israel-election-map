# Geocoding Spike

Last updated: 2026-07-08

## Goal

Before bulk geocoding, validate a small representative sample of deduplicated polling-place queries.

The spike must answer:

- Does the provider return accurate results for Hebrew street addresses?
- Does it handle polling-place and school names, not only street addresses?
- Does it expose enough result metadata to detect ambiguity?
- Which coordinate system is returned, and can it be converted reproducibly?
- Are caching and publishing reviewed coordinates allowed?

## Representative Sample

Build the sample with:

```bash
python scripts/build_geocoding_spike_sample.py
```

Output:

- `data/processed/geocoding/geocoding_spike_sample.csv`
- `data/processed/geocoding/geocoding_spike_sample_summary.json`

The sample includes:

- clean full-address queries,
- heavily reused queries,
- place-with-locality queries,
- K17/K18/K19 place-only queries,
- composite-locality historical split/merge queries,
- suspicious OCR-prefix queries,
- high-voter manual-review queries,
- highest-voter queries overall.

## GovMap Candidate

Primary docs:

- Search API docs: https://api.govmap.gov.il/docs/search-functions/search
- Search result detail docs: https://api.govmap.gov.il/docs/search-functions/get-search-result-data
- Geocode JS docs: https://api.govmap.gov.il/docs/javascript-functions/geocode

GovMap API keys are domain-approved. The current request is for `yoavfried.com`, so the primary live spike path is the browser page documented in:

- `docs/GOVMAP_BROWSER_SPIKE.md`

Prepare the browser sample payload with:

```bash
python scripts/export_geocoding_spike_web.py
```

Output:

- `web/geocode-spike/sample.json`

The browser page calls GovMap from the approved domain and exports a CSV with the same review-oriented output contract as the Python spike.

The current spike script uses the same public service endpoints called by GovMap's published JavaScript API:

- `https://www.govmap.gov.il/api/search-service/api-search`
- `https://www.govmap.gov.il/api/layers-catalog/api-search-result-data`

This is acceptable for a small spike or local dry-run, but live calls may be blocked by GovMap domain/origin checks. Do not bulk geocode until API terms, rate limits, and caching/publishing permission are confirmed.

Run a dry run:

```bash
python scripts/run_govmap_geocoding_spike.py --dry-run
```

Run live after setting a token:

```bash
set GOVMAP_API_KEY=...
python scripts/run_govmap_geocoding_spike.py --limit 40
```

If the token only works from the approved browser origin, use the browser spike instead of this Python path.

Output:

- `data/processed/geocoding/govmap_spike_results.csv`

## ArcGIS Fallback Candidate

ArcGIS is now being tested as a separate fallback candidate because GovMap approval may not arrive or may not be usable for our workflow.

Docs:

- `docs/ARCGIS_GEOCODING_SPIKE.md`

Run a dry run:

```bash
python scripts/run_arcgis_geocoding_spike.py --dry-run
```

Run live after setting an ArcGIS access token/API key:

```bash
set ARCGIS_ACCESS_TOKEN=...
python scripts/run_arcgis_geocoding_spike.py --limit 50
```

Output:

- `data/processed/geocoding/arcgis_spike_results.csv`

The ArcGIS script defaults to `forStorage=true` because project coordinates are intended to be cached/reviewed. Use only a token with the right stored-geocoding privilege for retained results.


## Photon Local Candidate

Photon is being tested as a no-token, self-hosted fallback candidate. The local setup uses:

- Geofabrik `israel-and-palestine-latest.osm.pbf`.
- `mediagis/nominatim:5.3` to import the PBF into a local Nominatim/Postgres database.
- Photon `1.2.1` importing from that Nominatim database with `-languages he,en,ar` and `-country-codes il,ps`.

This path is free in API cost and permits local batch execution, but it is based on OpenStreetMap rather than official Israeli address data. Early manual testing showed that a query like `Begin 1 Jerusalem / Menachem Begin 1 Jerusalem` can return high-looking results in the wrong locality, so Photon matches must be reviewed for locality/stat-area plausibility before any promotion to the production cache.

Run a dry run:

```bash
python scripts/run_photon_geocoding_spike.py --dry-run
```

Run live after the local Photon server is listening on `127.0.0.1:2322`:

```bash
python scripts/run_photon_geocoding_spike.py --limit 50
```

Output:

- `data/processed/geocoding/photon_spike_results.csv`

The script applies an Israel/Palestine bounding box and a center-of-Israel bias by default. Those constraints reduce out-of-region drift but do not guarantee a correct locality match. The output therefore exposes Photon locality fields such as `photon_city`, `photon_district`, `photon_street`, and OSM metadata for manual review.

The first 50-row live Photon spike completed locally with 46 matches and 4 no-matches. The conservative locality check found 36 top results where the expected locality was visible and 10 where it was not. Some of those 10 are spelling/orthography review cases, but several are real wrong-locality matches, especially school/place-name queries.

## Cache Contract

The production cache path remains:

- `data/processed/geocoding/geocoded_points.csv`

Required production columns:

- `geocode_key`: use `geocoding_unit_id` from `geocoding_work_units.csv`.
- Either WGS84 `longitude` and `latitude`, or ITM `x_2039` and `y_2039`.
- `geocoder`
- `geocode_status`
- `review_status`

Recommended columns:

- `geocoder_query`
- `geocode_confidence`
- `matched_text`
- `matched_type`
- `matched_score`
- `matched_id`
- `coordinate_crs`
- `geocode_notes`

Review rule:

- `review_status=approved` means the row may be used by the final assignment stage.
- `review_status=needs_review`, `pending`, or `unreviewed` is ignored by final assignment.
- `geocode_status=no_match`, `failed`, `rejected`, `ambiguous`, or equivalent failure values are ignored.

The spike output intentionally uses `review_status=needs_review`, even for successful matches. Reviewed coordinates should be copied or promoted into `geocoded_points.csv` only after inspection.
