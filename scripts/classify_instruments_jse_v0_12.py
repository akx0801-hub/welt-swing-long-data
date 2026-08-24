#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests

SCHEMA = "WELT_SWING_INSTRUMENT_RESOLUTION_JSE_V0_12"

P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False
CANONICAL_MASTER_MUTATED = False

# Current public JSE isinfull_e layout observed and structurally validated in v0.12:
# 0:12 ISIN
# 12:67 Issuer name
# 67:178 Issue description
# 178:193 Number of securities
# 193:206 Nominal value
# 206:209 Currency code
# 209:219 Instrument type (10 chars)
# 219:227 Alpha code (8 chars, space-padded)
# 227:230 Instrument version (3 chars)
# 230:242 Old XC/legacy field
# 242:262 Issuer registration number
# 262:274 Issuer income-tax number
# 274:277 trailing/filler
EXPECTED_RECORD_LEN = 277

PASS_TYPES = {"Aord", "Bord", "Nord", "Ordinary"}
FAIL_TYPES = {
    "Barrier", "Basket", "Call", "Comp", "Deb", "DepRec", "ETF", "FPL",
    "Index", "LU", "LSU", "NilPL", "Options", "PL", "PPL", "PS", "UT",
    "Vanilla", "Wave", "Discount", "Ediv", "Spread", "Protected", "Variable",
}


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:900]


def extract_isinfull_links(html: str, base_url: str) -> list[str]:
    candidates: list[str] = []
    for m in re.finditer(r"href\s*=\s*[\"']([^\"']+)[\"']", html, flags=re.I):
        href = unescape(m.group(1)).strip()
        if "isinfull_e.zip" in href.lower():
            candidates.append(urljoin(base_url, href))
    for m in re.finditer(
        r"(?P<url>(?:https?://|/)[^\"'<>\\\s]*isinfull_e\.zip[^\"'<>\\\s]*)",
        html,
        flags=re.I,
    ):
        candidates.append(urljoin(base_url, unescape(m.group("url"))))
    out, seen = [], set()
    for u in candidates:
        u = u.replace("\\/", "/")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def decode_member(raw: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), enc
        except Exception:
            pass
    raise ValueError("Unable to decode JSE archive member")


def parse_jse_record(line: str) -> dict[str, str]:
    if len(line) != EXPECTED_RECORD_LEN:
        raise ValueError(f"Unexpected record length {len(line)} != {EXPECTED_RECORD_LEN}")
    rec = {
        "JSE_ISIN": line[0:12].strip(),
        "JSE_Issuer_Name": line[12:67].strip(),
        "JSE_Issue_Description": line[67:178].strip(),
        "JSE_Number_of_Securities": line[178:193].strip(),
        "JSE_Nominal_Value": line[193:206].strip(),
        "JSE_Currency_Code": line[206:209].strip(),
        "JSE_Instrument_Type": line[209:219].strip(),
        "JSE_Alpha_Code": line[219:227].strip(),
        "JSE_Instrument_Version": line[227:230].strip(),
        "JSE_Legacy_Field": line[230:242].strip(),
        "JSE_Issuer_Registration_Number": line[242:262].strip(),
        "JSE_Issuer_Income_Tax_Number": line[262:274].strip(),
        "JSE_Trailing": line[274:277],
    }
    return rec


