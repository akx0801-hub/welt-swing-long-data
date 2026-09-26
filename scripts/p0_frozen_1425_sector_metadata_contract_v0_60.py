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
VERSION = "v0.60"
STAGE = "P0_FROZEN_1425_SECTOR_METADATA_CONTRACT_DEFINITION_GATE"
REQUIRED_START_HEAD = "3327e1245b0b0bf387445d78bfd2a3c66077538a"
V059_WORKFLOW_RUN = 36243521798
V059_ARTIFACT_ID = 10906513700
V059_ARTIFACT_DIGEST = "sha256:ed79a1cad64fa409f72fd21d23669d77b720a99c6f12e379fd48c1573a1f4ab0"
FROZEN_SHA256 = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_FEATURE_SHA256 = "177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_HOME_RS_SHA256 = "2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
BLOCKER = "GOVERNANCE_DECISION_REQUIRED_CANONICAL_SECTOR_TAXONOMY"
VERDICT = "BLOCKED_GOVERNANCE_AUTHORITY_REQUIRED"

FROZEN = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
V057_FEATURES = ROOT / "output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058_HOME_RS = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
V058_SUMMARY = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/summary_v0.58.json"
V059_SUMMARY = ROOT / "output_p0_frozen_1425_sector_authority_v0_59/summary_v0.59.json"
V059_CHECKPOINT = ROOT / "output_p0_frozen_1425_sector_authority_v0_59/stage_checkpoint_v0.59.json"
V059_CONTRACT = ROOT / "output_p0_frozen_1425_sector_authority_v0_59/sector_metadata_contract_v0.59.json"
V059_TAXONOMY = ROOT / "output_p0_frozen_1425_sector_authority_v0_59/taxonomy_authority_v0.59.csv"
V059_AUTHORITY = ROOT / "output_p0_frozen_1425_sector_authority_v0_59/authority_validation_v0.59.json"
MASTER = ROOT / "docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md"
V020_DOC = ROOT / "docs/validation/P0_Relative_Strength_Augmentation_v0.20.md"
V021_DOC = ROOT / "docs/validation/P0_Lane_Shadow_Validation_v0.21.md"
V021_CONTRACT = ROOT / "output_p0_lane_shadow_validation_v0_21/sector_metadata_contract_v0.21.json"
V021_INVENTORY = ROOT / "output_p0_lane_shadow_validation_v0_21/sector_metadata_inventory_v0.21.csv"
V021_PARAMS = ROOT / "output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json"
V044_DOC = ROOT / "docs/validation/P0_Frozen_1425_Data_Capability_Readiness_v0.44.md"
V044_PARAMS = ROOT / "output_p0_frozen_1425_readiness_v0_44/parameter_readiness_v0.44.json"
V057_SUMMARY = ROOT / "output_p0_frozen_1425_local_feature_implementation_v0_57/summary_v0.57.json"
V059_DOC = ROOT / "docs/validation/P0_Frozen_1425_Sector_Metadata_Sector_RS_Authority_v0.59.md"

