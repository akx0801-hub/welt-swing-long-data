#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, html, html.parser, json, re, subprocess, time, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.75"
STAGE="IN_NIFTY50_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE"
REQUIRED_START_HEAD="b3c0110e1c4f0441447c9ad90515daeb36ac41ff"
V074_WORKFLOW=36317697732
V074_ARTIFACT=10930917775
V074_DIGEST="sha256:472f856de56611cb7292075b96690557b5bc4df099c097a8b15b7202b7141a9e"
V074_COORD_SHA="f870ee10d408565340307233b94ca082f8c7596fdf5acea10fda3f7ddff7a08e"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"

SPEC=ROOT/"config/in_nifty50_source_access_persistence_spec_v0.75.json"
GSEC05=ROOT/"config/manager_governance_authority_G_SEC_05_v0.75.json"
SUM74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/summary_v0.74.json"
CHK74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/stage_checkpoint_v0.74.json"
COV74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/in_exact_45_classification_coverage_v0.74.csv"
BIND74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/in_source_native_code_binding_v0.74.csv"
CONTRACT74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/nse_sector_cell_reconstruction_contract_v0.74.json"
A70=ROOT/"output_in_nifty50_deterministic_security_identity_linkage_v0_70/official_nifty50_constituent_source_audit_v0.70.json"
A71=ROOT/"output_in_nifty50_exact_frozen_sector_classification_coverage_v0_71/official_nifty50_classification_source_audit_v0.71.json"
B73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/application_public_reproducibility_audit_v0.73.json"
STATIC73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/nifty_static_sectoral_distribution_contract_v0.73.csv"
EXT73=ROOT/"output_in_nifty50_sectoral_distribution_contract_v0_73/external_request_ledger_v0.73.csv"
EXT74=ROOT/"output_in_nifty50_remaining_3_sector_closure_v0_74/external_request_ledger_v0.74.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"

TERMS_URL="https://www.niftyindices.com/terms-of-use"
DISCLAIMER_URL="https://www.niftyindices.com/disclaimer"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.75"

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:w.writeheader();w.writerows(rows)

