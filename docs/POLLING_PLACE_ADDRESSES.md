# Polling-Place Address Coverage

Last updated: 2026-07-15

## Purpose

The statistical-area map needs an approximate kalpi-to-statistical-area assignment. Official ballot-result rows include votes and kalpi identifiers, but no kalpi polygons or coordinates.

The statistical-area approach is:

> poll result row -> polling-place address/place source -> geocoded point -> 2022 statistical area

There is also a shortcut:

> if the reviewed 2022 locality has exactly one statistical area, assign by locality and skip geocoding

This is intentionally approximate. It maps the polling-place building, not each voter's residential statistical area.

Locality totals use the same normalized ballot rows but join directly through the reviewed locality crosswalk; they do not wait for address geocoding. Official locality aggregate files are useful as QA/reference material, but they are not product input totals.

Current product scope is K17-K25. K16 / 2003 is deferred until a usable election-specific polling-place address source is recovered.

## Sources Found

| Election | Address source | Current status |
|---|---|---|
| K25 / 2022 | Official K25 polling-place XLSX in `data/raw` | Election-specific; high confidence |
| K24 / 2021 | `data/raw/archive_knesset24_kalpies_report_tofes_b_18_3_21.xlsx` | Election-specific archived official XLSX; high confidence |
| K23 / 2020 | `data/raw/archive_knesset23_kalpies_report_19_1_20_1.xlsx` | Election-specific archived official XLSX; high confidence; includes AGS metadata |
| K22 / 2019 Sep | `data/raw/archive_knesset22_kalpies_report_tofes_b_6th_edition_15_9.xlsx` | Election-specific archived official XLSX; high confidence |
| K21 / 2019 Apr | Archived official K21 polling-place XLS | Election-specific; high confidence |
| K20 / 2015 | `data/raw/archive_knesset20_tell_the_polls_9_3.xls` | Election-specific archived official XLS; high confidence |
| K19 / 2013 | `data/raw/archive_knesset19_all_stations.pdf` | Election-specific archived official Excel-generated PDF; high confidence after parser cleanup |
| K18 / 2009 | `data/raw/archive_knesset18_kalpilist18.pdf` | Election-specific scanned PDF with embedded OCR text; reconciliation complete for ordinary rows |
| K17 / 2006 | Address field inside official ballot-result file plus `data/raw/archive_knesset17_kalpies-list17-*.pdf` | Election-specific; direct scan transcription recovered 456 polling-place names, including all 344 rows formerly described as locality-only/no-place |

Official election results package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Generic official polling-place datastore resource, kept as research-only fallback metadata:

https://data.gov.il/api/3/action/datastore_search?resource_id=68c4d7e8-2218-48ee-996f-2db2f72b2395

The generic table is not election-specific. It should not be used as production direct-address coverage for elections where an election-specific source is unavailable.

## Recovered 2026-07-07 Sources

### K20 / 2015

Primary source:

https://web.archive.org/web/20160330183320id_/http://bechirot.gov.il/election/Kneset20/Documents/TellThePolls.9.3.xls

Local raw file:

- `data/raw/archive_knesset20_tell_the_polls_9_3.xls`

Observed fields include committee code/name, election locality code/name, kalpi code, polling-place address, polling-place name, accessibility flags, eligible voters, split metadata, and joined-to metadata.

Reconciliation:

- Official K20 ballot-result rows: 10,414.
- Source polling-place rows: 10,464.
- Direct exact locality-code + kalpi matches: 10,003.
- Split rows resolved by locality + base kalpi + eligible voters: 116.
- Total matched rows: 10,119.
- Unmatched rows: 295, all special-envelope rows.
- Ordinary geographic rows without address: 0.

### K19 / 2013

Primary source:

https://web.archive.org/web/20130123205035id_/http://www.bechirot.gov.il:80/elections19/heb/about/AllStations.pdf

Local raw file:

- `data/raw/archive_knesset19_all_stations.pdf`

The PDF title is `מקומות הקלפי - רשימה סופית נכון ל- 13.12.12`. It was generated from Excel and contains extractable table text, not just scanned images. RTL extraction corrupts some long names, so parsing should trust locality code and extract the numeric kalpi prefix from the kalpi column.

Reconciliation:

- Official K19 ballot-result rows: 10,109.
- Parsed unique polling-place rows: 10,239.
- Matched result rows: 9,881.
- Unmatched rows: 228, all special-envelope rows.
- Ordinary geographic rows without address: 0.
- Match by locality code + kalpi number. Do not require eligible-voter equality; 226 matched rows have eligibility-count mismatches between the source PDF and the final result rows.

### K24 / 2021

Primary source:

https://web.archive.org/web/20211106033352id_/https://bechirot24.bechirot.gov.il/election/Kneset24/Documents/%D7%9B%D7%A0%D7%A1%D7%AA%2024/kalpies_report_tofes_b_18.3.21.xlsx

Local raw file:

- `data/raw/archive_knesset24_kalpies_report_tofes_b_18_3_21.xlsx`

Reconciliation:

- Source polling-place rows: 12,127.
- Rows with address: 12,127.
- Geocode-needed rows linked to ready address strings: 10,193.

### K23 / 2020

Primary source:

https://web.archive.org/web/20210119095351id_/https://bechirot23.bechirot.gov.il/election/Kneset20/Documents/%D7%9B%D7%A0%D7%A1%D7%AA%2023/kalpies_report_19_1_20_1.xlsx

Local raw file:

- `data/raw/archive_knesset23_kalpies_report_19_1_20_1.xlsx`

Reconciliation:

- Source polling-place rows: 10,631.
- Rows with address: 10,631.
- Rows with AGS source metadata: 8,031.
- Geocode-needed rows linked to ready address strings: 8,964.
- Normalized address rows now preserve `source_ags` and `source_concentration_code` for downstream geocoding QA.

### K22 / 2019 Sep

Primary source:

https://web.archive.org/web/20191113005230id_/https://bechirot22.bechirot.gov.il/election/Kneset20/Documents/%D7%9B%D7%A0%D7%A1%D7%AA%2022/kalpies_report_tofes_b_6th_edition_15_9.xlsx

Local raw file:

- `data/raw/archive_knesset22_kalpies_report_tofes_b_6th_edition_15_9.xlsx`

Reconciliation:

- Source polling-place rows: 10,543.
- Rows with address: 10,543.
- Geocode-needed rows linked to ready address strings: 8,878.

### K21 / 2019 Apr

Primary source:

https://web.archive.org/web/20221202061209id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies_full_report.xls

Local raw files:

- `data/raw/archive_knesset21_kalpies_full_report.xls`
- `data/raw/archive_knesset21_ballots_table.csv`
- `data/raw/archive_knesset21_special_kalpies.xls`
- `data/raw/archive_knesset21_kalpies_committee_summary.xls`

Reconciliation:

- The direct address source has 10,459 unique locality-code + kalpi rows.
- The official K21 ballot-result datastore has 10,765 rows.
- Direct address matching covers 10,459 rows.
- The 306 unmatched result rows are 305 special-envelope rows plus Nurit [833], kalpi 1, with 98 eligible voters and 82 actual voters.
- Nurit is a reviewed single-stat locality, so it is still assignable without geocoding.

## Deferred K16 Research

K16 / 2003 is outside current product scope. No usable full polling-place address source has been found yet. If K16 is reintroduced later, it should not rely on generic-table matches as production coverage.

## Normalized Address Source Availability

This table reflects the address sources currently present under `data/raw` and `data/manual` and parsed by `scripts/normalize_polling_places.py`.

| Election | Source rows | Rows with street address | Place-only rows | Missing election-specific source |
|---|---:|---:|---:|---|
| K25 | 11,547 | 11,540 | 2 | No |
| K24 | 12,127 | 12,127 | 0 | No |
| K23 | 10,631 | 10,631 | 0 | No |
| K22 | 10,543 | 10,543 | 0 | No |
| K21 | 10,459 | 10,459 | 0 | No |
| K20 | 10,464 | 10,464 | 0 | No |
| K19 | 10,239 | 10,233 | 6 | No |
| K18 | 9,263 | 9,248 | 15 | No |
| K17 | 8,718 | 8,262 | 456 | No |

K22-K24 address reports were recovered in an earlier research pass, then were stranded in the old Codex scratch folder during project-folder reorganization. They are now copied into `data/raw` and parsed by the pipeline.

