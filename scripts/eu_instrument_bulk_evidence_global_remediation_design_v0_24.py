#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_EU_INSTRUMENT_BULK_EVIDENCE_GLOBAL_REMEDIATION_DESIGN_V0_24"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_24"

P0_RUN = False
P0_LANE_DECISIONS = False
P0_SURVIVORS = 0
SECTOR_RS_PERFORMED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
EXTERNAL_REQUESTS = 0
WEB_CALLS_PER_SECURITY = False
ALPHA_VANTAGE_ALLOWED = False
PRODUCTIVE_TRADING_AUTHORITY = False
CANONICAL_MASTER_MUTATED = False
HISTORICAL_ARTIFACTS_MUTATED = False
INSTRUMENT_DECISIONS_CHANGED = 0


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


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def require_unique(df: pd.DataFrame, name: str, col: str = "WS_ID") -> None:
    require(col in df.columns, f"{name} missing {col}")
    require(not df[col].astype(str).duplicated().any(), f"{name} duplicate {col}")


def self_test() -> None:
    assert P0_RUN is False
    assert PRODUCTIVE_TRADING_AUTHORITY is False
    assert ALPHA_VANTAGE_ALLOWED is False
    assert EXTERNAL_REQUESTS == 0
    assert INSTRUMENT_DECISIONS_CHANGED == 0
    print("EU_INSTRUMENT_BULK_EVIDENCE_GLOBAL_REMEDIATION_DESIGN_V0_24_SELF_TEST_PASS")


def route_state(segment: str) -> dict[str, str]:
    # This registry is a design classification of already frozen evidence.
    # It is NOT a new source assertion and makes no instrument PASS/FAIL decision.
    registry = {
        "EU_STOXX600": {
            "Evidence_State_v0_24": "OFFICIAL_BULK_SECURITY_TYPE_ROUTE_REQUIRED",
            "Frozen_Evidence_Basis": "v0.9 STOXX capability probe failed before materialization; v0.23 has 365 unresolved rows",
            "Next_Probe_Objective": "Probe official primary-exchange bulk security reference by MIC; require deterministic security type/class or CFI semantics",
            "Probe_Priority": "P1",
        },
        "HK_HSI": {
            "Evidence_State_v0_24": "FROZEN_HKEX_BULK_REFERENCE_MATCHED_SEMANTICS_NOT_PROMOTED",
            "Frozen_Evidence_Basis": "v0.9 HKEX Full List matched all 82 frozen unresolved rows and contains Category/Sub-Category/ISIN",
            "Next_Probe_Objective": "Validate official HKEX Category/Sub-Category semantics for strict common/ordinary-share classification; no new member lookup required if frozen evidence remains accepted",
            "Probe_Priority": "P1",
        },
        "CA_TSX": {
            "Evidence_State_v0_24": "OFFICIAL_SEMANTICS_VALIDATION_BLOCKED",
            "Frozen_Evidence_Basis": "v0.14 official semantics reference validation failed; 105 unresolved rows remain",
            "Next_Probe_Objective": "Materialize auditable TMX/S&P-TSX security-type semantics or another official bulk security reference; no blanket index PASS",
            "Probe_Priority": "P2",
        },
        "KR_KOSPI200": {
            "Evidence_State_v0_24": "OFFICIAL_KRX_BULK_TRANSPORT_BLOCKED",
            "Frozen_Evidence_Basis": "v0.9/v0.10 official KRX bulk request returned HTTP 400; 92 unresolved rows remain",
            "Next_Probe_Objective": "Resolve current official KRX bulk transport/request shape and verify security-kind fields in one bounded bulk request",
            "Probe_Priority": "P2",
        },
        "MX_IPC": {
            "Evidence_State_v0_24": "OFFICIAL_BULK_SECURITY_TYPE_ROUTE_REQUIRED",
            "Frozen_Evidence_Basis": "v0.9 BMV page probe succeeded only as HTML capability probe; 6 unresolved rows remain",
            "Next_Probe_Objective": "Find official BMV bulk/reference security-type evidence or exact official security-class field for the six frozen rows",
            "Probe_Priority": "P3",
        },
    }
    return registry[segment]


