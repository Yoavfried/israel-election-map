# Project Status

Last updated: 2026-07-17

This is the repository's only project completion tracker. Methodology, audit
evidence, and generated coverage tables remain in subject-specific documents,
but open/complete workstream declarations belong here.

## Workstreams

| Workstream | Status | Current boundary |
|---|---|---|
| K17-K25 election normalization | Complete | 96,529 source rows are normalized and reconciled. |
| Locality-mode aggregation | Implemented; audit open | All geographic-scope rows are mapped, but the partial/no-result locality-history review is unfinished. |
| Historical statistical-area mode | Implemented; source gaps open | Election-specific CBS crosswalks and matching 1995/2008/2011 geometry are active. Pending rows remain explicit. |
| Party/list names | Complete | All published K17-K25 lists have reviewed display names. English labels may fall back to the reviewed Hebrew name when no separate translation is maintained. |
| Party colors | In progress | The stable-letter mechanism and election-specific overrides work; the editorial color table is incomplete. |
| Wikipedia links | In progress | Hebrew and English candidates exist for many lists, but links and intentional blanks are not fully audited. |
| UX and accessibility | In progress | The bilingual responsive map works, but interaction polish, mobile QA, keyboard behavior, and accessibility review continue. |
| Product features | In progress | Search/navigation, additional map coloring modes, contribution drill-down, methodology UI, and a possible polling-place layer remain planned or partial. |
| Public data distribution | Implemented; release policy open | Versioned K17-K25 ballot CSVs, polygon aggregates, full-resolution geography ZIPs, metadata, checksums, and validation are committed under `public-data/v1`. Licensing and a future release/versioning policy remain open. |
| Public repository hardening | In progress | Documentation and repository hygiene are public-facing; fresh-clone source bootstrap, licensing, CI, and performance checks are not finished. |

## Public Data Release

The committed `public-data/v1` release can be used without running the private
working-data pipeline. It includes:

- nine complete election-specific ballot-row CSVs covering 96,529 rows;
- statistical-area, locality, custom-geography, envelope, and unresolved tables;
- full-resolution 1995, 2008, 2011, and 2022 statistical-area packages;
- current locality, reviewed composite-locality, and custom-geography packages;
- direct `geography_id` joins, party/election metadata, checksums, and validation.

Map colors and other presentation choices are intentionally excluded from the
data release and remain in `web/app/`. The public files are downloadable, but a
reuse license has not yet been selected; the repository must not describe them
as legally open data until that decision is made.

## Statistical-Area Data Gaps

Statistical mode maps results to the historical area vintage named by the official election crosswalk: 1995 for K17, 2008 for K18, and 2011 for K19-K25. Pending rows are preserved but are not painted onto a polygon.

| Election | Pending rows | Pending actual voters | Mapped voter share |
|---|---:|---:|---:|
| K17 | 421 | 161,269 | 94.65% |
| K18 | 519 | 189,711 | 94.13% |
| K19 | 566 | 214,788 | 94.06% |
| K20 | 634 | 285,705 | 92.89% |
| K21 | 608 | 228,922 | 94.41% |
| K22 | 612 | 266,390 | 93.63% |
| K23 | 693 | 326,837 | 92.37% |
| K24 | 958 | 229,783 | 94.27% |
| K25 | 822 | 264,887 | 93.88% |

All pending rows lack a matching official ballot-crosswalk row and belong to a locality with multiple historical areas. Earlier near-100% K19-K25 coverage was incorrect because demographic reference fields were treated as election-area unions, making many multi-area localities appear eligible for a single-area fallback. That merge has been removed and the affected rows are pending again.

These are missing assignment records, not an address-geocoding queue. A polling-place building may serve voters from multiple statistical areas, so OSM, Photon, or another building geocoder cannot safely repair them.

## Geometry Caveats

- Every currently assigned statistical-area ID resolves to geometry; the generated assignment summary reports zero missing-geometry rows.
- Historical election-area IDs remain separate. The CBS `Stat08_Unite` and `Stat11_Ref` demographic references are not assignment or display unions.
- Twenty-three canonical historical IDs require documented supplements because the downloaded CBS geometry omits them. One comes from an official transition-key union and 22 use exact-ID ArcGIS geometry, including the 18 tribal localities and Hebron used only for 2011-vintage elections.
- Outside those explicit supplements, detailed West Bank footprints from ArcGIS are display-only derivatives. They never supply vote totals. K17/K18 now use detailed polygons for every ordinary West Bank marker with results; their tribe and Hebron results remain custom markers because 1995/2008 assignment evidence is absent.
- The neutral grey land backdrop is visual context only. It does not imply that a historical statistical area or election result exists underneath it.
- K25 intentionally stays on 2011 areas. At least 3,543 direct-crosswalk rows target 2011 areas that split across multiple 2022 areas, so a wholesale conversion would invent precision.

See `STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md` for the generated coverage table and `HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` for source and matching rules.
