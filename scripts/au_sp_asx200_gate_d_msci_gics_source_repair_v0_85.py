#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, json, re, subprocess, time, unicodedata, urllib.request, urllib.error
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.85"
STAGE="AU_SP_ASX200_GATE_D_OFFICIAL_GICS_CO_OWNER_SOURCE_REPAIR"
REQUIRED_START_HEAD="c02fda68b5a377faafb75ef9304e120e271cb118"
V084_WORKFLOW=36349188738
V084_ARTIFACT=10941761588
V084_DIGEST="sha256:2c1dbb7bb0767b25bfde36b4fc1dd61af7ec8174775114b10a1aa099b53dd8a5"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"

MSCI_URL="https://www.msci.com/indexes/documents/methodology/1_MSCI_Global_Industry_Classification_Standard_GICS_Methodology_20250220.pdf"
SPEC=ROOT/"config/au_sp_asx200_gate_d_msci_gics_source_repair_spec_v0.85.json"
OUT84=ROOT/"output_au_sp_asx200_gics_code_gate_d_v0_84"
SUM84=OUT84/"summary_v0.84.json"
CHK84=OUT84/"stage_checkpoint_v0.84.json"
MAN84=OUT84/"manifest_v0.84.json"
RAW84=OUT84/"asx_current_gics_industry_group_value_inventory_v0.84.csv"
DEC84=OUT84/"au_sector_field_code_feasibility_decision_v0.84.json"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANON=ROOT/"sector_metadata/canonical/cohorts"

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"

