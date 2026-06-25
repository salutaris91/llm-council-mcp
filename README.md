# LLM Council MCP (lokal, ohne Docker)

Ein schlanker, lokaler MCP-Server für deinen Mac, der den 3-Stufen-Workflow
von [llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus)
nachbildet — mit den **exakten Original-Prompts**, direkt gegen OpenRouter,
ohne Docker/NAS-Abhängigkeit. Nutzbar aus Claude Code, Codex CLI und
Antigravity über MCP.

## Was das ist (und was nicht)

`council_core.py` ist eine eigenständige Python-Portierung der 3 Stufen aus
`backend/council.py` und `backend/runtime_settings.py` des echten
llm-council-plus-Repos:

1. **Stufe 1** — jedes Council-Modell beantwortet deine Frage unabhängig, parallel.
2. **Stufe 2** — jedes Modell bewertet/rankt die anonymisierten Antworten der
   anderen ("Response A", "Response B", ...), damit kein Modell seine eigene
   Antwort erkennen und bevorzugen kann.
3. **Stufe 3** — ein Chairman-Modell liest Stufe 1 + 2 und schreibt eine
   finale, synthetisierte Antwort. Schlägt der Chairman fehl, probiert der
   Code automatisch die anderen Council-Modelle als Ersatz-Chairman durch
   (Fallback-Logik, 1:1 aus dem Original übernommen).

Die Prompt-Templates für alle 3 Stufen sind **wortwörtlich** aus
`backend/runtime_settings.py` kopiert (siehe `STAGE1_PROMPT_TEMPLATE`,
`STAGE2_PROMPT_TEMPLATE`, `STAGE3_PROMPT_TEMPLATE` in `council_core.py`),
ebenso die Default-Temperaturen (Stufe 1: 0.5, Stufe 2: 0.3, Stufe 3: 0.4)
und das OpenRouter-Aufruf-Schema (Retry mit Backoff bei 429).

**Bewusst weggelassen** (für ein schlankes, persönliches Tool nicht nötig):

- TOON-Encoding der Stufe-1/2-Daten (im Original nur eine
  Token-Effizienz-Optimierung, ändert das Ergebnis nicht)
- Web-Suche / Tool-Ergebnisse in Stufe 1
- Editierbare Prompts/Temperaturen über die UI (siehe unten) — die bleiben
  bewusst Konstanten in `council_core.py`, um die geprüfte Prompt-Treue zum
  Original nicht versehentlich zu gefährden. Wer sie ändern will, editiert
  die Datei direkt.
- Konversationsverlauf / Multi-Turn-Memory

Der Server hat **keinen eigenen Dateizugriff**. Das ist Absicht: das
aufrufende Tool (Claude Code, Codex, Antigravity) hat bereits Zugriff auf
deinen lokalen Code und übergibt relevanten Code/Kontext direkt als
Parameter (`code_context`) beim Tool-Aufruf — kein separater "Scout-Agent",
kein Ordner-Mounting nötig.

## Setup auf dem MacBook

```bash
cd llm-council-mcp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Öffne .env in einem Editor und trage deinen echten OPENROUTER_API_KEY ein.
# Nie den Key in einen Chat einfügen - nur lokal in die .env-Datei.
```

Schneller Funktionstest ohne MCP-Client (optional):

```bash
python3 -c "
import asyncio, council_core
async def main():
    r = await council_core.run_full_council('Sage in einem Satz: 2+2?')
    print(r['stage3']['response'])
asyncio.run(main())
"
```

## Setup-UI (empfohlen)

Statt `.env` von Hand zu editieren und die Registrierungsbefehle unten manuell
auszuführen, gibt es eine kleine lokale Weboberfläche dafür:

```bash
python3 setup_ui.py
```

Öffnet automatisch `http://127.0.0.1:5151` im Browser. Dort kannst du:

- OpenRouter-Key, Council-Modelle und Chairman-Modell setzen (schreibt in `.env`)
- pro Tool (Claude Code, Codex, Antigravity) per Knopfdruck installieren/entfernen,
  mit Status-Anzeige, ob aktuell installiert

Läuft **nur lokal** (127.0.0.1, kein Netzwerkzugriff von außen) und **nur
solange das Terminal offen ist** — kein Hintergrunddienst. Mit Strg+C beenden,
wenn fertig. Der eigentliche `ask_council`-MCP-Server (`server.py`) ist davon
komplett unabhängig und läuft separat on-demand, wenn Claude Code/Codex/
Antigravity ihn brauchen.

**Wie die Buttons technisch funktionieren** (siehe `installer.py`), pro Tool
unterschiedlich, bewusst so gewählt:

- **Claude Code**: über die offizielle `claude mcp add`/`remove`-CLI — die
  stabile, dokumentierte Schnittstelle. Setup-UI ruft diese Befehle für dich auf.
- **Codex**: direktes Schreiben in `~/.codex/config.toml` (Format laut aktueller
  offizieller Doku verifiziert). **Achtung:** Beim Speichern wird die gesamte
  Datei neu geschrieben — eigene Kommentare in dieser Datei gehen dabei verloren,
  andere `[mcp_servers.*]`-Einträge bleiben aber erhalten.
- **Antigravity**: direktes Schreiben in `mcp_config.json`, da kein offizielles
  CLI dafür existiert. Pfad ist im UI editierbar, falls der Standardpfad bei dir
  abweicht (siehe Unsicherheiten unten).

