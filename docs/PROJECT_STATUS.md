# Project Status

Last updated: 2026-07-18

This is the repository's only project completion tracker. Methodology, audit
evidence, and generated coverage tables remain in subject-specific documents,
but open/complete workstream declarations belong here.

## Workstreams

| Workstream | Status | Current boundary |
|---|---|---|
| K17-K25 election normalization | Complete | 96,529 source rows are normalized and reconcile to the official election totals. |
| Locality-mode aggregation | Implemented; audit open | Every geographic-scope result row is mapped. The 80 localities present in only some elections still need election-by-election historical review. |
| Historical statistical-area mode | Implemented; current-source audit complete | Election-specific CBS crosswalks and matching 1995/2008/2011 geometry are active. Direct AGS, stable-ballot, and exact aggregate evidence have been exhausted under conservative rules; remaining source gaps are classified and published. |
| Party/list names | Complete | All published K17-K25 lists have reviewed display names. English labels may fall back to Hebrew where no separate translation is maintained. |
| Party colors | In progress | Stable-letter defaults and election-specific overrides work; the editorial color table is incomplete. |
| Wikipedia links | In progress | Hebrew and English candidates exist for many lists, but links and intentional blanks are not fully audited. |
| UX and accessibility | Continuous | Responsive bilingual UX, mobile behavior, keyboard support, and accessibility remain ongoing product requirements. |
| Product features | Planned; search next | Search, national results, single-party mode, two-party comparison, and the equal-priority satellite/OSM/3D suite are recorded in `FEATURE_PLAN.md`. |
| Public data distribution | Implemented | `public-data/v1` is a schema-v2 release with 97 files, direct geography joins, checksums, validation, and row-level assignment provenance. Future versioning policy remains open. |
| Public repository hardening | In progress | MIT licensing, third-party notices, and public-facing repository hygiene are in place; fresh-clone source bootstrap, CI, and performance checks are unfinished. |

## Public Data Release

The committed `public-data/v1` release can be used without the private working
data. It includes:

- nine ballot-row CSVs covering all 96,529 normalized rows;
- statistical-area, locality, custom-geography, envelope, and unresolved tables;
- full-resolution 1995, 2008, 2011, and 2022 statistical-area packages;
- current locality, reviewed composite-locality, and custom-geography packages;
- direct `geography_id` joins, party/election metadata, checksums, and validation;
- 25 machine-readable provenance and audit artifacts under
  `metadata/assignment-provenance/`.

The release marks 148 ballot-to-area links as synthetic links, representing
40,752 actual voters. The ballot rows and votes themselves are never synthetic:

| Evidence | Rows | Actual voters |
|---|---:|---:|
| Official CBS stable-ballot inference | 134 | 35,129 |
| Reviewed exact ArcGIS residual inference | 9 | 3,599 |
| Reviewed cross-election correction | 5 | 2,024 |
| **Total** | **148** | **40,752** |

The separate 74 K23 AGS assignments, representing 29,685 actual voters, are
direct official evidence and are therefore not marked synthetic. Users can
exclude every inferred link with `assignment_is_synthetic_link=false`.

Map colors and other presentation choices remain in `web/app/`; they are not
part of the reusable election tables.

## Statistical-Area Coverage

Statistical mode uses the historical vintage named by the official crosswalk:
1995 for K17, 2008 for K18, and 2011 for K19-K25. K25 is not converted to 2022
areas because its official crosswalk still targets 2011.

Across all elections, 5,605 rows representing 2,097,509 actual voters remain
without a defensible statistical-area target. Supported statistical-mode voter
coverage is 93.97% overall. Locality coverage is 100% in every election.

