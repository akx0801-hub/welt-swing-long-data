#!/usr/bin/env python3
from __future__ import annotations
import argparse, io, json, re, hashlib
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import pandas as pd, requests
from pypdf import PdfReader

SCHEMA="WELT_SWING_INSTRUMENT_RESOLUTION_TMX_V0_14"

def t(v):
    try:
        if pd.isna(v): return ""
    except Exception: pass
    return "" if v is None else str(v).strip()

def norm(s):
    s=unescape(s or "").replace("’","'").replace("‘","'").replace("–","-").replace("—","-")
    s=re.sub(r"<[^>]+>"," ",s); return re.sub(r"\s+"," ",s).strip().lower()

def decode_response(r):
    if "pdf" in (r.headers.get("Content-Type","").lower()) or r.content[:4]==b"%PDF":
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(r.content)).pages)
    for e in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try: return r.content.decode(e)
        except Exception: pass
    raise ValueError("decode failed")

def fetch_validate(session,spec,timeout):
    st={"Source_Name":spec["name"],"Source_URL":spec["url"],"HTTP_Status":"","Content_Type":"",
        "Bytes":0,"SHA256":"","Status":"REQUEST_ERROR","Error":""}
    try:
        r=session.get(spec["url"],timeout=timeout)
        st.update(HTTP_Status=r.status_code,Content_Type=r.headers.get("Content-Type",""),
                  Bytes=len(r.content),SHA256=hashlib.sha256(r.content).hexdigest())
        r.raise_for_status(); text=norm(decode_response(r))
        missing=[p for p in spec["required_phrases"] if norm(p) not in text]
        if missing: raise ValueError(f"missing phrases: {missing}")
        st["Status"]="SEMANTICS_VALIDATED"; return True,st
    except Exception as e:
        st["Error"]=f"{type(e).__name__}: {e}"[:900]; return False,st

def classify(symbol,pattern,present):
    if str(present).lower()!="true":
        return ("NOT_VERIFIED","UNKNOWN","CURRENT_TMX_SYMBOL_NOT_EXACTLY_CONFIRMED")
    if pattern=="NO_DOT_SUFFIX":
        return ("PASS","COMMON_STOCK_BY_COMPOSITE_AND_TMX_SYMBOL_RULE",
                "COMPOSITE_COMMON_OR_INCOME_TRUST_AND_TMX_UNIT_REQUIRES_SUFFIX")
    if pattern=="DOT_CLASS_LIKE":
        return ("PASS","COMMON_EQUITY_CLASS_BY_COMPOSITE_AND_TMX_SYMBOL_RULE",
                "TMX_SHARE_CLASS_SUFFIX_AND_COMPOSITE_EXCLUDES_NONCOMMON_SPECIAL_TYPES")
    if pattern in {"DOT_UN","DOT_PR","DOT_WARRANT","DOT_RIGHT","DOT_DEBENTURE"}:
        return ("FAIL","NON_COMMON_TMX_SUFFIX","TMX_SUFFIX_IDENTIFIES_NON_COMMON_SECURITY_TYPE")
    return ("NOT_VERIFIED","UNKNOWN","TMX_SUFFIX_PATTERN_NOT_DETERMINISTIC")

def strict_status(r):
    if t(r.get("Cache_Status"))!="READY": return "FAIL"
    lg=t(r.get("Liquidity_Gate"))
    if lg!="PASS": return "FAIL" if lg in {"FAIL","FAIL_STRICT"} else "NOT_VERIFIED"
    if t(r.get("Scalable_Gate"))=="FAIL": return "FAIL"
    d=t(r.get("Instrument_Decision_v0_14"))
    return "PASS" if d=="PASS" else ("FAIL" if d=="FAIL" else "NOT_VERIFIED")

def self_test():
    assert classify("ABX","NO_DOT_SUFFIX",True)[0]=="PASS"
    assert classify("CTC.A","DOT_CLASS_LIKE",True)[0]=="PASS"
    assert classify("AD.UN","DOT_UN",True)[0]=="FAIL"
    assert classify("ABX","NO_DOT_SUFFIX",False)[0]=="NOT_VERIFIED"
    print("INSTRUMENT_RESOLUTION_TMX_V0_14_SELF_TEST_PASS")

