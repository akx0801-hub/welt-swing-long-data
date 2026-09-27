#!/usr/bin/env python3
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"scripts/jp_n225_source_access_evidence_persistence_v0_80.py"
spec=importlib.util.spec_from_file_location("jp80",MOD)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class GateHTests(unittest.TestCase):
    def test_stage_identity(self):
        self.assertEqual(mod.VERSION,"v0.80")
        self.assertEqual(mod.STAGE,"JP_N225_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE")
        self.assertEqual(mod.REQUIRED_START_HEAD,"954c7272b575c0d0c3ae9633db073ad2e126daa7")

    def test_gsec05(self):
        g=json.loads(mod.GSEC05.read_text(encoding="utf-8"))
        self.assertEqual(g["authority_id"],"G-SEC-05")
        self.assertFalse(g["legal_opinion"])
        self.assertTrue(g["rules"]["explicit_official_operational_restriction_requires_fail_closed"])
        self.assertTrue(g["rules"]["unknown_raw_redistribution_rights_alone_do_not_fail_when_raw_not_required"])

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"JP_N225")
        self.assertEqual(s["scope_gate"],"H_ACCESS_PERSISTENCE_ONLY")
        self.assertFalse(s["raw_persistence"]["required_for_audit"])
        self.assertTrue(s["forbidden"]["gate_f_rerun"])
        self.assertTrue(s["forbidden"]["canonical_materialization"])
        self.assertTrue(s["forbidden"]["sec_requests"])
        self.assertTrue(s["forbidden"]["nse_requests"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])

    def test_sources(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["sources"]["A"]["necessity"],"REQUIRED")
        self.assertEqual(s["sources"]["B"]["necessity"],"REQUIRED")
        self.assertEqual(s["sources"]["C"]["necessity"],"CORROBORATING_ONLY")
        self.assertEqual(s["sources"]["A"]["canonical_name"],"NIKKEI_INDEXES_NIKKEI225_COMPONENTS")
        self.assertEqual(s["sources"]["B"]["canonical_name"],"NIKKEI_INDEXES_NIKKEI225_PROFILE")

    def test_predecessor_summary(self):
        s=json.loads(mod.SUM79.read_text(encoding="utf-8"))
        self.assertEqual(s["verdict"],"PASS_JP_N225_EXACT_FROZEN_SECTOR_CLASSIFICATION_COVERAGE")
        self.assertEqual((s["classified"],s["total"]),(197,197))
        self.assertEqual(s["current_source_matches"],197)
        self.assertEqual(s["pdsc_coverage"],197)
        self.assertEqual(s["pdsc_collisions"],0)

    def test_policy_pages_official_only(self):
        self.assertEqual(len(mod.POLICY_DEFS),3)
        for d in mod.POLICY_DEFS:
            self.assertTrue(d["Official_URL"].startswith("https://indexes.nikkei.co.jp/"))

    def test_no_jp_canonical_partition(self):
        self.assertFalse(mod.JP_CANONICAL.exists())

    def test_future_metadata_contract(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        fields=set(s["future_canonical_metadata_fields"])
        needed={"WS_ID","Primary_MIC","Primary_Ticker","Sector_Taxonomy","Sector_Level","Sector_Code","Source_Sector_Code","Sector_Name","Sector_Code_Origin","Sector_Code_Method","Source_Name","Source_Reference","Source_Update_Raw","Source_Retrieved_UTC","Source_SHA256","Mapping_Status","Evidence_Final_Commit"}
        self.assertEqual(fields,needed)

if __name__=="__main__":unittest.main()
