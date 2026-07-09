# Israel Election Map

Local-first web map for exploring Israeli Knesset election results by geography.

The project is currently in data-discovery and foundation setup. The first supported geography modes are planned to be:

1. Statistical areas
2. Localities

Kalpi-level results are part of the source data, but the project will not present inferred areas as official kalpi borders. Statistical-area assignment is an approximation based on polling-place address geocoding plus a single-stat locality shortcut.

## Current Direction

- Use official Knesset election results from data.gov.il for K17-K25.
- K16 / 2003 is deferred until a usable election-specific polling-place address source is recovered.
- Use the 2022 statistical-area FileGDB as the canonical statistical-area polygon source.
- Derive locality polygons by dissolving the 2022 statistical-area polygons; locality mode must not show internal statistical-area borders.
- Build both statistical-area and locality totals from the row-level ballot pipeline, not from official locality aggregate files.
- Use the reviewed locality crosswalk and single-stat locality assignment table before geocoding.
- Preserve raw source data and generated/normalized data separately.
- Keep source metadata, assignment method, and mapped/unmapped coverage visible in the product.

Current K17-K25 statistical-area status: row assignment is classified for every result row, and every relevant row has a geocoder query. A full local Photon candidate run exists, but no production geocode cache has been approved yet. Candidate coordinates must pass point-in-expected-locality validation, manual review, and historical AGS QA where source AGS exists before promotion. Some K17/K18/K19 rows are place-name-only and need provider/manual review rather than blind acceptance.

Current core docs:

- `docs/PROJECT_PLAN.md`
- `docs/DATA_SOURCES.md`
- `docs/DATA_PIPELINE.md`
- `docs/POLLING_PLACE_ADDRESSES.md`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.md`
- `docs/GEOCODING_SPIKE.md`
- `docs/AGS_HISTORICAL_QA.md`
- `docs/GOVMAP_BROWSER_SPIKE.md`
- `docs/ARCGIS_GEOCODING_SPIKE.md`
- `docs/PHOTON_GEOCODING_SPIKE.md`

## Repository Layout

- `docs/` - project plan, source notes, decisions, and open questions.
- `data/` - local raw/processed data directories, intentionally gitignored.
- `scripts/` - ingestion, normalization, assignment, and aggregate-output scripts.
- `src/` - future web application source.

## Status

No product web app has been scaffolded yet. A temporary static GovMap provider-test page lives in `web/geocode-spike/`. The current data pipeline runs through final row-level geography assignment and public aggregate CSV generation; outputs are partial until a reviewed geocode cache is added. See `docs/DATA_PIPELINE.md`.

## License

TBD.
