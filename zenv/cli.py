import argparse
import sys
import os
import json
import tarfile
import tempfile
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
        parser = argparse.ArgumentParser(
            prog="zenv",
            description="Zenv Programming Language"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Run command
        run_parser = subparsers.add_parser("run", help="Run Zenv file")
        run_parser.add_argument("file", help=".zv or .zenv file")
        run_parser.add_argument("args", nargs="*", help="Arguments")
        
        # Transpile command
        transpile_parser = subparsers.add_parser("transpile", help="Transpile to Python")
        transpile_parser.add_argument("file", help="Input file")
        transpile_parser.add_argument("-o", "--output", help="Output file")
        
        # Build command
        build_parser = subparsers.add_parser("build", help="Build package")
        build_parser.add_argument("--n", dest="name", help="Package name")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifest file")
        build_parser.add_argument("-o", "--output", default="dist", help="Output directory")
        
        # Package commands
        pkg_parser = subparsers.add_parser("pkg", help="Package management")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command")
        
        install_parser = pkg_sub.add_parser("install", help="Install package")
        install_parser.add_argument("package", help="Package name")
        install_parser.add_argument("--version", default="latest", help="Version")
        
        pkg_sub.add_parser("list", help="List packages")
        
        remove_parser = pkg_sub.add_parser("remove", help="Remove package")
        remove_parser.add_argument("package", help="Package name")
        
        # Hub commands
        hub_parser = subparsers.add_parser("hub", help="Zenv Hub")
        hub_sub = hub_parser.add_subparsers(dest="hub_command")
        
        hub_sub.add_parser("status", help="Check hub status")
        
        login_parser = hub_sub.add_parser("login", help="Login to hub")
        login_parser.add_argument("token", nargs="?", help="Auth token")
        
        hub_sub.add_parser("logout", help="Logout")
        
        search_parser = hub_sub.add_parser("search", help="Search packages")
        search_parser.add_argument("query", help="Search query")
        
        publish_parser = hub_sub.add_parser("publish", help="Publish package")
        publish_parser.add_argument("file", help="Package file")
        
        pull_parser = hub_sub.add_parser("pull", help="Pull package")
        pull_parser.add_argument("package", help="Package name")
        pull_parser.add_argument("--version", default="latest", help="Version")
        
        # Version
        subparsers.add_parser("version", help="Show version")
        
        # Install site
        site_parser = subparsers.add_parser("site", help="Install to site-packages")
        site_parser.add_argument("package", help="Package name or file")
        
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
            return self._cmd_site(parsed.package)
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
            return self._install_package(parsed.package, parsed.version)
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
            token = parsed.token or input("Enter your Zenv Hub token: ")
            if self.hub.login(token):
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
            return self._publish_package(parsed.file)
            
        elif parsed.hub_command == "pull":
            return self._pull_package(parsed.package)
            
        else:
            print(f"❌ Unknown hub command: {parsed.hub_command}")
            return 1
    
    def _cmd_site(self, package: str) -> int:
        """Installer un package dans site-packages"""
        if os.path.exists(package):
            # Local file
            return self._install_from_file(package)
        else:
            # From hub
            return self._pull_and_install(package)
    
    def _install_package(self, package_name: str, version: str) -> int:
        print(f"📦 Installing {package_name}@{version}...")
        
        # Télécharger depuis le hub
        content = self.hub.download_package(package_name, version)
        if not content:
            print(f"❌ Package not found: {package_name}")
            return 1
        
        # Installer dans site-packages
        site_dir = Path("/usr/bin/zenv-site/c82")
        site_dir.mkdir(parents=True, exist_ok=True)
        
        package_dir = site_dir / package_name
        package_dir.mkdir(exist_ok=True)
        
        # Extraire
        with tempfile.NamedTemporaryFile(suffix='.zc.gs', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            with tarfile.open(tmp_path, 'r:gz') as tar:
                tar.extractall(package_dir)
            
            print(f"✅ Installed: {package_name}@{version}")
            print(f"📁 Location: {package_dir}")
            return 0
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
        
        import shutil
        shutil.rmtree(package_dir)
        print(f"✅ Removed: {package_name}")
        return 0
    
    def _publish_package(self, package_file: str) -> int:
        if not self.hub.is_logged_in():
            print("❌ Not logged in. Use: zenv hub login <token>")
            return 1
        
        # Extraire les métadonnées
        try:
            with tarfile.open(package_file, 'r:gz') as tar:
                # Chercher metadata.json
                for member in tar.getmembers():
                    if member.name.endswith('metadata.json'):
                        f = tar.extractfile(member)
                        if f:
                            metadata = json.load(f)
                            name = metadata.get('name', 'unknown')
                            version = metadata.get('version', '1.0.0')
                            description = metadata.get('description', '')
                            
                            if self.hub.upload_package(package_file, name, version, description):
                                return 0
                            else:
                                return 1
        except:
            pass
        
        # Fallback: utiliser le nom du fichier
        filename = os.path.basename(package_file)
        name = filename.split('-')[0] if '-' in filename else filename.replace('.zc.gs', '')
        
        if self.hub.upload_package(package_file, name, '1.0.0', f'Package {name}'):
            return 0
        else:
            return 1
    
    def _pull_package(self, package_name: str) -> int:
        return self._install_package(package_name, "latest")
    
    def _install_from_file(self, file_path: str) -> int:
        """Installer depuis un fichier local"""
        print(f"📦 Installing from file: {file_path}")
        
        site_dir = Path("/usr/bin/zenv-site/c82")
        site_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with tarfile.open(file_path, 'r:gz') as tar:
                # Trouver le nom du package
                package_name = "unknown"
                for member in tar.getmembers():
                    if member.name.endswith('metadata.json'):
                        f = tar.extractfile(member)
                        if f:
                            metadata = json.load(f)
                            package_name = metadata.get('name', 'unknown')
                            break
                
                package_dir = site_dir / package_name
                package_dir.mkdir(exist_ok=True)
                
                tar.extractall(package_dir)
                
                print(f"✅ Installed: {package_name}")
                print(f"📁 Location: {package_dir}")
                return 0
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return 1
    
    def _pull_and_install(self, package_name: str) -> int:
        """Télécharger et installer depuis le hub"""
        return self._install_package(package_name, "latest")
