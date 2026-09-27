#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path

VERSION="v0.78"
STAGE="SHARED_SEC_SOURCE_ACCESS_PARKING_POST_PARK_RESELECTION_JP_N225_GATE_D"
REQUIRED_START_HEAD="c567c86f08ffd0b98aea83f0f01246335b7b9443"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def writecsv(p:Path,rows:list[dict]):
    p.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0].keys())
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_shared_sec_park_jp_n225_gate_d_v0_78")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.78.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.78.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.78.csv")
    shared=readcsv(out/"shared_source_dependency_registry_v0.78.csv")
    selection=readcsv(out/"post_shared_park_next_cohort_selection_calculation_v0.78.csv")
    decision=json.loads((out/"jp_canonical_classification_level_decision_v0.78.json").read_text(encoding="utf-8"))
    pdsc=readcsv(out/"jp_pdsc_distinct_label_feasibility_audit_v0.78.csv")
    collisions=readcsv(out/"jp_pdsc_collision_audit_v0.78.csv")
    prov=json.loads((out/"provider_call_audit_v0.78.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.78.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(shared)!=2:raise RuntimeError("shared dependency rows")
    by={r["Affected_Cohort"]:r for r in shared}
    if by["US_SP400"]["Execution_State"]!="PARKED_SOURCE_ACCESS" or by["US_SP400"]["Gate_E"]!="NOT_VERIFIED":raise RuntimeError("SP400 park")
    if by["US_SP500"]["Execution_State"]!="PARKED_SHARED_SOURCE_PREREQUISITE" or by["US_SP500"]["Gate_E"]!="NOT_VERIFIED":raise RuntimeError("SP500 park")
    if by["US_SP500"]["Row_Level_Gate_E_Executed"]!="NO" or by["US_SP500"]["Row_Level_Result_Authority"]!="NONE_CREATED":raise RuntimeError("SP500 row fabrication")
    if pre["selected_cohort"]!="JP_N225":raise RuntimeError("selection")
    if pre["in_nifty50_park_state"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("IN park")
    if pre["canonical_ready_rows"]!=37 or pre["canonical_total_rows"]!=1425:raise RuntimeError("canonical state")
    if pre["sec_requests"]!=0 or pre["us_sp500_row_level_results_created"]!=0:raise RuntimeError("shared park scope")
    if pre["jp_gate_e_runs"]!=0 or pre["jp_gate_f_runs"]!=0 or pre["canonical_materialization_runs"]!=0:raise RuntimeError("JP downstream")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("downstream")

    if pre["jp_canonical_classification_level_ready"]:
        if pre["verdict"]!="PASS_JP_N225_CANONICAL_CLASSIFICATION_LEVEL_GATE_D":raise RuntimeError("success verdict")
        if pre["taxonomy"]!="NIKKEI_36_INDUSTRY_AND_SECTOR" or pre["selected_classification_level"]!="SECTOR" or pre["official_level_name"]!="Sector":raise RuntimeError("success level")
        if pre["native_code_available"]!="NO" or pre["pdsc_required"]!="YES":raise RuntimeError("success code path")
        if pre["distinct_labels"]!=6 or pre["pdsc_collisions"]!=0:raise RuntimeError("PDSC success")
        if not decision["JP_CANONICAL_CLASSIFICATION_LEVEL_READY"] or decision["Gate_D_After"]!="PASS_BY_CURRENT_GOVERNANCE":raise RuntimeError("decision")
        if len(pdsc)!=6 or any(r["Deterministic"]!="YES" for r in pdsc):raise RuntimeError("PDSC rows")
        if len(collisions)!=1 or collisions[0]["Collision_Count"]!="0":raise RuntimeError("collision audit")
        if pre["blocker"]!="" or pre["next_gate"]!="JP_N225 EXACT FROZEN SECTOR CLASSIFICATION COVERAGE GATE":raise RuntimeError("success next")
    else:
        if not pre["blocker"]:raise RuntimeError("blocked without blocker")

    # Central governance sidecars. Preserve the IN_NIFTY50 row fields exactly and append only G-SEC-07 U.S. parking rows.
    park_path=Path("sector_metadata/governance/parked_cohort_registry_v1.csv")
    old=readcsv(park_path)
    if len(old)!=1 or old[0]["Cohort"]!="IN_NIFTY50" or old[0]["Execution_State"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("park predecessor")
    fields=list(old[0].keys())
    us_rows=[
      {
        "Cohort":"US_SP400","Execution_State":"PARKED_SOURCE_ACCESS",
        "Technical_Gates_A_G":"A-D PASS; E NOT_VERIFIED; F NOT_EVALUATED; G PASS",
        "Gate_H":"NOT_EVALUATED","Gate_H_Blocker":"","Gate_F_Classified":"NOT_EXECUTED","Gate_F_Total":"368",
        "Canonical_Readiness":"NO","Canonical_Rows":"0","Reopen_Automatically":"NO","Authority":"G-SEC-07","Effective_From":"v0.78"
      },
      {
        "Cohort":"US_SP500","Execution_State":"PARKED_SHARED_SOURCE_PREREQUISITE",
        "Technical_Gates_A_G":"A-D PASS; E NOT_VERIFIED; F NOT_EVALUATED; G PASS",
        "Gate_H":"NOT_EVALUATED","Gate_H_Blocker":"","Gate_F_Classified":"NOT_EXECUTED","Gate_F_Total":"372",
        "Canonical_Readiness":"NO","Canonical_Rows":"0","Reopen_Automatically":"NO","Authority":"G-SEC-07","Effective_From":"v0.78"
      }
    ]
    # Ensure columns remain exactly the predecessor schema.
    for r in us_rows:
        if set(r)!=set(fields):raise RuntimeError("park schema mismatch")
    writecsv(park_path,[old[0],*us_rows])

    shared_path=Path("sector_metadata/governance/shared_source_dependency_registry_v1.csv")
    shutil.copyfile(out/"shared_source_dependency_registry_v0.78.csv",shared_path)

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.78 shared SEC dependency parking, deterministic post-park reselection, and JP_N225 Gate-D official hierarchy/PDSC-feasibility evidence"
    }
    (out/"artifact_binding_v0.78.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    summary["parked_cohort_registry_path"]=str(park_path);summary["parked_cohort_registry_sha256"]=sha(park_path)
    summary["shared_source_dependency_registry_path"]=str(shared_path);summary["shared_source_dependency_registry_sha256"]=sha(shared_path)
    (out/"summary_v0.78.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.78.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/Shared_SEC_Parking_Post_Park_Reselection_JP_N225_Gate_D_v0.78.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["jp_canonical_classification_level_ready"] else "NO"
    report.write_text("\n".join([
      "# Shared SEC Source-Access Parking / Post-Park Reselection / JP_N225 Gate-D v0.78","",
      "## Shared SEC dependency",
      "G-SEC-07 records the exact SEC company_tickers_exchange prerequisite as SHARED_SOURCE_ACCESS_BLOCKED. US_SP400 is PARKED_SOURCE_ACCESS with Gate E still NOT_VERIFIED and its v0.77 368 NOT_VERIFIED rows unchanged. US_SP500 is PARKED_SHARED_SOURCE_PREREQUISITE; its Gate E remains NOT_VERIFIED and no 372-row Gate-E execution or result set was created.","",
      "IN_NIFTY50 remains PARKED_EXTERNAL_AUTHORIZATION under G-SEC-06. Its Gate-F 45/45 authority and zero canonical rows are unchanged.","",
      "## Deterministic reselection",
      "After excluding BR_IBRX100 as canonical READY and the three parked cohorts, the v0.69 selection rule chooses JP_N225: it has three consecutive resolved gates A-C before unresolved D, versus AU_SP_ASX200 at two and CN_CSI300/TW_TW50 at one.","",
      "## JP_N225 official hierarchy",
      f"The bounded official Nikkei audit retrieved {pre['nikkei_component_security_count']} current component securities, {pre['nikkei_sector_count']} parent sectors and {pre['nikkei_industry_count']} Nikkei industrial classifications from the official component/profile/factsheet sources.",
      "The Nikkei 225 profile explicitly states that sector balance uses 6 sector categories consolidated from the 36 Nikkei industrial classifications. The component page independently reproduces the parent Sector -> Industry -> security structure. This supplies a structural hierarchy rather than semantic label inference.","",
      "## Gate-D decision",f"**{pre['verdict']}**","",
      f"JP_CANONICAL_CLASSIFICATION_LEVEL_READY = **{ready}**.",
      f"TAXONOMY = **{pre['taxonomy']}**.",
      f"SELECTED CLASSIFICATION LEVEL = **{pre['selected_classification_level']}**.",
      f"OFFICIAL LEVEL NAME = **{pre['official_level_name']}**.",
      f"NATIVE CODE AVAILABLE = **{pre['native_code_available']}**.",
      f"PDSC REQUIRED = **{pre['pdsc_required']}**.",
      f"DISTINCT LABELS = **{pre['distinct_labels']}**.",
      f"PDSC COLLISIONS = **{pre['pdsc_collisions']}**.","",
      "The selected canonical peer-group level is the official six-category Sector parent level because Nikkei itself designates those groups for Nikkei 225 sector balance and defines them as consolidations of the 36 child industrial classifications. The decision is not based merely on the English word 'Sector'. The child Industry level remains preserved as an official finer classification but is not mixed into the canonical peer level.","",
      "No source-native Sector classification code semantics were found in the bounded current official sources, consistent with v0.62. Security codes and HTML anchor fragments are not treated as classification codes. G-SEC-03 therefore permits PDSC_SHA256_V1 only after the exact SECTOR level/name binding; v0.78 tests only the six distinct current Sector labels, twice independently, with no row population.","",
      "## Scope boundary",
      "No SEC request, US row-level Gate-E execution, NSE request, JP Gate E, JP Gate F, Frozen-197 classification coverage, canonical materialization, other-cohort research, Sector RS, or P0/P1/P2 occurred.","",
      "## Immutability",
      "- Frozen SHA remains 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 and v0.58 semantic authorities remain unchanged.",
      "- BR canonical semantic SHA remains bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.",
      "- IN Gate F remains 45/45; global canonical READY remains 37/1425.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no JP Gate F, US requests, canonical materialization, next-cohort execution, Sector RS, or P0."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.78.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    files[str(park_path)]={"sha256":sha(park_path),"bytes":park_path.stat().st_size}
    files[str(shared_path)]={"sha256":sha(shared_path),"bytes":shared_path.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "in_nifty50_park_state":pre["in_nifty50_park_state"],"us_sp400_park_state":pre["us_sp400_park_state"],
      "us_sp500_park_state":pre["us_sp500_park_state"],"selected_cohort":"JP_N225",
      "jp_canonical_classification_level_ready":pre["jp_canonical_classification_level_ready"],
      "taxonomy":pre["taxonomy"],"selected_classification_level":pre["selected_classification_level"],
      "official_level_name":pre["official_level_name"],"native_code_available":pre["native_code_available"],
      "pdsc_required":pre["pdsc_required"],"distinct_labels":pre["distinct_labels"],"pdsc_collisions":pre["pdsc_collisions"],
      "blocker":pre["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "parked_cohort_registry_path":str(park_path),"parked_cohort_registry_sha256":sha(park_path),
      "shared_source_dependency_registry_path":str(shared_path),"shared_source_dependency_registry_sha256":sha(shared_path),
      "canonical_ready_rows":37,"canonical_total_rows":1425,"jp_gate_e_runs":0,"jp_gate_f_runs":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.78.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"in_nifty50_park_state":pre["in_nifty50_park_state"],
      "us_sp400_park_state":pre["us_sp400_park_state"],"us_sp500_park_state":pre["us_sp500_park_state"],
      "selected_cohort":"JP_N225","ready":pre["jp_canonical_classification_level_ready"],
      "taxonomy":pre["taxonomy"],"selected_classification_level":pre["selected_classification_level"],
      "official_level_name":pre["official_level_name"],"native_code_available":pre["native_code_available"],
      "pdsc_required":pre["pdsc_required"],"distinct_labels":pre["distinct_labels"],
      "pdsc_collisions":pre["pdsc_collisions"],"blocker":pre["blocker"],
      "workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
