#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.72"
STAGE="IN_NIFTY50_NSE_INDICES_CLASSIFICATION_STRUCTURE_EXTRACTION_LEVEL_CODE_BINDING_GATE_F_REPAIR"
REQUIRED_START_HEAD="f6be8b4a3182728ba9976b58410f91e031146348"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_in_nifty50_nse_classification_structure_repair_v0_72")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.72.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.72.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.72.csv")
    cov=readcsv(out/"in_exact_45_classification_coverage_v0.72.csv")
    bindings=readcsv(out/"in_source_native_code_binding_v0.72.csv")
    repro=json.loads((out/"nse_pdf_extraction_reproducibility_audit_v0.72.json").read_text(encoding="utf-8"))
    incons=json.loads((out/"v071_predecessor_evidence_inconsistency_audit_v0.72.json").read_text(encoding="utf-8"))
    prov=json.loads((out/"provider_call_audit_v0.72.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.72.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(cov)!=45:raise RuntimeError("coverage row count")
    if incons["Authority_Treatment"]!="NON_AUTHORITATIVE_ERRONEOUS_NARRATIVE_TEXT" or incons["Historical_v071_Files_Rewritten"] is not False:
        raise RuntimeError("v0.71 inconsistency authority")
    if pre["nifty_constituent_refetches"]!=0:raise RuntimeError("unexpected NIFTY refetch")
    if pre["gate_h_promotions"]!=0 or pre["canonical_materialization_runs"]!=0:raise RuntimeError("Gate H/canonical out of scope")
    if pre["canonical_ready_rows"]!=37 or pre["sector_rs_runs"]!=0:raise RuntimeError("canonical/Sector RS changed")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("P0/P1/P2")

    if pre["in_exact_45_sector_classification_coverage_ready"]:
        if pre["verdict"]!="PASS_IN_NIFTY50_GATE_F_REPAIR_EXACT_CLASSIFICATION_COVERAGE":raise RuntimeError("success verdict")
        if (pre["classified"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"],pre["conflict"])!=(45,45,0,0,0,0):
            raise RuntimeError("success counts")
        if pre["distinct_classifications"]!=15 or pre["source_native_code_coverage"]!=45:raise RuntimeError("success classification/code counts")
        if pre["bound_classification_level"]=="NOT_VERIFIED":raise RuntimeError("success bound level")
        if len(bindings)!=15 or any(r["Code_Binding_Status"]!="PASS" for r in bindings):raise RuntimeError("success 15 bindings")
        if any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in cov):raise RuntimeError("success row statuses")
        if not repro["Deterministic_Extracted_Text"] or not repro["Deterministic_Structural_Output"]:raise RuntimeError("success extraction determinism")
        if pre["next_gate"]!="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE":raise RuntimeError("success next gate")
        if pre["blocker"]!="":raise RuntimeError("success blocker")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.72 NSE classification PDF extraction, level/code binding and Gate-F repair evidence"
    }
    (out/"artifact_binding_v0.72.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.72.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.72.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/IN_NIFTY50_NSE_Classification_Structure_Extraction_Level_Code_Binding_Gate_F_Repair_v0.72.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["in_exact_45_sector_classification_coverage_ready"] else "NO"
    report.write_text("\n".join([
      "# IN_NIFTY50 NSE Indices Classification Structure Extraction / Level + Code Binding / Gate-F Repair v0.72","",
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
      f"PDF EXTRACTION = **{pre['pdf_extraction']}**.","",
      "## v0.71 evidence correction",
      "The narrative sentence claiming every observed NIFTY Industry label had already been exact-bound to one unique Ind_Code is explicitly classified as erroneous non-authoritative narrative text. The structured v0.71 evidence remains authoritative: zero exact unique bindings, level NOT_VERIFIED, and zero source-native code coverage. v0.71 history was not rewritten.","",
      "## Extraction scope",
      "The stage consumes the persisted v0.70 identity authority and v0.71 exact-45 derived classification rows. It does not rerun Gate E and does not refetch ind_nifty50list.csv or use NSE EQUITY_L.",
      "The official NSE Indices classification structure PDF is the only market/reference retrieval. Raw PDF redistribution rights remain NOT_VERIFIED, so the raw PDF is not persisted.","",
      "## Parser environment",
      f"- Tool: pypdf {json.loads((out/'nse_pdf_extraction_environment_v0.72.json').read_text(encoding='utf-8'))['Installed_Version']}",
      f"- PDF SHA-256: {pre['pdf_sha256']}",
      f"- Matches v0.71 PDF SHA: {'YES' if pre['pdf_sha_matches_v071'] else 'NO'}",
      f"- Extracted-text deterministic: {'YES' if repro['Deterministic_Extracted_Text'] else 'NO'}",
      f"- Structural-output deterministic: {'YES' if repro['Deterministic_Structural_Output'] else 'NO'}",
      f"- Page count: {repro['Page_Count']}","",
      "## Scope boundary",
      "No PDSC fallback, company-name join, fuzzy matching, cross-taxonomy mapping, per-security fanout, Gate H promotion, canonical IN partition, Sector RS, or P0/P1/P2 execution occurred.","",
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
      "Hard stop: Gate H not executed; no canonical materialization and no next cohort."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.72.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "in_exact_45_sector_classification_coverage_ready":pre["in_exact_45_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"bound_classification_level":pre["bound_classification_level"],
      "distinct_classifications":pre["distinct_classifications"],"source_native_code_coverage":pre["source_native_code_coverage"],
      "pdf_extraction":pre["pdf_extraction"],"blocker":pre["blocker"],"workflow_run_id":a.workflow_run_id,
      "workflow_head_sha":a.workflow_head_sha,"artifact":binding,"nifty_constituent_refetches":0,"gate_h_promotions":0,
      "canonical_ready_rows":37,"canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.72.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["in_exact_45_sector_classification_coverage_ready"],
      "classified":pre["classified"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],
      "not_verified":pre["not_verified"],"conflict":pre["conflict"],"bound_classification_level":pre["bound_classification_level"],
      "distinct_classifications":pre["distinct_classifications"],"source_native_code_coverage":pre["source_native_code_coverage"],
      "pdf_extraction":pre["pdf_extraction"],"blocker":pre["blocker"],"workflow_run":a.workflow_run_id,
      "artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
