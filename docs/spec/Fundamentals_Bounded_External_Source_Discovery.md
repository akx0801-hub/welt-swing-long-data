# Fundamentals Bounded External Source Discovery

## 1. Purpose

### FACT

This report executes exactly the authorized stage:

**Fundamentals Bounded External Source Discovery — RESEARCH / DISCOVERY ONLY — NO ACQUISITION — NO INTEGRATION**

The stage performs one bounded external-research pass to identify a small number of concrete source candidates that deserve formal qualification against the existing Fundamentals Bulk Source Capability Contract.

It does **not** qualify a provider, acquire fundamentals, call live fundamentals endpoints, create accounts, activate trials, download bulk/sample datasets, integrate providers, build mapping or fundamentals tables, calculate coverage or rankings, restart Guru Europe, or change Universe membership.

**STAGE STATUS: PASS**

**DISCOVERY RESULT: A — QUALIFICATION CANDIDATE(S) FOUND**

**QUALIFICATION HANDOFF COUNT: 3**

**NEXT AUTHORIZED STAGE: Fundamentals Bulk Source Qualification v2 Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO ACQUISITION — NO INTEGRATION**

## 2. Authorized Stage

### FACT

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Authorized stage: `Fundamentals Bounded External Source Discovery — RESEARCH / DISCOVERY ONLY — NO ACQUISITION — NO INTEGRATION`
- Candidate cap: 5
- Qualification handoff cap: 3
- External documentation research: authorized
- Data acquisition: not authorized
- Provider integration: not authorized
- Guru restart: not authorized
- Universe write: not authorized
- Alpha Vantage: prohibited / out of scope

## 3. Start HEAD Verification

### FACT

At stage start:

- `HEAD = e49a8208c44153158f65ba7e57e0bf1b34896a22`
- `origin/main = e49a8208c44153158f65ba7e57e0bf1b34896a22`
- commit message = `Fundamentals bulk source discovery manager gate`
- parent = `5ad73e492cf28a954f91fa508f3a7354b71635b8`

**Start Gate Result: PASS**

No merge, rebase, repair, or alternate-head continuation occurred.

## 4. Fixed Baseline

### FACT

| Measure | State |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| Universe Expansion | PAUSED — NOT ABANDONED |

PARKED populations remain:

- Canada
- Korea
- US-3
- Brazil
- Taiwan
- India — Nifty 50
- Mexico — S&P/BMV IPC

No baseline value or parked state is changed by this stage.

Productive trading authority remains exclusively **Welt-Swing v7.2**. WELT-SWING-LONG remains **DEV / RESEARCH / SHADOW**.

## 5. Normative Inputs

### FACT

The following repository documents govern this discovery:

1. `docs/spec/Fundamentals_Research_Layer_Architecture_and_Bulk_Source_Capability_Gate.md`
2. `docs/spec/Fundamentals_Bulk_Source_Qualification_Gate.md`
3. `docs/spec/Fundamentals_Bulk_Source_Discovery_Manager_Gate.md`

The architecture gate is `READY FOR SOURCE-CAPABILITY VALIDATION`. The prior qualification gate found `C — NO QUALIFIABLE REPOSITORY-EVIDENCED SOURCE PATH`. The manager gate therefore authorized exactly one bounded external discovery pass with a maximum of five detailed candidates and three qualification handoffs.

No architecture contract is redesigned here.

## 6. Research Boundary

### FACT

Allowed research consisted only of public documentation and capability evidence. Official technical, product, methodology, coverage, licensing and developer documentation was preferred.

No provider account was created. No API key was requested or used. No trial was activated. No company/fundamentals endpoint was called. No bulk or sample fundamentals file was downloaded. No provider data was stored in the repository.

### MANAGER REQUIREMENT APPLIED

Discovery Candidate != Qualified Bulk Source. A source advances only when official/public evidence creates a credible case for a later formal qualification gate. Unsupported attributes remain `UNKNOWN`.

## 7. Research Method

### DISCOVERY JUDGMENT

The manager-defined funnel was applied:

1. identify structured source categories and plausible concrete candidates;
2. apply immediate exclusions;
3. research only the strongest candidates against history, periods, identity, timing, provenance, sectors, scale, refresh and access;
4. stop at five detailed candidates;
5. hand off at most three sources with the strongest official capability evidence and highest expected information gain.

The five admitted detailed candidates are not intended to represent the full provider market.

## 8. Source Authority Hierarchy

### FACT

Capability claims in this report use the following hierarchy:

1. official technical/developer documentation;
2. official data catalogue, schema, product or methodology documentation;
3. official coverage/access/licensing documentation;
4. official provider statements;
5. reputable secondary material only as supplementary discovery evidence.

No secondary claim overrides contrary or absent official technical evidence.

Research date for external evidence: **2026-09-11**.

Undated official web pages are recorded as undated and researched on that date. Dated but older provider statistics are explicitly flagged.

## 9. Discovery Funnel

### DISCOVERY INFERENCE

Three source patterns emerged:

- global normalized institutional fundamentals platforms with broad history and industry templates;
- structured commercial APIs with explicit bulk fundamentals endpoints and strong security identifiers;
- lower-cost/API/bulk providers where core mechanics are strong but public evidence for geographic scale, point-in-time governance or population-wide bulk semantics remains incomplete.

A primary/regulatory reference path was also checked using SEC EDGAR/XBRL documentation. SEC provides structured JSON APIs and nightly bulk archives, but its regulatory scope is U.S.-centric and therefore does not by itself solve the STOXX Europe 600/global architecture target. It is retained only as evidence for the primary-source-versus-aggregator architecture comparison and is **not** admitted to the five-candidate inventory.

No open-ended second pass was performed.

## 10. Candidate Inventory

