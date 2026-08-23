#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import math
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

# Reuse the already frozen/validated project mapping rules instead of creating
# a second competing Yahoo-symbol implementation.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from price_cache import (  # noqa: E402
    MIC_SUFFIX_RULES,
    YAHOO_SYMBOL_SENTINELS,
    derive_yahoo_symbol,
    load_yahoo_symbol_overrides,
)

SCHEMA = "WELT_SWING_FULL_IDENTITY_PROVIDER_AUDIT_V0_1"
EXPECTED_ROWS = 3664
PRODUCTIVE_TRADING_AUTHORITY = False
P0_RUN = False
ALPHA_VANTAGE_ALLOWED = False

LEGAL_WORDS = {
    "ag", "sa", "se", "nv", "plc", "inc", "incorporated", "corp", "corporation",
    "co", "company", "limited", "ltd", "group", "holdings", "holding", "spa", "srl",
    "ab", "asa", "oyj", "a/s", "as", "pte", "llc", "lp", "the", "de", "cv",
}

US_SEGMENT = "US_SP1500"

# Yahoo exchange suffixes are already canonicalized in price_cache.py.  For the US
# source-superset, the source ticker itself is normally Yahoo-compatible, except
# that Yahoo uses a hyphen for share classes (e.g. BRK-B).
def us_source_to_yahoo(primary_ticker: str) -> tuple[str | None, str]:
    t = clean_text(primary_ticker).upper()
    if not t:
        return None, "MISSING_PRIMARY_TICKER"
    if "/" in t or " " in t:
        return None, "US_EXPLICIT_REVIEW_REQUIRED"
    return t.replace(".", "-"), "US_SOURCE_DIRECT"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    s = str(v).strip()
    if s.lower() in {"nan", "none", "null"}:
        return ""
    return s


def normalize_name(v: Any) -> str:
    s = clean_text(v)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    tokens = [t for t in s.split() if t and t not in LEGAL_WORDS]
    return " ".join(tokens)


def name_similarity(a: Any, b: Any) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jac = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    containment = min(
        len(ta & tb) / len(ta) if ta else 0.0,
        len(ta & tb) / len(tb) if tb else 0.0,
    )
    return max(seq, 0.60 * jac + 0.40 * containment)


def expected_suffix_for_row(row: pd.Series) -> str:
    segment = clean_text(row.get("Primary_Universe_Index"))
    mic = clean_text(row.get("Primary_MIC")).upper()
    if segment == US_SEGMENT:
        return ""
    return MIC_SUFFIX_RULES.get(mic, "")


def strip_expected_suffix(symbol: str, expected_suffix: str) -> str:
    s = clean_text(symbol).upper()
    suffix = clean_text(expected_suffix).upper()
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def is_valid_isin(v: Any) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", clean_text(v).upper()))


def mapping_candidate(
    row: pd.Series,
    overrides: dict[str, str],
) -> tuple[str | None, str, float]:
    ws_id = clean_text(row.get("WS_ID"))
    explicit = clean_text(row.get("Yahoo_Symbol"))
    if explicit.upper() in YAHOO_SYMBOL_SENTINELS:
        explicit = ""

    override = clean_text(overrides.get(ws_id))
    if override:
        return override, "PROJECT_OVERRIDE", 1.00
    if explicit:
        return explicit, "EXPLICIT_MASTER", 0.99

    segment = clean_text(row.get("Primary_Universe_Index"))
    if segment == US_SEGMENT:
        symbol, status = us_source_to_yahoo(row.get("Primary_Ticker"))
        return symbol, status, 0.94 if symbol else 0.0

    symbol, status = derive_yahoo_symbol(
        row.get("Primary_Ticker"),
        row.get("Primary_MIC"),
    )
    confidence = 0.93 if symbol else 0.0
    return symbol, status, confidence


