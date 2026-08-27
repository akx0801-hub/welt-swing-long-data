#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_UNIVERSE_GAP_ROOT_CAUSE_AUDIT_V0_23"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_23"

P0_RUN = False
P0_LANE_DECISIONS = False
P0_SURVIVORS = 0
SECTOR_RS_PERFORMED = False
PRICE_DOWNLOADS_PERFORMED = False
EXTERNAL_REQUESTS = 0
WEB_CALLS_PER_SECURITY = False
ALPHA_VANTAGE_ALLOWED = False
PRODUCTIVE_TRADING_AUTHORITY = False
CANONICAL_MASTER_MUTATED = False
HISTORICAL_ARTIFACTS_MUTATED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items: dict[str, str]) -> str:
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def require_unique(df: pd.DataFrame, name: str, col: str = "WS_ID") -> None:
    require(col in df.columns, f"{name} missing {col}")
    require(not df[col].astype(str).duplicated().any(), f"{name} has duplicate {col}")


def strict_primary_root_cause(row: pd.Series) -> tuple[str, str, str]:
    """Replay the frozen v0.14 strict-status precedence without changing decisions."""
    cache = txt(row.get("Cache_Status"))
    if cache != "READY":
        return (
            f"CACHE_NOT_READY:{cache or 'BLANK'}",
            txt(row.get("Cache_Reason")) or "NO_CACHE_REASON",
            "DATA_HISTORY_REMEDIATION_CANDIDATE",
        )

    liq = txt(row.get("Liquidity_Gate"))
    detail = txt(row.get("Liquidity_Bucket")) or txt(row.get("Liquidity_Data_Status")) or "NO_LIQUIDITY_REASON"
    if liq == "FAIL_STRICT":
        return "LIQUIDITY_FAIL_STRICT", detail, "VALID_STRICT_LIQUIDITY_EXCLUSION"
    if liq == "FAIL":
        return "LIQUIDITY_FAIL", detail, "VALID_STRICT_LIQUIDITY_EXCLUSION"
    if liq != "PASS":
        return f"LIQUIDITY_NOT_VERIFIED:{liq or 'BLANK'}", detail, "DATA_OR_FX_VERIFICATION_CANDIDATE"

    if txt(row.get("Scalable_Gate")) == "FAIL":
        return (
            "SCALABLE_NOT_AVAILABLE",
            txt(row.get("Scalable_Tradeability_Status")) or "SCALABLE_GATE_FAIL",
            "VALID_EXECUTION_GATE_EXCLUSION",
        )

    inst = txt(row.get("Instrument_Decision_v0_14"))
    reason = txt(row.get("Instrument_Resolution_Reason_v0_14")) or "NO_INSTRUMENT_REASON"
    if inst == "FAIL":
        return "INSTRUMENT_FAIL", reason, "VALID_INSTRUMENT_GATE_EXCLUSION"
    if inst != "PASS":
        return f"INSTRUMENT_NOT_VERIFIED:{inst or 'BLANK'}", reason, "INSTRUMENT_EVIDENCE_REMEDIATION_CANDIDATE"

    return "UNEXPLAINED_STRICT_STATUS_MISMATCH", "ALL_REPLAY_GATES_PASS_BUT_ROW_NOT_STRICT", "AUDIT_ERROR"


def all_blockers(row: pd.Series) -> str:
    blockers: list[str] = []
    cache = txt(row.get("Cache_Status"))
    if cache != "READY":
        blockers.append(f"CACHE:{cache or 'BLANK'}:{txt(row.get('Cache_Reason')) or 'NO_REASON'}")

    liq = txt(row.get("Liquidity_Gate"))
    if liq != "PASS":
        blockers.append(
            f"LIQUIDITY:{liq or 'BLANK'}:"
            + (txt(row.get("Liquidity_Bucket")) or txt(row.get("Liquidity_Data_Status")) or "NO_REASON")
        )

    if txt(row.get("Scalable_Gate")) == "FAIL":
        blockers.append(
            "SCALABLE:FAIL:"
            + (txt(row.get("Scalable_Tradeability_Status")) or "NO_REASON")
        )

    inst = txt(row.get("Instrument_Decision_v0_14"))
    if inst != "PASS":
        blockers.append(
            f"INSTRUMENT:{inst or 'BLANK'}:"
            + (txt(row.get("Instrument_Resolution_Reason_v0_14")) or "NO_REASON")
        )
    return ";".join(blockers)


