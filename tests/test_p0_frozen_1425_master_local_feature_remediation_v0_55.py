from __future__ import annotations

import importlib.util
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/p0_frozen_1425_master_local_feature_remediation_v0_55.py"
spec=importlib.util.spec_from_file_location("v055",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

def test_gap_reconciliation_exact():
    assert len(mod.GAPS)==11
    assert len(mod.CONTRACT_ROWS)==11
    assert [r["feature_family"] for r in mod.CONTRACT_ROWS]==mod.GAPS
    assert mod.contract_counts()=={
        "CONTRACT_EXACT":0,
        "CONTRACT_DERIVABLE":3,
        "CONTRACT_AMBIGUOUS":8,
        "CONTRACT_CONFLICT":0,
        "CONTRACT_NOT_FOUND":0,
    }

def test_ambiguous_contracts_are_not_implemented():
    for r in mod.CONTRACT_ROWS:
        if r["contract_classification"]=="CONTRACT_AMBIGUOUS":
            assert r["promotion_status"]=="BLOCKED_NOT_IMPLEMENTED"

def test_promoted_contracts_are_only_derivable():
    promoted=[r for r in mod.CONTRACT_ROWS if r["feature_family"] not in mod.REMAINING]
    assert [r["feature_family"] for r in promoted]==["R1","TRUE_RANGE_CURRENT","RUNUP_5_20_60_SEMANTICS"]
    assert all(r["contract_classification"]=="CONTRACT_DERIVABLE" for r in promoted)

def test_r1_min_history_and_division_zero():
    assert mod._last_return(pd.Series([100.0]),1) is None
    assert mod._last_return(pd.Series([0.0,1.0]),1) is None
    assert mod._last_return(pd.Series([100.0,101.0]),1)==0.010000000000000009

def test_canonical_feature_count_after_two_new_columns():
    assert len(mod.OLD21)==21
    assert len(mod.NEW_FEATURES)==2
    assert len(mod.CANONICAL_FEATURES)==23
    assert "R1" in mod.CANONICAL_FEATURES
    assert "TrueRange_Current" in mod.CANONICAL_FEATURES

def test_runup_binding_has_no_duplicate_columns():
    assert "RUNUP_5_20_60_SEMANTICS" not in mod.CANONICAL_FEATURES
    row=next(r for r in mod.CONTRACT_ROWS if r["feature_family"]=="RUNUP_5_20_60_SEMANTICS")
    assert row["promotion_status"]=="CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN"
