# Liquidity QA v1 Bounded Implementation Gate

## Authority state

**IMPLEMENTATION_PERSISTED_VALIDATION_PENDING**

This document records the bounded implementation authority for Liquidity QA v1. Persistence of this implementation does not constitute independent execution attestation and does not set `IMPLEMENTATION_VALIDATED`.

## Purpose and governance

Liquidity QA v1 normalizes committed repository-local liquidity evidence onto the current 2,527-security Research Partial with exactly one row per current `Security_Key`. It is DEV / RESEARCH / SHADOW infrastructure only. Productive trading authority remains Welt-Swing v7.2.

Layer separation remains mandatory:

`Membership != History QA != Liquidity QA != Tradeability != Eligibility != Scan != Execution`.

This implementation does not change Research Partial membership, Strict, Frozen/U3K, Tradeability, Eligibility, Scan, Execution, Company_Key, Company/Security Mapping, or History QA v1.

## Population

Fixed implementation population:

- Research Partial: 2,527
- original cohort: 1,633
- US1 integrated cohort: 372
- US2 unsupported liquidity cohort: 369
- AU1 unsupported liquidity cohort: 153
- unsupported liquidity total: 522
- Strict diagnostic count: 759
- Frozen: 0

Output order is exactly current Research Partial order. `Security_Key` is obtained only through `scripts/generate_company_security_mapping_v1.py`; no ad-hoc ISIN/ticker/MIC/company-name key construction is permitted.

## Output schema

Exact ordered schema:

1. `Security_Key`
2. `Source_WS_ID`
3. `Evidence_Source_WS_ID`
4. `Liquidity_Status`
5. `Liquidity_Bucket`
6. `Usable_Session_Count`
7. `MedianTurnover20_EUR`
8. `Zero_Volume_Share`
9. `Price_Currency`
10. `FX_Evidence_Status`
11. `Last_Liquidity_Observation_Date`
12. `Liquidity_Currentness_Status`
13. `Listing_Resolution_Status`
14. `Source_ID`
15. `Evidence_Artifact`
16. `Source_AsOf`
17. `Retrieved_At`
18. `Liquidity_Policy_Version`
19. `QA_Confidence`
20. `QA_Flags`

Zero means a measured zero. Empty means unavailable, unsupported or not measured. Required schema presence does not imply every value is non-empty.

## Status vocabulary and precedence

Primary status vocabulary:

1. `LIQUIDITY_CONFLICT`
2. `LIQUIDITY_IDENTITY_UNRESOLVED`
3. `LIQUIDITY_UNAVAILABLE`
4. `LIQUIDITY_STALE`
5. `LIQUIDITY_VERY_THIN`
6. `LIQUIDITY_THIN`
7. `LIQUIDITY_OK`

The list above is also exact precedence. Material contradiction therefore outranks favorable measured turnover.

Auxiliary bucket vocabulary:

- `PREFERRED`
- `STANDARD`
- `LOW_EXCEPTION`
- `FAIL_LT_5M`

Preferred and standard are both `LIQUIDITY_OK`; the bucket preserves the established quality distinction without expanding primary status vocabulary.

## Threshold policy

A measured classification requires all of:

- `Usable_Session_Count >= 18`
- defensible FX status
- `LISTING_RESOLVED`

Threshold mapping:

- `MedianTurnover20_EUR >= 20,000,000` -> `PREFERRED` / `LIQUIDITY_OK`
- `15,000,000 <= value < 20,000,000` -> `STANDARD` / `LIQUIDITY_OK`
- `5,000,000 <= value < 15,000,000` -> `LOW_EXCEPTION` / `LIQUIDITY_THIN`
- `value < 5,000,000` -> `FAIL_LT_5M` / `LIQUIDITY_VERY_THIN`

If usable sessions are below 18, the row is `LIQUIDITY_UNAVAILABLE`, the bucket is empty, and `INSUFFICIENT_USABLE_SESSIONS` is set. Insufficient-window evidence is not classified as very thin.

Policy version: `WELT-SWING-LIQUIDITY-QA-v1.0`.

Numeric liquidity stale threshold remains `DEFERRED`. Zero-volume status threshold is `NONE_INFORMATIONAL_ONLY`.

## FX contract

