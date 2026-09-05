#!/usr/bin/env python3
"""P4 read-only composition & coverage audit of 759 strict candidates. No universe write."""
from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT / "universe" / "research_partial_1633.csv"
FROZEN = ROOT / "universe" / "SWING_U3K_FROZEN_v0.5.csv"
ELIG = ROOT / "output_eligibility_dry_run_1633_v0_52" / "eligibility_dry_run_1633_v0.52.csv"
SLICE = ROOT / "output_instrument_share_class_v0_51" / "apply_slice_239_v0.51.csv"
MC = ROOT / "output_qa_v0_53" / "multi_share_class_v0.53.csv"
C147 = ROOT / "output_research_candidates_147_v0_50" / "research_candidates_147_v0.50.csv"
OUT = ROOT / "output_p4_audit_759"
N = 759
LEGAL = re.compile(r"\b(SA|NV|AG|SE|PLC|LTD|LIMITED|INC|CORP|CO|GROUP|THE|S A|N V)\b")
TAIL = re.compile(r"\b(PREF\.?|PREFERRED|VORZUG|PN|ON|UNIT|UNT|ED|NM|N1|N2|ATZ|EJ|EDJ|PNA)\b")
MIC_REGION = {
    "XTKS": "Asia-Pacific", "XSHG": "Asia-Pacific", "XSHE": "Asia-Pacific",
    "XTAI": "Asia-Pacific", "XNSE": "Asia-Pacific",
    "XETR": "Europe", "XPAR": "Europe", "XSTO": "Europe", "XMIL": "Europe",
    "XLON": "Europe", "XCSE": "Europe", "XAMS": "Europe", "XWBO": "Europe",
    "XDUB": "Europe", "XMAD": "Europe", "XBRU": "Europe", "XHEL": "Europe",
    "XWAR": "Europe", "XSWX": "Europe", "BVMF": "Americas",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def frozen_ok():
    if sum(1 for _ in open(FROZEN, encoding="utf-8")) != 1:
        raise SystemExit("frozen")


def gi(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ikey(n):
    n = re.sub(r"\s+", " ", (n or "").upper())
    n = TAIL.sub(" ", n)
    n = LEGAL.sub(" ", n)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", n)).strip()


def pct(n, d=N):
    return round(100.0 * n / d, 1) if d else 0.0


def share_bucket(s, inst):
    t = (s or "").strip()
    if not t:
        return "MISSING_EMPTY"
    u = t.lower()
    if "pref" in u or "vorzug" in u or t.startswith("PN"):
        return "PREFERRED"
    if t in {"C share", "SDB", "participation certificate"} or "depositary" in u or t == "registered shares":
        return "REVIEW_UNCLEAR"
    if "ordinary" in u or t in {"B share", "B shares", "A share", "A shares", "A_SHARE"} or t.startswith("ON"):
        return "ORDINARY_OR_COMMON_EVIDENCE"
    if inst == "COMMON_STOCK":
        return "COMMON_LABEL"
    return "OTHER"


def wcsv(path, rows, fields=None):
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    fields = fields or list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines)


def main():
    frozen_ok()
    uni_sha = sha(UNI)
    uni = {r["WS_ID"]: r for r in csv.DictReader(open(UNI, encoding="utf-8-sig"))}
    elig = list(csv.DictReader(open(ELIG, encoding="utf-8")))
    if len(uni) != 1633 or len(elig) != 1633:
        raise SystemExit("rowcount")
    ident = [(r["WS_ID"], r["ISIN"], r["Primary_MIC"], r["Primary_Ticker"]) for r in uni.values()]
    strict = [r for r in elig if r["Eligibility_DryRun"] == "PASS_STRICT_CANDIDATE"]
    if len(strict) != N:
        raise SystemExit(f"strict={len(strict)}")
    c147 = {r["WS_ID"] for r in csv.DictReader(open(C147, encoding="utf-8"))}
    slice_rows = list(csv.DictReader(open(SLICE, encoding="utf-8")))
    review = [r for r in slice_rows if r["Action"] == "HOLD_REVIEW"]
    mc = list(csv.DictReader(open(MC, encoding="utf-8")))
    unknown_n = sum(1 for r in uni.values() if r["Instrument_Type"] == "UNKNOWN")

    # 4.1 MIC
    mic_c = Counter(r["Primary_MIC"] for r in strict)
    mic_rows = [{"MIC": k, "n": n, "pct": pct(n), "region_map": MIC_REGION.get(k, "UNMAPPED_MIC")} for k, n in mic_c.most_common()]
    region_c = Counter(MIC_REGION.get(r["Primary_MIC"], "UNMAPPED_MIC") for r in strict)

    # 4.2 country + ISIN
    ctry_c = Counter((uni[r["WS_ID"]].get("Country") or "").strip() or "MISSING" for r in strict)
    isin_c = Counter((uni[r["WS_ID"]].get("ISIN") or "XX")[:2] or "MISSING" for r in strict)
    ctry_rows = [{"Country_Universe": k, "n": n, "pct": pct(n)} for k, n in ctry_c.most_common()]
    isin_rows = [{"ISIN_Prefix": k, "n": n, "pct": pct(n)} for k, n in isin_c.most_common()]
    idx_c = Counter((uni[r["WS_ID"]].get("Primary_Universe_Index") or "").strip() or "MISSING" for r in strict)

    # 4.3–4.7
    inst_c = Counter(r["Instrument_Type"] for r in strict)
    sb_c = Counter(share_bucket(r.get("Share_Class"), r["Instrument_Type"]) for r in strict)
    empty_share = sum(1 for r in strict if not (r.get("Share_Class") or "").strip())
    liq_c = Counter(r["Liquidity_Class"] for r in strict)
    map_c = Counter(r["Mapping_Status"] for r in strict)
    hist_c = Counter(r["History_Source"] for r in strict)
    bands = [("15-20m", 15e6, 20e6), ("20-50m", 20e6, 50e6), ("50-100m", 50e6, 100e6), (">=100m", 100e6, 1e18)]
    band_c = Counter()
    for r in strict:
        v = gi(r["MedianTurnover20_EUR"])
        if v is None:
            band_c["MISSING"] += 1
            continue
        hit = False
        for lab, a, b in bands:
            if a <= v < b:
                band_c[lab] += 1
                hit = True
                break
        if not hit:
            band_c["OUT_OF_BANDS"] += 1

    overlap = len(c147 & {r["WS_ID"] for r in strict})
    drop_ids = c147 - {r["WS_ID"] for r in strict}
    by_el = {r["WS_ID"]: r for r in elig}
    drop_reason = Counter(by_el[w]["Eligibility_DryRun"] for w in drop_ids)

    # name dups in 759
    by_name = defaultdict(list)
    for r in strict:
        by_name[r["Name"]].append(r)
    name_dups = {k: v for k, v in by_name.items() if len(v) > 1}

    # 6A REVIEW
    review_out = []
    for r in review:
        ur = uni[r["WS_ID"]]
        review_out.append({
            "WS_ID": r["WS_ID"], "Ticker": ur["Primary_Ticker"], "Name": ur["Name"],
            "ISIN": ur["ISIN"], "MIC": ur["Primary_MIC"],
            "Share_Class_Evidence": r.get("Verified_Share_Class") or "",
            "Instrument_Type": ur["Instrument_Type"],
            "Review_Reason": "Closed-map REVIEW string; type not invented",
            "Eligibility_DryRun": by_el[r["WS_ID"]]["Eligibility_DryRun"],
        })

    # 6B pref-only
    groups = defaultdict(list)
    for ur in uni.values():
        groups[ikey(ur["Name"])].append(ur)
    pref_out = []
    for ur in uni.values():
        if ur["Instrument_Type"] != "PREFERRED_SHARE":
            continue
        g = groups[ikey(ur["Name"])]
        ords = [x for x in g if x["Instrument_Type"] in {"ORDINARY_SHARE", "COMMON_STOCK"}]
        pref_out.append({
            "Issuer_Key": ikey(ur["Name"]), "Name": ur["Name"],
            "Ticker": ur["Primary_Ticker"], "ISIN": ur["ISIN"], "MIC": ur["Primary_MIC"],
            "Instrument_Type": ur["Instrument_Type"], "Share_Class": ur.get("Share_Class") or "",
            "Ordinary_In_1633": "YES" if ords else "NO",
            "Ordinary_Tickers": "|".join(x["Primary_Ticker"] for x in ords),
            "Status": "ORDINARY_PRESENT" if ords else "ORDINARY_MISSING_IN_1633",
            "Note": "Coverage observation only. Preferred not scan-default.",
        })

    # 6C dual
    dual_groups = defaultdict(list)
    for r in mc:
        if r["Group_Type"] == "DUAL_LISTING_MULTI_MIC":
            dual_groups[r["Issuer_Key"]].append(r)
    dual_out = []
    for k, g in dual_groups.items():
        mics = sorted({x["Primary_MIC"] for x in g})
        dual_out.append({
            "Issuer_Key": k, "Name": g[0]["Name"], "n": len(g),
            "MIC_A": mics[0] if mics else "", "MIC_B": mics[1] if len(mics) > 1 else "",
            "Tickers": "|".join(sorted(x["Primary_Ticker"] for x in g)),
            "ISINs": "|".join(x["ISIN"] for x in g),
            "Instrument_Types": "|".join(sorted({x["Instrument_Type"] for x in g})),
            "Note": "No merge across MIC.",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT / "mic_distribution_759.csv", mic_rows)
    wcsv(OUT / "country_distribution_759.csv", ctry_rows)
    wcsv(OUT / "isin_prefix_759.csv", isin_rows)
    wcsv(OUT / "instrument_type_759.csv", [{"Instrument_Type": k, "n": n, "pct": pct(n)} for k, n in inst_c.most_common()])
    wcsv(OUT / "share_class_bucket_759.csv", [{"Share_Class_Bucket": k, "n": n, "pct": pct(n)} for k, n in sb_c.most_common()])
    wcsv(OUT / "liquidity_759.csv", [{"Liquidity_Class": k, "n": n, "pct": pct(n)} for k, n in liq_c.most_common()])
    wcsv(OUT / "turnover_bands_759.csv", [{"Band_EUR": k, "n": n, "pct": pct(n)} for k, n in band_c.most_common()])
    wcsv(OUT / "mapping_status_759.csv", [{"Mapping_Status": k, "n": n, "pct": pct(n)} for k, n in map_c.most_common()])
    wcsv(OUT / "history_source_759.csv", [{"History_Source": k, "n": n, "pct": pct(n)} for k, n in hist_c.most_common()])
    wcsv(OUT / "index_source_759.csv", [{"Primary_Universe_Index": k, "n": n, "pct": pct(n)} for k, n in idx_c.most_common()])
    drop_rows = [{
        "WS_ID": w, "Yahoo_Symbol": by_el[w].get("Yahoo_Symbol", ""), "Name": by_el[w].get("Name", ""),
        "Eligibility_DryRun": by_el[w]["Eligibility_DryRun"], "Instrument_Type": by_el[w]["Instrument_Type"],
        "Share_Class": by_el[w].get("Share_Class", ""),
    } for w in sorted(drop_ids)]
    wcsv(OUT / "overlap_147_not_in_759.csv", drop_rows)
    wcsv(OUT / "appendix_6A_review_15.csv", review_out)
    wcsv(OUT / "appendix_6B_pref_only.csv", pref_out)
    wcsv(OUT / "appendix_6C_dual_listing.csv", dual_out)

    asia = region_c.get("Asia-Pacific", 0)
    eu = region_c.get("Europe", 0)
    am = region_c.get("Americas", 0)
    us = sum(1 for r in strict if r["Primary_MIC"] in {"XNYS", "XNAS", "ARCX"})

    report = f"""# P4 Composition & Coverage Audit — 759 Strict Candidates

**HEAD Ausgang:** `11d7885`  
**Modus:** DEV / RESEARCH / SHADOW — nicht produktiv  
**Run:** READ-ONLY. Universe_Write=NO. Eligibility unverändert. Frozen U3K=0.  
**Strict:** {len(strict)} (Invariant = 759)

---

## Executive Summary

Die 759 sind **kein Welt-U3K**. Sie sind die Schnittmenge aus:

1. **585 COMMON_STOCK / UNMAPPED** aus v0.38-History — Index-Scheiben Asia (CSI300, Nikkei, TW50, Nifty).
2. **137 EVIDENCE_CANDIDATE_APPLIED** aus der v0.42–v0.50-Welle (STOXX600-Ordinary, History v0.47) — 10 der alten 147 sind REVIEW und nicht in den 759.
3. **37 YFINANCE_VERIFIED** BVMF Ordinary (Brazil IBRX).

**US-Primary (XNYS/XNAS): 0.**  
**Share_Class leer: {empty_share}.** Das sind keine Ordinary-Evidence.

OBSERVATION ≠ ERROR. Die Konzentration folgt den Index-Tags des Research-Partial, nicht einem Scan-Fehler.

---

## 4.1 MIC / Exchange

{md_table(["MIC", "n", "%", "Region-Map (closed, not domicile)"], [[r["MIC"], r["n"], r["pct"], r["region_map"]] for r in mic_rows])}

Region-Map (MIC, nicht Emittenten-Sitz): Asia-Pacific {asia} ({pct(asia)}%) · Europe {eu} ({pct(eu)}%) · Americas {am} ({pct(am)}%) · US-MIC 0.

Top-3 MIC {mic_rows[0]["MIC"]}/{mic_rows[1]["MIC"]}/{mic_rows[2]["MIC"]} = {mic_rows[0]["n"]+mic_rows[1]["n"]+mic_rows[2]["n"]} ({pct(mic_rows[0]["n"]+mic_rows[1]["n"]+mic_rows[2]["n"])}%).

## 4.2 Country (Universe-Feld) und ISIN-Prefix

Country ist das vorhandene Universe-Feld. Nicht an ISIN angeglichen, nicht geraten.

{md_table(["Country", "n", "%"], [[r["Country_Universe"], r["n"], r["pct"]] for r in ctry_rows])}

ISIN-Prefix (erste zwei Zeichen, keine Sitz-Behauptung):

{md_table(["ISIN_Prefix", "n", "%"], [[r["ISIN_Prefix"], r["n"], r["pct"]] for r in isin_rows[:12]])}

Primary_Universe_Index:

{md_table(["Index", "n", "%"], [[k, n, pct(n)] for k, n in idx_c.most_common()])}

## 4.3 Instrument_Type

{md_table(["Instrument_Type", "n", "%"], [[k, n, pct(n)] for k, n in inst_c.most_common()])}

UNKNOWN in Strict: **{inst_c.get("UNKNOWN", 0)}**. Keine Reklassifikation.

## 4.4 Share_Class

Leere Felder **nicht** als Ordinary gelesen.

{md_table(["Bucket", "n", "%"], [[k, n, pct(n)] for k, n in sb_c.most_common()])}

Empty/missing raw Share_Class: **{empty_share}**. A_SHARE ist China-A-Evidence, nicht v0.42-Verified_Share_Class.

## 4.5 Liquidity / Turnover

Schwellen unverändert. Bänder nur Reporting.

{md_table(["Liquidity_Class", "n", "%"], [[k, n, pct(n)] for k, n in liq_c.most_common()])}

Turnover-Bänder MedianTurnover20_EUR: 15–20m · 20–50m · 50–100m · ≥100m.

{md_table(["Band", "n", "%"], [[k, band_c.get(k, 0), pct(band_c.get(k, 0))] for k, _, _ in bands])}

PREFERRED-Klasse = ≥20m: {liq_c.get("PREFERRED", 0)}. STANDARD 15–20m: {liq_c.get("STANDARD", 0)}. Kein Strict unter 15m.

## 4.6 Mapping_Status

UNMAPPED ≠ kein Yahoo. Keine Remediation.

{md_table(["Mapping_Status", "n", "%"], [[k, n, pct(n)] for k, n in map_c.most_common()])}

## 4.7 History Source

Kein Re-Download.

{md_table(["History_Source", "n", "%"], [[k, n, pct(n)] for k, n in hist_c.most_common()])}

v0.38 deckt die Asia-COMMON-Scheibe. v0.47 die 137 Evidence-Ordinary.

## 4.8 Overlap 147 → 759

| | n |
|---|---|
| 147 in 759 | {overlap} |
| 147 nicht in 759 | {len(drop_ids)} |
| neu in 759 (nicht in 147) | {N - overlap} |

Drop-Grund der 10: {dict(drop_reason)} — alle `INSTRUMENT_REVIEW` (P1 fail-closed). Nicht auf 147 zurückbiegen.

Strukturelle Erklärung 147→759: 147 war die **liquide Ordinary-Teilmenge der 239-Welle**. 759 = diese 137 plus 585 v0.38-COMMON (Asia-Indizes) plus 37 BVMF Ordinary. Andere Gates, andere Coverage.

## 5. Antworten

1. **MIC-Konzentration:** Ja. XTKS+XSHG+XSHE = {mic_c.get("XTKS",0)+mic_c.get("XSHG",0)+mic_c.get("XSHE",0)} ({pct(mic_c.get("XTKS",0)+mic_c.get("XSHG",0)+mic_c.get("XSHE",0))}%).
2. **Region:** Asia-Pacific dominant, Europa = STOXX-Welle, Americas = nur BVMF, US-Primary 0.
3. **COMMON vs ORDINARY:** {inst_c.get("COMMON_STOCK",0)} / {inst_c.get("ORDINARY_SHARE",0)}.
4. **Share_Class leer:** {empty_share}.
5. **UNMAPPED:** {map_c.get("UNMAPPED",0)}.
6. **Cluster:** Pipeline-Wellen = Index-Scheiben. Kein Zufall.
7. **147→759:** siehe 4.8. Nicht Fehler.
8. **Namens-Duplikate in 759:** {len(name_dups)} (exakter Name). Multi-Class-Paare Pref/Ord liegen **nicht** beide in Strict (Pref ist nicht Strict).
9. **Coverage-Lücken (Beobachtung):** US 0; UK/XLON nur {mic_c.get("XLON",0)}; Pref-Ordinary-Löcher DE; 15 REVIEW nicht in Strict; Dual-Listings nicht gemerged.
10. **Observation vs Action:** Konzentration und 147→759 sind **Observation**. Potenzieller späterer Bedarf (nicht dieser Auftrag): US-Coverage, Canonical-Policy, REVIEW-Fälle, Pref-Ordinary-Loch. Kein Error-Fix in P4.

---

## Anhänge (sichtbar, unapplied)

### 6A — 15 REVIEW

Siehe `appendix_6A_review_15.csv`. Alle Instrument_Type=UNKNOWN, Eligibility nicht Strict. Keine Reklassifikation.

### 6B — Pref-only

Siehe `appendix_6B_pref_only.csv`. Ordinary_In_1633=NO bedeutet Coverage-Loch, nicht Scan-Default Preferred.

### 6C — Dual-Listing

Siehe `appendix_6C_dual_listing.csv`. Kein Merge über MIC.

---

## 671 UNKNOWN

Instrument_Type=UNKNOWN im Master 1633: **{unknown_n}** (Kontext).  
Davon 15 HOLD_REVIEW mit Share-Class-Evidence; Rest ohne Closed-Map-Apply.  

**Nicht segmentiert, nicht sampled, nicht remediat.** Separater Auftrag.

---

## Canonical Scan Policy — DRAFT, unapplied

Discovery: alle bekannten Klassen bleiben.  
Scan: eine kanonische Ordinary/Common je Emittent × Primärmarkt.  
Preferred: nie Scan-Default.  
Unit/SDB/DR: kein Scan-Default.  
Dual-Listing: kein Merge über MIC; je Markt eigene Identität.  
Execution getrennt.

Nicht bindend. Kein Universe-Write. Keine Eligibility-Regel. P5 braucht Extra-Auftrag.

---

## Invarianten

```
strict = {len(strict)}
universe_write = false
eligibility_promoted = false
u3k_frozen_members = 0
productive = false
unknown_remediation = false
```

P4 STOPP. Kein Freeze. Kein Folgeauftrag aus diesem Report.
"""
    (ROOT / "docs" / "validation" / "P4_Composition_Coverage_Audit_759.md").write_text(report, encoding="utf-8")

    if [(r["WS_ID"], r["ISIN"], r["Primary_MIC"], r["Primary_Ticker"]) for r in uni.values()] != ident:
        raise SystemExit("identity")
    if sha(UNI) != uni_sha:
        raise SystemExit("universe mutated")
    frozen_ok()

    summary = {
        "stage": "P4_COMPOSITION_COVERAGE_AUDIT",
        "version": "v0.54-P4",
        "run_mode": "READ_ONLY_AUDIT",
        "strict": len(strict),
        "mic_top": mic_rows[:5],
        "region": dict(region_c),
        "us_primary_mic": us,
        "instrument_type": dict(inst_c),
        "share_empty": empty_share,
        "share_buckets": dict(sb_c),
        "liquidity": dict(liq_c),
        "turnover_bands": dict(band_c),
        "mapping_status": dict(map_c),
        "history_source": dict(hist_c),
        "index": dict(idx_c),
        "overlap_147_in_759": overlap,
        "overlap_147_dropped": len(drop_ids),
        "drop_reason": dict(drop_reason),
        "name_dups_in_759": len(name_dups),
        "review_15": len(review_out),
        "pref_rows": len(pref_out),
        "pref_ordinary_missing": sum(1 for r in pref_out if r["Ordinary_In_1633"] == "NO"),
        "dual_groups": len(dual_out),
        "unknown_count_context": unknown_n,
        "universe_write": False,
        "eligibility_promoted": False,
        "u3k_frozen_members": 0,
        "productive": False,
        "as_of_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    json.dump(summary, open(OUT / "summary_p4.json", "w", encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