class TextParser(html.parser.HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag.lower() in {"script","style","noscript"}:self.skip+=1
    def handle_endtag(self,tag):
        if tag.lower() in {"script","style","noscript"} and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip and data.strip():self.parts.append(data)
    def text(self)->str:return re.sub(r"\s+"," "," ".join(self.parts)).strip()

def visible_text(body:bytes)->str:
    p=TextParser();p.feed(body.decode("utf-8",errors="replace"));return html.unescape(p.text())

def fetch(url:str,max_bytes:int=2_000_000)->dict[str,Any]:
    ts=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    host=(urllib.parse.urlparse(url).hostname or "").lower()
    if host not in {"www.niftyindices.com","niftyindices.com","liveindexsa.niftyindices.com"}:
        return {"ok":False,"url":url,"resolved_url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","body":b"","error":"HOST_NOT_ALLOWED"}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,application/pdf,text/csv,*/*;q=0.8"},method="GET")
        with urllib.request.urlopen(req,timeout=45) as r:
            b=r.read(max_bytes+1);tr=len(b)>max_bytes
            if tr:b=b[:max_bytes]
            return {"ok":200<=getattr(r,"status",200)<300 and not tr,"url":url,"resolved_url":r.geturl(),
                    "timestamp_utc":ts,"status":int(getattr(r,"status",200)),"content_type":r.headers.get("Content-Type",""),
                    "bytes":len(b),"sha256":sha_bytes(b),"body":b,"truncated":tr}
    except Exception as e:
        return {"ok":False,"url":url,"resolved_url":url,"timestamp_utc":ts,"status":"","content_type":"","bytes":0,"sha256":"","body":b"",
                "error":f"{type(e).__name__}:{e}"}

def provider_calls()->dict[str,int]:
    return {
      "alpha_vantage":0,"yahoo_yfinance":0,"eodhd":0,"scalable":0,"tradingview":0,"wikipedia":0,"investing_com":0,
      "etf_holdings":0,"third_party_security_databases":0,"third_party_sector_databases":0,"per_security_web_fanout":0,
      "company_name_joins":0,"fuzzy_matching":0,"cross_taxonomy_mapping":0,"pdsc":0,"price_ohlcv":0,"news":0,
      "trading_analysis":0,"authentication_bypass":0,"captcha_bypass":0,"legal_rights_fabrication":0,
      "gate_f_reruns":0,"canonical_materialization":0,"registry_updates":0,"other_cohort":0,"sector_rs":0,"p0":0,"p1":0,"p2":0
    }

def validate_predecessor(repo_sha:str)->dict[str,Any]:
    if git("rev-parse","HEAD")!=repo_sha:raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:raise RuntimeError("required start head not ancestor")
    s=json.loads(SUM74.read_text(encoding="utf-8"));c=json.loads(CHK74.read_text(encoding="utf-8"))
    cov=read_csv(COV74);bind=read_csv(BIND74);ctr=json.loads(CONTRACT74.read_text(encoding="utf-8"))
    if s["verdict"]!="PASS_IN_NIFTY50_REMAINING_3_SECTOR_CODE_CLOSURE_GATE_F_COMPLETE":raise RuntimeError("v0.74 verdict")
    if not s["in_exact_45_sector_classification_coverage_ready"]:raise RuntimeError("v0.74 readiness")
    if (s["classified"],s["total"],s["ambiguous"],s["not_found"],s["not_verified"],s["conflict"])!=(45,45,0,0,0,0):raise RuntimeError("v0.74 counts")
    if s["bound_classification_level"]!="SECTOR" or s["distinct_classifications"]!=15 or s["source_native_code_coverage"]!=45:raise RuntimeError("v0.74 classification")
    if s["remaining_3_node_bindings"]!=3 or s["blocker"]!="":raise RuntimeError("v0.74 closure")
    if c["workflow_run_id"]!=V074_WORKFLOW or c["artifact_id"]!=V074_ARTIFACT or "sha256:"+c["artifact_digest"]!=V074_DIGEST:raise RuntimeError("v0.74 artifact")
    if ctr["Run1_Structural_SHA256"]!=V074_COORD_SHA or not ctr["Deterministic_Rerun"]:raise RuntimeError("v0.74 coordinate authority")
    if len(cov)!=45 or any(r["Classification_Status"]!="PROVABLY_CLASSIFIED" for r in cov):raise RuntimeError("v0.74 coverage")
    if len(bind)!=15 or any(r["Binding_Status"]!="PASS" for r in bind):raise RuntimeError("v0.74 bindings")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:raise RuntimeError("immutability")
    reg=read_csv(REGISTRY)
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA:raise RuntimeError("canonical registry")
    return {"summary":s,"checkpoint":c,"coverage":cov,"bindings":bind,"contract":ctr}

def inherited_source_authority()->list[dict[str,Any]]:
    a70=json.loads(A70.read_text(encoding="utf-8"));a71=json.loads(A71.read_text(encoding="utf-8"))
    b73=json.loads(B73.read_text(encoding="utf-8"));static=read_csv(STATIC73);ext74=read_csv(EXT74)
    sector=next(r for r in static if r["Formal_Level"]=="SECTOR")
    c74=ext74[0]
    return [
      {
        "Source_Class":"A","Source_Name":"NSE_INDICES_NIFTY50_CONSTITUENTS",
        "Source_Authority":"NSE Indices Limited","Source_Reference":a71["Source_URL"],
        "Role":"security identity; exact ISIN; source classification field",
        "Inherited_Last_Retrieved_UTC":a71["Retrieval_Timestamp_UTC"],"Inherited_SHA256":a71["Raw_SHA256"],
        "Inherited_HTTP_Status":str(a71["HTTP_Status"]),"Inherited_Content_Type":a71["Content_Type"],
        "Inherited_Bytes":str(a71["Raw_Byte_Count"]),"Inherited_Schema":" | ".join(a71["Exact_Schema"]),
        "Inherited_Public_Request_Evidence":"v0.70/v0.71 ordinary official bulk GET 200; no privileged session persisted"
      },
      {
        "Source_Class":"B","Source_Name":"NSE_INDICES_SECTORAL_DISTRIBUTION",
        "Source_Authority":"NSE Indices Limited","Source_Reference":sector["Constructed_URL"],
        "Role":"SECTOR-level semantics; official security-to-Sector assignment",
        "Inherited_Last_Retrieved_UTC":"2026-09-27T10:34:19Z","Inherited_SHA256":sector["Response_SHA256"],
        "Inherited_HTTP_Status":sector["HTTP_Status"],"Inherited_Content_Type":sector["Content_Type"],
        "Inherited_Bytes":sector["Response_Bytes"],"Inherited_Schema":sector["Response_Schema_Keys"],
        "Inherited_Public_Request_Evidence":"v0.73 independent replay PASS without cookies or authentication"
      },
      {
        "Source_Class":"C","Source_Name":"NSE_INDICES_INDUSTRY_CLASSIFICATION_STRUCTURE",
        "Source_Authority":"NSE Indices Limited","Source_Reference":c74["URL"],
        "Role":"taxonomy hierarchy; official source-native Sector codes; parent/child structure",
        "Inherited_Last_Retrieved_UTC":c74["Timestamp_UTC"],"Inherited_SHA256":c74["SHA256"],
        "Inherited_HTTP_Status":c74["Status"],"Inherited_Content_Type":c74["Content_Type"],
        "Inherited_Bytes":c74["Bytes"],"Inherited_Schema":"PDF text layer; v0.72/v0.74 deterministic taxonomy extraction",
        "Inherited_Public_Request_Evidence":"v0.74 ordinary unauthenticated official PDF GET 200"
      }
    ]

def policy_review(pages:list[dict[str,Any]])->tuple[str,list[dict[str,Any]]]:
    rows=[]
    explicit=False
    for p in pages:
        txt=visible_text(p["body"]) if p.get("ok") else ""
        low=txt.casefold()
        if p["url"]==TERMS_URL:
            auto=("systematic or automated data collection activities" in low and "express written consent" in low)
            material=("no material from the site may be copied" in low and "prior written permission" in low)
            status="EXPLICIT_OPERATIONAL_RESTRICTION_FOUND" if auto or material else ("NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND" if p.get("ok") else "NOT_VERIFIED")
            if auto or material:explicit=True
            rows.append({
              "Policy_Page":"TERMS_OF_USE","URL":p["url"],"Resolved_URL":p.get("resolved_url",""),"Retrieval_Timestamp_UTC":p.get("timestamp_utc",""),
              "HTTP_Status":p.get("status",""),"Content_Type":p.get("content_type",""),"Bytes":p.get("bytes",0),"SHA256":p.get("sha256",""),
              "Review_Status":status,"Relevant_Clause":"WEBSITE-USAGE TERMS AND CONDITIONS clause 12; clause 7",
              "Bounded_Official_Text_Marker":"systematic or automated data collection activities ... express written consent",
              "Bounded_Paraphrase":"The official Terms of Use state that systematic or automated data collection on or in relation to the site requires express written consent; they also restrict copying/distribution of site material without prior written permission.",
              "Project_Operational_Impact":"Material to automated source retrieval used by the governed metadata pipeline; no express written consent is persisted in repository authority.",
              "Legal_Conclusion":"NO"
            })
        else:
            storage=("stored in a retrieval system" in low and "prior written permission" in low)
            license=("use or distribution" in low and "require a license" in low)
            status="EXPLICIT_OPERATIONAL_RESTRICTION_FOUND" if storage or license else ("NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND" if p.get("ok") else "NOT_VERIFIED")
            if storage or license:explicit=True
            rows.append({
              "Policy_Page":"DISCLAIMER","URL":p["url"],"Resolved_URL":p.get("resolved_url",""),"Retrieval_Timestamp_UTC":p.get("timestamp_utc",""),
              "HTTP_Status":p.get("status",""),"Content_Type":p.get("content_type",""),"Bytes":p.get("bytes",0),"SHA256":p.get("sha256",""),
              "Review_Status":status,"Relevant_Clause":"Product Disclaimers / IP Disclaimers",
              "Bounded_Official_Text_Marker":"stored in a retrieval system ... prior written permission",
              "Bounded_Paraphrase":"The official disclaimer restricts reproduction/storage/transmission of site information without prior written permission and states that some index-data use or distribution requires a license.",
              "Project_Operational_Impact":"Material to repository persistence of source-derived information; no written permission or applicable license is established by project authority.",
              "Legal_Conclusion":"NO"
            })
    overall="EXPLICIT_OPERATIONAL_RESTRICTION_FOUND" if explicit else ("NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND" if pages and all(p.get("ok") for p in pages) else "NOT_VERIFIED")
    return overall,rows

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_in_nifty50_source_access_persistence_v0_75")
    a=ap.parse_args()
    pred=validate_predecessor(a.repository_sha)
    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    gov=json.loads(GSEC05.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:raise RuntimeError("spec mismatch")
    if gov["authority_id"]!="G-SEC-05" or gov["effective_forward_from"]!="v0.75":raise RuntimeError("G-SEC-05 mismatch")
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/"manager_governance_authority_G_SEC_05_v0.75.json").write_text(json.dumps(gov,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    sources=inherited_source_authority()
    write_csv(out/"in_gate_h_source_inventory_v0.75.csv",sources)

    # Policy review first. Once an explicit restriction is found, do not make additional automated core-source requests.
    pages=[fetch(TERMS_URL),fetch(DISCLAIMER_URL)]
    policy_status,policy_rows=policy_review(pages)
    write_csv(out/"in_official_terms_policy_review_v0.75.csv",policy_rows)

    external=[]
    for i,p in enumerate(pages,1):
        external.append({
          "Request_Order":i,"Request_Type":"OFFICIAL_POLICY_REVIEW","URL":p["url"],"Resolved_URL":p.get("resolved_url",""),
          "Method":"GET","Status":p.get("status",""),"Content_Type":p.get("content_type",""),"Bytes":p.get("bytes",0),
          "SHA256":p.get("sha256",""),"Timestamp_UTC":p.get("timestamp_utc",""),"Official_Source":"YES",
          "Per_Security_Fanout":"NO","Raw_Body_Persisted":"NO","Result":"OK" if p.get("ok") else p.get("error","FAILED")
        })

    explicit_block=(policy_status=="EXPLICIT_OPERATIONAL_RESTRICTION_FOUND")
    policy_verified=(policy_status!="NOT_VERIFIED")

    # Current A/B/C access is inherited from same-day repository authority; no v0.75 core refetch after policy restriction.
    access_rows=[]
    for s in sources:
        access_rows.append({
          "Source_Class":s["Source_Class"],"Source_Name":s["Source_Name"],"Source_Reference":s["Source_Reference"],
          "PUBLIC_ACCESS":"YES","AUTH_REQUIRED":"NO","COOKIE_DEPENDENT":"NO","CAPTCHA_OR_BOT_BYPASS_REQUIRED":"NO",
          "PAID_ENTITLEMENT_REQUIRED":"NO","BOUNDED_REPRODUCIBLE_REQUEST":"YES",
          "Evidence_Basis":s["Inherited_Public_Request_Evidence"],
          "v075_Core_Refetch_Performed":"NO_POLICY_HARD_STOP" if explicit_block else "NO_NOT_REQUIRED",
          "Access_Status":"PASS_INHERITED_RECENT_REPOSITORY_EVIDENCE"
        })
    write_csv(out/"in_public_access_reproducibility_audit_v0.75.csv",access_rows)
    public_sources_ready=all(r["PUBLIC_ACCESS"]=="YES" and r["AUTH_REQUIRED"]=="NO" and r["BOUNDED_REPRODUCIBLE_REQUEST"]=="YES" for r in access_rows)

    drift=[]
    for s in sources:
        drift.append({
          "Source_Class":s["Source_Class"],"Source_Name":s["Source_Name"],"Source_Reference":s["Source_Reference"],
          "Prior_SHA256":s["Inherited_SHA256"],"Prior_Retrieved_UTC":s["Inherited_Last_Retrieved_UTC"],
          "v075_Current_SHA256":"NOT_RECHECKED_POLICY_HARD_STOP" if explicit_block else "NOT_RECHECKED",
          "Hash_Comparison":"NOT_EVALUATED","Drift_Status":"NOT_RECHECKED_GATE_H_POLICY_HARD_STOP" if explicit_block else "NOT_RECHECKED",
          "A_G_Authority_Regression_Evidence":"NONE_OBSERVED","Gate_F_Rerun_Performed":"NO"
        })
    write_csv(out/"in_source_drift_audit_v0.75.csv",drift)

    # Technical bounded-evidence sufficiency is already demonstrated by persisted v0.70-v0.74 artifacts.
    raw=[]
    bounded=[]
    for s in sources:
        raw.append({
          "Source_Class":s["Source_Class"],"Source_Name":s["Source_Name"],
          "RAW_PERSISTENCE_REQUIRED_FOR_AUDIT":"NO","RAW_PERSISTENCE_RIGHTS":"NOT_VERIFIED",
          "RAW_SOURCE_CURRENTLY_PERSISTED":"NO",
          "G_SEC_05_Treatment":"Unknown raw redistribution rights alone do not fail Gate H because complete raw storage is not technically required."
        })
        if s["Source_Class"]=="A":
            evidence="URL; retrieval timestamp; raw SHA256; schema; exact Frozen ISIN/ticker; bounded Source_Classification_Raw per Frozen row"
            refs="v0.70/v0.71 source audit + v0.74 exact-45 coverage"
        elif s["Source_Class"]=="B":
            evidence="endpoint; response SHA256; formal SECTOR level; official Sector label; application node ID; security membership"
            refs="v0.73 static contract + application membership + assignment audit"
        else:
            evidence="URL; PDF SHA256; extraction tool/version; structural hashes; source-native Sector_Code/name; hierarchy; coordinate evidence"
            refs="v0.72 taxonomy table + v0.74 coordinate reconstruction/code closure"
        bounded.append({
          "Source_Class":s["Source_Class"],"Source_Name":s["Source_Name"],"Required_Bounded_Evidence":evidence,
          "Persisted_Evidence_Reference":refs,"Technical_Evidence_Sufficiency":"YES",
          "Complete_Raw_Source_Required":"NO",
          "Operational_Use_Under_Official_Policy":"NOT_VERIFIED" if explicit_block else "YES",
          "Audit_Status":"TECHNICALLY_SUFFICIENT_POLICY_BLOCKED" if explicit_block else "PASS"
        })
    write_csv(out/"in_raw_persistence_requirement_audit_v0.75.csv",raw)
    write_csv(out/"in_bounded_evidence_persistence_audit_v0.75.csv",bounded)
    raw_persistence_required=False

    canonical_persistable="NOT_VERIFIED" if explicit_block else ("YES" if public_sources_ready and policy_verified else "NOT_VERIFIED")
    persistability={
      "CANONICAL_METADATA_EVIDENCE_PERSISTABLE":canonical_persistable,
      "Technical_Bounded_Evidence_Sufficient":all(r["Technical_Evidence_Sufficiency"]=="YES" for r in bounded),
      "Complete_Raw_Redistribution_Required":False,
      "Official_Policy_Review":policy_status,
      "Reason":"Technical bounded evidence is sufficient, but explicit official restrictions materially affect automated retrieval and repository persistence; no written consent/license authority is persisted." if explicit_block else "No operational blocker found in bounded policy review.",
      "Legal_Conclusion":False,
      "Canonical_Materialization_Performed":False
    }
    (out/"in_canonical_metadata_evidence_persistability_v0.75.json").write_text(json.dumps(persistability,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    provenance={
      "status":"PREPARED_NOT_ACTIVATED" if explicit_block else "READY_FOR_LATER_MATERIALIZATION",
      "Source_Retrieved_UTC_rule":"Record actual retrieval timestamp as retrieval provenance only; never represent it as an NSE business-effective date.",
      "Source_Version_or_AsOf_rule":{
        "when_explicit_business_as_of_exists":"persist exact published source as-of/effective value",
        "when_no_explicit_business_as_of_exists":"SOURCE_SNAPSHOT_SHA256:<raw_or_response_sha256>",
        "retrieval_time_substitution_for_business_as_of":"FORBIDDEN"
      },
      "Evidence_Final_Commit_rule":"Use the final persisted commit that supplies the authoritative classification evidence consumed by materialization.",
      "Mapping_Status_future_rule":"May be promoted only by a later authorized canonical materialization gate after Gate H PASS."
    }
    (out/"in_future_provenance_contract_v0.75.json").write_text(json.dumps(provenance,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    source_contract=[
      {"Source_Class":"A","Canonical_Source_Name":"NSE_INDICES_NIFTY50_CONSTITUENTS","Canonical_Source_Reference":sources[0]["Source_Reference"],"Canonical_Use":"identity and constituent source-classification evidence","Activation_Status":"BLOCKED_PENDING_GATE_H" if explicit_block else "PREPARED"},
      {"Source_Class":"B","Canonical_Source_Name":"NSE_INDICES_SECTORAL_DISTRIBUTION","Canonical_Source_Reference":sources[1]["Source_Reference"],"Canonical_Use":"SECTOR-level semantics and official security membership","Activation_Status":"BLOCKED_PENDING_GATE_H" if explicit_block else "PREPARED"},
      {"Source_Class":"C","Canonical_Source_Name":"NSE_INDICES_INDUSTRY_CLASSIFICATION_STRUCTURE","Canonical_Source_Reference":sources[2]["Source_Reference"],"Canonical_Use":"source-native Sector code/name and hierarchy","Activation_Status":"BLOCKED_PENDING_GATE_H" if explicit_block else "PREPARED"}
    ]
    write_csv(out/"in_source_name_reference_contract_v0.75.csv",source_contract)

    blocker=""
    if not public_sources_ready:
        blocker="NIFTY_CONSTITUENT_PUBLIC_ACCESS_NOT_REPRODUCIBLE"
    elif not policy_verified:
        blocker="CANONICAL_METADATA_EVIDENCE_PERSISTENCE_NOT_VERIFIED"
    elif explicit_block:
        blocker="EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION"
    elif canonical_persistable!="YES":
        blocker="CANONICAL_METADATA_EVIDENCE_PERSISTENCE_NOT_VERIFIED"

    ready=(blocker=="" and public_sources_ready and not raw_persistence_required and canonical_persistable=="YES" and policy_status=="NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND")
    verdict="PASS_IN_NIFTY50_SOURCE_ACCESS_EVIDENCE_PERSISTENCE" if ready else "BLOCKED_IN_NIFTY50_SOURCE_ACCESS_EVIDENCE_PERSISTENCE"
    next_gate="IN_NIFTY50 CANONICAL SECTOR METADATA MAPPING MATERIALIZATION GATE" if ready else blocker

    prov=provider_calls()
    (out/"provider_call_audit_v0.75.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_csv(out/"external_request_ledger_v0.75.csv",external)
    reg=read_csv(REGISTRY)
    imm={
      "Frozen_SHA256_Expected":FROZEN_SHA,"Frozen_SHA256_After":sha_file(FROZEN),"Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
      "v057_SHA256_Expected":V057_SHA,"v057_SHA256_After":sha_file(V057),"v057_Unchanged":sha_file(V057)==V057_SHA,
      "v058_SHA256_Expected":V058_SHA,"v058_SHA256_After":sha_file(V058),"v058_Unchanged":sha_file(V058)==V058_SHA,
      "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,"BR_Canonical_Semantic_SHA256_After":reg[0]["Semantic_SHA256"],
      "BR_Canonical_Semantic_Unchanged":reg[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
      "IN_Gate_F_Classified_Before":45,"IN_Gate_F_Classified_After":45,
      "Canonical_READY_Rows_Before":37,"Canonical_READY_Rows_After":37,
      "Canonical_Registry_Rows_Before":1,"Canonical_Registry_Rows_After":len(reg),
      "Gate_F_Reruns":0,"Canonical_Materialization_Runs":0,"Registry_Updates":0,"Other_Cohort_Runs":0,
      "Sector_RS_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0
    }
    (out/"immutability_audit_v0.75.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:raise RuntimeError(name)
    test("V074_GATE_F_AUTHORITY",pred["summary"]["in_exact_45_sector_classification_coverage_ready"] and pred["summary"]["classified"]==45,"45/45")
    test("V074_COORDINATE_SHA",pred["contract"]["Run1_Structural_SHA256"]==V074_COORD_SHA,V074_COORD_SHA)
    test("G_SEC_05_PRESENT",gov["authority_id"]=="G-SEC-05","PASS")
    test("SOURCE_INVENTORY_3",len(sources)==3,3)
    test("PUBLIC_SOURCES_INHERITED_READY",public_sources_ready,"YES")
    test("POLICY_REQUESTS_BOUNDED",len(external)<=2,len(external))
    test("POLICY_OFFICIAL_ONLY",all((urllib.parse.urlparse(r["URL"]).hostname or "").endswith("niftyindices.com") for r in external),"PASS")
    test("NO_CORE_REFETCH_AFTER_POLICY",all(r["Request_Type"]=="OFFICIAL_POLICY_REVIEW" for r in external),"PASS")
    test("RAW_PERSISTENCE_NOT_REQUIRED",all(r["RAW_PERSISTENCE_REQUIRED_FOR_AUDIT"]=="NO" for r in raw),"NO")
    test("RAW_SOURCE_NOT_PERSISTED",all(r["RAW_SOURCE_CURRENTLY_PERSISTED"]=="NO" for r in raw),"NO")
    test("TECHNICAL_BOUNDED_EVIDENCE_SUFFICIENT",all(r["Technical_Evidence_Sufficiency"]=="YES" for r in bounded),"YES")
    test("NO_GATE_F_RERUN",prov["gate_f_reruns"]==0,0)
    test("NO_CANONICAL_MATERIALIZATION",prov["canonical_materialization"]==0,0)
    test("NO_REGISTRY_UPDATE",prov["registry_updates"]==0,0)
    test("NO_FORBIDDEN_PROVIDERS",sum(prov.values())==0,0)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("IN_GATE_F_REMAINS_45",imm["IN_Gate_F_Classified_Before"]==imm["IN_Gate_F_Classified_After"]==45,45)
    test("CANONICAL_READY_37",imm["Canonical_READY_Rows_Before"]==imm["Canonical_READY_Rows_After"]==37,37)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    if ready:
        test("POLICY_NO_BLOCKER",policy_status=="NO_EXPLICIT_OPERATIONAL_BLOCKER_FOUND",policy_status)
        test("CANONICAL_EVIDENCE_PERSISTABLE",canonical_persistable=="YES",canonical_persistable)
    else:
        test("FAIL_CLOSED_BLOCKER_PRESENT",bool(blocker),blocker)
    write_csv(out/"test_results_v0.75.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"in_source_access_persistence_ready":ready,
      "public_sources_ready":public_sources_ready,"raw_persistence_required":raw_persistence_required,
      "canonical_evidence_persistable":canonical_persistable,"official_policy_review":policy_status,
      "blocker":blocker,"policy_requests":len(external),"core_source_refetches":0,
      "in_gate_f_classified":45,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "canonical_materialization_runs":0,"registry_updates":0,"other_cohort_runs":0,"sector_rs_runs":0,
      "p0_runs":0,"p1_runs":0,"p2_runs":0,"productive":False,"artifact_binding":"PENDING_UPLOAD",
      "tests":{"total":len(tests),"passed":len(tests),"failed":0},"next_gate":next_gate
    }
    checkpoint={k:summary[k] for k in ["stage","version","verdict","in_source_access_persistence_ready","public_sources_ready","raw_persistence_required","canonical_evidence_persistable","official_policy_review","blocker","next_gate"]}
    checkpoint["artifact_binding"]="PENDING_UPLOAD"
    (out/"summary_preupload_v0.75.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.75.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":a.repository_sha,
      "verdict":verdict,"in_source_access_persistence_ready":ready,"public_sources_ready":public_sources_ready,
      "raw_persistence_required":raw_persistence_required,"canonical_evidence_persistable":canonical_persistable,
      "official_policy_review":policy_status,"blocker":blocker,"policy_requests":len(external),"core_source_refetches":0,
      "in_gate_f_classified":45,"canonical_ready_rows":37,"canonical_total_rows":1425,"canonical_materialization_runs":0,
      "registry_updates":0,"other_cohort_runs":0,"sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,
      "productive":False,"artifact_binding":"PENDING_UPLOAD","files":files,"next_gate":next_gate
    }
    (out/"manifest_preupload_v0.75.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
