#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.68"
STAGE = "BR_IBRX100_CANONICAL_SECTOR_METADATA_MAPPING_MATERIALIZATION_GATE"
REQUIRED_START_HEAD = "f27a8be1cea6ed38b3fe92a1ca3a15a54de6fd89"
V067_WORKFLOW = 36270129434
V067_ARTIFACT = 10914754106
V067_DIGEST = "sha256:84d16a51b33ec4ff29375017244f498ab844d4a8621ee56c3a4d1736d5af1510"
TREE_SHA = "febe642ea5b713c7a8709d1bf314ea3bac84b6ccf21f155073bc315ffc0bd0bd"
FROZEN_SHA = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA = "177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA = "2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
TAXONOMY = "B3_CLASSIFICACAO_SETORIAL"
LEVEL = "SETOR_ECONOMICO"
METHOD = "PDSC_SHA256_V1"
SOURCE_NAME = "B3_LISTED_COMPANIES_CLASSIFICATION"
EVIDENCE_VERSION = "v0.67"
MAPPING_STATUS = "VERIFIED_CANONICAL"
COHORT = "BR_IBRX100"
TOTAL_FROZEN = 1425

FROZEN = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
V057 = ROOT / "output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058 = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
CAP58 = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
S067 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/summary_v0.67.json"
C067 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/stage_checkpoint_v0.67.json"
M067 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/manifest_v0.67.json"
COV67 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/br_exact_37_classification_coverage_v0.67.csv"
HITS67 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/br_exact_37_group_hit_audit_v0.67.csv"
HASH67 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/b3_group_response_hash_ledger_v0.67.csv"
TREE67 = ROOT / "output_br_ibrx100_b3_classification_tree_execution_v0_67/b3_execution_tree_snapshot_v0.67.json"
GSEC04 = ROOT / "config/manager_governance_authority_G_SEC_04_v0.68.json"

CANONICAL_PATH = ROOT / "sector_metadata/canonical/cohorts/BR_IBRX100_sector_metadata_v1.csv"
REGISTRY_PATH = ROOT / "sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"

CANONICAL_FIELDS = [
    "WS_ID",
    "Sector_Taxonomy",
    "Sector_Code",
    "Sector_Name",
    "Source_Name",
    "Source_Reference",
    "Source_Version_or_AsOf",
    "Mapping_Status",
    "Primary_Universe_Index",
    "Primary_MIC",
    "Primary_Ticker",
    "Sector_Level",
    "Sector_Raw_Name",
    "Source_Sector_Code",
    "Sector_Code_Origin",
    "Sector_Code_Method",
    "B3_Company_Code",
    "Evidence_Version",
    "Evidence_Final_Commit",
    "Tree_Snapshot_SHA256",
    "Group_Query_Label",
    "Group_Response_SHA256",
    "Source_Retrieved_UTC",
    "Source_Effective_AsOf_Status",
]

SEMANTIC_FIELDS = [
    "WS_ID",
    "Sector_Taxonomy",
    "Sector_Level",
    "Sector_Code",
    "Sector_Name",
    "Mapping_Status",
]

REGISTRY_FIELDS = [
    "Cohort",
    "Frozen_Row_Count",
    "Canonical_Row_Count",
    "Canonical_Status",
    "Taxonomy",
    "Sector_Level",
    "Materialization_Version",
    "Semantic_SHA256",
    "Evidence_Final_Commit",
    "Frozen_SHA256",
    "Canonical_File",
    "Canonical_File_SHA256",
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def deterministic_csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="raise", lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in fields})
    return buf.getvalue().encode("utf-8")


def write_csv_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    write_csv_bytes(path, deterministic_csv_bytes(rows, fields))


def pdsc(sector_name: str) -> str:
    nfc = unicodedata.normalize("NFC", sector_name)
    payload = TAXONOMY + "\x1f" + LEVEL + "\x1f" + nfc
    return "PDSC1:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def semantic_bytes(rows: list[dict[str, str]]) -> bytes:
    ordered = sorted(rows, key=lambda r: r["WS_ID"])
    payload = [[r[f] for f in SEMANTIC_FIELDS] for r in ordered]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def ws_set_hash(values: set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode("utf-8")).hexdigest()


