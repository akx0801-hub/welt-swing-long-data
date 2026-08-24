#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCHEMA = "WELT_SWING_U3K_LIQUIDITY_FX_AUDIT_V0_5"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
STOCK_PRICE_DOWNLOADS_PERFORMED = False
FREE_FLOAT_MARKET_CAP_STATUS = "NOT_COLLECTED_BULK_RELIABLY_QA_ONLY"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def load_cfg(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().eq("true")


def normalize_currency(raw: Any, aliases: dict[str, str]) -> str:
    c = txt(raw).upper().replace(" ", "_")
    return aliases.get(c, c)


def instrument_gate(value: Any, pass_values: set[str], fail_tokens: list[str]) -> tuple[str, str]:
    v = txt(value).upper()
    if v in pass_values:
        return "PASS", "EXPLICIT_ALLOWED_INSTRUMENT_TYPE"
    if any(tok in v for tok in fail_tokens):
        return "FAIL", "EXPLICIT_DISALLOWED_INSTRUMENT_TYPE"
    return "NOT_VERIFIED", "INSTRUMENT_TYPE_NOT_STRICTLY_VERIFIED"


def extract_close_matrix(raw: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = [str(x) for x in raw.columns.get_level_values(0)]
        lvl1 = [str(x) for x in raw.columns.get_level_values(1)]
        if "Close" in lvl0:
            out = raw["Close"].copy()
        elif "Close" in lvl1:
            out = raw.xs("Close", axis=1, level=1).copy()
        else:
            return pd.DataFrame()
        if isinstance(out, pd.Series):
            out = out.to_frame(symbols[0] if symbols else "VALUE")
        return out

    if "Close" in raw.columns and len(symbols) == 1:
        return raw[["Close"]].rename(columns={"Close": symbols[0]})
    return pd.DataFrame()


def download_fx_history(currencies: list[str], cfg: dict) -> tuple[pd.DataFrame, dict]:
    import yfinance as yf

    cutoff = pd.Timestamp(cfg["fx_completed_cutoff_date"])
    non_eur = sorted(c for c in currencies if c and c != "EUR")
    direct = {c: f"{c}EUR=X" for c in non_eur}
    symbols = list(direct.values())

    frames = []
    unresolved = set(non_eur)
    direct_ok = []

    if symbols:
        raw = yf.download(
            tickers=symbols,
            period=str(cfg.get("fx_period", "6mo")),
            interval="1d",
            auto_adjust=False,
            actions=False,
            repair=False,
            group_by="ticker",
            threads=bool(cfg.get("fx_batch_threads", True)),
            progress=False,
            timeout=20,
        )
        close = extract_close_matrix(raw, symbols)
        if not close.empty:
            close.index = pd.to_datetime(close.index).tz_localize(None)
            close = close.loc[close.index <= cutoff]
            for c, sym in direct.items():
                if sym not in close.columns:
                    continue
                s = pd.to_numeric(close[sym], errors="coerce").dropna()
                s = s[s > 0]
                if s.empty:
                    continue
                frames.append(pd.DataFrame({
                    "day": s.index,
                    "Currency": c,
                    "FX_to_EUR": s.values,
                    "FX_Source_Symbol": sym,
                    "FX_Direction": "DIRECT_CCY_TO_EUR",
                }))
                unresolved.discard(c)
                direct_ok.append(c)

    reverse_ok = []
    if unresolved:
        reverse = {c: f"EUR{c}=X" for c in sorted(unresolved)}
        rsymbols = list(reverse.values())
        raw2 = yf.download(
            tickers=rsymbols,
            period=str(cfg.get("fx_period", "6mo")),
            interval="1d",
            auto_adjust=False,
            actions=False,
            repair=False,
            group_by="ticker",
            threads=bool(cfg.get("fx_batch_threads", True)),
            progress=False,
            timeout=20,
        )
        close2 = extract_close_matrix(raw2, rsymbols)
        if not close2.empty:
            close2.index = pd.to_datetime(close2.index).tz_localize(None)
            close2 = close2.loc[close2.index <= cutoff]
            for c, sym in reverse.items():
                if sym not in close2.columns:
                    continue
                s = pd.to_numeric(close2[sym], errors="coerce").dropna()
                s = s[s > 0]
                if s.empty:
                    continue
                inv = 1.0 / s
                frames.append(pd.DataFrame({
                    "day": inv.index,
                    "Currency": c,
                    "FX_to_EUR": inv.values,
                    "FX_Source_Symbol": sym,
                    "FX_Direction": "REVERSE_EUR_TO_CCY_INVERTED",
                }))
                unresolved.discard(c)
                reverse_ok.append(c)

    # EUR is identity and needs no external call.
    eur_dates = pd.date_range(
        cutoff - pd.Timedelta(days=200),
        cutoff,
        freq="D",
    )
    frames.append(pd.DataFrame({
        "day": eur_dates,
        "Currency": "EUR",
        "FX_to_EUR": 1.0,
        "FX_Source_Symbol": "EUR_IDENTITY",
        "FX_Direction": "IDENTITY",
    }))

    fx = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["day","Currency","FX_to_EUR","FX_Source_Symbol","FX_Direction"]
    )
    fx["day"] = pd.to_datetime(fx["day"]).dt.tz_localize(None)
    fx = fx.sort_values(["Currency","day"]).drop_duplicates(["Currency","day"], keep="last")

    meta = {
        "requested_currencies": currencies,
        "non_eur_requested": non_eur,
        "direct_resolved": sorted(direct_ok),
        "reverse_resolved": sorted(reverse_ok),
        "unresolved": sorted(unresolved),
        "resolved_count_including_eur": int(len(set(fx["Currency"].astype(str)))),
        "cutoff_date": cfg["fx_completed_cutoff_date"],
    }
    return fx, meta


def fx_lookup_series(fx: pd.DataFrame, currency: str, days: pd.Series) -> pd.Series:
    f = fx.loc[fx["Currency"].eq(currency), ["day","FX_to_EUR"]].copy()
    if f.empty:
        return pd.Series(np.nan, index=days.index, dtype=float)
    f = f.sort_values("day")
    q = pd.DataFrame({"day": pd.to_datetime(days).dt.tz_localize(None)})
    q["_row"] = np.arange(len(q))
    merged = pd.merge_asof(
        q.sort_values("day"),
        f,
        on="day",
        direction="backward",
        tolerance=pd.Timedelta(days=10),
    ).sort_values("_row")
    return pd.Series(merged["FX_to_EUR"].values, index=days.index, dtype=float)


def compute_liquidity_for_security(
    conn: sqlite3.Connection,
    ws_id: str,
    currency: str,
    quote_scale: float,
    fx: pd.DataFrame,
    min_usable_20: int,
) -> dict[str, Any]:
    from feature_builder import technical_valid_mask_for_features

    px = pd.read_sql_query(
        """
        SELECT day,open,high,low,close,adj_close,volume,stock_splits
        FROM price_daily
        WHERE ws_id=?
        ORDER BY day
        """,
        conn,
        params=[ws_id],
    )
    if px.empty:
        return {
            "Usable20": 0, "Usable60": 0,
            "MedianTurnover20_EUR": np.nan,
            "MedianTurnover60_EUR": np.nan,
            "FX_Coverage20": 0,
            "FX_Coverage60": 0,
            "Liquidity_Data_Status": "NO_CACHED_PRICE_ROWS",
        }

    px["day"] = pd.to_datetime(px["day"], errors="coerce").dt.tz_localize(None)
    px = px.dropna(subset=["day"]).sort_values("day")
    valid = technical_valid_mask_for_features(px)
    px = px.loc[valid].copy()
    if px.empty:
        return {
            "Usable20": 0, "Usable60": 0,
            "MedianTurnover20_EUR": np.nan,
            "MedianTurnover60_EUR": np.nan,
            "FX_Coverage20": 0,
            "FX_Coverage60": 0,
            "Liquidity_Data_Status": "NO_VALID_PRICE_ROWS",
        }

    # Turnover uses actual raw close * actual raw volume. Invalid OHLC rows were
    # removed above; no split-adjusted synthetic turnover is created.
    px["close_num"] = pd.to_numeric(px["close"], errors="coerce")
    px["volume_num"] = pd.to_numeric(px["volume"], errors="coerce")
    px["Turnover_Major_Native"] = (
        px["close_num"] * px["volume_num"] * float(quote_scale)
    )
    px.loc[
        (px["close_num"] <= 0) | (px["volume_num"] <= 0),
        "Turnover_Major_Native"
    ] = np.nan

    last60 = px.tail(60).copy()
    last60["FX_to_EUR"] = fx_lookup_series(fx, currency, last60["day"])
    last60["Turnover_EUR"] = last60["Turnover_Major_Native"] * last60["FX_to_EUR"]

    last20 = last60.tail(20).copy()
    usable20 = int(last20["Turnover_EUR"].notna().sum())
    usable60 = int(last60["Turnover_EUR"].notna().sum())
    fx20 = int(last20["FX_to_EUR"].notna().sum())
    fx60 = int(last60["FX_to_EUR"].notna().sum())

    med20 = float(last20["Turnover_EUR"].median()) if usable20 else np.nan
    med60 = float(last60["Turnover_EUR"].median()) if usable60 else np.nan

    if fx20 < min(len(last20), min_usable_20):
        status = "FX_OR_TURNOVER_COVERAGE_INSUFFICIENT_20"
    elif usable20 < min_usable_20:
        status = "USABLE_SESSIONS_BELOW_18_OF_20"
    else:
        status = "OK"

    return {
        "Usable20": usable20,
        "Usable60": usable60,
        "MedianTurnover20_EUR": med20,
        "MedianTurnover60_EUR": med60,
        "FX_Coverage20": fx20,
        "FX_Coverage60": fx60,
        "Liquidity_Data_Status": status,
        "Liquidity_Last_Session": txt(last60["day"].max().date()) if not last60.empty else "",
    }


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_cfg(cfg_path)
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    master = pd.read_csv(cfg["source_master"], keep_default_na=False, dtype=str)
    active = master.loc[bool_series(master["Active"])].copy()
    if len(active) != int(cfg["expected_active_rows"]):
        raise SystemExit(
            f"Active master rows {len(active)} != expected {cfg['expected_active_rows']}"
        )
    if active["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in active master")
    if active["Yahoo_Symbol"].astype(str).str.strip().eq("").any():
        raise SystemExit("Active master contains blank provider symbols")
    if active["Yahoo_Symbol"].astype(str).duplicated().any():
        raise SystemExit("Active master contains provider-symbol duplicates")

    aliases = {str(k).upper(): str(v).upper() for k, v in cfg["currency_aliases"].items()}
    active["Currency_Normalized"] = active["Primary_Currency"].map(
        lambda x: normalize_currency(x, aliases)
    )
    currencies = sorted(c for c in active["Currency_Normalized"].unique() if c)

    fx, fx_meta = download_fx_history(currencies, cfg)
    fx.to_csv(out_dir / "fx_history_to_eur_v0.5.csv", index=False)
    (out_dir / "fx_meta_v0.5.json").write_text(
        json.dumps(fx_meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    conn = sqlite3.connect(cfg["source_cache"])
    try:
        states = pd.read_sql_query("SELECT * FROM cache_state", conn)
        if len(states) != int(cfg["expected_active_rows"]):
            raise SystemExit(
                f"Operational cache states {len(states)} != active rows {cfg['expected_active_rows']}"
            )
        ready_n = int(states["status"].astype(str).eq("READY").sum())
        if ready_n != int(cfg["expected_ready_rows"]):
            raise SystemExit(
                f"READY states {ready_n} != expected {cfg['expected_ready_rows']}"
            )

        state = states.set_index("ws_id", drop=False)
        pass_values = set(str(x).upper() for x in cfg["instrument_pass_values"])
        fail_tokens = [str(x).upper() for x in cfg["instrument_fail_tokens"]]
        quote_scale_map = {str(k): float(v) for k, v in cfg["quote_scale_by_mic"].items()}
        liq_cfg = cfg["liquidity"]

        rows = []
        ready_ids = set(states.loc[states["status"].eq("READY"), "ws_id"].astype(str))

        for _, m in active.iterrows():
            ws = str(m["WS_ID"])
            if ws not in state.index:
                raise SystemExit(f"Missing cache_state for active {ws}")
            st = state.loc[ws]
            ig, ig_reason = instrument_gate(
                m.get("Instrument_Type", ""),
                pass_values,
                fail_tokens,
            )

            currency = str(m["Currency_Normalized"])
            scale = float(quote_scale_map.get(str(m.get("Primary_MIC", "")), 1.0))

            base_row = {
                "WS_ID": ws,
                "Name": m.get("Name", ""),
                "Country": m.get("Country", ""),
                "Primary_Universe_Index": m.get("Primary_Universe_Index", ""),
                "Primary_MIC": m.get("Primary_MIC", ""),
                "Primary_Ticker": m.get("Primary_Ticker", ""),
                "Yahoo_Symbol": m.get("Yahoo_Symbol", ""),
                "Primary_Currency": m.get("Primary_Currency", ""),
                "Currency_Normalized": currency,
                "Quote_Scale_To_Major_Currency": scale,
                "Instrument_Type": m.get("Instrument_Type", ""),
                "Instrument_Gate": ig,
                "Instrument_Gate_Reason": ig_reason,
                "Scalable_Tradeability_Status": m.get("Scalable_Tradeability_Status", ""),
                "Cache_Status": st["status"],
                "Cache_Reason": st["reason_code"],
                "Unique_Bars": st["unique_bars"],
                "Valid_Bars": st["valid_bars"],
                "FreeFloatMarketCap_EUR": np.nan,
                "FreeFloatMarketCap_Status": FREE_FLOAT_MARKET_CAP_STATUS,
            }

            if ws in ready_ids:
                liq = compute_liquidity_for_security(
                    conn=conn,
                    ws_id=ws,
                    currency=currency,
                    quote_scale=scale,
                    fx=fx,
                    min_usable_20=int(liq_cfg["minimum_usable_sessions_20"]),
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
            if liq["Liquidity_Data_Status"] != "OK" or pd.isna(med20):
                liq_gate = "NOT_VERIFIED"
                liq_bucket = "DATA_OR_FX_NOT_VERIFIED"
            elif med20 >= float(liq_cfg["preferred_eur"]):
                liq_gate = "PASS"
                liq_bucket = "PREFERRED_GE_20M"
            elif med20 >= float(liq_cfg["standard_pass_eur"]):
                liq_gate = "PASS"
                liq_bucket = "STANDARD_15_TO_20M"
            elif med20 >= float(liq_cfg["exception_floor_eur"]):
                liq_gate = "FAIL_STRICT"
                liq_bucket = "LOW_LIQUIDITY_EXCEPTION_5_TO_15M"
            else:
                liq_gate = "FAIL"
                liq_bucket = "FAIL_LT_5M"

            scalable = txt(m.get("Scalable_Tradeability_Status", "")).upper()
            scalable_gate = (
                "FAIL" if scalable == "SCALABLE_NOT_AVAILABLE"
                else "PASS_OR_NOT_VERIFIED"
            )

            eligibility = "PASS"
            blockers = []
            if st["status"] != "READY":
                eligibility = "FAIL"
                blockers.append(f"HISTORY_CACHE_{st['status']}")
            if ig == "FAIL":
                eligibility = "FAIL"
                blockers.append("INSTRUMENT_FAIL")
            elif ig == "NOT_VERIFIED":
                if eligibility != "FAIL":
                    eligibility = "NOT_VERIFIED"
                blockers.append("INSTRUMENT_NOT_VERIFIED")
            if liq_gate != "PASS":
                if liq_gate in {"FAIL", "FAIL_STRICT"}:
                    eligibility = "FAIL"
                elif eligibility != "FAIL":
                    eligibility = "NOT_VERIFIED"
                blockers.append(f"LIQUIDITY_{liq_bucket}")
            if scalable_gate == "FAIL":
                eligibility = "FAIL"
                blockers.append("SCALABLE_NOT_AVAILABLE")

            rows.append({
                **base_row,
                **liq,
                "Liquidity_Gate": liq_gate,
                "Liquidity_Bucket": liq_bucket,
                "Scalable_Gate": scalable_gate,
                "Strict_Eligibility": eligibility,
                "Blocking_Reasons": ";".join(blockers),
            })
    finally:
        conn.close()

    audit = pd.DataFrame(rows)
    audit.to_csv(out_dir / "eligibility_rows_v0.5.csv", index=False)

    standard_liq = audit.loc[
        audit["Cache_Status"].eq("READY")
        & audit["Liquidity_Gate"].eq("PASS")
    ].copy()

    provisional = standard_liq.copy()
    provisional["_ff_sort"] = pd.to_numeric(
        provisional["FreeFloatMarketCap_EUR"], errors="coerce"
    ).fillna(-1)
    provisional = provisional.sort_values(
        ["MedianTurnover20_EUR","MedianTurnover60_EUR","_ff_sort","WS_ID"],
        ascending=[False,False,False,True],
        kind="mergesort",
    ).drop(columns=["_ff_sort"])
    provisional.insert(0, "Provisional_Liquidity_Rank", np.arange(1, len(provisional)+1))
    provisional.to_csv(cfg["provisional_pool_csv"], index=False)

    strict_eligible = audit.loc[audit["Strict_Eligibility"].eq("PASS")].copy()
    strict_eligible["_ff_sort"] = pd.to_numeric(
        strict_eligible["FreeFloatMarketCap_EUR"], errors="coerce"
    ).fillna(-1)
    strict_eligible = strict_eligible.sort_values(
        ["MedianTurnover20_EUR","MedianTurnover60_EUR","_ff_sort","WS_ID"],
        ascending=[False,False,False,True],
        kind="mergesort",
    ).drop(columns=["_ff_sort"])

    unresolved_instr = audit.loc[
        audit["Cache_Status"].eq("READY")
        & audit["Liquidity_Gate"].eq("PASS")
        & audit["Instrument_Gate"].eq("NOT_VERIFIED")
    ].copy()
    unresolved_instr.to_csv(out_dir / "instrument_review_queue_v0.5.csv", index=False)

    low_pool = audit.loc[
        audit["Liquidity_Bucket"].eq("LOW_LIQUIDITY_EXCEPTION_5_TO_15M")
    ].copy()
    low_pool.to_csv(out_dir / "low_liquidity_exception_pool_v0.5.csv", index=False)

    non_ready = audit.loc[~audit["Cache_Status"].eq("READY")].copy()
    non_ready.to_csv(out_dir / "non_ready_exclusions_v0.5.csv", index=False)

    # Strict freeze is only valid if every otherwise standard-liquidity candidate
    # has a strict instrument decision and every currency needed for those rows
    # has resolved FX. Free-float market cap is QA-only and not a hard gate in
    # Swing Long DEV v0.1.
    fx_unresolved_standard = sorted(set(
        unresolved for unresolved in standard_liq["Currency_Normalized"].astype(str)
        if unresolved in set(fx_meta["unresolved"])
    ))
    strict_freeze_allowed = (
        len(unresolved_instr) == 0
        and len(fx_unresolved_standard) == 0
    )

    frozen_cols = list(strict_eligible.columns)
    if strict_freeze_allowed:
        frozen = strict_eligible.head(int(cfg["u3k_cap"])).copy()
        frozen.insert(0, "U3K_Rank", np.arange(1, len(frozen)+1))
    else:
        frozen = pd.DataFrame(columns=["U3K_Rank"] + frozen_cols)
    frozen.to_csv(cfg["strict_frozen_csv"], index=False)

    segment = audit.groupby(
        ["Primary_Universe_Index","Cache_Status","Liquidity_Bucket","Instrument_Gate"],
        dropna=False,
    ).size().reset_index(name="Rows")
    segment.to_csv(out_dir / "segment_gate_counts_v0.5.csv", index=False)

    status_counts = audit["Cache_Status"].value_counts().to_dict()
    liq_counts = audit["Liquidity_Bucket"].value_counts().to_dict()
    instrument_counts = audit["Instrument_Gate"].value_counts().to_dict()
    eligibility_counts = audit["Strict_Eligibility"].value_counts().to_dict()

    run_status = (
        "U3K_LIQUIDITY_FX_AUDIT_COMPLETE_STRICT_FREEZE_ALLOWED"
        if strict_freeze_allowed
        else "U3K_LIQUIDITY_FX_AUDIT_COMPLETE_WITH_BLOCKERS"
    )

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": run_status,
        "as_of_date": cfg["as_of_date"],
        "fx_completed_cutoff_date": cfg["fx_completed_cutoff_date"],
        "active_master_rows": int(len(active)),
        "cache_state_rows": int(len(audit)),
        "ready_rows": int((audit["Cache_Status"] == "READY").sum()),
        "cache_status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "fx": fx_meta,
        "liquidity_bucket_counts": {str(k): int(v) for k, v in liq_counts.items()},
        "instrument_gate_counts": {str(k): int(v) for k, v in instrument_counts.items()},
        "strict_eligibility_counts": {str(k): int(v) for k, v in eligibility_counts.items()},
        "standard_liquidity_ready_rows": int(len(standard_liq)),
        "provisional_liquidity_pool_rows": int(len(provisional)),
        "instrument_review_queue_rows": int(len(unresolved_instr)),
        "low_liquidity_exception_pool_rows": int(len(low_pool)),
        "strict_eligible_rows": int(len(strict_eligible)),
        "strict_freeze_allowed": bool(strict_freeze_allowed),
        "strict_frozen_rows": int(len(frozen)),
        "u3k_cap": int(cfg["u3k_cap"]),
        "free_float_market_cap_status": FREE_FLOAT_MARKET_CAP_STATUS,
        "free_float_market_cap_role": cfg["free_float_market_cap_policy"],
        "stock_price_downloads_performed": STOCK_PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": True,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "Swing Long DEV v0.1 makes MedianTurnover20_EUR the primary U3K liquidity gate: >=15m EUR standard PASS, 5-15m EUR exception pool, <5m EUR fail, with at least 18 usable of 20 sessions.",
            "The U3K cap sorts by MedianTurnover20_EUR, then MedianTurnover60_EUR, then reliable free-float market cap if available, then WS_ID.",
            "Free-float market cap is QA/research metadata in Swing Long DEV v0.1 and is not a standalone hard gate.",
            "FX is downloaded in one batch per direction and cached only as run output; no per-security FX calls are made.",
            "London and JSE quote-unit scale corrections are applied before EUR conversion.",
            "Instrument_Type values not explicitly verified as common/ordinary shares block STRICT U3K but do not erase the provisional liquidity pool.",
            "No P0 or stock-price refresh is executed."
        ],
    }
    (out_dir / "summary_v0.5.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Compact workbook for manual review.
    with pd.ExcelWriter(cfg["audit_xlsx"], engine="openpyxl") as xw:
        pd.DataFrame([{
            k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            for k, v in summary.items()
        }]).to_excel(xw, sheet_name="Summary", index=False)
        provisional.to_excel(xw, sheet_name="Provisional_Liquidity", index=False)
        unresolved_instr.to_excel(xw, sheet_name="Instrument_Review", index=False)
        low_pool.to_excel(xw, sheet_name="Low_Liq_Exception", index=False)
        non_ready.to_excel(xw, sheet_name="Non_READY", index=False)
        segment.to_excel(xw, sheet_name="Segment_Gates", index=False)
        fx.to_excel(xw, sheet_name="FX_History", index=False)

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def self_test() -> None:
    p = {"COMMON_STOCK","ORDINARY_SHARE","COMMON_SHARE"}
    f = ["PREFERRED","ETF","FUND","UNIT","WARRANT","RIGHT"]
    assert instrument_gate("COMMON_STOCK", p, f)[0] == "PASS"
    assert instrument_gate("PREFERRED_STOCK", p, f)[0] == "FAIL"
    assert instrument_gate("UNVERIFIED_EQUITY_SECURITY", p, f)[0] == "NOT_VERIFIED"

    aliases = {"GBX":"GBP","ZAC":"ZAR"}
    assert normalize_currency("GBX", aliases) == "GBP"
    assert normalize_currency("ZAc", aliases) == "ZAR"

    # Deterministic cap ordering: 20D first, 60D second, WS_ID tie-break.
    x = pd.DataFrame({
        "WS_ID":["B","A","C"],
        "MedianTurnover20_EUR":[20,20,30],
        "MedianTurnover60_EUR":[10,10,5],
        "FreeFloatMarketCap_EUR":[np.nan,np.nan,np.nan],
    })
    x["_ff_sort"] = pd.to_numeric(x["FreeFloatMarketCap_EUR"], errors="coerce").fillna(-1)
    y = x.sort_values(
        ["MedianTurnover20_EUR","MedianTurnover60_EUR","_ff_sort","WS_ID"],
        ascending=[False,False,False,True],
        kind="mergesort",
    )
    assert y["WS_ID"].tolist() == ["C","A","B"]

    print("U3K_LIQUIDITY_FX_AUDIT_V0_5_SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/u3k_liquidity_fx_v0.5.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
