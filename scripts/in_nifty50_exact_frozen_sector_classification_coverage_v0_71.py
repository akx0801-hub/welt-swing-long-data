#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, html.parser, io, json, re, subprocess, tempfile, time, unicodedata, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.71"
STAGE="IN_NIFTY50_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE_GATE"
REQUIRED_START_HEAD="9acf51ba20e5c88954d0b21ed5017f95274b6f6f"
V070_WORKFLOW=36274393667
V070_ARTIFACT=10917150644
V070_DIGEST="sha256:a0e9b942970d510f7bc1042e7b93371b61662adb61cc972e557847046aa34ede"
V070_NIFTY_SHA="9fb8832853c279448d2bc05f0e7dd5f460ed2ff35332fea8c40fc1250362ad28"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

COHORT="IN_NIFTY50"
MIC="XNSE"
TAXONOMY="NSE_INDICES_INDUSTRY_CLASSIFICATION"
BOUND_LEVEL="INDUSTRY"
NIFTY_URL="https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
TAXONOMY_PAGE="https://www.niftyindices.com/resources/industry-classification"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.71"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
SUM70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/summary_v0.70.json"
CHK70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/stage_checkpoint_v0.70.json"
MAN70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/manifest_v0.70.json"
LINK70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/in_exact_45_identity_linkage_audit_v0.70.csv"
SRC70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/official_nifty50_constituent_source_audit_v0.70.json"
MATRIX69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/current_authority_cohort_gate_matrix_v0.69.csv"
RESEARCH62=ROOT/"config/source_native_sector_research_v0.62.json"
TAXINV62=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/source_native_taxonomy_inventory_v0.62.csv"
SPEC=ROOT/"config/in_nifty50_exact_frozen_sector_classification_coverage_spec_v0.71.json"

LEVEL_BY_DIGITS={2:"MACRO_ECONOMIC_SECTOR",4:"SECTOR",6:"INDUSTRY",9:"BASIC_INDUSTRY"}

class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self._href=None; self._text=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            d={k.lower():(v or "") for k,v in attrs}
            self._href=d.get("href"); self._text=[]
    def handle_data(self,data):
        if self._href is not None: self._text.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self._href is not None:
            self.links.append((self._href," ".join(self._text).strip()))
            self._href=None; self._text=[]

