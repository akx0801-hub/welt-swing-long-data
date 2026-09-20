# Market Evidence 522 Acquisition Adapter v1

## Authority state

IMPLEMENTATION_PERSISTED_EXECUTION_PENDING after the bounded persistence commit.

This document is implementation authority for the acquisition adapter only. It does not validate an acquisition run and does not change History QA v1 or Liquidity QA v1 authority.

## Purpose and fixed population

The adapter supplies governed OHLCV and FX evidence for exactly the current missing-evidence cohort:

- US2: 369
- AU1: 153
- total: 522
- Research Partial: 2527
- Strict diagnostic count: 759
- Frozen: 0
- Universe write: false
- Productive trading authority: false

Layer separation remains mandatory:

Membership != Acquisition Evidence != History QA != Liquidity QA != Tradeability != Eligibility != Scan != Execution.

Company_Key is not required.

## Identity and cohort binding

Canonical source is universe/research_partial_1633.csv.

Canonical Security_Key authority is scripts/generate_company_security_mapping_v1.py.

The adapter selects only:

- Source_ID US2_SP400_COMMON_ADMISSION -> exactly 369 rows
- Source_ID AU1_EVIDENCE_ADMISSION_GATE -> exactly 153 rows

Join is current WS_ID to mapping Source_WS_ID to canonical Security_Key. Names are never join keys.

Whole-run hard failures include missing or duplicate Security_Key, duplicate Source_WS_ID, missing mapping, mapping/listing contradiction, count mismatch, unsupported cohort MIC/currency, unresolved provider symbol and provider-symbol collision.

## Provider symbol authority

Provider mapping reuses scripts/price_cache.py:

- derive_yahoo_symbol
- audited project Yahoo overrides when present
- current explicit Yahoo_Symbol only when consistent with governed MIC/ticker mapping

US2 permits XNYS/XNAS and USD only. Existing US Yahoo rules apply without venue suffix.

AU1 permits XASX and AUD only. Existing XASX .AX rule applies.

An unexplained explicit-versus-derived or explicit-versus-override mismatch is a governance failure. No symbol search, alternate listing search, web lookup or silent provider fallback is authorized.

## Stock acquisition contract

Provider authority is YFINANCE_FREE through the existing YFinanceBatchClient.

Stock request contract:

- period 2y
- interval 1d
- auto_adjust false
- back_adjust false
- actions true
- batch size 100
- maximum one identical retry per batch
- one grouped rescue wave for symbols omitted from an otherwise successful initial response
- no serial per-security symbol fallback
- repair false for initial and rescue passes
- bounded repair true only for the existing suspicious-return QA condition

Provider duplicate dates are detected before existing normalization can collapse them. A duplicate-date security becomes DUPLICATE_DATE_CONFLICT and ambiguous observations are not persisted.

## Closed-bar contract

One UTC Retrieved_At is captured per run.

Closed_Bar_Cutoff equals UTC calendar date of Retrieved_At minus one calendar day.

Only observations on or before the cutoff are persisted. Later rows are excluded and counted/flagged. No synthetic bars are created for holidays, weekends or missing sessions.

Source_AsOf records the fixed closed-bar cutoff. Actual market recency remains auditable from observation dates and acquisition QA.

## Evidence artifacts

All artifacts are DERIVED / NON-CANONICAL and have no Universe authority.

### security_binding_522.csv

Exact ordered schema:

Security_Key, Source_WS_ID, Cohort, ISIN, Primary_MIC, Primary_Ticker, Provider_Symbol, Provider_Mapping_Status, Price_Currency, Source_ID

Key: Security_Key.

Order: current Research Partial order restricted to the target cohort.

### ohlcv_daily_522.csv

Exact ordered schema:

Security_Key, Source_WS_ID, Observation_Date, Open, High, Low, Close, Adjusted_Close, Volume, Dividend, Stock_Split, Price_Currency, Primary_MIC, Primary_Ticker, Provider_Symbol, Provider_Repaired, Source_ID, Source_AsOf, Retrieved_At, Adjustment_Status, Observation_Status

Key: Security_Key + Observation_Date.

Adjusted_Close, Dividend and Stock_Split are retained when supplied. Blank means unavailable; measured zero remains zero. Acquisition does not claim ADJUSTMENT_OK merely because adjustment fields exist.

