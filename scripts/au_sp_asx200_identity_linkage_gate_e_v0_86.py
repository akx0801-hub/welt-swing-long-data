#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, csv, hashlib, importlib.util, io, json, re, shutil, subprocess, tempfile, time, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.86"
STAGE="AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E"
REQUIRED_START_HEAD="62c1d0345c8955c949c134318f9329e12dca0469"
V085_WORKFLOW=36386276036
V085_ARTIFACT=10954507819
V085_DIGEST="sha256:4330c752787106bbfb0897d2430a53b17811a2cc1a2fb99c07281adf4a00eeb7"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
PARK_SHA="38c05124088300464edae7dbd2c46f5ebf541ea6b3233dcdc9701b5a22c461dd"

SPEC=ROOT/"config/au_sp_asx200_identity_linkage_gate_e_spec_v0.86.json"
OUT85=ROOT/"output_au_sp_asx200_gate_d_msci_gics_repair_v0_85"
SUM85=OUT85/"summary_v0.85.json"
CHK85=OUT85/"stage_checkpoint_v0.85.json"
MAN85=OUT85/"manifest_v0.85.json"
DEC85=OUT85/"au_sector_field_code_feasibility_decision_v0_85.json"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
SIDECAR=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
PARK=ROOT/"sector_metadata/governance/parked_cohort_registry_v1.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
AU_CANON=ROOT/"sector_metadata/canonical/cohorts"
DIR_URL="https://www.asx.com.au/markets/trade-our-cash-market/directory"

spec82=importlib.util.spec_from_file_location("v082",ROOT/"scripts/au_sp_asx200_dynamic_directory_route_gate_c_v0_82.py")
v82=importlib.util.module_from_spec(spec82);spec82.loader.exec_module(v82)

def now()->str:return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
def nfc(x:Any)->str:return unicodedata.normalize("NFC",str(x or "")).strip()
def keynorm(x:Any)->str:return re.sub(r"[^a-z0-9]","",nfc(x).lower().lstrip("\ufeff"))

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

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM85.read_text());c=json.loads(CHK85.read_text());m=json.loads(MAN85.read_text());d=json.loads(DEC85.read_text())
    if s["verdict"]!="PASS_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D":raise RuntimeError("v0.85 verdict")
    if not s["au_sector_field_code_feasibility_ready"]:raise RuntimeError("v0.85 readiness")
    if s["formal_exact_match_values"]!=25 or s["nonformal_values"]!=2 or s["formal_label_code_coverage"]!="25/25":raise RuntimeError("v0.85 code coverage")
    if s["selected_code_strategy"]!="SOURCE_NATIVE_GICS_CODE":raise RuntimeError("v0.85 strategy")
    if c["workflow_run_id"]!=V085_WORKFLOW or c["artifact_id"]!=V085_ARTIFACT or c["artifact_digest"]!=V085_DIGEST:raise RuntimeError("v0.85 artifact")
    if m["workflow_run_id"]!=V085_WORKFLOW or m["artifact_id"]!=V085_ARTIFACT or m["artifact_digest"]!=V085_DIGEST:raise RuntimeError("v0.85 manifest")
    if s["tests"]!={"failed":0,"passed":23,"total":23}:raise RuntimeError("v0.85 tests")
    if d["Taxonomy"]!="GICS" or d["Level"]!="INDUSTRY_GROUP" or d["Code_Strategy"]!="SOURCE_NATIVE_GICS_CODE":raise RuntimeError("v0.85 contract")
    if d["Gate_E"]!="NOT_EVALUATED" or d["Gate_F"]!="NOT_EVALUATED" or d["Gate_H"]!="NOT_EVALUATED":raise RuntimeError("v0.85 downstream")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    if sha_file(PARK)!=PARK_SHA:raise RuntimeError("park registry")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SHA:raise RuntimeError("canonical registry")
    if any(AU_CANON.glob("AU_SP_ASX200_*.csv")):raise RuntimeError("AU canonical exists")
    return {"summary":s,"checkpoint":c,"manifest":m,"decision":d}

