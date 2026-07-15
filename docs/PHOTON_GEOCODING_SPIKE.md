# Photon Geocoding Spike

Last updated: 2026-07-15

## Status

Photon is installed locally through a Nominatim-backed import from the Geofabrik Israel/Palestine OpenStreetMap extract. It is now a fallback for units not resolved by the direct OSM exact-address or street-geometry layers.

The local services used during setup are:

- Nominatim HTTP: `http://127.0.0.1:18080`
- Nominatim/Postgres: `127.0.0.1:15432`
- Photon API: `http://127.0.0.1:2322/api`

Nominatim was verified with a Hebrew Jerusalem query. Photon was verified to respond, but the first manual test returned wrong-locality bus-stop matches for `Begin 1 Jerusalem / Menachem Begin 1 Jerusalem`, so quality is not assumed.

## Local Setup Summary

The local Nominatim database was built from:

- `https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf`

Photon was imported from Nominatim using Photon `1.2.1`:

```powershell
java -Xmx6g -jar "$PhotonJar" import `
  -data-dir "$PhotonData" `
  -host 127.0.0.1 `
  -port 15432 `
  -database nominatim `
  -user nominatim `
  -password nominatim_pass_local `
  -languages he,en,ar `
  -country-codes il,ps `
  -j 4
```

Serve Photon locally with:

```powershell
java -Xmx4g -jar "$PhotonJar" serve `
  -data-dir "$PhotonData" `
  -listen-ip 127.0.0.1 `
  -listen-port 2322 `
  -default-language he `
  -max-results 10
```

## Spike Runner

Run a dry run:

```bash
python scripts/run_photon_geocoding_spike.py --dry-run
```

Run live against the local Photon server:

```bash
python scripts/run_photon_geocoding_spike.py --limit 50
```

Output:

- `data/processed/geocoding/photon_spike_results.csv`

For fallback bulk address testing, use unresolved rows from the address-only work units rather than the broad spike sample:

```bash
python scripts/run_photon_geocoding_spike.py --input data/processed/geocoding/geocoding_address_work_units.csv --output data/processed/geocoding/photon_address_work_unit_results.csv
```

`geocoding_address_work_units.csv` is limited to deduplicated street-number-locality queries from rows that actually need address geocoding after the single-stat-locality shortcut.

All rows are marked `review_status=needs_review`. Photon is a candidate source only after manual inspection confirms that returned coordinates match the expected locality/statistical-area context.


## Current Spike Result

The first 50-row live Photon spike completed locally:

- `matched`: 46
- `no_match`: 4
- `expected_locality_seen`: 36
- `expected_locality_not_seen`: 10
- `not_checked`: 4, corresponding to no-match rows

The locality check is conservative and can flag spelling/orthography variants for review, but the spike also exposed real wrong-locality matches for school/place-name queries. Photon remains useful as a free candidate, but only with locality/stat-area validation and manual review before promotion to `geocoded_points.csv`.


## Candidate Polygon Validation

Photon candidate coordinates were checked against the expected dissolved 2022 locality polygon with:

```bash
python scripts/validate_geocode_candidate_localities.py --candidates data/processed/geocoding/photon_work_unit_results.csv
```

Output:

- `data/processed/geocoding/geocode_candidate_locality_validation.csv`
- `data/processed/geocoding/geocode_candidate_locality_validation_summary.json`

Pre-visual-correction 7,196-work-unit validation result:

| Validation status | Units | Meaning |
| --- | ---: | --- |
| `inside_expected_locality` | 5,668 | Candidate coordinate falls inside the expected 2022 dissolved locality polygon. |
| `outside_expected_locality` | 858 | Candidate coordinate falls inside a different 2022 locality polygon and must not be auto-accepted. |
| `outside_all_localities` | 15 | Candidate coordinate does not fall inside any dissolved 2022 locality polygon. |
| `candidate_not_matched` | 634 | Photon did not return usable coordinates. |
| `expected_locality_missing` | 21 | Work unit lacks a target locality code for this validation. |

This is a stronger check than the earlier text-locality heuristic. Text checks remain useful for diagnostics, but the practical acceptance rule is spatial: a candidate coordinate can be promoted only if it lands inside the expected locality polygon, or if a reviewer explicitly approves a known exception.

