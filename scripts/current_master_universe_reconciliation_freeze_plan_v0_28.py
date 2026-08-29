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

SCHEMA = "WELT_SWING_CURRENT_MASTER_UNIVERSE_RECONCILIATION_FREEZE_PLAN_V0_28"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_28"
LINEAGE_SCOPE = "CURRENT_MASTER_CLEAN_RESTART"
STAGE_ID = "CURRENT_MASTER_OFFICIAL_SOURCE_UNIVERSE_RECONCILIATION_AND_FREEZE_PLAN"

TARGET_SEGMENTS = [
    ("EU_STOXX600", "STOXX Europe 600"),
    ("US_SP1500", "S&P Composite 1500"),
    ("CA_TSX", "S&P/TSX Composite"),
    ("MX_IPC", "S&P/BMV IPC"),
    ("JP_N225", "Nikkei 225"),
    ("HK_HSI", "Hang Seng Index"),
    ("CN_CSI300", "CSI 300"),
    ("IN_NIFTY50", "Nifty 50"),
    ("KR_KOSPI200", "KOSPI 200"),
    ("TW_TW50", "FTSE TWSE Taiwan 50"),
    ("AU_ASX200", "S&P/ASX 200"),
    ("NZ_NZX50", "S&P/NZX 50"),
    ("BR_IBRX100", "IBrX 100"),
    ("ZA_TOP40", "FTSE/JSE Top 40"),
]

KNOWN_BLOCKER_OVERRIDES = {
    "US_SP1500": (
        "SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED",
        "Official S&P public access does not provide a verified full S&P Composite 1500 constituent export; "
        "do not substitute Wikipedia or another third-party list.",
    ),
}

IMPORTED_EXPECTED = {
    "EU_STOXX600": 600,
    "CA_TSX": 217,
    "JP_N225": 225,
    "HK_HSI": 93,
    "CN_CSI300": 300,
    "IN_NIFTY50": 50,
    "TW_TW50": 50,
}

P0_RUN = False
SECTOR_RS_PERFORMED = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
SWING_U3K_FROZEN = False
SOURCE_SUPERSET_COMPLETE = False


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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_master(path: Path) -> tuple[pd.DataFrame, list[str]]:
    xls = pd.ExcelFile(path)
    require("Universe_Master" in xls.sheet_names, f"Universe_Master sheet missing; sheets={xls.sheet_names}")
    df = pd.read_excel(path, sheet_name="Universe_Master", dtype=str, keep_default_na=False)
    return df, list(xls.sheet_names)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items: dict[str, str]) -> str:
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def valid_isin(v: Any) -> bool:
    s = re.sub(r"\s+", "", txt(v)).upper()
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", s))


def identity_class(row: pd.Series) -> str:
    ws = txt(row.get("WS_ID"))
    mic = txt(row.get("Primary_MIC"))
    ticker = txt(row.get("Primary_Ticker"))
    isin = txt(row.get("ISIN"))
    if valid_isin(isin) and ws and mic and ticker:
        return "ISIN_MIC_TICKER_STRICT_IDENTITY"
    if not isin and ws and mic and ticker:
        return "MIC_TICKER_WSID_FALLBACK_IDENTITY"
    return "IDENTITY_INCOMPLETE_OR_INVALID"


def source_ids(series: pd.Series) -> str:
    vals = sorted({txt(x) for x in series if txt(x)})
    return ";".join(vals)


def date_range_text(series: pd.Series) -> str:
    vals = [txt(x) for x in series if txt(x)]
    if not vals:
        return ""
    return f"{min(vals)}..{max(vals)}"


