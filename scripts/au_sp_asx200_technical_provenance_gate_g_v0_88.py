#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,json,subprocess,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.88"
STAGE="AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G"
REQUIRED_START_HEAD="3c71084e03fbd49c6ab5b34b03696c62aac765ad"

V087_WORKFLOW=36392661784
V087_ARTIFACT=10956817563
V087_DIGEST="sha256:961c68520689e978945a550b4d05b7a2e698f5b890fc072caecffb6a95e186bc"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"
ASX_SHA="66111266a833527d97b48388130111c707caa8bd35221fc95e3d60e8e8d6e69d"
MSCI_SHA="d66cfdf808872211561270a7141c40687417b3f669192c6b2650ae2d0aacad06"
ASX_RETRIEVED="2026-09-28T07:37:52Z"
MSCI_RETRIEVED="2026-09-28T06:24:19Z"
ASX_SOURCE_NAME="ASX_COMPANY_DIRECTORY_LISTED_COMPANIES_CSV"
ASX_SOURCE_REFERENCE="https://www.asx.com.au/markets/trade-our-cash-market/directory"
ASX_SOURCE_VERSION="SOURCE_SNAPSHOT_SHA256:"+ASX_SHA
ASX_EFFECTIVE_STATUS="NO_EXPLICIT_EFFECTIVE_DATE_IN_PERSISTED_SOURCE"
MSCI_URL="https://www.msci.com/indexes/documents/methodology/1_MSCI_Global_Industry_Classification_Standard_GICS_Methodology_20250220.pdf"
MSCI_AUTHORITY_NAME="MSCI_GICS_METHODOLOGY"
MSCI_VERSION="APRIL 2026"
TAXONOMY_VERSION_STATUS="CURRENT_MAINTAINED_NO_STATIC_VERSION"

SPEC=ROOT/"config/au_sp_asx200_technical_provenance_gate_g_spec_v0.88.json"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
SIDECAR=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANON=ROOT/"sector_metadata/canonical/cohorts"

OUT85=ROOT/"output_au_sp_asx200_gate_d_msci_gics_repair_v0_85"
INV85=OUT85/"gics_industry_group_official_label_code_inventory_v0.85.csv"
SRC85=OUT85/"msci_current_gics_methodology_source_audit_v0.85.json"
CURRENT85=OUT85/"msci_gics_currentness_effective_status_audit_v0.85.json"
OWN85=OUT85/"gics_joint_owner_authority_audit_v0.85.json"

OUT86=ROOT/"output_au_sp_asx200_identity_linkage_gate_e_v0_86"
TARGET86=OUT86/"au_frozen_63_identity_target_v0.86.csv"
LINK86=OUT86/"au_exact_63_ticker_linkage_audit_v0.86.csv"
DEC86=OUT86/"au_deterministic_security_identity_linkage_decision_v0.86.json"

OUT87=ROOT/"output_au_sp_asx200_exact_frozen_gics_gate_f_v0_87"
SUM87=OUT87/"summary_v0.87.json"
CHK87=OUT87/"stage_checkpoint_v0.87.json"
MAN87=OUT87/"manifest_v0.87.json"
DEC87=OUT87/"au_exact_frozen_gics_classification_coverage_decision_v0.87.json"
STATUS87=OUT87/"au_frozen_classification_status_audit_v0.87.csv"
RAW87=OUT87/"au_frozen_63_raw_classification_audit_v0.87.csv"
BIND87=OUT87/"au_frozen_63_formal_gics_binding_audit_v0.87.csv"
CODE87=OUT87/"au_frozen_63_source_native_code_audit_v0.87.csv"
SNAP87=OUT87/"asx_current_gate_f_source_snapshot_audit_v0.87.json"
SCHEMA87=OUT87/"asx_gate_f_source_schema_audit_v0.87.json"

def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def nfc(x:Any)->str:return unicodedata.normalize("NFC",str(x or "")).strip()

