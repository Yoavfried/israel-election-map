# Project Plan

Last updated: 2026-07-02

## Goal

Build a local-first election visualization website for Israeli Knesset elections. A user should be able to choose an election, switch between geography modes, inspect mapped results, and drill into vote distribution details.

Initial geography modes:

1. Statistical areas
2. Localities

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

## Statistical Areas

Confirmed official national polygon layer:

https://data.gov.il/api/3/action/package_show?id=statistical-area-2008

Dataset title: CBS statistical areas from the 2008 census.

The layer is useful for visualization, but source metadata says it is for statistical publication and is not an authoritative reconstruction of settlement or other legal boundaries.

Decision:

Use this layer initially, but label it clearly as the 2008 CBS statistical-area polygon layer unless a newer official polygon source is confirmed.

## 2022 Statistical Area Data

A 2022 census package exists:

https://data.gov.il/api/3/action/package_show?id=2022

The inspected resources are tabular CSV files. The relevant table includes `LocalityCode`, `StatArea`, and `StatAreaCmb`, but no geometry. If a separate 2022 polygon export is found, prefer GeoJSON for the web prototype and keep Shapefile as an archival backup.

## Kalpi to Statistical Area

This is conditionally feasible, not guaranteed.

The ballot-result rows include vote counts and kalpi identifiers, but no geometry. A separate official polling-place table found on data.gov.il has address-like fields but no coordinates and does not appear to fully cover Knesset 25 by row count.

Feasible pipeline:

1. Obtain election-specific polling-place address or coordinate data.
2. Normalize addresses and kalpi identifiers.
3. Geocode polling places to points.
4. Run point-in-polygon against statistical areas.
5. Join ballot results to assigned statistical areas.
6. Store assignment method, confidence, and source.

Product caveat:

The statistical area containing a polling-place building is not necessarily the residential statistical area of the voters assigned to that kalpi. The UI must distinguish this clearly.

## Aggregation Model

For each statistical area:

- Sum eligible voters, voters, invalid votes, valid votes, and party votes.
- Store the number of contributing kalpis.
- Store each kalpi contribution for drill-down.
- Keep unassigned kalpis separately.

For localities:

- Use official locality resources where available.
- Aggregate ballot rows where separate locality resources are unavailable.

## Frontend Direction

Map-first interface:

- Election dropdown.
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

Candidate stack:

- React or Svelte
- MapLibre GL
- Static local JSON/GeoJSON initially
- PMTiles/vector tiles later if geometry is heavy

## Open Questions

1. Is there a newer official nationwide statistical-area polygon layer than the 2008 layer?
2. Can we obtain election-specific polling-place addresses or coordinates for K25 and earlier elections?
3. Which geocoder should be used for polling-place addresses?
4. Should statistical-area mode represent polling-place geography, voter-residence geography, or both where possible?
5. What official or reliable locality polygon source should be used?
6. Are pre-2003 locality-level results available from an official archive outside the inspected open-data package?
7. How should party colors be governed across party splits, mergers, renamed lists, and reused letters?