Reviewed K18 scan corrections and source confirmations are stored separately in `data/manual/manual_k18_address_reviews.csv` and applied by normalization. The generated OCR-reconciliation CSV is not edited by hand. The overlay now contains 126 rows: 121 corrections and 5 confirmations of weak text visible in the scan; its final 113-row batch covers the 82 suspicious signatures reviewed by the user.

## Geocoding Input Readiness

This table covers only rows that need address-level point-in-polygon assignment after applying the reviewed locality crosswalk, custom buckets, and single-stat locality shortcut.

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

## Address-Only Geocoding Scope

The broad geocoding work-unit table keeps all rows that need geographic placement, including place-name and review cases. For the OSM-first exact-address/street pass and any later geocoder fallback, the scoped file is:

- `data/processed/geocoding/geocoding_address_work_units.csv`

It keeps only deduplicated street-number-locality queries from rows in multi-stat 2022 localities. Current counts:

| Metric | Count |
|---|---:|
| Unique geocoding units | 7,190 |
| Proper street-number-locality address units | 5,663 |
| Proper street-number-locality address rows | 62,506 |
| Excluded units needing manual or non-address handling | 1,527 |
| Proper address units with K23 source AGS | 2,071 |

The 1,527 excluded units are not discarded. They remain in the broad geocoding work-unit table and manual/review queues; they are only excluded from the clean OSM exact-address input and later street-address geocoder fallbacks.

| Exclusion scope | Units | Rows | Meaning |
|---|---:|---:|---|
| `excluded_missing_house_number` | 836 | 10,317 | Address text has no house number, so a street/locality result cannot identify a building. |
| `excluded_not_street_address_query` | 590 | 5,285 | Query is place-name-based, such as school/place plus locality, not street-number-locality. |
| `excluded_suspicious_ocr_or_prefix` | 99 | 135 | Address has an OCR-like prefix, Latin/replacement character, digit substitution, or implausibly short parsed street. |
| `excluded_missing_target_locality_code` | 2 | 4 | Missing target locality code, so spatial locality validation cannot be automated. |

The broader source-fidelity and usability audit is documented in `docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md`. It checks all 93,991 normalized source rows against available source evidence, finds zero missing evidence links and zero normalized-field mismatches, and identifies 1,525 address-content review units. Of those, 615 PDF/OCR units are independently corroborated by a matching digital-election query, and 450 still require a visual decision.

Interpretation:

- K22-K25 and K20-K21 have ready address strings for all rows that need geocoding.
- K19 and K18 have a small number of place-only rows that need manual/reviewed geocoding.
- K17 has 456 place-only rows recovered directly from the scanned polling-place lists.

## K17 Scan Recovery

All 344 K17 rows previously described as locality-only with no place have now been transcribed directly from the far-left `מקום הקלפי` scan column. The current unresolved locality-only/no-place count is zero. The exact polls are in `docs/K17_LOCALITY_ONLY_SCAN_RECOVERY.csv`.

The Maghar scan lists stations 1-20, while the digital K17 result table contains only 1-16. Stations 17-20 are absent result records rather than blank-address rows.

### Superseded Partial Snapshot

The table below records the earlier 11-row partial recovery and is retained only as investigation history; it is not the current scope.

At that stage K17 had 15 non-envelope rows with an empty address field.

Rows assignable without geocoding:

| Locality | Kalpi | Rule |
|---|---:|---|
| ניצן | 20 | Single-stat locality |
| אום בטין | 10 | Single-stat locality |
| בית אריה | 10 | Reviewed alias for בית אריה-עופרים, single-stat |
| בית אריה | 30 | Reviewed alias for בית אריה-עופרים, single-stat |

Rows recovered from the K17 scanned lists but still needing geocoding/review:

| Locality | Result kalpi | PDF source | Scanned address column | Polling-place name |
|---|---:|---|---|---|
| ערערה-בנגב | 50 | part 2 page 133 | `0` | ביה"ס אבן סינא |
| ערערה-בנגב | 9900 | part 2 page 133 | `0` | ביה"ס אבן סינא |
| טייבה | 110 | part 1 page 123 | `0` | ביה"ס אבן-סינא ב' |
| טייבה | 150 | part 1 page 123 | `0` | ביה"ס אבן-סינא ב' |
| טייבה | 250 | part 1 page 123 | `0` | ביה"ס חט"ב אל-סלאם |
| טייבה | 260 | part 1 page 123 | `0` | ביה"ס חט"ב אל-סלאם |
| טייבה | 270 | part 1 page 123 | `0` | ביה"ס חט"ב אל-סלאם |
| טייבה | 280 | part 1 page 123 | `0` | ביה"ס אבן-סינא ב' |
| טייבה | 290 | part 1 page 123 | `0` | ביה"ס אבן-סינא ב' |
| טייבה | 300 | part 1 page 123 | `0` | ביה"ס אל-חכמה |
| טייבה | 310 | part 1 page 123 | `0` | ביה"ס אל-חכמה |

## Geocoding Scope

Geocoding is only needed where:

- the row is not an official envelope or reviewed non-geographic row,
- the row can be linked to a polling-place address or place name,
- the reviewed 2022 locality has multiple statistical areas or the row is an address-target-set case.

Rows already assignable by the single-stat locality shortcut should not be geocoded unless a QA/debug view needs the point.

`data/manual/polling_place_assignment_overrides.csv` stores reviewed row-level exceptions. Dimona kalpi 91 at `מחנה עדי` in K22-K25 is classified there as envelope votes and is excluded before geocoding.

Row-level assignment should store one method:

- `single_stat_locality`
- `direct_address_geocode_needed`
- `address_geocode_to_current_polygons`
- `custom_point_size_polygon`
- `special_non_geographic`
- `official_envelope`
- `unresolved`

## Geocoding Provider Research

Provider status is documented in `docs/GEOCODING_SPIKE.md`, `docs/GOVMAP_BROWSER_SPIKE.md`, `docs/ARCGIS_GEOCODING_SPIKE.md`, and `docs/PHOTON_GEOCODING_SPIKE.md`.

Current position:

- GovMap remains the preferred official Israeli candidate, but approval/token behavior, rate limits, coordinate fields, and caching/publication terms still need live verification.
- ArcGIS is a fallback only if an access token/API key with stored-geocoding rights is available.
- Direct OSM exact-address and street geometry are the first placement layers after address-quality validation.
- Photon is a later free local fallback. A full local run exists, but it already showed wrong-locality matches, so Photon output is candidate data only until it passes locality-polygon validation and manual review. Source/historical AGS checks are supplemental diagnostics only; multiple source AGS values at one address prove the field is not a building-location truth, and single-source-AGS rows cannot be treated as hard passes either.
- Google geocoding should not be the primary source for public downloadable coordinates unless its storage and redistribution constraints are explicitly cleared.
- Public Nominatim should not be used for bulk geocoding. The only open-data path currently considered is self-hosted Nominatim/Photon.

## Locality History

Localities can change between elections: names change, codes change, localities split, localities merge, and some localities disappear or are represented differently in later CBS layers.

The pipeline needs an explicit locality crosswalk with provenance.

Rules:

- Exact current locality-code matches can be automated.
- Historical aliases, spelling changes, merges, and splits must be reviewed and recorded.
- In statistical-area mode, reviewed split localities and Sha'ar Shomron are address-target sets: use each ballot row's address/geocoded point to assign it to the correct component polygon.
- In locality mode, באקה-ג'ת, עיר כרמל, שגור, and שער שומרון use reviewed election-specific unions of their component locality polygons. This preserves the election-time municipality without heuristically splitting votes.
- Reviewed custom buckets (`TRIBE`, `GAZA`, `N.S.`, `HEBRON`) are assigned to synthetic point-size polygon geographies and preserve source-row contributions.
- A merge can use the single-stat shortcut only if the merged 2022 target has exactly one statistical area, or if a reviewed rule assigns the old locality unambiguously.

## Current Blockers

- Deciding which of the 450 PDF/OCR-only address-content units that lack digital-election or reviewed-image corroboration warrant the next visual-review batch.
- Geocoding/reviewing the K17, K18, and K19 place-name-only rows.
- Building and reviewing the geocoding cache for addressed K17-K25 multi-stat localities.
- Designing custom point-size polygon buckets in the frontend.
