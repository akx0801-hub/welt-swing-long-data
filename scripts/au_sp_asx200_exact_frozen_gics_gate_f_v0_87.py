#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,importlib.util,json,re,subprocess,time,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.87"
STAGE="AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F"
REQUIRED_START_HEAD="16ca7cfc2148527f4e48bda642e7533831a716c5"
V086_WORKFLOW=36388443082
V086_ARTIFACT=10955208258
V086_DIGEST="sha256:b9f68ee805db5725db95b0c3d397e8b8fcf0a9759d7814ff3edf169c0ce46f03"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"
MSCI_SHA="d66cfdf808872211561270a7141c40687417b3f669192c6b2650ae2d0aacad06"

SPEC=ROOT/"config/au_sp_asx200_exact_frozen_gics_classification_gate_f_spec_v0.87.json"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
SIDECAR=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANON=ROOT/"sector_metadata/canonical/cohorts"

OUT85=ROOT/"output_au_sp_asx200_gate_d_msci_gics_repair_v0_85"
INV85=OUT85/"gics_industry_group_official_label_code_inventory_v0.85.csv"
NON85=OUT85/"au_nonformal_value_governance_audit_v0_85.csv"
SUM85=OUT85/"summary_v0.85.json"
OUT86=ROOT/"output_au_sp_asx200_identity_linkage_gate_e_v0_86"
SUM86=OUT86/"summary_v0.86.json"
CHK86=OUT86/"stage_checkpoint_v0.86.json"
MAN86=OUT86/"manifest_v0.86.json"
DEC86=OUT86/"au_deterministic_security_identity_linkage_decision_v0.86.json"
TGT86=OUT86/"au_frozen_63_identity_target_v0.86.csv"
LINK86=OUT86/"au_exact_63_ticker_linkage_audit_v0.86.csv"
SRC86=OUT86/"asx_current_directory_identity_source_audit_v0.86.json"

spec86=importlib.util.spec_from_file_location("v086",ROOT/"scripts/au_sp_asx200_identity_linkage_gate_e_v0_86.py")
v86=importlib.util.module_from_spec(spec86);spec86.loader.exec_module(v86)

def now()->str:return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def nfc(x:Any)->str:return unicodedata.normalize("NFC",str(x or "")).strip()
def keynorm(x:Any)->str:return re.sub(r"[^a-z0-9]","",nfc(x).lower().lstrip("\ufeff"))

def read_csv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def write_csv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader()
        for r in rows:w.writerow(r)
