# Fundamentals Bulk Source Qualification v2 Gate

## 1. Purpose

### FACT

This report executes exactly the authorized stage:

**Fundamentals Bulk Source Qualification v2 Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO ACQUISITION — NO INTEGRATION**

It formally validates exactly the three discovery handoff candidates against the existing Fundamentals Bulk Source Capability Contract:

1. LSEG Company Fundamentals / Worldscope
2. FactSet Fundamentals DataFeed
3. EODHD Fundamentals + Bulk Fundamentals API

No provider is added or substituted. No fundamentals are acquired. No provider is integrated. No Guru workflow or Universe work is executed.

**STAGE STATUS: PASS**

**QUALIFICATION RESULT: A — QUALIFIED BULK SOURCE PATH EXISTS**

**Preferred Qualified Path: LSEG Company Fundamentals / Worldscope**

**Preferred Path Classification: QUALIFIED_BULK_SOURCE**

**Qualified Runner-Up: EODHD Fundamentals + Bulk Fundamentals API**

**NEXT AUTHORIZED STAGE: Fundamentals Bulk Acquisition & Mapping Design Gate — READ-ONLY / SPEC ONLY — PREFERRED QUALIFIED PATH ONLY — NO DATA ACQUISITION**

## 2. Authorized Stage

### FACT

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Authorized stage: `Fundamentals Bulk Source Qualification v2 Gate — READ-ONLY / EXTERNAL-EVIDENCE VALIDATION ONLY — NO ACQUISITION — NO INTEGRATION`
- Expected start HEAD: `9519b0729f9c92c8a5986980dbcdaa426def0bf6`
- Expected start commit: `Fundamentals bounded external source discovery`
- Required parent: `e49a8208c44153158f65ba7e57e0bf1b34896a22`
- Candidate lock: exactly three candidates
- New provider discovery: prohibited
- Live fundamentals calls: prohibited
- Acquisition/integration: prohibited

## 3. Start HEAD Verification

### FACT

At stage start and immediately before repository write:

- `HEAD = 9519b0729f9c92c8a5986980dbcdaa426def0bf6`
- `origin/main = 9519b0729f9c92c8a5986980dbcdaa426def0bf6`
- commit message = `Fundamentals bounded external source discovery`
- parent = `e49a8208c44153158f65ba7e57e0bf1b34896a22`

**Start Gate Result: PASS**

No merge, rebase, repair or alternate-head continuation occurred.

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
- Nifty 50
- Mexico

No baseline value or parked state changes in this stage.

Productive trading authority remains exclusively **Welt-Swing v7.2**. WELT-SWING-LONG remains **DEV / RESEARCH / SHADOW**.

## 5. Normative Inputs

### FACT

The following repository documents are normative:

1. `docs/spec/Fundamentals_Research_Layer_Architecture_and_Bulk_Source_Capability_Gate.md`
2. `docs/spec/Fundamentals_Bulk_Source_Qualification_Gate.md`
3. `docs/spec/Fundamentals_Bulk_Source_Discovery_Manager_Gate.md`
4. `docs/spec/Fundamentals_Bounded_External_Source_Discovery.md`

The architecture contract is not redesigned here. Candidate identity and the three-candidate handoff are inherited from the discovery report.

## 6. Candidate Lock

### FACT

Exactly these candidates were evaluated:

- `QUAL2-01-LSEG` — LSEG Company Fundamentals / Worldscope
- `QUAL2-02-FACTSET` — FactSet Fundamentals DataFeed
- `QUAL2-03-EODHD` — EODHD Fundamentals + Bulk Fundamentals API

No substitute provider was researched. No evidence-insufficient or rejected discovery candidate was promoted. Alpha Vantage remained prohibited and was not researched.

## 7. Evidence Method

### FACT

External evidence validation was limited to public documentation. Evidence hierarchy applied:

1. official technical/API documentation;
2. official schema/data-dictionary/product documentation;
3. official methodology/coverage documentation;
4. official legal/licensing/pricing documentation;
5. official knowledge-base/support documentation;
6. secondary evidence only where supplementary.

Research date: **2026-09-11**.

No accounts, credentials, trials, API keys, live fundamentals queries, sample-data acquisition, scraping, endpoint reverse-engineering or downloads were used.

### QUALIFICATION JUDGMENT

A `PASS` requires direct or strongly supported capability evidence. `CONDITIONAL` is used only for bounded uncertainty where underlying capability is strongly evidenced and a later design/validation step can close the issue. `UNKNOWN` is never converted to PASS.

---

## 8. Candidate 1 — LSEG / Worldscope

### 8.1 Official Evidence Record

#### OFFICIAL FACT — Company Fundamentals / As Reported

- Source: LSEG
- Title: `Fundamentals (As Reported)`
- URL: `https://www.lseg.com/en/data-catalogue/company-data/company-fundamentals/fundamentals-as-reported`
- Evidence date: undated/current page
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- global geographic coverage across North America, Asia/Pacific, EMEA and Latin America/Caribbean;
- 110,000+ public companies on the current page;
- U.S. history from 1983 and non-U.S. from 1996;
- income statement, balance sheet, cash flow, notes and segments;
- annual and interim periods;
- amendments/restatements;
- API, Web Service, Cloud, FTP, Bulk and Snowflake delivery;
- structured output formats including JSON, CSV, XML, SQL and text;
- explicit coverage of ordinary shares, preference shares, depositary receipts and other equity instruments.

#### OFFICIAL FACT — Company Fundamentals DaaS User Guide

- Source: LSEG Developer Community
- Title: `LSEG Company Fundamentals – Data as a Service`
- URL: `https://developers.lseg.com/content/dam/devportal/api-families/lseg-data-platform/data-as-a-service/userguides/fundamentals/LSEGDataasaServiceFundamentalsuserguide.pdf`
- Document version: 100.02
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- common data model and consistent structures;
- hosted SQL database or bulk database/file distribution;
- standardized, as-reported and combined variants;
- full fundamentals universe of active and inactive organizations;
- equity concordance data;
- data dictionary, field descriptions and entity relationship diagrams;
- database updates every 2 hours;
- bulk-file feed updates every 3 hours;
- weekly initialization files;
- primary statements plus footnotes, segments, major customers, ratios and industry metrics;
- LSEG permanent identifiers plus CUSIP, SEDOL, ISIN, RIC, MIC and LEI for mapping;
- explicit REIT property data and industry operating metrics.

