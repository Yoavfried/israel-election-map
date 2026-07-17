# K17 Eligible-Voter Recovery

Last updated: 2026-07-16

## Purpose

The official K17 result file contains turnout numerators and party votes but omits the eligible-voter denominator. The official scanned final reports and planned polling-place lists retain that denominator. This recovery restores ballot-level eligible-voter counts so locality and statistical-area aggregates can calculate K17 turnout.

The production source of truth is `data/manual/k17_eligible_voters.csv`. It has one row for each of the 8,277 ordinary K17 result rows and is joined by `source_row_uid` during normalization.

## Result

| Scope | Eligible voters |
|---|---:|
| Ordinary polling registers represented by result rows | 5,011,053 |
| Separate Gush Katif evacuee register | 3,569 |
| Official national denominator | 5,014,622 |

The row-level table reconciles exactly to 5,011,053. The 3,569-person supplemental register is documented separately because the available result data does not distribute its votes among ordinary ballot rows, localities, or statistical areas. It must not be assigned to a map polygon or to the envelope aggregate.

Envelope results have votes but no matching geographic eligible-voter register in the source data. Their turnout remains unavailable rather than zero.

## Evidence Methods

| Method | Rows |
|---|---:|
| Final-report image OCR | 8,199 |
| Direct recovery from unaligned final-report text lines | 14 |
| Final-report omission of a zero-voter planned row | 1 |
| Planned-list fallback, reconciled to national total | 10 |
| Planned-list fallback for missing Rehovot final-report pages | 49 |
| Planned-list fallback, reconciled to printed subtotal | 4 |
| **Total** | **8,277** |

The OCR reads fixed numeric cells from the final-report page images. Embedded PDF OCR text was used only for alignment and audit because visual checks found incorrect embedded digits. The official planned list is a fallback, not a source of invented result rows.

## Reviewed Exceptions

- `K17:2450`, Sinsana ballot 1.0: final-report eligible count 90.
- `K17:5058`, Bnei Brak ballot 42.0: final-report eligible count 575, replacing the planned-list value 533.
- `K17:3518`, Jerusalem ballot 50.3: planned with 75 eligible voters but zero actual voters; absent from the final report and its printed Jerusalem subtotal, so the result-row denominator is 0.
- Rehovot ballots 88 onward: 49 rows use the planned list because the available local final-report scan ends at ballot 87. These values are supported collectively by exact national reconciliation.

The reviewed printed locality subtotals for Jerusalem (336,913), locality code 3574 (2,578), locality code 3797 (11,891), and Bnei Brak/code 6100 (83,379) resolve the apparent discrepancies caused by faulty embedded OCR.

## Pipeline Guards

`scripts/normalize_election_results.py` fails when:

- the override file lacks a required column;
- a `source_row_uid` is missing or duplicated;
- the file does not contain exactly 8,277 keys;
- an override's stored actual-voter count differs from its official result row;
- any eligible-voter value is lower than its actual-voter value; or
- the ordinary eligible-voter sum is not exactly 5,011,053.

`scripts/build_public_outputs.py` forces the combined envelope/non-geographic display aggregate back to a zero denominator. This prevents the few military/special rows that carry a local denominator from implying a turnout rate for the much larger envelope vote total.

## Reproduction Artifacts

The extraction and reconciliation scripts are under `work/`; large intermediate OCR output remains under `tmp/` and is not production input. The checked-in CSV is intentionally self-describing: each row records its evidence method, source PDF/page where available, OCR confidence, and an evidence note.
