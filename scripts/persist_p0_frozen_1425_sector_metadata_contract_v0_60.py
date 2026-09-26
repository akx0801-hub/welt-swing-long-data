#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

VERSION = "v0.60"
STAGE = "P0_FROZEN_1425_SECTOR_METADATA_CONTRACT_DEFINITION_GATE"
REQUIRED_START_HEAD = "3327e1245b0b0bf387445d78bfd2a3c66077538a"
BLOCKER = "GOVERNANCE_DECISION_REQUIRED_CANONICAL_SECTOR_TAXONOMY"
VERDICT = "BLOCKED_GOVERNANCE_AUTHORITY_REQUIRED"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="output_p0_frozen_1425_sector_metadata_contract_v0_60")
    ap.add_argument("--artifact-id", required=True, type=int)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--workflow-run-id", required=True, type=int)
    ap.add_argument("--workflow-head-sha", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    pre = json.loads((out / "summary_preupload_v0.60.json").read_text(encoding="utf-8"))
    chk = json.loads((out / "stage_checkpoint_preupload_v0.60.json").read_text(encoding="utf-8"))
    contract = json.loads((out / "sector_metadata_contract_v0.60.json").read_text(encoding="utf-8"))
    tests = read_csv(out / "test_results_v0.60.csv")

    if pre["verdict"] != VERDICT:
        raise RuntimeError("unexpected v0.60 verdict")
    if pre["sector_metadata_contract_ready"] is not False:
        raise RuntimeError("contract cannot be persisted READY")
    if pre["blocker"] != BLOCKER or pre["affected_count"] != 1425:
        raise RuntimeError("governance blocker mismatch")
    if contract["canonical_taxonomy"] != "NOT_DEFINED" or contract["canonical_sector_field"] != "NOT_DEFINED":
        raise RuntimeError("taxonomy/field must remain undefined")
    if contract["population_permitted"] is not False or contract["sector_rs_materialization_permitted"] is not False:
        raise RuntimeError("out-of-scope materialization was enabled")
    if any(r["Result"] != "PASS" for r in tests):
        raise RuntimeError("cannot persist failed tests")
    if any(pre["provider_calls"].values()):
        raise RuntimeError("provider-call audit not zero")
    if pre["p0_runs"] or pre["p1_runs"] or pre["p2_runs"]:
        raise RuntimeError("P0/P1/P2 run count not zero")

    binding = {
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "artifact_id": args.artifact_id,
        "artifact_name": args.artifact_name,
        "artifact_digest": args.artifact_digest,
        "artifact_verified": "PASS",
        "artifact_scope": "pre-persistence v0.60 sector metadata contract governance evidence package",
    }
    (out / "artifact_binding_v0.60.json").write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = dict(pre)
    summary["artifact_binding"] = "PASS"
    summary["artifact"] = binding
    (out / "summary_v0.60.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checkpoint = dict(chk)
    checkpoint.update({
        "artifact_binding": "PASS",
        "workflow_run_id": args.workflow_run_id,
        "artifact_id": args.artifact_id,
        "artifact_digest": args.artifact_digest,
    })
    (out / "stage_checkpoint_v0.60.json").write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = Path("docs/validation/P0_Frozen_1425_Sector_Metadata_Contract_Definition_v0.60.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join([
            "# P0 Frozen-1425 Sector Metadata Contract Definition Gate v0.60",
            "",
            "## Verdict",
            f"**{VERDICT}**",
            "",
            "SECTOR_METADATA_CONTRACT_READY = **NO**.",
            "",
            "## Predecessor authority",
            f"- Required start HEAD verified before mutation: {REQUIRED_START_HEAD}",
            "- v0.59 verdict: PASS_WITH_SECTOR_METADATA_CONTRACT_BLOCKER",
            "- v0.59 Sector RS ready: false",
            "- v0.59 BLOCKED_METADATA: 1425",
            "- v0.59 affected_count: 1425",
            "- v0.59 materialization_runs: 0",
            "- v0.59 workflow: 36243521798",
            "- v0.59 artifact: 10906513700",
            "- v0.59 artifact digest: sha256:ed79a1cad64fa409f72fd21d23669d77b720a99c6f12e379fd48c1573a1f4ab0",
            "- v0.58 Home-Market RS remains 1425/1425 READY.",
            "",
            "## Authority-first finding",
            "The authoritative repository materials bind several partial contract semantics: WS_ID linkage; required normalized metadata fields; allowed bulk source classes; provenance fields; source version/as-of; Mapping_Status; fail-closed handling of ambiguous or absent metadata; and a prohibition on silent taxonomy mixing without a crosswalk.",
            "",
            "They do **not** explicitly select GICS, ICB, another single taxonomy, or an authorized taxonomy-selection rule. They also do not bind one canonical sector field to a selected taxonomy, and they do not define an authoritative crosswalk for mixed taxonomies.",
            "",
            "The v0.59 authority explicitly states that historical US GICS data is source-specific historical evidence and is not promoted as the canonical global Frozen-1425 taxonomy or mapping authority. Therefore v0.60 does not promote GICS, ICB, any other taxonomy, or a crosswalk.",
            "",
            "## Canonical field decision",
            "- Canonical taxonomy: NOT_DEFINED",
            "- Canonical sector field: NOT_DEFINED",
            "- Source-field crosswalk created: NO",
            "- Sector metadata population: NOT RUN",
            "- Sector RS materialization: NOT RUN",
            "",
            "## Smallest governance blocker",
            f"**{BLOCKER}**",
            "",
            "An explicit governance authority must select the canonical sector taxonomy, or explicitly authorize a deterministic taxonomy-selection rule. Downstream field binding and any optional crosswalk design remain blocked until that decision exists.",
            "",
            "## Immutability",
            "- Frozen SHA-256 unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb",
            "- v0.57 Feature Semantic SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9",
            "- v0.58 Home-Market RS Semantic SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32",
            "- Security identity mutation: NO",
            "- Provider mapping mutation: NO",
            "- Local feature mutation: NO",
            "- Provider calls: market=0, Yahoo/yfinance=0, EODHD=0, Alpha Vantage=0, Scalable=0",
            "- P0/P1/P2 runs: 0",
            "",
            "## Artifact binding",
            f"- Workflow run: {args.workflow_run_id}",
            f"- Workflow head: {args.workflow_head_sha}",
            f"- Artifact: {args.artifact_id}",
            f"- Artifact name: {args.artifact_name}",
            f"- Artifact digest: {args.artifact_digest}",
            "",
            "## Next gate",
            f"**{BLOCKER}**",
            "",
            "Hard stop: no taxonomy selection, no sector population, no Sector RS, no P0/P1/P2, no shortlist, no Scalable check, no trading statement.",
        ]) + "\n",
        encoding="utf-8",
    )

    files: dict[str, dict[str, int | str]] = {}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "manifest_v0.60.json":
            files[p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    files[str(report)] = {"sha256": sha256_file(report), "bytes": report.stat().st_size}

    manifest = {
        "stage": STAGE,
        "version": VERSION,
        "verdict": VERDICT,
        "sector_metadata_contract_ready": False,
        "ready": 0,
        "total": 1425,
        "affected_count": 1425,
        "blocker": BLOCKER,
        "required_start_head": REQUIRED_START_HEAD,
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "artifact": binding,
        "frozen_sha256": pre["input_immutability"]["frozen_expected_sha256"],
        "v057_feature_sha256": pre["input_immutability"]["v057_feature_expected_sha256"],
        "v058_home_rs_sha256": pre["input_immutability"]["v058_home_rs_expected_sha256"],
        "provider_calls": pre["provider_calls"],
        "sector_metadata_population_runs": 0,
        "sector_rs_materialization_runs": 0,
        "p0_runs": 0,
        "p1_runs": 0,
        "p2_runs": 0,
        "productive": False,
        "files": files,
        "next_gate": BLOCKER,
    }
    (out / "manifest_v0.60.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": VERDICT,
        "sector_metadata_contract_ready": False,
        "affected_count": 1425,
        "blocker": BLOCKER,
        "workflow_run_id": args.workflow_run_id,
        "artifact_id": args.artifact_id,
        "next_gate": BLOCKER,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
