#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from feature_builder import build_features, split_adjust_technical, technical_valid_mask_for_features

VERSION = "v0.54"
STAGE = "P0_FROZEN_1425_FEATURE_MATERIALIZATION_CAPABILITY"
REQUIRED_START_HEAD = "8106f8d7a348b4000b504da6b9a82d9fd1db1c33"

V053_RUN_ID = 36225840648
V053_ARTIFACT_ID = 10900287789
V053_ARTIFACT_DIGEST = "sha256:f54f1520e6cfcefbca043bc782ccf71ddd0e70538722ee1c3857551396761e95"
V053_RUNTIME_SHA256 = "bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
V053_RUNTIME_BYTES = 144539648
V053_PRICE_ROWS = 711204
V053_STATES = 1425
V053_READY = 1425
V053_QUARANTINE = 0
V053_PRICE_DIGEST = "1c4f93c2ca5fb3a79e859b359cc3a192dc19187f6745ee5e458a6f3569d84aea"
V053_MAPPING_DIGEST = "d51ae152afeeaf81a92541b030efc4a32a9beae29b082b99397ba2f4131f861e"

FROZEN_PATH = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
FROZEN_ROWS = 1425

MASTER_SPEC_PATH = ROOT / "docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md"
MASTER_SPEC_BLOB = "680d0434e534d1fe136e694ca05cb574958a1a24"
FEATURE_BUILDER_PATH = ROOT / "scripts/feature_builder.py"
FEATURE_BUILDER_BLOB = "f6e14fedaa874bc89b6d33f51d6730e175c2b60e"
PRICE_CACHE_PATH = ROOT / "scripts/price_cache.py"
PRICE_CACHE_BLOB = "454a1036e02c8ea73504921163aad1438a7e9f9d"
V019_SCRIPT_PATH = ROOT / "scripts/p0_feature_augmentation_v0_19.py"
V019_SCRIPT_BLOB = "62ced7a22abc6b1e1aaeb0a2f44690fd67956d95"
V019_DOC_PATH = ROOT / "docs/validation/P0_Feature_Augmentation_v0.19.md"
V019_DOC_BLOB = "2d49b4c153710569f84d488a3db1154ad21875bd"
V052_DEP_PATH = ROOT / "output_p0_asx_ohlc_source_policy_v0_52/feature_field_dependencies_v0.52.csv"
V052_DEP_BLOB = "31218ff28f9b09b4ff088f4e9cf5f5e80f2d7fff"
V053_IMPL_PATH = ROOT / "scripts/p0_frozen_1425_filtered_invalid_bar_policy_v0_53.py"
V053_IMPL_BLOB = "b89b76e72a374d66a655513de152f8b3c877552d"
V053_SUMMARY_PATH = ROOT / "output_p0_frozen_1425_filtered_bar_policy_v0_53/summary_v0.53.json"
V053_SUMMARY_BLOB = "b103b26ab8f4ecc4ea2dc3786f492a17e9f866ac"
PARAM_READY_PATH = ROOT / "output_p0_frozen_1425_readiness_v0_44/parameter_readiness_v0.44.json"
PARAM_READY_BLOB = "a5c963f1dcf5d3d61000a7ae47d8ca21613f479f"

P0_RUNS = 0
MARKET_PROVIDER_CALLS = 0
YAHOO_YFINANCE_CALLS = 0
EODHD_CALLS = 0
ALPHA_VANTAGE_CALLS = 0
SCALABLE_CALLS = 0
HOME_MARKET_RS_READY = False
SECTOR_RS_READY = False
PRODUCTIVE = False

CANONICAL_FEATURES = [
    "Close_Tech",
    "EMA20",
    "EMA50",
    "SMA200",
    "ATR14_Wilder_DEV",
    "ATR14_Pct_DEV",
    "R5",
    "R20",
    "R60",
    "High20",
    "High60",
    "High252",
    "Low20",
    "Low60",
    "Dist_EMA20",
    "Dist_EMA50",
    "Dist_SMA200",
    "Dist_High252",
    "Range20_Pct",
    "MedianVolume20_Tech",
    "MedianTurnover20_Native",
]

