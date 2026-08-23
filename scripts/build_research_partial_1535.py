#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

EXPECTED_MASTER_ROWS = 1535
EXPECTED_SEGMENTS = [
    "EU_STOXX600",
    "CA_TSX",
    "JP_N225",
    "HK_HSI",
    "CN_CSI300",
    "IN_NIFTY50",
    "TW_TW50",
]


def read_master(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name="Universe_Master")
    raise SystemExit(f"Unsupported master format: {suffix}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("--out", default="universe/research_partial_1535.csv")
    ap.add_argument("--manifest", default="universe/research_partial_1535_manifest.json")
    ap.add_argument("--require-master-rows", type=int, default=EXPECTED_MASTER_ROWS)
    args = ap.parse_args()

    master_path = Path(args.master)
    if not master_path.exists():
        raise SystemExit(f"Master missing: {master_path}")

    df = read_master(master_path)

    required = {"WS_ID", "Primary_Universe_Index", "Primary_Ticker", "Primary_MIC"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Master missing columns: {sorted(missing)}")

    if args.require_master_rows and len(df) != args.require_master_rows:
        raise SystemExit(
            f"Wrong master snapshot: expected {args.require_master_rows} rows, got {len(df)}. "
            "This research run is pinned to the current r6 1535-row snapshot."
        )

    if df["WS_ID"].astype(str).duplicated().any():
        dupes = (
            df.loc[df["WS_ID"].astype(str).duplicated(keep=False), "WS_ID"]
            .astype(str)
            .tolist()
        )
        raise SystemExit(f"Duplicate WS_ID in master: {sorted(set(dupes))[:20]}")

    segment_values = set(df["Primary_Universe_Index"].dropna().astype(str))
    missing_segments = [s for s in EXPECTED_SEGMENTS if s not in segment_values]
    unexpected_segments = sorted(segment_values - set(EXPECTED_SEGMENTS))
    if missing_segments:
        raise SystemExit(f"Master missing expected imported segments: {missing_segments}")
    if unexpected_segments:
        raise SystemExit(
            f"Master contains unexpected segments for this frozen research snapshot: "
            f"{unexpected_segments}"
        )

    # Deliberately copy the complete current 1535-row research snapshot.
    # No price, liquidity, news, setup, quality, ranking, P0 or trading filter is applied.
    out = df.copy()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    counts = (
        out["Primary_Universe_Index"]
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )

    manifest = {
        "schema": "WELT_SWING_LONG_RESEARCH_PARTIAL_1535_V0_1",
        "source_master": str(master_path),
        "source_master_rows": int(len(df)),
        "rows": int(len(out)),
        "selection": (
            "All 1535 rows from the frozen current r6 seven-segment master snapshot; "
            "no price/news/liquidity/setup/quality/ranking/P0 selection."
        ),
        "scope": "RESEARCH_PARTIAL",
        "universe_complete": False,
        "scope_note": (
            "Current source coverage is seven imported primary-index segments; "
            "this is not the final U3K and 3000 is a cap/target, not a denominator."
        ),
        "segments": EXPECTED_SEGMENTS,
        "counts": {str(k): int(v) for k, v in counts.items()},
        "research_csv_sha256": sha256_file(out_path),
        "productive": False,
        "p0_run": False,
        "alpha_vantage_allowed": False,
    }

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
