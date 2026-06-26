# Roadmap

## Next (0.1.5)
- (Noch keine Aufgaben geplant)

## Released in 0.1.4
- **Update-Hinweis in der Setup-UI:** Die UI vergleicht die installierte (gepinnte) Version mit der neuesten auf PyPI und zeigt einen nicht-blockierenden Hinweis, wenn ein Update verfügbar ist — inkl. Erinnerung an `uvx --refresh …` + erneutes „Install".
- **Single-Source-Version:** Eine kanonische `__version__`-Konstante in `_version.py`, aus der `pyproject.toml`, `server.py` und der Installer-Pin abgeleitet werden.
- **Feinere Fortschritts-Meldungen:** Stage 1/2 melden pro fertigem Modell ("Stage 1: 3/5 Modelle geantwortet") statt nur an Stage-Grenzen — lebendigeres Feedback auf rendernden Hosts (Antigravity). Best-effort, darf den Lauf nie unterbrechen.
- **README-Hinweis:** Kurzer Satz (DE/EN), dass Live-Fortschritt host-abhängig ist (Antigravity zeigt Progression, Codex nur Spinner) und ein Call 30–120 s dauert.
- **Automatisches Publishing via GitHub Actions:** Trusted Publishing (tokenlos via OIDC) bei Push eines Versions-Tags.

## Released in 0.1.3
- Codex-Install-Button repariert: tomli-Import scheiterte auf Python 3.11+ (uvx) und blockierte die Codex-Registrierung. Nutzt jetzt stdlib tomllib zum Lesen.
- Repo-URLs an den umbenannten GitHub-Namen (llm-council-mcp-server) angeglichen.

## Released in 0.1.2
- Bugfix: requirements.txt bereinigt (python-dotenv entfernt, platformdirs>=4.0.0 hinzugefügt) für Method B.

## Released in 0.1.1
- README: Quick-Start-Walkthrough, OpenRouter-Key-Quelle, Antigravity-Pfad `~/.gemini/config/mcp_config.json`, Usage-Beispiel, Troubleshooting, zweisprachig (DE/EN) und Vereinfachungen.
- serverInfo.version meldet App-Version (0.1.1) statt MCP-Library-Version.
- DEV_MODE = False standardmäßig im Release-Paket gesetzt.

## Soon
- `keyring`-Backend (API-Key im OS-Schlüsselspeicher statt Klartext-settings.json) als optionale Wahl.
- Freundlichere Installer-Fehlermeldung bei kaputtem JSON in mcp_config.json (Zeile/Datei nennen).
- Optional dünnes PyPI-Alias-Paket `llm-council-setup`, damit das bequeme bare `uvx llm-council-setup` funktioniert.

## Later / Maybe
- **Job/Poll-Modus für lange Calls:** `ask_council` gibt sofort eine job_id zurück, `get_council_result(job_id)` pollt. Macht Fortschritt auf JEDEM Host sichtbar und entschärft Tool-Call-Timeouts. Wird relevant, sobald Läufe real an Host-Timeouts scheitern (Laufzeiten > ~2–3 Min beobachtet).
- Windows-Support (aktuell Mac-zentriert).
- Weitere Hosts (z. B. Cursor).
- Aus dem Original bewusst ausgelassen: TOON-Encoding.
- Optionale Web-Suche in Stufe 1 (optionaler Aufruf externer Quellen).
- Bearbeitbare Prompt-Vorlagen in der UI / Konfiguration für maximale Anpassbarkeit.
- Alternative Modi für das Council (z. B. ein Modell als dedizierter "Kritiker" oder Advocatus Diaboli).
- Diskussions-Modus / Chat-Verlauf (z. B. iterativer Dialog zwischen dem anfragenden Client und dem Chairman, um gemeinschaftlich abzustimmen, welche Dateien für die Entscheidung im Kontext benötigt werden).
- `open_ui_on_start`-Default für sehr breite Distribution überdenken (aktuell True).
