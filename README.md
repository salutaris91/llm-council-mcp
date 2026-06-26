# LLM Council MCP

[English Version](#english-version) | [Deutsche Version](#deutsche-version)

---

# English Version

## Table of Contents
- [What it is (and how it works)](#what-it-is-and-how-it-works)
- [Installation & Setup](#installation--setup)
- [Quick Start / First Run](#-quick-start--first-run)
- [Setup UI & Settings Storage](#setup-ui--settings-storage)
- [Usage](#usage)
- [Tool Registration (Manual)](#tool-registration-manual-alternative-to-setup-ui)
- [Troubleshooting](#-troubleshooting)
- [Credits](#credits)

---

A lightweight, local MCP server for your Mac based on the original idea by Andrej Karpathy ([karpathy/llm-council](https://github.com/karpathy/llm-council)) with prompt/workflow templates ported from [DmitryBMsk/llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus). It replicates the 3-stage workflow using the **exact original prompts** directly against OpenRouter, without any Docker or NAS dependencies. Works with Claude Code, Codex CLI, and Antigravity via MCP.

## What it is (and how it works)

This tool replicates the AI deliberation process of the original project in three simple steps:

1. **Stage 1 (Answering):** Several AI models answer your question independently and at the same time.
2. **Stage 2 (Reviewing):** The models read all the answers without knowing who wrote which answer (blind review). Each model ranks the answers from best to worst to prevent self-bias.
3. **Stage 3 (Synthesis):** A final "Chairman" model reads all answers and reviews, and writes a single, balanced response for you. If the Chairman fails, another model automatically takes over.

The AI prompt instructions and settings are copied exactly from the original project to ensure the same high quality.

### What is currently left out (kept simple for now, but planned as optional features later):
- **Web Search / Internet Access in Stage 1:** Currently, models answer based on training and context. (Planned as an optional feature in a future release).
- **Editable Prompts / Custom Roles (e.g. Critic mode) in the UI:** Prompt templates are currently hardcoded for reliability. (Planned as an optional settings section).
- **Chat History & Interactive Discussion:** Currently designed for deep-dive single questions. (An optional discussion mode between Claude and the Chairman to decide which files are needed is planned).
- **Direct File Access:** The server does not read your workspace directly for security/simplicity. Your client (Claude Code, Antigravity) reads the files and passes them as parameters.

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

## Inhaltsverzeichnis
- [Was das ist (und wie es funktioniert)](#was-das-ist-und-wie-es-funktioniert)
- [Installation & Setup](#installation--setup-1)
- [Schnellstart / Erster Lauf](#-schnellstart--erster-lauf)
- [Setup-UI & Speicherort der Einstellungen](#setup-ui--speicherort-der-einstellungen)
- [Nutzung](#nutzung)
- [Tool-Registrierung (Manuell)](#tool-registrierung-manuell-alternativ-zur-setup-ui)
- [Fehlerbehebung](#-fehlerbehebung)
- [Credits](#credits-1)

---

Ein schlanker, lokaler MCP-Server für deinen Mac basierend auf der Originalidee von Andrej Karpathy ([karpathy/llm-council](https://github.com/karpathy/llm-council)) mit Prompt-/Workflow-Vorlagen portiert aus [DmitryBMsk/llm-council-plus](https://github.com/DmitryBMsk/llm-council-plus). Er bildet den 3-Stufen-Workflow mit den **exakten Original-Prompts** direkt gegen OpenRouter nach, ohne Docker- oder NAS-Abhängigkeit. Nutzbar aus Claude Code, Codex CLI und Antigravity über MCP.

## Was das ist (und wie es funktioniert)

Dieses Tool bildet den Entscheidungsprozess des Originalprojekts in drei einfachen Schritten ab:

1. **Stufe 1 (Antworten):** Mehrere KI-Modelle beantworten deine Frage gleichzeitig und unabhängig voneinander.
2. **Stufe 2 (Bewerten):** Die Modelle lesen alle Antworten, ohne zu wissen, welches Modell welche Antwort geschrieben hat (Blindverkostung). Jedes Modell bewertet die Antworten, um Eigenvoreingenommenheit zu verhindern.
3. **Stufe 3 (Zusammenfassen):** Ein finales "Chairman"-Modell liest alle Antworten und Bewertungen und verfasst eine ausgewogene Zusammenfassung für dich. Sollte das Chairman-Modell ausfallen, springt automatisch ein anderes Modell ein.

Die KI-Anweisungen (Prompts) und Einstellungen wurden exakt aus dem Originalprojekt übernommen, um die gleiche hohe Qualität der Antworten zu garantieren.

### Was aktuell bewusst weggelassen wurde (für maximale Einfachheit – später als optionale Funktionen geplant):
- **Web-Suche / Internetzugriff in Stufe 1:** Modelle antworten aktuell basierend auf ihrem Wissen und dem Kontext. (Als optionale Funktion für spätere Releases geplant).
- **Bearbeitbare Prompt-Vorlagen / Eigene Rollen (z. B. Kritiker-Modus) in der UI:** Prompt-Vorlagen sind für stabile Ergebnisse fest hinterlegt. (Als optionaler Einstellungsbereich geplant).
- **Chat-Verlauf & Interaktive Diskussion:** Aktuell für präzise Einzelanfragen konzipiert. (Ein optionaler Diskussionsmodus zwischen Client und Chairman zur gemeinschaftlichen Ermittlung benötigter Dateien ist geplant).
- **Direkter Dateizugriff:** Der Server liest deine Dateien aus Sicherheits- und Einfachheitsgründen nicht selbst. Dein Client (Claude Code, Antigravity) liest den Code aus und übergibt ihn automatisch.

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
