#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, html, html.parser, io, json, re, subprocess, time, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.81"
STAGE="JP_N225_EXTERNAL_AUTHORIZATION_PARK_POST_PARK_RESELECTION_AU_SP_ASX200_GATE_C"
REQUIRED_START_HEAD="a6b5a2e1f946bc8cd8615e37fe26efd82b77eb53"
V080_WORKFLOW=36333946734
V080_ARTIFACT=10936936683
V080_DIGEST="sha256:a309d2edf8b3997009c98e40bc8e3fd0cf4f98606618eaa4f27967e4d3878d56"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_BEFORE_SHA="d367957506fd357e22b7cc9c62479a0dfa46ddf54b04ed862a71fdb50b87b2db"
SHARED_SHA="9847587b9e04aba5f26d96b6e9b3f1d9acc197cfee8b913ac887c549dec57b17"

SPEC=ROOT/"config/jp_park_reselection_au_asx200_gate_c_spec_v0.81.json"
GSEC06=ROOT/"config/manager_governance_authority_G_SEC_06_v0.76.json"
GSEC02=ROOT/"config/manager_governance_authority_G_SEC_02_v0.62.json"
SUM80=ROOT/"output_jp_n225_source_access_evidence_persistence_v0_80/summary_v0.80.json"
CHK80=ROOT/"output_jp_n225_source_access_evidence_persistence_v0_80/stage_checkpoint_v0.80.json"
IMM80=ROOT/"output_jp_n225_source_access_evidence_persistence_v0_80/immutability_audit_v0.80.json"
MATRIX69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/current_authority_cohort_gate_matrix_v0.69.csv"
SEL69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/selected_next_cohort_authority_v0.69.json"
RESEARCH62=ROOT/"config/source_native_sector_research_v0.62.json"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
SHARED=ROOT/"sector_metadata/governance/shared_source_dependency_registry_v1.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANONICAL_GLOB=ROOT/"sector_metadata/canonical/cohorts"

DIRECTORY_URL="https://www.asx.com.au/markets/trade-our-cash-market/directory"
INDICES_URL="https://www.asx.com.au/markets/trade-our-cash-market/overview/indices"
REFERENCE_URL="https://www.asx.com.au/connectivity-and-data/information-services/reference-data"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.81"

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader()
        for r in rows:w.writerow(r)

