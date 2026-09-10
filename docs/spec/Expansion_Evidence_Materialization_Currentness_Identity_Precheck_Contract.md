# Expansion Evidence Materialization, Currentness & Identity Precheck Contract

## 1. Purpose

This document is the normative, population-independent governance contract that MUST be applied before any new population-specific Admission Policy Gate in WELT-SWING LONG DEV.

Its purpose is to prevent region-specific policy/evidence loops from starting before the candidate population has demonstrated a sufficiently reproducible, current, security-level, batch-capable evidence architecture with deterministic primary-listing and identity semantics.

This stage is SPEC ONLY. It performs no source hunt, no evidence acquisition, no population materialization, no candidate generation, no admission, no implementation and no Universe write.

**Stage result: PASS**

**NEXT AUTHORIZED STAGE: Post-Precheck-Contract Next-Population Manager Gate — READ-ONLY**

## 2. Scope

The contract applies prospectively to every new population candidate before a population-specific Admission Policy Gate.

It MUST NOT automatically reactivate or modify any parked population. Canada, Korea, US-3, Brazil and Taiwan remain PARKED. Any future reactivation requires a separately authorized Manager Gate.

The contract supplements existing population, identity, admission and U3K governance. It does not overwrite prior specifications, historical evidence or productive Welt-Swing v7.2.

## 3. Governance position

Repository: `akx0801-hub/welt-swing-long-data`

Branch: `main`

Start HEAD: `3d3f3c91c648b348bb3abf65d632f2f0175633af`

Verified start commit: `Post-Taiwan next population manager gate`

Authorized stage: `Expansion Evidence Materialization, Currentness & Identity Precheck Contract Gate — READ-ONLY / SPEC ONLY`

Productive trading authority remains exclusively Welt-Swing v7.2. WELT-SWING LONG DEV remains DEV / RESEARCH / SHADOW and MUST NOT be treated as productive authority.

Baseline MUST remain unchanged:

| Measure | State |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| US-1 | 372 |
| US-2 | 369 |
| US Total | 741 |
| AU-1 | 153 |
| Usable Integrated Expansion Rows | 894 |
| Canada | PARKED |
| Korea | PARKED |
| US-3 | PARKED |
| Brazil | PARKED |
| Taiwan | PARKED |

Research Partial is a workbench/research state. Strict is an Eligibility dry-run diagnostic. Strict is NOT U3K or Membership. Frozen MUST remain 0 unless separately and explicitly authorized. Membership != Eligibility != Scan != Execution.

Alpha Vantage MUST NOT be used.

## 4. Failure-mode background

This contract is required because the repository records a systemic evidence-governance gap across five parked populations.

### Canada

Failure mode: security-level identity / ISIN recovery did not scale and drifted toward per-security recovery.

Contract response: P9, P13, P15, P16 and P17 MUST block populations whose identity completion depends on broad manual security-by-security recovery.

### Korea

Failure mode: institutional population/listing/identity evidence could not be reproducibly materialized at row level.

Contract response: P2, P3, P5 and P14 MUST be proven before policy progression.

### US-3

Failure mode: a conceptually suitable named-index tracker failed at reproducible raw snapshot materialization/sealing.

Contract response: P3 and P4 are hard gates; theoretical dataset suitability is insufficient.

### Brazil

Failure mode: strong official exchange architecture existed, but the decisive security-level instrument/ISIN evidence path could not be reproducibly materialized and linked row-by-row.

Contract response: P3, P8, P9 and P14 MUST be demonstrated before population policy work begins.

### Taiwan

Failure mode: historical population and identity architecture was strong, but current security-level membership and identity currentness could not be reproducibly validated.

Contract response: P5 and P12 are hard gates; historical plausibility MUST NOT substitute for currentness evidence.

## 5. Precheck placement in stage sequence

The mandatory stage sequence is:

1. A Manager Gate identifies one exact population candidate.
2. An Expansion Evidence Precheck evaluates P0-P18 under this contract.
3. Only if `PRECHECK RESULT: READY` may the population proceed to a population-specific Admission Policy Gate.
4. Population-specific validation/build stages may follow only under separate explicit authorization.
5. Controlled integration write may occur only after a successful Admission Build and a separately authorized write stage.

The precheck MUST NOT be skipped.

## 6. P0-P18 normative contract

### P0 — Population Boundary

Status: `PASS` / `FAIL`.

PASS requires all of the following to be explicitly documented:

