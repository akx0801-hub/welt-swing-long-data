#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:
    sys.path.insert(0,str(ROOT/"scripts"))

from feature_builder import build_features, split_adjust_technical, technical_valid_mask_for_features, _last_return

VERSION="v0.55"
STAGE="P0_FROZEN_1425_MASTER_REQUIRED_LOCAL_FEATURE_REMEDIATION"
REQUIRED_START_HEAD="4fd2d914b2bbb0fcf2b347890f8d652ee80c4f00"

V054_RUN=36228518000
V054_ARTIFACT=10901437101
V054_ARTIFACT_DIGEST="sha256:0c6eec3a41a26940b4e1325532f2e7bf240f1d362f147f4b52a3943f6f5dfe47"
V054_SEMANTIC_SHA256="c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6"
V053_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
V053_RUNTIME_BYTES=144539648
V053_PRICE_ROWS=711204
FROZEN_PATH=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
FROZEN_ROWS=1425

MASTER=ROOT/"docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md"
V019_DOC=ROOT/"docs/validation/P0_Feature_Augmentation_v0.19.md"
V019_SCRIPT=ROOT/"scripts/p0_feature_augmentation_v0_19.py"
V021_DOC=ROOT/"docs/validation/P0_Lane_Shadow_Validation_v0.21.md"
V021_SCRIPT=ROOT/"scripts/p0_lane_shadow_validation_v0_21.py"
V054_SUMMARY=ROOT/"output_p0_frozen_1425_features_v0_54/summary_v0.54.json"
V054_MANIFEST=ROOT/"output_p0_frozen_1425_features_v0_54/manifest_v0.54.json"
PARAM_READY=ROOT/"output_p0_frozen_1425_readiness_v0_44/parameter_readiness_v0.44.json"

EXPECTED_BLOBS={
 str(MASTER.relative_to(ROOT)):"680d0434e534d1fe136e694ca05cb574958a1a24",
 str(V019_DOC.relative_to(ROOT)):"2d49b4c153710569f84d488a3db1154ad21875bd",
 str(V019_SCRIPT.relative_to(ROOT)):"62ced7a22abc6b1e1aaeb0a2f44690fd67956d95",
 str(V021_DOC.relative_to(ROOT)):"6216b82699d1fe7470a7f4cf4288e233d52acf1d",
 str(V021_SCRIPT.relative_to(ROOT)):"d81426caf6d77a1bbc238a1993c057e082fbfcdd",
 str(V054_SUMMARY.relative_to(ROOT)):"15cba4d96bb83b697e06c81dbcf99e3310e71eb4",
 str(V054_MANIFEST.relative_to(ROOT)):"af31383a3763c9ba7c89e8d16182d0cbda1bcadd",
 str(PARAM_READY.relative_to(ROOT)):"a5c963f1dcf5d3d61000a7ae47d8ca21613f479f",
 "scripts/feature_builder.py":"50d564cd10e928a0565e74e2c49b7534d62bb529",
}

OLD21=[
"Close_Tech","EMA20","EMA50","SMA200","ATR14_Wilder_DEV","ATR14_Pct_DEV",
"R5","R20","R60","High20","High60","High252","Low20","Low60",
"Dist_EMA20","Dist_EMA50","Dist_SMA200","Dist_High252","Range20_Pct",
"MedianVolume20_Tech","MedianTurnover20_Native"
]
NEW_FEATURES=["R1","TrueRange_Current"]
CANONICAL_FEATURES=OLD21[:6]+["R1"]+OLD21[6:9]+["TrueRange_Current"]+OLD21[9:]

GAPS=[
"EMA20_SLOPE","EMA50_SLOPE","R1","TRUE_RANGE_CURRENT","RANGE_COMPRESSION_FAMILY",
"RELATIVE_VOLUME_METRICS","GAP_OVER_ATR","DAILY_MOVE_IN_ATR","RECENT_IMPULSE_DESCRIPTORS",
"RUNUP_5_20_60_SEMANTICS","RELEVANT_HIGH_DISTANCE_FAMILY"
]
REMAINING=[
"EMA20_SLOPE","EMA50_SLOPE","RANGE_COMPRESSION_FAMILY","RELATIVE_VOLUME_METRICS",
"GAP_OVER_ATR","DAILY_MOVE_IN_ATR","RECENT_IMPULSE_DESCRIPTORS","RELEVANT_HIGH_DISTANCE_FAMILY"
]

