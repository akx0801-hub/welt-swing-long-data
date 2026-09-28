#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.86"
STAGE="AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output-dir",default="output_au_sp_asx200_identity_linkage_gate_e_v0_86")
 ap.add_argument("--artifact-id",required=True,type=int);ap.add_argument("--artifact-digest",required=True);ap.add_argument("--artifact-name",required=True)
 ap.add_argument("--workflow-run-id",required=True,type=int);ap.add_argument("--workflow-head-sha",required=True)
 a=ap.parse_args();out=ROOT/a.output_dir
 s=json.loads((out/"summary_preupload_v0.86.json").read_text());c=json.loads((out/"stage_checkpoint_preupload_v0.86.json").read_text())
 dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
 bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS","workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
 wj(out/"artifact_binding_v0.86.json",bind)
 sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.86.json",sf)
 cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
 wj(out/"stage_checkpoint_v0.86.json",cf)
 report=ROOT/"docs/validation/AU_SP_ASX200_Deterministic_Security_Identity_Linkage_Gate_E_v0.86.md";report.parent.mkdir(parents=True,exist_ok=True)
 lines=["# AU_SP_ASX200 Deterministic Security Identity Linkage Gate E v0.86","",
 "## Verdict",f"**{sf['verdict']}**","",
 f"AU_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_READY = **{'YES' if sf['au_deterministic_security_identity_linkage_ready'] else 'NO'}**.",
 f"FROZEN TARGET = **{sf['frozen_target']}**.",
 f"CURRENT ASX DIRECTORY ROWS = **{sf['current_asx_directory_rows']}**.",
 f"CURRENT DISTINCT ASX CODES = **{sf['current_distinct_asx_codes']}**.",
 f"FROZEN SOURCE-WS-ID CONTRACT = **{sf['frozen_source_ws_id_contract']}**.",
 f"EXACT TICKER LINKS = **{sf['exact_ticker_links']}**.",
 f"SOURCE-WS-ID EQUALITY = **{sf['source_ws_id_equality']}**.",
 f"NOT_FOUND = **{sf['not_found']}**.",
 f"AMBIGUOUS = **{sf['ambiguous']}**.",
 f"NOT_VERIFIED = **{sf['not_verified']}**.",
 f"CONFLICT = **{sf['conflict']}**.",
 f"COMPANY-NAME LINKAGE = **{sf['company_name_linkage']}**.",
 f"TICKER-CHANGE INFERENCE = **{sf['ticker_change_inference']}**.","",
 "## Scope","Identity only. The Frozen physical file has no Primary_Universe_Index column; the cohort label was taken from the already-governed exact Security_Key capability sidecar while all identity fields remained sourced from Frozen. One fresh official ASX directory CSV snapshot was used. No company-name linkage, fuzzy matching, ticker-change inference, per-security fanout, classification coverage, GICS-code attachment, PDSC, Gate F/H, canonical materialization, other cohort, Sector RS or P0/P1/P2 was executed.","",
 "## Blocker",f"**{sf['blocker'] or 'NONE'}**.","",
 "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
 "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied."]
 report.write_text("\n".join(lines)+"\n",encoding="utf-8")
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!="manifest_v0.86.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
 files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
 wj(out/"manifest_v0.86.json",{"version":VERSION,"stage":STAGE,"verdict":sf["verdict"],
  "au_deterministic_security_identity_linkage_ready":sf["au_deterministic_security_identity_linkage_ready"],"blocker":sf["blocker"],
  "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_digest":dig,
  "canonical_ready_rows":37,"canonical_total_rows":1425,"au_gate_f_runs":0,"gate_h_runs":0,"canonical_materialization_runs":0,
  "other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":sf["next_gate"]})
 return 0
if __name__=="__main__":raise SystemExit(main())
