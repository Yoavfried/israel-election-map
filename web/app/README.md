# Israel Election Map Web App

Local-first React/TypeScript map client for the K17–K25 pipeline. The app does not read the working CSV files at runtime. A build-time compiler validates them and writes disposable web assets under `public/data/v1/`.

## Run locally

Prerequisites:

- Node.js 20.19+ (the current workspace uses Node 24).
- The generated pipeline outputs under `../../data/processed/`.

```powershell
npm install
npm run dev
```

`npm run dev` first rebuilds the web data, then starts Vite on `http://localhost:4173`.

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

## Isolation from the data pipeline

- `scripts/build-data.mjs` only reads `data/processed/`.
- Generated web assets are ignored by Git.
- The compiler writes to a staging directory and replaces only `web/app/public/data/v1/` after a successful build.
- No existing pipeline script or in-progress review file is modified by this app.

## Coverage boundary

The compiler reads the promoted public assignment outputs. It does not treat analytical OSM candidates as final assignments. Until OSM matches are promoted by the Python assignment stage, the map intentionally shows only the current reviewed subset and displays pending-voter coverage prominently.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the data contract and phased implementation plan.
