from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/br_ibrx100_canonical_sector_metadata_materialization_v0_68.py"
spec=importlib.util.spec_from_file_location("v068",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class BRIBRX100CanonicalSectorMetadataV068Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"f27a8be1cea6ed38b3fe92a1ca3a15a54de6fd89")
        self.assertEqual(mod.V067_WORKFLOW,36270129434)
        self.assertEqual(mod.V067_ARTIFACT,10914754106)
        self.assertEqual(mod.V067_DIGEST,"sha256:84d16a51b33ec4ff29375017244f498ab844d4a8621ee56c3a4d1736d5af1510")
        self.assertEqual(mod.TREE_SHA,"febe642ea5b713c7a8709d1bf314ea3bac84b6ccf21f155073bc315ffc0bd0bd")
        self.assertEqual(mod.COHORT,"BR_IBRX100")
        self.assertEqual(mod.TAXONOMY,"B3_CLASSIFICACAO_SETORIAL")
        self.assertEqual(mod.LEVEL,"SETOR_ECONOMICO")
        self.assertEqual(mod.METHOD,"PDSC_SHA256_V1")

    def test_pdsc_deterministic(self):
        import unicodedata
        name="Consumo não Cíclico"
        self.assertEqual(mod.pdsc(name),mod.pdsc(unicodedata.normalize("NFD",name)))
        self.assertRegex(mod.pdsc(name),r"^PDSC1:[0-9a-f]{64}$")

    def test_semantic_hash_order_independent(self):
        rows=[
            {"WS_ID":"WS:BVMF:BBBB3","Sector_Taxonomy":"T","Sector_Level":"L","Sector_Code":"C2","Sector_Name":"S2","Mapping_Status":"VERIFIED_CANONICAL"},
            {"WS_ID":"WS:BVMF:AAAA3","Sector_Taxonomy":"T","Sector_Level":"L","Sector_Code":"C1","Sector_Name":"S1","Mapping_Status":"VERIFIED_CANONICAL"},
        ]
        self.assertEqual(mod.semantic_bytes(rows),mod.semantic_bytes(list(reversed(rows))))

    def test_csv_deterministic(self):
        rows=[{f:"x" for f in mod.CANONICAL_FIELDS}]
        self.assertEqual(mod.deterministic_csv_bytes(rows,mod.CANONICAL_FIELDS),mod.deterministic_csv_bytes(rows,mod.CANONICAL_FIELDS))

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_governance_authority(self):
        g=json.loads(mod.GSEC04.read_text(encoding="utf-8"))
        self.assertEqual(g["authority_id"],"G-SEC-04")
        self.assertEqual(g["version"],"v0.68")
        self.assertTrue(g["rules"]["canonical_sector_metadata_may_materialize_incrementally_by_complete_frozen_cohort"])
        self.assertFalse(g["rules"]["sector_rs_authorized"])
        self.assertFalse(g["rules"]["external_reference_requests_authorized"])

    def test_spec_scope(self):
        s=json.loads((ROOT/"config/br_ibrx100_canonical_sector_metadata_materialization_spec_v0.68.json").read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"BR_IBRX100")
        self.assertEqual(s["frozen_rows"],37)
        self.assertEqual(s["expected_distinct_setores"],10)
        self.assertEqual(s["global_ready_after_success"],37)
        self.assertEqual(s["global_total"],1425)
        self.assertFalse(s["external_market_reference_requests_allowed"])
        self.assertFalse(s["b3_requests_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])
        self.assertFalse(s["sector_rs_allowed"])
        self.assertFalse(s["p0_allowed"])

    def test_required_contract_fields(self):
        required={"WS_ID","Sector_Taxonomy","Sector_Code","Sector_Name","Source_Name","Source_Reference","Source_Version_or_AsOf","Mapping_Status"}
        self.assertTrue(required.issubset(set(mod.CANONICAL_FIELDS)))
        added={"Primary_Universe_Index","Primary_MIC","Primary_Ticker","Sector_Level","Sector_Raw_Name","Source_Sector_Code",
               "Sector_Code_Origin","Sector_Code_Method","B3_Company_Code","Evidence_Version","Evidence_Final_Commit","Tree_Snapshot_SHA256"}
        self.assertTrue(added.issubset(set(mod.CANONICAL_FIELDS)))

if __name__=="__main__":
    unittest.main()
