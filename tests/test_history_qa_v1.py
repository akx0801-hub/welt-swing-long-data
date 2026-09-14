#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

GENERATOR_PATH = SCRIPTS / "generate_history_qa_v1.py"
SOURCE_PATH = ROOT / "universe/research_partial_1633.csv"
POLICY_PATH = ROOT / "config/history_qa_v1_policy.json"
STRICT_SUMMARY_PATH = ROOT / "output_p4_audit_759/summary_p4.json"

EXPECTED_TOTAL = 2527
EXPECTED_EVIDENCE_BACKED = 2005
EXPECTED_NO_HISTORY = 522
EXPECTED_US2 = 369
EXPECTED_AU1 = 153

MISSING_MEASUREMENTS = [
    "History_Start",
    "History_End",
    "History_Observation_Count",
    "History_Valid_Observation_Count",
    "Expected_Session_Count",
    "Usable_Session_Count",
    "Gap_Count",
    "Gap_Share",
    "Zero_Volume_Share",
    "Last_Observation_Date",
]


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_history_qa_v1", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load History QA v1 generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HistoryQAV1Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.source_before = SOURCE_PATH.read_bytes()
        cls.source_fields, cls.source_rows = read_csv(SOURCE_PATH)

        run1_env = os.environ.get("HISTORY_QA_V1_OUTPUT", "")
        run2_env = os.environ.get("HISTORY_QA_V1_SECOND_OUTPUT", "")
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

    @classmethod
    def tearDownClass(cls) -> None:
        if SOURCE_PATH.read_bytes() != cls.source_before:
            raise AssertionError("current Research Partial was modified during validation")
        if cls.tempdir is not None:
            cls.tempdir.cleanup()

    def test_output_schema_exact(self) -> None:
        self.assertEqual(self.fields1, self.generator.F)
        self.assertEqual(self.fields2, self.generator.F)

    def test_population_and_current_security_identity_exact(self) -> None:
        self.assertEqual(len(self.source_rows), EXPECTED_TOTAL)
        self.assertEqual(len(self.rows1), EXPECTED_TOTAL)
        self.assertEqual(len(self.rows2), EXPECTED_TOTAL)

        current_ws = [(row.get("WS_ID") or "").strip() for row in self.source_rows]
        output_ws = [row["Source_WS_ID"] for row in self.rows1]
        self.assertEqual(output_ws, current_ws)
        self.assertEqual(len(set(output_ws)), EXPECTED_TOTAL)

        security_key = self.generator.skfn()
        expected_keys = [security_key(ws_id) for ws_id in current_ws]
        actual_keys = [row["Security_Key"] for row in self.rows1]
        self.assertEqual(actual_keys, expected_keys)
        self.assertEqual(len(set(actual_keys)), EXPECTED_TOTAL)

    def test_expected_partial_coverage_fail_closed(self) -> None:
        missing_flag = "MISSING_HISTORY_EVIDENCE"
        no_history = [
            row for row in self.rows1 if missing_flag in set(filter(None, row["QA_Flags"].split("|")))
        ]
        evidence_backed = [
            row for row in self.rows1 if missing_flag not in set(filter(None, row["QA_Flags"].split("|")))
        ]
        self.assertEqual(len(evidence_backed), EXPECTED_EVIDENCE_BACKED)
        self.assertEqual(len(no_history), EXPECTED_NO_HISTORY)

        us2 = [row for row in no_history if row["Source_ID"] == "US2_SP400_COMMON_ADMISSION"]
        au1 = [row for row in no_history if row["Source_ID"] == "AU1_EVIDENCE_ADMISSION_GATE"]
        self.assertEqual(len(us2), EXPECTED_US2)
        self.assertEqual(len(au1), EXPECTED_AU1)
        self.assertEqual(len(us2) + len(au1), EXPECTED_NO_HISTORY)

        for row in no_history:
            flags = set(filter(None, row["QA_Flags"].split("|")))
            self.assertEqual(row["History_Status"], "HISTORY_UNAVAILABLE")
            self.assertEqual(row["History_Currentness_Status"], "UNAVAILABLE")
            self.assertEqual(row["QA_Confidence"], "UNRESOLVED")
            self.assertIn("MISSING_CURRENTNESS_METADATA", flags)
            self.assertNotEqual(row["History_Status"], "HISTORY_OK")
            for field in MISSING_MEASUREMENTS:
                self.assertEqual(row[field], "", f"{row['Source_WS_ID']} {field}")

    def test_vocabularies_policy_and_flags(self) -> None:
        allowed_status = set(self.policy["history_status_vocabulary"])
        allowed_currentness = set(self.policy["currentness_vocabulary"])
        allowed_adjustment = set(self.policy["adjustment_vocabulary"])
        allowed_confidence = set(self.policy["confidence_vocabulary"])
        allowed_flags = set(self.policy["allowed_qa_flags"])
        for row in self.rows1:
            self.assertIn(row["History_Status"], allowed_status)
            self.assertIn(row["History_Currentness_Status"], allowed_currentness)
            self.assertIn(row["Adjustment_Integrity_Status"], allowed_adjustment)
            self.assertIn(row["QA_Confidence"], allowed_confidence)
            self.assertEqual(row["History_Policy_Version"], self.policy["policy_version"])
            self.assertTrue(set(filter(None, row["QA_Flags"].split("|"))) <= allowed_flags)

    def test_strict_frozen_and_membership_governance(self) -> None:
        summary = json.loads(STRICT_SUMMARY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(summary["strict"], 759)
        self.assertEqual(summary["u3k_frozen_members"], 0)
        self.assertFalse(summary["universe_write"])
        self.assertEqual(len(self.source_rows), EXPECTED_TOTAL)

    def test_repeated_generation_is_byte_and_sha_identical(self) -> None:
        self.assertEqual(self.run1.read_bytes(), self.run2.read_bytes())
        self.assertEqual(sha256(self.run1), sha256(self.run2))

    def test_source_conflict_helper_fails_closed(self) -> None:
        primary = {"Unique_Bars": "260", "Last_Bar": "2026-09-04"}
        support_same = {"Unique_Daily_Bars": "260", "Last_Completed_Bar": "2026-09-04"}
        support_conflict = {"Unique_Daily_Bars": "259", "Last_Completed_Bar": "2026-09-04"}
        pairs = [("Unique_Bars", "Unique_Daily_Bars"), ("Last_Bar", "Last_Completed_Bar")]
        self.assertFalse(self.generator.mat(primary, support_same, pairs))
        self.assertTrue(self.generator.mat(primary, support_conflict, pairs))
        chosen = self.generator.prec(
            self.policy,
            {"HISTORY_CONFLICT", "HISTORY_OK"},
        )
        self.assertEqual(chosen, "HISTORY_CONFLICT")


if __name__ == "__main__":
    unittest.main()