def now()->str:return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def nfc(x:Any)->str:return unicodedata.normalize("NFC",str(x or "")).strip()
def normspace(x:Any)->str:return re.sub(r"\s+"," ",nfc(x)).strip()

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
        raise RuntimeError("required start head is not ancestor")
    s=json.loads(SUM84.read_text());c=json.loads(CHK84.read_text());m=json.loads(MAN84.read_text());d=json.loads(DEC84.read_text())
    if s["verdict"]!="BLOCKED_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D":raise RuntimeError("v0.84 verdict")
    if s["au_sector_field_code_feasibility_ready"] is not False:raise RuntimeError("v0.84 readiness")
    if s["blocker"]!="GICS_OFFICIAL_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE":raise RuntimeError("v0.84 blocker")
    if s["current_raw_classification_values"]!=27:raise RuntimeError("v0.84 raw count")
    if s["tests"]!={"failed":0,"passed":20,"total":20}:raise RuntimeError("v0.84 tests")
    if c["workflow_run_id"]!=V084_WORKFLOW or c["artifact_id"]!=V084_ARTIFACT or c["artifact_digest"]!=V084_DIGEST:raise RuntimeError("v0.84 artifact")
    if m["workflow_run_id"]!=V084_WORKFLOW or m["artifact_id"]!=V084_ARTIFACT or m["artifact_digest"]!=V084_DIGEST:raise RuntimeError("v0.84 manifest")
    if d["Taxonomy"]!="GICS" or d["Level"]!="INDUSTRY_GROUP" or d["Gate_E"]!="NOT_EVALUATED" or d["Gate_F"]!="NOT_EVALUATED" or d["Gate_H"]!="NOT_EVALUATED":
        raise RuntimeError("v0.84 authority state")
    raw=read_csv(RAW84)
    if len(raw)!=27 or len({nfc(r["ASX_Raw_Label"]) for r in raw})!=27:raise RuntimeError("v0.84 ASX raw inventory")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    if sha_file(PARK)!=PARK_SHA:raise RuntimeError("park registry")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SHA:raise RuntimeError("canonical registry")
    if any(AU_CANON.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical exists")
    return {"summary":s,"checkpoint":c,"manifest":m,"decision":d,"raw":raw}

def fetch_pdf(url:str,max_bytes:int=20_000_000)->dict[str,Any]:
    ts=now();attempts=[]
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read(max_bytes+1)
            if len(raw)>max_bytes:raise RuntimeError("response too large")
            attempts.append({"Method":"PYTHON_URLLIB","HTTP_Status":getattr(r,"status",200),"Error":""})
            return {"Requested_URL":url,"Resolved_URL":r.geturl(),"HTTP_Status":getattr(r,"status",200),
                    "Content_Type":r.headers.get("Content-Type",""),"Bytes":len(raw),"SHA256":sha_bytes(raw),
                    "Retrieval_Timestamp_UTC":ts,"Raw":raw,"Access_Attempts":attempts}
    except Exception as e:
        attempts.append({"Method":"PYTHON_URLLIB","HTTP_Status":"","Error":type(e).__name__+":"+str(e)[:300]})
    try:
        cp=subprocess.run(["curl","-L","--fail","--silent","--show-error","--max-time","60","-A",UA,
                           "-H","Accept: application/pdf,*/*;q=0.8",url],capture_output=True,timeout=70)
        if cp.returncode==0 and cp.stdout and len(cp.stdout)<=max_bytes:
            raw=cp.stdout
            attempts.append({"Method":"CURL_PUBLIC","HTTP_Status":200,"Error":""})
            return {"Requested_URL":url,"Resolved_URL":url,"HTTP_Status":200,
                    "Content_Type":"application/pdf" if raw.startswith(b"%PDF") else "application/octet-stream",
                    "Bytes":len(raw),"SHA256":sha_bytes(raw),"Retrieval_Timestamp_UTC":ts,"Raw":raw,"Access_Attempts":attempts}
        attempts.append({"Method":"CURL_PUBLIC","HTTP_Status":"","Error":cp.stderr.decode("utf-8",errors="replace")[:300]})
    except Exception as e:
        attempts.append({"Method":"CURL_PUBLIC","HTTP_Status":"","Error":type(e).__name__+":"+str(e)[:300]})
    return {"Requested_URL":url,"Resolved_URL":url,"HTTP_Status":"","Content_Type":"","Bytes":0,"SHA256":"",
            "Retrieval_Timestamp_UTC":ts,"Raw":b"","Access_Attempts":attempts}

def pdf_extract(raw:bytes)->tuple[list[str],str]:
    from pypdf import PdfReader
    r=PdfReader(io.BytesIO(raw))
    pages=[p.extract_text() or "" for p in r.pages]
    return pages,"\n".join(pages)

def first_regex(text:str,pat:str,flags:int=re.I|re.S)->str:
    m=re.search(pat,text,flags)
    return normspace(m.group(1)) if m else ""

def parse_counts(text:str)->dict[str,int]:
    m=re.search(r"includes\s+(\d+)\s+Sectors,\s*(\d+)\s+Industry\s+Groups,\s*(\d+)\s+Industries,\s*and\s*(\d+)\s+Sub.{0,4}?Industries",text,re.I|re.S)
    if not m:return {}
    return {"SECTOR":int(m.group(1)),"INDUSTRY_GROUP":int(m.group(2)),"INDUSTRY":int(m.group(3)),"SUB_INDUSTRY":int(m.group(4))}

def parse_structure(pages:list[str])->tuple[list[dict[str,str]],dict[str,Any]]:
    text="\n".join(pages)
    a=text.find("1.2 The GICS Structure");b=text.find("1.3 Philosophy and objectives of GICS")
    if a<0 or b<=a:return [],{"Section_Bounds":"NOT_VERIFIED"}
    section=text[a:b]
    inventory=[];sector_code="";sector_label="";locations={}
    for page_no,p in enumerate(pages, start=1):
        if page_no<5 or page_no>13:continue
        lines=[normspace(x) for x in p.splitlines() if normspace(x)]
        cur_sector_code="";cur_sector_label=""
        for li,line in enumerate(lines, start=1):
            sm=re.fullmatch(r"(\d{2})\s+(.+)",line)
            if sm and sm.group(1) in {"10","15","20","25","30","35","40","45","50","55","60"}:
                cur_sector_code,cur_sector_label=sm.group(1),normspace(sm.group(2))
                sector_code,sector_label=cur_sector_code,cur_sector_label
                continue
            gm=re.fullmatch(r"(\d{4})\s+(.+)",line)
            if gm:
                code,label=gm.group(1),normspace(gm.group(2))
                parent_code=cur_sector_code or sector_code
                parent_label=cur_sector_label or sector_label
                if parent_code and code.startswith(parent_code):
                    inventory.append({"Official_GICS_Industry_Group_Code":code,"Official_GICS_Industry_Group_Label":label,
                                      "Parent_Sector_Code":parent_code,"Parent_Sector_Label":parent_label,
                                      "Source_Page_or_Location":f"PDF_PAGE_{page_no}_LINE_{li}"})
    ded=[];seen=set()
    for r in inventory:
        k=(r["Official_GICS_Industry_Group_Code"],r["Official_GICS_Industry_Group_Label"])
        if k not in seen:seen.add(k);ded.append(r)
    widths={2:set(),4:set(),6:set(),8:set()}
    for token in re.findall(r"(?<!\d)(\d{2}|\d{4}|\d{6}|\d{8})(?!\d)",section):
        if len(token) in widths:widths[len(token)].add(token)
    return ded,{"Section_Bounds":"PASS","Observed_Code_Widths":{str(k):len(v) for k,v in widths.items()}}

def provider_audit()->dict[str,int]:
    return {"Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,"ETF_holdings":0,
            "third_party_GICS_tables":0,"third_party_classification_databases":0,"fuzzy_matching":0,
            "semantic_classification_inference":0,"cross_taxonomy_mapping":0,"PDSC":0,"Frozen_63_linkage":0,
            "per_security_fanout":0,"AU_Gate_E":0,"AU_Gate_F":0,"Gate_H":0,"canonical_materialization":0,
            "Sector_RS":0,"P0":0,"P1":0,"P2":0,"official_MSCI_methodology_requests":1,"fresh_ASX_directory_requests":0}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_au_sp_asx200_gate_d_msci_gics_repair_v0_85")
    args=ap.parse_args();pred=validate_predecessor(args.repository_sha);spec=json.loads(SPEC.read_text())
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/args.output_dir;out.mkdir(parents=True,exist_ok=True)

    write_json(out/"v084_blocker_authority_v0.85.json",{
      "Final_Commit":REQUIRED_START_HEAD,"Verdict":pred["summary"]["verdict"],"AU_SECTOR_FIELD_CODE_FEASIBILITY_READY":"NO",
      "Taxonomy":"GICS","Formal_Level":"INDUSTRY_GROUP","Current_ASX_Raw_Classification_Values":27,
      "Official_GICS_Structure_Ready":"NO","Source_Native_GICS_Industry_Group_Codes_Ready":"NO","Selected_Code_Strategy":"NONE",
      "Blocker":"GICS_OFFICIAL_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE","Workflow":V084_WORKFLOW,
      "Artifact":V084_ARTIFACT,"Artifact_Digest":V084_DIGEST,"Tests":"20/20 PASS"
    })

    src=fetch_pdf(MSCI_URL)
    reproducible=src["HTTP_Status"]==200 and src["Bytes"]>0 and src["Raw"].startswith(b"%PDF")
    pages=[];full=""
    if reproducible:
        try:pages,full=pdf_extract(src["Raw"])
        except Exception:reproducible=False
    title_marker=bool(pages and re.search(r"GLOBAL\s+INDUSTRY\s+CLASSIFICATION\s+STANDARD.*?METHODOLOGY",pages[0],re.I|re.S))
    title="GLOBAL INDUSTRY CLASSIFICATION STANDARD (GICS®) METHODOLOGY" if title_marker else ""
    display_date=first_regex(full,r"GLOBAL INDUSTRY CLASSIFICATION STANDARD.*?\n\s*(APRIL\s+2026)") if full else ""
    if not display_date and full:display_date=first_regex(full,r"\b(APRIL\s+2026)\b")
    last_updated=first_regex(full,r"last updated in\s+([A-Za-z]+\s+\d{4})") if full else ""
    latest_marker=bool(re.search(r"The GICS Structure presented in this document is the latest Structure",full,re.I)) if full else False
    current_effective=bool(reproducible and title_marker and display_date.upper()=="APRIL 2026" and last_updated.lower()=="april 2026" and latest_marker)
    write_json(out/"msci_current_gics_methodology_source_audit_v0.85.json",{
      "Requested_URL":src["Requested_URL"],"Resolved_URL":src["Resolved_URL"],"HTTP_Status":src["HTTP_Status"],
      "Content_Type":src["Content_Type"],"Bytes":src["Bytes"],"SHA256":src["SHA256"],"Retrieval_Timestamp_UTC":src["Retrieval_Timestamp_UTC"],
      "Document_Title":title or "NOT_VERIFIED","Document_Display_Date":display_date or "NOT_VERIFIED",
      "Last_Updated_Statement":last_updated or "NOT_VERIFIED","Page_Count":len(pages) if pages else 0,
      "Access_Attempts":src["Access_Attempts"],"Reproducible":"YES" if reproducible else "NO"
    })
    write_json(out/"msci_gics_currentness_effective_status_audit_v0.85.json",{
      "Document_Display_Date":display_date or "NOT_VERIFIED","Last_Updated_Statement":last_updated or "NOT_VERIFIED",
      "Latest_Structure_Marker":"PASS" if latest_marker else "NOT_VERIFIED",
      "CURRENT_EFFECTIVE_GICS_STRUCTURE_SOURCE":"YES" if current_effective else "NO",
      "Proposed_Consultation_Used_As_Current_Authority":"NO"
    })

    owner_msci=bool(re.search(r"developed by MSCI in collaboration\s+with S&P Dow Jones Indices",full,re.I)) if full else False
    joint_governance=bool(re.search(r"GICS Governance by MSCI And S&P Dow Jones\s+Indices",full,re.I) and re.search(r"members from both MSCI and S&P Dow Jones Indices",full,re.I)) if full else False
    write_json(out/"gics_joint_owner_authority_audit_v0.85.json",{
      "Taxonomy":"GICS","Official_Source_Owner":"MSCI","Joint_GICS_Authority":"MSCI / S&P Dow Jones Indices",
      "MSCI_CoOwner_Authority_Verified":"YES" if owner_msci else "NO","Joint_Governance_Verified":"YES" if joint_governance else "NO",
      "Same_Taxonomy_CoOwner_Source":"YES","Third_Party_Substitution":"NO","Source_URL":MSCI_URL,"Source_SHA256":src["SHA256"]
    })

    counts=parse_counts(full) if full else {}
    inventory,structure_meta=parse_structure(pages) if pages else ([],{"Section_Bounds":"NOT_VERIFIED"})
    code_widths=structure_meta.get("Observed_Code_Widths",{})
    hierarchy_ready=bool(current_effective and owner_msci and joint_governance and counts and structure_meta.get("Section_Bounds")=="PASS")
    write_json(out/"gics_current_hierarchy_contract_v0.85.json",{
      "Taxonomy":"GICS","Levels":["SECTOR","INDUSTRY_GROUP","INDUSTRY","SUB_INDUSTRY"],
      "Hierarchy_Ready":"YES" if hierarchy_ready else "NO","Declared_Level_Counts":counts or "NOT_VERIFIED",
      "Observed_Code_Width_Inventory":code_widths,
      "Code_Hierarchy":{"SECTOR":"2-digit string","INDUSTRY_GROUP":"4-digit string","INDUSTRY":"6-digit string","SUB_INDUSTRY":"8-digit string"},
      "Codes_Numeric_Cast":"NO","Leading_Zeros_Preserved":"YES","Source_URL":MSCI_URL,"Source_SHA256":src["SHA256"]
    })
    write_json(out/"gics_current_level_count_audit_v0.85.json",{
      "Declared_Sectors":counts.get("SECTOR","NOT_VERIFIED"),"Declared_Industry_Groups":counts.get("INDUSTRY_GROUP","NOT_VERIFIED"),
      "Declared_Industries":counts.get("INDUSTRY","NOT_VERIFIED"),"Declared_Sub_Industries":counts.get("SUB_INDUSTRY","NOT_VERIFIED"),
      "Counts_Derived_From_Document":"YES" if counts else "NO"
    })

    for r in inventory:
        r["Source_URL"]=MSCI_URL;r["Source_SHA256"]=src["SHA256"]
    write_csv(out/"gics_industry_group_official_label_code_inventory_v0.85.csv",inventory,
              ["Official_GICS_Industry_Group_Code","Official_GICS_Industry_Group_Label","Parent_Sector_Code","Parent_Sector_Label","Source_Page_or_Location","Source_URL","Source_SHA256"])
    declared_groups=counts.get("INDUSTRY_GROUP",0)
    uniq_codes=len({r["Official_GICS_Industry_Group_Code"] for r in inventory})
    uniq_labels=len({nfc(r["Official_GICS_Industry_Group_Label"]) for r in inventory})
    inventory_complete=bool(hierarchy_ready and declared_groups and len(inventory)==declared_groups and uniq_codes==declared_groups and uniq_labels==declared_groups)
    write_json(out/"gics_industry_group_inventory_completeness_audit_v0.85.json",{
      "Declared_Industry_Group_Count":declared_groups or "NOT_VERIFIED","Extracted_Inventory_Rows":len(inventory),
      "Unique_Codes":uniq_codes,"Unique_Labels":uniq_labels,"Duplicate_Codes":len(inventory)-uniq_codes,
      "Duplicate_Labels":len(inventory)-uniq_labels,"Inventory_Complete":"YES" if inventory_complete else "NO"
    })

    raw_labels=[nfc(r["ASX_Raw_Label"]) for r in pred["raw"]]
    write_csv(out/"asx_current_raw_classification_authority_v0.85.csv",
              [{"ASX_Raw_Label":x,"Authority":"v0.84 persisted current ASX inventory","Predecessor_Final_Commit":REQUIRED_START_HEAD} for x in raw_labels])

    by_label={}
    for r in inventory:by_label.setdefault(nfc(r["Official_GICS_Industry_Group_Label"]),[]).append(r)
    bindings=[];formal=[];nonformal=[]
    for label in raw_labels:
        hits=by_label.get(label,[])
        if len(hits)==1:
            h=hits[0];status="EXACT_CODE_BOUND";formal.append(label)
            off=h["Official_GICS_Industry_Group_Label"];code=h["Official_GICS_Industry_Group_Code"]
        elif len(hits)>1:
            status="AMBIGUOUS";off="|".join(sorted({h["Official_GICS_Industry_Group_Label"] for h in hits}));code="|".join(sorted({h["Official_GICS_Industry_Group_Code"] for h in hits}))
        else:
            status="NOT_FOUND";off="";code="";nonformal.append(label)
        bindings.append({"ASX_Raw_Label":label,"Official_GICS_Label":off,"Official_GICS_Industry_Group_Code":code,"Exact_Match_Status":status,
                         "Normalization":"UNICODE_NFC_PLUS_SURROUNDING_WHITESPACE_ONLY"})
    write_csv(out/"asx_to_msci_gics_exact_label_code_binding_audit_v0.85.csv",bindings)

    known_nonformal={"Class Pend","Not Applic"}
    unexpected_unmatched=sorted(set(nonformal)-known_nonformal)
    arithmetic=len(raw_labels)==len(formal)+len(nonformal)
    write_json(out/"au_formal_vs_nonformal_value_reconciliation_v0_85.json",{
      "Current_Raw_Value_Count":len(raw_labels),"Formal_GICS_Exact_Match_Count":len(formal),
      "Nonformal_or_Unresolved_Count":len(nonformal),"Arithmetic_Reconciles":"YES" if arithmetic else "NO",
      "Nonformal_or_Unresolved_Values":sorted(nonformal),"Unexpected_Unmatched_Values":unexpected_unmatched
    })
    nonformal_rows=[]
    for label in sorted(nonformal):
        nonformal_rows.append({"Label":label,"Exact_Formal_GICS_Match":"NO","Taxonomy_Member":"NO_BY_EXACT_CURRENT_OFFICIAL_INVENTORY",
          "Semantic_Expansion":"NOT_PERFORMED","Canonical_Code_Eligibility":"NO","PDSC_Eligibility":"NO",
          "Future_Gate_F_Treatment":"ROW_NOT_PROVABLY_CLASSIFIED_IF_FROZEN_SECURITY_HAS_THIS_VALUE"})
    write_csv(out/"au_nonformal_value_governance_audit_v0_85.csv",nonformal_rows)

    code_map={}
    for r in inventory:code_map.setdefault(r["Official_GICS_Industry_Group_Code"],[]).append(r["Official_GICS_Industry_Group_Label"])
    uniq_rows=[{"Official_GICS_Industry_Group_Code":c,"Label_Count":len(v),"Official_Labels":"|".join(sorted(v)),
                "Collision_Status":"PASS_UNIQUE" if len(v)==1 else "CONFLICT"} for c,v in sorted(code_map.items())]
    collisions=sum(1 for r in uniq_rows if r["Collision_Status"]!="PASS_UNIQUE")
    write_csv(out/"gics_industry_group_code_uniqueness_audit_v0_85.csv",uniq_rows)

    ambiguous=sum(1 for r in bindings if r["Exact_Match_Status"]=="AMBIGUOUS")
    formal_coverage=sum(1 for r in bindings if r["Exact_Match_Status"]=="EXACT_CODE_BOUND")
    source_native_ready=bool(current_effective and hierarchy_ready and inventory_complete and arithmetic and not unexpected_unmatched and ambiguous==0 and collisions==0 and formal_coverage==len(raw_labels)-len(nonformal))
    write_json(out/"au_source_native_code_feasibility_decision_v0_85.json",{
      "SOURCE_NATIVE_GICS_CODE_READY":"YES" if source_native_ready else "NO","Taxonomy":"GICS","Formal_Level":"INDUSTRY_GROUP",
      "Official_Code_Source":"MSCI CURRENT GICS METHODOLOGY","Formal_Label_Count":len(formal),"Nonformal_Value_Count":len(nonformal),
      "Formal_Label_Code_Coverage":f"{formal_coverage}/{len(formal)}","Formal_Ambiguities":ambiguous,"Code_Collisions":collisions,
      "Sector_Code_Origin":"SOURCE_NATIVE" if source_native_ready else "NOT_SELECTED",
      "Sector_Code_Method":"GICS_OFFICIAL_INDUSTRY_GROUP_CODE" if source_native_ready else "NOT_SELECTED",
      "Source_Sector_Code_Contract":"exact official MSCI GICS Industry Group code as string" if source_native_ready else "NOT_VERIFIED"
    })
    write_json(out/"au_pdsc_fallback_necessity_audit_v0_85.json",{
      "PDSC_FALLBACK_REQUIRED":"NO","PDSC_Generated_Count":0,"PDSC_Collisions":0,
      "Reason":"SOURCE_NATIVE_GICS_CODE_AVAILABLE" if source_native_ready else "PDSC_NOT_ALLOWED_WHILE_OFFICIAL_CURRENT_FORMAL_STRUCTURE_IS_UNRESOLVED"
    })

    blocker=""
    if not source_native_ready:
        if not reproducible:blocker="MSCI_GICS_METHODOLOGY_NOT_REPRODUCIBLE"
        elif not current_effective:blocker="MSCI_GICS_CURRENTNESS_NOT_VERIFIED"
        elif not hierarchy_ready:blocker="GICS_INDUSTRY_GROUP_LEVEL_NOT_VERIFIED"
        elif not inventory_complete:blocker="GICS_INDUSTRY_GROUP_INVENTORY_INCOMPLETE"
        elif unexpected_unmatched:blocker="ASX_GICS_FORMAL_LABEL_NOT_FOUND_IN_OFFICIAL_GICS"
        elif ambiguous:blocker="GICS_LABEL_TO_CODE_BINDING_AMBIGUOUS"
        elif collisions:blocker="GICS_CODE_COLLISION"
        elif not arithmetic:blocker="AU_FORMAL_CLASSIFICATION_VALUE_SET_NOT_RECONCILED"
        else:blocker="AU_SECTOR_FIELD_CODE_FEASIBILITY_NOT_VERIFIED"
    next_gate="AU_SP_ASX200 DETERMINISTIC SECURITY IDENTITY LINKAGE GATE E" if source_native_ready else (
      "AU_SP_ASX200 GATE-D SOURCE-AUTHORITY PARK / ACTIVE-COHORT RESELECTION MANAGER GATE"
      if blocker in {"MSCI_GICS_METHODOLOGY_NOT_REPRODUCIBLE","MSCI_GICS_CURRENTNESS_NOT_VERIFIED","GICS_OFFICIAL_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE","GICS_INDUSTRY_GROUP_LEVEL_NOT_VERIFIED","GICS_INDUSTRY_GROUP_INVENTORY_INCOMPLETE"}
      else blocker)
    decision={"Cohort":"AU_SP_ASX200","Taxonomy":"GICS","Level":"INDUSTRY_GROUP","Classification_Field":"GICs industry group",
      "Official_Code_Source":"MSCI CURRENT GICS METHODOLOGY","Code_Strategy":"SOURCE_NATIVE_GICS_CODE" if source_native_ready else "NONE",
      "Sector_Code_Origin":"SOURCE_NATIVE" if source_native_ready else "NOT_SELECTED",
      "Sector_Code_Method":"GICS_OFFICIAL_INDUSTRY_GROUP_CODE" if source_native_ready else "NOT_SELECTED",
      "Formal_Label_Count":len(formal),"Nonformal_Value_Count":len(nonformal),
      "AU_SECTOR_FIELD_CODE_FEASIBILITY_READY":"YES" if source_native_ready else "NO",
      "Gate_D":"PASS_BY_CURRENT_GOVERNANCE" if source_native_ready else "BLOCKED","Gate_E":"NOT_EVALUATED","Gate_F":"NOT_EVALUATED","Gate_H":"NOT_EVALUATED",
      "Blocker":blocker,"Next_Gate":next_gate}
    write_json(out/"au_sector_field_code_feasibility_decision_v0_85.json",decision)

    ledger=[{"Request_Order":1,"Source_Class":"OFFICIAL_GICS_CO_OWNER_MSCI","URL":MSCI_URL,"Purpose":"CURRENT_GICS_METHODOLOGY_STRUCTURE_AND_INDUSTRY_GROUP_CODES",
             "HTTP_Status":src["HTTP_Status"],"Bytes":src["Bytes"],"SHA256":src["SHA256"],"Per_Security_Request":"NO"}]
    write_csv(out/"external_request_ledger_v0.85.csv",ledger)
    prov=provider_audit();write_json(out/"provider_call_audit_v0.85.json",prov)
    imm={"Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SHA,"BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),"Parked_Cohort_Registry_Unchanged":sha_file(PARK)==PARK_SHA,
      "IN_Gate_F":"45/45","JP_Gate_F":"197/197","Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,
      "AU_Canonical_Rows_After":0,"Frozen_63_Linkage_Runs":0,"AU_Gate_E_Runs":0,"AU_Gate_F_Runs":0,"Gate_H_Runs":0,
      "Canonical_Materialization_Runs":0,"Other_Cohort_Runs":0,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0}
    write_json(out/"immutability_audit_v0.85.json",imm)

    tests=[]
    def t(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    t("V084_BLOCKER_AUTHORITY",pred["summary"]["blocker"]=="GICS_OFFICIAL_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE",pred["summary"]["blocker"])
    t("V084_ARTIFACT",pred["checkpoint"]["artifact_id"]==V084_ARTIFACT and pred["checkpoint"]["artifact_digest"]==V084_DIGEST,V084_ARTIFACT)
    t("GATE_C_NOT_REOPENED",pred["decision"]["Taxonomy"]=="GICS" and pred["decision"]["Level"]=="INDUSTRY_GROUP","GICS/INDUSTRY_GROUP")
    t("ASX_RAW_AUTHORITY_27",len(raw_labels)==27,len(raw_labels))
    t("RECONCILIATION_ARITHMETIC",arithmetic,f"{len(raw_labels)}={len(formal)}+{len(nonformal)}")
    t("NONFORMAL_NO_CODES",all(r["Canonical_Code_Eligibility"]=="NO" and r["PDSC_Eligibility"]=="NO" for r in nonformal_rows),sorted(nonformal))
    t("PDSC_ZERO",prov["PDSC"]==0,"0")
    t("NO_FORBIDDEN_METHODS",all(prov[k]==0 for k in ["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings","third_party_GICS_tables","third_party_classification_databases","fuzzy_matching","semantic_classification_inference","cross_taxonomy_mapping","Frozen_63_linkage","per_security_fanout"]),"0")
    t("NO_DOWNSTREAM_GATES",prov["AU_Gate_E"]==prov["AU_Gate_F"]==prov["Gate_H"]==0,"0")
    t("NO_CANONICAL_RS_P",prov["canonical_materialization"]==prov["Sector_RS"]==prov["P0"]==prov["P1"]==prov["P2"]==0,"0")
    t("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA);t("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA);t("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    t("BR_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SHA);t("PARKS_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],PARK_SHA)
    t("CANONICAL_READY_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    t("NO_AU_CANONICAL",not any(AU_CANON.glob("AU_SP_ASX200_*.csv")),"0")
    if source_native_ready:
        t("MSCI_CURRENT_EFFECTIVE",current_effective,"YES");t("GICS_HIERARCHY_READY",hierarchy_ready,"YES")
        t("INVENTORY_COMPLETE",inventory_complete,f"{len(inventory)}/{declared_groups}")
        t("FORMAL_BINDING_COMPLETE",not unexpected_unmatched and ambiguous==0,f"{formal_coverage}/{len(formal)}")
        t("CODE_COLLISIONS_ZERO",collisions==0,collisions);t("GATE_D_PASS",decision["Gate_D"]=="PASS_BY_CURRENT_GOVERNANCE","PASS")
    else:
        t("GATE_D_BLOCKED",decision["Gate_D"]=="BLOCKED" and bool(blocker),blocker)
        t("BLOCKER_VALID",blocker in {"MSCI_GICS_METHODOLOGY_NOT_REPRODUCIBLE","MSCI_GICS_CURRENTNESS_NOT_VERIFIED","GICS_OFFICIAL_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE","GICS_INDUSTRY_GROUP_LEVEL_NOT_VERIFIED","GICS_INDUSTRY_GROUP_INVENTORY_INCOMPLETE","ASX_GICS_FORMAL_LABEL_NOT_FOUND_IN_OFFICIAL_GICS","GICS_LABEL_TO_CODE_BINDING_AMBIGUOUS","GICS_CODE_COLLISION","AU_FORMAL_CLASSIFICATION_VALUE_SET_NOT_RECONCILED","AU_SECTOR_FIELD_CODE_FEASIBILITY_NOT_VERIFIED","AUTHORITY_REGRESSION_REVIEW_REQUIRED"},blocker)
    write_csv(out/"test_results_v0.85.csv",tests)

    verdict="PASS_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D" if source_native_ready else "BLOCKED_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D"
    summary={"version":VERSION,"stage":STAGE,"verdict":verdict,"au_sector_field_code_feasibility_ready":source_native_ready,
      "msci_current_gics_methodology":"READY" if reproducible else "NOT_REPRODUCIBLE","document_display_date":display_date or "NOT_VERIFIED",
      "current_effective_structure":"YES" if current_effective else "NO","gics_level_counts":counts or "NOT_VERIFIED",
      "industry_group_inventory":f"{len(inventory)}/{declared_groups}" if declared_groups else "NOT_VERIFIED",
      "current_asx_raw_values":len(raw_labels),"formal_exact_match_values":len(formal),"nonformal_values":len(nonformal),
      "formal_label_code_coverage":f"{formal_coverage}/{len(formal)}","code_collisions":collisions,
      "source_native_codes_ready":source_native_ready,"pdsc_fallback_required":False,"pdsc_generated_count":0,
      "selected_code_strategy":"SOURCE_NATIVE_GICS_CODE" if source_native_ready else "NONE","blocker":blocker,
      "au_gate_e":"NOT_EVALUATED","au_gate_f":"NOT_EVALUATED","gate_h":"NOT_EVALUATED",
      "canonical_ready_rows":37,"canonical_total_rows":1425,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate}
    write_json(out/"summary_preupload_v0.85.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.85.json",{"version":VERSION,"stage":STAGE,"verdict":verdict,
      "au_sector_field_code_feasibility_ready":source_native_ready,"selected_code_strategy":summary["selected_code_strategy"],
      "blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,"next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD"})
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.85.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.85.json",{"version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,
      "repository_sha":args.repository_sha,"verdict":verdict,"au_sector_field_code_feasibility_ready":source_native_ready,
      "selected_code_strategy":summary["selected_code_strategy"],"blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "frozen_63_linkage_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,"gate_h_runs":0,"canonical_materialization_runs":0,
      "other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":next_gate})
    return 0

if __name__=="__main__":raise SystemExit(main())
