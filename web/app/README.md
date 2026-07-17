# Israel Election Map Web App

Local-first React/TypeScript map client for the K17-K25 pipeline. The app does not read working CSV files at runtime. A build-time compiler validates them and writes disposable web assets under `public/data/v2/`.

## Run Locally

Prerequisites:

- Node.js 20.19 or newer.
- Generated pipeline outputs under `../../data/processed/`.

```powershell
npm install
npm run dev
```

`npm run dev` rebuilds the web data and starts Vite on `http://localhost:4173`.

Useful commands:

```powershell
npm run data:build
npm test
npm run check
npm run build
```

To compile from another processed-data directory:

```powershell
npm run data:build -- --source C:\path\to\data\processed
```

## Isolation From the Data Pipeline

- `scripts/build-data.mjs` only reads `data/processed/`.
- Generated web assets are ignored by Git.
- The compiler writes to a staging directory and replaces only `web/app/public/data/v2/` after a successful build.
- The web build does not modify pipeline scripts or review files.

## Coverage Boundary

The compiler reads promoted public assignment outputs. Locality mode covers the complete K17-K25 geographic scope and includes reviewed election-specific composite municipalities and joined-register unions. Official envelope results appear as a separate selectable national aggregate.

Statistical mode uses official ballot-to-area crosswalks and election-specific historical geometry: 1995 for K17, 2008 for K18, and 2011 for K19-K25. Address-geocoding candidates are not eligible assignment inputs. Result payloads disclose mapped-voter coverage and preserve pending rows instead of inferring their polygons.

Party/list display names are complete. Party colors and Wikipedia-link review remain in progress, as do broader UX and feature work.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the data contract and implementation status.
