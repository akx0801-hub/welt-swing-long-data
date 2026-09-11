# LSEG Fundamentals Pre-Acquisition Licensing & Entitlement Validation Gate

## 1. Purpose

### QUALIFIED FACT

This report executes exactly the authorized stage:

**LSEG Fundamentals Pre-Acquisition Licensing & Entitlement Validation Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO DATA ACQUISITION**

Provider scope is locked to **LSEG Company Fundamentals / Worldscope**. The purpose is to determine whether authoritative public LSEG material is sufficient to establish that the intended Fundamentals Research Layer workflow is licensable and entitlement-feasible before any acquisition.

This is not procurement, legal advice, provider selection, integration, pilot execution or data acquisition.

**STAGE STATUS: PASS**

**LICENSING CONDITION STATUS: PARTIALLY_RESOLVED**

**LICENSING ACQUISITION READINESS: BLOCKED**

**CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED**

**PRE-ACQUISITION STATUS: BLOCKED**

**NEXT AUTHORIZED STAGE: LSEG Fundamentals Contract & Entitlement Confirmation Manager Gate — READ-ONLY / MANAGER ONLY — NO PROVIDER CONTACT — NO DATA ACQUISITION**

## 2. Authorized Stage

### QUALIFIED FACT

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Authorized stage: `LSEG Fundamentals Pre-Acquisition Licensing & Entitlement Validation Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO DATA ACQUISITION`
- Expected start HEAD: `5b4b278b3720f34b0f2fb9a9e629b7041fbe18ed`
- Expected start commit: `Fundamentals bulk acquisition and mapping design gate`
- Required parent: `8d6da30038d462301193ffefce14749cf85c6de3`
- Provider lock: LSEG Company Fundamentals / Worldscope only
- EODHD: qualified runner-up / inactive
- FactSet: conditionally qualified / inactive
- Currency gate execution: prohibited
- Provider contact: prohibited
- Acquisition/integration/pilot: prohibited

## 3. Start HEAD Verification

### QUALIFIED FACT

At stage start and immediately before the only repository write:

- `HEAD = 5b4b278b3720f34b0f2fb9a9e629b7041fbe18ed`
- `origin/main = 5b4b278b3720f34b0f2fb9a9e629b7041fbe18ed`
- commit message = `Fundamentals bulk acquisition and mapping design gate`
- parent = `8d6da30038d462301193ffefce14749cf85c6de3`

**Start Gate Result: PASS**

No merge, rebase, repair or alternate-head continuation occurred.

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
| FactSet | CONDITIONALLY_QUALIFIED / INACTIVE |
| Design Status | A — READY FOR PRE-ACQUISITION VALIDATION |
| Currency | PARTIALLY_RESOLVED |
| Licensing | UNRESOLVED entering stage |
| Pre-Acquisition | BLOCKED |

No baseline or provider-governance state is changed except the licensing condition is reclassified from `UNRESOLVED` to `PARTIALLY_RESOLVED` on the basis of this bounded public-evidence validation.

## 5. Normative Inputs

### ARCHITECTURE REQUIREMENT

The following repository documents remain normative:

1. `docs/spec/Fundamentals_Research_Layer_Architecture_and_Bulk_Source_Capability_Gate.md`
2. `docs/spec/Fundamentals_Bulk_Source_Qualification_Gate.md`
3. `docs/spec/Fundamentals_Bulk_Source_Discovery_Manager_Gate.md`
4. `docs/spec/Fundamentals_Bounded_External_Source_Discovery.md`
5. `docs/spec/Fundamentals_Bulk_Source_Qualification_v2_Gate.md`
6. `docs/spec/Fundamentals_Bulk_Acquisition_and_Mapping_Design_Gate.md`

The last design report defines the intended acquisition, storage, normalization, provenance, refresh and model-consumption workflow. This gate does not redesign it.

## 6. Provider Lock

### QUALIFIED FACT

Validation is limited to **LSEG Company Fundamentals / Worldscope**, principally through LSEG Data as a Service (DaaS) product and legal/usage materials.

EODHD remains `QUALIFIED RUNNER-UP / INACTIVE`. FactSet remains `CONDITIONALLY_QUALIFIED / INACTIVE`. No alternative provider was researched or activated.

## 7. Scope Boundary

### ARCHITECTURE REQUIREMENT

This gate addresses only:

- licensing;
- entitlement;
- permitted use;
- machine/non-display use;
- bulk access;
- local storage;
- retention;
- normalization/transformation;
- derived data/metrics;
- application/user restrictions;
- redistribution;
- termination implications.

Currency remains `PARTIALLY_RESOLVED`; incidental currency evidence is not used to change that status.

No account, login, credential, trial, contact, live API call, download, integration, pilot, Guru or Universe action occurred.

## 8. Evidence Method

### QUALIFIED FACT

Research date: **2026-09-11**.

