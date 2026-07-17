from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from functools import cache
from pathlib import Path
from typing import Any

from pipeline_common import (
    MANUAL_DIR,
    PROCESSED_DIR,
    int_value,
    normalize_spaces,
    write_csv,
    write_json,
)


ASSIGNMENT_PLAN = PROCESSED_DIR / "assignments" / "ballot_assignment_plan.csv"
HISTORICAL_ASSIGNMENTS = (
    PROCESSED_DIR / "assignments" / "historical_ballot_assignments.csv"
)
STAT_AREA_METADATA = (
    PROCESSED_DIR / "geographies" / "statistical_areas_2022.metadata.csv"
)
HISTORICAL_STAT_AREA_METADATA = (
    PROCESSED_DIR / "geographies" / "statistical_areas_2011.metadata.csv"
)
ARCGIS_RECONSTRUCTION_CANDIDATES = (
    PROCESSED_DIR / "audits" / "arcgis_assignment_reconstruction_candidates.csv"
)
ARCGIS_RECONSTRUCTION_LOCALITIES = (
    PROCESSED_DIR / "audits" / "arcgis_assignment_reconstruction_localities.csv"
)
ARCGIS_RECONSTRUCTION_REVIEWS = (
    MANUAL_DIR / "arcgis_assignment_reconstruction_reviews.csv"
)
OUT_DIR = PROCESSED_DIR / "assignments"
COMPOSITE_LOCALITIES = MANUAL_DIR / "composite_localities.csv"
HISTORICAL_PENDING_STATUSES = {
    "no_direct_historical_assignment",
    "crosswalk_area_missing_geometry",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def reconstruction_fingerprint(rows: list[dict[str, str]]) -> str:
    payload = "\n".join(
        f"{row['source_row_uid']}|{row['candidate_stat_area_id']}"
        for row in sorted(rows, key=lambda item: item["source_row_uid"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_locality_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    try:
        number = float(text)
    except ValueError:
        digits = "".join(char for char in text if char.isdigit())
        return str(int(digits)) if digits else ""
    if number.is_integer():
        return str(int(number))
    digits = "".join(char for char in text if char.isdigit())
    return str(int(digits)) if digits else ""


def split_locality_codes(value: Any) -> list[str]:
    codes: list[str] = []
    for part in str(value or "").split("|"):
        code = normalize_locality_code(part)
        if code and code not in codes:
            codes.append(code)
    return codes


@cache
def load_composite_locality_index() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(COMPOSITE_LOCALITIES)
    if not rows:
        raise FileNotFoundError(
            f"Missing or empty reviewed composite-locality table: {COMPOSITE_LOCALITIES}"
        )

    index: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        composite_id = row.get("composite_locality_id", "").strip()
        source_name = normalize_spaces(row.get("source_locality_name", ""))
        elections = [
            value.strip()
            for value in row.get("elections", "").split("|")
            if value.strip()
        ]
        if not composite_id or not source_name or not elections:
            raise ValueError(f"Invalid composite-locality row: {row}")
        for election in elections:
            key = (election, source_name)
            if key in index:
                raise ValueError(
                    f"Duplicate composite-locality matcher: {election} / {source_name}"
                )
            index[key] = row
    return index


def locality_assignment(row: dict[str, str]) -> dict[str, Any]:
    method = row.get("assignment_method", "")
    if method == "official_envelope":
        return {
            "locality_assignment_status": "official_envelope",
            "locality_geography_type": "envelope",
            "locality_geography_id": "envelope:official",
            "locality_result_code": "",
            "locality_result_name": "\u05de\u05e2\u05d8\u05e4\u05d5\u05ea \u05d7\u05d9\u05e6\u05d5\u05e0\u05d9\u05d5\u05ea",
            "is_locality_mapped": False,
        }
    if method == "special_non_geographic":
        return {
            "locality_assignment_status": "special_non_geographic",
            "locality_geography_type": "non_geographic",
            "locality_geography_id": "",
            "locality_result_code": "",
            "locality_result_name": row.get("target_locality_name", ""),
            "is_locality_mapped": False,
        }
    if method == "custom_point_size_polygon":
        return {
            "locality_assignment_status": "custom_geography_assigned",
            "locality_geography_type": "custom_geography",
            "locality_geography_id": row.get("custom_geography_id", ""),
            "locality_result_code": "",
            "locality_result_name": row.get("target_locality_name", ""),
            "is_locality_mapped": True,
        }

    composite = load_composite_locality_index().get(
        (
            row.get("election", ""),
            normalize_spaces(row.get("source_locality_name", "")),
        )
    )
    if composite:
        return {
            "locality_assignment_status": "composite_locality_assigned",
            "locality_geography_type": "composite_locality",
            "locality_geography_id": composite["composite_locality_id"],
            "locality_result_code": row.get("source_locality_code", ""),
            "locality_result_name": composite["name_he"],
            "is_locality_mapped": True,
        }

    target_codes = split_locality_codes(row.get("target_locality_code", ""))
    if len(target_codes) == 1:
        target_code = target_codes[0]
        return {
            "locality_assignment_status": "current_locality_assigned",
            "locality_geography_type": "locality",
            "locality_geography_id": f"loc:{target_code}",
            "locality_result_code": target_code,
            "locality_result_name": row.get("target_locality_name", ""),
            "is_locality_mapped": True,
        }

    return {
        "locality_assignment_status": "unresolved",
        "locality_geography_type": "unmapped",
        "locality_geography_id": "",
        "locality_result_code": "",
        "locality_result_name": row.get("target_locality_name", ""),
        "is_locality_mapped": False,
    }


def base_output(row: dict[str, str]) -> dict[str, Any]:
    return {
        "source_row_uid": row["source_row_uid"],
        "election": row["election"],
        "election_number": row["election_number"],
        "source_row_id": row["source_row_id"],
        "source_locality_code": row["source_locality_code"],
        "source_locality_name": row["source_locality_name"],
        "source_kalpi": row["source_kalpi"],
        "eligible_voters": row["eligible_voters"],
        "actual_voters": row["actual_voters"],
        "assignment_method": row["assignment_method"],
        "assignment_source": row["assignment_source"],
        **locality_assignment(row),
    }


def mapped_assignment(
    row: dict[str, str],
    stat_area_id: str,
    vintage: int,
    yishuv_stat: Any,
    stat_area_number: Any,
    locality_code: Any,
    locality_name: str,
    status: str,
    method: str,
    source: str,
) -> dict[str, Any]:
    return {
        **base_output(row),
        "geography_assignment_status": status,
        "geography_type": "statistical_area",
        "geography_id": stat_area_id,
        "stat_area_id": stat_area_id,
        "stat_area_vintage": vintage,
        "stat_area_yishuv_stat": yishuv_stat,
        "stat_area_number": stat_area_number,
        "stat_area_yishuv_stat_2022": yishuv_stat if vintage == 2022 else "",
        "stat_area_stat_2022": stat_area_number if vintage == 2022 else "",
        "locality_id": f"loc:{locality_code}",
        "locality_code": locality_code,
        "locality_name": locality_name,
        "custom_geography_id": "",
        "is_mapped": True,
        "is_geographic": True,
        "final_assignment_method": method,
        "final_assignment_source": source,
        "unresolved_reason": "",
    }


def historical_stat_assignment(
    row: dict[str, str], historical: dict[str, str]
) -> dict[str, Any]:
    return mapped_assignment(
        row=row,
        stat_area_id=historical["stat_area_id"],
        vintage=int_value(historical["stat_area_vintage"]),
        yishuv_stat=historical["yishuv_stat"],
        stat_area_number=historical["stat_area_number"],
        locality_code=historical["historical_locality_code"],
        locality_name=historical["historical_locality_name"],
        status=historical["historical_assignment_status"],
        method=historical["historical_assignment_method"],
        source=historical["historical_assignment_source"],
    )


def arcgis_reconstructed_assignment(
    row: dict[str, str],
    candidate: dict[str, str],
    stat: dict[str, str],
) -> dict[str, Any]:
    return mapped_assignment(
        row=row,
        stat_area_id=stat["stat_area_id"],
        vintage=int_value(stat["stat_area_vintage"]),
        yishuv_stat=stat["yishuv_stat"],
        stat_area_number=stat["stat_area_number"],
        locality_code=stat["locality_code"],
        locality_name=stat["locality_name_he"],
        status="arcgis_reconstructed_exact_assigned",
        method="arcgis_residual_partition_tier_a",
        source=(
            f"{candidate['source']};review="
            "data/manual/arcgis_assignment_reconstruction_reviews.csv"
        ),
    )


def current_stat_assignment(
    row: dict[str, str], stat: dict[str, str]
) -> dict[str, Any]:
    return mapped_assignment(
        row=row,
        stat_area_id=stat["stat_area_id"],
        vintage=2022,
        yishuv_stat=stat["yishuv_stat_2022"],
        stat_area_number=stat["stat_2022"],
        locality_code=stat["locality_code"],
        locality_name=stat["locality_name_he"],
        status="single_stat_assigned",
        method="single_stat_locality",
        source=row["assignment_source"],
    )


def custom_assignment(row: dict[str, str]) -> dict[str, Any]:
    return {
        **base_output(row),
        "geography_assignment_status": "custom_geography_assigned",
        "geography_type": "custom_geography",
        "geography_id": row["custom_geography_id"],
        "stat_area_id": "",
        "stat_area_vintage": "",
        "stat_area_yishuv_stat": "",
        "stat_area_number": "",
        "stat_area_yishuv_stat_2022": "",
        "stat_area_stat_2022": "",
        "locality_id": "",
        "locality_code": "",
        "locality_name": row["target_locality_name"],
        "custom_geography_id": row["custom_geography_id"],
        "is_mapped": True,
        "is_geographic": True,
        "final_assignment_method": "custom_point_size_polygon",
        "final_assignment_source": row["assignment_source"],
        "unresolved_reason": "",
    }


def unresolved(row: dict[str, str], status: str, reason: str) -> dict[str, Any]:
    return {
        **base_output(row),
        "geography_assignment_status": status,
        "geography_type": row["target_geography_type"] or "unmapped",
        "geography_id": row["custom_geography_id"],
        "stat_area_id": "",
        "stat_area_vintage": "",
        "stat_area_yishuv_stat": "",
        "stat_area_number": "",
        "stat_area_yishuv_stat_2022": "",
        "stat_area_stat_2022": "",
        "locality_id": "",
        "locality_code": row.get("target_locality_code", ""),
        "locality_name": row.get("target_locality_name", ""),
        "custom_geography_id": row["custom_geography_id"],
        "is_mapped": False,
        "is_geographic": False,
        "final_assignment_method": row["assignment_method"],
        "final_assignment_source": row["assignment_source"],
        "unresolved_reason": reason,
    }


def load_historical_assignments() -> dict[str, dict[str, str]]:
    rows = read_csv(HISTORICAL_ASSIGNMENTS)
    if not rows:
        raise FileNotFoundError(
            "Missing direct historical assignments; run "
            f"build_historical_ballot_assignments.py: {HISTORICAL_ASSIGNMENTS}"
        )
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        uid = row.get("source_row_uid", "")
        if not uid or uid in output:
            raise ValueError(
                f"Missing or duplicate historical assignment UID: {uid or '(blank)'}"
            )
        output[uid] = row
    return output


def load_approved_arcgis_reconstructions() -> dict[str, dict[str, str]]:
    reviews = read_csv(ARCGIS_RECONSTRUCTION_REVIEWS)
    candidates = read_csv(ARCGIS_RECONSTRUCTION_CANDIDATES)
    reports = read_csv(ARCGIS_RECONSTRUCTION_LOCALITIES)
    if not reviews or not candidates or not reports:
        raise FileNotFoundError(
            "ArcGIS reconstruction approvals require the reviewed table and "
            "fresh audit outputs"
        )

    def locality_key(row: dict[str, str]) -> tuple[str, str]:
        return (
            normalize_spaces(row.get("election", "")),
            normalize_locality_code(row.get("source_locality_code", "")),
        )

    report_index: dict[tuple[str, str], dict[str, str]] = {}
    for report in reports:
        key = locality_key(report)
        if key in report_index:
            raise ValueError(f"Duplicate ArcGIS reconstruction report: {key}")
        report_index[key] = report

    candidates_by_locality: dict[tuple[str, str], list[dict[str, str]]] = {}
    for candidate in candidates:
        candidates_by_locality.setdefault(locality_key(candidate), []).append(candidate)

    reviewed_keys: set[tuple[str, str]] = set()
    approved: dict[str, dict[str, str]] = {}
    for review in reviews:
        key = locality_key(review)
        if key in reviewed_keys:
            raise ValueError(f"Duplicate ArcGIS reconstruction review: {key}")
        reviewed_keys.add(key)
        decision = normalize_spaces(review.get("decision", "")).lower()
        if decision not in {"approved", "deferred", "rejected"}:
            raise ValueError(f"Unsupported ArcGIS reconstruction decision: {review}")
        if decision != "approved":
            continue

        report = report_index.get(key)
        locality_candidates = candidates_by_locality.get(key, [])
        if not report or not locality_candidates:
            raise ValueError(f"Approved ArcGIS reconstruction is absent from audit: {key}")
        if (
            review.get("evidence_tier") != "A"
            or report.get("status") != "unique_exact_partition"
            or report.get("evidence_tier") != "A"
            or int_value(report.get("secondary_area_mismatch_count")) != 0
        ):
            raise ValueError(f"Approved ArcGIS reconstruction is not current Tier A: {key}")
        if (
            int_value(review.get("candidate_rows")) != len(locality_candidates)
            or int_value(review.get("candidate_rows"))
            != int_value(report.get("candidate_rows"))
            or int_value(review.get("candidate_actual_voters"))
            != sum(int_value(row.get("actual_voters")) for row in locality_candidates)
            or int_value(review.get("candidate_actual_voters"))
            != int_value(report.get("pending_actual_voters"))
        ):
            raise ValueError(f"Approved ArcGIS reconstruction totals changed: {key}")
        if reconstruction_fingerprint(locality_candidates) != review.get(
            "candidate_assignment_sha256"
        ):
            raise ValueError(f"Approved ArcGIS reconstruction mapping changed: {key}")

        for candidate in locality_candidates:
            if candidate.get("evidence_tier") != "A":
                raise ValueError(f"Approved ArcGIS candidate is not Tier A: {key}")
            uid = candidate.get("source_row_uid", "")
            if not uid or uid in approved:
                raise ValueError(f"Missing or duplicate approved ArcGIS row: {uid}")
            approved[uid] = candidate
    return approved


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    assignment_rows = read_csv(ASSIGNMENT_PLAN)
    historical_assignments = load_historical_assignments()
    arcgis_reconstructions = load_approved_arcgis_reconstructions()
    stat_metadata = {
        row["stat_area_id"]: row for row in read_csv(STAT_AREA_METADATA)
    }
    historical_stat_metadata = {
        row["stat_area_id"]: row for row in read_csv(HISTORICAL_STAT_AREA_METADATA)
    }
    if not assignment_rows:
        raise FileNotFoundError(
            f"Missing assignment plan; run build_assignment_plan.py: {ASSIGNMENT_PLAN}"
        )

    output: list[dict[str, Any]] = []
    for row in assignment_rows:
        method = row["assignment_method"]
        historical = historical_assignments.get(row["source_row_uid"])

        if historical and normalize_bool(
            historical.get("is_historical_stat_mapped", "")
        ):
            output.append(historical_stat_assignment(row, historical))
            continue
        reconstruction = arcgis_reconstructions.get(row["source_row_uid"])
        if reconstruction:
            if (
                not historical
                or historical.get("historical_assignment_status")
                != "no_direct_historical_assignment"
            ):
                raise ValueError(
                    "ArcGIS reconstruction may only replace a missing direct "
                    f"historical assignment: {row['source_row_uid']}"
                )
            stat = historical_stat_metadata.get(
                reconstruction["candidate_stat_area_id"]
            )
            if not stat:
                raise ValueError(
                    "ArcGIS reconstruction target lacks 2011 metadata: "
                    f"{reconstruction['candidate_stat_area_id']}"
                )
            output.append(arcgis_reconstructed_assignment(row, reconstruction, stat))
            continue
        if (
            historical
            and historical.get("historical_assignment_status")
            != "not_applicable_non_geographic"
        ):
            output.append(
                unresolved(
                    row,
                    historical.get(
                        "historical_assignment_status",
                        "no_direct_historical_assignment",
                    ),
                    historical.get(
                        "unresolved_reason",
                        "No direct historical ballot assignment is available",
                    ),
                )
            )
            continue
        if method == "single_stat_locality":
            stat_id = row["target_stat_area_id"].split("|", 1)[0]
            stat = stat_metadata.get(stat_id)
            if stat:
                output.append(current_stat_assignment(row, stat))
            else:
                output.append(
                    unresolved(
                        row,
                        "missing_stat_area_metadata",
                        f"Statistical area not found: {stat_id}",
                    )
                )
            continue
        if method == "custom_point_size_polygon":
            output.append(custom_assignment(row))
            continue
        if method in {"special_non_geographic", "official_envelope"}:
            output.append(
                unresolved(
                    row,
                    method,
                    "Non-geographic row is counted but not mapped",
                )
            )
            continue
        output.append(
            unresolved(
                row,
                "unresolved",
                row.get("unresolved_reason", "Unresolved assignment"),
            )
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
        "geography_assignment_status",
        "geography_type",
        "geography_id",
        "stat_area_id",
        "stat_area_vintage",
        "stat_area_yishuv_stat",
        "stat_area_number",
        "stat_area_yishuv_stat_2022",
        "stat_area_stat_2022",
        "locality_id",
        "locality_code",
        "locality_name",
        "locality_assignment_status",
        "locality_geography_type",
        "locality_geography_id",
        "locality_result_code",
        "locality_result_name",
        "is_locality_mapped",
        "custom_geography_id",
        "is_mapped",
        "is_geographic",
        "final_assignment_method",
        "final_assignment_source",
        "unresolved_reason",
    ]
    write_csv(OUT_DIR / "ballot_geography_assignments.csv", output, fields)

    missing = [
        row
        for row in output
        if row["geography_assignment_status"] in HISTORICAL_PENDING_STATUSES
        or row["geography_assignment_status"] == "unresolved"
    ]
    write_csv(
        OUT_DIR / "unresolved_statistical_area_assignment_rows.csv",
        missing,
        fields,
    )

    summary: list[dict[str, Any]] = []
    for election in sorted({row["election"] for row in output}, reverse=True):
        rows = [row for row in output if row["election"] == election]
        statuses = Counter(row["geography_assignment_status"] for row in rows)
        mapped_rows = [row for row in rows if normalize_bool(row["is_mapped"])]
        locality_mapped_rows = [
            row for row in rows if normalize_bool(row["is_locality_mapped"])
        ]
        missing_rows = [
            row
            for row in rows
            if row["geography_assignment_status"] in HISTORICAL_PENDING_STATUSES
            or row["geography_assignment_status"] == "unresolved"
        ]
        summary.append(
            {
                "election": election,
                "rows": len(rows),
                "actual_voters": sum(int_value(row["actual_voters"]) for row in rows),
                "mapped_rows": len(mapped_rows),
                "mapped_actual_voters": sum(
                    int_value(row["actual_voters"]) for row in mapped_rows
                ),
                "stat_area_rows": sum(
                    row["geography_type"] == "statistical_area"
                    for row in mapped_rows
                ),
                "custom_geography_rows": sum(
                    row["geography_type"] == "custom_geography"
                    for row in mapped_rows
                ),
                "arcgis_reconstructed_rows": sum(
                    row["final_assignment_method"]
                    == "arcgis_residual_partition_tier_a"
                    for row in mapped_rows
                ),
                "arcgis_reconstructed_actual_voters": sum(
                    int_value(row["actual_voters"])
                    for row in mapped_rows
                    if row["final_assignment_method"]
                    == "arcgis_residual_partition_tier_a"
                ),
                "locality_mapped_rows": len(locality_mapped_rows),
                "locality_mapped_actual_voters": sum(
                    int_value(row["actual_voters"])
                    for row in locality_mapped_rows
                ),
                "statistical_area_pending_rows": len(missing_rows),
                "statistical_area_pending_actual_voters": sum(
                    int_value(row["actual_voters"]) for row in missing_rows
                ),
                "envelope_rows": statuses["official_envelope"],
                "special_non_geographic_rows": statuses[
                    "special_non_geographic"
                ],
                "unresolved_rows": statuses["unresolved"],
                "historical_unresolved_rows": sum(
                    statuses[status] for status in HISTORICAL_PENDING_STATUSES
                ),
            }
        )
    write_csv(
        OUT_DIR / "final_assignment_summary.csv",
        summary,
        list(summary[0].keys()) if summary else [],
    )
    write_json(OUT_DIR / "final_assignment_summary.json", summary)

    print(f"final_assignment_rows={len(output)}")
    print(f"statistical_area_pending_rows={len(missing)}")
    for row in summary:
        print(
            f"{row['election']}: mapped={row['mapped_rows']} "
            f"stat={row['stat_area_rows']} custom={row['custom_geography_rows']} "
            f"locality={row['locality_mapped_rows']} "
            f"stat_pending={row['statistical_area_pending_rows']}"
        )


if __name__ == "__main__":
    main()
