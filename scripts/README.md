# Scripts

Future ingestion/conversion scripts will live here.

Planned scripts:

- Fetch official election result resources.
- Normalize election result schemas.
- Convert polygon exports to web-friendly GeoJSON or PMTiles.
- Assign polling-place points to statistical areas.
- Aggregate results by statistical area and locality.

Current prototypes:

- `extract_k18_polling_places.py` extracts the scanned/OCRed K18 polling-place PDF into a raw table CSV, then reconciles it to the official K18 result datastore. `--validate` currently matches all 9,263 ordinary official K18 result rows and leaves only the special non-geographic row unmapped. It requires Python with `pdfplumber`.
