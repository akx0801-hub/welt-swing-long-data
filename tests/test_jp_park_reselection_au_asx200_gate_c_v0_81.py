#!/usr/bin/env python3
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"scripts/jp_park_reselection_au_asx200_gate_c_v0_81.py"
spec=importlib.util.spec_from_file_location("v081",MOD)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class V081Tests(unittest.TestCase):
    def test_stage(self):
        self.assertEqual(mod.VERSION,"v0.81")
        self.assertEqual(mod.REQUIRED_START_HEAD,"a6b5a2e1f946bc8cd8615e37fe26efd82b77eb53")

    def test_governance_authorities(self):
        g6=json.loads(mod.GSEC06.read_text(encoding="utf-8"))
        g2=json.loads(mod.GSEC02.read_text(encoding="utf-8"))
        self.assertEqual(g6["authority_id"],"G-SEC-06")
        self.assertTrue(g6["rules"]["external_consent_license_contractual_blocker_may_be_parked"])
        self.assertTrue(g6["rules"]["parking_does_not_downgrade_proven_technical_gates"])
        self.assertEqual(g2["authority_id"],"G-SEC-02")
        self.assertTrue(g2["rules"]["crosswalk_forbidden"])
        self.assertEqual(g2["future_peer_group_key"],["Sector_Taxonomy","Sector_Code"])

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertTrue(s["scope"]["jp_park"])
        self.assertTrue(s["scope"]["post_park_reselection"])
        self.assertTrue(s["scope"]["au_gate_c_only"])
        self.assertFalse(s["scope"]["au_gate_d_allowed"])
        self.assertFalse(s["scope"]["au_gate_e_allowed"])
        self.assertFalse(s["scope"]["au_gate_f_allowed"])
        self.assertFalse(s["scope"]["canonical_materialization_allowed"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])
        self.assertTrue(s["forbidden"]["pdsc"])
        self.assertTrue(s["forbidden"]["sec_requests"])
        self.assertTrue(s["forbidden"]["nse_requests"])

    def test_v080_predecessor(self):
        s=json.loads(mod.SUM80.read_text(encoding="utf-8"))
        c=json.loads(mod.CHK80.read_text(encoding="utf-8"))
        self.assertEqual(s["verdict"],"BLOCKED_JP_N225_SOURCE_ACCESS_EVIDENCE_PERSISTENCE_GATE")
        self.assertFalse(s["jp_source_access_persistence_ready"])
        self.assertEqual(s["blocker"],"EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION")
        self.assertEqual((s["jp_gate_f_classified"],s["jp_gate_f_total"]),(197,197))
        self.assertEqual(c["workflow_run_id"],36333946734)
        self.assertEqual(c["artifact_id"],10936936683)

    def test_park_predecessor(self):
        rows=mod.read_csv(mod.PARK);by={r["Cohort"]:r for r in rows}
        self.assertEqual(by["IN_NIFTY50"]["Execution_State"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(by["US_SP400"]["Execution_State"],"PARKED_SOURCE_ACCESS")
        self.assertEqual(by["US_SP500"]["Execution_State"],"PARKED_SHARED_SOURCE_PREREQUISITE")
        if "JP_N225" in by:
            self.assertEqual(by["JP_N225"]["Execution_State"],"PARKED_EXTERNAL_AUTHORIZATION")
            self.assertEqual(by["JP_N225"]["Gate_H_Blocker"],"EXPLICIT_NIKKEI_SOURCE_POLICY_OPERATIONAL_RESTRICTION")
            self.assertEqual(by["JP_N225"]["Gate_F_Classified"],"197")
            self.assertEqual(mod.sha_file(mod.PARK),mod.PARK_APPLIED_SHA)
        else:
            self.assertEqual(mod.sha_file(mod.PARK),mod.PARK_BEFORE_SHA)

    def test_bulk_discovery_rejects_generic_navigation(self):
        p=mod.PageParser()
        p.feed('<a href="/issuers/listed-company-services">Listed Company Services</a>')
        page={"resolved_url":mod.DIRECTORY_URL,"body":b'<a href="/issuers/listed-company-services">Listed Company Services</a>'}
        d=mod.discover_bulk_url(page,p)
        self.assertEqual(d["status"],"NOT_FOUND")

    def test_bulk_discovery_accepts_exact_control(self):
        p=mod.PageParser()
        p.feed('<a href="/data/ASXListedCompanies.csv">All ASX Listed Companies .csv</a>')
        page={"resolved_url":mod.DIRECTORY_URL,"body":b'<a href="/data/ASXListedCompanies.csv">All ASX Listed Companies .csv</a>'}
        d=mod.discover_bulk_url(page,p)
        self.assertEqual(d["status"],"FOUND")
        self.assertTrue(d["selected_url"].endswith("ASXListedCompanies.csv"))
        self.assertTrue(mod.is_official_asx_url(d["selected_url"]))

    def test_au_historical_authority(self):
        r=json.loads(mod.RESEARCH62.read_text(encoding="utf-8"))["cohort_findings"]["AU_SP_ASX200"]
        self.assertEqual(r["taxonomy_identity"],"NOT_VERIFIED")
        self.assertEqual(r["gate_status"]["A"],"PASS")
        self.assertEqual(r["gate_status"]["B"],"PASS")
        self.assertEqual(r["gate_status"]["C"],"NOT_VERIFIED")
        self.assertEqual(r["earliest_blocker"],"SOURCE_NATIVE_TAXONOMY_IDENTITY_NOT_VERIFIED")

    def test_selection_inputs(self):
        rows=mod.read_csv(mod.MATRIX69);by={r["Cohort"]:r for r in rows}
        self.assertEqual(by["AU_SP_ASX200"]["Frozen_Rows"],"63")
        self.assertEqual(by["AU_SP_ASX200"]["Consecutive_Resolved_Gates"],"2")
        self.assertEqual(by["AU_SP_ASX200"]["Current_Earliest_Unresolved_Gate"],"C")
        self.assertEqual(by["CN_CSI300"]["Consecutive_Resolved_Gates"],"1")
        self.assertEqual(by["TW_TW50"]["Consecutive_Resolved_Gates"],"1")

    def test_bulk_field_detector(self):
        x=mod.find_industry_field(["Company name","ASX code","GICS industry group"])
        self.assertTrue(x["available"])
        self.assertEqual(x["kind"],"GICS_INDUSTRY_GROUP")
        self.assertEqual(x["position"],3)
        y=mod.find_industry_field(["ASX Code","Company Name","Industry","List Date"])
        self.assertTrue(y["available"])
        self.assertEqual(y["kind"],"INDUSTRY")

    def test_no_au_canonical(self):
        self.assertFalse(any(mod.AU_CANONICAL_GLOB.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":unittest.main()
