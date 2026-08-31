#!/usr/bin/env python3
"""v0.36 offline source-access governance decision; no network access."""
from __future__ import annotations
import argparse,csv,datetime,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output_current_master_source_governance_v0_36"
MASTER=ROOT/"universe/Welt-Swing-Universe-Master-v2.0.xlsx"
RESEARCH=ROOT/"universe/research_partial_1633.csv"
MANIFEST=ROOT/"universe/research_partial_1633_manifest.json"
SEGMENTS=("US_SP1500","MX_IPC","KR_KOSPI200","AU_ASX200","NZ_NZX50","ZA_TOP40")
IMPORTED=("EU_STOXX600","CA_TSX","JP_N225","HK_HSI","CN_CSI300","IN_NIFTY50","TW_TW50","BR_IBRX100")
GOV={
"US_SP1500":("OFFICIAL_FULL_SOURCE_BROWSER_VISIBLE_RUNNER_BLOCKED","CLOUD_BROWSER_VISIBLE","RUNNER_HTTP_403","Official S&P full-constituents UI visible; runner 403."),
"MX_IPC":("OFFICIAL_CHANGE_DOCUMENTS_ONLY","OFFICIAL_DOCUMENT_VISIBLE","RUNNER_HTTP_200_CHANGE_DOCUMENT","March 2026 official BMV PDF documents VOLAR A ADD and CUERVO * DROP, not a full constituent list."),
"KR_KOSPI200":("OFFICIAL_SOURCE_FOUND_DATA_ENDPOINT_NOT_RESOLVED","OFFICIAL_PLATFORM_REACHABLE","OFFICIAL_API_CANDIDATE_TESTED","Official KRX endpoint exists but a complete anonymous request was not evidenced."),
"AU_ASX200":("OFFICIAL_FULL_SOURCE_BROWSER_VISIBLE_RUNNER_BLOCKED","CLOUD_BROWSER_VISIBLE","RUNNER_HTTP_403","S&P full-constituents UI visible; runner 403."),
"NZ_NZX50":("OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED","OFFICIAL_ROUTE_REACHABLE","SUBSCRIPTION_EVIDENCE_TRUE","No public full-membership export materialized."),
"ZA_TOP40":("OFFICIAL_ROUTE_HTTP_BLOCKED","OFFICIAL_ROUTE_DISCOVERED","RUNNER_HTTP_403","JSE landing route and historical 2024 review evidence were blocked; no current full asset materialized.")
}
def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git_blob(p):
    return subprocess.check_output(["git","hash-object",str(p)],cwd=ROOT,text=True).strip()
def write_csv(name,rows,fields):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def xlsx_rows():
    ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships","p":"http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(MASTER) as z:
        ss=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            ss=["".join(t.text or "" for t in x.iter("{%s}t"%ns["m"])) for x in root.findall("m:si",ns)]
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid=next(s.attrib["{"+ns["r"]+"}id"] for s in wb.findall("m:sheets/m:sheet",ns) if s.attrib["name"]=="Universe_Master")
        target=next(x.attrib["Target"] for x in rels.findall("p:Relationship",ns) if x.attrib["Id"]==rid)
        sheet=ET.fromstring(z.read("xl/"+target.lstrip("/")))
        def val(c):
            v=c.find("m:v",ns)
            if v is None:return ""
            return ss[int(v.text)] if c.attrib.get("t")=="s" else v.text
        raw=[]
        for row in sheet.findall("m:sheetData/m:row",ns):
            raw.append([val(c) for c in row.findall("m:c",ns)])
    header=raw[0]; return [dict(zip(header,r+[""]*(len(header)-len(r)))) for r in raw[1:] if any(r)]
def check_inputs(cfg):
    audit=[]
    for x in cfg["frozen_inputs"]:
        p=ROOT/x["path"]; actual=git_blob(p)
        expected=x.get("blob_sha","")
        ok=(not expected) or actual==expected
        audit.append({"Path":x["path"],"Expected_Blob_SHA":expected,"Actual_Blob_SHA":actual,"PASS":ok})
        if not ok: raise RuntimeError("frozen input changed: "+x["path"])
    return audit
