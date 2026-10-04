#!/usr/bin/env python3
"""G-P0-06/v1.04 reproducible DESIGN execution contract.
Input is immutable v0.53 SQLite; caller must supply Frozen WS_ID->Primary_MIC mapping.
Never query market bars after 2026-03-11. No provider calls.
"""
import sqlite3, pandas as pd, numpy as np
DESIGN_START="2025-09-17"; FIREWALL="2026-03-11"; BASE_ANCHORS=140451
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
    if any(pd.isna(r[x]) for x in required): return "DESIGN_CANDIDATE_NOT_VERIFIED_INPUT"
    n=int(p["Base_Window"]); k=int(p["Stage2_Persistence"])
    base=(r[f"BASE_WIDTH_{n}"]<=p["Base_Width_Boundary"] and bool(r[f"BASE_ABOVE_SMA200_{n}"]) and bool(r[f"BASE_EQ_PIVOT_{n}"]))
    stage=bool(r[f"STAGE2_{k}"]); branch=base or stage
    prox=r.P0_Pivot_Distance_ATR<=p["Pivot_Proximity_Cutoff_ATR"]
    climax=abs(r.DailyMove_Over_ATR14)>=p["Climax_Move_ATR"] and r.RVOL20>=p["Climax_RVOL"] and r.Close_Location_Value<=p["Climax_Close_Location"]
    runup=(r.R20>=p["Runup_R20"] and r.R60>=p["Runup_R60"]) or r.Pivot_Extension_ATR>=p["Runup_Pivot_Extension_ATR"]
    return "DESIGN_CANDIDATE_HIT" if branch and r.TREND and r.COMPRESSION and prox and not climax and not runup else "DESIGN_CANDIDATE_FALSE"
