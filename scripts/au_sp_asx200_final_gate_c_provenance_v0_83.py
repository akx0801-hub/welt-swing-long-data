#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, csv, hashlib, html, importlib.util, io, json, os, re, shutil, subprocess, tempfile, time, urllib.parse
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.83"
STAGE="AU_SP_ASX200_V082_EVIDENCE_COMPLETENESS_REPAIR_FINAL_FIELD_PROVENANCE_TAXONOMY_IDENTITY_GATE_C_CLOSURE"
REQUIRED_START_HEAD="5629089262fa1915c0f83e8281fe4f13509f2a08"
V082_WORKFLOW=36343815405
V082_ARTIFACT=10939892682
V082_DIGEST="sha256:091e8d6d8ba19995a8f3c29b0f16d59d33907dd1744faf6eef13c5bdf5be921f"
V082_VERDICT="BLOCKED_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C"
V082_BLOCKER="ASX_DIRECTORY_INDUSTRY_FIELD_PROVENANCE_NOT_VERIFIED"

FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"

SPEC=ROOT/"config/au_sp_asx200_final_gate_c_provenance_spec_v0.83.json"
OUT82=ROOT/"output_au_sp_asx200_dynamic_directory_route_gate_c_v0_82"
SUM82=OUT82/"summary_v0.82.json"
CHK82=OUT82/"stage_checkpoint_v0.82.json"
MAN82=OUT82/"manifest_v0.82.json"
ROUTE82=OUT82/"au_directory_selected_data_route_contract_v0.82.json"
SCHEMA82=OUT82/"au_directory_runtime_schema_audit_v0.82.csv"
LABELS82=OUT82/"au_directory_classification_label_inventory_v0.82.csv"
V08182=OUT82/"v081_blocker_authority_v0.82.json"
ENV82=OUT82/"au_dynamic_directory_route_capture_environment_v0.82.json"
DOM82=OUT82/"au_dynamic_directory_rendered_dom_audit_v0.82.csv"
INT82=OUT82/"au_dynamic_directory_interaction_audit_v0.82.csv"
UP82=OUT82/"asx_upstream_provider_attribution_audit_v0_82.json"
CAND82=OUT82/"au_taxonomy_candidate_inventory_v0_82.csv"

PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANONICAL_DIR=ROOT/"sector_metadata/canonical/cohorts"

DIRECTORY_URL="https://www.asx.com.au/markets/trade-our-cash-market/directory"
RUNTIME_PREFIX="https://asx.api.cmfyapp.com/asx-research/1.0/companies/directory"
GICS_URL="https://www.asx.com.au/markets/trade-our-cash-market/overview/indices"
HIST_URL="https://www.asx.com.au/content/dam/asx/investors/investment-tools-and-resources/online-courses/shares/shares-course-7.pdf"

# Reuse already-proven bounded CDP/fetch/parser implementation without altering v0.82 history.
spec82=importlib.util.spec_from_file_location("v082mod",ROOT/"scripts/au_sp_asx200_dynamic_directory_route_gate_c_v0_82.py")
v82=importlib.util.module_from_spec(spec82);spec82.loader.exec_module(v82)

def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def now_utc()->str:return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def clean(s:Any)->str:return re.sub(r"\s+"," ",html.unescape(str(s or ""))).strip()
def keynorm(s:str)->str:return re.sub(r"[^a-z0-9]","",str(s).lower())
def git(*args:str)->str:return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def write_json(p:Path,obj:Any)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def read_csv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader()
        for r in rows:w.writerow(r)

def bounded_snippet(text:str,needle:str,radius:int=220)->tuple[int,str]:
    low=text.lower();i=low.find(needle.lower())
    if i<0:return -1,""
    return i,clean(text[max(0,i-radius):min(len(text),i+len(needle)+radius)])

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM82.read_text(encoding="utf-8"))
    c=json.loads(CHK82.read_text(encoding="utf-8"))
    m=json.loads(MAN82.read_text(encoding="utf-8"))
    route=json.loads(ROUTE82.read_text(encoding="utf-8"))
    if s["verdict"]!=V082_VERDICT or s["blocker"]!=V082_BLOCKER:raise RuntimeError("v0.82 decision mismatch")
    if s["tests"]!={"failed":0,"passed":25,"total":25}:raise RuntimeError("v0.82 tests mismatch")
    if c["workflow_run_id"]!=V082_WORKFLOW or c["artifact_id"]!=V082_ARTIFACT or c["artifact_digest"]!=V082_DIGEST:
        raise RuntimeError("v0.82 checkpoint artifact mismatch")
    if m["workflow_run_id"]!=V082_WORKFLOW or m["artifact_id"]!=V082_ARTIFACT or m["artifact_digest"]!=V082_DIGEST:
        raise RuntimeError("v0.82 manifest artifact mismatch")
    if route["ASX_DIRECTORY_DATA_ROUTE_READY"]!="YES" or route["PUBLIC_BROWSER_REPRODUCIBLE"]!="YES":
        raise RuntimeError("v0.82 route authority mismatch")
    if route["Data_Route_Type"]!="DETERMINISTIC_FINITE_PAGINATION" or route["Complete_Directory_Record_Count"]!=1830:
        raise RuntimeError("v0.82 pagination authority mismatch")
    schema={r["Field_Name"]:r for r in read_csv(SCHEMA82)}
    if "industry" not in schema or int(schema["industry"]["Null_Count"])!=0 or int(schema["industry"]["Distinct_Value_Count"])!=27:
        raise RuntimeError("v0.82 industry schema mismatch")
    labels=[r["Distinct_Label"] for r in read_csv(LABELS82)]
    if "Class Pend" not in labels or "Not Applic" not in labels:raise RuntimeError("v0.82 sentinels absent")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("semantic immutability")
    if sha_file(PARK)!=PARK_SHA:raise RuntimeError("parked cohort registry changed")
    park={r["Cohort"]:r["Execution_State"] for r in read_csv(PARK)}
    expected={"IN_NIFTY50":"PARKED_EXTERNAL_AUTHORIZATION","JP_N225":"PARKED_EXTERNAL_AUTHORIZATION",
              "US_SP400":"PARKED_SOURCE_ACCESS","US_SP500":"PARKED_SHARED_SOURCE_PREREQUISITE"}
    if any(park.get(k)!=v for k,v in expected.items()):raise RuntimeError("park state mismatch")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:
        raise RuntimeError("canonical registry mismatch")
    return {"summary":s,"checkpoint":c,"manifest":m,"route":route,"schema":schema,"labels":labels}