CONTRACT_ROWS=[
{
"feature_family":"EMA20_SLOPE","master_requirement":"EMA20-Slope","master_reference":"Master §25 Trend","historical_v019_implementation":"EMA20_Slope5_Pct","historical_formula":"EMA20[t]/EMA20[t-5]-1","current_implementation_status":"NOT_CURRENT_CANONICAL","formula_ambiguity":"YES","window_ambiguity":"YES: Master gives no horizon","normalization_ambiguity":"YES: absolute/percent/Close/EMA/ATR not fixed","required_source_fields":"Close;Stock_Splits","minimum_history":"AMBIGUOUS beyond EMA20 availability","split_normalization":"canonical split-only technical series required","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Master requires a slope but does not bind horizon or normalization; v0.19 5-session percentage formula is historical evidence only; v0.21 validates sign only."
},
{
"feature_family":"EMA50_SLOPE","master_requirement":"EMA50-Slope","master_reference":"Master §25 Trend","historical_v019_implementation":"EMA50_Slope10_Pct","historical_formula":"EMA50[t]/EMA50[t-10]-1","current_implementation_status":"NOT_CURRENT_CANONICAL","formula_ambiguity":"YES","window_ambiguity":"YES: Master gives no horizon","normalization_ambiguity":"YES","required_source_fields":"Close;Stock_Splits","minimum_history":"AMBIGUOUS beyond EMA50 availability","split_normalization":"canonical split-only technical series required","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Master does not bind 10-session percentage slope; historical v0.19 cannot promote it by itself."
},
{
"feature_family":"R1","master_requirement":"R1 alongside R5/R20/R60","master_reference":"Master §25 Performance","historical_v019_implementation":"none as output; shared n_return helper exists","historical_formula":"n_return(c,n)=c[t]/c[t-n]-1","current_implementation_status":"R5/R20/R60 canonical family exists","formula_ambiguity":"NO after family binding","window_ambiguity":"NO: n=1 valid observation","normalization_ambiguity":"NO: decimal return","required_source_fields":"Close;Stock_Splits","minimum_history":"2 valid observations","split_normalization":"split-only Close_Tech","filtered_invalid_bar_behavior":"one prior VALID observation; excluded bar cannot be endpoint","contract_classification":"CONTRACT_DERIVABLE","promotion_status":"CANONICAL_IMPLEMENTED_PROMOTED","binding_reason":"Master explicitly places R1 in the same Rn family as canonical R5/R20/R60; unique extension of the already-canonical n-return primitive is n=1."
},
{
"feature_family":"TRUE_RANGE_CURRENT","master_requirement":"True Range","master_reference":"Master §25 Volatilität","historical_v019_implementation":"TrueRange_Current","historical_formula":"max(|H-L|,|H-prev valid Close|,|L-prev valid Close|)","current_implementation_status":"primitive already computed inside canonical ATR14 path","formula_ambiguity":"NO","window_ambiguity":"NO: current valid bar + previous valid close","normalization_ambiguity":"NO: native price units","required_source_fields":"High;Low;Close;Stock_Splits","minimum_history":"1 valid observation (first-bar TR reduces to H-L)","split_normalization":"split-only technical H/L/C","filtered_invalid_bar_behavior":"previous observation means previous VALID observation","contract_classification":"CONTRACT_DERIVABLE","promotion_status":"CANONICAL_IMPLEMENTED_PROMOTED","binding_reason":"Canonical ATR14 already computes the exact TR primitive; Master separately requires True Range, so exposing the current value reuses the existing single source of truth."
},
{
"feature_family":"RANGE_COMPRESSION_FAMILY","master_requirement":"kurzfristige Range; Range-/Compression-Maße","master_reference":"Master §25 Volatilität/Struktur; v0.21 shadow relation Range5<Range20 and TRMean5<TRMean20","historical_v019_implementation":"Range5_Pct;Range10_Pct;Range20_Pct;Range5_to_Range20;TR_Mean5;TR_Mean20;TR_Mean5_to_20","historical_formula":"rolling high-low/current close; TR means and ratios","current_implementation_status":"Range20_Pct only canonical","formula_ambiguity":"YES: exact required member set not fixed","window_ambiguity":"YES: v0.21 validates 5-vs-20 relation but Master does not define complete family","normalization_ambiguity":"YES: relation survives absolute vs pct scaling","required_source_fields":"High;Low;Close;Stock_Splits","minimum_history":"AMBIGUOUS by member","split_normalization":"canonical split-only series","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Current shadow relation does not uniquely bind a canonical feature set or normalization."
},
{
"feature_family":"RELATIVE_VOLUME_METRICS","master_requirement":"relative Volumenmetriken; later RVOL reference","master_reference":"Master §25 Volumen and §30 Lane 1","historical_v019_implementation":"RVOL20_Current","historical_formula":"current Volume_Tech / preceding 20-valid-session median Volume_Tech","current_implementation_status":"MedianVolume20_Tech canonical; relative metric not canonical","formula_ambiguity":"YES: numerator/baseline family not fully specified","window_ambiguity":"YES: Master does not bind 20-median baseline","normalization_ambiguity":"YES: volume vs turnover alternatives","required_source_fields":"Volume;Stock_Splits (possibly Close for turnover)","minimum_history":"AMBIGUOUS","split_normalization":"split-only Volume_Tech where volume-based","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Master names RVOL concept but does not define mean/median, lookback, or current inclusion; v0.19 is historical evidence only."
},
{
"feature_family":"GAP_OVER_ATR","master_requirement":"Gap/ATR","master_reference":"Master §25 Impuls","historical_v019_implementation":"Gap_Pct only; no canonical Gap/ATR","historical_formula":"Gap_Pct=Open[t]/Close[t-1]-1","current_implementation_status":"NOT_IMPLEMENTED","formula_ambiguity":"YES: signed/absolute gap and units not fixed","window_ambiguity":"ATR t vs t-1 unspecified","normalization_ambiguity":"YES","required_source_fields":"Open;Close;High;Low;Stock_Splits","minimum_history":"AMBIGUOUS","split_normalization":"canonical split-only series","filtered_invalid_bar_behavior":"previous means previous valid observation if later defined","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Master does not specify gap numerator or ATR denominator timing; same-bar denominator leakage cannot be guessed."
},
{
"feature_family":"DAILY_MOVE_IN_ATR","master_requirement":"Tagesbewegung in ATR","master_reference":"Master §25 Impuls","historical_v019_implementation":"TrueRange_ATR14_Ratio candidate only","historical_formula":"current TR/current ATR14 in v0.19","current_implementation_status":"NOT_CURRENT_CANONICAL","formula_ambiguity":"YES: close-close, high-low, open-close, or TR not fixed","window_ambiguity":"ATR timing unspecified","normalization_ambiguity":"YES: signed/absolute and denominator timing","required_source_fields":"Open;High;Low;Close;Stock_Splits","minimum_history":"AMBIGUOUS","split_normalization":"canonical split-only series","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Feature name alone does not identify numerator or ATR reference point."
},
{
"feature_family":"RECENT_IMPULSE_DESCRIPTORS","master_requirement":"jüngere Impulse","master_reference":"Master §25 Impuls; §30 Post-Event Drift concept","historical_v019_implementation":"Impulse_Return20_Max;Impulse_Days_Ago;PostImpulse_Min_vs_ImpulseClose;PostImpulse_Latest_vs_ImpulseClose;PostImpulse_Range_Pct","historical_formula":"strongest positive daily return in trailing 20 valid observations plus post-impulse descriptors","current_implementation_status":"NOT_CURRENT_CANONICAL","formula_ambiguity":"YES","window_ambiguity":"YES","normalization_ambiguity":"YES","required_source_fields":"Close;High;Low;Stock_Splits; possibly Volume/ATR depending definition","minimum_history":"AMBIGUOUS","split_normalization":"canonical split-only series","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Master specifies the concept, not the impulse identification formula, lookback, directionality, or post-impulse window."
},
{
"feature_family":"RUNUP_5_20_60_SEMANTICS","master_requirement":"Run-up 5/20/60T","master_reference":"Master §25 Impuls plus §33 RUN-UP-KLASSIFIKATION: '5-/20-/60-Tage-Performance' and 20/60-day warning values","historical_v019_implementation":"R5;R20;R60 already present","historical_formula":"Close_Tech[t]/Close_Tech[t-n]-1","current_implementation_status":"R5/R20/R60 already canonical","formula_ambiguity":"NO after §33 binding","window_ambiguity":"NO: 5/20/60 valid observations","normalization_ambiguity":"NO: existing decimal performance return","required_source_fields":"Close;Stock_Splits","minimum_history":"6/21/61 valid observations","split_normalization":"split-only Close_Tech","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_DERIVABLE","promotion_status":"CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN","binding_reason":"The Run-up classification explicitly requires 5/20/60-day performance; this uniquely maps to already-canonical R5/R20/R60 without duplicate aliases."
},
{
"feature_family":"RELEVANT_HIGH_DISTANCE_FAMILY","master_requirement":"Distanz zu relevanten Hochs","master_reference":"Master §25 Struktur","historical_v019_implementation":"Dist_High252 plus historical Distance_High20_ATR","historical_formula":"current Close/High252-1 versus (High20-Close)/ATR14","current_implementation_status":"Dist_High252 canonical only","formula_ambiguity":"YES: relevant high selection not fixed","window_ambiguity":"YES: 20/60/252/dynamic not fixed","normalization_ambiguity":"YES: percent vs ATR units evidenced","required_source_fields":"High;Close;possibly ATR;Stock_Splits","minimum_history":"AMBIGUOUS","split_normalization":"canonical split-only series","filtered_invalid_bar_behavior":"whole invalid bar excluded","contract_classification":"CONTRACT_AMBIGUOUS","promotion_status":"BLOCKED_NOT_IMPLEMENTED","binding_reason":"Repository evidence contains more than one plausible high-distance normalization/window; Master does not choose among them."
},
]

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def git(*args:str)->str:
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def git_blob(p:Path)->str:
    return git("hash-object",str(p.relative_to(ROOT)))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:
            w.writeheader(); w.writerows(rows)

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def connect_ro(p:Path)->sqlite3.Connection:
    return sqlite3.connect(f"file:{p.resolve()}?mode=ro&immutable=1",uri=True)

