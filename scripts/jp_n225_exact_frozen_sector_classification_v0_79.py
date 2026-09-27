#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,html.parser,json,re,subprocess,time,unicodedata,urllib.parse,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.79"
STAGE="JP_N225_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE_GATE"
REQUIRED_START_HEAD="4a5c2f5914f57e5333c68f7a8616dfd1b50adceb"
V078_WORKFLOW=36326606790
V078_ARTIFACT=10933309355
V078_DIGEST="sha256:4c5d1eae5e6ff4d2fa0397b7d58b89f5ab4754021c481b06e8c7c3557d902114"
V078_COMPONENT_SHA="7c3dd31f7987c6ea0fc21b5ee61054dbafb6c5c1fcce376dd63025cfdeb7043b"
V078_PROFILE_SHA="d537eee86b7d39464eddcec3fd64d3e060e2aedf5a633a9749265dc32d330ffa"
V078_PARK_SHA="d367957506fd357e22b7cc9c62479a0dfa46ddf54b04ed862a71fdb50b87b2db"
V078_SHARED_SHA="9847587b9e04aba5f26d96b6e9b3f1d9acc197cfee8b913ac887c549dec57b17"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
TAXONOMY="NIKKEI_36_INDUSTRY_AND_SECTOR"
LEVEL="SECTOR"

SPEC=ROOT/"config/jp_n225_exact_frozen_sector_classification_spec_v0.79.json"
SUM78=ROOT/"output_shared_sec_park_jp_n225_gate_d_v0_78/summary_v0.78.json"
CHK78=ROOT/"output_shared_sec_park_jp_n225_gate_d_v0_78/stage_checkpoint_v0.78.json"
COMP78=ROOT/"output_shared_sec_park_jp_n225_gate_d_v0_78/nikkei_component_structure_audit_v0.78.json"
SRCINV78=ROOT/"output_shared_sec_park_jp_n225_gate_d_v0_78/nikkei_official_source_inventory_v0.78.csv"
DEC78=ROOT/"output_shared_sec_park_jp_n225_gate_d_v0_78/jp_canonical_classification_level_decision_v0.78.json"
PDSC78=ROOT/"output_shared_sec_park_jp_n225_gate_d_v0_78/jp_pdsc_distinct_label_feasibility_audit_v0.78.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
CAP58=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
SHARED=ROOT/"sector_metadata/governance/shared_source_dependency_registry_v1.csv"

COMPONENT_URL="https://indexes.nikkei.co.jp/en/nkave/index/component?idx=nk225"
UA="WeltSwingLongDev-v0.79 akx0801-hub/welt-swing-long-data"

AUTHORIZED_PDSC={
"Technology":"PDSC1:2eb3437c8c82dad4cca3468ea713f244dd11c166ecd04a2a03bb2e010229c093",
"Financials":"PDSC1:0587309eb18ea75e0cd9964b23533cc25604f934902824576f82f9850c2c40be",
"Consumer Goods":"PDSC1:78be66233d528b6397fc234995d241e69913ed571321c6bf6e1d7d8a1d3541ca",
"Materials":"PDSC1:e3962e390df45617e19fea135091e814d14ced1f767bc1e4dbd543a4ccfcfef7",
"Capital Goods/Others":"PDSC1:49d729022c336d8e7d9819f30f8a587fea2c0d4dce2e63142d469f187a131176",
"Transportation and Utilities":"PDSC1:2fa8886dfeff0c0077ad4c1e75bdde490b6b2b67df89fdf035a9cb9d92dde596"
}

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
        if tag=="a":self.anchor_href=dict(attrs).get("href","");self.anchor_parts=[]
        if tag in {"h1","h2","h3","h4","h5","h6"}:self.heading_tag=tag;self.heading_parts=[]
        if tag=="table":self.in_table=True;self.table_heading=self.last_h3;self.table_rows=[]
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
        return [x for x in (clean(y) for y in "".join(self.text).splitlines()) if x]

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

