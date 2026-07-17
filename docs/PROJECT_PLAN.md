# Project Plan

Last updated: 2026-07-17

## Goal

Build a local-first bilingual map for K17-K25 election results with two usable views:

1. locality results on current locality display geometry, with reviewed election-specific unions;
2. statistical-area results on the historical area vintage used by the official ballot crosswalk for that election.

The map must distinguish geographic results, envelope votes, reviewed custom geographies, and unresolved source gaps without inventing spatial precision.

## Confirmed Direction

- K17 uses 1995 statistical areas.
- K18 uses 2008 statistical areas.
- K19-K25 use 2011 statistical areas because those are the targets of the official CBS crosswalks.
- Future elections use 2022 areas only when an official direct 2022 ballot crosswalk exists.
- Polling-place addresses do not assign voter results. OSM/Photon work is retained for polling-place location and address QA.
- Locality mode continues to aggregate normalized ballot rows, not published locality summary tables.
- Envelope results remain one separate national result per election.

## Implemented

- Official K17-K25 election-result normalization: 96,529 rows.
- Official CBS ballot-to-statistical-area crosswalk recovery for all nine elections.
- Reproducible 1995, 2008, 2011, and 2022 geography builds.
- Stable vintage-specific area IDs preserved exactly from the official ballot crosswalks.
- Detailed display footprints for 157 historical tiny proxies across the three old vintages and 115 current locality proxies.
- Fixed marker behavior for the remaining tiny locality proxies, including multi-point joined results.
- Direct assignment before any geolocation path.
- Statistical voter coverage from 94.13% to 100%, depending on source completeness.
- Complete locality-mode geographic coverage.
- Election-specific geometry selection in the web catalog and browser.
- Historical composite municipalities, reviewed joined-register unions, and envelope display.
- Complete result-column registry and reviewed K17-K25 published party/list display names.
- K17 eligible-voter recovery and turnout.

## Current Data Gaps

- Every election has statistical pending rows where the official ballot crosswalk has no match and the historical locality contains multiple areas; current counts range from 421 in K17 to 958 in K24.
- K25 cannot be honestly converted wholesale to 2022 areas: at least 3,543 direct-crosswalk rows target 2011 areas split across multiple 2022 areas.
- ArcGIS detailed geometry is derivative and is used only with explicit provenance. Its election totals never replace official totals.

## Remaining Product Work

1. Audit the 69 K20-K25 statistical pending rows and classify which are inherently non-spatial versus recoverable from another official table.
2. Investigate whether the K17/K18 omitted localities have a fuller official crosswalk or boundary table.
3. Finish the partial/no-result locality-history audit.
4. Finish party colors and the Hebrew/English Wikipedia-link audit. Party/list names are complete.
5. Continue UX, accessibility, mobile, and bilingual QA.
6. Finish planned features, including search/navigation, coloring modes, and optional ballot-contribution drill-down.
7. Add a visible methodology/provenance surface explaining the election's active statistical vintage.
8. Decide whether and how to expose polling-place building locations as a separate feature.
9. Finish public release hardening: fresh-clone source bootstrap, CI, licensing, performance checks, and release packaging.

## Integrity Rules

- Never infer voter geography from the polling-place building.
- Never split one published secret-ballot aggregate between polygons without a source.
- Never replace official vote totals with ArcGIS derivative totals.
- Never silently drop pending votes; show mode-specific coverage.
- Never convert a historical area to one current area when the transition is one-to-many.
- Keep assignment geometry and display-only geometry provenance separate.

## Release Gates

- `scripts/run_pipeline.py --skip-geographies` succeeds from saved raw sources.
- `npm run check` passes after rebuilding all web assets.
- Every result ID joins to the election-specific geometry asset.
- Mode-specific national totals and party totals reconcile.
- Desktop/mobile and Hebrew/English browser checks pass.
- Public methodology states the active vintage and remaining coverage for each election.
