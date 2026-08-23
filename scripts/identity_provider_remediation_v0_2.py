#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
from typing import Any, Iterable

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from price_cache import MIC_SUFFIX_RULES  # noqa: E402

SCHEMA = "WELT_SWING_IDENTITY_PROVIDER_REMEDIATION_V0_2"
EXPECTED_ROWS = 3664

PRODUCTIVE_TRADING_AUTHORITY = False
P0_RUN = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_HISTORY_ALLOWED = False

# Keep economically meaningful words such as "group" and "holdings".
# v0.1 removed them too aggressively and therefore created false duplicate
# candidates such as SoftBank Corp vs SoftBank Group Corp.
LEGAL_SUFFIX_WORDS = {
    "ag", "sa", "se", "nv", "plc", "inc", "incorporated", "corp",
    "corporation", "co", "company", "limited", "ltd", "spa", "srl",
    "ab", "asa", "oyj", "pte", "llc", "lp", "cv", "sab",
}

EU_SEGMENT = "EU_STOXX600"
MX_SEGMENT = "MX_IPC"
ZA_SEGMENT = "ZA_TOP40"
CA_SEGMENT = "CA_TSX"


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
    s = s.casefold().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    toks = s.split()

    # Strip only legal-form suffixes from the end; do not delete meaningful
    # middle words such as "group" or "holdings".
    while toks and toks[-1] in LEGAL_SUFFIX_WORDS:
        toks.pop()
    while toks and toks[0] == "the":
        toks.pop(0)
    return " ".join(toks)


def name_similarity(a: Any, b: Any) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jac = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    contain = (
        len(ta & tb) / min(len(ta), len(tb))
        if ta and tb
        else 0.0
    )
    return max(seq, 0.55 * jac + 0.45 * contain)


def quote_name(q: dict[str, Any]) -> str:
    return clean_text(
        q.get("longname")
        or q.get("shortname")
        or q.get("name")
        or q.get("symbol")
    )


def is_equity(q: dict[str, Any]) -> bool:
    qt = clean_text(q.get("quoteType")).upper()
    return qt in {"", "EQUITY"}


def expected_suffix(row: pd.Series) -> str:
    mic = clean_text(row.get("Primary_MIC")).upper()
    return MIC_SUFFIX_RULES.get(mic, "")


def strip_suffix(symbol: str, suffix: str) -> str:
    s = clean_text(symbol).upper()
    suf = clean_text(suffix).upper()
    if suf and s.endswith(suf):
        return s[:-len(suf)]
    return s


