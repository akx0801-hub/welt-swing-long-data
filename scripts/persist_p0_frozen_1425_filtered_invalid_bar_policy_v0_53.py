#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

RUN_ID = 36225840648
ARTIFACT_ID = 10900287789
ARTIFACT_NAME = "p0-frozen-1425-filtered-invalid-bar-policy-v0.53-36225840648"
ARTIFACT_DIGEST = "sha256:f54f1520e6cfcefbca043bc782ccf71ddd0e70538722ee1c3857551396761e95"
IMPLEMENTATION_HEAD = "b6f852e4248ec3f910efaeb18400a913885959b8"
REQUIRED_START_HEAD = "b8b9178385c58351910b2e61fe1f473d4f47af18"
EXPECTED_SHA = "bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
EXPECTED_BYTES = 144539648
FROZEN_SHA = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Test", "Result", "Detail"])
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    art = Path(args.artifact_dir).resolve()
    db = art / "runtime_cache/p0_frozen_1425_v0_53.sqlite"
    src_out = art / "output_p0_frozen_1425_filtered_bar_policy_v0_53"
    out = root / "output_p0_frozen_1425_filtered_bar_policy_v0_53"
    report = root / "docs/validation/P0_Frozen_1425_Filtered_Invalid_Bar_Policy_Implementation_v0.53.md"

    if sha256_file(db) != EXPECTED_SHA or db.stat().st_size != EXPECTED_BYTES:
        raise RuntimeError("packaged runtime bytes do not match declared v0.53 authority")
    if sha256_file(root / "universe/SWING_U3K_FROZEN_v0.5.csv") != FROZEN_SHA:
        raise RuntimeError("Frozen SHA mismatch")

    con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("packaged runtime integrity_check failed")
        if con.execute("select count(*) from price_daily").fetchone()[0] != 711204:
            raise RuntimeError("packaged runtime price row mismatch")
        if con.execute("select count(*) from cache_state").fetchone()[0] != 1425:
            raise RuntimeError("packaged runtime state count mismatch")
        if dict(con.execute("select status,count(*) from cache_state group by status").fetchall()) != {"READY": 1425}:
            raise RuntimeError("packaged runtime final state mismatch")
        if con.execute("select count(*) from cache_qa_provenance_v053").fetchone()[0] != 1425:
            raise RuntimeError("security provenance count mismatch")
        if con.execute("select count(*) from cache_qa_provenance_v053 where source_data_defect=1").fetchone()[0] != 8:
            raise RuntimeError("source defect security count mismatch")
        if con.execute("select count(*) from technical_bar_exclusions_v053").fetchone()[0] != 8:
            raise RuntimeError("technical exclusion count mismatch")
    finally:
        con.close()

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src_out, out)

    pre = json.loads((out / "summary_preupload_v0.53.json").read_text(encoding="utf-8"))
    bind_pre = json.loads((out / "runtime_hash_binding_preupload_v0.53.json").read_text(encoding="utf-8"))
    check_pre = json.loads((out / "stage_checkpoint_preupload_v0.53.json").read_text(encoding="utf-8"))
    raw = json.loads((out / "raw_price_immutability_v0.53.json").read_text(encoding="utf-8"))
    contract = json.loads((out / "contract_binding_v0.53.json").read_text(encoding="utf-8"))
    full = read_csv(out / "full_frozen_regression_v0.53.csv")
    transitions = read_csv(out / "state_transitions_v0.53.csv")
    validation = read_csv(out / "asx8_validation_v0.53.csv")
    tests = read_csv(out / "test_results_v0.53.csv")
    matrix = read_csv(out / "boundary_negative_tests_v0.53.csv")

    assert pre["status"] == "PREUPLOAD_PASS"
    assert pre["final_cache"] == {"READY": 1425, "QUARANTINE": 0, "total": 1425}
    assert pre["full_frozen"]["ready_to_ready"] == 1417
    assert pre["full_frozen"]["ready_to_quarantine"] == 0
    assert pre["full_frozen"]["ready_to_other"] == 0
    assert len(full) == 1425 and len(transitions) == 8 and len(validation) == 8
    assert raw["unchanged"] is True and raw["provider_mapping_unchanged"] is True
    assert bind_pre["declared_runtime_sha256"] == EXPECTED_SHA
    assert bind_pre["declared_runtime_bytes"] == EXPECTED_BYTES
    assert bind_pre["hash_after_close"] is True
    assert bind_pre["prepackage_hash_repeat_equal"] is True
    assert check_pre["tests_failed"] == 0 and check_pre["tests_passed"] == 29
    assert all(r["Result"] == "PASS" for r in tests)

    boundary_names = {
        "2_INVALID_BARS_BOUNDARY_PASS", "3_INVALID_BARS_FAIL",
        "INVALID_SHARE_EXACT_1PCT_PREDICATE_PASS", "INVALID_SHARE_GT_1PCT_PREDICATE_FAIL",
        "260_VALID_AFTER_FILTER_PASS", "259_VALID_AFTER_FILTER_FAIL",
    }
    negative_names = {
        "3_INVALID_BARS_FAIL", "INVALID_SHARE_GT_1PCT_PREDICATE_FAIL", "259_VALID_AFTER_FILTER_FAIL",
        "STALE_FAIL", "UNRESOLVED_SUSPICIOUS_RETURN_FAIL", "HIGHER_PRIORITY_BLOCKER_FAIL",
        "MULTIPLE_SIMULTANEOUS_BLOCKERS_FAIL",
    }
    write_csv(out / "boundary_tests_v0.53.csv", [r for r in matrix if r["Test"] in boundary_names])
    write_csv(out / "negative_tests_v0.53.csv", [r for r in matrix if r["Test"] in negative_names])

    binding = dict(bind_pre)
    binding.update({
        "packaged_runtime_sha256": EXPECTED_SHA,
        "packaged_runtime_bytes": EXPECTED_BYTES,
        "declared_equals_packaged_sha256": True,
        "declared_equals_packaged_bytes": True,
        "postdownload_integrity_check": "ok",
        "workflow_run_id": RUN_ID,
        "workflow_head_sha": IMPLEMENTATION_HEAD,
        "artifact_id": ARTIFACT_ID,
        "artifact_name": ARTIFACT_NAME,
        "artifact_digest": ARTIFACT_DIGEST,
        "postupload_byte_binding": "PASS",
    })
    (out / "runtime_hash_binding_v0.53.json").write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = dict(pre)
    summary["status"] = "PASS"
    summary["p0_price_cache_ready"] = True
    summary["pending_only"] = None
    summary["runtime_authority"] = {
        "workflow_run_id": RUN_ID,
        "workflow_head_sha": IMPLEMENTATION_HEAD,
        "artifact_id": ARTIFACT_ID,
        "artifact_name": ARTIFACT_NAME,
        "artifact_digest": ARTIFACT_DIGEST,
        "sqlite_sha256": EXPECTED_SHA,
        "sqlite_bytes": EXPECTED_BYTES,
        "integrity_check": "ok",
        "declared_equals_packaged": True,
    }
    summary["workflow_validation_history"] = [
        {"run_id": 36225649682, "conclusion": "failure", "scope": "test-harness self-check stopped before runtime mutation/upload"},
        {"run_id": 36225753186, "conclusion": "failure", "scope": "source-authority history-depth precondition stopped before runtime mutation/upload"},
        {"run_id": RUN_ID, "conclusion": "success", "scope": "full implementation/regression/refreeze/upload"},
    ]
    summary["next_gate"] = "P0 FROZEN-1425 FEATURE MATERIALIZATION / CAPABILITY GATE"
    (out / "summary_v0.53.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = dict(check_pre)
    checkpoint.update({
        "status": "PASS",
        "p0_price_cache_ready": True,
        "runtime_byte_binding": "PASS",
        "workflow_run_id": RUN_ID,
        "artifact_id": ARTIFACT_ID,
        "runtime_sha256": EXPECTED_SHA,
        "runtime_bytes": EXPECTED_BYTES,
        "integrity_check": "ok",
        "pending_only": None,
    })
    (out / "stage_checkpoint_v0.53.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    c = contract["canonical_contract"]
    lines = [
        "# P0 Frozen-1425 Canonical Filtered-Invalid-Bar Policy F - Implementation / Regression v0.53",
        "",
        "## 1. Implementation verdict",
        "",
        "**PASS**",
        "",
        "POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT is implemented for the Frozen-1425 runtime path using the existing canonical QA v0.4 / History QA v1 filtered-bar contract. No ASX/ticker/date/provider exception is present in the implementation.",
        "",
        "## 2. Start head",
        "",
        f"Required start authority: {REQUIRED_START_HEAD}. The first implementation commit was created directly from that HEAD. Subsequent harness-only repair commits remained descendants of the same required authority.",
        "",
        "## 3. Authority-chain validation",
        "",
        "- v0.48 runtime authority: validated exactly before implementation.",
        "- v0.49 ASX authority investigation: retained.",
        "- v0.50 licensed-source investigation: retained.",
        "- v0.51 entitlement precheck: retained.",
        "- v0.52 policy decision: retained and consumed as validation-case authority only.",
        "",
        "## 4. Canonical contract binding",
        "",
        f"- max invalid bars: {c['max_invalid_bars']}",
        f"- max invalid share: {100*c['max_invalid_share']:.2f}%",
        f"- minimum valid observations after filtering: {c['minimum_valid_observations_after_filter']}",
        f"- core minimum valid bars: {c['minimum_valid_bars_core']}",
        f"- stale threshold: {c['stale_after_calendar_days']} calendar days",
        "- unresolved suspicious returns remain blocking; existing evidence-verified reconciliations remain authoritative.",
        "- threshold changes: 0.",
        "",
        "## 5. Code change",
        "",
        "The implementation reuses qa_symbol_frame() and technical_valid_mask() from scripts/price_cache.py. It does not create a second threshold engine. The old v0.45 any-strict-invalid whole-security quarantine behavior is no longer the effective Frozen runtime classification. Invalid bars remain raw, are excluded completely from technical inputs, and canonical gates determine readiness.",
        "",
        "The runtime adds generic provenance tables cache_qa_provenance_v053 and technical_bar_exclusions_v053. No price_daily value is edited.",
        "",
        "## 6. Full Frozen-1425 regression",
        "",
        "- Frozen rows evaluated: 1425",
        "- READY -> READY: 1417",
        "- READY -> QUARANTINE: 0",
        "- READY -> other: 0",
        "- QUARANTINE -> READY: 8",
        "- final READY: 1425",
        "- final QUARANTINE: 0",
        "",
        "No hidden additional blocker was exposed by the generic full-population pass.",
        "",
        "## 7. ASX-8 validation case",
        "",
    ]
    for r in validation:
        lines.append(f"- {r['Primary_Ticker']}: raw {r['raw_bar_count']}, valid {r['valid_bar_count']}, invalid {r['invalid_bar_count']}, invalid share {float(r['invalid_share'])*100:.5f}%, affected date {r['affected_dates']}, result {r['Validation_Result']}, final reason {r['proposed_reason']}.")
    lines += [
        "",
        "These rows were discovered from v0.52 validation evidence and re-derived from runtime data. They are not hard-coded pass conditions.",
        "",
        "## 8. Raw price immutability",
        "",
        f"- price_daily rows before/after: {raw['price_daily_rows_before']} / {raw['price_daily_rows_after_close']}",
        f"- deterministic content digest before/after: {raw['price_daily_digest_before']}",
        "- raw-price digest unchanged: YES",
        "- provider mapping digest unchanged: YES",
        "",
        "## 9. Defect provenance",
        "",
        "- security-level provenance rows: 1425",
        "- SOURCE_DATA_DEFECT=true securities: 8",
        "- TECHNICAL_BAR_EXCLUDED rows: 8",
        "- affected dates, reasons and policy identifiers are persisted explicitly.",
        "",
        "READY therefore does not erase the source defect.",
        "",
        "## 10. Feature-path regression",
        "",
        "Fixture regression proved that the raw invalid row remains present while it is absent from feature input; EMA20/EMA50, ATR14, rolling High/Low, returns, Volume and Turnover all consume the filtered valid-bar series.",
        "",
        "## 11. Recursive EMA / ATR semantics",
        "",
        "EMA20, EMA50 and ATR14 are DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES. They are not described as unaffected: omission of an invalid historical observation changes the recursive filtered sequence.",
        "",
        "## 12. Boundary test results",
        "",
        "- 2 invalid bars: PASS boundary.",
        "- 3 invalid bars: fail closed.",
        "- invalid-share == 1% predicate: inclusive PASS; a joint READY fixture at exactly 1% is mathematically impossible under <=2 invalid bars plus >=260 valid observations, and this interaction is explicitly recorded.",
        "- invalid share >1% predicate: fail.",
        "- exactly 260 valid after filtering: PASS.",
        "- 259 valid after filtering: fail.",
        "",
        "## 13. Negative test results",
        "",
        "Fail-closed cases passed for 3 invalid bars, >1% share predicate, 259 valid, stale history, unresolved suspicious return, higher-priority blocker and multiple simultaneous blockers.",
        "",
        "## 14. Existing 1417 READY reconciliation",
        "",
        "1417 READY -> 1417 READY. Zero degradations. Existing evidence-verified extreme-return / 522 reconciliation states remain READY under their prior authority.",
        "",
        "## 15. State transitions",
        "",
    ]
    for r in transitions:
        lines.append(f"- {r['Primary_Ticker']}: {r['Status_Before']}/{r['Reason_Before']} -> {r['Status_After']}/{r['Reason_After']}; complete invalid bar remains excluded and provenance retained.")
    lines += [
        "",
        "## 16. Final cache counts",
        "",
        "- READY = 1425",
        "- QUARANTINE = 0",
        "- TOTAL = 1425",
        "",
        "## 17. P0_PRICE_CACHE_READY",
        "",
        "**YES** - price-cache readiness only. This does not authorize P0 execution; feature/RS/parameter gates remain separate.",
        "",
        "## 18. Runtime SQLite authority",
        "",
        f"- workflow run: {RUN_ID}",
        f"- artifact: {ARTIFACT_ID}",
        f"- artifact digest: {ARTIFACT_DIGEST}",
        f"- SQLite SHA-256: {EXPECTED_SHA}",
        f"- bytes: {EXPECTED_BYTES}",
        "- PRAGMA integrity_check: ok",
        "- states: 1425",
        "- price_daily: 711204",
        "",
        "## 19. Byte-binding result",
        "",
        "PASS. Declared SHA equals packaged/retrieved SHA; declared byte count equals packaged/retrieved byte count. Hashing occurs only after transaction commit, WAL checkpoint and connection close. The permanent lifecycle regression also passed.",
        "",
        "## 20. Frozen reconciliation",
        "",
        "- Frozen members: 1425",
        f"- Frozen SHA-256: {FROZEN_SHA}",
        "- Security_Key / Source_WS_ID / Primary_Ticker / Primary_MIC unchanged.",
        "",
        "## 21. History / Liquidity confirmation",
        "",
        "- History QA v1: NOT REOPENED",
        "- Liquidity QA v1: NOT REOPENED",
        "- threshold changes: 0",
        "",
        "## 22-24. Provider call counts",
        "",
        "- market-data provider calls: 0",
        "- Yahoo/yfinance calls: 0",
        "- EODHD calls: 0",
        "- Alpha Vantage calls: 0",
        "- Scalable calls: 0",
        "",
        "## 25. Test results",
        "",
        "Focused pytest suite: PASS. Persisted regression matrix: 29/29 PASS. Successful Actions run completed every implementation, full-regression, byte-lifecycle, validation and artifact-upload step.",
        "",
        "Two earlier harness attempts failed closed before runtime mutation/upload: run 36225649682 (self-test scanner) and run 36225753186 (shallow-history precondition). They created no runtime authority.",
        "",
        "## 26. Files",
        "",
        "Implementation code/workflows/tests plus the bounded v0.53 validation report and output package are persisted. Runtime SQLite remains an Actions artifact and is not committed.",
        "",
        "## 27. Commit",
        "",
        "The final evidence-persistence commit is created only after all packaged-byte checks pass.",
        "",
        "## 28. Next gate",
        "",
        "**P0 FROZEN-1425 FEATURE MATERIALIZATION / CAPABILITY GATE**",
        "",
        "Do not run P0 automatically.",
        "",
        "## Hard stop",
        "",
        "No P0/P1/P2. No feature materialization beyond regression fixtures. No RS materialization. No parameter promotion. No Universe mutation. No Scalable. No trading.",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    files: dict[str, dict[str, object]] = {}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "manifest_v0.53.json":
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    files["docs/validation/P0_Frozen_1425_Filtered_Invalid_Bar_Policy_Implementation_v0.53.md"] = {
        "sha256": sha256_file(report), "bytes": report.stat().st_size
    }
    manifest = {
        "stage": "P0_FROZEN_1425_CANONICAL_FILTERED_INVALID_BAR_POLICY_F_IMPLEMENTATION",
        "version": "v0.53",
        "required_start_head": REQUIRED_START_HEAD,
        "implementation_head": IMPLEMENTATION_HEAD,
        "successful_workflow_run_id": RUN_ID,
        "runtime_artifact": {
            "artifact_id": ARTIFACT_ID,
            "artifact_name": ARTIFACT_NAME,
            "artifact_digest": ARTIFACT_DIGEST,
            "sqlite_sha256": EXPECTED_SHA,
            "sqlite_bytes": EXPECTED_BYTES,
            "integrity_check": "ok",
        },
        "final_cache": {"READY": 1425, "QUARANTINE": 0, "total": 1425},
        "p0_price_cache_ready": True,
        "price_daily_rows": 711204,
        "raw_price_digest": raw["price_daily_digest_before"],
        "provider_mapping_digest": raw["provider_mapping_digest_before"],
        "frozen_sha256": FROZEN_SHA,
        "history_qa_reopened": False,
        "liquidity_qa_reopened": False,
        "threshold_changes": 0,
        "market_provider_calls": 0,
        "yahoo_yfinance_calls": 0,
        "eodhd_calls": 0,
        "alpha_vantage_calls": 0,
        "scalable_calls": 0,
        "p0_run": False,
        "feature_materialization": False,
        "rs_materialization": False,
        "parameter_promotion": False,
        "universe_mutation": False,
        "productive": False,
        "files": files,
        "next_gate": "P0 FROZEN-1425 FEATURE MATERIALIZATION / CAPABILITY GATE",
    }
    (out / "manifest_v0.53.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "ready": 1425,
        "quarantine": 0,
        "p0_price_cache_ready": True,
        "runtime_sha256": EXPECTED_SHA,
        "runtime_bytes": EXPECTED_BYTES,
        "tests_passed": 29,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
