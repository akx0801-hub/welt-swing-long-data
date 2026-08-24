#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCHEMA = "WELT_SWING_INSTRUMENT_RESOLUTION_MARKET_CODES_V0_7"
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


def combined(row: pd.Series, fields: list[str]) -> str:
    return " | ".join(txt(row.get(f, "")) for f in fields)


def resolve_brazil(row: pd.Series, cfg: dict) -> dict[str, str] | None:
    if txt(row.get("Primary_Universe_Index")) != "BR_IBRX100":
        return None

    ticker = txt(row.get("Primary_Ticker")).upper().replace(" ", "")
    br = cfg["brazil_rules"]

    if re.fullmatch(br["ordinary_regex"], ticker):
        return {
            "Instrument_Decision_v0_7": "PASS",
            "Instrument_Type_Resolved_v0_7": "ORDINARY_SHARE_BY_B3_TICKER_CODE",
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_CODE_RULE",
            "Instrument_Resolution_Reason_v0_7": "B3_SUFFIX_3_ORDINARY_SHARE",
            "Instrument_Evidence_URL_v0_7": br["evidence_b3_stocks"],
            "Instrument_Evidence_Note_v0_7": (
                "B3 official stock specification: final code 3 denotes ordinary stock. "
                "IBrX 100 methodology admits shares and units; Swing Long Strict U3K accepts "
                "ordinary shares and excludes preferred shares/units."
            ),
        }

    if re.fullmatch(br["preferred_regex"], ticker):
        return {
            "Instrument_Decision_v0_7": "FAIL",
            "Instrument_Type_Resolved_v0_7": "PREFERRED_SHARE_BY_B3_TICKER_CODE",
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_CODE_RULE",
            "Instrument_Resolution_Reason_v0_7": "B3_SUFFIX_4_TO_8_PREFERRED_SHARE",
            "Instrument_Evidence_URL_v0_7": br["evidence_b3_stocks"],
            "Instrument_Evidence_Note_v0_7": (
                "B3 official stock specification: final codes 4-8 denote preferred stock "
                "or preferred classes. Preferred shares are outside Swing Long Strict U3K."
            ),
        }

    if re.fullmatch(br["unit_regex"], ticker):
        return {
            "Instrument_Decision_v0_7": "FAIL",
            "Instrument_Type_Resolved_v0_7": "UNIT_BY_B3_TICKER_CODE",
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_CODE_RULE",
            "Instrument_Resolution_Reason_v0_7": "B3_SUFFIX_11_UNIT",
            "Instrument_Evidence_URL_v0_7": br["evidence_b3_units"],
            "Instrument_Evidence_Note_v0_7": (
                "B3 official Unit specification uses XXXX11 for securities deposit "
                "certificates/Units. Units are outside Swing Long Strict U3K."
            ),
        }

    return {
        "Instrument_Decision_v0_7": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_7": "UNKNOWN",
        "Instrument_Resolution_Method_v0_7": "B3_CODE_PATTERN_UNRESOLVED",
        "Instrument_Resolution_Reason_v0_7": "B3_TICKER_SUFFIX_NOT_MATCHED",
        "Instrument_Evidence_URL_v0_7": br["evidence_ibrx100"],
        "Instrument_Evidence_Note_v0_7": (
            "IBrX 100 may contain shares and Units. This ticker did not match the strict "
            "v0.7 B3 ordinary/preferred/unit code rules and is not guessed."
        ),
    }


def resolve_high_precision_fail(row: pd.Series, cfg: dict) -> dict[str, str] | None:
    seg = txt(row.get("Primary_Universe_Index"))
    for rule in cfg["high_precision_fail_rules"]:
        if seg not in set(rule["segments"]):
            continue
        hay = combined(row, list(rule["fields"]))
        if re.search(rule["regex"], hay):
            return {
                "Instrument_Decision_v0_7": "FAIL",
                "Instrument_Type_Resolved_v0_7": rule["resolved_type"],
                "Instrument_Resolution_Method_v0_7": "HIGH_PRECISION_SECURITY_STRUCTURE_RULE",
                "Instrument_Resolution_Reason_v0_7": rule["id"],
                "Instrument_Evidence_URL_v0_7": rule["evidence_url"],
                "Instrument_Evidence_Note_v0_7": rule["evidence_note"],
            }
    return None


def resolve_row(row: pd.Series, cfg: dict) -> dict[str, str]:
    br = resolve_brazil(row, cfg)
    if br is not None:
        return br

    hp = resolve_high_precision_fail(row, cfg)
    if hp is not None:
        return hp

    return {
        "Instrument_Decision_v0_7": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_7": "UNKNOWN",
        "Instrument_Resolution_Method_v0_7": "TARGETED_REVIEW_REQUIRED",
        "Instrument_Resolution_Reason_v0_7": "NO_HIGH_CONFIDENCE_V0_7_RULE",
        "Instrument_Evidence_URL_v0_7": "",
        "Instrument_Evidence_Note_v0_7": (
            "v0.7 deliberately makes no inference without a deterministic market-code "
            "rule or an explicit disallowed security-structure marker."
        ),
    }


