#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_technical_provenance_gate_g_v0_88.py"
s=importlib.util.spec_from_file_location("v088",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.88")
        self.assertEqual(m.REQUIRED_START_HEAD,"3c71084e03fbd49c6ab5b34b03696c62aac765ad")
    def test_scope(self):
        x=json.loads(m.SPEC.read_text())
        self.assertTrue(x["scope"]["gate_g_only"])
        self.assertEqual(x["scope"]["external_source_requests"],0)
        self.assertFalse(x["scope"]["gate_h_allowed"])
        self.assertFalse(x["scope"]["policy_review_allowed"])
        self.assertFalse(x["scope"]["canonical_materialization_allowed"])
        self.assertFalse(x["scope"]["asx_refetch_allowed"])
        self.assertFalse(x["scope"]["msci_refetch_allowed"])
        self.assertTrue(x["forbidden"]["alpha_vantage"])
    def test_predecessor(self):
        s=json.loads(m.SUM87.read_text());c=json.loads(m.CHK87.read_text())
        self.assertEqual(s["verdict"],"PASS_AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F")
        self.assertTrue(s["au_exact_frozen_gics_classification_coverage_ready"])
        self.assertEqual(s["provably_classified"],63)
        self.assertEqual(s["formal_label_binding"],"63/63")
        self.assertEqual(s["source_native_code_coverage"],"63/63")
        self.assertEqual(c["workflow_run_id"],m.V087_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V087_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V087_DIGEST)
    def test_authorities(self):
        a=m.load_authorities()
        self.assertEqual(len(a["target"]),63)
        self.assertEqual(len(a["link"]),63)
        self.assertEqual(len(a["status"]),63)
        self.assertEqual(len(a["inventory"]),25)
        self.assertEqual(a["snapshot"]["CSV_SHA256"],m.ASX_SHA)
        self.assertEqual(a["snapshot"]["Retrieval_Timestamp_UTC"],m.ASX_RETRIEVED)
        self.assertEqual(a["src85"]["SHA256"],m.MSCI_SHA)
        self.assertEqual(a["src85"]["Retrieval_Timestamp_UTC"],m.MSCI_RETRIEVED)
    def test_stable_source_contract(self):
        self.assertEqual(m.ASX_SOURCE_NAME,"ASX_COMPANY_DIRECTORY_LISTED_COMPANIES_CSV")
        self.assertEqual(m.ASX_SOURCE_REFERENCE,"https://www.asx.com.au/markets/trade-our-cash-market/directory")
        self.assertEqual(m.ASX_SOURCE_VERSION,"SOURCE_SNAPSHOT_SHA256:"+m.ASX_SHA)
        self.assertEqual(m.ASX_EFFECTIVE_STATUS,"NO_EXPLICIT_EFFECTIVE_DATE_IN_PERSISTED_SOURCE")
    def test_code_authority_contract(self):
        self.assertEqual(m.MSCI_AUTHORITY_NAME,"MSCI_GICS_METHODOLOGY")
        self.assertEqual(m.MSCI_VERSION,"APRIL 2026")
        self.assertEqual(m.TAXONOMY_VERSION_STATUS,"CURRENT_MAINTAINED_NO_STATIC_VERSION")
    def test_provider_zero(self):
        p=m.provider_audit()
        z=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings",
           "ASX_network_requests","MSCI_network_requests","SP_network_requests","third_party_classification_sources",
           "company_name_linkage","fuzzy_matching","semantic_inference","cross_taxonomy_mapping","PDSC",
           "per_security_web_fanout","Gate_H","canonical_materialization","Sector_RS","P0","P1","P2"]
        self.assertTrue(all(p[k]==0 for k in z))
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
    def test_no_au_canonical(self):
        self.assertFalse(any(m.AU_CANON.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":unittest.main()
