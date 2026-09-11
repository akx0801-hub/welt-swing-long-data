# Fundamentals Bulk Acquisition & Mapping Design Gate

## 1. Purpose

### QUALIFIED FACT

This report executes exactly the authorized stage:

**Fundamentals Bulk Acquisition & Mapping Design Gate — READ-ONLY / SPEC ONLY — PREFERRED QUALIFIED PATH ONLY — NO DATA ACQUISITION**

The preferred qualified path is locked to **LSEG Company Fundamentals / Worldscope**. The objective is to translate the already-approved generic Fundamentals Research Layer architecture into a concrete LSEG-oriented acquisition, identity-mapping, raw-observation, snapshot, provenance, normalization, data-quality, refresh, failure/recovery and pilot design.

This report acquires no fundamentals, calls no live fundamentals endpoint, downloads no provider dataset, creates no provider account, uses no credentials, integrates no provider, builds no mapping or fundamentals dataset, restarts no Guru workflow and changes no Universe state.

**STAGE STATUS: PASS**

**DESIGN STATUS: A — READY FOR PRE-ACQUISITION VALIDATION**

**CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED**

**LICENSING CONDITION STATUS: UNRESOLVED**

**PRE-ACQUISITION STATUS: BLOCKED**

**NEXT AUTHORIZED STAGE: LSEG Fundamentals Pre-Acquisition Licensing & Entitlement Validation Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO DATA ACQUISITION**

## 2. Authorized Stage

### QUALIFIED FACT

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Authorized stage: `Fundamentals Bulk Acquisition & Mapping Design Gate — READ-ONLY / SPEC ONLY — PREFERRED QUALIFIED PATH ONLY — NO DATA ACQUISITION`
- Expected start HEAD: `8d6da30038d462301193ffefce14749cf85c6de3`
- Expected start commit: `Fundamentals bulk source qualification v2 gate`
- Required parent: `9519b0729f9c92c8a5986980dbcdaa426def0bf6`
- Provider lock: LSEG Company Fundamentals / Worldscope only
- EODHD: qualified runner-up / inactive
- FactSet: conditionally qualified / inactive
- Acquisition: prohibited
- Integration: prohibited
- Guru restart: prohibited
- Universe write: prohibited

## 3. Start HEAD Verification

### QUALIFIED FACT

At stage start and immediately before the only repository write:

- `HEAD = 8d6da30038d462301193ffefce14749cf85c6de3`
- `origin/main = 8d6da30038d462301193ffefce14749cf85c6de3`
- commit message = `Fundamentals bulk source qualification v2 gate`
- parent = `9519b0729f9c92c8a5986980dbcdaa426def0bf6`

**Start Gate Result: PASS**

No merge, rebase, repair or alternate-head continuation was performed.

## 4. Fixed Baseline

### QUALIFIED FACT

| Measure | State |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| Universe Expansion | PAUSED — NOT ABANDONED |
| Preferred Fundamentals Source | LSEG Company Fundamentals / Worldscope |
| Qualified Runner-Up | EODHD Fundamentals + Bulk Fundamentals API |
| FactSet | CONDITIONALLY_QUALIFIED |

No baseline or provider-governance state above changes in this stage.

## 5. Normative Inputs

### ARCHITECTURE REQUIREMENT

The following repository documents are normative:

1. `docs/spec/Fundamentals_Research_Layer_Architecture_and_Bulk_Source_Capability_Gate.md`
2. `docs/spec/Fundamentals_Bulk_Source_Qualification_Gate.md`
3. `docs/spec/Fundamentals_Bulk_Source_Discovery_Manager_Gate.md`
4. `docs/spec/Fundamentals_Bounded_External_Source_Discovery.md`
5. `docs/spec/Fundamentals_Bulk_Source_Qualification_v2_Gate.md`

The qualification v2 report is authoritative for provider selection, qualification findings, strengths and residual conditions. This stage does not reopen provider selection or source discovery.

## 6. Provider Lock

### QUALIFIED FACT

Technical design is performed only for:

**LSEG Company Fundamentals / Worldscope**

EODHD remains `QUALIFIED RUNNER-UP / INACTIVE`. FactSet remains `CONDITIONALLY_QUALIFIED / INACTIVE`.

### ARCHITECTURE REQUIREMENT

No EODHD or FactSet acquisition path, connector, fallback ingestion or multi-provider blending is designed here. If the preferred LSEG path later fails a hard manager condition, governance returns to a manager gate rather than auto-activating another provider.

