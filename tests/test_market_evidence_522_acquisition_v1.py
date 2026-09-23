from __future__ import annotations
import copy,csv,hashlib,io,json,tempfile,unittest
from datetime import date
from pathlib import Path
from unittest import mock
import pandas as pd
import numpy as np
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import acquire_market_evidence_522_v1 as a

def src(nu=369,na=153):
 r=[]
 for i in range(nu):
  m='XNYS' if i%2==0 else 'XNAS';t=f'U{i:03d}';r.append(dict(WS_ID=f'WS:{m}:{t}',ISIN=f'US{i:010d}',Primary_MIC=m,Primary_Ticker=t,Primary_Currency='USD',Yahoo_Symbol=t,Source_ID='US2_SP400_COMMON_ADMISSION'))
 for i in range(na):
  t=f'A{i:03d}';r.append(dict(WS_ID=f'WS:XASX:{t}',ISIN=f'AU{i:010d}',Primary_MIC='XASX',Primary_Ticker=t,Primary_Currency='AUD',Yahoo_Symbol=f'{t}.AX',Source_ID='AU1_EVIDENCE_ADMISSION_GATE'))
 return r
def repair_src():
 r=src()
 specs=[
  (0,'WS:XNAS:STRL','US8592411016','XNAS','STRL','USD','STRL','US2_SP400_COMMON_ADMISSION'),
  (1,'WS:XNAS:MEDP','US58506Q1094','XNAS','MEDP','USD','MEDP','US2_SP400_COMMON_ADMISSION'),
  (2,'WS:XNYS:MP','US5533681012','XNYS','MP','USD','MP','US2_SP400_COMMON_ADMISSION'),
  (3,'WS:XNYS:KD','US50155Q1004','XNYS','KD','USD','KD','US2_SP400_COMMON_ADMISSION'),
  (369,'WS:XASX:MSB','AU000000MSB8','XASX','MSB','AUD','MSB.AX','AU1_EVIDENCE_ADMISSION_GATE'),
  (370,'WS:XASX:TUA','AU0000089724','XASX','TUA','AUD','TUA.AX','AU1_EVIDENCE_ADMISSION_GATE'),
  (371,'WS:XASX:CTD','AU000000CTD3','XASX','CTD','AUD','CTD.AX','AU1_EVIDENCE_ADMISSION_GATE'),
 ]
 for i,ws,isin,mic,tic,ccy,y,sid in specs:r[i].update(WS_ID=ws,ISIN=isin,Primary_MIC=mic,Primary_Ticker=tic,Primary_Currency=ccy,Yahoo_Symbol=y,Source_ID=sid)
 return r
def mp(rows):return [dict(Security_Key='WSSEC:'+r['WS_ID'],Source_WS_ID=r['WS_ID'],Primary_MIC=r['Primary_MIC'],Primary_Ticker=r['Primary_Ticker']) for r in rows]
def repair_bound():
 s=repair_src();x=a.construct_cohort(s,mp(s))
 with mock.patch.object(a,'load_yahoo_symbol_overrides',return_value={}):return a.bind_provider_symbols(x)
def cfgfile(d):
 p=Path(d)/'cfg.json';p.write_text(json.dumps({'policy_version':a.POLICY,'history':{'closed_bar_cutoff_days':1},'output_dir':'output_market_evidence_522_v1'}));return p
