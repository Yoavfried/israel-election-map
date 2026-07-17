# Public Data Dictionary

This dictionary describes schema version 1 under [`public-data/v1`](v1/).

## Ballot Tables

Files: `v1/ballots/k17.csv` through `v1/ballots/k25.csv`.

The grain is one official election-result source row, sometimes called a ballot
subdivision in the source. `source_row_uid` is the unique row key. Do not assume
that an address identifies the voters' statistical area or that a displayed
polling-station number is globally unique.

### Source And Vote Columns

| Column | Meaning |
|---|---|
| `source_row_uid` | Stable repository row key, unique across all elections. |
| `election`, `election_number` | Election key and Knesset number. |
| `source_row_id`, `source_order` | Source-system row identity and source order. |
| `source_locality_code`, `source_locality_name` | Locality identity printed by the election source. |
| `source_kalpi` | Polling-station/subdivision identifier printed by the source. |
| `eligible_voters` | Registered eligible voters where the source provides a usable denominator. |
| `actual_voters` | Ballots cast. |
| `valid_votes`, `invalid_votes` | Valid and invalid ballots. |
| `source_address` | Retained polling-place address text; not an area-assignment input. |
| `is_envelope` | Whether the source row is an official envelope result. |

The columns between `is_envelope` and `geography_assignment_status` are party
vote columns. Their names are the official ballot letters for that election.
Use [`metadata/parties.csv`](v1/metadata/parties.csv?raw=1), joined on
`(election, source_column)`, to resolve each column to a reviewed list name.
Party columns sum exactly to `valid_votes` on every published row.

### Statistical-Area Assignment

| Column | Meaning |
|---|---|
| `geography_assignment_status` | Final statistical-mode handling status. |
| `geography_type` | `statistical_area`, `custom_geography`, an envelope/special type, or unresolved handling. |
| `geography_id` | Final statistical-mode target ID when one exists. |
| `stat_area_id` | Stable historical statistical-area ID; blank unless a real area was assigned. |
| `stat_area_vintage` | 1995, 2008, or 2011 for K17-K25 assignments. |
| `stat_area_yishuv_stat` | Historical locality-area compound code from the source crosswalk. |
| `stat_area_number` | Area number within the historical locality. |
| `is_mapped` | Whether statistical mode has a supported mapped target. |
| `final_assignment_method`, `final_assignment_source` | Assignment provenance. |
| `unresolved_reason` | Why no defensible statistical polygon was assigned. |

For ordinary statistical assignments, join `stat_area_id` to
`properties.geography_id` in the package named for `stat_area_vintage`.
`geography_id` may instead point to a reviewed custom geography, so use that
generic field when reproducing the exact statistical-mode display.

### Locality Assignment

| Column | Meaning |
|---|---|
| `locality_assignment_status` | Independent locality-mode handling status. |
| `locality_geography_type` | Locality, composite locality, custom geography, envelope, or special handling. |
| `locality_geography_id` | Exact feature ID used by locality mode. |
| `locality_id`, `locality_code`, `locality_name` | Canonical 2022 locality identity where applicable. |
| `locality_result_code`, `locality_result_name` | Published result identity retained for aggregation/display. |
| `is_locality_mapped` | Whether locality mode has a supported mapped target. |
| `custom_geography_id` | Reviewed custom grouping when applicable. |
| `is_geographic` | Whether the source row represents an ordinary geographic result. |

Join `locality_geography_id` to
[`metadata/geographies.csv`](v1/metadata/geographies.csv?raw=1). The lookup's
`geometry_archive` tells you whether the feature is in `localities_2022`,
`composite_localities`, or `custom_geographies`.

## Aggregate Tables

Each election has separate tables under `v1/aggregates/`:

| Directory | Grain |
|---|---|
| `statistical-areas` | One row per mapped historical statistical area. |
| `localities` | One row per published/reviewed locality result. |
| `custom-geographies` | Reviewed custom results, with the applicable map mode. |
| `envelopes` | One national non-geographic envelope aggregate. |
| `unresolved` | Source rows without a statistical-area polygon, including non-geographic handling. |

Geographic aggregate tables expose `geography_id` and `geography_type` as their
first join columns. Vote totals and party columns are additive. Do not split a
published aggregate among component polygons unless another source supports the
split.

## Geography Tables And Archives

Every feature in every published GeoJSON has:

| Property | Meaning |
|---|---|
| `geography_id` | Stable join key used by ballot and aggregate CSVs. |
| `geography_type` | Statistical area, locality, composite locality, or custom geography. |

The CSV beside each ZIP contains the same non-geometry properties. The combined
`metadata/geographies.csv` adds `geography_package` and `geometry_archive`, which
makes package discovery possible from a join ID alone.

The statistical packages preserve the election-appropriate historical vintages.
K25 uses 2011 areas because its official ballot crosswalk targets 2011; the 2022
package is supplied for future elections and independent analysis, not as a
fabricated K25 conversion.

## Minimal Examples

Pandas:

```python
import geopandas as gpd
import pandas as pd
import zipfile

results = pd.read_csv("public-data/v1/aggregates/statistical-areas/k20.csv")
with zipfile.ZipFile("public-data/v1/geographies/statistical_areas_2011.zip") as z:
    z.extract("statistical_areas_2011.geojson", "tmp")

areas = gpd.read_file("tmp/statistical_areas_2011.geojson")
joined = areas.merge(results, on="geography_id", how="left", validate="one_to_one")
```

QGIS:

1. Extract the matching geography ZIP and open its GeoJSON.
2. Add the election aggregate CSV as a delimited-text layer without geometry.
3. Join CSV `geography_id` to GeoJSON `geography_id`.

## Nulls And Reconciliation

- Blank assignment IDs mean the evidence does not support a polygon; they are
  not zero-vote areas.
- Envelope and reviewed non-geographic rows remain counted but have no polygon.
- Statistical and locality coverage are different because they answer different
  geographic questions.
- `validation.json` verifies row counts, party-vote reconciliation, and that all
  nonblank published join IDs exist in the supplied geometry.
