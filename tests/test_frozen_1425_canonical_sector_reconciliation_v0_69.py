from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/frozen_1425_canonical_sector_reconciliation_v0_69.py"
spec=importlib.util.spec_from_file_location("v069",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class Frozen1425CanonicalSectorReconciliationV069Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"978404e766f7813819686835adf2254cd5071c62")
        self.assertEqual(mod.V068_WORKFLOW,36271957458)
        self.assertEqual(mod.V068_ARTIFACT,10916176386)
        self.assertEqual(mod.V068_DIGEST,"sha256:e3acc96caff5715a5e09d123b3183137a0f84097afb1315b7c523a75d3f24e77")
        self.assertEqual(mod.BR_SEMANTIC_SHA,"bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed")
        self.assertEqual(mod.BR_FILE_SHA,"83706c76baba6d9a4fcc557d170f0bcad6fd85c9ca90fbc9f062cd5765dcef28")

    def test_expected_counts(self):
        self.assertEqual(sum(mod.EXPECTED_COUNTS.values()),1425)
        self.assertEqual(mod.EXPECTED_COUNTS["BR_IBRX100"],37)
        self.assertEqual(mod.EXPECTED_COUNTS["IN_NIFTY50"],45)
        self.assertEqual(len(mod.UNRESOLVED_COHORTS),7)
        self.assertNotIn("BR_IBRX100",mod.UNRESOLVED_COHORTS)

    def test_status_conversion(self):
        self.assertEqual(mod.current_status_from_historical("PASS"),"PASS_INHERITED")
        self.assertEqual(mod.current_status_from_historical("NOT_VERIFIED"),"NOT_VERIFIED")
        self.assertEqual(mod.current_status_from_historical("NOT_EVALUATED"),"NOT_EVALUATED")

    def test_resolved_statuses(self):
        self.assertEqual(mod.RESOLVED,{"PASS_INHERITED","PASS_BY_CURRENT_GOVERNANCE"})

    def test_next_gate_templates(self):
        self.assertEqual(
            mod.NEXT_GATE_TEMPLATES["E"].format(cohort="IN_NIFTY50"),
            "IN_NIFTY50 DETERMINISTIC SECURITY IDENTITY LINKAGE GATE"
        )
        self.assertEqual(
            mod.NEXT_GATE_TEMPLATES["F"].format(cohort="JP_N225"),
            "JP_N225 EXACT FROZEN SECTOR CLASSIFICATION COVERAGE GATE"
        )

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_gsec03_contract_is_narrow(self):
        g=json.loads(mod.GSEC03.read_text(encoding="utf-8"))
        self.assertEqual(g["authority_id"],"G-SEC-03")
        self.assertTrue(g["rules"]["project_derived_canonical_sector_code_allowed_when_official_classification_exact_but_native_code_absent"])
        self.assertTrue(g["rules"]["classification_inference_forbidden"])
        self.assertTrue(g["rules"]["classification_guessing_forbidden"])
        self.assertEqual(g["rules"]["canonical_method_when_native_code_absent"],"PDSC_SHA256_V1")

    def test_spec_no_execution(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertFalse(s["external_requests_allowed"])
        self.assertFalse(s["provider_calls_allowed"])
        self.assertFalse(s["mapping_population_allowed"])
        self.assertFalse(s["sector_rs_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["other_cohort_execution_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

if __name__=="__main__":
    unittest.main()
