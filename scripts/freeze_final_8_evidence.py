#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = "WELT_SWING_FINAL_8_EVIDENCE_FREEZE_V0_1"
EXPECTED_MASTER_ROWS = 3664
EXPECTED_ACTIVE_ROWS = 3663
EXPECTED_INPUT_REVIEW = 8

PRODUCTIVE_TRADING_AUTHORITY = False
P0_RUN = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_HISTORY_ALLOWED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def run(args) -> dict:
    master_path = Path(args.master)
    review_path = Path(args.review)
    evidence_path = Path(args.evidence)
    out_dir = Path(args.out_dir)
    out_csv = Path(args.out_csv)
    out_xlsx = Path(args.out_xlsx)

    master = pd.read_csv(master_path, keep_default_na=False, dtype=str)
    review = pd.read_csv(review_path, keep_default_na=False, dtype=str)
    evidence = pd.read_csv(evidence_path, keep_default_na=False, dtype=str)

    if len(master) != EXPECTED_MASTER_ROWS:
        raise SystemExit(f"Expected {EXPECTED_MASTER_ROWS} master rows, got {len(master)}")
    if len(review) != EXPECTED_INPUT_REVIEW:
        raise SystemExit(f"Expected {EXPECTED_INPUT_REVIEW} review rows, got {len(review)}")
    if len(evidence) != EXPECTED_INPUT_REVIEW:
        raise SystemExit(f"Expected {EXPECTED_INPUT_REVIEW} evidence rows, got {len(evidence)}")
    if master["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in master")
    if evidence["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in evidence freeze")

    review_ids = set(review["WS_ID"])
    evidence_ids = set(evidence["WS_ID"])
    if review_ids != evidence_ids:
        raise SystemExit(
            "Evidence set does not exactly match v0.3 review queue. "
            f"missing={sorted(review_ids-evidence_ids)} extra={sorted(evidence_ids-review_ids)}"
        )

    by_id = evidence.set_index("WS_ID").to_dict("index")
    rows = []
    freeze_audit = []

    for _, src in master.iterrows():
        row = src.copy()
        ws = txt(row.get("WS_ID"))

        if ws in by_id:
            ev = by_id[ws]
            old_symbol = txt(row.get("Yahoo_Symbol"))
            old_status = txt(row.get("Mapping_Status"))

            row["Yahoo_Symbol"] = txt(ev["Frozen_Yahoo_Symbol"])
            row["Mapping_Status"] = "EVIDENCE_FROZEN_OVERRIDE"
            row["Provider_Listing_Type"] = "PRIMARY"
            row["Evidence_Freeze_Status"] = txt(ev["Evidence_Status"])
            row["Evidence_Primary_URL"] = txt(ev["Evidence_Primary_URL"])
            row["Evidence_Provider_URL"] = txt(ev["Evidence_Provider_URL"])
            row["Evidence_Note"] = txt(ev["Evidence_Note"])
            row["Evidence_Frozen_UTC"] = now_utc()

            freeze_audit.append({
                "WS_ID": ws,
                "Name": txt(row.get("Name")),
                "Primary_Universe_Index": txt(row.get("Primary_Universe_Index")),
                "Primary_MIC": txt(row.get("Primary_MIC")),
                "Source_Ticker": txt(ev["Source_Ticker"]),
                "Old_v0.3_Candidate": txt(ev["Old_Candidate"]),
                "Yahoo_Symbol_Before": old_symbol,
                "Yahoo_Status_Before": old_status,
                "Frozen_Yahoo_Symbol": txt(ev["Frozen_Yahoo_Symbol"]),
                "Market_Ticker": txt(ev["Market_Ticker"]),
                "Evidence_Status": txt(ev["Evidence_Status"]),
                "Evidence_Primary_URL": txt(ev["Evidence_Primary_URL"]),
                "Evidence_Provider_URL": txt(ev["Evidence_Provider_URL"]),
                "Evidence_Note": txt(ev["Evidence_Note"]),
            })

        rows.append(row)

    frozen = pd.DataFrame(rows)
    audit = pd.DataFrame(freeze_audit)

    if len(frozen) != EXPECTED_MASTER_ROWS:
        raise SystemExit("Frozen master row-count invariant failed")
    if frozen["WS_ID"].duplicated().any():
        raise SystemExit("Frozen master WS_ID uniqueness invariant failed")
    if len(audit) != EXPECTED_INPUT_REVIEW:
        raise SystemExit("Did not freeze exactly 8 rows")

    active = frozen["Active"].astype(str).str.lower().eq("true")
    active_rows = int(active.sum())
    active_mapped = int(
        (active & frozen["Yahoo_Symbol"].astype(str).str.len().gt(0)).sum()
    )
    active_unresolved = active_rows - active_mapped

    if active_rows != EXPECTED_ACTIVE_ROWS:
        raise SystemExit(f"Expected {EXPECTED_ACTIVE_ROWS} active rows, got {active_rows}")
    if active_unresolved != 0:
        unresolved = frozen.loc[
            active & frozen["Yahoo_Symbol"].astype(str).str.len().eq(0),
            ["WS_ID", "Name"]
        ].to_dict("records")
        raise SystemExit(f"Active unresolved remain after evidence freeze: {unresolved}")

    status_counts = (
        audit["Evidence_Status"].value_counts(dropna=False).sort_index().to_dict()
    )

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "EVIDENCE_FREEZE_COMPLETE",
        "master_rows": EXPECTED_MASTER_ROWS,
        "active_rows": active_rows,
        "active_provider_mapped": active_mapped,
        "active_provider_unresolved": active_unresolved,
        "active_provider_mapping_pct": round(100.0 * active_mapped / active_rows, 4),
        "evidence_rows_frozen": len(audit),
        "evidence_status_counts": status_counts,
        "corrected_candidate_rows": int(
            audit["Evidence_Status"].astype(str).str.startswith("CORRECT").sum()
            + audit["Evidence_Status"].astype(str).str.startswith("CORPORATE_ACTION").sum()
        ),
        "price_run_candidate_coverage_ready": active_unresolved == 0,
        "price_run_allowed_after_this_step": False,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "p0_run": P0_RUN,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "No price/history/OHLCV call is performed.",
            "Exactly the eight v0.3 review rows are frozen.",
            "Epiroc candidate corrected from EPIR-A.ST to EPI-A.ST.",
            "Roche candidate corrected from obsolete ROG.SW to current ROP.SW after the March 2026 corporate action.",
            "ALFA ALFAA.MX is an explicit public-evidence provider override because Yahoo Search omitted the exact result.",
            "No canonical WS_ID is changed.",
            "P0 and productive trading remain disabled.",
            "A full price run remains a separate explicit release step."
        ],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    frozen.to_csv(out_csv, index=False)
    audit.to_csv(out_dir / "final_8_evidence_audit_v0.1.csv", index=False)
    (out_dir / "summary_v0.1.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        frozen.to_excel(xw, sheet_name="Universe_Master", index=False)
        audit.to_excel(xw, sheet_name="Evidence_Freeze_8", index=False)
        pd.DataFrame([
            {
                "Key": k,
                "Value": json.dumps(v, ensure_ascii=False)
                if isinstance(v, (dict, list))
                else v,
            }
            for k, v in summary.items()
        ]).to_excel(xw, sheet_name="Run_Summary", index=False)

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def self_test(evidence_path: Path) -> None:
    ev = pd.read_csv(evidence_path, keep_default_na=False, dtype=str)
    assert len(ev) == 8
    by = ev.set_index("WS_ID")["Frozen_Yahoo_Symbol"].to_dict()
    assert by["WS:XETR:AG1G.DE"] == "AG1.DE"
    assert by["WS:XMAD:AMA.MC"] == "AMS.MC"
    assert by["WS:XSTO:EPIRA.ST"] == "EPI-A.ST"
    assert by["WS:XSTO:ERICB.ST"] == "ERIC-B.ST"
    assert by["WS:XSTO:HEXAB.ST"] == "HEXA-B.ST"
    assert by["WS:XSWX:ROPC.S"] == "ROP.SW"
    assert by["WS:XSWX:SRENH.S"] == "SREN.SW"
    assert by["WS:XMEX:ALFAA"] == "ALFAA.MX"
    print("FINAL_8_EVIDENCE_FREEZE_SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="universe/Welt-Swing-Universe-Master-FinalMapped-v0.6.csv")
    ap.add_argument("--review", default="output_identity_final/review_queue_v0.3.csv")
    ap.add_argument("--evidence", default="config/final_8_evidence_freeze_v0.1.csv")
    ap.add_argument("--out-dir", default="output_identity_evidence_freeze")
    ap.add_argument("--out-csv", default="universe/Welt-Swing-Universe-Master-EvidenceFrozen-v0.7.csv")
    ap.add_argument("--out-xlsx", default="universe/Welt-Swing-Universe-Master-EvidenceFrozen-v0.7.xlsx")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test(Path(args.evidence))
        return 0

    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
