from __future__ import annotations
import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/shared_sec_park_jp_n225_gate_d_v0_78.py"
spec=importlib.util.spec_from_file_location("v078",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

class SharedSECParkJPGateD078Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(mod.REQUIRED_START_HEAD,"c567c86f08ffd0b98aea83f0f01246335b7b9443")
        self.assertEqual(mod.V077_WORKFLOW,36324171127)
        self.assertEqual(mod.V077_ARTIFACT,10933038067)
        self.assertEqual(mod.V077_DIGEST,"sha256:68165105bdf9c666cac5912ee1a70446d26f971ff76d7fce0bdf3f5c7c174905")
        self.assertEqual(mod.TAXONOMY,"NIKKEI_36_INDUSTRY_AND_SECTOR")

    def test_post_park_selection(self):
        rows,sel=mod.post_park_selection()
        self.assertEqual(sel["Selected_Cohort"],"JP_N225")
        self.assertEqual(sel["Resolved_Gates_Before_Blocker"],3)
        self.assertEqual(sel["Earliest_Unresolved_Gate"],"D")
        by={r["Cohort"]:r for r in rows}
        self.assertTrue(by["IN_NIFTY50"]["Selection_State"].startswith("EXCLUDED_"))
        self.assertTrue(by["US_SP400"]["Selection_State"].startswith("EXCLUDED_"))
        self.assertTrue(by["US_SP500"]["Selection_State"].startswith("EXCLUDED_"))
        self.assertEqual(by["JP_N225"]["Consecutive_Resolved_Gates"],3)
        self.assertEqual(by["AU_SP_ASX200"]["Consecutive_Resolved_Gates"],2)

    def test_jp_count(self):
        self.assertEqual(mod.validate_jp_frozen_count(),197)

    def test_pdsc_deterministic(self):
        a=mod.pdsc("SECTOR","Technology")
        b=mod.pdsc("SECTOR","Technology")
        self.assertEqual(a,b)
        self.assertTrue(a.startswith("PDSC1:"))
        self.assertEqual(len(a),6+64)

    def test_synthetic_component_parser(self):
        sectors=[
          ("S1",[f"I{i}" for i in range(1,19)]),
          ("S2",[f"I{i}" for i in range(19,37)])
        ]
        # Synthetic parser test exercises mechanics, not production expected counts.
        list_html=""
        detail_html=""
        code=1000
        for s,inds in sectors:
            list_html+=s
            for ind in inds:
                list_html+=f'<a href="#{ind}">{ind}</a>'
                detail_html+=f'<h3>{ind}</h3><table><tr><th>Code</th><th>Company Name</th></tr><tr><td>{code}</td><td>X</td></tr></table>'
                code+=1
        html=f'<div>Industry List</div><div>Update：X</div>{list_html}{detail_html}'
        p=mod.parse_page(html.encode())
        result=mod.extract_component_structure(p)
        # Production validator intentionally rejects non-Nikkei 6-sector/225-security shape.
        self.assertFalse(result["valid"])

    def test_provider_calls_zero(self):
        self.assertTrue(all(v==0 for v in mod.provider_calls().values()))

    def test_spec_scope(self):
        s=json.loads(mod.SPEC.read_text(encoding="utf-8"))
        self.assertEqual(s["post_park_selection"]["expected_selected_cohort"],"JP_N225")
        self.assertEqual(s["jp_gate_d"]["cohort"],"JP_N225")
        self.assertEqual(s["jp_gate_d"]["frozen_rows"],197)
        self.assertEqual(s["jp_gate_d"]["taxonomy"],"NIKKEI_36_INDUSTRY_AND_SECTOR")
        self.assertEqual(s["jp_gate_d"]["max_official_requests"],3)
        self.assertFalse(s["shared_sec_parking"]["sec_requests_allowed"])
        self.assertFalse(s["jp_gate_d"]["gate_f_allowed"])
        self.assertFalse(s["scope_boundaries"]["jp_gate_e_execution_allowed"])
        self.assertFalse(s["scope_boundaries"]["jp_gate_f_execution_allowed"])
        self.assertFalse(s["scope_boundaries"]["us_gate_e_execution_allowed"])
        self.assertFalse(s["scope_boundaries"]["canonical_materialization_allowed"])
        self.assertTrue(s["forbidden"]["alpha_vantage"])
        self.assertTrue(s["forbidden"]["sec_requests"])

    def test_gsec07(self):
        g=json.loads(mod.GSEC07.read_text(encoding="utf-8"))
        self.assertEqual(g["authority_id"],"G-SEC-07")
        self.assertEqual(g["shared_sec_dependency"]["status"],"SHARED_SOURCE_ACCESS_BLOCKED")
        self.assertEqual(g["shared_sec_dependency"]["affected_cohorts"]["US_SP400"]["execution_state"],"PARKED_SOURCE_ACCESS")
        self.assertEqual(g["shared_sec_dependency"]["affected_cohorts"]["US_SP500"]["execution_state"],"PARKED_SHARED_SOURCE_PREREQUISITE")
        self.assertFalse(g["shared_sec_dependency"]["affected_cohorts"]["US_SP500"]["row_level_gate_execution_performed"])

if __name__=="__main__":
    unittest.main()
