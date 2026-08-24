#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_INSTRUMENT_RESOLUTION_ASX_V0_8"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False
EXTERNAL_REFERENCE_REQUESTS = 0


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def norm_code(v: Any) -> str:
    return txt(v).upper().replace(" ", "")


def classify_asx_security_type(security_type: str, cfg: dict) -> dict[str, str]:
    st = txt(security_type).upper()
    rules = cfg["asx_rules"]

    if st in {x.upper() for x in rules["pass_exact_security_types"]}:
        return {
            "Instrument_Decision_v0_8": "PASS",
            "Instrument_Type_Resolved_v0_8": "ORDINARY_SHARE_BY_ASX_SECURITY_TYPE",
            "Instrument_Resolution_Method_v0_8": "ASX_OFFICIAL_ISIN_DIRECTORY_SECURITY_TYPE",
            "Instrument_Resolution_Reason_v0_8": "ASX_SECURITY_TYPE_ORDINARY_FULLY_PAID",
        }

    if any(token.upper() in st for token in rules["fail_contains_tokens"]):
        resolved = "DISALLOWED_DEPOSITARY_OR_STAPLED_STRUCTURE"
        if "STAPLED" in st or "ORDINARY/UNITS" in st:
            resolved = "STAPLED_ORDINARY_AND_UNIT_SECURITY"
        elif "CDI" in st or "DEPOSITARY INTEREST" in st:
            resolved = "DEPOSITARY_INTEREST"
        return {
            "Instrument_Decision_v0_8": "FAIL",
            "Instrument_Type_Resolved_v0_8": resolved,
            "Instrument_Resolution_Method_v0_8": "ASX_OFFICIAL_ISIN_DIRECTORY_SECURITY_TYPE",
            "Instrument_Resolution_Reason_v0_8": "ASX_SECURITY_TYPE_OUTSIDE_STRICT_COMMON_ORDINARY_GATE",
        }

    return {
        "Instrument_Decision_v0_8": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_8": "UNKNOWN",
        "Instrument_Resolution_Method_v0_8": "ASX_SECURITY_TYPE_UNRECOGNIZED",
        "Instrument_Resolution_Reason_v0_8": "NO_DETERMINISTIC_ASX_V0_8_RULE",
    }


