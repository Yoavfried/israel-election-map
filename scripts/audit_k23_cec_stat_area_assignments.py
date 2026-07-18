from __future__ import annotations

import hashlib
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

LOCAL_AUDIT_PYTHON = Path(__file__).resolve().parents[1] / ".local" / "python-audit"
if LOCAL_AUDIT_PYTHON.exists():
    sys.path.append(str(LOCAL_AUDIT_PYTHON))

import pandas as pd

from pipeline_common import PROCESSED_DIR, RAW_DIR, ensure_dir, int_value, write_csv, write_json


SOURCE = RAW_DIR / "archive_knesset23_kalpies_report_19_1_20_1.xlsx"
ASSIGNMENTS = PROCESSED_DIR / "assignments" / "historical_ballot_assignments.csv"
METADATA = PROCESSED_DIR / "geographies" / "statistical_areas_2011.metadata.csv"
OUT_DIR = PROCESSED_DIR / "audits"

CANDIDATE_COLUMNS = [
    "source_row_uid",
    "election",
    "source_locality_code",
    "source_locality_name",
    "source_kalpi",
    "ballot_base",
    "actual_voters",
    "candidate_stat_area_id",
    "stat_area_number",
    "yishuv_stat",
    "ags_value",
    "evidence_method",
    "source_workbook",
]
VALIDATION_COLUMNS = [
    "source_locality_code",
    "ballot_base",
    "ags_value",
    "derived_stat_area_id",
    "crosswalk_stat_area_number",
    "crosswalk_stat_area_id",
    "status",
]
CONFLICT_COLUMNS = [
    "conflict_type",
    "source_locality_code",
    "source_locality_name",
    "ballot_base",
    "source_kalpi",
    "ags_values",
    "candidate_stat_area_id",
    "known_stat_area_id",
    "reason",
]
COVERAGE_COLUMNS = [
    "source_locality_code",
    "source_locality_name",
    "pending_rows",
    "pending_actual_voters",
    "candidate_rows",
    "candidate_actual_voters",
    "blank_ags_rows",
    "blank_ags_actual_voters",
]


