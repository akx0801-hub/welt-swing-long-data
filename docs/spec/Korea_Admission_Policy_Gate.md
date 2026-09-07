# Korea Admission Policy Gate

## Stage decision

**KOREA ADMISSION POLICY GATE — PASS**

**Recommended population: KOSPI 200**

**BUILD READINESS: CONDITIONAL**

**NEXT AUTHORIZED STAGE: Korea Pre-Build Evidence Validation Gate — READ-ONLY / NO UNIVERSE WRITE**

Conditional means policy-complete but not build-authorized. A later validation gate must prove row-level membership, current listing and Security-Level identity access before any Korea build.

## 1. Start and authorization

- Repository: akx0801-hub/welt-swing-long-data
- Branch: main
- Start HEAD: c249a5d66a9af19939b91aa815b5f31ce6b305f3
- origin/main at startcheck: c249a5d66a9af19939b91aa815b5f31ce6b305f3
- Commit verified: Post-Canada next population manager gate
- Authorized stage: Korea Admission Policy Gate — READ-ONLY
- No completed Korea Admission Policy Gate existed at startcheck.

## 2. Governance and current coverage

| Measure | Verified value |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| US-1 | 372 |
| US-2 | 369 |
| US total | 741 |
| AU-1 | 153 |
| Canada | PARKED |
| Korea current coverage | 0 |
| Korea build | NOT AUTHORIZED |

Welt-Swing v7.2 remains the only productive Trading Authority. WELT-SWING LONG DEV remains DEV / RESEARCH / SHADOW. Membership, Eligibility, Scan and Execution are separate layers. No CUSIP, local code, ticker-only match, issuer-only match, silent MIC merge, silent class mapping or successor migration can satisfy identity. Alpha Vantage is prohibited.

## 3. Canada lessons applied

Canada demonstrated that a population snapshot or ticker/MIC lineage does not establish an admissible Security-Level identity. The Korea path must prove, before build:

1. current population membership;
2. current ACTIVE primary listing;
3. exact issuer and Security name;
4. exact Share Class;
5. Instrument Type;
6. reproducible ISIN;
7. Primary MIC;
8. Primary Ticker;
9. Corporate-Action status;
10. collision and legacy-overlap status.

Missing evidence is REVIEW, not admission. A central evidence failure blocks the build.

## 4. Korea market structure

KRX is the relevant official exchange authority. This policy separates the KOSPI stock market from KOSDAQ and does not use the generic label KRX as a substitute for a market-specific MIC.

- KOSPI: primary market for this first Korea path.
- KOSDAQ: OUT OF SCOPE for this first path.
- KONEX: context only and OUT OF SCOPE.

The current official KRX Data Marketplace landing page is https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en. The Korea Securities Depository authority is https://www.ksd.or.kr/.

## 5. Population options evaluated

| Option | Assessment | Decision |
|---|---|---|
| KOSPI 200 | bounded large-cap population; strategic relevance; manageable policy scope; official KRX route identified | SELECTED |
| KOSPI 100 | potentially manageable but no superior currently validated row-level source path | NOT SELECTED |
| broader KOSPI large-cap family | broader but materially increases evidence, class and identity surface | NOT SELECTED |
| KOSDAQ / KOSDAQ 150 | different market structure and higher complexity; outside first path | NOT SELECTED |
| KONEX | unsuitable for first developed-market path | NOT SELECTED |

Exactly one primary population is selected: KOSPI 200.

## 6. Final population policy

- Primary Population: KOSPI 200
- Population type: current index membership, not a free-form issuer list
- Primary Market: KOSPI stock market
- Primary Exchange Scope: Korea Exchange KOSPI primary listings
- KOSDAQ: OUT OF SCOPE
- KONEX: OUT OF SCOPE
- Expected scope: approximately 200 index constituents, subject to the later current snapshot and deduplication; no artificial final row count is imposed.

## 7. Source hierarchy and source manifest

