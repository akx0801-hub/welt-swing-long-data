# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 17:46 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

Authoritative DEV master specification: `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Latest completed checkpoint: **TMX Symbol Semantics Probe v0.13**  
Repo HEAD: `b4d9501eb430e38ca1ad81ddd7580234cdb49fd6`

Confirmed v0.13:
- Canada targets 105
- exact current TMX symbol matches 105/105
- suffix patterns: 98 `NO_DOT_SUFFIX`, 7 `DOT_CLASS_LIKE`
- decisions changed 0
- remaining manual rows 650
- strict candidates 2,037
- strict freeze false
- P0 false
- Alpha Vantage forbidden

Remaining before v0.14: CA 105, EU 365, HK 82, KR 92, MX 6.

Next: **v0.14 — TMX Instrument Resolution**. It revalidates S&P/TSX Composite eligibility semantics and TMX Policy 5.8 root/suffix semantics before any classification. If either source validation fails, zero new decisions. No per-security requests.

Resume: read this file, master spec, newest summary, confirm `main` HEAD, then continue from the smallest valid stage.