Controlled FX vocabulary:

- `FX_IDENTITY_EUR`
- `FX_OK`
- `FX_PARTIAL`
- `FX_UNAVAILABLE`
- `FX_CONFLICT`

EUR is arithmetic identity and may use `FX_IDENTITY_EUR`.

A non-EUR populated `MedianTurnover20_EUR` requires `FX_OK` or `FX_PARTIAL`. `FX_UNAVAILABLE` forces the EUR turnover measurement to empty and the primary status to `LIQUIDITY_UNAVAILABLE`. `FX_CONFLICT` forces `LIQUIDITY_CONFLICT`. Native-currency turnover is never relabeled as EUR.

For v0.38, `FX_OK` requires persisted resolved currency coverage, persisted FX daily evidence and sufficient matching committed session evidence. Where the EUR turnover summary is persisted and FX resolution is demonstrable but equivalent committed session evidence is incomplete, the implementation uses `FX_PARTIAL` and fail-closed confidence/flags rather than overstating evidence.

For successfully bridged US1 rows, the persisted EUR turnover was built using `USDEUR=X`, but equivalent session-level FX lineage is not committed. Therefore US1 uses `FX_PARTIAL`.

AU1 currently has no liquidity evidence and uses `FX_UNAVAILABLE`; no external AUD retrieval is performed.

## Currentness semantics

Controlled vocabulary:

- `CURRENT`
- `STALE`
- `UNKNOWN`
- `UNAVAILABLE`

No numeric stale threshold is invented and the History QA 10-day rule is not reused.

- `CURRENT` only when committed row-level evidence deterministically establishes current alignment; v0.38 exact last-session/evidence-as-of equality qualifies.
- `STALE` only from explicit authoritative committed stale evidence.
- `UNKNOWN` when a measurement exists but committed metadata cannot distinguish current from stale.
- `UNAVAILABLE` when there is no defensible liquidity measurement.

## Listing semantics

Allowed listing states:

- `LISTING_RESOLVED`
- `LISTING_PARTIAL`
- `LISTING_UNRESOLVED`
- `LISTING_CONFLICT`
- `LISTING_INACTIVE`

Measured OK/thin/very-thin states require `LISTING_RESOLVED`. Partial/unresolved listings become `LIQUIDITY_IDENTITY_UNRESOLVED`; conflicts become `LIQUIDITY_CONFLICT`; inactive listings become `LIQUIDITY_UNAVAILABLE` with `LISTING_INACTIVE` flag. Missing ISIN alone does not force unresolved listing where governed MIC/ticker/Security_Key identity is sufficient.

## Confidence semantics

Vocabulary: `HIGH`, `MEDIUM`, `LOW`, `UNRESOLVED`.

- `UNRESOLVED`: conflict, identity-unresolved or unavailable primary status; or non-resolved listing.
- `LOW`: stale measured status, or at least two nonfatal limitations among currentness unknown, FX partial and missing session evidence.
- `MEDIUM`: exactly one such nonfatal limitation.
- `HIGH`: measured row, resolved listing, current evidence, FX identity/OK, session evidence present, no material contradiction.

`LEGACY_NORMALIZED` by itself is not a confidence downgrade. Exact US1 bridge use by itself is not a confidence downgrade.

## Controlled QA flags

Exact vocabulary:

- `MISSING_LIQUIDITY_EVIDENCE`
- `MISSING_SESSION_EVIDENCE`
- `MISSING_CURRENTNESS_METADATA`
- `INSUFFICIENT_USABLE_SESSIONS`
- `FX_EVIDENCE_MISSING`
- `FX_EVIDENCE_PARTIAL`
- `LEGACY_NORMALIZED`
- `IDENTITY_UNRESOLVED`
- `STALE_LIQUIDITY`
- `DATA_QUALITY_FAIL`
- `LISTING_INACTIVE`

Thin/very-thin, zero-volume warning and duplicate conflict flags are not added because primary status or field semantics already represent those concepts.

## Source precedence and normalization

### Original 1,633

Precedence:

1. v0.48 remediation evidence for exactly its committed 236 WS_IDs;
2. otherwise v0.38 liquidity evidence.

