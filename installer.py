"""
installer.py

Install/uninstall/status logic for registering the llm_council MCP server
in Claude Code, Codex CLI, and Google Antigravity.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import platformdirs

import sys

try:
    if sys.version_info >= (3, 11):
        import tomllib as _toml_reader      # Stdlib-Reader ab 3.11
    else:
        import tomli as _toml_reader
except ModuleNotFoundError:
    _toml_reader = None

try:
    import tomli_w
except ModuleNotFoundError:
    tomli_w = None

SERVER_NAME = "llm-council"
APP_NAME = "llm-council"

DEFAULT_ANTIGRAVITY_CONFIG_PATH = Path.home() / ".gemini" / "config" / "mcp_config.json"
DEFAULT_CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"


def _get_uvx_path() -> Optional[str]:
    return shutil.which("uvx")

def _get_base_dir() -> Path:
    return Path(__file__).resolve().parent

def _get_real_config_dir() -> str:
    return platformdirs.user_config_dir(APP_NAME)

DEV_MODE = False

def get_uvx_args(uvx_path: str, base_dir: Path, real_config_dir: str) -> list[str]:
    if DEV_MODE:
        return [uvx_path, "-q", "--from", str(base_dir), "llm-council-mcp", f"--config-dir={real_config_dir}"]
    return [uvx_path, "-q", "--from", "llm-council-mcp-server@0.1.3", "llm-council-mcp", f"--config-dir={real_config_dir}"]


# ---------------------------------------------------------------------------
# Claude Code - via official CLI
# ---------------------------------------------------------------------------

def _claude_binary() -> Optional[str]:
    return shutil.which("claude")


def claude_is_installed() -> Tuple[bool, str, str]:
    binary = _claude_binary()
    if not binary:
        return False, "claude_not_installed", ""
    try:
        result = subprocess.run(
            [binary, "mcp", "list"], capture_output=True, text=True, timeout=15
        )
        installed = SERVER_NAME in result.stdout
        return installed, "path_info", result.stdout.strip()
    except Exception as e:  # noqa: BLE001
        return False, "check_error", str(e)


def claude_install() -> Tuple[bool, str, str]:
    binary = _claude_binary()
    if not binary:
        return False, "claude_not_found", ""
        
    uvx_path = _get_uvx_path()
    if not uvx_path:
        return False, "uvx_not_found", ""
        
    base_dir = _get_base_dir()
    real_config_dir = _get_real_config_dir()
    
    try:
        cmd = [binary, "mcp", "add", SERVER_NAME, "--scope", "user", "--"] + get_uvx_args(uvx_path, base_dir, real_config_dir)
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30,
        )
        ok = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        key = "install_success_claude" if ok else "install_failed_claude"
        return ok, key, output or ("OK" if ok else "Unbekannter Fehler")
    except Exception as e:  # noqa: BLE001
        return False, "install_error", str(e)


def claude_uninstall() -> Tuple[bool, str, str]:
    binary = _claude_binary()
    if not binary:
        return False, "claude_not_found", ""
    try:
        result = subprocess.run(
            [binary, "mcp", "remove", SERVER_NAME, "--scope", "user"],
            capture_output=True, text=True, timeout=30,
        )
        ok = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        key = "uninstall_success_claude" if ok else "uninstall_failed_claude"
        return ok, key, output or ("OK" if ok else "Unbekannter Fehler")
    except Exception as e:  # noqa: BLE001
        return False, "uninstall_error", str(e)


# ---------------------------------------------------------------------------
# Codex CLI - via direct config.toml edit
# ---------------------------------------------------------------------------

def _require_toml_libs() -> Optional[str]:
    if _toml_reader is None or tomli_w is None:
        return "tomli/tomli_w fehlen. Bitte 'pip install -r requirements.txt' im venv ausführen."
    return None


def codex_is_installed(config_path: Optional[Path] = None) -> Tuple[bool, str, str]:
    path = config_path or DEFAULT_CODEX_CONFIG_PATH
    if not path.exists():
        return False, "config_not_found", str(path)
    err = _require_toml_libs()
    if err:
        return False, "toml_libs_missing", err
    try:
        data = _toml_reader.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        return False, "check_error", str(e)
    installed = SERVER_NAME in data.get("mcp_servers", {})
    return installed, "path_info", str(path)


def codex_install(config_path: Optional[Path] = None) -> Tuple[bool, str, str]:
    path = config_path or DEFAULT_CODEX_CONFIG_PATH
    err = _require_toml_libs()
    if err:
        return False, "toml_libs_missing", err
        
    uvx_path = _get_uvx_path()
    if not uvx_path:
        return False, "uvx_not_found", ""
        
    base_dir = _get_base_dir()
    real_config_dir = _get_real_config_dir()
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _toml_reader.loads(path.read_text()) if path.exists() else {}
        data.setdefault("mcp_servers", {})
        args = get_uvx_args(uvx_path, base_dir, real_config_dir)
        data["mcp_servers"][SERVER_NAME] = {
            "command": args[0],
            "args": args[1:],
        }
        
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".config.", suffix=".tmp")
        with os.fdopen(fd, 'w') as f:
            f.write(tomli_w.dumps(data))
        os.replace(tmp_path, path)
        return True, "install_success_file", str(path)
    except Exception as e:  # noqa: BLE001
        return False, "install_error", str(e)


def codex_uninstall(config_path: Optional[Path] = None) -> Tuple[bool, str, str]:
    path = config_path or DEFAULT_CODEX_CONFIG_PATH
    if not path.exists():
        return True, "no_config_to_remove", str(path)
    err = _require_toml_libs()
    if err:
        return False, "toml_libs_missing", err
    try:
        data = _toml_reader.loads(path.read_text())
        if SERVER_NAME in data.get("mcp_servers", {}):
            del data["mcp_servers"][SERVER_NAME]
            fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".config.", suffix=".tmp")
            with os.fdopen(fd, 'w') as f:
                f.write(tomli_w.dumps(data))
            os.replace(tmp_path, path)
            return True, "uninstall_success_file", str(path)
        return True, "not_registered", str(path)
    except Exception as e:  # noqa: BLE001
        return False, "uninstall_error", str(e)


# ---------------------------------------------------------------------------
# Antigravity - via direct mcp_config.json edit
# ---------------------------------------------------------------------------

def antigravity_is_installed(config_path: Optional[Path] = None) -> Tuple[bool, str, str]:
    path = config_path or DEFAULT_ANTIGRAVITY_CONFIG_PATH
    if not path.exists():
        return False, "config_not_found", str(path)
    try:
        data = json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        return False, "check_error", str(e)
    installed = SERVER_NAME in data.get("mcpServers", {})
    return installed, "path_info", str(path)


def antigravity_install(config_path: Optional[Path] = None) -> Tuple[bool, str, str]:
    path = config_path or DEFAULT_ANTIGRAVITY_CONFIG_PATH
    
    uvx_path = _get_uvx_path()
    if not uvx_path:
        return False, "uvx_not_found", ""
        
    base_dir = _get_base_dir()
    real_config_dir = _get_real_config_dir()
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(path.read_text()) if path.exists() else {}
        data.setdefault("mcpServers", {})
        
        # Cleanup stale spike
        if "llm-council-spike" in data["mcpServers"]:
            del data["mcpServers"]["llm-council-spike"]
            
        args = get_uvx_args(uvx_path, base_dir, real_config_dir)
        data["mcpServers"][SERVER_NAME] = {
            "command": args[0],
            "args": args[1:]
        }
        
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".mcp_config.", suffix=".tmp")
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
        
        return True, "install_success_file", str(path)
    except Exception as e:  # noqa: BLE001
        return False, "install_error", str(e)


def antigravity_uninstall(config_path: Optional[Path] = None) -> Tuple[bool, str, str]:
    path = config_path or DEFAULT_ANTIGRAVITY_CONFIG_PATH
    if not path.exists():
        return True, "no_config_to_remove", str(path)
    try:
        data = json.loads(path.read_text())
        modified = False
        if SERVER_NAME in data.get("mcpServers", {}):
            del data["mcpServers"][SERVER_NAME]
            modified = True
        if "llm-council-spike" in data.get("mcpServers", {}):
            del data["mcpServers"]["llm-council-spike"]
            modified = True
            
        if modified:
            fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".mcp_config.", suffix=".tmp")
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, path)
            return True, "uninstall_success_file", str(path)
            
        return True, "not_registered", str(path)
    except Exception as e:  # noqa: BLE001
        return False, "uninstall_error", str(e)


TOOLS = {
    "claude": {
        "label": "Claude Code",
        "is_installed": lambda **kw: claude_is_installed(),
        "install": lambda **kw: claude_install(),
        "uninstall": lambda **kw: claude_uninstall(),
        "needs_path_override": False,
    },
    "codex": {
        "label": "Codex CLI",
        "is_installed": lambda config_path=None, **kw: codex_is_installed(config_path),
        "install": lambda config_path=None, **kw: codex_install(config_path),
        "uninstall": lambda config_path=None, **kw: codex_uninstall(config_path),
        "needs_path_override": True,
        "default_path": str(DEFAULT_CODEX_CONFIG_PATH),
    },
    "antigravity": {
        "label": "Antigravity",
        "is_installed": lambda config_path=None, **kw: antigravity_is_installed(config_path),
        "install": lambda config_path=None, **kw: antigravity_install(config_path),
        "uninstall": lambda config_path=None, **kw: antigravity_uninstall(config_path),
        "needs_path_override": True,
        "default_path": str(DEFAULT_ANTIGRAVITY_CONFIG_PATH),
    },
}
