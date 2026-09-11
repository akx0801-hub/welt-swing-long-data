# S&P/BMV IPC Expansion Evidence Precheck

## 1. Purpose

This report executes exactly the authorized stage:

**S&P/BMV IPC Expansion Evidence Precheck — READ-ONLY / EVIDENCE VALIDATION ONLY / NO ADMISSION / NO UNIVERSE WRITE**

It evaluates only repository evidence committed at or before start HEAD `b49bb1a8d8ac82492d10a66005e7730788247e13` against the normative Expansion Evidence Materialization, Currentness & Identity Precheck Contract.

It performs no web research, no source hunt, no endpoint/provider testing, no new download, no population materialization, no identity recovery, no admission, no build and no Universe write.

**STAGE STATUS: PASS**

**PRECHECK RESULT: BLOCKED**

**MX_IPC state after this stage: PRECHECK_BLOCKED / MANAGER_DECISION_REQUIRED**

**NEXT AUTHORIZED STAGE: S&P/BMV IPC Precheck Blocker Manager Gate — READ-ONLY / MANAGER ONLY**

## 2. Authorized Stage and Start HEAD Verification

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Expected/start HEAD: `b49bb1a8d8ac82492d10a66005e7730788247e13`
- Verified start commit: `Post-Nifty next population manager gate`
- Authorized stage: `S&P/BMV IPC Expansion Evidence Precheck — READ-ONLY / EVIDENCE VALIDATION ONLY / NO ADMISSION / NO UNIVERSE WRITE`
- Start gate: PASS

## 3. Fixed Baseline

The fixed baseline remains unchanged:

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
| India — Nifty 50 | PARKED |

Productive authority remains Welt-Swing v7.2. DEV remains DEV / RESEARCH / SHADOW. Membership != Eligibility != Scan != Execution. Research Partial and Strict are not U3K.

## 4. Population Definition

- Population: **Mexico — S&P/BMV IPC**
- Population ID / boundary: `MX_IPC`
- Target population size in committed manager evidence: **35 target securities**
- Primary market: **Bolsa Mexicana de Valores**
- Primary MIC: `XMEX`
- Canonical imported source lineage: **NONE**
- Committed source IDs directly relevant to this precheck: `BMV_LANDING`, `BMV_IPC_2026_REBALANCE_FINAL`, and v0.30 source label `BMV_OFFICIAL_IPC_FINAL_REBALANCE_PDF`

The repository does not contain a canonical imported 35-row MX_IPC population at the start HEAD.

## 5. Normative Contract

Normative document:

`docs/spec/Expansion_Evidence_Materialization_Currentness_Identity_Precheck_Contract.md`

The contract requires actual P0-P18 assessment and permits only binary terminal results `READY` or `BLOCKED`. Any failed hard gate, P9 `WEAK`, P15 `HIGH`, P16 `NO`, or P17 overall risk `HIGH` requires `BLOCKED`.

## 6. Evidence Inventory

Only already committed evidence was used.

