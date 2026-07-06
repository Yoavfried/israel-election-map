# Locality Crosswalk Approval Table

Last updated: 2026-07-05

This table proposes one review action for each of the 155 unmatched K16-K25 locality identities.

Full review table:

- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.csv`

Use `approval_status` to mark each row as `approved`, `false`, or another reviewed state. Do not treat rows as accepted until reviewed.

## Proposed Actions

| Proposed action | Rows |
| --- | --- |
| map_to_2022_locality | 84 |
| no_2022_stat_area_assignment | 67 |
| split_multi_target | 4 |

## Confidence

| Confidence | Rows |
| --- | --- |
| medium | 75 |
| high | 74 |
| low | 6 |

## Top Rows By Affected Voters

| Review ID | Source locality | Affected voters | Proposed action | Proposed target | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 | תל אביב - יפו | 214,688 | map_to_2022_locality | תל אביב -יפו | high |
| 2 | הרצליה | 47,119 | map_to_2022_locality | הרצלייה | high |
| 3 | 939 מסעודין אל-עזאזמה | 26,595 | no_2022_stat_area_assignment |  | medium |
| 4 | מודיעין-מכבים-רעו | 25,732 | map_to_2022_locality | מודיעין-מכבים-רעות* | high |
| 5 | נהריה | 23,604 | map_to_2022_locality | נהרייה | high |
| 6 | קרית אתא | 23,434 | map_to_2022_locality | קריית אתא | high |
| 7 | קרית מוצקין | 20,772 | map_to_2022_locality | קריית מוצקין | high |
| 8 | נצרת עילית | 20,718 | map_to_2022_locality | נוף הגליל | high |
| 9 | קרית גת | 19,866 | map_to_2022_locality | קריית גת | high |
| 10 | קרית ביאליק | 19,537 | map_to_2022_locality | קריית ביאליק | high |
| 11 | קרית ים | 18,078 | map_to_2022_locality | קריית ים | high |
| 12 | קרית אונו | 14,643 | map_to_2022_locality | קריית אונו | high |
| 13 | יהוד-נווה אפרים | 13,087 | map_to_2022_locality | יהוד | medium |
| 14 | 961 אבו רוקייק )שבט( | 12,975 | no_2022_stat_area_assignment |  | medium |
| 15 | 963 אעצם )שבט( | 12,726 | no_2022_stat_area_assignment |  | medium |
| 16 | שגור | 11,069 | split_multi_target | בענה \| דייר אל-אסד \| מג'ד אל-כרום | medium |
| 17 | קרית שמונה | 9,028 | map_to_2022_locality | קריית שמונה | high |
| 18 | 966 אבו רובייעה )שבט( | 8,831 | no_2022_stat_area_assignment |  | medium |
| 19 | קרית מלאכי | 7,900 | map_to_2022_locality | קריית מלאכי | high |
| 20 | 968 אבו קורינאת )שבט( | 7,880 | map_to_2022_locality | אבו קורינאת (יישוב) | medium |
| 21 | באקה-ג'ת | 7,880 | split_multi_target | באקה אל-גרביה \| ג'ת | high |
| 22 | קרית טבעון | 7,873 | map_to_2022_locality | קריית טבעון | high |
| 23 | עיר כרמל | 7,703 | split_multi_target | דאלית אל-כרמל \| עספיא | high |
| 24 | צורן-קדימה | 6,878 | map_to_2022_locality | קדימה-צורן | high |
| 25 | בנימינה-גבעת עדה | 4,955 | map_to_2022_locality | בנימינה-גבעת עדה* | high |
| 26 | 1273 מכבים-רעות | 4,949 | map_to_2022_locality | מודיעין-מכבים-רעות* | medium |
| 27 | 1169 הוואשלה )שבט( | 4,656 | no_2022_stat_area_assignment |  | medium |
| 28 | 3826 שער שומרון | 4,173 | no_2022_stat_area_assignment |  | medium |
| 29 | קרית עקרון | 4,140 | map_to_2022_locality | קריית עקרון | high |
| 30 | 965 אטרש )שבט( | 3,627 | no_2022_stat_area_assignment |  | medium |
| 31 | 967 אבו ג'ווייעד (שבט) | 3,480 | no_2022_stat_area_assignment |  | medium |
| 32 | אפרתה | 3,467 | map_to_2022_locality | אפרת | high |
| 33 | פרדסיה | 2,920 | map_to_2022_locality | פרדסייה | high |
| 34 | 1170 סייד )שבט( | 2,892 | map_to_2022_locality | אל סייד | medium |
| 35 | 964 קודייראת א-צאנע(שבט) | 2,805 | no_2022_stat_area_assignment |  | medium |
| 36 | 3637 מעלה שומרון | 2,779 | map_to_2022_locality | קרני שומרון | medium |
| 37 | 956 הוזייל )שבט( | 2,738 | no_2022_stat_area_assignment |  | medium |
| 38 | דבוריה | 2,681 | map_to_2022_locality | דבורייה | high |
| 39 | קרית ארבע | 2,649 | map_to_2022_locality | קריית ארבע | high |
| 40 | 1234 קבועה )שבט( | 2,522 | no_2022_stat_area_assignment |  | medium |

## Full Review Table

| Review ID | Status | Source code | Source name | Elections | Affected voters | Proposed action | Target codes | Target names | Confidence | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | pending |  | תל אביב - יפו | K17 | 214,688 | map_to_2022_locality | 5000 | תל אביב -יפו | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 2 | pending |  | הרצליה | K17 | 47,119 | map_to_2022_locality | 6400 | הרצלייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 3 | pending | 939 | מסעודין אל-עזאזמה | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 26,595 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 4 | pending |  | מודיעין-מכבים-רעו | K17 | 25,732 | map_to_2022_locality | 1200 | מודיעין-מכבים-רעות* | high | K17 name is truncated; 2022 target is Modi'in-Maccabim-Re'ut. |
| 5 | pending |  | נהריה | K17 | 23,604 | map_to_2022_locality | 9100 | נהרייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 6 | pending |  | קרית אתא | K17 | 23,434 | map_to_2022_locality | 6800 | קריית אתא | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 7 | pending |  | קרית מוצקין | K17 | 20,772 | map_to_2022_locality | 8200 | קריית מוצקין | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 8 | pending |  | נצרת עילית | K17 | 20,718 | map_to_2022_locality | 1061 | נוף הגליל | high | Nazareth Illit was renamed Nof HaGalil. |
| 9 | pending |  | קרית גת | K17 | 19,866 | map_to_2022_locality | 2630 | קריית גת | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 10 | pending |  | קרית ביאליק | K17 | 19,537 | map_to_2022_locality | 9500 | קריית ביאליק | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 11 | pending |  | קרית ים | K17 | 18,078 | map_to_2022_locality | 9600 | קריית ים | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 12 | pending |  | קרית אונו | K17 | 14,643 | map_to_2022_locality | 2620 | קריית אונו | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 13 | pending |  | יהוד-נווה אפרים | K17 | 13,087 | map_to_2022_locality | 9400 | יהוד | medium | K17 name is represented in the 2022 layer as Yehud. |
| 14 | pending | 961 | אבו רוקייק )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 12,975 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 15 | pending | 963 | אעצם )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 12,726 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 16 | pending |  | שגור | K17 | 11,069 | split_multi_target | 483 \| 490 \| 516 | בענה \| דייר אל-אסד \| מג'ד אל-כרום | medium | Shagor should be reviewed as a split into Bi'ne, Deir al-Asad, and Majd al-Kurum. |
| 17 | pending |  | קרית שמונה | K17 | 9,028 | map_to_2022_locality | 2800 | קריית שמונה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 18 | pending | 966 | אבו רובייעה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 8,831 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 19 | pending |  | קרית מלאכי | K17 | 7,900 | map_to_2022_locality | 1034 | קריית מלאכי | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 20 | pending | 968 | אבו קורינאת )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 7,880 | map_to_2022_locality | 1342 | אבו קורינאת (יישוב) | medium | Abu Qureinat tribe has a 2022 locality entry as Abu Qureinat (settlement). |
| 21 | pending |  | באקה-ג'ת | K17 | 7,880 | split_multi_target | 6000 \| 628 | באקה אל-גרביה \| ג'ת | high | Baqa-Jatt should be reviewed as split into Baqa al-Gharbiyye and Jatt. |
| 22 | pending |  | קרית טבעון | K17 | 7,873 | map_to_2022_locality | 2300 | קריית טבעון | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 23 | pending |  | עיר כרמל | K17 | 7,703 | split_multi_target | 494 \| 534 | דאלית אל-כרמל \| עספיא | high | Ir Carmel should be reviewed as split into Daliyat al-Karmel and Isfiya. |
| 24 | pending |  | צורן-קדימה | K17 | 6,878 | map_to_2022_locality | 195 | קדימה-צורן | high | K17 uses reversed name order for Kadima-Zoran. |
| 25 | pending |  | בנימינה-גבעת עדה | K17 | 4,955 | map_to_2022_locality | 9800 | בנימינה-גבעת עדה* | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 26 | pending | 1273 | מכבים-רעות | K16 | 4,949 | map_to_2022_locality | 1200 | מודיעין-מכבים-רעות* | medium | Maccabim-Reut is represented in 2022 as Modi'in-Maccabim-Re'ut. |
| 27 | pending | 1169 | הוואשלה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 4,656 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 28 | pending | 3826 | שער שומרון | K25 | 4,173 | no_2022_stat_area_assignment |  |  | medium | Sha'ar Shomron does not appear in the 2022 statistical-area locality list. |
| 29 | pending |  | קרית עקרון | K17 | 4,140 | map_to_2022_locality | 469 | קריית עקרון | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 30 | pending | 965 | אטרש )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 3,627 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 31 | pending | 967 | אבו ג'ווייעד (שבט) | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 3,480 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 32 | pending |  | אפרתה | K17 | 3,467 | map_to_2022_locality | 3650 | אפרת | high | K17 name variant maps to Efrat. |
| 33 | pending |  | פרדסיה | K17 | 2,920 | map_to_2022_locality | 171 | פרדסייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 34 | pending | 1170 | סייד )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,892 | map_to_2022_locality | 1359 | אל סייד | medium | Sayyid tribe has a 2022 locality entry as Al Sayyid. |
| 35 | pending | 964 | קודייראת א-צאנע(שבט) | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,805 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 36 | pending | 3637 | מעלה שומרון | K16 K18 K19 K20 K21 K22 K23 | 2,779 | map_to_2022_locality | 3640 | קרני שומרון | medium | Ma'ale Shomron appears to be represented in the 2022 layer under Karne Shomron. |
| 37 | pending | 956 | הוזייל )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,738 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 38 | pending |  | דבוריה | K17 | 2,681 | map_to_2022_locality | 489 | דבורייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 39 | pending |  | קרית ארבע | K17 | 2,649 | map_to_2022_locality | 3611 | קריית ארבע | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 40 | pending | 1234 | קבועה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,522 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 41 | pending | 1306 | צור יגאל | K16 | 2,446 | map_to_2022_locality | 1224 | כוכב יאיר | medium | Zur Yigal is represented in the 2022 layer under Kokhav Ya'ir. |
| 42 | pending | 1308 | צורן | K16 | 2,240 | map_to_2022_locality | 195 | קדימה-צורן | high | Zoran is represented in the 2022 layer under Kadima-Zoran. |
| 43 | pending |  | סביון | K17 | 2,034 | map_to_2022_locality | 587 | סביון* | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 44 | pending | 3400 | חברון | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,986 | no_2022_stat_area_assignment |  |  | medium | Hebron election locality is not represented as a 2022 statistical-area locality in this layer. |
| 45 | pending | 1049 | רמת אפעל | K16 | 1,895 | map_to_2022_locality | 8600 | רמת גן | medium | Ramat Efal is represented in the 2022 layer under Ramat Gan. |
| 46 | pending |  | רמת אפעל | K17 | 1,861 | map_to_2022_locality | 8600 | רמת גן | medium | Ramat Efal is represented in the 2022 layer under Ramat Gan. |
| 47 | pending | 1062 | נווה אפרים | K16 | 1,651 | map_to_2022_locality | 9400 | יהוד | medium | Neve Efrayim is represented in the 2022 layer under Yehud. |
| 48 | pending |  | בית אריה | K17 | 1,524 | map_to_2022_locality | 3652 | בית אריה-עופרים | high | Beit Arye is represented in 2022 as Beit Arye-Ofarim. |
| 49 | pending |  | קציר-חריש | K17 | 1,404 | split_multi_target | 1243 \| 1247 | קציר \| חריש | medium | Katzir-Harish should be reviewed as split into Katzir and Harish. |
| 50 | pending | 976 | ג'נאביב )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,399 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 51 | pending |  | כאוכב אבו אל-היג' | K17 | 1,381 | map_to_2022_locality | 505 | כאוכב אבו אל-היג'א | high | K17 name lacks final alef; target is Kaokab Abu al-Hija. |
| 52 | pending | 1415 | מחנה יפה | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,318 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 53 | pending |  | כעביה-טבאש-חג'אג' | K17 | 1,285 | map_to_2022_locality | 978 | כעביה-טבאש-חג'אג'רה | high | K17 name variant maps to Ka'abiyye-Tabbash-Hajajre. |
| 54 | pending | 50 | גבעת עדה | K16 | 1,279 | map_to_2022_locality | 9800 | בנימינה-גבעת עדה* | medium | Giv'at Ada is represented in the 2022 layer under Binyamina-Giv'at Ada. |
| 55 | pending | 1041 | נצאצרה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,221 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 56 | pending | 957 | עוקבי )בנו עוקבה( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,200 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 57 | pending | 1412 | מחנה תל נוף | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,169 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 58 | pending |  | עופרה | K17 | 1,125 | map_to_2022_locality | 3617 | עפרה | high | K17 spelling maps to Ofra. |
| 59 | pending | 972 | קוואעין )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 1,111 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 60 | pending |  | מסעודין אל-עזאזמה | K17 | 1,062 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 61 | pending |  | קרית יערים | K17 | 1,062 | map_to_2022_locality | 1137 | קריית יערים | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 62 | pending |  | טובא-זנגריה | K17 | 1,029 | map_to_2022_locality | 962 | טובא-זנגרייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 63 | pending |  | נורדיה | K17 | 1,026 | map_to_2022_locality | 447 | נורדייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 64 | pending | 5427 | נווה דקלים | K16 | 996 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 65 | pending | 960 | אסד )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 807 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 66 | pending |  | אבו רוקייק (שבט) | K17 | 801 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 67 | pending |  | אעצם (שבט) | K17 | 782 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 68 | pending | 1418 | מחנה טלי | K18 K19 K20 K21 K22 K23 K24 K25 | 761 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 69 | pending | 1416 | מחנה יוכבד | K18 K19 K20 K21 K22 K23 K24 K25 | 593 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 70 | pending | 1413 | מחנה יהודית | K20 K21 K22 K23 K24 K25 | 575 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 71 | pending |  | אבו קורינאת (שבט) | K17 | 554 | map_to_2022_locality | 1342 | אבו קורינאת (יישוב) | medium | Abu Qureinat tribe has a 2022 locality entry as Abu Qureinat (settlement). |
| 72 | pending | 970 | תראבין א-צאנע (שבט) | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 530 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 73 | pending |  | חלמיש | K17 | 525 | map_to_2022_locality | 3573 | נווה צוף | medium | Halamish is represented in the 2022 layer as Neve Tsuf. |
| 74 | pending | 1411 | מחנה הילה | K21 K22 K23 K24 K25 | 495 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 75 | pending |  | דליה | K17 | 494 | map_to_2022_locality | 300 | דלייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 76 | pending | 1414 | מחנה מרים | K19 K20 K21 K22 K23 K24 K25 | 476 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 77 | pending |  | ריחאניה | K17 | 469 | map_to_2022_locality | 540 | ריחאנייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 78 | pending |  | אבו רובייעה (שבט) | K17 | 460 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 79 | pending | 781 | גני יהודה | K16 | 453 | map_to_2022_locality | 587 | סביון* | medium | Ganne Yehuda is represented in the 2022 layer under Savyon. |
| 80 | pending | 2032 | נווה אפעל | K16 | 444 | map_to_2022_locality | 8600 | רמת גן | medium | Neve Efal is represented in the 2022 layer under Ramat Gan. |
| 81 | pending |  | סייד (שבט) | K17 | 444 | map_to_2022_locality | 1359 | אל סייד | medium | Sayyid tribe has a 2022 locality entry as Al Sayyid. |
| 82 | pending |  | שגב | K17 | 444 | map_to_2022_locality | 917 | עצמון שגב | medium | K17 Segev likely maps to Atzmon Segev; needs review. |
| 83 | pending |  | סתריה | K17 | 427 | map_to_2022_locality | 610 | סתרייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 84 | pending |  | קודייראת א-צאנע(ש | K17 | 425 | no_2022_stat_area_assignment |  |  | low | No deterministic target was found; leave unassigned until reviewed. |
| 85 | pending | 5426 | ניסנית | K16 | 406 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 86 | pending |  | פוריה - נווה עובד | K17 | 393 | map_to_2022_locality | 1105 | פורייה - נווה עובד | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 87 | pending |  | הוואשלה (שבט) | K17 | 382 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 88 | pending |  | עראמשה | K17 | 375 | map_to_2022_locality | 1246 | עראמשה* | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 89 | pending |  | נווה אפעל | K17 | 358 | map_to_2022_locality | 8600 | רמת גן | medium | Neve Efal is represented in the 2022 layer under Ramat Gan. |
| 90 | pending |  | מעין צבי | K17 | 350 | map_to_2022_locality | 290 | מעיין צבי | high | K17 spelling maps to Ma'yan Zevi. |
| 91 | pending | 3792 | עופרים | K16 | 350 | map_to_2022_locality | 3652 | בית אריה-עופרים | high | Ofarim is represented in 2022 as Beit Arye-Ofarim. |
| 92 | pending |  | כפר אז"ר | K17 | 325 | map_to_2022_locality | 8600 | רמת גן | medium | Kfar Azar is represented in the 2022 layer under Ramat Gan. |
| 93 | pending | 180 | כפר אז"ר | K16 | 317 | map_to_2022_locality | 8600 | רמת גן | medium | Kfar Azar is represented in the 2022 layer under Ramat Gan. |
| 94 | pending | 969 | עטאוונה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 313 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 95 | pending | 883 | רמת פנקס | K16 | 312 | map_to_2022_locality | 2400 | אור יהודה | medium | Ramat Pinkas is represented in the 2022 layer under Or Yehuda. |
| 96 | pending | 958 | אבו עבדון )שבט( | K16 K19 K20 K21 K22 K23 K24 K25 | 309 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 97 | pending |  | מעלה שומרון | K17 | 308 | no_2022_stat_area_assignment |  |  | low | No deterministic target was found; leave unassigned until reviewed. |
| 98 | pending |  | ביריה | K17 | 305 | map_to_2022_locality | 368 | בירייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 99 | pending |  | רמת פנקס | K17 | 295 | map_to_2022_locality | 2400 | אור יהודה | medium | Ramat Pinkas is represented in the 2022 layer under Or Yehuda. |
| 100 | pending |  | אשדות יעקב (איחו | K17 | 294 | map_to_2022_locality | 199 | אשדות יעקב (איחוד) | high | K17 truncated name maps to Ashdot Ya'aqov (Ihud). |
| 101 | pending |  | חמד | K17 | 285 | map_to_2022_locality | 801 | חמ"ד | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 102 | pending |  | פוריה עילית | K17 | 264 | map_to_2022_locality | 1313 | פורייה עילית | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 103 | pending |  | צפריה | K17 | 262 | map_to_2022_locality | 594 | צפרייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 104 | pending |  | הודיה | K17 | 260 | map_to_2022_locality | 726 | הודייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 105 | pending | 1417 | מחנה עדי | K19 K20 | 250 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 106 | pending |  | אשדות יעקב (מאוח | K17 | 238 | map_to_2022_locality | 188 | אשדות יעקב (מאוחד) | high | K17 truncated name maps to Ashdot Ya'aqov (Me'uhad). |
| 107 | pending |  | אילניה | K17 | 232 | map_to_2022_locality | 49 | אילנייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 108 | pending | 986 | ח'ואלד )שבט( | K16 K18 K19 K20 | 232 | map_to_2022_locality | 1321 | ח'ואלד | medium | Khawaled tribe has a 2022 locality entry as Khawaled. |
| 109 | pending |  | שושנת העמקים (רסק | K17 | 227 | map_to_2022_locality | 224 | שושנת העמקים | high | K17 truncated name maps to Shoshannat HaAmaqim. |
| 110 | pending |  | חברון | K17 | 225 | no_2022_stat_area_assignment |  |  | low | No deterministic target was found; leave unassigned until reviewed. |
| 111 | pending |  | אטרש (שבט) | K17 | 213 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 112 | pending |  | קרית ענבים | K17 | 206 | map_to_2022_locality | 78 | קריית ענבים | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 113 | pending | 5428 | אלי סיני | K16 | 194 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 114 | pending |  | כרמיה | K17 | 194 | map_to_2022_locality | 768 | כרמייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 115 | pending |  | מלכיה | K17 | 194 | map_to_2022_locality | 596 | מלכייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 116 | pending |  | מעין ברוך | K17 | 184 | map_to_2022_locality | 416 | מעיין ברוך | high | K17 spelling maps to Ma'yan Barukh. |
| 117 | pending | 5425 | בני עצמון | K16 | 181 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 118 | pending |  | קרית נטפים | K17 | 180 | map_to_2022_locality | 3746 | קריית נטפים | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 119 | pending |  | אל-רום | K17 | 158 | map_to_2022_locality | 4003 | אל -רום | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 120 | pending |  | ניצנה (קהילת חינו | K17 | 153 | map_to_2022_locality | 1195 | ניצנה (קהילת חינוך) | high | K17 truncated name maps to Nizzana (Qehilat Hinukh). |
| 121 | pending |  | קבועה (שבט) | K17 | 148 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 122 | pending | 5429 | גדיד | K16 | 146 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 123 | pending |  | קוואעין (שבט) | K17 | 137 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 124 | pending | 5431 | גן אור | K16 | 136 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 125 | pending | 5423 | קטיף | K16 | 123 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 126 | pending |  | תושיה | K17 | 123 | map_to_2022_locality | 1083 | תושייה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 127 | pending |  | פוריה - כפר עבודה | K17 | 122 | map_to_2022_locality | 1104 | פורייה - כפר עבודה | high | Backlog candidate came from deterministic normalization against the 2022 stat locality list. |
| 128 | pending | 5405 | כפר דרום | K16 | 119 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 129 | pending |  | מחנה יפה | K17 | 117 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 130 | pending |  | מחנה תל נוף | K17 | 113 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 131 | pending | 5408 | נצרים | K16 | 112 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 132 | pending |  | כפר רוזנואלד (זרע | K17 | 110 | map_to_2022_locality | 1130 | כפר רוזנואלד (זרעית) | high | K17 truncated name maps to Kfar Rozenwald (Zarit). |
| 133 | pending |  | עוקבי (בנו עוקבה) | K17 | 110 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 134 | pending |  | הוזייל (שבט) | K17 | 106 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 135 | pending |  | אבו ג'ווייעד (שבט | K17 | 103 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 136 | pending |  | אסד (שבט) | K17 | 102 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 137 | pending | 5432 | בדולח | K16 | 90 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 138 | pending | 3642 | חומש | K16 | 79 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 139 | pending |  | מחנה טלי | K17 | 75 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
| 140 | pending |  | תראבין א-צאנע (שב | K17 | 74 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 141 | pending |  | עטאוונה (שבט) | K17 | 72 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 142 | pending | 989 | סואעד )כמאנה( )שב | K16 | 71 | map_to_2022_locality | 1331 | כמאנה | low | Sawa'id/Kamane tribe row may correspond to Kamane; needs review. |
| 143 | pending | 3758 | גנים | K16 | 67 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 144 | pending | 5407 | מורג | K16 | 63 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 145 | pending |  | נעמי | K17 | 56 | map_to_2022_locality | 3713 | נעמ"ה | medium | Naomi appears to correspond to Na'ama in the 2022 layer. |
| 146 | pending |  | ח'ואלד (שבט) | K17 | 55 | map_to_2022_locality | 1321 | ח'ואלד | medium | Khawaled tribe has a 2022 locality entry as Khawaled. |
| 147 | pending | 3729 | כדים | K16 | 52 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 148 | pending | 5433 | רפיח ים | K16 | 50 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 149 | pending |  | ג'נאביב (שבט) | K17 | 45 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 150 | pending | 5436 | פאת שדה | K16 | 44 | no_2022_stat_area_assignment |  |  | high | Source locality is a retired/evacuated locality and should not be reassigned to a different 2022 locality by name. |
| 151 | pending |  | סואעד (כמאנה) (שב | K17 | 40 | map_to_2022_locality | 1331 | כמאנה | low | Sawa'id/Kamane row may correspond to Kamane; needs review. |
| 152 | pending |  | נירן | K17 | 36 | map_to_2022_locality | 3620 | נערן | low | Niran may correspond to Na'aran; needs review. |
| 153 | pending |  | סוואעד חמיירה | K17 | 33 | map_to_2022_locality | 942 | סואעד (חמרייה)* | medium | Sawa'id Hamriyye appears in the 2022 layer as Sawa'id (Hamriyye). |
| 154 | pending |  | נצאצרה (שבט) | K17 | 29 | no_2022_stat_area_assignment |  |  | medium | Tribal/dispersed election locality has no clear 2022 statistical-area locality target in this layer. |
| 155 | pending | 1404 | חצרות יסף | K16 | 27 | no_2022_stat_area_assignment |  |  | medium | Camp/base locality row is not represented as a normal 2022 statistical-area locality. |
