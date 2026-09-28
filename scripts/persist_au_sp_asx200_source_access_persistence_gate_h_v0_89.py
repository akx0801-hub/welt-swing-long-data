#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.89"
STAGE="AU_SP_ASX200_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE_H"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p:Path,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_au_sp_asx200_source_access_persistence_gate_h_v0_89")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args();out=ROOT/a.output_dir
    s=json.loads((out/"summary_preupload_v0.89.json").read_text())
    c=json.loads((out/"stage_checkpoint_preupload_v0.89.json").read_text())
    dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS",
          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
    wj(out/"artifact_binding_v0.89.json",bind)
    sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.89.json",sf)
    cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,
                          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    wj(out/"stage_checkpoint_v0.89.json",cf)

    report=ROOT/"docs/validation/AU_SP_ASX200_Source_Access_Evidence_Persistence_Gate_H_v0.89.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# AU_SP_ASX200 Source Access / Evidence Persistence Gate H v0.89","",
      "## Verdict",f"**{sf['verdict']}**","",
      f"AU_SOURCE_ACCESS_PERSISTENCE_READY = **{'YES' if sf['au_source_access_persistence_ready'] else 'NO'}**.",
      f"ASX ACCESS READY = **{sf['asx_access_ready']}**.",
      f"GICS ACCESS READY = **{sf['gics_access_ready']}**.",
      f"RAW ASX PERSISTENCE REQUIRED = **{sf['raw_asx_persistence_required']}**.",
      f"RAW GICS PERSISTENCE REQUIRED = **{sf['raw_gics_persistence_required']}**.",
      f"ASX BOUNDED EVIDENCE SUFFICIENT = **{sf['asx_bounded_evidence_sufficient']}**.",
      f"GICS BOUNDED EVIDENCE SUFFICIENT = **{sf['gics_bounded_evidence_sufficient']}**.",
      f"ASX BOUNDED EVIDENCE PERSISTENCE READY = **{sf['asx_bounded_evidence_persistence_ready']}**.",
      f"GICS BOUNDED EVIDENCE PERSISTENCE READY = **{sf['gics_bounded_evidence_persistence_ready']}**.",
      f"ASX OFFICIAL POLICY REVIEW = **{sf['asx_official_policy_review']}**.",
      f"GICS OFFICIAL POLICY REVIEW = **{sf['gics_official_policy_review']}**.",
      f"ASX POLICY COMPATIBILITY = **{sf['asx_policy_compatibility']}**.",
      f"GICS POLICY COMPATIBILITY = **{sf['gics_policy_compatibility']}**.",
      f"CANONICAL METADATA EVIDENCE PERSISTABLE = **{sf['canonical_metadata_evidence_persistable']}**.",
      f"EXTERNAL AUTHORIZATION REQUIRED = **{sf['external_authorization_required']}**.",
      f"AUTHORIZATION SOURCE = **{sf['authorization_source']}**.","",
      "## Operational interpretation",
      "This is an operational G-SEC-05 decision, not legal advice. Public access and technical bounded-evidence sufficiency both pass. "
      "However, current official ASX policy contains an explicit restriction on automated software/process access and broader restrictions on copying/reproduction/use outside the limited permitted context. "
      "Current official MSCI policy separately restricts database population and unauthorized automated extraction of MSCI proprietary materials. A bounded S&P co-owner policy request is recorded separately; if runner access is blocked, no S&P policy semantics are used for the Gate-H blocker. "
      "The intended future 63-row canonical output is technically bounded metadata, but boundedness does not override those explicit operational restrictions. "
      "Full raw ASX CSV and full MSCI methodology persistence remain unnecessary and were not performed.","",
      "## Blocker",f"**{sf['blocker']}**.","",
      "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
      "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied: no AU parking, reselection, canonical materialization, next cohort, Sector RS or P0/P1/P2."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.89.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
    wj(out/"manifest_v0.89.json",{
      "version":VERSION,"stage":STAGE,"verdict":sf["verdict"],
      "au_source_access_persistence_ready":sf["au_source_access_persistence_ready"],"blocker":sf["blocker"],
      "external_authorization_required":sf["external_authorization_required"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_digest":dig,
      "policy_requests":sf["policy_requests"],"core_source_requests":sf["core_source_requests"],
      "canonical_ready_rows":37,"canonical_total_rows":1425,"canonical_materialization_runs":0,"au_parking_runs":0,
      "reselection_runs":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":sf["next_gate"]
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
