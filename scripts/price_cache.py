#!/usr/bin/env python3
"""
Welt-Swing Long DEV v0.1 + Free-Data Architecture Amendment A1
Batchfähiger yfinance Price-Cache-Pfad für SWING-U3K (bis ca. 3000 Securities).
GitHub/Android Free-Data Runtime Edition.

DEV / RESEARCH / SHADOW ONLY.

Leitplanken:
- Kein kommerzieller Datenprovider als Voraussetzung.
- Alpha Vantage ist vollständig verboten und besitzt keinen Fallback-Pfad.
- Operativer OHLCV-Pfad: yfinance / Yahoo Finance öffentlich zugängliche API.
- Bulk/Batch via yf.download(), nicht 3000 serielle Ticker.history()-Aufrufe.
- Persistenter dependency-armer SQLite-Cache + State/Manifest.
- Lokale QA; problematische Serien werden nicht als READY weitergereicht.
- Bulk-Pass standardmäßig repair=False; nur QA-auffällige Symbole dürfen in einem
  gezielten zweiten Pass repair=True erhalten.
- Der lokale Split-Normalizer wird auf yfinance-Daten NICHT automatisch angewandt,
  um Doppeladjustierung zu vermeiden. Splits dienen als QA-/Repair-Signal.

Die Implementierung ist kompatibel zum dokumentierten yfinance.download()-Vertrag
(Stand yfinance 1.6.0, 2026-08-13): Multi-Ticker-Download, threads, group_by,
auto_adjust, actions, repair, timeout und MultiIndex-Ausgabe.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
import json
import math
import sqlite3
import time

import pandas as pd
import numpy as np

SOURCE_ID = "YFINANCE_FREE"
ALPHA_VANTAGE_ALLOWED = False
PRODUCTIVE = False

# Optional project-level Yahoo symbol overrides. This is a provider-symbol layer only;
# it never changes canonical WS_ID / ISIN / MIC identity.
DEFAULT_YAHOO_OVERRIDE_FILE = Path("config/yahoo_symbol_overrides.csv")
YAHOO_SYMBOL_SENTINELS = {"", "UNMAPPED", "PENDING", "NA", "N/A", "NONE", "NULL"}


class FreeDataContractError(RuntimeError):
    pass


class YFinanceUnavailable(FreeDataContractError):
    pass


class BatchDownloadError(FreeDataContractError):
    pass


@dataclass(frozen=True)
class FreeDataConfig:
    batch_size: int = 100
    threads: bool | int = True
    timeout_seconds: float = 15.0
    initial_period: str = "2y"
    interval: str = "1d"
    overlap_calendar_days: int = 14
    min_valid_bars: int = 252
    ready_unique_bars: int = 260
    # Promoted QA v0.4 policy: raw malformed bars stay in cache, but up to two
    # isolated invalid bars may be excluded from technical calculations when
    # they are <=1% of the series and at least 260 valid bars remain.
    max_filterable_invalid_bars: int = 2
    max_filterable_invalid_share: float = 0.01
    stale_calendar_days: int = 10
    max_identical_retries: int = 1
    retry_sleep_seconds: float = 2.0
    pause_between_batches_seconds: float = 0.0
    repair_anomalies: bool = True
    repair_batch_size: int = 25
    suspicious_abs_return: float = 0.50
    zero_volume_warning_share: float = 0.20

    def validate(self) -> None:
        if not (1 <= self.batch_size <= 1000):
            raise ValueError("batch_size out of range")
        if self.min_valid_bars <= 0 or self.ready_unique_bars < self.min_valid_bars:
            raise ValueError("invalid bar thresholds")
        if not (0 <= self.max_filterable_invalid_bars <= 10):
            raise ValueError("max_filterable_invalid_bars out of range")
        if not (0.0 <= self.max_filterable_invalid_share <= 0.05):
            raise ValueError("max_filterable_invalid_share out of range")
        if self.max_identical_retries not in (0, 1):
            raise ValueError("A1 contract permits at most one identical retry")


# Yahoo Finance exchange suffix rules for the project's target market architecture.
# These are deterministic symbol-construction rules only. A derived symbol is not an
# identity source; WS_ID/ISIN/MIC remain canonical. Punctuation/share-class exceptions
# must be stored as explicit Yahoo_Symbol overrides instead of guessed.
MIC_SUFFIX_RULES: dict[str, str] = {
    # USA
    "XNYS": "", "XNAS": "", "XASE": "",
    # Canada / Mexico
    "XTSE": ".TO", "XTSX": ".V", "XMEX": ".MX",
    # Japan / HK / China / India / Korea / Taiwan
    "XTKS": ".T", "XHKG": ".HK", "XSHG": ".SS", "XSHE": ".SZ",
    "XNSE": ".NS", "XBOM": ".BO", "XKRX": ".KS", "XKOS": ".KS",
    "XKOSDAQ": ".KQ", "XTAI": ".TW",
    # Australia / New Zealand
    "XASX": ".AX", "XNZE": ".NZ",
    # Brazil / South Africa
    "BVMF": ".SA", "XJSE": ".JO",
    # Major European venues
    "XPAR": ".PA", "XETR": ".DE", "XLON": ".L", "XSWX": ".SW",
    "XAMS": ".AS", "XMIL": ".MI", "XMAD": ".MC", "XBRU": ".BR",
    "XSTO": ".ST", "XCSE": ".CO", "XHEL": ".HE", "XOSL": ".OL",
    "XLIS": ".LS", "XWBO": ".VI", "XDUB": ".IR", "XWAR": ".WA",
}

# Source-universe tickers may already carry venue/RIC-style suffixes.  These are
# syntax hints only, never identity evidence.  We strip only suffixes that are
# deterministic for the stated MIC, then re-apply Yahoo's venue suffix.
MIC_INPUT_SUFFIXES: dict[str, tuple[str, ...]] = {
    "XPAR": (".PA",), "XETR": (".DE",), "XLON": (".L",),
    "XSWX": (".S", ".SW"), "XAMS": (".AS",), "XMIL": (".MI",),
    "XMAD": (".MC",), "XBRU": (".BR",), "XSTO": (".ST",),
    "XCSE": (".CO",), "XHEL": (".HE",), "XOSL": (".OL",),
    "XLIS": (".LS",), "XWBO": (".VI",), "XDUB": (".I", ".IR"),
    "XWAR": (".WA",),
}


def _clean_text(v: Any) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v).strip()


def derive_yahoo_symbol(primary_ticker: str, primary_mic: str) -> tuple[str | None, str]:
    """Return (candidate symbol, mapping_status).

    The universe may store a primary ticker in venue/RIC-style form (for example
    LGEN.L, VZN.S or HEIN.AS).  For known MIC/suffix pairs we normalize that syntax
    before applying Yahoo's venue suffix.  This remains a *candidate* mapping only:
    actual price availability/QA is what validates the candidate.  Ambiguous
    punctuation is still left for explicit overrides.
    """
    ticker = _clean_text(primary_ticker)
    mic = _clean_text(primary_mic).upper()
    if not ticker:
        return None, "MISSING_PRIMARY_TICKER"
    if mic not in MIC_SUFFIX_RULES:
        return None, "UNSUPPORTED_MIC"
    if any(ch in ticker for ch in ["/", " "]):
        return None, "EXPLICIT_OVERRIDE_REQUIRED"

    suffix = MIC_SUFFIX_RULES[mic]
    base = ticker
    normalized = False

    # Strip only a MIC-compatible source suffix.  Longest first avoids .S matching
    # the tail of .SW on Swiss symbols.
    for src_suffix in sorted(MIC_INPUT_SUFFIXES.get(mic, ()), key=len, reverse=True):
        if base.upper().endswith(src_suffix.upper()):
            base = base[:-len(src_suffix)]
            normalized = True
            break

    base = base.upper()
    if not base:
        return None, "EXPLICIT_OVERRIDE_REQUIRED"

    if mic == "XHKG":
        # Yahoo convention for numeric HK codes: 0700.HK, 9988.HK.
        if not base.isdigit():
            return None, "EXPLICIT_OVERRIDE_REQUIRED"
        base = str(int(base)).zfill(4)
    elif mic in {"XSHG", "XSHE"}:
        if not base.isdigit():
            return None, "EXPLICIT_OVERRIDE_REQUIRED"
        base = base.zfill(6)
    elif mic in {"XNYS", "XNAS", "XASE", "XTSE", "XTSX"} and "." in base:
        # Yahoo uses hyphens for common US/Canadian share classes, e.g. BRK-B,
        # TECK-B.TO.  This is deterministic syntax normalization, not identity repair.
        base = base.replace(".", "-")
        normalized = True
    elif "." in base:
        # Any punctuation left after stripping the known venue suffix is ambiguous.
        return None, "EXPLICIT_OVERRIDE_REQUIRED"

    status = "DERIVED_RULE_NORMALIZED" if normalized else "DERIVED_RULE"
    return f"{base}{suffix}", status


def load_yahoo_symbol_overrides(path: str | Path | None = None) -> dict[str, str]:
    """Load a small audited provider-symbol override layer.

    The override file is optional. It must contain WS_ID and Yahoo_Symbol.
    Canonical identity remains in the universe master; this file only fixes provider syntax.
    """
    p = Path(path) if path is not None else DEFAULT_YAHOO_OVERRIDE_FILE
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    required = {"WS_ID", "Yahoo_Symbol"}
    missing = required - set(df.columns)
    if missing:
        raise FreeDataContractError(f"Yahoo override file missing required columns: {sorted(missing)}")
    if df["WS_ID"].astype(str).duplicated().any():
        dupes = df.loc[df["WS_ID"].astype(str).duplicated(keep=False), "WS_ID"].astype(str).tolist()
        raise FreeDataContractError(f"Duplicate WS_ID in Yahoo override file: {sorted(set(dupes))}")
    out: dict[str, str] = {}
    for _, r in df.iterrows():
        ws = _clean_text(r.get("WS_ID"))
        sym = _clean_text(r.get("Yahoo_Symbol"))
        if not ws or not sym or sym.upper() in YAHOO_SYMBOL_SENTINELS:
            raise FreeDataContractError(f"Invalid Yahoo override row for WS_ID={ws!r}")
        out[ws] = sym
    return out


def build_yahoo_symbol_map(universe: pd.DataFrame, *, override_path: str | Path | None = None) -> pd.DataFrame:
    required = {"WS_ID", "Primary_Ticker", "Primary_MIC"}
    missing = required - set(universe.columns)
    if missing:
        raise FreeDataContractError(f"Universe missing required columns: {sorted(missing)}")
    overrides = load_yahoo_symbol_overrides(override_path)
    rows: list[dict[str, Any]] = []
    for _, r in universe.iterrows():
        ws_id = str(r["WS_ID"])
        override = _clean_text(overrides.get(ws_id))
        explicit = _clean_text(r.get("Yahoo_Symbol"))
        if explicit.upper() in YAHOO_SYMBOL_SENTINELS:
            explicit = ""
        if override:
            symbol, status = override, "PROJECT_OVERRIDE"
        elif explicit:
            symbol, status = explicit, "EXPLICIT"
        else:
            symbol, status = derive_yahoo_symbol(r.get("Primary_Ticker"), r.get("Primary_MIC"))
        rows.append({
            "WS_ID": ws_id,
            "Yahoo_Symbol": symbol,
            "Yahoo_Mapping_Status": status,
            "Primary_Ticker": _clean_text(r.get("Primary_Ticker")),
            "Primary_MIC": _clean_text(r.get("Primary_MIC")).upper(),
            "Primary_Currency": _clean_text(r.get("Primary_Currency")).upper(),
        })
    return pd.DataFrame(rows)


def _canonical_hash(obj: Any) -> str:
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(blob).hexdigest()


class SQLitePriceCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._create_schema()

    def close(self) -> None:
        self.conn.commit(); self.conn.close()

    def _create_schema(self) -> None:
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS price_daily (
            ws_id TEXT NOT NULL,
            yahoo_symbol TEXT NOT NULL,
            day TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, adj_close REAL,
            volume REAL, dividends REAL, stock_splits REAL,
            repaired INTEGER NOT NULL DEFAULT 0,
            source_id TEXT NOT NULL,
            fetched_utc TEXT NOT NULL,
            PRIMARY KEY (ws_id, day)
        );
        CREATE INDEX IF NOT EXISTS ix_price_symbol_day ON price_daily(yahoo_symbol, day);
        CREATE TABLE IF NOT EXISTS cache_state (
            ws_id TEXT PRIMARY KEY,
            yahoo_symbol TEXT,
            mapping_status TEXT,
            status TEXT NOT NULL,
            reason_code TEXT,
            unique_bars INTEGER NOT NULL DEFAULT 0,
            valid_bars INTEGER NOT NULL DEFAULT 0,
            repaired_rows INTEGER NOT NULL DEFAULT 0,
            suspicious_returns INTEGER NOT NULL DEFAULT 0,
            zero_volume_share REAL,
            first_bar_date TEXT,
            last_bar_date TEXT,
            last_fetch_utc TEXT,
            batch_id TEXT,
            last_error TEXT
        );
        CREATE TABLE IF NOT EXISTS batch_log (
            batch_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            started_utc TEXT NOT NULL,
            finished_utc TEXT NOT NULL,
            symbol_count INTEGER NOT NULL,
            received_count INTEGER NOT NULL,
            missing_count INTEGER NOT NULL,
            retry_count INTEGER NOT NULL,
            repair_pass INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            error_text TEXT
        );
        """)
        self.conn.commit()

    def upsert_price_rows(self, rows: Sequence[tuple[Any, ...]]) -> None:
        if not rows:
            return
        self.conn.executemany("""
        INSERT INTO price_daily
        (ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired,source_id,fetched_utc)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(ws_id,day) DO UPDATE SET
          yahoo_symbol=excluded.yahoo_symbol, open=excluded.open, high=excluded.high,
          low=excluded.low, close=excluded.close, adj_close=excluded.adj_close,
          volume=excluded.volume, dividends=excluded.dividends,
          stock_splits=excluded.stock_splits, repaired=excluded.repaired,
          source_id=excluded.source_id, fetched_utc=excluded.fetched_utc
        """, rows)

    def upsert_state(self, state: Mapping[str, Any]) -> None:
        self.upsert_states([state])

    def upsert_states(self, states: Sequence[Mapping[str, Any]]) -> None:
        if not states:
            return
        cols = [
            "ws_id","yahoo_symbol","mapping_status","status","reason_code","unique_bars","valid_bars",
            "repaired_rows","suspicious_returns","zero_volume_share","first_bar_date","last_bar_date",
            "last_fetch_utc","batch_id","last_error"
        ]
        sql=f"""
        INSERT INTO cache_state ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})
        ON CONFLICT(ws_id) DO UPDATE SET
        {','.join(f'{c}=excluded.{c}' for c in cols[1:])}
        """
        self.conn.executemany(sql, [[state.get(c) for c in cols] for state in states])

    def log_batch(self, row: Mapping[str, Any]) -> None:
        cols = ["batch_id","source_id","started_utc","finished_utc","symbol_count","received_count","missing_count","retry_count","repair_pass","status","error_text"]
        self.conn.execute(f"INSERT OR REPLACE INTO batch_log ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", [row.get(c) for c in cols])

    def last_bar_dates(self, ws_ids: Sequence[str]) -> dict[str, date]:
        if not ws_ids: return {}
        q = ",".join("?" for _ in ws_ids)
        cur = self.conn.execute(f"SELECT ws_id,last_bar_date FROM cache_state WHERE ws_id IN ({q}) AND last_bar_date IS NOT NULL", list(ws_ids))
        out={}
        for ws,d in cur.fetchall():
            try: out[ws]=date.fromisoformat(d)
            except Exception: pass
        return out

    def reset_changed_symbols(self, mapping: pd.DataFrame) -> list[dict[str, str]]:
        """Purge cached history when a WS_ID is remapped to a different Yahoo symbol.

        Mixing bars from two provider symbols under one canonical WS_ID is forbidden.
        The security is reloaded as INITIAL on the same run after this reset.
        """
        if mapping.empty:
            return []
        current = {
            str(ws): (None if sym is None else str(sym))
            for ws, sym in self.conn.execute("SELECT ws_id,yahoo_symbol FROM cache_state").fetchall()
        }
        changed: list[dict[str, str]] = []
        for _, r in mapping.iterrows():
            ws = str(r["WS_ID"])
            new_sym = _clean_text(r.get("Yahoo_Symbol"))
            old_sym = _clean_text(current.get(ws))
            if old_sym and new_sym and old_sym != new_sym:
                self.conn.execute("DELETE FROM price_daily WHERE ws_id=?", (ws,))
                self.conn.execute("DELETE FROM cache_state WHERE ws_id=?", (ws,))
                changed.append({"WS_ID": ws, "old_symbol": old_sym, "new_symbol": new_sym})
        if changed:
            self.conn.commit()
        return changed

    def load_price_frame(self, ws_id: str) -> pd.DataFrame:
        """Return the complete cached history for one canonical security.

        Incremental downloads contain only the overlap window. QA must evaluate
        the complete persisted series, never just the freshly downloaded slice.
        """
        q = """
        SELECT day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired
        FROM price_daily WHERE ws_id=? ORDER BY day
        """
        x = pd.read_sql_query(q, self.conn, params=[ws_id])
        if x.empty:
            return pd.DataFrame()
        x["day"] = pd.to_datetime(x["day"], errors="coerce")
        x = x.dropna(subset=["day"]).set_index("day")
        return x

    def counts(self) -> dict[str, int]:
        return {
            "price_rows": int(self.conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]),
            "states": int(self.conn.execute("SELECT COUNT(*) FROM cache_state").fetchone()[0]),
            "ready": int(self.conn.execute("SELECT COUNT(*) FROM cache_state WHERE status='READY'").fetchone()[0]),
            "batches": int(self.conn.execute("SELECT COUNT(*) FROM batch_log").fetchone()[0]),
        }


