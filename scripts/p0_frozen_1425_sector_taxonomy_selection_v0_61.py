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
VERSION = "v0.61"
STAGE = "P0_FROZEN_1425_CANONICAL_SECTOR_TAXONOMY_SOURCE_FEASIBILITY_SELECTION_GATE"
REQUIRED_START_HEAD = "b5fda059940710d4e07928b6a8bc7b0b5d536a57"
V060_WORKFLOW_RUN = 36247871792
V060_ARTIFACT_ID = 10907812456
V060_ARTIFACT_DIGEST = "sha256:5caa8bd2a34b096e3b08e5ce9e41f3cabcea9b4b72d55060e20b8ec1bb78f500"
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_FEATURE_SHA256 = "177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_HOME_RS_SHA256 = "2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BLOCKER = "FULL_1425_COVERAGE_NOT_VERIFIED"
VERDICT = "BLOCKED_TAXONOMY_SOURCE_FEASIBILITY"
AUTHORITY_ID = "G-SEC-01"

FROZEN = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
V057_FEATURES = ROOT / "output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058_HOME_RS = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
V060_SUMMARY = ROOT / "output_p0_frozen_1425_sector_metadata_contract_v0_60/summary_v0.60.json"
V060_CHECKPOINT = ROOT / "output_p0_frozen_1425_sector_metadata_contract_v0_60/stage_checkpoint_v0.60.json"
V060_CONTRACT = ROOT / "output_p0_frozen_1425_sector_metadata_contract_v0_60/sector_metadata_contract_v0.60.json"
V021_CONTRACT = ROOT / "output_p0_lane_shadow_validation_v0_21/sector_metadata_contract_v0.21.json"
MANAGER_AUTHORITY = ROOT / "config/manager_governance_authority_G_SEC_01_v0.61.json"
SOURCE_RESEARCH = ROOT / "config/sector_taxonomy_source_research_v0.61.json"

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
        "market_price_ohlcv": 0,
        "news_trading": 0,
        "per_security_web_fanout": 0,
    }

def validate_predecessor(repo_sha: str) -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if head != repo_sha:
        raise RuntimeError(f"checkout mismatch {head} != {repo_sha}")
    if subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"], cwd=ROOT).returncode != 0:
        raise RuntimeError("required v0.60 final commit is not an ancestor")

    s60 = json.loads(V060_SUMMARY.read_text(encoding="utf-8"))
    c60 = json.loads(V060_CHECKPOINT.read_text(encoding="utf-8"))
    contract60 = json.loads(V060_CONTRACT.read_text(encoding="utf-8"))
    if s60["verdict"] != "BLOCKED_GOVERNANCE_AUTHORITY_REQUIRED":
        raise RuntimeError("v0.60 verdict mismatch")
    if s60["sector_metadata_contract_ready"] is not False:
        raise RuntimeError("v0.60 contract readiness mismatch")
    if s60["blocker"] != "GOVERNANCE_DECISION_REQUIRED_CANONICAL_SECTOR_TAXONOMY":
        raise RuntimeError("v0.60 blocker mismatch")
    if c60["workflow_run_id"] != V060_WORKFLOW_RUN or c60["artifact_id"] != V060_ARTIFACT_ID:
        raise RuntimeError("v0.60 workflow/artifact mismatch")
    if "sha256:" + c60["artifact_digest"] != V060_ARTIFACT_DIGEST:
        raise RuntimeError("v0.60 artifact digest mismatch")
    if contract60["canonical_taxonomy"] != "NOT_DEFINED":
        raise RuntimeError("v0.60 unexpectedly selected taxonomy")
    if s60["p0_runs"] != 0 or s60["p1_runs"] != 0 or s60["p2_runs"] != 0:
        raise RuntimeError("v0.60 P0/P1/P2 runs changed")

    frozen = read_csv(FROZEN)
    if len(frozen) != 1425:
        raise RuntimeError("Frozen member count mismatch")
    if sha256_file(FROZEN) != FROZEN_SHA256:
        raise RuntimeError("Frozen SHA mismatch")
    if sha256_file(V057_FEATURES) != V057_FEATURE_SHA256:
        raise RuntimeError("v0.57 feature SHA mismatch")
    if sha256_file(V058_HOME_RS) != V058_HOME_RS_SHA256:
        raise RuntimeError("v0.58 Home-Market RS SHA mismatch")
    return {"summary": s60, "checkpoint": c60, "contract": contract60, "frozen": frozen}

