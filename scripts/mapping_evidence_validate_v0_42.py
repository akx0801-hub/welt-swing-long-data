#!/usr/bin/env python3
import csv,json,hashlib,os,sys
from collections import Counter
from datetime import datetime,timezone

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __file__.endswith('/scripts/mapping_evidence_validate_v0_42.py') else os.getcwd()
CFG=os.path.join(ROOT,'config','mapping_evidence_acquisition_v0.42.csv')
OUT=os.path.join(ROOT,'output_mapping_evidence_v0_42')
AUD=os.path.join(ROOT,'output_current_master_research_partial_1633_data_gap_remediation_v0_39','mapping_gap_audit_239_v0.39.csv')
FROZEN=['WS_ID','ISIN','Primary_MIC','Primary_Exchange','Primary_Ticker','Primary_Currency','Primary_Universe_Index']
ALLOWED_DEC={'CONFIRMED_PROVIDER_SYMBOL_CANDIDATE','CONFIRMED_CURRENT_SYMBOL_BUT_PRICE_VERIFY_REQUIRED','CORPORATE_ACTION_REMAP_CANDIDATE','DELISTED_OR_INACTIVE_REVIEW','PRIMARY_IDENTITY_REVIEW_REQUIRED','PROVIDER_LISTING_NOT_FOUND','UNRESOLVED_MANUAL'}
ALLOWED_CONF={'HIGH','MEDIUM','LOW','UNRESOLVED'}; ALLOWED_RS={'NOT_STARTED','RESEARCHED','PARTIAL','BLOCKED'}
def rows(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rs,fields):
    with open(p,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rs)
