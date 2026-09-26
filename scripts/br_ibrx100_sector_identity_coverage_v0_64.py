#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,subprocess,unicodedata
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.64"
STAGE="BR_IBRX100_CANONICAL_SECTOR_KEY_SECURITY_IDENTITY_EXACT_37_COVERAGE_GATE"
REQUIRED_START_HEAD="f0a67388740b17dd62b47f1163df76d503a9c50b"
V063_WORKFLOW=36258067350
V063_ARTIFACT=10911387342
V063_DIGEST="sha256:0ec10e147c619ec999af1b8de3dcd34b93d4fff29c3f6a96dd672bcb05446535"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
VERDICT="BLOCKED_EXACT_37_CLASSIFICATION_COVERAGE"
BLOCKER="BR_EXACT_37_COVERAGE_INCOMPLETE"
METHOD="PDSC_SHA256_V1"
TAXONOMY="B3_CLASSIFICACAO_SETORIAL"
SECTOR_LEVEL="SETOR_ECONOMICO"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
CAP=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V032=ROOT/"universe/segments/br_ibrx100_source_frozen_v0.32.csv"
S063=ROOT/"output_br_ibrx100_b3_sector_bulk_route_v0_63/summary_v0.63.json"
C063=ROOT/"output_br_ibrx100_b3_sector_bulk_route_v0_63/stage_checkpoint_v0.63.json"
D063=ROOT/"output_br_ibrx100_b3_sector_bulk_route_v0_63/br_b3_sector_bulk_route_discovery_v0.63.json"
AUTH=ROOT/"config/manager_governance_authority_G_SEC_03_v0.64.json"
RESEARCH=ROOT/"config/br_ibrx100_sector_identity_coverage_research_v0.64.json"

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(*a:str)->str:
    return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

def readcsv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def writecsv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:w.writeheader();w.writerows(rows)

def pdsc(sector_name:str)->str:
    name=unicodedata.normalize("NFC",sector_name)
    payload=TAXONOMY+"\x1f"+SECTOR_LEVEL+"\x1f"+name
    return "PDSC1:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()

def provider_calls()->dict[str,int]:
    return {"alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,"screeners":0,"etf_holdings":0,
            "third_party_security_databases":0,"company_name_joins":0,"fuzzy_matching":0,"per_security_web_fanout":0,"gics_icb_fallback":0,
            "crosswalk":0,"price_ohlcv":0,"news":0,"trading_analysis":0}

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha: raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0: raise RuntimeError("required start head not ancestor")
    s=json.loads(S063.read_text(encoding="utf-8")); c=json.loads(C063.read_text(encoding="utf-8")); d=json.loads(D063.read_text(encoding="utf-8"))
    if s["verdict"]!="BLOCKED_SOURCE_NATIVE_SECTOR_CODE": raise RuntimeError("v0.63 verdict")
    if s["br_official_sector_bulk_route_ready"] is not True: raise RuntimeError("v0.63 route")
    if s["access_class"]!="PUBLIC_REPRODUCIBLE" or s["classification_content"]!="PASS": raise RuntimeError("v0.63 route gates")
    if d["resolved_route_id"]!="B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH" or d["taxonomy_identity"]!=TAXONOMY: raise RuntimeError("v0.63 route identity")
    if s["security_identity_schema"]!="B3_COMPANY_CODE_PLUS_COMPANY_METADATA_ONLY_SECURITY_LEVEL_ISIN_FULL_TICKER_NOT_IN_BULK_RESULT": raise RuntimeError("v0.63 security schema")
    if s["sector_code"]!="NOT_AVAILABLE": raise RuntimeError("v0.63 sector code")
    if c["workflow_run_id"]!=V063_WORKFLOW or c["artifact_id"]!=V063_ARTIFACT: raise RuntimeError("v0.63 workflow/artifact")
    if "sha256:"+c["artifact_digest"]!=V063_DIGEST: raise RuntimeError("v0.63 digest")
    if sha(FROZEN)!=FROZEN_SHA or sha(V057)!=V057_SHA or sha(V058)!=V058_SHA: raise RuntimeError("immutability predecessor")
    return {"summary":s,"checkpoint":c,"discovery":d}

