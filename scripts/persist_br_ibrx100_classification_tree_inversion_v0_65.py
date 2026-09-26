#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.65"
STAGE="BR_IBRX100_B3_CLASSIFICATION_TREE_INVERSION_EXACT_37_SECTOR_COVERAGE_GATE"
VERDICT="BLOCKED_B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBILITY"
BLOCKER="B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE"
REQUIRED_START_HEAD="4e8151225f19ad1748c203b295e3ff699eabb7bf"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_br_ibrx100_classification_tree_inversion_v0_65")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.65.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.65.json").read_text(encoding="utf-8"))
    cov=readcsv(out/"br_exact_37_classification_coverage_v0.65.csv")
    nodes=readcsv(out/"b3_classification_node_ledger_v0.65.csv")
    reqs=readcsv(out/"b3_group_request_ledger_v0.65.csv")
    tests=readcsv(out/"test_results_v0.65.csv")
    tree=json.loads((out/"b3_classification_tree_snapshot_v0.65.json").read_text(encoding="utf-8"))

    if pre["verdict"]!=VERDICT or pre["blocker"]!=BLOCKER: raise RuntimeError("preupload verdict/blocker")
    if pre["br_exact_37_classification_coverage_ready"] is not False: raise RuntimeError("ready unexpectedly true")
    if (pre["ready"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"])!=(0,37,0,0,37): raise RuntimeError("coverage counts")
    if pre["classification_nodes_queried"]!=0 or pre["distinct_setores"]!=0: raise RuntimeError("node/sector counts")
    if tree["capture_status"]!="INCOMPLETE_NOT_MACHINE_REPRODUCIBLE": raise RuntimeError("tree status")
    if len(cov)!=37 or any(r["Coverage_Status"]!="NOT_VERIFIED" for r in cov): raise RuntimeError("coverage rows")
    if any(r["Sector_Code"]!="NOT_GENERATED_WITHOUT_PROVABLY_MAPPABLE_ROW" for r in cov): raise RuntimeError("premature PDSC")
    if len(nodes)==0: raise RuntimeError("partial node evidence missing")
    if len(reqs)!=1 or reqs[0]["Retrieval_Status"]!="STOPPED_BEFORE_PARTIAL_TRAVERSAL": raise RuntimeError("group request ledger")
    if any(r["Result"]!="PASS" for r in tests): raise RuntimeError("failed tests")
    if any(pre["prohibited_provider_calls"].values()): raise RuntimeError("prohibited calls")
    if pre["canonical_mapping_population_runs"]!=0 or pre["sector_rs_runs"]!=0 or pre["other_cohort_rechecks"]!=0: raise RuntimeError("scope run")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0: raise RuntimeError("P0/P1/P2")

    binding={"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,
             "artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,"artifact_verified":"PASS",
             "artifact_scope":"pre-persistence v0.65 BR IBrX100 B3 classification-tree inversion evidence"}
    (out/"artifact_binding_v0.65.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre); summary["artifact_binding"]="PASS"; summary["artifact"]=binding
    (out/"summary_v0.65.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk); cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.65.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/BR_IBRX100_B3_Classification_Tree_Inversion_Exact_37_Sector_Coverage_v0.65.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join([
      "# BR_IBRX100 B3 Classification-Tree Inversion / Exact-37 Sector Coverage Gate v0.65","",
      "## Verdict",f"**{VERDICT}**","",
      "BR_EXACT_37_CLASSIFICATION_COVERAGE_READY = **NO**.",
      "READY / TOTAL = **0 / 37**.",
      "AMBIGUOUS = **0**.",
      "NOT_FOUND = **0**.",
      "NOT_VERIFIED = **37**.",
      "CLASSIFICATION NODES QUERIED = **0**.",
      "DISTINCT SETORES = **0**.","",
      "## Predecessor lock",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      "- v0.64 exact-37 readiness: NO, 0/37 ready, 37 NOT_VERIFIED.",
      "- v0.64 security -> company identity: 37/37 PASS.",
      "- Taxonomy / level / code method: B3_CLASSIFICACAO_SETORIAL / SETOR_ECONOMICO / PDSC_SHA256_V1.",
      "- v0.64 workflow/artifact: 36264343312 / 10913620188.",
      "- v0.64 artifact digest: sha256:970d4c510642f5803ca4228fe2715d10661fc8733c7eb7fee5e1ad94d700678c.","",
      "## Tree-capture result",
      "The official B3 root listed-companies application was machine-retrievable only as a partial rendered subsetor/segment slice. The official /classification endpoint was reachable but the bounded machine-readable extraction yielded an empty client-rendered shell. No complete official Setor Econômico -> Subsetor -> Segmento payload could be sealed.",
      "A partial traversal would not prove that all official queryable leaf nodes were included, so fail-closed execution stopped before group-level coverage requests.","",
      "## Query encoding",
      "The segment query encoding was independently reproduced for the existing official Agricultura and Minerais Metálicos examples. The verified mechanism is URLENCODE(BASE64(UTF8(encodeURIComponent(exact official label)))). No query-token guessing was used.",
      "This does not cure the missing complete official node inventory.","",
      "## Coverage consequence",
      "No company-driven requests and no 37-security page fanout were executed. The inherited 37 exact B3 company codes remain valid, but without a complete sealed taxonomy-node set the inversion cannot prove exhaustive company-code membership.",
      f"Smallest evidenced blocker: **{BLOCKER}**.","",
      "## PDSC",
      "PDSC generation is restricted to PROVABLY_MAPPABLE exact-37 rows. Since READY=0, no exact-37 PDSC code was generated; the determinism/collision evidence records NOT_APPLICABLE for this failed stage.","",
      "## Immutability",
      "- Canonical BR mapping population: 0",
      "- Sector RS: 0",
      "- Other cohorts reopened: 0",
      "- P0/P1/P2: 0/0/0",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{BLOCKER}**","",
      "Hard stop: no canonical sector metadata materialization and no other cohort opened."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.65.json": files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":VERDICT,
              "br_exact_37_classification_coverage_ready":False,"ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
              "classification_nodes_queried":0,"distinct_setores":0,"blocker":BLOCKER,
              "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
              "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,
              "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":BLOCKER}
    (out/"manifest_v0.65.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":VERDICT,"br_exact_37_classification_coverage_ready":False,"ready":0,"total":37,
                      "ambiguous":0,"not_found":0,"not_verified":37,"classification_nodes_queried":0,"distinct_setores":0,
                      "blocker":BLOCKER,"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":BLOCKER},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
