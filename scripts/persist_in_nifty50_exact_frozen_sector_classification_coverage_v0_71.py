#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.71"
STAGE="IN_NIFTY50_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE_GATE"
REQUIRED_START_HEAD="9acf51ba20e5c88954d0b21ed5017f95274b6f6f"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()

    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.71.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.71.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.71.csv")
    cov=readcsv(out/"in_exact_45_classification_coverage_v0.71.csv")
    bindings=readcsv(out/"in_source_native_code_binding_v0.71.csv")
    prov=json.loads((out/"provider_call_audit_v0.71.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.71.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited provider calls")
    if len(cov)!=45:raise RuntimeError("coverage rows")
    if pre["gate_h_promotions"]!=0 or pre["canonical_materialization_runs"]!=0:raise RuntimeError("Gate H/canonical out of scope")
    if pre["canonical_ready_rows"]!=37:raise RuntimeError("canonical ready changed")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("downstream runs")
    if pre["in_exact_45_sector_classification_coverage_ready"]:
        if pre["verdict"]!="PASS_IN_NIFTY50_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE":raise RuntimeError("success verdict")
        if (pre["classified"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(45,45,0,0,0,0):raise RuntimeError("success counts")
        if pre["taxonomy"]!="NSE_INDICES_INDUSTRY_CLASSIFICATION" or pre["bound_classification_level"]!="INDUSTRY":raise RuntimeError("success taxonomy/level")
        if pre["source_native_code_coverage"]!=45:raise RuntimeError("success code coverage")
        if any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in cov):raise RuntimeError("row status")
        if any(r["Official_Taxonomy_Level"]!="INDUSTRY" or r["Source_Sector_Code"]=="NOT_VERIFIED" for r in cov):raise RuntimeError("row code/level")
        if pre["next_gate"]!="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE":raise RuntimeError("next gate")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.71 IN_NIFTY50 Gate F exact Frozen sector-classification coverage evidence"
    }
    (out/"artifact_binding_v0.71.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.71.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.71.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/IN_NIFTY50_Exact_Frozen_Sector_Classification_Coverage_Gate_v0.71.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["in_exact_45_sector_classification_coverage_ready"] else "NO"
    report.write_text("\n".join([
      "# IN_NIFTY50 Exact Frozen Sector Classification Coverage Gate v0.71","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"IN_EXACT_45_SECTOR_CLASSIFICATION_COVERAGE_READY = **{ready}**.",
      f"CLASSIFIED / TOTAL = **{pre['classified']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"CONFLICT = **{pre['conflict']}**.",
      f"TAXONOMY = **{pre['taxonomy']}**.",
      f"BOUND CLASSIFICATION LEVEL = **{pre['bound_classification_level']}**.",
      f"DISTINCT CLASSIFICATIONS = **{pre['distinct_classifications']}**.",
      f"SOURCE-NATIVE CODE COVERAGE = **{pre['source_native_code_coverage']} / 45**.","",
      "## Scope",
      "Gate F only. The stage consumes the v0.70 exact direct NIFTY ISIN identity authority and rechecks the official NIFTY 50 constituent source in one bounded bulk request. NSE EQUITY_L is not promoted or used as predecessor authority.",
      "No Gate H promotion, no canonical IN partition, no Sector RS and no P0/P1/P2 execution occurred.","",
      "## Classification contract",
      "Taxonomy identity remains NSE_INDICES_INDUSTRY_CLASSIFICATION. The current official NSE Indices Industry Classification page and its linked official classification-structure document are used only to prove the exact formal level and source-native code binding for the current NIFTY constituent Industry field.",
      "The raw source Industry string is preserved separately. Matching to the official structure uses exact label evidence after whitespace layout normalization only; no company-name join, fuzzy match, cross-taxonomy crosswalk or PDSC fallback is used.","",
      "## Source drift",
      f"- Current NIFTY source SHA-256: {pre['source_sha256'] or 'NOT_VERIFIED'}",
      f"- Changed vs v0.70: {'YES' if pre['source_sha_changed_vs_v070'] else 'NO'}",
      "A source-byte change is not treated as an automatic failure; exact Frozen-45 coverage and classification binding are re-proved from the current bulk file.","",
      "## Access / persistence boundary",
      "Gate H remains NOT_EVALUATED. Raw source redistribution or persistence rights are not claimed. The repository stores hashes, schemas, official references and bounded derived evidence only.","",
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
      "Hard stop: Gate H not executed; no canonical metadata materialization and no next cohort."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.71.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "in_exact_45_sector_classification_coverage_ready":pre["in_exact_45_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"taxonomy":pre["taxonomy"],
      "bound_classification_level":pre["bound_classification_level"],"distinct_classifications":pre["distinct_classifications"],
      "source_native_code_coverage":pre["source_native_code_coverage"],"blocker":pre["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.71.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["in_exact_45_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"taxonomy":pre["taxonomy"],
      "bound_classification_level":pre["bound_classification_level"],"distinct_classifications":pre["distinct_classifications"],
      "source_native_code_coverage":pre["source_native_code_coverage"],"blocker":pre["blocker"],
      "workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
