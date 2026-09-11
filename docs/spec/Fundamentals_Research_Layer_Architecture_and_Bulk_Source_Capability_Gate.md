# Fundamentals Research Layer Architecture & Bulk Source Capability Gate

## 1. Purpose

This report executes exactly the authorized stage:

**Fundamentals Research Layer Architecture & Bulk Source Capability Gate — READ-ONLY / SPEC ONLY**

The stage defines a reusable, governed Fundamentals Research Layer and the capability contract that any future bulk fundamentals source or source combination must satisfy before it may feed that layer.

It does **not** acquire fundamentals, select or integrate a provider, restart Guru Europe, rank securities, change Universe membership, create datasets, or execute any population work.

**STAGE STATUS: PASS**

**ARCHITECTURE STATUS: READY FOR SOURCE-CAPABILITY VALIDATION**

**BULK SOURCE CAPABILITY STATUS: NOT YET VALIDATED**

**Bulk Fundamentals Source Qualified: NO**

**NEXT AUTHORIZED STAGE: Fundamentals Bulk Source Qualification Gate — READ-ONLY / EVIDENCE VALIDATION ONLY**

## 2. Authorized Stage

### FACT

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Authorized stage: `Fundamentals Research Layer Architecture & Bulk Source Capability Gate — READ-ONLY / SPEC ONLY`
- Start HEAD: `e2d761d3ed70afd37411ec3f94f3857cd041472b`
- Expected start commit: `Expansion vs development priority manager gate`
- Required parent of start HEAD: `c8c39327227137ba959e8cf737e1befd59d726a4`
- Start gate: PASS

No merge, rebase, repair, alternate-head continuation, provider integration, acquisition, or execution work occurred.

## 3. Start HEAD Verification

### FACT

At stage start:

- `HEAD = e2d761d3ed70afd37411ec3f94f3857cd041472b`
- `origin/main = e2d761d3ed70afd37411ec3f94f3857cd041472b`
- commit message = `Expansion vs development priority manager gate`
- parent = `c8c39327227137ba959e8cf737e1befd59d726a4`

**Start Gate Result: PASS**

## 4. Governance Lock

### FACT

Productive trading authority remains exclusively **Welt-Swing v7.2**.

WELT-SWING-LONG remains **DEV / RESEARCH / SHADOW**.

Universe expansion remains:

**PAUSED — NOT ABANDONED**

Fixed baseline:

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

PARKED populations remain:

- Canada
- Korea
- US-3
- Brazil
- Taiwan
- India — Nifty 50
- Mexico — S&P/BMV IPC

Mandatory distinctions remain:

- Membership != Eligibility != Scan != Execution
- Research Partial != U3K
- Strict 759 != U3K
- Company != Security
- Fundamental Data != Market Data
- Fundamental Coverage != Model Eligibility
- Model Eligibility != Ranking
- Ranking != Trading Decision

No baseline or state above is changed by this stage.

## 5. Strategic Context

### FACT

The preceding strategic manager gate concluded:

- `STRATEGIC PRIORITY DECISION: B — TEMPORARILY PAUSE EXPANSION AND PRIORITIZE DEVELOPMENT`
- `Expansion State: PAUSED — NOT ABANDONED`
- `Fundamentals Research Layer Priority: HIGH`
- `AUTHORIZED NEXT GURU STAGE: NONE`
- fundamentals acquisition: not authorized
- provider integration: not authorized

The manager gate also concluded that adding approximately another 400–500 listings is currently **not** more valuable than improving research capability for the existing 2527-row Research Partial.

### ARCHITECTURE REQUIREMENT

The Fundamentals Research Layer must therefore be a reusable project service, not a Guru-Europe-specific truth store.

Potential future consumers include:

- Guru Europe
- Marks / Value
- Turnaround
- Long Research
- future fundamental research modules

## 6. Current Guru Status

### FACT

Binding current status:

- Universe Population: PASS
- Fundamentals Bulk Coverage: BLOCKED / NOT YET BUILT
- Legacy 25-stock ranking: LEGACY PILOT
- New STOXX Europe 600 ranking: NOT AUTHORIZED
- New Guru Top 5: NOT AUTHORIZED
- Fundamentals Research Layer: PLANNED, NOT STARTED before this architecture gate
- AUTHORIZED NEXT GURU STAGE: NONE

### ARCHITECTURE REQUIREMENT

Guru Europe may later consume this shared layer, but must not create an isolated duplicate fundamentals truth store.

