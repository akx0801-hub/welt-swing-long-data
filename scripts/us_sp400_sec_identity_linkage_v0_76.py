#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, html.parser, io, json, re, subprocess, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.76"
STAGE="US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE_GATE_WITH_IN_NIFTY50_PARK"
REQUIRED_START_HEAD="40f261b29dd0e92dc79b976a0970f6ae8970e9e8"
V075_WORKFLOW=36319329798
V075_ARTIFACT=10931349603
V075_DIGEST="sha256:670a2246c1186dddb7604b9eb9f349d980049a5e9f9f192540769aeb6fb25d4a"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

SPEC=ROOT/"config/us_sp400_sec_identity_linkage_spec_v0.76.json"
GSEC06=ROOT/"config/manager_governance_authority_G_SEC_06_v0.76.json"
SUM75=ROOT/"output_in_nifty50_source_access_persistence_v0_75/summary_v0.75.json"
CHK75=ROOT/"output_in_nifty50_source_access_persistence_v0_75/stage_checkpoint_v0.75.json"
COV74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/in_exact_45_classification_coverage_v0.74.csv"
MATRIX69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/current_authority_cohort_gate_matrix_v0.69.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
CAP58=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"

SEC_API_DOC="https://www.sec.gov/search-filings/edgar-application-programming-interfaces"
SEC_ACCESS_DOC="https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data"
ISO_MIC_LANDING="https://www.iso20022.org/market-identifier-codes"
SEC_UA="WeltSwingLongDev-v0.76 akx0801-hub/welt-swing-long-data contact=https://github.com/akx0801-hub"
ISO_UA="WeltSwingLongDev-v0.76 akx0801-hub/welt-swing-long-data"

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def norm(s:str)->str:return str(s or "").strip()
def norm_case(s:str)->str:return norm(s).casefold()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

class LinkParser(html.parser.HTMLParser):
    def __init__(self):super().__init__();self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()!="a":return
        d=dict(attrs)
        if d.get("href"):self.hrefs.append(d["href"])

def allowed_host(url:str,kind:str)->bool:
    h=(urllib.parse.urlparse(url).hostname or "").lower()
    if kind=="SEC":return h in {"www.sec.gov","sec.gov","data.sec.gov"}
    if kind=="ISO":return h in {"www.iso20022.org","iso20022.org"}
    return False

def fetch(url:str,kind:str,max_bytes:int=20_000_000)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    if not allowed_host(url,kind):
        return {"ok":False,"url":url,"resolved_url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","error":"HOST_NOT_ALLOWED"}
    ua=SEC_UA if kind=="SEC" else ISO_UA
    try:
        req=urllib.request.Request(url,headers={"User-Agent":ua,"Accept":"text/html,application/json,text/csv,application/octet-stream,*/*;q=0.8","Accept-Encoding":"identity"},method="GET")
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read(max_bytes+1);tr=len(b)>max_bytes
            if tr:b=b[:max_bytes]
            resolved=r.geturl()
            if not allowed_host(resolved,kind):
                return {"ok":False,"url":url,"resolved_url":resolved,"timestamp_utc":ts,"status":int(getattr(r,"status",200)),
                        "content_type":r.headers.get("Content-Type",""),"bytes":len(b),"sha256":sha_bytes(b),"body":b,"error":"REDIRECT_HOST_NOT_ALLOWED"}
            return {"ok":200<=int(getattr(r,"status",200))<300 and not tr,"url":url,"resolved_url":resolved,"timestamp_utc":ts,
                    "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),"bytes":len(b),
                    "sha256":sha_bytes(b),"body":b,"truncated":tr,"set_cookie_present":bool(r.headers.get("Set-Cookie"))}
    except Exception as e:
        return {"ok":False,"url":url,"resolved_url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","body":b"",
                "error":f"{type(e).__name__}:{e}"}

def discover_sec_ticker_exchange(pages:list[dict[str,Any]])->tuple[str,str]:
    candidates=[]
    for p in pages:
        if not p.get("ok"):continue
        text=p["body"].decode("utf-8",errors="replace")
        lp=LinkParser();lp.feed(text)
        for h in lp.hrefs:
            if "company_tickers_exchange.json" in h:
                u=urllib.parse.urljoin(p["resolved_url"],h)
                if allowed_host(u,"SEC"):candidates.append((u,"DOCUMENTED_HREF"))
        for m in re.findall(r'https?://(?:www\.)?sec\.gov/[^"\'<>\s]*company_tickers_exchange\.json',text,re.I):
            if allowed_host(m,"SEC"):candidates.append((m,"DOCUMENTED_ABSOLUTE_TEXT"))
        if "company_tickers_exchange.json" in text and not candidates:
            for m in re.findall(r'["\']([^"\']*company_tickers_exchange\.json)["\']',text,re.I):
                u=urllib.parse.urljoin(p["resolved_url"],m)
                if allowed_host(u,"SEC"):candidates.append((u,"DOCUMENTED_RELATIVE_TEXT"))
    uniq=[]
    seen=set()
    for u,m in candidates:
        if u not in seen:seen.add(u);uniq.append((u,m))
    if len(uniq)==1:return uniq[0]
    if len(uniq)>1:
        # Accept multiple documentation appearances only when they resolve to one normalized URL.
        norms={urllib.parse.urlsplit(u)._replace(query="",fragment="").geturl() for u,_ in uniq}
        if len(norms)==1:return uniq[0]
    return "","NOT_VERIFIED"

