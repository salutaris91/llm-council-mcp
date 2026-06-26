# Roadmap

## Next (0.1.7)
- **Council-Modi als getrennte MCP-Tools (statt UI-Toggle):** Der Server exponiert mehrere Tools, der aufrufende Agent wählt situativ das passende — kein manuelles Umschalten. Drei Varianten, bewusst phasiert:
  - **Phase 1 (zuerst) — `ask_internal_council` (Light):** Läuft komplett auf dem Modell, bei dem der Nutzer gerade ist (Host-Abo, kein API-Key, keine Zusatzkosten). Ein einzelnes Modell nimmt nacheinander 5 verschiedene Sichtweisen ein. Das Tool führt nicht selbst aus, sondern liefert den strukturierten 5-Perspektiven-Prompt zurück, den der Host-Agent (Claude Code / Codex / Antigravity) auf seinem Abo ausführt. Einfachster, additivster Einstieg.
  - **Phase 2 — `ask_council` (bestehend):** Echtes Multi-Modell-Debating über parallele OpenRouter-Calls, keine Personas (= aktueller Karpathy-Modus, unverändert).
  - **Phase 3 — `ask_expert_council` (Voll/3a):** Multi-Modell wie Phase 2, aber jedes Modell bekommt zusätzlich eine Persona (1 Persona pro Modell, als Tonfall-/Fokus-Hint, nicht als volle Maske). Datenmodell wird zu Modell↔Persona-Paaren (`council_members`, schema_version 2, abwärtskompatibel); Stage 1 baut pro Modell einen eigenen System-Prompt, Stage 2/3 bleiben unberührt.
  - **Pro-Council an-/abschaltbar in den Einstellungen:** In der Setup-UI lässt sich jedes der drei Tools einzeln aktivieren/deaktivieren (z. B. nur internes Council für Nutzer ohne API-Key, oder Experten-Council ausblenden). Deaktivierte Tools werden vom Server gar nicht erst exponiert, damit der Host-Agent sie nicht anbietet. Da MCP-Hosts die Tool-Liste i. d. R. beim Serverstart lesen, wirkt das An-/Abschalten erst nach einem Host-/Server-Neustart — die UI muss das beim Umschalten klar kommunizieren („wird nach Neustart des Hosts aktiv", analog zum bestehenden Install-/Update-Flow).
  - **Kontextueller Diversitäts-Hinweis:** Je nach aktiviertem/gewähltem Modus erscheint ein nicht-blockierender Hinweis, wo die Aussagekraft eingeschränkt ist — z. B. beim internen Light-Council: „Achtung, die Diversität ist hier eingeschränkt, weil alle 5 Sichtweisen von *einem* Modell stammen (gemeinsame blinde Flecken). Für echte Modell-Diversität `ask_council` / `ask_expert_council` nutzen." Hinweis sowohl in der UI als auch in der Tool-Beschreibung/Ausgabe, damit der Modus nicht mit echtem Multi-Modell verwechselt wird.
  - Offene Entscheidung für Phase 3: Persona als leichter Hint vs. volle Charaktermaske (bestimmt, wie stark sich Phase 3 von Phase 2 abhebt).

## Released in 0.1.6
- **Update-Flow geglättet** — drei zusammenhängende Verbesserungen, damit ein Versionswechsel nicht mehr von Hand nachgezogen werden muss:
  - **Standalone-Setup-UI crasht nicht mehr bei belegtem Port.** `llm-council-setup` nutzt jetzt dieselbe „reuse-or-fallback"-Logik wie der server-eingebettete Starter (gemeinsame `resolve_ui_target`): läuft unsere UI schon auf 5151, wird einfach der Browser daraufgelenkt; ist der Port von einem Fremdprozess belegt, wird auf 5152–5160 ausgewichen — statt mit „Address already in use" abzubrechen.
  - **„Install" pinnt die neueste PyPI-Version statt der laufenden.** Behebt das Henne-Ei-Problem: bisher schrieb eine veraltete laufende UI ihren *eigenen* alten Versions-Pin zurück, sodass man nie vorwärtskam. `get_uvx_args`/die Install-Pfade nehmen jetzt die latest-Version, wenn ein Update erkannt wurde.
  - **Per-Host-Neustart-Hinweis nach dem Install.** Nach erfolgreicher Registrierung zeigt die UI pro Host genau den passenden Schritt (Claude Code/Codex: neue Session; Antigravity: App neu starten), weil MCP-Hosts ihre Config nur beim eigenen Start neu einlesen.

## Released in 0.1.5
- **Bugfix: Setup-UI öffnet sich nicht mehr bei jedem Server-Neustart erneut im Browser.** Wenn die UI bereits auf Port 5151 läuft (z. B. von einem vorherigen Start, den der LLM-Host neu gestartet hat), wurde zwar kein zweiter Flask-Server gestartet, aber trotzdem ein neuer Browser-Tab geöffnet. `_maybe_start_setup_ui` unterdrückt das Öffnen jetzt, wenn die eigene UI schon erreichbar ist.

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
