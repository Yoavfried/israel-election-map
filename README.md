# Israel Election Map

Local-first web map for exploring Israeli Knesset election results by geography.

The project is currently in data-discovery and foundation setup. The first supported geography modes are planned to be:

1. Statistical areas
2. Localities

Kalpi-level results are part of the source data, but the project will not present inferred areas as official kalpi borders. Statistical-area assignment is an approximation based on polling-place address geocoding plus a single-stat locality shortcut.

## Current Direction

- Use official Knesset election results from data.gov.il for K16-K25.
- Use the 2022 statistical-area FileGDB as the canonical statistical-area polygon source.
- Add locality mode separately.
- Preserve raw source data and generated/normalized data separately.
- Keep source metadata, assignment method, and mapped/unmapped coverage visible in the product.

## Repository Layout

- `docs/` - project plan, source notes, decisions, and open questions.
- `data/` - local raw/processed data directories, intentionally gitignored.
- `scripts/` - future ingestion and conversion scripts.
- `src/` - future web application source.

## Status

No runnable web app has been scaffolded yet.

## License

TBD.
