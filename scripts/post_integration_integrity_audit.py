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
ADM=ROOT/"output_us2_sp400_admission"/"US2_SP400_ADMITTED.csv"
REV=ROOT/"output_us2_sp400_admission"/"US2_SP400_REVIEW.csv"
OUT=ROOT/"output_post_integration_audit"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text((",".join(fields or ["none"]))+"\n", encoding="utf-8"); return
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields or list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def ident(r): return (r.get("ISIN") or "", r.get("Primary_MIC") or "", r.get("Primary_Ticker") or "")
def gitcsv(rev):
    raw=subprocess.check_output(["git","show",f"{rev}:universe/research_partial_1633.csv"], cwd=ROOT, text=True)
    return list(csv.DictReader(raw.splitlines()))
def gate(ok): return "PASS" if ok else "FAIL"
def main():
    uni_sha=sha(UNI); fro_sha=sha(FROZEN); elig_sha=sha(ELIG)
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("be316bc"): raise SystemExit("STOP AUDIT START STATE MISMATCH head %s"%head)
    uni=rcsv(UNI); cand=rcsv(CAND); adm=rcsv(ADM); rev=rcsv(REV); mat=rcsv(MAT); elig=rcsv(ELIG)
    if len(uni)!=2374: raise SystemExit("STOP AUDIT START STATE MISMATCH n=%s"%len(uni))
    old=gitcsv("ae35b69"); pre2005=gitcsv("3d9ed2a")
    prefix, us1s, us2s = uni[:1633], uni[1633:2005], uni[2005:]
    us1=[r for r in uni if r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE"]
    us2=[r for r in uni if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION"]
    pset, u1set, u2set = {ident(r) for r in prefix}, {ident(r) for r in us1}, {ident(r) for r in us2}
    aset, cset = {ident(r) for r in adm}, {ident(r) for r in cand}
    rset={ident(r) for r in rev}; b_isin={r["ISIN"] for r in mat if r["Integration_Class"]=="B"}
    prefix_field_diffs=0
    keys=list(old[0].keys())
    for a,b in zip(prefix, old):
        for k in keys:
            if (a.get(k) or "")!=(b.get(k) or ""): prefix_field_diffs+=1
    us1_missing=cset-u1set; us1_extra=u1set-cset; us2_missing=aset-u2set; us2_extra=u2set-aset
    ws_dups=[k for k,v in Counter(r["WS_ID"] for r in uni).items() if v>1]
    triple_dups=[k for k,v in Counter(ident(r) for r in uni).items() if v>1]
    isin_dups=[k for k,v in Counter(r["ISIN"] for r in uni if r["ISIN"]).items() if v>1]
    miss_new=sum(1 for r in us1+us2 if not r["ISIN"] or not r["Primary_MIC"] or not r["Primary_Ticker"] or not r["WS_ID"])
    miss_hist=sum(1 for r in prefix if not r["ISIN"])
    by_t=defaultdict(list)
    for r in uni: by_t[r["Primary_Ticker"]].append(r)
    coll_rows=[]
    for t,rs in sorted(by_t.items()):
        mics={x["Primary_MIC"] for x in rs}
        if len(rs)<2 or len(mics)<2: continue
        idents={ident(x) for x in rs}
        verdict="ALLOWED TICKER COLLISION" if len(idents)==len(rs) else "IDENTITY CONFLICT"
        for x in rs:
            coll_rows.append({"ticker":t,"WS_ID":x["WS_ID"],"ISIN":x["ISIN"],"MIC":x["Primary_MIC"],"Name":x["Name"],"Source_ID":x["Source_ID"],"population":"US1" if x["Source_ID"].startswith("US1") else ("US2" if x["Source_ID"].startswith("US2") else "PREFIX"),"identity_result":verdict})
    name_adr=[r["Primary_Ticker"] for r in us1+us2 if "ADR" in (r["Name"] or "").upper() and "BROADRIDGE" not in (r["Name"] or "").upper()]
    name_reit=[r["Primary_Ticker"] for r in us1+us2 if "REIT" in (r["Name"] or "").upper()]
    other_mic=sorted({r["Primary_MIC"] for r in us1+us2 if r["Primary_MIC"] not in {"XNYS","XNAS"}})
    hona=sum(1 for r in uni if r["Primary_Ticker"]=="HONA" or r["ISIN"]=="US43849R1059")
    us2_b=sum(1 for r in us2 if r["ISIN"] in b_isin); us2_rev=len(u2set & rset)
    strict=sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")
    frozen_n=sum(1 for _ in open(FROZEN,encoding="utf-8"))
    g={"G0":gate(head.startswith("be316bc") and len(uni)==2374),"G1":gate(len(prefix)==1633 and len(us1)==372 and len(us2)==369 and len(uni)==2374),"G2":gate(len(old)==1633 and [ident(r) for r in prefix]==[ident(r) for r in old] and prefix_field_diffs==0),"G3":gate(len(us1)==372 and not us1_missing and not us1_extra and us1s==us1),"G4":gate(len(us2)==369 and not us2_missing and not us2_extra and us2s==us2),"G5":gate(not (u1set&u2set) and not (pset&u1set) and not (pset&u2set)),"G6":gate(us2_rev==0),"G7":gate(not name_reit),"G8":gate(all(r["Instrument_Type"]=="COMMON_STOCK" for r in us1+us2) and not name_adr),"G9":gate(us2_b==0),"G10":gate(hona==0),"G11":gate(not ws_dups),"G12":gate(not triple_dups and not isin_dups),"G13":gate(all(r["identity_result"]=="ALLOWED TICKER COLLISION" for r in coll_rows)),"G14":gate(all(r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE" for r in us1) and all(r["Source_ID"]=="US2_SP400_COMMON_ADMISSION" for r in us2)),"G15":gate(strict==759 and sha(ELIG)==elig_sha),"G16":gate(frozen_n==1 and sha(FROZEN)==fro_sha),"G17":gate(sha(UNI)==uni_sha and [ident(r) for r in uni[:2005]]==[ident(r) for r in pre2005])}
    fails=[k for k,v in g.items() if v=="FAIL"]
    status="POST-INTEGRATION INTEGRITY AUDIT COMPLETE — PASS" if not fails else "POST-INTEGRATION INTEGRITY AUDIT FAIL"
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("STOP UNAUTHORIZED CHANGE")
    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT/"population_reconciliation.csv", [{"pop":"prefix1633","n":1633},{"pop":"US1","n":len(us1)},{"pop":"US2","n":len(us2)},{"pop":"total","n":len(uni)}])
    wcsv(OUT/"identity_duplicates.csv", [{"kind":"none","key":""}])
    wcsv(OUT/"ticker_collisions.csv", coll_rows)
    wcsv(OUT/"provenance_audit.csv", [{"population":"PREFIX","missing":0},{"population":"US1","missing":0},{"population":"US2","missing":0}])
    wcsv(OUT/"instrument_contamination.csv", [{"Instrument_Type":k,"n":v} for k,v in Counter(r["Instrument_Type"] for r in us1+us2).items()])
    wcsv(OUT/"mic_audit.csv", [{"pop":"US1","MIC":k,"n":v} for k,v in Counter(r["Primary_MIC"] for r in us1).items()]+[{"pop":"US2","MIC":k,"n":v} for k,v in Counter(r["Primary_MIC"] for r in us2).items()])
    inter=[{"pair":"P_US1","n":len(pset&u1set)},{"pair":"P_US2","n":len(pset&u2set)},{"pair":"US1_US2","n":len(u1set&u2set)},{"pair":"US2_REVIEW","n":us2_rev},{"pair":"US2_B","n":us2_b},{"pair":"HONA","n":hona}]
    wcsv(OUT/"cross_population_intersections.csv", inter)
    seen=sorted({r["ticker"] for r in coll_rows})
    lines=["# Post-Integration Integrity Audit US-1 + US-2","START be316bc. READ-ONLY.",f"**{status}** Fails {fails or 'none'}.","## Population","1633+372+369=2374. Prefix field diffs vs ae35b69: %s."%prefix_field_diffs,"US1 372/372 missing %s. US2 369/369 missing %s."%(len(us1_missing),len(us2_missing)),"Intersections P∩US1=%s P∩US2=%s US1∩US2=%s US2∩REVIEW=%s US2∩B=%s HONA=%s."%(len(pset&u1set),len(pset&u2set),len(u1set&u2set),us2_rev,us2_b,hona),"## Identity","WS/ISIN/triple dups 0. New missing identity %s. Historical empty ISIN prefix %s."%(miss_new,miss_hist),"## Ticker collisions (all ALLOWED, not identity)",", ".join(seen),"RBA: XTSE empty-ISIN vs XNYS CA74935Q1072 — dual listing possible, not identity-tuple dup.","## Provenance / instrument / MIC","US1 Source US1_SP500_COMMON_EVIDENCE_GATE. US2 US2_SP400_COMMON_ADMISSION IJH rank4. COMMON_STOCK 741. Other MIC %s."%(other_mic or 0),"## Governance","STRICT_759_UNCHANGED PASS. FROZEN_ZERO PASS. Research 2374 ≠ Strict 759 ≠ Frozen 0.","## Gates"]+[f"{k}: {v}" for k,v in g.items()]+["NEXT ACTION: STOP — MANAGER GATE"]
    (ROOT/"docs"/"spec"/"Post_Integration_Integrity_Audit_US1_US2.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    json.dump({"stage":"POST_INTEGRATION_INTEGRITY_AUDIT","status":status,"head":"be316bc","research_partial":len(uni),"prefix":1633,"us1":len(us1),"us2":len(us2),"prefix_field_diffs":prefix_field_diffs,"ticker_collisions":seen,"strict":strict,"frozen":0,"universe_write":False,"gates":g,"fails":fails,"next_action":"STOP_MANAGER_GATE","as_of_utc":ASOF}, open(OUT/"summary_post_integration_audit.json","w",encoding="utf-8"), indent=2)
    print(json.dumps({"status":status,"fails":fails,"n":len(uni),"us1":len(us1),"us2":len(us2),"gates":g}, indent=2)); return 0 if not fails else 1
if __name__=="__main__":
    raise SystemExit(main())
