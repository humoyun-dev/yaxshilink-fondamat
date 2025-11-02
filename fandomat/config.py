from __future__ import annotations

import json
from pathlib import Path
from .state import print_lock
import logging

log = logging.getLogger("fandomat")

CONFIG_PATH = Path("config.json")
DEFAULT_WS_URL = "wss://api.yaxshi.link/ws/fandomats"
DEFAULT_FANDOMAT_ID = 4
DEFAULT_DEVICE_TOKEN = "LJE-rsXEIQuhFifL_F7DbEZ5VCofU_0cR9bb1fQ1S88"


def load_existing_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def update_config(patch: dict) -> dict:
    """Merge and persist config values into config.json, returning the new config."""
    cfg = load_existing_config()
    cfg.update(patch)
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"Updated configuration at {CONFIG_PATH.resolve()}")
    except Exception as e:
        log.error(f"Failed to update {CONFIG_PATH}: {e}")
    return cfg


def _mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 8:
        return "*" * len(token)
    return f"{token[:4]}...{token[-4:]}"


def ensure_server_config_interactive() -> dict:
    """Prompt for WS_URL, FANDOMAT_ID, DEVICE_TOKEN and save to config.json."""
    existing = load_existing_config()

    def ask_str(prompt: str, default: str) -> str:
        s = input(f"{prompt} [{default}]: ").strip()
        return s or default

    def ask_int(prompt: str, default: int) -> int:
        while True:
            s = input(f"{prompt} [{default}]: ").strip()
            if not s:
                return default
            try:
                return int(s)
            except ValueError:
                print("Please enter a valid integer.")

    ws_url_default = existing.get("WS_URL", DEFAULT_WS_URL)
    fandomat_default = int(existing.get("FANDOMAT_ID", DEFAULT_FANDOMAT_ID))
    token_default = existing.get("DEVICE_TOKEN", DEFAULT_DEVICE_TOKEN)

    while True:
        ws_url = ask_str("WS_URL (WebSocket URL)", ws_url_default)
        if ws_url.startswith("ws://") or ws_url.startswith("wss://"):
            break
        print("URL must start with ws:// or wss://")

    fandomat_id = ask_int("FANDOMAT_ID (integer)", fandomat_default)

    token_prompt_default = _mask_token(token_default) if token_default else ""
    token_in = input(f"DEVICE_TOKEN [{token_prompt_default}]: ").strip()
    device_token = token_in or token_default

    data = {
        "WS_URL": ws_url,
        "FANDOMAT_ID": fandomat_id,
        "DEVICE_TOKEN": device_token,
    }

    try:
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"Saved configuration to {CONFIG_PATH.resolve()}")
    except Exception as e:
        log.error(f"Failed to write {CONFIG_PATH}: {e}")

    return data


def _is_complete(cfg: dict) -> bool:
    return bool(cfg.get("WS_URL") and cfg.get("FANDOMAT_ID") is not None and cfg.get("DEVICE_TOKEN"))


def ensure_server_config(setup: bool = False) -> dict:
    """Ensure configuration exists.

    - If setup=True or config missing/incomplete: prompt interactively and save.
    - Else: return existing config without prompting.
    """
    current = load_existing_config()
    if setup or not _is_complete(current):
        return ensure_server_config_interactive()
    return current
