#!/usr/bin/env python3
import importlib.util,json,unittest,hashlib,csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/tw_tw50_gate_b_runtime_candidate_content_verification_v0_92.py"
s=importlib.util.spec_from_file_location("v092",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.92")
        self.assertEqual(m.REQUIRED_START_HEAD,"14270624d2f34f68fc0041d1cb7bd9d94c4b8d4f")
    def test_spec_scope(self):
        x=json.loads(m.SPEC.read_text())
        self.assertTrue(x["scope"]["no_new_broad_source_hunt"])
        self.assertTrue(x["scope"]["evaluate_only_known_candidates"])
        self.assertFalse(x["scope"]["tw_gate_e"])
        self.assertFalse(x["scope"]["tw_gate_f"])
        self.assertFalse(x["scope"]["tw_gate_h"])
        self.assertFalse(x["scope"]["tw_parking"])
        self.assertFalse(x["scope"]["reselection"])
        self.assertFalse(x["scope"]["cn_csi300_execution"])
        self.assertEqual(len(x["candidates"]),5)
    def test_predecessor_authority(self):
        s=json.loads(m.SUM91.read_text());c=json.loads(m.CHK91.read_text())
        self.assertEqual(s["version"],"v0.91")
        self.assertEqual(s["pdf_route_reproducible"],"YES")
        self.assertEqual(s["pdf_parse_status"],"PASS")
        self.assertEqual(s["pdf_pages"],2)
        self.assertEqual(s["pdf_row_level_security_records"],"YES")
        self.assertEqual(s["pdf_security_identifier"],"NOT_AVAILABLE")
        self.assertEqual(s["pdf_icb_level"],"NOT_VERIFIED")
        self.assertEqual(c["workflow_run_id"],m.V091_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V091_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V091_DIGEST)
    def test_v091_page_reconciliation_input(self):
        rows=m.read_csv(m.PAGE91);pdf=json.loads(m.PDF91.read_text())
        self.assertEqual(pdf["PDF_Page_Count"],2)
        self.assertEqual(len(rows),3)
        self.assertEqual([int(r["Page"]) for r in rows],[1,2,3])
        self.assertEqual(len([r for r in rows if int(r["Page"])<=2]),2)
    def test_pdf_findings_accepted(self):
        self.assertEqual(json.loads(m.PDFID91.read_text())["Identifier_Field"],"NOT_AVAILABLE")
        self.assertEqual(json.loads(m.PDFICB91.read_text())["Observed_ICB_Level"],"NOT_VERIFIED")
        self.assertEqual(json.loads(m.PDFROW91.read_text())["ROW_LEVEL_SECURITY_RECORDS"],"YES")
    def test_candidate_order(self):
        x=json.loads(m.SPEC.read_text())
        self.assertEqual([r["id"] for r in x["candidates"]],["A","B","C","D","E"])
        self.assertEqual(x["candidates"][0]["url"],m.A_URL)
        self.assertEqual(x["candidates"][1]["url"],m.B_URL)
        self.assertEqual(x["candidates"][3]["url"],m.D_URL)
        self.assertEqual(x["candidates"][4]["url"],m.E_URL)
    def test_field_semantics_strict(self):
        sem=m.field_semantics(["Company Name","SEDOL","ICB Industry Group"],"ICB")
        self.assertEqual(sem["identifiers"][0]["Type"],"SEDOL")
        self.assertEqual(sem["icb_group_name"][0]["Field"],"ICB Industry Group")
        sem2=m.field_semantics(["Company Name","Industry"],"ICB")
        self.assertEqual(sem2["identifiers"],[])
        self.assertEqual(sem2["icb_group_name"],[])
    def test_forbidden_zero_contract(self):
        x=json.loads(m.SPEC.read_text())["forbidden"]
        for k in ["alpha_vantage","yahoo_yfinance","eodhd","scalable","tradingview","wikipedia","per_security_fanout","frozen_49_linkage"]:
            self.assertTrue(x[k])
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
        reg=m.read_csv(m.REGISTRY)
        self.assertEqual(len(reg),1)
        self.assertEqual(reg[0]["Cohort"],"BR_IBRX100")
        self.assertEqual(reg[0]["Semantic_SHA256"],m.BR_SHA)
    def test_no_tw_canonical(self):
        self.assertFalse(any(m.CANON_DIR.glob("TW_TW50_*.csv")))

if __name__=="__main__":unittest.main()
