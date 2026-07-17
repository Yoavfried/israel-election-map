# Third-Party Data Notices

The repository's original software and documentation are licensed under the
MIT License. That license does not replace terms attached to source data,
third-party content, trademarks, or bundled dependencies.

## Israel Central Bureau of Statistics

Statistical-area geometry, locality metadata, transition tables, and
ballot-to-area tables originate from the Israel Central Bureau of Statistics
(CBS). CBS publishes website information under its open end-user license,
which permits commercial and non-commercial reuse subject to conditions that
include source acknowledgement, non-endorsement, accuracy, privacy, and
third-party-rights limitations:

https://www.cbs.gov.il/en/Pages/Enduser-license.aspx

Exact product names, source URLs, access records, and checksums are retained in
the source manifest and `docs/DATA_SOURCES.md`. Derived files continue to carry
their source and method fields.

## Election Results

Ballot-level election results originate from official Central Elections
Committee and Israeli government data publications. The project does not
relicense official source files, logos, or other protected presentation. Users
of redistributed tables are responsible for complying with the terms at the
source publication.

## ArcGIS Feature Services

Two externally supplied ArcGIS FeatureServer layers are used for explicitly
identified geometry supplements, display detail, and reviewed aggregate
reconstruction evidence. Their service metadata does not state a reusable
content license. The project therefore makes no broader licensing claim for
those source geometries or aggregates. Every derivative use is labeled in
geography metadata or row-level assignment provenance.

## Software Dependencies

Packages installed through Python and npm remain under their respective
licenses. See `requirements.txt`, `web/app/package.json`, and installed package
metadata for the applicable notices.
