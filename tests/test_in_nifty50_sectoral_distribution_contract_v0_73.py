from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/in_nifty50_sectoral_distribution_contract_v0_73.py"
spec=importlib.util.spec_from_file_location("v073",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class INNifty50SectoralDistributionV073Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"7464e7c643922e946c39631c58174e9716cb53b4")
        self.assertEqual(mod.V072_WORKFLOW,36309975985)
        self.assertEqual(mod.V072_ARTIFACT,10929365141)
        self.assertEqual(mod.V072_DIGEST,"sha256:8c3fb77305adcb7e2321aed34805ab5525afc176d3a7b7b4fa26420ca649ebba")
        self.assertEqual(mod.V072_STRUCTURAL_SHA,"d431587f5f686b8432bc57755a8fe6aef232fed49fb858cf7e905b3318687173")

    def test_level_contract(self):
        self.assertEqual(set(mod.LEVEL_LABELS),{"MACRO_ECONOMIC_SECTOR","SECTOR","INDUSTRY","BASIC_INDUSTRY"})
        self.assertEqual(mod.DISPLAY_TO_LEVEL["Macro Economic Sector"],"MACRO_ECONOMIC_SECTOR")
        self.assertEqual(mod.DISPLAY_TO_LEVEL["Basic Industry"],"BASIC_INDUSTRY")

    def test_expected_labels(self):
        self.assertEqual(len(mod.EXPECTED_LABELS),15)
        self.assertEqual(len(set(mod.EXPECTED_LABELS)),15)
        self.assertIn("Information Technology",mod.EXPECTED_LABELS)

    def test_official_host(self):
        self.assertTrue(mod.is_official("https://www.niftyindices.com/x"))
        self.assertTrue(mod.is_official("https://assets.niftyindices.com/x"))
        self.assertFalse(mod.is_official("https://example.com/x"))

    def test_membership_extraction_nested(self):
        obj={"level":"Sector","category":{"name":"Financial Services","code":"IN0501",
             "stocks":[{"symbol":"HDFCBANK"},{"symbol":"ICICIBANK"}]}}
        rows=mod.extract_membership_records(obj,"LEVEL:Sector","https://www.niftyindices.com/api")
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r["category_label"]=="Financial Services" for r in rows))
        self.assertTrue(all(r["application_node_id_or_code"]=="IN0501" for r in rows))

    def test_taxonomy_lookup_code(self):
        maps={"SECTOR":{"IN0501":{"code":"IN0501","name":"Financial Services"}}}
        code,name,method=mod.taxonomy_lookup(maps,"SECTOR","Financial Services","IN0501")
        self.assertEqual(code,"IN0501")
        self.assertEqual(name,"Financial Services")
        self.assertEqual(method,"APPLICATION_NODE_ID_EQUALS_TAXONOMY_SOURCE_NATIVE_CODE")

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"IN_NIFTY50")
        self.assertEqual(s["scope_gate"],"GATE_F_APPLICATION_CONTRACT_RESOLUTION_ONLY")
        self.assertEqual(s["taxonomy"],"NSE_INDICES_INDUSTRY_CLASSIFICATION")
        self.assertFalse(s["nifty_constituent_refetch_allowed"])
        self.assertFalse(s["nse_equity_l_allowed"])
        self.assertFalse(s["company_name_join_allowed"])
        self.assertFalse(s["semantic_inference_allowed"])
        self.assertFalse(s["cross_taxonomy_mapping_allowed"])
        self.assertFalse(s["pdsc_fallback_allowed"])
        self.assertFalse(s["per_security_fanout_allowed"])
        self.assertFalse(s["gate_h_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

if __name__=="__main__":
    unittest.main()