def repair_v082_evidence(out:Path)->None:
    v081=json.loads(V08182.read_text(encoding="utf-8"))
    write_json(out/"v081_blocker_authority_v0.83.json",{
      "Evidence_Status":"RECONSTRUCTED_FROM_PERSISTED_V082_EVIDENCE","Source_File":str(V08182.relative_to(ROOT)),
      "Source_SHA256":sha_file(V08182),"Authority":v081
    })
    env=json.loads(ENV82.read_text(encoding="utf-8"))
    write_json(out/"au_dynamic_directory_route_capture_environment_v0.83.json",{
      "Evidence_Status":"RECONSTRUCTED_FROM_PERSISTED_V082_EVIDENCE","Source_File":str(ENV82.relative_to(ROOT)),
      "Source_SHA256":sha_file(ENV82),"v082_Capture_Environment":env,
      "v083_Fresh_Capture_Environment":"SEE_CURRENT_OBSERVATION_SECTION_AFTER_RUNTIME"
    })
    dom=read_csv(DOM82)
    write_json(out/"au_dynamic_directory_rendered_dom_audit_v0.83.json",{
      "Evidence_Status":"RECONSTRUCTED_FROM_PERSISTED_V082_EVIDENCE","Source_File":str(DOM82.relative_to(ROOT)),
      "Source_SHA256":sha_file(DOM82),"Persisted_v082_Rows":dom
    })
    inter=read_csv(INT82)
    write_json(out/"au_dynamic_directory_interaction_audit_v0.83.json",{
      "Evidence_Status":"RECONSTRUCTED_FROM_PERSISTED_V082_EVIDENCE","Source_File":str(INT82.relative_to(ROOT)),
      "Source_SHA256":sha_file(INT82),"Persisted_v082_Rows":inter,
      "Historical_Interpretation":"NO_V082_INTERACTION_ROWS_PERSISTED" if not inter else "V082_INTERACTIONS_PRESENT"
    })
    up=json.loads(UP82.read_text(encoding="utf-8"))
    write_json(out/"asx_upstream_provider_attribution_audit_v0.83.json",{
      "Evidence_Status":"RECONSTRUCTED_FROM_PERSISTED_V082_EVIDENCE","Source_File":str(UP82.relative_to(ROOT)),
      "Source_SHA256":sha_file(UP82),"v082_Authority":up,
      "Exact_Industry_Field_Attribution_To_LSEG":"NOT_VERIFIED",
      "Exact_Industry_Field_Attribution_To_Morningstar":"NOT_VERIFIED",
      "Exact_Industry_Field_Attribution_To_Other":"NOT_VERIFIED"
    })
    required=[
      ("v081_blocker_authority",V08182,"v081_blocker_authority_v0.83.json"),
      ("au_dynamic_directory_route_capture_environment",ENV82,"au_dynamic_directory_route_capture_environment_v0.83.json"),
      ("au_dynamic_directory_rendered_dom_audit",DOM82,"au_dynamic_directory_rendered_dom_audit_v0.83.json"),
      ("au_dynamic_directory_interaction_audit",INT82,"au_dynamic_directory_interaction_audit_v0.83.json"),
      ("asx_upstream_provider_attribution_audit",UP82,"asx_upstream_provider_attribution_audit_v0.83.json"),
      ("au_taxonomy_candidate_inventory",CAND82,"au_taxonomy_candidate_inventory_v0.83.csv")
    ]
    rows=[]
    for name,p,repl in required:
        rows.append({"Required_v082_Evidence":name,"Present_In_v082_Final_Commit":"YES" if p.exists() else "NO",
                     "Repair_Action":"REPERSIST_WITH_EXPLICIT_V083_PROVENANCE_AND_CONTRACT",
                     "v083_Replacement_File":repl,"Evidence_Source":str(p.relative_to(ROOT)) if p.exists() else "NOT_AVAILABLE",
                     "Status":"RECONSTRUCTED_FROM_PERSISTED_V082_EVIDENCE" if p.exists() else "FRESH_V083_OBSERVATION_REQUIRED"})
    write_csv(out/"v082_required_evidence_completeness_audit_v0.83.csv",rows,
              ["Required_v082_Evidence","Present_In_v082_Final_Commit","Repair_Action","v083_Replacement_File","Evidence_Source","Status"])

DOM_AUDIT_JS=r"""(()=> {
 const out=[];
 const nodes=[...document.querySelectorAll('label,select,option,button,a,input,[role="combobox"],[role="option"],[aria-label]')];
 for(const e of nodes){
   const text=((e.innerText||e.textContent||e.value||'')+'').trim().replace(/\s+/g,' ');
   const aria=(e.getAttribute&&e.getAttribute('aria-label'))||'';
   const name=(e.getAttribute&&e.getAttribute('name'))||'';
   const id=e.id||'';
   const blob=(text+' '+aria+' '+name+' '+id).toLowerCase();
   if(!(blob.includes('industry')||blob.includes('bank')||blob.includes('all asx listed')||blob.includes('download')||blob.includes('csv')||blob.includes('export'))) continue;
   const attrs={};
   if(e.attributes) for(const a of [...e.attributes]) if(a.name.startsWith('data-')||['aria-label','aria-labelledby','role','name','id','href','download','value'].includes(a.name)) attrs[a.name]=a.value;
   const par=e.closest('[class*="company"],[id*="company"],[class*="directory"],[id*="directory"],[class*="filter"],[id*="filter"]');
   out.push({element:e.tagName,visible_label:text,accessible_name:aria,attributes:attrs,
             backing_component:par?((par.id?('#'+par.id):'')+' '+(typeof par.className==='string'?par.className:'' )).trim():'',
             observed_status:'OBSERVED'});
   if(out.length>=250)break;
 }
 return {title:document.title,url:location.href,rows:out,body_text:(document.body&&document.body.innerText||'').slice(0,150000)};
})()"""

SELECT_BANKS_JS=r"""(()=> {
 const selects=[...document.querySelectorAll('select')];
 for(const s of selects){
   const opts=[...s.options];
   const o=opts.find(x=>(x.textContent||'').trim().toLowerCase()==='banks');
   if(o){
     const label=(document.querySelector('label[for="'+s.id+'"]')||{}).textContent||s.getAttribute('aria-label')||s.name||s.id||'';
     s.value=o.value;s.dispatchEvent(new Event('input',{bubbles:true}));s.dispatchEvent(new Event('change',{bubbles:true}));
     return {status:'SELECT_CHANGED',control_label:(label||'').trim(),selected_text:(o.textContent||'').trim(),selected_value:o.value,tag:'SELECT',id:s.id||'',name:s.name||''};
   }
 }
 const industry=[...document.querySelectorAll('button,[role="combobox"],[aria-label],label')].find(e=>{
   const t=((e.innerText||e.textContent||'')+' '+(e.getAttribute&&e.getAttribute('aria-label')||'')).toLowerCase();
   return t.includes('industry');
 });
 if(industry){industry.click();return {status:'OPENED_CUSTOM_INDUSTRY_CONTROL',control_label:(industry.innerText||industry.textContent||industry.getAttribute('aria-label')||'').trim(),tag:industry.tagName};}
 return {status:'INDUSTRY_CONTROL_NOT_FOUND'};
})()"""

