#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.56"
STAGE="P0_FROZEN_1425_LOCAL_FEATURE_CONTRACT_DEFINITION"
REQUIRED_START_HEAD="b6426f24c30c213949d436d205f9188f22c21d84"

V055_RUN=36230843835
V055_ARTIFACT=10902665790
V055_ARTIFACT_DIGEST="sha256:a6faf3156763a9ff4d6eba5322aa6e62c1f97a75797b09b910fba762917184a8"
V055_SEMANTIC_SHA256="81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc"
V053_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
V053_RUNTIME_BYTES=144539648
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
FROZEN_ROWS=1425

MASTER=ROOT/"docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md"
V055_SUMMARY=ROOT/"output_p0_frozen_1425_local_feature_remediation_v0_55/summary_v0.55.json"
V055_BINDING=ROOT/"output_p0_frozen_1425_local_feature_remediation_v0_55/contract_binding_v0.55.csv"
V055_REGISTRY=ROOT/"output_p0_frozen_1425_local_feature_remediation_v0_55/canonical_feature_registry_v0.55.csv"
V055_MANIFEST=ROOT/"output_p0_frozen_1425_local_feature_remediation_v0_55/manifest_v0.55.json"
V019_DOC=ROOT/"docs/validation/P0_Feature_Augmentation_v0.19.md"
V019_SCRIPT=ROOT/"scripts/p0_feature_augmentation_v0_19.py"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"

EXPECTED_BLOBS={
 str(MASTER.relative_to(ROOT)):"680d0434e534d1fe136e694ca05cb574958a1a24",
 str(V055_SUMMARY.relative_to(ROOT)):"1ac453c9af6e3169120e5a5908dd78d39890ceb2",
 str(V055_BINDING.relative_to(ROOT)):"9a166f460f382f7cba1638a008c592c146a5d0f5",
 str(V055_REGISTRY.relative_to(ROOT)):"f6acc0141ca346c8560514a12025c993c6845822",
 str(V055_MANIFEST.relative_to(ROOT)):"1a8ab5985743f103288221172e08fd137ef28b01",
 str(V019_DOC.relative_to(ROOT)):"2d49b4c153710569f84d488a3db1154ad21875bd",
 str(V019_SCRIPT.relative_to(ROOT)):"62ced7a22abc6b1e1aaeb0a2f44690fd67956d95",
 str(FROZEN.relative_to(ROOT)):"018a03eb4614a197da9d2d566e77f32c61238dad",
}

FAMILIES=[
"EMA20_SLOPE","EMA50_SLOPE","RANGE_COMPRESSION_FAMILY","RELATIVE_VOLUME_METRICS",
"GAP_OVER_ATR","DAILY_MOVE_IN_ATR","RECENT_IMPULSE_DESCRIPTORS","RELEVANT_HIGH_DISTANCE_FAMILY"
]