| Source | Authority | Rank | Population | Listing | Security / class | ISIN | Currentness / reproducibility | Limitation |
|---|---|---:|---|---|---|---|---|---|
| KRX Data Marketplace | Korea Exchange | R1 | YES, intended | YES, intended | PARTIAL until row-level export is validated | PARTIAL | official route identified; technical validation pending | prior repository probes returned HTTP 403/400 and zero parsed rows |
| KSD | Korea Securities Depository | R1 | NO as index membership | supporting | potential identifier/security support | potential identifier support | official authority; row-level access not validated in this gate | no build extraction performed |
| ISO 10383 MIC dataset | ISO / SWIFT RA | R1 | NO | MIC reference | NO | NO | current official MIC list is published and reproducible | does not prove security identity |
| Issuer IR / annual reports / filings | issuer or regulator | R1 | NO, supporting only | supporting | YES for named security/class where explicit | possible | document-level and case-specific | not a population source |
| Named institutional index/security data | institution | R2 | controlled fallback only | supporting | possible | possible | allowed only with snapshot and coverage disclosure | cannot silently replace R1 |
| Strong secondary sources | third party | R3 | NO | supporting only | supporting only | supporting only | cross-check only | never sufficient alone |
| Search engines / generic finance sites | discovery | R4 | NO | NO | NO | NO | discovery only | never admission evidence |

Alpha Vantage is prohibited.

## 8. KRX access feasibility

Repository evidence records the official KRX landing page as HTTP 200 but the row-level endpoint path as technically blocked or invalid in prior probes: one endpoint returned HTTP 403 and a later official endpoint retry returned HTTP 400 with zero parsed rows. Historical context also records login-gated or LOGOUT behavior for the public KOSPI 200 export.

Accordingly:

| Feasibility area | Status | Reason |
|---|---|---|
| KRX Population Access | CONDITIONAL | official route exists, but current row-level export is not yet reproducibly validated |
| KRX Listing Access | CONDITIONAL | official KRX route exists, but current security-level listing retrieval is not yet validated |
| KRX Security-Level Identity Access | CONDITIONAL | KRX/KSD/issuer paths are plausible, but exact row-level fields have not been proven in this gate |
| ISIN Source Feasibility | CONDITIONAL | official KSD/issuer/institutional paths are plausible; exact reproducible access remains to be tested |

No download, session experiment, authenticated request, constituent extraction or candidate generation was performed in this policy gate.

## 9. MIC and ticker policy

Primary MIC is ISO 10383 XKRX, the operating MIC for the Korea Exchange stock market. KOSDAQ is represented separately by the segment MIC XKOS and is out of scope here. No generic KRX value may be used as a substitute for the market-specific primary-MIC field.

Primary Ticker is the official six-digit, zero-padded KRX security code for the listed Security. The local code is a listing identifier and canonical ticker field, not identity by itself. Provider symbols, English abbreviations and issuer names cannot replace the official code.

Canonical identity is:

ISIN + Primary_MIC + Primary_Ticker + exact Security Name + exact Share Class

Canonical WS_ID may be generated only in a later build after the MIC and ticker are verified, using the repository format WS:XKRX:<six-digit-code> if that existing format is confirmed by the build validator. No WS_ID is generated in this gate.

The ISO MIC authority publishes the current MIC dataset at https://www.iso20022.org/market-identifier-codes.

## 10. ISIN policy

An admitted Security requires an ISIN from a reproducible Security-Level source. The later build must record the source, access date, document or endpoint reference, format validation, check digit/Luhn result, exact Security match, exact Share-Class match, ticker match, MIC match and currentness.

Not allowed:

- generated ISIN;
- assumed KR prefix;
- ticker-derived ISIN;
- issuer-level ISIN;
- CUSIP or Korean local code as an ISIN replacement;
- ISIN of another class, listing or depositary receipt.

CUSIP, local code, FIGI or other identifiers may be discovery or cross-check fields only.

## 11. Share-Class policy

| Share class | Policy |
|---|---|
| Common / Ordinary | ADMITTABLE if every hard gate passes |
| Preferred | REVIEW; never silently classify as Common |
| Multiple voting / different class | separate Security; REVIEW unless exact class evidence passes and the policy permits it |
| Treasury / non-listed | EXCLUDE |
| Other / unresolved | REVIEW |

Every listed class is a separate candidate. Separate class evidence, separate ISIN and separate Primary Ticker are required. No issuer-level merge is permitted.

## 12. Instrument policy