def run(cfgp):
    c=json.loads(Path(cfgp).read_text(encoding="utf-8")); out=Path(c["output_dir"]); out.mkdir(exist_ok=True)
    s=json.loads(Path(c["source_summary_v0_13"]).read_text(encoding="utf-8"))
    assert s["schema"]=="WELT_SWING_TMX_SYMBOL_SEMANTICS_PROBE_V0_13"
    assert s["run_status"]=="TMX_SYMBOL_SEMANTICS_PROBE_V0_13_COMPLETE_WITH_CURRENT_SYMBOL_EVIDENCE"
    assert s["source_manual_rows_v0_12"]==650 and s["strict_candidates_v0_13"]==2037
    assert s["ca_target_rows"]==105 and s["ca_current_symbol_matches"]==105 and s["ca_current_symbol_coverage"]==1.0
    assert s["p0_run"] is False and s["alpha_vantage_allowed"] is False

    q=pd.read_csv(c["source_manual_queue_v0_13"],keep_default_na=False,dtype=str)
    p=pd.read_csv(c["source_ca_presence_v0_13"],keep_default_na=False,dtype=str)
    full=pd.read_csv(c["source_full_eligibility_v0_12"],keep_default_na=False,dtype=str)
    assert len(q)==650 and q.WS_ID.is_unique and p.WS_ID.is_unique and full.WS_ID.is_unique
    ca=q[q.Primary_Universe_Index.eq("CA_TSX")].copy()
    assert len(ca)==105
    ca=ca.merge(p[["WS_ID","TMX_Target_Symbol","TMX_Suffix_Pattern","TMX_Current_Symbol_Present"]],
                on="WS_ID",how="left",validate="one_to_one")
    assert ca.TMX_Current_Symbol_Present.astype(str).str.lower().eq("true").all()
    if "Strict_Eligibility_v0_12" in full:
        assert full[full.WS_ID.isin(ca.WS_ID)].Strict_Eligibility_v0_12.eq("NOT_VERIFIED").all()

    ses=requests.Session(); ses.headers.update({"User-Agent":"Mozilla/5.0 WeltSwingLongDEV/0.14"})
    rows=[]; oks=[]
    for k in ("sp_tsx_methodology","tmx_symbol_policy"):
        ok,st=fetch_validate(ses,c["official_sources"][k],c["request_timeout_seconds"]); oks.append(ok); rows.append(st)
    pd.DataFrame(rows).to_csv(out/"source_status_v0.14.csv",index=False)
    sem=all(oks)

    if sem:
        x=ca.apply(lambda r: classify(r.TMX_Target_Symbol,r.TMX_Suffix_Pattern,r.TMX_Current_Symbol_Present),axis=1)
        ca[["Instrument_Decision_v0_14","Instrument_Type_Resolved_v0_14","Instrument_Resolution_Reason_v0_14"]]=pd.DataFrame(x.tolist(),index=ca.index)
        method="SP_TSX_COMPOSITE_ELIGIBILITY_PLUS_TMX_ROOT_SUFFIX_POLICY"
    else:
        ca["Instrument_Decision_v0_14"]="NOT_VERIFIED"; ca["Instrument_Type_Resolved_v0_14"]="UNKNOWN"
        ca["Instrument_Resolution_Reason_v0_14"]="OFFICIAL_SEMANTICS_REFERENCE_NOT_VALIDATED"; method="OFFICIAL_REFERENCE_VALIDATION_FAILED"
    ca["Instrument_Resolution_Method_v0_14"]=method
    ca["Instrument_Evidence_URL_v0_14"]=c["official_sources"]["sp_tsx_methodology"]["url"]+" | "+c["official_sources"]["tmx_symbol_policy"]["url"]
    ca["Instrument_Evidence_Note_v0_14"]="Combined official S&P/TSX Composite eligibility and TMX root/suffix semantics; v0.13 exact-current-symbol confirmation required."
    ca.to_csv(out/"tmx_security_type_resolution_v0.14.csv",index=False)

    for name,decision in [("tmx_new_pass_v0.14.csv","PASS"),("tmx_new_fail_v0.14.csv","FAIL"),("tmx_unresolved_v0.14.csv","NOT_VERIFIED")]:
        ca[ca.Instrument_Decision_v0_14.eq(decision)].to_csv(out/name,index=False)

    for nc,oc in [
        ("Instrument_Decision_v0_14","Instrument_Decision_v0_12"),
        ("Instrument_Type_Resolved_v0_14","Instrument_Type_Resolved_v0_12"),
        ("Instrument_Resolution_Method_v0_14","Instrument_Resolution_Method_v0_12"),
        ("Instrument_Resolution_Reason_v0_14","Instrument_Resolution_Reason_v0_12"),
        ("Instrument_Evidence_URL_v0_14","Instrument_Evidence_URL_v0_12"),
        ("Instrument_Evidence_Note_v0_14","Instrument_Evidence_Note_v0_12")]:
        full[nc]=full[oc] if oc in full else ""
    ov=ca.set_index("WS_ID")
    full=full.set_index("WS_ID")
    for col in [x for x in ov.columns if x.startswith("Instrument_") and x.endswith("_v0_14")]:
        if col in full.columns: full.loc[ov.index,col]=ov[col]
    full=full.reset_index()
    full["Strict_Eligibility_v0_14"]=full.apply(strict_status,axis=1)

    strict=full[full.Strict_Eligibility_v0_14.eq("PASS")].copy()
    strict["MedianTurnover20_EUR"]=pd.to_numeric(strict["MedianTurnover20_EUR"],errors="coerce")
    strict["MedianTurnover60_EUR"]=pd.to_numeric(strict["MedianTurnover60_EUR"],errors="coerce")
    strict=strict.sort_values(["MedianTurnover20_EUR","MedianTurnover60_EUR","WS_ID"],ascending=[False,False,True],kind="mergesort")
    strict.insert(0,"Strict_Candidate_Rank_v0_14",range(1,len(strict)+1))

    resolved=set(ca[ca.Instrument_Decision_v0_14.isin(["PASS","FAIL"])].WS_ID)
    rem=q[~q.WS_ID.isin(resolved)].copy()
    npass=(ca.Instrument_Decision_v0_14=="PASS").sum()
    assert len(strict)==2037+npass and len(rem)==650-len(resolved)

    full.to_csv(out/"eligibility_after_instrument_v0.14.csv",index=False)
    strict.to_csv(out/"strict_u3k_candidate_after_instrument_v0.14.csv",index=False)
    rem.to_csv(out/"instrument_manual_review_queue_v0.14.csv",index=False)
    rem.groupby("Primary_Universe_Index").size().reset_index(name="Rows").to_csv(out/"remaining_review_by_segment_v0.14.csv",index=False)
    ca.groupby(["TMX_Suffix_Pattern","Instrument_Decision_v0_14"]).size().reset_index(name="Rows").to_csv(out/"tmx_suffix_decision_counts_v0.14.csv",index=False)

    nfail=(ca.Instrument_Decision_v0_14=="FAIL").sum(); nun=(ca.Instrument_Decision_v0_14=="NOT_VERIFIED").sum()
    summary={"schema":SCHEMA,"generated_utc":datetime.now(timezone.utc).isoformat(),
      "run_status":"INSTRUMENT_RESOLUTION_TMX_V0_14_COMPLETE_WITH_REMAINING_REVIEW" if sem else "INSTRUMENT_RESOLUTION_TMX_V0_14_COMPLETE_WITH_SOURCE_BLOCK",
      "source_manual_rows_v0_13":650,"ca_target_rows":105,"official_semantics_validated":sem,
      "tmx_pass_rows":int(npass),"tmx_fail_rows":int(nfail),"tmx_unresolved_rows":int(nun),
      "remaining_manual_rows_v0_14":len(rem),"strict_candidates_v0_13":2037,"strict_candidates_v0_14":len(strict),
      "strict_freeze_allowed":len(rem)==0,"external_reference_requests":2,"max_external_reference_requests":2,
      "request_bound_respected":True,"p0_run":False,"productive_trading_authority":False,"alpha_vantage_allowed":False,
      "price_downloads_performed":False,"fx_downloads_performed":False,"web_calls_per_security":False,"canonical_master_mutated":False}
    (out/"summary_v0.14.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/instrument_resolution_tmx_v0.14.json"); ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test: self_test()
    else: run(a.config)

if __name__=="__main__": main()