| Candidate_ID | Source | Source Type | Commercial/Public | Access | Final Discovery Classification |
|---|---|---|---|---|---|
| `DISC-01-LSEG` | LSEG Company Fundamentals / Worldscope | global normalized fundamentals + as-reported + point-in-time | Commercial | API, DaaS, bulk/feed, cloud/FTP depending product | `DISCOVERED_CANDIDATE` |
| `DISC-02-FACTSET` | FactSet Fundamentals DataFeed | global normalized fundamentals datafeed | Commercial | DataFeed / structured loader and database/file delivery | `DISCOVERED_CANDIDATE` |
| `DISC-03-EODHD` | EODHD Fundamentals + Bulk Fundamentals API | structured commercial fundamentals API | Commercial | REST API, JSON/CSV bulk | `DISCOVERED_CANDIDATE` |
| `DISC-04-FMP` | Financial Modeling Prep | structured financial-data API | Commercial / free tiers exist | REST API | `DISCOVERY_EVIDENCE_INSUFFICIENT` |
| `DISC-05-SIMFIN` | SimFin | fundamentals API + bulk files | Commercial / public plans | Web/Python API, bulk CSV | `DISCOVERY_EVIDENCE_INSUFFICIENT` |

**Concrete Candidates Assessed: 5**

Alpha Vantage was not researched and is not counted; governance fixes it as `PROHIBITED_OUT_OF_SCOPE`.

## 11. Candidate Evidence Records

### 11.1 DISC-01-LSEG — LSEG Company Fundamentals / Worldscope

#### OFFICIAL SOURCE FACT

Material official evidence:

1. **LSEG — Fundamentals (As Reported)**  
   URL: https://www.lseg.com/en/data-catalogue/company-data/company-fundamentals/fundamentals-as-reported  
   Publisher: LSEG  
   Evidence date: current page, undated; research date 2026-09-11  
   Evidence type: official data catalogue  
   Supported claims: global regional coverage; 110,000+ public companies; history from 1983 with non-U.S. from 1996; annual and interim statement data; amendments/restatements; income, balance sheet, cash flow, segments/notes; API/Web Service/Cloud/FTP/Bulk/Snowflake delivery and structured formats.

2. **LSEG — Backtest your portfolio performance / Point-in-Time data**  
   URL: https://www.lseg.com/en/data-analytics/asset-management-solutions/portfolio-management/backtest-your-portfolio-performance  
   Publisher: LSEG  
   Evidence date: current page, undated; research date 2026-09-11  
   Evidence type: official methodology/product page  
   Supported claims: point-in-time data retains preliminary/final/restated values and exact availability timestamp; Worldscope and LSEG Financials have decades of coverage and daily updating.

3. **LSEG Developer — Company Fundamentals via DaaS**  
   URL: https://developers.lseg.com/en/api-catalog/daas/DaaS/Products/CompanyFundamentalsViaDaaS  
   Publisher: LSEG Developer Community  
   Evidence date: user guide 2025-07-14; addenda 2025-06-09 and 2026-05-06 visible; research date 2026-09-11  
   Evidence type: official technical/product documentation  
   Supported claims: standardized and as-reported primary statements, segments, customers, analytics, REIT property and industry metrics; full-depth history; DaaS delivery; reference-data/symbology history documentation exists.

4. **LSEG Developer — DaaS Bulk Data Feed**  
   URL: https://developers.lseg.com/en/api-catalog/daas/DaaS/QuickStart/AccessingDaaSProducts/BulkDataFeed  
   Publisher: LSEG Developer Community  
   Evidence date: file-retrieval guide dated 2026-04-30; research date 2026-09-11  
   Evidence type: official technical documentation  
   Supported claims: initialization files plus incremental updates for maintaining local copies of curated datasets through documented APIs.

#### DISCOVERY INFERENCE

The public evidence is unusually complete across global breadth, statement semantics, historical depth, industry-specific data, point-in-time controls and repeatable bulk refresh architecture. Exact licensing/cost and precise canonical identifier joins still require formal qualification.

#### Required fields

- Structured format: SUPPORTED
- Bulk/batch method: SUPPORTED
- Historical fundamentals: SUPPORTED
- Historical depth: early 1980s U.S.; 1990s non-U.S.; product-dependent specifics
- FY: SUPPORTED
- Quarterly/interim: SUPPORTED
- TTM: derivable/available within broader normalized environment; exact source semantics to qualify
- Currency metadata: credible but exact canonical field contract to qualify
- Company identifiers: strong entity-linked platform evidence
- Security identifiers / ISIN / exchange/MIC: mapping path appears strong through LSEG symbology/reference products; exact fields to qualify
- Publication/report timing: STRONG
- Restatement handling: SUPPORTED
- Sector coverage: broad; explicit REIT/industry data and cross-industry standardized fundamentals
- Missing-data behavior: exact status contract requires qualification
- Refresh: STRONG
- Licensing: Enterprise/contractual; exact permitted storage/use UNKNOWN until qualification
- 600 scale: SUPPORTED
- 2527 scale: SUPPORTED
- Automation: SUPPORTED
- Point-in-time: STRONG
- Evidence confidence: HIGH

### 11.2 DISC-02-FACTSET — FactSet Fundamentals DataFeed

#### OFFICIAL SOURCE FACT

1. **FactSet — At a Glance: Fundamentals DataFeed**  
   URL: https://insight.factset.com/resources/at-a-glance-factset-fundamental-datafeed  
   Publisher: FactSet  
   Evidence date: product/content statistics explicitly as of August 2019; research date 2026-09-11  
   Evidence type: official product/coverage page  
   Supported claims: annual and interim global financial-statement database; history beginning 1980; at the documented date 86,000+ companies in 115+ countries, annual 1980, semiannual 1994, quarterly 1995; 750+ data items; standardized accounting treatment; primary-source-document collection; Commercial, Bank, Insurance and Other Financial templates.

