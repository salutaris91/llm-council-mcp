# Roadmap

## Next
- **API-Key sicherer speichern:** Optionales `keyring`-Backend einführen, damit der OpenRouter-Key im OS-Schlüsselspeicher statt im Klartext-`settings.json` liegen kann. `settings.json` bleibt für nicht-sensitive Einstellungen zuständig; Migration und Fallback müssen klar dokumentiert sein.
- **Kaputte Konfiguration sichtbar machen:** `load_settings()` darf JSON-/Lesefehler nicht still zu `{}` degradieren. Setup-UI und Logs sollen Datei, Ursache und nächsten Schritt anzeigen, damit Nutzer nicht wegen unsichtbarer Config-Probleme falsche Defaults oder fehlende Tools debuggen.
- **Host-Update-/Restart-Zustand klarer anzeigen:** Nach Install/Update unterscheiden zwischen „Config-Pin geschrieben" und „Host läuft tatsächlich mit neuer Version". Für CLI-Hosts ggf. heuristisch arbeiten, aber die UI soll klar sagen, welcher Host noch einen Neustart braucht.
- **Installer-Fehler besser erklären:** Besonders kaputtes JSON in `mcp_config.json` mit Datei, Zeile/Position und Reparaturhinweis melden.

## Product Features After Stabilization
- **Job/Poll-Modus für lange `ask_council`-Runs:** `ask_council` bzw. ein neues Start-Tool gibt sofort eine `job_id` zurück; `get_council_result(job_id)` pollt Ergebnis und Status. Das macht Fortschritt host-unabhängig sichtbar und entschärft Tool-Timeouts, sobald reale Läufe >2-3 Minuten problematisch werden.
- **`ask_expert_council` (Voll/3a) als leichter Persona-Modus:** Multi-Modell wie `ask_council`, aber jedes Modell bekommt zusätzlich eine Persona als Tonfall-/Fokus-Hint, nicht als volle Charaktermaske. Datenmodell wird zu Modell↔Persona-Paaren (`council_members`, schema_version 2, abwärtskompatibel); Stage 1 baut pro Modell einen eigenen System-Prompt, Stage 2/3 bleiben unberührt.
- **Testabdeckung für die riskanten Ränder ausbauen:** Settings-Migration, kaputte Config-Dateien, Tool-Sichtbarkeit, Host-Installer-Pfade und Update-/Restart-Anzeigen gezielt testen.

## Deliberately Deferred
- **Kein direkter Workspace-Zugriff im Server:** Der MCP-Host soll Dateien lesen und relevanten Kontext übergeben. Das hält den Server sicherer, einfacher und host-kompatibel.
- **Keine frühe Websuche in Stage 1:** Erhöht Kosten, Latenz, Reproduzierbarkeitsprobleme und Sicherheitsfläche. Erst prüfen, wenn der Kernworkflow stabil bleibt und es einen klaren Nutzungsfall gibt.
- **Kein großer Chat-/Diskussionsmodus vor Zuverlässigkeitsarbeit:** Erst lange Runs, Config-Fehler, Secret-Handling und Update-UX stabilisieren; danach kann ein interaktiver Modus sinnvoll bewertet werden.
- **Light-Modus nicht als echte Modell-Diversität verkaufen:** Die klare Diversity-Warnung bleibt wichtig, weil alle Perspektiven vom Host-Modell simuliert werden.

## Released in 0.2.0
- **Neues Tool `ask_internal_council` (Light-Modus).** Liefert sofort einen strukturierten 5-Perspektiven-Prompt an den Host-Agenten zurück. Läuft ohne OpenRouter-API-Key und ohne zusätzliche API-Kosten, weil Claude Code / Codex / Antigravity das interne Council mit dem jeweils aktuellen Host-Modell ausführt.
- **Bestehendes `ask_council` bleibt der echte Multi-Modell-Modus.** Der vollständige Karpathy-Workflow über OpenRouter bleibt unverändert erhalten: mehrere Modelle antworten parallel, bewerten sich anonym und ein Chairman-Modell synthetisiert das Ergebnis.
- **Flache MCP-Parameter für beide Tools.** `ask_internal_council` und `ask_council` verwenden jetzt direkte Parameter wie `question`, `code_context`, `models` und `chairman` statt eines verschachtelten `params`-Objekts. Das behebt Kompatibilitätsprobleme mit Hosts, die Tool-Argumente flach übergeben, behält aber Schema-Beschreibungen und Längenlimits bei.
- **Tool-Sichtbarkeit in der Setup-UI.** `ask_internal_council` und `ask_council` können einzeln aktiviert oder ausgeblendet werden. Deaktivierte Tools werden dem MCP-Host nicht angeboten; Änderungen wirken nach einem Host-/Server-Neustart.
- **Diversitäts-Hinweise für den Light-Modus.** UI, Tool-Beschreibung und Prompt machen klar, dass die fünf Sichtweisen beim internen Council von einem einzigen Modell stammen und deshalb gemeinsame blinde Flecken haben können.
- **Dokumentation und Tests aktualisiert.** README erklärt beide Modi, die API-Key-/Kosten-Unterschiede und den passenden Einstieg; neue Tests prüfen Prompt-Generierung, bedingte Tool-Registrierung und flache MCP-Schemas.

