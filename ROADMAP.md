# Roadmap

## Next (0.1.1)
- README: Quick-Start-Walkthrough, OpenRouter-Key-Quelle, Antigravity-Pfad `~/.gemini/config/mcp_config.json`, Usage-Beispiel, requirements.txt-Fix, Troubleshooting.
- serverInfo.version meldet App-Version (0.1.0) statt MCP-Library-Version.
- GitHub-Repo: an Paketnamen anpassen (`llm-council-mcp-server`) und Sichtbarkeit entscheiden.

## Soon
- `keyring`-Backend (API-Key im OS-Schlüsselspeicher statt Klartext-settings.json) als optionale Wahl.
- Freundlichere Installer-Fehlermeldung bei kaputtem JSON in mcp_config.json (Zeile/Datei nennen).
- Optional dünnes PyPI-Alias-Paket `llm-council-setup`, damit das bequeme bare `uvx llm-council-setup` funktioniert.

## Later / Maybe
- Windows-Support (aktuell Mac-zentriert).
- Weitere Hosts (z. B. Cursor).
- Aus dem Original bewusst ausgelassen: TOON-Encoding, Web-Suche in Stufe 1 — nur falls je gewünscht.
- `open_ui_on_start`-Default für sehr breite Distribution überdenken (aktuell True).
