# Project Plan

Last updated: 2026-07-15

## Goal

Build a local-first election visualization website for Israeli Knesset elections from 2006 onward. A user should be able to choose an election, switch geography modes, inspect mapped results, and drill into vote distribution details.

Required geography modes:

1. Statistical areas, using 2022 statistical-area polygons.
2. Localities.

The current implementation target is K17-K25. K16 / 2003 is out of current scope until a usable election-specific polling-place address source is recovered.

## Confirmed Data Direction

Official Knesset election data exists in the data.gov.il `votes-knesset` package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Confirmed current-scope coverage:

| Election | Year | Ballot-level results | Locality-level results |
|---|---:|---|---|
| Knesset 25 | 2022 | CSV | CSV |
| Knesset 24 | 2021 | CSV | CSV |
| Knesset 23 | 2020 | CSV | CSV |
| Knesset 22 | 2019 Sep | CSV | CSV |
| Knesset 21 | 2019 Apr | CSV | CSV |
| Knesset 20 | 2015 | CSV | CSV |
| Knesset 19 | 2013 | CSV | CSV |
| Knesset 18 | 2009 | CSV | Aggregate from ballot rows |
| Knesset 17 | 2006 | XLS | Aggregate from ballot rows, with name-normalization caveats |

Locality-mode decision:

- Do not use official locality-level aggregates as product input.
- Build locality totals from the same row-level pipeline used for statistical areas: ballot row -> address/place source -> coordinate or reviewed shortcut -> 2022 statistical area -> dissolved 2022 locality.
- Keep official locality-level resources as QA/reference metadata only.
- Keep K16 and pre-2003 locality availability as later research items; current product scope starts at K17 / 2006.

## Statistical Areas

Canonical raw polygon source:

- `data/raw/ezorim_statistiim_2022.gdb`
- Layer: `statistical_areas_2022`
- 3,857 polygon features in the current raw FileGDB.
- 1,329 dissolved locality features.
- 1,184 dissolved localities have exactly one statistical-area feature.
- 145 dissolved localities have multiple statistical-area features.

Decision:

Use this FileGDB as the canonical 2022 statistical-area source. The previous `data/raw/statistical-areas-2022.geojson` was a partial export and is no longer a project source.

Locality geometry decision:

- Derive locality geometries by dissolving/unioning the 2022 statistical-area polygons by 2022 locality code/name.
- In locality mode, internal statistical-area boundaries must not be visible; the dissolved locality should render as one visual polygon or multipolygon.
- Do not introduce a separate official locality polygon layer for the current implementation unless later QA shows the dissolved 2022 statistical-area layer is insufficient.

Detailed audit:

- `docs/LOCALITY_STAT_LAYER_AUDIT.md`

For localities that have exactly one `STAT_2022`, locality-level or kalpi-level rows can be assigned directly to that statistical area when no finer address assignment is needed.

Apply this single-stat locality shortcut before geocoding. If a result row's matched 2022 locality has exactly one statistical area, geocoding its polling-place address cannot change the statistical-area assignment.

## Kalpi to Statistical Area

This is an accepted approximation for the product.

The ballot-result rows include vote counts and kalpi identifiers, but no geometry. Polling-place address data plus the single-stat locality shortcut supports a first-pass approximation for K17-K25.

The approximation is:

> assign each kalpi to the statistical area containing the polling-place building, then aggregate votes by statistical area

This does not represent the exact residential statistical area of the voters assigned to that kalpi. The UI should expose mapped coverage and assignment provenance.

## Synthetic Geographies

Some reviewed source rows are real geographic concepts but do not map cleanly to a 2022 locality/statistical-area polygon in the current layer. They should be represented as explicit synthetic point-size geometries, visible only for relevant elections:

| Bucket | Geometry direction |
|---|---|
| `TRIBE` | Small synthetic polygon/point-size marker in the north Negev |
| `HEBRON` | Small synthetic polygon/point-size marker in central Hebron |
| `N.S.` | Small synthetic polygon/point-size marker in north Samaria |
| `GAZA` | Small synthetic polygon/point-size marker in the Gaza Strip |

Implementation rules:

- Preserve source-row contributions and assignment provenance.
- Do not merge these rows into normal 2022 statistical-area or locality polygons.
- Tune the visual design later so these buckets are visible without pretending to be precise borders.

## Address Coverage

Detailed findings:

- `docs/POLLING_PLACE_ADDRESSES.md`

