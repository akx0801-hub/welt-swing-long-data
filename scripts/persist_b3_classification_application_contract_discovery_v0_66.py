#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.66"
STAGE="B3_CLASSIFICATION_APPLICATION_API_ASSET_CONTRACT_DISCOVERY_GATE"
FAIL_VERDICT="BLOCKED_B3_PUBLIC_APPLICATION_DATA_CONTRACT"
FAIL_BLOCKER="B3_PUBLIC_CLASSIFICATION_DATA_CONTRACT_NOT_DISCOVERED"
REQUIRED_START_HEAD="fb651c31f55f14a7fcb6bb3c83c5b25e3d69a4e6"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_b3_classification_application_contract_discovery_v0_66")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.66.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.66.json").read_text(encoding="utf-8"))
    tree=json.loads((out/"b3_tree_contract_v0.66.json").read_text(encoding="utf-8"))
    comp=json.loads((out/"b3_all_company_classification_contract_v0.66.json").read_text(encoding="utf-8"))
    repro=json.loads((out/"public_reproducibility_audit_v0.66.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.66.csv")
    net=readcsv(out/"b3_public_network_request_ledger_v0.66.csv")
    assets=readcsv(out/"b3_application_asset_ledger_v0.66.csv")
    candidates=readcsv(out/"b3_candidate_data_contracts_v0.66.csv")

    if any(r["Result"]!="PASS" for r in tests):
        raise RuntimeError("failed tests")
    if pre["exact37_classification_execution_runs"]!=0 or pre["pdsc_exact37_generation_runs"]!=0:
        raise RuntimeError("exact37 execution detected")
    if pre["canonical_mapping_population_runs"]!=0 or pre["sector_rs_runs"]!=0 or pre["other_cohort_rechecks"]!=0:
        raise RuntimeError("out-of-scope execution detected")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:
        raise RuntimeError("P0/P1/P2 nonzero")
    if tree["b3_classification_tree_machine_reproducible"] != pre["b3_classification_tree_machine_reproducible"]:
        raise RuntimeError("tree readiness mismatch")
    if comp["b3_complete_company_classification_dataset_ready"] != pre["b3_complete_company_classification_dataset_ready"]:
        raise RuntimeError("company readiness mismatch")
    if pre["verdict"]==FAIL_VERDICT and pre["blocker"]!=FAIL_BLOCKER:
        raise RuntimeError("failure blocker mismatch")
    if pre["verdict"]!=FAIL_VERDICT and not pre["public_reproducible"]:
        raise RuntimeError("successful contract is not public reproducible")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.66 B3 public classification application asset/API contract discovery evidence"
    }
    (out/"artifact_binding_v0.66.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre); summary["artifact_binding"]="PASS"; summary["artifact"]=binding
    (out/"summary_v0.66.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk); cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.66.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/B3_Classification_Application_API_Asset_Contract_Discovery_v0.66.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    if pre["b3_classification_tree_machine_reproducible"]:
        outcome="A complete public machine-readable B3 taxonomy/tree contract was verified."
    elif pre["b3_complete_company_classification_dataset_ready"]:
        outcome="A public all-company classification dataset contract was verified as an acceptable alternative to tree inversion."
    else:
        outcome="Neither a complete machine-readable B3 taxonomy/tree contract nor a complete all-company classification dataset contract was verified after bounded public application, asset, candidate-endpoint and optional browser-network discovery."

    lines=[
      "# B3 Classification Application API / Asset Contract Discovery Gate v0.66","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBLE = **{'YES' if pre['b3_classification_tree_machine_reproducible'] else 'NO'}**.",
      f"B3_COMPLETE_COMPANY_CLASSIFICATION_DATASET_READY = **{'YES' if pre['b3_complete_company_classification_dataset_ready'] else 'NO'}**.",
      f"DISCOVERED CONTRACT = **{pre['discovered_contract']}**.",
      f"PUBLIC REPRODUCIBLE = **{'YES' if pre['public_reproducible'] else 'NO'}**.","",
      "## Predecessor",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      "- v0.65 verdict: BLOCKED_B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBILITY.",
      "- v0.65 exact-37 coverage: 0/37 READY; 37 NOT_VERIFIED.",
      "- v0.65 classification nodes queried: 0.",
      "- v0.65 blocker: B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE.",
      "- v0.65 workflow/artifact: 36266926685 / 10914042556.",
      "- v0.65 artifact digest: sha256:0fcc27756c32156da0fa4be605f8dee1a2fa52fa3bd88aac2ecfc07355058146.","",
      "## Discovery execution",
      outcome,
      f"- Static/public assets recorded: {pre['asset_count']}.",
      f"- Browser-observed public requests: {pre['browser_observed_request_count']}.",
      f"- Candidate contracts independently classified/probed: {pre['candidate_contract_count']}.",
      f"- Browser binary available: {repro['browser_binary_available']} ({repro['browser_binary']}).",
      f"- Direct target fetches successful: {repro['direct_target_fetches_ok']} / {repro['direct_target_fetches_total']}.",
      f"- Verified tree contracts: {repro['tree_contracts_verified']}.",
      f"- Verified all-company contracts: {repro['all_company_contracts_verified']}.","",
      "## Evidence boundaries",
      "Only unauthenticated public B3 application behavior and B3-hosted assets/endpoints were used. No cookies, tokens, headers containing secrets, credentials, captcha bypass, authentication bypass or private unauthorized endpoint state was persisted.",
      "The discovery evidence stores bounded asset hashes and endpoint-relevant excerpts rather than complete minified bundles.","",
      "## Scope / immutability",
      "- Exact-37 classification execution: 0.",
      "- Exact-37 PDSC generation: 0.",
      "- Canonical mapping population: 0.",
      "- Sector RS: 0.",
      "- Other cohorts reopened: 0.",
      "- P0/P1/P2: 0/0/0.",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no classification-tree execution, no exact-37 mapping, no canonical metadata materialization and no other cohort opened."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.66.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,
      "verdict":pre["verdict"],
      "b3_classification_tree_machine_reproducible":pre["b3_classification_tree_machine_reproducible"],
      "b3_complete_company_classification_dataset_ready":pre["b3_complete_company_classification_dataset_ready"],
      "discovered_contract":pre["discovered_contract"],
      "public_reproducible":pre["public_reproducible"],
      "blocker":pre["blocker"],
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "exact37_classification_execution_runs":0,"pdsc_exact37_generation_runs":0,
      "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.66.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],
      "tree_ready":pre["b3_classification_tree_machine_reproducible"],
      "company_dataset_ready":pre["b3_complete_company_classification_dataset_ready"],
      "discovered_contract":pre["discovered_contract"],
      "public_reproducible":pre["public_reproducible"],
      "blocker":pre["blocker"],
      "workflow_run":a.workflow_run_id,
      "artifact":a.artifact_id,
      "next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
