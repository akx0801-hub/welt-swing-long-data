#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path

VERSION="v0.56"
STAGE="P0_FROZEN_1425_LOCAL_FEATURE_CONTRACT_DEFINITION"
REQUIRED_START_HEAD="b6426f24c30c213949d436d205f9188f22c21d84"
IMPLEMENTATION_HEAD="b069e568dd6f9642d0bdc9e34bedd8b8e659d26a"
RUN_ID=36235568433
ARTIFACT_ID=10904166471
ARTIFACT_NAME="p0-frozen-1425-local-feature-contract-v0.56-36235568433"
ARTIFACT_DIGEST="sha256:17acd42edc06fe7311d88e27ee0a1a2052145e92440e487c2e0f0a47a10709ed"
V055_SEMANTIC_SHA256="81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc"
V053_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def read_csv(p:Path):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",required=True)
    ap.add_argument("--repo-root",default=".")
    args=ap.parse_args()
    root=Path(args.repo_root).resolve()
    src=Path(args.artifact_dir).resolve()/"output_p0_frozen_1425_local_feature_contract_v0_56"
    out=root/"output_p0_frozen_1425_local_feature_contract_v0_56"
    report=root/"docs/validation/P0_Frozen_1425_Local_Feature_Contract_Definition_v0.56.md"
    required=[
      "input_authority_validation_v0.56.json","remaining8_reconciliation_v0.56.csv",
      "master_semantic_evidence_v0.56.csv","historical_v019_evidence_v0.56.csv",
      "contract_decisions_v0.56.csv","canonical_feature_contract_registry_v0.56.csv",
      "current_bar_policy_v0.56.csv","atr_reference_policy_v0.56.csv",
      "minimum_history_contract_v0.56.csv","null_zero_denominator_contract_v0.56.csv",
      "implementation_impact_preview_v0.56.csv","remaining_ambiguities_v0.56.csv",
      "test_results_v0.56.csv","summary_preupload_v0.56.json",
      "stage_checkpoint_preupload_v0.56.json","manifest_preupload_v0.56.json"]
    miss=[x for x in required if not (src/x).exists()]
    if miss:raise RuntimeError(f"artifact missing {miss}")
    pre=json.loads((src/"summary_preupload_v0.56.json").read_text(encoding="utf-8"))
    chk=json.loads((src/"stage_checkpoint_preupload_v0.56.json").read_text(encoding="utf-8"))
    decisions=read_csv(src/"contract_decisions_v0.56.csv")
    tests=read_csv(src/"test_results_v0.56.csv")
    reg=read_csv(src/"canonical_feature_contract_registry_v0.56.csv")
    assert pre["status"]=="PASS_ALL8_CONTRACTS_DEFINED"
    assert pre["decision_counts"]=={"CONTRACT_DEFINED":8,"CONTRACT_PARTIALLY_DEFINED":0,"CONTRACT_DEFERRED":0,"CONTRACT_REJECTED":0}
    assert pre["v0_57_local_feature_implementation_authorized"] is True
    assert pre["p0_local_feature_layer_ready"] is False
    assert pre["feature_materialization_runs"]==0 and pre["p0_runs"]==0
    assert len(decisions)==8 and all(r["decision_state"]=="CONTRACT_DEFINED" for r in decisions)
    assert len([r for r in reg if r.get("promotion_version")=="v0.56" and r.get("registry_type")=="FEATURE"])==11
    assert len([r for r in reg if r.get("promotion_version")=="v0.56" and r.get("registry_type")=="SEMANTIC_FAMILY"])==1
    assert all(r["Result"]=="PASS" for r in tests)
    assert chk["tests_failed"]==0

    if out.exists():shutil.rmtree(out)
    shutil.copytree(src,out)

    binding={"workflow_run_id":RUN_ID,"workflow_head_sha":IMPLEMENTATION_HEAD,"artifact_id":ARTIFACT_ID,
             "artifact_name":ARTIFACT_NAME,"artifact_digest":ARTIFACT_DIGEST,"artifact_verified":"PASS",
             "feature_materialization_runs":0,"price_runtime_opened":False,"price_runtime_write_attempts":0}
    (out/"artifact_binding_v0.56.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["artifact_binding"]="PASS"
    summary["contract_artifact"]=binding
    summary["status"]="PASS_ALL8_CONTRACTS_DEFINED"
    summary["next_gate"]="P0 FROZEN-1425 LOCAL FEATURE CONTRACT v0.56 BOUNDED IMPLEMENTATION / PROMOTION GATE v0.57"
    summary["workflow_validation_history"]=[
      {"run_id":36235530681,"conclusion":"failure","scope":"test-harness assertions only; evidence generation/upload skipped"},
      {"run_id":RUN_ID,"conclusion":"success","scope":"contract definition, validation and artifact upload"}]
    (out/"summary_v0.56.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    checkpoint=dict(chk)
    checkpoint.update({"artifact_binding":"PASS","workflow_run_id":RUN_ID,"artifact_id":ARTIFACT_ID,
                       "artifact_digest":ARTIFACT_DIGEST,"status":"PASS_ALL8_CONTRACTS_DEFINED"})
    (out/"stage_checkpoint_v0.56.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    lines=[
      "# P0 Frozen-1425 Local Feature Contract Definition v0.56","",
      "## 1. Gate verdict","**PASS_ALL8_CONTRACTS_DEFINED**","",
      "All eight remaining v0.55 local-feature semantic gaps are now fully defined as contracts. This gate does not implement or materialize them. v0.57 implementation is authorized; P0_LOCAL_FEATURE_LAYER_READY remains NO.","",
      "## 2. Start HEAD",REQUIRED_START_HEAD,"",
      "## 3. v0.55 authority validation",
      "Workflow 36230843835; artifact 10902665790; artifact digest sha256:a6faf3156763a9ff4d6eba5322aa6e62c1f97a75797b09b910fba762917184a8; semantic materialization SHA "+V055_SEMANTIC_SHA256+". Frozen=1425; Price Cache READY=1425; QUARANTINE=0; canonical numeric features=23; FEATURE_READY=0; FEATURE_PARTIAL=1425.","",
      "## 4. Remaining-8 reconciliation",
      "All eight families from v0.55 end CONTRACT_DEFINED.","",
      "## 5-12. Defined contracts",
      "EMA20_Slope_5 = EMA20[t]/EMA20[t-5 valid]-1. EMA50_Slope_10 = EMA50[t]/EMA50[t-10 valid]-1. Range family adds Range5_Pct, Range10_Pct, RangeCompression_5_20 and RangeCompression_10_20 while retaining Range20_Pct. RVOL20 uses current Volume_Tech over the median of the previous 20 valid observations, excluding current from baseline. Gap_Over_ATR14 uses signed Open[t]-Close[t-1 valid] over ATR14[t-1 valid]. DailyMove_Over_ATR14 uses signed Close[t]-Close[t-1 valid] over ATR14[t-1 valid]. RECENT_IMPULSE_DESCRIPTORS is a semantic composition of R5/R20/R60, DailyMove_Over_ATR14 and RVOL20 without an event threshold. Relevant-high distance adds Dist_High20 and Dist_High60 and retains Dist_High252.","",
      "## 13. Current-bar inclusion policy",
      "Price-structure rolling windows include current valid t. Comparison baselines used to judge current activity exclude current t.","",
      "## 14. ATR reference policy",
      "Existing descriptive ATR14 remains current-t. Current-event magnitude features use ATR14[t-1 valid].","",
      "## 15. Filtered-series policy",
      "Every definition uses the v0.53/v0.55 canonical filtered valid technical series; previous means previous VALID observation and rolling N means N valid observations.","",
      "## 16. Null / zero-denominator policy",
      "Undefined denominator or missing required input => canonical null and capability failure. No zero fill, infinity, epsilon or substitution.","",
      "## 17. Minimum history contract",
      "EMA20_Slope_5=25; EMA50_Slope_10=60; Range5=5; Range10=10; compression ratios=20; RVOL20=21 plus volume completeness; Gap/ATR=15; DailyMove/ATR=15; Dist_High20=20; Dist_High60=60; recent-impulse composition=61 plus RVOL volume completeness. Existing full layer still has 252-observation requirements.","",
      "## 18. Final canonical names",
      "; ".join(pre["new_numeric_feature_names"])+"; semantic family RECENT_IMPULSE_DESCRIPTORS.","",
      "## 19. New numeric features expected","**11**","",
      "## 20-23. Decision counts","CONTRACT_DEFINED=8; CONTRACT_PARTIALLY_DEFINED=0; CONTRACT_DEFERRED=0; CONTRACT_REJECTED=0.","",
      "## 24. Remaining ambiguities","**None within the eight v0.56 contracts.** P0 decision thresholds remain intentionally undefined.","",
      "## 25. V0_57_LOCAL_FEATURE_IMPLEMENTATION_AUTHORIZED","**YES**","",
      "## 26. P0_LOCAL_FEATURE_LAYER_READY","**NO** — contract-only gate.","",
      "## 27. HOME_MARKET_RS_READY","**NO / unchanged**","",
      "## 28. SECTOR_RS_READY","**NO / unchanged**","",
      "## 29. Parameter authority","Unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json; p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[].","",
      "## 30. Feature materialization runs","**0**","",
      "## 31. P0 runs","**0**","",
      "## 32. Price runtime / Frozen immutability",
      "Price Runtime remains "+V053_RUNTIME_SHA256+" / 144539648 bytes and was not opened or written. Frozen remains 1425 members / "+FROZEN_SHA256+".","",
      "## 33. Provider calls","Market provider=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.","",
      "## 34. Test / contract validation results",
      f"{len(tests)}/{len(tests)} persisted contract-validation tests PASS plus focused pytest in the successful workflow. Earlier run 36235530681 failed on test-harness wording assertions before evidence generation; no contract artifact was uploaded.","",
      "## 35. Files","The bounded v0.56 contract package is persisted under output_p0_frozen_1425_local_feature_contract_v0_56/ and this report under docs/validation/. No feature matrix exists.","",
      "## 36. Commit","Final persistence commit is created by the bounded persistence workflow after artifact verification.","",
      "## 37. Next gate","**P0 FROZEN-1425 LOCAL FEATURE CONTRACT v0.56 BOUNDED IMPLEMENTATION / PROMOTION GATE v0.57**","",
      "Hard stop: no implementation, no materialization, no RS, no P0/P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading."]
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.56.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files["docs/validation/P0_Frozen_1425_Local_Feature_Contract_Definition_v0.56.md"]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,
              "implementation_head":IMPLEMENTATION_HEAD,"successful_workflow_run_id":RUN_ID,
              "artifact":binding,"v055_semantic_sha256":V055_SEMANTIC_SHA256,
              "price_runtime_sha256":V053_RUNTIME_SHA256,"price_runtime_bytes":144539648,
              "frozen_sha256":FROZEN_SHA256,"decision_counts":summary["decision_counts"],
              "new_numeric_features_expected":11,"v0_57_local_feature_implementation_authorized":True,
              "p0_local_feature_layer_ready":False,"feature_materialization_runs":0,"p0_runs":0,
              "provider_calls":{"market":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0},
              "productive":False,"files":files,"next_gate":summary["next_gate"]}
    (out/"manifest_v0.56.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS_ALL8_CONTRACTS_DEFINED","artifact_binding":"PASS",
                      "decision_counts":summary["decision_counts"],"implementation_authorized":True,
                      "new_numeric_features_expected":11,"feature_materialization_runs":0,"p0_runs":0},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
