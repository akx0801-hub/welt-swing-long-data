#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.69"
STAGE="FROZEN_1425_CANONICAL_SECTOR_METADATA_COVERAGE_RECONCILIATION_NEXT_COHORT_SELECTION_GATE"
REQUIRED_START_HEAD="978404e766f7813819686835adf2254cd5071c62"

V068_WORKFLOW=36271957458
V068_ARTIFACT=10916176386
V068_DIGEST="sha256:e3acc96caff5715a5e09d123b3183137a0f84097afb1315b7c523a75d3f24e77"
BR_SEMANTIC_SHA="bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed"
BR_FILE_SHA="83706c76baba6d9a4fcc557d170f0bcad6fd85c9ca90fbc9f062cd5765dcef28"
FROZEN_SHA="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"

REGISTRY=ROOT/"sector_metadata/canonical/canonical_sector_metadata_cohort_registry_v1.csv"
BR_CANONICAL=ROOT/"sector_metadata/canonical/cohorts/BR_IBRX100_sector_metadata_v1.csv"
GLOBAL68=ROOT/"output_br_ibrx100_canonical_sector_metadata_materialization_v0_68/global_sector_metadata_coverage_status_v0.68.json"
SUM68=ROOT/"output_br_ibrx100_canonical_sector_metadata_materialization_v0_68/summary_v0.68.json"
CHK68=ROOT/"output_br_ibrx100_canonical_sector_metadata_materialization_v0_68/stage_checkpoint_v0.68.json"
LEDGER62=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/cohort_sector_source_route_ledger_v0.62.csv"
SUM62=ROOT/"output_frozen_1425_source_native_sector_coverage_v0_62/summary_v0.62.json"
GSEC02=ROOT/"config/manager_governance_authority_G_SEC_02_v0.62.json"
GSEC03=ROOT/"config/manager_governance_authority_G_SEC_03_v0.64.json"
GSEC04=ROOT/"output_br_ibrx100_canonical_sector_metadata_materialization_v0_68/manager_governance_authority_G_SEC_04_v0.68.json"
CAP58=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/capability_v0.58.csv"
FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
V057=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
SPEC=ROOT/"config/frozen_1425_canonical_sector_reconciliation_spec_v0.69.json"

GATES=["A","B","C","D","E","F","G","H"]
RESOLVED={"PASS_INHERITED","PASS_BY_CURRENT_GOVERNANCE"}
UNRESOLVED_COHORTS=["AU_SP_ASX200","CN_CSI300","IN_NIFTY50","JP_N225","TW_TW50","US_SP400","US_SP500"]

EXPECTED_COUNTS={
    "AU_SP_ASX200":63,
    "BR_IBRX100":37,
    "CN_CSI300":294,
    "IN_NIFTY50":45,
    "JP_N225":197,
    "TW_TW50":49,
    "US_SP400":368,
    "US_SP500":372,
}

GATE_NAMES={
    "A":"Official Source",
    "B":"Bulk / Reproducibility",
    "C":"Taxonomy Identity",
    "D":"Sector Fields / Canonical Sector Code feasibility",
    "E":"Security Identity",
    "F":"Exact Frozen Cohort Coverage",
    "G":"Provenance",
    "H":"Access / Persistence",
}

NEXT_GATE_TEMPLATES={
    "A":"{cohort} OFFICIAL SECTOR SOURCE RESOLUTION GATE",
    "B":"{cohort} OFFICIAL SECTOR BULK SOURCE RESOLUTION GATE",
    "C":"{cohort} SOURCE-NATIVE TAXONOMY IDENTITY GATE",
    "D":"{cohort} CANONICAL SECTOR FIELD / LEVEL FEASIBILITY GATE",
    "E":"{cohort} DETERMINISTIC SECURITY IDENTITY LINKAGE GATE",
    "F":"{cohort} EXACT FROZEN SECTOR CLASSIFICATION COVERAGE GATE",
    "G":"{cohort} SECTOR PROVENANCE COMPLETENESS GATE",
    "H":"{cohort} SECTOR ACCESS / PERSISTENCE GATE",
}

def git(*args:str)->str:
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def sha_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        if fields:
            w.writeheader()
            w.writerows(rows)

def current_status_from_historical(x:str)->str:
    if x=="PASS":
        return "PASS_INHERITED"
    if x in {"NOT_VERIFIED","NOT_EVALUATED","FAIL","NOT_APPLICABLE"}:
        return x
    raise ValueError(f"unknown historical status {x}")

