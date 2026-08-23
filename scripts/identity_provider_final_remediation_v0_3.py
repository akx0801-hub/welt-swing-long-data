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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from price_cache import MIC_SUFFIX_RULES  # noqa: E402

SCHEMA = "WELT_SWING_IDENTITY_PROVIDER_FINAL_REMEDIATION_V0_3"
EXPECTED_ROWS = 3664
EXPECTED_REVIEW_INPUT = 121

PRODUCTIVE_TRADING_AUTHORITY = False
P0_RUN = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_HISTORY_ALLOWED = False

# Curated candidates are provider-symbol candidates, not canonical identity changes.
# They were assembled specifically for the 121 rows left after remediation v0.2.
# Every normal candidate must still be validated against Yahoo Search at runtime,
# unless it is in PUBLIC_REFERENCE_CONFIRMED below.
CURATED_CANDIDATES: dict[str, str] = {
    # Netherlands / Belgium
    "WS:XAMS:AKZO.AS": "AKZA.AS",
    "WS:XAMS:ARDS.AS": "ARCAD.AS",
    "WS:XAMS:BAMN.AS": "BAMNB.AS",
    "WS:XAMS:EXOR.AS": "EXO.AS",
    "WS:XAMS:PHG.AS": "PHIA.AS",
    "WS:XAMS:VOPA.AS": "VPK.AS",
    "WS:XBRU:WDPP.BR": "WDP.BR",

    # Denmark / Ireland
    "WS:XCSE:ALKB.CO": "ALK-B.CO",
    "WS:XCSE:MAERSKB.CO": "MAERSK-B.CO",
    "WS:XCSE:ROCKB.CO": "ROCK-B.CO",
    "WS:XDUB:KSP.I": "KRX.IR",
    "WS:XDUB:KYGA.I": "KRZ.IR",

    # Germany
    "WS:XETR:AG1G.DE": "AG1.DE",
    "WS:XETR:BEIG.DE": "BEI.DE",
    "WS:XETR:BMWG.DE": "BMW.DE",
    "WS:XETR:DB1GN.DE": "DB1.DE",
    "WS:XETR:EONGN.DE": "EOAN.DE",
    "WS:XETR:FMEG.DE": "FME.DE",
    "WS:XETR:FPE3_P.DE": "FPE3.DE",
    "WS:XETR:FREG.DE": "FRE.DE",
    "WS:XETR:FTKN.DE": "FTK.DE",
    "WS:XETR:G1AG.DE": "G1A.DE",
    "WS:XETR:HNKG_P.DE": "HEN3.DE",
    "WS:XETR:MUVGN.DE": "MUV2.DE",
    "WS:XETR:PSHG_P.DE": "PAH3.DE",
    "WS:XETR:RAAG.DE": "RAA.DE",
    "WS:XETR:SATG_P.DE": "SRT3.DE",
    "WS:XETR:SDFGN.DE": "SDF.DE",
    "WS:XETR:SIEGN.DE": "SIE.DE",
    "WS:XETR:VOWG_P.DE": "VOW3.DE",

    # United Kingdom
    "WS:XLON:ADML.L": "ADM.L",
    "WS:XLON:BKGH.L": "BKG.L",
    "WS:XLON:BT.L": "BT-A.L",
    "WS:XLON:ICAG.L": "IAG.L",
    "WS:XLON:ICGIN.L": "ICG.L",
    "WS:XLON:SJP.L": "STJ.L",

    # Spain
    "WS:XMAD:AMA.MC": "AMS.MC",
    "WS:XMAD:PUIGB.MC": "PUIG.MC",
    "WS:XMAD:SABE.MC": "SAB.MC",

    # Italy
    "WS:XMIL:A2.MI": "A2A.MI",
    "WS:XMIL:AZMT.MI": "AZM.MI",
    "WS:XMIL:BCU.MI": "BC.MI",
    "WS:XMIL:GASI.MI": "G.MI",
    "WS:XMIL:HRA.MI": "HER.MI",
    "WS:XMIL:ITPG.MI": "IP.MI",
    "WS:XMIL:NEXII.MI": "NEXI.MI",
    "WS:XMIL:RECI.MI": "REC.MI",
    "WS:XMIL:TENR.MI": "TEN.MI",

    # Norway
    "WS:XOSL:GJFG.OL": "GJF.OL",

    # France
    "WS:XPAR:BOUY.PA": "EN.PA",
    "WS:XPAR:CAGR.PA": "ACA.PA",
    "WS:XPAR:CAPP.PA": "CAP.PA",
    "WS:XPAR:DAST.PA": "DSY.PA",
    "WS:XPAR:HRMS.PA": "RMS.PA",
    "WS:XPAR:LVMH.PA": "MC.PA",
    "WS:XPAR:MICP.PA": "ML.PA",
    "WS:XPAR:PUBP.PA": "PUB.PA",
    "WS:XPAR:SCOR.PA": "SCR.PA",
    "WS:XPAR:SOGN.PA": "GLE.PA",

    # Sweden
    "WS:XSTO:ADDTB.ST": "ADDT-B.ST",
    "WS:XSTO:AVANZ.ST": "AZA.ST",
    "WS:XSTO:BALDB.ST": "BALD-B.ST",
    "WS:XSTO:BEIJB.ST": "BEIJ-B.ST",
    "WS:XSTO:EPIRA.ST": "EPIR-A.ST",
    "WS:XSTO:ERICB.ST": "ERIC-B.ST",
    "WS:XSTO:ESSITYB.ST": "ESSITY-B.ST",
    "WS:XSTO:GETIB.ST": "GETI-B.ST",
    "WS:XSTO:HEXAB.ST": "HEXA-B.ST",
    "WS:XSTO:HMB.ST": "HM-B.ST",
    "WS:XSTO:HOLMB.ST": "HOLM-B.ST",
    "WS:XSTO:INDUC.ST": "INDU-C.ST",
    "WS:XSTO:INVEB.ST": "INVE-B.ST",
    "WS:XSTO:LAGRB.ST": "LAGR-B.ST",
    "WS:XSTO:LATOB.ST": "LATO-B.ST",
    "WS:XSTO:LIFCOB.ST": "LIFCO-B.ST",
    "WS:XSTO:LUNDB.ST": "LUND-B.ST",
    "WS:XSTO:NIBEB.ST": "NIBE-B.ST",
    # Octave SDR has no stable Yahoo Stockholm symbol observed; OCTV is the
    # 1:1 underlying Class B ordinary share on Nasdaq, documented by issuer/Nasdaq.
    "WS:XSTO:OCTVSDB.ST": "OCTV",
    "WS:XSTO:SAABB.ST": "SAAB-B.ST",
    "WS:XSTO:SAGAB.ST": "SAGA-B.ST",
    "WS:XSTO:SCAB.ST": "SCA-B.ST",
    "WS:XSTO:SEBA.ST": "SEB-A.ST",
    "WS:XSTO:SECTB.ST": "SECT-B.ST",
    "WS:XSTO:SECUB.ST": "SECU-B.ST",
    "WS:XSTO:SKAB.ST": "SKA-B.ST",
    "WS:XSTO:SKFB.ST": "SKF-B.ST",
    "WS:XSTO:SSABB.ST": "SSAB-B.ST",
    "WS:XSTO:SWECB.ST": "SWEC-B.ST",
    "WS:XSTO:TEL2B.ST": "TEL2-B.ST",
    "WS:XSTO:TRELB.ST": "TREL-B.ST",
    "WS:XSTO:VOLVB.ST": "VOLV-B.ST",

    # Switzerland / Austria
    "WS:XSWX:ALCC.S": "ALC.SW",
    "WS:XSWX:COTNE.S": "COTN.SW",
    "WS:XSWX:HBANC.S": "HBAN.SW",
    "WS:XSWX:ROPC.S": "ROG.SW",
    "WS:XSWX:SRENH.S": "SREN.SW",
    "WS:XWBO:OMVV.VI": "OMV.VI",

    # Mexico
    "WS:XMEX:ALFAA": "ALFAA.MX",
    "WS:XMEX:FEMSAUBD": "FEMSAUBD.MX",
    "WS:XMEX:GFINBURO": "GFINBURO.MX",
    "WS:XMEX:GFNORTEO": "GFNORTEO.MX",
    "WS:XMEX:MEGACPO": "MEGACPO.MX",
    "WS:XMEX:VOLARA": "VOLARA.MX",

    # South Africa / JSE
    "WS:SRC:ZA_TOP40:226ACE3524DC99B3": "INL.JO",  # Investec Ltd
    "WS:SRC:ZA_TOP40:269DEF2006BCDC3A": "IMP.JO",  # Implats
    "WS:SRC:ZA_TOP40:2DF0FDC7A9EB6AF3": "ANH.JO",  # AB InBev
    "WS:SRC:ZA_TOP40:3372028E3DD353C9": "ABG.JO",  # Absa
    "WS:SRC:ZA_TOP40:3598A879F2EA6E99": "SLM.JO",  # Sanlam
    "WS:SRC:ZA_TOP40:826AEDDC44AC58D6": "RMH.JO",  # RMB Holdings
    "WS:SRC:ZA_TOP40:8D915874D6D1F74D": "GRT.JO",  # Growthpoint
    "WS:SRC:ZA_TOP40:A5EBFF44983C436F": "BID.JO",  # Bidcorp
    "WS:SRC:ZA_TOP40:A707BAE04D25DE84": "GFI.JO",  # Gold Fields
    "WS:SRC:ZA_TOP40:B9672938BA6AA893": "FSR.JO",  # FirstRand
    "WS:SRC:ZA_TOP40:C3D446CB310D4D8C": "CPI.JO",  # Capitec
    "WS:SRC:ZA_TOP40:C4F89DB729DA585F": "BHG.JO",  # BHP
    "WS:SRC:ZA_TOP40:CA5BCEC12F716F44": "BTI.JO",  # BAT
    "WS:SRC:ZA_TOP40:CCFFACA1ACD941D3": "SBK.JO",  # Standard Bank
    "WS:SRC:ZA_TOP40:DFFDE2958F9E4E6C": "MNP.JO",  # Mondi
    "WS:SRC:ZA_TOP40:EEEF37437472AD5D": "APN.JO",  # Aspen
    "WS:SRC:ZA_TOP40:FA44132B238E6795": "DSY.JO",  # Discovery
}