Evidence priority:

1. LSEG/Refinitiv product-specific technical documentation;
2. LSEG product/service-description documentation;
3. LSEG official contract/terms materials;
4. LSEG licensing/redistribution guidance;
5. LSEG developer documentation;
6. secondary evidence only if necessary for corroboration.

Status discipline:

- `PASS` requires sufficient authoritative evidence.
- `CONDITIONAL` requires a credible underlying entitlement path plus a bounded contract-specific confirmation.
- `UNKNOWN` means public evidence is insufficient.
- technical availability is never treated as permission.

This report does not provide a legal opinion. Statements are limited to what public documents support and what the future customer contract/entitlement must confirm.

## 9. Evidence Register

### E1 — Company Fundamentals via DaaS

- **URL:** `https://developers.lseg.com/en/api-catalog/daas/DaaS/Products/CompanyFundamentalsViaDaaS`
- **Title:** Company Fundamentals via DaaS
- **Publisher:** LSEG Developer Community
- **Document type:** official product documentation
- **Document date:** current page; linked user guide July 14, 2025; linked service addendum June 9, 2025
- **Research date:** 2026-09-11
- **Claim supported:** Company Fundamentals is offered as a subscribed DaaS product with standardized/as-reported fundamentals and machine delivery paths.
- **Evidence strength:** STRONG
- **Interpretation:** establishes product capability and subscription model, not every downstream usage right.
- **Residual uncertainty:** actual order form, entitlement scope and incorporated usage restrictions.

### E2 — Company Fundamentals DaaS Service Description Addendum

- **URL:** `https://developers.lseg.com/content/dam/devportal/api-families/lseg-data-platform/data-as-a-service/userguides/fundamentals/Service_Description_AddendumDaaSFundamentals.pdf`
- **Title:** Company Fundamentals — Data as a Service / Service Description Addendum
- **Publisher:** LSEG
- **Document type:** official product/service description
- **Document date:** June 9, 2025
- **Research date:** 2026-09-11
- **Claim supported:** curated Company Fundamentals is available by bulk feed or normalized database, may be integrated into proprietary models/customer applications, and is intended for portfolio analysis, equity research, screening and quantitative analysis.
- **Evidence strength:** STRONG
- **Interpretation:** strong evidence for internal model/application feasibility.
- **Residual uncertainty:** precise contractual definition of permitted applications, non-display licensing and derived-data persistence.

### E3 — DaaS Bulk Data Feed

- **URL:** `https://developers.lseg.com/en/api-catalog/daas/DaaS/QuickStart/AccessingDaaSProducts/BulkDataFeed`
- **Title:** Bulk Data Feed
- **Publisher:** LSEG Developer Community
- **Document type:** official technical/product documentation
- **Document date:** current page, research date 2026-09-11
- **Claim supported:** subscribed curated content can initialise and maintain a local database copy, be combined with proprietary data and be used for big-data analytics or machine learning in customer-managed infrastructure.
- **Evidence strength:** STRONG
- **Interpretation:** demonstrates an explicit bulk/local-replica use pattern.
- **Residual uncertainty:** rights remain bounded by the actual commercial product licence and any third-party restrictions.

### E4 — DaaS File Retrieval API User Guide v6.11

- **URL:** `https://developers.lseg.com/content/dam/devportal/api-families/lseg-data-platform/data-as-a-service/userguides/bulk/lseg-data-as-a-service-file-retrieval-api-user-guide-v6-11.pdf`
- **Title:** LSEG Data as a Service File Retrieval API User Guide
- **Publisher:** LSEG
- **Document type:** official technical documentation
- **Document date:** April 30, 2026
- **Research date:** 2026-09-11
- **Claim supported:** the API checks the service account's commercial product and third-party content licences; returns only entitled files; supports local infrastructure; supports initialisation plus incremental updates; is designed for a long-running client-managed replica database.
- **Evidence strength:** STRONG
- **Interpretation:** proves automated/bulk entitlement architecture, local replica architecture and repeated refresh as an intended delivery model.
- **Residual uncertainty:** does not itself grant broad legal rights beyond the provisioned entitlement.

### E5 — Refinitiv Short Form Terms v1.1

- **URL:** `https://www.lseg.com/content/dam/lseg/en_us/documents/policies/refinitiv-short-form.pdf`
- **Title:** Refinitiv Short Form — Terms
- **Publisher:** Refinitiv / LSEG
- **Document type:** official general customer terms
- **Document date:** version 1.1; public file current at research date
- **Research date:** 2026-09-11
- **Claim supported:** order form and incorporated documents define permitted products/quantities/usage; use/copy/modify/distribute only as expressly specified; internal-business information-service rights are general but limited; automated downloading requires prior written consent unless otherwise expressly permitted; third-party provider terms may apply; usage rights end on termination unless otherwise agreed.
- **Evidence strength:** STRONG for general contractual framework; MEDIUM for Worldscope-specific rights.
- **Interpretation:** decisive proof that actual rights depend on the product/order-form contract and cannot be inferred from technical accessibility.
- **Residual uncertainty:** product-specific order form and incorporated terms were not publicly available.

