from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from pipeline_common import PROCESSED_DIR, ROOT, int_value, normalize_code, normalize_spaces, write_csv, write_json


BALLOT_ROWS = PROCESSED_DIR / "normalized" / "ballot_rows.csv"
LOCALITIES = PROCESSED_DIR / "geographies" / "localities_2022.metadata.csv"
CROSSWALK = ROOT / "docs" / "LOCALITY_CROSSWALK_RESOLUTION_PLAN.csv"
OUT_DIR = PROCESSED_DIR / "assignments"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def norm_name(value: Any) -> str:
    text = normalize_spaces(value)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = text.replace("׳", "").replace("״", "")
    text = text.replace("'", "").replace('"', "")
    text = re.sub(r"[\s.,:/(){}\[\]\-_*]+", "", text)
    return text


def split_source_identity(value: str) -> tuple[str, str]:
    match = re.search(r"\[(\d+)\]\s*$", value or "")
    code = normalize_code(match.group(1)) if match else ""
    name = re.sub(r"\s*\[\d+\]\s*$", "", value or "").strip()
    return name, code


def bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def locality_indexes(rows: list[dict[str, str]]) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    by_code: dict[str, dict] = {}
    by_name: dict[str, list[dict]] = {}
    for row in rows:
        code = normalize_code(row["locality_code"])
        row = dict(row)
        row["locality_code"] = code
        row["single_stat_area"] = bool_value(row["single_stat_area"])
        row["has_function_code"] = bool_value(row.get("has_function_code", ""))
        by_code[code] = row
        by_name.setdefault(norm_name(row["locality_name_he"]), []).append(row)
    return by_code, by_name


def prefer_real_locality(candidates: list[dict]) -> list[dict]:
    preferred = [candidate for candidate in candidates if candidate.get("has_function_code")]
    return preferred or candidates


def crosswalk_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict]:
    index: dict[tuple[str, str], dict] = {}
    for row in rows:
        source_name, source_code = split_source_identity(row["unique locality unmatched"])
        source_norm = norm_name(source_name)
        if source_code:
            index[(source_code, source_norm)] = row
        index.setdefault(("", source_norm), row)
    return index


def find_crosswalk(row: dict[str, str], index: dict[tuple[str, str], dict]) -> dict | None:
    code = normalize_code(row["source_locality_code"])
    name_norm = norm_name(row["source_locality_name"])
    if code and (code, name_norm) in index:
        return index[(code, name_norm)]
    return index.get(("", name_norm))


def find_target_by_name(target_name: str, by_name: dict[str, list[dict]]) -> tuple[dict | None, str]:
    candidates = prefer_real_locality(by_name.get(norm_name(target_name), []))
    if len(candidates) == 1:
        return candidates[0], ""
    if not candidates:
        return None, f"target locality not found: {target_name}"
    return None, f"target locality name is ambiguous: {target_name}"


def assignment_from_locality(target: dict, method_source: str) -> dict[str, Any]:
    if target["single_stat_area"]:
        return {
            "assignment_method": "single_stat_locality",
            "assignment_source": method_source,
            "target_geography_type": "statistical_area",
            "target_locality_code": target["locality_code"],
            "target_locality_name": target["locality_name_he"],
            "target_stat_area_id": target["stat_area_ids"],
            "custom_geography_id": "",
            "needs_geocoding": False,
            "unresolved_reason": "",
        }
    return {
        "assignment_method": "direct_address_geocode_needed",
        "assignment_source": method_source,
        "target_geography_type": "statistical_area_pending_geocode",
        "target_locality_code": target["locality_code"],
        "target_locality_name": target["locality_name_he"],
        "target_stat_area_id": "",
        "custom_geography_id": "",
        "needs_geocoding": True,
        "unresolved_reason": "",
    }


def assignment_from_crosswalk(
    source_row: dict[str, str],
    crosswalk_row: dict[str, str],
    by_name: dict[str, list[dict]],
) -> dict[str, Any]:
    solution = crosswalk_row["solution"]
    geometry_target = crosswalk_row["geometry target"]
    custom_id = crosswalk_row["custom geometry id"] or geometry_target

    if solution == "accepted_locality_match":
        target, reason = find_target_by_name(geometry_target, by_name)
        if not target:
            return unresolved("reviewed_locality_target_missing", reason)
        return assignment_from_locality(target, "reviewed_locality_crosswalk")

    if solution == "address_geocode_to_current_polygons":
        return {
            "assignment_method": "direct_address_geocode_needed",
            "assignment_source": "reviewed_address_target_set",
            "target_geography_type": "statistical_area_pending_geocode",
            "target_locality_code": "",
            "target_locality_name": geometry_target,
            "target_stat_area_id": "",
            "custom_geography_id": "",
            "needs_geocoding": True,
            "unresolved_reason": "",
        }

    if solution == "custom_point_size_polygon":
        return {
            "assignment_method": "custom_point_size_polygon",
            "assignment_source": "reviewed_custom_bucket",
            "target_geography_type": "custom_geography",
            "target_locality_code": "",
            "target_locality_name": geometry_target,
            "target_stat_area_id": "",
            "custom_geography_id": custom_id,
            "needs_geocoding": False,
            "unresolved_reason": "",
        }

    if solution == "special_non_geographic":
        return {
            "assignment_method": "special_non_geographic",
            "assignment_source": "reviewed_crosswalk",
            "target_geography_type": "special_non_geographic",
            "target_locality_code": "",
            "target_locality_name": geometry_target,
            "target_stat_area_id": "",
            "custom_geography_id": custom_id,
            "needs_geocoding": False,
            "unresolved_reason": "",
        }

    return unresolved("unsupported_crosswalk_solution", solution)


