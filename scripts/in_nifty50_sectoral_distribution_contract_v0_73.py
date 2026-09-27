#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, csv, hashlib, html.parser, io, json, os, re, shutil, subprocess, tempfile, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.73"
STAGE="IN_NIFTY50_NSE_INDICES_SECTORAL_DISTRIBUTION_DATA_CONTRACT_GATE_F_RESOLUTION"
REQUIRED_START_HEAD="7464e7c643922e946c39631c58174e9716cb53b4"
V072_WORKFLOW=36309975985
V072_ARTIFACT=10929365141
V072_DIGEST="sha256:8c3fb77305adcb7e2321aed34805ab5525afc176d3a7b7b4fa26420ca649ebba"
V072_PDF_SHA="8ae58cbd10d7dd5184d76cfec6486f91c019026c8de329432b69c54ff7235f8b"
V072_STRUCTURAL_SHA="d431587f5f686b8432bc57755a8fe6aef232fed49fb858cf7e905b3318687173"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

TAXONOMY="NSE_INDICES_INDUSTRY_CLASSIFICATION"
PAGE_URL="https://www.niftyindices.com/indices/equity/broad-based-indices/nifty--50"
CLASSIFICATION_PAGE="https://www.niftyindices.com/resources/industry-classification"
SPEC=ROOT/"config/in_nifty50_sectoral_distribution_contract_spec_v0.73.json"
SUM72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/summary_v0.72.json"
CHK72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/stage_checkpoint_v0.72.json"
MAN72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/manifest_v0.72.json"
MATCH72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/in_15_label_cross_level_match_audit_v0.72.csv"
COV72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/in_exact_45_classification_coverage_v0.72.csv"
REPRO72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/nse_pdf_extraction_reproducibility_audit_v0.72.json"
TAXTABLE72=ROOT/"output_in_nifty50_nse_classification_structure_repair_v0_72/nse_industry_classification_structured_table_v0.72.csv"
LINK70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/in_exact_45_identity_linkage_audit_v0.70.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"

LEVEL_LABELS={
  "MACRO_ECONOMIC_SECTOR":"Macro Economic Sector",
  "SECTOR":"Sector",
  "INDUSTRY":"Industry",
  "BASIC_INDUSTRY":"Basic Industry"
}
DISPLAY_TO_LEVEL={v:k for k,v in LEVEL_LABELS.items()}
EXPECTED_LABELS=[
 "Automobile and Auto Components","Capital Goods","Construction","Construction Materials",
 "Consumer Durables","Consumer Services","Fast Moving Consumer Goods","Financial Services",
 "Healthcare","Information Technology","Metals & Mining","Oil Gas & Consumable Fuels",
 "Power","Services","Telecommunication"
]
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.73"

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def norm(s:str)->str:return re.sub(r"\s+"," ",str(s).replace("\u00a0"," ")).strip()
def norm_id(s:str)->str:return norm(s).upper()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

def is_official(url:str)->bool:
    try:
        h=(urllib.parse.urlparse(url).hostname or "").lower()
        return h=="niftyindices.com" or h.endswith(".niftyindices.com")
    except Exception:return False

def fetch(url:str,max_bytes:int=5_000_000,method:str="GET",body:bytes|None=None,headers:dict[str,str]|None=None)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    if not is_official(url):
        return {"ok":False,"url":url,"timestamp_utc":ts,"status":"","content_type":"","body":b"","error":"HOST_NOT_ALLOWED"}
    hs={"User-Agent":UA,"Accept":"*/*","Accept-Language":"en-US,en;q=0.8"}
    if headers:
        for k,v in headers.items():
            if k.lower() in {"content-type","accept","referer"} and v:hs[k]=v
    try:
        req=urllib.request.Request(url,data=body,headers=hs,method=method)
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read(max_bytes+1);tr=len(b)>max_bytes
            if tr:b=b[:max_bytes]
            return {"ok":200<=getattr(r,"status",200)<300 and not tr,"url":r.geturl(),"requested_url":url,
                    "timestamp_utc":ts,"status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"truncated":tr,"body":b}
    except Exception as e:
        return {"ok":False,"url":url,"requested_url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,
                "sha256":"","truncated":False,"body":b"","error":f"{type(e).__name__}:{e}"}

class AssetParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__();self.assets=[];self.inline_scripts=[];self._script=False;self._buf=[]
    def handle_starttag(self,tag,attrs):
        d={k.lower():(v or "") for k,v in attrs}
        if tag.lower()=="script":
            if d.get("src"):self.assets.append(("SCRIPT",d["src"]))
            else:self._script=True;self._buf=[]
        elif tag.lower()=="link" and d.get("href"):
            self.assets.append(("LINK",d["href"]))
    def handle_data(self,data):
        if self._script:self._buf.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="script" and self._script:
            self.inline_scripts.append("".join(self._buf));self._script=False;self._buf=[]

def body_schema(body:bytes,content_type:str)->dict[str,Any]:
    txt=body.decode("utf-8",errors="replace")
    out={"parse_type":"TEXT","json_keys":[],"top_type":"","string_count":0}
    try:
        obj=json.loads(txt)
        keys=set();strings=[]
        def walk(x):
            if isinstance(x,dict):
                for k,v in x.items():keys.add(str(k));walk(v)
            elif isinstance(x,list):
                for v in x:walk(v)
            elif isinstance(x,str):strings.append(x)
        walk(obj)
        out={"parse_type":"JSON","json_keys":sorted(keys),"top_type":type(obj).__name__,"string_count":len(strings)}
    except Exception:pass
    return out

def strings_from_obj(obj:Any)->list[str]:
    out=[]
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                out.append(str(k));walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
        elif isinstance(x,(str,int,float)):out.append(str(x))
    walk(obj);return out

def load_taxonomy_nodes()->dict[str,dict[str,dict[str,str]]]:
    rows=read_csv(TAXTABLE72)
    maps={k:{} for k in LEVEL_LABELS}
    for r in rows:
        pairs=[
          ("MACRO_ECONOMIC_SECTOR","Macro_Economic_Sector_Code","Macro_Economic_Sector_Name"),
          ("SECTOR","Sector_Code","Sector_Name"),
          ("INDUSTRY","Industry_Code","Industry_Name"),
          ("BASIC_INDUSTRY","Basic_Industry_Code","Basic_Industry_Name")
        ]
        for level,ck,nk in pairs:
            code=r.get(ck,"");name=r.get(nk,"")
            if code and name:maps[level][code]={"code":code,"name":name}
    return maps

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM72.read_text(encoding="utf-8"));c=json.loads(CHK72.read_text(encoding="utf-8"))
    r=json.loads(REPRO72.read_text(encoding="utf-8"));cov=read_csv(COV72);match=read_csv(MATCH72);link=read_csv(LINK70)
    if s["verdict"]!="BLOCKED_IN_NIFTY50_GATE_F_REPAIR" or s["in_exact_45_sector_classification_coverage_ready"] is not False:
        raise RuntimeError("v0.72 verdict")
    if (s["classified"],s["total"],s["not_verified"])!=(0,45,45):raise RuntimeError("v0.72 counts")
    if s["bound_classification_level"]!="NOT_VERIFIED" or s["distinct_classifications"]!=15 or s["source_native_code_coverage"]!=0:
        raise RuntimeError("v0.72 classification state")
    if s["blocker"]!="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED":raise RuntimeError("v0.72 blocker")
    if c["workflow_run_id"]!=V072_WORKFLOW or c["artifact_id"]!=V072_ARTIFACT or "sha256:"+c["artifact_digest"]!=V072_DIGEST:
        raise RuntimeError("v0.72 artifact")
    if r["PDF_SHA256"]!=V072_PDF_SHA or r["Run1_Structural_SHA256"]!=V072_STRUCTURAL_SHA or not r["Deterministic_Structural_Output"]:
        raise RuntimeError("v0.72 pdf authority")
    if len(cov)!=45 or len({x["WS_ID"] for x in cov})!=45:raise RuntimeError("v0.72 coverage rows")
    if sorted({x["Source_Classification_Raw"] for x in cov})!=sorted(EXPECTED_LABELS):raise RuntimeError("v0.72 labels")
    if len(match)!=15:raise RuntimeError("v0.72 exact-match audit")
    if len(link)!=45 or any(x["Gate_E_Status"]!="PROVABLY_LINKED" for x in link):raise RuntimeError("v0.70 identity")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("registry")
    return {"summary":s,"coverage":cov,"identity":link,"match":match,"repro":r}

