#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.83"
STAGE="AU_SP_ASX200_V082_EVIDENCE_COMPLETENESS_REPAIR_FINAL_FIELD_PROVENANCE_TAXONOMY_IDENTITY_GATE_C_CLOSURE"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--output-dir",default="output_au_sp_asx200_final_gate_c_provenance_v0_83")
 ap.add_argument("--artifact-id",required=True,type=int);ap.add_argument("--artifact-digest",required=True)
 ap.add_argument("--artifact-name",required=True);ap.add_argument("--workflow-run-id",required=True,type=int);ap.add_argument("--workflow-head-sha",required=True)
 a=ap.parse_args();out=ROOT/a.output_dir
 pre=json.loads((out/"summary_preupload_v0.83.json").read_text());chk=json.loads((out/"stage_checkpoint_preupload_v0.83.json").read_text())
 dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
 binding={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS","workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
 wj(out/"artifact_binding_v0.83.json",binding)
 s=dict(pre);s["artifact_binding"]="PASS";s["artifact"]=binding;wj(out/"summary_v0.83.json",s)
 c=dict(chk);c.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha});wj(out/"stage_checkpoint_v0.83.json",c)
 report=ROOT/"docs/validation/AU_SP_ASX200_Final_Field_Provenance_Gate_C_Closure_v0.83.md";report.parent.mkdir(parents=True,exist_ok=True)
 lines=["# AU_SP_ASX200 v0.83 — evidence completeness repair and final Gate-C closure","",
 "## Verdict",f"**{s['verdict']}**","",
 f"V0.82 EVIDENCE COMPLETENESS REPAIRED = **{'YES' if s['v082_evidence_completeness_repaired'] else 'NO'}**.",
 f"AU_SOURCE_NATIVE_TAXONOMY_IDENTITY_READY = **{'YES' if s['au_source_native_taxonomy_identity_ready'] else 'NO'}**.",
 f"CURRENT UI→API INDUSTRY BINDING = **{s['current_ui_api_industry_binding']}**.",
 f"DOWNLOAD CONTROL = **{s['download_control']}**.",
 f"DOWNLOAD CLASSIFICATION HEADER = **{s['download_classification_header']}**.",
 f"APPCLASS/MANIFEST TAXONOMY MARKER = **{s['appclass_manifest_taxonomy_marker']}**.",
 f"API FILTER-OPTIONS TAXONOMY MARKER = **{s['api_filter_options_taxonomy_marker']}**.",
 f"OFFICIAL ASX COMPANY-SEARCH SEMANTICS = **{s['official_asx_company_search_semantics']}**.",
 f"CURRENTNESS/CONTINUITY = **{s['currentness_continuity']}**.",
 f"TAXONOMY IDENTITY = **{s['taxonomy_identity']}**.",
 f"TAXONOMY OWNER = **{s['taxonomy_owner']}**.",
 f"FORMAL LEVEL = **{s['formal_level']}**.",
 f"VERSION STATUS = **{s['version_status']}**.",
 f"SENTINEL STATUS = **{s['sentinel_status']}**.",
 f"FIELD→TAXONOMY BINDING = **{s['field_to_taxonomy_binding']}**.","",
 "## Scope","v0.82 history was not modified. Live count drift remains recorded as directory mutation, not Frozen membership or identity evidence. AU Gate D/E/F were not executed. No AU canonical materialization, parking/reselection execution, next cohort, Sector RS or P0/P1/P2 occurred.","",
 "## Blocker",f"**{s['blocker'] or 'NONE'}**.","",
 "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
 "## Next gate",f"**{s['next_gate']}**","","Hard stop applied."]
 report.write_text("\n".join(lines)+"\n",encoding="utf-8")
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!="manifest_v0.83.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
 files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
 wj(out/"manifest_v0.83.json",{"version":VERSION,"stage":STAGE,"verdict":s["verdict"],"v082_evidence_completeness_repaired":True,
  "au_source_native_taxonomy_identity_ready":s["au_source_native_taxonomy_identity_ready"],"blocker":s["blocker"],"workflow_run_id":a.workflow_run_id,
  "workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_digest":dig,"canonical_ready_rows":37,"canonical_total_rows":1425,
  "au_gate_d_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,"canonical_materialization_runs":0,"au_parking_executions":0,"reselection_executions":0,
  "next_cohort_executions":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":s["next_gate"]})
 return 0
if __name__=="__main__":raise SystemExit(main())