### E6 — LSEG Data Redistribution

- **URL:** `https://www.lseg.com/en/data-analytics/market-data/data-redistribution`
- **Title:** Data Redistribution
- **Publisher:** LSEG
- **Document type:** official licensing/product guidance
- **Document date:** current page; research date 2026-09-11
- **Claim supported:** LSEG distinguishes internal distribution from redistribution to customers; transformed outputs may be derived data; derived outputs can remain licensable; redistribution requires governed rights.
- **Evidence strength:** MEDIUM for general data-licensing concepts; not Worldscope-specific.
- **Interpretation:** external/public dissemination cannot be assumed from internal research rights.
- **Residual uncertainty:** exact Company Fundamentals derived-data terms.

### E7 — LSEG Academy: Financial Data for AI / Licensing

- **URL:** `https://www.lseg.com/content/dam/lseg/learning-centre/documents/how-to-optimise-financial-data-for-ai-presentation-slides.pdf`
- **Title:** How to optimise financial data for AI — Licensing slides
- **Publisher:** LSEG Academy
- **Document type:** official educational/licensing guidance
- **Document date:** public document; research date 2026-09-11
- **Claim supported:** distinguishes raw, normalized/modified and derived data; notes non-display/derived-data licensing may apply; explicitly directs clients to contractual terms for exact definitions/rights.
- **Evidence strength:** MEDIUM
- **Interpretation:** supports the need for explicit non-display/derived-data entitlement confirmation rather than assumption.
- **Residual uncertainty:** Company Fundamentals-specific licence language.

### E8 — Developer Terms of Use

- **URL:** `https://developers.lseg.com/en/terms-of-use`
- **Title:** Terms of Use — Developer Community
- **Publisher:** LSEG Developer Community
- **Document type:** official website/developer-community terms
- **Document date:** current page; research date 2026-09-11
- **Claim supported:** access to Refinitiv/LSEG products/services continues to be governed by the current customer master agreement; confidentiality and termination obligations apply to confidential material under those terms.
- **Evidence strength:** MEDIUM
- **Interpretation:** developer pages do not replace the customer/product contract.
- **Residual uncertainty:** exact Company Fundamentals agreement.

## 10. Public vs Contract-Specific Evidence

### PUBLICLY VALIDATED

Public authoritative material establishes that an entitlement path exists for:

1. subscribed Company Fundamentals DaaS access;
2. machine/service-account access;
3. bulk-file delivery;
4. local/client-managed replica database operation;
5. repeated initialisation/incremental refresh;
6. integration into proprietary models and customer applications;
7. portfolio analysis, equity research, screening and quantitative analytics as contemplated uses;
8. entitlement enforcement based on subscribed commercial products and third-party content licences.

These eight items establish technical/licensing feasibility at the product-architecture level, not complete customer-specific permission.

### REQUIRES CONTRACT / ENTITLEMENT CONFIRMATION

The following material rights remain contract-specific and must be confirmed before acquisition:

1. exact Company Fundamentals/Worldscope product package and delivery entitlement;
2. explicit machine/non-display use classification for the intended automated pipeline;
3. scope and duration of persistent local raw-data storage;
4. historical/vintage/restatement retention rights;
5. backup/archive/cache rights and any limits;
6. normalization/modified-data rights for the project's canonical representation;
7. internal derived-metric creation and persistence rights;
8. reuse of the same data layer across multiple internal research models/applications;
9. third-party identifier/content restrictions within the subscribed product;
10. post-termination deletion/retention rights for raw, normalized, derived and provenance data;
11. public/Git/repository exposure restrictions, including confirmation that raw provider data must remain outside public/shared repositories.

**Contract/Entitlement Confirmations Required: 11**

## 11. L1–L20 Matrix