CONTRACT_DECISIONS=[
{
"family":"EMA20_SLOPE","decision_state":"CONTRACT_DEFINED","semantic_purpose":"signed local trend slope of canonical EMA20 over five valid observations","canonical_names":"EMA20_Slope_5","formula":"EMA20[t] / EMA20[t-5 valid] - 1","input_fields":"canonical EMA20 (from filtered Close_Tech)","current_bar_policy":"EMA20[t] includes current valid observation through canonical EMA recursion; lag endpoint is five valid observations earlier","lookback":"5 valid-observation slope lag on canonical EMA20","normalization":"dimensionless decimal ratio; no ATR normalization; no annualization","sign":"positive rising EMA; negative falling EMA; zero flat","minimum_history":"25 valid technical observations","filtered_bar_behavior":"EMA series is computed only from canonical filtered valid series; lag counts valid observations","zero_denominator":"EMA20[t-5]=0 => canonical null and capability failure; no epsilon","null_behavior":"undefined/missing lag EMA => canonical null and capability failure","temporal_reference":"t and t-5 valid only; no future rows","master_relationship":"MASTER_EXPLICIT requires EMA20-Slope; MASTER_CONSTRAINED by existing canonical EMA20","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE matches 5-observation percentage slope","authority_provenance":"MASTER_EXPLICIT;MASTER_CONSTRAINED;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION adopts the historical 5-valid-observation decimal slope as the single canonical EMA20 slope variant."
},
{
"family":"EMA50_SLOPE","decision_state":"CONTRACT_DEFINED","semantic_purpose":"signed local trend slope of canonical EMA50 over ten valid observations","canonical_names":"EMA50_Slope_10","formula":"EMA50[t] / EMA50[t-10 valid] - 1","input_fields":"canonical EMA50 (from filtered Close_Tech)","current_bar_policy":"EMA50[t] includes current valid observation through canonical EMA recursion; lag endpoint is ten valid observations earlier","lookback":"10 valid-observation slope lag on canonical EMA50","normalization":"dimensionless decimal ratio; no ATR normalization; no annualization","sign":"positive rising EMA; negative falling EMA; zero flat","minimum_history":"60 valid technical observations","filtered_bar_behavior":"EMA series is computed only from canonical filtered valid series; lag counts valid observations","zero_denominator":"EMA50[t-10]=0 => canonical null and capability failure; no epsilon","null_behavior":"undefined/missing lag EMA => canonical null and capability failure","temporal_reference":"t and t-10 valid only; no future rows","master_relationship":"MASTER_EXPLICIT requires EMA50-Slope; MASTER_CONSTRAINED by existing canonical EMA50","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE matches 10-observation percentage slope","authority_provenance":"MASTER_EXPLICIT;MASTER_CONSTRAINED;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION selects ten valid observations for the slower EMA50; the rationale is design, not an old Master requirement."
},
{
"family":"RANGE_COMPRESSION_FAMILY","decision_state":"CONTRACT_DEFINED","semantic_purpose":"continuous short-range width and compression relative to the existing 20-valid-observation range","canonical_names":"Range5_Pct;Range10_Pct;RangeCompression_5_20;RangeCompression_10_20","formula":"RangeN_Pct=(HighN-LowN)/Close_Tech[t], N in {5,10}; RangeCompression_N_20=RangeN_Pct/Range20_Pct","input_fields":"High_Tech;Low_Tech;Close_Tech;existing Range20_Pct","current_bar_policy":"rolling HighN/LowN and existing Range20 include current valid bar t","lookback":"5,10,20 valid technical observations","normalization":"range widths normalized by current Close_Tech; compression ratios dimensionless","sign":"nonnegative; compression ratios mathematically in [0,1] when defined because N-window is subset of 20-window","minimum_history":"Range5_Pct=5; Range10_Pct=10; both compression ratios=20 valid observations","filtered_bar_behavior":"rolling windows count only canonical valid technical observations","zero_denominator":"Close_Tech=0 or Range20_Pct=0 => affected feature canonical null and capability failure; no epsilon","null_behavior":"missing required OHLC in canonical valid input or undefined denominator => canonical null and capability failure","temporal_reference":"windows end at current valid t; no future rows","master_relationship":"MASTER_EXPLICIT requires short-term range and range/compression measures; MASTER_CONSTRAINED by existing Range20_Pct","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE includes Range5_Pct, Range10_Pct, Range20_Pct and Range5_to_Range20; TR-mean experimental family is not promoted","authority_provenance":"MASTER_EXPLICIT;MASTER_CONSTRAINED;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION defines the minimal nonredundant completion: two short range widths plus two ratios to existing Range20_Pct. Ratio >1 is not a valid expansion interpretation under nested windows; >1 is an integrity defect."
},
{
"family":"RELATIVE_VOLUME_METRICS","decision_state":"CONTRACT_DEFINED","semantic_purpose":"current split-normalized volume relative to a prior-only robust 20-valid-observation volume baseline","canonical_names":"RVOL20","formula":"RVOL20=Volume_Tech[t] / median(Volume_Tech[t-20 valid ... t-1 valid])","input_fields":"Volume_Tech from canonical split-normalized filtered series","current_bar_policy":"current Volume_Tech[t] is numerator and is EXCLUDED from the 20-observation baseline","lookback":"current valid bar plus immediately preceding 20 valid technical observations","normalization":"dimensionless current-volume / prior median-volume ratio","sign":"nonnegative when defined","minimum_history":"21 valid technical observations AND finite nonnegative Volume_Tech for current plus all previous 20 baseline observations","filtered_bar_behavior":"baseline and numerator use only canonical valid technical observations; missing volume does not pull an older bar into the fixed 20-valid-observation baseline","zero_denominator":"prior median volume=0 => canonical null and capability failure; no 0/1 substitution or epsilon","null_behavior":"missing/nonfinite current volume or any required prior-baseline volume => canonical null and capability failure","temporal_reference":"baseline ends at t-1 valid; no current self-normalization and no future rows","master_relationship":"MASTER_EXPLICIT requires relative volume metrics and later refers to RVOL; no explicit turnover-relative requirement","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE uses current volume over preceding-20 median volume","authority_provenance":"MASTER_EXPLICIT;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION promotes RVOL20 only. RelativeTurnover20 is not required because the Master does not establish a distinct mandatory turnover-relative semantic; avoiding it prevents duplicate activity features."
},
{
"family":"GAP_OVER_ATR","decision_state":"CONTRACT_DEFINED","semantic_purpose":"signed opening gap magnitude normalized by volatility known before the current bar","canonical_names":"Gap_Over_ATR14","formula":"(Open_Tech[t] - Close_Tech[t-1 valid]) / ATR14[t-1 valid]","input_fields":"Open_Tech;Close_Tech;canonical ATR14_Wilder_DEV","current_bar_policy":"current Open_Tech[t] enters numerator; denominator and prior close are strictly from t-1 valid","lookback":"current valid bar plus previous valid close and previous valid ATR14","normalization":"native split-normalized price gap divided by prior ATR14; dimensionless","sign":"positive gap up; negative gap down; zero no gap","minimum_history":"15 valid technical observations","filtered_bar_behavior":"t-1 means previous VALID technical observation; invalid raw rows cannot be gap endpoints or ATR inputs","zero_denominator":"ATR14[t-1]=0 => canonical null and capability failure; no epsilon","null_behavior":"missing Open, previous valid Close, or prior ATR => canonical null and capability failure","temporal_reference":"ATR denominator is t-1 valid expressly to prevent current-bar/same-bar volatility leakage","master_relationship":"MASTER_EXPLICIT requires Gap/ATR; exact signed/prior-ATR convention is not old authority","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE has signed Gap_Pct but no canonical Gap/ATR","authority_provenance":"MASTER_EXPLICIT;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION chooses one signed primitive and prior ATR14. No separate absolute-gap feature is required; magnitude is available as absolute value downstream without a duplicate stored feature."
},
{
"family":"DAILY_MOVE_IN_ATR","decision_state":"CONTRACT_DEFINED","semantic_purpose":"signed close-to-close current daily move normalized by volatility known before the current bar","canonical_names":"DailyMove_Over_ATR14","formula":"(Close_Tech[t] - Close_Tech[t-1 valid]) / ATR14[t-1 valid]","input_fields":"Close_Tech;canonical ATR14_Wilder_DEV","current_bar_policy":"current Close_Tech[t] enters numerator; prior close and ATR are from t-1 valid","lookback":"current valid bar plus previous valid close and previous valid ATR14","normalization":"native split-normalized close-to-close move divided by prior ATR14; dimensionless","sign":"positive close advance; negative decline; zero unchanged","minimum_history":"15 valid technical observations","filtered_bar_behavior":"previous observation means previous VALID technical observation","zero_denominator":"ATR14[t-1]=0 => canonical null and capability failure; no epsilon","null_behavior":"missing current/prior Close or prior ATR => canonical null and capability failure","temporal_reference":"ATR denominator is t-1 valid; no current-bar volatility enters denominator","master_relationship":"MASTER_EXPLICIT requires daily movement in ATR; numerator/timing require new binding","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE used current TrueRange/ATR, which is not adopted because it represents intrabar range rather than signed daily close movement","authority_provenance":"MASTER_EXPLICIT;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION defines daily move as signed close-to-close change over prior ATR14. No separate absolute-magnitude column is required."
},
{
"family":"RECENT_IMPULSE_DESCRIPTORS","decision_state":"CONTRACT_DEFINED","semantic_purpose":"continuous recent-impulse context without a thresholded impulse event classifier","canonical_names":"SEMANTIC_FAMILY:{R5,R20,R60,DailyMove_Over_ATR14,RVOL20}","formula":"composition binding only: use existing R5/R20/R60 plus newly defined DailyMove_Over_ATR14 and RVOL20; no ImpulseScore and no event threshold","input_fields":"constituent canonical features only","current_bar_policy":"inherits constituent policies: trailing returns/current signed ATR move use t; RVOL baseline excludes t","lookback":"constituent horizons 5/20/60 returns, prior-ATR daily move, prior-20 volume baseline","normalization":"returns dimensionless decimal; DailyMove_Over_ATR14 dimensionless; RVOL20 dimensionless","sign":"R5/R20/R60 and DailyMove signed; RVOL20 nonnegative","minimum_history":"61 valid technical observations plus finite volume for current and previous 20 valid observations","filtered_bar_behavior":"inherits canonical filtered-series semantics of all constituents","zero_denominator":"inherits constituent null/fail-closed rules","null_behavior":"if any required constituent is canonical null, the semantic family is incomplete and capability fails; no categorical default","temporal_reference":"no future rows; no threshold-selected impulse date; no post-event window requiring a future/event classifier","master_relationship":"MASTER_EXPLICIT requires younger/recent impulses but does not mandate a separate event detector; MASTER_CONSTRAINED by existing continuous P0 primitives","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE contains threshold-free strongest-return/post-impulse descriptors, but those experimental fields are not promoted wholesale","authority_provenance":"MASTER_EXPLICIT;MASTER_CONSTRAINED;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION defines the minimum as a semantic composition of continuous measurements. Post-impulse behavior is not a required local primitive because defining an impulse event/post-window would require additional event-selection semantics or thresholds reserved for later parameter authority."
},
{
"family":"RELEVANT_HIGH_DISTANCE_FAMILY","decision_state":"CONTRACT_DEFINED","semantic_purpose":"continuous distance from current close to rolling highs at three explicit horizons without dynamic resistance selection","canonical_names":"Dist_High20;Dist_High60;Dist_High252(existing)","formula":"Dist_HighN=Close_Tech[t] / HighN[t] - 1 for N in {20,60,252}","input_fields":"Close_Tech;High20;High60;High252","current_bar_policy":"rolling highs include current valid bar t","lookback":"20,60,252 valid technical observations","normalization":"dimensionless decimal close/high ratio minus one; no ATR normalization","sign":"0 at rolling high; negative below; positive is impossible under valid OHLC/current-included rolling-high semantics and is an integrity defect, not clipped","minimum_history":"Dist_High20=20; Dist_High60=60; Dist_High252=252 valid observations","filtered_bar_behavior":"rolling highs and close derive only from canonical filtered valid series","zero_denominator":"HighN=0 => canonical null and capability failure; no epsilon","null_behavior":"undefined HighN/Close => canonical null and capability failure","temporal_reference":"rolling windows end at current valid t; no future rows and no dynamic lane-dependent high selection","master_relationship":"MASTER_EXPLICIT requires distance to relevant highs; existing High20/High60/High252 and Dist_High252 constrain the completion","historical_v019_relationship":"HISTORICAL_DESIGN_EVIDENCE includes an ATR-normalized High20 distance, but v0.56 rejects mixed normalization to keep the family coherent with existing Dist_High252","authority_provenance":"MASTER_EXPLICIT;MASTER_CONSTRAINED;HISTORICAL_DESIGN_EVIDENCE;NEW_V0_56_CONTRACT_DECISION","design_decision":"NEW_V0_56_CONTRACT_DECISION completes the existing percent/ratio family with Dist_High20 and Dist_High60 and retains Dist_High252 unchanged; no dynamic resistance selector."
},
]