#### OFFICIAL FACT — LSEG Point-in-Time Data

- Source: LSEG
- Title: `Backtest your portfolio performance`
- URL: `https://www.lseg.com/en/data-analytics/asset-management-solutions/portfolio-management/backtest-your-portfolio-performance`
- Evidence date: undated/current page
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- Worldscope Point-in-Time coverage of almost 90,000 companies from 1983;
- daily updating;
- all reported values including preliminary, final and restated values;
- timestamps to the exact date/time data became available;
- historical backtest use without relying only on period-end lag assumptions.

#### OFFICIAL FACT — DaaS Bulk Data Feed

- Source: LSEG Developer Community
- Title: `Bulk Data Feed`
- URL: `https://developers.lseg.com/en/api-catalog/daas/DaaS/QuickStart/AccessingDaaSProducts/BulkDataFeed`
- Evidence date: File Retrieval API guide dated 2026-04-30
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- initialization files for complete local database seeding;
- incremental updates when source content changes;
- API-based file retrieval;
- local database maintenance as an explicit supported use pattern.

### 8.2 Candidate Summary

### QUALIFICATION JUDGMENT

LSEG demonstrates the strongest evidence set across the full architecture: global scale, normalized and as-reported financials, deep history, explicit point-in-time data, bulk delivery, incremental refresh, rich symbology, industry templates, REIT content and maintained data dictionaries.

The principal unresolved details are contract/package-specific rather than capability-level: exact entitlement/licensing terms, exact monetary-currency field names, and precise missing/not-applicable code semantics available inside the subscribed data dictionary. These are bounded design-stage questions and do not undermine the demonstrated source architecture.

**Final Classification: QUALIFIED_BULK_SOURCE**

---

## 9. Candidate 2 — FactSet Fundamentals DataFeed

### 9.1 Official Evidence Record

#### OFFICIAL FACT — Fundamentals DataFeed

- Source: FactSet
- Title: `At a Glance: FactSet Fundamentals DataFeed`
- URL: `https://insight.factset.com/resources/at-a-glance-factset-fundamental-datafeed`
- Product statistics explicitly as of August 2019
- Research date: 2026-09-11
- Evidence strength: MEDIUM/STRONG

Supports:

- global annual and interim financial statements;
- reported and derived data items;
- history beginning 1980;
- worldwide developed and emerging markets;
- 86,000+ companies in 115+ countries at the stated 2019 snapshot;
- annual history from 1980, semiannual from 1994, quarterly from 1995;
- 750+ data items;
- standardized accounting treatment based on primary source documents;
- Commercial, Bank, Insurance and Other Financial statement templates;
- per-share data, ratios, segments and pension detail.

#### OFFICIAL FACT — Industry Metrics

- Source: FactSet
- Title: `At a Glance: FactSet Fundamentals Industry Metrics`
- URL: `https://insight.factset.com/resources/at-a-glance-factset-fundamentals-industry-metrics`
- Statistics include historical start dates by industry; page current at research date
- Research date: 2026-09-11
- Evidence strength: STRONG for sector breadth

Supports:

- developed and emerging markets;
- quarterly, semiannual and annual frequency;
- explicit bank and REIT industry metrics;
- intraday delivery frequency for the industry-metrics dataset;
- source collection from filings, exchanges, company sites and releases.

#### OFFICIAL FACT — DataFeed Loader

- Source: FactSet
- Title: `DataFeed Loader User Guide`
- URL: `https://go.factset.com/hubfs/Website_Downloads/DataFeed%20Loader/datafeed%20loader%20userguide.pdf`
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- bundled structured file download and loading into local databases;
- sequence-aware updates;
- repeatable reruns without data corruption;
- timestamped logs;
- failure recovery;
- bulk merge/copy/merge workflows for common database platforms.

#### OFFICIAL FACT — Symbology / Entity Model

- Source: FactSet official materials
- Titles: `Future Proofing Your Data`; FactSet symbology references in official product materials
- URLs: `https://insight.factset.com/future-proofing-your-data` and FactSet technical symbology documentation
- Research date: 2026-09-11
- Evidence strength: MEDIUM/STRONG

Supports:

- entity-centric symbology and Entity ID model;
- connection of entity, security and listing identifiers;
- use of ISIN and primary exchange/listing references in FactSet security-reference materials.

### 9.2 Candidate Summary

### QUALIFICATION INFERENCE

FactSet clearly demonstrates enterprise-scale fundamentals, deep global history, industry-specific templates and a deterministic DataFeed/Loader architecture. The remaining public-evidence gap is concentrated in hard governance details for the exact Fundamentals DataFeed: explicit observation-level publication/availability fields, exact missing/not-applicable semantics, original reporting-currency field contract, and the precise provenance/revision representation available in the subscribed feed.

FactSet does have separate point-in-time products, including Estimates PIT, but those cannot be silently treated as proof that the Fundamentals DataFeed itself preserves full historical vintage fundamentals. Same-day collection descriptions establish timeliness, not a complete vintage-history contract.

### QUALIFICATION JUDGMENT

The underlying bulk capability is strong, but too many hard governance fields remain conditional in public evidence to award full qualification in this gate.

**Final Classification: CONDITIONALLY_QUALIFIED**

**Blocking conditions:** validate the exact Fundamentals DataFeed schema for (1) publication/availability timing, (2) missing/not-applicable encoding, (3) reporting currency, and (4) observation-level revision/provenance semantics before acquisition design.

---

## 10. Candidate 3 — EODHD Fundamentals + Bulk Fundamentals API

### 10.1 Official Evidence Record

#### OFFICIAL FACT — Fundamentals API

