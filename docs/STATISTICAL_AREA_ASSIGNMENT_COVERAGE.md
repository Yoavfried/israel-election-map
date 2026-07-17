# Statistical-Area Assignment Coverage

Last updated: 2026-07-17

This is the current public statistical-mode coverage after official historical crosswalk assignment, single-historical-area fallback, and reviewed custom geographies. Envelope and reviewed non-geographic rows are excluded from the geographic-scope denominator.

| Election | Vintage | Mapped rows | Mapped actual voters | Pending rows | Pending actual voters | Mapped share |
|---|---:|---:|---:|---:|---:|---:|
| K25 | 2011 | 10,877 | 4,066,139 | 822 | 264,887 | 93.88% |
| K24 | 2011 | 11,161 | 3,780,231 | 958 | 229,783 | 94.27% |
| K23 | 2011 | 9,930 | 3,957,177 | 693 | 326,837 | 92.37% |
| K22 | 2011 | 9,919 | 3,915,521 | 612 | 266,390 | 93.63% |
| K21 | 2011 | 9,845 | 3,869,765 | 608 | 228,922 | 94.41% |
| K20 | 2011 | 9,478 | 3,733,619 | 634 | 285,705 | 92.89% |
| K19 | 2011 | 9,309 | 3,402,388 | 566 | 214,788 | 94.06% |
| K18 | 2008 | 8,740 | 3,039,550 | 519 | 189,711 | 94.13% |
| K17 | 1995 | 7,853 | 2,850,681 | 421 | 161,269 | 94.65% |

Generated evidence:

- `data/processed/assignments/historical_ballot_assignment_summary.csv`
- `data/processed/assignments/final_assignment_summary.csv`
- `data/processed/public/election_summary.csv`
- `data/processed/assignments/unresolved_statistical_area_assignment_rows.csv`

See `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` for source and matching rules.

Reason summary:

- Every pending row lacks a matching official ballot-crosswalk row and belongs to a locality with multiple historical areas.
- Demographic reference fields are not used to merge those areas or trigger a single-area fallback.
- No mapped row is pending because its statistical-area geometry is missing.

See `docs/PROJECT_STATUS.md` for the plain-language interpretation and product-work status.
