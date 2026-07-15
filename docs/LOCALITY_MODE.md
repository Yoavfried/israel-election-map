# Locality Mode

Last updated: 2026-07-15

## Status

Locality mode is complete for the current K17-K25 geographic scope. It does not wait for polling-place address geocoding.

Each ordinary ballot row already identifies an election locality. The reviewed locality crosswalk maps that identity directly to either:

- one 2022 locality (`loc:<code>`),
- one reviewed election-specific composite locality,
- or one reviewed custom geography.

Official envelope rows and reviewed special non-geographic rows are outside locality-map coverage. Envelope results are aggregated and shown separately in the web app.

| Election | Geographic rows mapped | Actual voters mapped | Locality coverage | Envelope rows | Envelope actual voters |
|---|---:|---:|---:|---:|---:|
| K25 | 11,699 | 4,331,026 | 100% | 838 | 462,807 |
| K24 | 12,119 | 4,010,014 | 100% | 799 | 425,512 |
| K23 | 10,623 | 4,284,014 | 100% | 548 | 330,209 |
| K22 | 10,531 | 4,181,911 | 100% | 362 | 282,442 |
| K21 | 10,453 | 4,098,687 | 100% | 305 | 240,783 |
| K20 | 10,112 | 4,019,324 | 100% | 295 | 234,599 |
| K19 | 9,875 | 3,617,176 | 100% | 228 | 215,789 |
| K18 | 9,259 | 3,229,261 | 100% | 1 | 186,919 |
| K17 | 8,274 | 3,011,950 | 100% | 149 | 174,484 |
| **Total** | **92,945** | **34,783,363** | **100%** | **3,525** | **2,553,544** |

The 92,945-row geographic scope includes 460 rows assigned to the four reviewed custom geographies. The remaining 59 rows, representing 6,317 actual voters, are reviewed special non-geographic rows and are not rendered as locality results.

## Composite Municipalities

The following source municipalities represent more than one locality in the 2022 CBS layer. Locality mode preserves the municipality that existed in the selected election by unioning its component polygons. The component features are hidden only for elections where the composite is active.

| Composite | Elections | 2022 component locality codes | Ballot rows | Actual voters |
|---|---|---|---:|---:|
| באקה-ג'ת | K17 | 6000, 628 | 27 | 7,880 |
| עיר כרמל | K17 | 494, 534 | 21 | 7,703 |
| שגור | K17 | 483, 490, 516 | 21 | 11,069 |
| באקה-ג'ת | K18 | 6000, 628 | 30 | 9,704 |
| עיר כרמל | K18 | 494, 534 | 27 | 7,735 |
| שגור | K18 | 483, 490, 516 | 27 | 12,834 |
| שער שומרון | K25 | 3720, 3778 | 10 | 4,173 |

The locality rule applies to every row from the composite source municipality, including rows whose polling-place evidence already points to one component. That evidence remains useful for statistical-area mode, but it must not split an election-time municipality in locality mode.

The reviewed source of truth is `data/manual/composite_localities.csv`. `scripts/build_geographies.py` writes the unioned features to `data/processed/geographies/composite_localities*.geojson`.

Sha'ar Shomron retains its unioned geometry but uses a fixed-size marker in the national view because both component features are tiny West Bank point proxies. The other composites render as polygons.

## Envelope Results

Envelope votes have no locality geometry and are never duplicated across polygons. `scripts/build_public_outputs.py` writes one aggregate per election under `data/processed/public/envelope_results/`.

The web app shows that aggregate as a selectable national result beside the map. Its detail panel includes actual voters, valid and invalid votes, the leading ballot, margin, contributing source rows, and the party breakdown. Turnout is omitted because envelope rows do not have a meaningful locality-level eligible-voter denominator.

## Statistical-Area Separation

Locality and statistical-area assignment are independent products:

- Locality mode uses the reviewed locality identity directly and is complete.
- Statistical-area mode still needs the polling-place building location when a locality has more than one 2022 statistical area.
- Historical composite rows may therefore be complete in locality mode while still awaiting address placement into one component's statistical areas.
- OSM and Photon work affects statistical-area coverage, not locality totals.

The final assignment table exposes this distinction through `locality_assignment_status`, `locality_geography_type`, `locality_geography_id`, `locality_result_code`, `locality_result_name`, and `is_locality_mapped` alongside the existing statistical-area assignment fields.

## Web Data Contract

The version 2 browser payload has mode-specific coverage. Locality payloads also carry:

- the official envelope aggregate,
- election-specific hidden geography IDs for composite/component replacement,
- composite locality records joined by stable `composite:<key>` IDs.

Generated-data tests require 100% locality coverage, ensure every visible result joins a geometry, ensure hidden component features have no simultaneous result, and validate envelope totals against the same party-vote contract used by map records.
