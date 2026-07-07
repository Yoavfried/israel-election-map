# Locality Crosswalk Approval Table

Last updated: 2026-07-06

Scope note: this file was created during the earlier K16-K25 investigation. Current product scope is K17-K25; K16-only rows are retained as historical review/future-reactivation context.

This table reflects the manual review file imported from Downloads.

Fill or edit `review` and `Notes` as needed.

## Review Summary

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

## Full Review Table

| unique locality unmatched | possible match | confidence | reason | review | Notes |
| --- | --- | --- | --- | --- | --- |
| תל אביב - יפו | תל אביב -יפו | high | spelling_or_format_variant | TRUE |  |
| הרצליה | הרצלייה | high | spelling_or_format_variant | TRUE |  |
| מסעודין אל-עזאזמה [939] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| מודיעין-מכבים-רעו | מודיעין-מכבים-רעות* | high | spelling_or_format_variant | TRUE |  |
| נהריה | נהרייה | high | spelling_or_format_variant | TRUE |  |
| קרית אתא | קריית אתא | high | spelling_or_format_variant | TRUE |  |
| קרית מוצקין | קריית מוצקין | high | spelling_or_format_variant | TRUE |  |
| נצרת עילית | נוף הגליל | high | official_name_change | TRUE |  |
| קרית גת | קריית גת | high | spelling_or_format_variant | TRUE |  |
| קרית ביאליק | קריית ביאליק | high | spelling_or_format_variant | TRUE |  |
| קרית ים | קריית ים | high | spelling_or_format_variant | TRUE |  |
| קרית אונו | קריית אונו | high | spelling_or_format_variant | TRUE |  |
| יהוד-נווה אפרים | יהוד | low | official_name_change | TRUE |  |
| אבו רוקייק )שבט( [961] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אעצם )שבט( [963] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| שגור | בענה \| דייר אל-אסד \| מג'ד אל-כרום | low | historical_split | TRUE |  |
| קרית שמונה | קריית שמונה | high | spelling_or_format_variant | TRUE |  |
| אבו רובייעה )שבט( [966] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| קרית מלאכי | קריית מלאכי | high | spelling_or_format_variant | TRUE |  |
| אבו קורינאת )שבט( [968] | אבו קורינאת (יישוב) | low | recognized_tribal_locality | TRUE |  |
| באקה-ג'ת | באקה אל-גרביה \| ג'ת | high | historical_split | TRUE |  |
| קרית טבעון | קריית טבעון | high | spelling_or_format_variant | TRUE |  |
| עיר כרמל | דאלית אל-כרמל \| עספיא | high | historical_split | TRUE |  |
| צורן-קדימה | קדימה-צורן | high | spelling_or_format_variant | TRUE |  |
| בנימינה-גבעת עדה | בנימינה-גבעת עדה* | high | spelling_or_format_variant | TRUE |  |
| מכבים-רעות [1273] | מודיעין-מכבים-רעות* | low | merged_or_absorbed_locality | TRUE |  |
| הוואשלה )שבט( [1169] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| שער שומרון [3826] |  | low | no_clear_stat_area_locality_match | SH | עץ אפרים and שערי תקווה united in to שער שומרון |
| קרית עקרון | קריית עקרון | high | spelling_or_format_variant | TRUE |  |
| אטרש )שבט( [965] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אבו ג'ווייעד (שבט) [967] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אפרתה | אפרת | high | spelling_or_format_variant | TRUE |  |
| פרדסיה | פרדסייה | high | spelling_or_format_variant | TRUE |  |
| סייד )שבט( [1170] | אל סייד | low | recognized_tribal_locality | TRUE |  |
| קודייראת א-צאנע(שבט) [964] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| מעלה שומרון [3637] | קרני שומרון | low | merged_or_absorbed_locality | TRUE |  |
| הוזייל )שבט( [956] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| דבוריה | דבורייה | high | spelling_or_format_variant | TRUE |  |
| קרית ארבע | קריית ארבע | high | spelling_or_format_variant | TRUE |  |
| קבועה )שבט( [1234] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| צור יגאל [1306] | כוכב יאיר | low | merged_or_absorbed_locality | TRUE |  |
| צורן [1308] | קדימה-צורן | high | merged_or_absorbed_locality | TRUE |  |
| סביון | סביון* | high | spelling_or_format_variant | TRUE |  |
| חברון [3400] |  | low | no_clear_stat_area_locality_match | HEBRON | new point size polygon needed |
| רמת אפעל [1049] | רמת גן | low | merged_or_absorbed_locality | TRUE |  |
| רמת אפעל | רמת גן | low | merged_or_absorbed_locality | TRUE |  |
| נווה אפרים [1062] | יהוד | low | merged_or_absorbed_locality | TRUE |  |
| בית אריה | בית אריה-עופרים | high | merged_or_absorbed_locality | TRUE |  |
| קציר-חריש | קציר \| חריש | low | historical_split | TRUE |  |
| ג'נאביב )שבט( [976] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| כאוכב אבו אל-היג' | כאוכב אבו אל-היג'א | high | spelling_or_format_variant | TRUE |  |
| מחנה יפה [1415] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| כעביה-טבאש-חג'אג' | כעביה-טבאש-חג'אג'רה | high | spelling_or_format_variant | TRUE |  |
| גבעת עדה [50] | בנימינה-גבעת עדה* | low | merged_or_absorbed_locality | TRUE |  |
| נצאצרה )שבט( [1041] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| עוקבי )בנו עוקבה( [957] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| מחנה תל נוף [1412] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| עופרה | עפרה | high | spelling_or_format_variant | TRUE |  |
| קוואעין )שבט( [972] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| מסעודין אל-עזאזמה |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| קרית יערים | קריית יערים | high | spelling_or_format_variant | TRUE |  |
| טובא-זנגריה | טובא-זנגרייה | high | spelling_or_format_variant | TRUE |  |
| נורדיה | נורדייה | high | spelling_or_format_variant | TRUE |  |
| נווה דקלים [5427] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| אסד )שבט( [960] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אבו רוקייק (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אעצם (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| מחנה טלי [1418] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| מחנה יוכבד [1416] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| מחנה יהודית [1413] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| אבו קורינאת (שבט) | אבו קורינאת (יישוב) | low | recognized_tribal_locality | TRUE |  |
| תראבין א-צאנע (שבט) [970] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| חלמיש | נווה צוף | low | official_name_change | TRUE |  |
| מחנה הילה [1411] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| דליה | דלייה | high | spelling_or_format_variant | TRUE |  |
| מחנה מרים [1414] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| ריחאניה | ריחאנייה | high | spelling_or_format_variant | TRUE |  |
| אבו רובייעה (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| גני יהודה [781] | סביון* | low | merged_or_absorbed_locality | TRUE |  |
| נווה אפעל [2032] | רמת גן | low | merged_or_absorbed_locality | TRUE |  |
| סייד (שבט) | אל סייד | low | recognized_tribal_locality | TRUE |  |
| שגב | עצמון שגב | low | spelling_or_format_variant | TRUE |  |
| סתריה | סתרייה | high | spelling_or_format_variant | TRUE |  |
| קודייראת א-צאנע(ש |  | low | no_clear_stat_area_locality_match | TRIBE | add to tribal point polygon |
| ניסנית [5426] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| פוריה - נווה עובד | פורייה - נווה עובד | high | spelling_or_format_variant | TRUE |  |
| הוואשלה (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| עראמשה | עראמשה* | high | spelling_or_format_variant | TRUE |  |
| נווה אפעל | רמת גן | low | merged_or_absorbed_locality | TRUE |  |
| מעין צבי | מעיין צבי | high | spelling_or_format_variant | TRUE |  |
| עופרים [3792] | בית אריה-עופרים | high | merged_or_absorbed_locality | TRUE |  |
| כפר אז"ר | רמת גן | low | merged_or_absorbed_locality | TRUE |  |
| כפר אז"ר [180] | רמת גן | low | merged_or_absorbed_locality | TRUE |  |
| עטאוונה )שבט( [969] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| רמת פנקס [883] | אור יהודה | low | merged_or_absorbed_locality | TRUE |  |
| אבו עבדון )שבט( [958] |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| מעלה שומרון |  | low | no_clear_stat_area_locality_match |  | שכונה בקרני שומרון |
| ביריה | בירייה | high | spelling_or_format_variant | TRUE |  |
| רמת פנקס | אור יהודה | low | merged_or_absorbed_locality | TRUE |  |
| אשדות יעקב (איחו | אשדות יעקב (איחוד) | high | spelling_or_format_variant | TRUE |  |
| חמד | חמ"ד | high | spelling_or_format_variant | TRUE |  |
| פוריה עילית | פורייה עילית | high | spelling_or_format_variant | TRUE |  |
| צפריה | צפרייה | high | spelling_or_format_variant | TRUE |  |
| הודיה | הודייה | high | spelling_or_format_variant | TRUE |  |
| מחנה עדי [1417] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| אשדות יעקב (מאוח | אשדות יעקב (מאוחד) | high | spelling_or_format_variant | TRUE |  |
| אילניה | אילנייה | high | spelling_or_format_variant | TRUE |  |
| ח'ואלד )שבט( [986] | ח'ואלד | low | recognized_tribal_locality | TRUE |  |
| שושנת העמקים (רסק | שושנת העמקים | high | spelling_or_format_variant | TRUE |  |
| חברון |  | low | no_clear_stat_area_locality_match | HEBRON | new point size polygon needed |
| אטרש (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| קרית ענבים | קריית ענבים | high | spelling_or_format_variant | TRUE |  |
| אלי סיני [5428] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| כרמיה | כרמייה | high | spelling_or_format_variant | TRUE |  |
| מלכיה | מלכייה | high | spelling_or_format_variant | TRUE |  |
| מעין ברוך | מעיין ברוך | high | spelling_or_format_variant | TRUE |  |
| בני עצמון [5425] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| קרית נטפים | קריית נטפים | high | spelling_or_format_variant | TRUE |  |
| אל-רום | אל -רום | high | spelling_or_format_variant | TRUE |  |
| ניצנה (קהילת חינו | ניצנה (קהילת חינוך) | high | spelling_or_format_variant | TRUE |  |
| קבועה (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| גדיד [5429] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| קוואעין (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| גן אור [5431] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| קטיף [5423] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| תושיה | תושייה | high | spelling_or_format_variant | TRUE |  |
| פוריה - כפר עבודה | פורייה - כפר עבודה | high | spelling_or_format_variant | TRUE |  |
| כפר דרום [5405] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| מחנה יפה |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| מחנה תל נוף |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| נצרים [5408] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| כפר רוזנואלד (זרע | כפר רוזנואלד (זרעית) | high | spelling_or_format_variant | TRUE |  |
| עוקבי (בנו עוקבה) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| הוזייל (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אבו ג'ווייעד (שבט |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| אסד (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| בדולח [5432] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| חומש [3642] |  | high | retired_or_evacuated_locality | N.S. | new point in north samaria for elections where this is present that includes all gaza related locality results |
| מחנה טלי |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
| תראבין א-צאנע (שב |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| עטאוונה (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| סואעד )כמאנה( )שב [989] | כמאנה | low | recognized_tribal_locality | TRUE |  |
| גנים [3758] |  | high | retired_or_evacuated_locality | N.S. | new point in north samaria for elections where this is present that includes all gaza related locality results |
| מורג [5407] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| נעמי | נעמ"ה | low | spelling_or_format_variant | TRUE |  |
| ח'ואלד (שבט) | ח'ואלד | low | recognized_tribal_locality | TRUE |  |
| כדים [3729] |  | high | retired_or_evacuated_locality | N.S. | new point in north samaria for elections where this is present that includes all gaza related locality results |
| רפיח ים [5433] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| ג'נאביב (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| פאת שדה [5436] |  | high | retired_or_evacuated_locality | GAZA | new point in gaza for elections where this is present that includes all gaza related locality results |
| סואעד (כמאנה) (שב | כמאנה | low | recognized_tribal_locality | TRUE |  |
| נירן | נערן | low | spelling_or_format_variant | TRUE |  |
| סוואעד חמיירה | סואעד (חמרייה)* | low | recognized_tribal_locality | TRUE |  |
| נצאצרה (שבט) |  | low | tribal_or_dispersed_no_match | TRIBE | add to tribal point polygon |
| חצרות יסף [1404] |  | low | camp_or_base_not_in_stat_layer | ENVELOPE | camp votes can be treated like envelope votes |
