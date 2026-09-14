#!/usr/bin/env python3
import argparse,csv,importlib.util,io,json
from datetime import date
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=lambda x:R/x
SRC=P('universe/research_partial_1633.csv'); POL=P('config/history_qa_v1_policy.json'); MAP=P('scripts/generate_company_security_mapping_v1.py')
V53=P('output_qa_v0_53/history_bar_qa_1633_v0.53.csv'); V38=P('output_current_master_research_partial_1633_data_refresh_v0_38/history_gate_current_1633_v0.38.csv')
V38M=P('output_current_master_research_partial_1633_data_refresh_v0_38/manifest_v0.38.json'); V38C=P('config/current_master_research_partial_1633_mapping_history_liquidity_data_refresh_v0.38.json')
V47=P('output_history_download_applied_239_v0_47/history_qa_239_v0.47.csv'); V47S=P('output_history_download_applied_239_v0_47/summary_v0.47.json')
U1=P('output_us1/history_qa_us1.csv'); U1S=P('output_us1/summary_us1.json'); BR=P('output_us1_write/dry_run_write_plan.csv')
OUT=P('output_history_qa_v1/history_qa_v1_2527.csv')
F=['Security_Key','Source_WS_ID','Evidence_Source_WS_ID','History_Status','History_Start','History_End','History_Observation_Count','History_Valid_Observation_Count','Expected_Session_Count','Usable_Session_Count','Gap_Count','Gap_Share','Zero_Volume_Share','Last_Observation_Date','History_Currentness_Status','Listing_Resolution_Status','Adjustment_Integrity_Status','Source_ID','Evidence_Artifact','Source_AsOf','Retrieved_At','History_Policy_Version','QA_Confidence','QA_Flags']
M=['History_Start','History_End','History_Observation_Count','History_Valid_Observation_Count','Expected_Session_Count','Usable_Session_Count','Gap_Count','Gap_Share','Zero_Volume_Share','Last_Observation_Date']

def jr(p):return json.loads(p.read_text(encoding='utf-8'))
def cr(p,req):
 with p.open(encoding='utf-8-sig',newline='') as h:
  r=csv.DictReader(h); miss=set(req)-set(r.fieldnames or [])
  if miss:raise ValueError(f'{p}: missing {sorted(miss)}')
  return list(r)
def ix(rows,k,label):
 d={}
 for x in rows:
  v=(x.get(k)or'').strip()
  if not v or v in d:raise ValueError(f'{label}: invalid/duplicate {k}: {v}')
  d[v]=x
 return d
def skfn():
 s=importlib.util.spec_from_file_location('m',MAP); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.security_key
def iv(v):
 v=(v or'').strip();return None if not v else int(float(v))
def yn(v):
 v=(v or'').strip().upper();return 0 if v in {'','NO','FALSE','0'} else 1 if v in {'YES','TRUE'} else int(float(v))
def dt(v):
 try:return date.fromisoformat((v or'').strip()[:10])
 except:return None
def fl(pol,s):
 u=set(s);a=pol['allowed_qa_flags']
 if u-set(a):raise ValueError('unknown QA flag')
 return '|'.join(x for x in a if x in u)
def prec(pol,s):
 for x in pol['history_status_precedence']:
  if x in s:return x
 raise ValueError('no status')
def conf(st,cu,ad):
 if st in {'HISTORY_UNAVAILABLE','HISTORY_IDENTITY_UNRESOLVED','HISTORY_CONFLICT'}:return'UNRESOLVED'
 if st in {'HISTORY_PARTIAL','HISTORY_STALE','HISTORY_TOO_SHORT','HISTORY_GAPPED'}:return'LOW'
 n=(cu!='CURRENT')+(ad!='ADJUSTMENT_OK');return'HIGH' if n==0 else'MEDIUM' if n==1 else'LOW'
def base(c,sk,pol):
 w=(c.get('WS_ID')or'').strip();mic=(c.get('Primary_MIC')or'').strip();tic=(c.get('Primary_Ticker')or'').strip();q={x:'' for x in F}
 q.update(Security_Key=sk(w),Source_WS_ID=w,Listing_Resolution_Status='LISTING_RESOLVED' if mic and tic else'LISTING_PARTIAL' if mic or tic else'LISTING_UNRESOLVED',History_Policy_Version=pol['policy_version']);return q
def unavail(c,sk,pol,ident=False):
 q=base(c,sk,pol);q.update(History_Status='HISTORY_IDENTITY_UNRESOLVED' if ident else'HISTORY_UNAVAILABLE',History_Currentness_Status='UNAVAILABLE',Adjustment_Integrity_Status='ADJUSTMENT_UNKNOWN',Source_ID=(c.get('Source_ID')or'').strip(),Source_AsOf=(c.get('Source_AsOf')or'').strip(),QA_Confidence='UNRESOLVED');s={'MISSING_HISTORY_EVIDENCE','MISSING_CURRENTNESS_METADATA','ADJUSTMENT_UNKNOWN'}
 if ident:s.add('IDENTITY_UNRESOLVED')
 q['QA_Flags']=fl(pol,s);return q