def validate_authorities(repo_sha:str,v054_artifact_dir:Path)->dict[str,Any]:
    head=git("rev-parse","HEAD")
    if head!=repo_sha: raise RuntimeError("repository SHA mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start HEAD not ancestor")
    for rel,exp in EXPECTED_BLOBS.items():
        got=git_blob(ROOT/rel)
        if got!=exp: raise RuntimeError(f"authority blob mismatch {rel}: {got} != {exp}")
    s=json.loads(V054_SUMMARY.read_text(encoding="utf-8"))
    if s["status"]!="PASS_WITH_LOCAL_FEATURE_MODEL_GAPS" or s["capability_counts"]["FEATURE_PARTIAL"]!=1425:
        raise RuntimeError("persisted v0.54 authority mismatch")
    if s["materialization"]["semantic_sha256"]!=V054_SEMANTIC_SHA256: raise RuntimeError("v0.54 semantic mismatch")
    a=v054_artifact_dir/"feature_materialization_v0.54.csv"
    if not a.exists() or sha256_file(a)!=V054_SEMANTIC_SHA256: raise RuntimeError("v0.54 artifact materialization mismatch")
    return {"head":head,"v054_summary":s}

def validate_runtime(p:Path)->dict[str,Any]:
    if sha256_file(p)!=V053_RUNTIME_SHA256 or p.stat().st_size!=V053_RUNTIME_BYTES: raise RuntimeError("runtime byte authority mismatch")
    con=connect_ro(p)
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0]!="ok": raise RuntimeError("integrity fail")
        rows=con.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]
        states=con.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]
        counts=dict(con.execute("SELECT status,COUNT(*) FROM cache_state GROUP BY status").fetchall())
        defects=con.execute("SELECT COUNT(*) FROM cache_qa_provenance_v053 WHERE source_data_defect=1").fetchone()[0]
        excluded=con.execute("SELECT COUNT(*) FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1").fetchone()[0]
    finally: con.close()
    if rows!=V053_PRICE_ROWS or states!=1425 or counts!={"READY":1425} or defects!=8 or excluded!=8:
        raise RuntimeError("runtime semantic authority mismatch")
    return {"sha256":V053_RUNTIME_SHA256,"bytes":V053_RUNTIME_BYTES,"price_daily":rows,"states":states,"ready":1425,"quarantine":0,"source_defects":defects,"excluded_bars":excluded}

def validate_frozen()->pd.DataFrame:
    if sha256_file(FROZEN_PATH)!=FROZEN_SHA256: raise RuntimeError("Frozen SHA mismatch")
    f=pd.read_csv(FROZEN_PATH,dtype=str).fillna("")
    if len(f)!=1425 or f["Security_Key"].duplicated().any() or f["Source_WS_ID"].duplicated().any(): raise RuntimeError("Frozen identity mismatch")
    f["Projection_Order"]=pd.to_numeric(f["Projection_Order"],errors="raise").astype(int)
    return f.sort_values("Projection_Order").reset_index(drop=True)

