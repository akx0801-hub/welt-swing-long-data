#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

SCHEMA = "WELT_SWING_CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_V0_29"
STAGE_ID = "CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION"
LINEAGE = "CURRENT_MASTER_CLEAN_RESTART"

MISSING = [
    "US_SP1500", "MX_IPC", "KR_KOSPI200", "AU_ASX200",
    "NZ_NZX50", "BR_IBRX100", "ZA_TOP40",
]


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def text(v):
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return "" if v is None else str(v).strip()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def require(cond, msg):
    if not cond:
        raise SystemExit(msg)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(items):
    payload = "|".join(f"{k}={items[k]}" for k in sorted(items))
    return hashlib.sha256(payload.encode()).hexdigest()


def allowed(url, domains):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in domains)


def slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")


def error_landing(url, html):
    low_url, low = url.lower(), html.lower()
    return (
        "/error/503" in low_url
        or "/comm/error/503" in low_url
        or ("service unavailable" in low and "503" in low)
        or ("오류" in html and "503" in html)
    )


def probe(session, src, raw_dir, domains):
    row = {
        "Segment_ID": src["segment_id"],
        "Source_ID": src["source_id"],
        "Source_Name": src["source_name"],
        "Configured_URL": src["url"],
        "Probe_Status": "NOT_RUN",
        "HTTP_Status": "",
        "Final_URL": "",
        "Response_Bytes": 0,
        "Candidate_Link_Count": 0,
        "Full_List_UI_Marker": False,
        "Subscription_Blocker_Marker": False,
        "Error": "",
    }
    try:
        require(allowed(src["url"], domains), f"URL outside allowlist: {src['url']}")
        r = session.get(src["url"], timeout=30, allow_redirects=True)
        row["HTTP_Status"] = r.status_code
        row["Final_URL"] = r.url
        row["Response_Bytes"] = len(r.content)
        require(allowed(r.url, domains), f"Redirect outside allowlist: {r.url}")
        r.raise_for_status()
        html = r.text
        if error_landing(r.url, html):
            raise RuntimeError(f"Error landing page: {r.url}")
        (raw_dir / f"{slug(src['source_id'])}.html").write_bytes(r.content)
        low = html.lower()
        row["Full_List_UI_Marker"] = (
            "full constituents list" in low
            or "constituents list" in low
            or "carteira teórica" in low
        )
        row["Subscription_Blocker_Marker"] = (
            "no longer displays indices constituent data" in low
            or ("subscription options" in low and "constituent" in low)
        )
        row["Probe_Status"] = "HTTP_OK"
        return row, html
    except Exception as e:
        row["Probe_Status"] = "ERROR"
        row["Error"] = f"{type(e).__name__}: {e}"
        return row, ""


def extract_candidate_links(src, html, domains):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    terms = (
        "download", "constituent", "composition", "carteira", "review",
        "rebalance", "index", "indice", "índice", "muestra", "portfolio",
        "appendix", "weight", "csv", "xlsx", "xls", "pdf",
    )
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        href = text(a.get("href"))
        label = " ".join(a.stripped_strings)
        url = urljoin(src["url"], href)
        if not href or not allowed(url, domains):
            continue
        sig = (label + " " + url).lower()
        if not any(t in sig for t in terms) or url in seen:
            continue
        seen.add(url)
        out.append({
            "Segment_ID": src["segment_id"],
            "Source_ID": src["source_id"],
            "Link_Label": label[:300],
            "Candidate_URL": url,
            "Machine_Readable_Extension": bool(re.search(r"\.(csv|xlsx?|zip)(\?|$)", url.lower())),
            "PDF_Extension": bool(re.search(r"\.pdf(\?|$)", url.lower())),
            "Fetched_In_v0_29": False,
            "Candidate_Only_Not_Authority": True,
        })
    return out


