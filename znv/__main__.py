# znv/__main__.py
"""
Point d'entrée principal du runtime Zenv
"""

import sys
import os
import argparse
import json
import subprocess
from pathlib import Path
from typing import List, Optional

from .runtime import ZenvVirtualMachine
from .package_manager import ZenvPackageManager
from .virtualenv import ZenvVirtualEnv
from .builder import ZenvBuilder
from .cache import ZenvCache

class ZenvCLI:
    """Interface CLI complète de Zenv"""
    
    def __init__(self):
        self.hub_url = "https://zenv-hub.onrender.com"
        self.cache = ZenvCache()
        self.pm = ZenvPackageManager(self.hub_url)
        self.vm = ZenvVirtualMachine()
        self.builder = ZenvBuilder()
        
    def run(self, args: List[str]) -> int:
        parser = argparse.ArgumentParser(
            prog="znv",
            description="Runtime Zenv - Écosystème complet",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Groupes de commandes
        subparsers = parser.add_subparsers(dest="command", help="Commandes")
        
        # === EXÉCUTION ===
        exec_parser = subparsers.add_parser("run", help="Exécuter un fichier")
        exec_parser.add_argument("file", help="Fichier .zv/.py")
        exec_parser.add_argument("args", nargs="*", help="Arguments")
        
        # === PACKAGES ===
        pkg_parser = subparsers.add_parser("pkg", help="Gestion des packages")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command")
        
        # Installer
        install = pkg_sub.add_parser("add", help="Installer un package")
        install.add_argument("package", help="Nom du package")
        install.add_argument("--bolt", action="store_true", help="Mode rapide")
        install.add_argument("--version", help="Version spécifique")
        
        # Supprimer
        remove = pkg_sub.add_parser("remove", help="Supprimer un package")
        remove.add_argument("package", help="Nom du package")
        
        # Lister
        list_cmd = pkg_sub.add_parser("list", help="Lister les packages")
        
        # Rechercher
        search = pkg_sub.add_parser("search", help="Rechercher un package")
        search.add_argument("query", help="Terme de recherche")
        
        # === BUILD ===
        build_parser = subparsers.add_parser("build", help="Compiler")
        build_parser.add_argument("-d", "--directory", help="Dossier source")
        build_parser.add_argument("-o", "--output", help="Fichier de sortie")
        build_parser.add_argument("--build-system", choices=["zenv", "python"], default="zenv")
        
        # === VENV ===
        venv_parser = subparsers.add_parser("venv", help="Environnements virtuels")
        venv_parser.add_argument("name", help="Nom de l'environnement")
        venv_parser.add_argument("--python", help="Version Python")
        venv_parser.add_argument("--system-site", action="store_true", help="Utiliser site-packages système")
        
        # === CACHE ===
        cache_parser = subparsers.add_parser("cache", help="Gestion du cache")
        cache_sub = cache_parser.add_subparsers(dest="cache_command")
        cache_sub.add_parser("clear", help="Vider le cache")
        cache_sub.add_parser("stats", help="Statistiques cache")
        
        # === SERVEUR ===
        server_parser = subparsers.add_parser("hub", help="Gestion du hub")
        server_sub = server_parser.add_subparsers(dest="hub_command")
        server_sub.add_parser("status", help="Statut du hub")
        upload = server_sub.add_parser("upload", help="Uploader un package")
        upload.add_argument("package", help="Fichier .zv ou dossier")
        
        # === REPL ===
        subparsers.add_parser("repl", help="Lancer le REPL interactif")
        
        # === INFOS ===
        info_parser = subparsers.add_parser("info", help="Informations système")
        info_parser.add_argument("package", nargs="?", help="Package spécifique")
        
        args = parser.parse_args(args)
        
        if not args.command:
            parser.print_help()
            return 0
        
        # Dispatch des commandes
        commands = {
            "run": self.cmd_run,
            "pkg": self.cmd_pkg,
            "build": self.cmd_build,
            "venv": self.cmd_venv,
            "cache": self.cmd_cache,
            "hub": self.cmd_hub,
            "repl": self.cmd_repl,
            "info": self.cmd_info,
        }
        
        return commands.get(args.command, self.cmd_unknown)(args)
    
    def cmd_run(self, args) -> int:
        """Exécuter un fichier"""
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Fichier non trouvé: {args.file}")
            return 1
        
        return self.vm.execute_file(str(file_path), args.args)
    
    def cmd_pkg(self, args) -> int:
        """Gestion des packages"""
        if args.pkg_command == "add":
            return self.pm.install_package(
                args.package, 
                version=args.version,
                fast=args.bolt
            )
        elif args.pkg_command == "remove":
            return self.pm.remove_package(args.package)
        elif args.pkg_command == "list":
            return self.pm.list_packages()
        elif args.pkg_command == "search":
            return self.pm.search_packages(args.query)
        return 0
    
    def cmd_build(self, args) -> int:
        """Compiler un package"""
        source_dir = args.directory or "."
        return self.builder.build(
            source_dir,
            output=args.output,
            build_system=args.build_system
        )
    
    def cmd_venv(self, args) -> int:
        """Créer un environnement virtuel"""
        venv = ZenvVirtualEnv(args.name)
        return venv.create(
            python_version=args.python,
            system_site_packages=args.system_site
        )
    
    def cmd_cache(self, args) -> int:
        """Gestion du cache"""
        if args.cache_command == "clear":
            return self.cache.clear()
        elif args.cache_command == "stats":
            return self.cache.stats()
        return 0
    
    def cmd_hub(self, args) -> int:
        """Interaction avec le hub"""
        if args.hub_command == "status":
            status = self.pm.hub_status()
            print(f"Hub: {self.hub_url}")
            print(f"Statut: {'✅ En ligne' if status else '❌ Hors ligne'}")
            return 0
        elif args.hub_command == "upload":
            return self.pm.upload_package(args.package)
        return 0
    
    def cmd_repl(self, args) -> int:
        """Lancer le REPL"""
        from .runtime import ZenvREPL
        repl = ZenvREPL()
        repl.start()
        return 0
    
    def cmd_info(self, args) -> int:
        """Informations système"""
        print("=== Zenv Runtime ===")
        print(f"Version: {self.vm.version}")
        print(f"Cache: {self.cache.get_path()}")
        print(f"Packages: {len(self.pm.list_installed())}")
        print(f"Hub: {self.hub_url}")
        
        if args.package:
            pkg_info = self.pm.get_package_info(args.package)
            if pkg_info:
                print(f"\n=== Package: {args.package} ===")
                print(f"Version: {pkg_info.get('version', 'N/A')}")
                print(f"Auteur: {pkg_info.get('author', 'N/A')}")
                print(f"Description: {pkg_info.get('description', 'N/A')}")
        return 0
    
    def cmd_unknown(self, args) -> int:
        print("Commande inconnue")
        return 1


def main():
    cli = ZenvCLI()
    sys.exit(cli.run(sys.argv[1:]))


if __name__ == "__main__":
    main()