- exact index or population;
- expected population size or tightly defined size range;
- primary market(s);
- primary MIC(s);
- security-level boundary;
- included instrument types;
- excluded instrument types;
- source lineage.

If the population boundary is ambiguous, P0 MUST be `FAIL` and the precheck MUST be `BLOCKED`.

### P1 — Population Authority

Status: `STRONG` / `CONDITIONAL` / `WEAK`.

`STRONG` means an official index administrator, primary exchange, regulator, official market infrastructure or already repository-qualified equivalent provides the governing population authority.

`CONDITIONAL` is permitted only when the authority limitation is explicit and all downstream hard gates remain independently demonstrable.

`WEAK` MUST block progression.

### P2 — Security-Level Population Evidence

Status: `PASS` / `FAIL`.

PASS requires complete security-level evidence for the governed population boundary.

The following MUST NOT satisfy P2 by themselves:

- index description;
- factsheet without complete constituents;
- marketing page;
- top holdings;
- issuer-level list;
- aggregate statistics;
- constituent count without rows.

P2 `FAIL` MUST block the Admission Policy Gate.

### P3 — Materialization Reproducibility

Status: `PASS` / `FAIL`.

P3 is a HARD GATE.

PASS requires a concrete evidence source and retrieval path for which the precheck can establish:

- exact source identity;
- exact retrieval method;
- raw snapshot is materializable;
- deterministic or bounded reproducible retrieval;
- reproducible extraction path;
- stable schema or deterministic schema-handling contract;
- no manual copy/paste dependency;
- batch-level acquisition.

Dataset existence without reproducible materialization MUST be `FAIL`.

P3 `FAIL` MUST set `PRECHECK RESULT: BLOCKED`.

### P4 — Snapshot Integrity

Status: `PASS` / `FAIL`.

The evidence architecture MUST support, for the later concrete snapshot:

- retrieval timestamp;
- source as-of date or explicit current-state marker;
- raw file/path or governed pointer;
- SHA256 or equivalent repository-approved content hash;
- raw row count;
- normalized row count;
- schema inventory;
- parsing notes;
- deterministic rerun description.

This contract does not create snapshots. It requires the architecture to support those fields before policy progression.

If snapshot integrity cannot be established, P4 MUST be `FAIL`.

### P5 — Currentness

Currentness Status MUST be exactly one of:

- `CURRENT`
- `STALE-BUT-RECONCILABLE`
- `STALE-NOT-RECONCILABLE`

Currentness Evidence status: `PASS` / `FAIL`.

PASS requires:

- explicit as-of date or authoritative current-state evidence;
- documented source publication/review cadence where relevant;
- current membership testability;
- current listing testability;
- corporate-action awareness;
- stale-snapshot detection;
- deterministic change reconciliation when stale.

A snapshot MUST NOT pass or fail solely because of calendar age. Age MUST be interpreted against index turnover, source cadence, currentness confirmation and deterministic reconciliation capability.

Only `CURRENT` or `STALE-BUT-RECONCILABLE` may receive Currentness Evidence `PASS`.

`STALE-NOT-RECONCILABLE` MUST set Currentness Evidence `FAIL` and block progression.

Historical plausibility alone MUST NOT satisfy P5.

### P6 — Primary Listing / MIC

Status: `PASS` / `FAIL`.

PASS requires:

- primary market known;
- primary MIC known;
- ADR/GDR/secondary/OTC representations excluded or explicitly separated;
- multi-market securities deterministically handled;
- broker/vendor ticker not treated as canonical identity.

P6 `FAIL` MUST block progression.

### P7 — Local Security Code / Primary Ticker

Status: `PASS` / `FAIL`.

A deterministic security-level join key MUST exist, such as:

- local security code;
- primary ticker;
- exchange instrument code;
- another explicitly governance-approved exact security-level identifier.

Issuer name alone MUST NOT satisfy P7.

Fuzzy ticker substitution MUST NOT be used.

### P8 — Security Identity

Status: `PASS` / `FAIL`.

Canonical security identity MUST be represented as:

`ISIN + Primary MIC + Primary Ticker/Local Security Code + Exact Security Name + Exact Share Class`

Where ISIN coverage is incomplete, P8 and P9 MUST remain distinct: an otherwise deterministic identity architecture may pass P8 only if the missing ISINs are explicitly quantified and P9 is not WEAK.

Issuer-level substitutes, fuzzy-name identity, guessed MICs, guessed ISINs, silent share-class substitution and silent ADR/local substitution MUST NOT be used.