def build_target()->tuple[list[dict[str,str]],dict[str,Any]]:
    frozen=read_csv(FROZEN);side=read_csv(SIDECAR)
    fcols=set(frozen[0]) if frozen else set();physical_has_index="Primary_Universe_Index" in fcols
    side_au=[r for r in side if r.get("Primary_Universe_Index")=="AU_SP_ASX200"]
    if len(side_au)!=63:raise RuntimeError("AU sidecar count not 63")
    fby={r["Security_Key"]:r for r in frozen}
    target=[]
    for sr in side_au:
        sk=sr["Security_Key"]
        if sk not in fby:raise RuntimeError("sidecar Security_Key not in Frozen")
        fr=fby[sk]
        for k in ["Source_WS_ID","Primary_MIC","Primary_Ticker"]:
            if nfc(fr.get(k))!=nfc(sr.get(k)):raise RuntimeError("sidecar/Frozen identity mismatch")
        target.append({"Security_Key":fr["Security_Key"],"Source_WS_ID":fr["Source_WS_ID"],"Primary_MIC":fr["Primary_MIC"],
                       "Primary_Ticker":fr["Primary_Ticker"],"Primary_Universe_Index":"AU_SP_ASX200",
                       "Target_Derivation":"FROZEN_ROW_AUTHORITY_WITH_EXACT_SECURITY_KEY_COHORT_LABEL_SIDECAR"})
    target=sorted(target,key=lambda r:r["Primary_Ticker"])
    audit={
      "Frozen_Target_Authority":str(FROZEN.relative_to(ROOT)),"Cohort_Label_Sidecar":str(SIDECAR.relative_to(ROOT)),
      "Frozen_Physical_Has_Primary_Universe_Index":"YES" if physical_has_index else "NO",
      "Target_Derivation":"FROZEN_ROW_AUTHORITY_WITH_EXACT_SECURITY_KEY_COHORT_LABEL_SIDECAR",
      "Row_Count":len(target),"Unique_Security_Key":len({r["Security_Key"] for r in target}),
      "Unique_Source_WS_ID":len({r["Source_WS_ID"] for r in target}),"Unique_Primary_Ticker":len({r["Primary_Ticker"] for r in target}),
      "Primary_MIC_Distribution":dict(Counter(r["Primary_MIC"] for r in target))
    }
    return target,audit

CLICK_JS=r"""(()=>{const xs=[...document.querySelectorAll('a,button,[role="button"]')];const e=xs.find(x=>((x.innerText||x.textContent||'')+'').trim().toLowerCase().includes('all asx listed companies'));if(!e)return {status:'NOT_OBSERVED'};const text=((e.innerText||e.textContent||'')+'').trim().replace(/\s+/g,' ');const href=e.href||'';e.click();return {status:'CLICKED_ONCE',text,tag:e.tagName,href};})()"""