| ID | Question | Status | Evidence / Interpretation |
|---|---|---|---|
| L1 | Automated/machine access supported under appropriate entitlement | PASS | DaaS File Retrieval API uses authenticated service accounts and commercial-product entitlements. |
| L2 | Population-scale/bulk retrieval permitted under appropriate entitlement | PASS | Bulk feed is explicitly designed to seed/maintain local replicas of subscribed curated datasets. |
| L3 | Internal research/analytics use permitted | PASS | Company Fundamentals addendum expressly contemplates proprietary models, equity research, screening and quantitative analysis. |
| L4 | Retrieved source data may be stored locally | PASS | File Retrieval guide explicitly supports local infrastructure and target replica databases. |
| L5 | Source data may persist beyond immediate retrieval session | PASS | Long-running replica and incremental-maintenance model necessarily contemplates persistence during the subscription/authorized use period. |
| L6 | Retention periods/deletion obligations known | CONDITIONAL | General terms state rights end and provider property must be destroyed/uninstalled on termination unless otherwise agreed; product-specific retention details are not public. |
| L7 | Historical fundamentals may be stored | PASS | Company Fundamentals includes full-depth history and DaaS is designed to replicate the subscribed product dataset locally; exact post-term retention remains conditional. |
| L8 | Normalized internal representations may be created | CONDITIONAL | Product is itself normalized and may feed proprietary models, but general terms prohibit modification/derivative works unless expressly permitted by the agreement. Exact internal transformation rights require contract confirmation. |
| L9 | Derived metrics may be calculated | CONDITIONAL | Proprietary-model/quantitative use is expressly contemplated; LSEG licensing guidance treats derived/non-display uses as contract-sensitive. |
| L10 | Derived metrics may be stored internally | CONDITIONAL | Technically inherent in model workflows, but persistence rights are not explicitly established for this product in public contract terms. |
| L11 | Restrictions on derived-data persistence known | UNKNOWN | No public Worldscope-specific persistence clause found. |
| L12 | Redistribution/external publication restrictions understood | CONDITIONAL | Public LSEG guidance clearly distinguishes internal use from redistribution and states derived outputs may remain licensable; exact Worldscope terms are contract-specific. |
| L13 | Raw source data may be stored in Git/repository | UNKNOWN | No public product-specific permission. Precautionary architecture rule: do not store raw provider data in Git. |
| L14 | Metadata/provenance references may be retained independently | CONDITIONAL | Operational metadata is inherent to DaaS processing, but perpetual/post-term retention of provider IDs/field metadata is not explicitly established. |
| L15 | User/device/application restrictions sufficiently known | CONDITIONAL | Service-account/application entitlement exists; exact licensed applications/users/environments are customer/order-form specific. |
| L16 | Bulk/API/data-feed requires distinct entitlement | PASS | File Retrieval guide checks a DaaS Commercial Product Licence and third-party licences and returns only entitled files. |
| L17 | Intended delivery mechanism requires specific licensed product/package | PASS | Company Fundamentals DaaS subscription plus selected bulk/database delivery is a specific commercial entitlement path. |
| L18 | Caching restrictions sufficiently known | CONDITIONAL | Persistent replica is supported, but cache/backup/archive limits are not completely public. |
| L19 | Cross-model internal use sufficiently licensed | CONDITIONAL | Proprietary-model use is contemplated, but number/scope of applications/use cases may be entitlement-specific. |
| L20 | Project architecture compatible with public restrictions | CONDITIONAL | No public evidence establishes an incompatibility; architecture is feasible if the 11 contract confirmations are satisfied. |

## 12. Automated Access

### OFFICIAL EXPLICIT

The DaaS File Retrieval API is an authenticated machine interface using service accounts and commercial-product entitlements. It returns files based on the requesting account's entitlement profile.

**Automated Access Technical Capability: YES**

**Automated Access Licensing Feasibility: PASS**

This is not equivalent to acquisition authorization; the actual account must later hold the correct product and third-party entitlements.

## 13. Bulk Entitlement

### OFFICIAL EXPLICIT

Bulk Data Feed and the File Retrieval API are designed to seed and maintain a complete local replica of subscribed DaaS datasets. The entitlement system filters delivered files to the commercial products and third-party content licences provisioned to the service account.

**600-Scale Entitlement Path: PASS**

**2527-Scale Entitlement Path: PASS**

These results mean a documented entitlement model exists at both scales. They do not prove that a future customer has purchased it.

## 14. Internal Research Use

### OFFICIAL EXPLICIT

The Company Fundamentals DaaS service description states that fundamentals can be integrated into proprietary models and customer applications and used in portfolio analysis, equity research, screening and quantitative analysis.

**Internal Research Use: PERMITTED**

### RESIDUAL CONDITION

Cross-model/application breadth remains subject to the actual agreement/order form, particularly if separate application/non-display licences are used.

## 15. Raw Data Storage

### OFFICIAL EXPLICIT

DaaS bulk documentation expressly supports downloading subscribed files to customer local infrastructure, loading them into staging tables and maintaining a target replica database over time.

**Raw Data Local Storage: PASS**

**Raw Historical Retention: PASS** for the active, appropriately entitled use period.

### UNRESOLVED CONDITION

Post-termination retention and any product-specific archive/backup limits are not publicly resolved.

## 16. Git / Repository Storage

### UNKNOWN

No authoritative public Company Fundamentals term found explicitly permits raw provider data to be committed into Git or an equivalent shared code repository.

**Raw Provider Data in Git: UNKNOWN**

### ARCHITECTURE REQUIREMENT

**DO NOT STORE RAW PROVIDER DATA IN GIT.**

