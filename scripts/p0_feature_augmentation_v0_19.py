#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

# This script is stored in scripts/, beside the audited free-data modules.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SOURCE_ID = "YFINANCE_FREE"
ALPHA_VANTAGE_ALLOWED = False

SCHEMA = "WELT_SWING_P0_FEATURE_AUGMENTATION_V0_19"
PARAM_SCHEMA = "WELT_SWING_P0_PARAMETER_REGISTRY_V0_19"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_19"
MANIFEST_SCHEMA = "WELT_SWING_P0_FEATURE_AUGMENTATION_MANIFEST_V0_19"

CORE_NUMERIC = [
    "Close_Tech", "EMA20", "EMA50", "SMA200", "ATR14_Wilder_DEV",
    "R5", "R20", "R60", "High20", "High60", "High252",
    "Low20", "Low60", "Dist_EMA20", "Dist_EMA50", "Dist_SMA200",
    "Dist_High252", "Range20_Pct", "MedianVolume20_Tech",
    "MedianTurnover20_Native",
]

AUGMENTED_NUMERIC = [
    "RVOL20_Current", "TrueRange_Current", "TrueRange_ATR14_Ratio",
    "Range_Current_Pct", "Close_Location_0_1", "Gap_Pct",
    "Range5_Pct", "Range10_Pct", "Range20_Pct", "Range5_to_Range20",
    "TR_Mean5", "TR_Mean20", "TR_Mean5_to_20",
    "EMA20_Slope5_Pct", "EMA50_Slope10_Pct",
    "Consecutive_Close_Above_EMA20", "Consecutive_Close_Above_EMA50",
    "Consecutive_Close_Above_SMA200",
    "Days_Since_Cross_Above_EMA20", "Days_Since_Cross_Below_EMA20",
    "Days_Since_Cross_Above_EMA50", "Days_Since_Cross_Below_EMA50",
    "RecentLow10_vs_Prior10_Pct", "Distance_Low20_ATR",
    "Distance_Low60_ATR", "Distance_High20_ATR",
    "Max_Daily_Return5", "Min_Daily_Return5", "Max_Daily_Return20",
    "Min_Daily_Return20", "Max_TR_Preceding_ATR14_20",
    "Max_Volume_PrecedingMedian20_20", "Impulse_Return20_Max",
    "Impulse_Days_Ago", "PostImpulse_Min_vs_ImpulseClose",
    "PostImpulse_Latest_vs_ImpulseClose", "PostImpulse_Range_Pct",
    "ReturnStd5", "ReturnStd20", "ReturnStd5_to_20",
    "AsOf_Age_Calendar_Days",
]

DISTRIBUTION_FIELDS = CORE_NUMERIC + AUGMENTED_NUMERIC

def technical_valid_mask_for_features(df: pd.DataFrame) -> pd.Series:
    """Mirror the audited price-cache hard bar validity for local descriptors."""
    o = pd.to_numeric(df["open"], errors="coerce")
    h = pd.to_numeric(df["high"], errors="coerce")
    l = pd.to_numeric(df["low"], errors="coerce")
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    finite_mask = pd.concat([o, h, l, c], axis=1).replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    positive = (pd.concat([o, h, l, c], axis=1) > 0).all(axis=1)
    relation = (h >= l) & (c <= h) & (c >= l)
    nonnegative_volume = ~((v < 0) & v.notna())
    return finite_mask & positive & relation & nonnegative_volume


def split_adjust_technical(df: pd.DataFrame) -> pd.DataFrame:
    """Same split-only technical normalization used by feature_builder.py."""
    x = df.copy().sort_values("day")
    split = pd.to_numeric(x["stock_splits"], errors="coerce").fillna(0.0)
    ratios = split.where(split > 0, 1.0)
    future_including = ratios.iloc[::-1].cumprod().iloc[::-1]
    factor = future_including.shift(-1, fill_value=1.0).replace(0, 1.0)
    for col in ["open", "high", "low", "close"]:
        x[f"{col}_tech"] = pd.to_numeric(x[col], errors="coerce") / factor
    x["volume_tech"] = pd.to_numeric(x["volume"], errors="coerce") * factor
    x["split_factor_future"] = factor
    return x



def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(path: str | Path) -> str:
    p = Path(path)
    data = p.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def chunks(seq: Sequence[Any], n: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), n):
        yield list(seq[i:i + n])


def finite(v: Any) -> float | None:
    try:
        x = float(v)
    except Exception:
        return None
    return x if math.isfinite(x) else None


def safe_ratio(a: Any, b: Any) -> float | None:
    aa, bb = finite(a), finite(b)
    if aa is None or bb is None or bb == 0:
        return None
    return aa / bb


def safe_return(a: Any, b: Any) -> float | None:
    r = safe_ratio(a, b)
    return None if r is None else r - 1.0