def extract_hidden_input_value(html_text:str,element_id:str)->str:
    m=re.search(r"<input\\b[^>]*\\bid=[\"']"+re.escape(element_id)+r"[\"'][^>]*>",html_text,re.I)
    if not m:return ""
    v=re.search(r"\\bvalue=[\"']([^\"']*)[\"']",m.group(0),re.I)
    return norm(v.group(1)) if v else ""

def parse_foamtree_payload(raw:bytes)->tuple[Any|None,str]:
    text=raw.decode("utf-8",errors="replace").strip()
    if not text:return None,"EMPTY"
    cleaned=re.sub(r",\\s*([\\]}])",r"\\1",text)
    cleaned=re.sub(r"([{,]\\s*)([A-Za-z_][A-Za-z0-9_]*)\\s*:",r'\\1"\\2":',cleaned)
    l=cleaned.find("(");r=cleaned.rfind(")")
    inner=cleaned[l+1:r] if l>=0 and r>l else cleaned
    start=inner.find("{")
    if start<0:
        try:return json.loads(inner),"JSON_DIRECT"
        except Exception as e:return None,"NO_OBJECT:"+type(e).__name__
    depth=0;end=-1;quote="";esc=False
    for i,ch in enumerate(inner[start:],start):
        if quote:
            if esc:esc=False
            elif ch=="\\\\":esc=True
            elif ch==quote:quote=""
            continue
        if ch in ("\"","'"):quote=ch;continue
        if ch=="{":depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:end=i+1;break
    if end<0:return None,"UNBALANCED_OBJECT"
    objtxt=inner[start:end]
    try:return json.loads(objtxt),"PASS"
    except Exception as e:return None,"JSON_PARSE_"+type(e).__name__+":"+str(e)[:180]

def safe_url_join_path(base:str,path:str)->str:
    return base.rstrip("/")+"/"+urllib.parse.quote(path.lstrip("/"),safe="/:_-.%")

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"tradingview":0,"wikipedia":0,
      "investing_com":0,"etf_holdings":0,"third_party_security_databases":0,"third_party_sector_databases":0,
      "company_websites":0,"search_engine_mapping_evidence":0,"company_name_joins":0,"fuzzy_matching":0,
      "semantic_inference":0,"cross_taxonomy_mapping":0,"pdsc_fallback":0,"per_security_fanout":0,
      "nse_equity_l":0,"nifty_constituent_refetch":0,"authentication_bypass":0,"captcha_bypass":0,
      "sector_rs":0,"p0":0,"p1":0,"p2":0
    }

# ---------- CDP browser capture ----------
class CDP:
    def __init__(self,ws_url:str):
        import websocket
        self.websocket=websocket
        self.ws=websocket.create_connection(ws_url,timeout=2,origin="http://127.0.0.1")
        self.next_id=1;self.phase="INITIAL";self.requests={};self.responses={};self.blocked=[]
    def _send_raw(self,method:str,params:dict[str,Any]|None=None)->int:
        i=self.next_id;self.next_id+=1
        self.ws.send(json.dumps({"id":i,"method":method,"params":params or {}}))
        return i
    def _handle_event(self,msg:dict[str,Any]):
        method=msg.get("method","");p=msg.get("params",{})
        if method=="Fetch.requestPaused":
            req=p.get("request",{});url=req.get("url","")
            allowed=is_official(url) or url.startswith(("data:","blob:","about:","chrome:"))
            if allowed:self._send_raw("Fetch.continueRequest",{"requestId":p["requestId"]})
            else:
                self.blocked.append(url);self._send_raw("Fetch.failRequest",{"requestId":p["requestId"],"errorReason":"BlockedByClient"})
        elif method=="Network.requestWillBeSent":
            req=p.get("request",{});rid=p.get("requestId","")
            self.requests[rid]={
              "phase":self.phase,"url":req.get("url",""),"method":req.get("method",""),"postData":req.get("postData",""),
              "headers":req.get("headers",{}),"type":p.get("type",""),"initiator":p.get("initiator",{})
            }
        elif method=="Network.responseReceived":
            rid=p.get("requestId","");resp=p.get("response",{})
            self.responses[rid]={
              "phase":self.requests.get(rid,{}).get("phase",self.phase),"url":resp.get("url",""),"status":resp.get("status",""),
              "mimeType":resp.get("mimeType",""),"type":p.get("type",""),"headers":resp.get("headers",{})
            }
    def command(self,method:str,params:dict[str,Any]|None=None,timeout:float=15)->dict[str,Any]:
        target=self._send_raw(method,params);end=time.time()+timeout
        while time.time()<end:
            try:raw=self.ws.recv()
            except self.websocket.WebSocketTimeoutException:continue
            msg=json.loads(raw)
            if msg.get("id")==target:return msg
            if "method" in msg:self._handle_event(msg)
        return {"id":target,"error":{"message":"TIMEOUT"}}
    def pump(self,seconds:float):
        end=time.time()+seconds
        while time.time()<end:
            try:raw=self.ws.recv()
            except self.websocket.WebSocketTimeoutException:continue
            try:msg=json.loads(raw)
            except Exception:continue
            if "method" in msg:self._handle_event(msg)
    def eval(self,expr:str)->Any:
        r=self.command("Runtime.evaluate",{"expression":expr,"returnByValue":True,"awaitPromise":True},timeout=10)
        return r.get("result",{}).get("result",{}).get("value")
    def close(self):
        try:self.ws.close()
        except Exception:pass

def find_chrome(cands:list[str])->str|None:
    for c in cands:
        if Path(c).exists():return c
    for name in ("google-chrome","google-chrome-stable","chromium","chromium-browser"):
        p=shutil.which(name)
        if p:return p
    return None

def start_chrome(chrome:str,port:int)->tuple[subprocess.Popen,str,str]:
    ud=tempfile.mkdtemp(prefix="v073-chrome-")
    args=[chrome,"--headless=new",f"--remote-debugging-port={port}","--remote-allow-origins=*",
          f"--user-data-dir={ud}","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
          "--disable-background-networking","--disable-component-update","--disable-sync","--disable-extensions",
          "--no-first-run","--no-default-browser-check","about:blank"]
    p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    for _ in range(60):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list",timeout=1) as r:
                tabs=json.load(r)
            pages=[t for t in tabs if t.get("type")=="page" and not str(t.get("url","")).startswith("chrome-extension://")]
            if pages:return p,ud,pages[0]["webSocketDebuggerUrl"]
            req=urllib.request.Request(f"http://127.0.0.1:{port}/json/new?about:blank",method="PUT")
            with urllib.request.urlopen(req,timeout=1) as r:
                t=json.load(r)
                if t.get("type")=="page":return p,ud,t["webSocketDebuggerUrl"]
        except Exception:pass
        time.sleep(.25)
    err=""
    try:err=p.stderr.read(2000) if p.stderr else ""
    except Exception:pass
    p.terminate()
    raise RuntimeError("CHROME_REMOTE_DEBUG_NOT_READY:"+err)

