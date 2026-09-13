#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path

EXPECTED_ROWS = 2527
EXPECTED_MISSING_ISIN = 1536
OUTPUT_FIELDS = [
    "Security_Key",
    "Source_WS_ID",
    "Company_Key",
    "ISIN",
    "Primary_MIC",
    "Primary_Ticker",
    "Share_Class",
    "Identity_Status",
    "Identity_Confidence",
]


def security_key(source_ws_id: str) -> str:
    source_ws_id = source_ws_id.strip()
    if not source_ws_id:
        raise ValueError("WS_ID is required")
    return f"WSSEC:{source_ws_id}"


def read_source(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"WS_ID", "ISIN", "Primary_MIC", "Primary_Ticker", "Share_Class"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"source missing required columns: {missing}")
        rows = list(reader)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"source row count {len(rows)} != {EXPECTED_ROWS}")
    return rows


def build_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    ws_ids = [row.get("WS_ID", "").strip() for row in source_rows]
    if any(not ws_id for ws_id in ws_ids):
        raise ValueError("source contains missing WS_ID")
    if len(set(ws_ids)) != EXPECTED_ROWS:
        raise ValueError("source WS_ID values are not unique")

    rows: list[dict[str, str]] = []
    for source, ws_id in zip(source_rows, ws_ids):
        isin = source.get("ISIN", "").strip()
        rows.append(
            {
                "Security_Key": security_key(ws_id),
                "Source_WS_ID": ws_id,
                "Company_Key": "",
                "ISIN": isin,
                "Primary_MIC": source.get("Primary_MIC", ""),
                "Primary_Ticker": source.get("Primary_Ticker", ""),
                "Share_Class": source.get("Share_Class", ""),
                "Identity_Status": "SECURITY_UNRESOLVED" if not isin else "COMPANY_UNRESOLVED",
                "Identity_Confidence": "UNRESOLVED",
            }
        )

    keys = [row["Security_Key"] for row in rows]
    if len(keys) != EXPECTED_ROWS or len(set(keys)) != EXPECTED_ROWS:
        raise ValueError("Security_Key collision or missing key")
    missing = [row for row in rows if not row["ISIN"]]
    if len(missing) != EXPECTED_MISSING_ISIN:
        raise ValueError(f"missing-ISIN count {len(missing)} != {EXPECTED_MISSING_ISIN}")
    if any(row["Identity_Status"] != "SECURITY_UNRESOLVED" for row in missing):
        raise ValueError("missing-ISIN rows are not fail-closed")
    if any(row["Company_Key"] for row in rows):
        raise ValueError("Company_Key inference is forbidden in v1")
    return rows


def serialize_rows(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=OUTPUT_FIELDS,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def generate_bytes(source_path: Path) -> bytes:
    return serialize_rows(build_rows(read_source(source_path)))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("universe/research_partial_1633.csv"))
    parser.add_argument("--output", type=Path, default=Path("universe/research_partial_2527_security_mapping_v1.csv"))
    args = parser.parse_args()

    data = generate_bytes(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"rows={EXPECTED_ROWS}")
    print(f"bytes={len(data)}")
    print(f"sha256={sha256_hex(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