def mat(a,b,pairs):return any((a.get(x)or'').strip() and (b.get(y)or'').strip() and (a.get(x)or'').strip()!=(b.get(y)or'').strip() for x,y in pairs)
def finish(q,pol,u,v,s,conflict=False,partial=False):
 has=(u or 0)>0 and(v or 0)>0;states=set()
 if conflict:states.add('HISTORY_CONFLICT');s.add('DATA_QUALITY_FAIL')
 if not has:states.add('HISTORY_UNAVAILABLE')
 if q['History_Currentness_Status']=='STALE':states.add('HISTORY_STALE');s.add('STALE_HISTORY')
 if q['History_Currentness_Status']=='UNKNOWN' and has:s.add('MISSING_CURRENTNESS_METADATA')
 if has and(u is None or v is None or u<pol['minimum_unique_bars'] or v<pol['minimum_valid_bars']):states.add('HISTORY_TOO_SHORT');s.add('SHORT_HISTORY')
 if partial:states.add('HISTORY_PARTIAL')
 if not states:states.add('HISTORY_OK')
 q['History_Status']=prec(pol,states)
 if q['History_Status']=='HISTORY_UNAVAILABLE':q['History_Currentness_Status']='UNAVAILABLE';[q.__setitem__(x,'') for x in M];s.add('MISSING_CURRENTNESS_METADATA')
 q['QA_Confidence']=conf(q['History_Status'],q['History_Currentness_Status'],q['Adjustment_Integrity_Status']);q['QA_Flags']=fl(pol,s);return q
def baseline(c,a,b38,b47,s47,pol,sk):
 q=base(c,sk,pol);w=q['Source_WS_ID'];s={'LEGACY_NORMALIZED'};q.update(Evidence_Source_WS_ID=w,History_Observation_Count=(a.get('Unique_Bars')or'').strip(),History_Valid_Observation_Count=(a.get('Valid_Bars')or'').strip(),History_Start=(a.get('First_Bar')or'').strip(),History_End=(a.get('Last_Bar')or'').strip());q['Last_Observation_Date']=q['History_End'];lin=(a.get('History_Source')or'').strip()
 if lin=='v0.47':
  b=b47.get(w);q.update(Source_ID='v0.47',Evidence_Artifact='output_history_download_applied_239_v0_47/history_qa_239_v0.47.csv',Source_AsOf=str(s47.get('as_of')or''),Retrieved_At=str(s47.get('as_of_utc')or''),Adjustment_Integrity_Status='ADJUSTMENT_PARTIAL');bad=b is None or mat(a,b,[('Unique_Bars','Unique_Bars'),('Valid_Bars','Valid_Bars'),('First_Bar','First_Bar'),('Last_Bar','Last_Bar')])
 else:
  b=b38.get(w);q.update(Source_ID='v0.38',Evidence_Artifact='output_current_master_research_partial_1633_data_refresh_v0_38/history_gate_current_1633_v0.38.csv',Adjustment_Integrity_Status='ADJUSTMENT_PARTIAL');bad=b is None
  if b:q.update(Source_AsOf=(b.get('Global_EOD_Safe_Cutoff')or'').strip(),Retrieved_At=(b.get('Fetch_Timestamp_UTC')or'').strip(),Zero_Volume_Share=(b.get('Zero_Volume_Share')or'').strip());bad|=mat(a,b,[('Unique_Bars','Unique_Daily_Bars'),('Valid_Bars','Valid_Completed_Bars'),('First_Bar','First_Valid_Bar'),('Last_Bar','Last_Completed_Bar')])
 u,v=iv(q['History_Observation_Count']),iv(q['History_Valid_Observation_Count']);la,so=dt(q['Last_Observation_Date']),dt(q['Source_AsOf']);q['History_Currentness_Status']='UNAVAILABLE' if not((u or 0)>0 and(v or 0)>0) else'UNKNOWN' if not la or not so else'STALE' if(so-la).days>pol['stale_after_calendar_days'] else'CURRENT';fu,du=yn(a.get('Future')),yn(a.get('Duplicates'));part=bool(fu or du)
 if fu:s.add('FUTURE_OBSERVATION')
 if du:s.add('DUPLICATE_OBSERVATION')
 if 'DATA_QUALITY_FAIL' in {(a.get('History_State')or'').strip(),(a.get('Bar_QA_Status')or'').strip()}:s.add('DATA_QUALITY_FAIL');part=True
 return finish(q,pol,u,v,s,bad,part)