This is a precautionary project rule, not a claim that Git storage is categorically prohibited by every possible LSEG contract.

## 17. Secure External Raw Storage

### OFFICIAL INDIRECT / REASONED INTERPRETATION

The DaaS design explicitly supports a customer-managed local database/infrastructure. Therefore a secured, entitlement-controlled external raw store is compatible with the delivery model, subject to the actual contract's retention, security and third-party-content clauses.

**External Secure Raw Storage: CONDITIONAL**

Required confirmation: permitted persistence period, backup/archive scope, access-control restrictions, third-party-content conditions and termination deletion obligations.

## 18. Normalized Data

### OFFICIAL INDIRECT

Company Fundamentals itself offers standardized/normalized data and expressly supports proprietary-model integration. However the general customer terms state that modification/derivative works are permitted only as expressly specified in the Agreement.

**Internal Normalization: CONDITIONAL**

The actual entitlement must expressly support or not prohibit internal normalization/transformation into the project's canonical schema while retaining required source/provenance fields.

## 19. Derived Metrics

### OFFICIAL INDIRECT

Proprietary-model and quantitative-analysis use strongly supports the feasibility of calculation. LSEG's own licensing guidance also makes clear that derived/non-display use can be separately licensed and must be checked against contractual terms.

**Internal Derived Metric Creation: CONDITIONAL**

**Internal Derived Metric Storage: CONDITIONAL**

**Derived Metric Redistribution: CONDITIONAL**

External redistribution is not required for the initial Fundamentals Research Layer and remains outside acquisition readiness.

## 20. Derived-Data Definition

### OFFICIAL FACT

LSEG public licensing guidance distinguishes raw, normalized/modified and derived data and describes derived data as transformed output that cannot readily recreate the source. LSEG also treats many non-display and derived-data uses as licence-sensitive.

These materials are general guidance, not a Company Fundamentals-specific contractual schedule.

**Derived-Data Definition Clarity: MEDIUM**

Project terminology must not be assumed identical to the final contract's definitions of `Raw Data`, `Modified Data`, `Derived Data`, `Non-Display`, `Application Use` or any third-party-provider terminology.

## 21. Non-Display / Machine Use

### OFFICIAL INDIRECT

DaaS bulk delivery is explicitly machine-to-machine and intended for local databases and analytical applications, proving a commercial machine-use path exists. Public LSEG licensing guidance shows that non-display use can carry separate licensing conditions.

**Non-Display / Machine Use Entitlement: CONDITIONAL**

Required confirmation: the intended automated Fundamentals Research Layer, number of applications/environments and model uses are included in the future order form/entitlement.

## 22. User / Application Restrictions

### OFFICIAL FACT

DaaS File Retrieval access is tied to service-account entitlement. The general terms state that order forms specify products, quantities and permissions, and that excess use can trigger additional charges. Third-party terms may also apply.

**User/Application Restrictions: PARTIAL**

Material impact: YES. The architecture requires at least one automated service/application identity and may feed multiple internal model consumers; those scopes must be covered explicitly.

## 23. Retention / Deletion

### OFFICIAL FACT

The general Refinitiv/LSEG terms state that unless otherwise agreed, upon termination usage rights end and each party must uninstall or destroy the other's property. The DaaS technical materials do not replace this contract rule.

**Retention Governance: CONDITIONAL**

**Termination/Deletion Governance: CONDITIONAL**

Required confirmation: active-term raw/cache/archive retention, backups, historical snapshots, normalized/derived outputs and deletion obligations after termination.

## 24. Historical Version Retention

### OFFICIAL INDIRECT

The product provides full historical fundamentals and a local-replica delivery model. The project also has a legitimate point-in-time/restatement design need. Public materials do not establish whether prior vintages/restated versions may be retained indefinitely under every entitlement.

**Historical Version Retention: CONDITIONAL**

This is a specific risk to historical point-in-time governance and must be confirmed before acquisition if the project intends to retain vintages beyond what the provider's current replica model naturally exposes.

## 25. Provenance Retention

### REASONED INTERPRETATION

The DaaS workflow necessarily uses product identifiers, schema/field metadata, processing timestamps and operational watermarks. Retaining run-level provenance is operationally necessary. However perpetual retention of provider field definitions/IDs after contract termination is not explicitly established in public Company Fundamentals terms.

**Metadata / Provenance Retention: CONDITIONAL**

The contract confirmation should distinguish non-value project metadata from provider proprietary metadata/content.

## 26. Redistribution

### OFFICIAL FACT

LSEG public licensing guidance distinguishes internal use from redistribution to customers and states that derived outputs can remain subject to licensing. The project's initial layer does not require external redistribution.

**Internal Sharing: CONDITIONAL**

**External Raw Redistribution: FAIL** unless separately licensed; no such entitlement is assumed.

**External Derived Redistribution: CONDITIONAL** and out of initial scope.

