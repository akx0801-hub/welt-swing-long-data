#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup


SCHEMA = "WELT_SWING_UNIVERSE_PHASE2_SOURCE_SUPERSET_V0_3"
EXPECTED_BASE_ROWS = 1535

BASE_SEGMENTS = [
    "EU_STOXX600",
    "CA_TSX",
    "JP_N225",
    "HK_HSI",
    "CN_CSI300",
    "IN_NIFTY50",
    "TW_TW50",
]

NEW_SEGMENTS = [
    "US_SP1500",
    "KR_KOSPI200",
    "AU_ASX200",
    "NZ_NZX50",
    "MX_IPC",
    "BR_IBRX100",
    "ZA_TOP40",
]

ALL_SEGMENTS = BASE_SEGMENTS + NEW_SEGMENTS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.8,de;q=0.5",
}

TIMEOUT = 35

SOURCES = {
    "US_SP500": {
        "segment": "US_SP1500",
        "url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "min_rows": 490,
        "max_rows": 515,
        "subtag": "US_SP500",
    },
    "US_SP400": {
        "segment": "US_SP1500",
        "url": "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
        "min_rows": 390,
        "max_rows": 415,
        "subtag": "US_SP400",
    },
    "US_SP600": {
        "segment": "US_SP1500",
        "url": "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies",
        "min_rows": 585,
        "max_rows": 620,
        "subtag": "US_SP600",
    },
    "KR_KOSPI200_WIKI": {
        "segment": "KR_KOSPI200",
        "url": "https://en.wikipedia.org/wiki/KOSPI_200",
        "min_rows": 185,
        "max_rows": 215,
    },
    "KR_KOSPI200_TV": {
        "segment": "KR_KOSPI200",
        "url": "https://www.tradingview.com/symbols/KRX-KOSPI200/components/",
        "min_rows": 185,
        "max_rows": 215,
        "tv_prefix": "KRX",
        "tv_index_symbol": "KOSPI200",
    },
    "AU_ASX200_WIKI": {
        "segment": "AU_ASX200",
        "url": "https://en.wikipedia.org/wiki/S%26P/ASX_200",
        "min_rows": 185,
        "max_rows": 220,
    },
    "AU_ASX200_TV": {
        "segment": "AU_ASX200",
        "url": "https://www.tradingview.com/symbols/ASX-XJO/components/",
        "min_rows": 185,
        "max_rows": 220,
        "tv_prefix": "ASX",
        "tv_index_symbol": "XJO",
    },
    "NZ_NZX50_TV": {
        "segment": "NZ_NZX50",
        "url": "https://www.tradingview.com/symbols/NZX-NZ50G/components/",
        "min_rows": 45,
        "max_rows": 60,
        "tv_prefix": "NZX",
        "tv_index_symbol": "NZ50G",
    },
    "NZ_NZX50_WIKI": {
        "segment": "NZ_NZX50",
        "url": "https://en.wikipedia.org/wiki/S%26P/NZX_50",
        "min_rows": 45,
        "max_rows": 60,
    },
    "MX_IPC_TV": {
        "segment": "MX_IPC",
        "url": "https://www.tradingview.com/symbols/BMV-ME/components/",
        "min_rows": 30,
        "max_rows": 45,
        "tv_prefix": "BMV",
        "tv_index_symbol": "ME",
    },
    "MX_IPC_WIKI": {
        "segment": "MX_IPC",
        "url": "https://en.wikipedia.org/wiki/Indice_de_Precios_y_Cotizaciones",
        "min_rows": 30,
        "max_rows": 45,
    },
    "BR_IBRX100_OBM": {
        "segment": "BR_IBRX100",
        "url": "https://obm.com.br/indices/IBXX",
        "min_rows": 90,
        "max_rows": 110,
    },
    "BR_IBRX100_DDM": {
        "segment": "BR_IBRX100",
        "url": "https://www.dadosdemercado.com.br/b3/ibxx",
        "min_rows": 90,
        "max_rows": 110,
    },
    "ZA_TOP40_TV": {
        "segment": "ZA_TOP40",
        "url": "https://www.tradingview.com/symbols/JSE-J200/components/",
        "min_rows": 35,
        "max_rows": 50,
        "tv_prefix": "JSE",
        "tv_index_symbol": "J200",
    },
    "ZA_TOP40_WIKI": {
        "segment": "ZA_TOP40",
        "url": "https://en.wikipedia.org/wiki/FTSE/JSE_Top_40_Index",
        "min_rows": 35,
        "max_rows": 50,
        "allow_name_only": True,
    },
}

