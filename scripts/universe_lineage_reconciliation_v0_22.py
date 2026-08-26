#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = "WELT_SWING_UNIVERSE_LINEAGE_RECONCILIATION_V0_22"
CHECKPOINT_SCHEMA = "WELT_SWING_STAGE_CHECKPOINT_V0_22"

P0_RUN = False
P0_LANE_DECISIONS = False
P0_SURVIVORS = 0
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
EXTERNAL_REQUESTS = 0
WEB_CALLS_PER_SECURITY = False
PRICE_DOWNLOADS_PERFORMED = False
SECTOR_RS_PERFORMED = False
CANONICAL_MASTER_MUTATED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items: dict[str, str]) -> str:
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_unique_ws_id(df: pd.DataFrame, name: str) -> None:
    require("WS_ID" in df.columns, f"{name} missing WS_ID")
    require(not df["WS_ID"].astype(str).duplicated().any(), f"{name} contains duplicate WS_ID")


def require_segment(df: pd.DataFrame, name: str) -> None:
    require("Primary_Universe_Index" in df.columns, f"{name} missing Primary_Universe_Index")


def stable_counts(df: pd.DataFrame, segment_col: str = "Primary_Universe_Index") -> dict[str, int]:
    return {str(k): int(v) for k, v in df.groupby(segment_col).size().sort_index().items()}