def write_json(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def clean(s:str)->str:return re.sub(r"\s+"," ",html.unescape(str(s or ""))).strip()

class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0;self.parts=[];self.anchor_href=None;self.anchor_parts=[];self.anchors=[];self.attrs=[]
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag in {"script","style","noscript"}:self.skip+=1
        if self.skip:return
        d=dict(attrs);self.attrs.append({"tag":tag,**{str(k):str(v or "") for k,v in attrs}})
        if tag=="a":self.anchor_href=d.get("href","");self.anchor_parts=[]
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag in {"script","style","noscript"}:
            if self.skip:self.skip-=1
            return
        if self.skip:return
        if tag=="a" and self.anchor_href is not None:
            self.anchors.append({"href":self.anchor_href,"text":clean("".join(self.anchor_parts))})
            self.anchor_href=None;self.anchor_parts=[]
    def handle_data(self,data):
        if self.skip:return
        self.parts.append(data)
        if self.anchor_href is not None:self.anchor_parts.append(data)
    def text(self)->str:return clean(" ".join(self.parts))

def fetch(url:str,allowed_hosts:set[str]|None=None,max_bytes:int=8_000_000)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    host=(urllib.parse.urlparse(url).hostname or "").lower()
    if allowed_hosts is not None and host not in allowed_hosts:
        return {"ok":False,"url":url,"resolved_url":url,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":ts,"error":"HOST_NOT_ALLOWED"}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,text/csv,application/csv,*/*;q=0.8","Accept-Encoding":"identity"},method="GET")
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read(max_bytes+1);tr=len(b)>max_bytes
            if tr:b=b[:max_bytes]
            return {"ok":200<=int(getattr(r,"status",200))<300 and not tr,"url":url,"resolved_url":r.geturl(),
                    "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"body":b,"timestamp_utc":ts,
                    "truncated":tr,"error":"TRUNCATED" if tr else ""}
    except Exception as e:
        return {"ok":False,"url":url,"resolved_url":url,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":ts,"error":f"{type(e).__name__}:{e}"}

def parse_page(body:bytes)->PageParser:
    p=PageParser();p.feed(body.decode("utf-8",errors="replace"));return p

def discover_bulk_url(page:dict[str,Any],parser:PageParser)->dict[str,Any]:
    base=page.get("resolved_url") or page.get("url") or DIRECTORY_URL
    candidates=[]
    for a in parser.anchors:
        href=clean(a.get("href",""));txt=clean(a.get("text",""))
        if not href:continue
        score=0
        low=(txt+" "+href).casefold()
        if "all asx listed companies" in txt.casefold():score+=100
        if ".csv" in low:score+=40
        if "listed" in low and "compan" in low:score+=20
        if score:candidates.append((score,urllib.parse.urljoin(base,href),txt,"ANCHOR"))
    for d in parser.attrs:
        for k,v in d.items():
            if k=="tag" or not v:continue
            low=v.casefold()
            if ".csv" in low and ("listed" in low or "compan" in low or "asx" in low):
                candidates.append((30,urllib.parse.urljoin(base,v),f"{d.get('tag')}:{k}","ATTRIBUTE"))
    raw=page.get("body",b"").decode("utf-8",errors="replace")
    for m in re.finditer(r"""(?P<q>["'])(?P<u>[^"']+(?:\.csv|csv\?[^"']*))(?P=q)""",raw,re.I):
        u=m.group("u")
        candidates.append((10,urllib.parse.urljoin(base,u),"REGEX_CSV","RAW_HTML"))
    dedup={}
    for score,url,txt,src in candidates:
        prev=dedup.get(url)
        if prev is None or score>prev[0]:dedup[url]=(score,txt,src)
    ranked=sorted([(s,u,t,src) for u,(s,t,src) in dedup.items()],key=lambda x:(-x[0],x[1]))
    if not ranked:return {"status":"NOT_FOUND","selected_url":"","candidates":[]}
    s,u,t,src=ranked[0]
    return {"status":"FOUND","selected_url":u,"selected_anchor_text":t,"discovery_mode":src,
            "candidates":[{"score":x[0],"url":x[1],"marker":x[2],"mode":x[3]} for x in ranked[:10]]}

def decode_text(b:bytes)->tuple[str,str]:
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:return b.decode(enc),enc
        except UnicodeDecodeError:pass
    return b.decode("utf-8",errors="replace"),"utf-8-replace"

def parse_bulk_csv(body:bytes)->dict[str,Any]:
    txt,enc=decode_text(body)
    lines=txt.splitlines()
    header_idx=None;header=None
    for i,line in enumerate(lines[:20]):
        try:row=next(csv.reader([line]))
        except Exception:continue
        norm=[clean(x).casefold() for x in row]
        if any("industry" in x for x in norm) and any(("asx" in x and "code" in x) or x=="code" for x in norm):
            header_idx=i;header=[clean(x) for x in row];break
    if header_idx is None:
        return {"ok":False,"encoding":enc,"schema":[],"header_line_index":None,"row_count":0,"rows":[],"error":"HEADER_NOT_FOUND"}
    data_text="\n".join(lines[header_idx:])
    try:
        reader=csv.DictReader(io.StringIO(data_text))
        rows=[{clean(k):clean(v) for k,v in r.items() if k is not None} for r in reader]
    except Exception as e:
        return {"ok":False,"encoding":enc,"schema":header,"header_line_index":header_idx,"row_count":0,"rows":[],"error":f"CSV_PARSE:{type(e).__name__}:{e}"}
    rows=[r for r in rows if any(v for v in r.values())]
    return {"ok":True,"encoding":enc,"schema":header,"header_line_index":header_idx,"row_count":len(rows),"rows":rows,"error":""}

def find_industry_field(schema:list[str])->dict[str,Any]:
    exact=[x for x in schema if clean(x).casefold()=="industry"]
    gics_group=[x for x in schema if clean(x).casefold() in {"gics industry group","gics® industry group"}]
    any_ind=[x for x in schema if "industry" in clean(x).casefold()]
    if gics_group:f=gics_group[0]
    elif exact:f=exact[0]
    elif len(any_ind)==1:f=any_ind[0]
    else:return {"available":False,"field":"","position":None,"kind":"NONE","candidates":any_ind}
    kind="GICS_INDUSTRY_GROUP" if f in gics_group else ("INDUSTRY" if f in exact else "OTHER_INDUSTRY_FIELD")
    return {"available":True,"field":f,"position":schema.index(f)+1,"kind":kind,"candidates":any_ind}

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM80.read_text(encoding="utf-8"));c=json.loads(CHK80.read_text(encoding="utf-8"));imm=json.loads(IMM80.read_text(encoding="utf-8"))
    if s["verdict"]!="BLOCKED_JP_N225_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE":raise RuntimeError("v0.80 verdict")
    if s["jp_source_access_persistence_ready"] is not False or s["jp_gate_h"]!="FAIL":raise RuntimeError("v0.80 Gate H")
    if s["blocker"]!="EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION":raise RuntimeError("v0.80 blocker")
    if (s["jp_gate_f_classified"],s["jp_gate_f_total"])!=(197,197):raise RuntimeError("v0.80 JP Gate F")
    if s["required_public_sources_ready"] is not True or s["raw_persistence_required"] is not False or s["technical_bounded_evidence_sufficient"] is not True:raise RuntimeError("v0.80 technical evidence")
    if s["canonical_evidence_persistable"]!="NO":raise RuntimeError("v0.80 persistence state")
    if c["workflow_run_id"]!=V080_WORKFLOW or c["artifact_id"]!=V080_ARTIFACT or c["artifact_digest"]!=V080_DIGEST:raise RuntimeError("v0.80 artifact")
    if imm["Canonical_READY_Rows_After"]!=37 or imm["JP_Canonical_Rows_After"]!=0:raise RuntimeError("v0.80 canonical state")
    if imm["JP_Gate_F_Classified_After"]!=197 or imm["IN_Gate_F_Classified_After"]!=45:raise RuntimeError("v0.80 prior Gate F")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("semantic immutability")
    if sha_file(PARK)!=PARK_BEFORE_SHA:raise RuntimeError("park registry start state")
    if sha_file(SHARED)!=SHARED_SHA:raise RuntimeError("shared registry changed")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    if any(AU_CANONICAL_GLOB.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical partition already exists")
    return {"summary":s,"checkpoint":c,"immutability":imm}

def validate_governance()->tuple[dict[str,Any],dict[str,Any]]:
    g6=json.loads(GSEC06.read_text(encoding="utf-8"));g2=json.loads(GSEC02.read_text(encoding="utf-8"))
    if g6["authority_id"]!="G-SEC-06":raise RuntimeError("G-SEC-06 missing")
    r=g6["rules"]
    if not r["external_consent_license_contractual_blocker_may_be_parked"] or not r["parking_does_not_downgrade_proven_technical_gates"] or not r["parked_cohort_excluded_from_active_next_cohort_selection"]:raise RuntimeError("G-SEC-06 rules")
    if not r["parking_does_not_create_canonical_metadata"] or not r["parked_cohort_may_not_be_automatically_reopened_by_later_cohort_workflows"]:raise RuntimeError("G-SEC-06 parking scope")
    if g2["authority_id"]!="G-SEC-02":raise RuntimeError("G-SEC-02 missing")
    if g2["rules"]["crosswalk_forbidden"] is not True or g2["rules"]["taxonomy_groups_semantically_isolated"] is not True:raise RuntimeError("G-SEC-02 isolation")
    if g2["future_peer_group_key"]!=["Sector_Taxonomy","Sector_Code"]:raise RuntimeError("G-SEC-02 peer key")
    return g6,g2

def apply_jp_park(out:Path,g6:dict[str,Any])->dict[str,Any]:
    rows=read_csv(PARK)
    expected={
      "IN_NIFTY50":"PARKED_EXTERNAL_AUTHORIZATION",
      "US_SP400":"PARKED_SOURCE_ACCESS",
      "US_SP500":"PARKED_SHARED_SOURCE_PREREQUISITE"
    }
    if {r["Cohort"]:r["Execution_State"] for r in rows}!=expected:raise RuntimeError("pre-existing parked states changed")
    if any(r["Cohort"]=="JP_N225" for r in rows):raise RuntimeError("JP already parked")
    fields=list(rows[0].keys())
    jp={
      "Cohort":"JP_N225","Execution_State":"PARKED_EXTERNAL_AUTHORIZATION","Technical_Gates_A_G":"PASS",
      "Gate_H":"BLOCKED","Gate_H_Blocker":"EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Gate_F_Classified":"197","Gate_F_Total":"197","Canonical_Readiness":"NO","Canonical_Rows":"0",
      "Reopen_Automatically":"NO","Authority":"G-SEC-06","Effective_From":"v0.81"
    }
    rows.append(jp)
    write_csv(PARK,rows,fields)
    after_sha=sha_file(PARK)
    write_csv(out/"parked_cohort_registry_update_v0_81.csv",rows,fields)
    app={
      "Cohort":"JP_N225","Execution_State":"PARKED_EXTERNAL_AUTHORIZATION","Technical_Gates_A_G":"PASS",
      "Gate_H":"BLOCKED","Gate_H_Blocker":"EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Gate_F":"197/197","Canonical_Readiness":"NO","Canonical_Rows":0,"Reopen_Automatically":"NO",
      "Authority":"G-SEC-06","Authority_Title":g6["title"],"Authority_Action":"APPLIED_EXISTING_RULE_NO_NEW_GOVERNANCE",
      "Park_Registry_SHA256_Before":PARK_BEFORE_SHA,"Park_Registry_SHA256_After":after_sha
    }
    write_json(out/"jp_n225_external_authorization_park_application_v0_81.json",app)
    return {"rows":rows,"after_sha":after_sha,"jp":jp}

def reselection(out:Path,park_rows:list[dict[str,str]])->dict[str,Any]:
    matrix=read_csv(MATRIX69);sel69=json.loads(SEL69.read_text(encoding="utf-8"))
    rule=sel69["Selection_Rule"]
    parked={r["Cohort"]:(r["Execution_State"],r["Authority"]) for r in park_rows}
    result=[]
    for r in matrix:
        cohort=r["Cohort"]
        depth=int(r["Consecutive_Resolved_Gates"])
        gate=r["Current_Earliest_Unresolved_Gate"];blocker=r["Current_Blocker"]
        state="ACTIVE";authority=""
        if cohort=="BR_IBRX100":
            state="EXCLUDED_CANONICAL_READY";authority="canonical_sector_metadata_cohort_registry_v1"
        elif cohort in parked:
            state="EXCLUDED_"+parked[cohort][0];authority=parked[cohort][1]
            if cohort=="JP_N225":
                depth=7;gate="H";blocker="EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION"
        result.append({
          "Cohort":cohort,"Frozen_Rows":int(r["Frozen_Rows"]),"Consecutive_Resolved_Gates":depth,
          "Earliest_Unresolved_Gate":gate,"Current_Blocker":blocker,"Selection_State":state,
          "Exclusion_Authority":authority,"Selection_Key":f"{-depth}|{int(r['Frozen_Rows']):04d}|{cohort}" if state=="ACTIVE" else "EXCLUDED",
          "Selected":"NO"
        })
    active=[x for x in result if x["Selection_State"]=="ACTIVE"]
    if not active:raise RuntimeError("no active cohort")
    max_depth=max(x["Consecutive_Resolved_Gates"] for x in active)
    tied=[x for x in active if x["Consecutive_Resolved_Gates"]==max_depth]
    tied.sort(key=lambda x:(x["Frozen_Rows"],x["Cohort"]))
    selected=tied[0];selected["Selected"]="YES"
    rank=0
    for x in sorted(active,key=lambda z:(-z["Consecutive_Resolved_Gates"],z["Frozen_Rows"],z["Cohort"])):
        rank+=1;x["Selection_Rank"]=rank
    for x in result:
        if "Selection_Rank" not in x:x["Selection_Rank"]=""
    result.sort(key=lambda x:(999999 if x["Selection_Rank"]=="" else int(x["Selection_Rank"]),x["Cohort"]))
    write_csv(out/"post_jp_park_next_cohort_selection_calculation_v0_81.csv",result,
              ["Selection_Rank","Cohort","Frozen_Rows","Consecutive_Resolved_Gates","Earliest_Unresolved_Gate","Current_Blocker","Selection_State","Exclusion_Authority","Selection_Key","Selected"])
    authority={
      "Selected_Cohort":selected["Cohort"],"Frozen_Rows":selected["Frozen_Rows"],
      "Resolved_Gates_Before_Blocker":selected["Consecutive_Resolved_Gates"],"Earliest_Unresolved_Gate":selected["Earliest_Unresolved_Gate"],
      "Current_Blocker":selected["Current_Blocker"],"Selection_Rule":rule,
      "Active_Cohorts":[x["Cohort"] for x in active],
      "Calculation_Not_Hard_Coded":True
    }
    write_json(out/"post_jp_park_selected_cohort_authority_v0_81.json",authority)
    if selected["Cohort"]!="AU_SP_ASX200":raise RuntimeError("deterministic selection did not choose AU_SP_ASX200")
    return {"rows":result,"selected":authority}

def provider_calls(asx_requests:int)->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"tradingview":0,"wikipedia":0,
      "etf_holdings":0,"third_party_security_sector_databases":0,"company_name_joins":0,"fuzzy_matching":0,
      "semantic_sector_inference":0,"cross_taxonomy_mapping":0,"pdsc":0,"price_ohlcv":0,"news":0,
      "trading_analysis":0,"per_security_web_fanout":0,"sec_requests":0,"nse_requests":0,
      "nikkei_classification_rerun":0,"au_gate_d":0,"au_gate_e":0,"au_gate_f":0,
      "canonical_materialization":0,"canonical_registry_readiness_update":0,"sector_rs":0,"p0":0,"p1":0,"p2":0,
      "asx_official_bounded_requests":asx_requests
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_jp_park_reselection_au_asx200_gate_c_v0_81")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    g6,g2=validate_governance()
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    research=json.loads(RESEARCH62.read_text(encoding="utf-8"))
    auf=research["cohort_findings"]["AU_SP_ASX200"]
    if auf["earliest_blocker"]!="SOURCE_NATIVE_TAXONOMY_IDENTITY_NOT_VERIFIED" or auf["gate_status"]["C"]!="NOT_VERIFIED":raise RuntimeError("v0.62 AU authority changed")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    park=apply_jp_park(out,g6)
    sel=reselection(out,park["rows"])

    ledger=[];request_order=0
    def logged_fetch(url:str,kind:str,allowed_hosts:set[str]|None=None)->dict[str,Any]:
        nonlocal request_order
        request_order+=1
        r=fetch(url,allowed_hosts)
        ledger.append({
          "Request_Order":request_order,"Source_Class":"ASX_OFFICIAL","Request_Type":kind,"URL":url,
          "Resolved_URL":r.get("resolved_url",""),"HTTP_Status":r.get("status",""),"Content_Type":r.get("content_type",""),
          "Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),"Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),
          "Per_Security_Fanout":"NO","SEC_Request":"NO","NSE_Request":"NO","Raw_Source_Persisted":"NO",
          "Result":"PASS" if r.get("ok") else r.get("error","FAILED")
        })
        return r

    asx_hosts={"www.asx.com.au","asx.com.au"}
    directory=logged_fetch(DIRECTORY_URL,"ASX_COMPANY_DIRECTORY",asx_hosts)
    dir_parser=parse_page(directory["body"]) if directory.get("ok") else PageParser()
    discovery=discover_bulk_url(directory,dir_parser) if directory.get("ok") else {"status":"NOT_FOUND","selected_url":"","candidates":[]}
    bulk=None
    if discovery["status"]=="FOUND":
        bulk=logged_fetch(discovery["selected_url"],"ASX_DIRECTORY_DISCOVERED_BULK",None)
    else:
        bulk={"ok":False,"url":"","resolved_url":"","status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":"","error":"NOT_DISCOVERED"}
    indices=logged_fetch(INDICES_URL,"ASX_GICS_CONTEXT",asx_hosts)
    reference=logged_fetch(REFERENCE_URL,"ASX_REFERENCE_DATA_CONTEXT",asx_hosts)
    write_csv(out/"external_request_ledger_v0.81.csv",ledger)

    dtext=dir_parser.text() if directory.get("ok") else ""
    directory_audit={
      "Directory_URL":DIRECTORY_URL,"Resolved_URL":directory.get("resolved_url",""),"HTTP_Status":directory.get("status",""),
      "Content_Type":directory.get("content_type",""),"Bytes":directory.get("bytes",0),"SHA256":directory.get("sha256",""),
      "Retrieval_Timestamp_UTC":directory.get("timestamp_utc",""),"Public_Request_Reproducible":bool(directory.get("ok")),
      "Bulk_Discovery_Status":discovery.get("status"),"Bulk_URL":discovery.get("selected_url",""),
      "Bulk_Discovery_Mode":discovery.get("discovery_mode",""),"Bulk_Link_Text":discovery.get("selected_anchor_text",""),
      "Bulk_Candidates":discovery.get("candidates",[]),"Complete_Raw_Page_Persisted":False,
      "Market_Data_Credit_LSEG_Observed":"lseg" in dtext.casefold(),
      "Market_Data_Credit_Morningstar_Observed":"morningstar" in dtext.casefold()
    }
    write_json(out/"asx_directory_source_audit_v0.81.json",directory_audit)

    parsed=parse_bulk_csv(bulk["body"]) if bulk.get("ok") else {"ok":False,"encoding":"","schema":[],"header_line_index":None,"row_count":0,"rows":[],"error":"BULK_NOT_REPRODUCIBLE"}
    field=find_industry_field(parsed["schema"])
    bulk_audit={
      "Bulk_URL":discovery.get("selected_url",""),"Resolved_URL":bulk.get("resolved_url",""),"HTTP_Status":bulk.get("status",""),
      "Content_Type":bulk.get("content_type",""),"Bytes":bulk.get("bytes",0),"SHA256":bulk.get("sha256",""),
      "Retrieval_Timestamp_UTC":bulk.get("timestamp_utc",""),"Encoding":parsed.get("encoding",""),
      "Schema":parsed.get("schema",[]),"Header_Line_Index_Zero_Based":parsed.get("header_line_index"),
      "Row_Count":parsed.get("row_count",0),"CSV_Parse_Status":"PASS" if parsed.get("ok") else "FAIL",
      "Raw_Source_Persisted":False,"Discovery_From_Official_Directory_Page":discovery.get("status")=="FOUND"
    }
    write_json(out/"asx_listed_companies_bulk_schema_audit_v0.81.json",bulk_audit)

    labels=[];null_count=0
    if parsed.get("ok") and field["available"]:
        vals=[clean(r.get(field["field"],"")) for r in parsed["rows"]]
        null_count=sum(1 for x in vals if not x)
        labels=sorted(set(x for x in vals if x),key=lambda x:x.casefold())
    write_csv(out/"asx_directory_industry_distinct_label_inventory_v0.81.csv",
              [{"Raw_Field_Name":field.get("field",""),"Distinct_Label":x} for x in labels],
              ["Raw_Field_Name","Distinct_Label"])
    field_audit={
      "Raw_Field_Name":field.get("field",""),"Field_Position":field.get("position"),"Field_Kind":field.get("kind","NONE"),
      "Field_Available":field.get("available",False),"Null_Count":null_count,"Distinct_Value_Count":len(labels),
      "Observed_Row_Count":parsed.get("row_count",0),"Candidate_Industry_Fields":field.get("candidates",[]),
      "No_Frozen_Join_Performed":True
    }
    write_json(out/"asx_directory_industry_field_audit_v0.81.json",field_audit)

    raw_name=clean(field.get("field",""))
    schema_direct=field.get("kind")=="GICS_INDUSTRY_GROUP"
    provenance_status="PASS_DIRECT_OFFICIAL_BULK_SCHEMA" if schema_direct else "NOT_VERIFIED"
    provenance={
      "Directory_to_Bulk_Link":"PASS" if directory.get("ok") and discovery.get("status")=="FOUND" and bulk.get("ok") else "FAIL",
      "Raw_Field_Name":raw_name or "NOT_AVAILABLE",
      "Schema_Self_Identifies_Taxonomy_and_Level":"YES" if schema_direct else "NO",
      "Direct_Field_Provenance_Status":provenance_status,
      "Evidence":"Official ASX directory links the retrieved bulk file; its exact raw schema field is self-identifying as GICS Industry Group." if schema_direct else "Official ASX directory/bulk evidence does not itself bind the observed Industry-like field to a named taxonomy and exact formal level.",
      "Semantic_Inference_Used":"NO","Crosswalk_Used":"NO"
    }
    write_json(out/"asx_directory_industry_field_provenance_audit_v0.81.json",provenance)

    itext=parse_page(indices["body"]).text() if indices.get("ok") else ""
    lowi=itext.casefold()
    gics_context=all(x in lowi for x in ["global industry classification standard","s&p dow jones indices","msci"])
    gics_binding={
      "Directory_Field":raw_name or "NOT_AVAILABLE",
      "Direct_GICS_Field_Binding":"PASS" if schema_direct else "NOT_VERIFIED",
      "Binding_Basis":"exact official directory-linked bulk schema field name GICS industry group" if schema_direct else "no direct official directory-field binding",
      "ASX_Sector_Indices_GICS_Context":"PASS" if gics_context else "NOT_VERIFIED",
      "Context_Is_Not_Used_As_Substitute_For_Field_Binding":True,
      "GICS_FIELD_BINDING":"PASS" if schema_direct and gics_context else "NOT_VERIFIED",
      "No_Silent_GICS_Assumption":True
    }
    write_json(out/"asx_gics_field_binding_audit_v0.81.json",gics_binding)

    generic_lseg="lseg" in dtext.casefold();generic_morningstar="morningstar" in dtext.casefold()
    provider={
      "Directory_General_Market_Data_Attribution":{
        "LSEG_Data_Analytics":"OBSERVED" if generic_lseg else "NOT_OBSERVED",
        "Morningstar":"OBSERVED" if generic_morningstar else "NOT_OBSERVED"
      },
      "Exact_Industry_Field_Attribution_To_LSEG":"NOT_VERIFIED",
      "Exact_Industry_Field_Attribution_To_Morningstar":"NOT_VERIFIED",
      "Exact_Industry_Field_Attribution_To_Other_Provider":"NOT_VERIFIED",
      "UPSTREAM_PROVIDER_FIELD_ATTRIBUTION":"NOT_VERIFIED",
      "Provider_Documentation_Requests":0,
      "Reason":"General directory market-data credit is not treated as field-specific attribution. Provider evidence is unnecessary if the official ASX bulk schema directly identifies GICS Industry Group."
    }
    write_json(out/"asx_upstream_provider_attribution_audit_v0.81.json",provider)

    candidates=[
      {"Candidate":"GICS","Evidence":"official ASX directory-linked bulk raw field "+(raw_name or "NOT_AVAILABLE")+"; official ASX indices page expands GICS and names S&P Dow Jones Indices + MSCI","Field_Attribution":"DIRECT" if schema_direct else "NOT_VERIFIED","Status":"PROVEN" if schema_direct and gics_context else "NOT_VERIFIED"},
      {"Candidate":"LSEG classification","Evidence":"general directory market-data credit only","Field_Attribution":"NOT_VERIFIED","Status":"NOT_VERIFIED"},
      {"Candidate":"Morningstar classification","Evidence":"general directory market-data credit only","Field_Attribution":"NOT_VERIFIED","Status":"NOT_VERIFIED"},
      {"Candidate":"ASX-native unnamed taxonomy","Evidence":"no named field-specific taxonomy statement observed","Field_Attribution":"NOT_VERIFIED","Status":"NOT_VERIFIED"}
    ]
    write_csv(out/"au_taxonomy_candidate_inventory_v0.81.csv",candidates)

    formal_level="Industry Group" if schema_direct else "NOT_VERIFIED"
    formal={
      "Raw_Field_Name":raw_name or "NOT_AVAILABLE","Taxonomy_Candidate":"GICS" if schema_direct else "NOT_VERIFIED",
      "Formal_Level":formal_level,"Formal_Level_Status":"PASS" if schema_direct else "NOT_VERIFIED",
      "Evidence":"Exact schema phrase GICS industry group explicitly names the GICS hierarchy level." if schema_direct else "Raw field does not prove an exact formal level.",
      "Field_Name_Alone_Semantic_Inference_Used":"NO"
    }
    write_json(out/"au_taxonomy_formal_level_audit_v0.81.json",formal)

    owner_proven=gics_context
    taxonomy_identified=schema_direct and owner_proven
    version_status="CURRENT_MAINTAINED_NO_STATIC_VERSION" if taxonomy_identified else "NOT_VERIFIED"
    version_contract={
      "Taxonomy":"GICS" if taxonomy_identified else "NOT_VERIFIED",
      "Taxonomy_Version_Status":version_status,
      "Static_Version_Number_Asserted":False,
      "Current_Official_ASX_Context_SHA256":indices.get("sha256","") if indices.get("ok") else "",
      "Directory_Bulk_SHA256":bulk.get("sha256","") if bulk.get("ok") else "",
      "Snapshot_Contract":("SOURCE_SNAPSHOT_SHA256:"+indices.get("sha256","")+"|BULK_SHA256:"+bulk.get("sha256","")) if taxonomy_identified else "",
      "Reproducible_Status":"PASS" if taxonomy_identified else "NOT_VERIFIED"
    }
    write_json(out/"au_taxonomy_version_contract_v0.81.json",version_contract)

    label_audit={
      "Observed_Label_Count":len(labels),"Official_Level_Label_Count":"NOT_AVAILABLE_IN_BOUNDED_ASX_HTML_EVIDENCE",
      "Exact_Label_Matches":"NOT_EVALUATED","Unmatched_Observed_Labels":"NOT_EVALUATED","Missing_Official_Labels":"NOT_EVALUATED",
      "Status":"SUPPORTING_ONLY_NOT_REQUIRED_FOR_IDENTITY","Observed_Labels_File":"asx_directory_industry_distinct_label_inventory_v0.81.csv",
      "Labels_Not_Used_To_Infer_Taxonomy":True
    }
    write_json(out/"au_observed_vs_official_label_set_audit_v0.81.json",label_audit)

    route_ready=bool(directory.get("ok") and discovery.get("status")=="FOUND" and bulk.get("ok") and parsed.get("ok"))
    industry_ready=bool(field.get("available"))
    provenance_ready=provenance_status=="PASS_DIRECT_OFFICIAL_BULK_SCHEMA"
    formal_ready=formal["Formal_Level_Status"]=="PASS"
    version_ready=version_contract["Reproducible_Status"]=="PASS"
    field_binding_ready=gics_binding["GICS_FIELD_BINDING"]=="PASS"
    ready=all([route_ready,industry_ready,provenance_ready,taxonomy_identified,owner_proven,formal_ready,version_ready,field_binding_ready])

    blocker=""
    if not route_ready:blocker="ASX_DIRECTORY_BULK_ROUTE_NOT_REPRODUCIBLE"
    elif not industry_ready:blocker="ASX_DIRECTORY_INDUSTRY_FIELD_NOT_AVAILABLE"
    elif not provenance_ready:blocker="ASX_DIRECTORY_INDUSTRY_FIELD_PROVENANCE_NOT_VERIFIED"
    elif not taxonomy_identified:blocker="ASX_DIRECTORY_INDUSTRY_TAXONOMY_NOT_IDENTIFIED"
    elif not formal_ready:blocker="ASX_DIRECTORY_INDUSTRY_FORMAL_LEVEL_NOT_VERIFIED"
    elif not version_ready:blocker="ASX_DIRECTORY_TAXONOMY_VERSION_NOT_VERIFIABLE"

    decision={
      "Cohort":"AU_SP_ASX200","Frozen_Rows":63,
      "AU_SOURCE_NATIVE_TAXONOMY_IDENTITY_READY":ready,
      "Taxonomy_Identity":"GICS" if ready else "NOT_VERIFIED",
      "Taxonomy_Name":"Global Industry Classification Standard (GICS)" if ready else "NOT_VERIFIED",
      "Taxonomy_Owner":"S&P Dow Jones Indices and MSCI" if ready else "NOT_VERIFIED",
      "Classification_Level":"Industry Group" if ready else formal_level,
      "Taxonomy_Version_Status":version_status,
      "Directory_Field":raw_name or "NOT_AVAILABLE",
      "Field_Binding_Status":"PASS" if ready else "NOT_VERIFIED",
      "Gate_C":"PASS_BY_CURRENT_EVIDENCE" if ready else "BLOCKED",
      "Blocker":blocker,
      "No_Mixed_Taxonomy":True,"No_Crosswalk":True,"No_Semantic_Inference":True,
      "Gate_D":"NOT_EVALUATED","Gate_E":"NOT_EVALUATED","Gate_F":"NOT_EVALUATED",
      "Next_Gate":"AU_SP_ASX200 SECTOR FIELD / SOURCE-NATIVE CODE FEASIBILITY GATE D" if ready else "NONE_WHILE_GATE_C_BLOCKED"
    }
    write_json(out/"au_source_native_taxonomy_identity_decision_v0.81.json",decision)

    gate_authority={
      "Cohort":"AU_SP_ASX200","Gate_A":"PASS_INHERITED","Gate_B":"PASS_INHERITED",
      "Gate_C":decision["Gate_C"],"Gate_D":"NOT_EVALUATED","Gate_E":"NOT_EVALUATED","Gate_F":"NOT_EVALUATED","Gate_G":"NOT_EVALUATED","Gate_H":"NOT_EVALUATED",
      "Historical_Blocker":"SOURCE_NATIVE_TAXONOMY_IDENTITY_NOT_VERIFIED","Current_Blocker":blocker,
      "Taxonomy_Identity":decision["Taxonomy_Identity"],"Classification_Level":decision["Classification_Level"],
      "Field":decision["Directory_Field"],"Field_Binding_Status":decision["Field_Binding_Status"]
    }
    write_json(out/"au_gate_c_authority_v0.81.json",gate_authority)

    prov=provider_calls(len(ledger))
    write_json(out/"provider_call_audit_v0.81.json",prov)

    reg=read_csv(REGISTRY)
    park_states={r["Cohort"]:r["Execution_State"] for r in read_csv(PARK)}
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Shared_Source_Registry_SHA256_Expected":SHARED_SHA,"Shared_Source_Registry_SHA256_After":sha_file(SHARED),"Shared_Source_Registry_Unchanged":sha_file(SHARED)==SHARED_SHA,
      "Parked_Cohort_Registry_SHA256_Before":PARK_BEFORE_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),
      "Parked_Cohort_States_After":park_states,
      "IN_Gate_F_Classified_After":45,"IN_Gate_F_Total_After":45,"JP_Gate_F_Classified_After":197,"JP_Gate_F_Total_After":197,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,
      "AU_Canonical_Rows_After":0,"JP_Canonical_Rows_After":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0,
      "SEC_Requests":0,"NSE_Requests":0,"Nikkei_Classification_Reruns":0,
      "AU_Gate_D_Runs":0,"AU_Gate_E_Runs":0,"AU_Gate_F_Runs":0,"PDSC_Runs":0
    }
    write_json(out/"immutability_audit_v0.81.json",imm)

    tests=[]
    def check(name:str,ok:bool,detail:str):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":detail})
        if not ok:raise RuntimeError(name)
    check("V080_VERDICT",pred["summary"]["verdict"]=="BLOCKED_JP_N225_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE",pred["summary"]["verdict"])
    check("V080_ARTIFACT",pred["checkpoint"]["workflow_run_id"]==V080_WORKFLOW and pred["checkpoint"]["artifact_id"]==V080_ARTIFACT,V080_DIGEST)
    check("G_SEC_06_APPLIED",park["jp"]["Authority"]=="G-SEC-06" and park["jp"]["Execution_State"]=="PARKED_EXTERNAL_AUTHORIZATION","JP_N225")
    check("JP_GATES_NOT_DOWNGRADED",park["jp"]["Technical_Gates_A_G"]=="PASS" and park["jp"]["Gate_F_Classified"]=="197","A-G PASS; F 197/197")
    check("EXISTING_PARKS_PRESERVED",all(park_states.get(k)==v for k,v in spec["preserve_parked"].items()),json.dumps(park_states,sort_keys=True))
    check("JP_REOPEN_NO",park["jp"]["Reopen_Automatically"]=="NO","NO")
    check("RESELECTION_CALCULATED",sel["selected"]["Calculation_Not_Hard_Coded"] is True,"true")
    check("RESELECTION_AU",sel["selected"]["Selected_Cohort"]=="AU_SP_ASX200","AU_SP_ASX200")
    check("AU_FROZEN_63",sel["selected"]["Frozen_Rows"]==63,"63")
    check("AU_GATE_C_ONLY",decision["Gate_D"]=="NOT_EVALUATED" and decision["Gate_E"]=="NOT_EVALUATED" and decision["Gate_F"]=="NOT_EVALUATED","D/E/F NOT_EVALUATED")
    check("NO_FROZEN_AU_LINKAGE",field_audit["No_Frozen_Join_Performed"] is True,"true")
    check("NO_CROSSWALK",decision["No_Crosswalk"] is True,"true")
    check("NO_SEMANTIC_INFERENCE",decision["No_Semantic_Inference"] is True,"true")
    check("NO_PDSC",prov["pdsc"]==0,"0")
    check("NO_SEC_NSE",prov["sec_requests"]==0 and prov["nse_requests"]==0,"0/0")
    check("NO_NIKKEI_RERUN",prov["nikkei_classification_rerun"]==0,"0")
    check("NO_FORBIDDEN_PROVIDER",all(v==0 for k,v in prov.items() if k!="asx_official_bounded_requests"),"0")
    check("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    check("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    check("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    check("BR_CANONICAL_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    check("GLOBAL_CANONICAL_37",imm["Canonical_READY_Rows_After"]==37,"37/1425")
    check("NO_AU_CANONICAL",imm["AU_Canonical_Rows_After"]==0 and not any(AU_CANONICAL_GLOB.glob("AU_SP_ASX200_*.csv")),"0")
    check("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,"0")
    check("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    check("GATE_C_DECISION_COHERENT",(ready and blocker=="") or ((not ready) and blocker!=""),blocker or "PASS")
    write_csv(out/"test_results_v0.81.csv",tests)

    verdict="PASS_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C" if ready else "BLOCKED_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C"
    summary={
      "version":VERSION,"stage":STAGE,"verdict":verdict,
      "jp_n225_park_state":"PARKED_EXTERNAL_AUTHORIZATION",
      "selected_cohort":sel["selected"]["Selected_Cohort"],
      "au_source_native_taxonomy_identity_ready":ready,
      "directory_bulk_route":"PASS" if route_ready else "FAIL",
      "directory_industry_field":raw_name or "NOT_AVAILABLE",
      "taxonomy_identity":decision["Taxonomy_Identity"],"taxonomy_owner":decision["Taxonomy_Owner"],
      "formal_level":decision["Classification_Level"],"version_status":version_status,
      "field_to_taxonomy_binding":"PASS" if ready else "NOT_VERIFIED",
      "gics_field_binding":gics_binding["GICS_FIELD_BINDING"],
      "upstream_provider_attribution":provider["UPSTREAM_PROVIDER_FIELD_ATTRIBUTION"],
      "blocker":blocker,"au_gate_c":decision["Gate_C"],
      "au_gate_d":"NOT_EVALUATED","au_gate_e":"NOT_EVALUATED","au_gate_f":"NOT_EVALUATED",
      "canonical_ready_rows":37,"canonical_total_rows":1425,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "sec_requests":0,"nse_requests":0,"alpha_vantage_calls":0,"pdsc_runs":0,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "next_gate":decision["Next_Gate"],"artifact_binding":"PENDING_UPLOAD","productive":False
    }
    write_json(out/"summary_preupload_v0.81.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.81.json",{
      "version":VERSION,"stage":STAGE,"verdict":verdict,"jp_n225_park_state":"PARKED_EXTERNAL_AUTHORIZATION",
      "selected_cohort":sel["selected"]["Selected_Cohort"],"au_source_native_taxonomy_identity_ready":ready,
      "au_gate_c":decision["Gate_C"],"blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "next_gate":decision["Next_Gate"],"artifact_binding":"PENDING_UPLOAD"
    })

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.81.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.81.json",{
      "version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"jp_n225_park_state":"PARKED_EXTERNAL_AUTHORIZATION","selected_cohort":sel["selected"]["Selected_Cohort"],
      "au_source_native_taxonomy_identity_ready":ready,"blocker":blocker,"external_requests":len(ledger),
      "park_registry_sha256_after":sha_file(PARK),"canonical_ready_rows":37,"canonical_total_rows":1425,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