This stage does not restart or re-rank Guru Europe.

## 7. Company vs Security Architecture

### ARCHITECTURE REQUIREMENT

The layer shall maintain a hard semantic boundary between economic-company data and listed-security data.

### Company-level data

Typical company-level fields include:

- revenue
- EBIT
- EBITDA
- net income
- operating cash flow
- free cash flow where calculated from company statements
- total assets
- equity
- debt
- cash
- operating and net margins
- ROIC / ROE inputs
- historical accounting periods
- company-level growth series

Company-level observations are keyed to `Company_Key` and must not be duplicated into multiple security records as if independently reported per security.

### Security-level data

Typical security-level fields include:

- `Security_Key`
- ISIN
- Primary MIC
- Primary Ticker / Local Code
- security/share class
- security type
- listing currency
- primary-listing status
- security-specific shares outstanding where applicable
- security-specific price
- market capitalization where security-specific
- liquidity / tradeability attributes
- valuation metrics that depend on security price or market capitalization

### SPEC JUDGMENT

Company fundamentals may be reused by multiple securities only through an explicit `Company_Key -> Security_Key` mapping. Reuse does not imply identical valuation, dividend economics, liquidity, voting rights, or model applicability.

## 8. Preferred-Share Governance Correction

### ARCHITECTURE REQUIREMENT

The prior Guru Europe v1.1 blanket treatment of preferred shares as automatically excluded / `NOT_APPLICABLE` is superseded.

Preferred or special share classes are **not automatically excluded**.

A preferred security may:

- share company-level fundamentals with another security of the same company;
- have distinct security-level valuation;
- have distinct liquidity;
- have distinct dividend economics;
- have distinct voting or control rights;
- require model-specific treatment.

Applicability is therefore determined by each downstream model's Minimum Data Contract and eligibility rules.

No blanket preferred-share exclusion may be reintroduced at the shared-layer level.

## 9. Architecture Layers

The target architecture contains seven conceptual layers.

### Layer A — Company Master

**Purpose:** stable economic-company identity independent of ticker/listing changes.

**Primary identity:** `Company_Key`.

**Allowed data:** canonical company name, issuer/legal-name lineage, country/domicile where governed, corporate-action lineage references, active/inactive status.

**Dependencies:** governed identity evidence.

**Outputs:** stable company identity for fundamentals observations and company-security mapping.

**Provenance:** every identity assertion must retain source and as-of lineage.

**Missing-data handling:** unresolved identity remains explicit; no ticker-based guessing.

### Layer B — Security Master / Company-Security Mapping

**Purpose:** connect listed securities to economic companies without collapsing share classes/listings.

**Primary identity:** `Security_Key`; foreign key `Company_Key`.

**Allowed data:** security identifiers, primary listing, share class, security type, currencies, effective dates, mapping status.

**Dependencies:** Company Master plus security identity evidence.

**Outputs:** governed company-security bridge for valuation and consumers.

**Provenance:** source/as-of/confidence retained per mapping assertion.

**Missing-data handling:** unresolved or ambiguous mappings remain fail-closed.

### Layer C — Raw / Source Fundamentals Observation Layer

**Purpose:** retain source observations before semantic normalization.

**Primary identity:** source observation key / `Provenance_ID` plus company/period/metric context.

**Allowed data:** original metric names, values, currencies, periods, publication metadata, source semantics.

**Dependencies:** Company Master and source qualification.

**Outputs:** immutable/traceable observation records for normalization.

**Provenance:** mandatory raw/source reference.

**Missing-data handling:** preserve source omissions as omissions; do not fabricate zeroes.

### Layer D — Normalized Fundamentals Layer

**Purpose:** convert qualified source observations into controlled canonical metrics.

**Primary identity:** `Company_Key + Normalized_Metric + Period/Period_Type + canonical revision/version`.

**Allowed data:** normalized statement metrics and canonical semantic fields.

**Dependencies:** Raw Observation Layer, normalization contract, provenance.

**Outputs:** canonical company-level time series.

**Provenance:** mandatory raw-to-normalized traceability.

**Missing-data handling:** explicit null/status semantics.

### Layer E — Derived Metrics Layer

**Purpose:** calculate controlled, versioned financial metrics from normalized fundamentals and, where necessary, governed security-level market inputs.

**Primary identity:** derived metric record with formula version, scope, as-of and required inputs.

**Allowed data:** versioned formulas and calculated outputs only.

**Dependencies:** normalized fundamentals; market/security input layer when required.

