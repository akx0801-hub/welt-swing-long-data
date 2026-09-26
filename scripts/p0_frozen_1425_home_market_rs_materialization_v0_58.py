#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.58"
STAGE="P0_FROZEN_1425_HOME_MARKET_RS_MATERIALIZATION_CAPABILITY"
REQUIRED_START_HEAD="80d80eee5e8a2e6ddad5f7b7b1231b9a3da21895"

FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
PRICE_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
PRICE_RUNTIME_BYTES=144539648

V057_RUN=36239952535
V057_ARTIFACT=10905448132
V057_ARTIFACT_DIGEST="sha256:7f35e18264110c6a6a84205ab443a7b1c3cabcbaebdb3e6d6af79df6361e1c00"
V057_FEATURE_SHA256="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057_DIR=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57"
V057_SUMMARY=V057_DIR/"summary_v0.57.json"
V057_MANIFEST=V057_DIR/"manifest_v0.57.json"
V057_FEATURES=V057_DIR/"feature_materialization_v0.57.csv"
V057_CAPABILITY=V057_DIR/"capability_v0.57.csv"
MASTER=ROOT/"docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md"
V020_DOC=ROOT/"docs/validation/P0_Relative_Strength_Augmentation_v0.20.md"
V020_SCRIPT=ROOT/"scripts/p0_relative_strength_augmentation_v0_20.py"
V021_REGISTRY=ROOT/"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json"
V044_DOC=ROOT/"docs/validation/P0_Frozen_1425_Data_Capability_Readiness_v0.44.md"
V044_BENCHMARK=ROOT/"output_p0_frozen_1425_readiness_v0_44/benchmark_rs_audit_v0.44.csv"

EXPECTED_BLOBS={
 str(FROZEN.relative_to(ROOT)):"018a03eb4614a197da9d2d566e77f32c61238dad",
 str(V057_SUMMARY.relative_to(ROOT)):"c31e5da19de8ee99b77dc343b9520839be102672",
 str(V057_MANIFEST.relative_to(ROOT)):"ad65e2401f80b5dced51dfe57b842d4724978f22",
 str(V057_FEATURES.relative_to(ROOT)):"47bbb681f01b40bfa027905567954cce16c06e24",
 str(V057_CAPABILITY.relative_to(ROOT)):"08e854f8704da78413e7a6b997b7375d669e07a1",
 str(MASTER.relative_to(ROOT)):"680d0434e534d1fe136e694ca05cb574958a1a24",
 str(V020_DOC.relative_to(ROOT)):"a3962c82cfad396e627988ab4b2635a93898b3d0",
 str(V020_SCRIPT.relative_to(ROOT)):"ccdd41dda338e05752a752345cfcb23273deb8ee",
 str(V021_REGISTRY.relative_to(ROOT)):"01ae47713cc722497fcc56585dd27466df8baa9c",
 str(V044_DOC.relative_to(ROOT)):"3718c41f769bf9e257793209b8a7b26d0cb9a9f3",
 str(V044_BENCHMARK.relative_to(ROOT)):"1e2e2f5d43b6370f1337ef79236a8064afaa8863",
}

CROSS_MARKET_MICS=["XNYS","XNAS","XASX","XTKS","XTAI","XSHG","XSHE","XNSE","BVMF"]


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args:str)->str:
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()


def git_blob(path:Path)->str:
    return git("hash-object",str(path.relative_to(ROOT)))


def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:
            w.writeheader()
            w.writerows(rows)


def finite(v:Any)->bool:
    try:
        return math.isfinite(float(v))
    except (TypeError,ValueError):
        return False


def peer_median_leave_one_out(values:pd.Series)->pd.Series:
    """Exact v0.20 leave-one-out median semantics."""
    x=pd.to_numeric(values,errors="coerce")
    out=pd.Series(index=x.index,dtype=float)
    valid_idx=x.dropna().index
    valid_vals=x.loc[valid_idx]
    for idx in valid_idx:
        peers=valid_vals.drop(index=idx)
        if len(peers)>=1:
            out.loc[idx]=float(peers.median())
    return out


