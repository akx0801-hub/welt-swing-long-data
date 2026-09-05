#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
CAND=ROOT/"output_us1_integration_gate"/"US1_INTEGRATION_CANDIDATES.csv"
AUD=ROOT/"docs"/"spec"/"US1_Post_Integration_Integrity_Audit.md"
OUT=ROOT/"output_us1_manager_gate"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
REPORT=r'''# US-1 CLOSED -> Manager Gate for Next Segment
START HEAD 1b64717. READ-ONLY. NO BUILD EXECUTED.
MANAGER APPROVAL REQUIRED FOR ANY NEXT SEGMENT.
## 1. Starting HEAD
1b64717 on write 122a581. Verified: 2005 / US-1 372 / Strict 759 / Frozen 0.
## 2. US-1 closure
CLOSED. 372/372 Class-A. Prefix 1633 unchanged. B=0 HONA=0 dups=0. Leftovers 26+104+HONA fail-closed, not next segment.
## 3. Research Partial
2005=1633+372. US_SP500 372/0 not Strict. CA 217/0 no ISIN. AU/KR 0. Toward \~3000 still open.
## 4-5. Strict 759 Frozen 0. Integrity PASS. Read-only.
## 6. Architecture
P5.0 B workbench. P5.1 US Primary=Common XNYS/XNAS, ISIN+MIC+Ticker. 2005 is Stage not U3K. 759 is not Tier-1. US-1 closed S&P500 Common only.
## 7-8. Matrix
US-2 rest of US Primary: CONDITIONAL (high coverage, evidence unspecified).
US-1 leftovers: DO NOT TOUCH YET.
Canada: NOT READY (0 ISIN).
UNKNOWN 686: DO NOT TOUCH YET.
HK/EU/BR: NOT READY.
AU/KR: NOT READY.
A1 15 REVIEW: CONDITIONAL not coverage.
READY FOR SEPARATE BUILD ORDER: none.
## 9. Recommended
B READ-ONLY ARCHITECTURE AUDIT = US-2 Admission Policy (P5.1-style, no download).
Not A: no source/carve-out/evidence rank for non-S&P.
Not C: coverage path remains US Primary.
If later authorized: sidecar then manager write gate. Not a dump onto 2005.
## 10.
NO BUILD EXECUTED.
MANAGER APPROVAL REQUIRED FOR ANY NEXT SEGMENT.
STATUS: MANAGER GATE — NO NEXT SEGMENT EXECUTED
'''
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def main():
    uni_sha=sha(UNI); fro_sha=sha(FROZEN)
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("1b64717"): raise SystemExit("STOP STATE MISMATCH head %s"%head)
    if not AUD.exists(): raise SystemExit("STOP audit report missing")
    uni=rcsv(UNI); elig=rcsv(ELIG); cands=rcsv(CAND)
    if len(uni)!=2005: raise SystemExit("STOP uni")
    if sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})!=372: raise SystemExit("STOP us")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("STOP strict")
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP frozen")
    if len(cands)!=372: raise SystemExit("STOP cands")
    if any(r["Primary_Ticker"]=="HONA" or r["Yahoo_Symbol"]=="HONA" for r in uni): raise SystemExit("STOP HONA")
    if sum(1 for r in uni[:1633] if r["Primary_MIC"] in {"XNYS","XNAS"})!=0: raise SystemExit("STOP prefix")
    summary={"stage":"US1_MANAGER_GATE_NEXT_SEGMENT","status":"MANAGER_GATE_NO_NEXT_SEGMENT_EXECUTED","head":head,"research_partial":2005,"us1":372,"strict":759,"frozen":0,"universe_write":False,"us1_closed":True,"recommended":"B_READ_ONLY_US2_ADMISSION_POLICY","ready_for_build":"NONE","next_action":"STOP_MANAGER_GATE","as_of_utc":ASOF}
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(summary, open(OUT/"summary_manager_gate.json","w",encoding="utf-8"), indent=2)
    (ROOT/"docs"/"spec"/"US1_Manager_Gate_Next_Segment.md").write_text(REPORT, encoding="utf-8")
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("mutation")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
