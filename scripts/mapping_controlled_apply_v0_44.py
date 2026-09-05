#!/usr/bin/env python3
import csv, json, hashlib, os, sys
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "config", "mapping_evidence_acquisition_v0.42.csv")
UNI = os.path.join(ROOT, "universe", "research_partial_1633.csv")
SIDE = os.path.join(ROOT, "output_mapping_price_verification_v0_43", "price_verification_239_v0.43.csv")
OUT = os.path.join(ROOT, "output_mapping_controlled_apply_v0_44")
FROZEN = ["WS_ID","ISIN","Name","Instrument_Type","Country","Primary_Ticker","Primary_Exchange","Primary_MIC","Primary_Currency","Alpha_Symbol","Share_Class"]
def sha(p):
    with open(p,"rb") as f: return hashlib.sha256(f.read()).hexdigest()
def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f); return r.fieldnames, list(r)
def main():
    ev_sha, uni_sha = sha(EV), sha(UNI)
    fields, uni = load(UNI); _, ev = load(EV); _, side = load(SIDE)
    if len(uni)!=1633 or len(ev)!=239: raise SystemExit("rowcount")
    if any(r.get("Evidence_Confidence")!="HIGH" for r in ev): raise SystemExit("non-HIGH")
    if any(r.get("Decision")!="CONFIRMED_PROVIDER_SYMBOL_CANDIDATE" for r in ev): raise SystemExit("decision")
    sby = {r["WS_ID"]: r for r in side}
    if len(sby)!=239 or any(r.get("Probe_Status")!="PASS" for r in side): raise SystemExit("sidecar")
    props = [(r.get("Proposed_Yahoo_Symbol") or "").strip() for r in ev]
    if any(not s for s in props) or len(set(props))!=239: raise SystemExit("proposed")
    uby = {r["WS_ID"]: r for r in uni}
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frozen0 = {r["WS_ID"]: {k: r.get(k) for k in FROZEN} for r in uni}
    log=[]; filled=0
    for r in ev:
        u = uby.get(r["WS_ID"])
        if u is None: raise SystemExit("missing "+r["WS_ID"])
        if (u.get("Yahoo_Symbol") or "").strip(): raise SystemExit("yahoo set "+r["WS_ID"])
        if u.get("Mapping_Status")!="UNMAPPED": raise SystemExit("not UNMAPPED "+r["WS_ID"])
        old_y, old_m = u.get("Yahoo_Symbol") or "", u.get("Mapping_Status")
        u["Yahoo_Symbol"]=r["Proposed_Yahoo_Symbol"]
        u["Mapping_Status"]="EVIDENCE_CANDIDATE_APPLIED"
        u["Last_Validated"]=asof
        filled += 1
        log.append({"WS_ID":r["WS_ID"],"Name":u.get("Name"),"Primary_Ticker":u.get("Primary_Ticker"),"Old_Yahoo_Symbol":old_y,"New_Yahoo_Symbol":u["Yahoo_Symbol"],"Old_Mapping_Status":old_m,"New_Mapping_Status":u["Mapping_Status"]})
    if filled!=239: raise SystemExit("fill")
    for r in uni:
        if frozen0[r["WS_ID"]]!={k:r.get(k) for k in FROZEN}: raise SystemExit("frozen "+r["WS_ID"])
    os.makedirs(OUT, exist_ok=True)
    with open(UNI,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(uni)
    with open(os.path.join(OUT,"apply_log_239_v0.44.csv"),"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(log[0].keys())); w.writeheader(); w.writerows(log)
    _, uni2 = load(UNI)
    if len(uni2)!=1633: raise SystemExit("post n")
    applied=[r for r in uni2 if r.get("Mapping_Status")=="EVIDENCE_CANDIDATE_APPLIED"]
    if len(applied)!=239: raise SystemExit("post applied")
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_MAPPING_APPLY","version":"v0.44","run_mode":"CONTROLLED_MAPPING_APPLY","status":"COMPLETE","universe_rows":1633,"applied_rows":239,"untouched_rows":1394,"mapping_status_applied":"EVIDENCE_CANDIDATE_APPLIED","yfinance_verified_set":False,"identity_frozen":True,"evidence_sha256_before":ev_sha,"universe_sha256_before":uni_sha,"universe_sha256_after":sha(UNI),"evidence_sha256_after":sha(EV),"v0_42_csv_mutated":sha(EV)!=ev_sha,"eligibility_promoted":False,"price_download":False,"productive":False,"as_of_utc":asof}
    json.dump(summary, open(os.path.join(OUT,"summary_v0.44.json"),"w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__": sys.exit(main())
