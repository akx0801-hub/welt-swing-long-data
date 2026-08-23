#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

from price_cache import derive_yahoo_symbol, split_download_frame, normalize_symbol_frame
from feature_builder import split_adjust_technical


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
    arr = np.ones((3,len(cols)))
    raw = pd.DataFrame(arr,index=idx,columns=cols)
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
    assert out[["open","high","low","close"]].notna().all(axis=1).all()
    ok("cross-market union placeholder rows removed")

def main():
    test_mapping(); test_split_adjustment(); test_multiindex_parser(); test_cross_market_union_placeholders()
    print("SELF_TEST_RESULT=PASS")


if __name__ == "__main__":
    main()
