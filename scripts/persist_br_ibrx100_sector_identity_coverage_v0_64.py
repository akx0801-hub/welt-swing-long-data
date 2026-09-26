#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

VERSION="v0.64"
STAGE="BR_IBRX100_CANONICAL_SECTOR_KEY_SECURITY_IDENTITY_EXACT_37_COVERAGE_GATE"
VERDICT="BLOCKED_EXACT_37_CLASSIFICATION_COVERAGE"
BLOCKER="BR_EXACT_37_COVERAGE_INCOMPLETE"
METHOD="PDSC_SHA256_V1"
REQUIRED_START_HEAD="f0a67388740b17dd62b47f1163df76d503a9c50b"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def readcsv(p: Path):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_br_ibrx100_sector_identity_coverage_v0_64")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()

    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.64.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.64.json").read_text(encoding="utf-8"))
    cov=readcsv(out/"br_exact_37_coverage_audit_v0.64.csv")
    ident=readcsv(out/"br_security_company_identity_audit_v0.64.csv")
    det=readcsv(out/"canonical_sector_code_determinism_test_v0.64.csv")
    col=json.loads((out/"canonical_sector_code_collision_audit_v0.64.json").read_text(encoding="utf-8"))
    level=json.loads((out/"br_b3_sector_level_binding_v0.64.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.64.csv")

    if pre["verdict"]!=VERDICT or pre["blocker"]!=BLOCKER:
        raise RuntimeError("preupload verdict/blocker mismatch")
    if pre["br_sector_identity_coverage_ready"] is not False:
        raise RuntimeError("readiness unexpectedly true")
    if (pre["ready"],pre["total"],pre["ambiguous"],pre["not_found"],pre["not_verified"])!=(0,37,0,0,37):
        raise RuntimeError("coverage totals mismatch")
    if pre["sector_code_method"]!=METHOD:
        raise RuntimeError("sector code method mismatch")
    if pre["security_to_company_ready"]!=37:
        raise RuntimeError("security-to-company readiness mismatch")
    if len(ident)!=37 or any(r["Security_To_Company_Status"]!="PASS" for r in ident):
        raise RuntimeError("security-to-company audit mismatch")
    if any(r["Company_Name_Join_Used"]!="NO" for r in ident):
        raise RuntimeError("company-name join detected")
    if len(cov)!=37 or any(r["Coverage_Status"]!="NOT_VERIFIED" for r in cov):
        raise RuntimeError("exact-37 coverage audit mismatch")
    if any(r["Sector_Code"]!="NOT_GENERATED_WITHOUT_VERIFIED_SECTOR_NAME" for r in cov):
        raise RuntimeError("premature canonical code generation")
    if level["Sector_Level"]!="SETOR_ECONOMICO" or level["Subsetor_Used"]!="NO" or level["Segmento_Used"]!="NO":
        raise RuntimeError("sector-level binding mismatch")
    if any(r["Deterministic"]!="PASS" for r in det) or col["result"]!="PASS" or col["collisions"]!=0:
        raise RuntimeError("PDSC validation mismatch")
    if any(r["Result"]!="PASS" for r in tests):
        raise RuntimeError("cannot persist failed tests")
    if any(pre["prohibited_provider_calls"].values()):
        raise RuntimeError("prohibited provider call nonzero")
    if pre["canonical_mapping_population_runs"]!=0 or pre["sector_rs_runs"]!=0 or pre["other_cohort_rechecks"]!=0:
        raise RuntimeError("out-of-scope execution detected")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0:
        raise RuntimeError("P0/P1/P2 nonzero")

    binding={
      "workflow_run_id":a.workflow_run_id,
      "workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,
      "artifact_name":a.artifact_name,
      "artifact_digest":a.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.64 BR IBrX100 canonical sector key / exact-37 identity coverage evidence"
    }
    (out/"artifact_binding_v0.64.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre); summary["artifact_binding"]="PASS"; summary["artifact"]=binding
    (out/"summary_v0.64.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk); cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.64.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/BR_IBRX100_Canonical_Sector_Key_Security_Identity_Exact_37_Coverage_v0.64.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join([
      "# BR_IBRX100 Canonical Sector Key + Security Identity / Exact-37 Coverage Gate v0.64","",
      "## Verdict",f"**{VERDICT}**","",
      "BR_SECTOR_IDENTITY_COVERAGE_READY = **NO**.",
      "READY / TOTAL = **0 / 37**.",
      "AMBIGUOUS = **0**.",
      "NOT_FOUND = **0**.",
      "NOT_VERIFIED = **37**.",
      f"SECTOR CODE METHOD = **{METHOD}**.","",
      "## Predecessor",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      "- v0.63 route: B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH",
      "- v0.63 route readiness: YES",
      "- v0.63 access: PUBLIC_REPRODUCIBLE",
      "- v0.63 classification content: PASS",
      "- v0.63 source-native Sector_Code: NOT_AVAILABLE",
      "- v0.63 workflow/artifact: 36258067350 / 10911387342",
      "- v0.63 artifact digest: sha256:0ec10e147c619ec999af1b8de3dcd34b93d4fff29c3f6a96dd672bcb05446535","",
      "## G-SEC-03 forward governance",
      "G-SEC-03 permits PDSC_SHA256_V1 when an authorized official taxonomy has an exact sector classification but no stable source-native Sector_Code. This changes forward governance only; historical v0.63 evidence is unchanged.",
      "For absent native code the audit state is Source_Sector_Code=NULL, Sector_Code_Origin=PROJECT_DERIVED_CANONICAL, Sector_Code_Method=PDSC_SHA256_V1.","",
      "## Security -> company identity",
      "All 37 Frozen BR rows are exact BVMF ordinary-share tickers already present in the official B3 IBrX100 source lineage. The official B3 share-code convention XXXXY defines the first four letters as the issuer/company code and 3 as ordinary share. The stage therefore derives the B3 company code from the exact official ticker without a company-name join.",
      "Security -> company status: **37 / 37 PASS**.",
      "Fuzzy matching: NO. Company-name joins: NO. Per-security web fanout: NO.","",
      "## Sector level binding",
      "Sector_Taxonomy = B3_CLASSIFICACAO_SETORIAL.",
      "Sector_Level = SETOR_ECONOMICO, bound to B3's first-level Setor Econômico. Subsetor and Segmento are not substituted for the canonical Sector level.","",
      "## PDSC_SHA256_V1 validation",
      "The contract uses NFC only, U+001F separators, UTF-8 and full lowercase SHA-256 in the form PDSC1:<sha256>. Three official B3 sector-label method vectors were generated twice independently and were deterministic with zero collisions among the tested vectors.",
      "These vectors validate the identifier method only; they are not claimed as exact-37 cohort coverage evidence.","",
      "## Exact-37 company -> classification coverage",
      "The already-authorized B3 classification route remains official and reproducible at route-design level. However, the bounded execution environment did not yield a sealable row-complete all-company classification payload containing the exact official Sector_Name for every one of the 37 company codes.",
      "The stage did not substitute 37 per-security web lookups. Consequently every row remains NOT_VERIFIED for exact company -> Sector_Name coverage, and no per-row PDSC canonical Sector_Code is generated.",
      f"Smallest evidenced blocker: **{BLOCKER}**.","",
      "## Immutability / scope",
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
      "Hard stop: no canonical BR mapping materialization and no other cohort opened."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.64.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":VERDICT,
      "br_sector_identity_coverage_ready":False,"ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
      "sector_code_method":METHOD,"blocker":BLOCKER,"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact":binding,"canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":BLOCKER
    }
    (out/"manifest_v0.64.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":VERDICT,"br_sector_identity_coverage_ready":False,"ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
                      "sector_code_method":METHOD,"blocker":BLOCKER,"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":BLOCKER},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
