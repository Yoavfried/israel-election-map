# Historical Statistical-Area Assignment

Last updated: 2026-07-17

## Decision

Statistical-area election results are assigned from election-specific CBS
ballot crosswalks. These tables directly associate ballot identifiers with the
statistical areas represented by the result rows.

Assignment precedence is:

1. official envelope or reviewed non-geographic handling;
2. official election-specific ballot-to-statistical-area crosswalk;
3. reviewed, uniquely reconstructed ballot-to-area assignment from an
   election-specific aggregate source;
4. the election-vintage locality when that locality has exactly one published statistical area;
5. reviewed custom geography where no supported historical statistical area exists;
6. unresolved.

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

### ArcGIS Aggregate Reconstruction

The downloaded 2015 and April 2019 ArcGIS layers contain one aggregate per 2011
statistical area. They are derivative and must not replace official election
totals, but exact aggregate reconciliation may identify ballot groupings omitted
from the CBS crosswalks.

The automated audit is implemented in
`scripts/audit_arcgis_assignment_reconstruction.py`. It found unique exact
candidates for 33 of 37 K20 pending localities, covering 585 rows and 262,038
actual voters. It found unique exact candidates for 34 of 37 K21 pending
localities, covering 600 rows and 225,827 actual voters.

K21 Umm al-Fahm is deliberately rejected even though the locality totals agree:
the ArcGIS layer collapses the locality into area 1 while existing CBS
assignments use areas 11-34, so assigned rows cannot be subtracted from matching
targets. Jerusalem and Nazareth fail exact source-total reconciliation.

Review should happen at the locality-election level, not by reading 1,185 rows
one at a time. The 67 unique-exact cases divide into two evidence tiers:

| Evidence tier | Locality-election cases | Candidate rows | Actual voters |
|---|---:|---:|---:|
| A: every residual area's ballot count, eligible, actual, valid, and invalid totals reconcile | 44 | 751 | 325,377 |
| B: ballot count, eligible, and actual reconcile; one residual area has a small valid/invalid shift | 23 | 434 | 162,488 |

Tier A is approved and active: 32 K20 locality-election decisions assign 573
rows representing 257,667 actual voters, and 12 K21 decisions assign 178 rows
representing 67,710 actual voters. Tier B remains review-only.

The assignment relationship is inferred, not the election result. Every ballot
row, eligible-voter value, vote count, and party vector still comes from the
official normalized election source. Public ballot rows identify the inferred
linkage with
`final_assignment_method=arcgis_residual_partition_tier_a` and retain both the
ArcGIS source and reviewed decision-table path in `final_assignment_source`.
The 44 decisions are published as
`public-data/v1/metadata/arcgis_reconstruction_reviews.csv`. Each decision pins
the exact row-to-area mapping with a SHA-256 fingerprint in addition to its row
and voter totals.

For example, the K21 source had three previously pending rows in ערערה-בנגב:

| Ballot | Eligible | Actual | Valid | Invalid | Candidate area |
|---:|---:|---:|---:|---:|---|
| 9 | 686 | 424 | 424 | 0 | `stat2011:11920001` |
| 10 | 718 | 265 | 264 | 1 | `stat2011:11920001` |
| 11 | 629 | 276 | 272 | 4 | `stat2011:11920001` |
| **Combined** | **2,033** | **965** | **960** | **5** | area 1 |

After the ballots already assigned by the official CBS crosswalk are subtracted
from the ArcGIS locality areas, area 1 has exactly this residual and no other
partition exists. This is a first-tier case because valid and invalid votes also
reconcile for the target area, so these rows are now mapped. By contrast, K21
Jerusalem is rejected before partitioning: ballot count and eligibility agree,
but ArcGIS has 262,100 actual voters while the official rows have 262,103. Umm
al-Fahm is rejected structurally because the ArcGIS area IDs do not correspond
to the CBS areas already assigned there.

The experiment must:

1. subtract official-crosswalk-assigned rows from each ArcGIS area aggregate;
2. partition remaining official ballot rows against residual eligible-voter,
   actual-voter, and ballot-count targets;
