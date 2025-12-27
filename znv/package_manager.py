# znv/package_manager.py
"""
Gestionnaire de packages Zenv - Connecté au hub Render
"""

import requests
import json
import hashlib
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

class ZenvPackageManager:
    """Gère les packages depuis le hub Zenv"""
    
    def __init__(self, hub_url: str = "https://zenv-hub.onrender.com"):
        self.hub_url = hub_url
        self.packages_dir = Path.home() / ".zenv" / "packages"
        self.bin_dir = Path.home() / ".zenv" / "bin"
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        
    def install_package(self, package_name: str, version: str = "latest", fast: bool = False) -> int:
        """Installe un package depuis le hub"""
        print(f"📦 Installation de {package_name}...")
        
        # Récupérer les infos du package
        package_info = self._get_package_info(package_name, version)
        if not package_info:
            print(f"❌ Package non trouvé: {package_name}")
            return 1
        
        # Télécharger
        download_url = f"{self.hub_url}/api/packages/download/{package_name}/{package_info['version']}"
        
        try:
            response = requests.get(download_url, stream=True)
            if response.status_code != 200:
                print(f"❌ Erreur de téléchargement: {response.status_code}")
                return 1
            
            # Sauvegarder temporairement
            with tempfile.NamedTemporaryFile(suffix=".zv", delete=False) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                temp_path = tmp.name
            
            # Déterminer le type de package
            if fast or package_info.get('type') == 'bolt':
                # Installation rapide - juste le fichier
                self._install_bolt(package_name, temp_path, package_info)
            else:
                # Installation complète avec build
                self._install_full(package_name, temp_path, package_info)
            
            print(f"✅ {package_name} v{package_info['version']} installé avec succès!")
            return 0
            
        except Exception as e:
            print(f"❌ Erreur d'installation: {e}")
            return 1
    
    def _install_bolt(self, package_name: str, package_path: str, info: Dict):
        """Installation rapide Bolt"""
        # Créer le dossier du package
        pkg_dir = self.packages_dir / package_name
        pkg_dir.mkdir(exist_ok=True)
        
        # Copier le fichier
        shutil.copy2(package_path, pkg_dir / f"{package_name}.zv")
        
        # Sauvegarder les métadonnées
        with open(pkg_dir / "package.json", "w") as f:
            json.dump(info, f, indent=2)
        
        # Si c'est un exécutable, créer un lien dans bin
        if info.get('executable'):
            bin_name = info.get('bin_name', package_name)
            bin_path = self.bin_dir / bin_name
            
            with open(bin_path, "w") as f:
                f.write(f"""#!/usr/bin/env python3
# Zenv executable: {package_name}
import sys
import os
sys.path.insert(0, r"{pkg_dir}")
from {package_name} import main
if __name__ == "__main__":
    sys.exit(main())
""")
            bin_path.chmod(0o755)
    
    def _install_full(self, package_name: str, package_path: str, info: Dict):
        """Installation complète avec build"""
        # Extraire dans un répertoire temporaire
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Déterminer le type d'archive
            if package_path.endswith('.zip'):
                with zipfile.ZipFile(package_path, 'r') as zipf:
                    zipf.extractall(tmpdir)
            else:
                # C'est juste un fichier .zv
                shutil.copy2(package_path, tmpdir_path / f"{package_name}.zv")
            
            # Chercher un fichier de build
            build_file = tmpdir_path / "zenv.build"
            if build_file.exists():
                # Build spécifique Zenv
                self._build_zenv_package(tmpdir_path, package_name, info)
            else:
                # Build Python standard
                self._build_python_package(tmpdir_path, package_name, info)
    
    def _build_zenv_package(self, source_dir: Path, package_name: str, info: Dict):
        """Builder un package Zenv"""
        # Transpiler tous les fichiers .zv
        from .builder import ZenvBuilder
        builder = ZenvBuilder()
        
        for zv_file in source_dir.rglob("*.zv"):
            py_file = zv_file.with_suffix('.py')
            builder.transpile_file(str(zv_file), str(py_file))
        
        # Installer
        self._install_from_source(source_dir, package_name, info)
    
    def _build_python_package(self, source_dir: Path, package_name: str, info: Dict):
        """Builder un package Python"""
        # Chercher setup.py ou pyproject.toml
        setup_py = source_dir / "setup.py"
        pyproject = source_dir / "pyproject.toml"
        
        if setup_py.exists():
            # Installation avec setuptools
            subprocess.run([sys.executable, "-m", "pip", "install", str(source_dir)], check=False)
        elif pyproject.exists():
            # Installation avec build
            subprocess.run([sys.executable, "-m", "pip", "install", str(source_dir)], check=False)
        else:
            # Installation directe
            self._install_from_source(source_dir, package_name, info)
    
    def _install_from_source(self, source_dir: Path, package_name: str, info: Dict):
        """Installation directe depuis source"""
        pkg_dir = self.packages_dir / package_name
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)
        
        shutil.copytree(source_dir, pkg_dir)
        
        # Sauvegarder les métadonnées
        with open(pkg_dir / "package.json", "w") as f:
            json.dump(info, f, indent=2)
    
    def _get_package_info(self, package_name: str, version: str) -> Optional[Dict]:
        """Récupère les infos d'un package depuis le hub"""
        try:
            response = requests.get(f"{self.hub_url}/api/packages")
            if response.status_code != 200:
                return None
            
            packages = response.json().get('packages', [])
            for pkg in packages:
                if pkg['name'] == package_name:
                    if version == "latest" or pkg['version'] == version:
                        return pkg
            
            return None
        except:
            return None
    
    def list_packages(self) -> int:
        """Lister les packages installés"""
        packages = []
        for pkg_dir in self.packages_dir.iterdir():
            if pkg_dir.is_dir():
                info_file = pkg_dir / "package.json"
                if info_file.exists():
                    with open(info_file) as f:
                        info = json.load(f)
                        packages.append(info)
        
        print(f"📦 Packages installés ({len(packages)}):")
        for pkg in packages:
            print(f"  • {pkg['name']} v{pkg.get('version', '?')}")
            if pkg.get('description'):
                print(f"    {pkg['description'][:60]}...")
        
        return 0
