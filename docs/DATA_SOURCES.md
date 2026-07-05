# Data Sources

Last updated: 2026-07-05

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
| K21 / 2019 Apr | Generic official `voting-polls` table | Medium; not election-specific |
| K20 / 2015 | Generic official `voting-polls` table | Medium; not election-specific |
| K19 / 2013 | Generic official `voting-polls` table | Medium; not election-specific |
| K18 / 2009 | Generic official `voting-polls` table | Medium; not election-specific |
| K17 / 2006 | Address field inside official ballot-result file | High for addressed rows |
| K16 / 2003 | Generic official `voting-polls` table | Medium; not election-specific |

Generic official polling-place datastore resource:

https://data.gov.il/api/3/action/datastore_search?resource_id=68c4d7e8-2218-48ee-996f-2db2f72b2395

Observed generic-table fields include locality code, kalpi code, street, house number, polling-place description, regional committee, and district. It has no coordinates and no polygons.

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