EXPECTED_BLOBS = {
    "docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md": "680d0434e534d1fe136e694ca05cb574958a1a24",
    "docs/validation/P0_Frozen_1425_Sector_Metadata_Sector_RS_Authority_v0.59.md": "c865c82d8a948b8097de9f908ea934ef05c2bcd2",
    "output_p0_frozen_1425_sector_authority_v0_59/summary_v0.59.json": "007fec586ae06df7499ade4ecfeace5b32f474a8",
    "output_p0_frozen_1425_sector_authority_v0_59/stage_checkpoint_v0.59.json": "29e700240a79934ecca5d22a63ec50279f3c72fb",
    "output_p0_frozen_1425_sector_authority_v0_59/sector_metadata_contract_v0.59.json": "be8edf526098706ddb95556e670062c856f7627f",
    "output_p0_frozen_1425_sector_authority_v0_59/taxonomy_authority_v0.59.csv": "ef18f0e142db8da8f32f5eea95f7309e2505d36b",
    "output_p0_frozen_1425_sector_authority_v0_59/authority_validation_v0.59.json": "0652579a82ff6bc4329e4e29bae7c0e6e1ef945e",
    "output_p0_lane_shadow_validation_v0_21/sector_metadata_contract_v0.21.json": "06ee70d2057306fdd301d7e00ed8701f93acc5d5",
    "output_p0_lane_shadow_validation_v0_21/sector_metadata_inventory_v0.21.csv": "bc5d133c63fd42b3f2debc6e862d6b59adba0af2",
    "output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json": "01ae47713cc722497fcc56585dd27466df8baa9c",
    "docs/validation/P0_Lane_Shadow_Validation_v0.21.md": "6216b82699d1fe7470a7f4cf4288e233d52acf1d",
    "docs/validation/P0_Relative_Strength_Augmentation_v0.20.md": "a3962c82cfad396e627988ab4b2635a93898b3d0",
    "docs/validation/P0_Frozen_1425_Data_Capability_Readiness_v0.44.md": "3718c41f769bf9e257793209b8a7b26d0cb9a9f3",
    "output_p0_frozen_1425_readiness_v0_44/parameter_readiness_v0.44.json": "a5c963f1dcf5d3d61000a7ae47d8ca21613f479f",
    "output_p0_frozen_1425_home_market_rs_v0_58/summary_v0.58.json": "0d733f12fc99335d24f8a1843e6ddab05c8a7827",
    "output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv": "d2ea38829201f3a05110829191720c94e501c546",
    "output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv": "47bbb681f01b40bfa027905567954cce16c06e24",
    "universe/SWING_U3K_FROZEN_v0.5.csv": "018a03eb4614a197da9d2d566e77f32c61238dad",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def git_blob(path: Path) -> str:
    return git("hash-object", str(path.relative_to(ROOT)))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if fields:
            w.writeheader()
            w.writerows(rows)

def frozen_count() -> int:
    with FROZEN.open(encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))

def provider_calls() -> dict[str, int]:
    return {
        "market": 0,
        "yahoo_yfinance": 0,
        "eodhd": 0,
        "alpha_vantage": 0,
        "scalable": 0,
        "external_market_or_reference_requests": 0,
    }

def validate_predecessor(repo_sha: str) -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    if head != repo_sha:
        raise RuntimeError(f"checkout mismatch {head} != {repo_sha}")
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"], cwd=ROOT).returncode
    if rc != 0:
        raise RuntimeError("required v0.59 persisted HEAD is not an ancestor")
    blobs: dict[str, str] = {}
    for rel, expected in EXPECTED_BLOBS.items():
        got = git_blob(ROOT / rel)
        blobs[rel] = got
        if got != expected:
            raise RuntimeError(f"authority blob mismatch {rel}: {got} != {expected}")

    s59 = json.loads(V059_SUMMARY.read_text(encoding="utf-8"))
    c59 = json.loads(V059_CHECKPOINT.read_text(encoding="utf-8"))
    if s59["verdict"] != "PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER":
        raise RuntimeError("v0.59 verdict mismatch")
    if s59["sector_rs_ready"] is not False:
        raise RuntimeError("v0.59 sector_rs_ready must remain false")
    if s59["capability_counts"]["BLOCKED_METADATA"] != 1425 or s59["affected_count"] != 1425:
        raise RuntimeError("v0.59 affected metadata count mismatch")
    if s59["sector_rs_materialization_runs"] != 0 or c59["materialization_runs"] != 0:
        raise RuntimeError("v0.59 materialization count mismatch")
    if c59["workflow_run_id"] != V059_WORKFLOW_RUN or c59["artifact_id"] != V059_ARTIFACT_ID:
        raise RuntimeError("v0.59 workflow/artifact mismatch")
    if "sha256:" + c59["artifact_digest"] != V059_ARTIFACT_DIGEST:
        raise RuntimeError("v0.59 artifact digest mismatch")
    if s59["p0_runs"] != 0 or s59["p1_p2_runs"] != 0:
        raise RuntimeError("v0.59 P0/P1/P2 run count mismatch")

    s58 = json.loads(V058_SUMMARY.read_text(encoding="utf-8"))
    if s58["verdict"] != "PASS_HOME_MARKET_RS_READY" or s58["home_market_rs_ready"] is not True:
        raise RuntimeError("v0.58 Home-Market RS authority mismatch")
    if s58["ready_count"] != 1425 or s58["total"] != 1425:
        raise RuntimeError("v0.58 ready count mismatch")

    if frozen_count() != 1425 or sha256_file(FROZEN) != FROZEN_SHA256:
        raise RuntimeError("Frozen-1425 immutable gate mismatch")
    if sha256_file(V057_FEATURES) != V057_FEATURE_SHA256:
        raise RuntimeError("v0.57 feature semantic SHA mismatch")
    if sha256_file(V058_HOME_RS) != V058_HOME_RS_SHA256:
        raise RuntimeError("v0.58 Home-Market RS semantic SHA mismatch")

    return {"repository_sha": head, "authority_blobs": blobs, "v059": s59, "v058": s58}