# MultiChoice has been taken over and appears delisted. Do not manufacture a live
# provider mapping for a stale source constituent.
STALE_EXCLUSIONS = {
    "WS:SRC:ZA_TOP40:8096AB44770BB485": {
        "reason": "DELISTED_TAKEOVER_SOURCE_STALE",
        "name": "MultiChoice",
    }
}

# These exact candidate mappings have separate public/issuer evidence and may be
# accepted even if Yahoo Search happens to omit the exact symbol in one run.
# This is intentionally small.
PUBLIC_REFERENCE_CONFIRMED = {
    "WS:XAMS:ARDS.AS",                       # Arcadis -> ARCAD.AS (Yahoo page)
    "WS:XSTO:OCTVSDB.ST",                    # Octave 1:1 underlying -> OCTV
    "WS:XSWX:HBANC.S",                       # Helvetia Baloise -> HBAN.SW
    "WS:XMEX:FEMSAUBD",                      # Yahoo comparable listing
    "WS:SRC:ZA_TOP40:269DEF2006BCDC3A",      # IMP.JO
    "WS:SRC:ZA_TOP40:2DF0FDC7A9EB6AF3",      # ANH.JO
    "WS:SRC:ZA_TOP40:3372028E3DD353C9",      # ABG.JO
    "WS:SRC:ZA_TOP40:826AEDDC44AC58D6",      # RMH.JO
    "WS:SRC:ZA_TOP40:8D915874D6D1F74D",      # GRT.JO
    "WS:SRC:ZA_TOP40:A707BAE04D25DE84",      # GFI.JO
    "WS:SRC:ZA_TOP40:B9672938BA6AA893",      # FSR.JO
    "WS:SRC:ZA_TOP40:C3D446CB310D4D8C",      # CPI.JO
    "WS:SRC:ZA_TOP40:C4F89DB729DA585F",      # BHG.JO
    "WS:SRC:ZA_TOP40:CA5BCEC12F716F44",      # BTI.JO
    "WS:SRC:ZA_TOP40:CCFFACA1ACD941D3",      # SBK.JO
    "WS:SRC:ZA_TOP40:DFFDE2958F9E4E6C",      # MNP.JO
    "WS:SRC:ZA_TOP40:EEEF37437472AD5D",      # APN.JO
    "WS:SRC:ZA_TOP40:FA44132B238E6795",      # DSY.JO
}

