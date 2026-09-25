#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,shutil,sqlite3
from pathlib import Path
from decimal import Decimal

SOURCE_SHA="9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9"
SOURCE_BYTES=144216064
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
SOURCE_STATES=1425
SOURCE_READY=1415
SOURCE_QUAR=10
SOURCE_PRICE_ROWS=711204
ECHO_HASH="c06667c4cf79b4b2fbd07749168210363b8b6db3df797e89363087f4160f8a44"
MRNA_HASH="cdb1b4ae475b73b925ebf6a780e12c4fee6790474c4a63acd6f3bb62b5b36ee9"

ASX={
"WS:XASX:ANZ":("ANZ.AX","High<Close"),
"WS:XASX:BSL":("BSL.AX","High<Close"),
"WS:XASX:BXB":("BXB.AX","High<Close"),
"WS:XASX:CBA":("CBA.AX","High<Close"),
"WS:XASX:NXT":("NXT.AX","Low>Close"),
"WS:XASX:PME":("PME.AX","High<Close"),
"WS:XASX:QAN":("QAN.AX","High<Close"),
"WS:XASX:SDF":("SDF.AX","Low>Close"),
}
EVENTS={
"WS:XNAS:ECHO":{
 "Security_Key":"WSSEC:WS:XNAS:ECHO","Provider_Symbol":"ECHO","Previous_Date":"2025-08-25","Event_Date":"2025-08-26",
 "Previous_Close":29.8799991607666,"Close":50.869998931884766,"Market_Evidence_SHA256":ECHO_HASH,
 "Evidence_Type":"ISSUER_MATERIAL_TRANSACTION","Primary_Authority_Class":"ISSUER",
 "Primary_Evidence_Source":"EchoStar Corporation — EchoStar Announces Spectrum Sale and Hybrid Mobile Network Operator Agreement",
 "Primary_Evidence_Reference":"https://ir.echostar.com/node/32621","Primary_Evidence_Date":"2025-08-26",
 "Classification":"GENUINE_MARKET_MOVE","Verdict":"LEGITIMATE_EVENT_READY"},
"WS:XNAS:MRNA":{
 "Security_Key":"WSSEC:WS:XNAS:MRNA","Provider_Symbol":"MRNA","Previous_Date":"2026-08-18","Event_Date":"2026-08-19",
 "Previous_Close":62.959999084472656,"Close":174.3800048828125,"Market_Evidence_SHA256":MRNA_HASH,
 "Evidence_Type":"ISSUER_PHASE3_TOPLINE_RESULTS","Primary_Authority_Class":"ISSUER",
 "Primary_Evidence_Source":"Moderna — Merck and Moderna Announce Phase 3 INTerpath-001 Trial Met RFS and DMFS Endpoints",
 "Primary_Evidence_Reference":"https://news.modernatx.com/merck-and-moderna-announce-phase-3-interpath-001-trial-of-intismeran-plus-keytruda-met-endpoints-of-rfs-and-dmfs-in-melanoma",
 "Primary_Evidence_Date":"2026-08-19","Classification":"GENUINE_MARKET_MOVE","Verdict":"LEGITIMATE_EVENT_READY"},
}
MARKET_FIELDS=["Security_Key","Source_WS_ID","Previous_Observation_Date","Observation_Date","Previous_Close","Observation_Close","Previous_Adjusted_Close","Observation_Adjusted_Close","Observation_Volume","Observation_Dividend","Observation_Stock_Split"]

def sha256_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def nt(v):
 s="" if v is None else str(v).strip()
 return "<NULL>" if not s else s.replace("\r\n","\n").replace("\r","\n")
def nd(v):
 s="" if v is None else str(v).strip()
 if not s:return "<NULL>"
 d=Decimal(s)
 if d==0:return "0"
 z=format(d,"f")
 return z.rstrip("0").rstrip(".") if "." in z else z
def market_hash(ev):
 numeric={"Previous_Close","Observation_Close","Previous_Adjusted_Close","Observation_Adjusted_Close","Observation_Volume","Observation_Dividend","Observation_Stock_Split"}
 vals=[nd(ev.get(f)) if f in numeric else nt(ev.get(f)) for f in MARKET_FIELDS]
 return hashlib.sha256((json.dumps(vals,ensure_ascii=False,separators=(",",":"))+"\n").encode()).hexdigest()

def connect_ro(p):
 return sqlite3.connect(f"file:{Path(p).resolve()}?mode=ro",uri=True)

def state_snapshot(con):
 rows=con.execute("""select ws_id,yahoo_symbol,mapping_status,status,coalesce(reason_code,''),unique_bars,valid_bars,
 repaired_rows,suspicious_returns,zero_volume_share,first_bar_date,last_bar_date,last_fetch_utc,batch_id,coalesce(last_error,'')
 from cache_state order by ws_id""").fetchall()
 return rows