| Instrument Type | Policy |
|---|---|
| COMMON_OR_ORDINARY | ADMITTABLE subject to all hard gates |
| PREFERRED | REVIEW |
| REIT | REVIEW |
| TRUST | REVIEW |
| UNIT | REVIEW |
| SPAC | REVIEW pending explicit instrument evidence |
| ETF | EXCLUDE |
| ETN | EXCLUDE |
| FUND | EXCLUDE |
| DEPOSITARY_RECEIPT | EXCLUDE |
| FOREIGN_SECONDARY_LISTING | EXCLUDE |
| STRUCTURED_PRODUCT | EXCLUDE |
| WARRANT | EXCLUDE |
| RIGHT | EXCLUDE |
| OTHER | REVIEW |
| UNRESOLVED | REVIEW |

REVIEW is not admission. Eligibility is not decided in this gate.

## 13. Foreign and secondary listings

Korean issuer with Korea primary listing may be eligible. Foreign issuer with a Korea secondary listing is EXCLUDE under this first path. Dual-listed issuers require evidence that Korea is the primary market for the admitted Security. ADR/GDR and other depositary structures are EXCLUDE. No foreign primary listing may be silently mapped to a Korean secondary listing.

## 14. Current listing and corporate actions

Only ACTIVE current listings can be admitted. The later build must classify ACTIVE, SUSPENDED, DELISTED, MERGED, ACQUIRED, SUCCESSOR, RENAME, TICKER_CHANGE, CLASS_CHANGE and UNKNOWN.

- ACTIVE: may proceed if all other gates pass.
- SUSPENDED or UNKNOWN: REVIEW.
- DELISTED, obsolete, merged or acquired without a current successor evaluation: EXCLUDE or REVIEW as evidence dictates.
- Any rename, code change, class conversion, merger, acquisition, spin-off, relisting, delisting, preferred/common conversion or code reuse: security-level re-evaluation required.
- No automatic successor migration.

## 15. Collision and overlap policy

Against Research Partial 2527, classify exactly one of:

- EXACT_IDENTITY_DUPLICATE;
- ISIN_DUPLICATE;
- MIC_TICKER_DUPLICATE;
- TICKER_ONLY_CROSS_MIC;
- TRUE_IDENTITY_CONFLICT;
- NO_COLLISION.

EXACT_IDENTITY_DUPLICATE is not a new admission. TRUE_IDENTITY_CONFLICT is REVIEW and fail-closed. TICKER_ONLY_CROSS_MIC is documented but is not automatically an identity conflict.

Because Korea coverage is currently zero, future builds must still test foreign listings, ADR/GDRs, code collisions and any ISIN overlap. A Korea issuer outside a Korean primary listing is not automatically a Korea admission.

## 16. Admission model

Every later candidate receives exactly one final status:

- ADMIT
- REVIEW
- EXCLUDE

Optional detail such as INSTRUMENT_REVIEW is a reason or subtype under REVIEW, not a fourth final status.

## 17. Admission hard gates

ADMIT only if all are PASS:

1. current KOSPI 200 membership is reproducibly verified;
2. current listing is ACTIVE;
3. Korea is the primary listing market;
4. Primary MIC is XKRX;
5. official six-digit Primary Ticker is verified;
6. exact issuer, Security Name and Share Class are verified;
7. Instrument Type is COMMON_OR_ORDINARY;
8. reproducible exact ISIN exists;
9. ISIN format and check digit/Luhn pass;
10. ISIN semantically matches the exact Security and class;
11. Primary MIC and ticker match the evidence;
12. no unresolved Corporate Action exists;
13. no TRUE_IDENTITY_CONFLICT exists;
14. no prohibited instrument or secondary-only listing exists;
15. source references are reproducible and current enough for the build.

Failure of any gate means REVIEW or EXCLUDE according to the evidence; never ADMIT.

## 18. Review and exclude rules

REVIEW for missing or conflicting membership, current listing, ISIN, exact class, instrument type, primary-market status, corporate action, multiple-class identity, suspension, identifier semantics, or collision evidence. Preferred, REIT, Trust and Unit are REVIEW under this first policy.

