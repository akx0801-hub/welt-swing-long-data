#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests

SCHEMA = "WELT_SWING_OFFICIAL_BULK_SECURITY_TYPE_PROBE_DATA_GAP_RECHECK_V0_25"

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def read_csv(p):
    return pd.read_csv(p, keep_default_na=False, dtype=str)

def require(cond, msg):
    if not cond:
        raise SystemExit(msg)

def sha256_file(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def combined_hash(d):
    payload = "|".join(f"{k}={d[k]}" for k in sorted(d))
    return hashlib.sha256(payload.encode()).hexdigest()

def host_allowed(url, allowed):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in allowed)

def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("_")

def markers(text):
    t = text.lower()
    return {
        "has_isin": "isin" in t,
        "has_security_type": ("security type" in t or "type of security" in t or "instrument type" in t),
        "has_share": ("share" in t or "shares" in t),
        "has_equity": ("equity" in t or "equities" in t),
        "has_ordinary": ("ordinary" in t or "common stock" in t or "common share" in t),
        "has_preferred": ("preferred" in t or "preference share" in t),
        "has_etf": "etf" in t,
        "has_fund": "fund" in t,
        "has_category": "category" in t,
        "has_subcategory": ("sub-category" in t or "subcategory" in t),
        "has_download": "download" in t,
    }

def candidate_links(base_url, html, allowed, limit):
    hrefs = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', html, flags=re.I)
    keys = ("download","issuer","instrument","security","securities","share","shares","equity","equities","list",".csv",".xls",".xlsx",".zip")
    seen, out = set(), []
    for href in hrefs:
        u = urljoin(base_url, href.strip())
        if not host_allowed(u, allowed):
            continue
        if not any(k in u.lower() for k in keys):
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= limit:
            break
    return out

def self_test():
    assert host_allowed("https://www.londonstockexchange.com/reports", ["londonstockexchange.com"])
    assert not host_allowed("https://example.com/a", ["londonstockexchange.com"])
    print("OFFICIAL_BULK_SECURITY_TYPE_PROBE_DATA_GAP_RECHECK_V0_25_SELF_TEST_PASS")

