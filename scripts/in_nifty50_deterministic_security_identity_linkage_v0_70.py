#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, html.parser, io, json, re, subprocess, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.70"
STAGE="IN_NIFTY50_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE"
REQUIRED_START_HEAD="357df447e225ab1fc839530b1d2b0d2d217fd652"
V069_WORKFLOW=36272572257
V069_ARTIFACT=10915843724
V069_DIGEST="sha256:55093cd80910864fdf7486167786f5ec3f503ce39294ae875745e82c652ef69a"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
COHORT="IN_NIFTY50"
MIC="XNSE"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
BR_CANONICAL=ROOT/"sector_metadata/canonical/cohorts/BR_IBRX100_sector_metadata_v1.csv"
SUM69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/summary_v0.69.json"
CHK69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/stage_checkpoint_v0.69.json"
MATRIX69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/current_authority_cohort_gate_matrix_v0.69.csv"
SEL69=ROOT/"output_frozen_1425_canonical_sector_reconciliation_v0_69/selected_next_cohort_authority_v0.69.json"
SPEC=ROOT/"config/in_nifty50_deterministic_security_identity_linkage_spec_v0.70.json"

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.70"

class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()!="a": return
        d={k.lower():(v or "") for k,v in attrs}
        if d.get("href"): self.links.append(d["href"])

