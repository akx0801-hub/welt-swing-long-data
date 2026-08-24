#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

SCHEMA='WELT_SWING_P0_RESEARCH_PARTIAL_DRY_RUN_V0_17'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1048576),b''): h.update(c)
    return h.hexdigest()

def self_test():
    assert SCHEMA.endswith('V0_17')
    print('P0_RESEARCH_PARTIAL_DRY_RUN_V0_17_SELF_TEST_PASS')

def lane_rows():
    return [
      ['BREAKOUT_COMPRESSION_VCP','PARTIAL','EMA50;SMA200;High20;High60;High252;ATR14;R20;R60;Range20','validated pivot/base/VCP detector; current RVOL; climax detector; validated run-up threshold'],
      ['PULLBACK_RETEST','PARTIAL','EMA20;EMA50;SMA200;Dist_EMA20;Dist_EMA50;Low20;Low60;R20;R60','former-breakout-zone detector; horizontal support detector; controlled-pullback sequence'],
      ['RECLAIM','PARTIAL','Close;EMA20;EMA50;R5;R20;Low20','multi-day reclaim/crossing sequence; higher-low detector; confirmation logic'],
      ['QUIET_STRENGTH_RELATIVE_STRENGTH','PARTIAL','R20;R60;EMA20;EMA50;SMA200','20d/60d home-market RS; sector RS; validated excess-momentum rule'],
      ['POST_EVENT_DRIFT','PARTIAL','R5;R20;R60;High20;Low20;Range20','impulse/held-level/tight-consolidation sequence; current RVOL'],
      ['CONTROLLED_MEAN_REVERSION','PARTIAL','R20;R60;EMA20;EMA50;SMA200;Low20;Low60;ATR14','stabilization sequence; falling-knife acceleration detector; definable invalidation'],
    ]

