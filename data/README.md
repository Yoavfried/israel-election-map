# Data Directory

This directory is for local source and generated data.

Expected subdirectories:

- `raw/` - downloaded source files, not committed.
- `processed/` - normalized generated files, not committed.
- `cache/` - temporary API/download cache, not committed.

Current important raw inputs:

- `raw/ezorim_statistiim_2022.gdb/` - canonical 2022 statistical-area polygon source.
- `raw/election-25_kalpi-places_kalpies_list_10_7_nagish.xlsx` - K25 polling-place address source.
- `raw/election-25_kalpi-places_statistic_report_10_7_nagish.xlsx` - K25 polling-place/statistical report source.
- `raw/archive_knesset21_kalpies_full_report.xls` - archived official K21 polling-place address source.
- `raw/archive_knesset20_tell_the_polls_9_3.xls` - archived official K20 polling-place address source.
- `raw/archive_knesset19_all_stations.pdf` - archived official K19 polling-place address source.
- `raw/archive_knesset18_kalpilist18.pdf` - archived official K18 polling-place list PDF.
- `raw/archive_knesset17_kalpies-list17-1.pdf` and `raw/archive_knesset17_kalpies-list17-2.pdf` - archived official K17 polling-place list scans.

Do not use the old partial `statistical-areas-2022.geojson` export as a project source.

Only small metadata files and documentation should be committed here.
