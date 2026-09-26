from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/p0_frozen_1425_local_feature_implementation_v0_57.py"
spec=importlib.util.spec_from_file_location("v057",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

from feature_builder import _lag_ratio_return,_rvol20_prior_baseline,_safe_divide


def test_exact_feature_sets():
    assert len(mod.OLD23)==23
    assert len(mod.NEW11)==11
    assert len(mod.ALL34)==34
    assert mod.NEW11==[
        "EMA20_Slope_5","EMA50_Slope_10","Range5_Pct","Range10_Pct",
        "RangeCompression_5_20","RangeCompression_10_20","RVOL20",
        "Gap_Over_ATR14","DailyMove_Over_ATR14","Dist_High20","Dist_High60"
    ]


def test_slope_minimum_history_semantics():
    ema20=pd.Series([np.nan]*19+[100.0,101.0,102.0,103.0,104.0])
    assert len(ema20)==24
    assert _lag_ratio_return(ema20,5) is None
    ema20=pd.concat([ema20,pd.Series([105.0])],ignore_index=True)
    assert _lag_ratio_return(ema20,5)==(105.0/100.0-1.0)

    ema50=pd.Series([np.nan]*49+[100.0]*10)
    assert len(ema50)==59
    assert _lag_ratio_return(ema50,10) is None
    ema50=pd.concat([ema50,pd.Series([110.0])],ignore_index=True)
    assert _lag_ratio_return(ema50,10)==(110.0/100.0-1.0)


def test_safe_divide_fail_closed():
    assert _safe_divide(1.0,0.0) is None
    assert _safe_divide(1.0,np.nan) is None
    assert _safe_divide(np.inf,2.0) is None
    assert _safe_divide(2.0,4.0)==0.5


def test_rvol_excludes_current_and_requires_complete_prior20():
    prior=pd.Series([10.0]*20+[100.0])
    assert _rvol20_prior_baseline(prior)==10.0
    with_missing=prior.copy()
    with_missing.iloc[3]=np.nan
    assert _rvol20_prior_baseline(with_missing) is None
    zero=pd.Series([0.0]*20+[5.0])
    assert _rvol20_prior_baseline(zero) is None
    assert _rvol20_prior_baseline(pd.Series([1.0]*20)) is None


def test_recent_impulse_is_binding_not_numeric_column():
    assert mod.IMPULSE_CONSTITUENTS==["R5","R20","R60","DailyMove_Over_ATR14","RVOL20"]
    assert "RECENT_IMPULSE_DESCRIPTORS" not in mod.ALL34


def test_authoritative_constants():
    assert mod.REQUIRED_START_HEAD=="0287a10bf7a2938ed1517d79a47c296f3ea34c9d"
    assert mod.V056_RUN==36235568433
    assert mod.V056_ARTIFACT==10904166471
    assert mod.V056_ARTIFACT_DIGEST=="sha256:17acd42edc06fe7311d88e27ee0a1a2052145e92440e487c2e0f0a47a10709ed"
    assert mod.V053_RUNTIME_SHA256=="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
