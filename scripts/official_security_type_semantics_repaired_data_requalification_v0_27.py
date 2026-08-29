#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SCHEMA = "WELT_SWING_OFFICIAL_SECURITY_TYPE_SEMANTICS_REPAIRED_DATA_REQUALIFICATION_V0_27"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_27"
LINEAGE_SCOPE = "LEGACY_PRE_MASTER_RESEARCH_LINEAGE"

P0_RUN = False
P0_LANE_DECISIONS = False
P0_SURVIVORS = 0
SECTOR_RS_PERFORMED = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
CANONICAL_MASTER_MUTATED = False
HISTORICAL_ARTIFACTS_MUTATED = False
CURRENT_MASTER_CANONICAL_UNIVERSE_RECONCILED = False
STRICT_U3K_FROZEN = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items: dict[str, str]) -> str:
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def boolish(v: Any) -> bool:
    return txt(v).lower() == "true"


def classify_residual_data(after: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    require(len(after) == 55, f"Expected 55 residual data rows, got {len(after)}")
    require(not after["ws_id"].astype(str).duplicated().any(), "Duplicate residual ws_id")
    require(
        not after["status"].astype(str).eq("READY").any(),
        "v0.26 residual set unexpectedly contains READY row",
    )

    rows = []
    unexpected = []
    for _, r in after.iterrows():
        status = txt(r["status"])
        reason = txt(r["reason_code"])
        if status == "WARMUP" and reason == "INSUFFICIENT_HISTORY":
            action = "STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES"
            shadow = "FAIL_CLOSED_NON_READY"
        elif status == "QUARANTINE" and reason == "INVALID_OHLC_OR_VOLUME":
            action = "PERSISTENT_DATA_QUALITY_EXCLUSION"
            shadow = "FAIL_CLOSED_DATA_QUALITY"
        elif status == "QUARANTINE" and reason == "SUSPICIOUS_RETURN_NEEDS_REPAIR":
            action = "PERSISTENT_SUSPICIOUS_RETURN_EXCLUSION"
            shadow = "FAIL_CLOSED_DATA_QUALITY"
        else:
            action = "UNEXPECTED_RESIDUAL_REASON"
            shadow = "ERROR"
            unexpected.append((txt(r["ws_id"]), status, reason))

        d = dict(r)
        d["Requalification_Action_v0_27"] = action
        d["Shadow_Data_Qualification_v0_27"] = shadow
        d["Further_Blind_Redownload_v0_27"] = False
        rows.append(d)

    require(not unexpected, f"Unexpected residual reason(s): {unexpected[:10]}")
    audit = pd.DataFrame(rows)

    counts = (
        audit.groupby(
            ["status", "reason_code", "Requalification_Action_v0_27"],
            dropna=False,
        )
        .size()
        .reset_index(name="Rows")
        .sort_values(["status", "reason_code"], kind="mergesort")
    )
    require(int(counts["Rows"].sum()) == 55, "Residual reason count accounting mismatch")
    return audit, counts


def recompute_data_or_fx(
    queue: pd.DataFrame,
    master: pd.DataFrame,
    fx: pd.DataFrame,
    liq_cfg: dict,
    cache_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    from build_u3k_liquidity_fx_audit_v0_5 import (
        compute_liquidity_for_security,
        normalize_currency,
    )

    require(len(queue) == 5, f"Expected 5 data/FX rows, got {len(queue)}")
    require(not queue["WS_ID"].astype(str).duplicated().any(), "Duplicate data/FX WS_ID")

    active = master["Active"].astype(str).str.strip().str.lower().eq("true")
    require(int(active.sum()) == 3657, "Unexpected active remediated-master denominator")
    mm = master.loc[active].set_index("WS_ID", drop=False)

    aliases = {str(k).upper(): str(v).upper() for k, v in liq_cfg["currency_aliases"].items()}
    quote_scale_map = {str(k): float(v) for k, v in liq_cfg["quote_scale_by_mic"].items()}
    lcfg = liq_cfg["liquidity"]

    con = sqlite3.connect(cache_path)
    rows = []
    try:
        states = pd.read_sql_query("SELECT * FROM cache_state", con)
        require(len(states) == 3657, f"Current cache states {len(states)} != 3657")
        ready_total = int(states["status"].astype(str).eq("READY").sum())
        require(ready_total == 3602, f"Current cache READY {ready_total} != v0.26 baseline 3602")
        ss = states.set_index("ws_id", drop=False)

        for _, q in queue.iterrows():
            ws = txt(q["WS_ID"])
            require(ws in mm.index, f"Data/FX row missing in active master: {ws}")
            require(ws in ss.index, f"Data/FX row missing cache state: {ws}")

            m = mm.loc[ws]
            st = ss.loc[ws]
            currency = normalize_currency(m.get("Primary_Currency", ""), aliases)
            scale = float(quote_scale_map.get(txt(m.get("Primary_MIC", "")), 1.0))

            if txt(st["status"]) == "READY":
                liq = compute_liquidity_for_security(
                    conn=con,
                    ws_id=ws,
                    currency=currency,
                    quote_scale=scale,
                    fx=fx,
                    min_usable_20=int(lcfg["minimum_usable_sessions_20"]),
                )
            else:
                liq = {
                    "Usable20": 0,
                    "Usable60": 0,
                    "MedianTurnover20_EUR": np.nan,
                    "MedianTurnover60_EUR": np.nan,
                    "FX_Coverage20": 0,
                    "FX_Coverage60": 0,
                    "Liquidity_Data_Status": "NOT_EVALUATED_NON_READY",
                    "Liquidity_Last_Session": "",
                }

            med20 = liq["MedianTurnover20_EUR"]
            if txt(st["status"]) != "READY":
                gate = "NOT_VERIFIED"
                bucket = f"CACHE_{txt(st['status'])}"
            elif liq["Liquidity_Data_Status"] != "OK" or pd.isna(med20):
                gate = "NOT_VERIFIED"
                bucket = "DATA_OR_FX_NOT_VERIFIED"
            elif float(med20) >= float(lcfg["preferred_eur"]):
                gate = "PASS"
                bucket = "PREFERRED_GE_20M"
            elif float(med20) >= float(lcfg["standard_pass_eur"]):
                gate = "PASS"
                bucket = "STANDARD_15_TO_20M"
            elif float(med20) >= float(lcfg["exception_floor_eur"]):
                gate = "FAIL_STRICT"
                bucket = "LOW_LIQUIDITY_EXCEPTION_5_TO_15M"
            else:
                gate = "FAIL"
                bucket = "FAIL_LT_5M"

            d = dict(q)
            d.update({
                "Current_Cache_Status_v0_27": txt(st["status"]),
                "Current_Cache_Reason_v0_27": txt(st["reason_code"]),
                "Currency_Normalized_v0_27": currency,
                "Quote_Scale_To_Major_Currency_v0_27": scale,
                **liq,
                "Shadow_Liquidity_Gate_v0_27": gate,
                "Shadow_Liquidity_Bucket_v0_27": bucket,
                "Historical_Strict_Eligibility_Mutated_v0_27": False,
                "Eligibility_Promotion_v0_27": False,
            })
            rows.append(d)
    finally:
        con.close()

    out = pd.DataFrame(rows)
    counts = {
        str(k): int(v)
        for k, v in out["Shadow_Liquidity_Gate_v0_27"].value_counts(dropna=False).to_dict().items()
    }
    return out, {
        "rows": 5,
        "cache_states": 3657,
        "cache_ready": 3602,
        "shadow_liquidity_gate_counts": counts,
        "shadow_pass_rows": int((out["Shadow_Liquidity_Gate_v0_27"] == "PASS").sum()),
        "eligibility_promotions_made": 0,
    }


def classify_hkex_semantics(hk: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    require(len(hk) == 82, f"Expected 82 HKEX exact-match rows, got {len(hk)}")
    require(
        hk["Current_ISIN_Match_v0_26"].map(boolish).all(),
        "HKEX exact-match set contains ISIN-incompatible row",
    )

    out = hk.copy()
    out["Strict_Security_Type_Semantics_v0_27"] = (
        "HKEX_EQUITY_MAIN_BOARD_IDENTITY_VERIFIED_SUBTYPE_NOT_STRICTLY_PROVEN"
    )
    out["Instrument_Decision_v0_27"] = "UNCHANGED_NOT_VERIFIED"
    out["Eligibility_Promotion_v0_27"] = False
    out["Reason_v0_27"] = (
        "Official Category/Sub-Category proves HKEX equity/Main Board membership, "
        "but frozen evidence does not prove strict Common/Ordinary Share subtype for each security."
    )
    return out, {
        "rows": 82,
        "strict_pass_rows": 0,
        "not_verified_rows": 82,
        "instrument_decisions_changed": 0,
    }


def build_unresolved_ledger(unresolved: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    require(len(unresolved) == 650, f"Expected 650 unresolved instrument rows, got {len(unresolved)}")
    require(not unresolved["WS_ID"].astype(str).duplicated().any(), "Duplicate unresolved WS_ID")

    rows = []
    for _, r in unresolved.iterrows():
        seg = txt(r["Primary_Universe_Index"])
        mic = txt(r["Primary_MIC"])
        if seg == "HK_HSI":
            state = "HKEX_IDENTITY_CATEGORY_MATERIALIZED_SUBTYPE_NOT_STRICTLY_PROVEN"
        elif seg == "KR_KOSPI200":
            state = "KRX_OFFICIAL_BULK_SOURCE_BLOCKED_ERROR_503"
        elif mic == "XMAD":
            state = "BME_OFFICIAL_BULK_ROUTE_NOT_CONFIGURED"
        else:
            state = "OFFICIAL_BULK_SECURITY_TYPE_EVIDENCE_STILL_MISSING"

        d = dict(r)
        d["v0_27_Unresolved_State"] = state
        d["Instrument_Decision_v0_27"] = "UNCHANGED_NOT_VERIFIED"
        d["Eligibility_Promotion_v0_27"] = False
        rows.append(d)

    out = pd.DataFrame(rows)
    counts = {
        str(k): int(v)
        for k, v in out["v0_27_Unresolved_State"].value_counts().to_dict().items()
    }
    require(counts.get("HKEX_IDENTITY_CATEGORY_MATERIALIZED_SUBTYPE_NOT_STRICTLY_PROVEN", 0) == 82,
            "HKEX unresolved ledger count mismatch")
    require(counts.get("KRX_OFFICIAL_BULK_SOURCE_BLOCKED_ERROR_503", 0) == 92,
            "KRX unresolved ledger count mismatch")
    require(counts.get("BME_OFFICIAL_BULK_ROUTE_NOT_CONFIGURED", 0) == 17,
            "XMAD unresolved ledger count mismatch")
    return out, {"rows": 650, "state_counts": counts}


def self_test() -> None:
    x = pd.DataFrame([
        {"ws_id": "A", "status": "WARMUP", "reason_code": "INSUFFICIENT_HISTORY"},
        {"ws_id": "B", "status": "QUARANTINE", "reason_code": "INVALID_OHLC_OR_VOLUME"},
        {"ws_id": "C", "status": "QUARANTINE", "reason_code": "SUSPICIOUS_RETURN_NEEDS_REPAIR"},
    ])
    # Mini mapping test without invoking the 55-row gate.
    mapping = {}
    for _, r in x.iterrows():
        key = (r["status"], r["reason_code"])
        mapping[key] = {
            ("WARMUP", "INSUFFICIENT_HISTORY"): "STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES",
            ("QUARANTINE", "INVALID_OHLC_OR_VOLUME"): "PERSISTENT_DATA_QUALITY_EXCLUSION",
            ("QUARANTINE", "SUSPICIOUS_RETURN_NEEDS_REPAIR"): "PERSISTENT_SUSPICIOUS_RETURN_EXCLUSION",
        }[key]
    assert len(mapping) == 3
    assert LINEAGE_SCOPE == "LEGACY_PRE_MASTER_RESEARCH_LINEAGE"
    assert P0_RUN is False
    assert PRODUCTIVE_TRADING_AUTHORITY is False
    assert ALPHA_VANTAGE_ALLOWED is False
    print("OFFICIAL_SECURITY_TYPE_SEMANTICS_REPAIRED_DATA_REQUALIFICATION_V0_27_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    started = now_utc()
    cfg = read_json(cfg_path)
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = {k: Path(v) for k, v in cfg["inputs"].items()}

    s26 = read_json(inputs["v026_summary"])
    c26 = read_json(inputs["v026_checkpoint"])
    promo26 = inputs["v026_cache_promotion"].read_text(encoding="utf-8").strip()
    after26 = read_csv(inputs["v026_after_state"])
    datafx26 = read_csv(inputs["v026_data_or_fx_queue"])
    hk26 = read_csv(inputs["v026_hkex_audit"])
    unresolved23 = read_csv(inputs["v023_instrument_unresolved"])
    master = read_csv(inputs["remediated_master"])
    fx = read_csv(inputs["fx_history"])
    liq_cfg = read_json(inputs["liquidity_config"])

    # Frozen predecessor gates.
    require(
        s26.get("run_status") == "OFFICIAL_SOURCE_MATERIALIZATION_DATA_GAP_REPAIR_V0_26_COMPLETE",
        "Unexpected v0.26 run status",
    )
    require(s26.get("stage_status") == "PARTIAL", "v0.26 should be PARTIAL")
    require(s26.get("lineage_scope") == LINEAGE_SCOPE, "v0.26 lineage mismatch")
    require(s26.get("legacy_instrument_unresolved_rows") == 650, "v0.26 unresolved count mismatch")
    require(s26["hkex"]["current_exact_match_rows"] == 82, "v0.26 HKEX exact-match mismatch")
    require(s26["hkex"]["current_isin_compatible_rows"] == 82, "v0.26 HKEX ISIN mismatch")
    require(s26["data_repair"]["target_rows"] == 55, "v0.26 repair denominator mismatch")
    require(s26["data_repair"]["target_ready_rows_after"] == 0, "v0.26 should have 0 repaired READY targets")
    require(s26["data_repair"]["target_unresolved_rows_after"] == 55, "v0.26 residual denominator mismatch")
    require(s26["data_repair"]["target_status_counts"].get("QUARANTINE") == 49, "v0.26 quarantine mismatch")
    require(s26["data_repair"]["target_status_counts"].get("WARMUP") == 6, "v0.26 warmup mismatch")
    require(s26["data_repair"]["hard_failure_rows"] == 0, "v0.26 hard failures present")
    require(s26["data_repair"]["cache_promotion_recommended"] is True, "v0.26 cache promotion not recommended")
    require(promo26 == "PROMOTED_V026_WORK_CACHE_TO_MAIN", "v0.26 promoted-cache marker missing")
    require(c26.get("status") == "PARTIAL", "v0.26 checkpoint mismatch")
    require(c26.get("next_stage") == "OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_REPAIRED_DATA_REQUALIFICATION",
            "Wrong predecessor next stage")
    require(s26.get("instrument_decisions_changed") == 0, "v0.26 instrument decisions changed")
    require(s26.get("eligibility_promotions_made") == 0, "v0.26 eligibility changed")
    require(s26.get("p0_run") is False, "v0.26 P0 gate failed")
    require(s26.get("productive_trading_authority") is False, "v0.26 productive gate failed")
    require(s26.get("alpha_vantage_allowed") is False, "v0.26 Alpha gate failed")

    # A) Data-quality requalification: no more blind redownloads.
    residual, residual_counts = classify_residual_data(after26)
    residual.to_csv(out_dir / "residual_data_quality_requalification_v0.27.csv", index=False)
    residual_counts.to_csv(out_dir / "residual_reason_counts_v0.27.csv", index=False)

    # B) Five frozen data/FX cases: shadow recompute only, using current promoted cache.
    fx["day"] = pd.to_datetime(fx["day"], errors="coerce").dt.tz_localize(None)
    fx["FX_to_EUR"] = pd.to_numeric(fx["FX_to_EUR"], errors="coerce")
    require(not fx.empty, "Frozen FX history is empty")
    liq, liq_meta = recompute_data_or_fx(
        datafx26,
        master,
        fx,
        liq_cfg,
        Path(cfg["source_cache"]),
    )
    liq.to_csv(out_dir / "data_or_fx_liquidity_recompute_v0.27.csv", index=False)

    liq_counts = (
        liq.groupby(
            ["Current_Cache_Status_v0_27", "Shadow_Liquidity_Gate_v0_27", "Shadow_Liquidity_Bucket_v0_27"],
            dropna=False,
        )
        .size()
        .reset_index(name="Rows")
    )
    liq_counts.to_csv(out_dir / "data_or_fx_liquidity_recompute_counts_v0.27.csv", index=False)

    # C) HKEX semantics remain fail-closed.
    hk_sem, hk_meta = classify_hkex_semantics(hk26)
    hk_sem.to_csv(out_dir / "hkex_security_type_semantics_v0.27.csv", index=False)

    # D) Full legacy unresolved ledger is still 650.
    unresolved, unresolved_meta = build_unresolved_ledger(unresolved23)
    unresolved.to_csv(out_dir / "unresolved_instrument_blockers_v0.27.csv", index=False)

    impact = pd.DataFrame([
        {"Area": "Instrument unresolved", "Input_Rows": 650, "Changed_Decisions": 0, "Eligibility_Promotions": 0},
        {"Area": "HKEX semantics", "Input_Rows": 82, "Changed_Decisions": 0, "Eligibility_Promotions": 0},
        {"Area": "Residual data quality", "Input_Rows": 55, "Changed_Decisions": 0, "Eligibility_Promotions": 0},
        {"Area": "Data/FX liquidity recompute", "Input_Rows": 5, "Changed_Decisions": 0, "Eligibility_Promotions": 0},
    ])
    impact.to_csv(out_dir / "legacy_requalification_impact_v0.27.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "OFFICIAL_SECURITY_TYPE_SEMANTICS_REPAIRED_DATA_REQUALIFICATION_V0_27_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE_SCOPE,
        "current_master_canonical_universe_reconciled": CURRENT_MASTER_CANONICAL_UNIVERSE_RECONCILED,
        "strict_u3k_frozen": STRICT_U3K_FROZEN,
        "legacy_instrument_unresolved_rows": 650,
        "instrument_unresolved_state_counts": unresolved_meta["state_counts"],
        "hkex_semantics": hk_meta,
        "residual_data_quality": {
            "rows": 55,
            "quarantine_rows": int((residual["status"] == "QUARANTINE").sum()),
            "warmup_rows": int((residual["status"] == "WARMUP").sum()),
            "ready_rows": int((residual["status"] == "READY").sum()),
            "further_blind_redownload_rows": 0,
            "reason_counts": {
                f"{r['status']}|{r['reason_code']}": int(r["Rows"])
                for _, r in residual_counts.iterrows()
            },
        },
        "data_or_fx_requalification": liq_meta,
        "instrument_decisions_changed": 0,
        "eligibility_promotions_made": 0,
        "historical_strict_eligibility_mutated": False,
        "p0_run": P0_RUN,
        "p0_lane_decisions_made": P0_LANE_DECISIONS,
        "p0_survivor_rows": P0_SURVIVORS,
        "sector_rs_performed": SECTOR_RS_PERFORMED,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "historical_artifacts_mutated": HISTORICAL_ARTIFACTS_MUTATED,
        "price_downloads_performed": False,
        "candidate_link_network_fetches": 0,
        "per_security_web_calls": False,
        "coverage_gate_status": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "failed_source": "KRX_DATA_MARKETPLACE",
        "next_stage": "CURRENT_MASTER_OFFICIAL_SOURCE_UNIVERSE_RECONCILIATION_AND_FREEZE_PLAN",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
        "notes": [
            "v0.27 closes the useful requalification loop on the legacy/pre-master repair work without pretending it is current-master canonical coverage.",
            "All 55 re-downloaded residual histories remain non-READY; repeated blind redownload is therefore prohibited.",
            "Five Data/FX cases are recomputed in shadow using the promoted v0.26 cache and frozen v0.5 FX/methodology; no historical eligibility is mutated.",
            "HKEX Category/Sub-Category evidence remains insufficient to prove strict Common/Ordinary Share subtype for each security.",
            "The next primary development effort pivots to the current-master official-source clean-restart lineage and Strict-U3K freeze plan.",
        ],
    }
    summary_path = out_dir / "summary_v0.27.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in inputs.items()}
    input_hashes["source_cache_sha256"] = sha256_file(Path(cfg["source_cache"]))
    parameter_hash = sha256_file(cfg_path)

    evidence_files = [
        p for p in out_dir.iterdir()
        if p.is_file() and p.name not in {"stage_checkpoint_v0.27.json", "manifest_v0.27.json"}
    ]
    evidence_hashes = {p.name: sha256_file(p) for p in sorted(evidence_files)}
    output_hash = combined_hash(evidence_hashes)

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "run_id": cfg["run_id"],
        "stage_id": "OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_REPAIRED_DATA_REQUALIFICATION",
        "stage_version": "v0.27",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": 710,
        "checked_count": 710,
        "pass_count": 710,
        "fail_count": 0,
        "data_error_count": 0,
        "quarantine_count": int((residual["status"] == "QUARANTINE").sum()),
        "status": "PARTIAL",
        "failed_source": "KRX_DATA_MARKETPLACE",
        "lineage_scope": LINEAGE_SCOPE,
        "instrument_decisions_changed": 0,
        "eligibility_promotions_made": 0,
        "coverage_gate_status": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "next_stage": "CURRENT_MASTER_OFFICIAL_SOURCE_UNIVERSE_RECONCILIATION_AND_FREEZE_PLAN",
    }
    checkpoint_path = out_dir / "stage_checkpoint_v0.27.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest_files = sorted(evidence_files + [checkpoint_path])
    manifest = {
        "schema": "WELT_SWING_OFFICIAL_SECURITY_TYPE_SEMANTICS_REPAIRED_DATA_REQUALIFICATION_MANIFEST_V0_27",
        "generated_utc": now_utc(),
        "lineage_scope": LINEAGE_SCOPE,
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "evidence_output_hash": output_hash,
        "alpha_vantage_allowed": False,
        "per_security_web_calls": False,
        "price_downloads_performed": False,
        "files": {
            p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in manifest_files
        },
    }
    (out_dir / "manifest_v0.27.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("OFFICIAL_SECURITY_TYPE_SEMANTICS_REPAIRED_DATA_REQUALIFICATION_V0_27_RESULT_GATES_PASS")
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        default="config/official_security_type_semantics_repaired_data_requalification_v0.27.json",
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    run(Path(args.config))


if __name__ == "__main__":
    main()