## 7. Known Qualification State

### QUALIFIED FACT

The qualification v2 gate established LSEG as `QUALIFIED_BULK_SOURCE` and preferred path. It established strong evidence for:

- global Company Fundamentals coverage;
- standardized and as-reported financial statements;
- deep history;
- annual and interim data;
- point-in-time support;
- bulk/database delivery;
- deterministic incremental updates;
- reference/symbology support including LSEG permanent identifiers and, subject to licensing, identifiers such as ISIN, CUSIP and SEDOL;
- broad sector support including REIT data and industry-specific metrics;
- machine-readable data dictionaries and entity relationships.

### OFFICIAL EXTERNAL EVIDENCE

LSEG's current Company Fundamentals DaaS user guide states that the service uses a common data model, supports hosted SQL or bulk-file distribution, delivers database updates every two hours and bulk-feed updates every three hours, publishes weekly initialization files, provides full-depth fundamentals history, and supports mapping through LSEG permanent identifiers plus third-party identifiers such as CUSIP, SEDOL and ISIN where licenses permit. It also states that product data dictionaries, column definitions and ERDs are accessible through Data Discovery and that delivery is entitlement-dependent.

Source: `https://developers.lseg.com/content/dam/devportal/api-families/lseg-data-platform/data-as-a-service/userguides/fundamentals/LSEGDataasaServiceFundamentalsuserguide.pdf`, document version 100.02, research date 2026-09-11.

LSEG's Company Fundamentals DaaS service-description addendum states that curated content may be accessed through bulk feeds or the integrated normalized database, may be integrated into proprietary models and customer applications, includes standardized and as-reported statements, and carries global coverage.

Source: `https://developers.lseg.com/content/dam/devportal/api-families/lseg-data-platform/data-as-a-service/userguides/fundamentals/Service_Description_AddendumDaaSFundamentals.pdf`, research date 2026-09-11.

## 8. Pre-Acquisition Hard Conditions

### ARCHITECTURE REQUIREMENT

Two residual conditions from qualification v2 are elevated to mandatory **PRE-ACQUISITION HARD CONDITIONS**:

1. Currency semantics and preservation.
2. Licensing / usage / entitlement governance.

A complete technical design does not imply acquisition authorization while either condition blocks safe acquisition.

### DESIGN DECISION

No pilot acquisition may be authorized unless:

- `LICENSING CONDITION STATUS = RESOLVED`; and
- currency semantics are sufficiently resolved to ensure raw values can be interpreted, preserved and normalized without ambiguity.

## 9. Target Population Contract

### ARCHITECTURE REQUIREMENT

The Fundamentals layer consumes a governed research population and never redefines Universe membership.

### DESIGN DECISION

Define a generic population reference object keyed by `Target_Population_ID`, not by a hard-coded STOXX Europe 600 assumption.

Conceptual minimum fields:

- `Population_ID`
- `Population_AsOf`
- `Security_Key`
- `ISIN`
- `Primary_MIC`
- `Primary_Ticker`
- `Security_Name`
- `Company_Key` if already resolved
- `Share_Class`
- `Security_Type`
- `Listing_Currency`
- `Active_Flag`

Potential future values include `EU_STOXX600`, `RESEARCH_PARTIAL_2527`, or another explicitly authorized research population. Population identity is immutable for each acquisition run through `Population_AsOf` plus a version/reference.

## 10. Company/Security Mapping Contract

### ARCHITECTURE REQUIREMENT

Company fundamentals attach canonically to `Company_Key`; security-specific market/valuation data attach to `Security_Key`.

### DESIGN DECISION

Define a mapping record with at least:

- `Mapping_ID`
- `Company_Key`
- `Security_Key`
- `ISIN`
- `Primary_MIC`
- `Primary_Ticker`
- `Local_Code`
- `Security_Name`
- `Issuer_Name`
- `Share_Class`
- `Security_Type`
- `Listing_Currency`
- `Primary_Listing_Flag`
- `LSEG_Company_ID`
- `LSEG_Security_ID`
- `Worldscope_ID`
- `Other_LSEG_Identifier` where documented and needed
- `Mapping_Source`
- `Mapping_AsOf`
- `Mapping_Method`
- `Mapping_Confidence`
- `Mapping_Status`
- `Valid_From`
- `Valid_To`

Exact LSEG physical field names are intentionally not invented. Where public documentation establishes only identifier families rather than exact table-column names, this report uses conceptual fields pending entitled data-dictionary validation.

