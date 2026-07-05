# Polling-Place Address Coverage

Last updated: 2026-07-05

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
| K21 / 2019 Apr | Generic official `voting-polls` table | Fallback only; not election-specific |
| K20 / 2015 | Generic official `voting-polls` table | Fallback only; not election-specific |
| K19 / 2013 | Generic official `voting-polls` table | Fallback only; not election-specific |
| K18 / 2009 | Generic official `voting-polls` table | Fallback only; not election-specific |
| K17 / 2006 | Address field inside official ballot-result file | Election-specific; high confidence for addressed rows |
| K16 / 2003 | Generic official `voting-polls` table | Fallback only; not election-specific |

Official election results package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Generic official polling-place datastore resource:

https://data.gov.il/api/3/action/datastore_search?resource_id=68c4d7e8-2218-48ee-996f-2db2f72b2395

K21 note:

- Historical-looking K21 URLs were found, but live and archived downloads did not yield a usable election-specific spreadsheet during this investigation.
- K21 remains fallback-quality until a real election-specific file is recovered.

## Direct Address Matching

Coverage is measured against official ballot-result rows.

Match key:

- locality code
- normalized kalpi number

Normalization:

- Split result rows such as `3.1` can match base kalpi `3`.
- For the generic polling-place table, aliases such as `10 -> 1` are accepted because the generic source uses a different kalpi-number convention.

This measures whether a ballot-result row can be associated with an address-like polling-place record. It does not prove historical exactness when the generic table is used.

## Direct Address Coverage

| Election | Year | Address source | Poll rows | Rows with direct address | Rows without direct address | Poll coverage | Eligible voters without direct address | Actual voters without direct address |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| K25 | 2022 | Official K25 polling-place XLSX | 12,545 | 11,707 | 838 | 93.32% | 0 (0.00%) | 462,807 (9.65%) |
| K24 | 2021 | Archived official polling-place XLSX | 12,926 | 12,127 | 799 | 93.82% | 0 (0.00%) | 425,512 (9.59%) |
| K23 | 2020 | Archived official polling-place XLSX | 11,179 | 10,631 | 548 | 95.10% | 0 (0.00%) | 330,209 (7.15%) |
| K22 | 2019 Sep | Archived official polling-place XLSX | 10,901 | 10,539 | 362 | 96.68% | 0 (0.00%) | 282,442 (6.33%) |
| K21 | 2019 Apr | Generic official polling-place table | 10,765 | 9,698 | 1,067 | 90.09% | 467,046 (7.37%) | 567,589 (13.08%) |
| K20 | 2015 | Generic official polling-place table | 10,414 | 9,804 | 610 | 94.14% | 176,373 (3.00%) | 362,617 (8.52%) |
| K19 | 2013 | Generic official polling-place table | 10,109 | 9,747 | 362 | 96.42% | 68,407 (1.21%) | 260,957 (6.81%) |
| K18 | 2009 | Generic official polling-place table | 9,264 | 9,227 | 37 | 99.60% | 210,419 (3.85%) | 201,065 (5.88%) |
| K17 | 2006 | Address field in official result file | 8,426 | 8,262 | 164 | 98.05% | Not available | 179,177 (5.62%) |
| K16 | 2003 | Generic official polling-place table | 7,886 | 7,674 | 212 | 97.31% | 191,007 (3.92%) | 182,385 (5.70%) |

Interpretation:

- K22-K25: every ordinary row has a direct address match; rows without direct addresses are not ordinary polling-place rows.
- K17: every ordinary row has an address except 15 rows listed below.
- K16 and K18-K21: matches use the generic polling-place table, so they are provisional. Kalpi numbers and polling-place locations may have changed.

## Ordinary Rows Without Direct Address

The table below excludes non-ordinary rows and shows only ordinary locality/kalpi rows that did not get a direct address match.

| Election | Ordinary rows without direct address | Ordinary eligible voters | Ordinary actual voters |
|---|---:|---:|---:|
| K25 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 |
| K21 | 762 | 467,046 | 326,806 |
| K20 | 317 | 176,373 | 129,708 |
| K19 | 136 | 68,407 | 47,160 |
| K18 | 36 | 23,500 | 14,146 |
| K17 | 15 | Not available | 4,693 |
| K16 | 63 | 32,711 | 24,089 |

