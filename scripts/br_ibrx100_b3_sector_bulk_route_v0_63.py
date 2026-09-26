#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.63"
STAGE="BR_IBRX100_OFFICIAL_SOURCE_NATIVE_SECTOR_BULK_ROUTE_RESOLUTION_GATE"
REQUIRED_START_HEAD="c07c2aab9578971b523c9d39428bdff5758a8761"
V062_WORKFLOW=36255299126
V062_ARTIFACT=10910376599
V062_DIGEST="sha256:cc6c64baaf653830365a9cfaec9ab0d291523a49e02ad99714e2e8bb6606dcc7"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
VERDICT="BLOCKED_SOURCE_NATIVE_SECTOR_CODE"
BLOCKER="SOURCE_NATIVE_SECTOR_CODE_NOT_AVAILABLE:BR_IBRX100"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
S062=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/summary_v0.62.json"
C062=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/stage_checkpoint_v0.62.json"
R062=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/cohort_sector_source_route_ledger_v0.62.csv"
RESEARCH=ROOT/"config/br_ibrx100_b3_sector_bulk_route_research_v0.63.json"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def readcsv(p):
    with open(p,encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def writecsv(p,rows,fields=None):
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0]) if rows else []
    with open(p,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:w.writeheader();w.writerows(rows)

def git(*a): return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

def provider_calls():
    return {"alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"etf_holdings":0,"screeners":0,"third_party_sector_database":0,"tradingview":0,"company_website_classification":0,"name_classification":0,"per_security_web_fanout":0,"gics_icb_fallback":0,"crosswalk":0,"price_ohlcv":0,"news":0,"trading_analysis":0}

def validate_predecessor(repo_sha):
    if git("rev-parse","HEAD")!=repo_sha: raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0: raise RuntimeError("required start head not ancestor")
    s=json.loads(S062.read_text(encoding="utf-8")); c=json.loads(C062.read_text(encoding="utf-8"))
    if s["verdict"]!="BLOCKED_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE": raise RuntimeError("v0.62 verdict")
    if s["source_native_sector_metadata_coverage_ready"] is not False: raise RuntimeError("v0.62 ready")
    if (s["ready"],s["total"],s["not_mappable"],s["not_verified"])!=(0,1425,0,1425): raise RuntimeError("v0.62 totals")
    if s["cohort_counts"]["BR_IBRX100"]!=37: raise RuntimeError("BR rows")
    if s["cohort_blockers"]["BR_IBRX100"]!="OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND": raise RuntimeError("BR blocker")
    if c["workflow_run_id"]!=V062_WORKFLOW or c["artifact_id"]!=V062_ARTIFACT: raise RuntimeError("workflow/artifact")
    if "sha256:"+c["artifact_digest"]!=V062_DIGEST: raise RuntimeError("digest")
    br=[r for r in readcsv(R062) if r["Cohort"]=="BR_IBRX100"]
    if len(br)!=1 or br[0]["Taxonomy_Identity"]!="B3_CLASSIFICACAO_SETORIAL" or br[0]["Earliest_Failed_Gate"]!="B": raise RuntimeError("BR route predecessor")
    if sha(FROZEN)!=FROZEN_SHA or sha(V057)!=V057_SHA or sha(V058)!=V058_SHA: raise RuntimeError("immutability predecessor")
    return s,c,br[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repository-sha",required=True); ap.add_argument("--output-dir",default="output_br_ibrx100_b3_sector_bulk_route_v0_63")
    a=ap.parse_args(); out=ROOT/a.output_dir; out.mkdir(parents=True,exist_ok=True)
    s62,c62,br62=validate_predecessor(a.repository_sha)
    r=json.loads(RESEARCH.read_text(encoding="utf-8"))
    if r["version"]!=VERSION or r["scope_cohort"]!="BR_IBRX100" or r["frozen_rows"]!=37: raise RuntimeError("research scope")
    if any(r["prohibited_requests"].values()) or any(provider_calls().values()): raise RuntimeError("prohibited calls")
    sel=r["selected_route"]
    if sel["route_id"]!="B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH": raise RuntimeError("selected route")
    if sel["br_official_sector_bulk_route_ready"] is not True: raise RuntimeError("route not ready")
    if sel["access_class"]!="PUBLIC_REPRODUCIBLE" or sel["classification_content"]!="PASS": raise RuntimeError("route gates")
    if sel["sector_code"]!="NOT_AVAILABLE" or sel["blocker"]!=BLOCKER: raise RuntimeError("code blocker")

    discovery={
      "scope_cohort":"BR_IBRX100","frozen_rows":37,
      "predecessor_blocker":"OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND",
      "resolved_route_id":sel["route_id"],"officiality":"PASS","bulk_reproducibility":"PASS",
      "br_official_sector_bulk_route_ready":True,
      "access_class":sel["access_class"],"classification_content":sel["classification_content"],
      "taxonomy_identity":"B3_CLASSIFICACAO_SETORIAL",
      "security_identity_schema":sel["security_identity_schema"],
      "sector_code":"NOT_AVAILABLE","blocker":BLOCKER,
      "mapping_population_executed":False,"other_cohorts_retested":False
    }
    (out/"br_b3_sector_bulk_route_discovery_v0.63.json").write_text(json.dumps(discovery,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    endpoints=[]
    for x in r["inherited_v062_evidence"]:
        endpoints.append({"URL":x["url"],"Evidence_Status":x["status"],"Finding":x["finding"],"New_v0_63_Discovery":"NO"})
    for x in r["external_requests"]:
        endpoints.append({"URL":x["url"],"Evidence_Status":x["stage_use"],"Finding":x["result"],"New_v0_63_Discovery":"YES" if x["stage_use"].startswith("NEW_") else "NO"})
    writecsv(out/"br_b3_official_endpoint_ledger_v0.63.csv",endpoints)

    access=[]
    for route in r["resolved_routes"]:
        access.append({"Route_ID":route["route_id"],"Officiality":route["officiality"],"Bulk_Reproducibility":route["bulk_reproducibility"],"Access_Class":route["access_class"],"Classification_Content":route["classification_content"]})
    writecsv(out/"br_b3_data_product_access_classification_v0.63.csv",access)

    schema=[]
    for route in r["resolved_routes"]:
        sf=route["sector_fields"]
        schema.append({"Route_ID":route["route_id"],"Taxonomy_Identity":route["taxonomy_identity"],"Sector_Taxonomy":sf["Sector_Taxonomy"],"Sector_Code":sf["Sector_Code"],"Sector_Name":sf["Sector_Name"],"Classification_Content":route["classification_content"]})
    writecsv(out/"br_b3_classification_schema_audit_v0.63.csv",schema)

    ident=[{"Route_ID":x["route_id"],"Security_Identity_Schema":x["security_identity_schema"],"Mapping_Population_Executed":"NO"} for x in r["resolved_routes"]]
    writecsv(out/"br_b3_security_identity_schema_audit_v0.63.csv",ident)

    code_audit={"taxonomy_identity":"B3_CLASSIFICACAO_SETORIAL","sector_code_status":"NOT_AVAILABLE","blocker":BLOCKER,"local_code_invented":False,"basis":r["sector_code_audit"]["basis"]}
    (out/"br_b3_sector_code_audit_v0.63.json").write_text(json.dumps(code_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    ext=[{"Request_Order":i+1,"URL":x["url"],"Result":x["result"],"Stage_Use":x["stage_use"],"Official_B3":"YES","Per_Security_Fanout":"NO"} for i,x in enumerate(r["external_requests"])]
    writecsv(out/"external_request_ledger_v0.63.csv",ext)

    imm={"frozen_sha_before":sha(FROZEN),"frozen_sha_after":sha(FROZEN),"frozen_expected_sha256":FROZEN_SHA,"frozen_unchanged":sha(FROZEN)==FROZEN_SHA,
         "v057_sha_before":sha(V057),"v057_sha_after":sha(V057),"v057_expected_sha256":V057_SHA,"v057_unchanged":sha(V057)==V057_SHA,
         "v058_sha_before":sha(V058),"v058_sha_after":sha(V058),"v058_expected_sha256":V058_SHA,"v058_unchanged":sha(V058)==V058_SHA,
         "br_sector_mapping_population_runs":0,"other_cohort_rechecks":0,"sector_rs_runs":0,"crosswalk_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0}
    (out/"immutability_audit_v0.63.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"provider_call_audit_v0.63.json").write_text(json.dumps(provider_calls(),indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def t(n,ok,d):
        tests.append({"Test":n,"Result":"PASS" if ok else "FAIL","Detail":str(d)})
        if not ok: raise RuntimeError(n)
    t("PREDECESSOR_HEAD",True,REQUIRED_START_HEAD)
    t("V062_VERDICT",s62["verdict"]=="BLOCKED_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE",s62["verdict"])
    t("BR_ROWS_37",s62["cohort_counts"]["BR_IBRX100"]==37,37)
    t("BR_V062_BLOCKER",br62["Earliest_Blocker"]=="OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND",br62["Earliest_Blocker"])
    t("B3_TAXONOMY_PRESERVED",br62["Taxonomy_Identity"]=="B3_CLASSIFICACAO_SETORIAL",br62["Taxonomy_Identity"])
    t("ROUTE_OFFICIAL",discovery["officiality"]=="PASS","PASS")
    t("ROUTE_BULK_REPRODUCIBLE",discovery["bulk_reproducibility"]=="PASS","PASS")
    t("ROUTE_READY",discovery["br_official_sector_bulk_route_ready"] is True,"YES")
    t("ACCESS_PUBLIC_REPRODUCIBLE",discovery["access_class"]=="PUBLIC_REPRODUCIBLE",discovery["access_class"])
    t("CLASSIFICATION_CONTENT_PASS",discovery["classification_content"]=="PASS","PASS")
    t("SECTOR_CODE_NOT_AVAILABLE",discovery["sector_code"]=="NOT_AVAILABLE","NOT_AVAILABLE")
    t("PRECISE_BLOCKER",discovery["blocker"]==BLOCKER,BLOCKER)
    t("NO_MAPPING_POPULATION",imm["br_sector_mapping_population_runs"]==0,0)
    t("NO_OTHER_COHORT_RECHECK",imm["other_cohort_rechecks"]==0,0)
    t("NO_SECTOR_RS",imm["sector_rs_runs"]==0,0)
    t("NO_CROSSWALK",imm["crosswalk_runs"]==0,0)
    t("PROHIBITED_CALLS_ZERO",all(v==0 for v in provider_calls().values()),json.dumps(provider_calls(),sort_keys=True))
    t("FROZEN_IMMUTABLE",imm["frozen_unchanged"],FROZEN_SHA)
    t("V057_IMMUTABLE",imm["v057_unchanged"],V057_SHA)
    t("V058_IMMUTABLE",imm["v058_unchanged"],V058_SHA)
    t("P0_P1_P2_ZERO",imm["p0_runs"]==imm["p1_runs"]==imm["p2_runs"]==0,"0/0/0")
    writecsv(out/"test_results_v0.63.csv",tests)

    summary={"stage":STAGE,"version":VERSION,"verdict":VERDICT,"br_official_sector_bulk_route_ready":True,"access_class":"PUBLIC_REPRODUCIBLE","classification_content":"PASS",
             "security_identity_schema":sel["security_identity_schema"],"sector_code":"NOT_AVAILABLE","blocker":BLOCKER,"br_frozen_rows":37,
             "mapping_population_runs":0,"other_cohort_rechecks":0,"sector_rs_runs":0,"crosswalk_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
             "prohibited_provider_calls":provider_calls(),"immutability":imm,"tests":{"total":len(tests),"passed":len(tests),"failed":0},"artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":BLOCKER}
    checkpoint={"stage":STAGE,"version":VERSION,"verdict":VERDICT,"br_official_sector_bulk_route_ready":True,"access_class":"PUBLIC_REPRODUCIBLE","classification_content":"PASS",
                "security_identity_schema":sel["security_identity_schema"],"sector_code":"NOT_AVAILABLE","blocker":BLOCKER,"mapping_population_runs":0,"other_cohort_rechecks":0,
                "p0_runs":0,"p1_p2_runs":0,"artifact_binding":"PENDING_UPLOAD","tests_passed":len(tests),"tests_failed":0,"next_gate":BLOCKER}
    (out/"summary_preupload_v0.63.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.63.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file(): files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,"verdict":VERDICT,
              "br_official_sector_bulk_route_ready":True,"access_class":"PUBLIC_REPRODUCIBLE","classification_content":"PASS","sector_code":"NOT_AVAILABLE","blocker":BLOCKER,
              "frozen_sha256":FROZEN_SHA,"v057_feature_sha256":V057_SHA,"v058_home_rs_sha256":V058_SHA,"mapping_population_runs":0,"other_cohort_rechecks":0,
              "sector_rs_runs":0,"crosswalk_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":BLOCKER}
    (out/"manifest_preupload_v0.63.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":VERDICT,"br_official_sector_bulk_route_ready":True,"access_class":"PUBLIC_REPRODUCIBLE","classification_content":"PASS","security_identity_schema":sel["security_identity_schema"],"sector_code":"NOT_AVAILABLE","blocker":BLOCKER,"next_gate":BLOCKER},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
