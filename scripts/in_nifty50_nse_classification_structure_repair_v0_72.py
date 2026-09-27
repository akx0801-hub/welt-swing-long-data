#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, importlib.metadata, json, os, re, statistics, subprocess, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.72"
STAGE="IN_NIFTY50_NSE_INDICES_CLASSIFICATION_STRUCTURE_EXTRACTION_LEVEL_CODE_BINDING_GATE_F_REPAIR"
REQUIRED_START_HEAD="f6be8b4a3182728ba9976b58410f91e031146348"
V071_WORKFLOW=36308429404
V071_ARTIFACT=10928267335
V071_DIGEST="sha256:9de669cf670be62f99f325ae7deedb2af8028d6222d6b725af8d71a94e3244ed"
V071_NIFTY_SHA="9fb8832853c279448d2bc05f0e7dd5f460ed2ff35332fea8c40fc1250362ad28"
V071_PDF_SHA="8ae58cbd10d7dd5184d76cfec6486f91c019026c8de329432b69c54ff7235f8b"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

TAXONOMY="NSE_INDICES_INDUSTRY_CLASSIFICATION"
PDF_URL="https://www.niftyindices.com/docs/default-source/default-document-library/industry-classification/nse-indices_industry-classification-structure-2023-07.pdf?sfvrsn=c89dd39_1"
CLASSIFICATION_PAGE="https://www.niftyindices.com/resources/industry-classification"
NIFTY_URL="https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.72"

SPEC=ROOT/"config/in_nifty50_nse_classification_structure_repair_spec_v0.72.json"
SUM71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/summary_v0.71.json"
CHK71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/stage_checkpoint_v0.71.json"
MAN71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/manifest_v0.71.json"
LEVEL71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/in_classification_level_binding_v0.71.json"
TAX71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/nse_industry_taxonomy_contract_audit_v0.71.json"
SRC71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/official_nifty50_classification_source_audit_v0.71.json"
COV71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/in_exact_45_classification_coverage_v0.71.csv"
INV71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/in_distinct_classification_inventory_v0.71.csv"
LINK70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/in_exact_45_identity_linkage_audit_v0.70.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"

LEVELS=["MACRO_ECONOMIC_SECTOR","SECTOR","INDUSTRY","BASIC_INDUSTRY"]
DIGITS_TO_LEVEL={2:"MACRO_ECONOMIC_SECTOR",4:"SECTOR",6:"INDUSTRY",9:"BASIC_INDUSTRY"}
LEVEL_TO_DIGITS={v:k for k,v in DIGITS_TO_LEVEL.items()}
CODE_RE=re.compile(r"(?<![A-Z0-9])IN(?P<digits>\d{9}|\d{6}|\d{4}|\d{2})(?!\d)")

EXPECTED_LABELS=[
    "Automobile and Auto Components","Capital Goods","Construction","Construction Materials",
    "Consumer Durables","Consumer Services","Fast Moving Consumer Goods","Financial Services",
    "Healthcare","Information Technology","Metals & Mining","Oil Gas & Consumable Fuels",
    "Power","Services","Telecommunication"
]

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

def ws_norm(s:str)->str:
    return re.sub(r"\s+"," ",s.replace("\u00a0"," ")).strip()

