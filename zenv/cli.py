#!/usr/bin/env python3
"""
Zenv CLI - Interface de ligne de commande
"""

import argparse
import sys
import os
import json
import tarfile
import tempfile
import shutil
import subprocess
import time
import threading
import signal
import requests
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from . import __version__
from .runtime import ZenvRuntime
from .builder import ZenvBuilder
from .utils.hub_client import ZenvHubClient

# ============================================================================
# CONSTANTES ET CONFIGURATION
# ============================================================================

ZENV_HUB_URL = "https://zenv-hub.onrender.com"
ZENV_LANG_PACKAGE = "zenv-lang"
ZENV_TOKEN_PAGE = "https://init-hubs-dql3.vercel.app"
CURRENT_VERSION = __version__

# ============================================================================
# UTILITAIRES D'AFFICHAGE
# ============================================================================

class Colors:
    """Codes de couleurs ANSI"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    
    @staticmethod
    def color(text: str, color_code: str) -> str:
        if sys.stdout.isatty():
            return f"{color_code}{text}{Colors.RESET}"
        return text
    
    @staticmethod
    def success(text: str) -> str:
        return Colors.color(f"✓ {text}", Colors.GREEN)
    
    @staticmethod
    def error(text: str) -> str:
        return Colors.color(f"✗ {text}", Colors.RED)
    
    @staticmethod
    def warning(text: str) -> str:
        return Colors.color(f"⚠ {text}", Colors.YELLOW)
    
    @staticmethod
    def info(text: str) -> str:
        return Colors.color(f"ℹ {text}", Colors.BLUE)
    
    @staticmethod
    def highlight(text: str) -> str:
        return Colors.color(text, Colors.CYAN + Colors.BOLD)

class Spinner:
    """Spinner pour opérations longues"""
    
    def __init__(self, message="Chargement..."):
        self.message = message
        self.running = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
    
    def spin(self):
        i = 0
        while self.running:
            sys.stdout.write(f"\r{Colors.color(self.spinner_chars[i], Colors.CYAN)} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(self.spinner_chars)
    
    def start(self):
        if sys.stdout.isatty():
            self.running = True
            self.thread = threading.Thread(target=self.spin, daemon=True)
            self.thread.start()
    
    def stop(self, success=True, message=None):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=0.5)
            
            if sys.stdout.isatty():
                sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
                sys.stdout.flush()
                
            if message:
                print(Colors.success(message) if success else Colors.error(message))

# ============================================================================
# GESTIONNAIRE DE VERSION ET MISE À JOUR
# ============================================================================

class VersionManager:
    """Gestion des versions et mises à jour"""
    
    @staticmethod
    def get_latest_version_from_hub():
        """Récupérer la dernière version depuis le hub"""
        try:
            with Spinner("Connexion au hub..."):
                hub = ZenvHubClient()
                packages = hub.search_packages(ZENV_LANG_PACKAGE)
                
                if packages:
                    latest = None
                    for pkg in packages:
                        if pkg.get('name') == ZENV_LANG_PACKAGE:
                            version = pkg.get('version', '0.0.0')
                            if not latest or VersionManager._compare_versions(version, latest) > 0:
                                latest = version
                    return latest
            return None
        except Exception as e:
            print(Colors.warning(f"Impossible de vérifier les mises à jour: {e}"))
            return None
    
    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Comparer deux versions"""
        def parse(v):
            parts = []
            for part in v.split('.'):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(part)
            return parts
        
        v1_parts = parse(v1)
        v2_parts = parse(v2)
        
        return (v1_parts > v2_parts) - (v1_parts < v2_parts)
    
    @staticmethod
    def check_update_available():
        """Vérifier si une mise à jour est disponible"""
        latest = VersionManager.get_latest_version_from_hub()
        if not latest:
            return None
        
        if VersionManager._compare_versions(latest, CURRENT_VERSION) > 0:
            return latest
        return None
    
    @staticmethod
    def prompt_for_update(latest_version: str):
        """Demander à l'utilisateur s'il veut mettre à jour"""
        print(f"\n{Colors.highlight('═' * 50)}")
        print(f"{Colors.highlight('MISE À JOUR DISPONIBLE')}")
        print(f"{Colors.highlight('═' * 50)}")
        print(f"{Colors.info('Version actuelle:')} {CURRENT_VERSION}")
        print(f"{Colors.info('Dernière version:')} {latest_version}")
        print(f"\n{Colors.highlight('Hey, tu as déjà testé Zenv !')}")
        print(f"{Colors.highlight('Passons en production avec la dernière version !')}")
        
        while True:
            response = input(f"\n{Colors.highlight(f'Installer Zenv-Lang-{latest_version} ?')} (yes/no): ").strip().lower()
            if response in ['yes', 'y', 'oui', 'o']:
                return True
            elif response in ['no', 'n', 'non']:
                return False
            print(Colors.warning("Répondez par 'yes' ou 'no'"))

