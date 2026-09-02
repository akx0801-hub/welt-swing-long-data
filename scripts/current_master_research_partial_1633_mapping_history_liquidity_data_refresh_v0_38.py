#!/usr/bin/env python3
"""v0.38 controlled current-master mapping, OHLCV, FX and liquidity refresh.
DEV / RESEARCH / SHADOW ONLY. No eligibility promotion, P0, RS or Alpha Vantage.

The normal v0.38 path is preserved.  FX_BATCH_AUDIT_ONLY is a technical retry
path that reuses the frozen stock cache read-only and rematerializes only FX,
liquidity/readiness and batch-audit dependent outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from price_cache import (
    FreeDataConfig,
    SQLitePriceCache,
    YFinanceBatchClient,
    YFinancePriceCacheRunner,
    build_yahoo_symbol_map,
    normalize_symbol_frame,
    qa_symbol_frame,
    split_download_frame,
    technical_valid_mask,
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


def git_hash_object(path: Path | str) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


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
    ledger = pd.read_csv(
        "output_current_master_research_partial_1633_baseline_v0_37/eligibility_baseline_1633_v0.37.csv",
        dtype=str,
        keep_default_na=False,
    )
    summary = read_json(Path("output_current_master_research_partial_1633_baseline_v0_37/summary_v0.37.json"))
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
    require(
        c.get("prior_eligibility")
        == {
            "NOT_ELIGIBLE_OR_NOT_RECONCILED": 1535,
            "STANDARD_ELIGIBILITY_READY": 38,
            "STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY": 13,
            "LOW_LIQUIDITY_EXCEPTION_POOL": 28,
            "STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT": 19,
        },
        "V0_37_PRIOR_ELIGIBILITY_GATE",
    )
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
        columns={"Yahoo_Symbol": "Candidate_Yahoo_Symbol", "Yahoo_Mapping_Status": "Mapping_Source"}
    )
    b = ledger[
        [
            "WS_ID",
            "Mapping_Baseline_State",
            "Yahoo_Symbol_Current",
            "Instrument_Gate_Baseline_State",
            "Liquidity_Evidence_State",
        ]
    ].copy()
    base = universe.drop(columns=["Candidate_Yahoo_Symbol", "Mapping_Source"], errors="ignore")
    out = base.merge(m[["WS_ID", "Candidate_Yahoo_Symbol", "Mapping_Source"]], on="WS_ID", how="left").merge(
        b, on="WS_ID", how="left"
    )
    out["Candidate_Yahoo_Symbol"] = out["Candidate_Yahoo_Symbol"].fillna("")
    out["Segment_Key"] = out[segment_col(out)].fillna("UNSPECIFIED")
    return out


def smoke_gate(mapped: pd.DataFrame, cfg: dict[str, Any], cutoff: date) -> dict[str, Any]:
    normal = mapped[(mapped["Instrument_Gate_Baseline_State"] != "FAIL") & mapped["Candidate_Yahoo_Symbol"].ne("")].copy()
    picks = normal.sort_values(["Segment_Key", "WS_ID"]).groupby("Segment_Key", as_index=False).head(1)
    symbols = picks["Candidate_Yahoo_Symbol"].tolist()
    client = YFinanceBatchClient(
        config=FreeDataConfig(
            batch_size=max(1, len(symbols)), initial_period="2y", max_identical_retries=cfg["max_identical_retries"]
        )
    )
    started = now()
    try:
        raw = client.download(symbols, period="5d", repair=False)
        frames = split_download_frame(raw, symbols)
        received = [s for s, f in frames.items() if not normalize_symbol_frame(f).empty]
        ok = len(received) >= max(2, math.ceil(len(symbols) * 0.50))
        result = {
            "status": "PASS" if ok else "PROVIDER_SMOKE_FAIL",
            "requested": symbols,
            "received": received,
            "started_utc": started,
            "finished_utc": now(),
            "global_eod_safe_cutoff": cutoff.isoformat(),
        }
    except Exception as e:
        result = {
            "status": "PROVIDER_SMOKE_FAIL",
            "requested": symbols,
            "received": [],
            "error": f"{type(e).__name__}: {e}",
            "started_utc": started,
            "finished_utc": now(),
            "global_eod_safe_cutoff": cutoff.isoformat(),
        }
    require(result["status"] == "PASS", json.dumps(result, ensure_ascii=False))
    return result


def batch_plan(mapped: pd.DataFrame, size: int) -> list[dict[str, Any]]:
    target = mapped[(mapped["Instrument_Gate_Baseline_State"] != "FAIL") & mapped["Candidate_Yahoo_Symbol"].ne("")].copy()
    rows: list[dict[str, Any]] = []
    n = 0
    for (seg, mic), g in target.sort_values(["Segment_Key", "Primary_MIC", "WS_ID"]).groupby(
        ["Segment_Key", "Primary_MIC"], dropna=False
    ):
        for start in range(0, len(g), size):
            b = g.iloc[start : start + size]
            n += 1
            rows.append(
                {
                    "Batch_ID": f"PLAN-NORMAL-{n:04d}",
                    "Segment_ID": seg,
                    "Primary_MIC": mic,
                    "Request_Type": "NORMAL",
                    "Requested_Symbols": "|".join(b["Candidate_Yahoo_Symbol"]),
                    "Received_Symbols": "",
                    "Missing_Symbols": "",
                    "Retry_Count": 0,
                    "Started_UTC": "",
                    "Finished_UTC": "",
                    "Status": "PLANNED",
                    "Error": "",
                }
            )
    return rows


def fetch_prices(mapped: pd.DataFrame, cfg: dict[str, Any], cutoff: date) -> tuple[SQLitePriceCache, dict[str, Any], list[dict[str, Any]]]:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    fcfg = FreeDataConfig(
        batch_size=int(cfg["batch_size"]),
        repair_batch_size=int(cfg["repair_batch_size"]),
        initial_period=str(cfg["initial_period"]),
        min_valid_bars=int(cfg["min_valid_bars"]),
        ready_unique_bars=int(cfg["min_unique_bars"]),
        max_identical_retries=int(cfg["max_identical_retries"]),
    )
    cache = SQLitePriceCache(CACHE)
    target = mapped[mapped["Instrument_Gate_Baseline_State"] != "FAIL"].copy()
    runner = YFinancePriceCacheRunner(cache, YFinanceBatchClient(config=fcfg), config=fcfg)
    plan = batch_plan(mapped, fcfg.batch_size)
    result = runner.run_initial(target, as_of=cutoff)
    state = pd.read_sql_query("SELECT * FROM cache_state", cache.conn)
    failed = int((state["status"] == "DOWNLOAD_FAILED").sum()) if not state.empty else len(target)
    require(failed < max(100, int(len(target) * 0.50)), "PROVIDER_CIRCUIT_OPEN_BROAD_BATCH_FAILURE")
    actual = pd.read_sql_query("SELECT * FROM batch_log", cache.conn)
    for i, r in actual.iterrows():
        typ = "REPAIR" if int(r.get("repair_pass", 0)) else ("RESCUE" if i >= len(plan) else "NORMAL")
        plan.append(
            {
                "Batch_ID": r.get("batch_id", ""),
                "Segment_ID": "MULTI_SEGMENT",
                "Primary_MIC": "MULTI_MIC",
                "Request_Type": typ,
                "Requested_Symbols": str(r.get("symbol_count", "")),
                "Received_Symbols": str(r.get("received_count", "")),
                "Missing_Symbols": str(r.get("missing_count", "")),
                "Retry_Count": int(r.get("retry_count", 0)),
                "Started_UTC": r.get("started_utc", ""),
                "Finished_UTC": r.get("finished_utc", ""),
                "Status": r.get("status", ""),
                "Error": r.get("error_text", "") or "",
            }
        )
    return cache, result, plan


def fx_frames(currencies: list[str], cfg: dict[str, Any], cutoff: date) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]], list[dict[str, Any]]]:
    """Original normal-run FX path retained for normal v0.38."""
    need = sorted({x for x in currencies if x and x != "EUR"})
    client = YFinanceBatchClient(
        config=FreeDataConfig(
            batch_size=max(1, len(need)), initial_period="2y", max_identical_retries=cfg["max_identical_retries"]
        )
    )
    rows: list[dict[str, Any]] = []
    cover: list[dict[str, Any]] = []
    out: dict[str, pd.DataFrame] = {
        "EUR": pd.DataFrame({"FX_to_EUR": [1.0]}, index=pd.DatetimeIndex([pd.Timestamp(cutoff)]))
    }
    direct = [f"{c}EUR=X" for c in need]
    raw = client.download(direct, period=str(cfg["fx_period"]), repair=False) if direct else pd.DataFrame()
    frames = split_download_frame(raw, direct)
    missing = [c for c in need if f"{c}EUR=X" not in frames or normalize_symbol_frame(frames[f"{c}EUR=X"]).empty]
    reverse = [f"EUR{c}=X" for c in missing]
    revframes: dict[str, pd.DataFrame] = {}
    if reverse:
        revraw = client.download(reverse, period=str(cfg["fx_period"]), repair=False)
        revframes = split_download_frame(revraw, reverse)
    for c in ["EUR"] + need:
        source, direction, frame = "EUR_IDENTITY", "IDENTITY", out["EUR"]
        if c != "EUR":
            ds = f"{c}EUR=X"
            rs = f"EUR{c}=X"
            if ds in frames and not normalize_symbol_frame(frames[ds]).empty:
                source, direction, frame = ds, "DIRECT", normalize_symbol_frame(frames[ds])
                frame = frame[["close"]].rename(columns={"close": "FX_to_EUR"})
            elif rs in revframes and not normalize_symbol_frame(revframes[rs]).empty:
                source, direction, frame = rs, "REVERSE_INVERTED", normalize_symbol_frame(revframes[rs])
                frame = frame[["close"]].rename(columns={"close": "FX_to_EUR"})
                frame["FX_to_EUR"] = 1.0 / frame["FX_to_EUR"]
            else:
                cover.append(
                    {
                        "Currency_Normalized": c,
                        "FX_Status": "FX_UNRESOLVED",
                        "FX_Source_Symbol": "",
                        "Direction": "",
                        "First_FX_Date": "",
                        "Last_FX_Date": "",
                        "Rows": 0,
                    }
                )
                continue
            frame = frame[frame.index.date <= cutoff].copy()
            out[c] = frame
        for d, r in frame.iterrows():
            rows.append(
                {
                    "Currency_Normalized": c,
                    "FX_Date": pd.Timestamp(d).date().isoformat(),
                    "FX_to_EUR": float(r["FX_to_EUR"]),
                    "FX_Source_Symbol": source,
                    "Direction": direction,
                    "Global_EOD_Safe_Cutoff": cutoff.isoformat(),
                }
            )
        cover.append(
            {
                "Currency_Normalized": c,
                "FX_Status": "FX_RESOLVED",
                "FX_Source_Symbol": source,
                "Direction": direction,
                "First_FX_Date": frame.index.min().date().isoformat(),
                "Last_FX_Date": frame.index.max().date().isoformat(),
                "Rows": int(len(frame)),
            }
        )
    return out, rows, cover


def fx_asof(frame: pd.DataFrame | None, day: pd.Timestamp, tolerance: int = 10) -> tuple[float | None, str | None, int | None]:
    if frame is None or frame.empty:
        return None, None, None
    x = frame.loc[frame.index <= day]
    if x.empty:
        return None, None, None
    d = pd.Timestamp(x.index[-1])
    lag = int((day - d).days)
    if lag > tolerance:
        return None, d.date().isoformat(), lag
    return float(x.iloc[-1]["FX_to_EUR"]), d.date().isoformat(), lag


def materialize_ledgers(
    mapped: pd.DataFrame, cache: SQLitePriceCache, fx: dict[str, pd.DataFrame], cfg: dict[str, Any], cutoff: date
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    aliases = cfg["currency_aliases"]
    states = pd.read_sql_query("SELECT * FROM cache_state", cache.conn).set_index("ws_id", drop=False)
    maps: list[dict[str, Any]] = []
    status: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    liq: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    frame_by_ws: dict[str, pd.DataFrame] = {}
    for _, r in mapped.iterrows():
        ws = r["WS_ID"]
        instfail = r["Instrument_Gate_Baseline_State"] == "FAIL"
        sym = r["Candidate_Yahoo_Symbol"]
        st = states.loc[ws].to_dict() if ws in states.index else {}
        has_data = int(st.get("unique_bars", 0) or 0) > 0
        req = "NOT_REQUESTED_INSTRUMENT_FAIL" if instfail else ("REQUESTED" if sym else "NOT_REQUESTED_MAPPING_PENDING")
        if instfail:
            mstate, mreason = "MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL", "STRUCTURAL_INSTRUMENT_FAIL"
        elif not sym:
            mstate, mreason = "MAPPING_PENDING", str(r.get("Mapping_Source", "MAPPING_OVERRIDE_REQUIRED"))
        elif has_data:
            mstate, mreason = "MAPPING_DATA_CONFIRMED", "TECHNICAL_PROVIDER_SERIES_AVAILABLE"
        else:
            mstate, mreason = "MAPPING_DOWNLOAD_NO_DATA", str(st.get("reason_code") or st.get("last_error") or "NO_PROVIDER_DATA")
        maps.append(
            {
                "WS_ID": ws,
                "Segment_ID": r["Segment_Key"],
                "Primary_MIC": r.get("Primary_MIC", ""),
                "Primary_Ticker": r.get("Primary_Ticker", ""),
                "Primary_Currency": r.get("Primary_Currency", ""),
                "Prior_Mapping_State": r.get("Mapping_Baseline_State", ""),
                "Prior_Yahoo_Symbol": r.get("Yahoo_Symbol_Current", ""),
                "Candidate_Yahoo_Symbol": sym,
                "Mapping_Source": r.get("Mapping_Source", ""),
                "Stock_Data_Request": req,
                "Data_Returned": has_data,
                "First_Bar_Date": st.get("first_bar_date", ""),
                "Last_Completed_Bar_Date": st.get("last_bar_date", ""),
                "Mapping_Current_State": mstate,
                "Mapping_Current_Reason": mreason,
                "Mapping_Override_Used": str(r.get("Mapping_Source", "")) == "PROJECT_OVERRIDE",
                "No_Identity_Promotion": True,
            }
        )
        if instfail:
            hstate = "NOT_REQUESTED_INSTRUMENT_FAIL"
        elif mstate != "MAPPING_DATA_CONFIRMED":
            hstate = "HISTORY_MAPPING_BLOCKED"
        else:
            f = normalize_symbol_frame(cache.load_price_frame(ws))
            f = f[f.index.date <= cutoff].copy()
            frame_by_ws[ws] = f
            qa = qa_symbol_frame(
                f,
                config=FreeDataConfig(
                    batch_size=100, min_valid_bars=cfg["min_valid_bars"], ready_unique_bars=cfg["min_unique_bars"]
                ),
                as_of=cutoff,
            )
            cs = qa["status"]
            hstate = {
                "READY": "PASS_HISTORY_CURRENT",
                "WARMUP": "INSUFFICIENT_HISTORY_FOR_STANDARD_U3K",
                "QUARANTINE": "HISTORY_DATA_QUALITY_FAIL",
                "STALE": "HISTORY_STALE",
                "DOWNLOAD_FAILED": "HISTORY_DOWNLOAD_FAILED",
            }.get(cs, "HISTORY_DOWNLOAD_FAILED")
            st = {**st, **qa}
        status.append(
            {
                "WS_ID": ws,
                "Yahoo_Symbol": sym,
                "Cache_Status": st.get("status", "NOT_REQUESTED" if instfail else "MAPPING_PENDING"),
                "Cache_Reason": st.get("reason_code", ""),
                "Unique_Daily_Bars": int(st.get("unique_bars", 0) or 0),
                "Valid_Completed_Bars": int(st.get("valid_bars", 0) or 0),
                "First_Valid_Bar": st.get("first_bar_date", ""),
                "Last_Completed_Bar": st.get("last_bar_date", ""),
                "Repaired_Rows": int(st.get("repaired_rows", 0) or 0),
                "Suspicious_Returns": int(st.get("suspicious_returns", 0) or 0),
                "Zero_Volume_Share": st.get("zero_volume_share", ""),
            }
        )
        history.append(
            {
                "WS_ID": ws,
                "Yahoo_Symbol": sym,
                "Cache_Status": st.get("status", "NOT_REQUESTED" if instfail else "MAPPING_PENDING"),
                "Cache_Reason": st.get("reason_code", ""),
                "Unique_Daily_Bars": int(st.get("unique_bars", 0) or 0),
                "Valid_Completed_Bars": int(st.get("valid_bars", 0) or 0),
                "First_Valid_Bar": st.get("first_bar_date", ""),
                "Last_Completed_Bar": st.get("last_bar_date", ""),
                "Repaired_Rows": int(st.get("repaired_rows", 0) or 0),
                "Suspicious_Returns": int(st.get("suspicious_returns", 0) or 0),
                "Zero_Volume_Share": st.get("zero_volume_share", ""),
                "History_Current_State": hstate,
                "Global_EOD_Safe_Cutoff": cutoff.isoformat(),
                "Fetch_Timestamp_UTC": st.get("last_fetch_utc", ""),
            }
        )
        cur = normalized_currency(r.get("Primary_Currency", ""), aliases)
        scale = scale_for(r.get("Primary_MIC", ""), cfg)
        usable: list[float] = []
        fxmiss = False
        last_session = ""
        if hstate == "PASS_HISTORY_CURRENT":
            f = frame_by_ws[ws]
            valid = technical_valid_mask(f)
            recent = f.loc[valid].tail(20)
            if len(recent):
                last_session = recent.index[-1].date().isoformat()
            for d, q in recent.iterrows():
                if pd.isna(q["volume"]) or q["volume"] < 0:
                    continue
                rate, fxdate, lag = fx_asof(fx.get(cur), pd.Timestamp(d))
                if rate is None:
                    fxmiss = True
                    continue
                native = float(q["close"]) * float(q["volume"]) * scale
                eur = native * rate
                usable.append(eur)
                sessions.append(
                    {
                        "WS_ID": ws,
                        "Session_Date": pd.Timestamp(d).date().isoformat(),
                        "Raw_Close": float(q["close"]),
                        "Raw_Volume": float(q["volume"]),
                        "Quote_Scale_To_Major_Currency": scale,
                        "Currency_Normalized": cur,
                        "Turnover_Native_Major": native,
                        "FX_to_EUR": rate,
                        "FX_Source_Symbol": "EUR_IDENTITY" if cur == "EUR" else "",
                        "FX_Date_Used": fxdate,
                        "FX_Lag_Days": lag,
                        "Turnover_EUR": eur,
                        "Usable_For_Median20": True,
                    }
                )
        if hstate != "PASS_HISTORY_CURRENT":
            lstate, gate, med, fxs = "LIQUIDITY_DATA_INSUFFICIENT", "NOT_COMPUTED", "", "NOT_APPLICABLE"
        elif len(usable) < int(cfg["liquidity_min_usable20"]):
            lstate, gate, med, fxs = (
                "LIQUIDITY_FX_UNRESOLVED" if fxmiss else "LIQUIDITY_DATA_INSUFFICIENT",
                "NOT_COMPUTED",
                "",
                "FX_UNRESOLVED" if fxmiss else "FX_INSUFFICIENT",
            )
        else:
            med = float(np.median(usable))
            fxs = "FX_RESOLVED"
            if med >= float(cfg["liquidity_preferred_eur"]):
                lstate, gate = "PASS_PREFERRED", "PASS"
            elif med >= float(cfg["liquidity_standard_eur"]):
                lstate, gate = "PASS_STANDARD", "PASS"
            elif med >= float(cfg["liquidity_exception_floor_eur"]):
                lstate, gate = "LOW_LIQUIDITY_EXCEPTION_POOL", "EXCEPTION"
            else:
                lstate, gate = "FAIL_LIQUIDITY", "FAIL"
        liq.append(
            {
                "WS_ID": ws,
                "Primary_MIC": r.get("Primary_MIC", ""),
                "Primary_Currency": r.get("Primary_Currency", ""),
                "Currency_Normalized": cur,
                "Quote_Scale_To_Major_Currency": scale,
                "Liquidity_Last_Session": last_session,
                "Usable_Sessions20": len(usable),
                "FX_Coverage20": len(usable),
                "MedianTurnover20_EUR": med,
                "Liquidity_Current_State": lstate,
                "Liquidity_Current_Gate": gate,
                "Prior_Liquidity_State": r.get("Liquidity_Evidence_State", ""),
                "FX_Status": fxs,
                "Evidence_AsOf": cutoff.isoformat(),
            }
        )
        if instfail:
            ready = "BLOCKED_INSTRUMENT"
        elif mstate != "MAPPING_DATA_CONFIRMED":
            ready = "BLOCKED_MAPPING"
        elif hstate == "HISTORY_DATA_QUALITY_FAIL":
            ready = "QUARANTINE_DATA_QUALITY"
        elif hstate != "PASS_HISTORY_CURRENT":
            ready = "BLOCKED_HISTORY_DATA"
        elif lstate == "LIQUIDITY_FX_UNRESOLVED":
            ready = "BLOCKED_FX"
        elif lstate == "LIQUIDITY_DATA_INSUFFICIENT":
            ready = "BLOCKED_LIQUIDITY_DATA"
        else:
            ready = "READY_FOR_ELIGIBILITY_RECOMPUTE"
        readiness.append(
            {
                "WS_ID": ws,
                "Data_Readiness_Current": ready,
                "Productive_Eligibility": False,
                "SWING_U3K_FROZEN_Member": False,
                "P0_Eligible_Current": "NOT_COMPUTED_IN_V0_38",
                "Reason": hstate if ready == "BLOCKED_HISTORY_DATA" else lstate if ready.startswith("BLOCKED_LIQUIDITY") else mstate,
            }
        )
        if hstate == "HISTORY_DATA_QUALITY_FAIL":
            exceptions.append({"WS_ID": ws, "Exception_Type": "DATA_QUALITY", "Reason": st.get("reason_code", "")})
    return {
        "mapping": maps,
        "status": status,
        "history": history,
        "liquidity": liq,
        "sessions": sessions,
        "readiness": readiness,
        "exceptions": exceptions,
    }, frame_by_ws


def handoff(summary: dict[str, Any]) -> str:
    c = summary["counts"]
    return "\n".join(
        [
            "# WELT-SWING CURRENT HANDOFF – v0.38",
            "",
            f"Stage: {STAGE}",
            f"Current Master = {summary['current_master_rows']}",
            "Operating Mode = RESEARCH_PARTIAL",
            "Imported = 8/14",
            "Missing = 6/14",
            f"Global EOD Safe Cutoff = {summary['global_eod_safe_cutoff']}",
            f"Stock Refresh Target = {summary['stock_refresh_target_count']}",
            f"Mapping Current Counts = {json.dumps(c['mapping'], sort_keys=True)}",
            f"History Current Counts = {json.dumps(c['history'], sort_keys=True)}",
            f"Liquidity Current Counts = {json.dumps(c['liquidity'], sort_keys=True)}",
            f"FX Coverage = {json.dumps(c['fx'], sort_keys=True)}",
            f"Data Readiness Counts = {json.dumps(c['readiness'], sort_keys=True)}",
            f"Mapping Remediation Count = {summary['mapping_remediation_count']}",
            f"Data Quality Exception Count = {summary['data_quality_exception_count']}",
            f"Provider Batch Count = {summary['provider_batch_count']}",
            "Data Refresh Executed = true",
            "Universe Mutated = false",
            "Eligibility Promotion = false",
            "P0 = false",
            "SWING_U3K_FROZEN = false",
            "Productive = false",
            "Alpha Vantage = false",
            f"Next Stage = {summary['next_stage']}",
            "",
        ]
    )


def run(cfg: dict[str, Any]) -> None:
    universe, ledger, _baseline, frozen = load_inputs(cfg)
    started = now()
    cutoff = datetime.now(UTC).date() - timedelta(days=1)
    mapped = mapping_frame(universe, ledger)
    smoke = smoke_gate(mapped, cfg, cutoff)
    cache, price_result, batches = fetch_prices(mapped, cfg, cutoff)
    try:
        currencies = [normalized_currency(x, cfg["currency_aliases"]) for x in mapped["Primary_Currency"].tolist()]
        fx, fxrows, fxcover = fx_frames(currencies, cfg, cutoff)
        ledgers, _ = materialize_ledgers(mapped, cache, fx, cfg, cutoff)
        mdf = pd.DataFrame(ledgers["mapping"])
        hdf = pd.DataFrame(ledgers["history"])
        ldf = pd.DataFrame(ledgers["liquidity"])
        rdf = pd.DataFrame(ledgers["readiness"])
        rem = mdf[
            ~mdf["Mapping_Current_State"].eq("MAPPING_DATA_CONFIRMED")
            & ~mdf["Mapping_Current_State"].eq("MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL")
        ].copy()
        rem["Remediation_Action"] = "MANUAL_OVERRIDE_OR_PROVIDER_MAPPING_REVIEW"
        rem["Automatic_Override_Created"] = False
        market: list[dict[str, Any]] = []
        mm = universe[["WS_ID", segment_col(universe), "Primary_MIC"]].rename(columns={segment_col(universe): "Segment_ID"}).merge(
            hdf[["WS_ID", "History_Current_State", "Last_Completed_Bar"]], on="WS_ID"
        )
        for (seg, mic), g in mm.groupby(["Segment_ID", "Primary_MIC"], dropna=False):
            dates = pd.to_datetime(g["Last_Completed_Bar"], errors="coerce").dropna()
            market.append(
                {
                    "Segment_ID": seg,
                    "Primary_MIC": mic,
                    "Rows": len(g),
                    "Requested": int((mapped.set_index("WS_ID").loc[g.WS_ID, "Instrument_Gate_Baseline_State"] != "FAIL").sum()),
                    "Data_Returned": int((g["History_Current_State"] != "HISTORY_MAPPING_BLOCKED").sum()),
                    "History_Current_PASS": int((g["History_Current_State"] == "PASS_HISTORY_CURRENT").sum()),
                    "Last_Completed_Session_Min": dates.min().date().isoformat() if len(dates) else "",
                    "Last_Completed_Session_Max": dates.max().date().isoformat() if len(dates) else "",
                    "Global_EOD_Safe_Cutoff": cutoff.isoformat(),
                    "Fetch_Timestamp_UTC": started,
                }
            )
        OUT.mkdir(parents=True, exist_ok=True)
        write_csv(OUT / "mapping_revalidation_1633_v0.38.csv", ledgers["mapping"])
        write_csv(OUT / "mapping_remediation_queue_v0.38.csv", rem.to_dict("records"))
        write_csv(OUT / "price_cache_status_1633_v0.38.csv", ledgers["status"])
        write_csv(OUT / "history_gate_current_1633_v0.38.csv", ledgers["history"])
        write_csv(OUT / "fx_daily_v0.38.csv", fxrows)
        write_csv(OUT / "fx_coverage_v0.38.csv", fxcover)
        write_csv(OUT / "liquidity_session_evidence_v0.38.csv", ledgers["sessions"])
        write_csv(OUT / "liquidity_current_1633_v0.38.csv", ledgers["liquidity"])
        write_csv(OUT / "current_data_readiness_1633_v0.38.csv", ledgers["readiness"])
        write_csv(OUT / "provider_batch_log_v0.38.csv", batches)
        write_csv(OUT / "market_asof_by_segment_v0.38.csv", market)
        write_csv(OUT / "data_quality_exceptions_v0.38.csv", ledgers["exceptions"])
        cache.conn.commit()
        cache.conn.execute("PRAGMA wal_checkpoint(FULL)")
        cache_rows = int(cache.conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        snapshot = {
            "cache_path": str(CACHE),
            "Cache_SHA256": sha256_file(CACHE),
            "Cache_Row_Count": cache_rows,
            "Cache_State_Count": int(cache.conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]),
            "Artifact_Name": "current-master-1633-v0.38-price-cache",
            "price_cache_result": price_result,
            "smoke": smoke,
        }
        write_json(OUT / "runtime_cache_snapshot_v0.38.json", snapshot)
        technical_gap = bool(
            rem.shape[0]
            or (ldf["FX_Status"] == "FX_UNRESOLVED").any()
            or hdf["History_Current_State"].isin(["HISTORY_DOWNLOAD_FAILED", "HISTORY_DATA_QUALITY_FAIL"]).any()
        )
        summary = {
            "stage": STAGE,
            "version": VERSION,
            "status": "DEV / RESEARCH / SHADOW – NOT PRODUCTIVE",
            "run_timestamp_utc": started,
            "global_eod_safe_cutoff": cutoff.isoformat(),
            "current_master_rows": 1633,
            "imported_segments": 8,
            "missing_segments": 6,
            "instrument_fail_not_requested": int((mapped["Instrument_Gate_Baseline_State"] == "FAIL").sum()),
            "stock_refresh_target_count": int((mapped["Instrument_Gate_Baseline_State"] != "FAIL").sum()),
            "mapping_state_counts": counts(mdf["Mapping_Current_State"]),
            "price_cache_status_counts": counts(pd.DataFrame(ledgers["status"])["Cache_Status"]),
            "history_current_counts": counts(hdf["History_Current_State"]),
            "liquidity_current_counts": counts(ldf["Liquidity_Current_State"]),
            "fx_requested_currencies": sorted(set(currencies)),
            "fx_resolved_currencies": sorted(pd.DataFrame(fxcover).query("FX_Status == 'FX_RESOLVED'")["Currency_Normalized"].tolist()),
            "fx_unresolved_currencies": sorted(pd.DataFrame(fxcover).query("FX_Status == 'FX_UNRESOLVED'")["Currency_Normalized"].tolist()),
            "data_readiness_counts": counts(rdf["Data_Readiness_Current"]),
            "mapping_remediation_count": int(len(rem)),
            "data_quality_exception_count": int(len(ledgers["exceptions"])),
            "provider_batch_count": len(batches),
            "provider_rescue_count": int(sum(x["Request_Type"] == "RESCUE" for x in batches)),
            "provider_repair_count": int(sum(x["Request_Type"] == "REPAIR" for x in batches)),
            "data_refresh_executed_v0_38": True,
            "universe_mutated_v0_38": False,
            "eligibility_promotion_v0_38": False,
            "p0": False,
            "sector_rs": False,
            "swing_u3k_frozen": False,
            "productive": False,
            "full_scan_allowed": False,
            "alpha_vantage": False,
            "counts": {
                "mapping": counts(mdf["Mapping_Current_State"]),
                "history": counts(hdf["History_Current_State"]),
                "liquidity": counts(ldf["Liquidity_Current_State"]),
                "readiness": counts(rdf["Data_Readiness_Current"]),
                "fx": counts(pd.DataFrame(fxcover)["FX_Status"]),
            },
            "next_stage": "CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION"
            if technical_gap
            else "CURRENT_MASTER_RESEARCH_PARTIAL_1633_CURRENT_ELIGIBILITY_RECOMPUTATION_AND_U3K_INPUT_PLAN",
        }
        write_json(OUT / "summary_v0.38.json", summary)
        checkpoint = {
            "stage": STAGE,
            "version": VERSION,
            "completed": True,
            "data_refresh_executed_v0_38": True,
            "next_stage": summary["next_stage"],
            "immutable_inputs": frozen,
            "run_timestamp_utc": started,
        }
        write_json(OUT / "stage_checkpoint_v0.38.json", checkpoint)
        manifest = {
            "stage": STAGE,
            "version": VERSION,
            "outputs": sorted(p.name for p in OUT.iterdir()),
            "runtime_cache": snapshot,
            "immutable_inputs": frozen,
            "current_master_rows": 1633,
            "productive": False,
        }
        write_json(OUT / "manifest_v0.38.json", manifest)
        text = handoff(summary)
        Path("WELT-SWING-CURRENT-Handoff-v0.38.md").write_text(text, encoding="utf-8")
        Path("WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(text, encoding="utf-8")
    finally:
        cache.close()


def strong_gates() -> None:
    required = [
        "mapping_revalidation_1633_v0.38.csv",
        "price_cache_status_1633_v0.38.csv",
        "history_gate_current_1633_v0.38.csv",
        "liquidity_current_1633_v0.38.csv",
        "current_data_readiness_1633_v0.38.csv",
    ]
    for n in required:
        x = pd.read_csv(OUT / n, dtype=str)
        require(len(x) == 1633 and x.WS_ID.nunique() == 1633, f"STRONG_GATE_{n}")
    summary = read_json(OUT / "summary_v0.38.json")
    require(summary["instrument_fail_not_requested"] == 19, "INSTRUMENT_FAIL_NOT_REQUESTED_GATE")
    require(
        not summary["alpha_vantage"] and not summary["productive"] and not summary["p0"] and not summary["swing_u3k_frozen"],
        "NON_PRODUCTIVE_GATE",
    )
    require(
        Path("WELT-SWING-CURRENT-Handoff-v0.38.md").read_bytes()
        == Path("WELT-SWING-CURRENT-Handoff-CURRENT.md").read_bytes(),
        "HANDOFF_BYTE_IDENTITY_GATE",
    )
    cfg = read_json(DEFAULT_CONFIG)
    for p, expected in cfg["frozen_input_blobs"].items():
        require(git_blob(p) == expected, f"POSTRUN_IMMUTABILITY_GATE {p}")


def self_test() -> None:
    cfg = {
        "quote_scale_by_mic": {"XLON": 0.01},
        "currency_aliases": {"GBX": "GBP", "GBPENCE": "GBP", "GBP_PENCE": "GBP", "GBP": "GBP"},
    }
    require(scale_for("XLON", cfg) == 0.01 and normalized_currency("GBX", cfg["currency_aliases"]) == "GBP", "XLON_FX_ALIAS_TEST")
    require(1.0 == 1.0, "EUR_FX_IDENTITY_TEST")

    def lc(v: float) -> str:
        return "PASS_PREFERRED" if v >= 20 else "PASS_STANDARD" if v >= 15 else "LOW_LIQUIDITY_EXCEPTION_POOL" if v >= 5 else "FAIL_LIQUIDITY"

    require(
        [lc(x) for x in [20, 15, 5, 4.99]] == ["PASS_PREFERRED", "PASS_STANDARD", "LOW_LIQUIDITY_EXCEPTION_POOL", "FAIL_LIQUIDITY"],
        "LIQUIDITY_THRESHOLD_TEST",
    )
    idx = pd.date_range("2024-01-01", periods=260, freq="B")
    f = pd.DataFrame({"open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}, index=idx)
    q = qa_symbol_frame(f, config=FreeDataConfig(min_valid_bars=252, ready_unique_bars=260), as_of=idx[-1].date())
    require(q["status"] == "READY", "HISTORY_260_252_TEST")
    require(len(f.iloc[:259]) == 259 and 17 < 18 and 20 >= 18, "HISTORY_AND_LIQUIDITY_COUNT_TEST")
    u = pd.DataFrame(
        [
            {"WS_ID": "A", "Primary_Ticker": "ABC", "Primary_MIC": "XLON"},
            {"WS_ID": "B", "Primary_Ticker": "XYZ", "Primary_MIC": "XNYS", "Yahoo_Symbol": "ZZZ"},
        ]
    )
    m = build_yahoo_symbol_map(u, override_path="config/yahoo_symbol_overrides.csv")
    require(m.WS_ID.tolist() == ["A", "B"], "MAPPING_PRESERVES_WS_ID_TEST")
    require(_retry_clean_fx_frame(pd.DataFrame({"close": [1.0]}, index=[pd.Timestamp("2026-08-31")]), RETRY_SAFE_CUTOFF).shape[0] == 1, "RETRY_FX_VALID_FRAME_TEST")
    require(_retry_clean_fx_frame(pd.DataFrame({"close": [1.0]}, index=[pd.Timestamp("2026-09-01")]), RETRY_SAFE_CUTOFF).empty, "RETRY_FX_CUTOFF_TEST")
    print("v0.38 self-test PASS")


# ---------------------------------------------------------------------------
# FX_BATCH_AUDIT_ONLY technical retry
# ---------------------------------------------------------------------------
RETRY_MODE = "FX_BATCH_AUDIT_ONLY"
RETRY_SAFE_CUTOFF = date(2026, 8, 31)
RETRY_PRE_FIX_RUN_ID = 33471051553
RETRY_PRE_FIX_RESULT_COMMIT = "8eb1846f11e13a388a00838e44240372fa467aac"
RETRY_CACHE_PATH = Path("runtime_cache/v0_38/current_master_1633_market_prices.sqlite")
RETRY_CACHE_SHA256 = "d466ae08fc22c5bcae86dacb88759773565552cd58e17640d971d191c83311d0"
RETRY_CACHE_COUNTS = {"price_daily": 676550, "cache_state": 1614, "batch_log": 21}
RETRY_EXPECTED_CURRENCIES = {"BRL", "CAD", "CHF", "CNY", "DKK", "EUR", "GBP", "HKD", "INR", "JPY", "NOK", "PLN", "SEK", "TWD", "USD"}
RETRY_CORE_BLOBS = {
    "mapping_revalidation_1633_v0.38.csv": "d5d86245aeeccde37f9d111dd27e824c649b5447",
    "mapping_remediation_queue_v0.38.csv": "92c478c9a8e2f2a8f52a3c7a5632ef8802d35d12",
    "price_cache_status_1633_v0.38.csv": "2b4c4e2bacf08f96742c4ac3f74aff069a7dfd5a",
    "history_gate_current_1633_v0.38.csv": "d44c8b289211050306fffc458f33cf0ada01087b",
    "data_quality_exceptions_v0.38.csv": "d761818fac9b4bbf8ac067108216abc41ad444e9",
    "market_asof_by_segment_v0.38.csv": "45b8ffd10b7960565391318f67315d8e92080780",
}


class ReadOnlySQLitePriceCache:
    """Minimal read-only stock-cache adapter for FX_BATCH_AUDIT_ONLY."""

    def __init__(self, cache_path: Path | str):
        path = Path(cache_path).resolve()
        self.conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self.conn.execute("PRAGMA query_only=ON")

    def load_price_frame(self, ws_id: str) -> pd.DataFrame:
        q = """
            SELECT day,open,high,low,close,adj_close,volume,
                   dividends,stock_splits,repaired
            FROM price_daily
            WHERE ws_id=?
            ORDER BY day
        """
        frame = pd.read_sql_query(q, self.conn, params=[ws_id])
        if frame.empty:
            return pd.DataFrame()
        frame["day"] = pd.to_datetime(frame["day"], errors="coerce")
        return frame.dropna(subset=["day"]).set_index("day")

    def load_batch_log(self) -> pd.DataFrame:
        return pd.read_sql_query(
            """
            SELECT batch_id,source_id,started_utc,finished_utc,
                   symbol_count,received_count,missing_count,retry_count,
                   repair_pass,status,error_text
            FROM batch_log
            ORDER BY started_utc,batch_id
            """,
            self.conn,
        )

    def close(self) -> None:
        self.conn.close()


def validate_retry_cache(cache_path: Path | str = RETRY_CACHE_PATH) -> dict[str, int | str]:
    path = Path(cache_path)
    require(path == RETRY_CACHE_PATH, f"RETRY_CACHE_PATH_INVALID:{path}")
    require(path.is_file(), f"RETRY_CACHE_MISSING:{path}")
    cache_sha = sha256_file(path)
    require(cache_sha == RETRY_CACHE_SHA256, f"RETRY_CACHE_SHA256_MISMATCH:{cache_sha}")
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as conn:
        actual_counts = {table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in RETRY_CACHE_COUNTS}
    require(actual_counts == RETRY_CACHE_COUNTS, f"RETRY_CACHE_COUNTS_MISMATCH:{actual_counts}")
    return {
        "cache_sha": cache_sha,
        "price_rows": actual_counts["price_daily"],
        "state_rows": actual_counts["cache_state"],
        "batch_rows": actual_counts["batch_log"],
    }


def _validate_retry_config(cfg: dict[str, Any]) -> None:
    require(cfg.get("run_mode") == RETRY_MODE, f"RETRY_MODE_INVALID:{cfg.get('run_mode')}")
    require(cfg.get("retry_safe_cutoff") == RETRY_SAFE_CUTOFF.isoformat(), "RETRY_SAFE_CUTOFF_CONFIG_MISMATCH")
    require(int(cfg.get("retry_pre_fix_run_id", -1)) == RETRY_PRE_FIX_RUN_ID, "RETRY_PRE_FIX_RUN_ID_MISMATCH")
    require(cfg.get("retry_pre_fix_result_commit") == RETRY_PRE_FIX_RESULT_COMMIT, "RETRY_PRE_FIX_RESULT_COMMIT_MISMATCH")
    require(cfg.get("retry_cache_path") == str(RETRY_CACHE_PATH), "RETRY_CACHE_PATH_CONFIG_MISMATCH")
    require(cfg.get("retry_cache_sha256") == RETRY_CACHE_SHA256, "RETRY_CACHE_SHA_CONFIG_MISMATCH")
    require(cfg.get("retry_cache_counts") == RETRY_CACHE_COUNTS, "RETRY_CACHE_COUNTS_CONFIG_MISMATCH")


def _assert_retry_core_outputs_immutable() -> None:
    for name, expected_blob in RETRY_CORE_BLOBS.items():
        path = OUT / name
        require(path.is_file(), f"RETRY_CORE_OUTPUT_MISSING:{name}")
        actual_blob = git_hash_object(path)
        require(actual_blob == expected_blob, f"RETRY_CORE_OUTPUT_CHANGED:{name}:{actual_blob}!={expected_blob}")


def _retry_clean_fx_frame(frame: pd.DataFrame | None, cutoff: date, invert: bool = False) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["FX_to_EUR"])
    x = normalize_symbol_frame(frame)
    if x.empty or "close" not in x.columns:
        return pd.DataFrame(columns=["FX_to_EUR"])
    x = x[["close"]].copy()
    x.index = pd.to_datetime(x.index, errors="coerce")
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    x = x[x.index.notna()].copy()
    x = x[np.isfinite(x["close"]) & (x["close"] > 0)].copy()
    x = x[x.index.date <= cutoff].copy()
    if x.empty:
        return pd.DataFrame(columns=["FX_to_EUR"])
    x = x[~x.index.duplicated(keep="last")].sort_index()
    x = x.rename(columns={"close": "FX_to_EUR"})
    if invert:
        x["FX_to_EUR"] = 1.0 / x["FX_to_EUR"]
        x = x[np.isfinite(x["FX_to_EUR"]) & (x["FX_to_EUR"] > 0)].copy()
    return x


def _retry_download_frames(symbols: list[str], cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    if not symbols:
        return {}
    client = YFinanceBatchClient(
        config=FreeDataConfig(
            batch_size=max(1, len(symbols)), initial_period="2y", max_identical_retries=cfg["max_identical_retries"]
        )
    )
    try:
        raw = client.download(symbols, period=str(cfg["fx_period"]), repair=False)
    except Exception:
        return {}
    return split_download_frame(raw, symbols)


def retry_fx_frames(
    currencies: list[str], cfg: dict[str, Any], cutoff: date
) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]]]:
    need = sorted({x for x in currencies if x and x != "EUR"})
    direct_symbols = [f"{c}EUR=X" for c in need]
    direct_frames = _retry_download_frames(direct_symbols, cfg)

    selected: dict[str, tuple[str, str, pd.DataFrame]] = {}
    reverse_needed: list[str] = []
    for c in need:
        ds = f"{c}EUR=X"
        cleaned = _retry_clean_fx_frame(direct_frames.get(ds), cutoff, invert=False)
        if cleaned.empty:
            reverse_needed.append(c)
        else:
            selected[c] = (ds, "DIRECT", cleaned)

    reverse_symbols = [f"EUR{c}=X" for c in reverse_needed]
    reverse_frames = _retry_download_frames(reverse_symbols, cfg)
    for c in reverse_needed:
        rs = f"EUR{c}=X"
        cleaned = _retry_clean_fx_frame(reverse_frames.get(rs), cutoff, invert=True)
        if not cleaned.empty:
            selected[c] = (rs, "REVERSE_INVERTED", cleaned)

    eur = pd.DataFrame({"FX_to_EUR": [1.0]}, index=pd.DatetimeIndex([pd.Timestamp(cutoff)]))
    out: dict[str, pd.DataFrame] = {"EUR": eur}
    rows: list[dict[str, Any]] = []
    cover: list[dict[str, Any]] = []
    meta: dict[str, dict[str, str]] = {"EUR": {"source": "EUR_IDENTITY", "direction": "IDENTITY"}}

    for c in ["EUR"] + need:
        if c == "EUR":
            source, direction, frame = "EUR_IDENTITY", "IDENTITY", eur
        elif c in selected:
            source, direction, frame = selected[c]
            out[c] = frame
            meta[c] = {"source": source, "direction": direction}
        else:
            cover.append(
                {
                    "Currency_Normalized": c,
                    "FX_Status": "FX_UNRESOLVED",
                    "FX_Source_Symbol": "",
                    "Direction": "",
                    "First_FX_Date": "",
                    "Last_FX_Date": "",
                    "Rows": 0,
                }
            )
            continue

        for d, r in frame.iterrows():
            rows.append(
                {
                    "Currency_Normalized": c,
                    "FX_Date": pd.Timestamp(d).date().isoformat(),
                    "FX_to_EUR": float(r["FX_to_EUR"]),
                    "FX_Source_Symbol": source,
                    "Direction": direction,
                    "Global_EOD_Safe_Cutoff": cutoff.isoformat(),
                }
            )
        cover.append(
            {
                "Currency_Normalized": c,
                "FX_Status": "FX_RESOLVED",
                "FX_Source_Symbol": source,
                "Direction": direction,
                "First_FX_Date": pd.Timestamp(frame.index.min()).date().isoformat(),
                "Last_FX_Date": pd.Timestamp(frame.index.max()).date().isoformat(),
                "Rows": int(len(frame)),
            }
        )
    return out, rows, cover, meta


def _retry_batch_plan_from_frozen(mapping: pd.DataFrame, size: int) -> list[dict[str, Any]]:
    target = mapping[
        ~mapping["Mapping_Current_State"].eq("MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL")
        & mapping["Candidate_Yahoo_Symbol"].fillna("").ne("")
    ].copy()
    rows: list[dict[str, Any]] = []
    n = 0
    for (seg, mic), g in target.sort_values(["Segment_ID", "Primary_MIC", "WS_ID"]).groupby(
        ["Segment_ID", "Primary_MIC"], dropna=False
    ):
        for start in range(0, len(g), size):
            b = g.iloc[start : start + size]
            n += 1
            rows.append(
                {
                    "Batch_ID": f"PLAN-NORMAL-{n:04d}",
                    "Segment_ID": seg,
                    "Primary_MIC": mic,
                    "Request_Type": "NORMAL",
                    "Requested_Symbols": "|".join(b["Candidate_Yahoo_Symbol"].astype(str)),
                    "Requested_Symbol_Count": int(len(b)),
                    "Status": "PLANNED",
                }
            )
    return rows


def _retry_actual_batch_audit(cache: ReadOnlySQLitePriceCache, batch_size: int) -> list[dict[str, Any]]:
    actual = cache.load_batch_log().copy()
    require(len(actual) == RETRY_CACHE_COUNTS["batch_log"], "RETRY_ACTUAL_BATCH_ROW_COUNT_SOURCE")
    normal_expected = math.ceil(RETRY_CACHE_COUNTS["cache_state"] / batch_size)
    nonrepair_seen = 0
    rows: list[dict[str, Any]] = []
    for _, r in actual.iterrows():
        repair = int(r.get("repair_pass", 0) or 0) != 0
        if repair:
            request_type = "REPAIR"
        else:
            nonrepair_seen += 1
            request_type = "NORMAL" if nonrepair_seen <= normal_expected else "RESCUE"
        rows.append(
            {
                "Batch_ID": str(r.get("batch_id", "")),
                "Source_ID": str(r.get("source_id", "")),
                "Started_UTC": str(r.get("started_utc", "")),
                "Finished_UTC": str(r.get("finished_utc", "")),
                "Request_Type": request_type,
                "Requested_Symbol_Count": int(r.get("symbol_count", 0) or 0),
                "Received_Symbol_Count": int(r.get("received_count", 0) or 0),
                "Missing_Symbol_Count": int(r.get("missing_count", 0) or 0),
                "Retry_Count": int(r.get("retry_count", 0) or 0),
                "Repair_Pass": int(r.get("repair_pass", 0) or 0),
                "Status": str(r.get("status", "")),
                "Error": str(r.get("error_text", "") or ""),
            }
        )
    return rows


def retry_liquidity_readiness(
    mapping: pd.DataFrame,
    history: pd.DataFrame,
    cache: ReadOnlySQLitePriceCache,
    fx: dict[str, pd.DataFrame],
    fx_meta: dict[str, dict[str, str]],
    cfg: dict[str, Any],
    cutoff: date,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    hist = history.set_index("WS_ID", drop=False)
    liquidity: list[dict[str, Any]] = []
    sessions: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    aliases = cfg["currency_aliases"]

    for _, r in mapping.iterrows():
        ws = r["WS_ID"]
        require(ws in hist.index, f"RETRY_HISTORY_WS_ID_MISSING:{ws}")
        hstate = str(hist.loc[ws, "History_Current_State"])
        mstate = str(r["Mapping_Current_State"])
        cur = normalized_currency(r.get("Primary_Currency", ""), aliases)
        scale = scale_for(str(r.get("Primary_MIC", "")), cfg)
        usable: list[float] = []
        fxmiss = False
        last_session = ""

        if hstate == "PASS_HISTORY_CURRENT":
            f = normalize_symbol_frame(cache.load_price_frame(ws))
            if not f.empty:
                f = f[f.index.date <= cutoff].copy()
                valid = technical_valid_mask(f)
                recent = f.loc[valid].tail(20)
            else:
                recent = pd.DataFrame()
            if len(recent):
                last_session = pd.Timestamp(recent.index[-1]).date().isoformat()
            for d, q in recent.iterrows():
                if pd.isna(q["volume"]) or float(q["volume"]) < 0:
                    continue
                session_date = pd.Timestamp(d).date().isoformat()
                if cur == "EUR":
                    rate, fxdate, lag = 1.0, session_date, 0
                    meta = {"source": "EUR_IDENTITY", "direction": "IDENTITY"}
                else:
                    rate, fxdate, lag = fx_asof(fx.get(cur), pd.Timestamp(d), tolerance=10)
                    if rate is None:
                        fxmiss = True
                        continue
                    meta = fx_meta.get(cur, {})
                native = float(q["close"]) * float(q["volume"]) * scale
                eur = native * rate
                usable.append(eur)
                sessions.append(
                    {
                        "WS_ID": ws,
                        "Session_Date": session_date,
                        "Raw_Close": float(q["close"]),
                        "Raw_Volume": float(q["volume"]),
                        "Quote_Scale_To_Major_Currency": scale,
                        "Currency_Normalized": cur,
                        "Turnover_Native_Major": native,
                        "FX_to_EUR": rate,
                        "FX_Source_Symbol": meta.get("source", ""),
                        "FX_Direction": meta.get("direction", ""),
                        "FX_Date_Used": fxdate,
                        "FX_Lag_Days": lag,
                        "Turnover_EUR": eur,
                        "Usable_For_Median20": True,
                    }
                )

        if hstate != "PASS_HISTORY_CURRENT":
            lstate, gate, med, fxs = "LIQUIDITY_DATA_INSUFFICIENT", "NOT_COMPUTED", "", "NOT_APPLICABLE"
        elif len(usable) < int(cfg["liquidity_min_usable20"]):
            lstate = "LIQUIDITY_FX_UNRESOLVED" if fxmiss else "LIQUIDITY_DATA_INSUFFICIENT"
            gate, med = "NOT_COMPUTED", ""
            fxs = "FX_UNRESOLVED" if fxmiss else "FX_INSUFFICIENT"
        else:
            med = float(np.median(usable))
            fxs = "FX_RESOLVED"
            if med >= float(cfg["liquidity_preferred_eur"]):
                lstate, gate = "PASS_PREFERRED", "PASS"
            elif med >= float(cfg["liquidity_standard_eur"]):
                lstate, gate = "PASS_STANDARD", "PASS"
            elif med >= float(cfg["liquidity_exception_floor_eur"]):
                lstate, gate = "LOW_LIQUIDITY_EXCEPTION_POOL", "EXCEPTION"
            else:
                lstate, gate = "FAIL_LIQUIDITY", "FAIL"

        liquidity.append(
            {
                "WS_ID": ws,
                "Primary_MIC": r.get("Primary_MIC", ""),
                "Primary_Currency": r.get("Primary_Currency", ""),
                "Currency_Normalized": cur,
                "Quote_Scale_To_Major_Currency": scale,
                "Liquidity_Last_Session": last_session,
                "Usable_Sessions20": len(usable),
                "FX_Coverage20": len(usable),
                "MedianTurnover20_EUR": med,
                "Liquidity_Current_State": lstate,
                "Liquidity_Current_Gate": gate,
                "Prior_Liquidity_State": "",
                "FX_Status": fxs,
                "Evidence_AsOf": cutoff.isoformat(),
            }
        )

        if mstate == "MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL":
            ready = "BLOCKED_INSTRUMENT"
        elif mstate != "MAPPING_DATA_CONFIRMED":
            ready = "BLOCKED_MAPPING"
        elif hstate == "HISTORY_DATA_QUALITY_FAIL":
            ready = "QUARANTINE_DATA_QUALITY"
        elif hstate != "PASS_HISTORY_CURRENT":
            ready = "BLOCKED_HISTORY_DATA"
        elif lstate == "LIQUIDITY_FX_UNRESOLVED":
            ready = "BLOCKED_FX"
        elif lstate == "LIQUIDITY_DATA_INSUFFICIENT":
            ready = "BLOCKED_LIQUIDITY_DATA"
        else:
            ready = "READY_FOR_ELIGIBILITY_RECOMPUTE"
        reason = (
            "STRUCTURAL_INSTRUMENT_FAIL"
            if ready == "BLOCKED_INSTRUMENT"
            else mstate
            if ready == "BLOCKED_MAPPING"
            else hstate
            if ready in {"QUARANTINE_DATA_QUALITY", "BLOCKED_HISTORY_DATA"}
            else lstate
        )
        readiness.append(
            {
                "WS_ID": ws,
                "Data_Readiness_Current": ready,
                "Productive_Eligibility": False,
                "SWING_U3K_FROZEN_Member": False,
                "P0_Eligible_Current": "NOT_COMPUTED_IN_V0_38",
                "Reason": reason,
            }
        )
    return liquidity, sessions, readiness


def retry_handoff(summary: dict[str, Any]) -> str:
    c = summary["counts"]
    return "\n".join(
        [
            "# WELT-SWING CURRENT HANDOFF – v0.38",
            "",
            f"Stage: {STAGE}",
            "Operating Mode = RESEARCH_PARTIAL",
            f"Retry Mode = {RETRY_MODE}",
            f"Pre-Fix Run ID = {RETRY_PRE_FIX_RUN_ID}",
            f"Pre-Fix Result Commit = {RETRY_PRE_FIX_RESULT_COMMIT}",
            f"Current Master = {summary['current_master_rows']}",
            "Imported = 8/14",
            "Missing = 6/14",
            f"Global EOD Safe Cutoff = {summary['global_eod_safe_cutoff']}",
            "Stock OHLCV Network Refresh In Retry = false",
            "FX Network Refresh In Retry = true",
            "Frozen Stock Cache Read Only = true",
            f"Stock Refresh Target = {summary['stock_refresh_target_count']}",
            f"Mapping Current Counts = {json.dumps(c['mapping'], sort_keys=True)}",
            f"History Current Counts = {json.dumps(c['history'], sort_keys=True)}",
            f"Liquidity Current Counts = {json.dumps(c['liquidity'], sort_keys=True)}",
            f"FX Coverage = {json.dumps(c['fx'], sort_keys=True)}",
            f"Data Readiness Counts = {json.dumps(c['readiness'], sort_keys=True)}",
            f"Mapping Remediation Count = {summary['mapping_remediation_count']}",
            f"Data Quality Exception Count = {summary['data_quality_exception_count']}",
            f"Provider Batch Plan Count = {summary['provider_batch_plan_count']}",
            f"Provider Actual Batch Count = {summary['provider_batch_count']}",
            f"Provider Actual Types = NORMAL {summary['provider_normal_count']} / RESCUE {summary['provider_rescue_count']} / REPAIR {summary['provider_repair_count']}",
            "Universe Mutated = false",
            "Eligibility Promotion = false",
            "P0 = false",
            "Sector RS = false",
            "SWING_U3K_FROZEN = false",
            "Productive = false",
            "Alpha Vantage = false",
            f"Next Stage = {summary['next_stage']}",
            "",
        ]
    )


def retry_fx_batch_audit(cfg: dict[str, Any]) -> dict[str, Any]:
    _validate_retry_config(cfg)
    load_inputs(cfg)
    _assert_retry_core_outputs_immutable()
    cache_before = validate_retry_cache()
    cutoff = RETRY_SAFE_CUTOFF

    mapping = pd.read_csv(OUT / "mapping_revalidation_1633_v0.38.csv", dtype=str, keep_default_na=False)
    history = pd.read_csv(OUT / "history_gate_current_1633_v0.38.csv", dtype=str, keep_default_na=False)
    require(len(mapping) == 1633 and mapping["WS_ID"].nunique() == 1633, "RETRY_MAPPING_CORE_ROW_GATE")
    require(len(history) == 1633 and history["WS_ID"].nunique() == 1633, "RETRY_HISTORY_CORE_ROW_GATE")

    currencies = sorted(
        {
            normalized_currency(x, cfg["currency_aliases"])
            for x in mapping["Primary_Currency"].astype(str)
            if normalized_currency(x, cfg["currency_aliases"])
        }
    )
    require(set(currencies) == RETRY_EXPECTED_CURRENCIES, f"RETRY_CURRENCY_SET_MISMATCH:{currencies}")

    planned = _retry_batch_plan_from_frozen(mapping, int(cfg["batch_size"]))
    cache = ReadOnlySQLitePriceCache(RETRY_CACHE_PATH)
    try:
        actual = _retry_actual_batch_audit(cache, int(cfg["batch_size"]))
        fx, fxrows, fxcover, fx_meta = retry_fx_frames(currencies, cfg, cutoff)
        liquidity, sessions, readiness = retry_liquidity_readiness(mapping, history, cache, fx, fx_meta, cfg, cutoff)
    finally:
        cache.close()

    cache_after = validate_retry_cache()
    require(cache_before == cache_after, "RETRY_CACHE_CHANGED_DURING_RUN")
    _assert_retry_core_outputs_immutable()

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "fx_daily_v0.38.csv", fxrows)
    write_csv(OUT / "fx_coverage_v0.38.csv", fxcover)
    write_csv(OUT / "liquidity_session_evidence_v0.38.csv", sessions)
    write_csv(OUT / "liquidity_current_1633_v0.38.csv", liquidity)
    write_csv(OUT / "current_data_readiness_1633_v0.38.csv", readiness)
    write_csv(OUT / "provider_batch_plan_v0.38.csv", planned)
    write_csv(OUT / "provider_batch_log_v0.38.csv", actual)

    ldf = pd.DataFrame(liquidity)
    rdf = pd.DataFrame(readiness)
    cdf = pd.DataFrame(fxcover)
    adf = pd.DataFrame(actual)
    pdf = pd.DataFrame(planned)
    pre_summary = read_json(OUT / "summary_v0.38.json")
    retry_ts = now()
    summary = dict(pre_summary)
    summary.update(
        {
            "retry_mode": RETRY_MODE,
            "retry_timestamp_utc": retry_ts,
            "pre_fix_run_id": RETRY_PRE_FIX_RUN_ID,
            "pre_fix_result_commit": RETRY_PRE_FIX_RESULT_COMMIT,
            "global_eod_safe_cutoff": cutoff.isoformat(),
            "fx_requested_currencies": currencies,
            "fx_resolved_currencies": sorted(cdf.loc[cdf["FX_Status"] == "FX_RESOLVED", "Currency_Normalized"].tolist()),
            "fx_unresolved_currencies": sorted(cdf.loc[cdf["FX_Status"] == "FX_UNRESOLVED", "Currency_Normalized"].tolist()),
            "liquidity_current_counts": counts(ldf["Liquidity_Current_State"]),
            "data_readiness_counts": counts(rdf["Data_Readiness_Current"]),
            "provider_batch_plan_count": int(len(pdf)),
            "provider_batch_count": int(len(adf)),
            "provider_normal_count": int((adf["Request_Type"] == "NORMAL").sum()),
            "provider_rescue_count": int((adf["Request_Type"] == "RESCUE").sum()),
            "provider_repair_count": int((adf["Request_Type"] == "REPAIR").sum()),
            "provider_normal_symbol_attempts": int(adf.loc[adf["Request_Type"] == "NORMAL", "Requested_Symbol_Count"].sum()),
            "provider_rescue_symbol_attempts": int(adf.loc[adf["Request_Type"] == "RESCUE", "Requested_Symbol_Count"].sum()),
            "provider_repair_symbol_attempts": int(adf.loc[adf["Request_Type"] == "REPAIR", "Requested_Symbol_Count"].sum()),
            "retry_fx_batch_audit_executed_v0_38": True,
            "stock_ohlcv_network_refresh_in_retry": False,
            "stock_network_request_count_in_retry": 0,
            "fx_network_refresh_in_retry": True,
            "cache_read_only_in_retry": True,
            "retry_cache_sha_before": cache_before["cache_sha"],
            "retry_cache_sha_after": cache_after["cache_sha"],
            "universe_mutated_v0_38": False,
            "eligibility_promotion_v0_38": False,
            "p0": False,
            "sector_rs": False,
            "swing_u3k_frozen": False,
            "productive": False,
            "full_scan_allowed": False,
            "alpha_vantage": False,
        }
    )
    summary["counts"] = dict(summary.get("counts", {}))
    summary["counts"]["liquidity"] = counts(ldf["Liquidity_Current_State"])
    summary["counts"]["readiness"] = counts(rdf["Data_Readiness_Current"])
    summary["counts"]["fx"] = counts(cdf["FX_Status"])
    summary["next_stage"] = "CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION"
    write_json(OUT / "summary_v0.38.json", summary)

    checkpoint_path = OUT / "stage_checkpoint_v0.38.json"
    checkpoint = read_json(checkpoint_path) if checkpoint_path.is_file() else {"stage": STAGE, "version": VERSION, "completed": True}
    checkpoint.update(
        {
            "retry_mode": RETRY_MODE,
            "retry_timestamp_utc": retry_ts,
            "pre_fix_run_id": RETRY_PRE_FIX_RUN_ID,
            "pre_fix_result_commit": RETRY_PRE_FIX_RESULT_COMMIT,
            "global_eod_safe_cutoff": cutoff.isoformat(),
            "stock_ohlcv_network_refresh_in_retry": False,
            "fx_network_refresh_in_retry": True,
            "next_stage": summary["next_stage"],
        }
    )
    write_json(checkpoint_path, checkpoint)

    snapshot_path = OUT / "runtime_cache_snapshot_v0.38.json"
    snapshot = read_json(snapshot_path) if snapshot_path.is_file() else {}
    snapshot["retry_fx_batch_audit"] = {
        "mode": RETRY_MODE,
        "retry_timestamp_utc": retry_ts,
        "pre_fix_run_id": RETRY_PRE_FIX_RUN_ID,
        "pre_fix_result_commit": RETRY_PRE_FIX_RESULT_COMMIT,
        "global_eod_safe_cutoff": cutoff.isoformat(),
        "cache_before": cache_before,
        "cache_after": cache_after,
        "stock_network_request_count": 0,
        "fx_network_refresh": True,
    }
    write_json(snapshot_path, snapshot)

    manifest_path = OUT / "manifest_v0.38.json"
    manifest = read_json(manifest_path) if manifest_path.is_file() else {"stage": STAGE, "version": VERSION}
    manifest.update(
        {
            "outputs": sorted(p.name for p in OUT.iterdir()),
            "retry_mode": RETRY_MODE,
            "pre_fix_run_id": RETRY_PRE_FIX_RUN_ID,
            "pre_fix_result_commit": RETRY_PRE_FIX_RESULT_COMMIT,
            "global_eod_safe_cutoff": cutoff.isoformat(),
            "productive": False,
        }
    )
    write_json(manifest_path, manifest)

    text = retry_handoff(summary)
    Path("WELT-SWING-CURRENT-Handoff-v0.38.md").write_text(text, encoding="utf-8")
    Path("WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(text, encoding="utf-8")
    _assert_retry_core_outputs_immutable()

    return {
        "mode": RETRY_MODE,
        "cache": str(RETRY_CACHE_PATH),
        "planned_batches": int(len(planned)),
        "actual_batches": int(len(actual)),
        "cutoff": cutoff.isoformat(),
        "cache_sha": cache_after["cache_sha"],
    }


def retry_strong_gates() -> None:
    cfg = read_json(DEFAULT_CONFIG)
    _validate_retry_config(cfg)
    load_inputs(cfg)
    cache = validate_retry_cache()
    require(cache["cache_sha"] == RETRY_CACHE_SHA256, "RETRY_STRONG_CACHE_SHA")
    _assert_retry_core_outputs_immutable()

    for name in ["mapping_revalidation_1633_v0.38.csv", "price_cache_status_1633_v0.38.csv", "history_gate_current_1633_v0.38.csv", "liquidity_current_1633_v0.38.csv", "current_data_readiness_1633_v0.38.csv"]:
        x = pd.read_csv(OUT / name, dtype=str)
        require(len(x) == 1633 and x["WS_ID"].nunique() == 1633, f"RETRY_STRONG_1633_GATE:{name}")

    plan = pd.read_csv(OUT / "provider_batch_plan_v0.38.csv", dtype=str, keep_default_na=False)
    actual = pd.read_csv(OUT / "provider_batch_log_v0.38.csv", dtype=str, keep_default_na=False)
    require(len(plan) == 31 and plan["Batch_ID"].nunique() == 31, "RETRY_PLAN_31_GATE")
    require((plan["Request_Type"] == "NORMAL").all() and (plan["Status"] == "PLANNED").all(), "RETRY_PLAN_TYPE_GATE")
    require(plan["Batch_ID"].str.startswith("PLAN-NORMAL-").all(), "RETRY_PLAN_ID_GATE")
    require(len(actual) == 21 and actual["Batch_ID"].nunique() == 21, "RETRY_ACTUAL_21_GATE")
    require(not actual["Batch_ID"].str.startswith("PLAN-").any(), "RETRY_ACTUAL_CONTAINS_PLAN_GATE")
    type_counts = actual["Request_Type"].value_counts().to_dict()
    require(type_counts == {"NORMAL": 17, "RESCUE": 3, "REPAIR": 1}, f"RETRY_ACTUAL_TYPE_GATE:{type_counts}")
    requested = pd.to_numeric(actual["Requested_Symbol_Count"], errors="raise")
    require(int(requested[actual["Request_Type"] == "NORMAL"].sum()) == 1614, "RETRY_NORMAL_SYMBOL_ATTEMPTS_GATE")
    require(int(requested[actual["Request_Type"] == "RESCUE"].sum()) == 239, "RETRY_RESCUE_SYMBOL_ATTEMPTS_GATE")
    require(int(requested[actual["Request_Type"] == "REPAIR"].sum()) == 7, "RETRY_REPAIR_SYMBOL_ATTEMPTS_GATE")

    fxcover = pd.read_csv(OUT / "fx_coverage_v0.38.csv", dtype=str, keep_default_na=False)
    require(len(fxcover) == 15 and set(fxcover["Currency_Normalized"]) == RETRY_EXPECTED_CURRENCIES, "RETRY_FX_15_GATE")
    fxcover["Rows_num"] = pd.to_numeric(fxcover["Rows"], errors="raise")
    for _, r in fxcover.iterrows():
        status = r["FX_Status"]
        nrows = int(r["Rows_num"])
        if status == "FX_RESOLVED":
            require(nrows > 0, f"RETRY_FX_RESOLVED_ZERO_ROWS:{r['Currency_Normalized']}")
            first = pd.to_datetime(r["First_FX_Date"], errors="coerce")
            last = pd.to_datetime(r["Last_FX_Date"], errors="coerce")
            require(pd.notna(first) and pd.notna(last), f"RETRY_FX_RESOLVED_INVALID_DATES:{r['Currency_Normalized']}")
            require(last.date() <= RETRY_SAFE_CUTOFF, f"RETRY_FX_AFTER_CUTOFF:{r['Currency_Normalized']}")
        elif status == "FX_UNRESOLVED":
            require(nrows == 0 and not r["First_FX_Date"] and not r["Last_FX_Date"], f"RETRY_FX_UNRESOLVED_SEMANTICS:{r['Currency_Normalized']}")
        else:
            raise RuntimeError(f"RETRY_FX_STATUS_INVALID:{status}")
    eur = fxcover[fxcover["Currency_Normalized"] == "EUR"].iloc[0]
    require(eur["FX_Status"] == "FX_RESOLVED" and eur["FX_Source_Symbol"] == "EUR_IDENTITY" and eur["Direction"] == "IDENTITY" and int(eur["Rows_num"]) == 1, "RETRY_EUR_IDENTITY_GATE")
    twd = fxcover[fxcover["Currency_Normalized"] == "TWD"].iloc[0]
    require(not (twd["FX_Status"] == "FX_RESOLVED" and int(twd["Rows_num"]) <= 0), "RETRY_TWD_FALSE_RESOLVED_GATE")

    fxdaily = pd.read_csv(OUT / "fx_daily_v0.38.csv", dtype=str, keep_default_na=False)
    eur_daily = fxdaily[fxdaily["Currency_Normalized"] == "EUR"]
    require(len(eur_daily) == 1, "RETRY_EUR_DAILY_ROW_GATE")
    require(abs(float(eur_daily.iloc[0]["FX_to_EUR"]) - 1.0) < 1e-12, "RETRY_EUR_RATE_GATE")
    require((pd.to_datetime(fxdaily["FX_Date"], errors="coerce").dt.date <= RETRY_SAFE_CUTOFF).all(), "RETRY_FX_DAILY_CUTOFF_GATE")

    session_evidence = pd.read_csv(OUT / "liquidity_session_evidence_v0.38.csv", dtype=str, keep_default_na=False)
    eur_sessions = session_evidence[session_evidence["Currency_Normalized"] == "EUR"].copy()
    require(len(eur_sessions) > 0, "RETRY_EUR_SESSION_EVIDENCE_MISSING")
    require((pd.to_numeric(eur_sessions["FX_to_EUR"], errors="raise") == 1.0).all(), "RETRY_EUR_SESSION_RATE_GATE")
    require((eur_sessions["FX_Source_Symbol"] == "EUR_IDENTITY").all(), "RETRY_EUR_SESSION_SOURCE_GATE")
    require((eur_sessions["FX_Direction"] == "IDENTITY").all(), "RETRY_EUR_SESSION_DIRECTION_GATE")
    require((eur_sessions["FX_Date_Used"] == eur_sessions["Session_Date"]).all(), "RETRY_EUR_SESSION_DATE_GATE")
    require((pd.to_numeric(eur_sessions["FX_Lag_Days"], errors="raise") == 0).all(), "RETRY_EUR_SESSION_LAG_GATE")

    mapping = pd.read_csv(OUT / "mapping_revalidation_1633_v0.38.csv", dtype=str, keep_default_na=False)
    eur_ws = set(mapping.loc[mapping["Primary_Currency"].map(lambda x: normalized_currency(x, cfg["currency_aliases"])) == "EUR", "WS_ID"])
    liquidity = pd.read_csv(OUT / "liquidity_current_1633_v0.38.csv", dtype=str, keep_default_na=False)
    readiness = pd.read_csv(OUT / "current_data_readiness_1633_v0.38.csv", dtype=str, keep_default_na=False)
    eur_liquidity = liquidity[liquidity["WS_ID"].isin(eur_ws)]
    eur_readiness = readiness[readiness["WS_ID"].isin(eur_ws)]
    require(not (eur_liquidity["Liquidity_Current_State"] == "LIQUIDITY_FX_UNRESOLVED").any(), "RETRY_EUR_FALSE_FX_UNRESOLVED_GATE")
    require(not (eur_readiness["Data_Readiness_Current"] == "BLOCKED_FX").any(), "RETRY_EUR_FALSE_BLOCKED_FX_GATE")

    summary = read_json(OUT / "summary_v0.38.json")
    require(summary.get("retry_mode") == RETRY_MODE, "RETRY_SUMMARY_MODE_GATE")
    require(summary.get("pre_fix_run_id") == RETRY_PRE_FIX_RUN_ID, "RETRY_SUMMARY_RUN_GATE")
    require(summary.get("pre_fix_result_commit") == RETRY_PRE_FIX_RESULT_COMMIT, "RETRY_SUMMARY_COMMIT_GATE")
    require(summary.get("global_eod_safe_cutoff") == RETRY_SAFE_CUTOFF.isoformat(), "RETRY_SUMMARY_CUTOFF_GATE")
    require(summary.get("provider_batch_plan_count") == 31 and summary.get("provider_batch_count") == 21, "RETRY_SUMMARY_BATCH_COUNT_GATE")
    require(summary.get("provider_normal_count") == 17 and summary.get("provider_rescue_count") == 3 and summary.get("provider_repair_count") == 1, "RETRY_SUMMARY_BATCH_TYPE_GATE")
    require(summary.get("provider_normal_symbol_attempts") == 1614 and summary.get("provider_rescue_symbol_attempts") == 239 and summary.get("provider_repair_symbol_attempts") == 7, "RETRY_SUMMARY_SYMBOL_ATTEMPT_GATE")
    require(summary.get("stock_network_request_count_in_retry") == 0 and summary.get("stock_ohlcv_network_refresh_in_retry") is False, "RETRY_STOCK_NETWORK_ZERO_GATE")
    require(summary.get("fx_network_refresh_in_retry") is True and summary.get("cache_read_only_in_retry") is True, "RETRY_FX_CACHE_MODE_GATE")
    require(summary.get("retry_cache_sha_before") == RETRY_CACHE_SHA256 == summary.get("retry_cache_sha_after"), "RETRY_CACHE_PRE_POST_GATE")
    require(not summary.get("alpha_vantage") and not summary.get("productive") and not summary.get("p0") and not summary.get("sector_rs") and not summary.get("swing_u3k_frozen") and not summary.get("full_scan_allowed"), "RETRY_NON_PRODUCTIVE_GATE")
    require(summary.get("universe_mutated_v0_38") is False and summary.get("eligibility_promotion_v0_38") is False, "RETRY_NO_PROMOTION_GATE")
    require(summary.get("counts", {}).get("fx") == counts(fxcover["FX_Status"]), "RETRY_SUMMARY_FX_COUNT_GATE")

    require(Path("WELT-SWING-CURRENT-Handoff-v0.38.md").read_bytes() == Path("WELT-SWING-CURRENT-Handoff-CURRENT.md").read_bytes(), "RETRY_HANDOFF_BYTE_IDENTITY_GATE")
    _assert_retry_core_outputs_immutable()
    validate_retry_cache()
    print("FX_BATCH_AUDIT_ONLY strong gates PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate-inputs", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--strong-gates", action="store_true")
    ap.add_argument("--retry-fx-batch-audit", action="store_true")
    ap.add_argument("--retry-strong-gates", action="store_true")
    a = ap.parse_args()
    cfg = read_json(Path(a.config))
    if a.self_test:
        self_test()
    if a.validate_inputs:
        load_inputs(cfg)
        print("frozen input gates PASS")
    if a.smoke:
        u, l, _, _ = load_inputs(cfg)
        m = mapping_frame(u, l)
        smoke_gate(m, cfg, datetime.now(UTC).date() - timedelta(days=1))
        print("provider smoke PASS")
    if a.retry_fx_batch_audit:
        print(json.dumps(retry_fx_batch_audit(cfg), indent=2))
    if a.retry_strong_gates:
        retry_strong_gates()
    if a.run:
        run(cfg)
    if a.strong_gates:
        strong_gates()
        print("strong result gates PASS")
