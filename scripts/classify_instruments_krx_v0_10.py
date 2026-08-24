#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

SCHEMA = "WELT_SWING_INSTRUMENT_RESOLUTION_KRX_V0_10"

P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False
CANONICAL_MASTER_MUTATED = False


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


def compact_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:700]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm_kr_code(v: Any) -> str:
    s = "".join(ch for ch in txt(v) if ch.isdigit())
    return s.zfill(6)[-6:] if s else ""


def classify_krx(secugrp: Any, stock_kind: Any) -> dict[str, str]:
    group = txt(secugrp)
    kind = txt(stock_kind)

    if group == "주권" and kind == "보통주":
        return {
            "Instrument_Decision_v0_10": "PASS",
            "Instrument_Type_Resolved_v0_10": "COMMON_STOCK_BY_KRX_STOCK_KIND",
            "Instrument_Resolution_Method_v0_10": "KRX_OFFICIAL_ALL_STOCK_BASIC_INFORMATION",
            "Instrument_Resolution_Reason_v0_10": "KRX_SECURITY_GROUP_STOCK_CERTIFICATE_AND_STOCK_KIND_COMMON",
        }

    if group == "주권" and "우선주" in kind:
        return {
            "Instrument_Decision_v0_10": "FAIL",
            "Instrument_Type_Resolved_v0_10": "PREFERRED_STOCK_BY_KRX_STOCK_KIND",
            "Instrument_Resolution_Method_v0_10": "KRX_OFFICIAL_ALL_STOCK_BASIC_INFORMATION",
            "Instrument_Resolution_Reason_v0_10": "KRX_STOCK_KIND_PREFERRED_OUTSIDE_STRICT_COMMON_ORDINARY_GATE",
        }

    return {
        "Instrument_Decision_v0_10": "NOT_VERIFIED",
        "Instrument_Type_Resolved_v0_10": "UNKNOWN",
        "Instrument_Resolution_Method_v0_10": "KRX_STOCK_KIND_NOT_DETERMINISTIC_FOR_STRICT_GATE",
        "Instrument_Resolution_Reason_v0_10": "KRX_SECURITY_GROUP_OR_STOCK_KIND_NOT_RECOGNIZED_BY_V0_10_RULE",
    }


def self_test() -> None:
    a = classify_krx("주권", "보통주")
    b = classify_krx("주권", "우선주")
    c = classify_krx("주권", "신형우선주")
    d = classify_krx("기타", "보통주")
    assert a["Instrument_Decision_v0_10"] == "PASS"
    assert b["Instrument_Decision_v0_10"] == "FAIL"
    assert c["Instrument_Decision_v0_10"] == "FAIL"
    assert d["Instrument_Decision_v0_10"] == "NOT_VERIFIED"
    assert norm_kr_code("5930") == "005930"
    assert norm_kr_code("005930") == "005930"

    payload = {
        "OutBlock_1": [
            {
                "ISU_CD": "KR7005930003",
                "ISU_SRT_CD": "005930",
                "ISU_NM": "삼성전자보통주",
                "ISU_ABBRV": "삼성전자",
                "ISU_ENG_NM": "Samsung Electronics Co.,Ltd.",
                "MKT_TP_NM": "KOSPI",
                "SECUGRP_NM": "주권",
                "SECT_TP_NM": "",
                "KIND_STKCERT_TP_NM": "보통주",
                "PARVAL": "100",
                "LIST_SHRS": "5969782550",
            },
            {
                "ISU_CD": "KR7005931001",
                "ISU_SRT_CD": "005935",
                "ISU_NM": "삼성전자우선주",
                "ISU_ABBRV": "삼성전자우",
                "ISU_ENG_NM": "Samsung Electronics Co.,Ltd.(1P)",
                "MKT_TP_NM": "KOSPI",
                "SECUGRP_NM": "주권",
                "SECT_TP_NM": "",
                "KIND_STKCERT_TP_NM": "우선주",
                "PARVAL": "100",
                "LIST_SHRS": "822886700",
            },
        ]
    }
    ref = pd.DataFrame(payload["OutBlock_1"])
    assert set(["ISU_SRT_CD", "SECUGRP_NM", "KIND_STKCERT_TP_NM"]).issubset(ref.columns)
    print("INSTRUMENT_RESOLUTION_KRX_V0_10_SELF_TEST_PASS")


