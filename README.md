# LLM Council MCP

[English Version](#english-version) | [Deutsche Version](#deutsche-version)

---

# English Version

A lightweight, local MCP server for your Mac that replicates the 3-stage workflow of [llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus) — using the **exact original prompts** directly against OpenRouter, without any Docker or NAS dependencies. Works with Claude Code, Codex CLI, and Antigravity via MCP.

## What it is (and what it isn't)

`council_core.py` is a standalone Python port of the 3 stages from `backend/council.py` and `backend/runtime_settings.py` of the original `llm-council-plus` repository:

1. **Stage 1** — Each council model answers your query independently in parallel.
2. **Stage 2** — Each model rates/ranks the anonymized answers of the others ("Response A", "Response B", ...), so no model can recognize and favor its own answer.
3. **Stage 3** — A Chairman model reads Stage 1 + 2 and writes a final synthesized answer. If the Chairman fails, the code automatically falls back to other council models as Chairman (1:1 fallback logic from original).

Prompt templates for all 3 stages are copied **word-for-word** from `backend/runtime_settings.py`, as well as the default temperatures (Stage 1: 0.5, Stage 2: 0.3, Stage 3: 0.4) and OpenRouter request logic (retries with backoff on 429).

**Deliberately left out** (for a lean, personal tool):
- TOON encoding of Stage 1/2 data (just token efficiency, doesn't change outcome).
- Web search / tool results in Stage 1.
- Editable prompts via UI — prompt templates remain constants in `council_core.py` to preserve prompt fidelity. Temperatures and max tokens, however, can be customized in the Setup UI settings.
- Conversation history / multi-turn memory.

The server has **no direct file access**. This is intentional: the calling tool (Claude Code, Codex, Antigravity) already has access to your local files and passes relevant code/context as parameters (`code_context`) during the tool call.

---

## Installation & Setup

### Method A: Quick Onboarding via PyPI (Recommended)
You can run the Setup UI directly from PyPI without cloning the repository (requires the package installer [uv](https://github.com/astral-sh/uv) to be installed, e.g., via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`):
```bash
uvx --from llm-council-mcp-server llm-council-setup
```
This automatically opens `http://127.0.0.1:5151` in your browser.

### Method B: Manual Clone (for Development)
If you want to modify the source code locally:
```bash
git clone https://github.com/salutaris91/llm-council-mcp.git
cd llm-council-mcp
python3 -m venv venv
source venv/bin/activate

# Install dependencies (either via requirements.txt or directly using pyproject.toml)
pip install -r requirements.txt  # Or: pip install .
```
Run the Setup UI locally:
```bash
python3 setup_ui.py
```

---

## 🚀 Quick Start / First Run

Follow these steps to get up and running:

1. **Get an OpenRouter API Key:**
   - Create an API key at **[openrouter.ai/keys](https://openrouter.ai/keys)**.
   - *Note:* Make sure your OpenRouter account has a small funded balance, as each query runs multiple models in parallel.
2. **Launch the Setup UI:**
   - Run `uvx --from llm-council-mcp-server llm-council-setup` in your terminal. This will automatically open the local configuration panel in your web browser.
3. **Configure Settings:**
   - Paste your API key, select your preferred council and Chairman models, and click **Save**.
4. **Register the Server:**
   - Under the **Install** section of the Setup UI, click the **Install** button next to your desired tool (Claude Code, Codex CLI, or Antigravity).
5. **Restart Your Tool:**
   - Fully restart your MCP-enabled editor/client (e.g. reload Antigravity) to apply the changes.
6. **Start Deliberating:**
   - In your chat client, run a query (see [Usage](#usage) below).

---

## Setup UI & Settings Storage

The Setup UI saves your API key, model selections, and custom temperatures to a `settings.json` file in your user config directory (e.g. `~/Library/Application Support/llm-council` on macOS).
*Legacy Note:* If you have an existing `.env` file from manual setups, it will be automatically imported into `settings.json` on the first start, and can be safely removed afterwards.

---

## Usage

To use the council, simply ask your MCP host to query it, passing any code context you want it to evaluate.

**Example Prompts:**
* *"Use the council to get a second opinion on whether we should use Redis or an in-memory cache for this class."*
* *"Ask the council to review my implementation of this sorting algorithm."*

**What happens under the hood:**
The server will run the 3-stage consensus pipeline. Because this involves multiple parallel and sequential LLM calls, the tool response typically takes **30 to 120 seconds** to complete. It will return a formatted Markdown report consisting of the Chairman's synthesis, followed by the individual models' responses and rankings.

---

## Tool Registration (Manual, alternative to Setup UI)

### 1. If installed via PyPI (Method A)

#### Claude Code
```bash
claude mcp add llm-council --scope user -- uvx --from llm-council-mcp-server llm-council-mcp
```

#### Codex CLI
Add to `~/.codex/config.toml`:
```toml
[mcp_servers.llm-council]
command = "uvx"
args = ["--from", "llm-council-mcp-server", "llm-council-mcp"]
```

#### Antigravity
Add to the configuration file located at `~/.gemini/config/mcp_config.json` (do not use `~/.gemini/antigravity/`):
```json
{
  "mcpServers": {
    "llm-council": {
      "command": "uvx",
      "args": ["--from", "llm-council-mcp-server", "llm-council-mcp"]
    }
  }
}
```

### 2. If cloned manually (Method B)
Replace `/path/to/venv/bin/python3` and `/path/to/llm-council-mcp/server.py` with your absolute paths.

#### Claude Code
```bash
claude mcp add llm-council --scope user -- /path/to/venv/bin/python3 /path/to/llm-council-mcp/server.py
```

#### Codex CLI (`~/.codex/config.toml`)
```toml
[mcp_servers.llm-council]
command = "/path/to/venv/bin/python3"
args = ["/path/to/llm-council-mcp/server.py"]
```

#### Antigravity (`~/.gemini/config/mcp_config.json`)
```json
{
  "mcpServers": {
    "llm-council": {
      "command": "/path/to/venv/bin/python3",
      "args": ["/path/to/llm-council-mcp/server.py"]
    }
  }
}
```

---

## 🛠️ Troubleshooting

* **Server not showing up in tool?**
  - Fully restart the client application (Claude Code, Codex, or Antigravity). MCP servers are loaded on startup.
* **Antigravity isn't picking up the server?**
  - Verify that the server is written to `~/.gemini/config/mcp_config.json`. If you manually created a file in `~/.gemini/antigravity/`, delete it and use the correct path.
* **OpenRouter API Errors (e.g. 401, 402)?**
  - Open the Setup UI and double-check your API key. Make sure your OpenRouter account has positive credit.
* **Check the Logs:**
  - Standard error logs are captured by your MCP host. Check your tool's log output or terminal window for details.

---

## Credits
- **Original Idea:** Andrej Karpathy — [karpathy/llm-council](https://github.com/karpathy/llm-council)
- **Prompt/Workflow Templates:** Ported from [DmitryBMsk/llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus)
- **This MCP Server:** Alexander Deja — [anderzlabs.de](https://www.anderzlabs.de/)

---

# Deutsche Version

Ein schlanker, lokaler MCP-Server für deinen Mac, der den 3-Stufen-Workflow von [llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus) nachbildet — mit den **exakten Original-Prompts**, direkt gegen OpenRouter, ohne Docker- oder NAS-Abhängigkeit. Nutzbar aus Claude Code, Codex CLI und Antigravity über MCP.

## Was das ist (und was nicht)

`council_core.py` ist eine eigenständige Python-Portierung der 3 Stufen aus `backend/council.py` und `backend/runtime_settings.py` des echten llm-council-plus-Repos:

1. **Stufe 1** — Jedes Council-Modell beantwortet deine Frage unabhängig, parallel.
2. **Stufe 2** — Jedes Modell bewertet/rankt die anonymisierten Antworten der anderen ("Response A", "Response B", ...), damit kein Modell seine eigene Antwort erkennen und bevorzugen kann.
3. **Stufe 3** — Ein Chairman-Modell liest Stufe 1 + 2 und schreibt eine finale, synthetisierte Antwort. Schlägt der Chairman fehl, probiert der Code automatisch die anderen Council-Modelle als Ersatz-Chairman durch (Fallback-Logik, 1:1 aus dem Original übernommen).

Die Prompt-Templates für alle 3 Stufen sind **wortwörtlich** aus `backend/runtime_settings.py` kopiert (siehe `STAGE1_PROMPT_TEMPLATE`, `STAGE2_PROMPT_TEMPLATE`, `STAGE3_PROMPT_TEMPLATE` in `council_core.py`), ebenso die Default-Temperaturen (Stufe 1: 0.5, Stufe 2: 0.3, Stufe 3: 0.4) und das OpenRouter-Aufruf-Schema (Retry mit Backoff bei 429).

**Bewusst weggelassen** (für ein schlankes, persönliches Tool):
- TOON-Encoding der Stufe-1/2-Daten (im Original nur eine Token-Effizienz-Optimierung, ändert das Ergebnis nicht).
- Web-Suche / Tool-Ergebnisse in Stufe 1.
- Editierbare Prompts über die UI — Prompt-Vorlagen bleiben Konstanten in `council_core.py`, um die Prompt-Treue zum Original nicht zu gefährden. Temperaturen und maximale Token können jedoch direkt in den Einstellungen der Setup-UI angepasst werden.
- Konversationsverlauf / Multi-Turn-Memory.

Der Server hat **keinen eigenen Dateizugriff**. Das ist Absicht: Das aufrufende Tool (Claude Code, Codex, Antigravity) hat bereits Zugriff auf deinen lokalen Code und übergibt relevanten Code/Kontext direkt als Parameter (`code_context`) beim Tool-Aufruf.

---

## Installation & Setup

### Methode A: Schnellstart via PyPI (Empfohlen)
Du kannst die Setup-Oberfläche direkt über PyPI ausführen, ohne das Repository klonen zu müssen (erfordert ein installiertes [uv](https://github.com/astral-sh/uv), z. B. installierbar via `curl -LsSf https://astral.sh/uv/install.sh | sh` oder `brew install uv`):
```bash
uvx --from llm-council-mcp-server llm-council-setup
```
Dies öffnet automatisch `http://127.0.0.1:5151` in deinem Browser.

### Methode B: Manueller Klon (für Entwickler)
Wenn du den Quellcode lokal anpassen möchtest:
```bash
git clone https://github.com/salutaris91/llm-council-mcp.git
cd llm-council-mcp
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren (entweder über requirements.txt oder pyproject.toml)
pip install -r requirements.txt  # Oder: pip install .
```
Lokale Setup-UI starten:
```bash
python3 setup_ui.py
```

---

## 🚀 Schnellstart / Erster Lauf

Befolge diese Schritte, um direkt loszulegen:

1. **OpenRouter API-Key holen:**
   - Erstelle einen API-Key auf **[openrouter.ai/keys](https://openrouter.ai/keys)**.
   - *Hinweis:* Stelle sicher, dass dein OpenRouter-Konto ein kleines Guthaben aufweist, da pro Anfrage mehrere Modell-Aufrufe parallel durchgeführt werden.
2. **Setup-UI starten:**
   - Führe `uvx --from llm-council-mcp-server llm-council-setup` im Terminal aus. Dadurch öffnet sich die lokale Konfigurationsoberfläche in deinem Browser.
3. **Einstellungen konfigurieren:**
   - Trage deinen API-Key ein, wähle deine bevorzugten Council- und Chairman-Modelle und klicke auf **Speichern**.
4. **Server registrieren:**
   - Klicke im Bereich **Install** der Setup-UI auf den Button **Install** neben dem Tool deiner Wahl (Claude Code, Codex CLI oder Antigravity).
5. **Tool neu starten:**
   - Starte deinen MCP-Client / Editor (z. B. Antigravity) komplett neu, um die Registrierung zu laden.
6. **Council anfragen:**
   - Stelle deine Frage im Chat-Interface (siehe [Nutzung](#nutzung-1) unten).

---

## Setup-UI & Speicherort der Einstellungen

Die Setup-UI speichert deinen API-Key, die Modell-Auswahl und angepasste Temperaturen in einer Datei namens `settings.json` im Konfigurationsverzeichnis (z. B. `~/Library/Application Support/llm-council` unter macOS).
*Migration:* Falls noch eine alte `.env`-Datei aus manuellen Setups vorhanden ist, wird diese beim ersten Start automatisch in die `settings.json` importiert und kann danach gelöscht werden.

---

## Nutzung

Um den Council zu nutzen, bitte einfach deinen MCP-Client darum, das Tool `ask_council` aufzurufen und übergib die Frage sowie den zu prüfenden Code.

**Beispiel-Prompts:**
* *"Nutze den Council für eine zweite Meinung dazu, ob wir für diese Klasse Redis oder einen In-Memory-Cache nehmen sollten."*
* *"Frag den Council nach einem Review für meine Implementierung dieses Sortieralgorithmus."*

**Was im Hintergrund passiert:**
Der Server führt die 3 Stufen des Council-Prozesses durch. Da dies mehrere parallele und sequenzielle LLM-Aufrufe erfordert, dauert die Antwort in der Regel **30 bis 120 Sekunden**. Du erhältst einen formatierten Markdown-Report mit der Synthese des Chairmans, gefolgt von den Antworten der Einzelmodelle sowie deren Rankings.

---

## Tool-Registrierung (Manuell, alternativ zur Setup-UI)

### 1. Bei Installation via PyPI (Methode A)

#### Claude Code
```bash
claude mcp add llm-council --scope user -- uvx --from llm-council-mcp-server llm-council-mcp
```

#### Codex CLI
Trage Folgendes in `~/.codex/config.toml` ein:
```toml
[mcp_servers.llm-council]
command = "uvx"
args = ["--from", "llm-council-mcp-server", "llm-council-mcp"]
```

#### Antigravity
Trage Folgendes in die Konfigurationsdatei unter `~/.gemini/config/mcp_config.json` ein (nutze nicht `~/.gemini/antigravity/`):
```json
{
  "mcpServers": {
    "llm-council": {
      "command": "uvx",
      "args": ["--from", "llm-council-mcp-server", "llm-council-mcp"]
    }
  }
}
```

### 2. Bei manuellem Klon (Methode B)
Ersetze `/pfad/zu/venv/bin/python3` und `/pfad/zu/llm-council-mcp/server.py` mit deinen absoluten Pfaden.

#### Claude Code
```bash
claude mcp add llm-council --scope user -- /pfad/zu/venv/bin/python3 /pfad/zu/llm-council-mcp/server.py
```

#### Codex CLI (`~/.codex/config.toml`)
```toml
[mcp_servers.llm-council]
command = "/pfad/zu/venv/bin/python3"
args = ["/pfad/zu/llm-council-mcp/server.py"]
```

#### Antigravity (`~/.gemini/config/mcp_config.json`)
```json
{
  "mcpServers": {
    "llm-council": {
      "command": "/pfad/zu/venv/bin/python3",
      "args": ["/pfad/zu/llm-council-mcp/server.py"]
    }
  }
}
```

---

## 🛠️ Fehlerbehebung

* **Server erscheint nicht im Tool?**
  - Starte die Client-Anwendung (Claude Code, Codex oder Antigravity) komplett neu. MCP-Server werden beim Start geladen.
* **Antigravity erkennt den Server nicht?**
  - Überprüfe, ob der Server-Eintrag in `~/.gemini/config/mcp_config.json` steht. Falls du manuell eine Datei in `~/.gemini/antigravity/` angelegt hast, lösche diese und nutze den korrekten Pfad.
* **Fehler beim Aufruf von OpenRouter (z. B. 401, 402)?**
  - Öffne die Setup-UI und kontrolliere deinen API-Key. Vergewissere dich, dass dein OpenRouter-Konto über ausreichend Guthaben verfügt.
* **Logs einsehen:**
  - Fehlermeldungen werden von deinem MCP-Client erfasst. Siehe in den Logs des Editors oder im Terminalfenster nach Details.

---

## Credits
- **Originalidee:** Andrej Karpathy — [karpathy/llm-council](https://github.com/karpathy/llm-council)
- **Prompt-/Workflow-Vorlage:** Portiert aus [DmitryBMsk/llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus)
- **Dieser MCP-Server:** Alexander Deja — [anderzlabs.de](https://www.anderzlabs.de/)
