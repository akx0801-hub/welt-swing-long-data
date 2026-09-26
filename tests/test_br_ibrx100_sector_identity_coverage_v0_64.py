from __future__ import annotations
import importlib.util,json,re,unittest,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/br_ibrx100_sector_identity_coverage_v0_64.py"
spec=importlib.util.spec_from_file_location("v064",SCRIPT)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class BRIBRX100IdentityCoverageV064Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"f0a67388740b17dd62b47f1163df76d503a9c50b")
        self.assertEqual(mod.V063_WORKFLOW,36258067350)
        self.assertEqual(mod.V063_ARTIFACT,10911387342)
        self.assertEqual(mod.V063_DIGEST,"sha256:0ec10e147c619ec999af1b8de3dcd34b93d4fff29c3f6a96dd672bcb05446535")
        self.assertEqual(mod.METHOD,"PDSC_SHA256_V1")
        self.assertEqual(mod.BLOCKER,"BR_EXACT_37_COVERAGE_INCOMPLETE")

    def test_authority(self):
        a=mod.validate_authority()
        self.assertEqual(a["authority_id"],"G-SEC-03")
        self.assertEqual(a["br_binding"]["Sector_Taxonomy"],"B3_CLASSIFICACAO_SETORIAL")
        self.assertEqual(a["br_binding"]["Sector_Level"],"SETOR_ECONOMICO")
        self.assertEqual(a["source_code_absent_values"]["Sector_Code_Method"],"PDSC_SHA256_V1")
        self.assertFalse(a["rules"]["canonical_mapping_population_authorized"])
        self.assertFalse(a["rules"]["sector_rs_authorized"])

    def test_target_37_and_company_code_rule(self):
        rows=mod.target_rows()
        self.assertEqual(len(rows),37)
        for r in rows:
            self.assertEqual(r["Primary_MIC"],"BVMF")
            self.assertEqual(len(r["Primary_Ticker"]),5)
            self.assertTrue(r["Primary_Ticker"].endswith("3"))
            self.assertEqual(len(r["Primary_Ticker"][:4]),4)

    def test_pdsc_exact_algorithm(self):
        raw="Consumo não Cíclico"
        code1=mod.pdsc(raw)
        code2=mod.pdsc(unicodedata.normalize("NFD",raw))
        self.assertEqual(code1,code2)
        self.assertRegex(code1,r"^PDSC1:[0-9a-f]{64}$")
        expected_payload="B3_CLASSIFICACAO_SETORIAL\x1fSETOR_ECONOMICO\x1f"+unicodedata.normalize("NFC",raw)
        import hashlib
        self.assertEqual(code1,"PDSC1:"+hashlib.sha256(expected_payload.encode("utf-8")).hexdigest())

    def test_research_exact37_fail_closed(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        x=r["exact_37_result"]
        self.assertEqual((x["ready"],x["ambiguous"],x["not_found"],x["not_verified"]),(0,0,0,37))
        self.assertEqual(x["blocker"],"BR_EXACT_37_COVERAGE_INCOMPLETE")
        self.assertEqual(x["security_to_company_rows"],37)
        self.assertEqual(x["exact_row_level_sector_name_coverage_status"],"NOT_VERIFIED")

    def test_no_prohibited_calls(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        self.assertTrue(all(v==0 for v in r["prohibited_requests"].values()))
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

if __name__=="__main__":
    unittest.main()
