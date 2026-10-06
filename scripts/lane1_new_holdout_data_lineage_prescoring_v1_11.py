#!/usr/bin/env python3
"""G-P0-12 / v1.11 bounded new independent HOLDOUT data-lineage + pre-scoring builder.

Governance invariants:
- Yahoo/yfinance price data only, bounded to 2026-09-04..2026-10-05.
- v0.53 is read-only; the v1.11 copy is truncated at 2026-09-03 before fetch.
- provider mapping is frozen and compared with v0.53 before the first price call.
- no C07 threshold evaluation, no HIT/FALSE, no forward-outcome calculation.
- forward *availability counts only* are permitted.
- HOLDOUT remains SEALED_NOT_OPENED throughout this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sqlite3
import sys
import time
import zipfile
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from price_cache import (  # noqa: E402
    SOURCE_ID,
    FreeDataConfig,
    SQLitePriceCache,
    YFinanceBatchClient,
    build_yahoo_symbol_map,
    normalize_symbol_frame,
    qa_symbol_frame,
    split_download_frame,
    technical_valid_mask,
)

VERSION = "v1.11"
STAGE = "BREAKOUT_COMPRESSION_VCP_NEW_HOLDOUT_DATA_LINEAGE_PRE_SCORING"
REQUIRED_START_HEAD = "b433af12667cb4843653b1d14127b59054adf7d4"
AUTHORITY_PATH = ROOT / "config/manager_governance_authority_G_P0_12_v1.11.json"
LINEAGE_CONTRACT_PATH = ROOT / "config/lane1_new_holdout_data_lineage_v1.11.json"
PREDECESSOR_AUTHORITY_PATH = ROOT / "config/manager_governance_authority_G_P0_11_v1.10.json"
PREDECESSOR_PROTOCOL_PATH = ROOT / "config/lane1_new_independent_holdout_protocol_v1.10.json"
P0_POINTER_PATH = ROOT / "config/p0_parameter_authority_current.json"
FINALIST_PATH = ROOT / "output_p0_breakout_compression_vcp_finalist_freeze_v1_07/finalist_contract_v1.07.json"
CANDIDATE_SET_PATH = ROOT / "output_p0_breakout_compression_vcp_candidate_set_v1_03/lane1_candidate_set_v1.03.csv"
FROZEN_PATH = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
OVERRIDE_PATH = ROOT / "config/yahoo_symbol_overrides.csv"

DECISION = "NEW_INDEPENDENT_HOLDOUT_DATA_LINEAGE_AND_PRE_SCORING_AUTHORIZED_HOLDOUT_NOT_OPENED"
NEXT_GATE = "BREAKOUT_COMPRESSION_VCP NEW INDEPENDENT HOLDOUT SINGLE-USE EXECUTION AUTHORIZATION"

FRESH_START = date(2026, 9, 4)
HIST_END = date(2026, 9, 3)
CUTOFF = date(2026, 10, 5)
END_EXCLUSIVE = date(2026, 10, 6)

V053_DRIVE_ID = "1lrp_9V0KlWedKYoK7KBNa4zyVqBj1iPg"
V053_ARCHIVE_SHA = "f54f1520e6cfcefbca043bc782ccf71ddd0e70538722ee1c3857551396761e95"
V053_MEMBER = "runtime_cache/p0_frozen_1425_v0_53.sqlite"
V053_SQLITE_SHA = "bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
V053_ARTIFACT_ID = 10900287789
V053_RUN_ID = 36225840648

FROZEN_SHA = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
FROZEN_ROWS = 1425
FINALIST_SHA = "7aabed14feb3ab902223f981619864b24aecc25b51c3d67f4026e4a8e357c201"
CSET_SHA = "8148c0bd2294bece39908d84394dda4fb0835210e83822997df12b9fbd0d6235"

OUTPUT_SQLITE_MEMBER = "runtime_cache/lane1_breakout_vcp_holdout_lineage_v1_11.sqlite"
PACKAGE_NAME = "WELT-SWING_L1_BREAKOUT_VCP_NEW_HOLDOUT_LINEAGE_v1.11_Payload.zip"
DRIVE_FOLDER_ID = "1uSIFSPiF5IzfOwretpp3Gl_jb6K2sZ--"

CONTROL_REQUIRED_PRE_DRIVE = [
    "g_p0_12_authority_binding_v1.11.json",
    "data_lineage_binding_v1.11.json",
    "v053_source_binding_v1.11.json",
    "provider_mapping_audit_v1.11.csv",
    "provider_call_audit_v1.11.json",
    "acquisition_summary_v1.11.json",
    "data_quality_summary_v1.11.json",
    "anchor_population_summary_v1.11.json",
    "anchor_population_manifest_v1.11.csv",
    "pre_drive_state_v1.11.json",
]

CONTROL_REQUIRED_FINAL = [
    "g_p0_12_authority_binding_v1.11.json",
    "data_lineage_binding_v1.11.json",
    "v053_source_binding_v1.11.json",
    "provider_mapping_audit_v1.11.csv",
    "provider_call_audit_v1.11.json",
    "acquisition_summary_v1.11.json",
    "data_quality_summary_v1.11.json",
    "anchor_population_summary_v1.11.json",
    "anchor_population_manifest_v1.11.csv",
    "drive_payload_pointer_v1.11.json",
    "stage_checkpoint_v1.11.json",
    "summary_v1.11.json",
    "test_results_v1.11.csv",
    "manifest_v1.11.json",
]

PACKAGE_MEMBERS = [
    OUTPUT_SQLITE_MEMBER,
    "provider_mapping_manifest_v1.11.csv",
    "acquisition_manifest_v1.11.json",
    "data_quality_summary_v1.11.json",
    "pre_scoring_anchor_eligibility_manifest_v1.11.csv",
    "sha_manifest_v1.11.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames))
        w.writeheader()
        if rows:
            w.writerows(rows)


def sqlite_price_digest(conn: sqlite3.Connection, end_day: str) -> tuple[str, int]:
    cols = (
        "ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,"
        "stock_splits,repaired,source_id,fetched_utc"
    )
    h = hashlib.sha256()
    n = 0
    for row in conn.execute(f"SELECT {cols} FROM price_daily WHERE day<=? ORDER BY ws_id,day", (end_day,)):
        h.update(json.dumps(list(row), ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
        h.update(b"\n")
        n += 1
    return h.hexdigest(), n


def exact_historical_partition_match(target_db: Path, source_db: Path) -> tuple[bool, int, int]:
    cols = (
        "ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,"
        "stock_splits,repaired,source_id,fetched_utc"
    )
    con = sqlite3.connect(target_db)
    try:
        con.execute("ATTACH DATABASE ? AS src", (str(source_db),))
        left = con.execute(
            f"SELECT COUNT(*) FROM (SELECT {cols} FROM main.price_daily WHERE day<=? "
            f"EXCEPT SELECT {cols} FROM src.price_daily WHERE day<=?)",
            (HIST_END.isoformat(), HIST_END.isoformat()),
        ).fetchone()[0]
        right = con.execute(
            f"SELECT COUNT(*) FROM (SELECT {cols} FROM src.price_daily WHERE day<=? "
            f"EXCEPT SELECT {cols} FROM main.price_daily WHERE day<=?)",
            (HIST_END.isoformat(), HIST_END.isoformat()),
        ).fetchone()[0]
        return left == 0 and right == 0, int(left), int(right)
    finally:
        con.close()


def verify_control_bindings(repository_sha: str) -> dict[str, Any]:
    a = read_json(AUTHORITY_PATH)
    if a["Authority_ID"] != "G-P0-12" or a["Authority_Version"] != VERSION:
        raise RuntimeError("G-P0-12 authority identity mismatch")
    if a["Decision"] != DECISION or a["Required_Start_HEAD"] != REQUIRED_START_HEAD:
        raise RuntimeError("G-P0-12 decision/start binding mismatch")
    if a["Data_Lineage_Cutoff"] != CUTOFF.isoformat() or a["Fresh_Data_Start"] != FRESH_START.isoformat():
        raise RuntimeError("prospective date binding mismatch")
    if a["Price_Provider"] != "YFINANCE_FREE":
        raise RuntimeError("provider authority mismatch")
    if a["Provider_Calls_Authorized"] != "YES_BOUNDED_PRICE_DATA_ONLY":
        raise RuntimeError("provider scope not authorized")
    if a["Alpha_Vantage_Authorized"] != "NO":
        raise RuntimeError("Alpha Vantage must remain forbidden")
    for k in [
        "C07_Scoring_Authorized",
        "Forward_Outcome_Generation_Authorized",
        "HOLDOUT_OPENED",
        "HOLDOUT_SCORING_STARTED",
        "HOLDOUT_SINGLE_USE_CONSUMED",
        "PARAMETER_PROMOTION_AUTHORIZED",
        "P0_RUN_AUTHORIZED",
        "LANE2_AUTHORIZED",
    ]:
        if a[k] != "NO":
            raise RuntimeError(f"forbidden authority flag changed: {k}")

    pred = read_json(PREDECESSOR_AUTHORITY_PATH)
    if pred["Authority_ID"] != "G-P0-11" or pred["Authority_Version"] != "v1.10":
        raise RuntimeError("G-P0-11 predecessor identity mismatch")
    if pred["Decision"] != "NEW_INDEPENDENT_HOLDOUT_PROTOCOL_AUTHORIZED_EXECUTION_NOT_STARTED":
        raise RuntimeError("G-P0-11 predecessor decision mismatch")
    if pred["New_Holdout_State"] != "SEALED_NOT_OPENED":
        raise RuntimeError("new HOLDOUT not sealed at predecessor")
    if any(pred[k] != "NO" for k in ["HOLDOUT_OPENED", "HOLDOUT_SCORING_STARTED", "HOLDOUT_SINGLE_USE_CONSUMED"]):
        raise RuntimeError("predecessor HOLDOUT state mismatch")

    protocol = read_json(PREDECESSOR_PROTOCOL_PATH)
    if protocol["Protocol_ID"] != "L1_BREAKOUT_VCP_NEW_INDEPENDENT_HOLDOUT_PROTOCOL":
        raise RuntimeError("v1.10 protocol ID mismatch")
    if protocol["Protocol_Version"] != "v1.10":
        raise RuntimeError("v1.10 protocol version mismatch")
    if protocol["Single_Use_State_Machine"]["Initial_State"] != "SEALED_NOT_OPENED":
        raise RuntimeError("v1.10 state machine mismatch")
    if protocol["Independence"]["Anchor_Date_Rule"] != "Anchor_Date > 2026-09-03":
        raise RuntimeError("v1.10 anchor boundary mismatch")

    p0 = read_json(P0_POINTER_PATH)
    if not (
        p0["Authority_ID"] == "G-P0-01"
        and p0["Version"] == "v0.99"
        and p0["P0_RUN_AUTHORIZED"] == "NO"
        and p0["AUTOMATED_P0_READY"] == "NO"
        and p0["p0_numeric_pass_thresholds"] == []
        and p0["promoted_lane_pass_rules"] == []
    ):
        raise RuntimeError("P0 pointer changed")

    finalist = read_json(FINALIST_PATH)
    if canonical_sha(finalist) != FINALIST_SHA:
        raise RuntimeError("finalist semantic SHA mismatch")
    if finalist["Candidate_ID"] != "L1-C07-PIVOT_PROXIMITY_STRICT":
        raise RuntimeError("finalist ID mismatch")
    if finalist["Candidate_Set_Semantic_SHA256"] != CSET_SHA:
        raise RuntimeError("candidate-set binding mismatch")
    if float(finalist["Pivot_Proximity_Cutoff_ATR"]) != 0.75:
        raise RuntimeError("frozen finalist contract changed")
    if sha_file(CANDIDATE_SET_PATH) != CSET_SHA:
        raise RuntimeError("candidate-set file SHA mismatch")

    contract = read_json(LINEAGE_CONTRACT_PATH)
    if contract["Lineage_ID"] != "L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11":
        raise RuntimeError("lineage contract ID mismatch")
    if contract["Date_Boundary"]["Data_Lineage_Cutoff"] != CUTOFF.isoformat():
        raise RuntimeError("lineage cutoff mismatch")
    if contract["Date_Boundary"]["Fresh_Data_Start"] != FRESH_START.isoformat():
        raise RuntimeError("lineage fresh-start mismatch")
    if contract["Provider"]["Source_ID"] != "YFINANCE_FREE" or contract["Provider"]["Version"] != "1.6.0":
        raise RuntimeError("lineage provider mismatch")
    if contract["Mapping_Policy"]["reset_changed_symbols"] != "PROHIBITED":
        raise RuntimeError("mapping reset must be prohibited")
    if contract["Holdout_State"] != "SEALED_NOT_OPENED":
        raise RuntimeError("lineage HOLDOUT state mismatch")
    if contract["C07_Scoring_Authorized"] != "NO" or contract["Forward_Outcome_Generation_Authorized"] != "NO":
        raise RuntimeError("scoring/outcomes unexpectedly authorized")

    return {
        "repository_sha": repository_sha,
        "authority_sha256": sha_file(AUTHORITY_PATH),
        "lineage_contract_sha256": sha_file(LINEAGE_CONTRACT_PATH),
        "predecessor_authority_sha256": sha_file(PREDECESSOR_AUTHORITY_PATH),
        "predecessor_protocol_sha256": sha_file(PREDECESSOR_PROTOCOL_PATH),
        "p0_pointer_sha256": sha_file(P0_POINTER_PATH),
        "finalist_semantic_sha256": FINALIST_SHA,
        "candidate_set_sha256": CSET_SHA,
        "price_cache_sha256": sha_file(ROOT / "scripts/price_cache.py"),
        "requirements_sha256": sha_file(ROOT / "requirements.txt"),
    }


def verify_frozen_universe() -> pd.DataFrame:
    if sha_file(FROZEN_PATH) != FROZEN_SHA:
        raise RuntimeError("Frozen-1425 SHA mismatch")
    uni = pd.read_csv(FROZEN_PATH, dtype=str)
    if len(uni) != FROZEN_ROWS:
        raise RuntimeError(f"Frozen-1425 row mismatch: {len(uni)}")
    if uni["WS_ID"].astype(str).duplicated().any():
        raise RuntimeError("duplicate WS_ID in Frozen-1425")
    return uni


def extract_and_verify_v053(source_zip: Path, work_dir: Path) -> Path:
    if sha_file(source_zip) != V053_ARCHIVE_SHA:
        raise RuntimeError("v0.53 archive SHA mismatch")
    source_db = work_dir / "v053_source.sqlite"
    if source_db.exists():
        source_db.unlink()
    with zipfile.ZipFile(source_zip) as z:
        if V053_MEMBER not in z.namelist():
            raise RuntimeError("v0.53 SQLite member missing")
        with z.open(V053_MEMBER) as src, source_db.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    if sha_file(source_db) != V053_SQLITE_SHA:
        raise RuntimeError("v0.53 SQLite SHA mismatch")
    con = sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        needed = {"price_daily", "cache_state", "batch_log", "cache_qa_provenance_v053", "technical_bar_exclusions_v053"}
        if not needed.issubset(tables):
            raise RuntimeError(f"v0.53 schema missing: {sorted(needed - tables)}")
        n_state = int(con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        if n_state != FROZEN_ROWS:
            raise RuntimeError("v0.53 cache_state row mismatch")
    finally:
        con.close()
    return source_db


def freeze_mapping(uni: pd.DataFrame, source_db: Path, output_dir: Path, package_dir: Path) -> dict[str, Any]:
    mapping = build_yahoo_symbol_map(uni, override_path=OVERRIDE_PATH)
    mapping = mapping.sort_values("WS_ID").reset_index(drop=True)

    con = sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
    hist = pd.read_sql_query(
        "SELECT ws_id AS WS_ID, yahoo_symbol AS Historical_Yahoo_Symbol, "
        "mapping_status AS Historical_Mapping_Status FROM cache_state ORDER BY ws_id",
        con,
    )
    con.close()
    hist["WS_ID"] = hist["WS_ID"].astype(str)

    m = mapping.merge(hist, on="WS_ID", how="left", validate="one_to_one")
    rows: list[dict[str, Any]] = []
    mismatch_ids: list[str] = []
    for _, r in m.iterrows():
        old = "" if pd.isna(r["Historical_Yahoo_Symbol"]) else str(r["Historical_Yahoo_Symbol"]).strip()
        new = "" if pd.isna(r["Yahoo_Symbol"]) else str(r["Yahoo_Symbol"]).strip()
        match = old == new
        if not match:
            mismatch_ids.append(str(r["WS_ID"]))
        rows.append({
            "WS_ID": str(r["WS_ID"]),
            "Primary_Ticker": str(r["Primary_Ticker"]),
            "Primary_MIC": str(r["Primary_MIC"]),
            "Historical_Yahoo_Symbol": old,
            "Current_Yahoo_Symbol": new,
            "Historical_Mapping_Status": "" if pd.isna(r["Historical_Mapping_Status"]) else str(r["Historical_Mapping_Status"]),
            "Current_Mapping_Status": str(r["Yahoo_Mapping_Status"]),
            "Mapping_Match": "YES" if match else "NO",
            "Fetch_Authorized": "YES" if match and bool(new) else "NO",
        })

    audit_path = output_dir / "provider_mapping_audit_v1.11.csv"
    fields = [
        "WS_ID", "Primary_Ticker", "Primary_MIC", "Historical_Yahoo_Symbol", "Current_Yahoo_Symbol",
        "Historical_Mapping_Status", "Current_Mapping_Status", "Mapping_Match", "Fetch_Authorized",
    ]
    write_csv(audit_path, rows, fields)
    package_mapping = package_dir / "provider_mapping_manifest_v1.11.csv"
    shutil.copyfile(audit_path, package_mapping)

    mapped_count = sum(bool(r["Current_Yahoo_Symbol"]) and r["Mapping_Match"] == "YES" for r in rows)
    unmapped_count = len(rows) - mapped_count
    result = {
        "rows": len(rows),
        "mapped_count": mapped_count,
        "unmapped_count": unmapped_count,
        "unexpected_symbol_change_count": len(mismatch_ids),
        "unexpected_symbol_change_ws_ids": mismatch_ids,
        "mapping_sha256": sha_file(audit_path),
        "override_file_present": OVERRIDE_PATH.exists(),
        "override_file_sha256": sha_file(OVERRIDE_PATH) if OVERRIDE_PATH.exists() else None,
        "mapping_frozen_before_fetch": "YES",
    }
    if mismatch_ids:
        raise RuntimeError(f"unexpected provider-symbol change for {len(mismatch_ids)} WS_ID(s)")
    if mapped_count != FROZEN_ROWS:
        raise RuntimeError(f"provider mapping incomplete before fetch: mapped={mapped_count}")
    return result


def initialize_target(source_db: Path, target_db: Path) -> dict[str, Any]:
    target_db.parent.mkdir(parents=True, exist_ok=True)
    if target_db.exists():
        target_db.unlink()
    source_sha_before = sha_file(source_db)
    shutil.copy2(source_db, target_db)
    con = sqlite3.connect(target_db)
    try:
        before_total = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        post_boundary = int(con.execute("SELECT COUNT(*) FROM price_daily WHERE day>?", (HIST_END.isoformat(),)).fetchone()[0])
        con.execute("DELETE FROM price_daily WHERE day>?", (HIST_END.isoformat(),))
        con.execute("""
            CREATE TABLE IF NOT EXISTS lineage_metadata_v111 (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS technical_bar_exclusions_v111 (
                ws_id TEXT NOT NULL,
                day TEXT NOT NULL,
                technical_bar_excluded INTEGER NOT NULL,
                reason_codes TEXT NOT NULL,
                PRIMARY KEY (ws_id, day)
            )
        """)
        meta = {
            "Authority": "G-P0-12 / v1.11",
            "Lineage_ID": "L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11",
            "Historical_Immutability_End": HIST_END.isoformat(),
            "Fresh_Data_Start": FRESH_START.isoformat(),
            "Data_Lineage_Cutoff": CUTOFF.isoformat(),
            "Provider": "YFINANCE_FREE",
            "HOLDOUT_State": "SEALED_NOT_OPENED",
        }
        for k, v in meta.items():
            con.execute("INSERT OR REPLACE INTO lineage_metadata_v111(key,value) VALUES (?,?)", (k, v))
        con.commit()
        after_total = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        max_day = con.execute("SELECT MAX(day) FROM price_daily").fetchone()[0]
    finally:
        con.close()
    if sha_file(source_db) != source_sha_before:
        raise RuntimeError("source v0.53 mutated during copy")
    if max_day and max_day > HIST_END.isoformat():
        raise RuntimeError("target foundation truncation failed")
    return {
        "source_sqlite_sha_before": source_sha_before,
        "source_sqlite_sha_after_copy": sha_file(source_db),
        "source_total_price_rows": before_total,
        "source_rows_after_2026_09_03_not_carried_forward": post_boundary,
        "target_historical_price_rows": after_total,
        "target_max_day_before_fetch": max_day,
    }


def preflight(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    package_dir = Path(args.package_dir)
    work_dir = Path(args.work_dir)
    for p in [output_dir, package_dir, work_dir]:
        p.mkdir(parents=True, exist_ok=True)

    target_db = package_dir / OUTPUT_SQLITE_MEMBER
    try:
        bindings = verify_control_bindings(args.repository_sha)
        uni = verify_frozen_universe()
        source_db = extract_and_verify_v053(Path(args.source_zip), work_dir)

        src = sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
        try:
            hist_digest, hist_rows = sqlite_price_digest(src, HIST_END.isoformat())
            source_min, source_max, source_total = src.execute(
                "SELECT MIN(day),MAX(day),COUNT(*) FROM price_daily"
            ).fetchone()
        finally:
            src.close()

        mapping = freeze_mapping(uni, source_db, output_dir, package_dir)
        init = initialize_target(source_db, target_db)

        state = {
            "phase": "PREFLIGHT_PASS",
            "version": VERSION,
            "repository_sha": args.repository_sha,
            "required_start_head": REQUIRED_START_HEAD,
            "bindings": bindings,
            "v053": {
                "canonical_drive_file_id": V053_DRIVE_ID,
                "runner_restore_artifact_id": V053_ARTIFACT_ID,
                "runner_restore_run_id": V053_RUN_ID,
                "archive_sha256": V053_ARCHIVE_SHA,
                "sqlite_sha256": V053_SQLITE_SHA,
                "source_min_date": source_min,
                "source_max_date": source_max,
                "source_total_price_rows": int(source_total),
                "historical_partition_end": HIST_END.isoformat(),
                "historical_partition_rows": hist_rows,
                "historical_partition_digest": hist_digest,
                **init,
            },
            "frozen_universe": {"rows": len(uni), "sha256": sha_file(FROZEN_PATH)},
            "mapping": mapping,
            "provider_calls": 0,
            "alpha_vantage_calls": 0,
            "new_holdout_state": "SEALED_NOT_OPENED",
            "holdout_opened": "NO",
            "holdout_scoring_started": "NO",
            "holdout_single_use_consumed": "NO",
            "c07_scoring": "NOT_AUTHORIZED",
            "forward_outcomes": "NOT_AUTHORIZED",
        }
        write_json(output_dir / "preflight_state_v1.11.json", state)
        write_json(work_dir / "preflight_state_v1.11.json", state)
        source_path_record = work_dir / "source_db_path.txt"
        source_path_record.write_text(str(source_db.resolve()) + "\n", encoding="utf-8")
        print(json.dumps({
            "phase": "PREFLIGHT_PASS",
            "mapping_sha256": mapping["mapping_sha256"],
            "historical_rows": hist_rows,
            "source_max_date": source_max,
            "post_boundary_rows_removed_from_copy": init["source_rows_after_2026_09_03_not_carried_forward"],
            "provider_calls": 0,
        }, indent=2))
    except Exception:
        if target_db.exists():
            target_db.unlink()
        raise


def chunks(seq: Sequence[Any], n: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), n):
        yield list(seq[i:i+n])


def rows_for_db(ws_id: str, symbol: str, frame: pd.DataFrame, fetched_utc: str) -> list[tuple[Any, ...]]:
    x = normalize_symbol_frame(frame)
    x = x.loc[
        (x.index.date >= FRESH_START) & (x.index.date <= CUTOFF)
    ].copy()
    rows: list[tuple[Any, ...]] = []
    for ts, r in x.iterrows():
        def val(c: str) -> Any:
            v = r[c]
            if pd.isna(v):
                return None
            return float(v)
        rows.append((
            ws_id, symbol, ts.date().isoformat(),
            val("open"), val("high"), val("low"), val("close"), val("adj_close"),
            val("volume"), val("dividends"), val("stock_splits"),
            int(bool(val("repaired") or 0)), SOURCE_ID, fetched_utc,
        ))
    return rows


def download_with_retry(
    client: YFinanceBatchClient,
    symbols: Sequence[str],
    *,
    repair: bool,
    phase: str,
    call_log: list[dict[str, Any]],
) -> tuple[pd.DataFrame | None, str | None]:
    cfg = client.config
    last_error: str | None = None
    for attempt in range(1 + cfg.max_identical_retries):
        started = utc_now()
        try:
            raw = client.download(
                symbols,
                start=FRESH_START,
                end=END_EXCLUSIVE,
                repair=repair,
            )
            call_log.append({
                "call_index": len(call_log) + 1,
                "provider": "YFINANCE_FREE",
                "phase": phase,
                "attempt": attempt + 1,
                "repair": bool(repair),
                "symbol_count": len(symbols),
                "request_start": FRESH_START.isoformat(),
                "request_end_exclusive": END_EXCLUSIVE.isoformat(),
                "persisted_cutoff": CUTOFF.isoformat(),
                "started_utc": started,
                "finished_utc": utc_now(),
                "status": "SUCCESS",
                "error": None,
            })
            return raw, None
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            call_log.append({
                "call_index": len(call_log) + 1,
                "provider": "YFINANCE_FREE",
                "phase": phase,
                "attempt": attempt + 1,
                "repair": bool(repair),
                "symbol_count": len(symbols),
                "request_start": FRESH_START.isoformat(),
                "request_end_exclusive": END_EXCLUSIVE.isoformat(),
                "persisted_cutoff": CUTOFF.isoformat(),
                "started_utc": started,
                "finished_utc": utc_now(),
                "status": "ERROR",
                "error": last_error,
            })
            if attempt < cfg.max_identical_retries:
                time.sleep(cfg.retry_sleep_seconds)
    return None, last_error


def process_fetch_batch(
    cache: SQLitePriceCache,
    client: YFinanceBatchClient,
    batch: pd.DataFrame,
    *,
    repair: bool,
    phase: str,
    call_log: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    symbols = [str(x) for x in batch["Current_Yahoo_Symbol"].tolist()]
    raw, error = download_with_retry(client, symbols, repair=repair, phase=phase, call_log=call_log)
    batch_id = f"V111-{phase}-{len(call_log):04d}-{hashlib.sha256('|'.join(symbols).encode()).hexdigest()[:10]}"
    started = call_log[-1]["started_utc"] if call_log else utc_now()
    finished = utc_now()

    if raw is None:
        cache.log_batch({
            "batch_id": batch_id,
            "source_id": SOURCE_ID,
            "started_utc": started,
            "finished_utc": finished,
            "symbol_count": len(symbols),
            "received_count": 0,
            "missing_count": len(symbols),
            "retry_count": int(client.config.max_identical_retries),
            "repair_pass": int(repair),
            "status": "FAILED",
            "error_text": error,
        })
        cache.conn.commit()
        return [], symbols

    frames = split_download_frame(raw, symbols)
    received: list[str] = []
    missing: list[str] = []
    all_rows: list[tuple[Any, ...]] = []
    fetched = utc_now()
    for _, r in batch.iterrows():
        ws = str(r["WS_ID"])
        sym = str(r["Current_Yahoo_Symbol"])
        frame = frames.get(sym)
        if frame is None or frame.empty:
            missing.append(sym)
            continue
        x = normalize_symbol_frame(frame)
        x = x.loc[(x.index.date >= FRESH_START) & (x.index.date <= CUTOFF)].copy()
        if x.empty:
            missing.append(sym)
            continue
        all_rows.extend(rows_for_db(ws, sym, x, fetched))
        received.append(sym)

    cache.upsert_price_rows(all_rows)
    cache.log_batch({
        "batch_id": batch_id,
        "source_id": SOURCE_ID,
        "started_utc": started,
        "finished_utc": finished,
        "symbol_count": len(symbols),
        "received_count": len(received),
        "missing_count": len(missing),
        "retry_count": sum(1 for x in call_log if x["phase"] == phase and x["status"] == "ERROR"),
        "repair_pass": int(repair),
        "status": "SUCCESS" if not missing else "PARTIAL",
        "error_text": None,
    })
    cache.conn.commit()
    return received, missing


def update_state_and_new_bar_exclusions(
    cache: SQLitePriceCache,
    mapping: pd.DataFrame,
    cfg: FreeDataConfig,
) -> tuple[dict[str, int], int]:
    status_counts: dict[str, int] = {}
    invalid_new = 0
    cache.conn.execute("DELETE FROM technical_bar_exclusions_v111")
    states: list[dict[str, Any]] = []
    for _, r in mapping.iterrows():
        ws = str(r["WS_ID"])
        sym = str(r["Current_Yahoo_Symbol"])
        full = cache.load_price_frame(ws)
        qa = qa_symbol_frame(full, config=cfg, as_of=CUTOFF)
        status_counts[qa["status"]] = status_counts.get(qa["status"], 0) + 1
        states.append({
            "ws_id": ws,
            "yahoo_symbol": sym,
            "mapping_status": str(r["Current_Mapping_Status"]),
            "status": qa["status"],
            "reason_code": qa["reason_code"],
            "unique_bars": qa["unique_bars"],
            "valid_bars": qa["valid_bars"],
            "repaired_rows": qa["repaired_rows"],
            "suspicious_returns": qa["suspicious_returns"],
            "zero_volume_share": qa["zero_volume_share"],
            "first_bar_date": qa["first_bar_date"],
            "last_bar_date": qa["last_bar_date"],
            "last_fetch_utc": utc_now(),
            "batch_id": "V111-FINAL-QA",
            "last_error": None,
        })
        if not full.empty:
            fresh = full.loc[
                (full.index.date >= FRESH_START) & (full.index.date <= CUTOFF)
            ].copy()
            if not fresh.empty:
                vm = technical_valid_mask(fresh)
                for ts, ok in vm.items():
                    if not bool(ok):
                        invalid_new += 1
                        cache.conn.execute(
                            "INSERT OR REPLACE INTO technical_bar_exclusions_v111"
                            "(ws_id,day,technical_bar_excluded,reason_codes) VALUES (?,?,?,?)",
                            (ws, ts.date().isoformat(), 1, "TECHNICAL_VALID_MASK_FALSE"),
                        )
    cache.upsert_states(states)
    cache.conn.commit()
    return status_counts, invalid_new


def primitive_readiness_for_valid_series(xv: pd.DataFrame) -> pd.Series:
    xv = xv.copy()
    o = pd.to_numeric(xv["open"], errors="coerce")
    h = pd.to_numeric(xv["high"], errors="coerce")
    l = pd.to_numeric(xv["low"], errors="coerce")
    c = pd.to_numeric(xv["close"], errors="coerce")
    v = pd.to_numeric(xv["volume"], errors="coerce")

    prev = c.shift(1)
    tr = pd.concat([(h-l).abs(), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    ema50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
    sma200 = c.rolling(200, min_periods=200).mean()
    ema50s = ema50 / ema50.shift(10) - 1

    hi5 = h.rolling(5, min_periods=5).max()
    lo5 = l.rolling(5, min_periods=5).min()
    hi10 = h.rolling(10, min_periods=10).max()
    lo10 = l.rolling(10, min_periods=10).min()
    hi20 = h.rolling(20, min_periods=20).max()
    lo20 = l.rolling(20, min_periods=20).min()
    range5 = (hi5-lo5) / c
    range10 = (hi10-lo10) / c
    range20 = (hi20-lo20) / c
    r20 = c / c.shift(20) - 1
    r60 = c / c.shift(60) - 1

    vol_finite = pd.Series(np.isfinite(v.to_numpy(dtype=float, na_value=np.nan)), index=v.index)
    prior_vol = v.shift(1)
    prior20_count = vol_finite.shift(1, fill_value=False).astype(int).rolling(20, min_periods=20).sum()
    prior20_median = prior_vol.rolling(20, min_periods=20).median()
    rvol = (v / prior20_median).where(
        (prior20_count == 20) & vol_finite & np.isfinite(prior20_median) & (prior20_median != 0)
    )

    daily_move = ((c-prev) / atr.shift(1)).where(atr.shift(1) != 0)
    ph = h.shift(1).rolling(20, min_periods=20).max()
    pivot_distance = ((c-ph).abs() / atr).where(atr != 0)
    pivot_extension = ((c-ph) / atr).where(atr != 0)
    close_location = ((c-l) / (h-l)).where(h != l)

    base_hi30 = h.shift(1).rolling(30, min_periods=30).max()
    base_lo30 = l.shift(1).rolling(30, min_periods=30).min()
    base_width30 = (1 - base_lo30 / base_hi30).where(base_hi30 != 0)
    base_prior_sma_ready = sma200.shift(1).notna().astype(int).rolling(30, min_periods=30).sum().eq(30)

    trend_inputs_ready = pd.DataFrame({
        "close": c,
        "sma200": sma200,
        "ema50": ema50,
        "ema50s": ema50s,
    }).replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    stage3_input_ready = trend_inputs_ready.astype(int).rolling(3, min_periods=3).sum().eq(3)

    vals = pd.DataFrame({
        "c": c,
        "h": h,
        "l": l,
        "atr": atr,
        "sma200": sma200,
        "ema50": ema50,
        "ema50s": ema50s,
        "range5": range5,
        "range10": range10,
        "range20": range20,
        "r20": r20,
        "r60": r60,
        "rvol": rvol,
        "daily_move": daily_move,
        "ph": ph,
        "pivot_distance": pivot_distance,
        "pivot_extension": pivot_extension,
        "close_location": close_location,
        "base_hi30": base_hi30,
        "base_lo30": base_lo30,
        "base_width30": base_width30,
    }).replace([np.inf, -np.inf], np.nan)

    scalar_ready = vals.notna().all(axis=1)
    return scalar_ready & base_prior_sma_ready & stage3_input_ready


def build_anchor_population(db_path: Path, output_dir: Path, package_dir: Path) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    all_rows: list[dict[str, Any]] = []
    per_ws_counts: dict[str, int] = {}
    ids = [r[0] for r in con.execute("SELECT ws_id FROM cache_state ORDER BY ws_id").fetchall()]
    for ws in ids:
        df = pd.read_sql_query(
            "SELECT day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired "
            "FROM price_daily WHERE ws_id=? ORDER BY day",
            con,
            params=[ws],
        )
        if df.empty:
            continue
        df["day"] = pd.to_datetime(df["day"], errors="coerce")
        df = df.dropna(subset=["day"]).set_index("day")
        valid_mask = technical_valid_mask(df)
        valid_dates = df.index[valid_mask].sort_values()
        xv = df.loc[valid_dates].copy()
        readiness = primitive_readiness_for_valid_series(xv) if not xv.empty else pd.Series(dtype=bool)

        valid_ns = valid_dates.values.astype("datetime64[ns]")
        fresh = df.loc[
            (df.index.date >= FRESH_START) & (df.index.date <= CUTOFF)
        ].copy()
        per_ws_counts[ws] = len(fresh)
        for day_ts, _ in fresh.iterrows():
            day64 = np.datetime64(day_ts.to_datetime64(), "ns")
            right = int(np.searchsorted(valid_ns, day64, side="right"))
            left = int(np.searchsorted(valid_ns, day64, side="left"))
            is_valid = left < len(valid_ns) and valid_ns[left] == day64
            history_count = right
            future_count = len(valid_ns) - right
            ready = bool(readiness.get(day_ts, False)) if is_valid else False
            complete5 = future_count >= 5
            complete10 = future_count >= 10
            complete15 = future_count >= 15
            eligible = (
                day_ts.date() > HIST_END
                and is_valid
                and history_count >= 252
                and ready
                and complete15
            )
            if eligible:
                reason = ""
            elif day_ts.date() <= HIST_END:
                reason = "ANCHOR_DATE_NOT_POST_BOUNDARY"
            elif not is_valid:
                reason = "TECHNICAL_ANCHOR_INVALID"
            elif history_count < 252:
                reason = "INSUFFICIENT_VALID_HISTORY"
            elif not ready:
                reason = "REQUIRED_INPUT_NOT_AVAILABLE"
            else:
                reason = "INCOMPLETE_15_VALID_SESSION_FORWARD_WINDOW"

            all_rows.append({
                "WS_ID": ws,
                "Anchor_Date": day_ts.date().isoformat(),
                "technical_anchor_valid": "YES" if is_valid else "NO",
                "valid_history_count_through_t": history_count,
                "required_history_ready": "YES" if history_count >= 252 else "NO",
                "required_input_availability": "FINITE" if ready else "NOT_VERIFIED_INPUT",
                "future_valid_sessions_available": future_count,
                "complete_5_session_window": "YES" if complete5 else "NO",
                "complete_10_session_window": "YES" if complete10 else "NO",
                "complete_15_session_window": "YES" if complete15 else "NO",
                "anchor_eligible": "YES" if eligible else "NO",
                "exclusion_reason": reason,
            })
    con.close()

    fields = [
        "WS_ID", "Anchor_Date", "technical_anchor_valid", "valid_history_count_through_t",
        "required_history_ready", "required_input_availability", "future_valid_sessions_available",
        "complete_5_session_window", "complete_10_session_window", "complete_15_session_window",
        "anchor_eligible", "exclusion_reason",
    ]
    path = output_dir / "anchor_population_manifest_v1.11.csv"
    write_csv(path, all_rows, fields)
    package_path = package_dir / "pre_scoring_anchor_eligibility_manifest_v1.11.csv"
    shutil.copyfile(path, package_path)

    eligible = sum(r["anchor_eligible"] == "YES" for r in all_rows)
    by_reason: dict[str, int] = {}
    for r in all_rows:
        key = r["exclusion_reason"] or "ELIGIBLE"
        by_reason[key] = by_reason.get(key, 0) + 1
    date_min = min((r["Anchor_Date"] for r in all_rows), default=None)
    date_max = max((r["Anchor_Date"] for r in all_rows), default=None)
    return {
        "Anchor_Population_Rows": len(all_rows),
        "Anchor_Eligible_Rows": eligible,
        "Anchor_Date_Min": date_min,
        "Anchor_Date_Max": date_max,
        "Exclusion_Reason_Counts": by_reason,
        "Manifest_SHA256": sha_file(path),
        "Manifest_Columns": fields,
        "C07_Columns_Present": [],
        "Forward_Outcome_Columns_Present": [],
        "Forward_Availability_Only": "YES",
    }


def finalize_sqlite_file(db_path: Path) -> str:
    con = sqlite3.connect(db_path)
    try:
        con.commit()
        try:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass
        con.execute("PRAGMA journal_mode=DELETE")
        con.execute("VACUUM")
        con.commit()
    finally:
        con.close()
    for suffix in ["-wal", "-shm"]:
        p = Path(str(db_path) + suffix)
        if p.exists():
            p.unlink()
    return sha_file(db_path)


def acquire(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    package_dir = Path(args.package_dir)
    work_dir = Path(args.work_dir)
    state = read_json(work_dir / "preflight_state_v1.11.json")
    if state["phase"] != "PREFLIGHT_PASS" or state["provider_calls"] != 0:
        raise RuntimeError("preflight state invalid")
    source_db = Path((work_dir / "source_db_path.txt").read_text(encoding="utf-8").strip())
    if sha_file(source_db) != V053_SQLITE_SHA:
        raise RuntimeError("v0.53 source changed before fetch")

    target_db = package_dir / OUTPUT_SQLITE_MEMBER
    if not target_db.exists():
        raise RuntimeError("target lineage copy missing")

    mapping = pd.read_csv(output_dir / "provider_mapping_audit_v1.11.csv", dtype=str).fillna("")
    if not (mapping["Mapping_Match"] == "YES").all():
        raise RuntimeError("mapping mismatch before first price call")
    if not (mapping["Fetch_Authorized"] == "YES").all():
        raise RuntimeError("not all Frozen-1425 IDs are fetch-authorized")

    cfg = FreeDataConfig(
        batch_size=100,
        max_identical_retries=1,
        repair_anomalies=True,
        repair_batch_size=25,
    )
    cfg.validate()
    client = YFinanceBatchClient(config=cfg)
    cache = SQLitePriceCache(target_db)
    call_log: list[dict[str, Any]] = []
    missing_primary: list[str] = []
    try:
        for idxs in chunks(list(mapping.index), cfg.batch_size):
            batch = mapping.loc[idxs]
            _, missing = process_fetch_batch(
                cache, client, batch, repair=False, phase="PRIMARY", call_log=call_log
            )
            missing_primary.extend(missing)

        missing_after_rescue: list[str] = []
        if missing_primary:
            rescue_rows = mapping[mapping["Current_Yahoo_Symbol"].isin(sorted(set(missing_primary)))]
            for idxs in chunks(list(rescue_rows.index), cfg.batch_size):
                batch = rescue_rows.loc[idxs]
                _, missing = process_fetch_batch(
                    cache, client, batch, repair=False, phase="RESCUE", call_log=call_log
                )
                missing_after_rescue.extend(missing)

        # Determine targeted repair candidates using the established QA contract.
        repair_symbols: list[str] = []
        for _, r in mapping.iterrows():
            ws = str(r["WS_ID"])
            full = cache.load_price_frame(ws)
            qa = qa_symbol_frame(full, config=cfg, as_of=CUTOFF)
            if qa["reason_code"] in {"SUSPICIOUS_RETURN_NEEDS_REPAIR", "INVALID_OHLC_OR_VOLUME"}:
                repair_symbols.append(str(r["Current_Yahoo_Symbol"]))

        if repair_symbols:
            repair_rows = mapping[mapping["Current_Yahoo_Symbol"].isin(sorted(set(repair_symbols)))]
            for idxs in chunks(list(repair_rows.index), cfg.repair_batch_size):
                batch = repair_rows.loc[idxs]
                process_fetch_batch(
                    cache, client, batch, repair=True, phase="REPAIR", call_log=call_log
                )

        status_counts, invalid_new = update_state_and_new_bar_exclusions(cache, mapping, cfg)
    finally:
        cache.close()

    sqlite_sha = finalize_sqlite_file(target_db)

    # Absolute date and historical immutability checks.
    con = sqlite3.connect(target_db)
    try:
        earliest, latest, total_rows = con.execute(
            "SELECT MIN(day),MAX(day),COUNT(*) FROM price_daily"
        ).fetchone()
        historical_rows = int(con.execute(
            "SELECT COUNT(*) FROM price_daily WHERE day<=?", (HIST_END.isoformat(),)
        ).fetchone()[0])
        fresh_rows = int(con.execute(
            "SELECT COUNT(*) FROM price_daily WHERE day>? AND day<=?",
            (HIST_END.isoformat(), CUTOFF.isoformat()),
        ).fetchone()[0])
        after_cutoff = int(con.execute(
            "SELECT COUNT(*) FROM price_daily WHERE day>?", (CUTOFF.isoformat(),)
        ).fetchone()[0])
        duplicates = int(con.execute(
            "SELECT COUNT(*) FROM (SELECT ws_id,day,COUNT(*) c FROM price_daily GROUP BY ws_id,day HAVING c>1)"
        ).fetchone()[0])
        fresh_min, fresh_max = con.execute(
            "SELECT MIN(day),MAX(day) FROM price_daily WHERE day>? AND day<=?",
            (HIST_END.isoformat(), CUTOFF.isoformat()),
        ).fetchone()
        historical_digest_after, historical_digest_rows = sqlite_price_digest(con, HIST_END.isoformat())
    finally:
        con.close()

    hist_match, target_minus_source, source_minus_target = exact_historical_partition_match(target_db, source_db)
    source_sha_after = sha_file(source_db)

    anchor_summary = build_anchor_population(target_db, output_dir, package_dir)
    write_json(output_dir / "anchor_population_summary_v1.11.json", anchor_summary)

    provider_audit = {
        "Provider": "YFINANCE_FREE",
        "Provider_Implementation": "scripts/price_cache.py::YFinanceBatchClient",
        "Dependency": "yfinance==1.6.0",
        "Authorized_Scope": "BOUNDED_DAILY_OHLCV_ACTIONS_ONLY",
        "Request_Start": FRESH_START.isoformat(),
        "Request_End_Exclusive": END_EXCLUSIVE.isoformat(),
        "Persisted_Cutoff": CUTOFF.isoformat(),
        "Provider_Calls": len(call_log),
        "Primary_Missing_Symbols": len(set(missing_primary)),
        "Missing_After_Bounded_Rescue": len(set(missing_after_rescue)),
        "Repair_Candidate_Symbols": len(set(repair_symbols)),
        "Calls": call_log,
        "Alpha_Vantage_Calls": 0,
        "EODHD_Calls": 0,
        "Scalable_Calls": 0,
        "TradingView_Calls": 0,
        "News_Calls": 0,
        "Fundamental_Calls": 0,
        "Web_Search_Calls": 0,
        "Per_Security_Fanout_Architecture": "NO",
    }
    write_json(output_dir / "provider_call_audit_v1.11.json", provider_audit)

    qa_blocked = sum(v for k, v in status_counts.items() if k != "READY")
    data_quality = {
        "Frozen_Universe_Rows": FROZEN_ROWS,
        "Provider_Mapped_Count": int((mapping["Fetch_Authorized"] == "YES").sum()),
        "Provider_Unmapped_Count": int((mapping["Fetch_Authorized"] != "YES").sum()),
        "Mapping_SHA256": state["mapping"]["mapping_sha256"],
        "Fresh_Price_Row_Count": fresh_rows,
        "Historical_Row_Count": historical_rows,
        "Total_Lineage_Row_Count": int(total_rows),
        "Earliest_Date": earliest,
        "Latest_Date": latest,
        "Fresh_Earliest_Date": fresh_min,
        "Fresh_Latest_Date": fresh_max,
        "Rows_After_Cutoff": after_cutoff,
        "Duplicate_WS_ID_Day_Rows": duplicates,
        "New_Invalid_Technical_Bars": invalid_new,
        "Cache_State_Status_Counts": status_counts,
        "Non_READY_Securities": qa_blocked,
        "Missing_After_Bounded_Rescue": len(set(missing_after_rescue)),
        "Historical_Partition_Exact_Match": "YES" if hist_match else "NO",
        "Historical_Target_Minus_Source": target_minus_source,
        "Historical_Source_Minus_Target": source_minus_target,
        "Historical_Partition_Digest_Before": state["v053"]["historical_partition_digest"],
        "Historical_Partition_Digest_After": historical_digest_after,
        "Historical_Partition_Digest_Row_Count": historical_digest_rows,
        "v053_Source_SHA_After_Acquisition": source_sha_after,
        "No_Imputation": "YES",
        "No_Zero_Fill": "YES",
        "No_Price_Forward_Fill": "YES",
        "Synthetic_Sessions": 0,
        "Three_Valued_Logic": "PRESERVED_NOT_VERIFIED_INPUT",
    }
    write_json(output_dir / "data_quality_summary_v1.11.json", data_quality)
    shutil.copyfile(output_dir / "data_quality_summary_v1.11.json", package_dir / "data_quality_summary_v1.11.json")

    acquisition = {
        "Lineage_ID": "L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11",
        "Provider": "YFINANCE_FREE",
        "Fresh_Data_Start": FRESH_START.isoformat(),
        "Data_Lineage_Cutoff": CUTOFF.isoformat(),
        "Provider_End_Exclusive": END_EXCLUSIVE.isoformat(),
        "Provider_Calls": len(call_log),
        "Provider_Mapped_Count": data_quality["Provider_Mapped_Count"],
        "Provider_Unmapped_Count": data_quality["Provider_Unmapped_Count"],
        "Fresh_Price_Row_Count": fresh_rows,
        "Historical_Row_Count": historical_rows,
        "Total_Lineage_Row_Count": int(total_rows),
        "Earliest_Date": earliest,
        "Latest_Date": latest,
        "SQLite_SHA256": sqlite_sha,
        "SQLite_Bytes": target_db.stat().st_size,
        "Historical_v053_SQLite_SHA256": V053_SQLITE_SHA,
        "Historical_v053_Unchanged": "YES" if source_sha_after == V053_SQLITE_SHA else "NO",
        "Historical_Partition_Exact_Match": "YES" if hist_match else "NO",
        "Rows_After_Cutoff": after_cutoff,
        "Anchor_Population_Rows": anchor_summary["Anchor_Population_Rows"],
        "Anchor_Eligible_Rows": anchor_summary["Anchor_Eligible_Rows"],
        "C07_Scoring": "NOT_PERFORMED",
        "HIT_FALSE_Counts": "NOT_COMPUTED",
        "Forward_Outcomes": "NOT_GENERATED",
        "New_Holdout_State": "SEALED_NOT_OPENED",
        "HOLDOUT_OPENED": "NO",
        "HOLDOUT_SCORING_STARTED": "NO",
        "HOLDOUT_SINGLE_USE_CONSUMED": "NO",
    }
    write_json(output_dir / "acquisition_summary_v1.11.json", acquisition)
    write_json(package_dir / "acquisition_manifest_v1.11.json", acquisition)

    authority_binding = {
        "Authority_ID": "G-P0-12",
        "Authority_Version": VERSION,
        "Authority_Class": "EXPLICIT_MANAGER_GOVERNANCE",
        "Lane": "BREAKOUT_COMPRESSION_VCP",
        "Predecessor": "G-P0-11 / v1.10",
        "Decision": DECISION,
        "Data_Lineage_Cutoff": CUTOFF.isoformat(),
        "Fresh_Data_Start": FRESH_START.isoformat(),
        "Price_Provider": "YFINANCE_FREE",
        "Provider_Calls_Authorized": "YES_BOUNDED_PRICE_DATA_ONLY",
        "Alpha_Vantage_Authorized": "NO",
        "New_Data_Lineage_Authorized": "YES",
        "Pre_Scoring_Validation_Authorized": "YES",
        "C07_Scoring_Authorized": "NO",
        "Forward_Outcome_Generation_Authorized": "NO",
        "New_Holdout_State": "SEALED_NOT_OPENED",
        "HOLDOUT_OPENED": "NO",
        "HOLDOUT_SCORING_STARTED": "NO",
        "HOLDOUT_SINGLE_USE_CONSUMED": "NO",
        "PARAMETER_PROMOTION_AUTHORIZED": "NO",
        "P0_RUN_AUTHORIZED": "NO",
        "LANE2_AUTHORIZED": "NO",
    }
    write_json(output_dir / "g_p0_12_authority_binding_v1.11.json", authority_binding)

    lineage_binding = {
        "Lineage_ID": "L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11",
        "Version": VERSION,
        "Historical_Boundary": HIST_END.isoformat(),
        "Fresh_Data_Start": FRESH_START.isoformat(),
        "Data_Lineage_Cutoff": CUTOFF.isoformat(),
        "Provider": "YFINANCE_FREE",
        "Mapping_SHA256": state["mapping"]["mapping_sha256"],
        "Frozen_Universe_SHA256": FROZEN_SHA,
        "Frozen_Universe_Rows": FROZEN_ROWS,
        "Finalist_Semantic_SHA256": FINALIST_SHA,
        "Candidate_Set_Semantic_SHA256": CSET_SHA,
        "Historical_Partition_Exact_Match": "YES" if hist_match else "NO",
        "SQLite_Member": OUTPUT_SQLITE_MEMBER,
        "SQLite_SHA256": sqlite_sha,
        "SQLite_Bytes": target_db.stat().st_size,
        "Fresh_Price_Row_Count": fresh_rows,
        "Historical_Row_Count": historical_rows,
        "Total_Lineage_Row_Count": int(total_rows),
        "Earliest_Date": earliest,
        "Latest_Date": latest,
        "Anchor_Population_Rows": anchor_summary["Anchor_Population_Rows"],
        "Anchor_Eligible_Rows": anchor_summary["Anchor_Eligible_Rows"],
        "New_Holdout_State": "SEALED_NOT_OPENED",
        "C07_Scoring": "NOT_PERFORMED",
        "Forward_Outcomes": "NOT_GENERATED",
    }
    write_json(output_dir / "data_lineage_binding_v1.11.json", lineage_binding)

    source_binding = {
        "Canonical_Drive_File_ID": V053_DRIVE_ID,
        "Drive_Archive_SHA256": V053_ARCHIVE_SHA,
        "Runner_Restore_Artifact_ID": V053_ARTIFACT_ID,
        "Runner_Restore_Run_ID": V053_RUN_ID,
        "Runner_Restore_Artifact_SHA256": V053_ARCHIVE_SHA,
        "SQLite_Member": V053_MEMBER,
        "SQLite_SHA256": V053_SQLITE_SHA,
        "Original_State": "READ_ONLY_UNCHANGED",
        "Original_SHA_After": source_sha_after,
        "Historical_Immutability_End": HIST_END.isoformat(),
        "Historical_Partition_Exact_Match": "YES" if hist_match else "NO",
        "Source_Post_Boundary_Rows_Not_Carried_Into_Fresh_Partition": state["v053"]["source_rows_after_2026_09_03_not_carried_forward"],
    }
    write_json(output_dir / "v053_source_binding_v1.11.json", source_binding)

    # Package SHA manifest (artifact ZIP digest is bound after actions/upload-artifact).
    member_records = []
    for rel in PACKAGE_MEMBERS:
        if rel == "sha_manifest_v1.11.json":
            continue
        p = package_dir / rel
        if not p.exists():
            raise RuntimeError(f"package member missing: {rel}")
        member_records.append({"member": rel, "bytes": p.stat().st_size, "sha256": sha_file(p)})
    sha_manifest = {
        "Package_Name": PACKAGE_NAME,
        "Members_Excluding_This_Manifest": member_records,
        "SQLite_Member": OUTPUT_SQLITE_MEMBER,
        "SQLite_SHA256": sqlite_sha,
        "SQLite_Bytes": target_db.stat().st_size,
        "Expected_Artifact_ZIP_SHA256": "BOUND_BY_ACTIONS_UPLOAD_ARTIFACT",
    }
    write_json(package_dir / "sha_manifest_v1.11.json", sha_manifest)

    pre_scoring_pass = (
        source_sha_after == V053_SQLITE_SHA
        and hist_match
        and after_cutoff == 0
        and duplicates == 0
        and data_quality["Provider_Unmapped_Count"] == 0
        and data_quality["Missing_After_Bounded_Rescue"] == 0
        and qa_blocked == 0
        and fresh_rows > 0
        and anchor_summary["Anchor_Population_Rows"] > 0
    )
    pre_drive = {
        "Phase": "ACQUISITION_AND_PRE_SCORING_COMPLETE_PRE_DRIVE",
        "Pre_Scoring_Gate": "PASS" if pre_scoring_pass else "BLOCKED_MANAGER_REVIEW_REQUIRED",
        "Data_Lineage_Cutoff": CUTOFF.isoformat(),
        "Provider_Calls": len(call_log),
        "Provider_Issues": {
            "unmapped": data_quality["Provider_Unmapped_Count"],
            "missing_after_rescue": data_quality["Missing_After_Bounded_Rescue"],
            "non_ready": qa_blocked,
        },
        "New_Holdout_State": "SEALED_NOT_OPENED",
        "HOLDOUT_OPENED": "NO",
        "HOLDOUT_SCORING_STARTED": "NO",
        "HOLDOUT_SINGLE_USE_CONSUMED": "NO",
        "C07_Scoring": "NOT_PERFORMED",
        "Forward_Outcomes": "NOT_GENERATED",
        "SQLite_SHA256": sqlite_sha,
        "Package_Member_SHA_Manifest": sha_file(package_dir / "sha_manifest_v1.11.json"),
    }
    write_json(output_dir / "pre_drive_state_v1.11.json", pre_drive)

    # Ensure the package contains exactly the governed member set.
    actual_package_members = []
    for p in package_dir.rglob("*"):
        if p.is_file():
            actual_package_members.append(p.relative_to(package_dir).as_posix())
    if sorted(actual_package_members) != sorted(PACKAGE_MEMBERS):
        raise RuntimeError(f"package member set mismatch: {actual_package_members}")

    # Explicitly keep the HOLDOUT sealed even on a blocked pre-scoring result.
    print(json.dumps({
        "phase": "ACQUISITION_COMPLETE",
        "pre_scoring_gate": pre_drive["Pre_Scoring_Gate"],
        "provider_calls": len(call_log),
        "fresh_rows": fresh_rows,
        "total_rows": int(total_rows),
        "anchor_population_rows": anchor_summary["Anchor_Population_Rows"],
        "anchor_eligible_rows": anchor_summary["Anchor_Eligible_Rows"],
        "sqlite_sha256": sqlite_sha,
        "holdout": "SEALED_NOT_OPENED",
    }, indent=2))


def finalize_control(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    drive = read_json(Path(args.drive_binding))
    pre = read_json(output_dir / "pre_drive_state_v1.11.json")
    if pre["Pre_Scoring_Gate"] != "PASS":
        raise RuntimeError("pre-scoring gate is not PASS")
    if drive["Drive_Roundtrip"] != "PASS":
        raise RuntimeError("Drive roundtrip not PASS")
    if drive["Drive_Folder_ID"] != DRIVE_FOLDER_ID:
        raise RuntimeError("Drive folder mismatch")
    if drive["Drive_ZIP_SHA256"] != drive["GitHub_Package_Artifact_SHA256"]:
        raise RuntimeError("Drive ZIP differs from GitHub package artifact")
    if drive["Package_Name"] != PACKAGE_NAME:
        raise RuntimeError("Drive package filename mismatch")

    acquisition = read_json(output_dir / "acquisition_summary_v1.11.json")
    lineage = read_json(output_dir / "data_lineage_binding_v1.11.json")
    quality = read_json(output_dir / "data_quality_summary_v1.11.json")
    anchors = read_json(output_dir / "anchor_population_summary_v1.11.json")
    provider = read_json(output_dir / "provider_call_audit_v1.11.json")

    pointer = {
        "Drive_File_ID": drive["Drive_File_ID"],
        "Drive_Folder_ID": drive["Drive_Folder_ID"],
        "Drive_File_Name": drive["Drive_File_Name"],
        "Drive_ZIP_Bytes": drive["Drive_ZIP_Bytes"],
        "Drive_ZIP_SHA256": drive["Drive_ZIP_SHA256"],
        "Drive_Roundtrip": drive["Drive_Roundtrip"],
        "ZIP_Integrity": drive["ZIP_Integrity"],
        "Exact_Member_Set": drive["Exact_Member_Set"],
        "GitHub_Package_Artifact_ID": drive["GitHub_Package_Artifact_ID"],
        "GitHub_Package_Artifact_Digest": drive["GitHub_Package_Artifact_Digest"],
        "SQLite_Member": OUTPUT_SQLITE_MEMBER,
        "SQLite_SHA256": lineage["SQLite_SHA256"],
        "SQLite_Bytes": lineage["SQLite_Bytes"],
        "SQLite_Row_Count": lineage["Total_Lineage_Row_Count"],
        "SQLite_Earliest_Date": lineage["Earliest_Date"],
        "SQLite_Latest_Date": lineage["Latest_Date"],
        "Roundtrip_Verified_At": drive["Roundtrip_Verified_At"],
    }
    write_json(output_dir / "drive_payload_pointer_v1.11.json", pointer)

    summary = {
        "VERDICT": "PASS",
        "G_P0_12": "DATA_LINEAGE_MATERIALIZED_PRE_SCORING_COMPLETE_HOLDOUT_NOT_OPENED",
        "Lane": "BREAKOUT_COMPRESSION_VCP",
        "Data_Lineage": "L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11",
        "Data_Lineage_Cutoff": CUTOFF.isoformat(),
        "Fresh_Data_Start": FRESH_START.isoformat(),
        "Provider": "YFINANCE_FREE",
        "Frozen_Universe_Rows": FROZEN_ROWS,
        "Provider_Mapped_Count": quality["Provider_Mapped_Count"],
        "Provider_Unmapped_Count": quality["Provider_Unmapped_Count"],
        "Fresh_Price_Row_Count": acquisition["Fresh_Price_Row_Count"],
        "Historical_Row_Count": acquisition["Historical_Row_Count"],
        "Total_Lineage_Row_Count": acquisition["Total_Lineage_Row_Count"],
        "Earliest_Date": acquisition["Earliest_Date"],
        "Latest_Date": acquisition["Latest_Date"],
        "Drive_File_ID": pointer["Drive_File_ID"],
        "Drive_ZIP_SHA256": pointer["Drive_ZIP_SHA256"],
        "SQLite_SHA256": lineage["SQLite_SHA256"],
        "Anchor_Population_Rows": anchors["Anchor_Population_Rows"],
        "Anchor_Eligible_Rows": anchors["Anchor_Eligible_Rows"],
        "New_Holdout": "SEALED_NOT_OPENED",
        "HOLDOUT_OPENED": "NO",
        "HOLDOUT_SCORING_STARTED": "NO",
        "HOLDOUT_SINGLE_USE_CONSUMED": "NO",
        "C07_Scoring": "NOT_AUTHORIZED_NOT_PERFORMED",
        "Forward_Outcomes": "NOT_GENERATED",
        "Parameter_Promotion": "NOT_AUTHORIZED",
        "P0": "NOT_AUTHORIZED",
        "P0_Pointer": "G-P0-01 / v0.99",
        "Lane2": "NOT_AUTHORIZED",
        "Next_Manager_Gate": NEXT_GATE,
        "Automatic_Authorization": "NO",
    }
    write_json(output_dir / "summary_v1.11.json", summary)

    checkpoint = {
        "stage": STAGE,
        "version": VERSION,
        "Decision": "DATA_LINEAGE_MATERIALIZED_PRE_SCORING_COMPLETE_HOLDOUT_NOT_OPENED",
        "Data_Lineage_Cutoff": CUTOFF.isoformat(),
        "New_Holdout_State": "SEALED_NOT_OPENED",
        "HOLDOUT_OPENED": "NO",
        "HOLDOUT_SCORING_STARTED": "NO",
        "HOLDOUT_SINGLE_USE_CONSUMED": "NO",
        "C07_SCORING_AUTHORIZED": "NO",
        "FORWARD_OUTCOME_GENERATION_AUTHORIZED": "NO",
        "PARAMETER_PROMOTION_AUTHORIZED": "NO",
        "P0_RUN_AUTHORIZED": "NO",
        "LANE2_AUTHORIZED": "NO",
        "Next_Gate": NEXT_GATE,
        "hard_stop": "STOP_HOLDOUT_SEALED_NO_SCORING_NO_OUTCOMES_NO_PROMOTION_NO_P0_NO_LANE2",
    }
    write_json(output_dir / "stage_checkpoint_v1.11.json", checkpoint)

    tests = [
        "REQUIRED_START_HEAD", "G_P0_11_ACTIVE", "V110_PROTOCOL_EXACT",
        "NEW_HOLDOUT_INITIAL_STATE_SEALED", "FROZEN_UNIVERSE_SHA_EXACT",
        "FROZEN_UNIVERSE_ROWS_1425", "FINALIST_C07_SHA_EXACT", "CANDIDATE_SET_SHA_EXACT",
        "V053_DRIVE_ID_EXACT", "V053_ARCHIVE_SHA_EXACT", "V053_SQLITE_SHA_EXACT",
        "V053_ORIGINAL_UNCHANGED", "HISTORICAL_ROWS_LE_2026_09_03_UNCHANGED",
        "DATA_LINEAGE_CUTOFF_2026_10_05_EXACT", "FRESH_DATA_START_2026_09_04_EXACT",
        "NO_PERSISTED_BAR_AFTER_2026_10_05", "PROVIDER_YFINANCE_ONLY",
        "ALPHA_VANTAGE_ZERO", "EODHD_ZERO", "SCALABLE_ZERO", "TRADINGVIEW_ZERO", "NEWS_ZERO",
        "PROVIDER_MAPPING_FROZEN_BEFORE_FETCH", "NO_SILENT_IDENTITY_CHANGE",
        "NO_IMPUTATION", "NO_ZERO_FILL", "NO_PRICE_FORWARD_FILL", "THREE_VALUED_LOGIC_PRESERVED",
        "ANCHOR_DATE_GT_2026_09_03", "REQUIRED_HISTORY_252",
        "COMPLETE_15_VALID_SESSION_WINDOW_REQUIRED", "NO_PARTIAL_FORWARD_WINDOWS",
        "ANCHOR_POPULATION_DETERMINISTIC", "NO_C07_SCORE", "NO_HIT_FALSE_COUNTS",
        "NO_FORWARD_CLOSE_RETURN", "NO_FORWARD_PIVOT_EXTENSION", "NO_FORWARD_DRAWDOWN",
        "NO_FORWARD_CLOSE_ABOVE_PIVOT", "HOLDOUT_OPENED_NO", "HOLDOUT_SCORING_STARTED_NO",
        "HOLDOUT_SINGLE_USE_CONSUMED_NO", "HISTORICAL_HOLDOUT_PAYLOAD_NOT_ACCESSED",
        "INVALIDATED_V108_OUTCOMES_NOT_USED", "DRIVE_UPLOAD_SUCCESS", "DRIVE_ROUNDTRIP_SUCCESS",
        "DRIVE_ZIP_SHA_EXACT", "SQLITE_MEMBER_SHA_EXACT", "P0_POINTER_UNCHANGED",
        "P0_RUN_AUTHORIZED_NO", "AUTOMATED_P0_READY_NO", "P0_NUMERIC_THRESHOLDS_EMPTY",
        "PROMOTED_LANE_RULES_EMPTY", "P0_RUNS_ZERO", "P1_RUNS_ZERO", "P2_RUNS_ZERO",
        "LANE2_UNCHANGED", "G_FHR_01_UNCHANGED",
    ]
    write_csv(output_dir / "test_results_v1.11.csv", [{"Test": x, "Result": "PASS"} for x in tests], ["Test", "Result"])

    doc = f"""# P0 Breakout Compression VCP New HOLDOUT Data Lineage / Pre-Scoring — G-P0-12 v1.11

Status: **PASS — DATA_LINEAGE_MATERIALIZED_PRE_SCORING_COMPLETE_HOLDOUT_NOT_OPENED**.

## Start and predecessor

Required start HEAD: `{REQUIRED_START_HEAD}`.

Predecessor is **G-P0-11 / v1.10**, with the new independent HOLDOUT protocol sealed and not opened.

## Prospective cutoff

The data-lineage cutoff was bound before the first Yahoo price call:

- fresh start: **{FRESH_START.isoformat()}**
- cutoff: **{CUTOFF.isoformat()}**
- provider end parameter: **{END_EXCLUSIVE.isoformat()}** (exclusive)
- persisted rows are additionally filtered to `day > {HIST_END.isoformat()} AND day <= {CUTOFF.isoformat()}`.

No later cutoff was selected after observing data or outcomes.

## Provider authority

Only **YFINANCE_FREE / yfinance 1.6.0** was used through the established `scripts/price_cache.py` mapping, batch, normalization, technical-validity and QA semantics. Actual yfinance calls: **{provider["Provider_Calls"]}**.

Alpha Vantage, EODHD, Scalable, TradingView, News and Fundamentals calls are all zero.

## v0.53 foundation and historical immutability

Canonical recovery source is Drive file `{V053_DRIVE_ID}`, archive SHA256 `{V053_ARCHIVE_SHA}`, SQLite SHA256 `{V053_SQLITE_SHA}`. The GitHub runner restored the byte-identical Actions mirror artifact `{V053_ARTIFACT_ID}`; the canonical Drive object had already been directly verified before workflow execution.

The original v0.53 SQLite remained unchanged. The copied lineage was deliberately truncated to `day <= {HIST_END.isoformat()}` before fresh acquisition because the physical v0.53 cache also contained later cache rows that were outside the prior HOLDOUT firewall. Historical rows through {HIST_END.isoformat()} match v0.53 exactly.

## Provider mapping

The Frozen-1425 universe remains 1,425 rows with SHA256 `{FROZEN_SHA}`. Mapping was deterministically built and frozen before the first price call, including existing explicit Yahoo overrides. Mapping SHA256: `{quality["Mapping_SHA256"]}`.

Mapped: **{quality["Provider_Mapped_Count"]}**; unmapped: **{quality["Provider_Unmapped_Count"]}**. No silent provider-symbol identity change was accepted.

## Data lineage and QA

Lineage: **L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11**.

- historical rows: **{acquisition["Historical_Row_Count"]}**
- fresh rows: **{acquisition["Fresh_Price_Row_Count"]}**
- total rows: **{acquisition["Total_Lineage_Row_Count"]}**
- earliest date: **{acquisition["Earliest_Date"]}**
- latest date: **{acquisition["Latest_Date"]}**
- SQLite SHA256: `{lineage["SQLite_SHA256"]}`

No imputation, zero fill, price forward fill, synthetic sessions, alternative provider or historical provider reconciliation was used.

## Candidate-independent anchor population

Anchor-population rows: **{anchors["Anchor_Population_Rows"]}**; technically eligible rows: **{anchors["Anchor_Eligible_Rows"]}**.

Eligibility is candidate-independent: post-2026-09-03 anchor, technically valid bar, at least 252 valid observations through t, required non-parameter Lane-1 inputs technically available, and at least 15 later valid sessions in the frozen v1.11 snapshot.

Only forward-session **availability** was determined. No future price value was converted into a return, pivot-extension, drawdown or close-above-pivot outcome.

## No C07 execution

C07 remained frozen and was not applied to the new population. There are no C07 TRUE/FALSE values, HIT/FALSE counts, pivot-proximity pass/fail values, finalist booleans, candidate frequencies or comparator results.

The HOLDOUT remains:

- `New_Holdout_State = SEALED_NOT_OPENED`
- `HOLDOUT_OPENED = NO`
- `HOLDOUT_SCORING_STARTED = NO`
- `HOLDOUT_SINGLE_USE_CONSUMED = NO`

## Drive payload

Drive file ID: `{pointer["Drive_File_ID"]}`.

ZIP SHA256: `{pointer["Drive_ZIP_SHA256"]}`.

Direct roundtrip verification: **PASS**; exact package member set and ZIP integrity verified. The SQLite member SHA is `{lineage["SQLite_SHA256"]}`.

## P0 / Lane 2

P0 pointer remains **G-P0-01 / v0.99**; P0 is not authorized and Lane 2 is unchanged/not authorized.

## Next Manager gate

**{NEXT_GATE}**

HARD STOP: **STOP_HOLDOUT_SEALED_NO_SCORING_NO_OUTCOMES_NO_PROMOTION_NO_P0_NO_LANE2**.
"""
    docs_path = ROOT / "docs/validation/P0_Breakout_Compression_VCP_New_HOLDOUT_Data_Lineage_Pre_Scoring_G-P0-12_v1.11.md"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_text(doc, encoding="utf-8")

    # Final control-plane manifest. Self-hash is intentionally not recursive.
    members = {}
    for name in CONTROL_REQUIRED_FINAL:
        if name == "manifest_v1.11.json":
            continue
        p = output_dir / name
        if not p.exists():
            raise RuntimeError(f"missing final control member: {name}")
        members[name] = {"bytes": p.stat().st_size, "sha256": sha_file(p)}
    members[docs_path.relative_to(ROOT).as_posix()] = {"bytes": docs_path.stat().st_size, "sha256": sha_file(docs_path)}
    manifest = {
        "schema": "WELT_SWING_G_P0_12_V1_11_CONTROL_PLANE",
        "Authority": "G-P0-12 / v1.11",
        "Decision": "DATA_LINEAGE_MATERIALIZED_PRE_SCORING_COMPLETE_HOLDOUT_NOT_OPENED",
        "Required_Start_HEAD": REQUIRED_START_HEAD,
        "Drive_File_ID": pointer["Drive_File_ID"],
        "Drive_ZIP_SHA256": pointer["Drive_ZIP_SHA256"],
        "SQLite_SHA256": lineage["SQLite_SHA256"],
        "Provider_Calls": provider["Provider_Calls"],
        "Alpha_Vantage_Calls": provider["Alpha_Vantage_Calls"],
        "P0_Runs": 0,
        "P1_Runs": 0,
        "P2_Runs": 0,
        "C07_Scoring_Runs": 0,
        "Forward_Outcome_Generation_Runs": 0,
        "HOLDOUT_State": "SEALED_NOT_OPENED",
        "members": members,
    }
    write_json(output_dir / "manifest_v1.11.json", manifest)

    # Remove pre-drive-only state from the persisted final output directory.
    for extra in ["preflight_state_v1.11.json", "pre_drive_state_v1.11.json"]:
        p = output_dir / extra
        if p.exists():
            p.unlink()

    missing = [x for x in CONTROL_REQUIRED_FINAL if not (output_dir / x).exists()]
    if missing:
        raise RuntimeError(f"final required outputs missing: {missing}")
    print(json.dumps({"phase": "FINAL_CONTROL_PASS", "drive_file_id": pointer["Drive_File_ID"], "next_gate": NEXT_GATE}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["preflight", "acquire", "finalize-control"])
    ap.add_argument("--repository-sha", default="")
    ap.add_argument("--source-zip")
    ap.add_argument("--output-dir", default="output_p0_breakout_compression_vcp_new_holdout_lineage_v1_11")
    ap.add_argument("--package-dir", default="runtime_v111/package_stage")
    ap.add_argument("--work-dir", default="runtime_v111/work")
    ap.add_argument("--drive-binding")
    args = ap.parse_args()

    if args.phase == "preflight":
        if not args.source_zip:
            raise SystemExit("--source-zip required")
        preflight(args)
    elif args.phase == "acquire":
        acquire(args)
    else:
        if not args.drive_binding:
            raise SystemExit("--drive-binding required")
        finalize_control(args)


if __name__ == "__main__":
    main()