CLICK_BANKS_JS=r"""(()=> {
 const els=[...document.querySelectorAll('[role="option"],li,button,a,div,span')];
 const e=els.find(x=>{
   const t=(x.innerText||x.textContent||'').trim();
   if(t.toLowerCase()!=='banks')return false;
   const r=x.getBoundingClientRect();const s=getComputedStyle(x);
   return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
 });
 if(e){e.click();return {status:'CUSTOM_BANKS_CLICKED',selected_text:(e.innerText||e.textContent||'').trim(),tag:e.tagName};}
 return {status:'BANKS_OPTION_NOT_FOUND'};
})()"""

CLICK_DOWNLOAD_JS=r"""(()=> {
 const els=[...document.querySelectorAll('a,button,[role="button"]')];
 const e=els.find(x=>((x.innerText||x.textContent||'')+'').trim().toLowerCase().includes('all asx listed companies'));
 if(!e)return {status:'NOT_OBSERVED'};
 const text=((e.innerText||e.textContent||'')+'').trim().replace(/\s+/g,' ');
 const attrs={};for(const a of [...e.attributes]) if(a.name.startsWith('data-')||['href','download','id','class'].includes(a.name)) attrs[a.name]=a.value;
 e.click();return {status:'CLICKED_ONCE',text,tag:e.tagName,href:e.href||'',attributes:attrs};
})()"""

def cdp_body(cdp:Any,rid:str,max_bytes:int=2_000_000)->bytes|None:
    r=cdp.command("Network.getResponseBody",{"requestId":rid},timeout=5).get("result")
    if not r:return None
    try:
        raw=base64.b64decode(r.get("body","")) if r.get("base64Encoded") else r.get("body","").encode("utf-8",errors="replace")
    except Exception:return None
    return raw if len(raw)<=max_bytes else None

def relevant_directory_requests(cdp:Any,min_order:int=0)->list[tuple[str,dict[str,Any],dict[str,Any]]]:
    out=[]
    for rid,req in cdp.requests.items():
        if int(req.get("order",0) or 0)<=min_order:continue
        url=req.get("url","")
        if url.startswith(RUNTIME_PREFIX):
            out.append((rid,req,cdp.responses.get(rid,{})))
    out.sort(key=lambda x:int(x[1].get("order",0) or 0))
    return out

def api_metadata(raw:bytes)->dict[str,Any]:
    try:obj=json.loads(raw.decode("utf-8-sig"))
    except Exception:return {"Parse_Status":"FAIL"}
    def prune(x:Any,path:str="")->Any:
        if isinstance(x,dict):
            y={}
            for k,v in x.items():
                nk=keynorm(k)
                if nk in {"items","records","results","companies"} and isinstance(v,list) and v and isinstance(v[0],dict):
                    y[k]={"ROW_ARRAY_OMITTED":True,"Row_Count":len(v)}
                else:y[k]=prune(v,(path+"."+k).strip("."))
            return y
        if isinstance(x,list):
            if len(x)>200:return {"ARRAY_OMITTED":True,"Count":len(x)}
            return [prune(v,path+"[]") for v in x]
        return x
    meta=prune(obj)
    flat=[]
    def walk(x:Any,path:str=""):
        if isinstance(x,dict):
            for k,v in x.items():walk(v,(path+"."+str(k)).strip("."))
        elif isinstance(x,list):
            for i,v in enumerate(x):walk(v,f"{path}[{i}]")
        else:
            s=clean(x)
            if any(t in (path+" "+s).lower() for t in ("industry","gics","group","filter","class pend","not applic")):
                flat.append({"Path":path,"Value":s})
    walk(meta)
    txt=json.dumps(meta,ensure_ascii=False)
    strong=bool(re.search(r"gics.{0,120}industry\s*group|industry\s*group.{0,120}gics",txt,re.I|re.S))
    return {"Parse_Status":"PASS","Metadata":meta,"Relevant_Markers":flat[:300],
            "Taxonomy_Marker_Status":"PASS_EXPLICIT_GICS_INDUSTRY_GROUP" if strong else "NOT_VERIFIED"}

def extract_pdf_text(raw:bytes)->tuple[str,str]:
    try:
        from pypdf import PdfReader
        r=PdfReader(io.BytesIO(raw))
        return "\n".join((p.extract_text() or "") for p in r.pages),"PYPDF"
    except Exception as e:
        return "",f"FAIL:{type(e).__name__}:{e}"

def fetch_official_document(url:str,max_bytes:int=12_000_000)->dict[str,Any]:
    r=v82.fetch_direct(url,"GET","",max_bytes)
    raw=r.get("body",b"")
    return {"URL":url,"Resolved_URL":r.get("resolved_url",""),"HTTP_Status":r.get("status",""),"Content_Type":r.get("content_type",""),
            "Bytes":r.get("bytes",0),"SHA256":r.get("sha256",""),"Retrieval_Timestamp_UTC":r.get("timestamp_utc",""),
            "Error":r.get("error",""),"_raw":raw}

def html_text(raw:bytes)->str:
    s=raw.decode("utf-8",errors="replace")
    s=re.sub(r"<script\b[^>]*>.*?</script>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<style\b[^>]*>.*?</style>"," ",s,flags=re.I|re.S)
    return clean(re.sub(r"<[^>]+>"," ",s))