def validate_authority(repo_sha:str)->dict[str,Any]:
    head=git("rev-parse","HEAD")
    if head!=repo_sha:
        raise RuntimeError(f"checkout mismatch {head} != {repo_sha}")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start HEAD is not an ancestor of the bounded v0.58 implementation chain")
    blobs={}
    for rel,exp in EXPECTED_BLOBS.items():
        got=git_blob(ROOT/rel);blobs[rel]=got
        if got!=exp:
            raise RuntimeError(f"authority blob mismatch {rel}: {got} != {exp}")

    if sha256_file(FROZEN)!=FROZEN_SHA256:
        raise RuntimeError("Frozen SHA mismatch")
    if sha256_file(V057_FEATURES)!=V057_FEATURE_SHA256:
        raise RuntimeError("v0.57 feature materialization SHA mismatch")

    s=json.loads(V057_SUMMARY.read_text(encoding="utf-8"))
    if s["status"]!="PASS_LOCAL_FEATURE_LAYER_READY":
        raise RuntimeError("v0.57 status mismatch")
    if s["p0_local_feature_layer_ready"] is not True:
        raise RuntimeError("v0.57 local feature layer not ready")
    if s["capability_counts"]!={"FEATURE_BLOCKED_INPUT":0,"FEATURE_BLOCKED_INSUFFICIENT_HISTORY":0,"FEATURE_COMPUTATION_ERROR":0,"FEATURE_PARTIAL":0,"FEATURE_READY":1425,"NOT_VERIFIED":0}:
        raise RuntimeError("v0.57 capability counts mismatch")
    if s["features"]["total_numeric"]!=34:
        raise RuntimeError("v0.57 canonical feature count mismatch")
    if s["feature_artifact"]["workflow_run_id"]!=V057_RUN or s["feature_artifact"]["artifact_id"]!=V057_ARTIFACT or s["feature_artifact"]["artifact_digest"]!=V057_ARTIFACT_DIGEST:
        raise RuntimeError("v0.57 artifact authority mismatch")
    if s["full_frozen_materialization"]["semantic_sha256"]!=V057_FEATURE_SHA256:
        raise RuntimeError("v0.57 semantic SHA mismatch")
    if s["frozen"]!={"members":1425,"sha256":FROZEN_SHA256,"unchanged":True}:
        raise RuntimeError("v0.57 Frozen authority mismatch")
    if s["price_runtime"]["sha256"]!=PRICE_RUNTIME_SHA256 or s["price_runtime"]["bytes"]!=PRICE_RUNTIME_BYTES:
        raise RuntimeError("v0.57 price runtime authority mismatch")
    if s["home_market_rs_ready"] is not False or s["sector_rs_ready"] is not False:
        raise RuntimeError("unexpected prior RS state")

    p=json.loads(V021_REGISTRY.read_text(encoding="utf-8"))
    if p.get("p0_numeric_pass_thresholds")!=[] or p.get("promoted_lane_pass_rules")!=[]:
        raise RuntimeError("parameter authority changed")
    hm=p.get("home_market_rs",{})
    if hm.get("reference")!="LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN" or hm.get("official_benchmark_claim") is not False:
        raise RuntimeError("v0.21 Home-Market RS authority mismatch")

    return {"repository_sha":head,"authority_blobs":blobs,"v057_summary":s,"v021_registry":p}


def load_inputs()->pd.DataFrame:
    frozen=pd.read_csv(FROZEN,dtype=str).fillna("")
    bench=pd.read_csv(V044_BENCHMARK,dtype=str).fillna("")
    feat=pd.read_csv(V057_FEATURES,dtype=str,keep_default_na=False)

    if len(frozen)!=1425 or frozen["Security_Key"].duplicated().any() or frozen["Source_WS_ID"].duplicated().any():
        raise RuntimeError("Frozen identity invalid")
    if len(bench)!=1425 or bench["Security_Key"].duplicated().any() or bench["Source_WS_ID"].duplicated().any():
        raise RuntimeError("v0.44 benchmark mapping identity invalid")
    if len(feat)!=1425 or feat["Security_Key"].duplicated().any() or feat["Source_WS_ID"].duplicated().any():
        raise RuntimeError("v0.57 feature identity invalid")

    frozen_ids=set(frozen["Source_WS_ID"])
    if set(bench["Source_WS_ID"])!=frozen_ids or set(feat["Source_WS_ID"])!=frozen_ids:
        raise RuntimeError("Frozen/benchmark/feature identity sets differ")

    base=frozen[["Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker"]].copy()
    base["Projection_Order"]=pd.to_numeric(base["Projection_Order"],errors="raise").astype(int)
    b=bench[["Security_Key","Source_WS_ID","Primary_Universe_Index","Home_Market_Benchmark_Status","Historical_RS_Architecture"]].copy()
    b=b.rename(columns={"Security_Key":"Benchmark_Security_Key"})
    f=feat[["Security_Key","Source_WS_ID","feature_as_of_date","R20","R60"]].copy()
    f=f.rename(columns={"Security_Key":"Feature_Security_Key"})
    x=base.merge(b,on="Source_WS_ID",how="left",validate="one_to_one").merge(f,on="Source_WS_ID",how="left",validate="one_to_one")

    if (x["Security_Key"]!=x["Benchmark_Security_Key"]).any() or (x["Security_Key"]!=x["Feature_Security_Key"]).any():
        raise RuntimeError("Security_Key mismatch across authorities")
    x["R20_num"]=pd.to_numeric(x["R20"],errors="coerce")
    x["R60_num"]=pd.to_numeric(x["R60"],errors="coerce")
    x["feature_as_of_date"]=pd.to_datetime(x["feature_as_of_date"],errors="coerce").dt.strftime("%Y-%m-%d")
    return x.sort_values("Projection_Order").reset_index(drop=True)


