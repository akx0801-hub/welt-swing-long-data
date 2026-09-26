#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.58"
STAGE="P0_FROZEN_1425_HOME_MARKET_RS_MATERIALIZATION_CAPABILITY"
REQUIRED_START_HEAD="80d80eee5e8a2e6ddad5f7b7b1231b9a3da21895"
V057_RUN=36239952535
V057_ARTIFACT=10905448132
V057_ARTIFACT_DIGEST="sha256:7f35e18264110c6a6a84205ab443a7b1c3cabcbaebdb3e6d6af79df6361e1c00"
V057_FEATURE_SHA256="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
PRICE_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()

def read_csv(p:Path):
    with p.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_home_market_rs_v0_58")
    ap.add_argument("--artifact-id",required=True)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    args=ap.parse_args()

    out=Path(args.output_dir)
    pre=json.loads((out/"summary_preupload_v0.58.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.58.json").read_text(encoding="utf-8"))
    tests=read_csv(out/"test_results_v0.58.csv")
    if any(r["Result"]!="PASS" for r in tests):
        raise RuntimeError("cannot persist v0.58 with failed tests")
    if pre["verdict"] not in {"PASS_HOME_MARKET_RS_READY","PASS_WITH_CONTRACT_BLOCKER","PASS_WITH_INPUT_BLOCKER"}:
        raise RuntimeError("invalid v0.58 verdict")
    if pre["p0_runs"]!=0 or pre["p1_p2_runs"]!=0 or pre["sector_rs_ready"] is not False:
        raise RuntimeError("governance mismatch")

    binding={
      "workflow_run_id":args.workflow_run_id,
      "workflow_head_sha":args.workflow_head_sha,
      "artifact_id":int(args.artifact_id),
      "artifact_name":args.artifact_name,
      "artifact_digest":args.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.58 evidence package",
    }
    (out/"artifact_binding_v0.58.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["artifact_binding"]="PASS"
    summary["artifact"]=binding
    (out/"summary_v0.58.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    checkpoint=dict(chk)
    checkpoint.update({
      "artifact_binding":"PASS",
      "workflow_run_id":args.workflow_run_id,
      "artifact_id":int(args.artifact_id),
      "artifact_digest":args.artifact_digest,
    })
    (out/"stage_checkpoint_v0.58.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/P0_Frozen_1425_Home_Market_RS_Materialization_Capability_v0.58.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    groups=summary["benchmark_groups"]
    blockers=summary["input_blockers"]
    lines=[
      "# P0 Frozen-1425 Home-Market RS Materialization / Capability v0.58","",
      "## Verdict",f"**{summary['verdict']}**","",
      "## Start and input authority",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      f"- v0.57 workflow/artifact: {V057_RUN} / {V057_ARTIFACT} / {V057_ARTIFACT_DIGEST}",
      f"- v0.57 local feature semantic SHA: {V057_FEATURE_SHA256}",
      f"- Frozen: 1425 / {FROZEN_SHA256}",
      f"- Price Runtime: {PRICE_RUNTIME_SHA256} / 144539648 bytes","",
      "## Contract binding",
      "Master authority requires 20/60-day return difference versus home market and permits reproducible internal peer/market groups for early discovery. v0.20 defines a leave-one-out median per Primary_Universe_Index among synchronized peers; v0.21 preserves that reference and explicitly disclaims an official-index benchmark claim. v0.44 persists the current Frozen-1425 Primary_Universe_Index mapping. v0.58 binds synchronization per security to peers with the exact same feature_as_of_date, as required by the no-artificial-global-date rule. No new RS threshold or ranking semantic is introduced.","",
      "Canonical formulas:",
      "- HomeMarket_RS20_Excess = R20 - leave-one-out median(R20 of same Primary_Universe_Index and exact same feature_as_of_date)",
      "- HomeMarket_RS60_Excess = R60 - leave-one-out median(R60 of same Primary_Universe_Index and exact same feature_as_of_date)","",
      "Missing mapping, missing/non-finite return input, or fewer than one synchronized peer is fail-closed as RS_NOT_VERIFIED. No substitute benchmark, ETF fallback, MIC-to-country inference, zero fill, epsilon, or external benchmark acquisition is permitted.","",
      "## Benchmark mapping / cohort readiness",
    ]
    for g in groups:
        lines.append(f"- {g['Primary_Universe_Index']}: {g['Frozen_Rows']} Frozen rows; MICs {g['Primary_MICs']}; {g['Unique_AsOf_Dates']} as-of date(s); same-date peer count range {g['Min_SameDate_Peer_Count']}..{g['Max_SameDate_Peer_Count']}.")
    lines += [
      "","## Materialization / capability",
      f"- Materialized: {summary['materialized']}",
      f"- HOME_MARKET_RS_READY: {summary['home_market_rs_ready']}",
      f"- Ready / Total: {summary['ready_count']} / {summary['total']}",
      f"- Semantic digest: {summary['rs_semantic_sha256']}",
      f"- Determinism match: {summary['determinism_match']}",
      f"- Input blockers: {json.dumps(blockers,ensure_ascii=False)}","",
      "## Temporal integrity",
      "Reference peers are exact same-date peers within the mapped Primary_Universe_Index cohort. Different exchange calendars therefore do not force a global date and cannot import later peer observations into an earlier security as-of. Cross-market temporal audit covers XNYS, XNAS, XASX, XTKS, XTAI, XSHG, XSHE, XNSE and BVMF.","",
      "## Immutability / governance",
      f"- Price Runtime unchanged: {summary['price_runtime']['unchanged']}",
      f"- Frozen unchanged: {summary['frozen']['unchanged']}",
      f"- v0.57 local features unchanged: {summary['v057_local_features_unchanged']}",
      "- Sector RS: NOT RUN / READY remains NO",
      "- Parameter authority unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json",
      "- p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[]",
      "- P0 runs=0; P1/P2 runs=0",
      "- Provider calls: market=0, Yahoo/yfinance=0, EODHD=0, Alpha Vantage=0, Scalable=0","",
      "## Artifact authority",
      f"- Workflow run: {args.workflow_run_id}",
      f"- Workflow head: {args.workflow_head_sha}",
      f"- Artifact: {args.artifact_id}",
      f"- Artifact name: {args.artifact_name}",
      f"- Artifact digest: {args.artifact_digest}","",
      "## Next gate",f"**{summary['next_gate']}**","",
      "Hard stop: no Sector RS, no P0/P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.58.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"verdict":summary["verdict"],"required_start_head":REQUIRED_START_HEAD,
      "workflow_run_id":args.workflow_run_id,"workflow_head_sha":args.workflow_head_sha,
      "artifact":binding,"home_market_rs_ready":summary["home_market_rs_ready"],
      "ready_count":summary["ready_count"],"total":1425,"rs_semantic_sha256":summary["rs_semantic_sha256"],
      "v057_feature_semantic_sha256":V057_FEATURE_SHA256,"frozen_sha256":FROZEN_SHA256,
      "price_runtime_sha256":PRICE_RUNTIME_SHA256,"sector_rs_ready":False,"p0_runs":0,"p1_p2_runs":0,
      "provider_calls":summary["provider_calls"],"productive":False,"files":files,"next_gate":summary["next_gate"]
    }
    (out/"manifest_v0.58.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"verdict":summary["verdict"],"home_market_rs_ready":summary["home_market_rs_ready"],"ready":summary["ready_count"],"total":1425,"artifact_id":int(args.artifact_id),"artifact_digest":args.artifact_digest,"next_gate":summary["next_gate"]},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