def load_prior_errors(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    # keep_default_na=False is essential because "NA" is a legitimate TSX ticker.
    df = pd.read_csv(path, keep_default_na=False, dtype=str)
    out: dict[str, dict[str, str]] = {}
    for _, r in df.iterrows():
        ws = clean_text(r.get("WS_ID") or r.get("ws_id"))
        if not ws:
            continue
        out[ws] = {
            "status": clean_text(r.get("status")),
            "reason_code": clean_text(r.get("reason_code")),
            "yahoo_symbol": clean_text(r.get("yahoo_symbol")),
            "mapping_status": clean_text(r.get("mapping_status")),
        }
    return out


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = clean_text(obj.get("cache_key"))
        if key:
            out[key] = obj
    return out


def append_cache(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def yahoo_search(query: str, max_results: int) -> list[dict[str, Any]]:
    # Search only.  No yf.download(), history(), quote-history or OHLCV call exists
    # anywhere in this audit.
    import yfinance as yf

    s = yf.Search(
        query=query,
        max_results=max_results,
        news_count=0,
        lists_count=0,
        include_cb=False,
        include_nav_links=False,
        include_research=False,
        include_cultural_assets=False,
        enable_fuzzy_query=False,
        recommended=0,
        timeout=25,
        raise_errors=False,
    )
    return list(s.quotes or [])


def quote_display_name(q: dict[str, Any]) -> str:
    return clean_text(
        q.get("longname")
        or q.get("shortname")
        or q.get("name")
        or q.get("symbol")
    )


def score_quote(
    row: pd.Series,
    quote: dict[str, Any],
    *,
    query_is_isin: bool,
) -> tuple[float, dict[str, float]]:
    symbol = clean_text(quote.get("symbol")).upper()
    if not symbol:
        return 0.0, {"name": 0.0, "suffix": 0.0, "equity": 0.0, "isin_query": 0.0}

    qtype = clean_text(quote.get("quoteType")).upper()
    equity = 1.0 if qtype in {"EQUITY", ""} else 0.0

    expected_suffix = expected_suffix_for_row(row).upper()
    segment = clean_text(row.get("Primary_Universe_Index"))

    if segment == US_SEGMENT:
        # A US S&P source constituent should not resolve to a foreign venue suffix.
        suffix_match = 1.0 if re.fullmatch(r"[A-Z0-9-]+", symbol) else 0.0
    elif expected_suffix:
        suffix_match = 1.0 if symbol.endswith(expected_suffix) else 0.0
    else:
        suffix_match = 0.5

    nscore = name_similarity(row.get("Name"), quote_display_name(quote))
    isin_bonus = 1.0 if query_is_isin else 0.0

    # Conservative weighting.  Search is allowed to auto-accept only when the
    # company name and venue context jointly agree.
    score = (
        0.55 * nscore
        + 0.25 * suffix_match
        + 0.10 * equity
        + 0.10 * isin_bonus
    )

    # Non-equities should never be promoted by search merely because the name is close.
    if qtype and qtype != "EQUITY":
        score *= 0.60

    return score, {
        "name": nscore,
        "suffix": suffix_match,
        "equity": equity,
        "isin_query": isin_bonus,
    }


def search_queries_for_row(row: pd.Series) -> list[tuple[str, bool]]:
    queries: list[tuple[str, bool]] = []
    isin = clean_text(row.get("ISIN")).upper()
    if is_valid_isin(isin):
        queries.append((isin, True))
    name = clean_text(row.get("Name"))
    if name:
        queries.append((name, False))
    # deterministic de-duplication while preserving order
    seen = set()
    out = []
    for q, is_isin in queries:
        key = q.casefold()
        if key not in seen:
            seen.add(key)
            out.append((q, is_isin))
    return out


def should_search(
    row: pd.Series,
    candidate: str | None,
    mapping_status: str,
    prior: dict[str, str] | None,
) -> bool:
    ws = clean_text(row.get("WS_ID"))
    segment = clean_text(row.get("Primary_Universe_Index"))
    ticker = clean_text(row.get("Primary_Ticker"))
    mic = clean_text(row.get("Primary_MIC"))

    # Existing explicit/project overrides are already audited provider mappings.
    if mapping_status in {"PROJECT_OVERRIDE", "EXPLICIT_MASTER"}:
        return False

    # The US source-superset has direct ticker symbols; exact primary MIC is an
    # identity metadata task, not a Yahoo-provider mapping blocker.
    if segment == US_SEGMENT and candidate:
        return False

    if ws.startswith("WS:SRC:"):
        return True
    if not candidate or not ticker:
        return True
    if not mic:
        return True

    if prior and prior.get("status") in {"DOWNLOAD_FAILED", "MAPPING_PENDING"}:
        return True

    if mapping_status in {
        "EXPLICIT_OVERRIDE_REQUIRED",
        "UNSUPPORTED_MIC",
        "MISSING_PRIMARY_TICKER",
        "US_EXPLICIT_REVIEW_REQUIRED",
    }:
        return True

    return False


def resolve_by_search(
    row: pd.Series,
    *,
    cache: dict[str, dict[str, Any]],
    cache_path: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
    accept_score: float,
    accept_margin: float,
    name_similarity_floor: float,
) -> dict[str, Any]:
    expected_suffix = expected_suffix_for_row(row)
    best_result: dict[str, Any] | None = None

    for query, query_is_isin in search_queries_for_row(row):
        cache_key = hashlib.sha256(
            f"{query}|{expected_suffix}|{clean_text(row.get('Primary_Universe_Index'))}".encode("utf-8")
        ).hexdigest()

        if cache_key in cache:
            entry = cache[cache_key]
            quotes = list(entry.get("quotes") or [])
            error = clean_text(entry.get("error"))
            cached = True
        else:
            if budget["used"] >= budget["max"]:
                return {
                    "accepted": False,
                    "reason": "SEARCH_BUDGET_EXCEEDED",
                    "query": query,
                    "query_is_isin": query_is_isin,
                    "quotes": [],
                }
            budget["used"] += 1
            error = ""
            try:
                quotes = yahoo_search(query, max_results=max_results)
            except Exception as exc:  # noqa: BLE001
                quotes = []
                error = f"{type(exc).__name__}: {exc}"
            entry = {
                "cache_key": cache_key,
                "query": query,
                "expected_suffix": expected_suffix,
                "segment": clean_text(row.get("Primary_Universe_Index")),
                "quotes": quotes,
                "error": error,
                "fetched_utc": utc_now(),
            }
            cache[cache_key] = entry
            append_cache(cache_path, entry)
            cached = False
            if pause_seconds > 0:
                time.sleep(pause_seconds)

        scored: list[tuple[float, dict[str, Any], dict[str, float]]] = []
        for q in quotes:
            score, parts = score_quote(row, q, query_is_isin=query_is_isin)
            scored.append((score, q, parts))
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            current = {
                "accepted": False,
                "reason": "SEARCH_NO_QUOTES" if not error else "SEARCH_ERROR",
                "query": query,
                "query_is_isin": query_is_isin,
                "error": error,
                "cached": cached,
                "quotes": [],
            }
        else:
            top_score, top_q, parts = scored[0]
            second_score = scored[1][0] if len(scored) > 1 else 0.0
            margin = top_score - second_score
            accepted = (
                top_score >= accept_score
                and margin >= accept_margin
                and (
                    parts["name"] >= name_similarity_floor
                    or (query_is_isin and parts["suffix"] >= 1.0)
                )
                and parts["equity"] >= 1.0
            )
            current = {
                "accepted": accepted,
                "reason": "SEARCH_HIGH_CONFIDENCE" if accepted else "SEARCH_AMBIGUOUS",
                "query": query,
                "query_is_isin": query_is_isin,
                "cached": cached,
                "error": error,
                "symbol": clean_text(top_q.get("symbol")).upper(),
                "result_name": quote_display_name(top_q),
                "quote_type": clean_text(top_q.get("quoteType")),
                "exchange": clean_text(top_q.get("exchange")),
                "exchange_display": clean_text(top_q.get("exchDisp")),
                "score": round(float(top_score), 6),
                "margin": round(float(margin), 6),
                "name_score": round(float(parts["name"]), 6),
                "suffix_score": round(float(parts["suffix"]), 6),
                "top_candidates": [
                    {
                        "symbol": clean_text(q.get("symbol")).upper(),
                        "name": quote_display_name(q),
                        "quoteType": clean_text(q.get("quoteType")),
                        "exchange": clean_text(q.get("exchange")),
                        "score": round(float(sc), 6),
                    }
                    for sc, q, _ in scored[:3]
                ],
            }

        if best_result is None:
            best_result = current
        else:
            if float(current.get("score", 0.0)) > float(best_result.get("score", 0.0)):
                best_result = current

        if current.get("accepted"):
            return current

    return best_result or {
        "accepted": False,
        "reason": "NO_SEARCH_QUERY",
        "query": "",
        "query_is_isin": False,
        "quotes": [],
    }


def add_duplicate_flags(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = master.copy()

    isin_groups: dict[str, list[int]] = defaultdict(list)
    name_groups: dict[str, list[int]] = defaultdict(list)

    for i, r in out.iterrows():
        isin = clean_text(r.get("ISIN")).upper()
        if is_valid_isin(isin):
            isin_groups[isin].append(i)
        nn = normalize_name(r.get("Name"))
        if nn:
            name_groups[nn].append(i)

    dup_records = []
    isin_flag = [""] * len(out)
    name_flag = [""] * len(out)

    for isin, idxs in isin_groups.items():
        if len(idxs) <= 1:
            continue
        gid = "ISIN:" + isin
        for i in idxs:
            isin_flag[i] = gid
            dup_records.append({
                "Duplicate_Type": "ISIN",
                "Duplicate_Key": isin,
                "WS_ID": clean_text(out.iloc[i].get("WS_ID")),
                "Name": clean_text(out.iloc[i].get("Name")),
                "Primary_Universe_Index": clean_text(out.iloc[i].get("Primary_Universe_Index")),
                "Primary_Ticker": clean_text(out.iloc[i].get("Primary_Ticker")),
                "Primary_MIC": clean_text(out.iloc[i].get("Primary_MIC")),
                "ISIN": isin,
            })

    for nn, idxs in name_groups.items():
        if len(idxs) <= 1:
            continue
        # Exact normalized-name duplicates are review evidence only.  They are never
        # auto-merged because cross-listings and unrelated same-name issuers exist.
        gid = "NAME:" + hashlib.sha256(nn.encode("utf-8")).hexdigest()[:12]
        for i in idxs:
            name_flag[i] = gid
            dup_records.append({
                "Duplicate_Type": "NORMALIZED_NAME",
                "Duplicate_Key": nn,
                "WS_ID": clean_text(out.iloc[i].get("WS_ID")),
                "Name": clean_text(out.iloc[i].get("Name")),
                "Primary_Universe_Index": clean_text(out.iloc[i].get("Primary_Universe_Index")),
                "Primary_Ticker": clean_text(out.iloc[i].get("Primary_Ticker")),
                "Primary_MIC": clean_text(out.iloc[i].get("Primary_MIC")),
                "ISIN": clean_text(out.iloc[i].get("ISIN")),
            })

    out["Duplicate_ISIN_Group"] = isin_flag
    out["Duplicate_Name_Group"] = name_flag
    return out, pd.DataFrame(dup_records)


def write_xlsx(
    master: pd.DataFrame,
    audit: pd.DataFrame,
    review: pd.DataFrame,
    duplicates: pd.DataFrame,
    summary: dict[str, Any],
    path: Path,
) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        master.to_excel(xw, sheet_name="Universe_Master", index=False)
        audit.to_excel(xw, sheet_name="Mapping_Audit", index=False)
        review.to_excel(xw, sheet_name="Review_Queue", index=False)
        duplicates.to_excel(xw, sheet_name="Duplicate_Review", index=False)
        pd.DataFrame(
            [
                {
                    "Key": k,
                    "Value": json.dumps(v, ensure_ascii=False)
                    if isinstance(v, (dict, list))
                    else v,
                }
                for k, v in summary.items()
            ]
        ).to_excel(xw, sheet_name="Run_Summary", index=False)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def offline_self_test() -> None:
    # Europe: an RIC-style source ticker can be corrected by a high-confidence
    # Yahoo search result while preserving the source/canonical fields.
    row = pd.Series({
        "WS_ID": "WS:XETR:ALVG.DE",
        "Name": "ALLIANZ",
        "Primary_Ticker": "ALVG.DE",
        "Primary_MIC": "XETR",
        "Primary_Universe_Index": "EU_STOXX600",
        "ISIN": "",
    })
    score, parts = score_quote(
        row,
        {
            "symbol": "ALV.DE",
            "shortname": "Allianz SE",
            "quoteType": "EQUITY",
            "exchange": "GER",
        },
        query_is_isin=False,
    )
    assert score >= 0.80, score
    assert parts["suffix"] == 1.0
    assert parts["equity"] == 1.0

    us, status = us_source_to_yahoo("BRK.B")
    assert us == "BRK-B"
    assert status == "US_SOURCE_DIRECT"

    jse = pd.Series({
        "Name": "BHP",
        "Primary_Ticker": "",
        "Primary_MIC": "XJSE",
        "Primary_Universe_Index": "ZA_TOP40",
    })
    score2, parts2 = score_quote(
        jse,
        {
            "symbol": "BHG.JO",
            "shortname": "BHP Group Limited",
            "quoteType": "EQUITY",
        },
        query_is_isin=False,
    )
    assert parts2["suffix"] == 1.0
    assert parts2["equity"] == 1.0
    assert score2 > 0.75

    print("FULL_IDENTITY_PROVIDER_AUDIT_OFFLINE_SELF_TEST_PASS")


def run_audit(config: dict[str, Any]) -> dict[str, Any]:
    master_path = Path(config["master_file"])
    prior_errors_path = Path(config["prior_errors_file"])
    override_path = Path(config["override_file"])
    output_dir = Path(config["output_dir"])
    cache_path = Path(config["search_cache"])

    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not master_path.exists():
        raise SystemExit(f"Master missing: {master_path}")

    # keep_default_na=False protects legitimate ticker values such as TSX:NA.
    master = pd.read_csv(master_path, keep_default_na=False, dtype=str)
    if len(master) != EXPECTED_ROWS:
        raise SystemExit(f"Expected {EXPECTED_ROWS} master rows, got {len(master)}")
    if master["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Master contains duplicate WS_ID before audit")

    required = {
        "WS_ID", "Name", "Primary_Ticker", "Primary_MIC", "Primary_Universe_Index",
        "Yahoo_Symbol", "Mapping_Status", "ISIN", "Universe_Status",
    }
    missing = required - set(master.columns)
    if missing:
        raise SystemExit(f"Master missing columns: {sorted(missing)}")

    prior_errors = load_prior_errors(prior_errors_path)
    overrides = load_yahoo_symbol_overrides(override_path)
    search_cache = load_cache(cache_path)

    budget = {
        "used": 0,
        "max": int(config.get("max_search_queries", 500)),
    }

    audit_rows: list[dict[str, Any]] = []
    updated_rows: list[pd.Series] = []

    for _, source_row in master.iterrows():
        row = source_row.copy()
        ws = clean_text(row.get("WS_ID"))
        prior = prior_errors.get(ws)

        candidate, mapping_status, mapping_conf = mapping_candidate(row, overrides)
        do_search = should_search(row, candidate, mapping_status, prior)

        search_result: dict[str, Any] = {}
        final_symbol = clean_text(candidate).upper()
        final_status = mapping_status
        final_conf = mapping_conf

        if do_search:
            search_result = resolve_by_search(
                row,
                cache=search_cache,
                cache_path=cache_path,
                budget=budget,
                max_results=int(config.get("search_max_results", 8)),
                pause_seconds=float(config.get("search_pause_seconds", 0.10)),
                accept_score=float(config.get("accept_score", 0.82)),
                accept_margin=float(config.get("accept_margin", 0.12)),
                name_similarity_floor=float(config.get("name_similarity_floor", 0.68)),
            )
            if search_result.get("accepted"):
                final_symbol = clean_text(search_result.get("symbol")).upper()
                final_status = "SEARCH_HIGH_CONFIDENCE"
                final_conf = float(search_result.get("score", 0.0))
            else:
                # A previously known-bad derived symbol must never silently remain
                # promoted just because the search was ambiguous.
                if prior and prior.get("status") in {"DOWNLOAD_FAILED", "MAPPING_PENDING"}:
                    final_symbol = ""
                elif not candidate:
                    final_symbol = ""
                final_status = clean_text(search_result.get("reason")) or "SEARCH_REVIEW_REQUIRED"
                final_conf = float(search_result.get("score", 0.0) or 0.0)

        expected_suffix = expected_suffix_for_row(row)
        resolved_ticker_candidate = (
            strip_expected_suffix(final_symbol, expected_suffix)
            if final_symbol
            else ""
        )

        identity_issues = []
        if not clean_text(row.get("Name")):
            identity_issues.append("MISSING_NAME")
        if not clean_text(row.get("Primary_Ticker")):
            identity_issues.append("MISSING_PRIMARY_TICKER")
        if not clean_text(row.get("Primary_MIC")):
            if clean_text(row.get("Primary_Universe_Index")) == US_SEGMENT:
                identity_issues.append("US_PRIMARY_MIC_PENDING")
            else:
                identity_issues.append("MISSING_PRIMARY_MIC")
        if ws.startswith("WS:SRC:"):
            identity_issues.append("TEMPORARY_SOURCE_ID")
        if not is_valid_isin(row.get("ISIN")):
            identity_issues.append("ISIN_NOT_VERIFIED")

        # ISIN_NOT_VERIFIED and US_PRIMARY_MIC_PENDING are informative; they do not
        # by themselves block provider mapping or flood the review queue.
        critical_issues = {
            x for x in identity_issues
            if x not in {"ISIN_NOT_VERIFIED", "US_PRIMARY_MIC_PENDING"}
        }

        provider_review = not bool(final_symbol) or final_status in {
            "SEARCH_AMBIGUOUS", "SEARCH_NO_QUOTES", "SEARCH_ERROR",
            "SEARCH_BUDGET_EXCEEDED", "NO_SEARCH_QUERY",
        }

        needs_review = bool(provider_review or critical_issues)

        row["Yahoo_Symbol"] = final_symbol
        row["Mapping_Status"] = final_status
        row["Identity_Audit_Status"] = (
            "REVIEW_REQUIRED" if needs_review else "AUDITED_NO_CRITICAL_IDENTITY_ISSUE"
        )
        row["Identity_Audit_Issues"] = ";".join(identity_issues)
        row["Yahoo_Mapping_Confidence"] = round(float(final_conf), 6)
        row["Resolved_Exchange_Ticker_Candidate"] = resolved_ticker_candidate
        row["Audit_UTC"] = utc_now()
        updated_rows.append(row)

        audit_rows.append({
            "WS_ID": ws,
            "Name": clean_text(row.get("Name")),
            "Country": clean_text(row.get("Country")),
            "Primary_Universe_Index": clean_text(row.get("Primary_Universe_Index")),
            "Primary_Ticker": clean_text(source_row.get("Primary_Ticker")),
            "Primary_MIC": clean_text(source_row.get("Primary_MIC")),
            "ISIN": clean_text(source_row.get("ISIN")),
            "Universe_Status": clean_text(source_row.get("Universe_Status")),
            "Yahoo_Symbol_Before": clean_text(source_row.get("Yahoo_Symbol")),
            "Yahoo_Symbol_After": final_symbol,
            "Yahoo_Mapping_Status": final_status,
            "Yahoo_Mapping_Confidence": round(float(final_conf), 6),
            "Resolved_Exchange_Ticker_Candidate": resolved_ticker_candidate,
            "Prior_Run_Status": clean_text(prior.get("status")) if prior else "",
            "Prior_Reason_Code": clean_text(prior.get("reason_code")) if prior else "",
            "Search_Attempted": bool(do_search),
            "Search_Query": clean_text(search_result.get("query")),
            "Search_Result_Name": clean_text(search_result.get("result_name")),
            "Search_Result_Exchange": clean_text(search_result.get("exchange")),
            "Search_Score": search_result.get("score", ""),
            "Search_Margin": search_result.get("margin", ""),
            "Search_Reason": clean_text(search_result.get("reason")),
            "Identity_Issues": ";".join(identity_issues),
            "Needs_Review": bool(needs_review),
        })

    audited = pd.DataFrame(updated_rows)
    audit_df = pd.DataFrame(audit_rows)

    if len(audited) != EXPECTED_ROWS or audited["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Post-audit row-count or WS_ID uniqueness invariant failed")

    audited, duplicates_df = add_duplicate_flags(audited)

    duplicate_ws = set(duplicates_df["WS_ID"].astype(str)) if not duplicates_df.empty else set()
    if duplicate_ws:
        audited.loc[audited["WS_ID"].astype(str).isin(duplicate_ws), "Identity_Audit_Issues"] = (
            audited.loc[audited["WS_ID"].astype(str).isin(duplicate_ws), "Identity_Audit_Issues"]
            .astype(str)
            .apply(lambda x: (x + ";POSSIBLE_DUPLICATE").strip(";"))
        )
        audited.loc[audited["WS_ID"].astype(str).isin(duplicate_ws), "Identity_Audit_Status"] = "REVIEW_REQUIRED"
        audit_df.loc[audit_df["WS_ID"].astype(str).isin(duplicate_ws), "Needs_Review"] = True
        audit_df.loc[audit_df["WS_ID"].astype(str).isin(duplicate_ws), "Identity_Issues"] = (
            audit_df.loc[audit_df["WS_ID"].astype(str).isin(duplicate_ws), "Identity_Issues"]
            .astype(str)
            .apply(lambda x: (x + ";POSSIBLE_DUPLICATE").strip(";"))
        )

    review_df = audit_df.loc[audit_df["Needs_Review"] == True].copy()  # noqa: E712

    status_counts = Counter(audit_df["Yahoo_Mapping_Status"].astype(str))
    segment_mapping = {}
    for segment, g in audit_df.groupby("Primary_Universe_Index"):
        mapped = int((g["Yahoo_Symbol_After"].astype(str).str.len() > 0).sum())
        segment_mapping[str(segment)] = {
            "rows": int(len(g)),
            "mapped": mapped,
            "mapped_pct": round(100.0 * mapped / len(g), 4) if len(g) else 0.0,
            "review": int(g["Needs_Review"].astype(bool).sum()),
        }

    mapped_count = int((audit_df["Yahoo_Symbol_After"].astype(str).str.len() > 0).sum())
    review_count = int(audit_df["Needs_Review"].astype(bool).sum())
    unresolved_count = EXPECTED_ROWS - mapped_count

    summary = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "run_status": (
            "AUDIT_COMPLETE" if review_count == 0 else "AUDIT_COMPLETE_WITH_REVIEW_QUEUE"
        ),
        "source_master": str(master_path),
        "source_master_sha256": sha256_file(master_path),
        "rows": EXPECTED_ROWS,
        "provider_mapped": mapped_count,
        "provider_mapping_pct": round(100.0 * mapped_count / EXPECTED_ROWS, 4),
        "provider_unresolved": unresolved_count,
        "review_queue_rows": review_count,
        "duplicate_review_rows": int(len(duplicates_df)),
        "search_queries_used_this_run": int(budget["used"]),
        "search_query_budget": int(budget["max"]),
        "mapping_status_counts": dict(sorted(status_counts.items())),
        "segment_mapping": segment_mapping,
        "identity_audit_executed_for_all_rows": True,
        "identity_fully_resolved": review_count == 0,
        "provider_mapping_complete": unresolved_count == 0,
        "price_run_allowed_after_this_step": False,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "p0_run": P0_RUN,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "No OHLCV/history download is performed by this audit.",
            "Existing project overrides and frozen deterministic MIC rules are reused.",
            "Known DOWNLOAD_FAILED/MAPPING_PENDING names from the 1535 diagnostic run are targeted for Yahoo Search remediation.",
            "New US S&P 1500 source tickers are mapped directly for Yahoo syntax; exact US primary MIC remains identity metadata pending.",
            "Name-only JSE source identities are eligible for targeted Yahoo Search; no ticker is invented.",
            "Ambiguous search results remain in Review_Queue and are not auto-promoted.",
            "Possible duplicates are never auto-merged.",
            "P0 and productive trading remain disabled.",
        ],
    }

    out_master_csv = Path(config["audited_master_csv"])
    out_master_xlsx = Path(config["audited_master_xlsx"])
    out_master_csv.parent.mkdir(parents=True, exist_ok=True)
    audited.to_csv(out_master_csv, index=False)

    audit_path = output_dir / "mapping_audit_v0.1.csv"
    review_path = output_dir / "review_queue_v0.1.csv"
    duplicates_path = output_dir / "duplicate_review_v0.1.csv"
    summary_path = output_dir / "summary_v0.1.json"
    search_log_path = output_dir / "search_cache_snapshot_v0.1.jsonl"

    audit_df.to_csv(audit_path, index=False)
    review_df.to_csv(review_path, index=False)
    duplicates_df.to_csv(duplicates_path, index=False)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if cache_path.exists():
        search_log_path.write_text(cache_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        search_log_path.write_text("", encoding="utf-8")

    write_xlsx(
        audited,
        audit_df,
        review_df,
        duplicates_df,
        summary,
        out_master_xlsx,
    )

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        offline_self_test()
        return 0

    if not args.config:
        raise SystemExit("--config required unless --self-test is used")

    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    run_audit(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