| # | Repository path | Evidence role |
|---:|---|---|
| 1 | `docs/spec/Expansion_Evidence_Materialization_Currentness_Identity_Precheck_Contract.md` | Normative P0-P18 and hard-gate contract |
| 2 | `docs/spec/Post_Nifty_Next_Population_Manager_Gate.md` | Authorized MX_IPC target and committed-evidence scope |
| 3 | `output_current_master_missing_source_materialization_v0_29/missing_segment_materialization_status_v0.29.csv` | Records BMV/SPDJI routes but no full current 35-list materialization |
| 4 | `output_current_master_missing_source_materialization_v0_29/official_candidate_links_v0.29.csv` | Pre-existing official BMV candidate links |
| 5 | `output_current_master_source_deep_materialization_v0_30/source_deep_materialization_status_v0.30.csv` | Records official BMV final rebalance document materialized; identity extraction pending |
| 6 | `output_current_master_source_deep_materialization_v0_30/summary_v0.30.json` | Exact direct PDF source metadata, HTTP 200, 137691 bytes, 2 pages |
| 7 | `output_current_master_remaining_source_materialization_v0_35/remaining_segment_official_endpoint_probe_v0.35.csv` | Runner-tested committed route/artifact metadata; full membership not validated |
| 8 | `output_current_master_remaining_source_materialization_v0_35/official_candidate_asset_links_v0.35.csv` | Direct-asset / runner-reproducibility evidence |
| 9 | `output_current_master_remaining_source_materialization_v0_35/raw_official_source/MX_IPC_BMV_LANDING.bin` | Committed official landing-page raw bytes |
| 10 | `output_current_master_remaining_source_materialization_v0_35/raw_official_source/MX_IPC_BMV_IPC_2026_REBALANCE_FINAL.bin` | Committed direct official rebalance-PDF raw bytes |
| 11 | `output_current_master_remaining_source_materialization_v0_35/manifest_v0.35.json` | Stage input freeze/integrity metadata; no canonical import |
| 12 | `config/current_master_remaining_missing_segment_official_source_materialization_v0.35.json` | Declares MX PDF expected semantics as `current_change_document` |
| 13 | `scripts/current_master_materialized_official_membership_identity_reconciliation_v0_31.py` | Existing deterministic parser logic classifies MX evidence as change-only |
| 14 | `output_current_master_membership_identity_reconciliation_v0_31/segment_identity_reconciliation_status_v0.31.csv` | Explicit committed status `CHANGE_LEDGER_ONLY_NOT_FULL_MEMBERSHIP` |

No evidence outside the repository was used.

## 7. Raw-Artifact Assessment

### BMV landing artifact

Committed raw artifact:

`output_current_master_remaining_source_materialization_v0_35/raw_official_source/MX_IPC_BMV_LANDING.bin`

- Official-domain route: YES
- Stored raw bytes: YES
- Runner-tested: YES
- Runner-reproducible: YES in committed v0.35 probe evidence
- Full membership validated: NO
- Canonical population snapshot: NO

### Direct rebalance PDF artifact

Committed raw artifact:

`output_current_master_remaining_source_materialization_v0_35/raw_official_source/MX_IPC_BMV_IPC_2026_REBALANCE_FINAL.bin`

Committed metadata establishes:

- source: official BMV-hosted S&P/BMV IPC final rebalance announcement
- HTTP status: 200
- content type: PDF
- bytes: 137691
- pages: 2
- announcement date: 2026-03-13
- effective date stated in the document: 2026-03-23
- repository Git blob SHA: `ffe3d7320dc485109e3363eaea1dbf445691f7b7`
- explicit SHA256 for this raw MX PDF in the inspected committed evidence: NONE identified
- full membership claimed: NO
- full membership validated: NO

The raw artifact itself is reproducibly stored, but it is not a complete constituent snapshot.

## 8. Rebalance-Document Classification

The committed deterministic v0.31 logic classifies the PDF as:

`OFFICIAL_FINAL_REBALANCE_CHANGE_ONLY`

and the committed segment status is:

`CHANGE_LEDGER_ONLY_NOT_FULL_MEMBERSHIP`.

The document contains exactly the committed change evidence:

- `VOLAR A` — ADD
- `CUERVO *` — DROP

It is therefore classification **C: only ADD/DROP/rebalance changes**, not A full current membership and not B complete membership plus changes.

No qualifying reproducible base population is committed that would permit deterministic reconstruction of a complete current 35-security set by applying those changes. No such reconstruction is performed in this stage.

## 9. P0-P18 Results

### P0 — Population Boundary

**Requirement:** Exact index/population, size or tight range, primary market/MIC, security-level boundary, instrument inclusion/exclusion and source lineage.

**Evidence:** `MX_IPC` / S&P/BMV IPC, 35-target manager boundary, BMV / XMEX. No canonical imported lineage and no committed complete security-level 35-member boundary or complete inclusion/exclusion instrument semantics.