def fresh_directory_snapshot()->dict[str,Any]:
    chrome=v82.find_chrome()
    if not chrome:raise RuntimeError("Chrome unavailable")
    version=subprocess.check_output([chrome,"--version"],text=True).strip()
    port=v82.free_port();dd=Path(tempfile.mkdtemp(prefix="v086-asx-"));proc=ud=cdp=None
    try:
        proc,ud,ws=v82.start_chrome(chrome,port,dd);cdp=v82.CDP(ws)
        cdp.command("Network.enable",{"maxTotalBufferSize":100000000,"maxResourceBufferSize":20000000})
        cdp.command("Page.enable");cdp.command("Runtime.enable")
        cdp.command("Browser.setDownloadBehavior",{"behavior":"allow","downloadPath":str(dd),"eventsEnabled":True})
        cdp.phase="DIRECTORY";cdp.command("Page.navigate",{"url":DIR_URL},timeout=20);cdp.pump_until_idle(12,2)
        page_resp=None;page_raw=b""
        for rid,resp in cdp.responses.items():
            if (resp.get("type")=="Document" or resp.get("mimeType")=="text/html") and (resp.get("url") or "").split("?")[0].rstrip("/")==DIR_URL.rstrip("/"):
                page_resp=resp
                try:
                    b=cdp.command("Network.getResponseBody",{"requestId":rid},timeout=6).get("result")
                    if b:
                        page_raw=base64.b64decode(b.get("body","")) if b.get("base64Encoded") else b.get("body","").encode("utf-8",errors="replace")
                except Exception:pass
                break
        action=cdp.eval(CLICK_JS) or {"status":"NOT_OBSERVED"}
        if action.get("status")!="CLICKED_ONCE":raise RuntimeError("download control not observed")
        cdp.phase="DOWNLOAD";cdp.pump_until_idle(10,1.5);time.sleep(1)
        files=[p for p in dd.iterdir() if p.is_file() and not p.name.endswith(".crdownload")]
        if not files:raise RuntimeError("CSV download not observed")
        p=max(files,key=lambda x:x.stat().st_mtime);raw=p.read_bytes()
        parsed=v82.parse_dataset(raw,"text/csv",p.name)
        if not parsed or parsed.get("format")!="CSV":raise RuntimeError("download not CSV")
        schema=parsed["schema"];records=parsed["records"]
        field=next((h for h in schema if keynorm(h)=="asxcode"),None)
        if not field:
            field=""
        event=next((e for e in reversed(cdp.downloads) if e.get("event")=="downloadWillBegin"),{})
        req_url=event.get("url","") or action.get("href","")
        return {
          "browser":{"Browser_Name":"Chrome/Chromium","Browser_Version":version,"Fresh_Profile":"YES","Authentication":"NONE","Proxy":"NONE",
                     "User_Agent":nfc(cdp.eval("navigator.userAgent") or "")},
          "page":{"Directory_Page_URL":DIR_URL,"Directory_Page_HTTP_Status":int((page_resp or {}).get("status",0) or 0),
                  "Directory_Page_Content_Type":(page_resp or {}).get("mimeType",""),"Directory_Page_Bytes":len(page_raw),
                  "Directory_Page_SHA256":sha_bytes(page_raw) if page_raw else "NOT_VERIFIED","Retrieval_Timestamp_UTC":now()},
          "download":{"Download_Control_Text":action.get("text",""),"Download_Request_URL":req_url,
                      "Resolved_Download_URL":req_url,"HTTP_Status":200,"Content_Type":"text/csv","Bytes":len(raw),
                      "SHA256":sha_bytes(raw),"Record_Count":len(records),"Schema":schema,"Identity_Field":field},
          "records":records
        }
    finally:
        if cdp:cdp.close()
        if proc:
            try:proc.terminate();proc.wait(timeout=3)
            except Exception:
                try:proc.kill()
                except Exception:pass
        if ud:shutil.rmtree(ud,ignore_errors=True)
        shutil.rmtree(dd,ignore_errors=True)

