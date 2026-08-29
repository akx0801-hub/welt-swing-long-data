#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from datetime import datetime, timezone

import pandas as pd
import requests
from pypdf import PdfReader

SCHEMA = "WELT_SWING_CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY_V0_30"
STAGE_ID = "CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY"
LINEAGE = "CURRENT_MASTER_CLEAN_RESTART"

SEGMENTS = [
    "US_SP1500", "MX_IPC", "KR_KOSPI200", "AU_ASX200",
    "NZ_NZX50", "BR_IBRX100", "ZA_TOP40",
]


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


def host_allowed(url: str, domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in domains)


def b3_materialize(session: requests.Session, cfg: dict, out_dir: Path) -> dict[str, Any]:
    payload = {
        "language": "pt-br",
        "pageNumber": 1,
        "pageSize": int(cfg["page_size"]),
        "index": "IBXX",
        "segment": "1",
    }
    encoded = base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    url = cfg["base_url"].rstrip("/") + "/" + encoded
    require(host_allowed(url, cfg["allowed_domains"]), "B3 URL outside allowlist")

    result = {
        "source": "B3_OFFICIAL_INDEXPROXY_GETPORTFOLIODAY",
        "url": url,
        "http_status": "",
        "status": "NOT_RUN",
        "rows": 0,
        "unique_codes": 0,
        "page_size": int(cfg["page_size"]),
        "error": "",
    }
    out_csv = out_dir / "b3_ibrx100_membership_v0.30.csv"
    raw_json = out_dir / "b3_ibrx100_official_raw_v0.30.json"

    try:
        r = session.get(url, timeout=30)
        result["http_status"] = int(r.status_code)
        r.raise_for_status()
        data = r.json()
        raw_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        rows = data.get("results")
        require(isinstance(rows, list), "B3 response missing results list")

        parsed = []
        for x in rows:
            code = txt(x.get("cod"))
            asset = txt(x.get("asset"))
            if not code or not asset:
                continue
            parsed.append({
                "Primary_Ticker_Candidate": code,
                "Security_Name_Official": asset,
                "B3_Type": txt(x.get("type")),
                "Theoretical_Quantity": txt(x.get("theoricalQty")),
                "Participation_Pct": txt(x.get("part")),
                "Segment_ID": "BR_IBRX100",
                "Primary_MIC_Candidate": "BVMF",
                "Source_ID": "B3_OFFICIAL_INDEXPROXY_GETPORTFOLIODAY",
                "Source_URL": url,
                "Source_AsOf_Observed_UTC": now_utc(),
                "Canonical_Import_v0_30": False,
                "Identity_Reconciliation_Required": True,
            })

        df = pd.DataFrame(parsed)
        if df.empty:
            df = pd.DataFrame(columns=[
                "Primary_Ticker_Candidate","Security_Name_Official","B3_Type",
                "Theoretical_Quantity","Participation_Pct","Segment_ID",
                "Primary_MIC_Candidate","Source_ID","Source_URL",
                "Source_AsOf_Observed_UTC","Canonical_Import_v0_30",
                "Identity_Reconciliation_Required",
            ])
        df = df.drop_duplicates(subset=["Primary_Ticker_Candidate"], keep="first")
        df.to_csv(out_csv, index=False)

        result["rows"] = int(len(df))
        result["unique_codes"] = int(df["Primary_Ticker_Candidate"].nunique()) if len(df) else 0
        if len(df) >= int(cfg["minimum_rows_for_membership_evidence"]):
            result["status"] = "MATERIALIZED_OFFICIAL_B3_CURRENT_MEMBERSHIP_EVIDENCE"
        else:
            result["status"] = "B3_RESPONSE_PARSED_ROW_COUNT_BELOW_GATE"
    except Exception as e:
        pd.DataFrame(columns=[
            "Primary_Ticker_Candidate","Security_Name_Official","B3_Type",
            "Theoretical_Quantity","Participation_Pct","Segment_ID",
            "Primary_MIC_Candidate","Source_ID","Source_URL",
            "Source_AsOf_Observed_UTC","Canonical_Import_v0_30",
            "Identity_Reconciliation_Required",
        ]).to_csv(out_csv, index=False)
        result["status"] = "B3_OFFICIAL_ENDPOINT_ERROR"
        result["error"] = f"{type(e).__name__}: {e}"
    return result


