# Frontend architecture and implementation plan

## Product boundary

The first product is a static, local-first web application. It reads versioned assets generated from the existing Python pipeline and does not own election ingestion, geocoding, assignment, or aggregation.

The web app supports:

- K17–K25 election selection.
- 2022 statistical-area and dissolved-2022-locality modes.
- English and Hebrew, including document-level LTR/RTL switching.
- Desktop and mobile layouts.
- Explicit mapped/unmapped vote coverage.
- Custom reviewed geographic buckets when they have results in an election.
- Election-specific composite municipalities in locality mode.
- Official envelope results as a selectable national, non-map result.

“Locality” is the contract term rather than “municipality”: the dissolved CBS layer contains localities, not only incorporated municipalities.

## Data flow

```text
data/processed CSV + GeoJSON
            |
            v
scripts/build-data.mjs
  - validates IDs and numeric fields
  - joins bilingual geography metadata
  - prunes GeoJSON properties
  - attaches stable feature IDs
  - merges custom geography results
  - applies election-specific composite visibility
  - attaches envelope aggregates
  - emits mode-specific coverage and provenance
            |
            v
public/data/v2/
  catalog.json
  geographies/*.geojson
  results/<election>/*.json
            |
            v
Zod-validated browser data client
            |
            v
MapLibre feature state + React detail panels
```

The browser loads the catalog first, then only the selected election/mode result file. The MapLibre bundle is dynamically imported into its own chunk (about 274 KB gzip in the current build). Geometry is mode-specific, and the compiler removes source-only fields and rounds web coordinates to six decimal places (well below the source simplification tolerance) before writing the browser payload. Each mode also has a small marker GeoJSON containing display-only point proxies for custom buckets and point-like West Bank features. The West Bank proxy rule is limited to locality codes 3500–3999 whose simplified geometry retains the tiny point-proxy signature; detailed settlement polygons remain polygonal.

## Version 2 contracts

`catalog.json` is the discovery and provenance document. It contains:

- `schemaVersion` and content-derived `buildId`.
- Election labels and result URLs.
- Geography labels, feature counts, geometry URLs, and Israel bounds.
- Per-election, per-mode mapped, pending, and unmapped vote coverage.
- SHA-256 and byte length for generated assets.
- A visible status for the provisional party-color policy.

Each result asset contains:

- Election and geography identity.
- Coverage repeated at the asset boundary.
- Party/ballot-letter definitions with bilingual labels and color-review status.
- Geography records with totals, turnout, winner/margin, and dynamic ballot-letter vote columns converted into `partyVotes`.
- One optional official-envelope record that uses the same validated party-vote contract but has no map feature.
- `hiddenGeographyIds`, used to replace component localities with an active composite only in the relevant election.

The compiler recomputes winner/share fields from party totals and requires their sum to equal `valid_votes`. A documented K18 exclusion removes the trailing `ת. עדכון` source-metadata field, which otherwise looks numeric and was classified upstream as a ballot list. The exclusion is surfaced in `catalog.json`; any other mismatch fails the build.

Stable feature IDs are the join boundary:

- `stat2022:<YISHUV_STAT_2022>` for statistical areas.
- `loc:<SEMEL_YISHUV>` for localities.
- `composite:<key>` for reviewed election-specific composite municipalities.
- `custom:<key>` for reviewed synthetic geographies.
- `envelope:official` for the separate national envelope result; this ID intentionally has no geometry.

The browser validates every catalog/result payload before rendering it.

## Party registry plan

Ballot letters are not stable party identities across elections. Version 2 therefore generates deterministic placeholder colors by election plus ballot letter and marks them `provisional`. Reviewed names and colors can be added to `config/party-overrides.json` without touching the compiler or UI.

Before a public demo, create a reviewed party registry with:

1. Election-specific list identity and official Hebrew/English name.
2. Ballot letter.
3. Display color and provenance.
4. Optional cross-election lineage for mergers, splits, and renamed lists.

