from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from provenance_snapshot_p0 import (  # noqa: E402
    SCHEMA_VERSION,
    build_snapshot_id,
    validate_manifest,
    validate_manifest_file,
)


class ProvenanceSnapshotP0Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "universe").mkdir()
        self.artifact = self.root / "universe" / "artifact.json"
        self.artifact.write_text('{"value": 1}\n', encoding="utf-8")
        digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.manifest = {
            "Artifact_ID": "universe/artifact.json",
            "Snapshot_ID": build_snapshot_id("RESEARCH_PARTIAL", "CURRENT_CANONICAL", "2026-08-30", SCHEMA_VERSION),
            "Source_ID": "CURRENT_CANONICAL",
            "Source_Authority": "RESEARCH_ONLY",
            "Source_AsOf": "2026-08-30",
            "Retrieved_At": "2026-08-30T16:09:40.298669+00:00",
            "Content_Hash": digest,
            "Schema_Version": SCHEMA_VERSION,
            "Population_or_Domain": "RESEARCH_PARTIAL",
            "Currentness_Status": "UNKNOWN",
            "Evidence_Strength": "MEDIUM",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def validate(self, manifest=None):
        return validate_manifest(manifest or self.manifest, self.root, allowed_source_ids={"CURRENT_CANONICAL"})

    def test_valid_manifest_passes(self):
        self.assertTrue(self.validate().ok)

    def test_missing_required_field_fails(self):
        item = copy.deepcopy(self.manifest); item.pop("Source_AsOf")
        self.assertEqual(self.validate(item)["reason_code"], "MISSING_FIELD")

    def test_invalid_source_authority_fails(self):
        item = copy.deepcopy(self.manifest); item["Source_Authority"] = "TRUST_ME"
        self.assertEqual(self.validate(item)["reason_code"], "INVALID_ENUM")

    def test_invalid_currentness_fails(self):
        item = copy.deepcopy(self.manifest); item["Currentness_Status"] = "FRESH"
        self.assertEqual(self.validate(item)["reason_code"], "INVALID_ENUM")

    def test_invalid_evidence_strength_fails(self):
        item = copy.deepcopy(self.manifest); item["Evidence_Strength"] = "PERFECT"
        self.assertEqual(self.validate(item)["reason_code"], "INVALID_ENUM")

    def test_invalid_source_asof_fails(self):
        item = copy.deepcopy(self.manifest); item["Source_AsOf"] = "30/08/2026"
        self.assertEqual(self.validate(item)["reason_code"], "INVALID_TIMESTAMP")

    def test_invalid_retrieved_at_fails(self):
        item = copy.deepcopy(self.manifest); item["Retrieved_At"] = "2026-08-30T16:09:40"
        self.assertEqual(self.validate(item)["reason_code"], "INVALID_TIMESTAMP")

    def test_malformed_sha256_fails(self):
        item = copy.deepcopy(self.manifest); item["Content_Hash"] = "abc123"
        self.assertEqual(self.validate(item)["reason_code"], "INVALID_SHA256")

    def test_missing_artifact_fails(self):
        item = copy.deepcopy(self.manifest); item["Artifact_ID"] = "universe/missing.json"
        self.assertEqual(self.validate(item)["reason_code"], "ARTIFACT_NOT_FOUND")

    def test_hash_mismatch_fails(self):
        item = copy.deepcopy(self.manifest); item["Content_Hash"] = "0" * 64
        self.assertEqual(self.validate(item)["reason_code"], "HASH_MISMATCH")

    def test_snapshot_id_deterministic(self):
        a = build_snapshot_id("RESEARCH_PARTIAL", "CURRENT_CANONICAL", "2026-08-30", SCHEMA_VERSION)
        b = build_snapshot_id("RESEARCH_PARTIAL", "CURRENT_CANONICAL", "2026-08-30", SCHEMA_VERSION)
        self.assertEqual(a, b)
        self.assertEqual(a, "WS-PROV-RESEARCH-PARTIAL-CURRENT-CANONICAL-20260830-PROVENANCE-P0-V1")

    def test_invalid_snapshot_id_fails(self):
        item = copy.deepcopy(self.manifest); item["Snapshot_ID"] = "WS-PROV-WRONG"
        self.assertEqual(self.validate(item)["reason_code"], "SNAPSHOT_ID_INVALID")

    def test_invalid_source_reference_fails(self):
        item = copy.deepcopy(self.manifest); item["Source_ID"] = "UNREGISTERED_SOURCE"
        item["Snapshot_ID"] = build_snapshot_id("RESEARCH_PARTIAL", item["Source_ID"], "2026-08-30", SCHEMA_VERSION)
        self.assertEqual(self.validate(item)["reason_code"], "SOURCE_REFERENCE_INVALID")

    def test_active_integration_manifest_passes(self):
        active_artifact = self.root / "universe" / "research_partial_1633_manifest.json"
        active_content = """{\n  \"Alpha_Vantage\": false,\n  \"P0_run\": false,\n  \"brazil_rows\": 98,\n  \"csv_sha256\": \"11e0d3e5a2154d6755ecce1b549adbda21aea3b8b1d5e8889516535cee30d77e\",\n  \"generated_utc\": \"2026-08-30T16:09:40.298669+00:00\",\n  \"imported_segments\": 8,\n  \"missing_segments\": 6,\n  \"news_run\": false,\n  \"price_scan_run\": false,\n  \"productive\": false,\n  \"ranking_run\": false,\n  \"rows\": 1633,\n  \"schema\": \"WELT_SWING_RESEARCH_PARTIAL_MANIFEST_V0_34\",\n  \"scope\": \"RESEARCH_PARTIAL\",\n  \"selection\": \"all current master rows\",\n  \"source_master_path\": \"universe/Welt-Swing-Universe-Master-v2.0.xlsx\",\n  \"source_master_sha256\": \"96d769b0611c05a6f41d5af41cc77d225a98f296f2a79eef3f2fc0b555bc1fdc\",\n  \"universe_complete\": false,\n  \"version\": \"v0.34\"\n}\n"""
        active_artifact.write_text(active_content, encoding="utf-8")
        self.assertEqual(hashlib.sha256(active_artifact.read_bytes()).hexdigest(), "c687a0b066200632268e386d8709a4e0f1d8f1c90acf81e54c4bc39aa926c294")
        sidecar = {
            "Artifact_ID": "universe/research_partial_1633_manifest.json",
            "Snapshot_ID": "WS-PROV-RESEARCH-PARTIAL-CURRENT-CANONICAL-20260830-PROVENANCE-P0-V1",
            "Source_ID": "CURRENT_CANONICAL",
            "Source_Authority": "RESEARCH_ONLY",
            "Source_AsOf": "2026-08-30",
            "Retrieved_At": "2026-08-30T16:09:40.298669+00:00",
            "Content_Hash": "c687a0b066200632268e386d8709a4e0f1d8f1c90acf81e54c4bc39aa926c294",
            "Schema_Version": "PROVENANCE_P0_V1",
            "Population_or_Domain": "RESEARCH_PARTIAL",
            "Currentness_Status": "UNKNOWN",
            "Evidence_Strength": "MEDIUM",
        }
        sidecar_path = self.root / "universe" / "research_partial_1633_manifest.provenance_p0.json"
        sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
        result = validate_manifest_file(sidecar_path, self.root, allowed_source_ids={"CURRENT_CANONICAL"})
        self.assertTrue(result.ok, result)


if __name__ == "__main__":
    unittest.main()