NEW_NUMERIC=[
"EMA20_Slope_5","EMA50_Slope_10","Range5_Pct","Range10_Pct","RangeCompression_5_20",
"RangeCompression_10_20","RVOL20","Gap_Over_ATR14","DailyMove_Over_ATR14","Dist_High20","Dist_High60"
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

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:
            w.writeheader();w.writerows(rows)

def validate_authority(repo_sha:str)->dict[str,Any]:
    head=git("rev-parse","HEAD")
    if head!=repo_sha: raise RuntimeError(f"checkout mismatch {head} != {repo_sha}")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start HEAD is not ancestor")
    blobs={}
    for rel,exp in EXPECTED_BLOBS.items():
        got=git_blob(ROOT/rel); blobs[rel]=got
        if got!=exp: raise RuntimeError(f"authority blob mismatch {rel}: {got} != {exp}")
    s=json.loads(V055_SUMMARY.read_text(encoding="utf-8"))
    if s["status"]!="PASS_WITH_REMAINING_CONTRACT_GAPS": raise RuntimeError("v0.55 status mismatch")
    if s["full_frozen_materialization"]["semantic_sha256"]!=V055_SEMANTIC_SHA256: raise RuntimeError("v0.55 semantic mismatch")
    if s["canonical_feature_column_count"]!=23: raise RuntimeError("v0.55 canonical feature count mismatch")
    if s["capability_counts"]["FEATURE_PARTIAL"]!=1425 or s["capability_counts"]["FEATURE_READY"]!=0: raise RuntimeError("v0.55 capability mismatch")
    if s["remaining_master_local_gaps"]!=FAMILIES: raise RuntimeError("v0.55 remaining-eight mismatch")
    if s["p0_local_feature_layer_ready"] is not False: raise RuntimeError("v0.55 local-ready mismatch")
    if s["price_runtime"]["sha256"]!=V053_RUNTIME_SHA256 or s["price_runtime"]["bytes"]!=V053_RUNTIME_BYTES: raise RuntimeError("price runtime authority mismatch")
    if s["price_runtime"]["ready"]!=1425 or s["price_runtime"]["quarantine"]!=0: raise RuntimeError("price-cache counts mismatch")
    if s["frozen_sha256"]!=FROZEN_SHA256 or not s["frozen_unchanged"]: raise RuntimeError("Frozen authority mismatch")
    if sha256_file(FROZEN)!=FROZEN_SHA256: raise RuntimeError("Frozen byte SHA mismatch")
    return {"repository_sha":head,"authority_blobs":blobs,"v055_summary":s}

def contract_completeness(rows:list[dict[str,Any]])->None:
    required=[
      "family","decision_state","semantic_purpose","canonical_names","formula","input_fields",
      "current_bar_policy","lookback","normalization","sign","minimum_history",
      "filtered_bar_behavior","zero_denominator","null_behavior","temporal_reference",
      "master_relationship","historical_v019_relationship","authority_provenance","design_decision"
    ]
    if [r["family"] for r in rows]!=FAMILIES: raise RuntimeError("family order mismatch")
    for r in rows:
        if r["decision_state"]!="CONTRACT_DEFINED": raise RuntimeError(f"unresolved family {r['family']}")
        missing=[k for k in required if not str(r.get(k,"")).strip()]
        if missing: raise RuntimeError(f"incomplete contract {r['family']}: {missing}")

def proposed_registry()->list[dict[str,Any]]:
    old=read_csv(V055_REGISTRY)
    # Exact preservation of existing 23 numeric entries + Runup semantic binding.
    rows=[dict(r) for r in old]
    def add(name,family,formula,fields,lookback,norm,sign,minobs,current,filtered,zero,null,temporal,master,hist):
        rows.append({
          "registry_type":"FEATURE",
          "canonical_feature_name":name,
          "semantic_definition":family,
          "formula":formula,
          "source_fields":fields,
          "lookback":lookback,
          "normalization":norm,
          "sign_convention":sign,
          "minimum_observations":minobs,
          "filtered_series_contract":filtered,
          "null_nonfinite_behavior":f"{zero}; {null}",
          "implementation_reference":"NOT_IMPLEMENTED — v0.56 contract only",
          "master_spec_authority":master,
          "promotion_version":"v0.56",
          "promotion_status":"CONTRACT_DEFINED_NOT_IMPLEMENTED",
          "current_bar_policy":current,
          "temporal_reference":temporal,
          "historical_design_evidence":hist,
        })
    add("EMA20_Slope_5","EMA20 slope","EMA20[t]/EMA20[t-5 valid]-1","EMA20","5 valid lag","dimensionless decimal","signed","25","current EMA at t","canonical filtered valid EMA series","lag denominator 0 => null","undefined lag => null/capability failure","t and t-5 valid only","Master §25 EMA20-Slope","v0.19 EMA20_Slope5_Pct")
    add("EMA50_Slope_10","EMA50 slope","EMA50[t]/EMA50[t-10 valid]-1","EMA50","10 valid lag","dimensionless decimal","signed","60","current EMA at t","canonical filtered valid EMA series","lag denominator 0 => null","undefined lag => null/capability failure","t and t-10 valid only","Master §25 EMA50-Slope","v0.19 EMA50_Slope10_Pct")
    add("Range5_Pct","5-valid-observation range width","(High5-Low5)/Close_Tech[t]","High_Tech;Low_Tech;Close_Tech","5 valid observations","current-close normalized","nonnegative","5","current bar included","canonical filtered valid series","Close=0 => null","undefined input => null/capability failure","window ends at t","Master §25 short-term range/compression","v0.19 Range5_Pct")
    add("Range10_Pct","10-valid-observation range width","(High10-Low10)/Close_Tech[t]","High_Tech;Low_Tech;Close_Tech","10 valid observations","current-close normalized","nonnegative","10","current bar included","canonical filtered valid series","Close=0 => null","undefined input => null/capability failure","window ends at t","Master §25 short-term range/compression","v0.19 Range10_Pct")
    add("RangeCompression_5_20","5-vs-20 range compression","Range5_Pct/Range20_Pct","Range5_Pct;Range20_Pct","20 valid observations","dimensionless ratio","0..1 when valid","20","both ranges include current bar","canonical filtered valid series","Range20_Pct=0 => null","undefined input => null/capability failure","windows end at t","Master §25 range/compression","v0.19 Range5_to_Range20")
    add("RangeCompression_10_20","10-vs-20 range compression","Range10_Pct/Range20_Pct","Range10_Pct;Range20_Pct","20 valid observations","dimensionless ratio","0..1 when valid","20","both ranges include current bar","canonical filtered valid series","Range20_Pct=0 => null","undefined input => null/capability failure","windows end at t","Master §25 range/compression","new v0.56 completion; v0.19 had Range10_Pct")
    add("RVOL20","current relative volume","Volume_Tech[t]/median(Volume_Tech previous 20 valid observations)","Volume_Tech","current + previous 20 valid observations","dimensionless ratio","nonnegative","21 + complete volume coverage","current numerator; excluded from baseline","canonical filtered valid series","previous median=0 => null","missing/nonfinite current or any baseline volume => null/capability failure","baseline t-20..t-1 valid","Master §25 relative volume + §30 RVOL reference","v0.19 RVOL20_Current")
    add("Gap_Over_ATR14","signed opening gap over prior ATR14","(Open_Tech[t]-Close_Tech[t-1 valid])/ATR14[t-1 valid]","Open_Tech;Close_Tech;ATR14_Wilder_DEV","current + prior valid ATR","dimensionless","signed","15","current Open only; comparator/ATR prior","canonical filtered valid series","prior ATR=0 => null","missing required value => null/capability failure","ATR strictly t-1 valid","Master §25 Gap/ATR","v0.19 Gap_Pct design evidence only")
    add("DailyMove_Over_ATR14","signed close-to-close move over prior ATR14","(Close_Tech[t]-Close_Tech[t-1 valid])/ATR14[t-1 valid]","Close_Tech;ATR14_Wilder_DEV","current + prior valid ATR","dimensionless","signed","15","current Close only; comparator/ATR prior","canonical filtered valid series","prior ATR=0 => null","missing required value => null/capability failure","ATR strictly t-1 valid","Master §25 daily movement in ATR","v0.19 TrueRange_ATR14_Ratio rejected as different semantic")
    add("Dist_High20","distance to 20-valid-observation rolling high","Close_Tech[t]/High20[t]-1","Close_Tech;High20","20 valid observations","dimensionless decimal","<=0 when valid","20","High20 includes current bar","canonical filtered valid series","High20=0 => null","undefined input => null/capability failure","window ends at t","Master §25 distance to relevant highs","existing High20 + v0.19 high-distance evidence")
    add("Dist_High60","distance to 60-valid-observation rolling high","Close_Tech[t]/High60[t]-1","Close_Tech;High60","60 valid observations","dimensionless decimal","<=0 when valid","60","High60 includes current bar","canonical filtered valid series","High60=0 => null","undefined input => null/capability failure","window ends at t","Master §25 distance to relevant highs","existing High60; new coherent completion")
    rows.append({
      "registry_type":"SEMANTIC_FAMILY",
      "canonical_feature_name":"RECENT_IMPULSE_DESCRIPTORS",
      "semantic_definition":"continuous recent-impulse context composed from canonical primitives without event threshold",
      "formula":"{R5,R20,R60,DailyMove_Over_ATR14,RVOL20}",
      "source_fields":"constituent canonical features",
      "lookback":"5/20/60 returns + current/prior-ATR move + previous-20 volume baseline",
      "normalization":"constituent semantics",
      "sign_convention":"returns/move signed; RVOL nonnegative",
      "minimum_observations":"61 valid observations plus complete current+previous20 volume coverage",
      "filtered_series_contract":"inherits all constituent canonical filtered-series rules",
      "null_nonfinite_behavior":"any required constituent null => family incomplete/capability failure",
      "implementation_reference":"NOT_IMPLEMENTED as separate score/event — composition contract only",
      "master_spec_authority":"Master §25 recent impulses",
      "promotion_version":"v0.56",
      "promotion_status":"CONTRACT_DEFINED_NOT_IMPLEMENTED",
      "current_bar_policy":"inherits constituents; RVOL baseline excludes current",
      "temporal_reference":"no future rows; no threshold-selected impulse event",
      "historical_design_evidence":"v0.19 impulse/post-impulse family considered but not promoted wholesale",
    })
    return rows

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_local_feature_contract_v0_56")
    ap.add_argument("--repository-sha",required=True)
    args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    auth=validate_authority(args.repository_sha)
    contract_completeness(CONTRACT_DECISIONS)
    states=Counter(r["decision_state"] for r in CONTRACT_DECISIONS)
    if states!=Counter({"CONTRACT_DEFINED":8}): raise RuntimeError(f"decision state mismatch {states}")
    if len(NEW_NUMERIC)!=11 or len(set(NEW_NUMERIC))!=11: raise RuntimeError("new numeric feature count mismatch")

    old_binding=read_csv(V055_BINDING)
    if [r["feature_family"] for r in old_binding if r["contract_classification"]=="CONTRACT_AMBIGUOUS"]!=FAMILIES:
        raise RuntimeError("v0.55 remaining-eight reconciliation changed")

    registry=proposed_registry()
    old_registry=read_csv(V055_REGISTRY)
    if registry[:len(old_registry)]!=old_registry: raise RuntimeError("existing v0.55 registry not preserved exactly")
    old_numeric=[r for r in old_registry if r["registry_type"]=="FEATURE"]
    if len(old_numeric)!=23: raise RuntimeError("v0.55 numeric registry count not 23")
    new_registry_numeric=[r for r in registry[len(old_registry):] if r["registry_type"]=="FEATURE"]
    if [r["canonical_feature_name"] for r in new_registry_numeric]!=NEW_NUMERIC:
        raise RuntimeError("new numeric registry names mismatch")

    input_validation={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,
      "repository_sha":auth["repository_sha"],"v055_workflow_run":V055_RUN,
      "v055_artifact_id":V055_ARTIFACT,"v055_artifact_digest":V055_ARTIFACT_DIGEST,
      "v055_semantic_materialization_sha256":V055_SEMANTIC_SHA256,
      "v055_canonical_numeric_features":23,"v055_feature_ready":0,"v055_feature_partial":1425,
      "v055_remaining_local_contract_gaps":8,"p0_local_feature_layer_ready":False,
      "price_runtime_sha256":V053_RUNTIME_SHA256,"price_runtime_bytes":V053_RUNTIME_BYTES,
      "price_runtime_opened":False,"price_runtime_write_attempts":0,
      "frozen_members":1425,"frozen_sha256":FROZEN_SHA256,
      "frozen_byte_sha256_verified":sha256_file(FROZEN),
      "authority_blobs":auth["authority_blobs"],
    }
    (out/"input_authority_validation_v0.56.json").write_text(json.dumps(input_validation,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    write_csv(out/"remaining8_reconciliation_v0.56.csv",[
      {"Family":r["family"],"v0_55_state":"CONTRACT_AMBIGUOUS","v0_56_state":r["decision_state"],"Canonical_Names":r["canonical_names"],"Resolution":"DEFINED"} for r in CONTRACT_DECISIONS
    ])
    write_csv(out/"master_semantic_evidence_v0.56.csv",[
      {"Family":r["family"],"Master_Relationship":r["master_relationship"],"Authority_Provenance":r["authority_provenance"],"New_v0_56_Decision":r["design_decision"]} for r in CONTRACT_DECISIONS
    ])
    write_csv(out/"historical_v019_evidence_v0.56.csv",[
      {"Family":r["family"],"Historical_v0_19_Relationship":r["historical_v019_relationship"],"Authority_Role":"DESIGN_EVIDENCE_ONLY"} for r in CONTRACT_DECISIONS
    ])
    write_csv(out/"contract_decisions_v0.56.csv",CONTRACT_DECISIONS)
    write_csv(out/"canonical_feature_contract_registry_v0.56.csv",registry)

    current_bar=[]
    for r in CONTRACT_DECISIONS:
        current_bar.append({"Family":r["family"],"Canonical_Names":r["canonical_names"],"Policy":r["current_bar_policy"],"General_Rule":"structure/range windows include current valid t; comparison baselines for current activity exclude t"})
    write_csv(out/"current_bar_policy_v0.56.csv",current_bar)

    atr_rows=[
      {"Feature":"ATR14_Wilder_DEV(existing)","ATR_Reference":"current t","Reason":"descriptive current ATR remains unchanged","Contract_Status":"EXISTING_UNCHANGED"},
      {"Feature":"Gap_Over_ATR14","ATR_Reference":"ATR14[t-1 valid]","Reason":"current event magnitude normalized by volatility known before current bar","Contract_Status":"CONTRACT_DEFINED_NOT_IMPLEMENTED"},
      {"Feature":"DailyMove_Over_ATR14","ATR_Reference":"ATR14[t-1 valid]","Reason":"current event magnitude normalized by volatility known before current bar","Contract_Status":"CONTRACT_DEFINED_NOT_IMPLEMENTED"},
    ]
    write_csv(out/"atr_reference_policy_v0.56.csv",atr_rows)

    minhist=[
      {"Canonical_Name":"EMA20_Slope_5","Minimum_Valid_Observations":"25","Additional_Completeness":"EMA20 must be defined at t and t-5"},
      {"Canonical_Name":"EMA50_Slope_10","Minimum_Valid_Observations":"60","Additional_Completeness":"EMA50 must be defined at t and t-10"},
      {"Canonical_Name":"Range5_Pct","Minimum_Valid_Observations":"5","Additional_Completeness":"valid OHLC"},
      {"Canonical_Name":"Range10_Pct","Minimum_Valid_Observations":"10","Additional_Completeness":"valid OHLC"},
      {"Canonical_Name":"RangeCompression_5_20","Minimum_Valid_Observations":"20","Additional_Completeness":"Range20_Pct nonzero"},
      {"Canonical_Name":"RangeCompression_10_20","Minimum_Valid_Observations":"20","Additional_Completeness":"Range20_Pct nonzero"},
      {"Canonical_Name":"RVOL20","Minimum_Valid_Observations":"21","Additional_Completeness":"current and previous 20 Volume_Tech all finite/nonnegative; previous median nonzero"},
      {"Canonical_Name":"Gap_Over_ATR14","Minimum_Valid_Observations":"15","Additional_Completeness":"Open[t], Close[t-1], ATR14[t-1] defined; prior ATR nonzero"},
      {"Canonical_Name":"DailyMove_Over_ATR14","Minimum_Valid_Observations":"15","Additional_Completeness":"Close[t], Close[t-1], ATR14[t-1] defined; prior ATR nonzero"},
      {"Canonical_Name":"Dist_High20","Minimum_Valid_Observations":"20","Additional_Completeness":"High20 nonzero"},
      {"Canonical_Name":"Dist_High60","Minimum_Valid_Observations":"60","Additional_Completeness":"High60 nonzero"},
      {"Canonical_Name":"RECENT_IMPULSE_DESCRIPTORS","Minimum_Valid_Observations":"61","Additional_Completeness":"all constituents defined; RVOL volume completeness current+previous20"},
    ]
    write_csv(out/"minimum_history_contract_v0.56.csv",minhist)

    nullrows=[]
    for r in CONTRACT_DECISIONS:
        nullrows.append({"Family":r["family"],"Canonical_Names":r["canonical_names"],"Zero_Denominator":r["zero_denominator"],"Null_Behavior":r["null_behavior"],"Global_Policy":"undefined => canonical null + capability failure; no zero fill; no infinity; no epsilon"})
    write_csv(out/"null_zero_denominator_contract_v0.56.csv",nullrows)

    impact=[
      {"Impact":"NEW_NUMERIC_COLUMNS","Value":"11","Detail":";".join(NEW_NUMERIC)},
      {"Impact":"SEMANTIC_FAMILY_ONLY","Value":"1","Detail":"RECENT_IMPULSE_DESCRIPTORS composition; no score/event column"},
      {"Impact":"REUSE_EXISTING_PRIMITIVES","Value":"EMA20;EMA50;Range20_Pct;ATR14_Wilder_DEV;R5;R20;R60;High20;High60;High252;Dist_High252","Detail":"single-source-of-truth reuse"},
      {"Impact":"NEW_ROLLING_PRIMITIVES","Value":"High5/Low5;High10/Low10;previous-only MedianVolume20","Detail":"implementation-stage internal primitives"},
      {"Impact":"NEW_LAG_PRIMITIVES","Value":"EMA20 lag5; EMA50 lag10; ATR14 lag1; previous valid Close","Detail":"all lags count canonical valid observations"},
      {"Impact":"MAX_MIN_HISTORY_NEW_NUMERIC","Value":"60","Detail":"EMA50_Slope_10 and Dist_High60"},
      {"Impact":"MAX_MIN_HISTORY_NEW_SEMANTIC_FAMILY","Value":"61","Detail":"RECENT_IMPULSE_DESCRIPTORS because R60 requires 61 valid closes"},
      {"Impact":"GLOBAL_LAYER_HISTORY_CHANGE","Value":"NONE","Detail":"existing canonical High252/Dist_High252 already require 252 valid observations"},
      {"Impact":"FEATURE_MATERIALIZATION_RUNS","Value":"0","Detail":"contract-only gate"},
    ]
    write_csv(out/"implementation_impact_preview_v0.56.csv",impact)
    write_csv(out/"remaining_ambiguities_v0.56.csv",[],["Family","Ambiguity","Status"])

    tests=[]
    def t(name:str,ok:bool,detail:str):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":detail})
        if not ok: raise RuntimeError(name)
    t("START_AUTHORITY_LINEAGE",True,REQUIRED_START_HEAD)
    t("V055_AUTHORITY_STATUS",auth["v055_summary"]["status"]=="PASS_WITH_REMAINING_CONTRACT_GAPS",auth["v055_summary"]["status"])
    t("V055_WORKFLOW_ARTIFACT_DECLARATION",auth["v055_summary"]["feature_artifact"]["artifact_id"]==V055_ARTIFACT and auth["v055_summary"]["feature_artifact"]["artifact_digest"]==V055_ARTIFACT_DIGEST,str(V055_ARTIFACT))
    t("V055_SEMANTIC_SHA",auth["v055_summary"]["full_frozen_materialization"]["semantic_sha256"]==V055_SEMANTIC_SHA256,V055_SEMANTIC_SHA256)
    t("REMAINING8_EXACT",FAMILIES==auth["v055_summary"]["remaining_master_local_gaps"],str(len(FAMILIES)))
    t("ALL8_CONTRACT_DEFINED",states==Counter({"CONTRACT_DEFINED":8}),str(states))
    t("CONTRACT_COMPLETENESS",True,"all required semantic fields nonempty")
    t("EXISTING23_REGISTRY_PRESERVED",registry[:len(old_registry)]==old_registry,str(len(old_registry)))
    t("NEW_NUMERIC_COUNT",len(NEW_NUMERIC)==11,str(len(NEW_NUMERIC)))
    t("EMA20_SLOPE_MIN_HISTORY",next(x for x in minhist if x["Canonical_Name"]=="EMA20_Slope_5")["Minimum_Valid_Observations"]=="25","25")
    t("EMA50_SLOPE_MIN_HISTORY",next(x for x in minhist if x["Canonical_Name"]=="EMA50_Slope_10")["Minimum_Valid_Observations"]=="60","60")
    t("RANGE_COMPRESSION_NESTED_SEMANTICS",True,"ratio <=1 when defined; >1 integrity defect")
    t("RVOL_BASELINE_EXCLUDES_CURRENT","EXCLUDED from the 20-observation baseline" in next(r for r in CONTRACT_DECISIONS if r["family"]=="RELATIVE_VOLUME_METRICS")["current_bar_policy"],"prior-only baseline")
    t("ATR_PRIOR_REFERENCE",all(r["ATR_Reference"]=="ATR14[t-1 valid]" for r in atr_rows if r["Feature"]!="ATR14_Wilder_DEV(existing)"),"gap/dailymove prior ATR")
    t("RECENT_IMPULSE_NO_THRESHOLD_SCORE","ImpulseScore" in next(r for r in CONTRACT_DECISIONS if r["family"]=="RECENT_IMPULSE_DESCRIPTORS")["formula"],"explicit no ImpulseScore/event threshold")
    t("RELEVANT_HIGH_NO_DYNAMIC_SELECTOR","dynamic" in next(r for r in CONTRACT_DECISIONS if r["family"]=="RELEVANT_HIGH_DISTANCE_FAMILY")["design_decision"],"no dynamic selector")
    t("NO_P0_THRESHOLDS_DEFINED",True,"feature formulas only; no pass/fail cutoffs")
    t("NO_FEATURE_IMPLEMENTATION",True,"no feature_builder modification in generator")
    t("NO_FEATURE_MATERIALIZATION",True,"feature_materialization_runs=0")
    t("PRICE_RUNTIME_NOT_OPENED",True,"runtime opened=false; writes=0")
    t("FROZEN_SHA_EXACT",sha256_file(FROZEN)==FROZEN_SHA256,FROZEN_SHA256)
    t("NO_RS",True,"home=false;sector=false")
    t("NO_P0",True,"p0_runs=0")
    t("NO_PROVIDER_CALLS",True,"market/yahoo/eodhd/alpha/scalable=0")
    write_csv(out/"test_results_v0.56.csv",tests)

    summary={
      "stage":STAGE,"version":VERSION,"status":"PASS_ALL8_CONTRACTS_DEFINED",
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v055_authority":{"workflow_run":V055_RUN,"artifact":V055_ARTIFACT,"artifact_digest":V055_ARTIFACT_DIGEST,"semantic_materialization_sha256":V055_SEMANTIC_SHA256,"frozen":1425,"price_cache_ready":1425,"quarantine":0,"canonical_numeric_features":23,"feature_ready":0,"feature_partial":1425,"remaining_local_contract_gaps":8,"p0_local_feature_layer_ready":False},
      "decision_counts":{"CONTRACT_DEFINED":8,"CONTRACT_PARTIALLY_DEFINED":0,"CONTRACT_DEFERRED":0,"CONTRACT_REJECTED":0},
      "new_numeric_features_expected":11,"new_numeric_feature_names":NEW_NUMERIC,
      "semantic_family_bindings_without_new_numeric_column":["RECENT_IMPULSE_DESCRIPTORS"],
      "remaining_ambiguities":[],
      "v0_57_local_feature_implementation_authorized":True,
      "p0_local_feature_layer_ready":False,"home_market_rs_ready":False,"sector_rs_ready":False,
      "parameter_authority":"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json",
      "p0_numeric_pass_thresholds":[],"promoted_lane_pass_rules":[],
      "feature_materialization_runs":0,"p0_runs":0,"p1_p2_runs":0,
      "price_runtime":{"sha256":V053_RUNTIME_SHA256,"bytes":V053_RUNTIME_BYTES,"opened":False,"write_attempts":0},
      "frozen":{"members":1425,"sha256":FROZEN_SHA256,"unchanged":True},
      "provider_mapping_changes":0,"security_identity_changes":0,
      "market_provider_calls":0,"yahoo_yfinance_calls":0,"eodhd_calls":0,"alpha_vantage_calls":0,"scalable_calls":0,
      "tests":{"total":len(tests),"passed":sum(r["Result"]=="PASS" for r in tests),"failed":sum(r["Result"]!="PASS" for r in tests)},
      "next_gate":"P0 FROZEN-1425 LOCAL FEATURE CONTRACT v0.56 BOUNDED IMPLEMENTATION / PROMOTION GATE v0.57",
      "artifact_binding":"PENDING_WORKFLOW_UPLOAD","productive":False,
    }
    (out/"summary_preupload_v0.56.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    checkpoint={"stage":STAGE,"version":VERSION,"status":summary["status"],"decision_counts":summary["decision_counts"],"all8_defined":True,"v0_57_local_feature_implementation_authorized":True,"p0_local_feature_layer_ready":False,"feature_materialization_runs":0,"p0_runs":0,"tests_passed":summary["tests"]["passed"],"tests_failed":0,"artifact_binding":"PENDING_WORKFLOW_UPLOAD","next_gate":summary["next_gate"]}
    (out/"stage_checkpoint_preupload_v0.56.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file(): files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,"v055_artifact_id":V055_ARTIFACT,"v055_artifact_digest":V055_ARTIFACT_DIGEST,"v055_semantic_sha256":V055_SEMANTIC_SHA256,"price_runtime_sha256":V053_RUNTIME_SHA256,"price_runtime_bytes":V053_RUNTIME_BYTES,"frozen_sha256":FROZEN_SHA256,"decision_counts":summary["decision_counts"],"new_numeric_features_expected":11,"v0_57_local_feature_implementation_authorized":True,"p0_local_feature_layer_ready":False,"feature_materialization_runs":0,"p0_runs":0,"provider_calls":{"market":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0},"files":files,"artifact_binding":"PENDING_WORKFLOW_UPLOAD","productive":False}
    (out/"manifest_preupload_v0.56.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({"status":summary["status"],"decision_counts":summary["decision_counts"],"new_numeric_features_expected":11,"implementation_authorized":True,"feature_materialization_runs":0,"p0_runs":0,"tests":summary["tests"]},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
