#!/usr/bin/env python3
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/"scripts/au_sp_asx200_dynamic_directory_route_gate_c_v0_82.py"
spec=importlib.util.spec_from_file_location("v082",MOD)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class V082Tests(unittest.TestCase):
    def test_stage(self):
        self.assertEqual(mod.VERSION,"v0.82")
        self.assertEqual(mod.REQUIRED_START_HEAD,"c7fed3a3e4463229f17cb515d4abac5860cfc809")

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertTrue(s["scope"]["dynamic_directory_route_repair"])
        self.assertTrue(s["scope"]["gate_c_completion_if_route_ready"])
        self.assertFalse(s["scope"]["au_gate_d_allowed"])
        self.assertFalse(s["scope"]["au_gate_e_allowed"])
        self.assertFalse(s["scope"]["au_gate_f_allowed"])
        self.assertFalse(s["scope"]["canonical_materialization_allowed"])
        self.assertFalse(s["scope"]["park_reselection_execution_allowed"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])
        self.assertTrue(s["forbidden"]["per_security_requests"])
        self.assertTrue(s["forbidden"]["pdsc"])

    def test_v081_authority(self):
        s=json.loads(mod.SUM81.read_text(encoding="utf-8"))
        c=json.loads(mod.CHK81.read_text(encoding="utf-8"))
        self.assertEqual(s["verdict"],"BLOCKED_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C")
        self.assertFalse(s["au_source_native_taxonomy_identity_ready"])
        self.assertEqual(s["directory_bulk_route"],"FAIL")
        self.assertEqual(s["directory_industry_field"],"NOT_AVAILABLE")
        self.assertEqual(s["blocker"],"ASX_DIRECTORY_BULK_ROUTE_NOT_REPRODUCIBLE")
        self.assertEqual(c["workflow_run_id"],36337443965)
        self.assertEqual(c["artifact_id"],10937766315)
        self.assertEqual(c["artifact_digest"],mod.V081_DIGEST)

    def test_parked_cohorts(self):
        rows={r["Cohort"]:r for r in mod.read_csv(mod.PARK)}
        self.assertEqual(rows["IN_NIFTY50"]["Execution_State"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(rows["JP_N225"]["Execution_State"],"PARKED_EXTERNAL_AUTHORIZATION")
        self.assertEqual(rows["US_SP400"]["Execution_State"],"PARKED_SOURCE_ACCESS")
        self.assertEqual(rows["US_SP500"]["Execution_State"],"PARKED_SHARED_SOURCE_PREREQUISITE")
        self.assertEqual(mod.sha_file(mod.PARK),mod.PARK_SHA)

    def test_logical_route_ephemeral_values(self):
        a=mod.logical_route("https://data.example/a?token=abc&page=1","GET")
        b=mod.logical_route("https://data.example/a?page=2&token=xyz","GET")
        self.assertEqual(a,b)
        self.assertIn("?page&token",a)

    def test_csv_parser(self):
        raw=b"ASX code,Company name,GICS Industry Group\nAAA,Alpha,Materials\nBBB,Beta,Banks\n"
        p=mod.parse_dataset(raw,"text/csv","https://www.asx.com.au/x.csv")
        self.assertEqual(p["format"],"CSV")
        self.assertEqual(len(p["records"]),2)
        a=mod.schema_analysis(p["schema"],p["records"])
        self.assertIn("ASX code",a["code_fields"])
        self.assertIn("Company name",a["name_fields"])
        self.assertIn("GICS Industry Group",a["classification_fields"])

    def test_json_parser(self):
        raw=json.dumps({"data":{"items":[{"asxCode":"AAA","companyName":"Alpha","industry":"Materials"} for _ in range(25)]}}).encode()
        p=mod.parse_dataset(raw,"application/json","https://example/asx")
        self.assertEqual(p["format"],"JSON")
        self.assertEqual(len(p["records"]),25)
        a=mod.schema_analysis(p["schema"],p["records"])
        self.assertTrue(a["directory_like"])
        self.assertIn("industry",a["classification_fields"])

    def test_explicit_gics_field_contract(self):
        selected={"analysis":{"classification_fields":["GICS Industry Group"]}}
        ctx={"GICS_Expanded":True,"SPDJI_Observed":True,"MSCI_Observed":True}
        d=mod.field_taxonomy_decision(selected,ctx,{})
        self.assertTrue(d["ready"])
        self.assertEqual(d["taxonomy_identity"],"GICS")
        self.assertEqual(d["formal_level"],"INDUSTRY_GROUP")
        self.assertEqual(d["field_binding"],"PASS_DIRECT_SCHEMA")

    def test_generic_industry_fail_closed(self):
        selected={"analysis":{"classification_fields":["Industry"]}}
        ctx={"GICS_Expanded":True,"SPDJI_Observed":True,"MSCI_Observed":True}
        d=mod.field_taxonomy_decision(selected,ctx,{})
        self.assertFalse(d["ready"])
        self.assertEqual(d["blocker"],"ASX_DIRECTORY_INDUSTRY_FIELD_PROVENANCE_NOT_VERIFIED")

    def test_provider_audit_zero_forbidden(self):
        p=mod.provider_audit(2,1,2)
        zero_keys=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings",
                   "third_party_security_sector_databases","company_name_joins","fuzzy_matching","semantic_classification_inference",
                   "cross_taxonomy_mapping","PDSC","price_OHLCV","news","trading_analysis","per_security_requests",
                   "AU_Gate_D","AU_Gate_E","AU_Gate_F","Sector_RS","P0","P1","P2","NSE_requests","SEC_requests","Nikkei_classification_requests"]
        self.assertTrue(all(p[k]==0 for k in zero_keys))

    def test_no_au_canonical(self):
        self.assertFalse(any(mod.AU_CANONICAL_DIR.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":
    unittest.main()
