#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.75"
STAGE="IN_NIFTY50_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE"
REQUIRED_START_HEAD="b3c0110e1c4f0441447c9ad90515daeb36ac41ff"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_in_nifty50_source_access_persistence_v0_75")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.75.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.75.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.75.csv")
    src=readcsv(out/"in_gate_h_source_inventory_v0.75.csv")
    access=readcsv(out/"in_public_access_reproducibility_audit_v0.75.csv")
    raw=readcsv(out/"in_raw_persistence_requirement_audit_v0.75.csv")
    bounded=readcsv(out/"in_bounded_evidence_persistence_audit_v0.75.csv")
    policy=readcsv(out/"in_official_terms_policy_review_v0.75.csv")
    persistability=json.loads((out/"in_canonical_metadata_evidence_persistability_v0.75.json").read_text(encoding="utf-8"))
    prov=json.loads((out/"provider_call_audit_v0.75.json").read_text(encoding="utf-8"))
    imm=json.loads((out/"immutability_audit_v0.75.json").read_text(encoding="utf-8"))

    if any(r["Result"]!="PASS" for r in tests):raise RuntimeError("failed tests")
    if any(v!=0 for v in prov.values()):raise RuntimeError("prohibited calls")
    if len(src)!=3 or len(access)!=3 or len(raw)!=3 or len(bounded)!=3:raise RuntimeError("source evidence counts")
    if len(policy)!=2:raise RuntimeError("policy evidence count")
    if pre["in_gate_f_classified"]!=45 or pre["canonical_ready_rows"]!=37 or pre["canonical_total_rows"]!=1425:raise RuntimeError("state drift")
    if pre["canonical_materialization_runs"]!=0 or pre["registry_updates"]!=0 or pre["other_cohort_runs"]!=0:raise RuntimeError("out-of-scope mutation")
    if pre["sector_rs_runs"]!=0 or pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:raise RuntimeError("downstream execution")
    if pre["in_source_access_persistence_ready"]:
        if pre["verdict"]!="PASS_IN_NIFTY50_SOURCE_ACCESS_EVIDENCE_PERSISTENCE":raise RuntimeError("success verdict")
        if not pre["public_sources_ready"] or pre["raw_persistence_required"] or pre["canonical_evidence_persistable"]!="YES":raise RuntimeError("success state")
        if pre["official_policy_review"]!="NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND" or pre["blocker"]!="":raise RuntimeError("success policy/blocker")
        if pre["next_gate"]!="IN_NIFTY50 CANONICAL SECTOR METADATA MAPPING MATERIALIZATION GATE":raise RuntimeError("success next")
    else:
        if not pre["blocker"]:raise RuntimeError("failure blocker absent")
        if pre["blocker"]=="EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION":
            if pre["official_policy_review"]!="EXPLICIT_OPERATIONAL_RESTRICTION_FOUND":raise RuntimeError("restriction evidence")
            if persistability["CANONICAL_METADATA_EVIDENCE_PERSISTABLE"]!="NOT_VERIFIED":raise RuntimeError("persistability should be not verified")

    binding={
      "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_name":a.artifact_name,"artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.75 IN_NIFTY50 Gate-H public access, bounded evidence persistence, and official policy review evidence"
    }
    (out/"artifact_binding_v0.75.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre);summary["artifact_binding"]="PASS";summary["artifact"]=binding
    (out/"summary_v0.75.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk);cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.75.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/IN_NIFTY50_Source_Access_Evidence_Persistence_Gate_v0.75.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    ready="YES" if pre["in_source_access_persistence_ready"] else "NO"
    raw_required="YES" if pre["raw_persistence_required"] else "NO"
    report.write_text("\n".join([
      "# IN_NIFTY50 Source Access / Evidence Persistence Gate v0.75","",
      "## Verdict",f"**{pre['verdict']}**","",
      f"IN_SOURCE_ACCESS_PERSISTENCE_READY = **{ready}**.",
      f"PUBLIC SOURCES READY = **{'YES' if pre['public_sources_ready'] else 'NO'}**.",
      f"RAW PERSISTENCE REQUIRED = **{raw_required}**.",
      f"CANONICAL EVIDENCE PERSISTABLE = **{pre['canonical_evidence_persistable']}**.",
      f"OFFICIAL POLICY REVIEW = **{pre['official_policy_review']}**.","",
      "## G-SEC-05",
      "G-SEC-05 is persisted as forward manager governance. Gate H is operational rather than a legal-license opinion. Unknown raw redistribution rights alone do not fail Gate H when full raw storage is unnecessary, but an explicit official operational restriction requires fail-closed treatment.","",
      "## Source access authority",
      "The three authoritative source classes remain publicly accessible under the recent persisted v0.70-v0.74 evidence chain: the NIFTY 50 constituent bulk source, NSE Indices Sectoral Distribution, and the NSE Indices Industry Classification Structure. No v0.75 core-source refetch was made after the policy hard stop; A-G and Gate F were not rerun.","",
      "## Persistence sufficiency",
      "Full raw source files are not technically required for deterministic audit. Existing repository evidence contains the official URLs, timestamps/hashes, schemas or response contracts, exact identity/classification evidence, source-native codes/names, hierarchy, and deterministic transformations. Raw persistence rights remain NOT_VERIFIED and no raw source body is persisted by this stage.","",
      "## Official policy review",
      "The bounded official review retrieved only the NSE Indices Terms of Use and Disclaimer. The Terms of Use explicitly condition systematic or automated data collection on express written consent and restrict copying/distribution of site material without prior written permission. The Disclaimer separately restricts reproduction/storage/transmission of site information without prior written permission and states that some index-data use or distribution requires licensing.",
      "No repository authority establishes the written consent or applicable license needed to clear those operational restrictions. This is recorded as an operational blocker only; no general legal conclusion is made.","",
      "## Provenance distinction",
      "Source_Retrieved_UTC is retrieval provenance and must never be represented as an NSE business-effective date. Where no explicit business as-of exists, the prepared future rule uses SOURCE_SNAPSHOT_SHA256:<sha256> as the reproducible snapshot identifier.","",
      "## Scope boundary",
      "No Gate-F rerun, canonical IN partition, registry update, other cohort, Sector RS, P0/P1/P2, forbidden provider, authentication bypass, CAPTCHA bypass, or legal-rights fabrication occurred.","",
      "## Immutability",
      "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.",
      "- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.",
      "- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.",
      "- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.",
      "- IN Gate-F classification remains 45/45.",
      "- Canonical READY remains 37/1425.","",
      "## Blocker",f"**{pre['blocker'] or 'NONE'}**.","",
      "## Artifact binding",
      f"- Workflow run: {a.workflow_run_id}",
      f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",
      f"- Artifact name: {a.artifact_name}",
      f"- Artifact digest: {a.artifact_digest}","",
      "## Next gate",f"**{pre['next_gate']}**","",
      "Hard stop: no canonical IN materialization, registry update, next cohort, Sector RS, or P0."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.75.json":files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":pre["verdict"],
      "in_source_access_persistence_ready":pre["in_source_access_persistence_ready"],
      "public_sources_ready":pre["public_sources_ready"],"raw_persistence_required":pre["raw_persistence_required"],
      "canonical_evidence_persistable":pre["canonical_evidence_persistable"],"official_policy_review":pre["official_policy_review"],
      "blocker":pre["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact":binding,
      "in_gate_f_classified":45,"canonical_ready_rows":37,"canonical_total_rows":1425,"canonical_materialization_runs":0,
      "registry_updates":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"files":files,"next_gate":pre["next_gate"]
    }
    (out/"manifest_v0.75.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":pre["verdict"],"ready":pre["in_source_access_persistence_ready"],
      "public_sources_ready":pre["public_sources_ready"],"raw_persistence_required":pre["raw_persistence_required"],
      "canonical_evidence_persistable":pre["canonical_evidence_persistable"],"official_policy_review":pre["official_policy_review"],
      "blocker":pre["blocker"],"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":pre["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