**Outputs:** model-consumable derived metrics.

**Provenance:** formula version and input references mandatory.

**Missing-data handling:** no calculation when required inputs are unavailable or semantically incompatible.

### Layer F — Model Coverage / Eligibility Layer

**Purpose:** evaluate whether each target security has enough appropriate data for each model.

**Primary identity:** `Model_ID + Model_Version + Security_Key + Research_AsOf`.

**Allowed data:** coverage status, missing fields, applicability state, identity state, model-specific eligibility flags.

**Dependencies:** Security Master, normalized/derived data, model Minimum Data Contract.

**Outputs:** explicit coverage and eligibility records.

**Provenance:** references to metric and identity states.

**Missing-data handling:** explicit `DATA_INCOMPLETE`, never silent exclusion.

### Layer G — Consumer / Ranking Layer

**Purpose:** allow approved downstream consumers to use canonical metrics, derived metrics and coverage status.

**Primary identity:** consumer/model run ID plus Security_Key.

**Allowed data:** only governed canonical/derived data and model outputs.

**Dependencies:** Layers A–F.

**Outputs:** future rankings, consensus, deep-dive queues, consumer-specific outputs.

**Provenance:** run version, model version, data snapshot and as-of required.

**Missing-data handling:** consumer must honor coverage status and may not bypass it by reading arbitrary raw source fields.

## 10. Company Master Concept

### ARCHITECTURE REQUIREMENT

`Company_Key` shall be an internal canonical identifier whose stability does not depend on ticker, exchange, current issuer display name, or a single external provider identifier.

Required properties:

- stable across ticker changes;
- stable across exchange/listing changes where the economic company remains the same;
- can map multiple securities to one company when evidence supports it;
- supports issuer renames;
- supports corporate-action lineage;
- supports multiple listings/share classes;
- can be closed/replaced when a corporate action creates a genuinely new economic entity;
- does not silently merge similarly named issuers.

No external company identifier is promoted to canonical authority merely by appearance in legacy or research data.

## 11. Security Master / Mapping Concept

### ARCHITECTURE REQUIREMENT

Conceptual fields:

- `Security_Key`
- `Company_Key`
- `ISIN`
- `Primary_MIC`
- `Primary_Ticker`
- `Local_Code` where applicable
- `Security_Name`
- `Issuer_Name`
- `Share_Class`
- `Security_Type`
- `Listing_Currency`
- `Primary_Listing_Flag`
- `Active_From`
- `Active_To`
- `Source_ID`
- `Source_AsOf`
- `Confidence`
- `Resolution_Status`

Minimum mapping statuses:

- `MAPPED`
- `IDENTITY_UNRESOLVED`
- `AMBIGUOUS`
- `INACTIVE_HISTORICAL`

Additional useful status:

- `CORPORATE_ACTION_REVIEW`

No table is populated by this stage.

## 12. Fundamentals Observation Model

### ARCHITECTURE REQUIREMENT

The canonical source/observation model is periodized and long-form; it is not defined as one monolithic spreadsheet.

Minimum conceptual fields:

- `Company_Key`
- `Metric`
- `Value`
- `Currency`
- `Period_Start` where applicable
- `Period_End`
- `Period_Type`
- `Fiscal_Year`
- `Fiscal_Quarter` where applicable
- `Report_Date`
- `Publication_Date` where available
- `Source_ID`
- `Source_AsOf`
- `Provenance_ID`
- `Confidence`
- `Normalization_Status`
- revision/restatement indicator where available

Supported conceptual `Period_Type` values include:

- `FY`
- `TTM`
- `INTERIM`
- `QUARTER`
- `LTM` only if separately and explicitly defined
- `POINT_IN_TIME` for balance-sheet observations where appropriate

Different metrics may require different period semantics; no universal period coercion is allowed.

## 13. Normalization Contract

### ARCHITECTURE REQUIREMENT

Normalization must be explicit and reversible through provenance.

### Currency

Store original currency and normalized currency separately. Currency conversion, if later authorized, must retain FX source, FX date/as-of and transformation lineage.

### Units

Original units must be retained. Canonical units may be standardized only with explicit scale transformation.

### Sign convention

Canonical sign conventions must be metric-specific and documented. Source sign must remain recoverable.

### Fiscal-period alignment

Calendar periods must not be assumed. Fiscal year/quarter boundaries must be retained.

### TTM vs FY

TTM must be independently identified or deterministically calculated from compatible periods. FY and TTM may not be silently substituted.

### Interim vs annual