class YFinanceBatchClient:
    """Thin adapter around yf.download(), injectable for deterministic offline tests."""
    def __init__(self, *, config: FreeDataConfig | None = None, download_func: Callable[..., pd.DataFrame] | None = None):
        self.config = config or FreeDataConfig(); self.config.validate()
        self._download_func = download_func
        self._yf = None

    def _resolve_download(self) -> Callable[..., pd.DataFrame]:
        if self._download_func is not None:
            return self._download_func
        try:
            import yfinance as yf  # type: ignore
        except Exception as e:
            raise YFinanceUnavailable(
                "yfinance ist in dieser Laufzeit nicht installiert. Für reale Läufe: yfinance==1.6.0 installieren."
            ) from e
        self._yf = yf
        try:
            # local metadata/tz cache, no credentials required
            yf.set_tz_cache_location(str(Path.home() / ".cache" / "welt_swing_long_yfinance"))
        except Exception:
            pass
        return yf.download

    def download(self, symbols: Sequence[str], *, period: str | None = None,
                 start: str | date | None = None, end: str | date | None = None,
                 repair: bool = False) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame()
        func = self._resolve_download()
        kwargs = dict(
            tickers=list(symbols), interval=self.config.interval,
            group_by="ticker", auto_adjust=False, back_adjust=False,
            repair=repair, actions=True, threads=self.config.threads,
            ignore_tz=True, keepna=False, progress=False,
            rounding=False, timeout=self.config.timeout_seconds,
            multi_level_index=True,
        )
        if period is not None:
            kwargs["period"] = period
        else:
            if start is not None: kwargs["start"] = str(start)
            if end is not None: kwargs["end"] = str(end)
        return func(**kwargs)


