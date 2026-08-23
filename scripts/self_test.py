#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

from price_cache import (
    derive_yahoo_symbol, split_download_frame, normalize_symbol_frame,
    qa_symbol_frame, FreeDataConfig, SQLitePriceCache, YFinanceBatchClient,
    YFinancePriceCacheRunner,
)
from feature_builder import split_adjust_technical, build_features


def ok(name):
    print(f"PASS: {name}")


def test_mapping():
    cases = [
        ("AAPL","XNAS","AAPL"),
        ("SAP","XETR","SAP.DE"),
        ("7203","XTKS","7203.T"),
        ("700","XHKG","0700.HK"),
        ("BHP","XASX","BHP.AX"),
        ("RELIANCE","XNSE","RELIANCE.NS"),
        # G3 mapping-regression cases from the r6 primary-universe master.
        ("LGEN.L","XLON","LGEN.L"),
        ("VZN.S","XSWX","VZN.SW"),
        ("ISS.CO","XCSE","ISS.CO"),
        ("HEIN.AS","XAMS","HEIN.AS"),
        ("INGP.WA","XWAR","INGP.WA"),
        ("TECK.B","XTSE","TECK-B.TO"),
    ]
    for t,mic,exp in cases:
        got,status = derive_yahoo_symbol(t,mic)
        assert got == exp, (t,mic,got,exp,status)
    ok("mapping rules")


def test_split_adjustment():
    df = pd.DataFrame({
        "day":["2026-01-01","2026-01-02","2026-01-03"],
        "open":[100,51,52],"high":[102,53,54],"low":[99,50,51],"close":[100,52,53],
        "volume":[1000,2000,2100],"stock_splits":[0,2,0],
    })
    out = split_adjust_technical(df)
    assert abs(out.loc[0,"close_tech"] - 50.0) < 1e-9
    assert abs(out.loc[1,"close_tech"] - 52.0) < 1e-9
    assert abs(out.loc[0,"volume_tech"] - 2000.0) < 1e-9
    ok("split-only technical normalization")


def test_multiindex_parser():
    idx = pd.date_range("2026-01-01", periods=3)
    cols = pd.MultiIndex.from_product([["AAA","BBB"],["Open","High","Low","Close","Volume"]])
    raw = pd.DataFrame(np.ones((3,len(cols))),index=idx,columns=cols)
    out = split_download_frame(raw,["AAA","BBB"])
    assert set(out)=={"AAA","BBB"}
    assert "close" in normalize_symbol_frame(out["AAA"]).columns
    ok("yfinance MultiIndex parser")


def test_cross_market_union_placeholders():
    idx = pd.date_range("2026-01-01", periods=5)
    df = pd.DataFrame({
        "open":[10,np.nan,np.nan,11,12],
        "high":[11,np.nan,np.nan,12,13],
        "low":[9,np.nan,np.nan,10,11],
        "close":[10.5,np.nan,np.nan,11.5,12.5],
        "volume":[100,np.nan,np.nan,120,130],
    }, index=idx)
    out = normalize_symbol_frame(df)
    assert len(out) == 3, len(out)
    ok("cross-market union placeholder rows removed")


def _good_frame(n=270, start="2025-01-02"):
    idx = pd.bdate_range(start, periods=n)
    close = np.linspace(100.0, 130.0, n)
    return pd.DataFrame({
        "open": close - 0.2,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "adj_close": close,
        "volume": np.full(n, 1_000_000.0),
        "dividends": np.zeros(n),
        "stock_splits": np.zeros(n),
        "repaired": np.zeros(n),
    }, index=idx)


def test_open_outside_range_is_not_hard_fail():
    df = _good_frame()
    # Deliberately place one Open above High; H/L/C remain internally valid.
    df.iloc[40, df.columns.get_loc("open")] = df.iloc[40]["high"] + 0.5
    qa = qa_symbol_frame(df, config=FreeDataConfig(), as_of=df.index[-1].date())
    assert qa["status"] == "READY", qa
    ok("open outside H/L is not a whole-security quarantine")


def test_one_isolated_invalid_bar_is_excluded_not_security_quarantined():
    df = _good_frame()
    df.iloc[40, df.columns.get_loc("low")] = df.iloc[40]["high"] + 5.0
    qa = qa_symbol_frame(df, config=FreeDataConfig(), as_of=df.index[-1].date())
    assert qa["status"] == "READY", qa
    assert qa["reason_code"] == "ISOLATED_INVALID_BAR_EXCLUDED", qa
    assert qa["unique_bars"] == 270 and qa["valid_bars"] == 269, qa
    ok("one isolated invalid bar is excluded while deep series stays READY")


def test_two_invalid_bars_still_quarantine():
    df = _good_frame()
    for i in (40, 80):
        df.iloc[i, df.columns.get_loc("low")] = df.iloc[i]["high"] + 5.0
    qa = qa_symbol_frame(df, config=FreeDataConfig(), as_of=df.index[-1].date())
    assert qa["status"] == "QUARANTINE", qa
    ok("two invalid bars still quarantine")