3. accept only a unique exact partition and leave ambiguous or approximate
   cases pending;
4. preserve party votes from the official normalized ballot rows;
5. record candidate provenance, source fields, and uniqueness evidence in a
   reviewed decision table;
6. rerun national, locality, party, and geometry-join reconciliation before a
   candidate becomes production data.

For Tier B, all 23 unique core partitions differ in only one residual area. The
ArcGIS valid count is one to three votes higher than the official rows and its
invalid count is lower by the same amount, while ballot count, eligible voters,
and actual voters remain exact. ArcGIS party fields sum exactly to its own valid
total in all 23 cases, so the discrepancy is internally consistent with that
source and is most likely a derivative-snapshot classification difference. The
next review should look for an alternate official aggregate export or service
version. If Tier B is later accepted, it must use a separate method such as
`arcgis_residual_partition_tier_b_snapshot_delta`; it must not silently inherit
Tier A provenance. ArcGIS party vectors are never copied into the project.

For K17-K19 and K22-K25, source recovery should search alternate CBS exports,
archived GIS catalogs, official election maps or statistical publications, and
reconcilable archived FeatureServer layers before requesting omitted records
from CBS or the State Archives. An assignment must never be transferred from a
different election merely because a ballot number appears stable.

## Geometry Provenance

`scripts/build_historical_geographies.py` builds canonical assignment geometry and separate display geometry.

| Vintage | Assignment features | Display replacements |
|---:|---:|---:|
| 1995 | 2,660 | 113 |
| 2008 | 3,030 | 102 |
| 2011 | 3,113 | 117 |

The canonical geometry is official CBS geometry except for 31 explicit supplements:

- `stat1995:9400008` is the union defined by the official CBS 1995-to-2008 transition key for Yehud-Newe Efrayim.
- Thirty 2011 areas are absent from the downloaded CBS GDB and use exact-ID
  geometry from the supplied ArcGIS layers. The original 22 include three
  crosswalk-backed records and 19 one-area records for 18 reviewed tribal
  localities plus Hebron. Eight additional targets support the aggregate audit:
  Umm al-Fahm area 1 and seven K21 camp areas.

The 19 tribe/Hebron supplements are eligible for the one-area fallback only in K19-K25, whose active vintage is 2011. The independent K20 ArcGIS table reproduces the official ballot count, eligible voters, actual voters, valid votes, and invalid votes exactly for all 19 localities. The K21 layer contains all 18 tribal localities but not Hebron; its ballot, eligible-voter, and actual-voter totals agree, while three localities shift one vote between valid and invalid. Election votes always come from the normalized official election source, never from ArcGIS. K17/K18 retain the reviewed tribe and Hebron markers because neither their official crosswalks nor the 1995/2008 CBS geometry supplies a defensible historical area.

For display only, schematic West Bank proxy shapes are replaced by detailed settlement footprints from the supplied ArcGIS election layers when the locality has exactly one statistical area, the candidate has a non-schematic boundary, and the candidate polygon is spatially consistent. Apart from the 30 explicit exact-ID geometry supplements above, ArcGIS does not replace canonical geometry. Its aggregates additionally support the explicitly labeled Tier A inferred assignments described above. The ArcGIS service itself warns that its election data are not official and that some polygons are schematic.

This replacement now covers 113 shapes in the 1995 layer and 102 in the 2008
layer. Replacement footprints are clipped against historical neighbors, and
the 1995/2008 display files preserve unsimplified shared boundaries so adjacent
areas do not paint over one another. `stat1995:9400008` is a non-exclusive
transition union and therefore renders as a marker instead of covering its
component polygons.

The same display-only rule replaces 115 tiny proxies in current 2022 locality geometry. Rotem, Maskiyot, Avnat, and Mavo'ot Yeriho have no usable detailed footprint in either supplied ArcGIS layer and remain fixed-size markers. Sha'ar Shomron now renders as the union of its two detailed component polygons. The active K25 Yitav/Mavo'ot result remains one result with two marker points so the unresolved Mavo'ot proxy is not hidden inside a mixed polygon.