def fetch_krx_reference(cfg: dict[str, Any]) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    spec = cfg["krx_source"]
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd",
            "X-Requested-With": "XMLHttpRequest",
        }
    )

    status: dict[str, Any] = {
        "source_name": spec["name"],
        "source_url": spec["url"],
        "method": "POST",
        "request_payload": spec["data"],
        "http_status": None,
        "content_type": "",
        "bytes": 0,
        "sha256": "",
        "status": "REQUEST_ERROR",
        "error": "",
    }

    try:
        resp = session.post(
            spec["url"],
            data=spec["data"],
            timeout=int(cfg["request_timeout_seconds"]),
        )
        status["http_status"] = int(resp.status_code)
        status["content_type"] = resp.headers.get("Content-Type", "")
        status["bytes"] = int(len(resp.content))
        status["sha256"] = sha256_bytes(resp.content) if resp.content else ""
        resp.raise_for_status()

        payload = resp.json()
        rows = payload.get("OutBlock_1")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"KRX OutBlock_1 missing/empty; keys={list(payload)[:30]}")

        ref = pd.DataFrame(rows)
        required = {"ISU_SRT_CD", "SECUGRP_NM", "KIND_STKCERT_TP_NM"}
        missing = sorted(required - set(ref.columns))
        if missing:
            raise ValueError(f"KRX required columns missing: {missing}; columns={list(ref.columns)}")

        ref["_KRX_CODE_NORM"] = ref["ISU_SRT_CD"].map(norm_kr_code)
        ref = ref.loc[ref["_KRX_CODE_NORM"].ne("")].copy()
        if ref["_KRX_CODE_NORM"].duplicated().any():
            dups = ref.loc[ref["_KRX_CODE_NORM"].duplicated(keep=False), "_KRX_CODE_NORM"].tolist()[:20]
            raise ValueError(f"Duplicate KRX short codes in reference: {dups}")

        status["status"] = "PARSED_REFERENCE"
        return ref, status

    except Exception as exc:
        status["error"] = compact_error(exc)
        return None, status


def final_strict_status(row: pd.Series) -> str:
    if txt(row.get("Cache_Status")) != "READY":
        return "FAIL"

    lg = txt(row.get("Liquidity_Gate"))
    if lg != "PASS":
        return "FAIL" if lg in {"FAIL", "FAIL_STRICT"} else "NOT_VERIFIED"

    if txt(row.get("Scalable_Gate")) == "FAIL":
        return "FAIL"

    d = txt(row.get("Instrument_Decision_v0_10"))
    if d == "PASS":
        return "PASS"
    if d == "FAIL":
        return "FAIL"
    return "NOT_VERIFIED"


