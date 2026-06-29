#!/usr/bin/env python3
"""
setup_ui.py

Lokale Einrichtungs-/Settings-Oberfläche für den llm_council MCP-Server.

Läuft NUR auf Anfrage (python3 setup_ui.py), bindet ausschließlich an
127.0.0.1 und ist kein Hintergrunddienst - schließe das Browser-Tab und
drücke Strg+C im Terminal, wenn du fertig bist. Der eigentliche MCP-Server
(server.py) läuft davon komplett unabhängig: er wird von Claude Code /
Codex / Antigravity selbst on-demand als Subprozess gestartet.

Diese UI macht zwei Dinge:
  1. Council-Modelle, Chairman-Modell und OpenRouter-Key in die .env
     schreiben (statt die Datei von Hand zu editieren).
  2. Den MCP-Server in Claude Code / Codex / Antigravity per Knopfdruck
     registrieren oder wieder entfernen (siehe installer.py für die
     Details pro Tool).
"""

import secrets
import sys
import threading
import webbrowser
import time
from pathlib import Path
from typing import Optional
import httpx

from flask import Flask, redirect, render_template_string, request, url_for, flash, session

import council_core
import installer
import council_settings
from _version import __version__ as current_version

_pypi_cache = {
    "version": None,
    "expires_at": 0.0
}

