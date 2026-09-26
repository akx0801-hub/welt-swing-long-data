from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/in_nifty50_deterministic_security_identity_linkage_v0_70.py"
spec=importlib.util.spec_from_file_location("v070",SCRIPT)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class INNifty50IdentityLinkageV070Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"357df447e225ab1fc839530b1d2b0d2d217fd652")
        self.assertEqual(mod.V069_WORKFLOW,36272572257)
        self.assertEqual(mod.V069_ARTIFACT,10915843724)
        self.assertEqual(mod.V069_DIGEST,"sha256:55093cd80910864fdf7486167786f5ec3f503ce39294ae875745e82c652ef69a")
        self.assertEqual(mod.COHORT,"IN_NIFTY50")
        self.assertEqual(mod.MIC,"XNSE")

    def test_header_normalization(self):
        self.assertEqual(mod.norm_header("ISIN NUMBER"),"isinnumber")
        self.assertEqual(mod.norm_header("ISIN Code"),"isincode")
        self.assertEqual(mod.norm_symbol(" hdfcbank "),"HDFCBANK")
        self.assertEqual(mod.norm_isin(" ine040a01034 "),"INE040A01034")

    def test_csv_parse(self):
        fields,rows=mod.parse_csv_bytes(b"Symbol,Series,ISIN Code\nABC,EQ,INE000A01000\n")
        self.assertEqual(fields,["Symbol","Series","ISIN Code"])
        self.assertEqual(rows[0]["Symbol"],"ABC")

    def test_pick_fields(self):
        fields=["Company Name","Industry","Symbol","Series","ISIN Code"]
        self.assertEqual(mod.pick_field(fields,["symbol"]),"Symbol")
        self.assertEqual(mod.pick_field(fields,["isincode","isin"]),"ISIN Code")

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"IN_NIFTY50")
        self.assertEqual(s["gate"],"E_SECURITY_IDENTITY")
        self.assertEqual(s["frozen_target_rows"],45)
        self.assertEqual(s["primary_mic"],"XNSE")
        self.assertFalse(s["sector_classification_population_allowed"])
        self.assertFalse(s["gate_f_execution_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["per_security_web_fanout_allowed"])
        self.assertFalse(s["company_name_join_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

    def test_frozen_target_shape(self):
        target=mod.parse_frozen_target()
        self.assertEqual(len(target),45)
        self.assertEqual(len({r["WS_ID"] for r in target}),45)
        self.assertTrue(all(r["Primary_MIC"]=="XNSE" for r in target))
        self.assertTrue(all(r["WS_ID"]=="WS:ISIN:"+r["ISIN"] for r in target))

if __name__=="__main__": unittest.main()
