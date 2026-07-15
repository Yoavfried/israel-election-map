# Geographic Assignment Status

Last updated: 2026-07-15

## Scope

The target is to place every non-envelope K17-K25 ballot row in a 2022 statistical area when the saved geographic evidence supports it. The unit being located is the polling place, not the voters' residence and not an official historical kalpi boundary.

The current pipeline contains 96,529 ballot-result rows. It excludes 3,525 official envelope rows and 59 reviewed envelope-like or non-geographic rows from the address-matching universe. That leaves 92,945 non-envelope rows.

## Matching Rules

The matching order is:

1. **Single-area locality:** if the reviewed target locality has exactly one 2022 statistical area, the row is assigned without geocoding.
2. **OSM street corridor:** a locality/street match is accepted when the complete OSM centerline and its 25 m corridor lie in one 2022 statistical area.
3. **OSM house number:** for numbered addresses, exact `addr:housenumber` objects with matching `addr:street` or `addr:place` can resolve a street that spans or touches multiple areas.
4. **Reviewed exceptions:** explicit row or OSM-feature reviews are stored in committed manual CSV files and fail closed when their expected prior status changes.
5. **Photon fallback:** only locations unresolved by OSM should proceed to Photon. A Photon point must first fall in the expected reviewed locality and is assigned by point-in-2022-statistical-area, not by Photon text alone.

Numbered physical addresses are checked once across elections using:

```text
target locality + canonical street name + canonical house number
```

Polling-place names remain lineage/evidence but do not create duplicate numbered-address requests. Street matching normalizes punctuation, common Hebrew street prefixes, and personal-name token order.

## Source Verification

The current address table has 93,991 source rows and zero missing evidence links or normalized-field mismatches.

| Verification state | Source rows |
|---|---:|
| Verified against raw digital source | 74,033 |
| K19 parser output, visual check still pending | 10,239 |
| K18 OCR intermediate, visual check still pending | 9,137 |
| Reviewed manual transcription | 456 |
| Verified against a visual source | 126 |
| **Total** | **93,991** |

The 78,247 rows that still need geographic placement collapse to 7,190 query-lineage units:

| Saved information quality | Units |
|---|---:|
| Street + house number | 5,665 |
| Street text without a house number | 829 |
| Locality repeated in address | 362 |
| Place only | 235 |
| Suspicious OCR/encoding | 98 |
| Number/no usable street | 1 |
| **Total** | **7,190** |

### K17 scan recovery

The earlier claim that 344 K17 rows had no polling-place name was caused by reading only the digital result table. The value exists in the far-left polling-place column of the original scans. Direct review recovered all 344 values across 36 localities. The committed K17 manual table now contains 456 scan transcriptions in total, and the current true locality-only/no-place count is zero.

### K18 visual review

`data/manual/manual_k18_address_reviews.csv` contains 126 reviewed rows: 121 corrections and 5 confirmations that the weak source text is genuinely what appears in the scan. The latest user-confirmed batch covered 82 suspicious address signatures and 113 source rows; all 113 now normalize as visually corrected rather than suspicious.

Five polling-place-name corrections from that review are also preserved:

- `בי"0 רוקח` -> `בי"ס רוקח`
- `נועם-בי"ס תורני לבנות` -> `נועם - בי"ס תורני לבנות`
- `בי"0 ממלכתי א )אלסלאם(` -> `בי"ס ממלכתי א )אלסלאם(`
- `בי"0 ישורון` -> `בי"ס ישורון`
- `בי"ס ממלכתי אלפואר` -> `בי"ס ממלכתי ג' - אלפואר`

After all corroboration and completed review overlays, 450 source-content units still require a visual decision: 196 missing-number, 133 locality-only, 98 suspicious-text, and 23 place-only units. This is a review queue, not a claim that all 450 are wrong.

## OSM Results

### Numbered addresses

The clean numbered-address pass contains 5,663 work units and 4,210 canonical physical addresses. Current canonical outcomes are:

| Outcome | Canonical addresses |
|---|---:|
| Assigned by one-area street corridor | 762 |
| Additional assignments from exact house number | 584 |
| Reviewed OSM evidence | 7 |
| Reviewed component-locality handling | 2 |
| **Resolved OSM-first** | **1,355** |
| Street spans areas; exact address absent | 1,188 |
| Street and exact address absent in target locality | 1,113 |
| Street corridor crosses a boundary; exact address absent | 554 |
| **Unresolved** | **2,855** |

At query-lineage grain, strict street or exact-address geometry resolves 1,922 units covering 24,211 source rows and 9,463,605 actual voters. These counts are not additive with the canonical-address table because multiple query variants can represent one physical address.

### Streets without house numbers

The missing-number pass contains 829 query units and 815 canonical locality/street pairs. A strict one-area corridor resolves 138 units, representing 132 pairs and 1,433 ballot rows. The remaining 683 pairs are 389 OSM misses, 167 streets spanning multiple areas, and 127 corridors crossing a boundary.

## Locality Mode Is Complete

The unmatched inventory below applies to statistical-area placement, not locality totals. Locality mode assigns all 92,945 geographic-scope rows directly through the reviewed locality crosswalk, election-specific composite municipalities, or reviewed custom geographies. The 3,525 official envelope rows and 59 reviewed `special:envelope_votes` rows are combined into one separate national result per election.

