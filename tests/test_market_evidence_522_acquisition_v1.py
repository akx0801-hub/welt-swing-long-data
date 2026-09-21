from __future__ import annotations
import csv,hashlib,json,tempfile,unittest
from datetime import date
from pathlib import Path
from unittest import mock
import pandas as pd
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
if __name__=='__main__':unittest.main()
