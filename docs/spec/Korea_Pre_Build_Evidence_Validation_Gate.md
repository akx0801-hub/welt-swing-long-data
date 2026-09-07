# Korea Pre-Build Evidence Validation Gate

## Stage decision

**KOREA PRE-BUILD EVIDENCE VALIDATION GATE — PASS**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Post-Korea Evidence Validation Manager Gate — READ-ONLY**

PASS means the bounded validation was completed and documented. It does not mean Korea is build-authorized.

## 1. Start and authorization

- Repository: akx0801-hub/welt-swing-long-data
- Branch: main
- Start HEAD: f32e0d00f507380069636adf37304f9c647fcf3a
- origin/main at startcheck: f32e0d00f507380069636adf37304f9c647fcf3a
- Commit verified: Korea admission policy gate
- Authorized stage: Korea Pre-Build Evidence Validation Gate — READ-ONLY / SIDECAR ONLY
- No newer completed validation gate was present at startcheck.

## 2. Governance and baseline

| Measure | Value |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| Canada | PARKED |
| Korea existing coverage | 0 |
| Korea population policy | KOSPI 200 |
| Primary market | KOSPI |
| Primary MIC policy | XKRX |
| Primary ticker policy | official six-digit zero-padded KRX security code |
| Build authorization at start | NOT AUTHORIZED |

Welt-Swing v7.2 remains the only productive Trading Authority. WELT-SWING LONG DEV remains DEV / RESEARCH / SHADOW. Membership, identity, eligibility, scan and execution remain separate. No ticker-only, issuer-only, local-code-only or CUSIP-as-ISIN identity was accepted. Alpha Vantage was not used.

## 3. Selection rule and frozen sample

The existing 200-row repository snapshot was read-only reference material. It is explicitly not current membership evidence because its lineage is `KR_KOSPI200_WIKI` and its notes say identity/provider mapping is pending.

The sample was frozen before evidence work by deduplicating on six-digit local code, sorting ascending, and selecting ranks round(i*(N-1)/11) for i=0..11. The 12 selected codes are:

`000080, 001800, 005380, 008770, 011790, 026960, 039490, 069620, 105560, 207940, 302440, 483650`.

Selection timestamp: 2026-09-07T05:38:59Z. Selection SHA256: eb46c9992faa5603de34f279356aee4756409d575de55f22a60b6893ddcf9a5d. No replacement, refill or second sample was performed.

## 4. KRX and KSD access tests

The official KRX landing page was reachable, but the row-level KRX endpoint path was not operationally reproducible in the available runner evidence. Existing repository tests recorded HTTP 403 on one official row-level request and HTTP 400 on a later official endpoint retry, both with zero parsed rows. The official landing response alone contains no validated row-level membership or listing proof.

- KRX Population Access: FAIL
- KRX Listing Access: FAIL
- KSD Access: CONDITIONAL
- KSD ISIN Capability: CONDITIONAL
- Security Identity Capability: FAIL

No credentials, login bypass, CAPTCHA bypass or other protection circumvention was attempted. The KSD authority is identified, but a public reproducible row-level security/class/ISIN path was not proven in this gate.

## 5. Validation chain results

All 12 rows had the same fail-closed outcome:

| Metric | Result |
|---|---:|
| Selected / processed | 12 / 12 |
| Membership verified | 0 |
| ACTIVE XKRX verified | 0 |
| Exact Security Name verified | 0 |
| Share Class verified | 0 |
| Instrument Type verified | 0 |
| Exact ISIN verified | 0 |
| ISIN Luhn PASS | 0 |
| Corporate Action Clear | 0 |
| TRUE_IDENTITY_CONFLICT | 0 |
| VALIDATION_READY | 0 |
| VALIDATION_REVIEW | 0 |
| VALIDATION_FAIL | 12 |

All rows were marked `CURRENT_MEMBERSHIP_UNRESOLVED`, `LISTING_UNRESOLVED`, exact class/instrument unresolved, missing ISIN and `VALIDATION_FAIL` because the central row-level evidence path was technically unusable. Corporate-action status remained UNKNOWN. Collision QA found no current Korea identity conflict in the 2527 Research Partial; unresolved candidates were not treated as admitted identities.