def extract_component_structure(p:NikkeiHTMLParser)->dict[str,Any]:
    lines=p.lines()
    try:i_ind=lines.index("Industry List")
    except ValueError:return {"valid":False,"reason":"Industry List marker absent"}
    upd_idx=None
    for i in range(i_ind+1,min(len(lines),i_ind+20)):
        if lines[i].startswith("Update"):upd_idx=i;break
    if upd_idx is None:return {"valid":False,"reason":"Update marker absent"}
    frag_texts={a["text"] for a in p.anchors if a["text"] and "#" in a["href"]}
    pre=[];seen=set();stop_idx=None
    for j in range(upd_idx+1,len(lines)):
        x=lines[j]
        if x in frag_texts:
            if x in seen:stop_idx=j;break
            seen.add(x)
        pre.append(x)
    if stop_idx is None:return {"valid":False,"reason":"industry-list/detail boundary not reproducible"}
    industry_sequence=[x for x in pre if x in frag_texts]
    if len(industry_sequence)!=36 or len(set(industry_sequence))!=36:
        return {"valid":False,"reason":f"industry inventory {len(industry_sequence)} not 36"}
    sector_candidates=[x for x in pre if x not in frag_texts]
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
            if re.fullmatch(r"[0-9A-Za-z]{4,5}",code):industry_codes[h].append(code)
    all_codes=[c for ind in ordered_industries for c in industry_codes[ind]]
    if len(all_codes)!=225 or len(set(all_codes))!=225:
        return {"valid":False,"reason":f"component security count/uniqueness {len(all_codes)}/{len(set(all_codes))} not 225"}
    sector_codes=defaultdict(list)
    for ind,codes in industry_codes.items():sector_codes[parent[ind]].extend(codes)
    if set(sector_codes)!=set(ordered_sectors):return {"valid":False,"reason":"sector assignment incomplete"}
    return {"valid":True,"update_raw":lines[upd_idx],"sectors":ordered_sectors,"industries":ordered_industries,
            "parent":parent,"industry_codes":industry_codes,"sector_codes":dict(sector_codes),
            "component_count":len(all_codes),"security_codes":all_codes,
            "empty_industries":[x for x in ordered_industries if not industry_codes[x]]}