**Public Repository Exposure: FAIL** for raw provider content as a project policy unless a future explicit licence says otherwise.

The `FAIL` values here do not block the internal acquisition path because external/public redistribution is not a required hard gate for the intended workflow.

## 27. Cross-Model Reuse

### OFFICIAL INDIRECT

The service description supports proprietary models and multiple research/analysis use cases, but public documents do not establish whether one future entitlement automatically covers every internal application/model consumer.

**Cross-Model Internal Reuse: CONDITIONAL**

Required confirmation: Guru Europe, Marks/Value, Turnaround and Long Research may consume the same internal normalized data layer under the selected entitlement/application scope.

## 28. Refresh Rights

### OFFICIAL EXPLICIT

The subscribed DaaS product is designed for initialization, incremental refresh and reinitialization throughout the life of an integration. The API returns only data permitted by the service account's entitlement profile.

**Repeated Refresh Licensing: PASS** subject to holding the appropriate active entitlement.

## 29. Termination Rights

### OFFICIAL FACT

General terms state that usage rights end on termination and provider property must be destroyed/uninstalled unless otherwise agreed. No public Company Fundamentals-specific post-termination carve-out was found for raw, normalized, derived or metadata layers.

**Post-Termination Raw Retention: CONDITIONAL**

**Post-Termination Derived Retention: CONDITIONAL**

**Post-Termination Metadata Retention: CONDITIONAL**

These items require actual contract/order-form confirmation.

## 30. Commercial Entitlement

### OFFICIAL EXPLICIT

DaaS File Retrieval documentation repeatedly refers to commercial product licences/subscriptions and service-account entitlement profiles. Company Fundamentals is a subscribed DaaS product.

**Commercial Entitlement Required: YES**

No purchase, trial or sales contact occurred.

## 31. Public Pricing if Relevant

No authoritative public Company Fundamentals/Worldscope DaaS price was needed to determine licensing feasibility, and no broad pricing investigation was performed.

**Public Pricing: UNKNOWN**

This does not block technical/licensing feasibility.

## 32. Licensing Risk Matrix

| Risk Dimension | Rating | Reason |
|---|---|---|
| Automated Access Risk | LOW | official DaaS service-account/API entitlement model exists |
| Storage Risk | MEDIUM | local replica explicitly supported, but exact retention/backup terms are contract-specific |
| Retention Risk | MEDIUM | active-term persistence is supported; termination and vintage retention need confirmation |
| Derived-Data Risk | MEDIUM | proprietary models are supported but exact modified/derived-data rights are contract-specific |
| Non-Display Risk | MEDIUM | machine use is integral to DaaS, but the intended application/use classification must be licensed |
| Redistribution Risk | HIGH | external/public redistribution is separately governed; not needed for initial architecture |
| Termination Risk | MEDIUM | general terms end usage rights and require destruction unless otherwise agreed |
| Overall Licensing Risk | MEDIUM | core product path is clearly feasible; material customer-specific rights remain bounded but unresolved |

## 33. Hard Licensing Gates

Hard-gate status:

- L1 Automated Access: PASS
- L2 Bulk Retrieval: PASS
- L3 Internal Research Use: PASS
- L4 Local Storage: PASS
- L7 Historical Storage: PASS
- L8 Normalization: CONDITIONAL
- L9 Derived Metrics: CONDITIONAL
- L10 Derived Metric Storage: CONDITIONAL
- L15 User/Application Restrictions: CONDITIONAL
- L16 Bulk/API Entitlement: PASS
- L17 Delivery Entitlement: PASS
- L18 Caching: CONDITIONAL
- L19 Cross-Model Use: CONDITIONAL
- L20 Architecture Compatibility: CONDITIONAL

No hard gate is `FAIL` or `UNKNOWN`. However multiple material usage rights are customer-contract-specific and therefore prevent `LICENSING CONDITION STATUS = RESOLVED`.

## 34. Publicly Validated

**Publicly Validated Core Rights / Feasibility Elements: 8**

1. machine/service-account access path exists;
2. Company Fundamentals DaaS commercial subscription path exists;
3. bulk acquisition path exists;
4. local client-managed replica storage is an intended use pattern;
5. repeated initialization/incremental refresh is an intended use pattern;
6. proprietary-model integration is an intended use case;
7. equity research/screening/quantitative analytics are intended use cases;
8. entitlement enforcement can constrain delivery to subscribed commercial and third-party content.

These are feasibility findings, not a substitute for the future executed agreement.

## 35. Requires Contract / Entitlement Confirmation

**Contract/Entitlement Confirmations Required: 11**