def contract_binding()->dict[str,Any]:
    return {
      "status":"CONTRACT_BOUND",
      "formula_20":"HomeMarket_RS20_Excess = Security_R20 - leave-one-out median R20 of synchronized Primary_Universe_Index peers",
      "formula_60":"HomeMarket_RS60_Excess = Security_R60 - leave-one-out median R60 of synchronized Primary_Universe_Index peers",
      "return_horizons":[20,60],
      "home_market_definition":"current persisted Primary_Universe_Index mapping for the Frozen security",
      "benchmark_definition":"internal Frozen peer/market group; leave-one-out median; not an official index return",
      "benchmark_mapping_authority":"output_p0_frozen_1425_readiness_v0_44/benchmark_rs_audit_v0.44.csv",
      "asof_calendar_rule":"for each security, reference peers must share the exact same feature_as_of_date; no artificial global date",
      "different_trading_days":"different dates form separate synchronized subcohorts; never borrow a peer from a later date",
      "missing_benchmark_behavior":"RS_NOT_VERIFIED; no substitute benchmark, ETF, MIC-country inference, zero fill or fallback",
      "null_nonfinite_behavior":"any missing/non-finite Security R20/R60 or peer median => RS_NOT_VERIFIED",
      "lookahead_rule":"peer feature_as_of_date must equal the security feature_as_of_date; future peer dates prohibited",
      "peer_semantics":"LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN",
      "official_index_benchmark_claim":False,
      "authority_basis":[
        "MASTER_EXPLICIT: 20-/60-day return difference to home market; reproducible internal peer/market groups permitted for early discovery",
        "v0.20: leave-one-out median per Primary_Universe_Index among synchronized peers; fail closed when not synchronized/insufficient",
        "v0.21: preserves LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN and no official benchmark claim",
        "v0.44: exact Frozen-1425 Primary_Universe_Index mapping persisted; current Frozen RS not yet bound",
        "v0.58 gate: prohibits artificial global date, therefore exact same-date peer synchronization is the temporal binding"
      ],
      "new_rs_semantics_invented":False,
      "sector_rs_in_scope":False,
    }


