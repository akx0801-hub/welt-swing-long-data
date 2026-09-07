# Korea Pre-Build Evidence Validation — Source Manifest

- Stage: Korea Pre-Build Evidence Validation Gate
- Start HEAD: f32e0d00f507380069636adf37304f9c647fcf3a
- Validation sample: 12 fixed rows; no full KOSPI-200 candidate population created.
- Selection reference: `universe/source_snapshots_v0.3/KR_KOSPI200.csv`, 200 rows, snapshot 2026-08-23, legacy source lineage `KR_KOSPI200_WIKI`. This file is used only to define a deterministic test probe, not as current membership evidence.
- Selection rule: deduplicate by six-digit local code, sort ascending, select ranks round(i*(N-1)/11), i=0..11. Selection frozen before evidence testing.
- Selection SHA256: eb46c9992faa5603de34f279356aee4756409d575de55f22a60b6893ddcf9a5d
- Access timestamp: 2026-09-07T05:38:59Z

## Sources

| Source | Rank | Role | Result |
|---|---|---|---|
| KRX Data Marketplace landing | R1 | Official population/listing authority | GET landing reachable (HTTP 200); no row-level evidence in landing |
| KRX `getJsonData.cmd` | R1 | Intended row-level membership/listing path | Prior repository probes returned HTTP 403 and HTTP 400; parsed rows 0; reproducibility not proven |
| Korea Securities Depository (KSD) | R1 | Identifier/security support | Official authority identified; no public row-level ISIN/class path was validated in this gate |
| Issuer IR / filings | R1 supporting | Security/class/corporate-action support | Not used to manufacture evidence after central KRX path failed |
| ISO 10383 MIC list | R1 reference | MIC semantics | Supports separate MIC treatment; does not prove security identity |

## Technical access record

- KRX endpoint: https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd
- Method: POST in prior runner path; parameters included the official KRX block identifier and trade-date context.
- Session/cookie/referer: endpoint behavior was not reproducibly successful; no bypass or authentication workaround attempted.
- Response: official landing 200; row-level endpoint 403/400; no row-level content.
- KSD: public authority page https://www.ksd.or.kr/; row-level security/class/ISIN capability remains unvalidated.
- ISO MIC reference: https://www.iso20022.org/market-identifier-codes

## Limitations

The sample results are validation outcomes, not admission records. Missing evidence is not converted into identity, ISIN or admission. No credentials, bypass, CAPTCHA workaround, full population download, candidate generation, admission, Universe write or follow-on stage was performed.
