#!/usr/bin/env python3
import csv, json, hashlib, os, glob
from collections import Counter
from datetime import datetime, timezone

VERSION='v0.41'
STAGE='CURRENT_MASTER_RESEARCH_PARTIAL_1633_MANUAL_MAPPING_EVIDENCE_REVIEW'
OUT='output_current_master_research_partial_1633_mapping_evidence_review_v0_41'
REQ=['WS_ID','Name','ISIN','Primary_MIC','Primary_Exchange','Primary_Ticker','Primary_Currency','Primary_Universe_Index','v0_39_Static_Symbol_Relation','v0_39_Diagnostic_Classification','Current_Yahoo_Symbol','Static_Candidate_Yahoo_Symbol','Proposed_Yahoo_Symbol','Provider_Listing_Type','Primary_Listing_Status','Provider_Symbol_Status','Corporate_Action_Status','Evidence_Status','Evidence_Confidence','Evidence_Primary_URL','Evidence_Provider_URL','Evidence_Secondary_URL','Evidence_Note','Evidence_AsOf_UTC','Decision','Needs_Price_Verification']

def find_audit():
    xs=glob.glob('**/mapping_gap_audit_239_v0.39.csv',recursive=True)
    if len(xs)!=1: raise SystemExit(f'audit_file_count={len(xs)}')
    return xs[0]
def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def find_master(audit):
    cand=[]
    for p in glob.glob('**/*.csv',recursive=True):
        if p==audit or OUT in p or 'mapping_gap_audit' in p: continue
        try:
            with open(p,encoding='utf-8-sig',newline='') as f:
                h=next(csv.reader(f))
            if 'WS_ID' in h and any(x in h for x in ('Name','ISIN','Primary_Exchange')): cand.append(p)
        except Exception: pass
    return sorted(cand,key=lambda p: (('research_partial_1633' in p),('master' in p),p),reverse=True)[0] if cand else None
audit=find_audit(); src=read_csv(audit)
if len(src)!=239 or len({r.get('WS_ID','') for r in src})!=239: raise SystemExit('239_row_or_unique_ws_id_gate_failed')
counts=Counter(r.get('Diagnostic_Classification','') for r in src)
expected={'EXACT_PROVIDER_SYMBOL_NO_DATA':151,'CASE_NORMALIZATION_SUSPECT':78,'SUFFIX_MAPPING_SUSPECT':10}
if counts!=expected: raise SystemExit(f'diagnostic_split_gate_failed:{dict(counts)}')
master=find_master(audit); idx={r.get('WS_ID',''):r for r in (read_csv(master) if master else [])}
now=datetime.now(timezone.utc).isoformat()
rows=[]
for r in src:
    m=idx.get(r.get('WS_ID',''),{})
    rel=r.get('Static_Symbol_Relation','')
    diag=r.get('Diagnostic_Classification','')
    out={k:'' for k in REQ}
    out.update({'WS_ID':r.get('WS_ID',''),'Name':m.get('Name',m.get('Instrument_Name',r.get('Name',''))),'ISIN':m.get('ISIN',r.get('ISIN','')),'Primary_MIC':m.get('Primary_MIC',r.get('Primary_MIC','')),'Primary_Exchange':m.get('Primary_Exchange',r.get('Primary_Exchange','')),'Primary_Ticker':m.get('Primary_Ticker',r.get('Primary_Ticker','')),'Primary_Currency':m.get('Primary_Currency',r.get('Primary_Currency','')),'Primary_Universe_Index':m.get('Primary_Universe_Index',m.get('Universe_Index','')),'v0_39_Static_Symbol_Relation':rel,'v0_39_Diagnostic_Classification':diag,'Current_Yahoo_Symbol':r.get('Prior_Yahoo_Symbol',''),'Static_Candidate_Yahoo_Symbol':r.get('Candidate_Yahoo_Symbol',''),'Provider_Listing_Type':'UNVERIFIED','Primary_Listing_Status':'UNVERIFIED','Provider_Symbol_Status':'UNVERIFIED','Corporate_Action_Status':'UNVERIFIED','Evidence_Status':'NOT_RESEARCHED','Evidence_Confidence':'UNRESOLVED','Evidence_Note':'Evidence review scaffold; no provider/primary evidence asserted. Manual research required.','Evidence_AsOf_UTC':now,'Decision':'UNRESOLVED_MANUAL','Needs_Price_Verification':'NO'})
    rows.append(out)
os.makedirs(OUT,exist_ok=True)
def write(name,data,fields=REQ):
    with open(os.path.join(OUT,name),'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(data)
write('mapping_evidence_review_239_v0.41.csv',rows)
write('mapping_override_candidates_v0.41.csv',[r for r in rows if r['Proposed_Yahoo_Symbol']])
write('mapping_current_symbol_candidates_v0.41.csv',[r for r in rows if r['Decision']=='CONFIRMED_CURRENT_SYMBOL_BUT_PRICE_VERIFY_REQUIRED'])
write('mapping_corporate_action_candidates_v0.41.csv',[r for r in rows if r['Decision']=='CORPORATE_ACTION_REMAP_CANDIDATE'])
write('mapping_identity_review_required_v0.41.csv',[r for r in rows if r['Decision']=='PRIMARY_IDENTITY_REVIEW_REQUIRED'])
write('mapping_unresolved_v0.41.csv',[r for r in rows if r['Decision']=='UNRESOLVED_MANUAL'])
sources=[]
with open(os.path.join(OUT,'evidence_sources_v0.41.csv'),'w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['WS_ID','Evidence_Primary_URL','Evidence_Provider_URL','Evidence_Secondary_URL','Evidence_AsOf_UTC','Evidence_Status']);w.writeheader()
    for r in rows:w.writerow({k:r[k] for k in w.fieldnames})
summary={'stage':STAGE,'version':VERSION,'status':'PASS_SCAFFOLD_UNRESOLVED','run_mode':'MAPPING_EVIDENCE_REVIEW_ONLY','input_audit':audit,'input_master':master,'evidence_count':len(rows),'unique_ws_id_count':len({r['WS_ID'] for r in rows}),'diagnostic_counts':dict(counts),'decision_counts':dict(Counter(r['Decision'] for r in rows)),'confidence_counts':dict(Counter(r['Evidence_Confidence'] for r in rows)),'strong_gates':{'exactly_239_rows':True,'exactly_239_unique_ws_ids':True,'diagnostic_split_exact':True,'identity_frozen':True,'universe_mutated':False,'eligibility_promoted':False,'mapping_override_created':False,'price_download':False,'fx_download':False,'alpha_vantage':False,'p0':False,'sector_rs':False,'swing_u3k_frozen_mutated':False,'productive':False},'research_status':'NO_EVIDENCE_ASSERTED_MANUAL_REVIEW_REQUIRED','created_utc':now}
for fn,obj in [('summary_v0.41.json',summary),('stage_checkpoint_v0.41.json',{'stage':STAGE,'version':VERSION,'status':'PASS_SCAFFOLD_UNRESOLVED','evidence_rows':239,'next_stage':'RESULT_REVIEW_BEFORE_V0_42'}),('manifest_v0.41.json',{'stage':STAGE,'version':VERSION,'files':sorted(os.listdir(OUT)),'input_sha256':hashlib.sha256(open(audit,'rb').read()).hexdigest()})]:
    with open(os.path.join(OUT,fn),'w',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)
print(json.dumps({'status':summary['status'],'evidence_count':239,'diagnostic_counts':dict(counts),'output':OUT},indent=2))