- Source: EODHD
- Title: `Fundamental Data API — Stocks, ETFs, Funds, Indices`
- URL: `https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds`
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- common stock/equity fundamentals for U.S. and non-U.S. exchanges;
- major U.S. company history from 1985 and non-U.S. generally from 2000;
- yearly and quarterly financial statements;
- Income Statement, Balance Sheet and Cash Flow sections;
- per-statement currency symbol;
- each yearly and quarterly report entry carries `date` and `filing_date`;
- identity fields including ticker, exchange, currency, country, ISIN, CUSIP, CIK and `PrimaryTicker` in documented stock responses;
- explicit statement that some fields may be empty when a company does not report a datapoint.

#### OFFICIAL FACT — Bulk Fundamentals API

- Source: EODHD
- Title: `Bulk Fundamental Data API — Stocks, ETFs, Funds`
- URL: `https://eodhd.com/financial-apis/bulk-fundamentals-api-via-extended-fundamentals-plan`
- Published roughly seven months before research
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- many-company bulk fundamentals in one structured route;
- exchange-wide, paginated or selected-symbol retrieval;
- JSON/CSV;
- up to 500 symbols per request;
- bulk endpoint supports any exchange code, including non-U.S. exchanges such as LSE and XETRA;
- documented use for keeping a local fundamentals database synchronized;
- full-exchange cached snapshots for six exchanges;
- bulk records intentionally contain a reduced field set and only the last four quarters/four years of history;
- versioned response templates.

#### OFFICIAL FACT — API Limits

- Source: EODHD
- Title: `API Limits: calls, requests, consumption`
- URL: `https://eodhd.com/financial-apis/api-limits`
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- default 100,000 API calls/day for paid plans/marketplace products;
- 1,000 requests/minute;
- standard Fundamentals requests cost 10 call units;
- bulk exchange requests have documented call-unit costs.

#### OFFICIAL FACT — Exchanges API

- Source: EODHD
- Title: `Exchanges API: Supported Exchanges & Ticker Lists`
- URL: `https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours`
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- 70 supported exchanges as of August 2026;
- operating MIC, country and trading currency in the exchange-list response;
- exchange symbol lists for active and delisted instruments;
- exchange code used consistently across APIs/bulk endpoints.

#### OFFICIAL FACT — Terms / Storage

- Source: EODHD
- Title: `Terms and Conditions`
- URL: `https://eodhd.com/financial-apis/terms-conditions`
- Research date: 2026-09-11
- Evidence strength: STRONG

Supports:

- non-professional personal users may store, manipulate and analyze data for private non-commercial purposes;
- redistribution/resale/access sharing restrictions apply;
- professional/commercial use requires the corresponding commercial arrangement.

#### OFFICIAL FACT — Public Pricing

- Source: EODHD
- Title: `Pricing plans`
- URL: `https://eodhd.com/pricing`
- Research date: 2026-09-11
- Evidence strength: STRONG

Public Fundamentals Data Feed price displayed at research date: **USD 59.99/month**, approximately **EUR 51.74/month** using USD/EUR 0.86254 on 2026-09-11. This public price does **not** include the Extended Fundamentals bulk entitlement; official bulk documentation states Extended Fundamentals details are provided on request. Therefore actual bulk-source commercial cost remains UNKNOWN.

### 10.2 Candidate Summary

### QUALIFICATION INFERENCE

EODHD demonstrates a concrete, current and highly automatable global bulk path. The general Fundamentals API supplies deeper history than the reduced bulk records, and the documented call limits make systematic per-symbol historical retrieval for a 2,527-security research population technically feasible without implying manual company-by-company research. The bulk endpoint itself is efficient for refresh/current-state coverage.

The source exposes `filing_date`, period dates, statement currencies, ISIN/CUSIP/CIK/PrimaryTicker, exchange codes and MICs. That is sufficient for current-screening anti-look-ahead governance and deterministic company/security reconciliation when combined with the project canonical identity layer.

The main limitations are weaker than LSEG on true vintage point-in-time history, public restatement lineage, original-source provenance and sector-specialized semantics. These are material for historical backtesting but do not prevent current/prospective fundamentals screening under the architecture, provided the limitations are preserved.

### QUALIFICATION JUDGMENT

The hard bulk-source contract is sufficiently evidenced for a later design gate. No live data validation or acquisition has occurred.

**Final Classification: QUALIFIED_BULK_SOURCE**

---

## 11. Q1–Q20 Assessment

### 11.1 LSEG / Worldscope

| Gate | Result | Qualification basis |
|---|---|---|
| Q1 Batch / Bulk | PASS | DaaS SQL database and bulk file distribution are explicit. |
| Q2 Population Scale | PASS | 110k+ public-company coverage and global markets; 600/2527 are far below documented scale. |
| Q3 Reproducibility | PASS | common data model, initialization files, recurring incremental updates. |
| Q4 Historical Periods | PASS | decades of company history; full-depth history in DaaS. |
| Q5 Metric Semantics | PASS | standardized + as-reported models, data dictionaries/glossaries. |
| Q6 Period Semantics | PASS | annual/interim and quarterly delivery; PIT history separate where required. |
| Q7 Currency | CONDITIONAL | capability is structurally supported, but exact monetary/reporting-currency field contract is entitlement/data-dictionary dependent and must be pinned in design. |
| Q8 Identity | PASS | LSEG permanent IDs plus CUSIP/SEDOL/ISIN/RIC/MIC/LEI. |
| Q9 Timing | PASS | dedicated PIT fundamentals with exact availability timestamps. |
| Q10 Provenance | PASS | source-aligned as-reported layer, provider identifiers, structured data dictionary and original-document linkage in the broader product. |
| Q11 Missingness | CONDITIONAL | deterministic schema exists; exact missing/not-applicable code semantics must be frozen from the subscribed dictionary before acquisition. |
| Q12 Sector | PASS | global cross-industry templates, REIT property data and industry metrics. |
| Q13 Restatements | PASS | amendments/restatements and PIT preliminary/final/restated values explicitly supported. |
| Q14 Corporate Actions | CONDITIONAL | symbology/history architecture exists; exact issuer/security corporate-action mapping contract belongs to design gate. |
| Q15 Licensing | CONDITIONAL | subscription/entitlement model explicit; exact internal storage/derived-use rights require contract-level confirmation before acquisition. |
| Q16 Automation | PASS | SQL/bulk feed/file-retrieval APIs and recurring updates. |
| Q17 Throughput | CONDITIONAL | feed cadence documented; customer-specific throughput constraints not public. |
| Q18 Failure Risk | LOW | one governed global source path with strong structured evidence. |
| Q19 Coverage Reporting | PASS | stable structured population and deterministic mapping/missingness can produce explicit coverage records. |
| Q20 Refresh | PASS | database every 2h, bulk updates every 3h, weekly initialization. |