def build_segment_inventory(master: pd.DataFrame) -> pd.DataFrame:
    actual_counts = master["Primary_Universe_Index"].astype(str).value_counts().to_dict()
    rows = []
    for seg_id, target_name in TARGET_SEGMENTS:
        n = int(actual_counts.get(seg_id, 0))
        if n > 0:
            state = "IMPORTED_CURRENT_MASTER_R6"
            source_gate = "IMPORTED_PENDING_EXPLICIT_SOURCE_EVIDENCE_FREEZE_AUDIT"
            blocker = ""
            note = (
                "Present in the current 1535-row r6 clean-restart master. "
                "v0.28 does not silently infer missing source-registry evidence."
            )
        else:
            state = "NOT_IMPORTED_CURRENT_MASTER_R6"
            if seg_id in KNOWN_BLOCKER_OVERRIDES:
                source_gate, note = KNOWN_BLOCKER_OVERRIDES[seg_id]
            else:
                source_gate = "NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED"
                note = (
                    "No current-master row is present. Official full-source materialization remains required; "
                    "legacy/pre-master constituent evidence is not accepted as canonical substitute."
                )
            blocker = source_gate

        rows.append({
            "Segment_ID": seg_id,
            "Target_Index_Name": target_name,
            "Current_Master_Rows": n,
            "Current_Master_State_v0_28": state,
            "Source_Gate_State_v0_28": source_gate,
            "Blocker_v0_28": blocker,
            "Canonical_Source_Authority_v0_28": (
                "CURRENT_MASTER_LINEAGE_IMPORTED_BUT_SOURCE_EVIDENCE_AUDIT_REQUIRED"
                if n > 0 else
                "NOT_CANONICAL_NOT_IMPORTED"
            ),
            "Notes_v0_28": note,
        })
    out = pd.DataFrame(rows)
    require(int(out["Current_Master_Rows"].sum()) == len(master), "Segment inventory does not reconcile to master")
    return out


def build_identity_quality(master: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = master.copy()
    work["Identity_Class_v0_28"] = work.apply(identity_class, axis=1)

    rows = []
    for seg_id, _ in TARGET_SEGMENTS:
        s = work.loc[work["Primary_Universe_Index"].astype(str).eq(seg_id)].copy()
        if s.empty:
            continue
        vc = s["Identity_Class_v0_28"].value_counts().to_dict()
        rows.append({
            "Segment_ID": seg_id,
            "Rows": len(s),
            "Unique_WS_ID": s["WS_ID"].astype(str).nunique(),
            "Duplicate_WS_ID_Rows": int(s["WS_ID"].astype(str).duplicated(keep=False).sum()),
            "Strict_ISIN_MIC_Ticker_Rows": int(vc.get("ISIN_MIC_TICKER_STRICT_IDENTITY", 0)),
            "Fallback_MIC_Ticker_WSID_Rows": int(vc.get("MIC_TICKER_WSID_FALLBACK_IDENTITY", 0)),
            "Incomplete_Or_Invalid_Identity_Rows": int(vc.get("IDENTITY_INCOMPLETE_OR_INVALID", 0)),
            "Missing_ISIN_Rows": int(s["ISIN"].astype(str).str.strip().eq("").sum()) if "ISIN" in s.columns else len(s),
            "Missing_Primary_MIC_Rows": int(s["Primary_MIC"].astype(str).str.strip().eq("").sum()),
            "Missing_Primary_Ticker_Rows": int(s["Primary_Ticker"].astype(str).str.strip().eq("").sum()),
            "Source_IDs": source_ids(s["Source_ID"]) if "Source_ID" in s.columns else "",
            "Source_AsOf_Range": date_range_text(s["Source_AsOf"]) if "Source_AsOf" in s.columns else "",
            "Last_Validated_Range": date_range_text(s["Last_Validated"]) if "Last_Validated" in s.columns else "",
        })

    out = pd.DataFrame(rows)
    duplicate_global = int(work["WS_ID"].astype(str).duplicated(keep=False).sum())
    incomplete_global = int((work["Identity_Class_v0_28"] == "IDENTITY_INCOMPLETE_OR_INVALID").sum())
    meta = {
        "rows": int(len(work)),
        "unique_ws_id": int(work["WS_ID"].astype(str).nunique()),
        "duplicate_ws_id_rows": duplicate_global,
        "strict_identity_rows": int((work["Identity_Class_v0_28"] == "ISIN_MIC_TICKER_STRICT_IDENTITY").sum()),
        "fallback_identity_rows": int((work["Identity_Class_v0_28"] == "MIC_TICKER_WSID_FALLBACK_IDENTITY").sum()),
        "incomplete_or_invalid_identity_rows": incomplete_global,
    }
    return out, meta


def build_source_authority_audit(master: pd.DataFrame, segment_inventory: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, inv in segment_inventory.iterrows():
        seg = inv["Segment_ID"]
        s = master.loc[master["Primary_Universe_Index"].astype(str).eq(seg)]
        rows.append({
            "Segment_ID": seg,
            "Target_Index_Name": inv["Target_Index_Name"],
            "Rows": int(len(s)),
            "Source_IDs_In_Master": source_ids(s["Source_ID"]) if len(s) and "Source_ID" in s.columns else "",
            "Source_AsOf_Populated_Rows": (
                int(s["Source_AsOf"].astype(str).str.strip().ne("").sum())
                if len(s) and "Source_AsOf" in s.columns else 0
            ),
            "Last_Validated_Populated_Rows": (
                int(s["Last_Validated"].astype(str).str.strip().ne("").sum())
                if len(s) and "Last_Validated" in s.columns else 0
            ),
            "v0_28_Source_Authority_State": inv["Canonical_Source_Authority_v0_28"],
            "v0_28_Source_Gate_State": inv["Source_Gate_State_v0_28"],
            "v0_28_Action": (
                "FREEZE_AND_AUDIT_OFFICIAL_SOURCE_PROVENANCE"
                if len(s) else
                "MATERIALIZE_OFFICIAL_FULL_CONSTITUENT_SOURCE"
            ),
        })
    return pd.DataFrame(rows)


def build_lineage_matrix() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Lineage": "CURRENT_MASTER_CLEAN_RESTART_R6",
            "Rows": 1535,
            "Source_Authority_For_Current_Master": True,
            "Universe_Complete": False,
            "Use": "PRIMARY_CURRENT_MASTER_RECONCILIATION_INPUT",
            "Notes": "Seven imported segments; current path toward canonical SOURCE_SUPERSET and future Strict U3K.",
        },
        {
            "Lineage": "LEGACY_PRE_MASTER_PHASE2",
            "Rows": 3663,
            "Source_Authority_For_Current_Master": False,
            "Universe_Complete": False,
            "Use": "ENGINEERING_AND_DIAGNOSTIC_EVIDENCE_ONLY",
            "Notes": "Contains fallback-derived constituent lineage incompatible with the current master source gate.",
        },
        {
            "Lineage": "LEGACY_V0_27_CLOSEOUT",
            "Rows": 710,
            "Source_Authority_For_Current_Master": False,
            "Universe_Complete": False,
            "Use": "LEGACY_REQUALIFICATION_CLOSEOUT_ONLY",
            "Notes": "Useful diagnostics; must not canonize fallback-derived memberships.",
        },
    ])


