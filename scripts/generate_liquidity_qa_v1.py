#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = lambda value: ROOT / value

SOURCE = P("universe/research_partial_1633.csv")
MAPPING = P("scripts/generate_company_security_mapping_v1.py")
POLICY = P("config/liquidity_qa_v1_policy.json")

L38 = P("output_current_master_research_partial_1633_data_refresh_v0_38/liquidity_current_1633_v0.38.csv")
S38 = P("output_current_master_research_partial_1633_data_refresh_v0_38/liquidity_session_evidence_v0.38.csv")
FX38 = P("output_current_master_research_partial_1633_data_refresh_v0_38/fx_coverage_v0.38.csv")
FXD38 = P("output_current_master_research_partial_1633_data_refresh_v0_38/fx_daily_v0.38.csv")
H38 = P("output_current_master_research_partial_1633_data_refresh_v0_38/history_gate_current_1633_v0.38.csv")
SUM38 = P("output_current_master_research_partial_1633_data_refresh_v0_38/summary_v0.38.json")

L48 = P("output_liquidity_fx_sidecar_236_v0_48/liquidity_236_v0.48.csv")
SUM48 = P("output_liquidity_fx_sidecar_236_v0_48/summary_v0.48.json")

US1 = P("output_us1/liquidity_us1.csv")
US1_SUM = P("output_us1/summary_us1.json")
US1_BRIDGE = P("output_us1_write/dry_run_write_plan.csv")

OUTPUT = P("output_liquidity_qa_v1/liquidity_qa_v1_2527.csv")

FIELDS = [
    "Security_Key",
    "Source_WS_ID",
    "Evidence_Source_WS_ID",
    "Liquidity_Status",
    "Liquidity_Bucket",
    "Usable_Session_Count",
    "MedianTurnover20_EUR",
    "Zero_Volume_Share",
    "Price_Currency",
    "FX_Evidence_Status",
    "Last_Liquidity_Observation_Date",
    "Liquidity_Currentness_Status",
    "Listing_Resolution_Status",
    "Source_ID",
    "Evidence_Artifact",
    "Source_AsOf",
    "Retrieved_At",
    "Liquidity_Policy_Version",
    "QA_Confidence",
    "QA_Flags",
]

EXPECTED_TOTAL = 2527
EXPECTED_ORIGINAL = 1633
EXPECTED_US1 = 372
EXPECTED_US2 = 369
EXPECTED_AU1 = 153
EXPECTED_UNSUPPORTED = 522

US1_SOURCE_ID = "US1_SP500_COMMON_EVIDENCE_GATE"
US2_SOURCE_ID = "US2_SP400_COMMON_ADMISSION"
AU1_SOURCE_ID = "AU1_EVIDENCE_ADMISSION_GATE"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path, required: list[str] | tuple[str, ...] = ()) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        missing = set(required) - set(fields)
        if missing:
            raise ValueError(f"{path}: missing required columns {sorted(missing)}")
        return list(reader)


def read_optional_csv(path: Path, required: list[str] | tuple[str, ...] = ()) -> list[dict[str, str]]:
    if path.stat().st_size == 0:
        return []
    return read_csv(path, required)