## Released in 0.1.10
- **Bugfix: „Aktualisieren" bei Claude Code schlug fehl** mit „MCP server llm-council already exists in user config". `claude mcp add` überschreibt keinen bestehenden Eintrag; `claude_install` entfernt den Eintrag jetzt zuerst (best-effort) und fügt ihn dann neu hinzu — idempotent/update-fähig, analog zu Codex/Antigravity, die ihre Config ohnehin überschreiben.
- **Setup-UI-Version im Header.** Die Seite zeigt jetzt „Setup-UI v<version>" direkt neben dem Titel, abgeleitet aus `_version.py` (Single Source) — aktualisiert sich also bei jedem Release automatisch, kann nicht vergessen werden. So ist sofort erkennbar, ob man eine alte oder die frische UI-Instanz vor sich hat (vorher nur aus dem Update-Hinweis ableitbar). README-Release-Schritt entsprechend ergänzt.
- **Banner „Aktualisierung noch nicht abgeschlossen".** Oben erscheint ein Hinweis, sobald mindestens ein Host noch auf einer älteren Version gepinnt ist als die Zielversion — mit Auflistung der betroffenen Hosts und ihrer aktuellen Version. Verschwindet erst, wenn alle Hosts auf der Zielversion sind (analog zum bestehenden PyPI-Update-Banner, aber für die Host-Pins).

## Released in 0.1.9
- **Install-Buttons & Host-Status zeigen jetzt die Version (statt nur „installiert").** Vorher hieß der Button immer „Installieren", obwohl es in Wahrheit das (Neu-)Schreiben des Versions-Pins ist — verwirrend, wenn ein Host schon eingetragen war. Jetzt: pro Host wird die **gepinnte Version** angezeigt (z. B. „✓ installiert (@0.1.7)"), und das Button-Label ist kontextabhängig — „Installieren" (nicht eingetragen), „Aktualisieren" (eingetragen, aber veraltet, farblich hervorgehoben) oder „Neu eintragen" (bereits auf Zielversion). Versions-Lesung via `installer.*_pinned_version()` (Regex auf die `@version`-Pins in den Host-Configs bzw. `claude mcp list`).

## Released in 0.1.8
- **Update-Hinweis-Text korrigiert (war irreführend).** Der `update_body` in `setup_ui.py` sagte „danach die Seite neu laden und erneut auf 'Installieren' klicken" — das war falsch: Neuladen bewirkt nichts (der Hinweis hängt am *laufenden* Server, nicht an der Seite), und der entscheidende Schritt **Host-Neustart** fehlte ganz. Neuer Text (DE/EN) nennt jetzt die drei echten Schritte: 1) Befehl im Terminal ausführen (öffnet die aktualisierte UI, ggf. auf Fallback-Port), 2) pro Host auf „Installieren" klicken, 3) Host neu starten — und stellt klar, dass der Hinweis erst nach dem Host-Neustart verschwindet.

## Released in 0.1.7
- **Standalone-Setup-UI reused nicht mehr eine bereits laufende (ältere) UI.** Folgefix zu 0.1.6: Der Reuse-Mechanismus war für den server-eingebetteten Auto-Start gedacht (kein Tab-Spam), aber falsch für den expliziten `llm-council-setup`-Aufruf — dort wurde der Nutzer auf eine evtl. veraltete, schon laufende UI (z. B. ein noch aktiver alter MCP-Server auf 5151) umgelenkt, statt die frisch via `uvx --refresh` geladene Version zu starten. Dadurch sah man die neue Install-/Neustart-Logik nie. `main()` startet jetzt **immer die eigene Version** (5151 wenn frei, sonst Fallback 5152–5160); der Reuse bleibt ausschließlich dem server-eingebetteten Starter vorbehalten.

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
- **Per-Host „Neustart ausstehend"-Anzeige.** Aktuell vergleicht der Stale-Host-Banner / „Aktualisieren"-Button nur den *Config-Pin* mit der Zielversion. Beim Klick auf „Aktualisieren" wird der Pin sofort geschrieben, also verschwindet die Markierung — obwohl der Host-Prozess noch die alte Version fährt, bis er neu gestartet wird. Gewünscht: zwischen „Config aktualisiert" und „Host läuft tatsächlich schon auf neuer Version" unterscheiden und z. B. „Neustart ausstehend: Codex, Claude Code" anzeigen. Knackpunkt: die *laufende* Version ist nur für den server-eingebetteten Prozess (Port-Ping/PID) ermittelbar, für CLI-Hosts (Codex/Claude) kaum — ggf. heuristisch über „seit Config-Änderung noch kein Neustart erkannt" lösen.
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
