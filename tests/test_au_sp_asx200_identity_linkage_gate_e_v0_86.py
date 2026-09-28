#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_identity_linkage_gate_e_v0_86.py"
s=importlib.util.spec_from_file_location("v086",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(m.VERSION,"v0.86");self.assertEqual(m.REQUIRED_START_HEAD,"62c1d0345c8955c949c134318f9329e12dca0469")
 def test_spec_scope(self):
  x=json.loads(m.SPEC.read_text())
  self.assertTrue(x["scope"]["gate_e_only"]);self.assertFalse(x["scope"]["gate_f_allowed"]);self.assertFalse(x["scope"]["gate_h_allowed"])
  self.assertFalse(x["scope"]["canonical_materialization_allowed"]);self.assertFalse(x["scope"]["pdsc_allowed"]);self.assertTrue(x["forbidden"]["alpha_vantage"])
 def test_predecessor(self):
  s=json.loads(m.SUM85.read_text());c=json.loads(m.CHK85.read_text())
  self.assertEqual(s["verdict"],"PASS_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D")
  self.assertTrue(s["au_sector_field_code_feasibility_ready"]);self.assertEqual(s["selected_code_strategy"],"SOURCE_NATIVE_GICS_CODE")
  self.assertEqual(c["workflow_run_id"],m.V085_WORKFLOW);self.assertEqual(c["artifact_id"],m.V085_ARTIFACT);self.assertEqual(c["artifact_digest"],m.V085_DIGEST)
 def test_target_contract(self):
  target,a=m.build_target()
  self.assertEqual(len(target),63);self.assertEqual(len({r["Security_Key"] for r in target}),63)
  self.assertEqual(len({r["Source_WS_ID"] for r in target}),63);self.assertEqual(len({r["Primary_Ticker"] for r in target}),63)
  self.assertTrue(all(r["Primary_MIC"]=="XASX" for r in target))
  self.assertTrue(all(r["Source_WS_ID"]=="WS:XASX:"+r["Primary_Ticker"] for r in target))
  self.assertEqual(a["Frozen_Physical_Has_Primary_Universe_Index"],"NO")
 def test_provider_zero(self):
  p=m.provider_audit()
  z=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings","third_party_identity_databases",
     "company_name_linkage","fuzzy_matching","ticker_change_inference","semantic_identity_inference","per_security_web_fanout","ASX_ISIN_fallback",
     "issuer_page_fallback","MSCI_methodology_requests","PDSC","AU_Gate_F","Gate_H","canonical_materialization","Sector_RS","P0","P1","P2"]
  self.assertTrue(all(p[k]==0 for k in z))
  self.assertEqual(p["fresh_ASX_directory_snapshots"],1)
 def test_row_hash_deterministic(self):
  r={"ASX code":"BHP","Company name":"BHP GROUP LIMITED"};s=["ASX code","Company name"]
  self.assertEqual(m.row_hash(r,s),m.row_hash(r,s))
 def test_immutability(self):
  self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA);self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
  self.assertEqual(m.sha_file(m.V058),m.V058_SHA);self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
 def test_no_au_canonical(self):
  self.assertFalse(any(m.AU_CANON.glob("AU_SP_ASX200_*.csv")))
if __name__=="__main__":unittest.main()
