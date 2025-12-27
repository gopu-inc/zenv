import argparse
import sys
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional

from ..runtime.run import ZenvRuntime
from ..builder.build import ZenvBuilder, ZenvManifest

class ZenvCommand:
    
    def __init__(self):
        self.hub_url = "https://zenv-hub.onrender.com"
        self.runtime = ZenvRuntime(self.hub_url)
        self.builder = ZenvBuilder()
        
    def execute(self, args: List[str]) -> int:
        pass

class ZenvCLI:
    
    def __init__(self):
        self.commands = {
            "run": self.cmd_run,
            "build": self.cmd_build,
            "publish": self.cmd_publish,
            "install": self.cmd_install,
            "venv": self.cmd_venv,
            "init": self.cmd_init,
            "search": self.cmd_search,
            "list": self.cmd_list,
            "remove": self.cmd_remove,
            "info": self.cmd_info,
            "version": self.cmd_version,
        }
        
    def run(self, args: List[str]) -> int:
        if not args:
            self.print_help()
            return 0
        
        command = args[0]
        command_args = args[1:]
        
        if command in self.commands:
            return self.commands[command](command_args)
        else:
            print(f"❌ Commande inconnue: {command}")
            self.print_help()
            return 1
    
    def print_help(self):
        print('''
        ZENV v0.1.0

Commandes disponibles:
  run <fichier>            Exécute un fichier .zv/.py
  build -f <manifeste>     Construit un package depuis .zcf
  publish <package>        Publie sur Zenv Hub
  install <package>        Installe un package depuis le hub
  venv <nom>              Crée un environnement virtuel
  init <nom>              Initialise un nouveau projet
  search <terme>          Recherche un package
  list                    Liste les packages installés
  remove <package>        Supprime un package
  info <package>          Info détaillée d'un package
  version                 Affiche la version

Exemples:
  zenv run app.zv
  zenv build -f package.zcf
  zenv install requests
  zenv venv mon-projet
  zenv init mon-package
  zenv search "web framework"
        ''')
    
    def cmd_run(self, args: List[str]) -> int:
        if not args:
            print("❌ Usage: zenv run <fichier> [args...]")
            return 1
        
        file_path = args[0]
        runtime = ZenvRuntime()
        return runtime.execute(file_path, args[1:])
    
    def cmd_build(self, args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="zenv build")
        parser.add_argument("-f", "--file", default="package.zcf", help="Fichier manifeste .zcf")
        parser.add_argument("-o", "--output", help="Fichier de sortie")
        parser.add_argument("--clean", action="store_true", help="Nettoyer avant build")
        
        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return 1
        
        builder = ZenvBuilder()
        return builder.build_from_manifest(parsed.file, parsed.output, parsed.clean)
    
    def cmd_publish(self, args: List[str]) -> int:
        if not args:
            print("❌ Usage: zenv publish <fichier.zcf.gs>")
            return 1
        
        package_file = args[0]
        return self._publish_to_hub(package_file)
    
    def cmd_install(self, args: List[str]) -> int:
        if not args:
            print("❌ Usage: zenv install <package> [--version=x.x.x]")
            return 1
        
        package_name = args[0]
        version = "latest"
        
        if "@" in package_name:
            package_name, version = package_name.split("@")
        elif "==" in package_name:
            package_name, version = package_name.split("==")
        
        return self._install_package(package_name, version)
    
    def cmd_venv(self, args: List[str]) -> int:
        if not args:
            print("❌ Usage: zenv venv <nom> [--python=3.x]")
            return 1
        
        venv_name = args[0]
        runtime = ZenvRuntime()
        return runtime.create_virtualenv(venv_name)
    
    def cmd_init(self, args: List[str]) -> int:
        project_name = args[0] if args else "."
        
        print(f"🚀 Initialisation du projet Zenv: {project_name}")
        
        project_path = Path(project_name)
        project_path.mkdir(exist_ok=True)
        
        files = {
            "package.zcf": '''# Zenv Configuration File
[Zenv]
name = my-package
version = 0.1.0
author = Your Name
description = A Zenv package
license = MIT

[File-build]
main = src/main.zv
include = 
    src/**/*.zv
    src/**/*.py
    README.md

[Dep.zv]

[Dep.py]

[Build]
type = zenv
output = dist/{name}-{version}.zcf.gs
''',
            
            "src/main.zv": '''# Main Zenv file
print "Hello from Zenv!"

def greet(name):
    return "Hello " + name + "!"

if __name__ == "__main__":
    result = greet("World")
    print result
''',
            
            "README.md": f'''# {project_path.name}

A Zenv package.

## Installation
```bash
zenv install {project_path.name}
```

Usage

```bash
zenv run src/main.zv
```

Building

```bash
zenv build -f package.zcf
```

''',
}

