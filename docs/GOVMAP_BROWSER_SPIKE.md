# GovMap Browser Spike

> Historical research note: this page tests polling-place building search. It is not a source for election-result statistical assignment.

Last updated: 2026-07-17

## Purpose

GovMap browser API tokens are approved for a specific web origin. The retained page under `web/geocode-spike/` runs the representative polling-place query sample from an approved deployment and exports review-oriented candidate data.

The token is entered at run time. It is not stored in source files, browser storage, or generated sample files.

## Runtime Origin Configuration

The repository does not embed a contributor-specific domain. Open the deployed page with the approved origin supplied as a URL-encoded query parameter:

```text
https://maps.example.org/geocode-spike/?approvedOrigin=https%3A%2F%2Fmaps.example.org
```

The page compares `window.location.origin` with that value and reports whether they match. This check is informational; GovMap remains the authority that accepts or rejects the token/origin pair.

## Prepare and Validate

```bash
python scripts/build_geocoding_spike_sample.py
python scripts/export_geocoding_spike_web.py
python scripts/check_geocode_spike_static.py
```

The page uses:

- `govmap.search(params)`
- `govmap.getSearchResultData(searchResult, apiToken)`

All returned candidates remain `needs_review`. Do not commit tokens or raw retained responses containing information that is not appropriate for the public repository.

## Live Check

1. Deploy `web/geocode-spike/` under the origin approved for the token.
2. Open the page with the `approvedOrigin` query parameter.
3. Confirm that the displayed origin matches.
4. Enter the token at run time.
5. Run one sample row before a batch.
6. Export the CSV and review locality, coordinates, match type, and raw-result provenance.

GovMap candidates may support a future polling-place layer. They must not be used to infer the residential statistical area represented by a ballot result.
