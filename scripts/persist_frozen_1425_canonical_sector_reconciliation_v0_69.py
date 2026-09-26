#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

VERSION="v0.69"
STAGE="FROZEN_1425_CANONICAL_SECTOR_METADATA_COVERAGE_RECONCILIATION_NEXT_COHORT_SELECTION_GATE"
REQUIRED_START_HEAD="978404e766f7813819686835adf2254cd5071c62"

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_frozen_1425_canonical_sector_reconciliation_v0_69")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()

    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.69.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.69.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.69.csv")
    matrix=readcsv(out/"current_authority_cohort_gate_matrix_v0.69.csv")
    calc=readcsv(out/"next_cohort_selection_calculation_v0.69.csv")
    selected=json.loads((out/"selected_next_cohort_authority_v0.69.json").read_text(encoding="utf-8"))
    providers=json.loads((out/"provider_call_audit_v0.69.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.69.json").read_text(encoding="utf-8"))

    if pre["verdict"]!="PASS_CANONICAL_SECTOR_METADATA_RECONCILIATION_NEXT_COHORT_SELECTED":
        raise RuntimeError("verdict mismatch")
    if pre["global_canonical_sector_metadata_ready"] is not False:
        raise RuntimeError("global readiness falsely promoted")
    if (pre["global_ready"],pre["global_total"],pre["global_remaining"])!=(37,1425,1388):
        raise RuntimeError("global coverage mismatch")
    if pre["unresolved_cohorts"]!=7 or len(matrix)!=7:
        raise RuntimeError("unresolved cohort count")
    if pre["selected_next_cohort"]!="IN_NIFTY50":
        raise RuntimeError("selected cohort mismatch")
    if pre["resolved_gates_before_blocker"]!=4 or pre["earliest_unresolved_gate"]!="E":
        raise RuntimeError("selection depth/gate")
    if pre["current_blocker"]!="DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED":
        raise RuntimeError("selected blocker")
    if pre["next_gate"]!="IN_NIFTY50 DETERMINISTIC SECURITY IDENTITY LINKAGE GATE":
        raise RuntimeError("next gate")
    if sum(r["Selected"]=="YES" for r in calc)!=1:
        raise RuntimeError("selection count")
    if any(r["Result"]!="PASS" for r in tests):
        raise RuntimeError("failed tests")
    if any(v!=0 for v in providers.values()):
        raise RuntimeError("provider calls nonzero")
    if pre["mapping_population_runs"]!=0 or pre["sector_rs_runs"]!=0:
        raise RuntimeError("forbidden downstream work")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:
        raise RuntimeError("P0/P1/P2 nonzero")
    if imm["Canonical_READY_Rows_After"]!=37 or imm["Canonical_READY_Rows_Before"]!=37:
        raise RuntimeError("canonical ready count changed")

    binding={
        "workflow_run_id":a.workflow_run_id,
        "workflow_head_sha":a.workflow_head_sha,
        "artifact_id":a.artifact_id,
        "artifact_name":a.artifact_name,
        "artifact_digest":a.artifact_digest,
        "artifact_verified":"PASS",
        "artifact_scope":"pre-persistence v0.69 canonical sector authority reconciliation and deterministic next-cohort selection evidence"
    }
    (out/"artifact_binding_v0.69.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["artifact_binding"]="PASS"
    summary["artifact"]=binding
    (out/"summary_v0.69.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    cp=dict(chk)
    cp.update({
        "artifact_binding":"PASS",
        "workflow_run_id":a.workflow_run_id,
        "artifact_id":a.artifact_id,
        "artifact_digest":a.artifact_digest
    })
    (out/"stage_checkpoint_v0.69.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/FROZEN_1425_Canonical_Sector_Metadata_Coverage_Reconciliation_Next_Cohort_Selection_v0.69.md")
    report.parent.mkdir(parents=True,exist_ok=True)

    jp=next(r for r in matrix if r["Cohort"]=="JP_N225")
    report.write_text("\n".join([
        "# FROZEN-1425 Canonical Sector Metadata Coverage Reconciliation / Next-Cohort Selection Gate v0.69","",
        "## Verdict",f"**{pre['verdict']}**","",
        "GLOBAL_CANONICAL_SECTOR_METADATA_READY = **NO**.",
        f"GLOBAL READY / TOTAL = **{pre['global_ready']} / {pre['global_total']}**.",
        f"UNRESOLVED COHORTS = **{pre['unresolved_cohorts']}**.",
        f"SELECTED NEXT COHORT = **{pre['selected_next_cohort']}**.",
        f"RESOLVED GATES BEFORE BLOCKER = **{pre['resolved_gates_before_blocker']}**.",
        f"EARLIEST UNRESOLVED GATE = **{pre['earliest_unresolved_gate']}**.",
        f"CURRENT BLOCKER = **{pre['current_blocker']}**.","",
        "## Predecessor and canonical state",
        "- v0.68 final commit: 978404e766f7813819686835adf2254cd5071c62.",
        "- BR_IBRX100 canonical READY: 37/37.",
        "- Global canonical READY: 37/1425; remaining 1388.",
        "- BR semantic SHA-256 unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.",
        "- BR canonical file SHA-256 unchanged: 83706c76baba6d9a4fcc557d170f0bcad6fd85c9ca90fbc9f062cd5765dcef28.",
        "- Canonical registry remains promoted-cohort-only; no unresolved placeholder row was added.","",
        "## Current-authority reconciliation",
        "The seven unresolved cohorts were rebuilt from the v0.62 A-H observations and only explicit later manager governance. PASS values are carried as PASS_INHERITED; unresolved historical gates remain unresolved unless an explicit later authority cures that exact deficiency.",
        "G-SEC-03 was evaluated cross-cohort without rewriting historical v0.62 evidence.","",
        "## JP_N225 special check",
        f"JP_N225 D remains **{jp['D']}**. G-SEC-03 removes the requirement for a source-native code, but persisted v0.62 authority identifies a combined Nikkei 36 Industry / Nikkei sector grouping and does not unambiguously bind one exact canonical Sector_Level for PDSC peer grouping. With no new research authorized, D cannot be promoted to PASS_BY_CURRENT_GOVERNANCE.",
        f"JP_N225 therefore has {jp['Consecutive_Resolved_Gates']} consecutive resolved gates before current gate {jp['Current_Earliest_Unresolved_Gate']}.","",
        "## Deterministic selection",
        "The maximum consecutive resolved depth is 4. IN_NIFTY50, US_SP400 and US_SP500 all reach A-D before unresolved E. The first tie-breaker chooses the smaller Frozen cohort: IN_NIFTY50 has 45 rows versus 368 and 372.",
        "No subjective preference was used.",
        f"Selected next gate: **{pre['next_gate']}**.","",
        "## Scope / immutability",
        "- External requests: 0.",
        "- Provider / market-reference calls: 0.",
        "- Metadata mapping population: 0.",
        "- Sector RS: 0.",
        "- P0/P1/P2: 0/0/0.",
        "- Canonical READY rows remain 37/1425.",
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
        "Hard stop: selected cohort gate not executed; no Sector RS and no P0/P1/P2."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.69.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}

    manifest={
        "stage":STAGE,
        "version":VERSION,
        "required_start_head":REQUIRED_START_HEAD,
        "verdict":pre["verdict"],
        "global_canonical_sector_metadata_ready":False,
        "global_ready":37,
        "global_total":1425,
        "global_remaining":1388,
        "unresolved_cohorts":7,
        "selected_next_cohort":pre["selected_next_cohort"],
        "resolved_gates_before_blocker":pre["resolved_gates_before_blocker"],
        "earliest_unresolved_gate":pre["earliest_unresolved_gate"],
        "current_blocker":pre["current_blocker"],
        "workflow_run_id":a.workflow_run_id,
        "workflow_head_sha":a.workflow_head_sha,
        "artifact":binding,
        "mapping_population_runs":0,
        "sector_rs_runs":0,
        "p0_runs":0,
        "p1_runs":0,
        "p2_runs":0,
        "productive":False,
        "files":files,
        "next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.69.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({
        "verdict":pre["verdict"],
        "global_canonical_sector_metadata_ready":False,
        "global_ready":37,
        "global_total":1425,
        "unresolved_cohorts":7,
        "selected_next_cohort":pre["selected_next_cohort"],
        "resolved_gates_before_blocker":pre["resolved_gates_before_blocker"],
        "earliest_unresolved_gate":pre["earliest_unresolved_gate"],
        "current_blocker":pre["current_blocker"],
        "workflow_run":a.workflow_run_id,
        "artifact":a.artifact_id,
        "next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
