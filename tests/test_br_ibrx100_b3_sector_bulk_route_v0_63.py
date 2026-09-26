from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/br_ibrx100_b3_sector_bulk_route_v0_63.py"
spec=importlib.util.spec_from_file_location("v063",SCRIPT)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class BRIBRX100RouteV063Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"c07c2aab9578971b523c9d39428bdff5758a8761")
        self.assertEqual(mod.V062_WORKFLOW,36255299126)
        self.assertEqual(mod.V062_ARTIFACT,10910376599)
        self.assertEqual(mod.V062_DIGEST,"sha256:cc6c64baaf653830365a9cfaec9ab0d291523a49e02ad99714e2e8bb6606dcc7")
        self.assertEqual(mod.BLOCKER,"SOURCE_NATIVE_SECTOR_CODE_NOT_AVAILABLE:BR_IBRX100")

    def test_research_route(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        sel=r["selected_route"]
        self.assertTrue(sel["br_official_sector_bulk_route_ready"])
        self.assertEqual(sel["access_class"],"PUBLIC_REPRODUCIBLE")
        self.assertEqual(sel["classification_content"],"PASS")
        self.assertEqual(sel["sector_code"],"NOT_AVAILABLE")
        self.assertEqual(sel["blocker"],mod.BLOCKER)

    def test_only_br_scope(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        self.assertEqual(r["scope_cohort"],"BR_IBRX100")
        self.assertEqual(r["frozen_rows"],37)

    def test_up2data_not_used_for_classification_pass(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        up=next(x for x in r["resolved_routes"] if x["route_id"]=="UP2DATA_LISTED_COMPANIES")
        self.assertEqual(up["classification_content"],"NOT_VERIFIED")
        self.assertEqual(up["access_class"],"ENTITLEMENT_REQUIRED")

    def test_no_prohibited_requests(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        self.assertTrue(all(v==0 for v in r["prohibited_requests"].values()))
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

if __name__=="__main__": unittest.main()
