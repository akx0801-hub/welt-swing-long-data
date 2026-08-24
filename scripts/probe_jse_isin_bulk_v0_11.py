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

SCHEMA = "WELT_SWING_JSE_ISIN_BULK_PROBE_V0_11"

P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False
CANONICAL_MASTER_MUTATED = False
DECISIONS_CHANGED = 0


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

    out: list[str] = []
    seen: set[str] = set()
    for u in candidates:
        u = u.replace("\\/", "/")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def inspect_zip(content: bytes) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    zf = zipfile.ZipFile(io.BytesIO(content))
    members = []
    samples = []

    for info in zf.infolist():
        members.append({
            "Archive_Member": info.filename,
            "Compressed_Bytes": int(info.compress_size),
            "Uncompressed_Bytes": int(info.file_size),
            "CRC": int(info.CRC),
        })

        if info.is_dir():
            continue

        suffix = Path(info.filename).suffix.lower()
        if suffix not in {".txt", ".csv", ".dat", ""}:
            continue

        raw = zf.read(info.filename)
        decoded = None
        encoding = ""
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                decoded = raw.decode(enc)
                encoding = enc
                break
            except Exception:
                pass
        if decoded is None:
            continue

        for i, line in enumerate(decoded.splitlines()[:20], start=1):
            samples.append({
                "Archive_Member": info.filename,
                "Encoding": encoding,
                "Sample_Line_Number": i,
                "Sample_Text": line[:2000],
            })

    member_df = pd.DataFrame(members)
    sample_df = pd.DataFrame(samples)
    meta = {
        "archive_members": int(len(members)),
        "sample_rows": int(len(samples)),
        "member_names": [m["Archive_Member"] for m in members],
    }
    return member_df, sample_df, meta


