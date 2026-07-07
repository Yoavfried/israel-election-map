# Polling-Place Address Coverage

Last updated: 2026-07-07

## Purpose

The statistical-area map needs an approximate kalpi-to-statistical-area assignment. Official ballot-result rows include votes and kalpi identifiers, but no kalpi polygons or coordinates.

The project approach is:

> poll result row -> polling-place address/place source -> geocoded point -> 2022 statistical area -> dissolved 2022 locality

There is also a shortcut:

> if the reviewed 2022 locality has exactly one statistical area, assign by locality and skip geocoding

This is intentionally approximate. It maps the polling-place building, not each voter's residential statistical area.

Both statistical-area and locality product totals should be generated from this row-level assignment pipeline. Official locality aggregate files are useful as QA/reference material, but they are not product input totals.

Current product scope is K17-K25. K16 / 2003 is deferred until a usable election-specific polling-place address source is recovered.

## Sources Found

| Election | Address source | Current status |
|---|---|---|
| K25 / 2022 | Official K25 polling-place XLSX in `data/raw` | Election-specific; high confidence |
| K24 / 2021 | Archived official K24 polling-place XLSX | Election-specific; high confidence |
| K23 / 2020 | Archived official K23 polling-place XLSX | Election-specific; high confidence |
| K22 / 2019 Sep | Archived official K22 polling-place XLSX | Election-specific; high confidence |
| K21 / 2019 Apr | Archived official K21 polling-place XLS | Election-specific; high confidence |
| K20 / 2015 | `data/raw/archive_knesset20_tell_the_polls_9_3.xls` | Election-specific archived official XLS; high confidence |
| K19 / 2013 | `data/raw/archive_knesset19_all_stations.pdf` | Election-specific archived official Excel-generated PDF; high confidence after parser cleanup |
| K18 / 2009 | `data/raw/archive_knesset18_kalpilist18.pdf` | Election-specific scanned PDF with embedded OCR text; reconciliation complete for ordinary rows |
| K17 / 2006 | Address field inside official ballot-result file plus `data/raw/archive_knesset17_kalpies-list17-*.pdf` | Election-specific; high confidence for addressed rows; targeted scan extraction recovered names for 11 remaining multi-stat rows |

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

## Direct Address Coverage

Coverage is measured against official ballot-result rows. Rows without direct address include special-envelope rows unless noted separately.

| Election | Year | Address source | Poll rows | Rows with direct address | Rows without direct address | Poll coverage | Eligible voters without direct address | Actual voters without direct address |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| K25 | 2022 | Official K25 polling-place XLSX | 12,545 | 11,707 | 838 | 93.32% | 0 (0.00%) | 462,807 (9.65%) |
| K24 | 2021 | Archived official polling-place XLSX | 12,926 | 12,127 | 799 | 93.82% | 0 (0.00%) | 425,512 (9.59%) |
| K23 | 2020 | Archived official polling-place XLSX | 11,179 | 10,631 | 548 | 95.10% | 0 (0.00%) | 330,209 (7.15%) |
| K22 | 2019 Sep | Archived official polling-place XLSX | 10,901 | 10,539 | 362 | 96.68% | 0 (0.00%) | 282,442 (6.33%) |
| K21 | 2019 Apr | Archived official polling-place XLS | 10,765 | 10,459 | 306 | 97.16% | 98 (0.00%) | 240,865 (5.55%) |
| K20 | 2015 | Archived official K20 TellThePolls XLS | 10,414 | 10,119 | 295 | 97.17% | 0 (0.00%) | 234,599 (5.51%) |
| K19 | 2013 | Archived official K19 AllStations PDF | 10,109 | 9,881 | 228 | 97.74% | 0 (0.00%) | 215,789 (5.63%) |
| K18 | 2009 | Official scanned polling-place PDF extraction | 9,264 | 9,263 | 1 | 99.99% | 186,919 (3.42%) | 186,919 (5.47%) |
| K17 | 2006 | Address field in official result file | 8,426 | 8,262 | 164 | 98.05% | Not available | 179,177 (5.62%) |

Interpretation:

- K19-K25 and K18: every ordinary geographic row now has a direct election-specific address source, except K21 Nurit, which is assignable by the single-stat shortcut.
- K17: every ordinary row has an address except 15 rows. Four are assignable by the single-stat shortcut. Eleven have recovered polling-place names from scans but still need geocoding/review.
- For K17-K25, the only remaining missing-address blocker needed for statistical-area assignment is the 11 K17 place-name-only rows listed below.

## Remaining Address Gap After Reviewed Assignment

This table excludes official envelope rows. `Still missing address` means the row is non-envelope, is not covered by single-stat locality assignment, is not covered by a custom point bucket, and lacks a direct address needed for multi-stat or reviewed address-target-set geocoding.

| Election | Year | Non-envelope rows without direct address | Assigned by single-stat | Assigned by custom point | Special non-geographic | Still missing address rows | Still missing eligible voters | Still missing actual voters | Actual voters lost from map |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| K25 | 2022 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K24 | 2021 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K23 | 2020 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K22 | 2019 Sep | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K21 | 2019 Apr | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K20 | 2015 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K19 | 2013 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K18 | 2009 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K17 | 2006 | 15 | 4 | 0 | 0 | 11 | Not available | 3,603 | 0.11% |

## K17 Remaining Rows

K17 has 15 non-envelope rows with an empty address field.

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

Row-level assignment should store one method:

- `single_stat_locality`
- `direct_address_geocode_needed`
- `address_geocode_to_current_polygons`
- `custom_point_size_polygon`
- `special_non_geographic`
- `official_envelope`
- `unresolved`

## Geocoding Provider Research

GovMap is the preferred first geocoding candidate because it is Israeli, supports Hebrew address search, and its documented search API can return point geometry/centroid data. Before bulk geocoding, run a small representative spike and confirm:

- API key flow and rate limits.
- Whether cached/reviewed coordinates may be stored and published in the project's public data outputs.
- Which coordinate system is returned in each geometry field, and the correct conversion to WGS84 longitude/latitude.
- Accuracy on older polling-place addresses, school/place names, and reviewed address-target-set cases.
- Fallback policy for ambiguous or failed results.

Google geocoding should not be the primary source for public downloadable coordinates unless its storage and redistribution constraints are explicitly cleared. Public Nominatim should not be used for bulk geocoding; a self-hosted/open-data fallback can be reconsidered if needed.

## Locality History

Localities can change between elections: names change, codes change, localities split, localities merge, and some localities disappear or are represented differently in later CBS layers.

The pipeline needs an explicit locality crosswalk with provenance.

Rules:

- Exact current locality-code matches can be automated.
- Historical aliases, spelling changes, merges, and splits must be reviewed and recorded.
- Reviewed split localities and Sha'ar Shomron are address-target sets: use each ballot row's address/geocoded point to assign it to the correct current polygon. Do not join current polygons, and do not split votes heuristically.
- Reviewed custom buckets (`TRIBE`, `GAZA`, `N.S.`, `HEBRON`) are assigned to synthetic point-size polygon geographies and preserve source-row contributions.
- A merge can use the single-stat shortcut only if the merged 2022 target has exactly one statistical area, or if a reviewed rule assigns the old locality unambiguously.

## Current Blockers

- Geocoding/reviewing the 11 K17 place-name-only rows.
- Building and reviewing the geocoding cache for addressed K17-K25 multi-stat localities.
- Designing custom point-size polygon buckets in the frontend.