Interim values remain distinct unless an explicitly versioned derivation is defined.

### Restatements

Restated and originally reported values must be distinguishable. Canonical latest and point-in-time views must not overwrite historical knowledge states.

### Missing values

Missing is null plus reason/status where available; it is not zero.

### Not meaningful values

Use explicit semantic state rather than arbitrary numeric sentinel values.

### Zero vs null

A reported zero is a value. Null means unavailable/not reported/not applicable according to explicit status.

### Accounting-standard differences

Do not force semantically non-equivalent line items into one metric merely because labels look similar. Semantic uncertainty must remain visible.

### Corporate-action effects

Per-share and share-count series require effective-date and security mapping controls.

### Discontinued operations

Where a source distinguishes them, preserve the distinction. Do not silently recombine.

### Source disagreement

Conflicts are governed by the multi-source conflict contract; no silent averaging.

## 14. Provenance Contract

### ARCHITECTURE REQUIREMENT

Every canonical fundamental observation must be traceable to its source evidence.

Minimum provenance fields:

- `Source_ID`
- `Source_Name`
- `Source_Type`
- `Source_AsOf`
- `Retrieval_AsOf` when future acquisition is authorized
- `Publication_Date` where available
- `Original_Metric_Name`
- `Normalized_Metric_Name`
- `Original_Value`
- `Normalized_Value`
- `Original_Currency`
- `Normalized_Currency`
- `Period`
- `Period_Type`
- `Transformation`
- `Confidence`
- `Raw_Artifact_Reference` where applicable
- `Provenance_ID`

The layer must support deterministic raw/source-to-normalized traceability without requiring every provider to use the same physical file format.

## 15. Metric Taxonomy

### ARCHITECTURE REQUIREMENT

The taxonomy is controlled and versioned. It distinguishes:

- **SOURCE METRIC** — exactly what the source reports/describes;
- **NORMALIZED METRIC** — canonical semantic mapping of a source metric;
- **DERIVED METRIC** — calculated from one or more governed inputs.

Minimum metric families:

1. Income Statement
2. Balance Sheet
3. Cash Flow
4. Profitability
5. Growth
6. Capital Efficiency
7. Leverage
8. Valuation Inputs
9. Shareholder Returns
10. Per-Share Metrics
11. Market-Linked Metrics

Derived values must never masquerade as source-reported values.

## 16. Derived-Metric Governance

### ARCHITECTURE REQUIREMENT

Every derived metric record/class requires:

- metric name and version;
- formula version;
- required inputs;
- input scope: company vs security;
- period alignment rule;
- currency alignment rule;
- calculation timestamp;
- calculation/research as-of;
- missing-input behavior;
- semantic applicability rule;
- provenance references to all inputs.

Examples that may later exist include FCF, Net Debt, ROIC, FCF Margin, Revenue Growth, EPS Growth, EV/EBITDA, P/E, P/FCF and FCF Yield.

This stage does not freeze final formulas for any downstream model.

## 17. Model-Specific Minimum Data Contract

### ARCHITECTURE REQUIREMENT

No universal giant data matrix is required before any model can operate.

Every downstream model must define a versioned Minimum Data Contract containing at minimum:

- `Model_ID`
- `Model_Version`
- `Required_Metrics`
- `Optional_Metrics`
- `Required_Periods`
- `Minimum_History`
- `Applicable_Sectors`
- `Special_Sector_Rules`
- `Security_Level_Requirements`
- `Missing_Data_Rule`
- `Eligibility_Rule`
- `Coverage_Status`

A model may require fewer or different fields than another model. Shared storage does not imply shared eligibility logic.

## 18. Coverage Status Contract

### ARCHITECTURE REQUIREMENT

Required statuses:

- `SCORED`
- `DATA_INCOMPLETE`
- `NOT_APPLICABLE`
- `IDENTITY_UNRESOLVED`

Recommended additional statuses:

- `SOURCE_CONFLICT`
- `PERIOD_INCOMPATIBLE`
- `QUALITY_REVIEW`

`DATA_INCOMPLETE` and `NOT_APPLICABLE` are semantically different and must never be conflated.

`SCORED` means the model's own Minimum Data Contract and applicability rules were satisfied for the stated version and as-of. It does not mean trading approval.

## 19. Sector-Specific Applicability

### ARCHITECTURE REQUIREMENT

The shared layer stores canonical data; models govern sector applicability.

At minimum future model contracts must explicitly address:

### Banks