def self_test() -> None:
    html = '<a href="/files/a.zip">x</a><a href="/Content/Reference/isinfull_e.zip">isinfull_e.zip</a>'
    links = extract_isinfull_links(html, "https://clientportal.jse.co.za/downloadable-files")
    assert links == ["https://clientportal.jse.co.za/Content/Reference/isinfull_e.zip"]

    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("isinfull_e.txt", "AAA|ZAE000000001|Example\nBBB|ZAE000000002|Example 2\n")
    members, samples, meta = inspect_zip(bio.getvalue())
    assert meta["archive_members"] == 1
    assert members.iloc[0]["Archive_Member"] == "isinfull_e.txt"
    assert len(samples) == 2
    print("JSE_ISIN_BULK_PROBE_V0_11_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    s10 = load_json(Path(cfg["source_summary_v0_10"]))
    if s10.get("schema") != "WELT_SWING_INSTRUMENT_RESOLUTION_KRX_V0_10":
        raise SystemExit("Wrong v0.10 source schema")
    if s10.get("run_status") not in {
        "INSTRUMENT_RESOLUTION_KRX_V0_10_COMPLETE_WITH_REMAINING_REVIEW",
        "INSTRUMENT_RESOLUTION_KRX_V0_10_COMPLETE_WITH_SOURCE_BLOCK",
    }:
        raise SystemExit("Unexpected v0.10 run status")
    if int(s10.get("remaining_manual_rows_v0_10", -1)) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.10 manual count")
    if int(s10.get("strict_candidates_v0_10", -1)) != int(cfg["expected_source_strict_candidates"]):
        raise SystemExit("Unexpected v0.10 strict candidate count")
    if s10.get("p0_run") is not False or s10.get("alpha_vantage_allowed") is not False:
        raise SystemExit("v0.10 governance gate failed")

    manual = pd.read_csv(cfg["source_manual_queue_v0_10"], keep_default_na=False, dtype=str)
    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Manual queue row count changed")
    if manual["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.10 manual queue")

    za = manual.loc[manual["Primary_Universe_Index"].eq("ZA_TOP40")].copy()
    if len(za) != int(cfg["expected_za_target_rows"]):
        raise SystemExit(f"ZA target rows {len(za)} != expected {cfg['expected_za_target_rows']}")

    manual.to_csv(out / "instrument_manual_review_queue_v0.11.csv", index=False)
    za.to_csv(out / "za_target_rows_v0.11.csv", index=False)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36 WeltSwingLongDEV/0.11",
        "Accept-Language": "en-US,en;q=0.8",
    })

    src = cfg["jse_source"]
    external_requests = 0
    page_status: dict[str, Any] = {
        "Page_URL": src["folder_url"],
        "Page_HTTP_Status": "",
        "Page_Content_Type": "",
        "Page_Bytes": 0,
        "Page_SHA256": "",
        "Link_Count": 0,
        "Selected_ZIP_URL": "",
        "ZIP_HTTP_Status": "",
        "ZIP_Content_Type": "",
        "ZIP_Bytes": 0,
        "ZIP_SHA256": "",
        "Probe_Status": "SOURCE_BLOCKED",
        "Error": "",
    }

    zip_meta: dict[str, Any] = {"archive_members": 0, "sample_rows": 0, "member_names": []}

    try:
        external_requests += 1
        page = session.get(src["folder_url"], timeout=int(cfg["request_timeout_seconds"]))
        page_status["Page_HTTP_Status"] = int(page.status_code)
        page_status["Page_Content_Type"] = page.headers.get("Content-Type", "")
        page_status["Page_Bytes"] = int(len(page.content))
        page_status["Page_SHA256"] = sha256_bytes(page.content) if page.content else ""
        page.raise_for_status()

        links = extract_isinfull_links(page.text, src["folder_url"])
        page_status["Link_Count"] = int(len(links))
        pd.DataFrame({"Discovered_URL": links}).to_csv(
            out / "jse_discovered_isinfull_links_v0.11.csv", index=False
        )

        if not links:
            raise ValueError("No isinfull_e.zip link discovered in official JSE Equities ISIN folder")

        selected = links[0]
        page_status["Selected_ZIP_URL"] = selected

        if external_requests >= int(cfg["max_external_reference_requests"]):
            raise RuntimeError("Request budget exhausted before ZIP download")

        external_requests += 1
        zresp = session.get(selected, timeout=int(cfg["request_timeout_seconds"]))
        page_status["ZIP_HTTP_Status"] = int(zresp.status_code)
        page_status["ZIP_Content_Type"] = zresp.headers.get("Content-Type", "")
        page_status["ZIP_Bytes"] = int(len(zresp.content))
        page_status["ZIP_SHA256"] = sha256_bytes(zresp.content) if zresp.content else ""
        zresp.raise_for_status()

        members, samples, zip_meta = inspect_zip(zresp.content)
        members.to_csv(out / "jse_isinfull_archive_members_v0.11.csv", index=False)
        samples.to_csv(out / "jse_isinfull_text_samples_v0.11.csv", index=False)
        page_status["Probe_Status"] = "JSE_ISINFULL_ZIP_PARSED"

    except Exception as exc:
        page_status["Error"] = compact_error(exc)

    if external_requests > int(cfg["max_external_reference_requests"]):
        raise SystemExit("External request budget exceeded")

    pd.DataFrame([page_status]).to_csv(out / "source_status_v0.11.csv", index=False)

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": (
            "JSE_ISIN_BULK_PROBE_V0_11_COMPLETE_WITH_EVIDENCE"
            if page_status["Probe_Status"] == "JSE_ISINFULL_ZIP_PARSED"
            else "JSE_ISIN_BULK_PROBE_V0_11_COMPLETE_WITH_SOURCE_BLOCK"
        ),
        "source_manual_rows_v0_10": int(len(manual)),
        "za_target_rows": int(len(za)),
        "strict_candidates_v0_10": int(cfg["expected_source_strict_candidates"]),
        "strict_candidates_v0_11": int(cfg["expected_source_strict_candidates"]),
        "remaining_manual_rows_v0_11": int(len(manual)),
        "decisions_changed": DECISIONS_CHANGED,
        "jse_probe_status": page_status["Probe_Status"],
        "jse_page_http_status": page_status["Page_HTTP_Status"],
        "jse_zip_http_status": page_status["ZIP_HTTP_Status"],
        "jse_discovered_zip_links": int(page_status["Link_Count"]),
        "jse_archive_members": int(zip_meta["archive_members"]),
        "external_reference_requests": int(external_requests),
        "max_external_reference_requests": int(cfg["max_external_reference_requests"]),
        "request_bound_respected": bool(external_requests <= int(cfg["max_external_reference_requests"])),
        "strict_freeze_allowed": False,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "source_error": page_status["Error"],
        "notes": [
            "v0.11 is evidence acquisition only. It makes zero instrument decisions.",
            "The frozen v0.10 manual-review queue is preserved as rows/values.",
            "Only the official JSE Equities ISIN downloadable-files folder is probed.",
            "At most two external requests are allowed: folder page and discovered isinfull_e.zip.",
            "No per-security requests are made.",
            "If the archive is acquired, v0.12 may define a deterministic classifier only after file fields and official semantics are verified.",
            "P0 remains off and the canonical master is not mutated.",
        ],
    }
    (out / "summary_v0.11.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_jse_probe_v0.11.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
