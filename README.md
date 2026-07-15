# Israel Election Map

Local-first web map for exploring K17-K25 Knesset election results on 2022 Israeli geography.

The repository contains both the reproducible election/geography pipeline and a React/TypeScript map client. Historical ballot rows are assigned to 2022 statistical areas where the evidence supports it; inferred areas are not presented as official historical polling boundaries.

## Current Status

- Official K17-K25 ballot results are normalized into 96,529 source rows.
- Every row has a handling rule: 2022 statistical area, reviewed custom geography, address placement required, envelope, or reviewed non-geographic exception.
- OSM is the first address-placement layer. Photon is reserved for unresolved fallback work.
- The current OSM audit leaves 4,893 unique unresolved location signatures covering 52,437 non-envelope ballot rows.
- Locality mode maps all 92,945 geographic-scope rows for K17-K25. Reviewed composite municipalities preserve the election-time locality geometry where the 2022 layer has separate component localities.
- Statistical-area mode does not yet promote OSM candidates; its current geographic-scope voter coverage ranges from 12.65% to 14.38% by election.
- Official envelope votes are aggregated as a separate national result for every election and are not placed on locality polygons.
- K17 scan recovery and the completed K18 visual-review corrections are part of the normalized source pipeline.

Locality behavior is documented in `docs/LOCALITY_MODE.md`. The statistical-area methodology, unmatched categories, and promotion boundary are documented in `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md`.

## Assignment Strategy

Locality mode assigns rows directly through the reviewed locality crosswalk. It does not wait for address geocoding. Statistical-area mode uses the following narrower process:

1. Exclude official envelope and reviewed non-geographic rows.
2. Assign a locality directly when it has exactly one 2022 statistical area.
3. In multi-area localities, accept an OSM street only when its 25 m corridor lies in one area.
4. Use an exact OSM house number to resolve streets that span or touch multiple areas.
5. Keep unresolved place names, suspicious source text, and OSM misses in explicit review inventories.
6. Use Photon only after OSM, with expected-locality validation and point-in-2022-area assignment.

Source AGS is diagnostic context, not a hard building-location check. Multiple kalpis and multiple source AGS values can share one polling-place building, and one observed AGS does not prove that the building lies inside it.

## Run

```powershell
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
```

When the generated 2022 geography files already exist, the non-geography stages can be reproduced without rebuilding the FileGDB layer:

```powershell
python scripts/run_pipeline.py --skip-geographies
```

Run the web app:

```powershell
cd web/app
npm install
npm run dev
```

Vite serves the app at `http://localhost:4173`. The frontend compiler reads `data/processed/` and writes disposable, validated assets under `web/app/public/data/v2/`.

## Documentation

- `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md` - current end-to-end assignment and unmatched inventory.
- `docs/LOCALITY_MODE.md` - complete locality coverage, composite municipalities, and envelope presentation.
- `docs/POLLING_PLACE_ADDRESS_QUALITY_AUDIT.md` - source fidelity, OCR/manual review, and OSM address QA.
- `docs/DATA_PIPELINE.md` - stages, outputs, commands, and verified run counts.
- `docs/POLLING_PLACE_ADDRESSES.md` - election-specific address sources.
- `docs/AGS_HISTORICAL_QA.md` - why AGS is diagnostic rather than a hard geocode gate.
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md` - assignments currently promoted to public outputs.
- `web/app/docs/ARCHITECTURE.md` - frontend data contract and product boundary.

## Repository Layout

- `data/manual/` - committed reviewed corrections and assignment overrides.
- `data/raw/` and `data/processed/` - local source and generated data, intentionally ignored by Git.
- `docs/` - methodology, source notes, decisions, and committed reference tables.
- `scripts/` - ingestion, normalization, QA, OSM matching, assignment, and aggregation.
- `web/app/` - Vite, React, TypeScript, and MapLibre client.
- `web/geocode-spike/` - static provider-research page retained for geocoder investigation.

## License

TBD.
