# Statistical-Area Assignment Coverage

Last updated: 2026-07-07

## Purpose

This document shows assignment coverage after applying the reviewed locality crosswalk and resolution plan.

It answers two separate questions:

1. Which election locality identities can be assigned directly because their reviewed 2022 locality has exactly one statistical area?
2. After direct address matching, reviewed locality assignment, custom buckets, and non-geographic buckets, how many rows still need an address and how many actual voters are still lost from the map?

Current product scope is K17-K25. K16 / 2003 is deferred until a usable election-specific polling-place address source is recovered.

## Generated Tables

Full CSV outputs:

- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.csv`
- `docs/ADDRESSLESS_ROWS_AFTER_REVIEWED_ASSIGNMENT.csv`

Source updates:

- K18 scanned polling-place PDF extraction resolves every ordinary official K18 result row to a polling-place address/place; only the special non-geographic row has no physical address.
- K17 scanned polling-place PDFs recover polling-place names for the 11 remaining multi-stat rows. Those rows still need geocoding/review because the scan address column is `0`, not a street address.
- K21 uses the archived official `archive_knesset21_kalpies_full_report.xls` instead of the generic polling-place fallback.
- K20 uses the archived official `archive_knesset20_tell_the_polls_9_3.xls`; every ordinary K20 row is addressed after split-row matching.
- K19 uses the archived official `archive_knesset19_all_stations.pdf`; every ordinary K19 row is addressed after RTL-aware table parsing.

The full single-stat mapping has 2,127 source locality identities from K17-K25 that resolve to exactly one 2022 statistical area.

| Match method | Source locality identities |
|---|---:|
| automatic_code_match | 1,103 |
| automatic_name_match | 937 |
| reviewed_locality | 87 |

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
| K20 | 2015 | 1,561 | 8,502 | 49 | 7 | 0 | 0 |
| K19 | 2013 | 1,532 | 8,298 | 45 | 6 | 0 | 0 |
| K18 | 2009 | 1,438 | 7,780 | 41 | 4 | 0 | 0 |
| K17 | 2006 | 1,241 | 6,984 | 38 | 3 | 11 | 3,603 |

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
| K20 | 2015 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K19 | 2013 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K18 | 2009 | 0 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| K17 | 2006 | 15 | 4 | 0 | 11 | Not available | 3,603 | 0.11% |

## Interpretation

- K19-K25 have no remaining non-envelope address gap after reviewed assignment.
- K18 has no remaining ordinary address gap after scanned-PDF extraction.
- K17 has 11 remaining multi-stat rows with recovered polling-place names but no street address.
- K16 is outside current product scope.
- Custom point-size polygon buckets are data-assigned now. Their visual treatment is a frontend design decision for later.