def self_test() -> None:
    cfg = {
        "asx_rules": {
            "pass_exact_security_types": ["ORDINARY FULLY PAID"],
            "fail_contains_tokens": ["STAPLED", "ORDINARY/UNITS", "CDI ", "CHESS DEPOSITARY INTERESTS"],
        }
    }
    assert classify_asx_security_type("ORDINARY FULLY PAID", cfg)["Instrument_Decision_v0_8"] == "PASS"
    assert classify_asx_security_type("FULLY PAID ORDINARY/UNITS STAPLED SECURITIES", cfg)["Instrument_Decision_v0_8"] == "FAIL"
    assert classify_asx_security_type("CDI 1:1 FOREIGN EXEMPT NYSE", cfg)["Instrument_Decision_v0_8"] == "FAIL"
    assert classify_asx_security_type("CHESS DEPOSITARY INTERESTS 1:1", cfg)["Instrument_Decision_v0_8"] == "FAIL"
    assert classify_asx_security_type("SOMETHING ELSE", cfg)["Instrument_Decision_v0_8"] == "NOT_VERIFIED"
    print("INSTRUMENT_RESOLUTION_ASX_V0_8_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    s7 = load_json(Path(cfg["source_summary_v0_7"]))
    if s7.get("schema") != "WELT_SWING_INSTRUMENT_RESOLUTION_PRIMARY_MARKET_V0_7":
        raise SystemExit("Wrong v0.7 source schema; do not continue")
    if s7.get("run_status") != "INSTRUMENT_RESOLUTION_PRIMARY_MARKET_V0_7_COMPLETE_WITH_REMAINING_REVIEW":
        raise SystemExit("Unexpected v0.7 source run status")
    if int(s7.get("remaining_manual_review_rows", -1)) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.7 remaining-manual count")
    if int(s7.get("strict_candidates_v0_7", -1)) != int(cfg["expected_source_strict_candidates"]):
        raise SystemExit("Unexpected v0.7 strict candidate count")
    if float(s7.get("asx_reference_probe", {}).get("target_coverage", 0.0)) != 1.0:
        raise SystemExit("ASX v0.7 reference coverage is not 100%")

    manual = pd.read_csv(cfg["source_manual_queue_v0_7"], keep_default_na=False, dtype=str)
    full = pd.read_csv(cfg["source_full_eligibility_v0_7"], keep_default_na=False, dtype=str)
    ref = pd.read_csv(cfg["source_asx_reference_matches_v0_7"], keep_default_na=False, dtype=str)

    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit(f"Manual rows {len(manual)} != expected {cfg['expected_source_manual_rows']}")
    if manual["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.7 manual queue")

    au = manual.loc[manual["Primary_Universe_Index"].eq("AU_ASX200")].copy()
    if len(au) != int(cfg["expected_asx_rows"]):
        raise SystemExit(f"ASX rows {len(au)} != expected {cfg['expected_asx_rows']}")
    if len(ref) != int(cfg["expected_asx_reference_rows"]):
        raise SystemExit(f"ASX reference rows {len(ref)} != expected {cfg['expected_asx_reference_rows']}")

    au["_ASX_CODE_NORM"] = au["Primary_Ticker"].map(norm_code)
    ref["_ASX_CODE_NORM"] = ref["ASX code"].map(norm_code)

    if au["_ASX_CODE_NORM"].duplicated().any():
        raise SystemExit("Duplicate ASX target code")
    if ref["_ASX_CODE_NORM"].duplicated().any():
        raise SystemExit("Duplicate ASX reference code")

    matched = au.merge(
        ref[["_ASX_CODE_NORM", "ASX code", "Company name", "Security type", "ISIN code"]],
        on="_ASX_CODE_NORM",
        how="left",
        validate="one_to_one",
        suffixes=("", "_ASX_REF"),
    )
    missing_ref = matched["Security type"].eq("") | matched["Security type"].isna()
    if missing_ref.any():
        bad = matched.loc[missing_ref, ["WS_ID","Primary_Ticker","Name"]]
        raise SystemExit("Missing ASX reference security type: " + json.dumps(bad.to_dict("records"), ensure_ascii=False))

    decisions = matched["Security type"].map(lambda x: classify_asx_security_type(x, cfg))
    dec_df = pd.DataFrame(decisions.tolist())
    matched = pd.concat([matched.reset_index(drop=True), dec_df.reset_index(drop=True)], axis=1)
    matched["Instrument_Evidence_URL_v0_8"] = cfg["asx_rules"]["reference_url"]
    matched["Instrument_Evidence_Note_v0_8"] = (
        cfg["asx_rules"]["reference_description"]
        + " Security type is read from the frozen v0.7 reference-match file; no new request is made."
    )

    unresolved_au = matched.loc[matched["Instrument_Decision_v0_8"].eq("NOT_VERIFIED")].copy()
    if not unresolved_au.empty:
        raise SystemExit(
            "ASX deterministic classification incomplete: "
            + json.dumps(
                unresolved_au[["WS_ID","Primary_Ticker","Name","Security type"]].to_dict("records"),
                ensure_ascii=False,
            )
        )

    asx_pass = matched.loc[matched["Instrument_Decision_v0_8"].eq("PASS")].copy()
    asx_fail = matched.loc[matched["Instrument_Decision_v0_8"].eq("FAIL")].copy()
    if len(asx_pass) != int(cfg["expected_asx_pass_rows"]):
        raise SystemExit(f"ASX PASS {len(asx_pass)} != expected {cfg['expected_asx_pass_rows']}")
    if len(asx_fail) != int(cfg["expected_asx_fail_rows"]):
        raise SystemExit(f"ASX FAIL {len(asx_fail)} != expected {cfg['expected_asx_fail_rows']}")

    overlay_cols = [
        "WS_ID",
        "Instrument_Decision_v0_8",
        "Instrument_Type_Resolved_v0_8",
        "Instrument_Resolution_Method_v0_8",
        "Instrument_Resolution_Reason_v0_8",
        "Instrument_Evidence_URL_v0_8",
        "Instrument_Evidence_Note_v0_8",
    ]
    overlay = matched[overlay_cols].copy()

    merged = full.merge(overlay, on="WS_ID", how="left")
    d7 = merged["Instrument_Decision_v0_7"].astype(str)

    existing_pass = d7.eq("PASS")
    existing_fail = d7.eq("FAIL")
    merged.loc[existing_pass, "Instrument_Decision_v0_8"] = "PASS"
    merged.loc[existing_fail, "Instrument_Decision_v0_8"] = "FAIL"
    merged.loc[existing_pass, "Instrument_Type_Resolved_v0_8"] = merged.loc[existing_pass, "Instrument_Type_Resolved_v0_7"]
    merged.loc[existing_fail, "Instrument_Type_Resolved_v0_8"] = merged.loc[existing_fail, "Instrument_Type_Resolved_v0_7"]

    merged["Instrument_Decision_v0_8"] = merged["Instrument_Decision_v0_8"].replace("", pd.NA).fillna(
        merged["Instrument_Decision_v0_7"].replace("", pd.NA).fillna("NOT_VERIFIED")
    )

    def final_status(r: pd.Series) -> str:
        if txt(r.get("Cache_Status")) != "READY":
            return "FAIL"
        if txt(r.get("Liquidity_Gate")) != "PASS":
            return "FAIL" if txt(r.get("Liquidity_Gate")) in {"FAIL", "FAIL_STRICT"} else "NOT_VERIFIED"
        if txt(r.get("Scalable_Gate")) == "FAIL":
            return "FAIL"
        d = txt(r.get("Instrument_Decision_v0_8"))
        if d == "PASS":
            return "PASS"
        if d == "FAIL":
            return "FAIL"
        return "NOT_VERIFIED"

    merged["Strict_Eligibility_v0_8"] = merged.apply(final_status, axis=1)
    strict = merged.loc[merged["Strict_Eligibility_v0_8"].eq("PASS")].copy()
    strict["MedianTurnover20_EUR"] = pd.to_numeric(strict["MedianTurnover20_EUR"], errors="coerce")
    strict["MedianTurnover60_EUR"] = pd.to_numeric(strict["MedianTurnover60_EUR"], errors="coerce")
    strict = strict.sort_values(
        ["MedianTurnover20_EUR","MedianTurnover60_EUR","WS_ID"],
        ascending=[False,False,True],
        kind="mergesort",
    )
    strict.insert(0, "Strict_Candidate_Rank_v0_8", range(1, len(strict)+1))

    remaining_ids = set(manual["WS_ID"].astype(str)) - set(overlay["WS_ID"].astype(str))
    remaining = manual.loc[manual["WS_ID"].astype(str).isin(remaining_ids)].copy()
    if len(remaining) != int(cfg["expected_remaining_manual_rows"]):
        raise SystemExit(f"Remaining manual {len(remaining)} != expected {cfg['expected_remaining_manual_rows']}")
    if len(strict) != int(cfg["expected_strict_candidates_v0_8"]):
        raise SystemExit(f"Strict candidates {len(strict)} != expected {cfg['expected_strict_candidates_v0_8']}")

    matched.to_csv(out / "asx_security_type_resolution_v0.8.csv", index=False)
    asx_pass.to_csv(out / "asx_new_pass_v0.8.csv", index=False)
    asx_fail.to_csv(out / "asx_new_fail_v0.8.csv", index=False)
    remaining.to_csv(out / "instrument_manual_review_queue_v0.8.csv", index=False)
    merged.to_csv(out / "eligibility_after_instrument_v0.8.csv", index=False)
    strict.to_csv(out / "strict_u3k_candidate_after_instrument_v0.8.csv", index=False)

    seg = remaining.groupby("Primary_Universe_Index").size().reset_index(name="Rows")
    seg.to_csv(out / "remaining_review_by_segment_v0.8.csv", index=False)

    type_counts = matched.groupby(["Security type", "Instrument_Decision_v0_8"]).size().reset_index(name="Rows")
    type_counts.to_csv(out / "asx_security_type_counts_v0.8.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "INSTRUMENT_RESOLUTION_ASX_V0_8_COMPLETE_WITH_REMAINING_REVIEW",
        "source_manual_rows_v0_7": int(len(manual)),
        "australia_source_rows": int(len(au)),
        "asx_reference_rows": int(len(ref)),
        "asx_reference_coverage": 1.0,
        "asx_pass_rows": int(len(asx_pass)),
        "asx_fail_rows": int(len(asx_fail)),
        "asx_unresolved_rows": int(len(unresolved_au)),
        "remaining_manual_rows": int(len(remaining)),
        "strict_candidates_v0_7": int(cfg["expected_source_strict_candidates"]),
        "strict_candidates_v0_8": int(len(strict)),
        "strict_freeze_allowed": bool(len(remaining) == 0),
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "external_reference_requests": EXTERNAL_REFERENCE_REQUESTS,
        "notes": [
            "v0.8 consumes the already frozen v0.7 ASX reference-match evidence and makes no new web request.",
            "All 63 remaining AU_ASX200 rows are resolved from the official ASX Security type column.",
            "ORDINARY FULLY PAID is strict PASS.",
            "Stapled ordinary/unit securities and CDI/CHESS depositary interests are strict FAIL under the common/ordinary-share-only instrument gate.",
            "Existing v0.7 Brazil and earlier instrument decisions remain immutable.",
            "The canonical universe master is not mutated.",
            "P0 remains off."
        ],
    }
    (out / "summary_v0.8.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_asx_v0.8.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