def index_unique(rows: list[dict[str, str]], key: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = (row.get(key) or "").strip()
        if not value or value in result:
            raise ValueError(f"{label}: invalid/duplicate {key}: {value!r}")
        result[value] = row
    return result


def mapping_security_key():
    spec = importlib.util.spec_from_file_location("company_security_mapping_v1", MAPPING)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Company/Security Mapping v1 authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.security_key


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def int_value(value: object) -> int | None:
    text = clean(value)
    if text == "":
        return None
    try:
        return int(Decimal(text))
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid integer value: {text!r}")


def decimal_value(value: object) -> Decimal | None:
    text = clean(value)
    if text == "":
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(f"invalid decimal value: {text!r}")


def decimal_text(value: object) -> str:
    number = decimal_value(value)
    if number is None:
        return ""
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def flags_text(policy: dict, flags: set[str]) -> str:
    allowed = policy["allowed_qa_flags"]
    unknown = flags - set(allowed)
    if unknown:
        raise ValueError(f"unknown QA flags: {sorted(unknown)}")
    return "|".join(flag for flag in allowed if flag in flags)


def listing_state(current: dict[str, str]) -> str:
    active = clean(current.get("Active")).upper()
    if active in {"FALSE", "0", "NO", "INACTIVE"}:
        return "LISTING_INACTIVE"
    mic = clean(current.get("Primary_MIC"))
    ticker = clean(current.get("Primary_Ticker"))
    if mic and ticker:
        return "LISTING_RESOLVED"
    if mic or ticker:
        return "LISTING_PARTIAL"
    return "LISTING_UNRESOLVED"


def bucket_for(policy: dict, median: Decimal) -> tuple[str, str]:
    thresholds = policy["thresholds"]
    preferred = Decimal(str(thresholds["preferred_turnover_eur"]))
    standard = Decimal(str(thresholds["standard_pass_turnover_eur"]))
    low = Decimal(str(thresholds["low_exception_turnover_eur"]))
    if median >= preferred:
        return "PREFERRED", "LIQUIDITY_OK"
    if median >= standard:
        return "STANDARD", "LIQUIDITY_OK"
    if median >= low:
        return "LOW_EXCEPTION", "LIQUIDITY_THIN"
    return "FAIL_LT_5M", "LIQUIDITY_VERY_THIN"


def legacy_v38_bucket(state: str) -> str | None:
    return {
        "PASS_PREFERRED": "PREFERRED",
        "PASS_STANDARD": "STANDARD",
        "LOW_LIQUIDITY_EXCEPTION_POOL": "LOW_EXCEPTION",
        "FAIL_LIQUIDITY": "FAIL_LT_5M",
    }.get(state)


def legacy_v48_bucket(value: str) -> str | None:
    return {
        "PREFERRED": "PREFERRED",
        "STANDARD": "STANDARD",
        "LOW_EXCEPTION": "LOW_EXCEPTION",
        "FAIL_LIQ": "FAIL_LT_5M",
    }.get(value)


def legacy_us1_bucket(value: str) -> str | None:
    return {
        "PREFERRED": "PREFERRED",
        "STANDARD": "STANDARD",
        "EXCEPTION": "LOW_EXCEPTION",
        "FAIL": "FAIL_LT_5M",
    }.get(value)


def status_precedence(policy: dict, candidates: set[str]) -> str:
    for status in policy["liquidity_status_precedence"]:
        if status in candidates:
            return status
    raise ValueError("no Liquidity_Status candidate")


def confidence_for(row: dict[str, str], flags: set[str]) -> str:
    status = row["Liquidity_Status"]
    listing = row["Listing_Resolution_Status"]
    if status in {"LIQUIDITY_CONFLICT", "LIQUIDITY_IDENTITY_UNRESOLVED", "LIQUIDITY_UNAVAILABLE"}:
        return "UNRESOLVED"
    if listing != "LISTING_RESOLVED":
        return "UNRESOLVED"
    if status == "LIQUIDITY_STALE":
        return "LOW"
    limitations = 0
    if row["Liquidity_Currentness_Status"] == "UNKNOWN":
        limitations += 1
    if row["FX_Evidence_Status"] == "FX_PARTIAL":
        limitations += 1
    if "MISSING_SESSION_EVIDENCE" in flags:
        limitations += 1
    if limitations >= 2:
        return "LOW"
    if limitations == 1:
        return "MEDIUM"
    return "HIGH"


def base_row(current: dict[str, str], key_fn, policy: dict) -> dict[str, str]:
    ws_id = clean(current.get("WS_ID"))
    if not ws_id:
        raise ValueError("current Research Partial contains blank WS_ID")
    row = {field: "" for field in FIELDS}
    row.update(
        Security_Key=key_fn(ws_id),
        Source_WS_ID=ws_id,
        Price_Currency=clean(current.get("Primary_Currency")).upper(),
        Listing_Resolution_Status=listing_state(current),
        Liquidity_Policy_Version=policy["policy_version"],
    )
    return row


def blank_measurements(row: dict[str, str], keep_usable: bool = False) -> None:
    if not keep_usable:
        row["Usable_Session_Count"] = ""
    row["Liquidity_Bucket"] = ""
    row["MedianTurnover20_EUR"] = ""
    row["Zero_Volume_Share"] = ""
    row["Last_Liquidity_Observation_Date"] = ""


def finalize_measured(
    row: dict[str, str],
    policy: dict,
    flags: set[str],
    usable: int | None,
    median: Decimal | None,
    legacy_bucket: str | None,
    explicit_stale: bool = False,
) -> dict[str, str]:
    listing = row["Listing_Resolution_Status"]
    candidates: set[str] = set()

    if listing == "LISTING_CONFLICT":
        candidates.add("LIQUIDITY_CONFLICT")
        flags.add("DATA_QUALITY_FAIL")
    elif listing in {"LISTING_PARTIAL", "LISTING_UNRESOLVED"}:
        candidates.add("LIQUIDITY_IDENTITY_UNRESOLVED")
        flags.add("IDENTITY_UNRESOLVED")
    elif listing == "LISTING_INACTIVE":
        candidates.add("LIQUIDITY_UNAVAILABLE")
        flags.add("LISTING_INACTIVE")

    if row["FX_Evidence_Status"] == "FX_CONFLICT":
        candidates.add("LIQUIDITY_CONFLICT")
        flags.add("DATA_QUALITY_FAIL")

    minimum = int(policy["thresholds"]["minimum_usable_sessions"])
    if usable is None or usable < minimum:
        candidates.add("LIQUIDITY_UNAVAILABLE")
        flags.add("INSUFFICIENT_USABLE_SESSIONS")
    if median is None and usable is not None and usable >= minimum:
        candidates.add("LIQUIDITY_UNAVAILABLE")
        flags.add("DATA_QUALITY_FAIL")

    if row["Price_Currency"] != "EUR" and row["FX_Evidence_Status"] not in {"FX_OK", "FX_PARTIAL"}:
        candidates.add("LIQUIDITY_UNAVAILABLE")
        if row["FX_Evidence_Status"] == "FX_UNAVAILABLE":
            flags.add("FX_EVIDENCE_MISSING")

    computed_bucket = ""
    if usable is not None and usable >= minimum and median is not None:
        computed_bucket, measured_status = bucket_for(policy, median)
        candidates.add(measured_status)
        if legacy_bucket is not None and legacy_bucket != computed_bucket:
            candidates.add("LIQUIDITY_CONFLICT")
            flags.add("DATA_QUALITY_FAIL")

    if explicit_stale and computed_bucket:
        candidates.add("LIQUIDITY_STALE")
        flags.add("STALE_LIQUIDITY")
        row["Liquidity_Currentness_Status"] = "STALE"

    if not candidates:
        candidates.add("LIQUIDITY_UNAVAILABLE")

    row["Liquidity_Status"] = status_precedence(policy, candidates)

    if row["Liquidity_Status"] in {"LIQUIDITY_OK", "LIQUIDITY_THIN", "LIQUIDITY_VERY_THIN", "LIQUIDITY_STALE"}:
        row["Liquidity_Bucket"] = computed_bucket
        row["MedianTurnover20_EUR"] = decimal_text(median)
    elif row["Liquidity_Status"] == "LIQUIDITY_UNAVAILABLE":
        row["Liquidity_Bucket"] = ""
        row["MedianTurnover20_EUR"] = ""
        row["Liquidity_Currentness_Status"] = "UNAVAILABLE"
    else:
        blank_measurements(row)
        row["Liquidity_Currentness_Status"] = "UNAVAILABLE"

    row["QA_Confidence"] = confidence_for(row, flags)
    row["QA_Flags"] = flags_text(policy, flags)
    return row


def unsupported_row(current: dict[str, str], key_fn, policy: dict, au1: bool) -> dict[str, str]:
    row = base_row(current, key_fn, policy)
    flags = {"MISSING_LIQUIDITY_EVIDENCE", "MISSING_CURRENTNESS_METADATA"}
    row.update(
        Liquidity_Status="LIQUIDITY_UNAVAILABLE",
        Liquidity_Bucket="",
        Usable_Session_Count="",
        MedianTurnover20_EUR="",
        Zero_Volume_Share="",
        FX_Evidence_Status="FX_UNAVAILABLE",
        Last_Liquidity_Observation_Date="",
        Liquidity_Currentness_Status="UNAVAILABLE",
        Source_ID=clean(current.get("Source_ID")),
        Evidence_Artifact="",
        Source_AsOf="",
        Retrieved_At="",
        QA_Confidence="UNRESOLVED",
    )
    if au1:
        flags.add("FX_EVIDENCE_MISSING")
    if row["Listing_Resolution_Status"] in {"LISTING_PARTIAL", "LISTING_UNRESOLVED"}:
        flags.add("IDENTITY_UNRESOLVED")
    if row["Listing_Resolution_Status"] == "LISTING_INACTIVE":
        flags.add("LISTING_INACTIVE")
    row["QA_Flags"] = flags_text(policy, flags)
    return row


def conflict_row(current: dict[str, str], key_fn, policy: dict, evidence_ws_id: str = "") -> dict[str, str]:
    row = base_row(current, key_fn, policy)
    row.update(
        Evidence_Source_WS_ID=evidence_ws_id,
        Liquidity_Status="LIQUIDITY_CONFLICT",
        FX_Evidence_Status="FX_CONFLICT",
        Liquidity_Currentness_Status="UNAVAILABLE",
        Listing_Resolution_Status="LISTING_CONFLICT",
        Source_ID="US1_LIQUIDITY_QA",
        Evidence_Artifact="output_us1_write/dry_run_write_plan.csv",
        QA_Confidence="UNRESOLVED",
    )
    row["QA_Flags"] = flags_text(policy, {"DATA_QUALITY_FAIL"})
    return row


def normalize_v38(
    current: dict[str, str],
    evidence: dict[str, str],
    history: dict[str, str] | None,
    session_count: int,
    fx_coverage: dict[str, dict[str, str]],
    fx_daily_currencies: set[str],
    key_fn,
    policy: dict,
) -> dict[str, str]:
    row = base_row(current, key_fn, policy)
    flags = {"LEGACY_NORMALIZED"}
    usable = int_value(evidence.get("Usable_Sessions20"))
    median = decimal_value(evidence.get("MedianTurnover20_EUR"))
    currency = clean(evidence.get("Currency_Normalized") or evidence.get("Primary_Currency") or row["Price_Currency"]).upper()
    row["Price_Currency"] = currency
    row["Usable_Session_Count"] = "" if usable is None else str(usable)
    row["Zero_Volume_Share"] = clean((history or {}).get("Zero_Volume_Share"))
    row["Last_Liquidity_Observation_Date"] = clean(evidence.get("Liquidity_Last_Session"))
    row["Source_AsOf"] = clean(evidence.get("Evidence_AsOf"))
    row["Retrieved_At"] = clean((history or {}).get("Fetch_Timestamp_UTC"))
    row["Source_ID"] = "LIQUIDITY_V0_38"
    row["Evidence_Artifact"] = "output_current_master_research_partial_1633_data_refresh_v0_38/liquidity_current_1633_v0.38.csv"

    if currency == "EUR":
        row["FX_Evidence_Status"] = "FX_IDENTITY_EUR"
    else:
        cover = fx_coverage.get(currency)
        fx_summary_ok = (
            clean(evidence.get("FX_Status")) == "FX_RESOLVED"
            and cover is not None
            and clean(cover.get("FX_Status")) == "FX_RESOLVED"
            and currency in fx_daily_currencies
        )
        if fx_summary_ok and session_count >= int(policy["thresholds"]["minimum_usable_sessions"]):
            row["FX_Evidence_Status"] = "FX_OK"
        elif fx_summary_ok and median is not None:
            row["FX_Evidence_Status"] = "FX_PARTIAL"
            flags.add("FX_EVIDENCE_PARTIAL")
        else:
            row["FX_Evidence_Status"] = "FX_UNAVAILABLE"

    if usable is not None and usable >= int(policy["thresholds"]["minimum_usable_sessions"]):
        if session_count < usable:
            flags.add("MISSING_SESSION_EVIDENCE")
            if row["FX_Evidence_Status"] == "FX_OK" and currency != "EUR":
                row["FX_Evidence_Status"] = "FX_PARTIAL"
                flags.add("FX_EVIDENCE_PARTIAL")
        if row["Last_Liquidity_Observation_Date"] and row["Source_AsOf"] and row["Last_Liquidity_Observation_Date"] == row["Source_AsOf"]:
            row["Liquidity_Currentness_Status"] = "CURRENT"
        else:
            row["Liquidity_Currentness_Status"] = "UNKNOWN"
            flags.add("MISSING_CURRENTNESS_METADATA")
    else:
        row["Liquidity_Currentness_Status"] = "UNAVAILABLE"

    explicit_stale = clean(evidence.get("Liquidity_Current_State")) == "LIQUIDITY_STALE"
    return finalize_measured(
        row,
        policy,
        flags,
        usable,
        median,
        legacy_v38_bucket(clean(evidence.get("Liquidity_Current_State"))),
        explicit_stale,
    )


def normalize_v48(
    current: dict[str, str],
    evidence: dict[str, str],
    summary: dict,
    key_fn,
    policy: dict,
) -> dict[str, str]:
    row = base_row(current, key_fn, policy)
    flags = {"LEGACY_NORMALIZED", "MISSING_SESSION_EVIDENCE", "MISSING_CURRENTNESS_METADATA"}
    usable = int_value(evidence.get("Usable20"))
    median = decimal_value(evidence.get("MedianTurnover20_EUR"))
    currency = clean(evidence.get("Primary_Currency") or row["Price_Currency"]).upper()
    row.update(
        Price_Currency=currency,
        Usable_Session_Count="" if usable is None else str(usable),
        Zero_Volume_Share="",
        Last_Liquidity_Observation_Date=clean(evidence.get("Last_Session")),
        Liquidity_Currentness_Status="UNKNOWN" if usable is not None and usable >= int(policy["thresholds"]["minimum_usable_sessions"]) else "UNAVAILABLE",
        Source_ID="LIQUIDITY_V0_48",
        Evidence_Artifact="output_liquidity_fx_sidecar_236_v0_48/liquidity_236_v0.48.csv",
        Source_AsOf="",
        Retrieved_At=clean(summary.get("as_of_utc")),
    )
    if currency == "EUR" and clean(evidence.get("FX_Status")) == "IDENTITY":
        row["FX_Evidence_Status"] = "FX_IDENTITY_EUR"
    elif currency != "EUR" and clean(evidence.get("FX_Status")) == "RESOLVED" and median is not None:
        row["FX_Evidence_Status"] = "FX_PARTIAL"
        flags.add("FX_EVIDENCE_PARTIAL")
    else:
        row["FX_Evidence_Status"] = "FX_UNAVAILABLE"
    return finalize_measured(
        row,
        policy,
        flags,
        usable,
        median,
        legacy_v48_bucket(clean(evidence.get("Liquidity_Class"))),
    )


def bridge_index(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], set[str]]:
    result: dict[str, dict[str, str]] = {}
    duplicates: set[str] = set()
    for row in rows:
        new_ws = clean(row.get("New_WS_ID"))
        if not new_ws:
            continue
        if new_ws in result:
            duplicates.add(new_ws)
        else:
            result[new_ws] = row
    return result, duplicates