**Result: FAIL**

**Reason:** Index identity and target size are clear, but the security-level governed boundary is not independently materialized and exact population instrument scope is not fully evidenced.

### P1 — Population Authority

**Requirement:** Official index administrator, primary exchange, regulator, market infrastructure, or repository-qualified equivalent; must not be WEAK.

**Evidence:** Official BMV-hosted S&P/BMV IPC final rebalance announcement and official BMV special-information route.

**Result: STRONG / gate PASS**

**Reason:** Authority is strong, but authority alone does not establish complete membership or currentness.

### P2 — Security-Level Population Evidence

**Requirement:** Complete security-level evidence for the governed population; counts or change-only documents are insufficient.

**Evidence:** Two explicit security-level change rows only (`VOLAR A` ADD, `CUERVO *` DROP). Committed v0.31 status explicitly says change ledger only, not full membership.

**Result: FAIL**

**Security Rows Evidenced:** 2 change rows; **0 complete full-population membership rows proven**.

**Reason:** The evidence does not enumerate the full current 35-security population.

### P3 — Materialization Reproducibility

**Requirement:** Exact source/retrieval path, materializable raw population snapshot, reproducible extraction, stable deterministic handling, no manual copy/paste, batch-level acquisition.

**Evidence:** The BMV landing page and direct PDF are committed raw artifacts and runner reproducibility is documented. However, the direct PDF is a change-only document, not a raw full-population snapshot. No exact full-population acquisition path is materialized in committed evidence.

**Result: FAIL**

**Reason:** Reproducible materialization exists for a limited change document, not for the governed population required by P3.

### P4 — Snapshot Integrity

**Requirement:** Retrieval/as-of metadata, raw path/pointer, SHA256 or approved equivalent, raw row count, normalized row count, schema inventory, parsing notes and deterministic rerun description for the governed evidence snapshot.

**Evidence:** Raw paths exist and Git blob identity is available; PDF byte size and deterministic change parser evidence exist. No qualifying full-population raw snapshot exists; no full-population raw row count/normalized count exists; no explicit SHA256 for the MX PDF was identified in the inspected committed evidence.

**Result: FAIL**

**Reason:** Integrity is demonstrable for the limited stored artifact, not for a qualifying population snapshot.

### P5 — Currentness

**Requirement:** Security-level currentness evidence, source as-of/current marker, current membership/listing testability, corporate-action awareness and deterministic stale reconciliation.

**Evidence:** Rebalance announcement date 2026-03-13; effective date 2026-03-23. No committed full-population as-of snapshot and no later currentness confirmation sufficient to prove the current 35-member set.

**Currentness Status: STALE-NOT-RECONCILABLE**

**Currentness Evidence Result: FAIL**

**Reason:** March 2026 ADD/DROP evidence does not prove current membership at the stage date, and no committed deterministic base+delta chain closes the gap.

### P6 — Primary Listing / MIC

**Requirement:** Primary market and MIC known per security; no silent ADR/GDR/secondary substitution.

**Evidence:** Population market is fixed as BMV / `XMEX`. The two change tickers are exchange-style security identifiers, but the complete 35-member set is absent and per-security primary-listing validation is not available for the governed population.

**Result: FAIL**

**Reason:** Population-level market architecture is known, but complete security-level primary-listing evidence is not.

### P7 — Local Security Code / Primary Ticker

**Requirement:** Deterministic security-level join key for the governed population.

**Evidence:** Exact announced ticker/series tokens exist for the two change rows (`VOLAR A`, `CUERVO *`). No complete 35-row local-code/ticker set is committed.

**Result: FAIL**

**Reason:** Two change-row identifiers do not establish the local-code architecture for the entire population.

### P8 — Security Identity

**Requirement:** `ISIN + Primary MIC + Primary Ticker/Local Security Code + Exact Security Name + Exact Share Class`.

