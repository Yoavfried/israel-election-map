# Historical Statistical-Area Assignment

Last updated: 2026-07-17

## Decision

Statistical-area election results are assigned from election-specific CBS ballot crosswalks, not from polling-place addresses.

A polling-place address locates the building where voting occurred. It does not identify the residential statistical areas of the voters served by that building. The official CBS crosswalk is the relevant source because it directly associates a ballot number with the statistical area represented by that ballot row.

Assignment precedence is:

1. official envelope or reviewed non-geographic handling;
2. official election-specific ballot-to-statistical-area crosswalk;
3. the election-vintage locality when that locality has exactly one published statistical area;
4. reviewed custom geography where no supported historical statistical area exists;
5. unresolved, with no address-based fallback.

Polling-place geolocation remains in the repository for address search, facility maps, and QA. It does not assign election votes to statistical areas.

## Election Vintages

| Election | Year | Statistical-area vintage | Official crosswalk |
|---|---:|---:|---|
| K17 | 2006 | 1995 | `Kalpi2006_stat1995.xls` |
| K18 | 2009 | 2008 | `kalpi2008_stat2008.xlsx` |
| K19 | 2013 | 2011 | `kalpi2013_stat2011.xlsx` |
| K20 | 2015 | 2011 | `kalpi2015_stat2011.xlsx` |
| K21 | Apr 2019 | 2011 | `kalpi_April2019_stat2011.xlsx` |
| K22 | Sep 2019 | 2011 | `kalpi_September2019_stat2011.xlsx` |
| K23 | 2020 | 2011 | `kalpi_March2020_stat2011.xlsx` |
| K24 | 2021 | 2011 | `kalpi_March2021_stat2011.xlsx` |
| K25 | 2022 | 2011 | `kalpi_November2022_stat2011.xlsx` |

K25 deliberately uses 2011 areas. The official November 2022 table targets 2011, not 2022. The CBS 2011-to-2022 transition table gives a single deterministic 2022 target for 7,217 of 10,761 K25 crosswalk rows; at least 3,543 rows point to 2011 areas split across multiple 2022 areas. Assigning those rows to one 2022 polygon would invent precision. A future election should use 2022 areas only when a direct official 2022 crosswalk exists.

## Source Recovery

`scripts/fetch_cbs_historical_geography.py` enumerates the public CBS GIS catalog, downloads the nine crosswalks, three geometry vintages, and transition tables, verifies file size and file signatures, and writes a SHA-256 manifest under `data/raw/cbs_historical_geography/`.

The CBS GIS catalog documents the historical ballot products, including ballot-to-1995 areas for 2006, ballot-to-2008 areas for 2009, and ballot-to-2011 areas for later elections. The K20 readme explicitly defines the locality, ballot, statistical-area, and combined locality-area fields.

## Geometry Provenance

`scripts/build_historical_geographies.py` builds canonical assignment geometry and separate display geometry.

| Vintage | Assignment features | Display replacements |
|---:|---:|---:|
| 1995 | 2,660 | 113 |
| 2008 | 3,030 | 102 |
| 2011 | 3,105 | 118 |

The canonical geometry is official CBS geometry except for 23 explicit supplements:

- `stat1995:9400008` is the union defined by the official CBS 1995-to-2008 transition key for Yehud-Newe Efrayim.
- Twenty-two 2011 areas are absent from the downloaded CBS GDB and use exact-ID geometry from the supplied 2015 ArcGIS layer. Three are the previously crosswalk-backed `stat2011:9860001`, `stat2011:36370001`, and `stat2011:37970001`; the other 19 are one-area records for 18 reviewed tribal localities plus Hebron.

The 19 tribe/Hebron supplements are eligible for the one-area fallback only in K19-K25, whose active vintage is 2011. The independent K20 ArcGIS table reproduces the official ballot count, eligible voters, actual voters, valid votes, and invalid votes exactly for all 19 localities. The K21 layer contains all 18 tribal localities but not Hebron; its ballot, eligible-voter, and actual-voter totals agree, while three localities shift one vote between valid and invalid. Election votes always come from the normalized official election source, never from ArcGIS. K17/K18 retain the reviewed tribe and Hebron markers because neither their official crosswalks nor the 1995/2008 CBS geometry supplies a defensible historical area.

