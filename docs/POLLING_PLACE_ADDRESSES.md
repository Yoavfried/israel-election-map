# Polling-Place Address Coverage

Last updated: 2026-07-07

## Purpose

The statistical-area map needs an approximate kalpi-to-statistical-area assignment. Official ballot-result rows include votes and kalpi identifiers, but no kalpi polygons or coordinates.

The project approach is:

> poll result row -> polling-place address -> geocoded point -> 2022 statistical area

There is also a shortcut:

> if the matched 2022 locality has exactly one statistical area, assign by locality and skip geocoding

This is intentionally approximate. It maps the polling-place building, not each voter's residential statistical area.

## Sources Found

| Election | Address source | Current status |
|---|---|---|
| K25 / 2022 | Official K25 polling-place XLSX in `data/raw` | Election-specific; high confidence |
| K24 / 2021 | Archived official K24 polling-place XLSX | Election-specific; high confidence |
| K23 / 2020 | Archived official K23 polling-place XLSX | Election-specific; high confidence |
| K22 / 2019 Sep | Archived official K22 polling-place XLSX | Election-specific; high confidence |
| K21 / 2019 Apr | Archived official K21 polling-place XLS | Election-specific; high confidence |
| K20 / 2015 | Generic official `voting-polls` table | Fallback only; not election-specific |
| K19 / 2013 | Generic official `voting-polls` table | Fallback only; not election-specific |
| K18 / 2009 | `data/raw/archive_knesset18_kalpilist18.pdf` | Election-specific scanned list with embedded OCR text layer; row-level reconciliation is complete for ordinary rows |
| K17 / 2006 | Address field inside official ballot-result file plus `data/raw/archive_knesset17_kalpies-list17-*.pdf` | Election-specific; high confidence for addressed rows, targeted scan extraction recovered place names for the 11 remaining multi-stat rows |
| K16 / 2003 | Generic official `voting-polls` table | Fallback only; not election-specific |

Official election results package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Generic official polling-place datastore resource:

https://data.gov.il/api/3/action/datastore_search?resource_id=68c4d7e8-2218-48ee-996f-2db2f72b2395

K21 update, 2026-07-07:

- Recovered election-specific archived official K21 polling-place files from `bechirot21.bechirot.gov.il`.
- Saved raw files:
  - `data/raw/archive_knesset21_kalpies_full_report.xls`
  - `data/raw/archive_knesset21_ballots_table.csv`
  - `data/raw/archive_knesset21_special_kalpies.xls`
  - `data/raw/archive_knesset21_kalpies_committee_summary.xls`
- `archive_knesset21_kalpies_full_report.xls` is the direct address source. It includes locality code/name, kalpi number, polling-place address, polling-place name, accessibility flags, and eligible voters.
- Exact locality-code + kalpi matching against the official K21 ballot-result datastore covers 10,459 / 10,765 result rows.
- The unmatched rows are 305 official envelope rows plus one ordinary row: `נורית` [833], kalpi 1, with 98 eligible voters and 82 actual voters. `נורית` is a reviewed single-stat locality, so it is still assignable without geocoding.

Archived source captures:

- `https://web.archive.org/web/20221202061209id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies_full_report.xls`
- `https://web.archive.org/web/20221201110430id_/https://bechirot21.bechirot.gov.il/election/Documents/%D7%98%D7%91%D7%9C%D7%AA%20%D7%A7%D7%9C%D7%A4%D7%99%D7%95%D7%AA.csv`
- `https://web.archive.org/web/20221205071624id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/special_kalpies21.xls`
- `https://web.archive.org/web/20221202061132id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies21_b.xls`

## Direct Address Matching

Coverage is measured against official ballot-result rows.

Match key:

- locality code
- normalized kalpi number

Normalization:

- Split result rows such as `3.1` can match base kalpi `3`.
- For the generic polling-place table, aliases such as `10 -> 1` are accepted because the generic source uses a different kalpi-number convention.

This measures whether a ballot-result row can be associated with an address-like polling-place record. It does not prove historical exactness when the generic table is used.

K18 update, 2026-07-06:

- The newly added `archive_knesset18_kalpilist18.pdf` is an election-specific polling-place list.
- It is scanned, but it has an embedded OCR text layer with usable word coordinates.
- The current extractor writes a raw OCR table CSV and a resolved official-row CSV.
- Row-level reconciliation matches 9,263 / 9,263 ordinary official K18 result rows.
- The only official K18 result row without a physical polling-place address is the special non-geographic `מעטפות כפולות` row, with 186,919 actual voters.

## Direct Address Coverage