def _field_name(x: Any) -> str:
    s = str(x).strip()
    return {
        "Adj Close": "adj_close", "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume", "Dividends": "dividends",
        "Stock Splits": "stock_splits", "Repaired?": "repaired",
    }.get(s, s.lower().replace(" ", "_"))


def split_download_frame(raw: pd.DataFrame, symbols: Sequence[str]) -> dict[str, pd.DataFrame]:
    """Split yfinance multi-ticker output into normalized per-symbol frames.

    Handles group_by='ticker' MultiIndex, group_by='column' MultiIndex and the
    single-level one-ticker shape for compatibility.
    """
    out: dict[str, pd.DataFrame] = {}
    if raw is None or len(raw) == 0:
        return out
    syms = [str(s) for s in symbols]

    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = set(map(str, raw.columns.get_level_values(0)))
        lvl1 = set(map(str, raw.columns.get_level_values(1))) if raw.columns.nlevels >= 2 else set()
        for sym in syms:
            try:
                if sym in lvl0:
                    df = raw[sym].copy()
                elif sym in lvl1:
                    df = raw.xs(sym, axis=1, level=1).copy()
                else:
                    continue
                if not df.empty:
                    df.columns = [_field_name(c) for c in df.columns]
                    out[sym] = df
            except Exception:
                continue
    else:
        if len(syms) == 1:
            df = raw.copy(); df.columns = [_field_name(c) for c in df.columns]
            out[syms[0]] = df
    return out


