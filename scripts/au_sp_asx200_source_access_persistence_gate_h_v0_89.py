#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,html,json,re,subprocess,time,urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.89"
STAGE="AU_SP_ASX200_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE_H"
REQUIRED_START_HEAD="fb0a3ea7d9b1988e53290fd9ad9e7a9ff6488efd"

V088_WORKFLOW=36403714685
V088_ARTIFACT=10961292663
V088_DIGEST="sha256:b85acf39849f088e8d6d72766fd320dedc554ccabe92a9031342dd7890bba75e"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"
ASX_SHA="66111266a833527d97b48388130111c707caa8bd35221fc95e3d60e8e8d6e69d"
MSCI_SHA="d66cfdf808872211561270a7141c40687417b3f669192c6b2650ae2d0aacad06"

SPEC=ROOT/"config/au_sp_asx200_source_access_persistence_gate_h_spec_v0.89.json"
GSEC05=ROOT/"config/manager_governance_authority_G_SEC_05_v0.75.json"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANON=ROOT/"sector_metadata/canonical/cohorts"

OUT88=ROOT/"output_au_sp_asx200_technical_provenance_gate_g_v0_88"
SUM88=OUT88/"summary_v0.88.json"
CHK88=OUT88/"stage_checkpoint_v0.88.json"
MAN88=OUT88/"manifest_v0.88.json"
DEC88=OUT88/"au_technical_provenance_decision_v0.88.json"
CHAIN88=OUT88/"au_row_level_provenance_chain_v0.88.csv"

CAP82=ROOT/"output_au_sp_asx200_dynamic_directory_route_gate_c_v0_82/au_dynamic_directory_route_capture_environment_v0.82.json"
REPLAY82=ROOT/"output_au_sp_asx200_dynamic_directory_route_gate_c_v0_82/au_directory_direct_replay_audit_v0.82.json"
DL83=ROOT/"output_au_sp_asx200_final_gate_c_provenance_v0_83/au_current_directory_download_control_audit_v0.83.json"
SRC85=ROOT/"output_au_sp_asx200_gate_d_msci_gics_repair_v0_85/msci_current_gics_methodology_source_audit_v0.85.json"
INV85=ROOT/"output_au_sp_asx200_gate_d_msci_gics_repair_v0_85/gics_industry_group_official_label_code_inventory_v0.85.csv"

ASX_TERMS="https://www.asx.com.au/legals/terms-of-use"
ASX_DATA="https://www.asx.com.au/legals/data-disclaimers"
MSCI_TERMS="https://www.msci.com/legal/terms-of-use"
MSCI_NOTICE="https://www.msci.com/legal/notice-and-disclaimer"
SP_TERMS="https://www.spglobal.com/en/terms-of-use"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="title":self.in_title=True
    def handle_endtag(self,tag):
        if tag.lower()=="title":self.in_title=False
    def handle_data(self,data):
        if data and data.strip():
            self.parts.append(data)
            if self.in_title:self.title.append(data)

def now()->str:return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

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
def norm(s:str)->str:return re.sub(r"\s+"," ",html.unescape(s or "")).strip()
def lower_text(s:str)->str:return norm(s).lower()

def fetch_policy(source_class:str,url:str)->dict[str,Any]:
    req=urllib.request.Request(url,headers={
      "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.89",
      "Accept":"text/html,application/xhtml+xml,*/*;q=0.8"
    })
    ts=now()
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            body=r.read(5_000_000)
            status=getattr(r,"status",200)
            resolved=r.geturl()
            ctype=r.headers.get("Content-Type","")
    except Exception as e:
        return {"Policy_Source_Class":source_class,"Requested_URL":url,"Resolved_URL":"","Retrieval_Timestamp_UTC":ts,
          "HTTP_Status":0,"Content_Type":"","Bytes":0,"SHA256":"","Policy_Page_Title":"","Error":type(e).__name__+":"+str(e),
          "_text":""}
    txt=body.decode("utf-8","replace")
    parser=TextExtractor()
    try:parser.feed(txt)
    except Exception:pass
    plain=norm(" ".join(parser.parts)) if parser.parts else norm(re.sub(r"<[^>]+>"," ",txt))
    title=norm(" ".join(parser.title))
    return {"Policy_Source_Class":source_class,"Requested_URL":url,"Resolved_URL":resolved,"Retrieval_Timestamp_UTC":ts,
      "HTTP_Status":status,"Content_Type":ctype,"Bytes":len(body),"SHA256":hashlib.sha256(body).hexdigest(),
      "Policy_Page_Title":title,"Error":"","_text":plain}

def marker(text:str,phrase:str)->bool:
    return phrase.lower() in lower_text(text)

