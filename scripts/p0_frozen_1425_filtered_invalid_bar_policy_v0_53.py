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
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from price_cache import (
    FreeDataConfig,
    normalize_symbol_frame,
    qa_symbol_frame,
    technical_valid_mask,
)
from feature_builder import build_features, technical_valid_mask_for_features, split_adjust_technical

VERSION = "v0.53"
REQUIRED_START_HEAD = "b8b9178385c58351910b2e61fe1f473d4f47af18"
SOURCE_RUNTIME_SHA256 = "8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063"
SOURCE_RUNTIME_BYTES = 144216064
SOURCE_PRICE_ROWS = 711204
SOURCE_STATES = 1425
SOURCE_READY = 1417
SOURCE_QUARANTINE = 8
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
FROZEN_ROWS = 1425
POLICY_DECISION_PATH = ROOT / "output_p0_asx_ohlc_source_policy_v0_52/decision_v0.52.json"
FROZEN_PATH = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
HISTORY_POLICY_PATH = ROOT / "config/history_qa_v1_policy.json"
CORE_POLICY_ID = "QA_Filtered_Bar_Policy_Promotion_v0.4"
IMPLEMENTATION_POLICY_ID = "POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT"
RESOLVED_SUSPICIOUS_REASONS = frozenset({"VERIFIED_EXTREME_RETURN", "VALIDATED_522_RECONCILIATION"})
FILTERABLE_DEFECT_REASONS = frozenset({
    "",
    "STRICT_OHLC_RELATION_FAIL",
    "INVALID_OHLC_OR_VOLUME",
    "ISOLATED_INVALID_BAR_EXCLUDED",
    "FILTERED_INVALID_BARS_EXCLUDED",
})
PRODUCTIVE = False
ALPHA_VANTAGE_CALLS = 0
SCALABLE_CALLS = 0
MARKET_PROVIDER_CALLS = 0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_file_binding(path: Path) -> dict[str, Any]:
    h1 = sha256_file(path)
    n1 = path.stat().st_size
    h2 = sha256_file(path)
    n2 = path.stat().st_size
    if h1 != h2 or n1 != n2:
        raise RuntimeError("runtime SQLite is not byte-stable")
    return {
        "sha256_pass_1": h1,
        "sha256_pass_2": h2,
        "bytes_pass_1": n1,
        "bytes_pass_2": n2,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def connect_ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def frozen_digest() -> str:
    return sha256_file(FROZEN_PATH)


def table_digest(conn: sqlite3.Connection, sql: str) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    cur = conn.execute(sql)
    for row in cur:
        payload = json.dumps(list(row), ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=str)
        h.update(payload.encode("utf-8"))
        h.update(b"\n")
        n += 1
    return h.hexdigest(), n


PRICE_DIGEST_SQL = """
SELECT ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired,source_id,fetched_utc
FROM price_daily
ORDER BY ws_id,day
"""

MAPPING_DIGEST_SQL = """
SELECT ws_id,yahoo_symbol,mapping_status
FROM cache_state
ORDER BY ws_id
"""


def validate_source_runtime(path: Path) -> dict[str, Any]:
    if path.stat().st_size != SOURCE_RUNTIME_BYTES:
        raise RuntimeError(f"source runtime byte mismatch: {path.stat().st_size}")
    if sha256_file(path) != SOURCE_RUNTIME_SHA256:
        raise RuntimeError("source runtime SHA-256 mismatch")
    con = connect_ro(path)
    try:
        integrity = str(con.execute("PRAGMA integrity_check").fetchone()[0])
        price_rows = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        states = int(con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        counts = {str(k): int(v) for k, v in con.execute(
            "SELECT status,COUNT(*) FROM cache_state GROUP BY status ORDER BY status"
        ).fetchall()}
        price_digest, price_digest_rows = table_digest(con, PRICE_DIGEST_SQL)
        mapping_digest, mapping_rows = table_digest(con, MAPPING_DIGEST_SQL)
    finally:
        con.close()
    if integrity != "ok":
        raise RuntimeError("source runtime integrity_check failed")
    if price_rows != SOURCE_PRICE_ROWS or price_digest_rows != SOURCE_PRICE_ROWS:
        raise RuntimeError("source runtime price row count mismatch")
    if states != SOURCE_STATES or mapping_rows != SOURCE_STATES:
        raise RuntimeError("source runtime state count mismatch")
    if counts != {"QUARANTINE": SOURCE_QUARANTINE, "READY": SOURCE_READY}:
        raise RuntimeError(f"source runtime status mismatch: {counts}")
    return {
        "integrity_check": integrity,
        "price_rows": price_rows,
        "states": states,
        "status_counts": counts,
        "price_daily_content_digest": price_digest,
        "provider_mapping_digest": mapping_digest,
    }


def validate_start_authority(repository_sha: str) -> dict[str, str]:
    head = git("rev-parse", "HEAD")
    if repository_sha and head != repository_sha:
        raise RuntimeError(f"workflow checkout SHA mismatch: {head} != {repository_sha}")
    parent = git("rev-parse", "HEAD^")
    anc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if anc.returncode != 0:
        raise RuntimeError("required start HEAD is not an ancestor of implementation")
    if frozen_digest() != FROZEN_SHA256:
        raise RuntimeError("Frozen SHA-256 mismatch")
    frozen = read_csv(FROZEN_PATH)
    if len(frozen) != FROZEN_ROWS:
        raise RuntimeError("Frozen row count mismatch")
    if len({r["Security_Key"] for r in frozen}) != FROZEN_ROWS:
        raise RuntimeError("Frozen Security_Key duplication")
    if len({r["Source_WS_ID"] for r in frozen}) != FROZEN_ROWS:
        raise RuntimeError("Frozen Source_WS_ID duplication")
    return {"head": head, "parent": parent}


def canonical_contract() -> dict[str, Any]:
    cfg = FreeDataConfig()
    hist = json.loads(HISTORY_POLICY_PATH.read_text(encoding="utf-8"))
    promoted = hist["promoted_filtered_bar_policy"]
    observed = {
        "max_invalid_bars": int(cfg.max_filterable_invalid_bars),
        "max_invalid_share": float(cfg.max_filterable_invalid_share),
        "minimum_valid_observations_after_filter": int(cfg.ready_unique_bars),
        "minimum_valid_bars_core": int(cfg.min_valid_bars),
        "stale_after_calendar_days": int(cfg.stale_calendar_days),
        "history_policy_version": str(hist["policy_version"]),
        "history_max_invalid_bars": int(promoted["max_invalid_bars"]),
        "history_max_invalid_share": float(promoted["max_invalid_share"]),
        "history_minimum_valid_after_filter": int(promoted["minimum_valid_observations_after_filter"]),
    }
    expected = {
        "max_invalid_bars": 2,
        "max_invalid_share": 0.01,
        "minimum_valid_observations_after_filter": 260,
    }
    if observed["max_invalid_bars"] != expected["max_invalid_bars"]:
        raise RuntimeError("canonical max invalid bars differs from v0.52 authority")
    if not math.isclose(observed["max_invalid_share"], expected["max_invalid_share"], rel_tol=0, abs_tol=1e-15):
        raise RuntimeError("canonical max invalid share differs from v0.52 authority")
    if observed["minimum_valid_observations_after_filter"] != expected["minimum_valid_observations_after_filter"]:
        raise RuntimeError("canonical minimum valid observations differs from v0.52 authority")
    if observed["history_max_invalid_bars"] != observed["max_invalid_bars"]:
        raise RuntimeError("History QA max invalid bars diverges from canonical core")
    if not math.isclose(observed["history_max_invalid_share"], observed["max_invalid_share"], rel_tol=0, abs_tol=1e-15):
        raise RuntimeError("History QA invalid share diverges from canonical core")
    if observed["history_minimum_valid_after_filter"] != observed["minimum_valid_observations_after_filter"]:
        raise RuntimeError("History QA minimum valid after filtering diverges from canonical core")
    return observed


def invalid_reason_codes(frame: pd.DataFrame) -> dict[str, list[str]]:
    x = normalize_symbol_frame(frame)
    out: dict[str, list[str]] = {}
    for ts, r in x.iterrows():
        reasons: list[str] = []
        vals = [r["open"], r["high"], r["low"], r["close"]]
        if not all(pd.notna(v) and np.isfinite(float(v)) for v in vals):
            reasons.append("NONFINITE_OHLC")
        elif not all(float(v) > 0 for v in vals):
            reasons.append("NONPOSITIVE_OHLC")
        if pd.notna(r["high"]) and pd.notna(r["low"]) and float(r["high"]) < float(r["low"]):
            reasons.append("HIGH_LOW_RELATION_FAIL")
        if all(pd.notna(r[c]) for c in ["high", "low", "close"]):
            if float(r["close"]) > float(r["high"]) or float(r["close"]) < float(r["low"]):
                reasons.append("CLOSE_OUTSIDE_RANGE")
        if pd.notna(r["volume"]) and float(r["volume"]) < 0:
            reasons.append("NEGATIVE_VOLUME")
        if reasons:
            out[pd.Timestamp(ts).date().isoformat()] = reasons
    return out


def higher_priority_blocker(existing_status: str, existing_reason: str) -> str:
    status = (existing_status or "").strip()
    reason = (existing_reason or "").strip()
    if status in {"MAPPING_PENDING", "DOWNLOAD_FAILED"}:
        return f"PRESERVE_{status}:{reason or 'NO_REASON'}"
    if status == "QUARANTINE" and reason not in FILTERABLE_DEFECT_REASONS and reason != "SUSPICIOUS_RETURN_NEEDS_REPAIR":
        return f"PRESERVE_EXISTING_QUARANTINE:{reason or 'NO_REASON'}"
    return "NONE"


def propose_state(
    qa: dict[str, Any],
    existing_status: str,
    existing_reason: str,
    external_blocker: str,
) -> tuple[str, str, str, str]:
    old_status = (existing_status or "").strip()
    old_reason = (existing_reason or "").strip()
    if external_blocker != "NONE":
        return old_status, old_reason, "BLOCK_HIGHER_PRIORITY", external_blocker
    if qa["status"] == "QUARANTINE" and qa["reason_code"] == "SUSPICIOUS_RETURN_NEEDS_REPAIR":
        if old_status == "READY" and old_reason in RESOLVED_SUSPICIOUS_REASONS:
            return "READY", old_reason, "PASS_EXISTING_SUSPICIOUS_RECONCILIATION", "RESOLVED_EXISTING_AUTHORITY"
        return "QUARANTINE", "SUSPICIOUS_RETURN_NEEDS_REPAIR", "BLOCK_UNRESOLVED_SUSPICIOUS_RETURN", "UNRESOLVED"
    if qa["status"] == "READY":
        reason = str(qa.get("reason_code") or "")
        if reason == "ISOLATED_INVALID_BAR_EXCLUDED":
            result = "PASS_ISOLATED_INVALID_BAR"
        elif reason == "FILTERED_INVALID_BARS_EXCLUDED":
            result = "PASS_FILTERED_INVALID_BARS"
        else:
            result = "PASS_CLEAN"
        return "READY", reason, result, "NONE"
    return str(qa["status"]), str(qa.get("reason_code") or ""), f"BLOCK_{qa['status']}", "NONE"


def load_runtime_frames(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    states = pd.read_sql_query(
        "SELECT ws_id,yahoo_symbol,mapping_status,status,coalesce(reason_code,'') reason_code,"
        "unique_bars,valid_bars,repaired_rows,suspicious_returns,zero_volume_share,"
        "first_bar_date,last_bar_date,last_fetch_utc,batch_id,coalesce(last_error,'') last_error "
        "FROM cache_state ORDER BY ws_id",
        conn,
    )
    px = pd.read_sql_query(
        "SELECT ws_id,day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired "
        "FROM price_daily ORDER BY ws_id,day",
        conn,
    )
    return states, px


def full_frozen_regression(conn: sqlite3.Connection, as_of: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frozen = read_csv(FROZEN_PATH)
    frozen_by = {r["Source_WS_ID"]: r for r in frozen}
    states, px = load_runtime_frames(conn)
    if len(states) != FROZEN_ROWS or set(states["ws_id"].astype(str)) != set(frozen_by):
        raise RuntimeError("runtime state identities differ from Frozen")
    groups = {str(k): v.copy() for k, v in px.groupby("ws_id", sort=False)}
    state_by = states.set_index("ws_id", drop=False)
    rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for ws in sorted(frozen_by, key=lambda x: int(frozen_by[x]["Projection_Order"])):
        fr = frozen_by[ws]
        if ws not in groups:
            raise RuntimeError(f"missing price history for Frozen identity {ws}")
        g = groups[ws].copy()
        g["day"] = pd.to_datetime(g["day"], errors="raise")
        g = g.set_index("day")
        qa = qa_symbol_frame(g, config=FreeDataConfig(), as_of=as_of)
        norm = normalize_symbol_frame(g)
        valid_mask = technical_valid_mask(norm)
        invalid = norm.loc[~valid_mask].copy()
        invalid_count = int((~valid_mask).sum())
        raw_count = int(len(norm))
        valid_count = int(valid_mask.sum())
        invalid_share = float(invalid_count / raw_count) if raw_count else 0.0
        reasons = invalid_reason_codes(norm)
        affected_dates = sorted(reasons)
        for d in affected_dates:
            excluded_rows.append({
                "Source_WS_ID": ws,
                "Security_Key": fr["Security_Key"],
                "Observation_Date": d,
                "SOURCE_DATA_DEFECT": True,
                "TECHNICAL_BAR_EXCLUDED": True,
                "Reason_Codes": "|".join(reasons[d]),
                "Core_QA_Policy": CORE_POLICY_ID,
                "Implementation_Policy": IMPLEMENTATION_POLICY_ID,
            })
        st = state_by.loc[ws]
        old_status = str(st["status"] or "")
        old_reason = str(st["reason_code"] or "")
        ext = higher_priority_blocker(old_status, old_reason)
        new_status, new_reason, policy_result, suspicious_resolution = propose_state(qa, old_status, old_reason, ext)
        stale_status = "STALE" if qa["status"] == "STALE" else "NOT_STALE"
        if int(qa["suspicious_returns"]) == 0:
            suspicious_status = "NONE"
        elif suspicious_resolution == "RESOLVED_EXISTING_AUTHORITY":
            suspicious_status = "RESOLVED_EXISTING_AUTHORITY"
        else:
            suspicious_status = "UNRESOLVED"
        if old_status == new_status and old_reason == new_reason:
            change_reason = "UNCHANGED"
        elif old_status == "QUARANTINE" and new_status == "READY" and invalid_count > 0:
            change_reason = "CANONICAL_FILTERED_INVALID_BAR_POLICY_ALIGNMENT"
        else:
            change_reason = f"{old_status}:{old_reason}->{new_status}:{new_reason}"
        rows.append({
            "Projection_Order": int(fr["Projection_Order"]),
            "Security_Key": fr["Security_Key"],
            "Source_WS_ID": ws,
            "Primary_MIC": fr["Primary_MIC"],
            "Primary_Ticker": fr["Primary_Ticker"],
            "Provider_Symbol": str(st["yahoo_symbol"] or ""),
            "raw_bar_count": raw_count,
            "valid_bar_count": valid_count,
            "invalid_bar_count": invalid_count,
            "invalid_share": invalid_share,
            "affected_dates": "|".join(affected_dates),
            "defect_reasons": "|".join(sorted({z for v in reasons.values() for z in v})),
            "stale_status": stale_status,
            "suspicious_return_count": int(qa["suspicious_returns"]),
            "suspicious_return_status": suspicious_status,
            "higher_priority_blocker_status": ext,
            "canonical_qa_status": str(qa["status"]),
            "canonical_qa_reason": str(qa.get("reason_code") or ""),
            "filtered_policy_result": policy_result,
            "old_cache_state": old_status,
            "old_reason": old_reason,
            "proposed_cache_state": new_status,
            "proposed_reason": new_reason,
            "state_change_reason": change_reason,
        })
    if len(rows) != FROZEN_ROWS:
        raise RuntimeError("full regression did not produce 1425 rows")
    return rows, excluded_rows


def create_provenance_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS cache_qa_provenance_v053 (
        ws_id TEXT PRIMARY KEY,
        source_data_defect INTEGER NOT NULL,
        invalid_bar_count INTEGER NOT NULL,
        invalid_share REAL NOT NULL,
        affected_dates_json TEXT NOT NULL,
        defect_reasons_json TEXT NOT NULL,
        core_qa_policy TEXT NOT NULL,
        history_qa_policy TEXT NOT NULL,
        implementation_policy TEXT NOT NULL,
        filtered_policy_result TEXT NOT NULL,
        evaluated_as_of TEXT NOT NULL,
        old_status TEXT NOT NULL,
        old_reason TEXT NOT NULL,
        final_status TEXT NOT NULL,
        final_reason TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS technical_bar_exclusions_v053 (
        ws_id TEXT NOT NULL,
        day TEXT NOT NULL,
        source_data_defect INTEGER NOT NULL,
        technical_bar_excluded INTEGER NOT NULL,
        reason_codes TEXT NOT NULL,
        core_qa_policy TEXT NOT NULL,
        implementation_policy TEXT NOT NULL,
        PRIMARY KEY (ws_id, day)
    );
    """)


def apply_regression_state(conn: sqlite3.Connection, rows: list[dict[str, Any]], excluded: list[dict[str, Any]], as_of: date, history_policy_version: str) -> list[dict[str, Any]]:
    create_provenance_tables(conn)
    conn.execute("DELETE FROM cache_qa_provenance_v053")
    conn.execute("DELETE FROM technical_bar_exclusions_v053")
    transitions: list[dict[str, Any]] = []
    by_ws_dates: dict[str, list[str]] = {}
    by_ws_reasons: dict[str, list[str]] = {}
    for r in excluded:
        by_ws_dates.setdefault(r["Source_WS_ID"], []).append(r["Observation_Date"])
        by_ws_reasons.setdefault(r["Source_WS_ID"], []).extend(r["Reason_Codes"].split("|"))
        conn.execute(
            "INSERT INTO technical_bar_exclusions_v053 "
            "(ws_id,day,source_data_defect,technical_bar_excluded,reason_codes,core_qa_policy,implementation_policy) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                r["Source_WS_ID"], r["Observation_Date"], 1, 1, r["Reason_Codes"],
                CORE_POLICY_ID, IMPLEMENTATION_POLICY_ID,
            ),
        )
    for r in rows:
        ws = r["Source_WS_ID"]
        final_status = r["proposed_cache_state"]
        final_reason = r["proposed_reason"]
        conn.execute(
            "INSERT INTO cache_qa_provenance_v053 "
            "(ws_id,source_data_defect,invalid_bar_count,invalid_share,affected_dates_json,defect_reasons_json,"
            "core_qa_policy,history_qa_policy,implementation_policy,filtered_policy_result,evaluated_as_of,"
            "old_status,old_reason,final_status,final_reason) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ws,
                1 if int(r["invalid_bar_count"]) > 0 else 0,
                int(r["invalid_bar_count"]),
                float(r["invalid_share"]),
                json.dumps(sorted(by_ws_dates.get(ws, [])), separators=(",", ":")),
                json.dumps(sorted(set(by_ws_reasons.get(ws, []))), separators=(",", ":")),
                CORE_POLICY_ID,
                history_policy_version,
                IMPLEMENTATION_POLICY_ID,
                r["filtered_policy_result"],
                as_of.isoformat(),
                r["old_cache_state"],
                r["old_reason"],
                final_status,
                final_reason,
            ),
        )
        if r["old_cache_state"] != final_status or r["old_reason"] != final_reason:
            cur = conn.execute(
                "UPDATE cache_state SET status=?, reason_code=?, last_error=? WHERE ws_id=? AND status=? AND coalesce(reason_code,'')=?",
                (
                    final_status,
                    final_reason or None,
                    None if final_status == "READY" else final_reason or None,
                    ws,
                    r["old_cache_state"],
                    r["old_reason"],
                ),
            )
            if cur.rowcount != 1:
                raise RuntimeError(f"state update precondition failed for {ws}")
            transitions.append({
                "Security_Key": r["Security_Key"],
                "Source_WS_ID": ws,
                "Primary_MIC": r["Primary_MIC"],
                "Primary_Ticker": r["Primary_Ticker"],
                "Provider_Symbol": r["Provider_Symbol"],
                "Status_Before": r["old_cache_state"],
                "Reason_Before": r["old_reason"],
                "Status_After": final_status,
                "Reason_After": final_reason,
                "State_Change_Reason": r["state_change_reason"],
                "invalid_bar_count": r["invalid_bar_count"],
                "invalid_share": r["invalid_share"],
                "affected_dates": r["affected_dates"],
            })
    return transitions


def finalize_sqlite_for_binding(conn: sqlite3.Connection, path: Path) -> dict[str, Any]:
    conn.commit()
    mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
    checkpoint = None
    if mode == "wal":
        checkpoint = tuple(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
    conn.commit()
    conn.close()
    # Permanent lifecycle contract: no runtime byte hash is taken before commit/checkpoint/close.
    bound = stable_file_binding(path)
    bound["journal_mode_before_close"] = mode
    bound["wal_checkpoint_result"] = checkpoint
    bound["hash_after_close"] = True
    return bound


def make_synthetic_frame(valid_count: int, invalid_count: int, end: date, suspicious: bool = False) -> pd.DataFrame:
    total = valid_count + invalid_count
    idx = pd.bdate_range(end=pd.Timestamp(end), periods=total)
    base = np.arange(total, dtype=float) * 0.05 + 100.0
    close = base.copy()
    if suspicious and total >= 30:
        pos = total - 20
        close[pos:] = close[pos:] + 100.0
    open_ = close - 0.10
    high = close + 0.30
    low = close - 0.30
    volume = np.full(total, 1000000.0)
    for i in range(invalid_count):
        high[i] = close[i] - 0.01
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close,
        "adj_close": close, "volume": volume, "dividends": 0.0,
        "stock_splits": 0.0, "repaired": 0.0,
    }, index=idx)


def synthetic_policy_tests(as_of: date) -> list[dict[str, Any]]:
    cfg = FreeDataConfig()
    rows: list[dict[str, Any]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        rows.append({"Test": name, "Result": "PASS" if passed else "FAIL", "Detail": detail})
        if not passed:
            raise AssertionError(f"{name}: {detail}")

    q = qa_symbol_frame(make_synthetic_frame(298, 2, as_of), config=cfg, as_of=as_of)
    record("2_INVALID_BARS_BOUNDARY_PASS", q["status"] == "READY" and q["reason_code"] == "FILTERED_INVALID_BARS_EXCLUDED", json.dumps(q, default=str))

    q = qa_symbol_frame(make_synthetic_frame(297, 3, as_of), config=cfg, as_of=as_of)
    record("3_INVALID_BARS_FAIL", q["status"] == "QUARANTINE" and q["reason_code"] == "INVALID_OHLC_OR_VOLUME", json.dumps(q, default=str))

    exact_share = 1 / 100
    record("INVALID_SHARE_EXACT_1PCT_PREDICATE_PASS", math.isclose(exact_share, cfg.max_filterable_invalid_share) and exact_share <= cfg.max_filterable_invalid_share,
           "Joint READY construction is mathematically impossible with <=2 invalid bars and >=260 valid bars; predicate boundary tested directly.")

    over_share = 2 / 100
    record("INVALID_SHARE_GT_1PCT_PREDICATE_FAIL", over_share > cfg.max_filterable_invalid_share,
           f"share={over_share}")

    q = qa_symbol_frame(make_synthetic_frame(260, 1, as_of), config=cfg, as_of=as_of)
    record("260_VALID_AFTER_FILTER_PASS", q["status"] == "READY" and q["valid_bars"] == 260, json.dumps(q, default=str))

    q = qa_symbol_frame(make_synthetic_frame(259, 1, as_of), config=cfg, as_of=as_of)
    record("259_VALID_AFTER_FILTER_FAIL", q["status"] != "READY" and q["valid_bars"] == 259, json.dumps(q, default=str))

    stale_end = as_of - timedelta(days=cfg.stale_calendar_days + 1)
    q = qa_symbol_frame(make_synthetic_frame(300, 0, stale_end), config=cfg, as_of=as_of)
    record("STALE_FAIL", q["status"] == "STALE", json.dumps(q, default=str))

    q = qa_symbol_frame(make_synthetic_frame(300, 0, as_of, suspicious=True), config=cfg, as_of=as_of)
    record("UNRESOLVED_SUSPICIOUS_RETURN_FAIL", q["status"] == "QUARANTINE" and q["reason_code"] == "SUSPICIOUS_RETURN_NEEDS_REPAIR", json.dumps(q, default=str))

    qclean = qa_symbol_frame(make_synthetic_frame(300, 0, as_of), config=cfg, as_of=as_of)
    st = propose_state(qclean, "QUARANTINE", "IDENTITY_CONFLICT", "PRESERVE_EXISTING_QUARANTINE:IDENTITY_CONFLICT")
    record("HIGHER_PRIORITY_BLOCKER_FAIL", st[0] == "QUARANTINE" and st[2] == "BLOCK_HIGHER_PRIORITY", str(st))

    qmulti = qa_symbol_frame(make_synthetic_frame(297, 3, stale_end, suspicious=True), config=cfg, as_of=as_of)
    st = propose_state(qmulti, "QUARANTINE", "IDENTITY_CONFLICT", "PRESERVE_EXISTING_QUARANTINE:IDENTITY_CONFLICT")
    record("MULTIPLE_SIMULTANEOUS_BLOCKERS_FAIL", st[0] == "QUARANTINE" and st[2] == "BLOCK_HIGHER_PRIORITY" and qmulti["status"] != "READY", f"qa={qmulti}; final={st}")

    qsusp = qa_symbol_frame(make_synthetic_frame(300, 0, as_of, suspicious=True), config=cfg, as_of=as_of)
    st = propose_state(qsusp, "READY", "VERIFIED_EXTREME_RETURN", "NONE")
    record("EXISTING_VERIFIED_SUSPICIOUS_RECONCILIATION_PRESERVED", st[0] == "READY" and st[1] == "VERIFIED_EXTREME_RETURN", str(st))

    return rows


def feature_path_regression(as_of: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db = root / "fixture.sqlite"
        uni = root / "universe.csv"
        con = sqlite3.connect(db)
        con.executescript("""
        CREATE TABLE cache_state (
            ws_id TEXT PRIMARY KEY, yahoo_symbol TEXT, mapping_status TEXT, status TEXT,
            reason_code TEXT, unique_bars INTEGER, valid_bars INTEGER, repaired_rows INTEGER,
            suspicious_returns INTEGER, zero_volume_share REAL, first_bar_date TEXT,
            last_bar_date TEXT, last_fetch_utc TEXT, batch_id TEXT, last_error TEXT
        );
        CREATE TABLE price_daily (
            ws_id TEXT NOT NULL, yahoo_symbol TEXT NOT NULL, day TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, adj_close REAL, volume REAL,
            dividends REAL, stock_splits REAL, repaired INTEGER NOT NULL DEFAULT 0,
            source_id TEXT NOT NULL, fetched_utc TEXT NOT NULL,
            PRIMARY KEY (ws_id, day)
        );
        """)
        n = 300
        idx = pd.bdate_range(end=pd.Timestamp(as_of), periods=n)
        close = np.linspace(100.0, 130.0, n)
        frame = pd.DataFrame({
            "day": idx,
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "adj_close": close,
            "volume": np.arange(n, dtype=float) * 1000.0 + 1_000_000.0,
            "dividends": 0.0,
            "stock_splits": 0.0,
            "repaired": 0,
        })
        bad_pos = 100
        bad_day = frame.loc[bad_pos, "day"].date().isoformat()
        frame.loc[bad_pos, "high"] = frame.loc[bad_pos, "close"] - 0.01
        dbrows = [
            (
                "FIXTURE", "FIXTURE", r.day.date().isoformat(), float(r.open), float(r.high), float(r.low),
                float(r.close), float(r.adj_close), float(r.volume), float(r.dividends),
                float(r.stock_splits), int(r.repaired), "FIXTURE", "FIXTURE"
            )
            for r in frame.itertuples(index=False)
        ]
        con.executemany(
            "INSERT INTO price_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            dbrows,
        )
        con.execute(
            "INSERT INTO cache_state VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("FIXTURE", "FIXTURE", "FIXTURE", "READY", "ISOLATED_INVALID_BAR_EXCLUDED",
             n, n - 1, 0, 0, 0.0, idx[0].date().isoformat(), idx[-1].date().isoformat(),
             "FIXTURE", "FIXTURE", None),
        )
        con.commit()
        raw_count_before = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        con.close()
        pd.DataFrame([{
            "WS_ID": "FIXTURE", "Name": "Fixture", "ISIN": "", "Country": "ZZ",
            "Primary_Ticker": "FIXTURE", "Primary_Exchange": "Fixture", "Primary_MIC": "XFIX",
            "Primary_Currency": "EUR", "Primary_Universe_Index": "FIXTURE", "Index_Tags": "FIXTURE",
        }]).to_csv(uni, index=False)

        features = build_features(db, uni)
        if len(features) != 1:
            raise AssertionError("feature fixture did not produce exactly one feature row")
        got = features.iloc[0]

        g = frame.copy().set_index("day")
        mask = technical_valid_mask_for_features(g)
        filtered = g.loc[mask].reset_index().rename(columns={"index": "day"})
        filtered = split_adjust_technical(filtered)
        c = pd.to_numeric(filtered["close_tech"], errors="coerce")
        h = pd.to_numeric(filtered["high_tech"], errors="coerce")
        l = pd.to_numeric(filtered["low_tech"], errors="coerce")
        v = pd.to_numeric(filtered["volume_tech"], errors="coerce")
        prev = c.shift(1)
        tr = pd.concat([(h-l).abs(), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
        ema20 = c.ewm(span=20, adjust=False, min_periods=20).mean().iloc[-1]
        ema50 = c.ewm(span=50, adjust=False, min_periods=50).mean().iloc[-1]
        atr14 = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean().iloc[-1]
        high20 = h.rolling(20, min_periods=20).max().iloc[-1]
        low20 = l.rolling(20, min_periods=20).min().iloc[-1]
        r20 = c.iloc[-1] / c.iloc[-21] - 1.0
        medvol20 = v.tail(20).median()
        medturn20 = (c * v).tail(20).median()

        con = sqlite3.connect(db)
        raw_count_after = int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        bad_still_present = int(con.execute("SELECT COUNT(*) FROM price_daily WHERE ws_id='FIXTURE' AND day=?", (bad_day,)).fetchone()[0])
        con.close()

        checks = [
            ("RAW_ROW_REMAINS_PRESENT", raw_count_before == n and raw_count_after == n and bad_still_present == 1, f"before={raw_count_before};after={raw_count_after};bad={bad_still_present}"),
            ("INVALID_ROW_ABSENT_FROM_FEATURE_INPUT", int(mask.sum()) == n-1 and not bool(mask.iloc[bad_pos]) and int(got["Excluded_Invalid_Bars"]) == 1, f"used={int(mask.sum())};excluded={got['Excluded_Invalid_Bars']}"),
            ("EMA20_FILTERED_PATH", math.isclose(float(got["EMA20"]), float(ema20), rel_tol=1e-12, abs_tol=1e-12), "DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES"),
            ("EMA50_FILTERED_PATH", math.isclose(float(got["EMA50"]), float(ema50), rel_tol=1e-12, abs_tol=1e-12), "DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES"),
            ("ATR14_FILTERED_PATH", math.isclose(float(got["ATR14_Wilder_DEV"]), float(atr14), rel_tol=1e-12, abs_tol=1e-12), "DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES"),
            ("ROLLING_HIGH_FILTERED_PATH", math.isclose(float(got["High20"]), float(high20), rel_tol=1e-12, abs_tol=1e-12), "filtered High20"),
            ("ROLLING_LOW_FILTERED_PATH", math.isclose(float(got["Low20"]), float(low20), rel_tol=1e-12, abs_tol=1e-12), "filtered Low20"),
            ("RETURNS_FILTERED_PATH", math.isclose(float(got["R20"]), float(r20), rel_tol=1e-12, abs_tol=1e-12), "filtered R20"),
            ("VOLUME_FILTERED_PATH", math.isclose(float(got["MedianVolume20_Tech"]), float(medvol20), rel_tol=1e-12, abs_tol=1e-12), "filtered MedianVolume20"),
            ("TURNOVER_FILTERED_PATH", math.isclose(float(got["MedianTurnover20_Native"]), float(medturn20), rel_tol=1e-12, abs_tol=1e-12), "filtered MedianTurnover20"),
        ]
        for name, ok, detail in checks:
            rows.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})
            if not ok:
                raise AssertionError(f"{name}: {detail}")
    return rows


def byte_lifecycle_regression() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "lifecycle.sqlite"
        con = sqlite3.connect(p)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, value TEXT)")
        con.execute("INSERT INTO t(value) VALUES ('a')")
        binding = finalize_sqlite_for_binding(con, p)
        try:
            con.execute("SELECT 1")
            closed_guard = False
        except sqlite3.ProgrammingError:
            closed_guard = True
        wal_exists = Path(str(p) + "-wal").exists()
        if not binding["hash_after_close"] or not closed_guard or wal_exists:
            raise AssertionError("byte lifecycle ordering regression failed")
        if binding["sha256_pass_1"] != binding["sha256_pass_2"]:
            raise AssertionError("byte lifecycle repeat hash mismatch")
        return {
            "Result": "PASS",
            "hash_after_close": binding["hash_after_close"],
            "connection_closed_guard": closed_guard,
            "wal_sidecar_after_close": wal_exists,
            "sha256": binding["sha256_pass_1"],
            "bytes": binding["bytes_pass_1"],
        }


def assert_no_special_pleading(source_path: Path) -> dict[str, Any]:
    decision = json.loads(POLICY_DECISION_PATH.read_text(encoding="utf-8"))
    src = source_path.read_text(encoding="utf-8")
    forbidden_literals = [decision["asx8_current_runtime_shape"]["anomaly_date"]]
    forbidden_literals.extend(decision["asx8_current_runtime_shape"]["securities"])
    hits = [x for x in forbidden_literals if x and x in src]
    structural_hits = []
    structural_tokens = [
        "M" + "IC" + " == ",
        "Primary_" + "MIC" + " == ",
        "provider" + " == ",
        "Ya" + "hoo" + " -> special",
        "max(" + "High" + ", " + "Close" + ")",
        "min(" + "Low" + ", " + "Close" + ")",
    ]
    for token in structural_tokens:
        if token in src:
            structural_hits.append(token)
    if hits or structural_hits:
        raise AssertionError(f"special-pleading literal found in implementation: literals={hits}, structural={structural_hits}")
    return {"Result": "PASS", "literal_hits": hits, "structural_hits": structural_hits}


def validation_case_rows(regression: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision = json.loads(POLICY_DECISION_PATH.read_text(encoding="utf-8"))
    shape = decision["asx8_current_runtime_shape"]
    tickers = set(shape["securities"])
    rows = [r for r in regression if r["Primary_Ticker"] in tickers and r["Primary_MIC"] == shape["primary_mic"]]
    if len(rows) != len(tickers):
        raise RuntimeError("v0.52 validation population did not reconcile against Frozen runtime")
    out: list[dict[str, Any]] = []
    for r in rows:
        checks = {
            "raw_matches_v052": int(r["raw_bar_count"]) == int(shape["each_raw_bars"]),
            "valid_matches_v052": int(r["valid_bar_count"]) == int(shape["each_valid_bars"]),
            "invalid_matches_v052": int(r["invalid_bar_count"]) == int(shape["each_invalid_bars"]),
            "invalid_count_gate": 1 <= int(r["invalid_bar_count"]) <= FreeDataConfig().max_filterable_invalid_bars,
            "invalid_share_gate": float(r["invalid_share"]) <= FreeDataConfig().max_filterable_invalid_share,
            "valid_bar_gate": int(r["valid_bar_count"]) >= FreeDataConfig().ready_unique_bars,
            "not_stale": r["stale_status"] == "NOT_STALE",
            "no_unresolved_suspicious_return": r["suspicious_return_status"] != "UNRESOLVED",
            "no_higher_priority_blocker": r["higher_priority_blocker_status"] == "NONE",
            "anomaly_date_present": shape["anomaly_date"] in r["affected_dates"].split("|"),
            "canonical_ready": r["proposed_cache_state"] == "READY",
        }
        passed = all(checks.values())
        if not passed:
            raise RuntimeError(f"v0.52 validation case failed closed for {r['Source_WS_ID']}: {checks}")
        out.append({
            "Security_Key": r["Security_Key"],
            "Source_WS_ID": r["Source_WS_ID"],
            "Primary_MIC": r["Primary_MIC"],
            "Primary_Ticker": r["Primary_Ticker"],
            "raw_bar_count": r["raw_bar_count"],
            "valid_bar_count": r["valid_bar_count"],
            "invalid_bar_count": r["invalid_bar_count"],
            "invalid_share": r["invalid_share"],
            "affected_dates": r["affected_dates"],
            "suspicious_return_status": r["suspicious_return_status"],
            "higher_priority_blocker_status": r["higher_priority_blocker_status"],
            "canonical_qa_status": r["canonical_qa_status"],
            "canonical_qa_reason": r["canonical_qa_reason"],
            "proposed_cache_state": r["proposed_cache_state"],
            "proposed_reason": r["proposed_reason"],
            "Validation_Result": "PASS",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sqlite", required=True)
    ap.add_argument("--target-sqlite", required=True)
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_filtered_bar_policy_v0_53")
    ap.add_argument("--repository-sha", required=True)
    ap.add_argument("--as-of", required=True)
    args = ap.parse_args()

    as_of = date.fromisoformat(args.as_of)
    source = Path(args.source_sqlite)
    target = Path(args.target_sqlite)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)

    start = validate_start_authority(args.repository_sha)
    contract = canonical_contract()
    source_info = validate_source_runtime(source)
    no_special = assert_no_special_pleading(Path(__file__))
    synthetic = synthetic_policy_tests(as_of)
    feature_reg = feature_path_regression(as_of)
    lifecycle = byte_lifecycle_regression()

    shutil.copyfile(source, target)
    if Path(str(target) + "-wal").exists() or Path(str(target) + "-shm").exists():
        raise RuntimeError("unexpected sidecar after source runtime copy")

    rw = sqlite3.connect(target)
    if str(rw.execute("PRAGMA integrity_check").fetchone()[0]) != "ok":
        raise RuntimeError("copied runtime failed integrity_check")
    before_price_digest, before_price_rows = table_digest(rw, PRICE_DIGEST_SQL)
    before_mapping_digest, before_mapping_rows = table_digest(rw, MAPPING_DIGEST_SQL)
    if before_price_digest != source_info["price_daily_content_digest"] or before_price_rows != SOURCE_PRICE_ROWS:
        raise RuntimeError("pre-mutation raw-price digest differs from source authority")
    if before_mapping_digest != source_info["provider_mapping_digest"] or before_mapping_rows != SOURCE_STATES:
        raise RuntimeError("pre-mutation provider mapping digest differs from source authority")

    regression, excluded = full_frozen_regression(rw, as_of)
    validation_rows = validation_case_rows(regression)

    old_ready = [r for r in regression if r["old_cache_state"] == "READY"]
    ready_to_ready = sum(r["proposed_cache_state"] == "READY" for r in old_ready)
    ready_to_quarantine = sum(r["proposed_cache_state"] == "QUARANTINE" for r in old_ready)
    ready_to_other = len(old_ready) - ready_to_ready - ready_to_quarantine
    if len(old_ready) != SOURCE_READY:
        raise RuntimeError("existing READY population mismatch")
    if ready_to_quarantine or ready_to_other:
        bad = [r for r in old_ready if r["proposed_cache_state"] != "READY"]
        raise RuntimeError(f"unexpected degradation of existing READY population: {bad[:5]}")

    history_policy_version = contract["history_policy_version"]
    transitions = apply_regression_state(rw, regression, excluded, as_of, history_policy_version)

    after_price_digest_open, after_price_rows_open = table_digest(rw, PRICE_DIGEST_SQL)
    after_mapping_digest_open, after_mapping_rows_open = table_digest(rw, MAPPING_DIGEST_SQL)
    if (before_price_digest, before_price_rows) != (after_price_digest_open, after_price_rows_open):
        raise RuntimeError("price_daily changed during state/provenance implementation")
    if (before_mapping_digest, before_mapping_rows) != (after_mapping_digest_open, after_mapping_rows_open):
        raise RuntimeError("provider mapping changed during state/provenance implementation")

    open_counts = {str(k): int(v) for k, v in rw.execute(
        "SELECT status,COUNT(*) FROM cache_state GROUP BY status ORDER BY status"
    ).fetchall()}
    if open_counts != {"READY": FROZEN_ROWS}:
        raise RuntimeError(f"generic full-Frozen reconciliation exposed blockers: {open_counts}")

    provenance_security_rows = int(rw.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053").fetchone()[0])
    provenance_defect_rows = int(rw.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053 WHERE source_data_defect=1").fetchone()[0])
    exclusion_rows = int(rw.execute("SELECT COUNT(*) FROM technical_bar_exclusions_v053").fetchone()[0])
    if provenance_security_rows != FROZEN_ROWS or exclusion_rows != len(excluded):
        raise RuntimeError("provenance persistence row mismatch")

    binding = finalize_sqlite_for_binding(rw, target)

    post = connect_ro(target)
    try:
        integrity = str(post.execute("PRAGMA integrity_check").fetchone()[0])
        final_price_digest, final_price_rows = table_digest(post, PRICE_DIGEST_SQL)
        final_mapping_digest, final_mapping_rows = table_digest(post, MAPPING_DIGEST_SQL)
        final_states = int(post.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        final_counts = {str(k): int(v) for k, v in post.execute(
            "SELECT status,COUNT(*) FROM cache_state GROUP BY status ORDER BY status"
        ).fetchall()}
        prov_count = int(post.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053").fetchone()[0])
        exclusion_count = int(post.execute("SELECT COUNT(*) FROM technical_bar_exclusions_v053").fetchone()[0])
        final_state_df = pd.read_sql_query(
            "SELECT ws_id,yahoo_symbol,mapping_status,status,coalesce(reason_code,'') reason_code,"
            "unique_bars,valid_bars,repaired_rows,suspicious_returns,zero_volume_share,"
            "first_bar_date,last_bar_date,last_fetch_utc,batch_id,coalesce(last_error,'') last_error "
            "FROM cache_state ORDER BY ws_id",
            post,
        )
    finally:
        post.close()

    if integrity != "ok":
        raise RuntimeError("final runtime integrity_check failed")
    if final_price_rows != SOURCE_PRICE_ROWS or final_price_digest != before_price_digest:
        raise RuntimeError("final price_daily immutability failed")
    if final_mapping_rows != SOURCE_STATES or final_mapping_digest != before_mapping_digest:
        raise RuntimeError("final provider mapping immutability failed")
    if final_states != FROZEN_ROWS or final_counts != {"READY": FROZEN_ROWS}:
        raise RuntimeError("final cache state reconciliation failed")
    if prov_count != FROZEN_ROWS or exclusion_count != len(excluded):
        raise RuntimeError("final provenance tables failed")
    if frozen_digest() != FROZEN_SHA256:
        raise RuntimeError("Frozen mutated")

    regression_fields = list(regression[0].keys())
    write_csv(out / "full_frozen_regression_v0.53.csv", regression_fields, regression)
    write_csv(out / "state_transitions_v0.53.csv", list(transitions[0].keys()) if transitions else [
        "Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker","Provider_Symbol",
        "Status_Before","Reason_Before","Status_After","Reason_After","State_Change_Reason",
        "invalid_bar_count","invalid_share","affected_dates"
    ], transitions)
    write_csv(out / "asx8_validation_v0.53.csv", list(validation_rows[0].keys()), validation_rows)
    write_csv(out / "defect_provenance_v0.53.csv", list(excluded[0].keys()) if excluded else [
        "Source_WS_ID","Security_Key","Observation_Date","SOURCE_DATA_DEFECT","TECHNICAL_BAR_EXCLUDED",
        "Reason_Codes","Core_QA_Policy","Implementation_Policy"
    ], excluded)
    write_csv(out / "feature_path_regression_v0.53.csv", ["Test","Result","Detail"], feature_reg)
    write_csv(out / "boundary_negative_tests_v0.53.csv", ["Test","Result","Detail"], synthetic)

    frozen_by = {r["Source_WS_ID"]: r for r in read_csv(FROZEN_PATH)}
    final_rows: list[dict[str, Any]] = []
    for r in final_state_df.to_dict("records"):
        fr = frozen_by[str(r["ws_id"])]
        final_rows.append({
            "Projection_Order": int(fr["Projection_Order"]),
            "Security_Key": fr["Security_Key"],
            "Source_WS_ID": str(r["ws_id"]),
            "Primary_MIC": fr["Primary_MIC"],
            "Primary_Ticker": fr["Primary_Ticker"],
            "Provider_Symbol": str(r["yahoo_symbol"] or ""),
            "Mapping_Status": str(r["mapping_status"] or ""),
            "Price_Cache_Status": str(r["status"] or ""),
            "Reason_Code": str(r["reason_code"] or ""),
            "Unique_Bars": int(r["unique_bars"]),
            "Valid_Bars": int(r["valid_bars"]),
            "Suspicious_Returns": int(r["suspicious_returns"]),
            "Last_Bar_Date": str(r["last_bar_date"] or ""),
        })
    final_rows.sort(key=lambda x: x["Projection_Order"])
    write_csv(out / "final_cache_state_v0.53.csv", list(final_rows[0].keys()), final_rows)

    contract_binding = {
        "stage": "P0_FROZEN_1425_CANONICAL_FILTERED_INVALID_BAR_POLICY_F_IMPLEMENTATION",
        "version": VERSION,
        "implementation_policy": IMPLEMENTATION_POLICY_ID,
        "core_policy": CORE_POLICY_ID,
        "canonical_contract": contract,
        "source_runtime": {
            "sha256": SOURCE_RUNTIME_SHA256,
            "bytes": SOURCE_RUNTIME_BYTES,
            "price_daily_rows": SOURCE_PRICE_ROWS,
            "states": SOURCE_STATES,
            "ready": SOURCE_READY,
            "quarantine": SOURCE_QUARANTINE,
        },
        "history_qa_reopened": False,
        "liquidity_qa_reopened": False,
        "threshold_changes": 0,
    }
    (out / "contract_binding_v0.53.json").write_text(json.dumps(contract_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    raw_immutability = {
        "price_daily_rows_before": before_price_rows,
        "price_daily_rows_after_open_mutation": after_price_rows_open,
        "price_daily_rows_after_close": final_price_rows,
        "price_daily_digest_before": before_price_digest,
        "price_daily_digest_after_open_mutation": after_price_digest_open,
        "price_daily_digest_after_close": final_price_digest,
        "unchanged": before_price_digest == after_price_digest_open == final_price_digest and before_price_rows == after_price_rows_open == final_price_rows,
        "provider_mapping_digest_before": before_mapping_digest,
        "provider_mapping_digest_after_open_mutation": after_mapping_digest_open,
        "provider_mapping_digest_after_close": final_mapping_digest,
        "provider_mapping_unchanged": before_mapping_digest == after_mapping_digest_open == final_mapping_digest,
    }
    (out / "raw_price_immutability_v0.53.json").write_text(json.dumps(raw_immutability, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    runtime_binding = {
        "source_runtime_sha256": SOURCE_RUNTIME_SHA256,
        "source_runtime_bytes": SOURCE_RUNTIME_BYTES,
        "declared_runtime_sha256": binding["sha256_pass_1"],
        "declared_runtime_bytes": binding["bytes_pass_1"],
        "hash_pass_1": binding["sha256_pass_1"],
        "hash_pass_2": binding["sha256_pass_2"],
        "prepackage_hash_repeat_equal": binding["sha256_pass_1"] == binding["sha256_pass_2"],
        "journal_mode_before_close": binding["journal_mode_before_close"],
        "wal_checkpoint_result": binding["wal_checkpoint_result"],
        "hash_after_close": binding["hash_after_close"],
        "integrity_check": integrity,
        "price_daily_rows": final_price_rows,
        "states": final_states,
        "status_counts": final_counts,
        "packaged_runtime_sha256": "PENDING_POST_UPLOAD_VERIFICATION",
        "packaged_runtime_bytes": "PENDING_POST_UPLOAD_VERIFICATION",
    }
    (out / "runtime_hash_binding_preupload_v0.53.json").write_text(json.dumps(runtime_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    tests = synthetic + feature_reg + [
        {"Test": "CANONICAL_THRESHOLD_IDENTITY", "Result": "PASS", "Detail": json.dumps(contract, sort_keys=True)},
        {"Test": "NO_SPECIAL_PLEADING", "Result": "PASS", "Detail": json.dumps(no_special, sort_keys=True)},
        {"Test": "RAW_PRICE_IMMUTABILITY", "Result": "PASS" if raw_immutability["unchanged"] else "FAIL", "Detail": before_price_digest},
        {"Test": "FROZEN_IMMUTABILITY", "Result": "PASS", "Detail": FROZEN_SHA256},
        {"Test": "PROVIDER_MAPPING_IMMUTABILITY", "Result": "PASS" if raw_immutability["provider_mapping_unchanged"] else "FAIL", "Detail": before_mapping_digest},
        {"Test": "BYTE_LIFECYCLE_REGRESSION", "Result": "PASS", "Detail": json.dumps(lifecycle, sort_keys=True)},
        {"Test": "FULL_FROZEN_1425_RECONCILIATION", "Result": "PASS" if final_counts == {"READY": FROZEN_ROWS} else "FAIL", "Detail": json.dumps(final_counts, sort_keys=True)},
        {"Test": "NO_PRODUCTIVE_P0", "Result": "PASS", "Detail": "p0_run=false; feature_materialization=false; rs=false; parameter_promotion=false"},
    ]
    write_csv(out / "test_results_v0.53.csv", ["Test","Result","Detail"], tests)
    if any(r["Result"] != "PASS" for r in tests):
        raise RuntimeError("one or more implementation tests failed")

    summary = {
        "stage": "P0_FROZEN_1425_CANONICAL_FILTERED_INVALID_BAR_POLICY_F_IMPLEMENTATION",
        "version": VERSION,
        "status": "PREUPLOAD_PASS",
        "required_start_head": REQUIRED_START_HEAD,
        "implementation_commit": start["head"],
        "implementation_policy": IMPLEMENTATION_POLICY_ID,
        "canonical_contract": contract,
        "full_frozen": {
            "rows": len(regression),
            "ready_to_ready": ready_to_ready,
            "ready_to_quarantine": ready_to_quarantine,
            "ready_to_other": ready_to_other,
            "transitions": len(transitions),
            "source_data_defect_securities": provenance_defect_rows,
            "technical_bar_exclusions": exclusion_rows,
        },
        "final_cache": {"READY": FROZEN_ROWS, "QUARANTINE": 0, "total": FROZEN_ROWS},
        "p0_price_cache_ready_preupload": True,
        "p0_price_cache_ready": False,
        "pending_only": "post-upload packaged runtime byte verification",
        "raw_price_immutability": raw_immutability,
        "runtime_preupload": runtime_binding,
        "frozen_sha256": FROZEN_SHA256,
        "history_qa_reopened": False,
        "liquidity_qa_reopened": False,
        "market_provider_calls": 0,
        "yahoo_yfinance_calls": 0,
        "eodhd_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "p0_run": False,
        "feature_materialization": False,
        "rs_materialization": False,
        "parameter_promotion": False,
        "universe_mutation": False,
        "productive": False,
        "next_gate_if_byte_binding_passes": "P0 FROZEN-1425 FEATURE MATERIALIZATION / CAPABILITY GATE",
    }
    (out / "summary_preupload_v0.53.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = {
        "stage": summary["stage"],
        "version": VERSION,
        "status": "PREUPLOAD_PASS",
        "tests_total": len(tests),
        "tests_passed": sum(r["Result"] == "PASS" for r in tests),
        "tests_failed": sum(r["Result"] != "PASS" for r in tests),
        "ready": FROZEN_ROWS,
        "quarantine": 0,
        "raw_price_digest_unchanged": raw_immutability["unchanged"],
        "provider_mapping_unchanged": raw_immutability["provider_mapping_unchanged"],
        "frozen_unchanged": frozen_digest() == FROZEN_SHA256,
        "p0_run": False,
        "productive": False,
        "pending_only": "post-upload packaged runtime byte verification",
    }
    (out / "stage_checkpoint_preupload_v0.53.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_files = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            manifest_files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    manifest = {
        "stage": summary["stage"],
        "version": VERSION,
        "repository_sha": start["head"],
        "required_start_head": REQUIRED_START_HEAD,
        "source_runtime_sha256": SOURCE_RUNTIME_SHA256,
        "source_runtime_bytes": SOURCE_RUNTIME_BYTES,
        "target_runtime_sha256": binding["sha256_pass_1"],
        "target_runtime_bytes": binding["bytes_pass_1"],
        "files": manifest_files,
        "runtime_artifact": "PENDING_POST_UPLOAD_VERIFICATION",
        "market_provider_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "p0_run": False,
        "universe_mutation": False,
        "productive": False,
    }
    (out / "manifest_preupload_v0.53.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PREUPLOAD_PASS",
        "ready": FROZEN_ROWS,
        "quarantine": 0,
        "transitions": len(transitions),
        "source_data_defect_securities": provenance_defect_rows,
        "excluded_bars": exclusion_rows,
        "runtime_sha256": binding["sha256_pass_1"],
        "runtime_bytes": binding["bytes_pass_1"],
        "p0_price_cache_ready_preupload": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
