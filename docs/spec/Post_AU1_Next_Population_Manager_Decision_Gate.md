# Post-AU-1 Next-Population Manager Decision Gate

## 1. Current verified state

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Verified HEAD: `d87fd072430caf000570d7fa865cf3c7e009172d`
- HEAD message: `AU-1 post-integration integrity audit PASS 153`
- Research Partial: 2,527
- Integrated expansion counts: US-1 = 372, US-2 = 369, AU-1 = 153
- Strict = 759
- Frozen = 0
- AU-1 Controlled Integration Write = PASS
- AU-1 Post-Integration Integrity Audit = PASS
- G0-G17 = PASS

No AU-1 artefact is reopened or modified by this decision gate.

## 2. Binding governance

- Welt-Swing v7.2 remains the sole productive trading authority.
- DEV remains DEV / RESEARCH / SHADOW and is not productive.
- Membership, Eligibility, Scan and Execution remain separate states.
- Research Partial is a research workbench, not a permanent master.
- Strict 759 is an eligibility dry-run, not a membership tier.
- Frozen remains 0; no U3K freeze is authorized.
- Identity is ISIN + Primary_MIC + Primary_Ticker.
- Missing or conflicting identity is fail-closed.
- No silent ISIN fallback, no MIC merge and no ticker-only identity.
- Alpha Vantage remains prohibited.
- This gate authorizes no download, build, membership change, Universe write, Eligibility change or scan/U3K action.

## 3. Decision baseline from current repository artefacts

The P5.0 architecture gate records:

- AU and Korea as zero-membership expansion directions.
- Canada as existing membership requiring conversion: 217 membership, 0 Strict.
- Canada is explicitly identity-blocked by missing ISIN evidence.
- The expansion sequence must remain policy -> evidence -> mapping -> history -> QA -> eligibility -> manager gate.

The P6 Coverage & Expansion Decision Gate records:

- Australia S&P/ASX 200 Common on XASX as the prior number-one expansion direction.
- Canada: `CANADA_REQUIRES_IDENTITY_GATE_FIRST`.
- Korea: `NOT NOW`.
- US-3: `NOT NOW`.
- P6 recommendation was not itself a build authorization.

AU-1 has now completed the Australia S&P/ASX 200 Common/Ordinary admission path and integrated 153 verified rows. Therefore the prior Australia-zero-coverage recommendation has been executed. A further Australia slice is not currently defined as a clean, disjoint repository-authorized population.

## 4. Options considered

### A. Further Australia slice / AU-2

Assessment: not recommended now.

AU-1 already covered the repository-defined S&P/ASX 200 Common/Ordinary path. The remaining AU-1 discovery classes were deliberately fail-closed:

- A-REIT: REVIEW
- Stapled securities: REVIEW
- Foreign-incorporated ASX ordinary: REVIEW
- ETF/Fund: EXCLUDE
- CDI/DR: EXCLUDE
- Other units and non-canonical classes: EXCLUDE or REVIEW

Turning these into a second population would risk reopening AU-1 exclusions, creating overlap, or converting instrument review into an unjustified admission. No separate AU-2 target with independent official membership and a clearly disjoint identity scope is documented in the current governance artefacts.

### B. Canada conversion / identity work

Assessment: recommended as the next bounded stage.

Canada already has 217 membership records, but 0 Strict and 0 usable ISIN identity under the current gate. This is not a new population problem; it is an identity/conversion problem. Resolving it read-only could add a materially relevant developed-market block without inventing membership or increasing US concentration.

Required controls remain:

- official/institutional evidence only;
- ISIN + Primary_MIC + Primary_Ticker for every candidate;
- no CUSIP-as-ISIN substitution;
- no ticker-only admission;
- no MIC merge;
- unresolved or conflicting rows remain REVIEW/EXCLUDE;
- no admission, mapping, history, liquidity, eligibility or write step in the identity gate.

Expected value is high if identity can be resolved, but admission is not presumed. The stage must be allowed to fail closed.

### C. Korea

Assessment: not recommended now.

Korea offers diversification, but it is a new population with zero current membership and higher structural complexity. The repository rates the option medium-high complexity and Asia is already a substantial part of the current coverage. It would require a new official-membership and primary-listing evidence chain before any meaningful comparison with Canada is possible.

### D. Further US population / US-3

Assessment: not recommended now.

US-1 and US-2 already provide 741 integrated rows. A further US slice would deepen an already large regional block rather than close the documented Canada/Oceania identity and coverage gaps. The current US policy also requires a separately bounded segment and explicit manager authorization; no such authorization is created by this report.

### E. Other regions

Assessment: not recommended.

The current repository does not provide a newer, sufficiently justified alternative that is superior to the documented Canada identity gate. No free-form expansion is introduced.

## 5. Comparative conclusion

| Option | Nature | Main benefit | Main risk | Decision |
|---|---|---|---|---|
| Further AU / AU-2 | New/reopened expansion | possible Oceania depth | overlap with AU-1; review classes improperly admitted | Reject now |
| Canada | Conversion/identity | 217 existing records; closes documented identity gap | missing ISIN; high collision/conversion risk | Recommend first |
| Korea | New expansion | regional diversification | zero membership; medium-high complexity; Asia already covered | Reject now |
| US-3 | Further US expansion | additional US breadth | concentration; quantity over quality | Reject now |
| Other | New expansion | not established | no repository-backed priority | Reject |

## 6. Final recommendation

**POST-AU1 MANAGER DECISION — RECOMMENDATION B**

First perform bounded Canada conversion/identity work. This is not a Canada build and not an admission authorization. It is a read-only identity gate to determine whether the existing 217 Canada membership records can be converted into valid, collision-free canonical primary listings.

NEXT AUTHORIZED STAGE:
**Canada Conversion / Identity Gate — READ-ONLY**

The next stage may not download a new population, create a candidate list, alter Membership, Research Partial, Strict, Frozen, History, Liquidity, Eligibility or Scan/U3K, and may not write to the Universe. Any later admission policy, evidence, mapping, eligibility and write stages require separate manager authorization.

## 7. Explicit closure

- No AU-2 build authorized.
- No Korea build authorized.
- No US-3 build authorized.
- No Canada admission or Universe write authorized.
- No U3K freeze authorized.
- No productive Welt-Swing-v7.2 rule changed.
- No Universe or data file changed by this decision gate.

**POST-AU1 MANAGER DECISION — RECOMMENDATION B**
