#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import pandas as pd
import requests
from pypdf import PdfReader

SCHEMA = "WELT_SWING_SP_TSX_SEMANTICS_REMEDIATION_V0_15"

def norm(s: str) -> str:
    s = unescape(s or "").replace("’","'").replace("‘","'").replace("–","-").replace("—","-")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()

def decode_response(r: requests.Response) -> str:
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "pdf" in ctype or r.content[:4] == b"%PDF":
        reader = PdfReader(io.BytesIO(r.content))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:
            return r.content.decode(enc)
        except Exception:
            pass
    raise ValueError("unable to decode response")

def probe(session, spec, timeout):
    row = {
        "Source_Name": spec["name"],
        "Source_URL": spec["url"],
        "HTTP_Status": "",
        "Content_Type": "",
        "Bytes": 0,
        "SHA256": "",
        "Status": "REQUEST_ERROR",
        "Required_Phrases_Total": len(spec["required_phrases"]),
        "Required_Phrases_Matched": 0,
        "Error": "",
    }
    text = ""
    try:
        r = session.get(spec["url"], timeout=timeout)
        row["HTTP_Status"] = int(r.status_code)
        row["Content_Type"] = r.headers.get("Content-Type","")
        row["Bytes"] = len(r.content)
        row["SHA256"] = hashlib.sha256(r.content).hexdigest() if r.content else ""
        r.raise_for_status()
        text = decode_response(r)
        n = norm(text)
        matched = [p for p in spec["required_phrases"] if norm(p) in n]
        row["Required_Phrases_Matched"] = len(matched)
        row["Status"] = "SEMANTICS_VALIDATED" if len(matched) == len(spec["required_phrases"]) else "CONTENT_OK_PHRASES_INCOMPLETE"
        if row["Status"] != "SEMANTICS_VALIDATED":
            missing = [p for p in spec["required_phrases"] if p not in matched]
            row["Error"] = "Missing required phrases: " + " | ".join(missing)
    except Exception as e:
        row["Error"] = f"{type(e).__name__}: {e}"[:900]
    return text, row

def self_test():
    html = "The S&P/TSX Composite is the principal broad market measure. It includes common stocks and income trust units. The index contains all of the income trust constituents from its parent index."
    n = norm(html)
    assert "includes common stocks and income trust units" in n
    assert "contains all of the income trust constituents" in n
    pdf = "Preferred shares Exchangeable shares Warrants Installment receipts USD-denominated securities"
    n2 = norm(pdf)
    for p in ["preferred shares","exchangeable shares","warrants","installment receipts"]:
        assert p in n2
    print("SP_TSX_SEMANTICS_REMEDIATION_V0_15_SELF_TEST_PASS")

def run(cfg_path: Path):
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    s14 = json.loads(Path(cfg["source_summary_v0_14"]).read_text(encoding="utf-8"))
    assert s14["schema"] == "WELT_SWING_INSTRUMENT_RESOLUTION_TMX_V0_14"
    assert s14["run_status"] == "INSTRUMENT_RESOLUTION_TMX_V0_14_COMPLETE_WITH_SOURCE_BLOCK"
    assert s14["remaining_manual_rows_v0_14"] == 650
    assert s14["strict_candidates_v0_14"] == 2037
    assert s14["tmx_pass_rows"] == 0 and s14["tmx_fail_rows"] == 0
    assert s14["p0_run"] is False and s14["alpha_vantage_allowed"] is False

    manual = pd.read_csv(cfg["source_manual_queue_v0_14"], keep_default_na=False, dtype=str)
    assert len(manual) == 650
    assert manual["WS_ID"].is_unique
    assert (manual["Primary_Universe_Index"] == "CA_TSX").sum() == 105
    manual.to_csv(out/"instrument_manual_review_queue_v0.15.csv", index=False)

    session = requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 WeltSwingLongDEV/0.15","Accept-Language":"en-US,en;q=0.8"})

    rows = []
    text_meta = []
    for key in ["methodology_article","localized_methodology_pdf"]:
        text, row = probe(session, cfg["official_sources"][key], int(cfg["request_timeout_seconds"]))
        rows.append(row)
        text_meta.append({
            "Source_Name": row["Source_Name"],
            "Normalized_Text_Chars": len(norm(text)),
            "Preview": re.sub(r"\s+"," ",text)[:5000],
        })

    pd.DataFrame(rows).to_csv(out/"source_status_v0.15.csv", index=False)
    pd.DataFrame(text_meta).to_csv(out/"source_text_preview_v0.15.csv", index=False)

    article_ok = rows[0]["Status"] == "SEMANTICS_VALIDATED"
    localized_pdf_ok = rows[1]["Status"] == "SEMANTICS_VALIDATED"

    summary = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run_status": (
            "SP_TSX_SEMANTICS_REMEDIATION_V0_15_COMPLETE_WITH_FULL_EVIDENCE"
            if article_ok and localized_pdf_ok
            else "SP_TSX_SEMANTICS_REMEDIATION_V0_15_COMPLETE_WITH_PARTIAL_EVIDENCE"
            if article_ok or localized_pdf_ok
            else "SP_TSX_SEMANTICS_REMEDIATION_V0_15_COMPLETE_WITH_SOURCE_BLOCK"
        ),
        "source_manual_rows_v0_14": 650,
        "ca_target_rows": 105,
        "methodology_article_validated": article_ok,
        "localized_methodology_pdf_validated": localized_pdf_ok,
        "strict_candidates_v0_14": 2037,
        "strict_candidates_v0_15": 2037,
        "remaining_manual_rows_v0_15": 650,
        "decisions_changed": 0,
        "external_reference_requests": 2,
        "max_external_reference_requests": 2,
        "request_bound_respected": True,
        "strict_freeze_allowed": False,
        "p0_run": False,
        "productive_trading_authority": False,
        "alpha_vantage_allowed": False,
        "price_downloads_performed": False,
        "fx_downloads_performed": False,
        "web_calls_per_security": False,
        "canonical_master_mutated": False,
        "notes": [
            "v0.15 is evidence-only and makes zero instrument decisions.",
            "It remediates the S&P/TSX semantics source block observed in v0.14.",
            "The public S&P methodology article must validate the common-stock/income-trust relationship.",
            "A localized official S&P methodology PDF path is probed for the explicit exclusion list.",
            "The frozen 650-row queue and 2,037 strict candidates are preserved.",
            "No per-security request is made; P0 remains off."
        ]
    }
    (out/"summary_v0.15.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_sp_tsx_remediation_v0.15.json")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    else:
        run(Path(a.config))

if __name__ == "__main__":
    main()