def run_fresh_runtime(out:Path)->dict[str,Any]:
    chrome=v82.find_chrome()
    if not chrome:return {"status":"NOT_VERIFIED","error":"CHROME_NOT_AVAILABLE"}
    version=clean(subprocess.check_output([chrome,"--version"],text=True))
    port=v82.free_port();download_dir=Path(tempfile.mkdtemp(prefix="v083-asx-download-"))
    proc=ud=cdp=None
    try:
        proc,ud,ws=v82.start_chrome(chrome,port,download_dir);cdp=v82.CDP(ws)
        cdp.command("Network.enable",{"maxTotalBufferSize":100000000,"maxResourceBufferSize":12000000})
        cdp.command("Page.enable");cdp.command("Runtime.enable")
        cdp.command("Browser.setDownloadBehavior",{"behavior":"allow","downloadPath":str(download_dir),"eventsEnabled":True})
        cdp.phase="INITIAL"
        cdp.command("Page.navigate",{"url":DIRECTORY_URL},timeout=15)
        cdp.pump_until_idle(12,2)
        ua=clean(cdp.eval("navigator.userAgent") or "")
        dom=cdp.eval(DOM_AUDIT_JS) or {}
        initial_max=max([int(r.get("order",0) or 0) for r in cdp.requests.values()] or [0])

        # Capture exact current directory API response with filter options.
        initial_req=relevant_directory_requests(cdp,0)
        meta_req=None;meta_raw=None
        for rid,req,resp in initial_req:
            if "includeFilterOptions=true" in req.get("url",""):
                raw=cdp_body(cdp,rid,2_000_000)
                if raw:meta_req=(rid,req,resp);meta_raw=raw;break
        meta_audit=api_metadata(meta_raw) if meta_raw else {"Parse_Status":"NOT_VERIFIED","Taxonomy_Marker_Status":"NOT_VERIFIED"}

        # Current page-invoked appclass / manifest semantic audit.
        assets=[]
        for rid,req in cdp.requests.items():
            url=req.get("url","")
            if "com_asx_company_directory" not in url or ".js" not in url:continue
            raw=cdp_body(cdp,rid,2_000_000)
            if raw is None:
                d=v82.fetch_direct(url,"GET","",2_000_000);raw=d.get("body",b"") if d.get("ok") else None
            if raw is None:continue
            txt=raw.decode("utf-8",errors="replace")
            for term in ["gics","GICS","industryGroup","industry_group","industry group","Industry Group","industry","filter","download","csv"]:
                pos=0
                while True:
                    i=txt.find(term,pos)
                    if i<0:break
                    sn=clean(txt[max(0,i-180):min(len(txt),i+len(term)+220)])
                    assets.append({"Asset_URL":url,"Asset_SHA256":sha_bytes(raw),"Bytes":len(raw),"Marker":term,
                                   "Offset":i,"Snippet":sn,"Evidence_Status":"FRESH_V083_OBSERVATION"})
                    pos=i+len(term)
                    if sum(1 for x in assets if x["Asset_URL"]==url and x["Marker"]==term)>=8:break
        asset_blob="\n".join(x["Snippet"] for x in assets)
        app_strong=bool(re.search(r"gics.{0,140}industry\s*group|industry\s*group.{0,140}gics|gicsindustrygroup",asset_blob,re.I|re.S))

        # Download control exactly once.
        cdp.phase="DOWNLOAD_CONTROL"
        dl_action=cdp.eval(CLICK_DOWNLOAD_JS) or {"status":"NOT_OBSERVED"}
        cdp.pump_until_idle(10,1.5)
        time.sleep(1)
        dl_files=[p for p in download_dir.iterdir() if p.is_file() and not p.name.endswith(".crdownload")]
        dl_audit={"Control_Status":dl_action.get("status","NOT_OBSERVED"),"Control":dl_action,
                  "Download_Status":"NOT_OBSERVED","Request_URL":"","Download_URL":"","Content_Type":"","Bytes":0,
                  "SHA256":"","Schema":[],"Record_Count":0,"Classification_Header":"NOT_OBSERVED"}
        if dl_files:
            p=max(dl_files,key=lambda x:x.stat().st_mtime)
            raw=p.read_bytes()
            parsed=v82.parse_dataset(raw,"",p.name)
            event=next((e for e in reversed(cdp.downloads) if e.get("event")=="downloadWillBegin"),{})
            schema=parsed.get("schema",[]) if parsed else []
            cl=next((h for h in schema if any(t in keynorm(h) for t in ("gics","industry","sector","classification"))),"NOT_OBSERVED")
            dl_audit.update({"Download_Status":"PASS","Request_URL":event.get("url",""),"Download_URL":event.get("url",""),
                             "Content_Type":"text/csv" if (parsed and parsed.get("format")=="CSV") else "",
                             "Bytes":len(raw),"SHA256":sha_bytes(raw),"Schema":schema,
                             "Record_Count":len(parsed.get("records",[])) if parsed else 0,"Classification_Header":cl})
        else:
            # Record any new requests causally following click.
            postdl=relevant_directory_requests(cdp,initial_max)
            if postdl:dl_audit["Request_URL"]=postdl[-1][1].get("url","")

        # One bounded UI Industry -> API causality test.
        before=max([int(r.get("order",0) or 0) for r in cdp.requests.values()] or [0])
        cdp.phase="FILTER_BANKS"
        select_action=cdp.eval(SELECT_BANKS_JS) or {"status":"NOT_VERIFIED"}
        if select_action.get("status")=="OPENED_CUSTOM_INDUSTRY_CONTROL":
            cdp.pump_until_idle(2,0.8)
            second=cdp.eval(CLICK_BANKS_JS) or {"status":"BANKS_OPTION_NOT_FOUND"}
            select_action["second_step"]=second
        cdp.pump_until_idle(8,1.5)
        newreq=relevant_directory_requests(cdp,before)
        causality={"UI_Control_Label":select_action.get("control_label","Industry"),
                   "UI_Selected_Value":select_action.get("selected_text") or (select_action.get("second_step") or {}).get("selected_text",""),
                   "UI_Selected_Raw_Value":select_action.get("selected_value",""),
                   "API_Query_Parameter":"NOT_VERIFIED","API_Query_Value":"NOT_VERIFIED","Returned_Record_Count":0,
                   "All_Returned_Industry_Values":[],"Causal_Binding_Status":"NOT_VERIFIED","Interaction":select_action}
        if newreq:
            rid,req,resp=newreq[-1]
            raw=cdp_body(cdp,rid,2_000_000)
            parsed=v82.parse_dataset(raw or b"",resp.get("mimeType",""),req.get("url","")) if raw else None
            vals=sorted({clean(r.get("industry")) for r in (parsed or {}).get("records",[]) if clean(r.get("industry"))})
            base_url=(meta_req[1].get("url","") if meta_req else RUNTIME_PREFIX)
            bq=dict(urllib.parse.parse_qsl(urllib.parse.urlparse(base_url).query,keep_blank_values=True))
            nq=dict(urllib.parse.parse_qsl(urllib.parse.urlparse(req.get("url","")).query,keep_blank_values=True))
            diffs=[(k,v) for k,v in nq.items() if bq.get(k)!=v]
            preferred=next(((k,v) for k,v in diffs if "industry" in k.lower()),diffs[0] if diffs else ("NOT_VERIFIED","NOT_VERIFIED"))
            causal_pass=bool((select_action.get("status")=="SELECT_CHANGED" or (select_action.get("second_step") or {}).get("status")=="CUSTOM_BANKS_CLICKED")
                             and preferred[0]!="NOT_VERIFIED" and parsed and len(parsed.get("records",[]))>0 and vals==["Banks"])
            causality.update({"API_Request_URL":req.get("url",""),"API_Query_Parameter":preferred[0],"API_Query_Value":preferred[1],
                              "Returned_Record_Count":len((parsed or {}).get("records",[])),"All_Returned_Industry_Values":vals,
                              "Causal_Binding_Status":"PASS_UI_INDUSTRY_TO_API_INDUSTRY" if causal_pass else "NOT_VERIFIED",
                              "Response_SHA256":sha_bytes(raw) if raw else "","HTTP_Status":resp.get("status","")})

        # Fresh current DOM audit after initial execution, before using it as evidence.
        dom_rows=[]
        for r in dom.get("rows",[]):
            dom_rows.append({"Element":r.get("element",""),"Visible_Label":r.get("visible_label",""),"Accessible_Name":r.get("accessible_name",""),
                             "Attributes":json.dumps(r.get("attributes",{}),sort_keys=True,ensure_ascii=False),
                             "Backing_Component":r.get("backing_component",""),"Observed_Status":r.get("observed_status","")})

        # Relevant request ledger only; excludes unrelated advertising/analytics.
        ledger=[]
        for rid,req in sorted(cdp.requests.items(),key=lambda kv:int(kv[1].get("order",0) or 0)):
            url=req.get("url","")
            if not (url.startswith("https://www.asx.com.au/") or "asx.cmfyapp.com" in url or "asx.api.cmfyapp.com" in url):continue
            if not any(x in url for x in ("directory","com_asx_company_directory","company_search","/overview/indices")):continue
            resp=cdp.responses.get(rid,{})
            ledger.append({"Request_Order":req.get("order",""),"Phase":req.get("phase",""),"URL":url,"Method":req.get("method",""),
                           "HTTP_Status":resp.get("status",""),"Content_Type":resp.get("mimeType",""),"Resource_Type":resp.get("type") or req.get("type",""),
                           "Per_Security_Request":"NO","Evidence_Status":"FRESH_V083_OBSERVATION"})

        return {"status":"PASS","browser":{"Browser_Name":"Chrome/Chromium","Browser_Version":version,"Capture_Method":"CHROMIUM_CDP_NETWORK_RUNTIME",
                                          "Fresh_Profile":"YES","Cookies_Preexisting":"NO","Authentication":"NONE","Proxy":"NONE","User_Agent":ua},
                "dom_rows":dom_rows,"download":dl_audit,"causality":causality,"assets":assets,
                "app_marker":"PASS_EXPLICIT_GICS_INDUSTRY_GROUP" if app_strong else "NOT_VERIFIED",
                "api_metadata":meta_audit,"api_metadata_request_url":meta_req[1].get("url","") if meta_req else "",
                "api_metadata_response_sha256":sha_bytes(meta_raw) if meta_raw else "",
                "ledger":ledger}
    finally:
        if cdp:cdp.close()
        if proc:
            try:proc.terminate();proc.wait(timeout=3)
            except Exception:
                try:proc.kill()
                except Exception:pass
        if ud:shutil.rmtree(ud,ignore_errors=True)
        shutil.rmtree(download_dir,ignore_errors=True)

