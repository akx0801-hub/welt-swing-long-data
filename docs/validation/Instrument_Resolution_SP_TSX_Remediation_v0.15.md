# Welt-Swing Long DEV — S&P/TSX Semantics Remediation v0.15

v0.14 lief korrekt fail-closed: Die TMX Policy 5.8 wurde validiert, der direkte englische S&P/TSX-Methodology-PDF-Download lieferte im GitHub-Runner jedoch HTTP 403. Deshalb wurden 0 Kanada-Entscheidungen getroffen.

v0.15 ist bewusst **Evidence-only**. Es prüft zwei alternative offizielle S&P-Pfade:

1. die öffentliche S&P/TSX Canadian Indices Methodology HTML-Seite;
2. einen offiziellen lokalisierten S&P-PDF-Pfad derselben Methodik.

Die HTML-Seite muss die Aussagen zu common stocks / income trust units und zur vollständigen Income-Trust-Komponente tragen. Der PDF-Pfad wird zusätzlich auf die expliziten Ausschlussbegriffe preferred shares, exchangeable shares, warrants, installment receipts und USD-denominated securities geprüft.

Maximal zwei Requests, keine Einzelabfragen, 0 Entscheidungen. Queue 650 und Strict Candidates 2.037 bleiben unverändert. Erst bei ausreichend materialisierter offizieller Evidenz folgt eine separate Klassifikationsstufe.