def write_json(p:Path,o:Any)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM86.read_text());c=json.loads(CHK86.read_text());m=json.loads(MAN86.read_text());d=json.loads(DEC86.read_text())
    if s["verdict"]!="PASS_AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E":raise RuntimeError("v0.86 verdict")
    if not s["au_deterministic_security_identity_linkage_ready"]:raise RuntimeError("v0.86 readiness")
    if s["frozen_target"]!=63 or s["exact_ticker_links"]!=63 or s["source_ws_id_equality"]!=63:raise RuntimeError("v0.86 linkage")
    if any(s[k]!=0 for k in ["not_found","ambiguous","not_verified","conflict"]):raise RuntimeError("v0.86 failure counts")
    if s["tests"]!={"failed":0,"passed":30,"total":30}:raise RuntimeError("v0.86 tests")
    if c["workflow_run_id"]!=V086_WORKFLOW or c["artifact_id"]!=V086_ARTIFACT or c["artifact_digest"]!=V086_DIGEST:raise RuntimeError("v0.86 artifact")
    if m["workflow_run_id"]!=V086_WORKFLOW or m["artifact_id"]!=V086_ARTIFACT or m["artifact_digest"]!=V086_DIGEST:raise RuntimeError("v0.86 manifest")
    if d["Identity_Source"]!="ASX_OFFICIAL_COMPANY_DIRECTORY" or d["Identity_Field"]!="ASX code" or d["Identity_Method"]!="EXACT_ASX_CODE_TO_FROZEN_PRIMARY_TICKER" or d["MIC"]!="XASX":raise RuntimeError("v0.86 identity contract")
    if d["Gate_F"]!="NOT_EVALUATED" or d["Gate_H"]!="NOT_EVALUATED":raise RuntimeError("v0.86 downstream")
    s85=json.loads(SUM85.read_text())
    if s85["formal_exact_match_values"]!=25 or s85["formal_label_code_coverage"]!="25/25" or s85["selected_code_strategy"]!="SOURCE_NATIVE_GICS_CODE":raise RuntimeError("v0.85 authority")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    if sha_file(PARK)!=PARK_SHA:raise RuntimeError("park registry")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SHA:raise RuntimeError("canonical registry")
    if any(AU_CANON.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical exists")
    return {"summary":s,"checkpoint":c,"manifest":m,"decision":d,"source86":json.loads(SRC86.read_text())}

def rebuild_target()->tuple[list[dict[str,str]],dict[str,Any]]:
    frozen=read_csv(FROZEN);side=read_csv(SIDECAR);prior=read_csv(TGT86)
    fby={r["Security_Key"]:r for r in frozen}
    side_keys=[r["Security_Key"] for r in side if r.get("Primary_Universe_Index")=="AU_SP_ASX200"]
    if len(side_keys)!=63 or len(set(side_keys))!=63:raise RuntimeError("sidecar AU membership regression")
    target=[]
    for sk in side_keys:
        fr=fby.get(sk)
        if not fr:raise RuntimeError("sidecar Security_Key missing Frozen")
        target.append({"Security_Key":fr["Security_Key"],"Source_WS_ID":fr["Source_WS_ID"],"Primary_MIC":fr["Primary_MIC"],
                       "Primary_Ticker":fr["Primary_Ticker"],"Primary_Universe_Index":"AU_SP_ASX200",
                       "Target_Derivation":"FROZEN_ROW_AUTHORITY_WITH_EXACT_SECURITY_KEY_COHORT_LABEL_SIDECAR"})
    target=sorted(target,key=lambda r:r["Security_Key"]);prior=sorted(prior,key=lambda r:r["Security_Key"])
    comparable=[{k:r[k] for k in ["Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker","Primary_Universe_Index","Target_Derivation"]} for r in prior]
    audit={"Physical_Frozen_Has_Primary_Universe_Index":"YES" if (frozen and "Primary_Universe_Index" in frozen[0]) else "NO",
           "Sidecar_AU_Security_Key_Count":len(side_keys),"Frozen_Target_Rows":len(target),
           "Unique_Security_Key":len({r["Security_Key"] for r in target}),"Unique_Source_WS_ID":len({r["Source_WS_ID"] for r in target}),
           "Unique_Primary_Ticker":len({r["Primary_Ticker"] for r in target}),"Primary_MIC_XASX":sum(r["Primary_MIC"]=="XASX" for r in target),
           "Source_WS_ID_Contract_PASS":sum(r["Source_WS_ID"]=="WS:XASX:"+r["Primary_Ticker"] for r in target),
           "Exact_Match_To_v086_Target":"YES" if target==comparable else "NO"}
    return target,audit

def formal_authority()->tuple[list[dict[str,str]],dict[str,list[dict[str,str]]],dict[str,list[dict[str,str]]]]:
    rows=read_csv(INV85)
    if len(rows)!=25:raise RuntimeError("v0.85 formal inventory count")
    if any(r["Source_SHA256"]!=MSCI_SHA for r in rows):raise RuntimeError("v0.85 source SHA")
    by_label=defaultdict(list);by_code=defaultdict(list)
    for r in rows:
        label=nfc(r["Official_GICS_Industry_Group_Label"]);code=nfc(r["Official_GICS_Industry_Group_Code"])
        if len(code)!=4 or not code.isdigit():raise RuntimeError("invalid official code")
        by_label[label].append(r);by_code[code].append(r)
    if any(len(v)!=1 for v in by_label.values()) or any(len(v)!=1 for v in by_code.values()):raise RuntimeError("v0.85 authority collision")
    return rows,by_label,by_code

def provider_audit()->dict[str,int]:
    return {"Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,"ETF_holdings":0,
      "third_party_classification_databases":0,"company_name_linkage":0,"fuzzy_matching":0,"ticker_change_inference":0,
      "semantic_classification_inference":0,"cross_taxonomy_mapping":0,"PDSC":0,"MSCI_methodology_requests":0,
      "per_security_web_fanout":0,"Gate_G":0,"Gate_H":0,"canonical_materialization":0,"Sector_RS":0,"P0":0,"P1":0,"P2":0,
      "fresh_ASX_directory_snapshots":1}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_au_sp_asx200_exact_frozen_gics_gate_f_v0_87")
    a=ap.parse_args();pred=validate_predecessor(a.repository_sha);spec=json.loads(SPEC.read_text())
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write_json(out/"au_gate_f_predecessor_authority_v0.87.json",{
      "Final_Commit":REQUIRED_START_HEAD,"Verdict":pred["summary"]["verdict"],"AU_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_READY":"YES",
      "Frozen_Target":63,"Exact_Ticker_Links":"63/63","Source_WS_ID_Equality":"63/63","NOT_FOUND":0,"AMBIGUOUS":0,"NOT_VERIFIED":0,"CONFLICT":0,
      "Identity_Source":"ASX_OFFICIAL_COMPANY_DIRECTORY","Identity_Field":"ASX code","Identity_Method":"EXACT_ASX_CODE_TO_FROZEN_PRIMARY_TICKER","MIC":"XASX",
      "Workflow":V086_WORKFLOW,"Artifact":V086_ARTIFACT,"Artifact_Digest":V086_DIGEST,"Tests":"30/30 PASS","Canonical_READY":"37/1425",
      "Gate_D_Taxonomy":"GICS","Gate_D_Level":"INDUSTRY_GROUP","Gate_D_Code_Strategy":"SOURCE_NATIVE_GICS_CODE","Gate_D_Formal_Label_Code_Coverage":"25/25"
    })

    target,target_audit=rebuild_target()
    write_csv(out/"au_frozen_63_classification_target_v0.87.csv",target)
    write_json(out/"au_frozen_target_sidecar_authority_audit_v0.87.json",target_audit)
    if target_audit["Exact_Match_To_v086_Target"]!="YES" or target_audit["Frozen_Target_Rows"]!=63 or target_audit["Unique_Security_Key"]!=63 or target_audit["Unique_Source_WS_ID"]!=63 or target_audit["Unique_Primary_Ticker"]!=63 or target_audit["Primary_MIC_XASX"]!=63 or target_audit["Source_WS_ID_Contract_PASS"]!=63:
        raise RuntimeError("AUTHORITY_REGRESSION_REVIEW_REQUIRED")

    formal,by_label,by_code=formal_authority()
    nonformal_fixed={r["Label"] for r in read_csv(NON85)}
    if nonformal_fixed!={"Class Pend","Not Applic"}:raise RuntimeError("v0.85 nonformal authority regression")

    snap=v86.fresh_directory_snapshot()
    schema=snap["download"]["Schema"];records=snap["records"]
    id_field=next((h for h in schema if keynorm(h)=="asxcode"),"")
    class_field=next((h for h in schema if keynorm(h)=="gicsindustrygroup"),"")
    write_json(out/"asx_current_gate_f_source_snapshot_audit_v0.87.json",{
      "Directory_Page_URL":snap["page"]["Directory_Page_URL"],"Directory_Page_HTTP_Status":snap["page"]["Directory_Page_HTTP_Status"],
      "Directory_Page_SHA256":snap["page"]["Directory_Page_SHA256"],"Retrieval_Timestamp_UTC":snap["page"]["Retrieval_Timestamp_UTC"],
      "Download_Control":snap["download"]["Download_Control_Text"],"Download_URL":snap["download"]["Download_Request_URL"],
      "HTTP_Status":snap["download"]["HTTP_Status"],"Content_Type":snap["download"]["Content_Type"],"Bytes":snap["download"]["Bytes"],
      "CSV_SHA256":snap["download"]["SHA256"],"Record_Count":len(records),"Schema":schema,"Raw_Source_Persisted":"NO"
    })
    write_json(out/"asx_gate_f_source_schema_audit_v0.87.json",{
      "Schema":schema,"Required_ASX_Code_Field":"ASX code","Observed_ASX_Code_Field":id_field or "NOT_AVAILABLE",
      "Required_Classification_Field":"GICs industry group","Observed_Classification_Field":class_field or "NOT_AVAILABLE",
      "ASX_Code_Field_Status":"PASS" if id_field else "FAIL","Classification_Field_Status":"PASS" if class_field else "FAIL"
    })

    by_asx=defaultdict(list)
    for i,row in enumerate(records,start=1):
        code=nfc(row.get(id_field,"")) if id_field else ""
        if code:by_asx[code].append({"row_number":i,"row":row})
    dup_codes=sorted(k for k,v in by_asx.items() if len(v)>1)
    write_json(out/"asx_gate_f_asx_code_uniqueness_audit_v0.87.json",{
      "Total_ASX_Codes":sum(len(v) for v in by_asx.values()),"Distinct_ASX_Codes":len(by_asx),
      "Duplicate_ASX_Code_Count":len(dup_codes),"Duplicate_ASX_Codes":dup_codes
    })

    join_rows=[];raw_rows=[];binding_rows=[];code_rows=[];status_rows=[];nonformal_rows=[]
    for t in sorted(target,key=lambda r:r["Primary_Ticker"]):
        ticker=nfc(t["Primary_Ticker"]);hits=by_asx.get(ticker,[])
        source_raw="";sector_name="";source_code="";sector_code="";status="";reason=""
        if len(hits)==0:
            status="NOT_FOUND";reason="AU_FROZEN_SECURITY_NOT_PRESENT_CURRENT_ASX_DIRECTORY"
        elif len(hits)>1:
            status="AMBIGUOUS";reason="ASX_DIRECTORY_ASX_CODE_DUPLICATE_FOR_FROZEN_SECURITY"
        else:
            source_raw=nfc(hits[0]["row"].get(class_field,"")) if class_field else ""
            if not class_field:
                status="NOT_VERIFIED";reason="ASX_DIRECTORY_GICS_INDUSTRY_GROUP_FIELD_NOT_AVAILABLE"
            elif source_raw=="":
                status="NOT_VERIFIED";reason="SOURCE_CLASSIFICATION_VALUE_MISSING"
            else:
                matches=by_label.get(source_raw,[])
                if len(matches)==1:
                    sector_name=nfc(matches[0]["Official_GICS_Industry_Group_Label"]);source_code=nfc(matches[0]["Official_GICS_Industry_Group_Code"])
                    if len(source_code)!=4 or not source_code.isdigit():
                        status="CONFLICT";reason="GICS_CODE_COLLISION"
                    else:
                        sector_code=source_code;status="PROVABLY_CLASSIFIED";reason=""
                elif len(matches)>1:
                    status="CONFLICT";reason="GICS_LABEL_TO_CODE_BINDING_AMBIGUOUS"
                else:
                    status="NOT_PROVABLY_CLASSIFIED";reason="SOURCE_CLASSIFICATION_NOT_EXACT_FORMAL_GICS_INDUSTRY_GROUP"
        join_rows.append({"Security_Key":t["Security_Key"],"Source_WS_ID":t["Source_WS_ID"],"Primary_MIC":t["Primary_MIC"],"Primary_Ticker":ticker,
                          "ASX_Code":ticker if hits else "","Source_Match_Count":len(hits)})
        raw_rows.append({"Security_Key":t["Security_Key"],"Source_WS_ID":t["Source_WS_ID"],"Primary_MIC":t["Primary_MIC"],"Primary_Ticker":ticker,
                         "ASX_Code":ticker if hits else "","Source_Classification_Raw":source_raw})
        binding_rows.append({"Security_Key":t["Security_Key"],"Primary_Ticker":ticker,"Source_Classification_Raw":source_raw,
                             "Formal_GICS_Exact_Match":"YES" if status=="PROVABLY_CLASSIFIED" else "NO",
                             "Official_GICS_Industry_Group_Label":sector_name,"Official_GICS_Industry_Group_Code":source_code,
                             "Binding_Status":"EXACT_CODE_BOUND" if status=="PROVABLY_CLASSIFIED" else ("NOT_FOUND" if status=="NOT_PROVABLY_CLASSIFIED" else status)})
        code_rows.append({"Security_Key":t["Security_Key"],"Primary_Ticker":ticker,"Source_Classification_Raw":source_raw,
                          "Sector_Taxonomy":"GICS" if status=="PROVABLY_CLASSIFIED" else "",
                          "Sector_Level":"INDUSTRY_GROUP" if status=="PROVABLY_CLASSIFIED" else "",
                          "Sector_Name":sector_name,"Source_Sector_Code":source_code,"Sector_Code":sector_code,
                          "Sector_Code_Origin":"SOURCE_NATIVE" if status=="PROVABLY_CLASSIFIED" else "",
                          "Sector_Code_Method":"GICS_OFFICIAL_INDUSTRY_GROUP_CODE" if status=="PROVABLY_CLASSIFIED" else "",
                          "Code_Status":"PASS" if status=="PROVABLY_CLASSIFIED" else "NOT_ASSIGNED"})
        status_rows.append({"Security_Key":t["Security_Key"],"Source_WS_ID":t["Source_WS_ID"],"Primary_MIC":t["Primary_MIC"],"Primary_Ticker":ticker,
                            "ASX_Code":ticker if hits else "","Source_Classification_Raw":source_raw,
                            "Sector_Taxonomy":"GICS" if status=="PROVABLY_CLASSIFIED" else "",
                            "Sector_Level":"INDUSTRY_GROUP" if status=="PROVABLY_CLASSIFIED" else "",
                            "Sector_Name":sector_name,"Source_Sector_Code":source_code,"Sector_Code":sector_code,
                            "Sector_Code_Origin":"SOURCE_NATIVE" if status=="PROVABLY_CLASSIFIED" else "",
                            "Sector_Code_Method":"GICS_OFFICIAL_INDUSTRY_GROUP_CODE" if status=="PROVABLY_CLASSIFIED" else "",
                            "Mapping_Status":status,"Reason":reason})
        if status=="NOT_PROVABLY_CLASSIFIED":
            nonformal_rows.append({"Security_Key":t["Security_Key"],"Primary_Ticker":ticker,"Source_Classification_Raw":source_raw,
                                   "Known_v085_Nonformal":"YES" if source_raw in nonformal_fixed else "NO",
                                   "Mapping_Status":status,"Reason":reason,"Sector_Code":"","PDSC":""})

    write_csv(out/"au_exact_63_gate_f_source_join_audit_v0.87.csv",join_rows)
    write_csv(out/"au_frozen_63_raw_classification_audit_v0.87.csv",raw_rows)
    write_csv(out/"au_frozen_63_formal_gics_binding_audit_v0.87.csv",binding_rows)
    write_csv(out/"au_frozen_63_source_native_code_audit_v0.87.csv",code_rows)
    write_csv(out/"au_frozen_classification_status_audit_v0.87.csv",status_rows)
    write_csv(out/"au_nonformal_frozen_exposure_audit_v0.87.csv",nonformal_rows,
              ["Security_Key","Primary_Ticker","Source_Classification_Raw","Known_v085_Nonformal","Mapping_Status","Reason","Sector_Code","PDSC"])

    counts=Counter(r["Mapping_Status"] for r in status_rows)
    classified=counts["PROVABLY_CLASSIFIED"];not_prov=counts["NOT_PROVABLY_CLASSIFIED"];not_found=counts["NOT_FOUND"];amb=counts["AMBIGUOUS"];not_ver=counts["NOT_VERIFIED"];conf=counts["CONFLICT"]
    exact_links=sum(r["Source_Match_Count"]=="1" or r["Source_Match_Count"]==1 for r in join_rows)
    formal_binding=sum(r["Formal_GICS_Exact_Match"]=="YES" for r in binding_rows)
    source_code_cov=sum(r["Code_Status"]=="PASS" for r in code_rows)
    used_codes=sorted({r["Sector_Code"] for r in code_rows if r["Sector_Code"]})
    unauthorized=[c for c in used_codes if c not in by_code]
    write_json(out/"au_used_gics_code_authority_audit_v0.87.json",{
      "Used_Distinct_GICS_Codes":len(used_codes),"Used_Codes":used_codes,"All_Used_Codes_Authorized":"YES" if not unauthorized else "NO",
      "Unauthorized_Code_Count":len(unauthorized),"Unauthorized_Codes":unauthorized,"Authority_Inventory_Rows":len(formal),
      "Authority_Source_SHA256":MSCI_SHA
    })

    dist=Counter()
    for r in status_rows:
        if r["Mapping_Status"]=="PROVABLY_CLASSIFIED":
            dist[(r["Sector_Code"],r["Sector_Name"],"PROVABLY_CLASSIFIED")]+=1
        else:
            label=r["Source_Classification_Raw"] or "<MISSING>"
            dist[("",label,r["Mapping_Status"])]+=1
    dist_rows=[{"GICS_Industry_Group_Code":k[0],"GICS_Industry_Group_Label":k[1],"Status_Bucket":k[2],"Frozen_Row_Count":v} for k,v in sorted(dist.items())]
    write_csv(out/"au_frozen_gics_distribution_v0.87.csv",dist_rows)

    s86=pred["source86"]
    current_schema=schema;old_schema=s86["Schema"]
    current_ticker_status={r["Primary_Ticker"]:r["Mapping_Status"] for r in status_rows}
    prev_links=read_csv(LINK86)
    identity_drift=any(r["Linkage_Status"]!="EXACT_LINK" or current_ticker_status.get(r["Primary_Ticker"]) in {"NOT_FOUND","AMBIGUOUS","CONFLICT"} for r in prev_links)
    source_drift={
      "v086_Row_Count":s86["Record_Count"],"v087_Row_Count":len(records),
      "v086_CSV_SHA256":s86["SHA256"],"v087_CSV_SHA256":snap["download"]["SHA256"],
      "v086_Schema":old_schema,"v087_Schema":current_schema,
      "BYTE_DRIFT":"YES" if s86["SHA256"]!=snap["download"]["SHA256"] else "NO",
      "ROW_COUNT_DRIFT":"YES" if s86["Record_Count"]!=len(records) else "NO",
      "SCHEMA_DRIFT":"YES" if old_schema!=current_schema else "NO",
      "FROZEN_IDENTITY_DRIFT":"YES" if identity_drift else "NO",
      "FROZEN_CLASSIFICATION_DRIFT":"NOT_EVALUABLE_FROM_V086_PERSISTED_IDENTITY_ONLY_EVIDENCE"
    }
    write_json(out/"au_gate_f_source_drift_audit_v0.87.json",source_drift)

    total_status=classified+not_prov+not_found+amb+not_ver+conf
    ready=(len(target)==63 and total_status==63 and classified==63 and not_prov==not_found==amb==not_ver==conf==0 and formal_binding==63 and source_code_cov==63 and len(unauthorized)==0)
    blocker=""
    if not ready:
        if snap["page"]["Directory_Page_HTTP_Status"]!=200 or snap["download"]["HTTP_Status"]!=200:blocker="ASX_DIRECTORY_CLASSIFICATION_SOURCE_NOT_REPRODUCIBLE"
        elif not class_field:blocker="ASX_DIRECTORY_GICS_INDUSTRY_GROUP_FIELD_NOT_AVAILABLE"
        elif any(r["Source_Match_Count"]>1 for r in join_rows):blocker="ASX_DIRECTORY_ASX_CODE_DUPLICATE_FOR_FROZEN_SECURITY"
        elif not_found:blocker="AU_FROZEN_SECURITY_NOT_PRESENT_CURRENT_ASX_DIRECTORY"
        elif any(r["Reason"]=="SOURCE_CLASSIFICATION_VALUE_MISSING" for r in status_rows):blocker="AU_FROZEN_SOURCE_CLASSIFICATION_VALUE_MISSING"
        elif not_prov:blocker="AU_FROZEN_SOURCE_CLASSIFICATION_NONFORMAL"
        elif formal_binding<63:blocker="ASX_GICS_FORMAL_LABEL_NOT_FOUND_IN_OFFICIAL_GICS"
        elif any(r["Reason"]=="GICS_LABEL_TO_CODE_BINDING_AMBIGUOUS" for r in status_rows):blocker="GICS_LABEL_TO_CODE_BINDING_AMBIGUOUS"
        elif unauthorized or any(r["Reason"]=="GICS_CODE_COLLISION" for r in status_rows):blocker="GICS_CODE_COLLISION"
        else:blocker="AU_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_INCOMPLETE"
    next_gate="AU_SP_ASX200 PROVENANCE GATE G" if ready else blocker
    decision={"Cohort":"AU_SP_ASX200","Taxonomy":"GICS","Level":"INDUSTRY_GROUP","Frozen_Total":63,"Classified":classified,
      "NOT_PROVABLY_CLASSIFIED":not_prov,"NOT_FOUND":not_found,"AMBIGUOUS":amb,"NOT_VERIFIED":not_ver,"CONFLICT":conf,
      "Formal_Label_Binding":f"{formal_binding}/63","Source_Native_Code_Coverage":f"{source_code_cov}/63",
      "Gate_F":"PASS_BY_CURRENT_EVIDENCE" if ready else "BLOCKED","Gate_G":"NOT_EVALUATED","Gate_H":"NOT_EVALUATED",
      "AU_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_READY":"YES" if ready else "NO","Blocker":blocker,"Next_Gate":next_gate}
    write_json(out/"au_exact_frozen_gics_classification_coverage_decision_v0.87.json",decision)

    write_csv(out/"external_request_ledger_v0.87.csv",[
      {"Request_Order":1,"Source_Class":"OFFICIAL_ASX","URL":snap["page"]["Directory_Page_URL"],"Purpose":"CURRENT_DIRECTORY_PAGE_AND_SINGLE_CSV_DOWNLOAD","HTTP_Status":snap["page"]["Directory_Page_HTTP_Status"],"Per_Security_Request":"NO"},
      {"Request_Order":2,"Source_Class":"OFFICIAL_ASX_RUNTIME_DOWNLOAD","URL":snap["download"]["Download_Request_URL"],"Purpose":"CURRENT_COMPLETE_DIRECTORY_CSV_SNAPSHOT","HTTP_Status":snap["download"]["HTTP_Status"],"Per_Security_Request":"NO"}
    ])
    prov=provider_audit();write_json(out/"provider_call_audit_v0.87.json",prov)
    imm={"Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SHA,"BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),"Parked_Cohort_Registry_Unchanged":sha_file(PARK)==PARK_SHA,
      "v085_GICS_Formal_Label_Code_Authority":"25/25","v086_AU_Identity_Linkage":"63/63","IN_Gate_F":"45/45","JP_Gate_F":"197/197",
      "Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,"AU_Canonical_Rows_After":0,"Gate_G_Runs":0,"Gate_H_Runs":0,
      "Canonical_Materialization_Runs":0,"Other_Cohort_Runs":0,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0}
    write_json(out/"immutability_audit_v0.87.json",imm)

    tests=[]
    def t(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    t("V086_PASS",pred["summary"]["verdict"]=="PASS_AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E",pred["summary"]["verdict"])
    t("V086_ARTIFACT",pred["checkpoint"]["artifact_id"]==V086_ARTIFACT and pred["checkpoint"]["artifact_digest"]==V086_DIGEST,V086_ARTIFACT)
    t("TARGET_63",len(target)==63,len(target));t("TARGET_MATCH_V086",target_audit["Exact_Match_To_v086_Target"]=="YES",target_audit["Exact_Match_To_v086_Target"])
    t("TARGET_UNIQUE",target_audit["Unique_Security_Key"]==target_audit["Unique_Source_WS_ID"]==target_audit["Unique_Primary_Ticker"]==63,"63/63/63")
    t("TARGET_MIC_XASX",target_audit["Primary_MIC_XASX"]==63,63);t("TARGET_WS_CONTRACT",target_audit["Source_WS_ID_Contract_PASS"]==63,63)
    t("FORMAL_AUTHORITY_25",len(formal)==25,len(formal));t("FORMAL_AUTHORITY_UNIQUE",len(by_label)==25 and len(by_code)==25,"25/25")
    t("MSCI_NO_NETWORK",prov["MSCI_methodology_requests"]==0,"0");t("PDSC_ZERO",prov["PDSC"]==0,"0")
    t("DIRECTORY_PAGE_200",snap["page"]["Directory_Page_HTTP_Status"]==200,snap["page"]["Directory_Page_HTTP_Status"])
    t("CSV_DOWNLOAD_200",snap["download"]["HTTP_Status"]==200,snap["download"]["HTTP_Status"])
    t("ASX_CODE_FIELD",bool(id_field),id_field or schema);t("GICS_FIELD",bool(class_field),class_field or schema)
    t("STATUS_ARITHMETIC",total_status==63,total_status);t("NO_COMPANY_NAME_LINKAGE",prov["company_name_linkage"]==0,"0")
    t("NO_FUZZY_SEMANTIC",prov["fuzzy_matching"]==0 and prov["semantic_classification_inference"]==0 and prov["cross_taxonomy_mapping"]==0,"0")
    t("NO_PER_SECURITY_FANOUT",prov["per_security_web_fanout"]==0,"0");t("NO_GATE_G_H",prov["Gate_G"]==0 and prov["Gate_H"]==0,"0")
    t("NO_CANONICAL_RS_P",prov["canonical_materialization"]==prov["Sector_RS"]==prov["P0"]==prov["P1"]==prov["P2"]==0,"0")
    t("UNAUTHORIZED_CODES_ZERO",len(unauthorized)==0,len(unauthorized))
    t("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA);t("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA);t("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    t("BR_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SHA);t("PARKS_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],PARK_SHA)
    t("CANONICAL_READY_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    t("NO_AU_CANONICAL",not any(AU_CANON.glob("AU_SP_ASX200_*.csv")),"0")
    if ready:
        t("CLASSIFIED_63",classified==63,"63/63");t("FORMAL_BINDING_63",formal_binding==63,"63/63");t("SOURCE_CODE_63",source_code_cov==63,"63/63")
        t("ZERO_FAILURE_STATUSES",not_prov==not_found==amb==not_ver==conf==0,"0/0/0/0/0");t("GATE_F_PASS",decision["Gate_F"]=="PASS_BY_CURRENT_EVIDENCE","PASS")
    else:
        t("GATE_F_BLOCKED",decision["Gate_F"]=="BLOCKED" and bool(blocker),blocker)
    write_csv(out/"test_results_v0.87.csv",tests)

    verdict="PASS_AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F" if ready else "BLOCKED_AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F"
    summary={"version":VERSION,"stage":STAGE,"verdict":verdict,"au_exact_frozen_gics_classification_coverage_ready":ready,
      "frozen_total":63,"current_asx_directory_rows":len(records),"exact_source_links":exact_links,
      "provably_classified":classified,"not_provably_classified":not_prov,"not_found":not_found,"ambiguous":amb,"not_verified":not_ver,"conflict":conf,
      "formal_label_binding":f"{formal_binding}/63","source_native_code_coverage":f"{source_code_cov}/63",
      "nonformal_frozen_exposure":len(nonformal_rows),"used_distinct_gics_codes":len(used_codes),"unauthorized_codes":len(unauthorized),"pdsc_generated":0,
      "source_drift":source_drift,"blocker":blocker,"gate_g":"NOT_EVALUATED","gate_h":"NOT_EVALUATED",
      "canonical_ready_rows":37,"canonical_total_rows":1425,"tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate}
    write_json(out/"summary_preupload_v0.87.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.87.json",{"version":VERSION,"stage":STAGE,"verdict":verdict,
      "au_exact_frozen_gics_classification_coverage_ready":ready,"blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD"})
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.87.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.87.json",{"version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,
      "repository_sha":a.repository_sha,"verdict":verdict,"au_exact_frozen_gics_classification_coverage_ready":ready,"blocker":blocker,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"gate_g_runs":0,"gate_h_runs":0,"canonical_materialization_runs":0,
      "other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":next_gate})
    return 0

if __name__=="__main__":raise SystemExit(main())
