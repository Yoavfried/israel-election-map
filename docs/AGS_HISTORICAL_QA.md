# AGS Historical QA

Last updated: 2026-07-15

## Purpose

The intended source-AGS QA check was:

> source polling-place row has an official AGS/statistical-area code -> geocoded coordinate falls inside the polygon for that same historical AGS layer

This check is now treated as diagnostic only. It can flag suspicious geocoder output, but it cannot certify that the polling-place building is inside the row's AGS. A polling-place building can serve voters from more than one source AGS, and the same uncertainty can exist even when a deduplicated address currently has only one observed source AGS.

This QA does not replace the product assignment target. The product still maps K17-K25 onto 2022 statistical-area polygons by polling-place building coordinate where address geocoding is needed.

## Current Source Findings

Local raw polling-place/result sources inspected on 2026-07-09:

The local CSV/XLS/XLSX header audit found exactly one AGS-like field under `data/raw`: K23 `archive_knesset23_kalpies_report_19_1_20_1.xlsx` has `AGS`/`source_ags` source metadata (`אג"ס` in the workbook). The other local workbooks are slimmer polling-place/address reports such as `tofes_b` or current kalpi-place lists. The current normalizer attempts to preserve an AGS field for every Excel source when that column exists, so the current evidence points to source-file coverage rather than the pipeline dropping AGS during cleaning.

| Election | Local source checked | Explicit AGS field found? | Notes |
| --- | --- | --- | --- |
| K25 / 2022 | `election-25_kalpi-places_kalpies_list_10_7_nagish.xlsx`; official result CSV | No | Has `סמל רכוז`/`ריכוז`, but not AGS in inspected headers. Because K25 happened in 2022, we still need to verify whether an official K25 AGS report exists and whether its AGS aligns to 2022 polygons. |
| K24 / 2021 | `archive_knesset24_kalpies_report_tofes_b_18_3_21.xlsx`; official result CSV | No | Has `סמל רכוז`/`ריכוז`, but not AGS in inspected headers. |
| K23 / 2020 | `archive_knesset23_kalpies_report_19_1_20_1.xlsx`; official result CSV | Yes | Polling-place report has `אג"ס` for 8,031 of 10,631 rows. `locality + kalpi` maps uniquely to AGS in that file. |
| K22 / 2019 Sep | `archive_knesset22_kalpies_report_tofes_b_6th_edition_15_9.xlsx`; official result CSV | No | Has `סמל רכוז`/`ריכוז`, but not AGS in inspected headers. |
| K21 / 2019 Apr | `archive_knesset21_kalpies_full_report.xls`, `archive_knesset21_ballots_table.csv`, official result CSV | No | Extra ballot table has `מיקום ע"ג מפה`, but inspected values include `חסר`; no AGS field found. |
| K20 / 2015 | `archive_knesset20_tell_the_polls_9_3.xls`; official result CSV | No | No AGS field found in inspected headers. |
| K19 / 2013 | `archive_knesset19_all_stations.pdf`; official result CSV | Not found yet | Existing parser/source docs expose polling-place address/place fields, not AGS. A deeper PDF text pass can be done if needed. |
| K18 / 2009 | `archive_knesset18_kalpilist18.pdf`; official result CSV | Not found yet | Existing parser/source docs expose polling-place address/place fields, not AGS. |
| K17 / 2006 | official result CSV plus scanned PDFs | No in result CSV | Result CSV has address text but no AGS. Scanned PDFs were used for targeted missing-place recovery, not AGS extraction. |

Important: `ריכוז` / `סמל רכוז` is not AGS. K23 proves this: within K23, `locality + concentration` is ambiguous in 741 AGS-bearing cases. `locality + kalpi` maps uniquely to the AGS values in the K23 report, but that only helps when the election-specific report contains AGS.

## Historical Polygon Source

The official CBS 2008 statistical-area package exists on data.gov.il:

- Package API: `https://data.gov.il/api/3/action/package_show?id=statistical-area-2008`
- Resource URL from the API: `https://e.data.gov.il/dataset/6b729165-dc9c-49b3-afc6-eceabd8fef70/resource/3b88cb58-62cd-43ea-9156-7b81ead557b1/download/50400-2008.7z`

