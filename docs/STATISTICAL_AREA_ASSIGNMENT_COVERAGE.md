# Statistical-Area Assignment Coverage

Last updated: 2026-07-07

## Purpose

This document shows current row-level coverage after applying:

1. official envelope detection,
2. the reviewed locality crosswalk,
3. the 2022 single-stat locality shortcut,
4. reviewed custom point-size geography buckets,
5. available polling-place address sources.

Two different states matter:

- Assignment classification: whether each ballot-result row has a known handling rule.
- Geocoding readiness: whether rows that need address-level point-in-polygon assignment currently have a usable address or reviewed geocode.

Current product scope is K17-K25. K16 / 2003 is deferred.

## Generated Tables

Current generated outputs live under `data/processed/`:

- `assignments/assignment_plan_summary.csv`
- `geocoding/geocoding_input_summary.csv`
- `assignments/final_assignment_summary.csv`
- `public/election_summary.csv`

Committed reference artifact:

- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.csv`

## Assignment Classification

This is the pre-geocode assignment plan. `Geocode-needed rows` are valid geographic rows whose final statistical-area assignment depends on a reviewed coordinate.

| Election | Year | Single-stat rows | Geocode-needed rows | Custom rows | Special rows | Envelope rows | Unresolved rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| K25 | 2022 | 1,803 | 9,834 | 63 | 7 | 838 | 0 |
| K24 | 2021 | 1,863 | 10,195 | 62 | 7 | 799 | 0 |
| K23 | 2020 | 1,603 | 8,967 | 54 | 7 | 548 | 0 |
| K22 | 2019 Sep | 1,597 | 8,881 | 54 | 7 | 362 | 0 |
| K21 | 2019 Apr | 1,591 | 8,808 | 54 | 7 | 305 | 0 |
| K20 | 2015 | 1,544 | 8,519 | 49 | 7 | 295 | 0 |
| K19 | 2013 | 1,515 | 8,315 | 45 | 6 | 228 | 0 |
| K18 | 2009 | 1,438 | 7,780 | 41 | 4 | 1 | 0 |
| K17 | 2006 | 1,241 | 6,995 | 38 | 3 | 149 | 0 |

## Geocoding Input Readiness

This table covers only rows that require address-level geocoding.

| Election | Ready address rows | Place-only rows | Missing address rows | Missing-address actual voters |
|---|---:|---:|---:|---:|
| K25 | 9,834 | 0 | 0 | 0 |
| K24 | 0 | 0 | 10,195 | 3,433,896 |
| K23 | 0 | 0 | 8,967 | 3,680,687 |
| K22 | 0 | 0 | 8,881 | 3,590,594 |
| K21 | 8,808 | 0 | 0 | 0 |
| K20 | 8,519 | 0 | 0 | 0 |
| K19 | 8,309 | 6 | 0 | 0 |
| K18 | 7,769 | 11 | 0 | 0 |
| K17 | 6,984 | 0 | 11 | 3,603 |

## Current Pre-Geocode Map Output

Because `data/processed/geocoding/geocoded_points.csv` does not exist yet, the final assignment stage currently maps only single-stat locality rows and custom geographies. Address-level rows remain pending.

| Election | Mapped rows | Mapped actual voters | Pending/missing geocode rows | Pending/missing geocode actual voters |
|---|---:|---:|---:|---:|
| K25 | 1,866 | 607,457 | 9,834 | 3,723,709 |
| K24 | 1,925 | 576,281 | 10,195 | 3,433,896 |
| K23 | 1,657 | 603,487 | 8,967 | 3,680,687 |
| K22 | 1,651 | 591,471 | 8,881 | 3,590,594 |
| K21 | 1,645 | 574,009 | 8,808 | 3,524,678 |
| K20 | 1,593 | 543,828 | 8,519 | 3,475,496 |
| K19 | 1,560 | 488,732 | 8,315 | 3,128,444 |
| K18 | 1,479 | 413,520 | 7,780 | 2,815,741 |
| K17 | 1,279 | 376,882 | 6,995 | 2,635,068 |

## Interpretation

- Assignment classification has no unresolved rows for K17-K25.
- K22-K24 are blocked for geocoding because election-specific polling-place address files are not currently present in `data/raw`.
- K25, K21, and K20 have ready geocoding inputs for all rows that need address-level assignment.
- K19 and K18 have a small number of place-only rows that need manual/reviewed geocoding.
- K17 has 11 rows in multi-stat localities with no usable street address; these still need manual resolution or an additional source.
- Custom point-size polygon buckets are assigned now. Their visual treatment is a frontend decision.
