#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

SCHEMA = "WELT_SWING_INSTRUMENT_RESOLUTION_PRIMARY_MARKET_V0_7"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False
ASX_AUTO_CLASSIFICATION_ENABLED = False


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def b3_numeric_suffix(ticker: Any) -> int | None:
    s = txt(ticker).upper()
    m = re.search(r"(\d{1,2})$", s)
    if not m:
        return None
    return int(m.group(1))


def classify_b3_ticker(ticker: Any, cfg: dict) -> dict[str, str]:
    suffix = b3_numeric_suffix(ticker)
    if suffix is None:
        return {
            "Instrument_Decision_v0_7": "NOT_VERIFIED",
            "Instrument_Type_Resolved_v0_7": "UNKNOWN",
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_RULE_UNRESOLVED",
            "Instrument_Resolution_Reason_v0_7": "NO_TRAILING_B3_SECURITY_TYPE_NUMBER",
        }

    direct = cfg["suffix_rules"].get(str(suffix))
    if direct is not None:
        decision, resolved_type = direct
        return {
            "Instrument_Decision_v0_7": decision,
            "Instrument_Type_Resolved_v0_7": resolved_type,
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_SUFFIX_RULE",
            "Instrument_Resolution_Reason_v0_7": f"B3_SUFFIX_{suffix:02d}",
        }

    if int(cfg["other_asset_suffix_min"]) <= suffix <= int(cfg["other_asset_suffix_max"]):
        return {
            "Instrument_Decision_v0_7": "FAIL",
            "Instrument_Type_Resolved_v0_7": "B3_OTHER_ASSET_UNIT_FUND_OR_OTHER_NONORDINARY",
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_SUFFIX_RULE",
            "Instrument_Resolution_Reason_v0_7": f"B3_SUFFIX_{suffix:02d}_OTHER_ASSET_11_30",
        }

    if int(cfg["bdr_suffix_min"]) <= suffix <= int(cfg["bdr_suffix_max"]):
        return {
            "Instrument_Decision_v0_7": "FAIL",
            "Instrument_Type_Resolved_v0_7": "BRAZILIAN_DEPOSITARY_RECEIPT",
            "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_SUFFIX_RULE",
            "Instrument_Resolution_Reason_v0_7": f"B3_SUFFIX_{suffix:02d}_BDR_31_40",
        }

    return {
        "Instrument_Decision_v0_7": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_7": "UNKNOWN",
        "Instrument_Resolution_Method_v0_7": "B3_OFFICIAL_TICKER_RULE_UNRESOLVED",
        "Instrument_Resolution_Reason_v0_7": f"B3_SUFFIX_{suffix:02d}_OUTSIDE_RULE",
    }


def normalize_col(v: Any) -> str:
    s = txt(v).upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s).strip("_")
    return s


def read_asx_workbook(raw_path: Path) -> tuple[list[dict[str, Any]], dict[str, pd.DataFrame]]:
    xls = pd.ExcelFile(raw_path, engine="xlrd")
    sheets: dict[str, pd.DataFrame] = {}
    meta: list[dict[str, Any]] = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(raw_path, sheet_name=sheet, engine="xlrd", dtype=str)
        df = df.fillna("")
        sheets[str(sheet)] = df
        meta.append({
            "Sheet": str(sheet),
            "Rows": int(len(df)),
            "Columns": int(len(df.columns)),
            "Column_Names": " | ".join(str(c) for c in df.columns),
        })
    return meta, sheets


def score_code_column(df: pd.DataFrame, target_codes: set[str]) -> list[dict[str, Any]]:
    scores = []
    for c in df.columns:
        vals = df[c].astype(str).str.strip().str.upper()
        matches = int(vals.isin(target_codes).sum())
        nonblank = int(vals.ne("").sum())
        if matches > 0:
            scores.append({
                "Column": str(c),
                "Normalized_Column": normalize_col(c),
                "Matches_Target_ASX_Codes": matches,
                "Nonblank": nonblank,
            })
    return sorted(scores, key=lambda x: (-x["Matches_Target_ASX_Codes"], x["Column"]))


