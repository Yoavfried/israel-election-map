# Project Status

Last updated: 2026-07-19

This is the repository's only project completion tracker. Methodology, audit
evidence, and generated coverage tables remain in subject-specific documents,
but open/complete workstream declarations belong here.

## Workstreams

| Workstream | Status | Current boundary |
|---|---|---|
| K17-K25 election normalization | Complete | 96,529 source rows are normalized and reconcile to the official election totals. |
| Locality-mode aggregation | Implemented; audit open | Every geographic-scope result row is mapped. Of 80 localities present in only some elections, Ganei Modi'in now has a supported explanation for every missing election and 79 still need election-by-election historical review. |
| Historical statistical-area mode | Implemented; reviewed pass complete | Election-specific CBS crosswalks and matching 1995/2008/2011 geometry are active. Fifty high-confidence polling-register continuity links are approved and labeled synthetic; lower-confidence and mixed-register candidates remain unresolved. Entirely unassigned localities use a documented display-only map fallback. |
| Party/list names | Complete | All published K17-K25 lists have reviewed display names. English labels may fall back to Hebrew where no separate translation is maintained. |
| Party colors | In progress | Stable-letter defaults and election-specific overrides work; the editorial color table is incomplete. |
| Wikipedia links | In progress | Hebrew and English candidates exist for many lists, but links and intentional blanks are not fully audited. |
| UX and accessibility | Continuous | Responsive bilingual UX, mobile behavior, keyboard support, and accessibility remain ongoing product requirements. |
| Product features | Planned; search next | Search, national results, single-party mode, two-party comparison, and the equal-priority satellite/OSM/3D suite are recorded in `FEATURE_PLAN.md`. |
| Public data distribution | Implemented | `public-data/v1` is a schema-v2 release with 102 manifest-listed data files plus release manifests and validation, direct geography joins, checksums, and row-level assignment provenance. Future versioning policy remains open. |
| Public repository hardening | In progress | MIT licensing, third-party notices, and public-facing repository hygiene are in place; fresh-clone source bootstrap, CI, and performance checks are unfinished. |

## Public Data Release

The committed `public-data/v1` release can be used without the private working
data. It includes:

- nine ballot-row CSVs covering all 96,529 normalized rows;
- statistical-area, locality, custom-geography, envelope, and unresolved tables;
- full-resolution 1995, 2008, 2011, and 2022 statistical-area packages;
- current locality, reviewed composite-locality, and custom-geography packages;
- direct `geography_id` joins, party/election metadata, checksums, and validation;
- 30 machine-readable provenance and audit artifacts under
  `metadata/assignment-provenance/`.

The release marks 198 ballot-to-area links as synthetic links, representing
58,829 actual voters. The ballot rows and votes themselves are never synthetic:

| Evidence | Rows | Actual voters |
|---|---:|---:|
| Official CBS stable-ballot inference | 134 | 35,129 |
| Reviewed exact ArcGIS residual inference | 9 | 3,599 |
| Reviewed cross-election correction | 5 | 2,024 |
| Reviewed polling-register continuity | 50 | 18,077 |
| **Total** | **198** | **58,829** |

The separate 74 K23 AGS assignments, representing 29,685 actual voters, are
direct official evidence and are therefore not marked synthetic. Users can
exclude every inferred link with `assignment_is_synthetic_link=false`.

Map colors and other presentation choices remain in `web/app/`; they are not
part of the reusable election tables.

## Statistical-Area Coverage

Statistical mode uses the historical vintage named by the official crosswalk:
1995 for K17, 2008 for K18, and 2011 for K19-K25. K25 is not converted to 2022
areas because its official crosswalk still targets 2011.

Across all elections, 5,498 rows representing 2,055,696 actual voters remain
without a defensible statistical-area target. Supported statistical-mode voter
coverage is 94.09% overall. Locality coverage is 100% in every election.

| Election | Vintage | Statistical-area rows | Custom rows | Pending rows | Pending actual voters | Supported voter share |
|---|---:|---:|---:|---:|---:|---:|
| K17 | 1995 | 7,872 | 44 | 358 | 136,480 | 95.47% |
| K18 | 2008 | 8,693 | 48 | 518 | 189,252 | 94.14% |
| K19 | 2011 | 9,317 | 0 | 558 | 212,413 | 94.13% |
| K20 | 2011 | 9,545 | 0 | 567 | 259,204 | 93.55% |
| K21 | 2011 | 9,855 | 0 | 597 | 224,925 | 94.51% |
| K22 | 2011 | 9,922 | 0 | 609 | 265,357 | 93.65% |
| K23 | 2011 | 10,006 | 0 | 617 | 296,376 | 93.08% |
| K24 | 2011 | 11,251 | 0 | 868 | 212,156 | 94.71% |
| K25 | 2011 | 10,893 | 0 | 806 | 259,533 | 94.01% |

The unresolved rows are classified rather than silently estimated:

| Current explanation | Rows |
|---|---:|
| Entire locality omitted from the official crosswalk | 5,245 |
| Election locality identity absent from the active historical vintage | 55 |
| K17 component locality has multiple areas but no component crosswalk | 31 |
| K18 component locality is nested in the published composite geometry | 84 |
| Central ballot 990, intentionally locality-only | 70 |
| Specific ordinary ballot omitted from the official crosswalk | 13 |
| **Total** | **5,498** |