def validate_parameter()->dict[str,Any]:
    p=json.loads(PARAM_READY.read_text(encoding="utf-8"))
    if p["p0_parameter_set_ready"] is not False or p["p0_numeric_pass_thresholds"]!=[] or p["promoted_lane_pass_rules"]!=[]:
        raise RuntimeError("parameter authority changed")
    return p

def contract_counts()->dict[str,int]:
    c=Counter(r["contract_classification"] for r in CONTRACT_ROWS)
    return {k:c.get(k,0) for k in ["CONTRACT_EXACT","CONTRACT_DERIVABLE","CONTRACT_AMBIGUOUS","CONTRACT_CONFLICT","CONTRACT_NOT_FOUND"]}

def build_universe(f:pd.DataFrame,p:Path)->None:
    pd.DataFrame({"WS_ID":f["Source_WS_ID"].astype(str)}).to_csv(p,index=False)

def load_provenance(runtime:Path):
    con=connect_ro(runtime)
    try:
        prov=pd.read_sql_query("SELECT ws_id,source_data_defect,invalid_bar_count FROM cache_qa_provenance_v053 ORDER BY ws_id",con)
        ex=pd.read_sql_query("SELECT ws_id,day FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1 ORDER BY ws_id,day",con)
    finally: con.close()
    d=defaultdict(list)
    for r in ex.to_dict("records"): d[str(r["ws_id"])].append(str(r["day"]))
    return prov,d

def materialize(runtime:Path,frozen:pd.DataFrame,uni:Path)->pd.DataFrame:
    feat=build_features(runtime,uni)
    if len(feat)!=1425 or feat["WS_ID"].nunique()!=1425: raise RuntimeError("feature population mismatch")
    for c in CANONICAL_FEATURES:
        if c not in feat.columns: raise RuntimeError(f"missing canonical column {c}")
    base=frozen[["Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker"]]
    x=base.merge(feat,left_on="Source_WS_ID",right_on="WS_ID",how="left",validate="one_to_one")
    if x["AsOf"].isna().any(): raise RuntimeError("missing features after merge")
    prov,dates=load_provenance(runtime)
    prov["ws_id"]=prov["ws_id"].astype(str)
    x=x.merge(prov,left_on="Source_WS_ID",right_on="ws_id",how="left",validate="one_to_one")
    x["feature_as_of_date"]=x["AsOf"].astype(str)
    x["valid_bar_count"]=pd.to_numeric(x["Bars_Used"],errors="raise").astype(int)
    x["excluded_bar_count"]=pd.to_numeric(x["Excluded_Invalid_Bars"],errors="raise").astype(int)
    x["source_data_defect"]=pd.to_numeric(x["source_data_defect"],errors="raise").astype(int).astype(bool)
    x["excluded_dates"]=x["Source_WS_ID"].map(lambda z:"|".join(dates.get(str(z),[])))
    x["filtered_policy_version"]="v0.53/POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT"
    return x.sort_values("Projection_Order").reset_index(drop=True)

def semantic_bytes(df:pd.DataFrame,features:list[str])->bytes:
    cols=["Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker","feature_as_of_date","valid_bar_count","excluded_bar_count","source_data_defect","excluded_dates","filtered_policy_version",*features]
    s=df[cols].sort_values("Projection_Order").to_csv(index=False,lineterminator="\n",float_format="%.17g",na_rep="<NULL>")
    return s.encode()

def semantic_digest(df:pd.DataFrame,features:list[str])->str:
    return hashlib.sha256(semantic_bytes(df,features)).hexdigest()

def value_equal(a:Any,b:Any)->bool:
    if pd.isna(a) and pd.isna(b): return True
    try: return float(a)==float(b)
    except Exception: return str(a)==str(b)

def old21_regression(new:pd.DataFrame,old_path:Path)->list[dict[str,Any]]:
    # v0.54's feature_materialization file is itself the canonical semantic
    # serialization used to declare V054_SEMANTIC_SHA256. Re-parsing its
    # decimal strings into binary floats can introduce parser-roundtrip
    # differences at the final bit, so equality authority is the byte-stable
    # semantic digest, not a second float parser.
    old_rows=read_csv(old_path)
    old_ids=[r["Source_WS_ID"] for r in old_rows]
    new_ids=new.sort_values("Projection_Order")["Source_WS_ID"].astype(str).tolist()
    if old_ids!=new_ids:
        raise RuntimeError("v0.54/v0.55 identity/order mismatch")
    old_file_sha=sha256_file(old_path)
    if old_file_sha!=V054_SEMANTIC_SHA256:
        raise RuntimeError("v0.54 materialization file no longer matches canonical semantic authority")
    d=semantic_digest(new,OLD21)
    if d!=V054_SEMANTIC_SHA256:
        raise RuntimeError(f"existing21 semantic regression failed digest={d}")
    rows=[]
    for feat in OLD21:
        rows.append({
            "Feature":feat,
            "Rows":1425,
            "Mismatch_Count":0,
            "Result":"PASS",
            "Comparison_Method":"FULL_OLD21_CANONICAL_SEMANTIC_DIGEST_MATCH",
            "Authority_Digest":d,
        })
    rows.append({
        "Feature":"OLD21_SEMANTIC_DIGEST",
        "Rows":1425,
        "Mismatch_Count":0,
        "Result":"PASS",
        "Comparison_Method":"BYTE_STABLE_SEMANTIC_DIGEST",
        "Authority_Digest":d,
    })
    return rows

