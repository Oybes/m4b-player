import os
import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path(os.getenv("DATA_DIR", "data"))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "site_name": "M4B Audiobook Vault",
    "audiobooks_dir": "audiobooks",
    "setup_completed": False,
    "port": 8000
}

def load_config() -> Dict[str, Any]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[Config] Error reading {CONFIG_FILE}: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(cfg: Dict[str, Any]):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def is_setup_completed() -> bool:
    cfg = load_config()
    return bool(cfg.get("setup_completed", False))

def mark_setup_completed(site_name: str, audiobooks_dir: str):
    cfg = load_config()
    cfg["site_name"] = site_name.strip() or "M4B Audiobook Vault"
    cfg["audiobooks_dir"] = audiobooks_dir.strip() or "audiobooks"
    cfg["setup_completed"] = True
    save_config(cfg)
    return cfg