### fx_daily_522.csv

Exact ordered schema:

FX_Observation_Date, Price_Currency, FX_to_EUR, FX_Source_Symbol, FX_Direction, Source_ID, Source_AsOf, Retrieved_At, Observation_Status

Key: Price_Currency + FX_Observation_Date.

Only USD and AUD are in scope.

### acquisition_qa_522.csv

Exact ordered schema:

Security_Key, Source_WS_ID, Cohort, Provider_Symbol, Acquisition_Status, Unique_Observations, Valid_Observations, Invalid_Observations, Duplicate_Dates, Future_Dates, Repaired_Observations, First_Observation_Date, Last_Observation_Date, Zero_Volume_Share, Adjustment_Status, Source_ID, Source_AsOf, Retrieved_At, QA_Flags

Exactly 522 rows are required, including row-level failures.

### acquisition_manifest_522.json

The manifest records repository SHA, policy version, source/cutoff/retrieval provenance, fixed cohort/governance counts, output row counts, SHA-256 and byte sizes for the four CSV artifacts, acquisition-status distributions, FX observation distributions and universe_write=false.

Raw runtime SQLite is not authority. No generated evidence artifact is automatically Universe, membership, History QA or Liquidity QA authority.

## OHLCV validity and row-level failure semantics

The adapter reuses price_cache.py normalization, technical validity and History QA behavior.

Cross-market all-OHLC-NaN placeholders are not observations. Invalid retained provider observations are marked OBSERVATION_INVALID_OHLCV rather than fabricated into valid bars.

Row-level statuses include:

- READY
- PROVIDER_UNAVAILABLE
- SECURITY_NOT_FOUND
- NO_HISTORY
- SHORT_HISTORY
- STALE_HISTORY
- DATA_QUALITY_FAIL
- DUPLICATE_DATE_CONFLICT
- IDENTITY_SYMBOL_MISMATCH

A row-level failure does not invalidate unrelated securities. Identity/governance corruption is a whole-run hard failure.

History thresholds remain unchanged: 260 unique bars, 252 valid bars and the validated 10-calendar-day stale policy.

## FX contract

Direct pairs:

- USD to EUR: USDEUR=X
- AUD to EUR: AUDEUR=X

If direct evidence is unavailable, only configured reverse pairs may be attempted:

- EURUSD=X
- EURAUD=X

Reverse values are explicitly inverted and labelled REVERSE_EUR_TO_CCY_INVERTED.

Raw FX observations preserve actual provider dates. Acquisition performs no synthetic forward fill, no current-spot substitution and no unbounded carry-forward.

For later Liquidity derivation, a security session may use the latest FX observation on or before that session only within a maximum backward tolerance of 10 calendar days. Future FX is never used. Missing bounded FX leaves the session without EUR turnover evidence.

Missing FX does not erase otherwise valid History evidence.

## Offline validation contract

Focused fixture tests cover:

- deterministic 369/153/522 cohort construction
- unique Security_Key and Source_WS_ID
- XNYS/XNAS and XASX symbol rules
- explicit-versus-derived contradiction
- duplicate provider-date detection before normalization
- closed-bar/future exclusion
- OHLCV validity and observation-key uniqueness
- USD/AUD binding
- FX direction
- 10-day bounded backward FX matching without synthetic fill
- row-level and whole-run failure behavior
- exact artifact schemas
- deterministic fixture serialization
- artifact hashes
- universe_write=false
- no provider call in offline helper tests

## Workflow and execution authority

Dedicated workflow:

.github/workflows/market_evidence_522_acquisition_v1.yml

It is workflow_dispatch only, contents read, checkout persist-credentials false, Python 3.11, bounded dependencies, no git commit/push and no repository mutation. Runtime/cache/output files are runner-local only. Exactly the five derived evidence artifacts are uploaded.

This implementation gate does not dispatch or execute the workflow.

## Non-authorizations

Not authorized by this implementation:

- provider calls during this gate
- acquisition execution during this gate
- committing generated evidence
- Universe/Research Partial mutation
- Strict/Frozen changes
- U3K freeze or membership
- History QA v1 modification
- Liquidity QA v1 modification
- Company_Key creation
- Tradeability, Eligibility, Scan or Execution decisions

## Next stage

522 Common OHLCV Acquisition — Execution Validation Gate.
