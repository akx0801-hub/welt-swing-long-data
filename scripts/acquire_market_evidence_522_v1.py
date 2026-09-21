#!/usr/bin/env python3
"""Bounded US2/AU1 market-evidence adapter. Import/offline-preflight is network-free."""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,io,json,math,os,sys,unicodedata,re
from collections import Counter
from dataclasses import dataclass
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
from typing import Any,Mapping,Sequence
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from price_cache import FreeDataConfig,YFinanceBatchClient,derive_yahoo_symbol,load_yahoo_symbol_overrides,normalize_symbol_frame,qa_symbol_frame,split_download_frame,technical_valid_mask
POLICY='WELT-SWING-MARKET-EVIDENCE-522-ACQUISITION-v1.0';SOURCE='YFINANCE_FREE'
N,NU,NA,STRICT,FROZEN=522,369,153,759,0
BIND=['Security_Key','Source_WS_ID','Cohort','ISIN','Primary_MIC','Primary_Ticker','Provider_Symbol','Provider_Mapping_Status','Price_Currency','Source_ID']
OHLCV=['Security_Key','Source_WS_ID','Observation_Date','Open','High','Low','Close','Adjusted_Close','Volume','Dividend','Stock_Split','Price_Currency','Primary_MIC','Primary_Ticker','Provider_Symbol','Provider_Repaired','Source_ID','Source_AsOf','Retrieved_At','Adjustment_Status','Observation_Status']
FX=['FX_Observation_Date','Price_Currency','FX_to_EUR','FX_Source_Symbol','FX_Direction','Source_ID','Source_AsOf','Retrieved_At','Observation_Status']
QA=['Security_Key','Source_WS_ID','Cohort','Provider_Symbol','Acquisition_Status','Unique_Observations','Valid_Observations','Invalid_Observations','Duplicate_Dates','Future_Dates','Repaired_Observations','First_Observation_Date','Last_Observation_Date','Zero_Volume_Share','Adjustment_Status','Source_ID','Source_AsOf','Retrieved_At','QA_Flags']
RECON_POLICY='WELT-SWING-SUSPICIOUS-RETURN-QA-RECONCILIATION-v1.0'
RECON_REGISTRY=ROOT/'config/market_evidence_qa_reconciliation_registry_v1.csv'
RECON_FIELDS=['Policy_Version','Record_ID','Security_Key','Source_WS_ID','Observation_Date','Reconciliation_State','Verification_Status','Evidence_Type','Primary_Authority_Class','Primary_Evidence_Source','Primary_Evidence_Reference','Primary_Evidence_Date','Secondary_Authority_Class','Secondary_Evidence_Source','Secondary_Evidence_Reference','Secondary_Evidence_Date','Retrieved_At','Verified_At','Review_Method','Previous_Observation_Date','Previous_Close','Observation_Close','Observed_Return_Pct','Market_Evidence_SHA256','Suspension_Start_Date','Reinstatement_Date','Last_Pre_Suspension_Trade_Date','First_Post_Reinstatement_Trade_Date','Continuity_Action','Record_SHA256']
MARKET_HASH_FIELDS=['Security_Key','Source_WS_ID','Previous_Observation_Date','Observation_Date','Previous_Close','Observation_Close','Previous_Adjusted_Close','Observation_Adjusted_Close','Observation_Volume','Observation_Dividend','Observation_Stock_Split']
REPAIR7_PAIRS=(
 ('WSSEC:WS:XNAS:STRL','WS:XNAS:STRL'),
 ('WSSEC:WS:XNAS:MEDP','WS:XNAS:MEDP'),
 ('WSSEC:WS:XNYS:MP','WS:XNYS:MP'),
 ('WSSEC:WS:XNYS:KD','WS:XNYS:KD'),
 ('WSSEC:WS:XASX:MSB','WS:XASX:MSB'),
 ('WSSEC:WS:XASX:TUA','WS:XASX:TUA'),
 ('WSSEC:WS:XASX:CTD','WS:XASX:CTD'),
)
REPAIR7_KEYS=frozenset(k for k,_ in REPAIR7_PAIRS);REPAIR7_IDS=frozenset(w for _,w in REPAIR7_PAIRS)
REPAIR7_OUTPUT_DIR=ROOT/'output_market_evidence_repair_7_v1'
REPAIR7_BIND='security_binding_repair_7.csv';REPAIR7_OHLCV='ohlcv_repair_7.csv';REPAIR7_QA='repair_qa_7.csv';REPAIR7_MANIFEST='repair_manifest_7.json'
SOURCE_ACQUISITION_RUN_ID=35568241641;SOURCE_ACQUISITION_SHA='255bc56eef99c447eb659a1ece645fed27a825f7'
class GovernanceFailure(RuntimeError):pass
@dataclass(frozen=True)
class Clock: retrieved_at:str; cutoff:date
def txt(v): return '' if v is None or (isinstance(v,float) and math.isnan(v)) else str(v).strip()
def num(v):
 try:f=float(v);return f if math.isfinite(f) else ''
 except Exception:return ''