## Address Scope and Source AGS QA

The 2026-07-15 address-only scope contains:

| Metric | Count |
| --- | ---: |
| Proper street-number-locality query units | 5,663 |
| Proper street-number-locality address rows | 62,506 |
| Proper address units with K23 source AGS metadata | 2,071 |

K23 source AGS is now preserved through the normalized address rows and geocoding work-unit rows. Existing full Photon candidates were checked against the 2022 statistical-area layer with:

```bash
python scripts/validate_geocode_candidate_source_ags.py --candidates data/processed/geocoding/photon_work_unit_results.csv
```

Output:

- `data/processed/geocoding/geocode_candidate_source_ags_validation.csv`
- `data/processed/geocoding/geocode_candidate_source_ags_validation_summary.json`

Overall source-AGS validation result:

| Validation status | Units |
| --- | ---: |
| `single_source_ags_candidate_inside_expected_ags` | 473 |
| `single_source_ags_candidate_outside_expected_ags` | 567 |
| `single_source_ags_not_in_stat_layer` | 496 |
| `multi_source_ags_candidate_inside_one_expected_ags` | 267 |
| `multi_source_ags_candidate_outside_expected_ags` | 259 |
| `multi_source_ags_not_in_stat_layer` | 204 |
| `multi_source_ags_candidate_outside_stat_area` | 1 |
| `candidate_not_matched` | 100 |
| `candidate_outside_stat_area` | 2 |
| `no_source_ags` | 4,827 |

Within the proper-address scope only:

| Validation status | Units |
| --- | ---: |
| `single_source_ags_candidate_inside_expected_ags` | 412 |
| `single_source_ags_candidate_outside_expected_ags` | 497 |
| `single_source_ags_not_in_stat_layer` | 433 |
| `multi_source_ags_candidate_inside_one_expected_ags` | 246 |
| `multi_source_ags_candidate_outside_expected_ags` | 231 |
| `multi_source_ags_not_in_stat_layer` | 183 |
| `multi_source_ags_candidate_outside_stat_area` | 1 |
| `candidate_not_matched` | 77 |
| `candidate_outside_stat_area` | 2 |
| `no_source_ags` | 3,729 |

Important caveat: this is a 2022-layer compatibility check, not final historical AGS QA. The official historical polygon layer is still missing. More importantly, K23 `source_ags` appears to describe the ballot row's source statistical area, not necessarily the polling-place building's location. A single polling-place address can carry multiple source AGS values because several kalpies share one building. That makes all `source_ags` validation statuses diagnostic only, including `single_source_ags_*`; they should not be used as simple geocode pass/fail results.

## Full Work-Unit Run

An earlier local Photon run over the pre-visual-correction set of 7,196 deduplicated geocoding work units produced:

| Query type | Units | Rows | Actual voters | Photon matched + expected locality text seen | Photon matched but expected locality text not seen | Photon no-match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Address with locality | 6,727 | 73,473 | 28,190,018 | 5,612 units / 64,220 rows / 24,775,385 voters | 672 units / 6,439 rows / 2,383,415 voters | 443 units / 2,814 rows / 1,031,218 voters |
| Place with locality | 451 | 4,761 | 1,796,049 | 136 units / 1,696 rows / 642,525 voters | 126 units / 1,477 rows / 561,284 voters | 189 units / 1,588 rows / 592,240 voters |
| Place only | 18 | 60 | 22,246 | 12 units / 35 rows / 13,262 voters | 4 units / 17 rows / 6,138 voters | 2 units / 8 rows / 2,846 voters |

Interpretation:

- True `place_only` is small: 18 unique work units, 60 ballot rows, 22,246 actual voters. This is feasible for manual review.
- All non-address queries (`place_with_locality` + `place_only`) are 469 unique work units, 4,821 ballot rows, 1,818,295 actual voters. That is too large to resolve fully by hand as a first pass.
- Address queries are the strongest Photon use case, but still cannot be accepted blindly. In the full run, Photon returned many plausible address matches, but also real wrong-locality matches.
- The practical Photon use rule should be: accept a Photon coordinate only if it passes a spatial locality validation against the expected 2022 locality polygon or an approved historical locality/crosswalk rule. Text locality checks are useful diagnostics but not sufficient.