def get_latest_pypi_version() -> Optional[str]:
    global _pypi_cache
    now = time.time()
    if _pypi_cache["version"] is not None and now < _pypi_cache["expires_at"]:
        return _pypi_cache["version"]
        
    try:
        resp = httpx.get("https://pypi.org/pypi/llm-council-mcp-server/json", timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            version = data.get("info", {}).get("version")
            if version:
                _pypi_cache["version"] = version
                _pypi_cache["expires_at"] = now + 3600.0  # cache 1 hour
                return version
    except Exception as e:
        print(f"Error checking PyPI version: {e}", file=sys.stderr)
        
    return None

HOST = "127.0.0.1"
PORT = 5151


def _is_port_in_use(host: str, port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0


def _is_our_ui(host: str, port: int) -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/__ping__", timeout=0.5) as response:
            if response.status == 200:
                return response.read().decode("utf-8").strip() == "llm-council"
    except Exception:
        pass
    return False


def resolve_ui_target(host: str = HOST, base_port: int = PORT):
    """Decide how to bring up the Setup UI without colliding with an existing one.

    Returns (target_port, should_start, is_reuse):
      - port free            -> (base_port, True,  False)  start here
      - our UI already there -> (base_port, False, True)   reuse the running one
      - taken by other proc  -> (fallback,  True,  False)  start on 5152-5160
      - no port available    -> (None,      False, False)

    This is used by the *server-embedded* starter, which reuses an already
    running UI (and does not reopen a tab) so host restarts don't spam tabs.
    The standalone launcher does NOT use this — see main(): it always runs its
    own freshly-invoked version rather than deferring to a possibly stale one.
    """
    if not _is_port_in_use(host, base_port):
        return base_port, True, False
    if _is_our_ui(host, base_port):
        return base_port, False, True
    for fallback_port in range(base_port + 1, base_port + 10):
        if not _is_port_in_use(host, fallback_port):
            return fallback_port, True, False
    return None, False, False


def _is_newer(latest: Optional[str], current: str) -> bool:
    if not latest:
        return False

    def parse(v: str):
        return tuple(int(x) for x in v.split(".") if x.isdigit())

    try:
        return parse(latest) > parse(current)
    except Exception:
        return False

TRANSLATIONS = {
    "de": {
        "title": "LLM Council - Einrichtung",
        "header": "LLM Council - lokale Einrichtung",
        "hint_local": "Läuft nur auf 127.0.0.1, solange dieses Skript aktiv ist. Mit Strg+C im Terminal beenden, wenn fertig.",
        "h2_models": "OpenRouter & Modelle",
        "label_api_key": "OpenRouter API Key",
        "placeholder_api_key": "aktuell gesetzt - leer lassen für unverändert",
        "hint_api_key": "Wird nur lokal gespeichert, verlässt diesen Rechner nie.",
        "presets_load": "Presets laden:",
        "preset_fast": "⚡ Schnell-Setup",
        "preset_hardcore": "🔥 Deep Review",
        "label_selected_models": "Gewählte Modelle",
        "hint_selected_models": "Wähle bis zu 5 Modelle. (Hinweis: Jedes zusätzliche Modell erhöht die Kosten und Latenz in Stage 2 spürbar!)",
        "warning_selected_models": "Hinweis: Bei mehr als 3 Council-Modellen steigen API-Kosten und Latenz in Stage 2 spürbar an.",
        "label_council_models": "Council-Modelle",
        "search_models": "Modelle durchsuchen...",
        "search_chairman": "Chairman durchsuchen...",
        "label_chairman_model": "Chairman-Modell",
        "hint_chairman_model": "Wähle das finale Entscheidungsmodell (unabhängig vom Rat).",
        "pro_mode": "Profi-Modus (Temperatur & Tokens)",
        "label_stage1_temp": "Stage 1 Temperatur (Default: 0.5)",
        "label_stage2_temp": "Stage 2 Temperatur (Default: 0.3)",
        "label_stage3_temp": "Stage 3 Temperatur (Default: 0.4)",
        "label_max_tokens": "Max Tokens (Default: 8192)",
        "btn_reset_pro": "Profi-Einstellungen zurücksetzen",
        "btn_save": "Speichern",
        "label_open_ui_on_start": "Setup-UI beim Server-Start automatisch im Browser öffnen",
        "h2_tools": "Aktivierte MCP-Tools",
        "label_expose_internal_council": "Internes Council aktivieren (ask_internal_council - Light, kostenlos)",
        "label_expose_council": "Echtes Council aktivieren (ask_council - Multi-Modell, OpenRouter)",
        "hint_expose_tools": "Deaktivierte Tools werden dem MCP-Host nicht angeboten. Änderungen werden erst nach einem Neustart des Host-Agents aktiv.",
        "warning_diversity_internal": "Achtung: Beim internen Council ist die Diversität eingeschränkt, da alle 5 Sichtweisen von einem einzigen Modell (deinem Host-Abo) stammen. Für echte Modell-Diversität bitte ask_council nutzen.",
        "h2_installation": "Installation pro Tool",
        "status_installed": "✓ installiert",
        "status_not_installed": "– nicht installiert",
        "btn_install": "Installieren",
        "btn_update": "Aktualisieren",
        "btn_reinstall": "Neu eintragen",
        "btn_remove": "Entfernen",
        "hint_paths": "Antigravity/Codex-Pfade sind Vermutungen basierend auf der aktuellen Doku und können je Version abweichen - im Feld oben jederzeit anpassbar.",
        "flash_saved": "Einstellungen gespeichert.",
        "flash_reset": "Profi-Einstellungen wurden zurückgesetzt.",
        "flash_unknown_tool": "Unbekanntes Tool: {tool}",
        "footer_created_by": "Erstellt von",
        "installer_claude_not_installed": "claude-Kommando nicht im PATH gefunden. Ist Claude Code installiert?",
        "installer_claude_not_found": "claude-Kommando nicht im PATH gefunden.",
        "installer_uvx_not_found": "uvx nicht gefunden im PATH",
        "installer_path_info": "{detail}",
        "installer_check_error": "Fehler beim Prüfen: {detail}",
        "installer_config_not_found": "Keine Config gefunden unter {detail}",
        "installer_toml_libs_missing": "{detail}",
        "installer_install_success_claude": "Erfolgreich registriert: {detail}",
        "installer_install_failed_claude": "Registrierung fehlgeschlagen: {detail}",
        "installer_install_success_file": "Eingetragen in {detail} (atomar)",
        "installer_install_error": "Fehler beim Installieren: {detail}",
        "installer_uninstall_success_claude": "Erfolgreich entfernt: {detail}",
        "installer_uninstall_failed_claude": "Entfernen fehlgeschlagen: {detail}",
        "installer_uninstall_success_file": "Entfernt aus {detail} (atomar)",
        "installer_no_config_to_remove": "Keine Config unter {detail} - nichts zu entfernen.",
        "installer_not_registered": "War nicht eingetragen in {detail}",
        "installer_uninstall_error": "Fehler beim Entfernen: {detail}",
        "update_title": "Update verfügbar!",
        "update_body": "Eine neuere Version ({latest}) ist auf PyPI verfügbar (installiert: {installed}). So aktualisierst du: 1) den folgenden Befehl im Terminal ausführen (öffnet die aktualisierte Setup-UI, ggf. auf einem anderen Port), 2) dort pro Host auf 'Installieren' klicken, 3) den Host neu starten. Erst nach dem Host-Neustart verschwindet dieser Hinweis – bloßes Neuladen der Seite genügt nicht:",
        "hosts_stale_title": "Aktualisierung noch nicht abgeschlossen",
        "hosts_stale_body": "Folgende Host(s) laufen noch auf einer älteren Version (Ziel: {target}). Klicke unten pro Host auf „Aktualisieren\" und starte den jeweiligen Host danach neu:",
        "restart_title": "🔄 Neustart nötig:",
        "restart_hints": {
            "claude": "Starte eine neue Claude-Code-Session, damit der MCP-Server mit der neuen Version geladen wird (laufende Sessions nutzen weiter die alte).",
            "codex": "Starte deine Codex-Session neu (Terminal/App), damit der MCP-Server mit der neuen Version geladen wird.",
            "antigravity": "Beende Antigravity vollständig und öffne es neu, damit der MCP-Server mit der neuen Version geladen wird.",
        },
    },
    "en": {
        "title": "LLM Council - Setup",
        "header": "LLM Council - Local Setup",
        "hint_local": "Runs only on 127.0.0.1 while this script is active. Press Ctrl+C in terminal to stop when done.",
        "h2_models": "OpenRouter & Models",
        "label_api_key": "OpenRouter API Key",
        "placeholder_api_key": "currently set - leave empty for unchanged",
        "hint_api_key": "Stored locally only, never leaves this machine.",
        "presets_load": "Load Presets:",
        "preset_fast": "⚡ Quick Setup",
        "preset_hardcore": "🔥 Deep Review",
        "label_selected_models": "Selected Models",
        "hint_selected_models": "Select up to 5 models. (Note: Each additional model increases Stage 2 cost and latency significantly!)",
        "warning_selected_models": "Note: With more than 3 council models, API costs and Stage 2 latency increase significantly.",
        "label_council_models": "Council Models",
        "search_models": "Search models...",
        "search_chairman": "Search Chairman...",
        "label_chairman_model": "Chairman Model",
        "hint_chairman_model": "Select the final decision-making model (independent of the council).",
        "pro_mode": "Pro-Mode (Temperature & Tokens)",
        "label_stage1_temp": "Stage 1 Temperature (Default: 0.5)",
        "label_stage2_temp": "Stage 2 Temperature (Default: 0.3)",
        "label_stage3_temp": "Stage 3 Temperature (Default: 0.4)",
        "label_max_tokens": "Max Tokens (Default: 8192)",
        "btn_reset_pro": "Reset Pro Settings",
        "btn_save": "Save",
        "label_open_ui_on_start": "Automatically open Setup UI in browser on server start",
        "h2_tools": "Exposed MCP Tools",
        "label_expose_internal_council": "Expose Internal Council (ask_internal_council - Light, free)",
        "label_expose_council": "Expose Real Council (ask_council - Multi-model, OpenRouter)",
        "hint_expose_tools": "Disabled tools are not exposed to the MCP host. Changes require a restart of the host agent to take effect.",
        "warning_diversity_internal": "Note: Diversity is limited in the internal council since all 5 perspectives are generated by a single model (your host subscription). Use ask_council for true multi-model diversity.",
        "h2_installation": "Installation per Tool",
        "status_installed": "✓ installed",
        "status_not_installed": "– not installed",
        "btn_install": "Install",
        "btn_update": "Update",
        "btn_reinstall": "Re-register",
        "btn_remove": "Remove",
        "hint_paths": "Antigravity/Codex paths are guesses based on current documentation and may vary per version - customizable in the field above.",
        "flash_saved": "Settings saved.",
        "flash_reset": "Pro settings reset.",
        "flash_unknown_tool": "Unknown tool: {tool}",
        "footer_created_by": "Created by",
        "installer_claude_not_installed": "claude command not found in PATH. Is Claude Code installed?",
        "installer_claude_not_found": "claude command not found in PATH.",
        "installer_uvx_not_found": "uvx not found in PATH",
        "installer_path_info": "{detail}",
        "installer_check_error": "Error during check: {detail}",
        "installer_config_not_found": "No config found at {detail}",
        "installer_toml_libs_missing": "{detail}",
        "installer_install_success_claude": "Successfully registered: {detail}",
        "installer_install_failed_claude": "Registration failed: {detail}",
        "installer_install_success_file": "Registered in {detail} (atomically)",
        "installer_install_error": "Error during installation: {detail}",
        "installer_uninstall_success_claude": "Successfully removed: {detail}",
        "installer_uninstall_failed_claude": "Removal failed: {detail}",
        "installer_uninstall_success_file": "Removed from {detail} (atomically)",
        "installer_no_config_to_remove": "No config at {detail} - nothing to remove.",
        "installer_not_registered": "Was not registered in {detail}",
        "installer_uninstall_error": "Error during removal: {detail}",
        "update_title": "Update Available!",
        "update_body": "A newer version ({latest}) is available on PyPI (installed: {installed}). To update: 1) run the following command in your terminal (it opens the updated setup UI, possibly on a different port), 2) click 'Install' for each host there, 3) restart the host. This notice only disappears after the host restart – reloading this page alone is not enough:",
        "hosts_stale_title": "Update not finished yet",
        "hosts_stale_body": "The following host(s) still run an older version (target: {target}). Click 'Update' for each host below, then restart that host:",
        "restart_title": "🔄 Restart required:",
        "restart_hints": {
            "claude": "Start a new Claude Code session so the MCP server loads the new version (running sessions keep using the old one).",
            "codex": "Restart your Codex session (terminal/app) so the MCP server loads the new version.",
            "antigravity": "Fully quit and reopen Antigravity so the MCP server loads the new version.",
        },
    }
}

BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = str(BASE_DIR / "server.py")
PYTHON_PATH = sys.executable  # same interpreter/venv running this UI

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # only needed for flash messages; no persistence required

@app.before_request
def protect_host():
    host = request.host.split(":")[0]
    if host not in ("127.0.0.1", "localhost"):
        return "Forbidden - DNS Rebinding Protection", 403


@app.route("/__ping__", methods=["GET"])
def ping():
    return "llm-council"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config_path_override(settings: dict, tool: str):
    key = f"{tool.lower()}_config_path"
    raw = settings.get(key, "").strip()
    return Path(raw) if raw else None


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

PAGE_TEMPLATE = """
<!doctype html>
<html lang="{{ lang }}">
<head>
<meta charset="utf-8">
<title>{{ t.title }}</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 760px; margin: 40px auto; color: #1a1a1a; line-height: 1.5; }
  h1 { font-size: 1.4em; }
  h2 { font-size: 1.1em; margin-top: 2em; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
  label { display: block; margin-top: 12px; font-weight: 600; font-size: 0.9em; }
  input[type=text], input[type=password] { width: 100%; padding: 6px 8px; margin-top: 4px; box-sizing: border-box; }
  .hint { color: #666; font-size: 0.85em; margin-top: 2px; }
  button { margin-top: 14px; padding: 6px 14px; cursor: pointer; }
  .tool-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; gap: 12px; }
  .tool-name { font-weight: 600; min-width: 140px; }
  .status-ok { color: #1a7f37; }
  .status-missing { color: #999; }
  .detail { font-size: 0.8em; color: #777; flex: 1; }
  .flash { background: #eef; border: 1px solid #99c; padding: 8px 12px; margin-bottom: 16px; border-radius: 4px; }
  .flash.error { background: #fee; border-color: #c99; }
  .flash.restart { background: #e8f4ff; border: 1px solid #90caf9; color: #0d47a1; font-weight: 500; }
  button.btn-update { background: #fff4e0; border-color: #ffb74d; color: #b76e00; font-weight: 600; }
  .ui-version { font-size: 0.45em; color: #999; font-weight: normal; vertical-align: middle; }
  form.inline { display: inline; }
  .path-override { width: 220px; font-size: 0.8em; }
  .chairman-chip { display: inline-block; background: #d0e0ff; border-radius: 16px; padding: 4px 10px; margin: 4px 4px 4px 0; font-size: 0.85em; border: 1px solid #aac; }
  .chip { display: inline-block; background: #e0e0e0; border-radius: 16px; padding: 4px 10px; margin: 4px 4px 4px 0; font-size: 0.85em; }
  .chip-remove { cursor: pointer; font-weight: bold; margin-left: 6px; color: #666; }
  .search-bar { width: 100%; padding: 6px; margin-bottom: 10px; box-sizing: border-box; }
  .warning { color: #a87b00; font-size: 0.85em; display: none; margin-bottom: 8px; }
  .model-item { display: block; }
</style>
</head>
<body>

<div style="display: flex; justify-content: flex-end; gap: 10px; font-size: 0.9em; margin-bottom: 20px;">
  <a href="{{ url_for('change_lang', lang='de') }}" style="text-decoration: {{ 'underline' if lang == 'de' else 'none' }}; color: #333; font-weight: {{ 'bold' if lang == 'de' else 'normal' }};">Deutsch</a> |
  <a href="{{ url_for('change_lang', lang='en') }}" style="text-decoration: {{ 'underline' if lang == 'en' else 'none' }}; color: #333; font-weight: {{ 'bold' if lang == 'en' else 'normal' }};">English</a>
</div>

{% if update_available %}
  <div class="flash" style="background: #fff9e6; border: 1px solid #ffe0b2; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px; color: #b78103;">
    <strong style="font-size: 1.1em;">💡 {{ t.update_title }}</strong>
    <p style="margin: 6px 0 10px 0; font-size: 0.9em;">
      {{ t.update_body.format(installed=current_version, latest=latest_version) }}
    </p>
    <code style="display: block; background: #fffde6; border: 1px solid #ffd54f; padding: 8px 12px; font-family: monospace; font-size: 0.9em; border-radius: 4px; color: #5d4037; overflow-x: auto; white-space: pre-wrap; word-break: break-all;">uvx --refresh --from llm-council-mcp-server llm-council-setup</code>
  </div>
{% endif %}

{% if stale_hosts %}
  <div class="flash" style="background: #fff4e0; border: 1px solid #ffb74d; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px; color: #b76e00;">
    <strong style="font-size: 1.1em;">⚠️ {{ t.hosts_stale_title }}</strong>
    <p style="margin: 6px 0 0 0; font-size: 0.9em;">
      {{ t.hosts_stale_body.format(target=target_version) }}
      {% for h in stale_hosts %}<br>· {{ h.label }} (@{{ h.pinned }}){% endfor %}
    </p>
  </div>
{% endif %}

<h1>{{ t.header }} <span class="ui-version">Setup-UI v{{ current_version }}</span></h1>
<p class="hint">{{ t.hint_local }}</p>

{% for category, message in get_flashed_messages(with_categories=true) %}
  <div class="flash {{ category }}">{{ message }}</div>
{% endfor %}

<h2>{{ t.h2_models }}</h2>
<form method="post" action="{{ url_for('save_settings') }}">
  <label>{{ t.label_api_key }}</label>
  <input type="password" name="api_key" placeholder="{{ t.placeholder_api_key if has_key else 'sk-or-...' }}">
  <div class="hint">{{ t.hint_api_key }}</div>

  
  <div style="margin-bottom: 15px; padding: 10px; background: #eef; border-radius: 6px; border: 1px solid #ccd;">
    <strong>{{ t.presets_load }}</strong><br>
    <button type="button" id="btn-preset-fast" style="margin-right: 10px; background: #fff;">{{ t.preset_fast }}</button>
    <button type="button" id="btn-preset-hardcore" style="background: #fff;">{{ t.preset_hardcore }}</button>
  </div>

  <label>{{ t.label_selected_models }}</label>
  <div class="hint">{{ t.hint_selected_models }}</div>
  <div id="selected-chips" style="margin-bottom: 10px;"></div>
  <div id="model-warning" class="warning">{{ t.warning_selected_models }}</div>

  <label style="margin-top: 20px;">{{ t.label_council_models }}</label>
  {% if recommended_models or other_models %}
    <div style="border: 1px solid #ccc; padding: 5px; margin-bottom: 1rem;">
      <input type="text" id="modelSearch" class="search-bar" placeholder="{{ t.search_models }}">
      <div id="modelList" style="max-height: 250px; overflow-y: auto;">
        {% if other_models %}
          {% for m in other_models %}
            <div class="model-item">
              <input type="checkbox" name="council_models" value="{{ m.id }}" id="cm_oth_{{ loop.index }}" {{ 'checked' if m.id in settings.get('council_models', []) else '' }}>
              <label for="cm_oth_{{ loop.index }}" style="display:inline; font-weight:normal; margin-left: 5px;">{{ m.name }} ({{ m.id }})</label>
            </div>
          {% endfor %}
        {% endif %}
      </div>
    </div>
  {% else %}
    <input type="text" name="council_models" value="{{ ','.join(settings.get('council_models', [])) }}">
  {% endif %}

  <label>{{ t.label_chairman_model }}</label>
  <div class="hint">{{ t.hint_chairman_model }}</div>
  {% if recommended_models or other_models %}
    <div style="border: 1px solid #ccc; padding: 5px; margin-bottom: 1rem;">
      <input type="text" id="chairmanSearch" class="search-bar" placeholder="{{ t.search_chairman }}">
      <div id="chairmanList" style="max-height: 250px; overflow-y: auto;">
        {% if other_models %}
          {% for m in other_models %}
            <div class="chairman-item">
              <input type="radio" name="chairman_model" value="{{ m.id }}" id="ch_oth_{{ loop.index }}" {{ 'checked' if m.id == settings.get('chairman_model', '') else '' }}>
              <label for="ch_oth_{{ loop.index }}" style="display:inline; font-weight:normal; margin-left: 5px;">{{ m.name }} ({{ m.id }})</label>
            </div>
          {% endfor %}
        {% endif %}
      </div>
    </div>
  {% else %}
    <input type="text" name="chairman_model" value="{{ settings.get('chairman_model', '') }}">
  {% endif %}

  <details style="margin-bottom: 1rem; padding: 10px; border: 1px solid #ccc; background: #f9f9f9;">
    <summary style="font-weight: 600; cursor: pointer;">{{ t.pro_mode }}</summary>
    <label>{{ t.label_stage1_temp }}</label>
    <input type="text" name="stage1_temperature" value="{{ settings.get('stage1_temperature', '') }}">
    <label>{{ t.label_stage2_temp }}</label>
    <input type="text" name="stage2_temperature" value="{{ settings.get('stage2_temperature', '') }}">
    <label>{{ t.label_stage3_temp }}</label>
    <input type="text" name="stage3_temperature" value="{{ settings.get('stage3_temperature', '') }}">
    <label>{{ t.label_max_tokens }}</label>
    <input type="text" name="max_tokens" value="{{ settings.get('max_tokens', '') }}">
    <div style="margin-top: 10px;">
        <button type="submit" formaction="{{ url_for('reset_pro') }}" style="background: #fee; border: 1px solid #c99; color: #a33;">{{ t.btn_reset_pro }}</button>
    </div>
  </details>

  <h2>{{ t.h2_tools }}</h2>
  <div class="hint" style="margin-bottom: 10px;">{{ t.hint_expose_tools }}</div>
  <div style="margin-bottom: 10px;">
    <label style="display: inline-block; font-weight: normal; margin-top: 0;">
      <input type="checkbox" name="expose_internal_council" value="true" {{ 'checked' if settings.get('expose_internal_council', True) else '' }} id="chk_expose_internal">
      {{ t.label_expose_internal_council }}
    </label>
    <div id="diversity-warn" class="hint" style="margin-left: 20px; color: #b76e00; background: #fff8e1; border-left: 3px solid #ffb74d; padding: 6px 10px; border-radius: 2px; margin-top: 4px; display: none;">
      ⚠️ {{ t.warning_diversity_internal }}
    </div>
  </div>
  <div style="margin-bottom: 20px;">
    <label style="display: inline-block; font-weight: normal; margin-top: 0;">
      <input type="checkbox" name="expose_council" value="true" {{ 'checked' if settings.get('expose_council', True) else '' }}>
      {{ t.label_expose_council }}
    </label>
  </div>

  <div style="margin-top: 15px; margin-bottom: 10px;">
    <label style="display: inline-block; font-weight: normal; margin-top: 0;">
      <input type="checkbox" name="open_ui_on_start" value="true" {{ 'checked' if settings.get('open_ui_on_start', True) else '' }}>
      {{ t.label_open_ui_on_start }}
    </label>
  </div>

  <button type="submit">{{ t.btn_save }}</button>
</form>

<h2>{{ t.h2_installation }}</h2>
{% for tool in tools %}
  <div class="tool-row">
    <span class="tool-name">{{ tool.label }}</span>
    <span class="{{ 'status-ok' if tool.installed else 'status-missing' }}">
      {{ t.status_installed if tool.installed else t.status_not_installed }}{% if tool.installed and tool.pinned %} (@{{ tool.pinned }}){% endif %}
    </span>
    <span class="detail">{{ tool.detail }}</span>
    <span>
      <form class="inline" method="post" action="{{ url_for('do_install', tool=tool.key) }}">
        {% if tool.needs_path_override %}
          <input class="path-override" type="text" name="config_path" value="{{ tool.path_value }}">
        {% endif %}
        <button type="submit"{% if tool.needs_update %} class="btn-update"{% endif %}>{% if not tool.installed %}{{ t.btn_install }}{% elif tool.needs_update %}{{ t.btn_update }}{% else %}{{ t.btn_reinstall }}{% endif %}</button>
      </form>
      <form class="inline" method="post" action="{{ url_for('do_uninstall', tool=tool.key) }}">
        {% if tool.needs_path_override %}
          <input type="hidden" name="config_path" value="{{ tool.path_value }}">
        {% endif %}
        <button type="submit">{{ t.btn_remove }}</button>
      </form>
    </span>
  </div>
{% endfor %}

<p class="hint">{{ t.hint_paths }}</p>


<script>
document.addEventListener('DOMContentLoaded', () => {
    // Council Search
    const searchInput = document.getElementById('modelSearch');
    const items = document.querySelectorAll('.model-item');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(term) ? 'block' : 'none';
            });
        });
    }

    // Chairman Search
    const chSearch = document.getElementById('chairmanSearch');
    const chItems = document.querySelectorAll('.chairman-item');
    if (chSearch) {
        chSearch.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            chItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(term) ? 'block' : 'none';
            });
        });
    }

    // Chips & Limits
    const checkboxes = document.querySelectorAll('input[name="council_models"]');
    const chipsContainer = document.getElementById('selected-chips');
    const warning = document.getElementById('model-warning');

    
    // Presets
    const PRESET_FAST = [
        "anthropic/claude-haiku-4.5",
        "google/gemini-3.1-flash-lite",
        "openai/gpt-5-nano",
        "deepseek/deepseek-v4-flash",
        "qwen/qwen3.6-flash"
    ];
    const CHAIRMAN_FAST = "anthropic/claude-opus-4.6";

    const PRESET_HARDCORE = [
        "anthropic/claude-opus-4.8",
        "deepseek/deepseek-v4-pro",
        "google/gemini-3.1-pro-preview",
        "openai/gpt-5.3-codex",
        "z-ai/glm-5.2"
    ];
    const CHAIRMAN_HARDCORE = "openai/gpt-5.5";

    
    function applyPreset(councilList, chairmanId) {
        // Uncheck all
        document.querySelectorAll('input[name="council_models"]').forEach(cb => cb.checked = false);
        document.querySelectorAll('input[name="chairman_model"]').forEach(rb => rb.checked = false);

        // Check council
        councilList.forEach(id => {
            const cb = document.querySelector(`input[name="council_models"][value="${id}"]`);
            if (cb) cb.checked = true;
        });

        // Check chairman
        const rb = document.querySelector(`input[name="chairman_model"][value="${chairmanId}"]`);
        if (rb) rb.checked = true;

        updateChips();
    }

    const btnFast = document.getElementById('btn-preset-fast');
    if (btnFast) btnFast.addEventListener('click', () => applyPreset(PRESET_FAST, CHAIRMAN_FAST));

    const btnHardcore = document.getElementById('btn-preset-hardcore');
    if (btnHardcore) btnHardcore.addEventListener('click', () => applyPreset(PRESET_HARDCORE, CHAIRMAN_HARDCORE));

    function updateChips() {
        if(!chipsContainer) return;
        chipsContainer.innerHTML = '';
        let count = 0;
        
        // Chairman Chip first
        const chairmanRadios = document.querySelectorAll('input[name="chairman_model"]');
        chairmanRadios.forEach(rb => {
            if (rb.checked) {
                const chip = document.createElement('span');
                chip.className = 'chairman-chip';
                chip.innerHTML = '👑 ' + rb.nextElementSibling.textContent;
                chipsContainer.appendChild(chip);
            }
        });

        // Council Chips
        checkboxes.forEach(cb => {
            if (cb.checked) {
                count++;
                const chip = document.createElement('span');
                chip.className = 'chip';
                chip.textContent = cb.nextElementSibling.textContent;
                
                const remove = document.createElement('span');
                remove.className = 'chip-remove';
                remove.textContent = '×';
                remove.onclick = () => { cb.checked = false; updateChips(); };
                
                chip.appendChild(remove);
                chipsContainer.appendChild(chip);
            }
        });
        
        if(warning) warning.style.display = (count > 3) ? 'block' : 'none';
    }

    // Also update chips when chairman changes
    document.querySelectorAll('input[name="chairman_model"]').forEach(rb => rb.addEventListener('change', updateChips));
    checkboxes.forEach(cb => cb.addEventListener('change', updateChips));
    if (chipsContainer) updateChips();
    // Diversity Warn for Light Council
    const chkInternal = document.getElementById('chk_expose_internal');
    const divWarn = document.getElementById('diversity-warn');
    if (chkInternal && divWarn) {
        const toggleWarn = () => {
            divWarn.style.display = chkInternal.checked ? 'block' : 'none';
        };
        chkInternal.addEventListener('change', toggleWarn);
        toggleWarn();
    }
});
</script>

<footer style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #ddd;
               color: #777; font-size: 0.85em; text-align: center;">
  {{ t.footer_created_by }} <strong>Alexander Deja</strong> ·
  <a href="https://www.anderzlabs.de/" target="_blank" rel="noopener noreferrer">anderzlabs.de</a>
</footer>
</body>

</html>
"""


@app.route("/change_lang/<lang>", methods=["GET"])
def change_lang(lang):
    if lang in ("de", "en"):
        settings = council_settings.load_settings()
        settings["ui_language"] = lang
        council_settings.save_settings(settings)
    return redirect(url_for("index"))


@app.route("/", methods=["GET"])
def index():
    settings = council_settings.load_settings()
    lang = settings.get("ui_language")
    if not lang:
        lang = request.accept_languages.best_match(["de", "en"]) or "de"
    t = TRANSLATIONS[lang]
    
    latest_version = get_latest_pypi_version()
    update_available = _is_newer(latest_version, current_version)
    # The version that clicking "Install" would write — same rule as do_install.
    target_version = latest_version if update_available else current_version

    api_key = settings.get("openrouter_api_key", "")
    recommended_models = []
    other_models = []
    import httpx
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        resp = httpx.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            for m in data:
                m_dict = {"id": m["id"], "name": m.get("name", m["id"])}
                other_models.append(m_dict)
            other_models.sort(key=lambda x: x["id"])
    except Exception as e:
        print(f"Fehler beim Laden der Modelle: {e}", file=sys.stderr)
            
    tools = []
    for tool_key in installer.TOOLS:
        spec = installer.TOOLS[tool_key]
        override = _config_path_override(settings, tool_key)
        installed, key, detail = spec["is_installed"](config_path=override)
        translated_detail = TRANSLATIONS[lang].get(f"installer_{key}", "{detail}").format(detail=detail)
        pinned = None
        if installed and "pinned_version" in spec:
            try:
                pinned = spec["pinned_version"](config_path=override)
            except Exception:
                pinned = None
        needs_update = bool(installed and pinned and pinned != target_version)
        tools.append({
            "key": tool_key,
            "label": spec["label"],
            "installed": installed,
            "detail": translated_detail,
            "pinned": pinned,
            "needs_update": needs_update,
            "needs_path_override": spec["needs_path_override"],
            "path_value": str(override) if override else spec.get("default_path", ""),
        })

    stale_hosts = [
        {"label": tool["label"], "pinned": tool["pinned"]}
        for tool in tools
        if tool["needs_update"]
    ]

    return render_template_string(
        PAGE_TEMPLATE,
        settings=settings,
        has_key=bool(settings.get("openrouter_api_key")),
        tools=tools,
        recommended_models=recommended_models,
        other_models=other_models,
        t=t,
        lang=lang,
        update_available=update_available,
        current_version=current_version,
        latest_version=latest_version or "",
        target_version=target_version,
        stale_hosts=stale_hosts,
    )


@app.route("/save_settings", methods=["POST"])
def save_settings():
    settings = council_settings.load_settings()

    new_key = request.form.get("api_key", "").strip()
    if new_key:
        settings["openrouter_api_key"] = new_key

    council_models_list = request.form.getlist("council_models")
    if council_models_list:
        if len(council_models_list) == 1 and "," in council_models_list[0]:
            settings["council_models"] = [m.strip() for m in council_models_list[0].split(",") if m.strip()]
        else:
            settings["council_models"] = [m.strip() for m in council_models_list if m.strip()]

    chairman_model = request.form.get("chairman_model", "").strip()
    if chairman_model:
        settings["chairman_model"] = chairman_model

    # Advanced Settings
    for key in ["stage1_temperature", "stage2_temperature", "stage3_temperature", "max_tokens"]:
        val = request.form.get(key, "").strip()
        if val:
            settings[key] = val

    settings["open_ui_on_start"] = "open_ui_on_start" in request.form
    settings["expose_internal_council"] = "expose_internal_council" in request.form
    settings["expose_council"] = "expose_council" in request.form

    council_settings.save_settings(settings)
    lang = settings.get("ui_language") or request.accept_languages.best_match(["de", "en"]) or "de"
    t = TRANSLATIONS[lang]
    flash(t["flash_saved"], "ok")
    return redirect(url_for("index"))

@app.route("/reset_pro", methods=["POST"])
def reset_pro():
    settings = council_settings.load_settings()
    for key in ["stage1_temperature", "stage2_temperature", "stage3_temperature", "max_tokens"]:
        if key in settings:
            del settings[key]
    council_settings.save_settings(settings)
    lang = settings.get("ui_language") or request.accept_languages.best_match(["de", "en"]) or "de"
    t = TRANSLATIONS[lang]
    flash(t["flash_reset"], "ok")
    return redirect(url_for("index"))


@app.route("/install/<tool>", methods=["POST"])
def do_install(tool):
    settings = council_settings.load_settings()
    lang = settings.get("ui_language") or request.accept_languages.best_match(["de", "en"]) or "de"
    t = TRANSLATIONS[lang]
    if tool not in installer.TOOLS:
        flash(t["flash_unknown_tool"].format(tool=tool), "error")
        return redirect(url_for("index"))

    spec = installer.TOOLS[tool]
    config_path = None
    if spec["needs_path_override"]:
        raw = request.form.get("config_path", "").strip()
        config_path = Path(raw) if raw else None
        _persist_path_override(tool, raw)

    # Pin the newest available version, not the version of whatever UI process
    # happens to be running. Otherwise an outdated embedded UI would re-pin its
    # own old version and the user could never move forward (chicken-and-egg).
    latest_version = get_latest_pypi_version()
    target_version = latest_version if _is_newer(latest_version, current_version) else current_version

    ok, key, detail = spec["install"](config_path=config_path, version=target_version)
    translated_msg = TRANSLATIONS[lang].get(f"installer_{key}", "{detail}").format(detail=detail)
    flash(f"{spec['label']}: {translated_msg}", "ok" if ok else "error")
    if ok:
        restart_hint = t.get("restart_hints", {}).get(tool)
        if restart_hint:
            flash(f"{t['restart_title']} {restart_hint}", "restart")
    return redirect(url_for("index"))


@app.route("/uninstall/<tool>", methods=["POST"])
def do_uninstall(tool):
    settings = council_settings.load_settings()
    lang = settings.get("ui_language") or request.accept_languages.best_match(["de", "en"]) or "de"
    t = TRANSLATIONS[lang]
    if tool not in installer.TOOLS:
        flash(t["flash_unknown_tool"].format(tool=tool), "error")
        return redirect(url_for("index"))

    spec = installer.TOOLS[tool]
    config_path = None
    if spec["needs_path_override"]:
        raw = request.form.get("config_path", "").strip()
        config_path = Path(raw) if raw else None

    ok, key, detail = spec["uninstall"](config_path=config_path)
    translated_msg = TRANSLATIONS[lang].get(f"installer_{key}", "{detail}").format(detail=detail)
    flash(f"{spec['label']}: {translated_msg}", "ok" if ok else "error")
    return redirect(url_for("index"))


def _persist_path_override(tool: str, raw_path: str) -> None:
    settings = council_settings.load_settings()
    settings[f"{tool.lower()}_config_path"] = raw_path
    council_settings.save_settings(settings)


def _open_browser_later(port: int = PORT):
    webbrowser.open(f"http://{HOST}:{port}")


def main():
    # The user explicitly invoked this (possibly freshly --refresh'd) version,
    # so always run our OWN UI. Never defer to a UI that may already be running
    # on 5151 from an older embedded server — otherwise `uvx --refresh ...
    # llm-council-setup` would silently bounce the user to stale code (and they
    # would never reach the new Install/restart behaviour). Take 5151 if free,
    # else fall back to 5152-5160.
    target_port = None
    if not _is_port_in_use(HOST, PORT):
        target_port = PORT
    else:
        for fallback_port in range(PORT + 1, PORT + 10):
            if not _is_port_in_use(HOST, fallback_port):
                target_port = fallback_port
                break

    if target_port is None:
        print(
            f"Konnte keinen freien Port ({PORT}-{PORT + 9}) finden. "
            "Bitte den belegenden Prozess beenden und erneut starten.",
            file=sys.stderr,
        )
        return

    threading.Timer(1.0, _open_browser_later, args=(target_port,)).start()
    busy_note = "" if target_port == PORT else f" (Port {PORT} war belegt – nutze {target_port})"
    print(
        f"Setup-UI läuft auf http://{HOST}:{target_port} (nur lokal){busy_note}. Strg+C zum Beenden.",
        file=sys.stderr,
    )
    app.run(host=HOST, port=target_port, debug=False)

if __name__ == "__main__":
    main()