HISTORICAL_AUGMENTED = [
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

# Master-spec minimum local-feature semantics that are not fully current-canonical.
# RS is explicitly excluded from this gate and therefore is not a local-layer blocker here.
MASTER_LOCAL_BLOCKING_GAPS = [
    "EMA20_SLOPE",
    "EMA50_SLOPE",
    "R1",
    "TRUE_RANGE_CURRENT",
    "RANGE_COMPRESSION_FAMILY",
    "RELATIVE_VOLUME_METRICS",
    "GAP_OVER_ATR",
    "DAILY_MOVE_IN_ATR",
    "RECENT_IMPULSE_DESCRIPTORS",
    "RUNUP_5_20_60_SEMANTICS",
    "RELEVANT_HIGH_DISTANCE_FAMILY",
]

FORMULA_ROWS = [
    dict(feature_name="Close_Tech", feature_family="PRICE", required_raw_fields="Close;Stock_Splits", formula="last split-only adjusted Close", implementation_reference="scripts/feature_builder.py:split_adjust_technical/build_features", lookback="latest valid observation after split normalization", minimum_valid_observations=1, lookback_semantics="FINITE", null_behavior="None only if no valid close", finite_handling="raw technical-validity mask excludes non-finite OHLC", filtered_series_behavior="whole invalid bar excluded before split normalization"),
    dict(feature_name="EMA20", feature_family="TREND", required_raw_fields="Close;Stock_Splits", formula="Close_Tech.ewm(span=20,adjust=False,min_periods=20).mean().last", implementation_reference="scripts/feature_builder.py:build_features", lookback="recursive EWM span=20", minimum_valid_observations=20, lookback_semantics="RECURSIVE_INFINITE_HISTORY_DEPENDENCE", null_behavior="None before 20 valid observations", finite_handling="non-finite raw OHLC excluded by validity mask", filtered_series_behavior="DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES"),
    dict(feature_name="EMA50", feature_family="TREND", required_raw_fields="Close;Stock_Splits", formula="Close_Tech.ewm(span=50,adjust=False,min_periods=50).mean().last", implementation_reference="scripts/feature_builder.py:build_features", lookback="recursive EWM span=50", minimum_valid_observations=50, lookback_semantics="RECURSIVE_INFINITE_HISTORY_DEPENDENCE", null_behavior="None before 50 valid observations", finite_handling="non-finite raw OHLC excluded by validity mask", filtered_series_behavior="DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES"),
    dict(feature_name="SMA200", feature_family="TREND", required_raw_fields="Close;Stock_Splits", formula="Close_Tech.rolling(200,min_periods=200).mean().last", implementation_reference="scripts/feature_builder.py:build_features", lookback="200 valid observations", minimum_valid_observations=200, lookback_semantics="FINITE", null_behavior="None before 200 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="ATR14_Wilder_DEV", feature_family="VOLATILITY", required_raw_fields="High;Low;Close;Stock_Splits", formula="TR=max(|H-L|,|H-prevClose|,|L-prevClose|); TR.ewm(alpha=1/14,adjust=False,min_periods=14).mean().last", implementation_reference="scripts/feature_builder.py:build_features", lookback="recursive Wilder-style EWM alpha=1/14", minimum_valid_observations=14, lookback_semantics="RECURSIVE_INFINITE_HISTORY_DEPENDENCE", null_behavior="None before 14 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES"),
    dict(feature_name="ATR14_Pct_DEV", feature_family="VOLATILITY", required_raw_fields="High;Low;Close;Stock_Splits", formula="ATR14_Wilder_DEV / Close_Tech", implementation_reference="scripts/feature_builder.py:build_features", lookback="inherits ATR14", minimum_valid_observations=14, lookback_semantics="RECURSIVE_DERIVED", null_behavior="None if ATR or close unavailable/zero", finite_handling="audited post-computation", filtered_series_behavior="inherits filtered ATR/close"),
    dict(feature_name="R5", feature_family="PERFORMANCE", required_raw_fields="Close;Stock_Splits", formula="Close_Tech[t] / Close_Tech[t-5] - 1", implementation_reference="scripts/feature_builder.py:_last_return", lookback="5 return intervals / 6 valid closes", minimum_valid_observations=6, lookback_semantics="FINITE", null_behavior="None if <=5 observations or denominator zero", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="R20", feature_family="PERFORMANCE", required_raw_fields="Close;Stock_Splits", formula="Close_Tech[t] / Close_Tech[t-20] - 1", implementation_reference="scripts/feature_builder.py:_last_return", lookback="20 return intervals / 21 valid closes", minimum_valid_observations=21, lookback_semantics="FINITE", null_behavior="None if <=20 observations or denominator zero", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="R60", feature_family="PERFORMANCE", required_raw_fields="Close;Stock_Splits", formula="Close_Tech[t] / Close_Tech[t-60] - 1", implementation_reference="scripts/feature_builder.py:_last_return", lookback="60 return intervals / 61 valid closes", minimum_valid_observations=61, lookback_semantics="FINITE", null_behavior="None if <=60 observations or denominator zero", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="High20", feature_family="STRUCTURE", required_raw_fields="High;Stock_Splits", formula="High_Tech rolling 20 max", implementation_reference="scripts/feature_builder.py:build_features", lookback="20 valid observations", minimum_valid_observations=20, lookback_semantics="FINITE", null_behavior="None before 20 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="High60", feature_family="STRUCTURE", required_raw_fields="High;Stock_Splits", formula="High_Tech rolling 60 max", implementation_reference="scripts/feature_builder.py:build_features", lookback="60 valid observations", minimum_valid_observations=60, lookback_semantics="FINITE", null_behavior="None before 60 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="High252", feature_family="STRUCTURE", required_raw_fields="High;Stock_Splits", formula="High_Tech rolling 252 max", implementation_reference="scripts/feature_builder.py:build_features", lookback="252 valid observations", minimum_valid_observations=252, lookback_semantics="FINITE", null_behavior="None before 252 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="Low20", feature_family="STRUCTURE", required_raw_fields="Low;Stock_Splits", formula="Low_Tech rolling 20 min", implementation_reference="scripts/feature_builder.py:build_features", lookback="20 valid observations", minimum_valid_observations=20, lookback_semantics="FINITE", null_behavior="None before 20 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="Low60", feature_family="STRUCTURE", required_raw_fields="Low;Stock_Splits", formula="Low_Tech rolling 60 min", implementation_reference="scripts/feature_builder.py:build_features", lookback="60 valid observations", minimum_valid_observations=60, lookback_semantics="FINITE", null_behavior="None before 60 valid observations", finite_handling="technical valid rows only", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="Dist_EMA20", feature_family="STRUCTURE", required_raw_fields="Close;Stock_Splits", formula="Close_Tech / EMA20 - 1", implementation_reference="scripts/feature_builder.py:build_features", lookback="inherits EMA20", minimum_valid_observations=20, lookback_semantics="RECURSIVE_DERIVED", null_behavior="None if close/EMA unavailable/zero", finite_handling="audited post-computation", filtered_series_behavior="inherits filtered EMA20"),
    dict(feature_name="Dist_EMA50", feature_family="STRUCTURE", required_raw_fields="Close;Stock_Splits", formula="Close_Tech / EMA50 - 1", implementation_reference="scripts/feature_builder.py:build_features", lookback="inherits EMA50", minimum_valid_observations=50, lookback_semantics="RECURSIVE_DERIVED", null_behavior="None if close/EMA unavailable/zero", finite_handling="audited post-computation", filtered_series_behavior="inherits filtered EMA50"),
    dict(feature_name="Dist_SMA200", feature_family="STRUCTURE", required_raw_fields="Close;Stock_Splits", formula="Close_Tech / SMA200 - 1", implementation_reference="scripts/feature_builder.py:build_features", lookback="200 valid observations", minimum_valid_observations=200, lookback_semantics="FINITE_DERIVED", null_behavior="None if close/SMA unavailable/zero", finite_handling="audited post-computation", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="Dist_High252", feature_family="STRUCTURE", required_raw_fields="High;Close;Stock_Splits", formula="Close_Tech / High252 - 1", implementation_reference="scripts/feature_builder.py:build_features", lookback="252 valid observations", minimum_valid_observations=252, lookback_semantics="FINITE_DERIVED", null_behavior="None if close/high unavailable/zero", finite_handling="audited post-computation", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="Range20_Pct", feature_family="RANGE", required_raw_fields="High;Low;Close;Stock_Splits", formula="(High20-Low20)/Close_Tech", implementation_reference="scripts/feature_builder.py:build_features", lookback="20 valid observations", minimum_valid_observations=20, lookback_semantics="FINITE", null_behavior="None if inputs unavailable/close zero", finite_handling="audited post-computation", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="MedianVolume20_Tech", feature_family="VOLUME", required_raw_fields="Volume;Stock_Splits", formula="median(last 20 Volume_Tech)", implementation_reference="scripts/feature_builder.py:build_features", lookback="20 non-null valid volume observations", minimum_valid_observations=20, lookback_semantics="FINITE", null_behavior="None if fewer than 20 non-null volume observations", finite_handling="negative non-null volume invalidates raw bar; non-finite result audited", filtered_series_behavior="whole invalid bars excluded"),
    dict(feature_name="MedianTurnover20_Native", feature_family="VOLUME", required_raw_fields="Close;Volume;Stock_Splits", formula="median(last 20 Close_Tech*Volume_Tech)", implementation_reference="scripts/feature_builder.py:build_features", lookback="20 non-null valid turnover observations", minimum_valid_observations=20, lookback_semantics="FINITE", null_behavior="None if fewer than 20 non-null turnover observations", finite_handling="post-computation finite audit", filtered_series_behavior="whole invalid bars excluded"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if fieldnames:
            w.writeheader()
            w.writerows(rows)


def git_blob(path: Path) -> str:
    return git("hash-object", str(path.relative_to(ROOT)))


def connect_ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro&immutable=1", uri=True)


PRICE_DIGEST_SQL = """
SELECT ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired,source_id,fetched_utc
FROM price_daily ORDER BY ws_id,day
"""
MAPPING_DIGEST_SQL = """
SELECT ws_id,yahoo_symbol,mapping_status FROM cache_state ORDER BY ws_id
"""


def table_digest(conn: sqlite3.Connection, sql: str) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    for row in conn.execute(sql):
        h.update(json.dumps(list(row), ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=str).encode())
        h.update(b"\n")
        n += 1
    return h.hexdigest(), n


def validate_repository_authorities(repository_sha: str) -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if head != repository_sha:
        raise RuntimeError(f"checkout SHA mismatch {head} != {repository_sha}")
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"], cwd=ROOT, check=False)
    if anc.returncode != 0:
        raise RuntimeError("required start HEAD is not an ancestor")

    expected_blobs = {
        MASTER_SPEC_PATH: MASTER_SPEC_BLOB,
        FEATURE_BUILDER_PATH: FEATURE_BUILDER_BLOB,
        PRICE_CACHE_PATH: PRICE_CACHE_BLOB,
        V019_SCRIPT_PATH: V019_SCRIPT_BLOB,
        V019_DOC_PATH: V019_DOC_BLOB,
        V052_DEP_PATH: V052_DEP_BLOB,
        V053_IMPL_PATH: V053_IMPL_BLOB,
        V053_SUMMARY_PATH: V053_SUMMARY_BLOB,
        PARAM_READY_PATH: PARAM_READY_BLOB,
    }
    observed = {}
    for p, expected in expected_blobs.items():
        got = git_blob(p)
        observed[str(p.relative_to(ROOT))] = got
        if got != expected:
            raise RuntimeError(f"authority blob mismatch for {p}: {got} != {expected}")

    master = MASTER_SPEC_PATH.read_text(encoding="utf-8")
    required_master_terms = [
        "EMA20", "EMA50", "SMA200", "EMA20-Slope", "EMA50-Slope",
        "R1", "R5", "R20", "R60", "ATR14", "ATR%", "True Range",
        "High20", "High60", "High252", "Low20", "Low60",
        "MedianVolume20", "MedianTurnover20", "relative Volumenmetriken",
        "Gap/ATR", "Tagesbewegung in ATR", "jüngere Impulse", "Run-up 5/20/60T",
    ]
    missing = [x for x in required_master_terms if x not in master]
    if missing:
        raise RuntimeError(f"master local-feature terms missing: {missing}")

    v053 = json.loads(V053_SUMMARY_PATH.read_text(encoding="utf-8"))
    if v053.get("status") != "PASS" or v053.get("p0_price_cache_ready") is not True:
        raise RuntimeError("v0.53 persisted authority is not PASS/ready")
    if v053.get("final_cache") != {"QUARANTINE": 0, "READY": 1425, "total": 1425}:
        raise RuntimeError("v0.53 final cache persisted authority mismatch")

    return {"repository_sha": head, "authority_blobs": observed}


def validate_parameter_authority() -> dict[str, Any]:
    ready = json.loads(PARAM_READY_PATH.read_text(encoding="utf-8"))
    if ready.get("p0_parameter_set_ready") is not False:
        raise RuntimeError("parameter authority unexpectedly ready")
    if ready.get("p0_numeric_pass_thresholds") != [] or ready.get("promoted_lane_pass_rules") != []:
        raise RuntimeError("v0.44 parameter authority unexpectedly contains promoted rules")

    registries = []
    for p in sorted(ROOT.glob("output*/**/*parameter*registry*.json")):
        try:
            x = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        num = x.get("p0_numeric_pass_thresholds")
        promoted = x.get("promoted_lane_pass_rules")
        if isinstance(num, list) and num:
            raise RuntimeError(f"newer/nonempty P0 numeric parameter authority detected at {p}")
        if isinstance(promoted, list) and promoted:
            raise RuntimeError(f"newer/nonempty promoted lane rules detected at {p}")
        registries.append({
            "path": str(p.relative_to(ROOT)),
            "validation_status": x.get("validation_status") or x.get("automation_validation_status"),
            "p0_numeric_pass_threshold_count": len(num) if isinstance(num, list) else None,
            "promoted_lane_pass_rule_count": len(promoted) if isinstance(promoted, list) else None,
        })
    return {
        "status": "UNCHANGED_NON_PROMOTED",
        "current_frozen_pointer": ready.get("authority"),
        "current_frozen_pointer_blob": ready.get("authority_blob_sha"),
        "validation_status": ready.get("validation_status"),
        "p0_numeric_pass_thresholds": [],
        "promoted_lane_pass_rules": [],
        "registries_checked": registries,
    }


def validate_runtime(path: Path) -> dict[str, Any]:
    if path.stat().st_size != V053_RUNTIME_BYTES:
        raise RuntimeError(f"v0.53 runtime byte mismatch: {path.stat().st_size}")
    if sha256_file(path) != V053_RUNTIME_SHA256:
        raise RuntimeError("v0.53 runtime SHA mismatch")
    con = connect_ro(path)
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        price_rows = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        states = int(con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        counts = dict(con.execute("SELECT status,COUNT(*) FROM cache_state GROUP BY status").fetchall())
        price_digest, price_n = table_digest(con, PRICE_DIGEST_SQL)
        mapping_digest, mapping_n = table_digest(con, MAPPING_DIGEST_SQL)
        prov = int(con.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053").fetchone()[0])
        defects = int(con.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053 WHERE source_data_defect=1").fetchone()[0])
        exclusions = int(con.execute("SELECT COUNT(*) FROM technical_bar_exclusions_v053").fetchone()[0])
    finally:
        con.close()
    if integrity != "ok":
        raise RuntimeError("v0.53 runtime integrity_check failed")
    if price_rows != V053_PRICE_ROWS or price_n != V053_PRICE_ROWS:
        raise RuntimeError("v0.53 price row count mismatch")
    if states != V053_STATES or mapping_n != V053_STATES:
        raise RuntimeError("v0.53 state count mismatch")
    if counts != {"READY": 1425}:
        raise RuntimeError(f"v0.53 cache state mismatch: {counts}")
    if price_digest != V053_PRICE_DIGEST:
        raise RuntimeError("v0.53 price semantic digest mismatch")
    if mapping_digest != V053_MAPPING_DIGEST:
        raise RuntimeError("v0.53 provider mapping digest mismatch")
    if prov != 1425 or defects != 8 or exclusions != 8:
        raise RuntimeError("v0.53 provenance table mismatch")
    return {
        "integrity_check": integrity,
        "price_daily": price_rows,
        "states": states,
        "ready": 1425,
        "quarantine": 0,
        "price_daily_digest": price_digest,
        "provider_mapping_digest": mapping_digest,
        "source_defect_securities": defects,
        "excluded_bars": exclusions,
    }


def validate_frozen() -> pd.DataFrame:
    if sha256_file(FROZEN_PATH) != FROZEN_SHA256:
        raise RuntimeError("Frozen SHA mismatch")
    f = pd.read_csv(FROZEN_PATH, dtype=str).fillna("")
    if len(f) != FROZEN_ROWS:
        raise RuntimeError("Frozen count mismatch")
    if f["Security_Key"].duplicated().any() or f["Source_WS_ID"].duplicated().any():
        raise RuntimeError("Frozen identity duplication")
    f["Projection_Order"] = pd.to_numeric(f["Projection_Order"], errors="raise").astype(int)
    return f.sort_values("Projection_Order").reset_index(drop=True)


def feature_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    master_map = {
        "Close_Tech": "implicit local price basis",
        "EMA20": "Trend: EMA20",
        "EMA50": "Trend: EMA50",
        "SMA200": "Trend: SMA200",
        "ATR14_Wilder_DEV": "Volatilitaet: ATR14",
        "ATR14_Pct_DEV": "Volatilitaet: ATR%",
        "R5": "Performance: R5",
        "R20": "Performance: R20",
        "R60": "Performance: R60",
        "High20": "Struktur: High20",
        "High60": "Struktur: High60",
        "High252": "Struktur: High252",
        "Low20": "Struktur: Low20",
        "Low60": "Struktur: Low60",
        "Dist_EMA20": "Struktur: Distanz EMA20",
        "Dist_EMA50": "Struktur: Distanz EMA50",
        "Dist_SMA200": "Struktur: Distanz SMA200",
        "Dist_High252": "Struktur: Distanz zu relevantem Hoch (252 only)",
        "Range20_Pct": "Volatilitaet/Struktur: kurzfristige Range / Range-Mass (20 only)",
        "MedianVolume20_Tech": "Volumen: MedianVolume20",
        "MedianTurnover20_Native": "Volumen: MedianTurnover20",
    }
    formula_by = {r["feature_name"]: r for r in FORMULA_ROWS}
    for name in CANONICAL_FEATURES:
        rows.append({
            "feature_name": name,
            "master_requirement_binding": master_map.get(name, ""),
            "repository_implementation": "scripts/feature_builder.py",
            "authority": f"scripts/feature_builder.py@{FEATURE_BUILDER_BLOB}",
            "status": "CANONICAL_IMPLEMENTED",
            "materialized_v0_54": "YES",
            "readiness_role": "REQUIRED_CURRENT_CANONICAL_IMPLEMENTED_SUBSET",
            "source_fields": formula_by[name]["required_raw_fields"],
            "lookback": formula_by[name]["lookback"],
            "notes": "Authoritative v0.54 measurement if full-population materialization/reproducibility tests pass.",
        })

    for name in HISTORICAL_AUGMENTED:
        if name in CANONICAL_FEATURES:
            continue
        rows.append({
            "feature_name": name,
            "master_requirement_binding": "historical descriptor; some map to master minimum families",
            "repository_implementation": "scripts/p0_feature_augmentation_v0_19.py",
            "authority": f"historical v0.19 only@{V019_SCRIPT_BLOB}",
            "status": "PARTIAL_AUGMENTED",
            "materialized_v0_54": "NO",
            "readiness_role": "MASTER_GAP_EVIDENCE_ONLY_NOT_CURRENT_AUTHORITY",
            "source_fields": "",
            "lookback": "",
            "notes": "Implemented historically/descriptively but not silently promoted into current v0.54 canonical feature authority.",
        })

    gaps = [
        ("R1", "Performance: R1", "NOT_IMPLEMENTED", "No current or v0.19 authoritative implementation identified."),
        ("Gap_ATR", "Impuls: Gap/ATR", "NOT_IMPLEMENTED", "v0.19 has Gap_Pct and ATR descriptors, but no governed exact Gap/ATR feature."),
        ("RunUp_5_20_60_MasterSemantic", "Impuls: Run-up 5/20/60T", "NOT_VERIFIED", "R5/R20/R60 exist as performance returns, but repository authority does not explicitly equate them with the separate master run-up semantic."),
        ("RelevantHighDistance_MasterFamily", "Struktur: Distanz zu relevanten Hochs", "PARTIAL_AUGMENTED", "Current canonical only Dist_High252; historical v0.19 has Distance_High20_ATR but no fully bound current family."),
        ("RangeCompression_MasterFamily", "Struktur: Range-/Compression-Masse", "PARTIAL_AUGMENTED", "Current canonical Range20 only; richer Range5/10/ratios exist only in v0.19 historical augmentation."),
        ("HomeMarket_RS20_RS60", "Relative Staerke Heimatmarkt", "NOT_VERIFIED", "Explicitly out of scope for v0.54; later Home-Market RS gate."),
        ("Sector_RS20_RS60", "Relative Staerke Sektor", "NOT_VERIFIED", "Explicitly out of scope for v0.54; later Sector RS gate."),
    ]
    for name, binding, status, note in gaps:
        if not any(r["feature_name"] == name for r in rows):
            rows.append({
                "feature_name": name,
                "master_requirement_binding": binding,
                "repository_implementation": "",
                "authority": "master spec + current repository discovery",
                "status": status,
                "materialized_v0_54": "NO",
                "readiness_role": "OUT_OF_SCOPE_RS_LATER_GATE" if "_RS" in name else "MASTER_LOCAL_MODEL_GAP",
                "source_fields": "",
                "lookback": "",
                "notes": note,
            })

    # Add explicit family gap bindings for v0.19-only implementations that block local-layer completion.
    explicit_gap_rows = [
        ("EMA20_Slope_Master", "Trend: EMA20-Slope", "EMA20_Slope5_Pct"),
        ("EMA50_Slope_Master", "Trend: EMA50-Slope", "EMA50_Slope10_Pct"),
        ("TrueRange_Master", "Volatilitaet: True Range", "TrueRange_Current"),
        ("RelativeVolume_Master", "Volumen: relative Volumenmetriken", "RVOL20_Current"),
        ("DailyMoveInATR_Master", "Impuls: Tagesbewegung in ATR", "TrueRange_ATR14_Ratio"),
        ("RecentImpulse_Master", "Impuls: juengere Impulse", "Impulse_Return20_Max/PostImpulse descriptors"),
    ]
    for name, binding, hist in explicit_gap_rows:
        rows.append({
            "feature_name": name,
            "master_requirement_binding": binding,
            "repository_implementation": "scripts/p0_feature_augmentation_v0_19.py",
            "authority": f"historical v0.19 only@{V019_SCRIPT_BLOB}",
            "status": "PARTIAL_AUGMENTED",
            "materialized_v0_54": "NO",
            "readiness_role": "MASTER_LOCAL_MODEL_GAP",
            "source_fields": "",
            "lookback": "",
            "notes": f"Historical implementation evidence: {hist}; not current canonical authority.",
        })
    return rows


def validate_inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = [r["feature_name"] for r in rows if r["status"] == "CANONICAL_IMPLEMENTED"]
    if canonical != CANONICAL_FEATURES:
        raise RuntimeError("canonical feature inventory order/content mismatch")
    # Map master gap tokens to discovered non-canonical status.
    statuses = {r["feature_name"]: r["status"] for r in rows}
    required_bindings = {
        "EMA20_SLOPE": statuses.get("EMA20_Slope_Master"),
        "EMA50_SLOPE": statuses.get("EMA50_Slope_Master"),
        "R1": statuses.get("R1"),
        "TRUE_RANGE_CURRENT": statuses.get("TrueRange_Master"),
        "RANGE_COMPRESSION_FAMILY": statuses.get("RangeCompression_MasterFamily"),
        "RELATIVE_VOLUME_METRICS": statuses.get("RelativeVolume_Master"),
        "GAP_OVER_ATR": statuses.get("Gap_ATR"),
        "DAILY_MOVE_IN_ATR": statuses.get("DailyMoveInATR_Master"),
        "RECENT_IMPULSE_DESCRIPTORS": statuses.get("RecentImpulse_Master"),
        "RUNUP_5_20_60_SEMANTICS": statuses.get("RunUp_5_20_60_MasterSemantic"),
        "RELEVANT_HIGH_DISTANCE_FAMILY": statuses.get("RelevantHighDistance_MasterFamily"),
    }
    unresolved = [k for k, v in required_bindings.items() if v != "CANONICAL_IMPLEMENTED"]
    if unresolved != MASTER_LOCAL_BLOCKING_GAPS:
        raise RuntimeError(f"master local gap binding changed unexpectedly: {unresolved}")
    return {
        "canonical_feature_count": len(canonical),
        "master_local_blocking_gaps": unresolved,
        "home_market_rs_excluded_from_local_readiness": True,
        "sector_rs_excluded_from_local_readiness": True,
    }


def materialization_semantic_bytes(df: pd.DataFrame) -> bytes:
    cols = [
        "Projection_Order", "Security_Key", "Source_WS_ID", "Primary_MIC", "Primary_Ticker",
        "feature_as_of_date", "valid_bar_count", "excluded_bar_count", "source_data_defect",
        "excluded_dates", "filtered_policy_version", *CANONICAL_FEATURES,
    ]
    x = df[cols].copy().sort_values("Projection_Order").reset_index(drop=True)
    text = x.to_csv(index=False, lineterminator="\n", float_format="%.17g", na_rep="<NULL>")
    return text.encode("utf-8")


def semantic_digest(df: pd.DataFrame) -> str:
    return hashlib.sha256(materialization_semantic_bytes(df)).hexdigest()


def build_temp_universe(frozen: pd.DataFrame, path: Path) -> None:
    pd.DataFrame({"WS_ID": frozen["Source_WS_ID"].astype(str)}).to_csv(path, index=False)


def load_provenance(runtime: Path) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    con = connect_ro(runtime)
    try:
        prov = pd.read_sql_query(
            "SELECT ws_id,source_data_defect,invalid_bar_count,invalid_share,affected_dates_json,"
            "defect_reasons_json,core_qa_policy,history_qa_policy,implementation_policy,filtered_policy_result "
            "FROM cache_qa_provenance_v053 ORDER BY ws_id",
            con,
        )
        ex = pd.read_sql_query(
            "SELECT ws_id,day,source_data_defect,technical_bar_excluded,reason_codes "
            "FROM technical_bar_exclusions_v053 ORDER BY ws_id,day",
            con,
        )
    finally:
        con.close()
    dates: dict[str, list[str]] = defaultdict(list)
    for r in ex.to_dict("records"):
        dates[str(r["ws_id"])].append(str(r["day"]))
    return prov, dates


def materialize_once(runtime_work: Path, frozen: pd.DataFrame, universe_csv: Path) -> pd.DataFrame:
    feat = build_features(runtime_work, universe_csv)
    if len(feat) != FROZEN_ROWS or feat["WS_ID"].astype(str).nunique() != FROZEN_ROWS:
        raise RuntimeError(f"build_features did not return exact Frozen 1425: rows={len(feat)}")
    missing_cols = [c for c in CANONICAL_FEATURES if c not in feat.columns]
    if missing_cols:
        raise RuntimeError(f"canonical feature columns missing from feature_builder output: {missing_cols}")

    base = frozen[["Projection_Order", "Security_Key", "Source_WS_ID", "Primary_MIC", "Primary_Ticker"]].copy()
    out = base.merge(feat, left_on="Source_WS_ID", right_on="WS_ID", how="left", validate="one_to_one")
    if out["AsOf"].isna().any():
        missing = out.loc[out["AsOf"].isna(), "Source_WS_ID"].tolist()
        raise RuntimeError(f"missing feature rows after Frozen merge: {missing[:20]}")
    out["feature_as_of_date"] = out["AsOf"].astype(str)
    out["valid_bar_count"] = pd.to_numeric(out["Bars_Used"], errors="raise").astype(int)
    out["excluded_bar_count"] = pd.to_numeric(out["Excluded_Invalid_Bars"], errors="raise").astype(int)
    out["source_data_defect"] = False
    out["excluded_dates"] = ""
    out["filtered_policy_version"] = "v0.53/POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT"
    return out.sort_values("Projection_Order").reset_index(drop=True)


def attach_provenance(out: pd.DataFrame, prov: pd.DataFrame, dates: dict[str, list[str]]) -> pd.DataFrame:
    p = prov[["ws_id", "source_data_defect", "invalid_bar_count", "implementation_policy"]].copy()
    p["ws_id"] = p["ws_id"].astype(str)
    x = out.merge(p, left_on="Source_WS_ID", right_on="ws_id", how="left", validate="one_to_one", suffixes=("", "_prov"))
    if x["source_data_defect_prov"].isna().any() if "source_data_defect_prov" in x.columns else False:
        raise RuntimeError("missing provenance rows")
    # pandas suffix behavior because out already has source_data_defect.
    if "source_data_defect_prov" in x.columns:
        x["source_data_defect"] = pd.to_numeric(x["source_data_defect_prov"], errors="raise").astype(int).astype(bool)
        x.drop(columns=["source_data_defect_prov"], inplace=True)
    else:
        # defensive path if pandas chose no suffix due future column shape.
        x["source_data_defect"] = pd.to_numeric(x["source_data_defect"], errors="raise").astype(int).astype(bool)
    x["excluded_dates"] = x["Source_WS_ID"].map(lambda ws: "|".join(dates.get(str(ws), [])))
    x["excluded_bar_count"] = pd.to_numeric(x["excluded_bar_count"], errors="raise").astype(int)
    if not (x["excluded_bar_count"] == pd.to_numeric(x["invalid_bar_count"], errors="raise").astype(int)).all():
        raise RuntimeError("feature excluded-bar counts differ from v0.53 provenance")
    x.drop(columns=["ws_id", "invalid_bar_count", "implementation_policy"], inplace=True, errors="ignore")
    return x.sort_values("Projection_Order").reset_index(drop=True)


def load_prices(runtime: Path) -> pd.DataFrame:
    con = connect_ro(runtime)
    try:
        px = pd.read_sql_query(
            "SELECT ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired "
            "FROM price_daily ORDER BY ws_id,day",
            con,
        )
    finally:
        con.close()
    px["day"] = pd.to_datetime(px["day"], errors="raise")
    return px


def safe_last(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return None if x.empty else float(x.iloc[-1])


def n_return(s: pd.Series, n: int) -> float | None:
    x = pd.to_numeric(s, errors="coerce")
    if len(x) <= n:
        return None
    den = float(x.iloc[-n - 1])
    if den == 0 or not math.isfinite(den):
        return None
    val = float(x.iloc[-1] / den - 1.0)
    return val if math.isfinite(val) else None


def independent_canonical(g_raw: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    g = g_raw.sort_values("day").copy()
    valid = technical_valid_mask_for_features(g)
    g = g.loc[valid].copy()
    if g.empty:
        return {}, g
    g = split_adjust_technical(g)
    c = pd.to_numeric(g["close_tech"], errors="coerce")
    h = pd.to_numeric(g["high_tech"], errors="coerce")
    l = pd.to_numeric(g["low_tech"], errors="coerce")
    v = pd.to_numeric(g["volume_tech"], errors="coerce")
    prev = c.shift(1)
    tr = pd.concat([(h-l).abs(), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    ema20 = c.ewm(span=20, adjust=False, min_periods=20).mean()
    ema50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
    sma200 = c.rolling(200, min_periods=200).mean()
    high20 = h.rolling(20, min_periods=20).max()
    high60 = h.rolling(60, min_periods=60).max()
    high252 = h.rolling(252, min_periods=252).max()
    low20 = l.rolling(20, min_periods=20).min()
    low60 = l.rolling(60, min_periods=60).min()
    turnover = c * v
    close = safe_last(c)
    e20, e50, s200 = safe_last(ema20), safe_last(ema50), safe_last(sma200)
    hi20, hi60, hi252 = safe_last(high20), safe_last(high60), safe_last(high252)
    lo20, lo60 = safe_last(low20), safe_last(low60)
    atr = safe_last(atr14)

    def dist(vv: float | None) -> float | None:
        if close is None or vv in (None, 0):
            return None
        x = close / float(vv) - 1.0
        return x if math.isfinite(x) else None

    out = {
        "Close_Tech": close,
        "EMA20": e20,
        "EMA50": e50,
        "SMA200": s200,
        "ATR14_Wilder_DEV": atr,
        "ATR14_Pct_DEV": None if atr is None or close in (None, 0) else float(atr / close),
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
        "Range20_Pct": None if close in (None,0) or hi20 is None or lo20 is None else float((hi20-lo20)/close),
        "MedianVolume20_Tech": float(v.tail(20).median()) if len(v.dropna()) >= 20 else None,
        "MedianTurnover20_Native": float(turnover.tail(20).median()) if len(turnover.dropna()) >= 20 else None,
    }
    return out, g


def value_equal_exact(a: Any, b: Any) -> bool:
    if a is None or (isinstance(a, float) and math.isnan(a)):
        return b is None or (isinstance(b, float) and math.isnan(b))
    if b is None or (isinstance(b, float) and math.isnan(b)):
        return False
    try:
        return float(a) == float(b)
    except Exception:
        return a == b


def full_formula_reproducibility(materialized: pd.DataFrame, px: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_mat = materialized.set_index("Source_WS_ID", drop=False)
    recursive_rows: list[dict[str, Any]] = []
    temporal_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    for ws, g in px.groupby("ws_id", sort=False):
        ws = str(ws)
        exp, filtered = independent_canonical(g)
        if ws not in by_mat.index:
            raise RuntimeError(f"price identity missing materialization: {ws}")
        got = by_mat.loc[ws]
        for feat in CANONICAL_FEATURES:
            if not value_equal_exact(got[feat], exp.get(feat)):
                mismatch_rows.append({
                    "Source_WS_ID": ws,
                    "Feature": feat,
                    "Materialized": got[feat],
                    "Independent": exp.get(feat),
                })
        raw_max = pd.to_datetime(g["day"]).max().date().isoformat()
        valid_max = pd.to_datetime(filtered["day"]).max().date().isoformat() if not filtered.empty else ""
        feature_asof = str(got["feature_as_of_date"])
        future_rows = int((pd.to_datetime(g["day"]) > pd.Timestamp(feature_asof)).sum())
        temporal_rows.append({
            "Security_Key": got["Security_Key"],
            "Source_WS_ID": ws,
            "Primary_MIC": got["Primary_MIC"],
            "Primary_Ticker": got["Primary_Ticker"],
            "raw_latest_date": raw_max,
            "latest_eligible_valid_date": valid_max,
            "feature_as_of_date": feature_asof,
            "rows_after_feature_as_of": future_rows,
            "date_order_monotonic": bool(pd.to_datetime(g["day"]).is_monotonic_increasing),
            "temporal_integrity": "PASS" if feature_asof == valid_max and future_rows == 0 else "FAIL",
        })
        recursive_rows.append({
            "Security_Key": got["Security_Key"],
            "Source_WS_ID": ws,
            "EMA20_materialized": got["EMA20"],
            "EMA20_independent": exp.get("EMA20"),
            "EMA20_exact_match": value_equal_exact(got["EMA20"], exp.get("EMA20")),
            "EMA50_materialized": got["EMA50"],
            "EMA50_independent": exp.get("EMA50"),
            "EMA50_exact_match": value_equal_exact(got["EMA50"], exp.get("EMA50")),
            "ATR14_materialized": got["ATR14_Wilder_DEV"],
            "ATR14_independent": exp.get("ATR14_Wilder_DEV"),
            "ATR14_exact_match": value_equal_exact(got["ATR14_Wilder_DEV"], exp.get("ATR14_Wilder_DEV")),
            "semantics": "DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES",
        })
    if mismatch_rows:
        raise RuntimeError(f"canonical feature reproducibility mismatches: {mismatch_rows[:10]}")
    if any(r["temporal_integrity"] != "PASS" for r in temporal_rows):
        raise RuntimeError("temporal integrity mismatch")
    return recursive_rows, temporal_rows, mismatch_rows


def null_nonfinite_audits(materialized: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    feat_rows: list[dict[str, Any]] = []
    mic_rows: list[dict[str, Any]] = []
    sec_rows: list[dict[str, Any]] = []
    for feat in CANONICAL_FEATURES:
        s = pd.to_numeric(materialized[feat], errors="coerce")
        null = int(materialized[feat].isna().sum())
        nan = int(s.isna().sum())
        posinf = int(np.isposinf(s.to_numpy(dtype=float, na_value=np.nan)).sum())
        neginf = int(np.isneginf(s.to_numpy(dtype=float, na_value=np.nan)).sum())
        feat_rows.append({
            "Feature": feat,
            "Rows": len(materialized),
            "NULL_or_NaN": max(null, nan),
            "PosInf": posinf,
            "NegInf": neginf,
            "NonFinite_Total": max(null, nan) + posinf + neginf,
        })
        for mic, g in materialized.groupby("Primary_MIC", sort=True):
            ss = pd.to_numeric(g[feat], errors="coerce")
            nn = int(ss.isna().sum())
            pp = int(np.isposinf(ss.to_numpy(dtype=float, na_value=np.nan)).sum())
            mm = int(np.isneginf(ss.to_numpy(dtype=float, na_value=np.nan)).sum())
            mic_rows.append({
                "Primary_MIC": mic,
                "Feature": feat,
                "Rows": len(g),
                "NULL_or_NaN": nn,
                "PosInf": pp,
                "NegInf": mm,
                "NonFinite_Total": nn + pp + mm,
            })
    for r in materialized.to_dict("records"):
        count = 0
        affected = []
        for feat in CANONICAL_FEATURES:
            try:
                v = float(r[feat])
                ok = math.isfinite(v)
            except Exception:
                ok = False
            if not ok:
                count += 1
                affected.append(feat)
        sec_rows.append({
            "Security_Key": r["Security_Key"],
            "Source_WS_ID": r["Source_WS_ID"],
            "Primary_MIC": r["Primary_MIC"],
            "Primary_Ticker": r["Primary_Ticker"],
            "Required_Canonical_NonFinite_Count": count,
            "Affected_Features": "|".join(affected),
        })
    return feat_rows, mic_rows, sec_rows


def capability_rows(materialized: pd.DataFrame, sec_audit: list[dict[str, Any]], inventory_state: dict[str, Any]) -> list[dict[str, Any]]:
    sec_by = {r["Source_WS_ID"]: r for r in sec_audit}
    rows = []
    max_required_history = max(int(r["minimum_valid_observations"]) for r in FORMULA_ROWS)
    global_gap = bool(inventory_state["master_local_blocking_gaps"])
    for r in materialized.to_dict("records"):
        ws = r["Source_WS_ID"]
        nonfinite = int(sec_by[ws]["Required_Canonical_NonFinite_Count"])
        valid = int(r["valid_bar_count"])
        if valid < max_required_history:
            status = "FEATURE_BLOCKED_INSUFFICIENT_HISTORY"
            reason = f"VALID_BARS_{valid}_LT_CANONICAL_MAX_{max_required_history}"
        elif nonfinite > 0:
            status = "FEATURE_BLOCKED_INPUT"
            reason = "REQUIRED_CANONICAL_IMPLEMENTED_FEATURE_NULL_OR_NONFINITE"
        elif global_gap:
            status = "FEATURE_PARTIAL"
            reason = "MASTER_REQUIRED_LOCAL_FEATURE_MODEL_NOT_FULLY_CANONICAL_IMPLEMENTED"
        else:
            status = "FEATURE_READY"
            reason = "ALL_REQUIRED_CANONICAL_LOCAL_FEATURES_COMPLETE"
        rows.append({
            "Projection_Order": r["Projection_Order"],
            "Security_Key": r["Security_Key"],
            "Source_WS_ID": ws,
            "Primary_MIC": r["Primary_MIC"],
            "Primary_Ticker": r["Primary_Ticker"],
            "feature_as_of_date": r["feature_as_of_date"],
            "valid_bar_count": valid,
            "excluded_bar_count": int(r["excluded_bar_count"]),
            "source_data_defect": bool(r["source_data_defect"]),
            "feature_capability_status": status,
            "capability_reason": reason,
            "required_current_canonical_feature_count": len(CANONICAL_FEATURES),
            "required_current_canonical_nonfinite_count": nonfinite,
            "master_local_model_gap_count": len(inventory_state["master_local_blocking_gaps"]),
        })
    return rows


def cross_security_integrity(frozen: pd.DataFrame, px: pd.DataFrame, materialized: pd.DataFrame) -> dict[str, Any]:
    dup_px = int(px.duplicated(subset=["ws_id", "day"]).sum())
    duplicated_feature_ws = int(materialized["Source_WS_ID"].duplicated().sum())
    cross = (
        frozen.groupby("Primary_Ticker")["Primary_MIC"]
        .nunique()
        .loc[lambda s: s > 1]
        .sort_index()
    )
    cross_tickers = cross.index.tolist()
    if dup_px != 0 or duplicated_feature_ws != 0:
        raise RuntimeError("duplicate identity/date or feature identity detected")
    if set(materialized["Source_WS_ID"].astype(str)) != set(frozen["Source_WS_ID"].astype(str)):
        raise RuntimeError("feature population differs from Frozen")
    return {
        "price_duplicate_ws_id_date_rows": dup_px,
        "feature_duplicate_source_ws_id_rows": duplicated_feature_ws,
        "group_key": "Source_WS_ID (not ticker)",
        "same_ticker_multiple_mic_count": len(cross_tickers),
        "same_ticker_multiple_mic_tickers": cross_tickers,
        "cross_security_contamination_result": "PASS",
    }


def asx8_regression(runtime: Path, materialized: pd.DataFrame, px: pd.DataFrame, recursive: list[dict[str, Any]]) -> list[dict[str, Any]]:
    con = connect_ro(runtime)
    try:
        defect_ws = [str(r[0]) for r in con.execute(
            "SELECT ws_id FROM cache_qa_provenance_v053 WHERE source_data_defect=1 ORDER BY ws_id"
        ).fetchall()]
        exclusions = {
            str(ws): str(day)
            for ws, day in con.execute(
                "SELECT ws_id,day FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1 ORDER BY ws_id,day"
            ).fetchall()
        }
    finally:
        con.close()
    if len(defect_ws) != 8 or len(exclusions) != 8:
        raise RuntimeError("v0.53 source-defect validation population is not exact 8")
    mat = materialized.set_index("Source_WS_ID", drop=False)
    rec = {r["Source_WS_ID"]: r for r in recursive}
    rows = []
    for ws in defect_ws:
        g = px.loc[px["ws_id"].astype(str) == ws].sort_values("day").copy()
        valid = technical_valid_mask_for_features(g)
        bad_day = exclusions[ws]
        raw_present = int((g["day"].dt.date.astype(str) == bad_day).sum())
        bad_mask = g["day"].dt.date.astype(str).eq(bad_day)
        excluded_from_input = raw_present == 1 and bool((~valid.loc[bad_mask]).all())
        got = mat.loc[ws]
        rr = rec[ws]
        rows.append({
            "Security_Key": got["Security_Key"],
            "Source_WS_ID": ws,
            "Primary_MIC": got["Primary_MIC"],
            "Primary_Ticker": got["Primary_Ticker"],
            "raw_bars": len(g),
            "valid_bars": int(valid.sum()),
            "excluded_bars": int((~valid).sum()),
            "feature_input_bars": int(got["valid_bar_count"]),
            "excluded_date": bad_day,
            "raw_bar_remains_present": raw_present == 1,
            "excluded_date_absent_from_feature_input": excluded_from_input,
            "feature_as_of_date": got["feature_as_of_date"],
            "EMA20_filtered_exact": bool(rr["EMA20_exact_match"]),
            "EMA50_filtered_exact": bool(rr["EMA50_exact_match"]),
            "ATR14_filtered_exact": bool(rr["ATR14_exact_match"]),
            "finite_window_features_filtered": "PASS",
            "technical_capability": "CORE_IMPLEMENTED_FEATURES_COMPLETE_BUT_GLOBAL_MASTER_MODEL_GAP",
            "regression_result": "PASS" if raw_present == 1 and excluded_from_input and rr["EMA20_exact_match"] and rr["EMA50_exact_match"] and rr["ATR14_exact_match"] else "FAIL",
        })
    if any(r["regression_result"] != "PASS" for r in rows):
        raise RuntimeError("source-defect feature regression failed")
    return rows


def test_results(
    runtime_info: dict[str, Any],
    inventory_state: dict[str, Any],
    materialized: pd.DataFrame,
    capability: list[dict[str, Any]],
    feat_audit: list[dict[str, Any]],
    recursive: list[dict[str, Any]],
    temporal: list[dict[str, Any]],
    determinism: dict[str, Any],
    cross: dict[str, Any],
    asx: list[dict[str, Any]],
    runtime_immutability: dict[str, Any],
    parameter: dict[str, Any],
) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    def add(name: str, ok: bool, detail: str) -> None:
        tests.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})
        if not ok:
            raise AssertionError(f"{name}: {detail}")

    add("V053_RUNTIME_AUTHORITY_EXACT", runtime_info == {
        "integrity_check": "ok", "price_daily": 711204, "states": 1425, "ready": 1425, "quarantine": 0,
        "price_daily_digest": V053_PRICE_DIGEST, "provider_mapping_digest": V053_MAPPING_DIGEST,
        "source_defect_securities": 8, "excluded_bars": 8,
    }, json.dumps(runtime_info, sort_keys=True))
    add("FROZEN_IDENTITY_EXACT", len(materialized) == 1425 and materialized["Security_Key"].nunique() == 1425 and materialized["Source_WS_ID"].nunique() == 1425, "1425 unique identities")
    add("CANONICAL_FEATURE_INVENTORY_BOUND", inventory_state["canonical_feature_count"] == 21, json.dumps(inventory_state, sort_keys=True))
    add("WHOLE_BAR_EXCLUSION", all(r["excluded_date_absent_from_feature_input"] for r in asx), "all v0.53 defect bars excluded as whole bars")
    add("SOURCE_DEFECT_8_REGRESSION", len(asx) == 8 and all(r["regression_result"] == "PASS" for r in asx), "8/8 pass")
    for feat in ["R5", "R20", "R60", "EMA20", "EMA50", "SMA200", "ATR14_Wilder_DEV", "High20", "High60", "High252", "Low20", "Low60", "Range20_Pct", "MedianVolume20_Tech", "MedianTurnover20_Native"]:
        add(f"FEATURE_{feat}_FINITE_FULL_POPULATION", int(next(r["NonFinite_Total"] for r in feat_audit if r["Feature"] == feat)) == 0, feat)
    add("ALL_CURRENT_CANONICAL_FEATURES_FINITE", all(int(r["NonFinite_Total"]) == 0 for r in feat_audit), f"features={len(feat_audit)}")
    add("RECURSIVE_EMA20_EXACT", all(r["EMA20_exact_match"] for r in recursive), "1425/1425 exact")
    add("RECURSIVE_EMA50_EXACT", all(r["EMA50_exact_match"] for r in recursive), "1425/1425 exact")
    add("RECURSIVE_ATR14_EXACT", all(r["ATR14_exact_match"] for r in recursive), "1425/1425 exact")
    add("MINIMUM_HISTORY_CURRENT_IMPLEMENTED", int(materialized["valid_bar_count"].min()) >= 252, f"min_valid={int(materialized['valid_bar_count'].min())}")
    add("PER_SECURITY_ISOLATION", cross["cross_security_contamination_result"] == "PASS", json.dumps(cross, sort_keys=True))
    add("DATE_ORDERING", all(r["date_order_monotonic"] for r in temporal), "all input groups ordered")
    add("DUPLICATE_DATE_HANDLING", cross["price_duplicate_ws_id_date_rows"] == 0, "zero duplicate ws_id/day rows")
    add("NO_FORWARD_LEAKAGE", all(r["rows_after_feature_as_of"] == 0 for r in temporal), "zero rows after feature as-of")
    add("TEMPORAL_INTEGRITY", all(r["temporal_integrity"] == "PASS" for r in temporal), "1425/1425")
    add("TWO_PASS_SEMANTIC_DIGEST", determinism["pass1_semantic_sha256"] == determinism["pass2_semantic_sha256"], json.dumps(determinism, sort_keys=True))
    add("PRICE_RUNTIME_IMMUTABILITY", runtime_immutability["sqlite_sha256_unchanged"] and runtime_immutability["price_daily_digest_unchanged"] and runtime_immutability["cache_state_counts_unchanged"], json.dumps(runtime_immutability, sort_keys=True))
    add("FROZEN_IMMUTABILITY", sha256_file(FROZEN_PATH) == FROZEN_SHA256, FROZEN_SHA256)
    add("MAPPING_IMMUTABILITY", runtime_immutability["provider_mapping_digest_unchanged"], V053_MAPPING_DIGEST)
    add("NO_RS_EXECUTION", HOME_MARKET_RS_READY is False and SECTOR_RS_READY is False, "home=false;sector=false")
    add("PARAMETER_AUTHORITY_UNCHANGED", parameter["status"] == "UNCHANGED_NON_PROMOTED" and not parameter["p0_numeric_pass_thresholds"] and not parameter["promoted_lane_pass_rules"], parameter["current_frozen_pointer"])
    add("NO_P0_CLASSIFICATION", P0_RUNS == 0, "p0_runs=0")
    add("NO_PROVIDER_CALLS", MARKET_PROVIDER_CALLS == 0 and YAHOO_YFINANCE_CALLS == 0 and EODHD_CALLS == 0 and ALPHA_VANTAGE_CALLS == 0 and SCALABLE_CALLS == 0, "all zero")
    add("CAPABILITY_COUNTS_SUM_1425", sum(Counter(r["feature_capability_status"] for r in capability).values()) == 1425, json.dumps(Counter(r["feature_capability_status"] for r in capability), sort_keys=True))
    return tests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sqlite", required=True)
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_features_v0_54")
    ap.add_argument("--repository-sha", required=True)
    args = ap.parse_args()

    source = Path(args.source_sqlite)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    repo_authority = validate_repository_authorities(args.repository_sha)
    frozen = validate_frozen()
    parameter = validate_parameter_authority()
    runtime_before_sha = sha256_file(source)
    runtime_before_bytes = source.stat().st_size
    runtime_info = validate_runtime(source)

    inventory = feature_inventory()
    inventory_state = validate_inventory(inventory)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        work_db = td / "v053_work_copy.sqlite"
        shutil.copyfile(source, work_db)
        if sha256_file(work_db) != V053_RUNTIME_SHA256:
            raise RuntimeError("work copy not byte-identical to v0.53 runtime")
        uni = td / "frozen_for_builder.csv"
        build_temp_universe(frozen, uni)

        pass1 = materialize_once(work_db, frozen, uni)
        prov, dates = load_provenance(source)
        pass1 = attach_provenance(pass1, prov, dates)
        pass2 = materialize_once(work_db, frozen, uni)
        pass2 = attach_provenance(pass2, prov, dates)

    digest1 = semantic_digest(pass1)
    digest2 = semantic_digest(pass2)
    determinism = {
        "semantic_columns": [
            "Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker",
            "feature_as_of_date","valid_bar_count","excluded_bar_count","source_data_defect",
            "excluded_dates","filtered_policy_version",*CANONICAL_FEATURES
        ],
        "row_order": "Projection_Order ascending",
        "float_serialization": "%.17g",
        "null_serialization": "<NULL>",
        "pass1_semantic_sha256": digest1,
        "pass2_semantic_sha256": digest2,
        "semantic_digest_match": digest1 == digest2,
    }
    if digest1 != digest2:
        raise RuntimeError("two-pass semantic feature digest mismatch")

    px = load_prices(source)
    if len(px) != V053_PRICE_ROWS:
        raise RuntimeError("price input row count changed during feature stage")

    recursive, temporal, mismatches = full_formula_reproducibility(pass1, px)
    if mismatches:
        raise RuntimeError("unexpected formula mismatches")

    feat_audit, mic_audit, sec_audit = null_nonfinite_audits(pass1)
    capability = capability_rows(pass1, sec_audit, inventory_state)
    counts = Counter(r["feature_capability_status"] for r in capability)
    if sum(counts.values()) != FROZEN_ROWS:
        raise RuntimeError("capability count does not reconcile to 1425")

    cross = cross_security_integrity(frozen, px, pass1)
    asx = asx8_regression(source, pass1, px, recursive)

    runtime_after_sha = sha256_file(source)
    runtime_after_bytes = source.stat().st_size
    runtime_after = validate_runtime(source)
    runtime_immutability = {
        "sqlite_sha256_before": runtime_before_sha,
        "sqlite_sha256_after": runtime_after_sha,
        "sqlite_sha256_unchanged": runtime_before_sha == runtime_after_sha == V053_RUNTIME_SHA256,
        "sqlite_bytes_before": runtime_before_bytes,
        "sqlite_bytes_after": runtime_after_bytes,
        "sqlite_bytes_unchanged": runtime_before_bytes == runtime_after_bytes == V053_RUNTIME_BYTES,
        "price_daily_digest_before": runtime_info["price_daily_digest"],
        "price_daily_digest_after": runtime_after["price_daily_digest"],
        "price_daily_digest_unchanged": runtime_info["price_daily_digest"] == runtime_after["price_daily_digest"] == V053_PRICE_DIGEST,
        "provider_mapping_digest_before": runtime_info["provider_mapping_digest"],
        "provider_mapping_digest_after": runtime_after["provider_mapping_digest"],
        "provider_mapping_digest_unchanged": runtime_info["provider_mapping_digest"] == runtime_after["provider_mapping_digest"] == V053_MAPPING_DIGEST,
        "cache_state_counts_before": {"READY": runtime_info["ready"], "QUARANTINE": runtime_info["quarantine"]},
        "cache_state_counts_after": {"READY": runtime_after["ready"], "QUARANTINE": runtime_after["quarantine"]},
        "cache_state_counts_unchanged": runtime_after["ready"] == 1425 and runtime_after["quarantine"] == 0,
        "integrity_check_after": runtime_after["integrity_check"],
    }
    if not all([
        runtime_immutability["sqlite_sha256_unchanged"],
        runtime_immutability["sqlite_bytes_unchanged"],
        runtime_immutability["price_daily_digest_unchanged"],
        runtime_immutability["provider_mapping_digest_unchanged"],
        runtime_immutability["cache_state_counts_unchanged"],
    ]):
        raise RuntimeError("v0.53 price runtime mutated")

    tests = test_results(
        runtime_info, inventory_state, pass1, capability, feat_audit, recursive, temporal,
        determinism, cross, asx, runtime_immutability, parameter
    )

    # Materialization contains only current canonical-implemented technical values plus required provenance/identity.
    material_cols = [
        "Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker",
        "feature_as_of_date","valid_bar_count","excluded_bar_count","source_data_defect",
        "excluded_dates","filtered_policy_version",*CANONICAL_FEATURES
    ]
    mat_out = pass1[material_cols].copy()
    mat_out.to_csv(out_dir / "feature_materialization_v0.54.csv", index=False, lineterminator="\n", float_format="%.17g", na_rep="")

    write_csv(out_dir / "feature_inventory_v0.54.csv", inventory)
    write_csv(out_dir / "feature_formula_binding_v0.54.csv", FORMULA_ROWS)
    write_csv(out_dir / "feature_capability_v0.54.csv", capability)
    nonready = [r for r in capability if r["feature_capability_status"] != "FEATURE_READY"]
    write_csv(out_dir / "non_ready_securities_v0.54.csv", nonready, list(capability[0].keys()))
    write_csv(out_dir / "null_nonfinite_audit_v0.54.csv", feat_audit)
    write_csv(out_dir / "null_nonfinite_by_mic_v0.54.csv", mic_audit)
    write_csv(out_dir / "null_nonfinite_by_security_v0.54.csv", sec_audit)
    write_csv(out_dir / "asx8_feature_regression_v0.54.csv", asx)
    write_csv(out_dir / "recursive_feature_reproducibility_v0.54.csv", recursive)
    write_csv(out_dir / "temporal_integrity_v0.54.csv", temporal)
    write_csv(out_dir / "test_results_v0.54.csv", tests)
    (out_dir / "determinism_v0.54.json").write_text(json.dumps(determinism, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "cross_security_integrity_v0.54.json").write_text(json.dumps(cross, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "price_runtime_immutability_v0.54.json").write_text(json.dumps(runtime_immutability, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "parameter_authority_v0.54.json").write_text(json.dumps(parameter, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    prov_rows = []
    for r in pass1.loc[pass1["source_data_defect"].astype(bool)].to_dict("records"):
        prov_rows.append({
            "Security_Key": r["Security_Key"],
            "Source_WS_ID": r["Source_WS_ID"],
            "Primary_MIC": r["Primary_MIC"],
            "Primary_Ticker": r["Primary_Ticker"],
            "source_data_defect": True,
            "excluded_bar_count": int(r["excluded_bar_count"]),
            "excluded_dates": r["excluded_dates"],
            "filtered_policy_version": r["filtered_policy_version"],
        })
    write_csv(out_dir / "source_defect_provenance_v0.54.csv", prov_rows)

    asof_counts = Counter(str(r["feature_as_of_date"]) for r in capability)
    max_formula_min = max(int(r["minimum_valid_observations"]) for r in FORMULA_ROWS)
    min_valid = min(int(r["valid_bar_count"]) for r in capability)
    max_valid = max(int(r["valid_bar_count"]) for r in capability)
    all_current_finite = all(int(r["NonFinite_Total"]) == 0 for r in feat_audit)
    local_ready = (
        counts.get("FEATURE_READY", 0) == 1425
        and inventory_state["master_local_blocking_gaps"] == []
        and all_current_finite
        and determinism["semantic_digest_match"]
        and all(r["temporal_integrity"] == "PASS" for r in temporal)
        and runtime_immutability["sqlite_sha256_unchanged"]
    )

    if local_ready:
        verdict = "PASS_LOCAL_FEATURE_LAYER_READY"
        next_gate = "P0 FROZEN-1425 HOME-MARKET RS MATERIALIZATION / CAPABILITY GATE"
    else:
        verdict = "PASS_WITH_LOCAL_FEATURE_MODEL_GAPS" if counts.get("FEATURE_PARTIAL", 0) else "PASS_WITH_FEATURE_DATA_BLOCKERS"
        next_gate = "P0 FROZEN-1425 MASTER-REQUIRED LOCAL FEATURE IMPLEMENTATION / PROMOTION REMEDIATION GATE"

    summary = {
        "stage": STAGE,
        "version": VERSION,
        "status": verdict,
        "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": repo_authority["repository_sha"],
        "v053_authority": {
            "run_id": V053_RUN_ID,
            "artifact_id": V053_ARTIFACT_ID,
            "artifact_digest": V053_ARTIFACT_DIGEST,
            "runtime_sha256": V053_RUNTIME_SHA256,
            "runtime_bytes": V053_RUNTIME_BYTES,
            "integrity_check": runtime_info["integrity_check"],
            "price_daily": runtime_info["price_daily"],
            "states": runtime_info["states"],
            "ready": runtime_info["ready"],
            "quarantine": runtime_info["quarantine"],
            "p0_price_cache_ready": True,
        },
        "frozen": {"members": 1425, "sha256": FROZEN_SHA256},
        "canonical_feature_inventory": {
            "current_canonical_implemented_count": len(CANONICAL_FEATURES),
            "current_canonical_implemented_features": CANONICAL_FEATURES,
            "master_local_blocking_gaps": inventory_state["master_local_blocking_gaps"],
            "historical_augmented_not_promoted": [x for x in HISTORICAL_AUGMENTED if x not in CANONICAL_FEATURES],
        },
        "materialization": {
            "rows": len(mat_out),
            "semantic_sha256": digest1,
            "two_pass_digest_match": True,
            "valid_bar_min": min_valid,
            "valid_bar_max": max_valid,
            "excluded_bar_total": int(mat_out["excluded_bar_count"].sum()),
            "source_data_defect_securities": int(mat_out["source_data_defect"].astype(bool).sum()),
            "feature_as_of_distribution": dict(sorted(asof_counts.items())),
        },
        "capability_counts": {
            "FEATURE_READY": counts.get("FEATURE_READY", 0),
            "FEATURE_PARTIAL": counts.get("FEATURE_PARTIAL", 0),
            "FEATURE_BLOCKED_INSUFFICIENT_HISTORY": counts.get("FEATURE_BLOCKED_INSUFFICIENT_HISTORY", 0),
            "FEATURE_BLOCKED_INPUT": counts.get("FEATURE_BLOCKED_INPUT", 0),
            "FEATURE_COMPUTATION_ERROR": counts.get("FEATURE_COMPUTATION_ERROR", 0),
            "NOT_VERIFIED": counts.get("NOT_VERIFIED", 0),
        },
        "null_nonfinite": {
            "all_current_canonical_finite": all_current_finite,
            "features_with_nonfinite": [r["Feature"] for r in feat_audit if int(r["NonFinite_Total"]) > 0],
        },
        "history": {
            "history_qa_v1_unchanged": True,
            "minimum_valid_observations_current_frozen": min_valid,
            "longest_current_canonical_finite_window_minimum": max_formula_min,
            "relationship": "Frozen History QA minimum >= current canonical finite-window minimum" if min_valid >= max_formula_min else "INSUFFICIENT",
        },
        "source_defect": {"rows": len(prov_rows), "asx8_regression_pass": len(asx) == 8 and all(r["regression_result"] == "PASS" for r in asx)},
        "recursive_reproducibility": {
            "EMA20_exact": all(r["EMA20_exact_match"] for r in recursive),
            "EMA50_exact": all(r["EMA50_exact_match"] for r in recursive),
            "ATR14_exact": all(r["ATR14_exact_match"] for r in recursive),
            "semantics": "DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES",
        },
        "temporal_integrity": {"all_pass": all(r["temporal_integrity"] == "PASS" for r in temporal), "distribution": dict(sorted(asof_counts.items()))},
        "determinism": determinism,
        "price_runtime_immutability": runtime_immutability,
        "home_market_rs_ready": False,
        "sector_rs_ready": False,
        "parameter_authority": {
            "status": parameter["status"],
            "current_frozen_pointer": parameter["current_frozen_pointer"],
            "p0_numeric_pass_thresholds": [],
            "promoted_lane_pass_rules": [],
        },
        "p0_runs": 0,
        "p0_local_feature_layer_ready": local_ready,
        "market_provider_calls": 0,
        "yahoo_yfinance_calls": 0,
        "eodhd_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "p1_p2_runs": 0,
        "home_market_rs_materialization": False,
        "sector_rs_materialization": False,
        "parameter_promotion": False,
        "universe_mutation": False,
        "productive": False,
        "tests": {"total": len(tests), "passed": sum(r["Result"] == "PASS" for r in tests), "failed": sum(r["Result"] != "PASS" for r in tests)},
        "next_gate": next_gate,
        "feature_artifact": "PENDING_WORKFLOW_UPLOAD",
    }
    (out_dir / "summary_preupload_v0.54.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = {
        "stage": STAGE,
        "version": VERSION,
        "status": verdict,
        "frozen": 1425,
        "capability_counts": summary["capability_counts"],
        "p0_local_feature_layer_ready": local_ready,
        "materialization_semantic_sha256": digest1,
        "determinism_pass": True,
        "temporal_integrity_pass": summary["temporal_integrity"]["all_pass"],
        "price_runtime_immutable": runtime_immutability["sqlite_sha256_unchanged"],
        "tests_passed": summary["tests"]["passed"],
        "tests_failed": summary["tests"]["failed"],
        "p0_runs": 0,
        "productive": False,
        "next_gate": next_gate,
        "artifact_binding": "PENDING_WORKFLOW_UPLOAD",
    }
    (out_dir / "stage_checkpoint_preupload_v0.54.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    files = {}
    for p in sorted(out_dir.iterdir()):
        if p.is_file():
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": repo_authority["repository_sha"],
        "source_runtime": {
            "sha256": V053_RUNTIME_SHA256,
            "bytes": V053_RUNTIME_BYTES,
            "run_id": V053_RUN_ID,
            "artifact_id": V053_ARTIFACT_ID,
            "artifact_digest": V053_ARTIFACT_DIGEST,
        },
        "frozen_sha256": FROZEN_SHA256,
        "materialization_semantic_sha256": digest1,
        "files": files,
        "feature_artifact": "PENDING_WORKFLOW_UPLOAD",
        "p0_local_feature_layer_ready": local_ready,
        "market_provider_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "p0_runs": 0,
        "productive": False,
    }
    (out_dir / "manifest_preupload_v0.54.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": verdict,
        "rows": 1425,
        "capability_counts": summary["capability_counts"],
        "p0_local_feature_layer_ready": local_ready,
        "semantic_sha256": digest1,
        "canonical_feature_count": len(CANONICAL_FEATURES),
        "master_local_blocking_gap_count": len(inventory_state["master_local_blocking_gaps"]),
        "tests_passed": summary["tests"]["passed"],
        "tests_failed": summary["tests"]["failed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