1. product/package + delivery entitlement;
2. automated non-display/application scope;
3. local raw persistence scope/duration;
4. historical/vintage/restatement retention;
5. backup/archive/cache rights;
6. normalization/modified-data rights;
7. derived metric creation/storage rights;
8. cross-model/application reuse rights;
9. third-party content/identifier constraints;
10. termination deletion and post-term retention;
11. public/Git/repository exposure restrictions and allowed provenance-only retention.

The unresolved items are bounded and contract/entitlement-specific rather than broad/architectural.

## 36. Contract Confirmation Checklist

| # | Question | Why It Matters | Required Confirmation | Acceptable Evidence | Blocking |
|---:|---|---|---|---|---|
| 1 | Which exact Company Fundamentals / Worldscope DaaS products and delivery channels are licensed? | defines lawful source/delivery scope | order form explicitly lists required product(s), bulk/database channel and relevant addenda | executed order form + incorporated product schedule | YES |
| 2 | Is automated service-account/non-display use for the planned pipeline permitted? | pipeline is machine-to-machine | agreement/application entitlement covers automated internal processing | entitlement schedule / non-display or application-use clause | YES |
| 3 | May raw fundamentals be persistently stored in a client-managed database? | design uses raw observation/snapshot layer | persistent local storage permitted for subscribed content | product/order-form storage clause | YES |
| 4 | May historical and restated/vintage observations be retained? | point-in-time/restatement governance | explicit permission for historical/vintage persistence or clear retention limits | product schedule / retention policy | YES |
| 5 | What cache, backup and archive rights/limits apply? | resilience and reproducibility | permitted cache/backup media, duration and deletion rules | incorporated usage/retention terms | YES |
| 6 | May raw values be normalized/reformatted into an internal canonical schema? | architecture requires normalized fundamentals | internal modification/normalization permitted | data-use/modified-data clause | YES |
| 7 | May internal derived metrics be calculated and retained? | all research models depend on derived features | creation + internal persistence permitted and definitions understood | derived-data/non-display/application licence clause | YES |
| 8 | May one data layer feed Guru Europe, Marks/Value, Turnaround and Long Research? | prevents application-scope breach | all intended internal applications/models covered | application/use-case schedule or explicit internal-use entitlement | YES |
| 9 | Which third-party identifiers/content carry additional restrictions? | mapping may use ISIN/other third-party fields | relevant fields are included and usable under required third-party licences | third-party terms + entitlement statement | YES |
| 10 | What must be deleted or may be retained after termination? | affects raw history, snapshots, derived metrics and reproducibility | explicit post-term treatment of raw/normalized/derived/metadata/backups | termination/retention clause | YES |
| 11 | Can any provider content/metadata be stored in Git, and what provenance-only metadata may persist? | protects repository from unauthorized provider-data exposure | raw Git storage either expressly permitted or expressly prohibited; metadata/provenance scope defined | contract/data-handling schedule | NO for acquisition if architecture keeps raw data outside Git, but YES before any repository exposure |

No vendor contact is authorized by this checklist.

## 37. LICENSING CONDITION STATUS

### QUALIFICATION JUDGMENT

**LICENSING CONDITION STATUS: PARTIALLY_RESOLVED**

Reason:

Public authoritative LSEG evidence establishes a concrete licensed architecture for subscribed Company Fundamentals DaaS: machine/service-account access, bulk delivery, customer-managed local replica databases, recurring incremental refresh and integration into proprietary models/research workflows. Therefore licensing feasibility is not broadly unknown.

However, the actual customer-specific order form/entitlement remains decisive for persistent storage scope, normalization, derived-data/non-display rights, multi-application reuse, third-party-content restrictions and termination retention. Those are material hard-gate usage rights and cannot be inferred from product capability documentation.

The remaining uncertainty is **bounded and contract/entitlement-specific**, not architectural.

## 38. LICENSING ACQUISITION READINESS

**LICENSING ACQUISITION READINESS: BLOCKED**

A `READY` status requires `LICENSING CONDITION STATUS = RESOLVED`. That threshold is not met.

## 39. Currency Boundary

### QUALIFIED FACT

Currency status entering this stage was `PARTIALLY_RESOLVED`.

This stage does not execute the Currency Semantics Validation Gate.

**CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED**

Any incidental currency references found during licensing research are reserved as `CURRENCY EVIDENCE FOR FUTURE GATE` and do not alter this status.

## 40. PRE-ACQUISITION STATUS

**PRE-ACQUISITION STATUS: BLOCKED**

Reasons:

1. licensing remains `PARTIALLY_RESOLVED`; and
2. currency remains `PARTIALLY_RESOLVED` and has not been separately validated to the required pre-acquisition threshold.

No pilot acquisition is authorized.

## 41. Exact Next Authorized Stage

Because the licensing result is `PARTIALLY_RESOLVED` and the remaining items are bounded, customer-contract/entitlement-specific questions, authorize exactly:

**NEXT AUTHORIZED STAGE: LSEG Fundamentals Contract & Entitlement Confirmation Manager Gate — READ-ONLY / MANAGER ONLY — NO PROVIDER CONTACT — NO DATA ACQUISITION**

