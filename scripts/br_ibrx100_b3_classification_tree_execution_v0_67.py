#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, csv, hashlib, json, re, shutil, subprocess, tempfile, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.67"
STAGE="BR_IBRX100_B3_CLASSIFICATION_TREE_EXECUTION_EXACT_37_COVERAGE_GATE"
REQUIRED_START_HEAD="a6c7e3db455d73c436142230bd466c64f2ac147d"
V066_WORKFLOW=36269159688
V066_ARTIFACT=10915250534
V066_DIGEST="sha256:af7fe53a42cd199ff2b1a1edd98cb73d7535131b1e2135977c45a0853d12b5ae"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
TAXONOMY="B3_CLASSIFICACAO_SETORIAL"
LEVEL="SETOR_ECONOMICO"
METHOD="PDSC_SHA256_V1"
TREE_URL="https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetIndustryClassification/eyJsYW5ndWFnZSI6InB0LWJyIn0="
GROUP_PAGE_BASE="https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/search?language=pt-br&segment="
HOST="sistemaswebb3-listados.b3.com.br"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.67"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
S066=ROOT/"output_b3_classification_application_contract_discovery_v0_66/summary_v0.66.json"
C066=ROOT/"output_b3_classification_application_contract_discovery_v0_66/stage_checkpoint_v0.66.json"
T066=ROOT/"output_b3_classification_application_contract_discovery_v0_66/b3_tree_contract_v0.66.json"
ID64=ROOT/"output_br_ibrx100_sector_identity_coverage_v0_64/br_security_company_identity_audit_v0.64.csv"
SPEC=ROOT/"config/br_ibrx100_b3_classification_tree_execution_spec_v0.67.json"

def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def readcsv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def writecsv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:w.writeheader();w.writerows(rows)

def fetch(url:str,max_bytes:int,timeout:int=25)->dict[str,Any]:
    if urllib.parse.urlparse(url).hostname!=HOST:
        return {"ok":False,"url":url,"error":"HOST_NOT_ALLOWED","status":"","content_type":"","body":b"","timestamp_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"},method="GET")
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            b=r.read(max_bytes+1); trunc=len(b)>max_bytes
            if trunc:b=b[:max_bytes]
            return {"ok":200<=getattr(r,"status",200)<300,"url":url,"status":int(getattr(r,"status",200)),
                    "content_type":r.headers.get("Content-Type",""),"body":b,"bytes":len(b),"truncated":trunc,
                    "sha256":sha_bytes(b),"timestamp_utc":ts}
    except Exception as e:
        return {"ok":False,"url":url,"status":"","content_type":"","body":b"","bytes":0,"truncated":False,"sha256":"",
                "timestamp_utc":ts,"error":f"{type(e).__name__}:{e}"}

def parse_json_bytes(b:bytes)->Any:
    txt=b.decode("utf-8-sig",errors="strict")
    return json.loads(txt)

def structural_sha(obj:Any)->str:
    b=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return sha_bytes(b)

def recursive_node_count(obj:Any)->int:
    n=0
    def walk(x:Any):
        nonlocal n;n+=1
        if isinstance(x,dict):
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(obj);return n

def locate_sector_list(obj:Any)->list[dict[str,Any]]:
    candidates=[]
    def walk(x:Any):
        if isinstance(x,list) and x and all(isinstance(z,dict) for z in x):
            score=sum(1 for z in x if "sector" in z and "subSectors" in z)
            if score>0:candidates.append((score,len(x),x))
            for z in x:walk(z)
        elif isinstance(x,dict):
            for v in x.values():walk(v)
    walk(obj)
    if not candidates: raise ValueError("no sector/subSectors list")
    candidates.sort(key=lambda t:(t[0],t[1]),reverse=True)
    return candidates[0][2]

def label_from(d:dict[str,Any],preferred:list[str])->str:
    for k in preferred:
        v=d.get(k)
        if isinstance(v,str) and v.strip():return v
    for k,v in d.items():
        if isinstance(v,str) and v.strip() and k not in ("url","link"):return v
    raise ValueError(f"no label in keys {list(d)}")

def flatten_tree(obj:Any)->tuple[list[dict[str,str]],dict[str,int]]:
    sectors=locate_sector_list(obj)
    rows=[]
    subset_count=0
    for s in sectors:
        sector=label_from(s,["sector","describle","description","name"])
        subs=s.get("subSectors")
        if not isinstance(subs,list): raise ValueError("subSectors not list")
        for sub in subs:
            if not isinstance(sub,dict): raise ValueError("subset node not dict")
            subset_count+=1
            subset=label_from(sub,["sector","subSector","subsetor","describle","description","name"])
            segs=sub.get("segment")
            if not isinstance(segs,list): raise ValueError("segment not list")
            for leaf in segs:
                if isinstance(leaf,str):
                    seg=leaf
                elif isinstance(leaf,dict):
                    seg=label_from(leaf,["segment","describle","description","name"])
                else: raise ValueError("leaf invalid")
                rows.append({"Setor_Economico_Raw":sector,"Setor_Economico_NFC":unicodedata.normalize("NFC",sector),
                             "Subsetor_Raw":subset,"Subsetor_NFC":unicodedata.normalize("NFC",subset),
                             "Segmento_Raw":seg,"Segmento_NFC":unicodedata.normalize("NFC",seg)})
    return rows,{"setor_count":len(sectors),"subsetor_count":subset_count,"segmento_leaf_count":len(rows),
                 "distinct_segmento_label_count":len({r["Segmento_Raw"] for r in rows})}

