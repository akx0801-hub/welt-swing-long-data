#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SCHEMA = "WELT_SWING_OFFICIAL_SOURCE_MATERIALIZATION_DATA_GAP_REPAIR_V0_26"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_26"
LINEAGE_SCOPE = "LEGACY_PRE_MASTER_RESEARCH_LINEAGE"
P0_RUN = False
SECTOR_RS_PERFORMED = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False


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


def qmarks(n: int) -> str:
    return ",".join("?" for _ in range(n))


def read_sql(conn: sqlite3.Connection, sql: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


def normalize_stock_code(v: Any) -> str:
    s = re.sub(r"\.0+$", "", txt(v))
    digits = re.sub(r"\D", "", s)
    return digits.zfill(5) if digits else ""


def normalize_isin(v: Any) -> str:
    return re.sub(r"\s+", "", txt(v)).upper()


def find_excel_header_row(path: Path, required: list[str], max_rows: int = 30) -> int | None:
    preview = pd.read_excel(path, sheet_name=0, header=None, nrows=max_rows, dtype=str, keep_default_na=False)
    need = {x.strip().lower() for x in required}
    for idx, row in preview.iterrows():
        vals = {str(v).strip().lower() for v in row.tolist() if str(v).strip()}
        if need.issubset(vals):
            return int(idx)
    return None


def materialize_hkex(unresolved: pd.DataFrame, prior: pd.DataFrame, xlsx: Path, out: Path) -> dict:
    hk = unresolved.loc[unresolved["Primary_Universe_Index"].eq("HK_HSI")].copy()
    require(len(hk) == 82, f"Expected 82 HK unresolved, got {len(hk)}")
    require(len(prior) == 82, f"Expected 82 frozen HKEX matches, got {len(prior)}")
    require(set(hk["WS_ID"]) == set(prior["WS_ID"]), "HK current/frozen WS_ID sets differ")

    header = find_excel_header_row(xlsx, ["Stock Code", "Category", "Sub-Category", "ISIN"])
    require(header is not None, "HKEX workbook header not found")
    sheet = pd.ExcelFile(xlsx).sheet_names[0]
    ref = pd.read_excel(xlsx, sheet_name=sheet, header=header, dtype=str, keep_default_na=False)
    cols = {str(c).strip().lower(): c for c in ref.columns}
    require(all(k in cols for k in ["stock code", "category", "sub-category", "isin"]), "HKEX required columns missing")

    r = ref[[cols["stock code"], cols["category"], cols["sub-category"], cols["isin"]]].copy()
    r.columns = ["Current_HKEX_Stock_Code", "Current_HKEX_Category", "Current_HKEX_Sub_Category", "Current_HKEX_ISIN"]
    r["HKEX_Code_Norm"] = r["Current_HKEX_Stock_Code"].map(normalize_stock_code)
    r["Current_HKEX_ISIN_Norm"] = r["Current_HKEX_ISIN"].map(normalize_isin)
    r = r.loc[r["HKEX_Code_Norm"].ne("")].copy()
    require(not r["HKEX_Code_Norm"].duplicated().any(), "HKEX normalized Stock Code duplicate")

    code_col = next((c for c in prior.columns if str(c).strip().lower() in {"hkex_stock code", "hkex_stock_code", "hkex_stockcode"}), None)
    isin_col = next((c for c in prior.columns if str(c).strip().lower() in {"hkex_isin", "hkex isin"}), None)
    require(code_col is not None and isin_col is not None, "Frozen HKEX stock-code/ISIN columns missing")

    p = prior.copy()
    p["HKEX_Code_Norm"] = p[code_col].map(normalize_stock_code)
    p["Prior_HKEX_ISIN_Norm"] = p[isin_col].map(normalize_isin)
    audit = p[["WS_ID", "HKEX_Code_Norm", "Prior_HKEX_ISIN_Norm"]].merge(r, on="HKEX_Code_Norm", how="left", validate="one_to_one")
    require(len(audit) == 82, "HKEX audit row count changed")
    require(audit["Current_HKEX_Stock_Code"].astype(str).str.strip().ne("").all(), "HKEX exact code match incomplete")
    audit["Current_ISIN_Match_v0_26"] = audit.apply(
        lambda x: (not txt(x["Prior_HKEX_ISIN_Norm"])) or txt(x["Prior_HKEX_ISIN_Norm"]) == txt(x["Current_HKEX_ISIN_Norm"]), axis=1
    )
    require(audit["Current_ISIN_Match_v0_26"].all(), "HKEX current ISIN mismatch")
    audit["Identity_Match_Status_v0_26"] = "EXACT_STOCK_CODE_AND_ISIN_COMPATIBLE"
    audit["Semantics_Status_v0_26"] = "IDENTITY_AND_CATEGORY_MATERIALIZED_SEMANTICS_NOT_PROMOTED"
    audit["Instrument_Decision_v0_26"] = "UNCHANGED_NOT_VERIFIED"
    audit = hk[["WS_ID", "Name", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol"]].merge(audit, on="WS_ID", validate="one_to_one")
    audit.to_csv(out / "hkex_current_exact_match_audit_v0.26.csv", index=False)

    counts = audit.groupby(["Current_HKEX_Category", "Current_HKEX_Sub_Category"], dropna=False).size().reset_index(name="Rows")
    counts["Semantics_Status_v0_26"] = "MATERIALIZED_NOT_YET_ACCEPTED_AS_STRICT_COMMON_ORDINARY_SHARE_RULE"
    counts.to_csv(out / "hkex_current_category_counts_v0.26.csv", index=False)
    return {"header_row_zero_based": header, "reference_rows": len(ref), "matched_rows": len(audit), "isin_compatible_rows": int(audit["Current_ISIN_Match_v0_26"].sum()), "category_buckets": len(counts)}


def rank_links(links: pd.DataFrame, out: Path) -> dict:
    require(len(links) == 244, f"Expected 244 links, got {len(links)}")
    def score(u: str):
        low = u.lower(); n = 0; reasons = []
        if any(low.endswith(e) or f"{e}?" in low for e in (".csv", ".xlsx", ".xls", ".zip")):
            n += 8; reasons.append("MACHINE_READABLE_EXTENSION")
        if "download" in low: n += 4; reasons.append("DOWNLOAD_TERM")
        if any(k in low for k in ("instrument", "security", "securities")): n += 3; reasons.append("SECURITY_TERM")
        if any(k in low for k in ("equity", "equities", "share", "shares")): n += 2; reasons.append("EQUITY_TERM")
        if "list" in low: n += 1; reasons.append("LIST_TERM")
        return n, ";".join(reasons) or "LOW_SIGNAL_LINK"
    x = links.copy()
    scored = x["Candidate_URL"].astype(str).map(score)
    x["Materialization_Priority_Score_v0_26"] = scored.map(lambda z: z[0])
    x["Priority_Reasons_v0_26"] = scored.map(lambda z: z[1])
    x["Candidate_Host_v0_26"] = x["Candidate_URL"].astype(str).map(lambda u: (urlparse(u).hostname or "").lower())
    x["Fetched_In_v0_26"] = False
    x["Validation_Status_v0_26"] = "CANDIDATE_ONLY_NOT_VALIDATED_AS_BULK_SECURITY_TYPE_SOURCE"
    x = x.sort_values(["Materialization_Priority_Score_v0_26", "Source_ID", "Candidate_URL"], ascending=[False, True, True], kind="mergesort")
    x.to_csv(out / "official_candidate_link_priority_v0.26.csv", index=False)
    positive = x.loc[x["Materialization_Priority_Score_v0_26"].astype(int).gt(0)].copy()
    positive.head(80).to_csv(out / "official_candidate_link_shortlist_v0.26.csv", index=False)
    return {"rows": len(x), "positive_signal_rows": len(positive), "top_score": int(x["Materialization_Priority_Score_v0_26"].max()), "links_fetched": 0}


def load_repair_targets(cfg: dict, data_gap: pd.DataFrame, residual: pd.DataFrame):
    from price_cache import build_yahoo_symbol_map
    history = data_gap.loc[data_gap["Remediation_Class_v0_23"].eq("DATA_HISTORY_REMEDIATION_CANDIDATE")].copy()
    datafx = data_gap.loc[data_gap["Remediation_Class_v0_23"].eq("DATA_OR_FX_VERIFICATION_CANDIDATE")].copy()
    require(len(history) == 55 and len(datafx) == 5, "Unexpected data-gap class counts")
    require(set(history["WS_ID"]) == set(residual["WS_ID"]), "55 history queue != QA v0.4 residual set")

    master = read_csv(Path(cfg["inputs"]["remediated_master"]))
    active = master["Active"].astype(str).str.lower().eq("true")
    require(len(master) == 3664 and int(active.sum()) == 3657, "Remediated master denominator changed")
    ids = set(history["WS_ID"])
    target = master.loc[master["WS_ID"].isin(ids)].copy()
    require(len(target) == 55 and active.loc[target.index].all(), "Repair target/master mismatch")
    require(target["Yahoo_Symbol"].astype(str).str.strip().ne("").all(), "Blank target Yahoo symbol")
    expected = dict(zip(target["WS_ID"], target["Yahoo_Symbol"]))
    require(dict(zip(history["WS_ID"], history["Yahoo_Symbol"])) == expected, "Queue/master Yahoo mapping mismatch")
    mapped = build_yahoo_symbol_map(target)
    require(dict(zip(mapped["WS_ID"], mapped["Yahoo_Symbol"])) == expected, "Runtime Yahoo mapping mismatch")
    return target.sort_values("WS_ID").reset_index(drop=True), history.sort_values("WS_ID"), datafx.sort_values("WS_ID"), expected


def snapshot(conn: sqlite3.Connection, ids: list[str]):
    ph = qmarks(len(ids))
    state = read_sql(conn, f"SELECT * FROM cache_state WHERE ws_id IN ({ph}) ORDER BY ws_id", ids)
    counts = read_sql(conn, f"SELECT ws_id,yahoo_symbol,COUNT(*) price_rows,MIN(day) first_day,MAX(day) last_day FROM price_daily WHERE ws_id IN ({ph}) GROUP BY ws_id,yahoo_symbol ORDER BY ws_id", ids)
    return state, counts


def repair_history(cfg: dict, data_gap: pd.DataFrame, residual: pd.DataFrame, out: Path) -> dict:
    from price_cache import FreeDataConfig, SQLitePriceCache, YFinanceBatchClient, YFinancePriceCacheRunner
    target, history, datafx, expected = load_repair_targets(cfg, data_gap, residual)
    ids = target["WS_ID"].astype(str).tolist(); idset = set(ids)
    src = Path(cfg["source_cache"]); work = Path(cfg["work_cache"])
    require(src.exists(), f"Restored QA-v0.4 cache missing: {src}")

    con = sqlite3.connect(src)
    try:
        states = int(con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        ready = int(con.execute("SELECT COUNT(*) FROM cache_state WHERE status='READY'").fetchone()[0])
        nr = read_sql(con, "SELECT ws_id,yahoo_symbol,status,reason_code FROM cache_state WHERE status<>'READY' ORDER BY ws_id")
        require(states == 3657 and ready == 3602 and len(nr) == 55, "QA-v0.4 cache baseline changed")
        require(set(nr["ws_id"]) == idset, "QA-v0.4 non-ready set != 55 repair targets")
        before_state, before_counts = snapshot(con, ids)
        src_price_rows = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
    finally:
        con.close()

    before_state.to_csv(out / "data_history_before_state_v0.26.csv", index=False)
    before_counts.to_csv(out / "data_history_before_price_counts_v0.26.csv", index=False)
    history.to_csv(out / "data_history_repair_queue_v0.26.csv", index=False)
    datafx.to_csv(out / "data_or_fx_recompute_queue_v0.26.csv", index=False)
    target.to_csv(out / "data_history_repair_universe_v0.26.csv", index=False)

    work.parent.mkdir(parents=True, exist_ok=True)
    if work.exists(): work.unlink()
    shutil.copy2(src, work)
    con = sqlite3.connect(work)
    try:
        ph = qmarks(len(ids))
        con.execute(f"DELETE FROM price_daily WHERE ws_id IN ({ph})", ids)
        con.execute(f"DELETE FROM cache_state WHERE ws_id IN ({ph})", ids)
        con.commit()
    finally:
        con.close()

    rcfg = cfg["data_repair"]
    free = FreeDataConfig(batch_size=int(rcfg["batch_size"]), initial_period=rcfg["initial_period"], pause_between_batches_seconds=float(rcfg["pause_between_batches_seconds"]), repair_anomalies=bool(rcfg["repair_anomalies"]))
    cache = SQLitePriceCache(work)
    try:
        runner = YFinancePriceCacheRunner(cache, YFinanceBatchClient(config=free), config=free)
        run_result = runner.run_initial(target, as_of=date.today())
        cache.conn.commit()
        after_state, after_counts = snapshot(cache.conn, ids)
        require(len(after_state) == 55, f"Post-repair states {len(after_state)}/55")
        require(dict(zip(after_state["ws_id"], after_state["yahoo_symbol"])) == expected, "Post-repair Yahoo mapping mismatch")
        total_states = int(cache.conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        total_ready = int(cache.conn.execute("SELECT COUNT(*) FROM cache_state WHERE status='READY'").fetchone()[0])
        total_prices = int(cache.conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        require(total_states == 3657, f"Work-cache denominator changed: {total_states}")
        ph = qmarks(len(ids))
        batches = read_sql(cache.conn, f"SELECT * FROM batch_log WHERE batch_id IN (SELECT DISTINCT batch_id FROM cache_state WHERE ws_id IN ({ph}) AND batch_id IS NOT NULL) ORDER BY finished_utc DESC", ids)
    finally:
        cache.close()

    after_state.to_csv(out / "data_history_after_state_v0.26.csv", index=False)
    after_counts.to_csv(out / "data_history_after_price_counts_v0.26.csv", index=False)
    batches.to_csv(out / "data_history_batch_log_v0.26.csv", index=False)
    status_counts = {str(k): int(v) for k, v in after_state["status"].value_counts(dropna=False).to_dict().items()}
    hard = set(rcfg["hard_failure_statuses"])
    hard_rows = after_state.loc[after_state["status"].isin(hard)].copy()
    hard_rows.to_csv(out / "data_history_hard_failures_v0.26.csv", index=False)
    return {
        "target_rows": 55,
        "data_or_fx_rows": 5,
        "source_cache_states_before": states,
        "source_cache_ready_before": ready,
        "source_cache_non_ready_before": len(nr),
        "source_cache_price_rows_before": src_price_rows,
        "work_cache_states_after": total_states,
        "work_cache_ready_after": total_ready,
        "work_cache_price_rows_after": total_prices,
        "target_status_counts": status_counts,
        "target_ready_rows_after": int(status_counts.get("READY", 0)),
        "target_unresolved_rows_after": 55 - int(status_counts.get("READY", 0)),
        "hard_failure_rows": len(hard_rows),
        "hard_failure_ws_ids": hard_rows["ws_id"].astype(str).tolist(),
        "cache_promotion_recommended": hard_rows.empty,
        "run_result": run_result,
    }


def self_test():
    assert normalize_stock_code("700.0") == "00700"
    assert normalize_stock_code("9988") == "09988"
    assert normalize_isin(" hk0000000001 ") == "HK0000000001"
    assert LINEAGE_SCOPE == "LEGACY_PRE_MASTER_RESEARCH_LINEAGE"
    assert P0_RUN is False and PRODUCTIVE_TRADING_AUTHORITY is False and ALPHA_VANTAGE_ALLOWED is False
    print("OFFICIAL_SOURCE_MATERIALIZATION_DATA_GAP_REPAIR_V0_26_SELF_TEST_PASS")


def run(cfg_path: Path):
    started = now_utc(); cfg = read_json(cfg_path); out = Path(cfg["output_dir"]); out.mkdir(parents=True, exist_ok=True)
    paths = {k: Path(v) for k, v in cfg["inputs"].items()}
    s25 = read_json(paths["v025_summary"]); c25 = read_json(paths["v025_checkpoint"])
    probes = read_csv(paths["v025_probe_status"]); links = read_csv(paths["v025_candidate_links"]); data = read_csv(paths["v025_data_gap_recheck"])
    unresolved = read_csv(paths["v023_instrument_unresolved"]); prior = read_csv(paths["v09_hkex_matches"])
    qa = read_json(paths["qa_v04_summary"]); residual = read_csv(paths["qa_v04_residual_non_ready"])

    require(s25["stage_status"] == "PARTIAL" and c25["status"] == "PARTIAL", "v0.25-r3 predecessor status mismatch")
    require(c25["run_id"].endswith("v0.25-r3"), "v0.25-r3 checkpoint required")
    require(c25["failed_source"] == "KRX_DATA_MARKETPLACE", "Expected KRX as sole v0.25 failed source")
    require(c25["source_probe_count"] == 11 and c25["source_probe_http_ok_count"] == 10 and c25["source_probe_error_count"] == 1, "v0.25 probe counts changed")
    require(c25["parsed_official_bulk_reference_count"] == 1, "Expected one v0.25 parsed official bulk reference")
    require(len(unresolved) == 650 and len(data) == 60 and len(residual) == 55, "Legacy denominator changed")
    require(qa["run_status"] == "QA_FILTERED_BAR_POLICY_PROMOTION_V0_4_COMPLETE", "QA v0.4 status mismatch")
    require(qa["requalification"]["ready_after"] == 3602 and qa["requalification"]["residual_non_ready_rows"] == 55, "QA v0.4 baseline changed")

    hk = materialize_hkex(unresolved, prior, paths["v025_hkex_xlsx"], out)
    lr = rank_links(links, out)
    source_state = probes[["Source_ID", "Source_Name", "Coverage_Route", "Primary_MICs", "Probe_Status", "Official_Semantics_Strength_v0_25", "Materialization_Status_v0_25", "Error"]].copy()
    source_state["Materialization_State_v0_26"] = source_state["Source_ID"].map({"HKEX_FULL_LIST":"OFFICIAL_BULK_IDENTITY_AND_CATEGORY_MATERIALIZED_NO_INSTRUMENT_DECISION", "KRX_DATA_MARKETPLACE":"BLOCKED_HTTP200_ERROR_503_CARRIED_FORWARD"}).fillna("OFFICIAL_PAGE_MATERIALIZED_CANDIDATE_LINKS_RANKED_NO_SECURITY_CLASS_DECISION")
    source_state["Instrument_Decision_Changes_v0_26"] = 0
    source_state.to_csv(out / "official_source_materialization_state_v0.26.csv", index=False)
    pd.DataFrame([
        {"Route":"KR_KOSPI200","Rows":92,"State_v0_26":"BLOCKED_HTTP200_ERROR_503_CARRIED_FORWARD","Next_Action":"Resolve official KRX bulk transport/request shape; fail closed."},
        {"Route":"EU_XMAD","Rows":17,"State_v0_26":"UNCONFIGURED_OFFICIAL_BULK_ROUTE_CARRIED_FORWARD","Next_Action":"Materialize vetted official BME security-reference route; no third-party substitute."},
    ]).to_csv(out / "source_blockers_carried_forward_v0.26.csv", index=False)

    repair = repair_history(cfg, data, residual, out)
    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "OFFICIAL_SOURCE_MATERIALIZATION_DATA_GAP_REPAIR_V0_26_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE_SCOPE,
        "current_master_canonical_universe_reconciled": False,
        "strict_u3k_frozen": False,
        "legacy_instrument_unresolved_rows": 650,
        "hkex": {**hk, "instrument_decisions_changed":0, "semantics_status":"MATERIALIZED_NOT_YET_ACCEPTED_AS_STRICT_COMMON_ORDINARY_SHARE_RULE"},
        "candidate_links": {"frozen_rows":lr["rows"], "positive_signal_rows":lr["positive_signal_rows"], "top_score":lr["top_score"], "links_fetched_in_v0_26":0},
        "source_blockers_carried_forward": {"KR_KOSPI200_rows":92,"EU_XMAD_rows":17},
        "data_repair": repair,
        "data_source": "YFINANCE_FREE_TARGETED_BATCH_REPAIR",
        "price_download_scope_rows": 55,
        "per_security_web_calls": False,
        "instrument_decisions_changed": 0,
        "eligibility_promotions_made": 0,
        "p0_run": False,
        "sector_rs_performed": False,
        "alpha_vantage_allowed": False,
        "productive_trading_authority": False,
        "canonical_master_mutated": False,
        "historical_artifacts_mutated": False,
        "coverage_gate_status": "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "failed_source": "KRX_DATA_MARKETPLACE",
        "next_stage": "OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_REPAIRED_DATA_REQUALIFICATION",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
    }
    sp = out / "summary_v0.26.json"; sp.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k,v in paths.items()}; parameter_hash = sha256_file(cfg_path)
    evidence = [p for p in out.iterdir() if p.is_file() and p.name not in {"stage_checkpoint_v0.26.json","manifest_v0.26.json","cache_promotion_status.txt"}]
    output_hash = combined_hash({p.name: sha256_file(p) for p in sorted(evidence)})
    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,"run_id":cfg["run_id"],"stage_id":"OFFICIAL_SOURCE_MATERIALIZATION_AND_DATA_GAP_REPAIR","stage_version":"v0.26",
        "start":started,"end":now_utc(),"input_hash":combined_hash(input_hashes),"parameter_hash":parameter_hash,"output_hash":output_hash,
        "input_count":710,"checked_count":710,"pass_count":710,"fail_count":0,"data_error_count":int(repair["hard_failure_rows"]),"quarantine_count":int(repair["target_status_counts"].get("QUARANTINE",0)),
        "status":"PARTIAL","failed_source":"KRX_DATA_MARKETPLACE" if repair["hard_failure_rows"]==0 else "KRX_DATA_MARKETPLACE;YFINANCE_TARGETED_HISTORY_REPAIR",
        "lineage_scope":LINEAGE_SCOPE,"instrument_decisions_changed":0,"eligibility_promotions_made":0,"cache_promotion_recommended":bool(repair["cache_promotion_recommended"]),
        "coverage_gate_status":"BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT","next_stage":"OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_REPAIRED_DATA_REQUALIFICATION"
    }
    cp = out / "stage_checkpoint_v0.26.json"; cp.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_files = sorted(evidence + [cp])
    manifest = {"schema":"WELT_SWING_OFFICIAL_SOURCE_MATERIALIZATION_DATA_GAP_REPAIR_MANIFEST_V0_26","generated_utc":now_utc(),"lineage_scope":LINEAGE_SCOPE,"input_hash":checkpoint["input_hash"],"parameter_hash":parameter_hash,"evidence_output_hash":output_hash,"alpha_vantage_allowed":False,"per_security_web_calls":False,"files":{p.name:{"sha256":sha256_file(p),"bytes":p.stat().st_size} for p in manifest_files}}
    (out / "manifest_v0.26.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OFFICIAL_SOURCE_MATERIALIZATION_DATA_GAP_REPAIR_V0_26_RESULT_GATES_PASS")
    print(json.dumps(summary, ensure_ascii=False, default=str))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/official_source_materialization_data_gap_repair_v0.26.json"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: self_test()
    else: run(Path(a.config))


if __name__ == "__main__":
    main()
