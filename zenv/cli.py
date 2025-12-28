import argparse
import sys
import os
import json
import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

from . import __version__
from .transpiler import ZenvTranspiler
from .runtime import ZenvRuntime
from .builder import ZenvBuilder
from .utils.hub_client import ZenvHubClient

class ZenvCLI:
    
    def __init__(self):
        self.transpiler = ZenvTranspiler()
        self.runtime = ZenvRuntime()
        self.builder = ZenvBuilder()
        self.hub = ZenvHubClient()
        
    def run(self, args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="zenv")
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Commande run
        run_parser = subparsers.add_parser("run", help="Run Zenv file")
        run_parser.add_argument("file", help=".zv file")
        run_parser.add_argument("args", nargs="*", help="Arguments")
        
        # Commande transpile
        transpile_parser = subparsers.add_parser("transpile", help="Transpile to Python")
        transpile_parser.add_argument("file", help="Input file")
        transpile_parser.add_argument("-o", "--output", help="Output file")
        
        # Commande build
        build_parser = subparsers.add_parser("build", help="Build package")
        build_parser.add_argument("--n", dest="name", help="Package name")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifest file")
        build_parser.add_argument("-o", "--output", default="dist", help="Output directory")
        
        # Commande pkg
        pkg_parser = subparsers.add_parser("pkg", help="Package management")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command")
        
        pkg_sub.add_parser("install", help="Install package").add_argument("package", help="Package name")
        pkg_sub.add_parser("list", help="List packages")
        pkg_sub.add_parser("remove", help="Remove package").add_argument("package", help="Package name")
        
        # Commande hub
        hub_parser = subparsers.add_parser("hub", help="Zenv Hub")
        hub_sub = hub_parser.add_subparsers(dest="hub_command")
        
        hub_sub.add_parser("status", help="Check hub status")
        hub_sub.add_parser("login", help="Login to hub").add_argument("token", help="Auth token")
        hub_sub.add_parser("logout", help="Logout")
        hub_sub.add_parser("search", help="Search packages").add_argument("query", help="Search query")
        hub_sub.add_parser("publish", help="Publish package").add_argument("file", help="Package file")
        
        # Commande version
        subparsers.add_parser("version", help="Show version")
        
        # Commande site (installation locale)
        site_parser = subparsers.add_parser("site", help="Install to site directory")
        site_parser.add_argument("file", help="Package file")
        
        if not args:
            parser.print_help()
            return 0
        
        parsed = parser.parse_args(args)
        
        if parsed.command == "run":
            return self._cmd_run(parsed.file, parsed.args)
        elif parsed.command == "transpile":
            return self._cmd_transpile(parsed.file, parsed.output)
        elif parsed.command == "build":
            return self._cmd_build(parsed.name, parsed.file, parsed.output)
        elif parsed.command == "pkg":
            return self._cmd_pkg(parsed)
        elif parsed.command == "hub":
            return self._cmd_hub(parsed)
        elif parsed.command == "version":
            print(f"Zenv v{__version__}")
            return 0
        elif parsed.command == "site":
            return self._cmd_site(parsed.file)
        else:
            parser.print_help()
            return 1
    
    def _cmd_run(self, file: str, args: List[str]) -> int:
        if not os.path.exists(file):
            print(f"❌ File not found: {file}")
            return 1
        
        return self.runtime.execute(file, args)
    
    def _cmd_transpile(self, file: str, output: Optional[str]) -> int:
        try:
            result = self.transpiler.transpile_file(file, output)
            if not output:
                print(result)
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    def _cmd_build(self, name: Optional[str], manifest: str, output: str) -> int:
        if name:
            # Créer un manifeste simple
            with open("package.zcf", "w") as f:
                f.write(f"""[Zenv]
name = {name}
version = 1.0.0
author = Zenv User
description = A Zenv package

[File-build]
files = *.zv
        *.py
        README.md
        LICENSE*

[docs]
description = README.md

[license]
file = LICENSE*
""")
            manifest = "package.zcf"
        
        result = self.builder.build(manifest, output)
        return 0 if result else 1
    
    def _cmd_pkg(self, parsed):
        if parsed.pkg_command == "install":
            return self._install_package(parsed.package)
        elif parsed.pkg_command == "list":
            return self._list_packages()
        elif parsed.pkg_command == "remove":
            return self._remove_package(parsed.package)
        else:
            print(f"❌ Unknown pkg command: {parsed.pkg_command}")
            return 1
    
    def _cmd_hub(self, parsed):
        if parsed.hub_command == "status":
            if self.hub.check_status():
                print("✅ Zenv Hub: Online")
                return 0
            else:
                print("❌ Zenv Hub: Offline")
                return 1
        elif parsed.hub_command == "login":
            if self.hub.login(parsed.token):
                print("✅ Logged in to Zenv Hub")
                return 0
            else:
                print("❌ Login failed")
                return 1
        elif parsed.hub_command == "logout":
            self.hub.logout()
            print("✅ Logged out")
            return 0
        elif parsed.hub_command == "search":
            results = self.hub.search_packages(parsed.query)
            if results:
                print(f"🔍 Found {len(results)} packages:")
                for pkg in results:
                    print(f"  • {pkg['name']} v{pkg.get('version', '?')} - {pkg.get('description', '')[:50]}")
            else:
                print("🔍 No packages found")
            return 0
        elif parsed.hub_command == "publish":
            if self.hub.upload_package(parsed.file):
                return 0
            else:
                return 1
        else:
            print(f"❌ Unknown hub command: {parsed.hub_command}")
            return 1
    
    def _cmd_site(self, package_file: str) -> int:
        """Installer un package localement"""
        if not os.path.exists(package_file):
            print(f"❌ File not found: {package_file}")
            return 1
        
        print(f"📦 Installing local package: {package_file}")
        
        # Créer le dossier site
        site_dir = Path("/usr/bin/zenv-site/c82")
        site_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extraire le nom du package
            with tarfile.open(package_file, 'r:gz') as tar:
                # Chercher metadata.json
                metadata = None
                for member in tar.getmembers():
                    if member.name.endswith('metadata.json'):
                        f = tar.extractfile(member)
                        if f:
                            metadata = json.load(f)
                            break
                
                if metadata:
                    package_name = metadata.get('name', Path(package_file).stem)
                else:
                    package_name = Path(package_file).stem.replace('.zv', '')
                
                package_dir = site_dir / package_name
                if package_dir.exists():
                    shutil.rmtree(package_dir)
                package_dir.mkdir()
                
                # Extraire
                tar.extractall(package_dir)
                
                print(f"✅ Installed: {package_name}")
                print(f"📁 Location: {package_dir}")
                return 0
                
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return 1
    
    def _install_package(self, package_name: str) -> int:
        print(f"📦 Installing {package_name}...")
        
        # Télécharger depuis le hub
        content = self.hub.download_package(package_name)
        if not content:
            print(f"❌ Package not found: {package_name}")
            return 1
        
        # Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(suffix='.zv', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Installer localement
            return self._cmd_site(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def _list_packages(self) -> int:
        site_dir = Path("/usr/bin/zenv-site/c82")
        if not site_dir.exists():
            print("📦 No packages installed")
            return 0
        
        packages = []
        for item in site_dir.iterdir():
            if item.is_dir():
                meta_file = item / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r') as f:
                            meta = json.load(f)
                            packages.append(meta)
                    except:
                        packages.append({'name': item.name, 'version': 'unknown'})
        
        if packages:
            print(f"📦 Installed packages ({len(packages)}):")
            for pkg in packages:
                print(f"  • {pkg['name']} v{pkg.get('version', '?')}")
        else:
            print("📦 No packages installed")
        
        return 0
    
    def _remove_package(self, package_name: str) -> int:
        site_dir = Path("/usr/bin/zenv-site/c82")
        package_dir = site_dir / package_name
        
        if not package_dir.exists():
            print(f"❌ Package not found: {package_name}")
            return 1
        
        shutil.rmtree(package_dir)
        print(f"✅ Removed: {package_name}")
        return 0
