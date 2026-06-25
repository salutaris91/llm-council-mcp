import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import platformdirs

APP_NAME = "llm-council"

# Safe, currently-resolvable OpenRouter defaults; models are user-overridable
DEFAULT_COUNCIL_MODELS = [
    "openai/gpt-4o",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-1.5-pro",
]
DEFAULT_CHAIRMAN_MODEL = "google/gemini-1.5-pro"

# Default temperatures
DEFAULT_STAGE1_TEMPERATURE = 0.5
DEFAULT_STAGE2_TEMPERATURE = 0.3
DEFAULT_STAGE3_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 8192

# Global override set by server.py at startup (if passed via CLI)
_global_config_dir_override: Optional[str] = None

def set_config_dir_override(path: str) -> None:
    global _global_config_dir_override
    _global_config_dir_override = path

def get_config_dir() -> Path:
    if _global_config_dir_override:
        return Path(_global_config_dir_override)
    return Path(platformdirs.user_config_dir(APP_NAME))

def get_settings_file() -> Path:
    return get_config_dir() / "settings.json"

def _get_legacy_env_path() -> Path:
    # Path to the old .env file next to server.py
    return Path(__file__).resolve().parent / ".env"

def migrate_from_env_if_needed() -> None:
    settings_file = get_settings_file()
    if settings_file.exists():
        return
        
    env_path = _get_legacy_env_path()
    if not env_path.exists():
        return
        
    # Read rudimentary .env
    values: Dict[str, Any] = {
        "schema_version": 1,
    }
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        
        if key == "OPENROUTER_API_KEY":
            values["openrouter_api_key"] = value
        elif key == "COUNCIL_MODELS":
            values["council_models"] = [m.strip() for m in value.split(",") if m.strip()]
        elif key == "CHAIRMAN_MODEL":
            values["chairman_model"] = value
            
    # Save to new format if we found anything useful
    if "openrouter_api_key" in values:
        save_settings(values)

def load_settings() -> Dict[str, Any]:
    migrate_from_env_if_needed()
    settings_file = get_settings_file()
    if not settings_file.exists():
        return {}
    
    try:
        with open(settings_file, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(settings: Dict[str, Any]) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    
    settings_file = get_settings_file()
    settings["schema_version"] = settings.get("schema_version", 1)
    
    # Atomic write
    fd, tmp_path = tempfile.mkstemp(dir=config_dir, prefix=".settings.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(settings, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        # Enforce 0o600 before replacing
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, settings_file)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