def krx_materialize(session: requests.Session, cfg: dict, out_dir: Path) -> dict[str, Any]:
    url = cfg["url"]
    require(host_allowed(url, cfg["allowed_domains"]), "KRX URL outside allowlist")
    payload = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT00701",
        "locale": "ko_KR",
        "trdDd": cfg["trade_date"],
        "indIdx": "1",
        "indIdx2": "028",
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
    }
    result = {
        "source": "KRX_OFFICIAL_MDCSTAT00701",
        "url": url,
        "trade_date": cfg["trade_date"],
        "http_status": "",
        "status": "NOT_RUN",
        "rows": 0,
        "unique_codes": 0,
        "error": "",
    }
    out_csv = out_dir / "krx_kospi200_membership_v0.30.csv"
    raw_path = out_dir / "krx_kospi200_official_raw_v0.30.txt"

    try:
        headers = {
            "Referer": "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd",
            "X-Requested-With": "XMLHttpRequest",
        }
        r = session.post(url, data=payload, headers=headers, timeout=30)
        result["http_status"] = int(r.status_code)
        raw_path.write_text(r.text, encoding="utf-8", errors="replace")
        r.raise_for_status()

        low = r.text.lower()
        if "logout" in low or "login" in low and "error" in low:
            result["status"] = "KRX_OFFICIAL_INTERNAL_API_AUTH_OR_SESSION_BLOCKED"
            pd.DataFrame(columns=[
                "Primary_Ticker_Candidate","Security_Name_Official","Segment_ID",
                "Primary_MIC_Candidate","Source_ID","Source_Trade_Date",
                "Canonical_Import_v0_30","Identity_Reconciliation_Required",
            ]).to_csv(out_csv, index=False)
            return result

        data = r.json()
        rows = data.get("output")
        if not isinstance(rows, list):
            for key in ("OutBlock_1", "block1", "result"):
                if isinstance(data.get(key), list):
                    rows = data[key]
                    break
        require(isinstance(rows, list), "KRX response missing constituent list")

        parsed = []
        for x in rows:
            code = txt(x.get("ISU_SRT_CD"))
            name = txt(x.get("ISU_ABBRV"))
            if not code:
                continue
            parsed.append({
                "Primary_Ticker_Candidate": code,
                "Security_Name_Official": name,
                "Segment_ID": "KR_KOSPI200",
                "Primary_MIC_Candidate": "XKRX",
                "Source_ID": "KRX_OFFICIAL_MDCSTAT00701",
                "Source_Trade_Date": cfg["trade_date"],
                "Canonical_Import_v0_30": False,
                "Identity_Reconciliation_Required": True,
            })

        df = pd.DataFrame(parsed)
        if df.empty:
            df = pd.DataFrame(columns=[
                "Primary_Ticker_Candidate","Security_Name_Official","Segment_ID",
                "Primary_MIC_Candidate","Source_ID","Source_Trade_Date",
                "Canonical_Import_v0_30","Identity_Reconciliation_Required",
            ])
        df = df.drop_duplicates("Primary_Ticker_Candidate")
        df.to_csv(out_csv, index=False)
        result["rows"] = int(len(df))
        result["unique_codes"] = int(df["Primary_Ticker_Candidate"].nunique()) if len(df) else 0
        if len(df) >= int(cfg["minimum_rows_for_membership_evidence"]):
            result["status"] = "MATERIALIZED_OFFICIAL_KRX_CURRENT_MEMBERSHIP_EVIDENCE"
        else:
            result["status"] = "KRX_RESPONSE_PARSED_ROW_COUNT_BELOW_GATE"
    except Exception as e:
        pd.DataFrame(columns=[
            "Primary_Ticker_Candidate","Security_Name_Official","Segment_ID",
            "Primary_MIC_Candidate","Source_ID","Source_Trade_Date",
            "Canonical_Import_v0_30","Identity_Reconciliation_Required",
        ]).to_csv(out_csv, index=False)
        if result["status"] == "NOT_RUN":
            result["status"] = "KRX_OFFICIAL_ENDPOINT_ERROR"
        result["error"] = f"{type(e).__name__}: {e}"
    return result


