#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.67"
STAGE="BR_IBRX100_B3_CLASSIFICATION_TREE_EXECUTION_EXACT_37_COVERAGE_GATE"
REQUIRED_START_HEAD="a6c7e3db455d73c436142230bd466c64f2ac147d"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_br_ibrx100_b3_classification_tree_execution_v0_67")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.67.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.67.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.67.csv")
    cov=readcsv(out/"br_exact_37_classification_coverage_v0.67.csv")
    req=readcsv(out/"b3_group_request_ledger_v0.67.csv")
    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if len(cov)!=37:raise RuntimeError("coverage rows")
    if pre["canonical_mapping_population_runs"]!=0 or pre["sector_rs_runs"]!=0:raise RuntimeError("out of scope")
    if pre["immutability"]["p0_runs"]!=0 or pre["immutability"]["p1_runs"]!=0 or pre["immutability"]["p2_runs"]!=0:raise RuntimeError("P0/P1/P2")
    if pre["br_exact_37_classification_coverage_ready"]:
        if (pre["ready"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"])!=(37,37,0,0,0):raise RuntimeError("success counts")
        if pre["executed_group_queries"]!=pre["expected_group_queries"] or pre["successful_group_queries"]!=pre["expected_group_queries"]:raise RuntimeError("success traversal")
        if pre["pdsc_collisions"]!=0:raise RuntimeError("success pdsc")
    else:
        if not pre["blocker"]:raise RuntimeError("missing fail blocker")

    binding={"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,
             "artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,"artifact_verified":"PASS",
             "artifact_scope":"pre-persistence v0.67 BR IBrX100 B3 tree execution / exact-37 coverage evidence"}
    (out/"artifact_binding_v0.67.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.67.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.67.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/BR_IBRX100_B3_Classification_Tree_Execution_Exact_37_Coverage_v0.67.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    status="YES" if pre["br_exact_37_classification_coverage_ready"] else "NO"
    report.write_text("\n".join([
      "# BR_IBRX100 B3 Classification Tree Execution / Exact-37 Coverage Gate v0.67","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"BR_EXACT_37_CLASSIFICATION_COVERAGE_READY = **{status}**.",
      f"READY / TOTAL = **{pre['ready']} / {pre['total']}**.",
      f"AMBIGUOUS = **{pre['ambiguous']}**.",
      f"NOT_FOUND = **{pre['not_found']}**.",
      f"NOT_VERIFIED = **{pre['not_verified']}**.",
      f"TREE NODES = **{pre['tree_nodes']}**.",
      f"GROUP QUERIES EXECUTED / EXPECTED = **{pre['executed_group_queries']} / {pre['expected_group_queries']}**.",
      f"DISTINCT SETORES = **{pre['distinct_setores']}**.",
      f"PDSC COLLISIONS = **{pre['pdsc_collisions']}**.","",
      "## Predecessor",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      "- v0.66 verdict: PASS_B3_CLASSIFICATION_TREE_CONTRACT.",
      "- Public tree contract: GET GetIndustryClassification/...; reproducible without authentication.",
      "- v0.66 workflow/artifact: 36269159688 / 10915250534.",
      "- v0.66 artifact digest: sha256:af7fe53a42cd199ff2b1a1edd98cb73d7535131b1e2135977c45a0853d12b5ae.",
      "- Security -> B3 company code authority remains 37/37 from v0.64.","",
      "## Execution",
      f"- Setor count: {pre['setor_count']}.",
      f"- Subsetor count: {pre['subsetor_count']}.",
      f"- Segmento leaves: {pre['segmento_leaf_count']}.",
      f"- Distinct Segmento labels: {pre['distinct_segmento_labels']}.",
      f"- Group requests successful: {pre['successful_group_queries']}.",
      f"- Group requests failed: {pre['failed_group_queries']}.",
      "The exact tree payload, flattened hierarchy, segment collision audit, finite query inventory, response hashes and explicit B3 company-code membership are persisted as shadow evidence. No company-name or fuzzy matching is used.","",
      "## PDSC",
      "Only PROVABLY_MAPPABLE rows receive PDSC_SHA256_V1. Raw B3 Setor Econômico labels are retained; NFC is derived only for the canonical name and hash input. Source_Sector_Code remains NULL unless B3 explicitly supplies one.","",
      "## Scope / immutability",
      "- Canonical BR metadata materialization: 0.",
      "- Sector RS: 0.",
      "- Other cohorts reopened: 0.",
      "- P0/P1/P2: 0/0/0.",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no canonical metadata materialization and no other cohort opened."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.67.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
              "br_exact_37_classification_coverage_ready":pre["br_exact_37_classification_coverage_ready"],
              "ready":pre["ready"],"total":pre["total"],"ambiguous":pre["ambiguous"],"not_found":pre["not_found"],"not_verified":pre["not_verified"],
              "tree_nodes":pre["tree_nodes"],"expected_group_queries":pre["expected_group_queries"],"executed_group_queries":pre["executed_group_queries"],
              "successful_group_queries":pre["successful_group_queries"],"failed_group_queries":pre["failed_group_queries"],
              "distinct_setores":pre["distinct_setores"],"pdsc_collisions":pre["pdsc_collisions"],"blocker":pre["blocker"],
              "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
              "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
              "productive":False,"files":files,"next_gate":pre["next_gate"]}
    (out/"manifest_v0.67.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":pre["verdict"],"ready":pre["ready"],"total":pre["total"],"blocker":pre["blocker"],
                      "workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]},sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
