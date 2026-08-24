#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests

SCHEMA = "WELT_SWING_PRIMARY_MARKET_BUNDLE_PROBE_V0_9"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:500]


def normalized_label(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", txt(value).lower())


def unique_columns(values: list[Any]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for i, raw in enumerate(values):
        base = txt(raw) or f"COL_{i}"
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.append(base if n == 0 else f"{base}__{n+1}")
    return out


def detect_header_row(frame: pd.DataFrame, required_tokens: set[str], max_rows: int = 40) -> int:
    for idx in range(min(max_rows, len(frame))):
        labels = {normalized_label(v) for v in frame.iloc[idx].tolist()}
        if required_tokens & labels:
            return idx
    raise ValueError(f"header row not found for tokens={sorted(required_tokens)}")


def norm_hk_code(value: Any) -> str:
    s = txt(value)
    if not s:
        return ""
    if re.fullmatch(r"\d+(?:\.0+)?", s):
        return f"{int(float(s)):05d}"
    digits = re.sub(r"\D", "", s)
    if digits:
        return digits.zfill(5)[-5:]
    return s.upper()


def norm_kr_code(value: Any) -> str:
    s = re.sub(r"\D", "", txt(value))
    return s.zfill(6)[-6:] if s else ""


def extract_candidate_links(html: str, base_url: str, keywords: list[str]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in re.finditer(
        r"<a\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        html,
        flags=re.I | re.S,
    ):
        href = unescape(m.group(1)).strip()
        label = re.sub(r"<[^>]+>", " ", unescape(m.group(2)))
        label = re.sub(r"\s+", " ", label).strip()
        absolute = urljoin(base_url, href)
        hay = f"{label} {absolute}".lower()
        if not any(k.lower() in hay for k in keywords):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        candidates.append({"label": label[:250], "url": absolute[:1000]})
    return candidates


def empty_match_frame(target: pd.DataFrame, prefix: str) -> pd.DataFrame:
    cols = [
        "WS_ID",
        "Name",
        "Primary_Universe_Index",
        "Primary_MIC",
        "Primary_Ticker",
        "Yahoo_Symbol",
        f"{prefix}_Match_Status",
        f"{prefix}_Match_Key",
    ]
    return pd.DataFrame(columns=cols)


def match_hkex(content: bytes, target: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = pd.read_excel(io.BytesIO(content), header=None, engine="openpyxl", dtype=object)
    header_idx = detect_header_row(raw, {"stockcode", "stockno", "code"})
    columns = unique_columns(raw.iloc[header_idx].tolist())
    ref = raw.iloc[header_idx + 1 :].copy()
    ref.columns = columns
    ref = ref.dropna(how="all").reset_index(drop=True)

    code_col = next(
        (
            c
            for c in ref.columns
            if normalized_label(c) in {"stockcode", "stockno", "code"}
        ),
        None,
    )
    if code_col is None:
        raise ValueError(f"HKEX stock-code column missing; columns={list(ref.columns)[:80]}")

    ref["_match_code"] = ref[code_col].map(norm_hk_code)
    ref = ref.loc[ref["_match_code"].ne("")].copy()
    ref = ref.drop_duplicates("_match_code", keep="first")

    left = target[
        ["WS_ID", "Name", "Primary_Universe_Index", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol"]
    ].copy()
    left["_match_code"] = left["Primary_Ticker"].map(norm_hk_code)

    rename = {c: f"HKEX_{c}" for c in ref.columns if c != "_match_code"}
    joined = left.merge(ref.rename(columns=rename), on="_match_code", how="left", validate="m:1")
    joined["HKEX_Match_Key"] = joined["_match_code"]
    source_probe_col = f"HKEX_{code_col}"
    joined["HKEX_Match_Status"] = joined[source_probe_col].map(
        lambda v: "MATCHED" if txt(v) else "NOT_MATCHED"
    )
    joined = joined.drop(columns=["_match_code"])

    meta = {
        "header_row_zero_based": int(header_idx),
        "reference_rows": int(len(ref)),
        "reference_columns": [str(c) for c in columns],
        "stock_code_column": str(code_col),
        "target_rows": int(len(target)),
        "matched_rows": int(joined["HKEX_Match_Status"].eq("MATCHED").sum()),
    }
    meta["coverage"] = (
        float(meta["matched_rows"] / meta["target_rows"]) if meta["target_rows"] else 1.0
    )
    return joined, meta


def match_krx(payload: dict[str, Any], target: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = payload.get("OutBlock_1")
    if not isinstance(rows, list):
        raise ValueError(f"KRX OutBlock_1 missing; keys={list(payload)[:30]}")
    ref = pd.DataFrame(rows)
    if ref.empty:
        raise ValueError("KRX reference returned zero rows")

    code_col = next(
        (
            c
            for c in ["ISU_SRT_CD", "ISU_CD", "ISU_CODE"]
            if c in ref.columns
        ),
        None,
    )
    if code_col is None:
        raise ValueError(f"KRX code column missing; columns={list(ref.columns)}")

    ref["_match_code"] = ref[code_col].map(norm_kr_code)
    ref = ref.loc[ref["_match_code"].ne("")].copy()
    ref = ref.drop_duplicates("_match_code", keep="first")

    left = target[
        ["WS_ID", "Name", "Primary_Universe_Index", "Primary_MIC", "Primary_Ticker", "Yahoo_Symbol"]
    ].copy()
    left["_match_code"] = left["Primary_Ticker"].map(norm_kr_code)

    rename = {c: f"KRX_{c}" for c in ref.columns if c != "_match_code"}
    joined = left.merge(ref.rename(columns=rename), on="_match_code", how="left", validate="m:1")
    joined["KRX_Match_Key"] = joined["_match_code"]
    source_probe_col = f"KRX_{code_col}"
    joined["KRX_Match_Status"] = joined[source_probe_col].map(
        lambda v: "MATCHED" if txt(v) else "NOT_MATCHED"
    )
    joined = joined.drop(columns=["_match_code"])

    meta = {
        "reference_rows": int(len(ref)),
        "reference_columns": [str(c) for c in ref.columns if c != "_match_code"],
        "stock_code_column": str(code_col),
        "target_rows": int(len(target)),
        "matched_rows": int(joined["KRX_Match_Status"].eq("MATCHED").sum()),
    }
    meta["coverage"] = (
        float(meta["matched_rows"] / meta["target_rows"]) if meta["target_rows"] else 1.0
    )
    return joined, meta


def session_for_probe() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0 Safari/537.36 "
                "WeltSwingLongDEV/0.9"
            ),
            "Accept-Language": "en-US,en;q=0.8",
        }
    )
    return s


def self_test() -> None:
    fake = pd.DataFrame(
        [
            ["noise", None],
            ["Stock Code", "Name of Securities"],
            [5, "Example A"],
            ["0700", "Example B"],
        ]
    )
    idx = detect_header_row(fake, {"stockcode"})
    assert idx == 1
    assert norm_hk_code(5) == "00005"
    assert norm_hk_code("0700") == "00700"
    assert norm_kr_code("5930") == "005930"

    links = extract_candidate_links(
        '<a href="/files/list.csv">Download full list CSV</a>'
        '<a href="/about">About</a>',
        "https://example.test/base",
        ["download", ".csv"],
    )
    assert len(links) == 1
    assert links[0]["url"] == "https://example.test/files/list.csv"
    print("PRIMARY_MARKET_BUNDLE_PROBE_V0_9_SELF_TEST_PASS")


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    summary8 = load_json(Path(cfg["source_summary_v0_8"]))
    if summary8["run_status"] != "INSTRUMENT_RESOLUTION_ASX_V0_8_COMPLETE_WITH_REMAINING_REVIEW":
        raise SystemExit("Unexpected v0.8 source run_status")
    if int(summary8["remaining_manual_rows"]) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.8 remaining manual count")
    if int(summary8["strict_candidates_v0_8"]) != int(cfg["expected_strict_candidates_v0_8"]):
        raise SystemExit("Unexpected v0.8 strict candidate count")
    if summary8["p0_run"] is not False or summary8["alpha_vantage_allowed"] is not False:
        raise SystemExit("Governance gate failed on v0.8 summary")

    manual = pd.read_csv(cfg["source_manual_queue_v0_8"], keep_default_na=False, dtype=str)
    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit(f"Manual rows {len(manual)} != expected {cfg['expected_source_manual_rows']}")
    if manual["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.8 manual queue")

    expected_segments = {k: int(v) for k, v in cfg["expected_segment_rows"].items()}
    actual_segments = (
        manual.groupby("Primary_Universe_Index", dropna=False).size().astype(int).to_dict()
    )
    if actual_segments != expected_segments:
        raise SystemExit(
            "Unexpected v0.8 segment counts: "
            + json.dumps({"actual": actual_segments, "expected": expected_segments}, ensure_ascii=False)
        )

    manual.to_csv(out / "instrument_manual_review_queue_v0.9.csv", index=False)
    pd.DataFrame(
        [
            {"Primary_Universe_Index": k, "Target_Rows": v}
            for k, v in expected_segments.items()
        ]
    ).to_csv(out / "target_counts_v0.9.csv", index=False)

    session = session_for_probe()
    source_status: list[dict[str, Any]] = []
    discovered_links: list[dict[str, str]] = []
    external_requests = 0
    hk_meta: dict[str, Any] = {"status": "NOT_RUN", "target_rows": expected_segments["HK_HSI"]}
    kr_meta: dict[str, Any] = {"status": "NOT_RUN", "target_rows": expected_segments["KR_KOSPI200"]}

    source_map = {x["market"]: x for x in cfg["sources"]}
    expected_markets = set(expected_segments)
    if set(source_map) != expected_markets:
        raise SystemExit("Source config markets do not match v0.8 remaining segments")

    for market in expected_segments:
        spec = source_map[market]
        target = manual.loc[manual["Primary_Universe_Index"].eq(market)].copy()
        method = spec["method"].upper()
        url = spec["url"]
        row: dict[str, Any] = {
            "Primary_Universe_Index": market,
            "Target_Rows": int(len(target)),
            "Source_Name": spec["name"],
            "Source_URL": url,
            "Method": method,
            "HTTP_Status": "",
            "Content_Type": "",
            "Bytes": 0,
            "SHA256": "",
            "Probe_Status": "ERROR",
            "Parse_Status": "NOT_ATTEMPTED",
            "Matched_Rows": "",
            "Coverage": "",
            "Error": "",
        }

        try:
            external_requests += 1
            if method == "POST":
                headers = dict(spec.get("headers", {}))
                response = session.post(
                    url,
                    data=spec.get("data", {}),
                    headers=headers,
                    timeout=int(cfg["request_timeout_seconds"]),
                )
            elif method == "GET":
                response = session.get(
                    url,
                    headers=spec.get("headers", {}),
                    timeout=int(cfg["request_timeout_seconds"]),
                )
            else:
                raise ValueError(f"Unsupported method {method}")

            row["HTTP_Status"] = int(response.status_code)
            row["Content_Type"] = response.headers.get("Content-Type", "")
            row["Bytes"] = int(len(response.content))
            row["SHA256"] = sha256_bytes(response.content) if response.content else ""
            response.raise_for_status()
            row["Probe_Status"] = "HTTP_OK"

            if market == "HK_HSI":
                try:
                    matched, meta = match_hkex(response.content, target)
                    matched.to_csv(out / "hkex_reference_matches_v0.9.csv", index=False)
                    hk_meta = {"status": "PARSED", **meta}
                    row["Parse_Status"] = "PARSED_REFERENCE"
                    row["Matched_Rows"] = meta["matched_rows"]
                    row["Coverage"] = meta["coverage"]
                except Exception as exc:
                    empty_match_frame(target, "HKEX").to_csv(
                        out / "hkex_reference_matches_v0.9.csv", index=False
                    )
                    hk_meta = {
                        "status": "PARSE_ERROR",
                        "target_rows": int(len(target)),
                        "error": compact_error(exc),
                    }
                    row["Parse_Status"] = "PARSE_ERROR"
                    row["Error"] = compact_error(exc)

            elif market == "KR_KOSPI200":
                try:
                    payload = response.json()
                    matched, meta = match_krx(payload, target)
                    matched.to_csv(out / "krx_reference_matches_v0.9.csv", index=False)
                    kr_meta = {"status": "PARSED", **meta}
                    row["Parse_Status"] = "PARSED_REFERENCE"
                    row["Matched_Rows"] = meta["matched_rows"]
                    row["Coverage"] = meta["coverage"]
                except Exception as exc:
                    empty_match_frame(target, "KRX").to_csv(
                        out / "krx_reference_matches_v0.9.csv", index=False
                    )
                    kr_meta = {
                        "status": "PARSE_ERROR",
                        "target_rows": int(len(target)),
                        "error": compact_error(exc),
                    }
                    row["Parse_Status"] = "PARSE_ERROR"
                    row["Error"] = compact_error(exc)

            else:
                body = response.text
                links = extract_candidate_links(body, url, list(spec.get("link_keywords", [])))
                for link in links[: int(cfg["max_discovered_links_per_market"])]:
                    discovered_links.append(
                        {
                            "Primary_Universe_Index": market,
                            "Source_Name": spec["name"],
                            "Label": link["label"],
                            "URL": link["url"],
                        }
                    )
                row["Parse_Status"] = "HTML_PROBED"
                row["Matched_Rows"] = ""
                row["Coverage"] = ""

        except Exception as exc:
            row["Error"] = compact_error(exc)
            if market == "HK_HSI":
                empty_match_frame(target, "HKEX").to_csv(
                    out / "hkex_reference_matches_v0.9.csv", index=False
                )
                hk_meta = {
                    "status": "REQUEST_ERROR",
                    "target_rows": int(len(target)),
                    "error": compact_error(exc),
                }
            if market == "KR_KOSPI200":
                empty_match_frame(target, "KRX").to_csv(
                    out / "krx_reference_matches_v0.9.csv", index=False
                )
                kr_meta = {
                    "status": "REQUEST_ERROR",
                    "target_rows": int(len(target)),
                    "error": compact_error(exc),
                }

        source_status.append(row)

    pd.DataFrame(source_status).to_csv(out / "source_probe_status_v0.9.csv", index=False)
    pd.DataFrame(
        discovered_links,
        columns=["Primary_Universe_Index", "Source_Name", "Label", "URL"],
    ).to_csv(out / "discovered_bulk_links_v0.9.csv", index=False)

    # v0.9 is deliberately evidence acquisition only. It must not alter any
    # v0.8 instrument decision or promote the Strict universe.
    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "PRIMARY_MARKET_BUNDLE_PROBE_V0_9_COMPLETE",
        "source_manual_rows_v0_8": int(len(manual)),
        "remaining_manual_rows_v0_9": int(len(manual)),
        "strict_candidates_v0_8": int(summary8["strict_candidates_v0_8"]),
        "strict_candidates_v0_9": int(summary8["strict_candidates_v0_8"]),
        "strict_freeze_allowed": False,
        "markets_probed": int(len(source_status)),
        "segment_rows": expected_segments,
        "external_reference_requests": int(external_requests),
        "max_external_reference_requests": int(cfg["max_external_reference_requests"]),
        "request_bound_respected": bool(
            external_requests <= int(cfg["max_external_reference_requests"])
        ),
        "hkex_reference_probe": hk_meta,
        "krx_reference_probe": kr_meta,
        "discovered_bulk_links": int(len(discovered_links)),
        "decisions_changed": 0,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "canonical_master_mutated": False,
        "notes": [
            "v0.9 probes only the 667 unresolved v0.8 rows, grouped into six remaining markets.",
            "Exactly one configured official/bourse-level request is attempted per market; no per-security requests are made.",
            "HKEX and KRX responses are matched to the frozen target queue when machine-readable reference data is returned.",
            "Canada, Europe, Mexico and South Africa are capability probes only in v0.9; no positive instrument inference is made from issuer/index membership.",
            "No v0.8 PASS/FAIL decision is changed and the Strict candidate count remains frozen at 2020.",
            "The next classification stage may use only security-specific fields whose semantics are documented by an official primary-market source.",
        ],
    }

    if not summary["request_bound_respected"]:
        raise SystemExit("External reference request bound exceeded")
    (out / "summary_v0.9.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if args.config is None:
        raise SystemExit("--config is required unless --self-test is used")

    summary = run(args.config)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
