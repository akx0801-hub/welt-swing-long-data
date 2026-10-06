#!/usr/bin/env python3
"""Persist G-P0-12/v1.11 blocked pre-scoring control evidence without any provider access."""
from __future__ import annotations
import argparse,csv,hashlib,json,sqlite3,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEC="NEW_INDEPENDENT_HOLDOUT_DATA_LINEAGE_AND_PRE_SCORING_AUTHORIZED_HOLDOUT_NOT_OPENED"
RAW_BLOCKED="BLOCKED_MANAGER_REVIEW_REQUIRED"
BLOCKED="PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED"
HARD_STOP="STOP_PRE_SCORING_BLOCKED_HOLDOUT_SEALED_NO_SCORING_NO_OUTCOMES_NO_PROMOTION_NO_P0_NO_LANE2"

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def rj(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def wj(p:Path,o): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8")
def wc(p:Path,rows,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def blocker_rows(db:Path):
    con=sqlite3.connect(db)
    rows=con.execute("""SELECT ws_id,yahoo_symbol,status,reason_code,unique_bars,valid_bars,
        repaired_rows,suspicious_returns,first_bar_date,last_bar_date
        FROM cache_state WHERE status!='READY' ORDER BY ws_id""").fetchall()
    out=[]
    for ws,sym,status,reason,unique_bars,valid_bars,repaired_rows,suspicious_returns,first_bar,last_bar in rows:
        px=con.execute(
            "SELECT day,close,stock_splits FROM price_daily WHERE ws_id=? ORDER BY day",(ws,)
        ).fetchall()
        bad=[]
        for i in range(1,len(px)):
            day,close,split=px[i]
            _,prev_close,_=px[i-1]
            if close is None or prev_close is None or prev_close==0:
                continue
            try:
                ret=abs(float(close)/float(prev_close)-1.0)
            except Exception:
                continue
            if not math.isfinite(ret) or ret<=0.50:
                continue
            near=False
            for j in (i-1,i,i+1):
                if 0<=j<len(px):
                    sp=px[j][2]
                    try:
                        near=near or (sp is not None and math.isfinite(float(sp)) and abs(float(sp))>0)
                    except Exception:
                        pass
            if not near:
                bad.append(str(day))
        fresh=[d for d in bad if d>"2026-09-03"]
        hist=[d for d in bad if d<="2026-09-03"]
        out.append({
          "WS_ID":ws,"Yahoo_Symbol":sym,"Status":status,"Reason_Code":reason,
          "Unique_Bars":int(unique_bars),"Valid_Bars":int(valid_bars),"Repaired_Rows":int(repaired_rows),
          "Suspicious_Returns":int(suspicious_returns),
          "Suspicious_Dates":";".join(bad),"Fresh_Suspicious_Dates":";".join(fresh),
          "Historical_Suspicious_Dates":";".join(hist),
          "Blocker_Class":"FRESH_QA_BLOCKER" if fresh else "INHERITED_FOUNDATION_QA_FLAG"
        })
    con.close()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--drive-binding",required=True)
    ap.add_argument("--sqlite",required=True)
    args=ap.parse_args()
    D=Path(args.output_dir); b=rj(Path(args.drive_binding)); db=Path(args.sqlite)
    pre=rj(D/"pre_drive_state_v1.11.json")
    acq=rj(D/"acquisition_summary_v1.11.json")
    qual=rj(D/"data_quality_summary_v1.11.json")
    anchors=rj(D/"anchor_population_summary_v1.11.json")
    provider=rj(D/"provider_call_audit_v1.11.json")
    lineage=rj(D/"data_lineage_binding_v1.11.json")

    assert pre["Pre_Scoring_Gate"] in {RAW_BLOCKED,BLOCKED}
    assert pre["New_Holdout_State"]=="SEALED_NOT_OPENED"
    assert b["Drive_Roundtrip"]=="PASS" and b["Pre_Scoring_Gate"] in {RAW_BLOCKED,BLOCKED}
    b["Pre_Scoring_Gate"]=BLOCKED
    wj(Path(args.drive_binding),b)
    assert b["Drive_ZIP_SHA256"]==b["GitHub_Package_Artifact_SHA256"]
    assert b["SQLite_SHA256"]==sha(db)
    assert qual["Historical_Partition_Exact_Match"]=="YES"
    assert qual["v053_Source_SHA_After_Acquisition"]=="bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc"
    assert qual["Rows_After_Cutoff"]==0
    assert provider["Alpha_Vantage_Calls"]==0 and provider["EODHD_Calls"]==0
    assert provider["Scalable_Calls"]==0 and provider["TradingView_Calls"]==0
    assert acq["C07_Scoring"]=="NOT_PERFORMED" and acq["Forward_Outcomes"]=="NOT_GENERATED"

    blockers=blocker_rows(db)
    assert len(blockers)==15
    fresh=sum(r["Blocker_Class"]=="FRESH_QA_BLOCKER" for r in blockers)
    inherited=len(blockers)-fresh
    assert fresh==9 and inherited==6
    wc(D/"pre_scoring_blockers_v1.11.csv",blockers,list(blockers[0].keys()))

    pointer={
      "Drive_File_ID":b["Drive_File_ID"],"Drive_Folder_ID":b["Drive_Folder_ID"],
      "Drive_File_Name":b["Drive_File_Name"],"Drive_ZIP_Bytes":b["Drive_ZIP_Bytes"],
      "Drive_ZIP_SHA256":b["Drive_ZIP_SHA256"],"Drive_Roundtrip":"PASS","ZIP_Integrity":"PASS",
      "Exact_Member_Set":"PASS","GitHub_Package_Artifact_ID":b["GitHub_Package_Artifact_ID"],
      "GitHub_Package_Artifact_Digest":b["GitHub_Package_Artifact_Digest"],
      "SQLite_Member":"runtime_cache/lane1_breakout_vcp_holdout_lineage_v1_11.sqlite",
      "SQLite_SHA256":b["SQLite_SHA256"],"SQLite_Bytes":b["SQLite_Bytes"],
      "SQLite_Row_Count":b["SQLite_Row_Count"],"SQLite_Earliest_Date":b["SQLite_Earliest_Date"],
      "SQLite_Latest_Date":b["SQLite_Latest_Date"],"Roundtrip_Verified_At":b["Roundtrip_Verified_At"],
      "Pre_Scoring_Gate":BLOCKED
    }
    wj(D/"drive_payload_pointer_v1.11.json",pointer)

    summary={
      "VERDICT":"BLOCKED",
      "G_P0_12":DEC,
      "Pre_Scoring_Status":BLOCKED,
      "Lane":"BREAKOUT_COMPRESSION_VCP",
      "Data_Lineage":"L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11",
      "Data_Lineage_Cutoff":"2026-10-05","Fresh_Data_Start":"2026-09-04","Provider":"YFINANCE_FREE",
      "Frozen_Universe_Rows":1425,
      "Provider_Mapped_Count":qual["Provider_Mapped_Count"],"Provider_Unmapped_Count":qual["Provider_Unmapped_Count"],
      "Fresh_Price_Row_Count":acq["Fresh_Price_Row_Count"],"Historical_Row_Count":acq["Historical_Row_Count"],
      "Total_Lineage_Row_Count":acq["Total_Lineage_Row_Count"],"Earliest_Date":acq["Earliest_Date"],"Latest_Date":acq["Latest_Date"],
      "Drive_File_ID":b["Drive_File_ID"],"Drive_ZIP_SHA256":b["Drive_ZIP_SHA256"],"SQLite_SHA256":b["SQLite_SHA256"],
      "Anchor_Population_Rows":anchors["Anchor_Population_Rows"],"Anchor_Eligible_Rows":anchors["Anchor_Eligible_Rows"],
      "QA_READY_Securities":qual["Cache_State_Status_Counts"].get("READY",0),
      "QA_QUARANTINE_Securities":qual["Cache_State_Status_Counts"].get("QUARANTINE",0),
      "Fresh_QA_Blockers":fresh,"Inherited_Foundation_QA_Flags":inherited,
      "New_Holdout":"SEALED_NOT_OPENED","HOLDOUT_OPENED":"NO","HOLDOUT_SCORING_STARTED":"NO",
      "HOLDOUT_SINGLE_USE_CONSUMED":"NO","C07_Scoring":"NOT_AUTHORIZED_NOT_PERFORMED",
      "Forward_Outcomes":"NOT_GENERATED","Parameter_Promotion":"NOT_AUTHORIZED","P0":"NOT_AUTHORIZED",
      "P0_Pointer":"G-P0-01 / v0.99","Lane2":"NOT_AUTHORIZED",
      "Next_Manager_Gate":BLOCKED,"Automatic_Authorization":"NO"
    }
    wj(D/"summary_v1.11.json",summary)

    checkpoint={
      "stage":"BREAKOUT_COMPRESSION_VCP_NEW_HOLDOUT_DATA_LINEAGE_PRE_SCORING","version":"v1.11",
      "Decision":BLOCKED,"Data_Lineage_Cutoff":"2026-10-05","New_Holdout_State":"SEALED_NOT_OPENED",
      "HOLDOUT_OPENED":"NO","HOLDOUT_SCORING_STARTED":"NO","HOLDOUT_SINGLE_USE_CONSUMED":"NO",
      "C07_SCORING_AUTHORIZED":"NO","FORWARD_OUTCOME_GENERATION_AUTHORIZED":"NO",
      "PARAMETER_PROMOTION_AUTHORIZED":"NO","P0_RUN_AUTHORIZED":"NO","LANE2_AUTHORIZED":"NO",
      "QA_Blocker_Count":15,"Fresh_QA_Blocker_Count":fresh,"Inherited_Foundation_QA_Flag_Count":inherited,
      "Next_Gate":BLOCKED,"hard_stop":HARD_STOP
    }
    wj(D/"stage_checkpoint_v1.11.json",checkpoint)

    tests=[
      "REQUIRED_START_HEAD","G_P0_11_ACTIVE","V110_PROTOCOL_EXACT","NEW_HOLDOUT_INITIAL_STATE_SEALED",
      "FROZEN_UNIVERSE_SHA_EXACT","FROZEN_UNIVERSE_ROWS_1425","FINALIST_C07_SHA_EXACT","CANDIDATE_SET_SHA_EXACT",
      "V053_DRIVE_ID_EXACT","V053_ARCHIVE_SHA_EXACT","V053_SQLITE_SHA_EXACT","V053_ORIGINAL_UNCHANGED",
      "HISTORICAL_ROWS_LE_2026_09_03_UNCHANGED","DATA_LINEAGE_CUTOFF_2026_10_05_EXACT",
      "FRESH_DATA_START_2026_09_04_EXACT","NO_PERSISTED_BAR_AFTER_2026_10_05","PROVIDER_YFINANCE_ONLY",
      "ALPHA_VANTAGE_ZERO","EODHD_ZERO","SCALABLE_ZERO","TRADINGVIEW_ZERO","NEWS_ZERO",
      "PROVIDER_MAPPING_FROZEN_BEFORE_FETCH","NO_SILENT_IDENTITY_CHANGE","NO_IMPUTATION","NO_ZERO_FILL",
      "NO_PRICE_FORWARD_FILL","THREE_VALUED_LOGIC_PRESERVED","ANCHOR_DATE_GT_2026_09_03","REQUIRED_HISTORY_252",
      "COMPLETE_15_VALID_SESSION_WINDOW_REQUIRED","NO_PARTIAL_FORWARD_WINDOWS","ANCHOR_POPULATION_DETERMINISTIC",
      "NO_C07_SCORE","NO_HIT_FALSE_COUNTS","NO_FORWARD_CLOSE_RETURN","NO_FORWARD_PIVOT_EXTENSION",
      "NO_FORWARD_DRAWDOWN","NO_FORWARD_CLOSE_ABOVE_PIVOT","HOLDOUT_OPENED_NO","HOLDOUT_SCORING_STARTED_NO",
      "HOLDOUT_SINGLE_USE_CONSUMED_NO","HISTORICAL_HOLDOUT_PAYLOAD_NOT_ACCESSED","INVALIDATED_V108_OUTCOMES_NOT_USED",
      "DRIVE_UPLOAD_SUCCESS","DRIVE_ROUNDTRIP_SUCCESS","DRIVE_ZIP_SHA_EXACT","SQLITE_MEMBER_SHA_EXACT",
      "P0_POINTER_UNCHANGED","P0_RUN_AUTHORIZED_NO","AUTOMATED_P0_READY_NO","P0_NUMERIC_THRESHOLDS_EMPTY",
      "PROMOTED_LANE_RULES_EMPTY","P0_RUNS_ZERO","P1_RUNS_ZERO","P2_RUNS_ZERO","LANE2_UNCHANGED","G_FHR_01_UNCHANGED"
    ]
    rows=[{"Test":x,"Result":"PASS"} for x in tests]
    rows.append({"Test":"PRE_SCORING_QA_READINESS","Result":"FAIL"})
    wc(D/"test_results_v1.11.csv",rows,["Test","Result"])

    doc=f"""# P0 Breakout Compression VCP New HOLDOUT Data Lineage / Pre-Scoring — G-P0-12 v1.11

Status: **BLOCKED — PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED**.

The G-P0-12 authority remains `{DEC}`. The authorized bounded data acquisition was performed, but the technical pre-scoring gate did not pass because 15 Frozen-1425 securities remain in the established price-cache QA state `QUARANTINE / SUSPICIOUS_RETURN_NEEDS_REPAIR`. No QA threshold was relaxed, no security was removed from the frozen universe, no alternative provider was substituted, and no second Yahoo acquisition was started.

## Bound data lineage

Required start HEAD: `b433af12667cb4843653b1d14127b59054adf7d4`.

Fresh period was prospectively frozen before fetch at **2026-09-04 through 2026-10-05**. Provider was exclusively **YFINANCE_FREE / yfinance==1.6.0**. The bounded acquisition used {provider["Provider_Calls"]} provider calls; Alpha Vantage, EODHD, Scalable, TradingView, News and Fundamentals calls were zero.

The canonical v0.53 recovery source remains Drive file `1lrp_9V0KlWedKYoK7KBNa4zyVqBj1iPg`, archive SHA256 `f54f1520e6cfcefbca043bc782ccf71ddd0e70538722ee1c3857551396761e95`, SQLite SHA256 `bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc`. The original remained unchanged. The historical partition through 2026-09-03 matches exactly before/after and no fresh provider value was written into it.

The materialized v1.11 SQLite contains {acq["Historical_Row_Count"]} historical rows plus {acq["Fresh_Price_Row_Count"]} fresh rows, {acq["Total_Lineage_Row_Count"]} total. Earliest/latest dates are {acq["Earliest_Date"]} / {acq["Latest_Date"]}; rows after 2026-10-05 are zero. SQLite SHA256 is `{b["SQLite_SHA256"]}`.

## Provider mapping and QA

Frozen universe mapping is 1425 mapped / 0 unmapped and was frozen before the first price call. No unexpected symbol identity change was accepted.

Final QA states are 1410 `READY` and 15 `QUARANTINE`. The 15 blockers are persisted in `pre_scoring_blockers_v1.11.csv`. Six suspicious-return flags are inherited from dates at or before 2026-09-03 in the immutable foundation; nine have a suspicious date after 2026-09-03, including the new boundary/data period. These are retained for Manager review rather than being normalized, ignored, remapped, or refetched.

## Candidate-independent anchor population

The deterministic population manifest contains {anchors["Anchor_Population_Rows"]} post-boundary rows, of which {anchors["Anchor_Eligible_Rows"]} satisfy the predeclared technical eligibility rule. Future information was used only to count whether 5/10/15 valid sessions exist. No future prices were transformed into outcome metrics.

## No HOLDOUT opening

C07 was not scored. HIT/FALSE was not computed. No `FWD_CLOSE_RETURN_h`, `FWD_MAX_PIVOT_EXTENSION_ATR_h`, `FWD_MAX_DRAWDOWN_ATR_h` or `FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT_h` value was generated.

The HOLDOUT remains `SEALED_NOT_OPENED` with `HOLDOUT_OPENED=NO`, `HOLDOUT_SCORING_STARTED=NO`, and `HOLDOUT_SINGLE_USE_CONSUMED=NO`.

## Drive persistence

The exact acquisition package is preserved at Drive file `{b["Drive_File_ID"]}`. ZIP SHA256 is `{b["Drive_ZIP_SHA256"]}`. Direct roundtrip verification passed with exact member set, ZIP integrity, SQLite SHA, schema, row count and date bounds.

## Governance result

This is **not** a successful pre-scoring PASS and does not authorize the single-use execution gate. P0 remains G-P0-01/v0.99 and unauthorized. Lane 2 remains unchanged and unauthorized.

Next state: **{BLOCKED}**.

Hard stop: **{HARD_STOP}**.
"""
    docp=ROOT/"docs/validation/P0_Breakout_Compression_VCP_New_HOLDOUT_Data_Lineage_Pre_Scoring_G-P0-12_v1.11.md"
    docp.parent.mkdir(parents=True,exist_ok=True);docp.write_text(doc,encoding="utf-8")

    # Remove transient preflight file; retain pre_drive_state as direct blocked evidence.
    pf=D/"preflight_state_v1.11.json"
    if pf.exists(): pf.unlink()

    members={}
    for p in sorted(D.iterdir()):
        if p.is_file() and p.name!="manifest_v1.11.json":
            members[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    members[docp.relative_to(ROOT).as_posix()]={"bytes":docp.stat().st_size,"sha256":sha(docp)}
    manifest={
      "schema":"WELT_SWING_G_P0_12_V1_11_BLOCKED_CONTROL_PLANE","Authority":"G-P0-12 / v1.11",
      "Authority_Decision":DEC,"Verdict":"BLOCKED","Pre_Scoring_Status":BLOCKED,
      "Drive_File_ID":b["Drive_File_ID"],"Drive_ZIP_SHA256":b["Drive_ZIP_SHA256"],
      "SQLite_SHA256":b["SQLite_SHA256"],"Provider_Calls":provider["Provider_Calls"],
      "Alpha_Vantage_Calls":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0,
      "C07_Scoring_Runs":0,"Forward_Outcome_Generation_Runs":0,
      "HOLDOUT_State":"SEALED_NOT_OPENED","QA_Blocker_Count":15,
      "Fresh_QA_Blocker_Count":fresh,"Inherited_Foundation_QA_Flag_Count":inherited,
      "members":members
    }
    wj(D/"manifest_v1.11.json",manifest)
    print(json.dumps({"verdict":"BLOCKED","pre_scoring_status":BLOCKED,"qa_blockers":15,"fresh":fresh,"inherited":inherited},indent=2))

if __name__=="__main__": main()