def self_test() -> None:
    base = {
        "Cache_Status": "READY",
        "Liquidity_Gate": "PASS",
        "Scalable_Gate": "PASS_OR_NOT_VERIFIED",
        "Instrument_Decision_v0_14": "PASS",
    }
    assert strict_primary_root_cause(pd.Series({**base, "Cache_Status": "STALE"}))[0] == "CACHE_NOT_READY:STALE"
    assert strict_primary_root_cause(pd.Series({**base, "Liquidity_Gate": "FAIL_STRICT"}))[0] == "LIQUIDITY_FAIL_STRICT"
    assert strict_primary_root_cause(pd.Series({**base, "Scalable_Gate": "FAIL"}))[0] == "SCALABLE_NOT_AVAILABLE"
    assert strict_primary_root_cause(pd.Series({**base, "Instrument_Decision_v0_14": "FAIL"}))[0] == "INSTRUMENT_FAIL"
    assert strict_primary_root_cause(pd.Series({**base, "Instrument_Decision_v0_14": "NOT_VERIFIED"}))[0].startswith("INSTRUMENT_NOT_VERIFIED")
    print("UNIVERSE_GAP_ROOT_CAUSE_AUDIT_V0_23_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict:
    started = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    paths = {k: Path(v) for k, v in cfg["inputs"].items()}
    exp = cfg["expected_counts"]

    v022 = read_json(paths["v022_summary"])
    v05 = read_json(paths["v05_summary"])
    nr = read_json(paths["non_ready_summary"])
    tr = read_json(paths["targeted_refresh_summary"])
    lineage = read_csv(paths["v022_lineage_rows"])
    full = read_csv(paths["v014_full_eligibility"])
    unresolved_q = read_csv(paths["v015_manual_queue"])
    listing = read_csv(paths["listing_remediation_audit"])
    targeted_state = read_csv(paths["targeted_refresh_state"])

    # Frozen status/governance gates.
    require(v022.get("run_status") == "UNIVERSE_LINEAGE_RECONCILIATION_V0_22_COMPLETE", "Wrong v0.22 status")
    require(v022.get("lineage_accounting_complete") is True, "v0.22 lineage accounting incomplete")
    require(v022.get("unattributed_gap_reason_rows") == 976, "Unexpected v0.22 unattributed gap count")
    require(v05.get("run_status") == "U3K_LIQUIDITY_FX_AUDIT_COMPLETE_WITH_BLOCKERS", "Wrong v0.5 status")
    require(nr.get("run_status") == "NON_READY_REMEDIATION_V0_2_COMPLETE", "Wrong non-ready remediation status")
    require(tr.get("run_status") == "TARGETED_REFRESH_6_COMPLETE", "Wrong targeted refresh status")
    for label, obj in [("v0.22", v022), ("v0.5", v05), ("non_ready", nr), ("targeted_refresh", tr)]:
        require(obj.get("p0_run") is False, f"{label}: P0 governance gate failed")
        require(obj.get("productive_trading_authority") is False, f"{label}: productive authority gate failed")
        require(obj.get("alpha_vantage_allowed") is False, f"{label}: Alpha Vantage gate failed")

    # Shape and set accounting.
    require_unique(lineage, "v0.22 lineage")
    require_unique(full, "v0.14 full eligibility")
    require_unique(unresolved_q, "v0.15 unresolved queue")
    require("ws_id" in targeted_state.columns and targeted_state["ws_id"].is_unique, "targeted refresh identity gate failed")
    require(len(lineage) == exp["v022_lineage_rows"], "Unexpected v0.22 lineage rows")
    require(len(full) == exp["historical_full_eligibility_rows"], "Unexpected v0.14 full eligibility rows")
    require(len(unresolved_q) == exp["instrument_unresolved_rows"], "Unexpected unresolved rows")
    require(v05.get("active_master_rows") == exp["historical_full_eligibility_rows"], "v0.5 denominator mismatch")
    require(nr.get("source_active_rows") == exp["pre_remediation_active_rows"], "Unexpected pre-remediation active rows")
    require(nr.get("active_rows_after_evidence_remediation") == exp["historical_full_eligibility_rows"], "Unexpected remediated active rows")
    require(nr.get("delisted_or_retired_exclusions") == exp["historical_inactive_exclusions"], "Unexpected inactive exclusion count")

    full_ids = set(full["WS_ID"].astype(str))
    strict_ids = set(full.loc[full["Strict_Eligibility_v0_14"].eq("PASS"), "WS_ID"].astype(str))
    unresolved_ids = set(unresolved_q["WS_ID"].astype(str))
    other_ids = set(lineage.loc[lineage["Lineage_Class_v0_22"].eq("EXCLUDED_OTHER_NON_STRICT_REASON_NOT_CLASSIFIED_V0_22"), "WS_ID"].astype(str))
    absent_ids = set(lineage.loc[lineage["Lineage_Class_v0_22"].eq("ABSENT_FROM_V0_14_FULL_ELIGIBILITY_REASON_NOT_CLASSIFIED_V0_22"), "WS_ID"].astype(str))
    require(len(strict_ids) == exp["strict_rows"], "Strict count mismatch")
    require(len(unresolved_ids) == exp["instrument_unresolved_rows"], "Unresolved set mismatch")
    require(len(other_ids) == exp["other_non_strict_rows"], "Other set mismatch")
    require(len(absent_ids) == exp["historical_inactive_exclusions"], "Absent set mismatch")
    require(strict_ids.isdisjoint(unresolved_ids) and strict_ids.isdisjoint(other_ids) and unresolved_ids.isdisjoint(other_ids), "Historical partitions overlap")
    require(strict_ids | unresolved_ids | other_ids == full_ids, "Historical full-eligibility partition mismatch")

    # Resolve six denominator exclusions using frozen v0.2 evidence.
    excluded = listing.loc[listing["Action"].eq("EXCLUDE_INACTIVE")].copy()
    require(len(excluded) == exp["historical_inactive_exclusions"], "EXCLUDE_INACTIVE count mismatch")
    excluded_ids = set(excluded["WS_ID"].astype(str))
    require(absent_ids == excluded_ids, "v0.22 absent set does not equal frozen inactive-remediation set")
    target_ids = set(targeted_state["ws_id"].astype(str))
    require(len(target_ids) == exp["targeted_refresh_rows"], "Targeted refresh count mismatch")
    require(absent_ids.isdisjoint(target_ids), "Inactive exclusions overlap targeted refresh")

    hist = lineage.loc[lineage["WS_ID"].isin(absent_ids)].copy()
    hist = hist.merge(
        excluded[["WS_ID", "Action", "Remediation_Status", "Effective_Date", "Evidence_URL", "Provider_Evidence_URL", "Evidence_Note"]],
        on="WS_ID", how="left", validate="one_to_one"
    )
    hist["Root_Cause_v0_23"] = "EVIDENCE_REMEDIATION_INACTIVE:" + hist["Remediation_Status"].astype(str)
    hist["Remediation_Class_v0_23"] = "VALID_HISTORICAL_INACTIVE_EXCLUSION_NO_REMEDIATION"
    hist["Historical_Eligibility_Denominator_Effect_v0_23"] = "EXCLUDED_BEFORE_V0_5_ELIGIBILITY"
    hist_path = out / "historical_active_denominator_reconciliation_v0.23.csv"
    hist.to_csv(hist_path, index=False)

    # Root-cause 970 other non-strict rows by replaying v0.14 precedence.
    other = full.loc[full["WS_ID"].isin(other_ids)].copy()
    require(len(other) == exp["other_non_strict_rows"], "Other extraction mismatch")
    require(not other["Strict_Eligibility_v0_14"].eq("PASS").any(), "Other set contains PASS")
    roots = other.apply(strict_primary_root_cause, axis=1)
    roots = pd.DataFrame(roots.tolist(), columns=["Primary_Root_Cause_v0_23", "Primary_Root_Cause_Detail_v0_23", "Remediation_Class_v0_23"], index=other.index)
    other = pd.concat([other, roots], axis=1)
    other["All_Blockers_v0_23"] = other.apply(all_blockers, axis=1)
    require(not other["Primary_Root_Cause_v0_23"].eq("UNEXPLAINED_STRICT_STATUS_MISMATCH").any(), "Unexplained other-non-strict row")
    require(other["All_Blockers_v0_23"].astype(str).str.len().gt(0).all(), "Other row without blocker evidence")

    other_cols = [c for c in [
        "WS_ID", "Name", "Country", "Primary_Universe_Index", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol",
        "Cache_Status", "Cache_Reason", "Liquidity_Data_Status", "Liquidity_Gate", "Liquidity_Bucket",
        "MedianTurnover20_EUR", "MedianTurnover60_EUR", "Scalable_Tradeability_Status", "Scalable_Gate",
        "Instrument_Decision_v0_14", "Instrument_Type_Resolved_v0_14", "Instrument_Resolution_Method_v0_14",
        "Instrument_Resolution_Reason_v0_14", "Strict_Eligibility_v0_14",
        "Primary_Root_Cause_v0_23", "Primary_Root_Cause_Detail_v0_23", "Remediation_Class_v0_23", "All_Blockers_v0_23"
    ] if c in other.columns]
    other_out = other[other_cols].sort_values(["Primary_Universe_Index", "Primary_Root_Cause_v0_23", "WS_ID"], kind="mergesort")
    other_path = out / "other_non_strict_root_causes_v0.23.csv"
    other_out.to_csv(other_path, index=False)
    other_counts = (
        other_out.groupby(["Primary_Universe_Index", "Primary_Root_Cause_v0_23", "Primary_Root_Cause_Detail_v0_23", "Remediation_Class_v0_23"], dropna=False)
        .size().reset_index(name="Rows")
        .sort_values(["Rows", "Primary_Universe_Index", "Primary_Root_Cause_v0_23"], ascending=[False, True, True], kind="mergesort")
    )
    other_counts_path = out / "other_non_strict_root_cause_counts_v0.23.csv"
    other_counts.to_csv(other_counts_path, index=False)

    # Root-cause 650 unresolved instrument rows.
    unresolved = full.loc[full["WS_ID"].isin(unresolved_ids)].copy()
    require(len(unresolved) == exp["instrument_unresolved_rows"], "Unresolved extraction mismatch")
    require(unresolved["Cache_Status"].eq("READY").all(), "Unresolved contains non-READY cache")
    require(unresolved["Liquidity_Gate"].eq("PASS").all(), "Unresolved contains non-PASS liquidity")
    require(~unresolved["Scalable_Gate"].eq("FAIL").any(), "Unresolved contains Scalable FAIL")
    require(unresolved["Instrument_Decision_v0_14"].eq("NOT_VERIFIED").all(), "Unresolved instrument decision mismatch")
    require(unresolved["Strict_Eligibility_v0_14"].eq("NOT_VERIFIED").all(), "Unresolved strict status mismatch")
    unresolved["Root_Cause_v0_23"] = "INSTRUMENT_TYPE_NOT_YET_STRICTLY_VERIFIED"
    unresolved["Remediation_Class_v0_23"] = "INSTRUMENT_BULK_EVIDENCE_REQUIRED"
    unresolved["Evidence_State_v0_23"] = unresolved["Instrument_Resolution_Method_v0_14"].astype(str) + ":" + unresolved["Instrument_Resolution_Reason_v0_14"].astype(str)
    unresolved_cols = [c for c in [
        "WS_ID", "Name", "Country", "Primary_Universe_Index", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol",
        "MedianTurnover20_EUR", "MedianTurnover60_EUR", "Instrument_Decision_v0_14",
        "Instrument_Type_Resolved_v0_14", "Instrument_Resolution_Method_v0_14", "Instrument_Resolution_Reason_v0_14",
        "Instrument_Evidence_URL_v0_14", "Instrument_Evidence_Note_v0_14", "Strict_Eligibility_v0_14",
        "Root_Cause_v0_23", "Remediation_Class_v0_23", "Evidence_State_v0_23"
    ] if c in unresolved.columns]
    unresolved_out = unresolved[unresolved_cols].sort_values(["Primary_Universe_Index", "Instrument_Resolution_Reason_v0_14", "WS_ID"], kind="mergesort")
    unresolved_path = out / "instrument_unresolved_root_causes_v0.23.csv"
    unresolved_out.to_csv(unresolved_path, index=False)
    unresolved_counts = (
        unresolved_out.groupby(["Primary_Universe_Index", "Instrument_Resolution_Method_v0_14", "Instrument_Resolution_Reason_v0_14", "Remediation_Class_v0_23"], dropna=False)
        .size().reset_index(name="Rows")
        .sort_values(["Rows", "Primary_Universe_Index"], ascending=[False, True], kind="mergesort")
    )
    unresolved_counts_path = out / "instrument_unresolved_reason_counts_v0.23.csv"
    unresolved_counts.to_csv(unresolved_counts_path, index=False)

    # Segment matrix and remediation plan.
    seg_rows = []
    for seg in sorted(lineage["Primary_Universe_Index"].astype(str).unique()):
        lseg = lineage[lineage["Primary_Universe_Index"].eq(seg)]
        oseg = other_out[other_out["Primary_Universe_Index"].eq(seg)]
        useg = unresolved_out[unresolved_out["Primary_Universe_Index"].eq(seg)]
        hseg = hist[hist["Primary_Universe_Index"].eq(seg)]
        strict_n = int(lseg["Lineage_Class_v0_22"].eq("INCLUDED_RESEARCH_PARTIAL_VERIFIED_STRICT").sum())
        valid_excl = int(oseg["Remediation_Class_v0_23"].astype(str).str.startswith("VALID_").sum()) + len(hseg)
        data_candidates = int(oseg["Remediation_Class_v0_23"].isin(["DATA_HISTORY_REMEDIATION_CANDIDATE", "DATA_OR_FX_VERIFICATION_CANDIDATE"]).sum())
        inst_candidates = len(useg) + int(oseg["Remediation_Class_v0_23"].eq("INSTRUMENT_EVIDENCE_REMEDIATION_CANDIDATE").sum())
        seg_rows.append({
            "Primary_Universe_Index": seg,
            "Source_Lineage_Rows_v0_22": len(lseg),
            "Strict_Rows": strict_n,
            "Instrument_Unresolved_Rows": len(useg),
            "Other_NonStrict_Rows": len(oseg),
            "Historical_Inactive_Exclusions": len(hseg),
            "Valid_Strict_or_Inactive_Exclusions": valid_excl,
            "Data_Remediation_Candidate_Rows": data_candidates,
            "Instrument_Evidence_Candidate_Rows": inst_candidates,
            "Root_Cause_Accounting_OK": strict_n + len(useg) + len(oseg) + len(hseg) == len(lseg),
        })
    seg_df = pd.DataFrame(seg_rows)
    require(seg_df["Root_Cause_Accounting_OK"].all(), "Segment accounting failed")
    seg_path = out / "segment_root_cause_matrix_v0.23.csv"
    seg_df.to_csv(seg_path, index=False)

    actions = {
        "DATA_HISTORY_REMEDIATION_CANDIDATE": "AUDIT_CURRENT_PRICE_HISTORY_STATE_BEFORE_RETRY",
        "DATA_OR_FX_VERIFICATION_CANDIDATE": "AUDIT_DATA_OR_FX_COVERAGE_BEFORE_RETRY",
        "VALID_STRICT_LIQUIDITY_EXCLUSION": "NO_RULE_WEAKENING_KEEP_EXCLUDED",
        "VALID_EXECUTION_GATE_EXCLUSION": "KEEP_EXCLUDED_UNLESS_EXECUTION_EVIDENCE_CHANGES",
        "VALID_INSTRUMENT_GATE_EXCLUSION": "NO_RULE_WEAKENING_KEEP_EXCLUDED",
        "INSTRUMENT_EVIDENCE_REMEDIATION_CANDIDATE": "ADD_TO_BULK_INSTRUMENT_EVIDENCE_WORKSTREAM",
    }
    plan_rows = []
    for (seg, rc), g in other_out.groupby(["Primary_Universe_Index", "Remediation_Class_v0_23"]):
        plan_rows.append({"Primary_Universe_Index": seg, "Source_Class": "OTHER_NON_STRICT", "Remediation_Class_v0_23": rc, "Rows": len(g), "Recommended_Action_v0_23": actions.get(str(rc), "AUDIT_REQUIRED")})
    for seg, g in unresolved_out.groupby("Primary_Universe_Index"):
        plan_rows.append({"Primary_Universe_Index": seg, "Source_Class": "INSTRUMENT_UNRESOLVED", "Remediation_Class_v0_23": "INSTRUMENT_BULK_EVIDENCE_REQUIRED", "Rows": len(g), "Recommended_Action_v0_23": "PROBE_REPRODUCIBLE_BULK_SECURITY_TYPE_SOURCE_NO_PER_SECURITY_FANOUT"})
    for seg, g in hist.groupby("Primary_Universe_Index"):
        plan_rows.append({"Primary_Universe_Index": seg, "Source_Class": "HISTORICAL_INACTIVE", "Remediation_Class_v0_23": "VALID_HISTORICAL_INACTIVE_EXCLUSION_NO_REMEDIATION", "Rows": len(g), "Recommended_Action_v0_23": "PRESERVE_EVIDENCE_REMEDIATION_EXCLUSION"})
    plan = pd.DataFrame(plan_rows).sort_values(["Rows", "Primary_Universe_Index"], ascending=[False, True], kind="mergesort")
    plan_path = out / "remediation_plan_v0.23.csv"
    plan.to_csv(plan_path, index=False)

    # Summary.
    valid_other = int(other_out["Remediation_Class_v0_23"].astype(str).str.startswith("VALID_").sum())
    data_other = int(other_out["Remediation_Class_v0_23"].isin(["DATA_HISTORY_REMEDIATION_CANDIDATE", "DATA_OR_FX_VERIFICATION_CANDIDATE"]).sum())
    instrument_other = int(other_out["Remediation_Class_v0_23"].eq("INSTRUMENT_EVIDENCE_REMEDIATION_CANDIDATE").sum())
    eu_other = other_out[other_out["Primary_Universe_Index"].eq("EU_STOXX600")]
    eu_unresolved = unresolved_out[unresolved_out["Primary_Universe_Index"].eq("EU_STOXX600")]
    require(len(eu_other) == exp["eu_other_non_strict_rows"], "EU other count mismatch")
    require(len(eu_unresolved) == exp["eu_instrument_unresolved_rows"], "EU unresolved count mismatch")

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "UNIVERSE_GAP_ROOT_CAUSE_AUDIT_V0_23_COMPLETE",
        "pre_remediation_source_active_rows": exp["pre_remediation_active_rows"],
        "historical_eligibility_scope_rows": len(full),
        "historical_inactive_exclusions_resolved": len(hist),
        "historical_inactive_exclusions_exactly_match_v0_2_evidence": True,
        "targeted_refresh_rows": len(target_ids),
        "targeted_refresh_disjoint_from_historical_inactive_exclusions": True,
        "strict_rows": len(strict_ids),
        "instrument_unresolved_rows": len(unresolved_out),
        "other_non_strict_rows": len(other_out),
        "other_non_strict_root_causes_attributed": len(other_out),
        "unattributed_gap_reason_rows_after_v0_23": 0,
        "valid_strict_or_historical_exclusion_rows": valid_other + len(hist),
        "data_remediation_candidate_rows": data_other,
        "instrument_evidence_candidate_rows_total": len(unresolved_out) + instrument_other,
        "remediable_coverage_candidate_rows_total": len(unresolved_out) + data_other + instrument_other,
        "historical_eligibility_scope_strict_coverage_pct": round(len(strict_ids) / len(full) * 100.0, 4),
        "eu_stoxx600": {
            "strict_rows": int((lineage["Primary_Universe_Index"].eq("EU_STOXX600") & lineage["Lineage_Class_v0_22"].eq("INCLUDED_RESEARCH_PARTIAL_VERIFIED_STRICT")).sum()),
            "instrument_unresolved_rows": len(eu_unresolved),
            "other_non_strict_rows": len(eu_other),
            "other_non_strict_root_cause_counts": {str(k): int(v) for k, v in eu_other["Primary_Root_Cause_v0_23"].value_counts().items()},
        },
        "global_p0_coverage_gate": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "root_cause_audit_complete": True,
        "p0_run": P0_RUN,
        "p0_lane_decisions_made": P0_LANE_DECISIONS,
        "p0_survivor_rows": P0_SURVIVORS,
        "sector_rs_performed": SECTOR_RS_PERFORMED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "external_requests": EXTERNAL_REQUESTS,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "historical_artifacts_mutated": HISTORICAL_ARTIFACTS_MUTATED,
        "next_stage": "EU_INSTRUMENT_BULK_EVIDENCE_AND_GLOBAL_GAP_REMEDIATION_DESIGN",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
    }
    summary_path = out / "summary_v0.23.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in paths.items()}
    parameter_hash = sha256_file(cfg_path)
    evidence_paths = [hist_path, other_path, other_counts_path, unresolved_path, unresolved_counts_path, seg_path, plan_path, summary_path]
    output_hash = combined_hash({p.name: sha256_file(p) for p in evidence_paths})

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "run_id": cfg["run_id"],
        "stage_id": "UNIVERSE_GAP_ROOT_CAUSE_AUDIT_AND_REMEDIATION_PLAN",
        "stage_version": "v0.23",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": len(lineage),
        "checked_count": len(lineage),
        "pass_count": len(lineage),
        "fail_count": 0,
        "data_error_count": 0,
        "quarantine_count": 0,
        "status": "SUCCESS",
        "failed_source": None,
        "coverage_gate_status": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "unattributed_gap_reason_rows": 0,
        "next_stage": "EU_INSTRUMENT_BULK_EVIDENCE_AND_GLOBAL_GAP_REMEDIATION_DESIGN",
    }
    checkpoint_path = out / "stage_checkpoint_v0.23.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest_paths = evidence_paths + [checkpoint_path]
    manifest = {
        "schema": "WELT_SWING_UNIVERSE_GAP_ROOT_CAUSE_MANIFEST_V0_23",
        "generated_utc": now_utc(),
        "data_source": "FROZEN_REPOSITORY_EVIDENCE_ONLY",
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "evidence_output_hash": output_hash,
        "external_requests": 0,
        "alpha_vantage_allowed": False,
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_paths},
    }
    (out / "manifest_v0.23.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("UNIVERSE_GAP_ROOT_CAUSE_AUDIT_V0_23_RESULT_GATES_PASS")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/universe_gap_root_cause_audit_v0.23.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
