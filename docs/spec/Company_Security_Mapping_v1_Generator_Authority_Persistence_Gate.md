# Company/Security Mapping v1 — Generator-Authority Persistence Gate

## Canonical model

- Canonical source: `universe/research_partial_1633.csv`
- Source Git blob at start head: `f8e0d521023d26f1da9e75b4b817b861f686bb41`
- Canonical generator: `scripts/generate_company_security_mapping_v1.py`
- Canonical validator/test: `tests/test_company_security_mapping_v1.py`
- Canonical validation report: this file
- Materialized sidecar: **DERIVED / NON-CANONICAL** and intentionally not committed.

The exact sidecar is fully reproducible from the committed source plus deterministic generator. It contains no sidecar-only information.

## Deterministic generation

- Generated sidecar rows: 2527
- Generated raw bytes: 217498
- Generated SHA-256: `83206eafe780d0bedc757c08132fcf59df3789aeb8d66c879fdff75c1a3f786e`
- Second-run SHA-256: `83206eafe780d0bedc757c08132fcf59df3789aeb8d66c879fdff75c1a3f786e`
- Second-run SHA equality: YES
- Serialization: UTF-8, stable column order, LF newlines, no timestamps/random/environment-dependent values.

## Validated invariants

- Security_Key: 2527; unique: 2527; collisions: 0
- Source_WS_ID: 2527; unique: 2527
- Rows missing ISIN: 1536; all have Security_Key
- Missing-ISIN incorrectly IDENTITY_OK: 0
- Company_Key assigned: 0; NULL/empty: 2527
- IDENTITY_OK: 0
- COMPANY_UNRESOLVED: 991
- SECURITY_UNRESOLVED: 1536
- LISTING_UNRESOLVED: 0
- SHARE_CLASS_UNRESOLVED: 0
- IDENTITY_CONFLICT: 0
- Confidence HIGH/MEDIUM/LOW: 0/0/0
- Confidence UNRESOLVED: 2527
- Distinct security merge violations: 0
- Focused tests: PASS
- Source CSV modified by generation/tests: NO

## Universe state

- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Universe membership changed: NO
