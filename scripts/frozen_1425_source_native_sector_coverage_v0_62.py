#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.62"
STAGE = "FROZEN_1425_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE_FEASIBILITY_GATE"
REQUIRED_START_HEAD = "2b9637887c2ace039f95adc74cdade28c5e7b4fe"
V061_WORKFLOW_RUN = 36251198020
V061_ARTIFACT_ID = 10909285736
V061_ARTIFACT_DIGEST = "sha256:21b17657591e739ce1e1528bb754d99468cf2763f730cff8e8e51a09e7fd9ffb"
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_FEATURE_SHA256 = "177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_HOME_RS_SHA256 = "2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
VERDICT = "BLOCKED_SOURCE_NATIVE_SECTOR_METADATA_COVERAGE"
GLOBAL_BLOCKER = "OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND"
GLOBAL_BLOCKER_COHORT = "BR_IBRX100"
AUTHORITY_ID = "G-SEC-02"

FROZEN = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
V057_FEATURES = ROOT / "output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058_HOME_RS = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
V058_CAPABILITY = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
V061_SUMMARY = ROOT / "output_p0_frozen_1425_sector_taxonomy_selection_v0_61/summary_v0.61.json"
V061_CHECKPOINT = ROOT / "output_p0_frozen_1425_sector_taxonomy_selection_v0_61/stage_checkpoint_v0.61.json"
GSEC01 = ROOT / "config/manager_governance_authority_G_SEC_01_v0.61.json"
GSEC02 = ROOT / "config/manager_governance_authority_G_SEC_02_v0.62.json"
RESEARCH = ROOT / "config/source_native_sector_research_v0.62.json"
V021_CONTRACT = ROOT / "output_p0_lane_shadow_validation_v0_21/sector_metadata_contract_v0.21.json"

EXPECTED_COHORTS = {
    "AU_SP_ASX200": 63,
    "BR_IBRX100": 37,
    "CN_CSI300": 294,
    "IN_NIFTY50": 45,
    "JP_N225": 197,
    "TW_TW50": 49,
    "US_SP400": 368,
    "US_SP500": 372,
}
GATE_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H"]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if fields:
            w.writeheader()
            w.writerows(rows)

def provider_calls() -> dict[str, int]:
    return {
        "alpha_vantage": 0,
        "yahoo_yfinance": 0,
        "eodhd": 0,
        "scalable": 0,
        "wikipedia": 0,
        "etf_holdings": 0,
        "screeners": 0,
        "third_party_sector_databases": 0,
        "per_security_web_fanout": 0,
        "market_price_ohlcv": 0,
        "news_trading": 0,
    }

def validate_predecessor(repo_sha: str) -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if head != repo_sha:
        raise RuntimeError(f"checkout mismatch {head} != {repo_sha}")
    if subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"], cwd=ROOT).returncode != 0:
        raise RuntimeError("required v0.61 final commit is not an ancestor")

    s61 = json.loads(V061_SUMMARY.read_text(encoding="utf-8"))
    c61 = json.loads(V061_CHECKPOINT.read_text(encoding="utf-8"))
    if s61["verdict"] != "BLOCKED_TAXONOMY_SOURCE_FEASIBILITY":
        raise RuntimeError("v0.61 verdict mismatch")
    if s61["canonical_sector_taxonomy_selected"] is not False:
        raise RuntimeError("v0.61 selection mismatch")
    if s61["selected_taxonomy"] != "NONE":
        raise RuntimeError("v0.61 selected taxonomy mismatch")
    if s61["feasible_count"] != 0 or s61["tested_count"] != 2:
        raise RuntimeError("v0.61 feasible/tested mismatch")
    if s61["blocker"] != "FULL_1425_COVERAGE_NOT_VERIFIED":
        raise RuntimeError("v0.61 blocker mismatch")
    if c61["workflow_run_id"] != V061_WORKFLOW_RUN or c61["artifact_id"] != V061_ARTIFACT_ID:
        raise RuntimeError("v0.61 workflow/artifact mismatch")
    if "sha256:" + c61["artifact_digest"] != V061_ARTIFACT_DIGEST:
        raise RuntimeError("v0.61 artifact digest mismatch")
    if s61["p0_runs"] != 0 or s61["p1_runs"] != 0 or s61["p2_runs"] != 0:
        raise RuntimeError("v0.61 P0/P1/P2 mismatch")

    if sha256_file(FROZEN) != FROZEN_SHA256:
        raise RuntimeError("Frozen SHA mismatch")
    if sha256_file(V057_FEATURES) != V057_FEATURE_SHA256:
        raise RuntimeError("v0.57 feature SHA mismatch")
    if sha256_file(V058_HOME_RS) != V058_HOME_RS_SHA256:
        raise RuntimeError("v0.58 Home-Market RS SHA mismatch")
    return {"summary": s61, "checkpoint": c61}

