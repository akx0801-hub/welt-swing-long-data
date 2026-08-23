#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np



def technical_valid_mask_for_features(df: pd.DataFrame) -> pd.Series:
    """Mirror price-cache hard bar validity; preserve raw cache, exclude bad bars from features."""
    o = pd.to_numeric(df["open"], errors="coerce")
    h = pd.to_numeric(df["high"], errors="coerce")
    l = pd.to_numeric(df["low"], errors="coerce")
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    finite = pd.concat([o,h,l,c], axis=1).replace([np.inf,-np.inf], np.nan).notna().all(axis=1)
    positive = (pd.concat([o,h,l,c], axis=1) > 0).all(axis=1)
    relation = (h >= l) & (c <= h) & (c >= l)
    nonnegative_volume = ~((v < 0) & v.notna())
    return finite & positive & relation & nonnegative_volume

def split_adjust_technical(df: pd.DataFrame) -> pd.DataFrame:
    """Create a split-only adjusted technical series.

    Prices before a split are divided by cumulative future split ratios.
    Volume before a split is multiplied by the same factor.
    Dividends are not used for this technical normalization.
    """
    x = df.copy().sort_values("day")
    split = pd.to_numeric(x["stock_splits"], errors="coerce").fillna(0.0)
    ratios = split.where(split > 0, 1.0)
    # cumulative factor including current row, then exclude current split by shifting forward
    future_including = ratios.iloc[::-1].cumprod().iloc[::-1]
    factor = future_including.shift(-1, fill_value=1.0).replace(0, 1.0)
    for c in ["open", "high", "low", "close"]:
        x[f"{c}_tech"] = pd.to_numeric(x[c], errors="coerce") / factor
    x["volume_tech"] = pd.to_numeric(x["volume"], errors="coerce") * factor
    x["split_factor_future"] = factor
    return x


def _last_return(s: pd.Series, n: int) -> float | None:
    s = s.dropna()
    if len(s) <= n or float(s.iloc[-n-1]) == 0:
        return None
    return float(s.iloc[-1] / s.iloc[-n-1] - 1.0)


def _safe_last(s: pd.Series) -> float | None:
    s = s.dropna()
    return None if s.empty else float(s.iloc[-1])


def build_features(db_path: str | Path, universe_csv: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        states = pd.read_sql_query("SELECT * FROM cache_state", conn)
        ready_ids = states.loc[states["status"] == "READY", "ws_id"].astype(str).tolist()
        if not ready_ids:
            return pd.DataFrame()
        placeholders = ",".join("?" for _ in ready_ids)
        px = pd.read_sql_query(
            f"SELECT * FROM price_daily WHERE ws_id IN ({placeholders}) ORDER BY ws_id, day",
            conn,
            params=ready_ids,
        )
    finally:
        conn.close()

    uni = pd.read_csv(universe_csv, dtype=str).fillna("")
    meta_cols = [c for c in [
        "WS_ID","Name","ISIN","Country","Primary_Ticker","Primary_Exchange",
        "Primary_MIC","Primary_Currency","Primary_Universe_Index","Index_Tags"
    ] if c in uni.columns]
    meta = uni[meta_cols].drop_duplicates("WS_ID") if "WS_ID" in uni.columns else pd.DataFrame()

    rows: list[dict] = []
    for ws_id, g in px.groupby("ws_id", sort=False):
        g = g.sort_values("day").copy()
        raw_bars = int(len(g))
        valid_mask = technical_valid_mask_for_features(g)
        g = g.loc[valid_mask].copy()
        excluded_invalid_bars = raw_bars - int(len(g))
        if g.empty:
            continue
        g = split_adjust_technical(g)
        c = pd.to_numeric(g["close_tech"], errors="coerce")
        h = pd.to_numeric(g["high_tech"], errors="coerce")
        l = pd.to_numeric(g["low_tech"], errors="coerce")
        v = pd.to_numeric(g["volume_tech"], errors="coerce")
        prev = c.shift(1)
        tr = pd.concat([(h-l).abs(), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
        atr14 = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
        ema20 = c.ewm(span=20, adjust=False, min_periods=20).mean()
        ema50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
        sma200 = c.rolling(200, min_periods=200).mean()
        high20 = h.rolling(20, min_periods=20).max()
        high60 = h.rolling(60, min_periods=60).max()
        high252 = h.rolling(252, min_periods=252).max()
        low20 = l.rolling(20, min_periods=20).min()
        low60 = l.rolling(60, min_periods=60).min()
        turnover = c * v

        last_close = _safe_last(c)
        def dist(last_val):
            if last_close is None or last_val in (None, 0): return None
            return float(last_close / last_val - 1.0)

        last_ema20, last_ema50, last_sma200 = _safe_last(ema20), _safe_last(ema50), _safe_last(sma200)
        last_high20, last_high60, last_high252 = _safe_last(high20), _safe_last(high60), _safe_last(high252)
        last_low20, last_low60 = _safe_last(low20), _safe_last(low60)
        last_atr = _safe_last(atr14)

        rows.append({
            "WS_ID": str(ws_id),
            "Yahoo_Symbol": str(g["yahoo_symbol"].iloc[-1]),
            "AsOf": str(g["day"].iloc[-1]),
            "Bars": int(len(g)),
            "Bars_Raw": raw_bars,
            "Bars_Used": int(len(g)),
            "Excluded_Invalid_Bars": excluded_invalid_bars,
            "Close_Raw": float(pd.to_numeric(g["close"], errors="coerce").iloc[-1]),
            "Close_Tech": last_close,
            "EMA20": last_ema20,
            "EMA50": last_ema50,
            "SMA200": last_sma200,
            "ATR14_Wilder_DEV": last_atr,
            "ATR14_Pct_DEV": None if last_atr is None or last_close in (None,0) else float(last_atr/last_close),
            "R5": _last_return(c, 5),
            "R20": _last_return(c, 20),
            "R60": _last_return(c, 60),
            "High20": last_high20,
            "High60": last_high60,
            "High252": last_high252,
            "Low20": last_low20,
            "Low60": last_low60,
            "Dist_EMA20": dist(last_ema20),
            "Dist_EMA50": dist(last_ema50),
            "Dist_SMA200": dist(last_sma200),
            "Dist_High252": dist(last_high252),
            "Range20_Pct": None if last_close in (None,0) or last_high20 is None or last_low20 is None else float((last_high20-last_low20)/last_close),
            "MedianVolume20_Tech": float(v.tail(20).median()) if len(v.dropna()) >= 20 else None,
            "MedianTurnover20_Native": float(turnover.tail(20).median()) if len(turnover.dropna()) >= 20 else None,
            "Split_Count": int((pd.to_numeric(g["stock_splits"], errors="coerce").fillna(0) > 0).sum()),
            "Feature_Status": "DEV_FEATURES_NOT_YET_PROMOTED",
        })

    out = pd.DataFrame(rows)
    if not meta.empty:
        out = meta.merge(out, on="WS_ID", how="right")
    return out
