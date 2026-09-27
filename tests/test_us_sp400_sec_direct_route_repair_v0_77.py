from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/us_sp400_sec_direct_route_repair_v0_77.py"
spec=importlib.util.spec_from_file_location("v077",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class USSP400SECDirectRepairV077Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"17c21283f6c4fbdf524bc80324235c029018b6d6")
        self.assertEqual(mod.V076_WORKFLOW,36322252802)
        self.assertEqual(mod.V076_ARTIFACT,10932404865)
        self.assertEqual(mod.V076_DIGEST,"sha256:d43417c1e101e0cee2da785ea0c78f80305f9f0d8cd03e2498017427259b0f34")
        self.assertEqual(mod.SEC_URL,"https://www.sec.gov/files/company_tickers_exchange.json")

    def test_target(self):
        rows,dist=mod.reconstruct_target()
        self.assertEqual(len(rows),368)
        self.assertEqual(len({r["WS_ID"] for r in rows}),368)
        self.assertEqual(len({r["Security_Key"] for r in rows}),368)
        self.assertEqual(dist,{"XNAS":126,"XNYS":242})

    def test_sec_schema_parser(self):
        body=b'{"fields":["cik","name","ticker","exchange"],"data":[[1,"Issuer","ABC","NYSE"]]}'
        rows,fields,pos=mod.parse_sec(body)
        self.assertEqual(fields,["cik","name","ticker","exchange"])
        self.assertEqual(pos["ticker"],2)
        self.assertEqual(rows[0]["cik"],"1")
        self.assertEqual(rows[0]["exchange"],"NYSE")

    def test_normalization(self):
        self.assertEqual(mod.cmpnorm(" Nasdaq "),"nasdaq")
        self.assertEqual(mod.cmpnorm("NYSE"),"nyse")

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"US_SP400")
        self.assertEqual(s["scope_gate"],"E_SECURITY_IDENTITY_DIRECT_ROUTE_REPAIR_ONLY")
        self.assertEqual(s["expected_frozen_rows"],368)
        self.assertEqual(s["sec_direct_source"]["url"],mod.SEC_URL)
        self.assertFalse(s["sec_direct_source"]["documentation_page_success_prerequisite"])
        self.assertEqual(s["sec_direct_source"]["max_attempts"],3)
        self.assertEqual(s["sec_direct_source"]["retry_only_transient_statuses"],[429,500,502,503,504])
        self.assertFalse(s["ticker_join"]["company_name_join_allowed"])
        self.assertFalse(s["ticker_join"]["fuzzy_matching_allowed"])
        self.assertFalse(s["optional_bulk_submissions"]["primary_http_failure_alternative_forbidden"] is False)
        self.assertFalse(s["scope_boundaries"]["us_gate_f_allowed"])
        self.assertFalse(s["scope_boundaries"]["us_sp500_allowed"])
        self.assertFalse(s["scope_boundaries"]["canonical_materialization_allowed"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])

    def test_failure_semantics(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        c=s["v076_failure_semantics_correction"]
        self.assertEqual(c["v076_sec_source_record_count"],0)
        self.assertTrue(c["v076_not_found_368_is_not_security_absence_evidence"])
        self.assertEqual(c["direct_route_failure_row_status"],"NOT_VERIFIED")

if __name__=="__main__":
    unittest.main()
