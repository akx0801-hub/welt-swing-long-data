from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/p0_frozen_1425_sector_metadata_contract_v0_60.py"
spec = importlib.util.spec_from_file_location("v060", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class SectorMetadataContractV060Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD, "3327e1245b0b0bf387445d78bfd2a3c66077538a")
        self.assertEqual(mod.V059_WORKFLOW_RUN, 36243521798)
        self.assertEqual(mod.V059_ARTIFACT_ID, 10906513700)
        self.assertEqual(mod.V059_ARTIFACT_DIGEST, "sha256:ed79a1cad64fa409f72fd21d23669d77b720a99c6f12e379fd48c1573a1f4ab0")
        self.assertEqual(mod.BLOCKER, "GOVERNANCE_DECISION_REQUIRED_CANONICAL_SECTOR_TAXONOMY")

    def test_contract_fails_closed_without_taxonomy_authority(self):
        c = mod.build_contract()
        self.assertFalse(c["sector_metadata_contract_ready"])
        self.assertEqual(c["canonical_taxonomy"], "NOT_DEFINED")
        self.assertEqual(c["canonical_sector_field"], "NOT_DEFINED")
        self.assertFalse(c["population_permitted"])
        self.assertFalse(c["sector_rs_materialization_permitted"])

    def test_v021_partial_semantics_are_inherited_not_promoted(self):
        c = mod.build_contract()
        inherited = c["inherited_explicit_authority"]
        self.assertEqual(inherited["required_identity_key"], "WS_ID")
        self.assertIn("Sector_Taxonomy", inherited["required_fields"])
        self.assertIn("Mapping_Status", inherited["required_fields"])
        self.assertIn("silent taxonomy mixing without crosswalk", inherited["prohibited_methods"])

    def test_taxonomy_matrix_authorizes_nothing(self):
        _, _, matrix = mod.authority_findings()
        self.assertEqual({r["Taxonomy_Candidate"] for r in matrix}, {
            "GICS", "ICB", "OTHER_SINGLE_TAXONOMY", "MIXED_TAXONOMIES_WITH_CROSSWALK"
        })
        self.assertTrue(all(r["Explicit_Selection_Authority"] == "NO" for r in matrix))
        self.assertTrue(all("NOT_AUTHORIZED" in r["Decision_v0_60"] for r in matrix))

    def test_historical_us_gics_not_promoted(self):
        _, discovery, _ = mod.authority_findings()
        self.assertTrue(discovery["v059_historical_us_gics_not_promoted"])
        self.assertFalse(discovery["v059_canonical_taxonomy_selected"])
        self.assertFalse(discovery["v059_canonical_sector_field_selected"])

    def test_provider_calls_zero(self):
        self.assertEqual(mod.provider_calls(), {
            "market": 0,
            "yahoo_yfinance": 0,
            "eodhd": 0,
            "alpha_vantage": 0,
            "scalable": 0,
            "external_market_or_reference_requests": 0,
        })

    def test_frozen_count(self):
        self.assertEqual(mod.frozen_count(), 1425)


if __name__ == "__main__":
    unittest.main()