### DESIGN DECISION — Mapping Status Contract

Minimum statuses:

- `MAPPED`
- `IDENTITY_UNRESOLVED`
- `AMBIGUOUS`
- `MULTIPLE_CANDIDATES`
- `INACTIVE_HISTORICAL`
- `SECURITY_MAPPED_COMPANY_UNRESOLVED`
- `COMPANY_MAPPED_SECURITY_UNRESOLVED`
- `NOT_COVERED_BY_SOURCE`

No fuzzy automatic acceptance is permitted.

## 11. Deterministic Mapping Hierarchy

### DESIGN DECISION

Mapping order:

1. Existing governed internal-to-LSEG stable identifier mapping with valid effective date.
2. Exact ISIN match where entitlement and source terms permit use.
3. Exact provider security identifier crosswalk already linked to the same canonical `Security_Key`.
4. Exact `Primary_MIC + Primary_Ticker + Share_Class` match with issuer/company corroboration.
5. Exact company-level crosswalk using LSEG permanent company identifier plus governed security relation.
6. Controlled manual exception review for a small bounded residual set.

### DESIGN DECISION — Tie Break / Ambiguity

If more than one provider security or company remains plausible after a deterministic step, mapping becomes `MULTIPLE_CANDIDATES` or `AMBIGUOUS`; no downstream fundamentals record becomes canonical until resolved.

Company name alone is never sufficient canonical identity.

## 12. Multi-Listing / Share-Class Governance

### ARCHITECTURE REQUIREMENT

The design must preserve multiple listings, share classes, preferred/special shares, ADR/GDRs, dual listings, primary/secondary listing distinctions, renames and ticker changes.

### DESIGN DECISION

- Company accounting fundamentals are stored once at `Company_Key` scope unless the source observation is genuinely security-specific.
- Multiple securities may map to one company without duplicating company fundamentals as independent observations.
- Preferred/special shares are not automatically excluded.
- ADR/GDR and secondary listings remain distinct `Security_Key` records.
- Primary-listing selection remains a Universe/security governance function, not a Fundamentals provider decision.
- Security-specific valuation and market inputs remain separate from company fundamentals.

## 13. Raw Observation Contract

### DESIGN DECISION

Conceptual Raw / Source Fundamentals Observation fields:

- `Observation_ID`
- `Snapshot_ID`
- `Company_Key`
- `Security_Key` where source/security-specific
- `Provider_Company_ID`
- `Provider_Security_ID`
- `Metric_Source_Name`
- `Metric_Source_Code`
- `Original_Value`
- `Original_Currency`
- `Period_Start`
- `Period_End`
- `Period_Type`
- `Fiscal_Year`
- `Fiscal_Quarter`
- `Report_Date`
- `Publication_Date`
- `Source_AsOf`
- `Retrieval_AsOf`
- `Restatement_Status`
- `Source_ID`
- `Provenance_ID`
- `Raw_Reference`
- `Ingestion_Status`

### ARCHITECTURE REQUIREMENT

Raw observations preserve provider semantics before normalization. Missing data is never fabricated as zero.

## 14. Period Contract

### DESIGN DECISION

Supported conceptual period types:

- `FY`
- `QUARTER`
- `INTERIM`
- `TTM`
- `POINT_IN_TIME`

`TTM` must include a derivation/source flag:

- `SOURCE_REPORTED_TTM`
- `INTERNALLY_DERIVED_TTM`

Internal TTM derivation is permitted only from compatible governed periods and with formula/version provenance. No universal period coercion is allowed.

## 15. Snapshot Contract

### DESIGN DECISION

Future Bulk Fundamentals Snapshot manifest:

- `Snapshot_ID`
- `Provider`
- `Provider_Product`
- `Target_Population_ID`
- `Population_AsOf`
- `Source_AsOf`
- `Acquisition_AsOf`
- `Retrieval_AsOf`
- `Mapping_Version`
- `Schema_Version`
- `Normalization_Version`
- `Metric_Taxonomy_Version`
- `Requested_Company_Count`
- `Requested_Security_Count`
- `Mapped_Company_Count`
- `Mapped_Security_Count`
- `Unmapped_Count`
- `Ambiguous_Count`
- `Returned_Company_Count`
- `Observation_Count`
- `Period_Coverage`
- `Currency_Coverage`
- `Sector_Coverage`
- `Completeness_Status`
- `Currentness_Status`
- `Provenance_Status`
- `Reproducibility_Status`
- `Licensing_Status`
- `Snapshot_Status`

