#!/usr/bin/env python3
"""v0.36 offline source-access governance decision; no network access."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output_current_master_source_governance_v0_36"
MASTER = ROOT / "universe/Welt-Swing-Universe-Master-v2.0.xlsx"
RESEARCH = ROOT / "universe/research_partial_1633.csv"
MANIFEST = ROOT / "universe/research_partial_1633_manifest.json"
SEGMENTS = ("US_SP1500", "MX_IPC", "KR_KOSPI200", "AU_ASX200", "NZ_NZX50", "ZA_TOP40")
IMPORTED = ("EU_STOXX600", "CA_TSX", "JP_N225", "HK_HSI", "CN_CSI300", "IN_NIFTY50", "TW_TW50", "BR_IBRX100")
GOVERNANCE = {
    "US_SP1500": ("OFFICIAL_FULL_SOURCE_BROWSER_VISIBLE_RUNNER_BLOCKED", "CLOUD_BROWSER_VISIBLE", "RUNNER_HTTP_403", "Official S&P full-constituents UI was visible; the runner received HTTP 403."),
    "MX_IPC": ("OFFICIAL_CHANGE_DOCUMENTS_ONLY", "OFFICIAL_DOCUMENT_VISIBLE", "RUNNER_HTTP_200_CHANGE_DOCUMENT", "March 2026 official BMV PDF records VOLAR A ADD and CUERVO * DROP, not a full constituent list."),
    "KR_KOSPI200": ("OFFICIAL_SOURCE_FOUND_DATA_ENDPOINT_NOT_RESOLVED", "OFFICIAL_PLATFORM_REACHABLE", "OFFICIAL_API_CANDIDATE_TESTED", "Official KRX endpoint was found and tested; a complete anonymous request was not evidenced."),
    "AU_ASX200": ("OFFICIAL_FULL_SOURCE_BROWSER_VISIBLE_RUNNER_BLOCKED", "CLOUD_BROWSER_VISIBLE", "RUNNER_HTTP_403", "Official S&P full-constituents UI was visible; the runner received HTTP 403."),
    "NZ_NZX50": ("OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED", "OFFICIAL_ROUTE_REACHABLE", "SUBSCRIPTION_EVIDENCE_TRUE", "No public full-membership export materialized; subscription evidence is recorded."),
    "ZA_TOP40": ("OFFICIAL_ROUTE_HTTP_BLOCKED", "OFFICIAL_ROUTE_DISCOVERED", "RUNNER_HTTP_403", "JSE landing route and historical 2024 review route were blocked; no current full asset materialized."),
}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()

def write_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def column_number(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    value = 0
    for char in letters:
        value = value * 26 + ord(char) - 64
    return value - 1

def workbook_rows() -> list[dict]:
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "p": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(MASTER) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(node.text or "" for node in item.iter("{%s}t" % ns["m"])) for item in root.findall("m:si", ns)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_id = next(sheet.attrib["{%s}id" % ns["r"]] for sheet in workbook.findall("m:sheets/m:sheet", ns) if sheet.attrib["name"] == "Universe_Master")
        target = next(rel.attrib["Target"] for rel in relations.findall("p:Relationship", ns) if rel.attrib["Id"] == rel_id).lstrip("/")
        target = target if target.startswith("xl/") else "xl/" + target
        worksheet = ET.fromstring(archive.read(target))
        values = []
        for row in worksheet.findall("m:sheetData/m:row", ns):
            cells = {}
            for cell in row.findall("m:c", ns):
                raw = cell.find("m:v", ns)
                if cell.attrib.get("t") == "inlineStr":
                    value = "".join(node.text or "" for node in cell.iter("{%s}t" % ns["m"]))
                elif raw is None:
                    value = ""
                else:
                    value = strings[int(raw.text)] if cell.attrib.get("t") == "s" else raw.text
                cells[column_number(cell.attrib.get("r", "A1"))] = value
            if cells:
                values.append([cells.get(index, "") for index in range(max(cells) + 1)])
    headers = values[0]
    return [dict(zip(headers, row + [""] * max(0, len(headers) - len(row)))) for row in values[1:] if any(row)]

def segment_counts(rows: list[dict]) -> dict[str, int]:
    aliases = {
        "EU_STOXX600": ("EU_STOXX600", "STOXX EUROPE 600", "STOXX 600"),
        "CA_TSX": ("CA_TSX", "S&P/TSX", "SP/TSX", "TSX COMPOSITE"),
        "JP_N225": ("JP_N225", "NIKKEI 225", "N225"),
        "HK_HSI": ("HK_HSI", "HANG SENG", "HSI"),
        "CN_CSI300": ("CN_CSI300", "CSI 300", "CSI300"),
        "IN_NIFTY50": ("IN_NIFTY50", "NIFTY 50", "NIFTY50"),
        "TW_TW50": ("TW_TW50", "TAIWAN 50", "TW50"),
        "BR_IBRX100": ("BR_IBRX100", "IBRX 100", "IBRX100"),
    }
    counts = {segment: 0 for segment in IMPORTED}
    unresolved = 0
    for row in rows:
        payload = " | ".join(str(value).upper() for value in row.values())
        matches = [segment for segment, tokens in aliases.items() if any(token in payload for token in tokens)]
        if len(matches) == 1:
            counts[matches[0]] += 1
        else:
            unresolved += 1
    if unresolved or not all(counts.values()) or sum(counts.values()) != len(rows):
        raise RuntimeError(f"master segment mapping unresolved={unresolved}; counts={counts}")
    return counts
def frozen_audit(config: dict) -> list[dict]:
    audit = []
    capture = bool(config.get("allow_initial_blob_capture", False))
    for item in config["frozen_inputs"]:
        path = ROOT / item["path"]
        expected = item.get("blob_sha", "")
        actual = git_blob(path)
        passed = bool(expected) and expected == actual
        if not passed and not capture:
            raise RuntimeError("frozen input blob mismatch or missing pin: " + item["path"])
        audit.append({"Path": item["path"], "Expected_Blob_SHA": expected, "Actual_Blob_SHA": actual, "PASS": passed, "Initial_Capture_Only": capture and not bool(expected)})
    return audit

def self_test() -> None:
    assert len(SEGMENTS) == 6 and len(IMPORTED) == 8
    assert not set(SEGMENTS).intersection(IMPORTED)
    assert GOVERNANCE["MX_IPC"][0] == "OFFICIAL_CHANGE_DOCUMENTS_ONLY"
    assert all(state.startswith("OFFICIAL_") for state, _, _, _ in GOVERNANCE.values())

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/current_master_source_access_governance_decision_v0.36.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print("v0.36 self-test PASS")
        return
    config = json.loads((ROOT / args.config).read_text(encoding="utf-8"))
    if config.get("network_access") is not False:
        raise RuntimeError("v0.36 must not permit network access")
    before_master, before_research, before_manifest = digest(MASTER), digest(RESEARCH), digest(MANIFEST)
    audit = frozen_audit(config)
    rows = workbook_rows()
    if len(rows) != 1633:
        raise RuntimeError(f"Current Master rows must be 1633, got {len(rows)}")
    counts = segment_counts(rows)
    imported = [{"Segment_ID": segment, "Current_Master_Row_Count": counts[segment], "Imported": True} for segment in IMPORTED]
    if sum(item["Current_Master_Row_Count"] for item in imported) != 1633:
        raise RuntimeError("imported segment counts do not reconcile to 1633")
    register = []
    for segment in SEGMENTS:
        state, browser, runner, note = GOVERNANCE[segment]
        register.append({
            "Segment_ID": segment, "Governance_State_v0_36": state, "Evidence_Source_Stage": "v0.35-r3",
            "Browser_Status": browser, "Runner_Status": runner, "Full_Membership_Materialized": False,
            "Materialized_Rows": 0, "Canonical_Import": False, "Fallback_Allowed": False,
            "Remediation_Status": "DEFERRED_UNTIL_EXTERNAL_ACCESS_CHANGE",
            "Reopen_Trigger": "new free official full-membership route; documented official API/download route; auth or subscription change; legitimate licensed access; official platform change; explicit manual governance recheck; later productive-promotion preparation",
            "Notes": note,
        })
    write_csv("remaining_segment_governance_register_v0.36.csv", register, list(register[0]))
    decision_rows = []
    for ident, rationale, evidence, impact in [
        ("OFFICIAL_SOURCE_GATE_RETAINED", "Official full-membership evidence remains mandatory.", "v0.35-r3 frozen evidence", "No substitute import."),
        ("THIRD_PARTY_FALLBACK_REJECTED", "Wikipedia, ETF holdings, screeners and unofficial lists remain prohibited.", "Master specification", "Fallback blocked."),
        ("LEGACY_PHASE2_MEMBERSHIP_NOT_CANONICAL", "Legacy phase2 membership cannot substitute official current evidence.", "Master specification", "No canonical import."),
        ("FULL_SCAN_NOT_ALLOWED", "Six target segments remain blocked.", "Governance register", "FULL_SCAN_ALLOWED=false."),
        ("RESEARCH_PARTIAL_CONTINUATION_ALLOWED", "Transparent 8/14 universe is allowed only for DEV research.", "Master specification", "RESEARCH_PARTIAL_ALLOWED=true."),
        ("CURRENT_MASTER_1633_RETAINED", "No source materialization or import occurs in v0.36.", "Immutability audit", "1633 retained."),
        ("MISSING_SEGMENTS_DEFERRED", "Retry only after explicit external-access-change evidence.", "Governance register", "Automatic retry=false."),
        ("GLOBAL_U3K_FREEZE_NOT_ALLOWED", "Global source superset is incomplete.", "Master specification", "No global freeze."),
        ("P0_NOT_RUN_IN_V0_36", "This is an offline governance stage.", "Stage configuration", "P0=false."),
        ("PRODUCTIVE_PROMOTION_NOT_ALLOWED", "Research-partial has no productive authority.", "Master specification", "productive=false."),
    ]:
        decision_rows.append({"Decision_ID": ident, "Decision": ident, "State": True, "Rationale": rationale, "Evidence": evidence, "Impact": impact})
    write_csv("source_access_governance_decision_matrix_v0.36.csv", decision_rows, list(decision_rows[0]))
    reopen = [{"Segment_ID": row["Segment_ID"], "Current_Governance_State": row["Governance_State_v0_36"], "Remediation_Status": row["Remediation_Status"], "Reopen_Trigger": row["Reopen_Trigger"], "Automatic_Retry": False, "Required_Evidence_For_Reopen": "current official reproducible full-membership route or legitimate documented access change"} for row in register]
    write_csv("source_reopen_trigger_register_v0.36.csv", reopen, list(reopen[0]))
    write_csv("current_master_imported_segment_inventory_v0.36.csv", imported, list(imported[0]))
    write_csv("frozen_input_audit_v0.36.csv", audit, list(audit[0]))
    scope = {"current_master_rows": 1633, "research_partial_rows": 1633, "imported_segments": 8, "missing_segments": 6, "imported_segment_counts": {row["Segment_ID"]: row["Current_Master_Row_Count"] for row in imported}, "segment_coverage_numerator": 8, "segment_coverage_denominator": 14, "source_superset_complete": False, "full_scan_allowed": False, "research_partial_allowed": True, "p0_run_v0_36": False, "swing_u3k_frozen": False, "productive": False, "alpha_vantage": False}
    (OUT / "research_partial_operating_scope_v0.36.json").write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
    if (digest(MASTER), digest(RESEARCH), digest(MANIFEST)) != (before_master, before_research, before_manifest):
        raise RuntimeError("immutable canonical input changed")
    common = {"stage": "CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION", "version": "v0.36", "status": "DEV / RESEARCH / SHADOW – NOT PRODUCTIVE", **scope, "canonical_master_import_v0_36": False, "universe_mutated_v0_36": False, "eligibility_promotion_v0_36": False, "sector_rs": False, "next_stage": "CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN", "frozen_input_audit": audit}
    for name in ("summary_v0.36.json", "stage_checkpoint_v0.36.json", "manifest_v0.36.json"):
        (OUT / name).write_text(json.dumps(common, indent=2) + "\n", encoding="utf-8")
    handoff = ["# WELT-SWING CURRENT HANDOFF v0.36", "", "Current Master = 1633", "Operating Mode = RESEARCH_PARTIAL", "Imported = 8/14", "Missing = 6/14", "Missing segments deferred until external access change", "No third-party fallback authorization", "FULL_SCAN_ALLOWED = false", "RESEARCH_PARTIAL_ALLOWED = true", "Source Superset Complete = false", "P0 = false", "SWING_U3K_FROZEN = false", "Productive = false", "Alpha Vantage = false", "", "## Missing segment governance states"]
    handoff += [f"- {row['Segment_ID']}: {row['Governance_State_v0_36']} (materialized rows 0)" for row in register]
    handoff += ["", "Recovery Order: v0.36 governance complete; reopen only after documented external-access change.", "Next Stage: CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN", ""]
    text = "\n".join(handoff)
    for name in ("WELT-SWING-CURRENT-Handoff-v0.36.md", "WELT-SWING-CURRENT-Handoff-CURRENT.md"):
        (ROOT / name).write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