def build_freeze_plan(segment_inventory: pd.DataFrame) -> pd.DataFrame:
    absent = segment_inventory.loc[segment_inventory["Current_Master_Rows"].eq(0), "Segment_ID"].tolist()
    return pd.DataFrame([
        {
            "Step": 1,
            "Stage": "CURRENT_MASTER_SOURCE_PROVENANCE_FREEZE",
            "Required": True,
            "State_v0_28": "PENDING",
            "Action": "Freeze explicit official-source provenance for the seven currently imported r6 segments.",
        },
        {
            "Step": 2,
            "Stage": "MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION",
            "Required": True,
            "State_v0_28": "BLOCKED_OR_NOT_RUN",
            "Action": "Materialize official full constituent sources for missing segments: " + ";".join(absent),
        },
        {
            "Step": 3,
            "Stage": "CURRENT_MASTER_IDENTITY_REVALIDATION",
            "Required": True,
            "State_v0_28": "NOT_RUN_GLOBAL",
            "Action": "Revalidate ISIN/MIC/Primary Ticker/WS_ID identities on the completed current-master source snapshot.",
        },
        {
            "Step": 4,
            "Stage": "SOURCE_SUPERSET_FREEZE",
            "Required": True,
            "State_v0_28": "NOT_READY",
            "Action": "Freeze a versioned current-master SOURCE_SUPERSET only after accepted source coverage accounting.",
        },
        {
            "Step": 5,
            "Stage": "U3K_ELIGIBILITY_REBUILD",
            "Required": True,
            "State_v0_28": "NOT_RUN",
            "Action": "Run data-quality, instrument, primary-market liquidity and execution eligibility against the current-master lineage.",
        },
        {
            "Step": 6,
            "Stage": "SWING_U3K_FROZEN",
            "Required": True,
            "State_v0_28": "NOT_READY",
            "Action": "Deterministically freeze <=3000 eligible securities; no regional quota and no threshold weakening.",
        },
        {
            "Step": 7,
            "Stage": "P0_GLOBAL_PRICE_FIRST",
            "Required": True,
            "State_v0_28": "BLOCKED",
            "Action": "Run P0 only after a valid SWING_U3K_FROZEN exists; otherwise remain RESEARCH_PARTIAL.",
        },
    ])