2. **FactSet — Fundamentals Industry Metrics**  
   URL: https://insight.factset.com/resources/at-a-glance-factset-fundamentals-industry-metrics  
   Publisher: FactSet  
   Evidence date: page states details as of December 2019; research date 2026-09-11  
   Evidence type: official product/coverage page  
   Supported claims: developed/emerging markets; quarterly/semiannual/annual frequency; specialized metrics including banks and REITs; timely filing collection.

3. **FactSet DataFeed Loader User Guide**  
   URL: https://go.factset.com/hubfs/Website_Downloads/DataFeed%20Loader/datafeed%20loader%20userguide.pdf  
   Publisher: FactSet  
   Evidence date: document route current; research date 2026-09-11  
   Evidence type: official technical guide  
   Supported claims: standardized datafeed loading, update sequencing, error recovery and database/file-oriented structured ingestion architecture.

#### DISCOVERY INFERENCE

FactSet clearly warrants formal qualification because the official evidence demonstrates global, periodized, standardized fundamentals and dedicated financial-sector templates plus a repeatable DataFeed delivery model. The main discovery weakness is evidence freshness: the strongest public coverage statistics are explicitly 2019-era. Dedicated historical point-in-time/vintage behavior for the precise Fundamentals feed was not sufficiently established in this pass.

#### Required fields

- Structured format: SUPPORTED
- Bulk/batch method: SUPPORTED
- Historical fundamentals: SUPPORTED
- Historical depth: annual from 1980; semiannual 1994; quarterly 1995 according to 2019 official material
- FY: SUPPORTED
- Quarterly/interim: SUPPORTED
- TTM: exact feed semantics UNKNOWN
- Currency metadata: expected in structured feed but exact public field evidence insufficient here
- Company/security identity: CONDITIONAL pending exact symbology join validation
- Publication/report timing: data-collection timeliness evidenced; formal PIT/vintage model CONDITIONAL
- Provenance: primary-source collection is documented; raw-to-canonical observation fields need qualification
- Restatements: UNKNOWN/needs formal validation
- Sector coverage: STRONG, including Commercial, Bank, Insurance, Other Financial; REIT industry metrics documented
- Missing-data behavior: UNKNOWN
- Refresh: SUPPORTED conceptually through DataFeed/update architecture
- Licensing: commercial/enterprise; exact terms UNKNOWN
- 600 scale: SUPPORTED
- 2527 scale: SUPPORTED
- Automation: SUPPORTED
- Point-in-time: CONDITIONAL
- Evidence confidence: MEDIUM/HIGH due dated coverage statistics

### 11.3 DISC-03-EODHD — EODHD Fundamentals / Bulk Fundamentals API

#### OFFICIAL SOURCE FACT

1. **EODHD — Bulk Fundamentals API**  
   URL: https://eodhd.com/financial-apis/bulk-fundamentals-api-via-extended-fundamentals-plan  
   Publisher: EODHD  
   Evidence date: published approximately 7 months before research; research date 2026-09-11  
   Evidence type: official API documentation  
   Supported claims: bulk fundamentals for many companies; exchange-wide or selected-symbol retrieval; pagination; JSON/CSV; up to 500 symbols/request; any exchange code on the paginated endpoint; local-database synchronization use case; separate full-exchange snapshots for selected exchanges; Extended Fundamentals plan required.

2. **EODHD — Fundamental Data API**  
   URL: https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds  
   Publisher: EODHD  
   Evidence date: current documentation, published about 1.5 years before research; research date 2026-09-11  
   Evidence type: official API documentation  
   Supported claims: major U.S., U.K., EU and Asian exchanges; company/profile, valuation, earnings and full statements; non-U.S. equities supported; structured financial statements and currency fields; identity/metadata including ISIN, LEI, OpenFIGI, PrimaryTicker and exchange context; report/filing dates documented in financial-record structures.

3. **EODHD — MCP/API documentation**  
   URL: https://eodhd.com/financial-apis/mcp-server-for-financial-data-by-eodhd  
   Publisher: EODHD  
   Evidence date: published approximately 11 months before research; research date 2026-09-11  
   Evidence type: official API capability documentation  
   Supported claims: bulk fundamentals covers General, Highlights, Valuation, Technicals, Earnings and Financials, with up to 500 tickers per call.

#### OFFICIAL SOURCE FACT — material limitation

The current bulk documentation states that the reduced bulk Financials/Earnings history is limited relative to the deeper single-ticker Fundamentals product; the documented bulk history includes only the recent four quarterly and four annual periods for those blocks. This is a material formal-qualification issue for model minimum-history requirements.

#### DISCOVERY INFERENCE

EODHD has the clearest current public evidence among lower-complexity APIs for an actual multi-company bulk fundamentals route, broad exchange support, machine-readable schemas and strong security identifiers. It therefore deserves qualification. However, the formal gate must not confuse deep single-symbol history with the history actually delivered through the bulk endpoint.

#### Required fields

- Structured format: JSON / CSV
- Bulk method: exchange pagination or selected symbols; max 500/request
- Historical fundamentals: SUPPORTED, but bulk-depth limitation is material
- FY: SUPPORTED
- Quarterly: SUPPORTED
- Interim: depends on issuer/report structures; exact model semantics to qualify
- TTM: some API sections/analytics may exist; canonical TTM semantics need qualification
- Currency metadata: SUPPORTED
- Company identifiers: provider company/ticker metadata
- Security identifiers: ISIN, LEI, OpenFIGI, PrimaryTicker, exchange-related identifiers documented
- Publication/report timing: filing/report dates provide a credible anti-look-ahead path
- Restatements: dedicated vintage/restatement handling not proven
- Sector breadth: broad geographic/equity coverage; exact banks/insurance/REIT statement-template completeness requires qualification
- Missing data: documentation acknowledges fields can be empty; detailed null/not-applicable semantics need qualification
- Refresh: bulk sync and hourly full-exchange snapshot architecture documented
- Licensing/access: paid Extended Fundamentals access; details partly by request
- 600 scale: SUPPORTED
- 2527 scale: SUPPORTED / CONDITIONAL on quotas, entitlements and actual population coverage
- Automation: SUPPORTED
- Point-in-time: CONDITIONAL
- Evidence confidence: HIGH