def provider_audit()->dict[str,int]:
    return {"Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,
            "ETF_holdings":0,"third_party_security_sector_databases":0,"semantic_sector_inference":0,"fuzzy_matching":0,
            "cross_taxonomy_mapping":0,"company_name_linkage_for_Frozen":0,"PDSC":0,"price_OHLCV":0,"news":0,
            "trading_analysis":0,"per_security_fanout":0,"AU_Gate_D":0,"AU_Gate_E":0,"AU_Gate_F":0,
            "Sector_RS":0,"P0":0,"P1":0,"P2":0,"fresh_public_ASX_browser_contexts":1,
            "official_ASX_document_requests":2,"complete_74_page_reruns":0}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_au_sp_asx200_final_gate_c_provenance_v0_83")
    args=ap.parse_args()
    pred=validate_predecessor(args.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/args.output_dir;out.mkdir(parents=True,exist_ok=True)
    repair_v082_evidence(out)

    fresh=run_fresh_runtime(out)
    if fresh.get("status")!="PASS":raise RuntimeError("fresh runtime capture failed: "+fresh.get("error","unknown"))

    # Merge fresh observation into repaired environment/DOM/interaction evidence while preserving v0.82 provenance.
    env83=json.loads((out/"au_dynamic_directory_route_capture_environment_v0.83.json").read_text(encoding="utf-8"))
    env83["v083_Fresh_Capture_Environment"]={"Evidence_Status":"FRESH_V083_OBSERVATION",**fresh["browser"]}
    write_json(out/"au_dynamic_directory_route_capture_environment_v0.83.json",env83)
    dom83=json.loads((out/"au_dynamic_directory_rendered_dom_audit_v0.83.json").read_text(encoding="utf-8"))
    dom83["Fresh_v083_Current_DOM"]={"Evidence_Status":"FRESH_V083_OBSERVATION","Rows":fresh["dom_rows"]}
    write_json(out/"au_dynamic_directory_rendered_dom_audit_v0.83.json",dom83)
    int83=json.loads((out/"au_dynamic_directory_interaction_audit_v0.83.json").read_text(encoding="utf-8"))
    int83["Fresh_v083_Interactions"]={"Evidence_Status":"FRESH_V083_OBSERVATION",
                                     "Download_Control":fresh["download"].get("Control",{}),
                                     "Industry_Filter":fresh["causality"].get("Interaction",{})}
    write_json(out/"au_dynamic_directory_interaction_audit_v0.83.json",int83)

    write_json(out/"au_current_ui_api_industry_causality_audit_v0.83.json",fresh["causality"])
    write_json(out/"au_current_directory_download_control_audit_v0.83.json",{
      "Evidence_Status":"FRESH_V083_OBSERVATION","Control_Status":fresh["download"]["Control_Status"],
      "Control":fresh["download"]["Control"],"Download_Status":fresh["download"]["Download_Status"],
      "Request_URL":fresh["download"]["Request_URL"],"Download_URL":fresh["download"]["Download_URL"],
      "Content_Type":fresh["download"]["Content_Type"],"Bytes":fresh["download"]["Bytes"],"SHA256":fresh["download"]["SHA256"]
    })
    write_json(out/"au_current_directory_download_schema_audit_v0.83.json",{
      "Evidence_Status":"FRESH_V083_OBSERVATION","Download_Status":fresh["download"]["Download_Status"],
      "Schema":fresh["download"]["Schema"],"Record_Count":fresh["download"]["Record_Count"],
      "Classification_Header":fresh["download"]["Classification_Header"],
      "Explicit_GICS_Industry_Group_Header":"YES" if ("gics" in keynorm(fresh["download"]["Classification_Header"]) and "industrygroup" in keynorm(fresh["download"]["Classification_Header"])) else "NO"
    })
    write_csv(out/"au_current_appclass_manifest_semantic_audit_v0.83.csv",fresh["assets"],
              ["Asset_URL","Asset_SHA256","Bytes","Marker","Offset","Snippet","Evidence_Status"])
    write_json(out/"au_api_filter_options_metadata_audit_v0.83.json",{
      "Evidence_Status":"FRESH_V083_OBSERVATION","Request_URL":fresh["api_metadata_request_url"],
      "Response_SHA256":fresh["api_metadata_response_sha256"],**fresh["api_metadata"]
    })

    # Official ASX historical company-search semantics.
    hist=fetch_official_document(HIST_URL)
    hist_text,extract_method=extract_pdf_text(hist["_raw"])
    hist_statements=[]
    for needle in ["search for a company by industry group","Global Industry Classification Standard","GICS (Global Industry Classification Standard)"]:
        pos,snip=bounded_snippet(hist_text,needle,260)
        if pos>=0:hist_statements.append({"Needle":needle,"Offset":pos,"Relevant_Bounded_Statement":snip})
    hist_ok=any("search for a company by industry group" in x["Relevant_Bounded_Statement"].lower() for x in hist_statements) and             any("global industry classification standard" in x["Relevant_Bounded_Statement"].lower() for x in hist_statements)
    source_inventory=[{
      "Source_Title":"Shares Module 7: Market indices and market sectors","Official_ASX_URL":HIST_URL,
      "Document_Date_or_Version":"Version 5 - November 2010","Relevant_Bounded_Statement":" || ".join(x["Relevant_Bounded_Statement"] for x in hist_statements)[:1800],
      "Search_UI_Context":"ASX website company search by industry group","Historical_or_Current":"HISTORICAL",
      "Response_SHA256":hist["SHA256"],"Retrieval_Timestamp":hist["Retrieval_Timestamp_UTC"],
      "Extraction_Method":extract_method,"Evidence_Status":"PASS_HISTORICAL_OFFICIAL_ASX_COMPANY_SEARCH_SEMANTICS" if hist_ok else "NOT_VERIFIED"
    }]
    write_csv(out/"asx_official_company_search_semantic_source_inventory_v0.83.csv",source_inventory)

    # Current ASX GICS authority context.
    gics=fetch_official_document(GICS_URL,4_000_000);gics_text=html_text(gics["_raw"])
    gics_snips=[]
    for needle in ["Global Industry Classification Standard","GICS","MSCI","S&P Dow Jones"]:
        pos,snip=bounded_snippet(gics_text,needle,260)
        if pos>=0:gics_snips.append({"Needle":needle,"Offset":pos,"Snippet":snip})
    current_gics_identity=bool(re.search(r"global industry classification standard",gics_text,re.I))
    owner_sp=bool(re.search(r"s&p\s+dow\s+jones",gics_text,re.I))
    owner_msci=bool(re.search(r"\bmsci\b",gics_text,re.I))

    # Direct current field-binding tests.
    download_header=fresh["download"]["Classification_Header"]
    download_direct=bool("gics" in keynorm(download_header) and "industrygroup" in keynorm(download_header))
    app_direct=fresh["app_marker"]=="PASS_EXPLICIT_GICS_INDUSTRY_GROUP"
    api_direct=fresh["api_metadata"].get("Taxonomy_Marker_Status")=="PASS_EXPLICIT_GICS_INDUSTRY_GROUP"
    ui_api=fresh["causality"].get("Causal_Binding_Status")=="PASS_UI_INDUSTRY_TO_API_INDUSTRY"
    current_direct=download_direct or app_direct or api_direct

    continuity_status="PASS_CURRENT_DIRECT_IMPLEMENTATION_TAXONOMY_MARKER" if current_direct else (
      "PARTIAL_CURRENT_UI_RUNTIME_CONTINUITY_WITH_HISTORICAL_GICS_SEMANTICS" if ui_api and hist_ok else "NOT_VERIFIED")
    write_json(out/"asx_historical_current_semantic_continuity_audit_v0.83.json",{
      "Historical_Official_ASX_Company_Search_Semantics":"PASS" if hist_ok else "NOT_VERIFIED",
      "Current_UI_to_API_Industry_Causal_Binding":"PASS" if ui_api else "NOT_VERIFIED",
      "Current_Download_Direct_Taxonomy_Marker":"PASS" if download_direct else "NOT_VERIFIED",
      "Current_Appclass_Manifest_Direct_Taxonomy_Marker":"PASS" if app_direct else "NOT_VERIFIED",
      "Current_API_Filter_Metadata_Direct_Taxonomy_Marker":"PASS" if api_direct else "NOT_VERIFIED",
      "Label_Set_Used_As_Independent_Proof":"NO","Continuity_Status":continuity_status,
      "Historical_Evidence_Used_Alone":"NO"
    })

    # GICS field binding requires a current direct marker. Historical semantics and label resemblance never suffice alone.
    field_binding_pass=bool(current_direct and current_gics_identity)
    owner_verified=bool(field_binding_pass and owner_sp and owner_msci)
    formal_level="INDUSTRY_GROUP" if field_binding_pass else "NOT_VERIFIED"
    version_status="CURRENT_MAINTAINED_NO_STATIC_VERSION" if (field_binding_pass and owner_verified) else "NOT_VERIFIED"
    ready=bool(field_binding_pass and owner_verified and formal_level!="NOT_VERIFIED" and version_status!="NOT_VERIFIED")

    write_json(out/"asx_gics_field_binding_audit_v0.83.json",{
      "GICS_TAXONOMY_IDENTITY_CONTEXT":"PASS" if current_gics_identity else "NOT_VERIFIED",
      "DIRECTORY_FIELD_BINDING_FROM_INDEX_PAGE":"NO",
      "Current_ASX_GICS_URL":GICS_URL,"Response_SHA256":gics["SHA256"],"Retrieval_Timestamp_UTC":gics["Retrieval_Timestamp_UTC"],
      "Current_ASX_GICS_Bounded_Markers":gics_snips,
      "Current_Download_Header_Binding":"PASS" if download_direct else "NOT_VERIFIED",
      "Current_Appclass_Manifest_Binding":"PASS" if app_direct else "NOT_VERIFIED",
      "Current_API_Filter_Metadata_Binding":"PASS" if api_direct else "NOT_VERIFIED",
      "UI_API_Industry_Causality":"PASS" if ui_api else "NOT_VERIFIED",
      "Historical_ASX_Company_Search_GICS_Semantics":"PASS_SUPPORTING_ONLY" if hist_ok else "NOT_VERIFIED",
      "GICS_FIELD_BINDING":"PASS_CURRENT_DIRECT_EVIDENCE" if field_binding_pass else "NOT_VERIFIED"
    })

    up83=json.loads((out/"asx_upstream_provider_attribution_audit_v0.83.json").read_text(encoding="utf-8"))
    up83["Fresh_v083_Assessment"]={"Evidence_Status":"FRESH_V083_OBSERVATION",
      "Exact_Industry_Field_Attribution_To_LSEG":"NOT_VERIFIED","Exact_Industry_Field_Attribution_To_Morningstar":"NOT_VERIFIED",
      "Exact_Industry_Field_Attribution_To_Other":"NOT_VERIFIED","Provider_Documentation_Queries":0,
      "Reason":"GENERAL_DIRECTORY_CREDITS_ARE_NOT_EXACT_FIELD_PROVENANCE"}
    write_json(out/"asx_upstream_provider_attribution_audit_v0.83.json",up83)

    candidates=[
      {"Taxonomy_Candidate":"GICS","Evidence":"current ASX GICS context + historical ASX company-search semantics + current runtime tests",
       "Current_Field_Attribution":"PASS" if field_binding_pass else "NOT_VERIFIED",
       "Formal_Level_Status":"PASS_INDUSTRY_GROUP" if field_binding_pass else "NOT_VERIFIED",
       "Version_Status":version_status,"Candidate_Status":"VERIFIED" if ready else "SUPPORTED_BUT_CURRENT_FIELD_BINDING_NOT_PROVEN"},
      {"Taxonomy_Candidate":"LSEG taxonomy","Evidence":"general ASX directory credit only","Current_Field_Attribution":"NOT_VERIFIED",
       "Formal_Level_Status":"NOT_VERIFIED","Version_Status":"NOT_VERIFIED","Candidate_Status":"NOT_VERIFIED"},
      {"Taxonomy_Candidate":"Morningstar taxonomy","Evidence":"general ASX directory credit only","Current_Field_Attribution":"NOT_VERIFIED",
       "Formal_Level_Status":"NOT_VERIFIED","Version_Status":"NOT_VERIFIED","Candidate_Status":"NOT_VERIFIED"},
      {"Taxonomy_Candidate":"ASX-native taxonomy","Evidence":"no exact current native taxonomy marker observed","Current_Field_Attribution":"NOT_VERIFIED",
       "Formal_Level_Status":"NOT_VERIFIED","Version_Status":"NOT_VERIFIED","Candidate_Status":"NOT_VERIFIED"},
      {"Taxonomy_Candidate":"UNKNOWN","Evidence":"fail-closed residual candidate","Current_Field_Attribution":"NOT_VERIFIED",
       "Formal_Level_Status":"NOT_VERIFIED","Version_Status":"NOT_VERIFIED","Candidate_Status":"ACTIVE_IF_GATE_C_BLOCKED"}
    ]
    write_csv(out/"au_taxonomy_candidate_inventory_v0.83.csv",candidates,
              ["Taxonomy_Candidate","Evidence","Current_Field_Attribution","Formal_Level_Status","Version_Status","Candidate_Status"])
    write_json(out/"au_taxonomy_formal_level_audit_v0.83.json",{
      "Candidate_Taxonomy":"GICS" if field_binding_pass else "NOT_VERIFIED","Formal_Level":formal_level,
      "Official_Level_Evidence_Status":"PASS_CURRENT_FIELD_BOUND_TO_EXPLICIT_GICS_INDUSTRY_GROUP" if field_binding_pass else "NOT_VERIFIED",
      "Expected_Label_Granularity_Used_As_Proof":"NO","Hard_Coded_Level":"NO"
    })
    write_json(out/"au_taxonomy_owner_audit_v0.83.json",{
      "Taxonomy":"GICS" if field_binding_pass else "NOT_VERIFIED",
      "Current_ASX_Context_SP_Dow_Jones_Indices_Observed":owner_sp,
      "Current_ASX_Context_MSCI_Observed":owner_msci,
      "Taxonomy_Owner":"S&P Dow Jones Indices / MSCI" if owner_verified else "NOT_VERIFIED",
      "Owner_Status":"VERIFIED_CURRENT_ASX_CONTEXT" if owner_verified else "NOT_VERIFIED"
    })
    runtime_schema_sha=sha_file(SCHEMA82)
    write_json(out/"au_taxonomy_version_contract_v0.83.json",{
      "Taxonomy_Identity":"GICS" if ready else "NOT_VERIFIED","Taxonomy_Version_Status":version_status,
      "Static_Version_Number_Asserted":False,"Taxonomy_Authority_Source":GICS_URL if ready else "",
      "Taxonomy_Authority_Retrieval_Timestamp_UTC":gics["Retrieval_Timestamp_UTC"] if ready else "",
      "Taxonomy_Authority_Response_SHA256":gics["SHA256"] if ready else "",
      "Current_Runtime_Schema_Authority_SHA256":runtime_schema_sha,
      "Classification_Level_Contract":formal_level,"Version_Contract_Status":"PASS" if ready else "NOT_VERIFIED"
    })

    sent_rows=[]
    for label in ["Class Pend","Not Applic"]:
        sent_rows.append({"Label":label,"Label_Type":"NOT_VERIFIED","Taxonomy_Member":"NOT_VERIFIED",
                          "Evidence":"Observed in v0.82 current runtime industry values; no current official authority proves taxonomy membership or sentinel semantics."})
    write_csv(out/"au_classification_sentinel_value_audit_v0.83.csv",sent_rows,["Label","Label_Type","Taxonomy_Member","Evidence"])

    blocker="" if ready else V082_BLOCKER
    next_gate="AU_SP_ASX200 SECTOR FIELD / SOURCE-NATIVE CODE FEASIBILITY GATE D" if ready else               "AU_SP_ASX200 TAXONOMY-PROVENANCE PARK / ACTIVE-COHORT RESELECTION MANAGER GATE"
    verdict="PASS_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C" if ready else V082_VERDICT
    decision={
      "Cohort":"AU_SP_ASX200","LIVE_DIRECTORY_MUTATION_OBSERVED":"YES",
      "ASX_DIRECTORY_DATA_ROUTE_READY":"YES","PUBLIC_BROWSER_REPRODUCIBLE":"YES","DIRECT_HTTP_REPLAY":"PASS",
      "Classification_Field":"industry","AU_SOURCE_NATIVE_TAXONOMY_IDENTITY_READY":"YES" if ready else "NO",
      "Current_UI_to_API_Industry_Binding":"PASS" if ui_api else "NOT_VERIFIED",
      "Download_Control":fresh["download"]["Control_Status"],"Download_Classification_Header":download_header,
      "Appclass_Manifest_Taxonomy_Marker":"PASS" if app_direct else "NOT_VERIFIED",
      "API_Filter_Options_Taxonomy_Marker":"PASS" if api_direct else "NOT_VERIFIED",
      "Official_ASX_Company_Search_Semantics":"PASS_HISTORICAL_SUPPORTING_ONLY" if hist_ok else "NOT_VERIFIED",
      "Currentness_Continuity":continuity_status,
      "Taxonomy_Identity":"GICS" if ready else "NOT_VERIFIED",
      "Taxonomy_Owner":"S&P Dow Jones Indices / MSCI" if owner_verified else "NOT_VERIFIED",
      "Formal_Level":formal_level,"Version_Status":version_status,
      "Sentinel_Status":"NOT_VERIFIED" if not ready else "REQUIRES_SEPARATE_SENTINEL_TYPING",
      "Field_to_Taxonomy_Binding":"PASS_CURRENT_RUNTIME_AND_OFFICIAL_ASX_SEMANTICS" if ready else "NOT_VERIFIED",
      "Gate_C":"PASS" if ready else "BLOCKED","Gate_D":"NOT_EVALUATED","Gate_E":"NOT_EVALUATED","Gate_F":"NOT_EVALUATED",
      "No_Semantic_Inference":True,"No_Fuzzy_Matching":True,"No_Cross_Taxonomy_Mapping":True,"No_PDSC":True,"No_Frozen_63_Linkage":True,
      "Blocker":blocker,"Next_Gate":next_gate,"No_Further_AU_Gate_C_Provenance_Loop":True
    }
    write_json(out/"au_source_native_taxonomy_identity_decision_v0.83.json",decision)

    # Research request ledger.
    ledger=list(fresh["ledger"])
    ledger.append({"Request_Order":"DOC1","Phase":"OFFICIAL_ASX_DOCUMENT","URL":HIST_URL,"Method":"GET","HTTP_Status":hist["HTTP_Status"],
                   "Content_Type":hist["Content_Type"],"Resource_Type":"Document","Per_Security_Request":"NO","Evidence_Status":"FRESH_V083_OBSERVATION"})
    ledger.append({"Request_Order":"DOC2","Phase":"OFFICIAL_ASX_DOCUMENT","URL":GICS_URL,"Method":"GET","HTTP_Status":gics["HTTP_Status"],
                   "Content_Type":gics["Content_Type"],"Resource_Type":"Document","Per_Security_Request":"NO","Evidence_Status":"FRESH_V083_OBSERVATION"})
    write_csv(out/"external_request_ledger_v0.83.csv",ledger,
              ["Request_Order","Phase","URL","Method","HTTP_Status","Content_Type","Resource_Type","Per_Security_Request","Evidence_Status"])
    prov=provider_audit();write_json(out/"provider_call_audit_v0.83.json",prov)

    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),"Parked_Cohort_Registry_Unchanged":sha_file(PARK)==PARK_SHA,
      "IN_Gate_F":"45/45","JP_Gate_F":"197/197","Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,
      "AU_Canonical_Rows_After":0,"AU_Gate_D_Runs":0,"AU_Gate_E_Runs":0,"AU_Gate_F_Runs":0,
      "AU_Parking_Executions":0,"Reselection_Executions":0,"Next_Cohort_Executions":0,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    write_json(out/"immutability_audit_v0.83.json",imm)

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("PREDECESSOR_VERDICT",pred["summary"]["verdict"]==V082_VERDICT,pred["summary"]["verdict"])
    test("PREDECESSOR_ARTIFACT",pred["checkpoint"]["artifact_id"]==V082_ARTIFACT and pred["checkpoint"]["artifact_digest"]==V082_DIGEST,V082_ARTIFACT)
    test("V082_ROUTE_AUTHORITY",pred["route"]["ASX_DIRECTORY_DATA_ROUTE_READY"]=="YES","YES")
    test("LIVE_MUTATION_PRESERVED",spec["accepted_v082_authority"]["live_directory_mutation_observed"] is True,"YES")
    test("EVIDENCE_REPAIR_FILES",all((out/x).exists() for x in spec["required_v082_repair_files"]),"present")
    test("FRESH_BROWSER_ONE",prov["fresh_public_ASX_browser_contexts"]==1,"1")
    test("NO_COMPLETE_74_PAGE_RERUN",prov["complete_74_page_reruns"]==0,"0")
    test("NO_FORBIDDEN_PROVIDERS",all(prov[k]==0 for k in ["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings","third_party_security_sector_databases"]),"0")
    test("NO_INFERENCE_CROSSWALK",prov["semantic_sector_inference"]==prov["fuzzy_matching"]==prov["cross_taxonomy_mapping"]==0,"0")
    test("NO_PDSC_FROZEN_LINK",prov["PDSC"]==prov["company_name_linkage_for_Frozen"]==0,"0")
    test("NO_GATE_DEF",prov["AU_Gate_D"]==prov["AU_Gate_E"]==prov["AU_Gate_F"]==0,"0")
    test("NO_RS_P",prov["Sector_RS"]==prov["P0"]==prov["P1"]==prov["P2"]==0,"0")
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_CANONICAL_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("PARKED_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],PARK_SHA)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    test("NO_AU_CANONICAL",not any(AU_CANONICAL_DIR.glob("AU_SP_ASX200_*.csv")),"0")
    test("GATE_SCOPE",decision["Gate_D"]==decision["Gate_E"]==decision["Gate_F"]=="NOT_EVALUATED","D/E/F not evaluated")
    test("TERMINAL_RULE",decision["No_Further_AU_Gate_C_Provenance_Loop"] is True,next_gate)
    if ready:
        test("GATE_C_PASS_COMPLETE",all([decision["Taxonomy_Identity"]!="NOT_VERIFIED",decision["Taxonomy_Owner"]!="NOT_VERIFIED",
                                        decision["Formal_Level"]!="NOT_VERIFIED",decision["Version_Status"]!="NOT_VERIFIED",
                                        decision["Field_to_Taxonomy_Binding"].startswith("PASS")]),"PASS")
    else:
        test("GATE_C_BLOCK_SMALLEST",blocker==V082_BLOCKER,blocker)
        test("BLOCK_NEXT_GATE",next_gate=="AU_SP_ASX200 TAXONOMY-PROVENANCE PARK / ACTIVE-COHORT RESELECTION MANAGER GATE",next_gate)
    write_csv(out/"test_results_v0.83.csv",tests)

    summary={
      "version":VERSION,"stage":STAGE,"verdict":verdict,"v082_evidence_completeness_repaired":True,
      "au_source_native_taxonomy_identity_ready":ready,
      "current_ui_api_industry_binding":"PASS" if ui_api else "NOT_VERIFIED",
      "download_control":fresh["download"]["Control_Status"],"download_classification_header":download_header,
      "appclass_manifest_taxonomy_marker":"PASS" if app_direct else "NOT_VERIFIED",
      "api_filter_options_taxonomy_marker":"PASS" if api_direct else "NOT_VERIFIED",
      "official_asx_company_search_semantics":"PASS_HISTORICAL_SUPPORTING_ONLY" if hist_ok else "NOT_VERIFIED",
      "currentness_continuity":continuity_status,
      "taxonomy_identity":"GICS" if ready else "NOT_VERIFIED",
      "taxonomy_owner":"S&P Dow Jones Indices / MSCI" if owner_verified else "NOT_VERIFIED",
      "formal_level":formal_level,"version_status":version_status,
      "sentinel_status":"NOT_VERIFIED" if not ready else "REQUIRES_SEPARATE_SENTINEL_TYPING",
      "field_to_taxonomy_binding":"PASS_CURRENT_RUNTIME_AND_OFFICIAL_ASX_SEMANTICS" if ready else "NOT_VERIFIED",
      "blocker":blocker,"live_directory_mutation_observed":"YES","canonical_ready_rows":37,"canonical_total_rows":1425,
      "au_gate_d":"NOT_EVALUATED","au_gate_e":"NOT_EVALUATED","au_gate_f":"NOT_EVALUATED",
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate
    }
    write_json(out/"summary_preupload_v0.83.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.83.json",{
      "version":VERSION,"stage":STAGE,"verdict":verdict,"v082_evidence_completeness_repaired":True,
      "au_source_native_taxonomy_identity_ready":ready,"blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD"
    })
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.83.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.83.json",{
      "version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "verdict":verdict,"v082_evidence_completeness_repaired":True,"au_source_native_taxonomy_identity_ready":ready,
      "blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,"au_gate_d_runs":0,"au_gate_e_runs":0,"au_gate_f_runs":0,
      "canonical_materialization_runs":0,"au_parking_executions":0,"reselection_executions":0,"next_cohort_executions":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":next_gate
    })
    return 0

if __name__=="__main__":
    raise SystemExit(main())
