from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/in_nifty50_remaining_3_sector_closure_v0_74.py"
spec=importlib.util.spec_from_file_location("v074",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class INNifty50Remaining3V074Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"57364dbf0b08edc2c563e0ecbf8f9d3e5fc2269f")
        self.assertEqual(mod.V073_WORKFLOW,36312901944)
        self.assertEqual(mod.V073_ARTIFACT,10929840911)
        self.assertEqual(mod.V073_DIGEST,"sha256:5d1cbce614a0f943af0cb76fddc4dcf7bd80b9e6a3213850a9bac4601784a706")
        self.assertEqual(mod.BOUND_LEVEL,"SECTOR")

    def test_remaining_nodes(self):
        self.assertEqual(set(mod.UNRESOLVED),{"Information Technology","Services","Telecommunication"})
        self.assertEqual(sum(v["affected"] for v in mod.UNRESOLVED.values()),7)
        self.assertEqual(mod.UNRESOLVED["Information Technology"]["node_id"],"11")
        self.assertEqual(mod.UNRESOLVED["Services"]["node_id"],"1")
        self.assertEqual(mod.UNRESOLVED["Telecommunication"]["node_id"],"7")

    def test_prefix_integrity(self):
        rows=[{
          "Macro_Economic_Sector_Code":"IN09","Sector_Code":"IN0901","Industry_Code":"IN090103","Basic_Industry_Code":"IN090103001"
        }]
        a=mod.prefix_integrity(rows)
        self.assertEqual(a["Mismatch_Count"],0)
        self.assertFalse(a["Used_As_Sole_Parent_Authority"])

    def test_parent_maps(self):
        rows=[{
          "Sector_Code":"IN0901","Sector_Name":"Services","Macro_Economic_Sector_Code":"IN09","Macro_Economic_Sector_Name":"Services",
          "Industry_Code":"IN090103","Basic_Industry_Code":"IN090103001"
        }]
        ip,bp,sm=mod.table_parent_maps(rows)
        self.assertEqual(ip["IN090103"],{"IN0901"})
        self.assertEqual(bp["IN090103001"],{"IN0901"})
        self.assertEqual(sm["IN0901"]["Macro_Code"],"IN09")

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"IN_NIFTY50")
        self.assertEqual(s["scope_gate"],"GATE_F_REMAINING_3_NODE_CLOSURE_ONLY")
        self.assertEqual(s["bound_classification_level"],"SECTOR")
        self.assertEqual(s["coordinate_extraction"]["required_version"],"1.26.4")
        self.assertFalse(s["application_contract_rediscovery_allowed"])
        self.assertFalse(s["application_endpoint_refetch_allowed"])
        self.assertFalse(s["nifty_constituent_refetch_allowed"])
        self.assertFalse(s["ocr_allowed"])
        self.assertFalse(s["fuzzy_matching_allowed"])
        self.assertFalse(s["semantic_inference_allowed"])
        self.assertFalse(s["pdsc_fallback_allowed"])
        self.assertFalse(s["gate_h_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

if __name__=="__main__":
    unittest.main()
