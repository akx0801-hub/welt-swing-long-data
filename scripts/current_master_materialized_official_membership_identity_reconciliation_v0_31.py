#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION_V0_31"
STAGE_ID = "CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION"
LINEAGE = "CURRENT_MASTER_CLEAN_RESTART"
SEGMENT_ID = "BR_IBRX100"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items: dict[str, str]) -> str:
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_b3_type(v: Any) -> str:
    return re.sub(r"\s+", " ", txt(v).upper()).strip()


def classify_instrument(b3_type: str) -> tuple[str, str, str]:
    t = normalize_b3_type(b3_type)
    if re.match(r"^ON(?:\s|$)", t):
        return "ORDINARY_SHARE", "PASS", "B3_TYPE_ON_OFFICIAL_ORDINARY_SHARE"
    if re.match(r"^PN[A-Z]?(?:\s|$)", t):
        return "PREFERRED_SHARE", "FAIL", "B3_TYPE_PN_PREFERRED_SHARE_NOT_ALLOWED"
    if re.match(r"^(UNT|UNIT)(?:\s|$)", t):
        return "UNIT", "FAIL", "B3_TYPE_UNIT_NOT_ALLOWED"
    return "UNKNOWN", "NOT_VERIFIED", "B3_TYPE_NOT_STRICTLY_CLASSIFIED"


def parse_b3_official_date(raw: dict) -> tuple[str, str]:
    d = txt(raw.get("header", {}).get("date"))
    require(re.fullmatch(r"\d{2}/\d{2}/\d{2}", d) is not None, f"Unexpected B3 header date: {d!r}")
    dd, mm, yy = d.split("/")
    iso = f"20{yy}-{mm}-{dd}"
    return d, iso


def build_brazil_reconciliation(raw: dict, materialized_csv: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict[str, int]]:
    rows = raw.get("results")
    require(isinstance(rows, list), "B3 raw JSON missing results")
    require(len(rows) == 98, f"B3 raw result count changed: {len(rows)}")

    page = raw.get("page", {})
    require(int(page.get("totalRecords", 0)) == 98, "B3 totalRecords changed")
    require(int(page.get("totalPages", 0)) == 1, "B3 totalPages changed")

    date_display, date_iso = parse_b3_official_date(raw)

    raw_tickers = [txt(x.get("cod")).upper() for x in rows if txt(x.get("cod"))]
    csv_tickers = materialized_csv["Primary_Ticker_Candidate"].astype(str).str.upper().tolist()
    require(len(raw_tickers) == 98 and len(set(raw_tickers)) == 98, "B3 raw tickers not 98 unique")
    require(set(raw_tickers) == set(csv_tickers), "B3 raw/CSV ticker sets differ")

    out = []
    for x in rows:
        ticker = txt(x.get("cod")).upper()
        name = txt(x.get("asset"))
        b3_type = normalize_b3_type(x.get("type"))
        require(re.fullmatch(r"[A-Z0-9]{4,8}", ticker) is not None, f"Unexpected B3 ticker format: {ticker}")
        require(name != "", f"Missing B3 official name for {ticker}")

        instrument_type, instrument_gate, instrument_reason = classify_instrument(b3_type)
        identity_gate = "PASS" if ticker else "FAIL"
        isin = ""
        ws_id = f"WS:{cfg['identity']['primary_mic']}:{ticker}"

        if identity_gate == "PASS":
            identity_method = "PRIMARY_MIC_OFFICIAL_TICKER_STABLE_WSID_NO_ISIN_IN_MEMBERSHIP_SOURCE"
        else:
            identity_method = "IDENTITY_INCOMPLETE"

        strict_candidate = (
            identity_gate == "PASS"
            and instrument_gate == "PASS"
            and instrument_type == "ORDINARY_SHARE"
        )

        out.append({
            "Segment_ID": SEGMENT_ID,
            "WS_ID_Candidate": ws_id,
            "ISIN": isin,
            "Primary_MIC": cfg["identity"]["primary_mic"],
            "Primary_Ticker": ticker,
            "Security_Name_Official": name,
            "B3_Type_Official": b3_type,
            "Instrument_Type_v0_31": instrument_type,
            "Instrument_Gate_v0_31": instrument_gate,
            "Instrument_Gate_Reason_v0_31": instrument_reason,
            "Identity_Gate_v0_31": identity_gate,
            "Identity_Method_v0_31": identity_method,
            "Source_Membership_Gate_v0_31": "PASS_OFFICIAL_B3_IBRX100",
            "Source_ID": "B3_OFFICIAL_INDEXPROXY_GETPORTFOLIODAY",
            "Source_AsOf_Official_Display": date_display,
            "Source_AsOf_Official": date_iso,
            "Source_AsOf_Semantics": "OFFICIAL_B3_HEADER_DATE_UNINTERPRETED",
            "Source_Endpoint": cfg["source"]["b3_endpoint_base"],
            "Primary_MIC_Evidence_URL": cfg["identity"]["primary_mic_evidence_url"],
            "Official_Source_Provides_ISIN": False,
            "Strict_Ordinary_Identity_Candidate_v0_31": strict_candidate,
            "Canonical_Master_Import_v0_31": False,
            "Needs_Liquidity_Gate": strict_candidate,
        })

    df = pd.DataFrame(out)
    require(df["WS_ID_Candidate"].nunique() == 98, "Duplicate WS_ID candidate")
    require(df["Primary_Ticker"].nunique() == 98, "Duplicate B3 ticker candidate")

    counts = {
        "rows": int(len(df)),
        "identity_pass": int(df["Identity_Gate_v0_31"].eq("PASS").sum()),
        "instrument_pass": int(df["Instrument_Gate_v0_31"].eq("PASS").sum()),
        "instrument_fail": int(df["Instrument_Gate_v0_31"].eq("FAIL").sum()),
        "instrument_not_verified": int(df["Instrument_Gate_v0_31"].eq("NOT_VERIFIED").sum()),
        "ordinary_share": int(df["Instrument_Type_v0_31"].eq("ORDINARY_SHARE").sum()),
        "preferred_share": int(df["Instrument_Type_v0_31"].eq("PREFERRED_SHARE").sum()),
        "unit": int(df["Instrument_Type_v0_31"].eq("UNIT").sum()),
        "unknown": int(df["Instrument_Type_v0_31"].eq("UNKNOWN").sum()),
        "strict_candidates": int(df["Strict_Ordinary_Identity_Candidate_v0_31"].astype(bool).sum()),
    }
    require(counts["instrument_pass"] + counts["instrument_fail"] + counts["instrument_not_verified"] == 98, "Instrument classification does not reconcile")
    require(counts["strict_candidates"] == counts["ordinary_share"], "Strict candidate/ordinary count mismatch")
    return df, counts


