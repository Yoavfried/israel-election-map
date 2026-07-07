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
- Use the reviewed locality crosswalk and single-stat locality assignment table before geocoding.
- Add locality mode separately.
- Preserve raw source data and generated/normalized data separately.
- Keep source metadata, assignment method, and mapped/unmapped coverage visible in the product.

Current K17-K25 statistical-area status: all ordinary rows are address/assignment covered except 11 K17 rows that have polling-place names from the scanned list but no street address.

Current core docs:

- `docs/PROJECT_PLAN.md`
- `docs/DATA_SOURCES.md`
- `docs/POLLING_PLACE_ADDRESSES.md`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.md`

## Repository Layout

- `docs/` - project plan, source notes, decisions, and open questions.
- `data/` - local raw/processed data directories, intentionally gitignored.
- `scripts/` - future ingestion and conversion scripts.
- `src/` - future web application source.

## Status

No runnable web app has been scaffolded yet.

## License

TBD.
