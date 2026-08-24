#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_QA_FILTERED_BAR_POLICY_PROMOTION_V0_4"
EXPECTED_CORE_GIT_BLOB = "52b53ba95da595af5221afbf4cb21b14bcc12def"

SOURCE_MASTER = Path("universe/Welt-Swing-Universe-Master-RemediatedData-v0.8.csv")
SOURCE_CACHE = Path("runtime_cache/full_3663_prices.sqlite")
WORK_CACHE = Path("runtime_cache/full_3663_prices_qa_v04_work.sqlite")
OUTPUT_DIR = Path("output_qa_policy_promotion_v0_4")
CORE_PATH = Path("scripts/price_cache.py")
FEATURE_BUILDER_PATH = Path("scripts/feature_builder.py")

AS_OF = date(2026, 8, 24)

EXPECTED_ACTIVE_ROWS = 3657
EXPECTED_READY_BEFORE = 3582
EXPECTED_PROMOTIONS = 20
EXPECTED_READY_AFTER = 3602
EXPECTED_STATUS_AFTER = {
    "READY": 3602,
    "QUARANTINE": 34,
    "WARMUP": 20,
    "STALE": 1,
}
EXPECTED_INACTIVE_STATE_IDS = {
    "WS:XASX:IFL",
    "WS:XASX:NSR",
    "WS:XMEX:ELEKTRA",
    "WS:XNZE:ARV",
    "WS:XNZE:MNW",
    "WS:US:CWEN.A",
}
EXPECTED_TARGETED_REFRESH_STATE = {
    "WS:XASX:XYX": ("XYZ.AX", "READY"),
    "WS:XMEX:ALFAA": ("SIGMAFA.MX", "READY"),
    "WS:XNZE:GMT": ("GNZ.NZ", "READY"),
    "WS:SRC:ZA_TOP40:3CA42D3A25639D8E": ("SOL.JO", "READY"),
    "WS:US:IESC": ("IESC", "STALE"),
    "WS:US:MNST": ("MNST", "QUARANTINE"),
}