## Matching Rules

- K17 stores ballot numbers in tenths: `10` means ballot 1; `61` and `62` are subdivisions of base ballot 6.
- Later sources use decimal subdivisions such as `1.1` and `1.2`. If the CBS table maps base ballot 1, its result subdivisions inherit that same target.
- The combined target area ID in a crosswalk is authoritative even when it crosses the result row's locality boundary.
- Each ballot crosswalk's statistical-area ID is preserved exactly. The CBS `Stat08_Unite` and `Stat11_Ref` demographic reference fields are not election-area union instructions. In particular, Ma'ale Adumim areas 1, 2, and 3 remain separate wherever the official crosswalk reports them separately.
- A locality-only fallback is allowed only when that historical locality has exactly one canonical statistical area.
- Missing crosswalk rows remain unresolved unless a separate reviewed source
  proves a unique exact assignment.

## Current Coverage

Coverage below is the share of actual voters in the geographic scope after adding reviewed custom geographies. Envelope and reviewed non-geographic rows are outside the denominator.

| Election | Statistical-area vintage | Mapped rows | Pending rows | Mapped voter share |
|---|---:|---:|---:|---:|
| K25 | 2011 | 10,877 | 822 | 93.88% |
| K24 | 2011 | 11,161 | 958 | 94.27% |
| K23 | 2011 | 9,930 | 693 | 92.37% |
| K22 | 2011 | 9,919 | 612 | 93.63% |
| K21 | 2011 | 10,023 | 430 | 96.07% |
| K20 | 2011 | 10,051 | 61 | 99.30% |
| K19 | 2011 | 9,309 | 566 | 94.06% |
| K18 | 2008 | 8,740 | 519 | 94.13% |
| K17 | 1995 | 7,853 | 421 | 94.65% |

Every pending row lacks a matching official ballot-crosswalk row and belongs to a locality with more than one historical statistical area. Earlier near-complete K19-K25 figures were invalid: they treated the CBS demographic reference fields as area unions, which made many multi-area localities look like single-area localities and triggered an unjustified fallback. Restoring the distinct source areas returned those rows to pending.

Ma'ale Adumim is the regression case that exposed the problem. Areas 1, 2, and 3 are now separate in both 2008 and 2011 geometry. The rebuilt K20 and K21 ballot counts for all ten Ma'ale Adumim areas match the independent 2015 and April 2019 ArcGIS election layers exactly. Election totals always remain official; ArcGIS is either validation evidence or explicitly labeled aggregate-reconstruction evidence for the approved Tier A rows.

Every pending row is preserved in
`unresolved_statistical_area_assignment_rows.csv`.

The geometry join itself has no current missing-ID gap: every mapped target
resolves to geometry. The remaining geometry caveats concern provenance and
display quality, including 31 documented historical supplements and derivative
ArcGIS West Bank display footprints.

## Generated Outputs

- `data/processed/geographies/statistical_areas_<vintage>.geojson`
- `data/processed/geographies/statistical_areas_<vintage>.display.simplified.geojson`
- `data/processed/geographies/statistical_areas_<vintage>.metadata.csv`
- `data/processed/geographies/statistical_areas_<vintage>.aliases.csv`
- `data/processed/assignments/historical_ballot_crosswalk.csv`
- `data/processed/assignments/historical_ballot_assignments.csv`
- `data/processed/assignments/historical_ballot_assignment_summary.csv`
- `data/processed/assignments/unresolved_statistical_area_assignment_rows.csv`
- `data/processed/audits/arcgis_assignment_reconstruction_candidates.csv`
- `data/processed/audits/arcgis_assignment_reconstruction_localities.csv`
- `data/processed/audits/arcgis_assignment_reconstruction_summary.json`
- `data/manual/arcgis_assignment_reconstruction_reviews.csv`
- `public-data/v1/metadata/arcgis_reconstruction_reviews.csv`

The browser catalog is schema version 3. Each election declares `statisticalAreaVintage` and election-specific `geographiesByMode`; switching elections can therefore switch geometry without changing the result contract.
