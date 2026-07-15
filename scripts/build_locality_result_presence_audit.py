#!/usr/bin/env python3
"""Audit standalone locality-result presence across K17 through K25."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "data" / "processed" / "geographies" / "localities_2022.metadata.csv"
RESULTS_ROOT = ROOT / "data" / "processed" / "public" / "locality_results"
OVERRIDES_PATH = ROOT / "data" / "manual" / "locality_display_overrides.csv"
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
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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
        "## Review Status",
        "",
        "This inventory is complete as a reproducible presence calculation, but the historical interpretation and election-specific display review are not complete. A `none` value in the reviewed-display column means that no explicit decision has been recorded yet; it does not mean that the current visible or neutral treatment is final.",
        "",
        "## Counts",
        "",
    ]
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

    lines.extend(["", "## No Standalone Result in K17-K25", ""])
    lines.extend(
        markdown_table(
            ("Code", "2022 name", "English name", "West Bank range", "Reviewed display rule"),
            [
                (
                    row["locality_code"],
                    row["locality_name_he"],
                    row["locality_name_en"],
                    row["west_bank_code_range"],
                    row["reviewed_display_rule"] or "none",
                )
                for row in no_result_rows
            ],
        )
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
            }
        )

    write_csv(AUDIT_CSV_PATH, audit_rows)
    write_markdown(
        AUDIT_MD_PATH,
        audit_rows,
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