ALTERNATE_LISTING_EQUIVALENT = {
    "WS:XSTO:OCTVSDB.ST": {
        "provider_listing_type": "ALTERNATE_UNDERLYING_1_TO_1",
        "note": "Nasdaq OCTV Class B ordinary share; Stockholm OCTV SDB is a 1:1 SDR and temporary program.",
    }
}


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


def norm_name(v: Any) -> str:
    s = clean_text(v)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    legal = {
        "ag","sa","se","nv","plc","inc","incorporated","corp","corporation",
        "co","company","limited","ltd","spa","srl","ab","asa","oyj","pte",
        "llc","lp","cv","sab",
    }
    toks = s.split()
    while toks and toks[-1] in legal:
        toks.pop()
    while toks and toks[0] == "the":
        toks.pop(0)
    return " ".join(toks)


def name_similarity(a: Any, b: Any) -> float:
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    contain = len(ta & tb) / min(len(ta), len(tb)) if ta and tb else 0.0
    return max(seq, contain)


def quote_name(q: dict[str, Any]) -> str:
    return clean_text(q.get("longname") or q.get("shortname") or q.get("name") or q.get("symbol"))


def is_equity(q: dict[str, Any]) -> bool:
    qt = clean_text(q.get("quoteType")).upper()
    return qt in {"", "EQUITY"}


