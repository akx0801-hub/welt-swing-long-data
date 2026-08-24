#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SCHEMA = "WELT_SWING_TARGETED_REFRESH_6_V0_3"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def read_cfg(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_sql(conn: sqlite3.Connection, sql: str, params=()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


def qmarks(n: int) -> str:
    return ",".join("?" for _ in range(n))


def load_targeted_universe(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    from price_cache import build_yahoo_symbol_map

    master = pd.read_csv(
        cfg["source_master"], keep_default_na=False, dtype=str
    )
    queue = pd.read_csv(
        cfg["source_queue"], keep_default_na=False, dtype=str
    )
    expected = {str(k): str(v) for k, v in cfg["expected_targets"].items()}

    if len(queue) != len(expected):
        raise SystemExit(f"Queue rows {len(queue)} != expected {len(expected)}")
    if queue["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate WS_ID in targeted refresh queue")

    got = dict(zip(queue["WS_ID"].astype(str), queue["Yahoo_Symbol"].astype(str)))
    if got != expected:
        raise SystemExit(
            "Target queue does not match frozen v0.3 target set. "
            + json.dumps({"expected": expected, "got": got}, ensure_ascii=False)
        )

    if "Active" not in master.columns:
        raise SystemExit("Remediated master lacks Active")
    active = master["Active"].astype(str).str.lower().eq("true")
    subset = master.loc[master["WS_ID"].astype(str).isin(expected)].copy()
    if len(subset) != len(expected):
        raise SystemExit("Not all target WS_IDs exist exactly once in remediated master")
    if subset["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate target WS_ID in remediated master")
    if not active.loc[subset.index].all():
        bad = subset.loc[~active.loc[subset.index], ["WS_ID", "Name"]].to_dict("records")
        raise SystemExit(f"Target contains inactive row(s): {bad}")

    master_symbols = dict(
        zip(subset["WS_ID"].astype(str), subset["Yahoo_Symbol"].astype(str))
    )
    if master_symbols != expected:
        raise SystemExit(
            "Remediated master target symbols do not match queue. "
            + json.dumps({"expected": expected, "master": master_symbols}, ensure_ascii=False)
        )

    active_master = master.loc[active].copy()
    for ws, sym in expected.items():
        other = active_master.loc[
            active_master["Yahoo_Symbol"].astype(str).eq(sym)
            & ~active_master["WS_ID"].astype(str).eq(ws),
            ["WS_ID", "Name", "Yahoo_Symbol"],
        ]
        if not other.empty:
            raise SystemExit(
                f"Provider-symbol collision for {ws} -> {sym}: "
                + json.dumps(other.to_dict("records"), ensure_ascii=False)
            )

    mapping = build_yahoo_symbol_map(subset)
    mapped = dict(
        zip(mapping["WS_ID"].astype(str), mapping["Yahoo_Symbol"].astype(str))
    )
    if mapped != expected:
        raise SystemExit(
            "Runtime provider mapping overrides the evidence-remediated target set. "
            + json.dumps({"expected": expected, "runtime": mapped}, ensure_ascii=False)
        )

    subset = subset.sort_values("WS_ID").reset_index(drop=True)
    queue = queue.sort_values("WS_ID").reset_index(drop=True)
    return subset, queue


def snapshot_before(conn: sqlite3.Connection, targets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ph = qmarks(len(targets))
    state = read_sql(
        conn,
        f"SELECT * FROM cache_state WHERE ws_id IN ({ph}) ORDER BY ws_id",
        targets,
    )
    counts = read_sql(
        conn,
        f"""
        SELECT ws_id, yahoo_symbol, COUNT(*) AS cached_price_rows,
               MIN(day) AS first_day, MAX(day) AS last_day
        FROM price_daily
        WHERE ws_id IN ({ph})
        GROUP BY ws_id, yahoo_symbol
        ORDER BY ws_id, yahoo_symbol
        """,
        targets,
    )
    return state, counts


def purge_targets(conn: sqlite3.Connection, targets: list[str]) -> None:
    ph = qmarks(len(targets))
    conn.execute(f"DELETE FROM price_daily WHERE ws_id IN ({ph})", targets)
    conn.execute(f"DELETE FROM cache_state WHERE ws_id IN ({ph})", targets)
    conn.commit()


def targeted_after(conn: sqlite3.Connection, targets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ph = qmarks(len(targets))
    state = read_sql(
        conn,
        f"SELECT * FROM cache_state WHERE ws_id IN ({ph}) ORDER BY ws_id",
        targets,
    )
    counts = read_sql(
        conn,
        f"""
        SELECT ws_id, yahoo_symbol, COUNT(*) AS refreshed_price_rows,
               MIN(day) AS first_day, MAX(day) AS last_day
        FROM price_daily
        WHERE ws_id IN ({ph})
        GROUP BY ws_id, yahoo_symbol
        ORDER BY ws_id, yahoo_symbol
        """,
        targets,
    )
    return state, counts


def build_target_features(
    conn: sqlite3.Connection,
    targeted_universe: pd.DataFrame,
    states: pd.DataFrame,
) -> pd.DataFrame:
    from non_ready_remediation_v0_2 import build_one_feature

    ready = set(
        states.loc[states["status"].astype(str).eq("READY"), "ws_id"].astype(str)
    )
    if not ready:
        return pd.DataFrame()

    meta = targeted_universe.set_index("WS_ID", drop=False)
    rows = []
    for ws in sorted(ready):
        px = read_sql(
            conn,
            "SELECT * FROM price_daily WHERE ws_id=? ORDER BY day",
            (ws,),
        )
        if ws not in meta.index:
            raise SystemExit(f"Missing target metadata for READY row {ws}")
        rows.append(build_one_feature(ws, px, meta.loc[ws]))
    return pd.DataFrame(rows)


def run_refresh(cfg: dict) -> dict[str, Any]:
    from price_cache import (
        FreeDataConfig,
        SQLitePriceCache,
        YFinanceBatchClient,
        YFinancePriceCacheRunner,
    )

    source_cache = Path(cfg["source_cache"])
    work_cache = Path(cfg["work_cache"])
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    targeted_universe, queue = load_targeted_universe(cfg)
    targets = targeted_universe["WS_ID"].astype(str).tolist()
    expected = {str(k): str(v) for k, v in cfg["expected_targets"].items()}

    if not source_cache.exists():
        raise SystemExit(f"Source SQLite cache missing: {source_cache}")

    work_cache.parent.mkdir(parents=True, exist_ok=True)
    if work_cache.exists():
        work_cache.unlink()
    shutil.copy2(source_cache, work_cache)

    raw_conn = sqlite3.connect(work_cache)
    try:
        before_state, before_counts = snapshot_before(raw_conn, targets)
        total_rows_before = int(
            raw_conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]
        )
        total_states_before = int(
            raw_conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]
        )
        purge_targets(raw_conn, targets)
    finally:
        raw_conn.close()

    before_state.to_csv(out_dir / "targeted_before_state_v0.3.csv", index=False)
    before_counts.to_csv(out_dir / "targeted_before_price_counts_v0.3.csv", index=False)
    targeted_universe.to_csv(out_dir / "targeted_universe_v0.3.csv", index=False)
    queue.to_csv(out_dir / "targeted_queue_frozen_v0.3.csv", index=False)

    free_cfg = FreeDataConfig(
        batch_size=int(cfg.get("batch_size", 6)),
        initial_period=str(cfg.get("initial_period", "2y")),
        pause_between_batches_seconds=float(
            cfg.get("pause_between_batches_seconds", 0.0)
        ),
        repair_anomalies=bool(cfg.get("repair_anomalies", True)),
    )

    cache = SQLitePriceCache(work_cache)
    try:
        client = YFinanceBatchClient(config=free_cfg)
        runner = YFinancePriceCacheRunner(cache, client, config=free_cfg)
        run_result = runner.run_initial(targeted_universe, as_of=date.today())
        cache.conn.commit()

        after_state, after_counts = targeted_after(cache.conn, targets)

        if len(after_state) != len(targets):
            raise SystemExit(
                f"Refresh did not create all target cache states: "
                f"{len(after_state)}/{len(targets)}"
            )

        observed = dict(
            zip(
                after_state["ws_id"].astype(str),
                after_state["yahoo_symbol"].astype(str),
            )
        )
        if observed != expected:
            raise SystemExit(
                "Post-refresh cache symbols mismatch. "
                + json.dumps({"expected": expected, "observed": observed}, ensure_ascii=False)
            )

        features = build_target_features(cache.conn, targeted_universe, after_state)

        ph = qmarks(len(targets))
        batch_rows = read_sql(
            cache.conn,
            f"""
            SELECT * FROM batch_log
            WHERE batch_id IN (
                SELECT DISTINCT batch_id FROM cache_state
                WHERE ws_id IN ({ph}) AND batch_id IS NOT NULL
            )
            ORDER BY finished_utc DESC
            """,
            targets,
        )

        total_rows_after = int(
            cache.conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]
        )
        total_states_after = int(
            cache.conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]
        )
    finally:
        cache.close()

    after_state.to_csv(out_dir / "targeted_after_state_v0.3.csv", index=False)
    after_counts.to_csv(out_dir / "targeted_after_price_counts_v0.3.csv", index=False)
    features.to_csv(out_dir / "targeted_ready_features_v0.3.csv", index=False)
    batch_rows.to_csv(out_dir / "targeted_batch_log_v0.3.csv", index=False)

    status_counts = {
        str(k): int(v)
        for k, v in after_state["status"].value_counts(dropna=False).to_dict().items()
    }
    hard = set(str(x) for x in cfg["hard_failure_statuses"])
    hard_rows = after_state.loc[after_state["status"].astype(str).isin(hard)].copy()
    promotion_recommended = hard_rows.empty

    ready_count = int(status_counts.get("READY", 0))
    if len(features) != ready_count:
        raise SystemExit(
            f"Target feature rows {len(features)} != target READY rows {ready_count}"
        )

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "TARGETED_REFRESH_6_COMPLETE",
        "target_rows": int(len(targets)),
        "target_symbols": expected,
        "refresh_mode": "FULL_2Y_TARGETED",
        "data_source": "YFINANCE_FREE",
        "source_cache_rows_before": total_rows_before,
        "source_cache_states_before": total_states_before,
        "work_cache_rows_after": total_rows_after,
        "work_cache_states_after": total_states_after,
        "status_counts": status_counts,
        "ready_count": ready_count,
        "target_feature_rows": int(len(features)),
        "hard_failure_rows": int(len(hard_rows)),
        "hard_failure_ws_ids": hard_rows["ws_id"].astype(str).tolist(),
        "cache_promotion_recommended": bool(promotion_recommended),
        "run_result": run_result,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "Only the six frozen targeted-refresh securities are downloaded.",
            "The source cache is copied first; destructive purge/reload occurs only in the work cache.",
            "All six target histories are purged in the work copy before a fresh 2y batch download, preventing old/new provider-symbol history mixing.",
            "The standard bounded rescue and targeted repair=True logic remains active.",
            "WARMUP, QUARANTINE and STALE are legitimate diagnostic outcomes and do not by themselves block cache promotion.",
            "DOWNLOAD_FAILED or MAPPING_PENDING blocks promotion of the work cache.",
            "No P0, ranking, news, P1-P5 or productive trading action is run."
        ],
    }
    (out_dir / "summary_v0.3.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/targeted_refresh_6_v0.3.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        expected = {
            "WS:XASX:XYX": "XYZ.AX",
            "WS:XMEX:ALFAA": "SIGMAFA.MX",
            "WS:XNZE:GMT": "GNZ.NZ",
            "WS:US:IESC": "IESC",
            "WS:SRC:ZA_TOP40:3CA42D3A25639D8E": "SOL.JO",
            "WS:US:MNST": "MNST",
        }
        assert len(expected) == 6
        assert len(set(expected.values())) == 6
        assert qmarks(6) == "?,?,?,?,?,?"
        print("TARGETED_REFRESH_6_V0_3_SELF_TEST_PASS")
        return 0

    cfg = read_cfg(Path(args.config))
    run_refresh(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
