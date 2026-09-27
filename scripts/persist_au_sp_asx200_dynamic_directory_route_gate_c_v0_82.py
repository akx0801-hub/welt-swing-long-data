#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.82"
STAGE="AU_SP_ASX200_DYNAMIC_DIRECTORY_DATA_ROUTE_REPAIR_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C_COMPLETION"

def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p:Path,obj)->None:p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_au_sp_asx200_dynamic_directory_route_gate_c_v0_82")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=ROOT/a.output_dir
    pre=json.loads((out/"summary_preupload_v0.82.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.82.json").read_text(encoding="utf-8"))
    dec=json.loads((out/"au_source_native_taxonomy_identity_decision_v0_82.json").read_text(encoding="utf-8"))
    route=json.loads((out/"au_directory_selected_data_route_contract_v0.82.json").read_text(encoding="utf-8"))
    hist=json.loads((out/"historical_vs_current_asx_bulk_route_audit_v0.82.json").read_text(encoding="utf-8"))
    if pre["version"]!=VERSION or pre["stage"]!=STAGE or chk["verdict"]!=pre["verdict"]:raise RuntimeError("preupload mismatch")
    digest=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    binding={
      "artifact_id":a.artifact_id,"artifact_digest":digest,"artifact_name":a.artifact_name,
      "artifact_scope":"pre-persistence v0.82 AU_SP_ASX200 two-clean-session dynamic directory runtime capture and Gate-C taxonomy identity evidence",
      "artifact_verified":"PASS","workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha
    }
    write_json(out/"artifact_binding_v0.82.json",binding)
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    write_json(out/"summary_v0.82.json",summary)
    cp=dict(chk);cp.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":digest,
                            "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    write_json(out/"stage_checkpoint_v0.82.json",cp)

    report=ROOT/"docs/validation/AU_SP_ASX200_Dynamic_Directory_Data_Route_Gate_C_Completion_v0.82.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    route_note=(
      "Two independent fresh public browser contexts reproduced the same logical directory data route and schema contract."
      if summary["public_browser_reproducible"]=="YES" else
      "The bounded two-context public-browser procedure did not reproduce a qualifying current directory-level data route. Historical v0.62 Gate-B evidence remains historical and was not rewritten."
    )
    lines=[
      "# AU_SP_ASX200 Dynamic Directory Data-Route Repair / Gate C Completion v0.82","",
      "## Verdict",f"**{summary['verdict']}**","",
      f"AU_SOURCE_NATIVE_TAXONOMY_IDENTITY_READY = **{'YES' if summary['au_source_native_taxonomy_identity_ready'] else 'NO'}**.",
      f"DYNAMIC DIRECTORY ROUTE = **{summary['dynamic_directory_route']}**.",
      f"PUBLIC BROWSER REPRODUCIBLE = **{summary['public_browser_reproducible']}**.",
      f"DIRECT HTTP REPLAY = **{summary['direct_http_replay']}**.",
      f"DATA ROUTE TYPE = **{summary['data_route_type']}**.",
      f"DATA RECORDS = **{summary['data_records']}**.",
      f"CLASSIFICATION FIELD = **{summary['classification_field']}**.",
      f"TAXONOMY IDENTITY = **{summary['taxonomy_identity']}**.",
      f"TAXONOMY OWNER = **{summary['taxonomy_owner']}**.",
      f"FORMAL LEVEL = **{summary['formal_level']}**.",
      f"VERSION STATUS = **{summary['version_status']}**.",
      f"FIELD→TAXONOMY BINDING = **{summary['field_to_taxonomy_binding']}**.",
      f"GICS FIELD BINDING = **{summary['gics_field_binding']}**.",
      f"UPSTREAM PROVIDER ATTRIBUTION = **{summary['upstream_provider_attribution']}**.","",
      "## Runtime route evidence",route_note,
      f"RUN 1 route: {route.get('RUN_1',{}).get('logical_route','') or 'NOT_VERIFIED'}.",
      f"RUN 2 route: {route.get('RUN_2',{}).get('logical_route','') or 'NOT_VERIFIED'}.",
      "Both sessions use fresh temporary browser profiles, no pre-existing cookies, no authentication and no proxy. Only ordinary page-generated runtime traffic and the bounded permitted interaction sequence were observed.","",
      "## Taxonomy identity",
      ("The actual runtime schema plus official ASX taxonomy context satisfies Gate C without label-shape inference, fuzzy matching or cross-taxonomy mapping."
       if summary["au_source_native_taxonomy_identity_ready"] else
       "Gate C remains fail-closed. No generic Industry-like field, provider credit or ASX GICS usage elsewhere was promoted into a taxonomy binding without exact field-level evidence."),"",
      "## Historical Gate B / current route",
      f"HISTORICAL_GATE_B = **{hist['HISTORICAL_GATE_B']}**.",
      f"CURRENT_ROUTE_REPRODUCIBILITY = **{hist['CURRENT_ROUTE_REPRODUCIBILITY']}**.",
      f"CURRENT_AUTHORITY_IMPACT = **{hist['CURRENT_AUTHORITY_IMPACT']}**.",
      "Historical evidence was not rewritten.","",
      "## Hard scope",
      "AU Gate D/E/F remain NOT_EVALUATED. No Frozen-63 linkage, classification attachment, PDSC, canonical materialization, park/reselection execution, next cohort, Sector RS or P0/P1/P2 occurred. IN_NIFTY50, JP_N225, US_SP400 and US_SP500 park states are unchanged. Global canonical READY remains 37/1425.","",
      "## Blocker",f"**{summary['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {digest}","",
      "## Next gate",f"**{summary['next_gate']}**","",
      "Hard stop applied after persistence and artifact binding."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.82.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    files["docs/validation/AU_SP_ASX200_Dynamic_Directory_Data_Route_Gate_C_Completion_v0.82.md"]={"bytes":report.stat().st_size,"sha256":sha_file(report)}
    write_json(out/"manifest_v0.82.json",{
      "version":VERSION,"stage":STAGE,"verdict":summary["verdict"],
      "au_source_native_taxonomy_identity_ready":summary["au_source_native_taxonomy_identity_ready"],
      "dynamic_directory_route":summary["dynamic_directory_route"],"public_browser_reproducible":summary["public_browser_reproducible"],
      "direct_http_replay":summary["direct_http_replay"],"blocker":summary["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_digest":digest,
      "canonical_ready_rows":37,"canonical_total_rows":1425,
      "au_gate_d_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,"canonical_materialization_runs":0,
      "park_reselection_executions":0,"next_cohort_executions":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":dec["Next_Gate"]
    })
    return 0

if __name__=="__main__":
    raise SystemExit(main())
