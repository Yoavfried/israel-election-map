# Data Sources

Last updated: 2026-07-07

## Election Results

Official Knesset election results package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Current project scope starts at K16 / 2003 and runs through K25 / 2022.

Useful notes:

- K19-K25 include official locality-level resources.
- K16-K18 locality totals can be generated from ballot-level rows.
- Party columns are election-specific ballot letters and must not be treated as stable party IDs across elections.
- Some direct file downloads from `e.data.gov.il` may hit browser/security interstitials; datastore/API access was usable for the current investigation.

25th Knesset official results site:

https://votes25.bechirot.gov.il/

## 2022 Statistical Areas

Canonical raw polygon source for the project:

- `data/raw/ezorim_statistiim_2022.gdb`
- Esri File Geodatabase layer: `statistical_areas_2022`
- 3,842 polygon features.
- 3,739 unique locality/statistical-area pairs.
- 1,283 represented locality codes.
- 1,139 locality codes have exactly one `STAT_2022`.
- 144 locality codes have multiple `STAT_2022` values.
- Coordinate range is WGS84/browser-map compatible: roughly `34.27,29.49` to `35.89,33.33`.

Observed fields:

| Field | Meaning |
|---|---|
| `SEMEL_YISHUV` | Locality code |
| `SHEM_YISHUV` | Locality name in Hebrew |
| `SHEM_YISHUV_ENGLISH` | Locality name in English |
| `STAT_2022` | 2022 statistical-area code within locality |
| `YISHUV_STAT_2022` | Combined locality/statistical-area code |
| `ROVA` | Quarter/borough code where present |
| `TAT_ROVA` | Sub-quarter code where present |
| `COD_TIFKUD` | Function/type code |

Importer caveat:

- The JS `fgdb` reader used during investigation decoded Hebrew attribute values as mojibake. This is repairable by decoding those strings as Latin-1 bytes into UTF-8. The pipeline should prefer locality code matching and keep Hebrew names as display/crosswalk fields.

Previous local source:

- `data/raw/statistical-areas-2022.geojson`
- This was a partial export with 1,776 features and 407 locality codes.
- It was missing major localities such as Haifa, Beer Sheva, Netanya, Herzliya, Kfar Saba, Rahat, Nazareth, Eilat, Tayibe, Umm Batin, and Ar'ara-BaNegev.
- It is no longer a project source and should not be used.

Detailed audit:

- `docs/LOCALITY_STAT_LAYER_AUDIT.md`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`

Older official CBS statistical-area polygon layer from the 2008 census:

https://data.gov.il/api/3/action/package_show?id=statistical-area-2008

The 2008 layer remains a historical reference only. It should not replace the 2022 layer for the main product.

## 2022 Census Statistical Area Attributes

2022 census package:

https://data.gov.il/api/3/action/package_show?id=2022

Relevant resource:

- Resource ID: `9a9e085f-3bc8-41df-b15f-be0daaf99e30`
- Includes `LocalityCode`, `StatArea`, `StatAreaCmb`, and census measures.
- No geometry resource was found in the inspected package.

## Polling Places

Dedicated findings note:

- `docs/POLLING_PLACE_ADDRESSES.md`

Address sources currently available:

| Election | Address source | Source quality |
|---|---|---|
| K25 / 2022 | Official K25 polling-place XLSX in `data/raw` | High |
| K24 / 2021 | Archived official K24 polling-place XLSX | High |
| K23 / 2020 | Archived official K23 polling-place XLSX | High |
| K22 / 2019 Sep | Archived official K22 polling-place XLSX | High |
| K21 / 2019 Apr | Archived official K21 polling-place XLS | High |
| K20 / 2015 | Generic official `voting-polls` table | Medium; not election-specific |
| K19 / 2013 | Generic official `voting-polls` table | Medium; not election-specific |
| K18 / 2009 | `data/raw/archive_knesset18_kalpilist18.pdf` | High; election-specific scanned PDF with embedded OCR text layer, reconciled to 9,263 / 9,263 ordinary official result rows |
| K17 / 2006 | Address field inside official ballot-result file plus `data/raw/archive_knesset17_kalpies-list17-*.pdf` | High for addressed rows; targeted scan review recovered polling-place names for the 11 remaining multi-stat rows |
| K16 / 2003 | Generic official `voting-polls` table | Medium; not election-specific |

Generic official polling-place datastore resource:

https://data.gov.il/api/3/action/datastore_search?resource_id=68c4d7e8-2218-48ee-996f-2db2f72b2395

Observed generic-table fields include locality code, kalpi code, street, house number, polling-place description, regional committee, and district. It has no coordinates and no polygons.

K21 archived official source added on 2026-07-07:

| Raw file | Source capture | Notes |
|---|---|---|
| `data/raw/archive_knesset21_kalpies_full_report.xls` | `https://web.archive.org/web/20221202061209id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies_full_report.xls` | Primary K21 address source: locality code/name, kalpi number, polling-place address, place name, accessibility flags, eligible voters. |
| `data/raw/archive_knesset21_ballots_table.csv` | `https://web.archive.org/web/20221201110430id_/https://bechirot21.bechirot.gov.il/election/Documents/%D7%98%D7%91%D7%9C%D7%AA%20%D7%A7%D7%9C%D7%A4%D7%99%D7%95%D7%AA.csv` | K21 ballot table with polling-place cluster/name and metadata. |
| `data/raw/archive_knesset21_special_kalpies.xls` | `https://web.archive.org/web/20221205071624id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/special_kalpies21.xls` | K21 accessible/special ballot subset. |
| `data/raw/archive_knesset21_kalpies_committee_summary.xls` | `https://web.archive.org/web/20221202061132id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies21_b.xls` | K21 committee-level polling-place summary. |

