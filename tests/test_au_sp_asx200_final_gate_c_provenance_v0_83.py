#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_final_gate_c_provenance_v0_83.py"
s=importlib.util.spec_from_file_location("v083",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(m.VERSION,"v0.83");self.assertEqual(m.REQUIRED_START_HEAD,"5629089262fa1915c0f83e8281fe4f13509f2a08")
 def test_spec_scope(self):
  x=json.loads(m.SPEC.read_text());self.assertTrue(x["scope"]["final_gate_c_provenance_attempt"])
  self.assertEqual(x["scope"]["fresh_browser_contexts_max"],1)
  self.assertFalse(x["scope"]["au_gate_d_allowed"]);self.assertFalse(x["scope"]["au_gate_e_allowed"]);self.assertFalse(x["scope"]["au_gate_f_allowed"])
  self.assertTrue(x["forbidden"]["alpha_vantage"]);self.assertTrue(x["terminal_rule"]["no_further_au_gate_c_provenance_loop"])
 def test_predecessor(self):
  x=json.loads(m.SUM82.read_text());c=json.loads(m.CHK82.read_text())
  self.assertEqual(x["verdict"],m.V082_VERDICT);self.assertEqual(x["blocker"],m.V082_BLOCKER)
  self.assertEqual(x["tests"],{"failed":0,"passed":25,"total":25})
  self.assertEqual(c["workflow_run_id"],m.V082_WORKFLOW);self.assertEqual(c["artifact_id"],m.V082_ARTIFACT);self.assertEqual(c["artifact_digest"],m.V082_DIGEST)
 def test_v082_route(self):
  r=json.loads(m.ROUTE82.read_text())
  self.assertEqual(r["ASX_DIRECTORY_DATA_ROUTE_READY"],"YES");self.assertEqual(r["PUBLIC_BROWSER_REPRODUCIBLE"],"YES")
  self.assertEqual(r["Data_Route_Type"],"DETERMINISTIC_FINITE_PAGINATION");self.assertEqual(r["Complete_Directory_Record_Count"],1830)
 def test_v082_industry(self):
  s={r["Field_Name"]:r for r in m.read_csv(m.SCHEMA82)}
  self.assertEqual(int(s["industry"]["Null_Count"]),0);self.assertEqual(int(s["industry"]["Distinct_Value_Count"]),27)
 def test_sentinels(self):
  labels=[r["Distinct_Label"] for r in m.read_csv(m.LABELS82)]
  self.assertIn("Class Pend",labels);self.assertIn("Not Applic",labels)
 def test_repair_sources_exist(self):
  for p in [m.V08182,m.ENV82,m.DOM82,m.INT82,m.UP82,m.CAND82]:self.assertTrue(p.exists())
 def test_provider_zero(self):
  p=m.provider_audit()
  keys=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings","third_party_security_sector_databases",
        "semantic_sector_inference","fuzzy_matching","cross_taxonomy_mapping","company_name_linkage_for_Frozen","PDSC","price_OHLCV","news","trading_analysis",
        "per_security_fanout","AU_Gate_D","AU_Gate_E","AU_Gate_F","Sector_RS","P0","P1","P2","complete_74_page_reruns"]
  self.assertTrue(all(p[k]==0 for k in keys))
 def test_immutability_constants(self):
  self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA);self.assertEqual(m.sha_file(m.V057),m.V057_SHA);self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
  self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
 def test_terminal_gate(self):
  x=json.loads(m.SPEC.read_text())
  self.assertEqual(x["terminal_rule"]["if_blocked"],"AU_SP_ASX200 TAXONOMY-PROVENANCE PARK / ACTIVE-COHORT RESELECTION MANAGER GATE")
if __name__=="__main__":unittest.main()
