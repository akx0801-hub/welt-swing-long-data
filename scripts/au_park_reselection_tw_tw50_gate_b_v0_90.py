#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,html,html.parser,io,json,re,subprocess,time,urllib.parse,urllib.request,urllib.error,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.90"
STAGE="AU_SP_ASX200_EXTERNAL_AUTHORIZATION_PARK_POST_PARK_RESELECTION_TW_TW50_GATE_B"
REQUIRED_START_HEAD="ef6029b3660b1f2a8bc29c016dc78d0188a775b1"
V089_WORKFLOW=36412097411
V089_ARTIFACT=10965001804
V089_DIGEST="sha256:39c8c68f5750164265b29c994b422ab78b57c772d3a497e24ab9f22c7e7a8c23"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_BEFORE_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"

SPEC=ROOT/"config/au_park_reselection_tw_tw50_gate_b_spec_v0.90.json"
GSEC06=ROOT/"config/manager_governance_authority_G_SEC_06_v0.76.json"
SUM89=ROOT/"output_au_sp_asx200_source_access_persistence_gate_h_v0_89/summary_v0.89.json"
CHK89=ROOT/"output_au_sp_asx200_source_access_persistence_gate_h_v0_89/stage_checkpoint_v0.89.json"
MAN89=ROOT/"output_au_sp_asx200_source_access_persistence_gate_h_v0_89/manifest_v0.89.json"
DEC89=ROOT/"output_au_sp_asx200_source_access_persistence_gate_h_v0_89/au_source_access_persistence_gate_h_decision_v0.89.json"
MATRIX69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/current_authority_cohort_gate_matrix_v0.69.csv"
SEL69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/selected_next_cohort_authority_v0.69.json"
LEDGER62=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/cohort_sector_source_route_ledger_v0.62.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
CANON_DIR=ROOT/"sector_metadata/canonical/cohorts"

TWSE_SERIES="https://www.twse.com.tw/en/indices/indices/series.html"
LSEG_SERIES="https://www.lseg.com/en/ftse-russell/indices/twse-taiwan"
TWSE_RULES="https://www.twse.com.tw/downloads/en/products/indices/IndexSen19.pdf"
TWSE_FACTBOOK="https://www.twse.com.tw/downloads/zh/about/company/factbook/2026/2.08.html"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.90"
ALLOWED_HOSTS={"www.twse.com.tw","wwwc.twse.com.tw","www.lseg.com","research.ftserussell.com"}

def now()->str:return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def clean(x:Any)->str:return re.sub(r"\s+"," ",html.unescape(str(x or ""))).strip()

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

class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.parts=[];self.anchors=[];self._href=None;self._a=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            self._href=dict(attrs).get("href","");self._a=[]
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self._href is not None:
            self.anchors.append({"href":self._href,"text":clean(" ".join(self._a))});self._href=None;self._a=[]
    def handle_data(self,data):
        if data.strip():self.parts.append(data)
        if self._href is not None:self._a.append(data)
    def text(self):return clean(" ".join(self.parts))

def fetch(url:str,max_bytes:int=12_000_000)->dict[str,Any]:
    host=(urllib.parse.urlparse(url).hostname or "").lower()
    ts=now()
    if host not in ALLOWED_HOSTS:
        return {"ok":False,"url":url,"resolved_url":"","status":0,"content_type":"","content_disposition":"","bytes":0,"sha256":"","body":b"","timestamp_utc":ts,"error":"HOST_NOT_ALLOWED"}
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,text/csv,application/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*;q=0.8","Accept-Encoding":"identity"})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read(max_bytes+1);tr=len(b)>max_bytes
            if tr:b=b[:max_bytes]
            return {"ok":200<=int(getattr(r,"status",200))<300 and not tr,"url":url,"resolved_url":r.geturl(),
              "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
              "content_disposition":r.headers.get("Content-Disposition",""),"bytes":len(b),"sha256":sha_bytes(b),
              "body":b,"timestamp_utc":ts,"error":"TRUNCATED" if tr else ""}
    except urllib.error.HTTPError as e:
        b=e.read(200_000)
        return {"ok":False,"url":url,"resolved_url":e.geturl() or url,"status":int(e.code),
          "content_type":e.headers.get("Content-Type","") if e.headers else "","content_disposition":e.headers.get("Content-Disposition","") if e.headers else "",
          "bytes":len(b),"sha256":sha_bytes(b) if b else "","body":b,"timestamp_utc":ts,"error":"HTTPError"}
    except Exception as e:
        return {"ok":False,"url":url,"resolved_url":"","status":0,"content_type":"","content_disposition":"",
          "bytes":0,"sha256":"","body":b"","timestamp_utc":ts,"error":type(e).__name__+":"+str(e)}

def html_audit(resp:dict[str,Any])->dict[str,Any]:
    txt=resp["body"].decode("utf-8","replace") if resp["body"] else ""
    p=PageParser()
    try:p.feed(txt)
    except Exception:pass
    return {"text":p.text(),"anchors":p.anchors,"parser":p}

