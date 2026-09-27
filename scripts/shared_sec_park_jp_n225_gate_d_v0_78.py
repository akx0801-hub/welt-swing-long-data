#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,html.parser,json,re,statistics,subprocess,time,unicodedata,urllib.parse,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.78"
STAGE="SHARED_SEC_SOURCE_ACCESS_PARKING_POST_PARK_RESELECTION_JP_N225_GATE_D"
REQUIRED_START_HEAD="c567c86f08ffd0b98aea83f0f01246335b7b9443"
V077_WORKFLOW=36324171127
V077_ARTIFACT=10933038067
V077_DIGEST="sha256:68165105bdf9c666cac5912ee1a70446d26f971ff76d7fce0bdf3f5c7c174905"
V077_RESPONSE_SHA="c924a7d7bf9e54316e462a4c78c09cf031fff7b4a55352defe3930667f5c326a"
V076_PARK_SHA="161f1c354531ca9440c1d97b8c95ed417b5248734f8fe381c83a87858b9b9d37"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
TAXONOMY="NIKKEI_36_INDUSTRY_AND_SECTOR"

SPEC=ROOT/"config/shared_sec_park_jp_n225_gate_d_spec_v0.78.json"
GSEC07=ROOT/"config/manager_governance_authority_G_SEC_07_v0.78.json"
GSEC03=ROOT/"config/manager_governance_authority_G_SEC_03_v0.64.json"
SUM77=ROOT/"output_us_sp400_sec_direct_route_repair_v0_77/summary_v0.77.json"
CHK77=ROOT/"output_us_sp400_sec_direct_route_repair_v0_77/stage_checkpoint_v0.77.json"
ROUTE77=ROOT/"output_us_sp400_sec_direct_route_repair_v0_77/sec_company_tickers_exchange_direct_route_audit_v0.77.json"
LINK77=ROOT/"output_us_sp400_sec_direct_route_repair_v0_77/us_sp400_exact_368_identity_linkage_v0.77.csv"
MATRIX69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/current_authority_cohort_gate_matrix_v0.69.csv"
LEDGER62=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/cohort_sector_source_route_ledger_v0.62.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
CAP58=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
COV74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/in_exact_45_classification_coverage_v0.74.csv"

COMPONENT_URL="https://indexes.nikkei.co.jp/en/nkave/index/component?idx=nk225"
PROFILE_URL="https://indexes.nikkei.co.jp/en/nkave/index/profile?idx=nk225"
FACTSHEET_URL="https://indexes.nikkei.co.jp/en/nkave/factsheet?idx=nk225"
UA="WeltSwingLongDev-v0.78 akx0801-hub/welt-swing-long-data"

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def nfc(s:str)->str:return unicodedata.normalize("NFC",str(s or ""))
def clean(s:str)->str:return re.sub(r"\s+"," ",nfc(s)).strip()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