def select_bmv_final_pdf(candidates: pd.DataFrame) -> str:
    x = candidates.loc[
        candidates["Segment_ID"].eq("MX_IPC")
        & candidates["Candidate_URL"].str.contains(
            r"SP BMV IPC Rebalance Announcement \(English\) - Final\.pdf",
            regex=True,
            case=False,
            na=False,
        )
    ].copy()
    require(len(x) >= 1, "Frozen v0.29 candidate set does not contain final BMV IPC rebalance PDF")
    # Prefer the constituents-list directory over the generic rebalancing directory.
    x["priority"] = x["Candidate_URL"].str.contains("/CTEN_INCM/", regex=False).map({True: 0, False: 1})
    x = x.sort_values(["priority", "Candidate_URL"], kind="mergesort")
    return txt(x.iloc[0]["Candidate_URL"])


def bmv_materialize(session: requests.Session, cfg: dict, candidates: pd.DataFrame, out_dir: Path) -> dict[str, Any]:
    url = select_bmv_final_pdf(candidates)
    require(host_allowed(url, cfg["allowed_domains"]), "BMV PDF outside allowlist")
    result = {
        "source": "BMV_OFFICIAL_IPC_FINAL_REBALANCE_PDF",
        "url": url,
        "http_status": "",
        "status": "NOT_RUN",
        "pdf_bytes": 0,
        "pages": 0,
        "text_chars": 0,
        "error": "",
    }
    pdf_path = out_dir / "bmv_ipc_final_rebalance_v0.30.pdf"
    text_path = out_dir / "bmv_ipc_final_rebalance_text_v0.30.txt"

    try:
        r = session.get(url, timeout=30)
        result["http_status"] = int(r.status_code)
        r.raise_for_status()
        pdf_path.write_bytes(r.content)
        result["pdf_bytes"] = len(r.content)

        reader = PdfReader(BytesIO(r.content))
        parts = []
        for p in reader.pages:
            parts.append(p.extract_text() or "")
        all_text = "\n".join(parts)
        text_path.write_text(all_text, encoding="utf-8")
        result["pages"] = len(reader.pages)
        result["text_chars"] = len(all_text)

        low = all_text.lower()
        if "s&p/bmv ipc" in low and "final" in low and len(all_text) >= 500:
            result["status"] = "OFFICIAL_BMV_FINAL_REBALANCE_DOCUMENT_MATERIALIZED_IDENTITY_EXTRACTION_PENDING"
        else:
            result["status"] = "BMV_PDF_MATERIALIZED_CONTENT_SEMANTICS_NOT_VERIFIED"
    except Exception as e:
        text_path.write_text("", encoding="utf-8")
        result["status"] = "BMV_OFFICIAL_DOCUMENT_ERROR"
        result["error"] = f"{type(e).__name__}: {e}"
    return result


def carry_forward_statuses(s29: dict) -> dict[str, str]:
    states = dict(s29["missing_segment_states"])
    states["US_SP1500"] = "SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED"
    states["AU_ASX200"] = "SOURCE_BLOCKED_GITHUB_RUNNER_SPDJI_403_AND_FULL_EXPORT_NOT_MATERIALIZED"
    states["NZ_NZX50"] = "SOURCE_BLOCKED_PUBLIC_CONSTITUENT_DATA_WITHDRAWN_OR_SUBSCRIPTION_REQUIRED"
    states["ZA_TOP40"] = "SOURCE_BLOCKED_GITHUB_RUNNER_JSE_403_DIRECT_ASSET_ROUTE_REQUIRED"
    return states