| Election | Vintage | Statistical-area rows | Custom rows | Pending rows | Pending actual voters | Supported voter share |
|---|---:|---:|---:|---:|---:|---:|
| K17 | 1995 | 7,815 | 44 | 415 | 160,216 | 94.68% |
| K18 | 2008 | 8,692 | 48 | 519 | 189,711 | 94.13% |
| K19 | 2011 | 9,311 | 0 | 564 | 214,251 | 94.08% |
| K20 | 2011 | 9,521 | 0 | 591 | 269,029 | 93.31% |
| K21 | 2011 | 9,854 | 0 | 598 | 225,160 | 94.51% |
| K22 | 2011 | 9,920 | 0 | 611 | 266,046 | 93.64% |
| K23 | 2011 | 10,004 | 0 | 619 | 297,152 | 93.06% |
| K24 | 2011 | 11,248 | 0 | 871 | 212,701 | 94.70% |
| K25 | 2011 | 10,882 | 0 | 817 | 263,243 | 93.92% |

The unresolved rows are classified rather than silently estimated:

| Current explanation | Rows |
|---|---:|
| Entire locality omitted from the official crosswalk | 5,349 |
| Locality absent from the active historical geography | 99 |
| K17 historical composite municipality without a crosswalk | 57 |
| Central ballot 990, intentionally locality-only | 70 |
| Specific ordinary ballot omitted from the official crosswalk | 30 |
| **Total** | **5,605** |

The source audit found exactly one CBS direct crosswalk for each K17-K25
election and one stable-ballot workbook for each transition ending K19-K25. Of
the archived K20-K25 CEC polling-place reports, only K23 contains AGS. No second
in-scope official workbook was found.

The ArcGIS review is closed under the approved Tier A/B/C policy. Source
metadata states that statistical areas in Arab localities were merged, so 65
apparent locality partitions were rejected as locality totals rather than
detailed areas. One military/non-geographic case was also rejected. The only
structurally valid exact assignments are nine K21 rows: three Tier A rows in
Ar'ara-BaNegev and six Tier C rows in Jerusalem. K20 has no accepted ArcGIS
assignment. No 1-3 vote tolerance is used.

Official stable-ballot evidence adds 134 rows. One same-vintage contradiction
and 105 vintage-transition conflicts are retained in the audit and withheld.
The K23 AGS audit agrees with 6,775 of 6,776 comparable existing assignments,
withholds the one contradiction, and adds 74 direct assignments.

## Remaining Work

1. Finish the election-by-election audit of the 80 partial-presence locality
   features. The 36 never-standalone features already have reviewed
   explanations.
2. Preserve the K17 Maghar source omission as an explicit result-source gap:
   the planned list has stations 17-20, but the official digital result table
   has stations 1-16 only. Do not synthesize missing result rows.
3. Decide whether acceptable detailed display boundaries exist for Rotem,
   Maskiyot, Avnat, and Mavo'ot Yeriho. This is a geometry-quality issue, not an
   assignment gap.
4. Complete the Wikipedia-link and party-color audits. Party/list names are
   complete.
5. Continue UX work and implement the feature order in `FEATURE_PLAN.md`.
6. Add reproducible fresh-clone source bootstrap and CI checks.

Historical assignment gaps should only be reopened when a new official or
independently reconcilable source becomes available. Reusing a ballot number
across elections or approximate arithmetic is not sufficient evidence.

## Geometry Caveats

- Every assigned statistical-area ID resolves to a published geometry.
- Canonical feature counts are 2,660 for 1995, 3,030 for 2008, and 3,115 for
  2011. The 2011 layer includes 32 documented exact-ID ArcGIS supplements; the
  1995 layer includes one official transition-key union.
- Detailed West Bank ArcGIS footprints are display derivatives except for those
  explicit exact-ID supplements. ArcGIS vote totals are never imported.
- K17/K18 preserve shared boundaries and clip replacement footprints against
  historical neighbors. The non-exclusive K17 Yehud-Newe Efrayim transition
  union renders as a marker to avoid overlapping polygons.
- Population attributes attached to historical polygons are demographic
  proxies, not election-specific eligible-voter counts.
- The neutral grey land backdrop is visual context only.

See `HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` for the evidence hierarchy and
`public-data/v1/metadata/assignment-provenance/` for row-level audit artifacts.
