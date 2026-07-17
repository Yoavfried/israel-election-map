# Contributing

Contributions should preserve source provenance and avoid inventing geographic precision.

## Setup

1. Install Python dependencies from `requirements.txt` and Node.js 20.19 or newer.
2. Prepare ignored raw inputs as documented in `docs/DATA_SOURCES.md` and `data/README.md`.
3. Run `python scripts/run_pipeline.py` or reuse existing geography with `--skip-geographies`.
4. Run `npm install` in `web/app/` and use `npm run check` before submitting changes.

## Data Changes

- Put reviewed corrections and overrides in `data/manual/`, with source evidence in the row notes or relevant methodology document.
- Do not edit generated files in `data/processed/` or `web/app/public/data/` by hand.
- Do not infer voter geography from a polling-place address.
- Do not replace official totals with derivative ArcGIS values.
- Keep assignment geometry and display-only geometry provenance separate.

## Public Repository Hygiene

- Do not commit credentials, API tokens, private contact data, machine-specific paths, raw downloads, generated data, logs, or files under `work/`.
- Use environment variables for optional service credentials. Commit only documented example configuration with placeholder values.
- Keep documentation factual and source-oriented. Avoid private deployment domains or notes that depend on one contributor's machine.

## Change Checks

- Data pipeline changes should run the affected Python stage and its downstream reconciliation checks.
- Frontend or compiler changes should pass `npm run check` in `web/app/`.
- User-facing map changes should be checked in Hebrew and English and at desktop and mobile widths.
- Update `docs/PROJECT_STATUS.md` only when a workstream's actual completion state changes.

The repository does not yet have a selected license. External contributions should wait until contribution and licensing terms are explicitly established.