def write_handoff(versioned: Path, stable: Path, summary: dict, checkpoint: dict, prior: Path) -> None:
    prior_text = prior.read_text(encoding="utf-8")
    require("Version:** v0.29" in prior_text, "Expected v0.29 CURRENT handoff predecessor")

    body = f"""# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.30  
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

v0.30 performs deep source materialization only. It does not mutate canonical membership.

## 3. Deep materialization results

### BR_IBRX100
- Status: `{summary['b3_ibrx100']['status']}`
- Official rows: {summary['b3_ibrx100']['rows']}
- Unique security codes: {summary['b3_ibrx100']['unique_codes']}
- Canonical import: `false`

### KR_KOSPI200
- Status: `{summary['krx_kospi200']['status']}`
- Official rows: {summary['krx_kospi200']['rows']}
- Unique security codes: {summary['krx_kospi200']['unique_codes']}
- Trade date requested: `{summary['krx_kospi200']['trade_date']}`
- Canonical import: `false`

### MX_IPC
- Status: `{summary['bmv_ipc']['status']}`
- Official PDF bytes: {summary['bmv_ipc']['pdf_bytes']}
- Extracted pages: {summary['bmv_ipc']['pages']}
- Canonical import: `false`

### Carry-forward blockers
- US_SP1500: `{summary['segment_states']['US_SP1500']}`
- AU_ASX200: `{summary['segment_states']['AU_ASX200']}`
- NZ_NZX50: `{summary['segment_states']['NZ_NZX50']}`
- ZA_TOP40: `{summary['segment_states']['ZA_TOP40']}`

## 4. Governance

- Current-master rows before/after: 1,535 / 1,535
- Canonical segments imported in v0.30: 0
- Universe mutation: `false`
- Instrument decisions changed: 0
- Eligibility promotions: 0
- Price downloads: `false`
- P0: `false`
- `SWING_U3K_FROZEN`: `false`

Any materialized official membership remains **identity-import pending** until MIC/ticker/security-type/source-as-of reconciliation is complete.

## 5. Current checkpoint

- Stage: `{checkpoint['stage_id']}`
- Run ID: `{checkpoint['run_id']}`
- Status: `{checkpoint['status']}`
- Checked source workstreams: {checkpoint['checked_count']}
- Materialized membership evidence workstreams: {checkpoint['pass_count']}
- Remaining/non-materialized workstreams: {checkpoint['fail_count']}
- Output hash: `{checkpoint['output_hash']}`
- Next stage: `{checkpoint['next_stage']}`

## 6. Recovery order

1. `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
2. `WELT-SWING-CURRENT-Handoff-CURRENT.md`
3. `output_current_master_source_deep_materialization_v0_30/stage_checkpoint_v0.30.json`
4. `output_current_master_source_deep_materialization_v0_30/manifest_v0.30.json`
5. `output_current_master_source_deep_materialization_v0_30/source_deep_materialization_status_v0.30.csv`
6. `universe/Welt-Swing-Universe-Master-v2.0.xlsx`
7. `output_current_master_missing_source_materialization_v0_29/summary_v0.29.json`

## 7. Handoff policy

Every major DEV stage refreshes both a versioned Current Handoff and `WELT-SWING-CURRENT-Handoff-CURRENT.md`.

## 8. Next stage

`{summary['next_stage']}`

Only official membership evidence that is actually materialized may proceed to identity reconciliation.
"""
    versioned.write_text(body, encoding="utf-8")
    stable.write_text(body, encoding="utf-8")


def self_test() -> None:
    payload = {"language":"pt-br","pageNumber":1,"pageSize":200,"index":"IBXX","segment":"1"}
    enc = base64.b64encode(json.dumps(payload, separators=(",",":")).encode()).decode()
    assert enc.startswith("eyJ")
    assert host_allowed("https://data.krx.co.kr/x", ["krx.co.kr"])
    assert host_allowed("https://www.bmv.com.mx/x", ["bmv.com.mx"])
    assert len(SEGMENTS) == 7
    print("CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY_V0_30_SELF_TEST_PASS")


