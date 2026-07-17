# Geographic Assignment Status

Last updated: 2026-07-17

## Statistical-Area Mode

Statistical-area mode now uses direct election-specific CBS ballot crosswalks and matching historical geometry. It does not assign votes from polling-place addresses.

| Election | Vintage | Mapped geographic rows | Pending rows | Mapped voter share |
|---|---:|---:|---:|---:|
| K25 | 2011 | 10,877 | 822 | 93.88% |
| K24 | 2011 | 11,161 | 958 | 94.27% |
| K23 | 2011 | 9,930 | 693 | 92.37% |
| K22 | 2011 | 9,919 | 612 | 93.63% |
| K21 | 2011 | 9,845 | 608 | 94.41% |
| K20 | 2011 | 9,478 | 634 | 92.89% |
| K19 | 2011 | 9,309 | 566 | 94.06% |
| K18 | 2008 | 8,740 | 519 | 94.13% |
| K17 | 1995 | 7,853 | 421 | 94.65% |

The unresolved rows are source gaps, not an address queue. They remain visible in coverage and in `data/processed/assignments/unresolved_statistical_area_assignment_rows.csv`. The CBS `Stat08_Unite` and `Stat11_Ref` demographic references are deliberately ignored for election assignment; using them as unions previously created invalid single-area fallbacks.

## Locality Mode

Locality mode independently maps 100% of the geographic scope using the reviewed locality crosswalk, election-specific composite municipalities, joined polling-register display unions, and reviewed custom geographies. Envelope results remain a separate national result.

## Address Data

The OSM/Photon work is retained as a polling-place location dataset and source-quality audit. Its previous 2022 point-in-polygon assignments are research artifacts and are not promoted into election-result geography.

Full methodology and source provenance are in `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` and `docs/DATA_PIPELINE.md`. Overall workstream status is in `docs/PROJECT_STATUS.md`.
