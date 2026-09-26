from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/b3_classification_application_contract_discovery_v0_66.py"
spec=importlib.util.spec_from_file_location("v066",SCRIPT)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class B3ApplicationContractDiscoveryV066Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"fb651c31f55f14a7fcb6bb3c83c5b25e3d69a4e6")
        self.assertEqual(mod.V065_WORKFLOW,36266926685)
        self.assertEqual(mod.V065_ARTIFACT,10914042556)
        self.assertEqual(mod.V065_DIGEST,"sha256:0fcc27756c32156da0fa4be605f8dee1a2fa52fa3bd88aac2ecfc07355058146")
        self.assertEqual(mod.FAIL_VERDICT,"BLOCKED_B3_PUBLIC_APPLICATION_DATA_CONTRACT")
        self.assertEqual(mod.FAIL_BLOCKER,"B3_PUBLIC_CLASSIFICATION_DATA_CONTRACT_NOT_DISCOVERED")

    def test_allowed_host(self):
        allowed={"sistemaswebb3-listados.b3.com.br","www.b3.com.br","b3.com.br"}
        self.assertTrue(mod.allowed_host("https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/",allowed))
        self.assertTrue(mod.allowed_host("https://www.b3.com.br/a",allowed))
        self.assertFalse(mod.allowed_host("https://example.com/a",allowed))

    def test_json_contract_tree_candidate(self):
        obj={"setores":[{"setor":"A","subsetores":[{"subsetor":"B","segmentos":[{"segmento":"C"} for _ in range(10)]}]} for _ in range(2)]}
        cls=mod.json_contract_classification(obj)
        self.assertTrue(cls["tree_candidate"])
        self.assertFalse(cls["all_company_candidate"])

    def test_json_contract_company_candidate(self):
        obj=[{"codigo":f"C{i:04d}","empresa":f"E{i}","setor":"Financeiro"} for i in range(150)]
        cls=mod.json_contract_classification(obj)
        self.assertTrue(cls["all_company_candidate"])

    def test_endpoint_candidate_filter(self):
        allowed={"sistemaswebb3-listados.b3.com.br"}
        strings=["/listedCompaniesPage/api/classification","https://example.com/api/classification","/assets/main.js"]
        out=mod.endpoint_candidates(strings,"https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/",allowed)
        self.assertIn("https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/api/classification",out)
        self.assertTrue(all("example.com" not in x for x in out))
        self.assertTrue(all(not x.endswith(".js") for x in out))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"BR_IBRX100")
        self.assertFalse(s["authentication_bypass_allowed"])
        self.assertFalse(s["per_security_fanout_allowed"])
        self.assertFalse(s["exact37_execution_allowed"])
        self.assertFalse(s["canonical_mapping_population_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

if __name__=="__main__":
    unittest.main()
