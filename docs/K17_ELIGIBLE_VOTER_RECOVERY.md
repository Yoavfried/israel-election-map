# K17 Eligible-Voter Recovery

Last updated: 2026-07-17

## Purpose

The official K17 result file contains turnout numerators and party votes but
omits the eligible-voter denominator. Official scanned final reports and
planned station registers retain that denominator. This recovery restores
ballot-level eligible-voter counts so locality and statistical-area aggregates
can calculate K17 turnout.

The production source of truth is `data/manual/k17_eligible_voters.csv`. It has one row for each of the 8,277 ordinary K17 result rows and is joined by `source_row_uid` during normalization.

## Result

| Scope | Eligible voters |
|---|---:|
| Ordinary polling registers represented by result rows | 5,011,053 |
| Separate Gush Katif evacuee register | 3,569 |
| Official national denominator | 5,014,622 |

The row-level table reconciles exactly to 5,011,053. The 3,569-person
supplemental register is not distributed among ordinary ballot rows, localities,
or statistical areas and is never assigned to a polygon. It is stored in the
public envelope/non-geographic aggregate solely as a technical national-
denominator bucket.

Three non-geographic K17 camp rows contribute 518 ordinary eligible voters to
the same bucket. Its published denominator is therefore 4,087, while
geographically represented rows total 5,010,535; together they reproduce
5,014,622. This mixed bucket is not a meaningful envelope turnout denominator,
so envelope turnout remains unavailable.

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

`scripts/build_public_outputs.py` checks both reconciliations: ordinary rows plus
the Gush Katif register equal 5,014,622, and geographic rows plus the 4,087
technical envelope/non-geographic bucket also equal 5,014,622. Other elections
retain a zero envelope denominator.

## Reproduction Artifacts

The committed recovery table is intentionally self-describing: each row records
its evidence method, source PDF/page where available, OCR confidence, and an
evidence note. One-off page renders and OCR working files are not production
inputs and are not included in the repository. A fresh independent extraction
should start from the official scanned reports listed in `DATA_SOURCES.md` and
must satisfy every reconciliation guard above before replacing the reviewed
table.
