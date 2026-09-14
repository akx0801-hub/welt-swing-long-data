#!/usr/bin/env python3
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts/generate_liquidity_qa_v1.py"
SOURCE_PATH = ROOT / "universe/research_partial_1633.csv"
POLICY_PATH = ROOT / "config/liquidity_qa_v1_policy.json"
STRICT_SUMMARY_PATH = ROOT / "output_p4_audit_759/summary_p4.json"
FROZEN_PATH = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"

EXPECTED_TOTAL = 2527
EXPECTED_ORIGINAL = 1633
EXPECTED_US1 = 372
EXPECTED_US2 = 369
EXPECTED_AU1 = 153
EXPECTED_UNSUPPORTED = 522

US1_SOURCE_ID = "US1_SP500_COMMON_EVIDENCE_GATE"
US2_SOURCE_ID = "US2_SP400_COMMON_ADMISSION"
AU1_SOURCE_ID = "AU1_EVIDENCE_ADMISSION_GATE"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_liquidity_qa_v1", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Liquidity QA v1 generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flags(row: dict[str, str]) -> set[str]:
    return set(filter(None, row["QA_Flags"].split("|")))


class LiquidityQAV1Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.source_before = SOURCE_PATH.read_bytes()
        cls.source_fields, cls.source_rows = read_csv(SOURCE_PATH)

        run1_env = os.environ.get("LIQUIDITY_QA_V1_OUTPUT", "")
        run2_env = os.environ.get("LIQUIDITY_QA_V1_SECOND_OUTPUT", "")
        if run1_env and run2_env:
            cls.run1 = Path(run1_env)
            cls.run2 = Path(run2_env)
            cls.tempdir = None
        else:
            cls.tempdir = tempfile.TemporaryDirectory()
            cls.run1 = Path(cls.tempdir.name) / "run1.csv"
            cls.run2 = Path(cls.tempdir.name) / "run2.csv"
            cls.run1.write_bytes(cls.generator.generate_bytes())
            cls.run2.write_bytes(cls.generator.generate_bytes())

        cls.fields1, cls.rows1 = read_csv(cls.run1)
        cls.fields2, cls.rows2 = read_csv(cls.run2)
        cls.source_by_ws = {row["WS_ID"]: row for row in cls.source_rows}

    @classmethod
    def tearDownClass(cls) -> None:
        if SOURCE_PATH.read_bytes() != cls.source_before:
            raise AssertionError("current Research Partial was modified during validation")
        if cls.tempdir is not None:
            cls.tempdir.cleanup()

    def test_schema_population_order_and_security_keys(self) -> None:
        self.assertEqual(self.fields1, self.generator.FIELDS)
        self.assertEqual(self.fields2, self.generator.FIELDS)
        self.assertEqual(len(self.source_rows), EXPECTED_TOTAL)
        self.assertEqual(len(self.rows1), EXPECTED_TOTAL)
        self.assertEqual(len(self.rows2), EXPECTED_TOTAL)

        source_ws = [(row.get("WS_ID") or "").strip() for row in self.source_rows]
        output_ws = [row["Source_WS_ID"] for row in self.rows1]
        self.assertEqual(output_ws, source_ws)
        self.assertEqual(len(set(output_ws)), EXPECTED_TOTAL)

        security_key = self.generator.mapping_security_key()
        expected_keys = [security_key(ws) for ws in source_ws]
        actual_keys = [row["Security_Key"] for row in self.rows1]
        self.assertEqual(actual_keys, expected_keys)
        self.assertEqual(len(set(actual_keys)), EXPECTED_TOTAL)

    def test_cohort_counts_and_fail_closed_unsupported_522(self) -> None:
        source_counts = {}
        for row in self.source_rows:
            sid = row.get("Source_ID") or ""
            source_counts[sid] = source_counts.get(sid, 0) + 1
        self.assertEqual(source_counts.get(US1_SOURCE_ID, 0), EXPECTED_US1)
        self.assertEqual(source_counts.get(US2_SOURCE_ID, 0), EXPECTED_US2)
        self.assertEqual(source_counts.get(AU1_SOURCE_ID, 0), EXPECTED_AU1)
        self.assertEqual(EXPECTED_TOTAL - EXPECTED_US1 - EXPECTED_US2 - EXPECTED_AU1, EXPECTED_ORIGINAL)

        unsupported = [row for row in self.rows1 if "MISSING_LIQUIDITY_EVIDENCE" in flags(row)]
        self.assertEqual(len(unsupported), EXPECTED_UNSUPPORTED)
        us2 = [row for row in unsupported if self.source_by_ws[row["Source_WS_ID"]]["Source_ID"] == US2_SOURCE_ID]
        au1 = [row for row in unsupported if self.source_by_ws[row["Source_WS_ID"]]["Source_ID"] == AU1_SOURCE_ID]
        self.assertEqual(len(us2), EXPECTED_US2)
        self.assertEqual(len(au1), EXPECTED_AU1)

        blank_fields = [
            "Liquidity_Bucket",
            "Usable_Session_Count",
            "MedianTurnover20_EUR",
            "Zero_Volume_Share",
            "Last_Liquidity_Observation_Date",
        ]
        for row in unsupported:
            self.assertEqual(row["Liquidity_Status"], "LIQUIDITY_UNAVAILABLE")
            self.assertEqual(row["Liquidity_Currentness_Status"], "UNAVAILABLE")
            self.assertEqual(row["QA_Confidence"], "UNRESOLVED")
            self.assertIn("MISSING_CURRENTNESS_METADATA", flags(row))
            self.assertNotIn(row["Liquidity_Status"], {"LIQUIDITY_OK", "LIQUIDITY_THIN", "LIQUIDITY_VERY_THIN"})
            for field in blank_fields:
                self.assertEqual(row[field], "", f"{row['Source_WS_ID']} {field}")
        for row in au1:
            self.assertEqual(row["FX_Evidence_Status"], "FX_UNAVAILABLE")
            self.assertIn("FX_EVIDENCE_MISSING", flags(row))

    def test_threshold_mapping_and_fx_invariants(self) -> None:
        minimum = int(self.policy["thresholds"]["minimum_usable_sessions"])
        valid_fx = {"FX_IDENTITY_EUR", "FX_OK", "FX_PARTIAL"}
        for row in self.rows1:
            usable = None if row["Usable_Session_Count"] == "" else int(row["Usable_Session_Count"])
            median = None if row["MedianTurnover20_EUR"] == "" else Decimal(row["MedianTurnover20_EUR"])
            listing_ok = row["Listing_Resolution_Status"] == "LISTING_RESOLVED"
            if usable is not None and usable < minimum:
                self.assertEqual(row["Liquidity_Status"], "LIQUIDITY_UNAVAILABLE")
                self.assertEqual(row["Liquidity_Bucket"], "")
            if row["FX_Evidence_Status"] == "FX_UNAVAILABLE":
                self.assertEqual(row["MedianTurnover20_EUR"], "")
            if row["FX_Evidence_Status"] == "FX_CONFLICT":
                self.assertEqual(row["Liquidity_Status"], "LIQUIDITY_CONFLICT")
            if row["Price_Currency"] != "EUR" and median is not None:
                self.assertIn(row["FX_Evidence_Status"], {"FX_OK", "FX_PARTIAL"})
            if (
                usable is not None
                and usable >= minimum
                and median is not None
                and row["FX_Evidence_Status"] in valid_fx
                and listing_ok
                and row["Liquidity_Status"] not in {"LIQUIDITY_CONFLICT", "LIQUIDITY_STALE"}
            ):
                bucket, status = self.generator.bucket_for(self.policy, median)
                self.assertEqual(row["Liquidity_Bucket"], bucket)
                self.assertEqual(row["Liquidity_Status"], status)

    def test_vocabularies_policy_flags_and_null_zero_semantics(self) -> None:
        self.assertEqual(self.policy["policy_version"], "WELT-SWING-LIQUIDITY-QA-v1.0")
        statuses = set(self.policy["liquidity_status_vocabulary"])
        buckets = set(self.policy["liquidity_bucket_vocabulary"])
        fx = set(self.policy["fx_status_vocabulary"])
        currentness = set(self.policy["currentness_vocabulary"])
        listing = set(self.policy["listing_status_vocabulary"])
        confidence = set(self.policy["confidence_vocabulary"])
        allowed_flags = set(self.policy["allowed_qa_flags"])
        for row in self.rows1:
            self.assertIn(row["Liquidity_Status"], statuses)
            self.assertTrue(row["Liquidity_Bucket"] == "" or row["Liquidity_Bucket"] in buckets)
            self.assertIn(row["FX_Evidence_Status"], fx)
            self.assertIn(row["Liquidity_Currentness_Status"], currentness)
            self.assertIn(row["Listing_Resolution_Status"], listing)
            self.assertIn(row["QA_Confidence"], confidence)
            self.assertEqual(row["Liquidity_Policy_Version"], self.policy["policy_version"])
            self.assertTrue(flags(row) <= allowed_flags)
            if row["Usable_Session_Count"] == "0":
                self.assertNotEqual(row["Usable_Session_Count"], "")

    def test_us1_bridge_traceability(self) -> None:
        us1 = [row for row in self.rows1 if self.source_by_ws[row["Source_WS_ID"]]["Source_ID"] == US1_SOURCE_ID]
        self.assertEqual(len(us1), EXPECTED_US1)
        for row in us1:
            if row["Liquidity_Status"] not in {"LIQUIDITY_CONFLICT", "LIQUIDITY_IDENTITY_UNRESOLVED"}:
                self.assertTrue(row["Evidence_Source_WS_ID"].startswith("US1:"))
                self.assertEqual(row["Price_Currency"], "USD")
                self.assertEqual(row["FX_Evidence_Status"], "FX_PARTIAL")
                self.assertIn("LEGACY_NORMALIZED", flags(row))
                self.assertIn("MISSING_SESSION_EVIDENCE", flags(row))
                self.assertIn("MISSING_CURRENTNESS_METADATA", flags(row))
                self.assertIn("FX_EVIDENCE_PARTIAL", flags(row))
                self.assertEqual(row["Liquidity_Currentness_Status"], "UNKNOWN")
                self.assertEqual(row["QA_Confidence"], "LOW")

    def test_repeated_generation_is_byte_and_sha_identical(self) -> None:
        self.assertEqual(self.run1.read_bytes(), self.run2.read_bytes())
        self.assertEqual(sha256(self.run1), sha256(self.run2))

    def test_governance_invariants(self) -> None:
        summary = json.loads(STRICT_SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(summary["strict"], 759)
        self.assertEqual(summary["u3k_frozen_members"], 0)
        self.assertFalse(summary["universe_write"])
        _, frozen_rows = read_csv(FROZEN_PATH)
        self.assertEqual(len(frozen_rows), 0)
        self.assertEqual(len(self.source_rows), EXPECTED_TOTAL)

    def test_static_no_provider_or_network_behavior(self) -> None:
        tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"), filename=str(GENERATOR_PATH))
        forbidden_import_roots = {"requests", "httpx", "aiohttp", "urllib", "socket", "ftplib", "yfinance"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(alias.name.split(".")[0], forbidden_import_roots)
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], forbidden_import_roots)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"urlopen"})


if __name__ == "__main__":
    unittest.main()
