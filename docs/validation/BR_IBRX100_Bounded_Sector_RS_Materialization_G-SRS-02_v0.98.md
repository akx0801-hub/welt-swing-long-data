# BR_IBRX100 Bounded Sector-RS Materialization — G-SRS-02 / v0.98

G-SRS-02 authorizes bounded BR_IBRX100 materialization under unchanged G-SRS-01/v0.97. The authoritative payload is the content-addressed Drive package `WELT-SWING_BR_IBRX100_Sector-RS_v0.98_Payload.zip`, Drive File ID `14rihggjcfiywzhph7HjPhwFE4jHTCl-a`, SHA-256 `de6cf0268cb1354d16ea663f8f6be4d27d16aa6ed8e628985456bee2189f02eb`.

Live Drive round-trip verification passed: 8,516 package bytes, ZIP integrity PASS, exact four-member set, member hashes verified. The complete materialization member has 37 rows: 28 `SECTOR_RS_VERIFIED`, 9 `RS_NOT_VERIFIED_INSUFFICIENT_SECTOR_PEERS`. Materialization member SHA-256: `991df87fa070fd4a36d6caa4fdbbe2a1632b0d13b189f764c8554edb1c2386ab`. Semantic SHA-256: `de1640a560a9f71d3fe364e0ac9812e40ddcdf330de4bc85c92779fc84e419ca`.

Git is the authority/control plane; Drive is the payload plane. No BR materialization CSV or peer-reference CSV is committed to Git. Future consumers resolve pointer → G-SRS-02 → exact Drive ID → package SHA → ZIP integrity → member SHA → semantic SHA; any mismatch fails closed with no historical fallback.

Global verified Sector-RS remains 28/1425; GLOBAL_SECTOR_RS_READY=NO. P0 numeric thresholds and promoted lane rules remain empty; P0/P1/P2 runs remain zero. Seven parked cohorts remain unchanged. No provider refresh or source research occurred.