### DESIGN DECISION — Snapshot Status Contract

- `DESIGNED`
- `ACQUISITION_BLOCKED`
- `ACQUIRED_RAW`
- `VALIDATION_FAILED`
- `VALIDATED_RAW`
- `NORMALIZATION_READY`
- `NORMALIZED`
- `REJECTED`
- `SUPERSEDED`

No real snapshot is created in this stage.

## 16. Provenance Contract

### DESIGN DECISION

Every future observation retains:

- `Provenance_ID`
- `Provider`
- `Product`
- `Delivery_Method`
- `Provider_Field`
- `Provider_Field_Definition`
- `Provider_Entity_ID`
- `Source_Period`
- `Source_Report_Date`
- `Source_Publication_Date`
- `Source_AsOf`
- `Retrieval_AsOf`
- `Raw_Artifact_Reference`
- `Transformation_ID`
- `Normalization_Version`

No normalized or derived value may lose traceability back to provider field semantics and source timing.

## 17. Raw Artifact Governance

### ARCHITECTURE REQUIREMENT

Provider raw data must not be assumed legally committable to Git or broadly redistributable.

### DESIGN DECISION

Allowed raw-artifact states:

- `RAW_ARTIFACT_RETAINED`
- `RAW_ARTIFACT_EXTERNAL_SECURE_STORAGE`
- `RAW_ARTIFACT_RETENTION_RESTRICTED`
- `RAW_ARTIFACT_NOT_PERMITTED`
- `RAW_ARTIFACT_REFERENCE_ONLY`

The actual state is selected only after licensing/entitlement validation. Raw artifact references may be metadata-only when provider terms restrict retention or repository storage.

## 18. Metric Taxonomy Mapping Contract

### DESIGN DECISION

Canonical mapping record:

- `Canonical_Metric_ID`
- `Provider_Metric_ID`
- `Provider_Metric_Name`
- `Canonical_Metric_Name`
- `Statement_Type`
- `Metric_Type`
- `Unit`
- `Currency_Behavior`
- `Period_Behavior`
- `Sector_Applicability`
- `Normalization_Rule`
- `Mapping_Status`
- `Mapping_Version`

Conceptual families:

- Income Statement
- Balance Sheet
- Cash Flow
- Profitability Inputs
- Growth Inputs
- Capital Efficiency Inputs
- Leverage Inputs
- Valuation Inputs
- Shareholder Return Inputs
- Per-Share Inputs

This stage defines the contract only; it does not create a full provider field map.

## 19. Normalization Contract

### ARCHITECTURE REQUIREMENT

Normalization must be explicit, reversible through provenance and versioned.

### DESIGN DECISION

Normalize, where appropriate, across:

- units;
- currency;
- sign convention;
- period type;
- fiscal year and quarter;
- source-reported vs internally derived TTM;
- interim periods;
- missing vs zero;
- restatements;
- discontinued operations;
- provider-standardized vs as-reported values;
- sector-specific semantics.

Always preserve `Original_Value`, `Original_Currency` and `Original_Metric`.

### DESIGN DECISION — Normalization Status

- `NORMALIZED`
- `SOURCE_AS_REPORTED`
- `DERIVED_FROM_SOURCE`
- `SEMANTIC_REVIEW_REQUIRED`
- `CURRENCY_REVIEW_REQUIRED`
- `PERIOD_REVIEW_REQUIRED`
- `SOURCE_CONFLICT`
- `NOT_APPLICABLE`
- `MISSING_SOURCE_DATA`
- `REJECTED`

## 20. Currency Normalization Design

### ARCHITECTURE REQUIREMENT

Company reporting currency must remain distinct from security trading/listing currency.

### DESIGN DECISION

Currency fields:

- `Reporting_Currency`
- `Observation_Currency`
- `Security_Trading_Currency`
- `Normalization_Currency`
- `FX_Source`
- `FX_AsOf`
- `FX_Rate`
- `FX_Method`

### DESIGN DECISION

No FX conversion is executed by acquisition. Raw data must first preserve source values and source currency.

Potential internal normalization methods are metric-dependent:

- stock/balance-sheet items: typically period-end or another explicitly governed accounting-consistent rate;
- flow/income/cash-flow items: potentially period-average or another governed method;
- report-date conversion: only when the model purpose explicitly requires it.

No universal conversion rule is frozen here.

### OFFICIAL EXTERNAL EVIDENCE

