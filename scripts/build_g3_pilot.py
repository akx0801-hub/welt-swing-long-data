#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import pandas as pd

SEGMENTS = [
    "EU_STOXX600",
    "CA_TSX",
    "JP_N225",
    "HK_HSI",
    "CN_CSI300",
    "IN_NIFTY50",
    "TW_TW50",
]
EXPECTED_MASTER_ROWS = 1535

def read_master(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        # Current r6 workbook uses the Universe_Master sheet.
        return pd.read_excel(path, sheet_name="Universe_Master")
    raise SystemExit(f"Unsupported master format: {suffix}")

def deterministic_pick(df: pd.DataFrame, n: int, segment: str) -> pd.DataFrame:
    x = df[df["Primary_Universe_Index"].astype(str).eq(segment)].copy()
    if "Active" in x.columns:
        x = x[x["Active"].fillna(False).astype(bool)]
    if "Universe_Status" in x.columns:
        x = x[x["Universe_Status"].astype(str).eq("ACTIVE_VERIFIED")]
    if len(x) < n:
        raise SystemExit(f"{segment}: only {len(x)} eligible rows, need {n}")
    x["_sample_key"] = x["WS_ID"].astype(str).map(
        lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
    )
    x = x.sort_values(["_sample_key", "WS_ID"], kind="mergesort").head(n)
    x = x.drop(columns=["_sample_key"])
    x["G3_Segment"] = segment
    return x

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("--out", default="universe/g3_pilot_210.csv")
    ap.add_argument("--manifest", default="universe/g3_pilot_210_manifest.json")
    ap.add_argument("--per-segment", type=int, default=30)
    ap.add_argument("--require-master-rows", type=int, default=EXPECTED_MASTER_ROWS)
    args = ap.parse_args()

    p = Path(args.master)
    if not p.exists():
        raise SystemExit(f"Master missing: {p}")

    df = read_master(p)
    req = {"WS_ID", "Primary_Universe_Index", "Primary_Ticker", "Primary_MIC"}
    miss = req - set(df.columns)
    if miss:
        raise SystemExit(f"Master missing columns: {sorted(miss)}")

    if args.require_master_rows and len(df) != args.require_master_rows:
        raise SystemExit(
            f"Wrong master snapshot: expected {args.require_master_rows} rows, got {len(df)}. "
            "Do not use the older 668-row master."
        )

    actual_segments = set(df["Primary_Universe_Index"].dropna().astype(str))
    missing_segments = [s for s in SEGMENTS if s not in actual_segments]
    if missing_segments:
        raise SystemExit(f"Master missing expected imported segments: {missing_segments}")

    picks = [deterministic_pick(df, args.per_segment, s) for s in SEGMENTS]
    out = pd.concat(picks, ignore_index=True)

    if len(out) != args.per_segment * len(SEGMENTS):
        raise SystemExit("Pilot row count mismatch")
    if out["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in pilot")

    op = Path(args.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(op, index=False)

    sha = hashlib.sha256(op.read_bytes()).hexdigest()
    counts = out["Primary_Universe_Index"].value_counts().sort_index().to_dict()
    manifest = {
        "schema": "WELT_SWING_LONG_G3_PILOT_V0_2",
        "source_master": str(p),
        "source_master_rows": int(len(df)),
        "selection": (
            "30 per imported segment; SHA256(WS_ID) ascending; deterministic; "
            "no price/news/quality selection"
        ),
        "segments": SEGMENTS,
        "per_segment": args.per_segment,
        "rows": int(len(out)),
        "counts": {str(k): int(v) for k, v in counts.items()},
        "pilot_sha256": sha,
        "productive": False,
        "p0_run": False,
    }
    mp = Path(args.manifest)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
