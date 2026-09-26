#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

VERSION="v0.68"
STAGE="BR_IBRX100_CANONICAL_SECTOR_METADATA_MAPPING_MATERIALIZATION_GATE"
REQUIRED_START_HEAD="f27a8be1cea6ed38b3fe92a1ca3a15a54de6fd89"
CANONICAL=Path("sector_metadata/canonical/cohorts/BR_IBRX100_sector_metadata_v1.csv")
REGISTRY=Path("sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv")

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_br_ibrx100_canonical_sector_metadata_materialization_v0_68")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()

    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.68.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.68.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.68.csv")
    providers=json.loads((out/"provider_call_audit_v0.68.json").read_text(encoding="utf-8"))
    global_state=json.loads((out/"global_sector_metadata_coverage_status_v0.68.json").read_text(encoding="utf-8"))
    meta=json.loads((out/"br_canonical_sector_metadata_materialization_metadata_v0.68.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):
        raise RuntimeError("failed tests")
    if any(v!=0 for v in providers.values()):
        raise RuntimeError("provider calls nonzero")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:
        raise RuntimeError("downstream runs nonzero")
    if pre["br_canonical_sector_metadata_ready"]:
        if pre["verdict"]!="PASS_BR_CANONICAL_SECTOR_METADATA_MATERIALIZATION":
            raise RuntimeError("success verdict mismatch")
        if (pre["br_ready"],pre["br_total"],pre["global_ready"],pre["global_total"])!=(37,37,37,1425):
            raise RuntimeError("success coverage counts")
        if pre["global_canonical_sector_metadata_ready"] is not False:
            raise RuntimeError("global readiness falsely promoted")
        if pre["distinct_setores"]!=10 or pre["pdsc_collisions"]!=0:
            raise RuntimeError("success sector checks")
        if not pre["semantic_sha256"]:
            raise RuntimeError("semantic hash missing")
        if not CANONICAL.exists() or not REGISTRY.exists():
            raise RuntimeError("canonical files missing")
        if sha(CANONICAL)!=pre["canonical_file_sha256"]:
            raise RuntimeError("canonical file sha mismatch")
        rows=readcsv(CANONICAL)
        reg=readcsv(REGISTRY)
        if len(rows)!=37 or len({r["WS_ID"] for r in rows})!=37:
            raise RuntimeError("canonical rows")
        if any(r["Mapping_Status"]!="VERIFIED_CANONICAL" for r in rows):
            raise RuntimeError("mapping status")
        if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Canonical_Status"]!="READY":
            raise RuntimeError("registry")
        if reg[0]["Semantic_SHA256"]!=pre["semantic_sha256"]:
            raise RuntimeError("registry semantic sha")
        if global_state["GLOBAL_READY"]!=37 or global_state["GLOBAL_TOTAL"]!=1425 or global_state["GLOBAL_REMAINING"]!=1388:
            raise RuntimeError("global state")
    else:
        if not pre["blocker"]:
            raise RuntimeError("failure blocker absent")

    binding={
        "workflow_run_id":a.workflow_run_id,
        "workflow_head_sha":a.workflow_head_sha,
        "artifact_id":a.artifact_id,
        "artifact_name":a.artifact_name,
        "artifact_digest":a.artifact_digest,
        "artifact_verified":"PASS",
        "artifact_scope":"pre-persistence v0.68 BR IBrX100 canonical sector metadata materialization evidence plus canonical partition and registry"
    }
    (out/"artifact_binding_v0.68.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["artifact_binding"]="PASS"
    summary["artifact"]=binding
    (out/"summary_v0.68.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    cp=dict(chk)
    cp.update({
        "artifact_binding":"PASS",
        "workflow_run_id":a.workflow_run_id,
        "artifact_id":a.artifact_id,
        "artifact_digest":a.artifact_digest
    })
    (out/"stage_checkpoint_v0.68.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/BR_IBRX100_Canonical_Sector_Metadata_Mapping_Materialization_v0.68.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    br_ready="YES" if pre["br_canonical_sector_metadata_ready"] else "NO"
    report.write_text("\n".join([
        "# BR_IBRX100 Canonical Sector Metadata Mapping Materialization Gate v0.68","",
        "## Verdict",f"**{pre['verdict']}**","",
        f"BR_CANONICAL_SECTOR_METADATA_READY = **{br_ready}**.",
        f"BR READY / TOTAL = **{pre['br_ready']} / {pre['br_total']}**.",
        f"GLOBAL READY / TOTAL = **{pre['global_ready']} / {pre['global_total']}**.",
        "GLOBAL_CANONICAL_SECTOR_METADATA_READY = **NO**.",
        f"DISTINCT SETORES = **{pre['distinct_setores']}**.",
        f"SEMANTIC SHA256 = **{pre['semantic_sha256'] or 'NOT_GENERATED'}**.","",
        "## Governance",
        "G-SEC-04 authorizes incremental canonical Sector Metadata promotion only by complete Frozen cohort. Partial cohort rows and invented placeholder rows are forbidden. BR may be READY while global canonical coverage remains not ready. G-SEC-01, G-SEC-02 and G-SEC-03 remain preserved; Sector RS remains unauthorized.","",
        "## Source and transformation",
        "The canonical BR partition is materialized only from persisted v0.67 PROVABLY_MAPPABLE coverage evidence at final commit f27a8be1cea6ed38b3fe92a1ca3a15a54de6fd89. No B3 or other external reference request was executed in v0.68.",
        "Source_Name is B3_LISTED_COMPANIES_CLASSIFICATION. Source references retain the official v0.67 tree and group paths. Retrieval timestamps are retained solely as provenance and are not represented as a B3 business-effective date.","",
        "## Canonical partition",
        "- Path: sector_metadata/canonical/cohorts/BR_IBRX100_sector_metadata_v1.csv",
        f"- Rows: {pre['br_ready'] if pre['br_canonical_sector_metadata_ready'] else 0}",
        f"- Ordinary file SHA-256: {pre['canonical_file_sha256'] or 'NOT_GENERATED'}",
        f"- Semantic SHA-256: {pre['semantic_sha256'] or 'NOT_GENERATED'}",
        "- Mapping_Status: VERIFIED_CANONICAL for every promoted row.",
        "- Source_Sector_Code: NULL; PDSC is explicitly project-derived canonical identity, not a B3 source-native code.","",
        "## Exact-row and value checks",
        f"- duplicates: {pre['duplicates']}",
        f"- missing: {pre['missing']}",
        f"- extra: {pre['extra']}",
        f"- value mismatches vs v0.67: {pre['value_mismatches']}",
        f"- PDSC mismatches: {pre['pdsc_mismatches']}",
        f"- PDSC collisions: {pre['pdsc_collisions']}",
        f"- provenance failures: {pre['provenance_failures']}.","",
        "## Global canonical coverage",
        f"- BR promoted: {global_state['BR_READY']} / {global_state['BR_TOTAL']}",
        f"- Global promoted: {global_state['GLOBAL_READY']} / {global_state['GLOBAL_TOTAL']}",
        f"- Remaining unresolved: {global_state['GLOBAL_REMAINING']}",
        "- Registry scope is promoted canonical cohort partitions only; unresolved cohorts are omitted until promoted.",
        "- Sector-RS readiness is not inferred.","",
        "## Immutability / scope",
        "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
        "- v0.57 Feature Semantic SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
        "- v0.58 Home-Market-RS Semantic SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.",
        "- Sector RS / P0 / P1 / P2 runs: 0 / 0 / 0 / 0.",
        "- External market/reference requests: 0; B3 requests: 0; Alpha Vantage requests: 0.","",
        "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
        "## Artifact binding",
        f"- Workflow run: {a.workflow_run_id}",
        f"- Workflow head: {a.workflow_head_sha}",
        f"- Artifact: {a.artifact_id}",
        f"- Artifact name: {a.artifact_name}",
        f"- Artifact digest: {a.artifact_digest}","",
        "## Next gate",f"**{pre['next_gate']}**","",
        "Hard stop: no Sector RS, no P0/P1/P2 and no next cohort execution."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.68.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    if CANONICAL.exists():
        files[str(CANONICAL)]={"sha256":sha(CANONICAL),"bytes":CANONICAL.stat().st_size}
    if REGISTRY.exists():
        files[str(REGISTRY)]={"sha256":sha(REGISTRY),"bytes":REGISTRY.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}

    manifest={
        "stage":STAGE,
        "version":VERSION,
        "required_start_head":REQUIRED_START_HEAD,
        "verdict":pre["verdict"],
        "br_canonical_sector_metadata_ready":pre["br_canonical_sector_metadata_ready"],
        "br_ready":pre["br_ready"],
        "br_total":pre["br_total"],
        "global_ready":pre["global_ready"],
        "global_total":pre["global_total"],
        "global_canonical_sector_metadata_ready":False,
        "distinct_setores":pre["distinct_setores"],
        "semantic_sha256":pre["semantic_sha256"],
        "canonical_file_sha256":pre["canonical_file_sha256"],
        "blocker":pre["blocker"],
        "workflow_run_id":a.workflow_run_id,
        "workflow_head_sha":a.workflow_head_sha,
        "artifact":binding,
        "sector_rs_runs":0,
        "p0_runs":0,
        "p1_runs":0,
        "p2_runs":0,
        "productive":False,
        "files":files,
        "next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.68.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({
        "verdict":pre["verdict"],
        "br_canonical_sector_metadata_ready":pre["br_canonical_sector_metadata_ready"],
        "br_ready":pre["br_ready"],
        "br_total":pre["br_total"],
        "global_ready":pre["global_ready"],
        "global_total":pre["global_total"],
        "distinct_setores":pre["distinct_setores"],
        "semantic_sha256":pre["semantic_sha256"],
        "blocker":pre["blocker"],
        "workflow_run":a.workflow_run_id,
        "artifact":a.artifact_id,
        "next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
