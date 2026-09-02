#!/usr/bin/env python3
"""v0.39 DATA_GAP_AUDIT_ONLY for the frozen v0.38 1,633-row research partial.

DEV / RESEARCH / SHADOW ONLY.

This stage is deliberately offline. It reads the frozen v0.38 result ledgers and
frozen SQLite stock cache, classifies the remaining data gaps, and writes a
remediation plan. It performs no provider search, no stock/FX download, no
mapping override, no universe mutation, no eligibility promotion, no P0, no
sector RS and no SWING_U3K_FROZEN mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import subprocess
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(".")
VERSION = "v0.39"
STAGE = "CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION"
MODE = "DATA_GAP_AUDIT_ONLY"
DEFAULT_CONFIG = ROOT / "config/current_master_research_partial_1633_data_gap_remediation_v0.39.json"
OUT = ROOT / "output_current_master_research_partial_1633_data_gap_remediation_v0_39"
UTC = timezone.utc

NETWORK_ALLOWED = False
STOCK_DOWNLOAD_ALLOWED = False
FX_DOWNLOAD_ALLOWED = False
PROVIDER_SEARCH_ALLOWED = False
AUTOMATIC_MAPPING_OVERRIDE_ALLOWED = False
UNIVERSE_MUTATION_ALLOWED = False
ELIGIBILITY_PROMOTION_ALLOWED = False
P0_ALLOWED = False
SECTOR_RS_ALLOWED = False
SWING_U3K_FROZEN_MUTATION_ALLOWED = False
PRODUCTIVE_ALLOWED = False


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def inum(v: Any, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def fnum(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], text=True).strip()


def git_ancestor(sha: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], check=False).returncode == 0


def counts(series: pd.Series) -> dict[str, int]:
    return {str(k): int(v) for k, v in series.fillna("NULL").value_counts(dropna=False).to_dict().items()}


class FrozenReadOnlyCache:
    def __init__(self, path: Path):
        self.path = path
        resolved = path.resolve()
        self.conn = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
        self.conn.execute("PRAGMA query_only=ON")

    def load_price_frame(self, ws_id: str) -> pd.DataFrame:
        frame = pd.read_sql_query(
            """
            SELECT day,open,high,low,close,adj_close,volume,
                   dividends,stock_splits,repaired
            FROM price_daily
            WHERE ws_id=?
            ORDER BY day
            """,
            self.conn,
            params=[ws_id],
        )
        if frame.empty:
            return frame
        frame["day"] = pd.to_datetime(frame["day"], errors="coerce")
        return frame.dropna(subset=["day"]).sort_values("day").reset_index(drop=True)

    def close(self) -> None:
        self.conn.close()


def validate_frozen_cache(cfg: dict[str, Any]) -> dict[str, Any]:
    path = Path(cfg["frozen_cache_path"])
    require(path.is_file(), f"FROZEN_CACHE_MISSING:{path}")
    sha = sha256_file(path)
    require(sha == cfg["frozen_cache_sha256"], f"FROZEN_CACHE_SHA_MISMATCH:{sha}")
    expected = {k: int(v) for k, v in cfg["frozen_cache_counts"].items()}
    with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as conn:
        actual = {k: int(conn.execute(f"SELECT COUNT(*) FROM {k}").fetchone()[0]) for k in expected}
    require(actual == expected, f"FROZEN_CACHE_COUNT_MISMATCH:{actual}")
    return {"path": str(path), "sha256": sha, "counts": actual}


def validate_frozen_inputs(cfg: dict[str, Any]) -> None:
    require(cfg.get("stage") == STAGE, "CONFIG_STAGE_MISMATCH")
    require(cfg.get("version") == VERSION, "CONFIG_VERSION_MISMATCH")
    require(cfg.get("run_mode") == MODE, "CONFIG_MODE_MISMATCH")
    require(cfg.get("network_allowed") is False, "NETWORK_MUST_BE_DISABLED")
    require(cfg.get("stock_download_allowed") is False, "STOCK_DOWNLOAD_MUST_BE_DISABLED")
    require(cfg.get("fx_download_allowed") is False, "FX_DOWNLOAD_MUST_BE_DISABLED")
    require(cfg.get("provider_search_allowed") is False, "PROVIDER_SEARCH_MUST_BE_DISABLED")
    require(cfg.get("automatic_mapping_override_allowed") is False, "AUTO_OVERRIDE_MUST_BE_DISABLED")
    require(cfg.get("universe_mutation_allowed") is False, "UNIVERSE_MUTATION_MUST_BE_DISABLED")
    require(cfg.get("eligibility_promotion_allowed") is False, "ELIGIBILITY_PROMOTION_MUST_BE_DISABLED")
    require(git_ancestor(cfg["source_result_commit"]), "SOURCE_RESULT_COMMIT_NOT_IN_HISTORY")
    for path, expected in cfg["frozen_input_blobs"].items():
        actual = git_blob(path)
        require(actual == expected, f"FROZEN_INPUT_BLOB_MISMATCH:{path}:{actual}!={expected}")
    workflow_path = Path(cfg["audit_workflow_path"])
    require(workflow_path.is_file(), f"AUDIT_WORKFLOW_MISSING:{workflow_path}")
    workflow_text = workflow_path.read_text(encoding="utf-8")
    require("workflow_dispatch:" in workflow_text, "AUDIT_WORKFLOW_MANUAL_DISPATCH_MISSING")
    for forbidden in ("\n  push:", "\n  schedule:", "\n  pull_request:", "\n  repository_dispatch:"):
        require(forbidden not in workflow_text, f"AUDIT_WORKFLOW_NON_MANUAL_TRIGGER_FORBIDDEN:{forbidden.strip()}")
    require(cfg.get("workflow_execution_allowed") is True, "AUDIT_WORKFLOW_EXECUTION_NOT_AUTHORIZED")
    require(cfg.get("workflow_trigger_policy") == "MANUAL_DISPATCH_ONLY", "AUDIT_WORKFLOW_TRIGGER_POLICY_MISMATCH")


def valid_mask(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=bool)
    def n(col: str) -> pd.Series:
        return pd.to_numeric(frame[col], errors="coerce")
    o, h, l, c, v = n("open"), n("high"), n("low"), n("close"), n("volume")
    finite = pd.concat([o, h, l, c], axis=1).replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    positive = (pd.concat([o, h, l, c], axis=1) > 0).all(axis=1)
    relation = (h >= l) & (c <= h) & (c >= l)
    nonnegative_volume = ~((v < 0) & v.notna())
    return finite & positive & relation & nonnegative_volume


def suspicious_events(frame: pd.DataFrame, threshold: float, split_window_rows: int) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    x = frame.sort_values("day").reset_index(drop=True).copy()
    close = pd.to_numeric(x["close"], errors="coerce")
    ret = close.pct_change()
    splits = pd.to_numeric(x.get("stock_splits", pd.Series(0.0, index=x.index)), errors="coerce").fillna(0.0)
    out: list[dict[str, Any]] = []
    for pos in x.index[ret.abs() > threshold]:
        lo = max(0, int(pos) - split_window_rows)
        hi = min(len(x), int(pos) + split_window_rows + 1)
        split_nearby = bool((splits.iloc[lo:hi] > 0).any())
        out.append(
            {
                "day": pd.Timestamp(x.loc[pos, "day"]).date().isoformat(),
                "return": float(ret.loc[pos]),
                "close": fnum(x.loc[pos, "close"], float("nan")),
                "previous_close": fnum(x.loc[pos - 1, "close"], float("nan")) if pos > 0 else None,
                "split_nearby": split_nearby,
            }
        )
    return out


def symbol_relation(prior_symbol: str, candidate_symbol: str) -> str:
    p = txt(prior_symbol)
    c = txt(candidate_symbol)
    if p == c:
        return "EXACT"
    if p.upper() == c.upper():
        return "CASE_ONLY"
    pbase, psuf = (p.rsplit(".", 1) + [""])[:2] if "." in p else (p, "")
    cbase, csuf = (c.rsplit(".", 1) + [""])[:2] if "." in c else (c, "")
    if pbase.upper() == cbase.upper() and psuf.upper() != csuf.upper():
        return "SUFFIX_CHANGED"
    if psuf.upper() == csuf.upper() and pbase.upper() != cbase.upper():
        return "BASE_CHANGED"
    return "OTHER_TRANSFORM"


def mapping_audit_row(r: pd.Series) -> dict[str, Any]:
    relation = symbol_relation(r.get("Prior_Yahoo_Symbol", ""), r.get("Candidate_Yahoo_Symbol", ""))
    if relation == "EXACT":
        classification = "EXACT_PROVIDER_SYMBOL_NO_DATA"
        disposition = "RETRY_DATA"
        action = "CONTROLLED_RETRY_SAME_PROVIDER_SYMBOL_ONLY"
    elif relation == "CASE_ONLY":
        classification = "CASE_NORMALIZATION_SUSPECT"
        disposition = "MANUAL_REVIEW"
        action = "VERIFY_PRIMARY_LISTING_AND_PROVIDER_CASE_BEFORE_EXPLICIT_OVERRIDE"
    elif relation == "SUFFIX_CHANGED":
        classification = "SUFFIX_MAPPING_SUSPECT"
        disposition = "MANUAL_REVIEW"
        action = "VERIFY_PRIMARY_LISTING_AND_PROVIDER_SUFFIX_BEFORE_EXPLICIT_OVERRIDE"
    else:
        classification = "STATIC_MAPPING_TRANSFORM_REVIEW"
        disposition = "MANUAL_REVIEW"
        action = "VERIFY_PRIMARY_LISTING_AND_PROVIDER_SYMBOL_BEFORE_EXPLICIT_OVERRIDE"
    return {
        "WS_ID": txt(r.get("WS_ID")),
        "Gap_Family": "MAPPING",
        "Segment_ID": txt(r.get("Segment_ID")),
        "Primary_MIC": txt(r.get("Primary_MIC")),
        "Primary_Ticker": txt(r.get("Primary_Ticker")),
        "Primary_Currency": txt(r.get("Primary_Currency")),
        "Source_State": txt(r.get("Mapping_Current_State")),
        "Source_Reason": txt(r.get("Mapping_Current_Reason")),
        "Prior_Yahoo_Symbol": txt(r.get("Prior_Yahoo_Symbol")),
        "Candidate_Yahoo_Symbol": txt(r.get("Candidate_Yahoo_Symbol")),
        "Static_Symbol_Relation": relation,
        "Diagnostic_Classification": classification,
        "Disposition": disposition,
        "Recommended_Action": action,
        "Auto_Fix_Safe": False,
        "Candidate_Override": "",
        "Terminal_Blocked": False,
        "Network_Required_For_Next_Step": True,
    }


def dq_audit_row(r: pd.Series, h: pd.Series, px: pd.DataFrame, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    reason = txt(r.get("Reason")).upper()
    vm = valid_mask(px) if not px.empty else pd.Series(dtype=bool)
    invalid = px.loc[~vm].copy() if not px.empty and len(vm) else pd.DataFrame()
    susp = suspicious_events(px, float(cfg["suspicious_abs_return"]), int(cfg["split_window_rows"]))
    raw = len(px)
    invalid_count = len(invalid)
    invalid_share = (invalid_count / raw) if raw else 1.0
    unique_bars = inum(h.get("Unique_Daily_Bars"))
    valid_bars = inum(h.get("Valid_Completed_Bars"))
    repaired_rows = inum(h.get("Repaired_Rows"))

    if reason == "INVALID_OHLC_OR_VOLUME":
        filterable = (
            raw > 0
            and invalid_count <= int(cfg["isolated_invalid_bar_max_count"])
            and invalid_share <= float(cfg["isolated_invalid_bar_max_share"])
            and unique_bars >= int(cfg["min_unique_bars"])
            and valid_bars >= int(cfg["min_valid_bars"])
        )
        if filterable:
            classification = "LIKELY_ISOLATED_INVALID_BARS_FILTERABLE"
            disposition = "MANUAL_REVIEW"
            action = "QA_FILTER_POLICY_REVIEW_BEFORE_ANY_REDOWNLOAD"
        else:
            classification = "INVALID_BAR_TARGETED_REPAIR_CANDIDATE"
            disposition = "RETRY_DATA"
            action = "TARGETED_SINGLE_SYMBOL_REDOWNLOAD_REPAIR_AND_QA_RECHECK"
    elif reason == "SUSPICIOUS_RETURN_NEEDS_REPAIR":
        if susp and all(bool(e["split_nearby"]) for e in susp):
            classification = "LIKELY_SPLIT_OR_CORPORATE_ACTION"
            disposition = "MANUAL_REVIEW"
            action = "VERIFY_CORPORATE_ACTION_BEFORE_QA_REQUALIFICATION"
        else:
            classification = "SUSPICIOUS_RETURN_TARGETED_REPAIR_CANDIDATE"
            disposition = "RETRY_DATA"
            action = "TARGETED_SINGLE_SYMBOL_REPAIR_THEN_EVENT_QA_RECHECK"
    else:
        classification = "DATA_QUALITY_REVIEW_REQUIRED"
        disposition = "MANUAL_REVIEW"
        action = "KEEP_QUARANTINE_PENDING_DIAGNOSIS"

    invalid_events = [
        {
            "WS_ID": txt(r.get("WS_ID")),
            "day": pd.Timestamp(x["day"]).date().isoformat() if pd.notna(x.get("day")) else "",
            "open": x.get("open"),
            "high": x.get("high"),
            "low": x.get("low"),
            "close": x.get("close"),
            "volume": x.get("volume"),
        }
        for _, x in invalid.iterrows()
    ]
    suspicious_rows = [{"WS_ID": txt(r.get("WS_ID")), **e} for e in susp]

    row = {
        "WS_ID": txt(r.get("WS_ID")),
        "Gap_Family": "DATA_QUALITY",
        "Source_State": txt(h.get("History_Current_State")),
        "Source_Reason": reason,
        "Yahoo_Symbol": txt(h.get("Yahoo_Symbol")),
        "Cache_Status": txt(h.get("Cache_Status")),
        "Cache_Reason": txt(h.get("Cache_Reason")),
        "Unique_Daily_Bars": unique_bars,
        "Valid_Completed_Bars": valid_bars,
        "Repaired_Rows": repaired_rows,
        "Cached_Price_Rows": raw,
        "Invalid_Cached_Bars": invalid_count,
        "Invalid_Cached_Bar_Share": invalid_share,
        "Suspicious_Return_Events_Recomputed": len(susp),
        "All_Suspicious_Events_Have_Split_Nearby": bool(susp) and all(bool(e["split_nearby"]) for e in susp),
        "Diagnostic_Classification": classification,
        "Disposition": disposition,
        "Recommended_Action": action,
        "Auto_Fix_Safe": False,
        "Terminal_Blocked": False,
        "Network_Required_For_Next_Step": disposition == "RETRY_DATA",
    }
    return row, invalid_events, suspicious_rows


def history_audit_row(h: pd.Series) -> dict[str, Any]:
    unique_bars = inum(h.get("Unique_Daily_Bars"))
    valid_bars = inum(h.get("Valid_Completed_Bars"))
    return {
        "WS_ID": txt(h.get("WS_ID")),
        "Gap_Family": "HISTORY",
        "Source_State": txt(h.get("History_Current_State")),
        "Source_Reason": txt(h.get("Cache_Reason")),
        "Yahoo_Symbol": txt(h.get("Yahoo_Symbol")),
        "Cache_Status": txt(h.get("Cache_Status")),
        "Unique_Daily_Bars": unique_bars,
        "Valid_Completed_Bars": valid_bars,
        "First_Valid_Bar": txt(h.get("First_Valid_Bar")),
        "Last_Completed_Bar": txt(h.get("Last_Completed_Bar")),
        "Bars_To_260": max(0, 260 - unique_bars),
        "Bars_To_252_Valid": max(0, 252 - valid_bars),
        "Diagnostic_Classification": "STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES",
        "Disposition": "DEFER_TEMPORAL",
        "Recommended_Action": "KEEP_WARMUP_NO_REPAIR",
        "Auto_Fix_Safe": False,
        "Terminal_Blocked": False,
        "Network_Required_For_Next_Step": False,
    }


def protected_instrument_rows(mapping: pd.DataFrame) -> list[dict[str, Any]]:
    x = mapping[mapping["Mapping_Current_State"] == "MAPPING_NOT_REQUESTED_INSTRUMENT_FAIL"].copy()
    rows: list[dict[str, Any]] = []
    for _, r in x.iterrows():
        rows.append(
            {
                "WS_ID": txt(r.get("WS_ID")),
                "Segment_ID": txt(r.get("Segment_ID")),
                "Primary_MIC": txt(r.get("Primary_MIC")),
                "Primary_Ticker": txt(r.get("Primary_Ticker")),
                "Primary_Currency": txt(r.get("Primary_Currency")),
                "Mapping_Current_State": txt(r.get("Mapping_Current_State")),
                "Mapping_Current_Reason": txt(r.get("Mapping_Current_Reason")),
                "Audit_Action": "PROTECTED_INSTRUMENT_FAIL_NO_DATA_REMEDIATION",
                "Included_In_Audit_Target_249": False,
            }
        )
    return rows


def run_audit(config_path: Path) -> dict[str, Any]:
    cfg = read_json(config_path)
    validate_frozen_inputs(cfg)
    cache_before = validate_frozen_cache(cfg)

    source = Path(cfg["source_output_dir"])
    mapping = pd.read_csv(source / "mapping_revalidation_1633_v0.38.csv", dtype=str, keep_default_na=False)
    mapping_queue = pd.read_csv(source / "mapping_remediation_queue_v0.38.csv", dtype=str, keep_default_na=False)
    history = pd.read_csv(source / "history_gate_current_1633_v0.38.csv", dtype=str, keep_default_na=False)
    dq = pd.read_csv(source / "data_quality_exceptions_v0.38.csv", dtype=str, keep_default_na=False)
    readiness = pd.read_csv(source / "current_data_readiness_1633_v0.38.csv", dtype=str, keep_default_na=False)
    summary38 = read_json(source / "summary_v0.38.json")

    exp = cfg["expected_source_counts"]
    require(len(mapping) == 1633 and mapping["WS_ID"].nunique() == 1633, "MAPPING_1633_GATE")
    require(len(mapping_queue) == int(exp["mapping_gap"]), "MAPPING_GAP_COUNT_GATE")
    require(len(dq) == int(exp["data_quality_gap"]), "DQ_GAP_COUNT_GATE")
    short_history = history[history["History_Current_State"] == "INSUFFICIENT_HISTORY_FOR_STANDARD_U3K"].copy()
    require(len(short_history) == int(exp["history_gap"]), "HISTORY_GAP_COUNT_GATE")
    protected = protected_instrument_rows(mapping)
    require(len(protected) == int(exp["instrument_fail_protected"]), "INSTRUMENT_FAIL_PROTECTED_COUNT_GATE")
    require(int((readiness["Data_Readiness_Current"] == "READY_FOR_ELIGIBILITY_RECOMPUTE").sum()) == int(exp["ready"]), "READY_COUNT_GATE")
    require(summary38["fx_unresolved_currencies"] == [], "SOURCE_FX_MUST_BE_CLEAN")

    map_ids = set(mapping_queue["WS_ID"])
    dq_ids = set(dq["WS_ID"])
    hist_ids = set(short_history["WS_ID"])
    require(not (map_ids & dq_ids or map_ids & hist_ids or dq_ids & hist_ids), "AUDIT_TARGET_FAMILIES_MUST_BE_DISJOINT")
    require(len(map_ids | dq_ids | hist_ids) == int(exp["audit_target_total"]), "AUDIT_TARGET_TOTAL_GATE")

    mapping_rows = [mapping_audit_row(r) for _, r in mapping_queue.iterrows()]
    hist_index = history.set_index("WS_ID", drop=False)
    cache = FrozenReadOnlyCache(Path(cfg["frozen_cache_path"]))
    dq_rows: list[dict[str, Any]] = []
    invalid_events: list[dict[str, Any]] = []
    suspicious_rows: list[dict[str, Any]] = []
    try:
        for _, r in dq.iterrows():
            ws = txt(r.get("WS_ID"))
            require(ws in hist_index.index, f"DQ_HISTORY_JOIN_MISSING:{ws}")
            h = hist_index.loc[ws]
            px = cache.load_price_frame(ws)
            row, bad, susp = dq_audit_row(r, h, px, cfg)
            dq_rows.append(row)
            invalid_events.extend(bad)
            suspicious_rows.extend(susp)
    finally:
        cache.close()

    history_rows = [history_audit_row(r) for _, r in short_history.iterrows()]
    all_rows = mapping_rows + dq_rows + history_rows
    priority = {"MANUAL_REVIEW": 1, "RETRY_DATA": 2, "DEFER_TEMPORAL": 3, "AUTO_FIX_SAFE": 0, "TERMINAL_BLOCKED": 4}
    all_rows = sorted(all_rows, key=lambda x: (priority.get(txt(x.get("Disposition")), 9), txt(x.get("Gap_Family")), txt(x.get("WS_ID"))))

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "mapping_gap_audit_239_v0.39.csv", mapping_rows)
    write_csv(OUT / "data_quality_gap_audit_7_v0.39.csv", dq_rows)
    write_csv(OUT / "history_gap_audit_3_v0.39.csv", history_rows)
    write_csv(OUT / "protected_instrument_fail_19_v0.39.csv", protected)
    write_csv(OUT / "data_gap_audit_249_v0.39.csv", all_rows)
    write_csv(OUT / "remediation_queue_v0.39.csv", all_rows)
    write_csv(OUT / "invalid_bar_events_v0.39.csv", invalid_events)
    write_csv(OUT / "suspicious_return_events_v0.39.csv", suspicious_rows)

    cache_after = validate_frozen_cache(cfg)
    require(cache_before["sha256"] == cache_after["sha256"], "CACHE_CHANGED_DURING_AUDIT")

    dispositions = Counter(txt(r.get("Disposition")) for r in all_rows)
    families = Counter(txt(r.get("Gap_Family")) for r in all_rows)
    classifications = Counter(txt(r.get("Diagnostic_Classification")) for r in all_rows)
    dq_reason_counts = Counter(txt(r.get("Source_Reason")) for r in dq_rows)

    summary = {
        "stage": STAGE,
        "version": VERSION,
        "run_mode": MODE,
        "status": "DEV / RESEARCH / SHADOW – NOT PRODUCTIVE",
        "source_result_commit": cfg["source_result_commit"],
        "source_v0_38_ready": int(exp["ready"]),
        "audit_target_count": len(all_rows),
        "gap_family_counts": dict(sorted(families.items())),
        "disposition_counts": dict(sorted(dispositions.items())),
        "classification_counts": dict(sorted(classifications.items())),
        "data_quality_reason_counts": dict(sorted(dq_reason_counts.items())),
        "protected_instrument_fail_count": len(protected),
        "automatic_fix_count": int(dispositions.get("AUTO_FIX_SAFE", 0)),
        "terminal_blocked_count": int(dispositions.get("TERMINAL_BLOCKED", 0)),
        "network_allowed": NETWORK_ALLOWED,
        "network_request_count": 0,
        "stock_download_allowed": STOCK_DOWNLOAD_ALLOWED,
        "stock_download_executed": False,
        "fx_download_allowed": FX_DOWNLOAD_ALLOWED,
        "fx_download_executed": False,
        "provider_search_allowed": PROVIDER_SEARCH_ALLOWED,
        "provider_search_executed": False,
        "cache_read_only": True,
        "cache_sha_before": cache_before["sha256"],
        "cache_sha_after": cache_after["sha256"],
        "automatic_mapping_override_allowed": AUTOMATIC_MAPPING_OVERRIDE_ALLOWED,
        "automatic_mapping_override_created": False,
        "universe_mutation_allowed": UNIVERSE_MUTATION_ALLOWED,
        "universe_mutated": False,
        "eligibility_promotion_allowed": ELIGIBILITY_PROMOTION_ALLOWED,
        "eligibility_promoted": False,
        "p0": P0_ALLOWED,
        "sector_rs": SECTOR_RS_ALLOWED,
        "swing_u3k_frozen_mutated": SWING_U3K_FROZEN_MUTATION_ALLOWED,
        "productive": PRODUCTIVE_ALLOWED,
        "audit_timestamp_utc": now_utc(),
        "next_stage": "CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_DATA_GAP_REMEDIATION",
    }
    write_json(OUT / "summary_v0.39.json", summary)
    write_json(
        OUT / "stage_checkpoint_v0.39.json",
        {
            "stage": STAGE,
            "version": VERSION,
            "run_mode": MODE,
            "completed": True,
            "strong_gates_required": True,
            "source_result_commit": cfg["source_result_commit"],
            "next_stage": summary["next_stage"],
        },
    )
    write_json(
        OUT / "manifest_v0.39.json",
        {
            "stage": STAGE,
            "version": VERSION,
            "run_mode": MODE,
            "source_result_commit": cfg["source_result_commit"],
            "outputs": sorted(p.name for p in OUT.iterdir()),
            "frozen_input_blobs": cfg["frozen_input_blobs"],
            "frozen_cache": cache_after,
            "network_request_count": 0,
            "productive": False,
        },
    )
    return summary


def strong_gates(config_path: Path) -> None:
    cfg = read_json(config_path)
    validate_frozen_inputs(cfg)
    cache = validate_frozen_cache(cfg)
    exp = cfg["expected_source_counts"]

    mapping = pd.read_csv(OUT / "mapping_gap_audit_239_v0.39.csv", dtype=str, keep_default_na=False)
    dq = pd.read_csv(OUT / "data_quality_gap_audit_7_v0.39.csv", dtype=str, keep_default_na=False)
    hist = pd.read_csv(OUT / "history_gap_audit_3_v0.39.csv", dtype=str, keep_default_na=False)
    protected = pd.read_csv(OUT / "protected_instrument_fail_19_v0.39.csv", dtype=str, keep_default_na=False)
    audit = pd.read_csv(OUT / "data_gap_audit_249_v0.39.csv", dtype=str, keep_default_na=False)
    queue = pd.read_csv(OUT / "remediation_queue_v0.39.csv", dtype=str, keep_default_na=False)
    summary = read_json(OUT / "summary_v0.39.json")

    require(len(mapping) == int(exp["mapping_gap"]) and mapping["WS_ID"].nunique() == len(mapping), "STRONG_MAPPING_239_GATE")
    require(len(dq) == int(exp["data_quality_gap"]) and dq["WS_ID"].nunique() == len(dq), "STRONG_DQ_7_GATE")
    require(len(hist) == int(exp["history_gap"]) and hist["WS_ID"].nunique() == len(hist), "STRONG_HISTORY_3_GATE")
    require(len(protected) == int(exp["instrument_fail_protected"]), "STRONG_PROTECTED_19_GATE")
    require(len(audit) == int(exp["audit_target_total"]) and audit["WS_ID"].nunique() == len(audit), "STRONG_AUDIT_249_GATE")
    require(audit.equals(queue), "STRONG_QUEUE_EQUALS_AUDIT_GATE")

    require(set(mapping["Source_State"]) == {"MAPPING_DOWNLOAD_NO_DATA"}, "STRONG_MAPPING_SOURCE_STATE_GATE")
    require((mapping["Auto_Fix_Safe"].str.lower() == "false").all(), "STRONG_NO_MAPPING_AUTO_FIX_GATE")
    require((mapping["Candidate_Override"] == "").all(), "STRONG_NO_CANDIDATE_OVERRIDE_GATE")
    require(not (mapping["Disposition"] == "AUTO_FIX_SAFE").any(), "STRONG_NO_AUTO_FIX_DISPOSITION_GATE")
    require(not (mapping["Disposition"] == "TERMINAL_BLOCKED").any(), "STRONG_NO_UNPROVEN_TERMINAL_MAPPING_GATE")

    dq_counts = counts(dq["Source_Reason"])
    require(dq_counts == {"SUSPICIOUS_RETURN_NEEDS_REPAIR": 5, "INVALID_OHLC_OR_VOLUME": 2}, f"STRONG_DQ_REASON_COUNTS:{dq_counts}")
    require((dq["Auto_Fix_Safe"].str.lower() == "false").all(), "STRONG_DQ_NO_AUTO_FIX_GATE")

    require(set(hist["Diagnostic_Classification"]) == {"STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES"}, "STRONG_HISTORY_CLASS_GATE")
    require(set(hist["Disposition"]) == {"DEFER_TEMPORAL"}, "STRONG_HISTORY_DISPOSITION_GATE")
    require(set(hist["Recommended_Action"]) == {"KEEP_WARMUP_NO_REPAIR"}, "STRONG_HISTORY_ACTION_GATE")

    require(set(protected["Audit_Action"]) == {"PROTECTED_INSTRUMENT_FAIL_NO_DATA_REMEDIATION"}, "STRONG_PROTECTED_ACTION_GATE")
    require((protected["Included_In_Audit_Target_249"].str.lower() == "false").all(), "STRONG_PROTECTED_EXCLUDED_GATE")

    require(summary["run_mode"] == MODE and summary["audit_target_count"] == int(exp["audit_target_total"]), "STRONG_SUMMARY_MODE_COUNT_GATE")
    require(summary["network_allowed"] is False and summary["network_request_count"] == 0, "STRONG_ZERO_NETWORK_GATE")
    require(summary["stock_download_executed"] is False and summary["fx_download_executed"] is False, "STRONG_ZERO_DOWNLOAD_GATE")
    require(summary["provider_search_executed"] is False, "STRONG_ZERO_PROVIDER_SEARCH_GATE")
    require(summary["cache_read_only"] is True, "STRONG_CACHE_READ_ONLY_GATE")
    require(summary["cache_sha_before"] == cfg["frozen_cache_sha256"] == summary["cache_sha_after"] == cache["sha256"], "STRONG_CACHE_IMMUTABILITY_GATE")
    require(summary["automatic_mapping_override_created"] is False, "STRONG_NO_OVERRIDE_GATE")
    require(summary["universe_mutated"] is False and summary["eligibility_promoted"] is False, "STRONG_NO_PROMOTION_MUTATION_GATE")
    require(summary["p0"] is False and summary["sector_rs"] is False and summary["swing_u3k_frozen_mutated"] is False and summary["productive"] is False, "STRONG_NONPRODUCTIVE_GATE")
    require(summary["automatic_fix_count"] == 0 and summary["terminal_blocked_count"] == 0, "STRONG_NO_UNSUPPORTED_FINAL_CLASSIFICATION_GATE")

    validate_frozen_inputs(cfg)
    print("DATA_GAP_AUDIT_ONLY strong gates PASS")


def self_test() -> None:
    require(symbol_relation("ABC.DE", "ABC.DE") == "EXACT", "SELF_SYMBOL_EXACT")
    require(symbol_relation("ABc.DE", "ABC.DE") == "CASE_ONLY", "SELF_SYMBOL_CASE")
    require(symbol_relation("AIBG.I", "AIBG.IR") == "SUFFIX_CHANGED", "SELF_SYMBOL_SUFFIX")
    f = pd.DataFrame(
        {
            "day": pd.to_datetime(["2026-08-28", "2026-08-31"]),
            "open": [10.0, 10.0],
            "high": [11.0, 11.0],
            "low": [9.0, 9.0],
            "close": [10.0, 10.5],
            "volume": [100.0, 100.0],
            "stock_splits": [0.0, 0.0],
        }
    )
    require(valid_mask(f).all(), "SELF_VALID_MASK")
    h = pd.Series({"WS_ID": "X", "Unique_Daily_Bars": "181", "Valid_Completed_Bars": "181", "Cache_Status": "WARMUP", "Cache_Reason": "INSUFFICIENT_HISTORY", "History_Current_State": "INSUFFICIENT_HISTORY_FOR_STANDARD_U3K"})
    r = history_audit_row(h)
    require(r["Disposition"] == "DEFER_TEMPORAL" and r["Bars_To_260"] == 79, "SELF_HISTORY")
    print("v0.39 DATA_GAP_AUDIT_ONLY self-test PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate-inputs", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--strong-gates", action="store_true")
    args = ap.parse_args()
    cfg_path = Path(args.config)
    if args.self_test:
        self_test()
    if args.validate_inputs:
        cfg = read_json(cfg_path)
        validate_frozen_inputs(cfg)
        validate_frozen_cache(cfg)
        print("v0.39 frozen inputs PASS")
    if args.audit:
        print(json.dumps(run_audit(cfg_path), ensure_ascii=False, indent=2))
    if args.strong_gates:
        strong_gates(cfg_path)
