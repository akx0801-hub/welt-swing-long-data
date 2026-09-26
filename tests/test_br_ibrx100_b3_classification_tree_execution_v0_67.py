from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/br_ibrx100_b3_classification_tree_execution_v0_67.py"
spec=importlib.util.spec_from_file_location("v067",SCRIPT)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class BRIBRX100TreeExecutionV067Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"a6c7e3db455d73c436142230bd466c64f2ac147d")
        self.assertEqual(mod.V066_WORKFLOW,36269159688)
        self.assertEqual(mod.V066_ARTIFACT,10915250534)
        self.assertEqual(mod.V066_DIGEST,"sha256:af7fe53a42cd199ff2b1a1edd98cb73d7535131b1e2135977c45a0853d12b5ae")
        self.assertEqual(mod.METHOD,"PDSC_SHA256_V1")

    def test_encoding_examples(self):
        a=mod.encode_segment("Agricultura")
        self.assertEqual(a["query_value"],"QWdyaWN1bHR1cmE%3D")
        m=mod.encode_segment("Minerais Metálicos")
        self.assertEqual(m["query_value"],"TWluZXJhaXMlMjBNZXQlQzMlQTFsaWNvcw%3D%3D")

    def test_pdsc_determinism(self):
        import unicodedata
        raw="Consumo não Cíclico"
        self.assertEqual(mod.pdsc(raw),mod.pdsc(unicodedata.normalize("NFD",raw)))
        self.assertRegex(mod.pdsc(raw),r"^PDSC1:[0-9a-f]{64}$")

    def test_flatten_synthetic_tree(self):
        obj=[{"sector":"S1","subSectors":[{"sector":"SS1","segment":[{"segment":"A"},{"segment":"B"}]}]},
             {"sector":"S2","subSectors":[{"sector":"SS2","segment":[{"segment":"C"}]}]}]
        rows,c=mod.flatten_tree(obj)
        self.assertEqual(c["setor_count"],2)
        self.assertEqual(c["subsetor_count"],2)
        self.assertEqual(c["segmento_leaf_count"],3)
        self.assertEqual(c["distinct_segmento_label_count"],3)
        self.assertEqual(rows[0]["Setor_Economico_Raw"],"S1")

    def test_company_record_extraction(self):
        obj={"results":[{"code":"ABEV","companyName":"Ambev"},{"code":"PETR","companyName":"Petrobras"}],"totalRecords":2}
        rows=mod.extract_company_records(obj)
        self.assertEqual({r["B3_Company_Code"] for r in rows},{"ABEV","PETR"})
        self.assertEqual(mod.find_total_records(obj),2)

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"BR_IBRX100")
        self.assertEqual(s["tree_endpoint"],mod.TREE_URL)
        self.assertFalse(s["alpha_vantage_allowed"])
        self.assertFalse(s["per_security_web_fanout_allowed"])
        self.assertFalse(s["canonical_mapping_population_allowed"])

if __name__=="__main__":unittest.main()
