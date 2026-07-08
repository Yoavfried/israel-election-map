# GovMap Browser Spike

Last updated: 2026-07-08

## Purpose

GovMap API tokens are approved for a domain. The current token request is for:

```text
yoavfried.com
```

That means the useful pre-token work is to prepare a browser page that can run from that exact domain after approval. The page lives in:

```text
web/geocode-spike/
```

It uses the existing 50-row representative geocoding sample and calls the documented GovMap browser API:

- `govmap.search(params)`
- `govmap.getSearchResultData(searchResult, apiToken)`

The token is pasted into the page at run time. It is not stored in source files, browser storage, or generated sample files.

## What "Under yoavfried.com" Means

The page can be served from any path on the approved host. These should be equivalent for GovMap domain approval:

```text
https://yoavfried.com/geocode-spike/
https://yoavfried.com/israel-election-map/geocode-spike/
```

The important part is the browser origin:

```text
https://yoavfried.com
```

Opening the same files from another origin is not the same thing:

```text
http://localhost:8765/
https://www.yoavfried.com/
https://yoavfried.github.io/
```

Those are useful for page-preview only. Live GovMap calls may fail unless GovMap also approves that exact host.

## Pre-Token Checklist

Build the sample and export the browser payload:

```bash
python scripts/build_geocoding_spike_sample.py
python scripts/export_geocoding_spike_web.py
python scripts/check_geocode_spike_static.py
```

Preview the static page locally:

```bash
python -m http.server 8765 -d web/geocode-spike
```

Open:

```text
http://127.0.0.1:8765/
```

Pre-token checks available there:

- `sample.json` loads.
- The page reports the current origin.
- `Download dry-run CSV` creates a CSV with the same columns expected from the live browser spike.
- The table layout works on desktop and narrow widths.

Pre-token checks that cannot be completed:

- Whether GovMap accepts the approved token from `yoavfried.com`.
- Whether GovMap blocks browser requests by CORS or origin.
- Real match quality and ambiguity rates.

## Deployment Options

Preferred if `yoavfried.com` already has a host:

1. Copy the contents of `web/geocode-spike/` to a path under the existing site.
2. Open the resulting URL on `https://yoavfried.com/...`.
3. Confirm the page shows `Origin: https://yoavfried.com`.

Use GitHub Pages only if it is acceptable for this repository to serve the domain:

1. Configure GitHub Pages for the repository.
2. Set the custom domain to `yoavfried.com`.
3. Point the domain DNS to GitHub Pages.
4. Serve the `web/geocode-spike/` files from the published site.

This can affect the current `yoavfried.com` site, so do not use this route if the domain already hosts something important.

## After Token Approval

1. Open the deployed page from `https://yoavfried.com/...`.
2. Paste the GovMap token into the token field.
3. Run `Run first row`.
4. Inspect the first result in the table.
5. Run all sample rows.
6. Download the CSV.
7. Save the result as:

```text
data/processed/geocoding/govmap_spike_results.csv
```

All rows are exported with `review_status=needs_review`. Nothing from the spike becomes production geography until reviewed rows are promoted into:

```text
data/processed/geocoding/geocoded_points.csv
```