def write_handoff(
    path: Path,
    stable_path: Path,
    summary: dict,
    checkpoint: dict,
    input_hashes: dict[str, str],
    segment_inventory: pd.DataFrame,
    coverage: dict,
) -> None:
    imported = segment_inventory.loc[segment_inventory["Current_Master_Rows"].gt(0)]
    absent = segment_inventory.loc[segment_inventory["Current_Master_Rows"].eq(0)]
    trigger_sha = os.environ.get("GITHUB_SHA", "LOCAL_OR_UNKNOWN")
    imported_lines = "\n".join(
        f"- `{r.Segment_ID}` — {r.Target_Index_Name}: {int(r.Current_Master_Rows)} rows"
        for r in imported.itertuples()
    )
    absent_lines = "\n".join(
        f"- `{r.Segment_ID}` — {r.Target_Index_Name}: `{r.Source_Gate_State_v0_28}`"
        for r in absent.itertuples()
    )
    handoff = f"""# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.28  
**Generated UTC:** {summary['generated_utc']}  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Primary lineage:** `CURRENT_MASTER_CLEAN_RESTART`  
**Trigger/input commit:** `{trigger_sha}`

## 1. Authority

Authoritative DEV master:

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains unchanged and solely authoritative for productive Swing decisions.

Alpha Vantage remains forbidden.

## 2. Current primary universe truth

The current-master r6 clean-restart snapshot contains **{summary['current_master_rows']} securities from {summary['imported_segment_count']} of {summary['target_segment_count']} target segments**.

It is a valid **RESEARCH_PARTIAL source snapshot**, not the final global SOURCE_SUPERSET and not a `SWING_U3K_FROZEN`.

Imported current-master segments:

{imported_lines}

Missing target segments:

{absent_lines}

## 3. Identity state

- Current-master rows: {summary['identity_quality']['rows']}
- Unique WS_ID: {summary['identity_quality']['unique_ws_id']}
- Duplicate WS_ID rows: {summary['identity_quality']['duplicate_ws_id_rows']}
- Strict ISIN + MIC + Primary Ticker rows: {summary['identity_quality']['strict_identity_rows']}
- Allowed fallback MIC + Primary Ticker + WS_ID rows: {summary['identity_quality']['fallback_identity_rows']}
- Incomplete/invalid identity rows: {summary['identity_quality']['incomplete_or_invalid_identity_rows']}

## 4. Historical r6 price snapshot — context only

The frozen historical `output_research_1535/coverage.json` is dated `{coverage.get('generated_utc','')}` and is **not a fresh current price run**.

- Universe: {coverage.get('universe_count')}
- READY: {coverage.get('ready_count')}
- Mapping coverage: {coverage.get('mapping_coverage_pct')}%
- Price-ready coverage: {coverage.get('price_ready_coverage_pct')}%
- P0: `{coverage.get('p0_status')}`

Do not use this historical coverage file as proof that prices are currently fresh.

## 5. Legacy lineage closeout

v0.27 successfully closed the useful legacy/pre-master requalification loop.

The old Phase2/3663 lineage remains engineering/diagnostic evidence only and is **not canonical source authority under the current master**.

Legacy v0.27 did not change instrument decisions or eligibility and did not run P0.

## 6. Current v0.28 checkpoint

- Stage: `{checkpoint['stage_id']}`
- Run ID: `{checkpoint['run_id']}`
- Status: `{checkpoint['status']}`
- Input count: {checkpoint['input_count']}
- Checked: {checkpoint['checked_count']}
- PASS accounting: {checkpoint['pass_count']}
- FAIL accounting: {checkpoint['fail_count']}
- Core output hash: `{checkpoint['output_hash']}`
- Coverage gate: `{checkpoint['coverage_gate_status']}`
- Strict U3K frozen: `{str(summary['swing_u3k_frozen']).lower()}`
- P0 run: `{str(summary['p0_run']).lower()}`

## 7. Recovery order

For reconstruction after context loss, use this order:

1. `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
2. `WELT-SWING-CURRENT-Handoff-CURRENT.md`
3. `output_current_master_reconciliation_v0_28/stage_checkpoint_v0.28.json`
4. `output_current_master_reconciliation_v0_28/manifest_v0.28.json`
5. `universe/Welt-Swing-Universe-Master-v2.0.xlsx`
6. `universe/research_partial_1535_manifest.json`
7. `output_research_1535/coverage.json` only as historical price-context
8. `output_official_security_type_data_requalification_v0_27/summary_v0.27.json` only for legacy closeout

Never reconstruct current-master canonical membership from the legacy Phase2/3663 source superset.

## 8. Frozen input SHA-256

- DEV master: `{input_hashes['master_spec']}`
- Current master r6 XLSX: `{input_hashes['current_master_xlsx']}`
- Research 1535 CSV: `{input_hashes['research_1535_csv']}`
- Research 1535 manifest: `{input_hashes['research_1535_manifest']}`
- Historical research coverage: `{input_hashes['research_1535_coverage']}`
- Legacy v0.27 summary: `{input_hashes['v027_summary']}`
- Legacy v0.27 checkpoint: `{input_hashes['v027_checkpoint']}`

## 9. Next stage

`{summary['next_stage']}`

Primary goal: materialize/freeze official source provenance for the current-master lineage and acquire the missing official full constituent sources without third-party substitution.

## 10. Handoff policy

From v0.28 onward, major development stages should refresh both:

- a versioned handoff (`WELT-SWING-CURRENT-Handoff-vX.Y.md`)
- the stable recovery alias (`WELT-SWING-CURRENT-Handoff-CURRENT.md`)

The stable alias is the first recovery document after the DEV master.
"""
    path.write_text(handoff, encoding="utf-8")
    stable_path.write_text(handoff, encoding="utf-8")