P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    hdr = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(hdr + data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_core() -> dict[str, str]:
    if not CORE_PATH.exists():
        raise SystemExit(f"Core file missing: {CORE_PATH}")

    before_blob = git_blob_sha(CORE_PATH)
    if before_blob != EXPECTED_CORE_GIT_BLOB:
        raise SystemExit(
            "Core price_cache.py is not the frozen pre-promotion version. "
            f"Expected git blob {EXPECTED_CORE_GIT_BLOB}, got {before_blob}."
        )

    text = CORE_PATH.read_text(encoding="utf-8")

    old_cfg = '''    ready_unique_bars: int = 260
    stale_calendar_days: int = 10
    max_identical_retries: int = 1
'''
    new_cfg = '''    ready_unique_bars: int = 260
    # Promoted QA v0.4 policy: raw malformed bars stay in cache, but up to two
    # isolated invalid bars may be excluded from technical calculations when
    # they are <=1% of the series and at least 260 valid bars remain.
    max_filterable_invalid_bars: int = 2
    max_filterable_invalid_share: float = 0.01
    stale_calendar_days: int = 10
    max_identical_retries: int = 1
'''
    if text.count(old_cfg) != 1:
        raise SystemExit("Could not locate unique FreeDataConfig insertion point")
    text = text.replace(old_cfg, new_cfg, 1)

    old_validate = '''        if self.min_valid_bars <= 0 or self.ready_unique_bars < self.min_valid_bars:
            raise ValueError("invalid bar thresholds")
        if self.max_identical_retries not in (0, 1):
'''
    new_validate = '''        if self.min_valid_bars <= 0 or self.ready_unique_bars < self.min_valid_bars:
            raise ValueError("invalid bar thresholds")
        if not (0 <= self.max_filterable_invalid_bars <= 10):
            raise ValueError("max_filterable_invalid_bars out of range")
        if not (0.0 <= self.max_filterable_invalid_share <= 0.05):
            raise ValueError("max_filterable_invalid_share out of range")
        if self.max_identical_retries not in (0, 1):
'''
    if text.count(old_validate) != 1:
        raise SystemExit("Could not locate unique FreeDataConfig validation block")
    text = text.replace(old_validate, new_validate, 1)

    old_qa = '''    # One isolated malformed historical bar does not invalidate an otherwise
    # deep, liquid two-year series. It remains preserved in RAW cache for audit,
    # but downstream technical features must exclude it. Two or more malformed
    # bars still quarantine the whole security unless a later repair succeeds.
    isolated_invalid_bar = (
        invalid_rows == 1
        and valid_bars >= config.ready_unique_bars
    )

    xv = x.loc[valid].copy() if unique_bars else x.copy()
'''
    new_qa = '''    # Promoted QA v0.4 policy.
    #
    # Raw malformed bars are NEVER deleted here. Downstream technical features
    # already exclude bars failing technical_valid_mask(). A security may remain
    # eligible after filtering only when:
    #   - 1..max_filterable_invalid_bars invalid bars are present,
    #   - those rows are <= max_filterable_invalid_share of the raw series,
    #   - at least ready_unique_bars valid observations remain.
    #
    # Suspicious returns and staleness are checked below and still override
    # filtered-bar eligibility. This prevents the three overlapping ZA scale
    # anomaly cases from being promoted simply because they have only two bad bars.
    invalid_share = (
        float(invalid_rows / unique_bars) if unique_bars else 0.0
    )
    filterable_invalid_bars = (
        0 < invalid_rows <= config.max_filterable_invalid_bars
        and invalid_share <= config.max_filterable_invalid_share
        and valid_bars >= config.ready_unique_bars
    )

    xv = x.loc[valid].copy() if unique_bars else x.copy()
'''
    if text.count(old_qa) != 1:
        raise SystemExit("Could not locate unique pre-promotion invalid-bar QA block")
    text = text.replace(old_qa, new_qa, 1)

    old_status = '''    if unique_bars == 0:
        status, reason = "DOWNLOAD_FAILED", "NO_DATA"
    elif invalid_rows > 0 and not isolated_invalid_bar:
        status, reason = "QUARANTINE", "INVALID_OHLC_OR_VOLUME"
    elif suspicious_returns > 0:
        status, reason = "QUARANTINE", "SUSPICIOUS_RETURN_NEEDS_REPAIR"
    elif stale:
        status, reason = "STALE", "LAST_BAR_TOO_OLD"
    elif unique_bars >= config.ready_unique_bars and valid_bars >= config.min_valid_bars:
        status = "READY"
        if isolated_invalid_bar:
            reason = "ISOLATED_INVALID_BAR_EXCLUDED"
    else:
        status, reason = "WARMUP", "INSUFFICIENT_HISTORY"
'''
    new_status = '''    if unique_bars == 0:
        status, reason = "DOWNLOAD_FAILED", "NO_DATA"
    elif invalid_rows > 0 and not filterable_invalid_bars:
        status, reason = "QUARANTINE", "INVALID_OHLC_OR_VOLUME"
    elif suspicious_returns > 0:
        status, reason = "QUARANTINE", "SUSPICIOUS_RETURN_NEEDS_REPAIR"
    elif stale:
        status, reason = "STALE", "LAST_BAR_TOO_OLD"
    elif unique_bars >= config.ready_unique_bars and valid_bars >= config.min_valid_bars:
        status = "READY"
        if invalid_rows == 1:
            reason = "ISOLATED_INVALID_BAR_EXCLUDED"
        elif invalid_rows > 1:
            reason = "FILTERED_INVALID_BARS_EXCLUDED"
    else:
        status, reason = "WARMUP", "INSUFFICIENT_HISTORY"
'''
    if text.count(old_status) != 1:
        raise SystemExit("Could not locate unique pre-promotion status decision block")
    text = text.replace(old_status, new_status, 1)

    CORE_PATH.write_text(text, encoding="utf-8")
    after_blob = git_blob_sha(CORE_PATH)

    return {
        "core_git_blob_before": before_blob,
        "core_git_blob_after": after_blob,
        "core_sha256_after": sha256_file(CORE_PATH),
    }


def import_core():
    script_dir = str(CORE_PATH.resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    if "price_cache" in sys.modules:
        del sys.modules["price_cache"]
    return importlib.import_module("price_cache")


def synthetic_policy_test() -> dict[str, str]:
    pc = import_core()
    cfg = pc.FreeDataConfig()

    if cfg.max_filterable_invalid_bars != 2:
        raise SystemExit("Promoted config max_filterable_invalid_bars != 2")
    if abs(cfg.max_filterable_invalid_share - 0.01) > 1e-12:
        raise SystemExit("Promoted config max_filterable_invalid_share != 0.01")

    idx = pd.date_range("2025-01-01", periods=300, freq="B")
    base = pd.DataFrame(
        {
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "close": 100.0,
            "adj_close": 100.0,
            "volume": 1000.0,
            "dividends": 0.0,
            "stock_splits": 0.0,
            "repaired": 0.0,
        },
        index=idx,
    )

    two = base.copy()
    two.iloc[10, two.columns.get_loc("high")] = 90.0
    two.iloc[11, two.columns.get_loc("high")] = 90.0
    q_two = pc.qa_symbol_frame(two, config=cfg, as_of=idx[-1].date())
    assert q_two["status"] == "READY", q_two
    assert q_two["reason_code"] == "FILTERED_INVALID_BARS_EXCLUDED", q_two
    assert q_two["valid_bars"] == 298, q_two

    three = two.copy()
    three.iloc[12, three.columns.get_loc("high")] = 90.0
    q_three = pc.qa_symbol_frame(three, config=cfg, as_of=idx[-1].date())
    assert q_three["status"] == "QUARANTINE", q_three
    assert q_three["reason_code"] == "INVALID_OHLC_OR_VOLUME", q_three

    suspicious = two.copy()
    suspicious.iloc[150, suspicious.columns.get_loc("open")] = 200.0
    suspicious.iloc[150, suspicious.columns.get_loc("high")] = 204.0
    suspicious.iloc[150, suspicious.columns.get_loc("low")] = 196.0
    suspicious.iloc[150, suspicious.columns.get_loc("close")] = 200.0
    suspicious.iloc[150, suspicious.columns.get_loc("adj_close")] = 200.0
    q_susp = pc.qa_symbol_frame(suspicious, config=cfg, as_of=idx[-1].date())
    assert q_susp["status"] == "QUARANTINE", q_susp
    assert q_susp["reason_code"] == "SUSPICIOUS_RETURN_NEEDS_REPAIR", q_susp

    stale = two.copy()
    stale_as_of = idx[-1].date().replace(year=idx[-1].year + 1)
    q_stale = pc.qa_symbol_frame(stale, config=cfg, as_of=stale_as_of)
    assert q_stale["status"] == "STALE", q_stale
    assert q_stale["reason_code"] == "LAST_BAR_TOO_OLD", q_stale

    short = base.iloc[:261].copy()
    short.iloc[10, short.columns.get_loc("high")] = 90.0
    short.iloc[11, short.columns.get_loc("high")] = 90.0
    q_short = pc.qa_symbol_frame(short, config=cfg, as_of=short.index[-1].date())
    assert q_short["status"] == "QUARANTINE", q_short
    assert q_short["reason_code"] == "INVALID_OHLC_OR_VOLUME", q_short

    return {
        "two_invalid": q_two["status"],
        "three_invalid": q_three["status"],
        "two_invalid_plus_suspicious": q_susp["status"],
        "two_invalid_plus_stale": q_stale["status"],
        "two_invalid_only_259_valid": q_short["status"],
    }


def load_master() -> pd.DataFrame:
    if not SOURCE_MASTER.exists():
        raise SystemExit(f"Remediated master missing: {SOURCE_MASTER}")
    master = pd.read_csv(SOURCE_MASTER, keep_default_na=False, dtype=str)
    if len(master) != 3664:
        raise SystemExit(f"Expected 3664 master rows, got {len(master)}")
    if master["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate WS_ID in remediated master")
    active_mask = master["Active"].astype(str).str.lower().eq("true")
    active = master.loc[active_mask].copy()
    if len(active) != EXPECTED_ACTIVE_ROWS:
        raise SystemExit(f"Expected {EXPECTED_ACTIVE_ROWS} active rows, got {len(active)}")
    if active["Yahoo_Symbol"].astype(str).str.strip().eq("").any():
        raise SystemExit("Active master contains blank Yahoo_Symbol")
    if active["Yahoo_Symbol"].astype(str).duplicated().any():
        dup = active.loc[
            active["Yahoo_Symbol"].astype(str).duplicated(keep=False),
            ["WS_ID", "Name", "Yahoo_Symbol"],
        ]
        raise SystemExit(
            "Active master contains provider-symbol duplicates: "
            + json.dumps(dup.head(20).to_dict("records"), ensure_ascii=False)
        )
    return active


def verify_post_targeted_cache(conn: sqlite3.Connection) -> None:
    states = pd.read_sql_query("SELECT ws_id,yahoo_symbol,status FROM cache_state", conn)
    if len(states) != 3663:
        raise SystemExit(
            "Expected restored post-targeted cache with 3663 states, "
            f"got {len(states)}"
        )
    got = states.set_index("ws_id")[["yahoo_symbol", "status"]]
    for ws, (symbol, status) in EXPECTED_TARGETED_REFRESH_STATE.items():
        if ws not in got.index:
            raise SystemExit(f"Post-targeted cache missing {ws}")
        r = got.loc[ws]
        if str(r["yahoo_symbol"]) != symbol or str(r["status"]) != status:
            raise SystemExit(
                f"Restored cache is not the validated post-targeted cache for {ws}: "
                f"got {(r['yahoo_symbol'], r['status'])}, expected {(symbol, status)}"
            )


def requalify() -> dict[str, Any]:
    pc = import_core()
    active = load_master()
    active_ids = set(active["WS_ID"].astype(str))
    active_meta = active.set_index("WS_ID", drop=False)

    if not SOURCE_CACHE.exists():
        raise SystemExit(f"Source cache missing: {SOURCE_CACHE}")

    WORK_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if WORK_CACHE.exists():
        WORK_CACHE.unlink()
    shutil.copy2(SOURCE_CACHE, WORK_CACHE)

    conn = sqlite3.connect(WORK_CACHE)
    try:
        verify_post_targeted_cache(conn)

        before_all = pd.read_sql_query("SELECT * FROM cache_state", conn)
        before_active = before_all.loc[before_all["ws_id"].astype(str).isin(active_ids)].copy()
        before_inactive = before_all.loc[~before_all["ws_id"].astype(str).isin(active_ids)].copy()

        inactive_ids = set(before_inactive["ws_id"].astype(str))
        if inactive_ids != EXPECTED_INACTIVE_STATE_IDS:
            raise SystemExit(
                "Inactive cache-state set mismatch. "
                + json.dumps(
                    {"expected": sorted(EXPECTED_INACTIVE_STATE_IDS), "got": sorted(inactive_ids)},
                    ensure_ascii=False,
                )
            )
        if len(before_active) != EXPECTED_ACTIVE_ROWS:
            raise SystemExit(
                f"Expected {EXPECTED_ACTIVE_ROWS} active cache states before, got {len(before_active)}"
            )
        ready_before = int(before_active["status"].astype(str).eq("READY").sum())
        if ready_before != EXPECTED_READY_BEFORE:
            raise SystemExit(f"Expected READY before={EXPECTED_READY_BEFORE}, got {ready_before}")

        if inactive_ids:
            marks = ",".join("?" for _ in inactive_ids)
            conn.execute(
                f"DELETE FROM cache_state WHERE ws_id IN ({marks})",
                list(sorted(inactive_ids)),
            )
            conn.commit()

        cfg = pc.FreeDataConfig()
        state_rows = []
        for ws in sorted(active_ids):
            state = pd.read_sql_query(
                "SELECT * FROM cache_state WHERE ws_id=?",
                conn,
                params=[ws],
            )
            if len(state) != 1:
                raise SystemExit(f"Expected one cache_state row for {ws}, got {len(state)}")
            old = state.iloc[0]

            master_symbol = str(active_meta.loc[ws, "Yahoo_Symbol"])
            if str(old["yahoo_symbol"]) != master_symbol:
                raise SystemExit(
                    f"Active provider symbol mismatch for {ws}: cache={old['yahoo_symbol']} master={master_symbol}"
                )

            px = pd.read_sql_query(
                "SELECT day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired "
                "FROM price_daily WHERE ws_id=? ORDER BY day",
                conn,
                params=[ws],
            )
            if px.empty:
                qa = {
                    "status": "DOWNLOAD_FAILED",
                    "reason_code": "NO_DATA",
                    "unique_bars": 0,
                    "valid_bars": 0,
                    "repaired_rows": 0,
                    "suspicious_returns": 0,
                    "zero_volume_share": None,
                    "first_bar_date": None,
                    "last_bar_date": None,
                }
            else:
                px["day"] = pd.to_datetime(px["day"], errors="coerce")
                px = px.dropna(subset=["day"]).set_index("day")
                qa = pc.qa_symbol_frame(px, config=cfg, as_of=AS_OF)

            state_rows.append(
                {
                    "ws_id": ws,
                    "yahoo_symbol": str(old["yahoo_symbol"]),
                    "mapping_status": old["mapping_status"],
                    "status": qa["status"],
                    "reason_code": qa["reason_code"],
                    "unique_bars": qa["unique_bars"],
                    "valid_bars": qa["valid_bars"],
                    "repaired_rows": qa["repaired_rows"],
                    "suspicious_returns": qa["suspicious_returns"],
                    "zero_volume_share": qa["zero_volume_share"],
                    "first_bar_date": qa["first_bar_date"],
                    "last_bar_date": qa["last_bar_date"],
                    "last_fetch_utc": old["last_fetch_utc"],
                    "batch_id": old["batch_id"],
                    "last_error": old["last_error"],
                }
            )

        cols = [
            "ws_id","yahoo_symbol","mapping_status","status","reason_code",
            "unique_bars","valid_bars","repaired_rows","suspicious_returns",
            "zero_volume_share","first_bar_date","last_bar_date",
            "last_fetch_utc","batch_id","last_error",
        ]
        sql = f"INSERT INTO cache_state ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)}) " \
              f"ON CONFLICT(ws_id) DO UPDATE SET {','.join(f'{c}=excluded.{c}' for c in cols[1:])}"
        conn.executemany(sql, [[r.get(c) for c in cols] for r in state_rows])
        conn.commit()

        after = pd.read_sql_query("SELECT * FROM cache_state", conn)
        if len(after) != EXPECTED_ACTIVE_ROWS:
            raise SystemExit(f"Expected {EXPECTED_ACTIVE_ROWS} states after alignment, got {len(after)}")

        after_counts = {
            str(k): int(v) for k, v in after["status"].value_counts().to_dict().items()
        }
        if after_counts != EXPECTED_STATUS_AFTER:
            raise SystemExit(
                "Post-promotion status counts mismatch. "
                + json.dumps({"expected": EXPECTED_STATUS_AFTER, "got": after_counts}, ensure_ascii=False)
            )

        before_idx = before_active.set_index("ws_id")
        after_idx = after.set_index("ws_id")
        changed = []
        for ws in sorted(active_ids):
            b = before_idx.loc[ws]
            a = after_idx.loc[ws]
            if str(b["status"]) != str(a["status"]) or str(b.get("reason_code", "")) != str(a.get("reason_code", "")):
                changed.append(
                    {
                        "WS_ID": ws,
                        "Name": str(active_meta.loc[ws, "Name"]),
                        "Yahoo_Symbol": str(a["yahoo_symbol"]),
                        "Status_Before": str(b["status"]),
                        "Reason_Before": str(b.get("reason_code", "")),
                        "Status_After": str(a["status"]),
                        "Reason_After": str(a.get("reason_code", "")),
                        "Unique_Bars": int(a["unique_bars"]),
                        "Valid_Bars": int(a["valid_bars"]),
                        "Suspicious_Returns": int(a["suspicious_returns"]),
                    }
                )

        changed_df = pd.DataFrame(changed)
        promotions = changed_df.loc[
            changed_df["Status_Before"].eq("QUARANTINE")
            & changed_df["Reason_Before"].eq("INVALID_OHLC_OR_VOLUME")
            & changed_df["Status_After"].eq("READY")
            & changed_df["Reason_After"].eq("FILTERED_INVALID_BARS_EXCLUDED")
        ].copy()

        if len(promotions) != EXPECTED_PROMOTIONS:
            raise SystemExit(f"Expected {EXPECTED_PROMOTIONS} exact QA promotions, got {len(promotions)}")

        unexpected_changes = changed_df.loc[
            ~changed_df["WS_ID"].isin(promotions["WS_ID"])
            & ~(changed_df["Status_Before"].eq("READY") & changed_df["Status_After"].eq("READY"))
        ].copy()
        if not unexpected_changes.empty:
            raise SystemExit(
                "Unexpected non-promotion status changes: "
                + json.dumps(unexpected_changes.head(30).to_dict("records"), ensure_ascii=False)
            )

        script_dir = str(FEATURE_BUILDER_PATH.resolve().parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        if "feature_builder" in sys.modules:
            del sys.modules["feature_builder"]
        fb = importlib.import_module("feature_builder")
        features = fb.build_features(WORK_CACHE, SOURCE_MASTER)

        if len(features) != EXPECTED_READY_AFTER:
            raise SystemExit(f"Expected {EXPECTED_READY_AFTER} feature rows, got {len(features)}")
        if features["WS_ID"].astype(str).duplicated().any():
            raise SystemExit("Duplicate WS_ID in promoted feature output")

        residual = active[["WS_ID","Name","Primary_Universe_Index","Yahoo_Symbol"]].merge(
            after[["ws_id","status","reason_code","unique_bars","valid_bars","suspicious_returns","first_bar_date","last_bar_date"]],
            left_on="WS_ID",
            right_on="ws_id",
            how="left",
        )
        residual = residual.loc[~residual["status"].eq("READY")].copy()

        price_rows_retained = int(conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        state_rows_after = int(conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
    finally:
        conn.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    before_active.to_csv(OUTPUT_DIR / "active_state_before_v0.4.csv", index=False)
    before_inactive.to_csv(OUTPUT_DIR / "inactive_states_removed_v0.4.csv", index=False)
    after.to_csv(OUTPUT_DIR / "active_state_after_v0.4.csv", index=False)
    changed_df.to_csv(OUTPUT_DIR / "state_changes_v0.4.csv", index=False)
    promotions.to_csv(OUTPUT_DIR / "qa_filtered_promotions_v0.4.csv", index=False)
    residual.to_csv(OUTPUT_DIR / "residual_non_ready_v0.4.csv", index=False)
    features.to_csv(OUTPUT_DIR / "features_active_v0.4.csv", index=False)

    return {
        "status_counts_after": EXPECTED_STATUS_AFTER,
        "ready_before": EXPECTED_READY_BEFORE,
        "promotions": len(promotions),
        "ready_after": EXPECTED_READY_AFTER,
        "feature_rows": len(features),
        "inactive_state_rows_removed": len(before_inactive),
        "price_rows_retained": price_rows_retained,
        "state_rows_after": state_rows_after,
        "residual_non_ready_rows": len(residual),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch-core", action="store_true")
    ap.add_argument("--requalify", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        assert EXPECTED_READY_AFTER - EXPECTED_READY_BEFORE == EXPECTED_PROMOTIONS
        assert sum(EXPECTED_STATUS_AFTER.values()) == EXPECTED_ACTIVE_ROWS
        assert len(EXPECTED_INACTIVE_STATE_IDS) == 6
        assert len(EXPECTED_TARGETED_REFRESH_STATE) == 6
        print("QA_FILTERED_POLICY_PROMOTION_V0_4_SELF_TEST_PASS")
        return 0

    if not args.patch_core and not args.requalify:
        raise SystemExit("Choose --patch-core and/or --requalify")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "IN_PROGRESS",
        "as_of_date": AS_OF.isoformat(),
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
    }

    if args.patch_core:
        payload["core_patch"] = patch_core()
        payload["synthetic_policy_test"] = synthetic_policy_test()

    if args.requalify:
        payload["core_git_blob_current"] = git_blob_sha(CORE_PATH)
        payload["core_sha256_current"] = sha256_file(CORE_PATH)
        payload["requalification"] = requalify()

    payload["run_status"] = "QA_FILTERED_BAR_POLICY_PROMOTION_V0_4_COMPLETE"
    payload["notes"] = [
        "The promoted core policy accepts at most two isolated invalid bars only when they are <=1% of the series and at least 260 valid bars remain.",
        "Suspicious returns override filtered-bar eligibility and remain quarantined.",
        "Staleness overrides filtered-bar eligibility and remains STALE.",
        "Raw malformed price rows are retained; feature_builder excludes them from technical calculations.",
        "Exactly 20 previously shadow-tested rows are promoted from QUARANTINE/INVALID_OHLC_OR_VOLUME to READY/FILTERED_INVALID_BARS_EXCLUDED.",
        "Six delisted/retired cache_state rows are removed so operational state coverage aligns to the 3,657 active remediated universe; their historical price_daily rows are retained for audit.",
        "No price/history download occurs in this workflow.",
        "P0 remains off.",
    ]
    (OUTPUT_DIR / "summary_v0.4.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
