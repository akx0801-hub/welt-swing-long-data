from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/p0_frozen_1425_sector_taxonomy_selection_v0_61.py"
spec = importlib.util.spec_from_file_location("v061", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class SectorTaxonomySelectionV061Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD, "b5fda059940710d4e07928b6a8bc7b0b5d536a57")
        self.assertEqual(mod.V060_WORKFLOW_RUN, 36247871792)
        self.assertEqual(mod.V060_ARTIFACT_ID, 10907812456)
        self.assertEqual(mod.V060_ARTIFACT_DIGEST, "sha256:5caa8bd2a34b096e3b08e5ce9e41f3cabcea9b4b72d55060e20b8ec1bb78f500")
        self.assertEqual(mod.BLOCKER, "FULL_1425_COVERAGE_NOT_VERIFIED")
        self.assertEqual(mod.AUTHORITY_ID, "G-SEC-01")

    def test_manager_authority(self):
        a = mod.validate_manager_authority()
        self.assertTrue(a["rules"]["exactly_one_full_pass_required"])
        self.assertTrue(a["rules"]["mixed_taxonomy_forbidden_in_v0_61"])
        self.assertTrue(a["rules"]["crosswalk_forbidden_in_v0_61"])
        self.assertEqual(a["candidate_minimum"], ["GICS", "ICB"])

    def test_candidate_matrix(self):
        import json
        research = json.loads(mod.SOURCE_RESEARCH.read_text(encoding="utf-8"))
        rows = mod.candidate_matrix(research)
        self.assertEqual(len(rows), 14)
        for candidate in ("GICS", "ICB"):
            statuses = {r["Gate"]: r["Status"] for r in rows if r["Candidate"] == candidate}
            self.assertEqual(statuses["A_TAXONOMY_DEFINITION"], "PASS")
            self.assertEqual(statuses["B_SOURCE_CLASS"], "PASS")
            self.assertEqual(statuses["C_BULK_REPRODUCIBILITY"], "PASS")
            self.assertEqual(statuses["D_FROZEN_1425_COVERAGE_FEASIBILITY"], "NOT_VERIFIED")
            self.assertEqual(statuses["E_IDENTITY"], "NOT_VERIFIED")
            self.assertEqual(statuses["F_PROVENANCE"], "PASS")
            self.assertEqual(statuses["G_SOURCE_ACCESS_PERSISTENCE"], "NOT_VERIFIED")

    def test_coverage_fail_closed(self):
        frozen = mod.read_csv(mod.FROZEN)
        rows = mod.coverage_rows(frozen)
        self.assertEqual(len(rows), 2850)
        self.assertTrue(all(r["Coverage_Feasibility"] == "NOT_VERIFIED" for r in rows))
        self.assertTrue(all(r["Sector_Value_Materialized"] == "NO" for r in rows))

    def test_prohibited_provider_calls_zero(self):
        self.assertEqual(mod.provider_calls(), {
            "alpha_vantage": 0,
            "yahoo_yfinance": 0,
            "eodhd": 0,
            "scalable": 0,
            "market_price_ohlcv": 0,
            "news_trading": 0,
            "per_security_web_fanout": 0,
        })


if __name__ == "__main__":
    unittest.main()
