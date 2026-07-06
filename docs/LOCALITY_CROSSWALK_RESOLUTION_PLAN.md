# Locality Crosswalk Resolution Plan

Last updated: 2026-07-06

This file turns the reviewed locality crosswalk table into implementation actions.

Source review table:

- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.csv`

Derived full-resolution CSV:

- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.csv`

## Review Outcomes

| review | rows | solution |
| --- | --- | --- |
| TRUE | 88 | Use approved locality match; historical split rows with multiple possible matches require address geocoding into current polygons. |
| TRIBE | 35 | Custom tribal/dispersed-settlement point-size polygon. |
| GAZA | 13 | Custom Gaza evacuated-localities point-size polygon. |
| ENVELOPE | 12 | Special non-geographic bucket, handled like envelope votes. |
| N.S. | 3 | Custom Northern Samaria evacuated-localities point-size polygon. |
| HEBRON | 2 | Custom Hebron point-size polygon. |
| (blank) | 1 | One row: Ma'ale Shomron maps to Karnei Shomron based on note. |
| SH | 1 | Use polling-place addresses to assign Sha'ar Shomron rows to current polygons. |

## Solution Counts

| solution | rows |
| --- | --- |
| accepted_locality_match | 85 |
| custom_point_size_polygon | 53 |
| special_non_geographic | 12 |
| address_geocode_to_current_polygons | 5 |

## Custom Geometry Buckets

