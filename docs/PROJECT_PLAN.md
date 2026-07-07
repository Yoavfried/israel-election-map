# Project Plan

Last updated: 2026-07-07

## Goal

Build a local-first election visualization website for Israeli Knesset elections from 2003 onward. A user should be able to choose an election, switch geography modes, inspect mapped results, and drill into vote distribution details.

Required geography modes:

1. Statistical areas, using 2022 statistical-area polygons.
2. Localities.

This is not a K23-only prototype. K16-K25 are the implementation target.

## Confirmed Data Direction

Official Knesset election data exists in the data.gov.il `votes-knesset` package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Confirmed coverage:

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
| Knesset 16 | 2003 | XLS | Aggregate from ballot rows |

Locality-mode decision:

- Use official locality-level resources for K19-K25.
- Generate locality totals from ballot rows for K16-K18.
- Keep pre-2003 locality availability as an open research item; current product scope starts at K16 / 2003.

## Statistical Areas

Canonical raw polygon source:

- `data/raw/ezorim_statistiim_2022.gdb`
- Layer: `statistical_areas_2022`
- 3,842 polygon features.
- 3,739 unique locality/statistical-area pairs.
- 1,283 represented locality codes.
- 1,139 single-stat locality codes.
- 144 multi-stat locality codes.

Decision:

Use this FileGDB as the canonical 2022 statistical-area source. The previous `data/raw/statistical-areas-2022.geojson` was a partial export and is no longer a project source.

Detailed audit:

- `docs/LOCALITY_STAT_LAYER_AUDIT.md`

For localities that have exactly one `STAT_2022`, locality-level or kalpi-level rows can be assigned directly to that statistical area when no finer address assignment is needed.

Apply this single-stat locality shortcut before geocoding. If a result row's matched 2022 locality has exactly one statistical area, geocoding its polling-place address cannot change the statistical-area assignment.

## Kalpi to Statistical Area

This is an accepted approximation for the product.

The ballot-result rows include vote counts and kalpi identifiers, but no geometry. Polling-place address data plus the single-stat locality shortcut supports a first-pass approximation for K17-K25. K16 remains only partially mappable until a real K16 polling-place address/list source is recovered.

The approximation is:

> assign each kalpi to the statistical area containing the polling-place building, then aggregate votes by statistical area

This does not represent the exact residential statistical area of the voters assigned to that kalpi. The UI should expose mapped coverage and assignment provenance.

## Address Coverage

Detailed findings:

- `docs/POLLING_PLACE_ADDRESSES.md`

Direct address-source summary:

| Election | Year | Address source | Direct poll coverage | Actual voters without direct address |
|---|---:|---|---:|---:|
| K25 | 2022 | Official K25 polling-place XLSX | 93.32% | 462,807 (9.65%) |
| K24 | 2021 | Archived official polling-place XLSX | 93.82% | 425,512 (9.59%) |
| K23 | 2020 | Archived official polling-place XLSX | 95.10% | 330,209 (7.15%) |
| K22 | 2019 Sep | Archived official polling-place XLSX | 96.68% | 282,442 (6.33%) |
| K21 | 2019 Apr | Archived official K21 polling-place XLS | 97.16% | 240,865 (5.55%) |
| K20 | 2015 | Archived official K20 TellThePolls XLS | 97.17% | 234,599 (5.51%) |
| K19 | 2013 | Archived official K19 AllStations PDF | 97.74% | 215,789 (5.63%) |
| K18 | 2009 | Official scanned polling-place PDF extraction | 99.99% | 186,919 (5.47%) |
| K17 | 2006 | Address field in official result file | 98.05% | 179,177 (5.62%) |
| K16 | 2003 | No usable election-specific source | 0.00% | 3,200,773 (100.00%) |

Interpretation:

- K19-K25 and K18 have election-specific address sources covering every ordinary geographic row, except K21 `נורית`, which is still assignable by single-stat locality.
- K17 has 15 ordinary rows with an empty address field. Four are assignable by single-stat locality; 11 have recovered polling-place names from scans and need geocoding/review.
- K16 has no usable polling-place address source yet. Generic-table matches are kept as research-only metadata, not production coverage.

## Reviewed Assignment Coverage

After applying the reviewed locality crosswalk, custom buckets, and the FileGDB-derived single-stat locality shortcut:

| Election | Non-envelope rows without direct address | Assigned by single-stat | Assigned by custom point | Still missing address rows | Still missing actual voters |
|---|---:|---:|---:|---:|---:|
| K25 | 0 | 0 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 | 0 | 0 |
| K21 | 1 | 1 | 0 | 0 | 0 |
| K20 | 0 | 0 | 0 | 0 | 0 |
| K19 | 0 | 0 | 0 | 0 | 0 |
| K18 | 0 | 0 | 0 | 0 | 0 |
| K17 | 15 | 4 | 0 | 11 | 3,603 |
| K16 | 7,737 | 1,209 | 53 | 6,472 | 2,674,963 |

