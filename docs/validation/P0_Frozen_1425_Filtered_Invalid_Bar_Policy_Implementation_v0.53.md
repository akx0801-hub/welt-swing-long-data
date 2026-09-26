# P0 Frozen-1425 Canonical Filtered-Invalid-Bar Policy F - Implementation / Regression v0.53

## 1. Implementation verdict

**PASS**

POLICY_F_CANONICAL_FILTERED_INVALID_BAR_SOURCE_DEFECT is implemented for the Frozen-1425 runtime path using the existing canonical QA v0.4 / History QA v1 filtered-bar contract. No ASX/ticker/date/provider exception is present in the implementation.

## 2. Start head

Required start authority: b8b9178385c58351910b2e61fe1f473d4f47af18. The first implementation commit was created directly from that HEAD. Subsequent harness-only repair commits remained descendants of the same required authority.

## 3. Authority-chain validation

- v0.48 runtime authority: validated exactly before implementation.
- v0.49 ASX authority investigation: retained.
- v0.50 licensed-source investigation: retained.
- v0.51 entitlement precheck: retained.
- v0.52 policy decision: retained and consumed as validation-case authority only.

## 4. Canonical contract binding

- max invalid bars: 2
- max invalid share: 1.00%
- minimum valid observations after filtering: 260
- core minimum valid bars: 252
- stale threshold: 10 calendar days
- unresolved suspicious returns remain blocking; existing evidence-verified reconciliations remain authoritative.
- threshold changes: 0.

## 5. Code change

The implementation reuses qa_symbol_frame() and technical_valid_mask() from scripts/price_cache.py. It does not create a second threshold engine. The old v0.45 any-strict-invalid whole-security quarantine behavior is no longer the effective Frozen runtime classification. Invalid bars remain raw, are excluded completely from technical inputs, and canonical gates determine readiness.

The runtime adds generic provenance tables cache_qa_provenance_v053 and technical_bar_exclusions_v053. No price_daily value is edited.

## 6. Full Frozen-1425 regression

- Frozen rows evaluated: 1425
- READY -> READY: 1417
- READY -> QUARANTINE: 0
- READY -> other: 0
- QUARANTINE -> READY: 8
- final READY: 1425
- final QUARANTINE: 0

No hidden additional blocker was exposed by the generic full-population pass.

## 7. ASX-8 validation case

- ANZ: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- BSL: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- BXB: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- CBA: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- NXT: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- PME: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- QAN: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.
- SDF: raw 507, valid 506, invalid 1, invalid share 0.19724%, affected date 2024-11-15, result PASS, final reason ISOLATED_INVALID_BAR_EXCLUDED.

These rows were discovered from v0.52 validation evidence and re-derived from runtime data. They are not hard-coded pass conditions.

## 8. Raw price immutability

- price_daily rows before/after: 711204 / 711204
- deterministic content digest before/after: 1c4f93c2ca5fb3a79e859b359cc3a192dc19187f6745ee5e458a6f3569d84aea
- raw-price digest unchanged: YES
- provider mapping digest unchanged: YES

## 9. Defect provenance

- security-level provenance rows: 1425
- SOURCE_DATA_DEFECT=true securities: 8
- TECHNICAL_BAR_EXCLUDED rows: 8
- affected dates, reasons and policy identifiers are persisted explicitly.

READY therefore does not erase the source defect.

## 10. Feature-path regression

Fixture regression proved that the raw invalid row remains present while it is absent from feature input; EMA20/EMA50, ATR14, rolling High/Low, returns, Volume and Turnover all consume the filtered valid-bar series.

## 11. Recursive EMA / ATR semantics

EMA20, EMA50 and ATR14 are DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES. They are not described as unaffected: omission of an invalid historical observation changes the recursive filtered sequence.

## 12. Boundary test results

- 2 invalid bars: PASS boundary.
- 3 invalid bars: fail closed.
- invalid-share == 1% predicate: inclusive PASS; a joint READY fixture at exactly 1% is mathematically impossible under <=2 invalid bars plus >=260 valid observations, and this interaction is explicitly recorded.
- invalid share >1% predicate: fail.
- exactly 260 valid after filtering: PASS.
- 259 valid after filtering: fail.

## 13. Negative test results

Fail-closed cases passed for 3 invalid bars, >1% share predicate, 259 valid, stale history, unresolved suspicious return, higher-priority blocker and multiple simultaneous blockers.

## 14. Existing 1417 READY reconciliation

1417 READY -> 1417 READY. Zero degradations. Existing evidence-verified extreme-return / 522 reconciliation states remain READY under their prior authority.

## 15. State transitions

- ANZ: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- BSL: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- BXB: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- CBA: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- NXT: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- PME: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- QAN: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.
- SDF: QUARANTINE/STRICT_OHLC_RELATION_FAIL -> READY/ISOLATED_INVALID_BAR_EXCLUDED; complete invalid bar remains excluded and provenance retained.

## 16. Final cache counts

- READY = 1425
- QUARANTINE = 0
- TOTAL = 1425

## 17. P0_PRICE_CACHE_READY

**YES** - price-cache readiness only. This does not authorize P0 execution; feature/RS/parameter gates remain separate.

## 18. Runtime SQLite authority

- workflow run: 36225840648
- artifact: 10900287789
- artifact digest: sha256:f54f1520e6cfcefbca043bc782ccf71ddd0e70538722ee1c3857551396761e95
- SQLite SHA-256: bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc
- bytes: 144539648
- PRAGMA integrity_check: ok
- states: 1425
- price_daily: 711204

## 19. Byte-binding result

PASS. Declared SHA equals packaged/retrieved SHA; declared byte count equals packaged/retrieved byte count. Hashing occurs only after transaction commit, WAL checkpoint and connection close. The permanent lifecycle regression also passed.

## 20. Frozen reconciliation

- Frozen members: 1425
- Frozen SHA-256: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb
- Security_Key / Source_WS_ID / Primary_Ticker / Primary_MIC unchanged.

## 21. History / Liquidity confirmation

- History QA v1: NOT REOPENED
- Liquidity QA v1: NOT REOPENED
- threshold changes: 0

## 22-24. Provider call counts

- market-data provider calls: 0
- Yahoo/yfinance calls: 0
- EODHD calls: 0
- Alpha Vantage calls: 0
- Scalable calls: 0

## 25. Test results

Focused pytest suite: PASS. Persisted regression matrix: 29/29 PASS. Successful Actions run completed every implementation, full-regression, byte-lifecycle, validation and artifact-upload step.

Two earlier harness attempts failed closed before runtime mutation/upload: run 36225649682 (self-test scanner) and run 36225753186 (shallow-history precondition). They created no runtime authority.

## 26. Files

Implementation code/workflows/tests plus the bounded v0.53 validation report and output package are persisted. Runtime SQLite remains an Actions artifact and is not committed.

## 27. Commit

The final evidence-persistence commit is created only after all packaged-byte checks pass.

## 28. Next gate

**P0 FROZEN-1425 FEATURE MATERIALIZATION / CAPABILITY GATE**

Do not run P0 automatically.

## Hard stop

No P0/P1/P2. No feature materialization beyond regression fixtures. No RS materialization. No parameter promotion. No Universe mutation. No Scalable. No trading.
