# Project Plan

Last updated: 2026-07-05

## Goal

Build a local-first election visualization website for Israeli Knesset elections from 2003 onward. A user should be able to choose an election, switch between geography modes, inspect mapped results, and drill into vote distribution details.

Required geography modes:

1. Statistical areas, using the local 2022 statistical-area polygons.
2. Localities.

This is not a K23-only prototype. K16-K25 are the implementation target.

## Data Findings

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

Current locality-mode decision:

- Use official locality-level resources for K19-K25.
- Generate locality totals from ballot rows for K16-K18.
- Keep pre-2003 locality availability as an open research item; the current product scope starts at K16 / 2003.

## Statistical Areas

Current project raw layer:

- `data/raw/statistical-areas-2022.geojson`
- 1,776 features.
- Useful properties observed: `SEMEL_YISHUV`, `STAT_2022`, `YISHUV_STAT_2022`.
- 407 localities appear in the layer.
- 364 localities have exactly one 2022 statistical area.
- 43 localities have multiple 2022 statistical areas.

Decision:

Use the local 2022 statistical-area GeoJSON as the first statistical-area geometry layer. The UI and metadata should identify it explicitly as the 2022 statistical-area layer.

For localities that have exactly one `STAT_2022`, locality-level results can be assigned directly to that statistical area when kalpi-level address assignment is unavailable.

Older official national polygon layer:

https://data.gov.il/api/3/action/package_show?id=statistical-area-2008

The 2008 layer remains useful as a fallback/reference layer, but it should not replace the 2022 layer unless the 2022 geometry proves unusable.

## Kalpi to Statistical Area

This is an accepted approximation for the product.

The ballot-result rows include vote counts and kalpi identifiers, but no geometry. Polling-place address data plus the single-stat locality shortcut is good enough to support a first-pass approximation for every election from K16 through K25, with different confidence levels by election.

The approximation is:

> assign each kalpi to the statistical area containing the polling-place building, then aggregate votes by that statistical area.

For a locality with exactly one 2022 statistical area, a result row can be assigned by locality without geocoding the kalpi address.

This does not represent the exact residential statistical area of the voters assigned to that kalpi, but it should create an interesting and usable exploratory map if caveats are visible.

### Direct Address Coverage

Detailed findings are documented in:

- `docs/POLLING_PLACE_ADDRESSES.md`

Direct address-source summary:

| Election | Year | Address source | Direct poll coverage | Actual voters without direct address |
|---|---:|---|---:|---:|
| K25 | 2022 | Official K25 polling-place XLSX | 93.32% | 462,807 (9.65%) |
| K24 | 2021 | Archived official polling-place XLSX | 93.82% | 425,512 (9.59%) |
| K23 | 2020 | Archived official polling-place XLSX | 95.10% | 330,209 (7.15%) |
| K22 | 2019 Sep | Archived official polling-place XLSX | 96.68% | 282,442 (6.33%) |
| K21 | 2019 Apr | Generic official polling-place table | 90.09% | 567,589 (13.08%) |
| K20 | 2015 | Generic official polling-place table | 94.14% | 362,617 (8.52%) |
| K19 | 2013 | Generic official polling-place table | 96.42% | 260,957 (6.81%) |
| K18 | 2009 | Generic official polling-place table | 99.60% | 201,065 (5.88%) |
| K17 | 2006 | Address field in official result file | 98.05% | 179,177 (5.62%) |
| K16 | 2003 | Generic official polling-place table | 97.31% | 182,385 (5.70%) |

For K22-K25, every ordinary row has a direct address match; only envelope rows lack direct addresses. K17 has 15 ordinary rows with an empty address field. K16 and K18-K21 use generic-table fallback matching and remain lower confidence until election-specific address files are recovered.

### Meaningful Ordinary Unresolved Rows

After applying the single-stat locality shortcut and excluding envelope rows, the ordinary unresolved set is:

| Election | Ordinary rows without direct address | Assignable by single-stat locality | Still unresolved rows | Still unresolved actual voters |
|---|---:|---:|---:|---:|
| K25 | 0 | 0 | 0 | 0 |
| K24 | 0 | 0 | 0 | 0 |
| K23 | 0 | 0 | 0 | 0 |
| K22 | 0 | 0 | 0 | 0 |
| K21 | 762 | 40 | 722 | 310,426 |
| K20 | 317 | 15 | 302 | 125,431 |
| K19 | 136 | 3 | 133 | 46,320 |
| K18 | 36 | 0 | 36 | 14,146 |
| K17 | 15 | 1 | 14 | 4,465 |
| K16 | 63 | 1 | 62 | 23,549 |

Implementation decision:

- Store assignment method for each row: direct address, single-stat locality, unresolved, or excluded envelope bucket.
- Do not silently drop actual votes from rows that cannot be placed on a map.
- Add an explicit locality-alias table before using historical aliases such as `בית אריה` to `בית אריה-עופרים`.

### K23 AGS Field

The K23 polling-place report includes an AGS-like field, but it is not compatible enough with the local 2022 statistical-area polygons:

- K23 unique locality+AGS pairs: 1,570.
- Matching pairs in the 2022 polygon layer: 589.
- Unique-pair match rate: 37.5%.

Decision:

Do not join K23 AGS directly to 2022 polygons. Use geocoded polling-place addresses plus point-in-polygon for direct-address rows, and use the single-stat locality shortcut only where the 2022 layer has exactly one statistical area for the locality.

## Geocoding And Assignment Pipeline

1. Load official ballot results for K16-K25 from datastore/file resources.
2. Load election-specific polling-place addresses where available.
3. Fall back to the generic official polling-place table only where no election-specific table has been found.
4. Normalize locality codes and kalpi identifiers.
5. Geocode polling-place addresses to point coordinates.
6. Run point-in-polygon against the 2022 statistical-area GeoJSON.
7. For rows without direct address assignment, assign by locality only when the locality has exactly one 2022 statistical area.
8. Join ballot results to assigned statistical areas.
9. Aggregate per statistical area and keep per-kalpi contribution details.
10. Store unresolved rows and their vote totals separately.
11. Persist assignment provenance: source, match rule, geocoder, confidence, and failure reason.

## Aggregation Model

For each statistical area:

- Sum eligible voters, voters, invalid votes, valid votes, and party votes.
- Store the number of contributing kalpis.
- Store each kalpi contribution for drill-down.
- Keep unresolved kalpis and envelope rows separately.

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

1. Can usable election-specific polling-place address files be recovered for K16 and K18-K21?
2. Which geocoder should be used for polling-place addresses, and can we cache/review results legally and reproducibly?
3. What official or reliable locality polygon source should be used?
4. Are pre-2003 locality-level results available from an official archive outside the inspected open-data package?
5. How should party colors be governed across party splits, mergers, renamed lists, and reused letters?
6. How should the UI communicate mapped vote coverage without weakening the map-first experience?
7. Which historical locality aliases should be accepted, such as `בית אריה` to `בית אריה-עופרים`?
