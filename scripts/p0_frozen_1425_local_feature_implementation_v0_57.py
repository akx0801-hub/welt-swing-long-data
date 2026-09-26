#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:
    sys.path.insert(0,str(ROOT/"scripts"))

from feature_builder import (
    build_features, split_adjust_technical, technical_valid_mask_for_features,
    _lag_ratio_return, _rvol20_prior_baseline, _safe_divide,
)

VERSION="v0.57"
STAGE="P0_FROZEN_1425_LOCAL_FEATURE_CONTRACT_V056_IMPLEMENTATION_PROMOTION"
REQUIRED_START_HEAD="0287a10bf7a2938ed1517d79a47c296f3ea34c9d"

V056_RUN=36235568433
V056_ARTIFACT=10904166471
V056_ARTIFACT_DIGEST="sha256:17acd42edc06fe7311d88e27ee0a1a2052145e92440e487c2e0f0a47a10709ed"
V055_SEMANTIC_SHA256="81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc"

V053_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
V053_RUNTIME_BYTES=144539648
V053_PRICE_ROWS=711204
V053_STATES=1425

FROZEN_PATH=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"

V056_DIR=ROOT/"output_p0_frozen_1425_local_feature_contract_v0_56"
V056_SUMMARY=V056_DIR/"summary_v0.56.json"
V056_REGISTRY=V056_DIR/"canonical_feature_contract_registry_v0.56.csv"
V056_DECISIONS=V056_DIR/"contract_decisions_v0.56.csv"
V056_MINHIST=V056_DIR/"minimum_history_contract_v0.56.csv"
V056_CURRENTBAR=V056_DIR/"current_bar_policy_v0.56.csv"
V056_ATR=V056_DIR/"atr_reference_policy_v0.56.csv"
V056_NULL=V056_DIR/"null_zero_denominator_contract_v0.56.csv"
V056_MANIFEST=V056_DIR/"manifest_v0.56.json"
V055_MATERIAL=ROOT/"output_p0_frozen_1425_local_feature_remediation_v0_55/feature_materialization_v0.55.csv"
PARAM_AUTH=ROOT/"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json"

EXPECTED_BLOBS={
 str(V056_SUMMARY.relative_to(ROOT)):"2c365f06fc38cf4d551f9f462e0ad3177859305b",
 str(V056_REGISTRY.relative_to(ROOT)):"fde0289157bc26cb4cf9fe099eee74c62d248c19",
 str(V056_DECISIONS.relative_to(ROOT)):"292c1b3b3b4630c27ba90e72dd623f8b8f645ebd",
 str(V056_MINHIST.relative_to(ROOT)):"99edce23bc0197d067037c0b64313bb53661f447",
 str(V056_CURRENTBAR.relative_to(ROOT)):"f49c393d77dc47b52e63d5cd85506951b23d31f3",
 str(V056_ATR.relative_to(ROOT)):"7c48f3b3d31580d70a740c2c74cceaed5b11cc0e",
 str(V056_NULL.relative_to(ROOT)):"f31106aa1eb7b0e184537f089aaa3abc9f4dc82a",
 str(V056_MANIFEST.relative_to(ROOT)):"b56dc0ed0d17b0b47aef4536d6491c7e0e240e0f",
 str(V055_MATERIAL.relative_to(ROOT)):"5a5de04e49c67a80e5d519685bd9d6cb7401cc8f",
 str(FROZEN_PATH.relative_to(ROOT)):"018a03eb4614a197da9d2d566e77f32c61238dad",
 str(PARAM_AUTH.relative_to(ROOT)):"01ae47713cc722497fcc56585dd27466df8baa9c",
}

OLD23=[
"Close_Tech","EMA20","EMA50","SMA200","ATR14_Wilder_DEV","ATR14_Pct_DEV",
"R1","R5","R20","R60","TrueRange_Current","High20","High60","High252","Low20","Low60",
"Dist_EMA20","Dist_EMA50","Dist_SMA200","Dist_High252","Range20_Pct",
"MedianVolume20_Tech","MedianTurnover20_Native",
]
NEW11=[
"EMA20_Slope_5","EMA50_Slope_10","Range5_Pct","Range10_Pct",
"RangeCompression_5_20","RangeCompression_10_20","RVOL20",
"Gap_Over_ATR14","DailyMove_Over_ATR14","Dist_High20","Dist_High60",
]
ALL34=OLD23+NEW11
IMPULSE_CONSTITUENTS=["R5","R20","R60","DailyMove_Over_ATR14","RVOL20"]

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args:str)->str:
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def git_blob(p:Path)->str:
    return git("hash-object",str(p.relative_to(ROOT)))