### P9 — ISIN Capability

Status: `STRONG` / `CONDITIONAL` / `WEAK`.

`STRONG` requires batch-capable security-level ISIN evidence with high expected population coverage.

`CONDITIONAL` requires all of the following:

- gaps are isolated and quantified;
- gaps are a minority of the population;
- gaps can fail closed in a later build;
- no broad manual recovery is required;
- no synthetic or inferred ISIN is used.

`WEAK` applies if the population has a systemic ISIN gap, security-level ISIN evidence is unavailable, or progression would require broad security-by-security recovery.

P9 `WEAK` MUST block progression.

No automatic ISIN-recovery cascade is permitted.

### P10 — Share-Class Fidelity

Status: `PASS` / `FAIL`.

PASS requires exact security-class semantics sufficient to prevent:

- issuer-level merging;
- ordinary/preferred substitution;
- ADR/local substitution;
- unit/common substitution;
- silent multiple-class collapse.

Share-class uncertainty that can change canonical security identity MUST be `FAIL`.

### P11 — Instrument Classification

Status: `PASS` / `FAIL`.

The evidence architecture MUST distinguish at least:

- Ordinary / Common;
- Preferred;
- REIT;
- Unit;
- ETF;
- Fund;
- ADR;
- GDR;
- Depositary Receipt;
- Rights;
- Warrants;
- Structured Product;
- Debt;
- Foreign Secondary Listing;
- Unknown.

Unknown MUST remain `REVIEW / FAIL-CLOSED` at later stages and MUST NOT be auto-admitted.

P11 `PASS` requires classification capability strong enough to enforce the population's inclusion/exclusion rules without broad manual reconstruction.

### P12 — Corporate-Action Visibility

Status: `PASS` / `FAIL`.

The evidence architecture MUST make identity-relevant changes detectable, including:

- ticker/code change;
- name change;
- share-class change;
- merger;
- spin-off;
- delisting;
- relisting;
- exchange move;
- identifier change;
- index replacement.

Full automatic resolution is not required. Visibility and fail-closed treatment are required.

If currentness cannot distinguish continuity from identity break, P12 MUST be `FAIL` and P5 MUST NOT pass.

No automatic successor mapping is permitted without explicit authoritative continuity evidence.

### P13 — Batch Capability

Status: `PASS` / `FAIL`.

PASS requires the central evidence path to process the governed population in a batch-capable, reproducible process.

Security-by-security research MUST NOT be the primary path.

If the central evidence architecture requires broad per-security lookup, P13 MUST be `FAIL`.

### P14 — Row-Level Reproducibility

Status: `PASS` / `FAIL`.

Every normalized security row MUST be deterministically traceable to raw evidence or a governed repository-approved evidence pointer.

Required:

- deterministic row key;
- deterministic parsing/mapping rule;
- traceable source reference;
- no unlogged manual mapping;
- reproducible identity linkage.

P14 `FAIL` MUST block progression.

### P15 — Manual Recovery Threshold

Status: `LOW` / `MEDIUM` / `HIGH`.

`LOW`: only trivial or no manual residual; progression permitted if all hard gates pass.

`MEDIUM`: permitted only if the residual is isolated, quantified, non-systemic, fail-closed, and does not require security-by-security completion to unlock the rest of the population.

`HIGH`: broad manual recovery, issuer-by-issuer recovery, security-by-security identity/ISIN/currentness recovery, or an unbounded exception queue.

P15 `HIGH` MUST block progression.

### P16 — Scalability

Status: `YES` / `LIMITED` / `NO`.

`YES`: the evidence and identity process scales to the governed population through deterministic batch operations.

`LIMITED`: allowed only if the limitation is explicitly bounded, does not create high manual recovery, and all hard gates pass.

`NO`: MUST block progression.

### P17 — Failure-Loop Risk

Each precheck MUST rate:

- Canada-Type Risk: `LOW` / `MEDIUM` / `HIGH`
- Korea-Type Risk: `LOW` / `MEDIUM` / `HIGH`
- US-3-Type Risk: `LOW` / `MEDIUM` / `HIGH`
- Brazil-Type Risk: `LOW` / `MEDIUM` / `HIGH`
- Taiwan-Type Risk: `LOW` / `MEDIUM` / `HIGH`
- Overall Failure-Loop Risk: `LOW` / `MEDIUM` / `HIGH`

The ratings MUST be evidence-based and tied to the concrete candidate architecture.

Overall Failure-Loop Risk `HIGH` MUST block progression.

