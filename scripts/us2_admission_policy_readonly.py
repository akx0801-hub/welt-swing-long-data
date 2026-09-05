#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
OUT=ROOT/"output_us2_admission_policy"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
REPORT=r'''# US-2 Admission Policy (Read-Only)
START HEAD 3b9ed92. Architecture only.
NO DOWNLOAD. NO BUILD. NO UNIVERSE WRITE.
MANAGER APPROVAL REQUIRED FOR US-2 BUILD.
## 1. Scope
US-2 = future additional US Primary Common on XNYS/XNAS outside closed US-1.
No candidates, no download. US-1 372/26 B/104 REVIEW/HONA not reopened.
Out: CA UNKNOWN AU KR A1 P6 Strict Freeze.
## 2. US Primary
Common/ordinary on XNYS or XNAS. US issuer != US Primary. ADR != US Primary.
ARCX/BATS/IEX/OTC/Pink not US-2. Ticker is never identity.
## 3. Instrument matrix
COMMON/ORDINARY: ADMIT if US Primary + identity + not ADR.
PREFERRED: DISCOVER, never scan default.
REIT/BDC/LP/MLP: REVIEW fail-closed, not ADMIT.
ETF/FUND/UNIT/WARRANT/RIGHT/SPAC: EXCLUDE.
ADR/ADS: EXCLUDE as US Primary. OTHER: REVIEW/EXCLUDE. No v7.2 broaden.
## 4. REIT
REVIEW only. Not ordinary, not written in US-2. Trusts != canonical common scan.
Later REIT policy is not US-2. Do not modify REIT rows.
## 5. ADR
EXCLUDE. MIC XNYS/XNAS does not make ADR primary. No ticker-only, no ISIN fallback.
## 6. Preferred
DISCOVER. Common exists -> scan common. Pref-only -> REVIEW.
## 7. Multi-class
Discover A/B separately. Canonical: one common per issuer x MIC.
Tie-break only in a later build: turnover then index else REVIEW.
## 8. Dual-listing
No MIC-merge, no name-merge. US+CA ticker collisions are not identity dups.
Identity = ISIN + Primary MIC + Primary Ticker.
## 9. Identity
No CUSIP-for-ISIN, no Yahoo-as-key. Missing ISIN/MIC = FAIL. Dup triple = FAIL.
Ticker collision different ISIN/MIC = allowed. WS:MIC:TICKER, no overwrite of US-1.
Exclude 372, 26 B ISINs, HONA US43849R1059.
## 10. Evidence
1 official index 2 exchange directory 3 issuer/SEC 4 institutional named-index file
5 secondary 6 discovery-only (never ADMIT). Conflict with higher rank = REVIEW.
Membership needs rank 1 or 4. Wikipedia alone is not enough.
## 11. Mapping
Identity -> Evidence -> Provider Mapping. Probe only after ADMIT + tuple + rank<=4.
Max 2 retries then FAIL. No mapping now.
## 12-13. History / Liquidity (not run, not relaxed)
260/252/18-20, no future/dup bars.
Turnover EUR: >=20m PREFERRED, 15-20 STANDARD, 5-15 REVIEW, <5 FAIL.
## 14. Canonical pipeline
Discovery->Admission->Evidence->Identity->Mapping->History->Liquidity->Eligibility Dry-Run->Manager Gate->Write.
No auto step. No Tier-1=759. No auto-Strict. No freeze.
## 15. Future build prerequisites (NOT this task)
Separate manager order. Bounded slice, not all NYSE/Nasdaq.
IF later authorized: S&P MidCap 400 Common XNYS/XNAS, disjoint from US-1 372/B-26/HONA.
Russell 1000 minus US-1 only with extra order. Sidecar output_us2/. No append to 2005.
## 16-17. Exclusions / fail-closed
372, 26 B, 104, HONA, CA, UNKNOWN, AU, KR, ADR/ETF as scan, REIT as ADMIT, no-ISIN.
Unclear = REVIEW/EXCLUDE. No mass-admit. STOP do not repair.
## 18.
US-2 ADMISSION POLICY — READ-ONLY COMPLETE
NO DOWNLOAD
NO BUILD
NO UNIVERSE WRITE
MANAGER APPROVAL REQUIRED FOR US-2 BUILD
NEXT ACTION: STOP — MANAGER GATE
'''
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def main():
    uni_sha=sha(UNI); fro_sha=sha(FROZEN)
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("3b9ed92"): raise SystemExit("STOP STATE MISMATCH head %s"%head)
    uni=rcsv(UNI); elig=rcsv(ELIG)
    n=len(uni); us=sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})
    st=sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")
    fr=sum(1 for _ in open(FROZEN,encoding="utf-8"))
    if n!=2005 or us!=372 or st!=759 or fr!=1: raise SystemExit("STOP counts %s %s %s %s"%(n,us,st,fr))
    if any(r["Primary_Ticker"]=="HONA" for r in uni): raise SystemExit("STOP HONA")
    if (ROOT/"output_us2").exists() and any(ROOT.joinpath("output_us2").glob("*.csv")): raise SystemExit("STOP UNAUTHORIZED CHANGE us2 csv")
    summary={"stage":"US2_ADMISSION_POLICY_READONLY","status":"US-2 ADMISSION POLICY — READ-ONLY COMPLETE","head":head,"research_partial":n,"us1":us,"strict":st,"frozen":0,"universe_write":False,"download":False,"build":False,"recommended_first_slice_if_later_authorized":"SP400_MIDCAP_COMMON_XNYS_XNAS_DISJOINT_US1","reit":"REVIEW_FAIL_CLOSED","adr":"EXCLUDE","ready_means":"policy_only_not_build","next_action":"STOP_MANAGER_GATE","as_of_utc":ASOF}
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(summary, open(OUT/"summary_us2_admission_policy.json","w",encoding="utf-8"), indent=2)
    (ROOT/"docs"/"spec"/"US2_Admission_Policy_ReadOnly.md").write_text(REPORT, encoding="utf-8")
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("STOP UNAUTHORIZED CHANGE")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
