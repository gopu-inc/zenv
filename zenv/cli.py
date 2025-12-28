import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Optional

from . import __version__
from .transpiler import ZenvTranspiler
from .runtime import ZenvRuntime
from .builder import ZenvBuilder
from .hub.client import ZenvHubClient

class ZenvCLI:
    
    def __init__(self):
        self.transpiler = ZenvTranspiler()
        self.runtime = ZenvRuntime()
        self.builder = ZenvBuilder()
        self.hub = ZenvHubClient()
        
    def run(self, args: List[str]) -> int:
        parser = argparse.ArgumentParser(
            prog="zenv",
            description="Zenv Programming Language - Modern transpiler to Python"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Command")
        
        # Run command
        run_parser = subparsers.add_parser("run", help="Run Zenv code")
        run_parser.add_argument("file", help=".zenv file to execute")
        run_parser.add_argument("args", nargs="*", help="Program arguments")
        
        # Transpile command
        transpile_parser = subparsers.add_parser("transpile", help="Transpile Zenv to Python")
        transpile_parser.add_argument("input", help="Input .zenv file")
        transpile_parser.add_argument("-o", "--output", help="Output .py file")
        
        # Build command
        build_parser = subparsers.add_parser("build", help="Build package")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifest file")
        build_parser.add_argument("-o", "--output", help="Output file")
        
        # Hub commands
        hub_parser = subparsers.add_parser("hub", help="Zenv Hub operations")
        hub_subparsers = hub_parser.add_subparsers(dest="hub_command")
        
        hub_status = hub_subparsers.add_parser("status", help="Check hub status")
        hub_login = hub_subparsers.add_parser("login", help="Login to hub")
        hub_login.add_argument("token", nargs="?", help="Auth token")
        hub_logout = hub_subparsers.add_parser("logout", help="Logout from hub")
        hub_search = hub_subparsers.add_parser("search", help="Search packages")
        hub_search.add_argument("query", help="Search query")
        hub_install = hub_subparsers.add_parser("install", help="Install package")
        hub_install.add_argument("package", help="Package name")
        hub_publish = hub_subparsers.add_parser("publish", help="Publish package")
        hub_publish.add_argument("file", help="Package file")
        
        # Version command
        subparsers.add_parser("version", help="Show version")
        
        # Init command
        init_parser = subparsers.add_parser("init", help="Initialize project")
        init_parser.add_argument("name", help="Project name")
        
        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate syntax")
        validate_parser.add_argument("file", help="File to validate")
        
        # Format command
        format_parser = subparsers.add_parser("format", help="Format code")
        format_parser.add_argument("file", help="File to format")
        format_parser.add_argument("-o", "--output", help="Output file")
        
        if not args:
            parser.print_help()
            return 0
            
        parsed = parser.parse_args(args)
        
        if parsed.command == "run":
            return self._cmd_run(parsed.file, parsed.args)
        elif parsed.command == "transpile":
            return self._cmd_transpile(parsed.input, parsed.output)
        elif parsed.command == "build":
            return self._cmd_build(parsed.file, parsed.output)
        elif parsed.command == "hub":
            return self._cmd_hub(parsed)
        elif parsed.command == "version":
            print(f"Zenv v{__version__}")
            return 0
        elif parsed.command == "init":
            return self._cmd_init(parsed.name)
        elif parsed.command == "validate":
            return self._cmd_validate(parsed.file)
        elif parsed.command == "format":
            return self._cmd_format(parsed.file, parsed.output)
        else:
            parser.print_help()
            return 1
    
    def _cmd_run(self, file: str, args: List[str]) -> int:
        if not os.path.exists(file):
            print(f"Error: File not found: {file}")
            return 1
        
        return self.runtime.execute(file, args)
    
    def _cmd_transpile(self, input_file: str, output_file: Optional[str]) -> int:
        try:
            result = self.transpiler.transpile_file(input_file, output_file)
            if not output_file:
                print(result)
            else:
                print(f"Transpiled: {input_file} -> {output_file}")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_build(self, manifest: str, output: Optional[str]) -> int:
        return self.builder.build_from_manifest(manifest, output)
    
    def _cmd_hub(self, parsed) -> int:
        if parsed.hub_command == "status":
            status = self.hub.check_status()
            print(f"Hub Status: {'Online' if status else 'Offline'}")
            return 0 if status else 1
        elif parsed.hub_command == "login":
            token = parsed.token or input("Enter hub token: ")
            return self.hub.login(token)
        elif parsed.hub_command == "logout":
            self.hub.logout()
            print("Logged out")
            return 0
        elif parsed.hub_command == "search":
            results = self.hub.search(parsed.query)
            for pkg in results:
                print(f"{pkg['name']} v{pkg['version']} - {pkg['description'][:50]}...")
            return 0
        elif parsed.hub_command == "install":
            return self.hub.install_package(parsed.package)
        elif parsed.hub_command == "publish":
            return self.hub.publish_package(parsed.file)
        else:
            print("Unknown hub command")
            return 1
    
    def _cmd_init(self, name: str) -> int:
        project_dir = Path(name)
        project_dir.mkdir(exist_ok=True)
        
        files = {
            "package.zcf": "[Zenv]\nname = my-package\nversion = 0.1.0\nauthor = Your Name\ndescription = A Zenv package\nlicense = MIT\n\n[Files]\nmain = src/main.zenv\n\n[Dependencies]\n",
            "src/main.zenv": 'print "Hello from Zenv!"\n\nfunction hello(name):\n    return "Hello " + name + "!"\n\nif __name__ == "__main__":\n    result = hello("World")\n    print result\n',
            ".zenvignore": "*.pyc\n__pycache__\n*.log\n",
        }
        
        for filename, content in files.items():
            file_path = project_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        print(f"Created project: {name}")
        return 0
    
    def _cmd_validate(self, file: str) -> int:
        try:
            with open(file, 'r') as f:
                content = f.read()
            
            valid, error = self.transpiler.validate(content)
            if valid:
                print(f"✓ Valid syntax: {file}")
                return 0
            else:
                print(f"✗ Invalid syntax: {error}")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _cmd_format(self, file: str, output: Optional[str]) -> int:
        try:
            with open(file, 'r') as f:
                content = f.read()
            
            formatted = self.transpiler.format_code(content)
            
            if output:
                with open(output, 'w') as f:
                    f.write(formatted)
                print(f"Formatted: {file} -> {output}")
            else:
                print(formatted)
            
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