LSEG public/current DaaS documentation establishes machine-readable Company Fundamentals, standardized/as-reported variants, data dictionaries and entitled subscription views, but the exact current DaaS public documentation reviewed does not expose enough detail to prove all per-observation currency-field semantics required by this architecture.

Historical LSEG/Refinitiv technical documentation demonstrates that financial data models can distinguish reported currency, pricing currency and converted currency, including explicit exchange-rate relations. This supports the underlying capability direction but is not treated as sufficient proof of the exact current DaaS Company Fundamentals field contract.

### UNRESOLVED CONDITION

Exact current DaaS field semantics still must establish:

- original reporting/presentation currency field(s);
- whether standardized values are provider-converted;
- currency code granularity per metric/statement/period;
- behavior when reporting currency changes across periods;
- treatment of multi-currency disclosures;
- any provider-supplied conversion rate provenance.

## 21. Derived Metric Boundary

### DESIGN DECISION

Future derived metrics require:

- `Derived_Metric_ID`
- `Formula_Version`
- `Required_Inputs`
- `Input_Period_Rules`
- `Currency_Alignment_Rules`
- `Company_or_Security_Scope`
- `Calculation_AsOf`
- `Missing_Input_Behavior`
- `Sector_Applicability`

No derived metric is calculated now.

## 22. Market-Data Boundary

### ARCHITECTURE REQUIREMENT

Accounting fundamentals and market data remain separate.

### DESIGN DECISION

Metrics such as P/E, P/B, P/FCF, Dividend Yield, Market Cap and Enterprise Value must explicitly reference:

- Company accounting inputs;
- `Security_Key`;
- `Market_Data_Source`;
- `Price_AsOf`;
- market-data currency;
- `Primary_MIC`;
- `Primary_Ticker`;
- calculation timestamp/version.

Technical analysis remains outside the Fundamentals layer.

## 23. Data Quality Contract

### DESIGN DECISION

Separate DQ dimensions:

- Completeness
- Currentness
- Consistency
- Identity Confidence
- Period Alignment
- Currency Integrity
- Provenance Completeness
- Reproducibility
- Semantic Confidence

Status scale per dimension:

- `PASS`
- `WARNING`
- `FAIL`
- `UNKNOWN`

### DESIGN DECISION — Hard-Fail Conditions

Hard fail includes:

- unresolved identity ambiguity affecting canonical mapping;
- missing provenance for canonicalized values;
- unusable period semantics;
- currency ambiguity that prevents interpretation of source values;
- irreconcilable semantic/source conflict;
- licensing violation risk;
- snapshot incompleteness beyond an explicitly approved pilot/production threshold;
- schema change not yet validated.

No opaque composite score is used.

## 24. Coverage Contract

### ARCHITECTURE REQUIREMENT

Target remains **100% COVERAGE STATUS**, not 100% scored.

### DESIGN DECISION

For each `Model_ID + Model_Version + Security_Key + Research_AsOf`, future coverage states include at minimum:

- `SCORED`
- `DATA_INCOMPLETE`
- `NOT_APPLICABLE`
- `IDENTITY_UNRESOLVED`

Additional states may include `SOURCE_CONFLICT`, `PERIOD_INCOMPATIBLE` or `QUALITY_REVIEW` if already governed by the shared architecture. This stage calculates no coverage.

## 25. Model Minimum-Data Interface

### DESIGN DECISION

Each downstream model declares:

- `Model_ID`
- `Model_Version`
- `Required_Metrics`
- `Optional_Metrics`
- `Required_Periods`
- `Minimum_History`
- `Applicable_Sectors`
- `Special_Sector_Rules`
- `Security_Level_Requirements`
- `Missing_Rule`
- `Eligibility_Rule`

The provider never defines model eligibility.

## 26. Sector-Specific Handling

### ARCHITECTURE REQUIREMENT

Preserve model-specific applicability for:

- Banks
- Insurance
- REITs / Property
- Other Financial Services
- Utilities where relevant

### DESIGN DECISION

Source accounting data may be shared canonically while downstream model contracts decide which metrics are meaningful. Generic industrial ratios are never forced onto sectors where their semantics are inappropriate.

## 27. Restatement Governance

### DESIGN DECISION

Event types:

- `NEW_FILING`
- `AMENDED_FILING`
- `RESTATED_HISTORICAL_PERIOD`
- `PROVIDER_CORRECTION`
- `LATE_ARRIVING_OBSERVATION`

For each new observation, processing rule determines whether it:

- supersedes the current latest view;
- coexists as a new vintage;
- requires manual/semantic review;
- triggers recalculation of downstream normalized/derived values.

