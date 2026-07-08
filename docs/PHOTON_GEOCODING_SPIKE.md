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