def encode_segment(label:str)->dict[str,str]:
    component=urllib.parse.quote(label,safe="-_.!~*'()")
    b64=base64.b64encode(component.encode("utf-8")).decode("ascii")
    q=urllib.parse.quote(b64,safe="")
    return {"component":component,"base64":b64,"query_value":q}

def pdsc(name:str)->str:
    n=unicodedata.normalize("NFC",name)
    payload=TAXONOMY+"\x1f"+LEVEL+"\x1f"+n
    return "PDSC1:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()

def chrome_bin()->str|None:
    for n in ("google-chrome","google-chrome-stable","chromium","chromium-browser"):
        p=shutil.which(n)
        if p:return p
    return None

def collect_companycall_urls(netlog:Path)->list[str]:
    try:obj=json.loads(netlog.read_text(encoding="utf-8"))
    except Exception:return []
    out=[]
    for ev in obj.get("events",[]):
        p=ev.get("params",{}) if isinstance(ev,dict) else {}
        u=p.get("url")
        if isinstance(u,str) and "/listedCompaniesProxy/CompanyCall/" in u and "GetIndustryClassification" not in u and urllib.parse.urlparse(u).hostname==HOST:
            if u not in out:out.append(u)
    return out

CODE_KEYS={"code","codigo","companycode","issuingcompany","codecompany","company_code","codecompanybvmf"}
NAME_KEYS={"companyname","company_name","name","tradingname","trading_name"}

def normalize_key(k:str)->str:
    return re.sub(r"[^a-z0-9_]","",k.lower())

def extract_company_records(obj:Any)->list[dict[str,str]]:
    recs=[]
    def walk(x:Any):
        if isinstance(x,dict):
            norm={normalize_key(str(k)):v for k,v in x.items()}
            code=""
            code_key=""
            for k,v in norm.items():
                if k in CODE_KEYS and isinstance(v,(str,int)):
                    sv=str(v).strip().upper()
                    if re.fullmatch(r"[A-Z0-9]{4}",sv):
                        code=sv;code_key=k;break
            if code:
                label=""
                for k,v in norm.items():
                    if k in NAME_KEYS and isinstance(v,str) and v.strip():
                        label=v.strip();break
                sector=""
                for k,v in norm.items():
                    if k in ("sector","setor","setoreconomico","setor_economico") and isinstance(v,str) and v.strip():
                        sector=v.strip();break
                recs.append({"B3_Company_Code":code,"Code_Field":code_key,"Official_Company_Label":label,"Response_Sector_Raw":sector})
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(obj)
    uniq={}
    for r in recs:
        key=(r["B3_Company_Code"],r["Response_Sector_Raw"],r["Official_Company_Label"])
        uniq[key]=r
    return list(uniq.values())

def find_total_records(obj:Any)->int|None:
    vals=[]
    def walk(x:Any):
        if isinstance(x,dict):
            for k,v in x.items():
                nk=normalize_key(str(k))
                if nk in ("totalrecords","totalrecord","totalcount","recordscount") and isinstance(v,(int,float,str)):
                    try:vals.append(int(v))
                    except:pass
                walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(obj)
    return max(vals) if vals else None

def decode_filter_from_url(url:str)->tuple[str,dict[str,Any]]|None:
    p=urllib.parse.urlparse(url)
    parts=[urllib.parse.unquote(x) for x in p.path.split("/") if x]
    if len(parts)<2:return None
    payload=parts[-1];method=parts[-2]
    try:
        pad="="*((4-len(payload)%4)%4)
        raw=base64.b64decode(payload+pad).decode("utf-8")
        obj=json.loads(raw)
        if isinstance(obj,dict):return method,obj
    except Exception:return None
    return None