### 11.2 FactSet Fundamentals DataFeed

| Gate | Result | Qualification basis |
|---|---|---|
| Q1 Batch / Bulk | PASS | dedicated DataFeed plus Loader. |
| Q2 Population Scale | PASS | documented 86k+ companies / 115+ countries in official 2019 snapshot. |
| Q3 Reproducibility | PASS | loader sequencing, logs and safe reruns. |
| Q4 Historical Periods | PASS | annual 1980, semiannual 1994, quarterly 1995 in official coverage material. |
| Q5 Metric Semantics | PASS | 750+ standardized items and industry templates. |
| Q6 Period Semantics | PASS | annual/interim/semiannual/quarterly documented. |
| Q7 Currency | CONDITIONAL | exact Fundamentals DataFeed currency-field contract not sufficiently public in this validation pass. |
| Q8 Identity | PASS | entity-centric symbology, FactSet Entity ID, ISIN and listing identifiers supported across FactSet data architecture. |
| Q9 Timing | CONDITIONAL | same-day collection/timeliness documented, but exact observation-level publication/availability fields for this feed remain insufficiently evidenced publicly. |
| Q10 Provenance | CONDITIONAL | collection from primary source documents documented; observation-level source/revision lineage fields need schema validation. |
| Q11 Missingness | CONDITIONAL | exact null/not-applicable/not-covered encoding requires feed-schema confirmation. |
| Q12 Sector | PASS | Commercial, Bank, Insurance, Other Financial; REIT metrics explicit. |
| Q13 Restatements | CONDITIONAL | exact Fundamentals revision/vintage representation not established by public evidence used here. |
| Q14 Corporate Actions | CONDITIONAL | entity/security symbology is strong, but the exact fundamentals-history interaction must be confirmed. |
| Q15 Licensing | CONDITIONAL | commercial DataFeed model clear; exact storage/derived-use terms not public enough. |
| Q16 Automation | PASS | DataFeed Loader supports deterministic local DB update pipelines. |
| Q17 Throughput | CONDITIONAL | delivery architecture strong; exact subscribed feed throughput not public. |
| Q18 Failure Risk | MEDIUM | capability is strong, but several hard governance fields require schema-level confirmation. |
| Q19 Coverage Reporting | PASS | structured global feed + deterministic entity model supports explicit population coverage computation. |
| Q20 Refresh | PASS | DataFeed update sequencing and loader operation support repeated refreshes. |

### 11.3 EODHD Fundamentals + Bulk Fundamentals API

| Gate | Result | Qualification basis |
|---|---|---|
| Q1 Batch / Bulk | PASS | dedicated bulk fundamentals endpoint with pagination/list/exchange scope. |
| Q2 Population Scale | PASS | any-exchange bulk path, 500 symbols/page and documented global exchange universe. |
| Q3 Reproducibility | PASS | versioned REST endpoints and deterministic exchange/symbol parameters. |
| Q4 Historical Periods | PASS | major U.S. from 1985, non-U.S. generally from 2000; yearly/quarterly statements. |
| Q5 Metric Semantics | PASS | documented Fundamentals sections and field glossary; financial statements and ratios are structured. |
| Q6 Period Semantics | PASS | yearly and quarterly statement sections with period dates; filing dates available. |
| Q7 Currency | PASS | statement `currency_symbol`, security `CurrencyCode` and exchange currency documented. |
| Q8 Identity | PASS | ISIN, CUSIP, CIK, PrimaryTicker, Exchange plus OperatingMIC from exchange API. |
| Q9 Timing | PASS | each yearly/quarterly report entry carries `date` and `filing_date`; sufficient for prospective current-screening timing governance. |
| Q10 Provenance | CONDITIONAL | provider-level lineage/retrieval provenance is governable; original filing/source lineage is not as strong/public as institutional providers. |
| Q11 Missingness | CONDITIONAL | docs state fields may be empty, but empty vs not-applicable/not-covered semantics require canonical normalization rules. |
| Q12 Sector | CONDITIONAL | global stock coverage is broad; explicit specialized bank/insurance/REIT financial-statement templates are not as strongly evidenced. |
| Q13 Restatements | WEAK | no strong public vintage/restatement lineage for general fundamentals established. |
| Q14 Corporate Actions | CONDITIONAL | splits/dividends and stable identifiers exist elsewhere in platform; exact fundamental-series revision handling is not fully documented. |
| Q15 Licensing | CONDITIONAL | personal storage/analysis rights and commercial-plan distinction documented; Extended Fundamentals exact terms/cost require plan confirmation before acquisition. |
| Q16 Automation | PASS | REST, bulk, pagination, structured JSON/CSV and documented local-sync use. |
| Q17 Throughput | PASS | 100k calls/day, 1000 requests/minute plus bulk call costs are documented. |
| Q18 Failure Risk | MEDIUM | technically clean path, but weaker PIT/restatement/sector semantics than LSEG. |
| Q19 Coverage Reporting | PASS | structured responses, symbol lists, missing fields and stable identity support deterministic coverage calculation. |
| Q20 Refresh | PASS | bulk sync, hourly snapshots for supported exchanges and repeatable API refresh are explicit. |

---

## 12. Company / Security Mapping

### LSEG

- Company Identity: **PASS**
- Security Mapping: **PASS**
- Evidence: LSEG permanent identifiers plus CUSIP, SEDOL, ISIN, RIC, MIC, LEI and equity concordance data.
- Architecture fit: company fundamentals can remain keyed to `Company_Key`; security-level valuation inputs can join through governed Security Master mappings.

### FactSet

