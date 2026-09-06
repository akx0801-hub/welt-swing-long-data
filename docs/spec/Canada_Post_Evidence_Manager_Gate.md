# Canada Post-Evidence Manager Gate

## Decision

**RECOMMENDATION B — TARGETED MANUAL RECOVERY**

**NEXT AUTHORIZED STAGE: Canada Targeted Manual Identity Recovery — READ-ONLY / NO UNIVERSE WRITE**

This is a manager decision only. It authorizes no evidence rerun, admission, mapping, integration, eligibility work or Universe write.

## Start and verified inputs

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Current verified HEAD: `e8c2c5390798f521d37b5142431688df75285ede`
- Verified v2 commit: `Canada exact evidence acquisition v2 split review`
- Canada baseline: 217
- v2 rows checked: 217
- EVIDENCE_READY: 0
- IDENTITY_REVIEW: 217
- INSTRUMENT_REVIEW: 0
- EXCLUDE: 0
- ISIN verified: 0
- Share Class verified: 0
- Instrument Type verified: 0
- Primary MIC verified: 217
- Primary Ticker verified: 217
- TRUE_IDENTITY_CONFLICT: 0
- TICKER_ONLY_CROSS_MIC: 12
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe touched by v2: NO
- Intended commit message: `Canada post evidence manager gate`

## Meaning of the result

The v2 stage is procedurally complete, but Canada is not conversion- or admission-ready. The result does not show that all 217 historical membership rows are wrong. It shows only that the tested workflow could not reproduce the complete Security-level identity tuple for any row under the enforced rules:

`ISIN + Primary_MIC + Primary_Ticker`

The three dominant blockers are:

- `MISSING_ISIN`
- `SHARE_CLASS_UNRESOLVED`
- `INSTRUMENT_TYPE_UNRESOLVED`

Ticker, issuer name or XTSE alone cannot cure these gaps.

## Option A — Park Canada

Parking is defensible because the full v2 run yielded zero ready rows and the available source stack did not provide a scalable, reproducible identifier/class feed. It avoids further work and all identity risk.

It is not selected as the immediate priority because Canada remains a documented regional diversification opportunity and the failure is concentrated in missing Security-level evidence, not in a demonstrated population-wide invalidity. Permanent parking would leave the 217-row baseline unresolved without testing whether a small, objectively defined group of high-evidence cases can be recovered efficiently.

Rejected next stage: `Post-Canada Next-Population Manager Gate — READ-ONLY`.

## Option B — Targeted Manual Recovery

A bounded recovery is justified, but only as a separate manual identity stage. The stage must be limited to **20–40 existing rows maximum** and must not reprocess all 217.

The candidate set must be selected by reproducible criteria, not subjective fame or ticker recognition:

1. established TSX common/ordinary equity;
2. existing XTSE/ticker pairing is clear;
3. official issuer or filing evidence is likely available;
4. no unresolved multiple-class ambiguity;
5. no trust, unit, preferred or other non-standard instrument unless explicitly included as a separate review subgroup;
6. no unresolved rename, merger, delisting or successor-security issue;
7. strategic value for Canadian diversification and likely evidence yield.

The later stage must require, for every promoted row:

- exact Security and Share Class;
- evidence-backed Instrument Type;
- exact ISIN with format and Luhn validation;
- verified Primary MIC and Primary Ticker;
- reproducible source/document/date references;
- no unresolved corporate action;
- collision QA against Research Partial;
- fail-closed status when any gate is missing.

No minimum READY quota is authorized. A low-yield result is acceptable if evidence quality is high. Any candidate that cannot satisfy all identity gates remains `IDENTITY_REVIEW`.

## Option C — Rebuild Canada

A rebuild would provide a cleaner current population only if the legacy 217 cannot be economically reconstructed and a new official/institutional source can provide complete Security-level fields. That has not been demonstrated by the current gate.

Rebuild is rejected now because it would introduce a new population question, risk replacing rather than analyzing the existing baseline, and require a separate admission-policy decision. The existing 217 rows remain unchanged and are not to be silently deleted or replaced.

Rejected next stage: `Canada Rebuild Admission Policy Gate — READ-ONLY`.

## Cost / benefit and opportunity cost

The full-population v2 approach has poor marginal efficiency: 217 cases produced no ready identity. A 20–40-row manual subset has a materially better chance of producing useful evidence because it can concentrate on simple, well-documented primary common shares while preserving strict fail-closed rules.

The expected benefit is not merely quantity. A successful subset would add verified Canadian primary listings and regional diversification to a universe that already contains 741 integrated US membership rows and 153 AU-1 rows. Canada therefore has diversification value, but not at the cost of weakening identity controls.

A full Canada recovery, a rebuild, Korea, AU-2 or US-3 are not authorized by this report. Their relative opportunity cost is acknowledged only for this decision.

## Hard limits for the next stage

- scope: existing Canada membership only;
- maximum size: 20–40 rows;
- no new members;
- no complete 217-row rerun;
- no CUSIP or ticker-only fallback;
- no issuer-level substitution for Security-level identity;
- no silent Share-Class conversion;
- no Membership, Research Partial, Strict or Frozen change;
- no History, Liquidity, Eligibility, Mapping, Integration or Admission;
- no Universe/Data Master write;
- Alpha Vantage prohibited.

## Quality gates

- G0 Correct `origin/main` HEAD: PASS
- G1 Correct manager stage: PASS
- G2 v2 result verified: PASS
- G3 0/217 EVIDENCE_READY acknowledged: PASS
- G4 No evidence rerun performed: PASS
- G5 Park option evaluated: PASS
- G6 Targeted recovery evaluated: PASS
- G7 Rebuild option evaluated: PASS
- G8 Cost/benefit evaluated: PASS
- G9 Governance risk evaluated: PASS
- G10 Diversification value evaluated: PASS
- G11 Alternative opportunity cost evaluated: PASS
- G12 Exactly one recommendation selected: PASS
- G13 Exact next stage defined: PASS
- G14 No Universe/Data write: PASS
- G15 Research Partial unchanged: PASS
- G16 Strict/Frozen unchanged: PASS
- G17 No unrelated stage started: PASS

## Final decision

**CANADA POST-EVIDENCE MANAGER GATE — RECOMMENDATION B**

**TARGETED MANUAL RECOVERY**

**NEXT AUTHORIZED STAGE: Canada Targeted Manual Identity Recovery — READ-ONLY / NO UNIVERSE WRITE**

This report does not authorize the recovery stage automatically beyond defining its exact scope. Canada remains 217 historical Membership rows, with 0 evidence-ready rows, until a separately executed and separately reviewed stage produces qualifying evidence.
