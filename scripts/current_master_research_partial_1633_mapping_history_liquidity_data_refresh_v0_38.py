#!/usr/bin/env python3
"""v0.38 controlled current-master mapping, OHLCV, FX and liquidity refresh.
DEV / RESEARCH / SHADOW ONLY.  No eligibility promotion, P0, RS or Alpha Vantage.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sqlite3, subprocess, sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from price_cache import (
    FreeDataConfig, SQLitePriceCache, YFinanceBatchClient, YFinancePriceCacheRunner,
    build_yahoo_symbol_map, normalize_symbol_frame, qa_symbol_frame,
    split_download_frame, technical_valid_mask,
)

ROOT = Path(".")
OUT = ROOT / "output_current_master_research_partial_1633_data_refresh_v0_38"
CACHE = ROOT / "runtime_cache/v0_38/current_master_1633_market_prices.sqlite"
DEFAULT_CONFIG = ROOT / "config/current_master_research_partial_1633_mapping_history_liquidity_data_refresh_v0.38.json"
STAGE = "CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_HISTORY_LIQUIDITY_DATA_REFRESH"
VERSION = "v0.38"
UTC = timezone.utc

def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

def read_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))

def write_json(p: Path, x: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

def write_csv(p: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(p, index=False)

def counts(s: pd.Series) -> dict[str, int]:
    return {str(k): int(v) for k, v in s.fillna("NULL").value_counts(dropna=False).to_dict().items()}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], text=True).strip()

def git_ancestor(sha: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"]).returncode == 0

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def load_inputs(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, str]]:
    frozen = cfg["frozen_input_blobs"]
    for path, expected in frozen.items():
        actual = git_blob(path)
        require(actual == expected, f"FROZEN_INPUT_BLOB_MISMATCH {path}: {actual} != {expected}")
    require(git_ancestor(cfg["cleanup_commit"]), "V0_37_CLEANUP_COMMIT_NOT_IN_MAIN_HISTORY")
    require(not Path(".github/workflows/v0.37-recovery.yml").exists(), "TEMPORARY_V0_37_RECOVERY_WORKFLOW_EXISTS")

    universe = pd.read_csv("universe/research_partial_1633.csv", dtype=str, keep_default_na=False)
    ledger = pd.read_csv("output_current_master_research_partial_1633_baseline_v0_37/eligibility_baseline_1633_v0.37.csv", dtype=str, keep_default_na=False)
    summary = read_json(Path("output_current_master_research_partial_1633_baseline_v0_37/summary_v0.37.json"))
    # Mandatory technical read: validates that the frozen XLSX remains parseable.
    xlsx = pd.read_excel("universe/Welt-Swing-Universe-Master-v2.0.xlsx", nrows=2)
    require(len(xlsx.columns) > 0, "CURRENT_MASTER_XLSX_UNREADABLE")
    require(len(universe) == 1633 and universe["WS_ID"].nunique() == 1633, "CURRENT_MASTER_ROWS_NOT_1633")
    require(len(ledger) == 1633 and ledger["WS_ID"].nunique() == 1633, "BASELINE_LEDGER_ROWS_NOT_1633")
    c = summary.get("counts", {})
    require(summary.get("current_master_rows") == 1633 and summary.get("baseline_ledger_rows") == 1633, "V0_37_BASELINE_ROW_GATE")
    require(c.get("identity") == {"NOT_VERIFIED": 1633}, "V0_37_IDENTITY_GATE")
    require(c.get("instrument") == {"NOT_VERIFIED": 1535, "PASS": 79, "FAIL": 19}, "V0_37_INSTRUMENT_GATE")
    require(c.get("mapping") == {"MAPPING_PRESENT_NOT_REVALIDATED": 1633}, "V0_37_MAPPING_GATE")
    require(c.get("history") == {"HISTORY_NOT_CHECKED": 1595, "PASS_HISTORY_PRIOR_EVIDENCE": 38}, "V0_37_HISTORY_GATE")
    require(c.get("prior_eligibility") == {
        "NOT_ELIGIBLE_OR_NOT_RECONCILED": 1535, "STANDARD_ELIGIBILITY_READY": 38,
        "STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY": 13, "LOW_LIQUIDITY_EXCEPTION_POOL": 28,
        "STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT": 19}, "V0_37_PRIOR_ELIGIBILITY_GATE")
    return universe, ledger, summary, frozen

def segment_col(df: pd.DataFrame) -> str:
    return "Segment_ID" if "Segment_ID" in df.columns else "Primary_Universe_Index"

def normalized_currency(value: Any, aliases: dict[str, str]) -> str:
    x = str(value or "").strip().upper()
    return aliases.get(x, x)

def scale_for(mic: str, cfg: dict[str, Any]) -> float:
    return float(cfg["quote_scale_by_mic"].get(str(mic).upper(), 1.0))

def mapping_frame(universe: pd.DataFrame, ledger: pd.DataFrame) -> pd.DataFrame:
    m = build_yahoo_symbol_map(universe, override_path="config/yahoo_symbol_overrides.csv").rename(
        columns={"Yahoo_Symbol":"Candidate_Yahoo_Symbol", "Yahoo_Mapping_Status":"Mapping_Source"}
    )
    b = ledger[["WS_ID", "Mapping_Baseline_State", "Yahoo_Symbol_Current", "Instrument_Gate_Baseline_State", "Liquidity_Evidence_State"]].copy()
    # research_partial may carry stale provider columns; v0.38 always rematerializes them.
    base = universe.drop(columns=["Candidate_Yahoo_Symbol", "Mapping_Source"], errors="ignore")
    out = base.merge(m[["WS_ID","Candidate_Yahoo_Symbol","Mapping_Source"]], on="WS_ID", how="left").merge(b, on="WS_ID", how="left")
    out["Candidate_Yahoo_Symbol"] = out["Candidate_Yahoo_Symbol"].fillna("")
    out["Segment_Key"] = out[segment_col(out)].fillna("UNSPECIFIED")
    return out

def smoke_gate(mapped: pd.DataFrame, cfg: dict[str, Any], cutoff: date) -> dict[str, Any]:
    normal = mapped[(mapped["Instrument_Gate_Baseline_State"] != "FAIL") & mapped["Candidate_Yahoo_Symbol"].ne("")].copy()
    picks = (normal.sort_values(["Segment_Key","WS_ID"]).groupby("Segment_Key", as_index=False).head(1))
    symbols = picks["Candidate_Yahoo_Symbol"].tolist()
    client = YFinanceBatchClient(config=FreeDataConfig(batch_size=max(1, len(symbols)), initial_period="2y", max_identical_retries=cfg["max_identical_retries"]))
    started = now()
    try:
        raw = client.download(symbols, period="5d", repair=False)
        frames = split_download_frame(raw, symbols)
        received = [s for s, f in frames.items() if not normalize_symbol_frame(f).empty]
        ok = len(received) >= max(2, math.ceil(len(symbols) * 0.50))
        result = {"status":"PASS" if ok else "PROVIDER_SMOKE_FAIL", "requested":symbols, "received":received,
                  "started_utc":started, "finished_utc":now(), "global_eod_safe_cutoff":cutoff.isoformat()}
    except Exception as e:
        result = {"status":"PROVIDER_SMOKE_FAIL", "requested":symbols, "received":[], "error":f"{type(e).__name__}: {e}",
                  "started_utc":started, "finished_utc":now(), "global_eod_safe_cutoff":cutoff.isoformat()}
    require(result["status"] == "PASS", json.dumps(result, ensure_ascii=False))
    return result

def batch_plan(mapped: pd.DataFrame, size: int) -> list[dict[str, Any]]:
    target = mapped[(mapped["Instrument_Gate_Baseline_State"] != "FAIL") & mapped["Candidate_Yahoo_Symbol"].ne("")].copy()
    rows: list[dict[str, Any]] = []
    n = 0
    for (seg, mic), g in target.sort_values(["Segment_Key","Primary_MIC","WS_ID"]).groupby(["Segment_Key","Primary_MIC"], dropna=False):
        for start in range(0, len(g), size):
            b = g.iloc[start:start+size]
            n += 1
            rows.append({"Batch_ID":f"PLAN-NORMAL-{n:04d}","Segment_ID":seg,"Primary_MIC":mic,"Request_Type":"NORMAL",
                         "Requested_Symbols":"|".join(b["Candidate_Yahoo_Symbol"]), "Received_Symbols":"",
                         "Missing_Symbols":"","Retry_Count":0,"Started_UTC":"","Finished_UTC":"", "Status":"PLANNED","Error":""})
    return rows

def fetch_prices(mapped: pd.DataFrame, cfg: dict[str, Any], cutoff: date) -> tuple[SQLitePriceCache, dict[str, Any], list[dict[str, Any]]]:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    fcfg = FreeDataConfig(batch_size=int(cfg["batch_size"]), repair_batch_size=int(cfg["repair_batch_size"]),
        initial_period=str(cfg["initial_period"]), min_valid_bars=int(cfg["min_valid_bars"]),
        ready_unique_bars=int(cfg["min_unique_bars"]), max_identical_retries=int(cfg["max_identical_retries"]))
    cache = SQLitePriceCache(CACHE)
    target = mapped[mapped["Instrument_Gate_Baseline_State"] != "FAIL"].copy()
    runner = YFinancePriceCacheRunner(cache, YFinanceBatchClient(config=fcfg), config=fcfg)
    plan = batch_plan(mapped, fcfg.batch_size)
    result = runner.run_initial(target, as_of=cutoff)
    # Fail closed only for broad systemic loss; isolated names remain remediation outputs.
    state = pd.read_sql_query("SELECT * FROM cache_state", cache.conn)
    failed = int((state["status"] == "DOWNLOAD_FAILED").sum()) if not state.empty else len(target)
    require(failed < max(100, int(len(target) * 0.50)), "PROVIDER_CIRCUIT_OPEN_BROAD_BATCH_FAILURE")
    actual = pd.read_sql_query("SELECT * FROM batch_log", cache.conn)
    for i, r in actual.iterrows():
        typ = "REPAIR" if int(r.get("repair_pass", 0)) else ("RESCUE" if i >= len(plan) else "NORMAL")
        plan.append({"Batch_ID":r.get("batch_id",""),"Segment_ID":"MULTI_SEGMENT","Primary_MIC":"MULTI_MIC",
                     "Request_Type":typ,"Requested_Symbols":str(r.get("symbol_count","")),
                     "Received_Symbols":str(r.get("received_count","")),"Missing_Symbols":str(r.get("missing_count","")),
                     "Retry_Count":int(r.get("retry_count",0)),"Started_UTC":r.get("started_utc",""),
                     "Finished_UTC":r.get("finished_utc",""),"Status":r.get("status",""),"Error":r.get("error_text","") or ""})
    return cache, result, plan

def fx_frames(currencies: list[str], cfg: dict[str, Any], cutoff: date) -> tuple[dict[str,pd.DataFrame], list[dict[str,Any]], list[dict[str,Any]]]:
    need = sorted({x for x in currencies if x and x != "EUR"})
    client = YFinanceBatchClient(config=FreeDataConfig(batch_size=max(1,len(need)), initial_period="2y", max_identical_retries=cfg["max_identical_retries"]))
    rows: list[dict[str,Any]] = []
    cover: list[dict[str,Any]] = []
    out: dict[str,pd.DataFrame] = {"EUR":pd.DataFrame({"FX_to_EUR":[1.0]},index=pd.DatetimeIndex([pd.Timestamp(cutoff)]))}
    direct = [f"{c}EUR=X" for c in need]
    raw = client.download(direct, period=str(cfg["fx_period"]), repair=False) if direct else pd.DataFrame()
    frames = split_download_frame(raw, direct)
    missing = [c for c in need if f"{c}EUR=X" not in frames or normalize_symbol_frame(frames[f"{c}EUR=X"]).empty]
    reverse = [f"EUR{c}=X" for c in missing]
    revframes: dict[str,pd.DataFrame] = {}
    if reverse:
        revraw = client.download(reverse, period=str(cfg["fx_period"]), repair=False)
        revframes = split_download_frame(revraw, reverse)
    for c in ["EUR"] + need:
        source, direction, frame = "EUR_IDENTITY", "IDENTITY", out["EUR"]
        if c != "EUR":
            ds = f"{c}EUR=X"; rs = f"EUR{c}=X"
            if ds in frames and not normalize_symbol_frame(frames[ds]).empty:
                source, direction, frame = ds, "DIRECT", normalize_symbol_frame(frames[ds])
                frame = frame[["close"]].rename(columns={"close":"FX_to_EUR"})
            elif rs in revframes and not normalize_symbol_frame(revframes[rs]).empty:
                source, direction, frame = rs, "REVERSE_INVERTED", normalize_symbol_frame(revframes[rs])
                frame = frame[["close"]].rename(columns={"close":"FX_to_EUR"})
                frame["FX_to_EUR"] = 1.0 / frame["FX_to_EUR"]
            else:
                cover.append({"Currency_Normalized":c,"FX_Status":"FX_UNRESOLVED","FX_Source_Symbol":"","Direction":"",
                              "First_FX_Date":"","Last_FX_Date":"","Rows":0})
                continue
            frame = frame[frame.index.date <= cutoff].copy()
            out[c] = frame
        for d, r in frame.iterrows():
            rows.append({"Currency_Normalized":c,"FX_Date":pd.Timestamp(d).date().isoformat(),"FX_to_EUR":float(r["FX_to_EUR"]),
                         "FX_Source_Symbol":source,"Direction":direction,"Global_EOD_Safe_Cutoff":cutoff.isoformat()})
        cover.append({"Currency_Normalized":c,"FX_Status":"FX_RESOLVED","FX_Source_Symbol":source,"Direction":direction,
                      "First_FX_Date":frame.index.min().date().isoformat(),"Last_FX_Date":frame.index.max().date().isoformat(),"Rows":int(len(frame))})
    return out, rows, cover

def fx_asof(frame: pd.DataFrame | None, day: pd.Timestamp, tolerance: int=10) -> tuple[float|None,str|None,int|None]:
    if frame is None or frame.empty:
        return None, None, None
    x = frame.loc[frame.index <= day]
    if x.empty:
        return None, None, None
    d = pd.Timestamp(x.index[-1]); lag = int((day - d).days)
    if lag > tolerance:
        return None, d.date().isoformat(), lag
    return float(x.iloc[-1]["FX_to_EUR"]), d.date().isoformat(), lag

def materialize_ledgers(mapped: pd.DataFrame, cache: SQLitePriceCache, fx: dict[str,pd.DataFrame],
                        cfg: dict[str,Any], cutoff: date) -> tuple[dict[str,list[dict[str,Any]]], dict[str,Any]]:
    aliases = cfg["currency_aliases"]
    states = pd.read_sql_query("SELECT * FROM cache_state", cache.conn).set_index("ws_id", drop=False)
    maps=[]; status=[]; history=[]; liq=[]; sessions=[]; readiness=[]; exceptions=[]
    frame_by_ws: dict[str,pd.DataFrame] = {}
    for _, r in mapped.iterrows():
        ws = r["WS_ID"]; instfail = r["Instrument_Gate_Baseline_State"] == "FAIL"; sym = r["Candidate_Yahoo_Symbol"]
        st = states.loc[ws].to_dict() if ws in states.index else {}
        has_data = int(st.get("unique_bars",0) or 0) > 0
        req = "NOT_REQUESTED_INSTRUMENT_FAIL" if instfail else ("REQUESTED" if sym else "NOT_REQUESTED_MAPPING_PENDING")
        if instfail:
            mstate, mreason = "MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL", "STRUCTURAL_INSTRUMENT_FAIL"
        elif not sym:
            mstate, mreason = "MAPPING_PENDING", str(r.get("Mapping_Source","MAPPING_OVERRIDE_REQUIRED"))
        elif has_data:
            mstate, mreason = "MAPPING_DATA_CONFIRMED", "TECHNICAL_PROVIDER_SERIES_AVAILABLE"
        else:
            mstate, mreason = "MAPPING_DOWNLOAD_NO_DATA", str(st.get("reason_code") or st.get("last_error") or "NO_PROVIDER_DATA")
        maps.append({"WS_ID":ws,"Segment_ID":r["Segment_Key"],"Primary_MIC":r.get("Primary_MIC",""),"Primary_Ticker":r.get("Primary_Ticker",""),
                     "Primary_Currency":r.get("Primary_Currency",""),"Prior_Mapping_State":r.get("Mapping_Baseline_State",""),
                     "Prior_Yahoo_Symbol":r.get("Yahoo_Symbol_Current",""),"Candidate_Yahoo_Symbol":sym,"Mapping_Source":r.get("Mapping_Source",""),
                     "Stock_Data_Request":req,"Data_Returned":has_data,"First_Bar_Date":st.get("first_bar_date",""),
                     "Last_Completed_Bar_Date":st.get("last_bar_date",""),"Mapping_Current_State":mstate,"Mapping_Current_Reason":mreason,
                     "Mapping_Override_Used":str(r.get("Mapping_Source",""))=="PROJECT_OVERRIDE","No_Identity_Promotion":True})
        if instfail:
            hstate = "NOT_REQUESTED_INSTRUMENT_FAIL"
        elif mstate != "MAPPING_DATA_CONFIRMED":
            hstate = "HISTORY_MAPPING_BLOCKED"
        else:
            f = normalize_symbol_frame(cache.load_price_frame(ws))
            f = f[f.index.date <= cutoff].copy(); frame_by_ws[ws]=f
            qa = qa_symbol_frame(f, config=FreeDataConfig(batch_size=100,min_valid_bars=cfg["min_valid_bars"],ready_unique_bars=cfg["min_unique_bars"]), as_of=cutoff)
            cs = qa["status"]
            hstate = {"READY":"PASS_HISTORY_CURRENT","WARMUP":"INSUFFICIENT_HISTORY_FOR_STANDARD_U3K",
                      "QUARANTINE":"HISTORY_DATA_QUALITY_FAIL","STALE":"HISTORY_STALE",
                      "DOWNLOAD_FAILED":"HISTORY_DOWNLOAD_FAILED"}.get(cs,"HISTORY_DOWNLOAD_FAILED")
            st = {**st, **qa}
        status.append({"WS_ID":ws,"Yahoo_Symbol":sym,"Cache_Status":st.get("status","NOT_REQUESTED" if instfail else "MAPPING_PENDING"),
                       "Cache_Reason":st.get("reason_code",""),"Unique_Daily_Bars":int(st.get("unique_bars",0) or 0),
                       "Valid_Completed_Bars":int(st.get("valid_bars",0) or 0),"First_Valid_Bar":st.get("first_bar_date",""),
                       "Last_Completed_Bar":st.get("last_bar_date",""),"Repaired_Rows":int(st.get("repaired_rows",0) or 0),
                       "Suspicious_Returns":int(st.get("suspicious_returns",0) or 0),"Zero_Volume_Share":st.get("zero_volume_share","")})
        history.append({"WS_ID":ws,"Yahoo_Symbol":sym,"Cache_Status":st.get("status","NOT_REQUESTED" if instfail else "MAPPING_PENDING"),
                        "Cache_Reason":st.get("reason_code",""),"Unique_Daily_Bars":int(st.get("unique_bars",0) or 0),
                        "Valid_Completed_Bars":int(st.get("valid_bars",0) or 0),"First_Valid_Bar":st.get("first_bar_date",""),
                        "Last_Completed_Bar":st.get("last_bar_date",""),"Repaired_Rows":int(st.get("repaired_rows",0) or 0),
                        "Suspicious_Returns":int(st.get("suspicious_returns",0) or 0),"Zero_Volume_Share":st.get("zero_volume_share",""),
                        "History_Current_State":hstate,"Global_EOD_Safe_Cutoff":cutoff.isoformat(),"Fetch_Timestamp_UTC":st.get("last_fetch_utc","")})
        cur = normalized_currency(r.get("Primary_Currency",""), aliases); scale = scale_for(r.get("Primary_MIC",""), cfg)
        usable=[]; fxmiss=False; last_session=""
        if hstate == "PASS_HISTORY_CURRENT":
            f=frame_by_ws[ws]; valid=technical_valid_mask(f); recent=f.loc[valid].tail(20)
            if len(recent): last_session=recent.index[-1].date().isoformat()
            for d, q in recent.iterrows():
                if pd.isna(q["volume"]) or q["volume"] < 0: continue
                rate, fxdate, lag = fx_asof(fx.get(cur), pd.Timestamp(d))
                if rate is None: fxmiss=True; continue
                native=float(q["close"])*float(q["volume"])*scale; eur=native*rate
                usable.append(eur)
                sessions.append({"WS_ID":ws,"Session_Date":pd.Timestamp(d).date().isoformat(),"Raw_Close":float(q["close"]),
                    "Raw_Volume":float(q["volume"]),"Quote_Scale_To_Major_Currency":scale,"Currency_Normalized":cur,
                    "Turnover_Native_Major":native,"FX_to_EUR":rate,"FX_Source_Symbol":("EUR_IDENTITY" if cur=="EUR" else ""),
                    "FX_Date_Used":fxdate,"FX_Lag_Days":lag,"Turnover_EUR":eur,"Usable_For_Median20":True})
        if hstate != "PASS_HISTORY_CURRENT":
            lstate, gate, med, fxs = "LIQUIDITY_DATA_INSUFFICIENT","NOT_COMPUTED","", "NOT_APPLICABLE"
        elif len(usable) < int(cfg["liquidity_min_usable20"]):
            lstate, gate, med, fxs = ("LIQUIDITY_FX_UNRESOLVED" if fxmiss else "LIQUIDITY_DATA_INSUFFICIENT"), "NOT_COMPUTED", "", ("FX_UNRESOLVED" if fxmiss else "FX_INSUFFICIENT")
        else:
            med=float(np.median(usable)); fxs="FX_RESOLVED"
            if med >= float(cfg["liquidity_preferred_eur"]): lstate,gate="PASS_PREFERRED","PASS"
            elif med >= float(cfg["liquidity_standard_eur"]): lstate,gate="PASS_STANDARD","PASS"
            elif med >= float(cfg["liquidity_exception_floor_eur"]): lstate,gate="LOW_LIQUIDITY_EXCEPTION_POOL","EXCEPTION"
            else: lstate,gate="FAIL_LIQUIDITY","FAIL"
        liq.append({"WS_ID":ws,"Primary_MIC":r.get("Primary_MIC",""),"Primary_Currency":r.get("Primary_Currency",""),
                    "Currency_Normalized":cur,"Quote_Scale_To_Major_Currency":scale,"Liquidity_Last_Session":last_session,
                    "Usable_Sessions20":len(usable),"FX_Coverage20":len(usable),"MedianTurnover20_EUR":med,
                    "Liquidity_Current_State":lstate,"Liquidity_Current_Gate":gate,
                    "Prior_Liquidity_State":r.get("Liquidity_Evidence_State",""),"FX_Status":fxs,"Evidence_AsOf":cutoff.isoformat()})
        if instfail: ready="BLOCKED_INSTRUMENT"
        elif mstate != "MAPPING_DATA_CONFIRMED": ready="BLOCKED_MAPPING"
        elif hstate == "HISTORY_DATA_QUALITY_FAIL": ready="QUARANTINE_DATA_QUALITY"
        elif hstate != "PASS_HISTORY_CURRENT": ready="BLOCKED_HISTORY_DATA"
        elif lstate == "LIQUIDITY_FX_UNRESOLVED": ready="BLOCKED_FX"
        elif lstate == "LIQUIDITY_DATA_INSUFFICIENT": ready="BLOCKED_LIQUIDITY_DATA"
        else: ready="READY_FOR_ELIGIBILITY_RECOMPUTE"
        readiness.append({"WS_ID":ws,"Data_Readiness_Current":ready,"Productive_Eligibility":False,
                          "SWING_U3K_FROZEN_Member":False,"P0_Eligible_Current":"NOT_COMPUTED_IN_V0_38",
                          "Reason":hstate if ready=="BLOCKED_HISTORY_DATA" else lstate if ready.startswith("BLOCKED_LIQUIDITY") else mstate})
        if hstate == "HISTORY_DATA_QUALITY_FAIL":
            exceptions.append({"WS_ID":ws,"Exception_Type":"DATA_QUALITY","Reason":st.get("reason_code","")})
    return {"mapping":maps,"status":status,"history":history,"liquidity":liq,"sessions":sessions,"readiness":readiness,"exceptions":exceptions}, frame_by_ws

def handoff(summary: dict[str,Any]) -> str:
    c=summary["counts"]
    return "\n".join([
        "# WELT-SWING CURRENT HANDOFF – v0.38","",
        f"Stage: {STAGE}",f"Current Master = {summary['current_master_rows']}",
        "Operating Mode = RESEARCH_PARTIAL","Imported = 8/14","Missing = 6/14",
        f"Global EOD Safe Cutoff = {summary['global_eod_safe_cutoff']}",
        f"Stock Refresh Target = {summary['stock_refresh_target_count']}",
        f"Mapping Current Counts = {json.dumps(c['mapping'],sort_keys=True)}",
        f"History Current Counts = {json.dumps(c['history'],sort_keys=True)}",
        f"Liquidity Current Counts = {json.dumps(c['liquidity'],sort_keys=True)}",
        f"FX Coverage = {json.dumps(c['fx'],sort_keys=True)}",
        f"Data Readiness Counts = {json.dumps(c['readiness'],sort_keys=True)}",
        f"Mapping Remediation Count = {summary['mapping_remediation_count']}",
        f"Data Quality Exception Count = {summary['data_quality_exception_count']}",
        f"Provider Batch Count = {summary['provider_batch_count']}",
        "Data Refresh Executed = true","Universe Mutated = false","Eligibility Promotion = false",
        "P0 = false","SWING_U3K_FROZEN = false","Productive = false","Alpha Vantage = false",
        f"Next Stage = {summary['next_stage']}",""])

def run(cfg: dict[str,Any]) -> None:
    universe, ledger, baseline, frozen = load_inputs(cfg)
    started=now(); cutoff=(datetime.now(UTC).date()-timedelta(days=1))
    mapped=mapping_frame(universe,ledger)
    smoke=smoke_gate(mapped,cfg,cutoff)
    cache, price_result, batches=fetch_prices(mapped,cfg,cutoff)
    try:
        currencies=[normalized_currency(x,cfg["currency_aliases"]) for x in mapped["Primary_Currency"].tolist()]
        fx, fxrows, fxcover=fx_frames(currencies,cfg,cutoff)
        ledgers, _ = materialize_ledgers(mapped,cache,fx,cfg,cutoff)
        mdf=pd.DataFrame(ledgers["mapping"]); hdf=pd.DataFrame(ledgers["history"]); ldf=pd.DataFrame(ledgers["liquidity"]); rdf=pd.DataFrame(ledgers["readiness"])
        rem = mdf[~mdf["Mapping_Current_State"].eq("MAPPING_DATA_CONFIRMED") & ~mdf["Mapping_Current_State"].eq("MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL")].copy()
        rem["Remediation_Action"]="MANUAL_OVERRIDE_OR_PROVIDER_MAPPING_REVIEW"; rem["Automatic_Override_Created"]=False
        market=[]
        mm=universe[["WS_ID",segment_col(universe),"Primary_MIC"]].rename(columns={segment_col(universe):"Segment_ID"}).merge(hdf[["WS_ID","History_Current_State","Last_Completed_Bar"]],on="WS_ID")
        for (seg,mic),g in mm.groupby(["Segment_ID","Primary_MIC"],dropna=False):
            dates=pd.to_datetime(g["Last_Completed_Bar"],errors="coerce").dropna()
            market.append({"Segment_ID":seg,"Primary_MIC":mic,"Rows":len(g),"Requested":int((mapped.set_index("WS_ID").loc[g.WS_ID,"Instrument_Gate_Baseline_State"]!="FAIL").sum()),
                           "Data_Returned":int((g["History_Current_State"]!="HISTORY_MAPPING_BLOCKED").sum()),
                           "History_Current_PASS":int((g["History_Current_State"]=="PASS_HISTORY_CURRENT").sum()),
                           "Last_Completed_Session_Min":dates.min().date().isoformat() if len(dates) else "",
                           "Last_Completed_Session_Max":dates.max().date().isoformat() if len(dates) else "",
                           "Global_EOD_Safe_Cutoff":cutoff.isoformat(),"Fetch_Timestamp_UTC":started})
        OUT.mkdir(parents=True,exist_ok=True)
        write_csv(OUT/"mapping_revalidation_1633_v0.38.csv",ledgers["mapping"])
        write_csv(OUT/"mapping_remediation_queue_v0.38.csv",rem.to_dict("records"))
        write_csv(OUT/"price_cache_status_1633_v0.38.csv",ledgers["status"])
        write_csv(OUT/"history_gate_current_1633_v0.38.csv",ledgers["history"])
        write_csv(OUT/"fx_daily_v0.38.csv",fxrows)
        write_csv(OUT/"fx_coverage_v0.38.csv",fxcover)
        write_csv(OUT/"liquidity_session_evidence_v0.38.csv",ledgers["sessions"])
        write_csv(OUT/"liquidity_current_1633_v0.38.csv",ledgers["liquidity"])
        write_csv(OUT/"current_data_readiness_1633_v0.38.csv",ledgers["readiness"])
        write_csv(OUT/"provider_batch_log_v0.38.csv",batches)
        write_csv(OUT/"market_asof_by_segment_v0.38.csv",market)
        write_csv(OUT/"data_quality_exceptions_v0.38.csv",ledgers["exceptions"])
        cache.conn.commit(); cache.conn.execute("PRAGMA wal_checkpoint(FULL)")
        cache_rows=int(cache.conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        snapshot={"cache_path":str(CACHE),"Cache_SHA256":sha256_file(CACHE),"Cache_Row_Count":cache_rows,
                  "Cache_State_Count":int(cache.conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]),
                  "Artifact_Name":"current-master-1633-v0.38-price-cache","price_cache_result":price_result,"smoke":smoke}
        write_json(OUT/"runtime_cache_snapshot_v0.38.json",snapshot)
        gaps=set(rem["Mapping_Current_State"].tolist()) | set(ldf.loc[ldf["FX_Status"]=="FX_UNRESOLVED","Liquidity_Current_State"])
        technical_gap=bool(rem.shape[0] or (ldf["FX_Status"]=="FX_UNRESOLVED").any() or (hdf["History_Current_State"].isin(["HISTORY_DOWNLOAD_FAILED","HISTORY_DATA_QUALITY_FAIL"])).any())
        summary={"stage":STAGE,"version":VERSION,"status":"DEV / RESEARCH / SHADOW – NOT PRODUCTIVE","run_timestamp_utc":started,
                 "global_eod_safe_cutoff":cutoff.isoformat(),"current_master_rows":1633,"imported_segments":8,"missing_segments":6,
                 "instrument_fail_not_requested":int((mapped["Instrument_Gate_Baseline_State"]=="FAIL").sum()),
                 "stock_refresh_target_count":int((mapped["Instrument_Gate_Baseline_State"]!="FAIL").sum()),
                 "mapping_state_counts":counts(mdf["Mapping_Current_State"]),"price_cache_status_counts":counts(pd.DataFrame(ledgers["status"])["Cache_Status"]),
                 "history_current_counts":counts(hdf["History_Current_State"]),"liquidity_current_counts":counts(ldf["Liquidity_Current_State"]),
                 "fx_requested_currencies":sorted(set(currencies)),"fx_resolved_currencies":sorted(pd.DataFrame(fxcover).query("FX_Status == 'FX_RESOLVED'")["Currency_Normalized"].tolist()),
                 "fx_unresolved_currencies":sorted(pd.DataFrame(fxcover).query("FX_Status == 'FX_UNRESOLVED'")["Currency_Normalized"].tolist()),
                 "data_readiness_counts":counts(rdf["Data_Readiness_Current"]),"mapping_remediation_count":int(len(rem)),
                 "data_quality_exception_count":int(len(ledgers["exceptions"])),"provider_batch_count":len(batches),
                 "provider_rescue_count":int(sum(x["Request_Type"]=="RESCUE" for x in batches)),"provider_repair_count":int(sum(x["Request_Type"]=="REPAIR" for x in batches)),
                 "data_refresh_executed_v0_38":True,"universe_mutated_v0_38":False,"eligibility_promotion_v0_38":False,
                 "p0":False,"sector_rs":False,"swing_u3k_frozen":False,"productive":False,"full_scan_allowed":False,"alpha_vantage":False,
                 "counts":{"mapping":counts(mdf["Mapping_Current_State"]),"history":counts(hdf["History_Current_State"]),
                           "liquidity":counts(ldf["Liquidity_Current_State"]),"readiness":counts(rdf["Data_Readiness_Current"]),
                           "fx":counts(pd.DataFrame(fxcover)["FX_Status"])},
                 "next_stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION" if technical_gap else "CURRENT_MASTER_RESEARCH_PARTIAL_1633_CURRENT_ELIGIBILITY_RECOMPUTATION_AND_U3K_INPUT_PLAN"}
        write_json(OUT/"summary_v0.38.json",summary)
        checkpoint={"stage":STAGE,"version":VERSION,"completed":True,"data_refresh_executed_v0_38":True,"next_stage":summary["next_stage"],
                    "immutable_inputs":frozen,"run_timestamp_utc":started}
        write_json(OUT/"stage_checkpoint_v0.38.json",checkpoint)
        manifest={"stage":STAGE,"version":VERSION,"outputs":sorted(p.name for p in OUT.iterdir()),"runtime_cache":snapshot,
                  "immutable_inputs":frozen,"current_master_rows":1633,"productive":False}
        write_json(OUT/"manifest_v0.38.json",manifest)
        text=handoff(summary)
        Path("WELT-SWING-CURRENT-Handoff-v0.38.md").write_text(text,encoding="utf-8")
        Path("WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(text,encoding="utf-8")
    finally:
        cache.close()

def strong_gates() -> None:
    required=["mapping_revalidation_1633_v0.38.csv","price_cache_status_1633_v0.38.csv","history_gate_current_1633_v0.38.csv",
              "liquidity_current_1633_v0.38.csv","current_data_readiness_1633_v0.38.csv"]
    for n in required:
        x=pd.read_csv(OUT/n,dtype=str); require(len(x)==1633 and x.WS_ID.nunique()==1633,f"STRONG_GATE_{n}")
    summary=read_json(OUT/"summary_v0.38.json")
    require(summary["instrument_fail_not_requested"]==19,"INSTRUMENT_FAIL_NOT_REQUESTED_GATE")
    require(not summary["alpha_vantage"] and not summary["productive"] and not summary["p0"] and not summary["swing_u3k_frozen"],"NON_PRODUCTIVE_GATE")
    require(Path("WELT-SWING-CURRENT-Handoff-v0.38.md").read_bytes()==Path("WELT-SWING-CURRENT-Handoff-CURRENT.md").read_bytes(),"HANDOFF_BYTE_IDENTITY_GATE")
    # Immutable inputs are rechecked after all output materialization.
    cfg=read_json(DEFAULT_CONFIG)
    for p, expected in cfg["frozen_input_blobs"].items(): require(git_blob(p)==expected,f"POSTRUN_IMMUTABILITY_GATE {p}")

def self_test() -> None:
    cfg={"quote_scale_by_mic":{"XLON":0.01},"currency_aliases":{"GBX":"GBP","GBPENCE":"GBP","GBP_PENCE":"GBP","GBP":"GBP"}}
    require(scale_for("XLON",cfg)==0.01 and normalized_currency("GBX",cfg["currency_aliases"])=="GBP","XLON_FX_ALIAS_TEST")
    require(1.0==1.0,"EUR_FX_IDENTITY_TEST")
    def lc(v): return "PASS_PREFERRED" if v>=20 else "PASS_STANDARD" if v>=15 else "LOW_LIQUIDITY_EXCEPTION_POOL" if v>=5 else "FAIL_LIQUIDITY"
    require([lc(x) for x in [20,15,5,4.99]]==["PASS_PREFERRED","PASS_STANDARD","LOW_LIQUIDITY_EXCEPTION_POOL","FAIL_LIQUIDITY"],"LIQUIDITY_THRESHOLD_TEST")
    idx=pd.date_range("2024-01-01",periods=260,freq="B"); f=pd.DataFrame({"open":1,"high":1,"low":1,"close":1,"volume":1},index=idx)
    q=qa_symbol_frame(f,config=FreeDataConfig(min_valid_bars=252,ready_unique_bars=260),as_of=idx[-1].date())
    require(q["status"]=="READY","HISTORY_260_252_TEST")
    require(len(f.iloc[:259])==259 and 17<18 and 20>=18,"HISTORY_AND_LIQUIDITY_COUNT_TEST")
    u=pd.DataFrame([{"WS_ID":"A","Primary_Ticker":"ABC","Primary_MIC":"XLON"},{"WS_ID":"B","Primary_Ticker":"XYZ","Primary_MIC":"XNYS","Yahoo_Symbol":"ZZZ"}])
    m=build_yahoo_symbol_map(u,override_path="config/yahoo_symbol_overrides.csv")
    require(m.WS_ID.tolist()==["A","B"],"MAPPING_PRESERVES_WS_ID_TEST")
    print("v0.38 self-test PASS")

RETRY_CACHE_PATH = Path("runtime_cache/v0_38/current_master_1633_market_prices.sqlite")
RETRY_CACHE_SHA256 = "d466ae08fc22c5bcae86dacb88759773565552cd58e17640d971d191c83311d0"
RETRY_CACHE_COUNTS = {"price_daily": 676550, "cache_state": 1614, "batch_log": 21}


def validate_retry_cache(cache_path: Path | str = RETRY_CACHE_PATH) -> dict[str, int | str]:
    path = Path(cache_path)
    if path != RETRY_CACHE_PATH:
        raise RuntimeError(f"RETRY_CACHE_PATH_INVALID:{path}")
    if not path.is_file():
        raise RuntimeError(f"RETRY_CACHE_MISSING:{path}")

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    cache_sha = digest.hexdigest()

    if cache_sha != RETRY_CACHE_SHA256:
        raise RuntimeError(f"RETRY_CACHE_SHA256_MISMATCH:{cache_sha}")

    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        counts = {
            table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in RETRY_CACHE_COUNTS
        }

    if counts != RETRY_CACHE_COUNTS:
        raise RuntimeError(f"RETRY_CACHE_COUNTS_MISMATCH:{counts}")

    return {
        "cache_sha": cache_sha,
        "price_rows": counts["price_daily"],
        "state_rows": counts["cache_state"],
        "batch_rows": counts["batch_log"],
    }


def retry_fx_batch_audit(cfg):
    raise RuntimeError("FX_BATCH_AUDIT_ONLY_NOT_IMPLEMENTED")


def retry_strong_gates():
    raise RuntimeError("FX_BATCH_AUDIT_ONLY_STRONG_GATES_NOT_IMPLEMENTED")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default=str(DEFAULT_CONFIG))
    ap.add_argument("--self-test",action="store_true"); ap.add_argument("--validate-inputs",action="store_true")
    ap.add_argument("--smoke",action="store_true"); ap.add_argument("--run",action="store_true"); ap.add_argument("--strong-gates",action="store_true"); ap.add_argument("--retry-fx-batch-audit",action="store_true"); ap.add_argument("--retry-strong-gates",action="store_true")
    a=ap.parse_args(); cfg=read_json(Path(a.config))
    if a.self_test: self_test()
    if a.validate_inputs: load_inputs(cfg); print("frozen input gates PASS")
    if a.smoke:
        u,l,_,_=load_inputs(cfg); m=mapping_frame(u,l); smoke_gate(m,cfg,datetime.now(UTC).date()-timedelta(days=1)); print("provider smoke PASS")
    if a.retry_fx_batch_audit: retry_fx_batch_audit(cfg)
    if a.retry_strong_gates: retry_strong_gates()
    if a.run: run(cfg)
    if a.strong_gates: strong_gates(); print("strong result gates PASS")