def test_incremental_qa_uses_full_persisted_history():
    full = _good_frame()
    overlap = full.tail(11).copy()
    calls = {"n":0}

    def fake_download(**kwargs):
        calls["n"] += 1
        symbols = kwargs.get("tickers") or []
        sym = list(symbols)[0]
        src = full if "period" in kwargs else overlap
        cols = pd.MultiIndex.from_product([[sym],["Open","High","Low","Close","Adj Close","Volume","Dividends","Stock Splits"]])
        arr = np.column_stack([
            src["open"],src["high"],src["low"],src["close"],src["adj_close"],src["volume"],src["dividends"],src["stock_splits"]
        ])
        return pd.DataFrame(arr,index=src.index,columns=cols)

    universe = pd.DataFrame([{
        "WS_ID":"TEST:AAA","Primary_Ticker":"AAA","Primary_MIC":"XNAS","Yahoo_Symbol":"AAA"
    }])
    with tempfile.TemporaryDirectory() as td:
        cache = SQLitePriceCache(Path(td)/"px.sqlite")
        try:
            cfg = FreeDataConfig(batch_size=10, pause_between_batches_seconds=0)
            runner = YFinancePriceCacheRunner(cache,YFinanceBatchClient(config=cfg,download_func=fake_download),config=cfg)
            runner.run_initial(universe,as_of=full.index[-1].date())
            st1 = pd.read_sql_query("SELECT status,unique_bars FROM cache_state WHERE ws_id='TEST:AAA'",cache.conn).iloc[0]
            assert st1.status == "READY" and int(st1.unique_bars) >= 260, st1.to_dict()
            runner.run_incremental(universe,end=full.index[-1].date(),as_of=full.index[-1].date())
            st2 = pd.read_sql_query("SELECT status,unique_bars FROM cache_state WHERE ws_id='TEST:AAA'",cache.conn).iloc[0]
            assert st2.status == "READY", st2.to_dict()
            assert int(st2.unique_bars) >= 260, st2.to_dict()
        finally:
            cache.close()
    ok("incremental QA uses full persisted cache, not overlap slice")



def test_missing_symbol_gets_bounded_rescue_batch():
    good = _good_frame()
    calls = []

    def fake_download(**kwargs):
        symbols = list(kwargs.get("tickers") or [])
        repair = bool(kwargs.get("repair", False))
        calls.append((tuple(symbols), repair, "period" in kwargs))
        # First bulk call omits BBB. Rescue call for BBB returns valid history.
        cols = []
        frames = []
        if symbols == ["AAA", "BBB"]:
            src_syms = ["AAA"]
        else:
            src_syms = symbols
        if not src_syms:
            return pd.DataFrame()
        arrays = []
        tuples = []
        for sym in src_syms:
            for col, series in [
                ("Open", good["open"]), ("High", good["high"]), ("Low", good["low"]),
                ("Close", good["close"]), ("Adj Close", good["adj_close"]),
                ("Volume", good["volume"]), ("Dividends", good["dividends"]),
                ("Stock Splits", good["stock_splits"]),
            ]:
                tuples.append((sym, col))
                arrays.append(series.to_numpy())
        data = np.column_stack(arrays)
        return pd.DataFrame(data, index=good.index, columns=pd.MultiIndex.from_tuples(tuples))

    universe = pd.DataFrame([
        {"WS_ID":"TEST:AAA","Primary_Ticker":"AAA","Primary_MIC":"XNAS","Yahoo_Symbol":"AAA"},
        {"WS_ID":"TEST:BBB","Primary_Ticker":"BBB","Primary_MIC":"XNAS","Yahoo_Symbol":"BBB"},
    ])
    with tempfile.TemporaryDirectory() as td:
        cache = SQLitePriceCache(Path(td)/"px.sqlite")
        try:
            cfg = FreeDataConfig(batch_size=10, pause_between_batches_seconds=0)
            runner = YFinancePriceCacheRunner(cache,YFinanceBatchClient(config=cfg,download_func=fake_download),config=cfg)
            result = runner.run_initial(universe, as_of=good.index[-1].date())
            states = pd.read_sql_query("SELECT ws_id,status FROM cache_state ORDER BY ws_id",cache.conn)
            assert states["status"].tolist() == ["READY","READY"], states.to_dict("records")
            assert int(result["rescue_attempted"]) == 1, result
            assert int(result["missing_symbols"]) == 0, result
            # One bulk call plus one rescue batch; not per-security fallback.
            assert len(calls) == 2, calls
        finally:
            cache.close()
    ok("missing symbol gets one bounded rescue batch")