def bound(r):q=dict(r);q.update(Security_Key='WSSEC:'+r['WS_ID'],Source_WS_ID=r['WS_ID'],Cohort='AU1' if r['Primary_MIC']=='XASX' else 'US2',Provider_Symbol=r['Yahoo_Symbol'],Provider_Mapping_Status='EXPLICIT_VERIFIED');return q
class Contract(unittest.TestCase):
 def test_cohort_369_153_522_and_unique_keys(self):
  x=a.construct_cohort(src(),mp(src()));self.assertEqual((len(x),sum(r['Cohort']=='US2' for r in x),sum(r['Cohort']=='AU1' for r in x)),(522,369,153));self.assertEqual(len({r['Security_Key'] for r in x}),522);self.assertEqual(len({r['Source_WS_ID'] for r in x}),522)
 def test_identity_hard_fail(self):
  s=src();m=mp(s);m[0]['Security_Key']=m[1]['Security_Key']
  with self.assertRaises(a.GovernanceFailure):a.construct_cohort(s,m)
 def test_provider_binding_and_contradiction(self):
  s=src(1,1);x=a.construct_cohort(s,mp(s),expected_us2=1,expected_au1=1)
  with mock.patch.object(a,'load_yahoo_symbol_overrides',return_value={}):y=a.bind_provider_symbols(x)
  self.assertEqual([r['Provider_Symbol'] for r in y],['U000','A000.AX'])
  s[1]['Yahoo_Symbol']='WRONG.AX';x=a.construct_cohort(s,mp(s),expected_us2=1,expected_au1=1)
  with mock.patch.object(a,'load_yahoo_symbol_overrides',return_value={}):
   with self.assertRaises(a.GovernanceFailure):a.bind_provider_symbols(x)
class Bars(unittest.TestCase):
 def setUp(self):self.r=bound(src(1,0)[0]);self.cl=a.RunClock('2026-09-20T12:00:00Z',date(2026,9,19));self.cfg=a.FreeDataConfig(min_valid_bars=1,ready_unique_bars=1,stale_calendar_days=10)
 def frame(self):return pd.DataFrame(dict(open=[10.,10.5],high=[11.,11.],low=[9.5,10.],close=[10.5,10.8],adj_close=[10.5,10.8],volume=[1000.,1100.],dividends=[0.,0.],stock_splits=[0.,0.],repaired=[0.,0.]),index=pd.to_datetime(['2026-09-18','2026-09-19']))
 def test_duplicate_before_normalization(self):
  f=self.frame();f=pd.concat([f,f.iloc[[1]]]);self.assertGreater(a.detect_duplicate_provider_dates(f),0);z=a.process_stock_frame(f,self.r,self.cl,config=self.cfg);self.assertEqual(z.qa['Acquisition_Status'],'DUPLICATE_DATE_CONFLICT');self.assertEqual(z.observations,[])
 def test_closed_bar_future_excluded_and_validity(self):
  f=self.frame();f.loc[pd.Timestamp('2026-09-20')]=f.iloc[-1];f.loc[pd.Timestamp('2026-09-19'),'high']=9.;z=a.process_stock_frame(f,self.r,self.cl,config=self.cfg);self.assertEqual(z.qa['Future_Dates'],1);self.assertTrue(all(o['Observation_Date']<='2026-09-19' for o in z.observations));self.assertTrue(any(o['Observation_Status']=='OBSERVATION_INVALID_OHLCV' for o in z.observations));self.assertEqual(len({(o['Security_Key'],o['Observation_Date']) for o in z.observations}),len(z.observations))
 def test_row_level_failure(self):self.assertEqual(a.row_level_failure(self.r,self.cl,'PROVIDER_UNAVAILABLE','TIMEOUT').qa['Acquisition_Status'],'PROVIDER_UNAVAILABLE')