def validate_source(con):
 assert con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 assert con.execute("select count(*) from price_daily").fetchone()[0]==SOURCE_PRICE_ROWS
 assert con.execute("select count(*) from cache_state").fetchone()[0]==SOURCE_STATES
 assert dict(con.execute("select status,count(*) from cache_state group by status").fetchall())=={"QUARANTINE":10,"READY":1415}
 q=con.execute("select ws_id,yahoo_symbol,reason_code from cache_state where status='QUARANTINE' order by ws_id").fetchall()
 assert {x[0] for x in q}==set(ASX)|set(EVENTS)
 for ws,sym,reason in q:
  if ws in ASX: assert (sym,reason)==(ASX[ws][0],"STRICT_OHLC_RELATION_FAIL")
  else: assert (sym,reason)==(EVENTS[ws]["Provider_Symbol"],"SUSPICIOUS_RETURN_NEEDS_REPAIR")

def event_payload(con,ws,e):
 prev=con.execute("select close,adj_close from price_daily where ws_id=? and day=?",(ws,e["Previous_Date"])).fetchone()
 cur=con.execute("select close,adj_close,volume,dividends,stock_splits from price_daily where ws_id=? and day=?",(ws,e["Event_Date"])).fetchone()
 assert prev and cur
 ev=dict(Security_Key=e["Security_Key"],Source_WS_ID=ws,Previous_Observation_Date=e["Previous_Date"],Observation_Date=e["Event_Date"],
 Previous_Close=prev[0],Observation_Close=cur[0],Previous_Adjusted_Close=prev[1],Observation_Adjusted_Close=cur[1],
 Observation_Volume=cur[2],Observation_Dividend=cur[3],Observation_Stock_Split=cur[4])
 assert market_hash(ev)==e["Market_Evidence_SHA256"]
 assert float(prev[0])==e["Previous_Close"] and float(cur[0])==e["Close"]
 return ev

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--source-sqlite",required=True)
 ap.add_argument("--diag-dir",required=True)
 ap.add_argument("--target-sqlite",required=True)
 ap.add_argument("--frozen",default="universe/SWING_U3K_FROZEN_v0.5.csv")
 ap.add_argument("--out",default="output_p0_frozen_1425_nonready10_resume_runtime_v0_48")
 args=ap.parse_args()
 src=Path(args.source_sqlite);target=Path(args.target_sqlite);diag=Path(args.diag_dir);out=Path(args.out);out.mkdir(parents=True,exist_ok=True);target.parent.mkdir(parents=True,exist_ok=True)
 assert src.stat().st_size==SOURCE_BYTES and sha256_file(src)==SOURCE_SHA
 assert sha256_file(Path(args.frozen))==FROZEN_SHA
 meta=json.loads((diag/"diagnostic_summary_v0.48.json").read_text())
 assert meta["runtime_sha256"]==SOURCE_SHA and meta["states"]==1425 and meta["ready"]==1415 and meta["quarantine"]==10
 assert meta["provider_calls"]==6 and meta["alpha_vantage_calls"]==0 and meta["scalable_calls"]==0

 con=connect_ro(src);validate_source(con);before=state_snapshot(con)
 # Verify Exact-10 provider refetch reproduces source anomaly/event values.
 with (diag/"provider_refetch_v0.48.csv").open(newline="",encoding="utf-8") as f: rf=list(csv.DictReader(f))
 for ws,(sym,rel) in ASX.items():
  srcrow=con.execute("select open,high,low,close,adj_close,volume from price_daily where ws_id=? and day='2024-11-15'",(ws,)).fetchone()
  rows=[r for r in rf if r["Source_WS_ID"]==ws and r["Date"]=="2024-11-15" and r["Repair"]=="false" and r["Fetch_Status"]=="OK"]
  assert len(rows)==1
  r=rows[0]
  vals=[float(r[x]) for x in ["open","high","low","close","volume"]]
  # Raw OHLC and volume must reproduce exactly. Adj Close may be retrospectively
  # restated by Yahoo when later corporate-action factors change, so it is audited
  # separately and cannot determine the raw OHLC relation result.
  assert vals==[float(srcrow[i]) for i in [0,1,2,3,5]]
 for ws,e in EVENTS.items():
  ev=event_payload(con,ws,e)
  rows=[r for r in rf if r["Source_WS_ID"]==ws and r["Date"]==e["Event_Date"] and r["Repair"]=="false" and r["Fetch_Status"]=="OK"]
  assert len(rows)==1
  r=rows[0]
  cur=con.execute("select open,high,low,close,adj_close,volume from price_daily where ws_id=? and day=?",(ws,e["Event_Date"])).fetchone()
  assert [float(r[x]) for x in ["open","high","low","close","adj_close","volume"]]==[float(x) for x in cur]
 con.close()

 shutil.copyfile(src,target)
 rw=sqlite3.connect(target)
 validate_source(rw)
 before_target=state_snapshot(rw)
 assert before_target==before
 # Only the two evidence-verified extreme-return states move to READY.
 for ws,e in EVENTS.items():
  cur=rw.execute("update cache_state set status='READY', reason_code='VERIFIED_EXTREME_RETURN', last_error=NULL where ws_id=? and status='QUARANTINE' and reason_code='SUSPICIOUS_RETURN_NEEDS_REPAIR'",(ws,))
  assert cur.rowcount==1
 rw.commit()
 mode=rw.execute("PRAGMA journal_mode").fetchone()[0].lower()
 checkpoint=None
 if mode=="wal": checkpoint=rw.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
 rw.commit();rw.close()

 h1=sha256_file(target);n1=target.stat().st_size;h2=sha256_file(target);n2=target.stat().st_size
 assert h1==h2 and n1==n2
 post=connect_ro(target)
 assert post.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
 assert post.execute("select count(*) from price_daily").fetchone()[0]==SOURCE_PRICE_ROWS
 counts=dict(post.execute("select status,count(*) from cache_state group by status").fetchall())
 assert counts=={"QUARANTINE":8,"READY":1417}
 after=state_snapshot(post)
 bmap={r[0]:r for r in before}; amap={r[0]:r for r in after}
 changed=[]
 for ws in sorted(bmap):
  if bmap[ws]!=amap[ws]: changed.append(ws)
 assert changed==sorted(EVENTS)
 for ws in ASX:
  st=post.execute("select yahoo_symbol,status,reason_code,unique_bars,valid_bars,suspicious_returns,last_bar_date from cache_state where ws_id=?",(ws,)).fetchone()
  assert st==(ASX[ws][0],"QUARANTINE","STRICT_OHLC_RELATION_FAIL",507,506,0,"2026-09-22")
 for ws,e in EVENTS.items():
  st=post.execute("select yahoo_symbol,status,reason_code,suspicious_returns from cache_state where ws_id=?",(ws,)).fetchone()
  assert st==(e["Provider_Symbol"],"READY","VERIFIED_EXTREME_RETURN",1)
 post.close()

 event_rows=[]
 for ws,e in EVENTS.items():
  ret=(e["Close"]/e["Previous_Close"]-1)*100
  event_rows.append({
   "Security_Key":e["Security_Key"],"Source_WS_ID":ws,"Provider_Symbol":e["Provider_Symbol"],
   "Previous_Observation_Date":e["Previous_Date"],"Observation_Date":e["Event_Date"],
   "Previous_Close":e["Previous_Close"],"Observation_Close":e["Close"],"Observed_Return_Pct":ret,
   "Market_Evidence_SHA256":e["Market_Evidence_SHA256"],"Reconciliation_State":"VERIFIED_EXTREME_RETURN",
   "Classification":e["Classification"],"Verdict":e["Verdict"],"Evidence_Type":e["Evidence_Type"],
   "Primary_Authority_Class":e["Primary_Authority_Class"],"Primary_Evidence_Source":e["Primary_Evidence_Source"],
   "Primary_Evidence_Reference":e["Primary_Evidence_Reference"],"Primary_Evidence_Date":e["Primary_Evidence_Date"]
  })
 with (out/"event_reconciliation_v0.48.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(event_rows[0]));w.writeheader();w.writerows(event_rows)

 with (out/"runtime_state_changes_v0.48.csv").open("w",newline="",encoding="utf-8") as f:
  fields=["Source_WS_ID","Provider_Symbol","Status_Before","Reason_Before","Status_After","Reason_After"]
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for ws in sorted(EVENTS):
   w.writerow({"Source_WS_ID":ws,"Provider_Symbol":EVENTS[ws]["Provider_Symbol"],"Status_Before":"QUARANTINE","Reason_Before":"SUSPICIOUS_RETURN_NEEDS_REPAIR","Status_After":"READY","Reason_After":"VERIFIED_EXTREME_RETURN"})

 runtime={
  "source_runtime_sha256":SOURCE_SHA,"source_runtime_bytes":SOURCE_BYTES,
  "final_runtime_sha256":h1,"final_runtime_bytes":n1,
  "hash_pass_1":h1,"hash_pass_2":h2,"deterministic_repeat":h1==h2,
  "journal_mode_before_close":mode,"wal_checkpoint_result":checkpoint,
  "integrity_check":"ok","price_rows":SOURCE_PRICE_ROWS,"states":1425,
  "status_counts":counts,"changed_state_identities":changed,
  "market_provider_calls_in_finalize":0,"diagnostic_provider_calls":6,
  "alpha_vantage_calls":0,"scalable_calls":0
 }
 (out/"runtime_prepackage_v0.48.json").write_text(json.dumps(runtime,indent=2,sort_keys=True)+"\n")
 print(json.dumps(runtime,sort_keys=True))
if __name__=="__main__":main()
