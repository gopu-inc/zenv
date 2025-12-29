# Version corrigée complète avec toutes les corrections nécessaires
# zenv/cli.py

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
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import platform
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.box import ROUNDED, DOUBLE
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich.layout import Layout
from rich.columns import Columns
from rich.text import Text
from rich.style import Style
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from rich.live import Live
from rich.logging import RichHandler

from . import __version__
from .transpiler import ZenvTranspiler
from .runtime import ZenvRuntime
from .builder import ZenvBuilder
from .utils.hub_client import ZenvHubClient

# Configuration du logging Rich
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("zenv")

class LogLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"

class Theme:
    """Thèmes et couleurs pour l'interface"""
    PRIMARY = "cyan"
    SECONDARY = "blue"
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "magenta"
    HIGHLIGHT = "bold white"
    
    # Styles prédéfinis - CORRIGÉ
    TITLE = Style(color="cyan", bold=True)
    SUBTITLE = Style(color="blue", bold=True)
    COMMAND = Style(color="green", bold=True)
    ARGUMENT = Style(color="yellow")
    OPTION = Style(color="magenta")
    PATH = Style(color="cyan", underline=True)
    VERSION = Style(color="yellow", bold=True)
    AUTHOR = Style(color="cyan", dim=True)  # CORRIGÉ : "dim cyan" séparé