class FxArtifacts(unittest.TestCase):
 def test_fx_bounded_no_future_fill(self):
  r=[dict(FX_Observation_Date='2026-09-18',Price_Currency='USD',FX_to_EUR=.86)];self.assertEqual(a.match_fx_to_session(r,'USD',date(2026,9,19),max_backward_days=10),(.86,date(2026,9,18)));self.assertIsNone(a.match_fx_to_session(r,'USD',date(2026,10,5),max_backward_days=10));self.assertIsNone(a.match_fx_to_session([dict(FX_Observation_Date='2026-09-20',Price_Currency='AUD',FX_to_EUR=.6)],'AUD',date(2026,9,19),max_backward_days=10))
 def test_reverse_direction(self):
  cl=a.RunClock('2026-09-20T12:00:00Z',date(2026,9,19));f=pd.DataFrame({'close':[2.]},index=pd.to_datetime(['2026-09-19']));r=a._extract_fx_rows_from_frame(f,currency='AUD',source_symbol='EURAUD=X',direction='REVERSE_EUR_TO_CCY_INVERTED',clock=cl,invert=True);self.assertEqual((r[0]['FX_Direction'],r[0]['FX_to_EUR']),('REVERSE_EUR_TO_CCY_INVERTED',.5))
 def test_artifact_schema_hash_determinism_universe_false(self):
  s=src();x=a.construct_cohort(s,mp(s))
  with mock.patch.object(a,'load_yahoo_symbol_overrides',return_value={}):x=a.bind_provider_symbols(x)
  br=a.binding_rows(x);cl=a.RunClock('2026-09-20T12:00:00Z',date(2026,9,19));qa=[a.row_level_failure(r,cl,'SECURITY_NOT_FOUND').qa for r in x];cfg={'artifacts':{'security_binding':'security_binding_522.csv','ohlcv_daily':'ohlcv_daily_522.csv','fx_daily':'fx_daily_522.csv','acquisition_qa':'acquisition_qa_522.csv','manifest':'acquisition_manifest_522.json'}}
  with tempfile.TemporaryDirectory() as d1,tempfile.TemporaryDirectory() as d2:
   m1=a.write_artifacts(Path(d1),bindings=br,observations=[],fx_rows=[],qa_rows=qa,clock=cl,repository_sha='abc',config=cfg);a.write_artifacts(Path(d2),bindings=br,observations=[],fx_rows=[],qa_rows=qa,clock=cl,repository_sha='abc',config=cfg)
   for n in ['security_binding_522.csv','ohlcv_daily_522.csv','fx_daily_522.csv','acquisition_qa_522.csv','acquisition_manifest_522.json']:self.assertEqual(Path(d1,n).read_bytes(),Path(d2,n).read_bytes())
   self.assertFalse(m1['universe_write'])
   for n,i in m1['artifact_hashes'].items():self.assertEqual(i['sha256'],hashlib.sha256(Path(d1,n).read_bytes()).hexdigest())
   for n,flds in [('security_binding_522.csv',a.BINDING_FIELDS),('ohlcv_daily_522.csv',a.OHLCV_FIELDS),('fx_daily_522.csv',a.FX_FIELDS),('acquisition_qa_522.csv',a.QA_FIELDS)]:
    with open(Path(d1,n),encoding='utf-8',newline='') as f:self.assertEqual(next(csv.reader(f)),flds)
 def test_offline_helpers_no_download(self):
  with mock.patch.object(a.YFinanceBatchClient,'download',side_effect=AssertionError('network forbidden')):
   s=src(1,1);x=a.construct_cohort(s,mp(s),expected_us2=1,expected_au1=1)
   with mock.patch.object(a,'load_yahoo_symbol_overrides',return_value={}):a.bind_provider_symbols(x)
