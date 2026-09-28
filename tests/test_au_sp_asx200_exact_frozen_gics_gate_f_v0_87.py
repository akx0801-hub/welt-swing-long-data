#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_exact_frozen_gics_gate_f_v0_87.py"
s=importlib.util.spec_from_file_location("v087",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.87")
        self.assertEqual(m.REQUIRED_START_HEAD,"16ca7cfc2148527f4e48bda642e7533831a716c5")
    def test_scope(self):
        x=json.loads(m.SPEC.read_text())
        self.assertTrue(x["scope"]["gate_f_only"])
        self.assertFalse(x["scope"]["gate_g_allowed"])
        self.assertFalse(x["scope"]["gate_h_allowed"])
        self.assertFalse(x["scope"]["canonical_materialization_allowed"])
        self.assertFalse(x["scope"]["pdsc_allowed"])
        self.assertTrue(x["forbidden"]["alpha_vantage"])
        self.assertTrue(x["forbidden"]["msci_methodology_requests"])
    def test_predecessor_files(self):
        s=json.loads(m.SUM86.read_text());c=json.loads(m.CHK86.read_text())
        self.assertEqual(s["verdict"],"PASS_AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E")
        self.assertTrue(s["au_deterministic_security_identity_linkage_ready"])
        self.assertEqual(s["exact_ticker_links"],63)
        self.assertEqual(s["source_ws_id_equality"],63)
        self.assertEqual(c["workflow_run_id"],m.V086_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V086_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V086_DIGEST)
    def test_target(self):
        target,a=m.rebuild_target()
        self.assertEqual(len(target),63)
        self.assertEqual(a["Exact_Match_To_v086_Target"],"YES")
        self.assertEqual(a["Unique_Security_Key"],63)
        self.assertEqual(a["Unique_Source_WS_ID"],63)
        self.assertEqual(a["Unique_Primary_Ticker"],63)
        self.assertEqual(a["Primary_MIC_XASX"],63)
        self.assertEqual(a["Source_WS_ID_Contract_PASS"],63)
    def test_formal_authority(self):
        rows,by_label,by_code=m.formal_authority()
        self.assertEqual(len(rows),25)
        self.assertEqual(len(by_label),25)
        self.assertEqual(len(by_code),25)
        self.assertTrue(all(len(k)==4 and k.isdigit() for k in by_code))
    def test_nonformal_authority(self):
        rows=m.read_csv(m.NON85)
        self.assertEqual({r["Label"] for r in rows},{"Class Pend","Not Applic"})
        self.assertTrue(all(r["Canonical_Code_Eligibility"]=="NO" for r in rows))
        self.assertTrue(all(r["PDSC_Eligibility"]=="NO" for r in rows))
    def test_provider_zero(self):
        p=m.provider_audit()
        z=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings",
           "third_party_classification_databases","company_name_linkage","fuzzy_matching","ticker_change_inference",
           "semantic_classification_inference","cross_taxonomy_mapping","PDSC","MSCI_methodology_requests",
           "per_security_web_fanout","Gate_G","Gate_H","canonical_materialization","Sector_RS","P0","P1","P2"]
        self.assertTrue(all(p[k]==0 for k in z))
        self.assertEqual(p["fresh_ASX_directory_snapshots"],1)
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
    def test_no_au_canonical(self):
        self.assertFalse(any(m.AU_CANON.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":unittest.main()
