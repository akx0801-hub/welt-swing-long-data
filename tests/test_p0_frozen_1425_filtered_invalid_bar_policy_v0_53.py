from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/p0_frozen_1425_filtered_invalid_bar_policy_v0_53.py"
spec = importlib.util.spec_from_file_location("v053", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

AS_OF = date(2026, 9, 26)


def test_canonical_contract_identity():
    x = mod.canonical_contract()
    assert x["max_invalid_bars"] == 2
    assert x["max_invalid_share"] == 0.01
    assert x["minimum_valid_observations_after_filter"] == 260


def test_no_special_pleading_in_implementation():
    assert mod.assert_no_special_pleading(SCRIPT)["Result"] == "PASS"


def test_boundary_and_negative_matrix():
    rows = mod.synthetic_policy_tests(AS_OF)
    assert rows
    assert all(r["Result"] == "PASS" for r in rows)


def test_feature_path_uses_filtered_valid_series():
    rows = mod.feature_path_regression(AS_OF)
    assert rows
    assert all(r["Result"] == "PASS" for r in rows)


def test_byte_lifecycle_hashes_only_after_close():
    x = mod.byte_lifecycle_regression()
    assert x["Result"] == "PASS"
    assert x["hash_after_close"] is True
    assert x["connection_closed_guard"] is True
    assert x["wal_sidecar_after_close"] is False
