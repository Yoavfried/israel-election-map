# Polling-Place Address Quality Audit

> Current scope: this is an address/OCR and polling-place-location audit. OSM containment results are not promoted into election statistical-area assignment.

Last updated: 2026-07-16

## Purpose

Address QA answers three separate questions:

1. Did the pipeline copy the official source correctly?
2. Is the saved value a usable street, house number, locality, or polling-place name?
3. Can OSM place the street or numbered address in one 2022 statistical area?

These checks must remain separate. Reproducing an official source cell does not prove that the official address is geographically correct. An OSM miss also does not prove that the municipality is wrong because OSM may lack the address object or use another name.

## Run

```bash
python scripts/audit_polling_place_address_quality.py
python scripts/build_osm_street_stat_lookup.py
python scripts/build_osm_address_stat_lookup.py
python scripts/build_unmatched_location_inventory.py
```

The audit covers K17-K25. Rows in a 2022 locality with only one statistical area are already assignable before address-dependent OSM matching.

## Source Fidelity

| Evidence | Source rows |
|---|---:|
| Official digital spreadsheet or result file | 74,033 |
| Fresh K19 text-PDF parser result | 10,239 |
| K18 OCR intermediate awaiting page review | 9,137 |
| Reviewed K17 scan transcription | 456 |
| Reviewed K18 source image | 126 |
| **Total** | **93,991** |

Current pipeline-fidelity failures:

| Failure | Rows |
|---|---:|
| Missing source evidence record | 0 |
| Normalized field differs from source evidence | 0 |

This rules out a downstream copy, row-key, or normalization mismatch in the current table. Fidelity comparisons apply only to fields actually present in each evidence source; the K17 result file's absent eligible-voter field is restored and validated separately rather than compared with a fabricated zero. This does not clear unreviewed K18 OCR or prove that an address printed by the election authority is geographically correct.

## Address Usability

Exclusive categories across all 93,991 source rows:

| Category | Source rows |
|---|---:|
| Street and house number | 65,090 |
| Locality name in the address field | 15,946 |
| Street, neighborhood, or other text without a house number | 12,295 |
| Suspicious OCR or encoding text | 137 |
| Empty address with a place name | 479 |
| Place-like text in the address field | 29 |
| Number or no usable street letters | 10 |
| Empty address and place | 5 |

The 78,247 rows requiring geographic placement form 7,190 query-lineage units:

| Category | Query units |
|---|---:|
| Street and house number | 5,665 |
| Street, neighborhood, or other text without a house number | 829 |
| Locality name in the address field | 362 |
| Empty address with a place name | 235 |
| Suspicious OCR or encoding text | 98 |
| Number or no usable street letters | 1 |
| **Total** | **7,190** |

A query unit preserves a normalized geocoder query for source-row lineage. It is not necessarily one physical address; punctuation variants and reversed personal-name order can produce more than one query for the same place.

The shared parser handles numeric street identifiers explicitly. `רח 6027 8` means street `רח 6027`, house 8. `רח 7025` and `שכ 24` do not acquire a house number merely because the street or neighborhood identifier is numeric.

## Manual Source Review

There are 1,525 address-content review units:

| Evidence status | Units |
|---|---:|
| PDF/OCR query corroborated by a digital election | 615 |
| PDF/OCR query corroborated by a manual scan transcription | 25 |
| PDF/OCR query corroborated by a reviewed image | 1 |
| Problem present directly in a digital source | 320 |
| Present in reviewed manual transcription | 112 |
| Present in a reviewed visual source | 2 |
| Still requires PDF or scan inspection | 450 |

The 450 visual-review units are 98 suspicious-text units, 196 missing-number units, 133 locality-only units, and 23 place-only units. They are a bounded decision queue, not evidence that every row is wrong.

Completed checks include:

- K18 Karmiel kalpi 14, 51, and 65: OCR `11,0` was corrected to `בז,11` from PDF pages 77-79 and K19-K25 digital corroboration.
- K18 Segev-Shalom kalpi 1-5: page 301 itself contains only `38,`; K19 repeats it. This remains a facility-placement case, not an OCR correction.
- Dimona kalpi 91 in K22-K25, address `מחנה עדי`: reviewed as envelope votes and removed from geographic address placement through `data/manual/polling_place_assignment_overrides.csv`.

The K18 review overlay now contains 126 source rows: 121 corrected values and 5 confirmations that the weak source text is genuinely present in the scan. The final user-confirmed batch covered 82 suspicious signatures and 113 rows. All 113 are now marked as visually corrected, including the five polling-place-name corrections listed in `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md`.

## K17 Locality-Only Correction

The earlier claim that 36 units covering 344 ballot boxes had no place name was incorrect.

- The K17 digital result rows contained only the locality in the address field and did not carry a polling-place column.
- The original K17 polling-place scans contain the value in the far-left `מקום הקלפי` column.
- Direct visual transcription recovered a non-empty place for all 344 rows across 36 localities.
- Every affected row is K17. None is K18 and no K18 value was copied as K17 evidence.

| Check | Result |
|---|---:|
| Formerly affected K17 rows | 344 |
| Rows with direct K17 scan transcription | 344 |
| Current locality-only/no-place units | 0 |

The committed K17 manual source contains 456 scan transcriptions in total; the 344 rows above are the formerly misclassified subset. The exact polls and scan pages are in `docs/K17_LOCALITY_ONLY_SCAN_RECOVERY.csv`. A station-count comparison found one separate source-data gap: the Maghar scan lists stations 1-20, while the digital K17 result table contains only 1-16. Stations 17-20 are absent digital result rows, not rows with blank polling-place values.

## OSM Matching Grain

OSM is the first geographic placement layer. Photon is a fallback after OSM.

