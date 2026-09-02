#!/usr/bin/env python3
"""v0.40 FIX2 – DQ_DEPENDENCY_RETRY_ONLY.

Technical correction after successful v0.40 Run 33649915242.

Scope is exactly three QA targets whose v0.40 repair attempt was invalidated by
a missing runtime dependency (scikit-learn):
- WS:XLON:ROR.L / ROR.L
- WS:XTSE:IAU   / IAU.TO
- WS:XTSE:LAC   / LAC.TO

The saved v0.40 working cache is restored as a frozen source, validated by
exact SHA256/table counts, copied to a FIX2 working cache, and only these three
WS_IDs may change there. All 151 mapping results and the other four QA results
remain frozen evidence.

DEV / RESEARCH / SHADOW ONLY. No eligibility promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import math
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(".")
VERSION = "v0.40-FIX2"
STAGE = "CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_DATA_GAP_REMEDIATION"
MODE = "DQ_DEPENDENCY_RETRY_ONLY"
DEFAULT_CONFIG = ROOT / "config/current_master_research_partial_1633_controlled_data_gap_remediation_v0.40-fix2.json"
OUT = ROOT / "output_current_master_research_partial_1633_controlled_data_gap_remediation_v0_40_fix2"
UTC = timezone.utc

EXPECTED_TARGETS = {
    "WS:XLON:ROR.L": "ROR.L",
    "WS:XTSE:IAU": "IAU.TO",
    "WS:XTSE:LAC": "LAC.TO",
}
FORBIDDEN_RUNTIME_MARKERS = (
    "ModuleNotFoundError",
    "No module named",
    "ImportError",
    "Traceback (most recent call last)",
)


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


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, data: pd.DataFrame | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    frame.to_csv(path, index=False)


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


def qmarks(n: int) -> str:
    return ",".join("?" for _ in range(n))


def validate_runtime_dependencies() -> dict[str, str]:
    # This is intentionally called BEFORE any cache copy/purge/mutation.
    modules = ["yfinance", "pandas", "numpy", "scipy", "sklearn"]
    for name in modules:
        importlib.import_module(name)
    report = {
        "yfinance": importlib.metadata.version("yfinance"),
        "pandas": importlib.metadata.version("pandas"),
        "numpy": importlib.metadata.version("numpy"),
        "scipy": importlib.metadata.version("scipy"),
        "scikit-learn": importlib.metadata.version("scikit-learn"),
    }
    return report


def validate_workflow_policy(cfg: dict[str, Any]) -> None:
    p = Path(cfg["workflow_path"])
    require(p.is_file(), f"WORKFLOW_MISSING:{p}")
    s = p.read_text(encoding="utf-8")
    require("workflow_dispatch:" in s, "WORKFLOW_DISPATCH_MISSING")
    for forbidden in ("\n  push:", "\n  schedule:", "\n  pull_request:", "\n  repository_dispatch:"):
        require(forbidden not in s, f"NON_MANUAL_TRIGGER_FORBIDDEN:{forbidden.strip()}")
    require(cfg["workflow_trigger_policy"] == "MANUAL_DISPATCH_ONLY", "WORKFLOW_POLICY_MISMATCH")
    require(cfg["source_cache_restore_key"] in s, "EXACT_SOURCE_CACHE_KEY_NOT_IN_WORKFLOW")
    require("fail-on-cache-miss: true" in s, "SOURCE_CACHE_FAIL_CLOSED_MISSING")


def validate_frozen_inputs(cfg: dict[str, Any]) -> None:
    require(cfg["stage"] == STAGE, "CONFIG_STAGE_MISMATCH")
    require(cfg["version"] == VERSION, "CONFIG_VERSION_MISMATCH")
    require(cfg["run_mode"] == MODE, "CONFIG_MODE_MISMATCH")
    require(git_ancestor(cfg["source_result_commit"]), "SOURCE_RESULT_COMMIT_NOT_ANCESTOR")
    require(cfg["provider_search_allowed"] is False, "PROVIDER_SEARCH_MUST_BE_FALSE")
    require(cfg["fx_download_allowed"] is False, "FX_DOWNLOAD_MUST_BE_FALSE")
    require(cfg["alpha_vantage_allowed"] is False, "ALPHA_VANTAGE_MUST_BE_FALSE")
    require(cfg["universe_mutation_allowed"] is False, "UNIVERSE_MUTATION_MUST_BE_FALSE")
    require(cfg["eligibility_promotion_allowed"] is False, "ELIGIBILITY_PROMOTION_MUST_BE_FALSE")
    require(cfg["target_ws_ids"] == sorted(EXPECTED_TARGETS), "CONFIG_TARGET_WS_IDS_GATE")
    require(cfg["target_provider_symbols"] == [EXPECTED_TARGETS[x] for x in sorted(EXPECTED_TARGETS)], "CONFIG_TARGET_SYMBOLS_GATE")
    for path, expected in cfg["frozen_input_blobs"].items():
        actual = git_blob(path)
        require(actual == expected, f"FROZEN_BLOB_MISMATCH:{path}:{actual}!={expected}")
    validate_workflow_policy(cfg)


def validate_source_cache(cfg: dict[str, Any]) -> dict[str, Any]:
    p = Path(cfg["source_cache_path"])
    require(p.is_file(), f"SOURCE_CACHE_MISSING:{p}")
    sha = sha256_file(p)
    require(sha == cfg["source_cache_sha256"], f"SOURCE_CACHE_SHA_MISMATCH:{sha}")
    expected = {k: int(v) for k, v in cfg["source_cache_counts"].items()}
    with sqlite3.connect(f"file:{p.resolve()}?mode=ro", uri=True) as conn:
        actual = {t: int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in expected}
    require(actual == expected, f"SOURCE_CACHE_COUNTS_MISMATCH:{actual}")
    return {"path": str(p), "sha256": sha, "counts": actual}


def table_digest_excluding_targets(conn: sqlite3.Connection, table: str, targets: list[str]) -> str:
    cols = [str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    require(bool(cols), f"TABLE_SCHEMA_MISSING:{table}")
    order = ",".join(f'"{c}"' for c in cols)
    ph = qmarks(len(targets))
    cur = conn.execute(
        f"SELECT {order} FROM {table} WHERE ws_id NOT IN ({ph}) ORDER BY {order}",
        targets,
    )
    h = hashlib.sha256()
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for row in rows:
            h.update(json.dumps(list(row), ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest()


def non_target_digest(conn: sqlite3.Connection, targets: list[str]) -> dict[str, str]:
    return {
        "price_daily": table_digest_excluding_targets(conn, "price_daily", targets),
        "cache_state": table_digest_excluding_targets(conn, "cache_state", targets),
    }


def snapshot(conn: sqlite3.Connection, targets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ph = qmarks(len(targets))
    state = pd.read_sql_query(
        f"SELECT * FROM cache_state WHERE ws_id IN ({ph}) ORDER BY ws_id",
        conn,
        params=targets,
    )
    counts = pd.read_sql_query(
        f"""SELECT ws_id,yahoo_symbol,COUNT(*) AS price_rows,
                   MIN(day) AS first_day,MAX(day) AS last_day
            FROM price_daily
            WHERE ws_id IN ({ph})
            GROUP BY ws_id,yahoo_symbol
            ORDER BY ws_id,yahoo_symbol""",
        conn,
        params=targets,
    )
    return state, counts


def purge(conn: sqlite3.Connection, targets: list[str]) -> None:
    ph = qmarks(len(targets))
    conn.execute(f"DELETE FROM price_daily WHERE ws_id IN ({ph})", targets)
    conn.execute(f"DELETE FROM cache_state WHERE ws_id IN ({ph})", targets)
    conn.commit()


def build_fix2_plan(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    src = Path(cfg["source_output_dir"])
    dq7 = pd.read_csv(src / "data_quality_repair_results_7_v0.40.csv", dtype=str, keep_default_na=False)
    mapping151 = pd.read_csv(src / "mapping_retry_results_151_v0.40.csv", dtype=str, keep_default_na=False)
    plan158 = pd.read_csv(src / "target_plan_158_v0.40.csv", dtype=str, keep_default_na=False)

    require(len(dq7) == 7 and dq7["WS_ID"].nunique() == 7, "SOURCE_DQ7_GATE")
    require(len(mapping151) == 151 and mapping151["WS_ID"].nunique() == 151, "SOURCE_MAPPING151_GATE")
    require(len(plan158) == 158 and plan158["WS_ID"].nunique() == 158, "SOURCE_PLAN158_GATE")

    fix = dq7[dq7["WS_ID"].isin(EXPECTED_TARGETS)].copy().sort_values("WS_ID")
    require(len(fix) == 3, "FIX2_TARGET_3_GATE")
    require(set(fix["WS_ID"]) == set(EXPECTED_TARGETS), "FIX2_TARGET_ID_SET_GATE")
    for _, r in fix.iterrows():
        ws = txt(r["WS_ID"])
        require(txt(r["Provider_Symbol"]) == EXPECTED_TARGETS[ws], f"FIX2_SYMBOL_GATE:{ws}")
        require(txt(r["Post_Status"]) == "DOWNLOAD_FAILED", f"FIX2_SOURCE_STATUS_GATE:{ws}")
        require(txt(r["Post_Reason"]) == "NO_DATA_IN_BATCH", f"FIX2_SOURCE_REASON_GATE:{ws}")
        require(txt(r["Gap_Family"]) == "DATA_QUALITY", f"FIX2_FAMILY_GATE:{ws}")
        require(txt(r["Diagnostic_Classification"]) == "SUSPICIOUS_RETURN_TARGETED_REPAIR_CANDIDATE", f"FIX2_CLASS_GATE:{ws}")

    plan = fix[[
        "WS_ID","Gap_Family","Diagnostic_Classification","Provider_Symbol",
        "Primary_MIC","Primary_Ticker","Primary_Currency","Name","Country",
        "Primary_Universe_Index","Yahoo_Mapping_Status"
    ]].copy()
    plan["Repair_Pass"] = True
    plan["Request_Start"] = cfg["request_start"]
    plan["Request_End_Exclusive"] = cfg["request_end_exclusive"]
    return plan, dq7, mapping151


def runner_frame(plan: pd.DataFrame) -> pd.DataFrame:
    x = plan.copy()
    x["Yahoo_Symbol"] = x["Provider_Symbol"]
    return x[[
        "WS_ID","Yahoo_Symbol","Yahoo_Mapping_Status","Primary_MIC",
        "Primary_Ticker","Primary_Currency","Name","Country","Primary_Universe_Index"
    ]].copy()


def new_batch_rows(conn: sqlite3.Connection, old_ids: set[str]) -> pd.DataFrame:
    x = pd.read_sql_query("SELECT * FROM batch_log ORDER BY finished_utc,batch_id", conn)
    if x.empty:
        return x
    return x[~x["batch_id"].astype(str).isin(old_ids)].copy()


def controlled_result(status: str, rows: int) -> str:
    s = txt(status).upper()
    if s == "READY":
        return "RECOVERED_READY_EVIDENCE_ONLY"
    if s == "WARMUP":
        return "DEFER_TEMPORAL_AFTER_DATA_RECOVERY"
    if s == "QUARANTINE":
        return "RESIDUAL_DATA_QUALITY"
    if s == "STALE":
        return "RESIDUAL_STALE"
    if s == "DOWNLOAD_FAILED" or rows == 0:
        return "RESIDUAL_NO_DATA"
    return "RESIDUAL_REVIEW_REQUIRED"


def merge_final_dq(dq7: pd.DataFrame, after_state: pd.DataFrame, after_counts: pd.DataFrame) -> pd.DataFrame:
    state = after_state.set_index("ws_id", drop=False)
    counts = after_counts.set_index("ws_id", drop=False) if not after_counts.empty else pd.DataFrame()
    out = dq7.copy()

    for i, r in out.iterrows():
        ws = txt(r["WS_ID"])
        if ws not in EXPECTED_TARGETS:
            continue
        require(ws in state.index, f"FIX2_AFTER_STATE_MISSING:{ws}")
        a = state.loc[ws]
        if isinstance(a, pd.DataFrame):
            require(len(a) == 1, f"FIX2_AFTER_STATE_DUP:{ws}")
            a = a.iloc[0]
        price_rows = 0
        first_day = ""
        last_day = ""
        if not counts.empty and ws in counts.index:
            c = counts.loc[ws]
            if isinstance(c, pd.DataFrame):
                c = c.iloc[0]
            price_rows = inum(c.get("price_rows"))
            first_day = txt(c.get("first_day"))
            last_day = txt(c.get("last_day"))

        status = txt(a.get("status"))
        out.at[i, "Post_Status"] = status
        out.at[i, "Post_Reason"] = txt(a.get("reason_code"))
        out.at[i, "Post_Price_Rows"] = str(price_rows)
        out.at[i, "Post_Unique_Bars"] = str(inum(a.get("unique_bars")))
        out.at[i, "Post_Valid_Bars"] = str(inum(a.get("valid_bars")))
        out.at[i, "Post_Repaired_Rows"] = str(inum(a.get("repaired_rows")))
        out.at[i, "Post_Suspicious_Returns"] = str(inum(a.get("suspicious_returns")))
        out.at[i, "Post_First_Day"] = first_day
        out.at[i, "Post_Last_Day"] = last_day
        out.at[i, "Provider_Data_Returned"] = "True" if price_rows > 0 else "False"
        out.at[i, "Controlled_Result"] = controlled_result(status, price_rows)
        out.at[i, "Eligibility_Promoted"] = "False"
        out.at[i, "Universe_Mutated"] = "False"
        out.at[i, "Mapping_Override_Created"] = "False"
    return out


def validate_execution_log(cfg: dict[str, Any]) -> None:
    p = Path(cfg["execution_log_path"])
    require(p.is_file(), f"EXECUTION_LOG_MISSING:{p}")
    s = p.read_text(encoding="utf-8", errors="replace")
    for marker in FORBIDDEN_RUNTIME_MARKERS:
        require(marker not in s, f"RUNTIME_ERROR_MARKER_FORBIDDEN:{marker}")


def run_fix2(config_path: Path) -> dict[str, Any]:
    cfg = read_json(config_path)
    validate_frozen_inputs(cfg)

    # Critical: prove all runtime dependencies exist before touching any cache.
    deps = validate_runtime_dependencies()
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "runtime_dependency_report_v0.40-fix2.json", deps)

    source = validate_source_cache(cfg)
    plan, dq7, mapping151 = build_fix2_plan(cfg)
    targets = sorted(EXPECTED_TARGETS)
    write_csv(OUT / "fix2_target_plan_3_v0.40.csv", plan)

    src_cache = Path(cfg["source_cache_path"])
    work = Path(cfg["work_cache_path"])
    work.parent.mkdir(parents=True, exist_ok=True)
    if work.exists():
        work.unlink()
    shutil.copy2(src_cache, work)
    require(sha256_file(work) == source["sha256"], "WORK_COPY_INITIAL_SHA_GATE")

    raw = sqlite3.connect(work)
    try:
        before_state, before_counts = snapshot(raw, targets)
        non_before = non_target_digest(raw, targets)
        old_batch_ids = {str(x[0]) for x in raw.execute("SELECT batch_id FROM batch_log").fetchall()}
        purge(raw, targets)
    finally:
        raw.close()

    write_csv(OUT / "fix2_before_state_v0.40.csv", before_state)
    write_csv(OUT / "fix2_before_price_counts_v0.40.csv", before_counts)

    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from price_cache import FreeDataConfig, SQLitePriceCache, YFinanceBatchClient, YFinancePriceCacheRunner  # type: ignore

    fcfg = FreeDataConfig(
        batch_size=25,
        repair_batch_size=25,
        initial_period="2y",
        min_valid_bars=int(cfg["min_valid_bars"]),
        ready_unique_bars=int(cfg["ready_unique_bars"]),
        max_filterable_invalid_bars=int(cfg["max_filterable_invalid_bars"]),
        max_filterable_invalid_share=float(cfg["max_filterable_invalid_share"]),
        stale_calendar_days=int(cfg["stale_calendar_days"]),
        max_identical_retries=int(cfg["max_identical_retries"]),
        retry_sleep_seconds=float(cfg["retry_sleep_seconds"]),
        pause_between_batches_seconds=0.0,
        repair_anomalies=False,
        suspicious_abs_return=float(cfg["suspicious_abs_return"]),
    )
    fcfg.validate()

    cutoff = date.fromisoformat(cfg["safe_cutoff"])
    start = date.fromisoformat(cfg["request_start"])
    end = date.fromisoformat(cfg["request_end_exclusive"])
    require(end == date.fromisoformat(cfg["safe_cutoff_plus_one"]), "FIX2_END_CUTOFF_PLUS_ONE_GATE")

    ledger = plan[["WS_ID","Provider_Symbol","Repair_Pass","Request_Start","Request_End_Exclusive"]].copy()
    ledger.insert(0, "Phase", "DQ_DEPENDENCY_RETRY")
    write_csv(OUT / "fix2_provider_request_ledger_v0.40.csv", ledger)

    cache = SQLitePriceCache(work)
    try:
        runner = YFinancePriceCacheRunner(cache, YFinanceBatchClient(config=fcfg), config=fcfg)
        batch = runner_frame(plan)
        runner._process_batch(
            batch,
            period=None,
            start=start,
            end=end,
            repair_pass=True,
            as_of=cutoff,
        )
        cache.conn.commit()
        after_state, after_counts = snapshot(cache.conn, targets)
        non_after = non_target_digest(cache.conn, targets)
        new_batches = new_batch_rows(cache.conn, old_batch_ids)
        ph = qmarks(len(targets))
        max_day = cache.conn.execute(
            f"SELECT MAX(day) FROM price_daily WHERE ws_id IN ({ph})",
            targets,
        ).fetchone()[0]
        require(not max_day or str(max_day) <= cfg["safe_cutoff"], f"FIX2_TARGET_FUTURE_BAR_GATE:{max_day}")
    finally:
        cache.close()

    write_csv(OUT / "fix2_after_state_v0.40.csv", after_state)
    write_csv(OUT / "fix2_after_price_counts_v0.40.csv", after_counts)
    write_csv(OUT / "fix2_provider_batch_log_new_v0.40.csv", new_batches)

    require(non_before == non_after, "FIX2_NON_TARGET_CACHE_MUTATION_GATE")
    source_after = validate_source_cache(cfg)
    require(source_after["sha256"] == source["sha256"], "FIX2_SOURCE_CACHE_CHANGED")

    final_dq = merge_final_dq(dq7, after_state, after_counts)
    final_all = pd.concat([mapping151, final_dq], ignore_index=True, sort=False)
    require(len(final_all) == 158 and final_all["WS_ID"].nunique() == 158, "FINAL_CONTROLLED_158_GATE")
    write_csv(OUT / "final_data_quality_results_7_v0.40.csv", final_dq)
    write_csv(OUT / "final_controlled_results_158_v0.40.csv", final_all)
    write_csv(OUT / "final_residual_non_ready_158_v0.40.csv", final_all[final_all["Post_Status"] != "READY"].copy())

    work_sha = sha256_file(work)
    with sqlite3.connect(f"file:{work.resolve()}?mode=ro", uri=True) as conn:
        work_counts = {t: int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in ("price_daily","cache_state","batch_log")}

    target_final = final_dq[final_dq["WS_ID"].isin(EXPECTED_TARGETS)].copy()
    summary = {
        "stage": STAGE,
        "version": VERSION,
        "run_mode": MODE,
        "status": "DEV / RESEARCH / SHADOW – NOT PRODUCTIVE",
        "source_result_commit": cfg["source_result_commit"],
        "source_run_id": cfg["source_run_id"],
        "target_count": 3,
        "target_ws_ids": targets,
        "target_provider_symbols": [EXPECTED_TARGETS[x] for x in targets],
        "runtime_dependencies": deps,
        "target_post_status_counts": dict(sorted(Counter(target_final["Post_Status"]).items())),
        "target_controlled_result_counts": dict(sorted(Counter(target_final["Controlled_Result"]).items())),
        "final_158_post_status_counts": dict(sorted(Counter(final_all["Post_Status"]).items())),
        "final_158_controlled_result_counts": dict(sorted(Counter(final_all["Controlled_Result"]).items())),
        "source_cache_sha_before": source["sha256"],
        "source_cache_sha_after": source_after["sha256"],
        "source_cache_counts": source["counts"],
        "work_cache_path": str(work),
        "work_cache_sha256": work_sha,
        "work_cache_counts": work_counts,
        "non_target_digest_before": non_before,
        "non_target_digest_after": non_after,
        "new_provider_batch_log_count": len(new_batches),
        "provider_search_executed": False,
        "fx_download_executed": False,
        "alpha_vantage_executed": False,
        "mapping_override_created": False,
        "universe_mutated": False,
        "eligibility_promoted": False,
        "p0": False,
        "sector_rs": False,
        "swing_u3k_frozen_mutated": False,
        "productive": False,
        "run_timestamp_utc": now_utc(),
        "next_stage": "CURRENT_MASTER_RESEARCH_PARTIAL_1633_MANUAL_MAPPING_EVIDENCE_REVIEW",
    }
    write_json(OUT / "summary_v0.40-fix2.json", summary)
    write_json(OUT / "stage_checkpoint_v0.40-fix2.json", {
        "stage": STAGE,
        "version": VERSION,
        "run_mode": MODE,
        "completed": True,
        "strong_gates_required": True,
        "source_result_commit": cfg["source_result_commit"],
        "source_run_id": cfg["source_run_id"],
        "work_cache_sha256": work_sha,
        "next_stage": summary["next_stage"],
    })
    write_json(OUT / "manifest_v0.40-fix2.json", {
        "stage": STAGE,
        "version": VERSION,
        "run_mode": MODE,
        "source_result_commit": cfg["source_result_commit"],
        "source_cache": source,
        "work_cache": {"path": str(work), "sha256": work_sha, "counts": work_counts},
        "frozen_input_blobs": cfg["frozen_input_blobs"],
        "outputs": sorted(p.name for p in OUT.iterdir()),
        "productive": False,
    })
    return summary


def strong_gates(config_path: Path) -> None:
    cfg = read_json(config_path)
    validate_frozen_inputs(cfg)
    validate_runtime_dependencies()
    source = validate_source_cache(cfg)
    validate_execution_log(cfg)

    plan = pd.read_csv(OUT / "fix2_target_plan_3_v0.40.csv", dtype=str, keep_default_na=False)
    req = pd.read_csv(OUT / "fix2_provider_request_ledger_v0.40.csv", dtype=str, keep_default_na=False)
    blog = pd.read_csv(OUT / "fix2_provider_batch_log_new_v0.40.csv", dtype=str, keep_default_na=False)
    final_dq = pd.read_csv(OUT / "final_data_quality_results_7_v0.40.csv", dtype=str, keep_default_na=False)
    final_all = pd.read_csv(OUT / "final_controlled_results_158_v0.40.csv", dtype=str, keep_default_na=False)
    summary = read_json(OUT / "summary_v0.40-fix2.json")

    require(len(plan) == 3 and set(plan["WS_ID"]) == set(EXPECTED_TARGETS), "STRONG_FIX2_TARGET_3_GATE")
    require(set(req["WS_ID"]) == set(EXPECTED_TARGETS), "STRONG_FIX2_REQUEST_ID_GATE")
    require(set(req["Provider_Symbol"]) == set(EXPECTED_TARGETS.values()), "STRONG_FIX2_REQUEST_SYMBOL_GATE")
    require((req["Repair_Pass"].str.lower() == "true").all(), "STRONG_FIX2_REPAIR_TRUE_GATE")
    require(set(req["Request_Start"]) == {cfg["request_start"]}, "STRONG_FIX2_START_GATE")
    require(set(req["Request_End_Exclusive"]) == {cfg["request_end_exclusive"]}, "STRONG_FIX2_END_GATE")
    require(len(blog) == 1, "STRONG_FIX2_EXACT_ONE_PROVIDER_BATCH_GATE")
    if "retry_count" in blog.columns:
        retries = pd.to_numeric(blog["retry_count"], errors="coerce").fillna(0)
        require((retries <= int(cfg["max_identical_retries"])).all(), "STRONG_FIX2_RETRY_CEILING_GATE")

    require(len(final_dq) == 7 and final_dq["WS_ID"].nunique() == 7, "STRONG_FINAL_DQ7_GATE")
    require(len(final_all) == 158 and final_all["WS_ID"].nunique() == 158, "STRONG_FINAL_158_GATE")

    original_mapping_blob = git_blob(cfg["mapping_results_path"])
    require(original_mapping_blob == cfg["frozen_input_blobs"][cfg["mapping_results_path"]], "STRONG_MAPPING151_IMMUTABLE_GATE")

    require(summary["source_cache_sha_before"] == cfg["source_cache_sha256"] == summary["source_cache_sha_after"] == source["sha256"], "STRONG_FIX2_SOURCE_CACHE_SHA_GATE")
    require(summary["non_target_digest_before"] == summary["non_target_digest_after"], "STRONG_FIX2_NON_TARGET_DIGEST_GATE")
    require(summary["provider_search_executed"] is False, "STRONG_NO_PROVIDER_SEARCH_GATE")
    require(summary["fx_download_executed"] is False, "STRONG_NO_FX_GATE")
    require(summary["alpha_vantage_executed"] is False, "STRONG_NO_ALPHA_GATE")
    require(summary["mapping_override_created"] is False, "STRONG_NO_MAPPING_OVERRIDE_GATE")
    require(summary["universe_mutated"] is False, "STRONG_NO_UNIVERSE_MUTATION_GATE")
    require(summary["eligibility_promoted"] is False, "STRONG_NO_ELIGIBILITY_PROMOTION_GATE")
    require(summary["p0"] is False and summary["sector_rs"] is False and summary["swing_u3k_frozen_mutated"] is False and summary["productive"] is False, "STRONG_NONPRODUCTIVE_GATE")

    work = Path(cfg["work_cache_path"])
    require(work.is_file(), "STRONG_FIX2_WORK_CACHE_MISSING")
    require(sha256_file(work) == summary["work_cache_sha256"], "STRONG_FIX2_WORK_CACHE_SHA_GATE")
    with sqlite3.connect(f"file:{work.resolve()}?mode=ro", uri=True) as conn:
        targets = sorted(EXPECTED_TARGETS)
        ph = qmarks(len(targets))
        max_day = conn.execute(f"SELECT MAX(day) FROM price_daily WHERE ws_id IN ({ph})", targets).fetchone()[0]
        require(not max_day or str(max_day) <= cfg["safe_cutoff"], "STRONG_FIX2_FUTURE_BAR_GATE")

    print("v0.40 FIX2 DQ_DEPENDENCY_RETRY_ONLY strong gates PASS")


def self_test() -> None:
    require(set(EXPECTED_TARGETS) == {"WS:XLON:ROR.L","WS:XTSE:IAU","WS:XTSE:LAC"}, "SELF_TARGETS")
    require(controlled_result("READY", 500) == "RECOVERED_READY_EVIDENCE_ONLY", "SELF_READY")
    require(controlled_result("WARMUP", 100) == "DEFER_TEMPORAL_AFTER_DATA_RECOVERY", "SELF_WARMUP")
    require(controlled_result("QUARANTINE", 500) == "RESIDUAL_DATA_QUALITY", "SELF_QUARANTINE")
    require(controlled_result("DOWNLOAD_FAILED", 0) == "RESIDUAL_NO_DATA", "SELF_FAIL")
    require(qmarks(3) == "?,?,?", "SELF_QMARKS")
    print("v0.40 FIX2 self-test PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate-inputs", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--strong-gates", action="store_true")
    args = ap.parse_args()
    cfg_path = Path(args.config)

    if args.self_test:
        self_test()
    if args.validate_inputs:
        cfg = read_json(cfg_path)
        validate_frozen_inputs(cfg)
        validate_runtime_dependencies()
        validate_source_cache(cfg)
        build_fix2_plan(cfg)
        print("v0.40 FIX2 frozen inputs, dependency preflight and target scope PASS")
    if args.run:
        print(json.dumps(run_fix2(cfg_path), ensure_ascii=False, indent=2))
    if args.strong_gates:
        strong_gates(cfg_path)
