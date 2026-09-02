#!/usr/bin/env python3
"""v0.40 CONTROLLED_RETRY_DATA_ONLY for the frozen v0.39 remediation queue.

DEV / RESEARCH / SHADOW ONLY.

Exactly 151 v0.39 MAPPING/RETRY_DATA rows with frozen EXACT provider symbols
and exactly 7 v0.39 DATA_QUALITY/RETRY_DATA rows are allowed. The frozen v0.38
cache is copied to an isolated v0.40 working cache; only those 158 WS_IDs may
change there, apart from append-only batch_log rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

ROOT = Path(".")
VERSION = "v0.40"
STAGE = "CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_DATA_GAP_REMEDIATION"
MODE = "CONTROLLED_RETRY_DATA_ONLY"
DEFAULT_CONFIG = ROOT / "config/current_master_research_partial_1633_controlled_data_gap_remediation_v0.40.json"
OUT = ROOT / "output_current_master_research_partial_1633_controlled_data_gap_remediation_v0_40"
UTC = timezone.utc

NETWORK_ALLOWED = True
STOCK_DOWNLOAD_ALLOWED = True
FX_DOWNLOAD_ALLOWED = False
PROVIDER_SEARCH_ALLOWED = False
ALPHA_VANTAGE_ALLOWED = False
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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
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


def chunks(seq: list[Any], n: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def qmarks(n: int) -> str:
    return ",".join("?" for _ in range(n))


def validate_workflow_policy(cfg: dict[str, Any]) -> None:
    p = Path(cfg["workflow_path"])
    require(p.is_file(), f"WORKFLOW_MISSING:{p}")
    s = p.read_text(encoding="utf-8")
    require("workflow_dispatch:" in s, "MANUAL_WORKFLOW_DISPATCH_MISSING")
    for forbidden in ("\n  push:", "\n  schedule:", "\n  pull_request:", "\n  repository_dispatch:"):
        require(forbidden not in s, f"NON_MANUAL_WORKFLOW_TRIGGER_FORBIDDEN:{forbidden.strip()}")
    require(cfg.get("workflow_trigger_policy") == "MANUAL_DISPATCH_ONLY", "WORKFLOW_TRIGGER_POLICY_MISMATCH")


def validate_frozen_inputs(cfg: dict[str, Any]) -> None:
    require(cfg.get("stage") == STAGE, "CONFIG_STAGE_MISMATCH")
    require(cfg.get("version") == VERSION, "CONFIG_VERSION_MISMATCH")
    require(cfg.get("run_mode") == MODE, "CONFIG_MODE_MISMATCH")
    require(cfg.get("network_allowed") is True, "NETWORK_POLICY_MISMATCH")
    require(cfg.get("stock_download_allowed") is True, "STOCK_DOWNLOAD_POLICY_MISMATCH")
    require(cfg.get("fx_download_allowed") is False, "FX_DOWNLOAD_MUST_BE_DISABLED")
    require(cfg.get("provider_search_allowed") is False, "PROVIDER_SEARCH_MUST_BE_DISABLED")
    require(cfg.get("alpha_vantage_allowed") is False, "ALPHA_VANTAGE_MUST_BE_DISABLED")
    require(cfg.get("automatic_mapping_override_allowed") is False, "AUTO_MAPPING_OVERRIDE_MUST_BE_DISABLED")
    require(cfg.get("universe_mutation_allowed") is False, "UNIVERSE_MUTATION_MUST_BE_DISABLED")
    require(cfg.get("eligibility_promotion_allowed") is False, "ELIGIBILITY_PROMOTION_MUST_BE_DISABLED")
    require(git_ancestor(cfg["source_result_commit"]), "SOURCE_RESULT_COMMIT_NOT_ANCESTOR")
    for path, expected in cfg["frozen_input_blobs"].items():
        actual = git_blob(path)
        require(actual == expected, f"FROZEN_INPUT_BLOB_MISMATCH:{path}:{actual}!={expected}")
    validate_workflow_policy(cfg)


def validate_source_cache(cfg: dict[str, Any]) -> dict[str, Any]:
    path = Path(cfg["frozen_source_cache_path"])
    require(path.is_file(), f"FROZEN_SOURCE_CACHE_MISSING:{path}")
    sha = sha256_file(path)
    require(sha == cfg["frozen_source_cache_sha256"], f"FROZEN_SOURCE_CACHE_SHA_MISMATCH:{sha}")
    expected = {k: int(v) for k, v in cfg["frozen_source_cache_counts"].items()}
    with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as conn:
        actual = {t: int(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in expected}
    require(actual == expected, f"FROZEN_SOURCE_CACHE_COUNTS_MISMATCH:{actual}")
    return {"path": str(path), "sha256": sha, "counts": actual}


def table_digest_excluding_targets(conn: sqlite3.Connection, table: str, targets: list[str]) -> str:
    ph = qmarks(len(targets))
    cols = [str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    require(bool(cols), f"TABLE_SCHEMA_MISSING:{table}")
    order = ",".join(f'"{c}"' for c in cols)
    cur = conn.execute(f"SELECT {order} FROM {table} WHERE ws_id NOT IN ({ph}) ORDER BY {order}", targets)
    h = hashlib.sha256()
    while True:
        rows = cur.fetchmany(5000)
        if not rows:
            break
        for row in rows:
            h.update(json.dumps([None if x is None else x for x in row], ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest()


def cache_non_target_digest(conn: sqlite3.Connection, targets: list[str]) -> dict[str, str]:
    return {
        "price_daily": table_digest_excluding_targets(conn, "price_daily", targets),
        "cache_state": table_digest_excluding_targets(conn, "cache_state", targets),
    }


def snapshot_target_state(conn: sqlite3.Connection, targets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ph = qmarks(len(targets))
    state = pd.read_sql_query(f"SELECT * FROM cache_state WHERE ws_id IN ({ph}) ORDER BY ws_id", conn, params=targets)
    counts = pd.read_sql_query(
        f"""SELECT ws_id,yahoo_symbol,COUNT(*) AS price_rows,MIN(day) AS first_day,MAX(day) AS last_day
            FROM price_daily WHERE ws_id IN ({ph}) GROUP BY ws_id,yahoo_symbol ORDER BY ws_id,yahoo_symbol""",
        conn, params=targets,
    )
    return state, counts


def purge_targets(conn: sqlite3.Connection, targets: list[str]) -> None:
    ph = qmarks(len(targets))
    conn.execute(f"DELETE FROM price_daily WHERE ws_id IN ({ph})", targets)
    conn.execute(f"DELETE FROM cache_state WHERE ws_id IN ({ph})", targets)
    conn.commit()


def build_target_plan(cfg: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, set[str]]]:
    source = Path(cfg["source_output_dir"])
    queue = pd.read_csv(source / "remediation_queue_v0.39.csv", dtype=str, keep_default_na=False)
    master = pd.read_csv(cfg["source_universe"], dtype=str, keep_default_na=False)
    protected = pd.read_csv(source / "protected_instrument_fail_19_v0.39.csv", dtype=str, keep_default_na=False)
    exp = cfg["expected_source_counts"]

    require(len(queue) == 249 and queue["WS_ID"].nunique() == 249, "SOURCE_QUEUE_249_UNIQUE_GATE")
    require(int((queue["Disposition"] == "RETRY_DATA").sum()) == int(exp["retry_data_total"]), "SOURCE_RETRY_DATA_158_GATE")
    require(int((queue["Disposition"] == "MANUAL_REVIEW").sum()) == int(exp["manual_review"]), "SOURCE_MANUAL_REVIEW_88_GATE")
    require(int((queue["Disposition"] == "DEFER_TEMPORAL").sum()) == int(exp["history_defer"]), "SOURCE_HISTORY_DEFER_3_GATE")
    require(len(protected) == int(exp["protected_instrument_fail"]), "SOURCE_PROTECTED_19_GATE")

    mapping = queue[(queue["Gap_Family"] == "MAPPING") & (queue["Disposition"] == "RETRY_DATA")].copy()
    dq = queue[(queue["Gap_Family"] == "DATA_QUALITY") & (queue["Disposition"] == "RETRY_DATA")].copy()
    require(len(mapping) == int(exp["mapping_exact_retry"]), "MAPPING_RETRY_151_GATE")
    require(len(dq) == int(exp["data_quality_retry"]), "DQ_RETRY_7_GATE")
    require(set(mapping["Static_Symbol_Relation"]) == {"EXACT"}, "MAPPING_RETRY_MUST_BE_EXACT_ONLY")
    require(set(mapping["Diagnostic_Classification"]) == {"EXACT_PROVIDER_SYMBOL_NO_DATA"}, "MAPPING_RETRY_CLASS_GATE")
    require((mapping["Prior_Yahoo_Symbol"] == mapping["Candidate_Yahoo_Symbol"]).all(), "MAPPING_RETRY_SYMBOL_NOT_EXACT")
    require(set(dq["Diagnostic_Classification"]) == {"INVALID_BAR_TARGETED_REPAIR_CANDIDATE", "SUSPICIOUS_RETURN_TARGETED_REPAIR_CANDIDATE"}, "DQ_RETRY_CLASS_GATE")

    target_ids = set(mapping["WS_ID"]) | set(dq["WS_ID"])
    manual_ids = set(queue.loc[queue["Disposition"] == "MANUAL_REVIEW", "WS_ID"])
    history_ids = set(queue.loc[queue["Disposition"] == "DEFER_TEMPORAL", "WS_ID"])
    protected_ids = set(protected["WS_ID"])
    require(len(target_ids) == int(exp["retry_data_total"]), "TARGET_158_UNIQUE_GATE")
    require(not (target_ids & manual_ids), "TARGET_INTERSECTS_MANUAL_REVIEW")
    require(not (target_ids & history_ids), "TARGET_INTERSECTS_HISTORY_DEFER")
    require(not (target_ids & protected_ids), "TARGET_INTERSECTS_PROTECTED_INSTRUMENT")

    require(master["WS_ID"].nunique() == len(master), "SOURCE_UNIVERSE_WS_ID_UNIQUE_GATE")
    meta = master.set_index("WS_ID", drop=False)
    rows: list[dict[str, Any]] = []
    for _, r in mapping.sort_values("WS_ID").iterrows():
        ws = txt(r["WS_ID"]); require(ws in meta.index, f"TARGET_MASTER_JOIN_MISSING:{ws}"); m = meta.loc[ws]
        rows.append({"WS_ID":ws,"Gap_Family":"MAPPING","Diagnostic_Classification":txt(r["Diagnostic_Classification"]),"Provider_Symbol":txt(r["Candidate_Yahoo_Symbol"]),"Request_Mode":"NORMAL_FIXED_WINDOW","Repair_Pass":False,"Primary_MIC":txt(m.get("Primary_MIC")),"Primary_Ticker":txt(m.get("Primary_Ticker")),"Primary_Currency":txt(m.get("Primary_Currency")),"Name":txt(m.get("Name")),"Country":txt(m.get("Country")),"Primary_Universe_Index":txt(m.get("Primary_Universe_Index")),"Yahoo_Mapping_Status":"FROZEN_V0_39_EXACT_RETRY"})
    for _, r in dq.sort_values("WS_ID").iterrows():
        ws = txt(r["WS_ID"]); require(ws in meta.index, f"TARGET_MASTER_JOIN_MISSING:{ws}"); m = meta.loc[ws]
        rows.append({"WS_ID":ws,"Gap_Family":"DATA_QUALITY","Diagnostic_Classification":txt(r["Diagnostic_Classification"]),"Provider_Symbol":txt(r["Yahoo_Symbol"]),"Request_Mode":"REPAIR_FIXED_WINDOW","Repair_Pass":True,"Primary_MIC":txt(m.get("Primary_MIC")),"Primary_Ticker":txt(m.get("Primary_Ticker")),"Primary_Currency":txt(m.get("Primary_Currency")),"Name":txt(m.get("Name")),"Country":txt(m.get("Country")),"Primary_Universe_Index":txt(m.get("Primary_Universe_Index")),"Yahoo_Mapping_Status":"FROZEN_V0_39_DQ_REPAIR"})
    plan = pd.DataFrame(rows).sort_values(["Gap_Family","WS_ID"]).reset_index(drop=True)
    require(len(plan) == int(exp["retry_data_total"]), "TARGET_PLAN_158_GATE")
    require((plan["Provider_Symbol"].str.len() > 0).all(), "EMPTY_PROVIDER_SYMBOL_GATE")
    require(not plan["Provider_Symbol"].duplicated().any(), "TARGET_PROVIDER_SYMBOL_COLLISION_GATE")
    return plan, {"target_ids":set(plan["WS_ID"]),"mapping_ids":set(mapping["WS_ID"]),"dq_ids":set(dq["WS_ID"]),"manual_ids":manual_ids,"history_ids":history_ids,"protected_ids":protected_ids}


def runner_frame(plan: pd.DataFrame) -> pd.DataFrame:
    x = plan.copy(); x["Yahoo_Symbol"] = x["Provider_Symbol"]
    return x[["WS_ID","Yahoo_Symbol","Yahoo_Mapping_Status","Primary_MIC","Primary_Ticker","Primary_Currency","Name","Country","Primary_Universe_Index"]].copy()


def new_batch_log_rows(conn: sqlite3.Connection, before_ids: set[str]) -> pd.DataFrame:
    x = pd.read_sql_query("SELECT * FROM batch_log ORDER BY finished_utc,batch_id", conn)
    return x if x.empty else x[~x["batch_id"].astype(str).isin(before_ids)].copy()


def outcome_disposition(status: str, reason: str, price_rows: int) -> str:
    status = txt(status).upper()
    if status == "READY": return "RECOVERED_READY_EVIDENCE_ONLY"
    if status == "WARMUP": return "DEFER_TEMPORAL_AFTER_DATA_RECOVERY"
    if status == "QUARANTINE": return "RESIDUAL_DATA_QUALITY"
    if status == "DOWNLOAD_FAILED" or price_rows == 0: return "RESIDUAL_NO_DATA"
    if status == "STALE": return "RESIDUAL_STALE"
    return "RESIDUAL_REVIEW_REQUIRED"


def result_rows(plan: pd.DataFrame, before_state: pd.DataFrame, before_counts: pd.DataFrame, after_state: pd.DataFrame, after_counts: pd.DataFrame) -> pd.DataFrame:
    bs = before_state.set_index("ws_id", drop=False) if not before_state.empty else None
    bc = before_counts.set_index("ws_id", drop=False) if not before_counts.empty else None
    ast = after_state.set_index("ws_id", drop=False) if not after_state.empty else None
    ac = after_counts.set_index("ws_id", drop=False) if not after_counts.empty else None
    rows=[]
    for _, p in plan.iterrows():
        ws=txt(p["WS_ID"]); require(ast is not None and ws in ast.index, f"AFTER_STATE_MISSING:{ws}")
        a=ast.loc[ws]; a=a.iloc[0] if isinstance(a,pd.DataFrame) else a
        pre_status=pre_reason=""; pre_rows=0
        if bs is not None and ws in bs.index:
            b=bs.loc[ws]; b=b.iloc[0] if isinstance(b,pd.DataFrame) else b; pre_status=txt(b.get("status")); pre_reason=txt(b.get("reason_code"))
        if bc is not None and ws in bc.index:
            c=bc.loc[ws]; c=c.iloc[0] if isinstance(c,pd.DataFrame) else c; pre_rows=inum(c.get("price_rows"))
        post_rows=0; first_day=last_day=""
        if ac is not None and ws in ac.index:
            c=ac.loc[ws]; c=c.iloc[0] if isinstance(c,pd.DataFrame) else c; post_rows=inum(c.get("price_rows")); first_day=txt(c.get("first_day")); last_day=txt(c.get("last_day"))
        ps=txt(a.get("status")); pr=txt(a.get("reason_code"))
        rows.append({**{k:p[k] for k in plan.columns},"Pre_Status":pre_status,"Pre_Reason":pre_reason,"Pre_Price_Rows":pre_rows,"Post_Status":ps,"Post_Reason":pr,"Post_Price_Rows":post_rows,"Post_Unique_Bars":inum(a.get("unique_bars")),"Post_Valid_Bars":inum(a.get("valid_bars")),"Post_Repaired_Rows":inum(a.get("repaired_rows")),"Post_Suspicious_Returns":inum(a.get("suspicious_returns")),"Post_First_Day":first_day,"Post_Last_Day":last_day,"Provider_Data_Returned":post_rows>0,"Controlled_Result":outcome_disposition(ps,pr,post_rows),"Eligibility_Promoted":False,"Universe_Mutated":False,"Mapping_Override_Created":False})
    return pd.DataFrame(rows)


def run_controlled(config_path: Path) -> dict[str, Any]:
    cfg=read_json(config_path); validate_frozen_inputs(cfg); source_before=validate_source_cache(cfg)
    plan,sets=build_target_plan(cfg); targets=sorted(sets["target_ids"]); mapping_ids=sorted(sets["mapping_ids"]); dq_ids=sorted(sets["dq_ids"])
    OUT.mkdir(parents=True,exist_ok=True); write_csv(OUT/"target_plan_158_v0.40.csv",plan)
    src=Path(cfg["frozen_source_cache_path"]); work=Path(cfg["work_cache_path"]); work.parent.mkdir(parents=True,exist_ok=True)
    if work.exists(): work.unlink()
    shutil.copy2(src,work); require(sha256_file(work)==source_before["sha256"],"WORK_CACHE_INITIAL_COPY_SHA_MISMATCH")
    raw=sqlite3.connect(work)
    try:
        before_state,before_counts=snapshot_target_state(raw,targets); non_before=cache_non_target_digest(raw,targets); before_batch_ids={str(x[0]) for x in raw.execute("SELECT batch_id FROM batch_log").fetchall()}; purge_targets(raw,targets)
    finally: raw.close()
    write_csv(OUT/"target_before_state_v0.40.csv",before_state); write_csv(OUT/"target_before_price_counts_v0.40.csv",before_counts)

    script_dir=Path(__file__).resolve().parent
    if str(script_dir) not in sys.path: sys.path.insert(0,str(script_dir))
    from price_cache import FreeDataConfig,SQLitePriceCache,YFinanceBatchClient,YFinancePriceCacheRunner
    fcfg=FreeDataConfig(batch_size=int(cfg["batch_size"]),repair_batch_size=int(cfg["repair_batch_size"]),initial_period="2y",min_valid_bars=int(cfg["min_valid_bars"]),ready_unique_bars=int(cfg["ready_unique_bars"]),max_filterable_invalid_bars=int(cfg["max_filterable_invalid_bars"]),max_filterable_invalid_share=float(cfg["max_filterable_invalid_share"]),stale_calendar_days=int(cfg["stale_calendar_days"]),max_identical_retries=int(cfg["max_identical_retries"]),retry_sleep_seconds=float(cfg["retry_sleep_seconds"]),pause_between_batches_seconds=float(cfg["pause_between_batches_seconds"]),repair_anomalies=False,suspicious_abs_return=float(cfg["suspicious_abs_return"])); fcfg.validate()
    cutoff=date.fromisoformat(cfg["safe_cutoff"]); start=date.fromisoformat(cfg["request_start"]); end=date.fromisoformat(cfg["request_end_exclusive"])
    require(start<cutoff<end and end==date.fromisoformat(cfg["safe_cutoff_plus_one"]),"REQUEST_WINDOW_DATE_GATE")
    logical=[]; requests=[]; missing_normal=set()
    cache=SQLitePriceCache(work)
    try:
        runner=YFinancePriceCacheRunner(cache,YFinanceBatchClient(config=fcfg),config=fcfg)
        mr=runner_frame(plan[plan["Gap_Family"]=="MAPPING"].copy())
        for seq,idxs in enumerate(chunks(list(mr.index),fcfg.batch_size),1):
            b=mr.loc[idxs]; label=f"MAPPING_NORMAL_{seq:03d}"; logical.append({"Logical_Batch":label,"Phase":"MAPPING_NORMAL","Repair_Pass":False,"WS_ID_Count":len(b),"Request_Start":cfg["request_start"],"Request_End_Exclusive":cfg["request_end_exclusive"]})
            for _,r in b.iterrows(): requests.append({"Logical_Batch":label,"Phase":"MAPPING_NORMAL","WS_ID":txt(r["WS_ID"]),"Provider_Symbol":txt(r["Yahoo_Symbol"]),"Repair_Pass":False,"Request_Start":cfg["request_start"],"Request_End_Exclusive":cfg["request_end_exclusive"]})
            _,miss=runner._process_batch(b,period=None,start=start,end=end,repair_pass=False,as_of=cutoff); missing_normal.update(str(x) for x in miss if x)
        if missing_normal:
            rescue=mr[mr["Yahoo_Symbol"].astype(str).isin(sorted(missing_normal))].copy()
            for seq,idxs in enumerate(chunks(list(rescue.index),fcfg.batch_size),1):
                b=rescue.loc[idxs]; label=f"MAPPING_RESCUE_{seq:03d}"; logical.append({"Logical_Batch":label,"Phase":"MAPPING_RESCUE","Repair_Pass":False,"WS_ID_Count":len(b),"Request_Start":cfg["request_start"],"Request_End_Exclusive":cfg["request_end_exclusive"]})
                for _,r in b.iterrows(): requests.append({"Logical_Batch":label,"Phase":"MAPPING_RESCUE","WS_ID":txt(r["WS_ID"]),"Provider_Symbol":txt(r["Yahoo_Symbol"]),"Repair_Pass":False,"Request_Start":cfg["request_start"],"Request_End_Exclusive":cfg["request_end_exclusive"]})
                runner._process_batch(b,period=None,start=start,end=end,repair_pass=False,as_of=cutoff)
        dq=runner_frame(plan[plan["Gap_Family"]=="DATA_QUALITY"].copy())
        for seq,idxs in enumerate(chunks(list(dq.index),fcfg.repair_batch_size),1):
            b=dq.loc[idxs]; label=f"DQ_REPAIR_{seq:03d}"; logical.append({"Logical_Batch":label,"Phase":"DQ_REPAIR","Repair_Pass":True,"WS_ID_Count":len(b),"Request_Start":cfg["request_start"],"Request_End_Exclusive":cfg["request_end_exclusive"]})
            for _,r in b.iterrows(): requests.append({"Logical_Batch":label,"Phase":"DQ_REPAIR","WS_ID":txt(r["WS_ID"]),"Provider_Symbol":txt(r["Yahoo_Symbol"]),"Repair_Pass":True,"Request_Start":cfg["request_start"],"Request_End_Exclusive":cfg["request_end_exclusive"]})
            runner._process_batch(b,period=None,start=start,end=end,repair_pass=True,as_of=cutoff)
        cache.conn.commit(); after_state,after_counts=snapshot_target_state(cache.conn,targets); non_after=cache_non_target_digest(cache.conn,targets); new_batches=new_batch_log_rows(cache.conn,before_batch_ids); max_day=cache.conn.execute("SELECT MAX(day) FROM price_daily").fetchone()[0]; require(not max_day or str(max_day)<=cfg["safe_cutoff"],f"WORK_CACHE_FUTURE_BAR_GATE:{max_day}")
    finally: cache.close()

    write_csv(OUT/"logical_batch_plan_v0.40.csv",logical); write_csv(OUT/"provider_request_ledger_v0.40.csv",requests); write_csv(OUT/"mapping_missing_after_normal_v0.40.csv",pd.DataFrame({"Provider_Symbol":sorted(missing_normal)})); write_csv(OUT/"provider_batch_log_new_v0.40.csv",new_batches); write_csv(OUT/"target_after_state_v0.40.csv",after_state); write_csv(OUT/"target_after_price_counts_v0.40.csv",after_counts)
    results=result_rows(plan,before_state,before_counts,after_state,after_counts); write_csv(OUT/"controlled_results_158_v0.40.csv",results); write_csv(OUT/"mapping_retry_results_151_v0.40.csv",results[results["Gap_Family"]=="MAPPING"].copy()); write_csv(OUT/"data_quality_repair_results_7_v0.40.csv",results[results["Gap_Family"]=="DATA_QUALITY"].copy()); write_csv(OUT/"residual_non_ready_v0.40.csv",results[results["Post_Status"]!="READY"].copy())
    source_after=validate_source_cache(cfg); require(source_before["sha256"]==source_after["sha256"],"FROZEN_SOURCE_CACHE_CHANGED"); require(non_before==non_after,"WORK_CACHE_NON_TARGET_MUTATION_GATE")
    work_sha=sha256_file(work)
    with sqlite3.connect(f"file:{work.resolve()}?mode=ro",uri=True) as c: work_counts={t:int(c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]) for t in ("price_daily","cache_state","batch_log")}
    retry_count=int(pd.to_numeric(new_batches.get("retry_count",pd.Series(dtype=float)),errors="coerce").fillna(0).sum())
    summary={"stage":STAGE,"version":VERSION,"run_mode":MODE,"status":"DEV / RESEARCH / SHADOW – NOT PRODUCTIVE","source_result_commit":cfg["source_result_commit"],"safe_cutoff":cfg["safe_cutoff"],"request_start":cfg["request_start"],"request_end_exclusive":cfg["request_end_exclusive"],"target_total":len(plan),"mapping_exact_retry_targets":len(mapping_ids),"data_quality_repair_targets":len(dq_ids),"manual_review_excluded":len(sets["manual_ids"]),"history_defer_excluded":len(sets["history_ids"]),"protected_instrument_fail_excluded":len(sets["protected_ids"]),"post_status_counts":dict(sorted(Counter(results["Post_Status"].astype(str)).items())),"controlled_result_counts":dict(sorted(Counter(results["Controlled_Result"].astype(str)).items())),"mapping_missing_after_normal_count":len(missing_normal),"logical_batch_count":len(logical),"provider_batch_log_new_count":len(new_batches),"identical_retry_count_from_batch_log":retry_count,"network_allowed":True,"stock_download_allowed":True,"stock_download_executed":True,"fx_download_allowed":False,"fx_download_executed":False,"provider_search_allowed":False,"provider_search_executed":False,"alpha_vantage_allowed":False,"alpha_vantage_executed":False,"automatic_mapping_override_allowed":False,"automatic_mapping_override_created":False,"frozen_source_cache_sha_before":source_before["sha256"],"frozen_source_cache_sha_after":source_after["sha256"],"work_cache_path":str(work),"work_cache_sha256":work_sha,"work_cache_counts":work_counts,"work_cache_non_target_digest_before":non_before,"work_cache_non_target_digest_after":non_after,"universe_mutation_allowed":False,"universe_mutated":False,"eligibility_promotion_allowed":False,"eligibility_promoted":False,"p0":False,"sector_rs":False,"swing_u3k_frozen_mutated":False,"productive":False,"run_timestamp_utc":now_utc(),"next_stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_MANUAL_MAPPING_EVIDENCE_REVIEW"}
    write_json(OUT/"summary_v0.40.json",summary); write_json(OUT/"stage_checkpoint_v0.40.json",{"stage":STAGE,"version":VERSION,"run_mode":MODE,"completed":True,"strong_gates_required":True,"source_result_commit":cfg["source_result_commit"],"work_cache_sha256":work_sha,"next_stage":summary["next_stage"]}); write_json(OUT/"manifest_v0.40.json",{"stage":STAGE,"version":VERSION,"run_mode":MODE,"source_result_commit":cfg["source_result_commit"],"outputs":sorted(p.name for p in OUT.iterdir()),"frozen_input_blobs":cfg["frozen_input_blobs"],"frozen_source_cache":source_after,"work_cache":{"path":str(work),"sha256":work_sha,"counts":work_counts},"productive":False})
    return summary


def strong_gates(config_path: Path) -> None:
    cfg=read_json(config_path); validate_frozen_inputs(cfg); source=validate_source_cache(cfg); exp=cfg["expected_source_counts"]
    plan=pd.read_csv(OUT/"target_plan_158_v0.40.csv",dtype=str,keep_default_na=False); req=pd.read_csv(OUT/"provider_request_ledger_v0.40.csv",dtype=str,keep_default_na=False); batches=pd.read_csv(OUT/"logical_batch_plan_v0.40.csv",dtype=str,keep_default_na=False); results=pd.read_csv(OUT/"controlled_results_158_v0.40.csv",dtype=str,keep_default_na=False); mr=pd.read_csv(OUT/"mapping_retry_results_151_v0.40.csv",dtype=str,keep_default_na=False); dq=pd.read_csv(OUT/"data_quality_repair_results_7_v0.40.csv",dtype=str,keep_default_na=False); blog=pd.read_csv(OUT/"provider_batch_log_new_v0.40.csv",dtype=str,keep_default_na=False); missing=pd.read_csv(OUT/"mapping_missing_after_normal_v0.40.csv",dtype=str,keep_default_na=False); summary=read_json(OUT/"summary_v0.40.json")
    expected_plan,source_sets=build_target_plan(cfg)
    require(len(plan)==int(exp["retry_data_total"]) and plan["WS_ID"].nunique()==len(plan),"STRONG_TARGET_158_GATE"); require(len(mr)==int(exp["mapping_exact_retry"]),"STRONG_MAPPING_151_GATE"); require(len(dq)==int(exp["data_quality_retry"]),"STRONG_DQ_7_GATE"); require(len(results)==len(plan) and results["WS_ID"].nunique()==len(results),"STRONG_RESULTS_158_GATE")
    plan_key=set(zip(plan["WS_ID"],plan["Gap_Family"],plan["Provider_Symbol"])); expected_key=set(zip(expected_plan["WS_ID"],expected_plan["Gap_Family"],expected_plan["Provider_Symbol"])); require(plan_key==expected_key,"STRONG_TARGET_PLAN_EQUALS_FROZEN_SOURCE_GATE")
    require(set(mr["Diagnostic_Classification"])=={"EXACT_PROVIDER_SYMBOL_NO_DATA"},"STRONG_MAPPING_EXACT_CLASS_GATE"); require((mr["Mapping_Override_Created"].str.lower()=="false").all(),"STRONG_NO_MAPPING_OVERRIDE_GATE"); require(set(dq["Diagnostic_Classification"])=={"INVALID_BAR_TARGETED_REPAIR_CANDIDATE","SUSPICIOUS_RETURN_TARGETED_REPAIR_CANDIDATE"},"STRONG_DQ_CLASS_GATE")
    target_ids=set(plan["WS_ID"]); request_ids=set(req["WS_ID"]); require(request_ids<=target_ids,"STRONG_REQUEST_OUTSIDE_TARGET_GATE"); require(not (request_ids & source_sets["manual_ids"]),"STRONG_REQUEST_MANUAL_REVIEW_FORBIDDEN"); require(not (request_ids & source_sets["history_ids"]),"STRONG_REQUEST_HISTORY_FORBIDDEN"); require(not (request_ids & source_sets["protected_ids"]),"STRONG_REQUEST_PROTECTED_FORBIDDEN"); require(set(req.loc[req["Phase"].str.startswith("MAPPING"),"WS_ID"])<=set(mr["WS_ID"]),"STRONG_MAPPING_REQUEST_SCOPE_GATE"); require(set(req.loc[req["Phase"]=="DQ_REPAIR","WS_ID"])==set(dq["WS_ID"]),"STRONG_DQ_REQUEST_SCOPE_GATE"); require((req.loc[req["Phase"].str.startswith("MAPPING"),"Repair_Pass"].str.lower()=="false").all(),"STRONG_MAPPING_REPAIR_FLAG_GATE"); require((req.loc[req["Phase"]=="DQ_REPAIR","Repair_Pass"].str.lower()=="true").all(),"STRONG_DQ_REPAIR_FLAG_GATE"); require(set(req["Request_Start"])=={cfg["request_start"]} and set(req["Request_End_Exclusive"])=={cfg["request_end_exclusive"]},"STRONG_FIXED_WINDOW_GATE")
    rescue_symbols=set(req.loc[req["Phase"]=="MAPPING_RESCUE","Provider_Symbol"]); missing_symbols=set(missing["Provider_Symbol"]) if "Provider_Symbol" in missing.columns else set(); require(rescue_symbols==missing_symbols,"STRONG_RESCUE_EQUALS_NORMAL_MISSING_GATE")
    require(len(blog)==len(batches),"STRONG_BATCH_LOG_COUNT_GATE")
    if not blog.empty and "retry_count" in blog.columns: require((pd.to_numeric(blog["retry_count"],errors="coerce").fillna(0)<=int(cfg["max_identical_retries"])).all(),"STRONG_IDENTICAL_RETRY_CEILING_GATE")
    require(summary["network_allowed"] is True and summary["stock_download_executed"] is True,"STRONG_STOCK_NETWORK_GATE"); require(summary["fx_download_executed"] is False and summary["provider_search_executed"] is False and summary["alpha_vantage_executed"] is False,"STRONG_FORBIDDEN_NETWORK_GATE"); require(summary["automatic_mapping_override_created"] is False,"STRONG_NO_AUTO_OVERRIDE_GATE"); require(summary["frozen_source_cache_sha_before"]==cfg["frozen_source_cache_sha256"]==summary["frozen_source_cache_sha_after"]==source["sha256"],"STRONG_SOURCE_CACHE_IMMUTABILITY_GATE"); require(summary["work_cache_non_target_digest_before"]==summary["work_cache_non_target_digest_after"],"STRONG_NON_TARGET_CACHE_IMMUTABILITY_GATE"); require(summary["universe_mutated"] is False and summary["eligibility_promoted"] is False and summary["p0"] is False and summary["sector_rs"] is False and summary["swing_u3k_frozen_mutated"] is False and summary["productive"] is False,"STRONG_NONPRODUCTIVE_NO_PROMOTION_GATE")
    work=Path(cfg["work_cache_path"]); require(work.is_file(),"STRONG_WORK_CACHE_MISSING"); require(sha256_file(work)==summary["work_cache_sha256"],"STRONG_WORK_CACHE_SHA_GATE")
    with sqlite3.connect(f"file:{work.resolve()}?mode=ro",uri=True) as c: max_day=c.execute("SELECT MAX(day) FROM price_daily").fetchone()[0]; require(not max_day or str(max_day)<=cfg["safe_cutoff"],"STRONG_FUTURE_BAR_GATE")
    validate_frozen_inputs(cfg); print("v0.40 CONTROLLED_RETRY_DATA_ONLY strong gates PASS")


def self_test() -> None:
    require(outcome_disposition("READY","",500)=="RECOVERED_READY_EVIDENCE_ONLY","SELF_READY"); require(outcome_disposition("WARMUP","INSUFFICIENT_HISTORY",90)=="DEFER_TEMPORAL_AFTER_DATA_RECOVERY","SELF_WARMUP"); require(outcome_disposition("QUARANTINE","X",500)=="RESIDUAL_DATA_QUALITY","SELF_QUARANTINE"); require(outcome_disposition("DOWNLOAD_FAILED","NO_DATA",0)=="RESIDUAL_NO_DATA","SELF_NO_DATA"); require(qmarks(3)=="?,?,?","SELF_QMARKS"); require(list(chunks([1,2,3,4,5],2))==[[1,2],[3,4],[5]],"SELF_CHUNKS"); print("v0.40 CONTROLLED_RETRY_DATA_ONLY self-test PASS")


if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default=str(DEFAULT_CONFIG)); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--validate-inputs",action="store_true"); ap.add_argument("--run",action="store_true"); ap.add_argument("--strong-gates",action="store_true"); args=ap.parse_args(); cfg_path=Path(args.config)
    if args.self_test: self_test()
    if args.validate_inputs:
        cfg=read_json(cfg_path); validate_frozen_inputs(cfg); validate_source_cache(cfg); build_target_plan(cfg); print("v0.40 frozen inputs and target scope PASS")
    if args.run: print(json.dumps(run_controlled(cfg_path),ensure_ascii=False,indent=2))
    if args.strong_gates: strong_gates(cfg_path)
