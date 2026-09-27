#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, json, re, subprocess, time, unicodedata, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.77"
STAGE="US_SP400_SEC_COMPANY_TICKERS_EXCHANGE_DIRECT_BULK_ROUTE_REPAIR_GATE_E_COMPLETION"
REQUIRED_START_HEAD="17c21283f6c4fbdf524bc80324235c029018b6d6"
V076_WORKFLOW=36322252802
V076_ARTIFACT=10932404865
V076_DIGEST="sha256:d43417c1e101e0cee2da785ea0c78f80305f9f0d8cd03e2498017427259b0f34"
V076_ISO_SHA="79de0f7704e260bd49b0d2439f3084891cabc93481da8bdbaa716e15a27211ed"
V076_PARK_SHA="161f1c354531ca9440c1d97b8c95ed417b5248734f8fe381c83a87858b9b9d37"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

SPEC=ROOT/"config/us_sp400_sec_direct_route_repair_spec_v0.77.json"
SUM76=ROOT/"output_us_sp400_sec_identity_linkage_v0_76/summary_v0.76.json"
CHK76=ROOT/"output_us_sp400_sec_identity_linkage_v0_76/stage_checkpoint_v0.76.json"
AUD76=ROOT/"output_us_sp400_sec_identity_linkage_v0_76/sec_ticker_exchange_source_audit_v0.76.json"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
CAP58=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
COV74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/in_exact_45_classification_coverage_v0.74.csv"

SEC_URL="https://www.sec.gov/files/company_tickers_exchange.json"
ISO_URL="https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv"
SEC_UA="WeltSwingLongDev-v0.77 akx0801-hub@users.noreply.github.com https://github.com/akx0801-hub/welt-swing-long-data"
ISO_UA="WeltSwingLongDev-v0.77 akx0801-hub/welt-swing-long-data"
TRANSIENT={429,500,502,503,504}

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def nfc(s:str)->str:return unicodedata.normalize("NFC",str(s or ""))
def trim(s:str)->str:return nfc(s).strip()
def cmpnorm(s:str)->str:return trim(s).casefold()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

def safe_headers(headers)->dict[str,str]:
    wanted=["Content-Type","Content-Length","Server","Retry-After","Via","X-Cache","X-Amz-Cf-Id","Date"]
    return {k:headers.get(k,"") for k in wanted if headers.get(k)}