def run(cfg_path: Path) -> dict:
    started = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    paths = {k: Path(v) for k, v in cfg["inputs"].items()}

    s23 = read_json(paths["v023_summary"])
    unresolved = read_csv(paths["v023_instrument_unresolved"])
    other = read_csv(paths["v023_other_non_strict"])
    plan23 = read_csv(paths["v023_remediation_plan"])
    probe9 = read_csv(paths["v09_source_probe_status"])
    hk9 = read_csv(paths["v09_hkex_matches"])
    qa4 = read_json(paths["v04_qa_summary"])
    residual4 = read_csv(paths["v04_residual_non_ready"])

    # ---- predecessor and governance gates -----------------------------------
    require(s23.get("run_status") == "UNIVERSE_GAP_ROOT_CAUSE_AUDIT_V0_23_COMPLETE", "Unexpected v0.23 status")
    require(s23.get("root_cause_audit_complete") is True, "v0.23 root cause audit incomplete")
    require(s23.get("unattributed_gap_reason_rows_after_v0_23") == 0, "v0.23 still has unattributed gap rows")
    require(s23.get("next_stage") == "EU_INSTRUMENT_BULK_EVIDENCE_AND_GLOBAL_GAP_REMEDIATION_DESIGN", "v0.23 next-stage mismatch")
    require(qa4.get("run_status") == "QA_FILTERED_BAR_POLICY_PROMOTION_V0_4_COMPLETE", "Unexpected QA v0.4 status")

    for label, obj in [("v0.23", s23), ("QA v0.4", qa4)]:
        require(obj.get("p0_run") is False, f"{label} P0 gate failed")
        require(obj.get("productive_trading_authority") is False, f"{label} productive gate failed")
        require(obj.get("alpha_vantage_allowed") is False, f"{label} Alpha Vantage gate failed")

    require_unique(unresolved, "v0.23 unresolved")
    require_unique(other, "v0.23 other non-strict")
    require_unique(hk9, "v0.9 HKEX matches")
    require_unique(residual4, "v0.4 residual non-ready")

    expected = cfg["expected_counts"]
    require(len(unresolved) == expected["instrument_unresolved_rows"], "Unexpected unresolved count")
    require(len(other) == expected["other_non_strict_rows"], "Unexpected other non-strict count")
    require(len(residual4) == expected["residual_non_ready_rows_v0_4"], "Unexpected QA residual count")
    require(qa4["requalification"]["ready_after"] == expected["qa_ready_after"], "Unexpected QA ready count")

    seg_counts = unresolved["Primary_Universe_Index"].value_counts().to_dict()
    require(seg_counts == expected["instrument_unresolved_by_segment"], f"Unexpected unresolved segment counts: {seg_counts}")

    # ---- Europe 365: MIC/country route inventory -----------------------------
    eu = unresolved.loc[unresolved["Primary_Universe_Index"].eq("EU_STOXX600")].copy()
    require(len(eu) == 365, "EU unresolved count changed")
    require(eu["Primary_MIC"].astype(str).str.strip().ne("").all(), "EU unresolved contains blank Primary_MIC")
    require(eu["Primary_Ticker"].astype(str).str.strip().ne("").all(), "EU unresolved contains blank Primary_Ticker")

    eu_routes = (
        eu.groupby(["Country", "Primary_MIC"], dropna=False)
        .agg(
            Rows=("WS_ID", "size"),
            Unique_Primary_Tickers=("Primary_Ticker", "nunique"),
            Unique_Yahoo_Symbols=("Yahoo_Symbol", "nunique"),
        )
        .reset_index()
        .sort_values(["Rows", "Country", "Primary_MIC"], ascending=[False, True, True], kind="mergesort")
    )
    eu_routes["Preferred_Source_Class_v0_24"] = "OFFICIAL_PRIMARY_EXCHANGE_BULK_SECURITY_REFERENCE"
    eu_routes["Required_Security_Fields_v0_24"] = "PRIMARY_EXCHANGE_CODE_OR_ISIN + SECURITY_TYPE_OR_CLASS_OR_CFI + SOURCE_VERSION_OR_ASOF"
    eu_routes["Deterministic_Match_Key_v0_24"] = "Primary_MIC + Primary_Ticker"
    eu_routes["Ambiguous_Mapping_Policy_v0_24"] = "FAIL_CLOSED"
    eu_routes["Per_Security_Web_Fanout_Allowed_v0_24"] = False
    eu_routes["Route_Status_v0_24"] = "OFFICIAL_BULK_ROUTE_PROBE_REQUIRED"
    eu_route_path = out / "eu_unresolved_route_inventory_v0.24.csv"
    eu_routes.to_csv(eu_route_path, index=False)

    # ---- Global unresolved route state ---------------------------------------
    global_rows = []
    for seg in sorted(seg_counts):
        r = route_state(seg)
        p = probe9.loc[probe9["Primary_Universe_Index"].eq(seg)]
        prior_probe = "NO_V0_9_ROW"
        prior_parse = "NO_V0_9_ROW"
        prior_cov = ""
        if len(p) == 1:
            prior_probe = txt(p.iloc[0].get("Probe_Status"))
            prior_parse = txt(p.iloc[0].get("Parse_Status"))
            prior_cov = txt(p.iloc[0].get("Coverage"))
        global_rows.append({
            "Primary_Universe_Index": seg,
            "Rows": int(seg_counts[seg]),
            "Evidence_State_v0_24": r["Evidence_State_v0_24"],
            "Frozen_Evidence_Basis": r["Frozen_Evidence_Basis"],
            "Prior_v0_9_Probe_Status": prior_probe,
            "Prior_v0_9_Parse_Status": prior_parse,
            "Prior_v0_9_Coverage": prior_cov,
            "Next_Probe_Objective": r["Next_Probe_Objective"],
            "Probe_Priority": r["Probe_Priority"],
            "Required_Provenance": "Source_Name + Source_Reference + Source_Version_or_AsOf + raw SHA256",
            "Required_Identifier_Link": "Deterministic exact match to frozen WS_ID via venue code/ticker or ISIN",
            "Per_Security_Web_Fanout": False,
            "Automatic_PASS_Allowed_In_v0_24": False,
        })
    global_routes = pd.DataFrame(global_rows).sort_values(["Probe_Priority", "Rows"], ascending=[True, False], kind="mergesort")
    global_route_path = out / "global_instrument_evidence_route_inventory_v0.24.csv"
    global_routes.to_csv(global_route_path, index=False)

    # ---- HKEX: exploit frozen bulk evidence without making a decision --------
    hk = unresolved.loc[unresolved["Primary_Universe_Index"].eq("HK_HSI")].copy()
    hk_ids = set(hk["WS_ID"].astype(str))
    hk9_ids = set(hk9["WS_ID"].astype(str))
    require(hk_ids == hk9_ids, "Frozen HKEX reference does not exactly cover current 82 unresolved HK rows")
    require(hk9["HKEX_Match_Status"].eq("MATCHED").all(), "HKEX frozen reference contains non-matched row")
    require(hk9["HKEX_Category"].astype(str).str.strip().ne("").all(), "HKEX Category missing")
    require(hk9["HKEX_Sub-Category"].astype(str).str.strip().ne("").all(), "HKEX Sub-Category missing")

    hk_inv = (
        hk9.groupby(["HKEX_Category", "HKEX_Sub-Category"], dropna=False)
        .size().reset_index(name="Rows")
        .sort_values(["Rows", "HKEX_Category", "HKEX_Sub-Category"], ascending=[False, True, True], kind="mergesort")
    )
    hk_inv["Classification_Status_v0_24"] = "SEMANTICS_NOT_YET_VALIDATED_NO_PASS_FAIL_DECISION"
    hk_inv["Required_Next_Evidence_v0_24"] = "Official HKEX semantics proving which Category/Sub-Category values satisfy strict common/ordinary-share gate"
    hk_path = out / "hkex_frozen_semantics_inventory_v0.24.csv"
    hk_inv.to_csv(hk_path, index=False)

    # ---- Reconcile the 60 data candidates against later QA policy evidence ---
    data_classes = {"DATA_HISTORY_REMEDIATION_CANDIDATE", "DATA_OR_FX_VERIFICATION_CANDIDATE"}
    data = other.loc[other["Remediation_Class_v0_23"].isin(data_classes)].copy()
    require(len(data) == expected["data_remediation_rows_total"], "Unexpected v0.23 data candidate count")

    hist_data = data.loc[data["Remediation_Class_v0_23"].eq("DATA_HISTORY_REMEDIATION_CANDIDATE")].copy()
    datafx = data.loc[data["Remediation_Class_v0_23"].eq("DATA_OR_FX_VERIFICATION_CANDIDATE")].copy()
    require(len(hist_data) == expected["data_history_rows"], "Unexpected data-history count")
    require(len(datafx) == expected["data_or_fx_rows"], "Unexpected data/FX count")

    residual_ids = set(residual4["WS_ID"].astype(str))
    history_ids = set(hist_data["WS_ID"].astype(str))
    require(history_ids == residual_ids, "The 55 v0.23 data-history candidates do not exactly match QA v0.4 residual non-ready rows")

    residual_cols = [c for c in ["WS_ID", "status", "reason_code", "unique_bars", "valid_bars", "suspicious_returns", "first_bar_date", "last_bar_date"] if c in residual4.columns]
    data_recon = data.merge(residual4[residual_cols], on="WS_ID", how="left", validate="one_to_one")
    data_recon["Current_Evidence_State_v0_24"] = data_recon.apply(
        lambda r: (
            "QA_V0_4_RESIDUAL_NON_READY"
            if txt(r.get("Remediation_Class_v0_23")) == "DATA_HISTORY_REMEDIATION_CANDIDATE"
            else "CACHE_READY_BUT_LIQUIDITY_DATA_OR_FX_RECHECK_REQUIRED"
        ), axis=1
    )
    data_recon["Recommended_Next_Action_v0_24"] = data_recon.apply(
        lambda r: (
            "BOUNDED_CURRENT_HISTORY_RECHECK_OR_TARGETED_REFRESH_AFTER_REASON_REVIEW"
            if txt(r.get("Remediation_Class_v0_23")) == "DATA_HISTORY_REMEDIATION_CANDIDATE"
            else "RECOMPUTE_LIQUIDITY_DATA_COVERAGE_WITH_ACCEPTED_CACHE_AND_FX_INPUTS"
        ), axis=1
    )
    data_recon["Automatic_Eligibility_Promotion_v0_24"] = False
    data_recon_path = out / "data_remediation_reconciliation_v0.24.csv"
    data_recon.to_csv(data_recon_path, index=False)

    data_counts = (
        data_recon.groupby(["Primary_Universe_Index", "Remediation_Class_v0_23", "Current_Evidence_State_v0_24", "Recommended_Next_Action_v0_24"], dropna=False)
        .size().reset_index(name="Rows")
        .sort_values(["Rows", "Primary_Universe_Index"], ascending=[False, True], kind="mergesort")
    )
    data_counts_path = out / "data_remediation_counts_v0.24.csv"
    data_counts.to_csv(data_counts_path, index=False)

    # ---- Combined priority plan ---------------------------------------------
    priorities = []
    # Instrument workstreams.
    for _, r in global_routes.iterrows():
        priorities.append({
            "Priority": r["Probe_Priority"],
            "Workstream": "INSTRUMENT_EVIDENCE",
            "Primary_Universe_Index": r["Primary_Universe_Index"],
            "Rows": int(r["Rows"]),
            "Current_State": r["Evidence_State_v0_24"],
            "Next_Action": r["Next_Probe_Objective"],
            "Rule_Weakening": False,
        })
    # Data workstreams.
    for _, r in data_counts.iterrows():
        priorities.append({
            "Priority": "P2" if r["Remediation_Class_v0_23"] == "DATA_HISTORY_REMEDIATION_CANDIDATE" else "P3",
            "Workstream": "DATA_REMEDIATION",
            "Primary_Universe_Index": r["Primary_Universe_Index"],
            "Rows": int(r["Rows"]),
            "Current_State": r["Current_Evidence_State_v0_24"],
            "Next_Action": r["Recommended_Next_Action_v0_24"],
            "Rule_Weakening": False,
        })
    priority_df = pd.DataFrame(priorities).sort_values(["Priority", "Rows", "Primary_Universe_Index"], ascending=[True, False, True], kind="mergesort")
    priority_path = out / "global_remediation_priority_v0.24.csv"
    priority_df.to_csv(priority_path, index=False)

    # ---- Bounded network policy for the NEXT stage, not this stage -----------
    probe_policy = {
        "schema": "WELT_SWING_BOUNDED_BULK_SOURCE_PROBE_POLICY_V0_24",
        "generated_utc": now_utc(),
        "applies_to_next_stage_only": True,
        "v0_24_external_requests": 0,
        "alpha_vantage_allowed": False,
        "per_security_web_fanout_allowed": False,
        "allowed_source_classes": [
            "official primary exchange bulk security reference",
            "official index administrator bulk/reference data when security-type semantics are explicit",
            "official security registry bulk reference data",
        ],
        "required_source_evidence": [
            "Source_Name",
            "Source_Reference",
            "Source_Version_or_AsOf",
            "raw content SHA256",
            "machine-readable schema inventory",
            "deterministic match-key definition",
            "security-type/class/CFI semantics from official source",
        ],
        "mapping_policy": "AMBIGUOUS_OR_UNMATCHED_FAIL_CLOSED",
        "taxonomy_policy": "NO_SILENT_MIXING; source-specific security-type semantics must be documented before cross-source normalization",
        "decision_policy": "NO INSTRUMENT PASS/FAIL FROM INDEX MEMBERSHIP ALONE UNLESS THE OFFICIAL ELIGIBILITY RULE ITSELF IS ACCEPTED AS SUFFICIENT COMMON/ORDINARY-SHARE EVIDENCE",
        "request_budget_design": {
            "EU_STOXX600": "bulk by official venue/source route; never 365 individual requests",
            "HK_HSI": "prefer frozen v0.9 82/82 HKEX match evidence; probe semantics only if needed",
            "CA_TSX": "bounded official bulk/reference semantics probe",
            "KR_KOSPI200": "one/few bounded official bulk transport probes; never per-security",
            "MX_IPC": "bounded official bulk/reference probe for six rows",
        },
    }
    policy_path = out / "bounded_probe_policy_v0.24.json"
    policy_path.write_text(json.dumps(probe_policy, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- Summary -------------------------------------------------------------
    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "EU_INSTRUMENT_BULK_EVIDENCE_GLOBAL_REMEDIATION_DESIGN_V0_24_COMPLETE",
        "instrument_unresolved_rows": len(unresolved),
        "instrument_unresolved_by_segment": {str(k): int(v) for k, v in sorted(seg_counts.items())},
        "eu_unresolved_rows": len(eu),
        "eu_route_buckets_country_mic": len(eu_routes),
        "eu_primary_mic_count": int(eu["Primary_MIC"].nunique()),
        "eu_country_count": int(eu["Country"].nunique()),
        "eu_automatic_instrument_pass_rows": 0,
        "hk_unresolved_rows": len(hk),
        "hk_frozen_reference_exact_match_rows": len(hk9),
        "hk_frozen_reference_set_equal_current_unresolved": True,
        "hk_semantics_buckets": len(hk_inv),
        "hk_automatic_instrument_pass_rows": 0,
        "data_remediation_rows_total": len(data),
        "data_history_rows": len(hist_data),
        "data_history_exactly_match_qa_v0_4_residual_non_ready": True,
        "data_or_fx_rows": len(datafx),
        "qa_v0_4_ready_after": int(qa4["requalification"]["ready_after"]),
        "qa_v0_4_residual_non_ready_rows": int(qa4["requalification"]["residual_non_ready_rows"]),
        "instrument_decisions_changed": INSTRUMENT_DECISIONS_CHANGED,
        "eligibility_promotions_made": 0,
        "global_p0_coverage_gate": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "design_complete": True,
        "p0_run": P0_RUN,
        "p0_lane_decisions_made": P0_LANE_DECISIONS,
        "p0_survivor_rows": P0_SURVIVORS,
        "sector_rs_performed": SECTOR_RS_PERFORMED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "external_requests": EXTERNAL_REQUESTS,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "historical_artifacts_mutated": HISTORICAL_ARTIFACTS_MUTATED,
        "next_stage": "OFFICIAL_BULK_SECURITY_TYPE_PROBE_AND_DATA_GAP_RECHECK",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
    }
    summary_path = out / "summary_v0.24.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in paths.items()}
    parameter_hash = sha256_file(cfg_path)
    evidence_pre_checkpoint = [eu_route_path, global_route_path, hk_path, data_recon_path, data_counts_path, priority_path, policy_path, summary_path]
    evidence_hashes = {p.name: sha256_file(p) for p in evidence_pre_checkpoint}
    output_hash = combined_hash(evidence_hashes)

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "run_id": cfg["run_id"],
        "stage_id": "EU_INSTRUMENT_BULK_EVIDENCE_AND_GLOBAL_GAP_REMEDIATION_DESIGN",
        "stage_version": "v0.24",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": len(unresolved) + len(data),
        "checked_count": len(unresolved) + len(data),
        "pass_count": len(unresolved) + len(data),
        "fail_count": 0,
        "data_error_count": 0,
        "quarantine_count": 0,
        "status": "SUCCESS",
        "failed_source": None,
        "coverage_gate_status": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "instrument_decisions_changed": 0,
        "next_stage": "OFFICIAL_BULK_SECURITY_TYPE_PROBE_AND_DATA_GAP_RECHECK",
    }
    checkpoint_path = out / "stage_checkpoint_v0.24.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest_files = evidence_pre_checkpoint + [checkpoint_path]
    manifest = {
        "schema": "WELT_SWING_EU_INSTRUMENT_BULK_EVIDENCE_GLOBAL_REMEDIATION_DESIGN_MANIFEST_V0_24",
        "generated_utc": now_utc(),
        "data_source": "FROZEN_REPOSITORY_EVIDENCE_ONLY",
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "evidence_output_hash": output_hash,
        "external_requests": 0,
        "alpha_vantage_allowed": False,
        "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in manifest_files},
    }
    manifest_path = out / "manifest_v0.24.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("EU_INSTRUMENT_BULK_EVIDENCE_GLOBAL_REMEDIATION_DESIGN_V0_24_RESULT_GATES_PASS")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/eu_instrument_bulk_evidence_global_remediation_design_v0.24.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    run(Path(args.config))


if __name__ == "__main__":
    main()