- Company Identity: **PASS**
- Security Mapping: **PASS**
- Evidence: entity-centric symbology, FactSet Entity ID and security/listing identifier relationships including ISIN and primary listing references.
- Architecture fit: strong company/entity separation; exact join tables must be frozen in acquisition design.

### EODHD

- Company Identity: **PASS**
- Security Mapping: **PASS**
- Evidence: ISIN, CUSIP, CIK, PrimaryTicker, Exchange; exchange list includes OperatingMIC.
- Architecture fit: deterministic mapping is feasible, but provider ticker must never become canonical identity.

## 13. Multi-Listing / Share-Class Assessment

### QUALIFICATION JUDGMENT

- **LSEG:** PASS. Broad symbology/reference architecture, instrument classes and concordance support multi-listing/share-class mapping. Preference shares are explicitly present in dataset coverage and are not blanket-excluded.
- **FactSet:** PASS. Entity-centric symbology separates entity/security/listing levels; primary exchange and ISIN references are supported.
- **EODHD:** CONDITIONAL. `PrimaryTicker`, exchange and ISIN support are strong, but share-class semantics are less richly documented than LSEG/FactSet; canonical project Security Master must resolve classes explicitly.

No candidate is allowed to collapse preferred/special shares, ADR/GDRs or secondary listings into one company row without Security Master mapping.

## 14. Historical Depth

| Candidate | Documented Historical Depth | Adequacy |
|---|---|---|
| LSEG | Worldscope ~1983; non-U.S. as-reported from 1996; LSEG Financials ~1980; full-depth DaaS history | Strong for current screening, multi-year quality/value/growth, capital efficiency and long research |
| FactSet | annual from 1980; semiannual from 1994; quarterly from 1995 per official 2019 coverage snapshot | Strong, but coverage statistics are stale and should be refreshed in later commercial/design validation |
| EODHD | major U.S. from 1985; non-U.S. generally from 2000; minor companies may have only six years; bulk records only last 4 years/4 quarters | Adequate overall when deeper per-symbol API history is used; bulk-only history is insufficient for some long-history models |

## 15. Period Semantics

- LSEG: **PASS** — annual/interim, standardized/as-reported and PIT datasets; exact fiscal field names reside in data dictionary.
- FactSet: **PASS** — annual, semiannual/interim and quarterly are explicit.
- EODHD: **PASS** — yearly and quarterly statement structures, report dates and filing dates are documented.

TTM need not be a source-provided primitive where internally derivable from governed compatible quarters.

## 16. Point-in-Time / Look-Ahead

### LSEG

- Point-in-Time Capability: **STRONG**
- Historical Backtest Look-Ahead Risk: **LOW** when PIT product/fields are used correctly
- Current-Screening Timing Governance: **PASS**

LSEG explicitly preserves preliminary, final and restated values and timestamps the moment data became available.

### FactSet

- Point-in-Time Capability: **CONDITIONAL**
- Historical Backtest Look-Ahead Risk: **MEDIUM**
- Current-Screening Timing Governance: **CONDITIONAL**

FactSet documents same-day collection and has separate point-in-time products, but the public evidence used here does not prove that the specific Fundamentals DataFeed carries a complete historical-vintage availability model. The exact feed schema must be validated before historical backtests.

### EODHD

- Point-in-Time Capability: **CONDITIONAL**
- Historical Backtest Look-Ahead Risk: **MEDIUM/HIGH** for latest-restated historical datasets
- Current-Screening Timing Governance: **PASS**

Statement records carry `filing_date`, making prospective current research governable. True vintage history/restatement lineage was not established for the general Fundamentals API.

## 17. Restatement Handling

- LSEG: **STRONG** — amendments/restatements in as-reported data and preliminary/final/restated PIT history.
- FactSet: **CONDITIONAL** — collection/update architecture is strong, but exact historical revision/vintage fields in Fundamentals DataFeed need schema confirmation.
- EODHD: **WEAK** — public documentation validated current structured statements and filing dates but not robust historical vintage/restatement lineage.

## 18. Provenance

- LSEG: **PASS** — source-aligned as-reported content, common data model, dictionaries/glossaries, provider identifiers and original-document linkage capability.
- FactSet: **CONDITIONAL** — primary-document sourcing is explicit, but exact per-observation source/revision fields in the DataFeed need confirmation.
- EODHD: **CONDITIONAL** — provider-level source, endpoint/version, retrieval as-of, field/period and identifiers can be recorded; original filing-level provenance is weaker.

## 19. Metric Semantics

### LSEG

**PASS.** Standardized and as-reported data are explicitly separated. Financial Concept Codes, standardized/as-reported glossaries and item lists are documented.

### FactSet

**PASS.** Standardized methods and 750+ data items are documented. Four industry profiles provide sector-appropriate statement templates.

### EODHD

**PASS with lower semantic depth.** The documentation exposes structured financial-statement fields and glossaries. Internal normalization must retain provider metric names and must not assume equivalence to LSEG/FactSet standardized concepts.

## 20. Metric-Family Coverage

| Metric family | LSEG | FactSet | EODHD |
|---|---|---|---|
| Income Statement | SUPPORTED | SUPPORTED | SUPPORTED |
| Balance Sheet | SUPPORTED | SUPPORTED | SUPPORTED |
| Cash Flow | SUPPORTED | SUPPORTED | SUPPORTED |
| Profitability Inputs | SUPPORTED | SUPPORTED | SUPPORTED |
| Growth Inputs | SUPPORTED | SUPPORTED | SUPPORTED |
| Capital Efficiency Inputs | SUPPORTED | SUPPORTED | SUPPORTED |
| Leverage Inputs | SUPPORTED | SUPPORTED | SUPPORTED |
| Valuation Inputs | SUPPORTED | SUPPORTED | SUPPORTED/PARTIAL depending market-data join |
| Shareholder Return Inputs | SUPPORTED | SUPPORTED | SUPPORTED |
| Per-Share Inputs | SUPPORTED | SUPPORTED | SUPPORTED |

Derived metrics remain internal/versioned where source inputs are sufficient.

## 21. Currency

### LSEG

