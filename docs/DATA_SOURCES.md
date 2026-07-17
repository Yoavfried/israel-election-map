# Data Sources

Last updated: 2026-07-17

## Election Results

Official Knesset election results package:

https://data.gov.il/api/3/action/package_show?id=26f9fa06-fcd7-4173-8df5-65797b63e857

Current project scope starts at K17 / 2006 and runs through K25 / 2022.

Useful notes:

- K19-K25 include official locality-level resources, but product totals should not depend on them.
- Locality totals are generated directly from normalized ballot rows and the reviewed locality crosswalk. They do not wait for statistical-area assignment.
- The recovered K17 result CSV contains voters, valid votes, and party votes but no ballot-level eligible-voter field. `data/manual/k17_eligible_voters.csv` restores the denominator for all 8,277 ordinary result rows from archived official reports and polling-place lists. The table passes key, turnout-constraint, and national-total checks, so locality/statistical-area turnout is now published. Envelope turnout remains unavailable rather than zero.
- Party columns are election-specific ballot letters and must not be treated as stable party IDs across elections.
- Some direct file downloads from `e.data.gov.il` may hit browser/security interstitials; datastore/API access was usable during investigation.
- K16 / 2003 is deferred until a usable election-specific polling-place address source is recovered.

25th Knesset official results site:

https://votes25.bechirot.gov.il/

## Party/List Registry

`data/manual/party_registry.csv` is the election-specific lookup used by the web compiler. Its key is `(election, source_column)`, because the same ballot letters can identify different lists in different elections. `ballot_letter` stores the official code separately; the known K19 source column `מרץ` is retained as the data key and corrected to official code `מרצ` for display. Structural coverage and published display-name review are complete; Wikipedia-link review is not.

The registry tracks all 309 K17-K25 source columns: 297 with at least one national vote and 12 zero-filled columns. The web payload excludes all 12 zero-filled lists after confirming that they did not run: K18 `פח`; K19 `זה` / `פך`; K20 `יך`; K21 `זנ` / `נך` / `ץז`; K22 `זן` / `כ` / `נץ`; K23 `זץ`; and K24 `רק`. The source-row validation and row counts are recorded in `web/app/config/party-overrides.json`. This leaves 297 published lists. Names come from the official Central Elections Committee national results pages for K21-K25, official results PDFs for K17-K20 where extractable, and official candidate-list publications for old zero-vote rows missing from the result PDFs. Positive-vote Wikipedia rows are matched within the same election by exact national vote total; duplicate totals are disambiguated by ballot code. Zero-vote article matches are explicit.

The builder keeps Hebrew links only when its checks identify a standalone party/list article. Redirects to a person or to the election article itself are rejected. English links come only from the Hebrew article's actual English interlanguage link, never from a guessed title. The current snapshot contains 165 Hebrew URLs and 150 English URLs, but the links and intentional blanks have not completed manual auditing. The party/list display names are complete independently of that link audit.

Party identity and presentation policy are deliberately separate. `web/app/config/party-overrides.json` gives reviewed official ballot letters a stable default color across elections and supports election-specific source-column name/color overrides. All K17-K25 published display names are reviewed; English presentation falls back to the reviewed Hebrew name where no separate English label is maintained. The later-election color table remains partial; unreviewed and mixed lists use deterministic placeholders. Reusing a color for the same letter is a display convention, not a claim that every list using that letter is the same party.

### K17 Eligible-Voter Recovery

The official data.gov.il package exposes only one K17 result resource, and its schema omits eligible voters. However, `data/raw/archive_knesset17_kalpies-list17-1.pdf` and `data/raw/archive_knesset17_kalpies-list17-2.pdf` print an eligible-voter count for each planned polling place, followed by a locality subtotal and polling-place count. The old official site also exposes national and 18 regional-committee totals. The official K17 memorandum records the national total of 5,014,622 eligible voters and states that the polling-station and regional protocols, together with the other documents used to determine the results, were deposited with the Interior Minister and State Archives.