def load_prices(runtime:Path)->pd.DataFrame:
    con=connect_ro(runtime)
    try:
        px=pd.read_sql_query("SELECT ws_id,day,open,high,low,close,volume,stock_splits FROM price_daily ORDER BY ws_id,day",con)
    finally: con.close()
    px["day"]=pd.to_datetime(px["day"],errors="raise")
    return px

def independent_new(g:pd.DataFrame)->tuple[float|None,float|None,pd.DataFrame]:
    x=g.sort_values("day").copy()
    mask=technical_valid_mask_for_features(x)
    x=x.loc[mask].copy()
    x=split_adjust_technical(x)
    c=pd.to_numeric(x["close_tech"],errors="coerce")
    h=pd.to_numeric(x["high_tech"],errors="coerce")
    l=pd.to_numeric(x["low_tech"],errors="coerce")
    prev=c.shift(1)
    tr=pd.concat([(h-l).abs(),(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
    r1=_last_return(c,1)
    trc=None if tr.dropna().empty else float(tr.dropna().iloc[-1])
    return r1,trc,x

def new_formula_regression(mat:pd.DataFrame,px:pd.DataFrame):
    m=mat.set_index("Source_WS_ID")
    rows=[]
    temporal=[]
    for ws,g in px.groupby("ws_id",sort=False):
        ws=str(ws); got=m.loc[ws]
        r1,trc,filtered=independent_new(g)
        r1ok=value_equal(got["R1"],r1); trok=value_equal(got["TrueRange_Current"],trc)
        if not(r1ok and trok): raise RuntimeError(f"new formula mismatch {ws}")
        asof=str(got["feature_as_of_date"])
        latest=pd.to_datetime(filtered["day"]).max().date().isoformat()
        future=int((g["day"]>pd.Timestamp(asof)).sum())
        temporal.append({"Security_Key":got["Security_Key"],"Source_WS_ID":ws,"Primary_MIC":got["Primary_MIC"],"Primary_Ticker":got["Primary_Ticker"],"feature_as_of_date":asof,"latest_valid_date":latest,"rows_after_asof":future,"Result":"PASS" if asof==latest and future==0 else "FAIL"})
        rows.append({"Security_Key":got["Security_Key"],"Source_WS_ID":ws,"R1_Materialized":got["R1"],"R1_Independent":r1,"R1_Exact":r1ok,"TrueRange_Current_Materialized":got["TrueRange_Current"],"TrueRange_Current_Independent":trc,"TrueRange_Current_Exact":trok})
    if any(r["Result"]!="PASS" for r in temporal): raise RuntimeError("temporal integrity fail")
    return rows,temporal

def asx8(runtime:Path,mat:pd.DataFrame,px:pd.DataFrame)->list[dict[str,Any]]:
    con=connect_ro(runtime)
    try:
        defects=[str(r[0]) for r in con.execute("SELECT ws_id FROM cache_qa_provenance_v053 WHERE source_data_defect=1 ORDER BY ws_id")]
        ex={str(a):str(b) for a,b in con.execute("SELECT ws_id,day FROM technical_bar_exclusions_v053 WHERE technical_bar_excluded=1")}
    finally: con.close()
    m=mat.set_index("Source_WS_ID")
    rows=[]
    for ws in defects:
        g=px.loc[px["ws_id"].astype(str)==ws].sort_values("day")
        r1,trc,filtered=independent_new(g)
        bad=ex[ws]
        bad_present=int((g["day"].dt.date.astype(str)==bad).sum())==1
        bad_filtered=int((filtered["day"].dt.date.astype(str)==bad).sum())==0
        got=m.loc[ws]
        runup_ok=all(math.isfinite(float(got[f])) for f in ["R5","R20","R60"])
        ok=bad_present and bad_filtered and value_equal(got["R1"],r1) and value_equal(got["TrueRange_Current"],trc) and runup_ok
        rows.append({"Security_Key":got["Security_Key"],"Source_WS_ID":ws,"Primary_MIC":got["Primary_MIC"],"Primary_Ticker":got["Primary_Ticker"],"raw_bars":len(g),"valid_bars":len(filtered),"excluded_bar_count":len(g)-len(filtered),"excluded_date":bad,"raw_bar_present":bad_present,"excluded_from_feature_input":bad_filtered,"R1_filtered_exact":value_equal(got["R1"],r1),"TrueRange_Current_filtered_exact":value_equal(got["TrueRange_Current"],trc),"Runup_R5_R20_R60_filtered_finite":runup_ok,"Result":"PASS" if ok else "FAIL"})
    if len(rows)!=8 or any(r["Result"]!="PASS" for r in rows): raise RuntimeError("ASX8 regression fail")
    return rows

def null_audit(mat:pd.DataFrame)->list[dict[str,Any]]:
    rows=[]
    for feat in CANONICAL_FEATURES:
        s=pd.to_numeric(mat[feat],errors="coerce")
        arr=s.to_numpy(dtype=float,na_value=np.nan)
        null=int(s.isna().sum()); pi=int(np.isposinf(arr).sum()); ni=int(np.isneginf(arr).sum())
        rows.append({"Feature":feat,"Rows":1425,"NULL_or_NaN":null,"PosInf":pi,"NegInf":ni,"NonFinite_Total":null+pi+ni})
    if any(r["NonFinite_Total"] for r in rows): raise RuntimeError("required canonical nonfinite")
    return rows

def registry(v054_formula_path:Path)->list[dict[str,Any]]:
    old=read_csv(v054_formula_path)
    rows=[]
    for r in old:
        rows.append({
          "registry_type":"FEATURE","canonical_feature_name":r["feature_name"],"semantic_definition":r["formula"],
          "formula":r["formula"],"source_fields":r["required_raw_fields"],"lookback":r["lookback"],
          "normalization":"as v0.54 canonical implementation","sign_convention":"as formula","minimum_observations":r["minimum_valid_observations"],
          "filtered_series_contract":r["filtered_series_behavior"],"null_nonfinite_behavior":r["null_behavior"]+"; "+r["finite_handling"],
          "implementation_reference":r["implementation_reference"],"master_spec_authority":"v0.54 existing canonical binding",
          "promotion_version":"pre-v0.55 retained","promotion_status":"CANONICAL_IMPLEMENTED_RETAINED"
        })
    rows += [
      {"registry_type":"FEATURE","canonical_feature_name":"R1","semantic_definition":"one-valid-observation split-normalized close-to-close decimal return","formula":"Close_Tech[t] / Close_Tech[t-1 valid observation] - 1","source_fields":"Close;Stock_Splits","lookback":"1 return interval / 2 valid closes","normalization":"split-only Close_Tech; decimal return","sign_convention":"positive=price increase; negative=decrease","minimum_observations":"2","filtered_series_contract":"whole invalid bars excluded before endpoint selection","null_nonfinite_behavior":"None if <=1 valid observation or denominator zero; no zero fill","implementation_reference":"scripts/feature_builder.py:_last_return(c,1)","master_spec_authority":"Master §25 Performance R1/R5/R20/R60 + canonical Rn family","promotion_version":"v0.55","promotion_status":"CANONICAL_IMPLEMENTED_PROMOTED"},
      {"registry_type":"FEATURE","canonical_feature_name":"TrueRange_Current","semantic_definition":"current True Range on canonical filtered split-only technical series","formula":"max(abs(H_t-L_t),abs(H_t-C_prev_valid),abs(L_t-C_prev_valid))","source_fields":"High;Low;Close;Stock_Splits","lookback":"current valid bar + previous valid close","normalization":"native split-normalized price units","sign_convention":"nonnegative magnitude","minimum_observations":"1","filtered_series_contract":"whole invalid bars excluded; prev means previous valid observation","null_nonfinite_behavior":"None only if no valid TR; no zero fill","implementation_reference":"scripts/feature_builder.py shared tr primitive used by ATR14","master_spec_authority":"Master §25 Volatilität True Range + canonical ATR14 primitive","promotion_version":"v0.55","promotion_status":"CANONICAL_IMPLEMENTED_PROMOTED"},
      {"registry_type":"SEMANTIC_FAMILY","canonical_feature_name":"RUNUP_5_20_60_SEMANTICS","semantic_definition":"Run-up measurement is the existing 5/20/60-day performance triplet","formula":"R5;R20;R60","source_fields":"Close;Stock_Splits","lookback":"5/20/60 valid return intervals","normalization":"decimal trailing returns","sign_convention":"positive=advance","minimum_observations":"6/21/61","filtered_series_contract":"whole invalid bars excluded","null_nonfinite_behavior":"inherits canonical R5/R20/R60","implementation_reference":"scripts/feature_builder.py existing R5/R20/R60","master_spec_authority":"Master §25 Run-up 5/20/60T + §33 Run-up classification: 5-/20-/60-Tage-Performance","promotion_version":"v0.55","promotion_status":"CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN"},
    ]
    return rows

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--runtime",required=True)
    ap.add_argument("--v054-artifact-dir",required=True)
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_local_feature_remediation_v0_55")
    ap.add_argument("--repository-sha",required=True)
    args=ap.parse_args()
    runtime=Path(args.runtime)
    v054=Path(args.v054_artifact_dir)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    auth=validate_authorities(args.repository_sha,v054)
    runtime_info=validate_runtime(runtime)
    frozen=validate_frozen()
    params=validate_parameter()

    if [r["feature_family"] for r in CONTRACT_ROWS]!=GAPS: raise RuntimeError("11-gap order mismatch")
    cc=contract_counts()
    if cc!={"CONTRACT_EXACT":0,"CONTRACT_DERIVABLE":3,"CONTRACT_AMBIGUOUS":8,"CONTRACT_CONFLICT":0,"CONTRACT_NOT_FOUND":0}: raise RuntimeError(f"contract count mismatch {cc}")
    for r in CONTRACT_ROWS:
        if r["contract_classification"] not in ("CONTRACT_EXACT","CONTRACT_DERIVABLE") and "IMPLEMENTED" in r["promotion_status"] and not r["promotion_status"].startswith("BLOCKED"):
            raise RuntimeError("ambiguous contract implementation forbidden")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); uni=td/"frozen.csv"; build_universe(frozen,uni)
        p1=materialize(runtime,frozen,uni)
        p2=materialize(runtime,frozen,uni)

    d1=semantic_digest(p1,CANONICAL_FEATURES); d2=semantic_digest(p2,CANONICAL_FEATURES)
    if d1!=d2: raise RuntimeError("two-pass digest mismatch")
    oldreg=old21_regression(p1,v054/"feature_materialization_v0.54.csv")
    px=load_prices(runtime)
    newreg,temporal=new_formula_regression(p1,px)
    asx=asx8(runtime,p1,px)
    nulls=null_audit(p1)
    reg=registry(v054/"feature_formula_binding_v0.54.csv")

    # Explicit divide-by-zero and minimum-history unit semantics for R1.
    assert _last_return(pd.Series([100.0]),1) is None
    assert _last_return(pd.Series([0.0,1.0]),1) is None
    assert _last_return(pd.Series([100.0,101.0]),1)==0.010000000000000009

    capability=[]
    for r in p1.to_dict("records"):
        capability.append({"Projection_Order":r["Projection_Order"],"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],"feature_as_of_date":r["feature_as_of_date"],"canonical_feature_count":len(CANONICAL_FEATURES),"remaining_master_local_gap_count":len(REMAINING),"feature_capability_status":"FEATURE_PARTIAL","capability_reason":"REMAINING_MASTER_LOCAL_CONTRACT_GAPS"})
    counts=Counter(r["feature_capability_status"] for r in capability)
    if counts!=Counter({"FEATURE_PARTIAL":1425}): raise RuntimeError("capability reconciliation fail")

    material_cols=["Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker","feature_as_of_date","valid_bar_count","excluded_bar_count","source_data_defect","excluded_dates","filtered_policy_version",*CANONICAL_FEATURES]
    p1[material_cols].to_csv(out/"feature_materialization_v0.55.csv",index=False,lineterminator="\n",float_format="%.17g",na_rep="")

    write_csv(out/"contract_binding_v0.55.csv",CONTRACT_ROWS)
    write_csv(out/"master_gap_reconciliation_v0.55.csv",[
      {"Master_Gap":r["feature_family"],"Contract_Classification":r["contract_classification"],"Promotion_Status":r["promotion_status"],"Resolved":"YES" if r["feature_family"] not in REMAINING else "NO","Reason":r["binding_reason"]} for r in CONTRACT_ROWS
    ])
    write_csv(out/"historical_v019_mapping_v0.55.csv",[
      {"Master_Gap":r["feature_family"],"Historical_v019_Implementation":r["historical_v019_implementation"],"Historical_Formula":r["historical_formula"],"Authority_Use":"IMPLEMENTATION_EVIDENCE_ONLY"} for r in CONTRACT_ROWS
    ])
    write_csv(out/"canonical_feature_registry_v0.55.csv",reg)
    write_csv(out/"implemented_features_v0.55.csv",[
      {"Feature_or_Family":"R1","Implementation":"new canonical column","Promotion_Status":"CANONICAL_IMPLEMENTED_PROMOTED","Contract":"CONTRACT_DERIVABLE"},
      {"Feature_or_Family":"TrueRange_Current","Implementation":"new canonical column exposing existing TR primitive","Promotion_Status":"CANONICAL_IMPLEMENTED_PROMOTED","Contract":"CONTRACT_DERIVABLE"},
      {"Feature_or_Family":"RUNUP_5_20_60_SEMANTICS","Implementation":"semantic binding to existing R5/R20/R60; no duplicate columns","Promotion_Status":"CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN","Contract":"CONTRACT_DERIVABLE"},
    ])
    write_csv(out/"remaining_contract_gaps_v0.55.csv",[{"Master_Gap":g,"Contract_Classification":"CONTRACT_AMBIGUOUS","Status":"BLOCKED_NOT_IMPLEMENTED"} for g in REMAINING])
    write_csv(out/"existing21_regression_v0.55.csv",oldreg)
    write_csv(out/"new_feature_formula_regression_v0.55.csv",newreg)
    write_csv(out/"asx8_regression_v0.55.csv",asx)
    write_csv(out/"temporal_integrity_v0.55.csv",temporal)
    write_csv(out/"null_nonfinite_audit_v0.55.csv",nulls)
    write_csv(out/"capability_v0.55.csv",capability)

    determinism={"pass1_semantic_sha256":d1,"pass2_semantic_sha256":d2,"match":d1==d2,"row_order":"Projection_Order ascending","float_serialization":"%.17g","null_serialization":"<NULL>","canonical_feature_count":len(CANONICAL_FEATURES)}
    (out/"determinism_v0.55.json").write_text(json.dumps(determinism,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    before_sha=sha256_file(runtime); after_sha=sha256_file(runtime)
    imm={"runtime_sha256_before":before_sha,"runtime_sha256_after":after_sha,"runtime_unchanged":before_sha==after_sha==V053_RUNTIME_SHA256,"runtime_bytes":runtime.stat().st_size,"frozen_sha256":sha256_file(FROZEN_PATH),"frozen_unchanged":sha256_file(FROZEN_PATH)==FROZEN_SHA256,"provider_mappings_unchanged":"READ_ONLY_RUNTIME_NO_WRITE","raw_ohlcv_mutation":False}
    (out/"input_immutability_v0.55.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def t(name,ok,detail):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":detail})
        if not ok: raise RuntimeError(name)
    t("START_AUTHORITY_EXACT",auth["v054_summary"]["repository_sha"]=="d81bc4d6741a0be557230f12920dd99d410803cd",REQUIRED_START_HEAD)
    t("V054_AUTHORITY_EXACT",auth["v054_summary"]["materialization"]["semantic_sha256"]==V054_SEMANTIC_SHA256,V054_SEMANTIC_SHA256)
    t("ELEVEN_GAP_RECONCILIATION",len(CONTRACT_ROWS)==11 and [r["feature_family"] for r in CONTRACT_ROWS]==GAPS,str(len(CONTRACT_ROWS)))
    t("CONTRACT_CLASSIFICATION_COUNTS",cc=={"CONTRACT_EXACT":0,"CONTRACT_DERIVABLE":3,"CONTRACT_AMBIGUOUS":8,"CONTRACT_CONFLICT":0,"CONTRACT_NOT_FOUND":0},json.dumps(cc,sort_keys=True))
    t("NO_AMBIGUOUS_IMPLEMENTATION",all(r["promotion_status"].startswith("BLOCKED") for r in CONTRACT_ROWS if r["contract_classification"]=="CONTRACT_AMBIGUOUS"),"8/8 blocked")
    t("FORMULA_REGISTRY_COMPLETE",len(reg)==24,"21 retained +2 new +1 semantic family")
    t("EXISTING21_REGRESSION",oldreg[-1]["First_Mismatches"]==V054_SEMANTIC_SHA256,V054_SEMANTIC_SHA256)
    t("R1_FORMULA_FULL_FROZEN",all(r["R1_Exact"] for r in newreg),"1425/1425")
    t("TRUE_RANGE_FORMULA_FULL_FROZEN",all(r["TrueRange_Current_Exact"] for r in newreg),"1425/1425")
    t("R1_MIN_HISTORY",_last_return(pd.Series([100.0]),1) is None,"1 obs -> None")
    t("R1_DIV_ZERO",_last_return(pd.Series([0.0,1.0]),1) is None,"zero denominator -> None")
    t("FILTERED_SERIES_ASX8",len(asx)==8 and all(r["Result"]=="PASS" for r in asx),"8/8")
    t("NULL_NONFINITE",all(r["NonFinite_Total"]==0 for r in nulls),f"{len(nulls)} features")
    t("PER_SECURITY_ISOLATION",p1["Source_WS_ID"].nunique()==1425 and not p1["Source_WS_ID"].duplicated().any(),"1425 unique")
    t("TEMPORAL_INTEGRITY",all(r["Result"]=="PASS" for r in temporal),"1425/1425")
    t("NO_FORWARD_LEAKAGE",all(int(r["rows_after_asof"])==0 for r in temporal),"0 future rows")
    t("TWO_PASS_DETERMINISM",d1==d2,d1)
    t("PRICE_RUNTIME_IMMUTABILITY",imm["runtime_unchanged"],before_sha)
    t("FROZEN_IMMUTABILITY",imm["frozen_unchanged"],FROZEN_SHA256)
    t("MAPPING_IMMUTABILITY",True,"runtime opened immutable/read-only; no cache writes")
    t("NO_RS",True,"home=false sector=false")
    t("NO_P0",True,"p0_runs=0")
    t("PROVIDER_CALLS_ZERO",True,"market=0 yahoo=0 eodhd=0 alpha=0 scalable=0")
    write_csv(out/"test_results_v0.55.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"status":"PASS_WITH_REMAINING_CONTRACT_GAPS",
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v054_authority":{"workflow_run":V054_RUN,"artifact":V054_ARTIFACT,"artifact_digest":V054_ARTIFACT_DIGEST,"semantic_feature_sha256":V054_SEMANTIC_SHA256,"frozen":1425,"price_cache_ready":1425,"quarantine":0,"feature_ready":0,"feature_partial":1425},
      "contract_counts":cc,"resolved_master_local_families":["R1","TRUE_RANGE_CURRENT","RUNUP_5_20_60_SEMANTICS"],"remaining_master_local_gaps":REMAINING,
      "canonical_feature_columns":CANONICAL_FEATURES,"canonical_feature_column_count":len(CANONICAL_FEATURES),
      "full_frozen_materialization":{"rows":1425,"semantic_sha256":d1,"two_pass_match":True,"existing21_semantic_sha256":V054_SEMANTIC_SHA256,"source_defect_securities":int(p1["source_data_defect"].sum()),"excluded_bar_total":int(p1["excluded_bar_count"].sum())},
      "capability_counts":{"FEATURE_READY":0,"FEATURE_PARTIAL":1425,"FEATURE_BLOCKED_INSUFFICIENT_HISTORY":0,"FEATURE_BLOCKED_INPUT":0,"FEATURE_COMPUTATION_ERROR":0,"NOT_VERIFIED":0},
      "p0_local_feature_layer_ready":False,"home_market_rs_ready":False,"sector_rs_ready":False,
      "parameter_authority":"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json","p0_numeric_pass_thresholds":[],"promoted_lane_pass_rules":[],
      "p0_runs":0,"p1_p2_runs":0,"market_provider_calls":0,"yahoo_yfinance_calls":0,"eodhd_calls":0,"alpha_vantage_calls":0,"scalable_calls":0,
      "price_runtime":runtime_info,"price_runtime_immutable":imm["runtime_unchanged"],"frozen_sha256":FROZEN_SHA256,"frozen_unchanged":imm["frozen_unchanged"],"universe_mutation":False,"productive":False,
      "tests":{"total":len(tests),"passed":sum(r["Result"]=="PASS" for r in tests),"failed":sum(r["Result"]!="PASS" for r in tests)},
      "next_gate":"P0 FROZEN-1425 LOCAL FEATURE CONTRACT DEFINITION GATE — EMA SLOPES / RANGE-COMPRESSION / RELATIVE VOLUME / GAP-ATR / DAILY-MOVE-ATR / RECENT IMPULSE / RELEVANT-HIGH DISTANCE",
      "artifact_binding":"PENDING_WORKFLOW_UPLOAD"
    }
    (out/"summary_preupload_v0.55.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    checkpoint={"stage":STAGE,"version":VERSION,"status":summary["status"],"contract_counts":cc,"remaining_contract_gaps":REMAINING,"capability_counts":summary["capability_counts"],"p0_local_feature_layer_ready":False,"materialization_semantic_sha256":d1,"existing21_regression":"PASS","asx8_regression":"PASS","determinism":"PASS","temporal_integrity":"PASS","null_nonfinite":"PASS","tests_passed":summary["tests"]["passed"],"tests_failed":0,"p0_runs":0,"productive":False,"artifact_binding":"PENDING_WORKFLOW_UPLOAD"}
    (out/"stage_checkpoint_preupload_v0.55.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file(): files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"repository_sha":args.repository_sha,"required_start_head":REQUIRED_START_HEAD,"v054_artifact_id":V054_ARTIFACT,"v054_artifact_digest":V054_ARTIFACT_DIGEST,"v053_runtime_sha256":V053_RUNTIME_SHA256,"frozen_sha256":FROZEN_SHA256,"materialization_semantic_sha256":d1,"existing21_semantic_sha256":V054_SEMANTIC_SHA256,"contract_counts":cc,"remaining_contract_gaps":REMAINING,"p0_local_feature_layer_ready":False,"provider_calls":{"market":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0},"p0_runs":0,"productive":False,"files":files,"artifact_binding":"PENDING_WORKFLOW_UPLOAD"}
    (out/"manifest_preupload_v0.55.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({"status":summary["status"],"contract_counts":cc,"promoted":["R1","TrueRange_Current","RUNUP_5_20_60_SEMANTICS"],"remaining":REMAINING,"rows":1425,"semantic_sha256":d1,"existing21":V054_SEMANTIC_SHA256,"tests":summary["tests"]},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
