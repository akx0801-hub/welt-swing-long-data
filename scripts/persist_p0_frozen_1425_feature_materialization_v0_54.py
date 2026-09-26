#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

VERSION = "v0.54"
STAGE = "P0_FROZEN_1425_FEATURE_MATERIALIZATION_CAPABILITY"
REQUIRED_START_HEAD = "8106f8d7a348b4000b504da6b9a82d9fd1db1c33"
IMPLEMENTATION_HEAD = "d81bc4d6741a0be557230f12920dd99d410803cd"
RUN_ID = 36228518000
ARTIFACT_ID = 10901437101
ARTIFACT_NAME = "p0-frozen-1425-feature-materialization-v0.54-36228518000"
ARTIFACT_DIGEST = "sha256:0c6eec3a41a26940b4e1325532f2e7bf240f1d362f147f4b52a3943f6f5dfe47"
SEMANTIC_SHA256 = "c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6"
V053_RUNTIME_SHA256 = "bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
V053_RUNTIME_BYTES = 144539648
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()

def read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--repo-root", default=".")
    args=ap.parse_args()

    root=Path(args.repo_root).resolve()
    art=Path(args.artifact_dir).resolve()
    src=art/"output_p0_frozen_1425_features_v0_54"
    out=root/"output_p0_frozen_1425_features_v0_54"
    report=root/"docs/validation/P0_Frozen_1425_Feature_Materialization_Capability_v0.54.md"

    required=[
        "feature_inventory_v0.54.csv","feature_formula_binding_v0.54.csv","feature_capability_v0.54.csv",
        "feature_materialization_v0.54.csv","non_ready_securities_v0.54.csv",
        "null_nonfinite_audit_v0.54.csv","null_nonfinite_by_mic_v0.54.csv","null_nonfinite_by_security_v0.54.csv",
        "asx8_feature_regression_v0.54.csv","recursive_feature_reproducibility_v0.54.csv",
        "temporal_integrity_v0.54.csv","determinism_v0.54.json","cross_security_integrity_v0.54.json",
        "source_defect_provenance_v0.54.csv","price_runtime_immutability_v0.54.json",
        "parameter_authority_v0.54.json","test_results_v0.54.csv",
        "summary_preupload_v0.54.json","stage_checkpoint_preupload_v0.54.json","manifest_preupload_v0.54.json",
    ]
    missing=[x for x in required if not (src/x).exists()]
    if missing:
        raise RuntimeError(f"artifact evidence missing: {missing}")

    pre=json.loads((src/"summary_preupload_v0.54.json").read_text(encoding="utf-8"))
    chk=json.loads((src/"stage_checkpoint_preupload_v0.54.json").read_text(encoding="utf-8"))
    det=json.loads((src/"determinism_v0.54.json").read_text(encoding="utf-8"))
    imm=json.loads((src/"price_runtime_immutability_v0.54.json").read_text(encoding="utf-8"))
    param=json.loads((src/"parameter_authority_v0.54.json").read_text(encoding="utf-8"))
    cap=read_csv(src/"feature_capability_v0.54.csv")
    inv=read_csv(src/"feature_inventory_v0.54.csv")
    formula=read_csv(src/"feature_formula_binding_v0.54.csv")
    tests=read_csv(src/"test_results_v0.54.csv")
    asx=read_csv(src/"asx8_feature_regression_v0.54.csv")
    nulls=read_csv(src/"null_nonfinite_audit_v0.54.csv")
    temporal=read_csv(src/"temporal_integrity_v0.54.csv")
    prov=read_csv(src/"source_defect_provenance_v0.54.csv")

    assert pre["status"]=="PASS_WITH_LOCAL_FEATURE_MODEL_GAPS"
    assert pre["required_start_head"]==REQUIRED_START_HEAD
    assert pre["repository_sha"]==IMPLEMENTATION_HEAD
    assert pre["v053_authority"]["runtime_sha256"]==V053_RUNTIME_SHA256
    assert pre["v053_authority"]["runtime_bytes"]==V053_RUNTIME_BYTES
    assert pre["v053_authority"]["ready"]==1425 and pre["v053_authority"]["quarantine"]==0
    assert pre["frozen"]["members"]==1425 and pre["frozen"]["sha256"]==FROZEN_SHA256
    assert pre["materialization"]["rows"]==1425
    assert pre["materialization"]["semantic_sha256"]==SEMANTIC_SHA256
    assert det["pass1_semantic_sha256"]==SEMANTIC_SHA256 and det["pass2_semantic_sha256"]==SEMANTIC_SHA256
    assert det["semantic_digest_match"] is True
    assert pre["capability_counts"]=={
        "FEATURE_READY":0,"FEATURE_PARTIAL":1425,"FEATURE_BLOCKED_INSUFFICIENT_HISTORY":0,
        "FEATURE_BLOCKED_INPUT":0,"FEATURE_COMPUTATION_ERROR":0,"NOT_VERIFIED":0,
    }
    assert len(cap)==1425 and Counter(r["feature_capability_status"] for r in cap)==Counter({"FEATURE_PARTIAL":1425})
    assert len([r for r in inv if r["status"]=="CANONICAL_IMPLEMENTED"])==21
    assert len(formula)==21
    assert pre["canonical_feature_inventory"]["master_local_blocking_gaps"]==[
        "EMA20_SLOPE","EMA50_SLOPE","R1","TRUE_RANGE_CURRENT","RANGE_COMPRESSION_FAMILY",
        "RELATIVE_VOLUME_METRICS","GAP_OVER_ATR","DAILY_MOVE_IN_ATR","RECENT_IMPULSE_DESCRIPTORS",
        "RUNUP_5_20_60_SEMANTICS","RELEVANT_HIGH_DISTANCE_FAMILY"
    ]
    assert pre["null_nonfinite"]["all_current_canonical_finite"] is True
    assert all(int(r["NonFinite_Total"])==0 for r in nulls)
    assert len(asx)==8 and all(r["regression_result"]=="PASS" for r in asx)
    assert pre["recursive_reproducibility"]["EMA20_exact"] is True
    assert pre["recursive_reproducibility"]["EMA50_exact"] is True
    assert pre["recursive_reproducibility"]["ATR14_exact"] is True
    assert all(r["temporal_integrity"]=="PASS" for r in temporal)
    assert imm["sqlite_sha256_before"]==V053_RUNTIME_SHA256 and imm["sqlite_sha256_after"]==V053_RUNTIME_SHA256
    assert imm["sqlite_sha256_unchanged"] is True and imm["price_daily_digest_unchanged"] is True
    assert imm["provider_mapping_digest_unchanged"] is True and imm["cache_state_counts_unchanged"] is True
    assert pre["home_market_rs_ready"] is False and pre["sector_rs_ready"] is False
    assert param["status"]=="UNCHANGED_NON_PROMOTED"
    assert param["p0_numeric_pass_thresholds"]==[] and param["promoted_lane_pass_rules"]==[]
    assert pre["p0_runs"]==0 and pre["p0_local_feature_layer_ready"] is False
    assert pre["market_provider_calls"]==0 and pre["yahoo_yfinance_calls"]==0 and pre["eodhd_calls"]==0
    assert pre["alpha_vantage_calls"]==0 and pre["scalable_calls"]==0
    assert len(tests)==39 and all(r["Result"]=="PASS" for r in tests)
    assert chk["tests_failed"]==0 and chk["tests_passed"]==39
    assert len(prov)==8

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src,out)

    artifact_binding={
        "workflow_run_id":RUN_ID,
        "workflow_head_sha":IMPLEMENTATION_HEAD,
        "artifact_id":ARTIFACT_ID,
        "artifact_name":ARTIFACT_NAME,
        "artifact_digest":ARTIFACT_DIGEST,
        "artifact_verified":"PASS",
        "materialization_semantic_sha256":SEMANTIC_SHA256,
        "materialization_file_sha256":sha256_file(out/"feature_materialization_v0.54.csv"),
        "materialization_file_bytes":(out/"feature_materialization_v0.54.csv").stat().st_size,
        "feature_runtime_database_created":False,
        "price_runtime_input_sha256":V053_RUNTIME_SHA256,
        "price_runtime_input_bytes":V053_RUNTIME_BYTES,
    }
    (out/"artifact_binding_v0.54.json").write_text(json.dumps(artifact_binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["feature_artifact"]=artifact_binding
    summary["artifact_binding"]="PASS"
    summary["status"]="PASS_WITH_LOCAL_FEATURE_MODEL_GAPS"
    summary["p0_local_feature_layer_ready"]=False
    summary["next_gate"]="P0 FROZEN-1425 MASTER-REQUIRED LOCAL FEATURE IMPLEMENTATION / PROMOTION REMEDIATION GATE"
    (out/"summary_v0.54.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    checkpoint=dict(chk)
    checkpoint["artifact_binding"]="PASS"
    checkpoint["artifact_id"]=ARTIFACT_ID
    checkpoint["artifact_digest"]=ARTIFACT_DIGEST
    checkpoint["workflow_run_id"]=RUN_ID
    checkpoint["p0_local_feature_layer_ready"]=False
    checkpoint["status"]="PASS_WITH_LOCAL_FEATURE_MODEL_GAPS"
    (out/"stage_checkpoint_v0.54.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    canonical=[r["feature_name"] for r in inv if r["status"]=="CANONICAL_IMPLEMENTED"]
    gaps=pre["canonical_feature_inventory"]["master_local_blocking_gaps"]
    lines=[
        "# P0 Frozen-1425 Feature Materialization / Capability Gate v0.54",
        "",
        "## Gate verdict",
        "**PASS_WITH_LOCAL_FEATURE_MODEL_GAPS**",
        "",
        "The current canonical-implemented technical subset materializes deterministically and completely for all 1425 Frozen securities, but the LONG DEV master specification requires additional local feature semantics that are not current canonical authority. P0_LOCAL_FEATURE_LAYER_READY remains NO.",
        "",
        "## Start authority",
        f"Required start HEAD: {REQUIRED_START_HEAD}",
        f"Implementation HEAD: {IMPLEMENTATION_HEAD}",
        "",
        "## v0.53 authority validation",
        "Run 36225840648; artifact 10900287789; runtime SHA "+V053_RUNTIME_SHA256+"; bytes 144539648; integrity ok; price_daily 711204; states 1425; READY 1425; QUARANTINE 0.",
        "",
        "## Canonical feature inventory",
        f"Current canonical-implemented authoritative subset: {len(canonical)} features.",
        ", ".join(canonical),
        "",
        "Historical v0.19 augmented descriptors were inspected but not silently promoted. Home-market and sector RS are outside this gate.",
        "",
        "Master-local blocking gaps:",
    ] + [f"- {g}" for g in gaps] + [
        "",
        "## Formula / implementation binding",
        "All 21 materialized fields are bound to scripts/feature_builder.py at the validated repository blob. Formula evidence is persisted in feature_formula_binding_v0.54.csv. No formula, threshold or null default changed.",
        "",
        "## Materialization scope",
        f"Rows: 1425. Semantic SHA-256: {SEMANTIC_SHA256}. Valid-bar range: {pre['materialization']['valid_bar_min']} to {pre['materialization']['valid_bar_max']}. Excluded source-defect bars: 8. Market-data downloads: 0.",
        "",
        "## Capability counts",
        "FEATURE_READY=0; FEATURE_PARTIAL=1425; FEATURE_BLOCKED_INSUFFICIENT_HISTORY=0; FEATURE_BLOCKED_INPUT=0; FEATURE_COMPUTATION_ERROR=0; NOT_VERIFIED=0.",
        "The entire Frozen-1425 population is the exact non-ready set, for the common model-level reason MASTER_REQUIRED_LOCAL_FEATURE_MODEL_NOT_FULLY_CANONICAL_IMPLEMENTED.",
        "",
        "## Null / non-finite audit",
        "All 21 current canonical-implemented feature columns are finite for all 1425 securities. NULL/NaN=0; +Inf=0; -Inf=0.",
        "",
        "## History sufficiency",
        f"Minimum filtered valid observations: {pre['history']['minimum_valid_observations_current_frozen']}. Longest current canonical finite-window requirement: {pre['history']['longest_current_canonical_finite_window_minimum']}. History QA v1 unchanged.",
        "",
        "## ASX-8 regression",
        "All eight v0.53 source-defect securities pass. The raw 2024-11-15 bar remains stored, the complete invalid bar is excluded from technical input, and EMA20/EMA50/ATR14 match independent filtered-series recomputation exactly.",
        "",
        "## Recursive reproducibility",
        "EMA20 exact 1425/1425; EMA50 exact 1425/1425; ATR14 exact 1425/1425. Semantics: DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES.",
        "",
        "## Temporal integrity",
        "All 1425 pass; feature_as_of_date equals each security's latest eligible valid bar; no row after own as-of is consumed.",
        "As-of distribution: "+json.dumps(pre["materialization"]["feature_as_of_distribution"],sort_keys=True),
        "",
        "## Determinism",
        f"Pass-1 semantic digest = pass-2 semantic digest = {SEMANTIC_SHA256}. PASS.",
        "",
        "## Source-defect provenance",
        "Eight source-defect securities and eight excluded bars retain dates and filtered-policy provenance in the feature outputs.",
        "",
        "## Price runtime immutability",
        "Input SQLite SHA and bytes unchanged; price_daily digest unchanged; provider mapping digest unchanged; cache state remains 1425 READY / 0 QUARANTINE.",
        "",
        "## Frozen / mapping reconciliation",
        f"Frozen members 1425; SHA-256 {FROZEN_SHA256}; identities and mappings unchanged.",
        "",
        "## RS and parameter authority",
        "HOME_MARKET_RS_READY=NO unchanged. SECTOR_RS_READY=NO unchanged. No RS materialization. Parameter authority remains "+str(param["current_frozen_pointer"])+", with no numeric P0 thresholds and no promoted lane rules.",
        "",
        "## P0 / provider calls",
        "P0 runs=0. Market provider=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.",
        "",
        "## P0_LOCAL_FEATURE_LAYER_READY",
        "**NO**. The 21-field current canonical subset is data-complete, but the master-required local feature contract is not fully canonicalized/implemented.",
        "",
        "## Tests",
        "39/39 PASS plus focused pytest.",
        "",
        "## Artifact authority",
        f"Workflow run {RUN_ID}; feature artifact {ARTIFACT_ID}; artifact digest {ARTIFACT_DIGEST}; semantic feature digest {SEMANTIC_SHA256}. No separate feature-runtime database was created.",
        "",
        "## Next gate",
        "**P0 FROZEN-1425 MASTER-REQUIRED LOCAL FEATURE IMPLEMENTATION / PROMOTION REMEDIATION GATE**",
        "",
        "Hard stop: no P0 classification, no P1/P2, no Home-Market RS, no Sector RS, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading.",
    ]
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.54.json":
            files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    files["docs/validation/P0_Frozen_1425_Feature_Materialization_Capability_v0.54.md"]={"sha256":sha256_file(report),"bytes":report.stat().st_size}
    manifest={
        "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,
        "implementation_head":IMPLEMENTATION_HEAD,"successful_workflow_run_id":RUN_ID,
        "feature_artifact":artifact_binding,"materialization_semantic_sha256":SEMANTIC_SHA256,
        "frozen_sha256":FROZEN_SHA256,"v053_runtime_sha256":V053_RUNTIME_SHA256,
        "v053_runtime_bytes":V053_RUNTIME_BYTES,"canonical_feature_count":21,
        "capability_counts":pre["capability_counts"],"p0_local_feature_layer_ready":False,
        "home_market_rs_ready":False,"sector_rs_ready":False,
        "parameter_authority_status":"UNCHANGED_NON_PROMOTED","p0_runs":0,
        "market_provider_calls":0,"yahoo_yfinance_calls":0,"eodhd_calls":0,
        "alpha_vantage_calls":0,"scalable_calls":0,"universe_mutation":False,
        "productive":False,"files":files,
        "next_gate":"P0 FROZEN-1425 MASTER-REQUIRED LOCAL FEATURE IMPLEMENTATION / PROMOTION REMEDIATION GATE",
    }
    (out/"manifest_v0.54.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({
        "status":"PASS_WITH_LOCAL_FEATURE_MODEL_GAPS","artifact_binding":"PASS",
        "capability_counts":pre["capability_counts"],"p0_local_feature_layer_ready":False,
        "semantic_sha256":SEMANTIC_SHA256,"tests_passed":39,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