def normalize_us1(
    current: dict[str, str],
    bridge: dict[str, str] | None,
    duplicate_bridge: bool,
    evidence_by_legacy: dict[str, dict[str, str]],
    summary: dict,
    key_fn,
    policy: dict,
) -> dict[str, str]:
    current_ws = clean(current.get("WS_ID"))
    if duplicate_bridge:
        legacy = clean((bridge or {}).get("WS_ID"))
        return conflict_row(current, key_fn, policy, legacy)
    if bridge is None:
        row = base_row(current, key_fn, policy)
        row.update(
            Liquidity_Status="LIQUIDITY_IDENTITY_UNRESOLVED",
            FX_Evidence_Status="FX_UNAVAILABLE",
            Liquidity_Currentness_Status="UNAVAILABLE",
            Source_ID="US1_LIQUIDITY_QA",
            Evidence_Artifact="output_us1_write/dry_run_write_plan.csv",
            QA_Confidence="UNRESOLVED",
        )
        row["QA_Flags"] = flags_text(policy, {"IDENTITY_UNRESOLVED", "MISSING_CURRENTNESS_METADATA"})
        return row

    legacy_ws = clean(bridge.get("WS_ID"))
    identity_ok = clean(bridge.get("New_WS_ID")) == current_ws and all(
        clean(bridge.get(field)) == clean(current.get(field))
        for field in ("ISIN", "Primary_MIC", "Primary_Ticker")
    )
    if not identity_ok:
        return conflict_row(current, key_fn, policy, legacy_ws)

    evidence = evidence_by_legacy.get(legacy_ws)
    if evidence is None:
        row = base_row(current, key_fn, policy)
        flags = {"MISSING_LIQUIDITY_EVIDENCE", "MISSING_CURRENTNESS_METADATA"}
        row.update(
            Evidence_Source_WS_ID=legacy_ws,
            Liquidity_Status="LIQUIDITY_UNAVAILABLE",
            FX_Evidence_Status="FX_UNAVAILABLE",
            Liquidity_Currentness_Status="UNAVAILABLE",
            Source_ID="US1_LIQUIDITY_QA",
            Evidence_Artifact="output_us1/liquidity_us1.csv",
            Retrieved_At=clean(summary.get("source_as_of_utc")),
            QA_Confidence="UNRESOLVED",
        )
        row["QA_Flags"] = flags_text(policy, flags)
        return row

    row = base_row(current, key_fn, policy)
    flags = {
        "LEGACY_NORMALIZED",
        "MISSING_SESSION_EVIDENCE",
        "MISSING_CURRENTNESS_METADATA",
        "FX_EVIDENCE_PARTIAL",
    }
    usable = int_value(evidence.get("Usable20"))
    median = decimal_value(evidence.get("MedianTurnover20_EUR"))
    row.update(
        Evidence_Source_WS_ID=legacy_ws,
        Price_Currency="USD",
        Usable_Session_Count="" if usable is None else str(usable),
        Zero_Volume_Share="",
        FX_Evidence_Status="FX_PARTIAL",
        Last_Liquidity_Observation_Date="",
        Liquidity_Currentness_Status="UNKNOWN" if usable is not None and usable >= int(policy["thresholds"]["minimum_usable_sessions"]) else "UNAVAILABLE",
        Source_ID="US1_LIQUIDITY_QA",
        Evidence_Artifact="output_us1/liquidity_us1.csv",
        Source_AsOf="",
        Retrieved_At=clean(summary.get("source_as_of_utc")),
    )
    return finalize_measured(
        row,
        policy,
        flags,
        usable,
        median,
        legacy_us1_bucket(clean(evidence.get("Liquidity_Class"))),
    )