Current geocoding-input readiness:

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

Interpretation:

- K22-K25 and K20-K21 have ready address strings for rows that need geocoding.
- K19 and K18 have a small number of place-only rows that need manual/reviewed geocoding.
- K17 has 456 place-only rows recovered directly from the scanned polling-place lists, including all 344 rows formerly described as locality-only/no-place.
- K16 has no usable polling-place address source and is deferred from current scope.

## Reviewed Assignment Coverage

After applying the reviewed locality crosswalk, custom buckets, and the FileGDB-derived single-stat locality shortcut, every K17-K25 row has a handling rule. Before geocoding, only single-stat rows and custom geographies are mapped:

| Election | Mapped rows now | Mapped actual voters now | Pending/missing geocode rows | Pending/missing geocode actual voters |
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

Full coverage artifacts:

- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/DATA_PIPELINE.md`
- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.csv`
- `docs/ADDRESSLESS_ROWS_AFTER_REVIEWED_ASSIGNMENT.csv`

Implementation decisions:

- Store assignment method for each row: single-stat locality, direct address geocode needed, address-geocode-to-current-polygons, custom point-size polygon, special non-geographic, official envelope, or unresolved.
- Do not silently drop actual votes from rows that cannot be placed on a map.
- Use the reviewed locality resolution plan before deciding whether a row needs address geocoding.
- Expose mapped/unmapped coverage in the UI.

## K23 AGS Field

The K23 polling-place report includes an AGS/statistical-area-like field, but it is not compatible enough with the 2022 polygons for direct joining:

- K23 total polling-place report rows: 10,631.
- K23 rows with non-empty AGS: 8,031.
- Unique K23 locality+AGS pairs with non-empty AGS: 1,570.
- The current FileGDB build has 3,857 unique `YISHUV_STAT_2022` / `stat_area_id` features.
- Earlier direct compatibility checks against 2022 polygons were weak enough that K23 AGS should not be joined directly to the 2022 layer.
- K23 `locality + concentration` is not a substitute for AGS: among AGS-bearing rows, 741 `locality + concentration` pairs map to more than one AGS.

Decision:

Keep K23 AGS as source metadata only. Use geocoded polling-place addresses plus point-in-polygon for multi-stat localities, and use the single-stat locality shortcut only where the 2022 layer has exactly one statistical area for the locality.

## Historical AGS QA

Historical/source AGS validation is a diagnostic QA layer for geocoded candidates where source AGS metadata exists. The original goal was to test whether a candidate coordinate falls inside the official historical statistical-area polygon named by the source row, but K23 shows that source AGS can describe the ballot row/voter assignment rather than the polling-place building itself.

Current finding: the local K23 polling-place report has explicit AGS metadata; inspected K17-K22/K24-K25 local sources do not yet expose equivalent AGS fields. The 2008 CBS statistical-area package exists on data.gov.il, but the actual archive still needs to be downloaded outside the command-line browser challenge.

Do not use source AGS as a hard accept/reject gate. Keep `outside_expected_locality` as blocked-from-auto-accept, and keep source-AGS mismatches as manual-review diagnostics. See `docs/AGS_HISTORICAL_QA.md`.

## Geocoding And Assignment Pipeline

1. Load official ballot results for K17-K25.
2. Normalize locality codes, locality names, and kalpi identifiers.
3. Load the 2022 statistical-area FileGDB and generate a web-friendly polygon layer plus locality/stat metadata.
4. Apply the reviewed locality resolution plan for exact matches, aliases, merges, splits, custom buckets, and non-geographic buckets.
5. Assign by locality first when the mapped 2022 locality has exactly one statistical area.
6. Assign reviewed custom point-size polygon rows without geocoding.
7. Keep official envelope and reviewed special non-geographic rows outside geographic polygon assignment.
8. Load election-specific polling-place addresses where available.
9. Geocode polling-place addresses for rows in multi-stat localities and reviewed address-target sets that still need address-level assignment.
10. Run point-in-polygon against the 2022 statistical-area polygons.
11. Join ballot results to assigned statistical areas, custom geographies, or non-geographic buckets.
12. Aggregate per geography and keep per-kalpi/source-row contribution details.
13. Store unresolved rows and their vote totals separately.
14. Persist assignment provenance: source, match rule, geocoder, confidence, and failure reason.

Geocoding provider decision status:

- GovMap remains the preferred official Israeli candidate, but approval/token behavior, rate limits, coordinate fields, and caching/publication terms still need live verification.
- ArcGIS is a paid/stored-geocoding fallback only if a token/API key with the right storage privileges is available.
- A source-fidelity and usability audit runs before geographic matching. It verifies all 93,991 normalized address-source rows against available evidence, excludes malformed/non-address inputs from the clean exact-address scope, and keeps PDF/OCR-only cases in a finite 450-unit visual-review queue.
- OSM geometry from the local Geofabrik PBF is the first address-placement layer. After canonical physical-address deduplication, the numbered-address scope contains 4,210 addresses. A strict 25 m street corridor or exact OSM house number assigns 1,346 canonical addresses; nine reviewed OSM/component-locality exceptions bring the OSM-first resolved total to 1,355. At strict query-lineage grain this is 1,922 units, 24,211 source rows, and 9,463,605 actual voters. Exact matching accepts `addr:street` or `addr:place` with `addr:housenumber`, and exact scalar numbers outrank matching multi-value tags. These candidates are not yet promoted into the final assignment stage.
- Photon is a free self-hosted fallback for unresolved OSM cases. A full local run exists, but it is not trusted blindly; candidate coordinates must pass locality-polygon validation before promotion. Source/historical AGS QA is supplemental diagnostic context only because one polling-place address can serve multiple source AGS values, and even single-source-AGS cases do not prove the building lies in that AGS.
- Do not use Google as the primary geocoder for public downloadable coordinates unless its storage and redistribution constraints are explicitly cleared.
- Do not use public Nominatim for bulk geocoding. The only open-data path currently considered is self-hosted Nominatim/Photon.

## Locality Crosswalk

Localities can change between elections: names change, codes change, localities split, localities merge, and some localities disappear or are represented differently in later CBS layers.

The pipeline needs a reviewed locality crosswalk rather than relying only on exact string matching.

Current review artifact:

- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.md`
- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.csv`

Current resolution artifact:

- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.md`
- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.csv`

Scope note: the crosswalk review files may still retain K16-only rows from the earlier investigation. Current product loaders should filter source elections to K17-K25.

Minimum crosswalk fields:

- election
- source locality code and name from the election result file
- target 2022 locality code and name, when applicable
- mapping status: exact code, exact name, alias, merge, split/address-target-set, custom point bucket, non-geographic, retired, unknown
- whether the target can use the single-stat locality shortcut
- notes/source for the decision

Reviewed split localities and Sha'ar Shomron are modeled as address-target sets. Their rows should be assigned by polling-place geocoding into the correct current polygon. Do not join current polygons, and do not split votes heuristically.

## Aggregation Model

For each statistical area:

- Sum eligible voters, voters, invalid votes, valid votes, and party votes.
- Store the number of contributing kalpis.
- Store each kalpi contribution for drill-down.
- Keep unresolved rows separately.

For localities:

- Aggregate statistical-area results into 2022 locality results.
- Preserve the contributing statistical areas and source ballot rows for drill-down.
- Keep official locality resources as QA/reference metadata, not as product totals.

## Frontend Direction

Implemented map-first foundation under `web/app/`:

- Election dropdown for K17-K25.
- Geography switch: Statistical areas / Localities.
- Winning-party map coloring with unmapped polygons kept visible.
- Area details with totals, winner/margin, party distribution, and contributing kalpis.
- English/Hebrew switching with document-level LTR/RTL.
- Explicit mapped/pending voter coverage for every election.
- Build-time CSV/GeoJSON compiler with Zod-validated browser assets.

Implemented stack:

- React, TypeScript, and Vite.
- MapLibre GL.
- Static local JSON/GeoJSON generated from `data/processed/`.
- PMTiles/vector tiles later if production transfer or mobile parsing requires them.

Still planned: selected-party share, turnout, and margin coloring; searchable geography navigation; contribution drill-down; reviewed cross-election party names/colors; and browser accessibility/performance release gates. See `web/app/docs/ARCHITECTURE.md`.

## Open Questions

1. Should K16 be added later if a usable election-specific polling-place address/list source is recovered?
2. Which geocoder should be used for polling-place addresses, and can we cache/review results legally and reproducibly?
3. Are pre-2003 locality-level results available from an official archive outside the inspected open-data package?
4. How should party colors be governed across party splits, mergers, renamed lists, and reused letters?
5. How should the UI communicate mapped vote coverage without weakening the map-first experience?
6. How should custom point-size polygon buckets be drawn and explained in the UI?
