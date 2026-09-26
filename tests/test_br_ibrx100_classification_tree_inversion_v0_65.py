from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/br_ibrx100_classification_tree_inversion_v0_65.py"
spec=importlib.util.spec_from_file_location("v065",SCRIPT)
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class BRIBRX100TreeInversionV065Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"4e8151225f19ad1748c203b295e3ff699eabb7bf")
        self.assertEqual(mod.V064_WORKFLOW,36264343312)
        self.assertEqual(mod.V064_ARTIFACT,10913620188)
        self.assertEqual(mod.V064_DIGEST,"sha256:970d4c510642f5803ca4228fe2715d10661fc8733c7eb7fee5e1ad94d700678c")
        self.assertEqual(mod.BLOCKER,"B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE")

    def test_encoding_agricultura(self):
        x=mod.encode_segment("Agricultura")
        self.assertEqual(x["encoded_component"],"Agricultura")
        self.assertEqual(x["base64"],"QWdyaWN1bHR1cmE=")
        self.assertEqual(x["query_value"],"QWdyaWN1bHR1cmE%3D")

    def test_encoding_minerais_metalicos(self):
        x=mod.encode_segment("Minerais Metálicos")
        self.assertEqual(x["encoded_component"],"Minerais%20Met%C3%A1licos")
        self.assertEqual(x["base64"],"TWluZXJhaXMlMjBNZXQlQzMlQTFsaWNvcw==")
        self.assertEqual(x["query_value"],"TWluZXJhaXMlMjBNZXQlQzMlQTFsaWNvcw%3D%3D")

    def test_research_fail_closed(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        self.assertEqual(r["hierarchy_capture"]["result"],"NOT_MACHINE_REPRODUCIBLE_COMPLETE")
        self.assertEqual(r["coverage_execution"]["coverage_classification_nodes_queried"],0)
        self.assertEqual(r["coverage_execution"]["exact37_ready"],0)
        self.assertEqual(r["coverage_execution"]["not_verified"],37)
        self.assertEqual(r["blocker"],mod.BLOCKER)

    def test_no_prohibited_calls(self):
        r=json.loads(mod.RESEARCH.read_text(encoding="utf-8"))
        self.assertTrue(all(v==0 for v in r["prohibited_requests"].values()))
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

if __name__=="__main__": unittest.main()