v0.38 mappings include `Usable_Sessions20`, `MedianTurnover20_EUR`, `Currency_Normalized`, `Liquidity_Last_Session`, `Evidence_AsOf`, plus matching v0.38 zero-volume/fetch metadata. Legacy class is cross-checked, but v1 bucket/status is recomputed from v1 policy.

v0.48 mappings include `Usable20`, `MedianTurnover20_EUR`, `Primary_Currency`, `Last_Session` and legacy FX/class evidence. Currentness is `UNKNOWN` unless committed evidence deterministically proves another allowed state. Zero-volume share is not silently copied from an older pre-remediation measurement.

### US1 372

Binding is exactly:

`legacy US1 WS_ID -> output_us1_write/dry_run_write_plan.csv New_WS_ID -> current Source_WS_ID -> canonical Security_Key`.

Bridge identity must match `ISIN`, `Primary_MIC` and `Primary_Ticker` exactly.

- missing bridge -> `LIQUIDITY_IDENTITY_UNRESOLVED`
- duplicate `New_WS_ID` bridge -> `LIQUIDITY_CONFLICT`
- material listing disagreement -> `LIQUIDITY_CONFLICT`
- canonical Security_Key failure -> hard generator failure

Successfully normalized US1 rows map `Usable20` and `MedianTurnover20_EUR`, use `Price_Currency=USD`, `FX_PARTIAL`, blank last liquidity observation date, `UNKNOWN` currentness and default flags `LEGACY_NORMALIZED|MISSING_SESSION_EVIDENCE|MISSING_CURRENTNESS_METADATA|FX_EVIDENCE_PARTIAL`. Default confidence is LOW.

### US2 369 and AU1 153

All 522 unsupported securities remain explicit output rows and fail closed as `LIQUIDITY_UNAVAILABLE`.

Required unsupported fields:

- bucket empty
- usable sessions empty
- median turnover empty
- zero-volume share empty
- last liquidity observation empty
- currentness `UNAVAILABLE`
- confidence `UNRESOLVED`
- flags include `MISSING_LIQUIDITY_EVIDENCE` and `MISSING_CURRENTNESS_METADATA`

AU1 additionally uses `FX_UNAVAILABLE` and `FX_EVIDENCE_MISSING`. Admission `Source_ID` may remain for provenance but does not imply market-data evidence.

## Generator and output authority

Generator: `scripts/generate_liquidity_qa_v1.py`.

Derived output: `output_liquidity_qa_v1/liquidity_qa_v1_2527.csv`.

Authority model:

`COMMITTED INPUTS + POLICY + GENERATOR + VALIDATOR + SPEC/REPORT`.

The materialized CSV is **DERIVED / NON-CANONICAL** and must not be committed by this gate.

Generation is deterministic: UTF-8, LF, fixed schema, exact Research Partial order, no runtime timestamps, no runtime-today dependency, no provider/network calls and no runtime SQLite dependency.

## Validation requirements

Focused validation must establish at least:

- 2,527 rows
- 2,527 unique Security_Key
- 2,527 unique Source_WS_ID
- exact source order
- Security_Key exact canonical mapping
- cohort counts 1,633 / 372 / 369 / 153
- exactly 522 unsupported liquidity rows
- all 522 fail closed
- all AU1 unsupported rows carry the additional FX missing state/flag
- threshold/bucket/status mapping
- insufficient-window fail-closed behavior
- FX invariants
- controlled vocabularies and flags
- US1 bridge traceability
- deterministic double generation with byte and SHA-256 equality
- Research Partial 2,527
- Strict 759
- Frozen 0
- Universe write false
- no provider/network behavior in generator

Independent execution/CI attestation is a later gate. Persistence alone does not set `IMPLEMENTATION_VALIDATED`.

## Non-authorizations

This implementation does not authorize:

- provider or market-data acquisition
- FX download
- Universe/Research Partial mutation
- U3K membership or freeze
- productive release
- Tradeability, Eligibility, Scan or Execution decisions
- Company_Key inference
- security merges
- History QA modification
- Company/Security Mapping redesign
- P0 byte-work reopening

## Next state

After the authorized implementation commit, authority state is:

**IMPLEMENTATION_PERSISTED_VALIDATION_PENDING**

The next bounded stage is independent execution validation / CI enablement. No automatic continuation is authorized here.
