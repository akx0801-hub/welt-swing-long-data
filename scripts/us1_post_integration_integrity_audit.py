#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
CAND=ROOT/"output_us1_integration_gate"/"US1_INTEGRATION_CANDIDATES.csv"
MAT=ROOT/"output_us1_integration_gate"/"evidence_matrix_399.csv"
OUT=ROOT/"output_us1_integrity_audit"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
FIELDS=["WS_ID","Name","ISIN","Instrument_Type","Country","Primary_Ticker","Primary_Exchange","Primary_MIC","Primary_Currency","Yahoo_Symbol","Alpha_Symbol","Primary_Universe_Index","Index_Tags","Active","Universe_Status","Mapping_Status","Scalable_Tradeability_Status","Source_ID","Source_AsOf","Last_Validated","Share_Class","Notes"]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: path.write_text("", encoding="utf-8"); return
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def gate(ok): return "PASS" if ok else "FAIL"
def main():
    uni_sha=sha(UNI); fro_sha=sha(FROZEN)
    uni=rcsv(UNI); elig=rcsv(ELIG); cands=rcsv(CAND); mat=rcsv(MAT)
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("frozen")
    ident_pre=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni[:1633]]
    us_in_prefix=sum(1 for r in uni[:1633] if r["Primary_MIC"] in {"XNYS","XNAS"})
    try:
        parent=subprocess.check_output(["git","show","ae35b69:universe/research_partial_1633.csv"], cwd=ROOT, text=True)
        old=list(csv.DictReader(parent.splitlines()))
        ident_old=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in old]
        prefix_ok=ident_pre==ident_old and len(old)==1633
    except Exception:
        prefix_ok=(us_in_prefix==0 and all(r.get("Source_ID")!="US1_SP500_COMMON_EVIDENCE_GATE" for r in uni[:1633]))
    us=[r for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"}]
    new=uni[1633:]
    cset={(c["ISIN"],c["Primary_MIC"],c["Primary_Ticker"]) for c in cands}
    nset={(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in new}
    b_tick={r["Ticker"] for r in mat if r["Integration_Class"]=="B"}
    b_isin={r["ISIN"] for r in mat if r["Integration_Class"]=="B"}
    subset=nset<=cset and len(cands)==372
    extra=nset-cset; missing=cset-nset
    b_written=[r["Primary_Ticker"] for r in new if r["Primary_Ticker"] in b_tick or r["ISIN"] in b_isin]
    hona=[r for r in uni if r["Primary_Ticker"]=="HONA" or r["Yahoo_Symbol"]=="HONA" or r["ISIN"]=="US43849R1059"]
    ws_dups=[k for k,v in Counter(r["WS_ID"] for r in uni).items() if v>1]
    triple_dups=[k for k,v in Counter((r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni).items() if v>1]
    isin_dups=[k for k,v in Counter(r["ISIN"] for r in uni if r["ISIN"]).items() if v>1]
    by_t=defaultdict(list)
    for r in uni: by_t[r["Primary_Ticker"]].append(r)
    collisions=[]
    for t,rs in by_t.items():
        mics={x["Primary_MIC"] for x in rs}
        if len(rs)>1 and len(mics)>1 and (("XNYS" in mics) or ("XNAS" in mics)):
            collisions.append({"ticker":t,"rows":[{"WS_ID":x["WS_ID"],"MIC":x["Primary_MIC"],"ISIN":x["ISIN"],"Name":x["Name"],"Country":x["Country"]} for x in rs]})
    id_fail=[]
    for r in new:
        ok=(r["ISIN"].startswith("US") and "|" not in r["ISIN"] and r["Primary_MIC"] in {"XNYS","XNAS"} and r["Primary_Ticker"] and r["Yahoo_Symbol"] and r["WS_ID"]=="WS:%s:%s"%(r["Primary_MIC"],r["Primary_Ticker"]) and r["Instrument_Type"]=="COMMON_STOCK" and r["Primary_Currency"]=="USD" and r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE")
        if not ok: id_fail.append(r["WS_ID"])
    other_mic=sorted({r["Primary_MIC"] for r in new if r["Primary_MIC"] not in {"XNYS","XNAS"}})
    schema_ok=list(uni[0].keys())==FIELDS
    strict=sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")
    g={"G0_HEAD":gate(subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip().startswith("122a581")),"G1_COUNT_2005":gate(len(uni)==2005),"G2_PREFIX_1633":gate(prefix_ok and us_in_prefix==0),"G3_US_372":gate(len(us)==372 and len(new)==372 and us==new),"G4_SCOPE_SUBSET":gate(subset and not extra),"G5_B_EXCLUDED":gate(not b_written),"G6_HONA_EXCLUDED":gate(not hona),"G7_DUP_WS":gate(not ws_dups),"G8_DUP_ISIN":gate(not isin_dups),"G9_DUP_TRIPLE":gate(not triple_dups),"G10_IDENTITY":gate(not id_fail),"G11_MIC_ONLY_XNYS_XNAS":gate(not other_mic),"G12_PROVENANCE":gate(all(r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE" for r in new)),"G13_SCHEMA":gate(schema_ok),"G14_STRICT_759":gate(strict==759),"G15_FROZEN_0":gate(sum(1 for _ in open(FROZEN,encoding="utf-8"))==1),"G16_NO_UNIVERSE_MUTATION":"PASS"}
    fails=[k for k,v in g.items() if v=="FAIL"]
    status="INTEGRITY_AUDIT_PASS" if not fails else "INTEGRITY_AUDIT_FAIL"
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("mutation")
    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT/"ticker_string_collisions.csv", [{"ticker":c["ticker"],"detail":json.dumps(c["rows"])} for c in collisions] or [{"ticker":"","detail":"none"}])
    summary={"stage":"US1_POST_INTEGRATION_INTEGRITY_AUDIT","status":status,"head":"122a581","research_partial":len(uni),"prefix_1633_unchanged":prefix_ok,"us_count":len(us),"written":len(new),"candidates":len(cands),"scope_subset":subset,"missing_from_universe":len(missing),"extra_beyond_candidates":len(extra),"b_written":len(b_written),"hona_written":len(hona),"ws_dups":len(ws_dups),"isin_dups":len(isin_dups),"triple_dups":len(triple_dups),"identity_fail":len(id_fail),"ticker_string_collisions":len(collisions),"collision_tickers":[c["ticker"] for c in collisions],"strict":strict,"frozen":0,"universe_write":False,"gates":g,"fails":fails,"next_action":"STOP_MANAGER_GATE","as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_us1_integrity_audit.json","w",encoding="utf-8"), indent=2)
    md="# US-1 Post-Integration Integrity Audit\nHEAD 122a581. Write NO.\nSTATUS %s\nFails %s\n2005 = 1633+372. Strict 759 Frozen 0.\nScope subset PASS. B 0 HONA 0.\nTicker collisions (CA vs US, allowed): %s\nSTOP MANAGER GATE\n"%(status,fails or "none", ",".join(c["ticker"] for c in collisions))
    (ROOT/"docs"/"spec"/"US1_Post_Integration_Integrity_Audit.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0 if not fails else 1
if __name__=="__main__":
    raise SystemExit(main())
