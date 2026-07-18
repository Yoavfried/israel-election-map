from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

LOCAL_AUDIT_PYTHON = Path(__file__).resolve().parents[1] / ".local" / "python-audit"
if LOCAL_AUDIT_PYTHON.exists():
    sys.path.append(str(LOCAL_AUDIT_PYTHON))

import pandas as pd

from pipeline_common import (
    MANUAL_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    ensure_dir,
    int_value,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = RAW_DIR / "cbs_historical_geography"
ASSIGNMENTS = PROCESSED_DIR / "assignments" / "historical_ballot_assignments.csv"
HISTORICAL_OVERRIDES = MANUAL_DIR / "historical_stat_area_overrides.csv"
ARCGIS_CANDIDATES = (
    PROCESSED_DIR / "audits" / "arcgis_assignment_reconstruction_candidates.csv"
)
K23_CEC_AGS_CANDIDATES = (
    PROCESSED_DIR / "audits" / "k23_cec_ags_assignment_candidates.csv"
)
OUT_DIR = PROCESSED_DIR / "audits"

SAME_VINTAGE_EDGES = [
    ("K19", "K20", "stable_ballots_k20.xls"),
    ("K20", "K21", "stable_ballots_k21.xlsx"),
    ("K20", "K22", "stable_ballots_k22.xlsx"),
    ("K22", "K23", "stable_ballots_k23.xlsx"),
    ("K23", "K24", "stable_ballots_k24.xlsx"),
    ("K24", "K25", "stable_ballots_k25.xlsx"),
]
TRANSITION_EDGE = ("K18", "K19", "stable_ballots_k19.xlsx")

TRANSITION_COLUMNS = [
    "locality_code",
    "ballot",
    "source_2008_areas",
    "source_2011_areas",
    "transition_2011_targets",
    "transition_2008_targets",
    "status",
    "source",
]
COMPONENT_COLUMNS = [
    "locality_code",
    "ballot",
    "component_elections",
    "known_area_ids",
    "known_assignment_evidence",
    "source_workbooks",
    "status",
    "candidate_rows",
    "candidate_actual_voters",
]
CONFLICT_COLUMNS = [
    "conflict_type",
    "locality_code",
    "ballot",
    "elections",
    "known_area_ids",
    "source_workbooks",
    "reason",
]
CANDIDATE_COLUMNS = [
    "source_row_uid",
    "election",
    "source_locality_code",
    "source_locality_name",
    "source_kalpi",
    "actual_voters",
    "candidate_stat_area_id",
    "evidence_method",
    "evidence_elections",
    "source_workbooks",
    "known_assignment_evidence",
]


def normalize_number(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    try:
        return format(Decimal(text).normalize(), "f")
    except InvalidOperation:
        return text


def bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_stable_keys(filename: str) -> set[tuple[str, str]]:
    path = SOURCE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing official CBS stable-ballot workbook: {path}")
    raw = pd.read_excel(path, sheet_name=1, header=None, dtype=str).fillna("")
    header_index = None
    code_column = None
    ballot_column = None
    for index, row in raw.iterrows():
        values = [str(value).strip() for value in row]
        candidate_code = next(
            (
                position
                for position, value in enumerate(values)
                if value.startswith("סמל יישוב") or value.startswith("סמל ישוב")
            ),
            None,
        )
        candidate_ballot = next(
            (
                position
                for position, value in enumerate(values)
                if value.startswith("מספר קלפי")
            ),
            None,
        )
        if candidate_code is not None and candidate_ballot is not None:
            header_index = index
            code_column = candidate_code
            ballot_column = candidate_ballot
            break
    if header_index is None or code_column is None or ballot_column is None:
        raise ValueError(f"Cannot find stable-ballot columns in {path.name}")

    keys = {
        (normalize_number(row.iloc[code_column]), normalize_number(row.iloc[ballot_column]))
        for _, row in raw.iloc[header_index + 1 :].iterrows()
    }
    keys.discard(("", ""))
    return {(code, ballot) for code, ballot in keys if code and ballot}


def load_aliases(vintage: int) -> dict[int, str]:
    path = (
        PROCESSED_DIR
        / "geographies"
        / f"statistical_areas_{vintage}.aliases.csv"
    )
    rows = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    return {
        int_value(row["source_yishuv_stat"]): row["canonical_stat_area_id"]
        for _, row in rows.iterrows()
    }


def load_transition_maps() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    path = SOURCE_DIR / "statistical_area_2008_to_2011.xlsx"
    raw = pd.read_excel(path, sheet_name=1, header=0, dtype=str).fillna("")
    aliases_2008 = load_aliases(2008)
    aliases_2011 = load_aliases(2011)
    forward: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    for _, row in raw.iterrows():
        source_code = int_value(row.get("YISHUV_STAT2008"))
        target_code = int_value(row.get("YISHUV_STAT2011"))
        if not source_code or not target_code:
            continue
        source = aliases_2008.get(source_code, f"stat2008:{source_code}")
        target = aliases_2011.get(target_code, f"stat2011:{target_code}")
        forward[source].add(target)
        reverse[target].add(source)
    return dict(forward), dict(reverse)


def assignment_fingerprint(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(
        f"{row['source_row_uid']}|{row['candidate_stat_area_id']}"
        for row in sorted(rows, key=lambda item: item["source_row_uid"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_frame(frame: pd.DataFrame, filename: str) -> None:
    ensure_dir(OUT_DIR)
    frame.to_csv(OUT_DIR / filename, index=False, encoding="utf-8-sig")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = pd.read_csv(ASSIGNMENTS, dtype=str, encoding="utf-8-sig").fillna("")
    rows["key_code"] = rows["source_locality_code"].map(normalize_number)
    # The official stable-ballot workbooks identify the base polling register.
    # Later result files may publish that register as 14.1, 14.2, etc.; all
    # subdivisions inherit the same geographic boundary and must share one node.
    rows["key_ballot"] = rows["ballot_base"].map(normalize_number)
    rows["is_officially_mapped"] = rows["is_historical_stat_mapped"].map(
        bool_value
    )

    overrides = pd.read_csv(
        HISTORICAL_OVERRIDES, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    if overrides.empty or overrides["source_row_uid"].duplicated().any():
        raise ValueError("Historical override table is empty or contains duplicates")
    override_by_uid = {
        row["source_row_uid"]: row.to_dict() for _, row in overrides.iterrows()
    }

    arcgis = pd.read_csv(
        ARCGIS_CANDIDATES, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    arcgis = arcgis[arcgis["assignment_applied"].map(bool_value)].copy()
    if arcgis["source_row_uid"].duplicated().any():
        raise ValueError("Approved ArcGIS candidates contain duplicate row IDs")
    arcgis_by_uid = {
        row["source_row_uid"]: row.to_dict() for _, row in arcgis.iterrows()
    }

    k23_cec = pd.read_csv(
        K23_CEC_AGS_CANDIDATES, dtype=str, encoding="utf-8-sig"
    ).fillna("")
    if k23_cec["source_row_uid"].duplicated().any():
        raise ValueError("K23 CEC AGS candidates contain duplicate row IDs")
    if not k23_cec["evidence_method"].eq("official_cec_k23_ags").all():
        raise ValueError("K23 CEC AGS candidates contain an unsupported method")
    k23_cec_by_uid = {
        row["source_row_uid"]: row.to_dict() for _, row in k23_cec.iterrows()
    }

    node_rows: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    official_areas: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    arcgis_areas: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    arcgis_tiers: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    k23_cec_areas: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    override_nodes: set[tuple[str, str, str]] = set()
    for index, row in rows.iterrows():
        key = (row["election"], row["key_code"], row["key_ballot"])
        if not row["key_code"] or not row["key_ballot"]:
            continue
        node_rows[key].append(index)
        override = override_by_uid.get(row["source_row_uid"])
        if override:
            if not row["is_officially_mapped"]:
                raise ValueError(
                    f"Historical override does not replace a direct assignment: "
                    f"{row['source_row_uid']}"
                )
            expected = (
                row["election"],
                row["key_code"],
                row["key_ballot"],
            )
            observed = (
                override["election"],
                normalize_number(override["source_locality_code"]),
                normalize_number(override["source_kalpi"]),
            )
            if observed != expected:
                raise ValueError(
                    f"Historical override source identity changed: "
                    f"{row['source_row_uid']}"
                )
            if (
                override["evidence_status"]
                != "reviewed_exact_stable_conflict_resolution"
                or int_value(override["stat_area_vintage"]) != 2011
                or not override["target_stat_area_id"].startswith("stat2011:")
            ):
                raise ValueError(
                    f"Unsupported historical override: {row['source_row_uid']}"
                )
            official_areas[key].add(override["target_stat_area_id"])
            override_nodes.add(key)
        elif row["is_officially_mapped"] and row["stat_area_id"]:
            official_areas[key].add(row["stat_area_id"])
        candidate = arcgis_by_uid.get(row["source_row_uid"])
        if candidate:
            arcgis_areas[key].add(candidate["candidate_stat_area_id"])
            arcgis_tiers[key].add(candidate["evidence_tier"])
        k23_candidate = k23_cec_by_uid.get(row["source_row_uid"])
        if k23_candidate:
            k23_cec_areas[key].add(k23_candidate["candidate_stat_area_id"])

    for key in official_areas.keys() | arcgis_areas.keys() | k23_cec_areas.keys():
        areas = (
            official_areas.get(key, set())
            | arcgis_areas.get(key, set())
            | k23_cec_areas.get(key, set())
        )
        if len(areas) > 1:
            raise ValueError(f"One election ballot key maps to multiple areas: {key}")

    transition_keys = read_stable_keys(TRANSITION_EDGE[2])
    forward, reverse = load_transition_maps()
    transition_candidates: dict[tuple[str, str, str], str] = {}
    transition_reports: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for code, ballot in sorted(transition_keys):
        key_2008 = ("K18", code, ballot)
        key_2011 = ("K19", code, ballot)
        if key_2008 not in node_rows or key_2011 not in node_rows:
            continue
        areas_2008 = official_areas.get(key_2008, set())
        areas_2011 = official_areas.get(key_2011, set())
        proposed_2011 = (
            set().union(*(forward.get(area, set()) for area in areas_2008))
            if areas_2008
            else set()
        )
        proposed_2008 = (
            set().union(*(reverse.get(area, set()) for area in areas_2011))
            if areas_2011
            else set()
        )
        status = "no_unique_transition"
        if areas_2008 and areas_2011:
            status = (
                "validated_existing_transition"
                if proposed_2011 == areas_2011 and proposed_2008 == areas_2008
                else "existing_transition_conflict"
            )
        elif len(proposed_2011) == 1:
            transition_candidates[key_2011] = next(iter(proposed_2011))
            status = "candidate_2011_from_2008"
        elif len(proposed_2008) == 1:
            transition_candidates[key_2008] = next(iter(proposed_2008))
            status = "candidate_2008_from_2011"
        transition_reports.append(
            {
                "locality_code": code,
                "ballot": ballot,
                "source_2008_areas": "|".join(sorted(areas_2008)),
                "source_2011_areas": "|".join(sorted(areas_2011)),
                "transition_2011_targets": "|".join(sorted(proposed_2011)),
                "transition_2008_targets": "|".join(sorted(proposed_2008)),
                "status": status,
                "source": TRANSITION_EDGE[2],
            }
        )
        if status == "existing_transition_conflict":
            conflicts.append(
                {
                    "conflict_type": "2008_2011_transition",
                    "locality_code": code,
                    "ballot": ballot,
                    "elections": "K18|K19",
                    "known_area_ids": "|".join(sorted(areas_2008 | areas_2011)),
                    "source_workbooks": TRANSITION_EDGE[2],
                    "reason": "Stable ballot has incompatible known areas under the official transition table",
                }
            )

    adjacency: dict[tuple[str, str, str], set[tuple[str, str, str]]] = defaultdict(set)
    edge_sources: dict[
        frozenset[tuple[str, str, str]], set[str]
    ] = defaultdict(set)
    available_sources = [TRANSITION_EDGE[2]]
    missing_sources: list[str] = []
    for left, right, filename in SAME_VINTAGE_EDGES:
        if not (SOURCE_DIR / filename).exists():
            missing_sources.append(filename)
            continue
        available_sources.append(filename)
        for code, ballot in read_stable_keys(filename):
            left_key = (left, code, ballot)
            right_key = (right, code, ballot)
            if left_key not in node_rows or right_key not in node_rows:
                continue
            adjacency[left_key].add(right_key)
            adjacency[right_key].add(left_key)
            edge_sources[frozenset((left_key, right_key))].add(filename)

    candidates: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for start in sorted(adjacency):
        if start in seen:
            continue
        stack = [start]
        component: list[tuple[str, str, str]] = []
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            component.append(node)
            stack.extend(adjacency[node] - seen)

        known: dict[str, list[str]] = defaultdict(list)
        authoritative_methods: set[str] = set()
        for node in component:
            for area in official_areas.get(node, set()):
                if node in override_nodes:
                    known[area].append(f"{node[0]}:reviewed_historical_override")
                    authoritative_methods.add("reviewed_historical_override")
                else:
                    known[area].append(f"{node[0]}:official")
                    authoritative_methods.add("official_historical_assignment")
            for area in arcgis_areas.get(node, set()):
                tiers = "+".join(sorted(arcgis_tiers.get(node, set())))
                known[area].append(f"{node[0]}:reviewed_arcgis_tier_{tiers}")
                authoritative_methods.add("reviewed_arcgis_residual_partition")
            for area in k23_cec_areas.get(node, set()):
                known[area].append(f"{node[0]}:official_cec_ags")
                authoritative_methods.add("official_cec_k23_ags")
            if node in transition_candidates:
                known[transition_candidates[node]].append(f"{node[0]}:transition")
                authoritative_methods.add("official_stable_transition")

        component_sources: set[str] = set()
        component_set = set(component)
        for node in component:
            for neighbor in adjacency[node] & component_set:
                component_sources.update(edge_sources[frozenset((node, neighbor))])

        status = "no_known_assignment"
        target_area = ""
        if len(known) > 1:
            status = "conflicting_known_assignments"
            code, ballot = start[1], start[2]
            conflicts.append(
                {
                    "conflict_type": "same_vintage_stable_component",
                    "locality_code": code,
                    "ballot": ballot,
                    "elections": "|".join(sorted(node[0] for node in component)),
                    "known_area_ids": "|".join(sorted(known)),
                    "source_workbooks": "|".join(sorted(component_sources)),
                    "reason": "Officially stable ballot component contains incompatible known 2011 areas",
                }
            )
        elif len(known) == 1 and authoritative_methods:
            target_area = next(iter(known))
            status = "unanimous_known_assignment"

        component_candidates = 0
        component_voters = 0
        if status == "unanimous_known_assignment":
            for node in component:
                for row_index in node_rows[node]:
                    row = rows.loc[row_index]
                    if row["is_officially_mapped"]:
                        continue
                    if row["source_row_uid"] in arcgis_by_uid:
                        continue
                    if row["source_row_uid"] in k23_cec_by_uid:
                        continue
                    if node in transition_candidates and node[0] == "K19":
                        method = "cbs_stable_ballot_transition_2008_2011"
                    elif "official_stable_transition" in authoritative_methods:
                        method = "cbs_stable_ballot_transition_chain"
                    elif authoritative_methods == {
                        "reviewed_arcgis_residual_partition"
                    }:
                        method = "cbs_stable_ballot_from_reviewed_arcgis"
                    elif authoritative_methods == {"official_cec_k23_ags"}:
                        method = "cbs_stable_ballot_from_official_cec_ags"
                    elif sum(len(values) for values in known.values()) > 1:
                        method = "cbs_stable_ballot_cross_election_consensus"
                    else:
                        method = "cbs_stable_ballot_cross_election_carry"
                    candidates.append(
                        {
                            "source_row_uid": row["source_row_uid"],
                            "election": row["election"],
                            "source_locality_code": row["source_locality_code"],
                            "source_locality_name": row["source_locality_name"],
                            "source_kalpi": row["source_kalpi"],
                            "actual_voters": int_value(row["actual_voters"]),
                            "candidate_stat_area_id": target_area,
                            "evidence_method": method,
                            "evidence_elections": "|".join(
                                sorted({value.split(":", 1)[0] for values in known.values() for value in values})
                            ),
                            "source_workbooks": "|".join(sorted(component_sources)),
                            "known_assignment_evidence": "|".join(
                                sorted(value for values in known.values() for value in values)
                            ),
                        }
                    )
                    component_candidates += 1
                    component_voters += int_value(row["actual_voters"])

        components.append(
            {
                "locality_code": start[1],
                "ballot": start[2],
                "component_elections": "|".join(sorted(node[0] for node in component)),
                "known_area_ids": "|".join(sorted(known)),
                "known_assignment_evidence": "|".join(
                    sorted(value for values in known.values() for value in values)
                ),
                "source_workbooks": "|".join(sorted(component_sources)),
                "status": status,
                "candidate_rows": component_candidates,
                "candidate_actual_voters": component_voters,
            }
        )

    existing_candidate_uids = {row["source_row_uid"] for row in candidates}
    for node, target_area in transition_candidates.items():
        for row_index in node_rows[node]:
            row = rows.loc[row_index]
            if row["is_officially_mapped"]:
                continue
            if row["source_row_uid"] in arcgis_by_uid:
                continue
            if row["source_row_uid"] in k23_cec_by_uid:
                continue
            if row["source_row_uid"] in existing_candidate_uids:
                continue
            source_election = "K19" if node[0] == "K18" else "K18"
            candidates.append(
                {
                    "source_row_uid": row["source_row_uid"],
                    "election": row["election"],
                    "source_locality_code": row["source_locality_code"],
                    "source_locality_name": row["source_locality_name"],
                    "source_kalpi": row["source_kalpi"],
                    "actual_voters": int_value(row["actual_voters"]),
                    "candidate_stat_area_id": target_area,
                    "evidence_method": (
                        "cbs_stable_ballot_transition_2011_2008"
                        if node[0] == "K18"
                        else "cbs_stable_ballot_transition_2008_2011"
                    ),
                    "evidence_elections": source_election,
                    "source_workbooks": TRANSITION_EDGE[2],
                    "known_assignment_evidence": f"{source_election}:official",
                }
            )
            existing_candidate_uids.add(row["source_row_uid"])

    candidate_uids = [row["source_row_uid"] for row in candidates]
    if len(candidate_uids) != len(set(candidate_uids)):
        duplicates = sorted(
            uid for uid in set(candidate_uids) if candidate_uids.count(uid) > 1
        )
        raise ValueError(f"Stable-ballot audit produced duplicate candidates: {duplicates[:10]}")

    candidates.sort(key=lambda row: row["source_row_uid"])
    transition_frame = pd.DataFrame(transition_reports, columns=TRANSITION_COLUMNS)
    component_frame = pd.DataFrame(components, columns=COMPONENT_COLUMNS)
    conflict_frame = pd.DataFrame(conflicts, columns=CONFLICT_COLUMNS)
    candidate_frame = pd.DataFrame(candidates, columns=CANDIDATE_COLUMNS)
    write_frame(
        transition_frame,
        "stable_ballot_transition_audit.csv",
    )
    write_frame(component_frame, "stable_ballot_assignment_components.csv")
    write_frame(conflict_frame, "stable_ballot_assignment_conflicts.csv")
    write_frame(candidate_frame, "stable_ballot_assignment_candidates.csv")

    summary = {
        "status": "complete" if not missing_sources else "partial_missing_sources",
        "source": "official_cbs_stable_ballot_workbooks",
        "ballot_key": "historical_ballot_base_including_decimal_subdivisions",
        "available_source_workbooks": available_sources,
        "missing_source_workbooks": missing_sources,
        "candidate_rows": len(candidates),
        "candidate_actual_voters": sum(
            int_value(row["actual_voters"]) for row in candidates
        ),
        "candidate_assignment_sha256": assignment_fingerprint(candidates),
        "same_vintage_components": len(components),
        "same_vintage_conflicts": sum(
            row["status"] == "conflicting_known_assignments" for row in components
        ),
        "transition_conflicts": sum(
            row["status"] == "existing_transition_conflict"
            for row in transition_reports
        ),
        "by_election": {
            election: {
                "candidate_rows": sum(row["election"] == election for row in candidates),
                "candidate_actual_voters": sum(
                    int_value(row["actual_voters"])
                    for row in candidates
                    if row["election"] == election
                ),
            }
            for election in [f"K{number}" for number in range(17, 26)]
        },
    }
    write_json(OUT_DIR / "stable_ballot_assignment_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
