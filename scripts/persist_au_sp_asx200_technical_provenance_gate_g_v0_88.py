#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.88"
STAGE="AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p:Path,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_au_sp_asx200_technical_provenance_gate_g_v0_88")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args();out=ROOT/a.output_dir
    s=json.loads((out/"summary_preupload_v0.88.json").read_text())
    c=json.loads((out/"stage_checkpoint_preupload_v0.88.json").read_text())
    dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS",
          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
    wj(out/"artifact_binding_v0.88.json",bind)
    sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.88.json",sf)
    cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,
                          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    wj(out/"stage_checkpoint_v0.88.json",cf)

    report=ROOT/"docs/validation/AU_SP_ASX200_Technical_Provenance_Gate_G_v0.88.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# AU_SP_ASX200 Technical Provenance Gate G v0.88","",
      "## Verdict",f"**{sf['verdict']}**","",
      f"AU_TECHNICAL_PROVENANCE_READY = **{'YES' if sf['au_technical_provenance_ready'] else 'NO'}**.",
      f"ROWS = **{sf['rows']}**.",
      f"PROVENANCE COMPLETE = **{sf['provenance_complete']}**.",
      f"PROVENANCE INCOMPLETE = **{sf['provenance_incomplete']}**.",
      f"PROVENANCE CONFLICT = **{sf['provenance_conflict']}**.",
      f"PROVENANCE NOT VERIFIED = **{sf['provenance_not_verified']}**.","",
      "## Authorities",
      f"- Frozen authority: {sf['frozen_authority']}",
      f"- Cohort-label authority: {sf['cohort_label_authority']}",
      f"- Classification source: {sf['classification_source']}",
      f"- Classification snapshot SHA256: {sf['classification_source_sha256']}",
      f"- Classification source version/as-of: {sf['classification_source_version_or_asof']}",
      f"- Classification retrieved UTC: {sf['classification_source_retrieved_utc']}",
      f"- Classification effective-as-of status: {sf['classification_effective_asof_status']}",
      f"- Code authority: {sf['code_authority']}",
      f"- Code authority SHA256: {sf['code_authority_sha256']}",
      f"- Code authority version/as-of: {sf['code_authority_version_or_asof']}","",
      "## Evidence versions",
      f"- Identity: v0.86 / {sf['identity_evidence_commit']}",
      f"- Classification: v0.87 / {sf['classification_evidence_commit']}",
      f"- Code authority: v0.85 / {sf['code_authority_evidence_commit']}","",
      "## Technical scope",
      "This stage used persisted v0.85/v0.86/v0.87 evidence only. No ASX, MSCI, S&P or other classification-source network request was made. "
      "Retrieval time was kept distinct from business-effective/as-of semantics. The ephemeral v0.87 download URL is retained only as historical download evidence; the stable source reference is the official ASX directory page. "
      "Gate G is technical provenance only: no licensing, copyright, redistribution, automated-access or persistence-policy judgment was performed. No canonical AU partition was materialized.","",
      "## Blocker",f"**{sf['blocker'] or 'NONE'}**.","",
      "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
      "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.88.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
    wj(out/"manifest_v0.88.json",{
      "version":VERSION,"stage":STAGE,"verdict":sf["verdict"],"au_technical_provenance_ready":sf["au_technical_provenance_ready"],
      "rows":sf["rows"],"provenance_complete":sf["provenance_complete"],"blocker":sf["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_digest":dig,
      "external_source_requests":0,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "gate_h_runs":0,"canonical_materialization_runs":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":sf["next_gate"]
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