```
    for filename, content in files.items():
        file_path = project_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(content)
            print(f"  ✓ Créé: {filename}")
    
    print(f"✅ Projet initialisé dans: {project_path}")
    return 0

def cmd_search(self, args: List[str]) -> int:
    if not args:
        print("❌ Usage: zenv search <terme>")
        return 1
    
    query = args[0]
    return self._search_packages(query)

def cmd_list(self, args: List[str]) -> int:
    packages_dir = Path.home() / ".zenv" / "packages"
    
    if not packages_dir.exists():
        print("📦 Aucun package installé")
        return 0
    
    packages = []
    for pkg_dir in packages_dir.iterdir():
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

def cmd_remove(self, args: List[str]) -> int:
    if not args:
        print("❌ Usage: zenv remove <package>")
        return 1
    
    package_name = args[0]
    return self._remove_package(package_name)

def cmd_info(self, args: List[str]) -> int:
    if not args:
        print("❌ Usage: zenv info <package>")
        return 1
    
    package_name = args[0]
    return self._show_package_info(package_name)

def cmd_version(self, args: List[str]) -> int:
    from .. import __version__
    print(f"Zenv Ecosystem v{__version__}")
    return 0

def _publish_to_hub(self, package_file: str) -> int:
    print(f"📤 Publication de {package_file} sur Zenv Hub...")
    
    try:
        with open(package_file, 'rb') as f:
            file_content = f.read()
        
        hub_url = "https://zenv-hub.onrender.com/api/packages/upload"
        
        files = {'file': (package_file, file_content)}
        data = {'name': Path(package_file).stem}
        
        response = requests.post(hub_url, files=files, data=data)
        
        if response.status_code == 200:
            print("✅ Package publié avec succès!")
            return 0
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            return 1
            
    except Exception as e:
        print(f"❌ Erreur de publication: {e}")
        return 1

def _install_package(self, package_name: str, version: str) -> int:
    print(f"📦 Installation de {package_name}@{version}...")
    
    try:
        download_url = f"https://zenv-hub.onrender.com/api/packages/download/{package_name}/{version}"
        response = requests.get(download_url, stream=True)
        
        if response.status_code != 200:
            print(f"❌ Package non trouvé: {package_name}")
            return 1
        
        packages_dir = Path.home() / ".zenv" / "packages" / package_name
        packages_dir.mkdir(parents=True, exist_ok=True)
        
        package_file = packages_dir / f"{package_name}.zcf.gs"
        with open(package_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        from ..builder.build import ZenvBuilder
        builder = ZenvBuilder()
        builder.install_package(str(package_file))
        
        print(f"✅ {package_name}@{version} installé avec succès!")
        return 0
        
    except Exception as e:
        print(f"❌ Erreur d'installation: {e}")
        return 1

def _search_packages(self, query: str) -> int:
    try:
        hub_url = "https://zenv-hub.onrender.com/api/packages"
        response = requests.get(hub_url)
        
        if response.status_code != 200:
            print("❌ Impossible de contacter Zenv Hub")
            return 1
        
        packages = response.json().get('packages', [])
        
        results = [pkg for pkg in packages if query.lower() in pkg.get('name', '').lower()]
        
        if not results:
            print(f"🔍 Aucun package trouvé pour: {query}")
            return 0
        
        print(f"🔍 Résultats pour '{query}' ({len(results)}):")
        for pkg in results:
            print(f"  • {pkg['name']} v{pkg.get('version', '?')}")
            if pkg.get('description'):
                print(f"    {pkg['description'][:60]}...")
            print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur de recherche: {e}")
        return 1

def _remove_package(self, package_name: str) -> int:
    package_dir = Path.home() / ".zenv" / "packages" / package_name
    
    if not package_dir.exists():
        print(f"❌ Package non installé: {package_name}")
        return 1
    
    try:
        import shutil
        shutil.rmtree(package_dir)
        print(f"✅ Package supprimé: {package_name}")
        return 0
    except Exception as e:
        print(f"❌ Erreur de suppression: {e}")
        return 1

def _show_package_info(self, package_name: str) -> int:
    local_dir = Path.home() / ".zenv" / "packages" / package_name
    if local_dir.exists():
        info_file = local_dir / "package.json"
        if info_file.exists():
            with open(info_file) as f:
                info = json.load(f)
            
            print(f"📦 Package: {info.get('name', package_name)}")
            print(f"📄 Version: {info.get('version', 'N/A')}")
            print(f"👤 Auteur: {info.get('author', 'N/A')}")
            print(f"📝 Description: {info.get('description', 'N/A')}")
            print(f"📁 Chemin: {local_dir}")
            return 0
    
    try:
        hub_url = f"https://zenv-hub.onrender.com/api/packages"
        response = requests.get(hub_url)
        
        if response.status_code == 200:
            packages = response.json().get('packages', [])
            for pkg in packages:
                if pkg['name'] == package_name:
                    print(f"📦 Package: {pkg['name']}")
                    print(f"📄 Version: {pkg.get('version', 'N/A')}")
                    print(f"👤 Auteur: {pkg.get('author', 'N/A')}")
                    print(f"📝 Description: {pkg.get('description', 'N/A')}")
                    print(f"📥 Téléchargements: {pkg.get('downloads_count', 0)}")
                    return 0
    except:
        pass
    
    print(f"❌ Package non trouvé: {package_name}")
    return 1
