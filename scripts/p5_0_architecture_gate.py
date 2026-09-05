#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
MD=ROOT/"docs"/"spec"/"P5_0_Architecture_Coverage_Gate.md"
OUT=ROOT/"output_p5_0_architecture"
SEGS=[("USA","none","XNYS|XNAS","expansion"),("Europe","EU_STOXX600","XETR|XPAR|XLON|XSTO|XMIL|XAMS|XMAD|XCSE|XHEL|XBRU|XWBO|XDUB|XOSL|XWAR|XLIS|XSWX","conversion"),("Japan","JP_N225","XTKS","stage_strict"),("China","CN_CSI300","XSHG|XSHE","stage_strict"),("Taiwan","TW_TW50","XTAI","stage_strict"),("India","IN_NIFTY50","XNSE","stage_strict"),("Brazil","BR_IBRX100","BVMF","conversion"),("Canada","CA_TSX","XTSE","conversion"),("Hong Kong","HK_HSI","XHKG","conversion"),("Australia","none","XASX","expansion"),("Korea","none","XKRX","expansion")]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tbl(headers, rows):
    lines=["| "+" | ".join(headers)+" |","|"+"|".join("---" for _ in headers)+"|"]
    for r in rows: lines.append("| "+" | ".join(str(x) for x in r)+" |")
    return "\n".join(lines)
def main():
    if sum(1 for _ in open(FROZEN, encoding="utf-8"))!=1: raise SystemExit("frozen")
    uni_sha=sha(UNI)
    uni=list(csv.DictReader(open(UNI, encoding="utf-8-sig")))
    elig=list(csv.DictReader(open(ELIG, encoding="utf-8")))
    if len(uni)!=1633 or len(elig)!=1633: raise SystemExit("rowcount")
    ident=[(r["WS_ID"], r["ISIN"], r["Primary_MIC"], r["Primary_Ticker"]) for r in uni]
    strict={r["WS_ID"] for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE"}
    if len(strict)!=759: raise SystemExit("strict")
    rows=[]
    for region,index,mics,kind in SEGS:
        allow=set(mics.split("|"))
        mem=[r for r in uni if r["Primary_MIC"] in allow]
        st=[r for r in mem if r["WS_ID"] in strict]
        rows.append((region,index,len(mem),len(st),kind))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"coverage_segments_p5_0.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=["Region","Index","Membership_1633","Strict_759","Gap_Type"]); w.writeheader()
        for r in rows: w.writerow({"Region":r[0],"Index":r[1],"Membership_1633":r[2],"Strict_759":r[3],"Gap_Type":r[4]})
    us_m=sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})
    ca_m=sum(1 for r in uni if r["Primary_MIC"]=="XTSE")
    ca_s=sum(1 for r in uni if r["Primary_MIC"]=="XTSE" and r["WS_ID"] in strict)
    unk=sum(1 for r in uni if r["Instrument_Type"]=="UNKNOWN")
    md="# P5.0 Strategic Architecture & Coverage Gate\n\nHEAD `16816a9`. READ-ONLY. Strict=759. Frozen=0. Universe_Write=NO.\n\n## 1. Executive Decision\n\nEMPFOHLEN: B — 1633 bleibt Workbench / Research Stage\nGOVERNANCE: C als Layer-Modell (NICHT Tier-1 = 759)\nVERWORFEN: A (1633 = dauerhafter Master); C als 759-U3K-light\nNAECHSTER BAU: keiner ohne neuen Manager-Auftrag\nERSTE SCHEIBE: US-Primary XNYS/XNAS (nur nach extra Auftrag)\n\nBegruendung: P4 zeigt 759 = indexgebundenes Partial-Subset (77% Asia, 0 US). \~3000 liquide Primary Listings bleiben nur mit B erreichbar. A gaebe das U3K-Ziel auf. 759 darf kein Membership-Freeze werden.\n\n## 2. P4-Ausgang\n1633 Membership. 759 Strict. Asia 585 / EU 137 / BVMF 37 / US 0. COMMON 585 = UNMAPPED 585. Share_Class leer 291. Konzentration = Coverage, kein QA-Fehler.\n\n## 3. Option A VERWORFEN\nUS bleibt 0, Ziel \~3000 still tot.\n\n## 4. Option B EMPFOHLEN\n1633 = Stage. Expansion nur Segment -> Policy -> Evidence -> Mapping -> History -> QA -> Eligibility -> Manager-Gate. Kein 3663-Dump.\n\n## 5. Option C nur Layer zu B\nMembership / Eligibility / Scan / Execution. Verboten: Tier 1 = 759 = Mini-U3K.\n\n## 6. Empfehlung\nB + C-Layer. A verworfen.\n\n## 7. U3K-Definition unapplied\nCa. 3000 liquide kanonische Primary-Scan-Listings. Nicht 3000 Share-Classes, nicht 3000 Emittenten, nicht 3000 Membership-Zeilen. Scan = eine Ordinary/Common je Emittent x Markt. Preferred nie Scan-Default. Dual: kein MIC-Merge.\n\n## 8. Layer\nMembership != Eligibility != Scan != Execution. 759 != Frozen Universe.\n\n## 9. Coverage\n"+tbl(["Region","Index","Membership","Strict","Typ"], rows)+"\n\nUSA/AU/KR = Expansion. CA/HK/EU/BR = Conversion (Membership da). CA 217/0 Strict ist kein US-Ersatz.\n\n## 10. Erste Expansion falls beschlossen\nUS-Primary XNYS/XNAS. Membership+Strict = %s. Kein Download in P5.0.\n\n## 11. Expansionsregel\n1 Segment 2 Policy 3 Evidence 4 Mapping 5 History 6 QA 7 Liquidity 8 Eligibility Dry-Run 9 Manager-Gate. Kein stiller Master-Write.\n\n## 12. Verworfen\nA; 759-U3K-light; A1 jetzt; P6-Welle; 3663; Freeze; US-Download hier.\n\n## 13. Offen unbearbeitet\n15 REVIEW. 14 Pref-only. 7 Dual. UNKNOWN %s. CA Strict %s/%s.\n\n## 14. Manager Gate\nB annehmen? Dann GENAU eines: A1 ODER Canonical ODER US-Segment. P5.0 startet keinen Datenbau.\n"%(us_m, unk, ca_s, ca_m)
    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text(md, encoding="utf-8")
    if [(r["WS_ID"], r["ISIN"], r["Primary_MIC"], r["Primary_Ticker"]) for r in uni]!=ident or sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    summary={"stage":"P5_0_ARCHITECTURE_COVERAGE_GATE","version":"v0.55-P5.0","run_mode":"READ_ONLY_ARCHITECTURE","recommended_architecture":"B_1633_WORKBENCH","governance":"C_LAYERS_NOT_TIER1_U3K","rejected":["A_1633_MASTER","C_AS_759_U3K_LIGHT"],"u3k_working_definition":"approx_3000_liquid_canonical_primary_scan_listings","first_expansion_if_approved":"US_PRIMARY_XNYS_XNAS","strict":759,"membership":1633,"us_primary_membership":us_m,"canada_membership":ca_m,"canada_strict":ca_s,"unknown_instrument_type":unk,"universe_write":False,"eligibility_promoted":False,"u3k_frozen_members":0,"productive":False,"next_data_build":"NONE_WITHOUT_MANAGER_ORDER","as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_p5_0.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