Debt and leverage semantics differ from industrial companies; Net Debt / EBITDA and enterprise-value constructs may be inappropriate. Capital, book-value and regulatory balance-sheet measures may be more relevant.

### Insurance

Industrial leverage and operating cash-flow interpretations may be misleading; book value, capital adequacy and underwriting/investment semantics may require specialized rules.

### REITs / Property

FFO, NAV-oriented concepts and property-specific balance-sheet/earnings semantics may be relevant; generic industrial cash-flow/earnings measures may need model-specific applicability rules.

### Financial Services

Business-model and balance-sheet structure can invalidate ordinary industrial valuation ratios.

### Utilities

Capital intensity, regulated returns and debt structures may require special treatment where a model depends heavily on industrial comparables.

### SPEC JUDGMENT

The architecture does not solve sector models here. It provides an explicit place for sector applicability, `NOT_APPLICABLE`, and specialized metric requirements.

## 20. Coverage Target Principle

### ARCHITECTURE REQUIREMENT

The target is **100% COVERAGE STATUS**, not 100% scored.

For every target security in every target model population, the process must end with an explicit status such as:

- `SCORED`
- `DATA_INCOMPLETE`
- `NOT_APPLICABLE`
- `IDENTITY_UNRESOLVED`

A future STOXX Europe 600 run is not required to score 600/600. It is required to account for 600/600 with explicit governed status.

The same principle applies to a 2527-row research population or any other approved population.

## 21. Reference Pipeline

### ARCHITECTURE REQUIREMENT

Target high-level pipeline:

`Population Rows`
→ `Company/Security Mapping Records`
→ `Bulk Fundamentals Snapshot`
→ `Normalized Fundamentals`
→ `Derived Metrics`
→ `Coverage Record per Model`
→ `Model-Specific Eligibility/Status`
→ `Rankings`
→ `Consensus`
→ `Deep Dives`
→ `Downstream Consumer Output`

Conceptual STOXX Europe 600 example:

`600 Population Rows`
→ `600 Company/Security Mapping Records`
→ `Bulk Fundamentals Snapshot`
→ `600 Coverage Records per Model`
→ `Model-Specific Eligibility/Status`
→ `Rankings`
→ `Consensus`
→ `Deep Dives`
→ `Guru Europe Top 5`

No step in this pipeline is executed by this stage.

## 22. Bulk Source Capability Gate

### ARCHITECTURE REQUIREMENT

Any future source or governed source combination must be evaluated against the following reusable capability dimensions before it may feed population-wide fundamentals.

1. Batch / bulk capability
2. Population-wide scalability
3. Reproducibility
4. Historical-period availability
5. Metric semantics clarity
6. FY / TTM / interim distinction
7. Currency handling
8. Company/security identity support
9. Source-as-of / publication timing
10. Provenance
11. Missing-data behavior
12. Sector breadth
13. Restatement handling if observable
14. Corporate-action robustness
15. Licensing / usage constraints where repository evidence supports assessment
16. Automation feasibility
17. Rate-limit / throughput constraints where known from committed evidence
18. Failure-loop risk
19. Ability to produce deterministic coverage results
20. Suitability for repeated refreshes

### Gate logic

A future qualification result must be evidence-based and fail-closed. A source that cannot support population-scale, reproducible and identity-safe acquisition cannot be classified as a qualified bulk source merely because it works for a handful of companies.

## 23. Source Classification

### ARCHITECTURE REQUIREMENT

Future source capability statuses:

- `QUALIFIED_BULK_SOURCE`
- `CONDITIONALLY_QUALIFIED`
- `DEEP_DIVE_ONLY`
- `IDENTITY_CROSSCHECK_ONLY`
- `NOT_QUALIFIED`
- `UNKNOWN_NOT_TESTED`

Rules:

- A source suitable for individual company research is not automatically a bulk source.
- A source used for identity crosscheck is not automatically canonical Universe identity authority.
- A provider useful for Guru deep dives is not automatically acceptable for population-wide fundamentals.
- Previously mentioned external candidates remain only repository-evidenced candidates unless their committed evidence satisfies the gate.

## 24. Existing Source Evidence Boundary

### FACT

The repository contains extensive governance experience for source authority, provenance, mapping, reproducibility, batch data handling and fail-closed qualification in Universe/market-data work. The current strategic report also records that fundamentals are not yet integrated as a bulk capability.

No committed evidence reviewed in this architecture stage proves that a specific fundamentals provider already satisfies all twenty Bulk Source Capability dimensions at population scale.

