#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path

VERSION="v0.76"
STAGE="US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE_GATE_WITH_IN_NIFTY50_PARK"
REQUIRED_START_HEAD="40f261b29dd0e92dc79b976a0970f6ae8970e9e8"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_us_sp400_sec_identity_linkage_v0_76")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.76.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.76.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.76.csv")
    target=readcsv(out/"us_sp400_frozen_368_identity_target_v0.76.csv")
    links=readcsv(out/"us_sp400_exact_368_identity_linkage_v0.76.csv")
    micmap=readcsv(out/"sec_exchange_to_mic_mapping_v0.76.csv")
    park=readcsv(out/"parked_cohort_registry_v0.76.csv")
    calc=readcsv(out/"post_park_next_cohort_selection_calculation_v0.76.csv")
    prov=json.loads((out/"provider_call_audit_v0.76.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.76.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(target)!=368 or len(links)!=368:raise RuntimeError("target/link rows")
    if len({r["WS_ID"] for r in target})!=368 or len({r["Security_Key"] for r in target})!=368:raise RuntimeError("target uniqueness")
    if len(park)!=1 or park[0]["Cohort"]!="IN_NIFTY50" or park[0]["Execution_State"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("park state")
    if park[0]["Gate_F_Classified"]!="45" or park[0]["Canonical_Rows"]!="0":raise RuntimeError("park counts")
    if pre["selected_cohort"]!="US_SP400" or pre["in_nifty50_park_state"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("selection/park")
    if pre["in_gate_f_classified"]!=45 or pre["in_canonical_rows"]!=0:raise RuntimeError("IN state")
    if pre["canonical_ready_rows"]!=37 or pre["canonical_total_rows"]!=1425:raise RuntimeError("canonical state")
    if pre["us_gate_f_runs"]!=0 or pre["canonical_materialization_runs"]!=0 or pre["us_sp500_runs"]!=0 or pre["other_cohort_runs"]!=0:raise RuntimeError("out of scope")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("downstream")
    if pre["us_sp400_deterministic_sec_identity_ready"]:
        if pre["verdict"]!="PASS_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE":raise RuntimeError("success verdict")
        if (pre["linked"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(368,368,0,0,0,0):raise RuntimeError("success counts")
        if any(r["Gate_E_Status"]!="PROVABLY_LINKED" for r in links):raise RuntimeError("success linkage rows")
        if not micmap or any(r["Mapping_Status"]!="PASS" for r in micmap):raise RuntimeError("MIC mapping")
        if pre["blocker"]!="" or pre["next_gate"]!="US_SP400 EXACT FROZEN SEC SIC CLASSIFICATION COVERAGE GATE":raise RuntimeError("success next/blocker")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")

    # Persist central park registry as a governance sidecar, never the canonical sector registry.
    park_path=Path("sector_metadata/governance/parked_cohort_registry_v1.csv")
    park_path.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(out/"parked_cohort_registry_v0.76.csv",park_path)

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.76 IN_NIFTY50 park governance plus US_SP400 deterministic SEC ticker/exchange-to-MIC identity linkage evidence"
    }
    (out/"artifact_binding_v0.76.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    summary["park_registry_path"]=str(park_path);summary["park_registry_sha256"]=sha(park_path)
    (out/"summary_v0.76.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.76.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/US_SP400_Deterministic_SEC_Security_Identity_Linkage_Gate_v0.76.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["us_sp400_deterministic_sec_identity_ready"] else "NO"
    report.write_text("\n".join([
      "# US_SP400 Deterministic SEC Security Identity Linkage Gate + IN_NIFTY50 Park v0.76","",
      "## Governance",
      "G-SEC-06 parks IN_NIFTY50 as PARKED_EXTERNAL_AUTHORIZATION. Its proven technical gates A-G and Gate-F 45/45 remain unchanged; Gate H remains blocked by EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION. Parking creates no canonical rows and excludes IN_NIFTY50 from automatic next-cohort selection.","",
      "Applying the persisted v0.69 deterministic selection rule after excluding BR_IBRX100 (canonical READY) and IN_NIFTY50 (parked) selects US_SP400. US_SP400 and US_SP500 both have four consecutive resolved gates A-D, and 368 rows wins the row-count tie-break against 372.","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"US_SP400_DETERMINISTIC_SEC_IDENTITY_READY = **{ready}**.",
      f"LINKED / TOTAL = **{pre['linked']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"CONFLICT = **{pre['conflict']}**.","",
      "## Identity route",pre["sec_identity_route"],"",
      "The SEC ticker/exchange file URL is discovered from official SEC EDGAR documentation. Exchange-to-MIC authority is taken only from the official ISO 10383 MIC dataset discovered from the ISO 20022 MIC landing page. The join never uses company names or fuzzy matching; CIK is retained as issuer-reference evidence and share classes are not collapsed.","",
      "## Exchange-to-MIC authority",pre["exchange_mic_authority"],"",
      "## SEC fair access",
      "SEC requests use a descriptive project User-Agent/contact URL, bounded bulk requests, no per-security fanout, and no polling or throttling bypass. Request URLs, statuses, hashes, and timestamps are persisted in the external request ledger.","",
      "## Scope boundary",
      "No US Gate F, SIC promotion, canonical materialization, US_SP500 execution, other cohort execution, NSE request, Sector RS, P0/P1/P2, price/news/trading analysis, or forbidden provider call occurred.","",
      "## Immutability",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.",
      "- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.",
      "- IN Gate-F remains 45/45; IN canonical rows remain 0.",
      "- Global canonical READY remains 37/1425.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no US Gate F, canonical metadata materialization, US_SP500 execution, Sector RS, or P0."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.76.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    files[str(park_path)]={"sha256":sha(park_path),"bytes":park_path.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","selected_cohort":"US_SP400",
      "us_sp400_deterministic_sec_identity_ready":pre["us_sp400_deterministic_sec_identity_ready"],
      "linked":pre["linked"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"sec_identity_route":pre["sec_identity_route"],
      "exchange_mic_authority":pre["exchange_mic_authority"],"blocker":pre["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "park_registry_path":str(park_path),"park_registry_sha256":sha(park_path),
      "in_gate_f_classified":45,"in_canonical_rows":0,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "us_gate_f_runs":0,"canonical_materialization_runs":0,"us_sp500_runs":0,"other_cohort_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.76.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","selected_cohort":"US_SP400",
      "ready":pre["us_sp400_deterministic_sec_identity_ready"],"linked":pre["linked"],"total":pre["total"],
      "ambiguous":pre["ambiguous"],"not_found":pre["not_found"],"not_verified":pre["not_verified"],"conflict":pre["conflict"],
      "sec_identity_route":pre["sec_identity_route"],"exchange_mic_authority":pre["exchange_mic_authority"],
      "blocker":pre["blocker"],"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
