from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/in_nifty50_exact_frozen_sector_classification_coverage_v0_71.py"
spec=importlib.util.spec_from_file_location("v071",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class INNifty50GateFV071Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"9acf51ba20e5c88954d0b21ed5017f95274b6f6f")
        self.assertEqual(mod.V070_WORKFLOW,36274393667)
        self.assertEqual(mod.V070_ARTIFACT,10917150644)
        self.assertEqual(mod.V070_DIGEST,"sha256:a0e9b942970d510f7bc1042e7b93371b61662adb61cc972e557847046aa34ede")
        self.assertEqual(mod.V070_NIFTY_SHA,"9fb8832853c279448d2bc05f0e7dd5f460ed2ff35332fea8c40fc1250362ad28")
        self.assertEqual(mod.TAXONOMY,"NSE_INDICES_INDUSTRY_CLASSIFICATION")
        self.assertEqual(mod.BOUND_LEVEL,"INDUSTRY")

    def test_header_and_id_normalization(self):
        self.assertEqual(mod.norm_header("ISIN Code"),"isincode")
        self.assertEqual(mod.norm_id(" ine002a01018 "),"INE002A01018")
        self.assertEqual(mod.layout_norm("IT   -\n Software"),"IT - Software")

    def test_csv_parser(self):
        fields,rows=mod.parse_csv_bytes(b"Company Name,Industry,Symbol,Series,ISIN Code\nX,Banks,ABC,EQ,INE000A01000\n")
        self.assertEqual(fields,["Company Name","Industry","Symbol","Series","ISIN Code"])
        self.assertEqual(rows[0]["Industry"],"Banks")

    def test_label_occurrence_industry(self):
        txt="IN05 Financial Services IN050102 Banks IN050102001 Private Sector Bank"
        occ=mod.exact_label_occurrences(txt,"Banks")
        self.assertEqual(len([x for x in occ if x["level"]=="INDUSTRY" and x["code"]=="IN050102"]),1)

    def test_label_occurrence_cross_level(self):
        txt="IN03 Energy IN0301 Oil Gas IN030101 Energy IN030101001 Energy"
        occ=mod.exact_label_occurrences(txt,"Energy")
        levels={x["level"] for x in occ}
        self.assertIn("MACRO_ECONOMIC_SECTOR",levels)
        self.assertIn("INDUSTRY",levels)
        self.assertIn("BASIC_INDUSTRY",levels)

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"IN_NIFTY50")
        self.assertEqual(s["gate"],"F_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE")
        self.assertEqual(s["frozen_target_rows"],45)
        self.assertEqual(s["primary_mic"],"XNSE")
        self.assertEqual(s["taxonomy"],"NSE_INDICES_INDUSTRY_CLASSIFICATION")
        self.assertFalse(s["pdsc_fallback_allowed"])
        self.assertFalse(s["gate_h_promotion_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["per_security_web_fanout_allowed"])
        self.assertFalse(s["cross_taxonomy_crosswalk_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

if __name__=="__main__":
    unittest.main()
