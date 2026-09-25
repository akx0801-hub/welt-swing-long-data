#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, json, sqlite3
from pathlib import Path
from typing import Any
import pandas as pd
import numpy as np
import yfinance as yf

EXPECTED_SHA="9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9"
EXPECTED_BYTES=144216064
EXPECTED_ROWS=711204
EXPECTED_STATES=1425
EXPECTED_READY=1415
EXPECTED_QUAR=10

EXACT = {
 "WS:XASX:ANZ":("ANZ.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:BSL":("BSL.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:BXB":("BXB.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:CBA":("CBA.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:NXT":("NXT.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:PME":("PME.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:QAN":("QAN.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XASX:SDF":("SDF.AX","STRICT_OHLC_RELATION_FAIL","2024-11-15"),
 "WS:XNAS:ECHO":("ECHO","SUSPICIOUS_RETURN_NEEDS_REPAIR","2025-08-26"),
 "WS:XNAS:MRNA":("MRNA","SUSPICIOUS_RETURN_NEEDS_REPAIR","2026-08-19"),
}

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
 return h.hexdigest()

def norm_frame(raw:pd.DataFrame,symbol:str)->pd.DataFrame:
 if raw is None or raw.empty: return pd.DataFrame()
 x=raw.copy()
 if isinstance(x.columns,pd.MultiIndex):
  if symbol in x.columns.get_level_values(0):
   x=x[symbol].copy()
  elif symbol in x.columns.get_level_values(-1):
   x=x.xs(symbol,axis=1,level=-1).copy()
 x.columns=[str(c).strip().lower().replace(" ","_") for c in x.columns]
 aliases={"adj_close":"adj_close","adjclose":"adj_close","stock_splits":"stock_splits","stock_splits_":"stock_splits"}
 x=x.rename(columns=aliases)
 for c in ["open","high","low","close","adj_close","volume","dividends","stock_splits"]:
  if c not in x.columns: x[c]=np.nan if c not in ("dividends","stock_splits") else 0.0
  x[c]=pd.to_numeric(x[c],errors="coerce")
 x.index=pd.to_datetime(x.index).tz_localize(None)
 return x.sort_index()

def download(symbols,start,end,repair):
 raw=yf.download(
  tickers=list(symbols), start=start, end=end, interval="1d",
  group_by="ticker", auto_adjust=False, actions=True,
  repair=repair, threads=True, progress=False, timeout=30
 )
 return raw

def relation(row):
 out=[]
 o,h,l,c=[float(row[k]) for k in ["open","high","low","close"]]
 checks=[("High<Open",h<o,o-h),("High<Close",h<c,c-h),("High<Low",h<l,l-h),
         ("Low>Open",l>o,l-o),("Low>Close",l>c,l-c),("Low>High",l>h,l-h)]
 for name,bad,mag in checks:
  if bad: out.append((name,mag,mag/max(abs(o),abs(h),abs(l),abs(c),1e-300)))
 return out

def row_payload(ws,sym,day,row,source_kind,repair):
 d={"Source_WS_ID":ws,"Provider_Symbol":sym,"Date":day,"Source_Kind":source_kind,"Repair":str(repair).lower()}
 for c in ["open","high","low","close","adj_close","volume","dividends","stock_splits"]:
  v=row.get(c,np.nan); d[c]=None if pd.isna(v) else float(v)
 rel=relation(row) if all(pd.notna(row.get(c)) for c in ["open","high","low","close"]) else []
 d["Failed_Relations"]="|".join(x[0] for x in rel)
 d["Max_Abs_Violation"]=max([x[1] for x in rel],default=0.0)
 d["Max_Rel_Violation"]=max([x[2] for x in rel],default=0.0)
 return d

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--sqlite",required=True)
 ap.add_argument("--out",default="output_p0_frozen_1425_nonready10_resume_diag_v0_48")
 args=ap.parse_args()
 db=Path(args.sqlite); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
 assert db.stat().st_size==EXPECTED_BYTES
 assert sha256_file(db)==EXPECTED_SHA
 con=sqlite3.connect(f"file:{db.resolve()}?mode=ro",uri=True)
 assert con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 assert con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]==EXPECTED_ROWS
 assert con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]==EXPECTED_STATES
 counts=dict(con.execute("SELECT status,COUNT(*) FROM cache_state GROUP BY status").fetchall())
 assert counts=={"QUARANTINE":10,"READY":1415}
 qrows=con.execute("SELECT ws_id,yahoo_symbol,reason_code FROM cache_state WHERE status='QUARANTINE' ORDER BY ws_id").fetchall()
 assert {r[0] for r in qrows}==set(EXACT)
 for ws,sym,reason in qrows:
  es,er,_=EXACT[ws]; assert sym==es and reason==er

 anomaly=[]
 for ws,(sym,reason,eventday) in EXACT.items():
  rows=con.execute("""SELECT day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired,source_id,fetched_utc
                     FROM price_daily WHERE ws_id=? ORDER BY day""",(ws,)).fetchall()
  cols=["day","open","high","low","close","adj_close","volume","dividends","stock_splits","repaired","source_id","fetched_utc"]
  x=pd.DataFrame(rows,columns=cols).set_index(pd.to_datetime([r[0] for r in rows]))
  x=x.drop(columns=["day"])
  if reason=="STRICT_OHLC_RELATION_FAIL":
   for ts,r in x.iterrows():
    rel=relation(r)
    for name,amag,rmag in rel:
     anomaly.append({
      "Source_WS_ID":ws,"Provider_Symbol":sym,"Date":ts.date().isoformat(),"Anomaly_Type":"STRICT_OHLC",
      "Relation":name,"Abs_Magnitude":amag,"Rel_Magnitude":rmag,
      "Open":r.open,"High":r.high,"Low":r.low,"Close":r.close,"Adj_Close":r.adj_close,"Volume":r.volume,
      "Dividends":r.dividends,"Stock_Splits":r.stock_splits,"Repaired":r.repaired,"Source_ID":r.source_id,"Fetched_UTC":r.fetched_utc
     })
  else:
   x["ret"]=x["close"].pct_change(fill_method=None)
   sus=x[x["ret"].abs()>0.50]
   for ts,r in sus.iterrows():
    pos=x.index.get_loc(ts); prev=x.iloc[pos-1] if pos>0 else None
    anomaly.append({
     "Source_WS_ID":ws,"Provider_Symbol":sym,"Date":ts.date().isoformat(),"Anomaly_Type":"SUSPICIOUS_RETURN",
     "Relation":"ABS_RETURN_GT_0.50","Abs_Magnitude":abs(float(r.ret)),"Rel_Magnitude":abs(float(r.ret)),
     "Open":r.open,"High":r.high,"Low":r.low,"Close":r.close,"Adj_Close":r.adj_close,"Volume":r.volume,
     "Dividends":r.dividends,"Stock_Splits":r.stock_splits,"Repaired":r.repaired,"Source_ID":r.source_id,"Fetched_UTC":r.fetched_utc,
     "Previous_Date":x.index[pos-1].date().isoformat() if pos>0 else "",
     "Previous_Close":float(prev.close) if prev is not None else None,
     "Raw_Return":float(r.ret)
    })

 # exactly six authorized provider calls: normal + repair for each anomaly-date group.
 groups=[
  (["ANZ.AX","BSL.AX","BXB.AX","CBA.AX","NXT.AX","PME.AX","QAN.AX","SDF.AX"],"2024-11-13","2024-11-20"),
  (["ECHO"],"2025-08-22","2025-08-30"),
  (["MRNA"],"2026-08-17","2026-08-25"),
 ]
 refetch=[]; call_count=0
 ws_by_sym={v[0]:k for k,v in EXACT.items()}
 for symbols,start,end in groups:
  for repair in [False,True]:
   raw=download(symbols,start,end,repair); call_count+=1
   for sym in symbols:
    x=norm_frame(raw,sym)
    ws=ws_by_sym[sym]
    if x.empty:
     refetch.append({"Source_WS_ID":ws,"Provider_Symbol":sym,"Date":"","Source_Kind":"PROVIDER_REFETCH","Repair":str(repair).lower(),"Fetch_Status":"NO_DATA"})
     continue
    for ts,r in x.iterrows():
     d=row_payload(ws,sym,ts.date().isoformat(),r,"PROVIDER_REFETCH",repair)
     d["Fetch_Status"]="OK"; refetch.append(d)

 pd.DataFrame(anomaly).to_csv(out/"anomaly_rows_persisted_v0.48.csv",index=False)
 pd.DataFrame(refetch).to_csv(out/"provider_refetch_v0.48.csv",index=False)

 comparison=[]
 rf=pd.DataFrame(refetch)
 for ws,(sym,reason,eventday) in EXACT.items():
  persisted=[a for a in anomaly if a["Source_WS_ID"]==ws and a["Date"]==eventday]
  for repair in [False,True]:
   rr=rf[(rf.Source_WS_ID==ws)&(rf.Date==eventday)&(rf.Repair==str(repair).lower())]
   rec={"Source_WS_ID":ws,"Provider_Symbol":sym,"Event_Date":eventday,"Reason":reason,"Repair":repair,"Refetch_Row_Present":len(rr)==1}
   if len(rr)==1:
    r=rr.iloc[0]
    for c in ["Open","High","Low","Close","Adj_Close","Volume","Dividends","Stock_Splits","Failed_Relations","Max_Abs_Violation","Max_Rel_Violation"]:
     rec["Refetch_"+c]=r.get(c)
    if persisted:
     p=persisted[0]
     for c in ["Open","High","Low","Close","Adj_Close","Volume","Dividends","Stock_Splits"]:
      pv=p.get(c); rv=r.get(c)
      rec["Delta_"+c]=None if pv is None or pd.isna(rv) else float(rv)-float(pv)
   comparison.append(rec)
 pd.DataFrame(comparison).to_csv(out/"provider_reproducibility_v0.48.csv",index=False)
 meta={
  "runtime_sha256":EXPECTED_SHA,"runtime_bytes":EXPECTED_BYTES,"states":EXPECTED_STATES,
  "ready":EXPECTED_READY,"quarantine":EXPECTED_QUAR,"price_rows":EXPECTED_ROWS,
  "exact10":list(EXACT),"provider_calls":call_count,"alpha_vantage_calls":0,"scalable_calls":0,
  "p0_run":False,"features_promoted":False,"rs_promoted":False,"parameters_promoted":False,
  "universe_mutation":False
 }
 (out/"diagnostic_summary_v0.48.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(meta,sort_keys=True))
 return 0
if __name__=="__main__": raise SystemExit(main())