def main():
    rs=rows(CFG); aud=rows(AUD); af={r['WS_ID']:r for r in aud}; errs=[]
    if len(rs)!=239 or len({r.get('WS_ID','') for r in rs})!=239: errs.append('evidence rows/unique WS_ID != 239')
    if set(af)!=set(r.get('WS_ID') for r in rs): errs.append('WS_ID set differs from v0.39 audit')
    if Counter(r.get('v0_39_Diagnostic_Classification',r.get('Diagnostic_Classification','')) for r in rs)!=Counter({'EXACT_PROVIDER_SYMBOL_NO_DATA':151,'CASE_NORMALIZATION_SUSPECT':78,'SUFFIX_MAPPING_SUSPECT':10}): errs.append('diagnostic split mismatch')
    for r in rs:
        a=af.get(r.get('WS_ID'))
        if not a: continue
        for k in FROZEN:
            if r.get(k,'')!=a.get(k,''): errs.append(f'frozen mismatch {r.get("WS_ID")} {k}')
        if r.get('Research_Status') not in ALLOWED_RS: errs.append(f'invalid Research_Status {r.get("WS_ID")}')
        if r.get('Evidence_Confidence') not in ALLOWED_CONF: errs.append(f'invalid confidence {r.get("WS_ID")}')
        if r.get('Decision') not in ALLOWED_DEC: errs.append(f'invalid decision {r.get("WS_ID")}')
        if r.get('Evidence_Confidence')=='HIGH':
            if not r.get('Evidence_Primary_URL') or not r.get('Evidence_Provider_URL') or not r.get('Proposed_Yahoo_Symbol'): errs.append(f'HIGH evidence incomplete {r.get("WS_ID")}')
            if r.get('Provider_Listing_Type') not in {'PRIMARY','SECONDARY','ADR','OTC'}: errs.append(f'HIGH provider type {r.get("WS_ID")}')
    bysym={}; coll=[]
    for r in rs:
        s=r.get('Proposed_Yahoo_Symbol','').strip()
        if s: bysym.setdefault(s,[]).append(r['WS_ID'])
    for s,ids in bysym.items():
        if len(ids)>1: coll.append({'Proposed_Yahoo_Symbol':s,'WS_IDs':'|'.join(ids),'Collision_Status':'REVIEW_REQUIRED'})
        for wid in ids:
            r=next(x for x in rs if x['WS_ID']==wid)
            if len(ids)>1 and r.get('Evidence_Confidence')=='HIGH': errs.append(f'collision marked HIGH {wid}')
    os.makedirs(OUT,exist_ok=True); fields=list(rs[0]) if rs else []
    write(os.path.join(OUT,'mapping_evidence_239_v0.42.csv'),rs,fields)
    groups={'high_confidence_candidates_v0.42.csv':[r for r in rs if r.get('Evidence_Confidence')=='HIGH'],'medium_confidence_candidates_v0.42.csv':[r for r in rs if r.get('Evidence_Confidence')=='MEDIUM'],'corporate_action_candidates_v0.42.csv':[r for r in rs if r.get('Decision')=='CORPORATE_ACTION_REMAP_CANDIDATE'],'identity_review_required_v0.42.csv':[r for r in rs if r.get('Decision')=='PRIMARY_IDENTITY_REVIEW_REQUIRED'],'provider_not_found_v0.42.csv':[r for r in rs if r.get('Decision')=='PROVIDER_LISTING_NOT_FOUND'],'unresolved_v0.42.csv':[r for r in rs if r.get('Evidence_Confidence') in {'LOW','UNRESOLVED'} or r.get('Decision')=='UNRESOLVED_MANUAL']}
    for fn,gr in groups.items(): write(os.path.join(OUT,fn),gr,fields)
    write(os.path.join(OUT,'candidate_collision_review_v0.42.csv'),coll,['Proposed_Yahoo_Symbol','WS_IDs','Collision_Status'])
    prog=[{'WS_ID':r['WS_ID'],'Research_Status':r.get('Research_Status',''),'Evidence_AsOf_UTC':r.get('Evidence_AsOf_UTC',''),'Decision':r.get('Decision','')} for r in rs]; write(os.path.join(OUT,'research_progress_v0.42.csv'),prog,list(prog[0]))
    counts=lambda k:dict(Counter(r.get(k,'') for r in rs))
    summary={'stage':'CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_EVIDENCE_ACQUISITION','version':'v0.42','run_mode':'MAPPING_EVIDENCE_ACQUISITION_ONLY','status':'FAILED' if errs else ('COMPLETE' if all(r.get('Research_Status') in {'RESEARCHED','PARTIAL','BLOCKED'} for r in rs) else 'IN_PROGRESS'),'evidence_rows':len(rs),'unique_ws_ids':len({r.get('WS_ID') for r in rs}),'research_status_counts':counts('Research_Status'),'confidence_counts':counts('Evidence_Confidence'),'decision_counts':counts('Decision'),'candidate_collisions':len(coll),'errors':errs,'universe_mutated':False,'eligibility_promoted':False,'price_download':False,'productive':False,'as_of_utc':datetime.now(timezone.utc).isoformat()}
    json.dump(summary,open(os.path.join(OUT,'summary_v0.42.json'),'w',encoding='utf-8'),indent=2)
    ck={'stage':'v0.42','research_status_counts':summary['research_status_counts'],'last_completed_market_mic':'','last_completed_ws_id':'','next_ws_id':next((r['WS_ID'] for r in rs if r.get('Research_Status')=='NOT_STARTED'),''),'as_of_utc':summary['as_of_utc']}; json.dump(ck,open(os.path.join(OUT,'stage_checkpoint_v0.42.json'),'w',encoding='utf-8'),indent=2)
    manifest={'files':sorted(os.listdir(OUT)),'evidence_sha256':hashlib.sha256(open(CFG,'rb').read()).hexdigest(),'as_of_utc':summary['as_of_utc']}; json.dump(manifest,open(os.path.join(OUT,'manifest_v0.42.json'),'w',encoding='utf-8'),indent=2)
    print(json.dumps(summary,indent=2)); return 1 if errs else 0
if __name__=='__main__': sys.exit(main())