K21 reconciliation:

- `archive_knesset21_kalpies_full_report.xls` has 10,459 unique locality-code + kalpi rows.
- The official K21 ballot-result datastore has 10,765 unique locality-code + kalpi rows.
- Direct address matching covers 10,459 rows.
- The 306 unmatched result rows are 305 official envelope rows plus one ordinary `נורית` [833] row, which is assignable through the single-stat locality shortcut.

New scanned/PDF sources added on 2026-07-06:

| Election | Raw file | Extraction status |
|---|---|---|
| K18 / 2009 | `data/raw/archive_knesset18_kalpilist18.pdf` | 304-page official polling-place list. It is scanned, but has an embedded OCR text layer with word coordinates. The current coordinate-based extractor writes a raw OCR table CSV and a resolved official-row CSV. Reconciliation matches 9,263 / 9,263 ordinary official result rows; the only official row without a physical polling-place address is the special non-geographic `מעטפות כפולות` row. |
| K17 / 2006 | `data/raw/archive_knesset17_kalpies-list17-1.pdf`, `data/raw/archive_knesset17_kalpies-list17-2.pdf` | Image-only scans. Full OCR is not available locally yet, but targeted visual extraction is practical. The 11 previously unresolved multi-stat rows were located in the scans and have polling-place names, although their address column is `0` rather than a street address. |

Reproducible K18 prototype:

```bash
python scripts/extract_k18_polling_places.py --validate
```

Validation writes:

- `data/processed/k18_polling_places_extracted_prototype.csv`
- `data/processed/k18_polling_places_resolved.csv`

## K23 Statistical Area Field

The K23 polling-place report includes an `אג"ס` field, but it still should not be joined directly to the 2022 statistical-area polygons.

Observed match against the FileGDB-derived 2022 locality/stat pairs:

- K23 rows with `אג"ס`: 10,631.
- Unique K23 locality+`אג"ס` pairs: 2,701.
- Unique 2022 locality+`STAT_2022` pairs in the FileGDB: 3,739.
- Row matches: 5,379 / 10,631, or 50.60%.
- Unique-pair matches: 1,053 / 2,701, or 38.99%.

Decision:

Keep K23 `אג"ס` as source metadata only. Use geocoded polling-place addresses plus point-in-polygon for multi-stat localities, and use the single-stat locality shortcut only where the 2022 layer has exactly one statistical area for the locality.

## Preferred Polygon Export Format

For project ingestion, keep the most complete official/raw source available. The current canonical source is the FileGDB because it contains the complete 2022 statistical-area layer we inspected.

If a source offers multiple formats:

1. GeoJSON is convenient for web development when it is a complete export.
2. FileGDB is acceptable as canonical raw input when it preserves the full official layer.
3. Shapefile is useful as a backup/archive.
4. KML is useful for inspection.
5. CSV/JSON are useful only if geometry is explicitly included.

Prefer WGS84 / EPSG:4326 when available.