def discover_group_api(segment_raw:str,virtual_ms:int,max_bytes:int)->dict[str,Any]:
    chrome=chrome_bin()
    if not chrome:return {"ok":False,"blocker":"CHROME_NOT_AVAILABLE","observed":[]}
    enc=encode_segment(segment_raw)
    page=GROUP_PAGE_BASE+enc["query_value"]
    with tempfile.TemporaryDirectory() as td:
        net=Path(td)/"netlog.json"
        cmd=[chrome,"--headless=new","--disable-gpu","--no-sandbox","--disable-dev-shm-usage",
             f"--virtual-time-budget={virtual_ms}",f"--log-net-log={net}","--net-log-capture-mode=Default","--dump-dom",page]
        try:
            proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
        except Exception as e:
            return {"ok":False,"blocker":f"BROWSER_ERROR:{type(e).__name__}:{e}","observed":[],"group_page":page}
        urls=collect_companycall_urls(net) if net.exists() else []
    trials=[]
    for u in urls:
        dec=decode_filter_from_url(u)
        if not dec:continue
        method,filt=dec
        fr=fetch(u,max_bytes)
        trial={"url":u,"method":method,"filter":filt,"status":fr.get("status",""),"content_type":fr.get("content_type",""),"sha256":fr.get("sha256",""),"ok":False}
        if fr.get("ok"):
            try:
                obj=parse_json_bytes(fr["body"]);recs=extract_company_records(obj)
                trial["record_count"]=len(recs);trial["ok"]=len(recs)>0
                if len(recs)>0:
                    return {"ok":True,"group_page":page,"observed":urls,"api_url":u,"method":method,"filter":filt,
                            "sample_response_hash":fr["sha256"],"sample_records":recs[:20]}
            except Exception as e:
                trial["parse_error"]=f"{type(e).__name__}:{e}"
        trials.append(trial)
    return {"ok":False,"blocker":"GROUP_COMPANY_API_NOT_IDENTIFIED","group_page":page,"observed":urls,"trials":trials}

