# Polling-Place Address Coverage

Last updated: 2026-07-05

## Purpose

The statistical-area map needs an approximate kalpi-to-statistical-area assignment. Since official ballot-result rows do not include polygons or coordinates, the primary approach is to attach each kalpi to the address of its polling-place building, geocode that address, and run point-in-polygon against the 2022 statistical-area layer.

There is also a shortcut for localities that have exactly one statistical area in the 2022 layer: those locality results can be assigned to that statistical area without a kalpi address.

This is intentionally approximate. It maps the polling place, not the voters' residential statistical areas.

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

- Historical-looking K21 URLs were found for files such as `election/Documents/table-of-kalpies.csv`, `Kneset20/Documents/kalpies21_b.xls`, `kalpies_full_report.xls`, and `special_kalpies21.xls`.
- Live requests redirected/failed, and archived downloads inspected during this pass produced small error/playback files rather than usable spreadsheets.
- K21 should be treated as a fallback-quality election until a real election-specific file is recovered.

## Direct Address Matching

Coverage is measured against official ballot-result rows.

Match key:

- locality code
- normalized kalpi number

Normalization:

- Split result rows such as `3.1` can match base kalpi `3`.
- For the generic polling-place table, aliases such as `10 -> 1` are accepted because the generic source uses a different kalpi-number convention.

This measures whether a ballot-result row can be associated with an address-like polling-place record. It does not prove the address is historically exact when the generic table is used.

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

- K22-K25: every ordinary row has a matched address; only envelope rows are unmapped by address.
- K17: every ordinary row has an address except 15 rows listed below.
- K16 and K18-K21: matches use the generic polling-place table, so they are provisional. Kalpi numbers and polling-place locations may have changed.

## Ordinary Rows Without Direct Address

Envelope rows are excluded from this section. The remaining rows are ordinary locality/kalpi rows that did not get a direct address match.

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

The 2022 statistical-area GeoJSON has:

| Layer measure | Count |
|---|---:|
| Localities in the layer | 407 |
| Localities with exactly one `STAT_2022` | 364 |
| Localities with multiple `STAT_2022` values | 43 |

If an ordinary unmatched row belongs to a locality with exactly one 2022 statistical area, it can still be assigned to statistical-area mode through the locality, without a polling-place address.

The table below excludes envelope rows and only evaluates ordinary rows without a direct matched address.

| Election | Ordinary rows without direct address | Assignable by single-stat locality | Still unresolved rows | Still unresolved eligible voters | Still unresolved actual voters |
|---|---:|---:|---:|---:|---:|
| K25 | 0 | 0 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 | 0 | 0 |
| K21 | 762 | 40 | 722 | 445,825 | 310,426 |
| K20 | 317 | 15 | 302 | 171,212 | 125,431 |
| K19 | 136 | 3 | 133 | 67,409 | 46,320 |
| K18 | 36 | 0 | 36 | 23,500 | 14,146 |
| K17 | 15 | 1 | 14 | Not available | 4,465 |
| K16 | 63 | 1 | 62 | 32,122 | 23,549 |

For K17, the one row resolved by this shortcut is `ניצן` kalpi `20`, because `ניצן` appears in the 2022 statistical-area layer with a single `STAT_2022`.

## K17 Ordinary Rows Without Address

K17 has 15 ordinary rows with an empty address field. After the single-stat locality shortcut, 14 remain unresolved by the current automated rules.

| Locality | Kalpi | 2022 stat-area status | Voters | Valid | Invalid |
|---|---:|---|---:|---:|---:|
| ניצן | 20 | Single-stat locality; assignable by locality | 228 | 226 | 2 |
| ערערה-בנגב | 50 | Not matched in current 2022 statistical-area GeoJSON | 186 | 180 | 6 |
| ערערה-בנגב | 9900 | Not matched in current 2022 statistical-area GeoJSON | 175 | 169 | 6 |
| אום בטין | 10 | Not matched in current 2022 statistical-area GeoJSON | 117 | 114 | 3 |
| טייבה | 110 | Not matched in current 2022 statistical-area GeoJSON | 353 | 346 | 7 |
| טייבה | 150 | Not matched in current 2022 statistical-area GeoJSON | 404 | 399 | 5 |
| טייבה | 250 | Not matched in current 2022 statistical-area GeoJSON | 432 | 426 | 6 |
| טייבה | 260 | Not matched in current 2022 statistical-area GeoJSON | 360 | 353 | 7 |
| טייבה | 270 | Not matched in current 2022 statistical-area GeoJSON | 414 | 414 | 0 |
| טייבה | 280 | Not matched in current 2022 statistical-area GeoJSON | 322 | 319 | 3 |
| טייבה | 290 | Not matched in current 2022 statistical-area GeoJSON | 301 | 297 | 4 |
| טייבה | 300 | Not matched in current 2022 statistical-area GeoJSON | 313 | 311 | 2 |
| טייבה | 310 | Not matched in current 2022 statistical-area GeoJSON | 343 | 341 | 2 |
| בית אריה | 10 | Exact name not matched; likely alias candidate for `בית אריה-עופרים`, which is single-stat | 375 | 375 | 0 |
| בית אריה | 30 | Exact name not matched; likely alias candidate for `בית אריה-עופרים`, which is single-stat | 370 | 367 | 3 |

Do not silently apply the `בית אריה` alias in the pipeline until a locality-alias table is added and documented.

## Implementation Decisions

- Proceed with K16-K25 for both locality and statistical-area modes.
- Treat the statistical-area map as polling-place geography, not voter-residence geography.
- For localities with exactly one 2022 statistical area, allow assignment by locality when direct kalpi address assignment is unavailable.
- Store every statistical-area assignment with provenance: election, address source, match rule, geocoder, coordinate, polygon id, confidence, and failure reason.
- Store unresolved rows separately with full vote totals and include them in details panels and election-level summaries.
- Show mapped coverage in the UI so users know how much of the vote total is represented by polygons for the selected election and mode.

## Current Blockers

- Recovering true election-specific polling-place files for K16 and K18-K21 would materially improve confidence.
- A geocoding decision is still needed.
- Locality polygons still need an official or reliable source.
- Historical locality aliases need an explicit, reviewed mapping table before being used in the pipeline.
