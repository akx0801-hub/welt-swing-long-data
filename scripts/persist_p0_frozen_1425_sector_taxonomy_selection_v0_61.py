#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

VERSION = "v0.61"
STAGE = "P0_FROZEN_1425_CANONICAL_SECTOR_TAXONOMY_SOURCE_FEASIBILITY_SELECTION_GATE"
REQUIRED_START_HEAD = "b5fda059940710d4e07928b6a8bc7b0b5d536a57"
VERDICT = "BLOCKED_TAXONOMY_SOURCE_FEASIBILITY"
BLOCKER = "FULL_1425_COVERAGE_NOT_VERIFIED"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_sector_taxonomy_selection_v0_61")
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--workflow-run-id", required=True, type=int)
    ap.add_argument("--workflow-head-sha", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    pre = json.loads((out / "summary_preupload_v0.61.json").read_text(encoding="utf-8"))
    chk = json.loads((out / "stage_checkpoint_preupload_v0.61.json").read_text(encoding="utf-8"))
    decision = json.loads((out / "taxonomy_selection_decision_v0.61.json").read_text(encoding="utf-8"))
    tests = read_csv(out / "test_results_v0.61.csv")
    coverage = read_csv(out / "frozen_1425_coverage_feasibility_v0.61.csv")

    if pre["verdict"] != VERDICT:
        raise RuntimeError("unexpected v0.61 verdict")
    if pre["canonical_sector_taxonomy_selected"] is not False or pre["selected_taxonomy"] != "NONE":
        raise RuntimeError("taxonomy was unexpectedly selected")
    if pre["feasible_count"] != 0 or pre["tested_count"] != 2:
        raise RuntimeError("candidate count mismatch")
    if pre["blocker"] != BLOCKER:
        raise RuntimeError("smallest blocker mismatch")
    if decision["mapping_population_executed"] or decision["sector_rs_executed"] or decision["crosswalk_created"]:
        raise RuntimeError("out-of-scope action recorded")
    if len(coverage) != 2850 or any(r["Coverage_Feasibility"] != "NOT_VERIFIED" for r in coverage):
        raise RuntimeError("coverage classification mismatch")
    if any(r["Result"] != "PASS" for r in tests):
        raise RuntimeError("cannot persist failed tests")
    if any(pre["prohibited_provider_calls"].values()):
        raise RuntimeError("prohibited provider call count is nonzero")
    if pre["mapping_population_runs"] != 0 or pre["sector_rs_runs"] != 0:
        raise RuntimeError("materialization count mismatch")
    if pre["p0_runs"] != 0 or pre["p1_runs"] != 0 or pre["p2_runs"] != 0:
        raise RuntimeError("P0/P1/P2 run count mismatch")

    binding = {
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "artifact_id": args.artifact_id,
        "artifact_name": args.artifact_name,
        "artifact_digest": args.artifact_digest,
        "artifact_verified": "PASS",
        "artifact_scope": "pre-persistence v0.61 canonical sector taxonomy source-feasibility evidence package",
    }
    (out / "artifact_binding_v0.61.json").write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = dict(pre)
    summary["artifact_binding"] = "PASS"
    summary["artifact"] = binding
    (out / "summary_v0.61.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = dict(chk)
    checkpoint.update({
        "artifact_binding": "PASS",
        "workflow_run_id": args.workflow_run_id,
        "artifact_id": args.artifact_id,
        "artifact_digest": args.artifact_digest,
    })
    (out / "stage_checkpoint_v0.61.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = Path("docs/validation/P0_Frozen_1425_Canonical_Sector_Taxonomy_Source_Feasibility_Selection_v0.61.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P0 Frozen-1425 Canonical Sector Taxonomy Source-Feasibility / Selection Gate v0.61",
        "",
        "## Verdict",
        f"**{VERDICT}**",
        "",
        "CANONICAL_SECTOR_TAXONOMY_SELECTED = **NO**.",
        "SELECTED TAXONOMY = **NONE**.",
        "FEASIBLE / TESTED = **0 / 2**.",
        "",
        "## Predecessor authority",
        f"- Required start HEAD: {REQUIRED_START_HEAD}",
        "- v0.60 verdict: BLOCKED_GOVERNANCE_AUTHORITY_REQUIRED",
        "- v0.60 blocker: GOVERNANCE_DECISION_REQUIRED_CANONICAL_SECTOR_TAXONOMY",
        "- v0.60 workflow/artifact: 36247871792 / 10907812456",
        "- v0.60 artifact digest: sha256:5caa8bd2a34b096e3b08e5ce9e41f3cabcea9b4b72d55060e20b8ec1bb78f500",
        "",
        "## New manager authority",
        "G-SEC-01 is persisted as explicit manager governance authority. Automatic promotion is permitted only when exactly one candidate taxonomy passes every A-G hard gate and is provably mappable for 1425/1425 Frozen securities. Multiple full-pass candidates require manager governance; zero full-pass candidates fail closed on the earliest concrete blocker.",
        "",
        "## Candidate gate result",
        "### GICS",
        "- A Taxonomy definition: PASS",
        "- B Source class: PASS",
        "- C Bulk/reproducibility: PASS",
        "- D Frozen-1425 coverage feasibility: NOT_VERIFIED",
        "- E Deterministic identity linkage: NOT_VERIFIED",
        "- F Provenance plan: PASS",
        "- G Source access/persistence: NOT_VERIFIED",
        "- Exact coverage classification: PROVABLY_MAPPABLE 0 / NOT_MAPPABLE 0 / NOT_VERIFIED 1425",
        "",
        "Official GICS materials establish a current global, coded taxonomy and official bulk-delivery routes. Public coverage claims are broad, but no entitled official bulk mapping file was accessed in this stage; therefore exact row-level Frozen-1425 coverage is not proven. Official materials also describe GICS data/content as proprietary/licensed and do not establish repository-specific permission for persisting a full mapping.",
        "",
        "### ICB",
        "- A Taxonomy definition: PASS",
        "- B Source class: PASS",
        "- C Bulk/reproducibility: PASS",
        "- D Frozen-1425 coverage feasibility: NOT_VERIFIED",
        "- E Deterministic identity linkage: NOT_VERIFIED",
        "- F Provenance plan: PASS",
        "- G Source access/persistence: NOT_VERIFIED",
        "- Exact coverage classification: PROVABLY_MAPPABLE 0 / NOT_MAPPABLE 0 / NOT_VERIFIED 1425",
        "",
        "Official FTSE Russell materials establish a current coded ICB taxonomy and a bulk ICB Universe route with weekly universe files plus daily updates. The public 85,000-security / 80+-country / 150-exchange statement does not prove that every one of the exact Frozen-1425 securities is present. Public materials also require licence/permission for use or further distribution; no project-specific permission for full mapping persistence is verified.",
        "",
        "## Other single taxonomy",
        "No third candidate was admitted. Bounded official-source research did not establish another concrete taxonomy satisfying G-SEC-01's admission rule. No synthetic third candidate, mixed taxonomy, or crosswalk was created.",
        "",
        "## Selection decision",
        f"Smallest common hard-gate blocker: **{BLOCKER}**.",
        "Because neither candidate reaches 1425/1425 PROVABLY_MAPPABLE, no canonical taxonomy can be selected under G-SEC-01.",
        "",
        "## External research governance",
        "Only bounded official taxonomy/index-administrator sources were used. All invoked official source URLs and bounded findings are persisted in external_request_ledger_v0.61.csv. Alpha Vantage, Yahoo/yfinance, EODHD, Scalable, price/OHLCV downloads, news/trading research and per-security web fanout were not used.",
        "",
        "## Immutability",
        "- Frozen SHA-256 unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb",
        "- v0.57 Feature Semantic SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9",
        "- v0.58 Home-Market-RS Semantic SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32",
        "- P0/P1/P2 runs: 0",
        "- Sector mapping population runs: 0",
        "- Sector-RS runs: 0",
        "",
        "## Artifact binding",
        f"- Workflow run: {args.workflow_run_id}",
        f"- Workflow head: {args.workflow_head_sha}",
        f"- Artifact: {args.artifact_id}",
        f"- Artifact name: {args.artifact_name}",
        f"- Artifact digest: {args.artifact_digest}",
        "",
        "## Next gate",
        f"**{BLOCKER}**",
        "",
        "Hard stop: no mapping population, no Sector RS, no crosswalk, no P0/P1/P2, no shortlist, no trading statement.",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    files = {}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "manifest_v0.61.json":
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    files[str(report)] = {"sha256": sha256_file(report), "bytes": report.stat().st_size}

    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "required_start_head": REQUIRED_START_HEAD,
        "canonical_sector_taxonomy_selected": False,
        "selected_taxonomy": "NONE",
        "feasible_count": 0,
        "tested_count": 2,
        "blocker": BLOCKER,
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "artifact": binding,
        "frozen_sha256": pre["immutability"]["frozen_expected_sha256"],
        "v057_feature_sha256": pre["immutability"]["v057_feature_expected_sha256"],
        "v058_home_rs_sha256": pre["immutability"]["v058_home_rs_expected_sha256"],
        "prohibited_provider_calls": pre["prohibited_provider_calls"],
        "mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "files": files,
        "next_gate": BLOCKER,
    }
    (out / "manifest_v0.61.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": VERDICT,
        "canonical_sector_taxonomy_selected": False,
        "selected_taxonomy": "NONE",
        "feasible": 0,
        "tested": 2,
        "blocker": BLOCKER,
        "workflow_run": args.workflow_run_id,
        "artifact": args.artifact_id,
        "next_gate": BLOCKER,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
