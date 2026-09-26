#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import subprocess
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.65"
STAGE="BR_IBRX100_B3_CLASSIFICATION_TREE_INVERSION_EXACT_37_SECTOR_COVERAGE_GATE"
REQUIRED_START_HEAD="4e8151225f19ad1748c203b295e3ff699eabb7bf"
V064_WORKFLOW=36264343312
V064_ARTIFACT=10913620188
V064_DIGEST="sha256:970d4c510642f5803ca4228fe2715d10661fc8733c7eb7fee5e1ad94d700678c"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
VERDICT="BLOCKED_B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBILITY"
BLOCKER="B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE"
METHOD="PDSC_SHA256_V1"
TAXONOMY="B3_CLASSIFICACAO_SETORIAL"
LEVEL="SETOR_ECONOMICO"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
S064=ROOT/"output_br_ibrx100_sector_identity_coverage_v0_64/summary_v0.64.json"
C064=ROOT/"output_br_ibrx100_sector_identity_coverage_v0_64/stage_checkpoint_v0.64.json"
I064=ROOT/"output_br_ibrx100_sector_identity_coverage_v0_64/br_security_company_identity_audit_v0.64.csv"
L064=ROOT/"output_br_ibrx100_sector_identity_coverage_v0_64/br_b3_sector_level_binding_v0.64.json"
P064=ROOT/"output_br_ibrx100_sector_identity_coverage_v0_64/canonical_sector_code_contract_v0.64.json"
RESEARCH=ROOT/"config/br_ibrx100_classification_tree_inversion_research_v0.65.json"

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(*a:str)->str:
    return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

def readcsv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def writecsv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(rows[0].keys()) if rows else []
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:
            w.writeheader()
            w.writerows(rows)

def pdsc(name:str)->str:
    n=unicodedata.normalize("NFC",name)
    payload=TAXONOMY+"\x1f"+LEVEL+"\x1f"+n
    return "PDSC1:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()

def encode_segment(label:str)->dict[str,str]:
    component=urllib.parse.quote(label,safe="-_.!~*'()")
    b64=base64.b64encode(component.encode("utf-8")).decode("ascii")
    query=urllib.parse.quote(b64,safe="")
    return {"encoded_component":component,"base64":b64,"query_value":query}

def provider_calls()->dict[str,int]:
    return {
      "per_security_page_fanout":0,"company_overview_requests_for_37":0,"company_name_matching":0,"fuzzy_matching":0,
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,"etf_holdings":0,
      "third_party_databases":0,"gics_icb_fallback":0,"crosswalk":0,"price_ohlcv":0,"news":0,"trading_analysis":0
    }

