#!/usr/bin/env python3
import csv, json, hashlib, os, sys, urllib.request
from collections import Counter
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __file__.endswith("mapping_price_verification_v0_43.py") else os.getcwd()
CFG = os.path.join(ROOT, "config", "mapping_evidence_acquisition_v0.42.csv")
OUT = os.path.join(ROOT, "output_mapping_price_verification_v0_43")
FIELDS = ["WS_ID","Proposed_Yahoo_Symbol","Primary_MIC","Primary_Currency","Quote_Currency","Currency_Match","Quote_Last","Quote_Exchange","Instrument_Type","Quote_Name","Probe_Status","Probe_AsOf_UTC","Notes"]
def sha(p):
    with open(p,"rb") as f: return hashlib.sha256(f.read()).hexdigest()
def probe(sym):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/"+sym+"?range=5d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r: d = json.load(r)
    res = d.get("chart",{}).get("result") or []
    if not res: raise RuntimeError("NO_RESULT")
    m = res[0]["meta"]
    q = ((res[0].get("indicators") or {}).get("quote") or [{}])[0]
    last = next((c for c in reversed(q.get("close") or []) if c is not None), None)
    return {"ccy": m.get("currency") or "","exch": m.get("exchangeName") or "","inst": m.get("instrumentType") or "","name": (m.get("shortName") or m.get("longName") or "")[:80],"last": last}
def ccy_match(frozen, quote):
    if frozen == quote: return "EXACT"
    if frozen == "GBP" and quote == "GBp": return "GBP_PENCE_EQUIVALENT"
    return "MISMATCH"
def main():
    before = sha(CFG)
    with open(CFG, encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
    if len(rows) != 239: raise SystemExit("expected 239")
    if any(r.get("Evidence_Confidence") != "HIGH" for r in rows): raise SystemExit("non-HIGH")
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for r in rows:
        rec = {k:"" for k in FIELDS}
        rec["WS_ID"]=r["WS_ID"]; rec["Proposed_Yahoo_Symbol"]=r["Proposed_Yahoo_Symbol"]
        rec["Primary_MIC"]=r["Primary_MIC"]; rec["Primary_Currency"]=r["Primary_Currency"]; rec["Probe_AsOf_UTC"]=asof
        try:
            p = probe(r["Proposed_Yahoo_Symbol"])
            rec["Quote_Currency"]=p["ccy"]; rec["Quote_Exchange"]=p["exch"]; rec["Instrument_Type"]=p["inst"]
            rec["Quote_Name"]=p["name"]; rec["Quote_Last"]="" if p["last"] is None else str(p["last"])
            rec["Currency_Match"]=ccy_match(r["Primary_Currency"], p["ccy"])
            if p["last"] is None: rec["Probe_Status"]="FAIL_DEAD"
            elif p["inst"] and p["inst"]!="EQUITY": rec["Probe_Status"]="FAIL_NOT_EQUITY"
            elif rec["Currency_Match"]=="MISMATCH": rec["Probe_Status"]="FAIL_CCY"
            else: rec["Probe_Status"]="PASS"
            if rec["Currency_Match"]=="GBP_PENCE_EQUIVALENT": rec["Notes"]="Yahoo LSE GBp pence vs frozen GBP; treated equivalent."
        except Exception as e:
            rec["Probe_Status"]="FAIL_DEAD"; rec["Notes"]=type(e).__name__+":"+str(e)[:120]
        out.append(rec)
        print(rec["Probe_Status"], rec["Proposed_Yahoo_Symbol"], rec["Currency_Match"] or "-")
    if sha(CFG)!=before: raise SystemExit("v0.42 csv mutated")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT,"price_verification_239_v0.43.csv"),"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(out)
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_PRICE_VERIFICATION","version":"v0.43","run_mode":"PRICE_VERIFICATION_SIDECAR_ONLY","status":"COMPLETE" if all(r["Probe_Status"]=="PASS" for r in out) else "FAIL","evidence_rows":239,"probe_rows":len(out),"probe_status_counts":dict(Counter(r["Probe_Status"] for r in out)),"currency_match_counts":dict(Counter(r["Currency_Match"] for r in out)),"source_evidence_sha256":before,"universe_mutated":False,"eligibility_promoted":False,"price_download":False,"productive":False,"mapping_applied":False,"v0_42_csv_mutated":False,"as_of_utc":asof}
    json.dump(summary, open(os.path.join(OUT,"summary_v0.43.json"),"w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"]=="COMPLETE" else 1
if __name__=="__main__": sys.exit(main())