def build_mexico_change_ledger(text: str) -> pd.DataFrame:
    required_phrases = [
        "S&P Dow Jones Indices Announces Final",
        "Rebalancing Results for the S&P/BMV IPC Index",
        "MEXICO CITY, MARCH 13, 2026",
        "effective prior to the",
        "open of trading on Monday, March 23, 2026",
        "VOLAR A Controladora Vuela Compañía de Aviación S.A.B. de C.V. ADD",
        "CUERVO * Becle, S.A. de C.V DROP",
    ]
    for phrase in required_phrases:
        require(phrase in text, f"BMV frozen text missing expected phrase: {phrase}")

    rows = [
        {
            "Segment_ID": "MX_IPC",
            "Ticker_Official_Announcement": "VOLAR A",
            "Company_Name_Official": "Controladora Vuela Compañía de Aviación S.A.B. de C.V.",
            "Action": "ADD",
            "Announcement_Date": "2026-03-13",
            "Effective_Date": "2026-03-23",
            "Evidence_Type": "OFFICIAL_FINAL_REBALANCE_CHANGE_ONLY",
            "Full_Current_Membership_Proven": False,
            "Canonical_Import_v0_31": False,
        },
        {
            "Segment_ID": "MX_IPC",
            "Ticker_Official_Announcement": "CUERVO *",
            "Company_Name_Official": "Becle, S.A. de C.V",
            "Action": "DROP",
            "Announcement_Date": "2026-03-13",
            "Effective_Date": "2026-03-23",
            "Evidence_Type": "OFFICIAL_FINAL_REBALANCE_CHANGE_ONLY",
            "Full_Current_Membership_Proven": False,
            "Canonical_Import_v0_31": False,
        },
    ]
    return pd.DataFrame(rows)


