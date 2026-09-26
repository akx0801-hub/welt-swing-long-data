from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/frozen_1425_source_native_sector_coverage_v0_62.py"
spec = importlib.util.spec_from_file_location("v062", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class SourceNativeSectorCoverageV062Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD, "2b9637887c2ace039f95adc74cdade28c5e7b4fe")
        self.assertEqual(mod.V061_WORKFLOW_RUN, 36251198020)
        self.assertEqual(mod.V061_ARTIFACT_ID, 10909285736)
        self.assertEqual(mod.V061_ARTIFACT_DIGEST, "sha256:21b17657591e739ce1e1528bb754d99468cf2763f730cff8e8e51a09e7fd9ffb")
        self.assertEqual(mod.AUTHORITY_ID, "G-SEC-02")
        self.assertEqual(mod.GLOBAL_BLOCKER, "OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND")
        self.assertEqual(mod.GLOBAL_BLOCKER_COHORT, "BR_IBRX100")

    def test_expected_cohort_counts(self):
        self.assertEqual(sum(mod.EXPECTED_COHORTS.values()), 1425)
        self.assertEqual(mod.EXPECTED_COHORTS, {
            "AU_SP_ASX200": 63,
            "BR_IBRX100": 37,
            "CN_CSI300": 294,
            "IN_NIFTY50": 45,
            "JP_N225": 197,
            "TW_TW50": 49,
            "US_SP400": 368,
            "US_SP500": 372,
        })

    def test_governance_authority(self):
        _, g2, c21 = mod.validate_authorities()
        self.assertTrue(g2["rules"]["taxonomy_groups_semantically_isolated"])
        self.assertTrue(g2["rules"]["peer_group_must_not_mix_sector_taxonomy"])
        self.assertTrue(g2["rules"]["cross_taxonomy_comparison_forbidden"])
        self.assertFalse(g2["rules"]["sector_rs_authorized"])
        self.assertFalse(g2["rules"]["sector_mapping_population_authorized"])
        self.assertEqual(g2["future_peer_group_key"], ["Sector_Taxonomy", "Sector_Code"])
        self.assertEqual(g2["accepted_source_classes_inherited_from_v0_21"], c21["accepted_source_classes"])

    def test_reconstructed_cohorts(self):
        rows, counts = mod.reconstruct_cohorts()
        self.assertEqual(len(rows), 1425)
        self.assertEqual(counts, mod.EXPECTED_COHORTS)

    def test_research_has_all_cohorts_and_earliest_blockers(self):
        research = json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        self.assertEqual(set(research["cohort_findings"]), set(mod.EXPECTED_COHORTS))
        for cohort, finding in research["cohort_findings"].items():
            self.assertIn(finding["earliest_blocker"], {
                "SOURCE_NATIVE_TAXONOMY_IDENTITY_NOT_VERIFIED",
                "OFFICIAL_SECTOR_BULK_SOURCE_NOT_FOUND",
                "OFFICIAL_SECTOR_BULK_SOURCE_NOT_VERIFIED",
                "DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED",
                "SOURCE_NATIVE_SECTOR_CODE_NOT_AVAILABLE",
            })
            self.assertIn(mod.first_nonpass(finding["gate_status"]), mod.GATE_ORDER)

    def test_prohibited_calls_zero(self):
        self.assertTrue(all(v == 0 for v in mod.provider_calls().values()))


if __name__ == "__main__":
    unittest.main()
