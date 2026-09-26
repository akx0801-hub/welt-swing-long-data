# P0 ASX OHLC Source-Policy / QA-Contract Decision v0.52

## 1. Policy-gate verdict

**PASS — POLICY_SELECTED_FOR_IMPLEMENTATION**

Selected policy:

**POLICY F — CANONICAL FILTERED INVALID-BAR SOURCE-DEFECT POLICY**

Precise implementation target:

> Preserve every raw provider observation unchanged. Represent a proven/unresolved source-data defect explicitly. Exclude the entire technically invalid bar from technical feature inputs. Determine security cache readiness with the already-promoted generic filtered-invalid-bar QA contract, including its higher-priority suspicious-return, currentness and history gates. Do not reuse individual fields from an otherwise invalid bar unless a later separately governed field-trust contract explicitly authorizes that behavior.

This gate selects policy only. It performs no implementation and promotes no security to READY.

**IMPLEMENTATION_AUTHORIZED = YES** for a subsequent bounded implementation gate only.

## 2. Start authority

Required and verified live main HEAD before this write stage:

`073c4c423579480a746ca6e03165c1bdcf498539`

Live main was identical to the required start HEAD. No pre-existing v0.52 package was present.

## 3. Authority-chain validation

- v0.48 runtime cache authority: validated; packaged SQLite was retrieved read-only and re-hashed to `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`, 144216064 bytes.
- v0.49 ASX-8 authority investigation: available and consistent.
- v0.50 official/licensed-source acquisition investigation: available and consistent.
- v0.51 EODHD entitlement precheck: available and consistent; acquisition remained unauthorized.
- Frozen authority: 1425 members, SHA-256 `54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb`.

Current state before and after this decision gate remains 1417 READY / 8 QUARANTINE.

## 4. Current QA-contract semantics

The repository contains two materially different layers of behavior.

### Canonical promoted core QA

`scripts/price_cache.py` defines technical validity at the bar level. O/H/L/C must be finite and positive; High must be >= Low; Close must lie inside [Low, High]; negative non-null Volume is invalid. The raw malformed observation is not rewritten.

The same core contains the promoted v0.4 filtered-bar policy. A series may remain eligible after technical filtering when:

- invalid bars <= 2;
- invalid share <= 1%;
- at least 260 valid observations remain;
- the series is not stale;
- unresolved suspicious returns do not override eligibility.

The promoted policy explicitly retains malformed raw rows in `price_daily`; the feature builder excludes them from technical calculations.

History QA v1 incorporates the same promoted filtered-bar contract.

### v0.45 Frozen remediation override

`scripts/p0_frozen_1425_price_cache_remediation_v0_45.py` added a stage-local strict-invalid test. If any strict-invalid raw bar exists, it forces `QUARANTINE / STRICT_OHLC_RELATION_FAIL` before the core filtered-bar readiness semantics can govern.

That strict override is why all eight ASX securities remain quarantined.

### Meaning of STRICT_OHLC_RELATION_FAIL

The repository evidence supports:

- **A — mandatory source-data integrity invariant:** YES at the individual raw-bar level.
- **B — provider-quality diagnostic:** YES.
- **C — intrinsic P0 computational prerequisite:** NO as a general rule. It became an upstream all-or-nothing cache gate in v0.45, but the canonical feature architecture is explicitly capable of excluding invalid bars.

Therefore `STRICT_OHLC_RELATION_FAIL` must not be interpreted as proof of security ineligibility.

## 5. ASX-8 runtime shape

Read-only inspection of the exact v0.48 packaged runtime established for each of ANZ, BSL, BXB, CBA, NXT, PME, QAN and SDF:

- raw bars: 507
- valid bars: 506
- invalid bars: 1
- invalid share: 1/507 = approximately 0.1972%
- suspicious-return events: 0
- last bar: 2026-09-22
- raw observations after 2024-11-15: 467

These facts satisfy the numeric shape of the existing isolated-invalid-bar contract. That is evidence for policy alignment and implementation authorization; it is **not** a READY promotion in this gate.

## 6. P0 field-dependency and active-lookback analysis

The historical v0.19 feature implementation is architecture evidence, not a current Frozen P0 result. v0.21 still has zero numeric P0 pass thresholds and zero promoted lane pass rules. v0.44 records current Frozen Home-Market RS and Sector RS as not verified.

For current 2026-09-22 feature position, the anomalous date is outside every explicit finite implemented lookback up to 252 observations:

- R5/R20/R60: outside
- High20/60/252 and Low20/60: outside
- SMA200: outside
- Range5/10/20: outside
- volume/turnover/RVOL20: outside
- return volatility and impulse windows <=20: outside

However EMA20, EMA50 and ATR14 are recursive EWMs with no finite cutoff. Whole-row exclusion changes the valid-history sequence and, for ATR, also changes the following valid observation's previous-close adjacency. Their current values therefore retain a deterministic decaying dependence on the filtered-history sequence.

This is why Policy C cannot be adopted literally as "wait until the defect is outside every active lookback": for the implemented recursive descriptors that condition never becomes mathematically exact.

The important safety point is different: the challenged raw High/Low/Close/Volume values are not consumed when the bar is excluded.

## 7. Close / range / volume trust

The evidence does support field distinctions as provenance:

- PME: independent complete secondary evidence strongly corroborates Close and indicates challenged High and Volume are inconsistent.
- CBA: an independent observed transaction at 155.13 corroborates the challenged Close and exceeds the challenged High.
- QAN: independent 8.89 Close corroboration.
- ANZ, BSL, BXB, NXT, SDF: no sufficient independent field-level authority establishes which member of the inconsistent relation is correct.

Therefore `CLOSE_UNTRUSTED`, `RANGE_FIELD_UNTRUSTED`, `VOLUME_UNTRUSTED`, `FULL_BAR_UNTRUSTED` and positive corroboration can be useful **evidence metadata**.

They are not yet safe selectors for partial-field feature consumption. The current feature architecture uses a whole-bar validity mask, and field-level authority is incomplete for five of eight cases.

Policy F therefore excludes the whole challenged bar. It does not rely on the convenience of assuming Close is correct.

## 8. Policy A — permanent security quarantine

Not selected.

It is maximally fail-closed but conflates a bounded source-row defect with security-level ineligibility, conflicts with the already-promoted filtered-bar QA architecture, and allows one provider defect to shrink Frozen indefinitely.

## 9. Policy B — source-defect / field-level quarantine

Architecturally useful but not selected for immediate implementation.

A true field-aware path would require a versioned dependency graph and field-specific feature masks. The repository does not currently implement that architecture, and field trust is not sufficiently established for all eight.

The selected Policy F may persist field-trust metadata for audit but does not use it to selectively consume raw fields.

## 10. Policy C — window-expiring field quarantine

Not selected.

It works conceptually for finite windows, but EMA20, EMA50 and ATR14 are recursive. There is no exact point at which the historical filtered-sequence dependency disappears for all implemented features.

## 11. Policy D — security-level READY with warning

Not selected as stated.

A warning without enforced exclusion can silently expose invalid raw data to technical features. If the warning is combined with hard whole-bar exclusion and canonical fail-closed thresholds, it becomes the selected Policy F rather than a warning-only policy.

## 12. Policy E — provider/date exception

Rejected.

No ticker, ASX-8 list, provider or 2024-11-15 hard-coded bypass is permitted. The incident is a validation case, not a special exception.

## 13. Policy F — selected generic architecture

**Selected.**

Policy F is not a new tolerance chosen to make the ASX-8 pass. It aligns the Frozen P0 price-cache path with an already-promoted generic QA contract:

1. Raw provider observations remain immutable.
2. A source-data defect remains permanently auditable until corrected or disproven.
3. A technically invalid bar is excluded as a whole from technical inputs.
4. Existing promoted filterability limits remain unchanged.
5. Suspicious returns, staleness, insufficient history, excessive invalid count/share, identity conflicts and other higher-priority gates remain fail-closed.
6. No field is fabricated, widened, clipped, interpolated or substituted.
7. No secondary source is relabeled as official.
8. No security/date/provider special case is allowed.
9. A later implementation gate must validate the entire affected cache behavior before any READY state changes.

## 14. History / Liquidity interaction

### History QA v1

**NO REOPEN.**

History QA v1 already carries the promoted filtered-bar thresholds and has been independently execution-validated. Policy F is compatible with that authority and changes none of its thresholds.

### Liquidity QA v1

**NO REOPEN.**

Liquidity QA v1 is a separate validated layer with its own session/turnover/FX evidence. This policy decision changes no liquidity evidence, thresholds, status or FX rule.

## 15. Proposed source-defect state model

The later implementation should preserve two separate dimensions:

- source evidence state: e.g. `SOURCE_DATA_DEFECT` plus optional field-trust metadata;
- technical-use/cache state: whole-bar exclusion plus canonical READY/QUARANTINE/STALE/WARMUP decision.

Suggested semantics are recorded in `output_p0_asx_ohlc_source_policy_v0_52/source_defect_state_model_v0.52.csv`.

The field-trust metadata is audit evidence only unless a later separately authorized field-aware architecture is validated.

## 16. Policy decision

**POLICY_SELECTED_FOR_IMPLEMENTATION**

Selected:

`POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT`

No thresholds are changed.

## 17. Implementation authorization

**IMPLEMENTATION_AUTHORIZED = YES**

This means only that a subsequent bounded implementation gate may:

- add/normalize generic source-defect provenance;
- align Frozen P0 cache classification with the existing promoted filtered-bar QA contract;
- validate full affected behavior and expected state changes.

It does not authorize this gate to make the eight READY.

## 18. Current state after v0.52

Unchanged:

- READY = 1417
- QUARANTINE = 8
- TOTAL = 1425
- P0_PRICE_CACHE_READY = NO
- runtime SQLite SHA-256 = `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`
- Frozen SHA-256 = `54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb`

No cache mutation. No Frozen mutation. No provider-mapping mutation.

## 19. Provider / execution calls

- new market-data provider calls: 0
- Alpha Vantage calls: 0
- Scalable calls: 0
- P0 runs: 0
- feature materializations: 0
- RS runs/promotions: 0
- parameter promotions: 0
- productive: false

The existing v0.48 Actions artifact was retrieved only to inspect and re-hash the already-authoritative runtime bytes read-only. This was not a market-data provider acquisition.

## 20. Next gate

**BOUNDED IMPLEMENTATION GATE FOR POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT**

The next gate must remain generic and must not contain an `if ticker in ASX8` or `if date == 2024-11-15` bypass.

Do not execute automatically.

## 21. Hard stop

STOP after this decision package.

No policy implementation. No cache mutation. No READY promotion. No P0. No feature materialization. No RS. No parameter promotion. No Universe mutation. No trading.