Die manuellen Befehle unten funktionieren weiterhin identisch — die UI ist nur
eine Komfortschicht darüber, kein zweiter Mechanismus.

## Registrierung in deinen 3 Tools (manuell, alternativ zur Setup-UI)

Bei allen drei brauchst du den **absoluten Pfad** zu `server.py` und idealerweise
zum `python3` aus deinem venv (`which python3` nach `source venv/bin/activate`).

### Claude Code

```bash
claude mcp add llm-council --scope user -- /absoluter/pfad/zu/venv/bin/python3 /absoluter/pfad/zu/llm-council-mcp/server.py
```

`--scope user` macht den Server in allen Projekten verfügbar (nicht nur im
aktuellen). Mit `claude mcp list` prüfst du, ob er registriert ist.

### Codex CLI

Codex unterstützt MCP-Server seit einiger Zeit offiziell (geprüft gegen die
aktuelle Doku auf developers.openai.com/codex/mcp). Zwei Wege, gleiches Ergebnis:

**Per CLI:**
```bash
codex mcp add llm-council -- /absoluter/pfad/zu/venv/bin/python3 /absoluter/pfad/zu/llm-council-mcp/server.py
```

**Oder manuell in `~/.codex/config.toml`:**
```toml
[mcp_servers.llm-council]
command = "/absoluter/pfad/zu/venv/bin/python3"
args = ["/absoluter/pfad/zu/llm-council-mcp/server.py"]
```

Mit `/mcp` in der Codex-TUI siehst du die aktiven Server.

### Antigravity

Antigravity legt MCP-Server in einer `mcp_config.json` ab (laut aktueller
Doku/Community-Quellen typischerweise unter `~/.gemini/antigravity/mcp_config.json`,
erreichbar auch über Settings → Customizations → MCP Servers in der App).
**Unsicherheit:** Antigravity ist noch jung und der genaue Pfad kann sich je
Version/Update unterscheiden — schau im Zweifel direkt im Settings-Menü nach
dem Punkt "MCP Servers" / "Customizations", statt blind dem Pfad zu folgen.

```json
{
  "mcpServers": {
    "llm-council": {
      "command": "/absoluter/pfad/zu/venv/bin/python3",
      "args": ["/absoluter/pfad/zu/llm-council-mcp/server.py"]
    }
  }
}
```

## Nutzung

Sobald registriert, kannst du in jedem der drei Tools sinngemäß sagen:

> Frag den Council: Sollten wir für den Cache Redis oder eine In-Memory-Lösung
> nehmen? Hier ist der relevante Code: [...]

Das Tool ruft `ask_council` mit `question` und `code_context` auf. Die Antwort
ist ein Markdown-Report: zuerst das Chairman-Fazit, danach die einzelnen
Stufe-1-Antworten zur Transparenz, danach (falls vorhanden) die Stufe-2-Rankings.

Ein Aufruf macht mehrere parallele + sequenzielle LLM-Calls und kann
**gut über eine Minute** dauern — bewusst gedacht für wichtige Einzel-
Entscheidungen, nicht für ständige Nutzung.

## Bekannte Unsicherheiten / was du selbst prüfen solltest

- Die exakten OpenRouter-Modell-IDs (`openai/gpt-5.1`,
  `google/gemini-3-pro-preview`, `anthropic/claude-sonnet-4.5`) stammen aus
  den Defaults von llm-council-plus zum Zeitpunkt der Recherche. Falls
  OpenRouter eine ID umbenennt oder ein Modell deprecated, schlägt der
  jeweilige Call mit einer Fehlermeldung fehl (wird im Report angezeigt,
  blockiert aber nicht die anderen Modelle) — einfach `COUNCIL_MODELS` in
  `.env` anpassen.
- Die `codex mcp add`-Syntax wurde gegen die aktuelle Doku geprüft; sollte sie
  sich geändert haben, hilft `codex mcp --help`.
- Antigravitys Config-Pfad/-Format wurde über Community-Quellen verifiziert,
  nicht über eine offizielle, vollständig geladene Doku-Seite (die Seite ist
  clientseitig gerendert und lieferte beim Abruf keinen Textinhalt) — im
  Zweifel das Settings-Menü in der App selbst prüfen.
- Die Setup-UI schreibt `config.toml` (Codex) und `mcp_config.json`
  (Antigravity) jeweils komplett neu. Bestehende Einträge anderer MCP-Server
  bleiben erhalten, aber eigene Kommentare/Formatierung in `config.toml`
  gehen beim Speichern verloren (TOML-Bibliotheken kennen keine Kommentare).
  Falls dir das wichtig ist: Codex lieber weiterhin manuell editieren.
- Die `claude mcp remove ... --scope user`-Syntax wurde nicht live gegen eine
  echte Installation getestet (kein `claude`-Binary in dieser Sandbox
  verfügbar) — die UI zeigt die rohe Kommandozeilen-Ausgabe an, falls etwas
  nicht wie erwartet läuft.

## Credits

- **Originalidee:** Andrej Karpathy — [karpathy/llm-council](https://github.com/karpathy/llm-council)
- **Prompt-/Workflow-Vorlage:** portiert aus [DmitryBMsk/llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus), einem Fork des Originals
- **Dieser MCP-Server:** Alexander Deja — [anderzlabs.de](https://www.anderzlabs.de/)

Die Prompts sind dem Original treu nachgebildet (Stage 1 & 2 wortgleich; Stage 3 auf Karpathys Original-Wortlaut zurückgeführt).
