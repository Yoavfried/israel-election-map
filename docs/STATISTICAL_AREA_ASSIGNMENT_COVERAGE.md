# Statistical-Area Assignment Coverage

Last updated: 2026-07-07

## Purpose

This document shows assignment coverage after applying the reviewed locality crosswalk and resolution plan.

It answers two separate questions:

1. Which election locality identities can be assigned directly because their reviewed 2022 locality has exactly one statistical area?
2. After direct address matching, reviewed locality assignment, custom buckets, and non-geographic buckets, how many rows still need an address and how many actual voters are still lost from the map?

## Generated Tables

Full CSV outputs:

- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.csv`
- `docs/ADDRESSLESS_ROWS_AFTER_REVIEWED_ASSIGNMENT.csv`

2026-07-06 source update:

- K18 scanned polling-place PDF extraction is now integrated into the coverage tables below. It resolves every ordinary official K18 result row to a polling-place address/place; only the special non-geographic row has no physical address.
- New K17 scanned polling-place PDFs recover polling-place names for the 11 remaining multi-stat rows. Those rows still need geocoding/review because the scan address column is `0`, not a street address.

2026-07-07 source update:

- K21 now uses the archived official `archive_knesset21_kalpies_full_report.xls` instead of the generic polling-place fallback.
- K21 has one ordinary row without a direct address: `נורית` [833], kalpi 1. It is covered by the reviewed single-stat locality shortcut.

The full single-stat mapping has 2,166 source locality identities from K16-K25 that resolve to exactly one 2022 statistical area.

| Match method | Source locality identities |
|---|---:|
| automatic_code_match | 1,133 |
| automatic_name_match | 939 |
| reviewed_locality | 94 |

## Assignment Coverage

This table is row-level ballot-result coverage after applying:

1. official envelope detection,
2. reviewed locality crosswalk and custom buckets,
3. single-stat locality assignment,
4. direct-address geocoding scope for remaining multi-stat localities.

| Election | Year | Single-stat locality rows | Direct-address geocode rows | Custom point rows | Special non-geographic rows | Unresolved rows | Unresolved actual voters |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| K25 | 2022 | 1,825 | 9,812 | 63 | 7 | 0 | 0 |
| K24 | 2021 | 1,887 | 10,171 | 62 | 7 | 0 | 0 |
| K23 | 2020 | 1,622 | 8,948 | 54 | 7 | 0 | 0 |
| K22 | 2019 Sep | 1,616 | 8,862 | 54 | 7 | 0 | 0 |
| K21 | 2019 Apr | 1,610 | 8,789 | 54 | 7 | 0 | 0 |
| K20 | 2015 | 1,561 | 8,229 | 49 | 7 | 273 | 116,744 |
| K19 | 2013 | 1,532 | 8,179 | 45 | 6 | 119 | 42,261 |
| K18 | 2009 | 1,438 | 7,780 | 41 | 4 | 0 | 0 |
| K17 | 2006 | 1,241 | 6,984 | 38 | 3 | 11 | 3,603 |
| K16 | 2003 | 1,209 | 6,416 | 53 | 3 | 56 | 21,938 |

## Remaining Address Gap

This table excludes official envelope rows. `Still missing address` means the row is non-envelope, is not covered by single-stat locality assignment, is not covered by a custom point bucket, and lacks a direct address needed for multi-stat or reviewed address-target-set geocoding.

`Actual voters lost from map` is the share of total actual voters in that election that remains unresolved after the reviewed assignment logic. Official envelope rows and reviewed non-geographic special rows are not counted as lost here.

| Election | Year | Non-envelope rows without direct address | Assigned by single-stat | Assigned by custom point | Still missing address rows | Still missing eligible voters | Still missing actual voters | Actual voters lost from map |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| K25 | 2022 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K24 | 2021 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K23 | 2020 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K22 | 2019 Sep | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K21 | 2019 Apr | 1 | 1 | 0 | 0 | 0 | 0 | 0.00% |
| K20 | 2015 | 317 | 39 | 5 | 273 | 157,603 | 116,744 | 2.74% |
| K19 | 2013 | 136 | 16 | 1 | 119 | 60,951 | 42,261 | 1.10% |
| K18 | 2009 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K17 | 2006 | 15 | 4 | 0 | 11 | Not available | 3,603 | 0.11% |
| K16 | 2003 | 63 | 3 | 4 | 56 | 30,028 | 21,938 | 0.69% |

## Interpretation

- K22-K25 have no remaining non-envelope address gap after reviewed assignment.
- K21 now has no remaining ordinary address gap after reviewed assignment; its former unresolved multi-stat rows have election-specific polling-place addresses and move into direct-address geocoding scope.
- K20, K19, and K16 still depend on the generic polling-place fallback, so their unresolved rows are mostly multi-stat localities where a direct historical address is still needed.
- K18 now uses the election-specific scanned polling-place PDF instead of the generic fallback and has no remaining ordinary address gap.
- K17 improves after the reviewed crosswalk: `ניצן`, `אום בטין`, and two `בית אריה` rows are assignable without geocoding. The 11 remaining multi-stat rows now have recovered polling-place names from the K17 scans, but still need geocoding/review.
- Custom point-size polygon buckets are data-assigned now. Their visual treatment is a frontend design decision for later.