Full coverage artifacts:

- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.csv`
- `docs/ADDRESSLESS_ROWS_AFTER_REVIEWED_ASSIGNMENT.csv`

Implementation decisions:

- Store assignment method for each row: single-stat locality, direct address geocode needed, address-geocode-to-current-polygons, custom point-size polygon, special non-geographic, official envelope, or unresolved.
- Do not silently drop actual votes from rows that cannot be placed on a map.
- Use the reviewed locality resolution plan before deciding whether a row needs address geocoding.
- Expose mapped/unmapped coverage in the UI.

## K23 AGS Field

The K23 polling-place report includes an `אג"ס` field, but it is not compatible enough with the 2022 polygons for direct joining:

- K23 rows with `אג"ס`: 10,631.
- Unique K23 locality+`אג"ס` pairs: 2,701.
- Unique 2022 locality+`STAT_2022` pairs: 3,739.
- Row match rate: 5,379 / 10,631, or 50.60%.
- Unique-pair match rate: 1,053 / 2,701, or 38.99%.

Decision:

Keep K23 `אג"ס` as source metadata only. Use geocoded polling-place addresses plus point-in-polygon for multi-stat localities, and use the single-stat locality shortcut only where the 2022 layer has exactly one statistical area for the locality.

## Geocoding And Assignment Pipeline

1. Load official ballot results for K16-K25.
2. Normalize locality codes, locality names, and kalpi identifiers.
3. Load the 2022 statistical-area FileGDB and generate a web-friendly polygon layer plus locality/stat metadata.
4. Apply the reviewed locality resolution plan for exact matches, aliases, merges, splits, custom buckets, and non-geographic buckets.
5. Assign by locality first when the mapped 2022 locality has exactly one statistical area.
6. Assign reviewed custom point-size polygon rows without geocoding.
7. Keep official envelope and reviewed special non-geographic rows outside geographic polygon assignment.
8. Load election-specific polling-place addresses where available.
9. Keep the generic official polling-place table as research-only fallback metadata unless an election-specific validation step approves it.
10. Geocode polling-place addresses for rows in multi-stat localities and reviewed address-target sets that still need address-level assignment.
11. Run point-in-polygon against the 2022 statistical-area polygons.
12. Join ballot results to assigned statistical areas, custom geographies, or non-geographic buckets.
13. Aggregate per geography and keep per-kalpi/source-row contribution details.
14. Store unresolved rows and their vote totals separately.
15. Persist assignment provenance: source, match rule, geocoder, confidence, and failure reason.

## Locality Crosswalk

Localities can change between elections: names change, codes change, localities split, localities merge, and some localities disappear or are represented differently in later CBS layers.

The pipeline needs a reviewed locality crosswalk rather than relying only on exact string matching.

Current review artifact:

- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.md`
- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.csv`

Current resolution artifact:

- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.md`
- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.csv`

Minimum crosswalk fields:

- election
- source locality code and name from the election result file
- target 2022 locality code and name, when applicable
- mapping status: exact code, exact name, alias, merge, split/address-target-set, custom point bucket, non-geographic, retired, unknown
- whether the target can use the single-stat locality shortcut
- notes/source for the decision

Reviewed split localities and `שער שומרון` are modeled as address-target sets. Their rows should be assigned by polling-place geocoding into the correct current polygon. Do not join current polygons, and do not split votes heuristically.

## Aggregation Model

For each statistical area:

- Sum eligible voters, voters, invalid votes, valid votes, and party votes.
- Store the number of contributing kalpis.
- Store each kalpi contribution for drill-down.
- Keep unresolved rows separately.

For localities:

- Use official locality resources where available.
- Aggregate ballot rows where separate locality resources are unavailable.

## Frontend Direction

Map-first interface:

- Election dropdown for K16-K25.
- Geography switch: Statistical areas / Localities.
- Coloring mode:
  - Winning party
  - Selected party vote share
  - Turnout
  - Margin
- Details panel:
  - Area name/code
  - Vote totals
  - Winning party and margin
  - Party distribution
  - Contributing kalpis
  - Unresolved vote impact where relevant

Candidate stack:

- React or Svelte
- MapLibre GL
- Static local JSON/GeoJSON initially
- PMTiles/vector tiles later if geometry is heavy

## Open Questions

1. Can a usable election-specific polling-place address/list source be recovered for K16?
2. Which geocoder should be used for polling-place addresses, and can we cache/review results legally and reproducibly?
3. What official or reliable locality polygon source should be used?
4. Are pre-2003 locality-level results available from an official archive outside the inspected open-data package?
5. How should party colors be governed across party splits, mergers, renamed lists, and reused letters?
6. How should the UI communicate mapped vote coverage without weakening the map-first experience?
7. How should custom point-size polygon buckets be drawn and explained in the UI?
