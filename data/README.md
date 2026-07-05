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

Do not use the old partial `statistical-areas-2022.geojson` export as a project source.

Only small metadata files and documentation should be committed here.
