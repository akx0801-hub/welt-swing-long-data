# Welt-Swing Long DEV — Instrument Resolution TMX v0.14

v0.14 klassifiziert die 105 verbleibenden Kanada-Zeilen deterministisch auf Basis der abgeschlossenen v0.13-Probe.

Ausgangspunkt: 650 offene Fälle, 2.037 Strict Candidates, 105/105 Kanada-Symbole exakt in der aktuellen TMX-Bulkliste bestätigt. Suffixmuster: 98 ohne Punkt-Suffix, 7 class-like.

Vor jeder Entscheidung werden zwei offizielle Quellen neu validiert: die S&P/TSX Canadian Indices Methodology und TMX Policy 5.8. Die S&P/TSX-Methodik begrenzt das Composite-Universum auf common stocks und income trust units und schließt u.a. preferred shares, exchangeable shares und warrants aus. TMX Policy 5.8 verlangt Suffixe zur Kennzeichnung spezifischer Aktienklassen sowie u.a. preferred shares, units, rights, warrants, debentures und subscription receipts.

Regeln: NO_DOT_SUFFIX = PASS; DOT_CLASS_LIKE = PASS; DOT_UN/DOT_PR/Warrant/Right/Debenture = FAIL; alles andere = NOT_VERIFIED. Diese Regeln gelten nur für v0.13-exakt-bestätigte aktuelle Symbole im eingefrorenen S&P/TSX-Composite-Targetset.

Scheitert eine offizielle Semantikprüfung, werden 0 neue Entscheidungen getroffen. Keine Namensheuristik, keine Einzelabfragen, kein Alpha Vantage, keine Preis-/FX-Downloads, P0 aus, Canonical Master unverändert.