- Original Reporting Currency: **SUPPORTED conceptually; exact field contract to pin**
- Currency Metadata: **CONDITIONAL**
- Provider-Currency Conversion: **UNKNOWN / product-dependent**

### FactSet

- Original Reporting Currency: **PARTIAL in public evidence**
- Currency Metadata: **CONDITIONAL**
- Provider-Currency Conversion: **UNKNOWN**

### EODHD

- Original Reporting Currency: **SUPPORTED through statement `currency_symbol`**
- Currency Metadata: **PASS**
- Provider-Currency Conversion: **UNKNOWN / not required for qualification**

Internal normalization must preserve original currency and any later FX transformation lineage.

## 22. Missing-Data Governance

- LSEG: **CONDITIONAL** — structured schemas and dictionaries are strong; exact canonical handling of missing vs not-applicable must be frozen from field metadata.
- FactSet: **CONDITIONAL** — requires exact feed-schema semantics.
- EODHD: **CONDITIONAL** — empty fields are documented; architecture must distinguish empty/unreported from model-level `NOT_APPLICABLE`.

None of the sources is allowed to convert missing values to zero.

## 23. Sector Breadth

- LSEG: **PASS** — broad industry coverage, standardized/as-reported financials, REIT property data and industry operating metrics.
- FactSet: **PASS** — Commercial, Bank, Insurance and Other Financial templates; explicit REIT/bank industry metrics.
- EODHD: **CONDITIONAL** — broad global stock coverage is credible, but public documentation is weaker on specialized financial-sector statement semantics.

Source coverage is distinct from model applicability.

## 24. Market-Data Boundary

### ARCHITECTURE REQUIREMENT APPLIED

For P/E, P/B, P/FCF, Dividend Yield, Market Cap and EV:

- all three providers may expose some values directly;
- source accounting inputs must remain distinguishable from security-price inputs;
- the Fundamentals Research Layer must not treat price-linked values as pure company accounting facts;
- separate market-data inputs may be used where preferable, with Security_Key, price source, currency and as-of retained.

A separate market-data dependency is not a qualification failure.

## 25. Bulk Mechanism

| Candidate | Bulk Mechanism | Population Request Model | Batch Capability |
|---|---|---|---|
| LSEG | DaaS SQL database + bulk file feed + File Retrieval API | initialization files + incremental updates / database tables | PASS |
| FactSet | Fundamentals DataFeed + DataFeed Loader | subscription bundles/files loaded into local DB | PASS |
| EODHD | REST Bulk Fundamentals + paginated exchange/list retrieval; six-exchange snapshot endpoint | up to 500 symbols/page or exchange-wide; deeper history also available via deterministic single-symbol Fundamentals API | PASS |

## 26. Scale / Throughput

### LSEG

- 600-Scale: **SUPPORTED**
- 2527-Scale: **SUPPORTED**
- Throughput: enterprise bulk-feed cadence documented; exact customer throughput **CONDITIONAL/contract-specific**.

### FactSet

- 600-Scale: **SUPPORTED**
- 2527-Scale: **SUPPORTED**
- Throughput: DataFeed delivery model supports population-scale loads; exact subscribed limits **CONDITIONAL**.

### EODHD

- 600-Scale: **SUPPORTED**
- 2527-Scale: **SUPPORTED**
- Throughput: **PASS** for documented mechanics — 500 symbols per bulk page, 1000 requests/minute, 100,000 call units/day on paid plans; bulk call costs explicitly documented.

No live throughput test was performed.

## 27. Refresh / Automation

| Candidate | Full Refresh | Incremental/Recurring Refresh | Restatement Refresh | Automation | Operational Burden |
|---|---|---|---|---|---|
| LSEG | PASS | PASS | PASS/strong PIT support | PASS | MEDIUM |
| FactSet | PASS | PASS | CONDITIONAL | PASS | MEDIUM |
| EODHD | PASS | PASS | CONDITIONAL/WEAK vintage lineage | PASS | LOW/MEDIUM |

LSEG is preferred because its bulk initialization/incremental model and PIT fundamentals jointly reduce custom recovery logic.

## 28. Licensing / Usage

### LSEG

- Automated Access Allowed: **YES subject to subscription/entitlement**
- Local Storage Allowed: **CONDITIONAL to subscribed bulk/database license**
- Derived Metrics Allowed: **CONDITIONAL to contract**
- Internal Research Use: **YES/CONDITIONAL to contract**
- Redistribution Restrictions: **PARTIAL / contract-dependent**
- Commercial Plan Required: **YES**
- Licensing / Usage Governance: **CONDITIONAL**

### FactSet

- Automated Access Allowed: **YES through DataFeed subscription**
- Local Storage Allowed: **YES/CONDITIONAL** because DataFeed Loader explicitly loads local databases, subject to contract
- Derived Metrics Allowed: **CONDITIONAL**
- Internal Research Use: **YES/CONDITIONAL**
- Redistribution Restrictions: **PARTIAL / contract-dependent**
- Commercial Plan Required: **YES**
- Licensing / Usage Governance: **CONDITIONAL**

### EODHD

- Automated Access Allowed: **YES under subscribed API plan**
- Local Storage Allowed: **YES for documented personal/non-professional use; commercial use requires commercial arrangement**
- Derived Metrics Allowed: **CONDITIONAL** to use class/plan terms
- Internal Research Use: **YES for private non-commercial use; commercial arrangement otherwise**
- Redistribution Restrictions: **KNOWN — redistribution/resale/access sharing restricted in standard terms**
- Commercial Plan Required: **depends on user/use classification**
- Extended Fundamentals bulk entitlement required: **YES**
- Licensing / Usage Governance: **CONDITIONAL**

No acquisition may occur until the preferred-path design gate records the exact applicable entitlement and storage terms.

## 29. Cost / Practicality

### LSEG

- Public exact price: not available in validated public material.
- Commercial Transparency: LOW
- Likely Cost Burden: HIGH
- Implementation Burden: MEDIUM
- Operating Burden: MEDIUM

### FactSet