The public PDFs make local recovery possible without individual voter-roll records. The production table is keyed only to the 8,277 ordinary result rows; planned polling places without a published result are not invented as zero-vote records. Final-report image OCR supplies 8,199 rows, 14 more are recovered from otherwise unaligned final-report lines, and one omitted zero-voter row is explicitly recorded as zero. The remaining 63 rows use the official planned list under exact subtotal or national reconciliation, including 49 Rehovot rows whose local final-report scan ends before their pages. The resulting ordinary-register total is exactly 5,011,053. The separate 3,569-person Gush Katif register brings the official national denominator to 5,014,622 but has no published ordinary result-row distribution, so it is not attached to map geographies. Full methods and exceptions are in `docs/K17_ELIGIBLE_VOTER_RECOVERY.md`.

## Historical Ballot Crosswalks And Geometry

The CBS public GIS catalog supplies direct ballot-to-statistical-area tables for every current-scope election:

- K17 -> 1995 areas
- K18 -> 2008 areas
- K19-K25 -> 2011 areas

It also supplies the corresponding 1995, 2008, and 2011 geometry plus transition tables. `scripts/fetch_cbs_historical_geography.py` downloads the selected files and records exact source URLs, byte lengths, and SHA-256 hashes in `data/raw/cbs_historical_geography/manifest.json`.

The two supplied ArcGIS FeatureServer layers are complete downloadable query services. They are used only for detailed display footprints and three explicit exact-ID geometry gaps. Current locality display geometry replaces 115 CBS point proxies from these sources; four settlements remain markers because no detailed footprint exists. The service description says the election output is not official and that some polygons are schematic, so its vote totals are never ingested. Full decisions are in `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md`.

## Current Locality Display Geometry (2022)

The 2022 FileGDB is canonical for current locality display geometry and for future elections that publish a direct 2022 ballot crosswalk. K17-K25 statistical results instead use their official 1995, 2008, or 2011 targets.

Canonical raw polygon source for the project:

- `data/raw/ezorim_statistiim_2022.gdb`
- Esri File Geodatabase layer: `statistical_areas_2022`
- 3,857 polygon features in the current raw FileGDB.
- 1,387 dissolved locality/display-footprint features.
- 1,242 dissolved locality/display-footprint features have exactly one statistical-area feature.
- 145 dissolved localities have multiple statistical-area features.
- 4 historical composite-municipality features and 96 joined-result display features are election-specific unions of 2022 component localities.
- Coordinate range is WGS84/browser-map compatible: roughly `34.27,29.49` to `35.89,33.33`.

The 1,387-feature layer deliberately preserves 58 polygons with no English locality label. Most are CBS no-jurisdiction land; two are the Neve Midbar and Al-Kasom regional-council footprints. Keeping them prevents false sea-colored gaps in locality mode. They carry no election result and are therefore neutral and non-interactive; Kinneret remains unfilled.

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

Previous local source:

- `data/raw/statistical-areas-2022.geojson`
- This was a partial export with 1,776 features and 407 locality codes.
- It was missing major localities and is no longer a project source.

Detailed audit:

