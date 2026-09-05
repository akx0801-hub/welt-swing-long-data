#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
OUT=ROOT/"output_au1_policy"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
MD="""# AU-1 Admission Policy (Read-Only)
START 386af4c. NO DOWNLOAD. NO BUILD. NO CANDIDATE LIST.
READY != BUILD AUTHORIZATION.
## Scope
S&P/ASX 200 Ordinary on XASX. Expansion, AU membership 0. Not ASX-full, not History.
## Evidence
R1 official S&P/ASX 200. R2 ASX/ASIC. R3 institutional index fund (no override of R1/R2). R4 Wikipedia never sole ADMIT.
Discovery != admission evidence.
## Identity
Mandatory ISIN + XASX + ticker. AUD required. No ticker-only. No ISIN fallback.
WS_ID later WS:XASX:TICKER. No overwrite.
## Instruments
Ordinary: ADMIT candidate. A-REIT: REVIEW. Stapled: REVIEW (stapled != common).
ETF/Fund: EXCLUDE. Preferred: DISCOVER. Other units: EXCLUDE. CDI/DR: EXCLUDE.
Foreign-incorp ASX ordinary: REVIEW (do not copy US-2 foreign-ISIN ADMIT).
## Dual / MIC
XASX only. No MIC-merge. Ticker collision other MIC allowed if identity differs.
## Buckets
DISCOVERY sidecar. ADMIT ordinary+XASX+ISIN+AUD+R1orR3. REVIEW REIT/stapled/identity. EXCLUDE ETF/CDI.
## Reuse / do not copy
Reuse: sidecar, buckets, identity triple, write-gate, fail-closed.
Do not copy: US REIT-as-afterthought, US foreign-ISIN ADMIT, US dual MIC.
## D1-D9
D1 YES. D2 XASX YES. D3 ordinary YES. D4 A-REIT REVIEW. D5 stapled REVIEW.
D6 ETF EXCLUDE. D7 CDI EXCLUDE. D8 ISIN+XASX+TICKER. D9 READY WITH CONDITIONS.
Conditions: separate manager order; R1 or R3; no Wikipedia-only; no REIT/stapled ADMIT.
## Gate
POLICY -> Manager -> Admission Build -> Evidence -> Manager -> Write -> Audit -> STOP.
AU-1 ADMISSION POLICY — READ-ONLY COMPLETE
NEXT ACTION: STOP — MANAGER GATE REQUIRED FOR AU-1 ADMISSION BUILD
"""
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def main():
    us,fs=sha(UNI),sha(FROZEN)
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("386af4c"): raise SystemExit("STOP head "+head)
    uni,elig=rcsv(UNI),rcsv(ELIG)
    n,us1,us2=len(uni),sum(1 for r in uni if r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE"),sum(1 for r in uni if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION")
    st=sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")
    au=sum(1 for r in uni if r["Primary_MIC"]=="XASX" or r["Country"]=="Australia")
    if n!=2374 or us1!=372 or us2!=369 or st!=759 or au!=0: raise SystemExit("STOP counts")
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP frozen")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"au1_policy_decision_matrix.csv","w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["decision","value"]); w.writerows([["D1","YES"],["D2","YES"],["D3","YES"],["D4","REVIEW"],["D5","REVIEW"],["D6","EXCLUDE"],["D7","EXCLUDE"],["D8","ISIN+XASX+TICKER"],["D9","READY_WITH_CONDITIONS"]])
    (ROOT/"docs"/"spec"/"AU1_Admission_Policy_ReadOnly.md").write_text(MD, encoding="utf-8")
    if sha(UNI)!=us or sha(FROZEN)!=fs: raise SystemExit("STOP UNAUTHORIZED CHANGE")
    s={"stage":"AU1_ADMISSION_POLICY_READONLY","status":"AU-1 ADMISSION POLICY — READ-ONLY COMPLETE","head":head,"research_partial":n,"strict":st,"frozen":0,"australia_membership":0,"d4":"REVIEW","d5":"REVIEW","d9":"READY_WITH_CONDITIONS","universe_write":False,"download":False,"build":False,"next_action":"STOP_MANAGER_GATE_REQUIRED_FOR_AU1_ADMISSION_BUILD","as_of_utc":ASOF}
    json.dump(s, open(OUT/"summary_au1_policy.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(s, indent=2))
if __name__=="__main__":
    main()
