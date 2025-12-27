"""
Environnements virtuels Zenv
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

class ZenvVirtualEnv:
    def __init__(self, name: str):
        self.name = name
        self.path = Path(name)
        
    def create(self, python_version: Optional[str] = None) -> int:
        """Crée un nouvel environnement virtuel"""
        print(f"🌱 Création de l'environnement '{self.name}'...")
        
        if self.path.exists():
            print(f"❌ Le dossier existe déjà: {self.name}")
            return 1
        
        try:
            # Créer la structure
            (self.path / "bin").mkdir(parents=True)
            (self.path / "lib").mkdir()
            (self.path / "include").mkdir()
            
            # Créer les scripts
            self._create_scripts()
            
            # Créer la configuration
            self._create_config(python_version)
            
            print(f"✅ Environnement créé: {self.path}")
            print(f"📖 Pour activer: source {self.name}/bin/activate")
            
            return 0
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            if self.path.exists():
                shutil.rmtree(self.path)
            return 1
    
    def _create_scripts(self):
        """Crée les scripts d'activation"""
        # Script d'activation bash
        activate_content = f"""#!/bin/bash
# Activation de l'environnement Zenv: {self.name}

export VIRTUAL_ENV="{self.path}"
export PATH="{self.path}/bin:$PATH"

# Désactiver PYTHONHOME s'il est défini
unset PYTHONHOME

PS1="({self.name}) $PS1"

echo "✅ Environnement Zenv '{self.name}' activé"
"""
        
        activate_path = self.path / "bin" / "activate"
        with open(activate_path, "w") as f:
            f.write(activate_content)
        activate_path.chmod(0o755)
        
        # Script python
        python_content = f"""#!/usr/bin/env python3
# Python wrapper pour l'environnement Zenv
import sys
import os

# Ajouter le chemin de l'environnement
env_path = r"{self.path}"
lib_path = os.path.join(env_path, "lib")

if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# Exécuter Python normalement
if __name__ == "__main__":
    from IPython import start_ipython
    start_ipython(argv=[])
"""
        
        python_path = self.path / "bin" / "python"
        with open(python_path, "w") as f:
            f.write(python_content)
        python_path.chmod(0o755)
    
    def _create_config(self, python_version: Optional[str]):
        """Crée le fichier de configuration"""
        config = {
            "name": self.name,
            "path": str(self.path.absolute()),
            "python_version": python_version or f"{sys.version_info.major}.{sys.version_info.minor}",
            "created_at": datetime.now().isoformat(),
            "zenv_version": "1.0.0"
        }
        
        with open(self.path / "zenv-env.json", "w") as f:
            json.dump(config, f, indent=2)
