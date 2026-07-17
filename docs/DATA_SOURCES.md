# Data Sources

Last updated: 2026-07-17

## Election Results

Official Knesset election results package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Current project scope starts at K17 / 2006 and runs through K25 / 2022.

- Locality totals are generated from normalized ballot rows and reviewed
  locality identities; official locality summaries are validation evidence.
- Party columns are election-specific ballot letters and are never treated as
  stable party IDs across elections.
- K16 / 2003 is outside the current product scope.
- K25 can also be checked against the official results site:
  https://votes25.bechirot.gov.il/

## K17 Eligible-Voter Recovery

The official K17 result resource omits ballot-level eligible-voter counts.
Archived official reports under `data/raw/` provide the missing counts,
locality subtotals, regional-committee totals, and the national denominator.
`data/manual/k17_eligible_voters.csv` restores the denominator for all 8,277
ordinary result rows.

Final-report image extraction supplies 8,199 rows, 14 more are recovered from
otherwise unaligned final-report lines, and one omitted zero-voter row is
recorded explicitly as zero. The remaining 63 rows use the official planned
list under exact subtotal or national reconciliation. The ordinary-register
total is 5,011,053.

The separate 3,569-person Gush Katif register brings the official national
denominator to 5,014,622. It has no ballot-level geographic distribution. The
public envelope/non-geographic aggregate therefore stores it as a technical
denominator bucket alongside 518 eligible voters from three non-geographic K17
camp rows: 4,087 in that bucket plus 5,010,535 geographically represented
eligible voters equals 5,014,622. The frontend does not calculate envelope
turnout from this mixed bucket. Full recovery methods are in
`docs/K17_ELIGIBLE_VOTER_RECOVERY.md`.

## Party/List Registry

`data/manual/party_registry.csv` is keyed by `(election, source_column)` because
the same ballot letters can identify different lists in different elections.
It tracks all 309 K17-K25 source columns: 297 published lists and 12 confirmed
zero-filled columns for lists that did not run.

All published Hebrew display names are reviewed. English labels may fall back
to the reviewed Hebrew name. Wikipedia links remain under manual audit.
`web/app/config/party-overrides.json` separates reviewed names and colors from
the data table, supports stable default colors by ballot letter, and allows
election-specific exceptions.

## Historical Ballot Crosswalks And Geometry

The CBS GIS catalog supplies direct ballot-to-statistical-area tables for every
current-scope election:

- K17 -> 1995 areas
- K18 -> 2008 areas
- K19-K25 -> 2011 areas

It also supplies the corresponding geometry and transition tables.
`scripts/fetch_cbs_historical_geography.py` records exact source URLs, byte
lengths, and SHA-256 hashes in
`data/raw/cbs_historical_geography/manifest.json`.

Two downloadable ArcGIS FeatureServer layers provide detailed display
footprints, 30 explicit exact-ID 2011 geometry supplements, and aggregate
evidence for the K20/K21 residual-partition audit. Forty-four reviewed Tier A
locality-election decisions use those aggregates to infer missing
ballot-to-area links. They never replace official ballot or vote values, and
every affected public row carries explicit inferred-assignment provenance.
Their service descriptions state that the election output is not official and
that some polygons are schematic.

See `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` for the exact precedence,
vintage rules, supplement IDs, audit results, and current coverage.

## Current Locality Display Geometry

The 2022 FileGDB is canonical for current locality display geometry and for a
future election that publishes a direct 2022 crosswalk. K17-K25 statistical
results continue to use their historical targets.

Canonical raw source:

- `data/raw/ezorim_statistiim_2022.gdb`
- layer `statistical_areas_2022`
- 3,857 source polygon features
- 1,387 dissolved locality/display features
- 1,242 dissolved features with one statistical-area component
- 145 dissolved localities with multiple components

The dissolved layer retains 58 unlabeled land polygons as neutral context so
they do not appear as water. Kinneret remains unfilled. The previous partial
`data/raw/statistical-areas-2022.geojson` export is no longer a project source.

Relevant source fields:

| Field | Meaning |
|---|---|
| `SEMEL_YISHUV` | Locality code |
| `SHEM_YISHUV` | Hebrew locality name |
| `SHEM_YISHUV_ENGLISH` | English locality name |
| `STAT_2022` | Area code within locality |
| `YISHUV_STAT_2022` | Combined locality/area code |
| `ROVA` | Quarter code where present |
| `TAT_ROVA` | Sub-quarter code where present |
| `COD_TIFKUD` | Function/type code |

`data/manual/composite_localities.csv` defines four election-time composite
municipalities. `data/manual/joined_locality_composites.csv` defines
source-backed host/result unions for elections where a small register was
published under a nearby host result.

## Locality Classification Evidence

The official CBS 2022 locality workbook and definitions support the current
no-standalone-result audit:

- https://www.cbs.gov.il/he/publications/DocLib/2019/ishuvim/bycode2022.xlsx
- https://www.cbs.gov.il/he/publications/DocLib/2019/ishuvim/intro.pdf

Reviewed form and population values are stored in
`data/manual/locality_result_presence_reviews.csv`. These 2022 classifications
do not by themselves prove a separate voter register in an older election.
Election-specific joins require independent result evidence.

Section 70 of the Knesset election law permits joining an area with fewer than
100 eligible voters to a nearby area:

https://www.gov.il/apps/elections/elections-knesset-17/heb/law/ElectionLaw.html

The resulting secret-ballot aggregate cannot be split into component party
totals. Where the source establishes the host, locality mode may display the
host and attached polygons as one election-specific union.

## 2022 Census Attributes

The 2022 census package is available at:

https://data.gov.il/api/3/action/package_show?id=2022

Resource `9a9e085f-3bc8-41df-b15f-be0daaf99e30` includes `LocalityCode`,
`StatArea`, `StatAreaCmb`, and census measures. No geometry resource was found
in the inspected package.

## Reuse And Provenance

Keep the most complete official/raw source for each vintage. Canonical inputs
are the CBS 1995 archive, 2008 FileGDB, 2011 FileGDB, and 2022 FileGDB. ArcGIS
layers are derivative supplement/display sources with explicit provenance.

Original project software and documentation use the MIT License. CBS and other
official source material remain subject to their source terms; see
`THIRD_PARTY_NOTICES.md`.