- Public exact Fundamentals DataFeed price: not available in validated public material.
- Commercial Transparency: LOW
- Likely Cost Burden: HIGH
- Implementation Burden: MEDIUM
- Operating Burden: MEDIUM

### EODHD

- Public Fundamentals Data Feed price: **USD 59.99/month ≈ EUR 51.74/month** at USD/EUR 0.86254 on 2026-09-11.
- Extended Fundamentals bulk entitlement price: UNKNOWN / provided on request.
- Commercial Transparency: MEDIUM
- Likely Cost Burden: MEDIUM until Extended Fundamentals cost is known
- Implementation Burden: LOW/MEDIUM
- Operating Burden: LOW/MEDIUM

Pricing does not drive qualification.

## 30. Provider Lock-In

### LSEG

**Provider Lock-In Risk: MEDIUM.** Rich proprietary concepts and IDs exist, but the project can retain independent `Company_Key`, `Security_Key`, canonical normalized metrics and provenance. Multiple standard identifiers reduce identity lock-in.

### FactSet

**Provider Lock-In Risk: MEDIUM.** FactSet Entity IDs/symbology are powerful but proprietary. The internal canonical identity layer must remain authoritative.

### EODHD

**Provider Lock-In Risk: LOW/MEDIUM.** Mapping can rely heavily on ISIN/MIC/ticker/CIK and provider-independent identifiers; metric names remain provider-specific and must be normalized behind the canonical layer.

## 31. Architecture Direction

### QUALIFICATION JUDGMENT

**Architecture Direction: GLOBAL_SINGLE_SOURCE**

The qualification evidence still supports the discovery-stage preference for one reusable global primary source rather than a regional patchwork.

LSEG is the preferred technical path because one source family can supply global standardized/as-reported fundamentals, explicit PIT history, broad sector templates, symbology and bulk refresh. EODHD remains a qualified runner-up with simpler implementation and transparent API mechanics but weaker PIT/restatement/semantic depth. FactSet remains a high-quality conditional path pending exact DataFeed governance-field validation.

No multi-source architecture is authorized by this result.

## 32. Qualification Matrix

| Candidate | Q1 Bulk | Q2 Scale | Q3 Repro | Q4 History | Q5 Semantics | Q6 Period | Q7 Currency | Q8 Identity | Q9 Timing | Q10 Provenance | Q11 Missingness | Q12 Sector | Q13 Restatements | Q14 Corp Actions | Q15 Licensing | Q16 Automation | Q17 Throughput | Q18 Failure Risk | Q19 Coverage Reporting | Q20 Refresh | 600 Scale | 2527 Scale | Final Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LSEG / Worldscope | PASS | PASS | PASS | PASS | PASS | PASS | CONDITIONAL | PASS | PASS | PASS | CONDITIONAL | PASS | PASS | CONDITIONAL | CONDITIONAL | PASS | CONDITIONAL | LOW | PASS | PASS | SUPPORTED | SUPPORTED | QUALIFIED_BULK_SOURCE |
| FactSet Fundamentals DataFeed | PASS | PASS | PASS | PASS | PASS | PASS | CONDITIONAL | PASS | CONDITIONAL | CONDITIONAL | CONDITIONAL | PASS | CONDITIONAL | CONDITIONAL | CONDITIONAL | PASS | CONDITIONAL | MEDIUM | PASS | PASS | SUPPORTED | SUPPORTED | CONDITIONALLY_QUALIFIED |
| EODHD Fundamentals + Bulk | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL | PASS | PASS | MEDIUM | PASS | PASS | SUPPORTED | SUPPORTED | QUALIFIED_BULK_SOURCE |

## 33. Comparative Strengths / Weaknesses

### LSEG / Worldscope

**Strongest demonstrated capabilities**

- most complete PIT/anti-look-ahead evidence;
- global standardized plus as-reported statements;
- deep history;
- strong identifiers/symbology;
- explicit REIT and industry content;
- full bulk initialization plus incremental updates;
- rich data dictionary/glossary architecture.

**Material weaknesses / conditions**

- commercial terms and exact entitlement rights not public;
- large enterprise dataset and operational footprint;
- exact missingness/currency field semantics require subscribed schema capture.

### FactSet

**Strongest demonstrated capabilities**

- deep global history;
- standardized financial statements;
- dedicated bank/insurance/other-financial templates;
- deterministic DataFeed Loader architecture;
- strong entity/security symbology.

**Material weaknesses / conditions**

- strongest public Fundamentals coverage numbers are explicitly 2019-era;
- exact Fundamentals feed PIT/publication-date fields are not sufficiently evidenced;
- missingness, reporting-currency and revision/provenance fields require feed-schema validation.

### EODHD

**Strongest demonstrated capabilities**

- explicit current bulk API mechanics;
- documented global exchange support and MICs;
- ISIN/CUSIP/CIK/PrimaryTicker identity;
- yearly/quarterly statements with `filing_date`;
- transparent rate limits;
- low implementation complexity;
- feasible 600 and 2527 automation path.

**Material weaknesses / conditions**

- bulk record history is only four years/four quarters; deeper history requires ordinary Fundamentals API requests;
- weaker true PIT/vintage history and restatement lineage;
- weaker explicit financial-sector specialized semantics;
- original-source provenance less rich;
- Extended Fundamentals pricing/terms are not public.

## 34. Candidate Classifications

### LSEG Company Fundamentals / Worldscope

**QUALIFIED_BULK_SOURCE**

Hard capabilities are sufficiently established. The remaining conditional items are bounded entitlement/schema details that can be frozen in the acquisition/mapping design gate without needing data acquisition.

### FactSet Fundamentals DataFeed

**CONDITIONALLY_QUALIFIED**

Blocking conditions are confined to the exact subscribed Fundamentals DataFeed schema for timing, reporting currency, missingness and revision/provenance semantics. The underlying bulk/history/semantic/sector architecture is strong.

### EODHD Fundamentals + Bulk Fundamentals API

**QUALIFIED_BULK_SOURCE**

The source satisfies the hard practical bulk contract for current/prospective research at both required scales. Historical backtests must not assume true vintage values. The later design must preserve this limitation.

Classification counts:

