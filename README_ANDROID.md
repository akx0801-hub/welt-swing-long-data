# Welt-Swing Long – Android/GitHub Anleitung für Einsteiger

## Ziel
Du brauchst auf dem Android-Handy **kein Python**, kein Notebook und keine Kommandozeile.
GitHub Actions führt Python + yfinance auf GitHub-Servern aus. Du bedienst nur den Browser.

Der erste Lauf ist absichtlich nur ein **Cross-Market-Smoke-Test mit 37 öffentlichen Testaktien**.
Er testet Technik, Mapping, yfinance, Cache, QA und Feature-Ausgabe. Er ist **kein Welt-Swing-Scan** und erzeugt **keine Kaufentscheidung**.

---

## Was du von ChatGPT bekommst
Eine Datei:

`welt-swing-long-github-starter-v0.1.zip`

Die ZIP enthält alle Python-Skripte, die Test-Aktienliste, Konfiguration und Dokumentation.

Zusätzlich enthält sie:

`WORKFLOW_TO_COPY.txt`

Den Inhalt dieser kleinen Datei kopierst du einmal in GitHub.

---

# TEIL A – GitHub-Repository anlegen

1. Öffne auf dem Android-Handy in Chrome: `https://github.com/`
2. Melde dich an oder erstelle ein kostenloses Konto.
3. Falls die mobile Seite unübersichtlich ist: Chrome-Menü `⋮` → **Desktopwebsite**.
4. Tippe oben rechts auf `+` → **New repository**.
5. Repository name: `welt-swing-long-data`
6. Visibility: **Public**.
7. `Add a README file` darf aktiviert sein.
8. Tippe **Create repository**.

Wichtig: Das Repository ist öffentlich. Niemals Depotdaten, Kontostände, private Dokumente, Passwörter oder API-Keys dort speichern.

---

# TEIL B – Starter-ZIP hochladen

1. Öffne dein neues Repository.
2. Tippe **Add file** → **Upload files**.
3. Wähle auf dem Handy die Datei:
   `welt-swing-long-github-starter-v0.1.zip`
4. Unten bei Commit message kannst du schreiben:
   `Upload Welt-Swing starter package`
5. Tippe **Commit changes**.

Die ZIP bleibt zunächst ungeöffnet im Repository. Das ist korrekt.

---

# TEIL C – Einen einzigen Workflow anlegen

1. Im Repository: **Add file** → **Create new file**.
2. Oben in das Feld für den Dateinamen exakt eingeben:

   `.github/workflows/update_market_data.yml`

   GitHub erzeugt die Ordner `.github/workflows` automatisch.

3. Öffne auf dem Handy die heruntergeladene Datei `WORKFLOW_TO_COPY.txt`.
4. Markiere den kompletten Inhalt und kopiere ihn.
5. Füge den Inhalt in das große GitHub-Textfeld ein.
6. Tippe **Commit changes**.
7. Commit message z. B.:
   `Add Welt-Swing data workflow`

---

# TEIL D – Ersten Datenlauf starten

1. Öffne oben im Repository den Tab **Actions**.
2. Links bzw. in der Liste sollte **Welt-Swing Data Update** stehen.
3. Tippe darauf.
4. Tippe rechts **Run workflow**.
5. Im kleinen Dialog noch einmal **Run workflow**.

Jetzt läuft alles auf GitHub-Servern. Du kannst die Seite verlassen.

Status:
- gelber Punkt/Kreis = läuft
- grüner Haken = technisch erfolgreich
- rotes X = Fehler; dann nichts selbst reparieren, sondern ChatGPT den Repository-Link schicken

Der erste Lauf kann einige Minuten dauern, weil Python-Pakete installiert und Kursdaten geladen werden.

---

# TEIL E – Nach dem Lauf

Gehe zurück auf **Code** und öffne den Ordner `output`.
Dort sollten u. a. erscheinen:

- `coverage.json`
- `mapping_audit.csv`
- `cache_status.csv`
- `errors.csv`
- `batch_log_latest.csv`
- `features_latest.csv`
- `manifest.json`

Die große SQLite-Kurshistorie wird **nicht** öffentlich in GitHub gespeichert. Sie liegt im GitHub-Actions-Cache und wird beim nächsten Lauf wiederhergestellt.

Schicke ChatGPT danach einfach den Link zu deinem Repository, z. B.:

`https://github.com/DEINNAME/welt-swing-long-data`

ChatGPT kann dann die öffentlichen Ergebnisdateien prüfen.

---

# Wenn das Speichern der Ergebnisse mit 403 scheitert

Bei neuen persönlichen GitHub-Repositories ist der `GITHUB_TOKEN` standardmäßig teilweise read-only. Der Workflow fordert `contents: write` an; falls GitHub das trotzdem blockiert:

1. Repository → **Settings**
2. **Actions** → **General**
3. Abschnitt **Workflow permissions**
4. **Read and write permissions** auswählen
5. **Save**
6. Workflow erneut starten

---

# Was beim ersten Lauf NICHT passiert

- kein Alpha Vantage
- kein kostenpflichtiger Datenprovider
- kein API-Key
- keine Scalable-Abfrage
- kein P0-Kandidatenscan
- keine Order
- keine automatische tägliche Ausführung

Der erste Lauf testet ausschließlich die Free-Data-Grundlage.

---

# Danach

Wenn der Smoke-Test sauber ist, wird `universe/u3k_master.csv` mit dem tatsächlichen U3K befüllt und `config/run_config.json` auf diese Datei umgestellt. Dann kann derselbe Workflow batchweise auf die vollständige verfügbare U3K-Basis skalieren.