def normalize_integer(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    try:
        return str(int(Decimal(text)))
    except (InvalidOperation, ValueError):
        digits = "".join(character for character in text if character.isdigit())
        return str(int(digits)) if digits else ""


def ballot_base(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(Decimal(text)))
    except InvalidOperation:
        return text.split(".", 1)[0]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assignment_fingerprint(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(
        f"{row['source_row_uid']}|{row['candidate_stat_area_id']}"
        for row in sorted(rows, key=lambda item: item["source_row_uid"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ensure_dir(OUT_DIR)
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing official K23 polling-place workbook: {SOURCE}")

    raw = pd.read_excel(SOURCE, sheet_name="DataSheet", header=0, dtype=str).fillna("")
    required = ["סמל ישוב בחירות", "שם ישוב בחירות", "סמל קלפי", 'אג"ס']
    missing = [column for column in required if column not in raw.columns]
    if missing:
        raise ValueError(f"K23 polling-place workbook is missing columns: {missing}")

    workbook = pd.DataFrame(
        {
            "source_locality_code": raw["סמל ישוב בחירות"].map(normalize_integer),
            "source_locality_name": raw["שם ישוב בחירות"].astype(str).str.strip(),
            "source_kalpi": raw["סמל קלפי"].astype(str).str.strip(),
            "ballot_base": raw["סמל קלפי"].map(ballot_base),
            "ags_value": raw['אג"ס'].map(normalize_integer),
        }
    )
    if (
        workbook["source_locality_code"].eq("")
        | workbook["ballot_base"].eq("")
    ).any():
        raise ValueError("K23 polling-place workbook contains a blank ballot key")

    key_columns = ["source_locality_code", "ballot_base"]
    workbook_index: dict[tuple[str, str], dict[str, str]] = {}
    conflicts: list[dict[str, Any]] = []
    multiple_value_keys = 0
    for key, group in workbook.groupby(key_columns, sort=True):
        values = sorted(set(value for value in group["ags_value"] if value))
        if len(values) > 1:
            multiple_value_keys += 1
            conflicts.append(
                {
                    "conflict_type": "multiple_ags_values",
                    "source_locality_code": key[0],
                    "source_locality_name": group.iloc[0]["source_locality_name"],
                    "ballot_base": key[1],
                    "source_kalpi": "|".join(group["source_kalpi"]),
                    "ags_values": "|".join(values),
                    "candidate_stat_area_id": "",
                    "known_stat_area_id": "",
                    "reason": "One base ballot has more than one non-empty AGS value",
                }
            )
            continue
        workbook_index[key] = {
            "ags_value": values[0] if values else "",
            "source_locality_name": group.iloc[0]["source_locality_name"],
            "source_kalpi": "|".join(group["source_kalpi"]),
        }

    assignments = pd.read_csv(
        ASSIGNMENTS, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    assignments = assignments[assignments["election"] == "K23"].copy()
    assignments["source_locality_code"] = assignments["source_locality_code"].map(
        normalize_integer
    )
    assignments["ballot_base"] = assignments["ballot_base"].map(normalize_integer)

    validation: list[dict[str, Any]] = []
    contradicted_keys: set[tuple[str, str]] = set()
    official = assignments[
        assignments["historical_assignment_method"].str.startswith(
            "official_cbs_ballot_crosswalk"
        )
    ]
    for key, group in official.groupby(key_columns, sort=True):
        workbook_row = workbook_index.get(key)
        if not workbook_row or not workbook_row["ags_value"]:
            continue
        known_ids = sorted(set(value for value in group["stat_area_id"] if value))
        known_numbers = sorted(
            set(value for value in group["stat_area_number"] if value)
        )
        if len(known_ids) != 1 or len(known_numbers) != 1:
            raise ValueError(f"Official K23 crosswalk is not unique for ballot key {key}")
        ags = workbook_row["ags_value"]
        yishuv_stat = str(int(key[0]) * 10000 + int(ags))
        derived_id = f"stat2011:{yishuv_stat}"
        status = "exact_agreement" if derived_id == known_ids[0] else "contradiction"
        validation.append(
            {
                "source_locality_code": key[0],
                "ballot_base": key[1],
                "ags_value": ags,
                "derived_stat_area_id": derived_id,
                "crosswalk_stat_area_number": known_numbers[0],
                "crosswalk_stat_area_id": known_ids[0],
                "status": status,
            }
        )
        if status == "contradiction":
            contradicted_keys.add(key)
            conflicts.append(
                {
                    "conflict_type": "official_crosswalk_contradiction",
                    "source_locality_code": key[0],
                    "source_locality_name": workbook_row["source_locality_name"],
                    "ballot_base": key[1],
                    "source_kalpi": workbook_row["source_kalpi"],
                    "ags_values": ags,
                    "candidate_stat_area_id": derived_id,
                    "known_stat_area_id": known_ids[0],
                    "reason": "The K23 AGS field contradicts the official CBS crosswalk",
                }
            )

    compared = len(validation)
    agreements = sum(row["status"] == "exact_agreement" for row in validation)
    if compared < 100 or agreements / compared < 0.999:
        raise ValueError(
            "K23 AGS validation is not strong enough to support direct assignments: "
            f"{agreements}/{compared}"
        )

    metadata = pd.read_csv(METADATA, dtype=str, encoding="utf-8-sig").fillna("")
    valid_stat_ids = set(metadata["stat_area_id"])
    candidates: list[dict[str, Any]] = []
    pending = assignments[
        assignments["historical_assignment_status"]
        == "no_direct_historical_assignment"
    ]
    for _, row in pending.iterrows():
        key = (row["source_locality_code"], row["ballot_base"])
        workbook_row = workbook_index.get(key)
        if not workbook_row or not workbook_row["ags_value"] or key in contradicted_keys:
            continue
        ags = workbook_row["ags_value"]
        yishuv_stat = str(int(key[0]) * 10000 + int(ags))
        stat_area_id = f"stat2011:{yishuv_stat}"
        if stat_area_id not in valid_stat_ids:
            conflicts.append(
                {
                    "conflict_type": "ags_target_missing_geometry",
                    "source_locality_code": key[0],
                    "source_locality_name": row["source_locality_name"],
                    "ballot_base": key[1],
                    "source_kalpi": row["source_kalpi"],
                    "ags_values": ags,
                    "candidate_stat_area_id": stat_area_id,
                    "known_stat_area_id": "",
                    "reason": "The derived 2011 statistical-area polygon is unavailable",
                }
            )
            continue
        candidates.append(
            {
                "source_row_uid": row["source_row_uid"],
                "election": "K23",
                "source_locality_code": key[0],
                "source_locality_name": row["source_locality_name"],
                "source_kalpi": row["source_kalpi"],
                "ballot_base": key[1],
                "actual_voters": int_value(row["actual_voters"]),
                "candidate_stat_area_id": stat_area_id,
                "stat_area_number": ags,
                "yishuv_stat": yishuv_stat,
                "ags_value": ags,
                "evidence_method": "official_cec_k23_ags",
                "source_workbook": SOURCE.name,
            }
        )

    if len({row["source_row_uid"] for row in candidates}) != len(candidates):
        raise ValueError("K23 AGS candidates contain duplicate source rows")

    candidate_ids = {row["source_row_uid"] for row in candidates}
    coverage: list[dict[str, Any]] = []
    for key, group in pending.groupby(
        ["source_locality_code", "source_locality_name"], sort=True
    ):
        selected = group[group["source_row_uid"].isin(candidate_ids)]
        blank = group[~group["source_row_uid"].isin(candidate_ids)]
        coverage.append(
            {
                "source_locality_code": key[0],
                "source_locality_name": key[1],
                "pending_rows": len(group),
                "pending_actual_voters": sum(map(int_value, group["actual_voters"])),
                "candidate_rows": len(selected),
                "candidate_actual_voters": sum(
                    map(int_value, selected["actual_voters"])
                ),
                "blank_ags_rows": len(blank),
                "blank_ags_actual_voters": sum(map(int_value, blank["actual_voters"])),
            }
        )

    write_csv(
        OUT_DIR / "k23_cec_ags_assignment_candidates.csv",
        candidates,
        CANDIDATE_COLUMNS,
    )
    write_csv(
        OUT_DIR / "k23_cec_ags_validation.csv", validation, VALIDATION_COLUMNS
    )
    write_csv(OUT_DIR / "k23_cec_ags_conflicts.csv", conflicts, CONFLICT_COLUMNS)
    write_csv(OUT_DIR / "k23_cec_ags_coverage.csv", coverage, COVERAGE_COLUMNS)

    summary = {
        "status": "complete",
        "election": "K23",
        "source": str(SOURCE.relative_to(Path(__file__).resolve().parents[1])).replace(
            "\\", "/"
        ),
        "source_sha256": file_sha256(SOURCE),
        "workbook_rows": len(workbook),
        "workbook_ballot_keys": len(workbook_index) + multiple_value_keys,
        "workbook_keys_with_ags": sum(
            bool(row["ags_value"]) for row in workbook_index.values()
        ),
        "workbook_keys_with_multiple_ags": multiple_value_keys,
        "crosswalk_comparisons": compared,
        "crosswalk_exact_agreements": agreements,
        "crosswalk_contradictions": compared - agreements,
        "crosswalk_agreement_rate": agreements / compared,
        "pending_rows_before": len(pending),
        "pending_actual_voters_before": sum(map(int_value, pending["actual_voters"])),
        "candidate_rows": len(candidates),
        "candidate_actual_voters": sum(
            int_value(row["actual_voters"]) for row in candidates
        ),
        "candidate_assignment_sha256": assignment_fingerprint(candidates),
        "withheld_conflicts": len(conflicts),
    }
    write_json(OUT_DIR / "k23_cec_ags_assignment_summary.json", summary)

    print(
        f"k23_ags_validation={agreements}/{compared} "
        f"({summary['crosswalk_agreement_rate']:.4%})"
    )
    print(
        f"k23_ags_candidates={len(candidates)} "
        f"actual_voters={summary['candidate_actual_voters']}"
    )
    print(f"k23_ags_withheld_conflicts={len(conflicts)}")


if __name__ == "__main__":
    main()
