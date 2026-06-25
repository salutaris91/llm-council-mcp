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
You can run the Setup UI directly from PyPI without cloning the repository (requires the package installer [uv](https://github.com/astral-sh/uv) to be installed):
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
pip install -r requirements.txt

cp .env.example .env
# Open .env and add your OPENROUTER_API_KEY.
```
Run the Setup UI locally:
```bash
python3 setup_ui.py
```

---

## Setup UI

The local web interface allows you to:
- Set your OpenRouter API Key, council models, and Chairman model (saves to `.env` or config directory).
- Install/uninstall the MCP server in Claude Code, Codex CLI, and Antigravity with a single click.

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
Add to `mcp_config.json`:
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

#### Antigravity (`mcp_config.json`)
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
Du kannst die Setup-Oberfläche direkt über PyPI ausführen, ohne das Repository klonen zu müssen (erfordert ein installiertes [uv](https://github.com/astral-sh/uv)):
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
pip install -r requirements.txt

cp .env.example .env
# Öffne .env und trage deinen echten OPENROUTER_API_KEY ein.
```
Lokale Setup-UI starten:
```bash
python3 setup_ui.py
```

---

## Setup-UI

Die lokale Weboberfläche ermöglicht es dir:
- Deinen OpenRouter-Key, die Council-Modelle und das Chairman-Modell zu setzen (speichert in `.env` oder Konfigurationsverzeichnis).
- Per Knopfdruck den MCP-Server in Claude Code, Codex CLI und Antigravity zu installieren/entfernen.

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
Trage Folgendes in `mcp_config.json` ein:
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

#### Antigravity (`mcp_config.json`)
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

## Credits
- **Originalidee:** Andrej Karpathy — [karpathy/llm-council](https://github.com/karpathy/llm-council)
- **Prompt-/Workflow-Vorlage:** Portiert aus [DmitryBMsk/llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus)
- **Dieser MCP-Server:** Alexander Deja — [anderzlabs.de](https://www.anderzlabs.de/)
