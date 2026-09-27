from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/in_nifty50_source_access_persistence_v0_75.py"
spec=importlib.util.spec_from_file_location("v075",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class INNifty50GateH075Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"b3c0110e1c4f0441447c9ad90515daeb36ac41ff")
        self.assertEqual(mod.V074_WORKFLOW,36317697732)
        self.assertEqual(mod.V074_ARTIFACT,10930917775)
        self.assertEqual(mod.V074_DIGEST,"sha256:472f856de56611cb7292075b96690557b5bc4df099c097a8b15b7202b7141a9e")
        self.assertEqual(mod.V074_COORD_SHA,"f870ee10d408565340307233b94ca082f8c7596fdf5acea10fda3f7ddff7a08e")

    def test_policy_urls(self):
        self.assertEqual(mod.TERMS_URL,"https://www.niftyindices.com/terms-of-use")
        self.assertEqual(mod.DISCLAIMER_URL,"https://www.niftyindices.com/disclaimer")

    def test_policy_marker_terms(self):
        body=b"<html><body>You may not conduct any systematic or automated data collection activities on our website without our express written consent.</body></html>"
        pages=[{"ok":True,"url":mod.TERMS_URL,"resolved_url":mod.TERMS_URL,"timestamp_utc":"x","status":200,"content_type":"text/html","bytes":len(body),"sha256":"x","body":body}]
        status,rows=mod.policy_review(pages)
        self.assertEqual(status,"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND")
        self.assertEqual(rows[0]["Review_Status"],"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND")
        self.assertEqual(rows[0]["Legal_Conclusion"],"NO")

    def test_policy_marker_disclaimer(self):
        body=b"<html><body>No part may be reproduced, stored in a retrieval system or transmitted without prior written permission.</body></html>"
        pages=[{"ok":True,"url":mod.DISCLAIMER_URL,"resolved_url":mod.DISCLAIMER_URL,"timestamp_utc":"x","status":200,"content_type":"text/html","bytes":len(body),"sha256":"x","body":body}]
        status,rows=mod.policy_review(pages)
        self.assertEqual(status,"EXPLICIT_OPERATIONAL_RESTRICTION_FOUND")
        self.assertEqual(rows[0]["Policy_Page"],"DISCLAIMER")

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["scope_cohort"],"IN_NIFTY50")
        self.assertEqual(s["scope_gate"],"H_ACCESS_PERSISTENCE_ONLY")
        self.assertTrue(s["policy_first_fail_closed"])
        self.assertFalse(s["core_source_refetch_if_explicit_policy_restriction_found"])
        self.assertEqual(s["max_policy_requests"],2)
        self.assertFalse(s["persist_raw_source_bodies"])
        self.assertFalse(s["persist_raw_policy_bodies"])
        self.assertFalse(s["gate_f_rerun_allowed"])
        self.assertFalse(s["canonical_materialization_allowed"])
        self.assertFalse(s["registry_update_allowed"])
        self.assertFalse(s["other_cohort_allowed"])
        self.assertFalse(s["pdsc_allowed"])
        self.assertFalse(s["authentication_bypass_allowed"])
        self.assertFalse(s["captcha_bypass_allowed"])
        self.assertFalse(s["alpha_vantage_allowed"])

    def test_gsec05(self):
        g=json.loads(mod.GSEC05.read_text(encoding="utf-8"))
        self.assertEqual(g["authority_id"],"G-SEC-05")
        self.assertFalse(g["legal_opinion"])
        self.assertTrue(g["rules"]["explicit_official_operational_restriction_requires_fail_closed"])
        self.assertTrue(g["rules"]["unknown_raw_redistribution_rights_alone_do_not_fail_when_raw_not_required"])

if __name__=="__main__":
    unittest.main()