## Single-Stat Locality Shortcut

The FileGDB-derived 2022 statistical-area layer has:

| Layer measure | Count |
|---|---:|
| Locality codes in the layer | 1,283 |
| Locality codes with exactly one `STAT_2022` | 1,139 |
| Locality codes with multiple `STAT_2022` values | 144 |

If an ordinary row without a direct address belongs to a matched locality with exactly one 2022 statistical area, it can still be assigned to statistical-area mode without geocoding.

This shortcut should be applied before geocoding. If a row's locality has exactly one 2022 statistical area, geocoding its polling-place address cannot change the statistical-area assignment.

| Election | Ordinary rows without direct address | Assignable by single-stat locality | Still unresolved rows | Still unresolved eligible voters | Still unresolved actual voters |
|---|---:|---:|---:|---:|---:|
| K25 | 0 | 0 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 | 0 | 0 |
| K21 | 762 | 102 | 660 | 412,944 | 288,511 |
| K20 | 317 | 38 | 279 | 161,215 | 117,778 |
| K19 | 136 | 16 | 120 | 61,674 | 42,370 |
| K18 | 36 | 10 | 26 | 17,089 | 11,189 |
| K17 | 15 | 2 | 13 | Not available | 4,348 |
| K16 | 63 | 1 | 62 | 32,122 | 23,549 |

## K17 Ordinary Rows Without Address

K17 has 15 ordinary rows with an empty address field.

| Locality | Kalpi | 2022 stat-area status | Voters | Valid | Invalid |
|---|---:|---|---:|---:|---:|
| ניצן | 20 | Single-stat locality; assignable by locality | 228 | 226 | 2 |
| אום בטין | 10 | Single-stat locality; assignable by locality | 117 | 114 | 3 |
| ערערה-בנגב | 50 | Matched locality with 3 statistical areas; needs address/geocode, but address is missing | 186 | 180 | 6 |
| ערערה-בנגב | 9900 | Matched locality with 3 statistical areas; needs address/geocode, but address is missing | 175 | 169 | 6 |
| טייבה | 110 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 353 | 346 | 7 |
| טייבה | 150 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 404 | 399 | 5 |
| טייבה | 250 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 432 | 426 | 6 |
| טייבה | 260 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 360 | 353 | 7 |
| טייבה | 270 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 414 | 414 | 0 |
| טייבה | 280 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 322 | 319 | 3 |
| טייבה | 290 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 301 | 297 | 4 |
| טייבה | 300 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 313 | 311 | 2 |
| טייבה | 310 | Matched locality with 8 statistical areas; needs address/geocode, but address is missing | 343 | 341 | 2 |
| בית אריה | 10 | Likely alias for `בית אריה-עופרים`, code 3652, single-stat; requires reviewed crosswalk before assignment | 375 | 375 | 0 |
| בית אריה | 30 | Likely alias for `בית אריה-עופרים`, code 3652, single-stat; requires reviewed crosswalk before assignment | 370 | 367 | 3 |

## Geocoding Scope

Geocoding is only needed where:

- the row is an ordinary row,
- the row can be linked to a polling-place address,
- the matched 2022 locality has multiple statistical areas.

Rows already assignable by the single-stat locality shortcut should not be geocoded unless a separate QA/debug view needs the point.

Row-level assignment should store one method:

- `single_stat_locality`
- `direct_address_geocode`
- `reviewed_crosswalk_single_stat`
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
- A split locality should stay unresolved unless the old locality can be mapped to one 2022 statistical area without ambiguity.
- A merge can use the single-stat shortcut only if the merged 2022 target has exactly one statistical area, or if a reviewed rule assigns the old locality unambiguously.

## Current Blockers

- Recovering true election-specific polling-place files for K16 and K18-K21 would materially improve confidence.
- A geocoding provider and cache/review policy is still needed.
- Locality polygons still need an official or reliable source.
- Historical locality aliases, splits, and merges need a reviewed crosswalk before they are used in the production pipeline.