The composite municipalities are באקה-ג'ת, עיר כרמל, and שגור in K17-K18, plus שער שומרון in K25. Their component polygons are unioned only for the elections where the composite source municipality exists. See `docs/LOCALITY_MODE.md` for the exact rows, voters, components, and frontend behavior.

## Current Unmatched Inventory

After the accepted single-locality and current OSM rules:

| Reconciliation item | Ballot rows |
|---|---:|
| Non-envelope assignment universe | 92,945 |
| Assigned to a 2022 area by single-area locality | 14,238 |
| Assigned by current OSM numbered-address rules | 24,377 |
| Assigned by current OSM no-number street rules | 1,433 |
| **Assigned to a 2022 statistical area** | **40,048** |
| Reviewed custom geography, not a 2022 statistical area | 460 |
| **Resolved by the analytical inventory** | **40,508** |
| **Unmatched** | **52,437** |

The 52,437 unmatched ballot rows collapse to 4,893 unique location signatures:

| Saved geographic information | Unique unresolved signatures | Ballot rows |
|---|---:|---:|
| Locality only | 0 | 0 |
| Locality + street | 370 | 1,000 |
| Locality + street + number | 149 | 345 |
| Locality + place | 578 | 5,356 |
| Locality + street + place | 999 | 7,825 |
| Locality + street + number + place | 2,797 | 37,911 |
| Locality + number, no street | 0 | 0 |
| Locality + number + place, no street | 0 | 0 |
| No Geo Data | 0 | 0 |
| **Total** | **4,893** | **52,437** |

For numbered addresses, signatures intentionally ignore the polling-place name, so the same physical address is tested once. If at least one source row supplies a place name, the grouped signature is shown in the richer `+ place` category; this is why the category table is not the same as classifying each source row independently.

The unmatched reasons, aggregated across structural categories, are:

| Reason | Signatures | Ballot rows |
|---|---:|---:|
| Street spans areas and exact address is absent | 1,188 | 17,845 |
| Street and exact address are absent in target locality | 1,113 | 12,168 |
| Exact address absent after 25 m corridor crosses boundary | 554 | 8,125 |
| Place matching not implemented | 578 | 5,356 |
| OSM street not found in target locality | 773 | 4,764 |
| Street spans multiple areas, no house number | 342 | 2,373 |
| 25 m street corridor crosses boundary, no house number | 254 | 1,688 |
| Suspicious source text deliberately not tested | 91 | 118 |
| **Total** | **4,893** | **52,437** |

The canonical generated files are:

- `data/processed/geocoding/unmatched_location_units.csv`
- `data/processed/geocoding/unmatched_location_category_summary.csv`
- `data/processed/geocoding/unmatched_location_reason_summary.csv`
- `data/processed/geocoding/unmatched_location_summary.json`

## AGS Limitation

Only the local K23 polling-place workbook exposes an explicit AGS field. Source AGS cannot be used as a hard building-location truth: 756 AGS-bearing work units have multiple AGS values at one polling-place address, and one observed value can simply mean that only one contributing kalpi is currently visible in the scoped data. An AGS mismatch is a review signal, not automatic geocode rejection. See `docs/AGS_HISTORICAL_QA.md`.

## Public Output Boundary

The OSM inventory above is analytical evidence. `scripts/build_final_geography_assignments.py` does not yet promote OSM candidates into `ballot_geography_assignments.csv`. Statistical-area mode therefore shows only single-area locality assignments and reviewed custom geographies; its current mapped-voter coverage ranges from 12.65% to 14.38% of the geographic scope by election. Locality mode is independently complete at 100%, and envelope results are visible separately rather than counted as unmapped geography.

Promoting OSM matches is the next implementation step. It must preserve whether each row was assigned by locality, strict street corridor, exact house number, or reviewed exception, along with the OSM source/version and canonical address key.

## Reproduce

Core pipeline using existing generated geography files:

```powershell
python scripts/run_pipeline.py --skip-geographies
```

OSM and unmatched inventory:

```powershell
python scripts/build_osm_street_stat_lookup.py
python scripts/build_osm_address_stat_lookup.py
python scripts/build_osm_street_stat_lookup.py --work-units data/processed/addresses/polling_place_address_quality_units.csv --quality-category missing_house_number --lookup-output data/processed/geocoding/osm_street_missing_house_number_lookup.csv --unit-output data/processed/geocoding/osm_street_missing_house_number_geocoding_units.csv --summary-output data/processed/geocoding/osm_street_missing_house_number_summary.json
python scripts/build_unmatched_location_inventory.py
```

Frontend validation:

```powershell
cd web/app
npm run check
```

## Remaining Decisions

1. Decide which of the 450 source-image review units justify opening scans next; do not start a large manual batch implicitly.
2. Implement place-name matching for the 578 place-only signatures.
3. Review the 91 suspicious-text signatures still deliberately excluded from OSM tests.
4. Promote accepted OSM assignments into the final assignment builder with full provenance.
5. Run Photon only on the residual inventory, validate expected locality, and review point-in-area results before promotion.