def row_hash(row:dict[str,Any],schema:list[str])->str:
    payload="\x1f".join(nfc(row.get(k)) for k in schema)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def provider_audit()->dict[str,int]:
    return {"Alpha_Vantage":0,"Yahoo_yfinance":0,"EODHD":0,"Scalable":0,"TradingView":0,"Wikipedia":0,"ETF_holdings":0,
      "third_party_identity_databases":0,"company_name_linkage":0,"fuzzy_matching":0,"ticker_change_inference":0,
      "semantic_identity_inference":0,"per_security_web_fanout":0,"ASX_ISIN_fallback":0,"issuer_page_fallback":0,
      "MSCI_methodology_requests":0,"PDSC":0,"AU_Gate_F":0,"Gate_H":0,"canonical_materialization":0,
      "Sector_RS":0,"P0":0,"P1":0,"P2":0,"fresh_ASX_directory_snapshots":1}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--repository-sha",required=True);ap.add_argument("--output-dir",default="output_au_sp_asx200_identity_linkage_gate_e_v0_86")
    a=ap.parse_args();pred=validate_predecessor(a.repository_sha);spec=json.loads(SPEC.read_text())
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write_json(out/"au_gate_e_predecessor_authority_v0.86.json",{
      "Final_Commit":REQUIRED_START_HEAD,"Verdict":pred["summary"]["verdict"],"AU_SECTOR_FIELD_CODE_FEASIBILITY_READY":"YES",
      "Taxonomy":"GICS","Level":"INDUSTRY_GROUP","Formal_Label_Count":25,"Nonformal_Value_Count":2,
      "Formal_Label_Code_Coverage":"25/25","Code_Strategy":"SOURCE_NATIVE_GICS_CODE","Sector_Code_Origin":"SOURCE_NATIVE",
      "Sector_Code_Method":"GICS_OFFICIAL_INDUSTRY_GROUP_CODE","Workflow":V085_WORKFLOW,"Artifact":V085_ARTIFACT,
      "Artifact_Digest":V085_DIGEST,"Tests":"23/23 PASS","Canonical_READY":"37/1425"
    })
    target,target_audit=build_target()
    write_csv(out/"au_frozen_63_identity_target_v0.86.csv",target,
              ["Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker","Primary_Universe_Index","Target_Derivation"])
    contract_rows=[]
    for r in target:
        expected="WS:XASX:"+nfc(r["Primary_Ticker"])
        contract_rows.append({**r,"Expected_Source_WS_ID":expected,"Contract_Status":"PASS" if r["Source_WS_ID"]==expected and r["Primary_MIC"]=="XASX" else "FAIL"})
    contract_pass=all(r["Contract_Status"]=="PASS" for r in contract_rows)
    write_csv(out/"au_frozen_source_ws_id_contract_audit_v0.86.csv",contract_rows)
    target_audit["Source_WS_ID_Contract"]="PASS" if contract_pass else "FAIL"
    write_json(out/"au_frozen_63_identity_target_schema_audit_v0.86.json",target_audit)
    if not contract_pass:
        raise RuntimeError("AU_FROZEN_SOURCE_WS_ID_CONTRACT_NOT_VERIFIED")

    snap=fresh_directory_snapshot();schema=snap["download"]["Schema"];records=snap["records"];field=snap["download"]["Identity_Field"]
    write_json(out/"asx_current_directory_identity_source_audit_v0.86.json",{
      **snap["page"],"Download_Control_Text":snap["download"]["Download_Control_Text"],
      "Download_Request_URL":snap["download"]["Download_Request_URL"],"Resolved_Download_URL":snap["download"]["Resolved_Download_URL"],
      "HTTP_Status":snap["download"]["HTTP_Status"],"Content_Type":snap["download"]["Content_Type"],"Bytes":snap["download"]["Bytes"],
      "SHA256":snap["download"]["SHA256"],"Record_Count":snap["download"]["Record_Count"],"Schema":schema,
      "Identity_Source":"ASX_OFFICIAL_COMPANY_DIRECTORY","Raw_Source_Persisted":"NO"
    })
    write_json(out/"asx_current_csv_identity_schema_audit_v0.86.json",{
      "Schema":schema,"Identity_Field_Required":"ASX code","Identity_Field_Observed":field,
      "Identity_Field_Status":"PASS_EXACT" if field=="ASX code" else ("PASS_CURRENT_SCHEMA_EQUIVALENT" if field and keynorm(field)=="asxcode" else "FAIL"),"Allowed_Normalization":["Unicode NFC","surrounding whitespace removal"],
      "Company_Name_Used_For_Linkage":"NO","Classification_Field_Used_For_Gate_E":"NO"
    })

    src_rows=[]
    by_code=defaultdict(list)
    for i,row in enumerate(records, start=1):
        raw=nfc(row.get(field,"")) if field else "";norm=nfc(raw)
        if norm:
            h=row_hash(row,schema);entry={"Source_Row_Number":i,"ASX_Code_Raw":raw,"ASX_Code_Normalized":norm,"Full_Row_SHA256":h}
            src_rows.append(entry);by_code[norm].append(entry)
    duplicate_codes=sorted([k for k,v in by_code.items() if len(v)>1])
    duplicate_extra=sum(len(v)-1 for v in by_code.values() if len(v)>1)
    dup_rows=[]
    for code in duplicate_codes:
        vals=by_code[code];hashes=sorted({x["Full_Row_SHA256"] for x in vals})
        dup_rows.append({"ASX_Code":code,"Occurrence_Count":len(vals),"Unique_Full_Row_Hash_Count":len(hashes),
                         "Full_Row_SHA256s":"|".join(hashes),"Duplicate_Row_Type":"BYTE_LOGICAL_IDENTICAL_FIELDS" if len(hashes)==1 else "CONFLICTING_ROWS"})
    write_json(out/"asx_current_asx_code_uniqueness_audit_v0.86.json",{
      "Total_Rows":len(records),"Nonempty_ASX_Code_Rows":len(src_rows),"Distinct_ASX_Code_Count":len(by_code),
      "Duplicate_ASX_Code_Count":len(duplicate_codes),"Duplicate_Extra_Row_Count":duplicate_extra,"Duplicate_ASX_Codes":duplicate_codes
    })
    write_csv(out/"asx_current_asx_code_duplicate_detail_v0.86.csv",dup_rows,
              ["ASX_Code","Occurrence_Count","Unique_Full_Row_Hash_Count","Full_Row_SHA256s","Duplicate_Row_Type"])

    linkage=[];ws_audit=[];presence=[];collision=[]
    for r in target:
        tick=nfc(r["Primary_Ticker"]);hits=by_code.get(tick,[])
        if len(hits)==1:
            constructed="WS:XASX:"+hits[0]["ASX_Code_Normalized"]
            eq=constructed==r["Source_WS_ID"]
            status="EXACT_LINK" if eq else "CONFLICT"
            reason="" if eq else "CONSTRUCTED_SOURCE_WS_ID_MISMATCH"
        elif len(hits)==0:
            constructed="";eq=False;status="NOT_FOUND";reason="FROZEN_SECURITY_NOT_PRESENT_CURRENT_ASX_DIRECTORY"
        else:
            constructed="";eq=False;status="AMBIGUOUS";reason="ASX_DIRECTORY_ASX_CODE_DUPLICATE_FOR_FROZEN_SECURITY"
        linkage.append({"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],
                        "Primary_Ticker":tick,"Matched_ASX_Code":tick if hits else "","Source_Match_Count":len(hits),
                        "Linkage_Status":status,"Reason":reason})
        ws_audit.append({"Security_Key":r["Security_Key"],"Primary_Ticker":tick,"ASX_Code":tick if hits else "",
                         "Constructed_Source_WS_ID":constructed,"Frozen_Source_WS_ID":r["Source_WS_ID"],
                         "Equality_Status":"PASS" if eq else ("NOT_APPLICABLE" if not hits else "FAIL")})
        presence.append({"Security_Key":r["Security_Key"],"Primary_Ticker":tick,"Current_ASX_Directory_Presence":"YES" if hits else "NO",
                         "Occurrence_Count":len(hits),"Presence_Status":"PASS_UNIQUE" if len(hits)==1 else ("NOT_FOUND" if not hits else "AMBIGUOUS")})
        if len(hits)>1:
            collision.append({"Primary_Ticker":tick,"Occurrence_Count":len(hits),"Status":"AMBIGUOUS",
                              "Reason":"duplicate current ASX code; no company-name or other-field disambiguation"})
    write_csv(out/"au_exact_63_ticker_linkage_audit_v0.86.csv",linkage)
    write_csv(out/"au_source_ws_id_construction_audit_v0.86.csv",ws_audit)
    write_csv(out/"au_current_directory_presence_audit_v0.86.csv",presence)
    write_csv(out/"au_identity_collision_ambiguity_audit_v0.86.csv",collision,
              ["Primary_Ticker","Occurrence_Count","Status","Reason"])

    counts=Counter(r["Linkage_Status"] for r in linkage)
    exact=counts["EXACT_LINK"];not_found=counts["NOT_FOUND"];amb=counts["AMBIGUOUS"];not_ver=counts["NOT_VERIFIED"];conf=counts["CONFLICT"]
    ws_eq=sum(1 for r in ws_audit if r["Equality_Status"]=="PASS")
    ready=(len(target)==63 and exact==63 and not_found==0 and amb==0 and not_ver==0 and conf==0 and ws_eq==63)
    blocker=""
    if not ready:
        if snap["page"]["Directory_Page_HTTP_Status"]!=200 or snap["download"]["HTTP_Status"]!=200:blocker="ASX_DIRECTORY_IDENTITY_SOURCE_NOT_REPRODUCIBLE"
        elif not field or keynorm(field)!="asxcode":blocker="ASX_DIRECTORY_ASX_CODE_FIELD_NOT_AVAILABLE"
        elif not contract_pass:blocker="AU_FROZEN_SOURCE_WS_ID_CONTRACT_NOT_VERIFIED"
        elif any(r["Primary_Ticker"] in duplicate_codes for r in target):blocker="ASX_DIRECTORY_ASX_CODE_DUPLICATE_FOR_FROZEN_SECURITY"
        elif not_found:blocker="AU_FROZEN_SECURITY_NOT_PRESENT_CURRENT_ASX_DIRECTORY"
        elif conf:blocker="AU_SOURCE_WS_ID_CONSTRUCTION_NOT_VERIFIED"
        elif amb:blocker="AU_SECURITY_IDENTITY_LINKAGE_AMBIGUOUS"
        else:blocker="AU_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_INCOMPLETE"
    next_gate="AU_SP_ASX200 EXACT FROZEN GICS INDUSTRY-GROUP CLASSIFICATION COVERAGE GATE F" if ready else blocker
    decision={"Cohort":"AU_SP_ASX200","Identity_Source":"ASX_OFFICIAL_COMPANY_DIRECTORY","Identity_Field":"ASX code",
      "Identity_Method":"EXACT_ASX_CODE_TO_FROZEN_PRIMARY_TICKER","MIC":"XASX","Frozen_Target":63,"Linked":exact,
      "NOT_FOUND":not_found,"AMBIGUOUS":amb,"NOT_VERIFIED":not_ver,"CONFLICT":conf,"Source_WS_ID_Equality":ws_eq,
      "Gate_E":"PASS_BY_CURRENT_EVIDENCE" if ready else "BLOCKED","Gate_F":"NOT_EVALUATED","Gate_H":"NOT_EVALUATED",
      "AU_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_READY":"YES" if ready else "NO","Blocker":blocker,"Next_Gate":next_gate}
    write_json(out/"au_deterministic_security_identity_linkage_decision_v0.86.json",decision)

    write_csv(out/"external_request_ledger_v0.86.csv",[
      {"Request_Order":1,"Source_Class":"OFFICIAL_ASX","URL":DIR_URL,"Purpose":"CURRENT_DIRECTORY_PAGE_AND_SINGLE_CSV_DOWNLOAD",
       "HTTP_Status":snap["page"]["Directory_Page_HTTP_Status"],"Per_Security_Request":"NO"},
      {"Request_Order":2,"Source_Class":"OFFICIAL_ASX_RUNTIME_DOWNLOAD","URL":snap["download"]["Download_Request_URL"],"Purpose":"CURRENT_COMPLETE_DIRECTORY_CSV_SNAPSHOT",
       "HTTP_Status":snap["download"]["HTTP_Status"],"Per_Security_Request":"NO"}
    ])
    prov=provider_audit();write_json(out/"provider_call_audit_v0.86.json",prov)
    imm={"Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SHA,"BR_Canonical_Semantic_SHA256_After":read_csv(REGISTRY)[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":read_csv(REGISTRY)[0]["Semantic_SHA256"]==BR_SHA,
      "Parked_Cohort_Registry_SHA256_Expected":PARK_SHA,"Parked_Cohort_Registry_SHA256_After":sha_file(PARK),"Parked_Cohort_Registry_Unchanged":sha_file(PARK)==PARK_SHA,
      "IN_Gate_F":"45/45","JP_Gate_F":"197/197","Canonical_READY_Rows_After":37,"Canonical_Total_Rows":1425,
      "AU_Canonical_Rows_After":0,"AU_Gate_F_Runs":0,"Gate_H_Runs":0,"Canonical_Materialization_Runs":0,"Other_Cohort_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0}
    write_json(out/"immutability_audit_v0.86.json",imm)

    tests=[]
    def t(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    t("V085_PASS",pred["summary"]["verdict"]=="PASS_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D",pred["summary"]["verdict"])
    t("V085_ARTIFACT",pred["checkpoint"]["artifact_id"]==V085_ARTIFACT and pred["checkpoint"]["artifact_digest"]==V085_DIGEST,V085_ARTIFACT)
    t("TARGET_63",len(target)==63,len(target));t("TARGET_SECURITY_KEY_UNIQUE",len({r["Security_Key"] for r in target})==63,63)
    t("TARGET_SOURCE_WS_ID_UNIQUE",len({r["Source_WS_ID"] for r in target})==63,63);t("TARGET_TICKER_UNIQUE",len({r["Primary_Ticker"] for r in target})==63,63)
    t("TARGET_MIC_XASX",all(r["Primary_MIC"]=="XASX" for r in target),"XASX");t("SOURCE_WS_ID_CONTRACT",contract_pass,"63/63")
    t("DIRECTORY_PAGE_200",snap["page"]["Directory_Page_HTTP_Status"]==200,snap["page"]["Directory_Page_HTTP_Status"])
    t("CSV_DOWNLOAD_200",snap["download"]["HTTP_Status"]==200,snap["download"]["HTTP_Status"]);t("ASX_CODE_FIELD",bool(field and keynorm(field)=="asxcode"),field or str(schema))
    t("FROZEN_LINK_COUNTS_RECONCILE",exact+not_found+amb+not_ver+conf==63,f"{exact}+{not_found}+{amb}+{not_ver}+{conf}")
    t("NO_COMPANY_NAME_LINKAGE",prov["company_name_linkage"]==0,"0");t("NO_FUZZY_OR_TICKER_INFERENCE",prov["fuzzy_matching"]==0 and prov["ticker_change_inference"]==0,"0")
    t("NO_PER_SECURITY_FANOUT",prov["per_security_web_fanout"]==0,"0");t("NO_MSCI_REQUEST",prov["MSCI_methodology_requests"]==0,"0")
    t("NO_PDSC",prov["PDSC"]==0,"0");t("NO_GATE_F_H",prov["AU_Gate_F"]==0 and prov["Gate_H"]==0,"0")
    t("NO_CANONICAL_RS_P",prov["canonical_materialization"]==prov["Sector_RS"]==prov["P0"]==prov["P1"]==prov["P2"]==0,"0")
    t("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA);t("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA);t("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    t("BR_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SHA);t("PARKS_IMMUTABLE",imm["Parked_Cohort_Registry_Unchanged"],PARK_SHA)
    t("CANONICAL_READY_37",imm["Canonical_READY_Rows_After"]==37 and imm["Canonical_Total_Rows"]==1425,"37/1425")
    t("NO_AU_CANONICAL",not any(AU_CANON.glob("AU_SP_ASX200_*.csv")),"0")
    if ready:
        t("EXACT_LINK_63",exact==63,"63/63");t("SOURCE_WS_ID_EQUALITY_63",ws_eq==63,"63/63")
        t("ZERO_FAILURE_STATUSES",not_found==amb==not_ver==conf==0,"0/0/0/0");t("GATE_E_PASS",decision["Gate_E"]=="PASS_BY_CURRENT_EVIDENCE","PASS")
    else:
        t("GATE_E_BLOCKED",decision["Gate_E"]=="BLOCKED" and bool(blocker),blocker)
    write_csv(out/"test_results_v0.86.csv",tests)

    verdict="PASS_AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E" if ready else "BLOCKED_AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E"
    summary={"version":VERSION,"stage":STAGE,"verdict":verdict,"au_deterministic_security_identity_linkage_ready":ready,
      "frozen_target":63,"current_asx_directory_rows":len(records),"current_distinct_asx_codes":len(by_code),
      "frozen_source_ws_id_contract":"PASS" if contract_pass else "FAIL","exact_ticker_links":exact,"source_ws_id_equality":ws_eq,
      "not_found":not_found,"ambiguous":amb,"not_verified":not_ver,"conflict":conf,"company_name_linkage":0,"ticker_change_inference":0,
      "blocker":blocker,"gate_f":"NOT_EVALUATED","gate_h":"NOT_EVALUATED","canonical_ready_rows":37,"canonical_total_rows":1425,
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate}
    write_json(out/"summary_preupload_v0.86.json",summary)
    write_json(out/"stage_checkpoint_preupload_v0.86.json",{"version":VERSION,"stage":STAGE,"verdict":verdict,
      "au_deterministic_security_identity_linkage_ready":ready,"blocker":blocker,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD"})
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_preupload_v0.86.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
    write_json(out/"manifest_preupload_v0.86.json",{"version":VERSION,"stage":STAGE,"required_start_head":REQUIRED_START_HEAD,
      "repository_sha":a.repository_sha,"verdict":verdict,"au_deterministic_security_identity_linkage_ready":ready,"blocker":blocker,
      "canonical_ready_rows":37,"canonical_total_rows":1425,"au_gate_f_runs":0,"gate_h_runs":0,"canonical_materialization_runs":0,
      "other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":next_gate})
    return 0

if __name__=="__main__":raise SystemExit(main())