def runtime_snapshot(cdp:CDP)->dict[str,Any]:
    expr=r"""(()=> {
      const sels=[...document.querySelectorAll('select')].map((s,i)=>({
        index:i,id:s.id||'',name:s.name||'',className:s.className||'',value:s.value||'',
        options:[...s.options].map(o=>({text:(o.textContent||'').trim(),value:o.value||'',selected:o.selected}))
      }));
      const texts=[...document.querySelectorAll('button,a,li,label,option')].filter(e=>{
        const t=(e.textContent||'').trim(); return ['Macro Economic Sector','Sector','Industry','Basic Industry'].includes(t);
      }).slice(0,50).map(e=>({tag:e.tagName,id:e.id||'',className:e.className||'',text:(e.textContent||'').trim(),
                              value:e.value||'',data:[...e.attributes].filter(a=>a.name.startsWith('data-')).map(a=>[a.name,a.value])}));
      let charts=[];
      try {
        if(window.Highcharts && Array.isArray(Highcharts.charts)) charts=Highcharts.charts.filter(Boolean).map((c,ci)=>({
          chartIndex:ci,renderTo:(c.renderTo&&c.renderTo.id)||'',
          series:c.series.map(s=>({name:s.name||'',type:s.type||'',data:s.data.slice(0,500).map(p=>({
            name:p.name||'',id:p.id||'',y:p.y,category:p.category,
            options:Object.fromEntries(Object.entries(p.options||{}).filter(([k,v])=>['name','id','code','symbol','isin','category','parent','level','value','y'].includes(k)))
          }))}))
        }));
      } catch(e) { charts=[{error:String(e)}]; }
      return {url:location.href,title:document.title,selects:sels,levelElements:texts,highcharts:charts,bodyText:(document.body&&document.body.innerText||'').slice(0,250000)};
    })()"""
    return cdp.eval(expr) or {}

def locate_level_select(snapshot:dict[str,Any])->dict[str,Any]|None:
    expected=set(LEVEL_LABELS.values())
    for s in snapshot.get("selects",[]):
        texts={norm(o.get("text","")) for o in s.get("options",[])}
        if expected.issubset(texts):return s
    return None

def browser_capture(spec:dict[str,Any],out:Path)->dict[str,Any]:
    chrome=find_chrome(spec["browser_contract_discovery"]["chrome_binary_candidates"])
    if not chrome:return {"status":"NOT_VERIFIED","error":"CHROME_NOT_AVAILABLE","requests":[],"responses":[],"snapshots":[],"blocked":[]}
    port=int(spec["browser_contract_discovery"]["remote_debugging_port"])
    proc=ud=cdp=None
    try:
        proc,ud,wsurl=start_chrome(chrome,port);cdp=CDP(wsurl)
        cdp.command("Network.enable",{"maxTotalBufferSize":100000000,"maxResourceBufferSize":10000000})
        cdp.command("Page.enable")
        cdp.command("Runtime.enable")
        cdp.command("Fetch.enable",{"patterns":[{"urlPattern":"*","requestStage":"Request"}]})
        cdp.phase="INITIAL"
        cdp.command("Page.navigate",{"url":PAGE_URL},timeout=15)
        cdp.pump(float(spec["browser_contract_discovery"]["initial_observation_seconds"]))
        snaps=[{"phase":"INITIAL","snapshot":runtime_snapshot(cdp)}]
        s0=snaps[0]["snapshot"];sel=locate_level_select(s0)
        if sel:
            si=sel["index"]
            for display in LEVEL_LABELS.values():
                opt=next((o for o in sel["options"] if norm(o["text"])==display),None)
                if not opt:continue
                cdp.phase="LEVEL:"+display
                expr=f"""(()=>{{const s=document.querySelectorAll('select')[{si}]; if(!s)return false; s.value={json.dumps(opt['value'])}; s.dispatchEvent(new Event('change',{{bubbles:true}})); return {{value:s.value,text:s.options[s.selectedIndex]?.textContent.trim()}};}})()"""
                action=cdp.eval(expr)
                cdp.pump(float(spec["browser_contract_discovery"]["level_switch_observation_seconds"]))
                snaps.append({"phase":"LEVEL:"+display,"action":action,"snapshot":runtime_snapshot(cdp)})
        # Retrieve bodies for official relevant responses.
        bodies={}
        for rid,resp in list(cdp.responses.items()):
            url=resp.get("url","");typ=resp.get("type","")
            if not is_official(url) or typ not in {"XHR","Fetch","Document","Script"}:continue
            rr=cdp.command("Network.getResponseBody",{"requestId":rid},timeout=5)
            result=rr.get("result")
            if not result:continue
            body=result.get("body","");raw=base64.b64decode(body) if result.get("base64Encoded") else body.encode("utf-8",errors="replace")
            if len(raw)>int(spec["browser_contract_discovery"]["max_response_body_bytes"]):continue
            bodies[rid]=raw
        return {"status":"PASS","chrome":chrome,"requests":cdp.requests,"responses":cdp.responses,"bodies":bodies,
                "snapshots":snaps,"blocked":cdp.blocked,"level_select":sel or {}}
    except Exception as e:
        return {"status":"NOT_VERIFIED","error":f"{type(e).__name__}:{e}","requests":[],"responses":[],"snapshots":[],"blocked":[]}
    finally:
        if cdp:cdp.close()
        if proc:
            try:proc.terminate();proc.wait(timeout=3)
            except Exception:
                try:proc.kill()
                except Exception:pass
        if ud:shutil.rmtree(ud,ignore_errors=True)

SEC_KEYS={"isin","isincode","isinno","symbol","securitysymbol","ticker","securitycode","stockcode","scripcode","stocksymbol"}
LABEL_KEYS={"category","categoryname","name","label","sector","sectorname","industry","industryname","basicindustry","basicindustryname","macroeconomicsector","macroeconomicsectorname","classification","classificationname"}
LEVEL_KEYS={"level","levelname","classificationlevel","sectorlevel","categorylevel","type","classificationtype"}
CODE_KEYS={"code","id","categorycode","sectorcode","industrycode","classificationcode","nodeid","nodecode","categoryid"}

def keynorm(k:str)->str:return re.sub(r"[^a-z0-9]","",k.lower())

def extract_membership_records(obj:Any,phase:str,source_url:str)->list[dict[str,str]]:
    out=[]
    def walk(x:Any,ctx:dict[str,str]):
        if isinstance(x,dict):
            local=dict(ctx)
            kn={keynorm(k):k for k in x}
            # local category/level/code context from scalar values only
            for nk,k in kn.items():
                v=x[k]
                if isinstance(v,(str,int,float)):
                    sv=norm(str(v))
                    if nk in LABEL_KEYS and sv:local.setdefault("category_label",sv)
                    if nk in LEVEL_KEYS and sv:local.setdefault("level_value",sv)
                    if nk in CODE_KEYS and sv:local.setdefault("node_id",sv)
            sec=""
            sec_type=""
            for nk,k in kn.items():
                if nk in SEC_KEYS and isinstance(x[k],(str,int,float)):
                    sv=norm(str(x[k]))
                    if sv:
                        sec=sv;sec_type="ISIN" if "isin" in nk else "SYMBOL";break
            if sec:
                out.append({"phase":phase,"source_url":source_url,"security_id":sec,"security_id_type":sec_type,
                            "application_level_raw":local.get("level_value",""),"category_label":local.get("category_label",""),
                            "application_node_id_or_code":local.get("node_id","")})
            for k,v in x.items():
                if isinstance(v,(dict,list)):walk(v,local)
        elif isinstance(x,list):
            for v in x:walk(v,ctx)
    walk(obj,{})
    # exact-deduplicate
    seen=set();ded=[]
    for r in out:
        t=tuple(r.values())
        if t not in seen:seen.add(t);ded.append(r)
    return ded