Statistical mode now makes the dominant missing-municipality case visible
without pretending it is area-level data. For 308 election/locality cases where
no ballot has a supported statistical-area assignment, the map shows the whole
locality total on a display-only locality or reviewed composite boundary with an
info notice. These displays represent 5,380 unresolved ballot rows and
2,028,085 actual voters. They do not write area IDs, alter the downloadable
ballot assignments, or increase the 94.09% coverage figure.

The source audit found exactly one public CBS direct crosswalk for each K17-K25
election and one stable-ballot workbook for each transition ending K19-K25. The
CBS product catalog also identifies a polling-district boundary layer named
`kalpi_artzi`, but classifies it as internal and unavailable for public sale or
download. Of the archived K20-K25 CEC polling-place reports, only K23 contains
AGS. No second public in-scope crosswalk was found.

The recurring omissions are not random missing shapefile polygons. Sixteen
localities are omitted from all nine published crosswalks, accounting for
3,409 pending rows, and another 16 recur in seven or eight elections. This is
consistent with the CBS-documented limitation on address anchoring and
statistical-area treatment in many Arab and Druze localities. The complete
recurrence table is published in
`historical_crosswalk_locality_omission_recurrence.csv`.

Reviewed K17/K18 polling-register evidence now identifies the component
locality for 164 rows: 153 historical composite-municipality rows and 11
Ma'ale Iron rows. It resolves 49 K17 rows directly to one historical area.
Thirty-one K17 rows remain in component localities
with multiple 1995 areas, and all 84 K18 rows remain nested inside composite
2008 geometry that does not publish separate component area IDs. These rows are
preserved as component-level evidence even when a statistical-area assignment
is not possible.

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

The supplied Kaplan K22-K25 map sources are now closed as assignment evidence.
Four payloads contain exactly one aggregate feature per locality. The additional
K25 payload contains 403 neighborhood aggregate points across 15 localities but
no boundaries, AGS IDs, or ballot crosswalk. After the continuity approvals, 53
remaining target rows in partially assigned municipalities represent 14,983
actual voters; the audit found zero defensible candidates and made no data
changes. The 50 continuity approvals use independent CEC polling-register and
CBS crosswalk evidence. Two moderate K19 Tel Sheva candidates and 15 mixed or
unallocated-register candidates remain withheld.

## Remaining Work

1. Finish the election-by-election audit of the remaining 79 partial-presence
   locality features. Ganei Modi'in is now fully explained, and the 36
   never-standalone features already have reviewed explanations.
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
7. Treat the supplied Kaplan layers as exhausted locality/neighborhood
   aggregates. Reopen recurring crosswalk omissions only if the internal CBS
   `kalpi_artzi` layer, another detailed official crosswalk, or independently
   reconcilable ballot-register evidence becomes available.

Historical assignment gaps should only be reopened when a new official or
independently reconcilable source becomes available. Reusing a ballot number
across elections or approximate arithmetic is not sufficient evidence.

## Geometry Caveats

- Every assigned statistical-area ID resolves to a published geometry.
- Canonical feature counts are 2,661 for 1995, 3,030 for 2008, and 3,115 for
  2011. The 2011 layer includes 32 documented exact-ID ArcGIS supplements; the
  1995 layer includes two official transition-key unions, including the
  reverse-transition reconstruction of Modi'in Illit.
- The raw-source inventory distinguishes assignable geometry records from
  multipart pieces and structural/non-area records, and is published in
  `historical_geography_build_summary.json`.
- Detailed West Bank ArcGIS footprints are display derivatives except for those
  explicit exact-ID supplements. ArcGIS vote totals are never imported.
- K17/K18 preserve shared boundaries and clip replacement footprints against
  historical neighbors. Reviewed confirmation places the K17 Yehud area 8
  result on the non-conflicting historical component polygon between Or Yehuda
  area 4 and Yehud area 3. The map calls it Yehud; canonical transition
  provenance remains unchanged.
- The K17/K18 Hebron custom target uses the exact detailed 2011 Hebron
  footprint. Tribal results use one combined marker in every election because
  the derivative ArcGIS tribe footprints overlap surrounding areas and are not
  defensible as exclusive boundaries. K19-K25 exact tribe assignments remain
  separate in the downloadable data and are combined only in the web display.
- Marker assets are data-dependent at runtime: resultless West Bank proxies,
  Umm al-Fahm points, and facility points do not render. The 16 evacuated Gaza
  features remain in the canonical 1995 download but are hidden in K17.
- Population attributes attached to historical polygons are demographic
  proxies, not election-specific eligible-voter counts.
- The neutral grey land backdrop is visual context only. Detailed West Bank
  locality footprints are excluded from that backdrop so historical polygons
  do not render on top of current Ma'ale Adumim, Ariel, Beitar Illit, or
  Modi'in Illit shapes.

See `HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md` for the evidence hierarchy and
`public-data/v1/metadata/assignment-provenance/` for row-level audit artifacts.
