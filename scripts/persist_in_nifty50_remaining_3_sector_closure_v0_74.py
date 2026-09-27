#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.74"
STAGE="IN_NIFTY50_REMAINING_3_SECTOR_NODE_SOURCE_NATIVE_CODE_CLOSURE_GATE_F_COMPLETION"
REQUIRED_START_HEAD="57364dbf0b08edc2c563e0ecbf8f9d3e5fc2269f"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_in_nifty50_remaining_3_sector_closure_v0_74")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.74.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.74.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.74.csv")
    rem=readcsv(out/"in_remaining_3_sector_code_binding_v0.74.csv")
    inv=readcsv(out/"in_15_sector_code_inventory_v0.74.csv")
    cov=readcsv(out/"in_exact_45_classification_coverage_v0.74.csv")
    bind=readcsv(out/"in_source_native_code_binding_v0.74.csv")
    contract=json.loads((out/"nse_sector_cell_reconstruction_contract_v0.74.json").read_text(encoding="utf-8"))
    prov=json.loads((out/"provider_call_audit_v0.74.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.74.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(rem)!=3 or len(inv)!=15 or len(bind)!=15 or len(cov)!=45:raise RuntimeError("evidence row counts")
    if pre["gate_h_promotions"]!=0 or pre["canonical_materialization_runs"]!=0:raise RuntimeError("Gate H/canonical out of scope")
    if pre["canonical_ready_rows"]!=37 or pre["sector_rs_runs"]!=0:raise RuntimeError("canonical/Sector RS")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("P0/P1/P2")
    if pre["in_exact_45_sector_classification_coverage_ready"]:
        if pre["verdict"]!="PASS_IN_NIFTY50_REMAINING_3_SECTOR_CODE_CLOSURE_GATE_F_COMPLETE":raise RuntimeError("success verdict")
        if (pre["classified"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(45,45,0,0,0,0):raise RuntimeError("success counts")
        if pre["bound_classification_level"]!="SECTOR" or pre["distinct_classifications"]!=15 or pre["source_native_code_coverage"]!=45:raise RuntimeError("success classification")
        if pre["remaining_3_node_bindings"]!=3:raise RuntimeError("remaining 3")
        if any(r["Binding_Status"]!="PASS" for r in rem):raise RuntimeError("remaining node binding")
        if any(r["Binding_Status"]!="PASS" for r in bind):raise RuntimeError("all 15 binding")
        if any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in cov):raise RuntimeError("coverage rows")
        if not contract["Deterministic_Rerun"]:raise RuntimeError("coordinate determinism")
        if pre["next_gate"]!="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE" or pre["blocker"]!="":raise RuntimeError("next/blocker")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.74 remaining-three NSE SECTOR source-native code closure and exact-45 Gate-F completion evidence"
    }
    (out/"artifact_binding_v0.74.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.74.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.74.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/IN_NIFTY50_Remaining_3_Sector_Node_Code_Closure_Gate_F_Completion_v0.74.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["in_exact_45_sector_classification_coverage_ready"] else "NO"
    report.write_text("\n".join([
      "# IN_NIFTY50 Remaining-3 Sector Node / Source-Native Code Closure / Gate-F Completion v0.74","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"IN_EXACT_45_SECTOR_CLASSIFICATION_COVERAGE_READY = **{ready}**.",
      f"CLASSIFIED / TOTAL = **{pre['classified']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"CONFLICT = **{pre['conflict']}**.",
      f"BOUND CLASSIFICATION LEVEL = **{pre['bound_classification_level']}**.",
      f"DISTINCT CLASSIFICATIONS = **{pre['distinct_classifications']}**.",
      f"SOURCE-NATIVE CODE COVERAGE = **{pre['source_native_code_coverage']} / 45**.",
      f"REMAINING-3 NODE BINDINGS = **{pre['remaining_3_node_bindings']} / 3**.","",
      "## Authority scope",
      "The v0.73 SECTOR-level binding and public application contract remain authoritative and are not reopened. Twelve v0.73 PASS Sector label/code bindings are preserved. Only Information Technology, Services, and Telecommunication are targeted for new code closure.","",
      "## Coordinate extraction",
      f"- Official PDF SHA-256: {pre['pdf_sha256']}",
      f"- Tool: {contract['Tool']} {contract['Tool_Version']}",
      f"- Method: {contract['Extraction_Method']}",
      f"- Deterministic rerun: {'PASS' if contract['Deterministic_Rerun'] else 'NOT_VERIFIED'}",
      f"- Coordinate structural SHA-256: {pre['coordinate_structural_sha256']}",
      "Only words whose coordinates fall inside the classification cell are retained. Adjacent-column tokens are discarded by the persisted column boundary; no words, spelling, or punctuation are supplied by model inference.","",
      "## Descendant closure",
      "Persisted v0.73 INDUSTRY and BASIC_INDUSTRY assignments for the seven affected securities are independently checked against coordinate-reconstructed official taxonomy cells. Parent Sector_Code is taken from the explicit Sector_Code column of the persisted v0.72 structured taxonomy row, not from an assumed prefix rule. Prefix hierarchy is audited only as an integrity check.","",
      "## Scope boundary",
      "No application-contract rediscovery, application endpoint refetch, constituent refetch, NSE EQUITY_L, OCR, screenshots, manual transcription, fuzzy matching, semantic inference, company-name join, cross-taxonomy mapping, PDSC fallback, Gate H, canonical materialization, Sector RS, or P0/P1/P2 occurred.","",
      "## Immutability",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.",
      "- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.",
      "- Canonical READY remains 37/1425.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: Gate H, canonical materialization, Sector RS, P0/P1/P2, and next cohort are not executed."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.74.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "in_exact_45_sector_classification_coverage_ready":pre["in_exact_45_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"bound_classification_level":pre["bound_classification_level"],
      "distinct_classifications":pre["distinct_classifications"],"source_native_code_coverage":pre["source_native_code_coverage"],
      "remaining_3_node_bindings":pre["remaining_3_node_bindings"],"blocker":pre["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,"sector_rs_runs":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.74.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["in_exact_45_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"bound_classification_level":pre["bound_classification_level"],
      "distinct_classifications":pre["distinct_classifications"],"source_native_code_coverage":pre["source_native_code_coverage"],
      "remaining_3_node_bindings":pre["remaining_3_node_bindings"],"blocker":pre["blocker"],
      "workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
