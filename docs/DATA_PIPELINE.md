# Data Pipeline

Last updated: 2026-07-17

## Product Grain

The normalized fact table has one row per election result row / ballot
subdivision. Statistical-area assignment means the CBS area associated with
that ballot's voters.

## Raw Source Preparation

Election results are fetched normally:

```powershell
python scripts/fetch_election_results.py
```

Historical geography is a network preparation step, not a routine rebuild step:

```powershell
python scripts/fetch_cbs_historical_geography.py
python scripts/fetch_arcgis_feature_layer.py <FeatureServer-layer-url> <output.geojson>
```

The CBS downloader enumerates the public catalog, verifies expected byte lengths and file signatures, and writes a SHA-256 manifest. The generic ArcGIS downloader inventories object IDs and requests complete paged GeoJSON rather than trusting a truncated single query.

## Normal Run

```powershell
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
```

Use existing current and historical geography assets:

```powershell
python scripts/run_pipeline.py --skip-geographies
```

Pipeline order:

1. fetch K17-K25 official election-result rows;
2. build 2022 statistical areas, dissolved localities, composites, and custom geometry;
3. build 1995, 2008, and 2011 historical statistical geometry;
4. normalize election results;
5. build the reviewed locality/handling plan;
6. build official historical ballot-to-area assignments;
7. run the K20/K21 ArcGIS residual-partition audit and attach reviewed decisions;
8. build final row-level geography assignments with official historical
   assignments first and approved inferred assignments second;
9. aggregate statistical-area, locality, custom, envelope, contribution, and unresolved working outputs;
10. publish the committed `public-data/v1` ballot CSVs, aggregate tables,
    full-resolution geography ZIPs, metadata, checksums, and validation report.

## Assignment Precedence

`scripts/build_final_geography_assignments.py` applies:

1. envelope and reviewed non-geographic rules;
2. official CBS election-specific ballot crosswalk;
3. approved Tier A ArcGIS residual reconstruction;
4. unique historical-area locality fallback;
5. reviewed custom geography rules when no supported historical area exists;
6. unresolved historical assignment.

Historical unresolved rows are terminal unless a separate reviewed source
proves a unique exact assignment. The Tier A path is guarded by the reviewed
locality-election table: changed tier, row count, voter total, exact
row-to-area SHA-256 fingerprint, or area-level valid/invalid reconciliation
causes the build to fail instead of silently retaining an old inference.

## Historical Geometry

`scripts/build_historical_geographies.py`:

- reads CBS 1995, 2008, and 2011 geometry;
- preserves each historical election-area ID and does not treat demographic reference fields as unions;
- produces stable IDs `stat<vintage>:<combined-code>`;
- constructs the one missing 1995 Yehud-Newe Efrayim target from the official transition table;
- adds 30 exact-ID 2011 geometry supplements from the audited ArcGIS layers;
- creates separate display geometry with detailed West Bank footprints where a CBS source is a small or low-vertex proxy;
- never imports ArcGIS vote totals.

Current feature counts are 2,660 for 1995, 3,030 for 2008, and 3,113 for
2011. Display-only detailed replacements number 113, 102, and 117
respectively. The 1995/2008 display assets preserve shared boundaries without
independent polygon simplification, and replacement footprints are clipped
against historical neighbors.

`scripts/build_geographies.py` applies the same display-only source policy to current geometry. It writes separate official and `.display` 2022 assets, replaces 115 current locality/statistical proxies, and builds composites from the display geometry. Four West Bank settlements without a detailed source remain markers.

## Crosswalk Rules

`scripts/build_historical_ballot_assignments.py`:

- reads all nine official CBS ballot tables;
- interprets K17 tenths encoding;
- maps later decimal ballot subdivisions through their base ballot;
- respects cross-locality combined target IDs;
- preserves exact crosswalk area IDs; `Stat08_Unite` and `Stat11_Ref` are demographic references, not election-area unions;
- permits a locality fallback only when one historical area exists;
- permits the reviewed tribe/Hebron custom rows to use that fallback only for the 2011 vintage; K17/K18 retain their custom markers;
- emits explicit unresolved and missing-geometry statuses.

After geometry supplements, missing-geometry status is zero in every election.

## Main Outputs

