#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

SCHEMA = "WELT_SWING_FULL_PRICE_UNIVERSE_3663_V0_1"
EXPECTED_SOURCE_ROWS = 3664
EXPECTED_ACTIVE_ROWS = 3663
EXPECTED_INACTIVE_ROWS = 1
EXPECTED_INACTIVE_WS_ID = "WS:SRC:ZA_TOP40:8096AB44770BB485"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "master",
        nargs="?",
        default="universe/Welt-Swing-Universe-Master-EvidenceFrozen-v0.7.csv",
    )
    ap.add_argument(
        "--out",
        default="universe/full_price_universe_3663.csv",
    )
    ap.add_argument(
        "--manifest",
        default="universe/full_price_universe_3663_manifest.json",
    )
    args = ap.parse_args()

    master_path = Path(args.master)
    if not master_path.exists():
        raise SystemExit(f"Evidence-frozen master missing: {master_path}")

    df = pd.read_csv(master_path, keep_default_na=False, dtype=str)

    required = {
        "WS_ID",
        "Name",
        "Primary_Universe_Index",
        "Primary_Ticker",
        "Primary_MIC",
        "Active",
        "Yahoo_Symbol",
        "Mapping_Status",
    }
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Master missing required columns: {sorted(missing)}")

    if len(df) != EXPECTED_SOURCE_ROWS:
        raise SystemExit(
            f"Wrong source master: expected {EXPECTED_SOURCE_ROWS}, got {len(df)}"
        )

    if df["WS_ID"].duplicated().any():
        dup = (
            df.loc[df["WS_ID"].duplicated(keep=False), "WS_ID"]
            .astype(str)
            .drop_duplicates()
            .tolist()
        )
        raise SystemExit(f"Duplicate WS_ID in source master: {dup[:20]}")

    active_raw = df["Active"].astype(str).str.strip().str.lower()
    allowed = {"true", "false"}
    if not active_raw.isin(allowed).all():
        bad = sorted(set(active_raw[~active_raw.isin(allowed)]))
        raise SystemExit(f"Unexpected Active values: {bad}")

    active = df.loc[active_raw.eq("true")].copy()
    inactive = df.loc[active_raw.eq("false")].copy()

    if len(active) != EXPECTED_ACTIVE_ROWS:
        raise SystemExit(
            f"Expected {EXPECTED_ACTIVE_ROWS} active rows, got {len(active)}"
        )
    if len(inactive) != EXPECTED_INACTIVE_ROWS:
        raise SystemExit(
            f"Expected {EXPECTED_INACTIVE_ROWS} inactive row, got {len(inactive)}"
        )
    inactive_ids = set(inactive["WS_ID"].astype(str))
    if inactive_ids != {EXPECTED_INACTIVE_WS_ID}:
        raise SystemExit(
            f"Unexpected inactive source rows: {sorted(inactive_ids)}"
        )

    blank_symbol = active["Yahoo_Symbol"].astype(str).str.strip().eq("")
    if blank_symbol.any():
        bad = active.loc[blank_symbol, ["WS_ID", "Name"]].to_dict("records")
        raise SystemExit(f"Active rows without Yahoo_Symbol: {bad[:20]}")

    # The price runtime keys the cache by canonical WS_ID. Provider-symbol
    # duplicates are allowed only as diagnostics; they do not alter identity.
    provider_dups = active.loc[
        active["Yahoo_Symbol"].astype(str).duplicated(keep=False),
        ["WS_ID", "Name", "Primary_Universe_Index", "Primary_MIC", "Yahoo_Symbol"],
    ].sort_values(["Yahoo_Symbol", "WS_ID"])

    out_path = Path(args.out)
    manifest_path = Path(args.manifest)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # No price/liquidity/setup/ranking filter: all active evidence-frozen rows.
    active.to_csv(out_path, index=False)

    segment_counts = (
        active["Primary_Universe_Index"]
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    mapping_status_counts = (
        active["Mapping_Status"]
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )

    manifest = {
        "schema": SCHEMA,
        "source_master": str(master_path),
        "source_master_sha256": sha256_file(master_path),
        "source_rows": int(len(df)),
        "active_rows": int(len(active)),
        "inactive_rows": int(len(inactive)),
        "inactive_ws_ids": sorted(inactive_ids),
        "rows": int(len(active)),
        "selection": (
            "All Active=True rows from the evidence-frozen v0.7 master. "
            "No price, liquidity, setup, quality, ranking, news, P0 or trading filter."
        ),
        "scope": "FULL_SOURCE_SUPERSET_PRICE_DATA_RUN",
        "segments": sorted(segment_counts),
        "segment_counts": {str(k): int(v) for k, v in segment_counts.items()},
        "yahoo_symbol_nonblank": int(
            active["Yahoo_Symbol"].astype(str).str.strip().ne("").sum()
        ),
        "provider_symbol_duplicate_rows": int(len(provider_dups)),
        "provider_symbol_duplicate_symbols": sorted(
            provider_dups["Yahoo_Symbol"].astype(str).unique().tolist()
        ) if not provider_dups.empty else [],
        "mapping_status_counts": {
            str(k): int(v) for k, v in mapping_status_counts.items()
        },
        "output_csv_sha256": sha256_file(out_path),
        "productive_trading_authority": False,
        "p0_run": False,
        "alpha_vantage_allowed": False,
        "notes": [
            "This is a data-collection release, not a trading-authority release.",
            "Canonical identity remains WS_ID/MIC/source identity; Yahoo_Symbol is provider mapping only.",
            "MultiChoice stale/delisted source row remains inactive and is excluded from the 3663 active denominator.",
            "P0 parameters remain unpromoted and P0 is not executed.",
        ],
    }

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps({
        "rows": manifest["rows"],
        "segments": len(manifest["segments"]),
        "mapped": manifest["yahoo_symbol_nonblank"],
        "provider_duplicate_rows": manifest["provider_symbol_duplicate_rows"],
        "p0_run": manifest["p0_run"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