Cross-election lineage must not silently force one color onto distinct lists that reused a ballot letter.

## Geometry strategy

Current simplified source sizes are about 11 MB for statistical areas and 7 MB for localities. Version 2 uses pruned GeoJSON URLs because it keeps the pipeline simple and is adequate for local development.

The migration boundary for production is intentionally narrow: replace each catalog `geometryUrl` with a PMTiles/vector-tile source and adapt only `MapCanvas`. Result contracts, controls, localization, feature IDs, and panels remain unchanged.

Move to tiles before public launch if any of these remain true after compression and hosting tests:

- Statistical-area geometry transfer is above roughly 3–5 MB compressed.
- Mobile parsing or first interaction is visibly delayed.
- Lower-end mobile devices show memory pressure.

## Responsive and bilingual behavior

- CSS uses logical properties so the layout mirrors under RTL.
- The header and controls remain reachable above the map.
- Desktop uses floating side panels; mobile uses a full-width stacked control and result rail over the map.
- Language, election, and geography preferences are stored in one versioned, minimal local-storage record.
- Number and percent formatting use `he-IL` or `en-IL`.

## Coverage and integrity rules

- A polygon without mapped results remains visible but muted.
- The UI never interprets an absent polygon result as zero votes.
- Mapped coverage is shown for every election and is prominent while it remains partial.
- Coverage is mode-specific: locality mode is complete for the current geographic scope while statistical-area mode remains partial.
- Envelope votes are excluded from polygon coverage and remain visible through the separate national result control.
- Active composite localities hide their 2022 component features; inactive composites are hidden. The compiler rejects any payload that hides a feature while also publishing a result for it.
- Custom geometries remain in the canonical geometry asset but are filtered out of rendering and hit-testing unless the selected result asset contains their ID.
- Custom buckets and point-like West Bank settlement geographies render as the same fixed-size small marker; their source polygons, IDs, aggregation, and joins are unchanged. Detailed West Bank settlement geometries continue to render as polygons.
- Compiler errors are fatal for missing metadata, duplicate result IDs, invalid numbers, or missing required output files.

## Implementation phases

### Implemented foundation

- Isolated Vite/React/TypeScript app under `web/app/`.
- Atomic build-time asset compiler.
- Runtime Zod contracts and cached data client.
- Election and geography selectors.
- Hebrew/English and RTL/LTR support.
- Responsive map shell and details panel.
- Coverage disclosure and partial-data treatment.
- Complete locality aggregation with election-specific composite geometry replacement.
- Selectable envelope summary and full national ballot breakdown.
- MapLibre renderer with stable feature-state joins.
- Unit tests for contracts, compiler behavior, preferences, and localized controls.

### Before the first product demo

1. Complete/review the production statistical-area assignments and rerun the compiler.
2. Build and approve the party registry.
3. Add coloring controls for winner, selected-party share, turnout, and margin.
4. Add a searchable locality/area navigator and keyboard-accessible result list.
5. Add per-area contribution drill-down from `ballot_contributions` through a separate on-demand asset.
6. Decide whether custom buckets belong in both modes or in a third explicit mode.
7. Add end-to-end browser tests for election/mode/language switching and mobile breakpoints.
8. Measure GeoJSON transfer/parse cost on a representative phone; switch to PMTiles if needed.

### Public-release hardening

1. Add source/provenance and methodology pages in both languages.
2. Add downloadable mapped/unmapped tables and a clear “2022 geography applied to historical elections” explanation.
3. Add asset cache headers and immutable build-ID paths.
4. Add privacy-safe analytics only if there is a concrete product need.
5. Run accessibility, browser, performance, and data-reconciliation checks as release gates.

## Non-goals for this stage

- No browser-side election ingestion, geocoding, or assignment logic.
- No server database or API.
- No claim that inferred statistical areas are official historical polling boundaries.
- No public basemap dependency or API key.
- No attempt to invent party lineage while the registry is unresolved.
