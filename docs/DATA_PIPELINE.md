# Data Pipeline

Last updated: 2026-07-18

## Product Grain

The normalized fact table has one row per official election-result row or
ballot subdivision. A statistical-area assignment identifies the area served by
that ballot register. The browser performs no assignment or aggregation.

## Source Preparation

```powershell
python scripts/fetch_cbs_historical_geography.py
python scripts/fetch_election_results.py
python scripts/run_pipeline.py
```

Historical geometry and ArcGIS downloads are preparation inputs rather than
routine web-build dependencies. The CBS downloader inventories the public
catalog, verifies file signatures and expected lengths, and writes a SHA-256
manifest. The generic ArcGIS downloader pages through all object IDs instead of
trusting a potentially truncated query.

Reuse existing generated geography with:

```powershell
python scripts/run_pipeline.py --skip-geographies
```

## Stage Order

`scripts/run_pipeline.py` executes:

1. fetch K17-K25 official result rows;
2. build 2022 statistical areas, current localities, composites, and custom geometry;
3. build 1995, 2008, and 2011 historical geometry;
4. normalize election results;
5. build the reviewed locality and special-handling plan;
6. normalize the nine official CBS ballot crosswalks;
7. audit source schemas and catalog completeness;
8. audit and stage direct K23 CEC AGS assignments;
9. audit K20/K21 ArcGIS residual candidates and reviewed decisions;
10. audit and stage official CBS stable-ballot assignments;
11. build final row-level assignments in evidence-precedence order;
12. classify every unresolved row and historical polygon coverage state;
13. aggregate statistical-area, locality, custom, envelope, contribution, and unresolved outputs;
14. build the committed schema-v2 `public-data/v1` release and validation report.

## Assignment Precedence

`scripts/build_final_geography_assignments.py` applies:

1. envelope and reviewed non-geographic rules;
2. reviewed historical overrides for specifically contradicted direct targets;
3. official CBS election-specific crosswalks;
4. direct official K23 CEC AGS;
5. approved exact ArcGIS residual reconstruction;
6. official CBS stable-ballot propagation with same-vintage consensus;
7. a locality fallback only when one historical area exists;
8. reviewed custom geography where no supported historical area exists;
9. unresolved historical assignment.

The output adds three general provenance fields:

- `assignment_evidence_class` groups the evidence hierarchy;
- `assignment_confidence` records `authoritative`, `high`, `moderate`,
  `not_applicable`, or `unresolved`;
- `assignment_is_synthetic_link` identifies inferred area links without
  implying synthetic vote data.

Synthetic-link builds are guarded by reviewed fingerprints and expected row and
voter totals. A changed mapping, evidence tier, or source reconciliation causes
the build to fail. Approximate arithmetic is not an assignment method.

## Historical Evidence Audits

### Source Fields

`scripts/audit_election_source_geography_fields.py` verifies that all nine CBS
crosswalks expose area fields, inventories the seven stable-ballot workbooks,
and checks archived CEC polling-place reports. Only K23 contains AGS among the
K20-K25 reports available locally.

### K23 AGS

`scripts/audit_k23_cec_stat_area_assignments.py` validates direct AGS against
existing assignments before staging pending rows. It requires a unique area,
withholds contradictions, and writes candidate, conflict, coverage, validation,
and summary artifacts.

### Stable Ballots

`scripts/audit_stable_ballot_assignments.py` builds components from the official
transition workbooks. It accepts a pending ballot only when all assigned
same-vintage members agree on one area. Decimal subdivisions share the
historical base ballot. Conflicts and cross-vintage transitions remain
published audit records rather than assignments.

### ArcGIS Residuals

`scripts/audit_arcgis_assignment_reconstruction.py` first classifies each
FeatureServer feature as a detailed area, a valid single-area locality total, or
a dissolved locality aggregate. Source metadata says Arab-locality areas were
merged, so dissolved aggregates cannot support detailed assignments.

Only reviewed, unique, exact residual partitions are staged. The current result
is nine K21 rows and zero K20 rows. No ArcGIS party or vote value enters the
official election fact table.

### Gap And Polygon Audit

`scripts/audit_historical_assignment_gaps.py` classifies all 5,605 pending rows,
compares K20/K21 detailed ArcGIS polygons where applicable, and writes
election-level polygon coverage and cross-election persistence tables.
Demographic population is labeled as a proxy and never treated as an
election-specific eligibility count.

