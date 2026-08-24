#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = "WELT_SWING_RESEARCH_PARTIAL_SNAPSHOT_V0_16"

P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
STRICT_U3K_FREEZE_ALLOWED = False
RESEARCH_PARTIAL_ALLOWED = True


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def txt(v) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def self_test() -> None:
    # RESEARCH_PARTIAL is not a SWING_U3K_FROZEN promotion.
    assert STRICT_U3K_FREEZE_ALLOWED is False
    assert RESEARCH_PARTIAL_ALLOWED is True
    assert P0_RUN is False
    print("RESEARCH_PARTIAL_SNAPSHOT_V0_16_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    summary15 = json.loads(Path(cfg["source_summary_v0_15"]).read_text(encoding="utf-8"))
    if summary15.get("schema") != "WELT_SWING_SP_TSX_SEMANTICS_REMEDIATION_V0_15":
        raise SystemExit("Wrong v0.15 source schema")
    if summary15.get("run_status") != "SP_TSX_SEMANTICS_REMEDIATION_V0_15_COMPLETE_WITH_SOURCE_BLOCK":
        raise SystemExit("Unexpected v0.15 run status")
    if int(summary15.get("strict_candidates_v0_15", -1)) != int(cfg["expected_strict_candidates"]):
        raise SystemExit("Unexpected v0.15 strict-candidate count")
    if int(summary15.get("remaining_manual_rows_v0_15", -1)) != int(cfg["expected_unresolved_instrument_rows"]):
        raise SystemExit("Unexpected v0.15 unresolved-instrument count")
    if summary15.get("p0_run") is not False or summary15.get("alpha_vantage_allowed") is not False:
        raise SystemExit("v0.15 governance gate failed")

    strict_path = Path(cfg["source_strict_candidates_v0_14"])
    full_path = Path(cfg["source_full_eligibility_v0_14"])
    unresolved_path = Path(cfg["source_manual_queue_v0_15"])

    strict = pd.read_csv(strict_path, keep_default_na=False, dtype=str)
    full = pd.read_csv(full_path, keep_default_na=False, dtype=str)
    unresolved = pd.read_csv(unresolved_path, keep_default_na=False, dtype=str)

    if len(strict) != int(cfg["expected_strict_candidates"]):
        raise SystemExit(f"Strict candidate rows {len(strict)} != expected")
    if len(unresolved) != int(cfg["expected_unresolved_instrument_rows"]):
        raise SystemExit(f"Unresolved rows {len(unresolved)} != expected")
    if len(full) != int(cfg["expected_full_eligibility_rows"]):
        raise SystemExit(f"Full eligibility rows {len(full)} != expected {cfg['expected_full_eligibility_rows']}")

    for name, df in [("strict", strict), ("full", full), ("unresolved", unresolved)]:
        if "WS_ID" not in df.columns:
            raise SystemExit(f"{name} missing WS_ID")
        if df["WS_ID"].duplicated().any():
            raise SystemExit(f"{name} contains duplicate WS_ID")

    strict_ids = set(strict["WS_ID"].astype(str))
    unresolved_ids = set(unresolved["WS_ID"].astype(str))
    full_ids = set(full["WS_ID"].astype(str))

    if not strict_ids.issubset(full_ids):
        raise SystemExit("Strict candidates are not a subset of full eligibility")
    if not unresolved_ids.issubset(full_ids):
        raise SystemExit("Unresolved queue is not a subset of full eligibility")
    if strict_ids & unresolved_ids:
        raise SystemExit("Strict and unresolved sets overlap")

    if "Strict_Eligibility_v0_14" in full.columns:
        strict_from_full = set(
            full.loc[full["Strict_Eligibility_v0_14"].astype(str).eq("PASS"), "WS_ID"].astype(str)
        )
        if strict_from_full != strict_ids:
            raise SystemExit("Strict candidate CSV does not equal PASS set in v0.14 full eligibility")

    # A RESEARCH_PARTIAL snapshot may contain only the verified strict subset.
    partial = strict.copy()

    # Stable ordering: preserve current strict rank if present, otherwise WS_ID.
    rank_cols = [c for c in partial.columns if c.startswith("Strict_Candidate_Rank")]
    if rank_cols:
        rc = rank_cols[0]
        partial["_rank_numeric"] = pd.to_numeric(partial[rc], errors="coerce")
        partial = partial.sort_values(["_rank_numeric", "WS_ID"], kind="mergesort").drop(columns=["_rank_numeric"])
    else:
        partial = partial.sort_values(["WS_ID"], kind="mergesort")

    partial.insert(0, "Research_Partial_Rank_v0_16", range(1, len(partial) + 1))
    partial["Research_Partial_Status_v0_16"] = "INCLUDED_VERIFIED_STRICT"
    partial["Research_Partial_AsOf_v0_16"] = cfg["as_of_date"]
    partial.to_csv(out / "research_partial_universe_v0.16.csv", index=False)

    unresolved_copy = unresolved.copy()
    unresolved_copy["Research_Partial_Exclusion_v0_16"] = "INSTRUMENT_TYPE_NOT_YET_STRICTLY_VERIFIED"
    unresolved_copy.to_csv(out / "missing_instrument_coverage_v0.16.csv", index=False)

    # Segment coverage: full rows, strict included, unresolved instrument rows,
    # and other non-strict rows that are gate-fail / not part of the partial scan.
    seg_col = "Primary_Universe_Index"
    full_seg = full.groupby(seg_col).size().rename("Full_Eligibility_Rows")
    strict_seg = partial.groupby(seg_col).size().rename("Included_Strict_Rows")
    unresolved_seg = unresolved.groupby(seg_col).size().rename("Unresolved_Instrument_Rows")

    coverage = (
        pd.concat([full_seg, strict_seg, unresolved_seg], axis=1)
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    coverage["Other_NonStrict_Rows"] = (
        coverage["Full_Eligibility_Rows"]
        - coverage["Included_Strict_Rows"]
        - coverage["Unresolved_Instrument_Rows"]
    )
    if (coverage["Other_NonStrict_Rows"] < 0).any():
        raise SystemExit("Negative Other_NonStrict_Rows in coverage arithmetic")

    coverage["Verified_Strict_Coverage_Pct_of_Full"] = (
        coverage["Included_Strict_Rows"] / coverage["Full_Eligibility_Rows"] * 100.0
    ).round(4)
    coverage["Instrument_Unresolved_Pct_of_Full"] = (
        coverage["Unresolved_Instrument_Rows"] / coverage["Full_Eligibility_Rows"] * 100.0
    ).round(4)
    coverage.to_csv(out / "coverage_by_segment_v0.16.csv", index=False)

    missing_segments = (
        unresolved.groupby(seg_col)
        .size()
        .reset_index(name="Rows")
        .sort_values(["Rows", seg_col], ascending=[False, True], kind="mergesort")
    )
    missing_segments.to_csv(out / "missing_segments_v0.16.csv", index=False)

    expected_other = int(cfg["expected_full_eligibility_rows"]) - int(cfg["expected_strict_candidates"]) - int(cfg["expected_unresolved_instrument_rows"])
    actual_other = int(len(full) - len(strict) - len(unresolved))
    if actual_other != expected_other:
        raise SystemExit("Full eligibility arithmetic mismatch")

    snapshot_manifest = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "snapshot_id": cfg["snapshot_id"],
        "mode": "RESEARCH_PARTIAL",
        "as_of_date": cfg["as_of_date"],
        "authority": "DEV_RESEARCH_SHADOW_NOT_PRODUCTIVE",
        "full_scan_claim": False,
        "strict_u3k_frozen": False,
        "research_partial_snapshot_frozen": True,
        "input_full_eligibility_rows": int(len(full)),
        "included_verified_strict_rows": int(len(partial)),
        "excluded_unresolved_instrument_rows": int(len(unresolved)),
        "other_non_strict_rows": int(actual_other),
        "verified_strict_coverage_pct_of_full": round(len(partial) / len(full) * 100.0, 4),
        "instrument_unresolved_pct_of_full": round(len(unresolved) / len(full) * 100.0, 4),
        "missing_segments": {
            str(r[seg_col]): int(r["Rows"])
            for _, r in missing_segments.iterrows()
        },
        "input_hashes_sha256": {
            "summary_v0_15": sha256_file(Path(cfg["source_summary_v0_15"])),
            "strict_candidates_v0_14": sha256_file(strict_path),
            "full_eligibility_v0_14": sha256_file(full_path),
            "manual_queue_v0_15": sha256_file(unresolved_path),
        },
        "output_hashes_sha256": {
            "research_partial_universe_v0.16.csv": sha256_file(out / "research_partial_universe_v0.16.csv"),
            "missing_instrument_coverage_v0.16.csv": sha256_file(out / "missing_instrument_coverage_v0.16.csv"),
            "coverage_by_segment_v0.16.csv": sha256_file(out / "coverage_by_segment_v0.16.csv"),
            "missing_segments_v0.16.csv": sha256_file(out / "missing_segments_v0.16.csv"),
        },
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "strict_u3k_freeze_allowed": STRICT_U3K_FREEZE_ALLOWED,
        "research_partial_allowed": RESEARCH_PARTIAL_ALLOWED,
        "next_stage": "P0_RESEARCH_PARTIAL_PARAMETER_FREEZE_AND_DRY_RUN",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
        "forbidden_result_wording": "weltweit bester Kandidat",
        "notes": [
            "This is not SWING_U3K_FROZEN and must never be presented as a complete global universe.",
            "The master specification explicitly permits RESEARCH_PARTIAL when a valid full Strict Universe is not available.",
            "The 650 instrument-unresolved rows remain outside this partial snapshot and remain NOT_VERIFIED.",
            "All 2,037 included rows are the currently verified strict subset carried from v0.14/v0.15.",
            "P0 is intentionally not run in v0.16; this stage only freezes the auditable partial input snapshot.",
        ],
    }
    (out / "snapshot_manifest_v0.16.json").write_text(
        json.dumps(snapshot_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_16",
        "run_id": cfg["snapshot_id"],
        "stage_id": "RESEARCH_PARTIAL_SNAPSHOT",
        "stage_version": "v0.16",
        "start": snapshot_manifest["generated_utc"],
        "end": now_utc(),
        "input_hash": hashlib.sha256(
            "|".join(snapshot_manifest["input_hashes_sha256"].values()).encode("utf-8")
        ).hexdigest(),
        "parameter_hash": hashlib.sha256(
            json.dumps(
                {
                    "mode": "RESEARCH_PARTIAL",
                    "strict_u3k_frozen": False,
                    "included_rule": "verified strict subset only",
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
        "output_hash": hashlib.sha256(
            "|".join(snapshot_manifest["output_hashes_sha256"].values()).encode("utf-8")
        ).hexdigest(),
        "input_count": int(len(full)),
        "checked_count": int(len(full)),
        "pass_count": int(len(partial)),
        "fail_count": int(actual_other),
        "data_error_count": 0,
        "quarantine_count": int(len(unresolved)),
        "status": "PARTIAL",
        "failed_source": "INSTRUMENT_RESOLUTION_BLOCKED_MARKETS",
        "next_stage": "P0_RESEARCH_PARTIAL_PARAMETER_FREEZE_AND_DRY_RUN",
    }
    (out / "stage_checkpoint_v0.16.json").write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "schema": "WELT_SWING_RESEARCH_PARTIAL_SNAPSHOT_SUMMARY_V0_16",
        "generated_utc": now_utc(),
        "run_status": "RESEARCH_PARTIAL_SNAPSHOT_V0_16_FROZEN",
        "full_eligibility_rows": int(len(full)),
        "included_verified_strict_rows": int(len(partial)),
        "unresolved_instrument_rows": int(len(unresolved)),
        "other_non_strict_rows": int(actual_other),
        "verified_strict_coverage_pct_of_full": round(len(partial) / len(full) * 100.0, 4),
        "strict_u3k_freeze_allowed": False,
        "research_partial_snapshot_frozen": True,
        "p0_run": False,
        "productive_trading_authority": False,
        "alpha_vantage_allowed": False,
        "next_stage": "P0_RESEARCH_PARTIAL_PARAMETER_FREEZE_AND_DRY_RUN",
    }
    (out / "summary_v0.16.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/research_partial_snapshot_v0.16.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