**Evidence:** The two change rows contain ticker/series tokens and company names. No complete population identity set exists. No full-population ISIN and exact share-series mapping exists.

**Result: FAIL**

**Complete Canonical Identity Rows:** 0/35 proven.

**Reason:** The canonical identity tuple is incomplete at population scale.

### P9 — ISIN Capability

**Requirement:** STRONG batch-capable security-level ISIN evidence with high coverage, or narrowly bounded CONDITIONAL gaps. Systemic absence is WEAK.

**Evidence:** No committed canonical MX_IPC population exists and no population-wide ISIN mapping is committed in the inspected MX evidence.

**Result: WEAK**

**ISIN Validated:** 0 population rows proven; full-population coverage UNKNOWN.

**Reason:** The evidence does not demonstrate a batch-capable population-wide ISIN path. P9 WEAK is blocking.

### P10 — Share-Class / Share-Series Fidelity

**Requirement:** Exact security-class semantics preventing issuer merging and silent class substitution.

**Evidence:** The two change rows preserve explicit ticker/series strings (`VOLAR A`, `CUERVO *`), which is useful change-level series evidence. No exact share-series evidence exists for the complete 35-member population.

**Result: FAIL**

**Exact Share-Series Validated:** 2 change rows only; 0/35 complete population rows proven.

**Reason:** Change-level series fidelity does not establish population-wide share-series fidelity.

### P11 — Instrument Classification

**Requirement:** Sufficient capability to distinguish ordinary/common, preferred, REIT, unit, ETF, fund, ADR/GDR, rights, warrants, structured product, debt, foreign secondary listing and unknown.

**Evidence:** The rebalance change ledger provides ticker, company and action, not a complete governed instrument-classification field set for the population.

**Result: FAIL**

**Reason:** Full-population instrument classification is not committed.

### P12 — Corporate-Action Visibility

**Requirement:** Detect identity-relevant ticker/name/class/merger/spin-off/delisting/relisting/exchange/identifier/index-replacement changes.

**Evidence:** The committed rebalance PDF demonstrates index ADD/DROP visibility for two securities. It does not establish a general population-wide corporate-action reconciliation architecture for identity continuity.

**Result: FAIL**

**Reason:** Index rebalance visibility is narrower than the contract's required identity-relevant corporate-action visibility.

### P13 — Batch Capability

**Requirement:** Central population evidence path must be batch-capable and reproducible; per-security research cannot be primary path.

**Evidence:** The committed script can deterministically parse the two change rows, but no complete 35-member source/pipeline exists. Full-population identity/ISIN/share-series batch processing is not evidenced.

**Result: FAIL**

**Reason:** Batch processing of a two-row change ledger is not batch processing of the governed population.

### P14 — Row-Level Reproducibility

**Requirement:** Every normalized security row traceable deterministically to raw evidence with deterministic row key and mapping rule.

**Evidence:** The two change rows are deterministically traceable to the committed PDF through the existing parser logic. No full-population normalized row set exists to trace to qualifying raw membership evidence.

**Result: FAIL**

**Row-Level Reproducible:** 2 change-ledger rows; 0/35 complete population membership rows proven reproducible.

**Reason:** Population-wide raw-to-row lineage is absent.

### P15 — Manual Recovery Threshold

**Requirement:** LOW or bounded MEDIUM only; broad population/security-by-security recovery is HIGH and blocking.

**Evidence:** Full current membership, complete identity, ISIN and share-series evidence are absent. Completing them from the current committed evidence would require an additional full-membership source path and/or broad manual reconstruction, both outside this stage.

**Result: HIGH**

**Residual Manual Recovery Count:** UNKNOWN; cannot be safely derived from a change-only ledger.

**Reason:** The missing evidence is systemic, not an isolated minority residual.

### P16 — Scalability

**Requirement:** YES or bounded LIMITED; NO blocks. Evidence architecture must scale through deterministic batch operations.

