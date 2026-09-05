# AU-1 Controlled Integration Write Report
Start HEAD: f6e3511
Local sealed input: output_au1_evidence_gate/AU1_INTEGRATION_READY.csv (not on origin; not reconstructed from 159).
Input SHA256: 2921df416aeb33ddf4e224ff89792ff9789f6f429a845841750454997ae7d21f
Input Count = 153. All Final_Admission_Status=INTEGRATION_READY.
Dry-run: TARGET 153 NEW 153 ALREADY_PRESENT 0 CONFLICT 0 INVALID 0 BLOCKED 0.
WRITE_ALLOWED default False. Lifted only because AND-guard matched 153/153/0/0/0/0.
Written = 153. Provenance Source_ID=AU1_EVIDENCE_ADMISSION_GATE + local sealed source sha256 2921df416aeb33dd. No origin sidecar path claimed.
Research Partial 2374 -> 2527. AU 0 -> 153.
Prefix-Integrity: first 2374 identity tuples FIELD DIFF = 0 (G12).
Duplicate QA: unique WS_ID; nonempty ISIN unique; full identity unique. Ticker-only vs other MIC allowed.
Exclusion QA: PDIDB/SGH/VAU/DNL/ELV/NWS NOT WRITTEN. Build REVIEW/EXCLUDE NOT WRITTEN.
No-touch: Strict 759 Frozen 0 US-1 372 US-2 369 v7.2 untouched.
Gates G0-G17: {'G0': 'PASS', 'G1': 'PASS', 'G2': 'PASS', 'G3': 'PASS', 'G4': 'PASS', 'G5': 'PASS', 'G6': 'PASS', 'G7': 'PASS', 'G8': 'PASS', 'G9': 'PASS', 'G10': 'PASS', 'G11': 'PASS', 'G12': 'PASS', 'G13': 'PASS', 'G14': 'PASS', 'G15': 'PASS', 'G16': 'PASS', 'G17': 'PASS'}
Commit: write script + write artifacts + research partial + this report only. Evidence-gate sidecar not in this commit.
Next: SEPARATE AU-1 Post-Integration Integrity Audit. WRITE PASS ≠ AUDIT PASS.
Status: AU-1 CONTROLLED INTEGRATION WRITE — PASS