### P18 — Policy-Gate Readiness

The only valid precheck result values are:

- `READY`
- `BLOCKED`

No `CONDITIONAL PASS`, `SOFT PASS` or `PROVISIONAL READY` is permitted.

`READY` is allowed only if every hard gate passes and all threshold rules are satisfied.

Otherwise the result MUST be `BLOCKED`.

## 7. Hard gates

A population MUST NOT proceed to an Admission Policy Gate unless all of the following are true:

- Population Boundary = PASS
- Population Authority != WEAK
- Security-Level Population Evidence = PASS
- Materialization Reproducibility = PASS
- Snapshot Integrity Architecture = PASS
- Currentness Evidence = PASS
- Currentness Status is CURRENT or STALE-BUT-RECONCILABLE
- Primary Listing Architecture = PASS
- Local Security-Code Capability = PASS
- Security Identity Architecture = PASS
- ISIN Capability != WEAK
- Share-Class Fidelity = PASS
- Instrument Classification = PASS
- Corporate Action Visibility = PASS
- Batch Capability = PASS
- Row-Level Reproducibility = PASS
- Manual Recovery != HIGH
- Scalability != NO
- Overall Failure-Loop Risk != HIGH

If any condition is not met, the precheck MUST return `BLOCKED`.

## 8. READY criteria

`PRECHECK RESULT: READY` means only that the population has cleared this evidence-governance precondition and may enter a separately authorized population-specific Admission Policy Gate.

READY MUST NOT mean:

- admitted;
- Member;
- Strict;
- Frozen;
- scan eligible;
- execution eligible;
- productive.

READY MUST NOT cause any population, Membership, Research Partial, Strict, Frozen or Universe write.

## 9. BLOCKED criteria

`PRECHECK RESULT: BLOCKED` is mandatory if any hard gate fails, any required status is unresolved, or progression would depend on generic source hunting, broad manual recovery or an unbounded exception process.

BLOCKED means:

- no Admission Policy Gate;
- no Population Build;
- no Candidate Generation;
- no Universe write;
- no region-specific recovery loop.

A Manager Gate MUST then choose exactly one of:

A. authorize one bounded evidence qualification path; or
B. PARK the population.

## 10. Currentness contract

Currentness MUST be demonstrated at security level for the governed population.

The currentness architecture MUST support deterministic reconciliation of:

- retained members;
- removed members;
- incoming members;
- listing status;
- local code changes;
- share-class changes;
- identity-relevant corporate actions.

A stale snapshot may proceed only as `STALE-BUT-RECONCILABLE` when the repository can deterministically reconcile the delta using an authorized evidence mechanism. Otherwise it MUST be `STALE-NOT-RECONCILABLE` and BLOCKED.

## 11. Identity / ISIN contract

Identity is security-level, never issuer-level.

The canonical target tuple SHALL be:

`ISIN + Primary MIC + Primary Ticker/Local Security Code + Exact Security Name + Exact Share Class`.

Missing ISINs MAY be tolerated only under P9 `CONDITIONAL` where the residual is isolated, quantified, non-systemic and fail-closed.

Systemic missing ISINs MUST be `WEAK` and BLOCKED.

No guessed, synthetic, issuer-level, wrong-class, ADR/GDR-substitute or silently inherited ISIN is permitted.

## 12. Share-class / instrument contract

Share class and instrument type MUST be explicit enough to enforce inclusion/exclusion rules without issuer-level inference.

Different valid classes MUST remain distinct securities. Preferred, units, ADR/GDR, funds, ETFs, debt, rights, warrants, structured products and foreign secondary listings MUST NOT be silently substituted for local Ordinary/Common shares.

Unknown classification MUST remain fail-closed.

## 13. Materialization contract

Every future precheck MUST identify the exact intended source path before policy progression.

The path MUST specify:

- provider/authority;
- dataset/product/file/endpoint identity;
- retrieval mechanism;
- expected security-level granularity;
- expected population coverage;
- expected schema;
- expected batch capability;
- expected reproducibility;
- exact problem the path solves.

A URL, provider name or statement that a dataset "exists" is insufficient.

No manual copy/paste primary materialization is permitted.

## 14. Raw snapshot integrity contract

The concrete later evidence snapshot MUST be capable of being sealed with:

- retrieval timestamp;
- source as-of/current-state metadata;
- raw path or governed pointer;
- SHA256 or approved equivalent;
- raw row count;
- normalized row count;
- schema inventory;
- parser/version or deterministic parsing note;
- deterministic rerun description.