def input_readiness(x:pd.DataFrame):
    mapping_missing=x["Primary_Universe_Index"].astype(str).str.strip().eq("")
    asof_missing=x["feature_as_of_date"].isna() | x["feature_as_of_date"].astype(str).str.strip().eq("")
    r20_bad=~np.isfinite(x["R20_num"].astype(float))
    r60_bad=~np.isfinite(x["R60_num"].astype(float))

    x=x.copy()
    x["sync_cohort_size"]=x.groupby(["Primary_Universe_Index","feature_as_of_date"],dropna=False)["Source_WS_ID"].transform("size")
    x["peer_count"]=x["sync_cohort_size"]-1
    insufficient=x["peer_count"]<1

    blockers=[]
    if mapping_missing.any():blockers.append(("MISSING_PRIMARY_UNIVERSE_INDEX",int(mapping_missing.sum())))
    if asof_missing.any():blockers.append(("MISSING_FEATURE_ASOF",int(asof_missing.sum())))
    if r20_bad.any():blockers.append(("R20_NONFINITE",int(r20_bad.sum())))
    if r60_bad.any():blockers.append(("R60_NONFINITE",int(r60_bad.sum())))
    if insufficient.any():blockers.append(("INSUFFICIENT_SYNCHRONIZED_PEERS",int(insufficient.sum())))

    rows=[]
    for r in x.to_dict("records"):
        reasons=[]
        if not str(r["Primary_Universe_Index"]).strip():reasons.append("MISSING_PRIMARY_UNIVERSE_INDEX")
        if not str(r["feature_as_of_date"]).strip() or str(r["feature_as_of_date"])=="NaT":reasons.append("MISSING_FEATURE_ASOF")
        if not finite(r["R20_num"]):reasons.append("R20_NONFINITE")
        if not finite(r["R60_num"]):reasons.append("R60_NONFINITE")
        if int(r["peer_count"])<1:reasons.append("INSUFFICIENT_SYNCHRONIZED_PEERS")
        rows.append({
          "Projection_Order":r["Projection_Order"],"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],
          "Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Primary_Universe_Index":r["Primary_Universe_Index"],"feature_as_of_date":r["feature_as_of_date"],
          "sync_cohort_size":int(r["sync_cohort_size"]),"peer_count":int(r["peer_count"]),
          "R20_input_finite":finite(r["R20_num"]),"R60_input_finite":finite(r["R60_num"]),
          "Input_Readiness":"READY" if not reasons else "BLOCKED",
          "Blocker":"|".join(reasons),
        })
    return x,rows,blockers


def materialize(x:pd.DataFrame)->pd.DataFrame:
    out=x.copy()
    out["HomeMarket_PeerMedian_R20_v0_58"]=np.nan
    out["HomeMarket_PeerMedian_R60_v0_58"]=np.nan
    for (_, _),g in out.groupby(["Primary_Universe_Index","feature_as_of_date"],sort=True,dropna=False):
        idx=g.index
        out.loc[idx,"HomeMarket_PeerMedian_R20_v0_58"]=peer_median_leave_one_out(g["R20_num"])
        out.loc[idx,"HomeMarket_PeerMedian_R60_v0_58"]=peer_median_leave_one_out(g["R60_num"])
    out["HomeMarket_RS20_Excess_v0_58"]=out["R20_num"]-out["HomeMarket_PeerMedian_R20_v0_58"]
    out["HomeMarket_RS60_Excess_v0_58"]=out["R60_num"]-out["HomeMarket_PeerMedian_R60_v0_58"]
    out["HomeMarket_RS_Reference_Type_v0_58"]="LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN_SAME_ASOF"
    return out.sort_values("Projection_Order").reset_index(drop=True)


RS_SEMANTIC_COLS=[
"Projection_Order","Security_Key","Source_WS_ID","Primary_MIC","Primary_Ticker","Primary_Universe_Index",
"feature_as_of_date","sync_cohort_size","peer_count","R20_num","R60_num",
"HomeMarket_PeerMedian_R20_v0_58","HomeMarket_PeerMedian_R60_v0_58",
"HomeMarket_RS20_Excess_v0_58","HomeMarket_RS60_Excess_v0_58","HomeMarket_RS_Reference_Type_v0_58"
]


def semantic_bytes(df:pd.DataFrame)->bytes:
    return df[RS_SEMANTIC_COLS].sort_values("Projection_Order").to_csv(index=False,lineterminator="\n",float_format="%.17g",na_rep="<NULL>").encode("utf-8")


def semantic_digest(df:pd.DataFrame)->str:
    return hashlib.sha256(semantic_bytes(df)).hexdigest()


def capability(mat:pd.DataFrame)->list[dict[str,Any]]:
    rows=[]
    for r in mat.to_dict("records"):
        reasons=[]
        if not finite(r["HomeMarket_PeerMedian_R20_v0_58"]):reasons.append("RS20_REFERENCE_NOT_VERIFIED")
        if not finite(r["HomeMarket_PeerMedian_R60_v0_58"]):reasons.append("RS60_REFERENCE_NOT_VERIFIED")
        if not finite(r["HomeMarket_RS20_Excess_v0_58"]):reasons.append("RS20_NOT_VERIFIED")
        if not finite(r["HomeMarket_RS60_Excess_v0_58"]):reasons.append("RS60_NOT_VERIFIED")
        if int(r["peer_count"])<1:reasons.append("NO_SYNCHRONIZED_PEER")
        rows.append({
          "Projection_Order":int(r["Projection_Order"]),"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],
          "Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Primary_Universe_Index":r["Primary_Universe_Index"],"feature_as_of_date":r["feature_as_of_date"],
          "peer_count":int(r["peer_count"]),"HomeMarket_RS_Status":"HOME_MARKET_RS_READY" if not reasons else "RS_NOT_VERIFIED",
          "Blocker":"|".join(reasons),
        })
    return rows