**Evidence:** No existing full-population source-to-identity pipeline is committed. Existing deterministic handling covers only two rebalance changes.

**Result: NO**

**Reason:** The current evidence cannot scale to the governed 35-member population without a new evidence path.

### P17 — Failure-Loop Risk

**Requirement:** Rate Canada/Korea/US-3/Brazil/Taiwan patterns and overall repeat-failure risk.

**Evidence-based comparison:**

- Canada-Type Risk: **HIGH** — population-wide identity/ISIN completion is absent and would risk broad recovery.
- Korea-Type Risk: **HIGH** — full population evidence is not reproducibly materialized at row level.
- US-3-Type Risk: **MEDIUM** — raw materialization works, but for the wrong semantic object (change document rather than full population snapshot).
- Brazil-Type Risk: **HIGH** — official authority and raw artifact exist, but decisive identity/population linkage is incomplete.
- Taiwan-Type Risk: **HIGH** — current full membership/currentness is not proven.
- Nifty-Type Risk: **HIGH** — useful derived/limited security evidence exists without the complete independent population/currentness/identity chain.

**Overall Failure-Loop Risk: HIGH**

**Dominant pattern:** combined Korea/Taiwan/Nifty pattern — incomplete full-population materialization, absent currentness chain and absent population-wide raw-to-identity traceability despite useful official raw artifacts.

### P18 — Policy-Gate Readiness

**Requirement:** `READY` only if all hard gates and thresholds pass; otherwise `BLOCKED`.

**Evidence:** Multiple hard gates fail; P9 is WEAK; P15 is HIGH; P16 is NO; P17 overall risk is HIGH.

**Result: BLOCKED**

## 10. Hard-Gate Matrix

| Contract gate | Result |
|---|---|
| P0 Population Boundary | FAIL |
| P1 Population Authority | STRONG / PASS |
| P2 Security-Level Population Evidence | FAIL |
| P3 Materialization Reproducibility | FAIL |
| P4 Snapshot Integrity | FAIL |
| P5 Currentness | STALE-NOT-RECONCILABLE / FAIL |
| P6 Primary Listing / MIC | FAIL |
| P7 Local Security Code / Primary Ticker | FAIL |
| P8 Security Identity | FAIL |
| P9 ISIN Capability | WEAK |
| P10 Share-Series Fidelity | FAIL |
| P11 Instrument Classification | FAIL |
| P12 Corporate Action Visibility | FAIL |
| P13 Batch Capability | FAIL |
| P14 Row-Level Reproducibility | FAIL |
| P15 Manual Recovery | HIGH |
| P16 Scalability | NO |
| P17 Overall Failure-Loop Risk | HIGH |
| P18 Policy-Gate Readiness | BLOCKED |

## 11. Population and Currentness Assessment

- Target population size: 35 in committed manager evidence.
- Full current membership rows proven: 0/35.
- Change rows proven: 2.
- Announcement date: 2026-03-13.
- Effective date: 2026-03-23.
- Qualifying full-population as-of: NONE.
- Currentness confirmation sufficient for present population: NONE.
- Deterministic current base+delta reconciliation: NONE.

The March rebalance announcement cannot be treated as current full membership evidence.

## 12. Identity, ISIN and Share-Series Assessment

- Complete canonical identity rows proven: 0/35.
- ISIN coverage for full population: UNKNOWN; no population-wide committed mapping.
- Population-wide ISIN capability: WEAK.
- Exact announced share-series/ticker tokens: 2 change rows.
- Exact share-series for full population: not proven.
- Company name alone is not used as a substitute.
- No ISIN, MIC or series value is guessed or synthesized.

## 13. Instrument Classification Assessment

The two change rows identify security/company/action but do not provide the contract's full instrument taxonomy. No complete 35-member instrument classification exists. Therefore P11 is FAIL.

## 14. Corporate-Action Visibility

