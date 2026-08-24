#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_INSTRUMENT_RESOLUTION_V0_6"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False


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


def combined_fields(row: pd.Series, fields: list[str]) -> str:
    return " | ".join(txt(row.get(f, "")) for f in fields)


def apply_auto_fail(row: pd.Series, rules: list[dict]) -> tuple[str, str, str] | None:
    seg = txt(row.get("Primary_Universe_Index", ""))
    for rule in rules:
        segments = set(rule.get("segments", []))
        if "*" not in segments and seg not in segments:
            continue
        hay = combined_fields(row, list(rule.get("fields", [])))
        if re.search(str(rule["regex"]), hay):
            return (
                str(rule["decision"]),
                str(rule["resolved_instrument_type"]),
                str(rule["id"]),
            )
    return None


def resolve_review_row(row: pd.Series, cfg: dict) -> dict[str, Any]:
    seg = txt(row.get("Primary_Universe_Index", ""))
    group = cfg["group_rules"].get(seg, {})

    # Strong group PASS has precedence. This is intentionally limited to a
    # segment whose official index-family eligibility is accepted as common-equity
    # evidence. Mixed-market token rules are not allowed to override it.
    if group.get("decision") == "PASS":
        return {
            "Instrument_Decision_v0_6": "PASS",
            "Instrument_Type_Resolved_v0_6": group.get(
                "resolved_instrument_type", "COMMON_STOCK_BY_INDEX_ELIGIBILITY"
            ),
            "Instrument_Resolution_Method_v0_6": group.get("governance", "AUTO_PASS_GROUP_RULE"),
            "Instrument_Resolution_Reason_v0_6": group.get("reason", "GROUP_RULE_PASS"),
            "Instrument_Evidence_URL_v0_6": group.get("evidence_url", ""),
            "Instrument_Evidence_Note_v0_6": group.get("evidence_note", ""),
        }

    fail = apply_auto_fail(row, cfg["auto_fail_rules"])
    if fail is not None:
        decision, resolved_type, reason = fail
        return {
            "Instrument_Decision_v0_6": decision,
            "Instrument_Type_Resolved_v0_6": resolved_type,
            "Instrument_Resolution_Method_v0_6": "AUTO_FAIL_SECURITY_TOKEN_RULE",
            "Instrument_Resolution_Reason_v0_6": reason,
            "Instrument_Evidence_URL_v0_6": group.get("evidence_url", ""),
            "Instrument_Evidence_Note_v0_6": (
                "Clear disallowed security-structure token found in frozen row fields. "
                + group.get("evidence_note", "")
            ).strip(),
        }

    return {
        "Instrument_Decision_v0_6": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_6": "UNKNOWN",
        "Instrument_Resolution_Method_v0_6": group.get(
            "governance", "TARGETED_REVIEW_REQUIRED"
        ),
        "Instrument_Resolution_Reason_v0_6": group.get(
            "reason", "NO_GROUP_RULE"
        ),
        "Instrument_Evidence_URL_v0_6": group.get("evidence_url", ""),
        "Instrument_Evidence_Note_v0_6": group.get("evidence_note", ""),
    }