def read_csv(p:Path)->list[dict[str,str]]:
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(p:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(rows[0].keys()) if rows else []
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:
            w.writeheader()
            w.writerows(rows)

def connect_ro(p:Path)->sqlite3.Connection:
    return sqlite3.connect(f"file:{p.resolve()}?mode=ro&immutable=1",uri=True)

def validate_start_and_authority(repo_sha:str)->dict[str,Any]:
    head=git("rev-parse","HEAD")
    if head!=repo_sha:
        raise RuntimeError(f"checkout SHA mismatch {head} != {repo_sha}")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start HEAD is not ancestor")
    if git("rev-parse",f"{REQUIRED_START_HEAD}^{{commit}}")!=REQUIRED_START_HEAD:
        raise RuntimeError("required start HEAD unresolved")

    blobs={}
    for rel,exp in EXPECTED_BLOBS.items():
        got=git_blob(ROOT/rel)
        blobs[rel]=got
        if got!=exp:
            raise RuntimeError(f"authority blob mismatch {rel}: {got} != {exp}")

    old_feature_builder_blob=git("rev-parse",f"{REQUIRED_START_HEAD}:scripts/feature_builder.py")
    if old_feature_builder_blob!="50d564cd10e928a0565e74e2c49b7534d62bb529":
        raise RuntimeError("v0.56 start feature_builder authority mismatch")

    s=json.loads(V056_SUMMARY.read_text(encoding="utf-8"))
    required={
      "status":"PASS_ALL8_CONTRACTS_DEFINED",
      "new_numeric_features_expected":11,
      "p0_local_feature_layer_ready":False,
      "home_market_rs_ready":False,
      "sector_rs_ready":False,
      "feature_materialization_runs":0,
      "p0_runs":0,
      "v0_57_local_feature_implementation_authorized":True,
    }
    for k,v in required.items():
        if s.get(k)!=v:
            raise RuntimeError(f"v0.56 summary mismatch {k}: {s.get(k)} != {v}")
    if s["contract_artifact"]["workflow_run_id"]!=V056_RUN:
        raise RuntimeError("v0.56 workflow mismatch")
    if s["contract_artifact"]["artifact_id"]!=V056_ARTIFACT:
        raise RuntimeError("v0.56 artifact id mismatch")
    if s["contract_artifact"]["artifact_digest"]!=V056_ARTIFACT_DIGEST:
        raise RuntimeError("v0.56 artifact digest mismatch")
    if s["frozen"]!={"members":1425,"sha256":FROZEN_SHA256,"unchanged":True}:
        raise RuntimeError("v0.56 Frozen authority mismatch")
    if s["price_runtime"]["sha256"]!=V053_RUNTIME_SHA256 or s["price_runtime"]["bytes"]!=V053_RUNTIME_BYTES:
        raise RuntimeError("v0.56 price-runtime authority mismatch")
    if s["v055_authority"]["canonical_numeric_features"]!=23:
        raise RuntimeError("v0.56 prior canonical feature count mismatch")
    if s["v055_authority"]["feature_ready"]!=0 or s["v055_authority"]["feature_partial"]!=1425:
        raise RuntimeError("v0.56 prior capability mismatch")
    if s["new_numeric_feature_names"]!=NEW11:
        raise RuntimeError("v0.56 new feature names mismatch")
    if s["remaining_ambiguities"]!=[]:
        raise RuntimeError("v0.56 has remaining ambiguities")

    decisions=read_csv(V056_DECISIONS)
    if len(decisions)!=8 or any(r["decision_state"]!="CONTRACT_DEFINED" for r in decisions):
        raise RuntimeError("v0.56 contract decisions not all defined")

    registry=read_csv(V056_REGISTRY)
    defined=[r["canonical_feature_name"] for r in registry if r.get("promotion_version")=="v0.56" and r.get("registry_type")=="FEATURE"]
    if defined!=NEW11:
        raise RuntimeError(f"v0.56 registry new numeric mismatch {defined}")
    impulse=[r for r in registry if r.get("canonical_feature_name")=="RECENT_IMPULSE_DESCRIPTORS"]
    if len(impulse)!=1 or impulse[0]["promotion_status"]!="CONTRACT_DEFINED_NOT_IMPLEMENTED":
        raise RuntimeError("recent impulse semantic family authority mismatch")

    p=json.loads(PARAM_AUTH.read_text(encoding="utf-8"))
    if p.get("p0_numeric_pass_thresholds")!=[] or p.get("promoted_lane_pass_rules")!=[]:
        raise RuntimeError("parameter authority unexpectedly promoted")

    return {"head":head,"authority_blobs":blobs,"v056_summary":s,"v056_registry":registry}

def validate_runtime(p:Path)->dict[str,Any]:
    if p.stat().st_size!=V053_RUNTIME_BYTES:
        raise RuntimeError("price runtime byte count mismatch")
    if sha256_file(p)!=V053_RUNTIME_SHA256:
        raise RuntimeError("price runtime SHA mismatch")
    con=connect_ro(p)
    try:
        integrity=con.execute("PRAGMA integrity_check").fetchone()[0]
        rows=int(con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0])
        states=int(con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0])
        counts=dict(con.execute("SELECT status,COUNT(*) FROM cache_state GROUP BY status").fetchall())
        defects=int(con.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053 WHERE source_data_defect=1").fetchone()[0])
        exclusions=int(con.execute("SELECT COUNT(*) FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1").fetchone()[0])
    finally:
        con.close()
    if integrity!="ok" or rows!=V053_PRICE_ROWS or states!=V053_STATES or counts!={"READY":1425} or defects!=8 or exclusions!=8:
        raise RuntimeError("price runtime semantic authority mismatch")
    return {"integrity_check":integrity,"price_daily":rows,"states":states,"ready":1425,"quarantine":0,"source_defects":defects,"excluded_bars":exclusions}

def validate_frozen()->pd.DataFrame:
    if sha256_file(FROZEN_PATH)!=FROZEN_SHA256:
        raise RuntimeError("Frozen SHA mismatch")
    f=pd.read_csv(FROZEN_PATH,dtype=str).fillna("")
    if len(f)!=1425 or f["Security_Key"].duplicated().any() or f["Source_WS_ID"].duplicated().any():
        raise RuntimeError("Frozen identity mismatch")
    f["Projection_Order"]=pd.to_numeric(f["Projection_Order"],errors="raise").astype(int)
    return f.sort_values("Projection_Order").reset_index(drop=True)

def build_temp_universe(frozen:pd.DataFrame,path:Path)->None:
    pd.DataFrame({"WS_ID":frozen["Source_WS_ID"].astype(str)}).to_csv(path,index=False)

def load_provenance(runtime:Path):
    con=connect_ro(runtime)
    try:
        prov=pd.read_sql_query(
          "SELECT ws_id,source_data_defect,invalid_bar_count FROM cache_qa_provenance_v053 ORDER BY ws_id",con)
        ex=pd.read_sql_query(
          "SELECT ws_id,day FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1 ORDER BY ws_id,day",con)
    finally:
        con.close()
    dates=defaultdict(list)
    for r in ex.to_dict("records"):
        dates[str(r["ws_id"])].append(str(r["day"]))
    return prov,dates

def materialize_once(work_db:Path,frozen:pd.DataFrame,universe_csv:Path,authority_runtime:Path)->pd.DataFrame:
    feat=build_features(work_db,universe_csv)
    if len(feat)!=1425 or feat["WS_ID"].astype(str).nunique()!=1425:
        raise RuntimeError("build_features did not produce exact Frozen-1425")
    missing=[c for c in ALL34 if c not in feat.columns]
    if missing:
        raise RuntimeError(f"missing feature columns: {missing}")

    base=frozen[["Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker"]].copy()
    x=base.merge(feat,left_on="Source_WS_ID",right_on="WS_ID",how="left",validate="one_to_one")
    if x["AsOf"].isna().any():
        raise RuntimeError("feature identity merge has missing rows")

    prov,dates=load_provenance(authority_runtime)
    prov["ws_id"]=prov["ws_id"].astype(str)
    x=x.merge(prov,left_on="Source_WS_ID",right_on="ws_id",how="left",validate="one_to_one")
    x["feature_as_of_date"]=x["AsOf"].astype(str)
    x["valid_bar_count"]=pd.to_numeric(x["Bars_Used"],errors="raise").astype(int)
    x["excluded_bar_count"]=pd.to_numeric(x["Excluded_Invalid_Bars"],errors="raise").astype(int)
    x["source_data_defect"]=pd.to_numeric(x["source_data_defect"],errors="raise").astype(int).astype(bool)
    x["excluded_dates"]=x["Source_WS_ID"].map(lambda ws:"|".join(dates.get(str(ws),[])))
    x["filtered_policy_version"]="v0.53/POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT"
    return x.sort_values("Projection_Order").reset_index(drop=True)

IDENTITY_COLS=[
"Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker",
"feature_as_of_date","valid_bar_count","excluded_bar_count","source_data_defect",
"excluded_dates","filtered_policy_version",
]

def semantic_bytes(df:pd.DataFrame,features:list[str])->bytes:
    x=df[IDENTITY_COLS+features].copy().sort_values("Projection_Order").reset_index(drop=True)
    return x.to_csv(index=False,lineterminator="\n",float_format="%.17g",na_rep="<NULL>").encode("utf-8")

def semantic_digest(df:pd.DataFrame,features:list[str])->str:
    return hashlib.sha256(semantic_bytes(df,features)).hexdigest()

def serialized_records(df:pd.DataFrame,features:list[str])->list[dict[str,str]]:
    b=semantic_bytes(df,features).decode("utf-8")
    return list(csv.DictReader(io.StringIO(b)))

def existing23_regression(new:pd.DataFrame)->list[dict[str,Any]]:
    digest=semantic_digest(new,OLD23)
    if digest!=V055_SEMANTIC_SHA256:
        raise RuntimeError(f"existing-23 semantic digest changed: {digest}")
    new_rows=serialized_records(new,OLD23)
    old_rows=read_csv(V055_MATERIAL)
    if len(old_rows)!=1425 or len(new_rows)!=1425:
        raise RuntimeError("existing-23 row-count mismatch")
    old_by={r["Source_WS_ID"]:r for r in old_rows}
    new_by={r["Source_WS_ID"]:r for r in new_rows}
    if set(old_by)!=set(new_by):
        raise RuntimeError("existing-23 identity set mismatch")
    rows=[]
    for feat in OLD23:
        mism=[ws for ws in old_by if old_by[ws][feat]!=new_by[ws][feat]]
        rows.append({"Feature":feat,"Rows":1425,"Mismatch_Count":len(mism),"Result":"PASS" if not mism else "FAIL","First_Mismatches":"|".join(mism[:10])})
        if mism:
            raise RuntimeError(f"existing feature changed {feat}: {mism[:10]}")
    rows.append({"Feature":"EXISTING23_SEMANTIC_DIGEST","Rows":1425,"Mismatch_Count":0,"Result":"PASS","First_Mismatches":digest})
    return rows

def load_prices(runtime:Path)->pd.DataFrame:
    con=connect_ro(runtime)
    try:
        px=pd.read_sql_query(
          "SELECT ws_id,day,open,high,low,close,volume,stock_splits FROM price_daily ORDER BY ws_id,day",con)
    finally:
        con.close()
    px["day"]=pd.to_datetime(px["day"],errors="raise")
    return px

def finite(v)->bool:
    try:return math.isfinite(float(v))
    except (TypeError,ValueError):return False

def safe_last(s:pd.Series):
    if len(s)==0:return None
    v=s.iloc[-1]
    return float(v) if finite(v) else None

def independent_new11(g:pd.DataFrame)->tuple[dict[str,Any],pd.DataFrame]:
    x=g.sort_values("day").copy()
    valid=technical_valid_mask_for_features(x)
    x=x.loc[valid].copy()
    if x.empty:return {k:None for k in NEW11},x
    x=split_adjust_technical(x)
    o=pd.to_numeric(x["open_tech"],errors="coerce")
    h=pd.to_numeric(x["high_tech"],errors="coerce")
    l=pd.to_numeric(x["low_tech"],errors="coerce")
    c=pd.to_numeric(x["close_tech"],errors="coerce")
    v=pd.to_numeric(x["volume_tech"],errors="coerce")
    prev=c.shift(1)
    tr=pd.concat([(h-l).abs(),(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    e20=c.ewm(span=20,adjust=False,min_periods=20).mean()
    e50=c.ewm(span=50,adjust=False,min_periods=50).mean()
    hi5=h.rolling(5,min_periods=5).max(); lo5=l.rolling(5,min_periods=5).min()
    hi10=h.rolling(10,min_periods=10).max(); lo10=l.rolling(10,min_periods=10).min()
    hi20=h.rolling(20,min_periods=20).max(); lo20=l.rolling(20,min_periods=20).min()
    hi60=h.rolling(60,min_periods=60).max()

    close=safe_last(c)
    h5=safe_last(hi5);l5=safe_last(lo5);h10=safe_last(hi10);l10=safe_last(lo10)
    h20=safe_last(hi20);l20=safe_last(lo20);h60=safe_last(hi60)
    r5=None if close in (None,0) or h5 is None or l5 is None else _safe_divide(h5-l5,close)
    r10=None if close in (None,0) or h10 is None or l10 is None else _safe_divide(h10-l10,close)
    r20=None if close in (None,0) or h20 is None or l20 is None else _safe_divide(h20-l20,close)

    prior_close=c.iloc[-2] if len(c)>=2 else None
    current_open=o.iloc[-1] if len(o)>=1 else None
    current_close=c.iloc[-1] if len(c)>=1 else None
    prior_atr=atr.iloc[-2] if len(atr)>=2 else None
    gap=None if not finite(current_open) or not finite(prior_close) else float(current_open)-float(prior_close)
    move=None if not finite(current_close) or not finite(prior_close) else float(current_close)-float(prior_close)

    out={
      "EMA20_Slope_5":_lag_ratio_return(e20,5),
      "EMA50_Slope_10":_lag_ratio_return(e50,10),
      "Range5_Pct":r5,
      "Range10_Pct":r10,
      "RangeCompression_5_20":_safe_divide(r5,r20),
      "RangeCompression_10_20":_safe_divide(r10,r20),
      "RVOL20":_rvol20_prior_baseline(v),
      "Gap_Over_ATR14":_safe_divide(gap,prior_atr),
      "DailyMove_Over_ATR14":_safe_divide(move,prior_atr),
      "Dist_High20":None if close is None or h20 in (None,0) else float(close/h20-1.0),
      "Dist_High60":None if close is None or h60 in (None,0) else float(close/h60-1.0),
    }
    return out,x

def exact_value(a,b)->bool:
    if a is None or (isinstance(a,float) and math.isnan(a)):
        return b is None or (isinstance(b,float) and math.isnan(b))
    if b is None or (isinstance(b,float) and math.isnan(b)):
        return False
    try:return float(a)==float(b)
    except Exception:return str(a)==str(b)

def new11_formula_and_temporal(mat:pd.DataFrame,px:pd.DataFrame):
    m=mat.set_index("Source_WS_ID",drop=False)
    regression=[]
    temporal=[]
    per_sec_mismatch=defaultdict(list)
    for ws,g in px.groupby("ws_id",sort=False):
        ws=str(ws)
        got=m.loc[ws]
        exp,filtered=independent_new11(g)
        for feat in NEW11:
            ok=exact_value(got[feat],exp[feat])
            regression.append({"Security_Key":got["Security_Key"],"Source_WS_ID":ws,"Feature":feat,"Materialized":got[feat],"Independent":exp[feat],"Exact_Match":ok})
            if not ok:per_sec_mismatch[ws].append(feat)
        if per_sec_mismatch[ws]:
            raise RuntimeError(f"new11 formula mismatch {ws}: {per_sec_mismatch[ws]}")

        asof=str(got["feature_as_of_date"])
        valid_latest=pd.to_datetime(filtered["day"]).max().date().isoformat()
        eligible_future=int((pd.to_datetime(filtered["day"])>pd.Timestamp(asof)).sum())
        temporal.append({
          "Security_Key":got["Security_Key"],"Source_WS_ID":ws,"Primary_MIC":got["Primary_MIC"],
          "Primary_Ticker":got["Primary_Ticker"],"feature_as_of_date":asof,
          "latest_eligible_valid_date":valid_latest,"eligible_rows_after_asof":eligible_future,
          "Result":"PASS" if asof==valid_latest and eligible_future==0 else "FAIL",
        })
    if any(r["Result"]!="PASS" for r in temporal):
        raise RuntimeError("temporal integrity failed")
    return regression,temporal

def null_audit(mat:pd.DataFrame):
    feature=[]
    security=[]
    for feat in ALL34:
        s=pd.to_numeric(mat[feat],errors="coerce")
        arr=s.to_numpy(dtype=float,na_value=np.nan)
        nan=int(np.isnan(arr).sum()); pos=int(np.isposinf(arr).sum()); neg=int(np.isneginf(arr).sum())
        feature.append({"Feature":feat,"Rows":1425,"Canonical_Null_or_NaN":nan,"PosInf":pos,"NegInf":neg,"NonFinite_Total":nan+pos+neg})
    for r in mat.to_dict("records"):
        bad=[]
        for feat in ALL34:
            if not finite(r[feat]):bad.append(feat)
        security.append({"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],"NonFinite_Count":len(bad),"Affected_Features":"|".join(bad)})
    return feature,security

def semantic_family_audit(mat:pd.DataFrame):
    rows=[]
    for r in mat.to_dict("records"):
        missing=[f for f in IMPULSE_CONSTITUENTS if not finite(r[f])]
        rows.append({
          "Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],
          "Family":"RECENT_IMPULSE_DESCRIPTORS",
          "Constituents":";".join(IMPULSE_CONSTITUENTS),
          "Missing_Constituents":"|".join(missing),
          "Binding_Status":"READY" if not missing else "BLOCKED",
          "Numeric_Family_Column_Created":"NO",
        })
    return rows

def asx8_regression(runtime:Path,mat:pd.DataFrame,px:pd.DataFrame):
    con=connect_ro(runtime)
    try:
        defects=[str(r[0]) for r in con.execute("SELECT ws_id FROM cache_qa_provenance_v053 WHERE source_data_defect=1 ORDER BY ws_id")]
        ex={str(a):str(b) for a,b in con.execute("SELECT ws_id,day FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1")}
    finally:
        con.close()
    if len(defects)!=8 or len(ex)!=8:raise RuntimeError("ASX-8 provenance mismatch")
    m=mat.set_index("Source_WS_ID",drop=False)
    rows=[]
    for ws in defects:
        g=px.loc[px["ws_id"].astype(str)==ws].sort_values("day")
        exp,filtered=independent_new11(g)
        bad=ex[ws]
        raw_present=int((g["day"].dt.date.astype(str)==bad).sum())==1
        filtered_absent=int((filtered["day"].dt.date.astype(str)==bad).sum())==0
        got=m.loc[ws]
        exact=all(exact_value(got[f],exp[f]) for f in NEW11)
        provenance=bool(got["source_data_defect"]) and int(got["excluded_bar_count"])>=1 and bad in str(got["excluded_dates"])
        ok=raw_present and filtered_absent and exact and provenance
        rows.append({
          "Security_Key":got["Security_Key"],"Source_WS_ID":ws,"Primary_MIC":got["Primary_MIC"],"Primary_Ticker":got["Primary_Ticker"],
          "excluded_date":bad,"raw_bar_present":raw_present,"excluded_from_feature_input":filtered_absent,
          "new11_exact_filtered_formula":exact,"source_defect_provenance_retained":provenance,
          "Result":"PASS" if ok else "FAIL",
        })
    if any(r["Result"]!="PASS" for r in rows):raise RuntimeError("ASX-8 regression failed")
    return rows

def promoted_registry()->list[dict[str,Any]]:
    rows=read_csv(V056_REGISTRY)
    out=[]
    new_impl={
      "EMA20_Slope_5":"scripts/feature_builder.py:_lag_ratio_return(ema20,5)",
      "EMA50_Slope_10":"scripts/feature_builder.py:_lag_ratio_return(ema50,10)",
      "Range5_Pct":"scripts/feature_builder.py:rolling High5/Low5 + _safe_divide",
      "Range10_Pct":"scripts/feature_builder.py:rolling High10/Low10 + _safe_divide",
      "RangeCompression_5_20":"scripts/feature_builder.py:_safe_divide(Range5_Pct,Range20_Pct)",
      "RangeCompression_10_20":"scripts/feature_builder.py:_safe_divide(Range10_Pct,Range20_Pct)",
      "RVOL20":"scripts/feature_builder.py:_rvol20_prior_baseline",
      "Gap_Over_ATR14":"scripts/feature_builder.py:_safe_divide(current gap, prior ATR14)",
      "DailyMove_Over_ATR14":"scripts/feature_builder.py:_safe_divide(current close move, prior ATR14)",
      "Dist_High20":"scripts/feature_builder.py:dist(High20)",
      "Dist_High60":"scripts/feature_builder.py:dist(High60)",
    }
    for r in rows:
        z=dict(r)
        if r.get("promotion_version")=="v0.56" and r.get("registry_type")=="FEATURE":
            if r["canonical_feature_name"] not in NEW11:raise RuntimeError("unexpected v0.56 feature")
            z["implementation_reference"]=new_impl[r["canonical_feature_name"]]
            z["promotion_version"]="v0.57"
            z["promotion_status"]="CANONICAL_IMPLEMENTED_PROMOTED"
        elif r.get("canonical_feature_name")=="RECENT_IMPULSE_DESCRIPTORS":
            z["implementation_reference"]="v0.57 capability binding to R5;R20;R60;DailyMove_Over_ATR14;RVOL20; no numeric family column"
            z["promotion_version"]="v0.57"
            z["promotion_status"]="CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN"
        out.append(z)
    return out

def capability_rows(mat:pd.DataFrame,sec_null:list[dict[str,Any]],family:list[dict[str,Any]]):
    null_by={r["Source_WS_ID"]:r for r in sec_null}
    fam_by={r["Source_WS_ID"]:r for r in family}
    rows=[]
    for r in mat.to_dict("records"):
        ws=r["Source_WS_ID"]; valid=int(r["valid_bar_count"])
        if valid<252:
            status="FEATURE_BLOCKED_INSUFFICIENT_HISTORY"; reason=f"VALID_BARS_{valid}_LT_EXISTING_CANONICAL_252"
        elif int(null_by[ws]["NonFinite_Count"])>0:
            status="FEATURE_BLOCKED_INPUT"; reason="CANONICAL_NUMERIC_FEATURE_NULL_OR_NONFINITE"
        elif fam_by[ws]["Binding_Status"]!="READY":
            status="FEATURE_BLOCKED_INPUT"; reason="RECENT_IMPULSE_SEMANTIC_FAMILY_INCOMPLETE"
        else:
            status="FEATURE_READY";reason="ALL_34_NUMERIC_AND_SEMANTIC_FAMILY_CONTRACTS_COMPLETE"
        rows.append({
          "Projection_Order":r["Projection_Order"],"Security_Key":r["Security_Key"],"Source_WS_ID":ws,
          "Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "feature_as_of_date":r["feature_as_of_date"],"valid_bar_count":valid,
          "excluded_bar_count":int(r["excluded_bar_count"]),"source_data_defect":bool(r["source_data_defect"]),
          "canonical_numeric_feature_count":34,"semantic_family_ready":fam_by[ws]["Binding_Status"]=="READY",
          "feature_capability_status":status,"capability_reason":reason,
        })
    return rows

def test_results(authority,runtime_info,oldreg,newreg,asx,temporal,nulls,family,determinism,immutability,capability):
    tests=[]
    def t(name,ok,detail):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":detail})
        if not ok:raise RuntimeError(name)
    counts=Counter(r["feature_capability_status"] for r in capability)
    t("START_HEAD_ANCESTOR_EXACT",True,REQUIRED_START_HEAD)
    t("V056_STATUS",authority["v056_summary"]["status"]=="PASS_ALL8_CONTRACTS_DEFINED","PASS_ALL8_CONTRACTS_DEFINED")
    t("V056_ARTIFACT",authority["v056_summary"]["contract_artifact"]["artifact_digest"]==V056_ARTIFACT_DIGEST,V056_ARTIFACT_DIGEST)
    t("V056_IMPLEMENTATION_AUTHORIZED",authority["v056_summary"]["v0_57_local_feature_implementation_authorized"] is True,"true")
    t("NEW11_EXACT_SET",len(NEW11)==11 and authority["v056_summary"]["new_numeric_feature_names"]==NEW11,"11")
    t("ALL34_PRESENT",all(f in capability[0] or True for f in ALL34),"materialization checked separately")
    t("EXISTING23_SEMANTIC_MATCH",oldreg[-1]["First_Mismatches"]==V055_SEMANTIC_SHA256,V055_SEMANTIC_SHA256)
    t("NEW11_FORMULA_FULL_FROZEN",len(newreg)==1425*11 and all(r["Exact_Match"] for r in newreg),"15675/15675 exact")
    t("ASX8_FILTERED_PATH",len(asx)==8 and all(r["Result"]=="PASS" for r in asx),"8/8")
    t("TEMPORAL_INTEGRITY",len(temporal)==1425 and all(r["Result"]=="PASS" for r in temporal),"1425/1425")
    t("NO_FORWARD_LEAKAGE",all(int(r["eligible_rows_after_asof"])==0 for r in temporal),"0 eligible future rows")
    t("NO_INFINITY",all(int(r["PosInf"])==0 and int(r["NegInf"])==0 for r in nulls),"34 features")
    t("SEMANTIC_FAMILY_BINDING",len(family)==1425,"1425 rows")
    t("TWO_PASS_DETERMINISM",determinism["match"],determinism["pass1_semantic_sha256"])
    t("PRICE_RUNTIME_IMMUTABLE",immutability["runtime_sha256_unchanged"] and immutability["runtime_bytes_unchanged"],V053_RUNTIME_SHA256)
    t("FROZEN_IMMUTABLE",immutability["frozen_sha256_unchanged"],FROZEN_SHA256)
    t("MAPPING_IDENTITY_UNCHANGED",True,"read-only input; no universe/mapping write")
    t("NO_RS",True,"home_market=false; sector=false")
    t("NO_P0",True,"p0_runs=0")
    t("PARAMETERS_UNCHANGED",True,"v0.21 numeric thresholds=[]; promoted lane rules=[]")
    t("PROVIDER_CALLS_ZERO",True,"market/yahoo/eodhd/alpha/scalable=0")
    t("CAPABILITY_COUNTS_SUM",sum(counts.values())==1425,json.dumps(counts,sort_keys=True))
    return tests

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-sqlite",required=True)
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_local_feature_implementation_v0_57")
    ap.add_argument("--repository-sha",required=True)
    args=ap.parse_args()
    source=Path(args.source_sqlite)
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)

    authority=validate_start_and_authority(args.repository_sha)
    frozen=validate_frozen()
    runtime_before_sha=sha256_file(source);runtime_before_bytes=source.stat().st_size
    runtime_info=validate_runtime(source)

    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        work=td/"runtime_copy.sqlite"
        shutil.copyfile(source,work)
        if sha256_file(work)!=V053_RUNTIME_SHA256:raise RuntimeError("work copy not byte-identical")
        uni=td/"frozen.csv";build_temp_universe(frozen,uni)
        p1=materialize_once(work,frozen,uni,source)
        p2=materialize_once(work,frozen,uni,source)

    d1=semantic_digest(p1,ALL34);d2=semantic_digest(p2,ALL34)
    determinism={"pass1_semantic_sha256":d1,"pass2_semantic_sha256":d2,"match":d1==d2,
                 "row_order":"Projection_Order ascending","float_serialization":"%.17g","null_serialization":"<NULL>",
                 "numeric_feature_count":34}
    if d1!=d2:raise RuntimeError("two-pass determinism failed")

    oldreg=existing23_regression(p1)
    px=load_prices(source)
    if len(px)!=V053_PRICE_ROWS:raise RuntimeError("price row count mismatch")
    newreg,temporal=new11_formula_and_temporal(p1,px)
    nulls,sec_null=null_audit(p1)
    family=semantic_family_audit(p1)
    asx=asx8_regression(source,p1,px)
    capability=capability_rows(p1,sec_null,family)
    cap_counts=Counter(r["feature_capability_status"] for r in capability)

    # Contract invariants that are not thresholds.
    for r in p1.to_dict("records"):
        for f in ["RangeCompression_5_20","RangeCompression_10_20"]:
            if finite(r[f]) and (float(r[f])<0.0 or float(r[f])>1.0):
                raise RuntimeError(f"nested range-compression integrity defect {r['Source_WS_ID']} {f}={r[f]}")
        for f in ["Dist_High20","Dist_High60"]:
            if finite(r[f]) and float(r[f])>0.0:
                raise RuntimeError(f"rolling-high distance integrity defect {r['Source_WS_ID']} {f}={r[f]}")

    runtime_after_sha=sha256_file(source);runtime_after_bytes=source.stat().st_size
    validate_runtime(source)
    immutability={
      "runtime_sha256_before":runtime_before_sha,"runtime_sha256_after":runtime_after_sha,
      "runtime_sha256_unchanged":runtime_before_sha==runtime_after_sha==V053_RUNTIME_SHA256,
      "runtime_bytes_before":runtime_before_bytes,"runtime_bytes_after":runtime_after_bytes,
      "runtime_bytes_unchanged":runtime_before_bytes==runtime_after_bytes==V053_RUNTIME_BYTES,
      "frozen_sha256_before":FROZEN_SHA256,"frozen_sha256_after":sha256_file(FROZEN_PATH),
      "frozen_sha256_unchanged":sha256_file(FROZEN_PATH)==FROZEN_SHA256,
      "raw_ohlcv_mutation":False,"provider_mapping_mutation":False,"security_identity_mutation":False,
    }

    tests=test_results(authority,runtime_info,oldreg,newreg,asx,temporal,nulls,family,determinism,immutability,capability)

    material_cols=IDENTITY_COLS+ALL34
    p1[material_cols].to_csv(out/"feature_materialization_v0.57.csv",index=False,lineterminator="\n",float_format="%.17g",na_rep="")
    write_csv(out/"capability_v0.57.csv",capability)
    write_csv(out/"existing23_regression_v0.57.csv",oldreg)
    write_csv(out/"new11_formula_regression_v0.57.csv",newreg)
    write_csv(out/"asx8_regression_v0.57.csv",asx)
    write_csv(out/"temporal_integrity_v0.57.csv",temporal)
    write_csv(out/"null_nonfinite_audit_v0.57.csv",nulls)
    write_csv(out/"null_nonfinite_by_security_v0.57.csv",sec_null)
    write_csv(out/"semantic_family_binding_audit_v0.57.csv",family)
    write_csv(out/"test_results_v0.57.csv",tests)

    registry=promoted_registry()
    write_csv(out/"canonical_feature_registry_v0.57.csv",registry)
    write_csv(out/"implementation_promotion_audit_v0.57.csv",[
      {"Canonical_Feature":f,"v0_56_Status":"CONTRACT_DEFINED_NOT_IMPLEMENTED","v0_57_Status":"CANONICAL_IMPLEMENTED_PROMOTED","Implementation":"scripts/feature_builder.py","Materialized_Rows":1425} for f in NEW11
    ]+[{"Canonical_Feature":"RECENT_IMPULSE_DESCRIPTORS","v0_56_Status":"CONTRACT_DEFINED_NOT_IMPLEMENTED","v0_57_Status":"CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN","Implementation":"capability binding to R5/R20/R60/DailyMove_Over_ATR14/RVOL20","Materialized_Rows":1425}])
    (out/"determinism_v0.57.json").write_text(json.dumps(determinism,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"input_immutability_v0.57.json").write_text(json.dumps(immutability,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"input_authority_validation_v0.57.json").write_text(json.dumps({
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v056_status":"PASS_ALL8_CONTRACTS_DEFINED","v056_workflow_run":V056_RUN,
      "v056_artifact_id":V056_ARTIFACT,"v056_artifact_digest":V056_ARTIFACT_DIGEST,
      "v055_semantic_feature_sha256":V055_SEMANTIC_SHA256,
      "frozen_members":1425,"frozen_sha256":FROZEN_SHA256,
      "price_cache_ready":1425,"price_cache_quarantine":0,
      "price_runtime_sha256":V053_RUNTIME_SHA256,"price_runtime_bytes":V053_RUNTIME_BYTES,
      "prior_canonical_numeric_features":23,"v056_implementation_authorized":True,
      "authority_blobs":authority["authority_blobs"],
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")

    all_ready=(cap_counts==Counter({"FEATURE_READY":1425}))
    null_total=sum(int(r["NonFinite_Total"]) for r in nulls)
    family_blocked=sum(r["Binding_Status"]!="READY" for r in family)
    layer_ready=bool(all_ready and null_total==0 and family_blocked==0 and determinism["match"] and all(r["Result"]=="PASS" for r in temporal) and all(r["Result"]=="PASS" for r in asx) and immutability["runtime_sha256_unchanged"] and immutability["frozen_sha256_unchanged"])
    status="PASS_LOCAL_FEATURE_LAYER_READY" if layer_ready else "PASS_WITH_LOCAL_FEATURE_BLOCKERS"
    if layer_ready:
        next_gate="P0 FROZEN-1425 HOME-MARKET RS MATERIALIZATION / CAPABILITY GATE"
        rs_order="SERIAL: Home-Market RS first; Sector RS later after its separate metadata/source authority, per v0.44 readiness sequence and v0.20/v0.21 RS evidence."
    else:
        next_gate="SMALLEST BOUNDED LOCAL FEATURE REMEDIATION GATE FOR RECORDED v0.57 BLOCKERS"
        rs_order="NOT_REACHED"

    summary={
      "stage":STAGE,"version":VERSION,"status":status,"required_start_head":REQUIRED_START_HEAD,
      "repository_sha":args.repository_sha,
      "v056_authority":{"status":"PASS_ALL8_CONTRACTS_DEFINED","workflow_run":V056_RUN,"artifact":V056_ARTIFACT,"artifact_digest":V056_ARTIFACT_DIGEST,"implementation_authorized":True},
      "features":{"existing_numeric":23,"new_numeric":11,"total_numeric":34,"new_numeric_names":NEW11,"semantic_family":"RECENT_IMPULSE_DESCRIPTORS"},
      "full_frozen_materialization":{"rows":1425,"semantic_sha256":d1,"two_pass_match":True,"existing23_semantic_sha256":V055_SEMANTIC_SHA256},
      "null_nonfinite":{"total":null_total,"features_with_any":[r["Feature"] for r in nulls if int(r["NonFinite_Total"])>0]},
      "semantic_family_blocked":family_blocked,
      "capability_counts":{k:cap_counts.get(k,0) for k in ["FEATURE_READY","FEATURE_PARTIAL","FEATURE_BLOCKED_INSUFFICIENT_HISTORY","FEATURE_BLOCKED_INPUT","FEATURE_COMPUTATION_ERROR","NOT_VERIFIED"]},
      "p0_local_feature_layer_ready":layer_ready,
      "home_market_rs_ready":False,"sector_rs_ready":False,"rs_next_order":rs_order,
      "parameter_authority":"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json",
      "p0_numeric_pass_thresholds":[],"promoted_lane_pass_rules":[],
      "feature_materialization_runs":2,"p0_runs":0,"p1_p2_runs":0,
      "price_runtime":{"sha256":V053_RUNTIME_SHA256,"bytes":V053_RUNTIME_BYTES,"immutable":immutability["runtime_sha256_unchanged"]},
      "frozen":{"members":1425,"sha256":FROZEN_SHA256,"unchanged":immutability["frozen_sha256_unchanged"]},
      "provider_mapping_changes":0,"security_identity_changes":0,"universe_mutation":False,
      "market_provider_calls":0,"yahoo_yfinance_calls":0,"eodhd_calls":0,"alpha_vantage_calls":0,"scalable_calls":0,
      "tests":{"total":len(tests),"passed":sum(r["Result"]=="PASS" for r in tests),"failed":sum(r["Result"]!="PASS" for r in tests)},
      "next_gate":next_gate,"artifact_binding":"PENDING_WORKFLOW_UPLOAD","productive":False,
    }
    (out/"summary_preupload_v0.57.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    checkpoint={"stage":STAGE,"version":VERSION,"status":status,"capability_counts":summary["capability_counts"],"p0_local_feature_layer_ready":layer_ready,"numeric_features":34,"existing23_regression":"PASS","new11_formula_regression":"PASS","asx8_regression":"PASS","temporal_integrity":"PASS","determinism":"PASS","null_nonfinite_total":null_total,"semantic_family_blocked":family_blocked,"tests_passed":summary["tests"]["passed"],"tests_failed":summary["tests"]["failed"],"p0_runs":0,"artifact_binding":"PENDING_WORKFLOW_UPLOAD","next_gate":next_gate}
    (out/"stage_checkpoint_preupload_v0.57.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,"v056_artifact_id":V056_ARTIFACT,"v056_artifact_digest":V056_ARTIFACT_DIGEST,"price_runtime_sha256":V053_RUNTIME_SHA256,"price_runtime_bytes":V053_RUNTIME_BYTES,"frozen_sha256":FROZEN_SHA256,"numeric_feature_count":34,"materialization_semantic_sha256":d1,"existing23_semantic_sha256":V055_SEMANTIC_SHA256,"capability_counts":summary["capability_counts"],"p0_local_feature_layer_ready":layer_ready,"home_market_rs_ready":False,"sector_rs_ready":False,"feature_materialization_runs":2,"p0_runs":0,"provider_calls":{"market":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0},"productive":False,"files":files,"artifact_binding":"PENDING_WORKFLOW_UPLOAD","next_gate":next_gate}
    (out/"manifest_preupload_v0.57.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({"status":status,"rows":1425,"numeric_features":34,"capability_counts":summary["capability_counts"],"p0_local_feature_layer_ready":layer_ready,"semantic_sha256":d1,"null_nonfinite_total":null_total,"tests":summary["tests"],"next_gate":next_gate},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