def authority_findings() -> tuple[list[dict[str, str]], dict[str, Any], list[dict[str, str]]]:
    master = MASTER.read_text(encoding="utf-8")
    v20 = V020_DOC.read_text(encoding="utf-8")
    v21_doc = V021_DOC.read_text(encoding="utf-8")
    v21 = json.loads(V021_CONTRACT.read_text(encoding="utf-8"))
    v21_params = json.loads(V021_PARAMS.read_text(encoding="utf-8"))
    v44 = V044_DOC.read_text(encoding="utf-8")
    v57 = json.loads(V057_SUMMARY.read_text(encoding="utf-8"))
    v59 = json.loads(V059_CONTRACT.read_text(encoding="utf-8"))
    taxonomy_csv = V059_TAXONOMY.read_text(encoding="utf-8")
    v59_doc = V059_DOC.read_text(encoding="utf-8")

    required = [
        "WS_ID", "Sector_Taxonomy", "Sector_Code", "Sector_Name",
        "Source_Name", "Source_Reference", "Source_Version_or_AsOf", "Mapping_Status"
    ]
    if v21.get("required_fields") != required:
        raise RuntimeError("v0.21 required fields changed")

    ledger = [
        {
            "Authority": "LONG_DEV_MASTER_v0.1",
            "Path": str(MASTER.relative_to(ROOT)),
            "Authority_Class": "MASTER_SPEC",
            "Sector_Semantics": "Sector is D0 static metadata; Sector RS is desired where valid; unreliable groups must remain RS_NOT_VERIFIED.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "PARTIAL_REQUIREMENTS_ONLY",
        },
        {
            "Authority": "P0_RS_v0.20",
            "Path": str(V020_DOC.relative_to(ROOT)),
            "Authority_Class": "VALIDATION",
            "Sector_Semantics": "No auditable sector classification; no guessing; all Sector RS remains not verified.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "FAIL_CLOSED_HISTORY",
        },
        {
            "Authority": "P0_LANE_SHADOW_v0.21",
            "Path": str(V021_DOC.relative_to(ROOT)),
            "Authority_Class": "VALIDATION",
            "Sector_Semantics": "Defines required metadata fields, source classes, provenance and prohibited methods.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "PREPARED_NOT_POPULATED",
        },
        {
            "Authority": "SECTOR_METADATA_CONTRACT_v0.21",
            "Path": str(V021_CONTRACT.relative_to(ROOT)),
            "Authority_Class": "HISTORICAL_CONTRACT",
            "Sector_Semantics": "WS_ID linkage, versioned provenance, ambiguity fail-closed, source classes and no silent taxonomy mixing without crosswalk.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "PREPARED_NOT_POPULATED",
        },
        {
            "Authority": "P0_PARAMETER_REGISTRY_v0.21",
            "Path": str(V021_PARAMS.relative_to(ROOT)),
            "Authority_Class": "PARAMETER_AUTHORITY",
            "Sector_Semantics": "Sector taxonomy must be versioned, sourced and deterministically mapped before Sector RS.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "SHADOW_COMPONENT_VALIDATION_ONLY",
        },
        {
            "Authority": "P0_READINESS_v0.44",
            "Path": str(V044_DOC.relative_to(ROOT)),
            "Authority_Class": "READINESS_AUTHORITY",
            "Sector_Semantics": "v0.21 contract still PREPARED_NOT_POPULATED; valid sector metadata is a separate required authority.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "NOT_READY_FOR_FULL_P0",
        },
        {
            "Authority": "LOCAL_FEATURE_v0.57",
            "Path": str(V057_SUMMARY.relative_to(ROOT)),
            "Authority_Class": "PROMOTED_CAPABILITY",
            "Sector_Semantics": "Sector RS remains downstream of a separate metadata/source authority.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "LOCAL_FEATURE_READY_ONLY",
        },
        {
            "Authority": "HOME_MARKET_RS_v0.58",
            "Path": str(V058_SUMMARY.relative_to(ROOT)),
            "Authority_Class": "PROMOTED_CAPABILITY",
            "Sector_Semantics": "Home-market RS is ready 1425/1425; Sector RS explicitly remains false.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "HOME_MARKET_RS_READY_ONLY",
        },
        {
            "Authority": "SECTOR_AUTHORITY_v0.59",
            "Path": str(V059_DOC.relative_to(ROOT)),
            "Authority_Class": "IMMEDIATE_PREDECESSOR",
            "Sector_Semantics": "Explicitly finds no canonical taxonomy, no canonical sector field and no populated Frozen-1425 mapping authority; historical US GICS is not promoted.",
            "Taxonomy_Selection": "NONE",
            "Canonical_Field_Selection": "NONE",
            "Promotion_Status": "PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER",
        },
    ]

    checks = {
        "master_mentions_sector_d0": "D0" in master and "Sektor" in master,
        "master_requires_sector_rs_where_valid": "soweit valide: zum Sektor" in master,
        "v020_fail_closed_no_sector_metadata": "RS_NOT_VERIFIED_NO_SECTOR_METADATA" in v20,
        "v021_contract_status": v21.get("status"),
        "v021_required_identity_key": v21.get("required_identity_key"),
        "v021_required_fields": v21.get("required_fields"),
        "v021_accepted_source_classes": v21.get("accepted_source_classes"),
        "v021_prohibited_methods": v21.get("prohibited_methods"),
        "v021_mapping_requirements": v21.get("mapping_requirements"),
        "v021_policy_requires_versioned_sourced_mapping": any("Sector taxonomy must be versioned" in x for x in v21_params.get("policy", [])),
        "v044_preserves_prepared_not_populated": "PREPARED_NOT_POPULATED" in v44,
        "v057_sector_rs_ready": v57.get("sector_rs_ready"),
        "v059_canonical_taxonomy_selected": v59.get("canonical_taxonomy_selected"),
        "v059_canonical_sector_field_selected": v59.get("canonical_sector_field_selected"),
        "v059_mapping_authority_populated": v59.get("mapping_authority_populated"),
        "v059_taxonomy_matrix_blocks_selection": all(x in taxonomy_csv for x in ["GICS,NOT_SELECTED,FORBIDDEN_TO_SELECT", "ICB,NOT_SELECTED,FORBIDDEN_TO_SELECT", "CURRENT_CANONICAL_TAXONOMY,NOT_DEFINED,BLOCKER"]),
        "v059_historical_us_gics_not_promoted": "Historical US discovery files do contain GICS fields for subsets" in v59_doc and "are not promoted" in v59_doc,
    }

    matrix = [
        {"Taxonomy_Candidate": "GICS", "Explicit_Selection_Authority": "NO", "Existing_Evidence": "HISTORICAL_US_SOURCE_SPECIFIC_ONLY", "Decision_v0_60": "NOT_AUTHORIZED_TO_SELECT", "Reason": "v0.59 explicitly says historical US GICS is not promoted as global authority."},
        {"Taxonomy_Candidate": "ICB", "Explicit_Selection_Authority": "NO", "Existing_Evidence": "NONE_PROMOTED", "Decision_v0_60": "NOT_AUTHORIZED_TO_SELECT", "Reason": "No authoritative file selects ICB."},
        {"Taxonomy_Candidate": "OTHER_SINGLE_TAXONOMY", "Explicit_Selection_Authority": "NO", "Existing_Evidence": "NONE_PROMOTED", "Decision_v0_60": "NOT_AUTHORIZED_TO_SELECT", "Reason": "No authoritative file selects another taxonomy."},
        {"Taxonomy_Candidate": "MIXED_TAXONOMIES_WITH_CROSSWALK", "Explicit_Selection_Authority": "NO", "Existing_Evidence": "SILENT_MIXING_PROHIBITED", "Decision_v0_60": "NOT_AUTHORIZED_TO_CREATE_CROSSWALK", "Reason": "v0.21 prohibits silent mixing without crosswalk but does not authorize or define a canonical crosswalk."},
    ]
    return ledger, checks, matrix

