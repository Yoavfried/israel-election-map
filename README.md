# Israel Election Map

Local-first bilingual web map for exploring K17-K25 Knesset election results by locality and election-appropriate statistical area.

The repository contains a Python data pipeline and a React/TypeScript/MapLibre client. Statistical results are assigned from official CBS ballot-to-area crosswalks, not from polling-place addresses.

## Current Status

- Official K17-K25 results are normalized into 96,529 source rows.
- Statistical mode uses 1995 areas for K17, 2008 for K18, and 2011 for K19-K25.
- Statistical-mode mapped-voter coverage ranges from 92.37% to 94.65%; every row without a defensible historical-area assignment remains explicit and unpainted.
- Locality mode maps 100% of the geographic scope and supports reviewed historical municipalities and joined polling-register display unions.
- Envelope and reviewed envelope-like rows are shown as a separate national result, never duplicated across polygons.
- Historical geometry and current locality mode use audited detailed West Bank display footprints where available. Current locality mode replaces 115 tiny proxies; only Rotem, Maskiyot, Avnat, and Mavo'ot Yeriho remain settlement markers. The K25 Yitav/Mavo'ot joined result stays a two-point marker.
- K17 ordinary geography has reviewed eligible-voter denominators and turnout; envelope turnout remains unavailable.
- The party registry covers every K17-K25 result column, and the published party/list names are reviewed and complete. Party colors and Hebrew/English Wikipedia links remain separate, incomplete editorial work.

## Assignment Strategy

Statistical-area assignment precedence is:

1. official envelope or reviewed non-geographic handling;
2. reviewed custom geography;
3. official election-specific CBS ballot-to-statistical-area crosswalk;
4. historical locality fallback only when that locality has exactly one published area;
5. explicit unresolved status.

Address geolocation does not assign election results. A polling-place building can serve voters from several statistical areas, so its coordinates cannot recover voter geography. OSM and Photon code remains for polling-place search, address QA, and future building-location features.

K25 currently uses 2011 areas because the official November 2022 crosswalk targets 2011. Thousands of its target areas split across multiple 2022 areas, so forcing K25 onto 2022 polygons would invent precision.

## Local Setup

The full pipeline depends on downloaded official source files that are intentionally not committed. Start with `docs/DATA_SOURCES.md` and `data/README.md`; a fresh clone is not yet a one-command data bootstrap.

Install Python dependencies and download the sources supported by the fetch scripts:

```powershell
python -m pip install -r requirements.txt
python scripts/fetch_cbs_historical_geography.py
python scripts/fetch_election_results.py
```

After preparing the remaining raw inputs listed in the data-source documentation, run the pipeline:

```powershell
python scripts/run_pipeline.py
```

Reuse already generated current and historical geometry:

```powershell
python scripts/run_pipeline.py --skip-geographies
```

Run the web app:

```powershell
cd web/app
npm install
npm run dev
```

Vite serves the app at `http://localhost:4173`. The frontend compiler reads `data/processed/` and writes disposable validated assets under `web/app/public/data/v2/`.

ArcGIS layers used for audited display geometry are downloaded separately:

```powershell
python scripts/fetch_arcgis_feature_layer.py <FeatureServer-layer-url> <output.geojson>
```

## Documentation

- `docs/PROJECT_STATUS.md` - canonical completed/in-progress status and the current statistical-mode gap explanation.
- `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` - source hierarchy, vintages, geometry provenance, matching rules, and coverage.
- `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md` - concise current assignment state.
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md` - election-by-election published coverage.
- `docs/LOCALITY_MODE.md` - locality aggregation, composites, result-presence audit, and envelopes.
- `docs/DATA_PIPELINE.md` - reproducible stage order and outputs.
- `docs/DATA_SOURCES.md` - election, geography, party, and polling-place sources.
- `docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md` - address/OCR fidelity for the separate polling-place-location dataset.
- `docs/AGS_HISTORICAL_QA.md` - why source AGS is not a polling-place building test.
- `docs/K17_ELIGIBLE_VOTER_RECOVERY.md` - K17 turnout recovery.
- `web/app/docs/ARCHITECTURE.md` - frontend data contracts and product boundary.

## Explicitly Incomplete

- Historical crosswalk gaps remain in every election and require source research; demographic reference fields are not used to manufacture area assignments.
- The partial/no-result locality-history audit is not finished.
- Party colors and Wikipedia links are not fully reviewed. Party/list names are complete.
- General UX, accessibility, mobile QA, and broader end-to-end tests remain active work.
- Planned features such as search/navigation, additional coloring modes, contribution drill-down, and a polling-place layer are not complete.
- A fully automated fresh-clone source bootstrap and public release packaging are not complete.

## Repository Layout

- `data/manual/` - committed reviewed corrections and assignment overrides.
- `data/raw/` and `data/processed/` - local source and generated data, intentionally ignored by Git.
- `docs/` - methodology, source notes, decisions, and committed reference tables.
- `scripts/` - ingestion, normalization, geography, assignment, QA, and aggregation.
- `web/app/` - Vite, React, TypeScript, and MapLibre client.
- `web/geocode-spike/` - retained geocoder research page.

## Contributing

See `CONTRIBUTING.md` before changing reviewed data or generated outputs. Do not commit raw downloads, generated data, credentials, local paths, or disposable investigation files.

## License Status

No license has been selected yet. Public repository visibility does not grant permission to reuse the code or data; selecting an explicit code/data license remains a release task.
