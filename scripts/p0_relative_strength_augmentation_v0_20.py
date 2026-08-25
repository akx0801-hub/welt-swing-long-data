#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCHEMA = "WELT_SWING_P0_RELATIVE_STRENGTH_AUGMENTATION_V0_20"

P0_RUN = False
VALIDATED_AUTOMATED_P0_RUN = False
AUTOMATED_P0_READY = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
EXTERNAL_REQUESTS = 0
WEB_CALLS_PER_SECURITY = False
STRICT_U3K_FROZEN = False
FULL_SCAN_CLAIM = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _peer_medians(values: pd.Series) -> pd.Series:
    """Leave-one-out median for each row; no self contribution to the reference."""
    x = pd.to_numeric(values, errors="coerce")
    out = pd.Series(index=x.index, dtype=float)
    valid_idx = x.dropna().index
    valid_vals = x.loc[valid_idx]
    for idx in valid_idx:
        peers = valid_vals.drop(index=idx)
        if len(peers) >= 1:
            out.loc[idx] = float(peers.median())
    return out


def self_test() -> None:
    d = pd.DataFrame({
        "Primary_Universe_Index": ["A", "A", "A", "B", "B"],
        "R20": [0.10, 0.20, 0.30, 0.00, 0.10],
        "R60": [0.05, 0.15, 0.25, -0.10, 0.10],
        "AsOf": ["2026-08-21", "2026-08-21", "2026-08-21", "2026-08-21", "2026-08-20"],
    })
    d["AsOf"] = pd.to_datetime(d["AsOf"])
    sync = d["AsOf"].eq(pd.Timestamp("2026-08-21"))
    x = d.loc[sync].copy()
    x["peer20"] = x.groupby("Primary_Universe_Index", group_keys=False)["R20"].apply(_peer_medians)
    # A: for 0.10 peers are 0.20,0.30 => median 0.25.
    assert abs(float(x.loc[0, "peer20"]) - 0.25) < 1e-12
    # B has only one synchronized row, therefore no peer reference.
    assert pd.isna(x.loc[3, "peer20"])
    assert P0_RUN is False and VALIDATED_AUTOMATED_P0_RUN is False
    assert ALPHA_VANTAGE_ALLOWED is False and EXTERNAL_REQUESTS == 0
    print("P0_RELATIVE_STRENGTH_AUGMENTATION_V0_20_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    summary19_path = Path(cfg["source_summary_v0_19"])
    aug19_path = Path(cfg["source_augmented_v0_19"])
    asof19_path = Path(cfg["source_asof_distribution_v0_19"])
    lanes19_path = Path(cfg["source_lane_capability_v0_19"])
    params19_path = Path(cfg["source_parameter_registry_v0_19"])
    checkpoint19_path = Path(cfg["source_checkpoint_v0_19"])

    s19 = json.loads(summary19_path.read_text(encoding="utf-8"))
    p19 = json.loads(params19_path.read_text(encoding="utf-8"))
    ck19 = json.loads(checkpoint19_path.read_text(encoding="utf-8"))

    if s19.get("run_status") != "P0_FEATURE_AUGMENTATION_V0_19_COMPLETE":
        raise SystemExit("v0.19 was not a complete augmentation")
    if int(s19.get("input_rows", -1)) != int(cfg["expected_input_rows"]):
        raise SystemExit("Unexpected v0.19 input rows")
    if int(s19.get("augmented_feature_rows", -1)) != int(cfg["expected_input_rows"]):
        raise SystemExit("Unexpected v0.19 augmented rows")
    if int(s19.get("feature_quarantine_rows", -1)) != 0:
        raise SystemExit("v0.19 still has feature quarantine rows")
    if s19.get("p0_run") is not False or s19.get("alpha_vantage_allowed") is not False:
        raise SystemExit("v0.19 governance mismatch")
    if p19.get("p0_numeric_pass_thresholds") != []:
        raise SystemExit("v0.19 unexpectedly promoted numeric P0 thresholds")
    if ck19.get("next_stage") != "P0_RELATIVE_STRENGTH_AUGMENTATION_AND_LANE_PARAMETER_VALIDATION":
        raise SystemExit("Unexpected v0.19 next stage")

    # SHA256 gate, independent of Git blob gates in workflow.
    expected_sha = cfg["expected_sha256"]
    for key, path in {
        "summary_v0_19": summary19_path,
        "augmented_v0_19": aug19_path,
        "asof_distribution_v0_19": asof19_path,
        "lane_capability_v0_19": lanes19_path,
        "parameter_registry_v0_19": params19_path,
        "checkpoint_v0_19": checkpoint19_path,
    }.items():
        if sha256_file(path) != expected_sha[key]:
            raise SystemExit(f"SHA256 mismatch for {key}")

    df = pd.read_csv(aug19_path, keep_default_na=False)
    if len(df) != int(cfg["expected_input_rows"]):
        raise SystemExit("Augmented CSV row count mismatch")
    if df["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.19 augmented input")

    for col in ["R20", "R60", "AsOf", "Primary_Universe_Index", "WS_ID", "Name"]:
        if col not in df.columns:
            raise SystemExit(f"Missing required field: {col}")

    ref = pd.Timestamp(cfg["closed_bar_reference_date"])
    parsed_asof = pd.to_datetime(df["AsOf"], errors="coerce")
    df["RS_Reference_AsOf_v0_20"] = ref.date().isoformat()
    df["RS_AsOf_Parsed_v0_20"] = parsed_asof.dt.strftime("%Y-%m-%d").fillna("")
    df["RS_AsOf_Lag_Calendar_Days_v0_20"] = (ref - parsed_asof).dt.days
    sync = parsed_asof.eq(ref)

    df["RS_AsOf_Status_v0_20"] = np.where(
        sync,
        "SYNCHRONIZED_TO_REFERENCE",
        "RS_NOT_VERIFIED_ASOF_MISMATCH",
    )

    mismatch = df.loc[~sync, [
        "WS_ID", "Name", "Country", "Primary_Universe_Index",
        "Yahoo_Symbol_v0_19", "AsOf", "RS_Reference_AsOf_v0_20",
        "RS_AsOf_Lag_Calendar_Days_v0_20", "RS_AsOf_Status_v0_20",
    ]].copy()

    expected_mismatch = set(cfg["expected_asof_mismatch_ws_ids"])
    actual_mismatch = set(mismatch["WS_ID"].astype(str))
    if actual_mismatch != expected_mismatch:
        raise SystemExit(
            f"AsOf mismatch identities changed: actual={sorted(actual_mismatch)} "
            f"expected={sorted(expected_mismatch)}"
        )

    mismatch["Audit_Conclusion_v0_20"] = "EXCLUDE_FROM_SYNCHRONIZED_RS_REFERENCE_NO_REASON_GUESSED"
    mismatch.to_csv(out/"p0_rs_asof_audit_v0.20.csv", index=False)

    # Internal primary-universe cohort RS.
    # Master permits reproducible internal peer/market groups for early discovery.
    # This is deliberately NOT labeled as an official benchmark index return.
    df["R20_num_v0_20"] = pd.to_numeric(df["R20"], errors="coerce")
    df["R60_num_v0_20"] = pd.to_numeric(df["R60"], errors="coerce")

    df["HomeMarket_Cohort_Size_Synchronized_v0_20"] = 0
    df["HomeMarket_Peer_Count_v0_20"] = 0
    df["HomeMarket_PeerMedian_R20_v0_20"] = np.nan
    df["HomeMarket_PeerMedian_R60_v0_20"] = np.nan

    sync_df = df.loc[sync].copy()

    for group_name, g in sync_df.groupby("Primary_Universe_Index", sort=True):
        idx = g.index
        n = len(g)
        df.loc[idx, "HomeMarket_Cohort_Size_Synchronized_v0_20"] = n
        df.loc[idx, "HomeMarket_Peer_Count_v0_20"] = max(0, n - 1)
        med20 = _peer_medians(g["R20_num_v0_20"])
        med60 = _peer_medians(g["R60_num_v0_20"])
        df.loc[idx, "HomeMarket_PeerMedian_R20_v0_20"] = med20
        df.loc[idx, "HomeMarket_PeerMedian_R60_v0_20"] = med60

    df["HomeMarket_RS20_Excess_v0_20"] = (
        df["R20_num_v0_20"] - df["HomeMarket_PeerMedian_R20_v0_20"]
    )
    df["HomeMarket_RS60_Excess_v0_20"] = (
        df["R60_num_v0_20"] - df["HomeMarket_PeerMedian_R60_v0_20"]
    )

    rs_available = (
        sync
        & df["HomeMarket_RS20_Excess_v0_20"].notna()
        & df["HomeMarket_RS60_Excess_v0_20"].notna()
    )
    df["HomeMarket_RS_Status_v0_20"] = np.where(
        rs_available,
        "DEV_INTERNAL_PRIMARY_UNIVERSE_COHORT_RS_AVAILABLE",
        np.where(
            ~sync,
            "RS_NOT_VERIFIED_ASOF_MISMATCH",
            "RS_NOT_VERIFIED_INSUFFICIENT_COHORT_REFERENCE",
        ),
    )
    df["HomeMarket_RS_Reference_Type_v0_20"] = np.where(
        rs_available,
        "LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN",
        "",
    )

    # "positive 20-/60-day relative strength" is an explicit master semantic.
    # It is recorded only as a component observation, never a lane PASS.
    df["Lane4_RS20_Positive_Component_v0_20"] = (
        rs_available & (df["HomeMarket_RS20_Excess_v0_20"] > 0)
    )
    df["Lane4_RS60_Positive_Component_v0_20"] = (
        rs_available & (df["HomeMarket_RS60_Excess_v0_20"] > 0)
    )
    df["Lane4_RS_Both_Positive_Component_v0_20"] = (
        df["Lane4_RS20_Positive_Component_v0_20"]
        & df["Lane4_RS60_Positive_Component_v0_20"]
    )
    df["Lane4_RS_Component_Status_v0_20"] = np.where(
        ~rs_available,
        "RS_COMPONENT_NOT_VERIFIED",
        np.where(
            df["Lane4_RS_Both_Positive_Component_v0_20"],
            "RS_COMPONENT_BOTH_POSITIVE",
            "RS_COMPONENT_NOT_BOTH_POSITIVE",
        ),
    )

    # Sector metadata is not present in the frozen v0.19 augmented input.
    df["Sector_RS_Status_v0_20"] = "RS_NOT_VERIFIED_NO_SECTOR_METADATA"
    df["Sector_RS20_Excess_v0_20"] = np.nan
    df["Sector_RS60_Excess_v0_20"] = np.nan

    df["P0_Lane_Decision_v0_20"] = "NOT_ALLOWED_PARAMETER_SET_NOT_VALIDATED"
    df["P0_PASS_v0_20"] = False
    df["P0_FAIL_v0_20"] = False

    # Save RS-augmented dataset.
    drop_helper = ["R20_num_v0_20", "R60_num_v0_20"]
    rs_out = df.drop(columns=drop_helper)
    rs_out.to_csv(out/"p0_rs_augmented_v0.20.csv", index=False)

    # Cohort reference report.
    cohort_rows = []
    for group_name, g in df.loc[sync].groupby("Primary_Universe_Index", sort=True):
        cohort_rows.append({
            "Primary_Universe_Index": group_name,
            "Synchronized_Rows": int(len(g)),
            "R20_Median_Including_Group_For_Audit": float(g["R20_num_v0_20"].median()),
            "R60_Median_Including_Group_For_Audit": float(g["R60_num_v0_20"].median()),
            "RS_Reference_Method": "LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN_PER_SECURITY",
            "Validation_Status": "DEV_EARLY_DISCOVERY_INTERNAL_MARKET_GROUP_NOT_OFFICIAL_INDEX_BENCHMARK",
        })
    cohort = pd.DataFrame(cohort_rows)
    cohort.to_csv(out/"home_market_cohort_rs_reference_v0.20.csv", index=False)

    # Segment-level sector-RS limitation.
    sector_status = (
        df.groupby("Primary_Universe_Index", sort=True)
        .size()
        .reset_index(name="Rows")
    )
    sector_status["Sector_Metadata_Status_v0_20"] = "NOT_AVAILABLE_IN_FROZEN_V0_19_INPUT"
    sector_status["Sector_RS_Status_v0_20"] = "RS_NOT_VERIFIED_NO_SECTOR_METADATA"
    sector_status.to_csv(out/"sector_rs_status_v0.20.csv", index=False)

    # Descriptive lane-parameter evidence only: no threshold promotion.
    lanes = pd.read_csv(lanes19_path, keep_default_na=False)
    evidence_rows: list[dict[str, Any]] = []
    for _, lane in lanes.iterrows():
        lane_name = str(lane["Lane"])
        fields = [x.strip() for x in str(lane["Available_Descriptive_Inputs"]).split(";") if x.strip()]
        for field in fields:
            if field not in df.columns:
                continue
            s = pd.to_numeric(df.loc[sync, field], errors="coerce").dropna()
            if s.empty:
                continue
            q = s.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
            evidence_rows.append({
                "Lane": lane_name,
                "Feature": field,
                "Rows": int(len(s)),
                "P05": float(q.loc[0.05]),
                "P25": float(q.loc[0.25]),
                "Median": float(q.loc[0.50]),
                "P75": float(q.loc[0.75]),
                "P95": float(q.loc[0.95]),
                "Evidence_Use_v0_20": "DESCRIPTIVE_ONLY_NO_THRESHOLD_PROMOTION",
            })
    # Add the newly available home-market RS fields to Lane 4 evidence.
    for field in ["HomeMarket_RS20_Excess_v0_20", "HomeMarket_RS60_Excess_v0_20"]:
        s = pd.to_numeric(df.loc[rs_available, field], errors="coerce").dropna()
        q = s.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
        evidence_rows.append({
            "Lane": "QUIET_STRENGTH_RELATIVE_STRENGTH",
            "Feature": field,
            "Rows": int(len(s)),
            "P05": float(q.loc[0.05]),
            "P25": float(q.loc[0.25]),
            "Median": float(q.loc[0.50]),
            "P75": float(q.loc[0.75]),
            "P95": float(q.loc[0.95]),
            "Evidence_Use_v0_20": "DESCRIPTIVE_ONLY_NO_THRESHOLD_PROMOTION",
        })
    evidence = pd.DataFrame(evidence_rows)
    evidence.to_csv(out/"lane_parameter_evidence_v0.20.csv", index=False)

    registry = {
        "schema": "WELT_SWING_P0_LANE_PARAMETER_REGISTRY_V0_20",
        "generated_utc": now_utc(),
        "validation_status": "PARTIAL_SEMANTIC_VALIDATION_ONLY",
        "p0_numeric_pass_thresholds": [],
        "master_semantic_conditions_recorded": [
            {
                "lane": "QUIET_STRENGTH_RELATIVE_STRENGTH",
                "condition": "HomeMarket_RS20_Excess_v0_20 > 0 AND HomeMarket_RS60_Excess_v0_20 > 0",
                "basis": "Master explicitly requests positive 20-/60-day relative strength",
                "effect": "RS_COMPONENT_ONLY_NOT_LANE_PASS",
            }
        ],
        "home_market_rs_reference": {
            "status": "DEV_INTERNAL_MARKET_GROUP_AVAILABLE_FOR_EARLY_DISCOVERY",
            "method": "LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN",
            "official_index_benchmark_claim": False,
        },
        "sector_rs": {
            "status": "RS_NOT_VERIFIED_NO_SECTOR_METADATA",
            "blocking_for_full_sector_rs_validation": True,
        },
        "remaining_unvalidated_lane_logic": {
            str(r["Lane"]): str(r["Still_Missing_or_Unvalidated"])
            for _, r in lanes.iterrows()
        },
        "policy": [
            "No descriptive quantile is promoted to a P0 PASS threshold.",
            "Positive 20/60 home-market RS is recorded only as an explicit semantic component of Lane 4.",
            "Relative strength is not an entry trigger and is not sufficient for a lane decision.",
            "AsOf-mismatched securities are fail-closed as RS_NOT_VERIFIED for synchronized cohort RS.",
            "Sector RS remains not verified until sector metadata is frozen and auditable.",
        ],
    }
    (out/"p0_lane_parameter_registry_v0.20.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "P0_RELATIVE_STRENGTH_AUGMENTATION_V0_20_COMPLETE_WITH_ASOF_EXCEPTION",
        "input_rows": int(len(df)),
        "closed_bar_reference_date": cfg["closed_bar_reference_date"],
        "asof_synchronized_rows": int(sync.sum()),
        "asof_mismatch_rows": int((~sync).sum()),
        "asof_mismatch_ws_ids": sorted(actual_mismatch),
        "home_market_rs_rows": int(rs_available.sum()),
        "home_market_rs_reference_type": "LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN",
        "home_market_rs_official_benchmark_claim": False,
        "lane4_rs_both_positive_component_rows": int(df["Lane4_RS_Both_Positive_Component_v0_20"].sum()),
        "sector_rs_rows": 0,
        "sector_rs_status": "RS_NOT_VERIFIED_NO_SECTOR_METADATA",
        "parameter_validation_status": "PARTIAL_SEMANTIC_VALIDATION_ONLY",
        "p0_numeric_pass_threshold_count": 0,
        "p0_run": P0_RUN,
        "p0_survivor_rows": 0,
        "p0_lane_decisions_made": False,
        "validated_automated_p0_run": VALIDATED_AUTOMATED_P0_RUN,
        "automated_p0_ready": AUTOMATED_P0_READY,
        "strict_u3k_frozen": STRICT_U3K_FROZEN,
        "full_scan_claim": FULL_SCAN_CLAIM,
        "research_partial_mode": True,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "external_requests": EXTERNAL_REQUESTS,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "canonical_master_mutated": False,
        "historical_v0_19_artifacts_mutated": False,
        "next_stage": "P0_LANE_PARAMETER_SHADOW_VALIDATION_AND_SECTOR_RS_PREP",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
    }
    (out/"summary_v0.20.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_20",
        "run_id": cfg["run_id"],
        "stage_id": "P0_RELATIVE_STRENGTH_AUGMENTATION_AND_LANE_PARAMETER_VALIDATION",
        "stage_version": "v0.20",
        "status": "PARTIAL",
        "input_count": int(len(df)),
        "checked_count": int(len(df)),
        "home_market_rs_count": int(rs_available.sum()),
        "rs_not_verified_count": int((~rs_available).sum()),
        "sector_rs_count": 0,
        "pass_count": 0,
        "fail_count": 0,
        "p0_survivor_count": 0,
        "validated_automated_p0_run": False,
        "automated_p0_ready": False,
        "next_stage": "P0_LANE_PARAMETER_SHADOW_VALIDATION_AND_SECTOR_RS_PREP",
    }
    (out/"stage_checkpoint_v0.20.json").write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    manifest = {
        "schema": "WELT_SWING_P0_RS_AUGMENTATION_MANIFEST_V0_20",
        "generated_utc": now_utc(),
        "external_requests": 0,
        "data_source": "FROZEN_V0_19_LOCAL_FEATURES_ONLY",
        "alpha_vantage_allowed": False,
        "files": {},
    }
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "rs_manifest_v0.20.json":
            manifest["files"][p.name] = {
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
            }
    (out/"rs_manifest_v0.20.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/p0_relative_strength_augmentation_v0.20.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
