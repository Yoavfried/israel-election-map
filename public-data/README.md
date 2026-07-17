# Public Election Data

The repository includes a versioned, ready-to-download data release under
[`public-data/v1`](v1/). You do not need to run the pipeline to use these files.

The release contains all 96,529 normalized K17-K25 ballot-result rows, separate
polygon aggregates, full-resolution geography packages, election and party
metadata, checksums, and a machine-readable validation report.

## Download One Election

Each ballot CSV contains every source result row for that election, one column
per registered ballot letter, and both statistical-area and locality join IDs.

| Election | Rows | Statistical vintage | Ballot rows | Statistical aggregates | Locality aggregates | Statistical polygons |
|---|---:|---:|---|---|---|---|
| K17 (2006) | 8,426 | 1995 | [CSV](v1/ballots/k17.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k17.csv?raw=1) | [CSV](v1/aggregates/localities/k17.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_1995.zip?raw=1) |
| K18 (2009) | 9,264 | 2008 | [CSV](v1/ballots/k18.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k18.csv?raw=1) | [CSV](v1/aggregates/localities/k18.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2008.zip?raw=1) |
| K19 (2013) | 10,109 | 2011 | [CSV](v1/ballots/k19.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k19.csv?raw=1) | [CSV](v1/aggregates/localities/k19.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |
| K20 (2015) | 10,414 | 2011 | [CSV](v1/ballots/k20.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k20.csv?raw=1) | [CSV](v1/aggregates/localities/k20.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |
| K21 (April 2019) | 10,765 | 2011 | [CSV](v1/ballots/k21.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k21.csv?raw=1) | [CSV](v1/aggregates/localities/k21.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |
| K22 (September 2019) | 10,901 | 2011 | [CSV](v1/ballots/k22.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k22.csv?raw=1) | [CSV](v1/aggregates/localities/k22.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |
| K23 (2020) | 11,179 | 2011 | [CSV](v1/ballots/k23.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k23.csv?raw=1) | [CSV](v1/aggregates/localities/k23.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |
| K24 (2021) | 12,926 | 2011 | [CSV](v1/ballots/k24.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k24.csv?raw=1) | [CSV](v1/aggregates/localities/k24.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |
| K25 (2022) | 12,545 | 2011 | [CSV](v1/ballots/k25.csv?raw=1) | [CSV](v1/aggregates/statistical-areas/k25.csv?raw=1) | [CSV](v1/aggregates/localities/k25.csv?raw=1) | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) |

Other election-specific downloads are organized under
[`aggregates/custom-geographies`](v1/aggregates/custom-geographies/),
[`aggregates/envelopes`](v1/aggregates/envelopes/), and
[`aggregates/unresolved`](v1/aggregates/unresolved/).

## Geography Packages

Each ZIP contains full-resolution GeoJSON and a CSV with the same feature
metadata. Every feature exposes `properties.geography_id`.

| Package | Features | Archive | Metadata only |
|---|---:|---|---|
| 1995 statistical areas | 2,660 | [ZIP](v1/geographies/statistical_areas_1995.zip?raw=1) | [CSV](v1/geographies/statistical_areas_1995.csv?raw=1) |
| 2008 statistical areas | 3,030 | [ZIP](v1/geographies/statistical_areas_2008.zip?raw=1) | [CSV](v1/geographies/statistical_areas_2008.csv?raw=1) |
| 2011 statistical areas | 3,105 | [ZIP](v1/geographies/statistical_areas_2011.zip?raw=1) | [CSV](v1/geographies/statistical_areas_2011.csv?raw=1) |
| 2022 statistical areas | 3,857 | [ZIP](v1/geographies/statistical_areas_2022.zip?raw=1) | [CSV](v1/geographies/statistical_areas_2022.csv?raw=1) |
| 2022 locality footprints | 1,387 | [ZIP](v1/geographies/localities_2022.zip?raw=1) | [CSV](v1/geographies/localities_2022.csv?raw=1) |
| Historical/reviewed locality composites | 100 | [ZIP](v1/geographies/composite_localities.zip?raw=1) | [CSV](v1/geographies/composite_localities.csv?raw=1) |
| Reviewed custom geographies | 4 | [ZIP](v1/geographies/custom_geographies.zip?raw=1) | [CSV](v1/geographies/custom_geographies.csv?raw=1) |

Use [`metadata/geographies.csv`](v1/metadata/geographies.csv?raw=1) as the
combined lookup from any `geography_id` to its geometry archive.

## Join Rules

- Statistical ballot assignment: `ballots/*.csv.stat_area_id` equals
  `GeoJSON.properties.geography_id` in the election's statistical package.
- Locality ballot assignment: `ballots/*.csv.locality_geography_id` equals
  `metadata/geographies.csv.geography_id`; `geometry_archive` identifies the
  package containing the feature.
- Polygon aggregates: every geographic aggregate CSV has a standard
  `geography_id` column that equals `GeoJSON.properties.geography_id`.
- Blank statistical IDs are intentional unresolved source gaps. Envelope rows
  are national non-geographic results and do not join to a polygon.

See the [data dictionary](DATA_DICTIONARY.md) for column-level definitions and
short pandas/QGIS examples.

## Metadata And Integrity

- [`metadata/elections.csv`](v1/metadata/elections.csv?raw=1) lists election
  years, active statistical vintages, and principal paths.
- [`metadata/parties.csv`](v1/metadata/parties.csv?raw=1) maps each
  election/ballot-letter combination to its reviewed list name and article
  metadata.
- [`metadata/coverage.csv`](v1/metadata/coverage.csv?raw=1) reports mapped and
  pending coverage by election.
- [`manifest.csv`](v1/manifest.csv?raw=1) and
  [`manifest.json`](v1/manifest.json?raw=1) contain file sizes, row counts, and
  SHA-256 checksums.
- [`validation.json`](v1/validation.json?raw=1) records the release checks.

CSVs are UTF-8 with a byte-order mark for reliable Hebrew display in spreadsheet
software. The release is generated by `scripts/build_public_data_release.py` and
must not be edited by hand.

## Data Versus Map Presentation

This release publishes election facts, reviewed party/list metadata, assignment
provenance, and geometry. It deliberately excludes map colors, concise UI label
overrides, layout, and interaction configuration. Those are presentation choices
owned by the map application under `web/app/`.

No reuse license has been selected yet. The files are publicly downloadable, but
repository visibility alone does not grant reuse rights; licensing remains in
the canonical [project status](../docs/PROJECT_STATUS.md).
