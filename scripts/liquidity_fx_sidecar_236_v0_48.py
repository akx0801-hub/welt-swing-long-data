#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, sqlite3, sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from price_cache import FreeDataConfig, YFinanceBatchClient, split_download_frame, normalize_symbol_frame, technical_valid_mask
UNI = ROOT / "universe" / "research_partial_1633.csv"
QA = ROOT / "output_history_download_applied_239_v0_47" / "history_qa_239_v0.47.csv"
CACHE = ROOT / "runtime_cache" / "applied_239_history_v0_47.sqlite"
OUT = ROOT / "output_liquidity_fx_sidecar_236_v0_48"
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def classify(med, usable):
    if usable < 18 or med is None or (isinstance(med, float) and np.isnan(med)): return "INSUFFICIENT"
    if med >= 20_000_000: return "PREFERRED"
    if med >= 15_000_000: return "STANDARD"
    if med >= 5_000_000: return "LOW_EXCEPTION"
    return "FAIL_LIQ"
def fx_asof(frame, day, tol=10):
    if frame is None or frame.empty: return np.nan
    x = frame.loc[frame.index <= day]
    if x.empty: return np.nan
    if int((day - pd.Timestamp(x.index[-1])).days) > tol: return np.nan
    return float(x.iloc[-1]["FX_to_EUR"])
def main():
    if not CACHE.exists(): raise SystemExit("missing cache")
    uni_sha = sha(UNI)
    qa = list(csv.DictReader(open(QA, encoding="utf-8")))
    pass_rows = [r for r in qa if r.get("History_QA")=="PASS_HISTORY"]
    if len(pass_rows)!=236: raise SystemExit("pass")
    uni = {r["WS_ID"]: r for r in csv.DictReader(open(UNI, encoding="utf-8-sig"))}
    cutoff = date.today() - timedelta(days=1)
    need = sorted({(uni[r["WS_ID"]].get("Primary_Currency") or "").upper() for r in pass_rows} - {"EUR"})
    client = YFinanceBatchClient(config=FreeDataConfig(batch_size=max(1,len(need)), initial_period="2y", timeout_seconds=30.0))
    direct = [f"{c}EUR=X" for c in need]
    frames = split_download_frame(client.download(direct, period="2y", repair=False), direct)
    fx = {"EUR": pd.DataFrame({"FX_to_EUR":[1.0]}, index=pd.DatetimeIndex([pd.Timestamp(cutoff)]))}
    for c in need:
        ds = f"{c}EUR=X"
        if ds in frames and not normalize_symbol_frame(frames[ds]).empty:
            fr = normalize_symbol_frame(frames[ds])[["close"]].rename(columns={"close":"FX_to_EUR"})
            fx[c] = fr[fr.index.date <= cutoff]
    conn = sqlite3.connect(CACHE)
    sidecar=[]
    for r in pass_rows:
        u = uni[r["WS_ID"]]; ccy=(u.get("Primary_Currency") or "").upper()
        scale = 0.01 if u.get("Primary_MIC")=="XLON" else 1.0
        px = pd.read_sql_query("SELECT day,open,high,low,close,adj_close,volume,stock_splits FROM price_daily WHERE ws_id=? ORDER BY day", conn, params=[r["WS_ID"]])
        px["day"]=pd.to_datetime(px["day"]); px=px[px["day"].dt.date<=cutoff].copy()
        for c in ["open","high","low","close","adj_close","volume","stock_splits"]:
            px[c]=pd.to_numeric(px[c], errors="coerce")
        px["repaired"]=0; px=px.set_index("day")
        xv=px.loc[technical_valid_mask(px)].copy()
        xv["native"]=xv["close"]*xv["volume"]*scale
        xv.loc[(xv["close"]<=0)|(xv["volume"]<=0),"native"]=np.nan
        last20=xv.tail(20).copy()
        last20["eur"]=last20["native"]*(1.0 if ccy=="EUR" else last20.index.map(lambda i: fx_asof(fx.get(ccy), pd.Timestamp(i))))
        usable=int(last20["eur"].notna().sum()); med=float(last20["eur"].median()) if usable else float("nan")
        sidecar.append({"WS_ID":r["WS_ID"],"Yahoo_Symbol":r["Yahoo_Symbol"],"Name":u.get("Name",""),"Primary_MIC":u.get("Primary_MIC"),"Primary_Currency":ccy,"Scale":scale,"Usable20":usable,"MedianTurnover20_EUR":"" if np.isnan(med) else round(med,2),"Liquidity_Class":classify(None if np.isnan(med) else med, usable),"Liquidity_Status":"OK" if usable>=18 else "USABLE_SESSIONS_BELOW_18_OF_20","FX_Status":"IDENTITY" if ccy=="EUR" else ("RESOLVED" if ccy in fx else "UNRESOLVED"),"Last_Session": last20.index.max().date().isoformat() if not last20.empty else ""})
    conn.close()
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"liquidity_236_v0.48.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(sidecar[0].keys())); w.writeheader(); w.writerows(sidecar)
    with open(OUT/"parked_3_short_history_v0.48.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=["WS_ID","Yahoo_Symbol","Reason"]); w.writeheader()
        for r in qa:
            if r.get("History_QA")!="PASS_HISTORY": w.writerow({"WS_ID":r["WS_ID"],"Yahoo_Symbol":r["Yahoo_Symbol"],"Reason":"FAIL_HISTORY_PARKED"})
    if sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    cls=Counter(x["Liquidity_Class"] for x in sidecar)
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_LIQUIDITY_FX_SIDECAR_236","version":"v0.48","run_mode":"LIQUIDITY_FX_SIDECAR_236_PASS_ONLY","status":"COMPLETE","sidecar_rows":len(sidecar),"class_counts":dict(cls),"universe_mutated":False,"eligibility_promoted":False,"mapping_status_flipped":False,"sqlite_committed":False,"productive":False,"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_v0.48.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