### 11.4 DISC-04-FMP — Financial Modeling Prep

#### OFFICIAL SOURCE FACT

1. **FMP — Financial Statement Symbols List API**  
   URL: https://intelligence.financialmodelingprep.com/developer/docs/stable/financial-symbols-list  
   Publisher: Financial Modeling Prep  
   Evidence date: page undated; research date 2026-09-11  
   Evidence type: official API documentation  
   Supported claims: structured API list of companies with financial statements, including international/global exchanges; income statements, balance sheets and cash-flow statements are available through the API ecosystem.

2. **FMP — Company Core Information Summary API**  
   URL: https://intelligence.financialmodelingprep.com/developer/docs/company-core-information-api  
   Publisher: Financial Modeling Prep  
   Evidence date: page undated; research date 2026-09-11  
   Evidence type: official API documentation  
   Supported claims: company identity fields include CIK, exchange and address.

3. **FMP — Income Statement Growth / related As-Reported APIs**  
   URL: https://intelligence.financialmodelingprep.com/developer/docs/stable/income-statement-growth  
   Publisher: Financial Modeling Prep  
   Evidence date: page undated; research date 2026-09-11  
   Evidence type: official API documentation  
   Supported claims: structured income-statement history/growth API family; official pages reference as-reported income and comprehensive financial statements derived from company filings.

#### UNKNOWN

This bounded pass did not obtain sufficient official evidence establishing all of the following as one governed bulk-fundamentals path: population-wide batch mechanics for statements, explicit throughput at 600/2527 scale, publication/vintage timing for anti-look-ahead, restatement treatment, financial-sector templates/breadth, and deterministic repeated population refresh.

Non-official material encountered during search was not used to promote these unknowns.

#### DISCOVERY JUDGMENT

**Classification: `DISCOVERY_EVIDENCE_INSUFFICIENT`.**

FMP is not rejected: structured global statements and identity APIs are documented. But current official evidence captured in this one pass is not strong enough to justify formal qualification under the project's bulk-source contract.

- 600 scale: CONDITIONAL / UNKNOWN
- 2527 scale: UNKNOWN
- point-in-time: UNKNOWN
- identity: CONDITIONAL
- implementation burden: MEDIUM
- operating burden: MEDIUM
- failure risk: HIGH if promoted without additional evidence
- evidence confidence: MEDIUM for API existence; LOW for bulk-contract completeness

### 11.5 DISC-05-SIMFIN — SimFin

#### OFFICIAL SOURCE FACT

1. **SimFin — Fundamental Data Download**  
   URL: https://www.simfin.com/en/fundamental-data-download/  
   Publisher: SimFin  
   Evidence date: current page; research date 2026-09-11  
   Evidence type: official product/data page  
   Supported claims: API plus bulk CSV; JSON/CSV; 20+ years of history; quarterly and annual balance sheet, P&L and cash flow; linked original reports for verification; approximately 5,000 U.S. stocks explicitly described.

2. **SimFin — Technical Updates to API v3 and Bulk Download**  
   URL: https://www.simfin.com/en/technical-updates-to-api-v3-and-bulk-download/  
   Publisher: SimFin  
   Evidence date: update entries through 2024 shown; research date 2026-09-11  
   Evidence type: official technical change log  
   Supported claims: structured statement endpoints; ISO currency strings; separate Banks template evidence and continuing bulk/API schema maintenance.

3. **SimFin — Roadmap**  
   URL: https://www.simfin.com/en/roadmap/  
   Publisher: SimFin  
   Evidence date: roadmap entries primarily 2023; research date 2026-09-11  
   Evidence type: official roadmap  
   Supported claims: 5,000+ North American stocks; ISIN added to exports; 20 years history at that stage.

4. **SimFin — Data License Agreement**  
   URL: https://www.simfin.com/en/commercial-license/  
   Publisher: SimFin Analytics GmbH  
   Evidence date: current page; research date 2026-09-11  
   Evidence type: official licensing terms  
   Supported claims: explicit license classes for non-commercial, commercial/internal and redistribution use; API/bulk data are covered by the license contract.

#### OFFICIAL SOURCE FACT — material coverage limitation

The current public fundamentals page states that nearly 5,000 U.S. stocks are covered and describes Canada/EU/Asia expansion as something to be made available successively. That is not sufficient evidence that current STOXX Europe 600 or the cross-market Research Partial 2527 can be covered today.

#### DISCOVERY JUDGMENT

**Classification: `DISCOVERY_EVIDENCE_INSUFFICIENT`.**

SimFin has strong bulk/history/provenance mechanics and deserves retention as an architecture reference. It does not advance because geographic/population coverage for the actual project targets is not established by current official public evidence.

- 600 scale: UNKNOWN for STOXX Europe 600
- 2527 scale: UNKNOWN
- historical statements: SUPPORTED
- period semantics: SUPPORTED for annual/quarterly
- point-in-time: CONDITIONAL/UNKNOWN
- identity: CONDITIONAL, with ISIN evidence
- implementation burden: LOW/MEDIUM
- operating burden: LOW/MEDIUM
- failure risk: MEDIUM/HIGH due target-market coverage uncertainty
- evidence confidence: HIGH for mechanics; LOW/MEDIUM for required geography

## 12. Structured / Bulk Access Assessment