# ============================================================================
# GESTIONNAIRE D'AUTHENTIFICATION
# ============================================================================

class AuthManager:
    """Gestion de l'authentification"""
    
    @staticmethod
    def check_token():
        """Vérifier si l'utilisateur a un token"""
        hub = ZenvHubClient()
        return hub.is_logged_in()
    
    @staticmethod
    def prompt_for_token():
        """Demander à l'utilisateur de se connecter"""
        print(f"\n{Colors.highlight('═' * 50)}")
        print(f"{Colors.highlight('AUTHENTIFICATION REQUISE')}")
        print(f"{Colors.highlight('═' * 50)}")
        print(f"{Colors.info('Pour utiliser cette fonctionnalité, vous avez besoin d\\'un token.')}")
        print(f"\n{Colors.highlight('1. Rendez-vous sur:')}")
        print(f"   {Colors.color(ZENV_TOKEN_PAGE, Colors.CYAN)}")
        print(f"\n{Colors.highlight('2. Connectez-vous ou créez un compte')}")
        print(f"{Colors.highlight('3. Copiez votre token (commence par zenv_)')}")
        print(f"\n{Colors.highlight('4. Utilisez la commande:')}")
        print(f"   {Colors.color('zenv hub login <votre_token>', Colors.CYAN)}")
        print(f"\n{Colors.info('Ou annulez avec Ctrl+C')}")

# ============================================================================
# GESTIONNAIRE D'INSTALLATION
# ============================================================================