Prior provenance is retained whenever licensing/storage terms permit.

## 28. Point-in-Time Governance

### QUALIFIED FACT

LSEG was qualified with strong point-in-time capability evidence.

### DESIGN DECISION

Timing fields:

- `Period_End`
- `Report_Date`
- `Publication_Date`
- `Source_AsOf`
- `Retrieval_AsOf`
- `Calculation_AsOf`

Anti-look-ahead rule:

> A model calculation at time T may use only information whose governed availability timestamp is at or before T.

### DESIGN DECISION

Current screening and historical backtesting remain distinct modes. Current screening may use current qualified/latest data with governed retrieval/publication timestamps. Historical backtests require point-in-time/vintage-preserving observations and may not substitute latest-restated history where the information was not yet available historically.

## 29. Refresh Contract

### DESIGN DECISION

Refresh types:

- `FULL`
- `INCREMENTAL`
- `RESTATEMENT`
- `IDENTITY`
- `CORPORATE_ACTION`

Conceptual triggers:

- initialization/rebaseline;
- provider incremental update arrival;
- amended/restated statement;
- identifier/entity change;
- listing/corporate-action change.

Affected layers must be revalidated selectively, not blindly rebuilt. Every refresh produces a governed run/snapshot reference and DQ state.

## 30. Reproducibility / Idempotency

### DESIGN DECISION

Repeated processing of the same:

- `Target_Population_ID + Population_AsOf`
- provider source snapshot/reference;
- `Mapping_Version`;
- `Schema_Version`;
- `Normalization_Version`;
- `Metric_Taxonomy_Version`

must yield deterministic canonical output.

Future manifests should carry immutable source references, version identifiers and hashes where actual acquired artifacts exist and licensing permits. This stage does not create hashes for nonexistent data.

## 31. Failure / Recovery Contract

### DESIGN DECISION

Fail-closed reason codes:

- `SOURCE_UNAVAILABLE`
- `AUTHORIZATION_FAILED`
- `ENTITLEMENT_FAILED`
- `SCHEMA_CHANGED`
- `IDENTITY_MAPPING_FAILED`
- `PARTIAL_DELIVERY`
- `PERIOD_SEMANTICS_FAILED`
- `CURRENCY_FAILED`
- `PROVENANCE_FAILED`
- `DQ_FAILED`
- `LICENSING_BLOCKED`
- `UNKNOWN_FAILURE`

No partial or failed acquisition becomes canonical automatically.

## 32. Partial Delivery Rule

### ARCHITECTURE REQUIREMENT

Partial acquisition != successful complete snapshot.

### DESIGN DECISION

A partial delivery is marked `PARTIAL_DELIVERY` and the snapshot cannot advance to `VALIDATED_RAW` unless the missing portion falls within an explicitly authorized bounded pilot exception and the snapshot remains clearly incomplete.

Partial data may be retained for diagnostics only when licensing permits. The target population is never silently reduced to fit what the provider returned.

## 33. Manual Recovery Rule

### DESIGN DECISION

Manual recovery is allowed only for small bounded exception sets.

Future exception records contain:

- `Exception_ID`
- target entity/security
- reason code
- mapping/source state
- review status
- reviewer/date
- resolution provenance

### DESIGN PROPOSAL

Pilot manual-recovery burden should remain a small minority of the stratified pilot. If manual exception handling becomes structural or begins to scale with population size, the pilot fails and returns to manager review.

## 34. Pilot Design

### DESIGN PROPOSAL

Recommended future bounded pilot size: **40–60 target securities**, stratified by design criteria rather than named companies.

Required strata should include:

- multiple countries/regions within the authorized target population;
- at least 4–6 reporting currencies;
- general corporates;
- banks;
- insurance;
- REIT/property;
- utilities where relevant;
- multiple listings/share classes;
- at least one preferred/special share class where population identity supports it;
- at least one ADR/GDR or cross-listing case where applicable;
- active and, if allowed by the pilot population, historical/inactive identity cases;
- issuers with long historical records;
- cases with missing fields;
- cases with observable restatement/amendment history;
- different fiscal year-ends.

The pilot is not authorized or executed by this report.

## 35. Pilot Success Criteria

### DESIGN PROPOSAL

Proposed criteria, to be ratified by a later pilot manager gate:

