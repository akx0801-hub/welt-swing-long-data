#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCHEMA = "WELT_SWING_NON_READY_REMEDIATION_V0_2"
PRODUCTIVE_TRADING_AUTHORITY = False
P0_RUN = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def load_cfg(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().eq("true")


def safe_last(s: pd.Series) -> float | None:
    x = s.dropna()
    return None if x.empty else float(x.iloc[-1])


def last_return(s: pd.Series, n: int) -> float | None:
    x = s.dropna()
    if len(x) <= n:
        return None
    base = float(x.iloc[-n-1])
    if base == 0:
        return None
    return float(x.iloc[-1] / base - 1.0)


def build_one_feature(ws_id: str, px: pd.DataFrame, meta_row: pd.Series) -> dict[str, Any]:
    # Import only on the real repository run. This keeps the offline self-test
    # dependency-free while reusing the exact existing feature-policy functions.
    from feature_builder import split_adjust_technical, technical_valid_mask_for_features

    g = px.copy().sort_values("day")
    raw_bars = len(g)
    mask = technical_valid_mask_for_features(g)
    g = g.loc[mask].copy()
    excluded = raw_bars - len(g)
    if g.empty:
        raise ValueError(f"No valid bars for {ws_id}")

    g = split_adjust_technical(g)
    c = pd.to_numeric(g["close_tech"], errors="coerce")
    h = pd.to_numeric(g["high_tech"], errors="coerce")
    l = pd.to_numeric(g["low_tech"], errors="coerce")
    v = pd.to_numeric(g["volume_tech"], errors="coerce")
    prev = c.shift(1)
    tr = pd.concat([(h-l).abs(), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    ema20 = c.ewm(span=20, adjust=False, min_periods=20).mean()
    ema50 = c.ewm(span=50, adjust=False, min_periods=50).mean()
    sma200 = c.rolling(200, min_periods=200).mean()
    high20 = h.rolling(20, min_periods=20).max()
    high60 = h.rolling(60, min_periods=60).max()
    high252 = h.rolling(252, min_periods=252).max()
    low20 = l.rolling(20, min_periods=20).min()
    low60 = l.rolling(60, min_periods=60).min()
    turnover = c * v

    last_close = safe_last(c)

    def dist(last_val):
        if last_close is None or last_val in (None, 0):
            return None
        return float(last_close / last_val - 1.0)

    e20, e50, s200 = safe_last(ema20), safe_last(ema50), safe_last(sma200)
    h20, h60, h252 = safe_last(high20), safe_last(high60), safe_last(high252)
    lo20, lo60 = safe_last(low20), safe_last(low60)
    atr = safe_last(atr14)

    meta_cols = [
        "WS_ID","Name","ISIN","Country","Primary_Ticker","Primary_Exchange",
        "Primary_MIC","Primary_Currency","Primary_Universe_Index","Index_Tags"
    ]
    row = {cname: txt(meta_row.get(cname)) for cname in meta_cols if cname in meta_row.index}
    row.update({
        "WS_ID": ws_id,
        "Yahoo_Symbol": txt(meta_row.get("Yahoo_Symbol")),
        "AsOf": txt(g["day"].iloc[-1]),
        "Bars": int(len(g)),
        "Bars_Raw": int(raw_bars),
        "Bars_Used": int(len(g)),
        "Excluded_Invalid_Bars": int(excluded),
        "Close_Raw": float(pd.to_numeric(g["close"], errors="coerce").iloc[-1]),
        "Close_Tech": last_close,
        "EMA20": e20,
        "EMA50": e50,
        "SMA200": s200,
        "ATR14_Wilder_DEV": atr,
        "ATR14_Pct_DEV": None if atr is None or last_close in (None, 0) else float(atr / last_close),
        "R5": last_return(c, 5),
        "R20": last_return(c, 20),
        "R60": last_return(c, 60),
        "High20": h20,
        "High60": h60,
        "High252": h252,
        "Low20": lo20,
        "Low60": lo60,
        "Dist_EMA20": dist(e20),
        "Dist_EMA50": dist(e50),
        "Dist_SMA200": dist(s200),
        "Dist_High252": dist(h252),
        "Range20_Pct": None if last_close in (None, 0) or h20 is None or lo20 is None else float((h20-lo20)/last_close),
        "MedianVolume20_Tech": float(v.tail(20).median()) if len(v.dropna()) >= 20 else None,
        "MedianTurnover20_Native": float(turnover.tail(20).median()) if len(turnover.dropna()) >= 20 else None,
        "Split_Count": int((pd.to_numeric(g["stock_splits"], errors="coerce").fillna(0) > 0).sum()),
        "Feature_Status": "DEV_QA_FILTERED_CANDIDATE_NOT_PROMOTED",
    })
    return row


def load_px(conn: sqlite3.Connection, ws_id: str) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT * FROM price_daily WHERE ws_id=? ORDER BY day",
        conn,
        params=[ws_id],
    )


def classify_event_shape(events: pd.DataFrame, override: dict[str, dict]) -> dict[str, Any]:
    ws = str(events["WS_ID"].iloc[0])
    if ws in override:
        o = override[ws]
        return {
            "Event_Classification": o["Classification"],
            "Event_Action": o["Action"],
            "Event_Evidence_URL": o.get("Evidence_URL", ""),
            "Event_Evidence_Note": o.get("Evidence_Note", ""),
        }

    ratios = 1.0 + pd.to_numeric(events["return"], errors="coerce")
    x100 = ((ratios.between(90, 110)) | (ratios.between(0.009, 0.011))).sum()
    if len(events) >= 2 and x100 >= 2:
        return {
            "Event_Classification": "LIKELY_PROVIDER_SCALE_SWITCH_X100",
            "Event_Action": "KEEP_QUARANTINE_SCALE_NORMALIZATION_RESEARCH",
            "Event_Evidence_URL": "",
            "Event_Evidence_Note": "Data-shape classification: repeated approximately 100x / 0.01x close transitions.",
        }
    if len(events) == 1:
        return {
            "Event_Classification": "SINGLE_EXTREME_MOVE_EVENT_RESEARCH",
            "Event_Action": "TARGETED_EVENT_OR_CORPORATE_ACTION_RESEARCH",
            "Event_Evidence_URL": "",
            "Event_Evidence_Note": "Single >50% close-to-close move without nearby split confirmation.",
        }
    return {
        "Event_Classification": "MULTI_EXTREME_MOVE_EVENT_RESEARCH",
        "Event_Action": "TARGETED_EVENT_OR_CORPORATE_ACTION_RESEARCH",
        "Event_Evidence_URL": "",
        "Event_Evidence_Note": "Multiple >50% close-to-close moves; no automatic normalization.",
    }


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_cfg(cfg_path)
    exp = cfg["expected"]
    qap = cfg["qa_policy"]

    master = pd.read_csv(cfg["source_master"], keep_default_na=False, dtype=str)
    diag = pd.read_csv(cfg["source_diagnostic"], keep_default_na=False, dtype=str)
    events = pd.read_csv(cfg["source_suspicious_events"], keep_default_na=False, dtype=str)
    base_features = pd.read_csv(cfg["source_features"], keep_default_na=False)

    if len(master) != exp["source_master_rows"]:
        raise SystemExit(f"master rows {len(master)} != {exp['source_master_rows']}")
    if int(bool_series(master["Active"]).sum()) != exp["source_active_rows"]:
        raise SystemExit("source active row count mismatch")
    if len(diag) != exp["source_non_ready_rows"]:
        raise SystemExit("diagnostic row count mismatch")
    if len(base_features) != exp["source_ready_rows"]:
        raise SystemExit("base feature row count mismatch")
    if master["WS_ID"].duplicated().any():
        raise SystemExit("duplicate WS_ID in source master")

    # Guard the Clearway identity case explicitly: the Class-C security already
    # exists as its own canonical row. Therefore the retired Class-A row must be
    # inactivated, not mapped onto CWEN and duplicated.
    cwen_ids = set(master.loc[
        master["WS_ID"].isin(["WS:US:CWEN", "WS:US:CWEN.A"]), "WS_ID"
    ])
    if cwen_ids != {"WS:US:CWEN", "WS:US:CWEN.A"}:
        raise SystemExit(f"Clearway identity guard failed: {sorted(cwen_ids)}")

    decisions = cfg["listing_evidence"] + cfg.get("additional_mapping_corrections", [])
    decision_by_id = {d["WS_ID"]: d for d in decisions}
    if len(decision_by_id) != len(decisions):
        raise SystemExit("duplicate evidence decision WS_ID")

    out_master = master.copy()
    for c in [
        "Data_Remediation_Status","Current_Exchange_Ticker",
        "Data_Remediation_Effective_Date","Data_Remediation_Evidence_URL",
        "Data_Remediation_Evidence_Note","Data_Remediation_UTC"
    ]:
        if c not in out_master.columns:
            out_master[c] = ""

    changed = []
    for idx, row in out_master.iterrows():
        ws = txt(row.get("WS_ID"))
        if ws not in decision_by_id:
            continue
        d = decision_by_id[ws]
        action = d["Action"]
        old_symbol = txt(row.get("Yahoo_Symbol"))
        if d.get("Old_Yahoo_Symbol") and old_symbol != d["Old_Yahoo_Symbol"]:
            raise SystemExit(
                f"{ws}: expected old symbol {d['Old_Yahoo_Symbol']}, got {old_symbol}"
            )

        if action == "EXCLUDE_INACTIVE":
            out_master.at[idx, "Active"] = "False"
        elif action == "REMAP_ACTIVE":
            out_master.at[idx, "Active"] = "True"
            out_master.at[idx, "Yahoo_Symbol"] = d["New_Yahoo_Symbol"]
            out_master.at[idx, "Mapping_Status"] = "EVIDENCE_REMEDIATED_V0_2"
            if "Provider_Listing_Type" in out_master.columns:
                out_master.at[idx, "Provider_Listing_Type"] = (
                    "CORPORATE_ACTION_SUCCESSOR"
                    if "SUCCESSOR" in d["Remediation_Status"]
                    else "PRIMARY"
                )
        elif action == "KEEP_ACTIVE_REFRESH":
            out_master.at[idx, "Active"] = "True"
        else:
            raise SystemExit(f"Unknown action {action} for {ws}")

        out_master.at[idx, "Data_Remediation_Status"] = d["Remediation_Status"]
        out_master.at[idx, "Current_Exchange_Ticker"] = d.get("Current_Exchange_Ticker", "")
        out_master.at[idx, "Data_Remediation_Effective_Date"] = d.get("Effective_Date", "")
        out_master.at[idx, "Data_Remediation_Evidence_URL"] = d.get("Evidence_URL", "")
        out_master.at[idx, "Data_Remediation_Evidence_Note"] = d.get("Evidence_Note", "")
        out_master.at[idx, "Data_Remediation_UTC"] = now_utc()
        changed.append({
            "WS_ID": ws,
            "Name": d["Name"],
            "Action": action,
            "Yahoo_Symbol_Before": old_symbol,
            "Yahoo_Symbol_After": txt(out_master.at[idx, "Yahoo_Symbol"]),
            "Remediation_Status": d["Remediation_Status"],
            "Effective_Date": d.get("Effective_Date", ""),
            "Evidence_URL": d.get("Evidence_URL", ""),
            "Provider_Evidence_URL": d.get("Provider_Evidence_URL", ""),
            "Evidence_Note": d.get("Evidence_Note", ""),
        })

    active_after = out_master.loc[bool_series(out_master["Active"])].copy()
    if len(active_after) != exp["active_rows_after_evidence_remediation"]:
        raise SystemExit(
            f"active after remediation {len(active_after)} != "
            f"{exp['active_rows_after_evidence_remediation']}"
        )
    if active_after["Yahoo_Symbol"].astype(str).str.strip().eq("").any():
        bad = active_after.loc[
            active_after["Yahoo_Symbol"].astype(str).str.strip().eq(""),
            ["WS_ID","Name"]
        ].to_dict("records")
        raise SystemExit(f"active blank Yahoo symbols after remediation: {bad[:10]}")
    dup_symbols = active_after.loc[
        active_after["Yahoo_Symbol"].astype(str).duplicated(keep=False),
        ["WS_ID","Name","Yahoo_Symbol"]
    ]
    if not dup_symbols.empty:
        raise SystemExit(
            "Provider symbol collision after remediation: "
            + json.dumps(dup_symbols.to_dict("records")[:20], ensure_ascii=False)
        )

    filterable = diag[
        diag["Diagnostic_Classification"].eq("LIKELY_ISOLATED_INVALID_BARS_FILTERABLE")
    ].copy()
    if len(filterable) != exp["filterable_invalid_candidates"]:
        raise SystemExit(
            f"filterable candidates {len(filterable)} != {exp['filterable_invalid_candidates']}"
        )

    filterable["Suspicious_Return_Events_Recomputed"] = pd.to_numeric(
        filterable["Suspicious_Return_Events_Recomputed"], errors="coerce"
    ).fillna(0).astype(int)

    qa_rows = []
    for _, r in filterable.iterrows():
        invalid = int(float(r["Invalid_Cached_Bars"]))
        cached = int(float(r["Cached_Price_Rows"]))
        valid = int(float(r["Valid_Bars"]))
        inv_share = invalid / cached if cached else 1.0
        fresh = float(r["Last_Bar_Age_Days"]) <= float(qap["stale_calendar_days"])
        has_susp = int(r["Suspicious_Return_Events_Recomputed"]) > 0
        strict_pass = (
            invalid <= qap["max_filterable_invalid_bars"]
            and inv_share <= qap["max_filterable_invalid_share"]
            and valid >= qap["minimum_valid_bars"]
            and fresh
            and not has_susp
        )
        qa_rows.append({
            "WS_ID": r["WS_ID"],
            "Name": r["Name"],
            "Primary_Universe_Index": r["Primary_Universe_Index"],
            "Yahoo_Symbol": r["Yahoo_Symbol"],
            "Invalid_Bars": invalid,
            "Cached_Bars": cached,
            "Valid_Bars": valid,
            "Invalid_Share": inv_share,
            "Fresh": bool(fresh),
            "Suspicious_Return_Events": int(r["Suspicious_Return_Events_Recomputed"]),
            "Strict_Filtered_QA_Pass": bool(strict_pass),
            "Shadow_Status": (
                "READY_FILTERED_QA_CANDIDATE_NOT_PROMOTED"
                if strict_pass
                else "KEEP_QUARANTINE_OVERLAPPING_ANOMALY"
            ),
        })
    qa_df = pd.DataFrame(qa_rows)
    shadow_ready = qa_df.loc[qa_df["Strict_Filtered_QA_Pass"]].copy()

    if len(shadow_ready) != exp["shadow_filtered_ready_expected"]:
        raise SystemExit(
            f"shadow filtered ready {len(shadow_ready)} != "
            f"{exp['shadow_filtered_ready_expected']}"
        )

    db_path = Path(cfg["sqlite_db"])
    if not db_path.exists():
        raise SystemExit(f"SQLite cache missing: {db_path}")

    meta = out_master.set_index("WS_ID", drop=False)
    shadow_feature_rows = []
    conn = sqlite3.connect(db_path)
    try:
        observed_rows = conn.execute("SELECT COUNT(*) FROM price_daily").fetchone()[0]
        if observed_rows < 1800000:
            raise SystemExit(f"SQLite cache incomplete: {observed_rows}")
        for ws in shadow_ready["WS_ID"].astype(str):
            px = load_px(conn, ws)
            if ws not in meta.index:
                raise SystemExit(f"Missing master metadata for {ws}")
            feat = build_one_feature(ws, px, meta.loc[ws])
            if int(feat["Excluded_Invalid_Bars"]) < 1:
                raise SystemExit(f"{ws}: expected invalid bars to be excluded")
            shadow_feature_rows.append(feat)
    finally:
        conn.close()

    added_features = pd.DataFrame(shadow_feature_rows)
    effective_features = pd.concat([base_features, added_features], ignore_index=True, sort=False)
    if effective_features["WS_ID"].astype(str).duplicated().any():
        dup = effective_features.loc[
            effective_features["WS_ID"].astype(str).duplicated(keep=False),
            ["WS_ID","Name"]
        ]
        raise SystemExit(
            "Duplicate features after shadow merge: "
            + str(dup.head(20).to_dict("records"))
        )
    expected_effective = exp["source_ready_rows"] + exp["shadow_filtered_ready_expected"]
    if len(effective_features) != expected_effective:
        raise SystemExit(
            f"effective features {len(effective_features)} != {expected_effective}"
        )

    event_override = {e["WS_ID"]: e for e in cfg.get("event_evidence", [])}
    event_rows = []
    for ws, g in events.groupby("WS_ID", sort=False):
        cls = classify_event_shape(g, event_override)
        diag_row = diag.loc[diag["WS_ID"].eq(ws)]
        original_status = txt(diag_row.iloc[0]["Original_Status"]) if len(diag_row) else ""
        original_reason = txt(diag_row.iloc[0]["Original_Reason"]) if len(diag_row) else ""
        event_rows.append({
            "WS_ID": ws,
            "Name": txt(g.iloc[0]["Name"]),
            "Primary_Universe_Index": txt(g.iloc[0]["Primary_Universe_Index"]),
            "Original_Status": original_status,
            "Original_Reason": original_reason,
            "Event_Count": int(len(g)),
            "Max_Abs_Return": float(pd.to_numeric(g["return"], errors="coerce").abs().max()),
            "Any_Split_Nearby": bool(
                g["split_nearby"].astype(str).str.lower().eq("true").any()
            ),
            **cls,
        })
    event_df = pd.DataFrame(event_rows)

    refresh = []
    for d in decisions:
        if d["Action"] in {"REMAP_ACTIVE", "KEEP_ACTIVE_REFRESH"}:
            refresh.append({
                "WS_ID": d["WS_ID"],
                "Name": d["Name"],
                "Yahoo_Symbol": d["New_Yahoo_Symbol"],
                "Reason": d["Remediation_Status"],
                "Refresh_Mode": "FULL_2Y_TARGETED",
                "Evidence_URL": d.get("Evidence_URL", ""),
            })
    for e in cfg.get("event_evidence", []):
        if e["Action"] == "TARGETED_FULL_REFRESH_AFTER_SPLIT":
            r = out_master.loc[out_master["WS_ID"].eq(e["WS_ID"])]
            if len(r) != 1:
                raise SystemExit(f"event evidence WS_ID missing/duplicate: {e['WS_ID']}")
            refresh.append({
                "WS_ID": e["WS_ID"],
                "Name": e["Name"],
                "Yahoo_Symbol": txt(r.iloc[0]["Yahoo_Symbol"]),
                "Reason": e["Classification"],
                "Refresh_Mode": "FULL_2Y_TARGETED",
                "Evidence_URL": e.get("Evidence_URL", ""),
            })
    refresh_df = pd.DataFrame(refresh).drop_duplicates("WS_ID")
    if len(refresh_df) != exp["targeted_refresh_queue_rows"]:
        raise SystemExit(
            f"refresh queue {len(refresh_df)} != {exp['targeted_refresh_queue_rows']}"
        )

    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    master_csv = Path(cfg["remediated_master_csv"])
    master_xlsx = Path(cfg["remediated_master_xlsx"])
    master_csv.parent.mkdir(parents=True, exist_ok=True)

    out_master.to_csv(master_csv, index=False)
    pd.DataFrame(changed).to_csv(
        out_dir / "listing_and_mapping_remediation_audit_v0.2.csv", index=False
    )
    qa_df.to_csv(
        out_dir / "qa_filtered_bar_policy_candidates_v0.2.csv", index=False
    )
    added_features.to_csv(
        out_dir / "qa_filtered_feature_additions_v0.2.csv", index=False
    )
    effective_features.to_csv(
        out_dir / "effective_features_shadow_v0.2.csv", index=False
    )
    event_df.to_csv(
        out_dir / "suspicious_event_classification_v0.2.csv", index=False
    )
    refresh_df.to_csv(
        out_dir / "targeted_refresh_queue_v0.2.csv", index=False
    )

    active_after_n = int(bool_series(out_master["Active"]).sum())
    shadow_ready_n = int(qa_df["Strict_Filtered_QA_Pass"].sum())
    effective_ready_shadow = exp["source_ready_rows"] + shadow_ready_n
    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "NON_READY_REMEDIATION_V0_2_COMPLETE",
        "source_master_rows": int(len(master)),
        "source_active_rows": exp["source_active_rows"],
        "active_rows_after_evidence_remediation": active_after_n,
        "delisted_or_retired_exclusions": sum(
            1 for d in decisions if d["Action"] == "EXCLUDE_INACTIVE"
        ),
        "provider_or_successor_remaps": sum(
            1 for d in decisions if d["Action"] == "REMAP_ACTIVE"
        ),
        "current_symbol_refresh_only": sum(
            1 for d in decisions if d["Action"] == "KEEP_ACTIVE_REFRESH"
        ),
        "filterable_invalid_bar_candidates": int(len(qa_df)),
        "shadow_filtered_ready_candidates": shadow_ready_n,
        "overlap_anomaly_hold_rows": int((~qa_df["Strict_Filtered_QA_Pass"]).sum()),
        "base_ready_rows": exp["source_ready_rows"],
        "effective_ready_shadow_if_qa_policy_approved": effective_ready_shadow,
        "effective_feature_rows_shadow": int(len(effective_features)),
        "effective_ready_shadow_pct_of_active_after_remediation": round(
            100.0 * effective_ready_shadow / active_after_n, 4
        ),
        "event_classification_rows": int(len(event_df)),
        "event_classification_counts": {
            str(k): int(v)
            for k, v in event_df["Event_Classification"].value_counts().to_dict().items()
        },
        "targeted_refresh_queue_rows": int(len(refresh_df)),
        "provider_symbol_duplicates_after_remediation": 0,
        "sqlite_price_rows_observed": int(observed_rows),
        "automatic_cache_status_promotions": 0,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "notes": [
            "Six stale/delisted/retired source rows are marked inactive; no replacement constituent is injected mid-freeze.",
            "Clearway Class A is inactivated because it converted into the already-existing canonical Class C row WS:US:CWEN; this prevents a duplicate provider symbol.",
            "Provider/successor mappings are evidence-remediated for Block ASX, Sigma Foods, Goodman NZ and Sasol ordinary shares.",
            "Sasol SOLBE1.JO is corrected to ordinary Top-40 share SOL.JO; SOLBE1 is a distinct BEE share class.",
            "The two-invalid-bar policy is evaluated only in shadow. Raw bars remain untouched and no cache state is promoted.",
            "Only rows with <=2 invalid bars, <=1% invalid share, >=260 valid bars, fresh data and zero suspicious-return events qualify for shadow filtered-ready.",
            "Existing feature logic excludes invalid bars; 20 additional shadow feature rows are computed to validate the policy before promotion.",
            "Suspicious-return rows are classified by data shape, with explicit evidence override for the Monster Beverage 2-for-1 split.",
            "A six-name targeted full-refresh queue is produced; that refresh is a separate next step.",
            "P0 remains off."
        ],
    }
    (out_dir / "summary_v0.2.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with pd.ExcelWriter(master_xlsx, engine="openpyxl") as xw:
        out_master.to_excel(xw, sheet_name="Universe_Master", index=False)
        pd.DataFrame(changed).to_excel(xw, sheet_name="Evidence_Audit", index=False)
        qa_df.to_excel(xw, sheet_name="QA_Filter_Candidates", index=False)
        event_df.to_excel(xw, sheet_name="Event_Classification", index=False)
        refresh_df.to_excel(xw, sheet_name="Targeted_Refresh", index=False)

    print(json.dumps(summary, ensure_ascii=False))
    return summary


def self_test() -> None:
    e = pd.DataFrame([
        {"WS_ID":"A","return":"-0.99"},
        {"WS_ID":"A","return":"99.0"},
    ])
    x = classify_event_shape(e, {})
    assert x["Event_Classification"] == "LIKELY_PROVIDER_SCALE_SWITCH_X100"

    e2 = pd.DataFrame([{"WS_ID":"B","return":"0.75"}])
    y = classify_event_shape(e2, {})
    assert y["Event_Classification"] == "SINGLE_EXTREME_MOVE_EVENT_RESEARCH"

    e3 = pd.DataFrame([
        {"WS_ID":"M","return":"-0.5"},
        {"WS_ID":"M","return":"1.0"},
    ])
    z = classify_event_shape(
        e3,
        {"M": {"Classification":"CONFIRMED_SPLIT_RELATED_PROVIDER_MIX",
               "Action":"TARGETED_FULL_REFRESH_AFTER_SPLIT"}}
    )
    assert z["Event_Classification"] == "CONFIRMED_SPLIT_RELATED_PROVIDER_MIX"

    print("NON_READY_REMEDIATION_V0_2_SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/non_ready_remediation_v0.2.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