Yields, all based on 12 selected rows:

| Yield | Result |
|---|---:|
| Membership Yield | 0% |
| Listing Yield | 0% |
| Security/Class Yield | 0% |
| Instrument Yield | 0% |
| ISIN Yield | 0% |
| Full Validation Yield | 0% |

## 6. Source capability and scalability

| Source capability | Security-level | Row-level | Current | Reproducible | Machine-readable | Scalability |
|---|---|---|---|---|---|---|
| KRX landing | NO | NO | YES as landing only | YES as landing only | PARTIAL | NO for admission |
| KRX row endpoint | INTENDED | INTENDED | UNKNOWN | NO | NO | NO |
| KSD public route | UNKNOWN | UNKNOWN | UNKNOWN | NO proven path | UNKNOWN | NO proven path |
| Issuer/filings | YES case-by-case | NO population rows | CASE-SPECIFIC | LIMITED | PARTIAL | LIMITED |
| ISO MIC list | NO | NO security rows | YES reference | YES | YES | YES for MIC reference only |

The central condition for a build — current row-level membership plus active listing plus exact Security/Class/ISIN — was not demonstrated. Therefore the sample is blocked under the <40% rule and under each central-source fail rule.

## 7. Canada failure-mode comparison

Canada evidence history:

- Legacy conversion/identity: 0/217 conversion-ready
- Canada Exact Evidence v1: FAILED / no ready output
- Canada Exact Evidence v2: 0/217 EVIDENCE_READY
- Targeted Manual Identity Recovery: 0/30 RECOVERY_READY
- Canada Rebuild Admission Build: 0/217 ADMIT
- Canada Targeted Current Evidence: 0/20 TARGET_EVIDENCE_READY

Korea validation: 0/12 VALIDATION_READY.

**Does Korea demonstrate a qualitatively different evidence capability? NO.**

KRX has a distinct official authority and KOSPI 200 is a bounded population, but the operationally decisive capability was not different in this test: the landing page was reachable while row-level current membership/listing/identity evidence was not reproducibly delivered. This is the same failure pattern as Canada at the gate level. No build is authorized.

## 8. Build-readiness decision

**BLOCKED.**

The full validation yield is 0%, below the 40% threshold. In addition, row-level current membership, ACTIVE XKRX listing, exact Security/Class identity and exact ISIN were not reproducible. This is more than one technical blocker, so CONDITIONAL is not permitted.

**NEXT AUTHORIZED STAGE: Post-Korea Evidence Validation Manager Gate — READ-ONLY**

No second sample, larger sample, full KOSPI-200 build or open-ended source hunt is authorized by this report.

## 9. Quality gates

- G0 Correct origin/main HEAD — PASS
- G1 Correct authorized Validation stage — PASS
- G2 Korea Policy Gate recognized — PASS
- G3 Sample selected deterministically before research — PASS
- G4 Sample frozen and SHA recorded — PASS
- G5 Population Membership tested — PASS
- G6 KRX current listing tested — PASS
- G7 Security/Class evidence tested — PASS
- G8 Instrument Type tested — PASS
- G9 ISIN evidence tested — PASS
- G10 KSD capability tested — PASS
- G11 Corporate Action tested — PASS
- G12 Collision QA tested — PASS
- G13 Per-security final status complete — PASS
- G14 Source scalability evaluated — PASS
- G15 Canada-failure-mode comparison completed — PASS
- G16 No Universe/Data write — PASS
- G17 No Korea Admission Build executed — PASS

## 10. No-touch confirmation

Only this report and the two bounded validation sidecars were created. No Korea candidate population, full constituent file, admission output, Universe/Data Master change, Research Partial change, Strict change, Frozen change, Canada change, mapping, history, liquidity, eligibility, scan or U3K action was performed. Korea coverage remains 0. No admission was performed.

## Final

**KOREA PRE-BUILD EVIDENCE VALIDATION GATE — PASS**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Post-Korea Evidence Validation Manager Gate — READ-ONLY**