def self_test() -> None:
    cfg = {
        "group_rules": {
            "US_SP1500": {
                "decision": "PASS",
                "resolved_instrument_type": "COMMON_STOCK_BY_INDEX_ELIGIBILITY",
                "reason": "US_COMMON",
                "governance": "AUTO_PASS_GROUP_RULE",
            },
            "CA_TSX": {
                "decision": "NOT_VERIFIED",
                "reason": "MIXED",
                "governance": "TARGETED_REVIEW_REQUIRED",
            },
        },
        "auto_fail_rules": [
            {
                "id": "CANADA_UNIT",
                "segments": ["CA_TSX"],
                "fields": ["Name", "Yahoo_Symbol"],
                "regex": r"(?i)(REIT|[-.]UN(?:[.-]|$))",
                "decision": "FAIL",
                "resolved_instrument_type": "UNIT_OR_TRUST_UNIT",
            }
        ],
    }
    us = pd.Series({"Primary_Universe_Index": "US_SP1500", "Name": "Example REIT Corp"})
    ca = pd.Series({"Primary_Universe_Index": "CA_TSX", "Name": "Example REIT", "Yahoo_Symbol": "ABC-UN.TO"})
    eu = pd.Series({"Primary_Universe_Index": "EU_STOXX600", "Name": "Example AG"})
    assert resolve_review_row(us, cfg)["Instrument_Decision_v0_6"] == "PASS"
    assert resolve_review_row(ca, cfg)["Instrument_Decision_v0_6"] == "FAIL"
    assert resolve_review_row(eu, cfg)["Instrument_Decision_v0_6"] == "NOT_VERIFIED"
    print("INSTRUMENT_RESOLUTION_V0_6_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    summary_v05 = load_json(Path(cfg["source_summary"]))
    if summary_v05["run_status"] != "U3K_LIQUIDITY_FX_AUDIT_COMPLETE_WITH_BLOCKERS":
        raise SystemExit("Unexpected v0.5 source run status")
    if int(summary_v05["instrument_review_queue_rows"]) != int(cfg["expected_review_rows"]):
        raise SystemExit("Unexpected v0.5 review count")
    if int(summary_v05["strict_eligible_rows"]) != int(cfg["expected_existing_explicit_pass_rows"]):
        raise SystemExit("Unexpected v0.5 strict PASS count")
    if summary_v05["p0_run"] is not False or summary_v05["alpha_vantage_allowed"] is not False:
        raise SystemExit("Source governance gate failed")

    elig = pd.read_csv(cfg["source_eligibility"], keep_default_na=False)
    review = pd.read_csv(cfg["source_review_queue"], keep_default_na=False)

    if len(review) != int(cfg["expected_review_rows"]):
        raise SystemExit(f"Review rows {len(review)} != expected {cfg['expected_review_rows']}")
    if review["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in review queue")
    if not review["Instrument_Gate"].eq("NOT_VERIFIED").all():
        raise SystemExit("Review queue contains non-NOT_VERIFIED instrument gate")
    if not review["Cache_Status"].eq("READY").all():
        raise SystemExit("Review queue contains non-READY rows")
    if not review["Liquidity_Gate"].eq("PASS").all():
        raise SystemExit("Review queue contains non-standard-liquidity rows")

    decisions = review.apply(lambda r: pd.Series(resolve_review_row(r, cfg)), axis=1)
    overlay = pd.concat([review.reset_index(drop=True), decisions.reset_index(drop=True)], axis=1)

    us_count = int((overlay["Primary_Universe_Index"].eq("US_SP1500")).sum())
    if us_count != int(cfg["expected_us_sp1500_review_rows"]):
        raise SystemExit(f"US review rows {us_count} != expected {cfg['expected_us_sp1500_review_rows']}")
    us_decisions = overlay.loc[overlay["Primary_Universe_Index"].eq("US_SP1500"), "Instrument_Decision_v0_6"]
    if not us_decisions.eq("PASS").all():
        raise SystemExit("Not all frozen US_SP1500 review rows resolved PASS by group rule")

    auto_pass = overlay.loc[overlay["Instrument_Decision_v0_6"].eq("PASS")].copy()
    auto_fail = overlay.loc[overlay["Instrument_Decision_v0_6"].eq("FAIL")].copy()
    manual = overlay.loc[overlay["Instrument_Decision_v0_6"].eq("NOT_VERIFIED")].copy()

    # Apply the overlay to the complete v0.5 eligibility table without mutating
    # the canonical master. Existing explicit PASS/FAIL remains authoritative.
    decision_cols = [
        "WS_ID",
        "Instrument_Decision_v0_6",
        "Instrument_Type_Resolved_v0_6",
        "Instrument_Resolution_Method_v0_6",
        "Instrument_Resolution_Reason_v0_6",
        "Instrument_Evidence_URL_v0_6",
        "Instrument_Evidence_Note_v0_6",
    ]
    merged = elig.merge(overlay[decision_cols], on="WS_ID", how="left")

    existing_pass = merged["Instrument_Gate"].eq("PASS")
    existing_fail = merged["Instrument_Gate"].eq("FAIL")
    merged.loc[existing_pass, "Instrument_Decision_v0_6"] = "PASS"
    merged.loc[existing_pass, "Instrument_Type_Resolved_v0_6"] = merged.loc[existing_pass, "Instrument_Type"]
    merged.loc[existing_pass, "Instrument_Resolution_Method_v0_6"] = "EXPLICIT_EXISTING_V0_5"
    merged.loc[existing_pass, "Instrument_Resolution_Reason_v0_6"] = "EXPLICIT_ALLOWED_INSTRUMENT_TYPE"

    merged.loc[existing_fail, "Instrument_Decision_v0_6"] = "FAIL"
    merged.loc[existing_fail, "Instrument_Type_Resolved_v0_6"] = merged.loc[existing_fail, "Instrument_Type"]
    merged.loc[existing_fail, "Instrument_Resolution_Method_v0_6"] = "EXPLICIT_EXISTING_V0_5"
    merged.loc[existing_fail, "Instrument_Resolution_Reason_v0_6"] = "EXPLICIT_DISALLOWED_INSTRUMENT_TYPE"

    merged["Instrument_Decision_v0_6"] = merged["Instrument_Decision_v0_6"].replace("", pd.NA).fillna("NOT_VERIFIED")
    merged["Instrument_Type_Resolved_v0_6"] = merged["Instrument_Type_Resolved_v0_6"].replace("", pd.NA).fillna("UNKNOWN")
    merged["Instrument_Resolution_Method_v0_6"] = merged["Instrument_Resolution_Method_v0_6"].replace("", pd.NA).fillna("UNCHANGED_NOT_VERIFIED")
    merged["Instrument_Resolution_Reason_v0_6"] = merged["Instrument_Resolution_Reason_v0_6"].replace("", pd.NA).fillna("NO_NEW_RESOLUTION")

    def final_status(r: pd.Series) -> str:
        if txt(r.get("Cache_Status")) != "READY":
            return "FAIL"
        if txt(r.get("Liquidity_Gate")) != "PASS":
            return "FAIL" if txt(r.get("Liquidity_Gate")) in {"FAIL", "FAIL_STRICT"} else "NOT_VERIFIED"
        if txt(r.get("Scalable_Gate")) == "FAIL":
            return "FAIL"
        d = txt(r.get("Instrument_Decision_v0_6"))
        if d == "PASS":
            return "PASS"
        if d == "FAIL":
            return "FAIL"
        return "NOT_VERIFIED"

    merged["Strict_Eligibility_v0_6"] = merged.apply(final_status, axis=1)

    strict_pass = merged.loc[merged["Strict_Eligibility_v0_6"].eq("PASS")].copy()
    strict_pass = strict_pass.sort_values(
        ["MedianTurnover20_EUR", "MedianTurnover60_EUR", "WS_ID"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    strict_pass.insert(0, "Strict_Candidate_Rank_v0_6", range(1, len(strict_pass)+1))

    # Strict freeze remains blocked while any standard-liquidity instrument row
    # is unresolved. This is a candidate file, not SWING_U3K_FROZEN.
    freeze_allowed = len(manual) == 0

    overlay.to_csv(out / "instrument_resolution_overlay_v0.6.csv", index=False)
    auto_pass.to_csv(out / "instrument_auto_pass_v0.6.csv", index=False)
    auto_fail.to_csv(out / "instrument_auto_fail_v0.6.csv", index=False)
    manual.to_csv(out / "instrument_manual_review_queue_v0.6.csv", index=False)
    merged.to_csv(out / "eligibility_after_instrument_v0.6.csv", index=False)
    strict_pass.to_csv(out / "strict_u3k_candidate_after_instrument_v0.6.csv", index=False)

    seg = overlay.groupby(
        ["Primary_Universe_Index", "Instrument_Decision_v0_6", "Instrument_Resolution_Method_v0_6"],
        dropna=False,
    ).size().reset_index(name="Rows")
    seg.to_csv(out / "instrument_resolution_by_segment_v0.6.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "INSTRUMENT_RESOLUTION_V0_6_COMPLETE_WITH_REMAINING_REVIEW" if not freeze_allowed else "INSTRUMENT_RESOLUTION_V0_6_COMPLETE_FREEZE_ALLOWED",
        "source_review_rows": int(len(review)),
        "auto_pass_rows": int(len(auto_pass)),
        "auto_fail_rows": int(len(auto_fail)),
        "manual_review_rows": int(len(manual)),
        "us_sp1500_group_pass_rows": int((auto_pass["Primary_Universe_Index"] == "US_SP1500").sum()),
        "existing_explicit_pass_rows_v0_5": int(cfg["expected_existing_explicit_pass_rows"]),
        "strict_candidate_rows_v0_6": int(len(strict_pass)),
        "strict_freeze_allowed": bool(freeze_allowed),
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "notes": [
            "Only the frozen v0.5 2,113-row instrument review queue is processed.",
            "US_SP1500 is the only blanket PASS segment in v0.6 because current official S&P U.S. index-family evidence is accepted as group-level common-equity evidence.",
            "Canada is explicitly not blanket-passed because the S&P/TSX Composite includes common stocks and income trust units.",
            "Australia, Mexico, New Zealand, Europe, Hong Kong, Korea, South Africa and Brazil remain targeted-review segments unless a clear disallowed security token yields an automatic FAIL.",
            "No canonical master mutation occurs in v0.6; decisions are stored as an overlay.",
            "No U3K freeze is emitted while manual instrument review remains non-zero.",
            "P0 remains off."
        ],
    }
    (out / "summary_v0.6.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_rules_v0.6.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
