import argparse
import sys
import os
import json
import requests
import shutil
import tarfile
from pathlib import Path
from typing import List, Dict, Optional

from .. import __version__
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
            "hub": self.cmd_hub,
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
        print(f'\n[ZENV:{__version__}]')
        print('\nCommandes disponibles:')
        print('  run <fichier>            Exécute un fichier .zv/.py')
        print('  build -f <manifeste>     Construit un package depuis .zcf')
        print('  publish <package>        Publie sur Zenv Hub')
        print('  install <package>        Installe un package depuis le hub')
        print('  venv <nom>              Crée un environnement virtuel')
        print('  init <nom>              Initialise un nouveau projet')
        print('  search <terme>          Recherche un package')
        print('  list                    Liste les packages installés')
        print('  remove <package>        Supprime un package')
        print('  info <package>          Info détaillée d\'un package')
        print('  hub <commande>          Gestion du Zenv Hub')
        print('  version                 Affiche la version')
        print('\nCommandes hub:')
        print('  hub status              Vérifie le statut du hub')
        print('  hub login <token>       Se connecter au hub')
        print('  hub logout              Se déconnecter')
        print('\nExemples:')
        print('  zenv run app.zv')
        print('  zenv build -f package.zcf')
        print('  zenv install requests')
        print('  zenv venv mon-projet')
        print('  zenv init mon-package')
        print('  zenv search "web framework"')
        print('  zenv hub status')
        print('')
    
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
            "package.zcf": "[Zenv]\nname = my-package\nversion = 0.1.0\nauthor = Your Name\ndescription = A Zenv package\nlicense = MIT\n\n[File-build]\nmain = src/main.zv\ninclude = \n    src/**/*.zv\n    src/**/*.py\n    README.md\n\n[Dep.zv]\n\n[Dep.py]\n\n[Build]\ntype = zenv\noutput = dist/{name}-{version}.zcf.gs\n",
            
            "src/main.zv": 'print "Hello from Zenv!"\n\ndef greet(name):\n    return "Hello " + name + "!"\n\nif __name__ == "__main__":\n    result = greet("World")\n    print result\n',
            
            "README.md": "# My Package\n\nA Zenv package.\n",
        }
        
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
        print(f"[ZENV:{__version__}]")
        return 0
    
    def cmd_hub(self, args: List[str]) -> int:
        if not args:
            print("❌ Usage: zenv hub <commande>")
            print("   Commandes: status, login, logout")
            return 1
        
        hub_command = args[0]
        
        if hub_command == "status":
            return self._hub_status()
        elif hub_command == "login":
            token = args[1] if len(args) > 1 else input("Entrez votre token Zenv: ")
            return self._hub_login(token)
        elif hub_command == "logout":
            return self._hub_logout()
        else:
            print(f"❌ Commande hub inconnue: {hub_command}")
            return 1
    
    def _hub_status(self) -> int:
        try:
            response = requests.get("https://zenv-hub.onrender.com/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Zenv Hub: En ligne")
                print(f"📊 Statut: {data.get('status', 'N/A')}")
                print(f"📡 GitHub: {data.get('github', 'N/A')}")
                return 0
            else:
                print(f"❌ Zenv Hub: Hors ligne ({response.status_code})")
                return 1
        except Exception as e:
            print(f"❌ Erreur de connexion au hub: {e}")
            return 1
    
    def _hub_login(self, token: str) -> int:
        token_file = Path.home() / ".zenv" / "token"
        token_file.parent.mkdir(exist_ok=True)
        
        with open(token_file, "w") as f:
            f.write(token.strip())
        
        try:
            headers = {"Authorization": f"Token {token}"}
            response = requests.get(
                "https://zenv-hub.onrender.com/api/auth/profile",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json().get('user', {})
                print(f"✅ Connecté au Zenv Hub")
                print(f"👤 Utilisateur: {user_data.get('username', 'N/A')}")
                print(f"🎯 Rôle: {user_data.get('role', 'N/A')}")
                return 0
            else:
                print(f"❌ Token invalide: {response.status_code}")
                token_file.unlink(missing_ok=True)
                return 1
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            token_file.unlink(missing_ok=True)
            return 1
    
    def _hub_logout(self) -> int:
        token_file = Path.home() / ".zenv" / "token"
        if token_file.exists():
            token_file.unlink()
            print("✅ Déconnecté du Zenv Hub")
        else:
            print("ℹ️  Aucune session active")
        return 0
    
    def _get_auth_headers(self):
        token_file = Path.home() / ".zenv" / "token"
        if token_file.exists():
            with open(token_file, "r") as f:
                token = f.read().strip()
                return {"Authorization": f"Token {token}"}
        return {}
    
    def _publish_to_hub(self, package_file: str) -> int:
        print(f"📤 Publication de {package_file} sur Zenv Hub...")
        
        try:
            path = Path(package_file)
            if not path.exists():
                print(f"❌ Fichier non trouvé: {package_file}")
                return 1
            
            with open(package_file, 'rb') as f:
                file_content = f.read()
            
            package_name = path.stem.replace('.zcf', '')
            version = "1.0.0"
            description = ""
            
            try:
                with tarfile.open(package_file, "r:gz") as tar:
                    for member in tar.getmembers():
                        if member.name.endswith("metadata.json") or member.name.endswith("package.zcf"):
                            metadata_file = tar.extractfile(member)
                            if metadata_file:
                                content = metadata_file.read().decode('utf-8')
                                if 'metadata.json' in member.name:
                                    metadata = json.loads(content)
                                    package_name = metadata.get('name', package_name)
                                    version = metadata.get('version', version)
                                    description = metadata.get('description', description)
                                elif 'package.zcf' in member.name:
                                    import configparser
                                    config = configparser.ConfigParser()
                                    config.read_string(content)
                                    if 'Zenv' in config:
                                        package_name = config['Zenv'].get('name', package_name)
                                        version = config['Zenv'].get('version', version)
                                        description = config['Zenv'].get('description', description)
            except:
                pass
            
            hub_url = "https://zenv-hub.onrender.com/api/packages/upload"
            
            files = {
                'file': (path.name, file_content, 'application/gzip')
            }
            
            data = {
                'name': package_name,
                'version': version,
                'description': description or f"Package {package_name}",
                'author': 'Zenv User'
            }
            
            headers = self._get_auth_headers()
            
            response = requests.post(
                hub_url,
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                print("✅ Package publié avec succès!")
                print(f"📦 Nom: {package_name}")
                print(f"📄 Version: {version}")
                if response.json():
                    print(f"🔗 URL: https://zenv-hub.onrender.com/api/packages/download/{package_name}/{version}")
                return 0
            else:
                print(f"❌ Erreur: {response.status_code}")
                print(f"   Message: {response.text}")
                
                if response.status_code == 401:
                    print("\n💡 Conseil: Connectez-vous d'abord avec:")
                    print("   zenv hub login <votre_token>")
                
                return 1
                
        except Exception as e:
            print(f"❌ Erreur de publication: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def _install_package(self, package_name: str, version: str) -> int:
        print(f"📦 Installation de {package_name}@{version}...")
        
        try:
            headers = self._get_auth_headers()
            
            check_url = f"https://zenv-hub.onrender.com/api/packages"
            response = requests.get(check_url, headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Erreur de connexion au hub: {response.status_code}")
                return 1
            
            packages = response.json().get('packages', [])
            package_info = None
            
            for pkg in packages:
                if pkg['name'] == package_name:
                    package_info = pkg
                    if version == "latest":
                        version = pkg.get('version', '1.0.0')
                    break
            
            if not package_info:
                print(f"❌ Package non disponible sur le hub: {package_name}")
                print(f"   Packages disponibles: {[p['name'] for p in packages]}")
                return 1
            
            filename = package_info.get('filename', f"{package_name}-{version}.zv")
            
            download_url = f"https://zenv-hub.onrender.com/api/packages/download/{package_name}/{version}"
            response = requests.get(download_url, headers=headers, stream=True)
            
            if response.status_code != 200:
                if response.status_code == 404:
                    print(f"❌ Version non trouvée: {package_name}@{version}")
                elif response.status_code == 401:
                    print(f"❌ Accès non autorisé")
                    print("💡 Connectez-vous avec: zenv hub login <token>")
                else:
                    print(f"❌ Erreur: {response.status_code}")
                return 1
            
            packages_dir = Path.home() / ".zenv" / "packages" / package_name
            if packages_dir.exists():
                shutil.rmtree(packages_dir)
            packages_dir.mkdir(parents=True, exist_ok=True)
            
            archive_file = packages_dir / filename
            with open(archive_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"📦 Extraction de l'archive...")
            
            try:
                with tarfile.open(archive_file, "r:gz") as tar:
                    tar.extractall(packages_dir)
                
                print(f"✅ Archive extraite")
                
                from ..transpiler.tra import ZenvTranspiler
                transpiler = ZenvTranspiler()
                
                for zv_file in packages_dir.rglob("*.zv"):
                    if zv_file.is_file():
                        py_file = zv_file.with_suffix('.py')
                        try:
                            transpiler.transpile_file(str(zv_file), str(py_file))
                            print(f"✅ Transpilé: {zv_file.name}")
                        except Exception as e:
                            print(f"⚠️  Non transpilé: {zv_file.name}")
                
                archive_file.unlink(missing_ok=True)
                
            except Exception as e:
                print(f"❌ Erreur d'extraction: {e}")
                try:
                    from ..transpiler.tra import ZenvTranspiler
                    transpiler = ZenvTranspiler()
                    
                    py_file = archive_file.with_suffix('.py')
                    transpiler.transpile_file(str(archive_file), str(py_file))
                    print(f"✅ Fichier transpilé")
                except:
                    pass
            
            package_metadata = {
                'name': package_name,
                'version': version,
                'filename': filename,
                'description': package_info.get('description', ''),
                'author': package_info.get('author', ''),
                'size': package_info.get('size', 0),
                'installed_at': str(__import__('datetime').datetime.now()),
                'downloads_count': package_info.get('downloads_count', 0)
            }
            
            with open(packages_dir / "package.json", "w") as f:
                json.dump(package_metadata, f, indent=2)
            
            print(f"✅ {package_name}@{version} installé avec succès!")
            print(f"📁 Emplacement: {packages_dir}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Erreur d'installation: {e}")
            import traceback
            traceback.print_exc()
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
                print(f"📦 Taille: {info.get('size', 0)} octets")
                print(f"📥 Installé le: {info.get('installed_at', 'N/A')}")
                
                print(f"📂 Fichiers:")
                for item in local_dir.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(local_dir)
                        print(f"   • {rel_path}")
                
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
                        print(f"📦 Taille: {pkg.get('size', 0)} octets")
                        print(f"📅 Mise à jour: {pkg.get('updated_at', 'N/A')}")
                        return 0
        except:
            pass
        
        print(f"❌ Package non trouvé: {package_name}")
        return 1
