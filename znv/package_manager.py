"""
Gestionnaire de packages Zenv
"""

import requests
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, List

class ZenvPackageManager:
    def __init__(self, hub_url: str = "https://zenv-hub.onrender.com"):
        self.hub_url = hub_url
        self.zenv_home = Path.home() / ".zenv"
        self.packages_dir = self.zenv_home / "packages"
        self.cache_dir = self.zenv_home / "cache"
        
        # Créer les dossiers
        self.zenv_home.mkdir(exist_ok=True)
        self.packages_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
    
    def check_hub_status(self) -> bool:
        """Vérifie si le hub est en ligne"""
        try:
            response = requests.get(f"{self.hub_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_packages(self) -> int:
        """Liste les packages installés"""
        packages = []
        
        for pkg_dir in self.packages_dir.iterdir():
            if pkg_dir.is_dir():
                info_file = pkg_dir / "package.json"
                if info_file.exists():
                    with open(info_file) as f:
                        info = json.load(f)
                        packages.append(info)
        
        if not packages:
            print("📦 Aucun package installé")
            return 0
            
        print(f"📦 Packages installés ({len(packages)}):")
        for pkg in packages:
            print(f"  • {pkg.get('name', 'unknown')} v{pkg.get('version', '?')}")
            
        return 0
    
    def install_package(self, package_name: str, version: str = "latest", fast: bool = False) -> int:
        """Installe un package depuis le hub"""
        print(f"📦 Installation de {package_name}...")
        
        # Vérifier le hub
        if not self.check_hub_status():
            print("❌ Hub hors ligne")
            return 1
        
        # Récupérer les infos
        package_info = self._get_package_info(package_name)
        if not package_info:
            print(f"❌ Package {package_name} non trouvé sur le hub")
            return 1
        
        # Créer le dossier du package
        pkg_dir = self.packages_dir / package_name
        pkg_dir.mkdir(exist_ok=True)
        
        # Sauvegarder les infos
        with open(pkg_dir / "package.json", "w") as f:
            json.dump(package_info, f, indent=2)
        
        print(f"✅ {package_name} v{package_info.get('version', '?')} installé")
        print(f"   Emplacement: {pkg_dir}")
        
        return 0
    
    def _get_package_info(self, package_name: str) -> Optional[Dict]:
        """Récupère les infos d'un package depuis le hub"""
        try:
            response = requests.get(f"{self.hub_url}/api/packages")
            if response.status_code != 200:
                return None
                
            packages = response.json().get('packages', [])
            for pkg in packages:
                if pkg['name'] == package_name:
                    return pkg
                    
            return None
        except Exception as e:
            print(f"❌ Erreur de connexion au hub: {e}")
            return None