If the evidence cannot be preserved directly for licensing/governance reasons, the repository MUST use an already-approved pointer/metadata/hash convention sufficient to reproduce and audit the result. A non-reproducible citation or manual transcription MUST NOT substitute for raw-integrity evidence.

## 15. Row-level reproducibility contract

For every normalized row, the later evidence process MUST retain deterministic lineage to the exact raw record or governed evidence reference.

The row lineage MUST make it possible to audit at least:

- source row/reference;
- local security code;
- primary MIC;
- exact security name;
- share class;
- ISIN when present;
- normalization/mapping transformation;
- currentness/corporate-action interpretation.

Unlogged manual mapping MUST NOT be used.

## 16. Batch / scalability contract

The central evidence path MUST be batch-capable for the full governed population boundary.

Residual manual handling MAY exist only when P15 is LOW or narrowly MEDIUM. It MUST NOT be the principal mechanism for population identity, currentness, listing or ISIN completion.

A population that can only be completed through broad security-by-security research MUST be BLOCKED.

## 17. Manual recovery threshold

Manual recovery MUST be measured before policy progression.

The precheck report MUST state:

- expected number or percentage of unresolved rows where known;
- reason class;
- whether each residual can fail closed;
- whether progression of clean rows depends on recovery;
- whether any manual queue is bounded.

If the residual is systemic, open-ended or required to establish the core population evidence, Manual Recovery MUST be HIGH and the precheck MUST be BLOCKED.

## 18. Failure-loop risk framework

The five failure-mode dimensions are mandatory diagnostics:

- Canada-Type: per-security identity/ISIN recovery risk.
- Korea-Type: population/listing/identity evidence access/materialization risk.
- US-3-Type: qualified-data-theory but raw snapshot materialization/sealing risk.
- Brazil-Type: official security/instrument dataset exists but cannot be reproducibly materialized or row-linked.
- Taiwan-Type: historical identity is strong but current population/currentness cannot be reproducibly reconciled.

The precheck MUST explain any MEDIUM or HIGH rating.

Overall Failure-Loop Risk MUST be HIGH if one unresolved failure mode is capable of forcing the population into repeated source, recovery or materialization loops.

Overall HIGH MUST block progression.

## 19. One-Path-or-Park rule

If `PRECHECK RESULT: BLOCKED`, no automatic recovery sequence is allowed.

A subsequent Manager Gate MAY authorize at most ONE bounded evidence qualification path only if the path is already concretely identified with:

- provider;
- exact dataset/product/file/endpoint;
- authority;
- expected security-level granularity;
- expected batch capability;
- expected materialization reproducibility;
- exact blocking problem solved.

If no such path exists, the population MUST be PARKED.

If the single authorized path fails, the population MUST be PARKED.

No automatic second path is permitted.

## 20. Generic source-hunt prohibition

`Generic Source Hunt: VERBOTEN`.

A blocked precheck MUST NOT trigger:

- broad web search;
- trying multiple providers;
- trying multiple wrappers around the same failed source;
- manual security-by-security research;
- free-form issuer research;
- speculative API probing;
- ETF holdings as an undeclared substitute population architecture;
- copy/paste materialization.

A new evidence path requires explicit Manager authorization and must be concrete before execution.

## 21. Standard Precheck Result Template

Every future population precheck MUST report at least:

```text
Population:
<exact>

Index / Boundary:
<exact>

Primary Market:
<exact>

Primary MIC:
<exact>

Source Lineage:
<exact>

Population Size:
<n>

Population Boundary:
PASS / FAIL

Population Authority:
STRONG / CONDITIONAL / WEAK

Security-Level Population Evidence:
PASS / FAIL

Materialization Reproducibility:
PASS / FAIL

Snapshot Integrity Architecture:
PASS / FAIL

Currentness Status:
CURRENT / STALE-BUT-RECONCILABLE / STALE-NOT-RECONCILABLE

Currentness Evidence:
PASS / FAIL

Primary Listing Architecture:
PASS / FAIL

Local Security-Code Capability:
PASS / FAIL

Security Identity Architecture:
PASS / FAIL

ISIN Capability:
STRONG / CONDITIONAL / WEAK

ISIN Coverage:
<n>/<n>

Share-Class Fidelity:
PASS / FAIL

Instrument Classification:
PASS / FAIL

Corporate Action Visibility:
PASS / FAIL

Batch Capability:
PASS / FAIL

Row-Level Reproducibility:
PASS / FAIL

Manual Recovery:
LOW / MEDIUM / HIGH

Scalability:
YES / LIMITED / NO

Canada-Type Risk:
LOW / MEDIUM / HIGH

Korea-Type Risk:
LOW / MEDIUM / HIGH

US-3-Type Risk:
LOW / MEDIUM / HIGH

Brazil-Type Risk:
LOW / MEDIUM / HIGH

Taiwan-Type Risk:
LOW / MEDIUM / HIGH

Overall Failure-Loop Risk:
LOW / MEDIUM / HIGH

PRECHECK RESULT:
READY / BLOCKED

Blocking Reasons:
<exact>
```

