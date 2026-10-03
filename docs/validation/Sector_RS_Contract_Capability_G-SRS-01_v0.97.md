# Sector-RS Contract + Bounded Capability — G-SRS-01 / v0.97

G-SRS-01 is a new forward-only explicit manager governance contract. Historical v0.59 gaps are acknowledged rather than rewritten: aggregation mean/median, Sector-specific leave-one-out, numeric minimum peer size, and temporal/as-of alignment were unresolved.

Peer membership is exactly `(Sector_Taxonomy, Sector_Code)`. The reference method is explicitly `LEAVE_ONE_OUT_SECTOR_PEER_MEDIAN`. Exact matching `feature_as_of_date` and finite horizon returns are required. Minimum synchronized OTHER peers is 2, recorded as `NEW_G_SRS_01_MANAGER_CONTRACT_DECISION`.

The governed G-FHR-01/v0.93 Drive package was verified before capability analysis: package SHA-256 `45d85da89ec288d9bc75164666eb745856f400a995d3e44b85d20e721a494574`, ZIP integrity PASS, `features_candidate.csv` SHA-256 `04608872250c482c630ef682825f869d70f7bd3e6cddf70e27e993f83e6625c9`, 1425 rows. Actual identifier schema is `Source_WS_ID`; `feature_as_of_date`, `R20`, and `R60` are exact.

BR_IBRX100 canonical metadata recomputes static group sizes 7, 6, 6, 5, 4, 2, 2, 2, 2, 1. Static potentially capable rows = 28; too-small-group rows = 9. All 37 BR feature rows are present at 2026-09-24 with finite R20/R60. Therefore capability is 28 rows for both horizons and combined; 9 rows are `RS_NOT_VERIFIED_INSUFFICIENT_SECTOR_PEERS`.

No Sector-RS excess values were calculated or persisted. Contract authorization is YES; materialization authorization is NO. Global Sector-RS READY is NO; global canonical metadata READY is NO. The other 1388 Frozen rows remain `SECTOR_RS_NOT_VERIFIED_NO_CANONICAL_METADATA`, not FAIL.

P0 thresholds and promoted lane rules remain empty; P0/P1/P2 runs are zero. Seven parked cohorts remain unchanged. External/provider requests are zero.

Next gate: **BR_IBRX100 SECTOR-RS MATERIALIZATION AUTHORIZATION MANAGER GATE**.

**STOP — no Sector-RS values, no P0.**
