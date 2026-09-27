from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/in_nifty50_nse_classification_structure_repair_v0_72.py"
spec=importlib.util.spec_from_file_location("v072",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class INNifty50GateFRepairV072Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"f6be8b4a3182728ba9976b58410f91e031146348")
        self.assertEqual(mod.V071_WORKFLOW,36308429404)
        self.assertEqual(mod.V071_ARTIFACT,10928267335)
        self.assertEqual(mod.V071_DIGEST,"sha256:9de669cf670be62f99f325ae7deedb2af8028d6222d6b725af8d71a94e3244ed")
        self.assertEqual(mod.V071_PDF_SHA,"8ae58cbd10d7dd5184d76cfec6486f91c019026c8de329432b69c54ff7235f8b")
        self.assertEqual(mod.TAXONOMY,"NSE_INDICES_INDUSTRY_CLASSIFICATION")

    def test_expected_labels_exact_15(self):
        self.assertEqual(len(mod.EXPECTED_LABELS),15)
        self.assertEqual(len(set(mod.EXPECTED_LABELS)),15)
        self.assertIn("Oil Gas & Consumable Fuels",mod.EXPECTED_LABELS)
        self.assertIn("Telecommunication",mod.EXPECTED_LABELS)

    def test_code_level_contract(self):
        self.assertEqual(mod.DIGITS_TO_LEVEL[2],"MACRO_ECONOMIC_SECTOR")
        self.assertEqual(mod.DIGITS_TO_LEVEL[4],"SECTOR")
        self.assertEqual(mod.DIGITS_TO_LEVEL[6],"INDUSTRY")
        self.assertEqual(mod.DIGITS_TO_LEVEL[9],"BASIC_INDUSTRY")

    def test_simple_structured_parse(self):
        def cell(s,w):
            return s + " "*(w-len(s))
        line=(cell("IN01 Commodities",25)+
              cell("IN0101 Chemicals",30)+
              cell("IN010101 Chemicals & Petrochemicals",40)+
              cell("IN010101001 Commodity Chemicals",45)+
              "Definition")
        parsed=mod.parse_taxonomy([line])
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["nodes"]["MACRO_ECONOMIC_SECTOR"]["IN01"]["name"],"Commodities")
        self.assertEqual(parsed["nodes"]["SECTOR"]["IN0101"]["name"],"Chemicals")
        self.assertEqual(parsed["nodes"]["INDUSTRY"]["IN010101"]["name"],"Chemicals & Petrochemicals")
        self.assertEqual(parsed["nodes"]["BASIC_INDUSTRY"]["IN010101001"]["name"],"Commodity Chemicals")
        self.assertEqual(len(parsed["rows"]),1)

    def test_parent_path(self):
        nodes={
          "MACRO_ECONOMIC_SECTOR":{"IN02":{"name":"Consumer Discretionary"}},
          "SECTOR":{"IN0201":{"name":"Automobile and Auto Components"}},
          "INDUSTRY":{"IN020101":{"name":"Automobiles"}},
          "BASIC_INDUSTRY":{"IN020101001":{"name":"Passenger Cars & Utility Vehicles"}}
        }
        self.assertEqual(
          mod.parent_path("SECTOR","IN0201",nodes),
          "IN02 Consumer Discretionary > IN0201 Automobile and Auto Components"
        )

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"IN_NIFTY50")
        self.assertEqual(s["scope_gate"],"GATE_F_REPAIR_ONLY")
        self.assertEqual(s["taxonomy"],"NSE_INDICES_INDUSTRY_CLASSIFICATION")
        self.assertEqual(s["pdf_parser"]["package"],"pypdf")
        self.assertEqual(s["pdf_parser"]["required_version"],"5.9.0")
        self.assertFalse(s["nifty_constituent_refetch_allowed"])
        self.assertFalse(s["nse_equity_l_allowed"])
        self.assertFalse(s["ocr_allowed"])
        self.assertFalse(s["pdsc_fallback_allowed"])
        self.assertFalse(s["gate_h_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

if __name__=="__main__":
    unittest.main()