def load_jsonl(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
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


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def cache_key(query: str, suffix: str, segment: str) -> str:
    return hashlib.sha256(
        f"{query}|{suffix}|{segment}".encode("utf-8")
    ).hexdigest()


def yahoo_search(query: str, max_results: int) -> list[dict[str, Any]]:
    # Search only. No price/history/OHLCV method is used.
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


def get_quotes(
    *,
    query: str,
    row: pd.Series,
    cache: dict[str, dict[str, Any]],
    append_cache_path: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
) -> tuple[list[dict[str, Any]], str, bool]:
    suffix = expected_suffix(row)
    segment = clean_text(row.get("Primary_Universe_Index"))
    key = cache_key(query, suffix, segment)

    if key in cache:
        obj = cache[key]
        return list(obj.get("quotes") or []), clean_text(obj.get("error")), True

    if budget["used"] >= budget["max"]:
        return [], "SEARCH_BUDGET_EXCEEDED", False

    budget["used"] += 1
    error = ""
    try:
        quotes = yahoo_search(query, max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        quotes = []
        error = f"{type(exc).__name__}: {exc}"

    obj = {
        "cache_key": key,
        "query": query,
        "expected_suffix": suffix,
        "segment": segment,
        "quotes": quotes,
        "error": error,
        "fetched_utc": utc_now(),
        "remediation_schema": SCHEMA,
    }
    cache[key] = obj
    append_jsonl(append_cache_path, obj)
    if pause_seconds > 0:
        time.sleep(pause_seconds)
    return quotes, error, False


def merge_quotes(*quote_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = {}
    for quotes in quote_lists:
        for q in quotes:
            sym = clean_text(q.get("symbol")).upper()
            if not sym:
                continue
            # Keep the richer record when the same symbol is returned repeatedly.
            if sym not in out or len(json.dumps(q, default=str)) > len(json.dumps(out[sym], default=str)):
                out[sym] = q
    return list(out.values())


def market_candidates(
    row: pd.Series,
    quotes: list[dict[str, Any]],
) -> list[tuple[float, dict[str, Any]]]:
    suffix = expected_suffix(row).upper()
    out = []
    for q in quotes:
        sym = clean_text(q.get("symbol")).upper()
        if not sym or not is_equity(q):
            continue
        if suffix and not sym.endswith(suffix):
            continue
        ns = name_similarity(row.get("Name"), quote_name(q))
        out.append((ns, q))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def ric_class_hint(primary_ticker: str, mic: str) -> str:
    """
    Convert common Reuters/RIC share-class syntax into a Yahoo-style stem hint.

    Examples:
      CARLb.CO -> CARL-B
      COLOb.CO -> COLO-B
      ASSAb.ST -> ASSA-B
      ATCOa.ST -> ATCO-A

    This is a ranking hint only. It is never accepted without a Yahoo Search
    candidate on the expected market.
    """
    t = clean_text(primary_ticker)
    mic = clean_text(mic).upper()
    for src_suffix in {
        "XCSE": ".CO",
        "XSTO": ".ST",
    }.get(mic, ""):
        pass

    venue_suffix = {"XCSE": ".CO", "XSTO": ".ST"}.get(mic, "")
    if venue_suffix and t.upper().endswith(venue_suffix):
        stem = t[:-len(venue_suffix)]
    else:
        stem = t

    m = re.fullmatch(r"(.+?)([abAB])", stem)
    if m:
        return f"{m.group(1).upper()}-{m.group(2).upper()}"
    return stem.upper()


def choose_unique_market_candidate(
    row: pd.Series,
    quotes: list[dict[str, Any]],
    *,
    min_name: float,
    margin: float,
    use_class_hint: bool,
) -> dict[str, Any]:
    cands = market_candidates(row, quotes)
    if not cands:
        return {
            "accepted": False,
            "reason": "NO_EXPECTED_MARKET_CANDIDATE",
            "symbol": "",
            "candidate_count": 0,
        }

    source_hint = ric_class_hint(
        row.get("Primary_Ticker"),
        row.get("Primary_MIC"),
    ) if use_class_hint else ""

    rescored = []
    suffix = expected_suffix(row)
    for ns, q in cands:
        sym = clean_text(q.get("symbol")).upper()
        stem = strip_suffix(sym, suffix)
        hint_bonus = 0.0
        if source_hint:
            if stem == source_hint:
                hint_bonus = 0.25
            elif stem.replace("-", "") == source_hint.replace("-", ""):
                hint_bonus = 0.15
        score = min(1.0, ns + hint_bonus)
        rescored.append((score, ns, q, hint_bonus))
    rescored.sort(key=lambda x: x[0], reverse=True)

    top_score, top_name, top_q, top_bonus = rescored[0]
    second_score = rescored[1][0] if len(rescored) > 1 else 0.0
    gap = top_score - second_score

    accepted = (
        top_name >= min_name
        and (
            len(rescored) == 1
            or gap >= margin
            or top_bonus >= 0.25
        )
    )
    return {
        "accepted": accepted,
        "reason": (
            "EXPECTED_MARKET_UNIQUE"
            if accepted and len(rescored) == 1
            else "EXPECTED_MARKET_CLASS_HINT"
            if accepted and top_bonus >= 0.25
            else "EXPECTED_MARKET_CLEAR_WINNER"
            if accepted
            else "EXPECTED_MARKET_AMBIGUOUS"
        ),
        "symbol": clean_text(top_q.get("symbol")).upper() if accepted else "",
        "result_name": quote_name(top_q),
        "exchange": clean_text(top_q.get("exchange")),
        "name_score": round(float(top_name), 6),
        "score": round(float(top_score), 6),
        "margin": round(float(gap), 6),
        "candidate_count": len(rescored),
        "candidates": [
            {
                "symbol": clean_text(q.get("symbol")).upper(),
                "name": quote_name(q),
                "exchange": clean_text(q.get("exchange")),
                "name_score": round(float(ns), 6),
                "score": round(float(sc), 6),
            }
            for sc, ns, q, _ in rescored[:5]
        ],
    }


def mexico_compact_symbol(primary_ticker: str) -> str:
    t = clean_text(primary_ticker).upper()
    t = t.replace("*", "")
    t = re.sub(r"\s+", "", t)
    return f"{t}.MX" if t else ""


def exact_symbol_hit(
    row: pd.Series,
    quotes: list[dict[str, Any]],
    symbol: str,
    min_name: float,
) -> dict[str, Any]:
    wanted = clean_text(symbol).upper()
    hits = [
        q for q in quotes
        if clean_text(q.get("symbol")).upper() == wanted and is_equity(q)
    ]
    if not hits:
        return {"accepted": False, "reason": "EXACT_SYMBOL_NOT_RETURNED"}

    ranked = sorted(
        [(name_similarity(row.get("Name"), quote_name(q)), q) for q in hits],
        key=lambda x: x[0],
        reverse=True,
    )
    ns, q = ranked[0]
    return {
        "accepted": ns >= min_name,
        "reason": "EXACT_SYMBOL_VERIFIED" if ns >= min_name else "EXACT_SYMBOL_NAME_MISMATCH",
        "symbol": wanted if ns >= min_name else "",
        "result_name": quote_name(q),
        "exchange": clean_text(q.get("exchange")),
        "name_score": round(float(ns), 6),
    }


def remediate_mexico(
    row: pd.Series,
    *,
    cache: dict[str, dict[str, Any]],
    append_cache_path: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
) -> dict[str, Any]:
    candidate = mexico_compact_symbol(row.get("Primary_Ticker"))
    if not candidate:
        return {"accepted": False, "reason": "MX_NO_TICKER"}

    q1, e1, _ = get_quotes(
        query=candidate,
        row=row,
        cache=cache,
        append_cache_path=append_cache_path,
        budget=budget,
        max_results=max_results,
        pause_seconds=pause_seconds,
    )
    r = exact_symbol_hit(row, q1, candidate, min_name=0.52)
    if r.get("accepted"):
        r["method"] = "MX_SPACE_CLASS_NORMALIZATION"
        return r

    q2, e2, _ = get_quotes(
        query=clean_text(row.get("Name")),
        row=row,
        cache=cache,
        append_cache_path=append_cache_path,
        budget=budget,
        max_results=max_results,
        pause_seconds=pause_seconds,
    )
    r2 = exact_symbol_hit(row, q2, candidate, min_name=0.52)
    if r2.get("accepted"):
        r2["method"] = "MX_SPACE_CLASS_NORMALIZATION"
        return r2

    merged = merge_quotes(q1, q2)
    market = choose_unique_market_candidate(
        row, merged, min_name=0.70, margin=0.12, use_class_hint=False
    )
    if market.get("accepted"):
        market["method"] = "MX_EXPECTED_MARKET_SEARCH"
        return market

    return {
        "accepted": False,
        "reason": "MX_REVIEW_REQUIRED",
        "candidate": candidate,
        "errors": ";".join(x for x in [e1, e2] if x),
        "market_detail": market,
    }


def remediate_europe(
    row: pd.Series,
    *,
    cache: dict[str, dict[str, Any]],
    append_cache_path: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
) -> dict[str, Any]:
    # First reuse the company-name query already cached by v0.1.
    q1, e1, _ = get_quotes(
        query=clean_text(row.get("Name")),
        row=row,
        cache=cache,
        append_cache_path=append_cache_path,
        budget=budget,
        max_results=max_results,
        pause_seconds=pause_seconds,
    )
    result = choose_unique_market_candidate(
        row, q1, min_name=0.62, margin=0.08, use_class_hint=True
    )
    if result.get("accepted"):
        result["method"] = "EU_EXPECTED_MARKET_FILTER"
        return result

    # Second targeted query is bounded and used only for unresolved European names.
    suffix = expected_suffix(row)
    venue_hint = suffix.lstrip(".")
    q2_query = f"{clean_text(row.get('Name'))} {venue_hint}".strip()
    q2, e2, _ = get_quotes(
        query=q2_query,
        row=row,
        cache=cache,
        append_cache_path=append_cache_path,
        budget=budget,
        max_results=max_results,
        pause_seconds=pause_seconds,
    )
    merged = merge_quotes(q1, q2)
    result2 = choose_unique_market_candidate(
        row, merged, min_name=0.62, margin=0.08, use_class_hint=True
    )
    if result2.get("accepted"):
        result2["method"] = "EU_EXPECTED_MARKET_FILTER_TARGETED"
        return result2

    return {
        "accepted": False,
        "reason": "EU_REVIEW_REQUIRED",
        "errors": ";".join(x for x in [e1, e2] if x),
        "market_detail": result2,
    }


def remediate_jse(
    row: pd.Series,
    *,
    cache: dict[str, dict[str, Any]],
    append_cache_path: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
) -> dict[str, Any]:
    name = clean_text(row.get("Name"))
    q1, e1, _ = get_quotes(
        query=name,
        row=row,
        cache=cache,
        append_cache_path=append_cache_path,
        budget=budget,
        max_results=max_results,
        pause_seconds=pause_seconds,
    )
    q2, e2, _ = get_quotes(
        query=f"{name} JSE",
        row=row,
        cache=cache,
        append_cache_path=append_cache_path,
        budget=budget,
        max_results=max_results,
        pause_seconds=pause_seconds,
    )
    merged = merge_quotes(q1, q2)

    # JSE source rows had no ticker. Therefore share-class ambiguity must be treated
    # more strictly than Europe. A unique .JO equity can be promoted; multiple
    # credible .JO securities remain review-required.
    cands = market_candidates(row, merged)
    credible = [(ns, q) for ns, q in cands if ns >= 0.62]

    if len(credible) == 1:
        ns, q = credible[0]
        return {
            "accepted": True,
            "reason": "JSE_UNIQUE_MARKET_EQUITY",
            "method": "JSE_SECOND_PASS",
            "symbol": clean_text(q.get("symbol")).upper(),
            "result_name": quote_name(q),
            "exchange": clean_text(q.get("exchange")),
            "name_score": round(float(ns), 6),
            "candidate_count": 1,
        }

    if len(credible) > 1:
        # If the same company has more than one JSE security (e.g. ordinary vs BEE
        # share class), do not guess.
        return {
            "accepted": False,
            "reason": "JSE_MULTI_SECURITY_REVIEW",
            "candidate_count": len(credible),
            "candidates": [
                {
                    "symbol": clean_text(q.get("symbol")).upper(),
                    "name": quote_name(q),
                    "exchange": clean_text(q.get("exchange")),
                    "name_score": round(float(ns), 6),
                }
                for ns, q in credible[:6]
            ],
        }

    return {
        "accepted": False,
        "reason": "JSE_NO_UNIQUE_MARKET_EQUITY",
        "errors": ";".join(x for x in [e1, e2] if x),
        "candidate_count": 0,
    }


def classify_duplicate_groups(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    work = df.copy()
    work["_IssuerNorm"] = work["Name"].map(normalize_name)

    groups = []
    cross = []
    same = []

    for norm, g in work.groupby("_IssuerNorm", sort=False):
        if not norm or len(g) <= 1:
            continue

        mics = {clean_text(x) for x in g["Primary_MIC"].tolist()}
        ws_ids = g["WS_ID"].astype(str).tolist()
        symbols = g["Yahoo_Symbol"].astype(str).tolist()

        group_id = "NAME:" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]

        # Same venue can be a share-class pair or a false name collision; it is
        # blocking review. Different venues are retained as valid listings and are
        # non-blocking cross-listing candidates.
        nonempty_mics = {x for x in mics if x}
        same_venue = len(nonempty_mics) == 1 and len(mics) == 1

        kind = (
            "SAME_VENUE_POSSIBLE_DUPLICATE_REVIEW"
            if same_venue
            else "CROSS_LISTING_OR_DUAL_LISTING_NON_BLOCKING"
        )

        for _, r in g.iterrows():
            rec = {
                "Group_ID": group_id,
                "Classification": kind,
                "Normalized_Issuer_Name": norm,
                "WS_ID": clean_text(r.get("WS_ID")),
                "Name": clean_text(r.get("Name")),
                "Primary_Universe_Index": clean_text(r.get("Primary_Universe_Index")),
                "Primary_MIC": clean_text(r.get("Primary_MIC")),
                "Primary_Ticker": clean_text(r.get("Primary_Ticker")),
                "Yahoo_Symbol": clean_text(r.get("Yahoo_Symbol")),
                "ISIN": clean_text(r.get("ISIN")),
            }
            groups.append(rec)
            (same if same_venue else cross).append(rec)

    return (
        pd.DataFrame(groups),
        pd.DataFrame(cross),
        pd.DataFrame(same),
    )


def write_xlsx(
    master: pd.DataFrame,
    audit: pd.DataFrame,
    review: pd.DataFrame,
    cross: pd.DataFrame,
    same: pd.DataFrame,
    proposed: pd.DataFrame,
    summary: dict[str, Any],
    path: Path,
) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        master.to_excel(xw, sheet_name="Universe_Master", index=False)
        audit.to_excel(xw, sheet_name="Remediation_Audit", index=False)
        review.to_excel(xw, sheet_name="Review_Queue", index=False)
        cross.to_excel(xw, sheet_name="Cross_Listings", index=False)
        same.to_excel(xw, sheet_name="Same_Venue_Duplicates", index=False)
        proposed.to_excel(xw, sheet_name="Proposed_Overrides", index=False)
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


def offline_self_test() -> None:
    assert mexico_compact_symbol("GFNORTE O") == "GFNORTEO.MX"
    assert mexico_compact_symbol("CEMEX CPO") == "CEMEXCPO.MX"
    assert mexico_compact_symbol("LIVEPOL C-1") == "LIVEPOLC-1.MX"
    assert mexico_compact_symbol("PE&OLES *") == "PE&OLES.MX"

    assert ric_class_hint("CARLb.CO", "XCSE") == "CARL-B"
    assert ric_class_hint("ASSAb.ST", "XSTO") == "ASSA-B"

    # Meaningful "Group" is retained, preventing the v0.1 SoftBank collision.
    assert normalize_name("SoftBank Corp.") == "softbank"
    assert normalize_name("SoftBank Group Corp.") == "softbank group"

    # Cross-listing names still normalize together.
    assert normalize_name("The a2 Milk Company Limited") == "a2 milk"
    assert normalize_name("a2 Milk Company") == "a2 milk"

    print("IDENTITY_PROVIDER_REMEDIATION_V0_2_SELF_TEST_PASS")


def run(config: dict[str, Any]) -> dict[str, Any]:
    master_path = Path(config["audited_master_file"])
    audit_v1_path = Path(config["audit_v1_file"])
    seed_cache_path = Path(config["seed_search_cache"])
    runtime_cache_path = Path(config["runtime_search_cache"])
    output_dir = Path(config["output_dir"])

    if not master_path.exists():
        raise SystemExit(f"Audited master missing: {master_path}")
    if not audit_v1_path.exists():
        raise SystemExit(f"v0.1 mapping audit missing: {audit_v1_path}")

    master = pd.read_csv(master_path, keep_default_na=False, dtype=str)
    audit_v1 = pd.read_csv(audit_v1_path, keep_default_na=False, dtype=str)

    if len(master) != EXPECTED_ROWS or len(audit_v1) != EXPECTED_ROWS:
        raise SystemExit(
            f"Expected {EXPECTED_ROWS} rows; got master={len(master)}, audit={len(audit_v1)}"
        )
    if master["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.4 audited master")

    prior = audit_v1.set_index("WS_ID", drop=False).to_dict("index")
    cache = load_jsonl([seed_cache_path, runtime_cache_path])
    budget = {"used": 0, "max": int(config.get("max_new_search_queries", 500))}
    max_results = int(config.get("search_max_results", 12))
    pause_seconds = float(config.get("search_pause_seconds", 0.12))

    rows = []
    audit_rows = []
    proposed_overrides = []

    for _, src in master.iterrows():
        row = src.copy()
        ws = clean_text(src.get("WS_ID"))
        p = prior.get(ws, {})

        old_symbol = clean_text(src.get("Yahoo_Symbol")).upper()
        old_status = clean_text(src.get("Mapping_Status"))
        segment = clean_text(src.get("Primary_Universe_Index"))

        final_symbol = old_symbol
        final_status = old_status
        method = "CARRY_FORWARD"
        detail: dict[str, Any] = {}
        changed = False

        # 1) Deterministic Canadian NA repair.
        if ws == "WS:XTSE:NA":
            final_symbol = "NA.TO"
            final_status = "MARKET_RULE_VERIFIED_CA_NA"
            method = "CA_LEGITIMATE_NA_TICKER"
            detail = {"accepted": True, "reason": "CANONICAL_WS_ID_PLUS_MIC_RULE"}
            changed = True

        # 2) Mexico: official index symbols preserve class spacing, while Yahoo
        # uses compact symbols (e.g. GFNORTE O -> GFNORTEO.MX).
        elif segment == MX_SEGMENT and (
            not old_symbol
            or "SEARCH_" in old_status
        ):
            detail = remediate_mexico(
                row,
                cache=cache,
                append_cache_path=runtime_cache_path,
                budget=budget,
                max_results=max_results,
                pause_seconds=pause_seconds,
            )
            if detail.get("accepted"):
                final_symbol = clean_text(detail.get("symbol")).upper()
                final_status = "MARKET_RULE_VERIFIED_MX"
                method = clean_text(detail.get("method")) or "MX_REMEDIATION"
                changed = final_symbol != old_symbol or final_status != old_status

        # 3) Europe: reuse v0.1 search results, but filter to the expected Yahoo
        # market suffix first. This avoids rejecting the correct primary listing
        # merely because the same company also appears in Frankfurt/London/etc.
        elif segment == EU_SEGMENT and (
            not old_symbol
            or old_status in {"SEARCH_AMBIGUOUS", "SEARCH_NO_QUOTES", "SEARCH_ERROR"}
        ):
            detail = remediate_europe(
                row,
                cache=cache,
                append_cache_path=runtime_cache_path,
                budget=budget,
                max_results=max_results,
                pause_seconds=pause_seconds,
            )
            if detail.get("accepted"):
                final_symbol = clean_text(detail.get("symbol")).upper()
                final_status = "EXPECTED_MARKET_VERIFIED_EU"
                method = clean_text(detail.get("method")) or "EU_REMEDIATION"
                changed = final_symbol != old_symbol or final_status != old_status

        # 4) JSE: revalidate all 40, including the 20 provisional v0.1 mappings.
        # A unique .JO equity may be promoted. Multiple JSE securities remain review.
        elif segment == ZA_SEGMENT:
            detail = remediate_jse(
                row,
                cache=cache,
                append_cache_path=runtime_cache_path,
                budget=budget,
                max_results=max_results,
                pause_seconds=pause_seconds,
            )
            if detail.get("accepted"):
                final_symbol = clean_text(detail.get("symbol")).upper()
                final_status = "SECOND_PASS_REVALIDATED_JSE"
                method = "JSE_UNIQUE_MARKET_SEARCH"
                changed = final_symbol != old_symbol or final_status != old_status
            else:
                # Do not carry forward a provisional v0.1 JSE search mapping when
                # the second pass finds multiple/uncertain same-market securities.
                final_symbol = ""
                final_status = clean_text(detail.get("reason")) or "JSE_REVIEW_REQUIRED"
                method = "JSE_REVALIDATION_REVIEW"
                changed = bool(old_symbol) or final_status != old_status

        row["Yahoo_Symbol"] = final_symbol
        row["Mapping_Status"] = final_status
        row["Remediation_Method"] = method
        row["Remediation_UTC"] = utc_now()

        # Preserve original provider/source fields while supplying canonical
        # candidates for later promotion.
        row["Source_Primary_Ticker"] = clean_text(src.get("Primary_Ticker"))
        ticker_candidate = strip_suffix(final_symbol, expected_suffix(row)) if final_symbol else ""
        row["Primary_Ticker_Resolved_Candidate"] = ticker_candidate

        canonical_ws_candidate = ""
        if segment == ZA_SEGMENT and final_symbol:
            canonical_ws_candidate = f"WS:XJSE:{ticker_candidate}"
        row["Canonical_WS_ID_Candidate"] = canonical_ws_candidate

        rows.append(row)

        if final_symbol and (
            changed
            or old_status.startswith("SEARCH_")
            or segment in {MX_SEGMENT, ZA_SEGMENT}
        ):
            proposed_overrides.append({
                "WS_ID": ws,
                "Yahoo_Symbol": final_symbol,
                "Primary_Ticker_Source": clean_text(src.get("Primary_Ticker")),
                "Primary_Ticker_Resolved_Candidate": ticker_candidate,
                "Reason": final_status,
                "Verified_UTC": utc_now(),
            })

        audit_rows.append({
            "WS_ID": ws,
            "Name": clean_text(src.get("Name")),
            "Primary_Universe_Index": segment,
            "Country": clean_text(src.get("Country")),
            "Primary_MIC": clean_text(src.get("Primary_MIC")),
            "Primary_Ticker_Source": clean_text(src.get("Primary_Ticker")),
            "Yahoo_Symbol_Before": old_symbol,
            "Yahoo_Status_Before": old_status,
            "Yahoo_Symbol_After": final_symbol,
            "Yahoo_Status_After": final_status,
            "Remediation_Method": method,
            "Changed": bool(changed),
            "Detail_Reason": clean_text(detail.get("reason")),
            "Detail_Result_Name": clean_text(detail.get("result_name")),
            "Detail_Exchange": clean_text(detail.get("exchange")),
            "Detail_Name_Score": detail.get("name_score", ""),
            "Detail_Margin": detail.get("margin", ""),
            "Detail_Candidate_Count": detail.get("candidate_count", ""),
            "Canonical_WS_ID_Candidate": canonical_ws_candidate,
        })

    remediated = pd.DataFrame(rows)
    rem_audit = pd.DataFrame(audit_rows)

    if len(remediated) != EXPECTED_ROWS:
        raise SystemExit("Row-count invariant failed after remediation")
    if remediated["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("WS_ID uniqueness invariant failed after remediation")

    dup_all, cross_df, same_df = classify_duplicate_groups(remediated)
    same_ws = set(same_df["WS_ID"].astype(str)) if not same_df.empty else set()

    # Review is now restricted to provider-unresolved rows and genuine same-venue
    # duplicate/share-class ambiguity. Expected cross-listings are explicitly
    # non-blocking.
    rem_audit["Provider_Unresolved"] = rem_audit["Yahoo_Symbol_After"].astype(str).str.len().eq(0)
    rem_audit["Same_Venue_Duplicate_Review"] = rem_audit["WS_ID"].astype(str).isin(same_ws)
    rem_audit["Needs_Review"] = (
        rem_audit["Provider_Unresolved"]
        | rem_audit["Same_Venue_Duplicate_Review"]
    )
    review_df = rem_audit.loc[rem_audit["Needs_Review"]].copy()

    mapped = int((rem_audit["Yahoo_Symbol_After"].astype(str).str.len() > 0).sum())
    unresolved = EXPECTED_ROWS - mapped
    changed_count = int(rem_audit["Changed"].astype(bool).sum())

    segment_mapping = {}
    for segment, g in rem_audit.groupby("Primary_Universe_Index"):
        smapped = int((g["Yahoo_Symbol_After"].astype(str).str.len() > 0).sum())
        segment_mapping[str(segment)] = {
            "rows": int(len(g)),
            "mapped": smapped,
            "mapped_pct": round(100.0 * smapped / len(g), 4),
            "review": int(g["Needs_Review"].astype(bool).sum()),
            "changed": int(g["Changed"].astype(bool).sum()),
        }

    status_counts = Counter(rem_audit["Yahoo_Status_After"].astype(str))

    summary = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "run_status": (
            "REMEDIATION_COMPLETE"
            if len(review_df) == 0
            else "REMEDIATION_COMPLETE_WITH_REVIEW_QUEUE"
        ),
        "rows": EXPECTED_ROWS,
        "provider_mapped": mapped,
        "provider_mapping_pct": round(100.0 * mapped / EXPECTED_ROWS, 4),
        "provider_unresolved": unresolved,
        "review_queue_rows": int(len(review_df)),
        "same_venue_duplicate_review_rows": int(len(same_df)),
        "cross_listing_rows_non_blocking": int(len(cross_df)),
        "changed_rows": changed_count,
        "new_search_queries_used": int(budget["used"]),
        "new_search_query_budget": int(budget["max"]),
        "mapping_status_counts": dict(sorted(status_counts.items())),
        "segment_mapping": segment_mapping,
        "price_run_allowed_after_this_step": False,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "p0_run": P0_RUN,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "No price/history/OHLCV call is performed.",
            "TSX ticker NA is deterministically restored as NA.TO.",
            "Mexico class notation is normalized only when Yahoo Search verifies the compact exact symbol or a unique expected-market candidate.",
            "European v0.1 ambiguous results are rescored after filtering to the expected Yahoo market suffix.",
            "All 40 JSE rows are revalidated; provisional v0.1 JSE mappings are demoted if multiple same-market securities remain possible.",
            "Expected cross-listings are non-blocking and are not merged.",
            "Only same-venue duplicate/share-class ambiguity remains duplicate-review blocking.",
            "Generated provider overrides are proposals; the production override registry is not modified by this workflow.",
            "P0 and productive trading remain disabled.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    master_csv = Path(config["remediated_master_csv"])
    master_xlsx = Path(config["remediated_master_xlsx"])
    master_csv.parent.mkdir(parents=True, exist_ok=True)

    remediated.to_csv(master_csv, index=False)
    rem_audit.to_csv(output_dir / "remediation_audit_v0.2.csv", index=False)
    review_df.to_csv(output_dir / "review_queue_v0.2.csv", index=False)
    cross_df.to_csv(output_dir / "cross_listing_candidates_v0.2.csv", index=False)
    same_df.to_csv(output_dir / "same_venue_duplicate_review_v0.2.csv", index=False)
    proposed_df = pd.DataFrame(proposed_overrides).drop_duplicates(
        subset=["WS_ID"], keep="last"
    ) if proposed_overrides else pd.DataFrame(columns=[
        "WS_ID", "Yahoo_Symbol", "Primary_Ticker_Source",
        "Primary_Ticker_Resolved_Candidate", "Reason", "Verified_UTC"
    ])
    proposed_df.to_csv(output_dir / "proposed_yahoo_overrides_v0.2.csv", index=False)
    (output_dir / "summary_v0.2.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if runtime_cache_path.exists():
        (output_dir / "search_cache_increment_v0.2.jsonl").write_text(
            runtime_cache_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    else:
        (output_dir / "search_cache_increment_v0.2.jsonl").write_text("", encoding="utf-8")

    write_xlsx(
        remediated,
        rem_audit,
        review_df,
        cross_df,
        same_df,
        proposed_df,
        summary,
        master_xlsx,
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

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    run(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