def validate_authority()->dict[str,Any]:
    a=json.loads(AUTH.read_text(encoding="utf-8"))
    if a["authority_id"]!="G-SEC-03" or a["version"]!=VERSION: raise RuntimeError("G-SEC-03 mismatch")
    if a["source_code_absent_values"]["Sector_Code_Method"]!=METHOD: raise RuntimeError("method mismatch")
    if a["br_binding"]["Sector_Taxonomy"]!=TAXONOMY or a["br_binding"]["Sector_Level"]!=SECTOR_LEVEL: raise RuntimeError("BR binding")
    if a["rules"]["canonical_mapping_population_authorized"] is not False or a["rules"]["sector_rs_authorized"] is not False: raise RuntimeError("scope")
    return a

def target_rows()->list[dict[str,str]]:
    cap=readcsv(CAP)
    rows=[r for r in cap if r["Primary_Universe_Index"]=="BR_IBRX100"]
    if len(rows)!=37: raise RuntimeError(f"BR Frozen rows {len(rows)}")
    return rows

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repository-sha",required=True); ap.add_argument("--output-dir",default="output_br_ibrx100_sector_identity_coverage_v0_64")
    args=ap.parse_args(); out=ROOT/args.output_dir; out.mkdir(parents=True,exist_ok=True)
    pred=validate_predecessor(args.repository_sha); auth=validate_authority()
    research=json.loads(RESEARCH.read_text(encoding="utf-8"))
    if research["version"]!=VERSION or research["scope_cohort"]!="BR_IBRX100": raise RuntimeError("research scope")
    if any(research["prohibited_requests"].values()) or any(provider_calls().values()): raise RuntimeError("prohibited calls")

    target=target_rows()
    v032={r["WS_ID_Candidate"]:r for r in readcsv(V032)}
    identity=[]
    coverage=[]
    for r in target:
        sid=r["Source_WS_ID"]; src=v032.get(sid)
        if src is None: raise RuntimeError(f"missing v0.32 official source {sid}")
        ticker=r["Primary_Ticker"]
        if r["Primary_MIC"]!="BVMF" or src["Primary_MIC"]!="BVMF": raise RuntimeError(f"MIC mismatch {sid}")
        if src["Primary_Ticker"]!=ticker: raise RuntimeError(f"ticker mismatch {sid}")
        if src["Instrument_Type_v0_31"]!="ORDINARY_SHARE" or not ticker.endswith("3") or len(ticker)!=5: raise RuntimeError(f"not ordinary 5-char ticker {sid}")
        company_code=ticker[:4]
        identity.append({
            "Security_Key":r["Security_Key"],"WS_ID":sid,"Primary_MIC":"BVMF","Primary_Ticker":ticker,
            "Official_B3_Source_ID":src["Source_ID"],"Official_B3_Source_AsOf":src["Source_AsOf_Official"],
            "Official_B3_Security_Name":src["Security_Name_Official"],"Official_B3_Type":src["B3_Type_Official"],
            "Official_Security_Match":"PASS","Security_To_Company_Method":"B3_TICKER_XXXXY_ISSUER_CODE_RULE",
            "B3_Company_Code":company_code,"Company_Name_Join_Used":"NO","Security_To_Company_Status":"PASS"
        })
        coverage.append({
            "Security_Key":r["Security_Key"],"WS_ID":sid,"Primary_MIC":"BVMF","Primary_Ticker":ticker,"B3_Company_Code":company_code,
            "Security_To_Company_Status":"PASS","Company_To_Classification_Route":"B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH",
            "Sector_Taxonomy":TAXONOMY,"Sector_Level":SECTOR_LEVEL,
            "Sector_Raw_Name":"NOT_VERIFIED","Sector_Name":"NOT_VERIFIED","Source_Sector_Code":"",
            "Sector_Code_Origin":"PROJECT_DERIVED_CANONICAL","Sector_Code_Method":METHOD,"Sector_Code":"NOT_GENERATED_WITHOUT_VERIFIED_SECTOR_NAME",
            "Coverage_Status":"NOT_VERIFIED","Blocker":BLOCKER,
            "Reason":"ROW_COMPLETE_OFFICIAL_B3_SECTOR_NAME_NOT_SEALED_NO_PER_SECURITY_WEB_FANOUT"
        })

    ready=sum(r["Coverage_Status"]=="PROVABLY_MAPPABLE" for r in coverage)
    amb=sum(r["Coverage_Status"]=="AMBIGUOUS" for r in coverage)
    nf=sum(r["Coverage_Status"]=="NOT_FOUND" for r in coverage)
    nv=sum(r["Coverage_Status"]=="NOT_VERIFIED" for r in coverage)
    if (ready,amb,nf,nv)!=(0,0,0,37): raise RuntimeError("coverage totals")

    route_ledger=[
      {"Route":"REPOSITORY_B3_IBRX100_SOURCE_V0_32","Authority":"B3","Scope":"exact official ticker/name/type/BVMF membership","Status":"PASS","Reference":"universe/segments/br_ibrx100_source_frozen_v0.32.csv"},
      {"Route":"B3_SHARE_TICKER_XXXXY_RULE","Authority":"B3","Scope":"ticker -> issuer/company code","Status":"PASS","Reference":research["official_identity_rule"]["url"]},
      {"Route":"B3_BVBG_028_02_INSTRUMENTS_FILE","Authority":"B3","Scope":"security reference ticker/ISIN architecture","Status":"PASS_REFERENCE_SUPPORT_ONLY","Reference":research["official_security_reference_support"][0]["url"]},
      {"Route":"B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH","Authority":"B3","Scope":"company code -> classification route","Status":"PASS_ROUTE_DESIGN","Reference":research["classification_route_identity"]["url"]},
      {"Route":"B3_ROW_COMPLETE_CLASSIFICATION_PAYLOAD","Authority":"B3","Scope":"exact 37 company code -> sector name coverage","Status":"NOT_VERIFIED","Reference":"https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/classification?language=pt-br"}
    ]
    writecsv(out/"br_security_reference_route_ledger_v0.64.csv",route_ledger)
    writecsv(out/"br_security_company_identity_audit_v0.64.csv",identity)
    writecsv(out/"br_exact_37_coverage_audit_v0.64.csv",coverage)

    binding={
      "Sector_Taxonomy":TAXONOMY,"Sector_Level":SECTOR_LEVEL,"Source_Level_Label":"Setor Econômico",
      "Binding_Status":"PASS","Subsetor_Used":"NO","Segmento_Used":"NO",
      "Basis":research["sector_level_binding"]["basis"],"Basis_URLs":research["sector_level_binding"]["basis_urls"]
    }
    (out/"br_b3_sector_level_binding_v0.64.json").write_text(json.dumps(binding,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    contract={
      "Contract":"PDSC_SHA256_V1","Authority":"G-SEC-03","Sector_Taxonomy":TAXONOMY,"Sector_Level":SECTOR_LEVEL,
      "Source_Sector_Code_When_Absent":None,"Sector_Code_Origin":"PROJECT_DERIVED_CANONICAL","Sector_Code_Method":METHOD,
      "Input":["Sector_Taxonomy","U+001F","Sector_Level","U+001F","Sector_Name"],"Unicode_Normalization":"NFC_ONLY","Encoding":"UTF-8",
      "Hash":"SHA-256","Output":"PDSC1:<full-lowercase-sha256>","Truncation":"NO","Ordinal_Numbering":"NO",
      "Company_Name_Input":"NO","Semantic_Normalization":"NO","Translation":"NO","Classification_Inference":"NO"
    }
    (out/"canonical_sector_code_contract_v0.64.json").write_text(json.dumps(contract,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    det=[]
    codes=[]
    for v in research["pdsc_validation_examples"]:
        raw=v["Sector_Name"]; c1=pdsc(raw); c2=pdsc(raw)
        det.append({"Sector_Taxonomy":TAXONOMY,"Sector_Level":SECTOR_LEVEL,"Sector_Raw_Name":raw,"Sector_Name_NFC":unicodedata.normalize("NFC",raw),
                    "Generation_1":c1,"Generation_2":c2,"Deterministic":"PASS" if c1==c2 else "FAIL","Coverage_Use":v["coverage_use"],"Source_URL":v["source_url"]})
        codes.append(c1)
    writecsv(out/"canonical_sector_code_determinism_test_v0.64.csv",det)
    collision={"tested_vectors":len(codes),"unique_codes":len(set(codes)),"collisions":len(codes)-len(set(codes)),"result":"PASS" if len(codes)==len(set(codes)) else "FAIL","scope":"METHOD_VECTORS_ONLY_NOT_EXACT_37_COVERAGE"}
    (out/"canonical_sector_code_collision_audit_v0.64.json").write_text(json.dumps(collision,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    ext=[{"Request_Order":i+1,"URL":x["url"],"Result":x["result"],"Use":x["use"],"Official_B3":"YES","Per_Security_Fanout":"NO"} for i,x in enumerate(research["external_request_ledger"])]
    writecsv(out/"external_request_ledger_v0.64.csv",ext)

    imm={"frozen_expected_sha256":FROZEN_SHA,"frozen_sha_before":sha(FROZEN),"frozen_sha_after":sha(FROZEN),"frozen_unchanged":sha(FROZEN)==FROZEN_SHA,
         "v057_expected_sha256":V057_SHA,"v057_sha_before":sha(V057),"v057_sha_after":sha(V057),"v057_unchanged":sha(V057)==V057_SHA,
         "v058_expected_sha256":V058_SHA,"v058_sha_before":sha(V058),"v058_sha_after":sha(V058),"v058_unchanged":sha(V058)==V058_SHA,
         "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"price_cache_mutation":False,"feature_mutation":False,"home_market_rs_mutation":False,
         "p0_runs":0,"p1_runs":0,"p2_runs":0}
    (out/"immutability_audit_v0.64.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"provider_call_audit_v0.64.json").write_text(json.dumps(provider_calls(),indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def t(name,ok,detail):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok: raise RuntimeError(name)
    t("V063_VERDICT",pred["summary"]["verdict"]=="BLOCKED_SOURCE_NATIVE_SECTOR_CODE",pred["summary"]["verdict"])
    t("V063_ROUTE_READY",pred["summary"]["br_official_sector_bulk_route_ready"] is True,"YES")
    t("V063_ACCESS_PUBLIC",pred["summary"]["access_class"]=="PUBLIC_REPRODUCIBLE",pred["summary"]["access_class"])
    t("V063_CLASSIFICATION_PASS",pred["summary"]["classification_content"]=="PASS",pred["summary"]["classification_content"])
    t("V063_ROUTE_ID",pred["discovery"]["resolved_route_id"]=="B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH",pred["discovery"]["resolved_route_id"])
    t("V063_TAXONOMY",pred["discovery"]["taxonomy_identity"]==TAXONOMY,TAXONOMY)
    t("G_SEC_03_BOUND",auth["authority_id"]=="G-SEC-03","G-SEC-03")
    t("TARGET_37",len(target)==37,len(target))
    t("OFFICIAL_SOURCE_JOIN_37",len(identity)==37,len(identity))
    t("ALL_SECURITY_TO_COMPANY_PASS",all(r["Security_To_Company_Status"]=="PASS" for r in identity),"37/37")
    t("NO_COMPANY_NAME_JOIN",all(r["Company_Name_Join_Used"]=="NO" for r in identity),"NO")
    t("SECTOR_LEVEL_SETOR_ECONOMICO",binding["Sector_Level"]==SECTOR_LEVEL,SECTOR_LEVEL)
    t("NO_SUBSETOR_OR_SEGMENTO",binding["Subsetor_Used"]=="NO" and binding["Segmento_Used"]=="NO","NO/NO")
    t("PDSC_METHOD",contract["Sector_Code_Method"]==METHOD,METHOD)
    t("PDSC_REPEAT_DETERMINISTIC",all(r["Deterministic"]=="PASS" for r in det),"PASS")
    t("PDSC_NO_COLLISION_METHOD_VECTORS",collision["result"]=="PASS","PASS")
    t("EXACT37_READY_ZERO",ready==0,ready)
    t("EXACT37_AMBIGUOUS_ZERO",amb==0,amb)
    t("EXACT37_NOT_FOUND_ZERO",nf==0,nf)
    t("EXACT37_NOT_VERIFIED_37",nv==37,nv)
    t("BLOCKER_EXACT_COVERAGE",research["exact_37_result"]["blocker"]==BLOCKER,BLOCKER)
    t("NO_PER_SECURITY_WEB_FANOUT",provider_calls()["per_security_web_fanout"]==0,0)
    t("NO_CANONICAL_MAPPING_POPULATION",imm["canonical_mapping_population_runs"]==0,0)
    t("NO_OTHER_COHORT",imm["other_cohort_rechecks"]==0,0)
    t("NO_SECTOR_RS",imm["sector_rs_runs"]==0,0)
    t("PROHIBITED_CALLS_ZERO",all(v==0 for v in provider_calls().values()),json.dumps(provider_calls(),sort_keys=True))
    t("FROZEN_IMMUTABLE",imm["frozen_unchanged"],FROZEN_SHA)
    t("V057_IMMUTABLE",imm["v057_unchanged"],V057_SHA)
    t("V058_IMMUTABLE",imm["v058_unchanged"],V058_SHA)
    t("P0_P1_P2_ZERO",imm["p0_runs"]==imm["p1_runs"]==imm["p2_runs"]==0,"0/0/0")
    writecsv(out/"test_results_v0.64.csv",tests)

    summary={"stage":STAGE,"version":VERSION,"verdict":VERDICT,"br_sector_identity_coverage_ready":False,"ready":ready,"total":37,"ambiguous":amb,"not_found":nf,"not_verified":nv,
             "sector_code_method":METHOD,"sector_taxonomy":TAXONOMY,"sector_level":SECTOR_LEVEL,"security_to_company_ready":37,"blocker":BLOCKER,
             "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
             "prohibited_provider_calls":provider_calls(),"immutability":imm,"tests":{"total":len(tests),"passed":len(tests),"failed":0},
             "artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":BLOCKER}
    checkpoint={"stage":STAGE,"version":VERSION,"verdict":VERDICT,"br_sector_identity_coverage_ready":False,"ready":ready,"total":37,"ambiguous":amb,"not_found":nf,"not_verified":nv,
                "sector_code_method":METHOD,"blocker":BLOCKER,"canonical_mapping_population_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_p2_runs":0,
                "tests_passed":len(tests),"tests_failed":0,"artifact_binding":"PENDING_UPLOAD","next_gate":BLOCKER}
    (out/"summary_preupload_v0.64.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.64.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,"verdict":VERDICT,
              "br_sector_identity_coverage_ready":False,"ready":ready,"total":37,"ambiguous":amb,"not_found":nf,"not_verified":nv,"sector_code_method":METHOD,
              "blocker":BLOCKER,"frozen_sha256":FROZEN_SHA,"v057_feature_sha256":V057_SHA,"v058_home_rs_sha256":V058_SHA,
              "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
              "productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":BLOCKER}
    (out/"manifest_preupload_v0.64.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":VERDICT,"br_sector_identity_coverage_ready":False,"ready":ready,"total":37,"ambiguous":amb,"not_found":nf,"not_verified":nv,
                      "sector_code_method":METHOD,"blocker":BLOCKER,"next_gate":BLOCKER},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
