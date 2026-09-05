#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from price_cache import FreeDataConfig, SQLitePriceCache, YFinanceBatchClient, YFinancePriceCacheRunner
UNI = ROOT / "universe" / "research_partial_1633.csv"
EV = ROOT / "config" / "mapping_evidence_acquisition_v0.42.csv"
OUT = ROOT / "output_history_download_applied_239_v0_47"
CACHE = ROOT / "runtime_cache" / "applied_239_history_v0_47.sqlite"
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    uni_sha, ev_sha = sha(UNI), sha(EV)
    with open(UNI, encoding="utf-8-sig", newline="") as f:
        uni = list(csv.DictReader(f))
    if len(uni) != 1633: raise SystemExit("universe rowcount")
    rows = [r for r in uni if r.get("Mapping_Status") == "EVIDENCE_CANDIDATE_APPLIED"]
    if len(rows) != 239: raise SystemExit("applied")
    import pandas as pd
    df = pd.DataFrame(rows)
    as_of = date.today() - timedelta(days=1)
    cfg = FreeDataConfig(batch_size=100, pause_between_batches_seconds=1.0, timeout_seconds=30.0)
    cache = SQLitePriceCache(CACHE)
    runner = YFinancePriceCacheRunner(cache, YFinanceBatchClient(config=cfg), config=cfg)
    result = runner.run_initial(df, as_of=as_of)
    states = list(cache.conn.execute("SELECT ws_id,yahoo_symbol,status,reason_code,unique_bars,valid_bars,first_bar_date,last_bar_date,last_error FROM cache_state"))
    cache.close()
    by = {r["WS_ID"]: r for r in rows}
    sidecar = []
    for ws, sym, st, reason, ub, vb, first, last, err in states:
        u = by.get(ws, {})
        hist = "PASS_HISTORY" if st == "READY" else "FAIL_HISTORY"
        sidecar.append({"WS_ID":ws,"Yahoo_Symbol":sym,"Primary_MIC":u.get("Primary_MIC",""),"Primary_Currency":u.get("Primary_Currency",""),"Cache_Status":st,"History_QA":hist,"Reason":reason or "","Unique_Bars":ub,"Valid_Bars":vb,"First_Bar":first or "","Last_Bar":last or "","Scale_Rule":"GBP_PENCE_EQUIVALENT" if u.get("Primary_MIC")=="XLON" else "NONE","Last_Error":err or ""})
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "history_qa_239_v0.47.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sidecar[0].keys())); w.writeheader(); w.writerows(sidecar)
    if sha(UNI) != uni_sha or sha(EV) != ev_sha: raise SystemExit("identity mutated")
    qa, stc = Counter(r["History_QA"] for r in sidecar), Counter(r["Cache_Status"] for r in sidecar)
    summary = {"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_HISTORY_DOWNLOAD_APPLIED_239","version":"v0.47","run_mode":"HISTORY_DOWNLOAD_APPLIED_239_ONLY","status":"COMPLETE","applied_rows":239,"sidecar_rows":len(sidecar),"history_qa_counts":dict(qa),"cache_status_counts":dict(stc),"pass_history":qa.get("PASS_HISTORY",0),"as_of":as_of.isoformat(),"sqlite_gitignored":True,"universe_mutated":False,"eligibility_promoted":False,"mapping_status_flipped":False,"productive":False,"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT / "summary_v0.47.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__ == "__main__":
    raise SystemExit(main())