### SPEC JUDGMENT

Accordingly:

- repository-known fundamentals/identity candidates, if mentioned elsewhere, remain **REPOSITORY-EVIDENCED CANDIDATE / NOT YET QUALIFIED** unless a later source-qualification gate proves otherwise;
- no provider is promoted to canonical authority here;
- no provider endpoint, website, API or dataset is tested here.

## 25. Individual Research Boundary

### ARCHITECTURE REQUIREMENT

Individual web/company research may later be used for:

- finalist deep dives;
- residual exception resolution;
- manual validation;
- qualitative confirmation.

It must not substitute for population-wide bulk coverage.

A process that manually researches a few dozen companies cannot claim a full-universe fundamentals ranking.

The legacy 25-stock Guru Europe ranking therefore remains **LEGACY PILOT** and must not be described as a STOXX Europe 600 ranking, full-universe ranking or current Guru Europe Top 5.

## 26. Bulk Snapshot Contract

### ARCHITECTURE REQUIREMENT

A future Bulk Fundamentals Snapshot must expose at minimum:

- `Snapshot_ID`
- `Target_Population_ID`
- `Population_AsOf`
- `Source_Set`
- `Source_AsOf`
- `Acquisition_AsOf`
- `Company_Count`
- `Security_Count`
- `Metric_Count`
- `Period_Coverage`
- `Currency_Coverage`
- `Sector_Coverage`
- `Mapped_Count`
- `Unmapped_Count`
- `Complete_Count`
- `Partial_Count`
- `Missing_Count`
- `Provenance_Status`
- `Reproducibility_Status`
- `Refresh_Status`

Recommended additional fields:

- source qualification version;
- normalization-contract version;
- identity snapshot reference;
- raw artifact manifest reference where applicable.

No snapshot is created by this stage.

## 27. Currentness / Point-in-Time Governance

### ARCHITECTURE REQUIREMENT

The layer must distinguish:

- Report Period
- Publication Date
- Source As-Of
- Retrieval/Acquisition As-Of
- Research As-Of

`Latest known value` is not equivalent to `value known at a historical research date`.

Where feasible, the architecture must retain revisions and publication timing sufficient to reconstruct point-in-time research states later.

## 28. Look-Ahead Bias Control

### ARCHITECTURE REQUIREMENT

Historical/backtest use may consume only information that was available by the relevant `Research_AsOf`.

Fiscal period end alone is insufficient. Publication availability controls historical visibility.

Restatements must not retroactively overwrite the historical information set without preserving original/revision lineage.

This architecture is point-in-time compatible; it does not implement a backtester.

## 29. Market-Data Boundary

### ARCHITECTURE REQUIREMENT

The Fundamentals Research Layer does not become the owner of ordinary market-data features such as:

- price
- volume
- ATR
- technical indicators
- intraday quotes
- liquidity history

These remain in market/price/liquidity architecture.

Where a valuation metric requires market data, the derived record must reference:

- exact `Security_Key`;
- price/market input source;
- price as-of;
- currency;
- calculation timestamp/as-of;
- company-level accounting inputs used.

## 30. Company-Security Valuation Boundary

### ARCHITECTURE REQUIREMENT

Metrics dependent on a listed security's price or market capitalization are not pure company fundamentals.

Examples:

- P/E
- P/B
- P/FCF
- Dividend Yield
- Market Cap
- Enterprise Value where market capitalization is an input

The derived record must explicitly combine:

1. company-level accounting inputs; and
2. security-level market inputs.

The architecture must preserve which security/share class supplied the market component.

## 31. Refresh Model

### ARCHITECTURE REQUIREMENT

Future refresh modes:

### FULL REFRESH
Rebuild qualified source coverage for the target population/as-of under a new snapshot ID.

### INCREMENTAL REFRESH
Acquire only newly available periods/publications while preserving previous observations and provenance.

### RESTATEMENT UPDATE
Add revised statements as new revisions without destroying the historical published state.

### IDENTITY UPDATE
Update company/security mapping lineage while retaining historical mappings.

### CORPORATE ACTION UPDATE
Record merger, spin-off, rename, share-class/listing or issuer-structure changes affecting identity and valuation continuity.

No refresh jobs are implemented here.

## 32. Data-Quality Dimensions

### ARCHITECTURE REQUIREMENT

Quality is multi-dimensional and may not be collapsed into one opaque score.

Required dimensions:

- Completeness
- Currentness
- Consistency
- Identity Confidence
- Period Alignment
- Currency Integrity
- Provenance Completeness
- Reproducibility
- Semantic Confidence