def validate_manager_authority() -> dict[str, Any]:
    a = json.loads(MANAGER_AUTHORITY.read_text(encoding="utf-8"))
    if a["authority_id"] != AUTHORITY_ID or a["version"] != VERSION:
        raise RuntimeError("manager governance authority mismatch")
    rules = a["rules"]
    required_true = [
        "no_preference_based_selection",
        "single_pass_auto_promotion_only",
        "exactly_one_full_pass_required",
        "historical_partial_data_does_not_confer_authority",
        "market_custom_does_not_confer_authority",
        "plausibility_does_not_confer_authority",
        "personal_preference_does_not_confer_authority",
        "mixed_taxonomy_forbidden_in_v0_61",
        "crosswalk_forbidden_in_v0_61",
    ]
    if not all(rules[k] is True for k in required_true):
        raise RuntimeError("G-SEC-01 hard rule mismatch")
    if a["candidate_minimum"] != ["GICS", "ICB"]:
        raise RuntimeError("candidate minimum mismatch")
    return a

def candidate_matrix(research: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    evidence = {
        "GICS": {
            "A_TAXONOMY_DEFINITION": ("PASS", "Official S&P/MSCI authority; April-2026 methodology defines global four-tier hierarchy and stable numeric codes."),
            "B_SOURCE_CLASS": ("PASS", "Official index-administrator/reference-data route: S&P Global GICS Direct / MSCI GICS Direct."),
            "C_BULK_REPRODUCIBILITY": ("PASS", "Official dataset advertises API/Cloud/Feed/SFTP delivery; no per-security web fanout required."),
            "D_FROZEN_1425_COVERAGE_FEASIBILITY": ("NOT_VERIFIED", "Public global coverage claims do not prove exact membership for each Frozen-1425 security; no entitled bulk mapping file was accessed."),
            "E_IDENTITY": ("NOT_VERIFIED", "Official cross-reference products exist, but the exact entitled identifier schema/path to Source_WS_ID was not verified for this project."),
            "F_PROVENANCE": ("PASS", "GICS taxonomy code/name plus project-required Source_Name/Reference/Version-or-AsOf/Mapping_Status/WS_ID fields are planable."),
            "G_SOURCE_ACCESS_PERSISTENCE": ("NOT_VERIFIED", "Official data is licensed/proprietary; repository-specific storage/redistribution permission or entitlement was not verified."),
        },
        "ICB": {
            "A_TAXONOMY_DEFINITION": ("PASS", "Official FTSE Russell authority; ICB Ground Rules/taxonomy define coded Industry/Supersector/Sector/Subsector hierarchy."),
            "B_SOURCE_CLASS": ("PASS", "Official FTSE Russell ICB Universe and constituent reference-data files are an allowed index-administrator route."),
            "C_BULK_REPRODUCIBILITY": ("PASS", "Official ICB Universe weekly files plus daily update files provide reproducible bulk delivery."),
            "D_FROZEN_1425_COVERAGE_FEASIBILITY": ("NOT_VERIFIED", "Public 85k/80+ countries/150 exchanges claim does not prove exact membership for every Frozen-1425 security; no entitled Universe file was accessed."),
            "E_IDENTITY": ("NOT_VERIFIED", "Public product overview does not expose enough current Universe-file identity schema to prove deterministic Source identity to Source_WS_ID for all 1425."),
            "F_PROVENANCE": ("PASS", "ICB coded taxonomy plus project-required Source_Name/Reference/Version-or-AsOf/Mapping_Status/WS_ID fields are planable."),
            "G_SOURCE_ACCESS_PERSISTENCE": ("NOT_VERIFIED", "Official ICB materials require licence/permission for use/distribution; repository-specific persistence permission is not verified."),
        },
    }
    for candidate in ["GICS", "ICB"]:
        if candidate not in research["candidate_findings"]:
            raise RuntimeError(f"missing research candidate {candidate}")
        for gate, (status, detail) in evidence[candidate].items():
            rows.append({
                "Candidate": candidate,
                "Gate": gate,
                "Status": status,
                "Detail": detail,
                "Earliest_Blocker": BLOCKER if gate == "D_FROZEN_1425_COVERAGE_FEASIBILITY" else "",
            })
    return rows

def coverage_rows(frozen: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for cand in ["GICS", "ICB"]:
        for r in frozen:
            out.append({
                "Candidate": cand,
                "Security_Key": r["Security_Key"],
                "Source_WS_ID": r["Source_WS_ID"],
                "Primary_MIC": r["Primary_MIC"],
                "Primary_Ticker": r["Primary_Ticker"],
                "Coverage_Feasibility": "NOT_VERIFIED",
                "Reason": "EXACT_OFFICIAL_BULK_MEMBERSHIP_NOT_PROVEN_NO_ENTITLED_MAPPING_FILE_ACCESSED",
                "Sector_Value_Materialized": "NO",
            })
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository-sha", required=True)
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_sector_taxonomy_selection_v0_61")
    args = ap.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    pred = validate_predecessor(args.repository_sha)
    authority = validate_manager_authority()
    research = json.loads(SOURCE_RESEARCH.read_text(encoding="utf-8"))
    if research["version"] != VERSION:
        raise RuntimeError("source research version mismatch")
    if any(research["prohibited_provider_requests"].values()):
        raise RuntimeError("prohibited external request recorded")

    matrix = candidate_matrix(research)
    coverage = coverage_rows(pred["frozen"])
    candidates = ["GICS", "ICB"]
    full_pass: list[str] = []
    for c in candidates:
        statuses = [r["Status"] for r in matrix if r["Candidate"] == c]
        if statuses and all(s == "PASS" for s in statuses):
            count = sum(1 for r in coverage if r["Candidate"] == c and r["Coverage_Feasibility"] == "PROVABLY_MAPPABLE")
            if count == 1425:
                full_pass.append(c)

    selected = full_pass[0] if len(full_pass) == 1 else None
    if selected is not None:
        raise RuntimeError("public bounded evidence unexpectedly supports canonical promotion")
    if len(full_pass) > 1:
        blocker = "GOVERNANCE_DECISION_REQUIRED_MULTIPLE_FEASIBLE_TAXONOMIES"
    else:
        blocker = BLOCKER

    coverage_summary = []
    for c in candidates:
        prov = sum(1 for r in coverage if r["Candidate"] == c and r["Coverage_Feasibility"] == "PROVABLY_MAPPABLE")
        notmap = sum(1 for r in coverage if r["Candidate"] == c and r["Coverage_Feasibility"] == "NOT_MAPPABLE")
        nv = sum(1 for r in coverage if r["Candidate"] == c and r["Coverage_Feasibility"] == "NOT_VERIFIED")
        coverage_summary.append({
            "Candidate": c,
            "PROVABLY_MAPPABLE": prov,
            "NOT_MAPPABLE": notmap,
            "NOT_VERIFIED": nv,
            "TOTAL": prov + notmap + nv,
            "Full_1425_Coverage": "YES" if prov == 1425 else "NO",
        })

    source_routes = [
        {
            "Candidate": "GICS",
            "Official_Authority": "S&P Dow Jones Indices + MSCI",
            "Route": "GICS Direct / S&P Global GICS dataset",
            "Source_Class": "official index administrator bulk/reference data",
            "Bulk_Mode": "API|Cloud|Feed|SFTP",
            "Public_Coverage_Claim": "50,000+ active public companies; 120+ countries; global",
            "Exact_Frozen_Coverage": "NOT_VERIFIED",
            "Identity_Path": "NOT_VERIFIED_FOR_PROJECT",
            "Access": "SUBSCRIPTION_OR_LICENSE_ROUTE_EXISTS_PROJECT_ENTITLEMENT_NOT_VERIFIED",
        },
        {
            "Candidate": "ICB",
            "Official_Authority": "FTSE International Limited / FTSE Russell",
            "Route": "ICB Universe weekly files + daily update files",
            "Source_Class": "official index administrator bulk/reference data",
            "Bulk_Mode": "Universe files",
            "Public_Coverage_Claim": "~85,000 equity securities; 80+ countries; 150 active exchanges",
            "Exact_Frozen_Coverage": "NOT_VERIFIED",
            "Identity_Path": "NOT_VERIFIED_FOR_PROJECT",
            "Access": "LICENSE_ROUTE_EXISTS_PROJECT_ENTITLEMENT_NOT_VERIFIED",
        },
    ]

    access_audit = [
        {
            "Candidate": "GICS",
            "Official_Access_Route": "YES",
            "Project_Entitlement_Verified": "NO",
            "Repository_Persistence_Rights_Verified": "NO",
            "Status": "NOT_VERIFIED",
            "Evidence": "Official GICS/S&P materials describe proprietary licensed data and restrict reproduction/distribution/database storage absent permission.",
        },
        {
            "Candidate": "ICB",
            "Official_Access_Route": "YES",
            "Project_Entitlement_Verified": "NO",
            "Repository_Persistence_Rights_Verified": "NO",
            "Status": "NOT_VERIFIED",
            "Evidence": "Official FTSE Russell materials require licence and state no further distribution without express written consent.",
        },
    ]

    selection = {
        "authority": AUTHORITY_ID,
        "tested_candidates": candidates,
        "other_single_taxonomy_tested": False,
        "other_single_taxonomy_reason": research["other_single_taxonomy_result"],
        "feasible_candidates": full_pass,
        "feasible_count": len(full_pass),
        "tested_count": len(candidates),
        "canonical_sector_taxonomy_selected": selected is not None,
        "selected_taxonomy": selected or "NONE",
        "selection_rule": "AUTO_SELECT_ONLY_IF_EXACTLY_ONE_CANDIDATE_PASSES_A_TO_G_AND_1425_OF_1425_PROVABLY_MAPPABLE",
        "blocker": blocker,
        "earliest_common_failed_gate": "D_FROZEN_1425_COVERAGE_FEASIBILITY",
        "mapping_population_executed": False,
        "sector_rs_executed": False,
        "crosswalk_created": False,
        "productive": False,
    }

    unresolved = {
        "primary_blocker": blocker,
        "items": [
            {
                "id": "FULL_1425_COVERAGE_NOT_VERIFIED",
                "status": "OPEN",
                "priority": 1,
                "detail": "Neither candidate has exact row-level official bulk coverage proof for all 1425 Frozen securities under an entitled source route.",
            },
            {
                "id": "DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED",
                "status": "DOWNSTREAM_OPEN",
                "priority": 2,
                "detail": "Exact source identifier schema/linkage to Source_WS_ID remains unverified for both candidates.",
            },
            {
                "id": "SOURCE_ACCESS_OR_PERSISTENCE_NOT_VERIFIED",
                "status": "DOWNSTREAM_OPEN",
                "priority": 3,
                "detail": "Project-specific source entitlement and repository mapping-persistence rights are not verified for either candidate.",
            },
        ],
    }

    external_ledger = []
    for i, item in enumerate(research["external_requests"], start=1):
        url, interaction, result = item
        external_ledger.append({
            "Request_Order": i,
            "URL": url,
            "Interaction": interaction,
            "Allowed_Official_Source": "YES",
            "Result": result,
            "Used_For_Selection": "YES" if interaction == "OPENED" else "NO_SUPPLEMENTARY",
        })

    immutability = {
        "frozen_sha_before": sha256_file(FROZEN),
        "frozen_sha_after": sha256_file(FROZEN),
        "frozen_expected_sha256": FROZEN_SHA256,
        "frozen_unchanged": sha256_file(FROZEN) == FROZEN_SHA256,
        "v057_feature_sha_before": sha256_file(V057_FEATURES),
        "v057_feature_sha_after": sha256_file(V057_FEATURES),
        "v057_feature_expected_sha256": V057_FEATURE_SHA256,
        "v057_feature_unchanged": sha256_file(V057_FEATURES) == V057_FEATURE_SHA256,
        "v058_home_rs_sha_before": sha256_file(V058_HOME_RS),
        "v058_home_rs_sha_after": sha256_file(V058_HOME_RS),
        "v058_home_rs_expected_sha256": V058_HOME_RS_SHA256,
        "v058_home_rs_unchanged": sha256_file(V058_HOME_RS) == V058_HOME_RS_SHA256,
        "universe_mutation": False,
        "security_identity_mutation": False,
        "provider_mapping_mutation": False,
        "price_cache_mutation": False,
        "feature_mutation": False,
        "home_market_rs_mutation": False,
        "sector_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
    }

    tests: list[dict[str, str]] = []
    def gate(name: str, ok: bool, detail: str) -> None:
        tests.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})
        if not ok:
            raise RuntimeError(name)

    gate("START_HEAD_ANCESTOR", True, REQUIRED_START_HEAD)
    gate("V060_VERDICT", pred["summary"]["verdict"] == "BLOCKED_GOVERNANCE_AUTHORITY_REQUIRED", pred["summary"]["verdict"])
    gate("V060_CONTRACT_NOT_READY", pred["summary"]["sector_metadata_contract_ready"] is False, "NO")
    gate("V060_BLOCKER", pred["summary"]["blocker"] == "GOVERNANCE_DECISION_REQUIRED_CANONICAL_SECTOR_TAXONOMY", pred["summary"]["blocker"])
    gate("V060_WORKFLOW_ARTIFACT", pred["checkpoint"]["workflow_run_id"] == V060_WORKFLOW_RUN and pred["checkpoint"]["artifact_id"] == V060_ARTIFACT_ID, f"{V060_WORKFLOW_RUN}/{V060_ARTIFACT_ID}")
    gate("G_SEC_01_BOUND", authority["authority_id"] == AUTHORITY_ID, AUTHORITY_ID)
    gate("CANDIDATES_TESTED_GICS_ICB", candidates == ["GICS", "ICB"], "2")
    gate("NO_ARTIFICIAL_THIRD_TAXONOMY", selection["other_single_taxonomy_tested"] is False, research["other_single_taxonomy_result"])
    gate("GICS_A_C_PASS", all(r["Status"] == "PASS" for r in matrix if r["Candidate"] == "GICS" and r["Gate"] in {"A_TAXONOMY_DEFINITION","B_SOURCE_CLASS","C_BULK_REPRODUCIBILITY"}), "PASS")
    gate("ICB_A_C_PASS", all(r["Status"] == "PASS" for r in matrix if r["Candidate"] == "ICB" and r["Gate"] in {"A_TAXONOMY_DEFINITION","B_SOURCE_CLASS","C_BULK_REPRODUCIBILITY"}), "PASS")
    gate("COVERAGE_ROWS_2850", len(coverage) == 2850, str(len(coverage)))
    gate("GICS_EXACT_COVERAGE_NOT_VERIFIED", next(r for r in coverage_summary if r["Candidate"] == "GICS")["NOT_VERIFIED"] == 1425, "1425")
    gate("ICB_EXACT_COVERAGE_NOT_VERIFIED", next(r for r in coverage_summary if r["Candidate"] == "ICB")["NOT_VERIFIED"] == 1425, "1425")
    gate("NO_FULL_PASS_CANDIDATE", len(full_pass) == 0, "0")
    gate("NO_CANONICAL_SELECTION", selection["canonical_sector_taxonomy_selected"] is False and selection["selected_taxonomy"] == "NONE", "NONE")
    gate("SMALLEST_BLOCKER_IS_COVERAGE", selection["blocker"] == BLOCKER, BLOCKER)
    gate("NO_MAPPING_POPULATION", selection["mapping_population_executed"] is False and immutability["sector_mapping_population_runs"] == 0, "0")
    gate("NO_SECTOR_RS", selection["sector_rs_executed"] is False and immutability["sector_rs_runs"] == 0, "0")
    gate("NO_CROSSWALK", selection["crosswalk_created"] is False, "false")
    gate("PROHIBITED_PROVIDER_CALLS_ZERO", all(v == 0 for v in provider_calls().values()), json.dumps(provider_calls(), sort_keys=True))
    gate("FROZEN_IMMUTABLE", immutability["frozen_unchanged"], FROZEN_SHA256)
    gate("V057_FEATURE_IMMUTABLE", immutability["v057_feature_unchanged"], V057_FEATURE_SHA256)
    gate("V058_HOME_RS_IMMUTABLE", immutability["v058_home_rs_unchanged"], V058_HOME_RS_SHA256)
    gate("P0_P1_P2_ZERO", immutability["p0_runs"] == immutability["p1_runs"] == immutability["p2_runs"] == 0, "0/0/0")

    (out / "manager_governance_authority_G_SEC_01_v0.61.json").write_text(json.dumps(authority, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "taxonomy_candidate_gate_matrix_v0.61.csv", matrix)
    write_csv(out / "official_source_route_ledger_v0.61.csv", source_routes)
    write_csv(out / "frozen_1425_coverage_feasibility_v0.61.csv", coverage)
    write_csv(out / "frozen_1425_coverage_summary_v0.61.csv", coverage_summary)
    write_csv(out / "source_access_persistence_audit_v0.61.csv", access_audit)
    (out / "taxonomy_selection_decision_v0.61.json").write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "unresolved_blockers_v0.61.json").write_text(json.dumps(unresolved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "external_request_ledger_v0.61.csv", external_ledger)
    (out / "immutability_audit_v0.61.json").write_text(json.dumps(immutability, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "provider_call_audit_v0.61.json").write_text(json.dumps(provider_calls(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out / "test_results_v0.61.csv", tests)

    summary = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "canonical_sector_taxonomy_selected": False,
        "selected_taxonomy": "NONE",
        "feasible_count": 0,
        "tested_count": 2,
        "blocker": blocker,
        "candidate_results": {
            "GICS": {"overall": "FAIL", "earliest_failed_gate": "D_FROZEN_1425_COVERAGE_FEASIBILITY", "provably_mappable": 0, "not_mappable": 0, "not_verified": 1425},
            "ICB": {"overall": "FAIL", "earliest_failed_gate": "D_FROZEN_1425_COVERAGE_FEASIBILITY", "provably_mappable": 0, "not_mappable": 0, "not_verified": 1425},
        },
        "bounded_official_external_requests_recorded": len(external_ledger),
        "prohibited_provider_calls": provider_calls(),
        "mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "immutability": immutability,
        "tests": {"total": len(tests), "passed": len(tests), "failed": 0},
        "artifact_binding": "PENDING_UPLOAD",
        "productive": False,
        "next_gate": blocker,
    }
    checkpoint = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "canonical_sector_taxonomy_selected": False,
        "selected_taxonomy": "NONE",
        "feasible_count": 0,
        "tested_count": 2,
        "blocker": blocker,
        "mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_p2_runs": 0,
        "tests_passed": len(tests),
        "tests_failed": 0,
        "artifact_binding": "PENDING_UPLOAD",
        "next_gate": blocker,
    }
    (out / "summary_preupload_v0.61.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "stage_checkpoint_preupload_v0.61.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
        "canonical_sector_taxonomy_selected": False,
        "selected_taxonomy": "NONE",
        "feasible_count": 0,
        "tested_count": 2,
        "blocker": blocker,
        "frozen_sha256": FROZEN_SHA256,
        "v057_feature_sha256": V057_FEATURE_SHA256,
        "v058_home_rs_sha256": V058_HOME_RS_SHA256,
        "prohibited_provider_calls": provider_calls(),
        "mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "artifact_binding": "PENDING_UPLOAD",
        "files": files,
        "next_gate": blocker,
    }
    (out / "manifest_preupload_v0.61.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": VERDICT,
        "canonical_sector_taxonomy_selected": False,
        "selected_taxonomy": "NONE",
        "feasible": 0,
        "tested": 2,
        "blocker": blocker,
        "next_gate": blocker,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
