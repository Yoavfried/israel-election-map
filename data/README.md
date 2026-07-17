# Data Directory

This directory is for local source and generated data.

Expected subdirectories:

- `raw/` - downloaded source files, not committed.
- `manual/` - small reviewed/manual source files committed with the repo.
- `processed/` - normalized generated files, not committed.
- `cache/` - temporary API/download cache, not committed.

Current important raw inputs:

- `raw/election_results/` - official K17-K25 ballot rows fetched from data.gov.il datastore by `scripts/fetch_election_results.py`.
- `raw/cbs_historical_geography/` - official K17-K25 ballot crosswalks, 1995/2008/2011 geometry, and transition tables fetched by `scripts/fetch_cbs_historical_geography.py`.
- `raw/ezorim_statistiim_2022.gdb/` - canonical 2022 statistical-area polygon source.
- `raw/arcgis_elections2015.geojson` and `raw/arcgis_elections2019.geojson` - derivative layers used only for audited geometry supplements/display footprints, never for official vote totals.
- `raw/election-25_kalpi-places_kalpies_list_10_7_nagish.xlsx` - K25 polling-place address source.
- `raw/election-25_kalpi-places_statistic_report_10_7_nagish.xlsx` - K25 polling-place/statistical report source.
- `raw/archive_knesset24_kalpies_report_tofes_b_18_3_21.xlsx` - archived official K24 polling-place address source.
- `raw/archive_knesset23_kalpies_report_19_1_20_1.xlsx` - archived official K23 polling-place address source.
- `raw/archive_knesset22_kalpies_report_tofes_b_6th_edition_15_9.xlsx` - archived official K22 polling-place address source.
- `raw/archive_knesset21_kalpies_full_report.xls` - archived official K21 polling-place address source.
- `raw/archive_knesset20_tell_the_polls_9_3.xls` - archived official K20 polling-place address source.
- `raw/archive_knesset19_all_stations.pdf` - archived official K19 polling-place address source.
- `raw/archive_knesset18_kalpilist18.pdf` - archived official K18 polling-place list PDF.
- `raw/archive_knesset17_kalpies-list17-1.pdf` and `raw/archive_knesset17_kalpies-list17-2.pdf` - archived official K17 polling-place list scans.
- `manual/manual_k17_scanned_place_names.csv` - targeted manual extraction from the K17 scans for 11 rows whose official result address is empty.

Known Current Data Gaps:

- The ignored raw directory is not a complete fresh-clone bootstrap. Archived polling-place sources and the canonical 2022 FileGDB still require preparation from the sources in `docs/DATA_SOURCES.md`.
- Statistical-mode pending rows are missing from the available historical ballot crosswalks. They are not waiting for a geocode cache; see `docs/PROJECT_STATUS.md`.
- A reviewed geocode cache remains optional input for the separate polling-place-location research dataset. It does not assign election results.

Do not use the old partial `statistical-areas-2022.geojson` export as a project source.

Only reviewed manual inputs, small metadata/reference files, and documentation should be committed here. Raw downloads and generated outputs remain ignored.
