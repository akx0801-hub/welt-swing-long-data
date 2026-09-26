#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,json,shutil
from pathlib import Path

VERSION="v0.55"
STAGE="P0_FROZEN_1425_MASTER_REQUIRED_LOCAL_FEATURE_REMEDIATION"
REQUIRED_START_HEAD="4fd2d914b2bbb0fcf2b347890f8d652ee80c4f00"
IMPLEMENTATION_HEAD="af813390c92f95e35b71dde95e1f506d231743bb"
RUN_ID=36230843835
ARTIFACT_ID=10902665790
ARTIFACT_NAME="p0-frozen-1425-master-local-feature-remediation-v0.55-36230843835"
ARTIFACT_DIGEST="sha256:a6faf3156763a9ff4d6eba5322aa6e62c1f97a75797b09b910fba762917184a8"
SEMANTIC_SHA256="81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc"
V054_SEMANTIC_SHA256="c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6"
V053_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def read_csv(p:Path):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",required=True)
    ap.add_argument("--repo-root",default=".")
    args=ap.parse_args()
    root=Path(args.repo_root).resolve()
    src=Path(args.artifact_dir).resolve()
    out=root/"output_p0_frozen_1425_local_feature_remediation_v0_55"
    report=root/"docs/validation/P0_Frozen_1425_Master_Local_Feature_Remediation_v0.55.md"

    required=[
      "master_gap_reconciliation_v0.55.csv","contract_binding_v0.55.csv","historical_v019_mapping_v0.55.csv",
      "canonical_feature_registry_v0.55.csv","implemented_features_v0.55.csv","remaining_contract_gaps_v0.55.csv",
      "feature_materialization_v0.55.csv","existing21_regression_v0.55.csv","new_feature_formula_regression_v0.55.csv",
      "asx8_regression_v0.55.csv","temporal_integrity_v0.55.csv","null_nonfinite_audit_v0.55.csv",
      "determinism_v0.55.json","capability_v0.55.csv","input_immutability_v0.55.json","test_results_v0.55.csv",
      "summary_preupload_v0.55.json","stage_checkpoint_preupload_v0.55.json","manifest_preupload_v0.55.json"
    ]
    missing=[x for x in required if not (src/x).exists()]
    if missing: raise RuntimeError(f"missing artifact files {missing}")

    s=json.loads((src/"summary_preupload_v0.55.json").read_text(encoding="utf-8"))
    c=json.loads((src/"stage_checkpoint_preupload_v0.55.json").read_text(encoding="utf-8"))
    d=json.loads((src/"determinism_v0.55.json").read_text(encoding="utf-8"))
    imm=json.loads((src/"input_immutability_v0.55.json").read_text(encoding="utf-8"))
    contracts=read_csv(src/"contract_binding_v0.55.csv")
    impl=read_csv(src/"implemented_features_v0.55.csv")
    gaps=read_csv(src/"remaining_contract_gaps_v0.55.csv")
    cap=read_csv(src/"capability_v0.55.csv")
    old=read_csv(src/"existing21_regression_v0.55.csv")
    asx=read_csv(src/"asx8_regression_v0.55.csv")
    nulls=read_csv(src/"null_nonfinite_audit_v0.55.csv")
    temporal=read_csv(src/"temporal_integrity_v0.55.csv")
    tests=read_csv(src/"test_results_v0.55.csv")

    assert s["status"]=="PASS_WITH_REMAINING_CONTRACT_GAPS"
    assert s["required_start_head"]==REQUIRED_START_HEAD
    assert s["repository_sha"]==IMPLEMENTATION_HEAD
    assert s["contract_counts"]=={"CONTRACT_EXACT":0,"CONTRACT_DERIVABLE":3,"CONTRACT_AMBIGUOUS":8,"CONTRACT_CONFLICT":0,"CONTRACT_NOT_FOUND":0}
    assert len(contracts)==11
    assert [r["Feature_or_Family"] for r in impl]==["R1","TrueRange_Current","RUNUP_5_20_60_SEMANTICS"]
    assert len(gaps)==8
    assert s["full_frozen_materialization"]["semantic_sha256"]==SEMANTIC_SHA256
    assert s["full_frozen_materialization"]["existing21_semantic_sha256"]==V054_SEMANTIC_SHA256
    assert d["pass1_semantic_sha256"]==SEMANTIC_SHA256 and d["pass2_semantic_sha256"]==SEMANTIC_SHA256 and d["match"] is True
    assert s["canonical_feature_column_count"]==23
    assert s["capability_counts"]=={"FEATURE_READY":0,"FEATURE_PARTIAL":1425,"FEATURE_BLOCKED_INSUFFICIENT_HISTORY":0,"FEATURE_BLOCKED_INPUT":0,"FEATURE_COMPUTATION_ERROR":0,"NOT_VERIFIED":0}
    assert len(cap)==1425 and all(r["feature_capability_status"]=="FEATURE_PARTIAL" for r in cap)
    assert all(r["Result"]=="PASS" for r in old)
    assert old[-1]["Authority_Digest"]==V054_SEMANTIC_SHA256
    assert len(asx)==8 and all(r["Result"]=="PASS" for r in asx)
    assert all(int(r["NonFinite_Total"])==0 for r in nulls)
    assert all(r["Result"]=="PASS" for r in temporal)
    assert s["p0_local_feature_layer_ready"] is False
    assert s["home_market_rs_ready"] is False and s["sector_rs_ready"] is False
    assert s["p0_numeric_pass_thresholds"]==[] and s["promoted_lane_pass_rules"]==[]
    assert s["p0_runs"]==0
    assert s["price_runtime"]["sha256"]==V053_RUNTIME_SHA256 and s["price_runtime_immutable"] is True
    assert s["frozen_sha256"]==FROZEN_SHA256 and s["frozen_unchanged"] is True
    assert s["market_provider_calls"]==0 and s["yahoo_yfinance_calls"]==0 and s["eodhd_calls"]==0
    assert s["alpha_vantage_calls"]==0 and s["scalable_calls"]==0
    assert len(tests)==23 and all(r["Result"]=="PASS" for r in tests)
    assert c["tests_failed"]==0 and c["tests_passed"]==23
    assert imm["runtime_unchanged"] is True and imm["frozen_unchanged"] is True

    if out.exists(): shutil.rmtree(out)
    shutil.copytree(src,out)

    artifact_binding={
      "workflow_run_id":RUN_ID,"workflow_head_sha":IMPLEMENTATION_HEAD,
      "artifact_id":ARTIFACT_ID,"artifact_name":ARTIFACT_NAME,"artifact_digest":ARTIFACT_DIGEST,
      "artifact_verified":"PASS","feature_runtime_database_created":False,
      "materialization_semantic_sha256":SEMANTIC_SHA256,
      "feature_materialization_file_sha256":sha256_file(out/"feature_materialization_v0.55.csv"),
      "feature_materialization_file_bytes":(out/"feature_materialization_v0.55.csv").stat().st_size,
      "price_runtime_input_sha256":V053_RUNTIME_SHA256
    }
    (out/"artifact_binding_v0.55.json").write_text(json.dumps(artifact_binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    final=dict(s)
    final["artifact_binding"]="PASS"
    final["feature_artifact"]=artifact_binding
    final["status"]="PASS_WITH_REMAINING_CONTRACT_GAPS"
    final["p0_local_feature_layer_ready"]=False
    (out/"summary_v0.55.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    cp=dict(c)
    cp["artifact_binding"]="PASS"; cp["artifact_id"]=ARTIFACT_ID; cp["artifact_digest"]=ARTIFACT_DIGEST; cp["workflow_run_id"]=RUN_ID
    (out/"stage_checkpoint_v0.55.json").write_text(json.dumps(cp,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    class_rows={r["feature_family"]:r for r in contracts}
    report_lines=[
      "# P0 Frozen-1425 Master-Required Local Feature Remediation v0.55","",
      "## 1. Gate verdict","**PASS_WITH_REMAINING_CONTRACT_GAPS**","",
      "Three of the eleven v0.54 master-local contract gaps are derivable from existing authority and are promoted in v0.55. Eight remain contract-ambiguous and are deliberately not implemented. P0_LOCAL_FEATURE_LAYER_READY remains NO.","",
      "## 2. Start HEAD",REQUIRED_START_HEAD,"",
      "## 3. v0.54 authority validation",
      f"Workflow {36228518000}; artifact 10901437101; artifact digest sha256:0c6eec3a41a26940b4e1325532f2e7bf240f1d362f147f4b52a3943f6f5dfe47; semantic feature SHA-256 {V054_SEMANTIC_SHA256}. Frozen=1425; Price Cache READY=1425; QUARANTINE=0; FEATURE_READY=0; FEATURE_PARTIAL=1425.","",
      "## 4. Master gap reconciliation","All eleven v0.54 gaps were reconciled exactly. Resolved: R1, TRUE_RANGE_CURRENT, RUNUP_5_20_60_SEMANTICS. Remaining: "+", ".join(s["remaining_master_local_gaps"])+".","",
      "## 5. Contract binding — all 11"
    ]
    for fam in [r["feature_family"] for r in contracts]:
        r=class_rows[fam]
        report_lines.append(f"- {fam}: **{r['contract_classification']}** — {r['binding_reason']}")
    report_lines += [
      "",
      "## 6-10. Contract counts",
      "CONTRACT_EXACT=0; CONTRACT_DERIVABLE=3; CONTRACT_AMBIGUOUS=8; CONTRACT_CONFLICT=0; CONTRACT_NOT_FOUND=0.","",
      "## 11. Implemented / promoted features",
      "- R1 — new canonical feature column: one-valid-observation split-normalized close-to-close decimal return.",
      "- TrueRange_Current — new canonical feature column exposing the existing canonical ATR true-range primitive.",
      "- RUNUP_5_20_60_SEMANTICS — canonical semantic binding to existing R5/R20/R60; no duplicate alias columns.","",
      "## 12. Features not implemented and why",
      "EMA20_SLOPE and EMA50_SLOPE: horizon/normalization not fixed by Master. RANGE_COMPRESSION_FAMILY: exact member set/normalization not fixed. RELATIVE_VOLUME_METRICS: numerator/baseline/window not fixed. GAP_OVER_ATR: gap and ATR timing not fixed. DAILY_MOVE_IN_ATR: numerator/sign/ATR timing not fixed. RECENT_IMPULSE_DESCRIPTORS: identification/lookback/direction/post-window not fixed. RELEVANT_HIGH_DISTANCE_FAMILY: high selection and percent-vs-ATR normalization not fixed.","",
      "## 13. Canonical feature registry",
      "v0.55 registry retains the existing 21 entries, adds R1 and TrueRange_Current as CANONICAL_IMPLEMENTED_PROMOTED, and adds the Run-up semantic-family binding. Registry file: canonical_feature_registry_v0.55.csv.","",
      "## 14. Full Frozen materialization",
      f"1425/1425 rows materialized. Canonical numeric columns: 23. Semantic SHA-256: {SEMANTIC_SHA256}. Source-defect securities=8; excluded bars=8.","",
      "## 15. Existing-21 regression",
      f"PASS. The complete old-21 canonical semantic digest remains exactly {V054_SEMANTIC_SHA256}. No existing canonical formula changed.","",
      "## 16. ASX-8 regression","8/8 PASS. The raw 2024-11-15 bars remain stored and excluded from all technical input; R1 and TrueRange_Current independently match the filtered-series computation; R5/R20/R60 remain finite and filtered.","",
      "## 17. Temporal integrity","1425/1425 PASS; no future observation and no row after each security's feature_as_of_date.","",
      "## 18. Null / non-finite audit","All 23 canonical feature columns: NULL/NaN=0, +Inf=0, -Inf=0 across Frozen-1425. R1 division-by-zero behavior is fail-closed to None; production filtered prices are positive.","",
      "## 19. Determinism",f"Two full passes match exactly at {SEMANTIC_SHA256}.","",
      "## 20. Remaining Master local gaps",", ".join(s["remaining_master_local_gaps"])+".","",
      "## 21. Capability counts","FEATURE_READY=0; FEATURE_PARTIAL=1425; all other capability states=0. This remains a global contract blocker, not individual security-data failure.","",
      "## 22. P0_LOCAL_FEATURE_LAYER_READY","**NO**","",
      "## 23. HOME_MARKET_RS_READY","**NO / unchanged**","",
      "## 24. SECTOR_RS_READY","**NO / unchanged**","",
      "## 25. Parameter authority","Unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json; p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[].","",
      "## 26. P0 runs","**0**","",
      "## 27. Price runtime / Frozen immutability",f"Runtime SHA-256 unchanged at {V053_RUNTIME_SHA256}; Frozen SHA-256 unchanged at {FROZEN_SHA256}; provider mappings and raw OHLCV unchanged.","",
      "## 28-30. Provider calls","Market provider=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.","",
      "## 31. Test results","23/23 persisted gate tests PASS plus 6/6 focused pytest tests in the successful workflow.","",
      "## 32. Files","The bounded v0.55 evidence package is persisted under output_p0_frozen_1425_local_feature_remediation_v0_55/ and this report under docs/validation/.","",
      "## 33. Artifact / runtime authority",f"Successful workflow run {RUN_ID}; artifact {ARTIFACT_ID}; artifact digest {ARTIFACT_DIGEST}; feature semantic digest {SEMANTIC_SHA256}. No separate feature-runtime database was created.","",
      "## 34. Commit","Final persistence commit is created by the bounded persistence workflow after artifact verification.","",
      "## 35. Next gate","**P0 FROZEN-1425 LOCAL FEATURE CONTRACT DEFINITION GATE — EMA SLOPES / RANGE-COMPRESSION / RELATIVE VOLUME / GAP-ATR / DAILY-MOVE-ATR / RECENT IMPULSE / RELEVANT-HIGH DISTANCE**","",
      "Hard stop: no Home-Market RS, no Sector RS, no P0 classification, no P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading."
    ]
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join(report_lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.55.json":
            files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    files[str(report.relative_to(root))]={"sha256":sha256_file(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"implementation_head":IMPLEMENTATION_HEAD,
      "successful_workflow_run_id":RUN_ID,"feature_artifact":artifact_binding,
      "materialization_semantic_sha256":SEMANTIC_SHA256,"existing21_semantic_sha256":V054_SEMANTIC_SHA256,
      "contract_counts":s["contract_counts"],"remaining_contract_gaps":s["remaining_master_local_gaps"],
      "capability_counts":s["capability_counts"],"p0_local_feature_layer_ready":False,
      "home_market_rs_ready":False,"sector_rs_ready":False,"parameter_authority":"UNCHANGED",
      "p0_runs":0,"market_provider_calls":0,"yahoo_yfinance_calls":0,"eodhd_calls":0,"alpha_vantage_calls":0,"scalable_calls":0,
      "price_runtime_sha256":V053_RUNTIME_SHA256,"frozen_sha256":FROZEN_SHA256,"universe_mutation":False,"productive":False,
      "files":files,"next_gate":s["next_gate"]
    }
    (out/"manifest_v0.55.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":final["status"],"artifact_binding":"PASS","semantic_sha256":SEMANTIC_SHA256,"contract_counts":s["contract_counts"],"remaining":s["remaining_master_local_gaps"],"tests_passed":23},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