- `QUALIFIED_BULK_SOURCE`: **2**
- `CONDITIONALLY_QUALIFIED`: **1**
- `NOT_QUALIFIED`: **0**
- `UNKNOWN_NOT_TESTED`: **0**

## 35. QUALIFICATION RESULT

### FACT

At least one candidate meets the hard qualification contract strongly enough for the next governed design stage.

### QUALIFICATION JUDGMENT

**QUALIFICATION RESULT: A — QUALIFIED BULK SOURCE PATH EXISTS**

600-Scale Qualified Candidate: **YES**

2527-Scale Qualified Candidate: **YES**

The existence of a qualified source path does not authorize acquisition, procurement, integration, Guru restart or any Universe change.

## 36. Preferred Qualified / Conditional Path

### Preferred Qualified Path

**LSEG Company Fundamentals / Worldscope**

**Classification: QUALIFIED_BULK_SOURCE**

Reason: strongest total architecture fit across global scale, history, standardized/as-reported semantics, PIT/timing, entity/security mapping, sector breadth, provenance, restatement handling and repeated bulk refresh. Its higher likely cost/complexity does not override capability qualification.

### Qualified Runner-Up

**EODHD Fundamentals + Bulk Fundamentals API**

Reason: strong structured/bulk mechanics, current global coverage, identity and filing-date support with materially lower implementation burden. It ranks behind LSEG due weaker vintage PIT, restatement and specialized semantic depth.

### Conditional Path

FactSet remains `CONDITIONALLY_QUALIFIED` but is not authorized as a parallel next path.

**Conditional Preferred Path: NONE** because result A exists and one qualified preferred path is selected.

**Blocking Conditions: NONE for preferred qualified path.** Design-stage conditions remain entitlement/schema details, not qualification blockers.

## 37. Exact Next Authorized Stage

Because `QUALIFICATION RESULT = A — QUALIFIED BULK SOURCE PATH EXISTS`, authorize exactly:

**NEXT AUTHORIZED STAGE: Fundamentals Bulk Acquisition & Mapping Design Gate — READ-ONLY / SPEC ONLY — PREFERRED QUALIFIED PATH ONLY — NO DATA ACQUISITION**

Preferred qualified path for that stage:

**LSEG Company Fundamentals / Worldscope**

The next stage may design only:

- acquisition contract;
- Company/Security mapping contract;
- snapshot contract;
- normalization handoff contract;
- refresh contract;
- data-quality contract;
- entitlement/licensing pre-acquisition check;
- failure/recovery contract.

It may not acquire data, create provider accounts, execute feeds, integrate code, restart Guru or modify Universe membership.

## 38. Guru Boundary

### FACT

- `AUTHORIZED NEXT GURU STAGE: NONE`
- Guru Restart: NO
- New STOXX Europe 600 Ranking: NO
- New Guru Top 5: NO
- Legacy 25-stock ranking: LEGACY PILOT

Qualification success does not restart Guru.

## 39. Fundamentals Boundary

### FACT

- Fundamentals Acquired: NO
- Bulk Dataset Built: NO
- Provider Integrated: NO
- Company Mapping Built: NO
- Normalization Executed: NO
- Derived Metrics Calculated: NO
- Coverage Calculated: NO
- Ranking Executed: NO
- Live Fundamentals API Called: NO
- Trial Activated: NO
- Provider Account Created: NO
- API Key Requested/Used: NO
- Bulk Dataset Downloaded: NO

## 40. Universe Boundary

### FACT

Universe Expansion remains:

**PAUSED — NOT ABANDONED**

Baseline remains:

- Research Partial = 2527
- Strict = 759
- Frozen = 0

No population selection, reopening, membership write, Universe write or expansion execution occurred.

## 41. No-Touch Verification

This stage performed:

- External documentation research on locked candidates: YES
- New provider discovery: NO
- Substitute candidate research: NO
- Alpha Vantage research: NO
- Provider account creation/login: NO
- API key request/use: NO
- Trial activation: NO
- Live fundamentals endpoint call: NO
- Individual company fundamentals query: NO
- Bulk fundamentals download: NO
- Sample provider dataset acquisition: NO
- Scraping: NO
- Endpoint reverse-engineering: NO
- Acquisition script/code: NO
- Provider integration: NO
- Fundamentals table build: NO
- Company/Security mapping build: NO
- Bulk Fundamentals Snapshot build: NO
- Normalization execution: NO
- Derived metrics: NO
- Coverage calculation: NO
- Ranking: NO
- Guru restart: NO
- Universe write: NO
- Universe expansion resume: NO

Only `docs/spec/Fundamentals_Bulk_Source_Qualification_v2_Gate.md` is written by this stage.

### Final Gate State

- STAGE STATUS: PASS
- Candidates Evaluated: 3
- LSEG / Worldscope Classification: QUALIFIED_BULK_SOURCE
- FactSet Classification: CONDITIONALLY_QUALIFIED
- EODHD Classification: QUALIFIED_BULK_SOURCE
- QUALIFIED_BULK_SOURCE: 2
- CONDITIONALLY_QUALIFIED: 1
- NOT_QUALIFIED: 0
- UNKNOWN_NOT_TESTED: 0
- 600-Scale Qualified Candidate: YES
- 2527-Scale Qualified Candidate: YES
- Preferred Architecture Direction: GLOBAL_SINGLE_SOURCE
- Overall Failure-Loop Risk: LOW for preferred LSEG path; MEDIUM across the full candidate set
- QUALIFICATION RESULT: A — QUALIFIED BULK SOURCE PATH EXISTS
- Preferred Qualified Path: LSEG Company Fundamentals / Worldscope
- Qualified Runner-Up: EODHD Fundamentals + Bulk Fundamentals API
- Conditional Preferred Path: NONE
- Guru Restart Authorized: NO
- AUTHORIZED NEXT GURU STAGE: NONE
- Universe Write: NO
- NEXT AUTHORIZED STAGE: Fundamentals Bulk Acquisition & Mapping Design Gate — READ-ONLY / SPEC ONLY — PREFERRED QUALIFIED PATH ONLY — NO DATA ACQUISITION

HARD STOP after commit and post-commit verification.
