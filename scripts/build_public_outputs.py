from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline_common import ELECTIONS, PROCESSED_DIR, ensure_dir, write_csv, write_json


ASSIGNMENTS = PROCESSED_DIR / "assignments" / "ballot_geography_assignments.csv"
WIDE_DIR = PROCESSED_DIR / "normalized" / "ballot_votes_wide"
OUT_DIR = PROCESSED_DIR / "public"

CORE_COLUMNS = {
    "source_row_uid",
    "election",
    "election_number",
    "source_row_id",
    "source_order",
    "source_locality_code",
    "source_locality_name",
    "source_kalpi",
    "eligible_voters",
    "actual_voters",
    "valid_votes",
    "invalid_votes",
    "source_address",
    "is_envelope",
}
NUMERIC_CORE = ["eligible_voters", "actual_voters", "valid_votes", "invalid_votes"]


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype("int64")
    return df


def party_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in df.columns if column not in CORE_COLUMNS]


def add_winner_fields(df: pd.DataFrame, parties: list[str]) -> pd.DataFrame:
    if df.empty or not parties:
        df["winning_ballot_letter"] = ""
        df["winning_votes"] = 0
        df["runner_up_votes"] = 0
        df["margin_votes"] = 0
        df["winning_vote_share"] = 0.0
        return df

    winners = []
    winning_votes = []
    runner_up_votes = []
    for _, row in df.iterrows():
        ordered = sorted(((party, int(row[party])) for party in parties), key=lambda item: item[1], reverse=True)
        winner, votes = ordered[0]
        runner_up = ordered[1][1] if len(ordered) > 1 else 0
        winners.append(winner)
        winning_votes.append(votes)
        runner_up_votes.append(runner_up)
    df["winning_ballot_letter"] = winners
    df["winning_votes"] = winning_votes
    df["runner_up_votes"] = runner_up_votes
    df["margin_votes"] = df["winning_votes"] - df["runner_up_votes"]
    df["winning_vote_share"] = (df["winning_votes"] / df["valid_votes"].where(df["valid_votes"] != 0, pd.NA)).fillna(0).round(6)
    return df


def aggregate(df: pd.DataFrame, group_columns: list[str], parties: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=group_columns + ["contributing_rows", "contributing_kalpis"] + NUMERIC_CORE + parties)

    value_columns = NUMERIC_CORE + parties
    grouped = df.groupby(group_columns, dropna=False)
    totals = grouped[value_columns].sum().reset_index()
    totals["contributing_rows"] = grouped.size().to_numpy()
    kalpi_source = df.copy()
    kalpi_source["_kalpi_identity"] = kalpi_source[["source_locality_code", "source_kalpi"]].astype(str).agg("::".join, axis=1)
    kalpis = kalpi_source.groupby(group_columns, dropna=False)["_kalpi_identity"].nunique().reset_index(name="contributing_kalpis")
    totals = totals.merge(kalpis, on=group_columns, how="left")
    totals = add_winner_fields(totals, parties)
    leading = group_columns + [
        "contributing_rows",
        "contributing_kalpis",
        "eligible_voters",
        "actual_voters",
        "valid_votes",
        "invalid_votes",
        "winning_ballot_letter",
        "winning_votes",
        "runner_up_votes",
        "margin_votes",
        "winning_vote_share",
    ]
    return totals[leading + parties]


