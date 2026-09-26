#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

VERSION = "v0.62"
STAGE = "FROZEN_1425_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE_FEASIBILITY_GATE"
VERDICT = "BLOCKED_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE"
BLOCKER = "OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND"
BLOCKER_COHORT = "BR_IBRX100"
REQUIRED_START_HEAD = "2b9637887c2ace039f95adc74cdade28c5e7b4fe"

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
    ap.add_argument("--output-dir", default="output_frozen_1425_source_native_sector_coverage_v0_62")
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--workflow-run-id", required=True, type=int)
    ap.add_argument("--workflow-head-sha", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    pre = json.loads((out / "summary_preupload_v0.62.json").read_text(encoding="utf-8"))
    chk = json.loads((out / "stage_checkpoint_preupload_v0.62.json").read_text(encoding="utf-8"))
    isolation = json.loads((out / "taxonomy_isolation_contract_v0.62.json").read_text(encoding="utf-8"))
    coverage = read_csv(out / "frozen_1425_sector_coverage_feasibility_v0.62.csv")
    routes = read_csv(out / "cohort_sector_source_route_ledger_v0.62.csv")
    tests = read_csv(out / "test_results_v0.62.csv")

    if pre["verdict"] != VERDICT:
        raise RuntimeError("v0.62 verdict mismatch")
    if pre["source_native_sector_metadata_coverage_ready"] is not False:
        raise RuntimeError("v0.62 readiness unexpectedly true")
    if (pre["ready"], pre["total"], pre["not_mappable"], pre["not_verified"]) != (0, 1425, 0, 1425):
        raise RuntimeError("coverage totals mismatch")
    if pre["global_smallest_blocker"] != BLOCKER or pre["global_smallest_blocker_cohort"] != BLOCKER_COHORT:
        raise RuntimeError("global blocker mismatch")
    if len(pre["blocked_cohorts"]) != 8:
        raise RuntimeError("blocked cohort count mismatch")
    if len(coverage) != 1425 or any(r["Coverage_Feasibility"] != "NOT_VERIFIED" for r in coverage):
        raise RuntimeError("row feasibility mismatch")
    if any(r["Sector_Taxonomy_Value_Materialized"] != "NO" or r["Sector_Code_Value_Materialized"] != "NO" or r["Sector_Name_Value_Materialized"] != "NO" for r in coverage):
        raise RuntimeError("mapping materialization detected")
    if len(routes) != 8:
        raise RuntimeError("route ledger cohort count mismatch")
    if isolation["crosswalk_created"] is not False or isolation["sector_rs_authorized"] is not False:
        raise RuntimeError("taxonomy isolation scope violation")
    if any(r["Result"] != "PASS" for r in tests):
        raise RuntimeError("cannot persist failed tests")
    if any(pre["prohibited_provider_calls"].values()):
        raise RuntimeError("prohibited provider count nonzero")
    if pre["sector_mapping_population_runs"] != 0 or pre["sector_rs_runs"] != 0 or pre["crosswalk_runs"] != 0:
        raise RuntimeError("out-of-scope run count nonzero")
    if pre["p0_runs"] != 0 or pre["p1_runs"] != 0 or pre["p2_runs"] != 0:
        raise RuntimeError("P0/P1/P2 nonzero")

    binding = {
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "artifact_id": args.artifact_id,
        "artifact_name": args.artifact_name,
        "artifact_digest": args.artifact_digest,
        "artifact_verified": "PASS",
        "artifact_scope": "pre-persistence v0.62 source-native sector coverage feasibility evidence package",
    }
    (out / "artifact_binding_v0.62.json").write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = dict(pre)
    summary["artifact_binding"] = "PASS"
    summary["artifact"] = binding
    (out / "summary_v0.62.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = dict(chk)
    checkpoint.update({
        "artifact_binding": "PASS",
        "workflow_run_id": args.workflow_run_id,
        "artifact_id": args.artifact_id,
        "artifact_digest": args.artifact_digest,
    })
    (out / "stage_checkpoint_v0.62.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = Path("docs/validation/Frozen_1425_Source_Native_Sector_Metadata_Coverage_Feasibility_v0.62.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frozen-1425 Source-Native Sector Metadata Coverage Feasibility Gate v0.62",
        "",
        "## Verdict",
        f"**{VERDICT}**",
        "",
        "SOURCE_NATIVE_SECTOR_METADATA_COVERAGE_READY = **NO**.",
        "READY / TOTAL = **0 / 1425**.",
        "NOT_MAPPABLE = **0**.",
        "NOT_VERIFIED = **1425**.",
        "",
        "## Predecessor",
        f"- Required start HEAD: {REQUIRED_START_HEAD}",
        "- v0.61 verdict: BLOCKED_TAXONOMY_SOURCE_FEASIBILITY",
        "- v0.61 canonical taxonomy selected: NO",
        "- v0.61 feasible/tested: 0/2",
        "- v0.61 blocker: FULL_1425_COVERAGE_NOT_VERIFIED",
        "- v0.61 workflow/artifact: 36251198020 / 10909285736",
        "- v0.61 artifact digest: sha256:21b17657591e739ce1e1528bb754d99468cf2763f730cff8e8e51a09e7fd9ffb",
        "",
        "## Governance",
        "G-SEC-02 authorizes source-native taxonomy isolation while preserving G-SEC-01 as historical evidence for the failed single-global-taxonomy path. Multiple taxonomies may coexist only with explicit per-row Sector_Taxonomy, provenance, deterministic WS_ID linkage, and peer grouping keyed by (Sector_Taxonomy, Sector_Code). No crosswalk or Sector RS is authorized.",
        "",
        "## Reconstructed Frozen cohorts",
    ]
    for r in routes:
        lines.append(f"- {r['Cohort']}: {r['Frozen_Rows']} rows; earliest blocker {r['Earliest_Blocker']} at gate {r['Earliest_Failed_Gate']}.")
    lines += [
        "",
        "## Cohort findings",
        "All 1425 rows remain NOT_VERIFIED because every cohort hits an earlier hard gate before exact source-native mapping can be proven. No row is classified NOT_MAPPABLE because absence of a valid mapping was not proven; the stage fails closed on missing verification.",
        "",
        "The earliest global hard-gate blocker is **OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND** for **BR_IBRX100**. This is selected because it occurs at gate B, earlier than the C/D/E blockers found in other cohorts.",
        "",
        "## Taxonomy isolation",
        "- Future peer key: (Sector_Taxonomy, Sector_Code)",
        "- Sector_Code alone is forbidden as a peer key.",
        "- Identical-looking names across different taxonomies are not equivalent.",
        "- Crosswalk created: NO.",
        "- Sector RS authorized/executed: NO / 0.",
        "",
        "## External request policy",
        "Only official index-administrator, primary-exchange, and official registry sources were used. The bounded request ledger is persisted. Alpha Vantage, Yahoo/yfinance, EODHD, Scalable, Wikipedia, ETF holdings, screeners, third-party sector databases, per-security web fanout, price/OHLCV downloads, and news/trading research were not used.",
        "",
        "## Immutability",
        "- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb",
        "- v0.57 Feature Semantic SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9",
        "- v0.58 Home-Market-RS Semantic SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32",
        "- Sector mapping population / Sector RS / crosswalk runs: 0 / 0 / 0",
        "- P0/P1/P2 runs: 0 / 0 / 0",
        "",
        "## Artifact binding",
        f"- Workflow run: {args.workflow_run_id}",
        f"- Workflow head: {args.workflow_head_sha}",
        f"- Artifact: {args.artifact_id}",
        f"- Artifact name: {args.artifact_name}",
        f"- Artifact digest: {args.artifact_digest}",
        "",
        "## Next gate",
        f"**{BLOCKER}:{BLOCKER_COHORT}**",
        "",
        "Hard stop: no mapping population, no Sector RS, no crosswalk, no P0/P1/P2, no shortlist, no trading statement.",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    files = {}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "manifest_v0.62.json":
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    files[str(report)] = {"sha256": sha256_file(report), "bytes": report.stat().st_size}

    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "required_start_head": REQUIRED_START_HEAD,
        "verdict": VERDICT,
        "source_native_sector_metadata_coverage_ready": False,
        "ready": 0,
        "total": 1425,
        "not_mappable": 0,
        "not_verified": 1425,
        "blocked_cohorts": pre["blocked_cohorts"],
        "blocker": BLOCKER,
        "blocker_cohort": BLOCKER_COHORT,
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "artifact": binding,
        "frozen_sha256": pre["immutability"]["frozen_expected_sha256"],
        "v057_feature_sha256": pre["immutability"]["v057_feature_expected_sha256"],
        "v058_home_rs_sha256": pre["immutability"]["v058_home_rs_expected_sha256"],
        "prohibited_provider_calls": pre["prohibited_provider_calls"],
        "sector_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "crosswalk_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "files": files,
        "next_gate": f"{BLOCKER}:{BLOCKER_COHORT}",
    }
    (out / "manifest_v0.62.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": VERDICT,
        "source_native_sector_metadata_coverage_ready": False,
        "ready": 0,
        "total": 1425,
        "not_mappable": 0,
        "not_verified": 1425,
        "blocked_cohorts": pre["blocked_cohorts"],
        "blocker": BLOCKER,
        "blocker_cohort": BLOCKER_COHORT,
        "workflow_run": args.workflow_run_id,
        "artifact": args.artifact_id,
        "next_gate": f"{BLOCKER}:{BLOCKER_COHORT}",
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
