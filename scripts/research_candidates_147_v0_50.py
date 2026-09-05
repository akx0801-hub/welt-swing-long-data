#!/usr/bin/env python3
import csv, json, hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT/"universe"/"research_partial_1633.csv"
DRY = ROOT/"output_eligibility_dry_run_v0_49"/"eligibility_dry_run_236_v0.49.csv"
OUT = ROOT/"output_research_candidates_147_v0_50"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    uni_sha=sha(UNI)
    dry=list(csv.DictReader(open(DRY, encoding="utf-8")))
    cand=sorted([r for r in dry if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE"], key=lambda r: (r["Primary_MIC"], r["Yahoo_Symbol"]))
    held=[r for r in dry if r["Eligibility_DryRun"]!="PASS_STRICT_CANDIDATE"]
    if len(cand)!=147: raise SystemExit("cand")
    OUT.mkdir(parents=True, exist_ok=True)
    fields=["WS_ID","Yahoo_Symbol","Name","Primary_MIC","Liquidity_Class","MedianTurnover20_EUR","Verified_Share_Class","Instrument_Bucket","Eligibility_DryRun","Universe_Write"]
    with open(OUT/"research_candidates_147_v0.50.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(cand)
    with open(OUT/"held_out_89_v0.50.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=["WS_ID","Yahoo_Symbol","Eligibility_DryRun","Liquidity_Class"], extrasaction="ignore"); w.writeheader(); w.writerows(held)
    if sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_RESEARCH_CANDIDATES_147","version":"v0.50","run_mode":"RESEARCH_CANDIDATE_LIST_ONLY","status":"COMPLETE","candidate_rows":147,"held_out_rows":len(held),"mic_counts":dict(Counter(r["Primary_MIC"] for r in cand)),"liq_counts":dict(Counter(r["Liquidity_Class"] for r in cand)),"universe_mutated":False,"u3k_frozen_mutated":False,"eligibility_promoted":False,"productive":False,"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_v0.50.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
