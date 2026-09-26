from __future__ import annotations

import importlib.util
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/p0_frozen_1425_feature_materialization_v0_54.py"
spec = importlib.util.spec_from_file_location("v054", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_formula_binding_exact_current_canonical_inventory():
    assert len(mod.CANONICAL_FEATURES) == 21
    assert [r["feature_name"] for r in mod.FORMULA_ROWS] == mod.CANONICAL_FEATURES


def test_master_local_gaps_are_explicit_and_rs_not_local_blocker():
    rows = mod.feature_inventory()
    state = mod.validate_inventory(rows)
    assert state["master_local_blocking_gaps"] == mod.MASTER_LOCAL_BLOCKING_GAPS
    assert "HomeMarket_RS20_RS60" not in state["master_local_blocking_gaps"]
    assert "Sector_RS20_RS60" not in state["master_local_blocking_gaps"]


def test_semantic_digest_is_row_order_stable_after_projection_sort():
    row = {
        "Projection_Order": 1, "Security_Key": "K1", "Source_WS_ID": "W1",
        "Primary_MIC": "X1", "Primary_Ticker": "T1", "feature_as_of_date": "2026-09-22",
        "valid_bar_count": 300, "excluded_bar_count": 0, "source_data_defect": False,
        "excluded_dates": "", "filtered_policy_version": "v0.53",
    }
    for i, f in enumerate(mod.CANONICAL_FEATURES):
        row[f] = float(i + 1)
    row2 = dict(row)
    row2["Projection_Order"] = 2
    row2["Security_Key"] = "K2"
    row2["Source_WS_ID"] = "W2"
    a = pd.DataFrame([row2, row])
    b = pd.DataFrame([row, row2])
    assert mod.semantic_digest(a) == mod.semantic_digest(b)


def test_capability_is_partial_when_master_model_gaps_remain():
    row = {
        "Projection_Order": 1, "Security_Key": "K1", "Source_WS_ID": "W1",
        "Primary_MIC": "X1", "Primary_Ticker": "T1", "feature_as_of_date": "2026-09-22",
        "valid_bar_count": 300, "excluded_bar_count": 0, "source_data_defect": False,
    }
    for f in mod.CANONICAL_FEATURES:
        row[f] = 1.0
    sec = [{"Source_WS_ID": "W1", "Required_Canonical_NonFinite_Count": 0}]
    state = {"master_local_blocking_gaps": mod.MASTER_LOCAL_BLOCKING_GAPS}
    got = mod.capability_rows(pd.DataFrame([row]), sec, state)
    assert got[0]["feature_capability_status"] == "FEATURE_PARTIAL"
