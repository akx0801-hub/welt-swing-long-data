#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_source_access_persistence_gate_h_v0_89.py"
s=importlib.util.spec_from_file_location("v089",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.89")
        self.assertEqual(m.REQUIRED_START_HEAD,"fb0a3ea7d9b1988e53290fd9ad9e7a9ff6488efd")
    def test_scope(self):
        x=json.loads(m.SPEC.read_text())
        self.assertTrue(x["scope"]["gate_h_only"])
        self.assertFalse(x["scope"]["gate_a_g_rerun_allowed"])
        self.assertFalse(x["scope"]["canonical_materialization_allowed"])
        self.assertFalse(x["scope"]["au_parking_allowed"])
        self.assertFalse(x["scope"]["reselection_allowed"])
        self.assertTrue(x["forbidden"]["alpha_vantage"])
    def test_governance(self):
        g=json.loads(m.GSEC05.read_text())
        self.assertEqual(g["authority_id"],"G-SEC-05")
        self.assertEqual(g["gate"],"H_ACCESS_PERSISTENCE")
        self.assertFalse(g["legal_opinion"])
        self.assertTrue(g["rules"]["raw_source_storage_not_required_for_pass"])
        self.assertTrue(g["rules"]["explicit_official_operational_restriction_requires_fail_closed"])
    def test_predecessor_files(self):
        s=json.loads(m.SUM88.read_text());c=json.loads(m.CHK88.read_text())
        self.assertEqual(s["verdict"],"PASS_AU_SP_ASX200_TECHNICAL_PROVENANCE_GATE_G")
        self.assertTrue(s["au_technical_provenance_ready"])
        self.assertEqual(s["provenance_complete"],63)
        self.assertEqual(s["cross_stage_conflicts"],0)
        self.assertEqual(c["workflow_run_id"],m.V088_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V088_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V088_DIGEST)
    def test_inherited_access_evidence(self):
        cap=json.loads(m.CAP82.read_text());replay=json.loads(m.REPLAY82.read_text());dl=json.loads(m.DL83.read_text())
        self.assertEqual(cap["Authentication"],"NONE")
        self.assertEqual(cap["Cookies_Preexisting"],"NO")
        self.assertEqual(cap["CAPTCHA_Bypass"],"NO")
        self.assertEqual(replay["DIRECT_HTTP_REPLAY"],"PASS")
        self.assertEqual(dl["Download_Status"],"PASS")
        self.assertIn("access_token=",dl["Download_URL"])
    def test_gics_access_evidence(self):
        x=json.loads(m.SRC85.read_text())
        self.assertEqual(x["HTTP_Status"],200)
        self.assertEqual(x["Reproducible"],"YES")
        self.assertEqual(x["SHA256"],m.MSCI_SHA)
    def test_technical_bounded_evidence(self):
        chain=m.read_csv(m.CHAIN88);inv=m.read_csv(m.INV85)
        self.assertEqual(len(chain),63)
        self.assertTrue(all(r["Classification_Source_Snapshot_SHA256"]==m.ASX_SHA for r in chain))
        self.assertTrue(all(r["Code_Authority_SHA256"]==m.MSCI_SHA for r in chain))
        self.assertEqual(len(inv),25)
    def test_provider_zero_baseline(self):
        p=m.provider_audit(2,2,1)
        z=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings",
           "per_security_web_fanout","Gate_A_rerun","Gate_B_rerun","Gate_C_rerun","Gate_D_rerun","Gate_E_rerun",
           "Gate_F_rerun","Gate_G_rerun","canonical_materialization","Sector_RS","P0","P1","P2",
           "core_ASX_classification_source_requests","core_MSCI_methodology_requests"]
        self.assertTrue(all(p[k]==0 for k in z))
        self.assertEqual(p["ASX_policy_requests"],2)
        self.assertEqual(p["MSCI_policy_requests"],2)
        self.assertEqual(p["SP_GICS_policy_requests"],1)
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
    def test_no_au_canonical(self):
        self.assertFalse(any(m.AU_CANON.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":unittest.main()