Attempted command-line download on 2026-07-08 returned a 42 KB HTML browser-challenge page, not the 7z archive. The bad local file was deleted and should not be treated as raw data.

Next source action: obtain the actual `50400-2008.7z` archive manually in a browser or through another trusted download path, then inspect its geometry fields and AGS identifiers.

## QA Decision

Do not use source AGS as a hard accept/reject gate for geocoded polling-place coordinates. A source-AGS pass is supportive context only. A source-AGS fail is a manual-review signal, not proof that the geocoder is wrong, because the source AGS may describe the voters/kalpi assignment rather than the physical polling-place building.

The hard automated spatial gate remains the expected 2022 dissolved locality polygon, plus final point-in-2022-statistical-area assignment for reviewed coordinates. AGS diagnostics can be kept in the review queue, but they should not override locality validation or manual review.

## Implemented Source-AGS Plumbing

As of 2026-07-09:

- `scripts/normalize_polling_places.py` preserves K23 `אג"ס` as `source_ags` and the concentration code as `source_concentration_code`.
- `scripts/build_geocoding_input.py` carries those fields into `geocoding_input.csv`.
- `scripts/build_geocoding_work_units.py` carries those fields into `geocoding_work_unit_rows.csv` and aggregates them into `geocoding_work_units.csv`.
- `scripts/validate_geocode_candidate_source_ags.py` checks candidate points against a supplied statistical-area layer.

The current rebuilt work-unit table contains 2,367 units with source AGS metadata, including 2,071 clean numbered-address units.

Current limitation: the only statistical-area polygon layer present locally is 2022. The validator therefore currently checks K23 source AGS against 2022 `stat_2022` where the source locality/AGS pair exists in that layer. This is diagnostic screening only; it is not final old-boundary QA and is not a hard geocode validation rule.

Current full Photon candidate result against the 2022 layer:

| Validation status | Units |
| --- | ---: |
| `single_source_ags_candidate_inside_expected_ags` | 473 |
| `single_source_ags_candidate_outside_expected_ags` | 567 |
| `single_source_ags_not_in_stat_layer` | 496 |
| `multi_source_ags_candidate_inside_one_expected_ags` | 267 |
| `multi_source_ags_candidate_outside_expected_ags` | 259 |
| `multi_source_ags_not_in_stat_layer` | 204 |
| `multi_source_ags_candidate_outside_stat_area` | 1 |
| `candidate_not_matched` | 100 |
| `candidate_outside_stat_area` | 2 |
| `no_source_ags` | 4,827 |

K23 source AGS is not one-to-one per deduplicated address: 1,613 AGS-bearing work units have one source AGS value, while 756 have multiple source AGS values because multiple kalpies can share the same polling-place address. This proves `source_ags` is not always the polling-place building's containing AGS. It also means single-source-AGS rows cannot be assumed safe: they may simply be cases where the same building currently has only one observed source AGS in our scoped data. Treat all source-AGS checks as review diagnostics rather than geocode pass/fail rules.

Review buckets after AGS QA should be:

| Bucket | Meaning |
| --- | --- |
| `historical_ags_pass` | Candidate coordinate falls inside the official historical AGS polygon for the source row. Supportive context, not auto-accept. |
| `historical_ags_fail` | Candidate coordinate has source AGS but does not fall inside that AGS polygon. Manual-review signal, not automatic rejection. |
| `no_source_ags` | Source row has no known AGS key, so only locality/stat-area/current checks are available. |
| `missing_historical_polygon` | Source has AGS but the matching historical polygon layer is not available or cannot be matched. |
| `known_crosswalk_exception` | Apparent wrong-locality case explained by reviewed split/merge/name-change/custom-bucket handling. |

## Implementation Plan

1. Preserve source AGS metadata in normalized polling-place/address rows where available, starting with K23.
2. Add a historical AGS polygon loader once the 2008 archive is available and inspected.
3. Build `geocode_candidate_historical_ags_validation.csv`: candidate coordinate -> historical AGS point-in-polygon result.
4. Combine locality validation and historical AGS validation into a review queue.
5. Only after this QA, produce the real bad-match list for manual review or rejection.
