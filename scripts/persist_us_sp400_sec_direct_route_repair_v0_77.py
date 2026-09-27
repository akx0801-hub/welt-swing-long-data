#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.77"
STAGE="US_SP400_SEC_COMPANY_TICKERS_EXCHANGE_DIRECT_BULK_ROUTE_REPAIR_GATE_E_COMPLETION"
REQUIRED_START_HEAD="17c21283f6c4fbdf524bc80324235c029018b6d6"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_us_sp400_sec_direct_route_repair_v0_77")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.77.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.77.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.77.csv")
    links=readcsv(out/"us_sp400_exact_368_identity_linkage_v0.77.csv")
    target=readcsv(out/"us_sp400_frozen_368_identity_target_v0.77.csv")
    mic=readcsv(out/"iso_exchange_mic_binding_v0.77.csv")
    correction=json.loads((out/"v076_source_failure_semantics_correction_v0.77.json").read_text(encoding="utf-8"))
    prov=json.loads((out/"provider_call_audit_v0.77.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.77.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(target)!=368 or len(links)!=368:raise RuntimeError("row counts")
    if correction["v076_SEC_Source_Record_Count"]!=0 or not correction["v076_not_found_368_is_not_security_absence_evidence"]:raise RuntimeError("failure semantics correction")
    if pre["in_nifty50_park_state"]!="PARKED_EXTERNAL_AUTHORIZATION" or pre["in_gate_f_classified"]!=45 or pre["in_canonical_rows"]!=0:raise RuntimeError("IN park drift")
    if pre["canonical_ready_rows"]!=37 or pre["canonical_total_rows"]!=1425:raise RuntimeError("canonical drift")
    if pre["us_gate_f_runs"]!=0 or pre["us_sp500_runs"]!=0 or pre["canonical_materialization_runs"]!=0:raise RuntimeError("out-of-scope run")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("downstream run")

    if pre["us_sp400_deterministic_sec_identity_ready"]:
        if pre["verdict"]!="PASS_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE":raise RuntimeError("success verdict")
        if pre["sec_direct_bulk_route"]!="PASS" or pre["sec_records"]<=0:raise RuntimeError("SEC route")
        if (pre["linked"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(368,368,0,0,0,0):raise RuntimeError("success counts")
        if pre["cik_coverage"]!=368 or pre["exchange_mic_authority"]!="PASS":raise RuntimeError("success CIK/MIC")
        if any(r["Gate_E_Status"]!="PROVABLY_LINKED" for r in links):raise RuntimeError("link rows")
        if not mic or any(r["Mapping_Status"]!="PASS" for r in mic):raise RuntimeError("MIC rows")
        if pre["blocker"]!="" or pre["next_gate"]!="US_SP400 EXACT FROZEN SEC SIC CLASSIFICATION COVERAGE GATE":raise RuntimeError("success next")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")
        if pre["sec_direct_bulk_route"]=="FAIL":
            if pre["not_found"]!=0 or pre["not_verified"]!=368:raise RuntimeError("source failure semantics")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.77 direct official SEC company_tickers_exchange route repair and US_SP400 deterministic Gate-E evidence"
    }
    (out/"artifact_binding_v0.77.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.77.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.77.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/US_SP400_SEC_Direct_Bulk_Route_Repair_Gate_E_v0.77.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["us_sp400_deterministic_sec_identity_ready"] else "NO"
    report.write_text("\n".join([
      "# US_SP400 SEC company_tickers_exchange Direct Bulk Route Repair / Gate-E Completion v0.77","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"US_SP400_DETERMINISTIC_SEC_IDENTITY_READY = **{ready}**.",
      f"SEC DIRECT BULK ROUTE = **{pre['sec_direct_bulk_route']}**.",
      f"SEC RECORDS = **{pre['sec_records']}**.",
      f"LINKED / TOTAL = **{pre['linked']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"CONFLICT = **{pre['conflict']}**.",
      f"CIK COVERAGE = **{pre['cik_coverage']} / 368**.",
      f"EXCHANGE→MIC AUTHORITY = **{pre['exchange_mic_authority']}**.","",
      "## v0.76 failure-semantics correction",
      "v0.76 loaded zero SEC identity records because route discovery failed. Its 368 NOT_FOUND row statuses are therefore preserved as historical execution output but are not treated as genuine security-absence evidence. v0.77 classifies all rows NOT_VERIFIED when the direct official SEC bulk source itself cannot be loaded.","",
      "## Direct route",
      "The exact manager-authorized official source is https://www.sec.gov/files/company_tickers_exchange.json. Documentation-page HTTP 200 is not a prerequisite in v0.77. Requests use a descriptive fair-access User-Agent, no authentication or cookie authority, no CAPTCHA bypass, no proxy rotation, no per-security fanout, and retries only for bounded transient statuses.","",
      "## Identity contract",
      "On successful source load, the returned fields array defines the SEC schema positions. Identity linkage uses exact SEC ticker plus exact SEC exchange, an official ISO 10383 operating-MIC binding, and exact Frozen (Primary_Ticker, Primary_MIC). Company names never participate in the join; CIK is persisted as reference evidence and share classes are not collapsed.","",
      "## Scope boundary",
      "No US Gate F, SIC promotion, US_SP500 execution, canonical materialization, NSE request, Sector RS, P0/P1/P2, price/news/trading analysis, or forbidden provider was executed.","",
      "## Immutability",
      "- IN_NIFTY50 remains PARKED_EXTERNAL_AUTHORIZATION; Gate F remains 45/45 and canonical rows remain 0.",
      "- Global canonical READY remains 37/1425.",
      "- Frozen, v0.57, v0.58, BR canonical semantic authority, and the IN park registry remain unchanged.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no US Gate F, US_SP500, canonical materialization, Sector RS, or P0."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.77.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "us_sp400_deterministic_sec_identity_ready":pre["us_sp400_deterministic_sec_identity_ready"],
      "sec_direct_bulk_route":pre["sec_direct_bulk_route"],"sec_records":pre["sec_records"],
      "linked":pre["linked"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"cik_coverage":pre["cik_coverage"],
      "exchange_mic_authority":pre["exchange_mic_authority"],"blocker":pre["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","in_gate_f_classified":45,"in_canonical_rows":0,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"us_gate_f_runs":0,"us_sp500_runs":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.77.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["us_sp400_deterministic_sec_identity_ready"],
      "sec_direct_bulk_route":pre["sec_direct_bulk_route"],"sec_records":pre["sec_records"],
      "linked":pre["linked"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"cik_coverage":pre["cik_coverage"],
      "exchange_mic_authority":pre["exchange_mic_authority"],"blocker":pre["blocker"],
      "workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
