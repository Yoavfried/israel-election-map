# ArcGIS Geocoding Spike

Last updated: 2026-07-08

## Why This Exists

GovMap remains the preferred Israeli-government source, and the GovMap browser spike remains in place. ArcGIS is added as a separate fallback candidate because GovMap approval may be slow, denied, or impractical for bulk geocoding.

Do not delete or replace the GovMap preparation. Provider comparison is now part of the geocoding decision.

## Coverage Finding

Esri's ArcGIS Geocoding service lists Israel as Level 1 coverage. For Israel, it lists:

- supported country codes: `ISR`, `IL`
- supported languages: Hebrew, Hebrew transliterated, Arabic, Arabic transliterated, English
- supported language codes: `HE`, `HEB`, `EN`, `ENG`, `AR`, `ARA`
- authoritative data sources: CBS, SPNI NETIVEI, NPA

Source:

- https://developers.arcgis.com/rest/geocode/geocode-coverage/

This makes ArcGIS plausible enough to test on the same 50-row representative sample.

## Endpoint

The spike uses:

```text
https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates
```

Request shape:

- `SingleLine`: our deduplicated Hebrew geocoder query
- `sourceCountry=ISR`
- `langCode=HE`
- `outSR=4326`
- `maxLocations=3`
- `searchExtent=34.1,29.3,35.9,33.6`
- `location=34.8516,31.0461`
- `locationType=rooftop`
- `forStorage=true` by default

If `sourceCountry=ISR` returns no candidates, the script can retry without `sourceCountry`. This matters because ArcGIS notes that disputed-region geocoded locations can have blank country output; some election polling places may be outside Israel's internationally recognized borders.

## Storage and Licensing Guardrail

ArcGIS distinguishes temporary display from stored geocoding results.

For this project, reviewed coordinates are intended to be cached, joined to election rows, and possibly published. Therefore ArcGIS production or retained spike output should use:

```text
forStorage=true
```

That requires an ArcGIS access token/API key with stored-geocoding privileges. The script defaults to `forStorage=true`. Use `--temporary` only for throwaway experiments whose results will not be retained or promoted.

Relevant docs:

- https://developers.arcgis.com/rest/geocode/find-address-candidates/

## Run

Build the shared 50-row sample:

```bash
python scripts/build_geocoding_spike_sample.py
```

Dry run without a token:

```bash
python scripts/run_arcgis_geocoding_spike.py --dry-run
```

Live run with a token:

```bash
set ARCGIS_ACCESS_TOKEN=...
python scripts/run_arcgis_geocoding_spike.py --limit 50
```

Output:

```text
data/processed/geocoding/arcgis_spike_results.csv
```

All output rows are marked:

```text
review_status=needs_review
```

Successful ArcGIS rows must be manually reviewed before any coordinate is promoted into:

```text
data/processed/geocoding/geocoded_points.csv
```

## No-Token Probe

On 2026-07-08, two one-row probes were run without an access token:

```bash
python scripts/run_arcgis_geocoding_spike.py --allow-no-token --limit 1 --sleep-ms 0 --output data/cache/arcgis_no_token_probe.csv
python scripts/run_arcgis_geocoding_spike.py --legacy-endpoint --allow-no-token --limit 1 --sleep-ms 0 --output data/cache/arcgis_legacy_no_token_probe.csv
```

Observed results:

- `https://geocode-api.arcgis.com/...` returned `403 Anonymous access is not allowed for geocode-api.arcgis.com`.
- `https://geocode.arcgis.com/...` returned `499 Token required but not passed in the request.`

Conclusion: ArcGIS is not a no-token replacement for GovMap. It is still a useful fallback if an ArcGIS access token/API key is available and its storage privileges fit the project.

## Evaluation Questions

The ArcGIS spike should answer:

- Does Hebrew `SingleLine` geocoding work well for Israeli street addresses?
- Does `sourceCountry=ISR` hurt West Bank/locality edge cases?
- Do place-name-only K17/K18/K19 rows resolve usefully or too vaguely?
- Are matched types mostly `PointAddress` / `StreetAddress`, or too many admin/place matches?
- Are scores and result metadata sufficient for automated pre-filtering?
- Can we legally store/cache/publish the reviewed coordinates under the available ArcGIS token?