def parse_b3(html, source_id, out_path):
    cols = [
        "Code", "Name", "Type", "Theoretical_Quantity", "Participation_Pct",
        "Source_ID", "Materialization_Status_v0_29",
    ]
    empty = pd.DataFrame(columns=cols)
    if not html:
        empty.to_csv(out_path, index=False)
        return {"rows": 0, "asof_text": "", "status": "NOT_MATERIALIZED_SOURCE_ERROR"}

    m = re.search(r"Carteira\s+do\s+Dia\s*-\s*(\d{2}/\d{2}/\d{2,4})", html, re.I)
    asof = m.group(1) if m else ""
    try:
        tables = pd.read_html(StringIO(html), decimal=",", thousands=".")
    except Exception:
        tables = []

    table = None
    for t in tables:
        heads = " ".join(str(c).strip().lower() for c in t.columns)
        if ("código" in heads or "codigo" in heads) and ("ação" in heads or "acao" in heads):
            table = t.copy()
            break
    if table is None:
        empty.to_csv(out_path, index=False)
        return {"rows": 0, "asof_text": asof, "status": "OFFICIAL_PAGE_REACHED_TABLE_NOT_MATERIALIZED"}

    rename = {}
    for c in table.columns:
        low = str(c).strip().lower()
        if "cód" in low or "cod" in low:
            rename[c] = "Code"
        elif "ação" in low or "acao" in low:
            rename[c] = "Name"
        elif low == "tipo":
            rename[c] = "Type"
        elif "qtde" in low or "quant" in low:
            rename[c] = "Theoretical_Quantity"
        elif "part" in low:
            rename[c] = "Participation_Pct"
    table = table.rename(columns=rename)
    if not {"Code", "Name"}.issubset(table.columns):
        empty.to_csv(out_path, index=False)
        return {"rows": 0, "asof_text": asof, "status": "OFFICIAL_TABLE_SCHEMA_NOT_VERIFIED"}

    keep = [c for c in ["Code","Name","Type","Theoretical_Quantity","Participation_Pct"] if c in table.columns]
    x = table[keep].copy()
    for c in ["Type","Theoretical_Quantity","Participation_Pct"]:
        if c not in x.columns:
            x[c] = ""
    x["Code"] = x["Code"].astype(str).str.strip()
    x["Name"] = x["Name"].astype(str).str.strip()
    x = x.loc[x["Code"].str.match(r"^[A-Z0-9]{4,12}$", na=False) & x["Name"].ne("")].copy()
    x = x.drop_duplicates("Code")
    x["Source_ID"] = source_id
    x["Materialization_Status_v0_29"] = "OFFICIAL_B3_IBRX100_PORTFOLIO_ROW"
    x = x[cols]
    x.to_csv(out_path, index=False)
    status = (
        "MATERIALIZED_OFFICIAL_B3_CURRENT_PORTFOLIO_EVIDENCE"
        if len(x) >= 80
        else "OFFICIAL_B3_TABLE_PARSED_BUT_ROW_COUNT_NOT_SUFFICIENT"
    )
    return {"rows": int(len(x)), "asof_text": asof, "status": status}


def segment_result(seg, probes, links, b3):
    p = probes.loc[probes["Segment_ID"].eq(seg)]
    ok = int(p["Probe_Status"].eq("HTTP_OK").sum())
    err = int(p["Probe_Status"].eq("ERROR").sum())
    nlinks = int(links["Segment_ID"].eq(seg).sum()) if len(links) else 0

    if seg == "US_SP1500":
        return "SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED", (
            f"Known blocker preserved; official probes OK={ok}, errors={err}; "
            "no verified public full 1500 export materialized."
        )
    if seg == "NZ_NZX50":
        blocked = p["Subscription_Blocker_Marker"].astype(str).str.lower().eq("true").any()
        if blocked:
            return "SOURCE_BLOCKED_PUBLIC_CONSTITUENT_DATA_WITHDRAWN_OR_SUBSCRIPTION_REQUIRED", (
                "NZX explicitly states constituent data is no longer displayed and points to S&P DJI."
            )
    if seg == "KR_KOSPI200":
        if err:
            return "SOURCE_BLOCKED_KRX_OFFICIAL_ROUTE_TECHNICAL_OR_SESSION_REQUIREMENT", (
                f"KRX fail-closed; OK={ok}, errors={err}."
            )
        return "OFFICIAL_KRX_ROUTE_REACHABLE_FULL_LIST_NOT_MATERIALIZED", (
            f"Official route reachable; no reproducible full 200 list materialized; links={nlinks}."
        )
    if seg == "BR_IBRX100":
        if b3["status"] == "MATERIALIZED_OFFICIAL_B3_CURRENT_PORTFOLIO_EVIDENCE":
            return "OFFICIAL_CURRENT_MEMBERSHIP_EVIDENCE_MATERIALIZED_IDENTITY_IMPORT_PENDING", (
                f"B3 portfolio parsed with {b3['rows']} unique security codes; no universe mutation."
            )
        return "OFFICIAL_ROUTE_REACHED_MEMBERSHIP_NOT_YET_MATERIALIZED", (
            f"B3 parser={b3['status']}; OK={ok}, errors={err}."
        )
    if seg == "MX_IPC":
        return "OFFICIAL_SPDJI_BMV_ROUTES_CONFIRMED_FULL_CURRENT_35_LIST_NOT_MATERIALIZED", (
            f"S&P DJI/BMV routes OK={ok}, errors={err}, candidate links={nlinks}."
        )
    if seg == "AU_ASX200":
        return "OFFICIAL_SPDJI_PRODUCT_ROUTE_CONFIRMED_FULL_CURRENT_200_LIST_NOT_MATERIALIZED", (
            f"S&P DJI route OK={ok}, errors={err}, candidate links={nlinks}."
        )
    if seg == "ZA_TOP40":
        return "OFFICIAL_JSE_REVIEW_ROUTE_MATERIALIZED_FULL_CURRENT_TOP40_SET_NOT_PROVEN", (
            f"JSE routes OK={ok}, errors={err}, document/review candidates={nlinks}."
        )
    return "OFFICIAL_PRODUCT_ROUTE_CONFIRMED_FULL_CURRENT_LIST_NOT_MATERIALIZED", (
        f"OK={ok}, errors={err}, candidate links={nlinks}."
    )