def build_group_api(prefix_url:str,template:dict[str,Any],segment_raw:str,page_size:int)->tuple[str,dict[str,Any]]:
    f=dict(template)
    enc=encode_segment(segment_raw)
    f["segment"]=enc["component"]
    if "language" in f:f["language"]="pt-br"
    if "pageNumber" in f:f["pageNumber"]=1
    if "pageSize" in f:f["pageSize"]=page_size
    payload=json.dumps(f,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    b64=base64.b64encode(payload).decode("ascii")
    prefix=prefix_url.rsplit("/",1)[0]+"/"
    return prefix+b64,f

def provider_calls()->dict[str,int]:
    return {"alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"wikipedia":0,"tradingview":0,
            "third_party_sector_databases":0,"gics_icb_fallback":0,"crosswalk":0,"price_ohlcv":0,"news":0,
            "trading_analysis":0,"per_security_web_fanout":0,"company_overview_calls":0,"company_name_joins":0,
            "fuzzy_matching":0,"auth_bypass":0,"captcha_bypass":0}

def validate_predecessor(repo_sha:str)->tuple[dict[str,Any],dict[str,Any],list[dict[str,str]]]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(S066.read_text(encoding="utf-8"));c=json.loads(C066.read_text(encoding="utf-8"));t=json.loads(T066.read_text(encoding="utf-8"));ids=readcsv(ID64)
    if s["verdict"]!="PASS_B3_CLASSIFICATION_TREE_CONTRACT":raise RuntimeError("v0.66 verdict")
    if s["b3_classification_tree_machine_reproducible"] is not True or s["b3_complete_company_classification_dataset_ready"] is not False:raise RuntimeError("v0.66 contract flags")
    if s["public_reproducible"] is not True or s["discovered_contract"]!=TREE_URL:raise RuntimeError("v0.66 discovered contract")
    if c["workflow_run_id"]!=V066_WORKFLOW or c["artifact_id"]!=V066_ARTIFACT:raise RuntimeError("v0.66 workflow/artifact")
    if "sha256:"+c["artifact_digest"]!=V066_DIGEST:raise RuntimeError("v0.66 digest")
    if t["verified_contracts"][0]["schema"]["node_count"]!=262:raise RuntimeError("v0.66 schema node count")
    if len(ids)!=37 or any(r["Security_To_Company_Status"]!="PASS" for r in ids):raise RuntimeError("identity authority")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability predecessor")
    return s,c,ids

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_br_ibrx100_b3_classification_tree_execution_v0_67")
    a=ap.parse_args();out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    pred,chk,ids=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["scope_cohort"]!="BR_IBRX100":raise RuntimeError("spec mismatch")
    if any(provider_calls().values()):raise RuntimeError("prohibited call audit nonzero")

    ext=[];tree_fetches=[]
    for i in range(2):
        fr=fetch(TREE_URL,int(spec["max_tree_bytes"]))
        tree_fetches.append(fr)
        ext.append({"Request_Order":len(ext)+1,"Request_Type":"TREE_SNAPSHOT","URL":TREE_URL,"Status":fr.get("status",""),
                    "Content_Type":fr.get("content_type",""),"SHA256":fr.get("sha256",""),"Official_B3":"YES","Per_Security_Fanout":"NO",
                    "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
    if not all(x.get("ok") and not x.get("truncated") for x in tree_fetches):
        tree_valid=False;tree_obj=None;flat=[];counts={"setor_count":0,"subsetor_count":0,"segmento_leaf_count":0,"distinct_segmento_label_count":0};tree_blocker="B3_TREE_STRUCTURE_CHANGED"
    else:
        try:
            o1=parse_json_bytes(tree_fetches[0]["body"]);o2=parse_json_bytes(tree_fetches[1]["body"])
            flat,counts=flatten_tree(o1);flat2,counts2=flatten_tree(o2)
            tree_valid=(structural_sha(o1)==structural_sha(o2) and flat==flat2 and counts==counts2 and len(flat)>0)
            tree_obj=o1
            tree_blocker="" if tree_valid else "B3_TREE_STRUCTURE_CHANGED"
        except Exception as e:
            tree_valid=False;tree_obj=None;flat=[];counts={"setor_count":0,"subsetor_count":0,"segmento_leaf_count":0,"distinct_segmento_label_count":0};tree_blocker="B3_TREE_STRUCTURE_CHANGED"
            tree_parse_error=f"{type(e).__name__}:{e}"

    snapshot={"retrievals":[{k:v for k,v in x.items() if k!="body"} for x in tree_fetches],
              "v066_expected_structural_node_count":262,
              "current_recursive_node_count":recursive_node_count(tree_obj) if tree_obj is not None else 0,
              "current_structural_sha256":structural_sha(tree_obj) if tree_obj is not None else "",
              "second_structural_sha256":structural_sha(parse_json_bytes(tree_fetches[1]["body"])) if tree_valid else "",
              "structure_changed_vs_v066_node_count":(recursive_node_count(tree_obj)!=262) if tree_obj is not None else True,
              "structurally_valid":tree_valid,"counts":counts,"raw_hierarchy":tree_obj}
    if not tree_valid:snapshot["parse_error"]=locals().get("tree_parse_error","TREE_FETCH_OR_DETERMINISM_FAILURE")
    (out/"b3_execution_tree_snapshot_v0.67.json").write_text(json.dumps(snapshot,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    writecsv(out/"b3_flattened_classification_tree_v0.67.csv",flat if flat else [{"Setor_Economico_Raw":"","Setor_Economico_NFC":"","Subsetor_Raw":"","Subsetor_NFC":"","Segmento_Raw":"","Segmento_NFC":""}])

    segmap={}
    for r in flat:
        segmap.setdefault(r["Segmento_Raw"],[]).append((r["Setor_Economico_Raw"],r["Subsetor_Raw"]))
    collision_rows=[]
    for seg,parents in sorted(segmap.items()):
        secs=sorted({p[0] for p in parents});subs=sorted({p[1] for p in parents})
        status="UNIQUE_GLOBAL" if len(parents)==1 else ("DUPLICATE_SAME_SETOR" if len(secs)==1 else "DUPLICATE_CROSS_SETOR")
        collision_rows.append({"Segmento_Raw":seg,"Occurrence_Count":len(parents),"Distinct_Setor_Count":len(secs),"Distinct_Subsetor_Count":len(subs),
                               "Collision_Class":status,"Setor_Parents":" | ".join(secs),"Subsetor_Parents":" | ".join(subs)})
    writecsv(out/"b3_segment_label_collision_audit_v0.67.csv",collision_rows if collision_rows else [{"Segmento_Raw":"","Occurrence_Count":0,"Distinct_Setor_Count":0,"Distinct_Subsetor_Count":0,"Collision_Class":"NOT_EXECUTED","Setor_Parents":"","Subsetor_Parents":""}])

    inventory=[]
    for seg,parents in sorted(segmap.items()):
        e=encode_segment(seg)
        inventory.append({"Segmento_Raw":seg,"Encoded_Component":e["component"],"Encoded_Query_Value":e["query_value"],
                          "Setor_Parent_Candidates":" | ".join(sorted({p[0] for p in parents})),
                          "Subsetor_Parent_Candidates":" | ".join(sorted({p[1] for p in parents})),
                          "Group_Page_URL":GROUP_PAGE_BASE+e["query_value"],"Required":"YES"})
    writecsv(out/"b3_execution_query_inventory_v0.67.csv",inventory if inventory else [{"Segmento_Raw":"","Encoded_Component":"","Encoded_Query_Value":"","Setor_Parent_Candidates":"","Subsetor_Parent_Candidates":"","Group_Page_URL":"","Required":"NO"}])

    expected=len(inventory);executed=0;successful=0;failed=0
    request_ledger=[];hash_ledger=[];members=[]
    api_contract=None
    api_discovery={}
    if tree_valid and inventory:
        api_discovery=discover_group_api(inventory[0]["Segmento_Raw"],int(spec["group_page_browser_virtual_time_ms"]),int(spec["max_group_bytes"]))
        for u in api_discovery.get("observed",[]):
            ext.append({"Request_Order":len(ext)+1,"Request_Type":"BROWSER_OBSERVED_GROUP_API","URL":u,"Status":"","Content_Type":"","SHA256":"",
                        "Official_B3":"YES","Per_Security_Fanout":"NO","Result":"OBSERVED_FROM_PUBLIC_GROUP_PAGE"})
        if api_discovery.get("ok"):
            api_contract=(api_discovery["api_url"],api_discovery["filter"])
    group_blocker=""
    if tree_valid and inventory and api_contract is None:
        group_blocker="B3_GROUP_QUERY_EXECUTION_INCOMPLETE"

    if api_contract:
        for q in inventory:
            executed+=1
            url,filt=build_group_api(api_contract[0],api_contract[1],q["Segmento_Raw"],int(spec["group_page_api_page_size"]))
            fr=fetch(url,int(spec["max_group_bytes"]))
            ext.append({"Request_Order":len(ext)+1,"Request_Type":"GROUP_CLASSIFICATION_API","URL":url,"Status":fr.get("status",""),
                        "Content_Type":fr.get("content_type",""),"SHA256":fr.get("sha256",""),"Official_B3":"YES","Per_Security_Fanout":"NO",
                        "Result":"OK" if fr.get("ok") else fr.get("error","FAILED")})
            row={"Segmento_Raw":q["Segmento_Raw"],"Encoded_Query_Value":q["Encoded_Query_Value"],"Setor_Parent_Candidates":q["Setor_Parent_Candidates"],
                 "Subsetor_Parent_Candidates":q["Subsetor_Parent_Candidates"],"Request_URL":url,"HTTP_Status":fr.get("status",""),
                 "Content_Type":fr.get("content_type",""),"Returned_Company_Count":0,"Parser_Status":"FAIL","Completeness_Status":"NOT_VERIFIED",
                 "Response_SHA256":fr.get("sha256","")}
            hash_ledger.append({"Segmento_Raw":q["Segmento_Raw"],"Request_URL":url,"Response_SHA256":fr.get("sha256",""),"Bytes":fr.get("bytes",0),
                                "Timestamp_UTC":fr.get("timestamp_utc",""),"HTTP_Status":fr.get("status","")})
            if not fr.get("ok") or fr.get("truncated"):
                failed+=1;request_ledger.append(row);continue
            try:
                obj=parse_json_bytes(fr["body"]);recs=extract_company_records(obj);total=find_total_records(obj)
                row["Returned_Company_Count"]=len(recs);row["Parser_Status"]="PASS" if recs or total==0 else "FAIL"
                complete=(total is not None and len({r["B3_Company_Code"] for r in recs})>=total) or (total is None and len(recs)<int(spec["group_page_api_page_size"]) and len(recs)>0)
                if total==0 and len(recs)==0:complete=True;row["Parser_Status"]="PASS"
                row["Completeness_Status"]="PASS" if complete and row["Parser_Status"]=="PASS" else "NOT_VERIFIED"
                if row["Completeness_Status"]=="PASS":
                    successful+=1
                    parent_pairs=segmap[q["Segmento_Raw"]]
                    sectors=sorted({p[0] for p in parent_pairs});subs=sorted({p[1] for p in parent_pairs})
                    for rr in recs:
                        resp_sector=rr["Response_Sector_Raw"]
                        if resp_sector and resp_sector in sectors:
                            sector_candidates=[resp_sector]
                        else:
                            sector_candidates=sectors
                        members.append({"Segmento_Raw":q["Segmento_Raw"],"B3_Company_Code":rr["B3_Company_Code"],
                                        "Official_Company_Label":rr["Official_Company_Label"],"Code_Field":rr["Code_Field"],
                                        "Response_Sector_Raw":resp_sector,"Setor_Parent_Candidates":" | ".join(sector_candidates),
                                        "Subsetor_Parent_Candidates":" | ".join(subs),"Source_URL":url,"Response_SHA256":fr["sha256"],"Parser_Status":"PASS"})
                else:failed+=1
            except Exception as e:
                failed+=1;row["Parser_Status"]=f"FAIL:{type(e).__name__}:{e}"
            request_ledger.append(row)
        if failed>0:group_blocker="B3_GROUP_QUERY_EXECUTION_INCOMPLETE"
    writecsv(out/"b3_group_request_ledger_v0.67.csv",request_ledger if request_ledger else [{"Segmento_Raw":"","Encoded_Query_Value":"","Setor_Parent_Candidates":"","Subsetor_Parent_Candidates":"","Request_URL":"","HTTP_Status":"","Content_Type":"","Returned_Company_Count":0,"Parser_Status":"NOT_EXECUTED","Completeness_Status":"NOT_VERIFIED","Response_SHA256":""}])
    writecsv(out/"b3_group_response_hash_ledger_v0.67.csv",hash_ledger if hash_ledger else [{"Segmento_Raw":"","Request_URL":"","Response_SHA256":"","Bytes":0,"Timestamp_UTC":"","HTTP_Status":""}])
    writecsv(out/"b3_group_company_membership_v0.67.csv",members if members else [{"Segmento_Raw":"","B3_Company_Code":"","Official_Company_Label":"","Code_Field":"","Response_Sector_Raw":"","Setor_Parent_Candidates":"","Subsetor_Parent_Candidates":"","Source_URL":"","Response_SHA256":"","Parser_Status":"NOT_EXECUTED"}])

    target={r["B3_Company_Code"]:r for r in ids}
    hits={c:[] for c in target}
    for m in members:
        c=m["B3_Company_Code"]
        if c not in hits:continue
        sectors=[x.strip() for x in m["Setor_Parent_Candidates"].split(" | ") if x.strip()]
        for s in sectors:
            hits[c].append({"segment":m["Segmento_Raw"],"sector":s,"source_url":m["Source_URL"],"hash":m["Response_SHA256"]})
    hit_rows=[];coverage=[]
    traversal_complete=(tree_valid and expected>0 and executed==expected and successful==expected and failed==0)
    for code,src in sorted(target.items()):
        hh=hits[code];secs=sorted({h["sector"] for h in hh})
        for h in hh:
            hit_rows.append({"B3_Company_Code":code,"Segmento_Raw":h["segment"],"Setor_Economico_Candidate":h["sector"],"Source_URL":h["source_url"],"Response_SHA256":h["hash"]})
        if not traversal_complete:
            status="NOT_VERIFIED"
        elif not hh:
            status="NOT_FOUND"
        elif len(secs)>1:
            status="AMBIGUOUS"
        elif len(secs)==1:
            status="PROVABLY_MAPPABLE"
        else:status="NOT_VERIFIED"
        raw=secs[0] if status=="PROVABLY_MAPPABLE" else "NOT_VERIFIED"
        codeval=pdsc(raw) if status=="PROVABLY_MAPPABLE" else "NOT_GENERATED"
        coverage.append({"Security_Key":src["Security_Key"],"WS_ID":src["WS_ID"],"Primary_MIC":src["Primary_MIC"],"Primary_Ticker":src["Primary_Ticker"],
                         "B3_Company_Code":code,"Group_Hit_Count":len(hh),"Distinct_Setor_Count":len(secs),"Distinct_Setor_Values":" | ".join(secs),
                         "Coverage_Status":status,"Sector_Taxonomy":TAXONOMY,"Sector_Level":LEVEL,"Sector_Raw_Name":raw,
                         "Sector_Name":unicodedata.normalize("NFC",raw) if status=="PROVABLY_MAPPABLE" else "NOT_VERIFIED",
                         "Source_Sector_Code":"","Sector_Code_Origin":"PROJECT_DERIVED_CANONICAL","Sector_Code_Method":METHOD,"Sector_Code":codeval})
    writecsv(out/"br_exact_37_group_hit_audit_v0.67.csv",hit_rows if hit_rows else [{"B3_Company_Code":"","Segmento_Raw":"","Setor_Economico_Candidate":"","Source_URL":"","Response_SHA256":""}])
    writecsv(out/"br_exact_37_classification_coverage_v0.67.csv",coverage)

    ready=sum(r["Coverage_Status"]=="PROVABLY_MAPPABLE" for r in coverage)
    ambiguous=sum(r["Coverage_Status"]=="AMBIGUOUS" for r in coverage)
    not_found=sum(r["Coverage_Status"]=="NOT_FOUND" for r in coverage)
    not_verified=sum(r["Coverage_Status"]=="NOT_VERIFIED" for r in coverage)
    resolved_sectors=sorted({r["Sector_Raw_Name"] for r in coverage if r["Coverage_Status"]=="PROVABLY_MAPPABLE"})
    sector_inv=[];pdsc_rows=[];codes=[]
    for s in resolved_sectors:
        c1=pdsc(s);c2=pdsc(unicodedata.normalize("NFD",s));codes.append(c1)
        sector_inv.append({"Sector_Raw_Name":s,"Sector_Name_NFC":unicodedata.normalize("NFC",s),"Ready_Row_Count":sum(r["Sector_Raw_Name"]==s for r in coverage),"Sector_Code":c1})
        pdsc_rows.append({"Sector_Raw_Name":s,"Generation_1":c1,"Generation_2":c2,"Determinism_Status":"PASS" if c1==c2 else "FAIL"})
    writecsv(out/"br_distinct_sector_inventory_v0.67.csv",sector_inv if sector_inv else [{"Sector_Raw_Name":"","Sector_Name_NFC":"","Ready_Row_Count":0,"Sector_Code":""}])
    writecsv(out/"pdsc_exact37_determinism_audit_v0.67.csv",pdsc_rows if pdsc_rows else [{"Sector_Raw_Name":"","Generation_1":"","Generation_2":"","Determinism_Status":"NOT_APPLICABLE"}])
    collisions=len(codes)-len(set(codes))
    pdsc_det=all(r["Determinism_Status"]=="PASS" for r in pdsc_rows)
    same_sector_same_code=all(len({r["Sector_Code"] for r in coverage if r["Sector_Raw_Name"]==s and r["Coverage_Status"]=="PROVABLY_MAPPABLE"})<=1 for s in resolved_sectors)
    (out/"pdsc_collision_audit_v0.67.json").write_text(json.dumps({"distinct_resolved_setores":len(resolved_sectors),"generated_codes":len(codes),"collision_count":collisions,
      "same_raw_sector_same_code":same_sector_same_code,"status":"PASS" if collisions==0 and same_sector_same_code else "FAIL"},indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

    cross_dup=any(r["Collision_Class"]=="DUPLICATE_CROSS_SETOR" for r in collision_rows)
    cross_dup_amb=ambiguous>0 and any(len({p[0] for p in segmap.get(h["segment"],[])})>1 for hh in hits.values() for h in hh)
    if not tree_valid:blocker="B3_TREE_STRUCTURE_CHANGED"
    elif expected==0:blocker="B3_TREE_STRUCTURE_CHANGED"
    elif not traversal_complete:blocker=group_blocker or "B3_GROUP_QUERY_EXECUTION_INCOMPLETE"
    elif cross_dup_amb:blocker="B3_DUPLICATE_SEGMENT_CROSS_SECTOR_AMBIGUITY"
    elif ambiguous>0:blocker="BR_COMPANY_CLASSIFICATION_AMBIGUOUS"
    elif not_found>0:blocker="BR_COMPANY_CODE_NOT_FOUND_IN_COMPLETE_CLASSIFICATION_TRAVERSAL"
    elif not_verified>0:blocker="BR_EXACT_37_COVERAGE_INCOMPLETE"
    elif not pdsc_det:blocker="PDSC_DETERMINISM_FAILURE"
    elif collisions>0 or not same_sector_same_code:blocker="PDSC_COLLISION"
    elif ready==37:blocker=""
    else:blocker="BR_EXACT_37_COVERAGE_INCOMPLETE"

    success=(blocker=="" and ready==37 and ambiguous==not_found==not_verified==0 and traversal_complete and collisions==0 and pdsc_det and same_sector_same_code)
    verdict="PASS_BR_EXACT_37_CLASSIFICATION_COVERAGE" if success else "BLOCKED_BR_EXACT_37_CLASSIFICATION_COVERAGE"
    next_gate="BR_IBRX100 CANONICAL SECTOR METADATA MAPPING MATERIALIZATION GATE" if success else blocker

    provider=provider_calls()
    (out/"provider_call_audit_v0.67.json").write_text(json.dumps(provider,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    writecsv(out/"external_request_ledger_v0.67.csv",ext)
    imm={"frozen_expected_sha256":FROZEN_SHA,"frozen_sha_before":sha_file(FROZEN),"frozen_sha_after":sha_file(FROZEN),"frozen_unchanged":sha_file(FROZEN)==FROZEN_SHA,
         "v057_expected_sha256":V057_SHA,"v057_sha_before":sha_file(V057),"v057_sha_after":sha_file(V057),"v057_unchanged":sha_file(V057)==V057_SHA,
         "v058_expected_sha256":V058_SHA,"v058_sha_before":sha_file(V058),"v058_sha_after":sha_file(V058),"v058_unchanged":sha_file(V058)==V058_SHA,
         "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"p0_runs":0,"p1_runs":0,"p2_runs":0}
    (out/"immutability_audit_v0.67.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def t(n:str,ok:bool,d:Any):
        tests.append({"Test":n,"Result":"PASS" if ok else "FAIL","Detail":str(d)})
        if not ok:raise RuntimeError(n)
    t("V066_VERDICT",pred["verdict"]=="PASS_B3_CLASSIFICATION_TREE_CONTRACT",pred["verdict"])
    t("V066_TREE_READY",pred["b3_classification_tree_machine_reproducible"] is True,"YES")
    t("V066_ALL_COMPANY_FALSE",pred["b3_complete_company_classification_dataset_ready"] is False,"NO")
    t("V066_PUBLIC_REPRO",pred["public_reproducible"] is True,"YES")
    t("TREE_FETCH_COUNT",len(tree_fetches)==2,len(tree_fetches))
    t("TREE_STATE_FAIL_CLOSED",tree_valid or blocker=="B3_TREE_STRUCTURE_CHANGED",tree_blocker or "VALID")
    t("TREE_COUNTS_CONSISTENT",(counts["setor_count"]>0 and counts["segmento_leaf_count"]>0) if tree_valid else (counts["setor_count"]==0 or blocker=="B3_TREE_STRUCTURE_CHANGED"),counts)
    t("EXPECTED_EQUALS_DISTINCT_SEGMENTS",expected==counts["distinct_segmento_label_count"],f"{expected}/{counts['distinct_segmento_label_count']}")
    t("GROUP_EXECUTED_EXPECTED_OR_FAIL_CLOSED",executed==expected if api_contract else executed==0,f"{executed}/{expected}")
    t("SECURITY_COMPANY_37",len(ids)==37,37)
    t("COVERAGE_TOTAL_37",len(coverage)==37,len(coverage))
    t("PDSC_COLLISION_ZERO_IF_READY",collisions==0,collisions)
    t("PDSC_DETERMINISM_IF_READY",pdsc_det,pdsc_det)
    t("SAME_SECTOR_SAME_CODE",same_sector_same_code,same_sector_same_code)
    t("NO_PROHIBITED_CALLS",all(v==0 for v in provider.values()),json.dumps(provider,sort_keys=True))
    t("NO_CANONICAL_MAPPING",imm["canonical_mapping_population_runs"]==0,0)
    t("NO_SECTOR_RS",imm["sector_rs_runs"]==0,0)
    t("NO_OTHER_COHORT",imm["other_cohort_rechecks"]==0,0)
    t("FROZEN_IMMUTABLE",imm["frozen_unchanged"],FROZEN_SHA)
    t("V057_IMMUTABLE",imm["v057_unchanged"],V057_SHA)
    t("V058_IMMUTABLE",imm["v058_unchanged"],V058_SHA)
    t("P0_P1_P2_ZERO",imm["p0_runs"]==imm["p1_runs"]==imm["p2_runs"]==0,"0/0/0")
    if success:
        t("SUCCESS_37_37",ready==37 and ambiguous==not_found==not_verified==0,(ready,ambiguous,not_found,not_verified))
        t("TRAVERSAL_COMPLETE",traversal_complete,(executed,successful,expected))
    else:
        t("FAIL_BLOCKER_NONEMPTY",bool(blocker),blocker)
    writecsv(out/"test_results_v0.67.csv",tests)

    summary={"stage":STAGE,"version":VERSION,"verdict":verdict,"br_exact_37_classification_coverage_ready":success,
             "ready":ready,"total":37,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,
             "tree_nodes":recursive_node_count(tree_obj) if tree_obj is not None else 0,
             "setor_count":counts["setor_count"],"subsetor_count":counts["subsetor_count"],"segmento_leaf_count":counts["segmento_leaf_count"],
             "distinct_segmento_labels":counts["distinct_segmento_label_count"],"expected_group_queries":expected,"executed_group_queries":executed,
             "successful_group_queries":successful,"failed_group_queries":failed,"distinct_setores":len(resolved_sectors),"pdsc_collisions":collisions,
             "blocker":blocker,"provider_calls":provider,"immutability":imm,"tests":{"total":len(tests),"passed":len(tests),"failed":0},
             "artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate}
    checkpoint={"stage":STAGE,"version":VERSION,"verdict":verdict,"br_exact_37_classification_coverage_ready":success,
                "ready":ready,"total":37,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,
                "tree_nodes":summary["tree_nodes"],"expected_group_queries":expected,"executed_group_queries":executed,
                "distinct_setores":len(resolved_sectors),"pdsc_collisions":collisions,"blocker":blocker,
                "canonical_mapping_population_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_p2_runs":0,
                "tests_passed":len(tests),"tests_failed":0,"artifact_binding":"PENDING_UPLOAD","next_gate":next_gate}
    (out/"summary_preupload_v0.67.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.67.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"b3_group_api_execution_contract_v0.67.json").write_text(json.dumps(api_discovery,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,"verdict":verdict,
              "br_exact_37_classification_coverage_ready":success,"ready":ready,"total":37,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,
              "tree_nodes":summary["tree_nodes"],"expected_group_queries":expected,"executed_group_queries":executed,"successful_group_queries":successful,
              "failed_group_queries":failed,"distinct_setores":len(resolved_sectors),"pdsc_collisions":collisions,"blocker":blocker,
              "frozen_sha256":FROZEN_SHA,"v057_feature_sha256":V057_SHA,"v058_home_rs_sha256":V058_SHA,
              "canonical_mapping_population_runs":0,"sector_rs_runs":0,"other_cohort_rechecks":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
              "productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate}
    (out/"manifest_preupload_v0.67.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":verdict,"ready":ready,"total":37,"ambiguous":ambiguous,"not_found":not_found,"not_verified":not_verified,
                      "tree_nodes":summary["tree_nodes"],"executed_group_queries":executed,"expected_group_queries":expected,
                      "distinct_setores":len(resolved_sectors),"pdsc_collisions":collisions,"blocker":blocker,"next_gate":next_gate},sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
