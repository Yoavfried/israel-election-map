# Photon Geocoding Spike

Last updated: 2026-07-08

## Status

Photon is installed locally through a Nominatim-backed import from the Geofabrik Israel/Palestine OpenStreetMap extract.

The local services used during setup are:

- Nominatim HTTP: `http://127.0.0.1:18080`
- Nominatim/Postgres: `127.0.0.1:15432`
- Photon API: `http://127.0.0.1:2322/api`

Nominatim was verified with a Hebrew Jerusalem query. Photon was verified to respond, but the first manual test returned wrong-locality bus-stop matches for `Begin 1 Jerusalem / Menachem Begin 1 Jerusalem`, so quality is not assumed.

## Local Setup Summary

The local Nominatim database was built from:

- `https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf`

Photon was imported from Nominatim using Photon `1.2.1`:

```powershell
java -Xmx6g -jar "$PhotonJar" import `
  -data-dir "$PhotonData" `
  -host 127.0.0.1 `
  -port 15432 `
  -database nominatim `
  -user nominatim `
  -password nominatim_pass_local `
  -languages he,en,ar `
  -country-codes il,ps `
  -j 4
```

Serve Photon locally with:

```powershell
java -Xmx4g -jar "$PhotonJar" serve `
  -data-dir "$PhotonData" `
  -listen-ip 127.0.0.1 `
  -listen-port 2322 `
  -default-language he `
  -max-results 10
```

## Spike Runner

Run a dry run:

```bash
python scripts/run_photon_geocoding_spike.py --dry-run
```

Run live against the local Photon server:

```bash
python scripts/run_photon_geocoding_spike.py --limit 50
```

Output:

- `data/processed/geocoding/photon_spike_results.csv`

All rows are marked `review_status=needs_review`. Photon is a candidate source only after manual inspection confirms that returned coordinates match the expected locality/statistical-area context.


## Current Spike Result

The first 50-row live Photon spike completed locally:

- `matched`: 46
- `no_match`: 4
- `expected_locality_seen`: 36
- `expected_locality_not_seen`: 10
- `not_checked`: 4, corresponding to no-match rows

The locality check is conservative and can flag spelling/orthography variants for review, but the spike also exposed real wrong-locality matches for school/place-name queries. Photon remains useful as a free candidate, but only with locality/stat-area validation and manual review before promotion to `geocoded_points.csv`.


## Full Work-Unit Run

A local Photon run over all 7,196 deduplicated geocoding work units produced:

| Query type | Units | Rows | Actual voters | Photon matched + expected locality text seen | Photon matched but expected locality text not seen | Photon no-match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Address with locality | 6,727 | 73,473 | 28,190,018 | 5,612 units / 64,220 rows / 24,775,385 voters | 672 units / 6,439 rows / 2,383,415 voters | 443 units / 2,814 rows / 1,031,218 voters |
| Place with locality | 451 | 4,761 | 1,796,049 | 136 units / 1,696 rows / 642,525 voters | 126 units / 1,477 rows / 561,284 voters | 189 units / 1,588 rows / 592,240 voters |
| Place only | 18 | 60 | 22,246 | 12 units / 35 rows / 13,262 voters | 4 units / 17 rows / 6,138 voters | 2 units / 8 rows / 2,846 voters |

Interpretation:

- True `place_only` is small: 18 unique work units, 60 ballot rows, 22,246 actual voters. This is feasible for manual review.
- All non-address queries (`place_with_locality` + `place_only`) are 469 unique work units, 4,821 ballot rows, 1,818,295 actual voters. That is too large to resolve fully by hand as a first pass.
- Address queries are the strongest Photon use case, but still cannot be accepted blindly. In the full run, Photon returned many plausible address matches, but also real wrong-locality matches.
- The practical Photon use rule should be: accept a Photon coordinate only if it passes a spatial locality validation against the expected 2022 locality polygon or an approved historical locality/crosswalk rule. Text locality checks are useful diagnostics but not sufficient.