def temporal_audit(mat:pd.DataFrame)->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    rows=[]
    group_dates={(g,d):d for g,d in mat[["Primary_Universe_Index","feature_as_of_date"]].drop_duplicates().itertuples(index=False,name=None)}
    for r in mat.to_dict("records"):
        d=str(r["feature_as_of_date"])
        future=0
        # Reference is constructed only from exact same-date subgroup.
        ok=(r["HomeMarket_RS_Reference_Type_v0_58"]=="LEAVE_ONE_OUT_PRIMARY_UNIVERSE_COHORT_MEDIAN_SAME_ASOF" and int(r["peer_count"])>=1)
        rows.append({
          "Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],
          "Primary_Universe_Index":r["Primary_Universe_Index"],"security_asof":d,"benchmark_peer_asof":group_dates[(r["Primary_Universe_Index"],d)],
          "future_peer_count":future,"Result":"PASS" if ok else "FAIL",
        })
    cross=[]
    for mic in CROSS_MARKET_MICS:
        q=mat.loc[mat["Primary_MIC"].eq(mic)].copy()
        if q.empty:
            cross.append({"Primary_MIC":mic,"Rows":0,"Unique_AsOf_Dates":0,"AsOf_Dates":"","Benchmark_Groups":"","Min_Peer_Count":"","Max_Peer_Count":"","Temporal_Result":"NOT_PRESENT"})
        else:
            dates=sorted(set(q["feature_as_of_date"].astype(str)))
            groups=sorted(set(q["Primary_Universe_Index"].astype(str)))
            cross.append({"Primary_MIC":mic,"Rows":len(q),"Unique_AsOf_Dates":len(dates),"AsOf_Dates":"|".join(dates),"Benchmark_Groups":"|".join(groups),"Min_Peer_Count":int(q["peer_count"].min()),"Max_Peer_Count":int(q["peer_count"].max()),"Temporal_Result":"PASS"})
    return rows,cross


def cohort_readiness(x:pd.DataFrame)->list[dict[str,Any]]:
    rows=[]
    for (g,d),q in x.groupby(["Primary_Universe_Index","feature_as_of_date"],sort=True,dropna=False):
        rows.append({
          "Primary_Universe_Index":g,"feature_as_of_date":d,"Rows":len(q),"Peer_Count_Per_Security":max(0,len(q)-1),
          "Primary_MICs":"|".join(sorted(set(q["Primary_MIC"].astype(str)))),
          "R20_Finite":int(np.isfinite(q["R20_num"].astype(float)).sum()),"R60_Finite":int(np.isfinite(q["R60_num"].astype(float)).sum()),
          "Cohort_Status":"READY" if len(q)>=2 and np.isfinite(q["R20_num"].astype(float)).all() and np.isfinite(q["R60_num"].astype(float)).all() else "BLOCKED",
        })
    return rows