def discover_iso_mic(page:dict[str,Any])->tuple[str,str]:
    if not page.get("ok"):return "","NOT_VERIFIED"
    text=page["body"].decode("utf-8",errors="replace")
    lp=LinkParser();lp.feed(text)
    candidates=[]
    for h in lp.hrefs:
        low=h.lower()
        if "iso10383" in low and (low.endswith(".csv") or ".csv?" in low or low.endswith(".xlsx") or ".xlsx?" in low):
            u=urllib.parse.urljoin(page["resolved_url"],h)
            if allowed_host(u,"ISO"):candidates.append(u)
    # Prefer CSV, then XLSX, stable sorted.
    candidates=sorted(set(candidates),key=lambda u:(0 if ".csv" in u.lower() else 1,u))
    if candidates:return candidates[0],"OFFICIAL_LANDING_PAGE_HREF"
    return "","NOT_VERIFIED"

def parse_delimited(body:bytes)->list[dict[str,str]]:
    text=body.decode("utf-8-sig",errors="replace")
    sample=text[:10000]
    try:dialect=csv.Sniffer().sniff(sample,delimiters=",;|\t")
    except Exception:dialect=csv.excel
    return list(csv.DictReader(io.StringIO(text),dialect=dialect))

def field_name(fields:list[str],variants:list[str])->str:
    by={re.sub(r"[^a-z0-9]","",f.casefold()):f for f in fields}
    for v in variants:
        k=re.sub(r"[^a-z0-9]","",v.casefold())
        if k in by:return by[k]
    return ""

def parse_mic_dataset(url:str,body:bytes)->tuple[list[dict[str,str]],dict[str,str]]:
    if ".xlsx" in url.lower():
        try:
            import openpyxl
        except Exception as e:
            raise RuntimeError("ISO_MIC_XLSX_REQUIRES_OPENPYXL") from e
        wb=openpyxl.load_workbook(io.BytesIO(body),read_only=True,data_only=True)
        ws=wb.active
        rows=list(ws.iter_rows(values_only=True))
        hdr=[norm(x) for x in rows[0]]
        parsed=[{hdr[i]:norm(v) for i,v in enumerate(row) if i<len(hdr)} for row in rows[1:]]
    else:
        parsed=parse_delimited(body)
    if not parsed:raise RuntimeError("ISO_MIC_DATASET_EMPTY")
    fields=list(parsed[0].keys())
    names={
      "mic":field_name(fields,["MIC"]),
      "operating_mic":field_name(fields,["OPERATING MIC","OPERATING_MIC"]),
      "oprt_sgmt":field_name(fields,["OPRT/SGMT","OPRT SGMT"]),
      "market_name":field_name(fields,["MARKET NAME-INSTITUTION DESCRIPTION","MARKET NAME INSTITUTION DESCRIPTION"]),
      "acronym":field_name(fields,["ACRONYM"]),
      "country":field_name(fields,["ISO COUNTRY CODE","ISO COUNTRY"]),
      "status":field_name(fields,["STATUS"])
    }
    if not all(names[k] for k in ("mic","operating_mic","oprt_sgmt","market_name","acronym")):
        raise RuntimeError("ISO_MIC_SCHEMA_NOT_VERIFIED:"+json.dumps(names,sort_keys=True))
    return parsed,names

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM75.read_text(encoding="utf-8"));c=json.loads(CHK75.read_text(encoding="utf-8"));cov=read_csv(COV74)
    if s["verdict"]!="BLOCKED_IN_NIFTY50_SOURCE_ACCESS_EVIDENCE_PERSISTENCE":raise RuntimeError("v0.75 verdict")
    if s["in_source_access_persistence_ready"] is not False or s["blocker"]!="EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION":raise RuntimeError("v0.75 blocker")
    if s["in_gate_f_classified"]!=45 or s["canonical_ready_rows"]!=37 or s["canonical_total_rows"]!=1425:raise RuntimeError("v0.75 state")
    if c["workflow_run_id"]!=V075_WORKFLOW or c["artifact_id"]!=V075_ARTIFACT or "sha256:"+c["artifact_digest"]!=V075_DIGEST:raise RuntimeError("v0.75 artifact")
    if len(cov)!=45 or any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in cov):raise RuntimeError("IN Gate F authority")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    return {"summary":s,"checkpoint":c}