class TargetedRepair7(unittest.TestCase):
 def setUp(self):self.full=repair_bound()
 def test_exact_seven_selected_after_full_522(self):
  x=a.select_authorized_repair7(self.full);self.assertEqual(len(x),7);self.assertEqual({r['Security_Key'] for r in x},a.REPAIR7_KEYS);self.assertEqual({r['Source_WS_ID'] for r in x},a.REPAIR7_IDS)
 def test_moga_sols_excluded(self):
  x=a.select_authorized_repair7(self.full);ids={r['Source_WS_ID'] for r in x};self.assertNotIn('WS:XNYS:MOGA',ids);self.assertNotIn('WS:XNAS:SOLS',ids)
 def test_missing_authorized_target_hard_fails(self):
  x=[dict(r) for r in self.full];x[0]['Security_Key']='WSSEC:OTHER';x[0]['Source_WS_ID']='WS:OTHER'
  with self.assertRaises(a.GovernanceFailure):a.select_authorized_repair7(x)
 def test_duplicate_target_hard_fails(self):
  x=[dict(r) for r in self.full];x[-1]=dict(x[0])
  with self.assertRaises(a.GovernanceFailure):a.select_authorized_repair7(x)
 def test_arbitrary_eighth_impossible(self):
  x=[dict(r) for r in self.full]+[dict(Security_Key='WSSEC:EIGHTH',Source_WS_ID='WS:EIGHTH',Cohort='US2')]
  with self.assertRaises(a.GovernanceFailure):a.select_authorized_repair7(x)
 def test_targeted_outputs_isolated(self):
  target=a.select_authorized_repair7(self.full);br=a.binding_rows(target);cl=a.RunClock('2026-09-20T12:00:00Z',date(2026,9,19));qa=[a.row_level_failure(r,cl,'DATA_QUALITY_FAIL','SUSPICIOUS_RETURN_NEEDS_REPAIR').qa for r in target]
  with tempfile.TemporaryDirectory() as d:
   m=a.write_repair7(Path(d),br,[],qa,cl,'abc');self.assertEqual(set(p.name for p in Path(d).iterdir()),{a.REPAIR7_BIND,a.REPAIR7_OHLCV,a.REPAIR7_QA,a.REPAIR7_MANIFEST});self.assertTrue({'security_binding_522.csv','ohlcv_daily_522.csv','fx_daily_522.csv','acquisition_qa_522.csv','acquisition_manifest_522.json'}.isdisjoint(set(p.name for p in Path(d).iterdir())));self.assertFalse(m['universe_write'])
 def test_modes_cannot_combine_before_canonical(self):
  with tempfile.TemporaryDirectory() as d:
   cfg=cfgfile(d)
   with mock.patch.object(sys,'argv',['p','--config',str(cfg),'--execute-acquisition','--execute-suspicious-return-repair-7','--repository-sha','abc']),mock.patch.object(a,'canonical',side_effect=AssertionError('canonical should not run')):
    with self.assertRaises(SystemExit):a.main()
 def test_targeted_main_binding_then_selection_and_stocks(self):
  calls=[];cl=a.RunClock('2026-09-20T12:00:00Z',date(2026,9,19))
  def can(_):calls.append('canonical');return 'CANONICAL'
  def bd(x,_):self.assertEqual(x,'CANONICAL');calls.append('bind');return self.full
  def st(rows,clock,cfg):calls.append('stocks');self.assertEqual(len(rows),7);self.assertEqual({r['Security_Key'] for r in rows},a.REPAIR7_KEYS);return [],[a.row_level_failure(r,cl,'DATA_QUALITY_FAIL').qa for r in rows]
  with tempfile.TemporaryDirectory() as d:
   cfg=cfgfile(d)
   with mock.patch.object(sys,'argv',['p','--config',str(cfg),'--execute-suspicious-return-repair-7','--repository-sha','abc','--retrieved-at','2026-09-20T12:00:00Z']),mock.patch.object(a,'canonical',side_effect=can),mock.patch.object(a,'bind',side_effect=bd),mock.patch.object(a,'stocks',side_effect=st),mock.patch.object(a,'write_repair7',return_value={'ok':1}):
    self.assertEqual(a.main(),0)
  self.assertEqual(calls,['canonical','bind','stocks'])
 def test_targeted_rejects_output_override_before_provider(self):
  with tempfile.TemporaryDirectory() as d:
   cfg=cfgfile(d)
   with mock.patch.object(sys,'argv',['p','--config',str(cfg),'--execute-suspicious-return-repair-7','--repository-sha','abc','--output-dir','output_market_evidence_522_v1']),mock.patch.object(a,'canonical',return_value='X'),mock.patch.object(a,'bind',return_value=self.full),mock.patch.object(a,'stocks',side_effect=AssertionError('provider path forbidden')):
    with self.assertRaises(SystemExit):a.main()
 def test_unknown_target_argument_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   cfg=cfgfile(d)
   with mock.patch.object(sys,'argv',['p','--config',str(cfg),'--execute-suspicious-return-repair-7','--target','MOGA']):
    with self.assertRaises(SystemExit):a.main()
 def test_full_acquisition_path_remains_522(self):
  cl=a.RunClock('2026-09-20T12:00:00Z',date(2026,9,19));seen={}
  def st(rows,clock,cfg):seen['stocks']=len(rows);return [],[a.row_level_failure(r,cl,'NO_HISTORY').qa for r in rows]
  with tempfile.TemporaryDirectory() as d:
   cfg=cfgfile(d)
   with mock.patch.object(sys,'argv',['p','--config',str(cfg),'--execute-acquisition','--repository-sha','abc','--retrieved-at','2026-09-20T12:00:00Z']),mock.patch.object(a,'canonical',return_value='X'),mock.patch.object(a,'bind',return_value=self.full),mock.patch.object(a,'stocks',side_effect=st),mock.patch.object(a,'acquire_fx',return_value=[]),mock.patch.object(a,'validate'),mock.patch.object(a,'write',return_value={'ok':1}):
    self.assertEqual(a.main(),0)
  self.assertEqual(seen['stocks'],522)
 def test_governance_constants_unchanged(self):self.assertEqual((a.N,a.NU,a.NA,a.STRICT,a.FROZEN),(522,369,153,759,0))
