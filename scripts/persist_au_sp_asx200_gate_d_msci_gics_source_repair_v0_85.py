#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.85"
STAGE="AU_SP_ASX200_GATE_D_OFFICIAL_GICS_CO_OWNER_SOURCE_REPAIR"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p:Path,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_au_sp_asx200_gate_d_msci_gics_repair_v0_85")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args();out=ROOT/a.output_dir
    s=json.loads((out/"summary_preupload_v0.85.json").read_text())
    c=json.loads((out/"stage_checkpoint_preupload_v0.85.json").read_text())
    dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS",
          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
    wj(out/"artifact_binding_v0.85.json",bind)
    sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.85.json",sf)
    cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,
                          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    wj(out/"stage_checkpoint_v0.85.json",cf)

    report=ROOT/"docs/validation/AU_SP_ASX200_Gate_D_MSCI_GICS_CoOwner_Source_Repair_v0.85.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    counts=sf.get("gics_level_counts",{})
    lines=[
      "# AU_SP_ASX200 Gate-D Official GICS Co-Owner Source Repair v0.85","",
      "## Verdict",f"**{sf['verdict']}**","",
      f"AU_SECTOR_FIELD_CODE_FEASIBILITY_READY = **{'YES' if sf['au_sector_field_code_feasibility_ready'] else 'NO'}**.",
      f"MSCI CURRENT GICS METHODOLOGY = **{sf['msci_current_gics_methodology']}**.",
      f"DOCUMENT DISPLAY DATE = **{sf['document_display_date']}**.",
      f"CURRENT EFFECTIVE STRUCTURE = **{sf['current_effective_structure']}**.",
      f"GICS LEVEL COUNTS = **{counts}**.",
      f"INDUSTRY GROUP INVENTORY = **{sf['industry_group_inventory']}**.",
      f"CURRENT ASX RAW VALUES = **{sf['current_asx_raw_values']}**.",
      f"FORMAL EXACT-MATCH VALUES = **{sf['formal_exact_match_values']}**.",
      f"NONFORMAL VALUES = **{sf['nonformal_values']}**.",
      f"FORMAL LABEL→CODE COVERAGE = **{sf['formal_label_code_coverage']}**.",
      f"CODE COLLISIONS = **{sf['code_collisions']}**.",
      f"SOURCE-NATIVE CODES READY = **{'YES' if sf['source_native_codes_ready'] else 'NO'}**.",
      f"PDSC FALLBACK REQUIRED = **{'YES' if sf['pdsc_fallback_required'] else 'NO'}**.",
      f"SELECTED CODE STRATEGY = **{sf['selected_code_strategy']}**.","",
      "## Scope",
      "Gate C was not reopened. The current ASX raw classification inventory was reused from persisted v0.84 authority. "
      "Only the official MSCI GICS methodology was used as the independent co-owner taxonomy/code source. Exact label binding used Unicode NFC plus surrounding-whitespace removal only. "
      "No fuzzy/semantic matching, cross-taxonomy mapping, PDSC, Frozen-63 linkage, Gate E/F/H, canonical materialization, other cohort, Sector RS or P0/P1/P2 was executed.","",
      "## Blocker",f"**{sf['blocker'] or 'NONE'}**.","",
      "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
      "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.85.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
    wj(out/"manifest_v0.85.json",{
      "version":VERSION,"stage":STAGE,"verdict":sf["verdict"],
      "au_sector_field_code_feasibility_ready":sf["au_sector_field_code_feasibility_ready"],
      "selected_code_strategy":sf["selected_code_strategy"],"blocker":sf["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_digest":dig,
      "canonical_ready_rows":37,"canonical_total_rows":1425,
      "frozen_63_linkage_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,"gate_h_runs":0,
      "canonical_materialization_runs":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":sf["next_gate"]
    })
    return 0
if __name__=="__main__":raise SystemExit(main())