def normalize_symbol_frame(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    # Canonicalize index to naive date (daily bars only).
    idx = pd.to_datetime(x.index, errors="coerce")
    try: idx = idx.tz_localize(None)
    except Exception: pass
    x.index = idx
    x = x[~x.index.isna()]
    x = x[~x.index.duplicated(keep="last")].sort_index()
    for c in ["open","high","low","close","adj_close","volume","dividends","stock_splits","repaired"]:
        if c not in x.columns:
            x[c] = np.nan if c not in {"dividends","stock_splits","repaired"} else 0.0
        x[c] = pd.to_numeric(x[c], errors="coerce")

    # yfinance multi-ticker downloads align all symbols in a batch to the union
    # of trading dates. For cross-market batches this creates placeholder rows
    # with OHLC all NaN on another market's trading day. These are not bars and
    # must not be counted as invalid OHLC. Keep rows with at least one OHLC value
    # so genuinely incomplete bars still fail QA below.
    ohlc = ["open", "high", "low", "close"]
    x = x.loc[~x[ohlc].isna().all(axis=1)].copy()

    x["repaired"] = x["repaired"].fillna(0).astype(float)
    return x[["open","high","low","close","adj_close","volume","dividends","stock_splits","repaired"]]


def technical_valid_mask(df: pd.DataFrame) -> pd.Series:
    """Hard-valid daily bars for technical calculations.

    Open must be finite/positive, but may lie marginally outside H/L on some Yahoo
    auction-market feeds. High/Low/Close must be internally consistent. Negative
    volume is invalid; missing volume is tolerated because price-only technical
    features can still be computed.
    """
    x = normalize_symbol_frame(df)
    finite_ohlc = x[["open","high","low","close"]].replace([np.inf,-np.inf], np.nan).notna().all(axis=1)
    positive = (x[["open","high","low","close"]] > 0).all(axis=1)
    relation = (x["high"] >= x["low"]) & (x["close"] <= x["high"]) & (x["close"] >= x["low"])
    nonnegative_volume = ~((x["volume"] < 0) & x["volume"].notna())
    return finite_ohlc & positive & relation & nonnegative_volume


def qa_symbol_frame(df: pd.DataFrame, *, config: FreeDataConfig, as_of: date | None = None) -> dict[str, Any]:
    x = normalize_symbol_frame(df)
    unique_bars = int(len(x))
    valid = technical_valid_mask(x) if unique_bars else pd.Series(dtype=bool)
    valid_bars = int(valid.sum()) if unique_bars else 0
    invalid_rows = int((~valid).sum()) if unique_bars else 0

    # Promoted QA v0.4 policy.
    #
    # Raw malformed bars are NEVER deleted here. Downstream technical features
    # already exclude bars failing technical_valid_mask(). A security may remain
    # eligible after filtering only when:
    #   - 1..max_filterable_invalid_bars invalid bars are present,
    #   - those rows are <= max_filterable_invalid_share of the raw series,
    #   - at least ready_unique_bars valid observations remain.
    #
    # Suspicious returns and staleness are checked below and still override
    # filtered-bar eligibility. This prevents the three overlapping ZA scale
    # anomaly cases from being promoted simply because they have only two bad bars.
    invalid_share = (
        float(invalid_rows / unique_bars) if unique_bars else 0.0
    )
    filterable_invalid_bars = (
        0 < invalid_rows <= config.max_filterable_invalid_bars
        and invalid_share <= config.max_filterable_invalid_share
        and valid_bars >= config.ready_unique_bars
    )

    xv = x.loc[valid].copy() if unique_bars else x.copy()

    vol = xv["volume"] if not xv.empty else pd.Series(dtype=float)
    zero_volume_share = float(((vol == 0) & vol.notna()).sum() / max(1, vol.notna().sum())) if len(vol) else 0.0
    repaired_rows = int((xv["repaired"].fillna(0) != 0).sum()) if not xv.empty else 0

    ret = xv["close"].pct_change(fill_method=None).abs() if not xv.empty else pd.Series(dtype=float)
    split = xv["stock_splits"].fillna(0).abs() > 0 if not xv.empty else pd.Series(dtype=bool)
    split_near = split | split.shift(1, fill_value=False) | split.shift(-1, fill_value=False) if not xv.empty else split
    suspicious_returns = int(((ret > config.suspicious_abs_return) & ~split_near).sum()) if not xv.empty else 0

    first_bar = xv.index.min().date().isoformat() if valid_bars else None
    last_bar = xv.index.max().date().isoformat() if valid_bars else None
    stale = False
    if valid_bars and as_of is not None:
        stale = (as_of - xv.index.max().date()).days > config.stale_calendar_days

    reason = None
    if unique_bars == 0:
        status, reason = "DOWNLOAD_FAILED", "NO_DATA"
    elif invalid_rows > 0 and not filterable_invalid_bars:
        status, reason = "QUARANTINE", "INVALID_OHLC_OR_VOLUME"
    elif suspicious_returns > 0:
        status, reason = "QUARANTINE", "SUSPICIOUS_RETURN_NEEDS_REPAIR"
    elif stale:
        status, reason = "STALE", "LAST_BAR_TOO_OLD"
    elif unique_bars >= config.ready_unique_bars and valid_bars >= config.min_valid_bars:
        status = "READY"
        if invalid_rows == 1:
            reason = "ISOLATED_INVALID_BAR_EXCLUDED"
        elif invalid_rows > 1:
            reason = "FILTERED_INVALID_BARS_EXCLUDED"
    else:
        status, reason = "WARMUP", "INSUFFICIENT_HISTORY"

    return {
        "status": status, "reason_code": reason,
        "unique_bars": unique_bars, "valid_bars": valid_bars,
        "repaired_rows": repaired_rows, "suspicious_returns": suspicious_returns,
        "zero_volume_share": zero_volume_share,
        "first_bar_date": first_bar, "last_bar_date": last_bar,
        "warning_zero_volume": zero_volume_share > config.zero_volume_warning_share,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _chunks(seq: Sequence[Any], n: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), n):
        yield list(seq[i:i+n])


class YFinancePriceCacheRunner:
    def __init__(self, cache: SQLitePriceCache, client: YFinanceBatchClient, *, config: FreeDataConfig | None = None):
        self.cache=cache; self.client=client; self.config=config or client.config; self.config.validate()
        self.source_circuit_open=False

    def _download_with_retry(self, symbols: Sequence[str], *, repair: bool, period: str | None = None,
                             start: date | None = None, end: date | None = None) -> tuple[pd.DataFrame | None, int, str | None]:
        attempts = 1 + self.config.max_identical_retries
        last_error=None
        for attempt in range(attempts):
            try:
                raw=self.client.download(symbols, period=period, start=start, end=end, repair=repair)
                return raw, attempt, None
            except Exception as e:
                last_error=f"{type(e).__name__}: {e}"
                if attempt + 1 < attempts:
                    time.sleep(self.config.retry_sleep_seconds)
        return None, attempts-1, last_error

    def _rows_for_db(self, ws_id: str, symbol: str, x: pd.DataFrame, fetched_utc: str) -> list[tuple[Any,...]]:
        out=[]
        x=normalize_symbol_frame(x)
        for ts,r in x.iterrows():
            def val(c):
                v=r[c]
                if pd.isna(v): return None
                return float(v)
            out.append((
                ws_id,symbol,ts.date().isoformat(),val("open"),val("high"),val("low"),val("close"),val("adj_close"),
                val("volume"),val("dividends"),val("stock_splits"),int(bool(val("repaired") or 0)),SOURCE_ID,fetched_utc
            ))
        return out

    def _process_batch(self, batch: pd.DataFrame, *, period: str | None, start: date | None, end: date | None,
                       repair_pass: bool=False, as_of: date | None=None) -> tuple[list[str], list[str]]:
        symbols=batch["Yahoo_Symbol"].tolist()
        batch_id=f"YF-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}-{_canonical_hash(symbols)[:8]}{'-R' if repair_pass else ''}"
        started=_utc_now()
        raw,retries,error=self._download_with_retry(symbols, repair=repair_pass, period=period, start=start, end=end)
        received=[]; missing=[]; repair_candidates=[]
        fetched=_utc_now()
        if raw is None:
            for _,r in batch.iterrows():
                self.cache.upsert_state({
                    "ws_id":r.WS_ID,"yahoo_symbol":r.Yahoo_Symbol,"mapping_status":r.Yahoo_Mapping_Status,
                    "status":"DOWNLOAD_FAILED","reason_code":"BATCH_ERROR","unique_bars":0,"valid_bars":0,
                    "repaired_rows":0,"suspicious_returns":0,"zero_volume_share":None,"first_bar_date":None,"last_bar_date":None,
                    "last_fetch_utc":fetched,"batch_id":batch_id,"last_error":error,
                })
                missing.append(r.Yahoo_Symbol)
            self.cache.log_batch({"batch_id":batch_id,"source_id":SOURCE_ID,"started_utc":started,"finished_utc":fetched,
                                  "symbol_count":len(symbols),"received_count":0,"missing_count":len(symbols),"retry_count":retries,
                                  "repair_pass":int(repair_pass),"status":"FAILED","error_text":error})
            self.cache.conn.commit(); return repair_candidates, missing

        frames=split_download_frame(raw,symbols)
        price_rows_buffer=[]
        received_rows=[]
        missing_rows=[]
        for _,r in batch.iterrows():
            sym=r.Yahoo_Symbol; ws=r.WS_ID
            if sym not in frames or frames[sym].empty:
                missing_rows.append(r)
                missing.append(sym)
                continue
            x=normalize_symbol_frame(frames[sym])
            # Some yfinance batch responses contain a symbol frame whose rows are
            # only union-calendar placeholders. After normalization that is NO DATA
            # and must enter the bounded rescue pass instead of counting as received.
            if x.empty:
                missing_rows.append(r)
                missing.append(sym)
                continue
            price_rows_buffer.extend(self._rows_for_db(ws,sym,x,fetched))
            received_rows.append(r)
            received.append(sym)

        # Persist the overlap/new bars first. Cache-state QA below MUST use the
        # full persisted history; otherwise every incremental run would assess
        # only ~10 overlap bars and incorrectly downgrade READY -> WARMUP.
        self.cache.upsert_price_rows(price_rows_buffer)

        state_buffer=[]
        for r in received_rows:
            sym=r.Yahoo_Symbol; ws=r.WS_ID
            full_x=self.cache.load_price_frame(ws)
            qa=qa_symbol_frame(full_x,config=self.config,as_of=as_of)
            state_buffer.append({"ws_id":ws,"yahoo_symbol":sym,"mapping_status":r.Yahoo_Mapping_Status,
                   "last_fetch_utc":fetched,"batch_id":batch_id,"last_error":None,**{k:v for k,v in qa.items() if k!="warning_zero_volume"}})
            if (
                not repair_pass
                and self.config.repair_anomalies
                and qa["reason_code"] in {"SUSPICIOUS_RETURN_NEEDS_REPAIR", "INVALID_OHLC_OR_VOLUME"}
            ):
                repair_candidates.append(sym)

        # A transient missing symbol in an incremental multi-ticker response must
        # not erase a previously valid cache. Keep the cached series and derive
        # its status from the full history. Only names with no cached history at
        # all become DOWNLOAD_FAILED.
        for r in missing_rows:
            sym=r.Yahoo_Symbol; ws=r.WS_ID
            full_x=self.cache.load_price_frame(ws)
            if not full_x.empty:
                qa=qa_symbol_frame(full_x,config=self.config,as_of=as_of)
                state_buffer.append({"ws_id":ws,"yahoo_symbol":sym,"mapping_status":r.Yahoo_Mapping_Status,
                    "last_fetch_utc":fetched,"batch_id":batch_id,"last_error":"NO_DATA_IN_BATCH",
                    **{k:v for k,v in qa.items() if k!="warning_zero_volume"}})
            else:
                state_buffer.append({
                    "ws_id":ws,"yahoo_symbol":sym,"mapping_status":r.Yahoo_Mapping_Status,
                    "status":"DOWNLOAD_FAILED","reason_code":"NO_DATA_IN_BATCH","unique_bars":0,"valid_bars":0,
                    "repaired_rows":0,"suspicious_returns":0,"zero_volume_share":None,"first_bar_date":None,"last_bar_date":None,
                    "last_fetch_utc":fetched,"batch_id":batch_id,"last_error":"NO_DATA_IN_BATCH",
                })
        self.cache.upsert_states(state_buffer)
        self.cache.log_batch({"batch_id":batch_id,"source_id":SOURCE_ID,"started_utc":started,"finished_utc":fetched,
                              "symbol_count":len(symbols),"received_count":len(received),"missing_count":len(missing),"retry_count":retries,
                              "repair_pass":int(repair_pass),"status":"SUCCESS" if not missing else "PARTIAL","error_text":None})
        self.cache.conn.commit(); return repair_candidates,missing

    def _rescue_missing_symbols(
        self,
        mapped: pd.DataFrame,
        missing_symbols: Sequence[str],
        *,
        as_of: date | None = None,
    ) -> tuple[list[str], list[str], int]:
        """One bounded rescue pass for symbols omitted by normal bulk responses.

        This is deliberately NOT a per-security fallback architecture. All names
        missing after the normal bulk pass are regrouped into rescue batches and
        fetched once with a full 2y period. The normal one-retry ceiling inside
        _download_with_retry still applies.
        """
        wanted = sorted(set(str(s) for s in missing_symbols if s))
        if not wanted:
            return [], [], 0
        rescue_df = mapped[mapped["Yahoo_Symbol"].isin(wanted)].copy()
        repair_syms: list[str] = []
        still_missing: list[str] = []
        attempted = 0
        for b in _chunks(list(rescue_df.index), self.config.batch_size):
            rb = rescue_df.loc[b]
            attempted += len(rb)
            r, m = self._process_batch(
                rb,
                period=self.config.initial_period,
                start=None,
                end=None,
                repair_pass=False,
                as_of=as_of,
            )
            repair_syms.extend(r)
            still_missing.extend(m)
            if self.config.pause_between_batches_seconds:
                time.sleep(self.config.pause_between_batches_seconds)
        return repair_syms, still_missing, attempted

    def _run_targeted_repair(
        self,
        mapped: pd.DataFrame,
        repair_symbols: Sequence[str],
        *,
        as_of: date | None = None,
    ) -> int:
        """Full-history repair=True only for QA-flagged survivors."""
        wanted = sorted(set(str(s) for s in repair_symbols if s))
        if not wanted:
            return 0
        repair_df = mapped[mapped["Yahoo_Symbol"].isin(wanted)].copy()
        attempted = 0
        for b in _chunks(list(repair_df.index), self.config.repair_batch_size):
            rb = repair_df.loc[b]
            attempted += len(rb)
            self._process_batch(
                rb,
                period=self.config.initial_period,
                start=None,
                end=None,
                repair_pass=True,
                as_of=as_of,
            )
        return attempted

    def run_initial(self, universe: pd.DataFrame, *, as_of: date | None=None) -> dict[str,Any]:
        mapping=build_yahoo_symbol_map(universe)
        symbol_resets=self.cache.reset_changed_symbols(mapping)
        mapped=mapping[mapping["Yahoo_Symbol"].notna()].copy()
        unmapped=mapping[mapping["Yahoo_Symbol"].isna()].copy()
        for _,r in unmapped.iterrows():
            self.cache.upsert_state({
                "ws_id":r.WS_ID,"yahoo_symbol":None,"mapping_status":r.Yahoo_Mapping_Status,
                "status":"MAPPING_PENDING","reason_code":r.Yahoo_Mapping_Status,"unique_bars":0,"valid_bars":0,
                "repaired_rows":0,"suspicious_returns":0,"zero_volume_share":None,"first_bar_date":None,"last_bar_date":None,
                "last_fetch_utc":_utc_now(),"batch_id":None,"last_error":None,
            })

        repair_syms: list[str] = []
        missing: list[str] = []
        for b in _chunks(list(mapped.index), self.config.batch_size):
            rb=mapped.loc[b]
            r,m=self._process_batch(
                rb,period=self.config.initial_period,start=None,end=None,
                repair_pass=False,as_of=as_of
            )
            repair_syms.extend(r); missing.extend(m)
            if self.config.pause_between_batches_seconds:
                time.sleep(self.config.pause_between_batches_seconds)

        # One bounded rescue pass for symbols omitted by otherwise valid bulk batches.
        rescue_repairs, missing_after_rescue, rescue_attempted = self._rescue_missing_symbols(
            mapped, missing, as_of=as_of
        )
        repair_syms.extend(rescue_repairs)

        # Targeted yfinance repair=True for both suspicious returns and isolated
        # invalid OHLC/volume findings. Full history is re-fetched only for those names.
        repaired_attempted = self._run_targeted_repair(mapped, repair_syms, as_of=as_of)

        self.cache.conn.commit()
        result={
            "mode":"INITIAL","source":SOURCE_ID,"productive":False,
            "universe_count":int(len(universe)),"mapped_count":int(len(mapped)),"unmapped_count":int(len(unmapped)),
            "symbol_resets":int(len(symbol_resets)),
            "rescue_attempted":int(rescue_attempted),
            "repair_candidates":int(len(set(repair_syms))),"repair_attempted":int(repaired_attempted),
            "missing_symbols":int(len(set(missing_after_rescue))),"cache_counts":self.cache.counts(),
            "mapping_status_counts":mapping["Yahoo_Mapping_Status"].value_counts(dropna=False).to_dict(),
            "config":asdict(self.config),
        }
        result["run_hash"]=_canonical_hash(result)
        return result

    def run_incremental(self, universe: pd.DataFrame, *, end: date, as_of: date | None=None) -> dict[str,Any]:
        mapping=build_yahoo_symbol_map(universe)
        symbol_resets=self.cache.reset_changed_symbols(mapping)
        mapped=mapping[mapping["Yahoo_Symbol"].notna()].copy()
        dates=self.cache.last_bar_dates(mapped["WS_ID"].tolist())
        initial_idx=[]; update_idx=[]
        for idx,r in mapped.iterrows():
            (update_idx if r.WS_ID in dates else initial_idx).append(idx)

        missing: list[str] = []
        repair_syms: list[str] = []

        # Never force single-ticker calls: new names still go through initial bulk batches.
        if initial_idx:
            for b in _chunks(initial_idx,self.config.batch_size):
                r,m=self._process_batch(
                    mapped.loc[b],period=self.config.initial_period,start=None,end=None,
                    repair_pass=False,as_of=as_of
                )
                repair_syms.extend(r); missing.extend(m)

        # Cached names: each batch uses the earliest overlap start, safe but slightly redundant.
        for b in _chunks(update_idx,self.config.batch_size):
            rb=mapped.loc[b]
            starts=[dates[ws]-timedelta(days=self.config.overlap_calendar_days) for ws in rb["WS_ID"]]
            start=min(starts)
            r,m=self._process_batch(
                rb,period=None,start=start,end=end + timedelta(days=1),
                repair_pass=False,as_of=as_of
            )
            repair_syms.extend(r); missing.extend(m)

        # Missing names are regrouped into at most normal-size rescue batches, never
        # expanded into one request per U3K constituent.
        rescue_repairs, missing_after_rescue, rescue_attempted = self._rescue_missing_symbols(
            mapped, missing, as_of=as_of
        )
        repair_syms.extend(rescue_repairs)

        # Full-history repair pass only for names actually flagged by QA.
        repaired_attempted = self._run_targeted_repair(mapped, repair_syms, as_of=as_of)

        self.cache.conn.commit()
        result={
            "mode":"INCREMENTAL","source":SOURCE_ID,"productive":False,
            "universe_count":int(len(universe)),
            "symbol_resets":int(len(symbol_resets)),
            "initial_names":len(initial_idx),"update_names":len(update_idx),
            "rescue_attempted":int(rescue_attempted),
            "repair_candidates":int(len(set(repair_syms))),
            "repair_attempted":int(repaired_attempted),
            "missing_symbols":int(len(set(missing_after_rescue))),
            "cache_counts":self.cache.counts(),"config":asdict(self.config)
        }
        result["run_hash"]=_canonical_hash(result)
        return result


def save_manifest(payload: Mapping[str,Any], path: str|Path) -> None:
    Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8")


if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(description="Welt-Swing Long DEV yfinance batch price-cache")
    p.add_argument("universe_csv")
    p.add_argument("--db",default="runtime_cache/welt_swing_long_prices.sqlite")
    p.add_argument("--manifest",default="welt_swing_long_price_cache_manifest.json")
    p.add_argument("--batch-size",type=int,default=100)
    p.add_argument("--incremental-end",default=None,help="YYYY-MM-DD; omit for initial 2y load")
    args=p.parse_args()
    if not ALPHA_VANTAGE_ALLOWED:
        pass  # explicit architecture guard, no Alpha adapter exists in this module.
    cfg=FreeDataConfig(batch_size=args.batch_size)
    uni=pd.read_csv(args.universe_csv)
    cache=SQLitePriceCache(args.db)
    try:
        runner=YFinancePriceCacheRunner(cache,YFinanceBatchClient(config=cfg),config=cfg)
        if args.incremental_end:
            result=runner.run_incremental(uni,end=date.fromisoformat(args.incremental_end),as_of=date.today())
        else:
            result=runner.run_initial(uni,as_of=date.today())
        save_manifest(result,args.manifest)
        print(json.dumps(result,indent=2,ensure_ascii=False,default=str))
    finally:
        cache.close()