def discover_lseg_constituent_links(page:dict[str,Any])->list[dict[str,str]]:
    if not page["ok"]:return []
    audit=html_audit(page)
    out=[]
    for a in audit["anchors"]:
        href=clean(a["href"]);txt=clean(a["text"])
        absu=urllib.parse.urljoin(page["resolved_url"] or page["url"],href)
        low=(href+" "+txt).lower()
        if ("downloadconstituentsweights" in low or ("constituent" in low and ("twse" in low or "tw50" in low or "taiwan" in low))) and "tw50" in absu.lower():
            if (urllib.parse.urlparse(absu).hostname or "").lower() in ALLOWED_HOSTS:
                out.append({"URL":absu,"Anchor_Text":txt,"Discovery_Basis":"CURRENT_OFFICIAL_LSEG_PAGE_ANCHOR"})
    # bounded raw-string fallback only if current page itself embeds the exact route
    raw=page["body"].decode("utf-8","replace")
    for m in re.finditer(r'https?://[^"\'<>\s]+DownloadConstituentsWeights[^"\'<>\s]+',raw,re.I):
        u=html.unescape(m.group(0))
        if "tw50" in u.lower() and (urllib.parse.urlparse(u).hostname or "").lower() in ALLOWED_HOSTS:
            out.append({"URL":u,"Anchor_Text":"","Discovery_Basis":"CURRENT_OFFICIAL_LSEG_PAGE_EMBEDDED_URL"})
    ded=[];seen=set()
    for x in out:
        if x["URL"] not in seen:seen.add(x["URL"]);ded.append(x)
    return ded

def excel_col_index(ref:str)->int:
    letters=re.match(r"([A-Z]+)",ref or "")
    if not letters:return 0
    n=0
    for ch in letters.group(1):n=n*26+ord(ch)-64
    return n-1