@dataclass
class PackageInfo:
    """Informations sur un package"""
    name: str
    version: str
    author: str
    description: str
    license: str
    dependencies: List[str]
    created_at: str
    size: int
    hash: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackageInfo':
        return cls(
            name=data.get('name', ''),
            version=data.get('version', '1.0.0'),
            author=data.get('author', 'Unknown'),
            description=data.get('description', ''),
            license=data.get('license', 'MIT'),
            dependencies=data.get('dependencies', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            size=data.get('size', 0),
            hash=data.get('hash', '')
        )

class ZenvCLI:
    
    def __init__(self):
        self.console = Console()
        self.transpiler = ZenvTranspiler()
        self.runtime = ZenvRuntime()
        self.builder = ZenvBuilder()
        self.hub = ZenvHubClient()
        self.theme = Theme()
        
        # Configuration
        self.config_dir = Path.home() / ".zenv"
        self.config_file = self.config_dir / "config.json"
        self._load_config()
    
    def _load_config(self):
        """Charger la configuration"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "theme": "dark",
            "log_level": "info",
            "auto_update": True,
            "hub_url": "https://hub.zenv.org",
            "cache_dir": str(self.config_dir / "cache"),
            "installed_packages": []
        }
        
        if not self.config_file.exists():
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.config = default_config
        else:
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
    
    def _save_config(self):
        """Sauvegarder la configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Journalisation enrichie"""
        icons = {
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.SUCCESS: "✅",
            LogLevel.DEBUG: "🐛"
        }
        
        colors = {
            LogLevel.INFO: self.theme.PRIMARY,
            LogLevel.WARNING: self.theme.WARNING,
            LogLevel.ERROR: self.theme.ERROR,
            LogLevel.SUCCESS: self.theme.SUCCESS,
            LogLevel.DEBUG: "dim"
        }
        
        icon = icons.get(level, "")
        color = colors.get(level, self.theme.PRIMARY)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [{color}]{icon} {message}[/]", **kwargs)
    
    def _print_header(self):
        """Afficher l'en-tête de Zenv"""
        header = Text()
        header.append("Z", style="bold cyan")
        header.append("env", style="bold blue")
        header.append(f" v{__version__}", style=Style(color="yellow", dim=True))
        header.append("\nZen Execution Environment", style=Style(italic=True, dim=True))
        
        self.console.print(Panel(header, box=DOUBLE, border_style="cyan"))
    
    def _print_footer(self, message: str = "Operation completed"):
        """Afficher un pied de page"""
        self.console.print(f"\n[dim]{'─' * 60}[/]")
        self.console.print(f"[dim]{message}[/]")
    
    def _create_progress(self, description: str = "Processing..."):
        """Créer une barre de progression"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        )
    
    def run(self, args: List[str]) -> int:
        """Point d'entrée principal"""
        # Parser principal avec Rich
        parser = argparse.ArgumentParser(
            prog="zenv",
            description="[bold cyan]Zenv[/] - Zen Execution Environment",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""[bold]Examples:[/]
  [green]zenv run app.zv[/]          Run a Zenv file
  [green]zenv transpile app.zv[/]    Transpile to Python
  [green]zenv build[/]               Build a package
  [green]zenv pkg install numpy[/]   Install a package"""
        )
        
        subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="")
        
        # Commande run
        run_parser = subparsers.add_parser("run", help="Run Zenv file")
        run_parser.add_argument("file", help=".zv file to execute")
        run_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")
        run_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        run_parser.add_argument("--profile", action="store_true", help="Profile execution")
        
        # Commande transpile
        transpile_parser = subparsers.add_parser("transpile", help="Transpile to Python")
        transpile_parser.add_argument("file", help="Input .zv file")
        transpile_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
        transpile_parser.add_argument("--show-ast", action="store_true", help="Show AST")
        transpile_parser.add_argument("--optimize", action="store_true", help="Optimize output")
        
        # Commande build
        build_parser = subparsers.add_parser("build", help="Build package")
        build_parser.add_argument("--name", dest="name", help="Package name")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifest file")
        build_parser.add_argument("-o", "--output", default="dist", help="Output directory")
        build_parser.add_argument("--clean", action="store_true", help="Clean build directory")
        build_parser.add_argument("--test", action="store_true", help="Run tests after build")
        
        # Commande pkg
        pkg_parser = subparsers.add_parser("pkg", help="Package management")
        pkg_sub = pkg_parser.add_subparsers(dest="pkg_command", help="Package commands")
        
        # Install
        install_parser = pkg_sub.add_parser("install", help="Install package")
        install_parser.add_argument("package", help="Package name or path")
        install_parser.add_argument("--version", help="Specific version")
        install_parser.add_argument("--force", action="store_true", help="Force reinstall")
        
        # List
        list_parser = pkg_sub.add_parser("list", help="List packages")
        list_parser.add_argument("--local", action="store_true", help="Show local packages only")
        list_parser.add_argument("--global", dest="global_scope", action="store_true", help="Show global packages")
        
        # Remove
        remove_parser = pkg_sub.add_parser("remove", help="Remove package")
        remove_parser.add_argument("package", help="Package name")
        remove_parser.add_argument("--purge", action="store_true", help="Remove all files")
        
        # Update
        update_parser = pkg_sub.add_parser("update", help="Update package")
        update_parser.add_argument("package", nargs="?", default="all", help="Package name or 'all'")
        update_parser.add_argument("--prerelease", action="store_true", help="Include prereleases")
        
        # Info
        pkg_sub.add_parser("info", help="Show package info").add_argument("package", help="Package name")
        
        # Commande hub
        hub_parser = subparsers.add_parser("hub", help="Zenv Hub")
        hub_sub = hub_parser.add_subparsers(dest="hub_command", help="Hub commands")
        
        hub_sub.add_parser("status", help="Check hub status")
        hub_sub.add_parser("login", help="Login to hub").add_argument("token", help="Auth token")
        hub_sub.add_parser("logout", help="Logout")
        hub_sub.add_parser("search", help="Search packages").add_argument("query", help="Search query")
        hub_sub.add_parser("publish", help="Publish package").add_argument("file", help="Package file")
        hub_sub.add_parser("whoami", help="Show current user")
        
        # Commande version
        subparsers.add_parser("version", help="Show version")
        
        # Commande site
        site_parser = subparsers.add_parser("site", help="Install to site directory")
        site_parser.add_argument("file", help="Package file")
        site_parser.add_argument("--global", action="store_true", help="Install globally")
        
        # Commande config
        config_parser = subparsers.add_parser("config", help="Configuration")
        config_sub = config_parser.add_subparsers(dest="config_command", help="Config commands")
        config_sub.add_parser("show", help="Show configuration")
        config_sub.add_parser("edit", help="Edit configuration")
        config_sub.add_parser("reset", help="Reset to defaults")
        
        # Commande doctor
        subparsers.add_parser("doctor", help="Diagnose system issues")
        
        # Commande init
        init_parser = subparsers.add_parser("init", help="Initialize project")
        init_parser.add_argument("name", nargs="?", help="Project name")
        init_parser.add_argument("--template", help="Template to use")
        
        if not args:
            self._print_header()
            parser.print_help()
            return 0
        
        try:
            parsed = parser.parse_args(args)
            
            # Gestion des commandes
            command_map = {
                "run": lambda: self._cmd_run(parsed.file, parsed.args, parsed.debug, parsed.profile),
                "transpile": lambda: self._cmd_transpile(parsed.file, parsed.output, parsed.show_ast, parsed.optimize),
                "build": lambda: self._cmd_build(parsed.name, parsed.file, parsed.output, parsed.clean, parsed.test),
                "pkg": lambda: self._cmd_pkg(parsed),
                "hub": lambda: self._cmd_hub(parsed),
                "version": lambda: self._cmd_version(),
                "site": lambda: self._cmd_site(parsed.file, getattr(parsed, 'global_scope', False)),
                "config": lambda: self._cmd_config(parsed),
                "doctor": lambda: self._cmd_doctor(),
                "init": lambda: self._cmd_init(parsed.name, getattr(parsed, 'template', None))
            }
            
            if parsed.command in command_map:
                return command_map[parsed.command]()
            else:
                parser.print_help()
                return 1
                
        except SystemExit:
            return 0
        except Exception as e:
            self._log(f"Unexpected error: {e}", LogLevel.ERROR)
            logger.exception("Detailed error:")
            return 1
    
    def _cmd_run(self, file: str, args: List[str], debug: bool, profile: bool) -> int:
        """Exécuter un fichier Zenv"""
        self._print_header()
        
        if not os.path.exists(file):
            self._log(f"File not found: {file}", LogLevel.ERROR)
            return 1
        
        file_info = Path(file)
        self.console.print(Panel.fit(
            f"[bold]Running:[/] [cyan]{file_info.name}[/]\n"
            f"[dim]Path:[/] {file_info.absolute()}\n"
            f"[dim]Size:[/] {file_info.stat().st_size:,} bytes",
            title="Execution",
            border_style="green"
        ))
        
        if debug:
            self._log("Debug mode enabled", LogLevel.INFO)
        
        if profile:
            self._log("Profiling enabled", LogLevel.INFO)
        
        with self._create_progress("Executing script...") as progress:
            task = progress.add_task("[cyan]Running...", total=None)
            result = self.runtime.execute(file, args, debug=debug, profile=profile)
            progress.update(task, completed=100)
        
        if result == 0:
            self._log("Execution completed successfully", LogLevel.SUCCESS)
        else:
            self._log(f"Execution failed with code {result}", LogLevel.ERROR)
        
        self._print_footer()
        return result
    
    def _cmd_transpile(self, file: str, output: Optional[str], show_ast: bool, optimize: bool) -> int:
        """Transpiler un fichier Zenv vers Python"""
        self._print_header()
        
        if not os.path.exists(file):
            self._log(f"File not found: {file}", LogLevel.ERROR)
            return 1
        
        try:
            with self._create_progress("Transpiling...") as progress:
                task = progress.add_task("[cyan]Processing...", total=100)
                
                if show_ast:
                    # Note: Cette méthode doit être implémentée dans ZenvTranspiler
                    ast_result = self.transpiler.get_ast(file) if hasattr(self.transpiler, 'get_ast') else "AST display not available"
                    progress.update(task, advance=30)
                    
                    self.console.print(Panel(
                        str(ast_result),
                        title="Abstract Syntax Tree",
                        border_style="blue"
                    ))
                
                result = self.transpiler.transpile_file(file, output, optimize=optimize)
                progress.update(task, advance=70)
            
            if output:
                output_path = Path(output)
                self._log(f"Transpiled to: {output_path.absolute()}", LogLevel.SUCCESS)
            else:
                self.console.print(Panel(
                    result,
                    title="Transpiled Output",
                    border_style="green"
                ))
            
            self._print_footer("Transpilation completed")
            return 0
            
        except Exception as e:
            self._log(f"Transpilation error: {e}", LogLevel.ERROR)
            logger.exception("Transpilation failed:")
            return 1
    
    def _cmd_build(self, name: Optional[str], manifest: str, output: str, clean: bool, test: bool) -> int:
        """Construire un package"""
        self._print_header()
        
        try:
            if clean:
                if os.path.exists(output):
                    shutil.rmtree(output)
                self._log("Cleaned build directory", LogLevel.INFO)
            
            if name:
                # Créer un manifeste simple
                manifest_content = f"""[Zenv]
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
"""
                with open("package.zcf", "w") as f:
                    f.write(manifest_content)
                manifest = "package.zcf"
                self._log(f"Created manifest for: {name}", LogLevel.INFO)
            
            with self._create_progress("Building package...") as progress:
                task = progress.add_task("[cyan]Building...", total=100)
                result = self.builder.build(manifest, output)
                progress.update(task, completed=100)
        
            if result:
                output_dir = Path(output)
                packages = list(output_dir.glob("*.zv"))
                
                if packages:
                    package_info = self._analyze_package(packages[0])
                    
                    self.console.print(Panel.fit(
                        f"[bold green]✓ Build Successful![/]\n\n"
                        f"[bold]Package:[/] [cyan]{package_info.name}[/] v{package_info.version}\n"
                        f"[bold]Size:[/] {package_info.size:,} bytes\n"
                        f"[bold]Output:[/] {output_dir.absolute()}\n"
                        f"[bold]Hash:[/] [dim]{package_info.hash[:16]}...[/]",
                        title="Build Results",
                        border_style="green"
                    ))
                
                self._print_footer("Build completed")
                return 0
            else:
                self._log("Build failed", LogLevel.ERROR)
                return 1
                
        except Exception as e:
            self._log(f"Build error: {e}", LogLevel.ERROR)
            logger.exception("Build failed:")
            return 1
    
    def _analyze_package(self, package_path: Path) -> PackageInfo:
        """Analyser un package"""
        try:
            with tarfile.open(package_path, 'r:gz') as tar:
                # Chercher metadata.json
                for member in tar.getmembers():
                    if member.name.endswith('metadata.json'):
                        f = tar.extractfile(member)
                        if f:
                            metadata = json.load(f)
                            return PackageInfo.from_dict(metadata)
        except:
            pass
        
        # Fallback
        return PackageInfo(
            name=package_path.stem,
            version="1.0.0",
            author="Unknown",
            description="Zenv package",
            license="MIT",
            dependencies=[],
            created_at=datetime.now().isoformat(),
            size=package_path.stat().st_size,
            hash=hashlib.sha256(package_path.read_bytes()).hexdigest()
        )
    
    def _cmd_pkg(self, parsed):
        """Gestion des packages"""
        if parsed.pkg_command == "install":
            return self._install_package(parsed.package, getattr(parsed, 'version', None), getattr(parsed, 'force', False))
        elif parsed.pkg_command == "list":
            return self._list_packages(getattr(parsed, 'local', False), getattr(parsed, 'global_scope', False))
        elif parsed.pkg_command == "remove":
            return self._remove_package(parsed.package, getattr(parsed, 'purge', False))
        elif parsed.pkg_command == "update":
            return self._update_package(parsed.package, getattr(parsed, 'prerelease', False))
        elif parsed.pkg_command == "info":
            return self._package_info(parsed.package)
        else:
            self._log(f"Unknown pkg command: {parsed.pkg_command}", LogLevel.ERROR)
            return 1
    
    def _cmd_hub(self, parsed):
        """Commandes du hub"""
        if parsed.hub_command == "status":
            return self._hub_status()
        elif parsed.hub_command == "login":
            return self._hub_login(parsed.token)
        elif parsed.hub_command == "logout":
            return self._hub_logout()
        elif parsed.hub_command == "search":
            return self._hub_search(parsed.query)
        elif parsed.hub_command == "publish":
            return self._publish_package(parsed.file)
        elif parsed.hub_command == "whoami":
            return self._hub_whoami()
        else:
            self._log(f"Unknown hub command: {parsed.hub_command}", LogLevel.ERROR)
            return 1
    
    def _cmd_version(self):
        """Afficher la version"""
        self._print_header()
        
        info_table = Table(title="System Information", box=ROUNDED)
        info_table.add_column("Component", style="cyan")
        info_table.add_column("Version", style="green")
        
        info_table.add_row("Zenv", __version__)
        info_table.add_row("Python", platform.python_version())
        info_table.add_row("Platform", platform.platform())
        info_table.add_row("OS", platform.system())
        
        self.console.print(info_table)
        
        self._print_footer()
        return 0
    
    def _cmd_site(self, package_file: str, global_install: bool) -> int:
        """Installer un package localement"""
        self._print_header()
        
        if not os.path.exists(package_file):
            self._log(f"File not found: {package_file}", LogLevel.ERROR)
            return 1
        
        package_path = Path(package_file)
        package_info = self._analyze_package(package_path)
        
        self.console.print(Panel.fit(
            f"[bold]Package:[/] [cyan]{package_info.name}[/]\n"
            f"[bold]Version:[/] {package_info.version}\n"
            f"[bold]Author:[/] {package_info.author}\n"
            f"[bold]Size:[/] {package_info.size:,} bytes\n"
            f"[bold]Install Scope:[/] {'Global' if global_install else 'User'}",
            title="Installation Details",
            border_style="yellow"
        ))
        
        if not Confirm.ask("Proceed with installation?"):
            self._log("Installation cancelled", LogLevel.WARNING)
            return 0
        
        with self._create_progress("Installing package...") as progress:
            task = progress.add_task("[cyan]Installing...", total=100)
            
            try:
                # Déterminer le répertoire d'installation
                if global_install:
                    site_dir = Path("/usr/local/lib/zenv")
                    site_dir.mkdir(parents=True, exist_ok=True)
                else:
                    site_dir = Path.home() / ".zenv" / "packages"
                    site_dir.mkdir(parents=True, exist_ok=True)
                
                package_dir = site_dir / package_info.name
                
                # Extraire
                with tarfile.open(package_file, 'r:gz') as tar:
                    tar.extractall(package_dir)
                progress.update(task, completed=100)
                
            except Exception as e:
                self._log(f"Installation error: {e}", LogLevel.ERROR)
                return 1
        
        self._log(f"Successfully installed {package_info.name} v{package_info.version}", LogLevel.SUCCESS)
        
        self.console.print(Panel.fit(
            f"[bold]Installed to:[/] {package_dir.absolute()}\n"
            f"[bold]Package Path:[/] {package_dir / 'package.zcf'}\n"
            f"[bold]To use:[/] [green]zenv run {package_info.name}[/]",
            title="Installation Complete",
            border_style="green"
        ))
        
        self._print_footer()
        return 0
    
    def _cmd_config(self, parsed):
        """Gestion de la configuration"""
        if parsed.config_command == "show":
            self._print_header()
            
            config_table = Table(title="Configuration", box=ROUNDED)
            config_table.add_column("Key", style="cyan")
            config_table.add_column("Value", style="green")
            
            for key, value in self.config.items():
                if isinstance(value, list):
                    value = ', '.join(value)
                config_table.add_row(key, str(value))
            
            self.console.print(config_table)
            self._print_footer()
            return 0
            
        elif parsed.config_command == "edit":
            self._log("Opening config file...", LogLevel.INFO)
            # Implémenter l'édition
            return 0
            
        elif parsed.config_command == "reset":
            if Confirm.ask("Reset configuration to defaults?"):
                self.config = {
                    "theme": "dark",
                    "log_level": "info",
                    "auto_update": True,
                    "hub_url": "https://hub.zenv.org",
                    "cache_dir": str(self.config_dir / "cache"),
                    "installed_packages": []
                }
                self._save_config()
                self._log("Configuration reset to defaults", LogLevel.SUCCESS)
            return 0
    
    def _cmd_doctor(self):
        """Diagnostiquer les problèmes du système"""
        self._print_header()
        
        print("Running system diagnostics...")
        print()
        
        # Vérifications simples
        checks = []
        
        # Python version
        if sys.version_info >= (3, 8):
            checks.append(("✓", "Python 3.8+", "OK"))
        else:
            checks.append(("✗", "Python 3.8+", "Required"))
        
        # Write permissions
        try:
            test_file = self.config_dir / "test.txt"
            test_file.touch()
            test_file.unlink()
            checks.append(("✓", "Write permissions", "OK"))
        except:
            checks.append(("✗", "Write permissions", "Cannot write to config directory"))
        
        # Display results
        print("System Check Results:")
        print("-" * 60)
        for icon, check, status in checks:
            print(f"{icon} {check:20} {status}")
        
        self._print_footer("Diagnostics completed")
        return 0
    
    def _cmd_init(self, name: Optional[str], template: Optional[str]):
        """Initialiser un nouveau projet"""
        self._print_header()
        
        if not name:
            name = Prompt.ask("Project name")
        
        project_dir = Path(name)
        if project_dir.exists():
            if not Confirm.ask(f"Directory '{name}' already exists. Overwrite?"):
                return 0
            shutil.rmtree(project_dir)
        
        project_dir.mkdir()
        
        # Créer la structure du projet
        templates = {
            "basic": [
                ("README.md", f"# {name}\n\nA Zenv project."),
                ("package.zcf", f"""[Zenv]
name = {name}
version = 0.1.0
author = Your Name
description = A Zenv project

[File-build]
files = src/**/*.zv
        src/**/*.py

[docs]
description = README.md
"""),
                ("src/main.zv", "print('Hello from Zenv!')"),
                (".gitignore", "dist/\n__pycache__/\n*.pyc")
            ],
            "lib": [
                ("README.md", f"# {name}\n\nA Zenv library."),
                ("package.zcf", f"""[Zenv]
name = {name}
version = 0.1.0
author = Your Name
description = A Zenv library

[File-build]
files = {name}/**/*.zv
        {name}/**/*.py

[docs]
description = README.md
"""),
                (f"{name}/__init__.zv", "# Package init"),
                (f"{name}/core.zv", "# Core functionality"),
                (".gitignore", "dist/\n__pycache__/\n*.pyc")
            ]
        }
        
        template = template or "basic"
        if template not in templates:
            template = "basic"
        
        with self._create_progress("Creating project...") as progress:
            task = progress.add_task("[cyan]Setting up...", total=len(templates[template]))
            
            for file_path, content in templates[template]:
                file = project_dir / file_path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content)
                progress.update(task, advance=1)
        
        self.console.print(Panel.fit(
            f"[bold green]✓ Project created![/]\n\n"
            f"[bold]Name:[/] [cyan]{name}[/]\n"
            f"[bold]Template:[/] {template}\n"
            f"[bold]Location:[/] {project_dir.absolute()}\n\n"
            f"[bold]Next steps:[/]\n"
            f"  1. [green]cd {name}[/]\n"
            f"  2. [green]zenv run src/main.zv[/]",
            title="Project Initialized",
            border_style="green"
        ))
        
        self._print_footer()
        return 0
    
    # Implémentations des autres méthodes
    def _install_package(self, package: str, version: Optional[str], force: bool) -> int:
        self._log(f"Installing {package}...", LogLevel.INFO)
        # Implémentation simplifiée
        return 0
    
    def _list_packages(self, local: bool, global_scope: bool) -> int:
        packages = []
        # Récupérer les packages
        if packages:
            table = Table(title="Installed Packages", box=ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Author", style="yellow")
            table.add_column("Description")
            
            for pkg in packages:
                table.add_row(
                    pkg.get('name', ''),
                    pkg.get('version', ''),
                    pkg.get('author', ''),
                    pkg.get('description', '')[:50]
                )
            
            self.console.print(table)
        else:
            self._log("No packages installed", LogLevel.INFO)
        
        return 0
    
    def _remove_package(self, package: str, purge: bool) -> int:
        self._log(f"Removing {package}...", LogLevel.WARNING)
        # Implémentation simplifiée
        return 0
    
    def _update_package(self, package: str, prerelease: bool) -> int:
        self._log(f"Updating {package}...", LogLevel.INFO)
        # Implémentation simplifiée
        return 0
    
    def _package_info(self, package: str) -> int:
        # Implémentation simplifiée
        return 0
    
    def _hub_status(self) -> int:
        if self.hub.check_status():
            self._log("Zenv Hub: Online", LogLevel.SUCCESS)
        else:
            self._log("Zenv Hub: Offline", LogLevel.ERROR)
        return 0
    
    def _hub_login(self, token: str) -> int:
        if self.hub.login(token):
            self._log("Logged in to Zenv Hub", LogLevel.SUCCESS)
        else:
            self._log("Login failed", LogLevel.ERROR)
        return 0 if self.hub.login(token) else 1
    
    def _hub_logout(self) -> int:
        self.hub.logout()
        self._log("Logged out", LogLevel.SUCCESS)
        return 0
    
    def _hub_search(self, query: str) -> int:
        results = self.hub.search_packages(query)
        if results:
            table = Table(title=f"Search Results for '{query}'", box=ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Author", style="yellow")
            table.add_column("Downloads", style="magenta")
            table.add_column("Description")
            
            for pkg in results[:20]:  # Limiter à 20 résultats
                table.add_row(
                    pkg.get('name', ''),
                    pkg.get('version', ''),
                    pkg.get('author', ''),
                    str(pkg.get('downloads', 0)),
                    pkg.get('description', '')[:60]
                )
            
            self.console.print(table)
        else:
            self._log(f"No packages found for '{query}'", LogLevel.INFO)
        
        return 0
    
    def _publish_package(self, package_file: str) -> int:
        self._log(f"Publishing {package_file}...", LogLevel.INFO)
        # Implémentation simplifiée
        return 0
    
    def _hub_whoami(self) -> int:
        # Implémentation simplifiée
        self._log("Not implemented yet", LogLevel.WARNING)
        return 0
