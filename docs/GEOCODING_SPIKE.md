# Geocoding Spike

Last updated: 2026-07-15

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

For the actual bulk address pass, use the scoped proper-address work units:

```bash
python scripts/run_photon_geocoding_spike.py --input data/processed/geocoding/geocoding_address_work_units.csv --output data/processed/geocoding/photon_address_work_unit_results.csv
```

This file excludes place-name queries, address-is-locality queries, suspicious OCR-prefix queries, and rows without a house number. It keeps only deduplicated street-number-locality queries from rows that still need geocoding because their target 2022 locality has multiple statistical areas.

The script applies an Israel/Palestine bounding box and a center-of-Israel bias by default. Those constraints reduce out-of-region drift but do not guarantee a correct locality match. The output therefore exposes Photon locality fields such as `photon_city`, `photon_district`, `photon_street`, and OSM metadata for manual review.

Current scoped proper-address work units:

| Metric | Count |
| --- | ---: |
| Proper street-number-locality query units | 5,663 |
| Proper street-number-locality address rows | 62,506 |
| Proper address units with source AGS metadata | 2,071 |

## OSM Address/Street Assignment Candidates

OSM is the first geographic placement layer. It can assign or narrow addresses before any Photon fallback in two ways:

1. Exact OSM address objects with `addr:housenumber` plus `addr:street` or `addr:place`.
2. Street containment where the street corridor stays inside one 2022 statistical area.

The exact-address rule is:

> if an OSM address object matches normalized `(target_locality_code, street_name, house_number)` and its geometry falls in one 2022 statistical area, assign that address to the containing statistical area

Implemented with:

```bash
python scripts/build_osm_address_stat_lookup.py
```

Outputs:

- `data/processed/geocoding/osm_address_stat_geocoding_units.csv`
- `data/processed/geocoding/osm_address_stat_canonical_addresses.csv`
- `data/processed/geocoding/osm_address_stat_matches.csv`
- `data/processed/geocoding/osm_address_stat_summary.json`
- `data/manual/manual_osm_address_stat_reviews.csv` (reviewed exception input)

Exact-address current result:

| OSM exact-address status | Units |
| --- | ---: |
| `osm_exact_address_single_stat` | 1,086 |
| `osm_exact_address_dominant_stat` | 3 |
| `osm_exact_address_conflicting_stats` | 3 |
| `osm_exact_address_boundary_only` | 3 |
| `osm_exact_address_not_found_in_target_locality` | 4,568 |

For the two street buckets that need house-number help, exact OSM addresses resolve:

| Prior street bucket | Strict exact-address units | Strict + dominant units |
| --- | ---: | ---: |
| `single_stat_centerline_only_buffer_multi_stat` | 258 | 258 |
| `multi_stat_or_boundary_street` | 578 | 581 |
| Combined | 836 | 839 |

The street-containment rule is:

> if the named OSM street corridor for a normalized `(target_locality_code, street_name)` stays inside one 2022 statistical area, then addresses on that street can be assigned to that statistical area without trusting Photon house-number precision

Implemented with:

```bash
python scripts/build_osm_street_stat_lookup.py
```

Inputs:

- `.local/geocoders/osm/israel-and-palestine-latest.osm.pbf`
- `data/processed/geographies/statistical_areas_2022.geojson`
- `data/processed/geographies/localities_2022_dissolved.geojson`
- `data/processed/geocoding/geocoding_address_work_units.csv`

Outputs:

- `data/processed/geocoding/osm_street_stat_lookup.csv`
- `data/processed/geocoding/osm_street_stat_geocoding_units.csv`
- `data/processed/geocoding/osm_street_stat_summary.json`

The current run uses a 25m buffer around matching OSM street lines. Only `single_stat_street_buffer` rows are direct assignment candidates. `single_stat_centerline_only_buffer_multi_stat` rows are review candidates because the centerline is in one stat area but nearby buildings may cross a boundary.

Current result:

| OSM street status | Units |
| --- | ---: |
| `single_stat_street_buffer` | 1,044 |
| `single_stat_centerline_only_buffer_multi_stat` | 1,003 |
| `multi_stat_or_boundary_street` | 2,180 |
| `osm_street_not_found_in_target_locality` | 1,436 |

The conservative street-only set covers 11,457 source rows and 4,499,783 actual voters.

Query units retain exact source-row lineage and therefore still include punctuation and formatting variants. Canonical physical-address deduplication reduces 5,663 testable query units to 4,210 locality-street-number addresses, including two supplemental reviewed target-locality queries.

Combined OSM candidate coverage:

| Candidate set | Units | Source rows | Actual voters |
| --- | ---: | ---: | ---: |
| Street corridor only | 1,044 | 11,457 | 4,499,783 |
| Street corridor or strict exact address | 1,922 | 24,211 | 9,463,605 |

At canonical-address grain, the OSM-first layer resolves 1,355 addresses: 762 by a single-area street corridor, 584 additional addresses by house number, seven reviewed OSM exceptions, and two reviewed component-locality cases. The remaining 2,855 canonical numbered addresses have no accepted placement yet. See `docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md` for the exact residual breakdown and the distinction between query units and physical addresses.

Caveats: exact OSM address objects are stronger than street-only placement, but they still need provenance in the assignment method. The reader does not yet infer streets for house-number-only features, expand address interpolation, or resolve `associatedStreet` relations. A street can be a statistical-area boundary, OSM names can differ from election spelling, and some localities have weak or unnamed street coverage. Boundary-touching or split streets remain in review unless an exact OSM address resolves them.



The earlier full local Photon run used the pre-visual-correction set of 7,196 deduplicated queries. It found that true `place_only` queries are small enough for manual review: 18 units, 60 ballot rows, and 22,246 actual voters. Broader non-address queries (`place_with_locality` + `place_only`) are larger: 469 units, 4,821 rows, and 1,818,295 actual voters. Address queries are Photon's strongest use case, but acceptance requires point-in-expected-locality validation rather than trusting the first text result. The validation script is `scripts/validate_geocode_candidate_localities.py`, and final assignment rejects reviewed coordinates that fall outside the expected locality with `geocoded_point_outside_expected_locality`.

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

Coordinate sanity rule:

Historical/source AGS QA note:

- Where an election-specific source row has an official AGS/statistical-area code, candidate coordinates can be tested against the matching historical AGS polygon layer as diagnostic context.
- Current local inspection found explicit AGS only in the K23 polling-place report. Other elections need additional source research before this QA can be applied.
- K23 `source_ags` is now preserved in `polling_place_addresses.csv`, `geocoding_input.csv`, and `geocoding_work_unit_rows.csv`.
- `scripts/validate_geocode_candidate_source_ags.py` currently validates source AGS against the available 2022 statistical-area layer. This is diagnostic only and should not be used as a hard pass/fail rule.
- See `docs/AGS_HISTORICAL_QA.md`.

- A reviewed geocode is usable only after the coordinate lands inside the expected dissolved 2022 locality polygon, or a reviewer records an explicit exception.
- The final assignment stage already checks whether a point falls inside a statistical area; it now also rejects points that fall in the wrong locality before assigning a statistical area.

- `review_status=approved` means the row may be used by the final assignment stage.
- `review_status=needs_review`, `pending`, or `unreviewed` is ignored by final assignment.
- `geocode_status=no_match`, `failed`, `rejected`, `ambiguous`, or equivalent failure values are ignored.

The spike output intentionally uses `review_status=needs_review`, even for successful matches. Reviewed coordinates should be copied or promoted into `geocoded_points.csv` only after inspection.