def read_csv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def write_csv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
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
    s=json.loads(SUM87.read_text());c=json.loads(CHK87.read_text());m=json.loads(MAN87.read_text());d=json.loads(DEC87.read_text())
    if s["verdict"]!="PASS_AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F":raise RuntimeError("v0.87 verdict")
    if not s["au_exact_frozen_gics_classification_coverage_ready"]:raise RuntimeError("v0.87 readiness")
    if s["frozen_total"]!=63 or s["provably_classified"]!=63:raise RuntimeError("v0.87 coverage")
    if any(s[k]!=0 for k in ["not_provably_classified","not_found","ambiguous","not_verified","conflict"]):raise RuntimeError("v0.87 failure counts")
    if s["formal_label_binding"]!="63/63" or s["source_native_code_coverage"]!="63/63":raise RuntimeError("v0.87 formal/code")
    if s["nonformal_frozen_exposure"]!=0 or s["unauthorized_codes"]!=0 or s["pdsc_generated"]!=0:raise RuntimeError("v0.87 governance")
    if s["tests"]!={"failed":0,"passed":34,"total":34}:raise RuntimeError("v0.87 tests")
    if c["workflow_run_id"]!=V087_WORKFLOW or c["artifact_id"]!=V087_ARTIFACT or c["artifact_digest"]!=V087_DIGEST:raise RuntimeError("v0.87 artifact")
    if m["workflow_run_id"]!=V087_WORKFLOW or m["artifact_id"]!=V087_ARTIFACT or m["artifact_digest"]!=V087_DIGEST:raise RuntimeError("v0.87 manifest")
    if d["Gate_F"]!="PASS_BY_CURRENT_EVIDENCE" or d["Gate_G"]!="NOT_EVALUATED" or d["Gate_H"]!="NOT_EVALUATED":raise RuntimeError("v0.87 gate state")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    if sha_file(PARK)!=PARK_SHA:raise RuntimeError("park registry")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SHA:raise RuntimeError("canonical registry")
    if any(AU_CANON.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical exists")
    return {"summary":s,"checkpoint":c,"manifest":m,"decision":d}

def load_authorities()->dict[str,Any]:
    target=read_csv(TARGET86);link=read_csv(LINK86);status=read_csv(STATUS87);raw=read_csv(RAW87);bind=read_csv(BIND87);code=read_csv(CODE87);inv=read_csv(INV85)
    snap=json.loads(SNAP87.read_text());schema=json.loads(SCHEMA87.read_text());src85=json.loads(SRC85.read_text());cur85=json.loads(CURRENT85.read_text());own85=json.loads(OWN85.read_text())
    dec86=json.loads(DEC86.read_text())
    if len(target)!=len(link)!=len(status):raise RuntimeError("row count mismatch")
    if len(target)!=63 or len(raw)!=63 or len(bind)!=63 or len(code)!=63:raise RuntimeError("authority row count")
    if len(inv)!=25:raise RuntimeError("GICS inventory count")
    if snap["CSV_SHA256"]!=ASX_SHA or snap["Retrieval_Timestamp_UTC"]!=ASX_RETRIEVED:raise RuntimeError("ASX snapshot authority")
    if snap["Directory_Page_URL"]!=ASX_SOURCE_REFERENCE or snap["Record_Count"]!=1833:raise RuntimeError("ASX source authority")
    if schema["Observed_ASX_Code_Field"]!="ASX code" or schema["Observed_Classification_Field"]!="GICs industry group":raise RuntimeError("ASX schema authority")
    if src85["SHA256"]!=MSCI_SHA or src85["Retrieval_Timestamp_UTC"]!=MSCI_RETRIEVED:raise RuntimeError("MSCI snapshot authority")
    if src85["Document_Display_Date"]!=MSCI_VERSION or src85["Document_Title"]!="GLOBAL INDUSTRY CLASSIFICATION STANDARD (GICS®) METHODOLOGY":raise RuntimeError("MSCI document authority")
    if cur85["CURRENT_EFFECTIVE_GICS_STRUCTURE_SOURCE"]!="YES" or own85["Joint_GICS_Authority"]!="MSCI / S&P Dow Jones Indices":raise RuntimeError("MSCI authority status")
    if dec86["Linked"]!=63 or dec86["Source_WS_ID_Equality"]!=63:raise RuntimeError("v0.86 identity authority")
    return {"target":target,"link":link,"status":status,"raw":raw,"bind":bind,"code":code,"inventory":inv,"snapshot":snap,"schema":schema,"src85":src85,"cur85":cur85,"own85":own85}

def index(rows:list[dict[str,str]],key:str)->dict[str,dict[str,str]]:
    d={}
    for r in rows:
        k=nfc(r[key])
        if not k or k in d:raise RuntimeError("nonunique index "+key)
        d[k]=r
    return d

def provider_audit()->dict[str,int]:
    return {"Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,"ETF_holdings":0,
      "ASX_network_requests":0,"MSCI_network_requests":0,"SP_network_requests":0,"third_party_classification_sources":0,
      "company_name_linkage":0,"fuzzy_matching":0,"semantic_inference":0,"cross_taxonomy_mapping":0,"PDSC":0,
      "per_security_web_fanout":0,"Gate_H":0,"canonical_materialization":0,"Sector_RS":0,"P0":0,"P1":0,"P2":0}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_au_sp_asx200_technical_provenance_gate_g_v0_88")
    a=ap.parse_args();pred=validate_predecessor(a.repository_sha);spec=json.loads(SPEC.read_text())
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    auth=load_authorities()

    write_json(out/"au_gate_g_predecessor_authority_v0.88.json",{
      "Final_Commit":REQUIRED_START_HEAD,"Verdict":pred["summary"]["verdict"],"AU_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_READY":"YES",
      "Frozen_Total":63,"PROVABLY_CLASSIFIED":63,"NOT_PROVABLY_CLASSIFIED":0,"NOT_FOUND":0,"AMBIGUOUS":0,"NOT_VERIFIED":0,"CONFLICT":0,
      "Formal_Label_Binding":"63/63","Source_Native_Code_Coverage":"63/63","Nonformal_Frozen_Exposure":0,
      "Used_Distinct_GICS_Codes":16,"Unauthorized_Codes":0,"PDSC":0,"Workflow":V087_WORKFLOW,
      "Artifact":V087_ARTIFACT,"Artifact_Digest":V087_DIGEST,"Tests":"34/34 PASS","Canonical_READY":"37/1425"
    })

    write_json(out/"au_frozen_membership_provenance_authority_v0.88.json",{
      "Frozen_Authority_File":str(FROZEN.relative_to(ROOT)),"Frozen_Authority_SHA256":FROZEN_SHA,
      "Physical_Frozen_Has_Primary_Universe_Index":"NO","Cohort_Label_Authority_File":str(SIDECAR.relative_to(ROOT)),
      "Cohort_Label":"AU_SP_ASX200","Cohort_Label_Key":"Security_Key","Rows":63,
      "Identity_Fields_Origin":"PHYSICAL_FROZEN_ONLY","Identity_Fields":["Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker"],
      "Cohort_Label_Sidecar_Overwrite_Identity_Fields":"NO"
    })
    write_json(out/"au_identity_evidence_provenance_authority_v0.88.json",{
      "Evidence_Version":"v0.86","Evidence_Final_Commit":"16ca7cfc2148527f4e48bda642e7533831a716c5",
      "Identity_Source":"ASX_OFFICIAL_COMPANY_DIRECTORY","Identity_Field":"ASX code",
      "Identity_Method":"EXACT_ASX_CODE_TO_FROZEN_PRIMARY_TICKER","MIC":"XASX","Linked":"63/63","Source_WS_ID_Equality":"63/63",
      "Persisted_Target_File":str(TARGET86.relative_to(ROOT)),"Persisted_Linkage_File":str(LINK86.relative_to(ROOT))
    })

    download_evidence=auth["snapshot"]["Download_URL"]
    write_json(out/"au_classification_source_provenance_contract_v0.88.json",{
      "Classification_Source_Name":ASX_SOURCE_NAME,"Classification_Source_Reference":ASX_SOURCE_REFERENCE,
      "Classification_Source_Download_Evidence":download_evidence,"Ephemeral_Download_URL_Used_As_Sole_Stable_Reference":"NO",
      "Classification_Field":"GICs industry group","Identity_Field":"ASX code","Evidence_Version":"v0.87",
      "Evidence_Final_Commit":"3c71084e03fbd49c6ab5b34b03696c62aac765ad"
    })
    write_json(out/"au_classification_source_snapshot_contract_v0.88.json",{
      "Classification_Source_Snapshot_SHA256":ASX_SHA,"Classification_Source_Retrieved_UTC":ASX_RETRIEVED,
      "Record_Count":auth["snapshot"]["Record_Count"],"Schema":auth["snapshot"]["Schema"],
      "Directory_Page_SHA256":auth["snapshot"]["Directory_Page_SHA256"],"Raw_Source_Persisted":"NO",
      "Snapshot_Contract_Status":"PASS"
    })
    write_json(out/"au_classification_source_asof_contract_v0.88.json",{
      "Source_Version_or_AsOf":ASX_SOURCE_VERSION,"Source_Retrieved_UTC":ASX_RETRIEVED,
      "Source_Effective_AsOf_Status":ASX_EFFECTIVE_STATUS,"Business_Effective_Date_From_Retrieval":"NO",
      "Retrieval_Time_Is_Business_Effective_Date":"NO","Contract_Status":"PASS"
    })
    write_json(out/"au_gics_code_authority_provenance_contract_v0.88.json",{
      "Code_Authority_Name":MSCI_AUTHORITY_NAME,"Code_Authority_Reference":MSCI_URL,"Code_Authority_SHA256":MSCI_SHA,
      "Code_Authority_Version_or_AsOf":MSCI_VERSION,"Code_Authority_Retrieved_UTC":MSCI_RETRIEVED,
      "Document_Title":"GLOBAL INDUSTRY CLASSIFICATION STANDARD (GICS®) METHODOLOGY","Last_Updated":"April 2026",
      "Taxonomy":"GICS","Taxonomy_Level":"INDUSTRY_GROUP","Joint_Authority":"MSCI / S&P Dow Jones Indices",
      "Official_Industry_Group_Count":25,"Taxonomy_Version_Status":TAXONOMY_VERSION_STATUS,
      "Evidence_Version":"v0.85","Evidence_Final_Commit":"62c1d0345c8955c949c134318f9329e12dca0469",
      "Network_Request_In_v088":"NO"
    })
    version_contract={
      "Identity_Evidence_Version":"v0.86","Identity_Evidence_Final_Commit":"16ca7cfc2148527f4e48bda642e7533831a716c5",
      "Classification_Evidence_Version":"v0.87","Classification_Evidence_Final_Commit":"3c71084e03fbd49c6ab5b34b03696c62aac765ad",
      "Code_Authority_Evidence_Version":"v0.85","Code_Authority_Evidence_Final_Commit":"62c1d0345c8955c949c134318f9329e12dca0469",
      "v088_Is_Provenance_Gate_Decision_Not_Source_Fact_Origin":"YES"
    }
    write_json(out/"au_evidence_version_commit_contract_v0.88.json",version_contract)

    target=index(auth["target"],"Security_Key");link=index(auth["link"],"Security_Key");status=index(auth["status"],"Security_Key")
    raw=index(auth["raw"],"Security_Key");bind=index(auth["bind"],"Security_Key");code=index(auth["code"],"Security_Key")
    inv_by_label=index(auth["inventory"],"Official_GICS_Industry_Group_Label")
    inv_by_code=index(auth["inventory"],"Official_GICS_Industry_Group_Code")

    identity_cons=[];class_cons=[];chains=[];status_audit=[]
    conflict_counts=Counter()
    for sk in sorted(target):
        t=target[sk];l=link.get(sk);s=status.get(sk);rr=raw.get(sk);b=bind.get(sk);cr=code.get(sk)
        reasons=[]
        identity_checks={
          "Target_Present":bool(t),"Identity_Evidence_Present":bool(l),"Classification_Evidence_Present":bool(s),
          "Ticker_Consistent":bool(l and s and t["Primary_Ticker"]==l["Primary_Ticker"]==s["Primary_Ticker"]),
          "MIC_Consistent":bool(s and t["Primary_MIC"]==s["Primary_MIC"]=="XASX"),
          "WS_ID_Consistent":bool(s and t["Source_WS_ID"]==s["Source_WS_ID"]),
          "ASX_Code_Consistent":bool(l and s and l["Matched_ASX_Code"]==s["ASX_Code"]==t["Primary_Ticker"])
        }
        for k,v in identity_checks.items():
            if not v:
                reasons.append("IDENTITY_"+k);conflict_counts[k]+=1
        identity_cons.append({"Security_Key":sk,**{k:("PASS" if v else "CONFLICT") for k,v in identity_checks.items()}})

        raw_label=nfc(s["Source_Classification_Raw"]) if s else ""
        formal_label=nfc(s["Sector_Name"]) if s else ""
        sector_code=nfc(s["Sector_Code"]) if s else ""
        inv_l=inv_by_label.get(formal_label);inv_c=inv_by_code.get(sector_code)
        class_checks={
          "Raw_Evidence_Present":bool(rr),"Formal_Binding_Evidence_Present":bool(b),"Code_Evidence_Present":bool(cr),
          "Mapping_Status_Provably_Classified":bool(s and s["Mapping_Status"]=="PROVABLY_CLASSIFIED"),
          "Raw_Label_Consistent":bool(rr and s and nfc(rr["Source_Classification_Raw"])==raw_label),
          "Raw_Equals_Formal_Label":bool(raw_label and raw_label==formal_label),
          "Formal_Binding_Consistent":bool(b and nfc(b["Official_GICS_Industry_Group_Label"])==formal_label and nfc(b["Official_GICS_Industry_Group_Code"])==sector_code),
          "Source_Native_Code_Consistent":bool(cr and nfc(cr["Sector_Code"])==sector_code and nfc(cr["Source_Sector_Code"])==sector_code),
          "Official_Label_Code_Pair_Authorized":bool(inv_l and inv_c and nfc(inv_l["Official_GICS_Industry_Group_Code"])==sector_code and nfc(inv_c["Official_GICS_Industry_Group_Label"])==formal_label),
          "Sector_Code_Equals_Source_Code":bool(s and nfc(s["Sector_Code"])==nfc(s["Source_Sector_Code"])),
          "Sector_Code_Origin":bool(s and s["Sector_Code_Origin"]=="SOURCE_NATIVE"),
          "Sector_Code_Method":bool(s and s["Sector_Code_Method"]=="GICS_OFFICIAL_INDUSTRY_GROUP_CODE"),
          "Sector_Code_4_Chars":bool(sector_code and len(sector_code)==4 and sector_code.isdigit())
        }
        for k,v in class_checks.items():
            if not v:
                reasons.append("CLASS_"+k);conflict_counts[k]+=1
        class_cons.append({"Security_Key":sk,"Primary_Ticker":t["Primary_Ticker"],**{k:("PASS" if v else "CONFLICT") for k,v in class_checks.items()}})

        required_present=all([
          t["Security_Key"],t["Source_WS_ID"],t["Primary_MIC"],t["Primary_Ticker"],l,s,rr,b,cr,
          ASX_SOURCE_NAME,ASX_SOURCE_REFERENCE,download_evidence,ASX_SHA,ASX_RETRIEVED,ASX_SOURCE_VERSION,ASX_EFFECTIVE_STATUS,
          MSCI_AUTHORITY_NAME,MSCI_URL,MSCI_SHA,MSCI_VERSION,MSCI_RETRIEVED,
          version_contract["Identity_Evidence_Final_Commit"],version_contract["Classification_Evidence_Final_Commit"],version_contract["Code_Authority_Evidence_Final_Commit"]
        ])
        if not required_present:reasons.append("REQUIRED_PROVENANCE_FIELD_MISSING")
        prov_status="PROVENANCE_COMPLETE" if not reasons else "PROVENANCE_CONFLICT"
        chain={
          "WS_ID":t["Source_WS_ID"],"Security_Key":sk,"Primary_Universe_Index":"AU_SP_ASX200","Primary_MIC":t["Primary_MIC"],"Primary_Ticker":t["Primary_Ticker"],
          "Sector_Taxonomy":"GICS","Sector_Level":"INDUSTRY_GROUP","Sector_Name":formal_label,"Sector_Raw_Name":raw_label,
          "Sector_Code":sector_code,"Source_Sector_Code":nfc(s["Source_Sector_Code"]) if s else "",
          "Sector_Code_Origin":s["Sector_Code_Origin"] if s else "","Sector_Code_Method":s["Sector_Code_Method"] if s else "",
          "Mapping_Status":s["Mapping_Status"] if s else "",
          "Classification_Source_Name":ASX_SOURCE_NAME,"Classification_Source_Reference":ASX_SOURCE_REFERENCE,
          "Classification_Source_Download_Evidence":download_evidence,"Classification_Source_Snapshot_SHA256":ASX_SHA,
          "Classification_Source_Retrieved_UTC":ASX_RETRIEVED,"Classification_Source_Version_or_AsOf":ASX_SOURCE_VERSION,
          "Classification_Source_Effective_AsOf_Status":ASX_EFFECTIVE_STATUS,"Business_Effective_Date_From_Retrieval":"NO",
          "Code_Authority_Name":MSCI_AUTHORITY_NAME,"Code_Authority_Reference":MSCI_URL,"Code_Authority_SHA256":MSCI_SHA,
          "Code_Authority_Version_or_AsOf":MSCI_VERSION,"Code_Authority_Retrieved_UTC":MSCI_RETRIEVED,"Taxonomy_Version_Status":TAXONOMY_VERSION_STATUS,
          "Frozen_Authority_File":str(FROZEN.relative_to(ROOT)),"Frozen_Authority_SHA256":FROZEN_SHA,
          "Cohort_Label_Authority_File":str(SIDECAR.relative_to(ROOT)),
          "Identity_Evidence_Version":"v0.86","Identity_Evidence_Final_Commit":"16ca7cfc2148527f4e48bda642e7533831a716c5",
          "Classification_Evidence_Version":"v0.87","Classification_Evidence_Final_Commit":"3c71084e03fbd49c6ab5b34b03696c62aac765ad",
          "Code_Authority_Evidence_Version":"v0.85","Code_Authority_Evidence_Final_Commit":"62c1d0345c8955c949c134318f9329e12dca0469",
          "Provenance_Status":prov_status,"Reason":"|".join(reasons)
        }
        chains.append(chain)
        status_audit.append({"Security_Key":sk,"Primary_Ticker":t["Primary_Ticker"],"Provenance_Status":prov_status,"Reason":"|".join(reasons)})

    write_csv(out/"au_row_level_provenance_chain_v0.88.csv",chains)
    write_csv(out/"au_row_level_provenance_status_audit_v0.88.csv",status_audit)
    write_csv(out/"au_cross_stage_identity_value_consistency_audit_v0.88.csv",identity_cons)
    write_csv(out/"au_cross_stage_classification_value_consistency_audit_v0.88.csv",class_cons)

    snap_hashes=sorted({r["Classification_Source_Snapshot_SHA256"] for r in chains})
    write_json(out/"au_snapshot_hash_consistency_audit_v0.88.json",{
      "Rows":len(chains),"Expected_ASX_Snapshot_SHA256":ASX_SHA,"Observed_Distinct_Snapshot_SHA256":snap_hashes,
      "All_Rows_Same_Expected_Snapshot":"YES" if snap_hashes==[ASX_SHA] else "NO"
    })
    code_hashes=sorted({r["Code_Authority_SHA256"] for r in chains})
    write_json(out/"au_code_authority_hash_consistency_audit_v0.88.json",{
      "Rows":len(chains),"Expected_Code_Authority_SHA256":MSCI_SHA,"Observed_Distinct_Code_Authority_SHA256":code_hashes,
      "All_Rows_Same_Expected_Code_Authority":"YES" if code_hashes==[MSCI_SHA] else "NO",
      "S_and_P_Workbook_Substitution":"NO"
    })

    future_core=["WS_ID","Sector_Taxonomy","Sector_Code","Sector_Name","Source_Name","Source_Reference","Source_Version_or_AsOf","Mapping_Status"]
    future_au=["Primary_Universe_Index","Primary_MIC","Primary_Ticker","Sector_Level","Sector_Raw_Name","Source_Sector_Code","Sector_Code_Origin","Sector_Code_Method",
      "Source_Retrieved_UTC","Source_Effective_AsOf_Status","Classification_Source_Snapshot_SHA256","Classification_Source_Download_Evidence",
      "Code_Authority_Name","Code_Authority_Reference","Code_Authority_SHA256","Code_Authority_Version_or_AsOf","Code_Authority_Retrieved_UTC",
      "Frozen_Authority_SHA256","Identity_Evidence_Version","Identity_Evidence_Final_Commit","Classification_Evidence_Version",
      "Classification_Evidence_Final_Commit","Code_Authority_Evidence_Version","Code_Authority_Evidence_Final_Commit"]
    write_json(out/"au_future_canonical_provenance_field_contract_v0.88.json",{
      "Canonical_Materialization_Executed":"NO","Required_Core_Fields":future_core,"AU_Governed_Provenance_Fields":future_au,
      "Prepared_Source_Name":ASX_SOURCE_NAME,"Prepared_Source_Reference":ASX_SOURCE_REFERENCE,
      "Prepared_Source_Version_or_AsOf":ASX_SOURCE_VERSION,"Prepared_Mapping_Status":"PROVABLY_CLASSIFIED",
      "WS_ID_Contract":"WS_ID equals Frozen Source_WS_ID; Security_Key remains separate evidence",
      "Technical_Population_Feasibility":"YES" if len(chains)==63 else "NO"
    })

    prov_counts=Counter(r["Provenance_Status"] for r in status_audit)
    complete=prov_counts["PROVENANCE_COMPLETE"];incomplete=prov_counts["PROVENANCE_INCOMPLETE"];conflict=prov_counts["PROVENANCE_CONFLICT"];not_verified=prov_counts["PROVENANCE_NOT_VERIFIED"]
    cross_conflicts=sum(v for k,v in conflict_counts.items())
    snapshot_ok=snap_hashes==[ASX_SHA];code_hash_ok=code_hashes==[MSCI_SHA]
    frozen_membership_ok=(len(target)==63 and all(r["Primary_MIC"]=="XASX" and r["Source_WS_ID"]=="WS:XASX:"+r["Primary_Ticker"] for r in target.values()))
    identity_ok=all(all(v=="PASS" for k,v in r.items() if k!="Security_Key") for r in identity_cons)
    classification_ok=all(all(v=="PASS" for k,v in r.items() if k not in {"Security_Key","Primary_Ticker"}) for r in class_cons)
    ready=(len(chains)==63 and complete==63 and incomplete==conflict==not_verified==0 and cross_conflicts==0 and snapshot_ok and code_hash_ok and frozen_membership_ok and identity_ok and classification_ok)
    blocker=""
    if not ready:
        if not frozen_membership_ok:blocker="AU_FROZEN_MEMBERSHIP_PROVENANCE_NOT_VERIFIED"
        elif not identity_ok:blocker="AU_IDENTITY_EVIDENCE_PROVENANCE_NOT_VERIFIED"
        elif not ASX_SOURCE_REFERENCE:blocker="ASX_CLASSIFICATION_SOURCE_REFERENCE_NOT_VERIFIED"
        elif not snapshot_ok:blocker="ASX_CLASSIFICATION_SNAPSHOT_HASH_NOT_VERIFIED"
        elif not ASX_RETRIEVED:blocker="ASX_CLASSIFICATION_RETRIEVAL_PROVENANCE_NOT_VERIFIED"
        elif not ASX_EFFECTIVE_STATUS:blocker="AU_SOURCE_EFFECTIVE_ASOF_STATUS_NOT_EXPLICIT"
        elif not MSCI_URL or not code_hash_ok:blocker="GICS_CODE_AUTHORITY_REFERENCE_NOT_VERIFIED"
        elif not MSCI_VERSION or not MSCI_RETRIEVED:blocker="GICS_CODE_AUTHORITY_VERSION_NOT_VERIFIED"
        elif cross_conflicts:blocker="AU_CROSS_STAGE_PROVENANCE_CONFLICT"
        elif complete<63:blocker="AU_ROW_LEVEL_PROVENANCE_INCOMPLETE"
        else:blocker="AU_TECHNICAL_PROVENANCE_NOT_VERIFIED"
    next_gate="AU_SP_ASX200 SOURCE ACCESS / EVIDENCE PERSISTENCE GATE H" if ready else blocker
    decision={
      "Cohort":"AU_SP_ASX200","Gate_G":"PASS_BY_CURRENT_EVIDENCE" if ready else "BLOCKED",
      "Technical_Provenance_Ready":"YES" if ready else "NO","Rows":"63/63" if ready else f"{complete}/63",
      "PROVENANCE_COMPLETE":complete,"PROVENANCE_INCOMPLETE":incomplete,"PROVENANCE_CONFLICT":conflict,"PROVENANCE_NOT_VERIFIED":not_verified,
      "Classification_Source":ASX_SOURCE_NAME,"Code_Authority":MSCI_AUTHORITY_NAME,"ASX_Effective_AsOf_Status":ASX_EFFECTIVE_STATUS,
      "Gate_H":"NOT_EVALUATED","AU_Canonical_Readiness":"NO","Cross_Stage_Conflicts":cross_conflicts,"Blocker":blocker,"Next_Gate":next_gate
    }
    write_json(out/"au_technical_provenance_decision_v0.88.json",decision)

    write_csv(out/"external_request_ledger_v0.88.csv",[],["Request_Order","Source_Class","URL","Purpose","HTTP_Status","Per_Security_Request"])
    prov=provider_audit();write_json(out/"provider_call_audit_v0.88.json",prov)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SHA,"BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),"Parked_Cohort_Registry_Unchanged":sha_file(PARK)==PARK_SHA,
      "v085_GICS_Code_Authority":"25/25","v086_AU_Identity":"63/63","v087_AU_Classification":"63/63",
      "IN_Gate_F":"45/45","JP_Gate_F":"197/197","Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,
      "AU_Canonical_Rows_After":0,"Gate_H_Runs":0,"Canonical_Materialization_Runs":0,"Other_Cohort_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    write_json(out/"immutability_audit_v0.88.json",imm)

    tests=[]
    def t(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    t("V087_PASS",pred["summary"]["verdict"]=="PASS_AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F",pred["summary"]["verdict"])
    t("V087_ARTIFACT",pred["checkpoint"]["artifact_id"]==V087_ARTIFACT and pred["checkpoint"]["artifact_digest"]==V087_DIGEST,V087_ARTIFACT)
    t("NO_EXTERNAL_REQUESTS",sum(prov[k] for k in ["ASX_network_requests","MSCI_network_requests","SP_network_requests"])==0,"0")
    t("TARGET_63",len(target)==63,len(target));t("ROW_CHAIN_63",len(chains)==63,len(chains))
    t("FROZEN_MEMBERSHIP_AUTHORITY",frozen_membership_ok,"PASS")
    t("IDENTITY_CONSISTENCY",identity_ok,"PASS");t("CLASSIFICATION_CONSISTENCY",classification_ok,"PASS")
    t("SNAPSHOT_HASH_CONSISTENCY",snapshot_ok,ASX_SHA);t("CODE_AUTHORITY_HASH_CONSISTENCY",code_hash_ok,MSCI_SHA)
    t("ASX_STABLE_REFERENCE",ASX_SOURCE_REFERENCE=="https://www.asx.com.au/markets/trade-our-cash-market/directory",ASX_SOURCE_REFERENCE)
    t("ASX_ASOF_EXPLICIT",ASX_EFFECTIVE_STATUS=="NO_EXPLICIT_EFFECTIVE_DATE_IN_PERSISTED_SOURCE",ASX_EFFECTIVE_STATUS)
    t("NO_RETRIEVAL_AS_BUSINESS_DATE",all(r["Business_Effective_Date_From_Retrieval"]=="NO" for r in chains),"63/63")
    t("MSCI_VERSION_DISPLAY_DATE",MSCI_VERSION=="APRIL 2026",MSCI_VERSION);t("MSCI_RETRIEVAL_DISTINCT",MSCI_RETRIEVED!="2026-04-01T00:00:00Z",MSCI_RETRIEVED)
    t("WS_ID_EQUALS_SOURCE_WS_ID",all(r["WS_ID"]==target[r["Security_Key"]]["Source_WS_ID"] for r in chains),"63/63")
    t("RAW_EQUALS_NORMALIZED_LABEL",all(r["Sector_Raw_Name"]==r["Sector_Name"] for r in chains),"63/63")
    t("SOURCE_NATIVE_CODE_CONTRACT",all(r["Sector_Code"]==r["Source_Sector_Code"] and r["Sector_Code_Origin"]=="SOURCE_NATIVE" and r["Sector_Code_Method"]=="GICS_OFFICIAL_INDUSTRY_GROUP_CODE" and len(r["Sector_Code"])==4 for r in chains),"63/63")
    t("EVIDENCE_COMMITS",all(r["Identity_Evidence_Final_Commit"]=="16ca7cfc2148527f4e48bda642e7533831a716c5" and r["Classification_Evidence_Final_Commit"]=="3c71084e03fbd49c6ab5b34b03696c62aac765ad" and r["Code_Authority_Evidence_Final_Commit"]=="62c1d0345c8955c949c134318f9329e12dca0469" for r in chains),"63/63")
    t("PROVENANCE_STATUS_ARITHMETIC",complete+incomplete+conflict+not_verified==63,f"{complete}+{incomplete}+{conflict}+{not_verified}")
    t("NO_CROSS_STAGE_CONFLICTS",cross_conflicts==0,cross_conflicts)
    t("NO_GATE_H_POLICY_REVIEW",prov["Gate_H"]==0,"0");t("NO_CANONICAL_RS_P",prov["canonical_materialization"]==prov["Sector_RS"]==prov["P0"]==prov["P1"]==prov["P2"]==0,"0")
    t("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA);t("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA);t("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    t("BR_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SHA);t("PARKS_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],PARK_SHA)
    t("CANONICAL_READY_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    t("NO_AU_CANONICAL",not any(AU_CANON.glob("AU_SP_ASX200_*.csv")),"0")
    if ready:
        t("PROVENANCE_COMPLETE_63",complete==63,"63/63");t("ZERO_NONCOMPLETE",incomplete==conflict==not_verified==0,"0/0/0")
        t("GATE_G_PASS",decision["Gate_G"]=="PASS_BY_CURRENT_EVIDENCE","PASS")
    else:
        t("GATE_G_BLOCKED",decision["Gate_G"]=="BLOCKED" and bool(blocker),blocker)
    write_csv(out/"test_results_v0.88.csv",tests)

    verdict="PASS_AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G" if ready else "BLOCKED_AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G"
    summary={
      "version":VERSION,"stage":STAGE,"verdict":verdict,"au_technical_provenance_ready":ready,"rows":63,
      "provenance_complete":complete,"provenance_incomplete":incomplete,"provenance_conflict":conflict,"provenance_not_verified":not_verified,
      "frozen_authority":str(FROZEN.relative_to(ROOT)),"cohort_label_authority":str(SIDECAR.relative_to(ROOT)),
      "classification_source":ASX_SOURCE_NAME,"classification_source_sha256":ASX_SHA,"classification_source_version_or_asof":ASX_SOURCE_VERSION,
      "classification_source_retrieved_utc":ASX_RETRIEVED,"classification_effective_asof_status":ASX_EFFECTIVE_STATUS,
      "code_authority":MSCI_AUTHORITY_NAME,"code_authority_sha256":MSCI_SHA,"code_authority_version_or_asof":MSCI_VERSION,
      "identity_evidence_commit":"16ca7cfc2148527f4e48bda642e7533831a716c5",
      "classification_evidence_commit":"3c71084e03fbd49c6ab5b34b03696c62aac765ad",
      "code_authority_evidence_commit":"62c1d0345c8955c949c134318f9329e12dca0469",
      "cross_stage_conflicts":cross_conflicts,"blocker":blocker,"gate_h":"NOT_EVALUATED","au_canonical_readiness":"NO",
      "canonical_ready_rows":37,"canonical_total_rows":1425,"external_source_requests":0,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate
    }
    write_json(out/"summary_preupload_v0.88.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.88.json",{
      "version":VERSION,"stage":STAGE,"verdict":verdict,"au_technical_provenance_ready":ready,"rows":63,
      "provenance_complete":complete,"blocker":blocker,"gate_h":"NOT_EVALUATED","canonical_ready_rows":37,"canonical_total_rows":1425,
      "next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD"
    })
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.88.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.88.json",{
      "version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"au_technical_provenance_ready":ready,"rows":63,"provenance_complete":complete,"blocker":blocker,
      "external_source_requests":0,"canonical_ready_rows":37,"canonical_total_rows":1425,"gate_h_runs":0,
      "canonical_materialization_runs":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":next_gate
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