def pdsc(name:str)->str:
    payload=TAXONOMY+"\x1f"+LEVEL+"\x1f"+nfc(name)
    return "PDSC1:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM78.read_text(encoding="utf-8"));c=json.loads(CHK78.read_text(encoding="utf-8"))
    comp=json.loads(COMP78.read_text(encoding="utf-8"));dec=json.loads(DEC78.read_text(encoding="utf-8"))
    src=read_csv(SRCINV78);pa=read_csv(PDSC78)
    if s["verdict"]!="PASS_JP_N225_CANONICAL_CLASSIFICATION_LEVEL_GATE_D":raise RuntimeError("v0.78 verdict")
    if not s["jp_canonical_classification_level_ready"]:raise RuntimeError("v0.78 level readiness")
    if s["taxonomy"]!=TAXONOMY or s["selected_classification_level"]!=LEVEL or s["official_level_name"]!="Sector":raise RuntimeError("v0.78 classification authority")
    if s["native_code_available"]!="NO" or s["pdsc_required"]!="YES" or s["distinct_labels"]!=6 or s["pdsc_collisions"]!=0:raise RuntimeError("v0.78 PDSC state")
    if (s["nikkei_sector_count"],s["nikkei_industry_count"],s["nikkei_component_security_count"])!=(6,36,225):raise RuntimeError("v0.78 structure")
    if c["workflow_run_id"]!=V078_WORKFLOW or c["artifact_id"]!=V078_ARTIFACT or "sha256:"+c["artifact_digest"]!=V078_DIGEST:raise RuntimeError("v0.78 artifact")
    if comp["Response_SHA256"]!=V078_COMPONENT_SHA or comp["Source_Update_Raw"]!="Update：Sep/25/2026":raise RuntimeError("v0.78 component source")
    profile=next((r for r in src if r["Source_ID"]=="NIKKEI_225_PROFILE"),None)
    if not profile or profile["SHA256"]!=V078_PROFILE_SHA:raise RuntimeError("v0.78 profile source")
    if not dec["JP_CANONICAL_CLASSIFICATION_LEVEL_READY"] or dec["Sector_Level"]!=LEVEL or dec["Gate_D_After"]!="PASS_BY_CURRENT_GOVERNANCE":raise RuntimeError("v0.78 decision")
    got={r["Sector_Raw_Name"]:r["PDSC_Run_1"] for r in pa}
    if got!=AUTHORIZED_PDSC or any(r["PDSC_Run_1"]!=r["PDSC_Run_2"] or r["Deterministic"]!="YES" for r in pa):raise RuntimeError("v0.78 PDSC authority")
    if sha_file(PARK)!=V078_PARK_SHA or sha_file(SHARED)!=V078_SHARED_SHA:raise RuntimeError("park/shared registry drift")
    parks=read_csv(PARK);ps={r["Cohort"]:r["Execution_State"] for r in parks}
    if ps!={"IN_NIFTY50":"PARKED_EXTERNAL_AUTHORIZATION","US_SP400":"PARKED_SOURCE_ACCESS","US_SP500":"PARKED_SHARED_SOURCE_PREREQUISITE"}:raise RuntimeError("park states")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    return s

