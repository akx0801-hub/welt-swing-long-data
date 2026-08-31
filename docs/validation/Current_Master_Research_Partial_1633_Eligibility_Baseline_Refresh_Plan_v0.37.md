# v0.37 — Research-Partial 1633 Eligibility Baseline and Data Refresh Plan

Status: DEV / RESEARCH / SHADOW — NOT PRODUCTIVE.

This offline stage reconciles the 1633-row current research partial. It does not retrieve prices, refresh mappings, execute P0, change the Current Master, promote eligibility, or reopen the six source-governance blocks.

The baseline separates source-superset membership from identity, instrument, mapping, history, liquidity, Scalable plausibility and prior eligibility evidence. Price-derived evidence is prior evidence only and is planned for refresh before any current eligibility calculation.

Required output gates are 1633 unique WS_ID rows in both baseline and refresh plan; all productive and frozen flags remain false. Brazil v0.34/v0.33/v0.32 files are joined only by WS_ID. Name-only joins and legacy promotion are rejected.

The follow-up is selected from the exception ledger: collision remediation if unresolved baseline collisions exist; otherwise controlled mapping/history/liquidity refresh. No network request is made in v0.37.