def self_test() -> None:
    row = pd.Series({"WS_ID":"W1","ISIN":"US0378331005","Primary_MIC":"XNAS","Primary_Ticker":"AAPL"})
    assert identity_class(row) == "ISIN_MIC_TICKER_STRICT_IDENTITY"
    row2 = pd.Series({"WS_ID":"W2","ISIN":"","Primary_MIC":"XTKS","Primary_Ticker":"7203"})
    assert identity_class(row2) == "MIC_TICKER_WSID_FALLBACK_IDENTITY"
    assert len(TARGET_SEGMENTS) == 14
    assert sum(IMPORTED_EXPECTED.values()) == 1535
    assert set(IMPORTED_EXPECTED) == {
        "EU_STOXX600","CA_TSX","JP_N225","HK_HSI","CN_CSI300","IN_NIFTY50","TW_TW50"
    }
    assert P0_RUN is False
    assert PRODUCTIVE_TRADING_AUTHORITY is False
    assert ALPHA_VANTAGE_ALLOWED is False
    print("CURRENT_MASTER_UNIVERSE_RECONCILIATION_FREEZE_PLAN_V0_28_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    started = now_utc()
    cfg = read_json(cfg_path)
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    inputs = {k: Path(v) for k, v in cfg["inputs"].items()}
    master_spec = inputs["master_spec"].read_text(encoding="utf-8")
    master, workbook_sheets = read_master(inputs["current_master_xlsx"])
    research = read_csv(inputs["research_1535_csv"])
    research_manifest = read_json(inputs["research_1535_manifest"])
    coverage = read_json(inputs["research_1535_coverage"])
    v27 = read_json(inputs["v027_summary"])
    c27 = read_json(inputs["v027_checkpoint"])

    # Authority/master gates.
    require("WELT-SWING LONG DEV v0.1" in master_spec, "DEV master identity not found")
    require("Alpha Vantage ist für WELT-SWING LONG vollständig ausgeschlossen" in master_spec, "Alpha prohibition missing")
    require(len(TARGET_SEGMENTS) == 14, "Target segment configuration changed")

    # Current r6 master gates.
    required_cols = {"WS_ID","ISIN","Primary_MIC","Primary_Ticker","Primary_Universe_Index"}
    require(required_cols.issubset(set(master.columns)), f"Current master missing columns: {sorted(required_cols-set(master.columns))}")
    require(len(master) == 1535, f"Current r6 master rows changed: {len(master)}")
    require(not master["WS_ID"].astype(str).duplicated().any(), "Duplicate WS_ID in current master")

    actual_counts = master["Primary_Universe_Index"].astype(str).value_counts().to_dict()
    require(actual_counts == IMPORTED_EXPECTED, f"Current r6 segment counts changed: {actual_counts}")

    # Research snapshot gates and exact key reconciliation.
    require(research_manifest.get("source_master_rows") == 1535, "Research manifest master count changed")
    require(research_manifest.get("rows") == 1535, "Research manifest row count changed")
    require(research_manifest.get("scope") == "RESEARCH_PARTIAL", "Research manifest scope changed")
    require(research_manifest.get("universe_complete") is False, "Research manifest unexpectedly claims complete universe")
    require(research_manifest.get("p0_run") is False, "Research manifest unexpectedly ran P0")
    require(research_manifest.get("alpha_vantage_allowed") is False, "Research manifest Alpha gate failed")
    require(research_manifest.get("counts") == IMPORTED_EXPECTED, "Research manifest segment counts differ from r6")
    require(
        sha256_file(inputs["research_1535_csv"]) == research_manifest.get("research_csv_sha256"),
        "Research 1535 CSV content hash differs from its manifest",
    )
    require(len(research) == 1535, "Research CSV row count changed")
    compare_cols = ["WS_ID","Primary_Universe_Index","Primary_MIC","Primary_Ticker"]
    mcmp = master[compare_cols].fillna("").astype(str).sort_values("WS_ID").reset_index(drop=True)
    rcmp = research[compare_cols].fillna("").astype(str).sort_values("WS_ID").reset_index(drop=True)
    require(mcmp.equals(rcmp), "Research 1535 identity keys differ from current master XLSX")

    # Historical price coverage is context only, never freshness authority.
    require(coverage.get("universe_count") == 1535, "Historical coverage denominator changed")
    require(coverage.get("productive_trading_authority") is False, "Historical coverage productive gate failed")
    require(coverage.get("alpha_vantage_allowed") is False, "Historical coverage Alpha gate failed")

    # Legacy closeout gates.
    require(v27.get("run_status") == "OFFICIAL_SECURITY_TYPE_SEMANTICS_REPAIRED_DATA_REQUALIFICATION_V0_27_COMPLETE", "v0.27 closeout missing")
    require(v27.get("lineage_scope") == "LEGACY_PRE_MASTER_RESEARCH_LINEAGE", "v0.27 lineage mismatch")
    require(v27.get("instrument_decisions_changed") == 0, "v0.27 changed instrument decisions")
    require(v27.get("eligibility_promotions_made") == 0, "v0.27 changed eligibility")
    require(v27.get("p0_run") is False, "v0.27 P0 gate failed")
    require(c27.get("next_stage") == STAGE_ID, "v0.27 next stage does not point to v0.28")

    segment_inventory = build_segment_inventory(master)
    identity_audit, identity_meta = build_identity_quality(master)
    source_audit = build_source_authority_audit(master, segment_inventory)
    lineage_matrix = build_lineage_matrix()
    freeze_plan = build_freeze_plan(segment_inventory)

    imported_count = int((segment_inventory["Current_Master_Rows"] > 0).sum())
    missing_count = int((segment_inventory["Current_Master_Rows"] == 0).sum())
    require(imported_count == 7, f"Imported segment count changed: {imported_count}")
    require(missing_count == 7, f"Missing segment count changed: {missing_count}")

    segment_inventory.to_csv(out_dir/"current_master_segment_inventory_v0.28.csv", index=False)
    identity_audit.to_csv(out_dir/"current_master_identity_quality_v0.28.csv", index=False)
    source_audit.to_csv(out_dir/"current_master_source_authority_audit_v0.28.csv", index=False)
    lineage_matrix.to_csv(out_dir/"lineage_authority_matrix_v0.28.csv", index=False)
    freeze_plan.to_csv(out_dir/"freeze_plan_v0.28.csv", index=False)

    blocker_register = segment_inventory.loc[
        segment_inventory["Current_Master_Rows"].eq(0),
        ["Segment_ID","Target_Index_Name","Source_Gate_State_v0_28","Blocker_v0_28","Notes_v0_28"],
    ].copy()
    blocker_register.to_csv(out_dir/"current_master_blocker_register_v0.28.csv", index=False)

    sheet_inventory = pd.DataFrame({"Workbook_Sheet": workbook_sheets})
    sheet_inventory.to_csv(out_dir/"current_master_workbook_sheet_inventory_v0.28.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "CURRENT_MASTER_UNIVERSE_RECONCILIATION_FREEZE_PLAN_V0_28_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE_SCOPE,
        "target_segment_count": 14,
        "imported_segment_count": imported_count,
        "missing_segment_count": missing_count,
        "current_master_rows": 1535,
        "imported_segment_counts": IMPORTED_EXPECTED,
        "missing_segments": blocker_register["Segment_ID"].tolist(),
        "identity_quality": identity_meta,
        "source_superset_complete": SOURCE_SUPERSET_COMPLETE,
        "source_superset_frozen": False,
        "swing_u3k_eligible_ready": False,
        "swing_u3k_frozen": SWING_U3K_FROZEN,
        "p0_run": P0_RUN,
        "sector_rs_performed": SECTOR_RS_PERFORMED,
        "price_downloads_performed": False,
        "external_requests": 0,
        "per_security_web_calls": False,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "legacy_phase2_canonical_source_authority": False,
        "historical_research_1535_price_context": {
            "generated_utc": coverage.get("generated_utc"),
            "ready_count": coverage.get("ready_count"),
            "price_ready_coverage_pct": coverage.get("price_ready_coverage_pct"),
            "mapping_coverage_pct": coverage.get("mapping_coverage_pct"),
            "freshness_authority": False,
        },
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE_7_OF_14",
        "failed_source": "MULTIPLE_TARGET_SEGMENTS_NOT_IMPORTED",
        "next_stage": "CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
        "notes": [
            "v0.28 is an offline reconciliation/plan stage. It makes no network requests and no constituent substitutions.",
            "The current r6 1535-row master is the primary current-master lineage; the legacy Phase2/3663 lineage is engineering evidence only.",
            "Seven target segments remain absent from the current-master source snapshot, so Strict U3K freeze and global P0 remain blocked.",
            "The historical research_1535 price coverage is retained as context only and is not treated as fresh market data.",
            "From v0.28 onward major stages refresh both a versioned Current Handoff and a stable recovery alias.",
        ],
    }
    summary_path = out_dir/"summary_v0.28.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in inputs.items()}
    parameter_hash = sha256_file(cfg_path)
    core_files = [
        out_dir/"current_master_segment_inventory_v0.28.csv",
        out_dir/"current_master_identity_quality_v0.28.csv",
        out_dir/"current_master_source_authority_audit_v0.28.csv",
        out_dir/"current_master_blocker_register_v0.28.csv",
        out_dir/"current_master_workbook_sheet_inventory_v0.28.csv",
        out_dir/"lineage_authority_matrix_v0.28.csv",
        out_dir/"freeze_plan_v0.28.csv",
        summary_path,
    ]
    output_hash = combined_hash({p.name: sha256_file(p) for p in core_files})

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "run_id": cfg["run_id"],
        "stage_id": STAGE_ID,
        "stage_version": "v0.28",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": 14,
        "checked_count": 14,
        "pass_count": 7,
        "fail_count": 7,
        "data_error_count": 0,
        "quarantine_count": 0,
        "status": "PARTIAL",
        "failed_source": "MULTIPLE_TARGET_SEGMENTS_NOT_IMPORTED",
        "lineage_scope": LINEAGE_SCOPE,
        "current_master_rows": 1535,
        "source_superset_complete": False,
        "swing_u3k_frozen": False,
        "p0_run": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE_7_OF_14",
        "next_stage": "CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION",
    }
    checkpoint_path = out_dir/"stage_checkpoint_v0.28.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    # Recovery handoff is generated from actual stage results.
    handoff_versioned = Path(cfg["handoff"]["versioned_path"])
    handoff_stable = Path(cfg["handoff"]["stable_path"])
    write_handoff(
        handoff_versioned,
        handoff_stable,
        summary,
        checkpoint,
        input_hashes,
        segment_inventory,
        coverage,
    )

    manifest_files = core_files + [checkpoint_path, handoff_versioned, handoff_stable]
    manifest = {
        "schema": "WELT_SWING_CURRENT_MASTER_UNIVERSE_RECONCILIATION_FREEZE_PLAN_MANIFEST_V0_28",
        "generated_utc": now_utc(),
        "lineage_scope": LINEAGE_SCOPE,
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "core_output_hash": output_hash,
        "external_requests": 0,
        "alpha_vantage_allowed": False,
        "p0_run": False,
        "files": {
            str(p): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in manifest_files
        },
    }
    manifest_path = out_dir/"manifest_v0.28.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("CURRENT_MASTER_UNIVERSE_RECONCILIATION_FREEZE_PLAN_V0_28_RESULT_GATES_PASS")
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        default="config/current_master_universe_reconciliation_freeze_plan_v0.28.json",
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    run(Path(args.config))


if __name__ == "__main__":
    main()
