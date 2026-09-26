from __future__ import annotations

import importlib.util
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/p0_frozen_1425_home_market_rs_materialization_v0_58.py"
spec=importlib.util.spec_from_file_location("v058",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_authority_constants():
    assert mod.REQUIRED_START_HEAD=="80d80eee5e8a2e6ddad5f7b7b1231b9a3da21895"
    assert mod.V057_RUN==36239952535
    assert mod.V057_ARTIFACT==10905448132
    assert mod.V057_ARTIFACT_DIGEST=="sha256:7f35e18264110c6a6a84205ab443a7b1c3cabcbaebdb3e6d6af79df6361e1c00"
    assert mod.V057_FEATURE_SHA256=="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"


def test_leave_one_out_median_exact():
    s=pd.Series([0.10,0.20,0.30],index=[0,1,2])
    out=mod.peer_median_leave_one_out(s)
    assert out.loc[0]==0.25
    assert out.loc[1]==0.20
    assert out.loc[2]==0.15


def test_singleton_has_no_reference():
    s=pd.Series([0.10],index=[4])
    out=mod.peer_median_leave_one_out(s)
    assert pd.isna(out.loc[4])


def test_same_date_cohort_separation():
    x=pd.DataFrame({
      "Projection_Order":[1,2,3,4],
      "Security_Key":["A","B","C","D"],
      "Source_WS_ID":["A","B","C","D"],
      "Primary_MIC":["XNYS"]*4,
      "Primary_Ticker":["A","B","C","D"],
      "Primary_Universe_Index":["US_SP500"]*4,
      "feature_as_of_date":["2026-09-24","2026-09-24","2026-09-23","2026-09-23"],
      "R20_num":[0.10,0.20,0.30,0.50],
      "R60_num":[0.15,0.25,0.35,0.55],
      "sync_cohort_size":[2,2,2,2],
      "peer_count":[1,1,1,1],
    })
    m=mod.materialize(x)
    a=m.set_index("Source_WS_ID")
    assert a.loc["A","HomeMarket_PeerMedian_R20_v0_58"]==0.20
    assert a.loc["B","HomeMarket_PeerMedian_R20_v0_58"]==0.10
    assert a.loc["C","HomeMarket_PeerMedian_R20_v0_58"]==0.50
    assert a.loc["D","HomeMarket_PeerMedian_R20_v0_58"]==0.30


def test_contract_binding_is_internal_peer_not_official_index():
    c=mod.contract_binding()
    assert c["status"]=="CONTRACT_BOUND"
    assert c["peer_semantics"]=="LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN"
    assert c["official_index_benchmark_claim"] is False
    assert "exact same feature_as_of_date" in c["asof_calendar_rule"]


def test_provider_calls_zero():
    assert mod.provider_calls()=={
      "market_data_provider_calls":0,
      "yahoo_yfinance":0,
      "eodhd":0,
      "alpha_vantage":0,
      "scalable":0,
    }