- deterministic mapping succeeds for the large majority of pilot rows without name-only matching;
- unresolved/ambiguous identity cases remain bounded and explicitly classified;
- raw observations preserve source metric, source value, currency, period and provenance;
- annual/interim/quarterly semantics are unambiguous for tested records;
- currency interpretation is complete enough for every acquired monetary observation used in normalization;
- provenance completeness is effectively universal for canonicalized observations;
- historical coverage satisfies the intended multi-year research horizon across strata;
- financial-sector and REIT records are structurally supported;
- rerunning the same governed pilot input produces reproducible output;
- no licensing condition is violated;
- no uncontrolled manual-recovery fanout is required.

No numerical threshold becomes binding until the manager gate approves it.

## 36. Pilot Failure Criteria

### DESIGN DECISION

Fail closed if any of the following occurs:

- licensing/entitlement remains unresolved;
- currency semantics remain unresolved for interpretation of acquired values;
- mapping is structurally weak or relies on name-only guesses;
- the bulk/database delivery mechanism contradicts qualification evidence;
- provider schema cannot support the canonical observation/provenance model;
- historical periods are materially inadequate for intended research uses;
- provenance cannot be preserved;
- manual recovery becomes excessive;
- refresh cannot be reproduced deterministically;
- point-in-time requirements cannot be honored for historical testing use cases.

Pilot failure returns to manager review. It does not activate EODHD automatically.

## 37. Runner-Up Failover Governance

### QUALIFIED FACT

EODHD remains the qualified runner-up and is inactive.

### DESIGN DECISION

Manager reconsideration triggers include:

- LSEG licensing incompatible with intended internal research/storage/derived-data use;
- LSEG acquisition technically infeasible under actual entitlement;
- LSEG mapping fails a bounded pilot structurally;
- LSEG economics later judged unacceptable by a separately authorized manager/procurement decision;
- a material contradiction emerges between qualification evidence and entitled product capability.

If triggered, return to a manager gate. No automatic failover or dual-provider implementation is permitted.

## 38. Currency Condition Assessment

### OFFICIAL EXTERNAL EVIDENCE

Current LSEG Company Fundamentals DaaS documentation establishes standardized and as-reported content, data dictionaries, provider identifiers, structured delivery and full-depth history. Historical LSEG/Refinitiv technical documentation also demonstrates explicit distinctions between reported, pricing and converted currencies and exchange-rate fields in financial-data responses.

### UNRESOLVED CONDITION

The public/current DaaS documents reviewed do not conclusively establish the exact entitled Company Fundamentals field contract for all required currency semantics, including per-observation original currency, provider-normalized/converted currency status, currency changes through time, multi-currency behavior and provider FX transformation provenance.

### DESIGN JUDGMENT

**CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED**

The remaining uncertainty affects normalization and may affect interpretation if standardized values are delivered without sufficient original-currency lineage. Therefore any future pilot manager gate must require exact entitled schema confirmation before raw observations are normalized; if raw delivered values themselves cannot be interpreted without those fields, acquisition remains blocked.

## 39. Licensing Condition Assessment

### OFFICIAL EXTERNAL EVIDENCE

LSEG public DaaS materials explicitly state that delivery is based on customer entitlement profiles. The Company Fundamentals DaaS user guide states that third-party identifiers are included only where required licenses are in place. The Reference Data and Symbology addendum explicitly notes that third-party identifiers such as CUSIP and ISIN may require third-party licenses. LSEG public materials also describe bulk feeds as a supported way for consumers to initialize and maintain local database copies and describe use in proprietary models/customer applications.

These facts establish technical capability and an entitlement-based commercial model, but they do not establish this project's exact contractual rights.

### UNRESOLVED CONDITION

Before any pilot acquisition, the project must establish from applicable official contract/service terms or equivalent authorized entitlement evidence:

- automated access permitted;
- intended internal research use permitted;
- local storage permitted;
- cache/persistence rules;
- historical storage permitted;
- creation of normalized/derived data permitted;
- internal derived metrics permitted;
- repository storage restrictions;
- redistribution restrictions;
- retention/deletion obligations;
- credential/user restrictions;
- bulk/batch entitlement;
- selected delivery mechanism covered by entitlement;
- identifier sublicense requirements relevant to the chosen mapping hierarchy.

### DESIGN JUDGMENT

**LICENSING CONDITION STATUS: UNRESOLVED**

**Acquisition Authorization: BLOCKED**

Technical accessibility is not treated as evidence of legal permission.

## 40. Design Completeness Check

