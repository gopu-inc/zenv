"""
Utilitaires pour Zenv
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

def get_zenv_home() -> Path:
    """Retourne le dossier home de Zenv"""
    home = Path.home() / ".zenv"
    home.mkdir(exist_ok=True)
    return home

def get_cache_dir() -> Path:
    """Retourne le dossier de cache"""
    cache_dir = get_zenv_home() / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir

def hash_string(text: str) -> str:
    """Hash une chaîne de caractères"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def load_json(path: Path, default: Any = None) -> Any:
    """Charge un fichier JSON"""
    if not path.exists():
        return default
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default

def save_json(path: Path, data: Any):
    """Sauvegarde des données en JSON"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def print_success(msg: str):
    """Affiche un message de succès"""
    print(f"✅ {msg}")

def print_error(msg: str):
    """Affiche un message d'erreur"""
    print(f"❌ {msg}")

def print_info(msg: str):
    """Affiche un message d'information"""
    print(f"ℹ️  {msg}")