def self_test() -> None:
    cfg = {
        "brazil_rules": {
            "ordinary_regex": "^[A-Z]{4}3$",
            "preferred_regex": "^[A-Z]{4}[45678]$",
            "unit_regex": "^[A-Z]{4}11$",
            "evidence_b3_stocks": "x",
            "evidence_b3_units": "y",
            "evidence_ibrx100": "z",
        },
        "high_precision_fail_rules": [
            {
                "id": "CA_EXPLICIT_TRUST_UNIT",
                "segments": ["CA_TSX"],
                "fields": ["Name", "Primary_Ticker", "Yahoo_Symbol"],
                "regex": r"(?i)((REIT|INCOME TRUST|REAL ESTATE INVESTMENT TRUST).*(\.UN|-UN\.TO)|((\.UN|-UN\.TO).*(REIT|INCOME TRUST|REAL ESTATE INVESTMENT TRUST)))",
                "resolved_type": "INCOME_TRUST_UNIT_OR_REIT_UNIT",
                "evidence_url": "u",
                "evidence_note": "n",
            }
        ],
    }
    r1 = resolve_row(pd.Series({"Primary_Universe_Index":"BR_IBRX100","Primary_Ticker":"VALE3"}), cfg)
    r2 = resolve_row(pd.Series({"Primary_Universe_Index":"BR_IBRX100","Primary_Ticker":"ITUB4"}), cfg)
    r3 = resolve_row(pd.Series({"Primary_Universe_Index":"BR_IBRX100","Primary_Ticker":"BPAC11"}), cfg)
    r4 = resolve_row(pd.Series({"Primary_Universe_Index":"CA_TSX","Name":"Example REIT","Primary_Ticker":"ABC.UN","Yahoo_Symbol":"ABC-UN.TO"}), cfg)
    assert r1["Instrument_Decision_v0_7"] == "PASS"
    assert r2["Instrument_Decision_v0_7"] == "FAIL"
    assert r3["Instrument_Decision_v0_7"] == "FAIL"
    assert r4["Instrument_Decision_v0_7"] == "FAIL"
    print("INSTRUMENT_RESOLUTION_MARKET_CODES_V0_7_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    s6 = load_json(Path(cfg["source_summary_v0_6"]))
    if s6["run_status"] != "INSTRUMENT_RESOLUTION_V0_6_COMPLETE_WITH_REMAINING_REVIEW":
        raise SystemExit("Unexpected v0.6 source status")
    if int(s6["manual_review_rows"]) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.6 manual-review count")
    if s6["p0_run"] is not False or s6["alpha_vantage_allowed"] is not False:
        raise SystemExit("Governance gate failed")

    manual = pd.read_csv(cfg["source_manual_queue_v0_6"], keep_default_na=False)
    full = pd.read_csv(cfg["source_full_eligibility_v0_6"], keep_default_na=False)

    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit(f"Manual rows {len(manual)} != expected {cfg['expected_source_manual_rows']}")
    if manual["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in source manual queue")

    br_count = int(manual["Primary_Universe_Index"].eq("BR_IBRX100").sum())
    if br_count != int(cfg["expected_brazil_rows"]):
        raise SystemExit(f"Brazil rows {br_count} != expected {cfg['expected_brazil_rows']}")

    decisions = manual.apply(lambda r: pd.Series(resolve_row(r, cfg)), axis=1)
    overlay = pd.concat([manual.reset_index(drop=True), decisions.reset_index(drop=True)], axis=1)

    brazil = overlay.loc[overlay["Primary_Universe_Index"].eq("BR_IBRX100")].copy()
    if brazil["Instrument_Decision_v0_7"].eq("NOT_VERIFIED").any():
        bad = brazil.loc[brazil["Instrument_Decision_v0_7"].eq("NOT_VERIFIED"),
                         ["WS_ID","Primary_Ticker","Name"]]
        raise SystemExit(
            "Brazil deterministic ticker classification incomplete: "
            + json.dumps(bad.to_dict("records"), ensure_ascii=False)
        )

    new_pass = overlay.loc[overlay["Instrument_Decision_v0_7"].eq("PASS")].copy()
    new_fail = overlay.loc[overlay["Instrument_Decision_v0_7"].eq("FAIL")].copy()
    remaining = overlay.loc[overlay["Instrument_Decision_v0_7"].eq("NOT_VERIFIED")].copy()

    decision_cols = [
        "WS_ID",
        "Instrument_Decision_v0_7",
        "Instrument_Type_Resolved_v0_7",
        "Instrument_Resolution_Method_v0_7",
        "Instrument_Resolution_Reason_v0_7",
        "Instrument_Evidence_URL_v0_7",
        "Instrument_Evidence_Note_v0_7",
    ]
    merged = full.merge(overlay[decision_cols], on="WS_ID", how="left")

    # v0.7 applies only to rows unresolved after v0.6. Existing v0.6 PASS/FAIL stay authoritative.
    existing6 = merged["Instrument_Decision_v0_6"].astype(str)
    merged.loc[existing6.eq("PASS"), "Instrument_Decision_v0_7"] = "PASS"
    merged.loc[existing6.eq("FAIL"), "Instrument_Decision_v0_7"] = "FAIL"
    merged.loc[existing6.eq("PASS"), "Instrument_Type_Resolved_v0_7"] = merged.loc[
        existing6.eq("PASS"), "Instrument_Type_Resolved_v0_6"
    ]
    merged.loc[existing6.eq("FAIL"), "Instrument_Type_Resolved_v0_7"] = merged.loc[
        existing6.eq("FAIL"), "Instrument_Type_Resolved_v0_6"
    ]
    merged["Instrument_Decision_v0_7"] = merged["Instrument_Decision_v0_7"].replace("", pd.NA).fillna(
        merged["Instrument_Decision_v0_6"].replace("", pd.NA).fillna("NOT_VERIFIED")
    )

    def final_status(r: pd.Series) -> str:
        if txt(r.get("Cache_Status")) != "READY":
            return "FAIL"
        if txt(r.get("Liquidity_Gate")) != "PASS":
            return "FAIL" if txt(r.get("Liquidity_Gate")) in {"FAIL", "FAIL_STRICT"} else "NOT_VERIFIED"
        if txt(r.get("Scalable_Gate")) == "FAIL":
            return "FAIL"
        d = txt(r.get("Instrument_Decision_v0_7"))
        if d == "PASS":
            return "PASS"
        if d == "FAIL":
            return "FAIL"
        return "NOT_VERIFIED"

    merged["Strict_Eligibility_v0_7"] = merged.apply(final_status, axis=1)
    strict = merged.loc[merged["Strict_Eligibility_v0_7"].eq("PASS")].copy()
    strict = strict.sort_values(
        ["MedianTurnover20_EUR","MedianTurnover60_EUR","WS_ID"],
        ascending=[False,False,True],
        kind="mergesort",
    )
    strict.insert(0, "Strict_Candidate_Rank_v0_7", range(1, len(strict)+1))

    overlay.to_csv(out / "instrument_market_code_overlay_v0.7.csv", index=False)
    new_pass.to_csv(out / "instrument_new_pass_v0.7.csv", index=False)
    new_fail.to_csv(out / "instrument_new_fail_v0.7.csv", index=False)
    remaining.to_csv(out / "instrument_manual_review_queue_v0.7.csv", index=False)
    merged.to_csv(out / "eligibility_after_instrument_v0.7.csv", index=False)
    strict.to_csv(out / "strict_u3k_candidate_after_instrument_v0.7.csv", index=False)

    seg = overlay.groupby(
        ["Primary_Universe_Index","Instrument_Decision_v0_7","Instrument_Resolution_Method_v0_7"],
        dropna=False,
    ).size().reset_index(name="Rows")
    seg.to_csv(out / "instrument_resolution_by_segment_v0.7.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "INSTRUMENT_RESOLUTION_V0_7_COMPLETE_WITH_REMAINING_REVIEW",
        "source_manual_rows": int(len(manual)),
        "new_pass_rows": int(len(new_pass)),
        "new_fail_rows": int(len(new_fail)),
        "remaining_manual_rows": int(len(remaining)),
        "brazil_source_rows": int(len(brazil)),
        "brazil_pass_rows": int((brazil["Instrument_Decision_v0_7"] == "PASS").sum()),
        "brazil_fail_rows": int((brazil["Instrument_Decision_v0_7"] == "FAIL").sum()),
        "strict_candidate_rows_v0_7": int(len(strict)),
        "strict_freeze_allowed": bool(len(remaining) == 0),
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "notes": [
            "v0.7 processes only the 778 unresolved v0.6 rows.",
            "All 48 BR_IBRX100 rows must resolve deterministically by official B3 ticker coding or the run fails.",
            "B3 suffix 3 is ordinary stock PASS; suffixes 4-8 are preferred-share FAIL; suffix 11 is Unit FAIL.",
            "Outside Brazil, only explicit high-precision trust/REIT security markers are auto-failed.",
            "No blanket PASS is added for Canada, Australia, Europe, Hong Kong, Korea, Mexico, or South Africa.",
            "No canonical master mutation occurs.",
            "No P0, stock-price downloads, FX downloads, or per-security web calls occur."
        ],
    }
    (out / "summary_v0.7.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_market_codes_v0.7.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