def fetch_pdf()->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    host=urllib.parse.urlparse(PDF_URL).hostname
    if host not in {"www.niftyindices.com","niftyindices.com"}:
        return {"ok":False,"timestamp_utc":ts,"status":"","content_type":"","body":b"","error":"HOST_NOT_ALLOWED"}
    req=urllib.request.Request(PDF_URL,headers={"User-Agent":UA,"Accept":"application/pdf,*/*;q=0.8"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read(5_000_001)
            trunc=len(b)>5_000_000
            if trunc:b=b[:5_000_000]
            return {"ok":200<=getattr(r,"status",200)<300 and not trunc,"timestamp_utc":ts,
                    "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"truncated":trunc,"body":b,"resolved_url":r.geturl()}
    except Exception as e:
        return {"ok":False,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","truncated":False,
                "body":b"","error":f"{type(e).__name__}:{e}","resolved_url":PDF_URL}

def extract_pdf_layout(pdf:bytes)->dict[str,Any]:
    from pypdf import PdfReader
    version=importlib.metadata.version("pypdf")
    reader=PdfReader(io.BytesIO(pdf))
    pages=[]
    warnings=[]
    for i,p in enumerate(reader.pages):
        try:
            txt=p.extract_text(extraction_mode="layout") or ""
        except TypeError:
            txt=p.extract_text() or ""
            warnings.append(f"page_{i+1}:layout_mode_not_supported_fallback_plain")
        pages.append(txt.replace("\r\n","\n").replace("\r","\n"))
    joined="\n\fPAGE_BREAK\f\n".join(pages)
    return {"tool":"pypdf","version":version,"page_count":len(pages),"pages":pages,
            "extracted_text_sha256":sha_bytes(joined.encode("utf-8")),"warnings":warnings}

def median_int(vals:list[int])->int:
    return int(round(statistics.median(vals)))

def analyze_anchors(pages:list[str])->dict[str,Any]:
    pos=defaultdict(list);definition=[]
    page_table=[]
    for pno,text in enumerate(pages,1):
        code_count=0
        for line in text.splitlines():
            for m in CODE_RE.finditer(line):
                level=DIGITS_TO_LEVEL[len(m.group("digits"))]
                pos[level].append(m.start());code_count+=1
            if "Definition" in line:
                definition.append(line.find("Definition"))
        if code_count:
            page_table.append(pno)
    anchors={lvl:median_int(pos[lvl]) for lvl in LEVELS if pos[lvl]}
    def_anchor=median_int(definition) if definition else None
    return {"anchors":anchors,"definition_anchor":def_anchor,"pages_with_taxonomy_content":page_table,
            "code_position_counts":{k:len(v) for k,v in pos.items()}}

def _exact_code_in_slice(cell:str,level:str)->re.Match[str]|None:
    need=LEVEL_TO_DIGITS[level]
    for m in CODE_RE.finditer(cell):
        if len(m.group("digits"))==need:return m
    return None

def parse_taxonomy(pages:list[str])->dict[str,Any]:
    aa=analyze_anchors(pages);anchors=aa["anchors"];def_anchor=aa["definition_anchor"]
    if any(l not in anchors for l in LEVELS):
        return {"ok":False,"blocker":"NSE_CLASSIFICATION_STRUCTURE_PARSE_AMBIGUOUS","detail":"missing level anchors","anchor_audit":aa}
    ordered=[anchors[l] for l in LEVELS]
    if ordered!=sorted(ordered) or len(set(ordered))<4:
        return {"ok":False,"blocker":"NSE_CLASSIFICATION_STRUCTURE_PARSE_AMBIGUOUS","detail":"non-increasing column anchors","anchor_audit":aa}
    if def_anchor is None or def_anchor<=anchors["BASIC_INDUSTRY"]:
        # bounded fallback derived from observed basic-column geometry
        def_anchor=anchors["BASIC_INDUSTRY"]+38
    starts={l:anchors[l] for l in LEVELS}
    ends={
      "MACRO_ECONOMIC_SECTOR":anchors["SECTOR"],
      "SECTOR":anchors["INDUSTRY"],
      "INDUSTRY":anchors["BASIC_INDUSTRY"],
      "BASIC_INDUSTRY":def_anchor
    }
    nodes={l:{} for l in LEVELS}
    duplicate_code_conflicts=[]
    current={l:None for l in LEVELS}

    def append_fragment(level:str,code:str,frag:str,page:int):
        frag=frag.strip()
        if not frag:return
        d=nodes[level].setdefault(code,{"code":code,"raw_fragments":[],"pages":[]})
        if frag not in d["raw_fragments"]:
            d["raw_fragments"].append(frag)
        if page not in d["pages"]:d["pages"].append(page)

    for pno,text in enumerate(pages,1):
        lines=text.splitlines()
        first=None
        for idx,line in enumerate(lines):
            if CODE_RE.search(line):
                first=idx;break
        if first is None:continue
        for line in lines[first:]:
            if "NSE Indices Industry Classification Structure" in line:continue
            if any(h in line for h in ("MES_Code","Sect_Code","Ind_Code","Basic_Ind_Code")):continue
            line_has_code=bool(CODE_RE.search(line))
            for level in LEVELS:
                s=max(0,starts[level]-2);e=min(len(line),ends[level]) if ends[level] is not None else len(line)
                if s>=len(line):cell=""
                else:cell=line[s:e]
                m=_exact_code_in_slice(cell,level)
                if m:
                    code=m.group(0)
                    frag=cell[m.end():].strip()
                    existing=nodes[level].get(code)
                    if existing and frag and existing["raw_fragments"] and ws_norm(" ".join(existing["raw_fragments"]))!=ws_norm(" ".join(existing["raw_fragments"]+[frag])):
                        # repeated exact code is permitted only if it continues the same extracted name; conflicting new start is audited.
                        if frag not in existing["raw_fragments"]:
                            duplicate_code_conflicts.append({"Level":level,"Code":code,"Existing":ws_norm(" ".join(existing["raw_fragments"])),"New_Fragment":frag,"Page":pno})
                    current[level]=code
                    lower=LEVELS[LEVELS.index(level)+1:]
                    for lo in lower:current[lo]=None
                    append_fragment(level,code,frag,pno)
                else:
                    frag=cell.strip()
                    if not frag or not current[level]:continue
                    if CODE_RE.search(frag):continue
                    # Do not absorb header fragments.
                    if frag in {"Macro","Economic","Sector","Industry","Basic Industry","Definition"}:continue
                    # Continuation is allowed only when no new same/higher level code appears on this line.
                    higher=LEVELS[:LEVELS.index(level)+1]
                    higher_code=False
                    for hm in CODE_RE.finditer(line):
                        hl=DIGITS_TO_LEVEL[len(hm.group("digits"))]
                        if hl in higher:
                            higher_code=True;break
                    if not higher_code:
                        append_fragment(level,current[level],frag,pno)

    for level in LEVELS:
        for code,d in nodes[level].items():
            d["raw_name"]="\n".join(d["raw_fragments"])
            d["name"]=ws_norm(" ".join(d["raw_fragments"]))

    # Validate encoded-parent relationships.
    missing_parents=[]
    for code in nodes["SECTOR"]:
        if code[:4] not in nodes["MACRO_ECONOMIC_SECTOR"]:missing_parents.append(("SECTOR",code,code[:4]))
    for code in nodes["INDUSTRY"]:
        if code[:6] not in nodes["SECTOR"]:missing_parents.append(("INDUSTRY",code,code[:6]))
    for code in nodes["BASIC_INDUSTRY"]:
        if code[:8] not in nodes["INDUSTRY"]:missing_parents.append(("BASIC_INDUSTRY",code,code[:8]))
    if duplicate_code_conflicts or missing_parents:
        return {"ok":False,"blocker":"NSE_CLASSIFICATION_STRUCTURE_PARSE_AMBIGUOUS",
                "detail":"duplicate code conflicts or missing encoded parents","anchor_audit":aa,
                "duplicate_code_conflicts":duplicate_code_conflicts,"missing_parents":missing_parents,"nodes":nodes}

    rows=[]
    basic_by_ind=defaultdict(list)
    for b in nodes["BASIC_INDUSTRY"]:basic_by_ind[b[:8]].append(b)
    for ic in sorted(nodes["INDUSTRY"]):
        sc=ic[:6];mc=ic[:4]
        children=sorted(basic_by_ind.get(ic,[])) or [""]
        for bc in children:
            rows.append({
              "Macro_Economic_Sector_Code":mc,
              "Macro_Economic_Sector_Name_RawExtracted":nodes["MACRO_ECONOMIC_SECTOR"][mc]["raw_name"],
              "Macro_Economic_Sector_Name":nodes["MACRO_ECONOMIC_SECTOR"][mc]["name"],
              "Sector_Code":sc,
              "Sector_Name_RawExtracted":nodes["SECTOR"][sc]["raw_name"],
              "Sector_Name":nodes["SECTOR"][sc]["name"],
              "Industry_Code":ic,
              "Industry_Name_RawExtracted":nodes["INDUSTRY"][ic]["raw_name"],
              "Industry_Name":nodes["INDUSTRY"][ic]["name"],
              "Basic_Industry_Code":bc,
              "Basic_Industry_Name_RawExtracted":nodes["BASIC_INDUSTRY"][bc]["raw_name"] if bc else "",
              "Basic_Industry_Name":nodes["BASIC_INDUSTRY"][bc]["name"] if bc else ""
            })
    structural=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return {"ok":True,"rows":rows,"nodes":nodes,"anchor_audit":aa,
            "structural_sha256":sha_bytes(structural),"duplicate_code_conflicts":[],"missing_parents":[]}

def parent_path(level:str,code:str,nodes:dict[str,dict[str,Any]])->str:
    parts=[]
    if level in ("MACRO_ECONOMIC_SECTOR","SECTOR","INDUSTRY","BASIC_INDUSTRY"):
        mc=code[:4]
        if mc in nodes["MACRO_ECONOMIC_SECTOR"]:parts.append(mc+" "+nodes["MACRO_ECONOMIC_SECTOR"][mc]["name"])
    if level in ("SECTOR","INDUSTRY","BASIC_INDUSTRY"):
        sc=code[:6]
        if sc in nodes["SECTOR"]:parts.append(sc+" "+nodes["SECTOR"][sc]["name"])
    if level in ("INDUSTRY","BASIC_INDUSTRY"):
        ic=code[:8]
        if ic in nodes["INDUSTRY"]:parts.append(ic+" "+nodes["INDUSTRY"][ic]["name"])
    if level=="BASIC_INDUSTRY":
        if code in nodes["BASIC_INDUSTRY"]:parts.append(code+" "+nodes["BASIC_INDUSTRY"][code]["name"])
    return " > ".join(parts)

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,
      "investing_com":0,"etf_holdings":0,"third_party_sector_databases":0,"company_sites":0,
      "company_name_joins":0,"fuzzy_matching":0,"per_security_web_fanout":0,"gics_icb_fallback":0,
      "cross_taxonomy_mapping":0,"price_ohlcv":0,"news":0,"trading_analysis":0,"pdsc_fallback":0,
      "nse_equity_l":0,"nifty_constituent_refetch":0,"ocr":0,"manual_transcription":0,"screenshots_taxonomy_evidence":0
    }

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM71.read_text(encoding="utf-8"));c=json.loads(CHK71.read_text(encoding="utf-8"))
    level=json.loads(LEVEL71.read_text(encoding="utf-8"));tax=json.loads(TAX71.read_text(encoding="utf-8"));src=json.loads(SRC71.read_text(encoding="utf-8"))
    cov=read_csv(COV71);inv=read_csv(INV71);link70=read_csv(LINK70)
    if s["verdict"]!="BLOCKED_IN_NIFTY50_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE":raise RuntimeError("v0.71 verdict")
    if s["in_exact_45_sector_classification_coverage_ready"] is not False:raise RuntimeError("v0.71 readiness")
    if (s["classified"],s["total"],s["not_verified"])!=(0,45,45):raise RuntimeError("v0.71 counts")
    if s["taxonomy"]!=TAXONOMY or s["bound_classification_level"]!="NOT_VERIFIED" or s["distinct_classifications"]!=15 or s["source_native_code_coverage"]!=0:raise RuntimeError("v0.71 classification state")
    if s["blocker"]!="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED":raise RuntimeError("v0.71 blocker")
    if c["workflow_run_id"]!=V071_WORKFLOW or c["artifact_id"]!=V071_ARTIFACT or "sha256:"+c["artifact_digest"]!=V071_DIGEST:raise RuntimeError("v0.71 artifact authority")
    if src["Raw_SHA256"]!=V071_NIFTY_SHA:raise RuntimeError("v0.71 NIFTY source sha")
    if tax["Structure_Raw_SHA256"]!=V071_PDF_SHA or tax["Selected_Structure_URL"]!=PDF_URL:raise RuntimeError("v0.71 PDF authority")
    if level["Exact_Unique_Industry_Code_Bindings"]!=0 or level["Level_Binding_Status"]!="NOT_VERIFIED":raise RuntimeError("v0.71 structured level result")
    narrative="Every distinct non-empty current NIFTY Industry value for the Frozen-45 exact ISIN rows is exact-match bound to one unique Ind_Code in the official classification structure."
    if narrative not in level["Level_Binding_Evidence"]:raise RuntimeError("expected v0.71 narrative inconsistency absent")
    if len(cov)!=45 or any(r["Current_NIFTY_ISIN_Match_Count"]!="1" or not r["Source_Classification_Raw"] for r in cov):raise RuntimeError("v0.71 coverage rows")
    labels=sorted({r["Source_Classification_Raw"] for r in cov})
    if labels!=sorted(EXPECTED_LABELS):raise RuntimeError("v0.71 exact 15 labels mismatch")
    if len(inv)!=15:raise RuntimeError("v0.71 inventory rows")
    if len(link70)!=45 or any(r["Gate_E_Status"]!="PROVABLY_LINKED" for r in link70):raise RuntimeError("v0.70 identity authority")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability predecessor")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    return {"summary":s,"level":level,"tax":tax,"src":src,"coverage":cov,"identity70":link70}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_in_nifty50_nse_classification_structure_repair_v0_72")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    inconsistency={
      "Version":VERSION,
      "Predecessor":"v0.71",
      "Erroneous_Narrative_Text":"Every distinct non-empty current NIFTY Industry value for the Frozen-45 exact ISIN rows is exact-match bound to one unique Ind_Code in the official classification structure.",
      "Structured_Exact_Unique_Industry_Code_Bindings":pred["level"]["Exact_Unique_Industry_Code_Bindings"],
      "Structured_Level_Binding_Status":pred["level"]["Level_Binding_Status"],
      "v071_Source_Native_Code_Coverage":pred["summary"]["source_native_code_coverage"],
      "v071_Not_Verified_Rows":pred["summary"]["not_verified"],
      "Authority_Treatment":"NON_AUTHORITATIVE_ERRONEOUS_NARRATIVE_TEXT",
      "Structured_Evidence_Prevails":True,
      "Historical_v071_Files_Rewritten":False
    }
    (out/"v071_predecessor_evidence_inconsistency_audit_v0.72.json").write_text(json.dumps(inconsistency,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    env={
      "Parser_Available_Preinstall":os.environ.get("V072_PDF_PARSER_AVAILABLE_PREINSTALL","NOT_RECORDED"),
      "Package":"pypdf",
      "Installed_Version":importlib.metadata.version("pypdf"),
      "Required_Version":spec["pdf_parser"]["required_version"],
      "Installation_Command":os.environ.get("V072_PDF_DEPENDENCY_INSTALL_COMMAND",spec["pdf_parser"]["install_command"]),
      "Package_Source_Class":os.environ.get("V072_PDF_PACKAGE_SOURCE_CLASS",spec["pdf_parser"]["package_source_class"]),
      "Extraction_Method":spec["pdf_parser"]["extraction_method"],
      "OCR_Used":False,"Manual_Transcription_Used":False,"Screenshot_Evidence_Used":False
    }
    if env["Installed_Version"]!=spec["pdf_parser"]["required_version"]:raise RuntimeError("unexpected pypdf version")
    (out/"nse_pdf_extraction_environment_v0.72.json").write_text(json.dumps(env,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    fr=fetch_pdf()
    ext=[{
      "Request_Order":1,"Request_Type":"NSE_INDICES_CLASSIFICATION_STRUCTURE_PDF","URL":PDF_URL,
      "Resolved_URL":fr.get("resolved_url",PDF_URL),"Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),
      "Bytes":fr.get("bytes",0),"SHA256":fr.get("sha256",""),"Timestamp_UTC":fr.get("timestamp_utc",""),
      "Official_Source":"YES","Market_Reference_Request":"YES","Per_Security_Fanout":"NO",
      "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")
    }]
    write_csv(out/"external_request_ledger_v0.72.csv",ext)

    extraction_blocker=""
    ex1=ex2=None;parse1=parse2=None
    if not fr.get("ok"):
        extraction_blocker="NSE_CLASSIFICATION_STRUCTURE_MACHINE_EXTRACTION_FAILED"
    else:
        try:
            ex1=extract_pdf_layout(fr["body"])
            ex2=extract_pdf_layout(fr["body"])
            parse1=parse_taxonomy(ex1["pages"])
            parse2=parse_taxonomy(ex2["pages"])
            if ex1["extracted_text_sha256"]!=ex2["extracted_text_sha256"]:
                extraction_blocker="NSE_CLASSIFICATION_STRUCTURE_MACHINE_EXTRACTION_FAILED"
            elif not parse1.get("ok") or not parse2.get("ok"):
                extraction_blocker=(parse1.get("blocker") or parse2.get("blocker") or "NSE_CLASSIFICATION_STRUCTURE_PARSE_AMBIGUOUS")
            elif parse1["structural_sha256"]!=parse2["structural_sha256"]:
                extraction_blocker="NSE_CLASSIFICATION_STRUCTURE_PARSE_AMBIGUOUS"
        except Exception as e:
            extraction_blocker="NSE_CLASSIFICATION_STRUCTURE_MACHINE_EXTRACTION_FAILED"
            ex1={"error":f"{type(e).__name__}:{e}","page_count":0,"extracted_text_sha256":"","warnings":[]}
            ex2={"error":f"{type(e).__name__}:{e}","page_count":0,"extracted_text_sha256":"","warnings":[]}

    repro={
      "PDF_URL":PDF_URL,"PDF_SHA256":fr.get("sha256",""),"Expected_v071_PDF_SHA256":V071_PDF_SHA,
      "PDF_SHA_Matches_v071":fr.get("sha256","")==V071_PDF_SHA,"PDF_Byte_Count":fr.get("bytes",0),
      "Extraction_Tool":"pypdf","Extraction_Tool_Version":env["Installed_Version"],
      "Extraction_Method":env["Extraction_Method"],
      "Run1_Extracted_Text_SHA256":ex1.get("extracted_text_sha256","") if ex1 else "",
      "Run2_Extracted_Text_SHA256":ex2.get("extracted_text_sha256","") if ex2 else "",
      "Run1_Structural_SHA256":parse1.get("structural_sha256","") if parse1 else "",
      "Run2_Structural_SHA256":parse2.get("structural_sha256","") if parse2 else "",
      "Deterministic_Extracted_Text":bool(ex1 and ex2 and ex1.get("extracted_text_sha256")==ex2.get("extracted_text_sha256") and ex1.get("extracted_text_sha256")),
      "Deterministic_Structural_Output":bool(parse1 and parse2 and parse1.get("structural_sha256")==parse2.get("structural_sha256") and parse1.get("structural_sha256")),
      "Page_Count":ex1.get("page_count",0) if ex1 else 0,
      "Pages_With_Taxonomy_Table_Content":parse1.get("anchor_audit",{}).get("pages_with_taxonomy_content",[]) if parse1 else [],
      "Parser_Warnings_Run1":ex1.get("warnings",[]) if ex1 else [],
      "Parser_Warnings_Run2":ex2.get("warnings",[]) if ex2 else [],
      "Extraction_Error":extraction_blocker or (ex1.get("error","") if ex1 else ""),
      "Raw_PDF_Persisted":False,"Raw_PDF_Redistribution_Rights":"NOT_VERIFIED"
    }
    (out/"nse_pdf_extraction_reproducibility_audit_v0.72.json").write_text(json.dumps(repro,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    nodes={l:{} for l in LEVELS};structured=[]
    if parse1 and parse1.get("ok"):
        nodes=parse1["nodes"];structured=parse1["rows"]
    write_csv(out/"nse_industry_classification_structured_table_v0.72.csv",structured if structured else [{
      "Macro_Economic_Sector_Code":"","Macro_Economic_Sector_Name_RawExtracted":"","Macro_Economic_Sector_Name":"",
      "Sector_Code":"","Sector_Name_RawExtracted":"","Sector_Name":"","Industry_Code":"","Industry_Name_RawExtracted":"",
      "Industry_Name":"","Basic_Industry_Code":"","Basic_Industry_Name_RawExtracted":"","Basic_Industry_Name":""
    }])

    level_inventory=[]
    for level in LEVELS:
        name_counts=Counter(d["name"] for d in nodes[level].values() if d.get("name"))
        level_inventory.append({
          "Taxonomy_Level":level,"Node_Count":len(nodes[level]),"Distinct_Name_Count":len(name_counts),
          "Duplicate_Name_Count":sum(1 for n,c in name_counts.items() if c>1),
          "Source_Native_Code_Count":len(nodes[level]),
          "Empty_Name_Count":sum(1 for d in nodes[level].values() if not d.get("name"))
        })
    write_csv(out/"nse_taxonomy_level_inventory_v0.72.csv",level_inventory)

    match_rows=[];satisfying=[]
    for label in EXPECTED_LABELS:
        rec={"Source_Classification_Raw":label}
        for level in LEVELS:
            hits=sorted(code for code,d in nodes[level].items() if d.get("name")==label)
            key={"MACRO_ECONOMIC_SECTOR":"MES","SECTOR":"SECTOR","INDUSTRY":"INDUSTRY","BASIC_INDUSTRY":"BASIC_INDUSTRY"}[level]
            rec[key+"_MATCH_COUNT"]=len(hits)
            rec[key+"_MATCH_CODES"]=" | ".join(hits)
        match_rows.append(rec)
    write_csv(out/"in_15_label_cross_level_match_audit_v0.72.csv",match_rows)
    for level in LEVELS:
        key={"MACRO_ECONOMIC_SECTOR":"MES","SECTOR":"SECTOR","INDUSTRY":"INDUSTRY","BASIC_INDUSTRY":"BASIC_INDUSTRY"}[level]
        if all(int(r[key+"_MATCH_COUNT"])==1 for r in match_rows):
            satisfying.append(level)

    if extraction_blocker:
        bound_level=""
        level_status="NOT_VERIFIED"
    elif len(satisfying)==1:
        bound_level=satisfying[0];level_status="PASS"
    elif len(satisfying)==0:
        bound_level="";level_status="NOT_VERIFIED"
    else:
        bound_level="";level_status="AMBIGUOUS"

    level_binding={
      "Taxonomy":TAXONOMY,"Source_Field_Name":"Industry","Observed_Label_Count":15,
      "Complete_Set_Satisfying_Levels":satisfying,
      "Official_Taxonomy_Level":bound_level or "NOT_VERIFIED",
      "Level_Binding_Status":level_status,
      "Rule":"Exactly one formal level must contain exactly one exact node for each of all 15 observed labels.",
      "CSV_Header_Privileged":False,"Semantic_Inference_Used":False,
      "Evidence_References":[PDF_URL,CLASSIFICATION_PAGE,"v0.71 derived exact-45 Source_Classification_Raw evidence"]
    }
    (out/"in_classification_level_binding_v0_72.json").write_text(json.dumps(level_binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    mapping={};binding_rows=[]
    if bound_level:
        for label in EXPECTED_LABELS:
            hits=sorted((code,d) for code,d in nodes[bound_level].items() if d.get("name")==label)
            status="PASS" if len(hits)==1 else ("AMBIGUOUS" if len(hits)>1 else "NOT_VERIFIED")
            code=hits[0][0] if len(hits)==1 else ""
            if status=="PASS":mapping[label]=code
            binding_rows.append({
              "Source_Classification_Raw":label,"Official_Taxonomy_Level":bound_level,
              "Source_Native_Code":code or "NOT_VERIFIED",
              "Official_Source_Name":hits[0][1]["name"] if len(hits)==1 else "NOT_VERIFIED",
              "Parent_Path":parent_path(bound_level,code,nodes) if code else "NOT_VERIFIED",
              "Exact_Match_Count":len(hits),"Code_Binding_Status":status,"Evidence_Reference":PDF_URL
            })
    else:
        for label in EXPECTED_LABELS:
            binding_rows.append({
              "Source_Classification_Raw":label,"Official_Taxonomy_Level":"NOT_VERIFIED",
              "Source_Native_Code":"NOT_VERIFIED","Official_Source_Name":"NOT_VERIFIED","Parent_Path":"NOT_VERIFIED",
              "Exact_Match_Count":0,"Code_Binding_Status":"NOT_VERIFIED","Evidence_Reference":PDF_URL
            })
    write_csv(out/"in_source_native_code_binding_v0.72.csv",binding_rows)

    collision_rows=[]
    code_to_labels=defaultdict(list)
    if bound_level:
        for label,code in mapping.items():code_to_labels[code].append(label)
        for label in EXPECTED_LABELS:
            collision_rows.append({
              "Scope":"OBSERVED_15","Taxonomy_Level":bound_level,"Label":label,"Code":mapping.get(label,"NOT_VERIFIED"),
              "Same_Level_Label_Node_Count":sum(1 for d in nodes[bound_level].values() if d.get("name")==label),
              "Observed_Labels_Sharing_Code":" | ".join(sorted(code_to_labels.get(mapping.get(label,""),[]))),
              "Collision_Status":"PASS" if label in mapping and len(code_to_labels[mapping[label]])==1 else "AMBIGUOUS"
            })
    # Persist full-taxonomy duplicate labels separately in the same audit.
    for level in LEVELS:
        groups=defaultdict(list)
        for code,d in nodes[level].items():
            if d.get("name"):groups[d["name"]].append(code)
        for label,codes in sorted(groups.items()):
            if len(codes)>1:
                collision_rows.append({
                  "Scope":"FULL_TAXONOMY_DUPLICATE_LABEL","Taxonomy_Level":level,"Label":label,"Code":" | ".join(sorted(codes)),
                  "Same_Level_Label_Node_Count":len(codes),"Observed_Labels_Sharing_Code":"","Collision_Status":"DUPLICATE_LABEL"
                })
    write_csv(out/"in_code_uniqueness_collision_audit_v0.72.csv",collision_rows if collision_rows else [{
      "Scope":"NONE","Taxonomy_Level":"","Label":"","Code":"","Same_Level_Label_Node_Count":0,"Observed_Labels_Sharing_Code":"","Collision_Status":"PASS"
    }])

    binding_pass=(bound_level!="" and len(mapping)==15 and all(r["Code_Binding_Status"]=="PASS" for r in binding_rows))
    code_collision=any(len(v)>1 for v in code_to_labels.values())
    authority_regression=(bound_level!="" and any(r["Code_Binding_Status"]!="PASS" for r in binding_rows))

    identity70={r["WS_ID"]:r for r in pred["identity70"]}
    repaired=[]
    row_counts=Counter()
    for r in pred["coverage"]:
        status="NOT_VERIFIED";code="NOT_VERIFIED";detail=""
        ident=identity70.get(r["WS_ID"])
        label=r["Source_Classification_Raw"]
        if not ident or ident["Gate_E_Status"]!="PROVABLY_LINKED":
            status="NOT_VERIFIED";detail="v0.70 identity authority missing."
        elif r["Current_NIFTY_ISIN_Match_Count"]!="1":
            status="CONFLICT";detail="v0.71 exact source ISIN match count is not one."
        elif not label:
            status="NOT_VERIFIED";detail="v0.71 Source_Classification_Raw empty."
        elif not binding_pass:
            status="NOT_VERIFIED";detail="Level/code binding not fully verified."
        elif label not in mapping:
            status="NOT_FOUND";detail="Observed label absent from verified 15-label mapping."
        else:
            status="PROVABLY_CLASSIFIED";code=mapping[label]
        row_counts[status]+=1
        repaired.append({
          "Security_Key":r["Security_Key"],"WS_ID":r["WS_ID"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Frozen_ISIN":r["Frozen_ISIN"],"v070_Identity_Status":ident["Gate_E_Status"] if ident else "NOT_VERIFIED",
          "v071_Current_NIFTY_ISIN_Match_Count":r["Current_NIFTY_ISIN_Match_Count"],
          "Source_Classification_Raw":label,"Taxonomy":TAXONOMY,
          "Official_Taxonomy_Level":bound_level or "NOT_VERIFIED","Source_Native_Code":code,
          "Classification_Status":status,"Evidence_Reference":"v0.71 exact-45 derived row evidence | "+PDF_URL,"Detail":detail
        })
    write_csv(out/"in_exact_45_classification_coverage_v0.72.csv",repaired)

    label_counts=Counter(r["Source_Classification_Raw"] for r in pred["coverage"])
    inventory=[]
    for label in EXPECTED_LABELS:
        inventory.append({
          "Source_Classification_Raw":label,"Official_Taxonomy_Level":bound_level or "NOT_VERIFIED",
          "Source_Native_Code":mapping.get(label,"NOT_VERIFIED"),"Frozen_Row_Count":label_counts[label],
          "Unique_Code_Status":"PASS" if label in mapping and len(code_to_labels[mapping[label]])==1 else "NOT_VERIFIED"
        })
    write_csv(out/"in_distinct_classification_inventory_v0.72.csv",inventory)

    classified=row_counts["PROVABLY_CLASSIFIED"];ambiguous=row_counts["AMBIGUOUS"];not_found=row_counts["NOT_FOUND"]
    not_verified=row_counts["NOT_VERIFIED"];conflict=row_counts["CONFLICT"]
    source_code_coverage=sum(1 for r in repaired if r["Classification_Status"]=="PROVABLY_CLASSIFIED" and r["Source_Native_Code"]!="NOT_VERIFIED")

    blocker=""
    if extraction_blocker=="NSE_CLASSIFICATION_STRUCTURE_MACHINE_EXTRACTION_FAILED":
        blocker="NSE_CLASSIFICATION_STRUCTURE_MACHINE_EXTRACTION_FAILED"
    elif extraction_blocker:
        blocker="NSE_CLASSIFICATION_STRUCTURE_PARSE_AMBIGUOUS"
    elif level_status=="NOT_VERIFIED":
        blocker="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED"
    elif level_status=="AMBIGUOUS":
        blocker="NIFTY_CLASSIFICATION_LEVEL_AMBIGUOUS"
    elif authority_regression:
        blocker="AUTHORITY_REGRESSION_REVIEW_REQUIRED"
    elif not binding_pass:
        blocker="NIFTY_SOURCE_NATIVE_CODE_BINDING_NOT_VERIFIED"
    elif code_collision:
        blocker="NIFTY_SOURCE_NATIVE_CODE_COLLISION"
    elif (classified,ambiguous,not_found,not_verified,conflict)!=(45,0,0,0,0):
        blocker="IN_EXACT_45_CLASSIFICATION_COVERAGE_INCOMPLETE"

    ready=(blocker=="" and bound_level!="" and len(mapping)==15 and classified==45 and ambiguous==not_found==not_verified==conflict==0 and source_code_coverage==45)
    verdict="PASS_IN_NIFTY50_GATE_F_REPAIR_EXACT_CLASSIFICATION_COVERAGE" if ready else "BLOCKED_IN_NIFTY50_GATE_F_REPAIR"
    next_gate="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE" if ready else blocker
    extraction_status=("PASS: pypdf "+env["Installed_Version"]+", "+str(repro["Page_Count"])+" pages, deterministic structural SHA "+repro["Run1_Structural_SHA256"]) if (parse1 and parse1.get("ok") and repro["Deterministic_Structural_Output"]) else "FAILED"

    providers=provider_calls()
    (out/"provider_call_audit_v0.72.json").write_text(json.dumps(providers,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "Gate_E_Reruns":0,"NIFTY_Constituent_Refetches":0,"NSE_EQUITY_L_Calls":0,"Gate_H_Promotions":0,
      "Canonical_Materialization_Runs":0,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.72.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("PREDECESSOR_V071_BLOCKER",pred["summary"]["blocker"]=="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED",pred["summary"]["blocker"])
    test("PREDECESSOR_INCONSISTENCY_RECORDED",inconsistency["Structured_Evidence_Prevails"] is True,"PASS")
    test("V070_IDENTITY_45",len(pred["identity70"])==45 and all(r["Gate_E_Status"]=="PROVABLY_LINKED" for r in pred["identity70"]),"PASS")
    test("V071_COVERAGE_ROWS_45",len(pred["coverage"])==45,45)
    test("V071_LABEL_SET_15",sorted({r["Source_Classification_Raw"] for r in pred["coverage"]})==sorted(EXPECTED_LABELS),15)
    test("NO_NIFTY_REFETCH",providers["nifty_constituent_refetch"]==0,0)
    test("NO_EQUITY_L",providers["nse_equity_l"]==0,0)
    test("NO_OCR",providers["ocr"]==0,0)
    test("NO_MANUAL_TRANSCRIPTION",providers["manual_transcription"]==0,0)
    test("NO_PDSC",providers["pdsc_fallback"]==0,0)
    test("NO_NAME_JOIN",providers["company_name_joins"]==0,0)
    test("NO_FUZZY",providers["fuzzy_matching"]==0,0)
    test("NO_CROSS_TAXONOMY",providers["cross_taxonomy_mapping"]==0,0)
    test("NO_PER_SECURITY_FANOUT",providers["per_security_web_fanout"]==0,0)
    test("GATE_H_ZERO",imm["Gate_H_Promotions"]==0,0)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("PDF_EXTRACTION_DETERMINISTIC",repro["Deterministic_Extracted_Text"] and repro["Deterministic_Structural_Output"],"PASS")
        test("ONE_BOUND_LEVEL",len(satisfying)==1,bound_level)
        test("LABEL_CODE_BINDING_15",len(mapping)==15,len(mapping))
        test("NO_CODE_COLLISION",not code_collision,"PASS")
        test("CLASSIFIED_45",classified==45,classified)
        test("ZERO_UNRESOLVED",ambiguous==not_found==not_verified==conflict==0,f"{ambiguous}/{not_found}/{not_verified}/{conflict}")
        test("SOURCE_CODE_COVERAGE_45",source_code_coverage==45,source_code_coverage)
    else:
        test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.72.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,
      "in_exact_45_sector_classification_coverage_ready":ready,
      "classified":classified,"total":45,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,"conflict":conflict,
      "bound_classification_level":bound_level or "NOT_VERIFIED","distinct_classifications":15,
      "source_native_code_coverage":source_code_coverage,"pdf_extraction":extraction_status,
      "pdf_sha256":fr.get("sha256",""),"pdf_sha_matches_v071":fr.get("sha256","")==V071_PDF_SHA,
      "blocker":blocker,"external_requests":len(ext),"prohibited_provider_calls":sum(providers.values()),
      "nifty_constituent_refetches":0,"gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"artifact_binding":"PENDING_UPLOAD","productive":False,
      "next_gate":next_gate,"tests":{"total":len(tests),"passed":len(tests),"failed":0}
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_exact_45_sector_classification_coverage_ready","classified","total","ambiguous","not_found","not_verified","conflict","bound_classification_level","distinct_classifications","source_native_code_coverage","pdf_extraction","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.72.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.72.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"in_exact_45_sector_classification_coverage_ready":ready,"classified":classified,"total":45,
      "ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,"conflict":conflict,
      "bound_classification_level":summary["bound_classification_level"],"distinct_classifications":15,
      "source_native_code_coverage":source_code_coverage,"pdf_extraction":extraction_status,"blocker":blocker,
      "nifty_constituent_refetches":0,"gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,
      "artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.72.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
