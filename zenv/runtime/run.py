"""
Runtime Zenv - Exécution de code .zv et gestion d'environnements
"""

import os
import sys
import subprocess
import tempfile
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import venv

class ZenvRuntime:
    """Runtime pour exécuter du code Zenv"""
    
    def __init__(self, hub_url: str = "https://zenv-hub.onrender.com"):
        self.hub_url = hub_url
        self.version = "1.0.0"
        
    def execute(self, file_path: str, args: List[str] = None) -> int:
        """Exécute un fichier .zv ou .py"""
        path = Path(file_path)
        
        if not path.exists():
            print(f"❌ Fichier non trouvé: {file_path}")
            return 1
            
        # Déterminer le type de fichier
        if path.suffix in ['.zv', '.zenv']:
            return self._execute_zv(path, args or [])
        else:
            return self._execute_python(path, args or [])
    
    def _execute_zv(self, path: Path, args: List[str]) -> int:
        """Exécute un fichier Zenv (transpile puis exécute)"""
        from ..transpiler.tra import ZenvTranspiler
        
        try:
            # Transpiler temporairement
            transpiler = ZenvTranspiler()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                python_code = transpiler.transpile_file(str(path))
                tmp.write(python_code)
                tmp_path = tmp.name
            
            # Exécuter le Python transpilé
            result = subprocess.run([sys.executable, tmp_path] + args)
            
            # Nettoyer
            os.unlink(tmp_path)
            
            return result.returncode
            
        except Exception as e:
            print(f"❌ Erreur d'exécution: {e}")
            return 1
    
    def _execute_python(self, path: Path, args: List[str]) -> int:
        """Exécute un fichier Python normalement"""
        try:
            result = subprocess.run([sys.executable, str(path)] + args)
            return result.returncode
        except Exception as e:
            print(f"❌ Erreur d'exécution: {e}")
            return 1
    
    def create_virtualenv(self, name: str, python_version: str = None) -> int:
        """Crée un environnement virtuel Zenv"""
        env_path = Path(name)
        
        if env_path.exists():
            print(f"❌ L'environnement existe déjà: {name}")
            return 1
            
        print(f"🌱 Création de l'environnement '{name}'...")
        
        try:
            # Créer l'environnement Python standard
            builder = venv.EnvBuilder(
                system_site_packages=False,
                clear=True,
                symlinks=True,
                with_pip=True
            )
            builder.create(env_path)
            
            # Créer la structure Zenv spécifique
            (env_path / "site-zenv").mkdir(exist_ok=True)
            (env_path / "zenv-packages").mkdir(exist_ok=True)
            
            # Créer le script d'activation Zenv
            self._create_zenv_activation(env_path)
            
            # Créer la configuration
            config = {
                "name": name,
                "python_version": python_version or f"{sys.version_info.major}.{sys.version_info.minor}",
                "zenv_version": self.version,
                "created_at": str(__import__('datetime').datetime.now())
            }
            
            with open(env_path / "zenv-config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Environnement créé: {env_path}")
            print(f"📖 Pour activer: source {name}/bin/zenv-activate")
            print(f"📖 Pour désactiver: deactivate")
            
            return 0
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            if env_path.exists():
                shutil.rmtree(env_path)
            return 1
    
    def _create_zenv_activation(self, env_path: Path):
        """Crée le script d'activation Zenv"""
        activate_content = f"""#!/bin/bash
# Activation de l'environnement Zenv

export ZENV_ENV="{env_path}"
export VIRTUAL_ENV="{env_path}"
export PATH="{env_path}/bin:$PATH"
export PYTHONPATH="{env_path}/site-zenv:$PYTHONPATH"

# Alias pour zenv
alias zenvi="{sys.executable} -m zenv"

PS1="(zenv:${{ZENV_ENV##*/}}) $PS1"

echo "✅ Environnement Zenv activé: {env_path.name}"
"""
        
        activate_file = env_path / "bin" / "zenv-activate"
        with open(activate_file, "w") as f:
            f.write(activate_content)
        activate_file.chmod(0o755)
