#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCHEMA = "WELT_SWING_NON_READY_DIAGNOSTIC_V0_1"
EXPECTED_UNIVERSE = 3663
EXPECTED_READY = 3578
EXPECTED_NON_READY = 85
EXPECTED_STATUS_COUNTS = {
    "QUARANTINE": 55,
    "WARMUP": 20,
    "DOWNLOAD_FAILED": 9,
    "STALE": 1,
}

PRODUCTIVE_TRADING_AUTHORITY = False
P0_RUN = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_HISTORY_CALLS_ALLOWED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def fnum(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        if math.isfinite(x):
            return x
    except Exception:
        pass
    return default


def inum(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def parse_day(v: Any) -> date | None:
    s = txt(v)
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def age_days(last_day: Any, as_of: date) -> int | None:
    d = parse_day(last_day)
    return None if d is None else (as_of - d).days


def valid_mask(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=bool)
    def n(col):
        return pd.to_numeric(df[col], errors="coerce")
    o, h, l, c, v = n("open"), n("high"), n("low"), n("close"), n("volume")
    finite = pd.concat([o, h, l, c], axis=1).replace(
        [np.inf, -np.inf], np.nan
    ).notna().all(axis=1)
    positive = (pd.concat([o, h, l, c], axis=1) > 0).all(axis=1)
    relation = (h >= l) & (c <= h) & (c >= l)
    nonnegative_volume = ~((v < 0) & v.notna())
    return finite & positive & relation & nonnegative_volume


def suspicious_events(
    df: pd.DataFrame, threshold: float, split_window_days: int
) -> list[dict[str, Any]]:
    if df.empty:
        return []
    x = df.sort_values("day").copy()
    c = pd.to_numeric(x["close"], errors="coerce")
    ret = c.pct_change()
    split = (
        pd.to_numeric(x["stock_splits"], errors="coerce").fillna(0.0)
        if "stock_splits" in x.columns
        else pd.Series(0.0, index=x.index)
    )
    days = pd.to_datetime(x["day"], errors="coerce")

    out = []
    for idx in x.index[ret.abs() > threshold]:
        pos = x.index.get_loc(idx)
        d = days.loc[idx]
        lo = max(0, pos - split_window_days)
        hi = min(len(x), pos + split_window_days + 1)
        nearby = x.iloc[lo:hi].copy()
        nearby_split = (
            pd.to_numeric(
                nearby.get("stock_splits", pd.Series(0.0, index=nearby.index)),
                errors="coerce",
            )
            .fillna(0.0)
            .gt(0)
            .any()
        )
        out.append({
            "day": "" if pd.isna(d) else d.date().isoformat(),
            "return": float(ret.loc[idx]),
            "close": fnum(x.loc[idx, "close"], float("nan")),
            "previous_close": (
                fnum(x.iloc[pos - 1]["close"], float("nan")) if pos > 0 else None
            ),
            "split_on_day": fnum(split.loc[idx]),
            "split_nearby": bool(nearby_split),
        })
    return out


def search_quotes(query: str, max_results: int) -> tuple[list[dict[str, Any]], str]:
    # Search only. No yf.download(), Ticker.history(), fast_info or quote history.
    try:
        import yfinance as yf
        s = yf.Search(
            query=query,
            max_results=max_results,
            news_count=0,
            lists_count=0,
            include_cb=False,
            include_nav_links=False,
            include_research=False,
            include_cultural_assets=False,
            enable_fuzzy_query=False,
            recommended=0,
            timeout=20,
            raise_errors=False,
        )
        return list(s.quotes or []), ""
    except Exception as exc:  # noqa: BLE001
        return [], f"{type(exc).__name__}: {exc}"


def exact_search_diagnostic(
    row: pd.Series, max_results: int, pause_seconds: float
) -> dict[str, Any]:
    symbol = txt(row.get("yahoo_symbol"))
    name = txt(row.get("Name"))
    quotes = []
    errors = []
    for q in [symbol, name, f"{name} {symbol}"]:
        q = q.strip()
        if not q:
            continue
        got, err = search_quotes(q, max_results)
        quotes.extend(got)
        if err:
            errors.append(err)
        if pause_seconds:
            time.sleep(pause_seconds)

    symbol_u = symbol.upper()
    exact = [
        q for q in quotes
        if txt(q.get("symbol")).upper() == symbol_u
        and txt(q.get("quoteType")).upper() in {"", "EQUITY"}
    ]
    first = exact[0] if exact else {}
    candidates = []
    seen = set()
    for q in quotes:
        sym = txt(q.get("symbol"))
        if not sym or sym in seen:
            continue
        seen.add(sym)
        candidates.append({
            "symbol": sym,
            "name": txt(q.get("longname") or q.get("shortname")),
            "exchange": txt(q.get("exchange")),
            "quoteType": txt(q.get("quoteType")),
        })
        if len(candidates) >= 8:
            break

    return {
        "exact_equity_search_hit": bool(exact),
        "exact_result_name": txt(first.get("longname") or first.get("shortname")),
        "exact_exchange": txt(first.get("exchange")),
        "search_errors": "; ".join(errors),
        "top_candidates_json": json.dumps(candidates, ensure_ascii=False),
    }


def load_price_rows(conn: sqlite3.Connection, ws_id: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(
            "SELECT * FROM price_daily WHERE ws_id = ? ORDER BY day",
            conn,
            params=[ws_id],
        )
    except Exception:
        return pd.DataFrame()


def classify(
    row: pd.Series,
    px: pd.DataFrame,
    *,
    as_of: date,
    cfg: dict[str, Any],
) -> tuple[str, str, list[dict[str, Any]], list[dict[str, Any]]]:
    status = txt(row.get("status")).upper()
    reason = txt(row.get("reason_code")).upper()
    last_age = age_days(row.get("last_bar_date"), as_of)
    valid_bars = inum(row.get("valid_bars"))
    unique_bars = inum(row.get("unique_bars"))

    invalid_rows = []
    if not px.empty and {"open", "high", "low", "close", "volume"}.issubset(px.columns):
        vm = valid_mask(px)
        bad = px.loc[~vm].copy()
        for _, b in bad.iterrows():
            invalid_rows.append({
                "day": txt(b.get("day")),
                "open": b.get("open"),
                "high": b.get("high"),
                "low": b.get("low"),
                "close": b.get("close"),
                "volume": b.get("volume"),
            })

    susp = suspicious_events(
        px,
        threshold=float(cfg["suspicious_abs_return"]),
        split_window_days=int(cfg["split_window_rows"]),
    )

    if status == "WARMUP":
        if reason == "INSUFFICIENT_HISTORY" and valid_bars == unique_bars:
            return (
                "ACCEPT_WARMUP_SHORT_HISTORY",
                "KEEP_WARMUP_NO_REPAIR",
                invalid_rows,
                susp,
            )
        return (
            "WARMUP_REVIEW_REQUIRED",
            "REVIEW_HISTORY_AND_BAR_VALIDITY",
            invalid_rows,
            susp,
        )

    if status == "STALE":
        return (
            "STALE_PROVIDER_OR_SOURCE_REVIEW",
            "VERIFY_CURRENT_LISTING_OR_PROVIDER_SYMBOL",
            invalid_rows,
            susp,
        )

    if status == "DOWNLOAD_FAILED":
        return (
            "NO_DATA_PROVIDER_OR_SOURCE_REVIEW",
            "TARGETED_SYMBOL_AND_LISTING_EVIDENCE",
            invalid_rows,
            susp,
        )

    if status == "QUARANTINE" and reason == "INVALID_OHLC_OR_VOLUME":
        raw = len(px)
        bad = len(invalid_rows)
        frac = bad / raw if raw else 1.0
        fresh = last_age is not None and last_age <= int(cfg["stale_calendar_days"])
        if (
            raw >= int(cfg["ready_unique_bars"])
            and valid_bars >= int(cfg["ready_unique_bars"])
            and bad <= int(cfg["isolated_invalid_bar_max_count"])
            and frac <= float(cfg["isolated_invalid_bar_max_share"])
            and fresh
        ):
            return (
                "LIKELY_ISOLATED_INVALID_BARS_FILTERABLE",
                "QA_POLICY_REVIEW_FOR_FILTERED_READY",
                invalid_rows,
                susp,
            )
        return (
            "INVALID_BAR_QUARANTINE_REVIEW",
            "KEEP_QUARANTINE_PENDING_BAR_ANALYSIS",
            invalid_rows,
            susp,
        )

    if status == "QUARANTINE" and reason == "SUSPICIOUS_RETURN_NEEDS_REPAIR":
        if susp and all(bool(e["split_nearby"]) for e in susp):
            return (
                "LIKELY_SPLIT_OR_CORPORATE_ACTION",
                "VERIFY_CORPORATE_ACTION_THEN_QA_POLICY_REVIEW",
                invalid_rows,
                susp,
            )
        return (
            "SUSPICIOUS_RETURN_RESEARCH_REQUIRED",
            "TARGETED_EVENT_RESEARCH_KEEP_QUARANTINE",
            invalid_rows,
            susp,
        )

    return (
        "NON_READY_REVIEW_REQUIRED",
        "KEEP_NON_READY_PENDING_DIAGNOSIS",
        invalid_rows,
        susp,
    )


def run(args) -> dict[str, Any]:
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    errors = pd.read_csv(args.errors, keep_default_na=False, dtype=str)
    coverage = json.loads(Path(args.coverage).read_text(encoding="utf-8"))

    if coverage["universe_count"] != EXPECTED_UNIVERSE:
        raise SystemExit(f"Expected universe {EXPECTED_UNIVERSE}, got {coverage['universe_count']}")
    if coverage["ready_count"] != EXPECTED_READY:
        raise SystemExit(f"Expected READY {EXPECTED_READY}, got {coverage['ready_count']}")
    if len(errors) != EXPECTED_NON_READY:
        raise SystemExit(f"Expected {EXPECTED_NON_READY} non-ready rows, got {len(errors)}")

    counts = errors["status"].value_counts().to_dict()
    for k, v in EXPECTED_STATUS_COUNTS.items():
        if int(counts.get(k, 0)) != v:
            raise SystemExit(f"Expected {k}={v}, got {counts.get(k, 0)}")

    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"Restored SQLite cache missing: {db}")

    conn = sqlite3.connect(db)
    try:
        row_count = conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]
        if row_count < int(cfg["minimum_expected_cached_price_rows"]):
            raise SystemExit(
                f"SQLite cache appears incomplete: price_daily rows={row_count}"
            )

        out_rows = []
        invalid_events = []
        suspicious_rows = []
        search_rows = []

        as_of = date.fromisoformat(str(cfg["as_of_date"]))

        for _, r in errors.iterrows():
            ws = txt(r.get("WS_ID"))
            px = load_price_rows(conn, ws)
            classification, action, bad_rows, susp = classify(
                r, px, as_of=as_of, cfg=cfg
            )

            for ev in bad_rows:
                invalid_events.append({
                    "WS_ID": ws,
                    "Name": txt(r.get("Name")),
                    "Primary_Universe_Index": txt(r.get("Primary_Universe_Index")),
                    **ev,
                })
            for ev in susp:
                suspicious_rows.append({
                    "WS_ID": ws,
                    "Name": txt(r.get("Name")),
                    "Primary_Universe_Index": txt(r.get("Primary_Universe_Index")),
                    **ev,
                })

            search_diag = {}
            if txt(r.get("status")).upper() in {"DOWNLOAD_FAILED", "STALE"}:
                search_diag = exact_search_diagnostic(
                    r,
                    max_results=int(cfg["search_max_results"]),
                    pause_seconds=float(cfg["search_pause_seconds"]),
                )
                search_rows.append({
                    "WS_ID": ws,
                    "Name": txt(r.get("Name")),
                    "Yahoo_Symbol": txt(r.get("yahoo_symbol")),
                    "Original_Status": txt(r.get("status")),
                    "Original_Reason": txt(r.get("reason_code")),
                    **search_diag,
                })

            out_rows.append({
                "WS_ID": ws,
                "Name": txt(r.get("Name")),
                "Country": txt(r.get("Country")),
                "Primary_Universe_Index": txt(r.get("Primary_Universe_Index")),
                "Primary_MIC": txt(r.get("Primary_MIC")),
                "Yahoo_Symbol": txt(r.get("yahoo_symbol")),
                "Original_Status": txt(r.get("status")),
                "Original_Reason": txt(r.get("reason_code")),
                "Unique_Bars": inum(r.get("unique_bars")),
                "Valid_Bars": inum(r.get("valid_bars")),
                "First_Bar_Date": txt(r.get("first_bar_date")),
                "Last_Bar_Date": txt(r.get("last_bar_date")),
                "Last_Bar_Age_Days": age_days(r.get("last_bar_date"), as_of),
                "Cached_Price_Rows": int(len(px)),
                "Invalid_Cached_Bars": int(len(bad_rows)),
                "Suspicious_Return_Events_Recomputed": int(len(susp)),
                "Diagnostic_Classification": classification,
                "Recommended_Action": action,
                "Exact_Equity_Search_Hit": search_diag.get("exact_equity_search_hit", ""),
                "Search_Result_Name": search_diag.get("exact_result_name", ""),
                "Search_Result_Exchange": search_diag.get("exact_exchange", ""),
                "Search_Errors": search_diag.get("search_errors", ""),
            })

    finally:
        conn.close()

    out = pd.DataFrame(out_rows)
    invalid_df = pd.DataFrame(invalid_events)
    susp_df = pd.DataFrame(suspicious_rows)
    search_df = pd.DataFrame(search_rows)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out.to_csv(out_dir / "non_ready_diagnostic_rows_v0.1.csv", index=False)
    invalid_df.to_csv(out_dir / "invalid_bar_events_v0.1.csv", index=False)
    susp_df.to_csv(out_dir / "suspicious_return_events_v0.1.csv", index=False)
    search_df.to_csv(out_dir / "failed_stale_search_diagnostic_v0.1.csv", index=False)

    cluster = (
        out.groupby(
            ["Original_Status", "Original_Reason", "Primary_Universe_Index",
             "Diagnostic_Classification", "Recommended_Action"],
            dropna=False,
        )
        .size()
        .reset_index(name="Rows")
        .sort_values(
            ["Original_Status", "Original_Reason", "Rows"],
            ascending=[True, True, False],
        )
    )
    cluster.to_csv(out_dir / "non_ready_clusters_v0.1.csv", index=False)

    class_counts = {
        str(k): int(v)
        for k, v in out["Diagnostic_Classification"].value_counts().to_dict().items()
    }
    action_counts = {
        str(k): int(v)
        for k, v in out["Recommended_Action"].value_counts().to_dict().items()
    }
    segment_status = (
        out.groupby(["Primary_Universe_Index", "Original_Status"])
        .size()
        .reset_index(name="Rows")
    )
    segment_status.to_csv(out_dir / "segment_status_counts_v0.1.csv", index=False)

    download_search_exact = 0
    if not search_df.empty and "exact_equity_search_hit" in search_df.columns:
        download_search_exact = int(
            search_df["exact_equity_search_hit"]
            .astype(str).str.lower().eq("true").sum()
        )

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "NON_READY_DIAGNOSTIC_COMPLETE",
        "source_universe_count": EXPECTED_UNIVERSE,
        "source_ready_count": EXPECTED_READY,
        "source_non_ready_count": EXPECTED_NON_READY,
        "source_status_counts": EXPECTED_STATUS_COUNTS,
        "diagnostic_rows": int(len(out)),
        "classification_counts": class_counts,
        "recommended_action_counts": action_counts,
        "invalid_bar_event_rows": int(len(invalid_df)),
        "suspicious_return_event_rows": int(len(susp_df)),
        "failed_or_stale_search_rows": int(len(search_df)),
        "failed_or_stale_exact_equity_search_hits": download_search_exact,
        "sqlite_price_rows_observed": int(row_count),
        "price_history_calls_performed": False,
        "provider_search_only_for_download_failed_and_stale": True,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "automatic_status_promotions": 0,
        "notes": [
            "This pass diagnoses the 85 non-READY rows only.",
            "No yfinance price/history/download call is made.",
            "No cache status is changed and no security is promoted to READY automatically.",
            "WARMUP can be accepted as short-history coverage without pretending it has 260 bars.",
            "Isolated invalid-bar cases are only flagged as candidates for a later QA-policy review.",
            "Suspicious returns remain quarantined until corporate-action/event evidence is checked.",
            "DOWNLOAD_FAILED and STALE rows receive Yahoo Search diagnostics only; listing/source evidence remains a separate step.",
            "P0 remains off."
        ],
    }
    (out_dir / "summary_v0.1.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def self_test() -> None:
    cfg = {
        "suspicious_abs_return": 0.5,
        "split_window_rows": 1,
        "stale_calendar_days": 10,
        "ready_unique_bars": 260,
        "isolated_invalid_bar_max_count": 2,
        "isolated_invalid_bar_max_share": 0.01,
    }
    days = pd.date_range("2025-01-01", periods=300, freq="B")
    px = pd.DataFrame({
        "day": days.strftime("%Y-%m-%d"),
        "open": 100.0,
        "high": 102.0,
        "low": 98.0,
        "close": 100.0,
        "volume": 1000.0,
        "stock_splits": 0.0,
    })
    px.loc[10, "high"] = 90.0
    px.loc[11, "high"] = 90.0
    r = pd.Series({
        "status": "QUARANTINE",
        "reason_code": "INVALID_OHLC_OR_VOLUME",
        "valid_bars": "298",
        "unique_bars": "300",
        "last_bar_date": "2026-02-24",
    })
    cls, action, bad, susp = classify(
        r, px, as_of=date(2026, 2, 24), cfg=cfg
    )
    assert cls == "LIKELY_ISOLATED_INVALID_BARS_FILTERABLE"
    assert len(bad) == 2

    w = pd.Series({
        "status": "WARMUP",
        "reason_code": "INSUFFICIENT_HISTORY",
        "valid_bars": "120",
        "unique_bars": "120",
        "last_bar_date": "2026-02-24",
    })
    cls2, _, _, _ = classify(w, px.head(120), as_of=date(2026, 2, 24), cfg=cfg)
    assert cls2 == "ACCEPT_WARMUP_SHORT_HISTORY"

    print("NON_READY_DIAGNOSTIC_V0_1_SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/non_ready_diagnostic_v0.1.json")
    ap.add_argument("--errors", default="output_full_3663/errors.csv")
    ap.add_argument("--coverage", default="output_full_3663/coverage.json")
    ap.add_argument("--db", default="runtime_cache/full_3663_prices.sqlite")
    ap.add_argument("--out-dir", default="output_non_ready_diagnostic")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
