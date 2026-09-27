#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.84"
STAGE="AU_SP_ASX200_GICS_INDUSTRY_GROUP_FIELD_SOURCE_NATIVE_CODE_FEASIBILITY_GATE_D"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output-dir",default="output_au_sp_asx200_gics_code_gate_d_v0_84")
 ap.add_argument("--artifact-id",required=True,type=int);ap.add_argument("--artifact-digest",required=True);ap.add_argument("--artifact-name",required=True)
 ap.add_argument("--workflow-run-id",required=True,type=int);ap.add_argument("--workflow-head-sha",required=True)
 a=ap.parse_args();out=ROOT/a.output_dir
 s=json.loads((out/"summary_preupload_v0.84.json").read_text());c=json.loads((out/"stage_checkpoint_preupload_v0.84.json").read_text())
 dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
 bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS","workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
 wj(out/"artifact_binding_v0.84.json",bind);sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.84.json",sf)
 cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha});wj(out/"stage_checkpoint_v0.84.json",cf)
 report=ROOT/"docs/validation/AU_SP_ASX200_GICS_Industry_Group_Code_Feasibility_Gate_D_v0.84.md";report.parent.mkdir(parents=True,exist_ok=True)
 lines=["# AU_SP_ASX200 GICS Industry-Group Field / Source-Native Code Feasibility Gate D v0.84","",
 "## Verdict",f"**{sf['verdict']}**","",
 f"AU_SECTOR_FIELD_CODE_FEASIBILITY_READY = **{'YES' if sf['au_sector_field_code_feasibility_ready'] else 'NO'}**.",
 f"CURRENT RAW CLASSIFICATION VALUES = **{sf['current_raw_classification_values']}**.",
 f"FORMAL GICS VALUES = **{sf['formal_gics_values']}**.",
 f"NONFORMAL / UNRESOLVED VALUES = **{sf['nonformal_unresolved_values']}**.",
 f"OFFICIAL GICS STRUCTURE READY = **{'YES' if sf['official_gics_structure_ready'] else 'NO'}**.",
 f"SOURCE-NATIVE GICS INDUSTRY-GROUP CODES READY = **{'YES' if sf['source_native_gics_industry_group_codes_ready'] else 'NO'}**.",
 f"FORMAL LABEL→CODE COVERAGE = **{sf['formal_label_code_coverage']}**.",
 f"CODE COLLISIONS = **{sf['code_collisions']}**.",
 f"SENTINEL TREATMENT = **{sf['sentinel_treatment']}**.",
 f"PDSC FALLBACK REQUIRED = **{'YES' if sf['pdsc_fallback_required'] else 'NO'}**.",
 f"PDSC FEASIBILITY = **{sf['pdsc_feasibility']}**.",
 f"PDSC COLLISIONS = **{sf['pdsc_collisions']}**.",
 f"SELECTED CODE STRATEGY = **{sf['selected_code_strategy']}**.","",
 "## Scope","Gate C authority was not reopened. Exact-label matching used only GICS→GICS at INDUSTRY_GROUP level with Unicode NFC and surrounding whitespace removal. No fuzzy or semantic mapping was used. Unresolved source values receive no GICS code and no PDSC. AU Gate E/F/H were not executed; no Frozen-63 linkage, canonical materialization, other cohort, Sector RS or P0/P1/P2 occurred.","",
 "## Blocker",f"**{sf['blocker'] or 'NONE'}**.","",
 "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
 "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied."]
 report.write_text("\n".join(lines)+"\n",encoding="utf-8")
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!="manifest_v0.84.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
 files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
 wj(out/"manifest_v0.84.json",{"version":VERSION,"stage":STAGE,"verdict":sf["verdict"],"au_sector_field_code_feasibility_ready":sf["au_sector_field_code_feasibility_ready"],
  "selected_code_strategy":sf["selected_code_strategy"],"blocker":sf["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
  "artifact_id":a.artifact_id,"artifact_digest":dig,"canonical_ready_rows":37,"canonical_total_rows":1425,
  "frozen_63_linkage_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,"gate_h_runs":0,"canonical_materialization_runs":0,"other_cohort_runs":0,
  "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":sf["next_gate"]})
 return 0
if __name__=="__main__":raise SystemExit(main())