def self_test():
    assert GOV["MX_IPC"][0]=="OFFICIAL_CHANGE_DOCUMENTS_ONLY"
    assert len(SEGMENTS)==6 and len(IMPORTED)==8 and not(set(SEGMENTS)&set(IMPORTED))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/current_master_source_access_governance_decision_v0.36.json"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: self_test(); print("v0.36 self-test PASS"); return
    cfg=json.loads((ROOT/a.config).read_text(encoding="utf-8")); self_test()
    before_master,before_research=sha256(MASTER),sha256(RESEARCH)
    frozen=check_inputs(cfg); rows=xlsx_rows()
    if len(rows)!=1633: raise RuntimeError(f"Current Master rows must be 1633, got {len(rows)}")
    counts={}
    for r in rows:
        s=(r.get("Primary_Universe_Index") or "").strip()
        counts[s]=counts.get(s,0)+1
    imported_rows=[{"Segment_ID":s,"Current_Master_Row_Count":counts.get(s,0),"Imported":True} for s in IMPORTED]
    if any(not r["Current_Master_Row_Count"] for r in imported_rows): raise RuntimeError("missing imported target segment in workbook")
    if sum(r["Current_Master_Row_Count"] for r in imported_rows)!=1633: raise RuntimeError("eight imported segments do not sum to 1633")
    reg=[]
    for s in SEGMENTS:
        state,browser,runner,note=GOV[s]
        reg.append({"Segment_ID":s,"Governance_State_v0_36":state,"Evidence_Source_Stage":"v0.35-r3","Browser_Status":browser,"Runner_Status":runner,"Full_Membership_Materialized":False,"Materialized_Rows":0,"Canonical_Import":False,"Fallback_Allowed":False,"Remediation_Status":"DEFERRED_UNTIL_EXTERNAL_ACCESS_CHANGE","Reopen_Trigger":"new free official full route; documented official API/download change; auth/subscription change; legitimate licensed access; official platform change; manual governance recheck; later productive-promotion preparation","Notes":note})
    write_csv("remaining_segment_governance_register_v0.36.csv",reg,list(reg[0]))
    decisions=[
("OFFICIAL_SOURCE_GATE_RETAINED",True,"Official full-membership evidence remains mandatory.","v0.35-r3 frozen evidence","No substitute import."),
("THIRD_PARTY_FALLBACK_REJECTED",True,"Wikipedia, ETF holdings, screeners and unofficial lists remain prohibited.","Master + v0.35-r3","Fallback blocked."),
("LEGACY_PHASE2_MEMBERSHIP_NOT_CANONICAL",True,"Legacy phase2 membership cannot substitute official current evidence.","Master","No canonical import."),
("FULL_SCAN_NOT_ALLOWED",True,"Six target segments remain blocked.","Governance register","FULL_SCAN_ALLOWED=false."),
("RESEARCH_PARTIAL_CONTINUATION_ALLOWED",True,"Transparent 8/14 universe is permitted for DEV research.","Master governance","RESEARCH_PARTIAL_ALLOWED=true."),
("CURRENT_MASTER_1633_RETAINED",True,"No source materialization or import occurs in v0.36.","SHA256 immutability audit","1633 retained."),
("MISSING_SEGMENTS_DEFERRED",True,"Retry only after an explicit external-access-change trigger.","Governance register","Automatic retry=false."),
("GLOBAL_U3K_FREEZE_NOT_ALLOWED",True,"Global source superset is incomplete.","Master governance","No global freeze."),
("P0_NOT_RUN_IN_V0_36",True,"This is an offline governance stage.","Stage config","P0=false."),
("PRODUCTIVE_PROMOTION_NOT_ALLOWED",True,"Research-partial is not productive authority.","Master governance","productive=false.")]
    dm=[{"Decision_ID":i,"Decision":i,"State":state,"Rationale":r,"Evidence":e,"Impact":impact} for i,state,r,e,impact in decisions]
    write_csv("source_access_governance_decision_matrix_v0.36.csv",dm,list(dm[0]))
    reopen=[{"Segment_ID":r["Segment_ID"],"Current_Governance_State":r["Governance_State_v0_36"],"Remediation_Status":r["Remediation_Status"],"Reopen_Trigger":r["Reopen_Trigger"],"Automatic_Retry":False,"Required_Evidence_For_Reopen":"current official, reproducible full-membership route or legitimate documented access change"} for r in reg]
    write_csv("source_reopen_trigger_register_v0.36.csv",reopen,list(reopen[0]))
    write_csv("current_master_imported_segment_inventory_v0.36.csv",imported_rows,list(imported_rows[0]))
    scope={"schema":"v0.36","current_master_rows":1633,"research_partial_rows":1633,"imported_segments":8,"missing_segments":6,"imported_segment_counts":{x["Segment_ID"]:x["Current_Master_Row_Count"] for x in imported_rows},"segment_coverage_numerator":8,"segment_coverage_denominator":14,"source_superset_complete":False,"full_scan_allowed":False,"research_partial_allowed":True,"p0_run_v0_36":False,"swing_u3k_frozen":False,"productive":False,"alpha_vantage":False}
    (OUT/"research_partial_operating_scope_v0.36.json").write_text(json.dumps(scope,indent=2)+"\n",encoding="utf-8")
    if sha256(MASTER)!=before_master or sha256(RESEARCH)!=before_research: raise RuntimeError("immutable input changed")
    common={"stage":"CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION","version":"v0.36","status":"DEV / RESEARCH / SHADOW – NOT PRODUCTIVE","current_master_rows":1633,"imported_target_segments":8,"missing_target_segments":6,"full_scan_allowed":False,"research_partial_allowed":True,"source_superset_complete":False,"canonical_master_import_v0_36":False,"universe_mutated_v0_36":False,"eligibility_promotion_v0_36":False,"p0":False,"sector_rs":False,"swing_u3k_frozen":False,"productive":False,"alpha_vantage":False,"next_stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN","frozen_input_audit":frozen}
    for n in ("summary_v0.36.json","stage_checkpoint_v0.36.json","manifest_v0.36.json"):(OUT/n).write_text(json.dumps(common,indent=2)+"\n",encoding="utf-8")
    h=["# WELT-SWING CURRENT HANDOFF v0.36","","Current Master = 1633","Operating Mode = RESEARCH_PARTIAL","Imported = 8/14; Missing = 6/14","FULL_SCAN_ALLOWED = false","RESEARCH_PARTIAL_ALLOWED = true","Source Superset Complete = false","P0 = false","SWING_U3K_FROZEN = false","Productive = false","Alpha Vantage = false","","## Deferred missing segments"]
    h += [f"- {r['Segment_ID']}: {r['Governance_State_v0_36']} (rows 0; fallback false; automatic retry false)" for r in reg]
    h += ["","Recovery Order: v0.36 governance complete; reopen a blocked source only after documented external-access change.","Next Stage: CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN",""]
    text="\n".join(h)
    for name in ("WELT-SWING-CURRENT-Handoff-v0.36.md","WELT-SWING-CURRENT-Handoff-CURRENT.md"):(ROOT/name).write_text(text,encoding="utf-8")
if __name__=="__main__": main()