def yahoo_search(query: str, max_results: int) -> list[dict[str, Any]]:
    # Search only. No download(), history(), chart or OHLCV call.
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


def append_cache(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def load_cache(*paths: Path) -> dict[str, dict[str, Any]]:
    out = {}
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            k = clean_text(o.get("cache_key"))
            if k:
                out[k] = o
    return out


def cache_key(query: str) -> str:
    return hashlib.sha256(("FINAL_V03|" + query).encode("utf-8")).hexdigest()


def get_quotes(
    query: str,
    *,
    cache: dict[str, dict[str, Any]],
    runtime_cache: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
) -> tuple[list[dict[str, Any]], str, bool]:
    key = cache_key(query)
    if key in cache:
        o = cache[key]
        return list(o.get("quotes") or []), clean_text(o.get("error")), True

    if budget["used"] >= budget["max"]:
        return [], "SEARCH_BUDGET_EXCEEDED", False

    budget["used"] += 1
    err = ""
    try:
        quotes = yahoo_search(query, max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        quotes = []
        err = f"{type(exc).__name__}: {exc}"

    o = {
        "cache_key": key,
        "query": query,
        "quotes": quotes,
        "error": err,
        "fetched_utc": utc_now(),
        "schema": SCHEMA,
    }
    cache[key] = o
    append_cache(runtime_cache, o)
    if pause_seconds:
        time.sleep(pause_seconds)
    return quotes, err, False


def expected_suffix(row: pd.Series) -> str:
    return MIC_SUFFIX_RULES.get(clean_text(row.get("Primary_MIC")).upper(), "")


def candidate_market_ok(row: pd.Series, symbol: str) -> bool:
    ws = clean_text(row.get("WS_ID"))
    if ws in ALTERNATE_LISTING_EQUIVALENT:
        return True
    suffix = expected_suffix(row).upper()
    return bool(suffix and clean_text(symbol).upper().endswith(suffix))


def validate_candidate(
    row: pd.Series,
    candidate: str,
    *,
    cache: dict[str, dict[str, Any]],
    runtime_cache: Path,
    budget: dict[str, int],
    max_results: int,
    pause_seconds: float,
) -> dict[str, Any]:
    queries = [
        candidate,
        clean_text(row.get("Name")),
        f"{clean_text(row.get('Name'))} {candidate}",
    ]
    seen = set()
    quotes: list[dict[str, Any]] = []
    errors = []

    for query in queries:
        q = query.strip()
        if not q or q.casefold() in seen:
            continue
        seen.add(q.casefold())
        qq, err, _ = get_quotes(
            q,
            cache=cache,
            runtime_cache=runtime_cache,
            budget=budget,
            max_results=max_results,
            pause_seconds=pause_seconds,
        )
        quotes.extend(qq)
        if err:
            errors.append(err)

    candidate_u = candidate.upper()
    exact = []
    for q in quotes:
        sym = clean_text(q.get("symbol")).upper()
        if sym == candidate_u and is_equity(q):
            exact.append(q)

    if exact:
        ranked = sorted(
            [(name_similarity(row.get("Name"), quote_name(q)), q) for q in exact],
            key=lambda x: x[0],
            reverse=True,
        )
        ns, q = ranked[0]
        return {
            "accepted": candidate_market_ok(row, candidate),
            "reason": "CURATED_CANDIDATE_YAHOO_SEARCH_VERIFIED",
            "candidate": candidate_u,
            "result_name": quote_name(q),
            "exchange": clean_text(q.get("exchange")),
            "name_score": round(float(ns), 6),
            "errors": ";".join(errors),
        }

    ws = clean_text(row.get("WS_ID"))
    if ws in PUBLIC_REFERENCE_CONFIRMED:
        return {
            "accepted": True,
            "reason": (
                "PUBLIC_REFERENCE_ALTERNATE_LISTING_VERIFIED"
                if ws in ALTERNATE_LISTING_EQUIVALENT
                else "PUBLIC_REFERENCE_CURATED_SYMBOL_VERIFIED"
            ),
            "candidate": candidate_u,
            "result_name": "",
            "exchange": "",
            "name_score": "",
            "errors": ";".join(errors),
        }

    return {
        "accepted": False,
        "reason": "CURATED_CANDIDATE_NOT_YAHOO_VERIFIED",
        "candidate": candidate_u,
        "result_name": "",
        "exchange": "",
        "name_score": "",
        "errors": ";".join(errors),
    }


def strip_suffix_for_ticker(row: pd.Series, symbol: str) -> str:
    if clean_text(row.get("WS_ID")) in ALTERNATE_LISTING_EQUIVALENT:
        return clean_text(symbol).upper()
    suffix = expected_suffix(row).upper()
    s = clean_text(symbol).upper()
    return s[:-len(suffix)] if suffix and s.endswith(suffix) else s


def offline_self_test() -> None:
    targeted = set(CURATED_CANDIDATES) | set(STALE_EXCLUSIONS)
    assert len(targeted) == EXPECTED_REVIEW_INPUT, len(targeted)

    assert CURATED_CANDIDATES["WS:XETR:BMWG.DE"] == "BMW.DE"
    assert CURATED_CANDIDATES["WS:XETR:VOWG_P.DE"] == "VOW3.DE"
    assert CURATED_CANDIDATES["WS:XPAR:LVMH.PA"] == "MC.PA"
    assert CURATED_CANDIDATES["WS:XSTO:VOLVB.ST"] == "VOLV-B.ST"
    assert CURATED_CANDIDATES["WS:XMEX:GFNORTEO"] == "GFNORTEO.MX"
    assert CURATED_CANDIDATES["WS:SRC:ZA_TOP40:C4F89DB729DA585F"] == "BHG.JO"
    assert "WS:SRC:ZA_TOP40:8096AB44770BB485" in STALE_EXCLUSIONS

    print(f"FINAL_REMEDIATION_V03_SELF_TEST_PASS targeted={len(targeted)}")


def run(cfg: dict[str, Any]) -> dict[str, Any]:
    master_path = Path(cfg["remediated_master_file"])
    review_path = Path(cfg["review_v02_file"])
    seed_cache = Path(cfg["seed_search_cache"])
    runtime_cache = Path(cfg["runtime_search_cache"])
    output_dir = Path(cfg["output_dir"])

    master = pd.read_csv(master_path, keep_default_na=False, dtype=str)
    review = pd.read_csv(review_path, keep_default_na=False, dtype=str)

    if len(master) != EXPECTED_ROWS:
        raise SystemExit(f"Expected {EXPECTED_ROWS} master rows, got {len(master)}")
    if len(review) != EXPECTED_REVIEW_INPUT:
        raise SystemExit(f"Expected {EXPECTED_REVIEW_INPUT} review rows, got {len(review)}")
    if master["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.5 master")

    expected_ids = set(review["WS_ID"].astype(str))
    covered_ids = set(CURATED_CANDIDATES) | set(STALE_EXCLUSIONS)
    if expected_ids != covered_ids:
        missing = sorted(expected_ids - covered_ids)
        extra = sorted(covered_ids - expected_ids)
        raise SystemExit(f"Review coverage mismatch missing={missing} extra={extra}")

    cache = load_cache(seed_cache, runtime_cache)
    budget = {"used": 0, "max": int(cfg.get("max_new_search_queries", 450))}
    max_results = int(cfg.get("search_max_results", 15))
    pause_seconds = float(cfg.get("search_pause_seconds", 0.10))

    target_ids = set(expected_ids)
    rows = []
    audit_rows = []
    promotions = []
    stale_rows = []

    for _, src in master.iterrows():
        row = src.copy()
        ws = clean_text(row.get("WS_ID"))
        old_symbol = clean_text(row.get("Yahoo_Symbol"))
        old_status = clean_text(row.get("Mapping_Status"))

        changed = False
        final_symbol = old_symbol
        final_status = old_status
        provider_listing_type = clean_text(row.get("Provider_Listing_Type")) or "PRIMARY"
        detail = {"reason": "NOT_TARGETED"}

        if ws in STALE_EXCLUSIONS:
            final_symbol = ""
            final_status = "SOURCE_STALE_DELISTED_EXCLUDED"
            provider_listing_type = "NONE"
            row["Active"] = "False"
            row["Universe_Status"] = "SOURCE_STALE_DELISTED_EXCLUDED"
            detail = {
                "accepted": False,
                "reason": STALE_EXCLUSIONS[ws]["reason"],
            }
            changed = True
            stale_rows.append({
                "WS_ID": ws,
                "Name": clean_text(row.get("Name")),
                "Reason": STALE_EXCLUSIONS[ws]["reason"],
                "Action": "Active=False; excluded from active provider denominator",
            })

        elif ws in CURATED_CANDIDATES:
            candidate = CURATED_CANDIDATES[ws]
            detail = validate_candidate(
                row,
                candidate,
                cache=cache,
                runtime_cache=runtime_cache,
                budget=budget,
                max_results=max_results,
                pause_seconds=pause_seconds,
            )
            if detail.get("accepted"):
                final_symbol = candidate
                final_status = clean_text(detail.get("reason"))
                if ws in ALTERNATE_LISTING_EQUIVALENT:
                    provider_listing_type = ALTERNATE_LISTING_EQUIVALENT[ws]["provider_listing_type"]
                else:
                    provider_listing_type = "PRIMARY"
                changed = final_symbol != old_symbol or final_status != old_status
                promotions.append({
                    "WS_ID": ws,
                    "Name": clean_text(row.get("Name")),
                    "Yahoo_Symbol": final_symbol,
                    "Source_Primary_Ticker": clean_text(row.get("Primary_Ticker")),
                    "Resolved_Ticker_Candidate": strip_suffix_for_ticker(row, final_symbol),
                    "Mapping_Status": final_status,
                    "Provider_Listing_Type": provider_listing_type,
                    "Reference_Note": (
                        ALTERNATE_LISTING_EQUIVALENT.get(ws, {}).get("note", "")
                    ),
                    "Verified_UTC": utc_now(),
                })
            else:
                # Keep unresolved. v0.3 must not invent provider availability.
                final_symbol = ""
                final_status = clean_text(detail.get("reason"))
                provider_listing_type = "UNRESOLVED"
                changed = final_symbol != old_symbol or final_status != old_status

        row["Yahoo_Symbol"] = final_symbol
        row["Mapping_Status"] = final_status
        row["Provider_Listing_Type"] = provider_listing_type
        row["Final_Remediation_UTC"] = utc_now()
        row["Final_Resolved_Ticker_Candidate"] = (
            strip_suffix_for_ticker(row, final_symbol) if final_symbol else ""
        )
        rows.append(row)

        if ws in target_ids:
            audit_rows.append({
                "WS_ID": ws,
                "Name": clean_text(row.get("Name")),
                "Primary_Universe_Index": clean_text(row.get("Primary_Universe_Index")),
                "Primary_MIC": clean_text(row.get("Primary_MIC")),
                "Source_Primary_Ticker": clean_text(src.get("Primary_Ticker")),
                "Yahoo_Symbol_Before": old_symbol,
                "Yahoo_Status_Before": old_status,
                "Curated_Candidate": clean_text(CURATED_CANDIDATES.get(ws)),
                "Yahoo_Symbol_After": final_symbol,
                "Yahoo_Status_After": final_status,
                "Provider_Listing_Type": provider_listing_type,
                "Changed": bool(changed),
                "Validation_Reason": clean_text(detail.get("reason")),
                "Yahoo_Result_Name": clean_text(detail.get("result_name")),
                "Yahoo_Result_Exchange": clean_text(detail.get("exchange")),
                "Name_Score": detail.get("name_score", ""),
                "Errors": clean_text(detail.get("errors")),
                "Active_After": clean_text(row.get("Active")),
            })

    final_master = pd.DataFrame(rows)
    audit_df = pd.DataFrame(audit_rows)

    if len(final_master) != EXPECTED_ROWS:
        raise SystemExit("Final master row-count invariant failed")
    if final_master["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Final master WS_ID uniqueness invariant failed")
    if len(audit_df) != EXPECTED_REVIEW_INPUT:
        raise SystemExit("Target audit row-count invariant failed")

    active_mask = final_master["Active"].astype(str).str.lower().isin({"true","1","yes","active"})
    # Old source rows should be active unless explicitly disabled. Empty Active is not treated
    # as active here; verify the input convention separately in the workflow.
    active_rows = int(active_mask.sum())
    active_mapped = int(
        (active_mask & final_master["Yahoo_Symbol"].astype(str).str.len().gt(0)).sum()
    )
    active_unresolved = active_rows - active_mapped

    target_unresolved = audit_df[
        audit_df["Yahoo_Symbol_After"].astype(str).str.len().eq(0)
        & audit_df["Yahoo_Status_After"].ne("SOURCE_STALE_DELISTED_EXCLUDED")
    ].copy()

    output_dir.mkdir(parents=True, exist_ok=True)
    final_csv = Path(cfg["final_master_csv"])
    final_xlsx = Path(cfg["final_master_xlsx"])
    final_csv.parent.mkdir(parents=True, exist_ok=True)

    final_master.to_csv(final_csv, index=False)
    audit_df.to_csv(output_dir / "final_remediation_audit_v0.3.csv", index=False)
    target_unresolved.to_csv(output_dir / "review_queue_v0.3.csv", index=False)

    promotions_df = pd.DataFrame(promotions)
    promotions_df.to_csv(output_dir / "promotion_overrides_v0.3.csv", index=False)

    stale_df = pd.DataFrame(stale_rows)
    stale_df.to_csv(output_dir / "stale_exclusions_v0.3.csv", index=False)

    status_counts = dict(sorted(Counter(audit_df["Yahoo_Status_After"].astype(str)).items()))
    segment_counts = {}
    for seg, g in audit_df.groupby("Primary_Universe_Index"):
        mapped = int(g["Yahoo_Symbol_After"].astype(str).str.len().gt(0).sum())
        stale = int(g["Yahoo_Status_After"].eq("SOURCE_STALE_DELISTED_EXCLUDED").sum())
        unresolved = len(g) - mapped - stale
        segment_counts[str(seg)] = {
            "target_rows": int(len(g)),
            "resolved": mapped,
            "stale_excluded": stale,
            "unresolved": int(unresolved),
        }

    summary = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "run_status": (
            "FINAL_REMEDIATION_COMPLETE"
            if len(target_unresolved) == 0
            else "FINAL_REMEDIATION_COMPLETE_WITH_REVIEW_QUEUE"
        ),
        "master_rows": EXPECTED_ROWS,
        "target_review_input_rows": EXPECTED_REVIEW_INPUT,
        "target_resolved_provider_rows": int(
            audit_df["Yahoo_Symbol_After"].astype(str).str.len().gt(0).sum()
        ),
        "target_stale_excluded_rows": int(
            audit_df["Yahoo_Status_After"].eq("SOURCE_STALE_DELISTED_EXCLUDED").sum()
        ),
        "target_unresolved_rows": int(len(target_unresolved)),
        "active_rows": active_rows,
        "active_provider_mapped": active_mapped,
        "active_provider_unresolved": active_unresolved,
        "active_provider_mapping_pct": (
            round(100.0 * active_mapped / active_rows, 4) if active_rows else 0.0
        ),
        "new_search_queries_used": int(budget["used"]),
        "new_search_query_budget": int(budget["max"]),
        "target_status_counts": status_counts,
        "target_segment_counts": segment_counts,
        "price_run_candidate_coverage_ready": (
            active_rows > 0 and (active_mapped / active_rows) >= 0.995
        ),
        "price_run_allowed_after_this_step": False,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "p0_run": P0_RUN,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "No price/history/OHLCV call is performed.",
            "All 121 v0.2 review rows are explicitly covered by a candidate or stale-exclusion decision.",
            "Curated candidates are normally promoted only when Yahoo Search returns the exact equity symbol.",
            "A small PUBLIC_REFERENCE_CONFIRMED set may be promoted from independent public/issuer evidence when Yahoo Search omits the exact candidate.",
            "Octave Stockholm SDR is represented by the documented 1:1 Nasdaq Class B underlying OCTV and is flagged as an alternate underlying mapping.",
            "MultiChoice is marked stale/delisted rather than assigned a fabricated live provider symbol.",
            "No canonical WS_ID is changed in this step.",
            "Production override registry is not modified automatically.",
            "P0 and productive trading remain disabled.",
        ],
    }
    (output_dir / "summary_v0.3.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with pd.ExcelWriter(final_xlsx, engine="openpyxl") as xw:
        final_master.to_excel(xw, sheet_name="Universe_Master", index=False)
        audit_df.to_excel(xw, sheet_name="Final_Remediation", index=False)
        target_unresolved.to_excel(xw, sheet_name="Review_Queue", index=False)
        promotions_df.to_excel(xw, sheet_name="Promotion_Overrides", index=False)
        stale_df.to_excel(xw, sheet_name="Stale_Exclusions", index=False)
        pd.DataFrame([
            {"Key": k, "Value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict,list)) else v}
            for k, v in summary.items()
        ]).to_excel(xw, sheet_name="Run_Summary", index=False)

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
