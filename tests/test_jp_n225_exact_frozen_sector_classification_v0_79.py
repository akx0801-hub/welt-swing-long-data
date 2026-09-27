from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/jp_n225_exact_frozen_sector_classification_v0_79.py"
spec=importlib.util.spec_from_file_location("v079",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class JPN225ExactFrozenSectorV079Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"4a5c2f5914f57e5333c68f7a8616dfd1b50adceb")
        self.assertEqual(mod.V078_WORKFLOW,36326606790)
        self.assertEqual(mod.V078_ARTIFACT,10933309355)
        self.assertEqual(mod.V078_DIGEST,"sha256:4c5d1eae5e6ff4d2fa0397b7d58b89f5ab4754021c481b06e8c7c3557d902114")
        self.assertEqual(mod.TAXONOMY,"NIKKEI_36_INDUSTRY_AND_SECTOR")
        self.assertEqual(mod.LEVEL,"SECTOR")

    def test_target(self):
        rows,audit=mod.reconstruct_target()
        self.assertEqual(len(rows),197)
        self.assertEqual(len({r["Security_Key"] for r in rows}),197)
        self.assertEqual(len({r["WS_ID"] for r in rows}),197)
        self.assertTrue(all(r["Primary_MIC"]=="XTKS" for r in rows))
        self.assertEqual(audit["Primary_MIC_Distribution"],{"XTKS":197})

    def test_pdsc_authority(self):
        expected={
          "Technology":"PDSC1:2eb3437c8c82dad4cca3468ea713f244dd11c166ecd04a2a03bb2e010229c093",
          "Financials":"PDSC1:0587309eb18ea75e0cd9964b23533cc25604f934902824576f82f9850c2c40be",
          "Consumer Goods":"PDSC1:78be66233d528b6397fc234995d241e69913ed571321c6bf6e1d7d8a1d3541ca",
          "Materials":"PDSC1:e3962e390df45617e19fea135091e814d14ced1f767bc1e4dbd543a4ccfcfef7",
          "Capital Goods/Others":"PDSC1:49d729022c336d8e7d9819f30f8a587fea2c0d4dce2e63142d469f187a131176",
          "Transportation and Utilities":"PDSC1:2fa8886dfeff0c0077ad4c1e75bdde490b6b2b67df89fdf035a9cb9d92dde596"
        }
        self.assertEqual(mod.AUTHORIZED_PDSC,expected)
        self.assertEqual({k:mod.pdsc(k) for k in expected},expected)

    def test_parser_rejects_missing_marker(self):
        p=mod.NikkeiHTMLParser()
        p.feed("<html><body><h3>Technology</h3></body></html>")
        x=mod.extract_component_structure(p)
        self.assertFalse(x["valid"])

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"JP_N225")
        self.assertEqual(s["scope_gate"],"F_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE_ONLY")
        self.assertEqual(s["taxonomy"],"NIKKEI_36_INDUSTRY_AND_SECTOR")
        self.assertEqual(s["sector_level"],"SECTOR")
        self.assertEqual(s["expected_frozen_rows"],197)
        self.assertEqual(s["expected_primary_mic"],"XTKS")
        self.assertEqual(s["component_source"]["max_requests"],1)
        self.assertFalse(s["identity_contract"]["numeric_casting_allowed"])
        self.assertFalse(s["identity_contract"]["zero_padding_allowed"])
        self.assertFalse(s["identity_contract"]["company_name_join_allowed"])
        self.assertFalse(s["identity_contract"]["fuzzy_matching_allowed"])
        self.assertFalse(s["limited_fallback"]["per_security_fanout_allowed"])
        self.assertFalse(s["scope_boundaries"]["gate_h_allowed"])
        self.assertFalse(s["scope_boundaries"]["canonical_materialization_allowed"])
        self.assertFalse(s["scope_boundaries"]["other_cohort_allowed"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])
        self.assertTrue(s["forbidden"]["sec_requests"])
        self.assertTrue(s["forbidden"]["nse_requests"])

if __name__=="__main__":
    unittest.main()
