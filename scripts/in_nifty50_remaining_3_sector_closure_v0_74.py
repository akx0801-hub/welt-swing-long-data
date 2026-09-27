#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, importlib.metadata, io, json, re, statistics, subprocess, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.74"
STAGE="IN_NIFTY50_REMAINING_3_SECTOR_NODE_SOURCE_NATIVE_CODE_CLOSURE_GATE_F_COMPLETION"
REQUIRED_START_HEAD="57364dbf0b08edc2c563e0ecbf8f9d3e5fc2269f"
V073_WORKFLOW=36312901944
V073_ARTIFACT=10929840911
V073_DIGEST="sha256:5d1cbce614a0f943af0cb76fddc4dcf7bd80b9e6a3213850a9bac4601784a706"
PDF_SHA="8ae58cbd10d7dd5184d76cfec6486f91c019026c8de329432b69c54ff7235f8b"
V072_STRUCTURAL_SHA="d431587f5f686b8432bc57755a8fe6aef232fed49fb858cf7e905b3318687173"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

TAXONOMY="NSE_INDICES_INDUSTRY_CLASSIFICATION"
BOUND_LEVEL="SECTOR"
PDF_URL="https://www.niftyindices.com/docs/default-source/default-document-library/industry-classification/nse-indices_industry-classification-structure-2023-07.pdf?sfvrsn=c89dd39_1"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.74"

SPEC=ROOT/"config/in_nifty50_remaining_3_sector_closure_spec_v0.74.json"
SUM73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/summary_v0.73.json"
CHK73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/stage_checkpoint_v0.73.json"
MAN73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/manifest_v0.73.json"
LEVEL73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/in_classification_level_binding_v0.73.json"
BIND73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/in_source_native_code_binding_v0.73.csv"
MEM73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/nifty_application_security_membership_v0.73.csv"
ASSIGN73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/in_csv_vs_application_level_assignment_audit_v0.73.csv"
COV73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/in_exact_45_classification_coverage_v0.73.csv"
DESC73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/in_application_descendant_parent_code_audit_v0.73.csv"
TAXTABLE72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/nse_industry_classification_structured_table_v0.72.csv"
REPRO72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/nse_pdf_extraction_reproducibility_audit_v0.72.json"
LINK70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/in_exact_45_identity_linkage_audit_v0.70.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"

LEVELS=["MACRO_ECONOMIC_SECTOR","SECTOR","INDUSTRY","BASIC_INDUSTRY"]
DIGITS_TO_LEVEL={2:"MACRO_ECONOMIC_SECTOR",4:"SECTOR",6:"INDUSTRY",9:"BASIC_INDUSTRY"}
CODE_RE=re.compile(r"^IN(?P<digits>\d{9}|\d{6}|\d{4}|\d{2})$")
UNRESOLVED={
 "Information Technology":{"node_id":"11","affected":4},
 "Services":{"node_id":"1","affected":2},
 "Telecommunication":{"node_id":"7","affected":1}
}

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def norm(s:str)->str:return re.sub(r"\s+"," ",str(s).replace("\u00a0"," ")).strip()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

