import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

from . import __version__
from .transpiler import ZenvTranspiler
from .runtime import ZenvRuntime
from .builder import ZenvBuilder
from .utils.package_manager import PackageManager

class ZenvCLI:
    
    def __init__(self):
        self.transpiler = ZenvTranspiler()
        self.runtime = ZenvRuntime()
        self.builder = ZenvBuilder()
        self.pkg_manager = PackageManager()
        
    def run(self, args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="zenv")
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # Run command
        run_parser = subparsers.add_parser("run", help="Run Zenv file or package")
        run_parser.add_argument("target", help="File or package name")
        run_parser.add_argument("-p", "--package", action="store_true", help="Run as package")
        run_parser.add_argument("args", nargs="*", help="Arguments")
        
        # Transpile command
        transpile_parser = subparsers.add_parser("transpile", help="Transpile Zenv to Python")
        transpile_parser.add_argument("file", help="Input file")
        transpile_parser.add_argument("-o", "--output", help="Output file")
        
        # Build command
        build_parser = subparsers.add_parser("build", help="Build package")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifest file")
        build_parser.add_argument("-n", "--name", help="Package name")
        build_parser.add_argument("-o", "--output", default="dist", help="Output directory")
        
        # Package commands
        pkg_parser = subparsers.add_parser("pkg", help="Package management")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command")
        
        pkg_sub.add_parser("install", help="Install package").add_argument("package", help="Package name")
        pkg_sub.add_parser("remove", help="Remove package").add_argument("package", help="Package name")
        pkg_sub.add_parser("list", help="List installed packages")
        pkg_sub.add_parser("search", help="Search packages").add_argument("query", help="Search query")
        
        # Pull command
        pull_parser = subparsers.add_parser("pull", help="Pull package from hub")
        pull_parser.add_argument("package", help="Package name")
        pull_parser.add_argument("--version", default="latest", help="Version")
        
        # Publish command
        pub_parser = subparsers.add_parser("publish", help="Publish to hub")
        pub_parser.add_argument("file", help="Package file")
        
        # Version
        subparsers.add_parser("version", help="Show version")
        
        if not args:
            parser.print_help()
            return 0
        
        parsed = parser.parse_args(args)
        
        if parsed.command == "run":
            return self._cmd_run(parsed)
        elif parsed.command == "transpile":
            return self._cmd_transpile(parsed.file, parsed.output)
        elif parsed.command == "build":
            return self._cmd_build(parsed.file, parsed.name, parsed.output)
        elif parsed.command == "pkg":
            return self._cmd_pkg(parsed)
        elif parsed.command == "pull":
            return self._cmd_pull(parsed.package, parsed.version)
        elif parsed.command == "publish":
            return self._cmd_publish(parsed.file)
        elif parsed.command == "version":
            print(f"Zenv v{__version__}")
            return 0
        else:
            parser.print_help()
            return 1
    
    def _cmd_run(self, parsed):
        if parsed.package:
            # Run package
            return self._run_package(parsed.target, parsed.args)
        else:
            # Run file
            return self.runtime.execute(parsed.target, parsed.args)
    
    def _run_package(self, package_name: str, args: List[str]) -> int:
        package_dir = Path("/usr/bin/zenv-site/c82") / package_name
        
        if not package_dir.exists():
            print(f"❌ Package not installed: {package_name}")
            return 1
        
        # Look for main file
        main_files = list(package_dir.glob("main.py")) + list(package_dir.glob("main.zv"))
        
        if not main_files:
            print(f"❌ No main file found in package: {package_name}")
            return 1
        
        main_file = main_files[0]
        
        if main_file.suffix == '.zv':
            # Transpile and run
            python_code = self.transpiler.transpile_file(str(main_file))
            with open("/tmp/zenv_temp.py", "w") as f:
                f.write(python_code)
            import subprocess
            result = subprocess.run([sys.executable, "/tmp/zenv_temp.py"] + args)
            return result.returncode
        else:
            # Run Python directly
            import subprocess
            result = subprocess.run([sys.executable, str(main_file)] + args)
            return result.returncode
    
    def _cmd_build(self, manifest: str, name: Optional[str], output: str) -> int:
        if name:
            # Create minimal manifest
            with open("package.zcf", "w") as f:
                f.write(f"""[Zenv]
name = {name}
version = 1.0.0

[File-build]
files = *.zv
        *.py
        README.md
        LICENSE*
""")
            manifest = "package.zcf"
        
        result = self.builder.build(manifest, output)
        return 0 if result else 1
    
    def _cmd_pkg(self, parsed):
        if parsed.pkg_command == "install":
            return 0 if self.pkg_manager.install(parsed.package) else 1
        elif parsed.pkg_command == "remove":
            return 0 if self.pkg_manager.remove(parsed.package) else 1
        elif parsed.pkg_command == "list":
            packages = self.pkg_manager.list_packages()
            for pkg in packages:
                print(f"• {pkg['name']} v{pkg.get('version', '?')}")
            return 0
        elif parsed.pkg_command == "search":
            results = self.pkg_manager.search_hub(parsed.query)
            for pkg in results:
                print(f"• {pkg['name']} v{pkg.get('version', '?')}")
            return 0
    
    def _cmd_pull(self, package: str, version: str) -> int:
        return 0 if self.pkg_manager.install(package, version) else 1
    
    def _cmd_publish(self, file: str) -> int:
        return 0 if self.pkg_manager.publish(file) else 1
    
    def _cmd_transpile(self, input_file: str, output_file: Optional[str]) -> int:
        try:
            result = self.transpiler.transpile_file(input_file, output_file)
            if not output_file:
                print(result)
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
