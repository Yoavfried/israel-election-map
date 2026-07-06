# Scripts

Future ingestion/conversion scripts will live here.

Planned scripts:

- Fetch official election result resources.
- Normalize election result schemas.
- Convert polygon exports to web-friendly GeoJSON or PMTiles.
- Assign polling-place points to statistical areas.
- Aggregate results by statistical area and locality.

Current prototypes:

- `extract_k18_polling_places.py` extracts the scanned/OCRed K18 polling-place PDF into CSV and can validate extracted locality/kalpi keys against the official K18 result datastore. It requires Python with `pdfplumber`.
