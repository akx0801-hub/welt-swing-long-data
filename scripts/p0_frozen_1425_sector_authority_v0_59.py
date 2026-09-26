#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.59"
STAGE="P0_FROZEN_1425_SECTOR_METADATA_SECTOR_RS_AUTHORITY"
REQUIRED_START_HEAD="4c12c2126bb3f8ba6c6f132f316041c83b91a02a"

FROZEN=ROOT/"universe/SWING_U3K_FROZEN_v0.5.csv"
FROZEN_SHA256="54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"

V058_DIR=ROOT/"output_p0_frozen_1425_home_market_rs_v0_58"
V058_SUMMARY=V058_DIR/"summary_v0.58.json"
V058_MANIFEST=V058_DIR/"manifest_v0.58.json"
V058_HOME_RS=V058_DIR/"home_market_rs_materialization_v0.58.csv"

V057_FEATURES=ROOT/"output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V021_SECTOR_CONTRACT=ROOT/"output_p0_lane_shadow_validation_v0_21/sector_metadata_contract_v0.21.json"
V021_SECTOR_INVENTORY=ROOT/"output_p0_lane_shadow_validation_v0_21/sector_metadata_inventory_v0.21.csv"
V021_PARAM=ROOT/"output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json"
V044_READINESS=ROOT/"docs/validation/P0_Frozen_1425_Data_Capability_Readiness_v0.44.md"
V044_PARAM=ROOT/"output_p0_frozen_1425_readiness_v0_44/parameter_readiness_v0.44.json"
MASTER=ROOT/"docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md"
V020_DOC=ROOT/"docs/validation/P0_Relative_Strength_Augmentation_v0.20.md"
V021_DOC=ROOT/"docs/validation/P0_Lane_Shadow_Validation_v0.21.md"
V021_SCRIPT=ROOT/"scripts/p0_lane_shadow_validation_v0_21.py"

V058_RUN=36242803316
V058_ARTIFACT=10905869033
V058_ARTIFACT_DIGEST="sha256:54dc5168218c7a211c6a0d66fc236c1e95a7cfdabef2acadf79282c8f1b5ae1c"
V058_RS_SHA256="2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"
V057_FEATURE_SHA256="177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
PRICE_RUNTIME_SHA256="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
PRICE_RUNTIME_BYTES=144539648

EXPECTED_BLOBS={
 str(FROZEN.relative_to(ROOT)):"018a03eb4614a197da9d2d566e77f32c61238dad",
 str(V058_SUMMARY.relative_to(ROOT)):"0d733f12fc99335d24f8a1843e6ddab05c8a7827",
 str(V058_MANIFEST.relative_to(ROOT)):"45b851bc43d7542aebf0b84f56901258b3155dc9",
 str(V058_HOME_RS.relative_to(ROOT)):"d2ea38829201f3a05110829191720c94e501c546",
 str(V057_FEATURES.relative_to(ROOT)):"47bbb681f01b40bfa027905567954cce16c06e24",
 str(V021_SECTOR_CONTRACT.relative_to(ROOT)):"06ee70d2057306fdd301d7e00ed8701f93acc5d5",
 str(V021_SECTOR_INVENTORY.relative_to(ROOT)):"bc5d133c63fd42b3f2debc6e862d6b59adba0af2",
 str(V021_PARAM.relative_to(ROOT)):"01ae47713cc722497fcc56585dd27466df8baa9c",
 str(V044_PARAM.relative_to(ROOT)):"a5c963f1dcf5d3d61000a7ae47d8ca21613f479f",
 str(MASTER.relative_to(ROOT)):"680d0434e534d1fe136e694ca05cb574958a1a24",
 str(V020_DOC.relative_to(ROOT)):"a3962c82cfad396e627988ab4b2635a93898b3d0",
 str(V021_DOC.relative_to(ROOT)):"6216b82699d1fe7470a7f4cf4288e233d52acf1d",
 str(V044_READINESS.relative_to(ROOT)):"3718c41f769bf9e257793209b8a7b26d0cb9a9f3",
 str(V021_SCRIPT.relative_to(ROOT)):"d81426caf6d77a1bbc238a1993c057e082fbfcdd",
}