- `docs/LOCALITY_STAT_LAYER_AUDIT.md`
- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`

Locality geometry decision:

- The current implementation derives locality polygons by dissolving/unioning this 2022 statistical-area layer by `SEMEL_YISHUV` / `SHEM_YISHUV`.
- Locality mode should render the dissolved locality as a single visual polygon or multipolygon with no internal statistical-area boundary lines.
- `data/manual/composite_localities.csv` defines the four source municipalities that require an election-specific union of multiple 2022 localities: באקה-ג'ת, עיר כרמל, שגור, and שער שומרון.
- `data/manual/joined_locality_composites.csv` defines source-backed host/result unions for K19, K20, and five reviewed K25 cases. The canonical result remains under the published host and is aliased to the union only in that election's web payload.
- A separate locality polygon source is not required for the current implementation.

Official 2022 locality metadata used for the no-standalone-result explanation audit:

- CBS locality workbook: https://www.cbs.gov.il/he/publications/DocLib/2019/ishuvim/bycode2022.xlsx
- CBS locality-file definitions: https://www.cbs.gov.il/he/publications/DocLib/2019/ishuvim/intro.pdf

The workbook supplies the reviewed locality form and population snapshot stored in `data/manual/locality_result_presence_reviews.csv`. The CBS definitions distinguish an institutional locality from a `place`, which is populated but not counted as an independent locality population. These classifications describe the 2022 feature; they do not by themselves prove that it had a separate voter register in an older election. As a completeness check, all 56 special-purpose geometry records in the 1700-1799 range are present in the workbook and have blank 2022 population; the additional 48 regional-council and 56 no-jurisdiction features are not ordinary locality candidates.

Small voter registers can be joined to a nearby polling area. Section 70 of the official Knesset election law permits joining a polling area with fewer than 100 eligible voters to the nearest reasonable polling area: https://www.gov.il/apps/elections/elections-knesset-17/heb/law/ElectionLaw.html. The published host result is a single secret-ballot aggregate and cannot be split back into locality-specific party totals. Where the source establishes the host, locality mode may display the host and attached 2022 polygons as one named union for that election.

Context sources for the three reviewed features with no ordinary K17-K25 polling-list row:

- `כפר עבודה`: the CBS workbook classifies it as institutional; an archived State Comptroller report describes the site as a youth institution: https://library.mevaker.gov.il/sites/DigitalLibrary/Documents/1950-2008/1960/1960-HAMOATZA_HAMEKOMIT_TEL_MOND.pdf
- `צופייה`: the CBS workbook classifies it as a `place` without a separate population; official planning material describes Maon Zofiyya as a Youth Protection residence for girls: https://apps.land.gov.il/IturTabotData/takanonim/merkaz/4050268.pdf
- `ידידה`: the CBS workbook classifies it as institutional, and the institution describes itself as a residential system for adults with special needs: https://www.yedida-h.co.il/. Unlike the two youth facilities, this context does not establish why no separate voter-list row exists; the residents may be registered elsewhere, but that remains an inference.

Official CBS 2008 statistical-area package:

https://data.gov.il/api/3/action/package_show?id=statistical-area-2008

The 2008 layer is active K18 statistical geometry. K17 uses 1995, K19-K25 use 2011, and locality mode continues to use dissolved 2022 display geometry.

## Historical AGS QA

Dedicated note:

- `docs/AGS_HISTORICAL_QA.md`

The official CBS 1995, 2008, and 2011 geometry and all K17-K25 ballot crosswalks are now downloaded and integrated. Source AGS is interpreted as ballot/voter assignment, not as the polling-place building's containing area.

The K23 polling-place report remains the only inspected address source with an explicit AGS field. Production assignment uses the separate official CBS ballot-to-2011-area table; the address AGS remains diagnostic metadata.

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
| K23 / 2020 | Archived official K23 polling-place XLSX | High; includes AGS source metadata for 8,031 rows |
| K22 / 2019 Sep | Archived official K22 polling-place XLSX | High |
| K21 / 2019 Apr | Archived official K21 polling-place XLS | High |
| K20 / 2015 | `data/raw/archive_knesset20_tell_the_polls_9_3.xls` | High; election-specific archived official XLS |
| K19 / 2013 | `data/raw/archive_knesset19_all_stations.pdf` | High; election-specific archived official Excel-generated PDF |
| K18 / 2009 | `data/raw/archive_knesset18_kalpilist18.pdf` | High; election-specific scanned PDF with embedded OCR text, reconciled to every ordinary official result row |
| K17 / 2006 | Address field inside official ballot-result file plus `data/raw/archive_knesset17_kalpies-list17-*.pdf` and `data/manual/manual_k17_scanned_place_names.csv` | High for addressed rows; direct scan review recovered 456 polling-place names, including all 344 rows formerly described as locality-only/no-place |

Generic official polling-place datastore resource:

https://data.gov.il/api/3/action/datastore_search?resource_id=68c4d7e8-2218-48ee-996f-2db2f72b2395

The generic resource has locality code, kalpi code, street, house number, polling-place description, regional committee, and district. It has no coordinates and no polygons. Because it is not election-specific, it is kept as research-only fallback metadata and should not be counted as production address coverage without explicit validation.

### Archived Official Sources

| Election | Local raw file | Source capture | Notes |
|---|---|---|---|
| K24 | `data/raw/archive_knesset24_kalpies_report_tofes_b_18_3_21.xlsx` | `https://web.archive.org/web/20211106033352id_/https://bechirot24.bechirot.gov.il/election/Kneset24/Documents/%D7%9B%D7%A0%D7%A1%D7%AA%2024/kalpies_report_tofes_b_18.3.21.xlsx` | Primary K24 address source; 12,127 rows with address/place coverage. |
| K23 | `data/raw/archive_knesset23_kalpies_report_19_1_20_1.xlsx` | `https://web.archive.org/web/20210119095351id_/https://bechirot23.bechirot.gov.il/election/Kneset20/Documents/%D7%9B%D7%A0%D7%A1%D7%AA%2023/kalpies_report_19_1_20_1.xlsx` | Primary K23 address source; 10,631 rows with address/place coverage and AGS metadata on 8,031 rows. |
| K22 | `data/raw/archive_knesset22_kalpies_report_tofes_b_6th_edition_15_9.xlsx` | `https://web.archive.org/web/20191113005230id_/https://bechirot22.bechirot.gov.il/election/Kneset20/Documents/%D7%9B%D7%A0%D7%A1%D7%AA%2022/kalpies_report_tofes_b_6th_edition_15_9.xlsx` | Primary K22 address source; 10,543 rows with address/place coverage. |
| K21 | `data/raw/archive_knesset21_kalpies_full_report.xls` | `https://web.archive.org/web/20221202061209id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies_full_report.xls` | Primary K21 address source. |
| K21 | `data/raw/archive_knesset21_ballots_table.csv` | `https://web.archive.org/web/20221201110430id_/https://bechirot21.bechirot.gov.il/election/Documents/%D7%98%D7%91%D7%9C%D7%AA%20%D7%A7%D7%9C%D7%A4%D7%99%D7%95%D7%AA.csv` | K21 ballot table with polling-place cluster/name and metadata. |
| K21 | `data/raw/archive_knesset21_special_kalpies.xls` | `https://web.archive.org/web/20221205071624id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/special_kalpies21.xls` | K21 accessible/special ballot subset. |
| K21 | `data/raw/archive_knesset21_kalpies_committee_summary.xls` | `https://web.archive.org/web/20221202061132id_/https://bechirot21.bechirot.gov.il/election/Kneset20/Documents/kalpies21_b.xls` | K21 committee-level polling-place summary. |
| K20 | `data/raw/archive_knesset20_tell_the_polls_9_3.xls` | `https://web.archive.org/web/20160330183320id_/http://bechirot.gov.il/election/Kneset20/Documents/TellThePolls.9.3.xls` | Primary K20 address source; ordinary rows fully reconciled after split-row matching. |
| K19 | `data/raw/archive_knesset19_all_stations.pdf` | `https://web.archive.org/web/20130123205035id_/http://www.bechirot.gov.il:80/elections19/heb/about/AllStations.pdf` | Primary K19 address source; Excel-generated PDF with extractable table text. |
| K18 | `data/raw/archive_knesset18_kalpilist18.pdf` | Local raw archive file | Official polling-place list scan with embedded OCR text layer. |
| K17 | `data/raw/archive_knesset17_kalpies-list17-1.pdf`, `data/raw/archive_knesset17_kalpies-list17-2.pdf` | Local raw archive files | Image-only scans used for targeted review of rows with empty address fields. |

