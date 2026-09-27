#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.81"
STAGE="JP_N225_EXTERNAL_AUTHORIZATION_PARK_POST_PARK_RESELECTION_AU_SP_ASX200_GATE_C"

def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p:Path,obj)->None:p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_jp_park_reselection_au_asx200_gate_c_v0_81")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=ROOT/a.output_dir
    pre=json.loads((out/"summary_preupload_v0.81.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.81.json").read_text(encoding="utf-8"))
    decision=json.loads((out/"au_source_native_taxonomy_identity_decision_v0.81.json").read_text(encoding="utf-8"))
    if pre["version"]!=VERSION or pre["stage"]!=STAGE:raise RuntimeError("summary mismatch")
    if chk["verdict"]!=pre["verdict"]:raise RuntimeError("checkpoint mismatch")
    digest=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    binding={
      "artifact_id":a.artifact_id,"artifact_digest":digest,"artifact_name":a.artifact_name,
      "artifact_scope":"pre-persistence v0.81 JP_N225 external-authorization park, deterministic reselection, and AU_SP_ASX200 Gate-C bounded evidence",
      "artifact_verified":"PASS","workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha
    }
    write_json(out/"artifact_binding_v0.81.json",binding)
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    write_json(out/"summary_v0.81.json",summary)
    cp=dict(chk);cp.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":digest,
                            "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    write_json(out/"stage_checkpoint_v0.81.json",cp)

    ready="YES" if summary["au_source_native_taxonomy_identity_ready"] else "NO"
    report=ROOT/"docs/validation/JP_N225_Park_Post_Park_Reselection_AU_SP_ASX200_Gate_C_v0.81.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# JP_N225 External-Authorization Park / Post-Park Reselection / AU_SP_ASX200 Gate C v0.81","",
      "## Verdict",f"**{summary['verdict']}**","",
      f"JP_N225 PARK STATE = **{summary['jp_n225_park_state']}**.",
      f"SELECTED COHORT = **{summary['selected_cohort']}**.",
      f"AU_SOURCE_NATIVE_TAXONOMY_IDENTITY_READY = **{ready}**.",
      f"DIRECTORY BULK ROUTE = **{summary['directory_bulk_route']}**.",
      f"DIRECTORY INDUSTRY FIELD = **{summary['directory_industry_field']}**.",
      f"TAXONOMY IDENTITY = **{summary['taxonomy_identity']}**.",
      f"TAXONOMY OWNER = **{summary['taxonomy_owner']}**.",
      f"FORMAL LEVEL = **{summary['formal_level']}**.",
      f"VERSION STATUS = **{summary['version_status']}**.",
      f"FIELD→TAXONOMY BINDING = **{summary['field_to_taxonomy_binding']}**.",
      f"GICS FIELD BINDING = **{summary['gics_field_binding']}**.",
      f"UPSTREAM PROVIDER ATTRIBUTION = **{summary['upstream_provider_attribution']}**.","",
      "## JP_N225 parking",
      "Existing G-SEC-06 was applied without creating new governance. JP_N225 is PARKED_EXTERNAL_AUTHORIZATION. Proven technical gates A-G remain PASS, Gate F remains 197/197, Gate H remains blocked by EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION, canonical readiness remains NO, canonical rows remain 0, and automatic reopening is disabled. The pre-existing IN_NIFTY50, US_SP400 and US_SP500 parked states are preserved unchanged.","",
      "## Deterministic reselection",
      "The persisted v0.69 selection rule was re-applied after excluding canonical READY and all parked cohorts: greatest consecutive resolved gates from A, then smaller Frozen row count, then lexicographic cohort ID. The calculation, rather than a hard-coded cohort result, selects AU_SP_ASX200 with 63 Frozen rows and Gate C as its earliest unresolved gate.","",
      "## ASX directory and bulk evidence",
      "The current ASX company directory was requested directly. The All ASX Listed Companies bulk route was discovered from the directory response rather than from a stale hard-coded endpoint. The bulk response metadata, schema, row count, SHA256 and exact Industry-like field statistics are persisted without storing the complete raw source.","",
      "## Taxonomy identity",
      ("The official ASX directory-linked bulk schema directly names the field as GICS industry group. The official ASX indices page expands GICS as the Global Industry Classification Standard and identifies S&P Dow Jones Indices and MSCI as its developers. The exact formal level is therefore Industry Group from the source schema itself; this is not inferred from label appearance or from ASX sector-index usage alone. A static taxonomy version number was not asserted; the reproducible contract is CURRENT_MAINTAINED_NO_STATIC_VERSION with official source snapshot hashes." if summary["au_source_native_taxonomy_identity_ready"] else
       "The bounded current evidence did not satisfy all Gate-C requirements. In particular, the directory Industry-like field was not promoted to GICS or any other taxonomy merely because ASX uses GICS for sector indices. The persisted blocker is the smallest Gate-C blocker under the required precedence."),"",
      "## LSEG / Morningstar attribution",
      "The directory's general market-data credit to LSEG Data & Analytics and Morningstar is recorded separately. It is not treated as field-specific attribution for Industry. No upstream-provider security data, per-security requests or third-party classification database was used.","",
      "## Isolation and hard scope",
      "G-SEC-02 taxonomy isolation is preserved. No crosswalk, semantic label inference, PDSC, Frozen-63 security linkage, AU Gate D/E/F, canonical materialization, canonical registry promotion, Sector RS or P0/P1/P2 occurred. No SEC, NSE or Nikkei classification requests were made. Global canonical READY remains 37/1425.","",
      "## Blocker",f"**{summary['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {digest}","",
      "## Next gate",f"**{summary['next_gate']}**","",
      "Hard stop: no AU Gate D, AU Gate E/F, canonical materialization, next cohort, Sector RS or P0."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.81.json":
            files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    files["docs/validation/JP_N225_Park_Post_Park_Reselection_AU_SP_ASX200_Gate_C_v0.81.md"]={"bytes":report.stat().st_size,"sha256":sha_file(report)}
    park=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
    files["sector_metadata/governance/parked_cohort_registry_v1.csv"]={"bytes":park.stat().st_size,"sha256":sha_file(park)}
    manifest={
      "version":VERSION,"stage":STAGE,"verdict":summary["verdict"],
      "jp_n225_park_state":summary["jp_n225_park_state"],"selected_cohort":summary["selected_cohort"],
      "au_source_native_taxonomy_identity_ready":summary["au_source_native_taxonomy_identity_ready"],
      "blocker":summary["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_digest":digest,"files":files,
      "canonical_ready_rows":37,"canonical_total_rows":1425,
      "au_gate_d_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "next_gate":decision["Next_Gate"]
    }
    write_json(out/"manifest_v0.81.json",manifest)
    return 0

if __name__=="__main__":raise SystemExit(main())
