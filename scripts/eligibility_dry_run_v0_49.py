#!/usr/bin/env python3
import csv, json, hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT/"universe"/"research_partial_1633.csv"
LIQ = ROOT/"output_liquidity_fx_sidecar_236_v0_48"/"liquidity_236_v0.48.csv"
EV = ROOT/"config"/"mapping_evidence_acquisition_v0.42.csv"
QA = ROOT/"output_history_download_applied_239_v0_47"/"history_qa_239_v0.47.csv"
OUT = ROOT/"output_eligibility_dry_run_v0_49"
PREF_TOKS=("preferred","preference","vorzug","participation","genussschein","sdb")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inst_bucket(txt):
    t=(txt or "").lower()
    if any(x in t for x in PREF_TOKS): return "NON_ORDINARY_REVIEW"
    if not t.strip(): return "UNKNOWN"
    return "ORDINARY_LIKE"
def main():
    uni_sha=sha(UNI)
    liq=list(csv.DictReader(open(LIQ,encoding="utf-8")))
    if len(liq)!=236: raise SystemExit("liq")
    ev={r["WS_ID"]:r for r in csv.DictReader(open(EV,encoding="utf-8-sig"))}
    parked=[r for r in csv.DictReader(open(QA,encoding="utf-8")) if r.get("History_QA")!="PASS_HISTORY"]
    rows=[]
    for r in liq:
        share=(ev.get(r["WS_ID"]) or {}).get("Verified_Share_Class") or ""
        ib=inst_bucket(share); klass=r["Liquidity_Class"]
        if klass=="FAIL_LIQ": dry="FAIL_LIQUIDITY"
        elif klass=="LOW_EXCEPTION": dry="EXCEPTION_POOL"
        elif klass in ("PREFERRED","STANDARD") and ib=="ORDINARY_LIKE": dry="PASS_STRICT_CANDIDATE"
        elif klass in ("PREFERRED","STANDARD"): dry="INSTRUMENT_REVIEW"
        else: dry="HOLD"
        rows.append({"WS_ID":r["WS_ID"],"Yahoo_Symbol":r["Yahoo_Symbol"],"Name":r.get("Name",""),"Primary_MIC":r["Primary_MIC"],"Liquidity_Class":klass,"MedianTurnover20_EUR":r.get("MedianTurnover20_EUR",""),"Verified_Share_Class":share,"Instrument_Bucket":ib,"Eligibility_DryRun":dry,"Universe_Write":"NO"})
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"eligibility_dry_run_236_v0.49.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(OUT/"parked_history_3_v0.49.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=["WS_ID","Yahoo_Symbol","Eligibility_DryRun","Universe_Write"]); w.writeheader()
        for r in parked: w.writerow({"WS_ID":r["WS_ID"],"Yahoo_Symbol":r["Yahoo_Symbol"],"Eligibility_DryRun":"PARKED_HISTORY","Universe_Write":"NO"})
    if sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    cnt=Counter(r["Eligibility_DryRun"] for r in rows)
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_DRY_RUN","version":"v0.49","run_mode":"ELIGIBILITY_DRY_RUN_ONLY","status":"COMPLETE","sidecar_rows":len(rows),"parked_history":len(parked),"dry_run_counts":dict(cnt),"universe_mutated":False,"universe_status_written":False,"eligibility_promoted":False,"u3k_frozen_mutated":False,"mapping_status_flipped":False,"productive":False,"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_v0.49.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