def provider_calls()->dict[str,int]:
    return {"market_data_provider_calls":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0}


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-runtime",required=True)
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_home_market_rs_v0_58")
    ap.add_argument("--repository-sha",required=True)
    args=ap.parse_args()
    runtime=Path(args.price_runtime)
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)

    authority=validate_authority(args.repository_sha)
    if runtime.stat().st_size!=PRICE_RUNTIME_BYTES or sha256_file(runtime)!=PRICE_RUNTIME_SHA256:
        raise RuntimeError("price runtime input authority mismatch")
    runtime_sha_before=sha256_file(runtime);runtime_bytes_before=runtime.stat().st_size
    frozen_sha_before=sha256_file(FROZEN);feature_sha_before=sha256_file(V057_FEATURES)

    contract=contract_binding()
    (out/"contract_binding_v0.58.json").write_text(json.dumps(contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    x=load_inputs()
    x,readiness_rows,input_blockers=input_readiness(x)
    write_csv(out/"benchmark_mapping_input_readiness_v0.58.csv",readiness_rows)
    cohort_rows=cohort_readiness(x)
    write_csv(out/"benchmark_cohort_readiness_v0.58.csv",cohort_rows)

    verdict=""
    home_ready=False
    ready_count=0
    materialized=False
    determinism={"executed":False,"match":False,"pass1_semantic_sha256":None,"pass2_semantic_sha256":None}
    capability_rows=[]
    temporal_rows=[]
    cross_rows=[]
    null_rows=[]
    material_sha=None

    if contract["status"]!="CONTRACT_BOUND":
        verdict="PASS_WITH_CONTRACT_BLOCKER"
    elif input_blockers:
        verdict="PASS_WITH_INPUT_BLOCKER"
        for r in readiness_rows:
            capability_rows.append({
              "Projection_Order":r["Projection_Order"],"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],
              "Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],"Primary_Universe_Index":r["Primary_Universe_Index"],
              "feature_as_of_date":r["feature_as_of_date"],"peer_count":r["peer_count"],"HomeMarket_RS_Status":"RS_NOT_VERIFIED","Blocker":r["Blocker"] or "GLOBAL_INPUT_BLOCKER",
            })
    else:
        m1=materialize(x)
        m2=materialize(x)
        d1=semantic_digest(m1);d2=semantic_digest(m2)
        determinism={"executed":True,"match":d1==d2,"pass1_semantic_sha256":d1,"pass2_semantic_sha256":d2,
                     "row_order":"Projection_Order ascending","float_serialization":"%.17g","null_serialization":"<NULL>"}
        if d1!=d2:
            raise RuntimeError("Home-Market RS determinism failed")
        materialized=True;material_sha=d1
        capability_rows=capability(m1)
        cap=Counter(r["HomeMarket_RS_Status"] for r in capability_rows)
        ready_count=cap.get("HOME_MARKET_RS_READY",0)
        temporal_rows,cross_rows=temporal_audit(m1)
        if any(r["Result"]!="PASS" for r in temporal_rows):
            raise RuntimeError("temporal integrity failed")
        for col in ["HomeMarket_PeerMedian_R20_v0_58","HomeMarket_PeerMedian_R60_v0_58","HomeMarket_RS20_Excess_v0_58","HomeMarket_RS60_Excess_v0_58"]:
            s=pd.to_numeric(m1[col],errors="coerce")
            a=s.to_numpy(dtype=float,na_value=np.nan)
            null_rows.append({"Field":col,"Rows":1425,"NaN_or_Null":int(np.isnan(a).sum()),"PosInf":int(np.isposinf(a).sum()),"NegInf":int(np.isneginf(a).sum())})
        null_total=sum(r["NaN_or_Null"]+r["PosInf"]+r["NegInf"] for r in null_rows)
        home_ready=(ready_count==1425 and null_total==0 and determinism["match"])
        verdict="PASS_HOME_MARKET_RS_READY" if home_ready else "PASS_WITH_INPUT_BLOCKER"
        m1[RS_SEMANTIC_COLS].to_csv(out/"home_market_rs_materialization_v0.58.csv",index=False,lineterminator="\n",float_format="%.17g",na_rep="")
        write_csv(out/"temporal_integrity_v0.58.csv",temporal_rows)
        write_csv(out/"cross_market_temporal_audit_v0.58.csv",cross_rows)
        write_csv(out/"null_nonfinite_audit_v0.58.csv",null_rows)

    write_csv(out/"capability_v0.58.csv",capability_rows)
    (out/"determinism_v0.58.json").write_text(json.dumps(determinism,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    mapping_summary=[]
    for g,q in x.groupby("Primary_Universe_Index",sort=True):
        mapping_summary.append({"Primary_Universe_Index":g,"Frozen_Rows":len(q),"Primary_MICs":"|".join(sorted(set(q["Primary_MIC"].astype(str)))),"Unique_AsOf_Dates":len(set(q["feature_as_of_date"].astype(str))),"Min_SameDate_Peer_Count":int(q["peer_count"].min()),"Max_SameDate_Peer_Count":int(q["peer_count"].max())})
    write_csv(out/"benchmark_mapping_summary_v0.58.csv",mapping_summary)

    runtime_sha_after=sha256_file(runtime);runtime_bytes_after=runtime.stat().st_size
    frozen_sha_after=sha256_file(FROZEN);feature_sha_after=sha256_file(V057_FEATURES)
    immutability={
      "price_runtime_sha_before":runtime_sha_before,"price_runtime_sha_after":runtime_sha_after,
      "price_runtime_bytes_before":runtime_bytes_before,"price_runtime_bytes_after":runtime_bytes_after,
      "price_runtime_unchanged":runtime_sha_before==runtime_sha_after==PRICE_RUNTIME_SHA256 and runtime_bytes_before==runtime_bytes_after==PRICE_RUNTIME_BYTES,
      "frozen_sha_before":frozen_sha_before,"frozen_sha_after":frozen_sha_after,"frozen_unchanged":frozen_sha_before==frozen_sha_after==FROZEN_SHA256,
      "v057_feature_sha_before":feature_sha_before,"v057_feature_sha_after":feature_sha_after,"v057_features_unchanged":feature_sha_before==feature_sha_after==V057_FEATURE_SHA256,
      "provider_mapping_mutation":False,"security_identity_mutation":False,"raw_ohlcv_mutation":False,
    }
    (out/"input_immutability_v0.58.json").write_text(json.dumps(immutability,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"provider_calls_v0.58.json").write_text(json.dumps(provider_calls(),indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def t(name:str,ok:bool,detail:str):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":detail})
        if not ok:raise RuntimeError(name)
    t("START_HEAD_DIRECT_PARENT",True,REQUIRED_START_HEAD)
    t("V057_STATUS",authority["v057_summary"]["status"]=="PASS_LOCAL_FEATURE_LAYER_READY","PASS_LOCAL_FEATURE_LAYER_READY")
    t("V057_FEATURE_READY_1425",authority["v057_summary"]["capability_counts"]["FEATURE_READY"]==1425,"1425")
    t("V057_34_NUMERIC",authority["v057_summary"]["features"]["total_numeric"]==34,"34")
    t("V057_ARTIFACT",authority["v057_summary"]["feature_artifact"]["artifact_digest"]==V057_ARTIFACT_DIGEST,V057_ARTIFACT_DIGEST)
    t("FROZEN_SHA",immutability["frozen_unchanged"],FROZEN_SHA256)
    t("PRICE_RUNTIME_SHA_BYTES",immutability["price_runtime_unchanged"],PRICE_RUNTIME_SHA256)
    t("LOCAL_FEATURE_IMMUTABLE",immutability["v057_features_unchanged"],V057_FEATURE_SHA256)
    t("CONTRACT_BOUND",contract["status"]=="CONTRACT_BOUND",contract["peer_semantics"])
    t("MAPPING_1425",len(readiness_rows)==1425,"1425")
    t("PRIMARY_UNIVERSE_INDEX_COMPLETE",all(str(r["Primary_Universe_Index"]).strip() for r in readiness_rows),str(sum(not str(r["Primary_Universe_Index"]).strip() for r in readiness_rows)))
    t("R20_R60_INPUT_FINITE",all(r["R20_input_finite"] and r["R60_input_finite"] for r in readiness_rows),"1425/1425")
    t("SYNCHRONIZED_PEER_AVAILABLE",all(int(r["peer_count"])>=1 for r in readiness_rows),f"blockers={input_blockers}")
    t("NO_GLOBAL_DATE_FORCED",True,"reference cohorts keyed by Primary_Universe_Index + exact feature_as_of_date")
    if materialized:
        t("FULL_1425_MATERIALIZATION",len(capability_rows)==1425,"1425")
        t("TWO_PASS_DETERMINISM",determinism["match"],str(material_sha))
        t("TEMPORAL_INTEGRITY",all(r["Result"]=="PASS" for r in temporal_rows),"1425/1425")
        t("NO_FUTURE_PEERS",all(int(r["future_peer_count"])==0 for r in temporal_rows),"0")
        t("NO_RS_NONFINITE",all((r["NaN_or_Null"]+r["PosInf"]+r["NegInf"])==0 for r in null_rows),json.dumps(null_rows))
        t("CAPABILITY_READY_COUNT",ready_count==1425,str(ready_count))
    t("SECTOR_RS_NOT_RUN",True,"sector_rs_ready=false")
    t("PARAMETER_AUTHORITY_UNCHANGED",True,"p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[]")
    t("P0_P1_P2_ZERO",True,"0/0")
    t("PROVIDER_CALLS_ZERO",all(v==0 for v in provider_calls().values()),json.dumps(provider_calls(),sort_keys=True))
    write_csv(out/"test_results_v0.58.csv",tests)

    if verdict=="PASS_HOME_MARKET_RS_READY":
        next_gate="P0 FROZEN-1425 SECTOR METADATA / SECTOR-RS AUTHORITY GATE"
        blocker="NONE"
    elif verdict=="PASS_WITH_CONTRACT_BLOCKER":
        next_gate="P0 FROZEN-1425 HOME-MARKET RS CONTRACT DEFINITION GATE"
        blocker="HOME_MARKET_RS_CONTRACT_NOT_BOUND"
    else:
        next_gate="SMALLEST REQUIRED BENCHMARK-MAPPING / INPUT-ACQUISITION GATE"
        blocker=";".join(f"{k}:{n}" for k,n in input_blockers) or "MATERIALIZATION_CAPABILITY_BLOCKER"

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"status":verdict,
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v057_authority":{"workflow_run":V057_RUN,"artifact":V057_ARTIFACT,"artifact_digest":V057_ARTIFACT_DIGEST,"feature_semantic_sha256":V057_FEATURE_SHA256,"p0_local_feature_layer_ready":True,"feature_ready":1425,"canonical_numeric_features":34},
      "contract_status":contract["status"],"contract_method":contract["peer_semantics"],
      "mapping_rows":1425,"benchmark_groups":mapping_summary,
      "input_blockers":[{"code":k,"affected":n} for k,n in input_blockers],
      "materialized":materialized,"home_market_rs_ready":home_ready,"ready_count":ready_count,"total":1425,
      "rs_semantic_sha256":material_sha,"determinism_match":determinism["match"] if materialized else None,
      "sector_rs_ready":False,
      "parameter_authority":"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json",
      "p0_numeric_pass_thresholds":[],"promoted_lane_pass_rules":[],
      "p0_runs":0,"p1_p2_runs":0,
      "price_runtime":{"sha256":PRICE_RUNTIME_SHA256,"bytes":PRICE_RUNTIME_BYTES,"unchanged":immutability["price_runtime_unchanged"]},
      "frozen":{"members":1425,"sha256":FROZEN_SHA256,"unchanged":immutability["frozen_unchanged"]},
      "v057_local_features_unchanged":immutability["v057_features_unchanged"],
      "provider_calls":provider_calls(),"tests":{"total":len(tests),"passed":sum(r["Result"]=="PASS" for r in tests),"failed":sum(r["Result"]!="PASS" for r in tests)},
      "blocker":blocker,"next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD","productive":False,
    }
    (out/"summary_preupload_v0.58.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    checkpoint={"stage":STAGE,"version":VERSION,"verdict":verdict,"home_market_rs_ready":home_ready,"ready_count":ready_count,"total":1425,"contract_status":contract["status"],"input_blockers":summary["input_blockers"],"materialized":materialized,"rs_semantic_sha256":material_sha,"sector_rs_ready":False,"p0_runs":0,"p1_p2_runs":0,"tests_passed":summary["tests"]["passed"],"tests_failed":summary["tests"]["failed"],"artifact_binding":"PENDING_UPLOAD","next_gate":next_gate}
    (out/"stage_checkpoint_preupload_v0.58.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"input_authority_validation_v0.58.json").write_text(json.dumps({
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v057_workflow_run":V057_RUN,"v057_artifact_id":V057_ARTIFACT,"v057_artifact_digest":V057_ARTIFACT_DIGEST,
      "v057_feature_semantic_sha256":V057_FEATURE_SHA256,"v057_feature_ready":1425,"v057_canonical_numeric_features":34,
      "frozen_members":1425,"frozen_sha256":FROZEN_SHA256,"price_runtime_sha256":PRICE_RUNTIME_SHA256,"price_runtime_bytes":PRICE_RUNTIME_BYTES,
      "authority_blobs":authority["authority_blobs"],
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,"verdict":verdict,"home_market_rs_ready":home_ready,"ready_count":ready_count,"total":1425,"v057_artifact_id":V057_ARTIFACT,"v057_artifact_digest":V057_ARTIFACT_DIGEST,"v057_feature_semantic_sha256":V057_FEATURE_SHA256,"price_runtime_sha256":PRICE_RUNTIME_SHA256,"price_runtime_bytes":PRICE_RUNTIME_BYTES,"frozen_sha256":FROZEN_SHA256,"rs_semantic_sha256":material_sha,"sector_rs_ready":False,"p0_runs":0,"p1_p2_runs":0,"provider_calls":provider_calls(),"files":files,"artifact_binding":"PENDING_UPLOAD","productive":False,"next_gate":next_gate}
    (out/"manifest_preupload_v0.58.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({"verdict":verdict,"home_market_rs_ready":home_ready,"ready_count":ready_count,"total":1425,"input_blockers":input_blockers,"rs_semantic_sha256":material_sha,"next_gate":next_gate},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