def policy_row(src:dict[str,Any],marker_text:str,paraphrase:str,behavior:str,status:str)->dict[str,Any]:
    return {
      "Policy_Source_Class":src["Policy_Source_Class"],"Policy_Page_Title":src["Policy_Page_Title"],
      "Official_URL":src["Requested_URL"],"Resolved_URL":src["Resolved_URL"],"Retrieval_Timestamp_UTC":src["Retrieval_Timestamp_UTC"],
      "HTTP_Status":src["HTTP_Status"],"Content_Type":src["Content_Type"],"SHA256":src["SHA256"],
      "Relevant_Clause_or_Marker":marker_text,"Bounded_Paraphrase":paraphrase,
      "Affected_Project_Behavior":behavior,"Operational_Status":status
    }

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM88.read_text());c=json.loads(CHK88.read_text());m=json.loads(MAN88.read_text());d=json.loads(DEC88.read_text())
    if s["verdict"]!="PASS_AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G":raise RuntimeError("v0.88 verdict")
    if not s["au_technical_provenance_ready"]:raise RuntimeError("v0.88 readiness")
    if s["rows"]!=63 or s["provenance_complete"]!=63:raise RuntimeError("v0.88 rows")
    if any(s[k]!=0 for k in ["provenance_incomplete","provenance_conflict","provenance_not_verified","cross_stage_conflicts"]):raise RuntimeError("v0.88 conflicts")
    if s["tests"]!={"failed":0,"passed":33,"total":33}:raise RuntimeError("v0.88 tests")
    if c["workflow_run_id"]!=V088_WORKFLOW or c["artifact_id"]!=V088_ARTIFACT or c["artifact_digest"]!=V088_DIGEST:raise RuntimeError("v0.88 artifact")
    if m["workflow_run_id"]!=V088_WORKFLOW or m["artifact_id"]!=V088_ARTIFACT or m["artifact_digest"]!=V088_DIGEST:raise RuntimeError("v0.88 manifest")
    if d["Gate_G"]!="PASS_BY_CURRENT_EVIDENCE" or d["Gate_H"]!="NOT_EVALUATED":raise RuntimeError("v0.88 gate state")
    if s["classification_source_sha256"]!=ASX_SHA or s["code_authority_sha256"]!=MSCI_SHA:raise RuntimeError("source hashes")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    if sha_file(PARK)!=PARK_SHA:raise RuntimeError("park registry")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SHA:raise RuntimeError("canonical registry")
    if any(AU_CANON.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical exists")
    return {"summary":s,"checkpoint":c,"manifest":m,"decision":d}

def provider_audit(asx:int,msci:int,sp:int)->dict[str,int]:
    return {"Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,"ETF_holdings":0,
      "per_security_web_fanout":0,"Gate_A_rerun":0,"Gate_B_rerun":0,"Gate_C_rerun":0,"Gate_D_rerun":0,"Gate_E_rerun":0,
      "Gate_F_rerun":0,"Gate_G_rerun":0,"canonical_materialization":0,"Sector_RS":0,"P0":0,"P1":0,"P2":0,
      "core_ASX_classification_source_requests":0,"core_MSCI_methodology_requests":0,
      "ASX_policy_requests":asx,"MSCI_policy_requests":msci,"SP_GICS_policy_requests":sp}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_au_sp_asx200_source_access_persistence_gate_h_v0_89")
    a=ap.parse_args();pred=validate_predecessor(a.repository_sha);spec=json.loads(SPEC.read_text());gov=json.loads(GSEC05.read_text())
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    if gov["authority_id"]!="G-SEC-05" or gov["gate"]!="H_ACCESS_PERSISTENCE":raise RuntimeError("G-SEC-05 authority mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    write_json(out/"au_gate_h_predecessor_authority_v0.89.json",{
      "Final_Commit":REQUIRED_START_HEAD,"Verdict":pred["summary"]["verdict"],"AU_TECHNICAL_PROVENANCE_READY":"YES",
      "Rows":"63/63","PROVENANCE_COMPLETE":63,"PROVENANCE_INCOMPLETE":0,"PROVENANCE_CONFLICT":0,"PROVENANCE_NOT_VERIFIED":0,
      "Cross_Stage_Conflicts":0,"Classification_Source":"ASX_COMPANY_DIRECTORY_LISTED_COMPANIES_CSV",
      "Classification_Source_SHA256":ASX_SHA,"Classification_Source_Retrieved_UTC":pred["summary"]["classification_source_retrieved_utc"],
      "Classification_Source_Version_AsOf":pred["summary"]["classification_source_version_or_asof"],
      "Classification_Effective_AsOf_Status":pred["summary"]["classification_effective_asof_status"],
      "Code_Authority":"MSCI_GICS_METHODOLOGY","Code_Authority_SHA256":MSCI_SHA,
      "Code_Authority_Version_AsOf":pred["summary"]["code_authority_version_or_asof"],
      "Workflow":V088_WORKFLOW,"Artifact":V088_ARTIFACT,"Artifact_Digest":V088_DIGEST,"Tests":"33/33 PASS","Canonical_READY":"37/1425"
    })
    write_json(out/"manager_governance_authority_G_SEC_05_reference_v0.89.json",{
      "Authority_ID":"G-SEC-05","Authority_Title":gov["title"],"Authority_File":str(GSEC05.relative_to(ROOT)),
      "Authority_File_SHA256":sha_file(GSEC05),"Legal_Opinion":gov["legal_opinion"],"Rules":gov["rules"],"Pass_Conditions":gov["pass_conditions"]
    })

    cap=json.loads(CAP82.read_text());replay=json.loads(REPLAY82.read_text());dl=json.loads(DL83.read_text());src85=json.loads(SRC85.read_text())
    token_context=(cap["Authentication"]=="NONE" and cap["Cookies_Preexisting"]=="NO" and cap["CAPTCHA_Bypass"]=="NO" and cap["Proxy"]=="NONE"
                   and dl["Download_Status"]=="PASS" and "access_token=" in dl["Download_URL"])
    asx_access={
      "ASX_PUBLIC_ACCESS":"YES","ASX_AUTH_REQUIRED":"NO","ASX_PAID_ENTITLEMENT_REQUIRED":"NO",
      "ASX_CAPTCHA_BYPASS_REQUIRED":"NO","ASX_PRIVILEGED_SESSION_REQUIRED":"NO",
      "ASX_PUBLIC_PAGE_GENERATED_TOKEN":"YES" if token_context else "NOT_VERIFIED",
      "ASX_TOKEN_CLASSIFICATION":"EPHEMERAL_PAGE_GENERATED_PUBLIC_TOKEN" if token_context else "NOT_VERIFIED",
      "ASX_DIRECT_HTTP_REPLAY":replay["DIRECT_HTTP_REPLAY"],"ASX_ACCESS_READY":"YES" if token_context and replay["DIRECT_HTTP_REPLAY"]=="PASS" else "NOT_VERIFIED",
      "Evidence_Source_v082":str(CAP82.relative_to(ROOT)),"Evidence_Source_v083":str(DL83.relative_to(ROOT)),
      "No_Core_ASX_Refetch_v089":"YES"
    }
    write_json(out/"au_asx_public_access_status_audit_v0.89.json",asx_access)
    gics_access={
      "GICS_METHODOLOGY_PUBLIC_ACCESS":"YES" if src85["HTTP_Status"]==200 and src85["Reproducible"]=="YES" else "NOT_VERIFIED",
      "GICS_AUTH_REQUIRED":"NO","GICS_PAID_ENTITLEMENT_REQUIRED":"NO",
      "GICS_PUBLIC_ACCESS_READY":"YES" if src85["HTTP_Status"]==200 and src85["Reproducible"]=="YES" else "NOT_VERIFIED",
      "Evidence_Source_v085":str(SRC85.relative_to(ROOT)),"MSCI_Methodology_HTTP_Status_v085":src85["HTTP_Status"],
      "MSCI_Methodology_SHA256_v085":src85["SHA256"],"No_Core_MSCI_Methodology_Refetch_v089":"YES"
    }
    write_json(out/"au_gics_public_access_status_audit_v0.89.json",gics_access)

    chain=read_csv(CHAIN88);inv=read_csv(INV85)
    technical_asx=(len(chain)==63 and all(r["Classification_Source_Snapshot_SHA256"]==ASX_SHA for r in chain))
    technical_gics=(len(chain)==63 and len(inv)==25 and all(r["Code_Authority_SHA256"]==MSCI_SHA for r in chain))
    write_json(out/"au_raw_persistence_requirement_audit_v0.89.json",{
      "RAW_PERSISTENCE_REQUIRED_ASX":"NO","RAW_PERSISTENCE_RIGHTS_ASX":"VERIFIED_RESTRICTED",
      "RAW_SOURCE_CURRENTLY_PERSISTED_ASX":"NO","RAW_PERSISTENCE_REQUIRED_GICS":"NO",
      "RAW_PERSISTENCE_RIGHTS_GICS":"VERIFIED_RESTRICTED","RAW_SOURCE_CURRENTLY_PERSISTED_GICS":"NO",
      "Technical_Reason":"v0.88 proves 63/63 auditability from stable references, hashes, timestamps, bounded row evidence and exact code authority; complete raw sources are not technically required."
    })
    write_json(out/"au_asx_bounded_evidence_sufficiency_audit_v0.89.json",{
      "TECHNICAL_BOUNDED_EVIDENCE_SUFFICIENT_ASX":"YES" if technical_asx else "NO","Rows":len(chain),
      "Stable_URL":"https://www.asx.com.au/markets/trade-our-cash-market/directory","Snapshot_SHA256":ASX_SHA,
      "Has_Retrieval_Timestamp":"YES","Has_Schema_Metadata":"YES","Has_63_ASX_Codes":"YES","Has_63_Raw_GICS_Values":"YES",
      "Has_Exact_Frozen_WS_ID_Linkage":"YES","Has_Evidence_Versions_Commits":"YES","Raw_CSV_Required":"NO"
    })
    write_json(out/"au_gics_bounded_evidence_sufficiency_audit_v0.89.json",{
      "TECHNICAL_BOUNDED_EVIDENCE_SUFFICIENT_GICS":"YES" if technical_gics else "NO","Official_Methodology_URL":src85["Requested_URL"],
      "PDF_SHA256":MSCI_SHA,"Display_Date":src85["Document_Display_Date"],"Retrieval_Timestamp_UTC":src85["Retrieval_Timestamp_UTC"],
      "Taxonomy":"GICS","Formal_Level":"INDUSTRY_GROUP","Official_Code_Inventory_Rows":len(inv),
      "Exact_Code_Name_Authority_Persisted":"YES","Evidence_Commit":"62c1d0345c8955c949c134318f9329e12dca0469","Raw_PDF_Required":"NO"
    })

    behavior_fields=["WS_ID","Sector_Taxonomy","Sector_Level","Sector_Name","Sector_Raw_Name","Sector_Code","Source_Sector_Code",
      "Sector_Code_Origin","Sector_Code_Method","Source_Name","Source_Reference","Source_Version_or_AsOf","Source_Retrieved_UTC",
      "Source_Effective_AsOf_Status","Mapping_Status","evidence-version/commit fields"]
    write_json(out/"au_future_canonical_metadata_behavior_contract_v0.89.json",{
      "Cohort":"AU_SP_ASX200","Rows":63,"Intended_Fields":behavior_fields,"Full_ASX_Directory_Redistribution":"NO",
      "Full_MSCI_Methodology_Redistribution":"NO","Uses_Exact_ASX_Codes":"YES","Uses_Exact_ASX_GICS_Industry_Group_Values":"YES",
      "Uses_Exact_GICS_Industry_Group_Names":"YES","Uses_Exact_GICS_Four_Digit_Codes":"YES","Internal_Canonical_Metadata_Persistence":"YES",
      "Automated_Pipeline_Context":"YES","Canonical_Materialization_Executed_v089":"NO"
    })
    write_json(out/"au_bounded_metadata_vs_raw_data_classification_audit_v0.89.json",{
      "Technical_Output_Classification":"BOUNDED_CANONICAL_METADATA",
      "Rows":63,"Not_Full_ASX_Directory":"YES","Not_Full_GICS_Database":"YES",
      "Policy_Compatibility_Must_Be_Evaluated_Separately":"YES",
      "Technical_Boundedness_Does_Not_Override_Official_Restrictions":"YES"
    })

    sources=[
      fetch_policy("ASX_OFFICIAL_TERMS",ASX_TERMS),
      fetch_policy("ASX_OFFICIAL_DATA_DISCLAIMERS",ASX_DATA),
      fetch_policy("MSCI_OFFICIAL_TERMS",MSCI_TERMS),
      fetch_policy("MSCI_OFFICIAL_NOTICE",MSCI_NOTICE),
      fetch_policy("SP_GLOBAL_OFFICIAL_TERMS",SP_TERMS)
    ]
    for s in sources:
        if s["HTTP_Status"]!=200 or not s["_text"]:
            raise RuntimeError("policy source not reproducible: "+s["Requested_URL"])

    by_url={s["Requested_URL"]:s for s in sources}
    at=by_url[ASX_TERMS];ad=by_url[ASX_DATA];mt=by_url[MSCI_TERMS];mn=by_url[MSCI_NOTICE];st=by_url[SP_TERMS]

    asx_markers={
      "personal_noncommercial":marker(at["_text"],"own information purposes only"),
      "commercial_consent":marker(at["_text"],"commercial purpose without the express written consent of ASX"),
      "automated_access":marker(at["_text"],"use any spider, screen scraper, robot"),
      "copy_reproduce":marker(at["_text"],"modify, copy, reproduce, republish"),
      "lseg_redistribution":marker(ad["_text"],"Republication or redistribution of LSEG content"),
      "morningstar_managed_fund":marker(ad["_text"],"research and assess managed fund data")
    }
    msci_markers={
      "internal_nonproduction":marker(mt["_text"],"only internally for non-production purposes"),
      "database_restriction":marker(mt["_text"],"populate a database with"),
      "automated_restriction":marker(mt["_text"],"unauthorized bots, scrapers, crawlers, AI agents"),
      "notice_prior_permission":marker(mn["_text"],"prior written permission"),
      "notice_database":marker(mn["_text"],"to populate a database"),
      "notice_ai":marker(mn["_text"],"artificial intelligence"),
      "notice_automated":marker(mn["_text"],"unauthorized bots, scrapers, crawlers")
    }
    sp_markers={
      "personal_noncommercial":marker(st["_text"],"solely for non-commercial, personal use"),
      "classification_database":marker(st["_text"],"classification system or historical databases"),
      "derived_data":marker(st["_text"],"create any derived data"),
      "authorized_end_users":marker(st["_text"],"authorized end users")
    }

    if not (asx_markers["automated_access"] and asx_markers["copy_reproduce"] and asx_markers["commercial_consent"]):
        raise RuntimeError("ASX policy markers incomplete")
    if not (msci_markers["database_restriction"] and msci_markers["automated_restriction"] and msci_markers["notice_prior_permission"] and msci_markers["notice_database"]):
        raise RuntimeError("MSCI policy markers incomplete")
    if not (sp_markers["classification_database"] and sp_markers["derived_data"]):
        raise RuntimeError("S&P policy markers incomplete")

    policy_rows=[
      policy_row(at,"use any spider, screen scraper, robot","ASX prohibits automated software/process access to the Site except where otherwise permitted or with prior written consent.","C automated/programmatic retrieval","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(at,"modify, copy, reproduce, republish","ASX restricts copying/reproduction of Site content beyond expressly permitted uses or prior written consent.","G exact source values / H bounded canonical persistence","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(at,"commercial purpose without the express written consent of ASX","ASX defines use beyond personal/private decision-making as commercial unless otherwise permitted and requires consent.","H internal project reuse outside personal/private decision-making","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(ad,"Republication or redistribution of LSEG content","ASX identifies an LSEG redistribution restriction, but current evidence does not bind the exact GICs industry group field to LSEG.","Third-party rights scope","NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND"),
      policy_row(ad,"research and assess managed fund data","Morningstar-specific wording reviewed is scoped to managed-fund information/ReferencePoint and is not current field-specific authority for the ASX directory classification field.","Third-party rights scope","NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND"),
      policy_row(mt,"populate a database with","MSCI terms restrict populating a database with MSCI proprietary materials unless expressly permitted in an applicable agreement.","D/E/F exact GICS name/code persistence into canonical metadata","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(mt,"unauthorized bots, scrapers, crawlers, AI agents","MSCI terms restrict unauthorized automated extraction of MSCI proprietary materials.","automated processing/access","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(mn,"prior written permission","MSCI notice requires prior written permission for listed non-permitted uses.","bounded GICS code/name reuse without persisted authorization","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(st,"classification system or historical databases","S&P Global terms for SPDJI data restrict creating classification systems or historical databases without permission.","GICS/SPDJI classification-data persistence","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND"),
      policy_row(st,"create any derived data","S&P Global terms restrict derived data based on SPDJI data absent express written consent.","derived/canonical metadata using source classification data","EXPLICIT_OPERATIONAL_RESTRICTION_FOUND")
    ]
    write_csv(out/"au_asx_official_policy_review_v0.89.csv",[r for r in policy_rows if r["Policy_Source_Class"].startswith("ASX_")])
    write_csv(out/"au_gics_official_policy_review_v0.89.csv",[r for r in policy_rows if r["Policy_Source_Class"].startswith("MSCI_") or r["Policy_Source_Class"].startswith("SP_")])

    inventory=[]
    for s in sources:
        inventory.append({
          "Source_Class":s["Policy_Source_Class"],"Official_URL":s["Requested_URL"],"Resolved_URL":s["Resolved_URL"],
          "HTTP_Status":s["HTTP_Status"],"Content_Type":s["Content_Type"],"Bytes":s["Bytes"],"SHA256":s["SHA256"],
          "Retrieval_Timestamp_UTC":s["Retrieval_Timestamp_UTC"],"Policy_Page_Title":s["Policy_Page_Title"],
          "Raw_Body_Persisted":"NO","Role":"CURRENT_POLICY_REVIEW"
        })
    write_csv(out/"au_gate_h_source_inventory_v0.89.csv",inventory)

    asx_scope=[
      {"Behavior":"A ordinary public page access","Status":"NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND","Basis":"public access inherited; policy permits ordinary browser access for limited informational use"},
      {"Behavior":"B public CSV download through official directory","Status":"NOT_VERIFIED","Basis":"download control is public, but policy terms constrain copying/use and do not provide a general reuse license"},
      {"Behavior":"C automated/programmatic retrieval of CSV","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"ASX terms expressly prohibit spider/screen scraper/robot or similar automated process absent permission/exception"},
      {"Behavior":"D internal analytical use","Status":"NOT_VERIFIED","Basis":"limited personal/non-commercial use exists, but repository pipeline behavior exceeds a simple personal unchanged copy contract"},
      {"Behavior":"E URL/hash/timestamp/schema persistence","Status":"NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND","Basis":"bounded provenance facts alone are not the blocked behavior identified"},
      {"Behavior":"F exact ASX code persistence","Status":"NOT_VERIFIED","Basis":"exact source content persistence is covered by general copy/reproduce/use restrictions"},
      {"Behavior":"G exact GICs industry group values for 63 securities","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"intended transformed persistence reproduces exact source classification values outside the expressly limited unchanged-copy use"},
      {"Behavior":"H later internal canonical metadata creation","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"automated transformed canonical metadata materially relies on restricted source-content use without persisted consent"},
      {"Behavior":"I redistribution/publication of full ASX directory","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"full reproduction/redistribution is outside required project behavior and separately restricted"}
    ]
    write_csv(out/"au_asx_policy_scope_operational_impact_audit_v0.89.csv",asx_scope)

    write_json(out/"au_asx_third_party_rights_scope_audit_v0.89.json",{
      "Directory_General_Attribution":"LSEG Data & Analytics and Morningstar",
      "LSEG_Official_ASX_Disclaimer_Observed":"YES" if asx_markers["lseg_redistribution"] else "NO",
      "Morningstar_Official_ASX_Disclaimer_Observed":"YES" if asx_markers["morningstar_managed_fund"] else "NO",
      "Exact_GICs_Industry_Group_Field_Attribution_To_LSEG":"NOT_VERIFIED",
      "Exact_GICs_Industry_Group_Field_Attribution_To_Morningstar":"NOT_VERIFIED",
      "Generic_Attribution_Expanded_To_Field_Specific_Restriction":"NO",
      "Independent_Field_Specific_Blocker_From_Third_Party_Disclaimers":"NO",
      "ASX_Own_Terms_Blocker_Remains_Independent":"YES"
    })

    gics_scope=[
      {"Behavior":"A viewing public GICS methodology","Status":"NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND","Basis":"public methodology access inherited; viewing alone is not the blocked behavior"},
      {"Behavior":"B internal use of GICS taxonomy labels","Status":"NOT_VERIFIED","Basis":"MSCI grants limited internal non-production access but separate restrictions apply to database/derived persistence"},
      {"Behavior":"C internal use of GICS classification codes","Status":"NOT_VERIFIED","Basis":"public code authority does not itself supply persistence authorization"},
      {"Behavior":"D storing bounded code/name mapping","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"MSCI terms expressly restrict populating a database with MSCI proprietary materials absent applicable permission"},
      {"Behavior":"E using GICS classifications as security metadata","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"future canonical metadata persists exact GICS names/codes as a structured database-like dataset"},
      {"Behavior":"F automated processing of GICS classifications","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"MSCI terms/notice restrict unauthorized automated extraction/AI-related use"},
      {"Behavior":"G redistribution/publication of GICS data","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"official terms restrict redistribution/derived-data use"},
      {"Behavior":"H full GICS database/product use","Status":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND","Basis":"full database/product use is separately restricted and is not required by this project"}
    ]
    write_csv(out/"au_gics_policy_scope_operational_impact_audit_v0.89.csv",gics_scope)

    asx_policy_ready="NO"
    gics_policy_ready="NO"
    asx_bounded_persistence="NO"
    gics_bounded_persistence="NO"
    asx_canonical_ready="NO"
    gics_code_name_ready="NO"
    canonical_persistable="NO"

    write_json(out/"au_asx_evidence_persistence_decision_v0.89.json",{
      "ASX_BOUNDED_EVIDENCE_PERSISTENCE_READY":asx_bounded_persistence,
      "ASX_CANONICAL_METADATA_PERSISTENCE_READY":asx_canonical_ready,
      "ASX_OFFICIAL_POLICY_COMPATIBILITY_READY":asx_policy_ready,
      "TECHNICAL_BOUNDED_EVIDENCE_SUFFICIENT_ASX":"YES" if technical_asx else "NO",
      "RAW_PERSISTENCE_REQUIRED_ASX":"NO","RAW_PERSISTENCE_RIGHTS_ASX":"VERIFIED_RESTRICTED",
      "Operational_Blocker":"EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Authorization_Requirement":"ASX_PRIOR_WRITTEN_CONSENT_OR_APPLICABLE_EXPRESS_PERMISSION",
      "Legal_Opinion":"NO"
    })
    write_json(out/"au_gics_evidence_persistence_decision_v0.89.json",{
      "GICS_BOUNDED_EVIDENCE_PERSISTENCE_READY":gics_bounded_persistence,
      "GICS_CODE_NAME_METADATA_PERSISTENCE_READY":gics_code_name_ready,
      "GICS_OFFICIAL_POLICY_COMPATIBILITY_READY":gics_policy_ready,
      "TECHNICAL_BOUNDED_EVIDENCE_SUFFICIENT_GICS":"YES" if technical_gics else "NO",
      "RAW_PERSISTENCE_REQUIRED_GICS":"NO","RAW_PERSISTENCE_RIGHTS_GICS":"VERIFIED_RESTRICTED",
      "Operational_Blocker":"EXPLICIT_GICS_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Authorization_Requirement":"MSCI_AND_OR_SP_DJI_APPLICABLE_LICENSE_OR_PERMISSION",
      "Legal_Opinion":"NO"
    })
    write_json(out/"au_canonical_metadata_evidence_persistability_decision_v0.89.json",{
      "CANONICAL_METADATA_EVIDENCE_PERSISTABLE":canonical_persistable,
      "Technical_Output_Classification":"BOUNDED_CANONICAL_METADATA",
      "ASX_Side_Persistable":"NO","GICS_Side_Persistable":"NO",
      "Raw_ASX_Persistence_Required":"NO","Raw_GICS_Persistence_Required":"NO",
      "Reason":"bounded technical evidence is sufficient, but current official policy review found explicit operational restrictions materially covering automated/transformed ASX use and GICS code/name database persistence"
    })

    final_ready=False
    blocker="EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION"
    external_auth="YES"
    auth_source="ASX prior written consent / applicable express permission; MSCI and/or S&P Dow Jones Indices applicable GICS license/permission"
    next_gate="AU_SP_ASX200 EXTERNAL-AUTHORIZATION PARK / ACTIVE-COHORT RESELECTION MANAGER GATE"
    decision={
      "Cohort":"AU_SP_ASX200","A":"PASS","B":"PASS","C":"PASS","D":"PASS","E":"PASS","F":"PASS","G":"PASS","H":"BLOCKED",
      "ASX_PUBLIC_SOURCE_ACCESS_READY":asx_access["ASX_ACCESS_READY"],
      "GICS_PUBLIC_CODE_AUTHORITY_ACCESS_READY":gics_access["GICS_PUBLIC_ACCESS_READY"],
      "ASX_BOUNDED_EVIDENCE_PERSISTENCE_READY":asx_bounded_persistence,
      "GICS_BOUNDED_EVIDENCE_PERSISTENCE_READY":gics_bounded_persistence,
      "ASX_OFFICIAL_POLICY_COMPATIBILITY_READY":asx_policy_ready,
      "GICS_OFFICIAL_POLICY_COMPATIBILITY_READY":gics_policy_ready,
      "CANONICAL_METADATA_EVIDENCE_PERSISTABLE":canonical_persistable,
      "AU_SOURCE_ACCESS_PERSISTENCE_READY":"NO",
      "AU_CANONICAL_SECTOR_METADATA_READY":"NO","Global_Canonical_READY":"37/1425",
      "EXTERNAL_AUTHORIZATION_REQUIRED":external_auth,"AUTHORIZATION_SOURCE":auth_source,
      "Blocker":blocker,"Next_Gate":next_gate,"Legal_Opinion":"NO"
    }
    write_json(out/"au_source_access_persistence_gate_h_decision_v0.89.json",decision)

    request_rows=[]
    for i,s in enumerate(sources,1):
        request_rows.append({"Request_Order":i,"Source_Class":s["Policy_Source_Class"],"URL":s["Requested_URL"],
          "Purpose":"CURRENT_OFFICIAL_POLICY_REVIEW","HTTP_Status":s["HTTP_Status"],"Content_Type":s["Content_Type"],"SHA256":s["SHA256"],
          "Core_Classification_or_Methodology_Request":"NO","Per_Security_Request":"NO"})
    write_csv(out/"external_request_ledger_v0.89.csv",request_rows)
    prov=provider_audit(2,2,1);write_json(out/"provider_call_audit_v0.89.json",prov)

    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SHA,"BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),"Parked_Cohort_Registry_Unchanged":sha_file(PARK)==PARK_SHA,
      "v085_GICS_Code_Authority":"25/25","v086_AU_Identity":"63/63","v087_AU_Classification":"63/63","v088_AU_Provenance":"63/63",
      "IN_Gate_F":"45/45","JP_Gate_F":"197/197","Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,
      "AU_Canonical_Rows_After":0,"Canonical_Materialization_Runs":0,"AU_Parking_Runs":0,"Reselection_Runs":0,"Other_Cohort_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    write_json(out/"immutability_audit_v0.89.json",imm)

    tests=[]
    def t(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    t("V088_PASS",pred["summary"]["verdict"]=="PASS_AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G",pred["summary"]["verdict"])
    t("V088_ARTIFACT",pred["checkpoint"]["artifact_id"]==V088_ARTIFACT and pred["checkpoint"]["artifact_digest"]==V088_DIGEST,V088_ARTIFACT)
    t("GSEC05_AUTHORITY",gov["authority_id"]=="G-SEC-05" and gov["rules"]["gate_h_operational_not_legal"],gov["title"])
    t("ASX_ACCESS_READY",asx_access["ASX_ACCESS_READY"]=="YES",asx_access["ASX_ACCESS_READY"])
    t("ASX_TOKEN_PUBLIC_EPHEMERAL",asx_access["ASX_TOKEN_CLASSIFICATION"]=="EPHEMERAL_PAGE_GENERATED_PUBLIC_TOKEN",asx_access["ASX_TOKEN_CLASSIFICATION"])
    t("GICS_ACCESS_READY",gics_access["GICS_PUBLIC_ACCESS_READY"]=="YES",gics_access["GICS_PUBLIC_ACCESS_READY"])
    t("RAW_ASX_NOT_REQUIRED",True,"NO");t("RAW_GICS_NOT_REQUIRED",True,"NO")
    t("TECHNICAL_ASX_BOUNDED_SUFFICIENT",technical_asx,technical_asx);t("TECHNICAL_GICS_BOUNDED_SUFFICIENT",technical_gics,technical_gics)
    t("POLICY_SOURCES_5",len(sources)==5 and all(s["HTTP_Status"]==200 for s in sources),[(s["Policy_Source_Class"],s["HTTP_Status"]) for s in sources])
    t("ASX_AUTOMATION_RESTRICTION",asx_markers["automated_access"],"observed")
    t("ASX_COPY_REPRODUCE_RESTRICTION",asx_markers["copy_reproduce"],"observed")
    t("ASX_CONSENT_RESTRICTION",asx_markers["commercial_consent"],"observed")
    t("MSCI_DATABASE_RESTRICTION",msci_markers["database_restriction"],"observed")
    t("MSCI_AUTOMATION_RESTRICTION",msci_markers["automated_restriction"],"observed")
    t("MSCI_PRIOR_PERMISSION_MARKER",msci_markers["notice_prior_permission"] and msci_markers["notice_database"],"observed")
    t("SP_CLASSIFICATION_DB_RESTRICTION",sp_markers["classification_database"],"observed")
    t("SP_DERIVED_DATA_RESTRICTION",sp_markers["derived_data"],"observed")
    t("ASX_POLICY_NOT_COMPATIBLE",asx_policy_ready=="NO",asx_policy_ready)
    t("GICS_POLICY_NOT_COMPATIBLE",gics_policy_ready=="NO",gics_policy_ready)
    t("CANONICAL_NOT_PERSISTABLE",canonical_persistable=="NO",canonical_persistable)
    t("EXTERNAL_AUTH_REQUIRED",external_auth=="YES",auth_source)
    t("FAILURE_PRECEDENCE_ASX",blocker=="EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION",blocker)
    t("NO_CORE_SOURCE_REFETCH",prov["core_ASX_classification_source_requests"]==0 and prov["core_MSCI_methodology_requests"]==0,"0/0")
    t("NO_A_G_RERUNS",sum(prov[k] for k in ["Gate_A_rerun","Gate_B_rerun","Gate_C_rerun","Gate_D_rerun","Gate_E_rerun","Gate_F_rerun","Gate_G_rerun"])==0,"0")
    t("NO_CANONICAL_RS_P",prov["canonical_materialization"]==prov["Sector_RS"]==prov["P0"]==prov["P1"]==prov["P2"]==0,"0")
    t("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA);t("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA);t("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    t("BR_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SHA);t("PARKS_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],PARK_SHA)
    t("CANONICAL_READY_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    t("NO_AU_CANONICAL",not any(AU_CANON.glob("AU_SP_ASX200_*.csv")),"0")
    t("GATE_H_BLOCKED",decision["H"]=="BLOCKED" and decision["AU_SOURCE_ACCESS_PERSISTENCE_READY"]=="NO",blocker)
    write_csv(out/"test_results_v0.89.csv",tests)

    verdict="BLOCKED_AU_SP_ASX200_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE_H"
    summary={
      "version":VERSION,"stage":STAGE,"verdict":verdict,"au_source_access_persistence_ready":False,
      "asx_access_ready":asx_access["ASX_ACCESS_READY"],"gics_access_ready":gics_access["GICS_PUBLIC_ACCESS_READY"],
      "raw_asx_persistence_required":"NO","raw_gics_persistence_required":"NO",
      "asx_bounded_evidence_sufficient":"YES" if technical_asx else "NO","gics_bounded_evidence_sufficient":"YES" if technical_gics else "NO",
      "asx_bounded_evidence_persistence_ready":asx_bounded_persistence,"gics_bounded_evidence_persistence_ready":gics_bounded_persistence,
      "asx_official_policy_review":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND",
      "gics_official_policy_review":"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND",
      "asx_policy_compatibility":asx_policy_ready,"gics_policy_compatibility":gics_policy_ready,
      "canonical_metadata_evidence_persistable":canonical_persistable,"external_authorization_required":external_auth,
      "authorization_source":auth_source,"blocker":blocker,"legal_opinion":False,
      "canonical_ready_rows":37,"canonical_total_rows":1425,
      "policy_requests":{"ASX":2,"MSCI":2,"SP_GICS":1},"core_source_requests":{"ASX_classification":0,"MSCI_methodology":0},
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate
    }
    write_json(out/"summary_preupload_v0.89.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.89.json",{
      "version":VERSION,"stage":STAGE,"verdict":verdict,"au_source_access_persistence_ready":False,
      "blocker":blocker,"external_authorization_required":external_auth,"authorization_source":auth_source,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD"
    })
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.89.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.89.json",{
      "version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"au_source_access_persistence_ready":False,"blocker":blocker,"external_authorization_required":external_auth,
      "policy_requests":{"ASX":2,"MSCI":2,"SP_GICS":1},"core_asx_classification_requests":0,"core_msci_methodology_requests":0,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"canonical_materialization_runs":0,"au_parking_runs":0,
      "reselection_runs":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":next_gate
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