A consumer may impose minimum thresholds by dimension, but must preserve the underlying states.

## 33. Manual-Recovery Rule

### ARCHITECTURE REQUIREMENT

Manual recovery is acceptable only for small, bounded residual exception sets.

It must not be the primary mechanism for population-wide mapping, metric recovery or period reconstruction.

If residual manual work is structurally high, the source/source combination cannot be considered scalable bulk infrastructure.

Manual exceptions must remain identifiable, auditable and excluded from false full-coverage claims.

## 34. Multi-Source Governance

### ARCHITECTURE REQUIREMENT

Multiple sources are permitted only under governed roles:

- **Primary Source** — canonical normal source for a metric/population scope after qualification;
- **Secondary Fallback** — used under explicit missing-data rules;
- **Crosscheck Source** — validates identity/value semantics but does not silently overwrite primary data;
- **Deep-Dive Source** — may support finalist analysis but not bulk canonical coverage unless separately qualified.

Rules:

- source combination must not create uncontrolled semantic mixing;
- role is metric/family/sector scoped where necessary;
- fallback activation is explicit and provenance-visible;
- no silent source priority;
- no silent averaging.

## 35. Source-Conflict Handling

### ARCHITECTURE REQUIREMENT

Minimum conflict statuses:

- `SOURCE_AGREEMENT`
- `SOURCE_CONFLICT`
- `SEMANTIC_MISMATCH`
- `PERIOD_MISMATCH`
- `CURRENCY_MISMATCH`
- `RESTATEMENT_DIFFERENCE`
- `UNRESOLVED`

Conflict resolution must cite source role, period, publication timing, metric semantics and transformation history.

Unresolved conflict remains explicit and may cause model `DATA_INCOMPLETE` or `QUALITY_REVIEW` depending on the model contract.

## 36. Consumer Contract

### ARCHITECTURE REQUIREMENT

Downstream consumers receive only governed interfaces containing:

- canonical normalized metrics;
- versioned derived metrics;
- model coverage status;
- provenance references;
- identity state;
- data-quality state;
- snapshot/as-of metadata.

Consumers must not bypass the canonical layers by reading arbitrary raw provider fields directly for scoring/ranking.

Consumer-specific transformations must be versioned and remain downstream of the shared canonical layer.

## 37. Guru Europe Future Integration

### ARCHITECTURE REQUIREMENT

Guru Europe must consume the generic Fundamentals Research Layer.

Future conceptual flow:

`EU_STOXX600 population`
→ `Company/Security Mapping`
→ `Fundamentals Research Layer`
→ `Guru model coverage records`
→ `four model-specific eligibility/scoring flows`
→ `model rankings`
→ `consensus`
→ `deep dives`
→ `Guru Europe Top 5`

Guru Europe may define model-specific Minimum Data Contracts and scoring, but not its own independent fundamentals truth store.

No stock is scored here.

## 38. Marks / Value Future Integration

### ARCHITECTURE REQUIREMENT

Marks/Value shall reuse the same canonical normalized and derived fundamentals while retaining its own:

- Minimum Data Contract;
- eligibility rules;
- sector applicability;
- derived-metric requirements;
- ranking logic;
- coverage statuses.

No Marks/Value model is implemented by this stage.

## 39. Turnaround Future Integration

### ARCHITECTURE REQUIREMENT

Turnaround may later consume shared company-level series such as:

- historical fundamentals;
- margin direction;
- cash-flow direction;
- balance-sheet improvement;
- earnings trend;
- debt trajectory.

This remains research input only. It does not alter productive Turnaround trading rules, stop logic, execution logic or Welt-Swing v7.2 authority.

## 40. Long Research Future Integration

### ARCHITECTURE REQUIREMENT

Long Research may reuse:

- company history;
- fundamental history;
- valuation history;
- quality metrics;
- growth metrics;
- capital-efficiency metrics.

It must not require separate duplicate acquisition of data already canonically available in the shared layer.

## 41. Architecture Status

### SPEC JUDGMENT

The architecture defined by this report is coherent and reusable across multiple consumers because it establishes:

- Company/Security separation;
- stable Company and Security identity concepts;
- periodized observations;
- normalization and provenance contracts;
- controlled metric taxonomy;
- versioned derived-metric governance;
- model-specific Minimum Data Contracts;
- explicit coverage statuses;
- sector-specific applicability controls;
- point-in-time/look-ahead controls;
- market-data valuation boundaries;
- refresh and quality models;
- bounded manual recovery;
- multi-source and conflict governance;
- consumer interfaces;
- a reusable Bulk Source Capability Gate.