| Candidate | Structured Access | Bulk Capability | Deterministic Route | Assessment |
|---|---|---|---|---|
| LSEG | API/DaaS/bulk/feed | SUPPORTED | SUPPORTED through initialization + incremental update architecture | STRONG |
| FactSet | DataFeed / loader / database-files | SUPPORTED | SUPPORTED conceptually | STRONG |
| EODHD | REST JSON/CSV | SUPPORTED; paginated up to 500/request | SUPPORTED | STRONG |
| FMP | REST API | population-wide statement bulk path not sufficiently evidenced | CONDITIONAL / UNKNOWN | INSUFFICIENT |
| SimFin | API + bulk CSV | SUPPORTED | SUPPORTED mechanically | STRONG mechanically; geography unresolved |

### DISCOVERY JUDGMENT

At least three candidates meet the discovery threshold for structured scalable acquisition without relying on manual company-by-company research.

## 13. Historical Fundamentals Assessment

### OFFICIAL SOURCE FACT

- LSEG: decades of standardized/as-reported history; early 1980s U.S. and 1990s non-U.S. evidence, with Worldscope/LSEG Financials point-in-time products.
- FactSet: annual data from 1980, semiannual from 1994 and quarterly from 1995 in the official 2019 coverage statement.
- EODHD: deep history exists in the broader fundamentals product, while the bulk endpoint exposes a materially shorter recent history for financial blocks.
- FMP: historical statement API families are evident, but depth and bulk-history contract were not sufficiently established in this pass.
- SimFin: 20+ years documented for paid/full data access and annual/quarterly statements.

### DISCOVERY JUDGMENT

Historical fundamentals credible candidate: **YES**. LSEG and FactSet clearly satisfy discovery-level historical-depth expectations; EODHD requires formal minimum-history testing at the bulk-route level.

## 14. Period Semantics Assessment

| Candidate | FY | Quarterly / Interim | TTM | Period-End Governance | Discovery Assessment |
|---|---|---|---|---|---|
| LSEG | SUPPORTED | SUPPORTED | PARTIAL / to qualify | SUPPORTED | STRONG |
| FactSet | SUPPORTED | SUPPORTED | UNKNOWN | SUPPORTED conceptually | STRONG for annual/interim; TTM unknown |
| EODHD | SUPPORTED | SUPPORTED | PARTIAL / to qualify | SUPPORTED | STRONG |
| FMP | SUPPORTED/PARTIAL | SUPPORTED/PARTIAL | UNKNOWN | PARTIAL | INSUFFICIENT for full contract |
| SimFin | SUPPORTED | SUPPORTED | derived metrics available, exact taxonomy to qualify | SUPPORTED | STRONG mechanically |

Period semantics credible candidate: **YES**.

## 15. Company / Security Identity Assessment

### OFFICIAL SOURCE FACT / DISCOVERY INFERENCE

- LSEG: company fundamentals are delivered inside a large entity-linked/reference-data ecosystem, and DaaS documentation includes reference-data/symbology-with-history material. Exact project join keys remain a qualification item.
- FactSet: stable entity/security architecture is strongly plausible within the DataFeed ecosystem, but exact public ISIN/MIC/share-class joins were not fully evidenced here. Classification therefore remains CONDITIONAL for project mapping.
- EODHD: the official fundamentals documentation directly exposes ISIN, LEI, OpenFIGI, PrimaryTicker and exchange-related metadata, producing the strongest explicit discovery-level security mapping evidence of the three handoff candidates.
- FMP: CIK and exchange are officially documented; broader canonical Company/Security mapping remains CONDITIONAL.
- SimFin: ISIN is officially stated as included in exports; target geography remains unresolved.

### DISCOVERY JUDGMENT

Company/Security Mapping credible candidate: **YES**. Mapping still requires formal qualification; no candidate is promoted to Universe Identity Authority.

## 16. Point-in-Time Assessment

| Candidate | PIT / Timing Classification | Evidence |
|---|---|---|
| LSEG | STRONG | explicit point-in-time values including preliminary/final/restated states and exact availability timestamps |
| FactSet | CONDITIONAL | timely collection/publication workflow documented, but a dedicated historical vintage contract for the exact Fundamentals feed was not sufficiently established in this pass |
| EODHD | CONDITIONAL | report/filing dates support anti-look-ahead controls, but full historical vintage/restatement behavior is not proven |
| FMP | UNKNOWN | official evidence captured did not establish availability-date/vintage governance strongly enough |
| SimFin | CONDITIONAL / UNKNOWN | original report links and statement history are strong; full publication/vintage semantics were not established |

Point-in-time credible candidate: **YES**, because LSEG has explicit official evidence.

## 17. Provenance Assessment

### OFFICIAL SOURCE FACT

- LSEG as-reported content explicitly preserves source-aligned disclosures and original-document linking, alongside standardized data.
- FactSet states that Fundamentals collection is based on primary source documents and standardized treatment.
- EODHD provides structured provider-origin records, identifiers and statement metadata, but formal raw-document lineage to every normalized field requires qualification.
- SimFin explicitly advertises verification through linked original reports.
- FMP as-reported APIs refer to official company filings, but the full population-wide provenance contract remains insufficiently evidenced.

### DISCOVERY JUDGMENT

Provenance is strongest at discovery level for LSEG and SimFin; FactSet also has credible primary-source lineage. Formal raw-to-normalized traceability remains a qualification responsibility.

## 18. Metric-Family Assessment

Legend: `SUPPORTED`, `PARTIAL`, `UNSUPPORTED`, `UNKNOWN`.

