# K17 locality-only polling-place recovery

Last updated: 2026-07-15

## Correction

The earlier statement that 36 units covering 344 ballot boxes had no polling-place name was wrong.

- The normalized K17 digital result rows contained only the locality in the address field and did not carry a separate polling-place value.
- The original K17 polling-place scans do contain a far-left `מקום הקלפי` column.
- Direct visual transcription recovered a non-empty polling-place value for every one of the 344 rows.
- All 344 rows are K17. None is K18 and no K18 value was copied into K17.

The 36 count was one locality-only query unit per locality, not 36 individual ballot boxes. The exact 344-row inventory, including source row ID, station, scan part/page, and transcribed place, is in `docs/K17_LOCALITY_ONLY_SCAN_RECOVERY.csv`. Its `source_kalpi` field preserves the K17 digital file's scaled notation: `10` is printed station 1, `81` is printed station 8.1, and so on.

## Verification

| Check | Result |
|---|---:|
| Formerly affected rows | 344 |
| Elections represented | K17 only |
| Localities represented | 36 |
| Blank transcribed place values | 0 |
| Rows missing from the canonical manual source | 0 |
| Transcription mismatches between the audit export and manual source | 0 |
| Current locality-only/no-place units after rebuild | 0 |

The canonical reviewed source now contains 456 K17 scan transcriptions in total, with no duplicate source-row keys and no blank place values. The 344 rows in this document are the formerly misclassified locality-only subset.

## Affected Polls

| Locality | K17 ballot rows |
|---|---:|
| אבו סנאן | 9 |
| אורנית | 6 |
| אכסאל | 9 |
| אעבלין | 10 |
| ביר אל-מכסור | 6 |
| בית ג'ן | 8 |
| ג'לג'וליה | 5 |
| ג'סר א-זרקא | 8 |
| דבוריה | 6 |
| דייר חנא | 7 |
| חורה | 4 |
| טורעאן | 8 |
| טירה | 18 |
| טמרה | 24 |
| יפיע | 13 |
| ירכא | 9 |
| כאבול | 9 |
| כסיפה | 3 |
| כפר יאסיף | 6 |
| כפר כנא | 13 |
| כפר מנדא | 9 |
| כפר קאסם | 13 |
| לקיה | 4 |
| מגאר | 16 |
| מג'דל שמס | 1 |
| נחף | 7 |
| סח'נין | 20 |
| עין מאהל | 8 |
| עראבה | 15 |
| ערערה | 9 |
| ערערה-בנגב | 3 |
| קלנסווה | 11 |
| רהט | 2 |
| ריינה | 10 |
| שגור | 9 |
| שפרעם | 26 |
| **Total** | **344** |

## Station Coverage Check

The scan station lists were also compared with the digital K17 result rows. The reviewed localities reconcile except for one independent source-data gap:

- The Maghar scan (`part 1 page 44`) lists printed stations 1 through 20.
- The digital K17 result table contains only stations 1 through 16 (`source_kalpi` 10 through 160 in that file's scaled notation).
- Printed stations 17, 18, 19, and 20 are absent result rows. They are not rows with a missing polling-place field and therefore cannot be repaired by adding an address to an existing result row.

K18 station numbers were used only as review leads during the investigation. The final recovery values all come directly from the K17 scans.

## Files

- `data/manual/manual_k17_scanned_place_names.csv`: canonical direct K17 scan transcriptions.
- `docs/K17_LOCALITY_ONLY_SCAN_RECOVERY.csv`: exact 344-row recovery inventory.
- `data/processed/addresses/polling_place_locality_only_no_place_units.csv`: contains zero rows because the current unresolved count is zero.
- `data/processed/addresses/k17_locality_only_k18_candidates.csv`: now header-only because no current K17 locality-only/no-place scope remains.
- `scripts/compare_k17_locality_only_to_k18.py`: reproducible current-scope comparison; its current result is zero rows.