**ARCHITECTURE STATUS: READY FOR SOURCE-CAPABILITY VALIDATION**

This is an architecture result only. It is not a source qualification, acquisition authorization or production approval.

## 42. Bulk Source Capability Status

### FACT

No new provider research, endpoint testing, live API call, website browsing, download or trial dataset was performed.

Existing repository evidence does not prove that a specific fundamentals source already satisfies the full Bulk Source Capability Contract defined here.

### SPEC JUDGMENT

**BULK SOURCE CAPABILITY STATUS: NOT YET VALIDATED**

**Bulk Fundamentals Source Qualified: NO**

A separate evidence-validation gate is required before any source can be promoted to `QUALIFIED_BULK_SOURCE` or `CONDITIONALLY_QUALIFIED`.

## 43. Exact Next Authorized Stage

Because:

- `ARCHITECTURE STATUS = READY FOR SOURCE-CAPABILITY VALIDATION`; and
- no bulk fundamentals source is qualified;

the exactly authorized next stage is:

**Fundamentals Bulk Source Qualification Gate — READ-ONLY / EVIDENCE VALIDATION ONLY**

Boundary of that future gate:

- may assess already repository-evidenced source candidates against this contract;
- may classify source capability;
- must not automatically authorize population-wide download;
- must not build a bulk fundamentals dataset;
- must not integrate a provider;
- must not restart Guru Europe;
- must not run rankings;
- must not change Universe membership.

Any acquisition/build/integration step requires separate explicit later authorization.

## 44. No-Touch Verification

### FACT

This stage performed:

- External Research: NO
- New Provider Search: NO
- Provider Endpoint Testing: NO
- Fundamentals Acquisition: NO
- Bulk Dataset Build: NO
- Provider Integration: NO
- Guru Restart: NO
- Guru Ranking: NO
- Population Selection: NO
- Population Precheck: NO
- Parked Population Recovery: NO
- Universe Write: NO
- Membership Write: NO
- Research Partial Write: NO
- Strict Write: NO
- Frozen Write: NO
- Code Modification: NO
- CSV/JSON/XLSX creation: NO

Authorization states after this stage:

- Universe Expansion: `PAUSED — NOT ABANDONED`
- Research Partial: `2527`
- Strict: `759`
- Frozen: `0`
- AUTHORIZED NEXT GURU STAGE: `NONE`
- Guru Restart: `NOT AUTHORIZED`
- Fundamentals Acquisition: `NOT AUTHORIZED`
- Provider Integration: `NOT AUTHORIZED`
- Bulk Dataset Build: `NOT AUTHORIZED`
- Universe Write: `NOT AUTHORIZED`

PARKED states remain unchanged:

- Canada — PARKED
- Korea — PARKED
- US-3 — PARKED
- Brazil — PARKED
- Taiwan — PARKED
- India — Nifty 50 — PARKED
- Mexico — S&P/BMV IPC — PARKED

Only this architecture report is written by the stage.

---

## Final Gate State

- Company/Security Separation Defined: YES
- Periodized Fundamentals Model Defined: YES
- Provenance Contract Defined: YES
- Metric Taxonomy Defined: YES
- Derived-Metric Governance Defined: YES
- Model Minimum-Data Contract Defined: YES
- Coverage Status Contract Defined: YES
- Sector-Specific Applicability Defined: YES
- Preferred-Share Blanket Exclusion Superseded: YES
- Bulk Source Capability Contract Defined: YES
- Point-in-Time / Look-Ahead Controls Defined: YES
- Multi-Source Conflict Governance Defined: YES
- 100% Coverage-Status Principle Defined: YES
- ARCHITECTURE STATUS: READY FOR SOURCE-CAPABILITY VALIDATION
- BULK SOURCE CAPABILITY STATUS: NOT YET VALIDATED
- Bulk Fundamentals Source Qualified: NO
- Fundamentals Acquired: NO
- Bulk Dataset Built: NO
- Provider Integrated: NO
- Guru Restart Authorized: NO
- AUTHORIZED NEXT GURU STAGE: NONE
- Universe Write: NO
- NEXT AUTHORIZED STAGE: `Fundamentals Bulk Source Qualification Gate — READ-ONLY / EVIDENCE VALIDATION ONLY`

HARD STOP after commit and post-commit verification.
