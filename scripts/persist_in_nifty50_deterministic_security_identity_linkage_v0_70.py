#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.70"
STAGE="IN_NIFTY50_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE"
REQUIRED_START_HEAD="357df447e225ab1fc839530b1d2b0d2d217fd652"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_in_nifty50_deterministic_security_identity_linkage_v0_70")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.70.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.70.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.70.csv")
    link=readcsv(out/"in_exact_45_identity_linkage_audit_v0.70.csv")
    prov=json.loads((out/"provider_call_audit_v0.70.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.70.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests): raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()): raise RuntimeError("prohibited provider calls")
    if len(link)!=45: raise RuntimeError("linkage rows")
    if pre["gate_f_executions"]!=0 or pre["sector_classification_population_rows"]!=0:
        raise RuntimeError("Gate F/sector population")
    if pre["canonical_ready_rows"]!=37 or pre["sector_rs_runs"]!=0:
        raise RuntimeError("canonical/Sector RS changed")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:
        raise RuntimeError("P0/P1/P2")
    if pre["in_deterministic_ws_id_linkage_ready"]:
        if pre["verdict"]!="PASS_IN_NIFTY50_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE":
            raise RuntimeError("success verdict")
        if (pre["linked"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(45,45,0,0,0,0):
            raise RuntimeError("success counts")
        if any(r["Gate_E_Status"]!="PROVABLY_LINKED" for r in link):
            raise RuntimeError("row linkage not all pass")
        if pre["next_gate"]!="IN_NIFTY50 EXACT FROZEN SECTOR CLASSIFICATION COVERAGE GATE":
            raise RuntimeError("next gate")
    else:
        if not pre["blocker"]: raise RuntimeError("failure blocker absent")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.70 IN_NIFTY50 Gate E deterministic official-source security identity linkage evidence"
    }
    (out/"artifact_binding_v0.70.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.70.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.70.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/IN_NIFTY50_Deterministic_Security_Identity_Linkage_Gate_v0.70.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["in_deterministic_ws_id_linkage_ready"] else "NO"
    report.write_text("\n".join([
      "# IN_NIFTY50 Deterministic Security Identity Linkage Gate v0.70","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"IN_DETERMINISTIC_WS_ID_LINKAGE_READY = **{ready}**.",
      f"LINKED / TOTAL = **{pre['linked']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"CONFLICT = **{pre['conflict']}**.",
      f"IDENTITY ROUTE = **{pre['identity_route']}**.","",
      "## Scope",
      "Gate E only. The exact Frozen target was reconstructed directly from SWING_U3K_FROZEN_v0.5.csv as the 45 XNSE rows. No sector-classification population, Gate F execution, canonical IN partition, Sector RS or P0/P1/P2 execution occurred.","",
      "## Official source route",
      "The builder discovered the current NIFTY 50 constituent bulk link from the official NIFTY 50 page and the NSE equity-security reference bulk link from the official NSE securities-available-for-trading page. Only official niftyindices.com / nseindia.com source classes were used.",
      "Identity matching uses only exact symbol/local identifiers and exact ISIN. Company-name joins, fuzzy matching, manual ticker-to-company inference and per-security web fanout are forbidden and audited at zero.","",
      "## Currentness boundary",
      f"Frozen identities linked while absent from current NIFTY membership: {pre['current_nifty_membership_absent_but_identity_linked']}. Such rows, if any, prove identity only; they do not imply Gate F classification coverage.","",
      "## Source persistence",
      "Raw third-party/exchange download redistribution rights were not asserted. v0.70 persists source URLs, retrieval timestamps, content types, raw hashes, schemas and bounded derived identity evidence rather than redistributing the complete downloaded source files.","",
      "## Immutability",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.",
      "- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.",
      "- Canonical READY remains 37/1425.",
      "- Sector RS / P0 / P1 / P2: 0 / 0 / 0 / 0.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: Gate F not executed; no sector mapping or canonical materialization."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.70.json": files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,
      "verdict":pre["verdict"],"in_deterministic_ws_id_linkage_ready":pre["in_deterministic_ws_id_linkage_ready"],
      "linked":pre["linked"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"identity_route":pre["identity_route"],
      "blocker":pre["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "gate_f_executions":0,"sector_classification_population_rows":0,"canonical_ready_rows":37,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.70.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["in_deterministic_ws_id_linkage_ready"],"linked":pre["linked"],"total":pre["total"],
      "ambiguous":pre["ambiguous"],"not_found":pre["not_found"],"not_verified":pre["not_verified"],"conflict":pre["conflict"],
      "identity_route":pre["identity_route"],"blocker":pre["blocker"],"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