def probe(spec, cfg, raw_dir):
    allowed = cfg["network_policy"]["allowed_domains"]
    url = spec["url"]
    require(host_allowed(url, allowed), f"Non-whitelisted source: {url}")
    row = {
        "Source_ID": spec["source_id"],
        "Source_Name": spec["source_name"],
        "Coverage_Route": spec["coverage_route"],
        "Primary_MICs": ";".join(spec.get("primary_mics", [])),
        "URL": url,
        "Method": "GET",
        "HTTP_Status": "",
        "Final_URL": "",
        "Content_Type": "",
        "Bytes": 0,
        "SHA256": "",
        "Probe_Status": "ERROR",
        "Candidate_Link_Count": 0,
        "Official_Semantics_Strength_v0_25": "NOT_VERIFIED",
        "Materialization_Status_v0_25": "NOT_MATERIALIZED",
        "Error": "",
    }
    links_out = []
    try:
        r = requests.get(
            url,
            timeout=cfg["network_policy"]["timeout_seconds"],
            allow_redirects=True,
            headers={
                "User-Agent": cfg["network_policy"]["user_agent"],
                "Accept": "text/html,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,*/*;q=0.5",
            },
        )
        row["HTTP_Status"] = r.status_code
        row["Final_URL"] = r.url
        row["Content_Type"] = r.headers.get("content-type", "")
        row["Bytes"] = len(r.content)
        row["SHA256"] = hashlib.sha256(r.content).hexdigest()
        if not host_allowed(r.url, allowed):
            raise RuntimeError(f"Redirect left approved official domains: {r.url}")
        r.raise_for_status()
        row["Probe_Status"] = "HTTP_OK"

        ext = spec.get("raw_extension", ".bin")
        raw = raw_dir / f"{safe_name(spec['source_id'])}{ext}"
        raw.write_bytes(r.content)

        ctype = row["Content_Type"].lower()
        if "text/" in ctype or "json" in ctype or ext in {".html",".txt",".json"}:
            m = markers(r.text)
            row.update(m)
            links = candidate_links(r.url, r.text, allowed, cfg["network_policy"]["candidate_link_limit_per_source"])
            row["Candidate_Link_Count"] = len(links)
            for u in links:
                links_out.append({
                    "Source_ID": spec["source_id"],
                    "Coverage_Route": spec["coverage_route"],
                    "Candidate_URL": u,
                    "Candidate_Host": urlparse(u).hostname or "",
                    "Followed_In_v0_25": False,
                })
            if m["has_isin"] and m["has_security_type"]:
                row["Official_Semantics_Strength_v0_25"] = "STRONG_PAGE_LEVEL_SECURITY_TYPE_SEMANTICS"
            elif m["has_isin"] and (m["has_share"] or m["has_equity"]):
                row["Official_Semantics_Strength_v0_25"] = "IDENTIFIER_PLUS_EQUITY_SEMANTICS"
            elif m["has_share"] or m["has_equity"]:
                row["Official_Semantics_Strength_v0_25"] = "EQUITY_SEMANTICS_ONLY"
            else:
                row["Official_Semantics_Strength_v0_25"] = "CAPABILITY_ONLY"
            row["Materialization_Status_v0_25"] = "RAW_OFFICIAL_PAGE_SAVED"
        else:
            row["Materialization_Status_v0_25"] = "RAW_OFFICIAL_BINARY_SAVED"

        if spec.get("parser") == "HKEX_LIST_XLSX":
            xls = pd.ExcelFile(raw)
            sheet = xls.sheet_names[0]
            df = pd.read_excel(raw, sheet_name=sheet, dtype=str, keep_default_na=False)
            cols = [str(c).strip() for c in df.columns]
            row["Workbook_Sheet"] = sheet
            row["Workbook_Rows"] = len(df)
            row["Workbook_Columns"] = ";".join(cols)
            cat = next((c for c in df.columns if str(c).strip().lower() == "category"), None)
            sub = next((c for c in df.columns if "sub-category" in str(c).strip().lower()), None)
            isin = next((c for c in df.columns if str(c).strip().lower() == "isin"), None)
            if cat is not None and sub is not None and isin is not None:
                row["Official_Semantics_Strength_v0_25"] = "BULK_IDENTIFIER_PLUS_CATEGORY_SUBCATEGORY"
                row["Materialization_Status_v0_25"] = "PARSED_OFFICIAL_BULK_REFERENCE"
            else:
                row["Materialization_Status_v0_25"] = "PARSED_BUT_REQUIRED_FIELDS_NOT_FOUND"
    except Exception as e:
        row["Error"] = f"{type(e).__name__}: {e}"
    return row, links_out

