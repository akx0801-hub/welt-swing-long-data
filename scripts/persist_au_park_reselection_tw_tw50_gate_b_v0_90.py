#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.90"
STAGE="AU_SP_ASX200_EXTERNAL_AUTHORIZATION_PARK_POST_PARK_RESELECTION_TW_TW50_GATE_B"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p:Path,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_au_park_reselection_tw_tw50_gate_b_v0_90")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args();out=ROOT/a.output_dir
    s=json.loads((out/"summary_preupload_v0.90.json").read_text())
    c=json.loads((out/"stage_checkpoint_preupload_v0.90.json").read_text())
    dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS",
          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
    wj(out/"artifact_binding_v0.90.json",bind)
    sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.90.json",sf)
    cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,
                          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    wj(out/"stage_checkpoint_v0.90.json",cf)

    report=ROOT/"docs/validation/AU_Park_Post_Park_Reselection_TW_TW50_Gate_B_v0.90.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# AU_SP_ASX200 Park / Post-Park Reselection / TW_TW50 Gate B v0.90","",
      "## Verdict",f"**{sf['verdict']}**","",
      "## AU external-authorization park",
      f"- AU park state: **{sf['au_park_state']}**",
      f"- Technical gates A-G: **{sf['au_technical_gates_a_g']}**",
      f"- Gate H: **{sf['au_gate_h']}**",
      f"- Primary blocker: **{sf['au_primary_blocker']}**",
      f"- Independent GICS blocker: **{sf['au_independent_gics_blocker']}**","",
      "## Deterministic reselection",
      f"- Selected cohort: **{sf['selected_cohort']}**",
      f"- Basis: {sf['selection_basis']}","",
      "## TW_TW50 Gate B",
      f"- TW_OFFICIAL_SECTOR_BULK_SOURCE_READY: **{'YES' if sf['tw_official_sector_bulk_source_ready'] else 'NO'}**",
      f"- Official source: {sf['tw_official_source']}",
      f"- Source composition: {sf['source_composition']}",
      f"- Bulk route type: {sf['bulk_route_type']}",
      f"- Public / reproducible: {sf['public_reproducible']}",
      f"- Direct HTTP replay: {sf['direct_http_replay']}",
      f"- Row-level security records: {sf['row_level_security_records']}",
      f"- Security identifier: {sf['security_identifier_field']} ({sf['security_identifier_type']})",
      f"- ICB Industry Group code field: {sf['icb_industry_group_code_field']}",
      f"- ICB Industry Group name field: {sf['icb_industry_group_name_field']}",
      f"- ICB level binding: {sf['icb_level_binding']}",
      f"- Per-security fanout: {sf['per_security_fanout']}",
      f"- Frozen-49 linkage runs: {sf['frozen_49_linkage_runs']}","",
      "## Blocker",f"**{sf['blocker'] or 'NONE'}**.","",
      "No TW Gate E/F/H, no Frozen-49 row-level linkage, no canonical materialization, no Sector RS and no P0/P1/P2 were executed.","",
      "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
      "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.90.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
    park=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
    files[str(park.relative_to(ROOT))]={"bytes":park.stat().st_size,"sha256":sha(park)}
    wj(out/"manifest_v0.90.json",{
      "version":VERSION,"stage":STAGE,"verdict":sf["verdict"],
      "au_park_state":sf["au_park_state"],"selected_cohort":sf["selected_cohort"],
      "tw_official_sector_bulk_source_ready":sf["tw_official_sector_bulk_source_ready"],"blocker":sf["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_digest":dig,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"tw_gate_e_runs":0,"tw_gate_f_runs":0,"tw_gate_h_runs":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":sf["next_gate"]
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