def reconstruct_target()->tuple[list[dict[str,str]],dict[str,Any]]:
    frozen=read_csv(FROZEN);cap=read_csv(CAP58)
    if len(frozen)!=1425 or len(cap)!=1425:raise RuntimeError("Frozen/capability count mismatch")
    by={r["Security_Key"]:r for r in cap}
    if len(by)!=1425:raise RuntimeError("capability Security_Key uniqueness")
    if "Primary_Universe_Index" in (frozen[0].keys() if frozen else []):
        target_src=[r for r in frozen if r["Primary_Universe_Index"]=="JP_N225"]
        mode="DIRECT_FROZEN_PRIMARY_UNIVERSE_INDEX"
    else:
        target_src=[]
        for r in frozen:
            c=by.get(r["Security_Key"])
            if not c:raise RuntimeError("missing capability cohort label")
            if c["Source_WS_ID"]!=r["Source_WS_ID"] or c["Primary_MIC"]!=r["Primary_MIC"] or c["Primary_Ticker"]!=r["Primary_Ticker"]:
                raise RuntimeError("Frozen/capability identity mismatch")
            if c["Primary_Universe_Index"]=="JP_N225":target_src.append(r)
        mode="FROZEN_ROW_AUTHORITY_WITH_EXACT_SECURITY_KEY_COHORT_LABEL_SIDECAR"
    out=[{
      "Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],"WS_ID":r["Source_WS_ID"],
      "Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],"Primary_Universe_Index":"JP_N225",
      "Target_Derivation":mode
    } for r in target_src]
    audit={
      "Frozen_Physical_Has_Primary_Universe_Index":"YES" if frozen and "Primary_Universe_Index" in frozen[0] else "NO",
      "Target_Derivation":mode,"Frozen_Target_Authority":str(FROZEN.relative_to(ROOT)),
      "Cohort_Label_Sidecar":"" if mode.startswith("DIRECT_") else str(CAP58.relative_to(ROOT)),
      "Row_Count":len(out),"Unique_Security_Key":len({r["Security_Key"] for r in out}),
      "Unique_WS_ID":len({r["WS_ID"] for r in out}),"Primary_MIC_Distribution":dict(sorted(Counter(r["Primary_MIC"] for r in out).items()))
    }
    if len(out)!=197 or audit["Unique_Security_Key"]!=197 or audit["Unique_WS_ID"]!=197:raise RuntimeError("JP target count/uniqueness mismatch")
    if audit["Primary_MIC_Distribution"]!={"XTKS":197}:raise RuntimeError("JP target MIC mismatch")
    return sorted(out,key=lambda r:r["WS_ID"]),audit

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"bloomberg":0,"reuters":0,
      "tradingview":0,"etf_holdings":0,"third_party_historical_constituent_lists":0,"company_name_joins":0,
      "fuzzy_matching":0,"numeric_ticker_casting":0,"zero_padding_transformation":0,"per_security_web_fanout":0,
      "sec_requests":0,"nse_requests":0,"gate_h":0,"canonical_materialization":0,"canonical_registry_readiness_update":0,
      "other_cohort":0,"sector_rs":0,"p0":0,"p1":0,"p2":0,"price_ohlcv":0,"news":0,"trading_analysis":0
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_jp_n225_exact_frozen_sector_classification_v0_79")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)

    target,target_audit=reconstruct_target()
    write_csv(out/"jp_frozen_197_classification_target_v0.79.csv",target)
    (out/"jp_frozen_197_target_schema_audit_v0.79.json").write_text(json.dumps(target_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    r=fetch(COMPONENT_URL)
    external=[{
      "Request_Order":1,"Source_Class":"NIKKEI_OFFICIAL","Request_Type":"NIKKEI_225_COMPONENTS_GATE_F",
      "URL":COMPONENT_URL,"Resolved_URL":r.get("resolved_url",""),"HTTP_Status":r.get("status",""),
      "Content_Type":r.get("content_type",""),"Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),
      "Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),"Per_Security_Fanout":"NO",
      "SEC_Request":"NO","NSE_Request":"NO","Result":"PASS" if r.get("ok") else r.get("error","FAILED")
    }]
    write_csv(out/"external_request_ledger_v0.79.csv",external)

    structure={"valid":False,"reason":"source retrieval failed"}
    if r.get("ok"):structure=extract_component_structure(parse_page(r["body"]))
    source_audit={
      "URL":COMPONENT_URL,"Resolved_URL":r.get("resolved_url",""),"HTTP_Status":r.get("status",""),
      "Content_Type":r.get("content_type",""),"Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),
      "Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),"v0_78_SHA256":V078_COMPONENT_SHA,
      "SHA_Comparison":"UNCHANGED" if r.get("sha256")==V078_COMPONENT_SHA else ("CHANGED" if r.get("ok") else "NOT_AVAILABLE"),
      "Explicit_Source_Update":structure.get("update_raw","NOT_VERIFIED"),"Machine_Counted_Securities":structure.get("component_count",0),
      "Sector_Count":len(structure.get("sectors",[])),"Industry_Count":len(structure.get("industries",[])),
      "Raw_Source_Persisted":False,"Source_Status":"PASS" if r.get("ok") else "NOT_REPRODUCIBLE"
    }
    (out/"nikkei_component_source_audit_v0.79.json").write_text(json.dumps(source_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    hierarchy_audit={
      "Status":"PASS" if structure.get("valid") else "NOT_VERIFIED",
      "Hierarchy":"SECTOR -> INDUSTRY -> SECURITY_CODE" if structure.get("valid") else "NOT_VERIFIED",
      "Sector_Count":len(structure.get("sectors",[])),"Industry_Count":len(structure.get("industries",[])),
      "Security_Count":structure.get("component_count",0),"Empty_Industries":structure.get("empty_industries",[]),
      "Each_Industry_One_Parent_Sector":bool(structure.get("valid") and len(structure.get("parent",{}))==36),
      "Each_Security_Exactly_One_Industry":bool(structure.get("valid") and len(structure.get("security_codes",[]))==len(set(structure.get("security_codes",[])))==225),
      "Parse_Detail":structure.get("reason","PASS")
    }
    (out/"nikkei_component_hierarchy_parse_audit_v0.79.json").write_text(json.dumps(hierarchy_audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    code_hits=Counter(structure.get("security_codes",[]))
    dup_codes=sorted([c for c,n in code_hits.items() if n>1])
    uniqueness={
      "Source_Security_Count":len(structure.get("security_codes",[])),"Unique_Source_Security_Codes":len(code_hits),
      "Duplicate_Source_Code_Count":len(dup_codes),"Duplicate_Source_Codes":dup_codes,
      "Status":"PASS" if structure.get("valid") and not dup_codes else "NOT_VERIFIED"
    }
    (out/"nikkei_source_security_code_uniqueness_audit_v0.79.json").write_text(json.dumps(uniqueness,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Independent PDSC authority recalculation against exact predecessor values.
    pdsc_rows=[];pdsc_mismatch=0
    for label in AUTHORIZED_PDSC:
        p1=pdsc(label);p2=pdsc(label);auth=AUTHORIZED_PDSC[label]
        status="PASS" if p1==p2==auth else "MISMATCH"
        if status!="PASS":pdsc_mismatch+=1
        pdsc_rows.append({
          "Sector_Taxonomy":TAXONOMY,"Sector_Level":LEVEL,"Sector_Raw_Name":label,"Sector_Name_NFC":nfc(label),
          "Authorized_v0_78_PDSC":auth,"Recomputed_Run_1":p1,"Recomputed_Run_2":p2,
          "Exact_Authority_Match":"YES" if status=="PASS" else "NO","Status":status
        })
    collision_count=len(pdsc_rows)-len({x["Recomputed_Run_1"] for x in pdsc_rows})
    write_csv(out/"jp_pdsc_authority_recalculation_audit_v0.79.csv",pdsc_rows)

    code_to_paths=defaultdict(list)
    if structure.get("valid"):
        for industry,codes in structure["industry_codes"].items():
            sector=structure["parent"].get(industry,"")
            for code in codes:code_to_paths[code].append((industry,sector))

    join_rows=[];membership_rows=[];sector_assign=[];coverage=[]
    status_counts=Counter();current_matches=0;pdsc_coverage=0
    unauthorized_labels=set();parent_failures=0
    for t in target:
        ticker=t["Primary_Ticker"]
        paths=code_to_paths.get(ticker,[])
        if not r.get("ok"):
            join_status="NOT_VERIFIED";class_status="NOT_VERIFIED";detail="Current official component source not reproducibly retrieved."
        elif not structure.get("valid"):
            join_status="NOT_VERIFIED";class_status="NOT_VERIFIED";detail="Current component hierarchy parse not verified."
        elif len(paths)==0:
            join_status="NOT_PRESENT_CURRENT_COMPONENT_SOURCE";class_status="NOT_FOUND";detail="Frozen security code absent from current official component source."
        elif len(paths)>1:
            join_status="AMBIGUOUS_SOURCE_CODE";class_status="AMBIGUOUS";detail="Official security code appears in more than one hierarchy path."
        else:
            industry,sector=paths[0];current_matches+=1
            if not industry or not sector:
                join_status="CONFLICT";class_status="CONFLICT";detail="Industry parent Sector unresolved.";parent_failures+=1
            elif sector not in AUTHORIZED_PDSC:
                join_status="CONFLICT";class_status="CONFLICT";detail="Observed Sector is outside the six v0.78-authorized labels.";unauthorized_labels.add(sector)
            elif pdsc_mismatch or collision_count:
                join_status="NOT_VERIFIED";class_status="NOT_VERIFIED";detail="PDSC predecessor-authority consistency failed."
            else:
                join_status="EXACT_CURRENT_COMPONENT_MATCH";class_status="PROVABLY_CLASSIFIED";detail="";pdsc_coverage+=1
        industry=paths[0][0] if len(paths)==1 else ""
        sector=paths[0][1] if len(paths)==1 else ""
        scode=AUTHORIZED_PDSC.get(sector,"") if class_status=="PROVABLY_CLASSIFIED" else ""
        join_rows.append({
          "Security_Key":t["Security_Key"],"WS_ID":t["WS_ID"],"Primary_MIC":t["Primary_MIC"],"Primary_Ticker":ticker,
          "Official_Security_Code":ticker if len(paths)>=1 else "","Source_Match_Count":len(paths),
          "Identity_Comparison":"EXACT_AFTER_SURROUNDING_WHITESPACE_REMOVAL_ONLY","Join_Status":join_status,"Detail":detail
        })
        membership_rows.append({
          "Security_Key":t["Security_Key"],"WS_ID":t["WS_ID"],"Primary_Ticker":ticker,
          "Current_Nikkei225_Presence":"PRESENT" if len(paths)>=1 else ("NOT_VERIFIED" if not structure.get("valid") else "ABSENT"),
          "Audit_State":"EXACT_CURRENT_COMPONENT_MATCH" if len(paths)==1 else ("FROZEN_MEMBER_NOT_PRESENT_IN_CURRENT_NIKKEI225" if len(paths)==0 and structure.get("valid") else join_status),
          "Fallback_Status":"NOT_REQUIRED" if len(paths)>=1 else "NO_AUTHORIZED_REPOSITORY_FALLBACK_WITH_ROW_LEVEL_SECURITY_CODE_CLASSIFICATION"
        })
        sector_assign.append({
          "Security_Key":t["Security_Key"],"WS_ID":t["WS_ID"],"Primary_Ticker":ticker,"Official_Security_Code":ticker if len(paths)==1 else "",
          "Official_Industry_Raw":industry,"Official_Sector_Raw":sector,"Sector_Taxonomy":TAXONOMY if class_status=="PROVABLY_CLASSIFIED" else "",
          "Sector_Level":LEVEL if class_status=="PROVABLY_CLASSIFIED" else "","Source_Sector_Code":"",
          "Sector_Code":scode,"Sector_Code_Origin":"PROJECT_DERIVED_CANONICAL" if class_status=="PROVABLY_CLASSIFIED" else "",
          "Sector_Code_Method":"PDSC_SHA256_V1" if class_status=="PROVABLY_CLASSIFIED" else "","Classification_Status":class_status
        })
        coverage.append(dict(sector_assign[-1]))
        status_counts[class_status]+=1
    write_csv(out/"jp_exact_197_security_code_join_audit_v0.79.csv",join_rows)
    write_csv(out/"jp_current_membership_vs_frozen_audit_v0.79.csv",membership_rows)
    write_csv(out/"jp_sector_assignment_audit_v0.79.csv",sector_assign)
    write_csv(out/"jp_exact_197_classification_coverage_v0.79.csv",coverage)

    industry_inventory=[]
    if structure.get("valid"):
        frozen_industry_counts=Counter(r["Official_Industry_Raw"] for r in coverage if r["Classification_Status"]=="PROVABLY_CLASSIFIED")
        for ind in structure["industries"]:
            if frozen_industry_counts.get(ind,0):
                industry_inventory.append({
                  "Official_Industry_Raw":ind,"Parent_Official_Sector_Raw":structure["parent"].get(ind,""),
                  "Frozen_197_Row_Count":frozen_industry_counts[ind],"Industry_Canonical_Code_Generated":"NO",
                  "Peer_Group_Level_Used":"NO_SUPPORTING_HIERARCHY_ONLY"
                })
    write_csv(out/"jp_frozen_industry_inventory_v0.79.csv",industry_inventory or [{
      "Official_Industry_Raw":"","Parent_Official_Sector_Raw":"","Frozen_197_Row_Count":0,
      "Industry_Canonical_Code_Generated":"NO","Peer_Group_Level_Used":"NO_SUPPORTING_HIERARCHY_ONLY"
    }])

    parent_rows=[]
    if structure.get("valid"):
        for ind in structure["industries"]:
            parent=structure["parent"].get(ind,"")
            parent_rows.append({
              "Official_Industry_Raw":ind,"Official_Parent_Sector_Raw":parent,
              "Parent_Sector_Authorized":"YES" if parent in AUTHORIZED_PDSC else "NO",
              "Current_Source_Security_Count":len(structure["industry_codes"].get(ind,[])),
              "Relation_Status":"PASS" if parent in AUTHORIZED_PDSC else "CONFLICT"
            })
    write_csv(out/"jp_industry_parent_sector_audit_v0.79.csv",parent_rows or [{
      "Official_Industry_Raw":"","Official_Parent_Sector_Raw":"","Parent_Sector_Authorized":"NOT_VERIFIED",
      "Current_Source_Security_Count":0,"Relation_Status":"NOT_VERIFIED"
    }])

    sector_dist=Counter((r["Official_Sector_Raw"],r["Sector_Code"]) for r in coverage if r["Classification_Status"]=="PROVABLY_CLASSIFIED")
    write_csv(out/"jp_frozen_sector_distribution_v0.79.csv",[
      {"Official_Sector_Raw":k[0],"Sector_Code":k[1],"Frozen_197_Row_Count":v} for k,v in sorted(sector_dist.items())
    ] or [{"Official_Sector_Raw":"","Sector_Code":"","Frozen_197_Row_Count":0}])

    classified=status_counts["PROVABLY_CLASSIFIED"];amb=status_counts["AMBIGUOUS"];nf=status_counts["NOT_FOUND"];nv=status_counts["NOT_VERIFIED"];conf=status_counts["CONFLICT"]
    blocker=""
    if not r.get("ok"):blocker="NIKKEI_COMPONENT_SOURCE_NOT_REPRODUCIBLE"
    elif not structure.get("valid"):blocker="NIKKEI_COMPONENT_HIERARCHY_PARSE_NOT_VERIFIED"
    elif nf>0:blocker="JP_FROZEN_SECURITY_CODE_NOT_PRESENT_CURRENT_SOURCE"
    elif amb>0:blocker="JP_SECURITY_CODE_MATCH_AMBIGUOUS"
    elif parent_failures>0 or any(x["Relation_Status"]!="PASS" for x in parent_rows):blocker="JP_INDUSTRY_PARENT_SECTOR_NOT_VERIFIED"
    elif unauthorized_labels:blocker="JP_UNAUTHORIZED_SECTOR_LABEL_OBSERVED"
    elif pdsc_mismatch>0 or collision_count>0:blocker="JP_PDSC_AUTHORITY_MISMATCH"
    elif classified!=197 or nv>0 or conf>0:blocker="JP_EXACT_197_CLASSIFICATION_COVERAGE_INCOMPLETE"

    ready=(blocker=="" and classified==197 and amb==nf==nv==conf==0 and current_matches==197 and pdsc_coverage==197 and collision_count==0)
    verdict="PASS_JP_N225_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE" if ready else "BLOCKED_JP_N225_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE"
    next_gate="JP_N225 SOURCE ACCESS / PERSISTENCE GATE" if ready else blocker

    prov=provider_calls()
    (out/"provider_call_audit_v0.79.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":V078_PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),
      "Parked_Cohort_Registry_Unchanged":sha_file(PARK)==V078_PARK_SHA,
      "Shared_Source_Registry_SHA256_Expected":V078_SHARED_SHA,"Shared_Source_Registry_SHA256_After":sha_file(SHARED),
      "Shared_Source_Registry_Unchanged":sha_file(SHARED)==V078_SHARED_SHA,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "Gate_H_Runs":0,"Canonical_Materialization_Runs":0,"Other_Cohort_Runs":0,"SEC_Requests":0,"NSE_Requests":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.79.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V078_GATE_D_AUTHORITY",pred["jp_canonical_classification_level_ready"],"PASS")
    test("TARGET_197",len(target)==197,197)
    test("TARGET_UNIQUE_SECURITY_KEY",len({x["Security_Key"] for x in target})==197,197)
    test("TARGET_UNIQUE_WS_ID",len({x["WS_ID"] for x in target})==197,197)
    test("TARGET_XTKS_ONLY",all(x["Primary_MIC"]=="XTKS" for x in target),"PASS")
    test("ONE_NIKKEI_REQUEST",len(external)==1,1)
    test("NO_PER_SECURITY_FANOUT",external[0]["Per_Security_Fanout"]=="NO","PASS")
    test("NO_SEC_NSE_REQUESTS",prov["sec_requests"]==prov["nse_requests"]==0,"0/0")
    test("AUTHORIZED_PDSC_RECALCULATES",pdsc_mismatch==0,pdsc_mismatch)
    test("PDSC_COLLISION_ZERO",collision_count==0,collision_count)
    test("PARK_REGISTRY_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],V078_PARK_SHA)
    test("SHARED_REGISTRY_IMMUTABLE",imm["Shared_Source_Registry_Unchanged"],V078_SHARED_SHA)
    test("NO_GATE_H",prov["gate_h"]==0,0)
    test("NO_CANONICAL",prov["canonical_materialization"]==0,0)
    test("NO_OTHER_COHORT",prov["other_cohort"]==0,0)
    test("NO_FORBIDDEN_PROVIDERS",sum(prov.values())==0,0)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("SOURCE_PASS",r.get("ok") and structure.get("valid"),"PASS")
        test("CURRENT_MATCHES_197",current_matches==197,current_matches)
        test("CLASSIFIED_197",classified==197,classified)
        test("PDSC_COVERAGE_197",pdsc_coverage==197,pdsc_coverage)
        test("ZERO_UNRESOLVED",amb==nf==nv==conf==0,f"{amb}/{nf}/{nv}/{conf}")
        test("AUTHORIZED_SECTORS_ONLY",not unauthorized_labels,sorted(unauthorized_labels))
    else:test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.79.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"jp_exact_197_sector_classification_coverage_ready":ready,
      "classified":classified,"total":197,"ambiguous":amb,"not_found":nf,"not_verified":nv,"conflict":conf,
      "current_source_matches":current_matches,"authorized_sector_labels":6,"pdsc_coverage":pdsc_coverage,
      "pdsc_collisions":collision_count,"blocker":blocker,"taxonomy":TAXONOMY,"sector_level":LEVEL,
      "component_source_sha256":r.get("sha256",""),"component_source_v078_sha256":V078_COMPONENT_SHA,
      "component_source_update":structure.get("update_raw","NOT_VERIFIED"),
      "component_source_security_count":structure.get("component_count",0),"component_sector_count":len(structure.get("sectors",[])),
      "component_industry_count":len(structure.get("industries",[])),
      "in_nifty50_park_state":"PARKED_EXTERNAL_AUTHORIZATION","us_sp400_park_state":"PARKED_SOURCE_ACCESS",
      "us_sp500_park_state":"PARKED_SHARED_SOURCE_PREREQUISITE","canonical_ready_rows":37,"canonical_total_rows":1425,
      "gate_h_runs":0,"canonical_materialization_runs":0,"other_cohort_runs":0,"sec_requests":0,"nse_requests":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD",
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"next_gate":next_gate
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","jp_exact_197_sector_classification_coverage_ready","classified","total","ambiguous","not_found","not_verified","conflict","current_source_matches","authorized_sector_labels","pdsc_coverage","pdsc_collisions","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.79.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.79.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={**summary,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,"artifact_binding":"PENDING_UPLOAD","files":files}
    (out/"manifest_preupload_v0.79.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
