import json,csv
from pathlib import Path
D=Path("output_p0_breakout_compression_vcp_design_v1_04")
a=json.load(open("config/manager_governance_authority_G_P0_06_v1.04.json"))
assert a["Decision"]=="DESIGN_EVIDENCE_COMPLETE_NO_PARAMETER_PROMOTION"
assert a["DESIGN_BASE_ANCHORS"]==140451 and a["VALIDATION_SCORING_AUTHORIZED"]=="NO"
rows=list(csv.DictReader(open(D/"candidate_execution_counts_v1.04.csv")))
assert len(rows)==21
for r in rows:
    assert int(r["Hit_Count"])+int(r["False_Count"])+int(r["Not_Verified_Count"])==140451
assert min(int(r["Hit_Count"]) for r in rows)==13024
assert max(int(r["Hit_Count"]) for r in rows)==29428
assert {int(r["Not_Verified_Count"]) for r in rows}=={112}
rt=json.load(open(D/"drive_roundtrip_verification_v1.04.json"))
assert rt["result"]=="PASS" and rt["anchor_rows"]==140451 and rt["candidate_status_columns"]==21
p=json.load(open("config/p0_parameter_authority_current.json"))
assert p["Authority_ID"]=="G-P0-01" and p["p0_numeric_pass_thresholds"]==[] and p["promoted_lane_pass_rules"]==[]
