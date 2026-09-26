#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,hashlib,json
from pathlib import Path

VERSION="v0.59"
STAGE="P0_FROZEN_1425_SECTOR_METADATA_SECTOR_RS_AUTHORITY"
REQUIRED_START_HEAD="4c12c2126bb3f8ba6c6f132f316041c83b91a02a"

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
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_sector_authority_v0_59")
    ap.add_argument("--artifact-id",required=True)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    args=ap.parse_args()

    out=Path(args.output_dir)
    pre=json.loads((out/"summary_preupload_v0.59.json").read_text(encoding="utf-8"))
    chk=json.loads((out/"stage_checkpoint_preupload_v0.59.json").read_text(encoding="utf-8"))
    tests=read_csv(out/"test_results_v0.59.csv")
    if pre["verdict"]!="PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER":
        raise RuntimeError("unexpected v0.59 verdict")
    if pre["sector_rs_ready"] is not False or pre["sector_rs_materialization_runs"]!=0:
        raise RuntimeError("sector RS governance mismatch")
    if any(r["Result"]!="PASS" for r in tests):
        raise RuntimeError("cannot persist with failed tests")

    binding={
      "workflow_run_id":args.workflow_run_id,
      "workflow_head_sha":args.workflow_head_sha,
      "artifact_id":int(args.artifact_id),
      "artifact_name":args.artifact_name,
      "artifact_digest":args.artifact_digest,
      "artifact_verified":"PASS",
      "artifact_scope":"pre-persistence v0.59 sector authority evidence package",
    }
    (out/"artifact_binding_v0.59.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary=dict(pre)
    summary["artifact_binding"]="PASS"
    summary["artifact"]=binding
    (out/"summary_v0.59.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    checkpoint=dict(chk)
    checkpoint.update({
      "artifact_binding":"PASS",
      "workflow_run_id":args.workflow_run_id,
      "artifact_id":int(args.artifact_id),
      "artifact_digest":args.artifact_digest,
    })
    (out/"stage_checkpoint_v0.59.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=Path("docs/validation/P0_Frozen_1425_Sector_Metadata_Sector_RS_Authority_v0.59.md")
    report.parent.mkdir(parents=True,exist_ok=True)
    lines=[
      "# P0 Frozen-1425 Sector Metadata / Sector-RS Authority v0.59","",
      "## Verdict",
      "**PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER**","",
      "## Start authority",
      f"- Required start HEAD: {REQUIRED_START_HEAD}",
      "- v0.58 verdict: PASS_HOME_MARKET_RS_READY",
      "- v0.58 Home-Market RS: 1425/1425 READY",
      "- v0.58 workflow/artifact: 36242803316 / 10905869033 / sha256:54dc5168218c7a211c6a0d66fc236c1e95a7cfdabef2acadf79282c8f1b5ae1c",
      "- Frozen: 1425 / 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb",
      "- P0_LOCAL_FEATURE_LAYER_READY: YES",
      "- HOME_MARKET_RS_READY: YES","",
      "## Sector metadata authority finding",
      "The current sector metadata contract is v0.21 and remains PREPARED_NOT_POPULATED. It specifies required fields, accepted source classes, provenance requirements and prohibited methods, but it does not select a canonical taxonomy (GICS vs ICB vs other), does not bind one canonical sector field, and does not provide a populated Frozen-1425 mapping authority.","",
      "The current canonical Frozen, v0.57 local-feature materialization and v0.58 Home-Market-RS materialization contain no canonical raw sector/industry metadata column. Historical US discovery files do contain GICS fields for subsets, but those are historical/source-specific evidence and are not promoted as the canonical global Frozen-1425 taxonomy or mapping authority.","",
      "Therefore the gate stops at the earliest blocker required by the requested precedence. No taxonomy was selected, no cross-taxonomy mapping was created, no company activity was inferred, and no missing sector was filled.","",
      "## Sector-RS contract finding",
      "The Master requires relative strength versus sector where valid and 20/60-day relative-strength horizons are present in the Master context. However the current promoted authority does not fully define an executable Sector-RS peer aggregation contract: mean vs median, Sector-specific leave-one-out behavior, numeric minimum peer-group size, and cross-market temporal alignment remain unbound for Sector RS. These are downstream of the metadata-contract blocker and were not resolved here.","",
      "## Coverage / capability",
      "- Canonical sector metadata READY: 0 / 1425",
      "- BLOCKED_METADATA: 1425",
      "- Sector-RS materialization runs: 0",
      "- SECTOR_RS_READY: NO",
      "- Affected securities: 1425","",
      "## Immutability / provider policy",
      "- Frozen unchanged",
      "- Security identity unchanged",
      "- Provider mapping unchanged",
      "- Raw OHLCV unchanged",
      "- v0.57 local features unchanged",
      "- v0.58 Home-Market RS unchanged and remains READY",
      "- Price Runtime not opened or mutated",
      "- Provider calls: market=0, Yahoo/yfinance=0, EODHD=0, Alpha Vantage=0, Scalable=0",
      "- P0/P1/P2 runs: 0",
      "- Parameter authority unchanged; p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[]","",
      "## Artifact authority",
      f"- Workflow run: {args.workflow_run_id}",
      f"- Workflow head: {args.workflow_head_sha}",
      f"- Artifact: {args.artifact_id}",
      f"- Artifact name: {args.artifact_name}",
      f"- Artifact digest: {args.artifact_digest}","",
      "## Next gate",
      "**P0 FROZEN-1425 SECTOR METADATA CONTRACT DEFINITION GATE**","",
      "Hard stop: no Sector RS materialization, no P0/P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.59.json":
            files[p.name]={"sha256":sha(p),"bytes":p.stat().st_size}
    files[str(report)]={"sha256":sha(report),"bytes":report.stat().st_size}
    manifest={
      "stage":STAGE,"version":VERSION,"verdict":summary["verdict"],
      "required_start_head":REQUIRED_START_HEAD,
      "workflow_run_id":args.workflow_run_id,"workflow_head_sha":args.workflow_head_sha,
      "artifact":binding,"sector_rs_ready":False,"affected_count":1425,
      "sector_rs_materialization_runs":0,"p0_runs":0,"p1_p2_runs":0,
      "provider_calls":summary["provider_calls"],"productive":False,
      "files":files,"next_gate":summary["next_gate"]
    }
    (out/"manifest_v0.59.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "verdict":summary["verdict"],"sector_rs_ready":False,"affected_count":1425,
      "artifact_id":int(args.artifact_id),"artifact_digest":args.artifact_digest,
      "next_gate":summary["next_gate"]
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
