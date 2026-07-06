# Locality to 2022 Statistical-Area Layer Audit

Last updated: 2026-07-06

## Purpose

This note audits whether election localities from K16-K25 can be found in the current 2022 statistical-area polygon source:

- `data/raw/ezorim_statistiim_2022.gdb`

This is the strict automatic baseline. Production assignment now applies the reviewed locality resolution plan on top of this baseline:

- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.md`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`

This matters because the statistical-area pipeline needs to know whether each election locality maps to:

- exactly one 2022 statistical area, where no polling-place geocoding is needed,
- multiple 2022 statistical areas, where polling-place address geocoding is needed, or
- no matched 2022 locality, where an explicit locality crosswalk is required.

## Source Shape

The current FileGDB has one layer, `statistical_areas_2022`.

| Measure | Count |
|---|---:|
| Polygon features | 3,842 |
| Unique locality/statistical-area pairs | 3,739 |
| Locality codes represented by `SEMEL_YISHUV` | 1,283 |
| Locality codes with one `STAT_2022` | 1,139 |
| Locality codes with multiple `STAT_2022` values | 144 |

The source includes the major localities that were missing from the old partial GeoJSON:

| Locality | Code | 2022 statistical areas |
|---|---:|---:|
| חיפה | 4000 | 106 |
| באר שבע | 9000 | 83 |
| נתניה | 7400 | 73 |
| הרצלייה | 6400 | 36 |
| כפר סבא | 6900 | 32 |
| רהט | 1161 | 21 |
| נצרת | 7300 | 24 |
| אילת | 2600 | 25 |
| טייבה | 2730 | 8 |
| אום בטין | 1358 | 1 |
| ערערה-בנגב | 1192 | 3 |
| בית אריה-עופרים | 3652 | 1 |

## Matching Method

For each K16-K25 ballot-result file:

1. Exclude envelope rows from this locality audit.
2. Aggregate result rows by election locality.
3. Match by locality code to `SEMEL_YISHUV` when the result file exposes a code.
4. Fall back to exact normalized locality name only when no locality code is available. This mainly affects K17.
5. Do not apply historical aliases, splits, merges, retired-locality rules, or spelling fixes in this audit.

This is deliberately strict. It measures automatic coverage before the reviewed locality crosswalk exists.

## Election Locality Match Summary

| Election | Election localities | Code matches | Name matches | Unmatched localities | Matched single-stat localities | Matched multi-stat localities | Matched voters | Unmatched voters |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| K25 | 1,215 | 1,186 | 0 | 29 | 1,042 | 144 | 4,311,724 | 20,062 |
| K24 | 1,214 | 1,186 | 0 | 28 | 1,042 | 144 | 3,997,838 | 13,015 |
| K23 | 1,213 | 1,184 | 0 | 29 | 1,040 | 144 | 4,267,860 | 17,066 |
| K22 | 1,213 | 1,184 | 0 | 29 | 1,040 | 144 | 4,166,688 | 16,038 |
| K21 | 1,213 | 1,184 | 0 | 29 | 1,040 | 144 | 4,089,267 | 10,203 |
| K20 | 1,195 | 1,165 | 0 | 30 | 1,021 | 144 | 4,007,940 | 12,199 |
| K19 | 1,184 | 1,155 | 0 | 29 | 1,011 | 144 | 3,607,970 | 9,887 |
| K18 | 1,156 | 1,130 | 0 | 26 | 989 | 141 | 3,222,827 | 6,841 |
| K17 | 1,149 | 0 | 1,055 | 94 | 937 | 118 | 2,442,550 | 569,705 |
| K16 | 1,172 | 1,115 | 2 | 55 | 973 | 144 | 3,015,072 | 27,405 |

Interpretation:

- K16 and K18-K25 have strong automatic locality-code coverage against the 2022 layer.
- K17 is different because the current datastore shape used here does not expose the same locality-code field. Exact name matching leaves many real localities unmatched due spelling and historical-name differences, for example `תל אביב - יפו`, `הרצליה`, and `מודיעין-מכבים-רעו`.
- The K17 unmatched-voter number is therefore mostly a crosswalk problem, not evidence that those voters cannot be mapped.

## K17 Addressless Rows

The K17 result file has 15 non-envelope rows with an empty address field. Against the FileGDB-derived 2022 layer plus the reviewed locality resolution:

- 2 rows are assignable by the single-stat locality shortcut: `ניצן` and `אום בטין`.
- 11 rows are in matched multi-stat localities: `ערערה-בנגב` has 3 statistical areas and `טייבה` has 8.
- 2 rows are `בית אריה`, now reviewed as an alias for `בית אריה-עופרים` code 3652, a single-stat locality.

## Consequences

1. Use the FileGDB as the canonical 2022 statistical-area source.
2. Do not use the old partial GeoJSON for coverage calculations.
3. Apply the reviewed locality resolution plan before deciding whether a row needs geocoding.
4. Apply the single-stat locality shortcut before geocoding.
5. Geocode polling-place addresses only for rows in matched multi-stat localities or reviewed address-target sets that are not covered by custom point or non-geographic rules.
6. Store assignment provenance so the UI can distinguish exact-code, exact-name, reviewed-crosswalk, address-target-set, custom point, geocoded, non-geographic, and unresolved records.

## Generated Audit Files

The working audit generated scratch files under the Codex workspace:

- `work/stat_area_counts_by_locality.json`
- `work/localities_by_stat_area_count.csv`
- `work/locality-stat-layer-audit-summary.json`
- `work/locality-stat-layer-unmatched.csv`
- `work/k{election}-locality-to-stat-layer-audit.json`

These files are diagnostics and are not committed to the project.