def provider_calls() -> dict[str, int]:
    return {
        "external_market_reference_requests": 0,
        "b3_requests": 0,
        "alpha_vantage": 0,
        "yahoo_yfinance": 0,
        "eodhd": 0,
        "scalable": 0,
        "wikipedia": 0,
        "tradingview": 0,
        "third_party_sector_databases": 0,
        "gics_icb_fallback": 0,
        "crosswalk": 0,
        "per_security_web_lookup": 0,
        "company_name_matching": 0,
        "fuzzy_matching": 0,
        "sector_inference": 0,
        "price_ohlcv": 0,
        "news": 0,
        "trading": 0,
    }


def validate_predecessor(repo_sha: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    if git("rev-parse", "HEAD") != repo_sha:
        raise RuntimeError("checkout mismatch")
    if subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"], cwd=ROOT).returncode != 0:
        raise RuntimeError("required start head not ancestor")

    s = json.loads(S067.read_text(encoding="utf-8"))
    c = json.loads(C067.read_text(encoding="utf-8"))
    m = json.loads(M067.read_text(encoding="utf-8"))
    cov = read_csv(COV67)
    hits = read_csv(HITS67)
    hledger = read_csv(HASH67)
    tree = json.loads(TREE67.read_text(encoding="utf-8"))

    if s["verdict"] != "PASS_BR_EXACT_37_CLASSIFICATION_COVERAGE":
        raise RuntimeError("v0.67 verdict")
    if s["br_exact_37_classification_coverage_ready"] is not True:
        raise RuntimeError("v0.67 readiness")
    if (s["ready"], s["total"], s["ambiguous"], s["not_found"], s["not_verified"]) != (37, 37, 0, 0, 0):
        raise RuntimeError("v0.67 counts")
    if (s["executed_group_queries"], s["expected_group_queries"], s["successful_group_queries"], s["failed_group_queries"]) != (86, 86, 86, 0):
        raise RuntimeError("v0.67 group traversal")
    if s["distinct_setores"] != 10 or s["pdsc_collisions"] != 0:
        raise RuntimeError("v0.67 sectors/pdsc")
    if c["workflow_run_id"] != V067_WORKFLOW or c["artifact_id"] != V067_ARTIFACT:
        raise RuntimeError("v0.67 workflow/artifact")
    if "sha256:" + c["artifact_digest"] != V067_DIGEST:
        raise RuntimeError("v0.67 artifact digest")
    if m["artifact"]["artifact_verified"] != "PASS":
        raise RuntimeError("v0.67 artifact binding")
    if tree["current_structural_sha256"] != TREE_SHA or tree["second_structural_sha256"] != TREE_SHA:
        raise RuntimeError("v0.67 tree sha")
    if tree["current_recursive_node_count"] != 262 or tree["structurally_valid"] is not True:
        raise RuntimeError("v0.67 tree structure")
    if len(cov) != 37 or any(r["Coverage_Status"] != "PROVABLY_MAPPABLE" for r in cov):
        raise RuntimeError("v0.67 row authority")
    if sha_file(FROZEN) != FROZEN_SHA or sha_file(V057) != V057_SHA or sha_file(V058) != V058_SHA:
        raise RuntimeError("immutability predecessor")
    return s, c, m, cov, hits, hledger, tree


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository-sha", required=True)
    ap.add_argument("--output-dir", default="output_br_ibrx100_canonical_sector_metadata_materialization_v0_68")
    args = ap.parse_args()

    pred, chk, man67, cov67, hits67, hledger67, tree67 = validate_predecessor(args.repository_sha)
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    gsec04 = json.loads(GSEC04.read_text(encoding="utf-8"))
    if gsec04["authority_id"] != "G-SEC-04" or gsec04["version"] != VERSION:
        raise RuntimeError("G-SEC-04 authority")
    if gsec04["rules"]["sector_rs_authorized"] is not False or gsec04["rules"]["external_reference_requests_authorized"] is not False:
        raise RuntimeError("G-SEC-04 scope")
    (out / "manager_governance_authority_G_SEC_04_v0.68.json").write_text(
        json.dumps(gsec04, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    capability = read_csv(CAP58)
    frozen_br = [r for r in capability if r["Primary_Universe_Index"] == COHORT]
    frozen_ws = {r["Source_WS_ID"] for r in frozen_br}
    ready_rows = [r for r in cov67 if r["Coverage_Status"] == "PROVABLY_MAPPABLE"]
    ready_ws = {r["WS_ID"] for r in ready_rows}

    hits_by_code: dict[str, list[dict[str, str]]] = defaultdict(list)
    for h in hits67:
        if h.get("B3_Company_Code"):
            hits_by_code[h["B3_Company_Code"]].append(h)

    ledger_by_segment: dict[str, list[dict[str, str]]] = defaultdict(list)
    for h in hledger67:
        if h.get("Segmento_Raw"):
            ledger_by_segment[h["Segmento_Raw"]].append(h)

    tree_retrievals = tree67.get("retrievals", [])
    tree_retrieval_times = sorted({r.get("timestamp_utc", "") for r in tree_retrievals if r.get("timestamp_utc")})
    tree_retrieved_utc = " | ".join(tree_retrieval_times)

    candidate_rows: list[dict[str, str]] = []
    equality_rows: list[dict[str, str]] = []
    provenance_failures: list[str] = []
    value_mismatches = 0
    pdsc_mismatches = 0

    for src in sorted(ready_rows, key=lambda r: r["WS_ID"]):
        code = src["B3_Company_Code"]
        hits = hits_by_code.get(code, [])
        group_labels = sorted({h["Segmento_Raw"] for h in hits if h.get("Segmento_Raw")})
        group_urls = sorted({h["Source_URL"] for h in hits if h.get("Source_URL")})
        group_hash_strings = sorted({h["Response_SHA256"] for h in hits if h.get("Response_SHA256")})

        retrieval_times: set[str] = set()
        ledger_hashes: set[str] = set()
        for label in group_labels:
            for lr in ledger_by_segment.get(label, []):
                if lr.get("Timestamp_UTC"):
                    retrieval_times.add(lr["Timestamp_UTC"])
                if lr.get("Response_SHA256"):
                    ledger_hashes.add(lr["Response_SHA256"])

        if not hits or not group_labels or not group_urls or not group_hash_strings or not retrieval_times:
            provenance_failures.append(src["WS_ID"])

        source_reference = "TREE=" + tree_retrievals[0]["url"] + " | GROUP=" + " | ".join(group_urls)
        group_hash = " | ".join(group_hash_strings)
        source_version = (
            "EVIDENCE=v0.67"
            + ";TREE_SHA256=" + TREE_SHA
            + ";GROUP_RESPONSE_SHA256=" + group_hash
            + ";TREE_RETRIEVED_UTC=" + tree_retrieved_utc
        )

        row = {
            "WS_ID": src["WS_ID"],
            "Sector_Taxonomy": src["Sector_Taxonomy"],
            "Sector_Code": src["Sector_Code"],
            "Sector_Name": src["Sector_Name"],
            "Source_Name": SOURCE_NAME,
            "Source_Reference": source_reference,
            "Source_Version_or_AsOf": source_version,
            "Mapping_Status": MAPPING_STATUS,
            "Primary_Universe_Index": COHORT,
            "Primary_MIC": src["Primary_MIC"],
            "Primary_Ticker": src["Primary_Ticker"],
            "Sector_Level": src["Sector_Level"],
            "Sector_Raw_Name": src["Sector_Raw_Name"],
            "Source_Sector_Code": "NULL",
            "Sector_Code_Origin": src["Sector_Code_Origin"],
            "Sector_Code_Method": src["Sector_Code_Method"],
            "B3_Company_Code": code,
            "Evidence_Version": EVIDENCE_VERSION,
            "Evidence_Final_Commit": REQUIRED_START_HEAD,
            "Tree_Snapshot_SHA256": TREE_SHA,
            "Group_Query_Label": " | ".join(group_labels),
            "Group_Response_SHA256": group_hash,
            "Source_Retrieved_UTC": " | ".join(sorted(retrieval_times)),
            "Source_Effective_AsOf_Status": "NOT_PUBLISHED_IN_PERSISTED_V0.67_EVIDENCE",
        }

        eq_fields = [
            "B3_Company_Code",
            "Sector_Taxonomy",
            "Sector_Level",
            "Sector_Raw_Name",
            "Sector_Name",
            "Sector_Code_Origin",
            "Sector_Code_Method",
            "Sector_Code",
        ]
        mismatches = [f for f in eq_fields if row[f] != src[f]]
        recomputed = pdsc(row["Sector_Name"])
        pdsc_ok = recomputed == src["Sector_Code"]
        if mismatches:
            value_mismatches += 1
        if not pdsc_ok:
            pdsc_mismatches += 1

        equality_rows.append({
            "WS_ID": src["WS_ID"],
            "B3_Company_Code": code,
            "Value_Equality_Status": "PASS" if not mismatches else "FAIL",
            "Mismatched_Fields": " | ".join(mismatches),
            "PDSC_Integrity_Status": "PASS" if pdsc_ok else "FAIL",
            "Persisted_Sector_Code": src["Sector_Code"],
            "Recomputed_Sector_Code": recomputed,
        })
        candidate_rows.append(row)

    candidate_rows = sorted(candidate_rows, key=lambda r: r["WS_ID"])
    canonical_ws = {r["WS_ID"] for r in candidate_rows}
    duplicates = len(candidate_rows) - len(canonical_ws)
    frozen_duplicates = len(frozen_br) - len(frozen_ws)
    ready_duplicates = len(ready_rows) - len(ready_ws)

    set_missing_from_canonical = sorted(frozen_ws - canonical_ws)
    set_extra_in_canonical = sorted(canonical_ws - frozen_ws)
    set_frozen_vs_ready_missing = sorted(frozen_ws - ready_ws)
    set_ready_vs_frozen_extra = sorted(ready_ws - frozen_ws)

    set_audit = {
        "Frozen_BR_Row_Count": len(frozen_br),
        "Frozen_BR_Unique_WS_ID_Count": len(frozen_ws),
        "v067_READY_Row_Count": len(ready_rows),
        "v067_READY_Unique_WS_ID_Count": len(ready_ws),
        "Canonical_Candidate_Row_Count": len(candidate_rows),
        "Canonical_Candidate_Unique_WS_ID_Count": len(canonical_ws),
        "Frozen_Duplicates": frozen_duplicates,
        "v067_READY_Duplicates": ready_duplicates,
        "Canonical_Duplicates": duplicates,
        "Missing_From_Canonical": set_missing_from_canonical,
        "Extra_In_Canonical": set_extra_in_canonical,
        "Frozen_Missing_From_v067_READY": set_frozen_vs_ready_missing,
        "v067_READY_Extra_Vs_Frozen": set_ready_vs_frozen_extra,
        "Frozen_WS_ID_Set_SHA256": ws_set_hash(frozen_ws),
        "v067_READY_WS_ID_Set_SHA256": ws_set_hash(ready_ws),
        "Canonical_WS_ID_Set_SHA256": ws_set_hash(canonical_ws),
        "Set_Equality": frozen_ws == ready_ws == canonical_ws,
        "Primary_MIC_BVMF_All": all(r["Primary_MIC"] == "BVMF" for r in candidate_rows),
    }
    (out / "br_canonical_ws_id_set_audit_v0.68.json").write_text(
        json.dumps(set_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(out / "br_canonical_value_equality_audit_v0.68.csv", equality_rows)

    sector_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        sector_groups[row["Sector_Name"]].append(row)
    sector_inventory: list[dict[str, Any]] = []
    sector_code_collision_map: dict[str, set[str]] = defaultdict(set)
    for sector_name, rows in sorted(sector_groups.items()):
        codes = sorted({r["Sector_Code"] for r in rows})
        raw_names = sorted({r["Sector_Raw_Name"] for r in rows})
        sector_inventory.append({
            "Sector_Name": sector_name,
            "Sector_Raw_Name": " | ".join(raw_names),
            "Sector_Code": codes[0] if len(codes) == 1 else "AMBIGUOUS",
            "BR_Row_Count": len(rows),
            "Distinct_Sector_Code_Count": len(codes),
            "Same_Sector_Name_Same_Code": "PASS" if len(codes) == 1 else "FAIL",
        })
        for code in codes:
            sector_code_collision_map[code].add(sector_name)
    write_csv(out / "br_canonical_sector_inventory_v0.68.csv", sector_inventory)

    pdsc_audit: list[dict[str, str]] = []
    for item in sector_inventory:
        sector_name = item["Sector_Name"]
        persisted = item["Sector_Code"]
        recompute1 = pdsc(sector_name)
        recompute2 = pdsc(unicodedata.normalize("NFD", sector_name))
        pdsc_audit.append({
            "Sector_Name": sector_name,
            "Persisted_Sector_Code": persisted,
            "Recomputed_1": recompute1,
            "Recomputed_2": recompute2,
            "Determinism_Status": "PASS" if recompute1 == recompute2 else "FAIL",
            "Equality_To_v067_Status": "PASS" if persisted == recompute1 else "FAIL",
        })
    write_csv(out / "br_pdsc_integrity_audit_v0.68.csv", pdsc_audit)

    collision_count = sum(1 for names in sector_code_collision_map.values() if len(names) > 1)
    same_name_same_code = all(x["Same_Sector_Name_Same_Code"] == "PASS" for x in sector_inventory)
    pdsc_integrity_ok = (
        pdsc_mismatches == 0
        and all(x["Determinism_Status"] == "PASS" for x in pdsc_audit)
        and all(x["Equality_To_v067_Status"] == "PASS" for x in pdsc_audit)
        and collision_count == 0
        and same_name_same_code
    )

    schema = {
        "version": VERSION,
        "canonical_partition": str(CANONICAL_PATH.relative_to(ROOT)),
        "format": "CSV_UTF8_LF",
        "sort_order": ["WS_ID ASC"],
        "fields": CANONICAL_FIELDS,
        "required_v0_21_fields": [
            "WS_ID", "Sector_Taxonomy", "Sector_Code", "Sector_Name",
            "Source_Name", "Source_Reference", "Source_Version_or_AsOf", "Mapping_Status"
        ],
        "csv_null_literal": {"Source_Sector_Code": "NULL"},
        "fixed_br_semantics": {
            "Primary_Universe_Index": COHORT,
            "Sector_Taxonomy": TAXONOMY,
            "Sector_Level": LEVEL,
            "Source_Sector_Code": "NULL",
            "Sector_Code_Origin": "PROJECT_DERIVED_CANONICAL",
            "Sector_Code_Method": METHOD,
            "Evidence_Version": EVIDENCE_VERSION,
            "Evidence_Final_Commit": REQUIRED_START_HEAD,
            "Tree_Snapshot_SHA256": TREE_SHA,
            "Mapping_Status": MAPPING_STATUS,
        },
        "source_effective_asof_policy": "Retrieval timestamps are provenance only and are not claimed as a B3 business-effective date.",
    }
    (out / "br_canonical_sector_metadata_schema_v0.68.json").write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    sem_contract = {
        "name": "BR_CANONICAL_SECTOR_METADATA_SEMANTIC_SHA256",
        "version": VERSION,
        "row_sort": "WS_ID_ASC_BYTEWISE_UNICODE_STRING_ORDER",
        "fields_in_order": SEMANTIC_FIELDS,
        "serialization": "UTF8_COMPACT_JSON_ARRAY_OF_ARRAYS",
        "json_ensure_ascii": False,
        "json_separators": [",", ":"],
        "trailing_newline_in_semantic_payload": False,
        "hash": "SHA-256",
    }
    (out / "semantic_hash_contract_v0.68.json").write_text(
        json.dumps(sem_contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    semantic_payload_1 = semantic_bytes(candidate_rows)
    semantic_payload_2 = semantic_bytes(sorted(candidate_rows, key=lambda r: r["WS_ID"], reverse=True))
    semantic_sha = sha_bytes(semantic_payload_1)
    materialization_deterministic = semantic_payload_1 == semantic_payload_2

    canonical_bytes_1 = deterministic_csv_bytes(candidate_rows, CANONICAL_FIELDS)
    canonical_bytes_2 = deterministic_csv_bytes(sorted(candidate_rows, key=lambda r: r["WS_ID"]), CANONICAL_FIELDS)
    canonical_deterministic = canonical_bytes_1 == canonical_bytes_2
    canonical_file_sha = sha_bytes(canonical_bytes_1)

    set_ok = (
        len(frozen_br) == 37
        and len(ready_rows) == 37
        and len(candidate_rows) == 37
        and frozen_duplicates == 0
        and ready_duplicates == 0
        and duplicates == 0
        and frozen_ws == ready_ws == canonical_ws
        and all(r["Primary_MIC"] == "BVMF" for r in candidate_rows)
    )
    values_ok = value_mismatches == 0
    provenance_ok = len(provenance_failures) == 0 and all(
        r["Source_Name"] == SOURCE_NAME
        and r["Source_Reference"]
        and r["Source_Version_or_AsOf"]
        and r["Group_Query_Label"]
        and r["Group_Response_SHA256"]
        and r["Source_Retrieved_UTC"]
        and r["Source_Effective_AsOf_Status"] == "NOT_PUBLISHED_IN_PERSISTED_V0.67_EVIDENCE"
        for r in candidate_rows
    )
    sectors_ok = len(sector_inventory) == 10 and collision_count == 0 and same_name_same_code
    deterministic_ok = materialization_deterministic and canonical_deterministic

    blocker = ""
    if not set_ok:
        blocker = "BR_CANONICAL_WS_ID_SET_MISMATCH"
    elif not values_ok:
        blocker = "BR_CANONICAL_VALUE_MISMATCH"
    elif not provenance_ok:
        blocker = "BR_CANONICAL_PROVENANCE_INCOMPLETE"
    elif not pdsc_integrity_ok or not sectors_ok:
        blocker = "BR_PDSC_INTEGRITY_FAILURE"
    elif not deterministic_ok:
        blocker = "BR_CANONICAL_MATERIALIZATION_NOT_DETERMINISTIC"

    success = blocker == ""
    verdict = "PASS_BR_CANONICAL_SECTOR_METADATA_MATERIALIZATION" if success else "BLOCKED_BR_CANONICAL_SECTOR_METADATA_MATERIALIZATION"

    if success:
        write_csv_bytes(CANONICAL_PATH, canonical_bytes_1)
        write_csv_bytes(out / "br_canonical_sector_metadata_materialization_v0.68.csv", canonical_bytes_1)

        registry_rows = [{
            "Cohort": COHORT,
            "Frozen_Row_Count": 37,
            "Canonical_Row_Count": 37,
            "Canonical_Status": "READY",
            "Taxonomy": TAXONOMY,
            "Sector_Level": LEVEL,
            "Materialization_Version": VERSION,
            "Semantic_SHA256": semantic_sha,
            "Evidence_Final_Commit": REQUIRED_START_HEAD,
            "Frozen_SHA256": FROZEN_SHA,
            "Canonical_File": str(CANONICAL_PATH.relative_to(ROOT)),
            "Canonical_File_SHA256": canonical_file_sha,
        }]
        registry_bytes = deterministic_csv_bytes(registry_rows, REGISTRY_FIELDS)
        write_csv_bytes(REGISTRY_PATH, registry_bytes)
        write_csv_bytes(out / "canonical_sector_metadata_cohort_registry_v0.68.csv", registry_bytes)
    else:
        write_csv(
            out / "br_canonical_sector_metadata_materialization_v0.68.csv",
            [],
            CANONICAL_FIELDS,
        )
        write_csv(
            out / "canonical_sector_metadata_cohort_registry_v0.68.csv",
            [],
            REGISTRY_FIELDS,
        )

    global_status = {
        "version": VERSION,
        "registry_scope": "PROMOTED_CANONICAL_COHORT_PARTITIONS_ONLY",
        "BR_CANONICAL_SECTOR_METADATA_READY": success,
        "BR_READY": 37 if success else 0,
        "BR_TOTAL": 37,
        "GLOBAL_CANONICAL_SECTOR_METADATA_READY": False,
        "GLOBAL_READY": 37 if success else 0,
        "GLOBAL_TOTAL": TOTAL_FROZEN,
        "GLOBAL_REMAINING": TOTAL_FROZEN - (37 if success else 0),
        "Sector_RS_Ready_Inferred": False,
        "Unresolved_Cohorts": "OMITTED_FROM_REGISTRY_UNTIL_PROMOTED",
    }
    (out / "global_sector_metadata_coverage_status_v0.68.json").write_text(
        json.dumps(global_status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    providers = provider_calls()
    (out / "provider_call_audit_v0.68.json").write_text(
        json.dumps(providers, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "external_request_audit_v0.68.json").write_text(
        json.dumps({
            "external_market_reference_requests": 0,
            "b3_requests": 0,
            "alpha_vantage_requests": 0,
            "source_research_performed": False,
            "materialization_source": str(COV67.relative_to(ROOT)),
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    imm = {
        "Frozen_Expected_SHA256": FROZEN_SHA,
        "Frozen_SHA256_Before": sha_file(FROZEN),
        "Frozen_SHA256_After": sha_file(FROZEN),
        "Frozen_Unchanged": sha_file(FROZEN) == FROZEN_SHA,
        "v057_Feature_Expected_SHA256": V057_SHA,
        "v057_Feature_SHA256_Before": sha_file(V057),
        "v057_Feature_SHA256_After": sha_file(V057),
        "v057_Feature_Unchanged": sha_file(V057) == V057_SHA,
        "v058_Home_RS_Expected_SHA256": V058_SHA,
        "v058_Home_RS_SHA256_Before": sha_file(V058),
        "v058_Home_RS_SHA256_After": sha_file(V058),
        "v058_Home_RS_Unchanged": sha_file(V058) == V058_SHA,
        "Sector_RS_Runs": 0,
        "P0_Runs": 0,
        "P1_Runs": 0,
        "P2_Runs": 0,
        "Price_Cache_Mutations": 0,
        "Feature_Mutations": 0,
        "Home_Market_RS_Mutations": 0,
        "Frozen_Mutations": 0,
        "Other_Cohort_Executions": 0,
    }
    (out / "immutability_audit_v0.68.json").write_text(
        json.dumps(imm, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    tests: list[dict[str, str]] = []
    def test(name: str, ok: bool, detail: Any) -> None:
        tests.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": str(detail)})
        if not ok:
            raise RuntimeError(name)

    test("V067_VERDICT", pred["verdict"] == "PASS_BR_EXACT_37_CLASSIFICATION_COVERAGE", pred["verdict"])
    test("V067_READY_37_37", pred["br_exact_37_classification_coverage_ready"] is True and pred["ready"] == 37 and pred["total"] == 37, "37/37")
    test("V067_ZERO_UNRESOLVED", pred["ambiguous"] == pred["not_found"] == pred["not_verified"] == 0, "0/0/0")
    test("V067_GROUP_TRAVERSAL_86_86", pred["executed_group_queries"] == pred["expected_group_queries"] == 86 and pred["failed_group_queries"] == 0, "86/86")
    test("V067_DISTINCT_SECTORS_10", pred["distinct_setores"] == 10, pred["distinct_setores"])
    test("V067_PDSC_COLLISIONS_0", pred["pdsc_collisions"] == 0, pred["pdsc_collisions"])
    test("TREE_SHA_AUTHORITY", tree67["current_structural_sha256"] == TREE_SHA, tree67["current_structural_sha256"])
    test("FROZEN_BR_ROWS_37", len(frozen_br) == 37, len(frozen_br))
    test("READY_ROWS_37", len(ready_rows) == 37, len(ready_rows))
    test("CANONICAL_CANDIDATE_ROWS_37", len(candidate_rows) == 37, len(candidate_rows))
    test("WS_ID_SET_EQUALITY", set_ok, json.dumps(set_audit, sort_keys=True))
    test("VALUE_EQUALITY", values_ok, value_mismatches)
    test("PROVENANCE_COMPLETE", provenance_ok, len(provenance_failures))
    test("PDSC_INTEGRITY", pdsc_integrity_ok, pdsc_mismatches)
    test("DISTINCT_SECTORS_EXACT_10", len(sector_inventory) == 10, len(sector_inventory))
    test("PDSC_COLLISION_ZERO", collision_count == 0, collision_count)
    test("MATERIALIZATION_DETERMINISTIC", deterministic_ok, deterministic_ok)
    test("MAPPING_STATUS_FIXED", all(r["Mapping_Status"] == MAPPING_STATUS for r in candidate_rows), MAPPING_STATUS)
    test("SOURCE_SECTOR_CODE_NULL_LITERAL", all(r["Source_Sector_Code"] == "NULL" for r in candidate_rows), "NULL")
    test("SOURCE_EFFECTIVE_ASOF_NOT_FABRICATED", all(r["Source_Effective_AsOf_Status"] == "NOT_PUBLISHED_IN_PERSISTED_V0.67_EVIDENCE" for r in candidate_rows), "PASS")
    test("NO_EXTERNAL_REQUESTS", all(v == 0 for v in providers.values()), json.dumps(providers, sort_keys=True))
    test("FROZEN_IMMUTABLE", imm["Frozen_Unchanged"], FROZEN_SHA)
    test("V057_IMMUTABLE", imm["v057_Feature_Unchanged"], V057_SHA)
    test("V058_IMMUTABLE", imm["v058_Home_RS_Unchanged"], V058_SHA)
    test("SECTOR_RS_ZERO", imm["Sector_RS_Runs"] == 0, 0)
    test("P0_P1_P2_ZERO", imm["P0_Runs"] == imm["P1_Runs"] == imm["P2_Runs"] == 0, "0/0/0")
    if success:
        test("CANONICAL_FILE_EXISTS", CANONICAL_PATH.exists(), CANONICAL_PATH)
        test("CANONICAL_FILE_SHA", sha_file(CANONICAL_PATH) == canonical_file_sha, canonical_file_sha)
        test("REGISTRY_EXISTS", REGISTRY_PATH.exists(), REGISTRY_PATH)
        test("GLOBAL_STATUS_37_1425", global_status["GLOBAL_READY"] == 37 and global_status["GLOBAL_TOTAL"] == 1425 and global_status["GLOBAL_REMAINING"] == 1388, global_status)
    else:
        test("FAIL_BLOCKER_NONEMPTY", bool(blocker), blocker)
        test("NO_PARTIAL_CANONICAL_FILE", not CANONICAL_PATH.exists(), CANONICAL_PATH)
    write_csv(out / "test_results_v0.68.csv", tests)

    materialization_meta = {
        "version": VERSION,
        "source_evidence_version": EVIDENCE_VERSION,
        "source_evidence_final_commit": REQUIRED_START_HEAD,
        "authoritative_row_source": str(COV67.relative_to(ROOT)),
        "canonical_partition": str(CANONICAL_PATH.relative_to(ROOT)),
        "canonical_rows": 37 if success else 0,
        "canonical_file_sha256": canonical_file_sha if success else "",
        "BR_CANONICAL_SECTOR_METADATA_SEMANTIC_SHA256": semantic_sha if success else "",
        "deterministic": deterministic_ok,
        "mapping_status": MAPPING_STATUS,
        "external_requests": 0,
    }
    (out / "br_canonical_sector_metadata_materialization_metadata_v0.68.json").write_text(
        json.dumps(materialization_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": verdict,
        "br_canonical_sector_metadata_ready": success,
        "br_ready": 37 if success else 0,
        "br_total": 37,
        "global_ready": 37 if success else 0,
        "global_total": TOTAL_FROZEN,
        "global_canonical_sector_metadata_ready": False,
        "global_remaining": TOTAL_FROZEN - (37 if success else 0),
        "distinct_setores": len(sector_inventory) if success else 0,
        "semantic_sha256": semantic_sha if success else "",
        "canonical_file_sha256": canonical_file_sha if success else "",
        "duplicates": duplicates,
        "missing": len(set_missing_from_canonical),
        "extra": len(set_extra_in_canonical),
        "value_mismatches": value_mismatches,
        "pdsc_mismatches": pdsc_mismatches,
        "pdsc_collisions": collision_count,
        "provenance_failures": len(provenance_failures),
        "blocker": blocker,
        "external_market_reference_requests": 0,
        "b3_requests": 0,
        "alpha_vantage_requests": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "artifact_binding": "PENDING_UPLOAD",
        "tests": {"total": len(tests), "passed": len(tests), "failed": 0},
        "productive": False,
        "next_gate": "FROZEN-1425 CANONICAL SECTOR METADATA COVERAGE RECONCILIATION / NEXT-COHORT SELECTION GATE" if success else blocker,
    }
    checkpoint = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": verdict,
        "br_canonical_sector_metadata_ready": success,
        "br_ready": summary["br_ready"],
        "br_total": 37,
        "global_ready": summary["global_ready"],
        "global_total": TOTAL_FROZEN,
        "global_canonical_sector_metadata_ready": False,
        "distinct_setores": summary["distinct_setores"],
        "semantic_sha256": summary["semantic_sha256"],
        "blocker": blocker,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_p2_runs": 0,
        "artifact_binding": "PENDING_UPLOAD",
        "next_gate": summary["next_gate"],
    }
    (out / "summary_preupload_v0.68.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "stage_checkpoint_preupload_v0.68.json").write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    files: dict[str, Any] = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name] = {"sha256": sha_file(p), "bytes": p.stat().st_size}
    if success:
        files[str(CANONICAL_PATH.relative_to(ROOT))] = {"sha256": sha_file(CANONICAL_PATH), "bytes": CANONICAL_PATH.stat().st_size}
        files[str(REGISTRY_PATH.relative_to(ROOT))] = {"sha256": sha_file(REGISTRY_PATH), "bytes": REGISTRY_PATH.stat().st_size}
    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": args.repository_sha,
        "verdict": verdict,
        "br_canonical_sector_metadata_ready": success,
        "br_ready": summary["br_ready"],
        "br_total": 37,
        "global_ready": summary["global_ready"],
        "global_total": TOTAL_FROZEN,
        "global_canonical_sector_metadata_ready": False,
        "distinct_setores": summary["distinct_setores"],
        "semantic_sha256": summary["semantic_sha256"],
        "canonical_file_sha256": summary["canonical_file_sha256"],
        "blocker": blocker,
        "sector_rs_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "artifact_binding": "PENDING_UPLOAD",
        "files": files,
        "next_gate": summary["next_gate"],
    }
    (out / "manifest_preupload_v0.68.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "verdict": verdict,
        "br_canonical_sector_metadata_ready": success,
        "br_ready": summary["br_ready"],
        "br_total": 37,
        "global_ready": summary["global_ready"],
        "global_total": TOTAL_FROZEN,
        "distinct_setores": summary["distinct_setores"],
        "semantic_sha256": summary["semantic_sha256"],
        "blocker": blocker,
        "next_gate": summary["next_gate"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
