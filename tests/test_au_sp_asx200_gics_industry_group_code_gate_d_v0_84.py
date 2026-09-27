#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_gics_industry_group_code_gate_d_v0_84.py"
s=importlib.util.spec_from_file_location("v084",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(m.VERSION,"v0.84");self.assertEqual(m.REQUIRED_START_HEAD,"258ecaa5e697f9bc51f0586bb6c2f2a3ee961647")
 def test_spec_scope(self):
  x=json.loads(m.SPEC.read_text())
  self.assertTrue(x["scope"]["gate_d_only"]);self.assertFalse(x["scope"]["gate_e_allowed"]);self.assertFalse(x["scope"]["gate_f_allowed"]);self.assertFalse(x["scope"]["gate_h_allowed"])
  self.assertFalse(x["scope"]["frozen_63_linkage_allowed"]);self.assertFalse(x["scope"]["canonical_materialization_allowed"]);self.assertTrue(x["forbidden"]["alpha_vantage"])
 def test_predecessor(self):
  x=json.loads(m.SUM83.read_text());c=json.loads(m.CHK83.read_text())
  self.assertEqual(x["verdict"],"PASS_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C")
  self.assertTrue(x["au_source_native_taxonomy_identity_ready"]);self.assertEqual(x["taxonomy_identity"],"GICS");self.assertEqual(x["formal_level"],"INDUSTRY_GROUP")
  self.assertEqual(x["download_classification_header"],"GICs industry group");self.assertEqual(c["workflow_run_id"],m.V083_WORKFLOW);self.assertEqual(c["artifact_id"],m.V083_ARTIFACT);self.assertEqual(c["artifact_digest"],m.V083_DIGEST)
 def test_pdsc_contract(self):
  code=m.pdsc("Banks")
  self.assertTrue(code.startswith("PDSC1:"));self.assertEqual(len(code),70)
  self.assertEqual(code,m.pdsc("Banks"))
 def test_code_extract(self):
  txt="GICS Industry Groups (Codes) Banks (4010) Financial Services (4020) Insurance (4030)"
  self.assertEqual(m.extract_code_for_label(txt,"Banks"),["4010"])
  self.assertEqual(m.extract_code_for_label(txt,"Financial Services"),["4020"])
 def test_provider_zero(self):
  p=m.provider_audit()
  z=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings","third_party_GICS_tables","third_party_security_sector_databases","company_name_Frozen_linkage","fuzzy_matching","semantic_classification_inference","cross_taxonomy_mapping","per_security_web_fanout","price_OHLCV","news","trading_analysis","AU_Gate_E","AU_Gate_F","Gate_H","canonical_materialization","Sector_RS","P0","P1","P2"]
  self.assertTrue(all(p[k]==0 for k in z))
 def test_immutability(self):
  self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA);self.assertEqual(m.sha_file(m.V057),m.V057_SHA);self.assertEqual(m.sha_file(m.V058),m.V058_SHA);self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
 def test_no_au_canonical(self):
  self.assertFalse(any(m.AU_CANON.glob("AU_SP_ASX200_*.csv")))
if __name__=="__main__":unittest.main()