| Contract | Defined |
|---|---|
| Acquisition Contract | YES |
| Mapping Contract | YES |
| Raw Observation Contract | YES |
| Snapshot Contract | YES |
| Provenance Contract | YES |
| Normalization Contract | YES |
| DQ Contract | YES |
| Refresh Contract | YES |
| Failure/Recovery Contract | YES |
| Pilot Contract | YES |
| Runner-Up Failover Governance | YES |

### DESIGN JUDGMENT

The technical design is sufficiently complete to move from architecture design to bounded resolution of pre-acquisition conditions.

## 41. DESIGN STATUS

**DESIGN STATUS: A — READY FOR PRE-ACQUISITION VALIDATION**

This means the pipeline contracts are sufficiently defined for the next validation step. It does **not** authorize data acquisition.

## 42. PRE-ACQUISITION STATUS

- `CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED`
- `LICENSING CONDITION STATUS: UNRESOLVED`

Because licensing is unresolved, the mandatory licensing-before-pilot rule blocks acquisition.

**PRE-ACQUISITION STATUS: BLOCKED**

**Pilot Acquisition Authorized: NO**

## 43. Exact Next Authorized Stage

Because `DESIGN STATUS = A` and `PRE-ACQUISITION STATUS = BLOCKED`, with licensing/entitlement as the highest-priority unresolved condition, authorize exactly:

**NEXT AUTHORIZED STAGE: LSEG Fundamentals Pre-Acquisition Licensing & Entitlement Validation Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO DATA ACQUISITION**

That future gate may validate only LSEG licensing/entitlement conditions relevant to the designed path. It may not acquire fundamentals, create accounts, use credentials, activate a trial, integrate LSEG, activate EODHD/FactSet, restart Guru or modify Universe state.

## 44. Guru Boundary

### QUALIFIED FACT

- Guru Restart Authorized: NO
- `AUTHORIZED NEXT GURU STAGE: NONE`
- New STOXX Europe 600 Ranking: NO
- New Guru Top 5: NO
- Legacy 25-stock ranking: `LEGACY PILOT`

No design outcome changes this state.

## 45. Universe Boundary

### QUALIFIED FACT

- Universe Expansion: `PAUSED — NOT ABANDONED`
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe Write: NO

No population selection, population reopening, membership change or expansion work occurs.

## 46. No-Touch Verification

This stage performed:

- Fundamentals acquisition: NO
- Live fundamentals API call: NO
- Bulk fundamentals download: NO
- Sample fundamentals download: NO
- Provider account creation: NO
- Credential request/use: NO
- Trial activation: NO
- Sales contact/form submission: NO
- Provider integration: NO
- Ingestion script/code creation: NO
- Raw dataset creation: NO
- Normalized dataset creation: NO
- Mapping dataset creation: NO
- Snapshot creation: NO
- Metric calculation: NO
- Coverage calculation: NO
- Ranking execution: NO
- EODHD activation: NO
- FactSet activation: NO
- New provider discovery: NO
- Guru restart: NO
- Universe write: NO
- Universe expansion resume: NO

Only `docs/spec/Fundamentals_Bulk_Acquisition_and_Mapping_Design_Gate.md` is written by this stage.

## Final Gate State

- `STAGE STATUS: PASS`
- Preferred Source: `LSEG Company Fundamentals / Worldscope`
- Qualified Runner-Up: `EODHD Fundamentals + Bulk Fundamentals API`
- Acquisition Contract Defined: YES
- Mapping Contract Defined: YES
- Raw Observation Contract Defined: YES
- Snapshot Contract Defined: YES
- Provenance Contract Defined: YES
- Normalization Contract Defined: YES
- DQ Contract Defined: YES
- Refresh Contract Defined: YES
- Failure/Recovery Contract Defined: YES
- Pilot Contract Defined: YES
- Runner-Up Failover Governance Defined: YES
- `CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED`
- `LICENSING CONDITION STATUS: UNRESOLVED`
- `DESIGN STATUS: A — READY FOR PRE-ACQUISITION VALIDATION`
- `PRE-ACQUISITION STATUS: BLOCKED`
- Pilot Acquisition Authorized: NO
- Fundamentals Acquired: NO
- Provider Integrated: NO
- EODHD Activated: NO
- FactSet Activated: NO
- Guru Restart Authorized: NO
- `AUTHORIZED NEXT GURU STAGE: NONE`
- Universe Write: NO
- `NEXT AUTHORIZED STAGE: LSEG Fundamentals Pre-Acquisition Licensing & Entitlement Validation Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO DATA ACQUISITION`

HARD STOP after commit and post-commit verification.
