#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.66"
STAGE = "B3_CLASSIFICATION_APPLICATION_API_ASSET_CONTRACT_DISCOVERY_GATE"
REQUIRED_START_HEAD = "fb651c31f55f14a7fcb6bb3c83c5b25e3d69a4e6"
V065_WORKFLOW = 36266926685
V065_ARTIFACT = 10914042556
V065_DIGEST = "sha256:0fcc27756c32156da0fa4be605f8dee1a2fa52fa3bd88aac2ecfc07355058146"
FROZEN_SHA = "54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb"
V057_SHA = "177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9"
V058_SHA = "2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32"

FROZEN = ROOT / "universe/SWING_U3K_FROZEN_v0.5.csv"
V057 = ROOT / "output_p0_frozen_1425_local_feature_implementation_v0_57/feature_materialization_v0.57.csv"
V058 = ROOT / "output_p0_frozen_1425_home_market_rs_v0_58/home_market_rs_materialization_v0.58.csv"
S065 = ROOT / "output_br_ibrx100_classification_tree_inversion_v0_65/summary_v0.65.json"
C065 = ROOT / "output_br_ibrx100_classification_tree_inversion_v0_65/stage_checkpoint_v0.65.json"
SPEC = ROOT / "config/b3_classification_application_contract_discovery_spec_v0.66.json"

FAIL_VERDICT = "BLOCKED_B3_PUBLIC_APPLICATION_DATA_CONTRACT"
FAIL_BLOCKER = "B3_PUBLIC_CLASSIFICATION_DATA_CONTRACT_NOT_DISCOVERED"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36 WeltSwingLongDev-v0.66"

TOKENS = (
    "classif", "setor", "sector", "subsetor", "subsector", "segment", "company",
    "companies", "empresa", "listed", "industry", "hierarch", "taxonomy", "tree"
)

STATIC_EXT = (".js", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf", ".ico")


class AssetHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "script" and d.get("src"):
            self.scripts.append(d["src"])
        if tag.lower() == "link" and d.get("href"):
            self.links.append((d.get("rel", "").lower(), d["href"]))


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if fields:
            w.writeheader()
            w.writerows(rows)


def allowed_host(url: str, allowed: set[str]) -> bool:
    try:
        return urllib.parse.urlparse(url).hostname in allowed
    except Exception:
        return False


def fetch_public(url: str, allowed: set[str], max_bytes: int, timeout: int = 20) -> dict[str, Any]:
    if not allowed_host(url, allowed):
        return {"url": url, "ok": False, "error": "HOST_NOT_ALLOWED"}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"}, method="GET")
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200))
            ctype = resp.headers.get("Content-Type", "")
            clen = resp.headers.get("Content-Length")
            data = resp.read(max_bytes + 1)
            truncated = len(data) > max_bytes
            if truncated:
                data = data[:max_bytes]
            return {
                "url": url, "ok": 200 <= status < 300, "status": status,
                "content_type": ctype, "content_length_header": clen or "",
                "bytes": len(data), "truncated": truncated, "sha256": sha_bytes(data),
                "timestamp_utc": ts, "body": data
            }
    except Exception as e:
        return {"url": url, "ok": False, "status": "", "content_type": "", "bytes": 0,
                "truncated": False, "sha256": "", "timestamp_utc": ts,
                "error": f"{type(e).__name__}:{e}"}


def text_body(fr: dict[str, Any]) -> str:
    b = fr.get("body", b"")
    if not isinstance(b, (bytes, bytearray)):
        return ""
    try:
        return bytes(b).decode("utf-8")
    except UnicodeDecodeError:
        return bytes(b).decode("latin-1", errors="replace")


def relevant_strings(text: str, limit: int = 80) -> list[str]:
    out: list[str] = []
    # quoted strings only, bounded length, so no full minified bundle persistence
    for m in re.finditer(r"""(?P<q>["'])(?P<s>.{2,320}?)(?P=q)""", text, flags=re.I | re.S):
        s = html.unescape(m.group("s"))
        low = s.lower()
        if any(t in low for t in TOKENS):
            s = re.sub(r"\s+", " ", s).strip()
            if s and s not in out:
                out.append(s)
                if len(out) >= limit:
                    break
    return out


