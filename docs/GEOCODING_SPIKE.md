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

The current spike script uses the same public service endpoints called by GovMap's published JavaScript API:

- `https://www.govmap.gov.il/api/search-service/api-search`
- `https://www.govmap.gov.il/api/layers-catalog/api-search-result-data`

This is acceptable for a small spike, but do not bulk geocode until API terms, rate limits, and caching/publishing permission are confirmed.

Run a dry run:

```bash
python scripts/run_govmap_geocoding_spike.py --dry-run
```

Run live after setting a token:

```bash
set GOVMAP_API_KEY=...
python scripts/run_govmap_geocoding_spike.py --limit 40
```

Output:

- `data/processed/geocoding/govmap_spike_results.csv`

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
