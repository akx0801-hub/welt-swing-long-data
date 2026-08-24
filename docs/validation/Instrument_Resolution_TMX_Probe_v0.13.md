# Welt-Swing Long DEV — TMX Symbol Semantics Probe v0.13

v0.13 ist eine Evidence-only-Stufe für die 105 verbleibenden `CA_TSX`-Zeilen.

Nach JSE v0.12 stehen **650 offene Fälle** und **2.037 Strict Candidates**. Südafrika ist mit 17/17 exakten JSE-Matches vollständig aufgelöst.

v0.13 nutzt maximal drei offizielle TMX-Requests: MOC-Seite, ggf. deren Full-List-Symbol-Download und die offizielle Symbol-Suffix-Notice. Es gibt keine per-Security-Abfragen und keine Instrumententscheidungen.

Suffixe wie `.UN`, `.PR.*`, `.A`, `.B` werden nur gezählt. Kein PASS aus fehlendem Suffix, keine Namensheuristik und keine automatische Entscheidung nur aus einem Muster.

Erst v0.14 darf klassifizieren, falls kombinierte offizielle Evidenz Common/Ordinary gegenüber Units/Preferreds/anderen Strukturen deterministisch trennt.

Governance unverändert: Alpha Vantage verboten, keine Preis-/FX-Downloads, P0 aus, keine produktive Trade Authority, Canonical Master unverändert.