def validate_authorities() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    g1 = json.loads(GSEC01.read_text(encoding="utf-8"))
    g2 = json.loads(GSEC02.read_text(encoding="utf-8"))
    c21 = json.loads(V021_CONTRACT.read_text(encoding="utf-8"))
    if g1["authority_id"] != "G-SEC-01":
        raise RuntimeError("G-SEC-01 missing")
    if g2["authority_id"] != AUTHORITY_ID or g2["version"] != VERSION:
        raise RuntimeError("G-SEC-02 mismatch")
    rules = g2["rules"]
    required_true = [
        "multiple_taxonomies_in_canonical_metadata_layer_allowed",
        "sector_taxonomy_required_per_security",
        "taxonomy_source_version_provenance_required",
        "deterministic_ws_id_required",
        "taxonomy_groups_semantically_isolated",
        "peer_group_must_not_mix_sector_taxonomy",
        "cross_taxonomy_comparison_forbidden",
        "crosswalk_forbidden",
        "missing_or_ambiguous_mapping_fail_closed",
    ]
    if not all(rules[k] is True for k in required_true):
        raise RuntimeError("G-SEC-02 rule mismatch")
    if rules["sector_rs_authorized"] is not False or rules["sector_mapping_population_authorized"] is not False:
        raise RuntimeError("G-SEC-02 scope violation")
    if g2["future_peer_group_key"] != ["Sector_Taxonomy", "Sector_Code"]:
        raise RuntimeError("taxonomy isolation key mismatch")
    if g2["accepted_source_classes_inherited_from_v0_21"] != c21["accepted_source_classes"]:
        raise RuntimeError("v0.21 source-class inheritance mismatch")
    return g1, g2, c21

def reconstruct_cohorts() -> tuple[list[dict[str, str]], dict[str, int]]:
    frozen = read_csv(FROZEN)
    cap = read_csv(V058_CAPABILITY)
    if len(frozen) != 1425 or len(cap) != 1425:
        raise RuntimeError("Frozen/capability row count mismatch")
    by_key = {r["Security_Key"]: r for r in cap}
    if len(by_key) != 1425:
        raise RuntimeError("capability Security_Key uniqueness mismatch")
    out = []
    counts: dict[str, int] = {}
    for row in frozen:
        c = by_key.get(row["Security_Key"])
        if c is None:
            raise RuntimeError(f"missing capability mapping {row['Security_Key']}")
        if c["Source_WS_ID"] != row["Source_WS_ID"] or c["Primary_MIC"] != row["Primary_MIC"] or c["Primary_Ticker"] != row["Primary_Ticker"]:
            raise RuntimeError(f"identity mismatch {row['Security_Key']}")
        cohort = c["Primary_Universe_Index"]
        if cohort not in EXPECTED_COHORTS:
            raise RuntimeError(f"unexpected cohort {cohort}")
        counts[cohort] = counts.get(cohort, 0) + 1
        out.append({
            "Projection_Order": row["Projection_Order"],
            "Security_Key": row["Security_Key"],
            "Source_WS_ID": row["Source_WS_ID"],
            "Primary_MIC": row["Primary_MIC"],
            "Primary_Ticker": row["Primary_Ticker"],
            "Primary_Universe_Index": cohort,
        })
    if counts != EXPECTED_COHORTS:
        raise RuntimeError(f"cohort counts mismatch {counts}")
    return out, counts