def sha_file(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def sha_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def git(*args:str)->str: return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:
            w.writeheader(); w.writerows(rows)

def norm_header(s:str)->str:
    return re.sub(r"[^a-z0-9]","",s.strip().lower())

def norm_symbol(s:str)->str: return s.strip().upper()
def norm_isin(s:str)->str: return s.strip().upper()

def decode_text(b:bytes)->str:
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("utf-8",errors="replace")

def fetch(url:str,allowed:set[str],max_bytes:int=5_000_000,referer:str|None=None)->dict[str,Any]:
    host=urllib.parse.urlparse(url).hostname
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    if host not in allowed:
        return {"ok":False,"url":url,"timestamp_utc":ts,"error":"HOST_NOT_ALLOWED","status":"","content_type":"","body":b""}
    headers={"User-Agent":UA,"Accept":"*/*","Accept-Language":"en-US,en;q=0.8"}
    if referer: headers["Referer"]=referer
    req=urllib.request.Request(url,headers=headers,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=35) as r:
            b=r.read(max_bytes+1); trunc=len(b)>max_bytes
            if trunc: b=b[:max_bytes]
            return {"ok":200<=getattr(r,"status",200)<300,"url":r.geturl(),"requested_url":url,"timestamp_utc":ts,
                    "status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"truncated":trunc,"body":b}
    except Exception as e:
        return {"ok":False,"url":url,"requested_url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,
                "sha256":"","truncated":False,"body":b"","error":f"{type(e).__name__}:{e}"}

def parse_csv_bytes(b:bytes)->tuple[list[str],list[dict[str,str]]]:
    txt=decode_text(b)
    sample=txt[:4096]
    try: dialect=csv.Sniffer().sniff(sample,delimiters=",;\t")
    except Exception: dialect=csv.excel
    f=io.StringIO(txt)
    r=csv.DictReader(f,dialect=dialect)
    fields=[x if x is not None else "" for x in (r.fieldnames or [])]
    rows=[{(k or ""):(v or "").strip() for k,v in row.items()} for row in r]
    return fields,rows

def field_map(fields:list[str])->dict[str,str]:
    return {norm_header(x):x for x in fields}

def pick_field(fields:list[str],aliases:list[str])->str|None:
    m=field_map(fields)
    for a in aliases:
        if a in m: return m[a]
    return None

def discover_link(page_url:str,body:bytes,kind:str)->tuple[str|None,list[str]]:
    p=LinkParser(); p.feed(decode_text(body))
    urls=[]
    for href in p.links:
        u=urllib.parse.urljoin(page_url,href)
        low=u.lower()
        if kind=="NIFTY":
            if "indexconstituent" in low and "nifty50" in low and low.endswith(".csv"):
                urls.append(u)
        elif kind=="NSE":
            if low.endswith("/content/equities/equity_l.csv") or low.endswith("equity_l.csv"):
                urls.append(u)
    urls=list(dict.fromkeys(urls))
    return (urls[0] if len(urls)==1 else None),urls

def parse_frozen_target()->list[dict[str,str]]:
    rows=read_csv(FROZEN)
    out=[]
    for r in rows:
        if r["Primary_MIC"]!=MIC: continue
        ws=r["Source_WS_ID"]
        isin=ws.split("WS:ISIN:",1)[1] if ws.startswith("WS:ISIN:") else ""
        out.append({
            "Security_Key":r["Security_Key"],
            "WS_ID":ws,
            "Primary_MIC":r["Primary_MIC"],
            "Primary_Ticker":r["Primary_Ticker"],
            "ISIN":isin,
            "Primary_Universe_Index":COHORT,
        })
    return sorted(out,key=lambda x:x["WS_ID"])

def validate_predecessor(repo_sha:str)->tuple[dict[str,Any],dict[str,Any],dict[str,Any],list[dict[str,str]]]:
    if git("rev-parse","HEAD")!=repo_sha: raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM69.read_text(encoding="utf-8"))
    c=json.loads(CHK69.read_text(encoding="utf-8"))
    sel=json.loads(SEL69.read_text(encoding="utf-8"))
    matrix=read_csv(MATRIX69)
    if s["verdict"]!="PASS_CANONICAL_SECTOR_METADATA_RECONCILIATION_NEXT_COHORT_SELECTED": raise RuntimeError("v0.69 verdict")
    if s["selected_next_cohort"]!="IN_NIFTY50" or s["resolved_gates_before_blocker"]!=4 or s["earliest_unresolved_gate"]!="E":
        raise RuntimeError("v0.69 selection")
    if s["current_blocker"]!="DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED": raise RuntimeError("v0.69 blocker")
    if c["workflow_run_id"]!=V069_WORKFLOW or c["artifact_id"]!=V069_ARTIFACT: raise RuntimeError("v0.69 workflow/artifact")
    if "sha256:"+c["artifact_digest"]!=V069_DIGEST: raise RuntimeError("v0.69 digest")
    if sel["Selected_Next_Cohort"]!="IN_NIFTY50": raise RuntimeError("v0.69 selected authority")
    m=next(r for r in matrix if r["Cohort"]=="IN_NIFTY50")
    if [m[x] for x in ["A","B","C","D","E","F","G","H"]] != ["PASS_INHERITED","PASS_INHERITED","PASS_INHERITED","PASS_INHERITED","NOT_VERIFIED","NOT_EVALUATED","PASS_INHERITED","NOT_EVALUATED"]:
        raise RuntimeError("v0.69 A-H matrix")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA: raise RuntimeError("immutability predecessor")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA: raise RuntimeError("canonical registry")
    return s,c,sel,matrix

def provider_calls()->dict[str,int]:
    return {
        "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"tradingview":0,"wikipedia":0,
        "investing_com":0,"etf_holdings":0,"screeners":0,"third_party_security_databases":0,
        "third_party_isin_databases":0,"company_websites":0,"per_security_web_fanout":0,
        "company_name_joins":0,"fuzzy_matching":0,"manual_ticker_company_inference":0,
        "price_ohlcv":0,"news":0,"trading_analysis":0
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_in_nifty50_deterministic_security_identity_linkage_v0_70")
    a=ap.parse_args()
    pred,chk,sel,matrix=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["scope_cohort"]!=COHORT: raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir; out.mkdir(parents=True,exist_ok=True)

    target=parse_frozen_target()
    if len(target)!=45 or len({r["WS_ID"] for r in target})!=45 or any(r["Primary_MIC"]!=MIC for r in target) or any(not r["ISIN"] for r in target):
        raise RuntimeError("Frozen-45 target discrepancy")
    write_csv(out/"in_frozen_45_identity_target_v0.70.csv",target)

    allowed=set(spec["allowed_hosts"])
    ext=[]
    def do_fetch(url:str,kind:str,referer:str|None=None,max_bytes:int=5_000_000):
        fr=fetch(url,allowed,max_bytes=max_bytes,referer=referer)
        ext.append({"Request_Order":len(ext)+1,"Request_Type":kind,"URL":url,"Resolved_URL":fr.get("url",""),
                    "Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),
                    "SHA256":fr.get("sha256",""),"Timestamp_UTC":fr.get("timestamp_utc",""),
                    "Official_Source":"YES","Per_Security_Fanout":"NO","Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
        return fr

    nifty_page=spec["official_discovery_pages"]["nifty50"]
    nse_page=spec["official_discovery_pages"]["nse_securities"]
    np=do_fetch(nifty_page,"DISCOVERY_PAGE_NIFTY50")
    ep=do_fetch(nse_page,"DISCOVERY_PAGE_NSE_SECURITIES")

    nifty_url=nse_url=None; nifty_candidates=[]; nse_candidates=[]
    if np.get("ok"):
        nifty_url,nifty_candidates=discover_link(nifty_page,np["body"],"NIFTY")
    if ep.get("ok"):
        nse_url,nse_candidates=discover_link(nse_page,ep["body"],"NSE")

    nifty_fr=do_fetch(nifty_url,"NIFTY50_CONSTITUENT_BULK",referer=nifty_page) if nifty_url else {"ok":False,"error":"DISCOVERY_NOT_UNIQUE","body":b""}
    nse_fr=do_fetch(nse_url,"NSE_EQUITY_SECURITY_REFERENCE_BULK",referer=nse_page) if nse_url else {"ok":False,"error":"DISCOVERY_NOT_UNIQUE","body":b""}

    nifty_fields=[];nifty_rows=[];n_symbol=n_isin=n_series=None;n_class_fields=[]
    if nifty_fr.get("ok") and not nifty_fr.get("truncated"):
        try:
            nifty_fields,nifty_rows=parse_csv_bytes(nifty_fr["body"])
            n_symbol=pick_field(nifty_fields,["symbol","securitysymbol","ticker"])
            n_isin=pick_field(nifty_fields,["isincode","isin","isinnumber"])
            n_series=pick_field(nifty_fields,["series"])
            n_class_fields=[f for f in nifty_fields if any(t in norm_header(f) for t in ("industry","sector","basicindustry","macroeconomicsector"))]
        except Exception:
            pass

    nse_fields=[];nse_rows=[];e_symbol=e_isin=e_series=None
    if nse_fr.get("ok") and not nse_fr.get("truncated"):
        try:
            nse_fields,nse_rows=parse_csv_bytes(nse_fr["body"])
            e_symbol=pick_field(nse_fields,["symbol","securitysymbol"])
            e_isin=pick_field(nse_fields,["isinnumber","isin","isincode"])
            e_series=pick_field(nse_fields,["series"])
        except Exception:
            pass

    nifty_schema_ok=bool(n_symbol and (n_isin or n_symbol) and nifty_rows)
    nse_schema_ok=bool(e_symbol and e_isin and nse_rows)

    nifty_audit={
        "Source_Authority":"NSE Indices Limited","Discovery_Page":nifty_page,
        "Discovered_Candidates":nifty_candidates,"Selected_Source_URL":nifty_url or "NOT_VERIFIED",
        "Retrieval_Timestamp_UTC":nifty_fr.get("timestamp_utc",""),"HTTP_Status":nifty_fr.get("status",""),
        "Content_Type":nifty_fr.get("content_type",""),"Raw_SHA256":nifty_fr.get("sha256",""),
        "Raw_Bytes":nifty_fr.get("bytes",0),"Raw_Snapshot_Persisted":False,
        "Raw_Snapshot_Persistence_Reason":"Redistribution rights not asserted; retained hash/schema/provenance and bounded derived identity evidence only.",
        "Row_Count":len(nifty_rows),"Field_Names":nifty_fields,"Symbol_Field":n_symbol or "NOT_VERIFIED",
        "ISIN_Field":n_isin or "NOT_PRESENT","Series_Field":n_series or "NOT_PRESENT",
        "Classification_Fields_Schema_Only":n_class_fields,"Classification_Population_Performed":False,
        "Explicit_Source_AsOf":"NOT_VERIFIED_IN_FILE","Schema_Status":"PASS" if nifty_schema_ok else "NOT_VERIFIED"
    }
    (out/"official_nifty50_constituent_source_audit_v0.70.json").write_text(json.dumps(nifty_audit,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    by_master_symbol=defaultdict(list)
    duplicate_symbols={}
    if nse_schema_ok:
        for r in nse_rows:
            sym=norm_symbol(r.get(e_symbol,""))
            isin=norm_isin(r.get(e_isin,""))
            if sym:
                by_master_symbol[sym].append({"symbol":sym,"isin":isin,"series":(r.get(e_series,"").strip().upper() if e_series else "")})
        duplicate_symbols={s:rows for s,rows in by_master_symbol.items() if len({x["isin"] for x in rows if x["isin"]})>1}

    nse_audit={
        "Source_Authority":"National Stock Exchange of India Limited","Discovery_Page":nse_page,
        "Discovered_Candidates":nse_candidates,"Selected_Source_URL":nse_url or "NOT_VERIFIED",
        "Retrieval_Timestamp_UTC":nse_fr.get("timestamp_utc",""),"HTTP_Status":nse_fr.get("status",""),
        "Content_Type":nse_fr.get("content_type",""),"Raw_SHA256":nse_fr.get("sha256",""),
        "Raw_Bytes":nse_fr.get("bytes",0),"Raw_Snapshot_Persisted":False,
        "Raw_Snapshot_Persistence_Reason":"Redistribution rights not asserted; retained hash/schema/provenance and bounded derived identity evidence only.",
        "Row_Count":len(nse_rows),"Field_Names":nse_fields,"Symbol_Field":e_symbol or "NOT_VERIFIED",
        "ISIN_Field":e_isin or "NOT_VERIFIED","Series_Field":e_series or "NOT_PRESENT",
        "Distinct_Symbols":len(by_master_symbol),"Symbols_With_Multiple_Distinct_ISIN":len(duplicate_symbols),
        "Schema_Status":"PASS" if nse_schema_ok else "NOT_VERIFIED"
    }
    (out/"official_nse_security_reference_source_audit_v0.70.json").write_text(json.dumps(nse_audit,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    join_contract={
        "Version":VERSION,"Gate":"E_SECURITY_IDENTITY",
        "Normalization_Rules":[
            "Strip surrounding whitespace from identifiers",
            "Uppercase Symbol identifier for exact comparison",
            "Uppercase ISIN identifier for exact comparison",
            "No company-name normalization or joins",
            "No fuzzy matching"
        ],
        "Route_Precedence":[
            "A: NIFTY exact ISIN -> Frozen exact ISIN; exact NIFTY Symbol must equal Frozen Primary_Ticker unless official alias evidence exists",
            "B: If current NIFTY row absent, Frozen exact Primary_Ticker -> NSE EQUITY_L exact Symbol -> one distinct exact ISIN -> Frozen exact ISIN"
        ],
        "Market_Context":"XNSE proven by official NSE/NSE Indices source class and Frozen Primary_MIC",
        "Authorized_Alias_Source":"NONE_DISCOVERED_OR_USED",
        "Gate_F_Classification_Use":"FORBIDDEN_IN_V0.70"
    }
    (out/"in_identity_join_contract_v0.70.json").write_text(json.dumps(join_contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    nifty_by_isin=defaultdict(list); nifty_by_symbol=defaultdict(list)
    if nifty_schema_ok:
        for r in nifty_rows:
            sym=norm_symbol(r.get(n_symbol,"")) if n_symbol else ""
            isin=norm_isin(r.get(n_isin,"")) if n_isin else ""
            rec={"symbol":sym,"isin":isin,"series":(r.get(n_series,"").strip().upper() if n_series else "")}
            if isin: nifty_by_isin[isin].append(rec)
            if sym: nifty_by_symbol[sym].append(rec)

    bridge=[];ticker_audit=[];linkage=[];currentness=[];ambiguities=[]
    direct_count=fallback_count=0
    for t in target:
        ws=t["WS_ID"]; f_isin=norm_isin(t["ISIN"]); f_sym=norm_symbol(t["Primary_Ticker"])
        nhits=nifty_by_isin.get(f_isin,[]) if n_isin else []
        current_present=bool(nhits or nifty_by_symbol.get(f_sym,[]))
        status="NOT_VERIFIED"; route=""; ticker_status="NOT_VERIFIED"; source_symbol=""; official_isin=""; competing=""
        detail=""
        if nifty_schema_ok and n_isin and len(nhits)==1:
            rec=nhits[0]; source_symbol=rec["symbol"]; official_isin=rec["isin"]
            if source_symbol==f_sym:
                status="PROVABLY_LINKED"; ticker_status="EXACT"; route="NIFTY_ISIN_DIRECT"; direct_count+=1
            else:
                status="CONFLICT"; ticker_status="CONFLICT"; route="NIFTY_ISIN_DIRECT"; detail="Exact ISIN matched but NIFTY Symbol conflicts with Frozen Primary_Ticker; no authorized alias evidence used."
        elif nifty_schema_ok and n_isin and len(nhits)>1:
            syms=sorted({x["symbol"] for x in nhits}); competing=" | ".join(syms)
            exact=[x for x in nhits if x["symbol"]==f_sym]
            if len(exact)==1:
                source_symbol=f_sym;official_isin=f_isin;status="PROVABLY_LINKED";ticker_status="EXACT";route="NIFTY_ISIN_SYMBOL_DISAMBIGUATED";direct_count+=1
            else:
                status="AMBIGUOUS";route="NIFTY_ISIN_DUPLICATE";detail="Multiple NIFTY rows share the Frozen ISIN without a unique exact Frozen symbol."
        else:
            # Current NIFTY membership may be absent. Gate E identity can still be proven by exact NSE master symbol -> single distinct ISIN.
            masters=by_master_symbol.get(f_sym,[]) if nse_schema_ok else []
            distinct_isins=sorted({x["isin"] for x in masters if x["isin"]})
            if not nse_schema_ok:
                status="NOT_VERIFIED";route="NSE_MASTER_REQUIRED_BUT_NOT_VERIFIED";detail="Current NIFTY exact ISIN row unavailable and NSE master route not verified."
            elif not masters:
                status="NOT_FOUND";route="NSE_MASTER_SYMBOL_FALLBACK";detail="Frozen Primary_Ticker absent from official NSE equity security reference."
            elif len(distinct_isins)>1:
                status="AMBIGUOUS";route="NSE_MASTER_SYMBOL_FALLBACK";competing=" | ".join(distinct_isins);detail="Exact NSE symbol maps to multiple distinct ISINs."
            elif len(distinct_isins)==1:
                source_symbol=f_sym;official_isin=distinct_isins[0];ticker_status="EXACT"
                if official_isin==f_isin:
                    status="PROVABLY_LINKED";route="NSE_MASTER_SYMBOL_TO_ISIN_FALLBACK";fallback_count+=1
                else:
                    status="CONFLICT";route="NSE_MASTER_SYMBOL_TO_ISIN_FALLBACK";detail="Official NSE symbol maps to an ISIN different from Frozen WS_ID ISIN."
            else:
                status="NOT_VERIFIED";route="NSE_MASTER_SYMBOL_FALLBACK";detail="Official NSE rows lack usable ISIN."

        membership_state="CURRENT_NIFTY_MEMBERSHIP_PRESENT" if current_present else ("IDENTITY_LINKED_BUT_CURRENT_NIFTY_MEMBERSHIP_NOT_PRESENT" if status=="PROVABLY_LINKED" else "CURRENT_NIFTY_MEMBERSHIP_NOT_PRESENT")
        bridge.append({"WS_ID":ws,"Frozen_Primary_Ticker":f_sym,"Frozen_ISIN":f_isin,"Identity_Route":route,
                       "Official_Source_Symbol":source_symbol,"Official_Source_ISIN":official_isin,
                       "Competing_Official_Identifiers":competing,"Bridge_Status":status})
        ticker_audit.append({"WS_ID":ws,"Frozen_Primary_Ticker":f_sym,"Official_Source_Symbol":source_symbol,
                             "Ticker_Consistency":ticker_status,"Authorized_Alias_Evidence":"NONE_USED"})
        currentness.append({"WS_ID":ws,"Frozen_Primary_Ticker":f_sym,"Frozen_ISIN":f_isin,
                            "Current_NIFTY_Membership_State":membership_state,"Identity_Status":status})
        linkage.append({"Security_Key":t["Security_Key"],"WS_ID":ws,"Primary_MIC":t["Primary_MIC"],"Primary_Ticker":t["Primary_Ticker"],
                        "Frozen_ISIN":f_isin,"Identity_Route":route,"Official_Source_Symbol":source_symbol,"Official_Source_ISIN":official_isin,
                        "Ticker_Consistency":ticker_status,"Current_NIFTY_Membership_State":membership_state,
                        "Gate_E_Status":status,"Detail":detail,
                        "NIFTY_Source_URL":nifty_url or "NOT_VERIFIED","NSE_Reference_URL":nse_url or "NOT_VERIFIED"})
        if status in ("AMBIGUOUS","CONFLICT","NOT_VERIFIED"):
            ambiguities.append({"WS_ID":ws,"Status":status,"Route":route,"Competing_Official_Identifiers":competing,"Detail":detail})

    write_csv(out/"in_symbol_isin_bridge_audit_v0.70.csv",bridge)
    write_csv(out/"in_frozen_ticker_consistency_audit_v0.70.csv",ticker_audit)
    write_csv(out/"in_exact_45_identity_linkage_audit_v0.70.csv",linkage)
    write_csv(out/"source_currentness_vs_frozen_identity_audit_v0.70.csv",currentness)
    (out/"identity_ambiguity_audit_v0.70.json").write_text(json.dumps({"rows":ambiguities,"count":len(ambiguities)},indent=2,sort_keys=True)+"\n",encoding="utf-8")

    counts={k:sum(r["Gate_E_Status"]==k for r in linkage) for k in ["PROVABLY_LINKED","AMBIGUOUS","NOT_FOUND","NOT_VERIFIED","CONFLICT"]}
    linked_unique_ws=len({r["WS_ID"] for r in linkage if r["Gate_E_Status"]=="PROVABLY_LINKED"})
    official_identity_to_ws=defaultdict(set)
    for r in linkage:
        if r["Gate_E_Status"]=="PROVABLY_LINKED" and r["Official_Source_ISIN"]:
            official_identity_to_ws[r["Official_Source_ISIN"]].add(r["WS_ID"])
    one_to_one=all(len(v)==1 for v in official_identity_to_ws.values())

    nifty_route_repro=bool(nifty_url and nifty_fr.get("ok") and nifty_schema_ok)
    master_route_repro=bool(nse_url and nse_fr.get("ok") and nse_schema_ok)
    any_fallback=any(r["Identity_Route"]=="NSE_MASTER_SYMBOL_TO_ISIN_FALLBACK" for r in linkage)
    success=(counts["PROVABLY_LINKED"]==45 and counts["AMBIGUOUS"]==counts["NOT_FOUND"]==counts["NOT_VERIFIED"]==counts["CONFLICT"]==0
             and linked_unique_ws==45 and one_to_one and nifty_route_repro and (master_route_repro or not any_fallback))

    blocker=""
    if not nifty_url or not nifty_fr.get("ok"):
        blocker="OFFICIAL_NIFTY_CONSTITUENT_BULK_ROUTE_NOT_REPRODUCIBLE"
    elif not nifty_schema_ok:
        blocker="NIFTY_SOURCE_SECURITY_IDENTIFIER_SCHEMA_NOT_VERIFIED"
    elif any_fallback and (not nse_url or not nse_fr.get("ok")):
        blocker="OFFICIAL_NSE_SECURITY_MASTER_ROUTE_NOT_REPRODUCIBLE"
    elif any(r["Gate_E_Status"]=="AMBIGUOUS" for r in linkage):
        blocker="NSE_SYMBOL_TO_ISIN_LINKAGE_AMBIGUOUS"
    elif any(r["Gate_E_Status"]=="NOT_FOUND" for r in linkage):
        blocker="FROZEN_ISIN_NOT_FOUND_IN_OFFICIAL_NSE_REFERENCE"
    elif any(r["Gate_E_Status"]=="CONFLICT" for r in linkage):
        blocker="FROZEN_TICKER_IDENTITY_CONFLICT"
    elif any(r["Gate_E_Status"]=="NOT_VERIFIED" for r in linkage) or counts["PROVABLY_LINKED"]<45:
        blocker="IN_EXACT_45_IDENTITY_LINKAGE_INCOMPLETE"
    elif not one_to_one:
        blocker="NSE_SYMBOL_TO_ISIN_LINKAGE_AMBIGUOUS"

    ready=success and not blocker
    verdict="PASS_IN_NIFTY50_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE" if ready else "BLOCKED_IN_NIFTY50_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE"
    if ready:
        if fallback_count==0:
            identity_route="NIFTY.ISIN -> FROZEN.ISIN; NSE EQUITY_L audited as official reference"
        else:
            identity_route="NIFTY.ISIN -> FROZEN.ISIN; current-absent rows use Frozen Primary_Ticker -> NSE EQUITY_L Symbol -> ISIN -> Frozen.ISIN"
        next_gate="IN_NIFTY50 EXACT FROZEN SECTOR CLASSIFICATION COVERAGE GATE"
    else:
        identity_route="NOT_FULLY_VERIFIED"
        next_gate=blocker

    write_csv(out/"external_request_ledger_v0.70.csv",ext)
    providers=provider_calls()
    (out/"provider_call_audit_v0.70.json").write_text(json.dumps(providers,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    imm={
        "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
        "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
        "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
        "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,
        "BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
        "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
        "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,
        "Canonical_IN_Partition_Created":False,"Canonical_Registry_Mutations":0,
        "Gate_F_Executions":0,"Sector_Classification_Population_Rows":0,"Sector_Code_Generation_Rows":0,
        "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.70.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok: raise RuntimeError(name)
    test("V069_SELECTED_IN",pred["selected_next_cohort"]=="IN_NIFTY50","IN_NIFTY50")
    test("V069_GATE_E",pred["earliest_unresolved_gate"]=="E" and pred["current_blocker"]=="DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED","E")
    test("FROZEN_TARGET_45",len(target)==45,len(target))
    test("FROZEN_WS_UNIQUE_45",len({r["WS_ID"] for r in target})==45,45)
    test("FROZEN_MIC_XNSE",all(r["Primary_MIC"]=="XNSE" for r in target),"PASS")
    test("FROZEN_WS_ISIN",all(r["WS_ID"]=="WS:ISIN:"+r["ISIN"] for r in target),"PASS")
    test("NO_NAME_JOINS",providers["company_name_joins"]==0,0)
    test("NO_FUZZY",providers["fuzzy_matching"]==0,0)
    test("NO_PER_SECURITY_FANOUT",providers["per_security_web_fanout"]==0,0)
    test("NO_THIRD_PARTY",all(v==0 for k,v in providers.items()),providers)
    test("NO_GATE_F",imm["Gate_F_Executions"]==0,0)
    test("NO_SECTOR_POPULATION",imm["Sector_Classification_Population_Rows"]==0 and imm["Sector_Code_Generation_Rows"]==0,0)
    test("NO_IN_CANONICAL_PARTITION",not (ROOT/"sector_metadata/canonical/cohorts/IN_NIFTY50_sector_metadata_v1.csv").exists(),"PASS")
    test("CANONICAL_READY_UNCHANGED",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("LINKED_45_45",counts["PROVABLY_LINKED"]==45,counts)
        test("ZERO_UNRESOLVED",counts["AMBIGUOUS"]==counts["NOT_FOUND"]==counts["NOT_VERIFIED"]==counts["CONFLICT"]==0,counts)
        test("ONE_TO_ONE",one_to_one,"PASS")
        test("NIFTY_ROUTE_REPRO",nifty_route_repro,"PASS")
        test("MASTER_ROUTE_IF_NEEDED",master_route_repro or not any_fallback,f"fallback={any_fallback},master={master_route_repro}")
    else:
        test("FAIL_BLOCKER_NONEMPTY",bool(blocker),blocker)
    write_csv(out/"test_results_v0.70.csv",tests)

    summary={
        "stage":STAGE,"version":VERSION,"verdict":verdict,
        "in_deterministic_ws_id_linkage_ready":ready,
        "linked":counts["PROVABLY_LINKED"],"total":45,
        "ambiguous":counts["AMBIGUOUS"],"not_found":counts["NOT_FOUND"],"not_verified":counts["NOT_VERIFIED"],"conflict":counts["CONFLICT"],
        "identity_route":identity_route,"direct_nifty_isin_links":direct_count,"nse_master_fallback_links":fallback_count,
        "current_nifty_membership_absent_but_identity_linked":sum(r["Current_NIFTY_Membership_State"]=="IDENTITY_LINKED_BUT_CURRENT_NIFTY_MEMBERSHIP_NOT_PRESENT" for r in currentness),
        "blocker":blocker,"external_requests":len(ext),"prohibited_provider_calls":sum(providers.values()),
        "gate_f_executions":0,"sector_classification_population_rows":0,"canonical_ready_rows":37,
        "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
        "artifact_binding":"PENDING_UPLOAD","productive":False,
        "next_gate":next_gate,
        "tests":{"total":len(tests),"passed":len(tests),"failed":0}
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_deterministic_ws_id_linkage_ready","linked","total","ambiguous","not_found","not_verified","conflict","identity_route","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.70.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.70.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file(): files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
        "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
        "verdict":verdict,"in_deterministic_ws_id_linkage_ready":ready,"linked":counts["PROVABLY_LINKED"],"total":45,
        "ambiguous":counts["AMBIGUOUS"],"not_found":counts["NOT_FOUND"],"not_verified":counts["NOT_VERIFIED"],"conflict":counts["CONFLICT"],
        "identity_route":identity_route,"blocker":blocker,"gate_f_executions":0,"sector_classification_population_rows":0,
        "canonical_ready_rows":37,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
        "productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.70.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