| Metric Family | LSEG | FactSet | EODHD | FMP | SimFin |
|---|---|---|---|---|---|
| Income Statement | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Balance Sheet | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Cash Flow | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Profitability | SUPPORTED / derivable | SUPPORTED / derived items | SUPPORTED / Highlights | PARTIAL | SUPPORTED / derived |
| Growth | SUPPORTED / derivable | SUPPORTED / derivable | PARTIAL/SUPPORTED | SUPPORTED API family | SUPPORTED / derived |
| Capital Efficiency | SUPPORTED / derivable | SUPPORTED / derivable | PARTIAL | PARTIAL | SUPPORTED / derived |
| Leverage | SUPPORTED / derivable | SUPPORTED / derivable | SUPPORTED / derivable | PARTIAL | SUPPORTED / derived |
| Valuation Inputs | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL/SUPPORTED | SUPPORTED / derived |
| Shareholder Returns | PARTIAL/SUPPORTED | PARTIAL/SUPPORTED | PARTIAL/SUPPORTED | UNKNOWN/PARTIAL | PARTIAL |
| Per-Share Data | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED |

Derived metrics do not need to be provider-reported if the qualified source later proves sufficient canonical inputs.

## 19. Sector Coverage Assessment

### OFFICIAL SOURCE FACT

- FactSet explicitly documents four statement profiles: Commercial, Bank, Insurance and Other Financial; REIT industry metrics are separately documented.
- LSEG states broad global company coverage and industry templates; DaaS fundamentals explicitly includes REIT property data and industry operating metrics.
- EODHD covers broad equity geographies and sector/industry classifications, but the discovery evidence did not establish equally strong specialized financial-sector statement templates.
- SimFin technical documentation explicitly shows a Banks template, while broader Insurance/template evidence and required non-U.S. coverage remain incomplete.
- FMP public evidence captured in this pass does not sufficiently establish specialized bank/insurance/REIT treatment at population scale.

### DISCOVERY JUDGMENT

Sector-breadth credible candidate: **YES**, led by FactSet and LSEG. EODHD's sector completeness remains an explicit qualification item.

## 20. Missing-Data Assessment

### DISCOVERY JUDGMENT

No candidate is assumed to satisfy the project's `100% COVERAGE STATUS` contract merely by having broad data.

- LSEG / FactSet: structured institutional feeds plausibly permit deterministic absence detection, but exact missing/not-applicable codes must be validated.
- EODHD: documentation notes fields may be empty; the distinction between absent, not reported and not applicable needs qualification.
- FMP: missingness semantics insufficiently evidenced.
- SimFin: structured bulk/API files make missingness detectable, but canonical reason states require qualification.

No zero/null/not-applicable inference is authorized at discovery stage.

## 21. Restatement Assessment

| Candidate | Restatement Classification | Basis |
|---|---|---|
| LSEG | SUPPORTED | as-reported page explicitly includes amendments/restatements; PIT product distinguishes preliminary/final/restated availability states |
| FactSet | PARTIAL / UNKNOWN | primary-source/timely collection is documented; explicit historical restatement-vintage behavior needs validation |
| EODHD | UNKNOWN | filing dates exist; dedicated restatement/vintage contract not established |
| FMP | UNKNOWN | as-reported statements exist, restatement governance not sufficiently evidenced |
| SimFin | PARTIAL / UNKNOWN | original-report-based data and re-extraction updates are documented; formal vintage behavior not established |

## 22. Scale Assessment

| Candidate | 600 Scale | 2527 Scale | Basis |
|---|---|---|---|
| LSEG | SUPPORTED | SUPPORTED | global company counts, broad exchange coverage, bulk/DaaS delivery |
| FactSet | SUPPORTED | SUPPORTED | documented global database and DataFeed architecture; statistics dated 2019 |
| EODHD | SUPPORTED | SUPPORTED / CONDITIONAL | up to 500/request with pagination; broad exchange universe; qualification needed on entitlements/coverage completeness |
| FMP | CONDITIONAL / UNKNOWN | UNKNOWN | global statements symbol list exists but bulk statement mechanics/throughput insufficiently established |
| SimFin | UNKNOWN for Europe target | UNKNOWN | strong mechanics but current official target-market coverage not established |

### DISCOVERY JUDGMENT

600-scale credible candidate: **YES**. 2527-scale credible candidate: **YES**. These are discovery-level capability statements, not acquisition authorization.

## 23. Refresh Assessment

| Candidate | Refresh Capability | Discovery Basis |
|---|---|---|
| LSEG | STRONG | bulk initialization plus incremental-update architecture; daily/PIT product updating evidence |
| FactSet | STRONG / CONDITIONAL | DataFeed loader/update sequencing and timely collection support repeatability; exact cadence contract to qualify |
| EODHD | STRONG | designed for local fundamentals DB sync; paginated live route and cached exchange snapshot route |
| FMP | CONDITIONAL | regularly updated API lists/statements evident; deterministic population refresh not sufficiently evidenced |
| SimFin | STRONG mechanically | maintained API/bulk exports and frequent statements, but global target coverage unresolved |

Repeated refresh credible candidate: **YES**.

## 24. Licensing / Access Assessment

### OFFICIAL SOURCE FACT

- LSEG: commercial/enterprise datasets; access is subscription/contract based. Public evidence establishes delivery mechanisms, not exact project license rights.
- FactSet: commercial datafeed; public pages direct prospects to sales. Exact storage/automation rights require qualification.
- EODHD: Bulk Fundamentals requires an Extended Fundamentals subscription; plan details are partly provided on request. No account or quote request was made.
- FMP: official docs expose free/premium API access paths, but no plan was activated and detailed bulk-use rights were not relied upon.
- SimFin: official license agreement explicitly distinguishes non-commercial, commercial/internal and redistribution rights.

### DISCOVERY JUDGMENT

No candidate is rejected solely because exact commercial pricing is not public. Exact price is unnecessary for this handoff. No foreign-currency provider price is relied upon in this report.

## 25. Implementation / Operating Burden

These ratings are **DISCOVERY JUDGMENT**, not provider facts.

