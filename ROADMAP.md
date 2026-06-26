# Roadmap

## Next (0.1.4)

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
- Windows-Support (aktuell Mac-zentriert).
- Weitere Hosts (z. B. Cursor).
- Aus dem Original bewusst ausgelassen: TOON-Encoding.
- Optionale Web-Suche in Stufe 1 (optionaler Aufruf externer Quellen).
- Bearbeitbare Prompt-Vorlagen in der UI / Konfiguration für maximale Anpassbarkeit.
- Alternative Modi für das Council (z. B. ein Modell als dedizierter "Kritiker" oder Advocatus Diaboli).
- Diskussions-Modus / Chat-Verlauf (z. B. iterativer Dialog zwischen dem anfragenden Client und dem Chairman, um gemeinschaftlich abzustimmen, welche Dateien für die Entscheidung im Kontext benötigt werden).
- `open_ui_on_start`-Default für sehr breite Distribution überdenken (aktuell True).