def self_test() -> None:
    assert P0_RUN is False
    assert P0_LANE_DECISIONS is False
    assert P0_SURVIVORS == 0
    assert PRODUCTIVE_TRADING_AUTHORITY is False
    assert ALPHA_VANTAGE_ALLOWED is False
    assert EXTERNAL_REQUESTS == 0
    assert PRICE_DOWNLOADS_PERFORMED is False
    print("UNIVERSE_LINEAGE_RECONCILIATION_V0_22_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict:
    started = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    paths = {k: Path(v) for k, v in cfg["inputs"].items()}

    # ---- Read frozen evidence -------------------------------------------------
    phase2_manifest = read_json(paths["phase2_manifest"])
    full_price_manifest = read_json(paths["full_price_manifest"])
    v016_summary = read_json(paths["v016_summary"])
    v016_manifest = read_json(paths["v016_manifest"])
    v021_summary = read_json(paths["v021_summary"])

    active = read_csv(paths["full_price_universe"])
    full_elig = read_csv(paths["v014_full_eligibility"])
    strict = read_csv(paths["v014_strict_candidates"])
    unresolved = read_csv(paths["v015_manual_queue"])
    partial = read_csv(paths["v016_research_partial"])
    v016_coverage = read_csv(paths["v016_coverage"])

    # ---- Frozen stage/schema gates -------------------------------------------
    require(
        phase2_manifest.get("schema") == "WELT_SWING_UNIVERSE_PHASE2_SOURCE_SUPERSET_V0_3",
        "Wrong Phase2 manifest schema",
    )
    require(phase2_manifest.get("status") == "COMPLETE_SOURCE_SUPERSET", "Phase2 source superset is not complete")
    require(phase2_manifest.get("missing_segments") == [], "Phase2 source superset has missing segments")

    require(
        full_price_manifest.get("schema") == "WELT_SWING_FULL_PRICE_UNIVERSE_3663_V0_1",
        "Wrong full-price universe manifest schema",
    )
    require(v016_summary.get("run_status") == "RESEARCH_PARTIAL_SNAPSHOT_V0_16_FROZEN", "Unexpected v0.16 status")
    require(v016_manifest.get("mode") == "RESEARCH_PARTIAL", "v0.16 is not RESEARCH_PARTIAL")
    require(v016_manifest.get("full_scan_claim") is False, "v0.16 unexpectedly claims full scan")
    require(
        v021_summary.get("run_status")
        == "P0_LANE_PARAMETER_SHADOW_VALIDATION_V0_21_COMPLETE_WITH_SECTOR_RS_BLOCK",
        "Unexpected v0.21 status",
    )

    # Governance.
    for label, obj in [
        ("phase2", phase2_manifest),
        ("full_price", full_price_manifest),
        ("v0.16", v016_manifest),
        ("v0.21", v021_summary),
    ]:
        require(obj.get("productive_trading_authority") is False, f"{label} productive authority gate failed")
        require(obj.get("alpha_vantage_allowed") is False, f"{label} Alpha Vantage gate failed")

    # ---- Hash gates on core frozen CSV evidence ------------------------------
    for key, expected in cfg["expected_sha256"].items():
        actual = sha256_file(paths[key])
        require(actual == expected, f"SHA256 mismatch for {key}: {actual} != {expected}")

    # ---- Identity / set invariants -------------------------------------------
    for name, df in [
        ("full_price_universe", active),
        ("v0.14_full_eligibility", full_elig),
        ("v0.14_strict_candidates", strict),
        ("v0.15_manual_queue", unresolved),
        ("v0.16_research_partial", partial),
    ]:
        require_unique_ws_id(df, name)
        require_segment(df, name)

    expected = cfg["expected_counts"]
    require(len(active) == int(expected["active_source_rows"]), "Unexpected active source count")
    require(len(full_elig) == int(expected["full_eligibility_rows"]), "Unexpected full eligibility count")
    require(len(strict) == int(expected["strict_rows"]), "Unexpected strict count")
    require(len(unresolved) == int(expected["unresolved_rows"]), "Unexpected unresolved count")
    require(len(partial) == int(expected["research_partial_rows"]), "Unexpected research partial count")

    active_ids = set(active["WS_ID"].astype(str))
    full_ids = set(full_elig["WS_ID"].astype(str))
    strict_ids = set(strict["WS_ID"].astype(str))
    unresolved_ids = set(unresolved["WS_ID"].astype(str))
    partial_ids = set(partial["WS_ID"].astype(str))

    require(full_ids.issubset(active_ids), "v0.14 full eligibility is not a subset of the active source universe")
    require(strict_ids.issubset(full_ids), "Strict rows are not a subset of v0.14 full eligibility")
    require(unresolved_ids.issubset(full_ids), "Unresolved rows are not a subset of v0.14 full eligibility")
    require(strict_ids.isdisjoint(unresolved_ids), "Strict and unresolved sets overlap")
    require(partial_ids == strict_ids, "v0.16 research partial does not exactly equal the v0.14 strict set")

    absent_from_full_ids = active_ids - full_ids
    other_non_strict_ids = full_ids - strict_ids - unresolved_ids

    require(
        len(absent_from_full_ids) == int(expected["active_absent_from_full_eligibility"]),
        "Unexpected active rows absent from v0.14 full eligibility",
    )
    require(
        len(other_non_strict_ids) == int(expected["other_non_strict_rows"]),
        "Unexpected other-non-strict count",
    )
    require(
        len(strict_ids | unresolved_ids | other_non_strict_ids | absent_from_full_ids) == len(active_ids),
        "Lineage partition does not cover the active source universe",
    )

    # ---- Row-level lineage classification ------------------------------------
    active_base = active[["WS_ID", "Primary_Universe_Index"]].copy()
    optional_cols = [
        c for c in ["Name", "Company_Name", "Ticker", "Yahoo_Symbol", "MIC", "Country", "Currency"]
        if c in active.columns
    ]
    if optional_cols:
        active_base = active[["WS_ID", "Primary_Universe_Index"] + optional_cols].copy()

    def classify(ws_id: str) -> str:
        if ws_id in strict_ids:
            return "INCLUDED_RESEARCH_PARTIAL_VERIFIED_STRICT"
        if ws_id in unresolved_ids:
            return "EXCLUDED_INSTRUMENT_TYPE_NOT_YET_STRICTLY_VERIFIED"
        if ws_id in other_non_strict_ids:
            return "EXCLUDED_OTHER_NON_STRICT_REASON_NOT_CLASSIFIED_V0_22"
        if ws_id in absent_from_full_ids:
            return "ABSENT_FROM_V0_14_FULL_ELIGIBILITY_REASON_NOT_CLASSIFIED_V0_22"
        return "LINEAGE_ERROR"

    active_base["Lineage_Class_v0_22"] = active_base["WS_ID"].astype(str).map(classify)
    active_base["In_Active_Source_v0_22"] = True
    active_base["In_Full_Eligibility_v0_14"] = active_base["WS_ID"].astype(str).isin(full_ids)
    active_base["In_Strict_v0_14"] = active_base["WS_ID"].astype(str).isin(strict_ids)
    active_base["In_Unresolved_Queue_v0_15"] = active_base["WS_ID"].astype(str).isin(unresolved_ids)
    active_base["In_Research_Partial_v0_16"] = active_base["WS_ID"].astype(str).isin(partial_ids)
    active_base = active_base.sort_values(["Primary_Universe_Index", "WS_ID"], kind="mergesort")
    row_path = out / "universe_lineage_row_reconciliation_v0.22.csv"
    active_base.to_csv(row_path, index=False)

    # ---- Segment-level reconciliation ----------------------------------------
    segs = sorted(set(active["Primary_Universe_Index"].astype(str)))
    rows = []
    phase2_counts = {str(k): int(v) for k, v in phase2_manifest["segment_counts"].items()}
    active_counts = stable_counts(active)
    full_counts = stable_counts(full_elig)
    strict_counts = stable_counts(strict)
    unresolved_counts = stable_counts(unresolved)

    # v0.21 uses 2,036 synchronized rows; one strict row (WBS) is fail-closed at AsOf.
    # We only assert the global v0.21 count here; per-segment P0 sync is inherited from v0.20.
    for seg in segs:
        a = active_counts.get(seg, 0)
        f = full_counts.get(seg, 0)
        s = strict_counts.get(seg, 0)
        u = unresolved_counts.get(seg, 0)
        other = f - s - u
        absent = a - f
        require(other >= 0, f"Negative other-non-strict count for {seg}")
        require(absent >= 0, f"Negative active-to-full gap for {seg}")

        rows.append(
            {
                "Primary_Universe_Index": seg,
                "Phase2_Source_Rows": phase2_counts.get(seg, 0),
                "Active_Source_Rows": a,
                "Full_Eligibility_Rows_v0_14": f,
                "Research_Partial_Strict_Rows_v0_16": s,
                "Instrument_Unresolved_Rows_v0_15": u,
                "Other_NonStrict_Rows": other,
                "Active_Absent_From_Full_Eligibility": absent,
                "Research_Partial_Coverage_Pct_of_Active": round((s / a * 100.0) if a else 0.0, 4),
                "Lineage_Accounting_OK": (s + u + other + absent == a),
                "Global_P0_Coverage_Gate_v0_22": "BLOCKED" if s < a else "COMPLETE",
            }
        )

    seg_df = pd.DataFrame(rows)
    seg_path = out / "universe_lineage_segment_reconciliation_v0.22.csv"
    seg_df.to_csv(seg_path, index=False)

    # Cross-check against the historical v0.16 segment evidence.
    hist = v016_coverage.copy()
    hist_cols = {
        "Full_Eligibility_Rows": "Full_Eligibility_Rows_v0_14",
        "Included_Strict_Rows": "Research_Partial_Strict_Rows_v0_16",
        "Unresolved_Instrument_Rows": "Instrument_Unresolved_Rows_v0_15",
        "Other_NonStrict_Rows": "Other_NonStrict_Rows",
    }
    hist = hist.rename(columns=hist_cols)
    check = seg_df.merge(
        hist[["Primary_Universe_Index"] + list(hist_cols.values())],
        on="Primary_Universe_Index",
        how="outer",
        suffixes=("_recomputed", "_historical"),
        indicator=True,
    )
    require((check["_merge"] == "both").all(), "Segment set differs from frozen v0.16 coverage")
    for col in hist_cols.values():
        require(
            pd.to_numeric(check[f"{col}_recomputed"]).equals(pd.to_numeric(check[f"{col}_historical"])),
            f"Historical v0.16 coverage mismatch in {col}",
        )

    # ---- Explicit regional audit ---------------------------------------------
    def regional(seg: str) -> dict:
        r = seg_df.loc[seg_df["Primary_Universe_Index"].eq(seg)]
        require(len(r) == 1, f"Missing segment {seg}")
        x = r.iloc[0]
        return {
            "segment": seg,
            "active_source_rows": int(x["Active_Source_Rows"]),
            "full_eligibility_rows": int(x["Full_Eligibility_Rows_v0_14"]),
            "research_partial_strict_rows": int(x["Research_Partial_Strict_Rows_v0_16"]),
            "instrument_unresolved_rows": int(x["Instrument_Unresolved_Rows_v0_15"]),
            "other_non_strict_rows": int(x["Other_NonStrict_Rows"]),
            "active_absent_from_full_eligibility": int(x["Active_Absent_From_Full_Eligibility"]),
            "research_partial_coverage_pct_of_active": float(x["Research_Partial_Coverage_Pct_of_Active"]),
        }

    eu = regional("EU_STOXX600")
    us = regional("US_SP1500")
    require(eu["active_source_rows"] == 600, "EU active source count changed")
    require(eu["research_partial_strict_rows"] == 0, "EU unexpectedly entered frozen v0.16 partial")
    require(eu["instrument_unresolved_rows"] == 365, "EU unresolved count changed")
    require(eu["other_non_strict_rows"] == 235, "EU other non-strict count changed")
    require(us["active_source_rows"] == 1506, "US active source count changed")
    require(us["research_partial_strict_rows"] == 1332, "US strict count changed")
    require(us["instrument_unresolved_rows"] == 0, "US unresolved count changed")

    # ---- Gap classification ---------------------------------------------------
    gaps = []
    for _, r in seg_df.iterrows():
        seg = str(r["Primary_Universe_Index"])
        if int(r["Instrument_Unresolved_Rows_v0_15"]) > 0:
            gaps.append({
                "Primary_Universe_Index": seg,
                "Gap_Class": "INSTRUMENT_TYPE_NOT_YET_STRICTLY_VERIFIED",
                "Rows": int(r["Instrument_Unresolved_Rows_v0_15"]),
                "Evidence_Level": "VERIFIED_FROM_V0_15_QUEUE",
                "Remediation_v0_22": "NOT_PERFORMED",
            })
        if int(r["Other_NonStrict_Rows"]) > 0:
            gaps.append({
                "Primary_Universe_Index": seg,
                "Gap_Class": "OTHER_NON_STRICT_REASON_NOT_CLASSIFIED_V0_22",
                "Rows": int(r["Other_NonStrict_Rows"]),
                "Evidence_Level": "VERIFIED_SET_DIFFERENCE_REASON_NOT_ATTRIBUTED",
                "Remediation_v0_22": "NOT_PERFORMED",
            })
        if int(r["Active_Absent_From_Full_Eligibility"]) > 0:
            gaps.append({
                "Primary_Universe_Index": seg,
                "Gap_Class": "ACTIVE_SOURCE_ROW_ABSENT_FROM_V0_14_FULL_ELIGIBILITY",
                "Rows": int(r["Active_Absent_From_Full_Eligibility"]),
                "Evidence_Level": "VERIFIED_SET_DIFFERENCE_REASON_NOT_ATTRIBUTED",
                "Remediation_v0_22": "NOT_PERFORMED",
            })

    gap_df = pd.DataFrame(gaps).sort_values(
        ["Rows", "Primary_Universe_Index", "Gap_Class"],
        ascending=[False, True, True],
        kind="mergesort",
    )
    gap_path = out / "universe_gap_classification_v0.22.csv"
    gap_df.to_csv(gap_path, index=False)

    # ---- Stage chain registry -------------------------------------------------
    stage_chain = {
        "schema": "WELT_SWING_UNIVERSE_LINEAGE_SOURCE_REGISTRY_V0_22",
        "generated_utc": now_utc(),
        "stages": [
            {
                "stage": "PHASE2_SOURCE_SUPERSET",
                "rows": int(phase2_manifest["deduplicated_rows"]),
                "segments": len(phase2_manifest["segments_present"]),
                "status": phase2_manifest["status"],
                "file": str(paths["phase2_manifest"]),
            },
            {
                "stage": "ACTIVE_FULL_PRICE_UNIVERSE",
                "rows": int(full_price_manifest["active_rows"]),
                "segments": len(full_price_manifest["segments"]),
                "status": "ACTIVE_SOURCE_UNIVERSE",
                "file": str(paths["full_price_universe"]),
            },
            {
                "stage": "V0_14_FULL_ELIGIBILITY",
                "rows": len(full_elig),
                "segments": int(full_elig["Primary_Universe_Index"].nunique()),
                "status": "FROZEN_HISTORICAL_ELIGIBILITY_INPUT",
                "file": str(paths["v014_full_eligibility"]),
            },
            {
                "stage": "V0_16_RESEARCH_PARTIAL_STRICT",
                "rows": len(partial),
                "segments": int(partial["Primary_Universe_Index"].nunique()),
                "status": v016_summary["run_status"],
                "file": str(paths["v016_research_partial"]),
            },
            {
                "stage": "V0_21_P0_SHADOW_INPUT",
                "rows": int(v021_summary["input_rows"]),
                "synchronized_rows": int(v021_summary["asof_synchronized_rows"]),
                "status": v021_summary["run_status"],
                "file": str(paths["v021_summary"]),
            },
        ],
        "lineage_conclusion": (
            "The canonical source universe already contains Europe and the US. "
            "Europe is absent from the frozen 2,037-row research/P0 path because none of its 600 active rows "
            "was in the verified strict subset at v0.16; 365 were explicitly instrument-unresolved and "
            "235 were other non-strict rows whose exact reason is not attributed by v0.22. "
            "US has 1,506 active source rows and 1,332 verified strict rows at v0.16; "
            "v0.21 has 2,036 synchronized rows globally because WS:US:WBS remains the one AsOf mismatch."
        ),
        "policy": [
            "No source universe is mutated by v0.22.",
            "No gap reason is inferred beyond frozen evidence.",
            "OTHER_NON_STRICT remains reason-not-attributed until a dedicated root-cause audit.",
            "No price download, Sector RS, P0 decision, threshold promotion or trading decision is performed.",
        ],
    }
    registry_path = out / "lineage_source_registry_v0.22.json"
    registry_path.write_text(json.dumps(stage_chain, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- Summary and checkpoint ----------------------------------------------
    research_coverage = round(len(partial) / len(active) * 100.0, 4)
    global_gate = "BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT"

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "UNIVERSE_LINEAGE_RECONCILIATION_V0_22_COMPLETE",
        "source_superset_rows": int(phase2_manifest["deduplicated_rows"]),
        "active_source_rows": len(active),
        "full_eligibility_rows_v0_14": len(full_elig),
        "research_partial_rows_v0_16": len(partial),
        "research_partial_coverage_pct_of_active": research_coverage,
        "instrument_unresolved_rows_v0_15": len(unresolved),
        "other_non_strict_rows": len(other_non_strict_ids),
        "active_absent_from_full_eligibility_rows": len(absent_from_full_ids),
        "segments_in_active_source": int(active["Primary_Universe_Index"].nunique()),
        "segments_in_research_partial": int(partial["Primary_Universe_Index"].nunique()),
        "eu_stoxx600": eu,
        "us_sp1500": us,
        "v0_21_input_rows": int(v021_summary["input_rows"]),
        "v0_21_asof_synchronized_rows": int(v021_summary["asof_synchronized_rows"]),
        "v0_21_asof_mismatch_ws_ids": v021_summary["asof_mismatch_ws_ids"],
        "global_p0_coverage_gate": global_gate,
        "lineage_accounting_complete": True,
        "unattributed_gap_reason_rows": len(other_non_strict_ids) + len(absent_from_full_ids),
        "p0_run": P0_RUN,
        "p0_lane_decisions_made": P0_LANE_DECISIONS,
        "p0_survivor_rows": P0_SURVIVORS,
        "sector_rs_performed": SECTOR_RS_PERFORMED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "external_requests": EXTERNAL_REQUESTS,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "next_stage": "UNIVERSE_GAP_ROOT_CAUSE_AUDIT_AND_REMEDIATION_PLAN",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
    }
    summary_path = out / "summary_v0.22.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in paths.items()}
    parameter_hash = sha256_file(cfg_path)

    evidence_files = {
        p.name: sha256_file(p)
        for p in [row_path, seg_path, gap_path, registry_path, summary_path]
    }
    output_hash = combined_hash(evidence_files)

    checkpoint = {
        "schema": CHECKPOINT_SCHEMA,
        "run_id": cfg["run_id"],
        "stage_id": "UNIVERSE_LINEAGE_RECONCILIATION_AND_COVERAGE_GATE",
        "stage_version": "v0.22",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": parameter_hash,
        "output_hash": output_hash,
        "input_count": len(active),
        "checked_count": len(active),
        "pass_count": len(active),
        "fail_count": 0,
        "data_error_count": 0,
        "quarantine_count": 0,
        "status": "SUCCESS",
        "failed_source": None,
        "coverage_gate_status": global_gate,
        "research_partial_count": len(partial),
        "next_stage": "UNIVERSE_GAP_ROOT_CAUSE_AUDIT_AND_REMEDIATION_PLAN",
    }
    checkpoint_path = out / "stage_checkpoint_v0.22.json"
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest_files = [row_path, seg_path, gap_path, registry_path, summary_path, checkpoint_path]
    manifest = {
        "schema": "WELT_SWING_UNIVERSE_LINEAGE_MANIFEST_V0_22",
        "generated_utc": now_utc(),
        "data_source": "FROZEN_REPOSITORY_EVIDENCE_ONLY",
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": parameter_hash,
        "evidence_output_hash": output_hash,
        "external_requests": 0,
        "alpha_vantage_allowed": False,
        "files": {
            p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in manifest_files
        },
    }
    manifest_path = out / "manifest_v0.22.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("UNIVERSE_LINEAGE_RECONCILIATION_V0_22_RESULT_GATES_PASS")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/universe_lineage_reconciliation_v0.22.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    run(Path(args.config))


if __name__ == "__main__":
    main()