## Historical Geometry

`scripts/build_historical_geographies.py`:

- reads CBS 1995, 2008, and 2011 geometry;
- preserves distinct election-area IDs and ignores demographic reference fields
  as union instructions;
- produces stable IDs `stat<vintage>:<combined-code>`;
- constructs one 1995 target from the official transition key;
- adds 32 exact-ID 2011 geometry supplements from audited ArcGIS layers;
- creates separate display geometry with detailed footprints where canonical
  shapes are schematic;
- clips historical replacements against neighbors and uses markers for
  materially overlapping non-exclusive supplements;
- never imports ArcGIS election totals.

Canonical feature counts are 2,660 for 1995, 3,030 for 2008, and 3,115 for
2011. `scripts/build_geographies.py` separately builds the 3,857-feature 2022
package for current locality display and future direct-crosswalk elections.

## Main Working Outputs

- `data/processed/geographies/statistical_areas_<vintage>.geojson`
- matching display GeoJSON, metadata CSV, and alias CSV files
- `data/processed/assignments/historical_ballot_crosswalk.csv`
- `data/processed/assignments/historical_ballot_assignments.csv`
- `data/processed/assignments/ballot_geography_assignments.csv`
- `data/processed/assignments/unresolved_statistical_area_assignment_rows.csv`
- `data/processed/audits/election_source_geography_field_audit.*`
- `data/processed/audits/k23_cec_ags_*`
- `data/processed/audits/stable_ballot_*`
- `data/processed/audits/arcgis_assignment_reconstruction_*`
- `data/processed/audits/historical_assignment_gap_*`
- `data/processed/audits/historical_polygon_*`
- `data/processed/public/<mode>/*.csv`

The curated repository release is written separately:

- `public-data/v1/ballots/*.csv`
- `public-data/v1/aggregates/<mode>/*.csv`
- `public-data/v1/geographies/*.zip` and feature-metadata CSVs
- `public-data/v1/metadata/*.csv`
- `public-data/v1/metadata/assignment-provenance/*`
- `public-data/v1/manifest.{csv,json}`
- `public-data/v1/validation.json`

The release builder rejects duplicate ballot rows, actual-voter totals that do
not equal valid plus invalid votes, missing geometry joins, party totals that do
not equal valid votes, and provenance totals that do not match the reviewed
decisions.

## Verified Coverage

Verified from the offline rebuild on 2026-07-18:

| Election | Vintage | Supported rows | Pending rows | Supported voter share | Locality share |
|---|---:|---:|---:|---:|---:|
| K17 | 1995 | 7,859 | 415 | 94.68% | 100% |
| K18 | 2008 | 8,740 | 519 | 94.13% | 100% |
| K19 | 2011 | 9,311 | 564 | 94.08% | 100% |
| K20 | 2011 | 9,521 | 591 | 93.31% | 100% |
| K21 | 2011 | 9,854 | 598 | 94.51% | 100% |
| K22 | 2011 | 9,920 | 611 | 93.64% | 100% |
| K23 | 2011 | 10,004 | 619 | 93.06% | 100% |
| K24 | 2011 | 11,248 | 871 | 94.70% | 100% |
| K25 | 2011 | 10,882 | 817 | 93.92% | 100% |

## Other Reviewed Inputs

- `data/manual/k17_eligible_voters.csv` restores K17 ordinary-register turnout
  and reconciles to 5,011,053 eligible voters.
- `data/manual/composite_localities.csv` and
  `data/manual/joined_locality_composites.csv` control election-specific
  locality display unions.
- `data/manual/locality_display_overrides.csv` controls reviewed historical
  names and visibility.
- `data/manual/historical_stat_area_overrides.csv` records five reviewed K19
  target corrections.
- `data/manual/arcgis_assignment_reconstruction_reviews.csv` records approved
  and rejected ArcGIS decisions.
- `data/manual/party_registry.csv` covers every election-specific result column;
  map colors remain presentation configuration under `web/app/`.

## Web Build

```powershell
cd web/app
npm install
npm run check
npm run dev
```

The compiler writes schema-v3 frontend assets under `web/app/public/data/v2/`.
That browser schema is separate from the public download release's schema-v2
ballot tables.