def write_handoff(versioned, stable, summary, status_df, checkpoint, prior):
    prior_text = Path(prior).read_text(encoding="utf-8")
    require("Version:** v0.28" in prior_text, "v0.28 CURRENT handoff required")
    lines = "\n".join(
        f"- `{r.Segment_ID}`: `{r.Materialization_State_v0_29}` — {r.Evidence_Summary_v0_29}"
        for r in status_df.itertuples()
    )
    body = f"""# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.29  
**Generated UTC:** {summary['generated_utc']}  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Primary lineage:** `CURRENT_MASTER_CLEAN_RESTART`  
**Trigger/input commit:** `{os.environ.get('GITHUB_SHA','LOCAL_OR_UNKNOWN')}`

## 1. Authority

Authoritative DEV master:
`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains solely authoritative for productive Swing decisions. Alpha Vantage remains forbidden.

## 2. Current-master universe

Canonical development snapshot remains unchanged at **1,535 securities from 7 of 14 target segments**.

v0.29 does not mutate the universe.

## 3. Missing-segment official-source materialization

{lines}

Configured official requests: {summary['official_request_count']}  
HTTP OK: {summary['official_http_ok_count']}  
Source errors: {summary['official_source_error_count']}  
Candidate-link follow requests: 0

## 4. Governance result

- Missing target segments checked: 7/7
- Canonical segments imported in v0.29: 0
- Universe mutation: `false`
- Instrument decisions changed: 0
- Eligibility promotions: 0
- Source superset complete: `false`
- `SWING_U3K_FROZEN`: `false`
- P0: `false`

Legacy Phase2/3663 membership remains diagnostic evidence only and must not populate the current master.

## 5. Current checkpoint

- Stage: `{checkpoint['stage_id']}`
- Run ID: `{checkpoint['run_id']}`
- Status: `{checkpoint['status']}`
- Checked: {checkpoint['checked_count']}
- Materialized-membership evidence segments: {checkpoint['pass_count']}
- Blocked/not-materialized: {checkpoint['fail_count']}
- Output hash: `{checkpoint['output_hash']}`
- Next stage: `{checkpoint['next_stage']}`

## 6. Recovery order

1. `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
2. `WELT-SWING-CURRENT-Handoff-CURRENT.md`
3. `output_current_master_missing_source_materialization_v0_29/stage_checkpoint_v0.29.json`
4. `output_current_master_missing_source_materialization_v0_29/manifest_v0.29.json`
5. `output_current_master_missing_source_materialization_v0_29/missing_segment_materialization_status_v0.29.csv`
6. `universe/Welt-Swing-Universe-Master-v2.0.xlsx`
7. `output_current_master_reconciliation_v0_28/summary_v0.28.json`

## 7. Handoff policy

Every major DEV stage refreshes both the versioned handoff and `WELT-SWING-CURRENT-Handoff-CURRENT.md`.

## 8. Next stage

`{summary['next_stage']}`

Only reproducibly materialized official evidence may proceed to identity/import/freeze.
"""
    Path(versioned).write_text(body, encoding="utf-8")
    Path(stable).write_text(body, encoding="utf-8")


def self_test():
    assert allowed("https://www.spglobal.com/x", ["spglobal.com"])
    assert allowed("https://data.krx.co.kr/x", ["krx.co.kr"])
    assert not allowed("https://example.com/x", ["spglobal.com"])
    assert error_landing("https://data.krx.co.kr/comm/error/503.html", "")
    assert len(MISSING) == 7
    print("CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_V0_29_SELF_TEST_PASS")


