#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/tw_tw50_gate_b_pdf_content_repair_v0_91.py"
s=importlib.util.spec_from_file_location("v091",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.91")
        self.assertEqual(m.REQUIRED_START_HEAD,"90f796612937089ec9ac115c2a77a72d2a66c2a1")
    def test_spec(self):
        x=json.loads(m.SPEC.read_text())
        self.assertTrue(x["fail_closed"])
        self.assertEqual(x["tw_authority"]["taxonomy"],"ICB")
        self.assertEqual(x["tw_authority"]["formal_level"],"INDUSTRY_GROUP")
        self.assertTrue(x["forbidden"]["alpha_vantage"])
        self.assertTrue(x["forbidden"]["tw_gate_e"])
        self.assertTrue(x["forbidden"]["tw_gate_f"])
        self.assertTrue(x["forbidden"]["tw_gate_h"])
        self.assertTrue(x["forbidden"]["frozen_49_linkage"])
    def test_v090_correction_authority(self):
        r1=json.loads(m.RUN1_90.read_text());r2=json.loads(m.RUN2_90.read_text());rp=json.loads(m.REPLAY90.read_text())
        for r in [r1,r2,rp]:
            self.assertEqual(r["status"],200)
            self.assertEqual(r["bytes"],335595)
            self.assertEqual(r["sha256"],"4fbd2617c611df41de1e1f9e64e8774a115eb66343c29498da526eda5681f86f")
            self.assertIn(".pdf",r["content_disposition"].lower())
        self.assertEqual(r1["Format"],"TEXT_DECODE_FAILED")
    def test_v090_park_and_selection(self):
        s=json.loads(m.SUM90.read_text());c=json.loads(m.CHK90.read_text())
        self.assertEqual(s["au_park_state"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(s["selected_cohort"],"TW_TW50")
        self.assertEqual(c["workflow_run_id"],m.V090_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V090_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V090_DIGEST)
    def test_park_registry(self):
        self.assertEqual(m.sha_file(m.PARK),m.PARK90_SHA)
        rows=m.read_csv(m.PARK)
        self.assertEqual(len(rows),5)
        by={r["Cohort"]:r["Execution_State"] for r in rows}
        self.assertEqual(by["AU_SP_ASX200"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(by["IN_NIFTY50"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(by["JP_N225"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(by["US_SP400"],"PARKED_SOURCE_ACCESS")
        self.assertEqual(by["US_SP500"],"PARKED_SHARED_SOURCE_PREREQUISITE")
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        reg=m.read_csv(m.REGISTRY)
        self.assertEqual(len(reg),1)
        self.assertEqual(reg[0]["Cohort"],"BR_IBRX100")
        self.assertEqual(reg[0]["Semantic_SHA256"],m.BR_SHA)
    def test_no_tw_canonical(self):
        self.assertFalse(any(m.CANON_DIR.glob("TW_TW50_*.csv")))
    def test_content_failure_precedence(self):
        blank={
          "ROW_LEVEL_SECURITY_RECORDS":"YES","Identifier_Usable_For_Future_Gate_E":"NO",
          "Industry_Group_Explicit":False,"ICB_Level":"NOT_VERIFIED"
        }
        ready,b=m.content_contract_from_pdf(blank)
        self.assertFalse(ready)
        self.assertEqual(b,"TWSE_BULK_SECURITY_IDENTIFIER_NOT_AVAILABLE")
    def test_identifier_patterns_do_not_include_company_name(self):
        names=[x[0] for x in m.IDENTIFIER_PATTERNS]
        self.assertNotIn("Company name",names)
        self.assertNotIn("Constituent",names)

if __name__=="__main__":unittest.main()
