#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT/"universe"/"research_partial_1633.csv"
EV = ROOT/"config"/"mapping_evidence_acquisition_v0.42.csv"
FROZEN = ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
OUT = ROOT/"output_instrument_share_class_v0_51"
IDENTITY = ("WS_ID","ISIN","Primary_MIC","Primary_Ticker","Primary_Currency","Name")
ORDINARY = {"ordinary shares","ordinary shares / actions ordinaires","B share","ordinary shares / azioni ordinarie","B shares","ordinary no-par shares","ordinary shares / acciones ordinarias","A share","ordinary bearer shares","bearer shares with no par value","no-par-value registered ordinary shares","registered no-par-value ordinary shares","stimmberechtigte Inhaber-Stammaktie","Registered shares without par value (ordinary equity)","ordinary shares (KGaA)","ordinary registered shares / Namensaktien","no-par value bearer shares","Inhaber-Stammaktie / ordinary equity","Inhaberaktie / ordinary equity","bearer ordinary shares","no-par-value bearer shares","Class A ordinary shares / acciones clase A","Class B ordinary shares","A shares"}
PREFERRED = {"preference shares","preference shares / Vorzugsaktien","preferred shares"}
REVIEW = {"registered shares","registered shares with restricted transferability","registered shares with no par value","registered no-par-value shares","bearer shares","C share","SDB","participation certificate","ordinary share represented by depositary receipts"}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def classify(text):
    s=(text or "").strip()
    if s in ORDINARY: return "ORDINARY_SHARE"
    if s in PREFERRED: return "PREFERRED_SHARE"
    if s in REVIEW: return "REVIEW"
    return "UNMAPPED_STRING"
def frozen_ok():
    if sum(1 for _ in open(FROZEN, encoding="utf-8"))!=1: raise SystemExit("frozen")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); args=ap.parse_args()
    frozen_ok(); uni_sha, ev_sha = sha(UNI), sha(EV)
    with open(UNI, encoding="utf-8-sig", newline="") as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; uni=list(reader)
    if len(uni)!=1633: raise SystemExit("universe")
    ev={r["WS_ID"]:r for r in csv.DictReader(open(EV, encoding="utf-8-sig"))}
    if len(ev)!=239: raise SystemExit("evidence")
    ident_before=[{k:r[k] for k in IDENTITY if k in r} for r in uni]
    unknown_before=sum(1 for r in uni if r["Instrument_Type"]=="UNKNOWN")
    rows=[]
    for r in uni:
        ws=r["WS_ID"]; e=ev.get(ws); prior=r["Instrument_Type"]
        share_ev=(e.get("Verified_Share_Class") if e else "") or ""
        if e:
            dest=classify(share_ev)
            if dest=="UNMAPPED_STRING": action,new_type,bucket="CONFLICT_UNMAPPED_STRING",prior,"CONFLICT"
            elif dest=="REVIEW": action,new_type,bucket="HOLD_REVIEW",prior,"REVIEW"
            elif prior not in ("UNKNOWN", dest): action,new_type,bucket="CONFLICT_EXISTING_TYPE",prior,dest
            else: action,new_type,bucket="APPLY",dest,dest
        else:
            action,new_type,bucket="NO_EVIDENCE",prior,"MISSING_EVIDENCE"
        write_share=bool(e) and action in ("APPLY","HOLD_REVIEW")
        rows.append({"WS_ID":ws,"Yahoo_Symbol":r.get("Yahoo_Symbol",""),"Mapping_Status":r.get("Mapping_Status",""),"Instrument_Type_Before":prior,"Instrument_Type_After":new_type,"Verified_Share_Class":share_ev,"Share_Class_After":share_ev if write_share else r.get("Share_Class",""),"Class_Bucket":bucket,"Action":action,"Universe_Write_Fields":("Instrument_Type,Share_Class" if action=="APPLY" else ("Share_Class" if action=="HOLD_REVIEW" else "NO"))})
    applied=[x for x in rows if x["Action"]=="APPLY"]
    conflicts=[x for x in rows if x["Action"].startswith("CONFLICT")]
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"classification_dry_run_1633_v0.51.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    slice_rows=[x for x in rows if x["WS_ID"] in ev]
    with open(OUT/"apply_slice_239_v0.51.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(slice_rows[0].keys())); w.writeheader(); w.writerows(slice_rows)
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_INSTRUMENT_SHARE_CLASS","version":"v0.51","run_mode":"APPLY" if args.apply else "DRY_RUN","unknown_before":unknown_before,"evidence_rows":239,"apply_ordinary":sum(1 for x in applied if x["Instrument_Type_After"]=="ORDINARY_SHARE"),"apply_preferred":sum(1 for x in applied if x["Instrument_Type_After"]=="PREFERRED_SHARE"),"hold_review":sum(1 for x in rows if x["Action"]=="HOLD_REVIEW"),"conflicts":len(conflicts),"unknown_without_evidence":sum(1 for x in rows if x["Action"]=="NO_EVIDENCE" and x["Instrument_Type_Before"]=="UNKNOWN"),"bucket_counts_239":dict(Counter(x["Class_Bucket"] for x in rows if x["WS_ID"] in ev)),"universe_identity_frozen":True,"eligibility_written":False,"u3k_frozen_members":0,"productive":False,"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if conflicts:
        json.dump(summary, open(OUT/"summary_v0.51.json","w",encoding="utf-8"), indent=2); print(json.dumps(summary, indent=2)); raise SystemExit("conflicts")
    if args.apply:
        by={x["WS_ID"]:x for x in rows if x["Action"] in ("APPLY","HOLD_REVIEW")}
        for r in uni:
            x=by.get(r["WS_ID"])
            if not x: continue
            if x["Action"]=="APPLY": r["Instrument_Type"]=x["Instrument_Type_After"]
            r["Share_Class"]=x["Verified_Share_Class"]
        if [{k:r[k] for k in IDENTITY if k in r} for r in uni]!=ident_before: raise SystemExit("identity")
        if sha(EV)!=ev_sha: raise SystemExit("evidence")
        with open(UNI,"w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(uni)
        frozen_ok()
        summary["instrument_after"]=dict(Counter(r["Instrument_Type"] for r in uni)); summary["applied_rows"]=len(by)
    json.dump(summary, open(OUT/"summary_v0.51.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