def run(cfg_path):
    start = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw_official_probe"
    raw_dir.mkdir(exist_ok=True)

    paths = {k: Path(v) for k,v in cfg["inputs"].items()}
    s24 = read_json(paths["v024_summary"])
    c24 = read_json(paths["v024_checkpoint"])
    routes24 = read_csv(paths["v024_global_routes"])
    eu24 = read_csv(paths["v024_eu_routes"])
    data24 = read_csv(paths["v024_data_reconciliation"])
    policy24 = read_json(paths["v024_bounded_policy"])
    unresolved23 = read_csv(paths["v023_instrument_unresolved"])

    require(s24["run_status"] == "EU_INSTRUMENT_BULK_EVIDENCE_GLOBAL_REMEDIATION_DESIGN_V0_24_COMPLETE", "Bad v0.24 summary")
    require(c24["status"] == "SUCCESS", "v0.24 checkpoint not SUCCESS")
    require(c24["next_stage"] == "OFFICIAL_BULK_SECURITY_TYPE_PROBE_AND_DATA_GAP_RECHECK", "Bad v0.24 next stage")
    require(s24["instrument_unresolved_rows"] == 650, "Bad unresolved denominator")
    require(len(routes24) == 5 and routes24["Rows"].astype(int).sum() == 650, "Bad route denominator")
    require(len(eu24) == 18 and eu24["Rows"].astype(int).sum() == 365, "Bad EU denominator")
    require(len(data24) == 60, "Bad data-gap denominator")
    require(len(unresolved23) == 650, "Bad unresolved source denominator")
    require(s24["p0_run"] is False and s24["productive_trading_authority"] is False, "Authority gate failed")
    require(s24["alpha_vantage_allowed"] is False, "Alpha gate failed")
    require(policy24["per_security_web_fanout_allowed"] is False, "Fanout policy mismatch")

    actual_mics = {str(r["Primary_MIC"]): int(r["Rows"]) for _,r in eu24.iterrows()}
    require(actual_mics == cfg["expected_counts"]["eu_mic_rows"], f"EU MIC rows changed: {actual_mics}")

    probe_rows, all_links = [], []
    for spec in cfg["source_probes"]:
        row, links = probe(spec, cfg, raw_dir)
        probe_rows.append(row)
        all_links.extend(links)
    probes = pd.DataFrame(probe_rows)
    probes.to_csv(out/"official_source_probe_status_v0.25.csv", index=False)
    pd.DataFrame(all_links, columns=["Source_ID","Coverage_Route","Candidate_URL","Candidate_Host","Followed_In_v0_25"]).to_csv(
        out/"official_candidate_links_v0.25.csv", index=False
    )

    configured = set()
    source_by_mic = {}
    for spec in cfg["source_probes"]:
        if spec["coverage_route"] == "EU_PRIMARY_EXCHANGES":
            for mic in spec.get("primary_mics", []):
                configured.add(mic)
                source_by_mic.setdefault(mic, []).append(spec["source_id"])
    eu_map = eu24.copy()
    eu_map["Configured_Official_Probe_v0_25"] = eu_map["Primary_MIC"].isin(configured)
    eu_map["Configured_Source_IDs_v0_25"] = eu_map["Primary_MIC"].map(lambda m: ";".join(source_by_mic.get(m, [])))
    eu_map["Instrument_Decision_v0_25"] = "UNCHANGED_NOT_VERIFIED"
    eu_map["Per_Security_Fanout_Used_v0_25"] = False
    eu_map.to_csv(out/"eu_official_probe_route_coverage_v0.25.csv", index=False)

    route_to_segment = {
        "EU_PRIMARY_EXCHANGES":"EU_STOXX600",
        "HK_HSI":"HK_HSI","CA_TSX":"CA_TSX","KR_KOSPI200":"KR_KOSPI200","MX_IPC":"MX_IPC"
    }
    pseg = []
    for _,r in probes.iterrows():
        pseg.append({
            "Primary_Universe_Index": route_to_segment[r["Coverage_Route"]],
            "Source_ID": r["Source_ID"],
            "Probe_Status": r["Probe_Status"],
            "Materialization_Status_v0_25": r["Materialization_Status_v0_25"],
            "Official_Semantics_Strength_v0_25": r["Official_Semantics_Strength_v0_25"],
        })
    pseg = pd.DataFrame(pseg)
    stats = pseg.groupby("Primary_Universe_Index").agg(
        Source_Probe_Count_v0_25=("Source_ID","size"),
        HTTP_OK_Count_v0_25=("Probe_Status", lambda x: int((x=="HTTP_OK").sum())),
        Parsed_Official_Bulk_Count_v0_25=("Materialization_Status_v0_25", lambda x: int((x=="PARSED_OFFICIAL_BULK_REFERENCE").sum())),
    ).reset_index()
    gs = routes24.merge(stats, on="Primary_Universe_Index", how="left")
    for c in ["Source_Probe_Count_v0_25","HTTP_OK_Count_v0_25","Parsed_Official_Bulk_Count_v0_25"]:
        gs[c] = gs[c].fillna(0).astype(int)
    gs["Instrument_Decision_Changes_v0_25"] = 0
    gs["Automatic_PASS_Allowed_v0_25"] = False
    gs["Next_State_v0_25"] = gs["HTTP_OK_Count_v0_25"].map(
        lambda n: "OFFICIAL_BULK_MATERIALIZATION_OR_SEMANTICS_VALIDATION_REQUIRED"
        if int(n) > 0 else "OFFICIAL_SOURCE_PROBE_BLOCKED_OR_NOT_CONFIGURED"
    )
    gs.to_csv(out/"global_instrument_probe_state_v0.25.csv", index=False)

    data = data24.copy()
    require(data["WS_ID"].duplicated().sum() == 0, "Duplicate data-gap WS_ID")
    hist = data["Remediation_Class_v0_23"].eq("DATA_HISTORY_REMEDIATION_CANDIDATE")
    fx = data["Remediation_Class_v0_23"].eq("DATA_OR_FX_VERIFICATION_CANDIDATE")
    require(int(hist.sum()) == 55 and int(fx.sum()) == 5, "Unexpected data-gap classes")
    data["Recheck_Mode_v0_25"] = "FROZEN_REPOSITORY_EVIDENCE_ONLY_NO_PRICE_OR_FX_DOWNLOAD"
    data["Data_Gap_State_v0_25"] = data["Remediation_Class_v0_23"].map({
        "DATA_HISTORY_REMEDIATION_CANDIDATE":"STILL_REQUIRES_TARGETED_HISTORY_REPAIR_OR_REQUALIFICATION",
        "DATA_OR_FX_VERIFICATION_CANDIDATE":"STILL_REQUIRES_LIQUIDITY_DATA_OR_FX_RECOMPUTE",
    })
    data["Automatic_Eligibility_Promotion_v0_25"] = False
    data.to_csv(out/"data_gap_recheck_v0.25.csv", index=False)
    data.groupby(
        ["Primary_Universe_Index","Remediation_Class_v0_23","Data_Gap_State_v0_25"], dropna=False
    ).size().reset_index(name="Rows").sort_values(
        ["Rows","Primary_Universe_Index"], ascending=[False,True], kind="mergesort"
    ).to_csv(out/"data_gap_recheck_counts_v0.25.csv", index=False)

    follow = []
    for _,r in probes.iterrows():
        if r["Probe_Status"] != "HTTP_OK":
            action = "REVIEW_OFFICIAL_ROUTE_OR_TRANSPORT_WITHOUT_PER_SECURITY_FANOUT"
        elif r["Materialization_Status_v0_25"] == "PARSED_OFFICIAL_BULK_REFERENCE":
            action = "VALIDATE_OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_DETERMINISTIC_MATCHING"
        elif int(r.get("Candidate_Link_Count", 0) or 0) > 0:
            action = "REVIEW_DISCOVERED_OFFICIAL_BULK_CANDIDATES_THEN_MATERIALIZE_BOUNDED_SOURCE"
        else:
            action = "SOURCE_CAPABILITY_ONLY_FIND_MACHINE_READABLE_OR_EXPLICIT_SECURITY_TYPE_ROUTE"
        follow.append({
            "Source_ID":r["Source_ID"],"Coverage_Route":r["Coverage_Route"],
            "Probe_Status":r["Probe_Status"],"Materialization_Status_v0_25":r["Materialization_Status_v0_25"],
            "Candidate_Link_Count":r.get("Candidate_Link_Count",0),
            "Recommended_Next_Action_v0_25":action,
            "May_Change_Instrument_Decisions_In_v0_25":False,
        })
    pd.DataFrame(follow).to_csv(out/"source_materialization_followup_v0.25.csv", index=False)

    n = len(cfg["source_probes"])
    ok = int((probes["Probe_Status"]=="HTTP_OK").sum())
    err = n-ok
    parsed = int((probes["Materialization_Status_v0_25"]=="PARSED_OFFICIAL_BULK_REFERENCE").sum())
    stage_status = "SUCCESS" if err == 0 else "PARTIAL"

    summary = {
        "schema":SCHEMA,
        "generated_utc":now_utc(),
        "run_status":"OFFICIAL_BULK_SECURITY_TYPE_PROBE_DATA_GAP_RECHECK_V0_25_COMPLETE" if err==0
                     else "OFFICIAL_BULK_SECURITY_TYPE_PROBE_DATA_GAP_RECHECK_V0_25_COMPLETE_WITH_SOURCE_PROBE_ERRORS",
        "stage_status":stage_status,
        "instrument_unresolved_rows":650,
        "instrument_unresolved_by_segment":{str(k):int(v) for k,v in unresolved23["Primary_Universe_Index"].value_counts().sort_index().to_dict().items()},
        "eu_unresolved_rows":365,
        "eu_route_buckets":18,
        "eu_configured_probe_route_rows":int(eu_map.loc[eu_map["Configured_Official_Probe_v0_25"],"Rows"].astype(int).sum()),
        "eu_unconfigured_probe_route_rows":int(eu_map.loc[~eu_map["Configured_Official_Probe_v0_25"],"Rows"].astype(int).sum()),
        "official_source_probe_count":n,
        "official_source_http_ok_count":ok,
        "official_source_probe_error_count":err,
        "parsed_official_bulk_reference_count":parsed,
        "candidate_link_count":len(all_links),
        "data_gap_rows_rechecked":60,
        "data_history_rows":55,
        "data_or_fx_rows":5,
        "data_gap_rows_automatically_promoted":0,
        "instrument_decisions_changed":0,
        "eligibility_promotions_made":0,
        "p0_run":False,
        "p0_lane_decisions_made":False,
        "p0_survivor_rows":0,
        "sector_rs_performed":False,
        "price_downloads_performed":False,
        "fx_downloads_performed":False,
        "external_requests":n,
        "web_calls_per_security":False,
        "alpha_vantage_allowed":False,
        "productive_trading_authority":False,
        "canonical_master_mutated":False,
        "historical_artifacts_mutated":False,
        "coverage_gate_status":"BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "next_stage":"OFFICIAL_SOURCE_MATERIALIZATION_AND_DATA_GAP_REPAIR",
        "required_result_wording":"bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording":"weltweit bester Kandidat",
    }
    (out/"summary_v0.25.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")

    input_hashes={k:sha256_file(v) for k,v in paths.items()}
    parameter_hash=sha256_file(cfg_path)
    evidence=[out/"official_source_probe_status_v0.25.csv",out/"official_candidate_links_v0.25.csv",
              out/"eu_official_probe_route_coverage_v0.25.csv",out/"global_instrument_probe_state_v0.25.csv",
              out/"data_gap_recheck_v0.25.csv",out/"data_gap_recheck_counts_v0.25.csv",
              out/"source_materialization_followup_v0.25.csv",out/"summary_v0.25.json"]
    raw_files=sorted([p for p in raw_dir.iterdir() if p.is_file()])
    output_hash=combined_hash({str(p.relative_to(out)):sha256_file(p) for p in evidence+raw_files})
    failed=probes.loc[probes["Probe_Status"]!="HTTP_OK","Source_ID"].astype(str).tolist()
    checkpoint={
        "schema":"WELT_SWING_STAGE_CHECKPOINT_V0_25",
        "run_id":cfg["run_id"],
        "stage_id":"OFFICIAL_BULK_SECURITY_TYPE_PROBE_AND_DATA_GAP_RECHECK",
        "stage_version":"v0.25",
        "start":start,"end":now_utc(),
        "input_hash":combined_hash(input_hashes),
        "parameter_hash":parameter_hash,
        "output_hash":output_hash,
        "input_count":710,"checked_count":710,"pass_count":710,"fail_count":0,
        "data_error_count":0,"quarantine_count":0,
        "status":stage_status,
        "failed_source":";".join(failed) if failed else None,
        "source_probe_count":n,
        "source_probe_http_ok_count":ok,
        "source_probe_error_count":err,
        "parsed_official_bulk_reference_count":parsed,
        "external_requests":n,
        "web_calls_per_security":False,
        "instrument_decisions_changed":0,
        "coverage_gate_status":"BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT",
        "next_stage":"OFFICIAL_SOURCE_MATERIALIZATION_AND_DATA_GAP_REPAIR",
    }
    cp=out/"stage_checkpoint_v0.25.json"
    cp.write_text(json.dumps(checkpoint,indent=2,ensure_ascii=False),encoding="utf-8")

    manifest_files=evidence+raw_files+[cp]
    manifest={
        "schema":"WELT_SWING_OFFICIAL_BULK_SECURITY_TYPE_PROBE_DATA_GAP_RECHECK_MANIFEST_V0_25",
        "generated_utc":now_utc(),
        "input_hash":checkpoint["input_hash"],"parameter_hash":parameter_hash,"evidence_output_hash":output_hash,
        "external_requests":n,"web_calls_per_security":False,"alpha_vantage_allowed":False,
        "files":{str(p.relative_to(out)):{"sha256":sha256_file(p),"bytes":p.stat().st_size} for p in manifest_files},
    }
    (out/"manifest_v0.25.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print("OFFICIAL_BULK_SECURITY_TYPE_PROBE_DATA_GAP_RECHECK_V0_25_RESULT_GATES_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config/official_bulk_security_type_probe_data_gap_recheck_v0.25.json")
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:
        self_test()
    else:
        run(Path(a.config))

if __name__=="__main__":
    main()