### Deferred K16 Research

K16 / 2003 is not part of current product scope.

Checked evidence:

- Official K16 datastore: 7,886 result rows, no address or polling-place name columns.
- Archived K16 Knesset pages: location lookup existed via voter notices, public notices, and phone information centers.
- Old K16 result UI: exposes some polling-place names, but no street addresses and no complete national archived list.
- Wayback filename/path searches did not find a national K16 polling-place list, XLS, CSV, or PDF.

K16 can be reconsidered later if a real election-specific source is found.

## K23 Statistical Area Field

The K23 polling-place report includes an AGS field, but production assignment does not join that address report to 2022 polygons.

Production uses the separate official `kalpi_March2020_stat2011.xlsx` crosswalk and 2011 geometry. This directly maps ballot rows to voter statistical areas without treating the polling-place building as voter geography.

Decision:

Keep the address-report AGS as diagnostic metadata. Use the official ballot crosswalk for election assignment.

## Preferred Polygon Export Format

For project ingestion, keep the most complete official/raw source for each vintage. Canonical inputs are the CBS 1995 archive, 2008 FileGDB, 2011 FileGDB, and 2022 FileGDB. ArcGIS layers are derivative display/supplement sources with explicit provenance, not replacements for CBS vote totals.

If a source offers multiple formats:

1. GeoJSON is convenient for web development when it is a complete export.
2. FileGDB is acceptable as canonical raw input when it preserves the full official layer.
3. Shapefile is useful as a backup/archive.
4. KML is useful for inspection.
5. CSV/JSON are useful only if geometry is explicitly included.

Prefer WGS84 / EPSG:4326 when available.