| Candidate | Implementation Burden | Operating Burden | Reason |
|---|---|---|---|
| LSEG | HIGH | MEDIUM/HIGH | rich enterprise content and PIT/symbology reduce semantic risk but require substantial schema, licensing and mapping design |
| FactSet | HIGH | MEDIUM | mature standardized feed, but formal schema/identity/PIT validation and commercial onboarding are substantial |
| EODHD | MEDIUM | MEDIUM | simpler documented REST/bulk architecture; bulk-history and sector/PIT limitations add governance work |
| FMP | MEDIUM | MEDIUM | API model straightforward, but unresolved bulk/timing/sector evidence creates design uncertainty |
| SimFin | LOW/MEDIUM | LOW/MEDIUM | accessible API/bulk mechanics; target-market coverage is the dominant blocker rather than integration mechanics |

## 26. Failure-Loop Risk

### DISCOVERY JUDGMENT

| Candidate | Failure Risk | Principal risk |
|---|---|---|
| LSEG | LOW/MEDIUM | licensing/complexity and exact canonical mapping, not basic capability |
| FactSet | MEDIUM | dated public coverage evidence plus PIT/restatement specifics require validation |
| EODHD | MEDIUM | bulk-history depth and sector/PIT semantics may fail model minimum contracts |
| FMP | HIGH | too many hard bulk/PIT/refresh dimensions remain unproven |
| SimFin | MEDIUM/HIGH | excellent mechanics may still fail required European/global population coverage |

**Overall Discovery Failure-Loop Risk: MEDIUM.**

The manager stop condition did not trigger because three candidates provide credible structured, historical, population-scale paths. Risk remains controlled by handing only those three to formal evidence validation and by prohibiting acquisition until a later gate.

## 27. Candidate Comparison Matrix

| Candidate | Class | Structured | Bulk | History | Periods | Currency | Identity | PIT | Provenance | Sector breadth | Refresh | 600 | 2527 | Impl. | Oper. | Risk | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LSEG | DISCOVERED_CANDIDATE | STRONG | STRONG | STRONG | STRONG | STRONG/qualify fields | STRONG/COND exact joins | STRONG | STRONG | STRONG | STRONG | SUPPORTED | SUPPORTED | HIGH | MED/HIGH | LOW/MED | HIGH |
| FactSet | DISCOVERED_CANDIDATE | STRONG | STRONG | STRONG | STRONG | CONDITIONAL | CONDITIONAL | CONDITIONAL | STRONG | STRONG | STRONG/COND | SUPPORTED | SUPPORTED | HIGH | MED | MED | MED/HIGH |
| EODHD | DISCOVERED_CANDIDATE | STRONG | STRONG | STRONG overall / limited bulk depth | STRONG | STRONG | STRONG | CONDITIONAL | CONDITIONAL | CONDITIONAL | STRONG | SUPPORTED | SUPPORTED/COND | MED | MED | MED | HIGH |
| FMP | DISCOVERY_EVIDENCE_INSUFFICIENT | STRONG | UNKNOWN/COND | PARTIAL | PARTIAL | UNKNOWN/COND | CONDITIONAL | UNKNOWN | PARTIAL | UNKNOWN | CONDITIONAL | COND/UNKNOWN | UNKNOWN | MED | MED | HIGH | MED |
| SimFin | DISCOVERY_EVIDENCE_INSUFFICIENT | STRONG | STRONG | STRONG | STRONG | STRONG | CONDITIONAL | COND/UNKNOWN | STRONG | PARTIAL | STRONG | UNKNOWN for Europe | UNKNOWN | LOW/MED | LOW/MED | MED/HIGH | HIGH mechanics / LOW-MED geography |

## 28. Candidate Classifications

### DISCOVERY JUDGMENT

- `DISCOVERED_CANDIDATE`: **3**
  - LSEG Company Fundamentals / Worldscope
  - FactSet Fundamentals DataFeed
  - EODHD Fundamentals + Bulk Fundamentals API
- `DISCOVERY_REJECTED`: **0**
- `DISCOVERY_EVIDENCE_INSUFFICIENT`: **2**
  - Financial Modeling Prep
  - SimFin

No source is classified `QUALIFIED_BULK_SOURCE` or `CONDITIONALLY_QUALIFIED`; those statuses are prohibited in discovery.

## 29. Global vs Regional Conclusion

### OFFICIAL SOURCE FACT

LSEG and FactSet both publish evidence of broad multi-region/global standardized company fundamentals. EODHD documents major U.S., U.K., EU and Asian exchange coverage and a cross-exchange bulk route. By contrast, the primary SEC XBRL reference is powerful but U.S.-regulatory in scope, and SimFin's public coverage evidence does not establish the required European/global target today.

### DISCOVERY JUDGMENT

**Preferred Architecture Direction: `GLOBAL_SINGLE_SOURCE`.**

Reason: discovery established at least two credible global-source paths before any need to assemble multiple regional pipelines. A tightly governed fallback may later be justified for residual identity/coverage exceptions, but the evidence does not justify selecting `REGIONAL_GOVERNED_SOURCE_SET` as the primary direction now.

This is an architecture direction only, not provider selection.

## 30. Qualification Handoff Ranking

Only `DISCOVERED_CANDIDATE` sources are ranked.

| Rank | Candidate | Why it deserves qualification | Strongest official evidence | Primary remaining uncertainty | 600 outlook | 2527 outlook | PIT outlook | Failure risk |
|---:|---|---|---|---|---|---|---|---|
| 1 | LSEG Company Fundamentals / Worldscope | strongest combined evidence for global standardized/as-reported fundamentals, PIT, restatements, bulk refresh and industry data | LSEG Fundamentals As Reported + PIT/backtest page + DaaS Company Fundamentals/Bulk Feed docs | exact license/use/storage rights and deterministic joins to project Company_Key/Security_Key | SUPPORTED | SUPPORTED | STRONG | LOW/MEDIUM |
| 2 | FactSet Fundamentals DataFeed | mature global periodized fundamentals and explicit Bank/Insurance/Other Financial templates with DataFeed infrastructure | FactSet Fundamentals DataFeed + Industry Metrics + DataFeed Loader | public coverage stats are dated; exact PIT/restatement and identity join contract | SUPPORTED | SUPPORTED | CONDITIONAL | MEDIUM |
| 3 | EODHD Fundamentals + Bulk Fundamentals API | current explicit multi-company bulk API, broad exchange support, strong identifiers, filing dates and refresh architecture | Bulk Fundamentals docs + Fundamental Data docs | limited history in bulk financial blocks, sector-template completeness, vintage/restatement semantics and entitlement economics | SUPPORTED | SUPPORTED/CONDITIONAL | CONDITIONAL | MEDIUM |