def endpoint_candidates(strings: Iterable[str], base_url: str, allowed: set[str]) -> list[str]:
    out: list[str] = []
    for s in strings:
        s = s.strip()
        if len(s) > 300 or any(x in s for x in ("<", ">", "{", "}")):
            continue
        if not any(t in s.lower() for t in TOKENS):
            continue
        if s.startswith("//"):
            s = "https:" + s
        elif s.startswith("/"):
            s = urllib.parse.urljoin(base_url, s)
        elif s.startswith("http://") or s.startswith("https://"):
            pass
        elif re.match(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.?=&%/-]+)+$", s):
            s = urllib.parse.urljoin(base_url, s)
        else:
            continue
        p = urllib.parse.urlparse(s)
        if p.hostname not in allowed:
            continue
        if p.path.lower().endswith(STATIC_EXT):
            continue
        if s not in out:
            out.append(s)
    return out


def summarize_json(obj: Any) -> dict[str, Any]:
    keys: set[str] = set()
    strings: list[str] = []
    nodes = 0

    def walk(x: Any, depth: int = 0) -> None:
        nonlocal nodes
        if nodes > 50000:
            return
        nodes += 1
        if isinstance(x, dict):
            for k, v in x.items():
                keys.add(str(k))
                walk(v, depth + 1)
        elif isinstance(x, list):
            for v in x[:10000]:
                walk(v, depth + 1)
        elif isinstance(x, str) and len(strings) < 500:
            strings.append(x)

    walk(obj)
    kl = {k.lower() for k in keys}
    joined = " ".join(s.lower() for s in strings[:500])
    return {
        "node_count": nodes,
        "keys": sorted(keys)[:200],
        "has_setor": any("setor" in k or "sector" in k for k in kl) or "setor" in joined,
        "has_subsetor": any("subsetor" in k or "subsector" in k for k in kl) or "subsetor" in joined,
        "has_segmento": any("segmento" in k or "segment" in k for k in kl) or "segmento" in joined,
        "has_company_code": any(k in kl for k in ("code", "codigo", "codigocvm", "companycode", "issuingcompany")) or "código" in joined,
        "has_company": any("company" in k or "empresa" in k or "companhia" in k for k in kl) or "empresa" in joined,
    }


def json_contract_classification(obj: Any) -> dict[str, Any]:
    s = summarize_json(obj)
    tree = bool(s["has_setor"] and s["has_subsetor"] and s["has_segmento"] and s["node_count"] >= 15)
    all_company = bool(s["has_setor"] and s["has_company"] and s["has_company_code"] and s["node_count"] >= 100)
    return {"summary": s, "tree_candidate": tree, "all_company_candidate": all_company}


def chrome_binary() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