def last_finite(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return None if x.empty else float(x.iloc[-1])


def n_return(s: pd.Series, n: int) -> float | None:
    x = pd.to_numeric(s, errors="coerce")
    if len(x) <= n:
        return None
    return safe_return(x.iloc[-1], x.iloc[-n - 1])


def trailing_streak(cond: pd.Series) -> int:
    n = 0
    for v in cond.fillna(False).astype(bool).iloc[::-1]:
        if not v:
            break
        n += 1
    return n


def days_since_last(cond: pd.Series) -> int | None:
    x = cond.fillna(False).astype(bool).to_numpy()
    idx = np.flatnonzero(x)
    return None if len(idx) == 0 else int(len(x) - 1 - idx[-1])


def rolling_range_pct(h: pd.Series, l: pd.Series, c: pd.Series, n: int) -> float | None:
    if len(c) < n:
        return None
    hi = finite(pd.to_numeric(h, errors="coerce").tail(n).max())
    lo = finite(pd.to_numeric(l, errors="coerce").tail(n).min())
    cl = finite(pd.to_numeric(c, errors="coerce").iloc[-1])
    if hi is None or lo is None or cl in (None, 0):
        return None
    return (hi - lo) / cl


def _base_and_augmented_features(g: pd.DataFrame, closed_bar_reference_date: date) -> dict[str, Any] | None:
    g = g.sort_values("day").copy()
    raw_bars = int(len(g))
    valid = technical_valid_mask_for_features(g)
    g = g.loc[valid].copy()
    excluded_invalid = raw_bars - int(len(g))
    if g.empty:
        return None

    g = split_adjust_technical(g)
    o = pd.to_numeric(g["open_tech"], errors="coerce")
    h = pd.to_numeric(g["high_tech"], errors="coerce")
    l = pd.to_numeric(g["low_tech"], errors="coerce")
    c = pd.to_numeric(g["close_tech"], errors="coerce")
    v = pd.to_numeric(g["volume_tech"], errors="coerce")

    prev_c = c.shift(1)
    tr = pd.concat([(h - l).abs(), (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    ema20 = c.ewm(span=20, adjust=False, min_periods=20).mean()
    ema50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
    sma200 = c.rolling(200, min_periods=200).mean()
    high20 = h.rolling(20, min_periods=20).max()
    high60 = h.rolling(60, min_periods=60).max()
    high252 = h.rolling(252, min_periods=252).max()
    low20 = l.rolling(20, min_periods=20).min()
    low60 = l.rolling(60, min_periods=60).min()
    turnover = c * v
    ret = c.pct_change(fill_method=None)

    close = last_finite(c)
    atr = last_finite(atr14)
    e20, e50, s200 = last_finite(ema20), last_finite(ema50), last_finite(sma200)
    hi20, hi60, hi252 = last_finite(high20), last_finite(high60), last_finite(high252)
    lo20, lo60 = last_finite(low20), last_finite(low60)

    def dist(x: Any) -> float | None:
        return safe_return(close, x)

    prior_vol_med20 = v.shift(1).rolling(20, min_periods=20).median()
    current_rvol = safe_ratio(last_finite(v), last_finite(prior_vol_med20))
    current_tr = last_finite(tr)
    current_range = None if close in (None, 0) else finite((h.iloc[-1] - l.iloc[-1]) / close)
    bar_range = finite(h.iloc[-1] - l.iloc[-1])
    clv = None if bar_range in (None, 0) else finite((c.iloc[-1] - l.iloc[-1]) / bar_range)
    gap = safe_return(o.iloc[-1], prev_c.iloc[-1]) if len(g) >= 2 else None

    range5 = rolling_range_pct(h, l, c, 5)
    range10 = rolling_range_pct(h, l, c, 10)
    range20_pct = rolling_range_pct(h, l, c, 20)
    tr_mean5 = last_finite(tr.rolling(5, min_periods=5).mean())
    tr_mean20 = last_finite(tr.rolling(20, min_periods=20).mean())

    above20 = c > ema20
    above50 = c > ema50
    above200 = c > sma200
    cross_above20 = above20 & ~(above20.shift(1, fill_value=False))
    cross_below20 = (~above20) & above20.shift(1, fill_value=False)
    cross_above50 = above50 & ~(above50.shift(1, fill_value=False))
    cross_below50 = (~above50) & above50.shift(1, fill_value=False)

    recent_low10 = finite(l.tail(10).min()) if len(l) >= 10 else None
    prior_low10 = finite(l.iloc[-20:-10].min()) if len(l) >= 20 else None
    higher_low_pct = safe_return(recent_low10, prior_low10)

    tr_preceding_atr = tr / atr14.shift(1)
    volume_preceding_med = v / prior_vol_med20

    ret_tail20 = ret.tail(20).replace([np.inf, -np.inf], np.nan)
    impulse_return = None
    impulse_days_ago = None
    post_min = None
    post_latest = None
    post_range = None
    if ret_tail20.notna().any():
        impulse_idx = ret_tail20.idxmax()
        impulse_return = finite(ret_tail20.loc[impulse_idx])
        all_idx = list(g.index)
        pos = all_idx.index(impulse_idx)
        impulse_days_ago = int(len(all_idx) - 1 - pos)
        impulse_close = finite(c.loc[impulse_idx])
        post = g.loc[impulse_idx:].copy()
        post_c = pd.to_numeric(post["close_tech"], errors="coerce")
        post_h = pd.to_numeric(post["high_tech"], errors="coerce")
        post_l = pd.to_numeric(post["low_tech"], errors="coerce")
        if impulse_close not in (None, 0):
            post_min = safe_return(post_c.min(), impulse_close)
            post_latest = safe_return(post_c.iloc[-1], impulse_close)
            post_hi, post_lo = finite(post_h.max()), finite(post_l.min())
            post_range = None if post_hi is None or post_lo is None else (post_hi - post_lo) / impulse_close

    std5 = finite(ret.tail(5).std(ddof=1)) if len(ret.dropna()) >= 5 else None
    std20 = finite(ret.tail(20).std(ddof=1)) if len(ret.dropna()) >= 20 else None

    asof = pd.to_datetime(g["day"].iloc[-1], errors="coerce")
    if pd.isna(asof):
        return None
    asof_date = asof.date()

    out: dict[str, Any] = {
        "AsOf": asof_date.isoformat(),
        "Bars": int(len(g)),
        "Bars_Raw": raw_bars,
        "Bars_Used": int(len(g)),
        "Excluded_Invalid_Bars": excluded_invalid,
        "Yahoo_Symbol_Observed": str(g["yahoo_symbol"].iloc[-1]),
        "Close_Raw": finite(pd.to_numeric(g["close"], errors="coerce").iloc[-1]),
        "Close_Tech": close,
        "EMA20": e20,
        "EMA50": e50,
        "SMA200": s200,
        "ATR14_Wilder_DEV": atr,
        "ATR14_Pct_DEV": safe_ratio(atr, close),
        "R5": n_return(c, 5),
        "R20": n_return(c, 20),
        "R60": n_return(c, 60),
        "High20": hi20,
        "High60": hi60,
        "High252": hi252,
        "Low20": lo20,
        "Low60": lo60,
        "Dist_EMA20": dist(e20),
        "Dist_EMA50": dist(e50),
        "Dist_SMA200": dist(s200),
        "Dist_High252": dist(hi252),
        "Range20_Pct": range20_pct,
        "MedianVolume20_Tech": finite(v.tail(20).median()) if len(v.dropna()) >= 20 else None,
        "MedianTurnover20_Native": finite(turnover.tail(20).median()) if len(turnover.dropna()) >= 20 else None,
        "RVOL20_Current": current_rvol,
        "TrueRange_Current": current_tr,
        "TrueRange_ATR14_Ratio": safe_ratio(current_tr, atr),
        "Range_Current_Pct": current_range,
        "Close_Location_0_1": clv,
        "Gap_Pct": gap,
        "Range5_Pct": range5,
        "Range10_Pct": range10,
        "Range5_to_Range20": safe_ratio(range5, range20_pct),
        "TR_Mean5": tr_mean5,
        "TR_Mean20": tr_mean20,
        "TR_Mean5_to_20": safe_ratio(tr_mean5, tr_mean20),
        "EMA20_Slope5_Pct": safe_return(ema20.iloc[-1], ema20.iloc[-6]) if len(ema20) >= 6 else None,
        "EMA50_Slope10_Pct": safe_return(ema50.iloc[-1], ema50.iloc[-11]) if len(ema50) >= 11 else None,
        "Consecutive_Close_Above_EMA20": trailing_streak(above20),
        "Consecutive_Close_Above_EMA50": trailing_streak(above50),
        "Consecutive_Close_Above_SMA200": trailing_streak(above200),
        "Days_Since_Cross_Above_EMA20": days_since_last(cross_above20),
        "Days_Since_Cross_Below_EMA20": days_since_last(cross_below20),
        "Days_Since_Cross_Above_EMA50": days_since_last(cross_above50),
        "Days_Since_Cross_Below_EMA50": days_since_last(cross_below50),
        "RecentLow10": recent_low10,
        "PriorLow10": prior_low10,
        "RecentLow10_vs_Prior10_Pct": higher_low_pct,
        "HigherLow10_Proxy": None if higher_low_pct is None else bool(higher_low_pct > 0),
        "Distance_Low20_ATR": None if atr in (None, 0) or close is None or lo20 is None else (close - lo20) / atr,
        "Distance_Low60_ATR": None if atr in (None, 0) or close is None or lo60 is None else (close - lo60) / atr,
        "Distance_High20_ATR": None if atr in (None, 0) or close is None or hi20 is None else (hi20 - close) / atr,
        "Max_Daily_Return5": finite(ret.tail(5).max()),
        "Min_Daily_Return5": finite(ret.tail(5).min()),
        "Max_Daily_Return20": finite(ret.tail(20).max()),
        "Min_Daily_Return20": finite(ret.tail(20).min()),
        "Max_TR_Preceding_ATR14_20": finite(tr_preceding_atr.tail(20).max()),
        "Max_Volume_PrecedingMedian20_20": finite(volume_preceding_med.tail(20).max()),
        "Impulse_Return20_Max": impulse_return,
        "Impulse_Days_Ago": impulse_days_ago,
        "PostImpulse_Min_vs_ImpulseClose": post_min,
        "PostImpulse_Latest_vs_ImpulseClose": post_latest,
        "PostImpulse_Range_Pct": post_range,
        "ReturnStd5": std5,
        "ReturnStd20": std20,
        "ReturnStd5_to_20": safe_ratio(std5, std20),
        "AsOf_Age_Calendar_Days": int((closed_bar_reference_date - asof_date).days),
        "Obs_R20_Warning_18pct": bool(n_return(c, 20) is not None and n_return(c, 20) >= 0.18),
        "Obs_R60_Warning_30pct": bool(n_return(c, 60) is not None and n_return(c, 60) >= 0.30),
        "HomeMarket_RS_Status": "NOT_IMPLEMENTED_V0_19",
        "Sector_RS_Status": "NOT_IMPLEMENTED_V0_19",
        "Feature_Status_v0_19": "DEV_AUGMENTED_FEATURES_THRESHOLD_NEUTRAL",
    }
    out["Core_Feature_Complete_v0_19"] = all(finite(out.get(k)) is not None for k in CORE_NUMERIC)
    return out


def build_feature_rows(db_path: str | Path, universe: pd.DataFrame, closed_bar_reference_date: date) -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = sqlite3.connect(db_path)
    try:
        states = pd.read_sql_query("SELECT * FROM cache_state", conn)
        px = pd.read_sql_query("SELECT * FROM price_daily ORDER BY ws_id, day", conn)
    finally:
        conn.close()

    state_by = states.set_index("ws_id", drop=False) if not states.empty else pd.DataFrame()
    groups = {str(k): v.copy() for k, v in px.groupby("ws_id", sort=False)} if not px.empty else {}

    meta_cols = [c for c in [
        "Research_Partial_Rank_v0_16", "WS_ID", "Name", "Country", "Primary_Ticker",
        "Primary_MIC", "Primary_Currency", "Primary_Universe_Index", "Yahoo_Symbol",
        "Scalable_Tradeability_Status",
    ] if c in universe.columns]

    feature_rows: list[dict[str, Any]] = []
    quarantine_rows: list[dict[str, Any]] = []
    for _, u in universe.iterrows():
        ws = str(u["WS_ID"])
        meta = {c: u.get(c, "") for c in meta_cols}
        st = state_by.loc[ws] if (not states.empty and ws in state_by.index) else None
        cache_status = "NO_CACHE_STATE" if st is None else str(st.get("status", ""))
        cache_reason = "" if st is None else str(st.get("reason_code", "") or "")
        yahoo_symbol = "" if st is None else str(st.get("yahoo_symbol", "") or "")
        mapping_status = "" if st is None else str(st.get("mapping_status", "") or "")

        reason = None
        feat = None
        if st is None:
            reason = "NO_CACHE_STATE"
        elif cache_status != "READY":
            reason = f"CACHE_{cache_status}:{cache_reason or 'NO_REASON'}"
        elif ws not in groups:
            reason = "NO_PRICE_ROWS"
        else:
            feat = _base_and_augmented_features(groups[ws], closed_bar_reference_date)
            if feat is None:
                reason = "FEATURE_BUILD_FAILED_OR_NO_VALID_BARS"
            elif not bool(feat.get("Core_Feature_Complete_v0_19")):
                reason = "CORE_FEATURE_INCOMPLETE"

        if reason is None and feat is not None:
            row = {**meta, "Yahoo_Symbol_v0_19": yahoo_symbol, "Yahoo_Mapping_Status_v0_19": mapping_status,
                   "Cache_Status_v0_19": cache_status, "Cache_Reason_v0_19": cache_reason, **feat}
            feature_rows.append(row)
        else:
            quarantine_rows.append({
                **meta,
                "Yahoo_Symbol_v0_19": yahoo_symbol,
                "Yahoo_Mapping_Status_v0_19": mapping_status,
                "Cache_Status_v0_19": cache_status,
                "Cache_Reason_v0_19": cache_reason,
                "Feature_Augmentation_Status_v0_19": "QUARANTINED",
                "QuarantineReason_v0_19": reason or "UNKNOWN",
            })

    return pd.DataFrame(feature_rows), pd.DataFrame(quarantine_rows)


def distribution_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for col in DISTRIBUTION_FIELDS:
        if col not in df.columns:
            rows.append({"Field": col, "Rows_Present": 0, "Rows_Missing": len(df), "Coverage_Pct": 0.0})
            continue
        x = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        row: dict[str, Any] = {
            "Field": col,
            "Rows_Present": int(len(x)),
            "Rows_Missing": int(len(df) - len(x)),
            "Coverage_Pct": round(100.0 * len(x) / max(1, len(df)), 4),
        }
        if not x.empty:
            q = x.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
            row.update({
                "Min": float(x.min()), "P05": float(q.loc[0.05]), "P25": float(q.loc[0.25]),
                "Median": float(q.loc[0.5]), "P75": float(q.loc[0.75]), "P95": float(q.loc[0.95]),
                "Max": float(x.max()),
            })
        rows.append(row)
    return pd.DataFrame(rows)


def lane_capability_table() -> pd.DataFrame:
    rows = [
        ["BREAKOUT_COMPRESSION_VCP", "PARTIAL_AUGMENTED", "High20;High60;High252;Range5_Pct;Range10_Pct;Range20_Pct;Range5_to_Range20;TR_Mean5_to_20;RVOL20_Current;Max_TR_Preceding_ATR14_20", "validated pivot/base/VCP detector; validated lane thresholds"],
        ["PULLBACK_RETEST", "PARTIAL_AUGMENTED", "EMA20;EMA50;SMA200;Dist_EMA20;Dist_EMA50;Consecutive_Close_Above_EMA20;Consecutive_Close_Above_EMA50;RecentLow10_vs_Prior10_Pct;Distance_Low20_ATR", "former-breakout-zone detector; horizontal support detector; validated controlled-pullback sequence"],
        ["RECLAIM", "PARTIAL_AUGMENTED", "Days_Since_Cross_Above_EMA20;Days_Since_Cross_Above_EMA50;Consecutive_Close_Above_EMA20;Consecutive_Close_Above_EMA50;RecentLow10_vs_Prior10_Pct", "validated multi-day reclaim/confirmation rule"],
        ["QUIET_STRENGTH_RELATIVE_STRENGTH", "PARTIAL_AUGMENTED", "R20;R60;EMA20_Slope5_Pct;EMA50_Slope10_Pct;Range5_to_Range20;TR_Mean5_to_20", "20d/60d home-market RS; sector RS; validated excess-momentum rule"],
        ["POST_EVENT_DRIFT", "PARTIAL_AUGMENTED", "Impulse_Return20_Max;Impulse_Days_Ago;PostImpulse_Min_vs_ImpulseClose;PostImpulse_Latest_vs_ImpulseClose;PostImpulse_Range_Pct;RVOL20_Current", "event identity/time; validated impulse/hold/drift thresholds"],
        ["CONTROLLED_MEAN_REVERSION", "PARTIAL_AUGMENTED", "Distance_Low20_ATR;Distance_Low60_ATR;ReturnStd5;ReturnStd20;ReturnStd5_to_20;EMA20_Slope5_Pct;EMA50_Slope10_Pct", "validated stabilization sequence; validated falling-knife detector; definable invalidation rule"],
    ]
    return pd.DataFrame(rows, columns=["Lane", "Capability_v0_19", "Available_Descriptive_Inputs", "Still_Missing_or_Unvalidated"]).assign(
        Automated_P0_Decision_v0_19="NOT_ALLOWED"
    )


def parameter_registry() -> dict[str, Any]:
    return {
        "schema": PARAM_SCHEMA,
        "validation_status": "HYPOTHESIS_ONLY_NOT_VALIDATED",
        "p0_numeric_pass_thresholds": [],
        "explicit_master_spec_numbers_not_promoted_to_p0_pass": [
            {"name": "later_breakout_entry_distance", "value": "about <=1 ATR over pivot", "use": "LATER_STAGE_REFERENCE_ONLY_NOT_P0_PASS"},
            {"name": "later_breakout_rvol_confirmation", "value": "about >=1.3", "use": "LATER_A_CONFIRMATION_ONLY_NOT_P0_PASS"},
            {"name": "later_climax_range_warning", "value": "about >2 ATR daily range with extreme volume and weak close", "use": "LATER_STAGE_REFERENCE_ONLY_NOT_P0_PASS"},
            {"name": "runup_warning_20d", "value": 0.18, "use": "WARNING_ONLY_NOT_AUTOMATIC_EXCLUSION"},
            {"name": "runup_warning_60d", "value": 0.30, "use": "WARNING_ONLY_NOT_AUTOMATIC_EXCLUSION"},
        ],
        "policy": [
            "No numeric P0 PASS threshold is invented in v0.19.",
            "Observed feature distributions are evidence for later parameter validation, not eligibility rules.",
            "Home-market and sector relative-strength fields remain explicitly NOT_IMPLEMENTED_V0_19.",
            "A future automated P0 requires separately versioned and validated lane logic before activation.",
        ],
    }


def write_empty_or_frame(df: pd.DataFrame, path: Path, columns: list[str] | None = None) -> None:
    if df.empty and columns is not None:
        pd.DataFrame(columns=columns).to_csv(path, index=False)
    else:
        df.to_csv(path, index=False)


def run(config_path: Path) -> None:
    # Price acquisition is delegated to the already-audited project free-data module.
    from price_cache import (
        ALPHA_VANTAGE_ALLOWED as PRICE_CACHE_ALPHA_ALLOWED,
        FreeDataConfig, SQLitePriceCache, YFinanceBatchClient,
        YFinancePriceCacheRunner, build_yahoo_symbol_map,
    )

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if ALPHA_VANTAGE_ALLOWED or PRICE_CACHE_ALPHA_ALLOWED:
        raise SystemExit("Governance violation: Alpha Vantage must be disabled")
    if cfg.get("alpha_vantage_allowed") is not False:
        raise SystemExit("Config governance violation: alpha_vantage_allowed must be false")

    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Frozen prior checkpoint gates. SHA-256 validates content; GitHub workflow also gates blob SHAs.
    s18_path = Path(cfg["source_summary_v0_18"])
    q18_path = Path(cfg["source_quarantine_v0_18"])
    partial_path = Path(cfg["source_partial_universe_v0_16"])
    s18 = json.loads(s18_path.read_text(encoding="utf-8"))
    if s18["run_status"] != "P0_RESEARCH_PARTIAL_INTEGRITY_FIX_V0_18_COMPLETE":
        raise SystemExit("v0.18 source summary not complete")
    if int(s18["partial_rows"]) != int(cfg["expected_partial_rows"]):
        raise SystemExit("v0.18 row-count gate failed")
    if int(s18["quarantine_rows_v0_18"]) != int(cfg["expected_prior_quarantine_rows"]):
        raise SystemExit("v0.18 quarantine-count gate failed")
    for key, path in [
        ("expected_source_summary_v0_18_sha256", s18_path),
        ("expected_source_quarantine_v0_18_sha256", q18_path),
        ("expected_partial_universe_sha256", partial_path),
    ]:
        expected = cfg.get(key)
        if expected and sha256_file(path) != expected:
            raise SystemExit(f"frozen SHA-256 gate failed for {path}")

    partial = pd.read_csv(partial_path, keep_default_na=False, dtype=str)
    if len(partial) != int(cfg["expected_partial_rows"]):
        raise SystemExit("partial universe count mismatch")
    if "WS_ID" not in partial.columns or not partial["WS_ID"].is_unique:
        raise SystemExit("partial universe WS_ID must be present and unique")
    prior_q = pd.read_csv(q18_path, keep_default_na=False, dtype=str)
    if len(prior_q) != int(cfg["expected_prior_quarantine_rows"]):
        raise SystemExit("prior quarantine count mismatch")

    request_start = date.fromisoformat(cfg["request_start"])
    request_end_exclusive = date.fromisoformat(cfg["request_end_exclusive"])
    closed_bar_reference_date = date.fromisoformat(cfg["closed_bar_reference_date"])
    if not (request_start < closed_bar_reference_date < request_end_exclusive):
        raise SystemExit("invalid fixed closed-bar window")

    batch_size = int(cfg["batch_size"])
    if batch_size < 2:
        raise SystemExit("batch_size must be >=2; no per-security fanout architecture")
    fd_cfg = FreeDataConfig(
        batch_size=batch_size,
        timeout_seconds=float(cfg.get("timeout_seconds", 15.0)),
        max_identical_retries=int(cfg.get("max_identical_retries", 1)),
        retry_sleep_seconds=float(cfg.get("retry_sleep_seconds", 2.0)),
        repair_anomalies=False,
    )
    fd_cfg.validate()

    runtime_db = Path(cfg["runtime_db"])
    runtime_db.parent.mkdir(parents=True, exist_ok=True)
    for p in [runtime_db, Path(str(runtime_db) + "-wal"), Path(str(runtime_db) + "-shm")]:
        if p.exists():
            p.unlink()

    mapping = build_yahoo_symbol_map(partial, override_path=cfg.get("yahoo_override_file"))
    mapping.to_csv(out_dir / "yahoo_symbol_map_v0.19.csv", index=False)

    cache = SQLitePriceCache(runtime_db)
    try:
        runner = YFinancePriceCacheRunner(cache, YFinanceBatchClient(config=fd_cfg), config=fd_cfg)
        mapped = mapping[mapping["Yahoo_Symbol"].notna()].copy()
        unmapped = mapping[mapping["Yahoo_Symbol"].isna()].copy()
        for _, r in unmapped.iterrows():
            cache.upsert_state({
                "ws_id": r.WS_ID, "yahoo_symbol": None, "mapping_status": r.Yahoo_Mapping_Status,
                "status": "MAPPING_PENDING", "reason_code": r.Yahoo_Mapping_Status,
                "unique_bars": 0, "valid_bars": 0, "repaired_rows": 0,
                "suspicious_returns": 0, "zero_volume_share": None,
                "first_bar_date": None, "last_bar_date": None,
                "last_fetch_utc": utc_now(), "batch_id": None, "last_error": None,
            })

        missing_symbols: list[str] = []
        # Fixed explicit date window. This deliberately avoids run_initial(period='2y') so an
        # in-progress 2026-08-24 bar cannot enter the research snapshot.
        for idxs in chunks(list(mapped.index), batch_size):
            _, missing = runner._process_batch(  # audited runner primitive; fixed-window orchestration only
                mapped.loc[idxs], period=None, start=request_start, end=request_end_exclusive,
                repair_pass=False, as_of=closed_bar_reference_date,
            )
            missing_symbols.extend(missing)

        # One bounded rescue wave, still using the same fixed date window. This is not a
        # one-symbol-per-security lookup architecture; missing names are regrouped.
        rescue_names = sorted(set(s for s in missing_symbols if s))
        if rescue_names:
            rescue_df = mapped[mapped["Yahoo_Symbol"].isin(rescue_names)].copy()
            for idxs in chunks(list(rescue_df.index), batch_size):
                runner._process_batch(
                    rescue_df.loc[idxs], period=None, start=request_start, end=request_end_exclusive,
                    repair_pass=False, as_of=closed_bar_reference_date,
                )
        cache.conn.commit()

        batch_log = pd.read_sql_query("SELECT * FROM batch_log ORDER BY started_utc, batch_id", cache.conn)
        cache_state = pd.read_sql_query("SELECT * FROM cache_state ORDER BY ws_id", cache.conn)
    finally:
        cache.close()

    batch_log.to_csv(out_dir / "yfinance_batch_log_v0.19.csv", index=False)
    cache_state.to_csv(out_dir / "price_cache_state_v0.19.csv", index=False)

    augmented, quarantine = build_feature_rows(runtime_db, partial, closed_bar_reference_date)
    if not augmented.empty and augmented["WS_ID"].duplicated().any():
        raise SystemExit("duplicate WS_ID in augmented features")
    if not quarantine.empty and quarantine["WS_ID"].duplicated().any():
        raise SystemExit("duplicate WS_ID in quarantine")
    if set(augmented.get("WS_ID", pd.Series(dtype=str))) & set(quarantine.get("WS_ID", pd.Series(dtype=str))):
        raise SystemExit("WS_ID overlap between augmented and quarantine")
    if len(augmented) + len(quarantine) != len(partial):
        raise SystemExit("coverage partition invariant failed")

    # A fixed-window run must not include the still-open/forbidden end-exclusive date.
    if not augmented.empty:
        asof_dt = pd.to_datetime(augmented["AsOf"], errors="coerce")
        if asof_dt.isna().any():
            raise SystemExit("invalid AsOf in augmented output")
        if (asof_dt.dt.date >= request_end_exclusive).any():
            raise SystemExit("bar on/after request_end_exclusive detected")

    augmented_path = out_dir / "p0_feature_augmented_v0.19.csv"
    quarantine_path = out_dir / "p0_feature_quarantine_v0.19.csv"
    write_empty_or_frame(augmented, augmented_path, columns=["WS_ID", "Feature_Status_v0_19"])
    write_empty_or_frame(quarantine, quarantine_path, columns=["WS_ID", "QuarantineReason_v0_19"])

    prior_ids = set(prior_q["WS_ID"].astype(str))
    current_aug_ids = set(augmented["WS_ID"].astype(str)) if not augmented.empty else set()
    current_q_ids = set(quarantine["WS_ID"].astype(str)) if not quarantine.empty else set()
    recovered_ids = prior_ids & current_aug_ids
    still_q_ids = prior_ids & current_q_ids

    prior_meta_cols = [c for c in ["WS_ID", "Name", "Country", "Primary_MIC", "Primary_Currency", "QuarantineReason_v0_18"] if c in prior_q.columns]
    recovered = prior_q[prior_q["WS_ID"].isin(recovered_ids)][prior_meta_cols].copy()
    if not recovered.empty:
        recovered["Recovery_Status_v0_19"] = "RECOVERED_BY_FRESH_FIXED_WINDOW_YFINANCE_ACQUISITION"
        sym_map = augmented.set_index("WS_ID")["Yahoo_Symbol_v0_19"].to_dict()
        recovered["Yahoo_Symbol_v0_19"] = recovered["WS_ID"].map(sym_map)
    write_empty_or_frame(recovered, out_dir / "recovered_prior_quarantine_v0.19.csv",
                         columns=prior_meta_cols + ["Recovery_Status_v0_19", "Yahoo_Symbol_v0_19"])

    dist = distribution_table(augmented)
    dist.to_csv(out_dir / "p0_feature_distribution_v0.19.csv", index=False)
    lane = lane_capability_table()
    lane.to_csv(out_dir / "p0_lane_feature_capability_v0.19.csv", index=False)

    if augmented.empty:
        asof_dist = pd.DataFrame(columns=["AsOf", "Rows"])
    else:
        asof_dist = augmented.groupby("AsOf", dropna=False).size().reset_index(name="Rows").sort_values("AsOf")
    asof_dist.to_csv(out_dir / "p0_asof_distribution_v0.19.csv", index=False)

    params = parameter_registry()
    (out_dir / "p0_parameter_registry_v0.19.json").write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")

    state_counts = cache_state["status"].value_counts(dropna=False).to_dict() if not cache_state.empty else {}
    reason_counts = quarantine["QuarantineReason_v0_19"].value_counts(dropna=False).to_dict() if not quarantine.empty else {}
    batch_invocations = int(len(batch_log))
    retry_invocations = int(pd.to_numeric(batch_log.get("retry_count", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not batch_log.empty else 0
    yf_download_invocations = batch_invocations + retry_invocations
    normal_batches = int(math.ceil(len(mapped) / batch_size)) if len(mapped) else 0
    rescue_batches = max(0, batch_invocations - normal_batches)

    if len(augmented) == 0:
        run_status = "P0_FEATURE_AUGMENTATION_V0_19_COMPLETE_WITH_SOURCE_BLOCK"
    elif len(quarantine) > 0:
        run_status = "P0_FEATURE_AUGMENTATION_V0_19_COMPLETE_WITH_PARTIAL_COVERAGE"
    else:
        run_status = "P0_FEATURE_AUGMENTATION_V0_19_COMPLETE"

    summary = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "run_status": run_status,
        "run_id": cfg["run_id"],
        "input_snapshot_id": s18["input_snapshot_id"],
        "input_rows": int(len(partial)),
        "augmented_feature_rows": int(len(augmented)),
        "feature_quarantine_rows": int(len(quarantine)),
        "prior_v0_18_quarantine_rows": int(len(prior_ids)),
        "recovered_prior_quarantine_rows": int(len(recovered_ids)),
        "still_quarantined_prior_rows": int(len(still_q_ids)),
        "prior_quarantine_recovered_ws_ids": sorted(recovered_ids),
        "prior_quarantine_still_quarantined_ws_ids": sorted(still_q_ids),
        "quarantine_reason_counts": reason_counts,
        "cache_status_counts": state_counts,
        "request_start": request_start.isoformat(),
        "request_end_exclusive": request_end_exclusive.isoformat(),
        "closed_bar_reference_date": closed_bar_reference_date.isoformat(),
        "batch_size": batch_size,
        "normal_batch_invocations": normal_batches,
        "rescue_batch_invocations": rescue_batches,
        "yf_download_batch_invocations": yf_download_invocations,
        "yf_batch_log_rows": batch_invocations,
        "yf_retry_invocations": retry_invocations,
        "network_http_request_count_measured": False,
        "network_http_request_count": None,
        "web_calls_per_security": False,
        "data_source": SOURCE_ID,
        "price_downloads_performed": True,
        "fx_downloads_performed": False,
        "news_downloads_performed": False,
        "fundamentals_downloaded": False,
        "scalable_execution_checked": False,
        "p0_run": False,
        "p0_survivor_rows": 0,
        "p0_lane_decisions_made": False,
        "validated_automated_p0_run": False,
        "automated_p0_ready": False,
        "parameter_validation_status": params["validation_status"],
        "p0_numeric_pass_threshold_count": 0,
        "home_market_rs_status": "NOT_IMPLEMENTED_V0_19",
        "sector_rs_status": "NOT_IMPLEMENTED_V0_19",
        "strict_u3k_frozen": False,
        "full_scan_claim": False,
        "research_partial_mode": True,
        "productive_trading_authority": False,
        "alpha_vantage_allowed": False,
        "canonical_master_mutated": False,
        "historical_v0_18_artifacts_mutated": False,
        "next_stage": "P0_RELATIVE_STRENGTH_AUGMENTATION_AND_LANE_PARAMETER_VALIDATION",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
    }
    (out_dir / "summary_v0.19.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "run_id": cfg["run_id"],
        "stage_id": "P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION",
        "stage_version": "v0.19",
        "status": "PARTIAL",
        "input_count": int(len(partial)),
        "checked_count": int(len(partial)),
        "augmented_count": int(len(augmented)),
        "quarantine_count": int(len(quarantine)),
        "pass_count": 0,
        "fail_count": 0,
        "p0_survivor_count": 0,
        "validated_automated_p0_run": False,
        "automated_p0_ready": False,
        "next_stage": summary["next_stage"],
    }
    (out_dir / "stage_checkpoint_v0.19.json").write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    # Manifest hashes output evidence only; runtime SQLite is intentionally excluded.
    output_files = sorted(p for p in out_dir.iterdir() if p.is_file() and p.name != "feature_augmentation_manifest_v0.19.json")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "generated_utc": utc_now(),
        "source_data": SOURCE_ID,
        "alpha_vantage_allowed": False,
        "runtime_sqlite_committed": False,
        "fixed_closed_bar_window": True,
        "request_start": request_start.isoformat(),
        "request_end_exclusive": request_end_exclusive.isoformat(),
        "closed_bar_reference_date": closed_bar_reference_date.isoformat(),
        "batch_size": batch_size,
        "yf_download_batch_invocations": yf_download_invocations,
        "network_http_request_count_measured": False,
        "files": {str(p): {"sha256": sha256_file(p), "git_blob_sha": git_blob_sha(p), "bytes": p.stat().st_size} for p in output_files},
    }
    (out_dir / "feature_augmentation_manifest_v0.19.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


def self_test() -> None:
    assert SCHEMA.endswith("V0_19")
    assert ALPHA_VANTAGE_ALLOWED is False
    n = 320
    days = pd.bdate_range("2025-01-02", periods=n)
    close = pd.Series(np.linspace(100.0, 140.0, n), index=days)
    frame = pd.DataFrame({
        "day": days.strftime("%Y-%m-%d"),
        "open": close.to_numpy() * 0.999,
        "high": close.to_numpy() * 1.01,
        "low": close.to_numpy() * 0.99,
        "close": close.to_numpy(),
        "adj_close": close.to_numpy(),
        "volume": np.linspace(1_000_000, 1_200_000, n),
        "dividends": 0.0,
        "stock_splits": 0.0,
        "repaired": 0,
        "yahoo_symbol": "TEST",
    })
    feat = _base_and_augmented_features(frame, days[-1].date())
    assert feat is not None
    assert feat["Core_Feature_Complete_v0_19"] is True
    assert feat["Bars"] == n
    assert feat["AsOf_Age_Calendar_Days"] == 0
    assert feat["RVOL20_Current"] is not None and feat["RVOL20_Current"] > 0
    assert 0 <= feat["Close_Location_0_1"] <= 1
    assert feat["HomeMarket_RS_Status"] == "NOT_IMPLEMENTED_V0_19"
    assert parameter_registry()["p0_numeric_pass_thresholds"] == []
    assert set(lane_capability_table()["Automated_P0_Decision_v0_19"]) == {"NOT_ALLOWED"}

    # Mini integration fixture for the SQLite -> augmented/quarantine partition.
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "mini.sqlite"
        conn = sqlite3.connect(db)
        try:
            conn.execute("CREATE TABLE cache_state (ws_id TEXT PRIMARY KEY, yahoo_symbol TEXT, mapping_status TEXT, status TEXT, reason_code TEXT)")
            conn.execute("CREATE TABLE price_daily (ws_id TEXT, yahoo_symbol TEXT, day TEXT, open REAL, high REAL, low REAL, close REAL, adj_close REAL, volume REAL, dividends REAL, stock_splits REAL, repaired INTEGER)")
            conn.execute("INSERT INTO cache_state VALUES (?,?,?,?,?)", ("WS:TEST:1", "TEST", "EXPLICIT", "READY", ""))
            conn.execute("INSERT INTO cache_state VALUES (?,?,?,?,?)", ("WS:TEST:2", "MISS", "EXPLICIT", "DOWNLOAD_FAILED", "NO_DATA"))
            rows=[]
            for i,d in enumerate(days):
                cc=float(close.iloc[i])
                rows.append(("WS:TEST:1","TEST",d.strftime("%Y-%m-%d"),cc*0.999,cc*1.01,cc*0.99,cc,cc,1_000_000+i,0.0,0.0,0))
            conn.executemany("INSERT INTO price_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            conn.commit()
        finally:
            conn.close()
        uni=pd.DataFrame([
            {"WS_ID":"WS:TEST:1","Name":"Ready Test","Country":"X","Primary_Ticker":"TEST","Primary_MIC":"XNYS","Primary_Currency":"USD","Primary_Universe_Index":"TEST"},
            {"WS_ID":"WS:TEST:2","Name":"Missing Test","Country":"X","Primary_Ticker":"MISS","Primary_MIC":"XNYS","Primary_Currency":"USD","Primary_Universe_Index":"TEST"},
        ])
        a,q=build_feature_rows(db,uni,days[-1].date())
        assert len(a)==1 and len(q)==1
        assert a.iloc[0]["WS_ID"]=="WS:TEST:1"
        assert q.iloc[0]["WS_ID"]=="WS:TEST:2"
        assert str(q.iloc[0]["QuarantineReason_v0_19"]).startswith("CACHE_DOWNLOAD_FAILED")
    print("P0_FEATURE_AUGMENTATION_V0_19_SELF_TEST_PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/p0_feature_augmentation_v0.19.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
