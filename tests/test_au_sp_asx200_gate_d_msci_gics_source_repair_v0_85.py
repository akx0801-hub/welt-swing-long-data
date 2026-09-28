#!/usr/bin/env python3
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/au_sp_asx200_gate_d_msci_gics_source_repair_v0_85.py"
s=importlib.util.spec_from_file_location("v085",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.VERSION,"v0.85")
        self.assertEqual(m.REQUIRED_START_HEAD,"c02fda68b5a377faafb75ef9304e120e271cb118")
    def test_spec_scope(self):
        x=json.loads(m.SPEC.read_text())
        self.assertTrue(x["scope"]["repair_v084_blocker_only"])
        self.assertFalse(x["scope"]["gate_e_allowed"])
        self.assertFalse(x["scope"]["gate_f_allowed"])
        self.assertFalse(x["scope"]["gate_h_allowed"])
        self.assertFalse(x["scope"]["frozen_63_linkage_allowed"])
        self.assertFalse(x["scope"]["canonical_materialization_allowed"])
        self.assertTrue(x["forbidden"]["alpha_vantage"])
        self.assertTrue(x["forbidden"]["pdsc"])
    def test_predecessor_files(self):
        s=json.loads(m.SUM84.read_text());c=json.loads(m.CHK84.read_text())
        self.assertEqual(s["verdict"],"BLOCKED_AU_SP_ASX200_GICS_INDUSTRY_GROUP_CODE_FEASIBILITY_GATE_D")
        self.assertEqual(s["blocker"],"GICS_OFFICIAL_CLASSIFICATION_STRUCTURE_NOT_REPRODUCIBLE")
        self.assertEqual(c["workflow_run_id"],m.V084_WORKFLOW)
        self.assertEqual(c["artifact_id"],m.V084_ARTIFACT)
        self.assertEqual(c["artifact_digest"],m.V084_DIGEST)
    def test_raw_inventory_27(self):
        r=m.read_csv(m.RAW84)
        self.assertEqual(len(r),27)
        self.assertEqual(len({m.nfc(x["ASX_Raw_Label"]) for x in r}),27)
        self.assertIn("Class Pend",{x["ASX_Raw_Label"] for x in r})
        self.assertIn("Not Applic",{x["ASX_Raw_Label"] for x in r})
    def test_counts_parser(self):
        t="designed with four levels of classifications that includes 11 Sectors, 25 Industry Groups, 74 Industries, and 163 Sub-Industries."
        self.assertEqual(m.parse_counts(t),{"SECTOR":11,"INDUSTRY_GROUP":25,"INDUSTRY":74,"SUB_INDUSTRY":163})
    def test_structure_parser(self):
        pages=[""]*13
        pages[4]="1.2 The GICS Structure\n10 Energy\n1010 Energy\n101010 Energy Equipment & Services\n10101010 Oil & Gas Drilling"
        pages[5]="15 Materials\n1510 Materials\n151010 Chemicals\n15101010 Commodity Chemicals"
        pages[11]="1.3 Philosophy and objectives of GICS"
        inv,meta=m.parse_structure(pages)
        self.assertEqual([(x["Official_GICS_Industry_Group_Code"],x["Official_GICS_Industry_Group_Label"]) for x in inv],[("1010","Energy"),("1510","Materials")])
        self.assertEqual(meta["Section_Bounds"],"PASS")
    def test_provider_zero(self):
        p=m.provider_audit()
        z=["Alpha_Vantage","Yahoo_yfinance","EODHD","Scalable","TradingView","Wikipedia","ETF_holdings","third_party_GICS_tables",
           "third_party_classification_databases","fuzzy_matching","semantic_classification_inference","cross_taxonomy_mapping","PDSC",
           "Frozen_63_linkage","per_security_fanout","AU_Gate_E","AU_Gate_F","Gate_H","canonical_materialization","Sector_RS","P0","P1","P2"]
        self.assertTrue(all(p[k]==0 for k in z))
        self.assertEqual(p["fresh_ASX_directory_requests"],0)
        self.assertEqual(p["official_MSCI_methodology_requests"],1)
    def test_immutability(self):
        self.assertEqual(m.sha_file(m.FROZEN),m.FROZEN_SHA)
        self.assertEqual(m.sha_file(m.V057),m.V057_SHA)
        self.assertEqual(m.sha_file(m.V058),m.V058_SHA)
        self.assertEqual(m.sha_file(m.PARK),m.PARK_SHA)
    def test_no_au_canonical(self):
        self.assertFalse(any(m.AU_CANON.glob("AU_SP_ASX200_*.csv")))

if __name__=="__main__":unittest.main()