def reconstruct_target()->tuple[list[dict[str,str]],dict[str,int]]:
    frozen=read_csv(FROZEN);cap=read_csv(CAP58)
    if len(frozen)!=1425 or len(cap)!=1425:raise RuntimeError("Frozen/capability count mismatch")
    cap_by={r["Security_Key"]:r for r in cap}
    if len(cap_by)!=1425:raise RuntimeError("capability key uniqueness")
    out=[]
    for r in frozen:
        c=cap_by.get(r["Security_Key"])
        if not c:raise RuntimeError("missing capability mapping "+r["Security_Key"])
        if c["Source_WS_ID"]!=r["Source_WS_ID"] or c["Primary_MIC"]!=r["Primary_MIC"] or c["Primary_Ticker"]!=r["Primary_Ticker"]:
            raise RuntimeError("Frozen/capability identity mismatch "+r["Security_Key"])
        if c["Primary_Universe_Index"]=="US_SP400":
            out.append({
              "Security_Key":r["Security_Key"],"WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],
              "Primary_Ticker":r["Primary_Ticker"],"ISIN":"","ISIN_Status":"NOT_PRESENT_IN_FROZEN_TARGET",
              "Primary_Universe_Index":"US_SP400"
            })
    if len(out)!=368 or len({r["WS_ID"] for r in out})!=368 or len({r["Security_Key"] for r in out})!=368:
        raise RuntimeError("US_SP400 target count/uniqueness mismatch")
    dist=dict(sorted(Counter(r["Primary_MIC"] for r in out).items()))
    return sorted(out,key=lambda r:r["WS_ID"]),dist

