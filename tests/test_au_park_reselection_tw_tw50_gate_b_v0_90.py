#!/usr/bin/env python3
import importlib.util,json,unittest,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_park_reselection_tw_tw50_gate_b_v0_90.py"
s=importlib.util.spec_from_file_location("v090",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.90")
        self.assertEqual(m.REQUIRED_START_HEAD,"ef6029b3660b1f2a8bc29c016dc78d0188a775b1")
    def test_spec_scope(self):
        x=json.loads(m.SPEC.read_text())
        self.assertEqual(x["governance_authority"],"config/manager_governance_authority_G_SEC_06_v0.76.json")
        self.assertEqual(x["tw"]["target_gate"],"B")
        self.assertFalse(x["tw"]["frozen_49_linkage"])
        self.assertFalse(x["tw"]["per_security_fanout"])
        self.assertTrue(x["forbidden"]["alpha_vantage"])
        self.assertTrue(x["forbidden"]["tw_gate_e"])
        self.assertTrue(x["forbidden"]["tw_gate_f"])
        self.assertTrue(x["forbidden"]["tw_gate_h"])
        self.assertTrue(x["forbidden"]["canonical_materialization"])
    def test_gsec06(self):
        g=json.loads(m.GSEC06.read_text())
        self.assertEqual(g["authority_id"],"G-SEC-06")
        self.assertTrue(g["rules"]["external_consent_license_contractual_blocker_may_be_parked"])
        self.assertTrue(g["rules"]["parking_does_not_downgrade_proven_technical_gates"])
        self.assertTrue(g["rules"]["parked_cohort_excluded_from_active_next_cohort_selection"])
    def test_predecessor(self):
        s=json.loads(m.SUM89.read_text());c=json.loads(m.CHK89.read_text())
        self.assertEqual(s["verdict"],"BLOCKED_AU_SP_ASX200_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE_H")
        self.assertFalse(s["au_source_access_persistence_ready"])
        self.assertEqual(s["blocker"],"EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION")
        self.assertEqual(s["gics_policy_compatibility"],"NO")
        self.assertEqual(c["workflow_run_id"],m.V089_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V089_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V089_DIGEST)
    def test_park_start(self):
        rows=m.read_csv(m.PARK)
        by={r["Cohort"]:r["Execution_State"] for r in rows}
        self.assertEqual(by,{
          "IN_NIFTY50":"PARKED_EXTERNAL_AUTHORIZATION",
          "US_SP400":"PARKED_SOURCE_ACCESS",
          "US_SP500":"PARKED_SHARED_SOURCE_PREREQUISITE",
          "JP_N225":"PARKED_EXTERNAL_AUTHORIZATION"
        })
        self.assertEqual(m.sha_file(m.PARK),m.PARK_BEFORE_SHA)
    def test_selection_authority(self):
        mat=m.read_csv(m.MATRIX69)
        by={r["Cohort"]:r for r in mat}
        self.assertEqual(by["TW_TW50"]["Frozen_Rows"],"49")
        self.assertEqual(by["TW_TW50"]["Consecutive_Resolved_Gates"],"1")
        self.assertEqual(by["TW_TW50"]["Current_Earliest_Unresolved_Gate"],"B")
        self.assertEqual(by["CN_CSI300"]["Frozen_Rows"],"294")
        self.assertEqual(by["CN_CSI300"]["Consecutive_Resolved_Gates"],"1")
    def test_tw_inherited_authority(self):
        rows=m.read_csv(m.LEDGER62)
        tw=[r for r in rows if r["Cohort"]=="TW_TW50"][0]
        self.assertEqual(tw["Taxonomy_Identity"],"ICB")
        self.assertEqual(tw["A_Official_Source"],"PASS")
        self.assertEqual(tw["B_Bulk_Reproducible"],"NOT_VERIFIED")
        self.assertEqual(tw["C_Taxonomy_Identity"],"PASS")
        self.assertEqual(tw["D_Sector_Fields"],"PASS")
        self.assertEqual(tw["G_Provenance"],"PASS")
    def test_link_discovery(self):
        body=b'<html><a href="https://research.ftserussell.com/analytics/factsheets/Home/DownloadConstituentsWeights/?indexdetails=TW50">FTSE TWSE 50</a></html>'
        r={"ok":True,"body":body,"resolved_url":m.LSEG_SERIES,"url":m.LSEG_SERIES}
        links=m.discover_lseg_constituent_links(r)
        self.assertEqual(len(links),1)
        self.assertIn("DownloadConstituentsWeights",links[0]["URL"])
    def test_csv_parser_and_fields(self):
        b=b"SEDOL,ICB Industry Group,Weight\n1234567,Technology Hardware,10\n7654321,Banks,8\n"
        h,rows,fmt=m.parse_tabular(b,"text/csv","")
        self.assertEqual(h,["SEDOL","ICB Industry Group","Weight"])
        self.assertEqual(len(rows),2)
        d=m.detect_fields(h)
        self.assertEqual(d["identifier_candidates"][0]["type"],"SEDOL")
        self.assertEqual(d["icb_group_name_candidates"][0]["field"],"ICB Industry Group")
    def test_no_silent_sector_binding(self):
        d=m.detect_fields(["SEDOL","ICB Sector","Weight"])
        self.assertEqual(d["icb_group_name_candidates"],[])
        self.assertEqual(d["icb_group_code_candidates"],[])
        self.assertEqual(d["icb_other_fields"][0]["field"],"ICB Sector")
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        reg=m.read_csv(m.REGISTRY)
        self.assertEqual(reg[0]["Semantic_SHA256"],m.BR_SHA)
    def test_no_au_canonical(self):
        self.assertFalse(any(m.CANON_DIR.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":unittest.main()
