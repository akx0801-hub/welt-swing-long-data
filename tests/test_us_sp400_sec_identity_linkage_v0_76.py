from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/us_sp400_sec_identity_linkage_v0_76.py"
spec=importlib.util.spec_from_file_location("v076",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class USSP400SECIdentityV076Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"40f261b29dd0e92dc79b976a0970f6ae8970e9e8")
        self.assertEqual(mod.V075_WORKFLOW,36319329798)
        self.assertEqual(mod.V075_ARTIFACT,10931349603)
        self.assertEqual(mod.V075_DIGEST,"sha256:670a2246c1186dddb7604b9eb9f349d980049a5e9f9f192540769aeb6fb25d4a")

    def test_target_reconstruction(self):
        rows,dist=mod.reconstruct_target()
        self.assertEqual(len(rows),368)
        self.assertEqual(len({r["WS_ID"] for r in rows}),368)
        self.assertEqual(len({r["Security_Key"] for r in rows}),368)
        self.assertEqual(sum(dist.values()),368)
        self.assertTrue(all(r["Primary_Universe_Index"]=="US_SP400" for r in rows))
        self.assertTrue(all(r["WS_ID"].startswith("WS:") for r in rows))

    def test_post_park_selection(self):
        calc,sel=mod.post_park_selection()
        self.assertEqual(sel["Selected_Cohort"],"US_SP400")
        self.assertEqual(sel["Resolved_Gates_Before_Blocker"],4)
        self.assertEqual(sel["Tie_Row_Counts"]["US_SP400"],368)
        self.assertEqual(sel["Tie_Row_Counts"]["US_SP500"],372)
        inrow=next(r for r in calc if r["Cohort"]=="IN_NIFTY50")
        self.assertEqual(inrow["Selection_Status"],"EXCLUDED_PARKED_EXTERNAL_AUTHORIZATION")

    def test_sec_discovery(self):
        html=b'<a href="/files/company_tickers_exchange.json">Ticker exchange</a>'
        page={"ok":True,"body":html,"resolved_url":"https://www.sec.gov/search-filings/edgar-application-programming-interfaces"}
        url,method=mod.discover_sec_ticker_exchange([page])
        self.assertEqual(url,"https://www.sec.gov/files/company_tickers_exchange.json")
        self.assertEqual(method,"DOCUMENTED_HREF")

    def test_iso_discovery(self):
        html=b'<a href="/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv">CSV</a>'
        page={"ok":True,"body":html,"resolved_url":"https://www.iso20022.org/market-identifier-codes"}
        url,method=mod.discover_iso_mic(page)
        self.assertEqual(url,"https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv")
        self.assertEqual(method,"OFFICIAL_LANDING_PAGE_HREF")

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["primary_scope_cohort"],"US_SP400")
        self.assertEqual(s["primary_scope_gate"],"E_SECURITY_IDENTITY_ONLY")
        self.assertEqual(s["expected_frozen_rows"],368)
        self.assertTrue(s["sec_documentation"]["discover_company_tickers_exchange_from_docs"])
        self.assertTrue(s["mic_authority"]["discover_mic_file_from_landing_page"])
        self.assertFalse(s["identifier_rules"]["company_name_join_allowed"])
        self.assertFalse(s["identifier_rules"]["fuzzy_matching_allowed"])
        self.assertFalse(s["scope_boundaries"]["us_gate_f_allowed"])
        self.assertFalse(s["scope_boundaries"]["canonical_materialization_allowed"])
        self.assertFalse(s["scope_boundaries"]["us_sp500_execution_allowed"])
        self.assertFalse(s["scope_boundaries"]["nifty_requests_allowed"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])

    def test_gsec06(self):
        g=json.loads(mod.GSEC06.read_text(encoding="utf-8"))
        self.assertEqual(g["authority_id"],"G-SEC-06")
        self.assertEqual(g["in_nifty50_authority"]["execution_state"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(g["in_nifty50_authority"]["gate_F_classified"],45)
        self.assertEqual(g["in_nifty50_authority"]["canonical_rows"],0)
        self.assertTrue(g["rules"]["parked_cohort_excluded_from_active_next_cohort_selection"])

if __name__=="__main__":
    unittest.main()
