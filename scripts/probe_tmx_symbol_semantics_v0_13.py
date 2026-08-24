#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
import pandas as pd
import requests

SCHEMA = "WELT_SWING_TMX_SYMBOL_SEMANTICS_PROBE_V0_13"
P0_RUN = False
PRODUCTIVE_TRADING_AUTHORITY = False
ALPHA_VANTAGE_ALLOWED = False
PRICE_DOWNLOADS_PERFORMED = False
FX_DOWNLOADS_PERFORMED = False
WEB_CALLS_PER_SECURITY = False
CANONICAL_MASTER_MUTATED = False
DECISIONS_CHANGED = 0

def now_utc(): return datetime.now(timezone.utc).isoformat()
def txt(v: Any) -> str:
    if v is None: return ""
    try:
        if pd.isna(v): return ""
    except Exception: pass
    return str(v).strip()
def load_json(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def sha256_bytes(data: bytes): return hashlib.sha256(data).hexdigest()
def compact_error(exc: Exception): return f"{type(exc).__name__}: {exc}"[:900]
def norm_tmx_symbol(v: Any): return txt(v).upper().replace(" ", "")

def suffix_pattern(symbol: str) -> str:
    s = norm_tmx_symbol(symbol)
    if "." not in s: return "NO_DOT_SUFFIX"
    suffix = s.split(".", 1)[1]
    if suffix == "UN": return "DOT_UN"
    if suffix.startswith("PR"): return "DOT_PR"
    if suffix in {"A","B","C","D","E","F","X"}: return "DOT_CLASS_LIKE"
    if suffix in {"SV","NV","MV","LV","RV"}: return "DOT_VOTING_RIGHTS"
    if suffix.startswith("WT"): return "DOT_WARRANT"
    if suffix.startswith("RT"): return "DOT_RIGHT"
    if suffix.startswith("DB"): return "DOT_DEBENTURE"
    return "DOT_OTHER"

def extract_links(html: str, base_url: str):
    out, seen = [], set()
    pat = re.compile(r'<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I|re.S)
    for href, label_html in pat.findall(html):
        href = unescape(href).strip()
        label = re.sub(r"<[^>]+>", " ", label_html)
        label = re.sub(r"\s+", " ", unescape(label)).strip()
        url = urljoin(base_url, href)
        key=(url,label)
        if key not in seen:
            seen.add(key); out.append({"URL":url,"Label":label})
    return out

def select_symbol_download(links):
    candidates=[]
    for row in links:
        u,l=row["URL"],row["Label"].lower()
        score=(4 if ".txt" in u.lower() else 0)+(3 if "full list" in l else 0)+(2 if "symbol" in l else 0)+(1 if "download" in l else 0)
        if score: candidates.append((score,u))
    candidates.sort(key=lambda x:(-x[0],x[1]))
    return candidates[0][1] if candidates else ""

def token_present(raw_text: str, symbol: str):
    s=norm_tmx_symbol(symbol)
    return bool(s and re.search(rf"(?<![A-Z0-9.]){re.escape(s)}(?![A-Z0-9.])", raw_text.upper()))

def self_test():
    assert suffix_pattern("AD.UN")=="DOT_UN"
    assert suffix_pattern("POW.PR.A")=="DOT_PR"
    assert suffix_pattern("CTC.A")=="DOT_CLASS_LIKE"
    assert suffix_pattern("AAP.SV")=="DOT_VOTING_RIGHTS"
    assert suffix_pattern("ABX")=="NO_DOT_SUFFIX"
    html = '<a href="/files/list.txt">Download the full list of symbols (TXT)</a><a href="/other">Other</a>'
    links=extract_links(html,"https://www.tsx.com/example")
    assert select_symbol_download(links)=="https://www.tsx.com/files/list.txt"
    raw="ABX\tBarrick\nAD.UN\tExample Trust\n"
    assert token_present(raw,"ABX") and token_present(raw,"AD.UN") and not token_present(raw,"A")
    print("TMX_SYMBOL_SEMANTICS_PROBE_V0_13_SELF_TEST_PASS")

def run(cfg_path: Path):
    cfg=load_json(cfg_path); out=Path(cfg["output_dir"]); out.mkdir(parents=True, exist_ok=True)
    s12=load_json(Path(cfg["source_summary_v0_12"]))
    if s12.get("schema")!="WELT_SWING_INSTRUMENT_RESOLUTION_JSE_V0_12": raise SystemExit("Wrong v0.12 source schema")
    if s12.get("run_status")!="INSTRUMENT_RESOLUTION_JSE_V0_12_COMPLETE_WITH_REMAINING_REVIEW": raise SystemExit("Unexpected v0.12 run status")
    if int(s12.get("remaining_manual_rows_v0_12",-1))!=int(cfg["expected_source_manual_rows"]): raise SystemExit("Unexpected manual count")
    if int(s12.get("strict_candidates_v0_12",-1))!=int(cfg["expected_source_strict_candidates"]): raise SystemExit("Unexpected strict count")
    if s12.get("p0_run") is not False or s12.get("alpha_vantage_allowed") is not False: raise SystemExit("Governance gate failed")
    manual=pd.read_csv(cfg["source_manual_queue_v0_12"],keep_default_na=False,dtype=str)
    if len(manual)!=int(cfg["expected_source_manual_rows"]): raise SystemExit("Manual queue changed")
    ca=manual.loc[manual["Primary_Universe_Index"].eq("CA_TSX")].copy()
    if len(ca)!=int(cfg["expected_ca_target_rows"]): raise SystemExit("Unexpected CA target count")
    ca["TMX_Target_Symbol"]=ca["Primary_Ticker"].map(norm_tmx_symbol)
    if ca["TMX_Target_Symbol"].eq("").any() or ca["TMX_Target_Symbol"].duplicated().any(): raise SystemExit("Invalid CA symbols")
    ca["TMX_Suffix_Pattern"]=ca["TMX_Target_Symbol"].map(suffix_pattern)
    ca.to_csv(out/"ca_target_symbol_patterns_v0.13.csv",index=False)
    ca.groupby("TMX_Suffix_Pattern").size().reset_index(name="Rows").to_csv(out/"ca_target_suffix_counts_v0.13.csv",index=False)
    manual.to_csv(out/"instrument_manual_review_queue_v0.13.csv",index=False)

    session=requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 WeltSwingLongDEV/0.13","Accept-Language":"en-US,en;q=0.8"})
    external_requests=0; max_requests=int(cfg["max_external_reference_requests"]); status_rows=[]
    moc=cfg["tmx_sources"]["moc_eligible"]; symbol_text=""; download_url=""

    try:
        external_requests+=1
        r=session.get(moc["url"],timeout=int(cfg["request_timeout_seconds"]))
        row={"Source":"TMX_MOC_PAGE","URL":moc["url"],"HTTP_Status":r.status_code,"Content_Type":r.headers.get("Content-Type",""),
             "Bytes":len(r.content),"SHA256":sha256_bytes(r.content) if r.content else "","Status":"HTTP_OK" if r.ok else "HTTP_ERROR","Error":""}
        r.raise_for_status()
        links=extract_links(r.text,moc["url"]); pd.DataFrame(links).to_csv(out/"tmx_moc_page_links_v0.13.csv",index=False)
        download_url=select_symbol_download(links); row["Discovered_Download_URL"]=download_url
        if not download_url: row["Status"]="PAGE_OK_NO_SYMBOL_DOWNLOAD_DISCOVERED"
        status_rows.append(row)
    except Exception as exc:
        status_rows.append({"Source":"TMX_MOC_PAGE","URL":moc["url"],"HTTP_Status":"","Content_Type":"","Bytes":0,"SHA256":"","Status":"REQUEST_ERROR","Error":compact_error(exc),"Discovered_Download_URL":""})

    if download_url and external_requests<max_requests:
        try:
            external_requests+=1
            r=session.get(download_url,timeout=int(cfg["request_timeout_seconds"])); r.raise_for_status()
            enc=""
            for e in ("utf-8-sig","utf-8","cp1252","latin-1"):
                try: symbol_text=r.content.decode(e); enc=e; break
                except Exception: pass
            if not symbol_text: raise ValueError("Unable to decode TMX symbol download")
            (out/"tmx_symbol_download_sample_v0.13.txt").write_text("\n".join(symbol_text.splitlines()[:100])+"\n",encoding="utf-8")
            status_rows.append({"Source":"TMX_MOC_SYMBOL_DOWNLOAD","URL":download_url,"HTTP_Status":r.status_code,"Content_Type":r.headers.get("Content-Type",""),
                "Bytes":len(r.content),"SHA256":sha256_bytes(r.content),"Status":"HTTP_OK","Error":"","Encoding":enc})
        except Exception as exc:
            status_rows.append({"Source":"TMX_MOC_SYMBOL_DOWNLOAD","URL":download_url,"HTTP_Status":"","Content_Type":"","Bytes":0,"SHA256":"","Status":"REQUEST_ERROR","Error":compact_error(exc)})

    notice=cfg["tmx_sources"]["symbol_suffix_notice"]
    if external_requests<max_requests:
        try:
            external_requests+=1
            r=session.get(notice["url"],timeout=int(cfg["request_timeout_seconds"])); r.raise_for_status()
            clean=re.sub(r"<[^>]+>"," ",r.text); clean=re.sub(r"\s+"," ",unescape(clean)).strip()
            (out/"tmx_symbol_suffix_notice_text_v0.13.txt").write_text(clean[:20000]+"\n",encoding="utf-8")
            status_rows.append({"Source":"TMX_SYMBOL_SUFFIX_NOTICE","URL":notice["url"],"HTTP_Status":r.status_code,"Content_Type":r.headers.get("Content-Type",""),
                "Bytes":len(r.content),"SHA256":sha256_bytes(r.content),"Status":"HTTP_OK","Error":""})
        except Exception as exc:
            status_rows.append({"Source":"TMX_SYMBOL_SUFFIX_NOTICE","URL":notice["url"],"HTTP_Status":"","Content_Type":"","Bytes":0,"SHA256":"","Status":"REQUEST_ERROR","Error":compact_error(exc)})

    if external_requests>max_requests: raise SystemExit("Request budget exceeded")
    pd.DataFrame(status_rows).to_csv(out/"source_status_v0.13.csv",index=False)
    ca["TMX_Current_Symbol_Present"]=ca["TMX_Target_Symbol"].map(lambda s: token_present(symbol_text,s)) if symbol_text else False
    ca[["WS_ID","Name","TMX_Target_Symbol","TMX_Suffix_Pattern","TMX_Current_Symbol_Present"]].to_csv(out/"ca_target_tmx_presence_v0.13.csv",index=False)
    matched=int(ca["TMX_Current_Symbol_Present"].sum())
    summary={"schema":SCHEMA,"generated_utc":now_utc(),
      "run_status":"TMX_SYMBOL_SEMANTICS_PROBE_V0_13_COMPLETE_WITH_CURRENT_SYMBOL_EVIDENCE" if matched>0 else "TMX_SYMBOL_SEMANTICS_PROBE_V0_13_COMPLETE_WITH_LIMITED_EVIDENCE",
      "source_manual_rows_v0_12":len(manual),"ca_target_rows":len(ca),"ca_current_symbol_matches":matched,
      "ca_current_symbol_coverage":matched/len(ca) if len(ca) else 0.0,
      "strict_candidates_v0_12":int(cfg["expected_source_strict_candidates"]),"strict_candidates_v0_13":int(cfg["expected_source_strict_candidates"]),
      "remaining_manual_rows_v0_13":len(manual),"decisions_changed":DECISIONS_CHANGED,
      "external_reference_requests":external_requests,"max_external_reference_requests":max_requests,
      "request_bound_respected":external_requests<=max_requests,"strict_freeze_allowed":False,"p0_run":P0_RUN,
      "productive_trading_authority":PRODUCTIVE_TRADING_AUTHORITY,"alpha_vantage_allowed":ALPHA_VANTAGE_ALLOWED,
      "price_downloads_performed":PRICE_DOWNLOADS_PERFORMED,"fx_downloads_performed":FX_DOWNLOADS_PERFORMED,
      "web_calls_per_security":WEB_CALLS_PER_SECURITY,"canonical_master_mutated":CANONICAL_MASTER_MUTATED,
      "notes":["v0.13 is evidence acquisition only and makes zero instrument decisions.",
               "The 650-row v0.12 review queue is preserved.",
               "Canada target suffix patterns are measured without treating names or suffixes as PASS evidence.",
               "The official TMX MOC page is used only to discover/validate current exchange symbols in bulk.",
               "The official TMX symbol-suffix notice is captured as semantics evidence if accessible.",
               "No per-security request is made.",
               "A later v0.14 classifier is permitted only if combined official evidence deterministically separates common/ordinary shares from units/preferreds/other structures.",
               "P0 remains off and the canonical master is not mutated."]}
    (out/"summary_v0.13.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False)); return summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",default="config/instrument_resolution_tmx_probe_v0.13.json"); ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test: self_test(); return 0
    run(Path(args.config)); return 0

if __name__=="__main__": raise SystemExit(main())