def readcsv(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def loadmap(path):
 s=importlib.util.spec_from_file_location('mapping_v1',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def cohort(src,maps,eu=NU,ea=NA):
 by={};out=[];seen=set();c=Counter()
 for m in maps:
  w=txt(m.get('Source_WS_ID'));k=txt(m.get('Security_Key'))
  if not w or not k or w in by:raise GovernanceFailure('invalid mapping keys')
  by[w]=m
 for r in src:
  sid=txt(r.get('Source_ID'));co='US2' if sid=='US2_SP400_COMMON_ADMISSION' else 'AU1' if sid=='AU1_EVIDENCE_ADMISSION_GATE' else ''
  if not co:continue
  w=txt(r.get('WS_ID'));m=by.get(w);k=txt(m.get('Security_Key')) if m else ''
  if not w or not k or w in seen:raise GovernanceFailure('missing/duplicate target identity')
  mic=txt(r.get('Primary_MIC')).upper();tic=txt(r.get('Primary_Ticker'));ccy=txt(r.get('Primary_Currency')).upper()
  if txt(m.get('Primary_MIC'))!=mic or txt(m.get('Primary_Ticker'))!=tic:raise GovernanceFailure('mapping/listing contradiction')
  if (co=='US2' and (mic not in {'XNYS','XNAS'} or ccy!='USD')) or (co=='AU1' and (mic!='XASX' or ccy!='AUD')):raise GovernanceFailure('cohort listing/currency contradiction')
  q=dict(r);q.update(Security_Key=k,Source_WS_ID=w,Cohort=co);out.append(q);seen.add(w);c[co]+=1
 if c!=Counter({'US2':eu,'AU1':ea}) or len({x['Security_Key'] for x in out})!=eu+ea:raise GovernanceFailure('cohort count/key mismatch')
 return out
def canonical(cfg,root=ROOT):
 p=root/cfg['source_universe'];src=readcsv(p)
 if len(src)!=2527:raise GovernanceFailure('Research Partial !=2527')
 m=loadmap(root/cfg['mapping_authority']);return cohort(src,m.build_rows(m.read_source(p)),cfg['target']['us2_rows'],cfg['target']['au1_rows'])
def bind(rows,override=None):
 ov=load_yahoo_symbol_overrides(override);used={};out=[]
 for r in rows:
  w=r['Source_WS_ID'];ex=txt(r.get('Yahoo_Symbol'));dr,st=derive_yahoo_symbol(r['Primary_Ticker'],r['Primary_MIC']);o=txt(ov.get(w))
  if not dr:raise GovernanceFailure('unresolved provider symbol')
  ps=o or ex or dr
  if o and ex and ex!=o:raise GovernanceFailure('explicit/override symbol contradiction')
  if not o and ex and ex!=dr:raise GovernanceFailure('explicit/derived symbol contradiction')
  if ps in used and used[ps]!=w:raise GovernanceFailure('provider symbol collision')
  used[ps]=w;q=dict(r);q.update(Provider_Symbol=ps,Provider_Mapping_Status='PROJECT_OVERRIDE' if o else 'EXPLICIT_VERIFIED' if ex else st);out.append(q)
 return out
def bindings(rows):return [{k:(txt(r.get('Primary_Currency')).upper() if k=='Price_Currency' else txt(r.get(k))) for k in BIND} for r in rows]
def select_authorized_repair7(rows):
 if len(rows)!=N or len({r['Security_Key'] for r in rows})!=N or len({r['Source_WS_ID'] for r in rows})!=N:raise GovernanceFailure('full 522 identity invariant required before repair selection')
 if Counter(r['Cohort'] for r in rows)!=Counter({'US2':NU,'AU1':NA}):raise GovernanceFailure('full 522 cohort invariant required before repair selection')
 bypair={}
 for r in rows:
  p=(r['Security_Key'],r['Source_WS_ID'])
  if p in bypair:raise GovernanceFailure('duplicate repair identity')
  bypair[p]=r
 if any(p not in bypair for p in REPAIR7_PAIRS):raise GovernanceFailure('authorized repair identity missing')
 out=[bypair[p] for p in REPAIR7_PAIRS]
 if len(out)!=7 or {r['Security_Key'] for r in out}!=REPAIR7_KEYS or {r['Source_WS_ID'] for r in out}!=REPAIR7_IDS:raise GovernanceFailure('repair-7 target invariant')
 return out
def clock(ts=None,days=1):
 d=datetime.fromisoformat(ts.replace('Z','+00:00')) if ts else datetime.now(timezone.utc);d=d.replace(tzinfo=d.tzinfo or timezone.utc).astimezone(timezone.utc);return Clock(d.strftime('%Y-%m-%dT%H:%M:%SZ'),d.date()-timedelta(days=days))
def dups(df):
 if df is None or df.empty:return 0
 i=pd.to_datetime(df.index,errors='coerce');
 try:i=i.tz_localize(None)
 except Exception:pass
 return int(pd.Index(i[~i.isna()]).duplicated(keep=False).sum())
def qbase(r,cl,status='NO_HISTORY',flags=''):
 return dict(Security_Key=r['Security_Key'],Source_WS_ID=r['Source_WS_ID'],Cohort=r['Cohort'],Provider_Symbol=r['Provider_Symbol'],Acquisition_Status=status,Unique_Observations=0,Valid_Observations=0,Invalid_Observations=0,Duplicate_Dates=0,Future_Dates=0,Repaired_Observations=0,First_Observation_Date='',Last_Observation_Date='',Zero_Volume_Share='',Adjustment_Status='ADJUSTMENT_UNKNOWN',Source_ID=SOURCE,Source_AsOf=cl.cutoff.isoformat(),Retrieved_At=cl.retrieved_at,QA_Flags=flags)
def _norm_text(v):
 s=txt(v)
 return '<NULL>' if not s else unicodedata.normalize('NFC',s).replace('\r\n','\n').replace('\r','\n')
def _norm_decimal(v):
 s=txt(v)
 if not s:return '<NULL>'
 try:d=Decimal(s)
 except InvalidOperation as e:raise GovernanceFailure('invalid numeric normalization') from e
 if not d.is_finite():raise GovernanceFailure('non-finite numeric normalization')
 if d==0:return '0'
 z=format(d,'f')
 return z.rstrip('0').rstrip('.') if '.' in z else z
def _hash_values(values):return hashlib.sha256((json.dumps(values,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')).hexdigest()
def market_evidence_sha(event):
 numeric={'Previous_Close','Observation_Close','Previous_Adjusted_Close','Observation_Adjusted_Close','Observation_Volume','Observation_Dividend','Observation_Stock_Split'}
 return _hash_values([_norm_decimal(event.get(f)) if f in numeric else _norm_text(event.get(f)) for f in MARKET_HASH_FIELDS])
def registry_record_sha(row):
 numeric={'Previous_Close','Observation_Close','Observed_Return_Pct'}
 return _hash_values([_norm_decimal(row.get(f)) if f in numeric else _norm_text(row.get(f)) for f in RECON_FIELDS[:-1]])
def _parse_date(v,label):
 try:return date.fromisoformat(txt(v))
 except Exception as e:raise GovernanceFailure(f'invalid {label}') from e
def _parse_utc(v,label):
 s=txt(v)
 if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',s):raise GovernanceFailure(f'invalid {label}')
 return datetime.strptime(s,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
def load_reconciliation_registry(path=RECON_REGISTRY):
 p=Path(path);data=p.read_bytes();reader=csv.DictReader(io.StringIO(data.decode('utf-8')))
 if list(reader.fieldnames or [])!=RECON_FIELDS:raise GovernanceFailure('reconciliation registry schema mismatch')
 rows=list(reader);by={};ids=set()
 for r in rows:
  rid=txt(r.get('Record_ID'));key=(txt(r.get('Security_Key')),txt(r.get('Observation_Date')))
  if not rid or rid in ids:raise GovernanceFailure('duplicate/missing reconciliation Record_ID')
  if not key[0] or not key[1] or key in by:raise GovernanceFailure('duplicate/missing reconciliation primary key')
  ids.add(rid)
  if txt(r.get('Policy_Version'))!=RECON_POLICY:raise GovernanceFailure('reconciliation policy mismatch')
  if key[0]!='WSSEC:'+txt(r.get('Source_WS_ID')) or not txt(r.get('Source_WS_ID')).startswith('WS:'):raise GovernanceFailure('reconciliation identity mismatch')
  _parse_date(key[1],'Observation_Date')
  if txt(r.get('Reconciliation_State')) not in {'VERIFIED_EXTREME_RETURN','CONTINUITY_BREAK_SUSPENSION'}:raise GovernanceFailure('unsupported reconciliation state')
  if txt(r.get('Verification_Status')) not in {'ACTIVE_VERIFIED','REVOKED'}:raise GovernanceFailure('unsupported verification state')
  if not txt(r.get('Primary_Evidence_Source')) or not txt(r.get('Primary_Evidence_Reference')):raise GovernanceFailure('missing primary evidence')
  _parse_date(r.get('Primary_Evidence_Date'),'Primary_Evidence_Date')
  if _parse_utc(r.get('Verified_At'),'Verified_At')<_parse_utc(r.get('Retrieved_At'),'Retrieved_At'):raise GovernanceFailure('verification precedes retrieval')
  for f in ('Previous_Observation_Date','Previous_Close','Observation_Close','Observed_Return_Pct','Market_Evidence_SHA256'):
   if not txt(r.get(f)):raise GovernanceFailure(f'missing {f}')
  _parse_date(r.get('Previous_Observation_Date'),'Previous_Observation_Date')
  if not re.fullmatch(r'[0-9a-f]{64}',txt(r.get('Market_Evidence_SHA256'))):raise GovernanceFailure('invalid market evidence hash')
  if txt(r.get('Reconciliation_State'))=='CONTINUITY_BREAK_SUSPENSION':
   for f in ('Suspension_Start_Date','Reinstatement_Date','Last_Pre_Suspension_Trade_Date','First_Post_Reinstatement_Trade_Date'):_parse_date(r.get(f),f)
   if txt(r.get('Continuity_Action'))!='BREAK_ORDINARY_RETURN_ADJACENCY':raise GovernanceFailure('invalid continuity action')
   if txt(r.get('Observation_Date'))!=txt(r.get('First_Post_Reinstatement_Trade_Date')):raise GovernanceFailure('suspension event date mismatch')
   if not (_parse_date(r.get('Last_Pre_Suspension_Trade_Date'),'Last_Pre')<_parse_date(r.get('First_Post_Reinstatement_Trade_Date'),'First_Post')):raise GovernanceFailure('invalid continuity order')
  elif any(txt(r.get(f)) for f in ('Suspension_Start_Date','Reinstatement_Date','Last_Pre_Suspension_Trade_Date','First_Post_Reinstatement_Trade_Date','Continuity_Action')):
   raise GovernanceFailure('unexpected suspension fields')
  if registry_record_sha(r)!=txt(r.get('Record_SHA256')):raise GovernanceFailure('invalid reconciliation Record_SHA256')
  by[key]=r
 return {'rows':rows,'by_key':by,'sha256':hashlib.sha256(data).hexdigest()}
def validate_registry_identities(registry,rows):
 pairs={(txt(r.get('Security_Key')),txt(r.get('Source_WS_ID'))) for r in rows}
 for rec in registry['rows']:
  if (rec['Security_Key'],rec['Source_WS_ID']) not in pairs:raise GovernanceFailure('reconciliation registry identity outside governed cohort')
 return True
def derive_extreme_events(x,r,cfg):
 x=normalize_symbol_frame(x);vm=technical_valid_mask(x);xv=x.loc[vm].copy()
 if xv.empty:return []
 ret=xv['close'].pct_change(fill_method=None);split=xv['stock_splits'].fillna(0).abs()>0;near=split|split.shift(1,fill_value=False)|split.shift(-1,fill_value=False);mask=(ret.abs()>cfg.suspicious_abs_return)&~near
 idxs=list(xv.index);out=[]
 for idx in list(xv.index[mask]):
  pos=idxs.index(idx)
  if pos==0:raise GovernanceFailure('extreme return without previous valid observation')
  pidx=idxs[pos-1];p=xv.loc[pidx];c=xv.loc[idx]
  e=dict(Security_Key=r['Security_Key'],Source_WS_ID=r['Source_WS_ID'],Previous_Observation_Date=pd.Timestamp(pidx).date().isoformat(),Observation_Date=pd.Timestamp(idx).date().isoformat(),Previous_Close=p['close'],Observation_Close=c['close'],Previous_Adjusted_Close=p['adj_close'],Observation_Adjusted_Close=c['adj_close'],Observation_Volume=c['volume'],Observation_Dividend=c['dividends'],Observation_Stock_Split=c['stock_splits'])
  e['Market_Evidence_SHA256']=market_evidence_sha(e);out.append(e)
 return out
def suspension_context(x,rec):
 x=normalize_symbol_frame(x);last_pre=_parse_date(rec['Last_Pre_Suspension_Trade_Date'],'Last_Pre');first_post=_parse_date(rec['First_Post_Reinstatement_Trade_Date'],'First_Post');dates=np.asarray(x.index.date,dtype=object);inside=(dates>last_pre)&(dates<first_post)
 conflict=False
 if inside.any():
  v=pd.to_numeric(x.loc[inside,'volume'],errors='coerce')
  conflict=bool((v.fillna(0)>0).any())
 pre=x.loc[dates==last_pre];post=x.loc[dates==first_post]
 if len(pre)!=1 or len(post)!=1:conflict=True;cumulative=''
 else:cumulative=float(post.iloc[0]['close']/pre.iloc[0]['close']-1)
 return {'inside_mask':inside,'conflict':conflict,'cumulative_return':cumulative,'pre_segment':x.loc[dates<=last_pre].copy(),'post_segment':x.loc[dates>=first_post].copy()}
def _status_after_reconciliation(x,cl,cfg):
 x=normalize_symbol_frame(x);vm=technical_valid_mask(x);u=len(x);v=int(vm.sum());bad=u-v;share=(bad/u if u else 0.0);filterable=(0<bad<=cfg.max_filterable_invalid_bars and share<=cfg.max_filterable_invalid_share and v>=cfg.ready_unique_bars)
 if u==0:return 'NO_HISTORY','NO_DATA'
 if bad>0 and not filterable:return 'DATA_QUALITY_FAIL','INVALID_OHLC_OR_VOLUME'
 xv=x.loc[vm].copy()
 if v and (cl.cutoff-xv.index.max().date()).days>cfg.stale_calendar_days:return 'STALE_HISTORY','LAST_BAR_TOO_OLD'
 if u>=cfg.ready_unique_bars and v>=cfg.min_valid_bars:return 'READY','ISOLATED_INVALID_BAR_EXCLUDED' if bad==1 else 'FILTERED_INVALID_BARS_EXCLUDED' if bad>1 else ''
 return 'SHORT_HISTORY','INSUFFICIENT_HISTORY'
def reconcile_extreme_events(x,r,cl,cfg,registry):
 qa=qa_symbol_frame(x,config=cfg,as_of=cl.cutoff);events=derive_extreme_events(x,r,cfg)
 if len(events)!=int(qa.get('suspicious_returns',0)):raise GovernanceFailure('extreme-event detector count mismatch')
 flags=[];unresolved=[];mismatch=[];verified=[];continuity=[];annotation_dates=set();conflict=False
 for e in events:
  rec=registry['by_key'].get((r['Security_Key'],e['Observation_Date'])) if registry else None
  if not rec or rec['Verification_Status']!='ACTIVE_VERIFIED':unresolved.append(e);continue
  if rec['Source_WS_ID']!=r['Source_WS_ID'] or rec['Market_Evidence_SHA256']!=e['Market_Evidence_SHA256']:mismatch.append(e);continue
  if rec['Reconciliation_State']=='VERIFIED_EXTREME_RETURN':verified.append(e);continue
  ctx=suspension_context(x,rec)
  if ctx['conflict']:conflict=True;continue
  continuity.append((e,ctx,rec));xx=normalize_symbol_frame(x)
  for d,m in zip(xx.index.date,ctx['inside_mask']):
   if m:annotation_dates.add(d.isoformat())
 if verified:flags.append('VERIFIED_EXTREME_RETURN')
 if continuity:flags.append('CONTINUITY_BREAK_SUSPENSION')
 if unresolved:flags.extend(['SUSPICIOUS_EXTREME_RETURN_UNVERIFIED','SUSPICIOUS_RETURN_NEEDS_REPAIR'])
 if mismatch:flags.extend(['DATA_QUALITY_FAIL','RECONCILIATION_MARKET_EVIDENCE_MISMATCH'])
 if conflict:flags.extend(['DATA_QUALITY_FAIL','CONTINUITY_EVIDENCE_CONFLICT'])
 if unresolved or mismatch or conflict:
  st='DATA_QUALITY_FAIL';reason='SUSPICIOUS_EXTREME_RETURN_UNVERIFIED' if unresolved else 'RECONCILIATION_MARKET_EVIDENCE_MISMATCH' if mismatch else 'CONTINUITY_EVIDENCE_CONFLICT'
 elif events and qa.get('status')=='QUARANTINE' and qa.get('reason_code')=='SUSPICIOUS_RETURN_NEEDS_REPAIR':st,reason=_status_after_reconciliation(x,cl,cfg)
 else:
  sm={'READY':'READY','WARMUP':'SHORT_HISTORY','STALE':'STALE_HISTORY','QUARANTINE':'DATA_QUALITY_FAIL','DOWNLOAD_FAILED':'NO_HISTORY'};st=sm.get(txt(qa.get('status')),'DATA_QUALITY_FAIL');reason=txt(qa.get('reason_code'))
 return dict(qa=qa,events=events,status=st,reason=reason,flags=flags,annotation_dates=annotation_dates,verified=verified,continuity=continuity,unresolved=unresolved,mismatch=mismatch,conflict=conflict)
def registry_file_sha(path=RECON_REGISTRY):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def process(df,r,cl,cfg,repaired=False,registry=None):
 dc=dups(df)
 if dc:
  q=qbase(r,cl,'DUPLICATE_DATE_CONFLICT','DUPLICATE_PROVIDER_DATE');q['Duplicate_Dates']=dc;return [],q,False
 x=normalize_symbol_frame(df)
 if x.empty:return [],qbase(r,cl,'NO_HISTORY','EMPTY_PROVIDER_HISTORY'),False
 fut=np.asarray(pd.Index(x.index.date)>cl.cutoff,dtype=bool);nf=int(fut.sum());x=x.loc[~fut].copy()
 if x.empty:
  q=qbase(r,cl,'NO_HISTORY','FUTURE_DATE_EXCLUDED');q['Future_Dates']=nf;return [],q,False
 vm=technical_valid_mask(x);adj='ADJUSTMENT_EVIDENCE_PRESENT' if x['adj_close'].notna().any() and {'dividends','stock_splits'}<=set(x.columns) else 'ADJUSTMENT_UNKNOWN'
 rg=registry if registry is not None else {'rows':[],'by_key':{},'sha256':''};rec=reconcile_extreme_events(x,r,cl,cfg,rg);qa=rec['qa'];st=rec['status'];fl=list(rec['flags'])
 if nf:fl.append('FUTURE_DATE_EXCLUDED')
 if st!='READY' and rec['reason'] and rec['reason'] not in fl:fl.append(rec['reason'])
 if repaired:fl.append('PROVIDER_REPAIR_PASS')
 obs=[]
 for (ts,z),ok in zip(x.iterrows(),vm.tolist()):
  ds=pd.Timestamp(ts).date().isoformat();ost='OBSERVATION_OK' if ok else 'OBSERVATION_INVALID_OHLCV'
  if ds in rec['annotation_dates'] and ost=='OBSERVATION_OK':ost='OBSERVATION_SUSPENSION_NONTRADING'
  obs.append(dict(Security_Key=r['Security_Key'],Source_WS_ID=r['Source_WS_ID'],Observation_Date=ds,Open=num(z.open),High=num(z.high),Low=num(z.low),Close=num(z.close),Adjusted_Close=num(z.adj_close),Volume=num(z.volume),Dividend=num(z.dividends),Stock_Split=num(z.stock_splits),Price_Currency=txt(r['Primary_Currency']).upper(),Primary_MIC=r['Primary_MIC'],Primary_Ticker=r['Primary_Ticker'],Provider_Symbol=r['Provider_Symbol'],Provider_Repaired=1 if repaired or bool(z.repaired) else 0,Source_ID=SOURCE,Source_AsOf=cl.cutoff.isoformat(),Retrieved_At=cl.retrieved_at,Adjustment_Status=adj,Observation_Status=ost))
 q=qbase(r,cl,st,'|'.join(sorted(set(fl))));q.update(Unique_Observations=int(qa.get('unique_bars',len(x))),Valid_Observations=int(qa.get('valid_bars',vm.sum())),Invalid_Observations=int(len(x)-vm.sum()),Future_Dates=nf,Repaired_Observations=sum(int(o['Provider_Repaired']) for o in obs),First_Observation_Date=txt(qa.get('first_bar_date')),Last_Observation_Date=txt(qa.get('last_bar_date')),Zero_Volume_Share=qa.get('zero_volume_share',''),Adjustment_Status=adj)
 return obs,q,bool(rec['unresolved'] or rec['mismatch'])
def dl(client,symbols,period,repair,retries):
 e=''
 for _ in range(retries+1):
  try:return client.download(symbols,period=period,repair=repair),''
  except Exception as x:e=f'{type(x).__name__}:{x}'
 return None,e
def stocks(rows,cl,cfg,client=None,registry=None):
 h=cfg['history'];pc=FreeDataConfig(batch_size=h['batch_size'],timeout_seconds=h['timeout_seconds'],initial_period=h['period'],interval=h['interval'],min_valid_bars=h['minimum_valid_bars'],ready_unique_bars=h['minimum_unique_bars'],stale_calendar_days=h['stale_calendar_days'],max_identical_retries=h['max_identical_retries'],repair_anomalies=h['repair_anomalies'],repair_batch_size=h['repair_batch_size']);client=client or YFinanceBatchClient(config=pc)
 if registry is None:registry=load_reconciliation_registry()
 validate_registry_identities(registry,rows);by={r['Provider_Symbol']:r for r in rows};res={};miss=[]
 def chunks(v,n):return [v[i:i+n] for i in range(0,len(v),n)]
 for b in chunks(list(by),pc.batch_size):
  raw,e=dl(client,b,h['period'],False,h['max_identical_retries'])
  if raw is None:
   for s in b:res[s]=([],qbase(by[s],cl,'PROVIDER_UNAVAILABLE',e),False)
   continue
  fr=split_download_frame(raw,b)
  for s in b:
   if s in fr:res[s]=process(fr[s],by[s],cl,pc,registry=registry)
   else:miss.append(s)
 for b in chunks(miss,pc.batch_size):
  raw,e=dl(client,b,h['period'],False,h['max_identical_retries']);fr=split_download_frame(raw,b) if raw is not None else {}
  for s in b:res[s]=process(fr[s],by[s],cl,pc,registry=registry) if s in fr else ([],qbase(by[s],cl,'SECURITY_NOT_FOUND','MISSING_AFTER_RESCUE' if raw is not None else e),False)
 if h['repair_anomalies']:
  rr=[s for s,v in res.items() if v[2]]
  for b in chunks(rr,h['repair_batch_size']):
   raw,_=dl(client,b,h['period'],True,h['max_identical_retries']);fr=split_download_frame(raw,b) if raw is not None else {}
   for s in b:
    if s in fr:res[s]=process(fr[s],by[s],cl,pc,True,registry)
 obs=[];qa=[]
 for r in rows:
  o,q,_=res.get(r['Provider_Symbol'],([],qbase(r,cl,'SECURITY_NOT_FOUND','NO_RESULT'),False));obs+=o;qa.append(q)
 return obs,qa
def fxrows(frame,ccy,sym,direction,cl,invert=False):
 if dups(frame):return []
 x=normalize_symbol_frame(frame);x=x.loc[np.asarray(pd.Index(x.index.date)<=cl.cutoff,dtype=bool)] if not x.empty else x;out=[]
 for ts,z in x.iterrows():
  v=num(z.close)
  if v=='' or v<=0:continue
  out.append(dict(FX_Observation_Date=pd.Timestamp(ts).date().isoformat(),Price_Currency=ccy,FX_to_EUR=1/v if invert else v,FX_Source_Symbol=sym,FX_Direction=direction,Source_ID=SOURCE,Source_AsOf=cl.cutoff.isoformat(),Retrieved_At=cl.retrieved_at,Observation_Status='OBSERVATION_OK'))
 return out
def acquire_fx(cl,cfg,client=None):
 f=cfg['fx'];h=cfg['history'];pc=FreeDataConfig(batch_size=2,timeout_seconds=h['timeout_seconds'],interval=h['interval'],max_identical_retries=h['max_identical_retries']);client=client or YFinanceBatchClient(config=pc);direct=f['direct_symbols'];sy=list(direct.values());raw,_=dl(client,sy,f['period'],False,h['max_identical_retries']);fr=split_download_frame(raw,sy) if raw is not None else {};out=[];missing=[]
 for c,s in direct.items():
  q=fxrows(fr[s],c,s,'DIRECT_CCY_TO_EUR',cl) if s in fr else []
  if q:out+=q
  else:missing.append(c)
 if missing:
  rev=f['reverse_symbols'];sy=[rev[c] for c in missing];raw,_=dl(client,sy,f['period'],False,h['max_identical_retries']);fr=split_download_frame(raw,sy) if raw is not None else {}
  for c in missing:
   s=rev[c]
   if s in fr:out+=fxrows(fr[s],c,s,'REVERSE_EUR_TO_CCY_INVERTED',cl,True)
 out.sort(key=lambda r:(r['Price_Currency'],r['FX_Observation_Date']));return out
def match_fx(rows,ccy,day,tol=10):
 q=[]
 for r in rows:
  try:d=date.fromisoformat(txt(r.get('FX_Observation_Date')));v=float(r.get('FX_to_EUR'))
  except Exception:continue
  if txt(r.get('Price_Currency')).upper()==ccy.upper() and d<=day and (day-d).days<=tol and v>0:q.append((d,v))
 if not q:return None
 d,v=max(q);return v,d
def csvbytes(rows,fields):
 b=io.StringIO(newline='');w=csv.DictWriter(b,fieldnames=fields,lineterminator='\n',extrasaction='raise');w.writeheader();w.writerows(rows);return b.getvalue().encode()
def write(out,br,obs,fx,qa,cl,sha,cfg):
 out.mkdir(parents=True,exist_ok=True);names=cfg['artifacts'];data={names['security_binding']:csvbytes(br,BIND),names['ohlcv_daily']:csvbytes(obs,OHLCV),names['fx_daily']:csvbytes(fx,FX),names['acquisition_qa']:csvbytes(qa,QA)}
 for n,v in data.items():(out/n).write_bytes(v)
 m=dict(schema='WELT_SWING_MARKET_EVIDENCE_522_ACQUISITION_MANIFEST_V1',policy_version=POLICY,Reconciliation_Policy_Version=RECON_POLICY,Reconciliation_Registry_SHA256=registry_file_sha(),repository_sha=sha,source_id=SOURCE,source_as_of=cl.cutoff.isoformat(),retrieved_at=cl.retrieved_at,target={'total':N,'US2':NU,'AU1':NA},research_partial=2527,strict=STRICT,frozen=FROZEN,universe_write=False,productive=False,artifact_rows={names['security_binding']:len(br),names['ohlcv_daily']:len(obs),names['fx_daily']:len(fx),names['acquisition_qa']:len(qa)},artifact_hashes={n:{'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for n,v in data.items()},acquisition_status_counts=dict(sorted(Counter(q['Acquisition_Status'] for q in qa).items())),fx_observation_counts=dict(sorted(Counter(x['Price_Currency'] for x in fx).items())))
 (out/names['manifest']).write_text(json.dumps(m,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');return m
def write_repair7(out,br,obs,qa,cl,sha):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);data={REPAIR7_BIND:csvbytes(br,BIND),REPAIR7_OHLCV:csvbytes(obs,OHLCV),REPAIR7_QA:csvbytes(qa,QA)}
 for n,v in data.items():(out/n).write_bytes(v)
 m=dict(schema='WELT_SWING_SUSPICIOUS_RETURN_REPAIR_7_MANIFEST_V1',policy_version=POLICY,Reconciliation_Policy_Version=RECON_POLICY,Reconciliation_Registry_SHA256=registry_file_sha(),mode='TARGETED_SUSPICIOUS_RETURN_REPAIR_7',repository_sha=sha,source_acquisition_run_id=SOURCE_ACQUISITION_RUN_ID,source_acquisition_repository_sha=SOURCE_ACQUISITION_SHA,source_id=SOURCE,source_as_of=cl.cutoff.isoformat(),retrieved_at=cl.retrieved_at,target={'total':7,'US2':4,'AU1':3},target_security_keys=[k for k,_ in REPAIR7_PAIRS],target_source_ws_ids=[w for _,w in REPAIR7_PAIRS],research_partial=2527,strict=STRICT,frozen=FROZEN,universe_write=False,productive=False,artifact_rows={REPAIR7_BIND:len(br),REPAIR7_OHLCV:len(obs),REPAIR7_QA:len(qa)},artifact_hashes={n:{'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for n,v in data.items()},acquisition_status_counts=dict(sorted(Counter(q['Acquisition_Status'] for q in qa).items())),repaired_observations=sum(int(q.get('Repaired_Observations') or 0) for q in qa))
 (out/REPAIR7_MANIFEST).write_text(json.dumps(m,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');return m
def validate_repair7(br,obs,qa,cl):
 if len(br)!=7 or len(qa)!=7 or {r['Security_Key'] for r in br}!=REPAIR7_KEYS or {r['Source_WS_ID'] for r in br}!=REPAIR7_IDS:raise GovernanceFailure('repair-7 binding invariant')
 if Counter(r['Cohort'] for r in br)!=Counter({'US2':4,'AU1':3}):raise GovernanceFailure('repair-7 cohort invariant')
 if {r['Security_Key'] for r in qa}!=REPAIR7_KEYS or {r['Source_WS_ID'] for r in qa}!=REPAIR7_IDS:raise GovernanceFailure('repair-7 QA identity invariant')
 seen=set()
 for r in obs:
  if r['Security_Key'] not in REPAIR7_KEYS or r['Source_WS_ID'] not in REPAIR7_IDS:raise GovernanceFailure('off-target repair evidence')
  k=(r['Security_Key'],r['Observation_Date'])
  if k in seen or date.fromisoformat(k[1])>cl.cutoff:raise GovernanceFailure('repair observation key/future invariant')
  seen.add(k)

def validate(br,obs,fx,qa,cl):
 if len(br)!=N or len(qa)!=N or len({r['Security_Key'] for r in br})!=N or len({r['Source_WS_ID'] for r in br})!=N:raise GovernanceFailure('522 key/count invariant')
 if Counter(r['Cohort'] for r in br)!=Counter({'US2':NU,'AU1':NA}):raise GovernanceFailure('cohort invariant')
 seen=set()
 for r in obs:
  k=(r['Security_Key'],r['Observation_Date'])
  if k in seen or date.fromisoformat(k[1])>cl.cutoff:raise GovernanceFailure('observation key/future invariant')
  seen.add(k)
 for r in fx:
  if r['Price_Currency'] not in {'USD','AUD'} or r['FX_Direction'] not in {'DIRECT_CCY_TO_EUR','REVERSE_EUR_TO_CCY_INVERTED'}:raise GovernanceFailure('FX invariant')

# Focused-test/readability aliases for the approved contract vocabulary.
BINDING_FIELDS=BIND;OHLCV_FIELDS=OHLCV;FX_FIELDS=FX;QA_FIELDS=QA
RunClock=Clock
def construct_cohort(source_rows,mapping_rows,**kw):
 return cohort(source_rows,mapping_rows,kw.get("expected_us2",NU),kw.get("expected_au1",NA))
def bind_provider_symbols(rows,*,override_path=None):return bind(rows,override_path)
binding_rows=bindings
detect_duplicate_provider_dates=dups
def process_stock_frame(df,binding,cl,*,config,provider_repaired=False,registry=None):
 o,q,r=process(df,binding,cl,config,provider_repaired,registry);return type("StockResult",(),{"observations":o,"qa":q,"repair_candidate":r})()
def row_level_failure(binding,cl,status,*flags):
 return type("StockResult",(),{"observations":[],"qa":qbase(binding,cl,status,"|".join(sorted(set(flags)))),"repair_candidate":False})()
def _extract_fx_rows_from_frame(frame,*,currency,source_symbol,direction,clock,invert):return fxrows(frame,currency,source_symbol,direction,clock,invert)
def match_fx_to_session(rows,currency,session_date,*,max_backward_days=10):return match_fx(rows,currency,session_date,max_backward_days)
def write_artifacts(output_dir,*,bindings,observations,fx_rows,qa_rows,clock,repository_sha,config,implementation_hashes=None):return write(Path(output_dir),bindings,observations,fx_rows,qa_rows,clock,repository_sha,config)
def validate_evidence_contract(bindings,observations,fx_rows,qa_rows,clock):return validate(bindings,observations,fx_rows,qa_rows,clock)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=ROOT/'config/market_evidence_522_acquisition_v1.json');ap.add_argument('--offline-preflight',action='store_true');ap.add_argument('--execute-acquisition',action='store_true');ap.add_argument('--execute-suspicious-return-repair-7',action='store_true');ap.add_argument('--repository-sha',default=os.getenv('GITHUB_SHA',''));ap.add_argument('--output-dir',type=Path);ap.add_argument('--retrieved-at');a=ap.parse_args();cfg=json.loads(a.config.read_text())
 modes=sum(bool(x) for x in (a.offline_preflight,a.execute_acquisition,a.execute_suspicious_return_repair_7))
 if cfg['policy_version']!=POLICY or modes!=1:raise SystemExit('policy/mode mismatch')
 rows=bind(canonical(cfg),ROOT/'config/yahoo_symbol_overrides.csv')
 if a.offline_preflight:print(json.dumps({'status':'OFFLINE_PREFLIGHT_PASS','target':len(rows),'network_calls':0,'universe_write':False}));return 0
 if not a.repository_sha:raise SystemExit('--repository-sha required')
 cl=clock(a.retrieved_at,cfg['history']['closed_bar_cutoff_days'])
 if a.execute_suspicious_return_repair_7:
  if a.output_dir is not None:raise SystemExit('targeted repair output directory is fixed')
  target=select_authorized_repair7(rows);br=bindings(target);obs,qa=stocks(target,cl,cfg);validate_repair7(br,obs,qa,cl);print(json.dumps(write_repair7(REPAIR7_OUTPUT_DIR,br,obs,qa,cl,a.repository_sha),sort_keys=True));return 0
 br=bindings(rows);obs,qa=stocks(rows,cl,cfg);fx=acquire_fx(cl,cfg);validate(br,obs,fx,qa,cl);print(json.dumps(write(a.output_dir or ROOT/cfg['output_dir'],br,obs,fx,qa,cl,a.repository_sha,cfg),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