def unresolved(reason: str, detail: str = "") -> dict[str, Any]:
    return {
        "assignment_method": "unresolved",
        "assignment_source": "",
        "target_geography_type": "unresolved",
        "target_locality_code": "",
        "target_locality_name": "",
        "target_stat_area_id": "",
        "custom_geography_id": "",
        "needs_geocoding": False,
        "unresolved_reason": f"{reason}: {detail}" if detail else reason,
    }


def assign_row(
    row: dict[str, str],
    localities_by_code: dict[str, dict],
    localities_by_name: dict[str, list[dict]],
    crosswalk: dict[tuple[str, str], dict],
) -> dict[str, Any]:
    if bool_value(row["is_envelope"]):
        return {
            "assignment_method": "official_envelope",
            "assignment_source": "envelope_detection",
            "target_geography_type": "official_envelope",
            "target_locality_code": "",
            "target_locality_name": "",
            "target_stat_area_id": "",
            "custom_geography_id": "special:envelope_votes",
            "needs_geocoding": False,
            "unresolved_reason": "",
        }

    reviewed = find_crosswalk(row, crosswalk)
    if reviewed:
        return assignment_from_crosswalk(row, reviewed, localities_by_name)

    code = normalize_code(row["source_locality_code"])
    if code and code in localities_by_code:
        return assignment_from_locality(localities_by_code[code], "automatic_code_match")

    candidates = prefer_real_locality(localities_by_name.get(norm_name(row["source_locality_name"]), []))
    if len(candidates) == 1:
        return assignment_from_locality(candidates[0], "automatic_name_match")
    if len(candidates) > 1:
        return unresolved("source locality name ambiguous", row["source_locality_name"])
    return unresolved("source locality not matched", row["source_locality_name"])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    ballot_rows = read_csv(BALLOT_ROWS)
    localities_by_code, localities_by_name = locality_indexes(read_csv(LOCALITIES))
    crosswalk = crosswalk_index(read_csv(CROSSWALK))

    output: list[dict[str, Any]] = []
    for row in ballot_rows:
        assignment = assign_row(row, localities_by_code, localities_by_name, crosswalk)
        output.append(
            {
                "source_row_uid": row["source_row_uid"],
                "election": row["election"],
                "election_number": row["election_number"],
                "source_row_id": row["source_row_id"],
                "source_locality_code": row["source_locality_code"],
                "source_locality_name": row["source_locality_name"],
                "source_kalpi": row["source_kalpi"],
                "eligible_voters": row["eligible_voters"],
                "actual_voters": row["actual_voters"],
                **assignment,
            }
        )

    fields = [
        "source_row_uid",
        "election",
        "election_number",
        "source_row_id",
        "source_locality_code",
        "source_locality_name",
        "source_kalpi",
        "eligible_voters",
        "actual_voters",
        "assignment_method",
        "assignment_source",
        "target_geography_type",
        "target_locality_code",
        "target_locality_name",
        "target_stat_area_id",
        "custom_geography_id",
        "needs_geocoding",
        "unresolved_reason",
    ]
    write_csv(OUT_DIR / "ballot_assignment_plan.csv", output, fields)

    summary_rows: list[dict[str, Any]] = []
    for election in sorted({row["election"] for row in output}, reverse=True):
        election_rows = [row for row in output if row["election"] == election]
        by_method = Counter(row["assignment_method"] for row in election_rows)
        summary_rows.append(
            {
                "election": election,
                "rows": len(election_rows),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in election_rows),
                "single_stat_rows": by_method["single_stat_locality"],
                "geocode_needed_rows": by_method["direct_address_geocode_needed"],
                "custom_rows": by_method["custom_point_size_polygon"],
                "special_non_geographic_rows": by_method["special_non_geographic"],
                "envelope_rows": by_method["official_envelope"],
                "unresolved_rows": by_method["unresolved"],
                "unresolved_actual_voters": sum(
                    int_value(row["actual_voters"])
                    for row in election_rows
                    if row["assignment_method"] == "unresolved"
                ),
            }
        )
    write_csv(
        OUT_DIR / "assignment_plan_summary.csv",
        summary_rows,
        [
            "election",
            "rows",
            "actual_voters",
            "single_stat_rows",
            "geocode_needed_rows",
            "custom_rows",
            "special_non_geographic_rows",
            "envelope_rows",
            "unresolved_rows",
            "unresolved_actual_voters",
        ],
    )
    write_json(OUT_DIR / "assignment_plan_summary.json", summary_rows)

    geocode_worklist = [row for row in output if row["assignment_method"] == "direct_address_geocode_needed"]
    write_csv(OUT_DIR / "geocoding_worklist.csv", geocode_worklist, fields)

    unresolved_rows = [row for row in output if row["assignment_method"] == "unresolved"]
    write_csv(OUT_DIR / "unresolved_assignment_rows.csv", unresolved_rows, fields)

    print(f"assignment_rows={len(output)}")
    print(f"geocode_worklist_rows={len(geocode_worklist)}")
    print(f"unresolved_rows={len(unresolved_rows)}")
    for row in summary_rows:
        print(
            f"{row['election']}: single={row['single_stat_rows']} geocode={row['geocode_needed_rows']} "
            f"custom={row['custom_rows']} special={row['special_non_geographic_rows']} "
            f"envelope={row['envelope_rows']} unresolved={row['unresolved_rows']}"
        )


if __name__ == "__main__":
    main()