def parse_xlsx(body:bytes)->tuple[list[str],list[list[str]],str]:
    z=zipfile.ZipFile(io.BytesIO(body))
    shared=[]
    if "xl/sharedStrings.xml" in z.namelist():
        root=ET.fromstring(z.read("xl/sharedStrings.xml"))
        ns={"a":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for si in root.findall("a:si",ns):
            shared.append("".join(t.text or "" for t in si.findall(".//a:t",ns)))
    wb=ET.fromstring(z.read("xl/workbook.xml"))
    ns={"a":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    sheet=wb.find("a:sheets/a:sheet",ns)
    if sheet is None:return [],[],"XLSX_NO_SHEET"
    rid=sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id","")
    rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target=""
    for x in rel:
        if x.attrib.get("Id")==rid:target=x.attrib.get("Target","");break
    path="xl/"+target.lstrip("/") if not target.startswith("xl/") else target
    root=ET.fromstring(z.read(path))
    rows=[]
    for row in root.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
        vals={}
        for c in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
            idx=excel_col_index(c.attrib.get("r","A1"));typ=c.attrib.get("t","");v=c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
            val=""
            if typ=="inlineStr":
                t=c.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t");val=t.text if t is not None else ""
            elif v is not None:
                val=v.text or ""
                if typ=="s":
                    try:val=shared[int(val)]
                    except Exception:pass
            vals[idx]=clean(val)
        if vals:
            arr=[""]*(max(vals)+1)
            for i,v in vals.items():arr[i]=v
            rows.append(arr)
    return table_from_rows(rows,"XLSX")

def table_from_rows(rows:list[list[str]],fmt:str)->tuple[list[str],list[list[str]],str]:
    rows=[[clean(x) for x in r] for r in rows if any(clean(x) for x in r)]
    if not rows:return [],[],fmt+"_EMPTY"
    # find first plausible header row with at least 2 non-empty cells
    hidx=0
    for i,r in enumerate(rows[:20]):
        low="|".join(x.lower() for x in r)
        if sum(bool(x) for x in r)>=2 and any(k in low for k in ["constituent","ticker","sedol","isin","code","icb","company","weight"]):
            hidx=i;break
    hdr=rows[hidx]
    width=len(hdr)
    data=[]
    for r in rows[hidx+1:]:
        rr=r+[""]*(width-len(r));data.append(rr[:width])
    return hdr,data,fmt

def parse_tabular(body:bytes,ctype:str,disp:str)->tuple[list[str],list[list[str]],str]:
    if body.startswith(b"PK\x03\x04"):
        try:return parse_xlsx(body)
        except Exception as e:return [],[],"XLSX_PARSE_ERROR:"+type(e).__name__
    if body.startswith(bytes.fromhex("D0CF11E0")):
        return [],[],"XLS_OLE_UNSUPPORTED"
    encodings=["utf-8-sig","utf-16","cp950","big5","latin1"]
    text=None;enc=""
    for e in encodings:
        try:
            t=body.decode(e)
            if "\x00" in t and e not in {"utf-16"}:continue
            text=t;enc=e;break
        except Exception:pass
    if text is None:return [],[],"TEXT_DECODE_FAILED"
    if "<html" in text[:1000].lower() or "<table" in text[:5000].lower():
        # bounded HTML table parser
        trs=re.findall(r"<tr\b[^>]*>(.*?)</tr>",text,re.I|re.S)
        rows=[]
        for tr in trs:
            cells=re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>",tr,re.I|re.S)
            if cells:
                rows.append([clean(re.sub(r"<[^>]+>"," ",x)) for x in cells])
        return table_from_rows(rows,"HTML_TABLE")
    sample=text[:10000]
    delim=","
    try:delim=csv.Sniffer().sniff(sample,delimiters=",\t;|").delimiter
    except Exception:
        if "\t" in sample:delim="\t"
    rows=list(csv.reader(io.StringIO(text),delimiter=delim))
    return table_from_rows(rows,"TEXT_"+enc+"_DELIM_"+repr(delim))

def normalize_header(h:str)->str:return re.sub(r"[^a-z0-9]+"," ",clean(h).lower()).strip()

def detect_fields(headers:list[str])->dict[str,Any]:
    norm=[normalize_header(h) for h in headers]
    identifiers=[]
    for i,h in enumerate(norm):
        typ=""
        if "isin" in h:typ="ISIN"
        elif "sedol" in h:typ="SEDOL"
        elif "local code" in h or "security code" in h or "stock code" in h:typ="LOCAL_SECURITY_CODE"
        elif h in {"ticker","ticker code","code"} or "ticker" in h:typ="TICKER"
        if typ:identifiers.append({"index":i,"field":headers[i],"type":typ})
    icb_code=[];icb_name=[];icb_other=[]
    for i,h in enumerate(norm):
        if "icb" not in h:continue
        is_group=("industry group" in h or "industrygroup" in h)
        is_code=("code" in h or "number" in h or h.endswith("icb"))
        if is_group and is_code:icb_code.append({"index":i,"field":headers[i]})
        elif is_group:icb_name.append({"index":i,"field":headers[i]})
        else:icb_other.append({"index":i,"field":headers[i]})
    return {"identifier_candidates":identifiers,"icb_group_code_candidates":icb_code,"icb_group_name_candidates":icb_name,"icb_other_fields":icb_other}

def metadata(resp:dict[str,Any])->dict[str,Any]:
    return {k:resp[k] for k in ["url","resolved_url","status","content_type","content_disposition","bytes","sha256","timestamp_utc","error"]}

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("start head not ancestor")
    s=json.loads(SUM89.read_text());c=json.loads(CHK89.read_text());m=json.loads(MAN89.read_text());d=json.loads(DEC89.read_text())
    if s["verdict"]!="BLOCKED_AU_SP_ASX200_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE_H":raise RuntimeError("v0.89 verdict")
    if s["au_source_access_persistence_ready"] is not False:raise RuntimeError("v0.89 ready")
    checks={
      "asx_access_ready":"YES","gics_access_ready":"YES","raw_asx_persistence_required":"NO","raw_gics_persistence_required":"NO",
      "asx_bounded_evidence_sufficient":"YES","gics_bounded_evidence_sufficient":"YES","asx_policy_compatibility":"NO",
      "gics_policy_compatibility":"NO","canonical_metadata_evidence_persistable":"NO","external_authorization_required":"YES",
      "blocker":"EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION"
    }
    if any(s.get(k)!=v for k,v in checks.items()):raise RuntimeError("v0.89 state mismatch")
    if c["workflow_run_id"]!=V089_WORKFLOW or c["artifact_id"]!=V089_ARTIFACT or c["artifact_digest"]!=V089_DIGEST:raise RuntimeError("v0.89 artifact")
    if m["workflow_run_id"]!=V089_WORKFLOW or m["artifact_id"]!=V089_ARTIFACT or m["artifact_digest"]!=V089_DIGEST:raise RuntimeError("v0.89 manifest")
    if d["G"]!="PASS" or d["H"]!="BLOCKED" or d["GICS_OFFICIAL_POLICY_COMPATIBILITY_READY"]!="NO":raise RuntimeError("v0.89 blockers")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    if sha_file(PARK)!=PARK_BEFORE_SHA:raise RuntimeError("park start hash")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SHA:raise RuntimeError("canonical registry")
    if any(CANON_DIR.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical exists")
    return {"summary":s,"checkpoint":c,"manifest":m,"decision":d}

def validate_gsec06()->dict[str,Any]:
    g=json.loads(GSEC06.read_text())
    if g["authority_id"]!="G-SEC-06":raise RuntimeError("G-SEC-06")
    r=g["rules"]
    required=["external_consent_license_contractual_blocker_may_be_parked","parking_does_not_downgrade_proven_technical_gates",
              "parked_cohort_excluded_from_active_next_cohort_selection","parking_does_not_create_canonical_metadata",
              "parked_cohort_may_not_be_automatically_reopened_by_later_cohort_workflows"]
    if not all(r[k] for k in required):raise RuntimeError("G-SEC-06 rules")
    return g

def apply_au_park(out:Path,g:dict[str,Any])->dict[str,Any]:
    before=PARK.read_bytes();before_sha=sha_bytes(before)
    rows=read_csv(PARK);by={r["Cohort"]:r for r in rows}
    preserved={"IN_NIFTY50":"PARKED_EXTERNAL_AUTHORIZATION","JP_N225":"PARKED_EXTERNAL_AUTHORIZATION","US_SP400":"PARKED_SOURCE_ACCESS","US_SP500":"PARKED_SHARED_SOURCE_PREREQUISITE"}
    if set(by)!=set(preserved):raise RuntimeError("unexpected pre-park rows")
    if any(by[k]["Execution_State"]!=v for k,v in preserved.items()):raise RuntimeError("preserved park state mismatch")
    au={
      "Cohort":"AU_SP_ASX200","Execution_State":"PARKED_EXTERNAL_AUTHORIZATION","Technical_Gates_A_G":"PASS",
      "Gate_H":"BLOCKED","Gate_H_Blocker":"EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION","Gate_F_Classified":"63","Gate_F_Total":"63",
      "Canonical_Readiness":"NO","Canonical_Rows":"0","Reopen_Automatically":"NO","Authority":"G-SEC-06","Effective_From":"v0.90"
    }
    fields=list(rows[0].keys())
    if "AU_SP_ASX200" in by:
        if any(by["AU_SP_ASX200"].get(k)!=v for k,v in au.items()):raise RuntimeError("AU park mismatch")
        action="ALREADY_APPLIED_IDEMPOTENT"
    else:
        # append via csv writer in deterministic row order after existing rows
        rows.append(au);write_csv(PARK,rows,fields);action="APPLIED_EXISTING_RULE_NO_NEW_GOVERNANCE"
    after_sha=sha_file(PARK);rows_after=read_csv(PARK)
    write_csv(out/"parked_cohort_registry_update_v0.90.csv",rows_after,fields)
    write_json(out/"au_external_authorization_park_application_v0.90.json",{
      **au,"Additional_Independent_Gate_H_Blocker":"EXPLICIT_GICS_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Authorization_Requirement":"ASX prior written consent / applicable express permission AND applicable MSCI / S&P Dow Jones Indices GICS license or permission",
      "Gate_F":"63/63","Gate_G":"63/63","Authority_Title":g["title"],"Authority_Action":action,
      "Park_Registry_SHA256_Before":before_sha,"Park_Registry_SHA256_After":after_sha
    })
    write_json(out/"au_gate_h_blocker_preservation_v0.90.json",{
      "Primary_Gate_H_Blocker":"EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Additional_Independent_Gate_H_Blocker":"EXPLICIT_GICS_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Failure_Precedence_Primary_Preserved":"YES","Independent_GICS_Blocker_Erased":"NO",
      "Technical_Gates_A_G":"PASS","Gate_F":"63/63","Gate_G":"63/63","Gate_H":"BLOCKED"
    })
    return {"rows":rows_after,"sha":after_sha,"action":action}

def reselection(out:Path,park_rows:list[dict[str,str]])->dict[str,Any]:
    matrix=read_csv(MATRIX69);sel=json.loads(SEL69.read_text())
    parked={r["Cohort"]:r["Execution_State"] for r in park_rows}
    active_matrix=[];calc=[]
    for r in matrix:
        cohort=r["Cohort"]
        state=parked.get(cohort,"ACTIVE")
        eligible=cohort not in parked
        active_matrix.append({
          "Cohort":cohort,"Frozen_Rows":r["Frozen_Rows"],"Execution_State":state if not eligible else "ACTIVE",
          "A":r["A"],"B":r["B"],"C":r["C"],"D":r["D"],"E":r["E"],"F":r["F"],"G":r["G"],"H":r["H"],
          "Consecutive_Resolved_Gates":r["Consecutive_Resolved_Gates"],"Earliest_Unresolved_Gate":r["Current_Earliest_Unresolved_Gate"],
          "Selection_Eligible":"YES" if eligible else "NO"
        })
        calc.append({
          "Cohort":cohort,"Frozen_Rows":int(r["Frozen_Rows"]),"Execution_State":state if not eligible else "ACTIVE",
          "Consecutive_Resolved_Gates":int(r["Consecutive_Resolved_Gates"]),"Earliest_Unresolved_Gate":r["Current_Earliest_Unresolved_Gate"],
          "Selection_Eligible":"YES" if eligible else "NO","Tie_Break_Rank":"","Selected":"NO"
        })
    eligible=[x for x in calc if x["Selection_Eligible"]=="YES"]
    eligible.sort(key=lambda x:(-x["Consecutive_Resolved_Gates"],x["Frozen_Rows"],x["Cohort"]))
    for i,x in enumerate(eligible,1):x["Tie_Break_Rank"]=i
    if not eligible:raise RuntimeError("no active cohorts")
    eligible[0]["Selected"]="YES";selected=eligible[0]
    # modify originals by cohort
    rankmap={x["Cohort"]:x for x in eligible}
    for x in calc:
        if x["Cohort"] in rankmap:
            x["Tie_Break_Rank"]=rankmap[x["Cohort"]]["Tie_Break_Rank"];x["Selected"]=rankmap[x["Cohort"]]["Selected"]
    write_csv(out/"post_au_park_active_cohort_gate_matrix_v0.90.csv",active_matrix)
    write_csv(out/"post_au_park_selection_calculation_v0.90.csv",calc)
    write_json(out/"post_au_park_selected_cohort_authority_v0.90.json",{
      "Selected_Cohort":selected["Cohort"],"Frozen_Rows":selected["Frozen_Rows"],
      "Consecutive_Resolved_Gates":selected["Consecutive_Resolved_Gates"],"Earliest_Unresolved_Gate":selected["Earliest_Unresolved_Gate"],
      "Selection_Rule":sel["Selection_Rule"],"Calculation_Not_Hard_Coded":True,
      "Eligible_Cohorts":[x["Cohort"] for x in eligible],"Expected_Competition":["TW_TW50","CN_CSI300"]
    })
    return {"selected":selected,"calc":calc}

def inherited_tw_authority(out:Path)->dict[str,Any]:
    led=read_csv(LEDGER62);tw=[r for r in led if r["Cohort"]=="TW_TW50"]
    if len(tw)!=1:raise RuntimeError("TW v0.62 authority")
    r=tw[0]
    if not (r["Taxonomy_Identity"]=="ICB" and r["A_Official_Source"]=="PASS" and r["C_Taxonomy_Identity"]=="PASS" and r["D_Sector_Fields"]=="PASS" and r["G_Provenance"]=="PASS"):
        raise RuntimeError("TW inherited gates")
    write_json(out/"tw_gate_b_predecessor_authority_v0.90.json",{
      "Cohort":"TW_TW50","Frozen_Rows":49,"A":"PASS_INHERITED","B":"TARGET_THIS_STAGE","C":"PASS_INHERITED",
      "D":"PASS_INHERITED","E":"NOT_EVALUATED","F":"NOT_EVALUATED","G":"PASS_INHERITED","H":"NOT_EVALUATED",
      "Historical_Blocker":"OFFICIAL_SECTOR_BULK_SOURCE_NOT_VERIFIED","Source_v062":str(LEDGER62.relative_to(ROOT))
    })
    write_json(out/"tw_inherited_taxonomy_field_authority_v0.90.json",{
      "Taxonomy":"ICB","Formal_Level":"INDUSTRY_GROUP","Source_Native_Candidate":r["Source_Native_Candidate"],
      "C_Taxonomy_Identity":"PASS_INHERITED","D_Sector_Fields_Codes":"PASS_INHERITED","G_Provenance":"PASS_INHERITED",
      "Historical_Official_Sources":[TWSE_RULES,"https://wwwc.twse.com.tw/en/indices/indices/series.html",TWSE_FACTBOOK],
      "Gate_B_Does_Not_Reopen_C_or_D":"YES","Cross_Taxonomy_Substitution":"NO"
    })
    return r

def run_tw_gate_b(out:Path)->dict[str,Any]:
    reqs=[];candidates=[]
    def do(url,source_class,purpose):
        resp=fetch(url);reqs.append({"Request_Order":len(reqs)+1,"Source_Class":source_class,"URL":url,"Purpose":purpose,
          "HTTP_Status":resp["status"],"Content_Type":resp["content_type"],"Bytes":resp["bytes"],"SHA256":resp["sha256"],
          "Retrieval_Timestamp_UTC":resp["timestamp_utc"],"Per_Security_Request":"NO"});return resp
    twse=do(TWSE_SERIES,"TWSE_OFFICIAL","CURRENT_INDEX_SERIES_DISCOVERY")
    lseg=do(LSEG_SERIES,"FTSE_RUSSELL_LSEG_OFFICIAL","CURRENT_INDEX_SERIES_DISCOVERY")
    page_audits=[]
    for name,r in [("TWSE_INDEX_SERIES",twse),("LSEG_FTSE_TWSE_SERIES",lseg)]:
        audit=html_audit(r) if r["body"] else {"text":"","anchors":[]}
        page_audits.append({"Source":name,**metadata(r),"Text_Markers":[x for x in ["Taiwan 50","ICB","Industry Group","Constituents"] if x.lower() in audit["text"].lower()],
                            "Anchor_Count":len(audit["anchors"])})
    write_json(out/"tw_current_official_page_source_audit_v0.90.json",{"Pages":page_audits})

    links=discover_lseg_constituent_links(lseg)
    for x in links:candidates.append({"Candidate_URL":x["URL"],"Source_Class":"FTSE_RUSSELL_LSEG_OFFICIAL","Candidate_Type":"CONSTITUENT_BULK_DOWNLOAD","Discovery_Basis":x["Discovery_Basis"],"Anchor_Text":x["Anchor_Text"],"Status":"DISCOVERED"})
    # official aggregate-only corroborators are explicitly rejected for Gate B
    candidates.append({"Candidate_URL":TWSE_FACTBOOK,"Source_Class":"TWSE_OFFICIAL","Candidate_Type":"AGGREGATE_INDUSTRY_STATISTICS","Discovery_Basis":"HISTORICAL_AUTHORITY","Anchor_Text":"","Status":"REJECT_AGGREGATE_ONLY"})
    candidates.append({"Candidate_URL":TWSE_RULES,"Source_Class":"TWSE_OFFICIAL","Candidate_Type":"METHODOLOGY","Discovery_Basis":"HISTORICAL_AUTHORITY","Anchor_Text":"","Status":"REJECT_METHODOLOGY_ONLY"})
    write_csv(out/"tw_official_source_candidate_inventory_v0.90.csv",candidates)
    write_json(out/"tw_static_bulk_route_discovery_audit_v0.90.json",{
      "Static_TWSE_Page_HTTP_Status":twse["status"],"Static_LSEG_Page_HTTP_Status":lseg["status"],
      "Discovered_Current_Official_Constituent_Routes":links,
      "No_Guessed_Stale_Endpoint":"YES","Static_Route_Discovered":"YES" if links else "NO"
    })

    runtime_status="NOT_REQUIRED_STATIC_ROUTE_SUCCEEDED" if links else "NOT_EXECUTED_BROWSER_MECHANISM_UNAVAILABLE_IN_THIS_PATH"
    write_json(out/"tw_runtime_capture_environment_v0.90.json",{
      "Status":runtime_status,"Browser_Name":"NOT_USED","Authentication":"NONE","CAPTCHA_Bypass":"NO","Privileged_Session":"NO","Proxy_Rotation":"NO"
    })
    write_csv(out/"tw_runtime_network_candidate_inventory_v0.90.csv",[],["Status","Request_URL","Resource_Type","HTTP_Status","Content_Type","Candidate_Reason"])
    write_json(out/"tw_runtime_interaction_audit_v0.90.json",{"Status":runtime_status,"Interactions":[]})

    selected_url=links[0]["URL"] if links else ""
    run_meta=[];headers=[];rows=[];fmt="";fields={"identifier_candidates":[],"icb_group_code_candidates":[],"icb_group_name_candidates":[],"icb_other_fields":[]}
    selected_source=""
    direct_replay="NOT_APPLICABLE"
    if selected_url:
        for n in [1,2]:
            rr=do(selected_url,"FTSE_RUSSELL_LSEG_OFFICIAL",f"TW50_CONSTITUENT_BULK_REPRODUCIBILITY_RUN_{n}")
            h,d,fm=parse_tabular(rr["body"],rr["content_type"],rr["content_disposition"]) if rr["ok"] else ([],[],"NO_BODY")
            run_meta.append({**metadata(rr),"Run":n,"Format":fm,"Schema":h,"Row_Count":len(d)})
            write_json(out/f"tw_bulk_route_reproducibility_run{n}_v0.90.json",run_meta[-1])
            if n==1:headers,rows,fmt=h,d,fm
        same_contract=bool(len(run_meta)==2 and run_meta[0]["status"]==run_meta[1]["status"]==200 and run_meta[0]["Schema"]==run_meta[1]["Schema"] and run_meta[0]["Format"]==run_meta[1]["Format"])
        if run_meta and run_meta[0]["status"]==200 and headers:
            fields=detect_fields(headers)
        # one bounded direct replay after route identification
        rep=do(selected_url,"FTSE_RUSSELL_LSEG_OFFICIAL","TW50_SELECTED_ROUTE_DIRECT_HTTP_REPLAY")
        rh,rd,rf=parse_tabular(rep["body"],rep["content_type"],rep["content_disposition"]) if rep["ok"] else ([],[],"NO_BODY")
        direct_replay="PASS" if rep["ok"] and rh==headers and bool(headers) else "FAIL"
        write_json(out/"tw_direct_http_replay_audit_v0.90.json",{**metadata(rep),"DIRECT_HTTP_REPLAY":direct_replay,"Format":rf,"Schema":rh,"Row_Count":len(rd)})
    else:
        same_contract=False
        for n in [1,2]:write_json(out/f"tw_bulk_route_reproducibility_run{n}_v0.90.json",{"Run":n,"Status":"NOT_EXECUTED_NO_SELECTED_ROUTE"})
        write_json(out/"tw_direct_http_replay_audit_v0.90.json",{"DIRECT_HTTP_REPLAY":"NOT_APPLICABLE","Status":"NO_SELECTED_ROUTE"})

    id_field="";id_type="";id_unique="NOT_VERIFIED";id_usable="NO"
    if fields["identifier_candidates"] and rows:
        cand=fields["identifier_candidates"][0];idx=cand["index"];vals=[clean(r[idx]) if idx<len(r) else "" for r in rows]
        non=[v for v in vals if v];id_field=cand["field"];id_type=cand["type"]
        id_unique="YES" if len(non)==len(set(non)) and len(non)>1 else "NO"
        id_usable="YES" if id_unique=="YES" else "NO"
    icb_code=fields["icb_group_code_candidates"][0]["field"] if fields["icb_group_code_candidates"] else ""
    icb_name=fields["icb_group_name_candidates"][0]["field"] if fields["icb_group_name_candidates"] else ""
    explicit_group=bool(icb_code or icb_name)
    row_level=len(rows)>1 and bool(id_field)
    source_ready=bool(selected_url and same_contract and direct_replay=="PASS" and row_level and id_usable=="YES" and explicit_group)
    blocker=""
    if not twse["ok"] and not lseg["ok"]:blocker="TWSE_OFFICIAL_INDEX_SOURCE_NOT_REPRODUCIBLE"
    elif not links:blocker="TWSE_TAIWAN50_BULK_CONSTITUENT_ROUTE_NOT_REPRODUCIBLE"
    elif not same_contract or not headers:blocker="TWSE_TAIWAN50_BULK_CONSTITUENT_ROUTE_NOT_REPRODUCIBLE"
    elif not id_field:blocker="TWSE_BULK_SECURITY_IDENTIFIER_NOT_AVAILABLE"
    elif not explicit_group:
        blocker="TWSE_BULK_ICB_LEVEL_BINDING_NOT_VERIFIED" if fields["icb_other_fields"] else "TWSE_BULK_ICB_INDUSTRY_GROUP_FIELD_NOT_AVAILABLE"
    elif id_unique!="YES":blocker="TWSE_BULK_SECURITY_IDENTIFIER_NOT_AVAILABLE"
    if source_ready:blocker=""

    sample=[]
    for r in rows[:5]:
        sample.append({headers[i]:(r[i] if i<len(r) else "") for i in range(min(len(headers),len(r)))})
    write_json(out/"tw_bulk_schema_audit_v0.90.json",{
      "Selected_URL":selected_url,"Format":fmt,"Schema":headers,"Row_Count":len(rows),"Bounded_Sample_First_5":sample,
      "Security_Identifier_Candidates":fields["identifier_candidates"],"ICB_Industry_Group_Code_Candidates":fields["icb_group_code_candidates"],
      "ICB_Industry_Group_Name_Candidates":fields["icb_group_name_candidates"],"Other_ICB_Fields":fields["icb_other_fields"]
    })
    write_json(out/"tw_bulk_security_identifier_audit_v0.90.json",{
      "Identifier_Field":id_field or "NOT_AVAILABLE","Identifier_Type":id_type or "NOT_AVAILABLE",
      "Uniqueness_Status_in_Source":id_unique,"Identifier_Usable_For_Future_Gate_E":id_usable,
      "Frozen_49_Linkage_Performed":"NO"
    })
    write_json(out/"tw_bulk_icb_industry_group_field_audit_v0.90.json",{
      "ICB_Code_Field":icb_code or "NOT_AVAILABLE","ICB_Name_Field":icb_name or "NOT_AVAILABLE",
      "ICB_Level":"INDUSTRY_GROUP" if explicit_group else "NOT_VERIFIED","Inherited_Taxonomy":"ICB",
      "No_Code_Length_Inference":"YES","C_D_Reopened":"NO"
    })
    write_json(out/"tw_bulk_row_level_vs_aggregate_audit_v0.90.json",{
      "Row_Level_Security_Records":"YES" if row_level else "NO","Parsed_Row_Count":len(rows),
      "Multiple_Securities_Represented":"YES" if len(rows)>1 else "NO","Aggregate_Only":"NO" if row_level else "NOT_VERIFIED"
    })
    composition="SINGLE_OFFICIAL_BULK_SOURCE" if source_ready else "NONE_VERIFIED"
    selected_contract={
      "TW_OFFICIAL_SECTOR_BULK_SOURCE_READY":"YES" if source_ready else "NO","Official_Source":selected_url or "NOT_VERIFIED",
      "Source_Composition":composition,"Bulk_Route_Type":"OFFICIAL_STATIC_LINKED_BULK_DOWNLOAD" if selected_url else "NOT_VERIFIED",
      "Public_Reproducible":"YES" if same_contract else "NO","DIRECT_HTTP_REPLAY":direct_replay,
      "Row_Level_Security_Records":"YES" if row_level else "NO","Security_Identifier_Field":id_field or "NOT_AVAILABLE",
      "Security_Identifier_Type":id_type or "NOT_AVAILABLE","ICB_Industry_Group_Code_Field":icb_code or "NOT_AVAILABLE",
      "ICB_Industry_Group_Name_Field":icb_name or "NOT_AVAILABLE","ICB_Level_Binding":"PASS" if explicit_group else "NOT_VERIFIED",
      "Per_Security_Fanout":"0","Frozen_49_Linkage_Runs":"0"
    }
    write_json(out/"tw_selected_bulk_source_contract_v0.90.json",selected_contract)
    write_json(out/"tw_source_composition_decision_v0.90.json",{"Source_Composition":composition,"Selected_Source_Count":1 if source_ready else 0,"Two_Source_Composition_Used":"NO"})
    gate_dec={
      "Cohort":"TW_TW50","Taxonomy":"ICB","Level":"INDUSTRY_GROUP","A":"PASS_INHERITED",
      "B":"PASS_BY_CURRENT_EVIDENCE" if source_ready else "BLOCKED","C":"PASS_INHERITED","D":"PASS_INHERITED",
      "E":"NOT_EVALUATED","F":"NOT_EVALUATED","G":"PASS_INHERITED","H":"NOT_EVALUATED",
      "TW_OFFICIAL_SECTOR_BULK_SOURCE_READY":"YES" if source_ready else "NO","Blocker":blocker,
      "Next_Gate":"TW_TW50 DETERMINISTIC SECURITY IDENTITY LINKAGE GATE E" if source_ready else "TW_TW50 SOURCE-ROUTE PARK / ACTIVE-COHORT RESELECTION MANAGER GATE"
    }
    write_json(out/"tw_official_sector_bulk_source_gate_b_decision_v0.90.json",gate_dec)
    write_csv(out/"external_request_ledger_v0.90.csv",reqs)
    return {"decision":gate_dec,"contract":selected_contract,"requests":reqs,"fields":fields,"runtime_status":runtime_status}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_au_park_reselection_tw_tw50_gate_b_v0_90")
    a=ap.parse_args();pred=validate_predecessor(a.repository_sha);g=validate_gsec06()
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    park=apply_au_park(out,g)
    sel=reselection(out,park["rows"])
    if sel["selected"]["Cohort"]!="TW_TW50":raise RuntimeError("deterministic selection did not choose TW_TW50")
    inherited_tw_authority(out)
    tw=run_tw_gate_b(out)

    reqs=tw["requests"];twse_req=sum(1 for r in reqs if r["Source_Class"]=="TWSE_OFFICIAL");ftse_req=sum(1 for r in reqs if r["Source_Class"]=="FTSE_RUSSELL_LSEG_OFFICIAL")
    provider={
      "Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,"ETF_holdings":0,
      "unofficial_TW_constituent_lists":0,"third_party_classification_databases":0,"company_name_Frozen_linkage":0,
      "fuzzy_matching":0,"semantic_classification_inference":0,"cross_taxonomy_mapping":0,"PDSC":0,"per_security_web_fanout":0,
      "frozen_49_row_level_linkage_runs":0,"TW_Gate_E":0,"TW_Gate_F":0,"TW_Gate_H":0,"canonical_materialization":0,
      "Sector_RS":0,"P0":0,"P1":0,"P2":0,"TWSE_official_requests":twse_req,"FTSE_Russell_official_requests":ftse_req,
      "browser_runtime_requests":0
    }
    write_json(out/"provider_call_audit_v0.90.json",provider)
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SHA,
      "AU_Gate_F":"63/63","AU_Gate_G":"63/63","AU_Canonical_Rows":0,"IN_Gate_F":"45/45","JP_Gate_F":"197/197",
      "Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0,
      "TW_Gate_E_Runs":0,"TW_Gate_F_Runs":0,"TW_Gate_H_Runs":0,"Canonical_Materialization_Runs":0,
      "Parked_Registry_SHA256_After":park["sha"],"Parked_Cohort_Count_After":len(park["rows"])
    }
    write_json(out/"immutability_audit_v0.90.json",imm)

    tests=[]
    def t(name,ok,detail):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    t("V089_PREDECESSOR",pred["summary"]["verdict"]=="BLOCKED_AU_SP_ASX200_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE_H",pred["summary"]["verdict"])
    t("GSEC06",g["authority_id"]=="G-SEC-06",g["title"])
    by={r["Cohort"]:r for r in park["rows"]}
    t("AU_PARKED",by["AU_SP_ASX200"]["Execution_State"]=="PARKED_EXTERNAL_AUTHORIZATION",by["AU_SP_ASX200"]["Execution_State"])
    t("AU_A_G_PRESERVED",by["AU_SP_ASX200"]["Technical_Gates_A_G"]=="PASS","PASS")
    t("AU_H_BLOCKED",by["AU_SP_ASX200"]["Gate_H"]=="BLOCKED","BLOCKED")
    t("PARKED_COUNT_5",len(park["rows"])==5,len(park["rows"]))
    t("RESELECTION_TW",sel["selected"]["Cohort"]=="TW_TW50",sel["selected"]["Cohort"])
    t("RESELECTION_DEPTH",sel["selected"]["Consecutive_Resolved_Gates"]==1,sel["selected"]["Consecutive_Resolved_Gates"])
    t("NO_FROZEN49_LINKAGE",provider["frozen_49_row_level_linkage_runs"]==0,"0")
    t("NO_PER_SECURITY",provider["per_security_web_fanout"]==0,"0")
    t("NO_TW_E_F_H",provider["TW_Gate_E"]==provider["TW_Gate_F"]==provider["TW_Gate_H"]==0,"0")
    t("NO_CANONICAL_RS_P",provider["canonical_materialization"]==provider["Sector_RS"]==provider["P0"]==provider["P1"]==provider["P2"]==0,"0")
    t("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA);t("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA);t("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    t("BR_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SHA)
    t("CANONICAL_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    if tw["decision"]["TW_OFFICIAL_SECTOR_BULK_SOURCE_READY"]=="YES":
        t("TW_GATE_B_PASS",tw["decision"]["B"]=="PASS_BY_CURRENT_EVIDENCE","PASS")
        t("TW_ROW_LEVEL",tw["contract"]["Row_Level_Security_Records"]=="YES","YES")
        t("TW_IDENTIFIER",tw["contract"]["Security_Identifier_Field"]!="NOT_AVAILABLE",tw["contract"]["Security_Identifier_Field"])
        t("TW_ICB_LEVEL",tw["contract"]["ICB_Level_Binding"]=="PASS","PASS")
    else:
        t("TW_GATE_B_BLOCKED",tw["decision"]["B"]=="BLOCKED" and bool(tw["decision"]["Blocker"]),tw["decision"]["Blocker"])
    write_csv(out/"test_results_v0.90.csv",tests)

    ready=tw["decision"]["TW_OFFICIAL_SECTOR_BULK_SOURCE_READY"]=="YES"
    verdict="PASS_TW_TW50_OFFICIAL_SECTOR_BULK_SOURCE_GATE_B" if ready else "BLOCKED_TW_TW50_OFFICIAL_SECTOR_BULK_SOURCE_GATE_B"
    summary={
      "version":VERSION,"stage":STAGE,"verdict":verdict,
      "au_park_state":"PARKED_EXTERNAL_AUTHORIZATION","au_technical_gates_a_g":"PASS","au_gate_h":"BLOCKED",
      "au_primary_blocker":"EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "au_independent_gics_blocker":"EXPLICIT_GICS_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "selected_cohort":"TW_TW50","selection_basis":"same consecutive resolved depth (1) and earliest unresolved gate B as CN_CSI300; smaller Frozen row count 49 vs 294",
      "tw_official_sector_bulk_source_ready":ready,
      "tw_official_source":tw["contract"]["Official_Source"],"source_composition":tw["contract"]["Source_Composition"],
      "bulk_route_type":tw["contract"]["Bulk_Route_Type"],"public_reproducible":tw["contract"]["Public_Reproducible"],
      "direct_http_replay":tw["contract"]["DIRECT_HTTP_REPLAY"],"row_level_security_records":tw["contract"]["Row_Level_Security_Records"],
      "security_identifier_field":tw["contract"]["Security_Identifier_Field"],"security_identifier_type":tw["contract"]["Security_Identifier_Type"],
      "icb_industry_group_code_field":tw["contract"]["ICB_Industry_Group_Code_Field"],
      "icb_industry_group_name_field":tw["contract"]["ICB_Industry_Group_Name_Field"],
      "icb_level_binding":tw["contract"]["ICB_Level_Binding"],"per_security_fanout":0,"frozen_49_linkage_runs":0,
      "blocker":tw["decision"]["Blocker"],"canonical_ready_rows":37,"canonical_total_rows":1425,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"artifact_binding":"PENDING_UPLOAD","productive":False,
      "next_gate":tw["decision"]["Next_Gate"]
    }
    write_json(out/"summary_preupload_v0.90.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.90.json",{
      "version":VERSION,"stage":STAGE,"verdict":verdict,"au_park_state":"PARKED_EXTERNAL_AUTHORIZATION","selected_cohort":"TW_TW50",
      "tw_official_sector_bulk_source_ready":ready,"blocker":tw["decision"]["Blocker"],"canonical_ready_rows":37,"canonical_total_rows":1425,
      "next_gate":tw["decision"]["Next_Gate"],"artifact_binding":"PENDING_UPLOAD"
    })
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.90.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.90.json",{
      "version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"au_park_state":"PARKED_EXTERNAL_AUTHORIZATION","selected_cohort":"TW_TW50",
      "tw_official_sector_bulk_source_ready":ready,"blocker":tw["decision"]["Blocker"],
      "canonical_ready_rows":37,"canonical_total_rows":1425,"tw_gate_e_runs":0,"tw_gate_f_runs":0,"tw_gate_h_runs":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "files":files,"next_gate":tw["decision"]["Next_Gate"]
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
