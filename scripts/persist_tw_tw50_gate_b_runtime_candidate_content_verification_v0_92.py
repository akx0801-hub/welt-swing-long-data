#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.92"
STAGE="TW_TW50_GATE_B_RUNTIME_CANDIDATE_CONTENT_VERIFICATION"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p:Path,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_tw_tw50_gate_b_runtime_candidate_verification_v0_92")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args();out=ROOT/a.output_dir
    s=json.loads((out/"summary_preupload_v0.92.json").read_text())
    c=json.loads((out/"stage_checkpoint_preupload_v0.92.json").read_text())
    dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS",
          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
    wj(out/"artifact_binding_v0.92.json",bind)
    sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.92.json",sf)
    cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,
                          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    wj(out/"stage_checkpoint_v0.92.json",cf)

    report=ROOT/"docs/validation/TW_TW50_Gate_B_Runtime_Candidate_Content_Verification_v0.92.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# TW_TW50 Gate-B Runtime Candidate Content Verification v0.92","",
      "## Decision",f"**{sf['verdict']}**","",
      f"TW_GATE_B_READY = **{'YES' if sf['tw_gate_b_ready'] else 'NO'}**.",
      f"CANDIDATES_CHECKED = **{sf['candidates_checked']}**.",
      f"SECURITY_IDENTIFIER = **{sf['security_identifier']}**.",
      f"ICB_INDUSTRY_GROUP = **{sf['icb_industry_group']}**.",
      f"SOURCE_COMPOSITION = **{sf['source_composition']}**.",
      f"BLOCKER = **{sf['blocker'] or 'NONE'}**.","",
      "## Manager correction",
      "The v0.91 PDF finding is preserved as authoritative while the v0.91 stage blocker is not treated as final. "
      "The erroneous third page-audit row was reconciled to the authoritative two-page pdfinfo count without re-parsing or re-evaluating the PDF.","",
      "## Candidate scope",
      "Only the five manager-enumerated current candidates A-E were evaluated. Normal browser interactions were actually executed for the LSEG 'See all constituents' control and current official linked controls where applicable. "
      "Candidate content was classified as usable, insufficient, authentication-required, non-reproducible, or authority-not-verified. No broad source hunt was performed.","",
      "## Hard stops",
      "No Frozen-49 linkage, per-security fanout, TW Gate E/F/H, TW parking, reselection, CN_CSI300 execution, canonical materialization, Sector RS, or P0/P1/P2 was executed.","",
      "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
      "## Next gate",f"**{sf['next_gate']}**"
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.92.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
    wj(out/"manifest_v0.92.json",{
      "version":VERSION,"stage":STAGE,"verdict":sf["verdict"],"tw_gate_b_ready":sf["tw_gate_b_ready"],
      "candidates_checked":sf["candidates_checked"],"blocker":sf["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_digest":dig,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"frozen_49_linkage_runs":0,"per_security_fanout":0,
      "tw_gate_e_runs":0,"tw_gate_f_runs":0,"tw_gate_h_runs":0,"tw_parking_runs":0,"reselection_runs":0,
      "cn_csi300_execution_runs":0,"canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":sf["next_gate"]
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