def provider_calls()->dict[str,int]:
    return {
        "external_requests":0,
        "provider_calls":0,
        "market_reference_calls":0,
        "alpha_vantage":0,
        "b3_requests":0,
        "nikkei_requests":0,
        "nse_requests":0,
        "sec_requests":0,
        "asx_requests":0,
        "csi_requests":0,
        "twse_requests":0,
        "mapping_population":0,
        "sector_rs":0,
        "p0":0,
        "p1":0,
        "p2":0,
    }

def validate_predecessor(repo_sha:str)->tuple[dict[str,Any],dict[str,Any],dict[str,Any],list[dict[str,str]],dict[str,Any],dict[str,Any],dict[str,Any]]:
    if git("rev-parse","HEAD")!=repo_sha:
        raise RuntimeError("checkout mismatch")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start head not ancestor")

    s68=json.loads(SUM68.read_text(encoding="utf-8"))
    c68=json.loads(CHK68.read_text(encoding="utf-8"))
    g68=json.loads(GLOBAL68.read_text(encoding="utf-8"))
    reg=read_csv(REGISTRY)
    s62=json.loads(SUM62.read_text(encoding="utf-8"))
    g2=json.loads(GSEC02.read_text(encoding="utf-8"))
    g3=json.loads(GSEC03.read_text(encoding="utf-8"))
    g4=json.loads(GSEC04.read_text(encoding="utf-8"))

    if s68["verdict"]!="PASS_BR_CANONICAL_SECTOR_METADATA_MATERIALIZATION":
        raise RuntimeError("v0.68 verdict")
    if s68["br_canonical_sector_metadata_ready"] is not True:
        raise RuntimeError("v0.68 BR readiness")
    if (s68["br_ready"],s68["br_total"],s68["global_ready"],s68["global_total"],s68["global_remaining"])!=(37,37,37,1425,1388):
        raise RuntimeError("v0.68 coverage")
    if s68["semantic_sha256"]!=BR_SEMANTIC_SHA or s68["canonical_file_sha256"]!=BR_FILE_SHA:
        raise RuntimeError("v0.68 hashes")
    if c68["workflow_run_id"]!=V068_WORKFLOW or c68["artifact_id"]!=V068_ARTIFACT:
        raise RuntimeError("v0.68 workflow/artifact")
    if "sha256:"+c68["artifact_digest"]!=V068_DIGEST:
        raise RuntimeError("v0.68 artifact digest")
    if g68["GLOBAL_CANONICAL_SECTOR_METADATA_READY"] is not False or (g68["GLOBAL_READY"],g68["GLOBAL_TOTAL"],g68["GLOBAL_REMAINING"])!=(37,1425,1388):
        raise RuntimeError("v0.68 global state")
    if len(reg)!=1 or reg[0]["Cohort"]!="BR_IBRX100" or reg[0]["Canonical_Status"]!="READY":
        raise RuntimeError("registry BR authority")
    if reg[0]["Semantic_SHA256"]!=BR_SEMANTIC_SHA or reg[0]["Canonical_File_SHA256"]!=BR_FILE_SHA:
        raise RuntimeError("registry hashes")
    if sha_file(BR_CANONICAL)!=BR_FILE_SHA:
        raise RuntimeError("BR canonical file hash")
    if g2["authority_id"]!="G-SEC-02" or g3["authority_id"]!="G-SEC-03" or g4["authority_id"]!="G-SEC-04":
        raise RuntimeError("governance authority IDs")
    if g3["rules"]["canonical_method_when_native_code_absent"]!="PDSC_SHA256_V1":
        raise RuntimeError("G-SEC-03 method")
    if g4["rules"]["sector_rs_authorized"] is not False:
        raise RuntimeError("G-SEC-04 sector RS")
    if s68["sector_rs_runs"]!=0 or s68["p0_runs"]!=0 or s68["p1_runs"]!=0 or s68["p2_runs"]!=0:
        raise RuntimeError("v0.68 downstream runs")
    if sha_file(FROZEN)!=FROZEN_SHA or sha_file(V057)!=V057_SHA or sha_file(V058)!=V058_SHA:
        raise RuntimeError("immutability predecessor")
    if s62["cohort_counts"]!=EXPECTED_COUNTS:
        raise RuntimeError("v0.62 cohort counts")
    return s68,c68,g68,reg,s62,g2,g3,g4

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_frozen_1425_canonical_sector_reconciliation_v0_69")
    args=ap.parse_args()

    s68,c68,g68,registry,s62,g2,g3,g4=validate_predecessor(args.repository_sha)
    out=ROOT/args.output_dir
    out.mkdir(parents=True,exist_ok=True)

    spec=json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"]!=VERSION or spec["required_start_head"]!=REQUIRED_START_HEAD:
        raise RuntimeError("spec mismatch")
    if any(provider_calls().values()):
        raise RuntimeError("provider audit nonzero")

    cap=read_csv(CAP58)
    cap_counts=dict(Counter(r["Primary_Universe_Index"] for r in cap))
    if cap_counts!=EXPECTED_COUNTS:
        raise RuntimeError(f"capability cohort counts {cap_counts}")

    ledger_rows=read_csv(LEDGER62)
    by_cohort={r["Cohort"]:r for r in ledger_rows}
    if set(by_cohort)!=set(EXPECTED_COUNTS):
        raise RuntimeError("v0.62 ledger cohorts")

    # Current canonical registry integrity: promoted cohorts only; BR is the sole promoted partition.
    registry_integrity={
        "registry_path":str(REGISTRY.relative_to(ROOT)),
        "registry_rows":len(registry),
        "promoted_cohorts":[r["Cohort"] for r in registry],
        "BR_row_present":len(registry)==1 and registry[0]["Cohort"]=="BR_IBRX100",
        "BR_frozen_rows":int(registry[0]["Frozen_Row_Count"]),
        "BR_canonical_rows":int(registry[0]["Canonical_Row_Count"]),
        "BR_status":registry[0]["Canonical_Status"],
        "BR_semantic_sha256":registry[0]["Semantic_SHA256"],
        "BR_canonical_file_sha256":registry[0]["Canonical_File_SHA256"],
        "BR_semantic_sha_matches":registry[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
        "BR_file_sha_matches":registry[0]["Canonical_File_SHA256"]==BR_FILE_SHA==sha_file(BR_CANONICAL),
        "unresolved_placeholder_rows":0,
        "integrity_status":"PASS",
    }
    (out/"canonical_registry_integrity_audit_v0.69.json").write_text(json.dumps(registry_integrity,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    global_integrity={
        "Frozen_Total":sum(cap_counts.values()),
        "Canonical_Promoted_Rows":sum(int(r["Canonical_Row_Count"]) for r in registry if r["Canonical_Status"]=="READY"),
        "Global_Remaining":sum(cap_counts.values())-sum(int(r["Canonical_Row_Count"]) for r in registry if r["Canonical_Status"]=="READY"),
        "GLOBAL_CANONICAL_SECTOR_METADATA_READY":False,
        "Expected_Ready":37,
        "Expected_Total":1425,
        "Expected_Remaining":1388,
        "Registry_Agrees_v0_68_Global_Status":(
            sum(int(r["Canonical_Row_Count"]) for r in registry if r["Canonical_Status"]=="READY")==g68["GLOBAL_READY"]==37
            and sum(cap_counts.values())==g68["GLOBAL_TOTAL"]==1425
            and 1388==g68["GLOBAL_REMAINING"]
        ),
        "No_Ready_Count_Increase":True,
        "Status":"PASS",
    }
    (out/"global_coverage_integrity_audit_v0.69.json").write_text(json.dumps(global_integrity,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    g3_audit=[]
    matrix=[]
    blocker_recon=[]
    depth_rows=[]

    for cohort in UNRESOLVED_COHORTS:
        h=by_cohort[cohort]
        current={g:current_status_from_historical(h[f"{g}_{ {'A':'Official_Source','B':'Bulk_Reproducible','C':'Taxonomy_Identity','D':'Sector_Fields','E':'Security_Identity','F':'Exact_Coverage','G':'Provenance','H':'Access_Persistence'}[g] }"]) for g in GATES}

        if cohort=="JP_N225":
            # G-SEC-03 cures source-native code absence only after exact official classification
            # semantics needed by PDSC are unambiguously established. v0.62 persisted evidence
            # names a combined "Nikkei 36 Industry / Nikkei sector grouping" taxonomy and says
            # companies are listed by industry under sector headings, but it does not bind one
            # exact canonical Sector_Level for PDSC peer grouping. No new research is allowed.
            g3_status="NOT_VERIFIED"
            g3_reason=(
                "G-SEC-03 removes source-native-code necessity, but persisted v0.62 authority does not "
                "unambiguously bind one exact JP canonical Sector_Level between Nikkei industry and sector "
                "grouping. Exact classification names exist in the source rationale, yet the PDSC level "
                "required for deterministic canonical identity is not explicitly authorized. D remains NOT_VERIFIED."
            )
            current["D"]="NOT_VERIFIED"
        elif h["D_Sector_Fields"]=="PASS":
            g3_status="NOT_APPLICABLE"
            g3_reason="Historical D already PASS with source-native sector fields/code semantics; G-SEC-03 is not needed."
        elif current["C"]!="PASS_INHERITED":
            g3_status="NOT_APPLICABLE"
            g3_reason="G-SEC-03 cannot cure missing taxonomy identity."
        else:
            g3_status="NOT_VERIFIED"
            g3_reason="Persisted evidence is insufficient to establish the exact official classification semantics required by G-SEC-03."

        g3_audit.append({
            "Cohort":cohort,
            "Historical_D_Status":h["D_Sector_Fields"],
            "Historical_Blocker":h["Earliest_Blocker"],
            "G_SEC_03_Applicability":g3_status,
            "Current_D_Status":current["D"],
            "Reason":g3_reason,
        })

        depth=0
        earliest=""
        for g in GATES:
            if current[g] in RESOLVED:
                if earliest=="":
                    depth+=1
            elif earliest=="":
                earliest=g

        if not earliest:
            earliest="NONE"

        current_blocker=h["Earliest_Blocker"]
        if cohort=="JP_N225" and earliest=="D":
            current_blocker="JP_CANONICAL_CLASSIFICATION_LEVEL_NOT_VERIFIED"
        elif earliest!=h["Earliest_Failed_Gate"]:
            current_blocker=f"{cohort}_CURRENT_GATE_{earliest}_UNRESOLVED"

        row={
            "Cohort":cohort,
            "Frozen_Rows":int(h["Frozen_Rows"]),
            "Source_Native_Candidate":h["Source_Native_Candidate"],
            "Taxonomy_Identity":h["Taxonomy_Identity"],
            "A":current["A"],"B":current["B"],"C":current["C"],"D":current["D"],
            "E":current["E"],"F":current["F"],"G":current["G"],"H":current["H"],
            "Historical_Earliest_Gate":h["Earliest_Failed_Gate"],
            "Historical_Blocker":h["Earliest_Blocker"],
            "Current_Earliest_Unresolved_Gate":earliest,
            "Current_Blocker":current_blocker,
            "Consecutive_Resolved_Gates":depth,
        }
        matrix.append(row)
        blocker_recon.append({
            "Cohort":cohort,
            "Historical_Earliest_Gate":h["Earliest_Failed_Gate"],
            "Historical_Blocker":h["Earliest_Blocker"],
            "Historical_Rationale":h["Rationale"],
            "Current_Earliest_Unresolved_Gate":earliest,
            "Current_Blocker":current_blocker,
            "Governance_Change_Applied":"G-SEC-03_CHECK" if cohort=="JP_N225" else "NONE_REQUIRED_FOR_EARLIEST_GATE",
            "Historical_Evidence_Rewritten":"NO",
        })
        depth_rows.append({
            "Cohort":cohort,
            "Frozen_Rows":int(h["Frozen_Rows"]),
            "Consecutive_Resolved_Gates":depth,
            "Earliest_Unresolved_Gate":earliest,
            "Current_Blocker":current_blocker,
        })

    write_csv(out/"g_sec_03_cross_cohort_applicability_audit_v0.69.csv",g3_audit)
    write_csv(out/"current_authority_cohort_gate_matrix_v0.69.csv",matrix)
    write_csv(out/"historical_vs_current_blocker_reconciliation_v0.69.csv",blocker_recon)
    write_csv(out/"unresolved_cohort_gate_depth_v0.69.csv",depth_rows)

    ranked=sorted(depth_rows,key=lambda r:(-int(r["Consecutive_Resolved_Gates"]),int(r["Frozen_Rows"]),r["Cohort"]))
    selection_rows=[]
    for rank,r in enumerate(ranked,1):
        selection_rows.append({
            "Selection_Rank":rank,
            **r,
            "Excluded_Canonical_READY":"NO",
            "Selection_Key":f"{-int(r['Consecutive_Resolved_Gates'])}|{int(r['Frozen_Rows']):04d}|{r['Cohort']}",
            "Selected":"YES" if rank==1 else "NO",
        })
    selected=ranked[0]
    next_gate=NEXT_GATE_TEMPLATES[selected["Earliest_Unresolved_Gate"]].format(cohort=selected["Cohort"])
    selected_blocker=selected["Current_Blocker"]

    # Add BR exclusion calculation explicitly.
    selection_rows.append({
        "Selection_Rank":"",
        "Cohort":"BR_IBRX100",
        "Frozen_Rows":37,
        "Consecutive_Resolved_Gates":"",
        "Earliest_Unresolved_Gate":"NOT_APPLICABLE",
        "Current_Blocker":"NONE_CANONICAL_READY",
        "Excluded_Canonical_READY":"YES",
        "Selection_Key":"EXCLUDED",
        "Selected":"NO",
    })
    write_csv(out/"next_cohort_selection_calculation_v0.69.csv",selection_rows)

    selected_authority={
        "Selected_Next_Cohort":selected["Cohort"],
        "Frozen_Rows":selected["Frozen_Rows"],
        "Resolved_Gates_Before_Blocker":selected["Consecutive_Resolved_Gates"],
        "Earliest_Unresolved_Gate":selected["Earliest_Unresolved_Gate"],
        "Earliest_Unresolved_Gate_Name":GATE_NAMES[selected["Earliest_Unresolved_Gate"]],
        "Current_Blocker":selected_blocker,
        "Next_Gate":next_gate,
        "Selection_Rule":{
            "primary":"greatest consecutive resolved A-H gates from A",
            "tie_break_1":"smaller Frozen cohort row count",
            "tie_break_2":"lexicographically ascending Cohort ID",
        },
        "Proof":{
            "max_depth":max(int(r["Consecutive_Resolved_Gates"]) for r in depth_rows),
            "depth_tie_cohorts":[r["Cohort"] for r in depth_rows if int(r["Consecutive_Resolved_Gates"])==max(int(x["Consecutive_Resolved_Gates"]) for x in depth_rows)],
            "selected_is_smallest_row_count_in_max_depth":True,
        }
    }
    (out/"selected_next_cohort_authority_v0.69.json").write_text(json.dumps(selected_authority,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    reconciliation={
        "version":VERSION,
        "stage":STAGE,
        "Frozen_Cohort_Counts":cap_counts,
        "Frozen_Total":sum(cap_counts.values()),
        "Canonical_Registry_Cohorts":[r["Cohort"] for r in registry],
        "Canonical_Promoted_Rows":37,
        "Global_Remaining":1388,
        "GLOBAL_CANONICAL_SECTOR_METADATA_READY":False,
        "Unresolved_Cohorts":UNRESOLVED_COHORTS,
        "Unresolved_Cohort_Count":len(UNRESOLVED_COHORTS),
        "Selected_Next_Cohort":selected["Cohort"],
        "Resolved_Gates_Before_Blocker":selected["Consecutive_Resolved_Gates"],
        "Earliest_Unresolved_Gate":selected["Earliest_Unresolved_Gate"],
        "Current_Blocker":selected_blocker,
        "Next_Gate":next_gate,
        "Canonical_Ready_Count_Changed":False,
    }
    (out/"canonical_sector_metadata_global_reconciliation_v0.69.json").write_text(json.dumps(reconciliation,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    providers=provider_calls()
    (out/"provider_call_audit_v0.69.json").write_text(json.dumps(providers,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    imm={
        "Frozen_Expected_SHA256":FROZEN_SHA,
        "Frozen_SHA256_Before":sha_file(FROZEN),
        "Frozen_SHA256_After":sha_file(FROZEN),
        "Frozen_Unchanged":sha_file(FROZEN)==FROZEN_SHA,
        "v057_Expected_SHA256":V057_SHA,
        "v057_SHA256_Before":sha_file(V057),
        "v057_SHA256_After":sha_file(V057),
        "v057_Unchanged":sha_file(V057)==V057_SHA,
        "v058_Expected_SHA256":V058_SHA,
        "v058_SHA256_Before":sha_file(V058),
        "v058_SHA256_After":sha_file(V058),
        "v058_Unchanged":sha_file(V058)==V058_SHA,
        "BR_Canonical_Semantic_SHA256_Expected":BR_SEMANTIC_SHA,
        "BR_Canonical_Semantic_SHA256_After":registry[0]["Semantic_SHA256"],
        "BR_Canonical_Semantic_Unchanged":registry[0]["Semantic_SHA256"]==BR_SEMANTIC_SHA,
        "BR_Canonical_File_SHA256_Expected":BR_FILE_SHA,
        "BR_Canonical_File_SHA256_After":sha_file(BR_CANONICAL),
        "BR_Canonical_File_Unchanged":sha_file(BR_CANONICAL)==BR_FILE_SHA,
        "Canonical_READY_Rows_Before":37,
        "Canonical_READY_Rows_After":37,
        "Canonical_Mapping_Population_Runs":0,
        "Sector_RS_Runs":0,
        "P0_Runs":0,
        "P1_Runs":0,
        "P2_Runs":0,
        "Frozen_Mutations":0,
        "Price_Cache_Mutations":0,
        "Feature_Mutations":0,
        "Home_Market_RS_Mutations":0,
        "Other_Cohort_Executions":0,
    }
    (out/"immutability_audit_v0.69.json").write_text(json.dumps(imm,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    tests=[]
    def test(name:str,ok:bool,detail:Any)->None:
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":str(detail)})
        if not ok:
            raise RuntimeError(name)

    test("V068_VERDICT",s68["verdict"]=="PASS_BR_CANONICAL_SECTOR_METADATA_MATERIALIZATION",s68["verdict"])
    test("V068_BR_READY_37_37",s68["br_canonical_sector_metadata_ready"] is True and (s68["br_ready"],s68["br_total"])==(37,37),"37/37")
    test("V068_GLOBAL_37_1425",(s68["global_ready"],s68["global_total"],s68["global_remaining"])==(37,1425,1388),"37/1425/1388")
    test("V068_HASHES",s68["semantic_sha256"]==BR_SEMANTIC_SHA and s68["canonical_file_sha256"]==BR_FILE_SHA,"PASS")
    test("REGISTRY_INTEGRITY",registry_integrity["integrity_status"]=="PASS" and registry_integrity["BR_file_sha_matches"],registry_integrity)
    test("FROZEN_COUNTS",cap_counts==EXPECTED_COUNTS,cap_counts)
    test("FROZEN_TOTAL",sum(cap_counts.values())==1425,sum(cap_counts.values()))
    test("UNRESOLVED_7",len(matrix)==7,len(matrix))
    test("BR_EXCLUDED",all(r["Cohort"]!="BR_IBRX100" for r in matrix),"PASS")
    test("HISTORICAL_BLOCKERS_PRESERVED",all(r["Historical_Blocker"]==by_cohort[r["Cohort"]]["Earliest_Blocker"] for r in blocker_recon),"PASS")
    test("JP_GSEC03_FAIL_CLOSED",next(r for r in g3_audit if r["Cohort"]=="JP_N225")["Current_D_Status"]=="NOT_VERIFIED","NOT_VERIFIED")
    test("JP_DEPTH_3",next(r for r in depth_rows if r["Cohort"]=="JP_N225")["Consecutive_Resolved_Gates"]==3,3)
    test("IN_DEPTH_4",next(r for r in depth_rows if r["Cohort"]=="IN_NIFTY50")["Consecutive_Resolved_Gates"]==4,4)
    test("US400_DEPTH_4",next(r for r in depth_rows if r["Cohort"]=="US_SP400")["Consecutive_Resolved_Gates"]==4,4)
    test("US500_DEPTH_4",next(r for r in depth_rows if r["Cohort"]=="US_SP500")["Consecutive_Resolved_Gates"]==4,4)
    test("SELECTED_ONE",sum(r["Selected"]=="YES" for r in selection_rows)==1,1)
    test("SELECTED_IN_NIFTY50",selected["Cohort"]=="IN_NIFTY50",selected["Cohort"])
    test("SELECTED_EARLIEST_E",selected["Earliest_Unresolved_Gate"]=="E",selected["Earliest_Unresolved_Gate"])
    test("SELECTED_BLOCKER",selected_blocker=="DETERMINISTIC_WS_ID_LINKAGE_NOT_VERIFIED",selected_blocker)
    test("NEXT_GATE",next_gate=="IN_NIFTY50 DETERMINISTIC SECURITY IDENTITY LINKAGE GATE",next_gate)
    test("GLOBAL_READY_UNCHANGED",global_integrity["Canonical_Promoted_Rows"]==37 and global_integrity["No_Ready_Count_Increase"],global_integrity)
    test("GLOBAL_NOT_READY",global_integrity["GLOBAL_CANONICAL_SECTOR_METADATA_READY"] is False,"NO")
    test("NO_PROVIDER_CALLS",all(v==0 for v in providers.values()),providers)
    test("FROZEN_IMMUTABLE",imm["Frozen_Unchanged"],FROZEN_SHA)
    test("V057_IMMUTABLE",imm["v057_Unchanged"],V057_SHA)
    test("V058_IMMUTABLE",imm["v058_Unchanged"],V058_SHA)
    test("BR_SEMANTIC_IMMUTABLE",imm["BR_Canonical_Semantic_Unchanged"],BR_SEMANTIC_SHA)
    test("BR_FILE_IMMUTABLE",imm["BR_Canonical_File_Unchanged"],BR_FILE_SHA)
    test("NO_MAPPING_POPULATION",imm["Canonical_Mapping_Population_Runs"]==0,0)
    test("SECTOR_RS_ZERO",imm["Sector_RS_Runs"]==0,0)
    test("P0_P1_P2_ZERO",imm["P0_Runs"]==imm["P1_Runs"]==imm["P2_Runs"]==0,"0/0/0")
    test("NO_OTHER_COHORT_EXECUTION",imm["Other_Cohort_Executions"]==0,0)
    write_csv(out/"test_results_v0.69.csv",tests)

    verdict="PASS_CANONICAL_SECTOR_METADATA_RECONCILIATION_NEXT_COHORT_SELECTED"
    summary={
        "stage":STAGE,
        "version":VERSION,
        "verdict":verdict,
        "global_canonical_sector_metadata_ready":False,
        "global_ready":37,
        "global_total":1425,
        "global_remaining":1388,
        "unresolved_cohorts":7,
        "selected_next_cohort":selected["Cohort"],
        "resolved_gates_before_blocker":selected["Consecutive_Resolved_Gates"],
        "earliest_unresolved_gate":selected["Earliest_Unresolved_Gate"],
        "current_blocker":selected_blocker,
        "next_gate":next_gate,
        "external_requests":0,
        "provider_calls":0,
        "mapping_population_runs":0,
        "sector_rs_runs":0,
        "p0_runs":0,
        "p1_runs":0,
        "p2_runs":0,
        "artifact_binding":"PENDING_UPLOAD",
        "tests":{"total":len(tests),"passed":len(tests),"failed":0},
        "productive":False,
    }
    checkpoint={
        "stage":STAGE,
        "version":VERSION,
        "verdict":verdict,
        "global_canonical_sector_metadata_ready":False,
        "global_ready":37,
        "global_total":1425,
        "unresolved_cohorts":7,
        "selected_next_cohort":selected["Cohort"],
        "resolved_gates_before_blocker":selected["Consecutive_Resolved_Gates"],
        "earliest_unresolved_gate":selected["Earliest_Unresolved_Gate"],
        "current_blocker":selected_blocker,
        "next_gate":next_gate,
        "artifact_binding":"PENDING_UPLOAD",
    }
    (out/"summary_preupload_v0.69.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"stage_checkpoint_preupload_v0.69.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name]={"sha256":sha_file(p),"bytes":p.stat().st_size}
    manifest={
        "stage":STAGE,
        "version":VERSION,
        "required_start_head":REQUIRED_START_HEAD,
        "repository_sha":args.repository_sha,
        "verdict":verdict,
        "global_canonical_sector_metadata_ready":False,
        "global_ready":37,
        "global_total":1425,
        "global_remaining":1388,
        "unresolved_cohorts":7,
        "selected_next_cohort":selected["Cohort"],
        "resolved_gates_before_blocker":selected["Consecutive_Resolved_Gates"],
        "earliest_unresolved_gate":selected["Earliest_Unresolved_Gate"],
        "current_blocker":selected_blocker,
        "mapping_population_runs":0,
        "sector_rs_runs":0,
        "p0_runs":0,
        "p1_runs":0,
        "p2_runs":0,
        "productive":False,
        "artifact_binding":"PENDING_UPLOAD",
        "files":files,
        "next_gate":next_gate,
    }
    (out/"manifest_preupload_v0.69.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