| Election | Year | Address source | Poll rows | Rows with direct address | Rows without direct address | Poll coverage | Eligible voters without direct address | Actual voters without direct address |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| K25 | 2022 | Official K25 polling-place XLSX | 12,545 | 11,707 | 838 | 93.32% | 0 (0.00%) | 462,807 (9.65%) |
| K24 | 2021 | Archived official polling-place XLSX | 12,926 | 12,127 | 799 | 93.82% | 0 (0.00%) | 425,512 (9.59%) |
| K23 | 2020 | Archived official polling-place XLSX | 11,179 | 10,631 | 548 | 95.10% | 0 (0.00%) | 330,209 (7.15%) |
| K22 | 2019 Sep | Archived official polling-place XLSX | 10,901 | 10,539 | 362 | 96.68% | 0 (0.00%) | 282,442 (6.33%) |
| K21 | 2019 Apr | Archived official polling-place XLS | 10,765 | 10,459 | 306 | 97.16% | 98 (0.00%) | 240,865 (5.55%) |
| K20 | 2015 | Generic official polling-place table | 10,414 | 9,804 | 610 | 94.14% | 176,373 (3.00%) | 362,617 (8.52%) |
| K19 | 2013 | Generic official polling-place table | 10,109 | 9,747 | 362 | 96.42% | 68,407 (1.21%) | 260,957 (6.81%) |
| K18 | 2009 | Official scanned polling-place PDF extraction | 9,264 | 9,263 | 1 | 99.99% | 186,919 (3.42%) | 186,919 (5.47%) |
| K17 | 2006 | Address field in official result file | 8,426 | 8,262 | 164 | 98.05% | Not available | 179,177 (5.62%) |
| K16 | 2003 | Generic official polling-place table | 7,886 | 7,674 | 212 | 97.31% | 191,007 (3.92%) | 182,385 (5.70%) |

Interpretation:

- K22-K25: every ordinary row has a direct address match; rows without direct addresses are not ordinary polling-place rows.
- K17: every ordinary row has an address except 15 rows listed below.
- K18: every ordinary row has a direct address match from the election-specific scanned PDF; the only row without an address is non-geographic.
- K16 and K19-K20: matches use the generic polling-place table, so they are provisional. Kalpi numbers and polling-place locations may have changed.
- K21: every ordinary row has a direct address match except `נורית` [833], kalpi 1, which is assignable by the single-stat locality shortcut.

## Ordinary Rows Without Direct Address

The table below excludes non-ordinary rows and shows only ordinary locality/kalpi rows that did not get a direct address match.

| Election | Ordinary rows without direct address | Ordinary eligible voters | Ordinary actual voters |
|---|---:|---:|---:|
| K25 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 |
| K21 | 1 | 98 | 82 |
| K20 | 317 | 176,373 | 129,708 |
| K19 | 136 | 68,407 | 47,160 |
| K18 | 0 | 0 | 0 |
| K17 | 15 | Not available | 4,693 |
| K16 | 63 | 32,711 | 24,089 |

## Single-Stat Locality Shortcut

The FileGDB-derived 2022 statistical-area layer has:

| Layer measure | Count |
|---|---:|
| Locality codes in the layer | 1,283 |
| Locality codes with exactly one `STAT_2022` | 1,139 |
| Locality codes with multiple `STAT_2022` values | 144 |

If a row belongs to a reviewed 2022 locality with exactly one statistical area, it can be assigned to statistical-area mode without geocoding.

This shortcut should be applied before geocoding. If a row's locality has exactly one 2022 statistical area, geocoding its polling-place address cannot change the statistical-area assignment.

Full reviewed assignment outputs:

- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.csv`
- `docs/ADDRESSLESS_ROWS_AFTER_REVIEWED_ASSIGNMENT.csv`

After applying the reviewed locality resolution plan, the remaining non-envelope address gap is:

| Election | Non-envelope rows without direct address | Assigned by single-stat | Assigned by custom point | Still missing address rows | Still missing eligible voters | Still missing actual voters |
|---|---:|---:|---:|---:|---:|---:|
| K25 | 0 | 0 | 0 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 | 0 | 0 | 0 |
| K21 | 1 | 1 | 0 | 0 | 0 | 0 |
| K20 | 317 | 39 | 5 | 273 | 157,603 | 116,744 |
| K19 | 136 | 16 | 1 | 119 | 60,951 | 42,261 |
| K18 | 0 | 0 | 0 | 0 | 0 | 0 |
| K17 | 15 | 4 | 0 | 11 | Not available | 3,603 |
| K16 | 63 | 3 | 4 | 56 | 30,028 | 21,938 |

## K17 Non-Envelope Rows Without Address

K17 has 15 non-envelope rows with an empty address field. After the reviewed locality resolution:

- 4 rows are assignable without geocoding: `ניצן`, `אום בטין`, and two `בית אריה` rows.
- The 11 remaining rows are in multi-stat localities, so locality-only assignment is not enough.
- The newly added K17 scanned polling-place lists locate those 11 rows and provide polling-place names. Their scanned address column is still `0`, so these should be geocoded as `polling-place name + locality` and manually reviewed.

Single-stat rows:

| Locality | Kalpi | 2022 stat-area status | Voters | Valid | Invalid |
|---|---:|---|---:|---:|---:|
| ניצן | 20 | Single-stat locality; assignable by locality | 228 | 226 | 2 |
| אום בטין | 10 | Single-stat locality; assignable by locality | 117 | 114 | 3 |
| בית אריה | 10 | Reviewed alias for `בית אריה-עופרים`, code 3652, single-stat; assignable by locality | 375 | 375 | 0 |
| בית אריה | 30 | Reviewed alias for `בית אריה-עופרים`, code 3652, single-stat; assignable by locality | 370 | 367 | 3 |

Rows recovered from the K17 scans:

| Locality | Result kalpi | PDF source | PDF kalpi | Scanned address column | Polling-place name | Voters | Valid | Invalid |
|---|---:|---|---|---|---|---:|---:|---:|
| ערערה-בנגב | 50 | part 2 page 133 | `005-0` | `0` | `בי"ס אבן סינא` | 186 | 180 | 6 |
| ערערה-בנגב | 9900 | part 2 page 133 | `990-0` | `0` | `בי"ס אבן סינא` | 175 | 169 | 6 |
| טייבה | 110 | part 1 page 123 | `011-0` | `0` | `בי"ס אבן-סינא ב'` | 353 | 346 | 7 |
| טייבה | 150 | part 1 page 123 | `015-0` | `0` | `בי"ס אבן-סינא ב'` | 404 | 399 | 5 |
| טייבה | 250 | part 1 page 123 | `025-0` | `0` | `בי"ס חט"ב אל-סלאם` | 432 | 426 | 6 |
| טייבה | 260 | part 1 page 123 | `026-0` | `0` | `בי"ס חט"ב אל-סלאם` | 360 | 353 | 7 |
| טייבה | 270 | part 1 page 123 | `027-0` | `0` | `בי"ס חט"ב אל-סלאם` | 414 | 414 | 0 |
| טייבה | 280 | part 1 page 123 | `028-0` | `0` | `בי"ס אבן-סינא ב'` | 322 | 319 | 3 |
| טייבה | 290 | part 1 page 123 | `029-0` | `0` | `בי"ס אבן-סינא ב'` | 301 | 297 | 4 |
| טייבה | 300 | part 1 page 123 | `030-0` | `0` | `בי"ס אל-חכמה` | 313 | 311 | 2 |
| טייבה | 310 | part 1 page 123 | `031-0` | `0` | `בי"ס אל-חכמה` | 343 | 341 | 2 |

Sanity checks:

- K17 PDF kalpi notation maps `011-0` to result kalpi `110`, `015-0` to `150`, and `990-0` to `9900`.
- The surrounding rows on the same pages align with the official result locality and kalpi sequences.
- These rows are no longer unknown polling places, but they still need geocoding/review because the scan does not provide street-level addresses.

## Geocoding Scope

Geocoding is only needed where:

- the row is not an official envelope or reviewed non-geographic special row,
- the row can be linked to a polling-place address,
- the matched 2022 locality has multiple statistical areas.

Rows already assignable by the single-stat locality shortcut should not be geocoded unless a separate QA/debug view needs the point.

Row-level assignment should store one method:

- `single_stat_locality`
- `direct_address_geocode_needed`
- `address_geocode_to_current_polygons`
- `custom_point_size_polygon`
- `special_non_geographic`
- `official_envelope`
- `unresolved`

## Locality History

Localities can change between elections: names change, codes change, localities split, localities merge, and some localities disappear or are represented differently in later CBS layers.

The pipeline needs an explicit locality crosswalk with provenance.

Minimum crosswalk fields:

- election
- source locality code and name from the election result file
- target 2022 locality code and name, when applicable
- mapping status: exact code, exact name, alias, merge, split, retired, unknown
- whether the target can use the single-stat locality shortcut
- notes/source for the decision

Rules:

- Exact current locality-code matches can be automated.
- Historical aliases, spelling changes, merges, and splits must be reviewed and recorded.
- Reviewed split localities and `שער שומרון` are address-target sets: use each ballot row's address/geocoded point to assign it to the correct current polygon. Do not join current polygons, and do not split votes heuristically.
- Reviewed custom buckets (`TRIBE`, `GAZA`, `N.S.`, `HEBRON`) are assigned to synthetic point-size polygon geographies and preserve source-row contributions.
- A merge can use the single-stat shortcut only if the merged 2022 target has exactly one statistical area, or if a reviewed rule assigns the old locality unambiguously.

## Current Blockers

- Recovering true election-specific polling-place files for K16, K19, and K20 would materially improve confidence.
- A geocoding provider and cache/review policy is still needed.
- Locality polygons still need an official or reliable source.
- The frontend still needs a visual design for custom point-size polygon buckets.
