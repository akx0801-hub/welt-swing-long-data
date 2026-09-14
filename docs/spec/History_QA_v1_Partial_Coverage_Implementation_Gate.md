# History QA v1 Partial Coverage Implementation Gate

## Authority state

**IMPLEMENTATION_VALIDATED**

Lifecycle model:

1. `IMPLEMENTATION_NOT_PERSISTED`
2. `IMPLEMENTATION_PERSISTED_VALIDATION_PENDING`
3. `IMPLEMENTATION_VALIDATED`

The implementation authority was persisted in the prior gate, repaired at commit `bb0ef11c4f8a8584006049b20449baa42ddb1831`, and subsequently validated by the committed GitHub Actions workflow. This closeout records the transition from `IMPLEMENTATION_PERSISTED_VALIDATION_PENDING` to `IMPLEMENTATION_VALIDATED`.

## Execution state

**EXECUTED / SUCCESS**

Authoritative validation execution:

- workflow: `.github/workflows/history_qa_v1_validation.yml`
- run ID: `34843238084`
- event: `workflow_dispatch`
- validated commit: `bb0ef11c4f8a8584006049b20449baa42ddb1831`
- run attempt: 1
- conclusion: `success`
- validation completion timestamp: `2026-09-14T12:07:48Z`

## Full population validation

**VALIDATED**

The committed workflow executed the History QA v1 generator twice independently against the complete committed repository inputs, compared raw bytes and SHA-256 values, ran the focused committed validator, checked full-population invariants, checked repository immutability, and uploaded validation evidence.

Validation checks:

- static no-network/provider gate: PASS
- policy contract gate: PASS
- focused implementation compile: PASS
- generator run 1: PASS
- generator run 2: PASS
- deterministic SHA-256 equality: PASS
- raw byte equality: PASS
- focused committed validator: 7 tests PASS
- full-population invariants: PASS
- repository immutability: PASS
- validation artifact upload: PASS

Generator evidence:

- run 1 SHA-256: `c8454ea60e559d04236241dcbe3323835592d0802f90ba3a9e0566841e680f60`
- run 2 SHA-256: `c8454ea60e559d04236241dcbe3323835592d0802f90ba3a9e0566841e680f60`
- output bytes per run: `820333`

## Validation artifact

- artifact name: `history-qa-v1-validation-34843238084`
- artifact ID: `10346693672`
- artifact digest: `sha256:1045793d906c5bcaba64d77413cd477d94aa76d8773af37acc412b3eb399c1a2`

The artifact is execution evidence only. The materialized History QA CSV remains derived and non-canonical.

## Production / QA release

**NOT_AUTHORIZED**

`IMPLEMENTATION_VALIDATED` establishes execution evidence for History QA v1 only. It does not authorize a productive Welt-Swing v7.2 Universe change, U3K freeze, U3K membership creation, production release, market-data refresh, automatic promotion of Research Partial members, Company_Key resolution, or reopening of P0 byte work.

## Canonical authority model

Canonical History QA v1 authority remains:

`SOURCE INPUTS + POLICY + GENERATOR + VALIDATOR + REPORT`

The materialized 2,527-row History QA CSV is **DERIVED / NON-CANONICAL**.

## Materialized output

The validation workflow created derived outputs only in the GitHub Actions workspace / validation evidence context.

Materialized output authority:

**DERIVED / NON-CANONICAL**

The derived CSV is not committed to the repository by the validation workflow or this closeout gate.

## Policy

Policy file:

`config/history_qa_v1_policy.json`

Policy version:

`WELT-SWING-HISTORY-QA-v1.0`

Validated policy thresholds:

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

The validated generator remains repository-local and deterministic. It uses the committed Company/Security mapping authority for `Security_Key`, preserves current Research Partial order, normalizes original baseline history evidence using v0.53 lineage with v0.47/v0.38 support, uses the persisted US1 legacy-to-current bridge, and emits explicit fail-closed unavailable rows when no History QA evidence is attached.

The validation workflow confirmed that the generator and focused validator contain no prohibited market-data provider/network behavior under the committed static gate.

## Fixed output schema

The derived output schema remains exactly:

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

## Validated population invariants

GitHub Actions run `34843238084` validated:

- Research Partial: 2527
- History QA output rows: 2527
- unique `Security_Key`: 2527
- unique `Source_WS_ID`: 2527
- evidence-backed rows: 2005
- no-history-evidence rows: 522
- US2 `HISTORY_UNAVAILABLE`: 369
- AU1 `HISTORY_UNAVAILABLE`: 153
- Strict: 759
- Frozen: 0
- Universe Membership Changed: NO

Actual execution distributions:

History status:

- `HISTORY_CONFLICT`: 9
- `HISTORY_OK`: 1606
- `HISTORY_PARTIAL`: 380
- `HISTORY_TOO_SHORT`: 9
- `HISTORY_UNAVAILABLE`: 523

Currentness:

- `CURRENT`: 1633
- `UNAVAILABLE`: 523
- `UNKNOWN`: 371

Adjustment integrity:

- `ADJUSTMENT_PARTIAL`: 1633
- `ADJUSTMENT_UNKNOWN`: 894

QA confidence:

- `LOW`: 380
- `MEDIUM`: 1606
- `UNRESOLVED`: 541

The total `HISTORY_UNAVAILABLE` count is 523 while the explicit no-history-evidence cohort is 522; one evidence-backed row is also unavailable. The two measures are intentionally not conflated.

## Fail-closed uncovered model

The focused validator and full-population invariant step validated the 522 no-history-evidence rows fail closed:

- `History_Status = HISTORY_UNAVAILABLE`
- `History_Currentness_Status = UNAVAILABLE`
- `QA_Confidence = UNRESOLVED`
- unavailable history measurement fields are NULL/empty
- `MISSING_HISTORY_EVIDENCE` present
- `MISSING_CURRENTNESS_METADATA` present
- no row in the cohort has `HISTORY_OK`

Admission provenance may remain in `Source_ID`; it does not imply a market-history source.

## Validator authority

Validator:

`tests/test_history_qa_v1.py`

The committed focused validator executed successfully in run `34843238084`:

- tests executed: 7
- tests passed: 7
- result: PASS

The tests cover exact output schema, current security population and identity, expected partial-coverage fail-closed behavior, vocabulary/policy/flags, Strict/Frozen governance, repeated byte/SHA determinism, and source-conflict precedence.

## Repository immutability

The validation workflow's repository immutability gate passed. The remote `main` head remained `bb0ef11c4f8a8584006049b20449baa42ddb1831` after validation and before this documentation-only closeout commit.

No generator, policy, validator, workflow, Universe source, Strict artifact, or Frozen artifact is modified by this closeout.

## Authority transition

Before closeout:

`IMPLEMENTATION_PERSISTED_VALIDATION_PENDING`

After closeout:

`IMPLEMENTATION_VALIDATED`

This transition is supported by successful full-population execution evidence and does not change any higher Universe membership layer or production-release state.
