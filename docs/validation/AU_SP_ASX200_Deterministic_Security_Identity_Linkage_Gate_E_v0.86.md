# AU_SP_ASX200 Deterministic Security Identity Linkage Gate E v0.86

## Verdict
**PASS_AU_SP_ASX200_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_GATE_E**

AU_DETERMINISTIC_SECURITY_IDENTITY_LINKAGE_READY = **YES**.
FROZEN TARGET = **63**.
CURRENT ASX DIRECTORY ROWS = **1833**.
CURRENT DISTINCT ASX CODES = **1833**.
FROZEN SOURCE-WS-ID CONTRACT = **PASS**.
EXACT TICKER LINKS = **63**.
SOURCE-WS-ID EQUALITY = **63**.
NOT_FOUND = **0**.
AMBIGUOUS = **0**.
NOT_VERIFIED = **0**.
CONFLICT = **0**.
COMPANY-NAME LINKAGE = **0**.
TICKER-CHANGE INFERENCE = **0**.

## Scope
Identity only. The Frozen physical file has no Primary_Universe_Index column; the cohort label was taken from the already-governed exact Security_Key capability sidecar while all identity fields remained sourced from Frozen. One fresh official ASX directory CSV snapshot was used. No company-name linkage, fuzzy matching, ticker-change inference, per-security fanout, classification coverage, GICS-code attachment, PDSC, Gate F/H, canonical materialization, other cohort, Sector RS or P0/P1/P2 was executed.

## Blocker
**NONE**.

## Artifact binding
- Workflow run: 36388443082
- Workflow head: 7eb12ecfa5b4ce3769bda8548c65469662ffd507
- Artifact: 10955208258
- Artifact digest: sha256:b9f68ee805db5725db95b0c3d397e8b8fcf0a9759d7814ff3edf169c0ce46f03

## Next gate
**AU_SP_ASX200 EXACT FROZEN GICS INDUSTRY-GROUP CLASSIFICATION COVERAGE GATE F**

Hard stop applied.
