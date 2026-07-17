# AGS Historical QA

Last updated: 2026-07-16

## Correct Interpretation

An election source AGS can describe the statistical area assigned to a ballot row or its voters. It does not necessarily describe the statistical area containing the polling-place building.

That explains why several kalpis at one address can carry different AGS values. It also means a single observed AGS at an address is not proof that the building lies inside that area.

## Product Decision

The project now uses the official CBS ballot-to-statistical-area crosswalks for K17-K25 as the primary election assignment source. See `docs/HISTORICAL_STATISTICAL_AREA_ASSIGNMENT.md`.

The old proposed QA test, "geocode the polling place and require it to fall inside source AGS," is not a valid assignment gate. A mismatch may be completely legitimate because the building and the voters it serves are different geographic concepts.

K23 `source_ags` remains preserved through the address pipeline. It may still be useful as diagnostic context when reviewing a geocoder, but it must not accept, reject, or relocate election-result rows.

## Address-Geolocation Scope

OSM, Photon, and other geocoders remain useful for:

- locating polling-place buildings;
- checking address parsing and source OCR;
- future polling-place search or facility-map features;
- detecting obvious wrong-locality geocoder responses.

They are not used to assign votes to historical statistical areas.
