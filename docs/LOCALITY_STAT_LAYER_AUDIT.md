# Locality to 2022 Statistical-Area Layer Audit

Last updated: 2026-07-05

## Purpose

This note audits whether election localities from K16-K25 can be found in the current local 2022 statistical-area GeoJSON:

- `data/raw/statistical-areas-2022.geojson`

This matters because the statistical-area pipeline depends on knowing whether each election locality maps to:

- exactly one 2022 statistical area, in which case no address geocoding is needed, or
- multiple 2022 statistical areas, in which case polling-place address geocoding is needed, or
- no known 2022 statistical-area locality, in which case the row is unresolved until a complete layer or a locality crosswalk fixes it.

## GeoJSON Shape

The current file is a GeoJSON `FeatureCollection`.

Each feature is one statistical-area polygon, not one locality. The useful properties are:

| Property | Meaning |
|---|---|
| `SEMEL_YISHUV` | Locality code |
| `SHEM_YISHUV` | Locality name in Hebrew |
| `SHEM_YISHUV_ENGLISH` | Locality name in English |
| `STAT_2022` | 2022 statistical-area code within locality |
| `YISHUV_STAT_2022` | Combined locality/statistical-area code |
| `ROVA` | Quarter/borough code where present |
| `TAT_ROVA` | Sub-quarter code where present |
| `COD_TIFKUD` | Function/type code |

Observed size:

| Measure | Count |
|---|---:|
| GeoJSON features | 1,776 |
| Localities represented by `SEMEL_YISHUV` | 407 |
| Represented localities with one `STAT_2022` | 364 |
| Represented localities with multiple `STAT_2022` values | 43 |

## Matching Method Used In Audit

For each K16-K25 ballot-result file:

1. Exclude envelope rows from this locality audit.
2. Aggregate result rows by locality.
3. If the result row has `סמל ישוב`, match it exactly to GeoJSON `SEMEL_YISHUV`.
4. If no locality code exists, as in K17, match normalized `שם ישוב` exactly to GeoJSON `SHEM_YISHUV`.
5. Do not apply aliases, splits, merges, or historical name fixes in this audit.

This is deliberately strict. It tells us what matches automatically and what requires a reviewed election-to-2022 locality crosswalk.

## Critical Finding

The current 2022 GeoJSON is not a complete national statistical-area layer for this project.

It is missing major localities that must exist in a complete product dataset, including:

| Locality searched | Result in current GeoJSON |
|---|---|
| חיפה | No match |
| באר שבע | No match |
| נתניה | No match |
| הרצליה | No match |
| כפר סבא | No match |
| רהט | No match |
| נצרת | No match |
| אילת | No match |
| טייבה | No match |
| אום בטין | No match |
| ערערה-בנגב / ערערה | No match |

Examples that do exist:

| Locality | Code | 2022 statistical areas |
|---|---:|---:|
| ירושלים | 3000 | 243 |
| תל אביב -יפו | 5000 | 157 |
| אשדוד | 70 | 71 |
| בית אריה-עופרים | 3652 | 1 |
| ניצן | 351 | 1 |

Therefore, all current one-stat-locality counts are diagnostic only. They are valid for the localities present in this file, but the file cannot be the final statistical-area base layer.

## Election Locality Match Summary

The table below compares ordinary election localities to the current GeoJSON. Because the GeoJSON is incomplete, the unmatched counts are very large.

| Election | Election localities | Code matches | Name matches | Unmatched localities | Matched voters | Unmatched voters |
|---|---:|---:|---:|---:|---:|---:|
| K25 | 1,215 | 355 | 0 | 860 | 2,268,834 | 2,062,952 |
| K24 | 1,214 | 354 | 0 | 860 | 2,136,446 | 1,874,407 |
| K23 | 1,213 | 355 | 0 | 858 | 2,203,107 | 2,081,819 |
| K22 | 1,213 | 355 | 0 | 858 | 2,178,994 | 2,003,732 |
| K21 | 1,213 | 356 | 0 | 857 | 2,175,486 | 1,923,984 |
| K20 | 1,195 | 352 | 0 | 843 | 2,090,335 | 1,929,804 |
| K19 | 1,184 | 348 | 0 | 836 | 1,908,890 | 1,708,967 |
| K18 | 1,156 | 347 | 0 | 809 | 1,699,808 | 1,529,860 |
| K17 | 1,149 | 0 | 326 | 823 | 1,260,872 | 1,751,383 |
| K16 | 1,172 | 346 | 2 | 824 | 1,562,760 | 1,479,717 |

K17 has no locality code field in the datastore result shape used here, so this audit falls back to exact name matching for K17. That is why K17 has name matches instead of code matches.

## K17 Locality Examples

For the 15 K17 ordinary rows with empty address:

| K17 locality | Current GeoJSON result | Interpretation |
|---|---|---|
| ניצן | Exists as `ניצן`, code `351`, one statistical area | Assignable by locality |
| בית אריה | Exact name not present; `בית אריה-עופרים`, code `3652`, has one statistical area | Likely crosswalk alias, but must be explicitly reviewed |
| אום בטין | Not present by exact name | Unresolved against current GeoJSON |
| טייבה | Not present by exact name | Unresolved against current GeoJSON |
| ערערה-בנגב | Not present by exact name | Unresolved against current GeoJSON |

This is not evidence that `אום בטין`, `טייבה`, or `ערערה-בנגב` have multiple statistical areas. It only means they are not represented in the current GeoJSON under those names.

## Consequences

1. Obtain or rebuild a complete official 2022 statistical-area polygon layer before implementing final statistical-area mode.
2. Treat the current GeoJSON as partial until its source/export scope is verified.
3. Build an election-to-2022 locality crosswalk before using locality-based assignment.
4. Apply the single-stat locality shortcut only after matching to a complete verified statistical-area layer.
5. Use address geocoding only for rows whose verified 2022 locality has multiple statistical areas.

## Generated Audit Files

The working audit generated local scratch files under the Codex workspace:

- `work/locality-stat-layer-audit-summary.json`
- `work/locality-stat-layer-unmatched.csv`
- `work/k{election}-locality-to-stat-layer-audit.json`

These files are diagnostics and are not currently committed to the project.
