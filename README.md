# Israel Election Map

Bilingual web map and reproducible data pipeline for exploring K17-K25 Knesset
election results by locality and election-appropriate statistical area.

The repository contains a Python data pipeline, a React/TypeScript/MapLibre map,
and a committed public-data release. Statistical results are assigned from
official CBS ballot-to-area crosswalks, not from polling-place addresses.

## Download The Data

Ready-to-use files are committed under [`public-data/v1`](public-data/v1/). No
pipeline run is required.

| Election | Full ballot-row CSV | Statistical-area results | Locality results |
|---|---|---|---|
| K17 (2006) | [Download](public-data/v1/ballots/k17.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k17.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k17.csv?raw=1) |
| K18 (2009) | [Download](public-data/v1/ballots/k18.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k18.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k18.csv?raw=1) |
| K19 (2013) | [Download](public-data/v1/ballots/k19.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k19.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k19.csv?raw=1) |
| K20 (2015) | [Download](public-data/v1/ballots/k20.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k20.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k20.csv?raw=1) |
| K21 (April 2019) | [Download](public-data/v1/ballots/k21.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k21.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k21.csv?raw=1) |
| K22 (September 2019) | [Download](public-data/v1/ballots/k22.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k22.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k22.csv?raw=1) |
| K23 (2020) | [Download](public-data/v1/ballots/k23.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k23.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k23.csv?raw=1) |
| K24 (2021) | [Download](public-data/v1/ballots/k24.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k24.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k24.csv?raw=1) |
| K25 (2022) | [Download](public-data/v1/ballots/k25.csv?raw=1) | [Download](public-data/v1/aggregates/statistical-areas/k25.csv?raw=1) | [Download](public-data/v1/aggregates/localities/k25.csv?raw=1) |

The full ballot CSVs contain every source result row, party-vote columns, and
the corresponding statistical-area and locality IDs. Polygon ZIPs expose the
same `geography_id`, so the join is direct.

- [Complete download index and polygon packages](public-data/README.md)
- [Data dictionary and join examples](public-data/DATA_DICTIONARY.md)
- [Machine-readable manifest and checksums](public-data/v1/manifest.csv?raw=1)

Map colors, concise UI labels, and interaction settings are not part of the data
release. They remain presentation configuration owned by `web/app/`.

## Geographic Assignment

Statistical-area assignment precedence is:

1. official envelope or reviewed non-geographic handling;
2. official election-specific CBS ballot-to-statistical-area crosswalk;
3. historical locality fallback only when that locality has one published area;
4. reviewed custom geography when no supported historical area exists;
5. explicit unresolved status.

Statistical mode uses 1995 areas for K17, 2008 for K18, and 2011 for K19-K25.
K25 remains on 2011 because its official crosswalk targets that vintage; forcing
those results onto 2022 areas would invent precision.

Address geolocation does not assign election results. A polling-place building
can serve voters from several statistical areas. OSM and Photon work remains in
the repository for polling-place search, address QA, and possible future
building-location features.

## Run Locally

The full pipeline depends on downloaded official source files that are not
committed. Start with [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) and
[`data/README.md`](data/README.md).

```powershell
python -m pip install -r requirements.txt
python scripts/fetch_cbs_historical_geography.py
python scripts/fetch_election_results.py
python scripts/run_pipeline.py
```

Reuse existing generated geography with:

```powershell
python scripts/run_pipeline.py --skip-geographies
```

Run the web app:

```powershell
cd web/app
npm install
npm run dev
```

Vite serves the app at `http://localhost:4173`. The frontend compiler reads
`data/processed/` and writes disposable validated assets under
`web/app/public/data/v2/`.

## Documentation

- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) is the only project
  completion tracker.
- [`docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md`](docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md)
  documents source hierarchy, vintages, matching rules, and coverage.
- [`docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`](docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md)
  is the generated election-by-election coverage table.
- [`docs/LOCALITY_MODE.md`](docs/LOCALITY_MODE.md) documents locality aggregation,
  composites, result-presence evidence, and envelopes.
- [`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) documents the reproducible
  stage order and outputs.
- [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) inventories election, geography,
  party, and polling-place sources.
- [`docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md`](docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md)
  covers the separate polling-place-location dataset.
- [`web/app/docs/ARCHITECTURE.md`](web/app/docs/ARCHITECTURE.md) defines the
  frontend data contract and product boundary.

## Repository Layout

- `public-data/` - committed, versioned data downloads and geography packages.
- `data/manual/` - committed reviewed corrections and assignment overrides.
- `data/raw/` and `data/processed/` - local source and generated working data,
  intentionally ignored by Git.
- `docs/` - methodology, source notes, decisions, and committed reference tables.
- `scripts/` - ingestion, normalization, geography, assignment, QA, aggregation,
  and public-release generation.
- `web/app/` - Vite, React, TypeScript, and MapLibre client.
- `web/geocode-spike/` - retained geocoder research page.

## Contributing And Licensing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing reviewed data or
generated releases. Do not commit credentials, local paths, disposable
investigation files, or raw source downloads.

No license has been selected yet. Public visibility and file downloadability do
not by themselves grant permission to reuse the code or data. Licensing is an
open release item in the canonical [project status](docs/PROJECT_STATUS.md).