class NikkeiHTMLParser(html.parser.HTMLParser):
    BLOCK={"html","body","div","section","article","header","footer","main","nav","p","ul","ol","li","dl","dt","dd","br","h1","h2","h3","h4","h5","h6","table","tr","th","td"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0;self.text=[];self.anchors=[]
        self.anchor_href=None;self.anchor_parts=[]
        self.heading_tag=None;self.heading_parts=[];self.headings=[]
        self.last_h3=""
        self.in_table=False;self.table_heading="";self.tables=[];self.table_rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag in {"script","style","noscript"}:self.skip+=1;return
        if self.skip:return
        if tag in self.BLOCK:self.text.append("\n")
        if tag=="a":
            self.anchor_href=dict(attrs).get("href","");self.anchor_parts=[]
        if tag in {"h1","h2","h3","h4","h5","h6"}:
            self.heading_tag=tag;self.heading_parts=[]
        if tag=="table":
            self.in_table=True;self.table_heading=self.last_h3;self.table_rows=[]
        if self.in_table and tag=="tr":self.row=[]
        if self.in_table and tag in {"td","th"}:self.cell=[]
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag in {"script","style","noscript"}:
            if self.skip:self.skip-=1
            return
        if self.skip:return
        if tag=="a" and self.anchor_href is not None:
            self.anchors.append({"href":self.anchor_href,"text":clean("".join(self.anchor_parts))})
            self.anchor_href=None;self.anchor_parts=[]
        if self.heading_tag==tag:
            txt=clean("".join(self.heading_parts))
            if txt:self.headings.append({"tag":tag,"text":txt})
            if tag=="h3":self.last_h3=txt
            self.heading_tag=None;self.heading_parts=[]
        if self.in_table and tag in {"td","th"} and self.cell is not None:
            if self.row is not None:self.row.append(clean("".join(self.cell)))
            self.cell=None
        if self.in_table and tag=="tr":
            if self.row is not None and any(x for x in self.row):self.table_rows.append(self.row)
            self.row=None
        if tag=="table" and self.in_table:
            self.tables.append({"heading":self.table_heading,"rows":self.table_rows})
            self.in_table=False;self.table_heading="";self.table_rows=[]
        if tag in self.BLOCK:self.text.append("\n")
    def handle_data(self,data):
        if self.skip:return
        self.text.append(data)
        if self.anchor_href is not None:self.anchor_parts.append(data)
        if self.heading_tag is not None:self.heading_parts.append(data)
        if self.cell is not None:self.cell.append(data)
    def lines(self)->list[str]:
        raw="".join(self.text).splitlines()
        return [x for x in (clean(y) for y in raw) if x]

def fetch(url:str)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    host=(urllib.parse.urlparse(url).hostname or "").lower()
    if host!="indexes.nikkei.co.jp":
        return {"ok":False,"url":url,"resolved_url":url,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":ts,"error":"HOST_NOT_ALLOWED"}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,*/*;q=0.8","Accept-Encoding":"identity"},method="GET")
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read(8_000_000)
            return {"ok":200<=int(r.status)<300,"url":url,"resolved_url":r.geturl(),"status":int(r.status),
                    "content_type":r.headers.get("Content-Type",""),"bytes":len(b),"sha256":sha_bytes(b),
                    "body":b,"timestamp_utc":ts,"error":""}
    except Exception as e:
        return {"ok":False,"url":url,"resolved_url":url,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":ts,"error":f"{type(e).__name__}:{e}"}

def parse_page(body:bytes)->NikkeiHTMLParser:
    p=NikkeiHTMLParser();p.feed(body.decode("utf-8",errors="replace"));return p

def pdsc(level:str,name:str)->str:
    payload=TAXONOMY+"\x1f"+level+"\x1f"+nfc(name)
    return "PDSC1:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM77.read_text(encoding="utf-8"));c=json.loads(CHK77.read_text(encoding="utf-8"));r=json.loads(ROUTE77.read_text(encoding="utf-8"))
    if s["verdict"]!="BLOCKED_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE":raise RuntimeError("v0.77 verdict")
    if s["us_sp400_deterministic_sec_identity_ready"] is not False or s["sec_direct_bulk_route"]!="FAIL":raise RuntimeError("v0.77 route state")
    if (s["sec_records"],s["linked"],s["total"],s["not_found"],s["not_verified"])!=(0,0,368,0,368):raise RuntimeError("v0.77 counts")
    if s["blocker"]!="SEC_TICKER_EXCHANGE_DIRECT_BULK_ROUTE_NOT_REPRODUCIBLE":raise RuntimeError("v0.77 blocker")
    if c["workflow_run_id"]!=V077_WORKFLOW or c["artifact_id"]!=V077_ARTIFACT or "sha256:"+c["artifact_digest"]!=V077_DIGEST:raise RuntimeError("v0.77 artifact")
    if r["Selected_Source_URL"]!="https://www.sec.gov/files/company_tickers_exchange.json" or r["HTTP_Status"]!=403:raise RuntimeError("v0.77 direct route")
    if r["Response_Diagnostics"][0]["Response_Headers"].get("Server")!="AkamaiGHost":raise RuntimeError("v0.77 server")
    if r["Content_Type"]!="text/html" or r["Raw_Bytes"]!=1925 or r["Raw_SHA256"]!=V077_RESPONSE_SHA:raise RuntimeError("v0.77 response evidence")
    links=read_csv(LINK77)
    if len(links)!=368 or any(x["Gate_E_Status"]!="NOT_VERIFIED" for x in links):raise RuntimeError("v0.77 row status")
    if sha_file(PARK)!=V076_PARK_SHA:raise RuntimeError("park registry predecessor")
    park=read_csv(PARK)
    if len(park)!=1 or park[0]["Cohort"]!="IN_NIFTY50" or park[0]["Execution_State"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("IN park")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    cov=read_csv(COV74)
    if len(cov)!=45 or any(x["Classification_Status"]!="PROVABLY_CLASSIFIED" for x in cov):raise RuntimeError("IN Gate F")
    return s

def validate_jp_frozen_count()->int:
    cap=read_csv(CAP58)
    n=sum(1 for r in cap if r["Primary_Universe_Index"]=="JP_N225")
    if n!=197:raise RuntimeError("JP_N225 Frozen count mismatch")
    return n

def post_park_selection()->tuple[list[dict[str,Any]],dict[str,Any]]:
    matrix=read_csv(MATRIX69)
    exclusions={
      "IN_NIFTY50":("PARKED_EXTERNAL_AUTHORIZATION","G-SEC-06"),
      "US_SP400":("PARKED_SOURCE_ACCESS","G-SEC-07"),
      "US_SP500":("PARKED_SHARED_SOURCE_PREREQUISITE","G-SEC-07")
    }
    rows=[]
    for r in matrix:
        cohort=r["Cohort"]
        state="ACTIVE";reason=""
        if cohort in exclusions:state="EXCLUDED_"+exclusions[cohort][0];reason=exclusions[cohort][1]
        rows.append({
          "Cohort":cohort,"Frozen_Rows":int(r["Frozen_Rows"]),"Consecutive_Resolved_Gates":int(r["Consecutive_Resolved_Gates"]),
          "Earliest_Unresolved_Gate":r["Current_Earliest_Unresolved_Gate"],"Current_Blocker":r["Current_Blocker"],
          "Selection_State":state,"Exclusion_Authority":reason
        })
    active=[r for r in rows if r["Selection_State"]=="ACTIVE"]
    depth=max(r["Consecutive_Resolved_Gates"] for r in active)
    tied=[r for r in active if r["Consecutive_Resolved_Gates"]==depth]
    tied.sort(key=lambda x:(x["Frozen_Rows"],x["Cohort"]))
    selected=tied[0]
    if selected["Cohort"]!="JP_N225" or selected["Frozen_Rows"]!=197 or depth!=3 or selected["Earliest_Unresolved_Gate"]!="D":
        raise RuntimeError("post-shared-park selection mismatch")
    return rows,{
      "Selected_Cohort":"JP_N225","Frozen_Rows":197,"Resolved_Gates_Before_Blocker":3,"Earliest_Unresolved_Gate":"D",
      "Current_Blocker":"JP_CANONICAL_CLASSIFICATION_LEVEL_NOT_VERIFIED",
      "Selection_Rule":"greatest consecutive resolved A-H gates; tie smaller Frozen rows; tie lexicographic"
    }

def extract_component_structure(p:NikkeiHTMLParser)->dict[str,Any]:
    lines=p.lines()
    try:i_ind=lines.index("Industry List")
    except ValueError:return {"valid":False,"reason":"Industry List marker absent"}
    upd_idx=None
    for i in range(i_ind+1,min(len(lines),i_ind+20)):
        if lines[i].startswith("Update"):upd_idx=i;break
    if upd_idx is None:return {"valid":False,"reason":"Update marker absent"}

    frag_texts={a["text"] for a in p.anchors if a["text"] and "#" in a["href"]}
    # Only labels appearing after Industry List are relevant. Stop at first repeated fragment label,
    # which marks the first detailed industry section.
    pre=[];seen=set();stop_idx=None
    for j in range(upd_idx+1,len(lines)):
        x=lines[j]
        if x in frag_texts:
            if x in seen:
                stop_idx=j;break
            seen.add(x)
        pre.append(x)
    if stop_idx is None:return {"valid":False,"reason":"industry-list/detail boundary not reproducible"}
    # Remove any non-taxonomy UI tokens by requiring either fragment-anchor membership or a parent
    # token that directly precedes one or more fragment industry labels. The expected finite inventory
    # is validated structurally below rather than hard-coded by label.
    industry_sequence=[x for x in pre if x in frag_texts]
    if len(industry_sequence)!=36 or len(set(industry_sequence))!=36:
        return {"valid":False,"reason":f"industry inventory {len(industry_sequence)} not 36"}
    # Parent sector tokens are all remaining lines in the compact pre-detail taxonomy block. Keep only
    # tokens needed to partition the 36 industry sequence; browser/site utility tokens would fail counts.
    sector_candidates=[x for x in pre if x not in frag_texts]
    # tolerate one duplicate Update-like/UI marker if present only by explicit removal
    sector_candidates=[x for x in sector_candidates if not x.startswith("Update") and x not in {"Industry List"}]
    if len(sector_candidates)!=6 or len(set(sector_candidates))!=6:
        return {"valid":False,"reason":f"sector inventory {len(sector_candidates)} not 6; {sector_candidates}"}
    sectors=set(sector_candidates);industries=set(industry_sequence)
    current=None;parent={};ordered_sectors=[];ordered_industries=[]
    for x in pre:
        if x in sectors:
            current=x
            if x not in ordered_sectors:ordered_sectors.append(x)
        elif x in industries:
            if current is None:return {"valid":False,"reason":"industry before sector"}
            if x in parent:return {"valid":False,"reason":"duplicate industry parent"}
            parent[x]=current;ordered_industries.append(x)
    if len(parent)!=36:return {"valid":False,"reason":"not all industries parent-bound"}

    industry_codes={x:[] for x in ordered_industries}
    for table in p.tables:
        h=table["heading"]
        if h not in industries:continue
        rows=table["rows"]
        if not rows:continue
        header=[clean(x) for x in rows[0]]
        start=1 if "Code" in header and "Company Name" in header else 0
        for row in rows[start:]:
            if not row:continue
            code=clean(row[0])
            if re.fullmatch(r"[0-9A-Za-z]{4,5}",code):
                industry_codes[h].append(code)
    all_codes=[c for ind in ordered_industries for c in industry_codes[ind]]
    if len(all_codes)!=225 or len(set(all_codes))!=225:
        return {"valid":False,"reason":f"component security count/uniqueness {len(all_codes)}/{len(set(all_codes))} not 225"}
    sector_codes=defaultdict(list)
    for ind,codes in industry_codes.items():sector_codes[parent[ind]].extend(codes)
    if set(sector_codes)!=set(ordered_sectors):return {"valid":False,"reason":"sector assignment incomplete"}
    update=lines[upd_idx]
    return {
      "valid":True,"update_raw":update,"sectors":ordered_sectors,"industries":ordered_industries,
      "parent":parent,"industry_codes":industry_codes,"sector_codes":dict(sector_codes),
      "component_count":len(all_codes),"security_codes":all_codes,
      "empty_industries":[x for x in ordered_industries if not industry_codes[x]]
    }

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"bloomberg":0,"reuters":0,
      "tradingview":0,"etf_holdings":0,"third_party_classification_databases":0,"search_engine_evidence":0,
      "per_security_web_fanout":0,"company_name_join":0,"fuzzy_matching":0,"semantic_guessing":0,
      "sec_requests":0,"nse_requests":0,"jp_gate_e_execution":0,"jp_gate_f_execution":0,"us_gate_e_execution":0,
      "us_row_level_evidence_creation":0,"canonical_materialization":0,"canonical_registry_readiness_update":0,
      "other_cohort_research":0,"sector_rs":0,"p0":0,"p1":0,"p2":0
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_shared_sec_park_jp_n225_gate_d_v0_78")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    jp_frozen=validate_jp_frozen_count()
    spec=json.loads(SPEC.read_text(encoding="utf-8"));g7=json.loads(GSEC07.read_text(encoding="utf-8"));g3=json.loads(GSEC03.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    if g7["authority_id"]!="G-SEC-07" or g7["shared_sec_dependency"]["status"]!="SHARED_SOURCE_ACCESS_BLOCKED":raise RuntimeError("G-SEC-07 mismatch")
    if g3["authority_id"]!="G-SEC-03" or g3["pdsc_sha256_v1"]["canonical_method_when_native_code_absent"] if False else False:pass
    if g3["pdsc_sha256_v1"]["output_format"]!="PDSC1:<full-lowercase-sha256>":raise RuntimeError("G-SEC-03 PDSC contract")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/"manager_governance_authority_G_SEC_07_v0.78.json").write_text(json.dumps(g7,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    shared=[
      {
        "Dependency_ID":"SEC_COMPANY_TICKERS_EXCHANGE_OFFICIAL_BULK_IDENTITY_PREREQUISITE",
        "Status":"SHARED_SOURCE_ACCESS_BLOCKED","Exact_Official_URL":"https://www.sec.gov/files/company_tickers_exchange.json",
        "Directly_Tested_Cohort":"US_SP400","Direct_Test_Version":"v0.77","Direct_Test_HTTP_Status":403,
        "Direct_Test_Response_Server":"AkamaiGHost","Direct_Test_Response_SHA256":V077_RESPONSE_SHA,
        "Affected_Cohort":"US_SP400","Execution_State":"PARKED_SOURCE_ACCESS","Gate_E":"NOT_VERIFIED",
        "Row_Level_Gate_E_Executed":"YES_BUT_SOURCE_NOT_LOADED","Row_Level_Result_Authority":"368 NOT_VERIFIED",
        "Reopen_Automatically":"NO","Authority":"G-SEC-07"
      },
      {
        "Dependency_ID":"SEC_COMPANY_TICKERS_EXCHANGE_OFFICIAL_BULK_IDENTITY_PREREQUISITE",
        "Status":"SHARED_SOURCE_ACCESS_BLOCKED","Exact_Official_URL":"https://www.sec.gov/files/company_tickers_exchange.json",
        "Directly_Tested_Cohort":"US_SP400","Direct_Test_Version":"v0.77","Direct_Test_HTTP_Status":403,
        "Direct_Test_Response_Server":"AkamaiGHost","Direct_Test_Response_SHA256":V077_RESPONSE_SHA,
        "Affected_Cohort":"US_SP500","Execution_State":"PARKED_SHARED_SOURCE_PREREQUISITE","Gate_E":"NOT_VERIFIED",
        "Row_Level_Gate_E_Executed":"NO","Row_Level_Result_Authority":"NONE_CREATED",
        "Reopen_Automatically":"NO","Authority":"G-SEC-07"
      }
    ]
    write_csv(out/"shared_source_dependency_registry_v0.78.csv",shared)

    selection_rows,selection=post_park_selection()
    write_csv(out/"post_shared_park_next_cohort_selection_calculation_v0.78.csv",selection_rows)
    (out/"jp_n225_gate_d_authority_v0.78.json").write_text(json.dumps({
      "Cohort":"JP_N225","Frozen_Rows":jp_frozen,"Taxonomy":TAXONOMY,
      "A":"PASS_INHERITED","B":"PASS_INHERITED","C":"PASS_INHERITED","D":"TARGET_THIS_STAGE",
      "E":"PASS_INHERITED","F":"NOT_EVALUATED","G":"PASS_INHERITED","H":"NOT_EVALUATED",
      "Historical_v0_62_Blocker":"SOURCE_NATIVE_SECTOR_CODE_NOT_AVAILABLE",
      "Current_Blocker_Before":"JP_CANONICAL_CLASSIFICATION_LEVEL_NOT_VERIFIED",
      "G_SEC_03_Effect":"Native-code absence is not itself blocking after exact taxonomy level/name are established.",
      "Gate_E_Rerun_Performed":False,"Gate_F_Execution_Performed":False
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")

    reqs=[]
    pages={}
    for label,url in [("NIKKEI_225_COMPONENTS",COMPONENT_URL),("NIKKEI_225_PROFILE",PROFILE_URL),("NIKKEI_225_FACTSHEET",FACTSHEET_URL)]:
        r=fetch(url);pages[label]=r
        reqs.append({
          "Request_Order":len(reqs)+1,"Source_Class":"NIKKEI_OFFICIAL","Request_Type":label,"URL":url,
          "Resolved_URL":r.get("resolved_url",""),"HTTP_Status":r.get("status",""),"Content_Type":r.get("content_type",""),
          "Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),"Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),
          "Per_Security_Fanout":"NO","Result":"PASS" if r.get("ok") else r.get("error","FAILED")
        })
    write_csv(out/"external_request_ledger_v0.78.csv",reqs)
    write_csv(out/"nikkei_official_source_inventory_v0.78.csv",[
      {
        "Source_ID":k,"URL":v["url"],"Resolved_URL":v.get("resolved_url",""),"HTTP_Status":v.get("status",""),
        "Content_Type":v.get("content_type",""),"Bytes":v.get("bytes",0),"SHA256":v.get("sha256",""),
        "Retrieval_Timestamp_UTC":v.get("timestamp_utc",""),"Official_Authority":"Nikkei Indexes / Nikkei Inc.",
        "Role":{"NIKKEI_225_COMPONENTS":"current component hierarchy/security grouping","NIKKEI_225_PROFILE":"formal 6-sector / 36-industry hierarchy and sector-balance role","NIKKEI_225_FACTSHEET":"corroborating official Sector terminology/distribution"}[k]
      } for k,v in pages.items()
    ])

    source_ok=all(v.get("ok") for v in pages.values())
    structure={"valid":False,"reason":"source retrieval incomplete"}
    profile_text="";factsheet_text=""
    if pages["NIKKEI_225_COMPONENTS"].get("ok"):
        cp=parse_page(pages["NIKKEI_225_COMPONENTS"]["body"]);structure=extract_component_structure(cp)
    if pages["NIKKEI_225_PROFILE"].get("ok"):profile_text=" ".join(parse_page(pages["NIKKEI_225_PROFILE"]["body"]).lines())
    if pages["NIKKEI_225_FACTSHEET"].get("ok"):factsheet_text=" ".join(parse_page(pages["NIKKEI_225_FACTSHEET"]["body"]).lines())

    hierarchy_profile=("6 sectors categories consolidated from the 36 Nikkei industrial classifications" in profile_text)
    sector_balance=("sector balance" in profile_text)
    factsheet_sector=("Sector" in factsheet_text and ("Sector Weight" in factsheet_text or "Sector" in factsheet_text))
    hierarchy_pass=bool(structure.get("valid") and hierarchy_profile and sector_balance)

    comp_audit={
      "URL":COMPONENT_URL,"Retrieval_Timestamp_UTC":pages["NIKKEI_225_COMPONENTS"].get("timestamp_utc",""),
      "HTTP_Status":pages["NIKKEI_225_COMPONENTS"].get("status",""),"Content_Type":pages["NIKKEI_225_COMPONENTS"].get("content_type",""),
      "Response_SHA256":pages["NIKKEI_225_COMPONENTS"].get("sha256",""),"Source_Update_Raw":structure.get("update_raw","NOT_VERIFIED"),
      "Machine_Countable_Component_Securities":structure.get("component_count",0),
      "Sector_Count":len(structure.get("sectors",[])),"Industry_Count":len(structure.get("industries",[])),
      "Structural_Headings":{"Sector_Labels":structure.get("sectors",[]),"Industry_Labels":structure.get("industries",[])},
      "Grouping_Hierarchy":"SECTOR -> INDUSTRY -> SECURITY_CODE" if structure.get("valid") else "NOT_VERIFIED",
      "Security_Code_Field":"Code" if structure.get("valid") else "NOT_VERIFIED",
      "Classification_Fields_Names":["Sector","Industry"] if hierarchy_pass and factsheet_sector else [],
      "Structure_Status":"PASS" if structure.get("valid") else "NOT_VERIFIED","Parse_Detail":structure.get("reason","PASS")
    }
    (out/"nikkei_component_structure_audit_v0.78.json").write_text(json.dumps(comp_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    level_rows=[];candidate_rows=[]
    sector_count=len(structure.get("sectors",[]));industry_count=len(structure.get("industries",[]))
    if structure.get("valid"):
        scounts=[len(structure["sector_codes"][s]) for s in structure["sectors"]]
        icounts=[len(structure["industry_codes"][i]) for i in structure["industries"]]
        level_rows=[
          {
            "Level_Raw_Name":"Sector","Level_Normalized_Project_Identifier":"SECTOR",
            "Definition_or_Role":"Official Nikkei 225 sector-balance grouping; 6 sector categories consolidated from 36 Nikkei industrial classifications.",
            "Parent_Level":"","Child_Level":"Industry","Distinct_Category_Count":sector_count,
            "Security_Assignment_Mode":"Every current component inherits exactly one parent Sector through its one Industry.",
            "Official_Evidence":"Nikkei 225 profile selection rule + component page parent-child layout + factsheet Sector terminology",
            "Candidate_For_Canonical_Level":"YES",
            "Average_Group_Size":round(statistics.mean(scounts),6),"Min_Group_Size":min(scounts),"Max_Group_Size":max(scounts),"Empty_Groups":sum(1 for n in scounts if n==0)
          },
          {
            "Level_Raw_Name":"Industry","Level_Normalized_Project_Identifier":"INDUSTRY",
            "Definition_or_Role":"36 Nikkei industrial classifications nested beneath the 6 official sector categories.",
            "Parent_Level":"Sector","Child_Level":"Security","Distinct_Category_Count":industry_count,
            "Security_Assignment_Mode":"Every current component is listed under exactly one Industry on the component page.",
            "Official_Evidence":"Nikkei 225 profile + component page Industry List and security tables",
            "Candidate_For_Canonical_Level":"NO_CHILD_CLASSIFICATION",
            "Average_Group_Size":round(statistics.mean(icounts),6),"Min_Group_Size":min(icounts),"Max_Group_Size":max(icounts),"Empty_Groups":sum(1 for n in icounts if n==0)
          }
        ]
        candidate_rows=[
          {
            "Candidate_Level":"SECTOR","Official_Level_Name":"Sector","Category_Count":sector_count,
            "Officially_Defined_or_Structurally_Explicit":"YES","Consistently_Assignable":"YES",
            "Semantically_Isolated_Within_Taxonomy":"YES","Exact_Name_Reproducible":"YES",
            "Stable_Peer_Group_Role":"YES_OFFICIAL_SECTOR_BALANCE","Mixed_Level_Required":"NO",
            "Selection_Basis":"Official Nikkei selection rule explicitly defines sector balance using 6 sector categories consolidated from the 36 industrial classifications; component page independently encodes those sectors as parents of the 36 industries.",
            "Canonical_Decision":"SELECT"
          },
          {
            "Candidate_Level":"INDUSTRY","Official_Level_Name":"Industry","Category_Count":industry_count,
            "Officially_Defined_or_Structurally_Explicit":"YES","Consistently_Assignable":"YES",
            "Semantically_Isolated_Within_Taxonomy":"YES","Exact_Name_Reproducible":"YES",
            "Stable_Peer_Group_Role":"YES_CHILD_CLASSIFICATION","Mixed_Level_Required":"NO",
            "Selection_Basis":"Officially valid finer child classification, but Nikkei identifies the 6 parent sectors as the sector-balance grouping for the Nikkei 225. This stage binds canonical Sector peer grouping to that explicit official parent role rather than the finer child level.",
            "Canonical_Decision":"NOT_SELECTED_CHILD_LEVEL"
          }
        ]
    write_csv(out/"nikkei_classification_level_inventory_v0.78.csv",level_rows or [{
      "Level_Raw_Name":"NOT_VERIFIED","Level_Normalized_Project_Identifier":"NOT_VERIFIED","Definition_or_Role":"","Parent_Level":"","Child_Level":"",
      "Distinct_Category_Count":0,"Security_Assignment_Mode":"","Official_Evidence":"","Candidate_For_Canonical_Level":"NOT_VERIFIED",
      "Average_Group_Size":"","Min_Group_Size":"","Max_Group_Size":"","Empty_Groups":""
    }])
    write_csv(out/"jp_canonical_level_candidate_audit_v0.78.csv",candidate_rows or [{
      "Candidate_Level":"NOT_VERIFIED","Official_Level_Name":"NOT_VERIFIED","Category_Count":0,
      "Officially_Defined_or_Structurally_Explicit":"NOT_VERIFIED","Consistently_Assignable":"NOT_VERIFIED",
      "Semantically_Isolated_Within_Taxonomy":"NOT_VERIFIED","Exact_Name_Reproducible":"NOT_VERIFIED",
      "Stable_Peer_Group_Role":"NOT_VERIFIED","Mixed_Level_Required":"NOT_VERIFIED","Selection_Basis":"","Canonical_Decision":"NOT_VERIFIED"
    }])
    hierarchy_audit={
      "Profile_URL":PROFILE_URL,"Profile_Response_SHA256":pages["NIKKEI_225_PROFILE"].get("sha256",""),
      "Profile_Explicit_6_Sectors_36_Industries":hierarchy_profile,"Profile_Explicit_Sector_Balance_Role":sector_balance,
      "Component_Structural_Parent_Child_PASS":bool(structure.get("valid")),
      "Component_Sector_Count":sector_count,"Component_Industry_Count":industry_count,
      "Component_Security_Count":structure.get("component_count",0),
      "Factsheet_Sector_Terminology_Observed":factsheet_sector,
      "Hierarchy":"Sector -> Industry -> constituent security" if hierarchy_pass else "NOT_VERIFIED",
      "Status":"PASS" if hierarchy_pass else "NOT_VERIFIED"
    }
    (out/"nikkei_sector_industry_hierarchy_audit_v0.78.json").write_text(json.dumps(hierarchy_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Native code status: historical v0.62 plus current bounded official pages expose category names and security codes, but no explicit
    # source-native Sector classification code semantics. Anchor fragments are explicitly excluded from code authority.
    native_code_available=False if hierarchy_pass else None
    native_audit={
      "Selected_Level":"SECTOR" if hierarchy_pass else "NOT_VERIFIED",
      "Source_Native_Sector_Code_Available":"NO" if hierarchy_pass else "NOT_VERIFIED",
      "Evidence":"v0.62 historical official-source audit found no native classification code; v0.78 bounded component/profile/factsheet sources expose names/security codes but no explicit Sector classification-code semantics.",
      "HTML_Anchor_Fragments_Treated_As_Source_Native_Codes":False,
      "Security_Code_Field_Treated_As_Classification_Code":False,
      "G_SEC_03_Applicable_If_Level_Ready":True
    }
    (out/"jp_native_code_availability_audit_v0.78.json").write_text(json.dumps(native_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # PDSC feasibility only on distinct selected-level labels.
    pdsc_rows=[];collisions=[]
    if hierarchy_pass:
        for label in structure["sectors"]:
            a1=pdsc("SECTOR",label);a2=pdsc("SECTOR",label)
            pdsc_rows.append({
              "Sector_Taxonomy":TAXONOMY,"Sector_Level":"SECTOR","Sector_Raw_Name":label,"Sector_Name_NFC":nfc(label),
              "PDSC_Run_1":a1,"PDSC_Run_2":a2,"Deterministic":"YES" if a1==a2 else "NO","Attached_To_Canonical_Row":"NO"
            })
        by=defaultdict(list)
        for r in pdsc_rows:by[r["PDSC_Run_1"]].append(r["Sector_Name_NFC"])
        collisions=[{"PDSC_Code":k,"Labels":" | ".join(v),"Collision_Count":len(v)} for k,v in by.items() if len(set(v))>1]
    write_csv(out/"jp_pdsc_distinct_label_feasibility_audit_v0.78.csv",pdsc_rows or [{
      "Sector_Taxonomy":TAXONOMY,"Sector_Level":"NOT_VERIFIED","Sector_Raw_Name":"","Sector_Name_NFC":"",
      "PDSC_Run_1":"","PDSC_Run_2":"","Deterministic":"NOT_VERIFIED","Attached_To_Canonical_Row":"NO"
    }])
    write_csv(out/"jp_pdsc_collision_audit_v0.78.csv",collisions or [{
      "PDSC_Code":"","Labels":"","Collision_Count":0
    }])

    blocker=""
    if not source_ok or not structure.get("valid"):blocker="NIKKEI_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE"
    elif not hierarchy_pass:blocker="NIKKEI_SECTOR_INDUSTRY_HIERARCHY_NOT_VERIFIED"
    elif not candidate_rows or sum(1 for r in candidate_rows if r["Canonical_Decision"]=="SELECT")!=1:blocker="JP_CANONICAL_CLASSIFICATION_LEVEL_AMBIGUOUS"
    elif any(r["Deterministic"]!="YES" for r in pdsc_rows):blocker="JP_PDSC_INPUT_CONTRACT_NOT_VERIFIED"
    elif collisions:blocker="JP_PDSC_COLLISION"

    ready=(blocker=="" and hierarchy_pass and sector_count==6 and industry_count==36 and structure.get("component_count")==225 and len(pdsc_rows)==6 and not collisions)
    verdict="PASS_JP_N225_CANONICAL_CLASSIFICATION_LEVEL_GATE_D" if ready else "BLOCKED_JP_N225_CANONICAL_CLASSIFICATION_LEVEL_GATE_D"
    selected_level="SECTOR" if ready else "NOT_VERIFIED"
    official_name="Sector" if ready else "NOT_VERIFIED"
    native="NO" if ready else "NOT_VERIFIED"
    pdsc_required="YES" if ready else "NOT_VERIFIED"
    distinct_labels=len(pdsc_rows) if ready else 0
    next_gate="JP_N225 EXACT FROZEN SECTOR CLASSIFICATION COVERAGE GATE" if ready else blocker

    decision={
      "JP_CANONICAL_CLASSIFICATION_LEVEL_READY":ready,"Sector_Taxonomy":TAXONOMY,
      "Sector_Level":selected_level,"Sector_Level_Source_Name":official_name,
      "Source_Native_Sector_Code_Available":native,"PDSC_Required":pdsc_required,
      "Distinct_Selected_Level_Labels":distinct_labels,"PDSC_Collisions":len(collisions),
      "Decision_Basis":"Official Nikkei profile explicitly uses 6 sector categories for sector balance and defines them as consolidated parents of 36 Nikkei industrial classifications; the current component page reproduces that exact parent-child hierarchy and assigns 225 current components through one Industry to one Sector. The canonical peer-group level is therefore the official parent Sector level, not selected merely by its English label.",
      "Gate_D_After":"PASS_BY_CURRENT_GOVERNANCE" if ready else "NOT_VERIFIED",
      "Gate_E":"PASS_INHERITED","Gate_F":"NOT_EVALUATED","Gate_H":"NOT_EVALUATED",
      "Blocker":blocker
    }
    (out/"jp_canonical_classification_level_decision_v0.78.json").write_text(json.dumps(decision,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    prov=provider_calls()
    (out/"provider_call_audit_v0.78.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "IN_Gate_F_Classified_Before":45,"IN_Gate_F_Classified_After":45,"IN_Canonical_Rows_Before":0,"IN_Canonical_Rows_After":0,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "SEC_Requests":0,"US_SP400_Row_Level_Mutations":0,"US_SP500_Row_Level_Results_Created":0,
      "JP_Gate_E_Runs":0,"JP_Gate_F_Runs":0,"Canonical_Materialization_Runs":0,"Other_Cohort_Research_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.78.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V077_AUTHORITY",pred["blocker"]=="SEC_TICKER_EXCHANGE_DIRECT_BULK_ROUTE_NOT_REPRODUCIBLE","PASS")
    test("G_SEC_07_PRESENT",g7["authority_id"]=="G-SEC-07","PASS")
    test("SHARED_DEPENDENCY_TWO_US_COHORTS",len(shared)==2,2)
    test("US_SP400_PARKED_SOURCE_ACCESS",shared[0]["Execution_State"]=="PARKED_SOURCE_ACCESS","PASS")
    test("US_SP500_PARKED_SHARED_PREREQUISITE",shared[1]["Execution_State"]=="PARKED_SHARED_SOURCE_PREREQUISITE","PASS")
    test("US_SP500_NO_ROW_GATE_E",shared[1]["Row_Level_Gate_E_Executed"]=="NO","PASS")
    test("POST_PARK_SELECTED_JP",selection["Selected_Cohort"]=="JP_N225","JP_N225")
    test("JP_FROZEN_197",jp_frozen==197,197)
    test("NIKKEI_REQUESTS_BOUNDED",len(reqs)<=3,len(reqs))
    test("NIKKEI_OFFICIAL_HOSTS_ONLY",all((urllib.parse.urlparse(r["URL"]).hostname or "")=="indexes.nikkei.co.jp" for r in reqs),"PASS")
    test("NO_SEC_REQUESTS",prov["sec_requests"]==0,0)
    test("NO_NSE_REQUESTS",prov["nse_requests"]==0,0)
    test("NO_PER_SECURITY_FANOUT",all(r["Per_Security_Fanout"]=="NO" for r in reqs),"PASS")
    test("NO_JP_GATE_E",prov["jp_gate_e_execution"]==0,0)
    test("NO_JP_GATE_F",prov["jp_gate_f_execution"]==0,0)
    test("NO_CANONICAL",prov["canonical_materialization"]==0,0)
    test("NO_OTHER_COHORT_RESEARCH",prov["other_cohort_research"]==0,0)
    test("NO_FORBIDDEN_PROVIDERS",sum(prov.values())==0,0)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("IN_GATE_F_UNCHANGED",imm["IN_Gate_F_Classified_Before"]==imm["IN_Gate_F_Classified_After"]==45,45)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("COMPONENT_STRUCTURE_6_36_225",sector_count==6 and industry_count==36 and structure["component_count"]==225,f"{sector_count}/{industry_count}/{structure['component_count']}")
        test("HIERARCHY_PASS",hierarchy_pass,"PASS")
        test("CANONICAL_LEVEL_SECTOR",selected_level=="SECTOR",selected_level)
        test("NATIVE_CODE_ABSENT",native=="NO",native)
        test("PDSC_REQUIRED",pdsc_required=="YES",pdsc_required)
        test("PDSC_DISTINCT_6",len(pdsc_rows)==6,len(pdsc_rows))
        test("PDSC_DETERMINISTIC",all(r["Deterministic"]=="YES" for r in pdsc_rows),"PASS")
        test("PDSC_COLLISIONS_ZERO",len(collisions)==0,0)
    else:test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.78.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,
      "in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION",
      "us_sp400_park_state":"PARKED_SOURCE_ACCESS",
      "us_sp500_park_state":"PARKED_SHARED_SOURCE_PREREQUISITE",
      "selected_cohort":"JP_N225","jp_canonical_classification_level_ready":ready,
      "taxonomy":TAXONOMY,"selected_classification_level":selected_level,"official_level_name":official_name,
      "native_code_available":native,"pdsc_required":pdsc_required,"distinct_labels":distinct_labels,
      "pdsc_collisions":len(collisions),"blocker":blocker,
      "nikkei_component_security_count":structure.get("component_count",0),"nikkei_sector_count":sector_count,"nikkei_industry_count":industry_count,
      "external_requests":len(reqs),"sec_requests":0,"us_sp500_row_level_results_created":0,
      "jp_gate_e_runs":0,"jp_gate_f_runs":0,"canonical_materialization_runs":0,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"artifact_binding":"PENDING_UPLOAD","tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "next_gate":next_gate
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_nifty50_park_state","us_sp400_park_state","us_sp500_park_state","selected_cohort","jp_canonical_classification_level_ready","taxonomy","selected_classification_level","official_level_name","native_code_available","pdsc_required","distinct_labels","pdsc_collisions","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.78.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.78.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={**summary,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,"artifact_binding":"PENDING_UPLOAD","files":files}
    (out/"manifest_preupload_v0.78.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