For display only, schematic West Bank proxy shapes are replaced by detailed settlement footprints from the supplied ArcGIS election layers when the locality has exactly one statistical area, the candidate has a non-schematic boundary, and the candidate polygon is spatially consistent. Apart from the 22 explicit exact-ID geometry supplements above, assignment IDs do not come from ArcGIS. The ArcGIS service itself warns that its election data are not official and that some polygons are schematic.

This replacement now covers 113 shapes in the 1995 layer and 102 in the 2008 layer. All ordinary K17/K18 West Bank markers that have results therefore render as detailed polygons. The remaining ten 1995 and three 2008 ordinary settlement markers have no result in those elections and no usable detailed candidate; the result-bearing tribe and Hebron custom buckets remain markers for the provenance reason above.

The same display-only rule replaces 115 tiny proxies in current 2022 locality geometry. Rotem, Maskiyot, Avnat, and Mavo'ot Yeriho have no usable detailed footprint in either supplied ArcGIS layer and remain fixed-size markers. Sha'ar Shomron now renders as the union of its two detailed component polygons. The active K25 Yitav/Mavo'ot result remains one result with two marker points so the unresolved Mavo'ot proxy is not hidden inside a mixed polygon.

## Matching Rules

- K17 stores ballot numbers in tenths: `10` means ballot 1; `61` and `62` are subdivisions of base ballot 6.
- Later sources use decimal subdivisions such as `1.1` and `1.2`. If the CBS table maps base ballot 1, its result subdivisions inherit that same target.
- The combined target area ID in a crosswalk is authoritative even when it crosses the result row's locality boundary.
- Each ballot crosswalk's statistical-area ID is preserved exactly. The CBS `Stat08_Unite` and `Stat11_Ref` demographic reference fields are not election-area union instructions. In particular, Ma'ale Adumim areas 1, 2, and 3 remain separate wherever the official crosswalk reports them separately.
- A locality-only fallback is allowed only when that historical locality has exactly one canonical statistical area.
- Missing crosswalk rows remain unresolved. They never fall through to OSM, Photon, or another building geocoder.

## Current Coverage

Coverage below is the share of actual voters in the geographic scope after adding reviewed custom geographies. Envelope and reviewed non-geographic rows are outside the denominator.

| Election | Statistical-area vintage | Mapped rows | Pending rows | Mapped voter share |
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

Every pending row lacks a matching official ballot-crosswalk row and belongs to a locality with more than one historical statistical area. Earlier near-complete K19-K25 figures were invalid: they treated the CBS demographic reference fields as area unions, which made many multi-area localities look like single-area localities and triggered an unjustified fallback. Restoring the distinct source areas returned those rows to pending.

Ma'ale Adumim is the regression case that exposed the problem. Areas 1, 2, and 3 are now separate in both 2008 and 2011 geometry. The rebuilt K20 and K21 ballot counts for all ten Ma'ale Adumim areas match the independent 2015 and April 2019 ArcGIS election layers exactly; those layers are validation evidence only, not the source of published totals.

These rows cannot be repaired from polling-place coordinates because the building is not the voters' residential statistical area. Every pending row is preserved in `unresolved_statistical_area_assignment_rows.csv`.

The geometry join itself has no current missing-ID gap: every mapped target resolves to geometry. The remaining geometry caveats concern provenance and display quality, including 23 documented historical supplements and derivative ArcGIS West Bank display footprints.

## Generated Outputs

- `data/processed/geographies/statistical_areas_<vintage>.geojson`
- `data/processed/geographies/statistical_areas_<vintage>.display.simplified.geojson`
- `data/processed/geographies/statistical_areas_<vintage>.metadata.csv`
- `data/processed/geographies/statistical_areas_<vintage>.aliases.csv`
- `data/processed/assignments/historical_ballot_crosswalk.csv`
- `data/processed/assignments/historical_ballot_assignments.csv`
- `data/processed/assignments/historical_ballot_assignment_summary.csv`
- `data/processed/assignments/unresolved_statistical_area_assignment_rows.csv`

The browser catalog is schema version 3. Each election declares `statisticalAreaVintage` and election-specific `geographiesByMode`; switching elections can therefore switch geometry without changing the result contract.