That manager gate may decide how future actual entitlement evidence may be obtained. It may not itself contact LSEG or acquire data.

No broader licensing search, provider comparison, runner-up activation or currency-gate execution is authorized by this report.

## 42. Guru Boundary

### QUALIFIED FACT

- Guru Restart Authorized: NO
- `AUTHORIZED NEXT GURU STAGE: NONE`
- New STOXX Europe 600 Ranking: NO
- New Guru Top 5: NO
- Legacy 25-stock ranking: `LEGACY PILOT`

No licensing result changes Guru status.

## 43. Fundamentals Execution Boundary

### QUALIFIED FACT

- Fundamentals Acquired: NO
- Live Fundamentals API Called: NO
- Bulk Dataset Downloaded: NO
- Provider Account Created: NO
- Login Performed: NO
- Trial Activated: NO
- Provider Integrated: NO
- Mapping Executed: NO
- Snapshot Created: NO
- Normalization Executed: NO
- Derived Metrics Calculated: NO
- Coverage Calculated: NO
- Pilot Acquisition Authorized: NO
- EODHD Activated: NO
- FactSet Activated: NO

## 44. Universe Boundary

### QUALIFIED FACT

- Universe Expansion: `PAUSED — NOT ABANDONED`
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe Write: NO

No population work occurred.

## 45. No-Touch Verification

This gate performed:

- External licensing/documentation research: YES
- LSEG-only scope: YES
- EODHD licensing research: NO
- FactSet licensing research: NO
- New provider discovery: NO
- Provider comparison: NO
- Currency gate execution: NO
- Provider contact: NO
- Account creation: NO
- Login: NO
- Credential use: NO
- API key request/use: NO
- Trial: NO
- Sales/demo form: NO
- Live fundamentals API call: NO
- Fundamentals download: NO
- Bulk dataset download: NO
- Sample fundamentals acquisition: NO
- Provider integration: NO
- Pilot: NO
- Mapping execution: NO
- Snapshot creation: NO
- Normalization execution: NO
- Derived metric calculation: NO
- Coverage calculation: NO
- Guru restart: NO
- Universe write: NO

Only `docs/spec/LSEG_Fundamentals_Pre_Acquisition_Licensing_and_Entitlement_Validation_Gate.md` is written by this stage.

## Final Gate State

- `STAGE STATUS: PASS`
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe Expansion: PAUSED — NOT ABANDONED
- Preferred Source: LSEG Company Fundamentals / Worldscope
- Qualified Runner-Up: EODHD Fundamentals + Bulk Fundamentals API
- Automated Access Licensing Feasibility: PASS
- 600-Scale Entitlement Path: PASS
- 2527-Scale Entitlement Path: PASS
- Internal Research Use: PERMITTED
- Raw Data Local Storage: PASS
- Raw Historical Retention: PASS
- Raw Provider Data in Git: UNKNOWN
- External Secure Raw Storage: CONDITIONAL
- Internal Normalization: CONDITIONAL
- Internal Derived Metric Creation: CONDITIONAL
- Internal Derived Metric Storage: CONDITIONAL
- Non-Display / Machine Use Entitlement: CONDITIONAL
- Retention Governance: CONDITIONAL
- Termination/Deletion Governance: CONDITIONAL
- Historical Version Retention: CONDITIONAL
- Metadata / Provenance Retention: CONDITIONAL
- Cross-Model Internal Reuse: CONDITIONAL
- Repeated Refresh Licensing: PASS
- Commercial Entitlement Required: YES
- Overall Licensing Risk: MEDIUM
- Publicly Validated Core Rights: 8
- Contract/Entitlement Confirmations Required: 11
- `LICENSING CONDITION STATUS: PARTIALLY_RESOLVED`
- `LICENSING ACQUISITION READINESS: BLOCKED`
- `CURRENCY CONDITION STATUS: PARTIALLY_RESOLVED`
- `PRE-ACQUISITION STATUS: BLOCKED`
- Provider Contact Performed: NO
- Account Created: NO
- Login Performed: NO
- Trial Activated: NO
- Live Fundamentals API Called: NO
- Fundamentals Acquired: NO
- Bulk Dataset Downloaded: NO
- Provider Integrated: NO
- EODHD Activated: NO
- FactSet Activated: NO
- Pilot Acquisition Authorized: NO
- Guru Restart Authorized: NO
- `AUTHORIZED NEXT GURU STAGE: NONE`
- Universe Write: NO
- `NEXT AUTHORIZED STAGE: LSEG Fundamentals Contract & Entitlement Confirmation Manager Gate — READ-ONLY / MANAGER ONLY — NO PROVIDER CONTACT — NO DATA ACQUISITION`

HARD STOP after commit and post-commit verification.