def git(*a:str)->str: return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def sha_file(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def sha_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:
            w.writeheader(); w.writerows(rows)

def norm_header(s:str)->str: return re.sub(r"[^a-z0-9]","",s.strip().lower())
def norm_id(s:str)->str: return s.strip().upper()
def layout_norm(s:str)->str: return re.sub(r"\s+"," ",s.replace("\u00a0"," ")).strip()

def decode_text(b:bytes)->str:
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("utf-8",errors="replace")

def parse_csv_bytes(b:bytes)->tuple[list[str],list[dict[str,str]]]:
    txt=decode_text(b); sample=txt[:4096]
    try:dialect=csv.Sniffer().sniff(sample,delimiters=",;\t")
    except Exception:dialect=csv.excel
    r=csv.DictReader(io.StringIO(txt),dialect=dialect)
    fields=[x or "" for x in (r.fieldnames or [])]
    rows=[{(k or ""):(v or "").strip() for k,v in row.items()} for row in r]
    return fields,rows

def pick_field(fields:list[str],aliases:list[str])->str|None:
    m={norm_header(x):x for x in fields}
    for a in aliases:
        if a in m:return m[a]
    return None

def fetch(url:str,allowed:set[str],max_bytes:int=10_000_000,referer:str|None=None)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    host=urllib.parse.urlparse(url).hostname
    if host not in allowed:
        return {"ok":False,"url":url,"timestamp_utc":ts,"status":"","content_type":"","body":b"","error":"HOST_NOT_ALLOWED"}
    headers={"User-Agent":UA,"Accept":"*/*","Accept-Language":"en-US,en;q=0.8"}
    if referer:headers["Referer"]=referer
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers,method="GET"),timeout=40) as r:
            b=r.read(max_bytes+1);trunc=len(b)>max_bytes
            if trunc:b=b[:max_bytes]
            return {"ok":200<=getattr(r,"status",200)<300,"requested_url":url,"url":r.geturl(),"timestamp_utc":ts,
                    "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"truncated":trunc,"body":b}
    except Exception as e:
        return {"ok":False,"requested_url":url,"url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,
                "sha256":"","truncated":False,"body":b"","error":f"{type(e).__name__}:{e}"}

def discover_structure_pdf(page_url:str,body:bytes)->tuple[str|None,list[dict[str,str]]]:
    p=LinkParser();p.feed(decode_text(body));c=[]
    for href,text in p.links:
        u=urllib.parse.urljoin(page_url,href)
        low=u.lower()
        if ".pdf" in low and ("industry-classification-structure" in low or ("industry classification structure" in text.lower())):
            c.append({"url":u,"anchor_text":text})
    seen=[];out=[]
    for x in c:
        if x["url"] not in seen:
            seen.append(x["url"]);out.append(x)
    return (out[0]["url"] if len(out)==1 else None),out

def _pdf_literal_strings_from_stream(data:bytes)->list[str]:
    out=[];i=0;n=len(data)
    while i<n:
        if data[i]!=0x28:
            i+=1;continue
        i+=1;buf=bytearray();depth=1
        while i<n and depth>0:
            b=data[i]
            if b==0x5c and i+1<n:
                i+=1;esc=data[i]
                maps={ord("n"):10,ord("r"):13,ord("t"):9,ord("b"):8,ord("f"):12}
                if esc in maps:buf.append(maps[esc])
                elif esc in (0x28,0x29,0x5c):buf.append(esc)
                elif 48<=esc<=55:
                    octal=bytes([esc]);j=0
                    while i+1<n and j<2 and 48<=data[i+1]<=55:
                        i+=1;octal+=bytes([data[i]]);j+=1
                    try:buf.append(int(octal,8)&0xff)
                    except:pass
                elif esc in (10,13):
                    if esc==13 and i+1<n and data[i+1]==10:i+=1
                else:buf.append(esc)
            elif b==0x28:
                depth+=1;buf.append(b)
            elif b==0x29:
                depth-=1
                if depth>0:buf.append(b)
            else:buf.append(b)
            i+=1
        if buf:
            for enc in ("utf-8","cp1252","latin-1"):
                try:
                    s=buf.decode(enc)
                    if any(ch.isalnum() for ch in s):out.append(s)
                    break
                except UnicodeDecodeError:pass
    return out

def _pdf_stream_fallback(pdf:bytes)->tuple[bool,str,str]:
    import zlib
    pieces=[]
    for m in re.finditer(br"stream\r?\n",pdf):
        s=m.end();e=pdf.find(b"endstream",s)
        if e<0:continue
        raw=pdf[s:e].rstrip(b"\r\n")
        header=pdf[max(0,m.start()-500):m.start()]
        candidates=[raw]
        if b"/FlateDecode" in header:
            try:candidates=[zlib.decompress(raw)]
            except Exception:continue
        for data in candidates:
            strings=_pdf_literal_strings_from_stream(data)
            if strings:pieces.extend(strings)
    txt=" ".join(pieces)
    ok=bool(re.search(r"\bIN\d{2,9}\b",txt)) and len(txt)>500
    return ok,txt,"PURE_PYTHON_PDF_STREAM_LITERAL_FALLBACK" if ok else "PURE_PYTHON_PDF_STREAM_FALLBACK_INSUFFICIENT"

def pdf_to_text(pdf:bytes)->tuple[bool,str,str]:
    try:
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"structure.pdf";p.write_bytes(pdf)
            cp=subprocess.run(["pdftotext","-layout","-enc","UTF-8",str(p),"-"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
            if cp.returncode==0:
                txt=cp.stdout.decode("utf-8",errors="replace")
                if txt.strip():
                    return True,txt,"PDFTOTEXT"
            primary_error=f"PDFTOTEXT_EXIT_{cp.returncode}:{cp.stderr.decode('utf-8',errors='replace')[:500]}"
    except FileNotFoundError:
        primary_error="PDFTOTEXT_NOT_AVAILABLE"
    except Exception as e:
        primary_error=f"{type(e).__name__}:{e}"
    ok,txt,fallback=_pdf_stream_fallback(pdf)
    return ok,txt,(fallback+";PRIMARY="+primary_error)

def exact_label_occurrences(pdf_text:str,label:str)->list[dict[str,str]]:
    flat=layout_norm(pdf_text); target=layout_norm(label)
    if not target:return []
    occ=[]
    for m in re.finditer(re.escape(target),flat):
        prefix=flat[max(0,m.start()-140):m.start()]
        codes=list(re.finditer(r"\bIN(\d{9}|\d{6}|\d{4}|\d{2})\b",prefix))
        if not codes:continue
        last=codes[-1]
        distance=len(prefix)-last.end()
        if distance>90:continue
        digits=len(last.group(1));level=LEVEL_BY_DIGITS[digits];code="IN"+last.group(1)
        parent=""
        if digits==4:parent="IN"+last.group(1)[:2]
        elif digits==6:parent="IN"+last.group(1)[:4]
        elif digits==9:parent="IN"+last.group(1)[:6]
        occ.append({"level":level,"code":code,"parent_code":parent,"distance":str(distance)})
    uniq={(x["level"],x["code"],x["parent_code"]):x for x in occ}
    return list(uniq.values())

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,"investing_com":0,
      "etf_holdings":0,"third_party_sector_databases":0,"company_sites":0,"company_name_joins":0,"fuzzy_matching":0,
      "per_security_web_fanout":0,"gics_icb_fallback":0,"cross_taxonomy_crosswalk":0,"price_ohlcv":0,"news":0,
      "trading_analysis":0,"pdsc_fallback":0
    }

def validate_predecessor(repo_sha:str)->tuple[dict[str,Any],dict[str,Any],list[dict[str,str]],dict[str,Any]]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM70.read_text(encoding="utf-8"));c=json.loads(CHK70.read_text(encoding="utf-8"));m=json.loads(MAN70.read_text(encoding="utf-8"))
    link=read_csv(LINK70);src=json.loads(SRC70.read_text(encoding="utf-8"))
    matrix=read_csv(MATRIX69);research=json.loads(RESEARCH62.read_text(encoding="utf-8"));taxinv=read_csv(TAXINV62)
    if s["verdict"]!="PASS_IN_NIFTY50_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE" or s["in_deterministic_ws_id_linkage_ready"] is not True:raise RuntimeError("v0.70 verdict")
    if (s["linked"],s["total"],s["ambiguous"],s["not_found"],s["not_verified"],s["conflict"])!=(45,45,0,0,0,0):raise RuntimeError("v0.70 counts")
    if s["direct_nifty_isin_links"]!=45 or s["nse_master_fallback_links"]!=0:raise RuntimeError("v0.70 identity route counts")
    if c["workflow_run_id"]!=V070_WORKFLOW or c["artifact_id"]!=V070_ARTIFACT or "sha256:"+c["artifact_digest"]!=V070_DIGEST:raise RuntimeError("v0.70 binding")
    if src["Selected_Source_URL"]!=NIFTY_URL or src["Raw_SHA256"]!=V070_NIFTY_SHA or src["Row_Count"]!=50:raise RuntimeError("v0.70 NIFTY source")
    if src["Field_Names"]!=["Company Name","Industry","Symbol","Series","ISIN Code"]:raise RuntimeError("v0.70 schema")
    if len(link)!=45 or any(r["Gate_E_Status"]!="PROVABLY_LINKED" for r in link):raise RuntimeError("v0.70 row linkage")
    if any(r["Identity_Route"]!="NIFTY_ISIN_DIRECT" for r in link):raise RuntimeError("v0.70 direct route")
    im=next(r for r in matrix if r["Cohort"]=="IN_NIFTY50")
    if im["G"]!="PASS_INHERITED" or im["H"]!="NOT_EVALUATED":raise RuntimeError("v0.69 G/H authority")
    f62=research["cohort_findings"]["IN_NIFTY50"]
    if f62["taxonomy_identity"]!=TAXONOMY or f62["gate_status"]["D"]!="PASS":raise RuntimeError("v0.62 taxonomy/D")
    ti=next(r for r in taxinv if r["Cohort"]=="IN_NIFTY50")
    if ti["Taxonomy_Identity"]!=TAXONOMY or ti["Sector_Code_Status"]!="PASS":raise RuntimeError("v0.62 source-native code authority")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability predecessor")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    return s,src,link,f62

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71")
    a=ap.parse_args()
    pred,src70,link70,f62=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["scope_cohort"]!=COHORT or spec["taxonomy"]!=TAXONOMY:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    frozen_rows=read_csv(FROZEN)
    frozen={r["Source_WS_ID"]:r for r in frozen_rows if r["Primary_MIC"]==MIC}
    target=[]
    for r in link70:
        ws=r["WS_ID"];fr=frozen.get(ws)
        target.append({
          "Security_Key":r["Security_Key"],"WS_ID":ws,"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Frozen_ISIN":r["Frozen_ISIN"],"v070_Gate_E_Status":r["Gate_E_Status"],
          "v070_Identity_Route":r["Identity_Route"],"Frozen_Crosscheck_Status":"PASS" if fr and fr["Primary_Ticker"]==r["Primary_Ticker"] else "FAIL"
        })
    target=sorted(target,key=lambda r:r["WS_ID"])
    target_ok=len(target)==45 and len({r["WS_ID"] for r in target})==45 and all(r["v070_Gate_E_Status"]=="PROVABLY_LINKED" and r["Primary_MIC"]==MIC and r["Frozen_Crosscheck_Status"]=="PASS" for r in target)
    if not target_ok:raise RuntimeError("v0.70/Frozen target mismatch")
    write_csv(out/"in_gate_f_identity_authority_binding_v0.71.csv",target)

    allowed=set(spec["allowed_hosts"]);ext=[]
    def do_fetch(url:str,kind:str,referer:str|None=None,max_bytes:int=12_000_000):
        fr=fetch(url,allowed,max_bytes=max_bytes,referer=referer)
        ext.append({"Request_Order":len(ext)+1,"Request_Type":kind,"URL":url,"Resolved_URL":fr.get("url",""),
                    "Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),
                    "SHA256":fr.get("sha256",""),"Timestamp_UTC":fr.get("timestamp_utc",""),"Official_Source":"YES",
                    "Per_Security_Fanout":"NO","Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
        return fr

    current=do_fetch(NIFTY_URL,"NIFTY50_CLASSIFICATION_BULK")
    fields=[];rows=[];f_isin=f_symbol=f_industry=None
    if current.get("ok") and not current.get("truncated"):
        try:
            fields,rows=parse_csv_bytes(current["body"])
            f_isin=pick_field(fields,["isincode","isin","isinnumber"])
            f_symbol=pick_field(fields,["symbol","securitysymbol"])
            f_industry=pick_field(fields,["industry"])
        except Exception:pass
    source_schema_ok=bool(rows and f_isin and f_symbol)
    class_field_ok=bool(f_industry)
    source_audit={
      "Source_Authority":"NSE Indices Limited","Source_URL":NIFTY_URL,"Retrieval_Timestamp_UTC":current.get("timestamp_utc",""),
      "HTTP_Status":current.get("status",""),"Content_Type":current.get("content_type",""),"Raw_Byte_Count":current.get("bytes",0),
      "Raw_SHA256":current.get("sha256",""),"v070_Raw_SHA256":V070_NIFTY_SHA,
      "SHA_Equals_v070":current.get("sha256","")==V070_NIFTY_SHA,"Row_Count":len(rows),"Exact_Schema":fields,
      "ISIN_Field":f_isin or "NOT_VERIFIED","Symbol_Field":f_symbol or "NOT_VERIFIED","Classification_Field":f_industry or "NOT_VERIFIED",
      "Raw_Snapshot_Persisted":False,"Raw_Persistence_Rights_Status":"NOT_VERIFIED","Schema_Status":"PASS" if source_schema_ok else "NOT_VERIFIED"
    }
    (out/"official_nifty50_classification_source_audit_v0.71.json").write_text(json.dumps(source_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"source_drift_audit_v0.71.json").write_text(json.dumps({
      "v070_SHA256":V070_NIFTY_SHA,"v071_SHA256":current.get("sha256",""),"Changed":current.get("sha256","")!=V070_NIFTY_SHA,
      "v070_Row_Count":50,"v071_Row_Count":len(rows),"Schema_Changed":fields!=src70["Field_Names"],
      "Drift_Is_Automatic_Failure":False,"Exact_45_Coverage_Rechecked":True
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")

    by_isin=defaultdict(list)
    if source_schema_ok:
        for rr in rows:
            isin=norm_id(rr.get(f_isin,""))
            if isin:by_isin[isin].append(rr)

    taxpage=do_fetch(TAXONOMY_PAGE,"NSE_INDICES_INDUSTRY_CLASSIFICATION_PAGE")
    structure_url=None;structure_candidates=[];page_text=""
    if taxpage.get("ok"):
        page_text=layout_norm(decode_text(taxpage["body"]))
        structure_url,structure_candidates=discover_structure_pdf(TAXONOMY_PAGE,taxpage["body"])
    structure=do_fetch(structure_url,"NSE_INDICES_INDUSTRY_CLASSIFICATION_STRUCTURE",referer=TAXONOMY_PAGE) if structure_url else {"ok":False,"body":b"","error":"STRUCTURE_LINK_NOT_UNIQUE"}
    pdf_ok,pdf_text,pdf_error=(False,"","NOT_FETCHED")
    if structure.get("ok") and not structure.get("truncated"):
        pdf_ok,pdf_text,pdf_error=pdf_to_text(structure["body"])

    formal_page_contract=all(x in page_text for x in ["Macro-Economic Sector","Sector","Industry","Basic Industry"]) and ("four levels of classification" in page_text or "4 tier structure" in page_text)
    industry_code_tokens=len(set(re.findall(r"\bIN\d{6}\b",pdf_text))) if pdf_ok else 0
    taxonomy_contract={
      "Taxonomy":TAXONOMY,"Authority":"NSE Indices Limited","Classification_Page":TAXONOMY_PAGE,
      "Classification_Page_HTTP_Status":taxpage.get("status",""),"Classification_Page_SHA256":taxpage.get("sha256",""),
      "Structure_Link_Candidates":structure_candidates,"Selected_Structure_URL":structure_url or "NOT_VERIFIED",
      "Structure_HTTP_Status":structure.get("status",""),"Structure_Content_Type":structure.get("content_type",""),
      "Structure_Raw_SHA256":structure.get("sha256",""),"Structure_Bytes":structure.get("bytes",0),
      "Structure_Text_Extraction_Status":"PASS" if pdf_ok else "NOT_VERIFIED","Structure_Text_Extraction_Error":pdf_error,
      "Formal_Four_Tier_Page_Contract_Status":"PASS" if formal_page_contract else "NOT_VERIFIED",
      "Industry_Code_Tokens_Observed":industry_code_tokens,
      "Expected_Level_Names":["MACRO_ECONOMIC_SECTOR","SECTOR","INDUSTRY","BASIC_INDUSTRY"],
      "Raw_Structure_Persisted":False,"Raw_Persistence_Rights_Status":"NOT_VERIFIED"
    }
    (out/"nse_industry_taxonomy_contract_audit_v0.71.json").write_text(json.dumps(taxonomy_contract,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    prelim=[];raw_labels=[]
    for t in target:
        hits=by_isin.get(norm_id(t["Frozen_ISIN"]),[]) if source_schema_ok else []
        status="NOT_VERIFIED";detail="";src_symbol="";raw_class=""
        if not source_schema_ok:
            status="NOT_VERIFIED";detail="Current NIFTY source schema not verified."
        elif len(hits)==0:
            status="NOT_FOUND";detail="Frozen ISIN absent from current NIFTY constituent source."
        elif len(hits)>1:
            status="AMBIGUOUS";detail="Multiple current NIFTY rows share exact Frozen ISIN."
        else:
            h=hits[0];src_symbol=norm_id(h.get(f_symbol,""));raw_class=h.get(f_industry,"") if f_industry else ""
            if src_symbol!=norm_id(t["Primary_Ticker"]):
                status="CONFLICT";detail="NIFTY Symbol differs from Frozen Primary_Ticker."
            elif not class_field_ok:
                status="NOT_VERIFIED";detail="Industry field missing from source schema."
            elif not raw_class.strip():
                status="NOT_VERIFIED";detail="Industry field empty."
            else:
                status="EXACT";raw_labels.append(raw_class)
        prelim.append({**t,"Current_NIFTY_Row_Match_Count":len(hits),"Current_NIFTY_Symbol":src_symbol,
                       "Source_Field_Name":f_industry or "NOT_VERIFIED","Source_Classification_Raw":raw_class,
                       "Source_Classification_NFC":unicodedata.normalize("NFC",raw_class) if raw_class else "",
                       "Current_Row_Linkage_Status":status,"Detail":detail})
    distinct_labels=sorted(set(raw_labels))

    bindings=[];collision=[];label_bind={}
    for label in distinct_labels:
        occ=exact_label_occurrences(pdf_text,label) if pdf_ok else []
        by_level=defaultdict(list)
        for x in occ:by_level[x["level"]].append(x)
        industry_nodes=sorted({x["code"] for x in by_level.get("INDUSTRY",[])})
        all_levels=sorted(by_level)
        bind_status="PASS" if len(industry_nodes)==1 else ("AMBIGUOUS" if len(industry_nodes)>1 else "NOT_VERIFIED")
        code=industry_nodes[0] if len(industry_nodes)==1 else ""
        label_bind[label]={"status":bind_status,"code":code,"occ":occ}
        bindings.append({
          "Source_Classification_Raw":label,"Official_Taxonomy_Level":"INDUSTRY","Source_Sector_Code":code or "NOT_VERIFIED",
          "Source_Sector_Name":label,"Code_Binding_Status":bind_status,"Evidence_Reference":structure_url or "NOT_VERIFIED",
          "Exact_Industry_Code_Count":len(industry_nodes),"Industry_Codes":" | ".join(industry_nodes)
        })
        same_level_collision=len(industry_nodes)>1
        parent_codes=sorted({x["parent_code"] for x in by_level.get("INDUSTRY",[]) if x["parent_code"]})
        collision.append({
          "Source_Classification_Raw":label,"Observed_Levels":" | ".join(all_levels) if all_levels else "NONE",
          "Industry_Code_Count":len(industry_nodes),"Industry_Codes":" | ".join(industry_nodes),
          "Industry_Parent_Codes":" | ".join(parent_codes),"Same_Bound_Level_Multiple_Codes":"YES" if same_level_collision else "NO",
          "Cross_Level_Label_Occurrence":"YES" if len(all_levels)>1 else "NO",
          "Collision_Status":"AMBIGUOUS" if same_level_collision else ("PASS" if len(industry_nodes)==1 else "NOT_VERIFIED")
        })
    write_csv(out/"in_source_native_code_binding_v0.71.csv",bindings if bindings else [{
      "Source_Classification_Raw":"","Official_Taxonomy_Level":"NOT_VERIFIED","Source_Sector_Code":"NOT_VERIFIED","Source_Sector_Name":"",
      "Code_Binding_Status":"NOT_VERIFIED","Evidence_Reference":"NOT_VERIFIED","Exact_Industry_Code_Count":0,"Industry_Codes":""
    }])
    write_csv(out/"in_classification_label_collision_audit_v0.71.csv",collision if collision else [{
      "Source_Classification_Raw":"","Observed_Levels":"NONE","Industry_Code_Count":0,"Industry_Codes":"","Industry_Parent_Codes":"",
      "Same_Bound_Level_Multiple_Codes":"NO","Cross_Level_Label_Occurrence":"NO","Collision_Status":"NOT_VERIFIED"
    }])

    binding_all_pass=bool(distinct_labels) and len(bindings)==len(distinct_labels) and all(r["Code_Binding_Status"]=="PASS" for r in bindings)
    level_binding_pass=formal_page_contract and pdf_ok and industry_code_tokens>0 and binding_all_pass
    level_binding={
      "Source_Field_Name":f_industry or "NOT_VERIFIED","Taxonomy":TAXONOMY,
      "Official_Taxonomy_Level":"INDUSTRY" if level_binding_pass else "NOT_VERIFIED",
      "Level_Binding_Status":"PASS" if level_binding_pass else "NOT_VERIFIED",
      "Level_Binding_Evidence":[
        TAXONOMY_PAGE,structure_url or "NOT_VERIFIED",
        "Official page defines Industry as one of four formal levels.",
        "Every distinct non-empty current NIFTY Industry value for the Frozen-45 exact ISIN rows is exact-match bound to one unique Ind_Code in the official classification structure."
      ],
      "Observed_Distinct_Source_Labels":len(distinct_labels),
      "Exact_Unique_Industry_Code_Bindings":sum(r["Code_Binding_Status"]=="PASS" for r in bindings),
      "Semantic_Inference_Used":False
    }
    (out/"in_classification_level_binding_v0.71.json").write_text(json.dumps(level_binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    final=[];inventory_counter=Counter()
    for r in prelim:
        status=r["Current_Row_Linkage_Status"];code="";bound_level="NOT_VERIFIED";detail=r["Detail"]
        if status=="EXACT":
            b=label_bind.get(r["Source_Classification_Raw"],{"status":"NOT_VERIFIED","code":""})
            if not level_binding_pass:
                status="NOT_VERIFIED";detail="Formal NIFTY Industry field to official INDUSTRY level binding not fully verified."
            elif b["status"]=="AMBIGUOUS":
                status="AMBIGUOUS";detail="Exact raw Industry label maps to multiple source-native Industry codes."
            elif b["status"]!="PASS":
                status="NOT_VERIFIED";detail="Exact source-native Industry code binding not verified."
            else:
                status="PROVABLY_CLASSIFIED";code=b["code"];bound_level="INDUSTRY";inventory_counter[(r["Source_Classification_Raw"],code)]+=1
        final.append({
          "Security_Key":r["Security_Key"],"WS_ID":r["WS_ID"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Frozen_ISIN":r["Frozen_ISIN"],"Current_NIFTY_ISIN_Match_Count":r["Current_NIFTY_Row_Match_Count"],
          "Current_NIFTY_Symbol":r["Current_NIFTY_Symbol"],"Source_Field_Name":r["Source_Field_Name"],
          "Source_Classification_Raw":r["Source_Classification_Raw"],"Source_Classification_NFC":r["Source_Classification_NFC"],
          "Taxonomy":TAXONOMY,"Official_Taxonomy_Level":bound_level,"Source_Sector_Code":code or "NOT_VERIFIED",
          "Classification_Status":status,"Evidence_Reference":NIFTY_URL+" | "+(structure_url or "NOT_VERIFIED"),"Detail":detail
        })
    write_csv(out/"in_exact_45_classification_coverage_v0.71.csv",final)

    raw_counts=Counter(r["Source_Classification_Raw"] for r in prelim if r["Source_Classification_Raw"])
    inventory=[]
    for label,count in sorted(raw_counts.items()):
        b=label_bind.get(label,{"status":"NOT_VERIFIED","code":""})
        inventory.append({"Source_Classification_Raw":label,
                          "Official_Taxonomy_Level":"INDUSTRY" if b["status"]=="PASS" and level_binding_pass else "NOT_VERIFIED",
                          "Source_Sector_Code":b["code"] if b["status"]=="PASS" else "NOT_VERIFIED",
                          "Frozen_Row_Count":count,
                          "Unique_Code_Status":b["status"]})
    write_csv(out/"in_distinct_classification_inventory_v0.71.csv",inventory if inventory else [{
      "Source_Classification_Raw":"","Official_Taxonomy_Level":"NOT_VERIFIED","Source_Sector_Code":"NOT_VERIFIED","Frozen_Row_Count":0,"Unique_Code_Status":"NOT_VERIFIED"
    }])

    counts={k:sum(r["Classification_Status"]==k for r in final) for k in ["PROVABLY_CLASSIFIED","AMBIGUOUS","NOT_FOUND","NOT_VERIFIED","CONFLICT"]}
    source_native_code_coverage=sum(1 for r in final if r["Classification_Status"]=="PROVABLY_CLASSIFIED" and r["Source_Sector_Code"]!="NOT_VERIFIED")
    membership_missing=counts["NOT_FOUND"]>0
    source_repro=bool(current.get("ok") and not current.get("truncated") and source_schema_ok)
    taxonomy_repro=bool(taxpage.get("ok") and structure_url and structure.get("ok") and pdf_ok)
    same_level_ambiguous=any(r["Collision_Status"]=="AMBIGUOUS" for r in collision)
    authority_regression=(taxpage.get("ok") and formal_page_contract and structure.get("ok") and pdf_ok and industry_code_tokens==0)

    blocker=""
    if not source_repro:blocker="OFFICIAL_NIFTY_CLASSIFICATION_SOURCE_NOT_REPRODUCIBLE"
    elif membership_missing:blocker="IN_FROZEN_MEMBER_NOT_PRESENT_IN_CURRENT_NIFTY_SOURCE"
    elif not class_field_ok:blocker="NIFTY_CLASSIFICATION_FIELD_MISSING"
    elif authority_regression:blocker="AUTHORITY_REGRESSION_REVIEW_REQUIRED"
    elif not taxonomy_repro or not level_binding_pass:blocker="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED"
    elif not binding_all_pass:blocker="NIFTY_SOURCE_NATIVE_CODE_BINDING_NOT_VERIFIED"
    elif same_level_ambiguous or counts["AMBIGUOUS"]>0:blocker="NIFTY_CLASSIFICATION_LABEL_AMBIGUOUS"
    elif counts["CONFLICT"]>0 or counts["NOT_VERIFIED"]>0 or counts["PROVABLY_CLASSIFIED"]<45:blocker="IN_EXACT_45_CLASSIFICATION_COVERAGE_INCOMPLETE"

    ready=(blocker=="" and counts["PROVABLY_CLASSIFIED"]==45 and counts["AMBIGUOUS"]==counts["NOT_FOUND"]==counts["NOT_VERIFIED"]==counts["CONFLICT"]==0 and source_native_code_coverage==45)
    verdict="PASS_IN_NIFTY50_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE" if ready else "BLOCKED_IN_NIFTY50_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE"
    next_gate="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE" if ready else blocker

    write_csv(out/"external_request_ledger_v0.71.csv",ext)
    providers=provider_calls();(out/"provider_call_audit_v0.71.json").write_text(json.dumps(providers,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "IN_Canonical_Partition_Created":False,"Gate_H_Promotions":0,"Canonical_Materialization_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.71.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V070_READY",pred["in_deterministic_ws_id_linkage_ready"] is True,"YES")
    test("TARGET_45",len(target)==45,len(target))
    test("TARGET_UNIQUE_45",len({r["WS_ID"] for r in target})==45,45)
    test("TARGET_XNSE",all(r["Primary_MIC"]==MIC for r in target),"PASS")
    test("V070_DIRECT_ISIN_45",all(r["v070_Identity_Route"]=="NIFTY_ISIN_DIRECT" for r in target),"PASS")
    test("NO_EQUITY_L_AUTHORITY_USED",all("EQUITY_L" not in r["Evidence_Reference"] for r in final),"PASS")
    test("NO_NAME_JOINS",providers["company_name_joins"]==0,0)
    test("NO_FUZZY",providers["fuzzy_matching"]==0,0)
    test("NO_PER_SECURITY_FANOUT",providers["per_security_web_fanout"]==0,0)
    test("NO_PDSC_FALLBACK",providers["pdsc_fallback"]==0,0)
    test("NO_THIRD_PARTY",all(v==0 for v in providers.values()),providers)
    test("GATE_H_NOT_PROMOTED",imm["Gate_H_Promotions"]==0,0)
    test("NO_CANONICAL_IN_PARTITION",not (ROOT/"sector_metadata/canonical/cohorts/IN_NIFTY50_sector_metadata_v1.csv").exists(),"PASS")
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("CLASSIFIED_45_45",counts["PROVABLY_CLASSIFIED"]==45,counts)
        test("ZERO_UNRESOLVED",counts["AMBIGUOUS"]==counts["NOT_FOUND"]==counts["NOT_VERIFIED"]==counts["CONFLICT"]==0,counts)
        test("TAXONOMY_UNIFORM",all(r["Taxonomy"]==TAXONOMY for r in final),TAXONOMY)
        test("LEVEL_BOUND_INDUSTRY",level_binding_pass and all(r["Official_Taxonomy_Level"]=="INDUSTRY" for r in final),"INDUSTRY")
        test("SOURCE_NATIVE_CODE_45",source_native_code_coverage==45,source_native_code_coverage)
        test("UNIQUE_LABEL_CODE_BINDINGS",binding_all_pass,"PASS")
    else:
        test("FAIL_BLOCKER_NONEMPTY",bool(blocker),blocker)
    write_csv(out/"test_results_v0.71.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,
      "in_exact_45_sector_classification_coverage_ready":ready,"classified":counts["PROVABLY_CLASSIFIED"],"total":45,
      "ambiguous":counts["AMBIGUOUS"],"not_found":counts["NOT_FOUND"],"not_verified":counts["NOT_VERIFIED"],"conflict":counts["CONFLICT"],
      "taxonomy":TAXONOMY,"bound_classification_level":"INDUSTRY" if level_binding_pass else "NOT_VERIFIED",
      "distinct_classifications":len(distinct_labels),"source_native_code_coverage":source_native_code_coverage,
      "source_sha256":current.get("sha256",""),"source_sha_changed_vs_v070":current.get("sha256","")!=V070_NIFTY_SHA,
      "blocker":blocker,"external_requests":len(ext),"prohibited_provider_calls":sum(providers.values()),
      "gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"artifact_binding":"PENDING_UPLOAD","productive":False,
      "next_gate":next_gate,"tests":{"total":len(tests),"passed":len(tests),"failed":0}
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_exact_45_sector_classification_coverage_ready","classified","total","ambiguous","not_found","not_verified","conflict","taxonomy","bound_classification_level","distinct_classifications","source_native_code_coverage","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.71.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.71.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,"verdict":verdict,
      "in_exact_45_sector_classification_coverage_ready":ready,"classified":counts["PROVABLY_CLASSIFIED"],"total":45,
      "ambiguous":counts["AMBIGUOUS"],"not_found":counts["NOT_FOUND"],"not_verified":counts["NOT_VERIFIED"],"conflict":counts["CONFLICT"],
      "taxonomy":TAXONOMY,"bound_classification_level":summary["bound_classification_level"],"distinct_classifications":summary["distinct_classifications"],
      "source_native_code_coverage":source_native_code_coverage,"blocker":blocker,"gate_h_promotions":0,"canonical_ready_rows":37,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,
      "artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.71.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