SEGMENT_META = {
    "US_SP1500": {
        "country": "",
        "exchange": "US primary exchange pending",
        "mic": "",
        "currency": "USD",
    },
    "KR_KOSPI200": {
        "country": "South Korea",
        "exchange": "Korea Exchange",
        "mic": "XKRX",
        "currency": "KRW",
    },
    "AU_ASX200": {
        "country": "Australia",
        "exchange": "Australian Securities Exchange",
        "mic": "XASX",
        "currency": "AUD",
    },
    "NZ_NZX50": {
        "country": "New Zealand",
        "exchange": "New Zealand Exchange",
        "mic": "XNZE",
        "currency": "NZD",
    },
    "MX_IPC": {
        "country": "Mexico",
        "exchange": "Bolsa Mexicana de Valores",
        "mic": "XMEX",
        "currency": "MXN",
    },
    "BR_IBRX100": {
        "country": "Brazil",
        "exchange": "B3",
        "mic": "BVMF",
        "currency": "BRL",
    },
    "ZA_TOP40": {
        "country": "South Africa",
        "exchange": "Johannesburg Stock Exchange",
        "mic": "XJSE",
        "currency": "ZAR",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_col(x: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(x).strip().lower())


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [
            " ".join(str(v) for v in tup if str(v) != "nan").strip()
            for tup in out.columns
        ]
    else:
        out.columns = [str(c).strip() for c in out.columns]
    return out


def fetch_text(url: str) -> str:
    last_error = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            if len(r.text) < 500:
                raise RuntimeError(f"response too short: {len(r.text)}")
            return r.text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < 2:
                time.sleep(2 + attempt * 2)
    raise RuntimeError(f"fetch failed for {url}: {last_error}")


def read_html_tables(html: str) -> list[pd.DataFrame]:
    try:
        return [flatten_columns(t) for t in pd.read_html(io.StringIO(html))]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"read_html failed: {exc}") from exc


SYMBOL_ALIASES = {
    "symbol", "ticker", "tickersymbol", "code", "codigo", "código",
    "stock", "stockcode", "ticker symbol", "símbolo"
}
NAME_ALIASES = {
    "security", "company", "name", "constituent", "empresa", "nome",
    "unternehmen", "compañía", "componente"
}


def find_col(df: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    alias_norm = {norm_col(a) for a in aliases}
    for c in df.columns:
        if norm_col(c) in alias_norm:
            return str(c)
    for c in df.columns:
        nc = norm_col(c)
        if any(a and a in nc for a in alias_norm):
            return str(c)
    return None


def choose_component_table(
    tables: list[pd.DataFrame],
    min_rows: int,
    max_rows: int,
) -> pd.DataFrame:
    scored = []
    for t in tables:
        if not (min_rows <= len(t) <= max_rows):
            continue
        scol = find_col(t, SYMBOL_ALIASES)
        ncol = find_col(t, NAME_ALIASES)
        score = (10 if scol else 0) + (5 if ncol else 0) + min(len(t), max_rows) / max_rows
        if scol:
            scored.append((score, t))
    if not scored:
        sizes = sorted({len(t) for t in tables})
        raise RuntimeError(
            f"no component table in expected range {min_rows}-{max_rows}; "
            f"table sizes={sizes[:30]}"
        )
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1].copy()



def choose_name_only_component_table(
    tables: list[pd.DataFrame],
    min_rows: int,
    max_rows: int,
) -> pd.DataFrame:
    scored = []
    for t in tables:
        if not (min_rows <= len(t) <= max_rows):
            continue
        ncol = find_col(t, NAME_ALIASES)
        if not ncol:
            continue
        # Prefer the table closest to the nominal middle of the expected range.
        midpoint = (min_rows + max_rows) / 2
        score = 10 - abs(len(t) - midpoint) / max(1, midpoint)
        scored.append((score, t))
    if not scored:
        sizes = sorted({len(t) for t in tables})
        raise RuntimeError(
            f"no name-only component table in expected range {min_rows}-{max_rows}; "
            f"table sizes={sizes[:30]}"
        )
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1].copy()