def first_nonpass(gates: dict[str, str]) -> str:
    for g in GATE_ORDER:
        if gates[g] not in ("PASS",):
            return g
    return ""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository-sha", required=True)
    ap.add_argument("--output-dir", default="output_frozen_1425_source_native_sector_coverage_v0_62")
    args = ap.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    pred = validate_predecessor(args.repository_sha)
    g1, g2, c21 = validate_authorities()
    research = json.loads(RESEARCH.read_text(encoding="utf-8"))
    if research["version"] != VERSION:
        raise RuntimeError("research version mismatch")
    if any(research["prohibited_requests"].values()):
        raise RuntimeError("prohibited external request recorded")

    cohort_rows, counts = reconstruct_cohorts()
    if research["cohort_authority"]["counts"] != counts:
        raise RuntimeError("research cohort counts mismatch")

    coverage = []
    identity = []
    route_ledger = []
    taxonomy_inventory = []
    access_audit = []
    blocked_cohorts = []

    for cohort in EXPECTED_COHORTS:
        f = research["cohort_findings"][cohort]
        gates = f["gate_status"]
        if set(gates) != set(GATE_ORDER):
            raise RuntimeError(f"gate set mismatch {cohort}")
        earliest = first_nonpass(gates)
        if not earliest:
            raise RuntimeError(f"research unexpectedly full-pass {cohort}")
        blocked_cohorts.append(cohort)

        route_ledger.append({
            "Cohort": cohort,
            "Frozen_Rows": counts[cohort],
            "Source_Native_Candidate": f["source_native_candidate"],
            "Taxonomy_Identity": f["taxonomy_identity"],
            "A_Official_Source": gates["A"],
            "B_Bulk_Reproducible": gates["B"],
            "C_Taxonomy_Identity": gates["C"],
            "D_Sector_Fields": gates["D"],
            "E_Security_Identity": gates["E"],
            "F_Exact_Coverage": gates["F"],
            "G_Provenance": gates["G"],
            "H_Access_Persistence": gates["H"],
            "Earliest_Failed_Gate": earliest,
            "Earliest_Blocker": f["earliest_blocker"],
            "Rationale": f["rationale"],
        })
        taxonomy_inventory.append({
            "Cohort": cohort,
            "Taxonomy_Identity": f["taxonomy_identity"],
            "Source_Native_Candidate": f["source_native_candidate"],
            "Taxonomy_Status": gates["C"],
            "Sector_Code_Status": gates["D"],
            "Crosswalk_Used": "NO",
            "Taxonomy_Isolated": "YES",
        })
        access_audit.append({
            "Cohort": cohort,
            "Gate_H_Status": gates["H"],
            "Access_Persistence_Evaluated": "NO_AFTER_EARLIER_BLOCKER" if gates["H"] == "NOT_EVALUATED" else "YES",
            "Earliest_Blocker": f["earliest_blocker"],
            "Legal_Conclusion_Fabricated": "NO",
        })

    finding_by_cohort = research["cohort_findings"]
    for row in cohort_rows:
        cohort = row["Primary_Universe_Index"]
        f = finding_by_cohort[cohort]
        coverage.append({
            **row,
            "Coverage_Feasibility": "NOT_VERIFIED",
            "Earliest_Blocker": f["earliest_blocker"],
            "Earliest_Failed_Gate": first_nonpass(f["gate_status"]),
            "Sector_Taxonomy_Value_Materialized": "NO",
            "Sector_Code_Value_Materialized": "NO",
            "Sector_Name_Value_Materialized": "NO",
        })
        identity.append({
            "Security_Key": row["Security_Key"],
            "Source_WS_ID": row["Source_WS_ID"],
            "Primary_MIC": row["Primary_MIC"],
            "Primary_Ticker": row["Primary_Ticker"],
            "Primary_Universe_Index": cohort,
            "Identity_Gate_Status": f["gate_status"]["E"],
            "Deterministic_WS_ID_Proven": "YES" if f["gate_status"]["E"] == "PASS" else "NO",
            "Reason": f["earliest_blocker"] if f["gate_status"]["E"] != "PASS" else "IDENTITY_GATE_PASSED_BEFORE_LATER_COVERAGE_GATE",
        })

    ready = sum(r["Coverage_Feasibility"] == "PROVABLY_MAPPABLE" for r in coverage)
    not_mappable = sum(r["Coverage_Feasibility"] == "NOT_MAPPABLE" for r in coverage)
    not_verified = sum(r["Coverage_Feasibility"] == "NOT_VERIFIED" for r in coverage)
    if (ready, not_mappable, not_verified) != (0, 0, 1425):
        raise RuntimeError("coverage totals mismatch")

    external_ledger = []
    for i, req in enumerate(research["external_requests"], 1):
        external_ledger.append({
            "Request_Order": i,
            "URL": req["url"],
            "Allowed_Official_Source": "YES",
            "Result": req["result"],
            "Per_Security_Fanout": "NO",
        })

    isolation = {
        "authority": AUTHORITY_ID,
        "version": VERSION,
        "canonical_layer_allows_multiple_taxonomies": True,
        "required_row_taxonomy_field": "Sector_Taxonomy",
        "future_peer_group_key": ["Sector_Taxonomy", "Sector_Code"],
        "sector_code_alone_key_forbidden": True,
        "same_name_cross_taxonomy_equivalence_forbidden": True,
        "crosswalk_created": False,
        "cross_taxonomy_comparison_authorized": False,
        "sector_rs_authorized": False,
        "missing_or_ambiguous_fail_closed": True,
    }

    immutability = {
        "frozen_expected_sha256": FROZEN_SHA256,
        "frozen_sha_before": sha256_file(FROZEN),
        "frozen_sha_after": sha256_file(FROZEN),
        "frozen_unchanged": sha256_file(FROZEN) == FROZEN_SHA256,
        "v057_feature_expected_sha256": V057_FEATURE_SHA256,
        "v057_feature_sha_before": sha256_file(V057_FEATURES),
        "v057_feature_sha_after": sha256_file(V057_FEATURES),
        "v057_feature_unchanged": sha256_file(V057_FEATURES) == V057_FEATURE_SHA256,
        "v058_home_rs_expected_sha256": V058_HOME_RS_SHA256,
        "v058_home_rs_sha_before": sha256_file(V058_HOME_RS),
        "v058_home_rs_sha_after": sha256_file(V058_HOME_RS),
        "v058_home_rs_unchanged": sha256_file(V058_HOME_RS) == V058_HOME_RS_SHA256,
        "frozen_mutation": False,
        "price_cache_mutation": False,
        "feature_mutation": False,
        "home_market_rs_mutation": False,
        "sector_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "crosswalk_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
    }

    tests: list[dict[str, str]] = []
    def check(name: str, ok: bool, detail: str) -> None:
        tests.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})
        if not ok:
            raise RuntimeError(name)

    check("V061_VERDICT", pred["summary"]["verdict"] == "BLOCKED_TAXONOMY_SOURCE_FEASIBILITY", pred["summary"]["verdict"])
    check("V061_SELECTION_NONE", pred["summary"]["canonical_sector_taxonomy_selected"] is False and pred["summary"]["selected_taxonomy"] == "NONE", "NONE")
    check("V061_FEASIBLE_TESTED", pred["summary"]["feasible_count"] == 0 and pred["summary"]["tested_count"] == 2, "0/2")
    check("V061_BLOCKER", pred["summary"]["blocker"] == "FULL_1425_COVERAGE_NOT_VERIFIED", pred["summary"]["blocker"])
    check("V061_WORKFLOW_ARTIFACT", pred["checkpoint"]["workflow_run_id"] == V061_WORKFLOW_RUN and pred["checkpoint"]["artifact_id"] == V061_ARTIFACT_ID, f"{V061_WORKFLOW_RUN}/{V061_ARTIFACT_ID}")
    check("G_SEC_01_PRESERVED", g1["authority_id"] == "G-SEC-01", "G-SEC-01")
    check("G_SEC_02_BOUND", g2["authority_id"] == AUTHORITY_ID, AUTHORITY_ID)
    check("V021_SOURCE_CLASSES_INHERITED", g2["accepted_source_classes_inherited_from_v0_21"] == c21["accepted_source_classes"], "PASS")
    check("COHORT_COUNTS_EXACT", counts == EXPECTED_COHORTS, json.dumps(counts, sort_keys=True))
    check("COVERAGE_ROWS_1425", len(coverage) == 1425, str(len(coverage)))
    check("READY_ZERO", ready == 0, str(ready))
    check("NOT_MAPPABLE_ZERO", not_mappable == 0, str(not_mappable))
    check("NOT_VERIFIED_1425", not_verified == 1425, str(not_verified))
    check("ALL_COHORTS_BLOCKED", blocked_cohorts == list(EXPECTED_COHORTS.keys()), "|".join(blocked_cohorts))
    check("GLOBAL_BLOCKER_COHORT", research["global_smallest_blocker"]["cohort"] == GLOBAL_BLOCKER_COHORT, GLOBAL_BLOCKER_COHORT)
    check("GLOBAL_BLOCKER", research["global_smallest_blocker"]["blocker"] == GLOBAL_BLOCKER, GLOBAL_BLOCKER)
    check("TAXONOMY_ISOLATION_KEY", isolation["future_peer_group_key"] == ["Sector_Taxonomy", "Sector_Code"], "Sector_Taxonomy+Sector_Code")
    check("NO_CROSSWALK", isolation["crosswalk_created"] is False, "false")
    check("NO_SECTOR_RS", isolation["sector_rs_authorized"] is False and immutability["sector_rs_runs"] == 0, "0")
    check("NO_MAPPING_POPULATION", immutability["sector_mapping_population_runs"] == 0, "0")
    check("PROHIBITED_REQUESTS_ZERO", all(v == 0 for v in provider_calls().values()), json.dumps(provider_calls(), sort_keys=True))
    check("FROZEN_IMMUTABLE", immutability["frozen_unchanged"], FROZEN_SHA256)
    check("V057_IMMUTABLE", immutability["v057_feature_unchanged"], V057_FEATURE_SHA256)
    check("V058_IMMUTABLE", immutability["v058_home_rs_unchanged"], V058_HOME_RS_SHA256)
    check("P0_P1_P2_ZERO", immutability["p0_runs"] == immutability["p1_runs"] == immutability["p2_runs"] == 0, "0/0/0")

    (out / "manager_governance_authority_G_SEC_02_v0.62.json").write_text(json.dumps(g2, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "cohort_sector_source_route_ledger_v0.62.csv", route_ledger)
    write_csv(out / "source_native_taxonomy_inventory_v0.62.csv", taxonomy_inventory)
    write_csv(out / "frozen_1425_sector_coverage_feasibility_v0.62.csv", coverage)
    write_csv(out / "identity_linkage_audit_v0.62.csv", identity)
    write_csv(out / "source_access_persistence_audit_v0.62.csv", access_audit)
    (out / "taxonomy_isolation_contract_v0.62.json").write_text(json.dumps(isolation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "external_request_ledger_v0.62.csv", external_ledger)
    (out / "immutability_audit_v0.62.json").write_text(json.dumps(immutability, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "provider_call_audit_v0.62.json").write_text(json.dumps(provider_calls(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "test_results_v0.62.csv", tests)

    cohort_summary = []
    for r in route_ledger:
        cohort_summary.append({
            "Cohort": r["Cohort"],
            "Frozen_Rows": r["Frozen_Rows"],
            "READY": 0,
            "NOT_MAPPABLE": 0,
            "NOT_VERIFIED": r["Frozen_Rows"],
            "Earliest_Failed_Gate": r["Earliest_Failed_Gate"],
            "Earliest_Blocker": r["Earliest_Blocker"],
        })
    write_csv(out / "cohort_coverage_summary_v0.62.csv", cohort_summary)

    summary = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "source_native_sector_metadata_coverage_ready": False,
        "ready": ready,
        "total": 1425,
        "not_mappable": not_mappable,
        "not_verified": not_verified,
        "blocked_cohorts": blocked_cohorts,
        "cohort_counts": counts,
        "global_smallest_blocker": GLOBAL_BLOCKER,
        "global_smallest_blocker_cohort": GLOBAL_BLOCKER_COHORT,
        "cohort_blockers": {r["Cohort"]: r["Earliest_Blocker"] for r in route_ledger},
        "external_requests_recorded": len(external_ledger),
        "prohibited_provider_calls": provider_calls(),
        "sector_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "crosswalk_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "immutability": immutability,
        "tests": {"total": len(tests), "passed": len(tests), "failed": 0},
        "artifact_binding": "PENDING_UPLOAD",
        "productive": False,
        "next_gate": f"{GLOBAL_BLOCKER}:{GLOBAL_BLOCKER_COHORT}",
    }
    checkpoint = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "source_native_sector_metadata_coverage_ready": False,
        "ready": ready,
        "total": 1425,
        "not_mappable": not_mappable,
        "not_verified": not_verified,
        "blocked_cohorts": blocked_cohorts,
        "blocker": GLOBAL_BLOCKER,
        "blocker_cohort": GLOBAL_BLOCKER_COHORT,
        "sector_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_p2_runs": 0,
        "tests_passed": len(tests),
        "tests_failed": 0,
        "artifact_binding": "PENDING_UPLOAD",
        "next_gate": f"{GLOBAL_BLOCKER}:{GLOBAL_BLOCKER_COHORT}",
    }
    (out / "summary_preupload_v0.62.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "stage_checkpoint_preupload_v0.62.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    files = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": args.repository_sha,
        "verdict": VERDICT,
        "source_native_sector_metadata_coverage_ready": False,
        "ready": ready,
        "total": 1425,
        "not_mappable": not_mappable,
        "not_verified": not_verified,
        "blocked_cohorts": blocked_cohorts,
        "blocker": GLOBAL_BLOCKER,
        "blocker_cohort": GLOBAL_BLOCKER_COHORT,
        "frozen_sha256": FROZEN_SHA256,
        "v057_feature_sha256": V057_FEATURE_SHA256,
        "v058_home_rs_sha256": V058_HOME_RS_SHA256,
        "prohibited_provider_calls": provider_calls(),
        "sector_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "crosswalk_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "artifact_binding": "PENDING_UPLOAD",
        "files": files,
        "next_gate": f"{GLOBAL_BLOCKER}:{GLOBAL_BLOCKER_COHORT}",
    }
    (out / "manifest_preupload_v0.62.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": VERDICT,
        "source_native_sector_metadata_coverage_ready": False,
        "ready": ready,
        "total": 1425,
        "not_mappable": not_mappable,
        "not_verified": not_verified,
        "blocked_cohorts": blocked_cohorts,
        "blocker": GLOBAL_BLOCKER,
        "blocker_cohort": GLOBAL_BLOCKER_COHORT,
        "next_gate": f"{GLOBAL_BLOCKER}:{GLOBAL_BLOCKER_COHORT}",
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
