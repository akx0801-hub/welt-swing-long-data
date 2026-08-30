#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf

STAGE_ID = "CURRENT_MASTER_BR_IBRX100_ELIGIBILITY_GATE_COMPLETION_AND_CONTROLLED_SEGMENT_IMPORT_PLAN"
VERSION = "v0.33"
SCHEMA = "WELT_SWING_CURRENT_MASTER_BR_IBRX100_ELIGIBILITY_GATE_COMPLETION_IMPORT_PLAN_V0_33"
LINEAGE = "CURRENT_MASTER_CLEAN_RESTART"
STATUS = "DEV / RESEARCH / SHADOW - NOT PRODUCTIVE"
PRIMARY_MIC = "BVMF"
PROVIDER = "YFINANCE_FREE"
SCALABLE_STATUS = "SCALABLE_NOT_VERIFIED"
SOURCE_ASOF = "2026-08-31"
STANDARD_CLASSES = {"PASS_PREFERRED", "PASS_STANDARD"}
HISTORY_PASS = "PASS_HISTORY_STANDARD_U3K"
HISTORY_INSUFFICIENT = "INSUFFICIENT_HISTORY_FOR_STANDARD_U3K"
HISTORY_DQ_FAIL = "DATA_QUALITY_FAIL_HISTORY"
HISTORY_DOWNLOAD_FAIL = "DOWNLOAD_FAILED"
ELIGIBILITY_READY = "STANDARD_ELIGIBILITY_READY"
EXPECTED_MASTER_COLUMNS = [
    "WS_ID", "Name", "ISIN", "Instrument_Type", "Country", "Primary_Ticker",
    "Primary_Exchange", "Primary_MIC", "Primary_Currency", "Yahoo_Symbol",
    "Alpha_Symbol", "Primary_Universe_Index", "Index_Tags", "Active",
    "Universe_Status", "Mapping_Status", "Scalable_Tradeability_Status",
    "Source_ID", "Source_AsOf", "Last_Validated", "Share_Class", "Notes",
]
OUTPUT_FILES = [
    "br_ibrx100_history_gate_v0.33.csv",
    "br_ibrx100_standard_eligibility_v0.33.csv",
    "br_ibrx100_standard_eligibility_ready_v0.33.csv",
    "br_ibrx100_low_liquidity_exception_pool_v0.33.csv",
    "br_ibrx100_standard_exclusions_v0.33.csv",
    "br_ibrx100_master_collision_audit_v0.33.csv",
    "br_ibrx100_controlled_master_import_plan_v0.33.csv",
    "br_ibrx100_master_import_projection_v0.33.csv",
    "br_ibrx100_history_cache_v0.33.csv",
    "eligibility_state_counts_v0.33.csv",
    "summary_v0.33.json",
    "stage_checkpoint_v0.33.json",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def txt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    return str(value).strip()


def safe_float(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def brazil_today() -> date:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def session_date(value) -> str:
    try:
        return pd.Timestamp(value).date().isoformat()
    except Exception:
        return ""


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


def load_inputs(cfg: dict) -> tuple[dict[str, Path], dict]:
    paths = {key: Path(value) for key, value in cfg["inputs"].items()}
    missing = [str(path) for path in paths.values() if not path.exists()]
    require(not missing, f"Missing inputs: {missing}")

    spec = paths["master_spec"].read_text(encoding="utf-8")
    handoff = paths["current_handoff"].read_text(encoding="utf-8")
    summary32 = read_json(paths["v032_summary"])
    checkpoint32 = read_json(paths["v032_checkpoint"])
    liquidity = read_csv(paths["v032_liquidity"])
    dq = read_csv(paths["v032_price_data_quality"])
    source = read_csv(paths["v032_source_frozen"])
    strict = read_csv(paths["v032_strict_frozen"])
    identity = read_csv(paths["v031_identity"])
    xls = pd.ExcelFile(paths["current_master_xlsx"], engine="openpyxl")
    require("Universe_Master" in xls.sheet_names, f"Universe_Master sheet missing: {xls.sheet_names}")
    master = pd.read_excel(paths["current_master_xlsx"], sheet_name="Universe_Master", dtype=str, keep_default_na=False, engine="openpyxl")
    return paths, {
        "spec": spec, "handoff": handoff, "summary32": summary32, "checkpoint32": checkpoint32,
        "liquidity": liquidity, "dq": dq, "source": source, "strict": strict,
        "identity": identity, "master": master, "sheets": list(xls.sheet_names),
    }


def validate_inputs(cfg: dict, paths: dict[str, Path], data: dict) -> dict:
    spec, handoff = data["spec"], data["handoff"]
    summary32, checkpoint32 = data["summary32"], data["checkpoint32"]
    liquidity, dq = data["liquidity"], data["dq"]
    source, strict, identity, master = data["source"], data["strict"], data["identity"], data["master"]

    require(cfg["stage_id"] == STAGE_ID and cfg["version"] == VERSION, "Config stage/version mismatch")
    require(cfg["provider"] == PROVIDER, "Provider must remain YFINANCE_FREE")
    require(cfg["alpha_vantage_allowed"] is False, "Alpha Vantage must remain false")
    for flag in [
        "canonical_master_import_v0_33", "universe_mutated", "eligibility_promotion_v0_33",
        "p0_run", "sector_rs_performed", "productive", "swing_u3k_frozen", "source_superset_complete",
    ]:
        require(cfg[flag] is False, f"Forbidden config flag enabled: {flag}")

    require("WELT-SWING LONG DEV v0.1" in spec, "Master specification identity missing")
    require("260" in spec and "252" in spec and "SMA200" in spec and "High252" in spec, "Master history requirements missing")
    require("Alpha Vantage" in spec and "vollständig ausgeschlossen" in spec, "Master Alpha-Vantage prohibition missing")
    require("**Version:** v0.32" in handoff, "CURRENT handoff is not v0.32")
    require(LINEAGE in handoff, "CURRENT handoff lineage mismatch")

    require(summary32["lineage_scope"] == LINEAGE, "v0.32 lineage mismatch")
    require(summary32["stage_status"] == "PARTIAL", "v0.32 stage status mismatch")
    require(summary32["current_master_rows_before"] == 1535 and summary32["current_master_rows_after"] == 1535, "v0.32 current-master count mismatch")
    require(summary32["source_frozen_rows"] == 98, "v0.32 source frozen count mismatch")
    require(summary32["strict_ordinary_frozen_rows"] == 79, "v0.32 strict count mismatch")
    require(summary32["instrument_fail_rows"] == 19, "v0.32 instrument fail mismatch")
    require(summary32["preferred_share_fail_rows"] == 12 and summary32["unit_fail_rows"] == 7, "v0.32 instrument breakdown mismatch")
    require(summary32["liquidity_class_counts"] == {
        "PASS_PREFERRED": 28, "PASS_STANDARD": 10,
        "LOW_LIQUIDITY_EXCEPTION_POOL": 28, "FAIL_LIQUIDITY": 13,
        "DATA_NOT_READY_QUARANTINE": 0,
    }, "v0.32 liquidity counts mismatch")
    require(summary32["price_asof"] == "2026-08-27" and summary32["eurbrl_asof"] == "2026-08-27", "v0.32 as-of mismatch")
    require(summary32["provider"] == PROVIDER and summary32["alpha_vantage_allowed"] is False, "v0.32 provider gate mismatch")
    require(summary32["next_stage"] == STAGE_ID, "v0.32 next-stage mismatch")

    require(checkpoint32["stage_version"] == "v0.32" and checkpoint32["lineage_scope"] == LINEAGE, "v0.32 checkpoint mismatch")
    require(checkpoint32["input_count"] == 79 and checkpoint32["pass_count"] == 38, "v0.32 checkpoint standard-pass mismatch")
    require(checkpoint32["exception_pool_count"] == 28 and checkpoint32["fail_count"] == 13, "v0.32 checkpoint exception/fail mismatch")
    require(checkpoint32["data_error_count"] == 0 and checkpoint32["quarantine_count"] == 0, "v0.32 checkpoint data state mismatch")

    source_required = {
        "WS_ID_Candidate", "ISIN", "Primary_MIC", "Primary_Ticker", "Security_Name_Official",
        "B3_Type_Official", "Instrument_Type_v0_31", "Instrument_Gate_v0_31",
        "Identity_Gate_v0_31", "Source_Membership_Gate_v0_31", "Source_ID",
        "Source_AsOf_Official", "Source_AsOf_Semantics",
    }
    liquidity_required = {
        "WS_ID", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol", "Security_Name",
        "Instrument_Type", "Source_AsOf_Official", "Price_AsOf", "Valid_Sessions",
        "MedianTurnover20_BRL", "MedianTurnover20_EUR", "Liquidity_Class",
        "Data_Quality_State", "Provider", "Mapping_State",
    }
    require(source_required.issubset(source.columns), "Source frozen schema mismatch")
    require(liquidity_required.issubset(liquidity.columns), "Liquidity schema mismatch")
    require(len(source) == 98 and source["WS_ID_Candidate"].nunique() == 98, "Source frozen membership mismatch")
    require(len(identity) == 98 and identity["WS_ID_Candidate"].nunique() == 98, "Identity ledger mismatch")
    require(source["WS_ID_Candidate"].tolist() == identity["WS_ID_Candidate"].tolist(), "Source frozen is not the authoritative v0.31 identity order")
    require(len(strict) == 79 and strict["WS_ID_Candidate"].nunique() == 79, "Strict frozen mismatch")
    require(strict["Instrument_Type_v0_31"].eq("ORDINARY_SHARE").all(), "Strict frozen contains non-ordinary instrument")
    require(source["Primary_MIC"].eq(PRIMARY_MIC).all(), "Source contains non-BVMF row")
    require(source["Source_AsOf_Official"].eq(SOURCE_ASOF).all(), "Source as-of changed")
    require(source["ISIN"].eq("").all(), "Source contains non-authoritative ISIN")
    require(source["Identity_Gate_v0_31"].eq("PASS").all(), "Identity gate changed")
    require(int(source["Instrument_Gate_v0_31"].eq("FAIL").sum()) == 19, "Instrument fail count changed")
    require(int(source["Instrument_Type_v0_31"].eq("PREFERRED_SHARE").sum()) == 12, "Preferred count changed")
    require(int(source["Instrument_Type_v0_31"].eq("UNIT").sum()) == 7, "Unit count changed")

    require(len(liquidity) == 79 and liquidity["WS_ID"].nunique() == 79, "Liquidity ledger mismatch")
    require(len(dq) == 79 and dq["WS_ID"].nunique() == 79, "Price data-quality ledger mismatch")
    require(liquidity["Primary_MIC"].eq(PRIMARY_MIC).all(), "Liquidity contains non-BVMF")
    require(liquidity["Provider"].eq(PROVIDER).all(), "Liquidity provider changed")
    require(liquidity["Data_Quality_State"].eq("READY").all(), "v0.32 data quality is not fully ready")
    require(liquidity["Mapping_State"].eq("RESOLVED_FORMAT_AND_OHLCV").all(), "v0.32 mapping state changed")
    class_counts = liquidity["Liquidity_Class"].value_counts().to_dict()
    require(class_counts == {
        "PASS_PREFERRED": 28, "LOW_LIQUIDITY_EXCEPTION_POOL": 28,
        "FAIL_LIQUIDITY": 13, "PASS_STANDARD": 10,
    }, f"Liquidity classes changed: {class_counts}")

    require(list(master.columns) == EXPECTED_MASTER_COLUMNS, f"Universe_Master columns changed: {list(master.columns)}")
    require(len(master) == 1535 and master["WS_ID"].nunique() == 1535, "Current Master row/WS_ID count mismatch")

    standard = liquidity[liquidity["Liquidity_Class"].isin(STANDARD_CLASSES)].copy()
    low = liquidity[liquidity["Liquidity_Class"].eq("LOW_LIQUIDITY_EXCEPTION_POOL")].copy()
    liq_fail = liquidity[liquidity["Liquidity_Class"].eq("FAIL_LIQUIDITY")].copy()
    instrument_fail = source[source["Instrument_Gate_v0_31"].eq("FAIL")].copy()
    require(len(standard) == 38 and standard["WS_ID"].nunique() == 38, "Standard liquidity set is not 38")
    require(len(low) == 28 and len(liq_fail) == 13 and len(instrument_fail) == 19, "Separated sets mismatch")
    require(set(standard["WS_ID"]).isdisjoint(set(low["WS_ID"])) and set(standard["WS_ID"]).isdisjoint(set(liq_fail["WS_ID"])), "Set separation failed")
    require(set(standard["WS_ID"]).issubset(set(strict["WS_ID_Candidate"])), "Standard candidates not subset of strict ordinary")

    return {
        "standard": standard.sort_values("WS_ID").reset_index(drop=True),
        "low": low.sort_values("WS_ID").reset_index(drop=True),
        "liquidity_fail": liq_fail.sort_values("WS_ID").reset_index(drop=True),
        "instrument_fail": instrument_fail.sort_values("WS_ID_Candidate").reset_index(drop=True),
        "master_sha256_before": sha256_file(paths["current_master_xlsx"]),
        "research_sha256_before": sha256_file(paths["research_partial_1535"]),
    }



def build_history_for_security(row: pd.Series, raw: pd.DataFrame, batch_error: str, today: date) -> tuple[dict, list[dict]]:
    ws_id = txt(row["WS_ID"])
    ticker = txt(row["Primary_Ticker"])
    symbol = txt(row["Yahoo_Symbol"])
    mapping_state = txt(row["Mapping_State"])
    base = {
        "WS_ID": ws_id,
        "Primary_MIC": txt(row["Primary_MIC"]),
        "Primary_Ticker": ticker,
        "Yahoo_Symbol": symbol,
        "Security_Name": txt(row["Security_Name"]),
        "Source_AsOf_Official": txt(row["Source_AsOf_Official"]),
        "Liquidity_Class": txt(row["Liquidity_Class"]),
        "Mapping_State": mapping_state,
        "Scalable_Tradeability_Status": SCALABLE_STATUS,
        "Provider": PROVIDER,
        "History_First_Date": "",
        "History_Last_Completed_Date": "",
        "Unique_Daily_Bars": 0,
        "Valid_Completed_Bars": 0,
        "Invalid_Completed_Bars": 0,
        "History_Gate_State": HISTORY_DOWNLOAD_FAIL,
        "Data_Quality_Detail": "",
        "Download_Error": "",
        "Replacement_Ticker_Used": False,
        "Current_Session_Excluded": True,
    }
    if txt(row["Primary_MIC"]) != PRIMARY_MIC or not symbol or symbol != f"{ticker}.SA":
        base["History_Gate_State"] = HISTORY_DQ_FAIL
        base["Data_Quality_Detail"] = "PRIMARY_MARKET_OR_MAPPING_CONFLICT"
        return base, []

    frame = extract_symbol_frame(raw, symbol)
    individual_error = ""
    if frame.empty:
        start = (today - timedelta(days=1100)).isoformat()
        end = (today + timedelta(days=1)).isoformat()
        individual, individual_error = download_with_one_retry([symbol], start, end, False)
        frame = extract_symbol_frame(individual, symbol)

    if frame.empty:
        base["Download_Error"] = individual_error or batch_error or "EMPTY_SYMBOL_HISTORY"
        return base, []

    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = sorted(required - set(frame.columns))
    if missing:
        base["History_Gate_State"] = HISTORY_DQ_FAIL
        base["Data_Quality_Detail"] = "MISSING_REQUIRED_COLUMNS:" + ",".join(missing)
        return base, []

    frame = frame[list(required)].copy()
    frame = frame[frame["Date"].ne("")].copy()
    frame = frame[frame["Date"].lt(today.isoformat())].copy()
    frame = frame[frame["Date"].le(today.isoformat())].copy()
    duplicate_dates = frame.loc[frame["Date"].duplicated(keep=False), "Date"].unique().tolist()
    if duplicate_dates:
        base["History_Gate_State"] = HISTORY_DQ_FAIL
        base["Data_Quality_Detail"] = "DUPLICATE_DAILY_DATES:" + ",".join(duplicate_dates[:10])
        return base, []

    frame = frame.sort_values("Date").reset_index(drop=True)
    cache_rows: list[dict] = []
    valid_count = 0
    for _, bar in frame.iterrows():
        open_value = safe_float(bar.get("Open"))
        high = safe_float(bar.get("High"))
        low_value = safe_float(bar.get("Low"))
        close = safe_float(bar.get("Close"))
        volume = safe_float(bar.get("Volume"))
        valid = bool(
            close is not None and close > 0
            and high is not None and high > 0
            and low_value is not None and low_value > 0
            and volume is not None and volume > 0
            and high >= low_value
        )
        valid_count += int(valid)
        cache_rows.append({
            "WS_ID": ws_id,
            "Primary_MIC": PRIMARY_MIC,
            "Primary_Ticker": ticker,
            "Yahoo_Symbol": symbol,
            "Date": txt(bar["Date"]),
            "Open": round(open_value, 8) if open_value is not None else "",
            "High": round(high, 8) if high is not None else "",
            "Low": round(low_value, 8) if low_value is not None else "",
            "Close": round(close, 8) if close is not None else "",
            "Volume": round(volume, 4) if volume is not None else "",
            "Valid_Completed_Bar": valid,
            "Provider": PROVIDER,
        })

    unique_count = int(frame["Date"].nunique())
    base["History_First_Date"] = txt(frame["Date"].min()) if unique_count else ""
    base["History_Last_Completed_Date"] = txt(frame["Date"].max()) if unique_count else ""
    base["Unique_Daily_Bars"] = unique_count
    base["Valid_Completed_Bars"] = valid_count
    base["Invalid_Completed_Bars"] = unique_count - valid_count
    if unique_count >= 260 and valid_count >= 252:
        base["History_Gate_State"] = HISTORY_PASS
    else:
        base["History_Gate_State"] = HISTORY_INSUFFICIENT
        base["Data_Quality_Detail"] = "FAIL_CLOSED_BELOW_260_UNIQUE_OR_252_VALID"
    return base, cache_rows


def run_history_stage(standard: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    today = brazil_today()
    symbols = standard["Yahoo_Symbol"].astype(str).tolist()
    require(len(symbols) == 38 and len(set(symbols)) == 38, "History symbol set must be 38 unique mappings")
    require(all(symbol == f"{ticker}.SA" for symbol, ticker in zip(symbols, standard["Primary_Ticker"])), "Yahoo mapping mismatch")
    days = int(cfg["history_calendar_days"])
    require(days >= 730, "History request window below two years")
    start = (today - timedelta(days=days)).isoformat()
    end = (today + timedelta(days=1)).isoformat()
    raw, batch_error = download_with_one_retry(symbols, start, end, True)

    ledger_rows: list[dict] = []
    cache_rows: list[dict] = []
    for _, row in standard.iterrows():
        ledger, cache = build_history_for_security(row, raw, batch_error, today)
        ledger_rows.append(ledger)
        cache_rows.extend(cache)

    history = pd.DataFrame(ledger_rows).sort_values("WS_ID").reset_index(drop=True)
    cache_columns = [
        "WS_ID", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol", "Date",
        "Open", "High", "Low", "Close", "Volume", "Valid_Completed_Bar", "Provider",
    ]
    cache = pd.DataFrame(cache_rows, columns=cache_columns)
    if not cache.empty:
        cache = cache.sort_values(["WS_ID", "Date"]).reset_index(drop=True)
    price_asof = txt(history["History_Last_Completed_Date"].max())
    return history, cache, price_asof


def build_standard_eligibility(standard: pd.DataFrame, history: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    source_fields = source[[
        "WS_ID_Candidate", "Source_Membership_Gate_v0_31", "Identity_Gate_v0_31",
        "Instrument_Gate_v0_31", "Instrument_Type_v0_31",
    ]].rename(columns={"WS_ID_Candidate": "WS_ID"})
    work = standard.merge(history, on=[
        "WS_ID", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol",
        "Security_Name", "Source_AsOf_Official", "Liquidity_Class", "Mapping_State",
    ], how="left", validate="one_to_one")
    work = work.merge(source_fields, on="WS_ID", how="left", validate="one_to_one")
    rows: list[dict] = []
    for _, row in work.iterrows():
        source_pass = txt(row["Source_Membership_Gate_v0_31"]) == "PASS"
        identity_pass = txt(row["Identity_Gate_v0_31"]) == "PASS"
        instrument_pass = txt(row["Instrument_Gate_v0_31"]) == "PASS" and txt(row["Instrument_Type_v0_31"]) == "ORDINARY_SHARE"
        liquidity_pass = txt(row["Liquidity_Class"]) in STANDARD_CLASSES
        mapping_pass = (
            txt(row["Primary_MIC"]) == PRIMARY_MIC
            and txt(row["Yahoo_Symbol"]) == f"{txt(row['Primary_Ticker'])}.SA"
            and txt(row["Mapping_State"]) == "RESOLVED_FORMAT_AND_OHLCV"
        )
        history_state = txt(row["History_Gate_State"])
        if source_pass and identity_pass and instrument_pass and liquidity_pass and mapping_pass and history_state == HISTORY_PASS:
            plan_state = ELIGIBILITY_READY
        elif history_state == HISTORY_INSUFFICIENT:
            plan_state = "STANDARD_U3K_NOT_READY_INSUFFICIENT_HISTORY"
        elif history_state == HISTORY_DOWNLOAD_FAIL:
            plan_state = "STANDARD_U3K_NOT_READY_DOWNLOAD_FAILED"
        else:
            plan_state = "STANDARD_U3K_NOT_READY_DATA_QUALITY"
        rows.append({
            "WS_ID": txt(row["WS_ID"]),
            "Primary_MIC": txt(row["Primary_MIC"]),
            "Primary_Ticker": txt(row["Primary_Ticker"]),
            "Yahoo_Symbol": txt(row["Yahoo_Symbol"]),
            "Security_Name": txt(row["Security_Name"]),
            "Instrument_Type": txt(row["Instrument_Type_v0_31"]),
            "Source_Gate_State": txt(row["Source_Membership_Gate_v0_31"]),
            "Identity_Gate_State": txt(row["Identity_Gate_v0_31"]),
            "Instrument_Gate_State": txt(row["Instrument_Gate_v0_31"]),
            "Liquidity_Class": txt(row["Liquidity_Class"]),
            "Mapping_State": txt(row["Mapping_State"]),
            "History_Gate_State": history_state,
            "History_First_Date": txt(row["History_First_Date"]),
            "History_Last_Completed_Date": txt(row["History_Last_Completed_Date"]),
            "Unique_Daily_Bars": int(row["Unique_Daily_Bars"]),
            "Valid_Completed_Bars": int(row["Valid_Completed_Bars"]),
            "Scalable_Tradeability_Status": SCALABLE_STATUS,
            "Eligibility_Plan_State": plan_state,
            "Provider": PROVIDER,
            "Canonical_Import_v0_33": False,
            "Eligibility_Promotion_v0_33": False,
        })
    return pd.DataFrame(rows).sort_values("WS_ID").reset_index(drop=True)


def projection_row(src: pd.Series, liquidity_by_ws: dict[str, dict], generated: str) -> dict:
    ws_id = txt(src["WS_ID_Candidate"])
    liq = liquidity_by_ws.get(ws_id)
    yahoo = txt(liq.get("Yahoo_Symbol")) if liq and txt(liq.get("Mapping_State")) == "RESOLVED_FORMAT_AND_OHLCV" else ""
    mapping = "YFINANCE_VERIFIED" if yahoo else "NOT_VERIFIED"
    instrument_type = txt(src["Instrument_Type_v0_31"])
    return {
        "WS_ID": ws_id,
        "Name": txt(src["Security_Name_Official"]),
        "ISIN": txt(src["ISIN"]),
        "Instrument_Type": instrument_type,
        "Country": "Brazil",
        "Primary_Ticker": txt(src["Primary_Ticker"]),
        "Primary_Exchange": "B3",
        "Primary_MIC": PRIMARY_MIC,
        "Primary_Currency": "BRL",
        "Yahoo_Symbol": yahoo,
        "Alpha_Symbol": "",
        "Primary_Universe_Index": "BR_IBRX100",
        "Index_Tags": "BR_IBRX100",
        "Active": True,
        "Universe_Status": "SOURCE_SUPERSET_PLANNED_NOT_IMPORTED",
        "Mapping_Status": mapping,
        "Scalable_Tradeability_Status": SCALABLE_STATUS,
        "Source_ID": txt(src["Source_ID"]),
        "Source_AsOf": SOURCE_ASOF,
        "Last_Validated": generated,
        "Share_Class": txt(src["B3_Type_Official"]),
        "Notes": "v0.33 controlled source-superset projection only; no canonical import",
    }


def normalize_name(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", txt(value).upper())


def build_collision_audit(projection: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Collision_Type", "Planned_WS_ID", "Planned_MIC", "Planned_Ticker", "Planned_Name",
        "Current_WS_ID", "Current_MIC", "Current_Ticker", "Current_Name", "Details", "Blocking",
    ]
    rows: list[dict] = []

    def add(kind: str, planned: pd.Series, current: pd.Series | None, detail: str) -> None:
        rows.append({
            "Collision_Type": kind,
            "Planned_WS_ID": txt(planned.get("WS_ID")),
            "Planned_MIC": txt(planned.get("Primary_MIC")),
            "Planned_Ticker": txt(planned.get("Primary_Ticker")),
            "Planned_Name": txt(planned.get("Name")),
            "Current_WS_ID": txt(current.get("WS_ID")) if current is not None else "",
            "Current_MIC": txt(current.get("Primary_MIC")) if current is not None else "",
            "Current_Ticker": txt(current.get("Primary_Ticker")) if current is not None else "",
            "Current_Name": txt(current.get("Name")) if current is not None else "",
            "Details": detail,
            "Blocking": True,
        })

    for _, planned in projection.iterrows():
        for _, current in master[master["WS_ID"].eq(planned["WS_ID"])].iterrows():
            add("WS_ID_COLLISION", planned, current, "Planned WS_ID already exists in Current Master")
        mic_ticker = master[
            master["Primary_MIC"].eq(planned["Primary_MIC"])
            & master["Primary_Ticker"].eq(planned["Primary_Ticker"])
        ]
        for _, current in mic_ticker.iterrows():
            add("PRIMARY_MIC_TICKER_COLLISION", planned, current, "Planned primary market identity already exists")
        current_name = master[
            master["Country"].astype(str).str.casefold().eq("brazil")
            & master["Name"].map(normalize_name).eq(normalize_name(planned["Name"]))
            & ~master["WS_ID"].eq(planned["WS_ID"])
        ]
        for _, current in current_name.iterrows():
            add("POTENTIAL_SHARE_CLASS_COLLISION", planned, current, "Brazil name collision requires share-class review")

    existing_br = master[
        master["Primary_Universe_Index"].eq("BR_IBRX100")
        | master["Index_Tags"].astype(str).str.contains(r"(^|[|,; ])BR_IBRX100($|[|,; ])", regex=True, na=False)
    ]
    for _, current in existing_br.iterrows():
        planned_match = projection[projection["Primary_Ticker"].eq(current["Primary_Ticker"])]
        if planned_match.empty:
            planned = pd.Series({"WS_ID": "", "Primary_MIC": PRIMARY_MIC, "Primary_Ticker": "", "Name": ""})
        else:
            planned = planned_match.iloc[0]
        add("EXISTING_BR_IBRX100_ROW", planned, current, "Current Master already contains BR_IBRX100 membership")

    for field_set, kind in [
        (["WS_ID"], "DUPLICATE_SOURCE_WS_ID"),
        (["Primary_MIC", "Primary_Ticker"], "DUPLICATE_SOURCE_PRIMARY_IDENTITY"),
    ]:
        duplicated = projection[projection.duplicated(field_set, keep=False)]
        for _, planned in duplicated.iterrows():
            add(kind, planned, None, "Duplicate inside 98-row source projection")

    return pd.DataFrame(rows, columns=columns)



def build_import_plan(source: pd.DataFrame, liquidity: pd.DataFrame, history: pd.DataFrame, eligibility: pd.DataFrame) -> pd.DataFrame:
    liquidity_by = {txt(row["WS_ID"]): row.to_dict() for _, row in liquidity.iterrows()}
    history_by = {txt(row["WS_ID"]): row.to_dict() for _, row in history.iterrows()}
    eligibility_by = {txt(row["WS_ID"]): row.to_dict() for _, row in eligibility.iterrows()}
    rows: list[dict] = []
    for _, src in source.iterrows():
        ws_id = txt(src["WS_ID_Candidate"])
        instrument_gate = txt(src["Instrument_Gate_v0_31"])
        liq = liquidity_by.get(ws_id)
        liquidity_class = txt(liq.get("Liquidity_Class")) if liq else "NOT_CHECKED_INSTRUMENT_FAIL"
        hist = history_by.get(ws_id)
        history_state = txt(hist.get("History_Gate_State")) if hist else "NOT_APPLICABLE_NOT_STANDARD_LIQUIDITY"
        if instrument_gate != "PASS":
            plan_state = "STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT"
        elif liquidity_class == "FAIL_LIQUIDITY":
            plan_state = "STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY"
        elif liquidity_class == "LOW_LIQUIDITY_EXCEPTION_POOL":
            plan_state = "LOW_LIQUIDITY_EXCEPTION_POOL"
        elif liquidity_class in STANDARD_CLASSES:
            require(ws_id in eligibility_by, f"Missing standard eligibility row for {ws_id}")
            plan_state = txt(eligibility_by[ws_id]["Eligibility_Plan_State"])
        else:
            plan_state = "STANDARD_U3K_NOT_READY_DATA_QUALITY"
        planned_action = (
            "ADD_TO_SOURCE_SUPERSET_WITH_STANDARD_ELIGIBILITY_READY_PLAN_STATE"
            if plan_state == ELIGIBILITY_READY
            else "ADD_TO_SOURCE_SUPERSET_ONLY"
        )
        rows.append({
            "WS_ID": ws_id,
            "Primary_MIC": txt(src["Primary_MIC"]),
            "Primary_Ticker": txt(src["Primary_Ticker"]),
            "Security_Name": txt(src["Security_Name_Official"]),
            "Instrument_Type": txt(src["Instrument_Type_v0_31"]),
            "Source_ID": txt(src["Source_ID"]),
            "Source_AsOf": txt(src["Source_AsOf_Official"]),
            "Source_Superset_Member": True,
            "Source_Gate_State": txt(src["Source_Membership_Gate_v0_31"]),
            "Identity_Gate_State": txt(src["Identity_Gate_v0_31"]),
            "Instrument_Gate_State": instrument_gate,
            "Liquidity_Class": liquidity_class,
            "History_Gate_State": history_state,
            "Standard_Eligibility_Plan_State": plan_state,
            "Scalable_Tradeability_Status": SCALABLE_STATUS,
            "Planned_Master_Action": planned_action,
            "Canonical_Import_v0_33": False,
            "Eligibility_Promotion_v0_33": False,
        })
    return pd.DataFrame(rows).sort_values("WS_ID").reset_index(drop=True)


def build_standard_exclusions(import_plan: pd.DataFrame) -> pd.DataFrame:
    excluded = import_plan[import_plan["Standard_Eligibility_Plan_State"].ne(ELIGIBILITY_READY)].copy()
    excluded["Standard_Exclusion_Reason"] = excluded["Standard_Eligibility_Plan_State"]
    return excluded.reset_index(drop=True)


def write_handoff(versioned: Path, stable: Path, summary: dict) -> None:
    h = summary["history_gate_counts"]
    e = summary["eligibility_state_counts"]
    s = summary["scalable_status_counts"]
    expected = summary["expected_current_master_rows_after_future_br_import"]
    expected_text = str(expected) if expected is not None else "BLOCKED_BY_COLLISIONS"
    body = f"""# WELT-SWING LONG DEV - CURRENT HANDOFF

**Version:** v0.33
**Generated UTC:** {summary['generated_utc']}
**Status:** DEV / RESEARCH / SHADOW - NOT PRODUCTIVE
**Primary lineage:** {LINEAGE}
**Trigger/input commit:** {os.environ.get('GITHUB_SHA', 'LOCAL_OR_UNKNOWN')}

## 1. Authority

Authoritative DEV master:

docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md

Welt-Swing v7.2 remains solely authoritative for productive Swing decisions. Alpha Vantage remains forbidden.

## 2. Current Master and stage boundary

- Current Master rows: 1,535
- Current Master changed in v0.33: false
- Canonical Master Import v0.33: false
- Eligibility Promotion v0.33: false
- Universe Mutated: false
- P0: false
- Sector RS: false
- Productive: false
- SWING_U3K_FROZEN: false
- Source Superset Complete: false

v0.33 completes currently testable Brazil standard eligibility gates and creates a controlled source-superset import plan. It does not import or promote securities.

## 3. Strict set separation

- BR Source Superset planned: {summary['source_members']}
- BR Strict Ordinary: {summary['strict_ordinary']}
- Standard Liquidity: {summary['standard_liquidity_candidates']}
- Low-Liquidity Exception Pool: {summary['low_liquidity_exception_pool']}
- Liquidity Fail: {summary['liquidity_fail']}
- Instrument Fail: {summary['instrument_fail']}
- Preferred Shares inside instrument fails: {summary['preferred_fail']}
- Units inside instrument fails: {summary['unit_fail']}

All 98 official members remain in the controlled source-superset plan. Instrument and liquidity eligibility are separate from source membership.

## 4. History gate

Only the 38 PASS_PREFERRED plus PASS_STANDARD candidates were downloaded.

- Provider: {summary['provider']}
- Primary market: B3 / BVMF
- Yahoo mapping: Primary_Ticker.SA
- History Price_AsOf: {summary['history_price_asof']}
- History candidates checked: {summary['history_candidates_checked']}
- PASS_HISTORY_STANDARD_U3K: {h.get(HISTORY_PASS, 0)}
- INSUFFICIENT_HISTORY_FOR_STANDARD_U3K: {h.get(HISTORY_INSUFFICIENT, 0)}
- DATA_QUALITY_FAIL_HISTORY: {h.get(HISTORY_DQ_FAIL, 0)}
- DOWNLOAD_FAILED: {h.get(HISTORY_DOWNLOAD_FAIL, 0)}
- Unique Daily Bars required: 260
- Valid completed Daily Bars required: 252
- Replacement or predecessor ticker history used: false

## 5. Standard eligibility plan

- STANDARD_ELIGIBILITY_READY: {e.get(ELIGIBILITY_READY, 0)}
- Meaning: all currently testable standard hard gates passed
- Productive eligibility promotion: false

Low-liquidity exceptions, liquidity fails and instrument fails are never counted as STANDARD_ELIGIBILITY_READY.

## 6. Scalable status

{json.dumps(s, ensure_ascii=False, sort_keys=True)}

No live Scalable queries were made. Missing evidence remains SCALABLE_NOT_VERIFIED.

## 7. Controlled source-superset import plan

- Import plan rows: {summary['import_plan_rows']}
- Master projection rows: {summary['master_projection_rows']}
- Collision count: {summary['collision_count']}
- Import plan state: {summary['controlled_import_plan_state']}
- Expected Current Master rows after a future controlled BR import: {expected_text}
- Canonical import performed now: false

## 8. Global classification

The global 14-segment source superset remains incomplete. Stage classification remains PARTIAL.

## 9. Recovery order

1. docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md
2. WELT-SWING-CURRENT-Handoff-CURRENT.md
3. output_current_master_br_ibrx100_eligibility_plan_v0_33/stage_checkpoint_v0.33.json
4. output_current_master_br_ibrx100_eligibility_plan_v0_33/manifest_v0.33.json
5. output_current_master_br_ibrx100_eligibility_plan_v0_33/summary_v0.33.json
6. output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_controlled_master_import_plan_v0.33.csv
7. output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_master_import_projection_v0.33.csv
8. output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_history_gate_v0.33.csv
9. output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_standard_eligibility_v0.33.csv
10. universe/segments/br_ibrx100_source_frozen_v0.32.csv
11. universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv
12. universe/Welt-Swing-Universe-Master-v2.0.xlsx

## 10. Next stage

{summary['next_stage']}

The next stage is not started by v0.33.
"""
    payload = body.encode("utf-8")
    versioned.write_bytes(payload)
    stable.write_bytes(payload)


def validate_outputs(cfg: dict) -> None:
    out = Path(cfg["output_dir"])
    required = OUTPUT_FILES + ["manifest_v0.33.json"]
    missing = [name for name in required if not (out / name).exists()]
    require(not missing, f"Missing outputs: {missing}")

    summary = read_json(out / "summary_v0.33.json")
    checkpoint = read_json(out / "stage_checkpoint_v0.33.json")
    history = read_csv(out / "br_ibrx100_history_gate_v0.33.csv")
    eligibility = read_csv(out / "br_ibrx100_standard_eligibility_v0.33.csv")
    ready = read_csv(out / "br_ibrx100_standard_eligibility_ready_v0.33.csv")
    low = read_csv(out / "br_ibrx100_low_liquidity_exception_pool_v0.33.csv")
    exclusions = read_csv(out / "br_ibrx100_standard_exclusions_v0.33.csv")
    collisions = read_csv(out / "br_ibrx100_master_collision_audit_v0.33.csv")
    plan = read_csv(out / "br_ibrx100_controlled_master_import_plan_v0.33.csv")
    projection = read_csv(out / "br_ibrx100_master_import_projection_v0.33.csv")
    cache = read_csv(out / "br_ibrx100_history_cache_v0.33.csv")

    source = read_csv(Path(cfg["inputs"]["v032_source_frozen"]))
    strict = read_csv(Path(cfg["inputs"]["v032_strict_frozen"]))
    liquidity = read_csv(Path(cfg["inputs"]["v032_liquidity"]))
    master = pd.read_excel(Path(cfg["inputs"]["current_master_xlsx"]), sheet_name="Universe_Master", dtype=str, keep_default_na=False, engine="openpyxl")

    require(summary["lineage_scope"] == LINEAGE and summary["stage_status"] == "PARTIAL", "Summary lineage/status mismatch")
    require(summary["source_members"] == 98 and summary["strict_ordinary"] == 79, "Summary source/strict mismatch")
    require(summary["standard_liquidity_candidates"] == 38, "Summary history input mismatch")
    require(summary["low_liquidity_exception_pool"] == 28 and summary["liquidity_fail"] == 13 and summary["instrument_fail"] == 19, "Summary separation mismatch")
    require(summary["current_master_rows_before"] == 1535 and summary["current_master_rows_after"] == 1535, "Current Master count changed")

    require(len(history) == 38 and history["WS_ID"].nunique() == 38, "History ledger must be exactly 38 unique rows")
    standard_ids = set(liquidity.loc[liquidity["Liquidity_Class"].isin(STANDARD_CLASSES), "WS_ID"])
    low_ids = set(liquidity.loc[liquidity["Liquidity_Class"].eq("LOW_LIQUIDITY_EXCEPTION_POOL"), "WS_ID"])
    liq_fail_ids = set(liquidity.loc[liquidity["Liquidity_Class"].eq("FAIL_LIQUIDITY"), "WS_ID"])
    instrument_fail_ids = set(source.loc[source["Instrument_Gate_v0_31"].eq("FAIL"), "WS_ID_Candidate"])
    require(set(history["WS_ID"]) == standard_ids, "History run does not equal the 38 standard-liquidity candidates")
    require(set(history["WS_ID"]).isdisjoint(low_ids | liq_fail_ids | instrument_fail_ids), "Excluded sets entered history run")
    require(history["Primary_MIC"].eq(PRIMARY_MIC).all() and history["Provider"].eq(PROVIDER).all(), "History market/provider mismatch")
    allowed_history = {HISTORY_PASS, HISTORY_INSUFFICIENT, HISTORY_DQ_FAIL, HISTORY_DOWNLOAD_FAIL}
    require(set(history["History_Gate_State"]).issubset(allowed_history), "Unknown history state")
    numeric_unique = pd.to_numeric(history["Unique_Daily_Bars"], errors="coerce").fillna(0)
    numeric_valid = pd.to_numeric(history["Valid_Completed_Bars"], errors="coerce").fillna(0)
    pass_rows = history["History_Gate_State"].eq(HISTORY_PASS)
    require((numeric_unique[pass_rows] >= 260).all() and (numeric_valid[pass_rows] >= 252).all(), "History PASS below master thresholds")
    insufficient_rows = history["History_Gate_State"].eq(HISTORY_INSUFFICIENT)
    require(((numeric_unique[insufficient_rows] < 260) | (numeric_valid[insufficient_rows] < 252)).all(), "Insufficient state without threshold failure")
    if not cache.empty:
        require(cache["WS_ID"].isin(standard_ids).all(), "History cache contains excluded security")
        require(cache["Provider"].eq(PROVIDER).all(), "History cache provider mismatch")
        require(cache["Date"].lt(brazil_today().isoformat()).all(), "History cache contains current or future session")

    require(len(eligibility) == 38 and eligibility["WS_ID"].nunique() == 38, "Eligibility ledger mismatch")
    require(set(eligibility["WS_ID"]) == standard_ids, "Eligibility set mismatch")
    require(len(ready) == int(eligibility["Eligibility_Plan_State"].eq(ELIGIBILITY_READY).sum()), "Ready subset mismatch")
    require(ready["History_Gate_State"].eq(HISTORY_PASS).all() if len(ready) else True, "Ready row without history PASS")
    require((ready["Canonical_Import_v0_33"].str.lower().eq("false")).all() if len(ready) else True, "Ready row imported")
    require((ready["Eligibility_Promotion_v0_33"].str.lower().eq("false")).all() if len(ready) else True, "Ready row promoted")

    require(len(low) == 28 and low["Liquidity_Class"].eq("LOW_LIQUIDITY_EXCEPTION_POOL").all(), "Low-liquidity pool mismatch")
    require(len(plan) == 98 and plan["WS_ID"].nunique() == 98, "Import plan must contain 98 unique source members")
    require(bool_series(plan["Source_Superset_Member"]).all(), "Import plan contains non-source member")
    require(plan["Primary_MIC"].eq(PRIMARY_MIC).all(), "Import plan contains non-BVMF")
    require(plan["Scalable_Tradeability_Status"].eq(SCALABLE_STATUS).all(), "Scalable evidence was invented")
    require((~bool_series(plan["Canonical_Import_v0_33"])).all(), "Canonical import marker enabled")
    require((~bool_series(plan["Eligibility_Promotion_v0_33"])).all(), "Eligibility promotion marker enabled")
    require(len(exclusions) == int(plan["Standard_Eligibility_Plan_State"].ne(ELIGIBILITY_READY).sum()), "Exclusion ledger mismatch")

    require(len(projection) == 98 and list(projection.columns) == list(master.columns) == EXPECTED_MASTER_COLUMNS, "Projection schema/row count mismatch")
    require(projection["WS_ID"].nunique() == 98, "Projection WS_ID duplicate")
    require(not projection.duplicated(["Primary_MIC", "Primary_Ticker"]).any(), "Projection primary identity duplicate")
    require(projection["Primary_MIC"].eq(PRIMARY_MIC).all(), "Projection contains non-BVMF")
    require(projection["Country"].eq("Brazil").all() and projection["Primary_Currency"].eq("BRL").all(), "Projection country/currency mismatch")
    require(projection["Primary_Universe_Index"].eq("BR_IBRX100").all(), "Projection index mismatch")
    require(projection["Index_Tags"].str.contains("BR_IBRX100", regex=False).all(), "Projection index tag missing")
    require(projection["Alpha_Symbol"].eq("").all(), "Projection contains Alpha symbol")
    require(projection["ISIN"].eq("").all(), "Projection contains guessed ISIN")

    require(len(collisions) == summary["collision_count"], "Collision count mismatch")
    if summary["collision_count"] == 0:
        require(summary["expected_current_master_rows_after_future_br_import"] == 1633, "Expected future row count must be 1633")
        require(summary["next_stage"] == "CURRENT_MASTER_BR_IBRX100_CONTROLLED_SOURCE_SUPERSET_IMPORT_AND_ELIGIBILITY_STATE_MATERIALIZATION", "Next stage mismatch")
    else:
        require(summary["expected_current_master_rows_after_future_br_import"] is None, "Collision case must not claim 1633")
        require(summary["next_stage"] == "CURRENT_MASTER_BR_IBRX100_IMPORT_COLLISION_REMEDIATION", "Collision next stage mismatch")

    for flag in [
        "canonical_master_import_v0_33", "universe_mutated", "eligibility_promotion_v0_33",
        "p0_run", "sector_rs_performed", "productive", "swing_u3k_frozen",
        "source_superset_complete", "alpha_vantage_allowed",
    ]:
        require(summary[flag] is False, f"Forbidden summary flag enabled: {flag}")
    require(len(master) == 1535, "Current Master workbook changed")
    require(sha256_file(Path(cfg["inputs"]["current_master_xlsx"])) == summary["current_master_sha256"], "Current Master bytes changed")
    require(sha256_file(Path(cfg["inputs"]["research_partial_1535"])) == summary["research_partial_1535_sha256"], "research_partial_1535 changed")
    versioned = Path(cfg["handoff_versioned"])
    stable = Path(cfg["handoff_current"])
    require(versioned.exists() and stable.exists() and versioned.read_bytes() == stable.read_bytes(), "Handoffs are not byte-identical")
    require("**Version:** v0.33" in stable.read_text(encoding="utf-8"), "CURRENT handoff is not v0.33")
    require(checkpoint["stage_version"] == VERSION and checkpoint["status"] == "PARTIAL", "Checkpoint mismatch")


def run(config_path: Path) -> None:
    cfg = read_json(config_path)
    paths, data = load_inputs(cfg)
    sets = validate_inputs(cfg, paths, data)
    standard, low = sets["standard"], sets["low"]
    source, liquidity, master = data["source"], data["liquidity"], data["master"]
    generated = now_utc()

    out = Path(cfg["output_dir"])
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    history, cache, price_asof = run_history_stage(standard, cfg)
    eligibility = build_standard_eligibility(standard, history, source)
    ready = eligibility[eligibility["Eligibility_Plan_State"].eq(ELIGIBILITY_READY)].copy().reset_index(drop=True)

    low_out = low.copy()
    low_out["Standard_Eligibility_Plan_State"] = "LOW_LIQUIDITY_EXCEPTION_POOL"
    low_out["Scalable_Tradeability_Status"] = SCALABLE_STATUS
    low_out["Canonical_Import_v0_33"] = False
    low_out["Eligibility_Promotion_v0_33"] = False

    liquidity_by = {txt(row["WS_ID"]): row.to_dict() for _, row in liquidity.iterrows()}
    projection = pd.DataFrame(
        [projection_row(row, liquidity_by, generated) for _, row in source.iterrows()],
        columns=list(master.columns),
    ).sort_values("WS_ID").reset_index(drop=True)
    collisions = build_collision_audit(projection, master)
    plan = build_import_plan(source, liquidity, history, eligibility)
    exclusions = build_standard_exclusions(plan)

    history_counts = {state: int((history["History_Gate_State"] == state).sum()) for state in [
        HISTORY_PASS, HISTORY_INSUFFICIENT, HISTORY_DQ_FAIL, HISTORY_DOWNLOAD_FAIL,
    ]}
    eligibility_counts = plan["Standard_Eligibility_Plan_State"].value_counts().to_dict()
    scalable_counts = plan["Scalable_Tradeability_Status"].value_counts().to_dict()
    collision_count = len(collisions)
    expected_rows = 1633 if collision_count == 0 else None
    next_stage = (
        "CURRENT_MASTER_BR_IBRX100_CONTROLLED_SOURCE_SUPERSET_IMPORT_AND_ELIGIBILITY_STATE_MATERIALIZATION"
        if collision_count == 0
        else "CURRENT_MASTER_BR_IBRX100_IMPORT_COLLISION_REMEDIATION"
    )
    controlled_state = "CONTROLLED_IMPORT_PLAN_READY" if collision_count == 0 else "CONTROLLED_IMPORT_BLOCKED_COLLISIONS"

    state_counts = pd.DataFrame([
        {"State_Family": "HISTORY_GATE", "State": key, "Count": value}
        for key, value in history_counts.items()
    ] + [
        {"State_Family": "STANDARD_ELIGIBILITY_PLAN", "State": key, "Count": int(value)}
        for key, value in eligibility_counts.items()
    ] + [
        {"State_Family": "SCALABLE", "State": key, "Count": int(value)}
        for key, value in scalable_counts.items()
    ])

    history.to_csv(out / "br_ibrx100_history_gate_v0.33.csv", index=False)
    eligibility.to_csv(out / "br_ibrx100_standard_eligibility_v0.33.csv", index=False)
    ready.to_csv(out / "br_ibrx100_standard_eligibility_ready_v0.33.csv", index=False)
    low_out.to_csv(out / "br_ibrx100_low_liquidity_exception_pool_v0.33.csv", index=False)
    exclusions.to_csv(out / "br_ibrx100_standard_exclusions_v0.33.csv", index=False)
    collisions.to_csv(out / "br_ibrx100_master_collision_audit_v0.33.csv", index=False)
    plan.to_csv(out / "br_ibrx100_controlled_master_import_plan_v0.33.csv", index=False)
    projection.to_csv(out / "br_ibrx100_master_import_projection_v0.33.csv", index=False)
    cache.to_csv(out / "br_ibrx100_history_cache_v0.33.csv", index=False)
    state_counts.to_csv(out / "eligibility_state_counts_v0.33.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": generated,
        "run_status": STAGE_ID + "_V0_33_COMPLETE",
        "stage_status": "PARTIAL",
        "status_label": STATUS,
        "lineage_scope": LINEAGE,
        "current_master_rows_before": 1535,
        "current_master_rows_after": 1535,
        "source_members": 98,
        "strict_ordinary": 79,
        "standard_liquidity_candidates": 38,
        "low_liquidity_exception_pool": 28,
        "liquidity_fail": 13,
        "instrument_fail": 19,
        "preferred_fail": 12,
        "unit_fail": 7,
        "history_candidates_checked": 38,
        "history_gate_counts": history_counts,
        "history_data_download_fail_count": history_counts[HISTORY_DQ_FAIL] + history_counts[HISTORY_DOWNLOAD_FAIL],
        "eligibility_state_counts": eligibility_counts,
        "standard_eligibility_ready": int((eligibility["Eligibility_Plan_State"] == ELIGIBILITY_READY).sum()),
        "scalable_status_counts": scalable_counts,
        "collision_count": collision_count,
        "controlled_import_plan_state": controlled_state,
        "import_plan_rows": len(plan),
        "master_projection_rows": len(projection),
        "expected_current_master_rows_after_future_br_import": expected_rows,
        "history_price_asof": price_asof,
        "provider": PROVIDER,
        "primary_mic": PRIMARY_MIC,
        "source_asof": SOURCE_ASOF,
        "history_unique_daily_bars_required": 260,
        "history_valid_completed_bars_required": 252,
        "replacement_ticker_history_used": False,
        "scalable_live_queries": 0,
        "current_master_sha256": sets["master_sha256_before"],
        "research_partial_1535_sha256": sets["research_sha256_before"],
        "workbook_sheets": data["sheets"],
        "universe_master_columns": list(master.columns),
        "canonical_master_import_v0_33": False,
        "universe_mutated": False,
        "eligibility_promotion_v0_33": False,
        "p0_run": False,
        "sector_rs_performed": False,
        "productive": False,
        "swing_u3k_frozen": False,
        "source_superset_complete": False,
        "alpha_vantage_allowed": False,
        "next_stage": next_stage,
    }
    write_json(out / "summary_v0.33.json", summary)

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_33",
        "run_id": "WS-LONG-CURRENT-MASTER-BR-IBRX100-ELIGIBILITY-PLAN-" + generated,
        "stage_id": STAGE_ID,
        "stage_version": VERSION,
        "start": generated,
        "end": now_utc(),
        "input_hash": stable_hash({key: sha256_file(path) for key, path in paths.items()}),
        "parameter_hash": stable_hash({key: value for key, value in cfg.items() if key != "inputs"}),
        "output_hash": stable_hash({
            "history": history_counts, "eligibility": eligibility_counts,
            "collisions": collision_count, "projection_rows": len(projection),
        }),
        "input_count": 98,
        "checked_count": 38,
        "pass_count": history_counts[HISTORY_PASS],
        "fail_count": 38 - history_counts[HISTORY_PASS],
        "standard_eligibility_ready": summary["standard_eligibility_ready"],
        "collision_count": collision_count,
        "status": "PARTIAL",
        "failed_source": "GLOBAL_SOURCE_SUPERSET_STILL_INCOMPLETE",
        "lineage_scope": LINEAGE,
        "universe_mutated": False,
        "eligibility_promotion_v0_33": False,
        "canonical_master_import_v0_33": False,
        "p0_run": False,
        "sector_rs_performed": False,
        "productive": False,
        "source_superset_complete": False,
        "swing_u3k_frozen": False,
        "next_stage": next_stage,
    }
    write_json(out / "stage_checkpoint_v0.33.json", checkpoint)
    write_handoff(Path(cfg["handoff_versioned"]), Path(cfg["handoff_current"]), summary)

    manifest_entries = []
    for name in OUTPUT_FILES:
        path = out / name
        manifest_entries.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    for path in [Path(cfg["handoff_versioned"]), Path(cfg["handoff_current"])]:
        manifest_entries.append({"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema": "WELT_SWING_MANIFEST_V0_33",
        "generated_utc": now_utc(),
        "stage_id": STAGE_ID,
        "version": VERSION,
        "files": manifest_entries,
    }
    write_json(out / "manifest_v0.33.json", manifest)
    validate_outputs(cfg)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def self_test() -> None:
    require(normalize_name("PETROBRAS S/A") == "PETROBRASSA", "normalize_name self-test")
    test = pd.DataFrame([
        {"Unique_Daily_Bars": 260, "Valid_Completed_Bars": 252},
        {"Unique_Daily_Bars": 259, "Valid_Completed_Bars": 252},
        {"Unique_Daily_Bars": 260, "Valid_Completed_Bars": 251},
    ])
    state = np.where(
        (test["Unique_Daily_Bars"] >= 260) & (test["Valid_Completed_Bars"] >= 252),
        HISTORY_PASS, HISTORY_INSUFFICIENT,
    ).tolist()
    require(state == [HISTORY_PASS, HISTORY_INSUFFICIENT, HISTORY_INSUFFICIENT], "history threshold self-test")
    require(STANDARD_CLASSES == {"PASS_PREFERRED", "PASS_STANDARD"}, "standard liquidity self-test")
    require(len(EXPECTED_MASTER_COLUMNS) == 22, "master schema self-test")
    print("SELF_TEST_OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    require(bool(args.config), "--config is required")
    cfg = read_json(Path(args.config))
    if args.validate:
        validate_outputs(cfg)
        print("RESULT_GATES_OK")
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