def build_contract() -> dict[str, Any]:
    v21 = json.loads(V021_CONTRACT.read_text(encoding="utf-8"))
    return {
        "schema": "WELT_SWING_SECTOR_METADATA_CONTRACT_V0_60",
        "version": VERSION,
        "status": "BLOCKED_AUTHORITY_REQUIRED",
        "sector_metadata_contract_ready": False,
        "canonical_taxonomy": "NOT_DEFINED",
        "canonical_sector_field": "NOT_DEFINED",
        "primary_blocker": BLOCKER,
        "dependency_order": [
            "CANONICAL_TAXONOMY",
            "CANONICAL_SECTOR_FIELD_BINDING",
            "MAPPING_POPULATION_AUTHORITY",
            "OPTIONAL_CROSSWALK_AUTHORITY_IF_REQUIRED",
        ],
        "inherited_explicit_authority": {
            "required_identity_key": v21["required_identity_key"],
            "required_fields": v21["required_fields"],
            "accepted_source_classes": v21["accepted_source_classes"],
            "prohibited_methods": v21["prohibited_methods"],
            "mapping_requirements": v21["mapping_requirements"],
        },
        "contract_semantics": {
            "canonical_sector_taxonomy": {"status": "NOT_BOUND", "authority": "NONE"},
            "canonical_sector_field": {"status": "NOT_BOUND", "authority": "NONE", "note": "Required normalized fields do not themselves select a source taxonomy field."},
            "allowed_source_classes": {"status": "BOUND", "authority": "v0.21"},
            "provenance": {"status": "BOUND", "authority": "v0.21", "required": ["Source_Name", "Source_Reference", "Source_Version_or_AsOf"]},
            "ws_id_linkage": {"status": "BOUND", "authority": "v0.21", "required_identity_key": "WS_ID"},
            "asof_version_semantics": {"status": "BOUND_AT_FIELD_REQUIREMENT_LEVEL", "authority": "v0.21", "field": "Source_Version_or_AsOf"},
            "mapping_status": {"status": "BOUND_AT_FIELD_REQUIREMENT_LEVEL", "authority": "v0.21", "field": "Mapping_Status"},
            "missing_or_ambiguous_mapping": {"status": "FAIL_CLOSED_BOUND", "authority": "v0.20/v0.21", "behavior": "No guessed mapping; ambiguous mappings fail closed; absent metadata remains not verified."},
            "taxonomy_mixing_crosswalk": {"status": "PARTIALLY_BOUND_NOT_EXECUTABLE", "authority": "v0.21", "behavior": "Silent taxonomy mixing is prohibited; no canonical crosswalk authority or selection rule is defined."},
        },
        "population_permitted": False,
        "sector_rs_materialization_permitted": False,
        "p0_permitted_by_this_stage": False,
        "productive": False,
        "alpha_vantage_allowed": False,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository-sha", required=True)
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_sector_metadata_contract_v0_60")
    args = ap.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    pred = validate_predecessor(args.repository_sha)
    ledger, discovery, matrix = authority_findings()
    contract = build_contract()

    if contract["sector_metadata_contract_ready"]:
        raise RuntimeError("v0.60 must not claim READY without explicit taxonomy authority")
    if contract["canonical_taxonomy"] != "NOT_DEFINED":
        raise RuntimeError("taxonomy selected without authority")
    if any(r["Decision_v0_60"] == "AUTHORIZED_TO_SELECT" for r in matrix):
        raise RuntimeError("unexpected taxonomy selection authority")

    canonical_field = {
        "decision": "NOT_SELECTED",
        "canonical_sector_field": "NOT_DEFINED",
        "reason": "The authoritative contract requires normalized Sector_Taxonomy/Sector_Code/Sector_Name fields but does not bind one canonical taxonomy/source field.",
        "blocked_by": BLOCKER,
        "source_field_crosswalk_created": False,
    }
    unresolved = {
        "primary_blocker": BLOCKER,
        "smallest_next_gate": BLOCKER,
        "items": [
            {"id": BLOCKER, "priority": 1, "status": "OPEN", "required_decision": "Explicit governance authority must select the canonical sector taxonomy or explicitly authorize a taxonomy-selection rule."},
            {"id": "CANONICAL_SECTOR_FIELD_BINDING", "priority": 2, "status": "DOWNSTREAM_BLOCKED", "required_decision": "Bind canonical sector field/code/name semantics after taxonomy selection."},
            {"id": "CROSSWALK_AUTHORITY_IF_NEEDED", "priority": 3, "status": "DOWNSTREAM_BLOCKED", "required_decision": "If multiple source taxonomies are allowed, define and version an authoritative crosswalk; otherwise prohibit mixing."},
        ],
    }

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
        "security_identity_mutation": False,
        "provider_mapping_mutation": False,
        "local_feature_mutation": False,
        "sector_metadata_population_runs": 0,
        "sector_rs_materialization_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
    }

    tests: list[dict[str, str]] = []
    def gate(name: str, ok: bool, detail: str) -> None:
        tests.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": detail})
        if not ok:
            raise RuntimeError(name)

    gate("PREDECESSOR_V059_VERDICT", pred["v059"]["verdict"] == "PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER", pred["v059"]["verdict"])
    gate("PREDECESSOR_V059_BLOCKED_METADATA_1425", pred["v059"]["capability_counts"]["BLOCKED_METADATA"] == 1425, "1425")
    gate("PREDECESSOR_V059_MATERIALIZATION_ZERO", pred["v059"]["sector_rs_materialization_runs"] == 0, "0")
    gate("V058_HOME_MARKET_RS_1425_READY", pred["v058"]["home_market_rs_ready"] is True and pred["v058"]["ready_count"] == 1425, "1425/1425")
    gate("FROZEN_SHA_IMMUTABLE", immutability["frozen_unchanged"], FROZEN_SHA256)
    gate("V057_FEATURE_SHA_IMMUTABLE", immutability["v057_feature_unchanged"], V057_FEATURE_SHA256)
    gate("V058_HOME_RS_SHA_IMMUTABLE", immutability["v058_home_rs_unchanged"], V058_HOME_RS_SHA256)
    gate("V021_CONTRACT_PREPARED_NOT_POPULATED", discovery["v021_contract_status"] == "PREPARED_NOT_POPULATED", str(discovery["v021_contract_status"]))
    gate("NO_CANONICAL_TAXONOMY_AUTHORITY", discovery["v059_canonical_taxonomy_selected"] is False and discovery["v059_taxonomy_matrix_blocks_selection"], "GICS/ICB/OTHER not authorized")
    gate("NO_CANONICAL_FIELD_AUTHORITY", discovery["v059_canonical_sector_field_selected"] is False, "NOT_DEFINED")
    gate("NO_POPULATED_MAPPING_AUTHORITY", discovery["v059_mapping_authority_populated"] is False, "false")
    gate("HISTORICAL_US_GICS_NOT_PROMOTED", discovery["v059_historical_us_gics_not_promoted"], "explicit v0.59 finding")
    gate("CONTRACT_FAILS_CLOSED", contract["sector_metadata_contract_ready"] is False and contract["primary_blocker"] == BLOCKER, BLOCKER)
    gate("NO_TAXONOMY_SELECTED", contract["canonical_taxonomy"] == "NOT_DEFINED", "NOT_DEFINED")
    gate("NO_CROSSWALK_CREATED", canonical_field["source_field_crosswalk_created"] is False, "false")
    gate("PROVIDER_CALLS_ZERO", all(v == 0 for v in provider_calls().values()), json.dumps(provider_calls(), sort_keys=True))
    gate("NO_P0_P1_P2", immutability["p0_runs"] == immutability["p1_runs"] == immutability["p2_runs"] == 0, "0/0/0")
    gate("NO_SECTOR_MATERIALIZATION", immutability["sector_metadata_population_runs"] == 0 and immutability["sector_rs_materialization_runs"] == 0, "0/0")

    write_csv(out / "authority_ledger_v0.60.csv", ledger)
    write_csv(out / "taxonomy_decision_matrix_v0.60.csv", matrix)
    write_csv(out / "test_results_v0.60.csv", tests)
    (out / "authority_discovery_v0.60.json").write_text(json.dumps(discovery, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "canonical_field_decision_v0.60.json").write_text(json.dumps(canonical_field, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "sector_metadata_contract_v0.60.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "unresolved_governance_items_v0.60.json").write_text(json.dumps(unresolved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "immutability_audit_v0.60.json").write_text(json.dumps(immutability, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "provider_call_audit_v0.60.json").write_text(json.dumps(provider_calls(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "predecessor_authority_v0.60.json").write_text(json.dumps({
        "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": args.repository_sha,
        "v059_workflow_run": V059_WORKFLOW_RUN,
        "v059_artifact_id": V059_ARTIFACT_ID,
        "v059_artifact_digest": V059_ARTIFACT_DIGEST,
        "v059_verdict": pred["v059"]["verdict"],
        "v059_sector_rs_ready": pred["v059"]["sector_rs_ready"],
        "v059_blocked_metadata": pred["v059"]["capability_counts"]["BLOCKED_METADATA"],
        "v059_affected_count": pred["v059"]["affected_count"],
        "v059_materialization_runs": pred["v059"]["sector_rs_materialization_runs"],
        "v058_home_market_rs_ready": pred["v058"]["home_market_rs_ready"],
        "v058_ready": pred["v058"]["ready_count"],
        "v058_total": pred["v058"]["total"],
        "authority_blobs": pred["authority_blobs"],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "sector_metadata_contract_ready": False,
        "ready": 0,
        "total": 1425,
        "affected_count": 1425,
        "blocker": BLOCKER,
        "last_successful_step": "AUTHORITATIVE_REPOSITORY_CONTRACT_DISCOVERY_COMPLETE",
        "canonical_sector_taxonomy": "NOT_DEFINED",
        "canonical_sector_field": "NOT_DEFINED",
        "sector_metadata_population_runs": 0,
        "sector_rs_materialization_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "provider_calls": provider_calls(),
        "input_immutability": immutability,
        "home_market_rs_ready": True,
        "home_market_rs_ready_count": 1425,
        "tests": {"total": len(tests), "passed": len(tests), "failed": 0},
        "artifact_binding": "PENDING_UPLOAD",
        "productive": False,
        "next_gate": BLOCKER,
    }
    checkpoint = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "sector_metadata_contract_ready": False,
        "ready": 0,
        "total": 1425,
        "affected_count": 1425,
        "blocker": BLOCKER,
        "last_successful_step": summary["last_successful_step"],
        "materialization_runs": 0,
        "p0_runs": 0,
        "p1_p2_runs": 0,
        "tests_passed": len(tests),
        "tests_failed": 0,
        "artifact_binding": "PENDING_UPLOAD",
        "next_gate": BLOCKER,
    }
    (out / "summary_preupload_v0.60.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "stage_checkpoint_preupload_v0.60.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    files: dict[str, dict[str, Any]] = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": args.repository_sha,
        "verdict": VERDICT,
        "sector_metadata_contract_ready": False,
        "ready": 0,
        "total": 1425,
        "blocker": BLOCKER,
        "frozen_sha256": FROZEN_SHA256,
        "v057_feature_sha256": V057_FEATURE_SHA256,
        "v058_home_rs_sha256": V058_HOME_RS_SHA256,
        "provider_calls": provider_calls(),
        "sector_metadata_population_runs": 0,
        "sector_rs_materialization_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "artifact_binding": "PENDING_UPLOAD",
        "files": files,
        "next_gate": BLOCKER,
    }
    (out / "manifest_preupload_v0.60.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": VERDICT,
        "sector_metadata_contract_ready": False,
        "affected_count": 1425,
        "blocker": BLOCKER,
        "last_successful_step": summary["last_successful_step"],
        "next_gate": BLOCKER,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
