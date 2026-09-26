from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/p0_frozen_1425_local_feature_contract_definition_v0_56.py"
spec=importlib.util.spec_from_file_location("v056",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def by_family(name):
    return next(r for r in mod.CONTRACT_DECISIONS if r["family"]==name)


def test_all_eight_contracts_defined():
    assert len(mod.CONTRACT_DECISIONS)==8
    assert [r["family"] for r in mod.CONTRACT_DECISIONS]==mod.FAMILIES
    assert all(r["decision_state"]=="CONTRACT_DEFINED" for r in mod.CONTRACT_DECISIONS)


def test_exact_new_numeric_names():
    assert mod.NEW_NUMERIC==[
        "EMA20_Slope_5","EMA50_Slope_10","Range5_Pct","Range10_Pct",
        "RangeCompression_5_20","RangeCompression_10_20","RVOL20",
        "Gap_Over_ATR14","DailyMove_Over_ATR14","Dist_High20","Dist_High60"
    ]


def test_ema_slope_contracts():
    e20=by_family("EMA20_SLOPE")
    e50=by_family("EMA50_SLOPE")
    assert e20["formula"]=="EMA20[t] / EMA20[t-5 valid] - 1"
    assert e20["minimum_history"]=="25 valid technical observations"
    assert e50["formula"]=="EMA50[t] / EMA50[t-10 valid] - 1"
    assert e50["minimum_history"]=="60 valid technical observations"


def test_range_compression_contract_is_nested_not_gt_one_expansion():
    r=by_family("RANGE_COMPRESSION_FAMILY")
    assert "RangeCompression_5_20" in r["canonical_names"]
    assert "RangeCompression_10_20" in r["canonical_names"]
    assert "mathematically in [0,1]" in r["sign"]
    assert ">1 is an integrity defect" in r["design_decision"]


def test_rvol_baseline_excludes_current():
    r=by_family("RELATIVE_VOLUME_METRICS")
    assert r["canonical_names"]=="RVOL20"
    assert "EXCLUDED" in r["current_bar_policy"]
    assert "previous 20" in r["formula"]


def test_atr_normalized_current_events_use_prior_atr():
    gap=by_family("GAP_OVER_ATR")
    move=by_family("DAILY_MOVE_IN_ATR")
    assert "ATR14[t-1 valid]" in gap["formula"]
    assert "ATR14[t-1 valid]" in move["formula"]
    assert "signed" in gap["sign"]
    assert "signed" in move["sign"]


def test_recent_impulse_is_composition_not_score():
    r=by_family("RECENT_IMPULSE_DESCRIPTORS")
    assert r["canonical_names"]=="SEMANTIC_FAMILY:{R5,R20,R60,DailyMove_Over_ATR14,RVOL20}"
    assert "no ImpulseScore" in r["formula"]
    assert "threshold" in r["design_decision"]


def test_high_distance_completion():
    r=by_family("RELEVANT_HIGH_DISTANCE_FAMILY")
    assert r["canonical_names"]=="Dist_High20;Dist_High60;Dist_High252(existing)"
    assert "Close_Tech[t] / HighN[t] - 1" in r["formula"]
    assert "dynamic resistance selector" in r["design_decision"]