Query units remain available for lineage, while physical numbered addresses are deduplicated by:

```text
target locality code + canonical street name + canonical house number
```

Canonical street matching ignores punctuation, standard `רח`/`רחוב` prefixes, and personal-name token order. An exact scalar OSM house number now outranks a semicolon/comma multi-value tag when both match.

The clean numbered-address input contains 5,663 query units and 4,210 canonical locality-street-number addresses, including two supplemental reviewed target-locality queries.

Current canonical resolution:

| Result | Canonical addresses |
|---|---:|
| Assigned because the entire 25 m OSM street corridor is in one area | 762 |
| Additional assignments from an exact OSM house number | 584 |
| Reviewed OSM evidence assignments | 7 |
| Reviewed component-locality assignments | 2 |
| **Resolved OSM-first assignments** | **1,355** |
| **Unresolved** | **2,855** |

The 2,855 unresolved addresses are:

| Reason | Canonical addresses |
|---|---:|
| Street spans multiple areas and exact address is missing in the target locality | 1,188 |
| Street is not found in the target locality and exact address is also missing | 1,113 |
| Street centerline is in one area but its 25 m corridor crosses a boundary; exact address is missing | 554 |

For 3,469 of the 4,210 canonical addresses, OSM has no explicit matching address object inside the target locality. In 2,213 cases the normalized street-number pair is absent from extracted OSM address tags anywhere in the PBF; in 1,256 it occurs elsewhere but not in the target locality. Two supplemental rows are not testable as ordinary locality/address pairs. A pair occurring elsewhere is not proof of a wrong municipality because common addresses repeat across Israel.

The reader supports `addr:housenumber` with `addr:street` or `addr:place` on OSM points, lines, and multipolygons. It does not yet infer streets for house-number-only objects, expand `addr:interpolation`, or resolve `associatedStreet` relations.

## Resolved Exceptions

All nine addresses in the four former review buckets now have explicit canonical assignments:

| Former bucket | Address | Resolution | 2022 area |
|---|---|---|---:|
| Conflicting exact features | גיבורי החיל 1, יבנה | Named OSM footprint for מתנ"ס גרמנוב | 35 |
| Conflicting exact features | הרב קוק 13, נתניה | Official coordinate selects OSM building footprint | 322 |
| Conflicting exact features | הרצל 3, נתניה | Exact scalar `3` outranks distant `17;3` feature | 321 |
| Building crosses boundary | חטיבת הנגב 45, אשדוד | Building representative point; 55.36% of footprint | 146 |
| Building crosses boundary | מבצע משה 39, ראשון לציון | Building representative point; 65.82% of footprint | 722 |
| At least 90% in one area | צדקיהו 6, חיפה | 98.13% of building footprint | 511 |
| At least 90% in one area | השלום 15, באר שבע | 98.73% of building footprint | 634 |
| Sha'ar Shomron target set | הברוש 13 | Official sources place it in עץ אפרים | 1 |
| Sha'ar Shomron target set | הערבה 2 | Reviewed sources place it in עץ אפרים | 1 |

The two genuinely boundary-crossing buildings use a documented representative-point convention. Their assignments do not claim that the full building lies in one area.

The review records are in `data/manual/manual_osm_address_stat_reviews.csv`. Each record stores its expected prior status. If a future OSM rebuild changes that status, the script fails and requires re-review instead of silently applying stale evidence.

The raw `osm_address_status` remains unchanged as evidence of what OSM originally returned, so raw unit-status counts still show conflicts and boundary cases. Whether an address is currently unresolved is determined by the canonical `resolution_status`; none of these nine rows remains unresolved there.

## Missing House Number

The old 654 figure mixed query-lineage units with locality/street pairs. The current parser and reviewed locality targets produce the following reproducible scope:

| Result | Query units | Canonical locality-street keys |
|---|---:|---:|
| Starting scope | 829 | 815 |
| Strict single-area street assignment | 138 | 132 |
| Residual | 691 | 683 |

The 683 canonical residuals comprise 389 street names not found in the target locality, 167 streets spanning multiple areas, and 127 streets whose 25 m corridor crosses a boundary. Some values may be neighborhoods, constituent-locality names, source typos, or missing OSM data; they are not all proven streets.

## Outputs

- `data/processed/addresses/polling_place_address_quality_rows.csv`: source rows with evidence and quality classification.
- `data/processed/addresses/polling_place_address_quality_units.csv`: query-lineage units.
- `data/processed/addresses/polling_place_address_quality_review_queue.csv`: address-content review units.
- `data/processed/addresses/polling_place_address_visual_review_queue.csv`: the 450 source-image review units.
- `data/processed/addresses/polling_place_locality_only_no_place_units.csv`: now empty.
- `docs/K17_LOCALITY_ONLY_SCAN_RECOVERY.csv`: exact 344-row K17 scan recovery.
- `data/manual/manual_osm_address_stat_reviews.csv`: reviewed OSM exception assignments.
- `data/processed/geocoding/osm_street_stat_lookup.csv`: canonical locality-street results.
- `data/processed/geocoding/osm_address_stat_canonical_addresses.csv`: canonical numbered-address resolutions.
- `data/processed/geocoding/osm_address_stat_geocoding_units.csv`: query-unit lineage.
- `data/processed/geocoding/osm_address_stat_matches.csv`: matched OSM feature evidence.
- `data/processed/geocoding/unmatched_location_units.csv`: one row per unresolved location signature.
- `data/processed/geocoding/unmatched_location_reason_summary.csv`: current unmatched reason totals.

OSM candidates are not promoted into election-result statistical assignments. They remain polling-place-location evidence and must retain OSM/review provenance if exposed as a separate feature. The current election assignment is in `docs/GEOGRAPHIC_ASSIGNMENT_STATUS.md`.
