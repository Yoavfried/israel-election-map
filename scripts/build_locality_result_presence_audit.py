#!/usr/bin/env python3
"""Audit standalone locality-result presence across K17 through K25."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "data" / "processed" / "geographies" / "localities_2022.metadata.csv"
RESULTS_ROOT = ROOT / "data" / "processed" / "public" / "locality_results"
OVERRIDES_PATH = ROOT / "data" / "manual" / "locality_display_overrides.csv"
REVIEWS_PATH = ROOT / "data" / "manual" / "locality_result_presence_reviews.csv"
JOINED_COMPOSITES_PATH = (
    ROOT / "data" / "manual" / "joined_locality_composites.csv"
)
POLLING_PLACES_PATH = (
    ROOT / "data" / "processed" / "addresses" / "polling_place_addresses.csv"
)
BALLOT_ROWS_PATH = ROOT / "data" / "processed" / "normalized" / "ballot_rows.csv"
AUDIT_CSV_PATH = ROOT / "docs" / "LOCALITY_RESULT_PRESENCE_AUDIT.csv"
AUDIT_MD_PATH = ROOT / "docs" / "LOCALITY_RESULT_PRESENCE_AUDIT.md"

ELECTIONS = tuple(f"K{number}" for number in range(17, 26))
STRUCTURAL_CODE_RANGES = (
    (1700, 1799, "special-purpose facilities"),
    (5500, 5599, "regional-council footprints"),
    (9900, 9999, "no-jurisdiction/background footprints"),
)
AUDIT_FIELDS = (
    "locality_id",
    "locality_code",
    "locality_name_he",
    "locality_name_en",
    "result_status",
    "result_elections",
    "missing_elections",
    "west_bank_code_range",
    "function_codes",
    "reviewed_display_rule",
    "review_note",
    "explanation_review_status",
    "explanation_category",
    "cbs_2022_name",
    "cbs_2022_form_code",
    "cbs_2022_form",
    "cbs_2022_population",
    "evidence_election",
    "evidence_eligible_voters",
    "joined_host_locality_code",
    "joined_host_locality_name",
    "joined_host_kalpi",
    "explanation_note",
)
EXPLANATION_LABELS = {
    "joined_exact": "K19 joined register; exact eligible-voter arithmetic",
    "joined_source_location": "attached row is explicitly located at the host",
    "joined_under_100_inferred": "under-100 register; host strongly inferred",
    "no_ordinary_voter_list": "no ordinary voter-list row in available K17-K25 sources",
}
REVIEW_STATUSES = {"confirmed", "strong"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm_name(value: object) -> str:
    return re.sub(r"[^\w\u0590-\u05ff]+", "", str(value or ""), flags=re.UNICODE)


def parse_explanation_reviews(
    rows: list[dict[str, str]],
    metadata_by_id: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    reviews: dict[str, dict[str, str]] = {}
    for row in rows:
        locality_id = row.get("locality_id", "").strip()
        status = row.get("review_status", "").strip()
        category = row.get("explanation_category", "").strip()
        if locality_id not in metadata_by_id:
            raise ValueError(f"Unknown locality explanation review: {locality_id or '(blank ID)'}")
        if locality_id in reviews:
            raise ValueError(f"Duplicate locality explanation review: {locality_id}")
        if status not in REVIEW_STATUSES:
            raise ValueError(f"{locality_id} has invalid explanation review status: {status}")
        if category not in EXPLANATION_LABELS:
            raise ValueError(f"{locality_id} has invalid explanation category: {category}")
        reviews[locality_id] = {key: (value or "").strip() for key, value in row.items()}
    return reviews


def validate_explanation_evidence(
    reviews: dict[str, dict[str, str]],
    metadata_by_id: dict[str, dict[str, str]],
) -> None:
    polling_rows = read_csv(POLLING_PLACES_PATH)
    ballot_rows = read_csv(BALLOT_ROWS_PATH)
    polling_by_code: dict[str, list[dict[str, str]]] = defaultdict(list)
    polling_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    ballot_by_key: dict[tuple[str, str, str], dict[str, str]] = {}

    for row in polling_rows:
        code = row.get("source_locality_code", "").strip()
        if code:
            polling_by_code[code].append(row)
            polling_by_key[
                (row["election"], code, row.get("source_kalpi", "").strip())
            ] = row
    for row in ballot_rows:
        code = row.get("source_locality_code", "").strip()
        if code:
            ballot_by_key[
                (row["election"], code, row.get("source_kalpi", "").strip())
            ] = row

    for locality_id, review in reviews.items():
        code = metadata_by_id[locality_id]["locality_code"].strip()
        category = review["explanation_category"]
        if category == "no_ordinary_voter_list":
            if polling_by_code.get(code):
                raise ValueError(f"{locality_id} is reviewed as having no polling-list row")
            continue

        host_code = review["joined_host_locality_code"]
        host_kalpi = review["joined_host_kalpi"]
        if not host_code or not host_kalpi:
            raise ValueError(f"{locality_id} is missing a joined host")

        if category == "joined_source_location":
            evidence_row = next(
                (
                    row
                    for row in polling_by_code.get(code, [])
                    if row["election"] == "K20"
                ),
                None,
            )
            if not evidence_row:
                raise ValueError(f"{locality_id} is missing its K20 attached polling row")
            host_name = review["joined_host_locality_name"]
            if norm_name(host_name) not in norm_name(evidence_row.get("address", "")):
                raise ValueError(f"{locality_id} K20 address does not name its reviewed host")
            continue

        election = review["evidence_election"]
        target_rows = [
            row
            for row in polling_by_code.get(code, [])
            if row["election"] == election
        ]
        if len(target_rows) != 1:
            raise ValueError(
                f"{locality_id} expected one {election} polling row; found {len(target_rows)}"
            )
        target_eligible = int(review["evidence_eligible_voters"])
        if int(target_rows[0]["source_eligible_voters"]) != target_eligible:
            raise ValueError(f"{locality_id} eligible-voter evidence changed")

        host_key = (election, host_code, host_kalpi)
        host_plan = polling_by_key.get(host_key)
        host_result = ballot_by_key.get(host_key)
        if not host_plan or not host_result:
            raise ValueError(f"{locality_id} reviewed host row is missing for {election}")
        host_delta = int(host_result["eligible_voters"]) - int(
            host_plan["source_eligible_voters"]
        )
        if category == "joined_exact":
            host_name = review["joined_host_locality_name"]
            normalized_host_name = norm_name(
                host_plan.get("source_locality_name", "") or host_name
            )
            if normalized_host_name not in norm_name(target_rows[0].get("address", "")):
                raise ValueError(f"{locality_id} polling address does not name its host")
            other_attached_eligible = [
                int(row["source_eligible_voters"])
                for row in polling_rows
                if row["election"] == election
                and row.get("source_locality_code", "").strip() != host_code
                and normalized_host_name in norm_name(row.get("address", ""))
                and row is not target_rows[0]
            ]
            remaining_delta = host_delta - target_eligible
            possible_other_totals = {0}
            for eligible in other_attached_eligible:
                possible_other_totals |= {
                    subtotal + eligible for subtotal in possible_other_totals
                }
            if remaining_delta not in possible_other_totals:
                raise ValueError(
                    f"{locality_id} ({target_eligible}) cannot participate in an exact "
                    f"source-register sum for the {host_name} host delta ({host_delta})"
                )
        if category == "joined_under_100_inferred":
            if target_eligible >= 100 or abs(host_delta - target_eligible) > 15:
                raise ValueError(f"{locality_id} no longer fits its inferred under-100 host")


def normalize_code(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        return ""


def derive_addressed_join_groups(
    election: str,
    polling_rows: list[dict[str, str]],
    ballot_rows: list[dict[str, str]],
    metadata_codes: set[str],
) -> tuple[dict[str, list[str]], dict[str, list[dict[str, str]]]]:
    election_results = [row for row in ballot_rows if row["election"] == election]
    result_codes = {
        normalize_code(row.get("source_locality_code", ""))
        for row in election_results
        if normalize_code(row.get("source_locality_code", ""))
    }
    result_names: dict[str, dict[str, str]] = defaultdict(dict)
    for row in election_results:
        code = normalize_code(row.get("source_locality_code", ""))
        if code:
            result_names[norm_name(row.get("source_locality_name", ""))][code] = row.get(
                "source_locality_name", ""
            )

    all_attached_by_host: dict[str, list[dict[str, str]]] = defaultdict(list)
    geometry_codes_by_host: dict[str, set[str]] = defaultdict(set)
    for row in polling_rows:
        code = normalize_code(row.get("source_locality_code", ""))
        if row["election"] != election or not code or code in result_codes:
            continue
        address_locality = row.get("address", "").split(",", 1)[0].strip()
        normalized_address_locality = norm_name(address_locality)
        candidates = dict(result_names.get(normalized_address_locality, {}))
        if not candidates:
            candidates = {
                candidate_code: candidate_name
                for candidate_name_key, matches in result_names.items()
                if candidate_name_key.startswith(normalized_address_locality)
                or normalized_address_locality.startswith(candidate_name_key)
                for candidate_code, candidate_name in matches.items()
            }
        candidates = {
            candidate_code: candidate_name
            for candidate_code, candidate_name in candidates.items()
            if candidate_code and candidate_code != code
        }
        if len(candidates) != 1:
            continue
        host_code = next(iter(candidates))
        if host_code not in metadata_codes:
            continue
        all_attached_by_host[host_code].append(row)
        if code in metadata_codes:
            geometry_codes_by_host[host_code].add(code)

    groups = {
        host_code: [host_code, *sorted(attached_codes, key=int)]
        for host_code, attached_codes in geometry_codes_by_host.items()
        if attached_codes
    }
    return groups, all_attached_by_host


def validate_joined_composites(
    rows: list[dict[str, str]],
    metadata_by_id: dict[str, dict[str, str]],
) -> None:
    polling_rows = read_csv(POLLING_PLACES_PATH)
    ballot_rows = read_csv(BALLOT_ROWS_PATH)
    metadata_codes = {
        normalize_code(row["locality_code"]) for row in metadata_by_id.values()
    }
    required = {
        "joined_composite_id",
        "election",
        "host_locality_code",
        "host_kalpi",
        "component_locality_codes",
        "evidence_status",
        "evidence_method",
        "note",
    }
    if not rows or required - set(rows[0]):
        raise ValueError("Joined-locality composite table is empty or has missing columns")

    seen_ids: set[str] = set()
    seen_components: set[tuple[str, str]] = set()
    rows_by_key: dict[tuple[str, str], dict[str, str]] = {}
    ballot_codes_by_election: dict[str, set[str]] = defaultdict(set)
    ballot_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    polling_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in ballot_rows:
        code = normalize_code(row.get("source_locality_code", ""))
        if code:
            ballot_codes_by_election[row["election"]].add(code)
            ballot_by_key[(row["election"], code, row["source_kalpi"])] = row
    for row in polling_rows:
        code = normalize_code(row.get("source_locality_code", ""))
        if code:
            polling_by_key[(row["election"], code, row["source_kalpi"])] = row

    for row in rows:
        composite_id = row["joined_composite_id"].strip()
        election = row["election"].strip()
        host_code = normalize_code(row["host_locality_code"])
        component_codes = [
            normalize_code(value)
            for value in row["component_locality_codes"].split("|")
            if normalize_code(value)
        ]
        if not composite_id or composite_id in seen_ids:
            raise ValueError(f"Missing or duplicate joined composite ID: {composite_id}")
        seen_ids.add(composite_id)
        if (
            election not in {"K19", "K20", "K25"}
            or len(component_codes) < 2
            or component_codes[0] != host_code
            or len(component_codes) != len(set(component_codes))
        ):
            raise ValueError(f"Invalid joined composite row: {composite_id}")
        if set(component_codes) - metadata_codes:
            raise ValueError(f"{composite_id} contains a non-geometry locality code")
        if host_code not in ballot_codes_by_election[election]:
            raise ValueError(f"{composite_id} host has no published result")
        for attached_code in component_codes[1:]:
            if attached_code in ballot_codes_by_election[election]:
                raise ValueError(
                    f"{composite_id} would hide standalone result {attached_code}"
                )
            component_key = (election, attached_code)
            if component_key in seen_components:
                raise ValueError(
                    f"{election} locality {attached_code} belongs to multiple joins"
                )
            seen_components.add(component_key)
        key = (election, host_code)
        if key in rows_by_key:
            raise ValueError(f"Duplicate joined host: {election} / {host_code}")
        rows_by_key[key] = row

    for election, expected_method in (
        ("K19", "exact_eligible_arithmetic"),
        ("K20", "explicit_source_location"),
    ):
        expected_groups, all_attached_by_host = derive_addressed_join_groups(
            election,
            polling_rows,
            ballot_rows,
            metadata_codes,
        )
        actual_groups = {
            host_code: [
                normalize_code(value)
                for value in row["component_locality_codes"].split("|")
            ]
            for (row_election, host_code), row in rows_by_key.items()
            if row_election == election
        }
        if actual_groups != expected_groups:
            missing = sorted(set(expected_groups) - set(actual_groups), key=int)
            extra = sorted(set(actual_groups) - set(expected_groups), key=int)
            changed = sorted(
                host_code
                for host_code in set(expected_groups) & set(actual_groups)
                if expected_groups[host_code] != actual_groups[host_code]
            )
            raise ValueError(
                f"{election} joined composites changed; missing={missing}, "
                f"extra={extra}, changed={changed}"
            )
        for host_code, attached_rows in all_attached_by_host.items():
            if host_code not in expected_groups:
                continue
            row = rows_by_key[(election, host_code)]
            if row["evidence_method"] != expected_method:
                raise ValueError(f"{row['joined_composite_id']} has the wrong evidence method")
            if election == "K19":
                host_plan_total = sum(
                    int(item["source_eligible_voters"])
                    for item in polling_rows
                    if item["election"] == election
                    and normalize_code(item.get("source_locality_code", "")) == host_code
                )
                host_result_total = sum(
                    int(item["eligible_voters"])
                    for item in ballot_rows
                    if item["election"] == election
                    and normalize_code(item.get("source_locality_code", "")) == host_code
                )
                attached_total = sum(
                    int(item["source_eligible_voters"]) for item in attached_rows
                )
                if host_result_total - host_plan_total != attached_total:
                    raise ValueError(
                        f"{row['joined_composite_id']} no longer reconciles exactly"
                    )

    for (election, host_code), row in rows_by_key.items():
        if election != "K25":
            continue
        if row["evidence_method"] != "under_100_host_delta":
            raise ValueError(f"{row['joined_composite_id']} has the wrong K25 evidence method")
        host_kalpi = row["host_kalpi"].strip()
        host_key = (election, host_code, host_kalpi)
        host_plan = polling_by_key.get(host_key)
        host_result = ballot_by_key.get(host_key)
        if not host_plan or not host_result:
            raise ValueError(f"{row['joined_composite_id']} is missing its K25 host station")
        attached_total = 0
        for attached_code in row["component_locality_codes"].split("|")[1:]:
            matches = [
                item
                for item in polling_rows
                if item["election"] == election
                and normalize_code(item.get("source_locality_code", "")) == attached_code
            ]
            if len(matches) != 1 or int(matches[0]["source_eligible_voters"]) >= 100:
                raise ValueError(
                    f"{row['joined_composite_id']} has invalid K25 attached-register evidence"
                )
            attached_total += int(matches[0]["source_eligible_voters"])
        host_delta = int(host_result["eligible_voters"]) - int(
            host_plan["source_eligible_voters"]
        )
        if abs(host_delta - attached_total) > 15:
            raise ValueError(f"{row['joined_composite_id']} no longer fits its K25 host")


def structural_class(code: int) -> str:
    for start, end, label in STRUCTURAL_CODE_RANGES:
        if start <= code <= end:
            return label
    return ""


def parse_override_rows(
    rows: list[dict[str, str]],
    metadata_by_id: dict[str, dict[str, str]],
    result_ids_by_election: dict[str, set[str]],
) -> dict[str, list[dict[str, object]]]:
    configured_elections = set(ELECTIONS)
    overrides_by_id: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()

    for row in rows:
        locality_id = row.get("locality_id", "").strip()
        election_ids = tuple(
            value.strip() for value in row.get("elections", "").split("|") if value.strip()
        )
        visibility = row.get("visibility", "").strip() or "default"

        if locality_id not in metadata_by_id:
            raise ValueError(f"Unknown locality display override: {locality_id or '(blank ID)'}")
        if not election_ids or not set(election_ids) <= configured_elections:
            raise ValueError(f"{locality_id} has invalid display-override elections")
        if visibility not in {"default", "hidden"}:
            raise ValueError(f"{locality_id} has invalid visibility: {visibility}")

        for election in election_ids:
            key = (election, locality_id)
            if key in seen:
                raise ValueError(f"Duplicate locality display override: {election}.{locality_id}")
            seen.add(key)
            if visibility == "hidden" and locality_id in result_ids_by_election[election]:
                raise ValueError(f"{election} hides result-bearing locality {locality_id}")

        overrides_by_id[locality_id].append(
            {
                "elections": election_ids,
                "visibility": visibility,
                "name_he": row.get("name_he", "").strip(),
                "name_en": row.get("name_en", "").strip(),
                "note": row.get("note", "").strip(),
            }
        )

    return overrides_by_id


def format_elections(elections: tuple[str, ...] | list[str]) -> str:
    numbers = [int(election.removeprefix("K")) for election in elections]
    if not numbers:
        return "none"

    groups: list[tuple[int, int]] = []
    start = previous = numbers[0]
    for number in numbers[1:]:
        if number == previous + 1:
            previous = number
            continue
        groups.append((start, previous))
        start = previous = number
    groups.append((start, previous))
    return ", ".join(
        f"K{start}" if start == end else f"K{start}-K{end}" for start, end in groups
    )


def summarize_overrides(overrides: list[dict[str, object]]) -> tuple[str, str]:
    rules: list[str] = []
    notes: list[str] = []
    for override in overrides:
        election_label = format_elections(override["elections"])
        actions: list[str] = []
        if override["visibility"] == "hidden":
            actions.append("hidden")
        if override["name_he"]:
            actions.append(f"Hebrew name={override['name_he']}")
        if override["name_en"]:
            actions.append(f"English name={override['name_en']}")
        if actions:
            rules.append(f"{election_label}: {', '.join(actions)}")
        if override["note"] and override["note"] not in notes:
            notes.append(str(override["note"]))
    return "; ".join(rules), " ".join(notes)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_explanation_evidence(row: dict[str, str]) -> str:
    category = row["explanation_category"]
    election = row["evidence_election"]
    eligible = row["evidence_eligible_voters"]
    if category == "no_ordinary_voter_list":
        return f"{election}: no ordinary polling-list row"
    if category == "joined_source_location":
        return f"{election}: source row names host"
    return f"{election}: {eligible} eligible"


def markdown_table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    output.extend(
        "| " + " | ".join(markdown_cell(value) for value in row) + " |" for row in rows
    )
    return output


def write_markdown(
    path: Path,
    audit_rows: list[dict[str, str]],
    joined_rows: list[dict[str, str]],
    status_counts: Counter[str],
    structural_counts: Counter[str],
    metadata_count: int,
) -> None:
    west_bank_rows = [row for row in audit_rows if row["west_bank_code_range"] == "yes"]
    no_result_rows = [row for row in audit_rows if row["result_status"] == "none"]
    other_partial_rows = [
        row
        for row in audit_rows
        if row["result_status"] == "partial" and row["west_bank_code_range"] == "no"
    ]
    explanation_counts = Counter(row["explanation_category"] for row in no_result_rows)
    explanation_status_counts = Counter(
        row["explanation_review_status"] for row in no_result_rows
    )
    joined_counts = Counter(row["election"] for row in joined_rows)
    joined_component_counts = Counter(
        {
            election: sum(
                max(
                    0,
                    len(
                        [
                            value
                            for value in row["component_locality_codes"].split("|")
                            if value
                        ]
                    )
                    - 1,
                )
                for row in joined_rows
                if row["election"] == election
            )
            for election in joined_counts
        }
    )
    audit_by_code = {row["locality_code"]: row for row in audit_rows}
    joined_attached_codes = {
        component_code
        for row in joined_rows
        for component_code in row["component_locality_codes"].split("|")[1:]
        if component_code
    }
    joined_elections_by_code: dict[str, set[str]] = defaultdict(set)
    for row in joined_rows:
        for component_code in row["component_locality_codes"].split("|")[1:]:
            if component_code:
                joined_elections_by_code[component_code].add(row["election"])
    joined_attached_status_counts = Counter(
        audit_by_code[code]["result_status"]
        for code in joined_attached_codes
        if code in audit_by_code
    )
    joined_none_count = joined_attached_status_counts["none"]
    joined_partial_count = joined_attached_status_counts["partial"]
    partial_without_join_count = status_counts["partial"] - joined_partial_count
    partial_with_unresolved_election_count = sum(
        any(
            election not in joined_elections_by_code.get(row["locality_code"], set())
            for election in row["missing_elections"].split("|")
            if election
        )
        for row in audit_rows
        if row["result_status"] == "partial"
    )

    lines = [
        "# Locality Result-Presence Audit",
        "",
        "Generated by `python scripts/build_locality_result_presence_audit.py`.",
        "",
        "## Scope and Method",
        "",
        "This audit asks whether each 2022 CBS display feature has its own standalone row in each K17-K25 locality-result file. It does not test whether all published election rows are mapped; locality-mode row coverage is independently 100%.",
        "",
        "The 1700-1799 special-purpose facilities, 5500-5599 regional-council footprints, and 9900-9999 no-jurisdiction/background footprints are structural display geometry, not candidate election localities, and are excluded from the exception inventory.",
        "",
        "The structural exclusion was checked against the official 2022 CBS locality workbook. All 56 special-purpose records have a blank 2022 population; the other 104 features are regional-council or no-jurisdiction footprints rather than locality records. No additional never-result polygon with an expected locality electorate sits outside the 36-row review set.",
        "",
        "## Review Status",
        "",
        "The 36 features with no standalone K17-K25 result now have evidence-level explanations. The 80 partial-presence features still require historical and election-specific review. A `none` value in the reviewed-display column means that no explicit visibility decision has been recorded; it does not mean the explanation audit is missing.",
        "",
        "A joined polling area cannot be split back into locality-specific party totals. The published host row contains one secret-ballot aggregate for the host and every attached register, so moving the whole result to an attached locality would be incorrect.",
        "",
        "For `כפר עבודה` and `צופייה`, youth-institution context makes the absence of an adult locality register unsurprising. `ידידה` is an adult residential institution: its absence from every available ordinary polling list is confirmed, but whether its residents remain registered at other addresses or are handled elsewhere is not established by the election sources.",
        "",
        "## Election-Specific Joined Polygons",
        "",
        "The locality map substitutes reviewed host-plus-attached polygon unions only in elections supported by the source evidence. The canonical locality-result CSV remains under the published host locality; the web bundle aliases that one result to the combined display feature without copying or splitting votes. The visible title remains the published host locality, while an info tooltip lists every attached 2022 polygon represented by the union. Historical source registers without a 2022 polygon cannot add geometry and remain documented only in the source evidence.",
        "",
    ]
    lines.extend(
        markdown_table(
            ("Election", "Combined polygons", "Attached 2022 polygons", "Evidence"),
            [
                (
                    "K19",
                    joined_counts["K19"],
                    joined_component_counts["K19"],
                    "exact host-level eligible-voter arithmetic",
                ),
                (
                    "K20",
                    joined_counts["K20"],
                    joined_component_counts["K20"],
                    "official polling rows explicitly name the host",
                ),
                (
                    "K25",
                    joined_counts["K25"],
                    joined_component_counts["K25"],
                    "reviewed under-100 host-delta inference",
                ),
            ],
        )
    )
    lines.extend(
        [
            "",
            f"Across elections, {joined_none_count} of the {status_counts['none']} never-present meaningful polygons participate in at least one supported host union; the other {status_counts['none'] - joined_none_count} are the institution/place cases with no ordinary polling-list row. The unions also include {joined_partial_count} of the {status_counts['partial']} partial-presence polygons where the source identifies their host.",
            "",
            f"K17-K18 and K21-K24 currently have no joined-polygon display rules because the available source rows do not establish the host relationship. {partial_without_join_count} partial-presence polygons have no joined election yet, and all {partial_with_unresolved_election_count} partial histories still contain at least one missing election without a supported host rule.",
            "",
            "## Counts",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ("Feature class", "Count"),
            [
                ("All 2022 metadata features", metadata_count),
                ("Structural display features excluded", sum(structural_counts.values())),
                ("Meaningful features with results in all 9 elections", status_counts["all"]),
                ("Meaningful features with results in some elections", status_counts["partial"]),
                ("Meaningful features with no standalone result", status_counts["none"]),
            ],
        )
    )

    lines.extend(["", "No-standalone-result explanation breakdown:", ""])
    lines.extend(
        markdown_table(
            ("Explanation", "Count"),
            [
                (EXPLANATION_LABELS[category], explanation_counts[category])
                for category in EXPLANATION_LABELS
            ],
        )
    )
    lines.extend(["", "Review confidence:", ""])
    lines.extend(
        markdown_table(
            ("Status", "Count"),
            [
                ("confirmed", explanation_status_counts["confirmed"]),
                ("strong inference", explanation_status_counts["strong"]),
            ],
        )
    )
    lines.extend(["", "Structural breakdown:", ""])
    lines.extend(
        markdown_table(
            ("Structural class", "Count"),
            [(label, structural_counts[label]) for _, _, label in STRUCTURAL_CODE_RANGES],
        )
    )

    lines.extend(
        [
            "",
            "## West Bank Review Set",
            "",
            "These are the 2022 localities in the West Bank code range that lack a standalone result in at least one election. `אבנת` and `מבואות יריחו` are already reviewed as hidden for K17-K25; the other missing-election cases remain visible until explicitly reviewed.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ("Code", "2022 name", "Results present", "Missing", "Reviewed display rule"),
            [
                (
                    row["locality_code"],
                    row["locality_name_he"],
                    format_elections(row["result_elections"].split("|") if row["result_elections"] else []),
                    format_elections(row["missing_elections"].split("|") if row["missing_elections"] else []),
                    row["reviewed_display_rule"] or "none",
                )
                for row in west_bank_rows
            ],
        )
    )

    lines.extend(
        [
            "",
            "## No Standalone Result in K17-K25",
            "",
            "The CBS form and population values are a reviewed 2022 snapshot from the official locality workbook. `place` is a CBS location that is not counted as an independent locality population. Exact joins are validated against the archived K19 polling list and published K19 eligible-voter totals; strong inferences use an explicit attached-row address or an under-100 K25 register plus the nearby host delta.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            (
                "Code",
                "2022 display name",
                "CBS form / population",
                "Explanation",
                "Evidence",
                "Joined host",
                "Confidence",
            ),
            [
                (
                    row["locality_code"],
                    row["locality_name_he"],
                    f"{row['cbs_2022_form']} / {row['cbs_2022_population'] or 'not separate'}",
                    EXPLANATION_LABELS[row["explanation_category"]],
                    format_explanation_evidence(row),
                    (
                        f"{row['joined_host_locality_name']} "
                        f"({row['joined_host_locality_code']}), "
                        f"station {row['joined_host_kalpi']}"
                        if row["joined_host_locality_code"]
                        else "none"
                    ),
                    row["explanation_review_status"],
                )
                for row in no_result_rows
            ],
        )
    )
    lines.extend(
        [
            "",
            "Detailed arithmetic, source-name discrepancies, and display decisions are retained in `docs/LOCALITY_RESULT_PRESENCE_AUDIT.csv` and `data/manual/locality_result_presence_reviews.csv`.",
        ]
    )

    lines.extend(["", "## Other Partial-Result Localities", ""])
    lines.extend(
        markdown_table(
            ("Code", "2022 name", "Results present", "Missing"),
            [
                (
                    row["locality_code"],
                    row["locality_name_he"],
                    format_elections(row["result_elections"].split("|")),
                    format_elections(row["missing_elections"].split("|")),
                )
                for row in other_partial_rows
            ],
        )
    )
    lines.extend(
        [
            "",
            "The complete machine-readable exception inventory is `docs/LOCALITY_RESULT_PRESENCE_AUDIT.csv`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    metadata_rows = read_csv(METADATA_PATH)
    metadata_by_id: dict[str, dict[str, str]] = {}
    for row in metadata_rows:
        locality_id = row.get("locality_id", "").strip()
        if not locality_id or locality_id in metadata_by_id:
            raise ValueError(f"Missing or duplicate locality metadata ID: {locality_id}")
        metadata_by_id[locality_id] = row

    result_ids_by_election: dict[str, set[str]] = {}
    for election in ELECTIONS:
        rows = read_csv(RESULTS_ROOT / f"{election.lower()}.csv")
        locality_ids = [row.get("locality_id", "").strip() for row in rows]
        duplicates = sorted(
            locality_id
            for locality_id, count in Counter(locality_ids).items()
            if locality_id and count > 1
        )
        if duplicates:
            raise ValueError(f"{election} has duplicate locality result IDs: {duplicates}")
        unknown_ids = sorted(
            locality_id
            for locality_id in locality_ids
            if locality_id.startswith("loc:") and locality_id not in metadata_by_id
        )
        if unknown_ids:
            raise ValueError(f"{election} has result IDs missing from 2022 metadata: {unknown_ids}")
        result_ids_by_election[election] = set(locality_ids)

    overrides_by_id = parse_override_rows(
        read_csv(OVERRIDES_PATH), metadata_by_id, result_ids_by_election
    )
    explanation_reviews = parse_explanation_reviews(
        read_csv(REVIEWS_PATH), metadata_by_id
    )

    structural_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    audit_rows: list[dict[str, str]] = []

    for metadata in sorted(metadata_rows, key=lambda row: int(row["locality_code"])):
        locality_id = metadata["locality_id"]
        locality_code = int(metadata["locality_code"])
        structural_label = structural_class(locality_code)
        present = tuple(
            election for election in ELECTIONS if locality_id in result_ids_by_election[election]
        )

        if structural_label:
            structural_counts[structural_label] += 1
            if present:
                raise ValueError(
                    f"Structural display feature {locality_id} has election results in {present}"
                )
            continue

        missing = tuple(election for election in ELECTIONS if election not in present)
        status = "all" if not missing else "none" if not present else "partial"
        status_counts[status] += 1
        if status == "all":
            continue

        reviewed_rule, review_note = summarize_overrides(overrides_by_id.get(locality_id, []))
        explanation = explanation_reviews.get(locality_id, {})
        audit_rows.append(
            {
                "locality_id": locality_id,
                "locality_code": str(locality_code),
                "locality_name_he": metadata.get("locality_name_he", ""),
                "locality_name_en": metadata.get("locality_name_en", ""),
                "result_status": status,
                "result_elections": "|".join(present),
                "missing_elections": "|".join(missing),
                "west_bank_code_range": "yes" if 3500 <= locality_code < 4000 else "no",
                "function_codes": metadata.get("cod_tifkud_values", ""),
                "reviewed_display_rule": reviewed_rule,
                "review_note": review_note,
                "explanation_review_status": explanation.get("review_status", ""),
                "explanation_category": explanation.get("explanation_category", ""),
                "cbs_2022_name": explanation.get("cbs_2022_name", ""),
                "cbs_2022_form_code": explanation.get("cbs_2022_form_code", ""),
                "cbs_2022_form": explanation.get("cbs_2022_form", ""),
                "cbs_2022_population": explanation.get("cbs_2022_population", ""),
                "evidence_election": explanation.get("evidence_election", ""),
                "evidence_eligible_voters": explanation.get(
                    "evidence_eligible_voters", ""
                ),
                "joined_host_locality_code": explanation.get(
                    "joined_host_locality_code", ""
                ),
                "joined_host_locality_name": explanation.get(
                    "joined_host_locality_name", ""
                ),
                "joined_host_kalpi": explanation.get("joined_host_kalpi", ""),
                "explanation_note": explanation.get("explanation_note", ""),
            }
        )

    no_result_ids = {
        row["locality_id"] for row in audit_rows if row["result_status"] == "none"
    }
    if set(explanation_reviews) != no_result_ids:
        missing = sorted(no_result_ids - set(explanation_reviews))
        extra = sorted(set(explanation_reviews) - no_result_ids)
        raise ValueError(
            f"No-result explanation review coverage changed; missing={missing}, extra={extra}"
        )
    validate_explanation_evidence(explanation_reviews, metadata_by_id)
    joined_rows = read_csv(JOINED_COMPOSITES_PATH)
    validate_joined_composites(joined_rows, metadata_by_id)

    write_csv(AUDIT_CSV_PATH, audit_rows)
    write_markdown(
        AUDIT_MD_PATH,
        audit_rows,
        joined_rows,
        status_counts,
        structural_counts,
        len(metadata_rows),
    )

    print(f"metadata_features={len(metadata_rows)}")
    print(f"structural_features={sum(structural_counts.values())}")
    print(f"all_elections={status_counts['all']}")
    print(f"partial_elections={status_counts['partial']}")
    print(f"no_elections={status_counts['none']}")
    print(f"exception_rows={len(audit_rows)}")
    print(f"wrote={AUDIT_CSV_PATH.relative_to(ROOT)}")
    print(f"wrote={AUDIT_MD_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