def test_invalid_ohlc_triggers_targeted_full_history_repair():
    good = _good_frame()
    bad = good.copy()
    # Two genuinely impossible H/L/C rows: beyond isolated-bar tolerance,
    # therefore targeted repair must still trigger.
    for i in (20, 40):
        bad.iloc[i, bad.columns.get_loc("low")] = bad.iloc[i]["high"] + 5.0
    calls = []

    def fake_download(**kwargs):
        symbols = list(kwargs.get("tickers") or [])
        repair = bool(kwargs.get("repair", False))
        calls.append((tuple(symbols), repair, "period" in kwargs))
        src = good if repair else bad
        sym = symbols[0]
        tuples=[]; arrays=[]
        for col, series in [
            ("Open", src["open"]), ("High", src["high"]), ("Low", src["low"]),
            ("Close", src["close"]), ("Adj Close", src["adj_close"]),
            ("Volume", src["volume"]), ("Dividends", src["dividends"]),
            ("Stock Splits", src["stock_splits"]),
        ]:
            tuples.append((sym,col)); arrays.append(series.to_numpy())
        return pd.DataFrame(
            np.column_stack(arrays), index=src.index,
            columns=pd.MultiIndex.from_tuples(tuples)
        )

    universe = pd.DataFrame([{
        "WS_ID":"TEST:CCC","Primary_Ticker":"CCC","Primary_MIC":"XNAS","Yahoo_Symbol":"CCC"
    }])
    with tempfile.TemporaryDirectory() as td:
        cache = SQLitePriceCache(Path(td)/"px.sqlite")
        try:
            cfg = FreeDataConfig(batch_size=10, pause_between_batches_seconds=0, repair_anomalies=True)
            runner = YFinancePriceCacheRunner(cache,YFinanceBatchClient(config=cfg,download_func=fake_download),config=cfg)
            result = runner.run_initial(universe, as_of=good.index[-1].date())
            state = pd.read_sql_query("SELECT status,reason_code FROM cache_state WHERE ws_id='TEST:CCC'",cache.conn).iloc[0]
            assert state.status == "READY", state.to_dict()
            assert int(result["repair_candidates"]) == 1, result
            assert int(result["repair_attempted"]) == 1, result
            assert any(repair for _,repair,_ in calls), calls
        finally:
            cache.close()
    ok("invalid OHLC triggers targeted full-history yfinance repair")


def test_feature_builder_excludes_isolated_invalid_bar():
    good = _good_frame()
    with tempfile.TemporaryDirectory() as td:
        db = Path(td)/"px.sqlite"
        universe_csv = Path(td)/"universe.csv"
        cache = SQLitePriceCache(db)
        try:
            rows=[]
            fetched="2026-08-23T00:00:00+00:00"
            for day, r in good.iterrows():
                low=float(r["low"])
                if day == good.index[40]:
                    low=float(r["high"])+5.0
                rows.append((
                    "TEST:AAA","AAA",day.date().isoformat(),
                    float(r["open"]),float(r["high"]),low,float(r["close"]),
                    float(r["adj_close"]),float(r["volume"]),0.0,0.0,0,
                    "YFINANCE_FREE",fetched
                ))
            cache.upsert_price_rows(rows)
            qa=qa_symbol_frame(cache.load_price_frame("TEST:AAA"),config=FreeDataConfig(),as_of=good.index[-1].date())
            cache.upsert_state({
                "ws_id":"TEST:AAA","yahoo_symbol":"AAA","mapping_status":"EXPLICIT",
                "last_fetch_utc":fetched,"batch_id":"T","last_error":None,
                **{k:v for k,v in qa.items() if k!="warning_zero_volume"}
            })
            cache.conn.commit()
        finally:
            cache.close()
        pd.DataFrame([{
            "WS_ID":"TEST:AAA","Name":"AAA","Primary_Ticker":"AAA","Primary_MIC":"XNAS",
            "Primary_Currency":"USD"
        }]).to_csv(universe_csv,index=False)
        feat=build_features(db,universe_csv)
        assert len(feat)==1, feat
        row=feat.iloc[0]
        assert int(row["Bars_Raw"])==270, row.to_dict()
        assert int(row["Bars_Used"])==269, row.to_dict()
        assert int(row["Excluded_Invalid_Bars"])==1, row.to_dict()
    ok("feature builder excludes isolated invalid bar from technical series")

def main():
    test_mapping()
    test_split_adjustment()
    test_multiindex_parser()
    test_cross_market_union_placeholders()
    test_open_outside_range_is_not_hard_fail()
    test_one_isolated_invalid_bar_is_excluded_not_security_quarantined()
    test_two_invalid_bars_still_quarantine()
    test_incremental_qa_uses_full_persisted_history()
    test_missing_symbol_gets_bounded_rescue_batch()
    test_invalid_ohlc_triggers_targeted_full_history_repair()
    test_feature_builder_excludes_isolated_invalid_bar()
    print("SELF_TEST_RESULT=PASS")


if __name__ == "__main__":
    main()