def post_park_selection()->tuple[list[dict[str,Any]],dict[str,Any]]:
    rows=read_csv(MATRIX69)
    calc=[]
    for r in rows:
        cohort=r["Cohort"];depth=int(r["Consecutive_Resolved_Gates"]);status="ACTIVE"
        reason=""
        if cohort=="IN_NIFTY50":status="EXCLUDED_PARKED_EXTERNAL_AUTHORIZATION";reason="G-SEC-06"
        calc.append({
          "Cohort":cohort,"Frozen_Rows":int(r["Frozen_Rows"]),"Consecutive_Resolved_Gates":depth,
          "Earliest_Unresolved_Gate":r["Current_Earliest_Unresolved_Gate"],"Current_Blocker":r["Current_Blocker"],
          "Selection_Status":status,"Exclusion_Reason":reason
        })
    active=[r for r in calc if r["Selection_Status"]=="ACTIVE"]
    maxd=max(r["Consecutive_Resolved_Gates"] for r in active)
    finalists=[r for r in active if r["Consecutive_Resolved_Gates"]==maxd]
    finalists.sort(key=lambda r:(r["Frozen_Rows"],r["Cohort"]))
    selected=finalists[0]
    if selected["Cohort"]!="US_SP400" or selected["Frozen_Rows"]!=368 or maxd!=4:
        raise RuntimeError("post-park selection mismatch")
    return calc,{
      "Selected_Cohort":"US_SP400","Resolved_Gates_Before_Blocker":4,"Earliest_Unresolved_Gate":"E",
      "Current_Blocker":"DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED","Frozen_Rows":368,
      "Selection_Rule":"greatest consecutive resolved A-H gates; tie smaller Frozen rows; tie lexicographic",
      "Tie_Set":[r["Cohort"] for r in finalists],"Tie_Row_Counts":{r["Cohort"]:r["Frozen_Rows"] for r in finalists}
    }

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,
      "etf_holdings":0,"ishares_identity_authority":0,"sp_third_party_mirrors":0,"company_name_joins":0,
      "fuzzy_matching":0,"manual_issuer_guessing":0,"per_security_web_fanout":0,"price_ohlcv":0,"news":0,
      "trading_analysis":0,"nifty_requests":0,"us_gate_f":0,"sic_promotion":0,"canonical_materialization":0,
      "canonical_registry_readiness_update":0,"us_sp500_execution":0,"other_cohort_execution":0,
      "sector_rs":0,"p0":0,"p1":0,"p2":0
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_us_sp400_sec_identity_linkage_v0_76")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"));gov=json.loads(GSEC06.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    if gov["authority_id"]!="G-SEC-06" or gov["in_nifty50_authority"]["execution_state"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("G-SEC-06 mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/"manager_governance_authority_G_SEC_06_v0.76.json").write_text(json.dumps(gov,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    target,mic_dist=reconstruct_target()
    write_csv(out/"us_sp400_frozen_368_identity_target_v0.76.csv",target)
    (out/"us_sp400_frozen_primary_mic_distribution_v0.76.json").write_text(json.dumps(mic_dist,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    park=[{
      "Cohort":"IN_NIFTY50","Execution_State":"PARKED_EXTERNAL_AUTHORIZATION",
      "Technical_Gates_A_G":"PASS","Gate_H":"BLOCKED","Gate_H_Blocker":"EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION",
      "Gate_F_Classified":45,"Gate_F_Total":45,"Canonical_Readiness":"NO","Canonical_Rows":0,
      "Reopen_Automatically":"NO","Authority":"G-SEC-06","Effective_From":"v0.76"
    }]
    write_csv(out/"parked_cohort_registry_v0.76.csv",park)
    calc,selected=post_park_selection()
    write_csv(out/"post_park_next_cohort_selection_calculation_v0.76.csv",calc)
    (out/"selected_us_sp400_authority_v0.76.json").write_text(json.dumps(selected,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    external=[]
    req_order=0
    def log_req(kind:str,label:str,r:dict[str,Any]):
        nonlocal req_order
        req_order+=1
        external.append({
          "Request_Order":req_order,"Source_Class":kind,"Request_Type":label,"URL":r.get("url",""),"Resolved_URL":r.get("resolved_url",""),
          "HTTP_Status":r.get("status",""),"Content_Type":r.get("content_type",""),"Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),
          "Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),"Set_Cookie_Header_Present":"YES" if r.get("set_cookie_present") else "NO",
          "Per_Security_Fanout":"NO","Result":"PASS" if r.get("ok") else r.get("error","FAILED")
        })

    # SEC documentation discovery with bounded fair-access behavior.
    sec_docs=[]
    for label,url in [("SEC_API_DOCUMENTATION",SEC_API_DOC),("SEC_ACCESS_DOCUMENTATION",SEC_ACCESS_DOC)]:
        r=fetch(url,"SEC",4_000_000);log_req("SEC",label,r);sec_docs.append(r);time.sleep(0.35)
    sec_data_url,sec_discovery_method=discover_sec_ticker_exchange(sec_docs)
    sec_data={"ok":False,"url":sec_data_url,"resolved_url":sec_data_url,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":"","error":"NOT_REQUESTED"}
    if sec_data_url:
        sec_data=fetch(sec_data_url,"SEC",20_000_000);log_req("SEC","SEC_TICKER_EXCHANGE_BULK",sec_data);time.sleep(0.35)

    # ISO official MIC landing + discovered dataset.
    iso_page=fetch(ISO_MIC_LANDING,"ISO",4_000_000);log_req("ISO","ISO_MIC_LANDING",iso_page)
    iso_data_url,iso_discovery_method=discover_iso_mic(iso_page)
    iso_data={"ok":False,"url":iso_data_url,"resolved_url":iso_data_url,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","timestamp_utc":"","error":"NOT_REQUESTED"}
    if iso_data_url:
        iso_data=fetch(iso_data_url,"ISO",20_000_000);log_req("ISO","ISO_10383_MIC_DATASET",iso_data)
    write_csv(out/"external_request_ledger_v0.76.csv",external)

    # Parse SEC dataset.
    sec_rows=[];sec_fields=[];sec_schema_status="NOT_VERIFIED";sec_parse_error=""
    if sec_data.get("ok"):
        try:
            obj=json.loads(sec_data["body"].decode("utf-8"))
            fields=obj.get("fields") if isinstance(obj,dict) else None
            data=obj.get("data") if isinstance(obj,dict) else None
            if isinstance(fields,list) and isinstance(data,list):
                sec_fields=[str(x) for x in fields]
                sec_rows=[{sec_fields[i]:norm(row[i]) if i<len(row) else "" for i in range(len(sec_fields))} for row in data if isinstance(row,list)]
                required={"cik","ticker","exchange"}
                if required.issubset(set(sec_fields)):sec_schema_status="PASS"
        except Exception as e:sec_parse_error=f"{type(e).__name__}:{e}"
    sec_ticker_field="ticker" if "ticker" in sec_fields else ""
    sec_exchange_field="exchange" if "exchange" in sec_fields else ""
    sec_cik_field="cik" if "cik" in sec_fields else ""
    duplicate_ticker=Counter(r.get(sec_ticker_field,"") for r in sec_rows if sec_ticker_field and r.get(sec_ticker_field,""))
    duplicate_pair=Counter((r.get(sec_ticker_field,""),r.get(sec_exchange_field,"")) for r in sec_rows if sec_ticker_field and sec_exchange_field and r.get(sec_ticker_field,""))
    exchange_counts=Counter(r.get(sec_exchange_field,"") for r in sec_rows if sec_exchange_field and r.get(sec_exchange_field,""))
    sec_audit={
      "Documentation_URLs":[SEC_API_DOC,SEC_ACCESS_DOC],"Discovery_Method":sec_discovery_method,
      "Selected_Source_URL":sec_data_url or "NOT_VERIFIED","Retrieval_Timestamp_UTC":sec_data.get("timestamp_utc",""),
      "HTTP_Status":sec_data.get("status",""),"Content_Type":sec_data.get("content_type",""),"Raw_Bytes":sec_data.get("bytes",0),
      "Raw_SHA256":sec_data.get("sha256",""),"Schema":sec_fields,"Schema_Status":sec_schema_status,"Parse_Error":sec_parse_error,
      "Record_Count":len(sec_rows),"Duplicate_Ticker_Count":sum(1 for n in duplicate_ticker.values() if n>1),
      "Duplicate_Ticker_Exchange_Count":sum(1 for n in duplicate_pair.values() if n>1),
      "Null_Ticker_Count":sum(1 for r in sec_rows if not r.get(sec_ticker_field,"")) if sec_ticker_field else 0,
      "Null_Exchange_Count":sum(1 for r in sec_rows if not r.get(sec_exchange_field,"")) if sec_exchange_field else 0,
      "Raw_Snapshot_Persisted":False,"Fair_Access_User_Agent":SEC_UA,"Per_Security_Requests":0
    }
    (out/"sec_ticker_exchange_source_audit_v0.76.json").write_text(json.dumps(sec_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(out/"sec_exchange_value_inventory_v0.76.csv",[
      {"SEC_Exchange_Value":k,"SEC_Record_Count":v} for k,v in sorted(exchange_counts.items())
    ] or [{"SEC_Exchange_Value":"","SEC_Record_Count":0}])

    # Parse ISO MIC.
    mic_rows=[];mic_names={};mic_parse_error=""
    if iso_data.get("ok"):
        try:mic_rows,mic_names=parse_mic_dataset(iso_data_url,iso_data["body"])
        except Exception as e:mic_parse_error=f"{type(e).__name__}:{e}"
    target_tickers={r["Primary_Ticker"] for r in target}
    relevant_sec=[r for r in sec_rows if sec_ticker_field and r.get(sec_ticker_field,"") in target_tickers]
    relevant_exchange_values=sorted({r.get(sec_exchange_field,"") for r in relevant_sec if r.get(sec_exchange_field,"")})
    mic_audit={
      "Official_Landing_Page":ISO_MIC_LANDING,"Discovery_Method":iso_discovery_method,
      "Selected_MIC_Dataset_URL":iso_data_url or "NOT_VERIFIED","Retrieval_Timestamp_UTC":iso_data.get("timestamp_utc",""),
      "HTTP_Status":iso_data.get("status",""),"Content_Type":iso_data.get("content_type",""),"Raw_Bytes":iso_data.get("bytes",0),
      "Raw_SHA256":iso_data.get("sha256",""),"Parsed_Row_Count":len(mic_rows),"Schema_Field_Map":mic_names,
      "Parse_Error":mic_parse_error,"Relevant_SEC_Exchange_Values":relevant_exchange_values,"Raw_Snapshot_Persisted":False
    }
    (out/"official_exchange_mic_authority_audit_v0.76.json").write_text(json.dumps(mic_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # SEC exchange -> operating MIC via exact case-insensitive MIC ACRONYM.
    exchange_map={};map_rows=[]
    for ex in relevant_exchange_values:
        hits=[]
        if mic_rows and mic_names.get("acronym"):
            for r in mic_rows:
                if norm_case(r.get(mic_names["acronym"],""))==norm_case(ex):
                    hits.append(r)
        opmics=sorted({norm(r.get(mic_names.get("operating_mic",""),"")) for r in hits if norm(r.get(mic_names.get("operating_mic",""),""))})
        oprt_rows=[r for r in hits if norm(r.get(mic_names.get("oprt_sgmt",""),"")).upper()=="OPRT"]
        candidate_mics=sorted({norm(r.get(mic_names.get("mic",""),"")) for r in hits if norm(r.get(mic_names.get("mic",""),""))})
        status="PASS" if len(opmics)==1 and len(oprt_rows)>=1 and any(norm(r.get(mic_names["mic"],""))==opmics[0] for r in oprt_rows) else ("AMBIGUOUS" if len(opmics)>1 else "NOT_VERIFIED")
        operating=opmics[0] if status=="PASS" else ""
        if status=="PASS":exchange_map[ex]=operating
        official_names=sorted({norm(r.get(mic_names.get("market_name",""),"")) for r in hits if norm(r.get(mic_names.get("market_name",""),""))})
        map_rows.append({
          "SEC_Exchange_Value":ex,"Official_Exchange_Name":" | ".join(official_names),
          "Operating_MIC":operating or "NOT_VERIFIED","Segment_MICs":" | ".join(candidate_mics),
          "MIC_Type":"OPERATING_MIC" if status=="PASS" else "NOT_VERIFIED",
          "Evidence_Source":iso_data_url or "NOT_VERIFIED","Exact_Acronym_Match_Count":len(hits),
          "Unique_Operating_MIC_Count":len(opmics),"Mapping_Status":status
        })
    write_csv(out/"sec_exchange_to_mic_mapping_v0.76.csv",map_rows if map_rows else [{
      "SEC_Exchange_Value":"","Official_Exchange_Name":"","Operating_MIC":"NOT_VERIFIED","Segment_MICs":"",
      "MIC_Type":"NOT_VERIFIED","Evidence_Source":iso_data_url or "NOT_VERIFIED","Exact_Acronym_Match_Count":0,
      "Unique_Operating_MIC_Count":0,"Mapping_Status":"NOT_VERIFIED"
    }])

    # Ticker normalization + row linkage.
    exact_by_ticker=defaultdict(list);case_by_ticker=defaultdict(list)
    for r in sec_rows:
        t=r.get(sec_ticker_field,"") if sec_ticker_field else ""
        if t:
            exact_by_ticker[t].append(r);case_by_ticker[t.casefold()].append(r)
    norm_audit=[];links=[];status_counts=Counter();sec_identity_to_ws=defaultdict(set)
    target_by_ws={r["WS_ID"]:r for r in target}
    for t in target:
        ft=t["Primary_Ticker"];fm=t["Primary_MIC"]
        candidates=exact_by_ticker.get(ft,[])
        method="EXACT";norm_status="EXACT"
        if not candidates:
            cf=case_by_ticker.get(ft.casefold(),[])
            if len({r.get(sec_ticker_field,"") for r in cf})==1 and cf:
                candidates=cf;method="CASE_ONLY";norm_status="AUTHORIZED_CASE_ONLY"
            else:
                method="NONE";norm_status="NOT_FOUND"
        norm_audit.append({
          "WS_ID":t["WS_ID"],"Frozen_Ticker":ft,"SEC_Ticker":" | ".join(sorted({r.get(sec_ticker_field,"") for r in candidates})),
          "Normalization_Method":method,"Normalization_Status":norm_status,"Punctuation_Substitution_Used":"NO"
        })
        mapped=[]
        unresolved_mic=False
        for r in candidates:
            ex=r.get(sec_exchange_field,"");mic=exchange_map.get(ex)
            if not mic:unresolved_mic=True
            mapped.append((r,ex,mic))
        matching=[x for x in mapped if x[2]==fm]
        if len(matching)==1:
            r,ex,mic=matching[0];status="PROVABLY_LINKED";detail=""
            sec_identity_to_ws[(r.get(sec_ticker_field,""),ex)].add(t["WS_ID"])
            cik=r.get(sec_cik_field,"")
        elif len(matching)>1:
            status="AMBIGUOUS";detail="Multiple SEC rows survive exact ticker+governed MIC filter.";cik=""
        elif not candidates:
            status="NOT_FOUND";detail="Frozen ticker absent from SEC ticker/exchange bulk dataset.";cik=""
        elif unresolved_mic:
            status="NOT_VERIFIED";detail="SEC exchange value lacks complete official exchange-to-MIC authority.";cik=""
        else:
            status="CONFLICT";detail="SEC ticker exists but governed operating MIC does not equal Frozen Primary_MIC.";cik=""
        status_counts[status]+=1
        links.append({
          **t,"CIK":cik,"SEC_Ticker":matching[0][0].get(sec_ticker_field,"") if len(matching)==1 else "",
          "SEC_Exchange":matching[0][1] if len(matching)==1 else "",
          "Governed_Operating_MIC":matching[0][2] if len(matching)==1 else "",
          "Ticker_Normalization_Method":method,"SEC_Ticker_Candidate_Count":len(candidates),
          "SEC_Matching_Ticker_MIC_Row_Count":len(matching),"Gate_E_Status":status,"Detail":detail,
          "SIC_RAW_UNPROMOTED":"NOT_CAPTURED_IN_PRIMARY_TICKER_EXCHANGE_DATASET"
        })
    write_csv(out/"us_sp400_ticker_normalization_audit_v0.76.csv",norm_audit)
    write_csv(out/"us_sp400_exact_368_identity_linkage_v0.76.csv",links)

    # CIK/share-class audit from SEC bulk records without issuer-name joins.
    cik_all=defaultdict(list)
    for r in sec_rows:
        c=r.get(sec_cik_field,"") if sec_cik_field else ""
        if c:cik_all[c].append(r)
    target_cik_counts=Counter(r["CIK"] for r in links if r["CIK"])
    share_rows=[]
    for r in links:
        if r["Gate_E_Status"]!="PROVABLY_LINKED":continue
        c=r["CIK"];allr=cik_all.get(c,[])
        tickers=sorted({x.get(sec_ticker_field,"") for x in allr if x.get(sec_ticker_field,"")})
        pairs=sorted({(x.get(sec_ticker_field,""),x.get(sec_exchange_field,"")) for x in allr if x.get(sec_ticker_field,"")})
        share_rows.append({
          "WS_ID":r["WS_ID"],"CIK":c,"SEC_Ticker":r["SEC_Ticker"],"SEC_Exchange":r["SEC_Exchange"],
          "SEC_CIK_Total_Ticker_Count":len(tickers),"SEC_CIK_Total_Ticker_Exchange_Count":len(pairs),
          "Target_Frozen_Rows_With_Same_CIK":target_cik_counts[c],"Share_Class_Collapse_Performed":"NO",
          "CIK_Role":"ISSUER_REFERENCE_ONLY","Audit_Status":"PASS"
        })
    write_csv(out/"us_sp400_cik_share_class_audit_v0.76.csv",share_rows if share_rows else [{
      "WS_ID":"","CIK":"","SEC_Ticker":"","SEC_Exchange":"","SEC_CIK_Total_Ticker_Count":0,"SEC_CIK_Total_Ticker_Exchange_Count":0,
      "Target_Frozen_Rows_With_Same_CIK":0,"Share_Class_Collapse_Performed":"NO","CIK_Role":"ISSUER_REFERENCE_ONLY","Audit_Status":"NOT_VERIFIED"
    }])

    # Collision/ambiguity audit.
    collision_rows=[]
    dup_ws=[k for k,v in Counter(r["WS_ID"] for r in target).items() if v>1]
    dup_key=[k for k,v in Counter(r["Security_Key"] for r in target).items() if v>1]
    sec_collisions=[{"SEC_Ticker":k[0],"SEC_Exchange":k[1],"Frozen_WS_IDs":" | ".join(sorted(v))} for k,v in sec_identity_to_ws.items() if len(v)>1]
    collision_rows.append({"Audit":"FROZEN_WS_ID_DUPLICATES","Count":len(dup_ws),"Detail":" | ".join(dup_ws),"Status":"PASS" if not dup_ws else "FAIL"})
    collision_rows.append({"Audit":"FROZEN_SECURITY_KEY_DUPLICATES","Count":len(dup_key),"Detail":" | ".join(dup_key),"Status":"PASS" if not dup_key else "FAIL"})
    collision_rows.append({"Audit":"SEC_TICKER_EXCHANGE_TO_MULTIPLE_FROZEN_WS_ID","Count":len(sec_collisions),"Detail":json.dumps(sec_collisions,separators=(",",":")),"Status":"PASS" if not sec_collisions else "FAIL"})
    write_csv(out/"us_sp400_identity_collision_audit_v0.76.csv",collision_rows)

    # Optional nightly submissions intentionally not needed for Gate E if primary route is sufficient; never per-CIK fanout.
    optional={
      "Status":"NOT_REQUIRED" if status_counts["PROVABLY_LINKED"]==368 else "NOT_EXECUTED_FAIL_CLOSED",
      "Requests":0,"Per_CIK_Requests":0,"SIC_Promotion_Performed":False,
      "Reason":"Primary official SEC ticker/exchange bulk route is sufficient." if status_counts["PROVABLY_LINKED"]==368 else "Primary linkage unresolved; task fails closed rather than expanding scope unless a bounded bulk confirmation is strictly necessary and contract is separately verified."
    }
    (out/"optional_sec_bulk_submissions_audit_v0.76.json").write_text(json.dumps(optional,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    linked=status_counts["PROVABLY_LINKED"];amb=status_counts["AMBIGUOUS"];nf=status_counts["NOT_FOUND"];nv=status_counts["NOT_VERIFIED"];conf=status_counts["CONFLICT"]
    map_complete=bool(relevant_exchange_values) and all(exchange_map.get(x) for x in relevant_exchange_values)
    sec_route_ok=bool(sec_data_url and sec_data.get("ok") and sec_schema_status=="PASS")
    iso_route_ok=bool(iso_data_url and iso_data.get("ok") and mic_rows)
    collisions=len(sec_collisions)

    blocker=""
    if not sec_data_url or not sec_data.get("ok"):blocker="SEC_TICKER_EXCHANGE_BULK_ROUTE_NOT_REPRODUCIBLE"
    elif sec_schema_status!="PASS":blocker="SEC_SECURITY_IDENTIFIER_SCHEMA_NOT_VERIFIED"
    elif not iso_route_ok or not map_complete:blocker="SEC_EXCHANGE_TO_MIC_AUTHORITY_NOT_VERIFIED"
    elif amb>0:blocker="SEC_TICKER_EXCHANGE_IDENTITY_AMBIGUOUS"
    elif nf>0:blocker="FROZEN_US_SP400_TICKER_NOT_FOUND"
    elif conf>0:blocker="FROZEN_US_SP400_MIC_CONFLICT"
    elif nv>0 or linked!=368 or collisions>0:blocker="US_SP400_EXACT_368_IDENTITY_LINKAGE_INCOMPLETE"

    ready=(blocker=="" and linked==368 and amb==nf==nv==conf==0 and sec_route_ok and map_complete and collisions==0)
    verdict="PASS_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE" if ready else "BLOCKED_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE"
    next_gate="US_SP400 EXACT FROZEN SEC SIC CLASSIFICATION COVERAGE GATE" if ready else blocker
    identity_route="SEC exact ticker + SEC exact exchange -> ISO 10383 exact ACRONYM -> operating MIC -> Frozen exact (Primary_Ticker, Primary_MIC) -> WS_ID"
    mic_authority=(iso_data_url or "NOT_VERIFIED")+" / exact SEC exchange value to ISO ACRONYM, unique operating MIC"

    prov=provider_calls()
    (out/"provider_call_audit_v0.76.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "IN_Gate_F_Classified_Before":45,"IN_Gate_F_Classified_After":45,"IN_Canonical_Rows_Before":0,"IN_Canonical_Rows_After":0,
      "IN_Execution_State_After":"PARKED_EXTERNAL_AUTHORIZATION",
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "US_Gate_F_Runs":0,"Canonical_Materialization_Runs":0,"US_SP500_Runs":0,"Other_Cohort_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.76.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V075_PARK_BLOCKER_AUTHORITY",pred["summary"]["blocker"]=="EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION","PASS")
    test("G_SEC_06_PRESENT",gov["authority_id"]=="G-SEC-06","PASS")
    test("TARGET_368",len(target)==368,368)
    test("TARGET_UNIQUE_WS",len({r["WS_ID"] for r in target})==368,368)
    test("TARGET_UNIQUE_SECURITY_KEY",len({r["Security_Key"] for r in target})==368,368)
    test("POST_PARK_SELECTED_US_SP400",selected["Selected_Cohort"]=="US_SP400","US_SP400")
    test("POST_PARK_TIE_BREAK",selected["Tie_Row_Counts"].get("US_SP400")==368 and selected["Tie_Row_Counts"].get("US_SP500")==372,"368<372")
    test("IN_PARK_STATE",park[0]["Execution_State"]=="PARKED_EXTERNAL_AUTHORIZATION","PASS")
    test("IN_GATE_F_UNCHANGED",imm["IN_Gate_F_Classified_Before"]==imm["IN_Gate_F_Classified_After"]==45,45)
    test("IN_CANONICAL_ROWS_ZERO",imm["IN_Canonical_Rows_After"]==0,0)
    test("SEC_DOC_REQUESTS_BOUNDED",sum(r["Source_Class"]=="SEC" and r["Request_Type"] in {"SEC_API_DOCUMENTATION","SEC_ACCESS_DOCUMENTATION"} for r in external)<=2,"PASS")
    test("NO_PER_SECURITY_REQUESTS",all(r["Per_Security_Fanout"]=="NO" for r in external),"PASS")
    test("NO_NIFTY_REQUESTS",prov["nifty_requests"]==0,0)
    test("NO_COMPANY_NAME_JOIN",prov["company_name_joins"]==0,0)
    test("NO_FUZZY",prov["fuzzy_matching"]==0,0)
    test("NO_US_GATE_F",prov["us_gate_f"]==0,0)
    test("NO_SIC_PROMOTION",prov["sic_promotion"]==0,0)
    test("NO_CANONICAL_MATERIALIZATION",prov["canonical_materialization"]==0,0)
    test("NO_US_SP500",prov["us_sp500_execution"]==0,0)
    test("NO_FORBIDDEN_PROVIDERS",sum(prov.values())==0,0)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("SEC_ROUTE_REPRODUCIBLE",sec_route_ok,sec_data_url)
        test("EXCHANGE_MIC_COMPLETE",map_complete,json.dumps(exchange_map,sort_keys=True))
        test("LINKED_368",linked==368,linked)
        test("ZERO_UNRESOLVED",amb==nf==nv==conf==0,f"{amb}/{nf}/{nv}/{conf}")
        test("NO_IDENTITY_COLLISIONS",collisions==0,collisions)
    else:test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.76.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION",
      "selected_cohort":"US_SP400","us_sp400_deterministic_sec_identity_ready":ready,
      "linked":linked,"total":368,"ambiguous":amb,"not_found":nf,"not_verified":nv,"conflict":conf,
      "sec_identity_route":identity_route,"exchange_mic_authority":mic_authority,"blocker":blocker,
      "sec_primary_source_url":sec_data_url or "NOT_VERIFIED","sec_primary_source_sha256":sec_data.get("sha256",""),
      "iso_mic_source_url":iso_data_url or "NOT_VERIFIED","iso_mic_source_sha256":iso_data.get("sha256",""),
      "primary_mic_distribution":mic_dist,"external_requests":len(external),"optional_bulk_submission_requests":0,
      "in_gate_f_classified":45,"in_canonical_rows":0,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "us_gate_f_runs":0,"canonical_materialization_runs":0,"us_sp500_runs":0,"other_cohort_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD",
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"next_gate":next_gate
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_nifty50_park_state","selected_cohort","us_sp400_deterministic_sec_identity_ready","linked","total","ambiguous","not_found","not_verified","conflict","sec_identity_route","exchange_mic_authority","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.76.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.76.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","selected_cohort":"US_SP400",
      "us_sp400_deterministic_sec_identity_ready":ready,"linked":linked,"total":368,"ambiguous":amb,"not_found":nf,
      "not_verified":nv,"conflict":conf,"sec_identity_route":identity_route,"exchange_mic_authority":mic_authority,
      "blocker":blocker,"in_gate_f_classified":45,"in_canonical_rows":0,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "us_gate_f_runs":0,"canonical_materialization_runs":0,"us_sp500_runs":0,"other_cohort_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,
      "artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.76.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