def run(cfg_path):
    started = now_utc()
    cfg = read_json(cfg_path)
    out = Path(cfg["output_dir"])
    raw = out/"raw_official_source"
    out.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)

    inp = {k: Path(v) for k, v in cfg["inputs"].items()}
    s28 = read_json(inp["v028_summary"])
    c28 = read_json(inp["v028_checkpoint"])
    blockers = read_csv(inp["v028_blocker_register"])
    source_audit = read_csv(inp["v028_source_authority_audit"])

    require(s28["run_status"] == "CURRENT_MASTER_UNIVERSE_RECONCILIATION_FREEZE_PLAN_V0_28_COMPLETE", "v0.28 summary mismatch")
    require(s28["lineage_scope"] == LINEAGE, "v0.28 lineage mismatch")
    require(s28["current_master_rows"] == 1535, "v0.28 master rows changed")
    require(s28["imported_segment_count"] == 7 and s28["missing_segment_count"] == 7, "v0.28 segment counts changed")
    require(c28["next_stage"] == STAGE_ID, "v0.28 next stage mismatch")
    require(set(blockers["Segment_ID"]) == set(MISSING), "v0.28 blocker set changed")
    require(Path(inp["current_handoff"]).exists(), "CURRENT handoff missing")

    sources = cfg["official_sources"]
    domains = cfg["network"]["allowed_domains"]
    require(len(sources) == cfg["network"]["max_requests"] == 10, "v0.29 request count/cap mismatch")
    require(set(x["segment_id"] for x in sources) == set(MISSING), "Every missing segment must have source coverage")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Welt-Swing-Long-DEV-v0.29 official-source-research/1.0",
        "Accept-Language": "en-US,en;q=0.8",
    })

    probe_rows, link_rows, html_by_id = [], [], {}
    for src in sources:
        row, html = probe(session, src, raw, domains)
        links = extract_candidate_links(src, html, domains)
        row["Candidate_Link_Count"] = len(links)
        probe_rows.append(row)
        link_rows.extend(links)
        html_by_id[src["source_id"]] = html

    probes = pd.DataFrame(probe_rows)
    links = pd.DataFrame(link_rows)
    if links.empty:
        links = pd.DataFrame(columns=[
            "Segment_ID","Source_ID","Link_Label","Candidate_URL",
            "Machine_Readable_Extension","PDF_Extension",
            "Fetched_In_v0_29","Candidate_Only_Not_Authority",
        ])
    probes.to_csv(out/"official_source_probe_status_v0.29.csv", index=False)
    links.to_csv(out/"official_candidate_links_v0.29.csv", index=False)

    b3 = parse_b3(
        html_by_id.get("B3_IBRX100_DAY_PORTFOLIO",""),
        "B3_IBRX100_DAY_PORTFOLIO",
        out/"b3_ibrx100_materialized_membership_v0.29.csv",
    )

    status_rows = []
    for seg in MISSING:
        state, evidence = segment_result(seg, probes, links, b3)
        old = blockers.loc[blockers["Segment_ID"].eq(seg), "Source_Gate_State_v0_28"].iloc[0]
        status_rows.append({
            "Segment_ID": seg,
            "v0_28_State": old,
            "Materialization_State_v0_29": state,
            "Evidence_Summary_v0_29": evidence,
            "Canonical_Membership_Imported_v0_29": False,
            "Universe_Mutated_v0_29": False,
            "Instrument_Decisions_Changed_v0_29": 0,
            "Eligibility_Promotions_v0_29": 0,
        })
    status = pd.DataFrame(status_rows)
    status.to_csv(out/"missing_segment_materialization_status_v0.29.csv", index=False)

    carry = source_audit.loc[source_audit["Rows"].astype(int).gt(0)].copy()
    carry["v0_29_State"] = "CURRENT_MASTER_IMPORTED_PROVENANCE_FREEZE_STILL_REQUIRED"
    carry["v0_29_Network_Probe_Performed"] = False
    carry["Canonical_Membership_Changed_v0_29"] = False
    carry.to_csv(out/"imported_segment_provenance_carryforward_v0.29.csv", index=False)

    pass_count = int(status["Materialization_State_v0_29"].str.startswith(
        "OFFICIAL_CURRENT_MEMBERSHIP_EVIDENCE_MATERIALIZED"
    ).sum())

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": "CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_V0_29_COMPLETE",
        "stage_status": "PARTIAL",
        "lineage_scope": LINEAGE,
        "current_master_rows_before": 1535,
        "current_master_rows_after": 1535,
        "imported_segments_before": 7,
        "imported_segments_after": 7,
        "missing_segments_checked": 7,
        "missing_segment_states": dict(zip(status["Segment_ID"], status["Materialization_State_v0_29"])),
        "materialized_membership_evidence_segments": pass_count,
        "canonical_segments_imported_v0_29": 0,
        "b3_ibrx100": b3,
        "official_request_count": len(probes),
        "official_http_ok_count": int(probes["Probe_Status"].eq("HTTP_OK").sum()),
        "official_source_error_count": int(probes["Probe_Status"].eq("ERROR").sum()),
        "candidate_link_count": len(links),
        "candidate_link_follow_requests": 0,
        "source_superset_complete": False,
        "source_superset_frozen": False,
        "swing_u3k_eligible_ready": False,
        "swing_u3k_frozen": False,
        "universe_mutated": False,
        "instrument_decisions_changed": 0,
        "eligibility_promotions_made": 0,
        "price_downloads_performed": False,
        "sector_rs_performed": False,
        "p0_run": False,
        "per_security_web_calls": False,
        "alpha_vantage_allowed": False,
        "productive_trading_authority": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": "CURRENT_MASTER_OFFICIAL_MEMBERSHIP_IDENTITY_IMPORT_AND_SOURCE_PROVENANCE_FREEZE",
    }
    sp = out/"summary_v0.29.json"
    sp.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    input_hashes = {k: sha256_file(v) for k, v in inp.items()}
    param_hash = sha256_file(cfg_path)
    core = [
        out/"official_source_probe_status_v0.29.csv",
        out/"official_candidate_links_v0.29.csv",
        out/"b3_ibrx100_materialized_membership_v0.29.csv",
        out/"missing_segment_materialization_status_v0.29.csv",
        out/"imported_segment_provenance_carryforward_v0.29.csv",
        sp,
    ]
    out_hash = combined_hash({p.name: sha256_file(p) for p in core})
    failed = status.loc[
        ~status["Materialization_State_v0_29"].str.startswith("OFFICIAL_CURRENT_MEMBERSHIP_EVIDENCE_MATERIALIZED"),
        "Segment_ID"
    ].tolist()
    checkpoint = {
        "schema": "WELT_SWING_STAGE_CHECKPOINT_V0_29",
        "run_id": cfg["run_id"],
        "stage_id": STAGE_ID,
        "stage_version": "v0.29",
        "start": started,
        "end": now_utc(),
        "input_hash": combined_hash(input_hashes),
        "parameter_hash": param_hash,
        "output_hash": out_hash,
        "input_count": 7,
        "checked_count": 7,
        "pass_count": pass_count,
        "fail_count": 7-pass_count,
        "data_error_count": 0,
        "quarantine_count": 0,
        "status": "PARTIAL",
        "failed_source": ";".join(failed),
        "lineage_scope": LINEAGE,
        "official_request_count": len(probes),
        "official_source_error_count": int(probes["Probe_Status"].eq("ERROR").sum()),
        "universe_mutated": False,
        "source_superset_complete": False,
        "swing_u3k_frozen": False,
        "p0_run": False,
        "coverage_gate_status": "BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE",
        "next_stage": summary["next_stage"],
    }
    cp = out/"stage_checkpoint_v0.29.json"
    cp.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")

    hv = Path(cfg["handoff"]["versioned_path"])
    hc = Path(cfg["handoff"]["stable_path"])
    write_handoff(hv, hc, summary, status, checkpoint, inp["current_handoff"])

    raw_files = list(raw.glob("*.html"))
    manifest_files = core + [cp, hv, hc] + raw_files
    manifest = {
        "schema": "WELT_SWING_CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_MANIFEST_V0_29",
        "generated_utc": now_utc(),
        "lineage_scope": LINEAGE,
        "input_hash": checkpoint["input_hash"],
        "parameter_hash": param_hash,
        "core_output_hash": out_hash,
        "official_requests": len(probes),
        "candidate_link_follow_requests": 0,
        "per_security_web_calls": False,
        "alpha_vantage_allowed": False,
        "universe_mutated": False,
        "files": {
            str(p): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in manifest_files
        },
    }
    (out/"manifest_v0.29.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_V0_29_RESULT_GATES_PASS")
    print(json.dumps(summary, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/current_master_missing_segment_official_source_materialization_v0.29.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    else:
        run(Path(args.config))


if __name__ == "__main__":
    main()
