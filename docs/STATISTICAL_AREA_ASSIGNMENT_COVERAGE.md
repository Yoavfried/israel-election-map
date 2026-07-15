# Statistical-Area Assignment Coverage

Last updated: 2026-07-15

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

This document is intentionally limited to statistical-area placement. Locality mode does not inherit these pending-geocode counts: it maps the full geographic scope directly and separately shows the combined official and reviewed-special envelope aggregate. See `docs/LOCALITY_MODE.md`.

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
| K25 | 2022 | 1,819 | 9,817 | 63 | 8 | 838 | 0 |
| K24 | 2021 | 1,864 | 10,193 | 62 | 8 | 799 | 0 |
| K23 | 2020 | 1,605 | 8,964 | 54 | 8 | 548 | 0 |
| K22 | 2019 Sep | 1,599 | 8,878 | 54 | 8 | 362 | 0 |
| K21 | 2019 Apr | 1,593 | 8,806 | 54 | 7 | 305 | 0 |
| K20 | 2015 | 1,547 | 8,516 | 49 | 7 | 295 | 0 |
| K19 | 2013 | 1,517 | 8,313 | 45 | 6 | 228 | 0 |
| K18 | 2009 | 1,444 | 7,774 | 41 | 4 | 1 | 0 |
| K17 | 2006 | 1,250 | 6,986 | 38 | 3 | 149 | 0 |

## Geocoding Input Readiness

This table covers only rows that require address-level geocoding.

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

## Current Pre-Geocode Statistical-Area Output

Because `data/processed/geocoding/geocoded_points.csv` does not exist yet, the final assignment stage currently maps only single-stat locality rows and custom geographies. Address-level rows remain pending.

| Election | Mapped rows | Mapped actual voters | Pending/missing geocode rows | Pending/missing geocode actual voters |
|---|---:|---:|---:|---:|
| K25 | 1,882 | 613,521 | 9,817 | 3,717,505 |
| K24 | 1,926 | 576,695 | 10,193 | 3,433,319 |
| K23 | 1,659 | 604,128 | 8,964 | 3,679,886 |
| K22 | 1,653 | 592,134 | 8,878 | 3,589,777 |
| K21 | 1,647 | 574,684 | 8,806 | 3,524,003 |
| K20 | 1,596 | 544,451 | 8,516 | 3,474,873 |
| K19 | 1,562 | 489,305 | 8,313 | 3,127,871 |
| K18 | 1,485 | 415,673 | 7,774 | 2,813,588 |
| K17 | 1,288 | 380,986 | 6,986 | 2,630,964 |

## Interpretation

- Assignment classification has no unresolved rows for K17-K25.
- K22-K25 and K20-K21 have ready geocoding inputs for all rows that need address-level assignment.
- K19 and K18 have a small number of place-only rows that need manual/reviewed geocoding.
- K17 has 456 place-only rows recovered directly from the scanned polling-place lists; they still need facility geocoding/review, but the current locality-only/no-place count is zero.
- Custom point-size polygon buckets are assigned now. Their visual treatment is a frontend decision.
- The broader OSM audit is intentionally not included in this table until those candidates are promoted into the final assignment builder. See `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md`.
