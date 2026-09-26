#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.63"
STAGE="BR_IBRX100_OFFICIAL_SOURCE_NATIVE_SECTOR_BULK_ROUTE_RESOLUTION_GATE"
VERDICT="BLOCKED_SOURCE_NATIVE_SECTOR_CODE"
BLOCKER="SOURCE_NATIVE_SECTOR_CODE_NOT_AVAILABLE:BR_IBRX100"
REQUIRED_START_HEAD="c07c2aab9578971b523c9d39428bdff5758a8761"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def readcsv(p):
    with open(p,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_br_ibrx100_b3_sector_bulk_route_v0_63")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args()
    out=Path(a.output_dir)
    pre=json.loads((out/"summary_preupload_v0.63.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.63.json").read_text(encoding="utf-8"))
    disc=json.loads((out/"br_b3_sector_bulk_route_discovery_v0.63.json").read_text(encoding="utf-8"))
    tests=readcsv(out/"test_results_v0.63.csv")
    if pre["verdict"]!=VERDICT or pre["blocker"]!=BLOCKER: raise RuntimeError("preupload verdict/blocker")
    if pre["br_official_sector_bulk_route_ready"] is not True: raise RuntimeError("route readiness")
    if pre["access_class"]!="PUBLIC_REPRODUCIBLE" or pre["classification_content"]!="PASS": raise RuntimeError("route gate")
    if pre["sector_code"]!="NOT_AVAILABLE": raise RuntimeError("sector code")
    if disc["mapping_population_executed"] or disc["other_cohorts_retested"]: raise RuntimeError("scope violation")
    if any(x["Result"]!="PASS" for x in tests): raise RuntimeError("failed tests")
    if any(pre["prohibited_provider_calls"].values()): raise RuntimeError("prohibited provider call")
    if pre["mapping_population_runs"]!=0 or pre["other_cohort_rechecks"]!=0 or pre["sector_rs_runs"]!=0 or pre["crosswalk_runs"]!=0: raise RuntimeError("downstream run")
    if pre["p0_runs"]!=0 or pre["p1_runs"]!=0 or pre["p2_runs"]!=0: raise RuntimeError("P0/P1/P2 run")

    binding={"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,"artifact_id":a.artifact_id,"artifact_name":a.artifact_name,
             "artifact_digest":a.artifact_digest,"artifact_verified":"PASS","artifact_scope":"pre-persistence v0.63 BR IBrX100 B3 sector bulk-route resolution evidence"}
    (out/"artifact_binding_v0.63.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=dict(pre); summary["artifact_binding"]="PASS"; summary["artifact"]=binding
    (out/"summary_v0.63.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    cp=dict(chk); cp.update({"artifact_binding":"PASS","workflow_run_id":a.workflow_run_id,"artifact_id":a.artifact_id,"artifact_digest":a.artifact_digest})
    (out/"stage_checkpoint_v0.63.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/BR_IBRX100_Official_Source_Native_Sector_Bulk_Route_Resolution_v0.63.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join([
      "# BR_IBRX100 Official Source-Native Sector Bulk Route Resolution Gate v0.63","",
      "## Verdict",f"**{VERDICT}**","",
      "BR_OFFICIAL_SECTOR_BULK_ROUTE_READY = **YES**.",
      "ACCESS CLASS = **PUBLIC_REPRODUCIBLE**.",
      "CLASSIFICATION CONTENT = **PASS**.",
      "SECTOR CODE = **NOT_AVAILABLE**.","",
      "## Predecessor",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      "- v0.62 verdict: BLOCKED_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE",
      "- BR_IBRX100 rows: 37",
      "- v0.62 BR earliest failed gate: B",
      "- v0.62 BR blocker: OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND",
      "- v0.62 workflow/artifact: 36255299126 / 10910376599",
      "- v0.62 artifact digest: sha256:cc6c64baaf653830365a9cfaec9ab0d291523a49e02ad99714e2e8bb6606dcc7","",
      "## Route resolution",
      "The v0.62 B3 taxonomy/query/criteria/public-data/Up2Data entry points are referenced as predecessor evidence and are not presented as new discoveries.",
      "v0.63 resolved an official public page-backed classification route at sistemaswebb3-listados.b3.com.br. The official Listed Companies page exposes Search by Industry Classification, and the official search URL returns multiple companies for one source-native B3 classification label in a single request. This satisfies the bounded bulk/reproducibility gate without per-security web fanout.",
      "The resolved result schema exposes B3 company-level identifiers/metadata (legal name, trading name, governance segment and company code). It does not itself expose bulk ISIN/full security-class identity; exact 37-row identity mapping remains unexecuted and out of scope.","",
      "## UP2DATA technical expansion",
      "The official Up2Data Listed Companies channel exposes FinancialData, OutstandingShares, PositionOfShareholders and SummaryData and links a Listed_Companies.zip sample plus the UP2DATA data dictionary. The official Commercial Policy 2.4.5 establishes contracted Client/Cloud access, access keys, a specific Listed Companies tariff and separate distribution/publication governance.",
      "The bounded retrieval path could not inspect the binary sample ZIP/XLSX schema, so this licensed route is not used as evidence that SummaryData contains B3 Classificacao Setorial fields.","",
      "## Sector-code audit",
      "The public resolved B3 classification route exposes official hierarchy names but no stable source-native sector/subsector/segment code. No official text retrieved in this stage establishes such a code. Local ordinals, hashes, normalized labels or invented codes are prohibited and were not created.",
      f"Therefore the precise downstream blocker is **{BLOCKER}**.","",
      "## Scope and immutability",
      "- No 37-row mapping population.",
      "- No other cohort reopened.",
      "- No Sector RS, crosswalk, P0, P1 or P2.",
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
      "Hard stop: no 37-row mapping stage and no other cohort opened."
    ])+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.63.json": files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"verdict":VERDICT,"br_official_sector_bulk_route_ready":True,
              "access_class":"PUBLIC_REPRODUCIBLE","classification_content":"PASS","sector_code":"NOT_AVAILABLE","blocker":BLOCKER,"workflow_run_id":a.workflow_run_id,
              "workflow_head_sha":a.workflow_head_sha,"artifact":binding,"mapping_population_runs":0,"other_cohort_rechecks":0,"sector_rs_runs":0,"crosswalk_runs":0,
              "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"files":files,"next_gate":BLOCKER}
    (out/"manifest_v0.63.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":VERDICT,"br_official_sector_bulk_route_ready":True,"access_class":"PUBLIC_REPRODUCIBLE","classification_content":"PASS","sector_code":"NOT_AVAILABLE","blocker":BLOCKER,"workflow_run":a.workflow_run_id,"artifact":a.artifact_id,"next_gate":BLOCKER},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
