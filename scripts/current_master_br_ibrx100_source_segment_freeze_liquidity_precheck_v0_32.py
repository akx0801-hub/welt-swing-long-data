#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

SCHEMA = "WELT_SWING_CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK_V0_32"
STAGE_ID = "CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK"
VERSION = "v0.32"
LINEAGE = "CURRENT_MASTER_CLEAN_RESTART"
SEGMENT_ID = "BR_IBRX100"
PRIMARY_MIC = "BVMF"
PROVIDER = "YFINANCE_FREE"
TURNOVER_METHOD = "PRICE_X_VOLUME_TURNOVER_APPROXIMATION"
FX_SYMBOL = "EURBRL=X"
SOURCE_SEMANTICS = "OFFICIAL_B3_HEADER_DATE_UNINTERPRETED"
NEXT_STAGE = "CURRENT_MASTER_BR_IBRX100_ELIGIBILITY_GATE_COMPLETION_AND_CONTROLLED_SEGMENT_IMPORT_PLAN"

PASS_PREFERRED = "PASS_PREFERRED"
PASS_STANDARD = "PASS_STANDARD"
LOW_LIQUIDITY_EXCEPTION_POOL = "LOW_LIQUIDITY_EXCEPTION_POOL"
FAIL_LIQUIDITY = "FAIL_LIQUIDITY"
DATA_NOT_READY_QUARANTINE = "DATA_NOT_READY_QUARANTINE"
LIQUIDITY_CLASSES = [
    PASS_PREFERRED,
    PASS_STANDARD,
    LOW_LIQUIDITY_EXCEPTION_POOL,
    FAIL_LIQUIDITY,
    DATA_NOT_READY_QUARANTINE,
]


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


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items: dict[str, str]) -> str:
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().eq("true")


def git_safe_float(v: Any) -> float | None:
    try:
        n = float(v)
    except Exception:
        return None
    if pd.isna(n):
        return None
    return n


def classify_liquidity(median_eur: float | None, ready: bool, thresholds: dict) -> str:
    if not ready or median_eur is None:
        return DATA_NOT_READY_QUARANTINE
    if median_eur >= float(thresholds["preferred_eur"]):
        return PASS_PREFERRED
    if median_eur >= float(thresholds["standard_eur"]):
        return PASS_STANDARD
    if median_eur >= float(thresholds["exception_pool_eur"]):
        return LOW_LIQUIDITY_EXCEPTION_POOL
    return FAIL_LIQUIDITY


def yahoo_symbol(primary_ticker: str) -> str:
    ticker = txt(primary_ticker).upper()
    require(re.fullmatch(r"[A-Z0-9]{4,8}", ticker) is not None, f"Invalid B3 primary ticker: {ticker!r}")
    return f"{ticker}.SA"


def session_date(v: Any) -> str:
    return pd.Timestamp(v).date().isoformat()