# Suspicious-return QA reconciliation v1 focused offline tests.
FIX={
'STRL':('WSSEC:WS:XNAS:STRL','WS:XNAS:STRL','2026-05-04','529.489990234375','2026-05-05','806.0','2429100.0'),
'MEDP':('WSSEC:WS:XNAS:MEDP','WS:XNAS:MEDP','2025-07-21','308.8800048828125','2025-07-22','477.7300109863281','4473400.0'),
'MP':('WSSEC:WS:XNYS:MP','WS:XNYS:MP','2025-07-09','30.030000686645508','2025-07-10','45.22999954223633','86416200.0'),
'KD':('WSSEC:WS:XNYS:KD','WS:XNYS:KD','2026-02-06','23.489999771118164','2026-02-09','10.59000015258789','60968900.0'),
'MSB':('WSSEC:WS:XASX:MSB','WS:XASX:MSB','2024-12-18','1.9800000190734863','2024-12-19','3.049999952316284','46747972.0'),
'TUA':('WSSEC:WS:XASX:TUA','WS:XASX:TUA','2026-05-15','6.099999904632568','2026-05-18','2.2699999809265137','21574277.0')}
RCL=a.RunClock('2026-09-21T12:00:00Z',date(2026,9,20))
RCFG=a.FreeDataConfig(min_valid_bars=1,ready_unique_bars=1,stale_calendar_days=10,suspicious_abs_return=0.50)
def rb(n):
 sk,ws,*_=FIX[n];mic=ws.split(':')[1];tic=ws.split(':')[2]
 return dict(Security_Key=sk,Source_WS_ID=ws,Cohort='AU1' if mic=='XASX' else 'US2',Primary_Currency='AUD' if mic=='XASX' else 'USD',Primary_MIC=mic,Primary_Ticker=tic,Provider_Symbol=tic+'.AX' if mic=='XASX' else tic,Provider_Mapping_Status='EXPLICIT_VERIFIED',ISIN='',Source_ID='')
def rf(n,third=None):
 sk,ws,d0,p0,d1,c1,vol=FIX[n];p=float(p0);c=float(c1);rows=[dict(open=p,high=p,low=p,close=p,adj_close=p,volume=1000.,dividends=0.,stock_splits=0.,repaired=0.),dict(open=c,high=max(c,c*1.05),low=min(c,c*.95),close=c,adj_close=c,volume=float(vol),dividends=0.,stock_splits=0.,repaired=0.)];dates=[d0,d1]
 if third is not None:z=float(third);rows.append(dict(open=z,high=z*1.05,low=z*.95,close=z,adj_close=z,volume=12345.,dividends=0.,stock_splits=0.,repaired=0.));dates.append('2026-05-06' if n=='STRL' else '2026-06-01')
 else:z=c*1.01;rows.append(dict(open=z,high=z*1.02,low=z*.98,close=z,adj_close=z,volume=12000.,dividends=0.,stock_splits=0.,repaired=0.));dates.append('2026-09-18')
 return pd.DataFrame(rows,index=pd.to_datetime(dates))
