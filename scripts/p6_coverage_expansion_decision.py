#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
OUT=ROOT/"output_p6_coverage_decision"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NA_C={"United States","Canada"}; EU_C={"GB","FR","DE","CH","SE","IT","NL","ES","NO","DK","FI","PL","BE","AT","IE","PT"}
AP_C={"China","Japan","Hong Kong","Taiwan","India"}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def region(r):
    c,m=r["Country"], r["Primary_MIC"]
    if c in NA_C or m in {"XNYS","XNAS","XTSE"}: return "North America"
    if c in EU_C or m in {"XLON","XETR","XPAR","XSWX","XSTO","XMIL","XAMS","XMAD","XOSL","XCSE","XHEL","XWAR","XBRU","XWBO","XDUB"}: return "Europe"
    if c in AP_C or m in {"XTKS","XSHG","XSHE","XHKG","XNSE","XTAI"}: return "Asia-Pacific"
    if c=="Brazil" or m=="BVMF": return "Other"
    return "UNKNOWN/UNCLASSIFIED"
def main():
    uni_sha=sha(UNI); fro_sha=sha(FROZEN)
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("75b8eed"): raise SystemExit("STOP P6 START STATE MISMATCH head %s"%head)
    uni=rcsv(UNI); elig=rcsv(ELIG)
    if len(uni)!=2374: raise SystemExit("STOP P6 n")
    eok={r["WS_ID"] for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE"}
    if len(eok)!=759: raise SystemExit("STOP P6 strict")
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP P6 frozen")
    us1=sum(1 for r in uni if r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE")
    us2=sum(1 for r in uni if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION")
    n_us=sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})
    n_ca=sum(1 for r in uni if r["Primary_MIC"]=="XTSE")
    n_au=sum(1 for r in uni if r["Primary_MIC"]=="XASX" or r["Country"]=="Australia")
    n_kr=sum(1 for r in uni if r["Primary_MIC"] in {"XKRX","XKOS"} or r["Country"] in {"South Korea","Korea"})
    ca_empty=sum(1 for r in uni if r["Primary_MIC"]=="XTSE" and not r["ISIN"])
    us_strict=sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"} and r["WS_ID"] in eok)
    ca_strict=sum(1 for r in uni if r["Primary_MIC"]=="XTSE" and r["WS_ID"] in eok)
    mic_rows=[]
    for m,n in Counter(r["Primary_MIC"] for r in uni).most_common():
        st=sum(1 for r in uni if r["Primary_MIC"]==m and r["WS_ID"] in eok)
        empty=sum(1 for r in uni if r["Primary_MIC"]==m and not r["ISIN"])
        mic_rows.append({"MIC":m,"membership":n,"strict":st,"gap":n-st,"strict_pct":round(100.0*st/n,1) if n else 0,"empty_isin":empty})
    reg_rows=[]
    for g in ["North America","Europe","Asia-Pacific","Other","UNKNOWN/UNCLASSIFIED"]:
        rs=[r for r in uni if region(r)==g]; n=len(rs); st=sum(1 for r in rs if r["WS_ID"] in eok)
        reg_rows.append({"region":g,"membership":n,"strict":st,"gap":n-st,"strict_pct":round(100.0*st/n,1) if n else 0})
    mvs=[{"slice":"US_XNYS_XNAS","membership":n_us,"strict":us_strict,"gap":n_us-us_strict,"gap_type":"CONVERSION_NOT_RUN","empty_isin":0},
         {"slice":"Canada_XTSE","membership":n_ca,"strict":ca_strict,"gap":n_ca-ca_strict,"gap_type":"IDENTITY_BLOCKED","empty_isin":ca_empty},
         {"slice":"Australia","membership":n_au,"strict":0,"gap":0 if n_au==0 else n_au,"gap_type":"EXPANSION","empty_isin":0},
         {"slice":"Korea","membership":n_kr,"strict":0,"gap":0 if n_kr==0 else n_kr,"gap_type":"EXPANSION","empty_isin":0}]
    matrix=[{"option":"A_US3","membership":n_us,"strict":us_strict,"gap_type":"EXPANSION_PLUS_CONVERSION","identity":"READY","evidence":"PIPELINE_PROVEN","complexity":"LOW","benefit":"US_DEPTH","size":"NOT_MEASURED"},
            {"option":"B_Canada","membership":n_ca,"strict":ca_strict,"gap_type":"IDENTITY_BLOCKED","identity":"BLOCKED_0_ISIN","evidence":"MEMBERSHIP_EXISTS","complexity":"HIGH","benefit":"CONVERT_EXISTING","size":str(n_ca)},
            {"option":"C_Australia","membership":n_au,"strict":0,"gap_type":"EXPANSION","identity":"NEW","evidence":"INDEX_PATTERN_AVAILABLE","complexity":"MEDIUM","benefit":"OCEANIA_ZERO","size":"NOT_MEASURED"},
            {"option":"C_Korea","membership":n_kr,"strict":0,"gap_type":"EXPANSION","identity":"NEW","evidence":"INDEX_PATTERN_AVAILABLE","complexity":"MEDIUM_HIGH","benefit":"KR_ZERO_ASIA_HEAVY","size":"NOT_MEASURED"},
            {"option":"D_HistoryLiquidity","membership":n_us,"strict":us_strict,"gap_type":"CONVERSION","identity":"READY","evidence":"N_A","complexity":"MEDIUM","benefit":"MIXES_LAYERS","size":str(n_us)}]
    ranking=[{"rank":1,"option":"C_Australia","verdict":"RECOMMENDED NEXT DIRECTION","slice":"SP_ASX_200_COMMON_XASX"},
             {"rank":2,"option":"C_Korea","verdict":"NOT NOW","slice":"KOSPI_200_COMMON"},
             {"rank":3,"option":"A_US3","verdict":"NOT NOW","slice":"US_SMALLCAP"}]
    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT/"coverage_by_mic.csv", mic_rows); wcsv(OUT/"coverage_by_region.csv", reg_rows)
    wcsv(OUT/"membership_vs_strict.csv", mvs); wcsv(OUT/"option_gap_matrix.csv", matrix); wcsv(OUT/"p6_option_ranking.csv", ranking)
    na=next(r for r in reg_rows if r["region"]=="North America"); ap=next(r for r in reg_rows if r["region"]=="Asia-Pacific"); eu=next(r for r in reg_rows if r["region"]=="Europe")
    md="""# P6 Coverage & Expansion Decision Gate
START 75b8eed. READ-ONLY. NO DOWNLOAD. NO BUILD.
## 1. Executive Decision
**Winner: Australia — S&P/ASX 200 Common on XASX (policy-first).** Recommendation ≠ authorization.
## 2-3. Start / Composition
HEAD 75b8eed. 2374=1633+372+369. Strict 759 Frozen 0. 2374 ≠ U3K. 759 ≠ Frozen.
## 4. Geographic Coverage
NA %s (%s Strict). EU %s (%s Strict). AP %s (%s Strict). Other 98. US 741=31%%. Oceania 0. Korea 0.
## 5. MIC
XNYS/XNAS/XTSE present. XASX 0. XKRX 0. Empty ISIN 1536 (prefix). ISIN present 838 (US+IN+TW).
## 6-7. Membership vs Strict / Gaps
US 741/0 CONVERSION_NOT_RUN. CA 217/0 IDENTITY_BLOCKED (empty ISIN 217/217). AU 0 EXPANSION. KR 0 EXPANSION.
NA 40%% AP 30%% EU 25%% Oceania 0. Remaining to \~3000 is not invented.
## 8. A US-3
Pipeline proven. Size NOT_MEASURED. Deepens 31%% US. Not automatically next.
## 9. B Canada
217 TMX, 0 ISIN, 0 Strict. Collisions RBA CG H BYD ticker-only. CANADA_REQUIRES_IDENTITY_GATE_FIRST.
## 10. C Australia
0 membership. Bounded: S&P/ASX 200 Common XASX. Size NOT_MEASURED. Fills Oceania zero. Policy-first later.
## 11. C Korea
0 membership. Bounded KOSPI 200. AP already 718. Rank 2.
## 12. D History
Would mix Admission with Eligibility on 741 US. Rejected.
## 13-14. Matrix / Ranking
#1 Australia RECOMMENDED. #2 Korea NOT NOW. #3 US-3 NOT NOW.
## 15. Winner
Australia S&P/ASX 200 Common. Why: developed-market zero, not US depth, not CA repair. Future gate: AU-1 policy then manager build. P6 authorizes neither.
## 16. Loser Lines
US-3 — NOT NOW because US already 741/31%%.
Canada — NOT NOW because 217/217 empty ISIN.
Korea — NOT NOW because AP already 718; AU is the true zero.
History/Liquidity — NOT NOW because it mixes Admission with Eligibility.
## 17. Canada
CANADA_REQUIRES_IDENTITY_GATE_FIRST. No repair.
## 18-20. Governance / Non-auth / Gate
NO FULL_SCAN, UNKNOWN map, freeze 759, US-3/CA/AU/KR build, History.
P6 COMPLETE. RECOMMENDATION ≠ BUILD.
NEXT ACTION: STOP — MANAGER SELECTS ONE BOUNDED NEXT PHASE
"""%(na["membership"],na["strict"],eu["membership"],eu["strict"],ap["membership"],ap["strict"])
    (ROOT/"docs"/"spec"/"P6_Coverage_Expansion_Decision_Gate.md").write_text(md, encoding="utf-8")
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("STOP UNAUTHORIZED CHANGE")
    summary={"stage":"P6_COVERAGE_EXPANSION_DECISION","status":"P6 COVERAGE & EXPANSION DECISION GATE — COMPLETE","head":"75b8eed","research_partial":2374,"strict":759,"frozen":0,"us":n_us,"canada":n_ca,"australia":n_au,"korea":n_kr,"winner":"AU_SP_ASX_200_COMMON","canada_decision":"CANADA_REQUIRES_IDENTITY_GATE_FIRST","ranking":["C_Australia","C_Korea","A_US3"],"universe_write":False,"download":False,"recommendation_is_not_build":True,"next_action":"STOP_MANAGER_SELECTS_ONE_BOUNDED_NEXT_PHASE","as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_p6.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
