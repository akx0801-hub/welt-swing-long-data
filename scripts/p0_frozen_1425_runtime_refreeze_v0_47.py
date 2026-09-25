#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3

SOURCE_RUN_ID = 36138138825
SOURCE_ARTIFACT_ID = 10865594502
SOURCE_ARTIFACT_ZIP_SHA256 = "d5dfeb8250949632d0982ad7272046e9dbca24f0ee650eb8a9c3ba7dc1c29fab"
SOURCE_SQLITE_SHA256 = "9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9"
SOURCE_SQLITE_BYTES = 144216064
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
EXPECTED_PRICE_ROWS = 711204
EXPECTED_STATES = 1425
EXPECTED_READY = 1415
EXPECTED_QUARANTINE = 10

EXACT10 = {
    "WS:XASX:ANZ": ("ANZ.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:BSL": ("BSL.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:BXB": ("BXB.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:CBA": ("CBA.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:NXT": ("NXT.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:PME": ("PME.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:QAN": ("QAN.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XASX:SDF": ("SDF.AX", "STRICT_OHLC_RELATION_FAIL"),
    "WS:XNAS:ECHO": ("ECHO", "SUSPICIOUS_RETURN_NEEDS_REPAIR"),
    "WS:XNAS:MRNA": ("MRNA", "SUSPICIOUS_RETURN_NEEDS_REPAIR"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_file_binding(path: Path) -> dict:
    h1 = sha256_file(path)
    n1 = path.stat().st_size
    h2 = sha256_file(path)
    n2 = path.stat().st_size
    if h1 != h2 or n1 != n2:
        raise RuntimeError("runtime sqlite is not byte-stable")
    return {"sha256_pass_1": h1, "sha256_pass_2": h2, "bytes_pass_1": n1, "bytes_pass_2": n2}


def finalize_sqlite_for_binding(conn: sqlite3.Connection, path: Path) -> dict:
    conn.commit()
    mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
    checkpoint = None
    if mode == "wal":
        checkpoint = tuple(conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
    conn.commit()
    conn.close()
    # HARD ORDERING: hash only after checkpoint/commit/close.
    bound = stable_file_binding(path)
    bound["journal_mode_before_close"] = mode
    bound["wal_checkpoint_result"] = checkpoint
    return bound


def inspect_sqlite(path: Path) -> dict:
    uri = f"file:{path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        price_rows = int(conn.execute("SELECT COUNT(*) FROM price_rows").fetchone()[0])
        states = int(conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        status_counts = {str(k): int(v) for k, v in conn.execute(
            "SELECT status, COUNT(*) FROM cache_state GROUP BY status ORDER BY status"
        ).fetchall()}
        exact = {
            str(ws): {"provider": str(sym or ""), "status": str(status or ""), "reason": str(reason or "")}
            for ws, sym, status, reason in conn.execute(
                "SELECT ws_id, yahoo_symbol, status, reason_code FROM cache_state WHERE status='QUARANTINE' ORDER BY ws_id"
            ).fetchall()
        }
    finally:
        conn.close()
    return {
        "integrity_check": integrity,
        "price_rows": price_rows,
        "states": states,
        "status_counts": status_counts,
        "exact_quarantine": exact,
    }


def validate_logical_state(x: dict) -> None:
    if x["integrity_check"] != "ok":
        raise RuntimeError("sqlite integrity_check failed")
    if x["price_rows"] != EXPECTED_PRICE_ROWS:
        raise RuntimeError(f"price row mismatch: {x['price_rows']}")
    if x["states"] != EXPECTED_STATES:
        raise RuntimeError(f"state count mismatch: {x['states']}")
    if x["status_counts"] != {"QUARANTINE": EXPECTED_QUARANTINE, "READY": EXPECTED_READY}:
        raise RuntimeError(f"status mismatch: {x['status_counts']}")
    if set(x["exact_quarantine"]) != set(EXACT10):
        raise RuntimeError("exact quarantine identity mismatch")
    for ws, (sym, reason) in EXACT10.items():
        got = x["exact_quarantine"][ws]
        if got != {"provider": sym, "status": "QUARANTINE", "reason": reason}:
            raise RuntimeError(f"quarantine state mismatch for {ws}: {got}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-sqlite", required=True)
    ap.add_argument("--target-sqlite", required=True)
    ap.add_argument("--frozen", default="universe/SWING_U3K_FROZEN_v0.5.csv")
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_runtime_refreeze_v0_47")
    ap.add_argument("--repository-sha", required=True)
    args = ap.parse_args()

    src = Path(args.source_sqlite)
    dst = Path(args.target_sqlite)
    frozen = Path(args.frozen)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if sha256_file(frozen) != FROZEN_SHA256:
        raise RuntimeError("Frozen SHA-256 mismatch")
    if src.stat().st_size != SOURCE_SQLITE_BYTES:
        raise RuntimeError("source sqlite byte count mismatch")
    source_hash = sha256_file(src)
    if source_hash != SOURCE_SQLITE_SHA256:
        raise RuntimeError(f"source sqlite hash mismatch: {source_hash}")

    source_state = inspect_sqlite(src)
    validate_logical_state(source_state)

    # Re-freeze by exact byte copy of the already finalized authoritative artifact.
    shutil.copyfile(src, dst)
    if Path(str(dst) + "-wal").exists() or Path(str(dst) + "-shm").exists():
        raise RuntimeError("unexpected sidecar after exact copy")

    # Read-only logical validation closes its handle before byte binding.
    target_state = inspect_sqlite(dst)
    validate_logical_state(target_state)
    binding = stable_file_binding(dst)

    if binding["sha256_pass_1"] != SOURCE_SQLITE_SHA256:
        raise RuntimeError("refrozen sqlite bytes differ from source")
    if binding["bytes_pass_1"] != SOURCE_SQLITE_BYTES:
        raise RuntimeError("refrozen sqlite size differs from source")

    state_rows = []
    for ws in sorted(EXACT10):
        q = target_state["exact_quarantine"][ws]
        state_rows.append({
            "Source_WS_ID": ws,
            "Provider_Symbol": q["provider"],
            "Price_Cache_Status": q["status"],
            "Blocking_Reason": q["reason"],
        })
    with (out / "state_reconciliation_v0.47.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Source_WS_ID","Provider_Symbol","Price_Cache_Status","Blocking_Reason"])
        w.writeheader(); w.writerows(state_rows)

    runtime_integrity = {
        "source_run_id": SOURCE_RUN_ID,
        "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_zip_sha256": SOURCE_ARTIFACT_ZIP_SHA256,
        "source_sqlite_sha256": source_hash,
        "source_sqlite_bytes": src.stat().st_size,
        "refrozen_sqlite_sha256": binding["sha256_pass_1"],
        "refrozen_sqlite_bytes": binding["bytes_pass_1"],
        "hash_pass_1": binding["sha256_pass_1"],
        "hash_pass_2": binding["sha256_pass_2"],
        "integrity_check": target_state["integrity_check"],
        "price_rows": target_state["price_rows"],
        "states": target_state["states"],
        "status_counts": target_state["status_counts"],
        "exact_quarantine": target_state["exact_quarantine"],
        "frozen_sha256": FROZEN_SHA256,
        "market_provider_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "repository_sha": args.repository_sha,
    }
    (out / "runtime_integrity_v0.47.json").write_text(json.dumps(runtime_integrity, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    hash_binding = {
        "declared_runtime_sha256": binding["sha256_pass_1"],
        "declared_runtime_bytes": binding["bytes_pass_1"],
        "packaged_runtime_sha256": "PENDING_POST_UPLOAD_VERIFICATION",
        "packaged_runtime_bytes": "PENDING_POST_UPLOAD_VERIFICATION",
        "prepackage_hash_repeat_equal": binding["sha256_pass_1"] == binding["sha256_pass_2"],
        "source_and_refrozen_byte_identity": source_hash == binding["sha256_pass_1"],
    }
    (out / "hash_binding_preupload_v0.47.json").write_text(json.dumps(hash_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "stage": "P0_FROZEN_1425_V045_RUNTIME_CACHE_INTEGRITY_CORRECTION_REFREEZE",
        "version": "v0.47",
        "status": "PREUPLOAD_PASS",
        "runtime_cache_authority_valid": False,
        "pending_only": "post-upload packaged byte verification",
        "ready": EXPECTED_READY,
        "quarantine": EXPECTED_QUARANTINE,
        "p0_price_cache_ready": False,
        "p0_run": False,
        "market_provider_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "universe_mutation": False,
        "productive": False,
        "runtime_integrity": runtime_integrity,
    }
    (out / "summary_preupload_v0.47.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status":"PREUPLOAD_PASS","sha256":binding["sha256_pass_1"],"bytes":binding["bytes_pass_1"],"ready":1415,"quarantine":10}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