def probe_asx_reference(
    asx_rows: pd.DataFrame,
    cfg: dict,
    out_dir: Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "NOT_RUN",
        "url": cfg["official_isin_xls"],
        "download_attempts": 1,
        "auto_classification_enabled": bool(cfg.get("auto_classification_enabled", False)),
        "target_rows": int(len(asx_rows)),
        "target_unique_codes": int(asx_rows["Primary_Ticker"].astype(str).nunique()),
    }

    raw_path = Path(cfg["runtime_raw_path"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(
            cfg["official_isin_xls"],
            timeout=int(cfg.get("download_timeout_seconds", 30)),
            headers={"User-Agent": "Welt-Swing-Long-DEV/0.7 reference-data audit"},
        )
        result["http_status"] = int(r.status_code)
        r.raise_for_status()
        content = r.content
        result["download_bytes"] = int(len(content))
        if len(content) <= 0:
            raise RuntimeError("ASX ISIN download returned zero bytes")
        if len(content) > int(cfg.get("max_download_bytes", 25000000)):
            raise RuntimeError("ASX ISIN download exceeds configured size cap")
        raw_path.write_bytes(content)
        result["sha256"] = sha256_file(raw_path)
        result["content_type"] = txt(r.headers.get("content-type", ""))
    except Exception as exc:
        result["status"] = "DOWNLOAD_FAILED"
        result["error"] = f"{type(exc).__name__}: {exc}"
        (out_dir / "asx_reference_probe_v0.7.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return result

    try:
        sheet_meta, sheets = read_asx_workbook(raw_path)
        pd.DataFrame(sheet_meta).to_csv(
            out_dir / "asx_reference_workbook_schema_v0.7.csv",
            index=False,
        )

        target_codes = set(asx_rows["Primary_Ticker"].astype(str).str.strip().str.upper())
        code_candidates: list[dict[str, Any]] = []
        for sheet_name, df in sheets.items():
            for item in score_code_column(df, target_codes):
                code_candidates.append({"Sheet": sheet_name, **item})
        code_candidates = sorted(
            code_candidates,
            key=lambda x: (-x["Matches_Target_ASX_Codes"], x["Sheet"], x["Column"]),
        )
        pd.DataFrame(code_candidates).to_csv(
            out_dir / "asx_reference_code_column_candidates_v0.7.csv",
            index=False,
        )

        if not code_candidates:
            result["status"] = "PARSED_NO_CODE_COLUMN_MATCH"
            result["sheet_count"] = len(sheets)
            result["best_code_matches"] = 0
            (out_dir / "asx_reference_probe_v0.7.json").write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return result

        best = code_candidates[0]
        bdf = sheets[best["Sheet"]].copy()
        code_col = best["Column"]
        bdf["_ASX_CODE_NORM"] = bdf[code_col].astype(str).str.strip().str.upper()
        matched = bdf.loc[bdf["_ASX_CODE_NORM"].isin(target_codes)].copy()

        # Keep all columns from the official directory so the next promotion
        # decision is based on the actual schema, not on guessed column names.
        matched.insert(0, "ASX_Reference_Sheet", best["Sheet"])
        matched.insert(1, "ASX_Reference_Code_Column", code_col)
        matched.to_csv(out_dir / "asx_reference_matches_v0.7.csv", index=False)

        result.update({
            "status": "PARSED_MATCHES_AVAILABLE",
            "sheet_count": len(sheets),
            "best_sheet": best["Sheet"],
            "best_code_column": code_col,
            "best_code_matches": int(best["Matches_Target_ASX_Codes"]),
            "matched_rows": int(len(matched)),
            "matched_unique_target_codes": int(matched["_ASX_CODE_NORM"].nunique()),
            "target_coverage": (
                float(matched["_ASX_CODE_NORM"].nunique()) / float(len(target_codes))
                if target_codes else 0.0
            ),
            "official_columns": [str(c) for c in bdf.columns if c != "_ASX_CODE_NORM"],
        })
    except Exception as exc:
        result["status"] = "PARSE_FAILED"
        result["error"] = f"{type(exc).__name__}: {exc}"

    (out_dir / "asx_reference_probe_v0.7.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def strict_status(row: pd.Series) -> str:
    if txt(row.get("Cache_Status")) != "READY":
        return "FAIL"
    liq = txt(row.get("Liquidity_Gate"))
    if liq != "PASS":
        return "FAIL" if liq in {"FAIL", "FAIL_STRICT"} else "NOT_VERIFIED"
    if txt(row.get("Scalable_Gate")) == "FAIL":
        return "FAIL"
    d = txt(row.get("Instrument_Decision_v0_7"))
    if d == "PASS":
        return "PASS"
    if d == "FAIL":
        return "FAIL"
    return "NOT_VERIFIED"


def self_test() -> None:
    cfg = {
        "suffix_rules": {
            "1": ["FAIL", "RIGHT"],
            "2": ["FAIL", "RIGHT_PREF"],
            "3": ["PASS", "ORDINARY_SHARE"],
            "4": ["FAIL", "PREFERRED_SHARE"],
            "9": ["FAIL", "RECEIPT"],
            "10": ["FAIL", "RECEIPT_PREF"],
        },
        "other_asset_suffix_min": 11,
        "other_asset_suffix_max": 30,
        "bdr_suffix_min": 31,
        "bdr_suffix_max": 40,
    }
    assert classify_b3_ticker("PETR3", cfg)["Instrument_Decision_v0_7"] == "PASS"
    assert classify_b3_ticker("ITUB4", cfg)["Instrument_Decision_v0_7"] == "FAIL"
    assert classify_b3_ticker("BPAC11", cfg)["Instrument_Decision_v0_7"] == "FAIL"
    assert classify_b3_ticker("ABCD33", cfg)["Instrument_Decision_v0_7"] == "FAIL"
    assert classify_b3_ticker("NOPE", cfg)["Instrument_Decision_v0_7"] == "NOT_VERIFIED"

    df = pd.DataFrame({
        "Security Code": ["BHP", "CBA", "XYZ"],
        "ISIN": ["AU000000BHP4", "AU000000CBA7", "AU000000XYZ0"],
    })
    scored = score_code_column(df, {"BHP", "CBA"})
    assert scored[0]["Column"] == "Security Code"
    assert scored[0]["Matches_Target_ASX_Codes"] == 2
    print("INSTRUMENT_RESOLUTION_PRIMARY_MARKET_V0_7_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    s6 = load_json(Path(cfg["source_summary_v0_6"]))
    if s6["run_status"] != "INSTRUMENT_RESOLUTION_V0_6_COMPLETE_WITH_REMAINING_REVIEW":
        raise SystemExit("Unexpected v0.6 source status")
    if int(s6["manual_review_rows"]) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.6 manual-review count")
    if int(s6["strict_candidate_rows_v0_6"]) != int(cfg["expected_strict_candidates_v0_6"]):
        raise SystemExit("Unexpected v0.6 strict-candidate count")
    if s6["p0_run"] is not False or s6["alpha_vantage_allowed"] is not False:
        raise SystemExit("v0.6 governance gate failed")

    elig = pd.read_csv(cfg["source_eligibility_v0_6"], keep_default_na=False)
    manual = pd.read_csv(cfg["source_manual_queue_v0_6"], keep_default_na=False)

    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Manual queue row count mismatch")
    if manual["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.6 manual queue")

    b3_seg = cfg["b3"]["segment"]
    asx_seg = cfg["asx_probe"]["segment"]
    b3_rows = manual.loc[manual["Primary_Universe_Index"].eq(b3_seg)].copy()
    asx_rows = manual.loc[manual["Primary_Universe_Index"].eq(asx_seg)].copy()

    if len(b3_rows) != int(cfg["expected_brazil_rows"]):
        raise SystemExit(f"Brazil rows {len(b3_rows)} != expected {cfg['expected_brazil_rows']}")
    if len(asx_rows) != int(cfg["expected_australia_rows"]):
        raise SystemExit(f"Australia rows {len(asx_rows)} != expected {cfg['expected_australia_rows']}")

    b3_decisions = b3_rows["Primary_Ticker"].apply(
        lambda x: pd.Series(classify_b3_ticker(x, cfg["b3"]))
    )
    b3_overlay = pd.concat(
        [b3_rows.reset_index(drop=True), b3_decisions.reset_index(drop=True)],
        axis=1,
    )
    b3_overlay["Instrument_Evidence_URL_v0_7"] = cfg["b3"]["official_manual_url"]
    b3_overlay["Instrument_Evidence_Note_v0_7"] = cfg["b3"]["rule_effective_reference"]

    b3_unresolved = int(b3_overlay["Instrument_Decision_v0_7"].eq("NOT_VERIFIED").sum())
    if b3_unresolved != 0:
        bad = b3_overlay.loc[
            b3_overlay["Instrument_Decision_v0_7"].eq("NOT_VERIFIED"),
            ["WS_ID", "Name", "Primary_Ticker"],
        ].to_dict("records")
        raise SystemExit("B3 official suffix rule did not resolve all 48 frozen Brazil rows: " + json.dumps(bad))

    b3_overlay.to_csv(out_dir / "b3_instrument_resolution_v0.7.csv", index=False)

    # Australia is a one-request reference-data probe only. No instrument
    # decision is made from an unknown workbook schema in this version.
    asx_probe = probe_asx_reference(asx_rows, cfg["asx_probe"], out_dir)

    merged = elig.copy()
    merged["Instrument_Decision_v0_7"] = merged["Instrument_Decision_v0_6"]
    merged["Instrument_Type_Resolved_v0_7"] = merged["Instrument_Type_Resolved_v0_6"]
    merged["Instrument_Resolution_Method_v0_7"] = merged["Instrument_Resolution_Method_v0_6"]
    merged["Instrument_Resolution_Reason_v0_7"] = merged["Instrument_Resolution_Reason_v0_6"]
    merged["Instrument_Evidence_URL_v0_7"] = merged.get("Instrument_Evidence_URL_v0_6", "")
    merged["Instrument_Evidence_Note_v0_7"] = merged.get("Instrument_Evidence_Note_v0_6", "")

    b3_cols = [
        "WS_ID",
        "Instrument_Decision_v0_7",
        "Instrument_Type_Resolved_v0_7",
        "Instrument_Resolution_Method_v0_7",
        "Instrument_Resolution_Reason_v0_7",
        "Instrument_Evidence_URL_v0_7",
        "Instrument_Evidence_Note_v0_7",
    ]
    upd = b3_overlay[b3_cols].set_index("WS_ID")
    idx = merged["WS_ID"].isin(upd.index)
    for c in b3_cols[1:]:
        merged.loc[idx, c] = merged.loc[idx, "WS_ID"].map(upd[c])

    merged["Strict_Eligibility_v0_7"] = merged.apply(strict_status, axis=1)

    remaining = merged.loc[
        merged["Cache_Status"].eq("READY")
        & merged["Liquidity_Gate"].eq("PASS")
        & merged["Instrument_Decision_v0_7"].eq("NOT_VERIFIED")
    ].copy()

    # Every Brazil manual row must have disappeared from the unresolved queue.
    if int(remaining["Primary_Universe_Index"].eq(b3_seg).sum()) != 0:
        raise SystemExit("Brazil remains in manual review after exact B3 resolution")

    expected_remaining = int(cfg["expected_source_manual_rows"]) - int(cfg["expected_brazil_rows"])
    if len(remaining) != expected_remaining:
        raise SystemExit(
            f"Remaining review rows {len(remaining)} != exact expected {expected_remaining}"
        )

    strict_candidates = merged.loc[merged["Strict_Eligibility_v0_7"].eq("PASS")].copy()
    strict_candidates = strict_candidates.sort_values(
        ["MedianTurnover20_EUR", "MedianTurnover60_EUR", "WS_ID"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    strict_candidates.insert(0, "Strict_Candidate_Rank_v0_7", range(1, len(strict_candidates) + 1))

    remaining.to_csv(out_dir / "instrument_manual_review_queue_v0.7.csv", index=False)
    merged.to_csv(out_dir / "eligibility_after_instrument_v0.7.csv", index=False)
    strict_candidates.to_csv(out_dir / "strict_u3k_candidate_after_instrument_v0.7.csv", index=False)

    seg = remaining.groupby("Primary_Universe_Index", dropna=False).size().reset_index(name="Rows")
    seg.to_csv(out_dir / "remaining_review_by_segment_v0.7.csv", index=False)

    b3_counts = (
        b3_overlay["Instrument_Decision_v0_7"].value_counts().to_dict()
    )
    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "INSTRUMENT_RESOLUTION_PRIMARY_MARKET_V0_7_COMPLETE_WITH_REMAINING_REVIEW",
        "source_manual_rows_v0_6": int(len(manual)),
        "brazil_source_rows": int(len(b3_rows)),
        "brazil_pass_rows": int(b3_counts.get("PASS", 0)),
        "brazil_fail_rows": int(b3_counts.get("FAIL", 0)),
        "brazil_unresolved_rows": int(b3_counts.get("NOT_VERIFIED", 0)),
        "australia_source_rows": int(len(asx_rows)),
        "asx_reference_probe": asx_probe,
        "remaining_manual_review_rows": int(len(remaining)),
        "strict_candidates_v0_6": int(cfg["expected_strict_candidates_v0_6"]),
        "strict_candidates_v0_7": int(len(strict_candidates)),
        "strict_freeze_allowed": False,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "external_reference_requests": 1,
        "notes": [
            "All 48 frozen Brazil review rows are resolved only from the official B3 numeric security-type suffix standard.",
            "B3 suffix 03 is ordinary share PASS; 01-02 rights, 04-08 preferred, 09-10 subscription receipts, 11-30 other assets/units/funds and 31-40 BDRs are strict FAIL.",
            "Australia is not blanket-passed because the current S&P/ASX methodology admits ordinary and preferred equity stocks and REITs.",
            "The official ASX monthly ISIN directory is downloaded once and its actual workbook schema plus match coverage are audited. v0.7 does not auto-classify ASX rows from an unverified schema.",
            "The canonical universe master is not mutated.",
            "No stock-price or FX refresh occurs.",
            "P0 remains off."
        ],
    }
    (out_dir / "summary_v0.7.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_primary_market_v0.7.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
