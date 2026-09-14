# History QA v1 Partial Coverage Implementation Gate

## Authority state

**IMPLEMENTATION_PERSISTED_VALIDATION_PENDING**

Lifecycle model:

1. `IMPLEMENTATION_NOT_PERSISTED`
2. `IMPLEMENTATION_PERSISTED_VALIDATION_PENDING`
3. `IMPLEMENTATION_VALIDATED`

This persistence gate moves only from state 1 to state 2. It does not establish state 3.

## Execution state

**NOT_EXECUTED**

Full-population generator execution was intentionally not performed in this gate because the current builder environment cannot materialize the required large committed CSV inputs as complete local files without prohibited reconstruction.

## Full population validation

**VALIDATION_PENDING**

No full-population History QA result, status distribution, output byte count, output SHA-256, deterministic generation result, or focused full-population test result is claimed here.

## CI workflow

`.github/workflows/history_qa_v1_validation.yml`

CI workflow status:

**PERSISTED / NOT YET EXECUTED**

The workflow is outside this gate's changed-file scope and is not modified here. It is the authorized later execution environment for complete-repository validation.

## Production / QA release

**NOT_AUTHORIZED**

A later successful CI execution and explicit execution-attestation gate are required before `IMPLEMENTATION_VALIDATED` may be asserted.

## Canonical authority model

Canonical History QA v1 authority is:

`SOURCE INPUTS + POLICY + GENERATOR + VALIDATOR + REPORT`

The materialized 2,527-row History QA CSV is **DERIVED / NON-CANONICAL**.

## Materialized output

Materialized output:

**NOT_CREATED IN THIS GATE**

Materialized output authority:

**DERIVED / NON-CANONICAL**

Expected derived path when later executed:

`output_history_qa_v1/history_qa_v1_2527.csv`

That derived CSV is not committed by this gate.

## Policy

Policy file:

`config/history_qa_v1_policy.json`

Policy version:

`WELT-SWING-HISTORY-QA-v1.0`

Promoted thresholds encoded in policy:

- minimum unique bars: 260
- minimum valid bars: 252
- stale after calendar days: 10
- maximum invalid bars under promoted filtered-bar policy: 2
- maximum invalid share: 0.01
- minimum valid observations after filtering: 260
- continuity gap threshold: `DEFERRED`

No numeric continuity/gap threshold is invented.

## Generator authority

Generator:

`scripts/generate_history_qa_v1.py`

Approved inputs:

- `universe/research_partial_1633.csv`
- `scripts/generate_company_security_mapping_v1.py`
- `output_qa_v0_53/history_bar_qa_1633_v0.53.csv`
- `output_current_master_research_partial_1633_data_refresh_v0_38/history_gate_current_1633_v0.38.csv`
- `output_current_master_research_partial_1633_data_refresh_v0_38/manifest_v0.38.json`
- `config/current_master_research_partial_1633_mapping_history_liquidity_data_refresh_v0.38.json`
- `output_history_download_applied_239_v0_47/history_qa_239_v0.47.csv`
- `output_history_download_applied_239_v0_47/summary_v0.47.json`
- `output_us1/history_qa_us1.csv`
- `output_us1/summary_us1.json`
- `output_us1_write/dry_run_write_plan.csv`
- `config/history_qa_v1_policy.json`

The generator is repository-local and deterministic by construction. It uses the committed Company/Security mapping authority for `Security_Key`, preserves current Research Partial order, normalizes original baseline history evidence using v0.53 lineage with v0.47/v0.38 support, uses the persisted US1 legacy-to-current bridge, and emits explicit fail-closed unavailable rows when no History QA evidence is attached.

It contains no provider calls, no network calls, no raw-cache dependency, no runtime timestamps, no Universe write, no membership mutation, and no Company_Key inference.

## Fixed output schema

The derived output schema is exactly:

1. `Security_Key`
2. `Source_WS_ID`
3. `Evidence_Source_WS_ID`
4. `History_Status`
5. `History_Start`
6. `History_End`
7. `History_Observation_Count`
8. `History_Valid_Observation_Count`
9. `Expected_Session_Count`
10. `Usable_Session_Count`
11. `Gap_Count`
12. `Gap_Share`
13. `Zero_Volume_Share`
14. `Last_Observation_Date`
15. `History_Currentness_Status`
16. `Listing_Resolution_Status`
17. `Adjustment_Integrity_Status`
18. `Source_ID`
19. `Evidence_Artifact`
20. `Source_AsOf`
21. `Retrieved_At`
22. `History_Policy_Version`
23. `QA_Confidence`
24. `QA_Flags`

Zero means an actually measured zero. Empty/NULL means unavailable, unsupported, or not measured.

## Source precedence and normalization

For the original baseline population, `output_qa_v0_53/history_bar_qa_1633_v0.53.csv` is the primary History-QA authority. `History_Source=v0.47` binds to the v0.47 supporting artifacts; other baseline lineage binds to applicable v0.38 evidence.

For current US1 integration, `output_us1_write/dry_run_write_plan.csv` supplies the persisted legacy `WS_ID` to current `New_WS_ID` bridge, and `output_us1/history_qa_us1.csv` supplies History QA evidence. Identity/listing disagreement fails closed rather than attaching ambiguous history.

Material contradiction among authoritative evidence maps to `HISTORY_CONFLICT`.

No liquidity-only usable-session metric is promoted into the History v1 core.

## Fail-closed uncovered model

When no History QA evidence exists, the generator encodes:

- `History_Status = HISTORY_UNAVAILABLE`
- `History_Currentness_Status = UNAVAILABLE`
- `QA_Confidence = UNRESOLVED`
- history measurement fields = NULL/empty
- `MISSING_HISTORY_EVIDENCE`
- `MISSING_CURRENTNESS_METADATA`

Admission provenance may remain in `Source_ID`; it does not imply a market-history source.

## Validator authority

Validator:

`tests/test_history_qa_v1.py`

The validator is designed for the later complete-repository CI execution. It checks exact output schema and current security population, expected partial-coverage invariants, fail-closed missing-history semantics, approved vocabularies, policy version, Strict/Frozen governance, repeated byte/SHA determinism, and source-conflict precedence.

These checks are defined but **NOT_EXECUTED** in this persistence gate.

## Expected CI invariants

The following are expected future CI invariants, not results from this gate:

- total History QA rows: 2527
- evidence-backed rows: 2005
- no-history-evidence rows: 522
- US2 unavailable rows: 369
- AU1 unavailable rows: 153
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe Membership Changed: NO

Actual History status, currentness, adjustment, and confidence distributions remain **NOT_EXECUTED** until CI.

## Static persistence checks

Bounded static checks authorized for this gate cover Python syntax, JSON syntax, approved schema/vocabularies, absence of provider/network logic, absence of Universe mutation logic, absence of runtime timestamp dependence, and compatibility with the persisted CI workflow.

Full generator execution: **NOT_EXECUTED**

Focused full-population tests: **NOT_EXECUTED**

Full-population validation: **VALIDATION_PENDING**

## CI handoff

The persisted workflow is expected later to check out the complete repository, execute the committed generator twice, compare raw bytes and SHA-256 values, execute the focused validator, verify the expected 2527 / 2005 / 522 / 369 / 153 and 2527 / 759 / 0 invariants, report actual distributions, and upload validation evidence.

A successful CI run still does not by itself rewrite this report or assert `IMPLEMENTATION_VALIDATED`; that state transition belongs to the later execution-attestation gate.