def parse_jse_archive(content: bytes) -> tuple[pd.DataFrame, dict[str, Any]]:
    zf = zipfile.ZipFile(io.BytesIO(content))
    files = [i for i in zf.infolist() if not i.is_dir()]
    if len(files) != 1:
        raise ValueError(f"Expected exactly one JSE ISIN data member, got {len(files)}")
    raw = zf.read(files[0].filename)
    decoded, encoding = decode_member(raw)
    lines = decoded.splitlines()
    if not lines:
        raise ValueError("JSE ISIN data member is empty")

    lengths = pd.Series([len(x) for x in lines], dtype="int64")
    if not lengths.eq(EXPECTED_RECORD_LEN).all():
        bad = lengths.value_counts().sort_index().to_dict()
        raise ValueError(f"JSE record-length distribution incompatible with v0.12 layout: {bad}")

    records = pd.DataFrame([parse_jse_record(x) for x in lines])
    if records.empty:
        raise ValueError("No parsed JSE records")

    # Structural validation of the fixed-width interpretation.
    isin_ok = records["JSE_ISIN"].str.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", na=False)
    currency_ok = records["JSE_Currency_Code"].str.fullmatch(r"[A-Z]{3}", na=False)
    version_ok = records["JSE_Instrument_Version"].str.fullmatch(r"[A-Z0-9]{3}", na=False)
    alpha_ok = records["JSE_Alpha_Code"].str.fullmatch(r"[A-Z0-9.\-]{1,8}", na=False)
    if float(isin_ok.mean()) < 0.99:
        raise ValueError(f"ISIN structural coverage too low: {isin_ok.mean():.6f}")
    if float(currency_ok.mean()) < 0.99:
        raise ValueError(f"Currency structural coverage too low: {currency_ok.mean():.6f}")
    if float(version_ok.mean()) < 0.99:
        raise ValueError(f"Version structural coverage too low: {version_ok.mean():.6f}")
    if float(alpha_ok.mean()) < 0.99:
        raise ValueError(f"Alpha structural coverage too low: {alpha_ok.mean():.6f}")

    meta = {
        "archive_member": files[0].filename,
        "archive_member_bytes": int(files[0].file_size),
        "encoding": encoding,
        "record_rows": int(len(records)),
        "record_length": EXPECTED_RECORD_LEN,
        "isin_structural_coverage": float(isin_ok.mean()),
        "currency_structural_coverage": float(currency_ok.mean()),
        "version_structural_coverage": float(version_ok.mean()),
        "alpha_structural_coverage": float(alpha_ok.mean()),
    }
    return records, meta


def target_alpha(row: pd.Series) -> str:
    # ZA rows currently have blank Primary_Ticker. Use the already-frozen Yahoo symbol
    # only as a lookup key, then require an exact alpha-code match in the official JSE file.
    p = txt(row.get("Primary_Ticker")).upper()
    if p:
        return p
    y = txt(row.get("Yahoo_Symbol")).upper()
    if y.endswith(".JO"):
        return y[:-3]
    return ""


def classify_type(value: Any) -> dict[str, str]:
    it = txt(value)
    if it in PASS_TYPES:
        return {
            "Instrument_Decision_v0_12": "PASS",
            "Instrument_Type_Resolved_v0_12": f"JSE_{it.upper()}",
            "Instrument_Resolution_Reason_v0_12": "JSE_OFFICIAL_INSTRUMENT_TYPE_IS_ORDINARY_SHARE_CLASS",
        }
    if it in FAIL_TYPES:
        return {
            "Instrument_Decision_v0_12": "FAIL",
            "Instrument_Type_Resolved_v0_12": f"JSE_{it.upper()}",
            "Instrument_Resolution_Reason_v0_12": "JSE_OFFICIAL_INSTRUMENT_TYPE_OUTSIDE_STRICT_COMMON_ORDINARY_GATE",
        }
    return {
        "Instrument_Decision_v0_12": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_12": "UNKNOWN",
        "Instrument_Resolution_Reason_v0_12": "JSE_INSTRUMENT_TYPE_NOT_DETERMINISTIC_UNDER_V0_12_RULES",
    }


def final_strict_status(row: pd.Series) -> str:
    if txt(row.get("Cache_Status")) != "READY":
        return "FAIL"
    lg = txt(row.get("Liquidity_Gate"))
    if lg != "PASS":
        return "FAIL" if lg in {"FAIL", "FAIL_STRICT"} else "NOT_VERIFIED"
    if txt(row.get("Scalable_Gate")) == "FAIL":
        return "FAIL"
    d = txt(row.get("Instrument_Decision_v0_12"))
    if d == "PASS":
        return "PASS"
    if d == "FAIL":
        return "FAIL"
    return "NOT_VERIFIED"


