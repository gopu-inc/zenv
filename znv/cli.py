"""
Interface CLI principale pour znv
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import List

from .runtime import ZenvVirtualMachine, ZenvREPL
from .package_manager import ZenvPackageManager
from .virtualenv import ZenvVirtualEnv
from .builder import ZenvBuilder

class ZenvCLI:
    def __init__(self):
        self.hub_url = "https://zenv-hub.onrender.com"
        self.pm = ZenvPackageManager(self.hub_url)
        self.vm = ZenvVirtualMachine()
        
    def parse_args(self, args: List[str]):
        parser = argparse.ArgumentParser(
            prog="znv",
            description="Runtime Zenv - Écosystème complet",
            usage="znv <command> [options]"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")
        
        # Commande: run
        run_parser = subparsers.add_parser("run", help="Exécuter un fichier")
        run_parser.add_argument("file", help="Fichier .zv ou .py")
        run_parser.add_argument("args", nargs="*", help="Arguments à passer")
        
        # Commande: pkg
        pkg_parser = subparsers.add_parser("pkg", help="Gérer les packages")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command")
        
        pkg_sub.add_parser("list", help="Lister les packages installés")
        
        add_parser = pkg_sub.add_parser("add", help="Installer un package")
        add_parser.add_argument("package", help="Nom du package")
        add_parser.add_argument("--bolt", action="store_true", help="Mode installation rapide")
        add_parser.add_argument("--version", help="Version spécifique")
        
        # Commande: venv
        venv_parser = subparsers.add_parser("venv", help="Créer un environnement virtuel")
        venv_parser.add_argument("name", help="Nom de l'environnement")
        venv_parser.add_argument("--python", help="Version Python")
        
        # Commande: repl
        subparsers.add_parser("repl", help="Mode interactif")
        
        # Commande: version
        subparsers.add_parser("version", help="Afficher la version")
        
        # Commande: hub
        hub_parser = subparsers.add_parser("hub", help="Interagir avec le hub")
        hub_sub = hub_parser.add_subparsers(dest="hub_command")
        hub_sub.add_parser("status", help="Vérifier le statut du hub")
        
        if not args:
            parser.print_help()
            return None
            
        return parser.parse_args(args)
    
    def run(self, parsed_args):
        if parsed_args.command == "run":
            return self.vm.execute_file(parsed_args.file, parsed_args.args)
        elif parsed_args.command == "pkg":
            if parsed_args.pkg_command == "list":
                return self.pm.list_packages()
            elif parsed_args.pkg_command == "add":
                return self.pm.install_package(
                    parsed_args.package,
                    version=parsed_args.version,
                    fast=parsed_args.bolt
                )
        elif parsed_args.command == "venv":
            venv = ZenvVirtualEnv(parsed_args.name)
            return venv.create(python_version=parsed_args.python)
        elif parsed_args.command == "repl":
            repl = ZenvREPL()
            repl.start()
            return 0
        elif parsed_args.command == "version":
            print("Zenv Runtime v1.0.0")
            return 0
        elif parsed_args.command == "hub":
            if parsed_args.hub_command == "status":
                status = self.pm.check_hub_status()
                print(f"Hub: {self.hub_url}")
                print(f"Statut: {'✅ En ligne' if status else '❌ Hors ligne'}")
                return 0
        
        return 1

def main():
    cli = ZenvCLI()
    args = cli.parse_args(sys.argv[1:])
    
    if args is None:
        return 0
        
    try:
        return cli.run(args)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        if os.environ.get('ZENV_DEBUG'):
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