def run(cfg_path: Path) -> dict[str, Any]:
    cfg = load_json(cfg_path)
    out = Path(cfg["output_dir"])
    out.mkdir(parents=True, exist_ok=True)

    s9 = load_json(Path(cfg["source_summary_v0_9"]))
    if s9.get("schema") != "WELT_SWING_PRIMARY_MARKET_BUNDLE_PROBE_V0_9":
        raise SystemExit("Wrong v0.9 source schema")
    if s9.get("run_status") != "PRIMARY_MARKET_BUNDLE_PROBE_V0_9_COMPLETE":
        raise SystemExit("Unexpected v0.9 run status")
    if int(s9.get("remaining_manual_rows_v0_9", -1)) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Unexpected v0.9 manual count")
    if int(s9.get("strict_candidates_v0_9", -1)) != int(cfg["expected_source_strict_candidates"]):
        raise SystemExit("Unexpected v0.9 strict candidate count")
    if s9.get("p0_run") is not False or s9.get("alpha_vantage_allowed") is not False:
        raise SystemExit("v0.9 governance gate failed")

    manual = pd.read_csv(cfg["source_manual_queue_v0_9"], keep_default_na=False, dtype=str)
    full8 = pd.read_csv(cfg["source_full_eligibility_v0_8"], keep_default_na=False, dtype=str)

    if len(manual) != int(cfg["expected_source_manual_rows"]):
        raise SystemExit("Manual queue row count changed")
    if manual["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in manual queue")
    if full8["WS_ID"].duplicated().any():
        raise SystemExit("Duplicate WS_ID in v0.8 full eligibility")

    kr_target = manual.loc[manual["Primary_Universe_Index"].eq("KR_KOSPI200")].copy()
    if len(kr_target) != int(cfg["expected_kr_target_rows"]):
        raise SystemExit(f"KR target rows {len(kr_target)} != expected {cfg['expected_kr_target_rows']}")

    base_decision = (
        full8.loc[full8["WS_ID"].isin(set(kr_target["WS_ID"])), ["WS_ID", "Instrument_Decision_v0_8"]]
        .set_index("WS_ID")["Instrument_Decision_v0_8"]
    )
    if not base_decision.astype(str).eq("NOT_VERIFIED").all():
        raise SystemExit("KR v0.10 target contains a pre-existing v0.8 PASS/FAIL decision")

    ref, source_status = fetch_krx_reference(cfg)
    external_reference_requests = 1

    kr_resolution = kr_target.copy()
    kr_resolution["_KRX_CODE_NORM"] = kr_resolution["Primary_Ticker"].map(norm_kr_code)

    if ref is None:
        kr_resolution["KRX_Match_Status"] = "SOURCE_BLOCKED"
        kr_resolution["KRX_Match_Key"] = kr_resolution["_KRX_CODE_NORM"]
        kr_resolution["KRX_SECUGRP_NM"] = ""
        kr_resolution["KRX_KIND_STKCERT_TP_NM"] = ""
        kr_resolution["Instrument_Decision_v0_10"] = "NOT_VERIFIED"
        kr_resolution["Instrument_Type_Resolved_v0_10"] = "UNKNOWN"
        kr_resolution["Instrument_Resolution_Method_v0_10"] = "KRX_SOURCE_REQUEST_FAILED"
        kr_resolution["Instrument_Resolution_Reason_v0_10"] = "KRX_OFFICIAL_BULK_SOURCE_NOT_MATERIALIZED"
    else:
        ref.to_csv(out / "krx_reference_full_v0.10.csv", index=False)

        keep_cols = [
            c for c in [
                "_KRX_CODE_NORM",
                "ISU_CD",
                "ISU_SRT_CD",
                "ISU_NM",
                "ISU_ABBRV",
                "ISU_ENG_NM",
                "LIST_DD",
                "MKT_TP_NM",
                "SECUGRP_NM",
                "SECT_TP_NM",
                "KIND_STKCERT_TP_NM",
                "PARVAL",
                "LIST_SHRS",
            ]
            if c in ref.columns
        ]
        rename = {c: f"KRX_{c}" for c in keep_cols if c != "_KRX_CODE_NORM"}
        kr_resolution = kr_resolution.merge(
            ref[keep_cols].rename(columns=rename),
            on="_KRX_CODE_NORM",
            how="left",
            validate="one_to_one",
        )
        kr_resolution["KRX_Match_Key"] = kr_resolution["_KRX_CODE_NORM"]
        kr_resolution["KRX_Match_Status"] = kr_resolution.get("KRX_ISU_SRT_CD", "").map(
            lambda v: "MATCHED" if txt(v) else "NOT_MATCHED"
        )

        decisions = kr_resolution.apply(
            lambda r: classify_krx(r.get("KRX_SECUGRP_NM"), r.get("KRX_KIND_STKCERT_TP_NM")),
            axis=1,
        )
        dec_df = pd.DataFrame(decisions.tolist())
        kr_resolution = pd.concat(
            [kr_resolution.reset_index(drop=True), dec_df.reset_index(drop=True)],
            axis=1,
        )

        unmatched = kr_resolution["KRX_Match_Status"].ne("MATCHED")
        kr_resolution.loc[unmatched, "Instrument_Decision_v0_10"] = "NOT_VERIFIED"
        kr_resolution.loc[unmatched, "Instrument_Type_Resolved_v0_10"] = "UNKNOWN"
        kr_resolution.loc[unmatched, "Instrument_Resolution_Method_v0_10"] = "KRX_EXACT_CODE_NOT_MATCHED"
        kr_resolution.loc[unmatched, "Instrument_Resolution_Reason_v0_10"] = "NO_EXACT_KRX_REFERENCE_MATCH"

    kr_resolution["Instrument_Evidence_URL_v0_10"] = cfg["krx_source"]["evidence_url"]
    kr_resolution["Instrument_Evidence_Note_v0_10"] = (
        "Official KRX Data Marketplace all-stock basic-information payload. "
        "Strict PASS only when exact target-code match has SECUGRP_NM=주권 and "
        "KIND_STKCERT_TP_NM=보통주. Preferred-stock labels containing 우선주 are strict FAIL. "
        "All other values remain NOT_VERIFIED."
    )
    kr_resolution = kr_resolution.drop(columns=["_KRX_CODE_NORM"], errors="ignore")
    kr_resolution.to_csv(out / "krx_security_type_resolution_v0.10.csv", index=False)

    new_pass = kr_resolution.loc[kr_resolution["Instrument_Decision_v0_10"].eq("PASS")].copy()
    new_fail = kr_resolution.loc[kr_resolution["Instrument_Decision_v0_10"].eq("FAIL")].copy()
    unresolved_kr = kr_resolution.loc[kr_resolution["Instrument_Decision_v0_10"].eq("NOT_VERIFIED")].copy()

    new_pass.to_csv(out / "krx_new_pass_v0.10.csv", index=False)
    new_fail.to_csv(out / "krx_new_fail_v0.10.csv", index=False)
    unresolved_kr.to_csv(out / "krx_unresolved_v0.10.csv", index=False)

    # Start v0.10 full decision columns from frozen v0.8 decisions, then overlay only KR targets.
    full = full8.copy()
    carry = {
        "Instrument_Decision_v0_10": "Instrument_Decision_v0_8",
        "Instrument_Type_Resolved_v0_10": "Instrument_Type_Resolved_v0_8",
        "Instrument_Resolution_Method_v0_10": "Instrument_Resolution_Method_v0_8",
        "Instrument_Resolution_Reason_v0_10": "Instrument_Resolution_Reason_v0_8",
        "Instrument_Evidence_URL_v0_10": "Instrument_Evidence_URL_v0_8",
        "Instrument_Evidence_Note_v0_10": "Instrument_Evidence_Note_v0_8",
    }
    for new_col, old_col in carry.items():
        full[new_col] = full[old_col] if old_col in full.columns else ""

    overlay_cols = [
        "WS_ID",
        "Instrument_Decision_v0_10",
        "Instrument_Type_Resolved_v0_10",
        "Instrument_Resolution_Method_v0_10",
        "Instrument_Resolution_Reason_v0_10",
        "Instrument_Evidence_URL_v0_10",
        "Instrument_Evidence_Note_v0_10",
    ]
    overlay = kr_resolution[overlay_cols].copy().set_index("WS_ID")
    full = full.set_index("WS_ID")
    for col in overlay_cols[1:]:
        full.loc[overlay.index, col] = overlay[col]
    full = full.reset_index()

    full["Strict_Eligibility_v0_10"] = full.apply(final_strict_status, axis=1)

    strict = full.loc[full["Strict_Eligibility_v0_10"].eq("PASS")].copy()
    strict["MedianTurnover20_EUR"] = pd.to_numeric(strict["MedianTurnover20_EUR"], errors="coerce")
    strict["MedianTurnover60_EUR"] = pd.to_numeric(strict["MedianTurnover60_EUR"], errors="coerce")
    strict = strict.sort_values(
        ["MedianTurnover20_EUR", "MedianTurnover60_EUR", "WS_ID"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    strict.insert(0, "Strict_Candidate_Rank_v0_10", range(1, len(strict) + 1))

    resolved_ids = set(
        kr_resolution.loc[
            kr_resolution["Instrument_Decision_v0_10"].isin(["PASS", "FAIL"]), "WS_ID"
        ].astype(str)
    )
    remaining = manual.loc[~manual["WS_ID"].astype(str).isin(resolved_ids)].copy()

    if len(strict) != int(cfg["expected_source_strict_candidates"]) + len(new_pass):
        raise SystemExit(
            f"Strict candidate arithmetic failed: {len(strict)} != "
            f"{cfg['expected_source_strict_candidates']} + {len(new_pass)}"
        )
    if len(remaining) != int(cfg["expected_source_manual_rows"]) - len(resolved_ids):
        raise SystemExit("Remaining-manual arithmetic failed")

    full.to_csv(out / "eligibility_after_instrument_v0.10.csv", index=False)
    strict.to_csv(out / "strict_u3k_candidate_after_instrument_v0.10.csv", index=False)
    remaining.to_csv(out / "instrument_manual_review_queue_v0.10.csv", index=False)

    seg = remaining.groupby("Primary_Universe_Index").size().reset_index(name="Rows")
    seg.to_csv(out / "remaining_review_by_segment_v0.10.csv", index=False)

    if ref is not None:
        kind_counts = (
            kr_resolution.groupby(
                ["KRX_SECUGRP_NM", "KRX_KIND_STKCERT_TP_NM", "Instrument_Decision_v0_10"],
                dropna=False,
            )
            .size()
            .reset_index(name="Rows")
        )
    else:
        kind_counts = pd.DataFrame(
            [{
                "KRX_SECUGRP_NM": "",
                "KRX_KIND_STKCERT_TP_NM": "",
                "Instrument_Decision_v0_10": "NOT_VERIFIED",
                "Rows": len(kr_resolution),
            }]
        )
    kind_counts.to_csv(out / "krx_kind_counts_v0.10.csv", index=False)

    source_status_row = {
        "Source_Name": source_status["source_name"],
        "Source_URL": source_status["source_url"],
        "Method": source_status["method"],
        "HTTP_Status": source_status["http_status"] if source_status["http_status"] is not None else "",
        "Content_Type": source_status["content_type"],
        "Bytes": source_status["bytes"],
        "SHA256": source_status["sha256"],
        "Probe_Status": source_status["status"],
        "Target_Rows": len(kr_target),
        "Matched_Rows": int(kr_resolution["KRX_Match_Status"].eq("MATCHED").sum()),
        "PASS_Rows": len(new_pass),
        "FAIL_Rows": len(new_fail),
        "Unresolved_Rows": len(unresolved_kr),
        "Error": source_status["error"],
    }
    pd.DataFrame([source_status_row]).to_csv(out / "source_status_v0.10.csv", index=False)

    source_ok = source_status["status"] == "PARSED_REFERENCE"
    status_name = (
        "INSTRUMENT_RESOLUTION_KRX_V0_10_COMPLETE_WITH_REMAINING_REVIEW"
        if source_ok
        else "INSTRUMENT_RESOLUTION_KRX_V0_10_COMPLETE_WITH_SOURCE_BLOCK"
    )

    summary = {
        "schema": SCHEMA,
        "generated_utc": now_utc(),
        "run_status": status_name,
        "source_manual_rows_v0_9": int(len(manual)),
        "krx_target_rows": int(len(kr_target)),
        "krx_source_status": source_status["status"],
        "krx_http_status": source_status["http_status"],
        "krx_reference_rows": int(len(ref)) if ref is not None else 0,
        "krx_matched_rows": int(kr_resolution["KRX_Match_Status"].eq("MATCHED").sum()),
        "krx_pass_rows": int(len(new_pass)),
        "krx_fail_rows": int(len(new_fail)),
        "krx_unresolved_rows": int(len(unresolved_kr)),
        "remaining_manual_rows_v0_10": int(len(remaining)),
        "strict_candidates_v0_9": int(cfg["expected_source_strict_candidates"]),
        "strict_candidates_v0_10": int(len(strict)),
        "strict_freeze_allowed": bool(len(remaining) == 0),
        "external_reference_requests": int(external_reference_requests),
        "p0_run": P0_RUN,
        "productive_trading_authority": PRODUCTIVE_TRADING_AUTHORITY,
        "alpha_vantage_allowed": ALPHA_VANTAGE_ALLOWED,
        "price_downloads_performed": PRICE_DOWNLOADS_PERFORMED,
        "fx_downloads_performed": FX_DOWNLOADS_PERFORMED,
        "web_calls_per_security": WEB_CALLS_PER_SECURITY,
        "canonical_master_mutated": CANONICAL_MASTER_MUTATED,
        "source_error": source_status["error"],
        "notes": [
            "v0.10 consumes the frozen v0.9 667-row manual-review queue and frozen v0.8 full eligibility state.",
            "The KRX transport shape is remediated to a single official bulk POST using only bld and mktId=STK.",
            "No per-security request is made.",
            "Strict PASS requires an exact target-code match plus SECUGRP_NM=주권 and KIND_STKCERT_TP_NM=보통주.",
            "Preferred-stock labels containing 우선주 are strict FAIL.",
            "Unmatched or unrecognized KRX security-kind values remain NOT_VERIFIED.",
            "If the official KRX bulk source is blocked, the run completes fail-closed with zero new decisions.",
            "P0 remains off and the canonical master is not mutated.",
        ],
    }
    (out / "summary_v0.10.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/instrument_resolution_krx_v0.10.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    run(Path(args.config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