def self_test() -> None:
    assert classify_type("Ordinary")["Instrument_Decision_v0_12"] == "PASS"
    assert classify_type("Aord")["Instrument_Decision_v0_12"] == "PASS"
    assert classify_type("PS")["Instrument_Decision_v0_12"] == "FAIL"
    assert classify_type("DepRec")["Instrument_Decision_v0_12"] == "FAIL"
    assert classify_type("Securities")["Instrument_Decision_v0_12"] == "NOT_VERIFIED"

    # Synthetic current-layout record based on the structure observed in v0.11.
    line = (
        "ZAE000320990"
        + "10X FUND MANAGERS (RF) PROPRIETARY LIMITED".ljust(55)
        + "10X Income Actively Managed ETF".ljust(111)
        + "000000076124264"
        + "0000000000000"
        + "ZAC"
        + "ETF".ljust(10)
        + "INCOME".ljust(8)
        + "000"
        + "".ljust(12)
        + "2006/006498/07".ljust(20)
        + "".ljust(12)
        + "".ljust(3)
    )
    assert len(line) == EXPECTED_RECORD_LEN
    r = parse_jse_record(line)
    assert r["JSE_Instrument_Type"] == "ETF"
    assert r["JSE_Alpha_Code"] == "INCOME"
    assert r["JSE_Instrument_Version"] == "000"
    print("INSTRUMENT_RESOLUTION_JSE_V0_12_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    s11 = load_json(Path(cfg["source_summary_v0_11"]))
    if s11.get("schema") != "WELT_SWING_JSE_ISIN_BULK_PROBE_V0_11":
        raise SystemExit("Wrong v0.11 source schema")
    if s11.get("run_status") != "JSE_ISIN_BULK_PROBE_V0_11_COMPLETE_WITH_EVIDENCE":
        raise SystemExit("v0.11 did not materialize JSE evidence")
    if int(s11.get("remaining_manual_rows_v0_11", -1)) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.11 manual count")
    if int(s11.get("strict_candidates_v0_11", -1)) != int(cfg["expected_source_strict_candidates"]):
        raise SystemExit("Unexpected v0.11 strict candidate count")
    if s11.get("p0_run") is not False or s11.get("alpha_vantage_allowed") is not False:
        raise SystemExit("v0.11 governance gate failed")

    manual = pd.read_csv(cfg["source_manual_queue_v0_11"], keep_default_na=False, dtype=str)
    full10 = pd.read_csv(cfg["source_full_eligibility_v0_10"], keep_default_na=False, dtype=str)

    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Manual queue row count changed")
    if manual["WS_ID"].duplicated().any() or full10["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in source data")

    za = manual.loc[manual["Primary_Universe_Index"].eq("ZA_TOP40")].copy()
    if len(za) != int(cfg["expected_za_target_rows"]):
        raise SystemExit(f"ZA target rows {len(za)} != expected {cfg['expected_za_target_rows']}")
    za["_TARGET_ALPHA"] = za.apply(target_alpha, axis=1)
    if za["_TARGET_ALPHA"].eq("").any() or za["_TARGET_ALPHA"].duplicated().any():
        raise SystemExit("ZA target lookup-alpha keys missing or duplicated")

    # Existing ZA rows must still be unresolved before v0.12.
    base = full10.loc[full10["WS_ID"].isin(set(za["WS_ID"])), ["WS_ID", "Instrument_Decision_v0_10"]]
    if not base["Instrument_Decision_v0_10"].astype(str).eq("NOT_VERIFIED").all():
        raise SystemExit("ZA target contains pre-existing v0.10 PASS/FAIL decision")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36 WeltSwingLongDEV/0.12",
        "Accept-Language": "en-US,en;q=0.8",
    })
    src = cfg["jse_source"]
    external_requests = 0
    source_status = {
        "Page_URL": src["folder_url"],
        "Page_HTTP_Status": "",
        "ZIP_URL": "",
        "ZIP_HTTP_Status": "",
        "ZIP_SHA256": "",
        "Probe_Status": "SOURCE_BLOCKED",
        "Error": "",
    }
    records = None
    meta = {}

    try:
        external_requests += 1
        page = session.get(src["folder_url"], timeout=int(cfg["request_timeout_seconds"]))
        source_status["Page_HTTP_Status"] = int(page.status_code)
        page.raise_for_status()
        links = extract_isinfull_links(page.text, src["folder_url"])
        if len(links) != 1:
            raise ValueError(f"Expected exactly one isinfull_e.zip link, got {len(links)}")
        zurl = links[0]
        source_status["ZIP_URL"] = zurl

        if external_requests >= int(cfg["max_external_reference_requests"]):
            raise RuntimeError("Request budget exhausted before ZIP")

        external_requests += 1
        zresp = session.get(zurl, timeout=int(cfg["request_timeout_seconds"]))
        source_status["ZIP_HTTP_Status"] = int(zresp.status_code)
        source_status["ZIP_SHA256"] = sha256_bytes(zresp.content) if zresp.content else ""
        zresp.raise_for_status()
        records, meta = parse_jse_archive(zresp.content)
        source_status["Probe_Status"] = "JSE_REFERENCE_PARSED"
    except Exception as exc:
        source_status["Error"] = compact_error(exc)

    if external_requests > int(cfg["max_external_reference_requests"]):
        raise SystemExit("External request budget exceeded")

    if records is None:
        # Fail closed: no classification, preserve full queue and current strict set.
        manual.to_csv(out / "instrument_manual_review_queue_v0.12.csv", index=False)
        full10.to_csv(out / "eligibility_after_instrument_v0.12.csv", index=False)
        strict10 = pd.read_csv(cfg["source_strict_candidates_v0_10"], keep_default_na=False, dtype=str)
        strict10.to_csv(out / "strict_u3k_candidate_after_instrument_v0.12.csv", index=False)
        za["Instrument_Decision_v0_12"] = "NOT_VERIFIED"
        za["Instrument_Type_Resolved_v0_12"] = "UNKNOWN"
        za["Instrument_Resolution_Reason_v0_12"] = "JSE_OFFICIAL_BULK_SOURCE_NOT_MATERIALIZED_OR_LAYOUT_INVALID"
        za.to_csv(out / "jse_security_type_resolution_v0.12.csv", index=False)
        new_pass = za.iloc[0:0].copy()
        new_fail = za.iloc[0:0].copy()
        unresolved = za.copy()
        strict_count = int(cfg["expected_source_strict_candidates"])
        remaining_count = int(len(manual))
        matched_rows = 0
        parsed_rows = 0
    else:
        records.to_csv(out / "jse_reference_parsed_v0.12.csv", index=False)
        type_counts = records.groupby("JSE_Instrument_Type", dropna=False).size().reset_index(name="Rows")
        type_counts.to_csv(out / "jse_instrument_type_counts_v0.12.csv", index=False)

        # Exact current-alpha match. If multiple versions exist for a target alpha, require exactly
        # one record with version 000; otherwise remain unresolved.
        candidate = records.loc[records["JSE_Alpha_Code"].isin(set(za["_TARGET_ALPHA"]))].copy()
        candidate.to_csv(out / "jse_target_reference_candidates_v0.12.csv", index=False)

        selected_rows = []
        for _, t in za.iterrows():
            c = candidate.loc[candidate["JSE_Alpha_Code"].eq(t["_TARGET_ALPHA"])].copy()
            c0 = c.loc[c["JSE_Instrument_Version"].eq("000")].copy()
            chosen = c0 if len(c0) == 1 else (c if len(c) == 1 else c.iloc[0:0])
            row = t.to_dict()
            if len(chosen) == 1:
                rr = chosen.iloc[0]
                row.update({k: rr[k] for k in records.columns})
                row["JSE_Match_Status"] = "MATCHED_EXACT_ALPHA"
            else:
                row["JSE_Match_Status"] = "NOT_UNIQUELY_MATCHED"
                for k in records.columns:
                    row[k] = ""
            selected_rows.append(row)

        resolution = pd.DataFrame(selected_rows)
        decisions = resolution["JSE_Instrument_Type"].map(classify_type)
        dec_df = pd.DataFrame(decisions.tolist())
        resolution = pd.concat([resolution.reset_index(drop=True), dec_df.reset_index(drop=True)], axis=1)

        bad_match = resolution["JSE_Match_Status"].ne("MATCHED_EXACT_ALPHA")
        resolution.loc[bad_match, "Instrument_Decision_v0_12"] = "NOT_VERIFIED"
        resolution.loc[bad_match, "Instrument_Type_Resolved_v0_12"] = "UNKNOWN"
        resolution.loc[bad_match, "Instrument_Resolution_Reason_v0_12"] = "NO_UNIQUE_EXACT_JSE_ALPHA_MATCH"

        resolution["Instrument_Resolution_Method_v0_12"] = "JSE_OFFICIAL_ISINFULL_E_INSTRUMENT_TYPE"
        resolution["Instrument_Evidence_URL_v0_12"] = src["folder_url"]
        resolution["Instrument_Evidence_Note_v0_12"] = (
            "Official JSE Equities ISIN bulk file. v0.12 validates the current 277-character "
            "fixed-width structure before reading Instrument Type and Alpha Code. PASS is limited "
            "to JSE Aord/Bord/Nord/Ordinary; clearly non-ordinary types are FAIL; all other types remain NOT_VERIFIED."
        )
        resolution.to_csv(out / "jse_security_type_resolution_v0.12.csv", index=False)

        new_pass = resolution.loc[resolution["Instrument_Decision_v0_12"].eq("PASS")].copy()
        new_fail = resolution.loc[resolution["Instrument_Decision_v0_12"].eq("FAIL")].copy()
        unresolved = resolution.loc[resolution["Instrument_Decision_v0_12"].eq("NOT_VERIFIED")].copy()
        new_pass.to_csv(out / "jse_new_pass_v0.12.csv", index=False)
        new_fail.to_csv(out / "jse_new_fail_v0.12.csv", index=False)
        unresolved.to_csv(out / "jse_unresolved_v0.12.csv", index=False)

        # Carry v0.10 decisions forward and overlay only ZA v0.12 decisions.
        full = full10.copy()
        carry = {
            "Instrument_Decision_v0_12": "Instrument_Decision_v0_10",
            "Instrument_Type_Resolved_v0_12": "Instrument_Type_Resolved_v0_10",
            "Instrument_Resolution_Method_v0_12": "Instrument_Resolution_Method_v0_10",
            "Instrument_Resolution_Reason_v0_12": "Instrument_Resolution_Reason_v0_10",
            "Instrument_Evidence_URL_v0_12": "Instrument_Evidence_URL_v0_10",
            "Instrument_Evidence_Note_v0_12": "Instrument_Evidence_Note_v0_10",
        }
        for new_col, old_col in carry.items():
            full[new_col] = full[old_col] if old_col in full.columns else ""

        overlay_cols = [
            "WS_ID",
            "Instrument_Decision_v0_12",
            "Instrument_Type_Resolved_v0_12",
            "Instrument_Resolution_Method_v0_12",
            "Instrument_Resolution_Reason_v0_12",
            "Instrument_Evidence_URL_v0_12",
            "Instrument_Evidence_Note_v0_12",
        ]
        overlay = resolution[overlay_cols].set_index("WS_ID")
        full = full.set_index("WS_ID")
        for col in overlay_cols[1:]:
            full.loc[overlay.index, col] = overlay[col]
        full = full.reset_index()
        full["Strict_Eligibility_v0_12"] = full.apply(final_strict_status, axis=1)

        strict = full.loc[full["Strict_Eligibility_v0_12"].eq("PASS")].copy()
        strict["MedianTurnover20_EUR"] = pd.to_numeric(strict["MedianTurnover20_EUR"], errors="coerce")
        strict["MedianTurnover60_EUR"] = pd.to_numeric(strict["MedianTurnover60_EUR"], errors="coerce")
        strict = strict.sort_values(
            ["MedianTurnover20_EUR", "MedianTurnover60_EUR", "WS_ID"],
            ascending=[False, False, True],
            kind="mergesort",
        )
        strict.insert(0, "Strict_Candidate_Rank_v0_12", range(1, len(strict) + 1))

        resolved_ids = set(
            resolution.loc[resolution["Instrument_Decision_v0_12"].isin(["PASS", "FAIL"]), "WS_ID"].astype(str)
        )
        remaining = manual.loc[~manual["WS_ID"].astype(str).isin(resolved_ids)].copy()

        expected_strict = int(cfg["expected_source_strict_candidates"]) + len(new_pass)
        if len(strict) != expected_strict:
            raise SystemExit(f"Strict arithmetic failed: {len(strict)} != {expected_strict}")
        if len(remaining) != int(cfg["expected_source_manual_rows"]) - len(resolved_ids):
            raise SystemExit("Remaining manual arithmetic failed")

        full.to_csv(out / "eligibility_after_instrument_v0.12.csv", index=False)
        strict.to_csv(out / "strict_u3k_candidate_after_instrument_v0.12.csv", index=False)
        remaining.to_csv(out / "instrument_manual_review_queue_v0.12.csv", index=False)

        seg = remaining.groupby("Primary_Universe_Index").size().reset_index(name="Rows")
        seg.to_csv(out / "remaining_review_by_segment_v0.12.csv", index=False)

        strict_count = len(strict)
        remaining_count = len(remaining)
        matched_rows = int(resolution["JSE_Match_Status"].eq("MATCHED_EXACT_ALPHA").sum())
        parsed_rows = int(len(records))

    pd.DataFrame([source_status]).to_csv(out / "source_status_v0.12.csv", index=False)

    if records is None:
        seg = manual.groupby("Primary_Universe_Index").size().reset_index(name="Rows")
        seg.to_csv(out / "remaining_review_by_segment_v0.12.csv", index=False)
        pd.DataFrame(columns=["JSE_Instrument_Type", "Rows"]).to_csv(
            out / "jse_instrument_type_counts_v0.12.csv", index=False
        )
        new_pass.to_csv(out / "jse_new_pass_v0.12.csv", index=False)
        new_fail.to_csv(out / "jse_new_fail_v0.12.csv", index=False)
        unresolved.to_csv(out / "jse_unresolved_v0.12.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": (
            "INSTRUMENT_RESOLUTION_JSE_V0_12_COMPLETE_WITH_REMAINING_REVIEW"
            if records is not None
            else "INSTRUMENT_RESOLUTION_JSE_V0_12_COMPLETE_WITH_SOURCE_OR_LAYOUT_BLOCK"
        ),
        "source_manual_rows_v0_11": int(len(manual)),
        "za_target_rows": int(len(za)),
        "jse_source_status": source_status["Probe_Status"],
        "jse_page_http_status": source_status["Page_HTTP_Status"],
        "jse_zip_http_status": source_status["ZIP_HTTP_Status"],
        "jse_reference_rows": int(parsed_rows),
        "jse_matched_rows": int(matched_rows),
        "jse_pass_rows": int(len(new_pass)),
        "jse_fail_rows": int(len(new_fail)),
        "jse_unresolved_rows": int(len(unresolved)),
        "remaining_manual_rows_v0_12": int(remaining_count),
        "strict_candidates_v0_11": int(cfg["expected_source_strict_candidates"]),
        "strict_candidates_v0_12": int(strict_count),
        "strict_freeze_allowed": bool(remaining_count == 0),
        "external_reference_requests": int(external_requests),
        "max_external_reference_requests": int(cfg["max_external_reference_requests"]),
        "request_bound_respected": bool(external_requests <= int(cfg["max_external_reference_requests"])),
        "record_layout_validated": bool(records is not None),
        "record_layout_meta": meta,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "source_error": source_status["Error"],
        "notes": [
            "v0.12 consumes the frozen v0.11 queue and v0.10 full eligibility state.",
            "Only two official JSE requests are permitted: folder page plus current isinfull_e.zip.",
            "The current JSE fixed-width record structure must validate before any Instrument Type is read.",
            "ZA Primary_Ticker is currently blank; the frozen Yahoo .JO symbol is used only as a lookup key and must exact-match the official JSE Alpha Code.",
            "Strict PASS is limited to JSE Aord, Bord, Nord and Ordinary types.",
            "Depository receipts, funds, linked units, preference shares and other clearly non-ordinary types are strict FAIL.",
            "Generic or unrecognized types remain NOT_VERIFIED.",
            "P0 remains off and the canonical master is not mutated.",
        ],
    }
    (out / "summary_v0.12.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_jse_v0.12.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