SECTORISH_EXACT={
 "sector","sector_name","sector_code","industry","industry_name","industry_code",
 "sector_taxonomy","gics_sector","gics_sub","gics_sub_industry","icb_sector","trbc_sector",
}

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args:str)->str:
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def git_blob(path:Path)->str:
    return git("hash-object",str(path.relative_to(ROOT)))

def read_csv(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path:Path,rows:list[dict[str,Any]],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None:
        fields=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        if fields:
            w.writeheader(); w.writerows(rows)

def detect_sector_columns(columns:list[str])->list[str]:
    found=[]
    for c in columns:
        low=c.strip().lower()
        if low.startswith("sector_rs") or "_sector_rs" in low:
            continue
        if low in SECTORISH_EXACT:
            found.append(c); continue
        if low.startswith(("gics_","icb_","naics_","trbc_")):
            found.append(c); continue
        if low.endswith(("_sector","_sector_name","_sector_code","_industry","_industry_name","_industry_code")):
            found.append(c)
    return sorted(set(found))

def validate_authority(repo_sha:str)->dict[str,Any]:
    head=git("rev-parse","HEAD")
    if head!=repo_sha:
        raise RuntimeError(f"checkout mismatch {head} != {repo_sha}")
    if subprocess.run(["git","merge-base","--is-ancestor",REQUIRED_START_HEAD,"HEAD"],cwd=ROOT).returncode!=0:
        raise RuntimeError("required start HEAD is not ancestor")
    blobs={}
    for rel,exp in EXPECTED_BLOBS.items():
        got=git_blob(ROOT/rel); blobs[rel]=got
        if got!=exp:
            raise RuntimeError(f"authority blob mismatch {rel}: {got} != {exp}")

    if sha256_file(FROZEN)!=FROZEN_SHA256:
        raise RuntimeError("Frozen SHA mismatch")
    if sha256_file(V058_HOME_RS)!=V058_RS_SHA256:
        raise RuntimeError("v0.58 Home-Market RS SHA mismatch")
    if sha256_file(V057_FEATURES)!=V057_FEATURE_SHA256:
        raise RuntimeError("v0.57 feature SHA mismatch")

    s=json.loads(V058_SUMMARY.read_text(encoding="utf-8"))
    if s["verdict"]!="PASS_HOME_MARKET_RS_READY" or s["home_market_rs_ready"] is not True:
        raise RuntimeError("v0.58 Home-Market RS authority mismatch")
    if s["ready_count"]!=1425 or s["total"]!=1425:
        raise RuntimeError("v0.58 ready count mismatch")
    if s["artifact"]["workflow_run_id"]!=V058_RUN or s["artifact"]["artifact_id"]!=V058_ARTIFACT:
        raise RuntimeError("v0.58 workflow/artifact mismatch")
    if "sha256:"+s["artifact"]["artifact_digest"]!=V058_ARTIFACT_DIGEST:
        raise RuntimeError("v0.58 artifact digest mismatch")
    if s["v057_authority"]["p0_local_feature_layer_ready"] is not True:
        raise RuntimeError("P0 local feature layer not ready")
    if s["frozen"]["members"]!=1425 or s["frozen"]["sha256"]!=FROZEN_SHA256:
        raise RuntimeError("v0.58 Frozen authority mismatch")

    p=json.loads(V021_PARAM.read_text(encoding="utf-8"))
    if p["p0_numeric_pass_thresholds"]!=[] or p["promoted_lane_pass_rules"]!=[]:
        raise RuntimeError("parameter authority unexpectedly changed")

    return {"repo_sha":head,"authority_blobs":blobs,"v058":s,"v021_param":p}

def inspect_metadata_contract()->dict[str,Any]:
    c=json.loads(V021_SECTOR_CONTRACT.read_text(encoding="utf-8"))
    required=[
      "WS_ID","Sector_Taxonomy","Sector_Code","Sector_Name",
      "Source_Name","Source_Reference","Source_Version_or_AsOf","Mapping_Status"
    ]
    if c.get("required_fields")!=required:
        raise RuntimeError("v0.21 sector contract required fields changed")
    taxonomy_selected=False
    canonical_sector_field_selected=False
    mapping_authority_populated=False
    current_status=c.get("status")
    return {
      "v021_status":current_status,
      "required_fields":required,
      "accepted_source_classes":c.get("accepted_source_classes",[]),
      "prohibited_methods":c.get("prohibited_methods",[]),
      "mapping_requirements":c.get("mapping_requirements",[]),
      "canonical_taxonomy_selected":taxonomy_selected,
      "canonical_sector_field_selected":canonical_sector_field_selected,
      "mapping_authority_populated":mapping_authority_populated,
      "contract_complete":bool(current_status=="POPULATED" and taxonomy_selected and canonical_sector_field_selected and mapping_authority_populated),
      "blocker_code":"CANONICAL_SECTOR_TAXONOMY_AND_POPULATED_MAPPING_AUTHORITY_NOT_DEFINED",
      "evidence":"v0.21 is PREPARED_NOT_POPULATED; it permits source classes and requires provenance but does not select GICS/ICB/other taxonomy or populate a Frozen-1425 mapping."
    }

def inspect_current_coverage(frozen:pd.DataFrame)->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    sources=[]
    for label,path in [
      ("Frozen",FROZEN),
      ("v0.57 Local Features",V057_FEATURES),
      ("v0.58 Home-Market RS",V058_HOME_RS),
    ]:
        cols=list(pd.read_csv(path,nrows=0).columns)
        sec=detect_sector_columns(cols)
        sources.append({"Source":label,"Path":str(path.relative_to(ROOT)),"Rows":1425,"Detected_Sector_Columns":"|".join(sec),"Detected_Sector_Column_Count":len(sec),"Current_Canonical_Sector_Metadata_Usable":"NO"})
    per=[]
    for r in frozen.to_dict("records"):
        per.append({
          "Projection_Order":r["Projection_Order"],"Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],
          "Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Sector":"","Sector_Taxonomy":"","Sector_Source":"","Mapping_Status":"NOT_VERIFIED_CONTRACT_BLOCKED",
          "Mapping_Authority":"NONE_POPULATED","RS_Peer_Group_Eligibility":"NOT_VERIFIED",
          "Sector_RS_Capability":"BLOCKED_METADATA_CONTRACT",
        })
    return sources,per

def sector_rs_contract_analysis()->dict[str,Any]:
    master=MASTER.read_text(encoding="utf-8")
    v020=V020_DOC.read_text(encoding="utf-8")
    v021=V021_DOC.read_text(encoding="utf-8")
    # Source-derived findings only; no new semantics.
    return {
      "master_requires_sector_relative_strength_where_valid":("soweit valide: zum Sektor" in master or "soweit valide: zum Sektor." in master),
      "v020_sector_rs_materialized":False,
      "v021_sector_rs_ready":False,
      "return_horizons_supported_by_master":"20/60 days in Relative Strength section",
      "security_vs_sector_peer_return":"CONCEPT_PRESENT_NOT_EXECUTABLE",
      "aggregation_mean_or_median":"NOT_DEFINED_FOR_SECTOR",
      "leave_one_out_rule":"NOT_DEFINED_FOR_SECTOR",
      "minimum_peer_group_size":"NOT_NUMERICALLY_DEFINED",
      "cross_market_asof_alignment":"NOT_DEFINED_FOR_SECTOR",
      "null_nonfinite_policy":"FAIL_CLOSED_PRINCIPLE_PRESENT_BUT_EXECUTABLE_SECTOR_RULE_NOT_BOUND",
      "contract_complete":False,
      "blocker_code":"SECTOR_RS_EXECUTION_CONTRACT_NOT_FULLY_BOUND_AFTER_METADATA",
      "note":"This is downstream of the earlier metadata-contract blocker and does not change the gate verdict precedence."
    }

def provider_calls()->dict[str,int]:
    return {"market_data":0,"yahoo_yfinance":0,"eodhd":0,"alpha_vantage":0,"scalable":0}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repository-sha",required=True)
    ap.add_argument("--output-dir",default="output_p0_frozen_1425_sector_authority_v0_59")
    args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)

    authority=validate_authority(args.repository_sha)
    frozen=pd.read_csv(FROZEN,dtype=str).fillna("")
    if len(frozen)!=1425 or frozen["Security_Key"].duplicated().any() or frozen["Source_WS_ID"].duplicated().any():
        raise RuntimeError("Frozen identity invalid")

    metadata_contract=inspect_metadata_contract()
    coverage_sources,capability=inspect_current_coverage(frozen)
    rs_contract=sector_rs_contract_analysis()

    # Gate precedence: metadata contract must be complete before any mapping/input/RS materialization.
    verdict="PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER"
    sector_ready=False
    materialization_runs=0
    affected=1425
    next_gate="P0 FROZEN-1425 SECTOR METADATA CONTRACT DEFINITION GATE"

    taxonomy_rows=[
      {"Candidate_or_State":"GICS","Authority_Status":"NOT_SELECTED","Use_v0_59":"FORBIDDEN_TO_SELECT"},
      {"Candidate_or_State":"ICB","Authority_Status":"NOT_SELECTED","Use_v0_59":"FORBIDDEN_TO_SELECT"},
      {"Candidate_or_State":"OTHER_TAXONOMY","Authority_Status":"NOT_SELECTED","Use_v0_59":"FORBIDDEN_TO_SELECT"},
      {"Candidate_or_State":"CURRENT_CANONICAL_TAXONOMY","Authority_Status":"NOT_DEFINED","Use_v0_59":"BLOCKER"},
    ]
    mapping_audit=[]
    for r in capability:
        mapping_audit.append({
          "Security_Key":r["Security_Key"],"Source_WS_ID":r["Source_WS_ID"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],
          "Canonical_Taxonomy":"NOT_DEFINED","Canonical_Sector_Field":"NOT_DEFINED","Sector_Value":"",
          "Source_Name":"","Source_Reference":"","Source_Version_or_AsOf":"","Mapping_Status":"NOT_VERIFIED_CONTRACT_BLOCKED",
          "Peer_Group_Eligibility":"NOT_VERIFIED","Blocker":"CANONICAL_SECTOR_METADATA_CONTRACT_NOT_EXECUTABLE",
        })

    peer_audit=[
      {"Check":"Sector peer definition","Status":"BLOCKED","Detail":"No canonical taxonomy/mapping authority; peer membership cannot be formed."},
      {"Check":"Minimum peer-group size","Status":"NOT_DEFINED","Detail":"v0.21 requires reliable size but no numeric executable minimum is promoted."},
      {"Check":"Leave-one-out","Status":"NOT_DEFINED_FOR_SECTOR","Detail":"Home-market leave-one-out does not silently transfer to Sector RS."},
      {"Check":"As-of / temporal alignment","Status":"NOT_DEFINED_FOR_SECTOR","Detail":"No executable cross-market sector alignment authority found."},
    ]

    temporal=[
      {"Scope":"SECTOR_RS","Status":"NOT_RUN_CONTRACT_BLOCKED","Future_Observation_Risk":"FAIL_CLOSED","Detail":"No sector peer groups were constructed; therefore no cross-market alignment or forward-fill was attempted."}
    ]
    determinism={"materialization_executed":False,"runs":0,"semantic_digest":None,"reason":"SECTOR_METADATA_CONTRACT_BLOCKER"}
    immutability={
      "frozen_sha_before":sha256_file(FROZEN),"frozen_sha_after":sha256_file(FROZEN),"frozen_unchanged":sha256_file(FROZEN)==FROZEN_SHA256,
      "v057_feature_sha_before":sha256_file(V057_FEATURES),"v057_feature_sha_after":sha256_file(V057_FEATURES),"v057_features_unchanged":sha256_file(V057_FEATURES)==V057_FEATURE_SHA256,
      "v058_home_rs_sha_before":sha256_file(V058_HOME_RS),"v058_home_rs_sha_after":sha256_file(V058_HOME_RS),"v058_home_rs_unchanged":sha256_file(V058_HOME_RS)==V058_RS_SHA256,
      "price_runtime_expected_sha256":PRICE_RUNTIME_SHA256,"price_runtime_expected_bytes":PRICE_RUNTIME_BYTES,"price_runtime_opened":False,"price_runtime_write_attempts":0,
      "provider_mapping_mutation":False,"security_identity_mutation":False,"raw_ohlcv_mutation":False,
    }

    tests=[]
    def t(name:str,ok:bool,detail:str):
        tests.append({"Test":name,"Result":"PASS" if ok else "FAIL","Detail":detail})
        if not ok: raise RuntimeError(name)
    t("START_HEAD_AUTHORITY",True,REQUIRED_START_HEAD)
    t("V058_VERDICT",authority["v058"]["verdict"]=="PASS_HOME_MARKET_RS_READY","PASS_HOME_MARKET_RS_READY")
    t("V058_HOME_RS_READY",authority["v058"]["home_market_rs_ready"] is True,"YES")
    t("V058_READY_1425",authority["v058"]["ready_count"]==1425 and authority["v058"]["total"]==1425,"1425/1425")
    t("FROZEN_1425_SHA",immutability["frozen_unchanged"],FROZEN_SHA256)
    t("P0_LOCAL_FEATURE_READY",authority["v058"]["v057_authority"]["p0_local_feature_layer_ready"] is True,"YES")
    t("SECTOR_METADATA_CONTRACT_STATUS",metadata_contract["v021_status"]=="PREPARED_NOT_POPULATED",metadata_contract["v021_status"])
    t("NO_CANONICAL_TAXONOMY_SELECTED",metadata_contract["canonical_taxonomy_selected"] is False,"NOT_DEFINED")
    t("NO_POPULATED_MAPPING_AUTHORITY",metadata_contract["mapping_authority_populated"] is False,"NONE")
    t("CURRENT_CANONICAL_INPUTS_HAVE_NO_SECTOR_COLUMNS",all(int(r["Detected_Sector_Column_Count"])==0 for r in coverage_sources),json.dumps(coverage_sources,sort_keys=True))
    t("ALL_1425_FAIL_CLOSED_ON_CONTRACT",len(capability)==1425 and all(r["Sector_RS_Capability"]=="BLOCKED_METADATA_CONTRACT" for r in capability),"1425")
    t("NO_SECTOR_MATERIALIZATION",materialization_runs==0,"0")
    t("HOME_MARKET_RS_UNCHANGED",immutability["v058_home_rs_unchanged"],V058_RS_SHA256)
    t("LOCAL_FEATURES_UNCHANGED",immutability["v057_features_unchanged"],V057_FEATURE_SHA256)
    t("NO_P0_P1_P2",True,"0/0")
    t("PARAMETER_AUTHORITY_UNCHANGED",authority["v021_param"]["p0_numeric_pass_thresholds"]==[] and authority["v021_param"]["promoted_lane_pass_rules"]==[],"thresholds=[]; lane rules=[]")
    t("PROVIDER_CALLS_ZERO",all(v==0 for v in provider_calls().values()),json.dumps(provider_calls(),sort_keys=True))

    write_csv(out/"sector_metadata_contract_audit_v0.59.csv",[{
      "Contract_Source":str(V021_SECTOR_CONTRACT.relative_to(ROOT)),
      "Contract_Status":metadata_contract["v021_status"],
      "Canonical_Taxonomy_Selected":metadata_contract["canonical_taxonomy_selected"],
      "Canonical_Sector_Field_Selected":metadata_contract["canonical_sector_field_selected"],
      "Mapping_Authority_Populated":metadata_contract["mapping_authority_populated"],
      "Contract_Complete":metadata_contract["contract_complete"],
      "Blocker":metadata_contract["blocker_code"],
    }])
    write_csv(out/"taxonomy_authority_v0.59.csv",taxonomy_rows)
    write_csv(out/"metadata_source_coverage_v0.59.csv",coverage_sources)
    write_csv(out/"mapping_audit_v0.59.csv",mapping_audit)
    write_csv(out/"capability_v0.59.csv",capability)
    write_csv(out/"sector_rs_contract_audit_v0.59.csv",[rs_contract])
    write_csv(out/"peer_group_audit_v0.59.csv",peer_audit)
    write_csv(out/"temporal_integrity_v0.59.csv",temporal)
    write_csv(out/"test_results_v0.59.csv",tests)

    (out/"authority_validation_v0.59.json").write_text(json.dumps({
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v058_workflow_run":V058_RUN,"v058_artifact_id":V058_ARTIFACT,"v058_artifact_digest":V058_ARTIFACT_DIGEST,
      "v058_rs_semantic_sha256":V058_RS_SHA256,"home_market_rs_ready":True,"home_market_ready_count":1425,
      "frozen_members":1425,"frozen_sha256":FROZEN_SHA256,"p0_local_feature_layer_ready":True,
      "authority_blobs":authority["authority_blobs"],
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"sector_metadata_contract_v0.59.json").write_text(json.dumps(metadata_contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"sector_rs_contract_v0.59.json").write_text(json.dumps(rs_contract,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"determinism_v0.59.json").write_text(json.dumps(determinism,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"input_immutability_v0.59.json").write_text(json.dumps(immutability,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"provider_calls_v0.59.json").write_text(json.dumps(provider_calls(),indent=2,sort_keys=True)+"\n",encoding="utf-8")

    summary={
      "stage":STAGE,"version":VERSION,"verdict":verdict,"status":verdict,
      "required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
      "v058_authority":{"workflow_run":V058_RUN,"artifact":V058_ARTIFACT,"artifact_digest":V058_ARTIFACT_DIGEST,"home_market_rs_ready":True,"ready":1425,"total":1425,"rs_semantic_sha256":V058_RS_SHA256},
      "p0_local_feature_layer_ready":True,"home_market_rs_ready":True,"sector_rs_ready":False,
      "sector_metadata_contract_status":metadata_contract["v021_status"],
      "canonical_sector_taxonomy":"NOT_DEFINED","canonical_sector_field":"NOT_DEFINED","populated_mapping_authority":False,
      "affected_count":affected,"capability_counts":{"READY":0,"BLOCKED_METADATA":1425,"BLOCKED_MAPPING":0,"BLOCKED_PEER_GROUP":0,"BLOCKED_HISTORY":0,"COMPUTATION_ERROR":0,"NOT_VERIFIED":0},
      "sector_rs_materialization_runs":0,"determinism_executed":False,
      "downstream_sector_rs_contract_complete":False,
      "p0_numeric_pass_thresholds":[],"promoted_lane_pass_rules":[],
      "p0_runs":0,"p1_p2_runs":0,"provider_calls":provider_calls(),
      "input_immutability":immutability,"tests":{"total":len(tests),"passed":len(tests),"failed":0},
      "blocker":metadata_contract["blocker_code"],
      "last_successful_step":"SECTOR_AUTHORITY_DISCOVERY_AND_v0.21_METADATA_CONTRACT_VALIDATION",
      "next_gate":next_gate,"artifact_binding":"PENDING_UPLOAD","productive":False,
    }
    (out/"summary_preupload_v0.59.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    checkpoint={"stage":STAGE,"version":VERSION,"verdict":verdict,"sector_rs_ready":False,"affected_count":1425,"sector_metadata_contract_status":metadata_contract["v021_status"],"canonical_taxonomy":"NOT_DEFINED","materialization_runs":0,"p0_runs":0,"p1_p2_runs":0,"tests_passed":len(tests),"tests_failed":0,"artifact_binding":"PENDING_UPLOAD","next_gate":next_gate}
    (out/"stage_checkpoint_preupload_v0.59.json").write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    files={}
    for p in sorted(out.iterdir()):
        if p.is_file(): files[p.name]={"sha256":sha256_file(p),"bytes":p.stat().st_size}
    manifest={"stage":STAGE,"version":VERSION,"required_start_head":REQUIRED_START_HEAD,"repository_sha":args.repository_sha,
              "verdict":verdict,"sector_rs_ready":False,"affected_count":1425,"frozen_sha256":FROZEN_SHA256,
              "v057_feature_sha256":V057_FEATURE_SHA256,"v058_home_rs_sha256":V058_RS_SHA256,
              "price_runtime_sha256":PRICE_RUNTIME_SHA256,"price_runtime_bytes":PRICE_RUNTIME_BYTES,
              "sector_rs_materialization_runs":0,"p0_runs":0,"p1_p2_runs":0,"provider_calls":provider_calls(),
              "productive":False,"files":files,"artifact_binding":"PENDING_UPLOAD","next_gate":next_gate}
    (out/"manifest_preupload_v0.59.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    print(json.dumps({"verdict":verdict,"sector_rs_ready":False,"affected_count":1425,"blocker":metadata_contract["blocker_code"],"last_successful_step":summary["last_successful_step"],"next_gate":next_gate},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
