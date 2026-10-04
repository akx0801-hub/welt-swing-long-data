#!/usr/bin/env python3
"""G-P0-06/v1.04 reproducible DESIGN execution contract.
Input is immutable v0.53 SQLite; caller must supply Frozen WS_ID->Primary_MIC mapping.
Never query market bars after 2026-03-11. No provider calls.
"""
import sqlite3, pandas as pd, numpy as np, json
HOLDOUT_START="2026-06-09"; FIREWALL="2026-09-03"; BASE_ANCHORS=66148
CSET_SHA="8148c0bd2294bece39908d84394dda4fb0835210e83822997df12b9fbd0d6235"
def valid_bars(x):
    q=x[["open","high","low","close","volume"]].apply(pd.to_numeric,errors="coerce")
    return np.isfinite(q[["open","high","low","close"]]).all(1)&(q[["open","high","low","close"]]>0).all(1)&(q.high>=q.low)&(q.close<=q.high)&(q.close>=q.low)&~((q.volume<0)&q.volume.notna())
def technical_frame(g):
    g=g.sort_values("day").loc[valid_bars(g)].reset_index(drop=True)
    o,h,l,c,v=[pd.to_numeric(g[x],errors="coerce") for x in ["open","high","low","close","volume"]]
    prev=c.shift(1); tr=pd.concat([(h-l).abs(),(h-prev).abs(),(l-prev).abs()],axis=1).max(1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    e50=c.ewm(span=50,adjust=False,min_periods=50).mean(); s200=c.rolling(200,min_periods=200).mean(); e50s=e50/e50.shift(10)-1
    hi=lambda n:h.rolling(n,min_periods=n).max(); lo=lambda n:l.rolling(n,min_periods=n).min()
    ph=h.shift(1).rolling(20,min_periods=20).max()
    z=pd.DataFrame({"day":g.day,"Close_Tech":c,"High_Tech":h,"Low_Tech":l,"ATR14":atr,"SMA200":s200,"EMA50":e50,"EMA50_Slope_10":e50s,
      "Range5_Pct":(hi(5)-lo(5))/c,"Range10_Pct":(hi(10)-lo(10))/c,"Range20_Pct":(hi(20)-lo(20))/c,
      "R20":c/c.shift(20)-1,"R60":c/c.shift(60)-1,"RVOL20":v/v.shift(1).rolling(20,min_periods=20).median(),
      "DailyMove_Over_ATR14":(c-prev)/atr.shift(1),"PriorHigh20_excl_t":ph,
      "P0_Pivot_Distance_ATR":(c-ph).abs()/atr,"Pivot_Extension_ATR":(c-ph)/atr,
      "Close_Location_Value":((c-l)/(h-l)).where(h!=l)})
    z["TREND"]=(c>s200)&(e50>s200)&(e50s>0); z["COMPRESSION"]=(z.Range5_Pct<z.Range10_Pct)&(z.Range10_Pct<z.Range20_Pct)
    for n in (20,30,40):
      bh=h.shift(1).rolling(n).max(); bl=l.shift(1).rolling(n).min()
      z[f"BASE_WIDTH_{n}"]=1-bl/bh; z[f"BASE_EQ_PIVOT_{n}"]=bh==ph
      z[f"BASE_ABOVE_SMA200_{n}"]=(((c>s200)&np.isfinite(s200)).shift(1).rolling(n).sum()==n)
    for k in (1,3,5): z[f"STAGE2_{k}"]=(z.TREND.astype(int).rolling(k).sum()==k)
    for q in (5,10,15):
      z[f"FWD_CLOSE_RETURN_{q}"]=c.shift(-q)/c-1
      z[f"FWD_MAX_PIVOT_EXTENSION_ATR_{q}"]=(h.shift(-1)[::-1].rolling(q).max()[::-1]-ph)/atr
      z[f"FWD_MAX_DRAWDOWN_ATR_{q}"]=(l.shift(-1)[::-1].rolling(q).min()[::-1]-c)/atr
      z[f"FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT_{q}"]=c.shift(-1)[::-1].rolling(q).max()[::-1]>ph
    return z
def tri_or(a,b):
    if a=="TRUE" or b=="TRUE": return "TRUE"
    if a=="FALSE" and b=="FALSE": return "FALSE"
    return "NOT_VERIFIED_INPUT"
def candidate_status(r,p):
    required=["TREND","COMPRESSION","P0_Pivot_Distance_ATR","DailyMove_Over_ATR14","RVOL20","Close_Location_Value","R20","R60","Pivot_Extension_ATR"]
    if any(pd.isna(r[x]) for x in required): return "HOLDOUT_FINALIST_NOT_VERIFIED_INPUT"
    n=int(p["Base_Window"]); k=int(p["Stage2_Persistence"])
    base=(r[f"BASE_WIDTH_{n}"]<=p["Base_Width_Boundary"] and bool(r[f"BASE_ABOVE_SMA200_{n}"]) and bool(r[f"BASE_EQ_PIVOT_{n}"]))
    stage=bool(r[f"STAGE2_{k}"]); branch=base or stage
    prox=r.P0_Pivot_Distance_ATR<=p["Pivot_Proximity_Cutoff_ATR"]
    climax=abs(r.DailyMove_Over_ATR14)>=p["Climax_Move_ATR"] and r.RVOL20>=p["Climax_RVOL"] and r.Close_Location_Value<=p["Climax_Close_Location"]
    runup=(r.R20>=p["Runup_R20"] and r.R60>=p["Runup_R60"]) or r.Pivot_Extension_ATR>=p["Runup_Pivot_Extension_ATR"]
    return "HOLDOUT_FINALIST_HIT" if branch and r.TREND and r.COMPRESSION and prox and not climax and not runup else "HOLDOUT_FINALIST_FALSE"

def execute_holdout(db_path, universe_csv, out_dir):
    from pathlib import Path
    import hashlib, json, zipfile
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    uni=pd.read_csv(universe_csv,dtype=str); mic=dict(zip(uni["Source_WS_ID"],uni["Primary_MIC"]))
    con=sqlite3.connect(db_path)
    try: px=pd.read_sql_query("SELECT * FROM price_daily WHERE day <= ? ORDER BY ws_id,day",con,params=[FIREWALL])
    finally: con.close()
    p={"Base_Window":30,"Base_Width_Boundary":0.18,"Stage2_Persistence":3,"Pivot_Proximity_Cutoff_ATR":0.75,"Climax_Move_ATR":2.25,"Climax_RVOL":2.25,"Climax_Close_Location":0.50,"Runup_R20":0.20,"Runup_R60":0.35,"Runup_Pivot_Extension_ATR":1.25}
    rows=[]; raw=0
    for ws,g in px.groupby("ws_id",sort=False):
        z=technical_frame(g); z["i"]=np.arange(len(z))
        rawmask=(z.day>=HOLDOUT_START)&(z.day<=FIREWALL)&(z.i>=251)
        raw+=int(rawmask.sum())
        mask=rawmask&(z.i+15<len(z))
        for _,r in z.loc[mask].iterrows():
            st=candidate_status(r,p)
            n=30
            req=["TREND","COMPRESSION","P0_Pivot_Distance_ATR","DailyMove_Over_ATR14","RVOL20","Close_Location_Value","R20","R60","Pivot_Extension_ATR"]
            nv=any(pd.isna(r[x]) for x in req)
            base="NOT_VERIFIED_INPUT" if any(pd.isna(r[x]) for x in [f"BASE_WIDTH_{n}",f"BASE_ABOVE_SMA200_{n}",f"BASE_EQ_PIVOT_{n}"]) else ("TRUE" if r[f"BASE_WIDTH_{n}"]<=.18 and bool(r[f"BASE_ABOVE_SMA200_{n}"]) and bool(r[f"BASE_EQ_PIVOT_{n}"]) else "FALSE")
            stage="TRUE" if bool(r["STAGE2_3"]) else "FALSE"
            branch="TRUE" if "TRUE" in (base,stage) else ("FALSE" if base==stage=="FALSE" else "NOT_VERIFIED_INPUT")
            tri=lambda v,missing=False:"NOT_VERIFIED_INPUT" if missing else ("TRUE" if bool(v) else "FALSE")
            trend=tri(r.TREND,pd.isna(r.TREND)); comp=tri(r.COMPRESSION,pd.isna(r.COMPRESSION)); prox=tri(r.P0_Pivot_Distance_ATR<=.75,pd.isna(r.P0_Pivot_Distance_ATR))
            cm=any(pd.isna(r[x]) for x in ["DailyMove_Over_ATR14","RVOL20","Close_Location_Value"]); climax=tri(abs(r.DailyMove_Over_ATR14)>=2.25 and r.RVOL20>=2.25 and r.Close_Location_Value<=.5,cm)
            rm=any(pd.isna(r[x]) for x in ["R20","R60","Pivot_Extension_ATR"]); runup=tri((r.R20>=.2 and r.R60>=.35) or r.Pivot_Extension_ATR>=1.25,rm)
            rec={"WS_ID":ws,"Anchor_Date":r.day,"Primary_MIC":mic[ws],"C07_Status":st,"BASE_BRANCH":base,"STAGE2_BRANCH":stage,"BASE_OR_STAGE2_BRANCH":branch,"TREND_CONTEXT":trend,"COMPRESSION":comp,"PIVOT_PROXIMITY_PASS":prox,"CLIMAX":climax,"EXCESSIVE_RUNUP":runup,"COMPLETE_FINALIST":st}
            for q in (5,10,15):
                for m in ["FWD_CLOSE_RETURN","FWD_MAX_PIVOT_EXTENSION_ATR","FWD_MAX_DRAWDOWN_ATR","FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT"]: rec[f"{m}_{q}"]=r[f"{m}_{q}"]
            rows.append(rec)
    df=pd.DataFrame(rows)
    assert raw==84925,(raw,"raw"); assert len(df)==66148,len(df); assert raw-len(df)==18777
    ap=out/"holdout_anchor_evidence_v1.08.csv"; df.to_csv(ap,index=False)
    H="HOLDOUT_FINALIST_HIT"; F="HOLDOUT_FINALIST_FALSE"; N="HOLDOUT_FINALIST_NOT_VERIFIED_INPUT"; vc=df.C07_Status.value_counts(); hc=int(vc.get(H,0));fc=int(vc.get(F,0));nc=int(vc.get(N,0));ev=hc+fc; assert hc+fc+nc==66148
    pd.DataFrame([{"Holdout_Base_Anchors":66148,"Hit_Count":hc,"False_Count":fc,"Not_Verified_Count":nc,"Hit_Share_of_Holdout_Base":hc/66148,"Evaluable_Count":ev,"Hit_Share_of_Evaluable":hc/ev,"Not_Verified_Share":nc/66148}]).to_csv(out/"finalist_execution_counts_v1.08.csv",index=False)
    cr=[]
    for c in ["BASE_BRANCH","STAGE2_BRANCH","BASE_OR_STAGE2_BRANCH","TREND_CONTEXT","COMPRESSION","PIVOT_PROXIMITY_PASS","CLIMAX","EXCESSIVE_RUNUP","COMPLETE_FINALIST"]:
        s=df[c].replace({H:"TRUE",F:"FALSE",N:"NOT_VERIFIED_INPUT"});v=s.value_counts();cr.append({"Component":c,"TRUE":int(v.get("TRUE",0)),"FALSE":int(v.get("FALSE",0)),"NOT_VERIFIED_INPUT":int(v.get("NOT_VERIFIED_INPUT",0))})
    pd.DataFrame(cr).to_csv(out/"finalist_component_counts_v1.08.csv",index=False)
    cont=[];boo=[];subs={"HIT":df[df.C07_Status==H],"FALSE":df[df.C07_Status==F],"ALL_EVALUABLE":df[df.C07_Status!=N]}
    for q in (5,10,15):
      for sn,s in subs.items():
       for m in ["FWD_CLOSE_RETURN","FWD_MAX_PIVOT_EXTENSION_ATR","FWD_MAX_DRAWDOWN_ATR"]:
        x=pd.to_numeric(s[f"{m}_{q}"],errors="coerce").dropna();cont.append({"Horizon":q,"Subset":sn,"Metric":m,"N":len(x),"P25":x.quantile(.25),"MEDIAN":x.median(),"P75":x.quantile(.75)})
       x=s[f"FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT_{q}"].dropna().astype(bool);boo.append({"Horizon":q,"Subset":sn,"N":len(x),"True_Count":int(x.sum()),"False_Count":int((~x).sum()),"True_Share":float(x.mean())})
    pd.DataFrame(cont).to_csv(out/"finalist_forward_continuous_summary_v1.08.csv",index=False);pd.DataFrame(boo).to_csv(out/"finalist_forward_boolean_summary_v1.08.csv",index=False)
    df["Month"]=df.Anchor_Date.str[:7]
    for key,name in [("Primary_MIC","finalist_primary_mic_stability_v1.08.csv"),("Month","finalist_month_stability_v1.08.csv")]:
      rr=[]
      for val,s in df.groupby(key):
       v=s.C07_Status.value_counts();hh=int(v.get(H,0));ff=int(v.get(F,0));nn=int(v.get(N,0));r={key:val,"Anchor_Count":len(s),"Hit_Count":hh,"False_Count":ff,"Not_Verified_Count":nn,"Hit_Share_of_Evaluable":hh/(hh+ff) if hh+ff else None};hs=s[s.C07_Status==H]
       for q in (5,10,15):
        for m in ["FWD_CLOSE_RETURN","FWD_MAX_PIVOT_EXTENSION_ATR","FWD_MAX_DRAWDOWN_ATR"]:r[f"HIT_{m}_{q}_MEDIAN"]=hs[f"{m}_{q}"].median()
        r[f"HIT_PIVOT_CROSS_{q}_TRUE_SHARE"]=hs[f"FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT_{q}"].mean()
       rr.append(r)
      pd.DataFrame(rr).to_csv(out/name,index=False)
    ah=hashlib.sha256(ap.read_bytes()).hexdigest()
    man={"filename":"holdout_anchor_evidence_v1.08.csv","bytes":ap.stat().st_size,"sha256":ah,"role":"ROW_LEVEL_HOLDOUT_EVIDENCE","Finalist_Candidate_ID":"L1-C07-PIVOT_PROXIMITY_STRICT","Finalist_Semantic_SHA256":"7aabed14feb3ab902223f981619864b24aecc25b51c3d67f4026e4a8e357c201","Candidate_Set_ID":"L1_BREAKOUT_VCP_CSET_01","Candidate_Set_Semantic_SHA256":CSET_SHA,"Frozen_SHA256":"54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb","v053_SQLite_SHA256":"bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc","Holdout_Base_Anchors":66148,"Max_Market_Bar_Read_Date":"2026-09-03","HOLDOUT_SINGLE_USE":"YES"}
    mp=out/"holdout_payload_manifest_v1.08.json";mp.write_text(json.dumps(man,indent=2)+"\n")
    return {"raw":raw,"purged":raw-len(df),"base":len(df),"hit":hc,"false":fc,"nv":nc,"anchor_sha":ah}
if __name__=="__main__":
 import sys
 print(json.dumps(execute_holdout(sys.argv[1],sys.argv[2],sys.argv[3]),indent=2))