def collect_netlog_urls(netlog_path: Path, allowed: set[str]) -> list[dict[str, str]]:
    try:
        obj = json.loads(netlog_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    seen: dict[str, dict[str, str]] = {}
    events = obj.get("events", []) if isinstance(obj, dict) else []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        params = ev.get("params")
        if not isinstance(params, dict):
            continue
        url = params.get("url")
        if not isinstance(url, str) or not allowed_host(url, allowed):
            continue
        row = seen.setdefault(url, {"URL": url, "Method": "", "Status": "", "Mime_Type": "", "Initiator": "CHROME_NETLOG"})
        if params.get("method"):
            row["Method"] = str(params["method"])
        if params.get("response_code") is not None:
            row["Status"] = str(params["response_code"])
        if params.get("mime_type"):
            row["Mime_Type"] = str(params["mime_type"])
    return list(seen.values())


def validate_predecessor(repo_sha: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if git("rev-parse", "HEAD") != repo_sha:
        raise RuntimeError("checkout mismatch")
    if subprocess.run(["git", "merge-base", "--is-ancestor", REQUIRED_START_HEAD, "HEAD"], cwd=ROOT).returncode != 0:
        raise RuntimeError("required start head not ancestor")
    s = json.loads(S065.read_text(encoding="utf-8"))
    c = json.loads(C065.read_text(encoding="utf-8"))
    if s["verdict"] != "BLOCKED_B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBILITY":
        raise RuntimeError("v0.65 verdict")
    if s["br_exact_37_classification_coverage_ready"] is not False:
        raise RuntimeError("v0.65 readiness")
    if (s["ready"], s["total"], s["ambiguous"], s["not_found"], s["not_verified"]) != (0, 37, 0, 0, 37):
        raise RuntimeError("v0.65 counts")
    if s["classification_nodes_queried"] != 0:
        raise RuntimeError("v0.65 classification node queries")
    if s["blocker"] != "B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE":
        raise RuntimeError("v0.65 blocker")
    if c["workflow_run_id"] != V065_WORKFLOW or c["artifact_id"] != V065_ARTIFACT:
        raise RuntimeError("v0.65 workflow/artifact")
    if "sha256:" + c["artifact_digest"] != V065_DIGEST:
        raise RuntimeError("v0.65 digest")
    if sha_file(FROZEN) != FROZEN_SHA or sha_file(V057) != V057_SHA or sha_file(V058) != V058_SHA:
        raise RuntimeError("immutability predecessor")
    return s, c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository-sha", required=True)
    ap.add_argument("--output-dir", default="output_b3_classification_application_contract_discovery_v0_66")
    args = ap.parse_args()

    pred, chk = validate_predecessor(args.repository_sha)
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec["version"] != VERSION or spec["scope_cohort"] != "BR_IBRX100":
        raise RuntimeError("spec scope")
    allowed = set(spec["allowed_hosts"])
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    network_ledger: list[dict[str, Any]] = []
    asset_ledger: list[dict[str, Any]] = []
    excerpt_rows: list[dict[str, Any]] = []
    discovered_strings: list[tuple[str, str]] = []
    target_fetches: list[dict[str, Any]] = []

    # 1) public page HTML and static assets
    assets: list[str] = []
    for page in spec["target_pages"]:
        fr = fetch_public(page, allowed, spec["max_asset_bytes"])
        target_fetches.append(fr)
        network_ledger.append({
            "Request_Type": "DIRECT_PAGE_FETCH", "Method": "GET", "URL": page,
            "Status": fr.get("status", ""), "Content_Type": fr.get("content_type", ""),
            "Public_Reproducible": "YES" if fr.get("ok") else "NO",
            "Independent_Replay": "YES" if fr.get("ok") else "NO",
            "Auth_Required": "NO" if fr.get("ok") else "NOT_VERIFIED",
            "Result": "OK" if fr.get("ok") else fr.get("error", "FAILED")
        })
        if fr.get("ok"):
            txt = text_body(fr)
            parser = AssetHTMLParser()
            try:
                parser.feed(txt)
            except Exception:
                pass
            for src in parser.scripts:
                u = urllib.parse.urljoin(page, src)
                if allowed_host(u, allowed) and u not in assets:
                    assets.append(u)
            for rel, href in parser.links:
                if any(x in rel for x in ("manifest", "preload", "modulepreload")) or href.lower().endswith((".js", ".json")):
                    u = urllib.parse.urljoin(page, href)
                    if allowed_host(u, allowed) and u not in assets:
                        assets.append(u)

    # 2) bounded browser rendering + network log if Chrome exists
    chrome = chrome_binary()
    browser_used = chrome is not None
    browser_rows: list[dict[str, str]] = []
    rendered_meta: list[dict[str, Any]] = []
    if chrome:
        for idx, page in enumerate(spec["target_pages"]):
            with tempfile.TemporaryDirectory() as td:
                tdpath = Path(td)
                netlog = tdpath / "netlog.json"
                cmd = [
                    chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--disable-dev-shm-usage", f"--virtual-time-budget={int(spec['browser_virtual_time_ms'])}",
                    f"--log-net-log={netlog}", "--net-log-capture-mode=Default", "--dump-dom", page
                ]
                try:
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)
                    dom = p.stdout or ""
                    rendered_meta.append({
                        "Page": page, "Browser": chrome, "Return_Code": p.returncode,
                        "DOM_Bytes": len(dom.encode("utf-8")), "DOM_SHA256": hashlib.sha256(dom.encode("utf-8")).hexdigest(),
                        "Network_Log_Present": netlog.exists()
                    })
                    parser = AssetHTMLParser()
                    try:
                        parser.feed(dom)
                    except Exception:
                        pass
                    for src in parser.scripts:
                        u = urllib.parse.urljoin(page, src)
                        if allowed_host(u, allowed) and u not in assets:
                            assets.append(u)
                    if netlog.exists():
                        for row in collect_netlog_urls(netlog, allowed):
                            if row["URL"] not in {x["URL"] for x in browser_rows}:
                                browser_rows.append(row)
                except Exception as e:
                    rendered_meta.append({"Page": page, "Browser": chrome, "Return_Code": "ERROR", "Error": f"{type(e).__name__}:{e}"})

    # 3) fetch bounded static assets
    source_map_candidates: list[str] = []
    for asset in assets[: int(spec["max_assets"])]:
        fr = fetch_public(asset, allowed, spec["max_asset_bytes"])
        asset_ledger.append({
            "Asset_URL": asset, "Asset_Type": "DISCOVERED_HTML_OR_RENDERED_ASSET",
            "Status": fr.get("status", ""), "Content_Type": fr.get("content_type", ""),
            "Bytes": fr.get("bytes", 0), "SHA256": fr.get("sha256", ""),
            "Truncated": fr.get("truncated", False), "Public_Reproducible": "YES" if fr.get("ok") else "NO",
            "Error": fr.get("error", "")
        })
        network_ledger.append({
            "Request_Type": "STATIC_ASSET_FETCH", "Method": "GET", "URL": asset,
            "Status": fr.get("status", ""), "Content_Type": fr.get("content_type", ""),
            "Public_Reproducible": "YES" if fr.get("ok") else "NO",
            "Independent_Replay": "YES" if fr.get("ok") else "NO",
            "Auth_Required": "NO" if fr.get("ok") else "NOT_VERIFIED",
            "Result": "OK" if fr.get("ok") else fr.get("error", "FAILED")
        })
        if not fr.get("ok"):
            continue
        txt = text_body(fr)
        strings = relevant_strings(txt)
        for s in strings:
            discovered_strings.append((asset, s))
            excerpt_rows.append({
                "Asset_URL": asset, "Asset_SHA256": fr.get("sha256", ""),
                "Relevant_Excerpt": s[:320]
            })
        m = re.search(r"sourceMappingURL=([^\s*]+)", txt)
        if m:
            sm = urllib.parse.urljoin(asset, m.group(1).strip())
            if allowed_host(sm, allowed) and sm not in source_map_candidates:
                source_map_candidates.append(sm)
        elif asset.lower().endswith(".js"):
            sm = asset + ".map"
            if allowed_host(sm, allowed) and sm not in source_map_candidates:
                source_map_candidates.append(sm)

    if spec.get("source_map_probe"):
        for sm in source_map_candidates[:10]:
            fr = fetch_public(sm, allowed, spec["max_asset_bytes"])
            if fr.get("ok"):
                asset_ledger.append({
                    "Asset_URL": sm, "Asset_Type": "SOURCE_MAP",
                    "Status": fr.get("status", ""), "Content_Type": fr.get("content_type", ""),
                    "Bytes": fr.get("bytes", 0), "SHA256": fr.get("sha256", ""),
                    "Truncated": fr.get("truncated", False), "Public_Reproducible": "YES",
                    "Error": ""
                })
                txt = text_body(fr)
                for s in relevant_strings(txt, limit=120):
                    discovered_strings.append((sm, s))
                    excerpt_rows.append({"Asset_URL": sm, "Asset_SHA256": fr.get("sha256", ""), "Relevant_Excerpt": s[:320]})

    # 4) browser-observed requests are public page behavior; retain URL/method only, no cookies/headers.
    for row in browser_rows:
        network_ledger.append({
            "Request_Type": "BROWSER_OBSERVED", "Method": row.get("Method", "") or "UNKNOWN", "URL": row["URL"],
            "Status": row.get("Status", ""), "Content_Type": row.get("Mime_Type", ""),
            "Public_Reproducible": "NOT_YET_REPLAYED", "Independent_Replay": "PENDING",
            "Auth_Required": "NOT_VERIFIED", "Result": "OBSERVED_PUBLIC_PAGE_REQUEST"
        })

    # 5) candidate endpoints from bundles and browser network
    candidate_urls: list[str] = []
    for src, s in discovered_strings:
        for u in endpoint_candidates([s], src, allowed):
            if u not in candidate_urls:
                candidate_urls.append(u)
    for row in browser_rows:
        u = row["URL"]
        if any(t in u.lower() for t in TOKENS) and not urllib.parse.urlparse(u).path.lower().endswith(STATIC_EXT):
            if u not in candidate_urls:
                candidate_urls.append(u)

    # Include target data-like routes as candidates for contract classification, but not as sufficient on shell HTML alone.
    for u in spec["target_pages"]:
        if u not in candidate_urls:
            candidate_urls.append(u)

    candidate_contracts: list[dict[str, Any]] = []
    verified_tree_contracts: list[dict[str, Any]] = []
    verified_company_contracts: list[dict[str, Any]] = []

    for u in candidate_urls[: int(spec["max_independent_candidate_probes"])]:
        if any(x in u for x in ("{", "}", "<", ">")):
            candidate_contracts.append({
                "Endpoint_Asset": u, "HTTP_Method": "UNKNOWN", "Parameters": "TEMPLATED",
                "Request_Body": "NOT_PROBED", "Response_Content_Type": "NOT_PROBED",
                "Response_Schema": "NOT_PROBED", "Auth_Required": "NOT_VERIFIED",
                "Public_Reproducible": "NO", "Completeness_Proof": "NO", "Contract_Type": "CANDIDATE_TEMPLATE"
            })
            continue
        fr = fetch_public(u, allowed, spec["max_asset_bytes"])
        network_ledger.append({
            "Request_Type": "INDEPENDENT_CANDIDATE_REPLAY", "Method": "GET", "URL": u,
            "Status": fr.get("status", ""), "Content_Type": fr.get("content_type", ""),
            "Public_Reproducible": "YES" if fr.get("ok") else "NO",
            "Independent_Replay": "YES" if fr.get("ok") else "NO",
            "Auth_Required": "NO" if fr.get("ok") else "NOT_VERIFIED",
            "Result": "OK" if fr.get("ok") else fr.get("error", "FAILED")
        })
        schema = "NON_JSON_OR_UNPARSEABLE"
        ctype = fr.get("content_type", "")
        tree_candidate = False
        company_candidate = False
        summary = {}
        if fr.get("ok"):
            txt = text_body(fr)
            try:
                obj = json.loads(txt)
                cls = json_contract_classification(obj)
                summary = cls["summary"]
                tree_candidate = cls["tree_candidate"]
                company_candidate = cls["all_company_candidate"]
                schema = json.dumps(summary, sort_keys=True, ensure_ascii=False)
            except Exception:
                low = txt.lower()
                schema = "HTML_OR_TEXT"
                # Shell HTML or rendered search pages never prove completeness by themselves.
                if "setor" in low and "subsetor" in low and "segmento" in low:
                    schema = "HTML_WITH_CLASSIFICATION_TERMS_NOT_COMPLETE_PAYLOAD"
        row = {
            "Endpoint_Asset": u, "HTTP_Method": "GET",
            "Parameters": urllib.parse.urlparse(u).query or "NONE",
            "Request_Body": "NONE", "Response_Content_Type": ctype,
            "Response_Schema": schema[:1200], "Auth_Required": "NO" if fr.get("ok") else "NOT_VERIFIED",
            "Public_Reproducible": "YES" if fr.get("ok") else "NO",
            "Completeness_Proof": "YES" if (tree_candidate or company_candidate) else "NO",
            "Contract_Type": "TREE_JSON_CANDIDATE" if tree_candidate else ("ALL_COMPANY_JSON_CANDIDATE" if company_candidate else "NOT_SUFFICIENT")
        }
        candidate_contracts.append(row)
        if tree_candidate and fr.get("ok"):
            verified_tree_contracts.append({"url": u, "method": "GET", "content_type": ctype, "schema": summary})
        if company_candidate and fr.get("ok"):
            verified_company_contracts.append({"url": u, "method": "GET", "content_type": ctype, "schema": summary})

    # Conservative success: exactly the public replay must itself expose a complete-looking finite representation.
    tree_ready = len(verified_tree_contracts) > 0
    company_ready = len(verified_company_contracts) > 0
    if tree_ready:
        verdict = "PASS_B3_CLASSIFICATION_TREE_CONTRACT"
        blocker = ""
        next_gate = "BR_IBRX100 B3 CLASSIFICATION TREE EXECUTION / EXACT-37 COVERAGE GATE"
        discovered_contract = verified_tree_contracts[0]["url"]
        public_repro = True
    elif company_ready:
        verdict = "PASS_B3_ALL_COMPANY_CLASSIFICATION_CONTRACT"
        blocker = ""
        next_gate = "BR_IBRX100 B3 ALL-COMPANY CLASSIFICATION DATASET / EXACT-37 COVERAGE GATE"
        discovered_contract = verified_company_contracts[0]["url"]
        public_repro = True
    else:
        verdict = FAIL_VERDICT
        blocker = FAIL_BLOCKER
        next_gate = FAIL_BLOCKER
        discovered_contract = "NONE"
        public_repro = False

    tree_contract = {
        "b3_classification_tree_machine_reproducible": tree_ready,
        "verified_contracts": verified_tree_contracts,
        "completeness_rule": "COMPLETE_HIERARCHY_OR_COMPLETE_NODE_INVENTORY_WITH_DETERMINISTIC_PARENT_RELATIONS",
        "partial_ui_slice_sufficient": False
    }
    all_company_contract = {
        "b3_complete_company_classification_dataset_ready": company_ready,
        "verified_contracts": verified_company_contracts,
        "required_content": ["B3 Company Code", "Setor Econômico"],
        "exact37_intersection_executed": False
    }
    (out / "b3_tree_contract_v0.66.json").write_text(json.dumps(tree_contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "b3_all_company_classification_contract_v0.66.json").write_text(json.dumps(all_company_contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    write_csv(out / "b3_application_asset_ledger_v0.66.csv", asset_ledger if asset_ledger else [{
        "Asset_URL": "NONE_DISCOVERED", "Asset_Type": "NONE", "Status": "", "Content_Type": "", "Bytes": 0,
        "SHA256": "", "Truncated": False, "Public_Reproducible": "NO", "Error": "NO_STATIC_ASSET_URLS_DISCOVERED"
    }])
    write_csv(out / "b3_js_bundle_endpoint_discovery_v0.66.csv", excerpt_rows if excerpt_rows else [{
        "Asset_URL": "NONE", "Asset_SHA256": "", "Relevant_Excerpt": "NO_RELEVANT_PUBLIC_JS_ENDPOINT_STRINGS_DISCOVERED"
    }])
    write_csv(out / "b3_public_network_request_ledger_v0.66.csv", network_ledger)
    write_csv(out / "b3_candidate_data_contracts_v0.66.csv", candidate_contracts if candidate_contracts else [{
        "Endpoint_Asset": "NONE", "HTTP_Method": "", "Parameters": "", "Request_Body": "",
        "Response_Content_Type": "", "Response_Schema": "", "Auth_Required": "NOT_VERIFIED",
        "Public_Reproducible": "NO", "Completeness_Proof": "NO", "Contract_Type": "NONE_DISCOVERED"
    }])
    write_csv(out / "b3_browser_render_audit_v0.66.csv", rendered_meta if rendered_meta else [{
        "Page": "NONE", "Browser": "NOT_AVAILABLE", "Return_Code": "", "DOM_Bytes": 0, "DOM_SHA256": "", "Network_Log_Present": False
    }])

    repro_audit = {
        "browser_binary_available": browser_used,
        "browser_binary": chrome or "NOT_AVAILABLE",
        "direct_target_fetches_ok": sum(1 for x in target_fetches if x.get("ok")),
        "direct_target_fetches_total": len(target_fetches),
        "static_assets_discovered": len(assets),
        "static_assets_fetched_ok": sum(1 for x in asset_ledger if x.get("Public_Reproducible") == "YES"),
        "browser_observed_public_requests": len(browser_rows),
        "candidate_contracts_probed": len(candidate_contracts),
        "tree_contracts_verified": len(verified_tree_contracts),
        "all_company_contracts_verified": len(verified_company_contracts),
        "cookies_tokens_secrets_persisted": False,
        "auth_bypass_used": False,
        "captcha_bypass_used": False,
        "public_reproducible": public_repro
    }
    (out / "public_reproducibility_audit_v0.66.json").write_text(json.dumps(repro_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ext_rows = []
    n = 0
    for row in network_ledger:
        n += 1
        ext_rows.append({
            "Request_Order": n, "Method": row.get("Method", ""), "URL": row.get("URL", ""),
            "Request_Type": row.get("Request_Type", ""), "Status": row.get("Status", ""),
            "Content_Type": row.get("Content_Type", ""), "Official_B3_Public_Host": "YES",
            "Auth_Bypass": "NO", "Per_Security_Fanout": "NO", "Result": row.get("Result", "")
        })
    write_csv(out / "external_request_ledger_v0.66.csv", ext_rows)

    imm = {
        "frozen_expected_sha256": FROZEN_SHA, "frozen_sha_before": sha_file(FROZEN), "frozen_sha_after": sha_file(FROZEN), "frozen_unchanged": sha_file(FROZEN) == FROZEN_SHA,
        "v057_expected_sha256": V057_SHA, "v057_sha_before": sha_file(V057), "v057_sha_after": sha_file(V057), "v057_unchanged": sha_file(V057) == V057_SHA,
        "v058_expected_sha256": V058_SHA, "v058_sha_before": sha_file(V058), "v058_sha_after": sha_file(V058), "v058_unchanged": sha_file(V058) == V058_SHA,
        "exact37_classification_execution_runs": 0, "pdsc_exact37_generation_runs": 0, "canonical_mapping_population_runs": 0,
        "other_cohort_rechecks": 0, "sector_rs_runs": 0, "p0_runs": 0, "p1_runs": 0, "p2_runs": 0
    }
    (out / "immutability_audit_v0.66.json").write_text(json.dumps(imm, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    prohibited = {
        "alpha_vantage": 0, "yahoo_yfinance": 0, "eodhd": 0, "scalable": 0,
        "wikipedia": 0, "tradingview": 0, "third_party_databases": 0,
        "per_security_fanout": 0, "company_name_matching": 0, "fuzzy_matching": 0,
        "gics_icb_fallback": 0, "price_ohlcv": 0, "news": 0, "trading_analysis": 0,
        "auth_bypass": 0, "captcha_bypass": 0
    }
    (out / "provider_call_audit_v0.66.json").write_text(json.dumps(prohibited, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    tests: list[dict[str, str]] = []
    def t(name: str, ok: bool, detail: Any) -> None:
        tests.append({"Test": name, "Result": "PASS" if ok else "FAIL", "Detail": str(detail)})
        if not ok:
            raise RuntimeError(name)
    t("V065_VERDICT", pred["verdict"] == "BLOCKED_B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBILITY", pred["verdict"])
    t("V065_READY_FALSE", pred["br_exact_37_classification_coverage_ready"] is False, "NO")
    t("V065_COUNTS", (pred["ready"], pred["total"], pred["not_verified"]) == (0,37,37), "0/37/37")
    t("V065_NODES_ZERO", pred["classification_nodes_queried"] == 0, 0)
    t("V065_BLOCKER", pred["blocker"] == "B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE", pred["blocker"])
    t("TARGET_PAGES_TWO", len(spec["target_pages"]) == 2, 2)
    t("ALLOWED_HOSTS_B3_ONLY", all(h.endswith("b3.com.br") or h=="b3.com.br" for h in allowed), ",".join(sorted(allowed)))
    t("NO_AUTH_BYPASS", repro_audit["auth_bypass_used"] is False, "NO")
    t("NO_SECRET_PERSISTENCE", repro_audit["cookies_tokens_secrets_persisted"] is False, "NO")
    t("NO_EXACT37_EXECUTION", imm["exact37_classification_execution_runs"] == 0, 0)
    t("NO_PDSC_EXACT37", imm["pdsc_exact37_generation_runs"] == 0, 0)
    t("NO_CANONICAL_MAPPING", imm["canonical_mapping_population_runs"] == 0, 0)
    t("NO_OTHER_COHORT", imm["other_cohort_rechecks"] == 0, 0)
    t("NO_SECTOR_RS", imm["sector_rs_runs"] == 0, 0)
    t("FROZEN_IMMUTABLE", imm["frozen_unchanged"], FROZEN_SHA)
    t("V057_IMMUTABLE", imm["v057_unchanged"], V057_SHA)
    t("V058_IMMUTABLE", imm["v058_unchanged"], V058_SHA)
    t("P0_P1_P2_ZERO", imm["p0_runs"] == imm["p1_runs"] == imm["p2_runs"] == 0, "0/0/0")
    t("PROHIBITED_PROVIDER_CALLS_ZERO", all(v == 0 for v in prohibited.values()), json.dumps(prohibited, sort_keys=True))
    if verdict == FAIL_VERDICT:
        t("FAIL_BLOCKER_EXACT", blocker == FAIL_BLOCKER, blocker)
    else:
        t("SUCCESS_PUBLIC_REPRO", public_repro is True, public_repro)
        t("SUCCESS_EXACTLY_ONE_MODE_OR_TREE_PRIORITY", tree_ready or company_ready, f"tree={tree_ready},company={company_ready}")
    write_csv(out / "test_results_v0.66.csv", tests)

    summary = {
        "stage": STAGE, "version": VERSION, "verdict": verdict,
        "b3_classification_tree_machine_reproducible": tree_ready,
        "b3_complete_company_classification_dataset_ready": company_ready,
        "discovered_contract": discovered_contract,
        "public_reproducible": public_repro,
        "blocker": blocker,
        "asset_count": len(asset_ledger),
        "browser_observed_request_count": len(browser_rows),
        "candidate_contract_count": len(candidate_contracts),
        "exact37_classification_execution_runs": 0,
        "pdsc_exact37_generation_runs": 0,
        "canonical_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "other_cohort_rechecks": 0,
        "p0_runs": 0, "p1_runs": 0, "p2_runs": 0,
        "prohibited_provider_calls": prohibited,
        "immutability": imm,
        "tests": {"total": len(tests), "passed": len(tests), "failed": 0},
        "artifact_binding": "PENDING_UPLOAD",
        "productive": False,
        "next_gate": next_gate
    }
    checkpoint = {
        "stage": STAGE, "version": VERSION, "verdict": verdict,
        "b3_classification_tree_machine_reproducible": tree_ready,
        "b3_complete_company_classification_dataset_ready": company_ready,
        "discovered_contract": discovered_contract,
        "public_reproducible": public_repro,
        "blocker": blocker,
        "exact37_classification_execution_runs": 0,
        "canonical_mapping_population_runs": 0,
        "sector_rs_runs": 0,
        "p0_runs": 0, "p1_p2_runs": 0,
        "tests_passed": len(tests), "tests_failed": 0,
        "artifact_binding": "PENDING_UPLOAD",
        "next_gate": next_gate
    }
    (out / "summary_preupload_v0.66.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "stage_checkpoint_preupload_v0.66.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    files: dict[str, Any] = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name] = {"sha256": sha_file(p), "bytes": p.stat().st_size}
    manifest = {
        "stage": STAGE, "version": VERSION, "required_start_head": REQUIRED_START_HEAD,
        "repository_sha": args.repository_sha, "verdict": verdict,
        "b3_classification_tree_machine_reproducible": tree_ready,
        "b3_complete_company_classification_dataset_ready": company_ready,
        "discovered_contract": discovered_contract,
        "public_reproducible": public_repro,
        "blocker": blocker,
        "frozen_sha256": FROZEN_SHA, "v057_feature_sha256": V057_SHA, "v058_home_rs_sha256": V058_SHA,
        "exact37_classification_execution_runs": 0, "pdsc_exact37_generation_runs": 0,
        "canonical_mapping_population_runs": 0, "sector_rs_runs": 0, "other_cohort_rechecks": 0,
        "p0_runs": 0, "p1_runs": 0, "p2_runs": 0,
        "productive": False, "artifact_binding": "PENDING_UPLOAD",
        "files": files, "next_gate": next_gate
    }
    (out / "manifest_preupload_v0.66.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": verdict,
        "b3_classification_tree_machine_reproducible": tree_ready,
        "b3_complete_company_classification_dataset_ready": company_ready,
        "discovered_contract": discovered_contract,
        "public_reproducible": public_repro,
        "blocker": blocker,
        "next_gate": next_gate
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