def extract_symbol_frame(raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            level0 = list(raw.columns.get_level_values(0))
            leveln = list(raw.columns.get_level_values(-1))
            if symbol in level0:
                frame = raw.xs(symbol, axis=1, level=0, drop_level=True).copy()
            elif symbol in leveln:
                frame = raw.xs(symbol, axis=1, level=-1, drop_level=True).copy()
            else:
                return pd.DataFrame()
        else:
            frame = raw.copy()
    except Exception:
        return pd.DataFrame()

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = ["_".join(str(x) for x in c if str(x)) for c in frame.columns]
    frame.columns = [str(c).strip() for c in frame.columns]
    frame = frame.loc[:, ~frame.columns.duplicated()].copy()
    frame["Date"] = [session_date(x) for x in frame.index]
    return frame.reset_index(drop=True)


def download_with_one_retry(symbols: list[str], start: str, end: str, threads: bool) -> tuple[pd.DataFrame, str]:
    last_error = ""
    for attempt in range(2):
        try:
            data = yf.download(
                tickers=symbols,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                actions=False,
                progress=False,
                threads=threads,
                group_by="ticker",
                timeout=30,
            )
            if data is not None and not data.empty:
                return data, ""
            last_error = f"EMPTY_RESPONSE_ATTEMPT_{attempt + 1}"
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
    return pd.DataFrame(), last_error[:500]


def validate_frozen_inputs(cfg: dict, inp: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, dict, dict]:
    master = inp["master_spec"].read_text(encoding="utf-8")
    summary31 = read_json(inp["v031_summary"])
    checkpoint31 = read_json(inp["v031_checkpoint"])
    identity = read_csv(inp["v031_identity_reconciliation"])
    strict = read_csv(inp["v031_strict_ordinary"])
    exclusions = read_csv(inp["v031_instrument_exclusions"])
    raw_b3 = read_json(inp["v030_b3_raw"])
    handoff = inp["current_handoff"].read_text(encoding="utf-8")

    require("WELT-SWING LONG DEV v0.1" in master, "DEV master identity missing")
    require("Alpha Vantage" in master and "vollständig ausgeschlossen" in master, "Master Alpha-Vantage prohibition missing")
    require("MedianTurnover20_EUR" in master, "Master liquidity metric missing")
    require("20 Mio. EUR" in master and "15 Mio. EUR" in master and "5–15 Mio. EUR" in master, "Master liquidity thresholds missing")

    require(summary31["lineage_scope"] == LINEAGE, "v0.31 lineage mismatch")
    require(summary31["stage_status"] == "PARTIAL", "v0.31 stage classification mismatch")
    require(summary31["current_master_rows_before"] == 1535, "v0.31 current-master before count changed")
    require(summary31["current_master_rows_after"] == 1535, "v0.31 current-master after count changed")
    require(summary31["br_ibrx100_counts"]["rows"] == 98, "v0.31 official B3 membership count changed")
    require(summary31["br_ibrx100_counts"]["identity_pass"] == 98, "v0.31 identity PASS count changed")
    require(summary31["br_ibrx100_counts"]["strict_candidates"] == 79, "v0.31 strict candidate count changed")
    require(summary31["br_ibrx100_counts"]["instrument_fail"] == 19, "v0.31 instrument FAIL count changed")
    require(summary31["br_ibrx100_counts"]["preferred_share"] == 12, "v0.31 preferred count changed")
    require(summary31["br_ibrx100_counts"]["unit"] == 7, "v0.31 unit count changed")
    require(summary31["br_ibrx100_counts"]["instrument_not_verified"] == 0, "v0.31 instrument NOT VERIFIED changed")
    require(summary31["br_primary_mic"] == PRIMARY_MIC, "v0.31 primary MIC changed")
    require(summary31["br_isin_guessed"] is False, "v0.31 guessed-ISIN gate changed")
    require(summary31["br_ibrx100_source_asof"] == "2026-08-31", "v0.31 source as-of changed")
    require(summary31["universe_mutated"] is False, "v0.31 universe mutation detected")
    require(summary31["next_stage"] == STAGE_ID, "v0.31 next-stage mismatch")

    require(checkpoint31["stage_version"] == "v0.31", "v0.31 checkpoint version mismatch")
    require(checkpoint31["lineage_scope"] == LINEAGE, "v0.31 checkpoint lineage mismatch")
    require(checkpoint31["input_count"] == 98 and checkpoint31["checked_count"] == 98, "v0.31 checkpoint membership counts changed")
    require(checkpoint31["pass_count"] == 79 and checkpoint31["fail_count"] == 19, "v0.31 checkpoint pass/fail changed")
    require(checkpoint31["quarantine_count"] == 0, "v0.31 checkpoint quarantine changed")
    require(checkpoint31["status"] == "PARTIAL", "v0.31 checkpoint status changed")
    require(checkpoint31["next_stage"] == STAGE_ID, "v0.31 checkpoint next-stage mismatch")

    required_columns = {
        "WS_ID_Candidate", "ISIN", "Primary_MIC", "Primary_Ticker",
        "Security_Name_Official", "Instrument_Type_v0_31", "Instrument_Gate_v0_31",
        "Identity_Gate_v0_31", "Source_AsOf_Official_Display", "Source_AsOf_Official",
        "Source_AsOf_Semantics", "Strict_Ordinary_Identity_Candidate_v0_31",
        "Canonical_Master_Import_v0_31",
    }
    require(required_columns.issubset(identity.columns), "v0.31 identity schema missing required columns")
    require(len(identity) == 98, "v0.31 identity ledger row count changed")
    require(identity["WS_ID_Candidate"].nunique() == 98, "v0.31 identity WS_ID duplicate")
    require(identity["Primary_Ticker"].nunique() == 98, "v0.31 identity ticker duplicate")
    require(identity["Primary_MIC"].eq(PRIMARY_MIC).all(), "v0.31 identity contains non-BVMF market")
    require(identity["Identity_Gate_v0_31"].eq("PASS").all(), "v0.31 identity contains non-PASS row")
    require(identity["ISIN"].eq("").all(), "v0.31 identity unexpectedly contains ISIN")
    require(identity["Source_AsOf_Official_Display"].eq("31/08/26").all(), "B3 display date changed")
    require(identity["Source_AsOf_Official"].eq("2026-08-31").all(), "B3 source date changed")
    require(identity["Source_AsOf_Semantics"].eq(SOURCE_SEMANTICS).all(), "B3 date semantics changed")
    require(not bool_series(identity["Canonical_Master_Import_v0_31"]).any(), "v0.31 canonical import detected")

    require(len(strict) == 79, "v0.31 strict ordinary row count changed")
    require(strict["WS_ID_Candidate"].nunique() == 79, "v0.31 strict WS_ID duplicate")
    require(strict["Primary_Ticker"].nunique() == 79, "v0.31 strict ticker duplicate")
    require(strict["Primary_MIC"].eq(PRIMARY_MIC).all(), "v0.31 strict contains non-BVMF")
    require(strict["Instrument_Type_v0_31"].eq("ORDINARY_SHARE").all(), "v0.31 strict contains non-ordinary instrument")
    require(strict["Instrument_Gate_v0_31"].eq("PASS").all(), "v0.31 strict contains instrument non-PASS")
    require(strict["Identity_Gate_v0_31"].eq("PASS").all(), "v0.31 strict contains identity non-PASS")
    require(strict["ISIN"].eq("").all(), "v0.31 strict unexpectedly contains ISIN")
    require(bool_series(strict["Strict_Ordinary_Identity_Candidate_v0_31"]).all(), "v0.31 strict marker changed")

    require(len(exclusions) == 19, "v0.31 exclusions row count changed")
    require(exclusions["Instrument_Type_v0_31"].isin(["PREFERRED_SHARE", "UNIT"]).all(), "v0.31 exclusions contain unexpected type")
    require(exclusions["Instrument_Gate_v0_31"].eq("FAIL").all(), "v0.31 exclusions contain non-FAIL")
    require(set(exclusions["WS_ID_Candidate"]).isdisjoint(set(strict["WS_ID_Candidate"])), "Excluded instrument leaked into strict set")
    require(int(exclusions["Instrument_Type_v0_31"].eq("PREFERRED_SHARE").sum()) == 12, "Preferred-share exclusion count changed")
    require(int(exclusions["Instrument_Type_v0_31"].eq("UNIT").sum()) == 7, "Unit exclusion count changed")

    require(raw_b3.get("page", {}).get("totalRecords") == 98, "B3 raw totalRecords changed")
    require(len(raw_b3.get("results", [])) == 98, "B3 raw results count changed")
    require(raw_b3.get("header", {}).get("date") == "31/08/26", "B3 raw header.date changed")
    raw_codes = [txt(x.get("cod")).upper() for x in raw_b3["results"]]
    require(len(set(raw_codes)) == 98, "B3 raw codes not unique")
    require(set(raw_codes) == set(identity["Primary_Ticker"]), "B3 raw/identity membership mismatch")

    require("Version:** v0.31" in handoff, "Expected v0.31 CURRENT handoff predecessor")
    require("CURRENT_MASTER_CLEAN_RESTART" in handoff, "CURRENT handoff lineage missing")
    return identity, strict, exclusions, raw_b3, summary31, checkpoint31


def prepare_fx(raw_fx: pd.DataFrame, cutoff_date: str) -> pd.DataFrame:
    frame = extract_symbol_frame(raw_fx, FX_SYMBOL)
    if frame.empty or "Close" not in frame.columns:
        return pd.DataFrame(columns=["Date", "EURBRL", "Provider"])
    frame["EURBRL"] = pd.to_numeric(frame["Close"], errors="coerce")
    frame = frame.loc[(frame["Date"] < cutoff_date) & frame["EURBRL"].gt(0), ["Date", "EURBRL"]].copy()
    frame = frame.drop_duplicates("Date", keep="last").sort_values("Date")
    frame["Provider"] = PROVIDER
    return frame.reset_index(drop=True)


def process_security(row: pd.Series, raw_prices: pd.DataFrame, fx: pd.DataFrame, cutoff_date: str, required_sessions: int, thresholds: dict, provider_error: str) -> tuple[dict, dict, list[dict]]:
    ws_id = txt(row["WS_ID_Candidate"])
    ticker = txt(row["Primary_Ticker"]).upper()
    mic = txt(row["Primary_MIC"])
    name = txt(row["Security_Name_Official"])
    instrument_type = txt(row["Instrument_Type_v0_31"])
    source_asof = txt(row["Source_AsOf_Official"])
    symbol = yahoo_symbol(ticker)

    frame = extract_symbol_frame(raw_prices, symbol)
    if not frame.empty:
        for col in ["Close", "Volume"]:
            if col not in frame.columns:
                frame[col] = pd.NA
        frame["Close_BRL"] = pd.to_numeric(frame["Close"], errors="coerce")
        frame["Volume"] = pd.to_numeric(frame["Volume"], errors="coerce")
        frame = frame.loc[frame["Date"] < cutoff_date, ["Date", "Close_BRL", "Volume"]].copy()
        frame = frame.loc[~(frame["Close_BRL"].isna() & frame["Volume"].isna())]
        frame = frame.drop_duplicates("Date", keep="last").sort_values("Date")
    else:
        frame = pd.DataFrame(columns=["Date", "Close_BRL", "Volume"])

    raw_sessions = int(len(frame))
    invalid_price_rows = int((frame["Close_BRL"].isna() | frame["Close_BRL"].le(0)).sum()) if raw_sessions else 0
    invalid_volume_rows = int((frame["Volume"].isna() | frame["Volume"].le(0)).sum()) if raw_sessions else 0

    if len(fx):
        left = frame.copy()
        left["_Date"] = pd.to_datetime(left["Date"])
        right = fx.rename(columns={"Date": "EURBRL_Source_Date"}).copy()
        right["_FX_Date"] = pd.to_datetime(right["EURBRL_Source_Date"])
        aligned = pd.merge_asof(
            left.sort_values("_Date"),
            right.sort_values("_FX_Date"),
            left_on="_Date",
            right_on="_FX_Date",
            direction="backward",
            allow_exact_matches=True,
        )
        aligned = aligned.drop(columns=["_Date", "_FX_Date"], errors="ignore")
    else:
        aligned = frame.copy()
        aligned["EURBRL_Source_Date"] = ""
        aligned["EURBRL"] = pd.NA
        aligned["Provider"] = PROVIDER

    if "EURBRL" not in aligned.columns:
        aligned["EURBRL"] = pd.NA
    if "EURBRL_Source_Date" not in aligned.columns:
        aligned["EURBRL_Source_Date"] = ""

    aligned["Price_Valid"] = aligned["Close_BRL"].gt(0)
    aligned["Volume_Valid"] = aligned["Volume"].gt(0)
    aligned["FX_Valid"] = pd.to_numeric(aligned["EURBRL"], errors="coerce").gt(0)
    aligned["Session_Valid"] = aligned["Price_Valid"] & aligned["Volume_Valid"] & aligned["FX_Valid"]
    aligned["Turnover_BRL"] = aligned["Close_BRL"] * aligned["Volume"]
    aligned["Turnover_EUR"] = aligned["Turnover_BRL"] / pd.to_numeric(aligned["EURBRL"], errors="coerce")

    missing_fx_rows = int((aligned["Price_Valid"] & aligned["Volume_Valid"] & ~aligned["FX_Valid"]).sum())
    valid = aligned.loc[aligned["Session_Valid"]].copy().sort_values("Date")
    valid_sessions = int(len(valid))
    last20 = valid.tail(required_sessions)

    mapping_state = "RESOLVED_FORMAT_AND_OHLCV" if raw_sessions and frame["Close_BRL"].gt(0).any() else "UNRESOLVED_YFINANCE_SYMBOL"
    if mic != PRIMARY_MIC:
        dq_state = "QUARANTINE_UNKNOWN_OR_WRONG_MARKET"
        dq_reason = f"PRIMARY_MIC_{mic or 'MISSING'}"
    elif symbol != f"{ticker}.SA":
        dq_state = "QUARANTINE_MAPPING_CONFLICT"
        dq_reason = "YAHOO_SYMBOL_MAPPING_CONFLICT"
    elif raw_sessions == 0:
        dq_state = "QUARANTINE_SYMBOL_UNRESOLVED"
        dq_reason = provider_error or "NO_PRICE_ROWS"
    elif not frame["Close_BRL"].gt(0).any():
        dq_state = "QUARANTINE_PRICE_INVALID"
        dq_reason = "NO_POSITIVE_CLOSE"
    elif not frame["Volume"].gt(0).any():
        dq_state = "QUARANTINE_VOLUME_INVALID"
        dq_reason = "NO_POSITIVE_VOLUME"
    elif len(fx) == 0 or missing_fx_rows == raw_sessions:
        dq_state = "QUARANTINE_FX_MISSING"
        dq_reason = "NO_BACKWARD_ALIGNED_EURBRL"
    elif valid_sessions < required_sessions:
        dq_state = "DATA_NOT_READY"
        dq_reason = f"VALID_SESSIONS_{valid_sessions}_LT_{required_sessions}"
    else:
        dq_state = "READY"
        dq_reason = "PASS_20_VALID_COMPLETED_PRIMARY_SESSIONS"

    ready = dq_state == "READY"
    median_brl = float(last20["Turnover_BRL"].median()) if ready else None
    median_eur = float(last20["Turnover_EUR"].median()) if ready else None
    price_asof = txt(last20["Date"].iloc[-1]) if len(last20) else (txt(valid["Date"].iloc[-1]) if len(valid) else "")
    fx_asof = txt(last20["EURBRL_Source_Date"].iloc[-1]) if len(last20) else (txt(valid["EURBRL_Source_Date"].iloc[-1]) if len(valid) else "")
    liquidity_class = classify_liquidity(median_eur, ready, thresholds)

    ledger = {
        "WS_ID": ws_id,
        "Primary_MIC": mic,
        "Primary_Ticker": ticker,
        "Yahoo_Symbol": symbol,
        "Security_Name": name,
        "Instrument_Type": instrument_type,
        "Source_AsOf_Official": source_asof,
        "Price_AsOf": price_asof,
        "Valid_Sessions": valid_sessions,
        "MedianTurnover20_BRL": round(median_brl, 2) if median_brl is not None else "",
        "MedianTurnover20_EUR": round(median_eur, 2) if median_eur is not None else "",
        "EURBRL_AsOf": fx_asof,
        "Liquidity_Class": liquidity_class,
        "Data_Quality_State": dq_state,
        "Provider": PROVIDER,
        "Mapping_State": mapping_state,
        "Turnover_Method": TURNOVER_METHOD,
        "Eligibility_Promotion_v0_32": False,
        "Canonical_Master_Import_v0_32": False,
    }
    dq = {
        "WS_ID": ws_id,
        "Primary_MIC": mic,
        "Primary_Ticker": ticker,
        "Yahoo_Symbol": symbol,
        "Security_Name": name,
        "Instrument_Type": instrument_type,
        "Source_AsOf_Official": source_asof,
        "Raw_Sessions": raw_sessions,
        "Valid_Sessions": valid_sessions,
        "Invalid_Price_Rows": invalid_price_rows,
        "Invalid_Volume_Rows": invalid_volume_rows,
        "Missing_FX_Rows": missing_fx_rows,
        "Price_AsOf": price_asof,
        "EURBRL_AsOf": fx_asof,
        "Mapping_State": mapping_state,
        "Data_Quality_State": dq_state,
        "Data_Quality_Reason": dq_reason,
        "Provider": PROVIDER,
    }

    history: list[dict] = []
    for _, x in aligned.iterrows():
        close = git_safe_float(x.get("Close_BRL"))
        volume = git_safe_float(x.get("Volume"))
        fx_value = git_safe_float(x.get("EURBRL"))
        turnover_brl = git_safe_float(x.get("Turnover_BRL"))
        turnover_eur = git_safe_float(x.get("Turnover_EUR"))
        history.append({
            "WS_ID": ws_id,
            "Primary_MIC": mic,
            "Primary_Ticker": ticker,
            "Yahoo_Symbol": symbol,
            "Security_Name": name,
            "Instrument_Type": instrument_type,
            "Date": txt(x.get("Date")),
            "Close_BRL": round(close, 8) if close is not None else "",
            "Volume": round(volume, 4) if volume is not None else "",
            "Turnover_BRL": round(turnover_brl, 2) if turnover_brl is not None else "",
            "EURBRL": round(fx_value, 8) if fx_value is not None else "",
            "EURBRL_Source_Date": txt(x.get("EURBRL_Source_Date")),
            "Turnover_EUR": round(turnover_eur, 2) if turnover_eur is not None else "",
            "Price_Valid": bool(x.get("Price_Valid", False)),
            "Volume_Valid": bool(x.get("Volume_Valid", False)),
            "FX_Valid": bool(x.get("FX_Valid", False)),
            "Session_Valid": bool(x.get("Session_Valid", False)),
            "Provider": PROVIDER,
            "Turnover_Method": TURNOVER_METHOD,
        })
    return ledger, dq, history


def write_handoff(versioned: Path, stable: Path, summary: dict, checkpoint: dict) -> None:
    counts = summary["liquidity_class_counts"]
    body = f"""# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.32  
**Generated UTC:** {summary['generated_utc']}  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Primary lineage:** CURRENT_MASTER_CLEAN_RESTART  
**Trigger/input commit:** {os.environ.get('GITHUB_SHA', 'LOCAL_OR_UNKNOWN')}

## 1. Authority

Authoritative DEV master:
docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md

Welt-Swing v7.2 remains solely authoritative for productive Swing decisions. Alpha Vantage remains forbidden.

## 2. Current-master universe

The canonical development snapshot remains unchanged at **1,535 securities from 7 of 14 target segments**.

v0.32 freezes the official Brazil source segment and performs a non-productive liquidity precheck only.

- Canonical Master Import v0.32: false
- Eligibility Promotion v0.32: false
- Universe Mutated: false
- P0: false
- Sector RS: false
- SWING_U3K_FROZEN: false
- Source Superset Complete: false

## 3. Brazil source-segment freeze

- Official B3 / IBrX 100 source frozen: {summary['source_frozen_rows']}
- Strict Ordinary frozen: {summary['strict_ordinary_frozen_rows']}
- Instrument FAIL retained outside Strict: {summary['instrument_fail_rows']}
  - Preferred Shares: {summary['preferred_share_fail_rows']}
  - Units: {summary['unit_fail_rows']}
- Instrument NOT VERIFIED: {summary['instrument_not_verified_rows']}
- Primary MIC: BVMF
- Source_AsOf_Official: {summary['source_asof_official']}
- Source_AsOf_Semantics: {summary['source_asof_semantics']}
- No ISIN was guessed.

## 4. Liquidity precheck

Only the 79 Strict Ordinary candidates were checked.

- Provider: {summary['provider']}
- Yahoo market mapping: Primary_Ticker.SA
- FX symbol: {summary['fx_symbol']}
- Turnover method: {summary['turnover_method']}
- Required valid completed sessions: {summary['required_valid_sessions']}
- Price_AsOf: {summary['price_asof']}
- EURBRL_AsOf: {summary['eurbrl_asof']}

Result counts:
- PASS_PREFERRED: {counts[PASS_PREFERRED]}
- PASS_STANDARD: {counts[PASS_STANDARD]}
- LOW_LIQUIDITY_EXCEPTION_POOL: {counts[LOW_LIQUIDITY_EXCEPTION_POOL]}
- FAIL_LIQUIDITY: {counts[FAIL_LIQUIDITY]}
- DATA_NOT_READY / QUARANTINE: {counts[DATA_NOT_READY_QUARANTINE]}

Turnover is an explicit PRICE_X_VOLUME_TURNOVER_APPROXIMATION and is not directly reported B3 turnover.

PASS_PREFERRED or PASS_STANDARD means only that the liquidity precheck passed. It is not eligibility promotion and not canonical import.

## 5. Global stage classification

Stage status remains **PARTIAL** because the full 14-segment source superset is incomplete.

No P0 run, no productive scan and no productive trading authority are created by v0.32.

## 6. Current checkpoint

- Stage: {checkpoint['stage_id']}
- Run ID: {checkpoint['run_id']}
- Status: {checkpoint['status']}
- Input count: {checkpoint['input_count']}
- Checked count: {checkpoint['checked_count']}
- Data error / quarantine count: {checkpoint['quarantine_count']}
- Output hash: {checkpoint['output_hash']}
- Next stage: {checkpoint['next_stage']}

## 7. Recovery order

1. docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md
2. WELT-SWING-CURRENT-Handoff-CURRENT.md
3. output_current_master_br_ibrx100_liquidity_v0_32/stage_checkpoint_v0.32.json
4. output_current_master_br_ibrx100_liquidity_v0_32/manifest_v0.32.json
5. output_current_master_br_ibrx100_liquidity_v0_32/summary_v0.32.json
6. output_current_master_br_ibrx100_liquidity_v0_32/br_ibrx100_liquidity_precheck_v0.32.csv
7. output_current_master_br_ibrx100_liquidity_v0_32/br_ibrx100_price_data_quality_v0.32.csv
8. universe/segments/br_ibrx100_source_frozen_v0.32.csv
9. universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv
10. output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_identity_reconciliation_v0.31.csv
11. output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_strict_ordinary_candidates_v0.31.csv
12. output_current_master_source_deep_materialization_v0_30/b3_ibrx100_official_raw_v0.30.json
13. universe/Welt-Swing-Universe-Master-v2.0.xlsx

## 8. Next stage

{NEXT_STAGE}

This is a PLAN stage only. v0.32 performs no controlled segment import.
"""
    versioned.write_text(body, encoding="utf-8")
    stable.write_text(body, encoding="utf-8")
    require(versioned.read_bytes() == stable.read_bytes(), "Versioned and CURRENT handoffs are not byte-identical")


def result_gates(cfg_path: Path) -> None:
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    source_frozen = read_csv(Path(cfg["frozen_segments"]["source_path"]))
    strict_frozen = read_csv(Path(cfg["frozen_segments"]["strict_path"]))
    ledger = read_csv(out / "br_ibrx100_liquidity_precheck_v0.32.csv")
    dq = read_csv(out / "br_ibrx100_price_data_quality_v0.32.csv")
    history = read_csv(out / "br_ibrx100_price_history_v0.32.csv")
    fx = read_csv(out / "eurbrl_fx_history_v0.32.csv")
    class_counts = read_csv(out / "liquidity_class_counts_v0.32.csv")
    summary = read_json(out / "summary_v0.32.json")
    checkpoint = read_json(out / "stage_checkpoint_v0.32.json")
    manifest = read_json(out / "manifest_v0.32.json")

    require(len(source_frozen) == 98, "Result gate: source frozen must have 98 rows")
    require(source_frozen["WS_ID_Candidate"].nunique() == 98, "Result gate: source frozen WS_ID not unique")
    require(source_frozen["Primary_Ticker"].nunique() == 98, "Result gate: source frozen ticker not unique")
    require(source_frozen["Primary_MIC"].eq(PRIMARY_MIC).all(), "Result gate: source frozen non-BVMF")
    require(source_frozen["ISIN"].eq("").all(), "Result gate: source frozen contains guessed ISIN")

    require(len(strict_frozen) == 79, "Result gate: strict frozen must have 79 rows")
    require(strict_frozen["WS_ID_Candidate"].nunique() == 79, "Result gate: strict frozen WS_ID not unique")
    require(strict_frozen["Primary_Ticker"].nunique() == 79, "Result gate: strict frozen ticker not unique")
    require(strict_frozen["Primary_MIC"].eq(PRIMARY_MIC).all(), "Result gate: strict frozen non-BVMF")
    require(strict_frozen["Instrument_Type_v0_31"].eq("ORDINARY_SHARE").all(), "Result gate: preferred/unit leaked into strict frozen")
    require(strict_frozen["Instrument_Gate_v0_31"].eq("PASS").all(), "Result gate: instrument FAIL leaked into strict frozen")
    require(strict_frozen["ISIN"].eq("").all(), "Result gate: strict frozen contains guessed ISIN")

    require(len(ledger) == 79, "Result gate: liquidity ledger must have 79 rows")
    require(ledger["WS_ID"].nunique() == 79, "Result gate: liquidity WS_ID not unique")
    require(ledger["Primary_Ticker"].nunique() == 79, "Result gate: liquidity ticker not unique")
    require(set(ledger["WS_ID"]) == set(strict_frozen["WS_ID_Candidate"]), "Result gate: ledger/strict membership mismatch")
    require(ledger["Primary_MIC"].eq(PRIMARY_MIC).all(), "Result gate: liquidity ledger non-BVMF")
    require(ledger["Yahoo_Symbol"].eq(ledger["Primary_Ticker"] + ".SA").all(), "Result gate: Yahoo mapping mismatch")
    require(ledger["Provider"].eq(PROVIDER).all(), "Result gate: provider mismatch")
    require(ledger["Turnover_Method"].eq(TURNOVER_METHOD).all(), "Result gate: turnover method mismatch")
    require(ledger["Liquidity_Class"].isin(LIQUIDITY_CLASSES).all(), "Result gate: unknown liquidity class")
    require(not bool_series(ledger["Eligibility_Promotion_v0_32"]).any(), "Result gate: eligibility promotion detected")
    require(not bool_series(ledger["Canonical_Master_Import_v0_32"]).any(), "Result gate: canonical import detected")

    ready = ledger["Data_Quality_State"].eq("READY")
    med = pd.to_numeric(ledger["MedianTurnover20_EUR"], errors="coerce")
    valid_sessions = pd.to_numeric(ledger["Valid_Sessions"], errors="coerce").fillna(0)
    require(valid_sessions.loc[ready].ge(cfg["liquidity"]["required_valid_sessions"]).all(), "Result gate: READY row lacks 20 sessions")
    require(med.loc[ready].notna().all(), "Result gate: READY row lacks MedianTurnover20_EUR")
    require(med.loc[~ready].isna().all(), "Result gate: non-READY row has MedianTurnover20_EUR")
    require(ledger.loc[~ready, "Liquidity_Class"].eq(DATA_NOT_READY_QUARANTINE).all(), "Result gate: non-READY row classified as liquidity PASS")

    require(len(dq) == 79 and dq["WS_ID"].nunique() == 79, "Result gate: DQ ledger incomplete")
    require(set(dq["WS_ID"]) == set(ledger["WS_ID"]), "Result gate: DQ/liquidity membership mismatch")
    require(len(class_counts) == len(LIQUIDITY_CLASSES), "Result gate: incomplete class-count rows")
    require(set(class_counts["Liquidity_Class"]) == set(LIQUIDITY_CLASSES), "Result gate: class-count labels mismatch")
    require(int(pd.to_numeric(class_counts["Count"]).sum()) == 79, "Result gate: class counts do not sum to 79")
    require(len(fx) > 0, "Result gate: FX history empty")
    require(fx["Provider"].eq(PROVIDER).all(), "Result gate: FX provider mismatch")
    if len(history):
        require(history["Primary_MIC"].eq(PRIMARY_MIC).all(), "Result gate: history non-BVMF")
        require(history["Provider"].eq(PROVIDER).all(), "Result gate: history provider mismatch")
        require(history["Turnover_Method"].eq(TURNOVER_METHOD).all(), "Result gate: history turnover method mismatch")

    require(summary["stage_status"] == "PARTIAL", "Result gate: global stage must remain PARTIAL")
    require(summary["lineage_scope"] == LINEAGE, "Result gate: lineage mismatch")
    require(summary["current_master_rows_before"] == 1535 and summary["current_master_rows_after"] == 1535, "Result gate: current master changed")
    require(summary["source_frozen_rows"] == 98 and summary["strict_ordinary_frozen_rows"] == 79, "Result gate: frozen counts mismatch")
    require(summary["instrument_fail_rows"] == 19, "Result gate: instrument FAIL count mismatch")
    require(summary["eligibility_promotion_v0_32"] is False, "Result gate: eligibility promotion")
    require(summary["canonical_master_import_v0_32"] is False, "Result gate: canonical import")
    require(summary["universe_mutated"] is False, "Result gate: universe mutation")
    require(summary["p0_run"] is False, "Result gate: P0")
    require(summary["sector_rs_performed"] is False, "Result gate: sector RS")
    require(summary["productive"] is False, "Result gate: productive status")
    require(summary["swing_u3k_frozen"] is False, "Result gate: SWING_U3K_FROZEN")
    require(summary["source_superset_complete"] is False, "Result gate: source superset falsely complete")
    require(summary["alpha_vantage_allowed"] is False, "Result gate: Alpha Vantage allowed")
    require(summary["next_stage"] == NEXT_STAGE, "Result gate: next stage mismatch")
    require(checkpoint["status"] == "PARTIAL", "Result gate: checkpoint must be PARTIAL")
    require(checkpoint["input_count"] == 79 and checkpoint["checked_count"] == 79, "Result gate: checkpoint count mismatch")

    hv = Path(cfg["handoff"]["versioned_path"])
    hc = Path(cfg["handoff"]["stable_path"])
    require(hv.exists() and hc.exists(), "Result gate: handoff missing")
    require(hv.read_bytes() == hc.read_bytes(), "Result gate: handoffs not byte-identical")

    required_files = {
        str(out / "br_ibrx100_liquidity_precheck_v0.32.csv"),
        str(out / "br_ibrx100_price_data_quality_v0.32.csv"),
        str(out / "br_ibrx100_price_history_v0.32.csv"),
        str(out / "eurbrl_fx_history_v0.32.csv"),
        str(out / "liquidity_class_counts_v0.32.csv"),
        str(out / "summary_v0.32.json"),
        str(out / "stage_checkpoint_v0.32.json"),
        str(Path(cfg["frozen_segments"]["source_path"])),
        str(Path(cfg["frozen_segments"]["strict_path"])),
        str(hv),
        str(hc),
    }
    require(required_files.issubset(set(manifest["files"])), "Result gate: manifest missing required files")
    print("CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK_V0_32_RESULT_GATES_PASS")


def self_test() -> None:
    thresholds = {"preferred_eur": 20_000_000, "standard_eur": 15_000_000, "exception_pool_eur": 5_000_000}
    assert yahoo_symbol("ABEV3") == "ABEV3.SA"
    assert yahoo_symbol("B3SA3") == "B3SA3.SA"
    assert classify_liquidity(20_000_000, True, thresholds) == PASS_PREFERRED
    assert classify_liquidity(19_999_999.99, True, thresholds) == PASS_STANDARD
    assert classify_liquidity(15_000_000, True, thresholds) == PASS_STANDARD
    assert classify_liquidity(14_999_999.99, True, thresholds) == LOW_LIQUIDITY_EXCEPTION_POOL
    assert classify_liquidity(5_000_000, True, thresholds) == LOW_LIQUIDITY_EXCEPTION_POOL
    assert classify_liquidity(4_999_999.99, True, thresholds) == FAIL_LIQUIDITY
    assert classify_liquidity(25_000_000, False, thresholds) == DATA_NOT_READY_QUARANTINE
    prices = pd.DataFrame({"Date": pd.to_datetime(["2026-08-28"]), "Close_BRL": [10.0], "Volume": [100.0]})
    fx = pd.DataFrame({"EURBRL_Source_Date": ["2026-08-27"], "_FX_Date": pd.to_datetime(["2026-08-27"]), "EURBRL": [6.0]})
    merged = pd.merge_asof(prices, fx, left_on="Date", right_on="_FX_Date", direction="backward")
    assert merged.loc[0, "EURBRL_Source_Date"] == "2026-08-27"
    assert merged.loc[0, "_FX_Date"] <= merged.loc[0, "Date"]
    print("CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK_V0_32_SELF_TEST_PASS")


def run(cfg_path: Path) -> None:
    started = now_utc()
    cfg = read_json(cfg_path)
    require(cfg["stage_id"] == STAGE_ID and cfg["stage_version"] == VERSION, "Config stage identity mismatch")
    require(cfg["governance"]["lineage_scope"] == LINEAGE, "Config lineage mismatch")
    require(cfg["governance"]["canonical_master_import_allowed"] is False, "Config permits canonical import")
    require(cfg["governance"]["eligibility_promotion_allowed"] is False, "Config permits eligibility promotion")
    require(cfg["governance"]["universe_mutation_allowed"] is False, "Config permits universe mutation")
    require(cfg["governance"]["p0_run_allowed"] is False, "Config permits P0")
    require(cfg["governance"]["sector_rs_allowed"] is False, "Config permits sector RS")
    require(cfg["governance"]["alpha_vantage_allowed"] is False, "Config permits Alpha Vantage")
    require(cfg["price"]["provider"] == PROVIDER and cfg["price"]["fx_symbol"] == FX_SYMBOL, "Config provider/FX mismatch")

    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    inp = {k: Path(v) for k, v in cfg["inputs"].items()}
    identity, strict, exclusions, raw_b3, summary31, checkpoint31 = validate_frozen_inputs(cfg, inp)

    source_frozen_path = Path(cfg["frozen_segments"]["source_path"])
    strict_frozen_path = Path(cfg["frozen_segments"]["strict_path"])
    source_frozen_path.parent.mkdir(parents=True, exist_ok=True)
    source_frozen_path.write_bytes(inp["v031_identity_reconciliation"].read_bytes())
    strict_frozen_path.write_bytes(inp["v031_strict_ordinary"].read_bytes())
    require(sha256_file(source_frozen_path) == sha256_file(inp["v031_identity_reconciliation"]), "Source frozen is not byte-exact v0.31 identity snapshot")
    require(sha256_file(strict_frozen_path) == sha256_file(inp["v031_strict_ordinary"]), "Strict frozen is not byte-exact v0.31 strict snapshot")

    lookback_days = int(cfg["price"]["lookback_calendar_days"])
    required_sessions = int(cfg["liquidity"]["required_valid_sessions"])
    br_today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    cutoff_date = br_today.isoformat()
    start_date = (br_today - timedelta(days=lookback_days)).isoformat()
    end_date = (br_today + timedelta(days=1)).isoformat()

    symbols = [yahoo_symbol(x) for x in strict["Primary_Ticker"]]
    raw_prices, price_provider_error = download_with_one_retry(symbols, start_date, end_date, True)
    raw_fx, fx_provider_error = download_with_one_retry([FX_SYMBOL], start_date, end_date, False)
    fx = prepare_fx(raw_fx, cutoff_date)
    fx.to_csv(out / "eurbrl_fx_history_v0.32.csv", index=False)

    ledger_rows: list[dict] = []
    dq_rows: list[dict] = []
    history_rows: list[dict] = []
    for _, row in strict.sort_values(["Primary_Ticker", "WS_ID_Candidate"]).iterrows():
        ledger, dq, history = process_security(
            row,
            raw_prices,
            fx,
            cutoff_date,
            required_sessions,
            cfg["liquidity"]["thresholds"],
            price_provider_error,
        )
        if fx_provider_error and dq["Data_Quality_State"] == "QUARANTINE_FX_MISSING":
            dq["Data_Quality_Reason"] = fx_provider_error
        ledger_rows.append(ledger)
        dq_rows.append(dq)
        history_rows.extend(history)

    ledger_df = pd.DataFrame(ledger_rows)
    dq_df = pd.DataFrame(dq_rows)
    history_columns = [
        "WS_ID", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol", "Security_Name", "Instrument_Type",
        "Date", "Close_BRL", "Volume", "Turnover_BRL", "EURBRL", "EURBRL_Source_Date", "Turnover_EUR",
        "Price_Valid", "Volume_Valid", "FX_Valid", "Session_Valid", "Provider", "Turnover_Method",
    ]
    history_df = pd.DataFrame(history_rows, columns=history_columns)

    ledger_df.to_csv(out / "br_ibrx100_liquidity_precheck_v0.32.csv", index=False)
    dq_df.to_csv(out / "br_ibrx100_price_data_quality_v0.32.csv", index=False)
    history_df.to_csv(out / "br_ibrx100_price_history_v0.32.csv", index=False)

    class_count_map = {c: int(ledger_df["Liquidity_Class"].eq(c).sum()) for c in LIQUIDITY_CLASSES}
    class_counts_df = pd.DataFrame([{"Liquidity_Class": c, "Count": class_count_map[c]} for c in LIQUIDITY_CLASSES])
    class_counts_df.to_csv(out / "liquidity_class_counts_v0.32.csv", index=False)

    price_asofs = sorted(x for x in ledger_df["Price_AsOf"].astype(str).tolist() if x)
    fx_asofs = sorted(x for x in ledger_df["EURBRL_AsOf"].astype(str).tolist() if x)
    generated = now_utc()
    summary = {
        "schema": SCHEMA,
        "generated_utc": generated,
        "run_status": "CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK_V0_32_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE,
        "current_master_rows_before": 1535,
        "current_master_rows_after": 1535,
        "source_frozen_rows": 98,
        "strict_ordinary_frozen_rows": 79,
        "instrument_fail_rows": 19,
        "preferred_share_fail_rows": 12,
        "unit_fail_rows": 7,
        "instrument_not_verified_rows": 0,
        "source_asof_official": "2026-08-31",
        "source_asof_semantics": SOURCE_SEMANTICS,
        "primary_mic": PRIMARY_MIC,
        "isin_guessed": False,
        "provider": PROVIDER,
        "fx_symbol": FX_SYMBOL,
        "turnover_method": TURNOVER_METHOD,
        "price_asof": max(price_asofs) if price_asofs else "",
        "price_asof_min": min(price_asofs) if price_asofs else "",
        "eurbrl_asof": max(fx_asofs) if fx_asofs else "",
        "required_valid_sessions": required_sessions,
        "liquidity_class_counts": class_count_map,
        "data_quality_ready_count": int(ledger_df["Data_Quality_State"].eq("READY").sum()),
        "data_not_ready_quarantine_count": class_count_map[DATA_NOT_READY_QUARANTINE],
        "price_provider_error": price_provider_error,
        "fx_provider_error": fx_provider_error,
        "eligibility_promotion_v0_32": False,
        "canonical_master_import_v0_32": False,
        "universe_mutated": False,
        "p0_run": False,
        "sector_rs_performed": False,
        "productive": False,
        "swing_u3k_frozen": False,
        "source_superset_complete": False,
        "alpha_vantage_allowed": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": NEXT_STAGE,
        "notes": [
            "The 98-row official B3 source snapshot and 79-row Strict Ordinary subset are byte-exact freezes of the v0.31 authoritative ledgers.",
            "The 19 instrument FAIL rows remain documented in v0.31 and are excluded from the Strict Ordinary frozen segment.",
            "Turnover is Close_BRL multiplied by Volume and is explicitly an approximation, not B3-reported turnover.",
            "EURBRL alignment uses only the same-day or latest prior valid FX observation; no future FX value is used.",
            "Liquidity PASS is precheck-only. No eligibility promotion, canonical import, universe mutation, P0 or productive scan occurs.",
        ],
    }
    summary_path = out / "summary_v0.32.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in inp.items()}
    parameter_hash = sha256_file(cfg_path)
    core = [
        source_frozen_path,
        strict_frozen_path,
        out / "br_ibrx100_liquidity_precheck_v0.32.csv",
        out / "br_ibrx100_price_data_quality_v0.32.csv",
        out / "br_ibrx100_price_history_v0.32.csv",
        out / "eurbrl_fx_history_v0.32.csv",
        out / "liquidity_class_counts_v0.32.csv",
        summary_path,
    ]
    output_hash = combined_hash({str(p): sha256_file(p) for p in core})
    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_32",
        "run_id": cfg["run_id"],
        "stage_id": STAGE_ID,
        "stage_version": VERSION,
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": 79,
        "checked_count": 79,
        "pass_count": class_count_map[PASS_PREFERRED] + class_count_map[PASS_STANDARD],
        "exception_pool_count": class_count_map[LOW_LIQUIDITY_EXCEPTION_POOL],
        "fail_count": class_count_map[FAIL_LIQUIDITY],
        "data_error_count": class_count_map[DATA_NOT_READY_QUARANTINE],
        "quarantine_count": class_count_map[DATA_NOT_READY_QUARANTINE],
        "status": "PARTIAL",
        "failed_source": "GLOBAL_SOURCE_SUPERSET_STILL_INCOMPLETE",
        "lineage_scope": LINEAGE,
        "source_frozen_rows": 98,
        "strict_ordinary_frozen_rows": 79,
        "universe_mutated": False,
        "eligibility_promotion_v0_32": False,
        "canonical_master_import_v0_32": False,
        "p0_run": False,
        "sector_rs_performed": False,
        "productive": False,
        "source_superset_complete": False,
        "swing_u3k_frozen": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": NEXT_STAGE,
    }
    checkpoint_path = out / "stage_checkpoint_v0.32.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    hv = Path(cfg["handoff"]["versioned_path"])
    hc = Path(cfg["handoff"]["stable_path"])
    write_handoff(hv, hc, summary, checkpoint)

    manifest_files = core + [checkpoint_path, hv, hc]
    manifest = {
        "schema": "WELT_SWING_CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK_MANIFEST_V0_32",
        "generated_utc": now_utc(),
        "lineage_scope": LINEAGE,
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "core_output_hash": output_hash,
        "provider": PROVIDER,
        "turnover_method": TURNOVER_METHOD,
        "alpha_vantage_allowed": False,
        "eligibility_promotion_v0_32": False,
        "canonical_master_import_v0_32": False,
        "universe_mutated": False,
        "p0_run": False,
        "files": {
            str(p): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in manifest_files
        },
    }
    (out / "manifest_v0.32.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    result_gates(cfg_path)
    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        default="config/current_master_br_ibrx100_source_segment_freeze_liquidity_precheck_v0.32.json",
    )
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    elif args.validate:
        result_gates(Path(args.config))
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
