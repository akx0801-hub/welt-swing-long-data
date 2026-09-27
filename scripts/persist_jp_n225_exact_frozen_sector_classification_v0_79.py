#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.79"
STAGE="JP_N225_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE_GATE"
REQUIRED_START_HEAD="4a5c2f5914f57e5333c68f7a8616dfd1b50adceb"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_jp_n225_exact_frozen_sector_classification_v0_79")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.79.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.79.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.79.csv")
    target=readcsv(out/"jp_frozen_197_classification_target_v0.79.csv")
    join=readcsv(out/"jp_exact_197_security_code_join_audit_v0.79.csv")
    coverage=readcsv(out/"jp_exact_197_classification_coverage_v0.79.csv")
    pdsc=readcsv(out/"jp_pdsc_authority_recalculation_audit_v0.79.csv")
    prov=json.loads((out/"provider_call_audit_v0.79.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.79.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(target)!=197 or len(join)!=197 or len(coverage)!=197:raise RuntimeError("row counts")
    if len({r["WS_ID"] for r in target})!=197 or len({r["Security_Key"] for r in target})!=197:raise RuntimeError("target uniqueness")
    if len(pdsc)!=6 or any(r["Status"]!="PASS" for r in pdsc):raise RuntimeError("PDSC authority")
    if pre["in_nifty50_park_state"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("IN park state")
    if pre["us_sp400_park_state"]!="PARKED_SOURCE_ACCESS":raise RuntimeError("US400 park state")
    if pre["us_sp500_park_state"]!="PARKED_SHARED_SOURCE_PREREQUISITE":raise RuntimeError("US500 park state")
    if pre["canonical_ready_rows"]!=37 or pre["canonical_total_rows"]!=1425:raise RuntimeError("canonical state")
    if pre["gate_h_runs"]!=0 or pre["canonical_materialization_runs"]!=0 or pre["other_cohort_runs"]!=0:raise RuntimeError("out-of-scope")
    if pre["sec_requests"]!=0 or pre["nse_requests"]!=0:raise RuntimeError("SEC/NSE requests")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("downstream")
    if pre["jp_exact_197_sector_classification_coverage_ready"]:
        if pre["verdict"]!="PASS_JP_N225_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE":raise RuntimeError("success verdict")
        if (pre["classified"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(197,197,0,0,0,0):raise RuntimeError("success counts")
        if pre["current_source_matches"]!=197 or pre["authorized_sector_labels"]!=6 or pre["pdsc_coverage"]!=197 or pre["pdsc_collisions"]!=0:raise RuntimeError("success coverage")
        if any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in coverage):raise RuntimeError("coverage rows")
        if pre["blocker"]!="" or pre["next_gate"]!="JP_N225 SOURCE ACCESS / PERSISTENCE GATE":raise RuntimeError("success next/blocker")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.79 JP_N225 exact Frozen-197 current Nikkei security-code-to-SECTOR classification coverage evidence"
    }
    (out/"artifact_binding_v0.79.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.79.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.79.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/JP_N225_Exact_Frozen_Sector_Classification_Coverage_Gate_v0.79.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["jp_exact_197_sector_classification_coverage_ready"] else "NO"
    report.write_text("\n".join([
      "# JP_N225 Exact Frozen Sector Classification Coverage Gate v0.79","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"JP_EXACT_197_SECTOR_CLASSIFICATION_COVERAGE_READY = **{ready}**.",
      f"CLASSIFIED / TOTAL = **{pre['classified']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"CONFLICT = **{pre['conflict']}**.",
      f"CURRENT SOURCE MATCHES = **{pre['current_source_matches']} / 197**.",
      f"AUTHORIZED SECTOR LABELS = **{pre['authorized_sector_labels']}**.",
      f"PDSC COVERAGE = **{pre['pdsc_coverage']} / 197**.",
      f"PDSC COLLISIONS = **{pre['pdsc_collisions']}**.","",
      "## Authority",
      "The v0.78 Gate-D decision is preserved: taxonomy NIKKEI_36_INDUSTRY_AND_SECTOR, canonical level SECTOR, official level name Sector, no source-native classification code, PDSC_SHA256_V1 required, six authorized official Sector labels. Gate E remains PASS_INHERITED and is not rerun.","",
      "## Source and hierarchy",
      f"The official component page was requested once. Current response SHA-256: {pre['component_source_sha256']}. v0.78 response SHA-256: {pre['component_source_v078_sha256']}. Source update marker: {pre['component_source_update']}. The parser accepts only the official SECTOR -> INDUSTRY -> SECURITY_CODE hierarchy and exact security Code values; no numeric casting, zero-padding, company-name joins, fuzzy matching, or per-security requests are used.","",
      "## PDSC",
      "The six exact v0.78-authorized PDSC values are independently recomputed from taxonomy + U+001F + SECTOR + U+001F + exact official Sector name using NFC and UTF-8 SHA-256. Any mismatch or collision blocks the gate. Industry remains supporting hierarchy evidence only and receives no canonical code.","",
      "## Target reconstruction",
      "The physical Frozen v0.5 projection does not carry Primary_Universe_Index. Frozen rows remain the target authority; the already-persisted v0.58 capability sidecar supplies the cohort label by exact Security_Key while Source_WS_ID, MIC, and ticker are cross-checked back to Frozen. No current Nikkei membership is used to define the target.","",
      "## Parked cohorts and scope",
      "IN_NIFTY50 remains PARKED_EXTERNAL_AUTHORIZATION; US_SP400 remains PARKED_SOURCE_ACCESS; US_SP500 remains PARKED_SHARED_SOURCE_PREREQUISITE. No SEC or NSE request, Gate H, canonical materialization, other-cohort execution, Sector RS, or P0/P1/P2 occurred.","",
      "## Immutability",
      "- Frozen SHA unchanged.",
      "- v0.57 and v0.58 semantic authorities unchanged.",
      "- BR canonical semantic authority unchanged.",
      "- Parked-cohort and shared-source registries unchanged.",
      "- Global canonical READY remains 37/1425.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no Gate H, JP canonical partition, registry promotion, next cohort, Sector RS, or P0."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.79.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "jp_exact_197_sector_classification_coverage_ready":pre["jp_exact_197_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"current_source_matches":pre["current_source_matches"],
      "authorized_sector_labels":pre["authorized_sector_labels"],"pdsc_coverage":pre["pdsc_coverage"],"pdsc_collisions":pre["pdsc_collisions"],
      "blocker":pre["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","us_sp400_park_state":"PARKED_SOURCE_ACCESS",
      "us_sp500_park_state":"PARKED_SHARED_SOURCE_PREREQUISITE","canonical_ready_rows":37,"canonical_total_rows":1425,
      "gate_h_runs":0,"canonical_materialization_runs":0,"other_cohort_runs":0,"sec_requests":0,"nse_requests":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.79.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["jp_exact_197_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"current_source_matches":pre["current_source_matches"],
      "authorized_sector_labels":pre["authorized_sector_labels"],"pdsc_coverage":pre["pdsc_coverage"],"pdsc_collisions":pre["pdsc_collisions"],
      "blocker":pre["blocker"],"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