def run(cfg_path: Path) -> None:
    started = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    inputs = {k: Path(v) for k, v in cfg["inputs"].items()}
    s29 = read_json(inputs["v029_summary"])
    c29 = read_json(inputs["v029_checkpoint"])
    probes29 = read_csv(inputs["v029_probe_status"])
    candidates29 = read_csv(inputs["v029_candidate_links"])
    prior_handoff = inputs["current_handoff"]

    require(s29["run_status"] == "CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_V0_29_COMPLETE", "v0.29 summary mismatch")
    require(s29["lineage_scope"] == LINEAGE, "v0.29 lineage mismatch")
    require(s29["current_master_rows_after"] == 1535, "v0.29 current-master rows changed")
    require(s29["materialized_membership_evidence_segments"] == 0, "v0.29 materialized evidence count changed")
    require(c29["status"] == "PARTIAL", "v0.29 checkpoint status changed")
    require(len(probes29) == 10, "v0.29 probe count changed")
    require(len(candidates29) == 385, "v0.29 candidate-link count changed")
    require(prior_handoff.exists(), "CURRENT handoff missing")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Welt-Swing-Long-DEV-v0.30 official-source-materialization/1.0",
        "Accept-Language": "en-US,en;q=0.8,pt-BR;q=0.7,ko;q=0.6",
    })

    b3 = b3_materialize(session, cfg["b3"], out)
    krx = krx_materialize(session, cfg["krx"], out)
    bmv = bmv_materialize(session, cfg["bmv"], candidates29, out)

    states = carry_forward_statuses(s29)
    states["BR_IBRX100"] = b3["status"]
    states["KR_KOSPI200"] = krx["status"]
    states["MX_IPC"] = bmv["status"]

    status_df = pd.DataFrame([
        {"Segment_ID": seg, "Materialization_State_v0_30": states[seg], "Canonical_Import_v0_30": False}
        for seg in SEGMENTS
    ])
    status_df.to_csv(out/"source_deep_materialization_status_v0.30.csv", index=False)

    membership_passes = int(
        b3["status"].startswith("MATERIALIZED_OFFICIAL_")
    ) + int(
        krx["status"].startswith("MATERIALIZED_OFFICIAL_")
    )

    if membership_passes > 0:
        next_stage = "CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION"
    else:
        next_stage = "CURRENT_MASTER_OFFICIAL_SOURCE_ACCESS_REMEDIATION_V0_31"

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY_V0_30_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE,
        "current_master_rows_before": 1535,
        "current_master_rows_after": 1535,
        "canonical_segments_imported_v0_30": 0,
        "b3_ibrx100": b3,
        "krx_kospi200": krx,
        "bmv_ipc": bmv,
        "segment_states": states,
        "materialized_membership_evidence_workstreams": membership_passes,
        "universe_mutated": False,
        "instrument_decisions_changed": 0,
        "eligibility_promotions_made": 0,
        "price_downloads_performed": False,
        "sector_rs_performed": False,
        "p0_run": False,
        "source_superset_complete": False,
        "source_superset_frozen": False,
        "swing_u3k_frozen": False,
        "per_security_web_calls": False,
        "alpha_vantage_allowed": False,
        "productive_trading_authority": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": next_stage,
    }
    summary_path = out/"summary_v0.30.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in inputs.items()}
    parameter_hash = sha256_file(cfg_path)
    core = [
        out/"b3_ibrx100_membership_v0.30.csv",
        out/"krx_kospi200_membership_v0.30.csv",
        out/"bmv_ipc_final_rebalance_text_v0.30.txt",
        out/"source_deep_materialization_status_v0.30.csv",
        summary_path,
    ]
    output_hash = combined_hash({p.name: sha256_file(p) for p in core})

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_30",
        "run_id": cfg["run_id"],
        "stage_id": STAGE_ID,
        "stage_version": "v0.30",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": 3,
        "checked_count": 3,
        "pass_count": membership_passes,
        "fail_count": 3-membership_passes,
        "data_error_count": 0,
        "quarantine_count": 0,
        "status": "PARTIAL",
        "failed_source": "" if membership_passes == 3 else "UNMATERIALIZED_SOURCE_WORKSTREAMS_REMAIN",
        "lineage_scope": LINEAGE,
        "universe_mutated": False,
        "source_superset_complete": False,
        "swing_u3k_frozen": False,
        "p0_run": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": next_stage,
    }
    checkpoint_path = out/"stage_checkpoint_v0.30.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    hv = Path(cfg["handoff"]["versioned_path"])
    hc = Path(cfg["handoff"]["stable_path"])
    write_handoff(hv, hc, summary, checkpoint, prior_handoff)

    files = core + [checkpoint_path, hv, hc]
    for optional in [
        out/"b3_ibrx100_official_raw_v0.30.json",
        out/"krx_kospi200_official_raw_v0.30.txt",
        out/"bmv_ipc_final_rebalance_v0.30.pdf",
    ]:
        if optional.exists():
            files.append(optional)

    manifest = {
        "schema": "WELT_SWING_CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY_MANIFEST_V0_30",
        "generated_utc": now_utc(),
        "lineage_scope": LINEAGE,
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "core_output_hash": output_hash,
        "external_requests_max": 3,
        "per_security_web_calls": False,
        "alpha_vantage_allowed": False,
        "universe_mutated": False,
        "files": {
            str(p): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in files
        },
    }
    (out/"manifest_v0.30.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY_V0_30_RESULT_GATES_PASS")
    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/current_master_official_source_deep_materialization_retry_v0.30.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