**Qualification Handoff Count: 3**

Quality, not the cap itself, determines the count.

## 31. DISCOVERY RESULT

### FACT

At least one candidate — in fact three — satisfies the discovery threshold of a credible source path worth formal qualification. None is qualified for acquisition by this stage.

### DISCOVERY JUDGMENT

**DISCOVERY RESULT: A — QUALIFICATION CANDIDATE(S) FOUND**

Discovery-level capability summary:

- 600-Scale Credible Candidate: YES
- 2527-Scale Credible Candidate: YES
- Historical Fundamentals Credible Candidate: YES
- Period Semantics Credible Candidate: YES
- Point-in-Time Credible Candidate: YES
- Company/Security Mapping Credible Candidate: YES
- Sector-Breadth Credible Candidate: YES
- Repeated Refresh Credible Candidate: YES

The next gate must independently validate the three handoff candidates against the full Q1–Q20 contract. Discovery success is not qualification.

## 32. Exact Next Authorized Stage

Authorize exactly:

**NEXT AUTHORIZED STAGE: Fundamentals Bulk Source Qualification v2 Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO ACQUISITION — NO INTEGRATION**

That stage may validate the evidence captured for the three handoff candidates and resolve specific remaining qualification uncertainties.

It may not automatically:

- acquire fundamentals;
- call live company-data endpoints;
- create provider accounts or trials;
- integrate a provider;
- build a bulk fundamentals dataset;
- build Company/Security mappings;
- normalize data;
- calculate model coverage or rankings;
- restart Guru;
- modify Universe membership.

## 33. Guru Boundary

### FACT

- `AUTHORIZED NEXT GURU STAGE: NONE`
- Guru Restart: NO / NOT AUTHORIZED
- New STOXX Europe 600 Ranking: NO / NOT AUTHORIZED
- New Guru Top 5: NO / NOT AUTHORIZED
- Legacy 25-stock Ranking: `LEGACY PILOT`

Discovery is for reusable shared fundamentals infrastructure, not a Guru-specific truth store.

## 34. Fundamentals Boundary

### FACT

- Fundamentals Acquired: NO
- Live Fundamentals API Called: NO
- Trial Activated: NO
- Provider Account Created: NO
- Bulk Dataset Downloaded: NO
- Sample Fundamentals Downloaded: NO
- Provider Integrated: NO
- Company Mapping Built: NO
- Normalization Executed: NO
- Derived Metrics Calculated: NO
- Coverage Calculated: NO
- Ranking Executed: NO

Only provider documentation/capability evidence was researched.

## 35. Universe Boundary

### FACT

Universe Expansion remains:

**PAUSED — NOT ABANDONED**

Baseline remains:

- Research Partial = 2527
- Strict = 759
- Frozen = 0

No population was selected, reopened, prechecked or written. No Universe/Membership state changed.

## 36. No-Touch Verification

### FACT

This stage performed:

- External Web Research: YES
- Official Provider Documentation Research: YES
- Secondary Evidence Used for Positive Qualification Claim: NO
- Candidate Cap Exceeded: NO
- Concrete Detailed Candidates: 5
- Qualification Handoff Candidates: 3
- Alpha Vantage Research/Evaluation: NO
- Live Fundamentals Endpoint Test: NO
- Fundamentals API Data Call: NO
- API Key Request/Use: NO
- Provider Account Creation: NO
- Trial Activation: NO
- Vendor Contact: NO
- Bulk/Sample Fundamentals Download: NO
- Raw Provider Artifact Creation: NO
- Acquisition Script/Integration Code: NO
- Fundamentals Dataset Build: NO
- Mapping Dataset Build: NO
- Normalization/Derived Metric/Coverage Execution: NO
- Guru Restart: NO
- Universe Write: NO
- Membership Write: NO
- Universe Expansion Resume: NO

Only `docs/spec/Fundamentals_Bounded_External_Source_Discovery.md` is written by this stage.

## Final Discovery State

- `STAGE STATUS: PASS`
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe Expansion: PAUSED — NOT ABANDONED
- External Research Performed: YES
- Candidate Cap: 5
- Concrete Candidates Assessed: 5
- `DISCOVERED_CANDIDATE`: 3
- `DISCOVERY_REJECTED`: 0
- `DISCOVERY_EVIDENCE_INSUFFICIENT`: 2
- Qualification Handoff Count: 3
- Qualification Handoff Candidates: LSEG Company Fundamentals / Worldscope; FactSet Fundamentals DataFeed; EODHD Fundamentals + Bulk Fundamentals API
- Preferred Architecture Direction: `GLOBAL_SINGLE_SOURCE`
- Overall Discovery Failure-Loop Risk: MEDIUM
- `DISCOVERY RESULT: A — QUALIFICATION CANDIDATE(S) FOUND`
- Fundamentals Acquired: NO
- Provider Integrated: NO
- Guru Restart Authorized: NO
- `AUTHORIZED NEXT GURU STAGE: NONE`
- Universe Write: NO
- `NEXT AUTHORIZED STAGE: Fundamentals Bulk Source Qualification v2 Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO ACQUISITION — NO INTEGRATION`

HARD STOP after commit and post-commit verification.