def us1(c,b,h,su,pol,sk):
 if not b:return unavail(c,sk,pol,True)
 lg=(b.get('WS_ID')or'').strip();ok=(b.get('New_WS_ID')or'').strip()==(c.get('WS_ID')or'').strip() and all((b.get(k)or'').strip()==(c.get(k)or'').strip() for k in ['ISIN','Primary_MIC','Primary_Ticker'])
 if not ok:q=unavail(c,sk,pol,True);q.update(Evidence_Source_WS_ID=lg,Evidence_Artifact='output_us1_write/dry_run_write_plan.csv');return q
 if h is None:q=unavail(c,sk,pol);q.update(Evidence_Source_WS_ID=lg,Evidence_Artifact='output_us1/history_qa_us1.csv');return q
 q=base(c,sk,pol);s={'LEGACY_NORMALIZED','ADJUSTMENT_UNKNOWN','MISSING_CURRENTNESS_METADATA'};q.update(Evidence_Source_WS_ID=lg,Source_ID='US1_HISTORY_QA',Evidence_Artifact='output_us1/history_qa_us1.csv',Source_AsOf=str(su.get('source_as_of_utc')or''),Retrieved_At=str(su.get('source_as_of_utc')or''),Adjustment_Integrity_Status='ADJUSTMENT_UNKNOWN',History_Observation_Count=(h.get('Unique_Bars')or'').strip(),History_Valid_Observation_Count=(h.get('Valid_Bars')or'').strip(),History_Currentness_Status='UNKNOWN');bad=any((h.get(k)or'').strip()!=(c.get(k)or'').strip() for k in ['ISIN','Primary_MIC']);u,v=iv(q['History_Observation_Count']),iv(q['History_Valid_Observation_Count']);fu,du=yn(h.get('Future_Bars')),yn(h.get('Duplicate_Dates'));part=bool(fu or du)
 if fu:s.add('FUTURE_OBSERVATION')
 if du:s.add('DUPLICATE_OBSERVATION')
 if(h.get('History_State')or'').strip() not in {'PASS','PASS_HISTORY','PASS_HISTORY_CURRENT'}:s.add('DATA_QUALITY_FAIL');part=part or((u or 0)>0 and(v or 0)>0)
 return finish(q,pol,u,v,s,bad,part)
def build_rows():
 pol=jr(POL);sk=skfn();cur=cr(SRC,['WS_ID','ISIN','Primary_MIC','Primary_Ticker','Source_ID','Source_AsOf'])
 if len(cur)!=2527:raise ValueError('Research Partial count')
 ci=ix(cur,'WS_ID','current');a=cr(V53,['WS_ID','History_State','History_Source','Unique_Bars','Valid_Bars','First_Bar','Last_Bar','Future','Duplicates','Bar_QA_Status'])
 if len(a)!=1633:raise ValueError('v0.53 count')
 a=ix(a,'WS_ID','v0.53')
 if set(a)-set(ci):raise ValueError('obsolete v0.53 security')
 b38=ix(cr(V38,['WS_ID','Unique_Daily_Bars','Valid_Completed_Bars','First_Valid_Bar','Last_Completed_Bar','Zero_Volume_Share','Global_EOD_Safe_Cutoff','Fetch_Timestamp_UTC']),'WS_ID','v0.38');b47=ix(cr(V47,['WS_ID','History_QA','Unique_Bars','Valid_Bars','First_Bar','Last_Bar']),'WS_ID','v0.47');s47=jr(V47S);jr(V38M);jr(V38C);uh=ix(cr(U1,['WS_ID','ISIN','Primary_MIC','Unique_Bars','Valid_Bars','Future_Bars','Duplicate_Dates','History_State','History_Source']),'WS_ID','US1');su=jr(U1S);br={}
 for x in cr(BR,['WS_ID', 'ISIN', 'Primary_MIC', 'Primary_Ticker', 'New_WS_ID']):
  n=(x.get('New_WS_ID')or'').strip()
  if n:
   if n in br:raise ValueError('duplicate US1 bridge')
   br[n]=x
 if sum((x.get('Source_ID')or'').strip()=='US1_SP500_COMMON_EVIDENCE_GATE' for x in cur)!=372:raise ValueError('US1 current count')
 out=[]
 for c in cur:
  w=(c.get('WS_ID')or'').strip()
  if w in a:q=baseline(c,a[w],b38,b47,s47,pol,sk)
  elif(c.get('Source_ID')or'').strip()=='US1_SP500_COMMON_EVIDENCE_GATE':b=br.get(w);lg=(b.get('WS_ID')or'').strip() if b else'';q=us1(c,b,uh.get(lg) if lg else None,su,pol,sk)
  else:q=unavail(c,sk,pol)
  out.append(q)
 ws=[x['Source_WS_ID'] for x in out];ks=[x['Security_Key'] for x in out]
 if len(out)!=2527 or len(set(ws))!=2527 or len(set(ks))!=2527 or ws!=[(x.get('WS_ID')or'').strip() for x in cur]:raise ValueError('population/key/order invariant')
 return out
def generate_bytes():
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=F,lineterminator='\n',extrasaction='raise');w.writeheader();w.writerows(build_rows());return s.getvalue().encode()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=OUT);a=p.parse_args();d=generate_bytes();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(d);print('rows=2527');return 0
if __name__=='__main__':raise SystemExit(main())