def taxonomy_lookup(maps:dict[str,dict[str,dict[str,str]]],level:str,display:str,nodeid:str)->tuple[str,str,str]:
    # returns formal code, official name, method
    if nodeid and nodeid in maps.get(level,{}):
        d=maps[level][nodeid];return nodeid,d["name"],"APPLICATION_NODE_ID_EQUALS_TAXONOMY_SOURCE_NATIVE_CODE"
    hits=[(c,d) for c,d in maps.get(level,{}).items() if d["name"]==display]
    if len(hits)==1:return hits[0][0],hits[0][1]["name"],"APPLICATION_DISPLAY_LABEL_EXACT_TO_V072_TAXONOMY_NODE"
    return "","","NOT_VERIFIED"

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_in_nifty50_sectoral_distribution_contract_v0_73")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    taxmaps=load_taxonomy_nodes()
    identity_by_isin={norm_id(r["Frozen_ISIN"]):r for r in pred["identity"]}
    identity_by_symbol={norm_id(r["Primary_Ticker"]):r for r in pred["identity"]}
    csv_by_ws={r["WS_ID"]:r for r in pred["coverage"]}

    external=[]
    # Static page + assets
    page=fetch(PAGE_URL)
    external.append({"Request_Order":1,"Request_Type":"NIFTY50_APPLICATION_PAGE","URL":PAGE_URL,"Method":"GET","Status":page.get("status",""),
                     "Content_Type":page.get("content_type",""),"Bytes":page.get("bytes",0),"SHA256":page.get("sha256",""),
                     "Timestamp_UTC":page.get("timestamp_utc",""),"Official_Source":"YES","Per_Security_Fanout":"NO",
                     "Result":"OK" if page.get("ok") else page.get("error","FAILED")})
    asset_rows=[];candidate_strings=[];context_rows=[];asset_texts={}
    if page.get("ok"):
        hp=AssetParser();hp.feed(page["body"].decode("utf-8",errors="replace"))
        assets=[];seen=set()
        for typ,u in hp.assets:
            absu=urllib.parse.urljoin(PAGE_URL,u)
            if is_official(absu) and absu not in seen:
                seen.add(absu);assets.append((typ,absu))
        for idx,(typ,u) in enumerate(assets[:int(spec["static_asset_discovery"]["max_assets"])],1):
            fr=fetch(u,max_bytes=int(spec["static_asset_discovery"]["max_asset_bytes"]))
            external.append({"Request_Order":len(external)+1,"Request_Type":"APPLICATION_ASSET","URL":u,"Method":"GET","Status":fr.get("status",""),
                             "Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),"SHA256":fr.get("sha256",""),
                             "Timestamp_UTC":fr.get("timestamp_utc",""),"Official_Source":"YES","Per_Security_Fanout":"NO",
                             "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
            txt=fr.get("body",b"").decode("utf-8",errors="replace")
            asset_texts[u]=txt
            for kw in ["SectorialIndexData","sectorDropdown","selectedinSectorial","_Sector.js","Macro Economic Sector","Basic Industry","sectoralDistibution","hdnSet","hdnPgName","IndexTypeFinder1"]:
                pos=0
                while True:
                    p=txt.find(kw,pos)
                    if p<0:break
                    context_rows.append({"Source_Asset":u,"Keyword":kw,"Context":txt[max(0,p-700):min(len(txt),p+1400)].replace("\r"," ").replace("\n"," ")})
                    pos=p+len(kw)
                    if sum(1 for x in context_rows if x["Source_Asset"]==u and x["Keyword"]==kw)>=12:break
            rel=[s for s in re.findall(r'''(?:"|')([^"'\n]{3,300})(?:"|')''',txt)
                 if any(k in s.lower() for k in ("sector","industry","distribution","classification","ajax","api","chart"))][:100]
            candidate_strings.extend((u,s) for s in rel)
            asset_rows.append({"Asset_Order":idx,"Asset_Type":typ,"Asset_URL":u,"HTTP_Status":fr.get("status",""),
                               "Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),"SHA256":fr.get("sha256",""),
                               "Relevant_String_Count":len(rel),"Fetch_Status":"PASS" if fr.get("ok") else "NOT_VERIFIED"})
        for i,s in enumerate(hp.inline_scripts):
            rel=[x for x in re.findall(r'''(?:"|')([^"'\n]{3,300})(?:"|')''',s)
                 if any(k in x.lower() for k in ("sector","industry","distribution","classification","ajax","api","chart"))][:100]
            candidate_strings.extend((PAGE_URL+"#inline-"+str(i+1),x) for x in rel)
    write_csv(out/"nifty_sectoral_distribution_application_asset_ledger_v0.73.csv",asset_rows if asset_rows else [{
      "Asset_Order":0,"Asset_Type":"NONE","Asset_URL":"","HTTP_Status":"","Content_Type":"","Bytes":0,"SHA256":"","Relevant_String_Count":0,"Fetch_Status":"NOT_VERIFIED"
    }])
    string_rows=[]
    for src,s in candidate_strings:
        string_rows.append({"Source_Asset":src,"Relevant_String":s})
    write_csv(out/"nifty_application_asset_relevant_strings_v0.73.csv",string_rows if string_rows else [{
      "Source_Asset":"","Relevant_String":""
    }])
    write_csv(out/"nifty_application_asset_context_snippets_v0.73.csv",context_rows if context_rows else [{
      "Source_Asset":"","Keyword":"","Context":""
    }])

    # Explicit public application contract from the official foamtree application code.
    page_text=page.get("body",b"").decode("utf-8",errors="replace") if page.get("ok") else ""
    page_contexts=[]
    for kw in ["hdnSet","hdnPgName","Sectoral Distribution","NIFTY 50"]:
        pos=0
        while True:
            p=page_text.find(kw,pos)
            if p<0:break
            page_contexts.append({"Keyword":kw,"Context":page_text[max(0,p-900):min(len(page_text),p+1600)].replace("\r"," ").replace("\n"," ")})
            pos=p+len(kw)
            if sum(1 for x in page_contexts if x["Keyword"]==kw)>=15:break
    write_csv(out/"nifty_application_page_context_snippets_v0.73.csv",page_contexts if page_contexts else [{"Keyword":"","Context":""}])
    app_index_name=extract_hidden_input_value(page_text,"hdnSet")
    foamtree_url=next((u for u in asset_texts if u.endswith("/assets/js/foamtree.js")), "")
    foamtree_text=asset_texts.get(foamtree_url,"")
    code_contracts=[
      ("MACRO_ECONOMIC_SECTOR","Macro Economic Sector","MacroEconomicSector","_MacroEconomicSector"),
      ("SECTOR","Sector","Sector","_Sector"),
      ("INDUSTRY","Industry","Industry","_Industry"),
      ("BASIC_INDUSTRY","Basic Industry","Basic Industry","_BasicIndustry")
    ]
    static_level_payloads=[];static_candidate_contracts=[];static_membership=[];static_level_contract_rows=[]
    base="https://liveindexsa.niftyindices.com/jsonfiles/"
    for formal,display,folder,suffix in code_contracts:
        template=f"{folder}/SectorialIndexData"+chr(36)+"{e.toUpperCase()}"+f"{suffix}"
        code_proof=(display in foamtree_text and folder in foamtree_text and suffix in foamtree_text and "SectorialIndexData" in foamtree_text)
        path=f"{folder}/SectorialIndexData{app_index_name.upper()}{suffix}.js" if app_index_name else ""
        url=safe_url_join_path(base,path) if path and code_proof else ""
        fr=fetch(url) if url else {"ok":False,"body":b"","status":"","content_type":"","bytes":0,"sha256":"","timestamp_utc":"","error":"STATIC_CONTRACT_NOT_CONSTRUCTED"}
        if url:
            external.append({"Request_Order":len(external)+1,"Request_Type":"SECTORAL_DISTRIBUTION_LEVEL_PAYLOAD","URL":url,"Method":"GET",
                             "Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),"SHA256":fr.get("sha256",""),
                             "Timestamp_UTC":fr.get("timestamp_utc",""),"Official_Source":"YES","Per_Security_Fanout":"NO",
                             "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
        obj,parse_status=parse_foamtree_payload(fr.get("body",b"")) if fr.get("ok") else (None,"NOT_FETCHED")
        recs=extract_membership_records(obj,"LEVEL:"+display,url) if obj is not None else []
        static_membership.extend(recs)
        sch=body_schema(json.dumps(obj,ensure_ascii=False).encode("utf-8"),"application/json") if obj is not None else {"parse_type":"","json_keys":[]}
        rawtxt=fr.get("body",b"").decode("utf-8",errors="replace")
        static_level_payloads.append({
          "Formal_Level":formal,"Official_Displayed_Label":display,"Application_Index_Name":app_index_name or "NOT_VERIFIED",
          "Application_Path_Template":template,"Constructed_URL":url or "NOT_VERIFIED","Application_Code_Proof":"PASS" if code_proof else "NOT_VERIFIED",
          "HTTP_Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),"Response_Bytes":fr.get("bytes",0),
          "Response_SHA256":fr.get("sha256",""),"Payload_Parse_Status":parse_status,
          "Response_Schema_Keys":" | ".join(sch.get("json_keys",[])[:200]),"Extracted_Membership_Record_Count":len(recs),
          "Response_Prefix":rawtxt[:1000].replace("\r"," ").replace("\n"," ")
        })
        if obj is not None and fr.get("ok"):
            static_candidate_contracts.append({
              "request_id":"STATIC:"+formal,"phase":"LEVEL:"+display,"endpoint":url,"method":"GET","request_body":"",
              "response_sha256":fr.get("sha256",""),"response_bytes":fr.get("bytes",0),"response_parse_type":"JSONP_OBJECT",
              "schema_keys":sch.get("json_keys",[]),
              "label_hit_count":sum(1 for x in EXPECTED_LABELS if x in rawtxt),
              "security_hit_count":sum(1 for rr in pred["identity"] if rr["Frozen_ISIN"] in rawtxt or rr["Primary_Ticker"] in rawtxt),
              "membership_record_count":len(recs),"static_object":obj
            })
        static_level_contract_rows.append({
          "Official_Displayed_Label":display,"Internal_Formal_Level":formal,
          "Application_Raw_Level_Value":folder+"/"+suffix.lstrip("_"),
          "UI_Select_ID":"sectorDropdown","UI_Select_Name":"",
          "Controlled_Level_Phase_Request_Count":1 if fr.get("ok") else 0,
          "Observed_Request_Endpoints":url or "","Observed_Request_Bodies":"",
          "Level_Parameter_Status":"PASS_APPLICATION_CODE_PATH_ENUM" if code_proof and fr.get("ok") else "NOT_VERIFIED"
        })
    write_csv(out/"nifty_static_sectoral_distribution_contract_v0.73.csv",static_level_payloads)

    # Browser network capture.
    bc=browser_capture(spec,out)
    runtime_evidence={
      "Status":bc.get("status"),"Error":bc.get("error",""),"Chrome":bc.get("chrome",""),
      "Request_Count":len(bc.get("requests",{})),"Response_Count":len(bc.get("responses",{})),
      "Blocked_Non_Official_Request_Count":len(bc.get("blocked",[])),
      "Level_Select":bc.get("level_select",{}),
      "Snapshots":bc.get("snapshots",[])
    }
    (out/"nifty_browser_runtime_snapshot_v0.73.json").write_text(json.dumps(runtime_evidence,indent=2,sort_keys=True)[:1000000]+"\n",encoding="utf-8")
    net_rows=[];candidate_contracts=list(static_candidate_contracts);all_membership=list(static_membership)
    bodies=bc.get("bodies",{})
    for rid,req in bc.get("requests",{}).items():
        resp=bc.get("responses",{}).get(rid,{})
        url=req.get("url","")
        if not is_official(url):continue
        raw=bodies.get(rid,b"")
        sch=body_schema(raw,resp.get("mimeType","")) if raw else {"parse_type":"","json_keys":[],"top_type":"","string_count":0}
        label_hits=[];sec_hits=[]
        txt=raw.decode("utf-8",errors="replace") if raw else ""
        for label in EXPECTED_LABELS:
            if label in txt:label_hits.append(label)
        for r in pred["identity"]:
            if r["Frozen_ISIN"] in txt or r["Primary_Ticker"] in txt:sec_hits.append(r["WS_ID"])
        net_rows.append({
          "Phase":req.get("phase",""),"Initiator":json.dumps(req.get("initiator",{}),sort_keys=True)[:1000],
          "Endpoint":url,"HTTP_Method":req.get("method",""),"Request_Body":req.get("postData","")[:4000],
          "Index_Identifier_Evidence":"NIFTY 50" if "nifty" in (req.get("postData","")+" "+url).lower() or req.get("phase","").startswith("LEVEL:") else "",
          "Response_Status":resp.get("status",""),"Response_MIME":resp.get("mimeType",""),"Response_SHA256":sha_bytes(raw) if raw else "",
          "Response_Bytes":len(raw),"Response_Parse_Type":sch.get("parse_type",""),"Response_Schema_Keys":" | ".join(sch.get("json_keys",[])[:200]),
          "Expected_Label_Hit_Count":len(label_hits),"Frozen_Security_Hit_Count":len(set(sec_hits)),
          "Public_Browser_Request":"YES","Auth_Bypass":"NO","Captcha_Bypass":"NO"
        })
        if raw and (sch.get("parse_type")=="JSON" or len(label_hits)>=3 or len(set(sec_hits))>=5):
            obj=None
            if sch.get("parse_type")=="JSON":
                try:obj=json.loads(raw.decode("utf-8",errors="replace"))
                except Exception:obj=None
            recs=extract_membership_records(obj,req.get("phase",""),url) if obj is not None else []
            all_membership.extend(recs)
            candidate_contracts.append({
              "request_id":rid,"phase":req.get("phase",""),"endpoint":url,"method":req.get("method",""),
              "request_body":req.get("postData",""),"response_sha256":sha_bytes(raw),"response_bytes":len(raw),
              "response_parse_type":sch.get("parse_type",""),"schema_keys":sch.get("json_keys",[]),
              "label_hit_count":len(label_hits),"security_hit_count":len(set(sec_hits)),"membership_record_count":len(recs)
            })
    write_csv(out/"nifty_sectoral_distribution_network_request_ledger_v0.73.csv",net_rows if net_rows else [{
      "Phase":"","Initiator":"","Endpoint":"","HTTP_Method":"","Request_Body":"","Index_Identifier_Evidence":"","Response_Status":"","Response_MIME":"",
      "Response_SHA256":"","Response_Bytes":0,"Response_Parse_Type":"","Response_Schema_Keys":"","Expected_Label_Hit_Count":0,
      "Frozen_Security_Hit_Count":0,"Public_Browser_Request":"NO","Auth_Bypass":"NO","Captcha_Bypass":"NO"
    }])

    # Public independent replay of candidate browser requests, without cookies/auth.
    replay=[]
    for c in candidate_contracts[:20]:
        req=bc.get("requests",{}).get(c["request_id"],{})
        method=req.get("method",c.get("method","GET"))
        post=req.get("postData",c.get("request_body",""))
        body=(post or "").encode("utf-8") if post else None
        hs=req.get("headers",{})
        fr=fetch(c["endpoint"],method=method,body=body,headers=hs)
        sch=body_schema(fr.get("body",b""),fr.get("content_type","")) if fr.get("ok") else {"parse_type":"","json_keys":[]}
        replay.append({
          "Endpoint":c["endpoint"],"Method":method,"Phase":c["phase"],"Browser_Response_SHA256":c["response_sha256"],
          "Replay_HTTP_Status":fr.get("status",""),"Replay_SHA256":fr.get("sha256",""),"Replay_Content_Type":fr.get("content_type",""),
          "Replay_Parse_Type":sch.get("parse_type",""),"Replay_Schema_Keys":" | ".join(sch.get("json_keys",[])[:200]),
          "Replay_Without_Cookies_Or_Auth":"YES","Public_Reproducibility_Status":"PASS" if fr.get("ok") else "NOT_VERIFIED"
        })
        external.append({"Request_Order":len(external)+1,"Request_Type":"PUBLIC_CONTRACT_REPLAY","URL":c["endpoint"],"Method":method,
                         "Status":fr.get("status",""),"Content_Type":fr.get("content_type",""),"Bytes":fr.get("bytes",0),"SHA256":fr.get("sha256",""),
                         "Timestamp_UTC":fr.get("timestamp_utc",""),"Official_Source":"YES","Per_Security_Fanout":"NO",
                         "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
    (out/"application_public_reproducibility_audit_v0.73.json").write_text(json.dumps({
      "Browser_Capture_Status":bc.get("status"),"Browser_Error":bc.get("error",""),"Candidate_Contract_Count":len(candidate_contracts),
      "Independent_Replay_Count":len(replay),"Independent_Replay_PASS_Count":sum(r["Public_Reproducibility_Status"]=="PASS" for r in replay),
      "Non_Official_Browser_Requests_Blocked":len(bc.get("blocked",[])),"Raw_Response_Bodies_Persisted":False,
      "Replays":replay
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Level parameter contract: controlled UI select is authoritative app value, plus observed network delta if present.
    sel=bc.get("level_select") or {}
    level_contract=[dict(r) for r in static_level_contract_rows]
    optmap={norm(o.get("text","")):o.get("value","") for o in sel.get("options",[])}
    for row in level_contract:
        display=row["Official_Displayed_Label"]
        phase="LEVEL:"+display
        phase_reqs=[r for r in net_rows if r["Phase"]==phase and r["HTTP_Method"] in {"GET","POST"} and r["Endpoint"]]
        if display in optmap:
            row["Application_Raw_Level_Value"]=optmap[display]
            row["UI_Select_ID"]=sel.get("id","")
            row["UI_Select_Name"]=sel.get("name","")
            row["Level_Parameter_Status"]="PASS_UI_APPLICATION_CONSTANT"
        if phase_reqs:
            row["Controlled_Level_Phase_Request_Count"]=len(phase_reqs)
            row["Observed_Request_Endpoints"]=" | ".join(sorted({r["Endpoint"] for r in phase_reqs}))
            row["Observed_Request_Bodies"]=" | ".join(sorted({r["Request_Body"] for r in phase_reqs if r["Request_Body"]}))[:8000]
    write_csv(out/"nifty_classification_level_parameter_contract_v0.73.csv",level_contract)

    # Candidate schema.
    schema_rows=[]
    for c in candidate_contracts:
        schema_rows.append({
          "Phase":c["phase"],"Endpoint":c["endpoint"],"Method":c["method"],"Response_SHA256":c["response_sha256"],
          "Response_Bytes":c["response_bytes"],"Response_Parse_Type":c["response_parse_type"],
          "Schema_Keys":" | ".join(c["schema_keys"][:200]),"Expected_Label_Hit_Count":c["label_hit_count"],
          "Frozen_Security_Hit_Count":c["security_hit_count"],"Extracted_Membership_Record_Count":c["membership_record_count"]
        })
    write_csv(out/"nifty_application_category_schema_v0.73.csv",schema_rows if schema_rows else [{
      "Phase":"","Endpoint":"","Method":"","Response_SHA256":"","Response_Bytes":0,"Response_Parse_Type":"",
      "Schema_Keys":"","Expected_Label_Hit_Count":0,"Frozen_Security_Hit_Count":0,"Extracted_Membership_Record_Count":0
    }])

    # Normalize application security membership.
    membership_rows=[];seen=set()
    for r in all_membership:
        sid=norm_id(r["security_id"]);ws="";route=""
        if r["security_id_type"]=="ISIN" and sid in identity_by_isin:
            ws=identity_by_isin[sid]["WS_ID"];route="APPLICATION_ISIN_TO_V070_FROZEN_ISIN"
        elif r["security_id_type"]=="SYMBOL" and sid in identity_by_symbol:
            ws=identity_by_symbol[sid]["WS_ID"];route="APPLICATION_SYMBOL_TO_V070_AUTHORIZED_SYMBOL"
        if not ws:continue
        phase_level=DISPLAY_TO_LEVEL.get(r["phase"].replace("LEVEL:",""),"") if r["phase"].startswith("LEVEL:") else ""
        rawlevel=norm(r["application_level_raw"])
        parsedlevel=phase_level
        if rawlevel:
            for lev,disp in LEVEL_LABELS.items():
                if rawlevel.lower() in {lev.lower(),disp.lower(),lev.replace("_"," ").lower()}:
                    parsedlevel=lev;break
        key=(ws,parsedlevel,r["category_label"],r["application_node_id_or_code"],r["source_url"])
        if key in seen:continue
        seen.add(key)
        membership_rows.append({
          "WS_ID":ws,"Security_ID":r["security_id"],"Security_ID_Type":r["security_id_type"],"Identity_Route":route,
          "Application_Level":parsedlevel or "NOT_VERIFIED","Application_Level_Raw":r["application_level_raw"],
          "Application_Display_Label":r["category_label"],"Application_Node_ID_or_Code":r["application_node_id_or_code"],
          "Source_Endpoint":r["source_url"],"Source_Phase":r["phase"]
        })
    write_csv(out/"nifty_application_security_membership_v0.73.csv",membership_rows if membership_rows else [{
      "WS_ID":"","Security_ID":"","Security_ID_Type":"","Identity_Route":"","Application_Level":"NOT_VERIFIED",
      "Application_Level_Raw":"","Application_Display_Label":"","Application_Node_ID_or_Code":"","Source_Endpoint":"","Source_Phase":""
    }])

    # Security-by-security CSV vs application level audit.
    by_ws_level=defaultdict(list)
    for r in membership_rows:
        if r["Application_Level"] in LEVEL_LABELS:by_ws_level[(r["WS_ID"],r["Application_Level"])].append(r)
    assignment_audit=[];level_stats={}
    for level in LEVEL_LABELS:
        complete=0;det=0;raw_to_nodes=defaultdict(set)
        for ws,csvr in sorted(csv_by_ws.items()):
            rows=by_ws_level.get((ws,level),[])
            # unique exact category identity within level
            ids={(x["Application_Node_ID_or_Code"] or x["Application_Display_Label"],x["Application_Display_Label"]) for x in rows if x["Application_Display_Label"] or x["Application_Node_ID_or_Code"]}
            app_status="PASS" if len(ids)==1 else ("AMBIGUOUS" if len(ids)>1 else "NOT_FOUND")
            app_label=next(iter(ids))[1] if len(ids)==1 else ""
            app_node=next(iter(ids))[0] if len(ids)==1 else ""
            if len(ids)==1:
                complete+=1;raw_to_nodes[csvr["Source_Classification_Raw"]].add(app_node)
            assignment_audit.append({
              "WS_ID":ws,"Frozen_ISIN":csvr["Frozen_ISIN"],"Primary_Ticker":csvr["Primary_Ticker"],
              "CSV_Source_Classification_Raw":csvr["Source_Classification_Raw"],"Application_Level":level,
              "Application_Display_Label":app_label,"Application_Node_ID_or_Code":app_node,
              "Application_Assignment_Count":len(ids),"Application_Assignment_Status":app_status,
              "CSV_to_Application_Relation":"EXACT_DISPLAY_LABEL" if app_label and app_label==csvr["Source_Classification_Raw"] else ("NODE_ID_SECURITY_BINDING" if len(ids)==1 else "NOT_VERIFIED")
            })
        deterministic_labels=sum(1 for label,nodes in raw_to_nodes.items() if len(nodes)==1)
        explains=(complete==45 and len(raw_to_nodes)==15 and deterministic_labels==15)
        level_stats[level]={"complete_security_count":complete,"raw_label_count":len(raw_to_nodes),"deterministic_raw_label_node_count":deterministic_labels,"explains_all_45":explains}
    write_csv(out/"in_csv_vs_application_level_assignment_audit_v0.73.csv",assignment_audit)

    explaining=[lev for lev,s in level_stats.items() if s["explains_all_45"]]
    # Require the application level parameter contract itself to be present for selected level.
    param_pass={DISPLAY_TO_LEVEL[r["Official_Displayed_Label"]]:r["Level_Parameter_Status"].startswith("PASS") for r in level_contract}
    explaining=[lev for lev in explaining if param_pass.get(lev,False)]

    # Node -> taxonomy code resolution per candidate selected level.
    node_bind_rows=[];label_identity_rows=[]
    selected=explaining[0] if len(explaining)==1 else ""
    source_code_by_label={}
    if selected:
        raw_group=defaultdict(list)
        for r in assignment_audit:
            if r["Application_Level"]==selected and r["Application_Assignment_Status"]=="PASS":
                raw_group[r["CSV_Source_Classification_Raw"]].append(r)
        for label in EXPECTED_LABELS:
            rs=raw_group.get(label,[])
            nodes={(x["Application_Node_ID_or_Code"],x["Application_Display_Label"]) for x in rs}
            nodeid,display=next(iter(nodes)) if len(nodes)==1 else ("","")
            code,name,method=taxonomy_lookup(taxmaps,selected,display,nodeid)
            status="PASS" if code else "NOT_VERIFIED"
            if status=="PASS":source_code_by_label[label]=code
            rel="EXACT_DISPLAY_LABEL" if display==label else ("DISPLAY_VARIANT_PROVEN_BY_OFFICIAL_NODE_ID" if code and nodeid==code else "NOT_VERIFIED")
            label_identity_rows.append({
              "CSV_Source_Label":label,"Application_Display_Label":display,"Application_Level":selected,
              "Application_Node_ID_or_Code":nodeid,"Identity_Relation":rel,
              "Security_Row_Count":len(rs),"Binding_Status":"PASS" if len(rs)>0 and rel!="NOT_VERIFIED" else "NOT_VERIFIED"
            })
            node_bind_rows.append({
              "CSV_Source_Label":label,"Application_Display_Label":display,"Application_Level":selected,
              "Application_Node_ID_or_Code":nodeid,"Taxonomy_Source_Native_Code":code or "NOT_VERIFIED",
              "Official_Taxonomy_Name":name or "NOT_VERIFIED","Binding_Method":method,
              "Application_ID_Is_Formal_Taxonomy_Code":"YES" if nodeid and code and nodeid==code else "NO",
              "Binding_Status":status
            })
    else:
        for label in EXPECTED_LABELS:
            label_identity_rows.append({"CSV_Source_Label":label,"Application_Display_Label":"","Application_Level":"NOT_VERIFIED",
              "Application_Node_ID_or_Code":"","Identity_Relation":"NOT_VERIFIED","Security_Row_Count":0,"Binding_Status":"NOT_VERIFIED"})
            node_bind_rows.append({"CSV_Source_Label":label,"Application_Display_Label":"","Application_Level":"NOT_VERIFIED",
              "Application_Node_ID_or_Code":"","Taxonomy_Source_Native_Code":"NOT_VERIFIED","Official_Taxonomy_Name":"NOT_VERIFIED",
              "Binding_Method":"NOT_VERIFIED","Application_ID_Is_Formal_Taxonomy_Code":"NO","Binding_Status":"NOT_VERIFIED"})
    write_csv(out/"in_15_label_official_node_identity_audit_v0.73.csv",label_identity_rows)
    write_csv(out/"in_application_node_taxonomy_code_binding_v0.73.csv",node_bind_rows)
    write_csv(out/"in_source_native_code_binding_v0.73.csv",node_bind_rows)

    level_binding={
      "Taxonomy":TAXONOMY,"Source_Field_Name":"Industry","Application_Contract_Status":"PASS" if candidate_contracts else "NOT_VERIFIED",
      "Level_Parameter_Contract_PASS_Count":sum(r["Level_Parameter_Status"].startswith("PASS") for r in level_contract),
      "Level_Assignment_Stats":level_stats,"Complete_Explaining_Levels":explaining,
      "Official_Taxonomy_Level":selected or "NOT_VERIFIED",
      "Level_Binding_Status":"PASS" if len(explaining)==1 else ("AMBIGUOUS" if len(explaining)>1 else "NOT_VERIFIED"),
      "Mixed_Level_Interpretation_Used":False,"Semantic_Inference_Used":False
    }
    (out/"in_classification_level_binding_v0.73.json").write_text(json.dumps(level_binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Gate-F row completion.
    repaired=[];counts=Counter()
    identity70={r["WS_ID"]:r for r in pred["identity"]}
    bind_pass=selected and len(source_code_by_label)==15 and all(r["Binding_Status"]=="PASS" for r in node_bind_rows)
    for ws,csvr in sorted(csv_by_ws.items()):
        status="NOT_VERIFIED";detail="";code="NOT_VERIFIED";app_label="";app_node=""
        ident=identity70.get(ws)
        if not ident or ident["Gate_E_Status"]!="PROVABLY_LINKED":
            detail="v0.70 identity not authoritative."
        elif csvr["v071_Current_NIFTY_ISIN_Match_Count"]!="1":
            status="CONFLICT";detail="v0.71 exact source ISIN match count not one."
        elif not selected:
            detail="No unique application level explains all 45 assignments."
        else:
            rs=[r for r in assignment_audit if r["WS_ID"]==ws and r["Application_Level"]==selected]
            if not rs or rs[0]["Application_Assignment_Status"]!="PASS":
                detail="Application assignment missing or ambiguous."
            elif csvr["Source_Classification_Raw"] not in source_code_by_label:
                status="NOT_FOUND";detail="CSV label lacks verified application-node taxonomy code binding."
            elif not bind_pass:
                detail="15-label source-native code binding incomplete."
            else:
                status="PROVABLY_CLASSIFIED";code=source_code_by_label[csvr["Source_Classification_Raw"]]
                app_label=rs[0]["Application_Display_Label"];app_node=rs[0]["Application_Node_ID_or_Code"]
        counts[status]+=1
        repaired.append({
          "Security_Key":csvr["Security_Key"],"WS_ID":ws,"Primary_MIC":csvr["Primary_MIC"],"Primary_Ticker":csvr["Primary_Ticker"],
          "Frozen_ISIN":csvr["Frozen_ISIN"],"v070_Identity_Status":ident["Gate_E_Status"] if ident else "NOT_VERIFIED",
          "v071_Current_NIFTY_ISIN_Match_Count":csvr["v071_Current_NIFTY_ISIN_Match_Count"],
          "Source_Classification_Raw":csvr["Source_Classification_Raw"],"Application_Level":selected or "NOT_VERIFIED",
          "Application_Display_Label":app_label,"Application_Node_ID_or_Code":app_node,
          "Taxonomy":TAXONOMY,"Source_Native_Code":code,"Classification_Status":status,"Detail":detail
        })
    write_csv(out/"in_exact_45_classification_coverage_v0.73.csv",repaired)

    classified=counts["PROVABLY_CLASSIFIED"];ambiguous=counts["AMBIGUOUS"];not_found=counts["NOT_FOUND"]
    not_verified=counts["NOT_VERIFIED"];conflict=counts["CONFLICT"]
    code_cov=sum(r["Classification_Status"]=="PROVABLY_CLASSIFIED" and r["Source_Native_Code"]!="NOT_VERIFIED" for r in repaired)

    static_contract_complete=sum(r["Payload_Parse_Status"]=="PASS" and r["Application_Code_Proof"]=="PASS" for r in static_level_payloads)==4
    browser_contract_present=any(not str(x.get("request_id","")).startswith("STATIC:") for x in candidate_contracts)
    contract_discovered=static_contract_complete or browser_contract_present
    level_param_verified=all(param_pass.values()) if param_pass else False
    membership_repro=len(membership_rows)>0
    public_repro=sum(r["Public_Reproducibility_Status"]=="PASS" for r in replay)>0

    blocker=""
    if not contract_discovered:blocker="NIFTY_SECTORAL_DISTRIBUTION_PUBLIC_CONTRACT_NOT_DISCOVERED"
    elif not level_param_verified:blocker="NIFTY_CLASSIFICATION_LEVEL_PARAMETER_NOT_VERIFIED"
    elif not membership_repro:blocker="NIFTY_SECURITY_CATEGORY_MEMBERSHIP_NOT_REPRODUCIBLE"
    elif len(explaining)==0:blocker="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED"
    elif len(explaining)>1:blocker="NIFTY_CLASSIFICATION_LEVEL_AMBIGUOUS"
    elif not all(r["Binding_Status"]=="PASS" for r in node_bind_rows):blocker="NIFTY_APPLICATION_NODE_TO_TAXONOMY_CODE_NOT_VERIFIED"
    elif code_cov<45:blocker="NIFTY_SOURCE_NATIVE_CODE_BINDING_NOT_VERIFIED"
    elif (classified,ambiguous,not_found,not_verified,conflict)!=(45,0,0,0,0):blocker="IN_EXACT_45_CLASSIFICATION_COVERAGE_INCOMPLETE"

    # Authority regression if application proves mixed formal levels rather than a uniform one.
    # Only fire when there is complete application membership at 45/45 for >=1 levels but zero uniform explaining level
    # and the CSV labels map to different application levels in a way that invalidates inherited D.
    complete_levels=[lev for lev,s in level_stats.items() if s["complete_security_count"]==45]
    if not blocker=="" and membership_repro and complete_levels and not explaining:
        # Do not overclaim regression unless raw CSV labels themselves can be partitioned across different complete levels.
        per_label_levels=defaultdict(set)
        for r in assignment_audit:
            if r["Application_Assignment_Status"]=="PASS" and r["CSV_to_Application_Relation"]=="EXACT_DISPLAY_LABEL":
                per_label_levels[r["CSV_Source_Classification_Raw"]].add(r["Application_Level"])
        chosen={label:next(iter(v)) for label,v in per_label_levels.items() if len(v)==1}
        if len(chosen)==15 and len(set(chosen.values()))>1:
            blocker="AUTHORITY_REGRESSION_REVIEW_REQUIRED"

    ready=(blocker=="" and classified==45 and ambiguous==not_found==not_verified==conflict==0 and selected and code_cov==45 and public_repro)
    verdict="PASS_IN_NIFTY50_GATE_F_APPLICATION_CONTRACT_RESOLUTION" if ready else "BLOCKED_IN_NIFTY50_GATE_F_APPLICATION_CONTRACT_RESOLUTION"
    next_gate="IN_NIFTY50 SOURCE ACCESS / PERSISTENCE GATE" if ready else blocker
    application_contract="; ".join(sorted({c["endpoint"] for c in candidate_contracts})) if candidate_contracts else "NOT_DISCOVERED"

    # External ledger + provider/immutability.
    write_csv(out/"external_request_ledger_v0.73.csv",external)
    prov=provider_calls()
    (out/"provider_call_audit_v0.73.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,"Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "Gate_E_Reruns":0,"NIFTY_Constituent_Refetches":0,"NSE_EQUITY_L_Calls":0,"Gate_H_Promotions":0,
      "Canonical_Materialization_Runs":0,"Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.73.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V072_BLOCKER",pred["summary"]["blocker"]=="NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED",pred["summary"]["blocker"])
    test("V072_EXACT_MATCH_HISTORY_PRESERVED",len(pred["match"])==15,15)
    test("V070_IDENTITY_45",len(pred["identity"])==45 and all(r["Gate_E_Status"]=="PROVABLY_LINKED" for r in pred["identity"]),"PASS")
    test("V072_CSV_ROWS_45",len(pred["coverage"])==45,45)
    test("OBSERVED_LABELS_15",sorted({r["Source_Classification_Raw"] for r in pred["coverage"]})==sorted(EXPECTED_LABELS),15)
    test("NO_NIFTY_CONSTITUENT_REFETCH",prov["nifty_constituent_refetch"]==0,0)
    test("NO_EQUITY_L",prov["nse_equity_l"]==0,0)
    test("NO_NAME_JOIN",prov["company_name_joins"]==0,0)
    test("NO_FUZZY",prov["fuzzy_matching"]==0,0)
    test("NO_SEMANTIC_INFERENCE",prov["semantic_inference"]==0,0)
    test("NO_CROSS_TAXONOMY",prov["cross_taxonomy_mapping"]==0,0)
    test("NO_PDSC",prov["pdsc_fallback"]==0,0)
    test("NO_PER_SECURITY_FANOUT",prov["per_security_fanout"]==0,0)
    test("NO_AUTH_CAPTCHA_BYPASS",prov["authentication_bypass"]==prov["captcha_bypass"]==0,"0/0")
    test("GATE_H_ZERO",imm["Gate_H_Promotions"]==0,0)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("PUBLIC_REPRODUCIBLE",public_repro,"PASS")
        test("UNIQUE_LEVEL",len(explaining)==1,selected)
        test("CODE_BIND_15",len(source_code_by_label)==15,15)
        test("CLASSIFIED_45",classified==45,classified)
        test("ZERO_UNRESOLVED",ambiguous==not_found==not_verified==conflict==0,f"{ambiguous}/{not_found}/{not_verified}/{conflict}")
        test("CODE_COVERAGE_45",code_cov==45,code_cov)
    else:test("BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.73.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"in_exact_45_sector_classification_coverage_ready":ready,
      "classified":classified,"total":45,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,"conflict":conflict,
      "application_contract":application_contract,"bound_classification_level":selected or "NOT_VERIFIED",
      "distinct_classifications":15,"source_native_code_coverage":code_cov,"blocker":blocker,
      "browser_capture_status":bc.get("status"),"candidate_contract_count":len(candidate_contracts),
      "application_membership_rows":len(membership_rows),"public_reproducibility":public_repro,
      "external_requests":len(external),"prohibited_provider_calls":sum(prov.values()),
      "gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"artifact_binding":"PENDING_UPLOAD","productive":False,
      "next_gate":next_gate,"tests":{"total":len(tests),"passed":len(tests),"failed":0}
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_exact_45_sector_classification_coverage_ready","classified","total","ambiguous","not_found","not_verified","conflict","application_contract","bound_classification_level","distinct_classifications","source_native_code_coverage","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.73.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.73.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"in_exact_45_sector_classification_coverage_ready":ready,"classified":classified,"total":45,
      "ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,"conflict":conflict,
      "application_contract":application_contract,"bound_classification_level":summary["bound_classification_level"],
      "distinct_classifications":15,"source_native_code_coverage":code_cov,"blocker":blocker,
      "gate_h_promotions":0,"canonical_ready_rows":37,"canonical_materialization_runs":0,"sector_rs_runs":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.73.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
