# Locality Crosswalk Backlog

Last updated: 2026-07-05

## Purpose

This file defines the next data-cleaning backlog: every unique locality identity from K16-K25 that did not automatically match the 2022 statistical-area locality list.

The source for this backlog is the FileGDB-based locality audit, not the old partial GeoJSON.

Tracked CSV:

- `docs/LOCALITY_CROSSWALK_BACKLOG.csv`

Review table:

- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.md`
- `docs/LOCALITY_CROSSWALK_APPROVAL_TABLE.csv`

Resolution plan:

- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.md`
- `docs/LOCALITY_CROSSWALK_RESOLUTION_PLAN.csv`

Reviewed assignment coverage:

- `docs/STATISTICAL_AREA_ASSIGNMENT_COVERAGE.md`
- `docs/LOCALITY_SINGLE_STAT_ASSIGNMENTS.csv`

## Summary

- Unique unmatched locality identities: 155
- Total affected actual voters across K16-K25 rows: 702,421

| Initial bucket | Localities | Affected actual voters |
| --- | --- | --- |
| name_only_probable_spelling_or_spacing_match | 39 | 453,981 |
| code_absent_no_name_candidate | 61 | 132,716 |
| needs_research | 55 | 115,724 |

## Initial Buckets

- `name_only_probable_spelling_or_spacing_match`: usually K17 rows where the election result has no locality code and exact names differ from the 2022 layer by spelling, hyphen spacing, or yod spelling.
- `code_absent_name_candidate`: the election locality code is absent from the 2022 layer, but the name has a possible target under another 2022 code. These are likely code changes, merges, or aliases.
- `code_absent_no_name_candidate`: the election locality code is absent and no simple name candidate was found. These need historical/locality-status research.
- `needs_research`: no code and no simple name candidate.

## Highest-Impact Unreviewed Items

| Source code | Source name | Elections | Affected voters | Initial bucket | Candidate target names |
| --- | --- | --- | --- | --- | --- |
|  | תל אביב - יפו | K17 | 214,688 | name_only_probable_spelling_or_spacing_match | תל אביב -יפו |
|  | הרצליה | K17 | 47,119 | name_only_probable_spelling_or_spacing_match | הרצלייה |
| 939 | מסעודין אל-עזאזמה | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 26,595 | code_absent_no_name_candidate |  |
|  | מודיעין-מכבים-רעו | K17 | 25,732 | needs_research |  |
|  | נהריה | K17 | 23,604 | name_only_probable_spelling_or_spacing_match | נהרייה |
|  | קרית אתא | K17 | 23,434 | name_only_probable_spelling_or_spacing_match | קריית אתא |
|  | קרית מוצקין | K17 | 20,772 | name_only_probable_spelling_or_spacing_match | קריית מוצקין |
|  | נצרת עילית | K17 | 20,718 | needs_research |  |
|  | קרית גת | K17 | 19,866 | name_only_probable_spelling_or_spacing_match | קריית גת |
|  | קרית ביאליק | K17 | 19,537 | name_only_probable_spelling_or_spacing_match | קריית ביאליק |
|  | קרית ים | K17 | 18,078 | name_only_probable_spelling_or_spacing_match | קריית ים |
|  | קרית אונו | K17 | 14,643 | name_only_probable_spelling_or_spacing_match | קריית אונו |
|  | יהוד-נווה אפרים | K17 | 13,087 | needs_research |  |
| 961 | אבו רוקייק )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 12,975 | code_absent_no_name_candidate |  |
| 963 | אעצם )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 12,726 | code_absent_no_name_candidate |  |
|  | שגור | K17 | 11,069 | needs_research |  |
|  | קרית שמונה | K17 | 9,028 | name_only_probable_spelling_or_spacing_match | קריית שמונה |
| 966 | אבו רובייעה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 8,831 | code_absent_no_name_candidate |  |
|  | קרית מלאכי | K17 | 7,900 | name_only_probable_spelling_or_spacing_match | קריית מלאכי |
| 968 | אבו קורינאת )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 7,880 | code_absent_no_name_candidate |  |
|  | באקה-ג'ת | K17 | 7,880 | needs_research |  |
|  | קרית טבעון | K17 | 7,873 | name_only_probable_spelling_or_spacing_match | קריית טבעון |
|  | עיר כרמל | K17 | 7,703 | needs_research |  |
|  | צורן-קדימה | K17 | 6,878 | needs_research |  |
|  | בנימינה-גבעת עדה | K17 | 4,955 | name_only_probable_spelling_or_spacing_match | בנימינה-גבעת עדה* |
| 1273 | מכבים-רעות | K16 | 4,949 | code_absent_no_name_candidate |  |
| 1169 | הוואשלה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 4,656 | code_absent_no_name_candidate |  |
| 3826 | שער שומרון | K25 | 4,173 | code_absent_no_name_candidate |  |
|  | קרית עקרון | K17 | 4,140 | name_only_probable_spelling_or_spacing_match | קריית עקרון |
| 965 | אטרש )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 3,627 | code_absent_no_name_candidate |  |
| 967 | אבו ג'ווייעד (שבט) | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 3,480 | code_absent_no_name_candidate |  |
|  | אפרתה | K17 | 3,467 | needs_research |  |
|  | פרדסיה | K17 | 2,920 | name_only_probable_spelling_or_spacing_match | פרדסייה |
| 1170 | סייד )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,892 | code_absent_no_name_candidate |  |
| 964 | קודייראת א-צאנע(שבט) | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,805 | code_absent_no_name_candidate |  |
| 3637 | מעלה שומרון | K16 K18 K19 K20 K21 K22 K23 | 2,779 | code_absent_no_name_candidate |  |
| 956 | הוזייל )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,738 | code_absent_no_name_candidate |  |
|  | דבוריה | K17 | 2,681 | name_only_probable_spelling_or_spacing_match | דבורייה |
|  | קרית ארבע | K17 | 2,649 | name_only_probable_spelling_or_spacing_match | קריית ארבע |
| 1234 | קבועה )שבט( | K16 K18 K19 K20 K21 K22 K23 K24 K25 | 2,522 | code_absent_no_name_candidate |  |

## Review Rules

Each row needs one reviewed outcome before the statistical-area pipeline treats it as resolved:

- exact target 2022 locality code and name,
- reviewed alias/name-change rule,
- reviewed merge rule,
- reviewed split rule,
- retired/no-current-2022-locality rule,
- unresolved with reason.

Do not silently apply the candidates in the CSV. They are only hints for manual review.