| custom geometry id | solution | rows | example source rows |
| --- | --- | --- | --- |
| custom:tribal_negev | custom_point_size_polygon | 35 | מסעודין אל-עזאזמה [939] \| אבו רוקייק )שבט( [961] \| אעצם )שבט( [963] \| אבו רובייעה )שבט( [966] \| הוואשלה )שבט( [1169] |
| custom:hebron | custom_point_size_polygon | 2 | חברון [3400] \| חברון |
| custom:gaza_evacuated_localities | custom_point_size_polygon | 13 | נווה דקלים [5427] \| ניסנית [5426] \| אלי סיני [5428] \| בני עצמון [5425] \| גדיד [5429] |
| custom:northern_samaria_evacuated_localities | custom_point_size_polygon | 3 | חומש [3642] \| גנים [3758] \| כדים [3729] |

## Implementation Decisions

- Accepted single-locality matches use the reviewed 2022 locality name.
- Accepted historical split rows with multiple possible current matches must be assigned by polling-place address/geocode into current polygons. Do not join polygons and do not split votes heuristically.
- `TRIBE`, `GAZA`, `N.S.`, and `HEBRON` become custom point-size polygon buckets. The visual design can be decided later, but the data model treats each bucket as a synthetic geography with preserved source-row contributions.
- `ENVELOPE` rows are non-geographic and should be handled like envelope/special votes: included in totals and details, not assigned to map polygons.
- `SH` represents `שער שומרון`; use polling-place addresses to assign each row to the relevant current polygon, usually `עץ אפרים` or `שערי תקווה`.
- The blank reviewed row with note `שכונה בקרני שומרון` is resolved to `קרני שומרון`.

## Full Resolution Table

| unique locality unmatched | review | possible match | solution | geometry target | custom geometry id | data handling | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| תל אביב - יפו | TRUE | תל אביב -יפו | accepted_locality_match | תל אביב -יפו |  | Use the reviewed 2022 locality match. |  |
| הרצליה | TRUE | הרצלייה | accepted_locality_match | הרצלייה |  | Use the reviewed 2022 locality match. |  |
| מסעודין אל-עזאזמה [939] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| מודיעין-מכבים-רעו | TRUE | מודיעין-מכבים-רעות* | accepted_locality_match | מודיעין-מכבים-רעות* |  | Use the reviewed 2022 locality match. |  |
| נהריה | TRUE | נהרייה | accepted_locality_match | נהרייה |  | Use the reviewed 2022 locality match. |  |
| קרית אתא | TRUE | קריית אתא | accepted_locality_match | קריית אתא |  | Use the reviewed 2022 locality match. |  |
| קרית מוצקין | TRUE | קריית מוצקין | accepted_locality_match | קריית מוצקין |  | Use the reviewed 2022 locality match. |  |
| נצרת עילית | TRUE | נוף הגליל | accepted_locality_match | נוף הגליל |  | Use the reviewed 2022 locality match. |  |
| קרית גת | TRUE | קריית גת | accepted_locality_match | קריית גת |  | Use the reviewed 2022 locality match. |  |
| קרית ביאליק | TRUE | קריית ביאליק | accepted_locality_match | קריית ביאליק |  | Use the reviewed 2022 locality match. |  |
| קרית ים | TRUE | קריית ים | accepted_locality_match | קריית ים |  | Use the reviewed 2022 locality match. |  |
| קרית אונו | TRUE | קריית אונו | accepted_locality_match | קריית אונו |  | Use the reviewed 2022 locality match. |  |
| יהוד-נווה אפרים | TRUE | יהוד | accepted_locality_match | יהוד |  | Use the reviewed 2022 locality match. |  |
| אבו רוקייק )שבט( [961] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אעצם )שבט( [963] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| שגור | TRUE | בענה \| דייר אל-אסד \| מג'ד אל-כרום | address_geocode_to_current_polygons | בענה \| דייר אל-אסד \| מג'ד אל-כרום |  | Use each ballot row's polling-place address and point-in-polygon result to assign votes to the correct current 2022 polygon. Do not join polygons and do not split votes heuristically. |  |
| קרית שמונה | TRUE | קריית שמונה | accepted_locality_match | קריית שמונה |  | Use the reviewed 2022 locality match. |  |
| אבו רובייעה )שבט( [966] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| קרית מלאכי | TRUE | קריית מלאכי | accepted_locality_match | קריית מלאכי |  | Use the reviewed 2022 locality match. |  |
| אבו קורינאת )שבט( [968] | TRUE | אבו קורינאת (יישוב) | accepted_locality_match | אבו קורינאת (יישוב) |  | Use the reviewed 2022 locality match. |  |
| באקה-ג'ת | TRUE | באקה אל-גרביה \| ג'ת | address_geocode_to_current_polygons | באקה אל-גרביה \| ג'ת |  | Use each ballot row's polling-place address and point-in-polygon result to assign votes to the correct current 2022 polygon. Do not join polygons and do not split votes heuristically. |  |
| קרית טבעון | TRUE | קריית טבעון | accepted_locality_match | קריית טבעון |  | Use the reviewed 2022 locality match. |  |
| עיר כרמל | TRUE | דאלית אל-כרמל \| עספיא | address_geocode_to_current_polygons | דאלית אל-כרמל \| עספיא |  | Use each ballot row's polling-place address and point-in-polygon result to assign votes to the correct current 2022 polygon. Do not join polygons and do not split votes heuristically. |  |
| צורן-קדימה | TRUE | קדימה-צורן | accepted_locality_match | קדימה-צורן |  | Use the reviewed 2022 locality match. |  |
| בנימינה-גבעת עדה | TRUE | בנימינה-גבעת עדה* | accepted_locality_match | בנימינה-גבעת עדה* |  | Use the reviewed 2022 locality match. |  |
| מכבים-רעות [1273] | TRUE | מודיעין-מכבים-רעות* | accepted_locality_match | מודיעין-מכבים-רעות* |  | Use the reviewed 2022 locality match. |  |
| הוואשלה )שבט( [1169] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| שער שומרון [3826] | SH |  | address_geocode_to_current_polygons | עץ אפרים \| שערי תקווה |  | Use each Sha'ar Shomron ballot row's polling-place address and point-in-polygon result to assign it to the relevant current polygon, usually Etz Efraim or Sha'arei Tikva. | עץ אפרים and שערי תקווה united in to שער שומרון |
| קרית עקרון | TRUE | קריית עקרון | accepted_locality_match | קריית עקרון |  | Use the reviewed 2022 locality match. |  |
| אטרש )שבט( [965] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אבו ג'ווייעד (שבט) [967] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אפרתה | TRUE | אפרת | accepted_locality_match | אפרת |  | Use the reviewed 2022 locality match. |  |
| פרדסיה | TRUE | פרדסייה | accepted_locality_match | פרדסייה |  | Use the reviewed 2022 locality match. |  |
| סייד )שבט( [1170] | TRUE | אל סייד | accepted_locality_match | אל סייד |  | Use the reviewed 2022 locality match. |  |
| קודייראת א-צאנע(שבט) [964] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| מעלה שומרון [3637] | TRUE | קרני שומרון | accepted_locality_match | קרני שומרון |  | Use the reviewed 2022 locality match. |  |
| הוזייל )שבט( [956] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| דבוריה | TRUE | דבורייה | accepted_locality_match | דבורייה |  | Use the reviewed 2022 locality match. |  |
| קרית ארבע | TRUE | קריית ארבע | accepted_locality_match | קריית ארבע |  | Use the reviewed 2022 locality match. |  |
| קבועה )שבט( [1234] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| צור יגאל [1306] | TRUE | כוכב יאיר | accepted_locality_match | כוכב יאיר |  | Use the reviewed 2022 locality match. |  |
| צורן [1308] | TRUE | קדימה-צורן | accepted_locality_match | קדימה-צורן |  | Use the reviewed 2022 locality match. |  |
| סביון | TRUE | סביון* | accepted_locality_match | סביון* |  | Use the reviewed 2022 locality match. |  |
| חברון [3400] | HEBRON |  | custom_point_size_polygon | custom:hebron | custom:hebron | Aggregate Hebron rows into one Hebron custom area and preserve source-row contributions. | new point size polygon needed |
| רמת אפעל [1049] | TRUE | רמת גן | accepted_locality_match | רמת גן |  | Use the reviewed 2022 locality match. |  |
| רמת אפעל | TRUE | רמת גן | accepted_locality_match | רמת גן |  | Use the reviewed 2022 locality match. |  |
| נווה אפרים [1062] | TRUE | יהוד | accepted_locality_match | יהוד |  | Use the reviewed 2022 locality match. |  |
| בית אריה | TRUE | בית אריה-עופרים | accepted_locality_match | בית אריה-עופרים |  | Use the reviewed 2022 locality match. |  |
| קציר-חריש | TRUE | קציר \| חריש | address_geocode_to_current_polygons | קציר \| חריש |  | Use each ballot row's polling-place address and point-in-polygon result to assign votes to the correct current 2022 polygon. Do not join polygons and do not split votes heuristically. |  |
| ג'נאביב )שבט( [976] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| כאוכב אבו אל-היג' | TRUE | כאוכב אבו אל-היג'א | accepted_locality_match | כאוכב אבו אל-היג'א |  | Use the reviewed 2022 locality match. |  |
| מחנה יפה [1415] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| כעביה-טבאש-חג'אג' | TRUE | כעביה-טבאש-חג'אג'רה | accepted_locality_match | כעביה-טבאש-חג'אג'רה |  | Use the reviewed 2022 locality match. |  |
| גבעת עדה [50] | TRUE | בנימינה-גבעת עדה* | accepted_locality_match | בנימינה-גבעת עדה* |  | Use the reviewed 2022 locality match. |  |
| נצאצרה )שבט( [1041] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| עוקבי )בנו עוקבה( [957] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| מחנה תל נוף [1412] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| עופרה | TRUE | עפרה | accepted_locality_match | עפרה |  | Use the reviewed 2022 locality match. |  |
| קוואעין )שבט( [972] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| מסעודין אל-עזאזמה | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| קרית יערים | TRUE | קריית יערים | accepted_locality_match | קריית יערים |  | Use the reviewed 2022 locality match. |  |
| טובא-זנגריה | TRUE | טובא-זנגרייה | accepted_locality_match | טובא-זנגרייה |  | Use the reviewed 2022 locality match. |  |
| נורדיה | TRUE | נורדייה | accepted_locality_match | נורדייה |  | Use the reviewed 2022 locality match. |  |
| נווה דקלים [5427] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| אסד )שבט( [960] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אבו רוקייק (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אעצם (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| מחנה טלי [1418] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| מחנה יוכבד [1416] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| מחנה יהודית [1413] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| אבו קורינאת (שבט) | TRUE | אבו קורינאת (יישוב) | accepted_locality_match | אבו קורינאת (יישוב) |  | Use the reviewed 2022 locality match. |  |
| תראבין א-צאנע (שבט) [970] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| חלמיש | TRUE | נווה צוף | accepted_locality_match | נווה צוף |  | Use the reviewed 2022 locality match. |  |
| מחנה הילה [1411] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| דליה | TRUE | דלייה | accepted_locality_match | דלייה |  | Use the reviewed 2022 locality match. |  |
| מחנה מרים [1414] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| ריחאניה | TRUE | ריחאנייה | accepted_locality_match | ריחאנייה |  | Use the reviewed 2022 locality match. |  |
| אבו רובייעה (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| גני יהודה [781] | TRUE | סביון* | accepted_locality_match | סביון* |  | Use the reviewed 2022 locality match. |  |
| נווה אפעל [2032] | TRUE | רמת גן | accepted_locality_match | רמת גן |  | Use the reviewed 2022 locality match. |  |
| סייד (שבט) | TRUE | אל סייד | accepted_locality_match | אל סייד |  | Use the reviewed 2022 locality match. |  |
| שגב | TRUE | עצמון שגב | accepted_locality_match | עצמון שגב |  | Use the reviewed 2022 locality match. |  |
| סתריה | TRUE | סתרייה | accepted_locality_match | סתרייה |  | Use the reviewed 2022 locality match. |  |
| קודייראת א-צאנע(ש | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| ניסנית [5426] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| פוריה - נווה עובד | TRUE | פורייה - נווה עובד | accepted_locality_match | פורייה - נווה עובד |  | Use the reviewed 2022 locality match. |  |
| הוואשלה (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| עראמשה | TRUE | עראמשה* | accepted_locality_match | עראמשה* |  | Use the reviewed 2022 locality match. |  |
| נווה אפעל | TRUE | רמת גן | accepted_locality_match | רמת גן |  | Use the reviewed 2022 locality match. |  |
| מעין צבי | TRUE | מעיין צבי | accepted_locality_match | מעיין צבי |  | Use the reviewed 2022 locality match. |  |
| עופרים [3792] | TRUE | בית אריה-עופרים | accepted_locality_match | בית אריה-עופרים |  | Use the reviewed 2022 locality match. |  |
| כפר אז"ר | TRUE | רמת גן | accepted_locality_match | רמת גן |  | Use the reviewed 2022 locality match. |  |
| כפר אז"ר [180] | TRUE | רמת גן | accepted_locality_match | רמת גן |  | Use the reviewed 2022 locality match. |  |
| עטאוונה )שבט( [969] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| רמת פנקס [883] | TRUE | אור יהודה | accepted_locality_match | אור יהודה |  | Use the reviewed 2022 locality match. |  |
| אבו עבדון )שבט( [958] | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| מעלה שומרון |  |  | accepted_locality_match | קרני שומרון |  | Treat as a neighborhood of Karnei Shomron and use the 2022 locality match. | שכונה בקרני שומרון |
| ביריה | TRUE | בירייה | accepted_locality_match | בירייה |  | Use the reviewed 2022 locality match. |  |
| רמת פנקס | TRUE | אור יהודה | accepted_locality_match | אור יהודה |  | Use the reviewed 2022 locality match. |  |
| אשדות יעקב (איחו | TRUE | אשדות יעקב (איחוד) | accepted_locality_match | אשדות יעקב (איחוד) |  | Use the reviewed 2022 locality match. |  |
| חמד | TRUE | חמ"ד | accepted_locality_match | חמ"ד |  | Use the reviewed 2022 locality match. |  |
| פוריה עילית | TRUE | פורייה עילית | accepted_locality_match | פורייה עילית |  | Use the reviewed 2022 locality match. |  |
| צפריה | TRUE | צפרייה | accepted_locality_match | צפרייה |  | Use the reviewed 2022 locality match. |  |
| הודיה | TRUE | הודייה | accepted_locality_match | הודייה |  | Use the reviewed 2022 locality match. |  |
| מחנה עדי [1417] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| אשדות יעקב (מאוח | TRUE | אשדות יעקב (מאוחד) | accepted_locality_match | אשדות יעקב (מאוחד) |  | Use the reviewed 2022 locality match. |  |
| אילניה | TRUE | אילנייה | accepted_locality_match | אילנייה |  | Use the reviewed 2022 locality match. |  |
| ח'ואלד )שבט( [986] | TRUE | ח'ואלד | accepted_locality_match | ח'ואלד |  | Use the reviewed 2022 locality match. |  |
| שושנת העמקים (רסק | TRUE | שושנת העמקים | accepted_locality_match | שושנת העמקים |  | Use the reviewed 2022 locality match. |  |
| חברון | HEBRON |  | custom_point_size_polygon | custom:hebron | custom:hebron | Aggregate Hebron rows into one Hebron custom area and preserve source-row contributions. | new point size polygon needed |
| אטרש (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| קרית ענבים | TRUE | קריית ענבים | accepted_locality_match | קריית ענבים |  | Use the reviewed 2022 locality match. |  |
| אלי סיני [5428] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| כרמיה | TRUE | כרמייה | accepted_locality_match | כרמייה |  | Use the reviewed 2022 locality match. |  |
| מלכיה | TRUE | מלכייה | accepted_locality_match | מלכייה |  | Use the reviewed 2022 locality match. |  |
| מעין ברוך | TRUE | מעיין ברוך | accepted_locality_match | מעיין ברוך |  | Use the reviewed 2022 locality match. |  |
| בני עצמון [5425] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| קרית נטפים | TRUE | קריית נטפים | accepted_locality_match | קריית נטפים |  | Use the reviewed 2022 locality match. |  |
| אל-רום | TRUE | אל -רום | accepted_locality_match | אל -רום |  | Use the reviewed 2022 locality match. |  |
| ניצנה (קהילת חינו | TRUE | ניצנה (קהילת חינוך) | accepted_locality_match | ניצנה (קהילת חינוך) |  | Use the reviewed 2022 locality match. |  |
| קבועה (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| גדיד [5429] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| קוואעין (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| גן אור [5431] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| קטיף [5423] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| תושיה | TRUE | תושייה | accepted_locality_match | תושייה |  | Use the reviewed 2022 locality match. |  |
| פוריה - כפר עבודה | TRUE | פורייה - כפר עבודה | accepted_locality_match | פורייה - כפר עבודה |  | Use the reviewed 2022 locality match. |  |
| כפר דרום [5405] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| מחנה יפה | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| מחנה תל נוף | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| נצרים [5408] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| כפר רוזנואלד (זרע | TRUE | כפר רוזנואלד (זרעית) | accepted_locality_match | כפר רוזנואלד (זרעית) |  | Use the reviewed 2022 locality match. |  |
| עוקבי (בנו עוקבה) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| הוזייל (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אבו ג'ווייעד (שבט | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| אסד (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| בדולח [5432] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| חומש [3642] | N.S. |  | custom_point_size_polygon | custom:northern_samaria_evacuated_localities | custom:northern_samaria_evacuated_localities | Aggregate all Northern Samaria evacuated-locality rows per election into one custom area and preserve source-row contributions. | new point in north samaria for elections where this is present that includes all gaza related locality results |
| מחנה טלי | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
| תראבין א-צאנע (שב | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| עטאוונה (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| סואעד )כמאנה( )שב [989] | TRUE | כמאנה | accepted_locality_match | כמאנה |  | Use the reviewed 2022 locality match. |  |
| גנים [3758] | N.S. |  | custom_point_size_polygon | custom:northern_samaria_evacuated_localities | custom:northern_samaria_evacuated_localities | Aggregate all Northern Samaria evacuated-locality rows per election into one custom area and preserve source-row contributions. | new point in north samaria for elections where this is present that includes all gaza related locality results |
| מורג [5407] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| נעמי | TRUE | נעמ"ה | accepted_locality_match | נעמ"ה |  | Use the reviewed 2022 locality match. |  |
| ח'ואלד (שבט) | TRUE | ח'ואלד | accepted_locality_match | ח'ואלד |  | Use the reviewed 2022 locality match. |  |
| כדים [3729] | N.S. |  | custom_point_size_polygon | custom:northern_samaria_evacuated_localities | custom:northern_samaria_evacuated_localities | Aggregate all Northern Samaria evacuated-locality rows per election into one custom area and preserve source-row contributions. | new point in north samaria for elections where this is present that includes all gaza related locality results |
| רפיח ים [5433] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| ג'נאביב (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| פאת שדה [5436] | GAZA |  | custom_point_size_polygon | custom:gaza_evacuated_localities | custom:gaza_evacuated_localities | Aggregate all Gaza evacuated-locality rows per election into one Gaza custom area and preserve source-row contributions. | new point in gaza for elections where this is present that includes all gaza related locality results |
| סואעד (כמאנה) (שב | TRUE | כמאנה | accepted_locality_match | כמאנה |  | Use the reviewed 2022 locality match. |  |
| נירן | TRUE | נערן | accepted_locality_match | נערן |  | Use the reviewed 2022 locality match. |  |
| סוואעד חמיירה | TRUE | סואעד (חמרייה)* | accepted_locality_match | סואעד (חמרייה)* |  | Use the reviewed 2022 locality match. |  |
| נצאצרה (שבט) | TRIBE |  | custom_point_size_polygon | custom:tribal_negev | custom:tribal_negev | Aggregate all TRIBE rows per election into a single tribal/dispersed-settlement custom area and preserve source-row contributions. | add to tribal point polygon |
| חצרות יסף [1404] | ENVELOPE |  | special_non_geographic | special:envelope_votes |  | Treat like envelope/special votes: include in totals and details, but keep out of geographic polygon assignment. | camp votes can be treated like envelope votes |