def write_df(df: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def read_wide(election: str) -> pd.DataFrame:
    path = WIDE_DIR / f"{election.lower()}_ballot_votes.csv"
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.parse_args()

    assignments = pd.read_csv(ASSIGNMENTS, dtype=str, encoding="utf-8-sig").fillna("")
    assignment_columns = [
        "source_row_uid",
        "geography_assignment_status",
        "geography_type",
        "geography_id",
        "stat_area_id",
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
        "address_match_status",
        "address_query",
        "unresolved_reason",
    ]

    manifest: dict[str, Any] = {"elections": [], "outputs": {}}
    summary_rows: list[dict[str, Any]] = []

    for election_number in sorted(ELECTIONS.keys(), reverse=True):
        election = ELECTIONS[election_number]["key"]
        wide = read_wide(election)
        parties = party_columns(wide)
        merged = wide.merge(assignments[assignment_columns], on="source_row_uid", how="left")
        merged = numeric(merged, NUMERIC_CORE + parties)
        mapped = bool_series(merged["is_mapped"])
        locality_mapped = bool_series(merged["is_locality_mapped"])
        stat_rows = merged[mapped & (merged["geography_type"] == "statistical_area")].copy()
        custom_rows = merged[mapped & (merged["geography_type"] == "custom_geography")].copy()
        geographic_rows = merged[mapped & bool_series(merged["is_geographic"])].copy()
        unmapped_rows = merged[~mapped].copy()
        geographic_scope_mask = ~merged["locality_geography_type"].isin(
            ["envelope", "non_geographic"]
        )
        geographic_scope = merged[geographic_scope_mask].copy()
        locality_rows = merged[
            locality_mapped
            & merged["locality_geography_type"].isin(["locality", "composite_locality"])
        ].copy()
        locality_rows["locality_id"] = locality_rows["locality_geography_id"]
        locality_rows["locality_code"] = locality_rows["locality_result_code"]
        locality_rows["locality_name"] = locality_rows["locality_result_name"]
        locality_geographic_rows = merged[locality_mapped].copy()
        locality_unmapped_rows = merged[geographic_scope_mask & ~locality_mapped].copy()
        envelope_rows = merged[
            merged["locality_geography_type"].isin(["envelope", "non_geographic"])
        ].copy()
        envelope_rows["envelope_id"] = "envelope:official"
        envelope_rows["envelope_name_he"] = "מעטפות חיצוניות"
        envelope_rows["envelope_name_en"] = "Envelope votes"

        if not locality_unmapped_rows.empty:
            unresolved = ", ".join(
                sorted(locality_unmapped_rows["source_row_uid"].astype(str).head(10).tolist())
            )
            raise ValueError(
                f"{election} has {len(locality_unmapped_rows)} geographic rows without a locality assignment: {unresolved}"
            )

        stat_agg = aggregate(
            stat_rows,
            [
                "election",
                "stat_area_id",
                "stat_area_yishuv_stat_2022",
                "stat_area_stat_2022",
                "locality_id",
                "locality_code",
                "locality_name",
            ],
            parties,
        )
        locality_agg = aggregate(
            locality_rows,
            ["election", "locality_id", "locality_code", "locality_name"],
            parties,
        )
        custom_agg = aggregate(
            custom_rows,
            ["election", "custom_geography_id", "geography_id", "locality_name"],
            parties,
        )
        envelope_agg = aggregate(
            envelope_rows,
            ["election", "envelope_id", "envelope_name_he", "envelope_name_en"],
            parties,
        )

        contribution_columns = [
            "source_row_uid",
            "election",
            "source_row_id",
            "source_locality_code",
            "source_locality_name",
            "source_kalpi",
            "geography_assignment_status",
            "geography_type",
            "geography_id",
            "stat_area_id",
            "locality_id",
            "locality_code",
            "locality_name",
            "custom_geography_id",
            "final_assignment_method",
            "final_assignment_source",
            "eligible_voters",
            "actual_voters",
            "valid_votes",
            "invalid_votes",
        ] + parties
        unmapped_columns = contribution_columns + ["address_match_status", "address_query", "unresolved_reason"]

        outputs = {
            "statistical_area_results": OUT_DIR / "statistical_area_results" / f"{election.lower()}.csv",
            "locality_results": OUT_DIR / "locality_results" / f"{election.lower()}.csv",
            "custom_geography_results": OUT_DIR / "custom_geography_results" / f"{election.lower()}.csv",
            "envelope_results": OUT_DIR / "envelope_results" / f"{election.lower()}.csv",
            "ballot_contributions": OUT_DIR / "ballot_contributions" / f"{election.lower()}.csv",
            "unmapped_rows": OUT_DIR / "unmapped_rows" / f"{election.lower()}.csv",
        }
        write_df(stat_agg, outputs["statistical_area_results"])
        write_df(locality_agg, outputs["locality_results"])
        write_df(custom_agg, outputs["custom_geography_results"])
        write_df(envelope_agg, outputs["envelope_results"])
        write_df(geographic_rows[contribution_columns], outputs["ballot_contributions"])
        write_df(unmapped_rows[unmapped_columns], outputs["unmapped_rows"])

        total_actual = int(merged["actual_voters"].sum())
        mapped_actual = int(geographic_rows["actual_voters"].sum())
        geographic_scope_actual = int(geographic_scope["actual_voters"].sum())
        locality_mapped_actual = int(locality_geographic_rows["actual_voters"].sum())
        statistical_pending = merged[geographic_scope_mask & ~mapped]
        pending = merged[
            merged["geography_assignment_status"].str.startswith("missing_geocode")
            | merged["geography_assignment_status"].str.startswith("geocoding_input_not_ready")
            | (merged["geography_assignment_status"] == "geocoded_point_outside_stat_area")
        ]
        summary_rows.append(
            {
                "election": election,
                "rows": len(merged),
                "total_actual_voters": total_actual,
                "geographic_scope_rows": len(geographic_scope),
                "geographic_scope_actual_voters": geographic_scope_actual,
                "mapped_geographic_rows": len(geographic_rows),
                "mapped_geographic_actual_voters": mapped_actual,
                "mapped_actual_voter_share": round(mapped_actual / total_actual, 6) if total_actual else 0,
                "statistical_mode_mapped_rows": len(geographic_rows),
                "statistical_mode_mapped_actual_voters": mapped_actual,
                "statistical_mode_mapped_actual_voter_share": round(
                    mapped_actual / geographic_scope_actual, 6
                )
                if geographic_scope_actual
                else 0,
                "statistical_mode_pending_rows": len(statistical_pending),
                "statistical_mode_pending_actual_voters": int(
                    statistical_pending["actual_voters"].sum()
                ),
                "locality_mode_mapped_rows": len(locality_geographic_rows),
                "locality_mode_mapped_actual_voters": locality_mapped_actual,
                "locality_mode_mapped_actual_voter_share": round(
                    locality_mapped_actual / geographic_scope_actual, 6
                )
                if geographic_scope_actual
                else 0,
                "locality_mode_pending_rows": len(locality_unmapped_rows),
                "locality_mode_pending_actual_voters": int(
                    locality_unmapped_rows["actual_voters"].sum()
                ),
                "statistical_area_rows": len(stat_rows),
                "statistical_area_actual_voters": int(stat_rows["actual_voters"].sum()),
                "custom_geography_rows": len(custom_rows),
                "custom_geography_actual_voters": int(custom_rows["actual_voters"].sum()),
                "pending_or_missing_geocode_rows": len(pending),
                "pending_or_missing_geocode_actual_voters": int(pending["actual_voters"].sum()),
                "unmapped_rows": len(unmapped_rows),
                "unmapped_actual_voters": int(unmapped_rows["actual_voters"].sum()),
                "envelope_rows": len(envelope_rows),
                "envelope_actual_voters": int(envelope_rows["actual_voters"].sum()),
                "special_non_geographic_rows": int(
                    (merged["locality_geography_type"] == "non_geographic").sum()
                ),
                "special_non_geographic_actual_voters": int(
                    merged.loc[
                        merged["locality_geography_type"] == "non_geographic", "actual_voters"
                    ].sum()
                ),
            }
        )
        manifest["elections"].append(election)
        manifest["outputs"][election] = {key: str(path.relative_to(PROCESSED_DIR.parent)).replace("\\", "/") for key, path in outputs.items()}

    write_csv(OUT_DIR / "election_summary.csv", summary_rows, list(summary_rows[0].keys()) if summary_rows else [])
    write_json(OUT_DIR / "election_summary.json", summary_rows)
    write_json(OUT_DIR / "manifest.json", manifest)

    print(f"public_output_elections={len(summary_rows)}")
    for row in summary_rows:
        print(
            f"{row['election']}: mapped_rows={row['mapped_geographic_rows']} "
            f"pending_geocode={row['pending_or_missing_geocode_rows']} "
            f"stat_share={row['statistical_mode_mapped_actual_voter_share']:.2%} "
            f"locality_share={row['locality_mode_mapped_actual_voter_share']:.2%}"
        )


if __name__ == "__main__":
    main()