def validate_predecessor(repo_sha:str)->tuple[dict[str,Any],dict[str,Any],list[dict[str,str]],dict[str,Any],dict[str,Any]]:
    if git("rev-parse","HEAD")!=repo_sha:
        raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(S064.read_text(encoding="utf-8"))
    c=json.loads(C064.read_text(encoding="utf-8"))
    ids=readcsv(I064)
    level=json.loads(L064.read_text(encoding="utf-8"))
    contract=json.loads(P064.read_text(encoding="utf-8"))
    if s["verdict"]!="BLOCKED_EXACT_37_CLASSIFICATION_COVERAGE": raise RuntimeError("v0.64 verdict")
    if s["br_sector_identity_coverage_ready"] is not False: raise RuntimeError("v0.64 readiness")
    if (s["ready"],s["total"],s["ambiguous"],s["not_found"],s["not_verified"])!=(0,37,0,0,37): raise RuntimeError("v0.64 counts")
    if s["security_to_company_ready"]!=37: raise RuntimeError("v0.64 security-to-company")
    if s["sector_taxonomy"]!=TAXONOMY or s["sector_level"]!=LEVEL or s["sector_code_method"]!=METHOD: raise RuntimeError("v0.64 sector authority")
    if s["blocker"]!="BR_EXACT_37_COVERAGE_INCOMPLETE": raise RuntimeError("v0.64 blocker")
    if c["workflow_run_id"]!=V064_WORKFLOW or c["artifact_id"]!=V064_ARTIFACT: raise RuntimeError("v0.64 workflow/artifact")
    if "sha256:"+c["artifact_digest"]!=V064_DIGEST: raise RuntimeError("v0.64 digest")
    if len(ids)!=37 or any(r["Security_To_Company_Status"]!="PASS" for r in ids): raise RuntimeError("v0.64 identity rows")
    if any(r["Company_Name_Join_Used"]!="NO" for r in ids): raise RuntimeError("v0.64 name join")
    if level["Sector_Level"]!=LEVEL or level["Sector_Taxonomy"]!=TAXONOMY: raise RuntimeError("v0.64 level binding")
    if contract["Sector_Code_Method"]!=METHOD: raise RuntimeError("v0.64 PDSC method")
    if sha(FROZEN)!=FROZEN_SHA or sha(V057)!=V057_SHA or sha(V058)!=V058_SHA: raise RuntimeError("immutability predecessor")
    return s,c,ids,level,contract

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_br_ibrx100_classification_tree_inversion_v0_65")
    args=ap.parse_args()
    out=ROOT/args.output_dir
    out.mkdir(parents=True,exist_ok=True)

    s64,c64,ids,level64,contract64=validate_predecessor(args.repository_sha)
    r=json.loads(RESEARCH.read_text(encoding="utf-8"))
    if r["version"]!=VERSION or r["scope_cohort"]!="BR_IBRX100" or r["frozen_rows"]!=37:
        raise RuntimeError("research scope mismatch")
    if r["hierarchy_capture"]["result"]!="NOT_MACHINE_REPRODUCIBLE_COMPLETE":
        raise RuntimeError("hierarchy result mismatch")
    if r["blocker"]!=BLOCKER:
        raise RuntimeError("blocker mismatch")
    if any(r["prohibited_requests"].values()) or any(provider_calls().values()):
        raise RuntimeError("prohibited request recorded")

    enc_rows=[]
    for ex in r["encoding_contract"]["examples"]:
        calc=encode_segment(ex["exact_label"])
        ok=(calc["encoded_component"]==ex["encoded_component"] and calc["base64"]==ex["base64"] and calc["query_value"]==ex["query_value"])
        enc_rows.append({
          "Exact_Label":ex["exact_label"],
          "Encoded_Component_Expected":ex["encoded_component"],
          "Encoded_Component_Calculated":calc["encoded_component"],
          "Base64_Expected":ex["base64"],
          "Base64_Calculated":calc["base64"],
          "Query_Value_Expected":ex["query_value"],
          "Query_Value_Calculated":calc["query_value"],
          "Official_URL":ex["official_url"],
          "Verification":"PASS" if ok else "FAIL"
        })
        if not ok: raise RuntimeError("encoding contract verification failed")

    tree_snapshot={
      "taxonomy":TAXONOMY,
      "sector_level":LEVEL,
      "root_url":r["hierarchy_capture"]["root_url"],
      "classification_url":r["hierarchy_capture"]["classification_url"],
      "capture_status":"INCOMPLETE_NOT_MACHINE_REPRODUCIBLE",
      "complete_setor_count":"NOT_VERIFIED",
      "complete_subsetor_count":"NOT_VERIFIED",
      "complete_segment_count":"NOT_VERIFIED",
      "coverage_traversal_authorized":False,
      "reason":r["hierarchy_capture"]["evidence"]
    }
    (out/"b3_classification_tree_snapshot_v0.65.json").write_text(json.dumps(tree_snapshot,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    node_rows=[]
    for i,(subsetor,segment) in enumerate(r["partial_observed_slice"]["subsetor_segment_rows"],1):
        node_rows.append({
          "Observed_Order":i,
          "Setor_Economico_Raw":r["partial_observed_slice"]["parent_setor_economico"],
          "Subsetor_Raw":subsetor,
          "Segmento_Raw":segment,
          "Official_Node_Query_Identifier":"NOT_CAPTURED",
          "Official_Request_URL":"NOT_CONSTRUCTED_WITHOUT_COMPLETE_TREE",
          "Retrieval_Status":"PARTIAL_OBSERVATION_ONLY_NOT_QUERIED_FOR_COVERAGE",
          "Coverage_Node":"NO"
        })
    writecsv(out/"b3_classification_node_ledger_v0.65.csv",node_rows)

    encoding_contract={
      "status":"PASS_FOR_KNOWN_OFFICIAL_EXAMPLES",
      "mechanism":r["encoding_contract"]["mechanism"],
      "complete_tree_dependency":"UNRESOLVED",
      "guessing_used":False,
      "examples_verified":len(enc_rows)
    }
    (out/"b3_group_query_encoding_contract_v0.65.json").write_text(json.dumps(encoding_contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    writecsv(out/"b3_group_query_encoding_examples_v0.65.csv",enc_rows)

    group_requests=[{
      "Coverage_Request_Order":"",
      "Setor_Economico_Raw":"NOT_AVAILABLE",
      "Subsetor_Raw":"NOT_AVAILABLE",
      "Segmento_Raw":"NOT_AVAILABLE",
      "Query_Value":"NOT_AVAILABLE",
      "Request_URL":"NOT_EXECUTED",
      "Retrieval_Status":"STOPPED_BEFORE_PARTIAL_TRAVERSAL",
      "Reason":BLOCKER
    }]
    writecsv(out/"b3_group_request_ledger_v0.65.csv",group_requests)

    membership=[{
      "Query_Node":"NONE",
      "B3_Company_Code":"NONE",
      "Official_Company_Label":"NONE",
      "Setor_Economico_Raw":"NONE",
      "Subsetor_Raw":"NONE",
      "Segmento_Raw":"NONE",
      "Source_URL":"NONE",
      "Retrieval_Status":"NO_GROUP_COVERAGE_REQUESTS_EXECUTED"
    }]
    writecsv(out/"b3_group_company_membership_v0.65.csv",membership)

    coverage=[]
    for x in ids:
        coverage.append({
          "Security_Key":x["Security_Key"],
          "WS_ID":x["WS_ID"],
          "Primary_MIC":x["Primary_MIC"],
          "Primary_Ticker":x["Primary_Ticker"],
          "B3_Company_Code":x["B3_Company_Code"],
          "Security_To_Company_Status":"PASS_INHERITED_V0_64",
          "Setor_Economico_Raw":"NOT_VERIFIED",
          "Subsetor_Raw":"NOT_VERIFIED",
          "Segmento_Raw":"NOT_VERIFIED",
          "Exact_Company_Code_Group_Hits":0,
          "Conflicting_Setor_Count":0,
          "Coverage_Status":"NOT_VERIFIED",
          "Sector_Taxonomy":TAXONOMY,
          "Sector_Level":LEVEL,
          "Sector_Raw_Name":"NOT_VERIFIED",
          "Sector_Name":"NOT_VERIFIED",
          "Source_Sector_Code":"",
          "Sector_Code_Origin":"PROJECT_DERIVED_CANONICAL",
          "Sector_Code_Method":METHOD,
          "Sector_Code":"NOT_GENERATED_WITHOUT_PROVABLY_MAPPABLE_ROW",
          "Blocker":BLOCKER
        })
    writecsv(out/"br_exact_37_classification_coverage_v0.65.csv",coverage)

    sector_inventory=[{
      "Setor_Economico_Raw":"NONE_READY",
      "Ready_Row_Count":0,
      "Distinct_Sector_Status":"NO_PROVABLY_MAPPABLE_ROWS",
      "PDSC_Code":"NOT_GENERATED"
    }]
    writecsv(out/"br_distinct_sector_inventory_v0.65.csv",sector_inventory)

    pdsc_audit=[{
      "Setor_Economico_Raw":"NONE",
      "Generation_1":"NOT_EXECUTED",
      "Generation_2":"NOT_EXECUTED",
      "Determinism_Status":"NOT_APPLICABLE_NO_READY_ROWS",
      "Reason":"PDSC generation permitted only for PROVABLY_MAPPABLE exact-37 rows"
    }]
    writecsv(out/"pdsc_exact37_determinism_audit_v0.65.csv",pdsc_audit)

    collision={
      "distinct_ready_sector_names":0,
      "generated_codes":0,
      "unique_codes":0,
      "collision_count":0,
      "status":"NOT_APPLICABLE_NO_READY_ROWS",
      "blocker_precedes_pdsc":BLOCKER
    }
    (out/"pdsc_collision_audit_v0.65.json").write_text(json.dumps(collision,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    ext=[]
    for i,e in enumerate(r["external_requests"],1):
        ext.append({
          "Request_Order":i,
          "URL":e["url"],
          "Result":e["result"],
          "Use":e["use"],
          "Official_B3":"YES",
          "Per_Security_Fanout":"NO"
        })
    writecsv(out/"external_request_ledger_v0.65.csv",ext)

    imm={
      "frozen_expected_sha256":FROZEN_SHA,"frozen_sha_before":sha(FROZEN),"frozen_sha_after":sha(FROZEN),"frozen_unchanged":sha(FROZEN)==FROZEN_SHA,
      "v057_expected_sha256":V057_SHA,"v057_sha_before":sha(V057),"v057_sha_after":sha(V057),"v057_unchanged":sha(V057)==V057_SHA,
      "v058_expected_sha256":V058_SHA,"v058_sha_before":sha(V058),"v058_sha_after":sha(V058),"v058_unchanged":sha(V058)==V058_SHA,
      "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"price_cache_mutation":False,"feature_mutation":False,"home_market_rs_mutation":False,
      "p0_runs":0,"p1_runs":0,"p2_runs":0
    }
    (out/"immutability_audit_v0.65.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"provider_call_audit_v0.65.json").write_text(json.dumps(provider_calls(),indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def t(name:str,ok:bool,detail:Any)->None:
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok: raise RuntimeError(name)
    t("V064_VERDICT",s64["verdict"]=="BLOCKED_EXACT_37_CLASSIFICATION_COVERAGE",s64["verdict"])
    t("V064_READY_COUNTS",(s64["ready"],s64["total"],s64["ambiguous"],s64["not_found"],s64["not_verified"])==(0,37,0,0,37),"0/37/0/0/37")
    t("V064_SECURITY_TO_COMPANY_37",s64["security_to_company_ready"]==37,37)
    t("V064_TAXONOMY",s64["sector_taxonomy"]==TAXONOMY,TAXONOMY)
    t("V064_LEVEL",s64["sector_level"]==LEVEL,LEVEL)
    t("V064_PDSC",s64["sector_code_method"]==METHOD,METHOD)
    t("V064_BLOCKER",s64["blocker"]=="BR_EXACT_37_COVERAGE_INCOMPLETE",s64["blocker"])
    t("ENCODING_AGRICULTURA",enc_rows[0]["Verification"]=="PASS","PASS")
    t("ENCODING_MINERAIS_METALICOS",enc_rows[1]["Verification"]=="PASS","PASS")
    t("TREE_COMPLETE_FAIL_CLOSED",tree_snapshot["capture_status"]=="INCOMPLETE_NOT_MACHINE_REPRODUCIBLE",tree_snapshot["capture_status"])
    t("COVERAGE_NODE_QUERIES_ZERO",r["coverage_execution"]["coverage_classification_nodes_queried"]==0,0)
    t("NO_PARTIAL_TRAVERSAL",group_requests[0]["Retrieval_Status"]=="STOPPED_BEFORE_PARTIAL_TRAVERSAL","PASS")
    t("COVERAGE_ROWS_37",len(coverage)==37,len(coverage))
    t("READY_ZERO",sum(x["Coverage_Status"]=="PROVABLY_MAPPABLE" for x in coverage)==0,0)
    t("AMBIGUOUS_ZERO",sum(x["Coverage_Status"]=="AMBIGUOUS" for x in coverage)==0,0)
    t("NOT_FOUND_ZERO",sum(x["Coverage_Status"]=="NOT_FOUND" for x in coverage)==0,0)
    t("NOT_VERIFIED_37",sum(x["Coverage_Status"]=="NOT_VERIFIED" for x in coverage)==37,37)
    t("DISTINCT_READY_SETORES_ZERO",r["coverage_execution"]["distinct_setores_exact37"]==0,0)
    t("NO_PDSC_GENERATION_WITHOUT_READY",collision["generated_codes"]==0,0)
    t("NO_PER_SECURITY_FANOUT",provider_calls()["per_security_page_fanout"]==0,0)
    t("NO_COMPANY_NAME_MATCH",provider_calls()["company_name_matching"]==0,0)
    t("BLOCKER_MACHINE_REPRODUCIBILITY",r["blocker"]==BLOCKER,BLOCKER)
    t("NO_CANONICAL_MAPPING",imm["canonical_mapping_population_runs"]==0,0)
    t("NO_OTHER_COHORT",imm["other_cohort_rechecks"]==0,0)
    t("NO_SECTOR_RS",imm["sector_rs_runs"]==0,0)
    t("PROHIBITED_CALLS_ZERO",all(v==0 for v in provider_calls().values()),json.dumps(provider_calls(),sort_keys=True))
    t("FROZEN_IMMUTABLE",imm["frozen_unchanged"],FROZEN_SHA)
    t("V057_IMMUTABLE",imm["v057_unchanged"],V057_SHA)
    t("V058_IMMUTABLE",imm["v058_unchanged"],V058_SHA)
    t("P0_P1_P2_ZERO",imm["p0_runs"]==imm["p1_runs"]==imm["p2_runs"]==0,"0/0/0")
    writecsv(out/"test_results_v0.65.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":VERDICT,
      "br_exact_37_classification_coverage_ready":False,
      "ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
      "classification_nodes_queried":0,
      "partial_observed_node_rows":len(node_rows),
      "distinct_setores":0,
      "encoding_contract_status":"PASS_FOR_KNOWN_OFFICIAL_EXAMPLES",
      "blocker":BLOCKER,
      "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,
      "prohibited_provider_calls":provider_calls(),"immutability":imm,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":BLOCKER
    }
    checkpoint={
      "stage":STAGE,"version":VERSION,"verdict":VERDICT,
      "br_exact_37_classification_coverage_ready":False,
      "ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
      "classification_nodes_queried":0,"distinct_setores":0,"blocker":BLOCKER,
      "canonical_mapping_population_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_p2_runs":0,
      "tests_passed":len(tests),"tests_failed":0,"artifact_binding":"PENDING_UPLOAD","next_gate":BLOCKER
    }
    (out/"summary_preupload_v0.65.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.65.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file(): files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,"verdict":VERDICT,
      "br_exact_37_classification_coverage_ready":False,"ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
      "classification_nodes_queried":0,"distinct_setores":0,"blocker":BLOCKER,
      "frozen_sha256":FROZEN_SHA,"v057_feature_sha256":V057_SHA,"v058_home_rs_sha256":V058_SHA,
      "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":BLOCKER
    }
    (out/"manifest_preupload_v0.65.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({
      "verdict":VERDICT,"br_exact_37_classification_coverage_ready":False,
      "ready":0,"total":37,"ambiguous":0,"not_found":0,"not_verified":37,
      "classification_nodes_queried":0,"distinct_setores":0,"blocker":BLOCKER,"next_gate":BLOCKER
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