EXCLUDE on reliable evidence for ETF, ETN, Fund, Depositary Receipt, foreign secondary listing, structured product, warrant, right, obsolete/delisted security, non-primary Korean listing, exact duplicate not new, or another policy-prohibited instrument. Missing evidence alone is REVIEW.

## 19. Pre-build feasibility matrix

| Area | Result | Gate interpretation |
|---|---|---|
| Population Source Feasibility | CONDITIONAL | concrete official KRX route exists; row-level reproducibility pending |
| Current Listing Feasibility | CONDITIONAL | official KRX route identified; current Security-Level listing proof pending |
| Security Identity Feasibility | CONDITIONAL | KRX/KSD/issuer routes plausible; exact row-level fields pending |
| ISIN Feasibility | CONDITIONAL | official/institutional paths plausible; exact reproducible access pending |
| Share-Class Feasibility | CONDITIONAL | class distinctions are definable; systematic extraction pending |
| Instrument-Type Feasibility | CONDITIONAL | policy is explicit; source field validation pending |
| Corporate-Action Feasibility | CONDITIONAL | official notices and issuer/regulatory sources are available in principle |
| Collision QA Feasibility | PASS | deterministic comparison rules are defined; no Korea candidates are created here |

Because the central source and identity paths are CONDITIONAL, the build is not READY. The correct status is CONDITIONAL, with a separate validation gate before build.

## 20. Canada-failure-mode assessment

Canada-Failure-Mode Risk: MEDIUM/HIGH.

Korea is materially different in market architecture because KRX and KSD provide identifiable official authorities, the Korean local code is a defined exchange identifier, and the KOSPI 200 is a bounded official population candidate. However, that difference is not yet operationally proven: prior repository tests returned 403/400 and zero rows, and no current row-level ISIN/class export has been validated. Therefore Korea must not proceed directly to build. The required qualitative difference is not merely a better search; it is a successfully validated official row-level data path with current membership plus exact Security/Class/ISIN fields.

## 21. Build authorization

Policy status: PASS.

Build readiness: CONDITIONAL.

Not authorized by this report:

- Korea build;
- candidate generation;
- constituent download or extraction;
- admission;
- Universe or Research Partial write;
- Mapping, History, Liquidity, Eligibility, Scan or U3K work;
- Canada reactivation;
- productive v7.2 changes.

## 22. Exact next stage

**Korea Pre-Build Evidence Validation Gate — READ-ONLY / NO UNIVERSE WRITE**

The next gate may validate the one selected KOSPI 200 source path and its row-level fields. It may not create a candidate population, persist a constituent file, admit Securities or write the Universe. If validation fails, Korea becomes blocked and no open-ended search loop is authorized.

## 23. Quality gates

- G0 Correct origin/main HEAD — PASS
- G1 Correct Korea Policy stage — PASS
- G2 Korea coverage 0 verified — PASS
- G3 Canada PARKED retained — PASS
- G4 Population options evaluated — PASS
- G5 KRX access feasibility evaluated — PASS
- G6 Population source hierarchy defined — PASS
- G7 Listing source hierarchy defined — PASS
- G8 Security identity policy defined — PASS
- G9 ISIN policy defined — PASS
- G10 Share-Class policy defined — PASS
- G11 Instrument policy defined — PASS
- G12 Corporate-action policy defined — PASS
- G13 Collision policy defined — PASS
- G14 Canada-failure-mode risk evaluated — PASS
- G15 Exactly one Korea population decision — PASS
- G16 No Universe/Data write — PASS
- G17 No Build/candidate generation — PASS

## 24. No-touch confirmation

No Korea candidate files, discovery files, security-master extracts or admission sidecars were created. No download, build, candidate generation, membership write, Universe/Data Master change, Research Partial change, Strict change, Frozen change, Mapping, History, Liquidity, Eligibility, Scan/U3K action, Canada change or v7.2 change was performed.

Research Partial remains 2527. Strict remains 759. Frozen remains 0. Canada remains PARKED. Korea remains at 0 current coverage.

**KOREA ADMISSION POLICY GATE — PASS**

**BUILD READINESS: CONDITIONAL**

**NEXT AUTHORIZED STAGE: Korea Pre-Build Evidence Validation Gate — READ-ONLY / NO UNIVERSE WRITE**