def run(cfgp):
    c=json.loads(Path(cfgp).read_text())
    out=Path(c['output_dir']); out.mkdir(parents=True,exist_ok=True)
    s16=json.loads(Path(c['source_summary_v0_16']).read_text())
    m16=json.loads(Path(c['source_manifest_v0_16']).read_text())
    ck16=json.loads(Path(c['source_checkpoint_v0_16']).read_text())
    assert s16['run_status']=='RESEARCH_PARTIAL_SNAPSHOT_V0_16_FROZEN'
    assert s16['included_verified_strict_rows']==c['expected_partial_rows']
    assert s16['strict_u3k_freeze_allowed'] is False and s16['p0_run'] is False
    assert m16['full_scan_claim'] is False and m16['strict_u3k_frozen'] is False
    assert ck16['stage_id']=='RESEARCH_PARTIAL_SNAPSHOT' and ck16['status']=='PARTIAL'

    pp=Path(c['source_partial_universe_v0_16']); fp=Path(c['source_features_full_3663'])
    assert sha(pp)==c['expected_partial_sha256']
    pm=json.loads(Path(c['source_price_manifest']).read_text())
    assert pm['files'][str(fp)]==c['expected_feature_sha256']==sha(fp)
    pc=json.loads(Path(c['source_price_coverage']).read_text())
    assert pc['data_source']=='YFINANCE_FREE' and pc['alpha_vantage_allowed'] is False
    assert pc['p0_status']=='NOT_RUN_PARAMETERS_NOT_YET_PROMOTED'

    p=pd.read_csv(pp,keep_default_na=False,dtype=str)
    f=pd.read_csv(fp,keep_default_na=False,dtype=str)
    assert len(p)==c['expected_partial_rows'] and p.WS_ID.is_unique and f.WS_ID.is_unique
    cols=['WS_ID','AsOf','Bars','Close_Tech','EMA20','EMA50','SMA200','ATR14_Wilder_DEV','ATR14_Pct_DEV','R5','R20','R60','High20','High60','High252','Low20','Low60','Dist_EMA20','Dist_EMA50','Dist_SMA200','Dist_High252','Range20_Pct','MedianVolume20_Tech','MedianTurnover20_Native','Feature_Status']
    miss=[x for x in cols if x not in f.columns]
    if miss: raise SystemExit(f'missing persisted feature cols: {miss}')
    x=p.merge(f[cols],on='WS_ID',how='left',validate='one_to_one')
    if x.AsOf.astype(str).str.strip().eq('').any():
        x[x.AsOf.astype(str).str.strip().eq('')][['WS_ID','Name','Primary_Universe_Index']].to_csv(out/'p0_missing_feature_rows_v0.17.csv',index=False)
        raise SystemExit('not all 2037 partial rows have feature rows')

    nums=['Close_Tech','EMA20','EMA50','SMA200','ATR14_Wilder_DEV','R5','R20','R60','High20','High60','High252','Low20','Low60','Dist_EMA20','Dist_EMA50','Dist_SMA200','Dist_High252','Range20_Pct','MedianVolume20_Tech','MedianTurnover20_Native']
    for n in nums: x[n]=pd.to_numeric(x[n],errors='coerce')
    x['P0_Core_Feature_Complete_v0_17']=x[nums].notna().all(axis=1)
    x['Obs_Close_Above_EMA20']=x.Close_Tech>x.EMA20
    x['Obs_Close_Above_EMA50']=x.Close_Tech>x.EMA50
    x['Obs_Close_Above_SMA200']=x.Close_Tech>x.SMA200
    x['Obs_R20_Positive']=x.R20>0; x['Obs_R60_Positive']=x.R60>0
    x['Obs_R20_Warning_18pct']=x.R20>=.18; x['Obs_R60_Warning_30pct']=x.R60>=.30
    x['P0_Dry_Run_Status_v0_17']='NO_AUTOMATED_LANE_DECISION_PARAMETERS_NOT_VALIDATED'
    x['P0_PASS_v0_17']=False; x['P0_FAIL_NO_PRICE_SETUP_v0_17']=False; x['P0_MULTI_LANE_v0_17']=False
    x['P0_DATA_ERROR_v0_17']=~x.P0_Core_Feature_Complete_v0_17
    keep=['Research_Partial_Rank_v0_16','WS_ID','Name','Country','Primary_Ticker','Primary_MIC','Primary_Currency','Primary_Universe_Index','AsOf','Bars']+nums+['P0_Core_Feature_Complete_v0_17','Obs_Close_Above_EMA20','Obs_Close_Above_EMA50','Obs_Close_Above_SMA200','Obs_R20_Positive','Obs_R60_Positive','Obs_R20_Warning_18pct','Obs_R60_Warning_30pct','P0_Dry_Run_Status_v0_17','P0_PASS_v0_17','P0_FAIL_NO_PRICE_SETUP_v0_17','P0_MULTI_LANE_v0_17','P0_DATA_ERROR_v0_17']
    x[[k for k in keep if k in x.columns]].to_csv(out/'p0_dry_run_observations_v0.17.csv',index=False)

    cov=[]
    for n in nums:
        k=int(x[n].notna().sum()); cov.append([n,k,len(x)-k,round(100*k/len(x),4)])
    pd.DataFrame(cov,columns=['Field','Rows_Present','Rows_Missing','Coverage_Pct']).to_csv(out/'p0_field_coverage_v0.17.csv',index=False)
    pd.DataFrame(lane_rows(),columns=['Lane','Locally_Measurable_Now','Available_Inputs','Missing_or_Not_Promoted']).assign(Automated_P0_Decision_v0_17='NOT_ALLOWED').to_csv(out/'p0_lane_capability_matrix_v0.17.csv',index=False)
    x.groupby('AsOf').size().reset_index(name='Rows').sort_values('AsOf').to_csv(out/'p0_feature_asof_distribution_v0.17.csv',index=False)

    params={'schema':'WELT_SWING_P0_PARAMETER_REGISTRY_V0_17','automation_validation_status':'NOT_VALIDATED','p0_numeric_pass_thresholds':[],
      'explicit_master_spec_numbers_not_promoted_to_p0_pass':[
        {'name':'later_breakout_entry_distance','value':'about <=1 ATR over pivot','use':'LATER_STAGE_REFERENCE_ONLY_NOT_P0_PASS'},
        {'name':'later_breakout_rvol_confirmation','value':'about >=1.3','use':'LATER_A_CONFIRMATION_ONLY_NOT_P0_PASS'},
        {'name':'later_climax_range_warning','value':'about >2 ATR daily range with extreme volume and weak close','use':'LATER_STAGE_REFERENCE_ONLY_NOT_P0_PASS'},
        {'name':'runup_warning_20d','value':0.18,'use':'WARNING_ONLY_NOT_AUTOMATIC_EXCLUSION'},
        {'name':'runup_warning_60d','value':0.30,'use':'WARNING_ONLY_NOT_AUTOMATIC_EXCLUSION'}],
      'policy':['No invented precise P0 threshold where none is validated.','Parameters versioned/frozen before automated P0.','Qualitative structural DEV classification is allowed but is not a validated automated scan.']}
    (out/'p0_parameter_registry_v0.17.json').write_text(json.dumps(params,indent=2,ensure_ascii=False))

    cap={'schema':'WELT_SWING_P0_CAPABILITY_AUDIT_V0_17','partial_rows':len(x),'feature_matched_rows':len(x),'core_feature_complete_rows':int(x.P0_Core_Feature_Complete_v0_17.sum()),'data_error_rows':int(x.P0_DATA_ERROR_v0_17.sum()),
      'available_local_capabilities':['EMA20/EMA50/SMA200','ATR14','R5/R20/R60','20/60/252d highs','20/60d lows','EMA/high distances','Range20','MedianVolume20','MedianTurnover20'],
      'missing_or_unpromoted_for_validated_automated_p0':['validated algorithmic P0 lane thresholds','base/pivot/VCP detector','multi-day pullback/retest/reclaim/higher-low features','current RVOL','validated climax detector','20/60d RS versus home market and sector','post-impulse hold/drift features','mean-reversion stabilization detector','globally synchronized current AsOf'],
      'automated_p0_ready':False,'qualitative_structural_dev_possible':True}
    (out/'p0_capability_audit_v0.17.json').write_text(json.dumps(cap,indent=2,ensure_ascii=False))

    summary={'schema':SCHEMA,'generated_utc':datetime.now(timezone.utc).isoformat(),'run_status':'P0_RESEARCH_PARTIAL_DRY_RUN_V0_17_COMPLETE_NOT_AUTOMATION_READY','input_snapshot_id':m16['snapshot_id'],'partial_rows':len(x),'feature_matched_rows':len(x),'core_feature_complete_rows':int(x.P0_Core_Feature_Complete_v0_17.sum()),'p0_data_error_rows':int(x.P0_DATA_ERROR_v0_17.sum()),'p0_pass_rows':0,'p0_fail_no_price_setup_rows':0,'p0_multi_lane_rows':0,'p0_run':False,'p0_dry_run':True,'validated_automated_p0_run':False,'automated_p0_ready':False,'strict_u3k_frozen':False,'full_scan_claim':False,'research_partial_mode':True,'productive_trading_authority':False,'alpha_vantage_allowed':False,'web_calls_per_security':False,'external_reference_requests':0,'next_stage':'P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION','required_result_wording':'bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage'}
    (out/'summary_v0.17.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    checkpoint={'schema':'WELT_SWING_STAGE_CHECKPOINT_V0_17','run_id':c['run_id'],'stage_id':'P0_RESEARCH_PARTIAL_PARAMETER_FREEZE_AND_DRY_RUN','stage_version':'v0.17','status':'PARTIAL','input_count':len(x),'checked_count':len(x),'pass_count':0,'fail_count':0,'data_error_count':int(x.P0_DATA_ERROR_v0_17.sum()),'quarantine_count':0,'p0_survivor_count':0,'validated_automated_p0_run':False,'next_stage':'P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION'}
    (out/'stage_checkpoint_v0.17.json').write_text(json.dumps(checkpoint,indent=2,ensure_ascii=False))
    print(json.dumps(summary,ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/p0_research_partial_dry_run_v0.17.json'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else: run(Path(a.config))
if __name__=='__main__': main()
