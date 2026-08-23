#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import sqlite3
import sys

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from price_cache import (  # noqa: E402
    FreeDataConfig, SQLitePriceCache, YFinanceBatchClient, YFinancePriceCacheRunner,
    build_yahoo_symbol_map,
)
from feature_builder import build_features  # noqa: E402


def sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_cfg(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    try:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
    except Exception:
        return pd.DataFrame()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/run_config.json")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    cfgj = load_cfg(cfg_path)
    universe_path = Path(cfgj["universe_file"])
    db_path = Path(cfgj.get("db_path", "runtime_cache/market_prices.sqlite"))
    output_dir = Path(cfgj.get("output_dir", "output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not universe_path.exists():
        raise SystemExit(f"Universe file missing: {universe_path}")
    universe = pd.read_csv(universe_path)
    required = {"WS_ID", "Primary_Ticker", "Primary_MIC"}
    miss = required - set(universe.columns)
    if miss:
        raise SystemExit(f"Universe missing required columns: {sorted(miss)}")
    if len(universe) == 0:
        raise SystemExit("Universe is empty. For full mode, first populate universe/u3k_master.csv")

    batch_size = int(cfgj.get("batch_size", 10))
    free_cfg = FreeDataConfig(
        batch_size=batch_size,
        initial_period=str(cfgj.get("initial_period", "2y")),
        overlap_calendar_days=int(cfgj.get("overlap_calendar_days", 14)),
        pause_between_batches_seconds=float(cfgj.get("pause_between_batches_seconds", 0.0)),
        repair_anomalies=bool(cfgj.get("repair_anomalies", True)),
    )

    mapping = build_yahoo_symbol_map(universe)
    mapping.to_csv(output_dir / "mapping_audit.csv", index=False)

    cache = SQLitePriceCache(db_path)
    try:
        client = YFinanceBatchClient(config=free_cfg)
        runner = YFinancePriceCacheRunner(cache, client, config=free_cfg)
        mode = str(cfgj.get("mode", "auto")).lower()
        existing = cache.counts()["price_rows"]
        if mode == "initial" or (mode == "auto" and existing == 0):
            run_result = runner.run_initial(universe, as_of=date.today())
            effective_mode = "INITIAL"
        else:
            # price_cache adapter internally adds one calendar day because yfinance end= is exclusive.
            run_result = runner.run_incremental(universe, end=date.today(), as_of=date.today())
            effective_mode = "INCREMENTAL"
        cache.conn.commit()

        states = read_table(cache.conn, "cache_state")
        batches = read_table(cache.conn, "batch_log")
    finally:
        cache.close()

    # Merge human-readable universe metadata into state export.
    meta_cols = [c for c in ["WS_ID","Name","ISIN","Country","Primary_Ticker","Primary_Exchange","Primary_MIC","Primary_Currency","Primary_Universe_Index","Index_Tags"] if c in universe.columns]
    meta = universe[meta_cols].drop_duplicates("WS_ID") if "WS_ID" in universe.columns else pd.DataFrame()
    if not states.empty and not meta.empty:
        states = meta.merge(states, left_on="WS_ID", right_on="ws_id", how="right")
    states.to_csv(output_dir / "cache_status.csv", index=False)
    errors = states[states["status"] != "READY"].copy() if not states.empty and "status" in states.columns else pd.DataFrame()
    errors.to_csv(output_dir / "errors.csv", index=False)
    if not batches.empty:
        batches = batches.sort_values("finished_utc", ascending=False).head(250)
    batches.to_csv(output_dir / "batch_log_latest.csv", index=False)

    features = build_features(db_path, universe_path)
    features.to_csv(output_dir / "features_latest.csv", index=False)

    status_counts = states["status"].value_counts(dropna=False).to_dict() if not states.empty and "status" in states.columns else {}
    universe_count = int(len(universe))
    mapped_count = int(mapping["Yahoo_Symbol"].notna().sum())
    ready = int(status_counts.get("READY", 0))
    run_status = "FAILED" if universe_count > 0 and ready == 0 else ("COMPLETE" if ready == universe_count else "PARTIAL")

    coverage = {
        "schema": "WELT_SWING_LONG_FREE_DATA_COVERAGE_V0_1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_mode": effective_mode,
        "run_status": run_status,
        "data_source": "YFINANCE_FREE",
        "alpha_vantage_allowed": False,
        "productive_trading_authority": False,
        "universe_file": str(universe_path),
        "universe_count": universe_count,
        "mapped_count": mapped_count,
        "mapping_coverage_pct": round(100.0 * mapped_count / universe_count, 4) if universe_count else 0.0,
        "ready_count": ready,
        "price_ready_coverage_pct": round(100.0 * ready / universe_count, 4) if universe_count else 0.0,
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "features_rows": int(len(features)),
        "p0_status": "NOT_RUN_PARAMETERS_NOT_YET_PROMOTED",
        "run_result": run_result,
        "notes": [
            "Universe identity remains independent of Yahoo symbol mapping.",
            "Raw OHLCV is cached; features_latest uses split-only technical normalization.",
            "No paid provider or API key is used.",
            "No Alpha Vantage adapter or fallback exists.",
            "P0 candidate filtering is intentionally not executed in this starter package.",
        ],
    }
    (output_dir / "coverage.json").write_text(json.dumps(coverage, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    manifest_files = [
        universe_path, output_dir / "mapping_audit.csv", output_dir / "cache_status.csv",
        output_dir / "errors.csv", output_dir / "batch_log_latest.csv",
        output_dir / "features_latest.csv", output_dir / "coverage.json",
    ]
    manifest = {
        "schema": "WELT_SWING_LONG_FREE_DATA_MANIFEST_V0_1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "files": {str(p): sha256_file(p) for p in manifest_files if p.exists()},
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Human-readable one-line status for the Actions log.
    print(json.dumps({
        "run_status": run_status,
        "universe": universe_count,
        "mapped": mapped_count,
        "ready": ready,
        "features": len(features),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