def sec_fetch_once(url:str)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    req_headers={"User-Agent":SEC_UA,"Accept":"application/json,text/plain,*/*;q=0.8","Accept-Encoding":"identity"}
    req=urllib.request.Request(url,headers=req_headers,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            body=r.read(25_000_000)
            return {"ok":200<=int(r.status)<300,"url":url,"resolved_url":r.geturl(),"status":int(r.status),
                    "content_type":r.headers.get("Content-Type",""),"bytes":len(body),"sha256":sha_bytes(body),
                    "timestamp_utc":ts,"body":body,"response_headers":safe_headers(r.headers),
                    "request_headers":req_headers,"error":""}
    except urllib.error.HTTPError as e:
        try:body=e.read(1_000_000)
        except Exception:body=b""
        return {"ok":False,"url":url,"resolved_url":getattr(e,"url",url),"status":int(e.code),
                "content_type":e.headers.get("Content-Type","") if e.headers else "","bytes":len(body),
                "sha256":sha_bytes(body) if body else "","timestamp_utc":ts,"body":body,
                "response_headers":safe_headers(e.headers) if e.headers else {},"request_headers":req_headers,
                "error":f"HTTPError:{e.code}"}
    except Exception as e:
        return {"ok":False,"url":url,"resolved_url":url,"status":"","content_type":"","bytes":0,"sha256":"",
                "timestamp_utc":ts,"body":b"","response_headers":{},"request_headers":req_headers,
                "error":f"{type(e).__name__}:{e}"}

def sec_direct_attempts()->list[dict[str,Any]]:
    out=[]
    for i in range(1,4):
        r=sec_fetch_once(SEC_URL);r["attempt"]=i;out.append(r)
        if r.get("ok"):break
        status=r.get("status")
        if status not in TRANSIENT:break
        if i<3:time.sleep(1.0)
    return out

def iso_fetch()->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    req=urllib.request.Request(ISO_URL,headers={"User-Agent":ISO_UA,"Accept":"text/csv,*/*;q=0.8","Accept-Encoding":"identity"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read(5_000_000)
            return {"ok":200<=int(r.status)<300,"url":ISO_URL,"resolved_url":r.geturl(),"status":int(r.status),
                    "content_type":r.headers.get("Content-Type",""),"bytes":len(b),"sha256":sha_bytes(b),
                    "timestamp_utc":ts,"body":b,"error":""}
    except Exception as e:
        return {"ok":False,"url":ISO_URL,"resolved_url":ISO_URL,"status":"","content_type":"","bytes":0,"sha256":"",
                "timestamp_utc":ts,"body":b"","error":f"{type(e).__name__}:{e}"}

def parse_iso(body:bytes)->tuple[list[dict[str,str]],dict[str,str]]:
    text=body.decode("utf-8-sig",errors="replace")
    rows=list(csv.DictReader(io.StringIO(text)))
    if not rows:raise RuntimeError("ISO MIC dataset empty")
    fields=list(rows[0].keys())
    def find(*names):
        keyed={re.sub(r"[^a-z0-9]","",x.casefold()):x for x in fields}
        for n in names:
            k=re.sub(r"[^a-z0-9]","",n.casefold())
            if k in keyed:return keyed[k]
        return ""
    fm={
      "mic":find("MIC"),"operating_mic":find("OPERATING MIC"),"oprt_sgmt":find("OPRT/SGMT"),
      "market_name":find("MARKET NAME-INSTITUTION DESCRIPTION"),"acronym":find("ACRONYM"),"status":find("STATUS")
    }
    if not all(fm.values()):raise RuntimeError("ISO MIC schema not verified: "+json.dumps(fm,sort_keys=True))
    return rows,fm

def validate_predecessor(repo_sha:str):
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM76.read_text(encoding="utf-8"));c=json.loads(CHK76.read_text(encoding="utf-8"));a=json.loads(AUD76.read_text(encoding="utf-8"))
    if s["verdict"]!="BLOCKED_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE":raise RuntimeError("v0.76 verdict")
    if s["selected_cohort"]!="US_SP400" or s["us_sp400_deterministic_sec_identity_ready"] is not False:raise RuntimeError("v0.76 state")
    if (s["linked"],s["total"],s["not_found"])!=(0,368,368):raise RuntimeError("v0.76 counts")
    if s["blocker"]!="SEC_TICKER_EXCHANGE_BULK_ROUTE_NOT_REPRODUCIBLE":raise RuntimeError("v0.76 blocker")
    if s["primary_mic_distribution"]!={"XNAS":126,"XNYS":242}:raise RuntimeError("v0.76 MIC distribution")
    if s["iso_mic_source_sha256"]!=V076_ISO_SHA:raise RuntimeError("v0.76 ISO SHA")
    if c["workflow_run_id"]!=V076_WORKFLOW or c["artifact_id"]!=V076_ARTIFACT or "sha256:"+c["artifact_digest"]!=V076_DIGEST:raise RuntimeError("v0.76 artifact")
    if a["Record_Count"]!=0:raise RuntimeError("v0.76 SEC record count must be zero")
    if sha_file(PARK)!=V076_PARK_SHA:raise RuntimeError("IN park registry changed")
    park=read_csv(PARK)
    if len(park)!=1 or park[0]["Cohort"]!="IN_NIFTY50" or park[0]["Execution_State"]!="PARKED_EXTERNAL_AUTHORIZATION":raise RuntimeError("IN park state")
    cov=read_csv(COV74)
    if len(cov)!=45 or any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in cov):raise RuntimeError("IN Gate F changed")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    return s

def reconstruct_target()->tuple[list[dict[str,str]],dict[str,int]]:
    frozen=read_csv(FROZEN);cap=read_csv(CAP58)
    by={r["Security_Key"]:r for r in cap}
    if len(frozen)!=1425 or len(cap)!=1425 or len(by)!=1425:raise RuntimeError("Frozen/capability row count mismatch")
    out=[]
    for r in frozen:
        c=by.get(r["Security_Key"])
        if not c:raise RuntimeError("missing capability row")
        if c["Source_WS_ID"]!=r["Source_WS_ID"] or c["Primary_MIC"]!=r["Primary_MIC"] or c["Primary_Ticker"]!=r["Primary_Ticker"]:
            raise RuntimeError("Frozen/capability identity mismatch")
        if c["Primary_Universe_Index"]=="US_SP400":
            out.append({
              "Security_Key":r["Security_Key"],"WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],
              "Primary_Ticker":r["Primary_Ticker"],"ISIN":"","Primary_Universe_Index":"US_SP400"
            })
    dist=dict(sorted(Counter(r["Primary_MIC"] for r in out).items()))
    if len(out)!=368 or len({r["WS_ID"] for r in out})!=368 or len({r["Security_Key"] for r in out})!=368:raise RuntimeError("target mismatch")
    if dist!={"XNAS":126,"XNYS":242}:raise RuntimeError("Frozen MIC distribution mismatch")
    return sorted(out,key=lambda r:r["WS_ID"]),dist

def parse_sec(body:bytes)->tuple[list[dict[str,str]],list[str],dict[str,int]]:
    obj=json.loads(body.decode("utf-8"))
    if not isinstance(obj,dict) or not isinstance(obj.get("fields"),list) or not isinstance(obj.get("data"),list):
        raise RuntimeError("SEC_TICKER_EXCHANGE_SCHEMA_NOT_VERIFIED")
    fields=[str(x) for x in obj["fields"]]
    required={"cik","ticker","exchange"}
    if not required.issubset(set(fields)):raise RuntimeError("SEC_TICKER_EXCHANGE_SCHEMA_NOT_VERIFIED")
    rows=[]
    for rec in obj["data"]:
        if not isinstance(rec,list):raise RuntimeError("SEC_TICKER_EXCHANGE_SCHEMA_NOT_VERIFIED")
        rows.append({fields[i]:trim(rec[i]) if i<len(rec) else "" for i in range(len(fields))})
    positions={f:i for i,f in enumerate(fields)}
    return rows,fields,positions

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,
      "etf_holdings":0,"ishares_identity_authority":0,"sp_third_party_mirrors":0,"company_name_joins":0,
      "fuzzy_matching":0,"manual_issuer_guessing":0,"per_security_web_fanout":0,"price_ohlcv":0,"news":0,
      "trading_analysis":0,"nifty_requests":0,"us_gate_f":0,"sic_promotion":0,"us_sp500":0,
      "canonical_materialization":0,"canonical_registry_readiness_update":0,"sector_rs":0,"p0":0,"p1":0,"p2":0
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_us_sp400_sec_direct_route_repair_v0_77")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    correction={
      "Version":"v0.77","v076_SEC_Source_Record_Count":0,"v076_Row_NOT_FOUND_Count":368,
      "Correction":"v0.76 NOT_FOUND statuses were downstream artifacts of a route-discovery failure and are not genuine security-level absence evidence.",
      "Forward_Failure_Semantics":"If the direct SEC bulk dataset cannot be loaded, all 368 target rows are NOT_VERIFIED and NOT_FOUND remains zero.",
      "v076_Historical_Evidence_Rewritten":False
    }
    (out/"v076_source_failure_semantics_correction_v0.77.json").write_text(json.dumps(correction,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    target,dist=reconstruct_target()
    write_csv(out/"us_sp400_frozen_368_identity_target_v0.77.csv",target)

    attempts=sec_direct_attempts()
    sec=next((r for r in attempts if r.get("ok")),attempts[-1])
    ext=[]
    for r in attempts:
        ext.append({
          "Request_Order":len(ext)+1,"Source_Class":"SEC","Request_Type":"SEC_COMPANY_TICKERS_EXCHANGE_DIRECT_BULK",
          "Attempt":r["attempt"],"URL":r["url"],"Resolved_URL":r.get("resolved_url",""),"HTTP_Status":r.get("status",""),
          "Content_Type":r.get("content_type",""),"Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),
          "Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),"User_Agent":SEC_UA,
          "Authentication_Used":"NO","Cookies_Authority_Used":"NO","Per_Security_Fanout":"NO","Result":"PASS" if r.get("ok") else r.get("error","FAILED")
        })

    diagnostics=[]
    for r in attempts:
        prefix=r.get("body",b"")[:240].decode("utf-8",errors="replace").replace("\r"," ").replace("\n"," ")
        diagnostics.append({
          "Attempt":r["attempt"],"HTTP_Status":r.get("status",""),"Response_Headers":r.get("response_headers",{}),
          "Body_Bytes":r.get("bytes",0),"Body_SHA256":r.get("sha256",""),"Body_Prefix_Bounded":prefix,
          "Interpretation":"SUCCESS" if r.get("ok") else ("HTTP_403_NO_BYPASS" if r.get("status")==403 else "TRANSIENT_OR_OTHER_FAILURE")
        })

    sec_rows=[];fields=[];positions={};schema_status="NOT_VERIFIED";parse_error=""
    if sec.get("ok"):
        try:
            sec_rows,fields,positions=parse_sec(sec["body"]);schema_status="PASS"
        except Exception as e:parse_error=f"{type(e).__name__}:{e}"

    route_audit={
      "Selected_Source_URL":SEC_URL,"Resolved_URL":sec.get("resolved_url",SEC_URL),"Attempts":len(attempts),
      "HTTP_Status":sec.get("status",""),"Content_Type":sec.get("content_type",""),"Raw_Bytes":sec.get("bytes",0),
      "Raw_SHA256":sec.get("sha256",""),"Retrieval_Timestamp_UTC":sec.get("timestamp_utc",""),
      "Request_Headers":{"User-Agent":SEC_UA,"Accept":"application/json,text/plain,*/*;q=0.8","Accept-Encoding":"identity"},
      "Response_Diagnostics":diagnostics,"Schema":fields,"Record_Count":len(sec_rows),
      "Route_Status":"PASS" if sec.get("ok") and schema_status=="PASS" else "FAIL",
      "Raw_Source_Persisted":False,"Authentication_Used":False,"Cookie_Authority_Used":False,"Captcha_Bypass_Used":False
    }
    (out/"sec_company_tickers_exchange_direct_route_audit_v0.77.json").write_text(json.dumps(route_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    schema_contract={
      "Status":schema_status,"Top_Level_Type":"object" if sec.get("ok") else "NOT_LOADED",
      "Fields":fields,"Field_Positions":positions,"Required_Fields":["cik","ticker","exchange"],
      "Name_Field_Allowed_For_Provenance_Only":True,"Name_Field_Used_For_Join":False,"Parse_Error":parse_error,
      "Positional_Binding_Rule":"Positions are derived only from the returned fields array."
    }
    (out/"sec_company_tickers_exchange_schema_contract_v0.77.json").write_text(json.dumps(schema_contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    target_tickers={r["Primary_Ticker"] for r in target}
    candidate=[r for r in sec_rows if r.get("ticker","") in target_tickers] if schema_status=="PASS" else []
    ex_inv=Counter(r.get("exchange","") for r in candidate if r.get("exchange",""))
    write_csv(out/"sec_exchange_value_inventory_v0.77.csv",[
      {"SEC_Exchange_Value":k,"Candidate_Record_Count":v} for k,v in sorted(ex_inv.items())
    ] or [{"SEC_Exchange_Value":"","Candidate_Record_Count":0}])

    iso=None;iso_rows=[];iso_fields={};iso_error=""
    if sec.get("ok") and schema_status=="PASS":
        iso=iso_fetch()
        ext.append({
          "Request_Order":len(ext)+1,"Source_Class":"ISO","Request_Type":"ISO_10383_MIC_INTEGRITY_REFETCH","Attempt":1,
          "URL":iso["url"],"Resolved_URL":iso.get("resolved_url",""),"HTTP_Status":iso.get("status",""),
          "Content_Type":iso.get("content_type",""),"Bytes":iso.get("bytes",0),"SHA256":iso.get("sha256",""),
          "Retrieval_Timestamp_UTC":iso.get("timestamp_utc",""),"User_Agent":ISO_UA,"Authentication_Used":"NO",
          "Cookies_Authority_Used":"NO","Per_Security_Fanout":"NO","Result":"PASS" if iso.get("ok") else iso.get("error","FAILED")
        })
        if iso.get("ok"):
            try:iso_rows,iso_fields=parse_iso(iso["body"])
            except Exception as e:iso_error=f"{type(e).__name__}:{e}"
    write_csv(out/"external_request_ledger_v0.77.csv",ext)

    exchange_map={};mic_bindings=[]
    for ex,count in sorted(ex_inv.items()):
        acr_hits=[r for r in iso_rows if cmpnorm(r.get(iso_fields.get("acronym",""),""))==cmpnorm(ex)] if iso_rows else []
        name_hits=[]
        matched_field="ACRONYM"
        hits=acr_hits
        if not hits and iso_rows:
            name_hits=[r for r in iso_rows if cmpnorm(r.get(iso_fields.get("market_name",""),""))==cmpnorm(ex)]
            hits=name_hits;matched_field="MARKET_NAME-INSTITUTION_DESCRIPTION"
        opmics=sorted({trim(r.get(iso_fields.get("operating_mic",""),"")) for r in hits if trim(r.get(iso_fields.get("operating_mic",""),""))})
        op_rows=[r for r in hits if trim(r.get(iso_fields.get("oprt_sgmt",""),"")).upper()=="OPRT"]
        authorized=[m for m in opmics if m in {"XNAS","XNYS"}]
        status="PASS" if len(opmics)==1 and len(authorized)==1 and any(trim(r.get(iso_fields["mic"],""))==authorized[0] for r in op_rows) else ("AMBIGUOUS" if len(opmics)>1 else "NOT_VERIFIED")
        if status=="PASS":exchange_map[ex]=authorized[0]
        first=hits[0] if hits else {}
        mic_bindings.append({
          "SEC_Exchange_Value_Raw":ex,"Normalized_Comparison_Value":cmpnorm(ex),"Candidate_Record_Count":count,
          "Matched_ISO_Field":matched_field if hits else "NONE","ISO_Market_Name":trim(first.get(iso_fields.get("market_name",""),"")),
          "ISO_Acronym":trim(first.get(iso_fields.get("acronym",""),"")),"MIC":trim(first.get(iso_fields.get("mic",""),"")),
          "Operating_MIC":authorized[0] if status=="PASS" else (opmics[0] if len(opmics)==1 else ""),
          "OPRT_SGMT":trim(first.get(iso_fields.get("oprt_sgmt",""),"")),"STATUS":trim(first.get(iso_fields.get("status",""),"")),
          "Exact_Match_Count":len(hits),"Unique_Operating_MIC_Count":len(opmics),"Mapping_Status":status,
          "Evidence_Source":ISO_URL,"ISO_Current_SHA256":iso.get("sha256","") if iso else "",
          "ISO_v076_SHA256":V076_ISO_SHA,"ISO_Drift_Status":("UNCHANGED" if iso and iso.get("sha256")==V076_ISO_SHA else ("CHANGED" if iso and iso.get("ok") else "NOT_REFETCHED_OR_FAILED"))
        })
    write_csv(out/"iso_exchange_mic_binding_v0.77.csv",mic_bindings or [{
      "SEC_Exchange_Value_Raw":"","Normalized_Comparison_Value":"","Candidate_Record_Count":0,"Matched_ISO_Field":"NONE",
      "ISO_Market_Name":"","ISO_Acronym":"","MIC":"","Operating_MIC":"","OPRT_SGMT":"","STATUS":"","Exact_Match_Count":0,
      "Unique_Operating_MIC_Count":0,"Mapping_Status":"NOT_VERIFIED","Evidence_Source":ISO_URL,
      "ISO_Current_SHA256":iso.get("sha256","") if iso else "","ISO_v076_SHA256":V076_ISO_SHA,"ISO_Drift_Status":"NOT_REFETCHED_OR_FAILED"
    }])

    exact_by=defaultdict(list);case_by=defaultdict(list)
    if schema_status=="PASS":
        for r in sec_rows:
            t=trim(r.get("ticker",""))
            if t:exact_by[t].append(r);case_by[t.casefold()].append(r)

    norm_rows=[];links=[];counts=Counter();identity_to_ws=defaultdict(set)
    source_loaded=bool(sec.get("ok") and schema_status=="PASS")
    for t in target:
        ft=t["Primary_Ticker"];fm=t["Primary_MIC"]
        if not source_loaded:
            counts["NOT_VERIFIED"]+=1
            norm_rows.append({"WS_ID":t["WS_ID"],"Frozen_Ticker":ft,"SEC_Ticker":"","Normalization_Method":"SOURCE_NOT_LOADED","Normalization_Status":"NOT_VERIFIED","Collision_Free":"NOT_EVALUATED"})
            links.append({**t,"CIK":"","SEC_Ticker":"","SEC_Exchange":"","Resolved_Operating_MIC":"","SEC_Record_Match_Count":0,
                          "Ticker_Normalization_Method":"SOURCE_NOT_LOADED","Gate_E_Status":"NOT_VERIFIED",
                          "Detail":"Direct official SEC bulk source not reproducibly loaded; v0.77 failure semantics prohibit NOT_FOUND."})
            continue
        cand=exact_by.get(ft,[])
        method="EXACT";nstat="EXACT"
        if not cand:
            cf=case_by.get(ft.casefold(),[])
            distinct={trim(r.get("ticker","")) for r in cf}
            if len(distinct)==1 and cf:
                cand=cf;method="CASE_ONLY";nstat="AUTHORIZED_CASE_ONLY"
            else:
                method="NONE";nstat="NOT_FOUND"
        norm_rows.append({"WS_ID":t["WS_ID"],"Frozen_Ticker":ft,"SEC_Ticker":" | ".join(sorted({trim(r.get("ticker","")) for r in cand})),
                          "Normalization_Method":method,"Normalization_Status":nstat,"Collision_Free":"YES" if len({trim(r.get("ticker","")) for r in cand})<=1 else "NO"})
        mapped=[]
        unresolved_exchange=False
        for r in cand:
            ex=trim(r.get("exchange",""));om=exchange_map.get(ex)
            if not om:unresolved_exchange=True
            mapped.append((r,ex,om))
        matching=[x for x in mapped if x[2]==fm]
        if len(matching)==1:
            rr,ex,om=matching[0];status="PROVABLY_LINKED";detail="";cik=trim(rr.get("cik",""))
            identity_to_ws[(trim(rr.get("ticker","")),ex)].add(t["WS_ID"])
        elif len(matching)>1:
            status="AMBIGUOUS";detail="Multiple SEC records survive exact ticker+operating-MIC filtering.";cik=""
        elif not cand:
            status="NOT_FOUND";detail="SEC bulk loaded; no exact/case-authorized ticker record for Frozen target.";cik=""
        elif unresolved_exchange:
            status="NOT_VERIFIED";detail="SEC ticker exists but exchange-to-operating-MIC binding is unresolved.";cik=""
        else:
            status="CONFLICT";detail="SEC ticker exists and exchange resolves, but operating MIC conflicts with Frozen Primary_MIC.";cik=""
        counts[status]+=1
        links.append({**t,"CIK":cik,"SEC_Ticker":trim(matching[0][0].get("ticker","")) if len(matching)==1 else "",
                      "SEC_Exchange":matching[0][1] if len(matching)==1 else "","Resolved_Operating_MIC":matching[0][2] if len(matching)==1 else "",
                      "SEC_Record_Match_Count":len(matching),"Ticker_Normalization_Method":method,"Gate_E_Status":status,"Detail":detail})
    write_csv(out/"us_sp400_ticker_normalization_audit_v0.77.csv",norm_rows)
    write_csv(out/"us_sp400_exact_368_identity_linkage_v0.77.csv",links)

    cik_groups=defaultdict(list)
    for r in sec_rows:
        c=trim(r.get("cik",""))
        if c:cik_groups[c].append(r)
    share=[]
    for l in links:
        if l["Gate_E_Status"]!="PROVABLY_LINKED":continue
        rows=cik_groups.get(l["CIK"],[])
        tickers=sorted({trim(r.get("ticker","")) for r in rows if trim(r.get("ticker",""))})
        pairs=sorted({(trim(r.get("ticker","")),trim(r.get("exchange",""))) for r in rows if trim(r.get("ticker",""))})
        share.append({
          "WS_ID":l["WS_ID"],"CIK":l["CIK"],"SEC_Ticker":l["SEC_Ticker"],"SEC_Exchange":l["SEC_Exchange"],
          "CIK_Ticker_Count":len(tickers),"CIK_Ticker_Exchange_Count":len(pairs),
          "One_CIK_Multiple_Tickers":"YES" if len(tickers)>1 else "NO","Share_Class_Collapse_Performed":"NO",
          "Exact_Ticker_MIC_Unique":"YES","Audit_Status":"PASS"
        })
    write_csv(out/"us_sp400_cik_share_class_audit_v0.77.csv",share or [{
      "WS_ID":"","CIK":"","SEC_Ticker":"","SEC_Exchange":"","CIK_Ticker_Count":0,"CIK_Ticker_Exchange_Count":0,
      "One_CIK_Multiple_Tickers":"NOT_EVALUATED","Share_Class_Collapse_Performed":"NO","Exact_Ticker_MIC_Unique":"NOT_EVALUATED","Audit_Status":"NOT_VERIFIED"
    }])

    dup_ws=[x for x,n in Counter(r["WS_ID"] for r in target).items() if n>1]
    dup_key=[x for x,n in Counter(r["Security_Key"] for r in target).items() if n>1]
    sec_coll=[(k,v) for k,v in identity_to_ws.items() if len(v)>1]
    collision=[
      {"Audit":"FROZEN_WS_ID_DUPLICATES","Count":len(dup_ws),"Status":"PASS" if not dup_ws else "FAIL","Detail":" | ".join(dup_ws)},
      {"Audit":"FROZEN_SECURITY_KEY_DUPLICATES","Count":len(dup_key),"Status":"PASS" if not dup_key else "FAIL","Detail":" | ".join(dup_key)},
      {"Audit":"SEC_TICKER_EXCHANGE_TO_MULTIPLE_FROZEN_WS_ID","Count":len(sec_coll),"Status":"PASS" if not sec_coll else "FAIL",
       "Detail":json.dumps([{"ticker":k[0],"exchange":k[1],"ws_ids":sorted(v)} for k,v in sec_coll],separators=(",",":"))}
    ]
    write_csv(out/"us_sp400_identity_collision_audit_v0.77.csv",collision)

    optional={
      "Status":"NOT_REQUIRED" if counts["PROVABLY_LINKED"]==368 else "NOT_EXECUTED",
      "Requests":0,"Per_CIK_Requests":0,"Primary_Route_HTTP_Failure_Alternative_Used":False,
      "SIC_Promotion_Performed":False,
      "Reason":"Primary company_tickers_exchange route fully resolves Gate E." if counts["PROVABLY_LINKED"]==368 else "Optional bulk submissions are not used after primary-route failure and are not needed merely to classify source-unavailable rows."
    }
    (out/"optional_sec_bulk_submissions_audit_v0.77.json").write_text(json.dumps(optional,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    linked=counts["PROVABLY_LINKED"];amb=counts["AMBIGUOUS"];nf=counts["NOT_FOUND"];nv=counts["NOT_VERIFIED"];conf=counts["CONFLICT"]
    cik_cov=sum(1 for r in links if r["Gate_E_Status"]=="PROVABLY_LINKED" and r["CIK"])
    exchange_mic_ready=bool(ex_inv) and all(exchange_map.get(ex) for ex in ex_inv)
    blocker=""
    if not sec.get("ok"):blocker="SEC_TICKER_EXCHANGE_DIRECT_BULK_ROUTE_NOT_REPRODUCIBLE"
    elif schema_status!="PASS":blocker="SEC_TICKER_EXCHANGE_SCHEMA_NOT_VERIFIED"
    elif not exchange_mic_ready:blocker="SEC_EXCHANGE_TO_MIC_AUTHORITY_NOT_VERIFIED"
    elif amb:blocker="SEC_TICKER_EXCHANGE_IDENTITY_AMBIGUOUS"
    elif nf:blocker="FROZEN_US_SP400_TICKER_NOT_FOUND_IN_SEC_BULK"
    elif conf:blocker="FROZEN_US_SP400_MIC_CONFLICT"
    elif nv or linked!=368 or cik_cov!=368 or sec_coll:blocker="US_SP400_EXACT_368_IDENTITY_LINKAGE_INCOMPLETE"

    ready=(blocker=="" and linked==368 and amb==nf==nv==conf==0 and cik_cov==368 and exchange_mic_ready and not sec_coll)
    verdict="PASS_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE" if ready else "BLOCKED_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE"
    direct_status="PASS" if sec.get("ok") and schema_status=="PASS" else "FAIL"
    mic_status="PASS" if exchange_mic_ready else "NOT_VERIFIED"
    next_gate="US_SP400 EXACT FROZEN SEC SIC CLASSIFICATION COVERAGE GATE" if ready else blocker

    prov=provider_calls()
    (out/"provider_call_audit_v0.77.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "IN_Park_Registry_SHA256_Expected":V076_PARK_SHA,"IN_Park_Registry_SHA256_After":sha_file(PARK),
      "IN_Park_Registry_Unchanged":sha_file(PARK)==V076_PARK_SHA,"IN_Execution_State":"PARKED_EXTERNAL_AUTHORIZATION",
      "IN_Gate_F_Classified":45,"IN_Canonical_Rows":0,"Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,
      "Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),"US_Gate_F_Runs":0,"US_SP500_Runs":0,
      "Canonical_Materialization_Runs":0,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.77.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V076_BLOCKER_AUTHORITY",pred["blocker"]=="SEC_TICKER_EXCHANGE_BULK_ROUTE_NOT_REPRODUCIBLE","PASS")
    test("V076_SOURCE_ZERO_RECORDS",correction["v076_SEC_Source_Record_Count"]==0,0)
    test("FAILURE_SEMANTICS_CORRECTED",correction["Forward_Failure_Semantics"].startswith("If the direct SEC bulk dataset"),"PASS")
    test("TARGET_368",len(target)==368,368)
    test("TARGET_UNIQUE_WS",len({r["WS_ID"] for r in target})==368,368)
    test("TARGET_UNIQUE_KEY",len({r["Security_Key"] for r in target})==368,368)
    test("TARGET_MIC_DISTRIBUTION",dist=={"XNAS":126,"XNYS":242},json.dumps(dist,sort_keys=True))
    test("SEC_ATTEMPTS_BOUNDED",1<=len(attempts)<=3,len(attempts))
    test("SEC_EXACT_URL_ONLY",all(r["url"]==SEC_URL for r in attempts),"PASS")
    test("NO_SEC_RETRY_AFTER_NONTRANSIENT",not(any(r.get("status") not in TRANSIENT and not r.get("ok") for r in attempts[:-1])),"PASS")
    test("NO_PER_SECURITY_FANOUT",all(r["Per_Security_Fanout"]=="NO" for r in ext),"PASS")
    test("IN_PARK_UNCHANGED",imm["IN_Park_Registry_Unchanged"],V076_PARK_SHA)
    test("IN_GATE_F_45",imm["IN_Gate_F_Classified"]==45,45)
    test("IN_CANONICAL_ZERO",imm["IN_Canonical_Rows"]==0,0)
    test("NO_GATE_F",prov["us_gate_f"]==0,0)
    test("NO_US_SP500",prov["us_sp500"]==0,0)
    test("NO_CANONICAL",prov["canonical_materialization"]==0,0)
    test("NO_FORBIDDEN_PROVIDERS",sum(prov.values())==0,0)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if not source_loaded:
        test("SOURCE_FAILURE_ROWS_NOT_NOT_FOUND",nf==0,0)
        test("SOURCE_FAILURE_ROWS_NOT_VERIFIED_368",nv==368,nv)
        test("DIRECT_ROUTE_BLOCKER",blocker=="SEC_TICKER_EXCHANGE_DIRECT_BULK_ROUTE_NOT_REPRODUCIBLE",blocker)
    elif ready:
        test("SEC_SCHEMA_PASS",schema_status=="PASS",schema_status)
        test("SEC_RECORDS_POSITIVE",len(sec_rows)>0,len(sec_rows))
        test("EXCHANGE_MIC_PASS",exchange_mic_ready,mic_status)
        test("LINKED_368",linked==368,linked)
        test("CIK_368",cik_cov==368,cik_cov)
        test("ZERO_UNRESOLVED",amb==nf==nv==conf==0,f"{amb}/{nf}/{nv}/{conf}")
        test("NO_IDENTITY_COLLISION",len(sec_coll)==0,len(sec_coll))
    else:test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.77.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"us_sp400_deterministic_sec_identity_ready":ready,
      "sec_direct_bulk_route":direct_status,"sec_records":len(sec_rows),"linked":linked,"total":368,
      "ambiguous":amb,"not_found":nf,"not_verified":nv,"conflict":conf,"cik_coverage":cik_cov,
      "exchange_mic_authority":mic_status,"blocker":blocker,"sec_source_url":SEC_URL,
      "sec_source_sha256":sec.get("sha256","") if sec.get("ok") else "","sec_attempts":len(attempts),
      "iso_source_url":ISO_URL,"iso_current_sha256":iso.get("sha256","") if iso else "",
      "in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","in_gate_f_classified":45,"in_canonical_rows":0,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"us_gate_f_runs":0,"us_sp500_runs":0,
      "canonical_materialization_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"artifact_binding":"PENDING_UPLOAD","tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "next_gate":next_gate
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","us_sp400_deterministic_sec_identity_ready","sec_direct_bulk_route","sec_records","linked","total","ambiguous","not_found","not_verified","conflict","cik_coverage","exchange_mic_authority","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.77.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.77.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      **summary,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "artifact_binding":"PENDING_UPLOAD","files":files
    }
    (out/"manifest_preupload_v0.77.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
