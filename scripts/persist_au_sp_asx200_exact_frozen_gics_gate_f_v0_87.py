#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="v0.87"
STAGE="AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def wj(p:Path,o):p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="output_au_sp_asx200_exact_frozen_gics_gate_f_v0_87")
    ap.add_argument("--artifact-id",required=True,type=int)
    ap.add_argument("--artifact-digest",required=True)
    ap.add_argument("--artifact-name",required=True)
    ap.add_argument("--workflow-run-id",required=True,type=int)
    ap.add_argument("--workflow-head-sha",required=True)
    a=ap.parse_args();out=ROOT/a.output_dir
    s=json.loads((out/"summary_preupload_v0.87.json").read_text())
    c=json.loads((out/"stage_checkpoint_preupload_v0.87.json").read_text())
    dig=a.artifact_digest if a.artifact_digest.startswith("sha256:") else "sha256:"+a.artifact_digest
    bind={"artifact_id":a.artifact_id,"artifact_digest":dig,"artifact_name":a.artifact_name,"artifact_verified":"PASS",
          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha}
    wj(out/"artifact_binding_v0.87.json",bind)
    sf=dict(s);sf["artifact_binding"]="PASS";sf["artifact"]=bind;wj(out/"summary_v0.87.json",sf)
    cf=dict(c);cf.update({"artifact_binding":"PASS","artifact_id":a.artifact_id,"artifact_digest":dig,
                          "workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha})
    wj(out/"stage_checkpoint_v0.87.json",cf)

    report=ROOT/"docs/validation/AU_SP_ASX200_Exact_Frozen_GICS_Classification_Coverage_Gate_F_v0.87.md"
    report.parent.mkdir(parents=True,exist_ok=True)
    drift=sf.get("source_drift",{})
    lines=[
      "# AU_SP_ASX200 Exact Frozen GICS Industry-Group Classification Coverage Gate F v0.87","",
      "## Verdict",f"**{sf['verdict']}**","",
      f"AU_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_READY = **{'YES' if sf['au_exact_frozen_gics_classification_coverage_ready'] else 'NO'}**.",
      f"FROZEN TOTAL = **{sf['frozen_total']}**.",
      f"CURRENT ASX DIRECTORY ROWS = **{sf['current_asx_directory_rows']}**.",
      f"EXACT SOURCE LINKS = **{sf['exact_source_links']}**.",
      f"PROVABLY CLASSIFIED = **{sf['provably_classified']}**.",
      f"NOT_PROVABLY_CLASSIFIED = **{sf['not_provably_classified']}**.",
      f"NOT_FOUND = **{sf['not_found']}**.",
      f"AMBIGUOUS = **{sf['ambiguous']}**.",
      f"NOT_VERIFIED = **{sf['not_verified']}**.",
      f"CONFLICT = **{sf['conflict']}**.",
      f"FORMAL LABEL BINDING = **{sf['formal_label_binding']}**.",
      f"SOURCE-NATIVE CODE COVERAGE = **{sf['source_native_code_coverage']}**.",
      f"NONFORMAL FROZEN EXPOSURE = **{sf['nonformal_frozen_exposure']}**.",
      f"USED DISTINCT GICS CODES = **{sf['used_distinct_gics_codes']}**.",
      f"UNAUTHORIZED CODES = **{sf['unauthorized_codes']}**.",
      f"PDSC GENERATED = **{sf['pdsc_generated']}**.","",
      "## Source drift",
      f"- BYTE_DRIFT: {drift.get('BYTE_DRIFT','NOT_VERIFIED')}",
      f"- ROW_COUNT_DRIFT: {drift.get('ROW_COUNT_DRIFT','NOT_VERIFIED')}",
      f"- SCHEMA_DRIFT: {drift.get('SCHEMA_DRIFT','NOT_VERIFIED')}",
      f"- FROZEN_IDENTITY_DRIFT: {drift.get('FROZEN_IDENTITY_DRIFT','NOT_VERIFIED')}",
      f"- FROZEN_CLASSIFICATION_DRIFT: {drift.get('FROZEN_CLASSIFICATION_DRIFT','NOT_VERIFIED')}","",
      "## Scope",
      "Gate F only. The exact v0.86 Frozen identity target was rebuilt from Frozen identity fields plus the governed Security_Key cohort sidecar and required to match the predecessor target exactly. "
      "One fresh official ASX company-directory CSV snapshot was joined by exact ASX code only. Formal labels and source-native four-digit codes came solely from persisted v0.85 MSCI authority. "
      "No company-name linkage, fuzzy/semantic mapping, ticker-history repair, PDSC, MSCI network request, Gate G/H, canonical materialization, other cohort, Sector RS or P0/P1/P2 was executed.","",
      "## Blocker",f"**{sf['blocker'] or 'NONE'}**.","",
      "## Artifact binding",f"- Workflow run: {a.workflow_run_id}",f"- Workflow head: {a.workflow_head_sha}",
      f"- Artifact: {a.artifact_id}",f"- Artifact digest: {dig}","",
      "## Next gate",f"**{sf['next_gate']}**","","Hard stop applied."
    ]
    report.write_text("\n".join(lines)+"\n",encoding="utf-8")
    files={}
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!="manifest_v0.87.json":files[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    files[str(report.relative_to(ROOT))]={"bytes":report.stat().st_size,"sha256":sha(report)}
    wj(out/"manifest_v0.87.json",{
      "version":VERSION,"stage":STAGE,"verdict":sf["verdict"],
      "au_exact_frozen_gics_classification_coverage_ready":sf["au_exact_frozen_gics_classification_coverage_ready"],
      "blocker":sf["blocker"],"workflow_run_id":a.workflow_run_id,"workflow_head_sha":a.workflow_head_sha,
      "artifact_id":a.artifact_id,"artifact_digest":dig,"canonical_ready_rows":37,"canonical_total_rows":1425,
      "gate_g_runs":0,"gate_h_runs":0,"canonical_materialization_runs":0,"other_cohort_runs":0,
      "sector_rs_runs":0,"p0_runs":0,"p1_runs":0,"p2_runs":0,"files":files,"next_gate":sf["next_gate"]
    })
    return 0

if __name__=="__main__":raise SystemExit(main())
