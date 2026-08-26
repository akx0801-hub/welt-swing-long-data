#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

SCHEMA = "WELT_SWING_P0_LANE_PARAMETER_SHADOW_VALIDATION_V0_21"
P0_RUN = False
P0_LANE_DECISIONS_MADE = False
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(np.nan, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce")


def detect_sector_metadata_columns(columns: list[str]) -> list[str]:
    """Detect raw sector/industry taxonomy fields, excluding generated Sector-RS outputs."""
    found: list[str] = []
    for c in columns:
        low = c.lower()
        if low.startswith("sector_rs") or "_sector_rs" in low:
            continue
        if low in {"sector", "sector_name", "sector_code", "industry", "industry_name", "industry_code"}:
            found.append(c)
            continue
        if low.startswith(("gics_", "icb_", "naics_", "trbc_")):
            found.append(c)
            continue
        if low.endswith(("_sector", "_sector_name", "_sector_code", "_industry", "_industry_name", "_industry_code")):
            found.append(c)
    return sorted(set(found))


def combine_file_hashes(paths: dict[str, Path]) -> str:
    parts = [f"{key}:{sha256_file(path)}" for key, path in sorted(paths.items())]
    return sha256_text("\n".join(parts))


def component(
    obs: pd.DataFrame,
    name: str,
    predicate: pd.Series,
    required: list[pd.Series],
    asof_sync: pd.Series,
    additional_verified: pd.Series | None = None,
) -> None:
    verified = asof_sync.copy()
    for series in required:
        verified &= series.notna()
    if additional_verified is not None:
        verified &= additional_verified

    value_col = f"Shadow_{name}_v0_21"
    status_col = f"Shadow_{name}_Status_v0_21"
    obs[value_col] = False
    obs.loc[verified, value_col] = predicate.loc[verified].astype(bool)
    obs[status_col] = "NOT_VERIFIED_MISSING_INPUT"
    obs.loc[~asof_sync, status_col] = "NOT_VERIFIED_ASOF_MISMATCH"
    obs.loc[verified & predicate, status_col] = "VERIFIED_TRUE"
    obs.loc[verified & ~predicate, status_col] = "VERIFIED_FALSE"


def self_test() -> None:
    cols = [
        "WS_ID", "Sector_RS_Status_v0_20", "Sector_RS20_Excess_v0_20",
        "GICS_Sector", "Industry_Name", "R20",
    ]
    found = detect_sector_metadata_columns(cols)
    assert "GICS_Sector" in found and "Industry_Name" in found
    assert "Sector_RS_Status_v0_20" not in found
    assert "Sector_RS20_Excess_v0_20" not in found

    d = pd.DataFrame({"x": [2.0, 1.0, np.nan], "y": [1.0, 2.0, 1.0]})
    obs = pd.DataFrame(index=d.index)
    sync = pd.Series([True, True, False], index=d.index)
    component(obs, "TEST", d["x"] > d["y"], [d["x"], d["y"]], sync)
    assert obs["Shadow_TEST_v0_21"].tolist() == [True, False, False]
    assert obs["Shadow_TEST_Status_v0_21"].tolist() == [
        "VERIFIED_TRUE", "VERIFIED_FALSE", "NOT_VERIFIED_ASOF_MISMATCH"
    ]
    assert P0_RUN is False and P0_LANE_DECISIONS_MADE is False
    assert ALPHA_VANTAGE_ALLOWED is False and EXTERNAL_REQUESTS == 0
    print("P0_LANE_PARAMETER_SHADOW_VALIDATION_V0_21_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    started_utc = now_utc()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "summary": Path(cfg["source_summary_v0_20"]),
        "rs_augmented": Path(cfg["source_rs_augmented_v0_20"]),
        "asof_audit": Path(cfg["source_asof_audit_v0_20"]),
        "registry": Path(cfg["source_parameter_registry_v0_20"]),
        "sector_status": Path(cfg["source_sector_status_v0_20"]),
        "checkpoint": Path(cfg["source_checkpoint_v0_20"]),
        "manifest": Path(cfg["source_manifest_v0_20"]),
    }
    for key, p in paths.items():
        if not p.exists():
            raise SystemExit(f"Missing frozen v0.20 input {key}: {p}")

    s20 = json.loads(paths["summary"].read_text(encoding="utf-8"))
    r20 = json.loads(paths["registry"].read_text(encoding="utf-8"))
    ck20 = json.loads(paths["checkpoint"].read_text(encoding="utf-8"))
    m20 = json.loads(paths["manifest"].read_text(encoding="utf-8"))

    if s20.get("run_status") != "P0_RELATIVE_STRENGTH_AUGMENTATION_V0_20_COMPLETE_WITH_ASOF_EXCEPTION":
        raise SystemExit("Unexpected v0.20 run status")
    if int(s20.get("input_rows", -1)) != int(cfg["expected_input_rows"]):
        raise SystemExit("Unexpected v0.20 input count")
    if int(s20.get("asof_synchronized_rows", -1)) != 2036:
        raise SystemExit("Unexpected synchronized AsOf count")
    if s20.get("asof_mismatch_ws_ids") != ["WS:US:WBS"]:
        raise SystemExit("Unexpected v0.20 AsOf exception")
    if int(s20.get("home_market_rs_rows", -1)) != 2036:
        raise SystemExit("Unexpected Home-Market-RS count")
    if int(s20.get("lane4_rs_both_positive_component_rows", -1)) != int(cfg["expected_lane4_rs_both_positive_rows"]):
        raise SystemExit("Unexpected Lane-4 positive-RS component count")
    if int(s20.get("sector_rs_rows", -1)) != 0:
        raise SystemExit("Sector RS unexpectedly available")
    if s20.get("p0_run") is not False or s20.get("p0_lane_decisions_made") is not False:
        raise SystemExit("v0.20 governance mismatch")
    if s20.get("alpha_vantage_allowed") is not False:
        raise SystemExit("Alpha Vantage governance mismatch")
    if r20.get("p0_numeric_pass_thresholds") != []:
        raise SystemExit("v0.20 unexpectedly has numeric P0 pass thresholds")
    if ck20.get("next_stage") != "P0_LANE_PARAMETER_SHADOW_VALIDATION_AND_SECTOR_RS_PREP":
        raise SystemExit("Unexpected v0.20 next stage")
    if m20.get("external_requests") != 0 or m20.get("alpha_vantage_allowed") is not False:
        raise SystemExit("Unexpected v0.20 manifest governance")

    for key, p in paths.items():
        expected = cfg["expected_sha256"].get(key)
        if expected is not None:
            actual = sha256_file(p)
            if actual != expected:
                raise SystemExit(f"SHA256 mismatch for {key}: {actual} != {expected}")

    df = pd.read_csv(paths["rs_augmented"], keep_default_na=False)
    if len(df) != int(cfg["expected_input_rows"]):
        raise SystemExit("RS-augmented row count mismatch")
    if df["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.20 RS input")

    audit = pd.read_csv(paths["asof_audit"], keep_default_na=False)
    if len(audit) != 1 or str(audit.iloc[0]["WS_ID"]) != "WS:US:WBS":
        raise SystemExit("AsOf audit no longer matches frozen v0.20 evidence")

    asof_sync = df["RS_AsOf_Status_v0_20"].astype(str).eq("SYNCHRONIZED_TO_REFERENCE")
    if int(asof_sync.sum()) != 2036:
        raise SystemExit("Synchronized feature rows changed")
    mismatch_ids = df.loc[~asof_sync, "WS_ID"].astype(str).tolist()
    if mismatch_ids != ["WS:US:WBS"]:
        raise SystemExit(f"Unexpected fail-closed AsOf identities: {mismatch_ids}")

    sector_metadata_cols = detect_sector_metadata_columns(list(df.columns))
    inventory = pd.DataFrame([{
        "Input_File": cfg["source_rs_augmented_v0_20"],
        "Rows": len(df),
        "Detected_Raw_Sector_Metadata_Column_Count": len(sector_metadata_cols),
        "Detected_Raw_Sector_Metadata_Columns": ";".join(sector_metadata_cols),
        "Sector_Metadata_Usable_v0_21": len(sector_metadata_cols) > 0,
        "Sector_RS_Status_v0_21": (
            "SECTOR_METADATA_PRESENT_REQUIRES_MAPPING_VALIDATION"
            if sector_metadata_cols else "RS_NOT_VERIFIED_NO_FROZEN_SECTOR_METADATA"
        ),
    }])
    inventory.to_csv(out / "sector_metadata_inventory_v0.21.csv", index=False)
    if sector_metadata_cols:
        raise SystemExit(
            "Unexpected raw sector metadata appeared in frozen v0.20 input; "
            "requires separate mapping validation before sector RS."
        )

    contract = {
        "schema": "WELT_SWING_SECTOR_METADATA_CONTRACT_V0_21",
        "generated_utc": now_utc(),
        "status": "PREPARED_NOT_POPULATED",
        "required_identity_key": "WS_ID",
        "required_fields": [
            "WS_ID", "Sector_Taxonomy", "Sector_Code", "Sector_Name",
            "Source_Name", "Source_Reference", "Source_Version_or_AsOf", "Mapping_Status",
        ],
        "accepted_source_classes": [
            "official index administrator bulk constituent/reference data",
            "official primary exchange bulk reference data",
            "official security registry bulk reference data",
            "other explicitly approved bulk reference source after provenance review",
        ],
        "prohibited_methods": [
            "per-security web lookup fanout",
            "name-based guessed sector mapping",
            "silent taxonomy mixing without crosswalk",
            "unversioned sector labels",
            "Alpha Vantage",
        ],
        "mapping_requirements": [
            "deterministic WS_ID linkage",
            "taxonomy and source provenance recorded",
            "as-of/version recorded",
            "ambiguous mappings fail closed",
            "sector peer group must be large enough for a reliable reference or RS_NOT_VERIFIED",
        ],
        "current_frozen_input_sector_metadata_columns": sector_metadata_cols,
        "sector_rs_ready": False,
    }
    (out / "sector_metadata_contract_v0.21.json").write_text(
        json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    close = numeric(df, "Close_Tech")
    ema20 = numeric(df, "EMA20")
    ema50 = numeric(df, "EMA50")
    sma200 = numeric(df, "SMA200")
    ema20s = numeric(df, "EMA20_Slope5_Pct")
    ema50s = numeric(df, "EMA50_Slope10_Pct")
    r20abs = numeric(df, "R20")
    r60abs = numeric(df, "R60")
    range_ratio = numeric(df, "Range5_to_Range20")
    tr_ratio = numeric(df, "TR_Mean5_to_20")
    recent_low = numeric(df, "RecentLow10_vs_Prior10_Pct")
    post_min = numeric(df, "PostImpulse_Min_vs_ImpulseClose")
    post_latest = numeric(df, "PostImpulse_Latest_vs_ImpulseClose")
    rs20 = numeric(df, "HomeMarket_RS20_Excess_v0_20")
    rs60 = numeric(df, "HomeMarket_RS60_Excess_v0_20")
    rs_verified = df["HomeMarket_RS_Status_v0_20"].astype(str).eq(
        "DEV_INTERNAL_PRIMARY_UNIVERSE_COHORT_RS_AVAILABLE"
    )

    obs = pd.DataFrame({
        "WS_ID": df["WS_ID"].astype(str),
        "Name": df["Name"].astype(str),
        "Primary_Universe_Index": df["Primary_Universe_Index"].astype(str),
        "AsOf": df["AsOf"].astype(str),
        "RS_AsOf_Status_v0_20": df["RS_AsOf_Status_v0_20"].astype(str),
    })

    component(obs, "Close_Above_EMA20", close > ema20, [close, ema20], asof_sync)
    component(obs, "Close_Above_EMA50", close > ema50, [close, ema50], asof_sync)
    component(obs, "Close_Above_SMA200", close > sma200, [close, sma200], asof_sync)
    component(obs, "EMA20_Slope_Positive", ema20s > 0, [ema20s], asof_sync)
    component(obs, "EMA50_Slope_Positive", ema50s > 0, [ema50s], asof_sync)
    component(obs, "R20_Absolute_Positive", r20abs > 0, [r20abs], asof_sync)
    component(obs, "R60_Absolute_Positive", r60abs > 0, [r60abs], asof_sync)
    component(obs, "Range5_Narrower_Than_Range20", range_ratio < 1.0, [range_ratio], asof_sync)
    component(obs, "TRMean5_Lower_Than_TRMean20", tr_ratio < 1.0, [tr_ratio], asof_sync)
    component(obs, "HigherLow10_Proxy", recent_low > 0, [recent_low], asof_sync)
    component(obs, "PostImpulse_Held_ImpulseClose", post_min >= 0, [post_min], asof_sync)
    component(obs, "PostImpulse_Latest_Above_ImpulseClose", post_latest > 0, [post_latest], asof_sync)
    component(obs, "HomeMarket_RS20_Positive", rs20 > 0, [rs20], asof_sync, rs_verified)
    component(obs, "HomeMarket_RS60_Positive", rs60 > 0, [rs60], asof_sync, rs_verified)
    component(
        obs, "HomeMarket_RS_Both_Positive", (rs20 > 0) & (rs60 > 0),
        [rs20, rs60], asof_sync, rs_verified,
    )

    obs["P0_Shadow_Lane_Decision_v0_21"] = "NOT_ALLOWED_COMPONENT_EVIDENCE_ONLY"
    obs["P0_PASS_v0_21"] = False
    obs["P0_FAIL_v0_21"] = False
    obs.to_csv(out / "p0_shadow_component_observations_v0.21.csv", index=False)

    component_cols = [
        c for c in obs.columns
        if c.startswith("Shadow_") and not c.endswith("_Status_v0_21")
    ]
    counts: list[dict[str, Any]] = []
    for c in component_cols:
        status_col = c.replace("_v0_21", "_Status_v0_21")
        status = obs[status_col].astype(str)
        counts.append({
            "Component": c,
            "Verified_True_Rows": int(status.eq("VERIFIED_TRUE").sum()),
            "Verified_False_Rows": int(status.eq("VERIFIED_FALSE").sum()),
            "Not_Verified_Rows": int(status.str.startswith("NOT_VERIFIED").sum()),
            "AsOf_Mismatch_Rows": int(status.eq("NOT_VERIFIED_ASOF_MISMATCH").sum()),
            "Missing_Input_Rows": int(status.eq("NOT_VERIFIED_MISSING_INPUT").sum()),
            "Input_Rows": int(len(obs)),
            "Use_v0_21": "SHADOW_EVIDENCE_ONLY_NOT_LANE_PASS",
        })
    pd.DataFrame(counts).to_csv(out / "p0_shadow_component_counts_v0.21.csv", index=False)

    lane_matrix = pd.DataFrame([
        {
            "Lane": "BREAKOUT_COMPRESSION_VCP",
            "Semantically_Measurable_Components_v0_21": "Range5<Range20 relation; TRMean5<TRMean20 relation; close/EMA/SMA context; High20/High60/High252 distances available",
            "Still_Unvalidated_or_Missing_v0_21": "pivot/base/VCP detector; breakout pivot identity; validated lane thresholds",
            "Shadow_Validation_Status_v0_21": "COMPONENT_EVIDENCE_ONLY",
            "Automated_P0_Decision_v0_21": "NOT_ALLOWED",
        },
        {
            "Lane": "PULLBACK_RETEST",
            "Semantically_Measurable_Components_v0_21": "higher-low proxy; close/EMA/SMA context; ATR distances to recent lows",
            "Still_Unvalidated_or_Missing_v0_21": "former-breakout-zone detector; horizontal-support identity; validated controlled-pullback sequence",
            "Shadow_Validation_Status_v0_21": "COMPONENT_EVIDENCE_ONLY",
            "Automated_P0_Decision_v0_21": "NOT_ALLOWED",
        },
        {
            "Lane": "RECLAIM",
            "Semantically_Measurable_Components_v0_21": "cross timing fields; close/EMA context; higher-low proxy",
            "Still_Unvalidated_or_Missing_v0_21": "validated recency definition; multi-day reclaim/confirmation rule",
            "Shadow_Validation_Status_v0_21": "COMPONENT_EVIDENCE_ONLY",
            "Automated_P0_Decision_v0_21": "NOT_ALLOWED",
        },
        {
            "Lane": "QUIET_STRENGTH_RELATIVE_STRENGTH",
            "Semantically_Measurable_Components_v0_21": "20d/60d internal Home-Market-RS; positive-RS component; EMA slopes; range/TR compression relations; absolute return structure",
            "Still_Unvalidated_or_Missing_v0_21": "Sector RS; validated vertical-momentum-excess definition; validated coupling to breakout/pullback/retest/reclaim/drift",
            "Shadow_Validation_Status_v0_21": "HOME_MARKET_RS_COMPONENT_AVAILABLE_SECTOR_BLOCKED",
            "Automated_P0_Decision_v0_21": "NOT_ALLOWED",
        },
        {
            "Lane": "POST_EVENT_DRIFT",
            "Semantically_Measurable_Components_v0_21": "impulse timing/return proxy; post-impulse hold/latest relations; RVOL",
            "Still_Unvalidated_or_Missing_v0_21": "event identity/time; validated impulse definition; validated hold/drift thresholds",
            "Shadow_Validation_Status_v0_21": "COMPONENT_EVIDENCE_ONLY",
            "Automated_P0_Decision_v0_21": "NOT_ALLOWED",
        },
        {
            "Lane": "CONTROLLED_MEAN_REVERSION",
            "Semantically_Measurable_Components_v0_21": "higher-low proxy; EMA slopes; ATR distances; short/long volatility relations",
            "Still_Unvalidated_or_Missing_v0_21": "validated stabilization sequence; falling-knife detector; definable invalidation rule",
            "Shadow_Validation_Status_v0_21": "COMPONENT_EVIDENCE_ONLY",
            "Automated_P0_Decision_v0_21": "NOT_ALLOWED",
        },
    ])
    lane_matrix.to_csv(out / "p0_lane_shadow_validation_matrix_v0.21.csv", index=False)

    registry = {
        "schema": "WELT_SWING_P0_LANE_PARAMETER_REGISTRY_V0_21",
        "generated_utc": now_utc(),
        "validation_status": "SHADOW_COMPONENT_VALIDATION_ONLY",
        "p0_numeric_pass_thresholds": [],
        "promoted_lane_pass_rules": [],
        "explicit_semantic_components": [
            {
                "lane": "QUIET_STRENGTH_RELATIVE_STRENGTH",
                "component": "HomeMarket_RS20_Excess_v0_20 > 0 AND HomeMarket_RS60_Excess_v0_20 > 0",
                "effect": "COMPONENT_ONLY_NOT_LANE_PASS",
            },
            {
                "scope": "descriptive compression relation",
                "component": "Range5_to_Range20 < 1 and/or TR_Mean5_to_20 < 1",
                "effect": "RELATIONAL_OBSERVATION_ONLY_NOT_LANE_PASS",
            },
            {
                "scope": "descriptive higher-low relation",
                "component": "RecentLow10_vs_Prior10_Pct > 0",
                "effect": "RELATIONAL_OBSERVATION_ONLY_NOT_LANE_PASS",
            },
        ],
        "home_market_rs": {
            "status": "AVAILABLE_FOR_2036_SYNCHRONIZED_ROWS",
            "reference": "LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN",
            "official_benchmark_claim": False,
            "asof_exception_ws_id": "WS:US:WBS",
        },
        "sector_rs": {
            "status": "RS_NOT_VERIFIED_NO_FROZEN_SECTOR_METADATA",
            "metadata_contract": "sector_metadata_contract_v0.21.json",
            "ready": False,
        },
        "shadow_evidence_audit": {
            "tri_state_status": True,
            "asof_mismatch_fail_closed_for_all_dynamic_components": True,
            "false_separated_from_not_verified": True,
        },
        "policy": [
            "No shadow component is a P0 PASS/FAIL decision.",
            "No observed percentile or distribution is promoted into a threshold.",
            "Relative strength remains non-sufficient and is not an entry trigger.",
            "The stale v0.20 Lane-4 wording is forward-corrected here without mutating v0.20 history.",
            "Sector taxonomy must be versioned, sourced and deterministically mapped before Sector RS.",
            "As-of mismatches are fail-closed for all dynamic shadow observations.",
        ],
    }
    (out / "p0_lane_parameter_registry_v0.21.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    both_status = obs["Shadow_HomeMarket_RS_Both_Positive_Status_v0_21"].astype(str)
    both_positive = int(both_status.eq("VERIFIED_TRUE").sum())
    if both_positive != int(cfg["expected_lane4_rs_both_positive_rows"]):
        raise SystemExit(f"Lane-4 both-positive count changed: {both_positive}")

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "P0_LANE_PARAMETER_SHADOW_VALIDATION_V0_21_COMPLETE_WITH_SECTOR_RS_BLOCK",
        "input_rows": int(len(df)),
        "asof_synchronized_rows": int(asof_sync.sum()),
        "asof_mismatch_rows": int((~asof_sync).sum()),
        "asof_mismatch_ws_ids": ["WS:US:WBS"],
        "home_market_rs_rows": int(rs_verified.sum()),
        "lane4_home_market_rs_both_positive_rows": both_positive,
        "raw_sector_metadata_columns_detected": sector_metadata_cols,
        "sector_metadata_ready": False,
        "sector_rs_rows": 0,
        "sector_rs_status": "RS_NOT_VERIFIED_NO_FROZEN_SECTOR_METADATA",
        "shadow_component_count": len(component_cols),
        "shadow_component_status_model": "TRI_STATE_VERIFIED_TRUE_VERIFIED_FALSE_NOT_VERIFIED",
        "asof_mismatch_fail_closed_all_dynamic_components": True,
        "lane_count": 6,
        "parameter_validation_status": "SHADOW_COMPONENT_VALIDATION_ONLY",
        "p0_numeric_pass_threshold_count": 0,
        "p0_run": P0_RUN,
        "p0_lane_decisions_made": P0_LANE_DECISIONS_MADE,
        "p0_survivor_rows": 0,
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
        "historical_v0_20_artifacts_mutated": False,
        "next_stage": "P0_SECTOR_METADATA_BULK_SOURCE_PROBE_AND_SHADOW_RULE_TEST_DESIGN",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
    }
    (out / "summary_v0.21.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    evidence_paths = {
        "observations": out / "p0_shadow_component_observations_v0.21.csv",
        "counts": out / "p0_shadow_component_counts_v0.21.csv",
        "lane_matrix": out / "p0_lane_shadow_validation_matrix_v0.21.csv",
        "sector_inventory": out / "sector_metadata_inventory_v0.21.csv",
        "sector_contract": out / "sector_metadata_contract_v0.21.json",
        "registry": out / "p0_lane_parameter_registry_v0.21.json",
        "summary": out / "summary_v0.21.json",
    }
    input_hash = combine_file_hashes(paths)
    parameter_hash = sha256_file(cfg_path)
    output_hash = combine_file_hashes(evidence_paths)
    ended_utc = now_utc()

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_21",
        "run_id": cfg["run_id"],
        "stage_id": "P0_LANE_PARAMETER_SHADOW_VALIDATION_AND_SECTOR_RS_PREP",
        "stage_version": "v0.21",
        "start": started_utc,
        "end": ended_utc,
        "input_hash": input_hash,
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "status": "PARTIAL",
        "input_count": int(len(df)),
        "checked_count": int(len(df)),
        "home_market_rs_count": int(rs_verified.sum()),
        "sector_rs_count": 0,
        "shadow_component_count": len(component_cols),
        "lane_count": 6,
        "pass_count": 0,
        "fail_count": 0,
        "data_error_count": 0,
        "quarantine_count": 0,
        "p0_survivor_count": 0,
        "failed_source": "SECTOR_RS_BLOCKED_NO_FROZEN_SECTOR_METADATA",
        "validated_automated_p0_run": False,
        "automated_p0_ready": False,
        "next_stage": "P0_SECTOR_METADATA_BULK_SOURCE_PROBE_AND_SHADOW_RULE_TEST_DESIGN",
    }
    (out / "stage_checkpoint_v0.21.json").write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    manifest = {
        "schema": "WELT_SWING_P0_SHADOW_VALIDATION_MANIFEST_V0_21",
        "generated_utc": now_utc(),
        "data_source": "FROZEN_V0_20_LOCAL_OUTPUTS_ONLY",
        "input_hash": input_hash,
        "parameter_hash": parameter_hash,
        "evidence_output_hash": output_hash,
        "external_requests": 0,
        "alpha_vantage_allowed": False,
        "files": {},
    }
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "shadow_manifest_v0.21.json":
            manifest["files"][p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    (out / "shadow_manifest_v0.21.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/p0_lane_shadow_validation_v0.21.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
