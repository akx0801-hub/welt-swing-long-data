#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = "WELT_SWING_P0_RESEARCH_PARTIAL_INTEGRITY_FIX_V0_18"
RUN_STATUS = "P0_RESEARCH_PARTIAL_INTEGRITY_FIX_V0_18_COMPLETE"
DEFAULT_CONFIG = Path("config/p0_research_partial_integrity_fix_v0.18.json")
MISSING_SENTINELS = {"nan", "nat", "none", "null", "na", "n/a"}

CORE_NUMERIC_FIELDS = [
    "Close_Tech",
    "EMA20",
    "EMA50",
    "SMA200",
    "ATR14_Wilder_DEV",
    "R5",
    "R20",
    "R60",
    "High20",
    "High60",
    "High252",
    "Low20",
    "Low60",
    "Dist_EMA20",
    "Dist_EMA50",
    "Dist_SMA200",
    "Dist_High252",
    "Range20_Pct",
    "MedianVolume20_Tech",
    "MedianTurnover20_Native",
]

FEATURE_FIELDS = [
    "WS_ID",
    "AsOf",
    "Bars",
    *CORE_NUMERIC_FIELDS,
    "Feature_Status",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true")


def classify_integrity(work: pd.DataFrame) -> pd.DataFrame:
    out = work.copy()

    if "_feature_merge" not in out.columns:
        raise ValueError("_feature_merge column required")
    if "AsOf" not in out.columns:
        raise ValueError("AsOf column required")

    out["FeatureRowMatched_v0_18"] = out["_feature_merge"].eq("both")

    raw = out["AsOf"]
    text = raw.astype("string").str.strip()
    lower = text.str.lower()

    missing = raw.isna() | text.isna() | text.eq("")
    sentinel = (~missing) & lower.isin(MISSING_SENTINELS)
    candidate = text.mask(missing | sentinel)
    parsed = pd.to_datetime(candidate, errors="coerce", utc=True)
    invalid_datetime = (~missing) & (~sentinel) & parsed.isna()

    out["AsOfRaw_v0_18"] = text.fillna("")
    out["AsOfParsedUTC_v0_18"] = parsed.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
    out["AsOfValid_v0_18"] = (
        out["FeatureRowMatched_v0_18"]
        & (~missing)
        & (~sentinel)
        & (~invalid_datetime)
        & parsed.notna()
    )

    numeric = out[CORE_NUMERIC_FIELDS].apply(pd.to_numeric, errors="coerce")
    out["CoreFeatureComplete_v0_18"] = numeric.notna().all(axis=1)

    reason = pd.Series("USABLE", index=out.index, dtype="string")
    reason = reason.mask(~out["FeatureRowMatched_v0_18"], "UNMATCHED_FEATURE_ROW")
    reason = reason.mask(out["FeatureRowMatched_v0_18"] & missing, "ASOF_MISSING")
    reason = reason.mask(out["FeatureRowMatched_v0_18"] & sentinel, "ASOF_SENTINEL")
    reason = reason.mask(
        out["FeatureRowMatched_v0_18"] & invalid_datetime,
        "ASOF_INVALID_DATETIME",
    )
    reason = reason.mask(
        out["FeatureRowMatched_v0_18"]
        & out["AsOfValid_v0_18"]
        & (~out["CoreFeatureComplete_v0_18"]),
        "CORE_FEATURE_INCOMPLETE",
    )

    out["PersistentFeatureUsable_v0_18"] = (
        out["FeatureRowMatched_v0_18"]
        & out["AsOfValid_v0_18"]
        & out["CoreFeatureComplete_v0_18"]
    )
    out["IntegrityStatus_v0_18"] = out["PersistentFeatureUsable_v0_18"].map(
        {True: "USABLE", False: "QUARANTINED"}
    )
    out["QuarantineReason_v0_18"] = reason.where(
        ~out["PersistentFeatureUsable_v0_18"], ""
    )

    # v0.18 is an integrity/readiness correction only. It makes no P0 trade decision.
    out["P0QualificationAllowed_v0_18"] = False
    out["P0Survivor_v0_18"] = False
    out["TradingDecisionAllowed_v0_18"] = False
    out["P0ObservationOnly_v0_18"] = True
    return out


def self_test() -> None:
    # Regression test for the v0.17 failure mode: a left-join miss creates a real NaN.
    p = pd.DataFrame({"WS_ID": ["A", "B"]})
    f = pd.DataFrame(
        {
            "WS_ID": ["A"],
            "AsOf": ["2026-08-24"],
            **{field: [1.0] for field in CORE_NUMERIC_FIELDS},
        }
    )
    x = p.merge(f, on="WS_ID", how="left", indicator="_feature_merge", validate="one_to_one")
    r = classify_integrity(x)
    assert bool(r.loc[r.WS_ID.eq("A"), "PersistentFeatureUsable_v0_18"].iloc[0]) is True
    assert bool(r.loc[r.WS_ID.eq("B"), "PersistentFeatureUsable_v0_18"].iloc[0]) is False
    assert r.loc[r.WS_ID.eq("B"), "QuarantineReason_v0_18"].iloc[0] == "UNMATCHED_FEATURE_ROW"

    cases = pd.DataFrame(
        {
            "WS_ID": ["OK", "NONE", "NAN", "NAT", "BAD", "SPACE", "CORE"],
            "AsOf": ["2026-08-24", None, "nan", "NaT", "not-a-date", "   ", "2026-08-24"],
            "_feature_merge": ["both"] * 7,
            **{field: [1.0] * 7 for field in CORE_NUMERIC_FIELDS},
        }
    )
    cases.loc[cases.WS_ID.eq("CORE"), CORE_NUMERIC_FIELDS[0]] = None
    got = classify_integrity(cases).set_index("WS_ID")
    assert got.at["OK", "IntegrityStatus_v0_18"] == "USABLE"
    assert got.at["NONE", "QuarantineReason_v0_18"] == "ASOF_MISSING"
    assert got.at["NAN", "QuarantineReason_v0_18"] == "ASOF_SENTINEL"
    assert got.at["NAT", "QuarantineReason_v0_18"] == "ASOF_SENTINEL"
    assert got.at["BAD", "QuarantineReason_v0_18"] == "ASOF_INVALID_DATETIME"
    assert got.at["SPACE", "QuarantineReason_v0_18"] == "ASOF_MISSING"
    assert got.at["CORE", "QuarantineReason_v0_18"] == "CORE_FEATURE_INCOMPLETE"
    assert int(got["PersistentFeatureUsable_v0_18"].sum()) == 1
    assert int((got["IntegrityStatus_v0_18"] == "QUARANTINED").sum()) == 6

    print("P0_RESEARCH_PARTIAL_INTEGRITY_FIX_V0_18_SELF_TEST_PASS")


def run(config_path: Path) -> None:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if cfg["schema"] != "WELT_SWING_P0_RESEARCH_PARTIAL_INTEGRITY_FIX_CONFIG_V0_18":
        raise SystemExit("unexpected v0.18 config schema")

    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Frozen historical/source-state checks. v0.18 does not rewrite v0.16/v0.17.
    s16 = json.loads(Path(cfg["source_summary_v0_16"]).read_text(encoding="utf-8"))
    m16 = json.loads(Path(cfg["source_manifest_v0_16"]).read_text(encoding="utf-8"))
    ck16 = json.loads(Path(cfg["source_checkpoint_v0_16"]).read_text(encoding="utf-8"))
    s17 = json.loads(Path(cfg["source_summary_v0_17"]).read_text(encoding="utf-8"))

    assert s16["run_status"] == "RESEARCH_PARTIAL_SNAPSHOT_V0_16_FROZEN"
    assert s16["included_verified_strict_rows"] == cfg["expected_partial_rows"]
    assert s16["strict_u3k_freeze_allowed"] is False and s16["p0_run"] is False
    assert m16["full_scan_claim"] is False and m16["strict_u3k_frozen"] is False
    assert ck16["stage_id"] == "RESEARCH_PARTIAL_SNAPSHOT" and ck16["status"] == "PARTIAL"

    assert s17["schema"] == "WELT_SWING_P0_RESEARCH_PARTIAL_DRY_RUN_V0_17"
    assert s17["run_status"] == "P0_RESEARCH_PARTIAL_DRY_RUN_V0_17_COMPLETE_NOT_AUTOMATION_READY"
    assert s17["partial_rows"] == cfg["expected_partial_rows"]
    assert s17["feature_matched_rows"] == cfg["expected_v0_17_reported_feature_matched_rows"]
    assert s17["core_feature_complete_rows"] == cfg["expected_core_feature_complete_rows"]
    assert s17["p0_data_error_rows"] == cfg["expected_quarantine_rows"]
    assert s17["p0_run"] is False and s17["productive_trading_authority"] is False
    assert s17["alpha_vantage_allowed"] is False and s17["web_calls_per_security"] is False

    partial_path = Path(cfg["source_partial_universe_v0_16"])
    feature_path = Path(cfg["source_features_full_3663"])
    prior_obs_path = Path(cfg["source_observations_v0_17"])

    assert sha256_file(partial_path) == cfg["expected_partial_sha256"]
    assert sha256_file(feature_path) == cfg["expected_feature_sha256"]

    price_manifest = json.loads(Path(cfg["source_price_manifest"]).read_text(encoding="utf-8"))
    assert price_manifest["files"][str(feature_path)] == cfg["expected_feature_sha256"]
    price_coverage = json.loads(Path(cfg["source_price_coverage"]).read_text(encoding="utf-8"))
    assert price_coverage["data_source"] == "YFINANCE_FREE"
    assert price_coverage["alpha_vantage_allowed"] is False
    assert price_coverage["p0_status"] == "NOT_RUN_PARAMETERS_NOT_YET_PROMOTED"

    partial = pd.read_csv(partial_path, keep_default_na=False, dtype=str)
    features = pd.read_csv(feature_path, keep_default_na=False, dtype=str)
    prior_obs = pd.read_csv(prior_obs_path, keep_default_na=False, dtype=str)

    assert len(partial) == cfg["expected_partial_rows"]
    assert partial["WS_ID"].is_unique and features["WS_ID"].is_unique
    assert len(prior_obs) == cfg["expected_partial_rows"] and prior_obs["WS_ID"].is_unique

    missing_feature_fields = [c for c in FEATURE_FIELDS if c not in features.columns]
    if missing_feature_fields:
        raise SystemExit(f"missing persisted feature columns: {missing_feature_fields}")
    if "P0_DATA_ERROR_v0_17" not in prior_obs.columns:
        raise SystemExit("v0.17 observation missing P0_DATA_ERROR_v0_17")

    prior_err = prior_obs[["WS_ID", "P0_DATA_ERROR_v0_17"]].copy()
    prior_err["PriorV017DataError_v0_18"] = _as_bool(prior_err["P0_DATA_ERROR_v0_17"])
    prior_err = prior_err.drop(columns=["P0_DATA_ERROR_v0_17"])

    work = partial.merge(
        features[FEATURE_FIELDS],
        on="WS_ID",
        how="left",
        validate="one_to_one",
        indicator="_feature_merge",
    )
    work = work.merge(prior_err, on="WS_ID", how="left", validate="one_to_one")
    work["PriorV017DataError_v0_18"] = work["PriorV017DataError_v0_18"].fillna(False).astype(bool)

    fixed = classify_integrity(work)

    partial_rows = len(fixed)
    feature_matched_rows = int(fixed["FeatureRowMatched_v0_18"].sum())
    asof_valid_rows = int(fixed["AsOfValid_v0_18"].sum())
    core_complete_rows = int(fixed["CoreFeatureComplete_v0_18"].sum())
    usable_rows = int(fixed["PersistentFeatureUsable_v0_18"].sum())
    quarantine_rows = int((fixed["IntegrityStatus_v0_18"] == "QUARANTINED").sum())
    prior_error_rows = int(fixed["PriorV017DataError_v0_18"].sum())

    assert partial_rows == cfg["expected_partial_rows"]
    assert core_complete_rows == cfg["expected_core_feature_complete_rows"]
    assert usable_rows == cfg["expected_persistent_feature_usable_rows"]
    assert quarantine_rows == cfg["expected_quarantine_rows"]
    assert prior_error_rows == cfg["expected_quarantine_rows"]

    # The same two rows already flagged as v0.17 data errors are the only rows blocked here.
    quarantine_mask = fixed["IntegrityStatus_v0_18"].eq("QUARANTINED")
    if set(fixed.loc[quarantine_mask, "WS_ID"]) != set(
        fixed.loc[fixed["PriorV017DataError_v0_18"], "WS_ID"]
    ):
        raise SystemExit("v0.18 quarantine set differs from v0.17 data-error set")

    # Dynamic upstream diagnostics: preserve only fields that actually exist in the frozen partial source.
    identity_candidates = [
        "Research_Partial_Rank_v0_16",
        "WS_ID",
        "Name",
        "Country",
        "Primary_Ticker",
        "Primary_MIC",
        "Primary_Currency",
        "Primary_Universe_Index",
    ]
    diagnostic_tokens = ("status", "reason", "error", "cache", "source", "download", "coverage", "history")
    dynamic_diagnostics = [
        c
        for c in partial.columns
        if c not in identity_candidates and any(token in c.lower() for token in diagnostic_tokens)
    ]
    diagnostic_columns = []
    for c in identity_candidates + dynamic_diagnostics + [
        "Feature_Status",
        "Bars",
        "AsOfRaw_v0_18",
        "AsOfParsedUTC_v0_18",
        "FeatureRowMatched_v0_18",
        "AsOfValid_v0_18",
        "CoreFeatureComplete_v0_18",
        "PriorV017DataError_v0_18",
        "IntegrityStatus_v0_18",
        "QuarantineReason_v0_18",
        "PersistentFeatureUsable_v0_18",
    ]:
        if c in fixed.columns and c not in diagnostic_columns:
            diagnostic_columns.append(c)

    observation_columns = []
    for c in identity_candidates + [
        "AsOfRaw_v0_18",
        "AsOfParsedUTC_v0_18",
        "FeatureRowMatched_v0_18",
        "AsOfValid_v0_18",
        "CoreFeatureComplete_v0_18",
        "PersistentFeatureUsable_v0_18",
        "PriorV017DataError_v0_18",
        "IntegrityStatus_v0_18",
        "QuarantineReason_v0_18",
        "P0QualificationAllowed_v0_18",
        "P0Survivor_v0_18",
        "TradingDecisionAllowed_v0_18",
        "P0ObservationOnly_v0_18",
    ]:
        if c in fixed.columns and c not in observation_columns:
            observation_columns.append(c)

    fixed[observation_columns].to_csv(out_dir / "p0_integrity_observations_v0.18.csv", index=False)
    fixed.loc[quarantine_mask, diagnostic_columns].to_csv(
        out_dir / "p0_feature_quarantine_v0.18.csv", index=False
    )

    reason_counts = (
        fixed.loc[quarantine_mask, "QuarantineReason_v0_18"]
        .value_counts(dropna=False)
        .rename_axis("QuarantineReason_v0_18")
        .reset_index(name="Rows")
        .sort_values(["Rows", "QuarantineReason_v0_18"], ascending=[False, True])
    )
    reason_counts.to_csv(out_dir / "p0_integrity_reason_counts_v0.18.csv", index=False)

    counts = pd.DataFrame(
        [
            ["partial_rows", partial_rows],
            ["v0_17_reported_feature_matched_rows", int(s17["feature_matched_rows"])],
            ["feature_row_matched_rows_v0_18", feature_matched_rows],
            ["asof_valid_rows_v0_18", asof_valid_rows],
            ["core_feature_complete_rows_v0_18", core_complete_rows],
            ["persistent_feature_usable_rows_v0_18", usable_rows],
            ["quarantine_rows_v0_18", quarantine_rows],
            ["prior_v0_17_data_error_rows", prior_error_rows],
            ["p0_survivor_rows_v0_18", 0],
            ["decisions_changed_v0_18", 0],
        ],
        columns=["Metric", "Rows"],
    )
    counts.to_csv(out_dir / "integrity_counts_v0.18.csv", index=False)

    source_hashes = {
        "partial_universe_sha256": sha256_file(partial_path),
        "features_latest_sha256": sha256_file(feature_path),
        "v0_17_summary_sha256": sha256_file(Path(cfg["source_summary_v0_17"])),
        "v0_17_observations_sha256": sha256_file(prior_obs_path),
    }
    fix_manifest = {
        "schema": "WELT_SWING_P0_INTEGRITY_FIX_MANIFEST_V0_18",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": cfg["run_id"],
        "historical_v0_17_artifacts_mutated": False,
        "canonical_master_mutated": False,
        "network_requests_performed": False,
        "price_downloads_performed": False,
        "fx_downloads_performed": False,
        "web_calls_per_security": False,
        "alpha_vantage_allowed": False,
        "source_hashes": source_hashes,
        "integrity_fix": {
            "v0_17_defect": "post-merge missing AsOf could become string 'nan' under astype(str), while feature_matched_rows was reported as len(left_join_result)",
            "v0_18_rule": "feature row match is measured by merge indicator; AsOf is fail-closed; P0-usable also requires complete persisted core numeric features",
        },
    }
    (out_dir / "integrity_fix_manifest_v0.18.json").write_text(
        json.dumps(fix_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run_status": RUN_STATUS,
        "run_id": cfg["run_id"],
        "input_snapshot_id": m16["snapshot_id"],
        "partial_rows": partial_rows,
        "v0_17_reported_feature_matched_rows": int(s17["feature_matched_rows"]),
        "feature_row_matched_rows_v0_18": feature_matched_rows,
        "asof_valid_rows_v0_18": asof_valid_rows,
        "core_feature_complete_rows_v0_18": core_complete_rows,
        "persistent_feature_usable_rows_v0_18": usable_rows,
        "quarantine_rows_v0_18": quarantine_rows,
        "prior_v0_17_data_error_rows": prior_error_rows,
        "quarantine_reason_counts": {
            str(row["QuarantineReason_v0_18"]): int(row["Rows"])
            for _, row in reason_counts.iterrows()
        },
        "p0_survivor_rows": 0,
        "decisions_changed": 0,
        "p0_run": False,
        "p0_dry_run": True,
        "p0_qualification_automation_activated": False,
        "validated_automated_p0_run": False,
        "automated_p0_ready": False,
        "strict_u3k_frozen": False,
        "full_scan_claim": False,
        "research_partial_mode": True,
        "productive_trading_authority": False,
        "alpha_vantage_allowed": False,
        "price_downloads_performed": False,
        "fx_downloads_performed": False,
        "web_calls_per_security": False,
        "external_reference_requests": 0,
        "canonical_master_mutated": False,
        "historical_v0_17_artifacts_mutated": False,
        "next_stage": "P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION",
        "required_result_wording": "bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage",
    }
    (out_dir / "summary_v0.18.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_18",
        "run_id": cfg["run_id"],
        "stage_id": "P0_RESEARCH_PARTIAL_INTEGRITY_FIX",
        "stage_version": "v0.18",
        "status": "PARTIAL",
        "input_count": partial_rows,
        "checked_count": partial_rows,
        "usable_count": usable_rows,
        "quarantine_count": quarantine_rows,
        "p0_survivor_count": 0,
        "decisions_changed": 0,
        "validated_automated_p0_run": False,
        "next_stage": "P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION",
    }
    (out_dir / "stage_checkpoint_v0.18.json").write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