- `data/processed/geographies/statistical_areas_1995.geojson`
- `data/processed/geographies/statistical_areas_2008.geojson`
- `data/processed/geographies/statistical_areas_2011.geojson`
- matching `.display.simplified.geojson`, `.metadata.csv`, and `.aliases.csv` files
- `data/processed/geographies/statistical_areas_2022.simplified.geojson`
- `data/processed/geographies/statistical_areas_2022.display.simplified.geojson`
- `data/processed/geographies/localities_2022_dissolved.simplified.geojson`
- `data/processed/geographies/localities_2022_dissolved.display.simplified.geojson`
- `data/processed/assignments/historical_ballot_crosswalk.csv`
- `data/processed/assignments/historical_ballot_assignments.csv`
- `data/processed/assignments/ballot_geography_assignments.csv`
- `data/processed/assignments/unresolved_statistical_area_assignment_rows.csv`
- `data/processed/audits/arcgis_assignment_reconstruction_candidates.csv`
- `data/processed/audits/arcgis_assignment_reconstruction_localities.csv`
- `data/processed/audits/arcgis_assignment_reconstruction_summary.json`
- `data/manual/arcgis_assignment_reconstruction_reviews.csv`
- `data/processed/public/election_summary.csv`
- `data/processed/public/statistical_area_results/*.csv`
- `data/processed/public/locality_results/*.csv`
- `data/processed/public/custom_geography_results/*.csv`
- `data/processed/public/envelope_results/*.csv`
- `data/processed/public/ballot_contributions/*.csv`
- `data/processed/public/unmapped_rows/*.csv`

The curated repository release is written separately so ignored working data
does not need to be committed:

- `public-data/v1/ballots/*.csv`
- `public-data/v1/aggregates/<mode>/*.csv`
- `public-data/v1/geographies/*.zip` and matching feature-metadata CSVs
- `public-data/v1/metadata/*.csv`
- `public-data/v1/manifest.{csv,json}` and `validation.json`

Every published polygon aggregate has a generic `geography_id` that joins to
the same property in its GeoJSON. The release builder rejects missing geometry
IDs, duplicate assignment rows, and party totals that do not reconcile to valid
votes. It also checks that all published Tier A row and voter counts equal the
reviewed decisions.

`custom_geography_results` rows carry `geography_mode`. This keeps K17/K18 custom statistical markers separate from the locality-mode tribe/Hebron aggregates after K19-K25 move onto exact 2011 statistical polygons.

## Verified Coverage

Verified from an offline rebuild on 2026-07-17:

| Election | Vintage | Statistical rows mapped | Pending rows | Mapped voter share | Locality share |
|---|---:|---:|---:|---:|---:|
| K25 | 2011 | 10,877 | 822 | 93.88% | 100% |
| K24 | 2011 | 11,161 | 958 | 94.27% | 100% |
| K23 | 2011 | 9,930 | 693 | 92.37% | 100% |
| K22 | 2011 | 9,919 | 612 | 93.63% | 100% |
| K21 | 2011 | 10,023 | 430 | 96.07% | 100% |
| K20 | 2011 | 10,051 | 61 | 99.30% | 100% |
| K19 | 2011 | 9,309 | 566 | 94.06% | 100% |
| K18 | 2008 | 8,740 | 519 | 94.13% | 100% |
| K17 | 1995 | 7,853 | 421 | 94.65% | 100% |

## Other Reviewed Inputs

- `data/manual/k17_eligible_voters.csv` restores K17 ordinary-register turnout
  and reconciles to 5,011,053 eligible voters. The public K17
  envelope/non-geographic denominator bucket is 4,087 after adding the separate
  3,569-person Gush Katif register; envelope turnout is intentionally hidden.
- `data/manual/composite_localities.csv` and `joined_locality_composites.csv` control election-specific locality display unions.
- `data/manual/locality_display_overrides.csv` controls reviewed historical names and visibility.
- `data/manual/arcgis_assignment_reconstruction_reviews.csv` approves 44 Tier A
  K20/K21 locality-election decisions. It never changes official vote values;
  it authorizes only the inferred ballot-to-area linkage.
- `data/manual/party_registry.csv` covers all election-specific result columns and the published display names are complete; `web/app/config/party-overrides.json` contains the still-partial reviewed color assignments.

See `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md`, `docs/LOCALITY_MODE.md`, and `docs/K17_ELIGIBLE_VOTER_RECOVERY.md` for detailed decisions.

## Web Build

```powershell
cd web/app
npm install
npm run check
npm run dev
```

The compiler writes schema-v3 assets under `web/app/public/data/v2/`. Each election declares its statistical-area vintage and mode-specific geometry URLs. The browser does no assignment or aggregation.
