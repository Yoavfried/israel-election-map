# AGS Historical QA

Last updated: 2026-07-08

## Purpose

The strongest available QA for geocoded polling-place coordinates is not only checking that a point falls inside the expected 2022 locality. The stronger check is:

> source polling-place row has an official AGS/statistical-area code -> geocoded coordinate falls inside the polygon for that same historical AGS layer

If this passes, it is strong evidence that the geocoded point is not merely in the correct municipality, but in the correct small-area geography used by the election/polling-place source.

This QA does not replace the product assignment target. The product still maps K17-K25 onto 2022 statistical-area polygons. Historical AGS QA is a validation layer for candidate geocodes.

## Current Source Findings

Local raw polling-place/result sources inspected on 2026-07-08:

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

Do not classify Photon `outside_expected_locality` results as definitively bad until historical AGS QA has been applied where possible.

Review buckets after AGS QA should be:

| Bucket | Meaning |
| --- | --- |
| `historical_ags_pass` | Candidate coordinate falls inside the official historical AGS polygon for the source row. Strong candidate for acceptance. |
| `historical_ags_fail` | Candidate coordinate has source AGS but does not fall inside that AGS polygon. Strong reject/manual review. |
| `no_source_ags` | Source row has no known AGS key, so only locality/stat-area/current checks are available. |
| `missing_historical_polygon` | Source has AGS but the matching historical polygon layer is not available or cannot be matched. |
| `known_crosswalk_exception` | Apparent wrong-locality case explained by reviewed split/merge/name-change/custom-bucket handling. |

## Implementation Plan

1. Preserve source AGS metadata in normalized polling-place/address rows where available, starting with K23.
2. Add a historical AGS polygon loader once the 2008 archive is available and inspected.
3. Build `geocode_candidate_historical_ags_validation.csv`: candidate coordinate -> historical AGS point-in-polygon result.
4. Combine locality validation and historical AGS validation into a review queue.
5. Only after this QA, produce the real bad-match list for manual review or rejection.
