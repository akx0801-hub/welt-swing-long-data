# Canada Rebuild Admission Build Report

**CANADA REBUILD ADMISSION BUILD — PASS**

## Start / scope
- Start HEAD: 73d85735f2dc9ef50918ca2f09898c3e30821e8c
- Authorized stage: Canada Rebuild Admission Build — CONTROLLED BUILD / SIDECAR ONLY / NO UNIVERSE WRITE
- Policy: docs/spec/Canada_Rebuild_Admission_Policy_Gate.md
- Research Partial: 2527; Strict: 759; Frozen: 0.
- Legacy Canada: 217; unchanged and reference-only.

## Population
- Population: S&P/TSX Composite.
- Discovery count: 217; deduped candidates: 217.
- Snapshot: SRC_TMX_TSX_COMPOSITE, 2026-08-22.
- Official S&P characteristics page: 217 constituents as of 2026-08-31.
- Official full export was not exposed; status PARTIAL. No unofficial replacement was used.
- ARX and SES remain in the snapshot for explicit corporate-action QA and are excluded as obsolete historical securities. No successor was added. Snowline Gold was not added because its effective date is 2026-09-21.

## Coverage
| Measure | Count |
|---|---:|
| Membership verified in official lineage snapshot | 217 |
| Current full membership reconciled | 0 |
| XTSE in source lineage | 217 |
| Primary MIC carried from source lineage | 217 |
| Primary ticker carried from source lineage | 217 |
| Current ACTIVE listing freshly verified | 0 |
| ISIN verified | 0 |
| Share Class verified | 0 |
| Instrument Type verified | 0 |

No Canonical_WS_ID was created. TSX Venture is out of scope.

## Instrument / corporate action
Common/Ordinary 0; Preferred 0; REIT 0; Trust 0; Unit 0; ETF/Fund 0; Depositary Receipt 0; Foreign Secondary 0; Other 0; Unresolved 217.

Corporate-action cases: 2 (ARX and SES acquisition/removal notices). No automatic successor mapping.

## Collision / legacy overlap
EXACT_IDENTITY_DUPLICATE 0; ISIN_DUPLICATE 0; MIC_TICKER_DUPLICATE 0; TICKER_ONLY_CROSS_MIC 0; TRUE_IDENTITY_CONFLICT 0. Legacy overlap: NEW 0; ALREADY_PRESENT_EXACT 0; LEGACY_MATCH_REVIEW 217; CONFLICT 0. No exact identity could be constructed because no verified ISIN/Class exists.

## Final results
| Status | Count |
|---|---:|
| ADMIT | 0 |
| REVIEW | 215 |
| EXCLUDE | 2 |
| Final-status sum | 217 |

Admission yield 0.0%; ISIN yield 0.0%; Share-Class yield 0.0%; Instrument-Type yield 0.0%. Snapshot coverage is 217/217; current full reconciliation is 0/217. Listing lineage coverage is 217/217; current ACTIVE coverage is 0/217.

## Quality gates
G0 Correct origin/main HEAD — PASS  
G1 Authorized stage — PASS  
G2 Policy basis respected — PASS  
G3 Legacy unchanged — PASS  
G4 New pipeline separated — PASS  
G5 Population discovery completed — PASS  
G6 Discovery deduplicated — PASS  
G7 Listing fields isolated from legacy identity — PASS  
G8 Security identity fail-closed — PASS  
G9 Share-class QA — PASS  
G10 ISIN QA — PASS  
G11 Instrument classification — PASS  
G12 Primary listing/MIC/ticker handling — PASS  
G13 Corporate-action QA — PASS  
G14 Collision QA — PASS  
G15 Every candidate has one status — PASS  
G16 No Universe/Data Master write — PASS  
G17 No unrelated stage started — PASS  

## No-touch confirmation
Only the seven build sidecars/manifest/report were created. No Universe, Membership, Research Partial, Strict, Frozen, History, Liquidity, Eligibility, Scan/U3K or v7.2 file was changed. No integration or follow-on stage was started.

This PASS indicates a complete fail-closed sidecar build only. It does not approve admission, mapping, integration, eligibility or Universe write.
