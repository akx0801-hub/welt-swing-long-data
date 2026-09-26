#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,json,shutil
from pathlib import Path

VERSION="v0.57"
STAGE="P0_FROZEN_1425_LOCAL_FEATURE_CONTRACT_V056_IMPLEMENTATION_PROMOTION"
REQUIRED_START_HEAD="0287a10bf7a2938ed1517d79a47c296f3ea34c9d"
IMPLEMENTATION_HEAD="d51e0bad6349fd69ba24555db0b84296ad99b157"
RUN_ID=36239952535
ARTIFACT_ID=10905448132
ARTIFACT_NAME="p0-frozen-1425-local-feature-implementation-v0.57-36239952535"
ARTIFACT_DIGEST="sha256:7f35e18264110c6a6a84205ab443a7b1c3cabcbaebdb3e6d6af79df6361e1c00"
SEMANTIC_SHA256="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
EXISTING23_SHA256="81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc"
PRICE_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
PRICE_RUNTIME_BYTES=144539648
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

def read_csv(p:Path):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",required=True)
    ap.add_argument("--repo-root",default=".")
    args=ap.parse_args()
    root=Path(args.repo_root).resolve()
    src=Path(args.artifact_dir).resolve()/"output_p0_frozen_1425_local_feature_implementation_v0_57"
    out=root/"output_p0_frozen_1425_local_feature_implementation_v0_57"
    report=root/"docs/validation/P0_Frozen_1425_Local_Feature_Implementation_Promotion_v0.57.md"

    required=[
      "asx8_regression_v0.57.csv","canonical_feature_registry_v0.57.csv","capability_v0.57.csv",
      "determinism_v0.57.json","existing23_regression_v0.57.csv","feature_materialization_v0.57.csv",
      "implementation_promotion_audit_v0.57.csv","input_authority_validation_v0.57.json",
      "input_immutability_v0.57.json","manifest_preupload_v0.57.json",
      "new11_formula_regression_v0.57.csv","null_nonfinite_audit_v0.57.csv",
      "null_nonfinite_by_security_v0.57.csv","semantic_family_binding_audit_v0.57.csv",
      "stage_checkpoint_preupload_v0.57.json","summary_preupload_v0.57.json",
      "temporal_integrity_v0.57.csv","test_results_v0.57.csv"]
    miss=[x for x in required if not (src/x).exists()]
    if miss:raise RuntimeError(f"artifact missing {miss}")

    pre=json.loads((src/"summary_preupload_v0.57.json").read_text(encoding="utf-8"))
    chk=json.loads((src/"stage_checkpoint_preupload_v0.57.json").read_text(encoding="utf-8"))
    det=json.loads((src/"determinism_v0.57.json").read_text(encoding="utf-8"))
    imm=json.loads((src/"input_immutability_v0.57.json").read_text(encoding="utf-8"))
    mat=read_csv(src/"feature_materialization_v0.57.csv")
    cap=read_csv(src/"capability_v0.57.csv")
    old=read_csv(src/"existing23_regression_v0.57.csv")
    new=read_csv(src/"new11_formula_regression_v0.57.csv")
    asx=read_csv(src/"asx8_regression_v0.57.csv")
    temporal=read_csv(src/"temporal_integrity_v0.57.csv")
    nulls=read_csv(src/"null_nonfinite_audit_v0.57.csv")
    family=read_csv(src/"semantic_family_binding_audit_v0.57.csv")
    tests=read_csv(src/"test_results_v0.57.csv")
    registry=read_csv(src/"canonical_feature_registry_v0.57.csv")

    assert pre["status"]=="PASS_LOCAL_FEATURE_LAYER_READY"
    assert pre["required_start_head"]==REQUIRED_START_HEAD
    assert pre["repository_sha"]==IMPLEMENTATION_HEAD
    assert pre["v056_authority"]["workflow_run"]==36235568433
    assert pre["v056_authority"]["artifact"]==10904166471
    assert pre["v056_authority"]["artifact_digest"]=="sha256:17acd42edc06fe7311d88e27ee0a1a2052145e92440e487c2e0f0a47a10709ed"
    assert pre["features"]["existing_numeric"]==23 and pre["features"]["new_numeric"]==11 and pre["features"]["total_numeric"]==34
    assert pre["full_frozen_materialization"]["rows"]==1425
    assert pre["full_frozen_materialization"]["semantic_sha256"]==SEMANTIC_SHA256
    assert pre["full_frozen_materialization"]["existing23_semantic_sha256"]==EXISTING23_SHA256
    assert pre["full_frozen_materialization"]["two_pass_match"] is True
    assert pre["capability_counts"]=={
      "FEATURE_READY":1425,"FEATURE_PARTIAL":0,"FEATURE_BLOCKED_INSUFFICIENT_HISTORY":0,
      "FEATURE_BLOCKED_INPUT":0,"FEATURE_COMPUTATION_ERROR":0,"NOT_VERIFIED":0}
    assert pre["p0_local_feature_layer_ready"] is True
    assert pre["home_market_rs_ready"] is False and pre["sector_rs_ready"] is False
    assert pre["null_nonfinite"]["total"]==0 and pre["semantic_family_blocked"]==0
    assert pre["p0_runs"]==0 and pre["p1_p2_runs"]==0
    assert pre["market_provider_calls"]==0 and pre["yahoo_yfinance_calls"]==0 and pre["eodhd_calls"]==0
    assert pre["alpha_vantage_calls"]==0 and pre["scalable_calls"]==0
    assert pre["price_runtime"]["sha256"]==PRICE_RUNTIME_SHA256 and pre["price_runtime"]["bytes"]==PRICE_RUNTIME_BYTES
    assert pre["frozen"]["sha256"]==FROZEN_SHA256 and pre["frozen"]["members"]==1425

    assert len(mat)==1425 and len(cap)==1425
    assert len({r["Security_Key"] for r in mat})==1425 and len({r["Source_WS_ID"] for r in mat})==1425
    assert sha(src/"feature_materialization_v0.57.csv")==SEMANTIC_SHA256
    assert old[-1]["First_Mismatches"]==EXISTING23_SHA256 and all(r["Result"]=="PASS" for r in old)
    assert len(new)==15675 and all(r["Exact_Match"]=="True" for r in new)
    assert len(asx)==8 and all(r["Result"]=="PASS" for r in asx)
    assert len(temporal)==1425 and all(r["Result"]=="PASS" for r in temporal)
    assert sum(int(r["NonFinite_Total"]) for r in nulls)==0
    assert len(family)==1425 and all(r["Binding_Status"]=="READY" for r in family)
    assert det["match"] is True and det["pass1_semantic_sha256"]==SEMANTIC_SHA256 and det["pass2_semantic_sha256"]==SEMANTIC_SHA256
    assert imm["runtime_sha256_unchanged"] is True and imm["runtime_bytes_unchanged"] is True and imm["frozen_sha256_unchanged"] is True
    assert all(r["Result"]=="PASS" for r in tests)
    assert chk["tests_failed"]==0
    assert len([r for r in registry if r["registry_type"]=="FEATURE"])==34
    assert len([r for r in registry if r["canonical_feature_name"]=="RECENT_IMPULSE_DESCRIPTORS" and r["promotion_status"]=="CANONICAL_SEMANTIC_BINDING_PROMOTED_NO_NEW_COLUMN"])==1

    if out.exists():shutil.rmtree(out)
    shutil.copytree(src,out)

    binding={
      "workflow_run_id":RUN_ID,"workflow_head_sha":IMPLEMENTATION_HEAD,
      "artifact_id":ARTIFACT_ID,"artifact_name":ARTIFACT_NAME,
      "artifact_digest":ARTIFACT_DIGEST,"artifact_verified":"PASS",
      "materialization_semantic_sha256":SEMANTIC_SHA256,
      "materialization_file_sha256":sha(out/"feature_materialization_v0.57.csv"),
      "materialization_file_bytes":(out/"feature_materialization_v0.57.csv").stat().st_size,
      "feature_runtime_database_created":False,
      "price_runtime_input_sha256":PRICE_RUNTIME_SHA256,
      "price_runtime_input_bytes":PRICE_RUNTIME_BYTES}
    (out/"artifact_binding_v0.57.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["artifact_binding"]="PASS"
    summary["feature_artifact"]=binding
    summary["workflow_validation_history"]=[
      {"run_id":36239900498,"conclusion":"failure","scope":"focused floating-point test assertion only; full materialization skipped"},
      {"run_id":RUN_ID,"conclusion":"success","scope":"full Frozen-1425 implementation, two-pass materialization, regression, validation and artifact upload"}]
    summary["next_gate"]="P0 FROZEN-1425 HOME-MARKET RS MATERIALIZATION / CAPABILITY GATE"
    (out/"summary_v0.57.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    checkpoint=dict(chk)
    checkpoint.update({"artifact_binding":"PASS","workflow_run_id":RUN_ID,"artifact_id":ARTIFACT_ID,
                       "artifact_digest":ARTIFACT_DIGEST,"status":"PASS_LOCAL_FEATURE_LAYER_READY"})
    (out/"stage_checkpoint_v0.57.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    newnames="; ".join(pre["features"]["new_numeric_names"])
    report_lines=[
      "# P0 Frozen-1425 Local Feature Contract v0.56 — Implementation / Promotion Gate v0.57","",
      "## 1. Gate verdict","**PASS_LOCAL_FEATURE_LAYER_READY**","",
      "The persisted v0.56 contracts were implemented without semantic changes. The full local technical layer is complete for 1425/1425 Frozen securities. No P0 classification was run.","",
      "## 2. Start HEAD",REQUIRED_START_HEAD,"",
      "## 3. v0.56 authority validation",
      "PASS_ALL8_CONTRACTS_DEFINED; workflow 36235568433; artifact 10904166471; digest sha256:17acd42edc06fe7311d88e27ee0a1a2052145e92440e487c2e0f0a47a10709ed; V0_57_LOCAL_FEATURE_IMPLEMENTATION_AUTHORIZED=YES.","",
      "Frozen=1425, Price Cache READY=1425 / QUARANTINE=0, prior canonical numeric features=23, prior FEATURE_READY=0 / FEATURE_PARTIAL=1425.","",
      "## 4. Implemented and promoted features",newnames,"",
      "RECENT_IMPULSE_DESCRIPTORS is promoted only as the semantic binding {R5,R20,R60,DailyMove_Over_ATR14,RVOL20}; no numeric score/threshold column was created.","",
      "## 5. Formula / contract fidelity",
      "EMA20_Slope_5=EMA20[t]/EMA20[t-5 valid]-1; EMA50_Slope_10=EMA50[t]/EMA50[t-10 valid]-1; Range5_Pct=(High5-Low5)/Close_Tech[t]; Range10_Pct=(High10-Low10)/Close_Tech[t]; RangeCompression_5_20=Range5_Pct/Range20_Pct; RangeCompression_10_20=Range10_Pct/Range20_Pct; RVOL20=Volume_Tech[t]/median(previous 20 valid Volume_Tech), excluding t from baseline; Gap_Over_ATR14=(Open_Tech[t]-Close_Tech[t-1 valid])/ATR14[t-1 valid]; DailyMove_Over_ATR14=(Close_Tech[t]-Close_Tech[t-1 valid])/ATR14[t-1 valid]; Dist_High20=Close_Tech[t]/High20[t]-1; Dist_High60=Close_Tech[t]/High60[t]-1.","",
      "All previous/rolling references count only canonical valid technical observations. No zero-fill, epsilon, infinity or fallback was introduced.","",
      "## 6. Existing-23 regression",
      "PASS for all 23 existing numeric features across all 1425 securities. Semantic SHA remains "+EXISTING23_SHA256+".","",
      "## 7. Full Frozen materialization",
      "Rows=1425; unique Security_Key=1425; unique Source_WS_ID=1425; canonical numeric features=34; semantic SHA-256="+SEMANTIC_SHA256+". Valid-bar range remains 293-508; source-defect securities=8; excluded bars=8.","",
      "## 8. ASX-8 regression","8/8 PASS. Raw defect bars remain stored, are excluded from feature input, new 11 formulas match the filtered series, and defect provenance remains attached.","",
      "## 9. Temporal integrity","1425/1425 PASS; zero eligible observations after feature_as_of_date. Gap/DailyMove use previous valid close and prior ATR14, and RVOL uses a prior-only baseline.","",
      "## 10. Null / non-finite audit","Across all 34 canonical numeric features: canonical null/NaN=0, +Inf=0, -Inf=0. This is empirical for the current Frozen-1425 materialization, not an assumed property.","",
      "## 11. Determinism","Two complete materialization passes match exactly at semantic SHA-256 "+SEMANTIC_SHA256+".","",
      "## 12. Capability counts","FEATURE_READY=1425; FEATURE_PARTIAL=0; FEATURE_BLOCKED_INSUFFICIENT_HISTORY=0; FEATURE_BLOCKED_INPUT=0; FEATURE_COMPUTATION_ERROR=0; NOT_VERIFIED=0.","",
      "## 13. P0_LOCAL_FEATURE_LAYER_READY","**YES**","",
      "## 14. RS status and next ordering","HOME_MARKET_RS_READY=NO; SECTOR_RS_READY=NO. Existing readiness authority is serial: Home-Market RS is the next layer; Sector RS follows separately because its metadata/source authority remains distinct.","",
      "## 15. Parameter authority","Unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json; p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[].","",
      "## 16. Price runtime / Frozen immutability",
      "Price Runtime SHA-256 "+PRICE_RUNTIME_SHA256+" / 144539648 bytes before and after. Frozen remains 1425 members / "+FROZEN_SHA256+". No raw OHLCV, identity or provider mapping mutation.","",
      "## 17. Provider calls","Market-data providers=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.","",
      "## 18. Tests",
      f"{len(tests)}/{len(tests)} persisted validation tests PASS; new-11 formula regression=15675/15675 exact; semantic-family binding=1425/1425 READY. Successful workflow also passed the focused pytest suite.","",
      "An earlier workflow run 36239900498 stopped on a floating-point literal test assertion before full materialization. No artifact was accepted from that failed run.","",
      "## 19. Artifact authority",
      f"Workflow run {RUN_ID}; artifact {ARTIFACT_ID}; artifact digest {ARTIFACT_DIGEST}; feature semantic SHA {SEMANTIC_SHA256}. No feature-runtime database was created.","",
      "## 20. Next gate","**P0 FROZEN-1425 HOME-MARKET RS MATERIALIZATION / CAPABILITY GATE**","",
      "Hard stop: no Home-Market RS executed here, no Sector RS, no P0/P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading."]
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join(report_lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.57.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files["docs/validation/P0_Frozen_1425_Local_Feature_Implementation_Promotion_v0.57.md"]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,
      "implementation_head":IMPLEMENTATION_HEAD,"successful_workflow_run_id":RUN_ID,
      "artifact":binding,"materialization_semantic_sha256":SEMANTIC_SHA256,
      "existing23_semantic_sha256":EXISTING23_SHA256,"price_runtime_sha256":PRICE_RUNTIME_SHA256,
      "price_runtime_bytes":PRICE_RUNTIME_BYTES,"frozen_sha256":FROZEN_SHA256,
      "canonical_numeric_features":34,"capability_counts":pre["capability_counts"],
      "p0_local_feature_layer_ready":True,"home_market_rs_ready":False,"sector_rs_ready":False,
      "p0_runs":0,"provider_calls":{"market":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0},
      "productive":False,"files":files,"next_gate":summary["next_gate"]}
    (out/"manifest_v0.57.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({"status":"PASS_LOCAL_FEATURE_LAYER_READY","artifact_binding":"PASS",
                      "capability_counts":pre["capability_counts"],"p0_local_feature_layer_ready":True,
                      "semantic_sha256":SEMANTIC_SHA256,"next_gate":summary["next_gate"]},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
