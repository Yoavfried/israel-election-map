# Locality Mode

Last updated: 2026-07-15

## Status

Locality result-row assignment and aggregation are complete for the current K17-K25 geographic scope. They do not wait for polling-place address geocoding. The separate audit of which 2022 features should appear in elections where they have partial or no standalone results is not complete.

Each ordinary ballot row already identifies an election locality. The reviewed locality crosswalk maps that identity directly to either:

- one 2022 locality (`loc:<code>`),
- one reviewed election-specific composite locality,
- or one reviewed custom geography.

Official envelope rows and reviewed special non-geographic rows are outside locality-map coverage. Envelope results are aggregated and shown separately in the web app.

`100% locality coverage` means that every published geographic result row is assigned to a map geography and that the resulting totals reconcile with the source. It does not mean that every feature in the 2022 CBS locality layer has a standalone result in every election. That layer also contains non-electoral structural features, localities that did not yet exist in older elections, and small localities whose ballots were published under a host locality. A host result cannot be split between its component localities without more detailed source data.

| Election | Geographic rows mapped | Actual voters mapped | Locality coverage | Envelope rows | Envelope actual voters |
|---|---:|---:|---:|---:|---:|
| K25 | 11,699 | 4,331,026 | 100% | 846 | 463,567 |
| K24 | 12,119 | 4,010,014 | 100% | 807 | 426,351 |
| K23 | 10,623 | 4,284,014 | 100% | 556 | 331,121 |
| K22 | 10,531 | 4,181,911 | 100% | 370 | 283,257 |
| K21 | 10,453 | 4,098,687 | 100% | 312 | 241,566 |
| K20 | 10,112 | 4,019,324 | 100% | 302 | 235,414 |
| K19 | 9,875 | 3,617,176 | 100% | 234 | 216,470 |
| K18 | 9,259 | 3,229,261 | 100% | 5 | 187,326 |
| K17 | 8,274 | 3,011,950 | 100% | 152 | 174,789 |
| **Total** | **92,945** | **34,783,363** | **100%** | **3,584** | **2,559,861** |

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

## Election-Specific Display Overrides

The reviewed source of truth for historical names and no-result visibility is `data/manual/locality_display_overrides.csv`. These rules change presentation only; they do not delete 2022 geometry, create votes, or split a host locality's published aggregate.

- Locality code 3620 is displayed as `נירן` in K17-K21, matching the name in those election sources, while the retained 2022 geometry is `נערן`.
- `אבנת` has no standalone result in K17-K25 and is hidden for those elections. Its 2022 feature remains available for a future election in which it has an independent result.
- `מבואות יריחו` likewise has no standalone K17-K25 result and is hidden without removing its 2022 feature.

The compiler rejects a display rule that hides a locality in an election where that locality has a result row. It does not copy a host result onto a hidden component, because that would duplicate votes and falsely imply a component-level split.

The reproducible result-presence audit is `docs/LOCALITY_RESULT_PRESENCE_AUDIT.md`, with the complete 116-row exception inventory in `docs/LOCALITY_RESULT_PRESENCE_AUDIT.csv`. Of 1,227 meaningful locality/institution features, 1,111 have standalone results in all nine elections, 80 in some elections, and 36 in none. A separate 160 source features are structural facility, regional-council, or no-jurisdiction display footprints rather than candidate election localities.

The inventory is complete as a presence calculation, not as a historical or display-policy review. `נירן`/`נערן`, `אבנת`, `מבואות יריחו`, and the existing composite municipalities record decisions reviewed so far. Rows without a reviewed display rule remain open; their current neutral or visible state must not be interpreted as a final decision.

## Envelope Results

Envelope votes have no locality geometry and are never duplicated across polygons. `scripts/build_public_outputs.py` writes one aggregate per election under `data/processed/public/envelope_results/`. Each aggregate combines source-marked official envelope rows with reviewed military/special rows whose assignment target is `special:envelope_votes`; the latter remain separately countable in `election_summary.csv`.

The web app shows that aggregate as a selectable national result beside the map. Its detail panel includes actual voters, valid and invalid votes, the leading ballot, margin, contributing source rows, and the party breakdown. Turnout is omitted because envelope rows do not have a meaningful locality-level eligible-voter denominator.

## Statistical-Area Separation

Locality and statistical-area assignment are independent products:

- Locality mode uses the reviewed locality identity directly and has complete result-row coverage; its feature-presence/visibility audit remains open.
- Statistical-area mode still needs the polling-place building location when a locality has more than one 2022 statistical area.
- Historical composite rows may therefore be complete in locality mode while still awaiting address placement into one component's statistical areas.
- OSM and Photon work affects statistical-area coverage, not locality totals.

The final assignment table exposes this distinction through `locality_assignment_status`, `locality_geography_type`, `locality_geography_id`, `locality_result_code`, `locality_result_name`, and `is_locality_mapped` alongside the existing statistical-area assignment fields.

## Web Data Contract

The version 2 browser payload has mode-specific coverage. Locality payloads also carry:

- the combined official and reviewed-special envelope aggregate,
- election-specific hidden geography IDs for composite/component replacement and reviewed no-result display rules,
- composite locality records joined by stable `composite:<key>` IDs.

Generated-data tests require 100% locality coverage, ensure every visible result joins a geometry, ensure hidden component features have no simultaneous result, and validate envelope totals against the same party-vote contract used by map records.

## Neutral Land Coverage

The locality display geometry retains 160 structural CBS features: 56 special-purpose facility footprints, 48 regional-council footprints, and 56 no-jurisdiction/background footprints. The previously documented 58 polygons with no English locality label are a subset of these features. They carry no election result, so the web map renders them grey and non-interactive. This keeps Israeli land visually distinct from the sea, neighboring countries, Gaza, the unpolygoned parts of the West Bank, and Kinneret. Kinneret IDs are explicitly filtered in both geography modes.