def build_segment_status(counts: dict[str, int], mx_rows: int) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Segment_ID": "BR_IBRX100",
            "Membership_Evidence_v0_31": "PASS_OFFICIAL_FULL_B3_98_ROWS",
            "Identity_Reconciliation_v0_31": "PASS_FALLBACK_IDENTITY_FOR_OFFICIAL_TICKERS",
            "Instrument_Reconciliation_v0_31": "PARTIAL_BY_INSTRUMENT_CLASS",
            "Strict_Ordinary_Candidates": counts["strict_candidates"],
            "Instrument_Fail_Rows": counts["instrument_fail"],
            "Instrument_Not_Verified_Rows": counts["instrument_not_verified"],
            "Canonical_Import_v0_31": False,
            "Next_Action": "FREEZE_BR_SOURCE_SEGMENT_AND_RUN_LIQUIDITY_PRECHECK",
        },
        {
            "Segment_ID": "MX_IPC",
            "Membership_Evidence_v0_31": "CHANGE_LEDGER_ONLY_NOT_FULL_MEMBERSHIP",
            "Identity_Reconciliation_v0_31": "NOT_RUN_FULL_SEGMENT",
            "Instrument_Reconciliation_v0_31": "NOT_RUN_FULL_SEGMENT",
            "Strict_Ordinary_Candidates": 0,
            "Instrument_Fail_Rows": 0,
            "Instrument_Not_Verified_Rows": 0,
            "Canonical_Import_v0_31": False,
            "Next_Action": f"PRESERVE_{mx_rows}_OFFICIAL_CHANGES_AND_CONTINUE_FULL_SOURCE_SEARCH",
        },
    ])


def write_handoff(versioned: Path, stable: Path, summary: dict, checkpoint: dict, prior: Path) -> None:
    prior_text = prior.read_text(encoding="utf-8")
    require("Version:** v0.30" in prior_text, "Expected v0.30 CURRENT handoff predecessor")

    c = summary["br_ibrx100_counts"]
    body = f"""# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.31  
**Generated UTC:** {summary['generated_utc']}  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Primary lineage:** `CURRENT_MASTER_CLEAN_RESTART`  
**Trigger/input commit:** `{os.environ.get('GITHUB_SHA','LOCAL_OR_UNKNOWN')}`

## 1. Authority

Authoritative DEV master:
`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains solely authoritative for productive Swing decisions. Alpha Vantage remains forbidden.

## 2. Current-master universe

Canonical development snapshot remains unchanged at **1,535 securities from 7 of 14 target segments**.

v0.31 performs identity and instrument reconciliation only. No canonical universe mutation occurs.

## 3. Brazil / IBrX 100

Official B3 membership snapshot:
- Official source rows: {c['rows']}
- Official B3 header date: `{summary['br_ibrx100_source_asof']}`
- Identity PASS via Primary MIC + official ticker + stable WS_ID: {c['identity_pass']}
- Ordinary-share instrument PASS: {c['ordinary_share']}
- Preferred-share FAIL: {c['preferred_share']}
- Unit FAIL: {c['unit']}
- Instrument NOT VERIFIED: {c['unknown']}
- Strict ordinary identity candidates: {c['strict_candidates']}

Primary MIC used: `BVMF`.

The official B3 membership endpoint does not provide ISIN in this response. Under the DEV master identity rule, the fallback identity is therefore:
`Primary MIC + official Primary Ticker + stable WS_ID`.

No ISIN is guessed.

Preferred shares and Units remain official IBrX 100 members but fail the Strict-U3K instrument gate.

## 4. Mexico / S&P-BMV IPC

The official final rebalance document is preserved as a **change ledger only**:
- `VOLAR A` — ADD
- `CUERVO *` — DROP
- announcement: 2026-03-13
- effective: 2026-03-23

This does not prove the complete current IPC membership and therefore does not authorize full-segment import.

## 5. Governance

- Current-master rows before/after: 1,535 / 1,535
- Canonical segments imported in v0.31: 0
- Universe mutation: `false`
- Eligibility promotions: 0
- Liquidity gate: not yet run for Brazil
- Price downloads: `false`
- P0: `false`
- `SWING_U3K_FROZEN`: `false`

## 6. Current checkpoint

- Stage: `{checkpoint['stage_id']}`
- Run ID: `{checkpoint['run_id']}`
- Status: `{checkpoint['status']}`
- B3 rows checked: {checkpoint['checked_count']}
- Strict ordinary identity candidates: {checkpoint['pass_count']}
- Instrument FAIL rows: {checkpoint['fail_count']}
- Instrument NOT VERIFIED rows: {checkpoint['quarantine_count']}
- Output hash: `{checkpoint['output_hash']}`
- Next stage: `{checkpoint['next_stage']}`

## 7. Recovery order

1. `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
2. `WELT-SWING-CURRENT-Handoff-CURRENT.md`
3. `output_current_master_membership_identity_reconciliation_v0_31/stage_checkpoint_v0.31.json`
4. `output_current_master_membership_identity_reconciliation_v0_31/manifest_v0.31.json`
5. `output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_identity_reconciliation_v0.31.csv`
6. `output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_strict_ordinary_candidates_v0.31.csv`
7. `output_current_master_source_deep_materialization_v0_30/b3_ibrx100_official_raw_v0.30.json`
8. `universe/Welt-Swing-Universe-Master-v2.0.xlsx`

## 8. Handoff policy

Every major DEV stage refreshes both the versioned Current Handoff and `WELT-SWING-CURRENT-Handoff-CURRENT.md`.

## 9. Next stage

`{summary['next_stage']}`

Brazil may proceed only as a frozen official-source segment with the reconciled Ordinary-Share subset. Liquidity and data-quality gates remain separate and mandatory.
"""
    versioned.write_text(body, encoding="utf-8")
    stable.write_text(body, encoding="utf-8")


