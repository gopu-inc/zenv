# znv/virtualenv.py
"""
Environnements virtuels Zenv - Léger et compatible
"""

import os
import sys
import shutil
import venv
from pathlib import Path
from typing import Optional

class ZenvVirtualEnv:
    """Gestionnaire d'environnements virtuels Zenv"""
    
    def __init__(self, name: str):
        self.name = name
        self.path = Path.cwd() / name
        self.bin_dir = self.path / "bin"
        self.lib_dir = self.path / "lib"
        self.site_zenv = self.path / "site-zenv"
        
    def create(self, python_version: Optional[str] = None, system_site_packages: bool = False) -> int:
        """Crée un nouvel environnement virtuel"""
        print(f"🌱 Création de l'environnement '{self.name}'...")
        
        if self.path.exists():
            print(f"❌ L'environnement existe déjà: {self.name}")
            return 1
        
        try:
            # Créer la structure de base
            self.path.mkdir()
            self.bin_dir.mkdir()
            self.lib_dir.mkdir()
            self.site_zenv.mkdir()
            
            # Créer les scripts d'activation
            self._create_activation_scripts()
            
            # Créer le fichier de configuration
            self._create_config(python_version, system_site_packages)
            
            # Créer le lien vers Python
            self._create_python_symlink()
            
            # Créer le fichier site-zenv
            self._create_site_zenv()
            
            print(f"✅ Environnement créé: {self.path}")
            print(f"📖 Pour activer: source {self.name}/bin/start")
            print(f"📖 Pour désactiver: deactivate")
            
            return 0
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            if self.path.exists():
                shutil.rmtree(self.path)
            return 1
    
    def _create_activation_scripts(self):
        """Crée les scripts d'activation"""
        # Script start (activation)
        start_content = f"""#!/bin/bash
# Activation de l'environnement Zenv: {self.name}

export ZENV_ENV="{self.path}"
export VIRTUAL_ENV="{self.path}"
export PATH="{self.bin_dir}:$PATH"
export PYTHONPATH="{self.site_zenv}:$PYTHONPATH"

PS1="({self.name}) $PS1"

echo "✅ Environnement Zenv '{self.name}' activé"
"""
        
        with open(self.bin_dir / "start", "w") as f:
            f.write(start_content)
        
        (self.bin_dir / "start").chmod(0o755)
        
        # Script deactivate
        deactivate_content = """#!/bin/bash
# Désactivation de l'environnement Zenv

if [ -n "$ZENV_ENV" ]; then
    export PATH="$(echo $PATH | sed "s|$ZENV_ENV/bin:||")"
    unset ZENV_ENV
    unset VIRTUAL_ENV
    PS1="$(echo $PS1 | sed "s|^($(basename $VIRTUAL_ENV)) ||")"
    echo "✅ Environnement Zenv désactivé"
fi
"""
        
        with open(self.bin_dir / "deactivate", "w") as f:
            f.write(deactivate_content)
        
        (self.bin_dir / "deactivate").chmod(0o755)
    
    def _create_config(self, python_version: Optional[str], system_site: bool):
        """Crée le fichier de configuration"""
        config = {
            "name": self.name,
            "path": str(self.path),
            "python_version": python_version or f"{sys.version_info.major}.{sys.version_info.minor}",
            "system_site_packages": system_site,
            "created_at": str(datetime.now()),
            "zenv_version": "1.0.0"
        }
        
        with open(self.path / "zenv.env", "w") as f:
            json.dump(config, f, indent=2)
    
    def _create_python_symlink(self):
        """Crée un lien symbolique vers Python"""
        python_path = sys.executable
        if os.name == 'nt':  # Windows
            with open(self.bin_dir / "python", "w") as f:
                f.write(f'#!{python_path}\n')
            with open(self.bin_dir / "python3", "w") as f:
                f.write(f'#!{python_path}\n')
        else:
            os.symlink(python_path, self.bin_dir / "python")
            os.symlink(python_path, self.bin_dir / "python3")
    
    def _create_site_zenv(self):
        """Crée le fichier site-zenv personnalisé"""
        site_content = f"""# site-zenv pour {self.name}
import sys
import os

# Chemin vers les packages Zenv
zenv_path = r"{self.site_zenv}"
if os.path.exists(zenv_path):
    sys.path.insert(0, zenv_path)

# Configuration Zenv
os.environ['ZENV_ENV'] = r"{self.path}"
os.environ['ZENV_VERSION'] = '1.0.0'

print(f"Zenv environment: {{os.environ.get('ZENV_ENV')}}")
"""
        
        with open(self.site_zenv / "__init__.py", "w") as f:
            f.write(site_content)
