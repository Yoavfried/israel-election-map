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
| Historical statistical-area mode | Implemented; source gaps open | Election-specific CBS crosswalks and matching 1995/2008/2011 geometry are active. All 44 Tier A K20/K21 residual-partition decisions are applied with explicit inferred-assignment provenance; Tier B and other source gaps remain open. |
| Party/list names | Complete | All published K17-K25 lists have reviewed display names. English labels may fall back to the reviewed Hebrew name when no separate translation is maintained. |
| Party colors | In progress | The stable-letter mechanism and election-specific overrides work; the editorial color table is incomplete. |
| Wikipedia links | In progress | Hebrew and English candidates exist for many lists, but links and intentional blanks are not fully audited. |
| UX and accessibility | Continuous | Responsive bilingual UX, mobile behavior, keyboard support, and accessibility are reviewed with every change rather than treated as a one-time feature. |
| Product features | Planned; search next | Search may proceed now. National results, single-party mode, two-party comparison, and then the equal-priority satellite/OSM/3D suite follow the color and Wikipedia audits; design details are in `FEATURE_PLAN.md`. |
| Public data distribution | Implemented; release policy open | Versioned K17-K25 ballot CSVs, polygon aggregates, full-resolution geography ZIPs, metadata, checksums, and validation are committed under `public-data/v1`. Future release/versioning policy remains open. |
| Public repository hardening | In progress | MIT licensing, third-party data notices, and public-facing repository hygiene are in place; fresh-clone source bootstrap, CI, and performance checks are not finished. |

## Public Data Release

The committed `public-data/v1` release can be used without running the private
working-data pipeline. It includes:

- nine complete election-specific ballot-row CSVs covering 96,529 rows;
- statistical-area, locality, custom-geography, envelope, and unresolved tables;
- full-resolution 1995, 2008, 2011, and 2022 statistical-area packages;
- current locality, reviewed composite-locality, and custom-geography packages;
- direct `geography_id` joins, party/election metadata, checksums, and validation.
- machine-readable assignment provenance, including the 44 reviewed ArcGIS
  reconstruction decisions and row-level inferred-assignment labels.

Map colors and other presentation choices are intentionally excluded from the
data release and remain in `web/app/`. Original project software and
documentation use the MIT License. Official source data retain their source
terms as described in `THIRD_PARTY_NOTICES.md`.

## Statistical-Area Data Gaps

Statistical mode maps results to the historical area vintage named by the official election crosswalk: 1995 for K17, 2008 for K18, and 2011 for K19-K25. Pending rows are preserved but are not painted onto a polygon.

Across all nine elections, 5,082 rows representing 1,842,915 actual voters are
pending. Overall statistical mapped-voter coverage is 94.70%; the
election-specific range is shown below.

| Election | Pending rows | Pending actual voters | Mapped voter share |
|---|---:|---:|---:|
| K17 | 421 | 161,269 | 94.65% |
| K18 | 519 | 189,711 | 94.13% |
| K19 | 566 | 214,788 | 94.06% |
| K20 | 61 | 28,038 | 99.30% |
| K21 | 430 | 161,212 | 96.07% |
| K22 | 612 | 266,390 | 93.63% |
| K23 | 693 | 326,837 | 92.37% |
| K24 | 958 | 229,783 | 94.27% |
| K25 | 822 | 264,887 | 93.88% |

All pending rows lack a matching official ballot-crosswalk row and belong to a locality with multiple historical areas. Earlier near-100% K19-K25 coverage was incorrect because demographic reference fields were treated as election-area unions, making many multi-area localities appear eligible for a single-area fallback. That merge has been removed and the affected rows are pending again.

The automated ArcGIS residual-partition audit is complete. Tier A is approved:
573 K20 rows representing 257,667 actual voters and 178 K21 rows representing
67,710 actual voters are assigned. The linkage is inferred, while every ballot
and vote value remains from the official normalized result. Public ballot rows
identify it with `final_assignment_method=arcgis_residual_partition_tier_a`.

Tier B remains pending: 23 locality-election decisions cover 434 rows and
162,488 actual voters. Their ballot count, eligible-voter count, actual-voter
count, and unique partition are exact, but one residual area in each case shifts
one to three votes from invalid to valid in ArcGIS relative to the official
rows. This evidence class is not applied under the Tier A label.

The K21 count is one row lower than the earlier locality-total estimate because
Umm al-Fahm cannot be reconciled area by area: ArcGIS collapses the locality to
area 1 while existing CBS assignments use areas 11-34. Jerusalem and Nazareth
also fail exact source-total reconciliation. Ambiguous, approximate, and
structurally incompatible cases remain pending. Full evidence is in
`data/processed/audits/arcgis_assignment_reconstruction_*`.

## Data-Closure Order

1. Continue Tier B source review. ArcGIS party sums already reconcile to its
   valid-vote field in all 23 cases; check an alternate official aggregate
   export or service version for the small snapshot differences. Any future
   approval must use a separate Tier B provenance label and rerun full
   reconciliation.
2. Search for comparable official or archived area aggregates for K17-K19 and
   K22-K25. Any row with no defensible evidence remains a published, classified
   coverage gap.
3. Finish the election-by-election audit of the 80 partial-presence locality
   features. Twenty-eight already have at least one supported joined election;
   52 still have no supported join. The 36 never-standalone features already
   have reviewed explanations.
4. Investigate the K17 Maghar discrepancy: the planned polling list includes
   stations 17-20, while the digital result table contains stations 1-16 only.
   Do not synthesize result rows without an official result source.
5. Decide whether acceptable detailed boundaries exist for Rotem, Maskiyot,
   Avnat, and Mavo'ot Yeriho. These marker geometries are a display-quality gap,
   not a result-assignment gap.
6. Complete the 309-row Wikipedia metadata audit and classify every missing
   link as intentional or unresolved. Party/list display names are complete.
7. Complete the map-only party color table and election-specific exceptions,
   then regenerate and validate the public release. Search may proceed in
   parallel; the remaining product sequence is recorded in `FEATURE_PLAN.md`.

## Geometry Caveats

- Every currently assigned statistical-area ID resolves to geometry; the generated assignment summary reports zero missing-geometry rows.
- Historical election-area IDs remain separate. The CBS `Stat08_Unite` and `Stat11_Ref` demographic references are not assignment or display unions.
- Thirty-one canonical historical IDs require documented supplements because
  the downloaded CBS geometry omits them. One comes from an official
  transition-key union and 30 use exact-ID ArcGIS geometry, including the 18
  tribal localities, Hebron, Umm al-Fahm area 1, and seven K21 camp areas.
- Outside those explicit supplements, detailed West Bank footprints from
  ArcGIS are display-only derivatives. They never supply vote totals.
- K17/K18 preserve unsimplified shared boundaries in the display assets and
  clip replacement footprints against historical neighbors. The non-exclusive
  K17 Yehud-Newe Efrayim transition union renders as a marker, eliminating its
  unavoidable polygon overlay.
- The neutral grey land backdrop is visual context only. It does not imply that a historical statistical area or election result exists underneath it.
- K25 intentionally stays on 2011 areas. At least 3,543 direct-crosswalk rows target 2011 areas that split across multiple 2022 areas, so a wholesale conversion would invent precision.

See `HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` for source and matching rules.