def build_rows() -> list[dict[str, str]]:
    policy = read_json(POLICY)
    if policy.get("policy_version") != "WELT-SWING-LIQUIDITY-QA-v1.0":
        raise ValueError("unexpected Liquidity QA policy version")
    key_fn = mapping_security_key()

    current = read_csv(
        SOURCE,
        ["WS_ID", "ISIN", "Primary_MIC", "Primary_Ticker", "Primary_Currency", "Source_ID", "Active"],
    )
    if len(current) != EXPECTED_TOTAL:
        raise ValueError(f"Research Partial count {len(current)} != {EXPECTED_TOTAL}")
    current_index = index_unique(current, "WS_ID", "current Research Partial")

    source_counts = Counter(clean(row.get("Source_ID")) for row in current)
    if source_counts[US1_SOURCE_ID] != EXPECTED_US1:
        raise ValueError("US1 current cohort count mismatch")
    if source_counts[US2_SOURCE_ID] != EXPECTED_US2:
        raise ValueError("US2 current cohort count mismatch")
    if source_counts[AU1_SOURCE_ID] != EXPECTED_AU1:
        raise ValueError("AU1 current cohort count mismatch")
    original_count = EXPECTED_TOTAL - source_counts[US1_SOURCE_ID] - source_counts[US2_SOURCE_ID] - source_counts[AU1_SOURCE_ID]
    if original_count != EXPECTED_ORIGINAL:
        raise ValueError("original cohort count mismatch")

    l38_rows = read_csv(
        L38,
        [
            "WS_ID", "Primary_Currency", "Currency_Normalized", "Liquidity_Last_Session",
            "Usable_Sessions20", "FX_Coverage20", "MedianTurnover20_EUR",
            "Liquidity_Current_State", "FX_Status", "Evidence_AsOf",
        ],
    )
    l38 = index_unique(l38_rows, "WS_ID", "v0.38 liquidity")
    if len(l38) != EXPECTED_ORIGINAL:
        raise ValueError("v0.38 liquidity row count mismatch")

    h38_rows = read_csv(H38, ["WS_ID", "Zero_Volume_Share", "Fetch_Timestamp_UTC"])
    h38 = index_unique(h38_rows, "WS_ID", "v0.38 history support")
    if len(h38) != EXPECTED_ORIGINAL:
        raise ValueError("v0.38 history support row count mismatch")

    session_rows = read_optional_csv(S38, ["WS_ID"])
    session_count = Counter(clean(row.get("WS_ID")) for row in session_rows if clean(row.get("WS_ID")))

    fx_coverage_rows = read_csv(FX38, ["Currency_Normalized", "FX_Status"])
    fx_coverage = index_unique(fx_coverage_rows, "Currency_Normalized", "v0.38 FX coverage")
    fx_daily_rows = read_csv(FXD38, ["Currency_Normalized", "FX_Date", "FX_to_EUR"])
    fx_daily_currencies = {clean(row.get("Currency_Normalized")) for row in fx_daily_rows}
    summary38 = read_json(SUM38)
    if int(summary38.get("current_master_rows", -1)) != EXPECTED_ORIGINAL:
        raise ValueError("v0.38 summary population mismatch")

    l48_rows = read_csv(
        L48,
        ["WS_ID", "Primary_Currency", "Usable20", "MedianTurnover20_EUR", "Liquidity_Class", "FX_Status", "Last_Session"],
    )
    l48 = index_unique(l48_rows, "WS_ID", "v0.48 liquidity")
    summary48 = read_json(SUM48)
    if len(l48) != int(summary48.get("sidecar_rows", -1)) or len(l48) != 236:
        raise ValueError("v0.48 sidecar count mismatch")
    if set(l48) - set(l38):
        raise ValueError("v0.48 contains non-original WS_ID")

    us1_rows = read_csv(US1, ["WS_ID", "Liquidity_Class", "MedianTurnover20_EUR", "Usable20", "FX"])
    us1 = index_unique(us1_rows, "WS_ID", "US1 liquidity")
    us1_summary = read_json(US1_SUM)
    bridge_rows = read_csv(US1_BRIDGE, ["WS_ID", "ISIN", "Primary_MIC", "Primary_Ticker", "New_WS_ID"])
    bridge, duplicate_bridge = bridge_index(bridge_rows)

    output: list[dict[str, str]] = []
    for current_row in current:
        ws_id = clean(current_row.get("WS_ID"))
        source_id = clean(current_row.get("Source_ID"))
        if source_id == US2_SOURCE_ID:
            row = unsupported_row(current_row, key_fn, policy, au1=False)
        elif source_id == AU1_SOURCE_ID:
            row = unsupported_row(current_row, key_fn, policy, au1=True)
        elif source_id == US1_SOURCE_ID:
            row = normalize_us1(
                current_row,
                bridge.get(ws_id),
                ws_id in duplicate_bridge,
                us1,
                us1_summary,
                key_fn,
                policy,
            )
        else:
            if ws_id not in l38:
                raise ValueError(f"original cohort missing v0.38 liquidity evidence: {ws_id}")
            if ws_id in l48:
                row = normalize_v48(current_row, l48[ws_id], summary48, key_fn, policy)
            else:
                row = normalize_v38(
                    current_row,
                    l38[ws_id],
                    h38.get(ws_id),
                    session_count.get(ws_id, 0),
                    fx_coverage,
                    fx_daily_currencies,
                    key_fn,
                    policy,
                )
        output.append(row)

    current_ws = [clean(row.get("WS_ID")) for row in current]
    output_ws = [row["Source_WS_ID"] for row in output]
    keys = [row["Security_Key"] for row in output]
    if len(output) != EXPECTED_TOTAL or output_ws != current_ws:
        raise ValueError("population/order invariant failed")
    if len(set(output_ws)) != EXPECTED_TOTAL or len(set(keys)) != EXPECTED_TOTAL:
        raise ValueError("output key uniqueness invariant failed")
    expected_keys = [key_fn(ws_id) for ws_id in current_ws]
    if keys != expected_keys:
        raise ValueError("Security_Key mapping authority mismatch")

    unsupported = [row for row in output if "MISSING_LIQUIDITY_EVIDENCE" in set(filter(None, row["QA_Flags"].split("|")))]
    if len(unsupported) != EXPECTED_UNSUPPORTED:
        raise ValueError(f"unsupported liquidity cohort {len(unsupported)} != {EXPECTED_UNSUPPORTED}")
    return output


def generate_bytes() -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(build_rows())
    return buffer.getvalue().encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    data = generate_bytes()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"rows={EXPECTED_TOTAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