The evidence proves index-rebalance ADD/DROP visibility for two rows. It does not prove a comprehensive identity-relevant corporate-action mechanism covering ticker/name/share-class/merger/spin-off/delisting/relisting/exchange move/identifier change. P12 is FAIL.

## 15. Batch, Scalability and Row-Level Reproducibility

The committed repository demonstrates a deterministic parser for a two-row change ledger. It does not demonstrate a reproducible batch pipeline for the complete governed population.

- Population batch processable from existing full-membership evidence: NO
- Identity batch processable across 35: NO
- ISIN batch processable across 35: NO
- Currentness batch processable across 35: NO
- Complete population raw-to-row traceability: NO
- Scalability: NO

## 16. Manual-Recovery Assessment

Manual Recovery: **HIGH**.

The missing evidence is not an isolated residual. Full population membership, currentness, complete identity, ISIN and share-series coverage are absent at population scale. Completing those fields from current committed artifacts would require a new full-membership evidence path or broad reconstruction. Neither is allowed in this precheck.

## 17. Failure-Loop Assessment

Failure-Loop Risk: **HIGH**.

The central issue is not that official evidence is absent; official raw evidence exists. The problem is that the committed official evidence is semantically limited to a rebalance change ledger and therefore does not close the full-population, currentness, identity and row-lineage chain required by the contract.

This most closely repeats the Korea/Taiwan/Nifty family of failures and also carries Brazil-type risk: strong authority/raw artifacts without the decisive full security-level identity chain.

## 18. PRECHECK RESULT

**PRECHECK RESULT: BLOCKED**

### Primary Blocker

**No committed qualifying full-security-level S&P/BMV IPC membership snapshot exists. The only committed direct official security evidence is a March 2026 two-row ADD/DROP rebalance change document explicitly classified by the repository as `CHANGE_LEDGER_ONLY_NOT_FULL_MEMBERSHIP`.**

### Secondary Blockers

- no qualifying current full-population as-of / currentness chain;
- no population-wide canonical identity set;
- P9 ISIN capability is WEAK for the governed population;
- exact share-series fidelity is not established population-wide;
- no full-population instrument classification;
- no comprehensive corporate-action reconciliation architecture;
- no batch full-population source-to-row pipeline;
- no population-wide row-level raw traceability;
- Manual Recovery = HIGH;
- Scalability = NO;
- Overall Failure-Loop Risk = HIGH.

## 19. Existing Concrete Recovery Path

**Existing Concrete Recovery Path: NO**

The repository contains concrete official BMV routes and a concrete rebalance-change document, but no already-documented concrete recovery path that supplies a reproducible full current membership snapshot plus currentness and population-wide identity linkage.

The existing v0.31 status says the two official changes are preserved and indicates continuation of full-source search. That is a future source-search need, not a bounded concrete recovery path already satisfying the contract. This precheck performs no such search.

## 20. Exact Next Authorized Stage

Because the result is BLOCKED:

**NEXT AUTHORIZED STAGE: S&P/BMV IPC Precheck Blocker Manager Gate — READ-ONLY / MANAGER ONLY**

This stage does not execute that manager gate and does not park MX_IPC.

## 21. No-Touch Verification

No external research was performed. No source hunt was performed. No new provider or endpoint was tested. No new external evidence was acquired. No new raw snapshot was created. No population was materialized. No ISIN recovery or individual-security research was performed. No candidate population was created. No admission or build was performed. No Universe/Membership/Research Partial/Strict/Frozen state was modified.

Unchanged:

- Research Partial = 2527
- Strict = 759
- Frozen = 0
- US-1 = 372
- US-2 = 369
- US Total = 741
- AU-1 = 153
- Usable Integrated Expansion Rows = 894
- Canada = PARKED
- Korea = PARKED
- US-3 = PARKED
- Brazil = PARKED
- Taiwan = PARKED
- Nifty 50 = PARKED

Alpha Vantage was not used.

Only this report is intended as the repository write for this stage.