class InstallManager:
    """Gestion de l'installation des packages"""
    
    @staticmethod
    def install_zenv_lang(version: str):
        """Installer zenv-lang depuis le hub"""
        print(f"\n{Colors.highlight(f'Installation de Zenv-Lang v{version}...')}")
        
        try:
            hub = ZenvHubClient()
            
            with Spinner(f"Téléchargement de zenv-lang-{version}..."):
                content = hub.download_package(ZENV_LANG_PACKAGE, version)
            
            if not content:
                print(Colors.error("Échec du téléchargement"))
                return False
            
            with tempfile.NamedTemporaryFile(suffix='.zv', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                InstallManager._clean_old_versions()
                return InstallManager._install_package_file(tmp_path)
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            print(Colors.error(f"Erreur d'installation: {str(e)}"))
            return False
    
    @staticmethod
    def _clean_old_versions():
        """Nettoyer les anciennes versions de zenv"""
        try:
            current_dir = Path.cwd()
            for file in current_dir.glob("**/*"):
                if file.name in ['setup.py', 'pyproject.toml', 'setup.cfg']:
                    try:
                        file.unlink()
                        print(Colors.info(f"Supprimé: {file}"))
                    except:
                        pass
            
            site_dir = Path("/usr/bin/zenv-site/c82")
            if site_dir.exists():
                for item in site_dir.iterdir():
                    if item.is_dir() and item.name.startswith("zenv"):
                        try:
                            shutil.rmtree(item)
                            print(Colors.info(f"Supprimé ancienne version: {item.name}"))
                        except:
                            pass
        except Exception as e:
            print(Colors.warning(f"Note: {str(e)}"))
    
    @staticmethod
    def _install_package_file(package_file: str):
        """Installer un fichier package"""
        try:
            with tarfile.open(package_file, 'r:gz') as tar:
                metadata = None
                for member in tar.getmembers():
                    if member.name.endswith('metadata.json'):
                        f = tar.extractfile(member)
                        if f:
                            metadata = json.load(f)
                            break
                
                package_name = metadata.get('name', 'zenv-lang')
                
                site_dir = Path("/usr/bin/zenv-site/c82")
                site_dir.mkdir(parents=True, exist_ok=True)
                
                package_dir = site_dir / package_name
                if package_dir.exists():
                    shutil.rmtree(package_dir)
                
                package_dir.mkdir()
                tar.extractall(package_dir)
                
                print(Colors.success(f"Installé avec succès: {package_name}"))
                return True
                
        except Exception as e:
            print(Colors.error(f"Erreur d'installation: {str(e)}"))
            return False

# ============================================================================
# CLI PRINCIPAL
# ============================================================================

class ZenvCLI:
    """Interface de ligne de commande Zenv"""
    
    def __init__(self):
        self.runtime = ZenvRuntime()
        self.builder = ZenvBuilder()
        self.hub = ZenvHubClient()
        self._setup_signal_handler()
    
    def _setup_signal_handler(self):
        """Configurer le gestionnaire de signal Ctrl+C"""
        def signal_handler(sig, frame):
            print(f"\n{Colors.highlight('ZENV - ARRÊT DÉMANDÉ PAR L\\'UTILISATEUR')}")
            sys.exit(130)
        
        signal.signal(signal.SIGINT, signal_handler)
    
    def run(self, args: List[str]) -> int:
        """Exécuter la CLI"""
        self._check_for_updates_on_start()
        
        parser = self._create_parser()
        
        if not args:
            parser.print_help()
            return 0
        
        try:
            parsed = parser.parse_args(args)
            
            commands = {
                "run": lambda: self._cmd_run(parsed.file, parsed.args),
                "build": lambda: self._cmd_build(parsed),
                "pkg": lambda: self._cmd_pkg(parsed),
                "hub": lambda: self._cmd_hub(parsed),
                "version": self._cmd_version,
                "site": lambda: self._cmd_site(parsed.file),
                "init": lambda: self._cmd_init(parsed.name),
                "update": lambda: self._cmd_update(parsed.package, parsed.force),
                "info": lambda: self._cmd_info(parsed.package),
                "clean": self._cmd_clean,
                "config": lambda: self._cmd_config(parsed.action, parsed.key, parsed.value),
            }
            
            if parsed.command in commands:
                return commands[parsed.command]()
            else:
                parser.print_help()
                return 1
                
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            print(Colors.error(f"Erreur: {str(e)}"))
            return 1
    
    def _check_for_updates_on_start(self):
        """Vérifier les mises à jour au démarrage"""
        last_check_file = Path.home() / ".zenv" / "last_update_check"
        
        should_check = True
        if last_check_file.exists():
            try:
                last_check = datetime.fromisoformat(last_check_file.read_text().strip())
                hours_since = (datetime.now() - last_check).total_seconds() / 3600
                should_check = hours_since > 24
            except:
                pass
        
        if should_check:
            latest_version = VersionManager.check_update_available()
            if latest_version:
                if VersionManager.prompt_for_update(latest_version):
                    if InstallManager.install_zenv_lang(latest_version):
                        print(Colors.success("Mise à jour terminée ! Redémarrez zenv."))
                        sys.exit(0)
            
            last_check_file.parent.mkdir(exist_ok=True)
            last_check_file.write_text(datetime.now().isoformat())
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Créer le parser d'arguments"""
        parser = argparse.ArgumentParser(
            prog="zenv",
            description=f"Zenv Package Manager v{CURRENT_VERSION}",
            epilog="Documentation: https://zenv-hub.onrender.com"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commandes")
        
        # Commande run
        run_parser = subparsers.add_parser("run", help="Exécuter un fichier")
        run_parser.add_argument("file", help="Fichier .zv ou .py")
        run_parser.add_argument("args", nargs="*", help="Arguments")
        
        # Commande build
        build_parser = subparsers.add_parser("build", help="Construire un package")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifeste")
        build_parser.add_argument("-o", "--output", default="dist", help="Sortie")
        build_parser.add_argument("--name", help="Nom du package")
        build_parser.add_argument("--version", help="Version")
        
        # Commande pkg
        pkg_parser = subparsers.add_parser("pkg", help="Gestion des packages")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command")
        
        install = pkg_sub.add_parser("install", help="Installer")
        install.add_argument("package", help="Nom du package")
        install.add_argument("--version", help="Version")
        
        pkg_sub.add_parser("list", help="Lister")
        
        remove = pkg_sub.add_parser("remove", help="Supprimer")
        remove.add_argument("package", help="Nom")
        
        search = pkg_sub.add_parser("search", help="Rechercher")
        search.add_argument("query", help="Recherche")
        
        # Commande hub
        hub_parser = subparsers.add_parser("hub", help="Zenv Hub")
        hub_sub = hub_parser.add_subparsers(dest="hub_command")
        
        hub_sub.add_parser("status", help="Statut")
        
        login = hub_sub.add_parser("login", help="Connexion")
        login.add_argument("token", help="Token")
        
        hub_sub.add_parser("logout", help="Déconnexion")
        
        hub_search = hub_sub.add_parser("search", help="Recherche")
        hub_search.add_argument("query", help="Terme")
        
        publish = hub_sub.add_parser("publish", help="Publier")
        publish.add_argument("file", help="Fichier")
        
        # Commande version
        subparsers.add_parser("version", help="Version")
        
        # Commande site
        site = subparsers.add_parser("site", help="Installation locale")
        site.add_argument("file", help="Fichier")
        
        # Commande init
        init = subparsers.add_parser("init", help="Nouveau projet")
        init.add_argument("name", help="Nom")
        
        # Commande update
        update = subparsers.add_parser("update", help="Mettre à jour")
        update.add_argument("package", help="Package")
        update.add_argument("--force", action="store_true", help="Forcer")
        
        # Commande info
        info = subparsers.add_parser("info", help="Informations")
        info.add_argument("package", help="Package")
        
        # Commande clean
        subparsers.add_parser("clean", help="Nettoyer")
        
        # Commande config
        config = subparsers.add_parser("config", help="Configuration")
        config_sub = config.add_subparsers(dest="action")
        
        config_sub.add_parser("list", help="Lister")
        
        get = config_sub.add_parser("get", help="Obtenir")
        get.add_argument("key", help="Clé")
        
        set_parser = config_sub.add_parser("set", help="Définir")
        set_parser.add_argument("key", help="Clé")
        set_parser.add_argument("value", help="Valeur")
        
        return parser
    
    # ============================================================================
    # IMPLÉMENTATION DES COMMANDES
    # ============================================================================
    
    def _cmd_run(self, file: str, args: List[str]) -> int:
        if not os.path.exists(file):
            print(Colors.error(f"Fichier introuvable: {file}"))
            return 1
        
        print(Colors.info(f"Exécution: {file}"))
        return self.runtime.execute(file, args)
    
    def _cmd_build(self, parsed) -> int:
        if not os.path.exists(parsed.file):
            print(Colors.error(f"Manifeste introuvable: {parsed.file}"))
            return 1
        
        try:
            with Spinner("Construction..."):
                success = self.builder.build(parsed.file, parsed.output)
            
            if success:
                print(Colors.success("Package construit"))
                return 0
            else:
                print(Colors.error("Échec"))
                return 1
        except Exception as e:
            print(Colors.error(f"Erreur: {str(e)}"))
            return 1
    
    def _cmd_pkg(self, parsed):
        if parsed.pkg_command == "install":
            return self._install_package(parsed.package, parsed.version)
        elif parsed.pkg_command == "list":
            return self._list_packages()
        elif parsed.pkg_command == "remove":
            return self._remove_package(parsed.package)
        elif parsed.pkg_command == "search":
            return self._search_packages(parsed.query)
        else:
            print(Colors.error(f"Commande inconnue: {parsed.pkg_command}"))
            return 1
    
    def _cmd_hub(self, parsed):
        if parsed.hub_command == "status":
            with Spinner("Vérification..."):
                if self.hub.check_status():
                    print(Colors.success("Hub: En ligne"))
                    return 0
                else:
                    print(Colors.error("Hub: Hors ligne"))
                    return 1
        
        elif parsed.hub_command == "login":
            if not parsed.token.startswith('zenv_'):
                print(Colors.error("Token invalide. Doit commencer par 'zenv_'"))
                AuthManager.prompt_for_token()
                return 1
            
            with Spinner("Connexion..."):
                if self.hub.login(parsed.token):
                    print(Colors.success("Connecté"))
                    return 0
                else:
                    print(Colors.error("Échec"))
                    AuthManager.prompt_for_token()
                    return 1
        
        elif parsed.hub_command == "logout":
            self.hub.logout()
            print(Colors.success("Déconnecté"))
            return 0
        
        elif parsed.hub_command == "search":
            if not AuthManager.check_token():
                print(Colors.warning("Authentification requise"))
                AuthManager.prompt_for_token()
                return 1
            
            with Spinner("Recherche..."):
                results = self.hub.search_packages(parsed.query)
            
            if results:
                print(f"\n{Colors.highlight(f'Trouvés: {len(results)}')}")
                for pkg in results:
                    print(f"  • {Colors.color(pkg['name'], Colors.CYAN)} v{pkg.get('version', '?')}")
            else:
                print(Colors.warning("Aucun résultat"))
            return 0
        
        elif parsed.hub_command == "publish":
            if not AuthManager.check_token():
                print(Colors.warning("Authentification requise"))
                AuthManager.prompt_for_token()
                return 1
            
            return self._publish_package(parsed.file)
        
        else:
            print(Colors.error(f"Commande inconnue: {parsed.hub_command}"))
            return 1
    
    def _cmd_version(self):
        print(Colors.highlight(f"Zenv v{CURRENT_VERSION}"))
        return 0
    
    def _cmd_site(self, file: str):
        if not os.path.exists(file):
            print(Colors.error(f"Fichier introuvable: {file}"))
            return 1
        
        return InstallManager._install_package_file(file)
    
    def _cmd_init(self, name: str):
        print(Colors.highlight(f"Création du projet: {name}"))
        Path(name).mkdir(exist_ok=True)
        (Path(name) / "package.zcf").write_text(f"""[Zenv]
name = {name}
version = 1.0.0
""")
        print(Colors.success("Projet créé"))
        return 0
    
    def _cmd_update(self, package: str, force: bool):
        if package == ZENV_LANG_PACKAGE:
            latest = VersionManager.get_latest_version_from_hub()
            if latest:
                return 1 if not InstallManager.install_zenv_lang(latest) else 0
        
        print(Colors.info(f"Mise à jour de {package}"))
        return 0
    
    def _cmd_info(self, package: str):
        print(Colors.highlight(f"Informations: {package}"))
        return 0
    
    def _cmd_clean(self):
        print(Colors.info("Nettoyage..."))
        InstallManager._clean_old_versions()
        print(Colors.success("Nettoyé"))
        return 0
    
    def _cmd_config(self, action: str, key: str, value: str):
        print(Colors.info(f"Configuration: {action}"))
        return 0
    
    # ============================================================================
    # MÉTHODES AUXILIAIRES
    # ============================================================================
    
    def _install_package(self, package: str, version: str = None):
        """Installer un package"""
        print(Colors.highlight(f"Installation: {package}"))
        
        if package == ZENV_LANG_PACKAGE:
            ver = version or VersionManager.get_latest_version_from_hub()
            if ver:
                return 1 if not InstallManager.install_zenv_lang(ver) else 0
        
        if not AuthManager.check_token():
            print(Colors.warning("Authentification requise"))
            AuthManager.prompt_for_token()
            return 1
        
        with Spinner("Téléchargement..."):
            content = self.hub.download_package(package, version or "latest")
        
        if not content:
            print(Colors.error("Package introuvable"))
            return 1
        
        with tempfile.NamedTemporaryFile(suffix='.zv', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            return self._cmd_site(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def _list_packages(self):
        """Lister les packages installés"""
        site_dir = Path("/usr/bin/zenv-site/c82")
        if not site_dir.exists():
            print(Colors.warning("Aucun package installé"))
            return 0
        
        packages = []
        for item in site_dir.iterdir():
            if item.is_dir():
                meta_file = item / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r') as f:
                            meta = json.load(f)
                            packages.append(f"{meta['name']} v{meta.get('version', '?')}")
                    except:
                        packages.append(item.name)
        
        if packages:
            print(Colors.highlight(f"Packages installés ({len(packages)}):"))
            for pkg in packages:
                print(f"  • {pkg}")
        else:
            print(Colors.warning("Aucun package installé"))
        
        return 0
    
    def _remove_package(self, package: str):
        """Supprimer un package"""
        site_dir = Path("/usr/bin/zenv-site/c82") / package
        if not site_dir.exists():
            print(Colors.error(f"Package non trouvé: {package}"))
            return 1
        
        try:
            shutil.rmtree(site_dir)
            print(Colors.success(f"Supprimé: {package}"))
            return 0
        except Exception as e:
            print(Colors.error(f"Erreur: {str(e)}"))
            return 1
    
    def _search_packages(self, query: str):
        """Rechercher des packages"""
        if not AuthManager.check_token():
            print(Colors.warning("Authentification requise"))
            AuthManager.prompt_for_token()
            return 1
        
        with Spinner("Recherche..."):
            results = self.hub.search_packages(query)
        
        if results:
            print(f"\n{Colors.highlight(f'Résultats: {len(results)}')}")
            for pkg in results[:20]:
                desc = pkg.get('description', '')[:60]
                print(f"  • {Colors.color(pkg['name'], Colors.CYAN)} "
                      f"v{pkg.get('version', '?')} - {desc}")
        else:
            print(Colors.warning("Aucun résultat"))
        
        return 0
    
    def _publish_package(self, file: str):
        """Publier un package"""
        if not os.path.exists(file):
            print(Colors.error(f"Fichier introuvable: {file}"))
            return 1
        
        print(Colors.highlight(f"Publication: {os.path.basename(file)}"))
        
        with Spinner("Upload..."):
            success = self.hub.upload_package(file)
        
        if success:
            print(Colors.success("Publié avec succès"))
            return 0
        else:
            print(Colors.error("Échec de publication"))
            return 1

# ============================================================================
# POINT D'ENTRÉE DU SCRIPT
# ============================================================================

def console_script():
    """Point d'entrée pour le script de console"""
    cli = ZenvCLI()
    sys.exit(cli.run(sys.argv[1:]))

if __name__ == "__main__":
    console_script()
