#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.80"
STAGE="JP_N225_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE"

def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p:Path,obj)->None:p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_jp_n225_source_access_evidence_persistence_v0_80")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=ROOT/a.output_dir
    pre=json.loads((out/"summary_preupload_v0.80.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.80.json").read_text(encoding="utf-8"))
    if pre["version"]!=VERSION or pre["stage"]!=STAGE:raise RuntimeError("preupload summary mismatch")
    if chk["verdict"]!=pre["verdict"]:raise RuntimeError("checkpoint mismatch")
    digest=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    binding={
      "artifact_id":a.artifact_id,"artifact_digest":digest,"artifact_name":a.artifact_name,
      "artifact_scope":"pre-persistence v0.80 JP_N225 Gate-H official-source access, bounded evidence persistence, provenance and operational policy evidence",
      "artifact_verified":"PASS","workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha
    }
    write_json(out/"artifact_binding_v0.80.json",binding)
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    write_json(out/"summary_v0.80.json",summary)
    cp=dict(chk);cp.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":digest,"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    write_json(out/"stage_checkpoint_v0.80.json",cp)

    verdict=summary["verdict"];ready="YES" if summary["jp_source_access_persistence_ready"] else "NO"
    public="YES" if summary["required_public_sources_ready"] else "NO"
    raw="YES" if summary["raw_persistence_required"] else "NO"
    bounded="YES" if summary["technical_bounded_evidence_sufficient"] else "NO"
    factsheet="YES" if summary["factsheet_required_for_canonical_audit"] else "NO"
    report=ROOT/"docs/validation/JP_N225_Source_Access_Evidence_Persistence_Gate_v0.80.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# JP_N225 Source Access / Evidence Persistence Gate v0.80","",
      "## Verdict",f"**{verdict}**","",
      f"JP_SOURCE_ACCESS_PERSISTENCE_READY = **{ready}**.",
      f"REQUIRED PUBLIC SOURCES READY = **{public}**.",
      f"RAW PERSISTENCE REQUIRED = **{raw}**.",
      f"BOUNDED EVIDENCE TECHNICALLY SUFFICIENT = **{bounded}**.",
      f"CANONICAL EVIDENCE PERSISTABLE = **{summary['canonical_evidence_persistable']}**.",
      f"OFFICIAL POLICY REVIEW = **{summary['official_policy_review']}**.",
      f"FACTSHEET REQUIRED FOR CANONICAL AUDIT = **{factsheet}**.","",
      "## G-SEC-05",
      "Gate H is treated as an operational source-access and evidence-persistence gate, not a legal opinion. Complete raw-source storage is not required. Unknown raw redistribution rights alone do not fail the gate when raw storage is unnecessary; an explicit official operational restriction that materially covers the required project behavior is fail-closed.","",
      "## Required source access",
      "Source A (Nikkei 225 components) and Source B (Nikkei 225 profile) remain publicly reproducible from same-day exact official unauthenticated GET evidence persisted by v0.79/v0.78. v0.80 intentionally made no core-source refetch after determining that recent exact evidence was sufficient. Public HTTP access is evaluated separately from use/persistence policy.","",
      "## Source drift",
      "The component page byte hash changed between v0.78 and v0.79, but v0.79 preserved 6 sectors, 36 industries, 225 unique security codes, 197/197 exact Frozen matches and 197/197 classifications. BYTE_DRIFT=YES; STRUCTURAL_DRIFT=NO; CLASSIFICATION_DRIFT=NO; AUTHORITY_REGRESSION_REVIEW_REQUIRED=NO.","",
      "## Bounded evidence",
      "Source A is technically auditable without full raw HTML because the repository already persists the official URL, retrieval timestamp, explicit update marker, response SHA256, exact Security Code, Industry_Raw, Sector_Raw, exact Frozen identity/match evidence and v0.79 authority commit. Source B is technically auditable without full profile HTML because its URL, retrieval timestamp, response SHA256, explicit 6-Sector/36-Industry structure and Sector-balance role are persisted. Source C factsheet is corroborating only and supplies no uniquely required canonical field.","",
      "## PDSC",
      "PDSC1 identifiers remain PROJECT_DERIVED_CANONICAL under PDSC_SHA256_V1. They are not Nikkei source-native codes and are not source authorization. The underlying official Sector name and hierarchy evidence remain subject to the official policy review.","",
      "## Source version / provenance contract",
      "Source A preserves the exact published source-update value Update：Sep/25/2026; retrieval time remains provenance only. Source B has no invented effective date and uses its deterministic SOURCE_SNAPSHOT_SHA256:<sha256> identifier. Future source names are normalized to NIKKEI_INDEXES_NIKKEI225_COMPONENTS and NIKKEI_INDEXES_NIKKEI225_PROFILE; prior v0.78 names are retained as explicit aliases, not silently replaced authority.","",
      "## Official policy review",
      "The bounded official Nikkei Indexes review found explicit operational restrictions relevant to the required pipeline. Official data-provision material states that copying/reprinting/reproduction of site contents is prohibited and that use beyond personal use or copyright-law quotation requires a license agreement. Official Non-Display Usage material states that use of Nikkei index data as input for automatic machine processing is subject to Nikkei permission/license. Official Display Usage material separately states that dissemination of constituent lists requires contracted data use. These findings are recorded as an operational comparison only; no legal conclusion is asserted.","",
      "The scope audit does not collapse these restrictions: ordinary public page access remains operationally available; URLs/hashes/timestamps are not treated as equivalent to raw redistribution; full/raw redistribution is separately restricted. However the planned pipeline programmatically processes source-derived Nikkei component/classification content and would persist bounded security-code/sector-name metadata. No Nikkei license or permission authority is present in repository governance. Fail-closed, canonical metadata evidence is therefore not currently persistable under project authority.","",
      "## Scope / immutability",
      "No Gate-F rerun, JP canonical materialization, canonical registry readiness update, SEC/NSE request, other-cohort execution, Sector RS or P0/P1/P2 occurred. IN_NIFTY50, US_SP400 and US_SP500 remain parked. JP Gate F remains 197/197. Global canonical READY remains 37/1425.","",
      "## Blocker",f"**{summary['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {digest}","",
      "## Next gate",
      f"**{summary['next_gate']}**","",
      "Hard stop: no JP canonical partition, registry promotion, next cohort, Sector RS or P0."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.80.json":
            files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    files["docs/validation/JP_N225_Source_Access_Evidence_Persistence_Gate_v0.80.md"]={"bytes":report.stat().st_size,"sha256":sha_file(report)}
    manifest={
      "version":VERSION,"stage":STAGE,"verdict":summary["verdict"],
      "jp_source_access_persistence_ready":summary["jp_source_access_persistence_ready"],
      "blocker":summary["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_digest":digest,"files":files,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"jp_canonical_rows":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0
    }
    write_json(out/"manifest_v0.80.json",manifest)
    return 0

if __name__=="__main__":raise SystemExit(main())