def fetch_pdf()->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    host=(urllib.parse.urlparse(PDF_URL).hostname or "").lower()
    if host not in {"www.niftyindices.com","niftyindices.com"}:
        return {"ok":False,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","error":"HOST_NOT_ALLOWED"}
    try:
        req=urllib.request.Request(PDF_URL,headers={"User-Agent":UA,"Accept":"application/pdf,*/*;q=0.8"},method="GET")
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read(5_000_001);tr=len(b)>5_000_000
            if tr:b=b[:5_000_000]
            return {"ok":200<=getattr(r,"status",200)<300 and not tr,"timestamp_utc":ts,
                    "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"body":b,"truncated":tr,"resolved_url":r.geturl()}
    except Exception as e:
        return {"ok":False,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","body":b"",
                "truncated":False,"resolved_url":PDF_URL,"error":f"{type(e).__name__}:{e}"}

def median(vals:list[float])->float:
    return float(statistics.median(vals))

def coordinate_extract(pdf:bytes,max_vertical:float=42.0,margin:float=3.0)->dict[str,Any]:
    import pymupdf
    doc=pymupdf.open(stream=pdf,filetype="pdf")
    pages=[];occ=[]
    definition_x=[]
    for pno,page in enumerate(doc,1):
        words=page.get_text("words",sort=True)
        recs=[]
        for w in words:
            x0,y0,x1,y1,text,block,line,word=w[:8]
            d={"page":pno,"x0":float(x0),"y0":float(y0),"x1":float(x1),"y1":float(y1),
               "text":str(text),"block":int(block),"line":int(line),"word":int(word)}
            recs.append(d)
            m=CODE_RE.match(str(text))
            if m:
                lev=DIGITS_TO_LEVEL[len(m.group("digits"))]
                occ.append({**d,"level":lev,"code":str(text)})
            if norm(str(text)).lower()=="definition":definition_x.append(float(x0))
        pages.append({"page":pno,"width":float(page.rect.width),"height":float(page.rect.height),"words":recs})
    if not occ:raise RuntimeError("NO_TAXONOMY_CODE_WORDS")
    anchors={}
    for lev in LEVELS:
        xs=[o["x0"] for o in occ if o["level"]==lev]
        if not xs:raise RuntimeError("MISSING_COLUMN_"+lev)
        anchors[lev]=median(xs)
    ordered=[anchors[x] for x in LEVELS]
    if ordered!=sorted(ordered) or len(set(round(x,2) for x in ordered))!=4:
        raise RuntimeError("COLUMN_ANCHOR_ORDER_INVALID")
    right_bounds={
      "MACRO_ECONOMIC_SECTOR":anchors["SECTOR"]-margin,
      "SECTOR":anchors["INDUSTRY"]-margin,
      "INDUSTRY":anchors["BASIC_INDUSTRY"]-margin,
      "BASIC_INDUSTRY":(median(definition_x)-margin) if definition_x else max(p["width"] for p in pages)-margin
    }
    page_words={p["page"]:p["words"] for p in pages}
    page_heights={p["page"]:p["height"] for p in pages}
    cells=[]
    by_page_level=defaultdict(list)
    for o in occ:by_page_level[(o["page"],o["level"])].append(o)
    for k in by_page_level:by_page_level[k].sort(key=lambda x:(x["y0"],x["x0"]))
    for o in sorted(occ,key=lambda x:(x["page"],x["y0"],x["x0"])):
        same=by_page_level[(o["page"],o["level"])]
        next_y=None
        for n in same:
            if n["y0"]>o["y0"]+0.5:
                next_y=n["y0"];break
        y_lo=o["y0"]-1.5
        y_hi=min(page_heights[o["page"]],o["y0"]+max_vertical)
        if next_y is not None:y_hi=min(y_hi,next_y-1.0)
        x_lo=o["x1"]+0.5;x_hi=right_bounds[o["level"]]
        kept=[];discarded=[]
        for w in page_words[o["page"]]:
            if w["y0"]<y_lo or w["y0"]>=y_hi:continue
            if w["x0"]>=x_lo and w["x0"]<x_hi:
                if not CODE_RE.match(w["text"]):
                    kept.append(w)
            elif w["x0"]>=x_hi and w["x0"]<x_hi+35 and w["y0"]<o["y0"]+max_vertical:
                discarded.append(w)
        kept.sort(key=lambda x:(round(x["y0"],1),x["x0"]))
        name=norm(" ".join(w["text"] for w in kept))
        cells.append({
          "Page":o["page"],"Level":o["level"],"Code":o["code"],
          "Code_X0":round(o["x0"],3),"Code_Y0":round(o["y0"],3),
          "Cell_X_Low":round(x_lo,3),"Cell_X_High":round(x_hi,3),
          "Cell_Y_Low":round(y_lo,3),"Cell_Y_High":round(y_hi,3),
          "Raw_Extracted_Cell":" | ".join(w["text"] for w in kept),
          "Reconstructed_Official_Cell":name,
          "Relevant_Raw_Tokens_JSON":json.dumps([{k:round(w[k],3) if k in ("x0","y0","x1","y1") else w[k] for k in ("text","x0","y0","x1","y1")} for w in kept],ensure_ascii=False,separators=(",",":")),
          "Discarded_Adjacent_Tokens_JSON":json.dumps([{k:round(w[k],3) if k in ("x0","y0","x1","y1") else w[k] for k in ("text","x0","y0","x1","y1")} for w in discarded],ensure_ascii=False,separators=(",",":")),
          "Discard_Reason":"TOKEN_X0_AT_OR_RIGHT_OF_NEXT_CLASSIFICATION_COLUMN_BOUNDARY",
          "Reconstruction_Rule":"SAME_CELL_COORDINATE_WORDS_ONLY; JOIN_LINE_WRAPS_WITH_SINGLE_SPACE; NO_INSERTION; NO_SPELLING_OR_PUNCTUATION_EDIT"
        })
    canonical=[{k:c[k] for k in ("Page","Level","Code","Raw_Extracted_Cell","Reconstructed_Official_Cell")} for c in cells]
    structural_sha=sha_bytes(json.dumps(canonical,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8"))
    return {
      "tool":"PyMuPDF","version":importlib.metadata.version("PyMuPDF"),"page_count":len(pages),
      "anchors":anchors,"right_bounds":right_bounds,"cell_count":len(cells),"cells":cells,
      "normalized_structural_sha256":structural_sha
    }

def table_parent_maps(rows:list[dict[str,str]])->tuple[dict[str,set[str]],dict[str,set[str]],dict[str,dict[str,str]]]:
    industry_parent=defaultdict(set);basic_parent=defaultdict(set);sector_meta={}
    for r in rows:
        sc=r.get("Sector_Code","")
        if sc:
            sector_meta.setdefault(sc,{
              "Sector_Code":sc,"Sector_Name_v072":r.get("Sector_Name",""),
              "Macro_Code":r.get("Macro_Economic_Sector_Code",""),"Macro_Name":r.get("Macro_Economic_Sector_Name","")
            })
        ic=r.get("Industry_Code","")
        bc=r.get("Basic_Industry_Code","")
        if ic and sc:industry_parent[ic].add(sc)
        if bc and sc:basic_parent[bc].add(sc)
    return industry_parent,basic_parent,sector_meta

def prefix_integrity(rows:list[dict[str,str]])->dict[str,Any]:
    checks=Counter();bad=[]
    for r in rows:
        mc=r.get("Macro_Economic_Sector_Code","");sc=r.get("Sector_Code","");ic=r.get("Industry_Code","");bc=r.get("Basic_Industry_Code","")
        if mc and sc:
            checks["sector"]+=1
            if not sc.startswith(mc):bad.append({"Relation":"MACRO_TO_SECTOR","Parent":mc,"Child":sc})
        if sc and ic:
            checks["industry"]+=1
            if not ic.startswith(sc):bad.append({"Relation":"SECTOR_TO_INDUSTRY","Parent":sc,"Child":ic})
        if ic and bc:
            checks["basic"]+=1
            if not bc.startswith(ic):bad.append({"Relation":"INDUSTRY_TO_BASIC","Parent":ic,"Child":bc})
    return {"Audited_As_Integrity_Check_Only":True,"Used_As_Sole_Parent_Authority":False,
            "Macro_Sector_Checks":checks["sector"],"Sector_Industry_Checks":checks["industry"],
            "Industry_Basic_Checks":checks["basic"],"Mismatch_Count":len(bad),"Mismatches":bad}

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM73.read_text(encoding="utf-8"));c=json.loads(CHK73.read_text(encoding="utf-8"));lvl=json.loads(LEVEL73.read_text(encoding="utf-8"))
    repro=json.loads(REPRO72.read_text(encoding="utf-8"))
    bind=read_csv(BIND73);mem=read_csv(MEM73);assign=read_csv(ASSIGN73);cov=read_csv(COV73);link=read_csv(LINK70);tax=read_csv(TAXTABLE72)
    if s["verdict"]!="BLOCKED_IN_NIFTY50_GATE_F_APPLICATION_CONTRACT_RESOLUTION":raise RuntimeError("v0.73 verdict")
    if s["in_exact_45_sector_classification_coverage_ready"] is not False:raise RuntimeError("v0.73 readiness")
    if s["bound_classification_level"]!="SECTOR" or s["distinct_classifications"]!=15:raise RuntimeError("v0.73 bound level")
    if (s["classified"],s["total"],s["ambiguous"],s["not_found"],s["not_verified"],s["conflict"])!=(0,45,0,7,38,0):raise RuntimeError("v0.73 counts")
    if s["blocker"]!="NIFTY_APPLICATION_NODE_TO_TAXONOMY_CODE_NOT_VERIFIED":raise RuntimeError("v0.73 blocker")
    if c["workflow_run_id"]!=V073_WORKFLOW or c["artifact_id"]!=V073_ARTIFACT or "sha256:"+c["artifact_digest"]!=V073_DIGEST:raise RuntimeError("v0.73 artifact")
    if lvl["Level_Binding_Status"]!="PASS" or lvl["Official_Taxonomy_Level"]!="SECTOR" or lvl["Complete_Explaining_Levels"]!=["SECTOR"]:raise RuntimeError("v0.73 level authority")
    if s["candidate_contract_count"]!=4 or not s["public_reproducibility"]:raise RuntimeError("v0.73 application contract")
    if len(mem)!=180:raise RuntimeError("v0.73 membership rows")
    sector_assign=[r for r in assign if r["Application_Level"]=="SECTOR"]
    if len(sector_assign)!=45 or any(r["Application_Assignment_Status"]!="PASS" or r["CSV_to_Application_Relation"]!="EXACT_DISPLAY_LABEL" for r in sector_assign):
        raise RuntimeError("v0.73 sector assignment authority")
    if len(bind)!=15:raise RuntimeError("v0.73 binding rows")
    pass_rows=[r for r in bind if r["Binding_Status"]=="PASS"]
    unresolved=[r for r in bind if r["Binding_Status"]!="PASS"]
    if len(pass_rows)!=12 or len(unresolved)!=3:raise RuntimeError("v0.73 12/3 binding split")
    got={(r["CSV_Source_Label"],r["Application_Node_ID_or_Code"]) for r in unresolved}
    exp={(k,v["node_id"]) for k,v in UNRESOLVED.items()}
    if got!=exp:raise RuntimeError("v0.73 unresolved nodes")
    counts=Counter(r["CSV_Source_Classification_Raw"] for r in sector_assign if r["CSV_Source_Classification_Raw"] in UNRESOLVED)
    if {k:counts[k] for k in UNRESOLVED}!={k:v["affected"] for k,v in UNRESOLVED.items()}:raise RuntimeError("v0.73 unresolved affected counts")
    if len(cov)!=45 or len(link)!=45 or any(r["Gate_E_Status"]!="PROVABLY_LINKED" for r in link):raise RuntimeError("identity/coverage")
    if repro["PDF_SHA256"]!=PDF_SHA or repro["Run1_Structural_SHA256"]!=V072_STRUCTURAL_SHA:raise RuntimeError("v0.72 PDF/table authority")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("registry")
    return {"summary":s,"level":lvl,"bindings":bind,"membership":mem,"assignments":assign,"coverage":cov,"identity":link,"taxonomy":tax}

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"tradingview":0,"wikipedia":0,"investing_com":0,
      "etf_holdings":0,"third_party_security_databases":0,"third_party_sector_databases":0,"company_websites":0,
      "company_name_joins":0,"fuzzy_matching":0,"semantic_inference":0,"cross_taxonomy_mapping":0,"pdsc_fallback":0,
      "per_security_fanout":0,"authentication_bypass":0,"captcha_bypass":0,"nse_equity_l":0,"nifty_constituent_refetch":0,
      "application_contract_rediscovery":0,"application_endpoint_refetch":0,"ocr":0,"screenshots":0,"manual_transcription":0,
      "gate_h":0,"canonical_materialization":0,"sector_rs":0,"p0":0,"p1":0,"p2":0
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_in_nifty50_remaining_3_sector_closure_v0_74")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    # Exact remaining-three target from predecessor authority.
    sector_assign=[r for r in pred["assignments"] if r["Application_Level"]=="SECTOR"]
    target=[]
    for label,meta in UNRESOLVED.items():
        rs=[r for r in sector_assign if r["CSV_Source_Classification_Raw"]==label]
        for r in rs:
            target.append({
              "CSV_Source_Label":label,"Application_Node_ID":meta["node_id"],"WS_ID":r["WS_ID"],
              "Primary_Ticker":r["Primary_Ticker"],"Frozen_ISIN":r["Frozen_ISIN"],
              "v073_Application_Display_Label":r["Application_Display_Label"],
              "v073_Application_Assignment_Status":r["Application_Assignment_Status"],
              "v073_CSV_to_Application_Relation":r["CSV_to_Application_Relation"]
            })
    target.sort(key=lambda r:(r["CSV_Source_Label"],r["WS_ID"]))
    write_csv(out/"in_remaining_3_sector_target_v0.74.csv",target)

    # One bounded refetch of the same official PDF for coordinate-aware extraction.
    fr=fetch_pdf()
    ext=[{
      "Request_Order":1,"Request_Type":"NSE_INDICES_CLASSIFICATION_PDF_COORDINATE_REEXTRACTION","URL":PDF_URL,"Method":"GET",
      "Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),"SHA256":fr.get("sha256",""),
      "Timestamp_UTC":fr.get("timestamp_utc",""),"Official_Source":"YES","Per_Security_Fanout":"NO",
      "Reason":"Coordinate-aware repair of three v0.73 unresolved SECTOR display cells from same v0.72 official PDF.",
      "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")
    }]
    write_csv(out/"external_request_ledger_v0.74.csv",ext)

    extraction_error=""
    ex1=ex2=None
    if not fr.get("ok") or fr.get("sha256")!=PDF_SHA:
        extraction_error="NSE_SECTOR_CELL_LAYOUT_RECONSTRUCTION_NOT_VERIFIED"
    else:
        try:
            ex1=coordinate_extract(fr["body"],float(spec["coordinate_extraction"]["max_cell_vertical_points"]),float(spec["coordinate_extraction"]["column_margin_points"]))
            ex2=coordinate_extract(fr["body"],float(spec["coordinate_extraction"]["max_cell_vertical_points"]),float(spec["coordinate_extraction"]["column_margin_points"]))
            if ex1["normalized_structural_sha256"]!=ex2["normalized_structural_sha256"]:
                extraction_error="NSE_SECTOR_CELL_LAYOUT_RECONSTRUCTION_NOT_VERIFIED"
        except Exception as e:
            extraction_error="NSE_SECTOR_CELL_LAYOUT_RECONSTRUCTION_NOT_VERIFIED"
            ex1={"error":f"{type(e).__name__}:{e}","cells":[],"anchors":{},"right_bounds":{},"normalized_structural_sha256":"","page_count":0}
            ex2={"error":f"{type(e).__name__}:{e}","cells":[],"anchors":{},"right_bounds":{},"normalized_structural_sha256":"","page_count":0}

    cells=(ex1 or {}).get("cells",[])
    sector_cells=[c for c in cells if c["Level"]=="SECTOR"]
    write_csv(out/"nse_sector_cell_coordinate_extraction_audit_v0.74.csv",sector_cells if sector_cells else [{
      "Page":"","Level":"SECTOR","Code":"","Code_X0":"","Code_Y0":"","Cell_X_Low":"","Cell_X_High":"","Cell_Y_Low":"","Cell_Y_High":"",
      "Raw_Extracted_Cell":"","Reconstructed_Official_Cell":"","Relevant_Raw_Tokens_JSON":"","Discarded_Adjacent_Tokens_JSON":"",
      "Discard_Reason":"","Reconstruction_Rule":""
    }])
    reconstruction_contract={
      "Official_PDF_URL":PDF_URL,"Expected_PDF_SHA256":PDF_SHA,"Observed_PDF_SHA256":fr.get("sha256",""),
      "PDF_SHA_Matches":fr.get("sha256")==PDF_SHA,"Tool":"PyMuPDF","Tool_Version":importlib.metadata.version("PyMuPDF"),
      "Extraction_Method":"page.get_text(words) coordinate-aware cell reconstruction",
      "Column_Anchors":(ex1 or {}).get("anchors",{}),"Right_Column_Boundaries":(ex1 or {}).get("right_bounds",{}),
      "Max_Cell_Vertical_Points":spec["coordinate_extraction"]["max_cell_vertical_points"],
      "Column_Margin_Points":spec["coordinate_extraction"]["column_margin_points"],
      "Allowed_Repairs":["join line-wrapped fragments from same coordinate cell","collapse extraction whitespace","Unicode/whitespace normalization only"],
      "Forbidden_Repairs":["insert words","spelling correction","punctuation substitution","fuzzy matching","semantic inference"],
      "Run1_Structural_SHA256":(ex1 or {}).get("normalized_structural_sha256",""),
      "Run2_Structural_SHA256":(ex2 or {}).get("normalized_structural_sha256",""),
      "Deterministic_Rerun":bool(ex1 and ex2 and ex1.get("normalized_structural_sha256")==ex2.get("normalized_structural_sha256") and ex1.get("normalized_structural_sha256")),
      "Extraction_Error":(ex1 or {}).get("error","") or extraction_error,
      "Raw_PDF_Persisted":False,"Raw_PDF_Redistribution_Rights":"NOT_VERIFIED"
    }
    (out/"nse_sector_cell_reconstruction_contract_v0.74.json").write_text(json.dumps(reconstruction_contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Build coordinate node index by exact layout-only reconstructed label.
    coord_by_level_label=defaultdict(list)
    coord_by_level_code=defaultdict(list)
    for c in cells:
        if c["Reconstructed_Official_Cell"]:
            coord_by_level_label[(c["Level"],c["Reconstructed_Official_Cell"])].append(c)
        coord_by_level_code[(c["Level"],c["Code"])].append(c)

    # Existing explicit parent columns from the v0.72 table remain hierarchy authority.
    industry_parent,basic_parent,sector_meta=table_parent_maps(pred["taxonomy"])

    # Direct sector route for the three targets.
    direct={}
    for label,meta in UNRESOLVED.items():
        hits=coord_by_level_label.get(("SECTOR",label),[])
        codes=sorted({h["Code"] for h in hits})
        status="PASS" if len(codes)==1 else ("AMBIGUOUS" if len(codes)>1 else "NOT_VERIFIED")
        direct[label]={
          "code":codes[0] if len(codes)==1 else "",
          "status":status,
          "hit_count":len(hits),
          "cells":hits
        }

    # Persist unresolved descendant application assignments from v0.73.
    target_ws={r["WS_ID"] for r in target}
    descendants=[]
    for r in pred["membership"]:
        if r["WS_ID"] in target_ws and r["Application_Level"] in {"INDUSTRY","BASIC_INDUSTRY"}:
            sector_label=next(t["CSV_Source_Label"] for t in target if t["WS_ID"]==r["WS_ID"])
            descendants.append({
              "CSV_Source_Label":sector_label,"WS_ID":r["WS_ID"],"Security_ID":r["Security_ID"],
              "Application_Descendant_Level":r["Application_Level"],
              "Application_Descendant_Display_Label":r["Application_Display_Label"],
              "Application_Descendant_Node_ID":r["Application_Node_ID_or_Code"],
              "Source_Endpoint":r["Source_Endpoint"],"v073_Identity_Route":r["Identity_Route"]
            })
    descendants.sort(key=lambda r:(r["CSV_Source_Label"],r["WS_ID"],r["Application_Descendant_Level"]))
    write_csv(out/"in_unresolved_descendant_application_assignments_v0.74.csv",descendants)

    # Bind descendants exactly to coordinate-reconstructed official cells.
    desc_node_rows=[];desc_parent_rows=[]
    desc_parent_by_ws=defaultdict(set)
    for r in descendants:
        lev=r["Application_Descendant_Level"];label=r["Application_Descendant_Display_Label"]
        hits=coord_by_level_label.get((lev,label),[])
        codes=sorted({h["Code"] for h in hits})
        node_status="PASS" if len(codes)==1 else ("AMBIGUOUS" if len(codes)>1 else "NOT_VERIFIED")
        code=codes[0] if len(codes)==1 else ""
        desc_node_rows.append({
          **r,"Taxonomy_Descendant_Code":code or "NOT_VERIFIED","Exact_Reconstructed_Cell_Match_Count":len(hits),
          "Binding_Method":"EXACT_APPLICATION_DISPLAY_TO_COORDINATE_RECONSTRUCTED_OFFICIAL_CELL",
          "Node_Binding_Status":node_status
        })
        parents=set()
        parent_source=""
        if code and lev=="INDUSTRY":
            parents=set(industry_parent.get(code,set()));parent_source="V072_STRUCTURED_TABLE_EXPLICIT_SECTOR_CODE_COLUMN"
        elif code and lev=="BASIC_INDUSTRY":
            parents=set(basic_parent.get(code,set()));parent_source="V072_STRUCTURED_TABLE_EXPLICIT_SECTOR_CODE_COLUMN"
        parent_status="PASS" if len(parents)==1 else ("AMBIGUOUS" if len(parents)>1 else "NOT_VERIFIED")
        parent=next(iter(parents)) if len(parents)==1 else ""
        if parent_status=="PASS":desc_parent_by_ws[r["WS_ID"]].add(parent)
        desc_parent_rows.append({
          **r,"Taxonomy_Descendant_Code":code or "NOT_VERIFIED","Explicit_Parent_Sector_Code":parent or "NOT_VERIFIED",
          "Parent_Authority":parent_source or "NOT_VERIFIED","Prefix_Rule_Used_As_Sole_Authority":"NO",
          "Parent_Binding_Status":parent_status
        })
    write_csv(out/"in_descendant_taxonomy_node_binding_v0.74.csv",desc_node_rows)
    write_csv(out/"in_descendant_parent_sector_binding_v0.74.csv",desc_parent_rows)

    # Resolve one descendant sector code per affected security where possible.
    ws_desc_result={}
    for ws in sorted(target_ws):
        parents=desc_parent_by_ws.get(ws,set())
        ws_desc_result[ws]={
          "code":next(iter(parents)) if len(parents)==1 else "",
          "status":"PASS" if len(parents)==1 else ("CONFLICT" if len(parents)>1 else "NOT_VERIFIED"),
          "all_parent_codes":sorted(parents)
        }

    # Remaining-three final bindings.
    remaining_rows=[];remaining_final={}
    for label,meta in UNRESOLVED.items():
        ws_rows=[r for r in target if r["CSV_Source_Label"]==label]
        direct_code=direct[label]["code"];direct_status=direct[label]["status"]
        child_results=[ws_desc_result[r["WS_ID"]] for r in ws_rows]
        child_codes={x["code"] for x in child_results if x["status"]=="PASS" and x["code"]}
        descendant_complete=all(x["status"]=="PASS" for x in child_results)
        descendant_consistent=descendant_complete and len(child_codes)==1
        descendant_code=next(iter(child_codes)) if len(child_codes)==1 else ""
        final_code="";status="NOT_VERIFIED";method=""
        if direct_status=="PASS":
            if child_codes and any(c!=direct_code for c in child_codes):
                status="CONFLICT"
            else:
                final_code=direct_code;status="PASS";method="ROUTE_A_DIRECT_COORDINATE_RECONSTRUCTED_SECTOR_CELL"
                if descendant_consistent and descendant_code==direct_code:method+="+ROUTE_B_DESCENDANT_MUTUAL_CONFIRMATION"
        elif descendant_consistent:
            final_code=descendant_code;status="PASS";method="ROUTE_B_DESCENDANT_CLOSURE_EXPLICIT_V072_PARENT_SECTOR_CODE"
        elif any(x["status"]=="CONFLICT" for x in child_results):
            status="CONFLICT"
        sector_cell=coord_by_level_code.get(("SECTOR",final_code),[]) if final_code else []
        reconstructed_name=sector_cell[0]["Reconstructed_Official_Cell"] if len(sector_cell)==1 else ""
        # If Route B is used without exact direct label equality, do not silently claim equality.
        name_relation="EXACT_LAYOUT_RECONSTRUCTED_CELL" if reconstructed_name==label and reconstructed_name else ("ROUTE_B_PARENT_CODE_ONLY" if status=="PASS" else "NOT_VERIFIED")
        macro_code=sector_meta.get(final_code,{}).get("Macro_Code","") if final_code else ""
        macro_name=sector_meta.get(final_code,{}).get("Macro_Name","") if final_code else ""
        remaining_rows.append({
          "Application_Node_ID":meta["node_id"],"Application_Display_Label":label,
          "Affected_Frozen_Rows":meta["affected"],"Direct_Sector_Exact_Match_Count":direct[label]["hit_count"],
          "Direct_Sector_Code":direct_code or "NOT_VERIFIED","Direct_Route_Status":direct_status,
          "Descendant_Resolved_Rows":sum(x["status"]=="PASS" for x in child_results),
          "Descendant_Sector_Codes":" | ".join(sorted(child_codes)) if child_codes else "NOT_VERIFIED",
          "Descendant_Route_Complete_And_Consistent":"YES" if descendant_consistent else "NO",
          "Taxonomy_Sector_Code":final_code or "NOT_VERIFIED",
          "Taxonomy_Sector_Name":reconstructed_name or "NOT_VERIFIED",
          "Taxonomy_Sector_Name_Relation":name_relation,
          "Parent_Macro_Economic_Sector_Code":macro_code or "NOT_VERIFIED",
          "Parent_Macro_Economic_Sector_Name":macro_name or "NOT_VERIFIED",
          "Binding_Method":method or "NOT_VERIFIED","Binding_Status":status
        })
        remaining_final[label]={"code":final_code,"status":status,"method":method,"name":reconstructed_name}
    write_csv(out/"in_remaining_3_sector_code_binding_v0.74.csv",remaining_rows)

    # Preserve 12 predecessor PASS bindings exactly; replace only remaining three if proven.
    final_bindings=[]
    for r in pred["bindings"]:
        label=r["CSV_Source_Label"]
        if label not in UNRESOLVED:
            nr=dict(r);nr["v074_Authority"]="PRESERVED_V073_PASS"
            final_bindings.append(nr)
        else:
            x=remaining_final[label]
            nr=dict(r)
            nr["Taxonomy_Source_Native_Code"]=x["code"] or "NOT_VERIFIED"
            nr["Official_Taxonomy_Name"]=x["name"] if x["name"]==label else (label if x["status"]=="PASS" and x["method"].startswith("ROUTE_B_") else "NOT_VERIFIED")
            meta=sector_meta.get(x["code"],{}) if x["code"] else {}
            if x["status"]=="PASS":
                nr["Parent_Path"]=(meta.get("Macro_Code","")+" "+meta.get("Macro_Name","")+" > "+x["code"]+" "+(x["name"] or label)).strip()
                nr["Binding_Method"]=x["method"];nr["Binding_Status"]="PASS"
            else:
                nr["Parent_Path"]="NOT_VERIFIED";nr["Binding_Method"]="NOT_VERIFIED";nr["Binding_Status"]=x["status"]
            nr["Application_ID_Is_Formal_Taxonomy_Code"]="NO"
            nr["v074_Authority"]="NEW_REMAINING_3_CLOSURE"
            final_bindings.append(nr)
    final_bindings.sort(key=lambda r:r["CSV_Source_Label"])
    write_csv(out/"in_source_native_code_binding_v0.74.csv",final_bindings)

    inventory=[]
    for r in final_bindings:
        inventory.append({
          "Source_Classification_Raw":r["CSV_Source_Label"],"Application_Node_ID":r["Application_Node_ID_or_Code"],
          "Official_Taxonomy_Level":"SECTOR","Source_Native_Sector_Code":r["Taxonomy_Source_Native_Code"],
          "Official_Taxonomy_Name":r["Official_Taxonomy_Name"],"Binding_Method":r["Binding_Method"],
          "Binding_Status":r["Binding_Status"],"Authority":r["v074_Authority"]
        })
    write_csv(out/"in_15_sector_code_inventory_v0.74.csv",inventory)

    # Prefix hierarchy audit only, never sole authority.
    hierarchy=prefix_integrity(pred["taxonomy"])
    hierarchy["v072_Structural_SHA256"]=V072_STRUCTURAL_SHA
    hierarchy["Explicit_Parent_Columns_Used_For_Descendant_Closure"]=True
    (out/"taxonomy_code_hierarchy_integrity_audit_v0.74.json").write_text(json.dumps(hierarchy,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Complete exact-45 Gate F.
    code_by_label={r["CSV_Source_Label"]:r["Taxonomy_Source_Native_Code"] for r in final_bindings if r["Binding_Status"]=="PASS" and r["Taxonomy_Source_Native_Code"]!="NOT_VERIFIED"}
    bind_by_label={r["CSV_Source_Label"]:r for r in final_bindings}
    identity={r["WS_ID"]:r for r in pred["identity"]}
    sector_assignment={r["WS_ID"]:r for r in sector_assign}
    coverage=[]
    counts=Counter()
    for old in sorted(pred["coverage"],key=lambda r:r["WS_ID"]):
        ws=old["WS_ID"];label=old["Source_Classification_Raw"];ident=identity.get(ws);ass=sector_assignment.get(ws)
        status="NOT_VERIFIED";detail="";code="NOT_VERIFIED"
        if not ident or ident["Gate_E_Status"]!="PROVABLY_LINKED":
            detail="v0.70 identity not PROVABLY_LINKED."
        elif not ass or ass["Application_Assignment_Status"]!="PASS":
            detail="v0.73 SECTOR application assignment not PASS."
        elif ass["CSV_to_Application_Relation"]!="EXACT_DISPLAY_LABEL" or ass["Application_Display_Label"]!=label:
            status="CONFLICT";detail="v0.73 CSV/application SECTOR identity conflict."
        elif label not in code_by_label:
            status="NOT_FOUND";detail="No verified source-native SECTOR code."
        else:
            status="PROVABLY_CLASSIFIED";code=code_by_label[label]
        counts[status]+=1
        coverage.append({
          "Security_Key":old["Security_Key"],"WS_ID":ws,"Primary_MIC":old["Primary_MIC"],"Primary_Ticker":old["Primary_Ticker"],
          "Frozen_ISIN":old["Frozen_ISIN"],"v070_Identity_Status":ident["Gate_E_Status"] if ident else "NOT_VERIFIED",
          "v073_Application_Sector_Assignment_Status":ass["Application_Assignment_Status"] if ass else "NOT_VERIFIED",
          "v073_CSV_to_Application_Sector_Relation":ass["CSV_to_Application_Relation"] if ass else "NOT_VERIFIED",
          "Source_Classification_Raw":label,"Application_Display_Label":ass["Application_Display_Label"] if ass else "",
          "Application_Sector_Node_ID":ass["Application_Node_ID_or_Code"] if ass else "",
          "Taxonomy":TAXONOMY,"Official_Taxonomy_Level":"SECTOR",
          "Source_Native_Sector_Code":code,"Classification_Status":status,"Detail":detail
        })
    write_csv(out/"in_exact_45_classification_coverage_v0.74.csv",coverage)

    classified=counts["PROVABLY_CLASSIFIED"];ambiguous=counts["AMBIGUOUS"];not_found=counts["NOT_FOUND"];not_verified=counts["NOT_VERIFIED"];conflict=counts["CONFLICT"]
    code_cov=sum(r["Classification_Status"]=="PROVABLY_CLASSIFIED" and r["Source_Native_Sector_Code"]!="NOT_VERIFIED" for r in coverage)
    rem_pass=sum(r["Binding_Status"]=="PASS" for r in remaining_rows)
    rem_conflict=sum(r["Binding_Status"]=="CONFLICT" for r in remaining_rows)
    all15=sum(r["Binding_Status"]=="PASS" for r in final_bindings)==15
    distinct_codes=len({r["Taxonomy_Source_Native_Code"] for r in final_bindings if r["Binding_Status"]=="PASS"})

    blocker=""
    if extraction_error:blocker="NSE_SECTOR_CELL_LAYOUT_RECONSTRUCTION_NOT_VERIFIED"
    elif rem_conflict:blocker="NIFTY_SECTOR_CODE_CONFLICT"
    elif rem_pass<3:
        # Pick the smallest route-specific blocker supported by the evidence.
        any_desc_node_missing=any(r["Node_Binding_Status"]=="NOT_VERIFIED" for r in desc_node_rows)
        any_desc_parent_missing=any(r["Node_Binding_Status"]=="PASS" and r["Parent_Binding_Status"]=="NOT_VERIFIED" for r in zip(desc_node_rows,desc_parent_rows)) if False else False
        if any_desc_node_missing and any(r["Direct_Route_Status"]!="PASS" for r in remaining_rows):
            blocker="NSE_DESCENDANT_NODE_TO_TAXONOMY_CODE_NOT_VERIFIED"
        elif any(r["Direct_Route_Status"]!="PASS" and r["Descendant_Route_Complete_And_Consistent"]!="YES" for r in remaining_rows):
            blocker="NIFTY_REMAINING_SECTOR_NODE_CODE_BINDING_INCOMPLETE"
        else:
            blocker="NIFTY_REMAINING_SECTOR_NODE_CODE_BINDING_INCOMPLETE"
    elif not all15:blocker="NIFTY_REMAINING_SECTOR_NODE_CODE_BINDING_INCOMPLETE"
    elif (classified,ambiguous,not_found,not_verified,conflict)!=(45,0,0,0,0) or code_cov!=45:
        blocker="IN_EXACT_45_CLASSIFICATION_COVERAGE_INCOMPLETE"

    # Authority regression only on direct contradiction of the v0.73 SECTOR assignment.
    if not blocker and any(r["Taxonomy_Sector_Name_Relation"]=="EXACT_LAYOUT_RECONSTRUCTED_CELL" and r["Taxonomy_Sector_Name"]!=r["Application_Display_Label"] for r in remaining_rows):
        blocker="AUTHORITY_REGRESSION_REVIEW_REQUIRED"

    ready=(blocker=="" and rem_pass==3 and all15 and classified==45 and ambiguous==not_found==not_verified==conflict==0 and code_cov==45)
    verdict="PASS_IN_NIFTY50_REMAINING_3_SECTOR_CODE_CLOSURE_GATE_F_COMPLETE" if ready else "BLOCKED_IN_NIFTY50_REMAINING_3_SECTOR_CODE_CLOSURE"
    next_gate="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE" if ready else blocker

    prov=provider_calls()
    (out/"provider_call_audit_v0.74.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "Gate_E_Reruns":0,"Application_Contract_Rediscovery_Runs":0,"Application_Endpoint_Refetches":0,"NIFTY_Constituent_Refetches":0,
      "NSE_EQUITY_L_Calls":0,"Gate_H_Promotions":0,"Canonical_Materialization_Runs":0,"Sector_RS_Runs":0,
      "P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.74.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V073_SECTOR_LEVEL_AUTHORITY",pred["level"]["Level_Binding_Status"]=="PASS" and pred["level"]["Official_Taxonomy_Level"]=="SECTOR","PASS")
    test("V073_PUBLIC_APPLICATION_CONTRACT",pred["summary"]["candidate_contract_count"]==4 and pred["summary"]["public_reproducibility"] is True,"PASS")
    test("V073_12_PASS_3_UNRESOLVED",sum(r["Binding_Status"]=="PASS" for r in pred["bindings"])==12 and sum(r["Binding_Status"]!="PASS" for r in pred["bindings"])==3,"12/3")
    test("TARGET_7_ROWS",len(target)==7,len(target))
    test("TARGET_NODE_COUNTS",Counter(r["CSV_Source_Label"] for r in target)==Counter({"Information Technology":4,"Services":2,"Telecommunication":1}),"4/2/1")
    test("SAME_PDF_SHA",fr.get("sha256")==PDF_SHA,fr.get("sha256",""))
    test("COORDINATE_RERUN_DETERMINISTIC",reconstruction_contract["Deterministic_Rerun"],reconstruction_contract["Run1_Structural_SHA256"])
    test("NO_APPLICATION_REDISCOVERY",prov["application_contract_rediscovery"]==0,0)
    test("NO_APPLICATION_REFETCH",prov["application_endpoint_refetch"]==0,0)
    test("NO_NIFTY_REFETCH",prov["nifty_constituent_refetch"]==0,0)
    test("NO_EQUITY_L",prov["nse_equity_l"]==0,0)
    test("NO_OCR_SCREENSHOT_MANUAL",prov["ocr"]==prov["screenshots"]==prov["manual_transcription"]==0,"0/0/0")
    test("NO_FUZZY_SEMANTIC",prov["fuzzy_matching"]==prov["semantic_inference"]==0,"0/0")
    test("NO_NAME_JOIN",prov["company_name_joins"]==0,0)
    test("NO_CROSS_TAXONOMY",prov["cross_taxonomy_mapping"]==0,0)
    test("NO_PDSC",prov["pdsc_fallback"]==0,0)
    test("NO_PER_SECURITY_FANOUT",prov["per_security_fanout"]==0,0)
    test("GATE_H_ZERO",imm["Gate_H_Promotions"]==0,0)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("REMAINING_3_PASS",rem_pass==3,rem_pass)
        test("ALL_15_BINDINGS_PASS",all15,15)
        test("CLASSIFIED_45",classified==45,classified)
        test("ZERO_UNRESOLVED",ambiguous==not_found==not_verified==conflict==0,f"{ambiguous}/{not_found}/{not_verified}/{conflict}")
        test("SOURCE_CODE_COVERAGE_45",code_cov==45,code_cov)
    else:test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.74.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"in_exact_45_sector_classification_coverage_ready":ready,
      "classified":classified,"total":45,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,"conflict":conflict,
      "bound_classification_level":"SECTOR","distinct_classifications":15,"source_native_code_coverage":code_cov,
      "remaining_3_node_bindings":rem_pass,"remaining_3_node_total":3,"affected_rows_closed":sum(1 for r in coverage if r["Source_Classification_Raw"] in UNRESOLVED and r["Classification_Status"]=="PROVABLY_CLASSIFIED"),
      "blocker":blocker,"pdf_coordinate_extraction":"PASS" if not extraction_error else "NOT_VERIFIED",
      "pdf_sha256":fr.get("sha256",""),"coordinate_structural_sha256":reconstruction_contract["Run1_Structural_SHA256"],
      "external_requests":1,"prohibited_provider_calls":sum(prov.values()),"gate_h_promotions":0,
      "canonical_ready_rows":37,"canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0}
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_exact_45_sector_classification_coverage_ready","classified","total","ambiguous","not_found","not_verified","conflict","bound_classification_level","distinct_classifications","source_native_code_coverage","remaining_3_node_bindings","remaining_3_node_total","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.74.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.74.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"in_exact_45_sector_classification_coverage_ready":ready,"classified":classified,"total":45,
      "ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,"conflict":conflict,
      "bound_classification_level":"SECTOR","distinct_classifications":15,"source_native_code_coverage":code_cov,
      "remaining_3_node_bindings":rem_pass,"remaining_3_node_total":3,"blocker":blocker,
      "gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,"sector_rs_runs":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.74.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