def ctdb():return dict(Security_Key='WSSEC:WS:XASX:CTD',Source_WS_ID='WS:XASX:CTD',Cohort='AU1',Primary_Currency='AUD',Primary_MIC='XASX',Primary_Ticker='CTD',Provider_Symbol='CTD.AX',Provider_Mapping_Status='EXPLICIT_VERIFIED',ISIN='',Source_ID='')
def ctdf(conflict=False):
 vals=[('2025-08-22',16.06999969482422,93277.),('2025-08-25',16.06999969482422,0.),('2025-08-26',16.06999969482422,1. if conflict else 0.),('2026-09-02',16.06999969482422,0.),('2026-09-03',2.319999933242798,24878302.),('2026-09-04',2.25,11883957.),('2026-09-18',2.30,5000000.)]
 return pd.DataFrame([dict(open=c,high=c*1.05,low=c*.95,close=c,adj_close=c,volume=v,dividends=0.,stock_splits=0.,repaired=0.) for _,c,v in vals],index=pd.to_datetime([d for d,_,_ in vals]))
def er():return {'rows':[],'by_key':{},'sha256':''}
def lr():return a.load_reconciliation_registry()
def registry_text(rows):
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=a.RECON_FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows);return s.getvalue()
class ReconciliationPolicy(unittest.TestCase):
 def test_r01_threshold_unchanged(self):self.assertEqual(a.FreeDataConfig().suspicious_abs_return,.50)
 def test_r02_detector_authoritative(self):self.assertEqual(a.qa_symbol_frame(rf('STRL'),config=RCFG,as_of=RCL.cutoff)['reason_code'],'SUSPICIOUS_RETURN_NEEDS_REPAIR')
 def test_r03_derived_count_matches(self):self.assertEqual(len(a.derive_extreme_events(rf('STRL'),rb('STRL'),RCFG)),a.qa_symbol_frame(rf('STRL'),config=RCFG,as_of=RCL.cutoff)['suspicious_returns'])
 def test_r04_unregistered_fail_closed(self):self.assertEqual(a.process_stock_frame(rf('STRL'),rb('STRL'),RCL,config=RCFG,registry=er()).qa['Acquisition_Status'],'DATA_QUALITY_FAIL')
 def test_r05_unregistered_state_explicit(self):self.assertIn('SUSPICIOUS_EXTREME_RETURN_UNVERIFIED',a.process_stock_frame(rf('STRL'),rb('STRL'),RCL,config=RCFG,registry=er()).qa['QA_Flags'])
 def test_r06_wrong_security_key_fails(self):
  rows=copy.deepcopy(lr()['rows']);rows[0]['Security_Key']='WSSEC:WS:XNAS:WRONG';rows[0]['Record_SHA256']=a.registry_record_sha(rows[0])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.csv';p.write_text(registry_text(rows))
   with self.assertRaises(a.GovernanceFailure):a.load_reconciliation_registry(p)
 def test_r07_wrong_source_id_fails(self):
  rows=copy.deepcopy(lr()['rows']);rows[0]['Source_WS_ID']='WS:XNAS:WRONG';rows[0]['Record_SHA256']=a.registry_record_sha(rows[0])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.csv';p.write_text(registry_text(rows))
   with self.assertRaises(a.GovernanceFailure):a.load_reconciliation_registry(p)
 def test_r08_wrong_date_does_not_verify(self):
  f=rf('STRL').copy();f.index=pd.to_datetime(['2026-05-03','2026-05-04','2026-09-18']);self.assertTrue(a.reconcile_extreme_events(f,rb('STRL'),RCL,RCFG,lr())['unresolved'])
 def test_r09_duplicate_key_fails(self):
  rows=copy.deepcopy(lr()['rows']);z=copy.deepcopy(rows[0]);z['Record_ID']='DUP';z['Record_SHA256']=a.registry_record_sha(z);rows.append(z)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.csv';p.write_text(registry_text(rows))
   with self.assertRaises(a.GovernanceFailure):a.load_reconciliation_registry(p)
 def test_r10_revoked_no_effect(self):
  reg=copy.deepcopy(lr());r=reg['rows'][0];r['Verification_Status']='REVOKED';r['Record_SHA256']=a.registry_record_sha(r);reg['by_key']={(x['Security_Key'],x['Observation_Date']):x for x in reg['rows']};self.assertTrue(a.reconcile_extreme_events(rf('STRL'),rb('STRL'),RCL,RCFG,reg)['unresolved'])
 def test_r11_bad_record_hash_fails(self):
  rows=copy.deepcopy(lr()['rows']);rows[0]['Record_SHA256']='0'*64
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.csv';p.write_text(registry_text(rows))
   with self.assertRaises(a.GovernanceFailure):a.load_reconciliation_registry(p)
 def test_r12_market_hash_mismatch_fails(self):
  f=rf('STRL');f.loc[pd.Timestamp('2026-05-05'),'volume']+=1;self.assertIn('RECONCILIATION_MARKET_EVIDENCE_MISMATCH',a.process_stock_frame(f,rb('STRL'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r13_ticker_only_impossible(self):
  r=rb('STRL');r['Security_Key']='WSSEC:WS:XNAS:FAKE';r['Source_WS_ID']='WS:XNAS:FAKE';self.assertTrue(a.reconcile_extreme_events(rf('STRL'),r,RCL,RCFG,lr())['unresolved'])
 def test_r14_source_guard(self):self.assertTrue(a.validate_registry_identities(lr(),[rb(n) for n in FIX]+[ctdb()]))
 def test_r15_strl(self):self.assertIn('VERIFIED_EXTREME_RETURN',a.process_stock_frame(rf('STRL'),rb('STRL'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r16_medp(self):self.assertIn('VERIFIED_EXTREME_RETURN',a.process_stock_frame(rf('MEDP'),rb('MEDP'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r17_mp(self):self.assertIn('VERIFIED_EXTREME_RETURN',a.process_stock_frame(rf('MP'),rb('MP'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r18_kd(self):self.assertIn('VERIFIED_EXTREME_RETURN',a.process_stock_frame(rf('KD'),rb('KD'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r19_msb(self):self.assertIn('VERIFIED_EXTREME_RETURN',a.process_stock_frame(rf('MSB'),rb('MSB'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r20_tua(self):self.assertIn('VERIFIED_EXTREME_RETURN',a.process_stock_frame(rf('TUA'),rb('TUA'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r21_second_event_unresolved(self):self.assertIn('SUSPICIOUS_EXTREME_RETURN_UNVERIFIED',a.process_stock_frame(rf('STRL',1600),rb('STRL'),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r22_repair_flag_no_readiness(self):self.assertEqual(a.process_stock_frame(rf('STRL'),rb('STRL'),RCL,config=RCFG,provider_repaired=True,registry=er()).qa['Acquisition_Status'],'DATA_QUALITY_FAIL')
 def test_r23_zero_volume_no_inference(self):self.assertNotIn('OBSERVATION_SUSPENSION_NONTRADING',{o['Observation_Status'] for o in a.process_stock_frame(ctdf(),ctdb(),RCL,config=RCFG,registry=er()).observations})
 def test_r24_ctd_continuity(self):self.assertIn('CONTINUITY_BREAK_SUSPENSION',a.process_stock_frame(ctdf(),ctdb(),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r25_ctd_rows_retained(self):self.assertEqual(len(a.process_stock_frame(ctdf(),ctdb(),RCL,config=RCFG,registry=lr()).observations),len(ctdf()))
 def test_r26_ctd_annotation(self):self.assertIn('OBSERVATION_SUSPENSION_NONTRADING',{o['Observation_Status'] for o in a.process_stock_frame(ctdf(),ctdb(),RCL,config=RCFG,registry=lr()).observations})
 def test_r27_ctd_segments(self):
  c=a.suspension_context(ctdf(),lr()['by_key'][('WSSEC:WS:XASX:CTD','2026-09-03')]);self.assertEqual(c['pre_segment'].index.max().date().isoformat(),'2025-08-22');self.assertEqual(c['post_segment'].index.min().date().isoformat(),'2026-09-03')
 def test_r28_ctd_cumulative_informational(self):self.assertAlmostEqual(a.suspension_context(ctdf(),lr()['by_key'][('WSSEC:WS:XASX:CTD','2026-09-03')])['cumulative_return'],2.319999933242798/16.06999969482422-1)
 def test_r29_ctd_conflict(self):self.assertIn('CONTINUITY_EVIDENCE_CONFLICT',a.process_stock_frame(ctdf(True),ctdb(),RCL,config=RCFG,registry=lr()).qa['QA_Flags'])
 def test_r29a_ctd_annotation_starts_at_formal_suspension(self):
  obs=a.process_stock_frame(ctdf(),ctdb(),RCL,config=RCFG,registry=lr()).observations;by={o['Observation_Date']:o['Observation_Status'] for o in obs};self.assertNotEqual(by['2025-08-25'],'OBSERVATION_SUSPENSION_NONTRADING');self.assertEqual(by['2025-08-26'],'OBSERVATION_SUSPENSION_NONTRADING')
 def test_r29b_ctd_boundary_removed_before_extreme_return_mask(self):self.assertEqual(a.derive_extreme_events(ctdf(),ctdb(),RCFG,lr()),[])
 def test_r29c_ctd_ohlcv_unchanged(self):
  obs=a.process_stock_frame(ctdf(),ctdb(),RCL,config=RCFG,registry=lr()).observations;z=next(o for o in obs if o['Observation_Date']=='2025-08-26');self.assertEqual((z['Close'],z['Volume']),(16.06999969482422,0.0))
 def test_r29d_revoked_continuity_does_not_break_adjacency(self):
  reg=copy.deepcopy(lr());rec=reg['by_key'][('WSSEC:WS:XASX:CTD','2026-09-03')];rec['Verification_Status']='REVOKED';rec['Record_SHA256']=a.registry_record_sha(rec);reg['by_key']={(x['Security_Key'],x['Observation_Date']):x for x in reg['rows']};self.assertEqual(len(a.derive_extreme_events(ctdf(),ctdb(),RCFG,reg)),1)
 def test_r30_hash_determinism(self):
  e=a.derive_extreme_events(rf('MEDP'),rb('MEDP'),RCFG)[0];self.assertEqual(a.market_evidence_sha(e),a.market_evidence_sha(copy.deepcopy(e)));self.assertEqual(a.registry_record_sha(lr()['rows'][0]),a.registry_record_sha(copy.deepcopy(lr()['rows'][0])))
 def test_r31_registry_order_irrelevant(self):
  reg=lr();rev={'rows':list(reversed(reg['rows'])),'by_key':dict(reversed(list(reg['by_key'].items()))),'sha256':reg['sha256']};self.assertEqual(a.process_stock_frame(rf('MP'),rb('MP'),RCL,config=RCFG,registry=reg).qa['Acquisition_Status'],a.process_stock_frame(rf('MP'),rb('MP'),RCL,config=RCFG,registry=rev).qa['Acquisition_Status'])
 def test_r32_registry_exact_population(self):self.assertEqual((len(lr()['rows']),sum(x['Reconciliation_State']=='VERIFIED_EXTREME_RETURN' for x in lr()['rows']),sum(x['Reconciliation_State']=='CONTINUITY_BREAK_SUSPENSION' for x in lr()['rows'])),(7,6,1))
 def test_r33_manifest_provenance(self):
  cfg={'artifacts':{'security_binding':'b.csv','ohlcv_daily':'o.csv','fx_daily':'f.csv','acquisition_qa':'q.csv','manifest':'m.json'}}
  with tempfile.TemporaryDirectory() as d:
   m=a.write(Path(d),[],[],[],[],RCL,'abc',cfg);self.assertEqual(m['Reconciliation_Policy_Version'],a.RECON_POLICY);self.assertEqual(m['Reconciliation_Registry_SHA256'],a.registry_file_sha())
if __name__=='__main__':unittest.main()