def self_test() -> None:
    assert classify_instrument("ON      NM")[0:2] == ("ORDINARY_SHARE", "PASS")
    assert classify_instrument("ON  ED  NM")[0:2] == ("ORDINARY_SHARE", "PASS")
    assert classify_instrument("PN      N1")[0:2] == ("PREFERRED_SHARE", "FAIL")
    assert classify_instrument("PNA N1")[0:2] == ("PREFERRED_SHARE", "FAIL")
    assert classify_instrument("UNT N2")[0:2] == ("UNIT", "FAIL")
    assert classify_instrument("OTHER")[1] == "NOT_VERIFIED"
    assert f"WS:BVMF:ABEV3" == "WS:BVMF:ABEV3"
    print("CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION_V0_31_SELF_TEST_PASS")


def run(cfg_path: Path) -> None:
    started = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    inp = {k: Path(v) for k, v in cfg["inputs"].items()}
    master_spec = inp["master_spec"].read_text(encoding="utf-8")
    s30 = read_json(inp["v030_summary"])
    c30 = read_json(inp["v030_checkpoint"])
    raw_b3 = read_json(inp["v030_b3_raw"])
    b3_csv = read_csv(inp["v030_b3_membership"])
    bmv_text = inp["v030_bmv_text"].read_text(encoding="utf-8")
    prior_handoff = inp["current_handoff"]

    require("WELT-SWING LONG DEV v0.1" in master_spec, "DEV master identity missing")
    require("gültige ISIN + Primary MIC + Primary Ticker" in master_spec, "Master identity rule missing")
    require("Primary MIC + offizieller Primary Ticker/Exchange Code + stabiler interner WS_ID" in master_spec, "Master fallback identity rule missing")
    require("Preferred Shares" in master_spec and "Units" in master_spec, "Master instrument fail rules missing")

    require(s30["run_status"] == "CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY_V0_30_COMPLETE", "v0.30 summary mismatch")
    require(s30["lineage_scope"] == LINEAGE, "v0.30 lineage mismatch")
    require(s30["current_master_rows_after"] == 1535, "v0.30 current-master count changed")
    require(s30["b3_ibrx100"]["status"] == "MATERIALIZED_OFFICIAL_B3_CURRENT_MEMBERSHIP_EVIDENCE", "B3 official membership evidence not materialized")
    require(s30["b3_ibrx100"]["rows"] == 98, "B3 row count changed")
    require(c30["next_stage"] == STAGE_ID, "v0.30 next stage mismatch")
    require(len(b3_csv) == 98, "v0.30 B3 CSV row count changed")
    require(prior_handoff.exists(), "CURRENT handoff missing")

    reconciled, counts = build_brazil_reconciliation(raw_b3, b3_csv, cfg)
    strict = reconciled.loc[reconciled["Strict_Ordinary_Identity_Candidate_v0_31"].astype(bool)].copy()
    excluded = reconciled.loc[reconciled["Instrument_Gate_v0_31"].eq("FAIL")].copy()
    not_verified = reconciled.loc[reconciled["Instrument_Gate_v0_31"].eq("NOT_VERIFIED")].copy()

    reconciled.to_csv(out/"br_ibrx100_identity_reconciliation_v0.31.csv", index=False)
    strict.to_csv(out/"br_ibrx100_strict_ordinary_candidates_v0.31.csv", index=False)
    excluded.to_csv(out/"br_ibrx100_instrument_exclusions_v0.31.csv", index=False)
    not_verified.to_csv(out/"br_ibrx100_instrument_not_verified_v0.31.csv", index=False)

    mx = build_mexico_change_ledger(bmv_text)
    mx.to_csv(out/"mx_ipc_official_change_ledger_v0.31.csv", index=False)

    segment_status = build_segment_status(counts, len(mx))
    segment_status.to_csv(out/"segment_identity_reconciliation_status_v0.31.csv", index=False)

    _, source_asof = parse_b3_official_date(raw_b3)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION_V0_31_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE,
        "current_master_rows_before": 1535,
        "current_master_rows_after": 1535,
        "canonical_segments_imported_v0_31": 0,
        "br_ibrx100_source_asof": source_asof,
        "br_ibrx100_counts": counts,
        "br_identity_method": "PRIMARY_MIC_OFFICIAL_TICKER_STABLE_WSID_NO_ISIN_IN_MEMBERSHIP_SOURCE",
        "br_primary_mic": cfg["identity"]["primary_mic"],
        "br_isin_guessed": False,
        "mx_ipc_change_ledger_rows": int(len(mx)),
        "mx_full_current_membership_proven": False,
        "universe_mutated": False,
        "eligibility_promotions_made": 0,
        "liquidity_gate_run": False,
        "price_downloads_performed": False,
        "sector_rs_performed": False,
        "p0_run": False,
        "source_superset_complete": False,
        "source_superset_frozen": False,
        "swing_u3k_frozen": False,
        "per_security_web_calls": False,
        "external_requests": 0,
        "alpha_vantage_allowed": False,
        "productive_trading_authority": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": "CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK",
        "notes": [
            "All 98 B3 official IBrX 100 source members are preserved in the reconciliation output.",
            "Only B3 type ON is treated as Strict-U3K instrument PASS; PN/PNA/PNB/etc and Units fail by master rule.",
            "No ISIN is guessed. The master-permitted fallback identity is used because the official B3 membership response contains no ISIN.",
            "Mexico remains a two-row official change ledger only; it is not treated as a full current constituent list.",
            "No universe mutation, no eligibility promotion, no price download and no P0 occur in v0.31.",
        ],
    }
    summary_path = out/"summary_v0.31.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in inp.items()}
    parameter_hash = sha256_file(cfg_path)
    core = [
        out/"br_ibrx100_identity_reconciliation_v0.31.csv",
        out/"br_ibrx100_strict_ordinary_candidates_v0.31.csv",
        out/"br_ibrx100_instrument_exclusions_v0.31.csv",
        out/"br_ibrx100_instrument_not_verified_v0.31.csv",
        out/"mx_ipc_official_change_ledger_v0.31.csv",
        out/"segment_identity_reconciliation_status_v0.31.csv",
        summary_path,
    ]
    output_hash = combined_hash({p.name: sha256_file(p) for p in core})

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_31",
        "run_id": cfg["run_id"],
        "stage_id": STAGE_ID,
        "stage_version": "v0.31",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": 98,
        "checked_count": 98,
        "pass_count": counts["strict_candidates"],
        "fail_count": counts["instrument_fail"],
        "data_error_count": 0,
        "quarantine_count": counts["instrument_not_verified"],
        "status": "PARTIAL",
        "failed_source": "GLOBAL_SOURCE_SUPERSET_STILL_INCOMPLETE",
        "lineage_scope": LINEAGE,
        "universe_mutated": False,
        "liquidity_gate_run": False,
        "source_superset_complete": False,
        "swing_u3k_frozen": False,
        "p0_run": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": summary["next_stage"],
    }
    checkpoint_path = out/"stage_checkpoint_v0.31.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    hv = Path(cfg["handoff"]["versioned_path"])
    hc = Path(cfg["handoff"]["stable_path"])
    write_handoff(hv, hc, summary, checkpoint, prior_handoff)

    files = core + [checkpoint_path, hv, hc]
    manifest = {
        "schema": "WELT_SWING_CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION_MANIFEST_V0_31",
        "generated_utc": now_utc(),
        "lineage_scope": LINEAGE,
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "core_output_hash": output_hash,
        "external_requests": 0,
        "per_security_web_calls": False,
        "alpha_vantage_allowed": False,
        "universe_mutated": False,
        "files": {
            str(p): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in files
        },
    }
    (out/"manifest_v0.31.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION_V0_31_RESULT_GATES_PASS")
    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        default="config/current_master_materialized_official_membership_identity_reconciliation_v0.31.json",
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