## 22. Legacy and parked-population handling

This contract is prospective for new population progression.

It MUST NOT change, reopen or reinterpret the parked state of Canada, Korea, US-3, Brazil or Taiwan.

A later reactivation of any parked population requires an explicit Manager Gate and MUST then comply with this precheck contract before any new Admission Policy Gate.

No historical Membership, Research Partial, Strict, Frozen or Universe state is changed by adoption of this contract.

## 23. Relationship to existing specifications

This contract is an upstream governance layer.

It SHALL NOT overwrite:

- the WELT-SWING LONG DEV master specification;
- existing population-specific admission policies;
- existing identity policies;
- existing historical evidence/audits;
- productive Welt-Swing v7.2.

Where a population-specific policy is stricter than this contract, the stricter requirement remains binding.

## 24. No-touch confirmation

This stage MUST NOT and did not modify:

- Research Partial;
- Membership;
- Universe;
- Strict;
- Frozen;
- US-1;
- US-2;
- US-3;
- AU-1;
- Canada;
- Korea;
- Brazil;
- Taiwan;
- Mapping;
- History;
- Liquidity;
- Eligibility;
- Scan/U3K;
- Welt-Swing v7.2.

No script, validator, schema, CI workflow, source registry, source materialization, population build, evidence snapshot, ISIN recovery, candidate population or admission artifact is created by this stage.

## 25. Quality gates G0-G17

- G0 Start HEAD correct — PASS.
- G1 Correct authorized stage — PASS.
- G2 Baseline correct — PASS.
- G3 Five parked states unchanged — PASS.
- G4 All five failure modes incorporated — PASS.
- G5 Precheck contract population-independent — PASS.
- G6 P0-P18 defined — PASS.
- G7 Hard gates explicitly defined — PASS.
- G8 Materialization reproducibility is a hard gate — PASS.
- G9 Currentness is a hard gate — PASS.
- G10 Security Identity / ISIN rules explicit — PASS.
- G11 Batch / row-level reproducibility explicit — PASS.
- G12 Manual recovery threshold explicit — PASS.
- G13 One-Path-or-Park explicit — PASS.
- G14 Generic Source Hunt prohibited — PASS.
- G15 READY/BLOCKED semantics exact — PASS.
- G16 Only this spec report intended as write — PASS.
- G17 No follow-on stage executed — PASS.

**G0-G17: PASS**

## 26. Contract decision

**Systemic Gap Addressed: YES**

**Contract Population-Independent: YES**

**Precheck Placement Defined: YES**

**P0-P18 Defined: YES**

**Materialization Hard Gate: YES**

**Snapshot Integrity Contract: YES**

**Currentness Hard Gate: YES**

**Primary Listing Hard Gate: YES**

**Security Identity Hard Gate: YES**

**ISIN Weak Blocks Progression: YES**

**Share-Class Hard Gate: YES**

**Instrument Classification Hard Gate: YES**

**Corporate Action Visibility Required: YES**

**Batch Capability Hard Gate: YES**

**Row-Level Reproducibility Hard Gate: YES**

**Manual Recovery Threshold Defined: YES**

**Scalability Rule Defined: YES**

**Failure-Loop Risk Framework Defined: YES**

**One-Path-or-Park Rule Defined: YES**

**Generic Source Hunt Prohibited: YES**

**PRECHECK RESULT values: READY / BLOCKED**

**Admission Policy Gate Requires Precheck READY: YES**

## 27. Exact next authorized stage

**Post-Precheck-Contract Next-Population Manager Gate — READ-ONLY**

That Manager Gate must choose which remaining non-parked repository-documented population, if any, is first subjected to this new Expansion Evidence Precheck. It MUST NOT automatically execute the population precheck itself unless separately authorized.

HARD STOP after this contract stage and its commit verification.