def name_only_table_to_pairs(df: pd.DataFrame) -> list[tuple[str, str]]:
    ncol = find_col(df, NAME_ALIASES)
    if not ncol:
        raise RuntimeError(f"name column not found in {list(df.columns)}")

    pairs = []
    for _, row in df.iterrows():
        name = clean_name(row.get(ncol, ""))
        if not name:
            continue
        # This is deliberately NOT a ticker. It is only a deterministic internal
        # source-identity key until the one-shot identity/provider audit resolves
        # the real JSE ticker.
        key = "SRCNAME:" + hashlib.sha256(name.casefold().encode("utf-8")).hexdigest()[:16]
        pairs.append((key, name))
    return dedupe_pairs(pairs)

def clean_symbol(v: object) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    if s.lower() in {"nan", "none"}:
        return ""
    s = re.sub(r"\[[^\]]+\]", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def clean_name(v: object) -> str:
    s = clean_symbol(v)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_korean_code(v: object) -> str:
    s = clean_symbol(v).upper().replace(" ", "")
    if re.fullmatch(r"\d+(?:\.0+)?", s):
        s = s.split(".", 1)[0].zfill(6)
    return s


def table_to_pairs(
    df: pd.DataFrame,
    *,
    symbol_transform=None,
) -> list[tuple[str, str]]:
    scol = find_col(df, SYMBOL_ALIASES)
    ncol = find_col(df, NAME_ALIASES)
    if not scol:
        raise RuntimeError(f"symbol column not found in {list(df.columns)}")
    if not ncol:
        ncol = scol

    pairs = []
    for _, row in df.iterrows():
        sym = clean_symbol(row.get(scol, ""))
        if symbol_transform:
            sym = symbol_transform(sym)
        name = clean_name(row.get(ncol, "")) or sym
        if not sym:
            continue
        pairs.append((sym, name))
    return dedupe_pairs(pairs)


def dedupe_pairs(pairs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    out = {}
    for sym, name in pairs:
        key = clean_symbol(sym).upper()
        if not key:
            continue
        if key not in out or (out[key] == key and name != key):
            out[key] = clean_name(name) or key
    return [(k, out[k]) for k in out]


def parse_tradingview(html: str, prefix: str, index_symbol: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    marker = f"/symbols/{prefix.upper()}-"
    pairs = []

    for tr in soup.find_all("tr"):
        href = ""
        for a in tr.find_all("a", href=True):
            h = str(a.get("href", ""))
            if marker in h.upper():
                href = h
                break
        if not href:
            continue

        upper_href = href.upper()
        pos = upper_href.find(marker)
        raw = href[pos + len(marker):].split("?", 1)[0].split("#", 1)[0].strip("/")
        if not raw:
            continue
        sym = clean_symbol(raw)
        if sym.upper() == index_symbol.upper():
            continue

        # Keep the company label if it is visible in the component row.
        row_text = re.sub(r"\s+", " ", tr.get_text(" ", strip=True)).strip()
        name = row_text
        if row_text.upper().startswith(sym.upper()):
            name = row_text[len(sym):].strip()
        # Cut before the first market-cap/price-looking numeric field.
        name = re.split(
            r"\s+\d[\d.,\s]*\s*(?:T|B|M|K)?\s*(?:USD|EUR|AUD|NZD|MXN|ZAR|KRW|BRL)\b",
            name,
            maxsplit=1,
            flags=re.I,
        )[0].strip()
        if not name or len(name) > 180:
            name = sym
        pairs.append((sym, name))

    return dedupe_pairs(pairs)


def extract_pairs(source_id: str) -> tuple[list[tuple[str, str]], dict]:
    cfg = SOURCES[source_id]
    url = cfg["url"]
    html = fetch_text(url)

    if "tv_prefix" in cfg:
        pairs = parse_tradingview(html, cfg["tv_prefix"], cfg["tv_index_symbol"])
    else:
        tables = read_html_tables(html)
        try:
            table = choose_component_table(tables, cfg["min_rows"], cfg["max_rows"])
            transform = normalize_korean_code if cfg["segment"] == "KR_KOSPI200" else None
            pairs = table_to_pairs(table, symbol_transform=transform)
        except RuntimeError:
            if not cfg.get("allow_name_only", False):
                raise
            table = choose_name_only_component_table(
                tables, cfg["min_rows"], cfg["max_rows"]
            )
            pairs = name_only_table_to_pairs(table)

    count = len(pairs)
    ok = cfg["min_rows"] <= count <= cfg["max_rows"]
    audit = {
        "source_id": source_id,
        "segment": cfg["segment"],
        "url": url,
        "fetch_utc": utc_now(),
        "count": count,
        "min_expected": cfg["min_rows"],
        "max_expected": cfg["max_rows"],
        "status": "PASS" if ok else "COUNT_OUTSIDE_RANGE",
        "error": "",
    }
    if not ok:
        raise RuntimeError(
            f"{source_id}: count {count} outside {cfg['min_rows']}-{cfg['max_rows']}"
        )
    return pairs, audit


def load_single_with_fallback(source_ids: list[str], audit_rows: list[dict]) -> tuple[list[tuple[str, str]], str]:
    last_error = None
    for sid in source_ids:
        try:
            pairs, audit = extract_pairs(sid)
            audit_rows.append(audit)
            return pairs, sid
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            cfg = SOURCES[sid]
            audit_rows.append({
                "source_id": sid,
                "segment": cfg["segment"],
                "url": cfg["url"],
                "fetch_utc": utc_now(),
                "count": 0,
                "min_expected": cfg["min_rows"],
                "max_expected": cfg["max_rows"],
                "status": "FAIL",
                "error": str(exc),
            })
    raise RuntimeError(f"all fallbacks failed: {source_ids}: {last_error}")


def make_ws_id(segment: str, ticker: str) -> str:
    t = re.sub(r"\s+", "", ticker.upper())
    meta = SEGMENT_META[segment]
    mic = meta["mic"]
    if segment == "US_SP1500":
        return f"WS:US:{t}"
    return f"WS:{mic}:{t}"


def new_rows_from_pairs(
    segment: str,
    pairs: list[tuple[str, str]],
    source_id: str,
    *,
    subtag: str | None = None,
) -> pd.DataFrame:
    meta = SEGMENT_META[segment]
    source_url = SOURCES[source_id]["url"]
    now = utc_now()

    rows = []
    for ticker, name in pairs:
        tags = segment if not subtag else f"{segment};{subtag}"
        name_only = str(ticker).startswith("SRCNAME:")
        ws_id = (
            f"WS:SRC:{segment}:{str(ticker).split(':', 1)[1]}"
            if name_only
            else make_ws_id(segment, ticker)
        )
        primary_ticker = "" if name_only else ticker
        rows.append({
            "WS_ID": ws_id,
            "Name": name,
            "ISIN": "",
            "Instrument_Type": "UNVERIFIED_EQUITY_SECURITY",
            "Country": meta["country"],
            "Primary_Ticker": primary_ticker,
            "Primary_Exchange": meta["exchange"],
            "Primary_MIC": meta["mic"],
            "Primary_Currency": meta["currency"],
            "Yahoo_Symbol": "",
            "Alpha_Symbol": "",
            "Primary_Universe_Index": segment,
            "Index_Tags": tags,
            "Active": True,
            "Universe_Status": "ACTIVE_SOURCE_CAPTURED",
            "Mapping_Status": "UNMAPPED",
            "Scalable_Tradeability_Status": "NOT_VERIFIED",
            "Source_ID": source_id,
            "Source_AsOf": now[:10],
            "Last_Validated": now,
            "Share_Class": "",
            "Notes": (
                f"Source-superset capture; source={source_url}; "
                + (
                    "name-only source identity; real primary ticker pending one-shot audit"
                    if name_only
                    else "identity/provider mapping pending"
                )
            ),
        })
    return pd.DataFrame(rows)


def merge_duplicate_ws_ids(df: pd.DataFrame) -> pd.DataFrame:
    if not df["WS_ID"].astype(str).duplicated().any():
        return df

    rows = []
    for _, g in df.groupby(df["WS_ID"].astype(str), sort=False):
        base = g.iloc[0].copy()
        for c in df.columns:
            vals = [str(v).strip() for v in g[c].tolist() if str(v).strip() not in {"", "nan", "None"}]
            if c in {"Index_Tags", "Source_ID", "Notes"}:
                uniq = []
                for v in vals:
                    for part in v.split(";") if c != "Notes" else [v]:
                        p = part.strip()
                        if p and p not in uniq:
                            uniq.append(p)
                base[c] = ";".join(uniq)
            elif (str(base.get(c, "")).strip() in {"", "nan", "None"}) and vals:
                base[c] = vals[0]
        rows.append(base)
    return pd.DataFrame(rows, columns=df.columns)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_xlsx(master: pd.DataFrame, audit: pd.DataFrame, manifest: dict, path: Path) -> None:
    # This output is a convenience copy for human review. CSV remains canonical for automation.
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        master.to_excel(xw, sheet_name="Universe_Master", index=False)
        audit.to_excel(xw, sheet_name="Source_Audit", index=False)
        pd.DataFrame(
            [{"Key": k, "Value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v}
             for k, v in manifest.items()]
        ).to_excel(xw, sheet_name="Run_Summary", index=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default="universe/research_partial_1535.csv",
        help="Frozen seven-segment 1535-row base CSV",
    )
    ap.add_argument(
        "--out",
        default="universe/Welt-Swing-Universe-Master-Phase2-v0.3.csv",
    )
    ap.add_argument(
        "--xlsx",
        default="universe/Welt-Swing-Universe-Master-Phase2-v0.3.xlsx",
    )
    ap.add_argument(
        "--manifest",
        default="universe/phase2_completion_manifest_v0.3.json",
    )
    ap.add_argument(
        "--audit",
        default="universe/source_audit_phase2_v0.3.csv",
    )
    ap.add_argument(
        "--snapshots-dir",
        default="universe/source_snapshots_v0.3",
    )
    args = ap.parse_args()

    base_path = Path(args.base)
    if not base_path.exists():
        raise SystemExit(f"Base master missing: {base_path}")

    # keep_default_na=False is intentional: legitimate ticker "NA" must remain "NA".
    base = pd.read_csv(base_path, keep_default_na=False, dtype=str)
    if len(base) != EXPECTED_BASE_ROWS:
        raise SystemExit(
            f"Wrong base snapshot: expected {EXPECTED_BASE_ROWS}, got {len(base)}"
        )
    if base["WS_ID"].astype(str).duplicated().any():
        raise SystemExit("Base contains duplicate WS_ID")

    # Repair one known legacy-import artifact from the already frozen 1535 CSV:
    # pandas read_excel interpreted the legitimate TSX ticker "NA" (National Bank
    # of Canada) as a missing value before that CSV was created. The canonical
    # WS_ID still preserves the ticker unambiguously as WS:XTSE:NA.
    na_ws = base["WS_ID"].astype(str).eq("WS:XTSE:NA")
    if int(na_ws.sum()) != 1:
        raise SystemExit(
            f"Expected exactly one WS:XTSE:NA row in frozen base, found {int(na_ws.sum())}"
        )
    na_ticker = base.loc[na_ws, "Primary_Ticker"].astype(str).iloc[0].strip()
    if na_ticker == "":
        base.loc[na_ws, "Primary_Ticker"] = "NA"
        if "Notes" in base.columns:
            current_note = str(base.loc[na_ws, "Notes"].iloc[0]).strip()
            repair_note = "LEGACY_IMPORT_REPAIR: Primary_Ticker restored from WS_ID WS:XTSE:NA"
            base.loc[na_ws, "Notes"] = (
                f"{current_note}; {repair_note}" if current_note else repair_note
            )
    elif na_ticker != "NA":
        raise SystemExit(
            f"Unexpected Primary_Ticker for WS:XTSE:NA: {na_ticker!r}"
        )

    if str(base.loc[na_ws, "Primary_Ticker"].iloc[0]).strip() != "NA":
        raise SystemExit("Ticker NA repair failed")

    base_segments = set(base["Primary_Universe_Index"].astype(str))
    missing_base = [s for s in BASE_SEGMENTS if s not in base_segments]
    if missing_base:
        raise SystemExit(f"Base missing frozen segments: {missing_base}")

    audit_rows: list[dict] = []
    additions: list[pd.DataFrame] = []
    snapshots_dir = Path(args.snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # US Composite 1500 = S&P 500 + MidCap 400 + SmallCap 600 source memberships.
    for sid in ["US_SP500", "US_SP400", "US_SP600"]:
        pairs, audit = extract_pairs(sid)
        audit_rows.append(audit)
        df = new_rows_from_pairs(
            "US_SP1500",
            pairs,
            sid,
            subtag=SOURCES[sid]["subtag"],
        )
        df.to_csv(snapshots_dir / f"{sid}.csv", index=False)
        additions.append(df)

    fallback_plan = {
        "KR_KOSPI200": ["KR_KOSPI200_WIKI", "KR_KOSPI200_TV"],
        "AU_ASX200": ["AU_ASX200_WIKI", "AU_ASX200_TV"],
        "NZ_NZX50": ["NZ_NZX50_TV", "NZ_NZX50_WIKI"],
        "MX_IPC": ["MX_IPC_TV", "MX_IPC_WIKI"],
        "BR_IBRX100": ["BR_IBRX100_OBM", "BR_IBRX100_DDM"],
        "ZA_TOP40": ["ZA_TOP40_TV", "ZA_TOP40_WIKI"],
    }

    for segment, source_ids in fallback_plan.items():
        pairs, used_sid = load_single_with_fallback(source_ids, audit_rows)
        df = new_rows_from_pairs(segment, pairs, used_sid)
        df.to_csv(snapshots_dir / f"{segment}.csv", index=False)
        additions.append(df)

    new_all = pd.concat(additions, ignore_index=True)

    # Align to the current master schema while retaining any future columns in the base.
    for c in base.columns:
        if c not in new_all.columns:
            new_all[c] = ""
    for c in new_all.columns:
        if c not in base.columns:
            base[c] = ""
    new_all = new_all[base.columns]

    combined = pd.concat([base, new_all], ignore_index=True)
    raw_memberships = len(combined)
    combined = merge_duplicate_ws_ids(combined)
    combined = combined.sort_values(
        ["Primary_Universe_Index", "Primary_MIC", "Primary_Ticker", "WS_ID"],
        kind="mergesort",
        na_position="last",
    ).reset_index(drop=True)

    segment_counts = (
        combined["Primary_Universe_Index"]
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    missing_segments = [s for s in ALL_SEGMENTS if int(segment_counts.get(s, 0)) == 0]

    audit_df = pd.DataFrame(audit_rows)
    failed_sources = audit_df.loc[audit_df["status"] != "PASS", "source_id"].astype(str).tolist()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)

    status = "COMPLETE_SOURCE_SUPERSET" if not missing_segments else "PARTIAL_SOURCE_SUPERSET"
    manifest = {
        "schema": SCHEMA,
        "generated_utc": utc_now(),
        "status": status,
        "governance": "SOURCE_FLEXIBILITY_APPROVED_2026-08-23",
        "base_rows": int(len(base)),
        "raw_memberships_after_additions": int(raw_memberships),
        "deduplicated_rows": int(len(combined)),
        "segments_expected": ALL_SEGMENTS,
        "segments_present": [s for s in ALL_SEGMENTS if int(segment_counts.get(s, 0)) > 0],
        "missing_segments": missing_segments,
        "segment_counts": {str(k): int(v) for k, v in segment_counts.items()},
        "failed_or_unused_source_attempts": failed_sources,
        "canonical_csv": str(out_path),
        "canonical_csv_sha256": sha256_path(out_path),
        "identity_audit_complete": False,
        "provider_mapping_complete": False,
        "price_run_allowed_after_this_step": False,
        "productive_trading_authority": False,
        "p0_run": False,
        "alpha_vantage_allowed": False,
        "notes": [
            "Coverage/source-superset completion is separated from identity and provider mapping.",
            "Public/free sources and practical fallbacks are permitted; exact source hierarchy is secondary.",
            "US exact primary MIC/exchange is intentionally deferred to the one-shot identity/mapping audit.",
            "New source rows are ACTIVE_SOURCE_CAPTURED, not yet fully provider-mapped.",
            "Ticker NA is preserved by reading CSV with keep_default_na=False.",
            "No price, news, setup, ranking, P0, sizing or trade decision is performed.",
        ],
    }

    manifest_path = Path(args.manifest)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_path = Path(args.audit)
    audit_df.to_csv(audit_path, index=False)

    xlsx_path = Path(args.xlsx)
    write_xlsx(combined, audit_df, manifest, xlsx_path)

    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
