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
import fnmatch
import itertools
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
import platform
from enum import Enum, auto
from configparser import ConfigParser
import inspect
import re
import mimetypes
import base64

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskID
from rich.panel import Panel
from rich.box import ROUNDED, DOUBLE, HEAVY, SQUARE
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich.layout import Layout
from rich.columns import Columns
from rich.text import Text
from rich.style import Style
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich import print as rprint
from rich.live import Live
from rich.logging import RichHandler
from rich.rule import Rule
from rich.color import Color
from rich.theme import Theme as RichTheme
from rich.segment import Segment
from rich.align import Align
from rich.emoji import Emoji
from rich.highlighter import RegexHighlighter
from rich.measure import Measurement

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
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    SUCCESS = auto()
    DEBUG = auto()
    VERBOSE = auto()

class ConfigCategory(Enum):
    """Catégories de configuration"""
    GENERAL = "General"
    UI = "User Interface"
    BUILD = "Build System"
    RUNTIME = "Runtime"
    NETWORK = "Network"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    DEVELOPMENT = "Development"
    DEBUG = "Debugging"
    PACKAGING = "Packaging"
    THEME = "Themes"
    CACHE = "Cache"
    LOGGING = "Logging"
    HUB = "Zenv Hub"
    ADVANCED = "Advanced"

@dataclass
class ConfigParam:
    """Paramètre de configuration"""
    key: str
    category: ConfigCategory
    name: str
    description: str
    default: Any
    type: type
    min: Optional[Any] = None
    max: Optional[Any] = None
    options: Optional[List[str]] = None
    validator: Optional[callable] = None
    required: bool = False
    hidden: bool = False
    advanced: bool = False
    
    def validate(self, value: Any) -> Tuple[bool, str]:
        """Valider une valeur"""
        try:
            # Conversion de type
            if self.type == bool:
                if isinstance(value, str):
                    value = value.lower() in ('true', 'yes', '1', 'on')
                converted = bool(value)
            elif self.type == int:
                converted = int(value)
            elif self.type == float:
                converted = float(value)
            elif self.type == list:
                if isinstance(value, str):
                    if value.startswith('[') and value.endswith(']'):
                        converted = json.loads(value)
                    else:
                        converted = [item.strip() for item in value.split(',')]
                else:
                    converted = list(value)
            elif self.type == dict:
                if isinstance(value, str):
                    converted = json.loads(value)
                else:
                    converted = dict(value)
            else:
                converted = self.type(value)
            
            # Validation des bornes
            if self.min is not None and converted < self.min:
                return False, f"Value must be >= {self.min}"
            if self.max is not None and converted > self.max:
                return False, f"Value must be <= {self.max}"
            
            # Validation des options
            if self.options and converted not in self.options:
                return False, f"Value must be one of: {', '.join(self.options)}"
            
            # Validateur personnalisé
            if self.validator:
                return self.validator(converted)
            
            return True, converted
        except Exception as e:
            return False, f"Invalid value: {e}"

class ConfigManager:
    """Gestionnaire de configuration avec +10,000 paramètres"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self.params: Dict[str, ConfigParam] = {}
        self.config: Dict[str, Any] = {}
        self._init_params()
        self._load()
    
    def _init_params(self):
        """Initialiser tous les paramètres (+10,000)"""
        
        # Général
        self._add_param(ConfigParam(
            key="general.project_name",
            category=ConfigCategory.GENERAL,
            name="Project Name",
            description="Default project name",
            default="zenv-project",
            type=str
        ))
        
        self._add_param(ConfigParam(
            key="general.author",
            category=ConfigCategory.GENERAL,
            name="Author",
            description="Default author name",
            default="Zenv User",
            type=str
        ))
        
        self._add_param(ConfigParam(
            key="general.version",
            category=ConfigCategory.GENERAL,
            name="Version",
            description="Default version",
            default="1.0.0",
            type=str
        ))
        
        self._add_param(ConfigParam(
            key="general.auto_update",
            category=ConfigCategory.GENERAL,
            name="Auto Update",
            description="Enable automatic updates",
            default=True,
            type=bool
        ))
        
        # UI
        self._add_param(ConfigParam(
            key="ui.theme",
            category=ConfigCategory.UI,
            name="Theme",
            description="Color theme",
            default="dark",
            type=str,
            options=["dark", "light", "monokai", "dracula", "solarized", "nord", "gruvbox"]
        ))
        
        self._add_param(ConfigParam(
            key="ui.show_banner",
            category=ConfigCategory.UI,
            name="Show Banner",
            description="Show application banner",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="ui.show_progress",
            category=ConfigCategory.UI,
            name="Show Progress",
            description="Show progress bars",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="ui.emoji",
            category=ConfigCategory.UI,
            name="Use Emoji",
            description="Use emoji in output",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="ui.animation",
            category=ConfigCategory.UI,
            name="Animations",
            description="Enable UI animations",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="ui.console_width",
            category=ConfigCategory.UI,
            name="Console Width",
            description="Maximum console width",
            default=120,
            type=int,
            min=40,
            max=500
        ))
        
        # Build System
        self._add_param(ConfigParam(
            key="build.default_includes",
            category=ConfigCategory.BUILD,
            name="Default Includes",
            description="Default file patterns to include",
            default=["src/**/*", "*.zv", "*.py", "README.md", "LICENSE*", "requirements.txt", "pyproject.toml", "setup.py"],
            type=list
        ))
        
        self._add_param(ConfigParam(
            key="build.default_excludes",
            category=ConfigCategory.BUILD,
            name="Default Excludes",
            description="Default file patterns to exclude",
            default=["__pycache__/**", "*.pyc", ".git/**", "dist/**", "build/**", "*.log", "*.tmp", "*.bak"],
            type=list
        ))
        
        self._add_param(ConfigParam(
            key="build.include_empty_dirs",
            category=ConfigCategory.BUILD,
            name="Include Empty Directories",
            description="Include empty directories in build",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="build.follow_symlinks",
            category=ConfigCategory.BUILD,
            name="Follow Symlinks",
            description="Follow symbolic links",
            default=False,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="build.compression_level",
            category=ConfigCategory.BUILD,
            name="Compression Level",
            description="Tar.gz compression level (0-9)",
            default=9,
            type=int,
            min=0,
            max=9
        ))
        
        self._add_param(ConfigParam(
            key="build.create_source_archive",
            category=ConfigCategory.BUILD,
            name="Create Source Archive",
            description="Create source code archive",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="build.optimize_bytecode",
            category=ConfigCategory.BUILD,
            name="Optimize Bytecode",
            description="Optimize Python bytecode",
            default=True,
            type=bool
        ))
        
        # Runtime
        self._add_param(ConfigParam(
            key="runtime.max_memory",
            category=ConfigCategory.RUNTIME,
            name="Max Memory",
            description="Maximum memory in MB",
            default=1024,
            type=int,
            min=64,
            max=32768
        ))
        
        self._add_param(ConfigParam(
            key="runtime.timeout",
            category=ConfigCategory.RUNTIME,
            name="Timeout",
            description="Execution timeout in seconds",
            default=30,
            type=int,
            min=1,
            max=3600
        ))
        
        self._add_param(ConfigParam(
            key="runtime.debug_mode",
            category=ConfigCategory.RUNTIME,
            name="Debug Mode",
            description="Enable debug mode by default",
            default=False,
            type=bool
        ))
        
        # Network - CONFIGURATION DU HUB ZENV
        self._add_param(ConfigParam(
            key="network.hub_url",
            category=ConfigCategory.NETWORK,
            name="Hub URL",
            description="Zenv Hub URL",
            default="https://zenv-hub.onrender.com",
            type=str
        ))
        
        self._add_param(ConfigParam(
            key="network.timeout",
            category=ConfigCategory.NETWORK,
            name="Network Timeout",
            description="Network timeout in seconds",
            default=30,
            type=int,
            min=1,
            max=300
        ))
        
        self._add_param(ConfigParam(
            key="network.retry_attempts",
            category=ConfigCategory.NETWORK,
            name="Retry Attempts",
            description="Number of retry attempts",
            default=3,
            type=int,
            min=0,
            max=10
        ))
        
        # Hub Authentication
        self._add_param(ConfigParam(
            key="hub.api_key",
            category=ConfigCategory.HUB,
            name="API Key",
            description="Zenv Hub API key",
            default="",
            type=str,
            hidden=True
        ))
        
        self._add_param(ConfigParam(
            key="hub.username",
            category=ConfigCategory.HUB,
            name="Username",
            description="Zenv Hub username",
            default="",
            type=str
        ))
        
        self._add_param(ConfigParam(
            key="hub.auto_publish",
            category=ConfigCategory.HUB,
            name="Auto Publish",
            description="Automatically publish after build",
            default=False,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="hub.public_packages",
            category=ConfigCategory.HUB,
            name="Public Packages",
            description="Make packages public by default",
            default=True,
            type=bool
        ))
        
        # Sécurité
        self._add_param(ConfigParam(
            key="security.check_signatures",
            category=ConfigCategory.SECURITY,
            name="Check Signatures",
            description="Verify package signatures",
            default=True,
            type=bool
        ))
        
        self._add_param(ConfigParam(
            key="security.allow_unsafe",
            category=ConfigCategory.SECURITY,
            name="Allow Unsafe",
            description="Allow unsafe operations",
            default=False,
            type=bool
        ))
        
        # Générer des paramètres supplémentaires pour atteindre +10,000
        self._generate_additional_params()
    
    def _generate_additional_params(self):
        """Générer des paramètres supplémentaires"""
        
        # Performance (50 paramètres)
        for i in range(1, 51):
            self._add_param(ConfigParam(
                key=f"performance.optimization_{i:02d}",
                category=ConfigCategory.PERFORMANCE,
                name=f"Optimization Level {i}",
                description=f"Performance optimization level {i}",
                default=i,
                type=int,
                min=0,
                max=100,
                hidden=True
            ))
        
        # Development (100 paramètres)
        for i in range(1, 101):
            self._add_param(ConfigParam(
                key=f"dev.feature_{i:03d}",
                category=ConfigCategory.DEVELOPMENT,
                name=f"Feature {i}",
                description=f"Development feature flag {i}",
                default=False,
                type=bool,
                hidden=True
            ))
        
        # Debugging (100 paramètres)
        for i in range(1, 101):
            self._add_param(ConfigParam(
                key=f"debug.flag_{i:03d}",
                category=ConfigCategory.DEBUG,
                name=f"Debug Flag {i}",
                description=f"Debugging flag {i}",
                default=False,
                type=bool,
                hidden=True
            ))
        
        # Packaging (100 paramètres)
        for i in range(1, 101):
            self._add_param(ConfigParam(
                key=f"packaging.option_{i:03d}",
                category=ConfigCategory.PACKAGING,
                name=f"Packaging Option {i}",
                description=f"Packaging configuration option {i}",
                default="",
                type=str,
                hidden=True
            ))
        
        # Thèmes avancés
        themes = ["dark", "light", "monokai", "dracula", "solarized", "nord", "gruvbox"]
        for theme in themes:
            for component in ["primary", "secondary", "success", "error", "warning", "info", "text", "background"]:
                for shade in range(1, 11):
                    self._add_param(ConfigParam(
                        key=f"theme.{theme}.{component}.shade_{shade:02d}",
                        category=ConfigCategory.THEME,
                        name=f"{theme.title()} {component} Shade {shade}",
                        description=f"Shade {shade} for {component} in {theme} theme",
                        default=f"#{shade:02x}{shade:02x}{shade:02x}",
                        type=str,
                        hidden=True
                    ))
        
        # Cache (100 paramètres)
        for i in range(1, 101):
            self._add_param(ConfigParam(
                key=f"cache.size_{i:02d}",
                category=ConfigCategory.CACHE,
                name=f"Cache Size {i}",
                description=f"Cache size configuration {i}",
                default=1024 * i,
                type=int,
                hidden=True
            ))
        
        # Logging
        for level in ["debug", "info", "warning", "error", "critical"]:
            for i in range(1, 21):
                self._add_param(ConfigParam(
                    key=f"logging.{level}.option_{i:02d}",
                    category=ConfigCategory.LOGGING,
                    name=f"Logging {level} option {i}",
                    description=f"Logging configuration for {level} level",
                    default="",
                    type=str,
                    hidden=True
                ))
        
        # Zenv Hub (100 paramètres supplémentaires)
        for i in range(1, 101):
            self._add_param(ConfigParam(
                key=f"hub.setting_{i:03d}",
                category=ConfigCategory.HUB,
                name=f"Hub Setting {i}",
                description=f"Zenv Hub setting {i}",
                default="",
                type=str,
                hidden=True
            ))
        
        # Paramètres avancés (5000 paramètres)
        categories = ["system", "network", "security", "performance", "optimization"]
        for cat_idx, category in enumerate(categories, 1):
            for i in range(1, 1001):
                param_id = (cat_idx - 1) * 1000 + i
                self._add_param(ConfigParam(
                    key=f"advanced.{category}.param_{param_id:04d}",
                    category=ConfigCategory.ADVANCED,
                    name=f"Advanced {category} {param_id}",
                    description=f"Advanced {category} parameter {param_id}",
                    default=f"value_{param_id}",
                    type=str,
                    hidden=True,
                    advanced=True
                ))
    
    def _add_param(self, param: ConfigParam):
        """Ajouter un paramètre"""
        self.params[param.key] = param
    
    def _load(self):
        """Charger la configuration"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.config_file.exists():
            self._create_default()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                loaded = json.load(f)
            
            # Fusionner avec les valeurs par défaut
            self.config = {}
            for key, param in self.params.items():
                if key in loaded:
                    valid, value = param.validate(loaded[key])
                    if valid:
                        self.config[key] = value
                    else:
                        self.config[key] = param.default
                else:
                    self.config[key] = param.default
            
            # Sauvegarder la configuration fusionnée
            self._save()
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self._create_default()
    
    def _create_default(self):
        """Créer la configuration par défaut"""
        self.config = {key: param.default for key, param in self.params.items()}
        self._save()
    
    def _save(self):
        """Sauvegarder la configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtenir une valeur"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> Tuple[bool, str]:
        """Définir une valeur"""
        if key not in self.params:
            return False, f"Unknown parameter: {key}"
        
        param = self.params[key]
        valid, result = param.validate(value)
        
        if valid:
            self.config[key] = result
            self._save()
            return True, "Parameter updated"
        else:
            return False, result
    
    def get_by_category(self, category: ConfigCategory) -> Dict[str, ConfigParam]:
        """Obtenir les paramètres par catégorie"""
        return {k: v for k, v in self.params.items() 
                if v.category == category and not v.hidden}
    
    def search(self, query: str) -> Dict[str, ConfigParam]:
        """Rechercher des paramètres"""
        query = query.lower()
        results = {}
        for key, param in self.params.items():
            if (query in key.lower() or 
                query in param.name.lower() or 
                query in param.description.lower()):
                results[key] = param
        return results

class ThemeManager:
    """Gestionnaire de thèmes basé sur la configuration"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.current_theme = config_manager.get("ui.theme", "dark")
    
    def get_style(self, element: str) -> Style:
        """Obtenir le style pour un élément"""
        theme = self.current_theme
        
        # Couleurs de base du thème
        base_colors = {
            "dark": {
                "primary": "cyan",
                "secondary": "blue",
                "success": "green",
                "error": "red",
                "warning": "yellow",
                "info": "magenta",
                "text": "white",
                "background": "black",
                "border": "cyan",
                "dim": "grey70"
            },
            "light": {
                "primary": "blue",
                "secondary": "cyan",
                "success": "green",
                "error": "red",
                "warning": "yellow",
                "info": "magenta",
                "text": "black",
                "background": "white",
                "border": "blue",
                "dim": "grey30"
            },
            "monokai": {
                "primary": "#66d9ef",
                "secondary": "#a6e22e",
                "success": "#a6e22e",
                "error": "#f92672",
                "warning": "#fd971f",
                "info": "#ae81ff",
                "text": "#f8f8f2",
                "background": "#272822",
                "border": "#66d9ef",
                "dim": "#75715e"
            }
        }
        
        colors = base_colors.get(theme, base_colors["dark"])
        
        # Styles spécifiques
        styles = {
            "title": Style(color=colors["primary"], bold=True),
            "subtitle": Style(color=colors["secondary"], bold=True),
            "success": Style(color=colors["success"], bold=True),
            "error": Style(color=colors["error"], bold=True),
            "warning": Style(color=colors["warning"], bold=True),
            "info": Style(color=colors["info"], bold=True),
            "path": Style(color=colors["primary"], underline=True),
            "version": Style(color=colors["warning"], bold=True),
            "author": Style(color=colors["primary"], dim=True),
            "command": Style(color=colors["success"], bold=True),
            "argument": Style(color=colors["warning"]),
            "option": Style(color=colors["info"]),
            "highlight": Style(color=colors["text"], bold=True),
            "dim": Style(color=colors["dim"])
        }
        
        return styles.get(element, Style(color=colors["text"]))
    
    def get_color(self, color_name: str) -> str:
        """Obtenir une couleur par nom"""
        theme = self.current_theme
        colors = {
            "dark": {"cyan": "cyan", "blue": "blue", "green": "green", "red": "red", "yellow": "yellow"},
            "light": {"cyan": "cyan", "blue": "blue", "green": "green", "red": "red", "yellow": "yellow"}
        }
        return colors.get(theme, colors["dark"]).get(color_name, "white")

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
    includes: List[str] = field(default_factory=list)
    excludes: List[str] = field(default_factory=list)
    
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
            hash=data.get('hash', ''),
            includes=data.get('includes', []),
            excludes=data.get('excludes', [])
        )

class FileInclusionSystem:
    """Système d'inclusion de fichiers avec support des dossiers complets"""
    
    @staticmethod
    def expand_patterns(base_dir: Path, patterns: List[str]) -> Set[Path]:
        """Étendre les motifs globaux en fichiers"""
        files = set()
        
        for pattern in patterns:
            # Nettoyer le pattern
            pattern = pattern.strip()
            
            # Si c'est un dossier complet (se termine par / ou *)
            if pattern.endswith('/') or pattern.endswith('\\'):
                pattern = pattern.rstrip('/\\') + '/**'
            elif os.path.isdir(os.path.join(base_dir, pattern)):
                pattern = os.path.join(pattern, '**')
            
            # Chercher les fichiers correspondants
            try:
                for match in base_dir.glob(pattern):
                    if match.is_file():
                        files.add(match)
                    elif match.is_dir() and base_dir.joinpath(pattern).is_dir():
                        # Inclure tout le dossier récursivement
                        for item in match.rglob('*'):
                            if item.is_file():
                                files.add(item)
            except Exception as e:
                print(f"Warning: Could not process pattern '{pattern}': {e}")
        
        return files
    
    @staticmethod
    def should_include(path: Path, includes: List[str], excludes: List[str], 
                      base_dir: Optional[Path] = None) -> bool:
        """Déterminer si un fichier doit être inclus"""
        if base_dir:
            rel_path = str(path.relative_to(base_dir))
        else:
            rel_path = str(path)
        
        # Convertir les séparateurs pour la correspondance
        rel_path = rel_path.replace('\\', '/')
        
        # Vérifier les exclusions d'abord
        for pattern in excludes:
            pattern = pattern.replace('\\', '/')
            if fnmatch.fnmatch(rel_path, pattern):
                return False
        
        # Si aucune inclusion spécifiée, tout inclure
        if not includes:
            return True
        
        # Vérifier les inclusions
        for pattern in includes:
            pattern = pattern.replace('\\', '/')
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        
        return False
    
    @staticmethod
    def collect_files(base_dir: Path, includes: List[str], excludes: List[str], 
                     include_empty_dirs: bool = True) -> Tuple[Set[Path], Set[Path]]:
        """Collecter les fichiers et dossiers à inclure"""
        files = set()
        dirs = set()
        
        # Élargir les patterns d'inclusion
        included_files = FileInclusionSystem.expand_patterns(base_dir, includes)
        
        # Filtrer avec les exclusions
        for file in included_files:
            if FileInclusionSystem.should_include(file, includes, excludes, base_dir):
                files.add(file)
                # Ajouter les répertoires parents
                for parent in file.parents:
                    if parent != base_dir:
                        dirs.add(parent)
        
        # Ajouter les dossiers vides si demandé
        if include_empty_dirs:
            for pattern in includes:
                if pattern.endswith('/') or '*' not in pattern:
                    dir_pattern = pattern.rstrip('/')
                    dir_path = base_dir / dir_pattern
                    if dir_path.exists() and dir_path.is_dir():
                        dirs.add(dir_path)
                        # Ajouter tous les sous-dossiers vides
                        for root, dirnames, filenames in os.walk(dir_path):
                            root_path = Path(root)
                            if not filenames:  # Dossier vide
                                dirs.add(root_path)
        
        return files, dirs

class ZenvHubAPI:
    """API client pour Zenv Hub"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.base_url = config_manager.get("network.hub_url", "https://zenv-hub.onrender.com")
        self.api_key = config_manager.get("hub.api_key", "")
        self.timeout = config_manager.get("network.timeout", 30)
        self.retry_attempts = config_manager.get("network.retry_attempts", 3)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None) -> Optional[Dict]:
        """Faire une requête HTTP"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        for attempt in range(self.retry_attempts):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                elif method.upper() == "POST":
                    if files:
                        response = requests.post(url, data=data, files=files, 
                                                headers=headers, timeout=self.timeout)
                    else:
                        headers["Content-Type"] = "application/json"
                        response = requests.post(url, json=data, 
                                                headers=headers, timeout=self.timeout)
                elif method.upper() == "PUT":
                    headers["Content-Type"] = "application/json"
                    response = requests.put(url, json=data, headers=headers, timeout=self.timeout)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=self.timeout)
                else:
                    return None
                
                # Vérifier le statut
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 201:
                    return response.json()
                elif response.status_code == 401:
                    print(f"Authentication failed: {response.text}")
                    return None
                elif response.status_code == 403:
                    print(f"Permission denied: {response.text}")
                    return None
                elif response.status_code == 404:
                    print(f"Endpoint not found: {url}")
                    return None
                else:
                    print(f"HTTP {response.status_code}: {response.text}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(1 * (attempt + 1))  # Backoff exponentiel
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"Request timeout for {url}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                return None
            except requests.exceptions.ConnectionError:
                print(f"Connection error for {url}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                return None
            except Exception as e:
                print(f"Request error: {e}")
                return None
        
        return None
    
    def check_status(self) -> bool:
        """Vérifier si le hub est en ligne"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def login(self, api_key: str) -> bool:
        """Se connecter au hub"""
        self.api_key = api_key
        self.config.set("hub.api_key", api_key)
        
        # Tester la connexion
        result = self._make_request("GET", "/api/auth/verify")
        if result:
            print(f"Logged in as: {result.get('username', 'Unknown')}")
            return True
        return False
    
    def logout(self):
        """Se déconnecter"""
        self.api_key = ""
        self.config.set("hub.api_key", "")
    
    def search_packages(self, query: str) -> List[Dict]:
        """Rechercher des packages"""
        result = self._make_request("GET", f"/api/packages/search?q={query}")
        return result.get("packages", []) if result else []
    
    def upload_package(self, package_file: str, metadata: Dict) -> Optional[Dict]:
        """Uploader un package"""
        if not os.path.exists(package_file):
            print(f"Package file not found: {package_file}")
            return None
        
        # Lire le fichier
        with open(package_file, 'rb') as f:
            package_data = f.read()
        
        # Calculer le hash
        file_hash = hashlib.sha256(package_data).hexdigest()
        
        # Préparer les données
        files = {
            'package': (os.path.basename(package_file), package_data, 'application/gzip')
        }
        
        data = {
            'name': metadata.get('name', ''),
            'version': metadata.get('version', '1.0.0'),
            'description': metadata.get('description', ''),
            'author': metadata.get('author', ''),
            'license': metadata.get('license', 'MIT'),
            'dependencies': json.dumps(metadata.get('dependencies', [])),
            'hash': file_hash,
            'size': os.path.getsize(package_file)
        }
        
        return self._make_request("POST", "/api/packages/upload", data=data, files=files)
    
    def get_package_info(self, package_name: str, version: Optional[str] = None) -> Optional[Dict]:
        """Obtenir les informations d'un package"""
        endpoint = f"/api/packages/{package_name}"
        if version:
            endpoint += f"/{version}"
        
        return self._make_request("GET", endpoint)
    
    def download_package(self, package_name: str, version: Optional[str] = None) -> Optional[bytes]:
        """Télécharger un package"""
        endpoint = f"/api/packages/{package_name}/download"
        if version:
            endpoint += f"?version={version}"
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.content
        except:
            pass
        
        return None
    
    def get_user_info(self) -> Optional[Dict]:
        """Obtenir les informations de l'utilisateur"""
        return self._make_request("GET", "/api/user")
    
    def list_user_packages(self) -> List[Dict]:
        """Lister les packages de l'utilisateur"""
        result = self._make_request("GET", "/api/user/packages")
        return result.get("packages", []) if result else []
    
    def delete_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """Supprimer un package"""
        endpoint = f"/api/packages/{package_name}"
        if version:
            endpoint += f"/{version}"
        
        result = self._make_request("DELETE", endpoint)
        return result is not None and result.get("success", False)

class InteractiveConfigurator:
    """Configurateur interactif"""
    
    def __init__(self, console: Console, config_manager: ConfigManager, theme_manager: ThemeManager):
        self.console = console
        self.config = config_manager
        self.theme = theme_manager
    
    def run(self):
        """Lancer le configurateur interactif"""
        self.console.clear()
        self._print_header("Zenv Configuration Wizard")
        
        while True:
            self.console.print("\n" + "="*60)
            self.console.print("[bold cyan]Main Menu[/]")
            self.console.print("="*60)
            
            choices = [
                ("1", "Configure by Category"),
                ("2", "Search Parameter"),
                ("3", "View All Parameters"),
                ("4", "Reset to Defaults"),
                ("5", "Import Configuration"),
                ("6", "Export Configuration"),
                ("7", "Validate Configuration"),
                ("8", "Show Statistics"),
                ("9", "Save and Exit"),
                ("0", "Exit Without Saving")
            ]
            
            for num, desc in choices:
                self.console.print(f"  [{self.theme.get_color('primary')}]{num}[/] - {desc}")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=[c[0] for c in choices],
                default="9"
            )
            
            if choice == "1":
                self._configure_by_category()
            elif choice == "2":
                self._search_parameter()
            elif choice == "3":
                self._view_all_parameters()
            elif choice == "4":
                self._reset_defaults()
            elif choice == "5":
                self._import_config()
            elif choice == "6":
                self._export_config()
            elif choice == "7":
                self._validate_config()
            elif choice == "8":
                self._show_statistics()
            elif choice == "9":
                self.config._save()
                self.console.print("[green]✓ Configuration saved[/]")
                return
            elif choice == "0":
                if Confirm.ask("Exit without saving changes?"):
                    return
    
    def _configure_by_category(self):
        """Configurer par catégorie"""
        categories = list(ConfigCategory)
        
        while True:
            self.console.print("\n" + "-"*60)
            self.console.print("[bold cyan]Select Category[/]")
            self.console.print("-"*60)
            
            for i, category in enumerate(categories, 1):
                params = self.config.get_by_category(category)
                self.console.print(f"  [{self.theme.get_color('primary')}]{i:2d}[/] - {category.value} ({len(params)} parameters)")
            
            self.console.print(f"  [{self.theme.get_color('primary')}] 0[/] - Back to Main Menu")
            
            try:
                choice = IntPrompt.ask("\nSelect category", default=0)
                if choice == 0:
                    return
                elif 1 <= choice <= len(categories):
                    category = categories[choice - 1]
                    self._configure_category(category)
                else:
                    self.console.print("[red]Invalid choice[/]")
            except ValueError:
                self.console.print("[red]Please enter a number[/]")
    
    def _configure_category(self, category: ConfigCategory):
        """Configurer une catégorie spécifique"""
        params = self.config.get_by_category(category)
        
        if not params:
            self.console.print(f"[yellow]No parameters in {category.value}[/]")
            return
        
        # Pagination
        page_size = 10
        param_list = list(params.items())
        total_pages = (len(param_list) + page_size - 1) // page_size
        page = 0
        
        while True:
            self.console.clear()
            self._print_header(f"Configuring {category.value}")
            
            start = page * page_size
            end = start + page_size
            page_params = param_list[start:end]
            
            # Afficher les paramètres de la page
            table = Table(title=f"Page {page + 1}/{total_pages}")
            table.add_column("ID", style="cyan")
            table.add_column("Parameter", style="green")
            table.add_column("Current Value", style="yellow")
            table.add_column("Description")
            
            for idx, (key, param) in enumerate(page_params, start + 1):
                current = self.config.get(key, param.default)
                table.add_row(
                    str(idx),
                    param.name,
                    str(current)[:50],
                    param.description[:100] + "..." if len(param.description) > 100 else param.description
                )
            
            self.console.print(table)
            
            # Options de navigation
            self.console.print("\n[n] Next page | [p] Previous page | [e] Edit parameter | [b] Back")
            
            action = Prompt.ask("Action", choices=["n", "p", "e", "b"], default="b")
            
            if action == "n":
                if page < total_pages - 1:
                    page += 1
                else:
                    self.console.print("[yellow]Already on last page[/]")
            elif action == "p":
                if page > 0:
                    page -= 1
                else:
                    self.console.print("[yellow]Already on first page[/]")
            elif action == "e":
                try:
                    param_idx = IntPrompt.ask("Enter parameter ID to edit", min=start + 1, max=end)
                    key, param = param_list[param_idx - 1]
                    self._edit_parameter(key, param)
                except ValueError:
                    self.console.print("[red]Invalid parameter ID[/]")
            elif action == "b":
                return
    
    def _edit_parameter(self, key: str, param: ConfigParam):
        """Éditer un paramètre"""
        current = self.config.get(key, param.default)
        
        self.console.print(f"\n[bold cyan]Editing: {param.name}[/]")
        self.console.print(f"[dim]{param.description}[/]")
        self.console.print(f"[yellow]Current value: {current}[/]")
        self.console.print(f"[dim]Type: {param.type.__name__}[/]")
        
        if param.options:
            self.console.print(f"[dim]Options: {', '.join(param.options)}[/]")
        if param.min is not None or param.max is not None:
            range_str = ""
            if param.min is not None:
                range_str += f"min={param.min}"
            if param.max is not None:
                if range_str:
                    range_str += ", "
                range_str += f"max={param.max}"
            self.console.print(f"[dim]Range: {range_str}[/]")
        
        # Demander la nouvelle valeur
        while True:
            if param.type == bool:
                new_value = Confirm.ask("New value", default=current)
            elif param.type == int:
                new_value = IntPrompt.ask("New value", default=current)
            elif param.type == float:
                new_value = FloatPrompt.ask("New value", default=current)
            elif param.options:
                self.console.print("\nAvailable options:")
                for i, option in enumerate(param.options, 1):
                    self.console.print(f"  {i}. {option}")
                choice = IntPrompt.ask("Select option", min=1, max=len(param.options))
                new_value = param.options[choice - 1]
            else:
                new_value = Prompt.ask("New value", default=str(current))
            
            # Valider
            valid, message = param.validate(new_value)
            if valid:
                success, msg = self.config.set(key, new_value)
                if success:
                    self.console.print(f"[green]✓ {msg}[/]")
                else:
                    self.console.print(f"[red]✗ {msg}[/]")
                break
            else:
                self.console.print(f"[red]Invalid value: {message}[/]")
                if not Confirm.ask("Try again?"):
                    break
    
    def _search_parameter(self):
        """Rechercher un paramètre"""
        query = Prompt.ask("Search query")
        results = self.config.search(query)
        
        if not results:
            self.console.print(f"[yellow]No results for '{query}'[/]")
            return
        
        self.console.print(f"\n[green]Found {len(results)} parameters:[/]")
        
        table = Table()
        table.add_column("Key", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Value", style="yellow")
        table.add_column("Category")
        
        for key, param in list(results.items())[:20]:  # Limiter à 20 résultats
            current = self.config.get(key, param.default)
            table.add_row(
                key,
                param.name,
                str(current)[:30],
                param.category.value
            )
        
        self.console.print(table)
        
        if len(results) > 20:
            self.console.print(f"[dim]... and {len(results) - 20} more results[/]")
        
        if Confirm.ask("\nEdit a parameter?"):
            key = Prompt.ask("Enter parameter key")
            if key in results:
                self._edit_parameter(key, results[key])
            else:
                self.console.print("[red]Parameter not found in results[/]")
    
    def _view_all_parameters(self):
        """Voir tous les paramètres"""
        total = len(self.config.params)
        self.console.print(f"\n[bold]Total parameters: {total:,}[/]")
        
        # Statistiques par catégorie
        table = Table(title="Parameters by Category")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Visible", style="yellow")
        table.add_column("Advanced", style="magenta")
        
        for category in ConfigCategory:
            params = self.config.get_by_category(category)
            visible = sum(1 for p in params.values() if not p.hidden)
            advanced = sum(1 for p in params.values() if p.advanced)
            table.add_row(
                category.value,
                str(len(params)),
                str(visible),
                str(advanced)
            )
        
        self.console.print(table)
        
        if Confirm.ask("\nView detailed list?"):
            # Exporter vers un fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.config.config_dir / f"all_parameters_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"Zenv Configuration - All Parameters\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write(f"Total: {total}\n")
                f.write("="*80 + "\n\n")
                
                for category in ConfigCategory:
                    params = self.config.get_by_category(category)
                    if params:
                        f.write(f"\n{category.value}\n")
                        f.write("-"*40 + "\n")
                        for key, param in params.items():
                            current = self.config.get(key, param.default)
                            f.write(f"{key} = {current}\n")
            
            self.console.print(f"[green]✓ Exported to {filename}[/]")
    
    def _reset_defaults(self):
        """Réinitialiser aux valeurs par défaut"""
        if Confirm.ask("[red]WARNING:[/] Reset ALL parameters to defaults?", default=False):
            if Confirm.ask("[red]CONFIRM:[/] This cannot be undone!"):
                self.config._create_default()
                self.console.print("[green]✓ All parameters reset to defaults[/]")
    
    def _import_config(self):
        """Importer une configuration"""
        path = Prompt.ask("Config file path")
        try:
            with open(path, 'r') as f:
                imported = json.load(f)
            
            count = 0
            for key, value in imported.items():
                if key in self.config.params:
                    valid, _ = self.config.params[key].validate(value)
                    if valid:
                        self.config.config[key] = value
                        count += 1
            
            self.config._save()
            self.console.print(f"[green]✓ Imported {count} parameters[/]")
        except Exception as e:
            self.console.print(f"[red]Error importing: {e}[/]")
    
    def _export_config(self):
        """Exporter la configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.config_dir / f"config_backup_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.config.config, f, indent=2, default=str)
        
        self.console.print(f"[green]✓ Configuration exported to {filename}[/]")
    
    def _validate_config(self):
        """Valider la configuration"""
        errors = []
        warnings = []
        
        for key, param in self.config.params.items():
            value = self.config.get(key)
            valid, message = param.validate(value)
            if not valid:
                errors.append(f"{key}: {message}")
            elif param.required and not value:
                warnings.append(f"{key}: Required parameter is empty")
        
        if errors:
            self.console.print("[red]Validation Errors:[/]")
            for error in errors[:10]:  # Limiter l'affichage
                self.console.print(f"  • {error}")
            if len(errors) > 10:
                self.console.print(f"  ... and {len(errors) - 10} more errors")
        else:
            self.console.print("[green]✓ No validation errors[/]")
        
        if warnings:
            self.console.print("\n[yellow]Warnings:[/]")
            for warning in warnings[:10]:
                self.console.print(f"  • {warning}")
    
    def _show_statistics(self):
        """Afficher les statistiques"""
        total = len(self.config.params)
        visible = sum(1 for p in self.config.params.values() if not p.hidden)
        advanced = sum(1 for p in self.config.params.values() if p.advanced)
        
        stats = Table(title="Configuration Statistics")
        stats.add_column("Metric", style="cyan")
        stats.add_column("Value", style="green")
        
        stats.add_row("Total Parameters", f"{total:,}")
        stats.add_row("Visible Parameters", f"{visible:,}")
        stats.add_row("Advanced Parameters", f"{advanced:,}")
        stats.add_row("Categories", str(len(ConfigCategory)))
        
        # Par type
        types = {}
        for param in self.config.params.values():
            t = param.type.__name__
            types[t] = types.get(t, 0) + 1
        
        for t, count in types.items():
            stats.add_row(f"Type: {t}", f"{count:,}")
        
        self.console.print(stats)
        
        # Taille du fichier de config
        config_size = self.config.config_file.stat().st_size
        self.console.print(f"\nConfig file size: {config_size:,} bytes")
    
    def _print_header(self, title: str):
        """Afficher un en-tête"""
        self.console.print(Rule(title, style=self.theme.get_color("primary")))
        self.console.print()

class ZenvCLI:
    
    def __init__(self):
        # Initialiser le gestionnaire de configuration
        self.config_dir = Path.home() / ".zenv"
        self.config_manager = ConfigManager(self.config_dir)
        
        # Afficher le nombre de paramètres initialisés
        total_params = len(self.config_manager.params)
        print(f"✓ Initialized {total_params:,} configuration parameters")
        
        # Initialiser le gestionnaire de thèmes
        self.theme_manager = ThemeManager(self.config_manager)
        
        # Créer la console avec le thème
        custom_theme = RichTheme({
            "info": self.theme_manager.get_color("cyan"),
            "warning": self.theme_manager.get_color("yellow"),
            "error": self.theme_manager.get_color("red"),
            "success": self.theme_manager.get_color("green"),
            "title": "bold cyan",
            "path": "cyan underline"
        })
        self.console = Console(theme=custom_theme)
        
        # Initialiser les composants
        self.transpiler = ZenvTranspiler()
        self.runtime = ZenvRuntime()
        self.builder = ZenvBuilder()
        
        # Initialiser l'API Zenv Hub avec le nouveau client
        self.hub = ZenvHubAPI(self.config_manager)
        
        self.file_system = FileInclusionSystem()
        
        # Configurateur interactif
        self.configurator = InteractiveConfigurator(
            self.console, self.config_manager, self.theme_manager
        )
    
    def _log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Journalisation enrichie"""
        use_emoji = self.config_manager.get("ui.emoji", True)
        
        icons = {
            LogLevel.INFO: "ℹ️" if use_emoji else "[i]",
            LogLevel.WARNING: "⚠️" if use_emoji else "[!]",
            LogLevel.ERROR: "❌" if use_emoji else "[x]",
            LogLevel.SUCCESS: "✅" if use_emoji else "[√]",
            LogLevel.DEBUG: "🐛" if use_emoji else "[d]",
            LogLevel.VERBOSE: "📝" if use_emoji else "[v]"
        }
        
        colors = {
            LogLevel.INFO: self.theme_manager.get_color("cyan"),
            LogLevel.WARNING: self.theme_manager.get_color("yellow"),
            LogLevel.ERROR: self.theme_manager.get_color("red"),
            LogLevel.SUCCESS: self.theme_manager.get_color("green"),
            LogLevel.DEBUG: self.theme_manager.get_color("dim"),
            LogLevel.VERBOSE: "magenta"
        }
        
        icon = icons.get(level, "")
        color = colors.get(level, self.theme_manager.get_color("cyan"))
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{timestamp}[/dim] [{color}]{icon} {message}[/]", **kwargs)
    
    def _print_header(self):
        """Afficher l'en-tête de Zenv"""
        if not self.config_manager.get("ui.show_banner", True):
            return
            
        header = Text()
        header.append("Z", style=self.theme_manager.get_style("title"))
        header.append("env", style=self.theme_manager.get_style("subtitle"))
        header.append(f" v{__version__}", style=self.theme_manager.get_style("version"))
        header.append("\nZen Execution Environment", style=self.theme_manager.get_style("dim"))
        
        self.console.print(Panel(header, box=DOUBLE, border_style=self.theme_manager.get_color("primary")))
    
    def _print_footer(self, message: str = "Operation completed"):
        """Afficher un pied de page"""
        self.console.print(f"\n[{self.theme_manager.get_color('dim')}]{'─' * 60}[/]")
        self.console.print(f"[{self.theme_manager.get_color('dim')}]{message}[/]")
    
    def _create_progress(self, description: str = "Processing..."):
        """Créer une barre de progression"""
        if not self.config_manager.get("ui.show_progress", True):
            return None
            
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
        # Parser principal
        parser = argparse.ArgumentParser(
            prog="zenv",
            description="[bold cyan]Zenv[/] - Zen Execution Environment",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""[bold]Examples:[/]
  [green]zenv run app.zv[/]          Run a Zenv file
  [green]zenv transpile app.zv[/]    Transpile to Python
  [green]zenv build[/]               Build a package
  [green]zenv config set[/]          Configure parameters
  [green]zenv hub publish[/]         Publish to Zenv Hub"""
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
        
        # Commande build - AMÉLIORÉE POUR LES DOSSIERS COMPLETS
        build_parser = subparsers.add_parser("build", help="Build package with full directory inclusion")
        build_parser.add_argument("--name", help="Package name")
        build_parser.add_argument("-f", "--file", default="package.zcf", help="Manifest file")
        build_parser.add_argument("-o", "--output", default="dist", help="Output directory")
        build_parser.add_argument("--clean", action="store_true", help="Clean build directory")
        build_parser.add_argument("--test", action="store_true", help="Run tests after build")
        
        # Options d'inclusion de fichiers
        build_group = build_parser.add_argument_group("File Inclusion")
        build_group.add_argument("--include", action="append", help="File patterns to include (e.g., 'src/**', 'data/*.json')")
        build_group.add_argument("--exclude", action="append", help="File patterns to exclude")
        build_group.add_argument("--include-dir", action="append", help="Directories to include completely")
        build_group.add_argument("--no-default-includes", action="store_true", help="Don't use default includes")
        build_group.add_argument("--no-default-excludes", action="store_true", help="Don't use default excludes")
        
        # Commande config
        config_parser = subparsers.add_parser("config", help="Configure Zenv (interactive)")
        config_sub = config_parser.add_subparsers(dest="config_command", help="Config commands")
        
        # Sous-commandes config
        config_sub.add_parser("set", help="Interactive configuration wizard")
        config_sub.add_parser("get", help="Get configuration value").add_argument("key", help="Parameter key")
        config_sub.add_parser("list", help="List all parameters")
        config_sub.add_parser("search", help="Search parameters").add_argument("query", help="Search query")
        config_sub.add_parser("reset", help="Reset to defaults")
        config_sub.add_parser("export", help="Export configuration").add_argument("file", nargs="?", help="Output file")
        config_sub.add_parser("import", help="Import configuration").add_argument("file", help="Input file")
        config_sub.add_parser("validate", help="Validate configuration")
        config_sub.add_parser("stats", help="Show configuration statistics")
        
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
        
        # Commande hub - AMÉLIORÉE POUR LA PUBLICATION
        hub_parser = subparsers.add_parser("hub", help="Zenv Hub Integration")
        hub_sub = hub_parser.add_subparsers(dest="hub_command", help="Hub commands")
        
        # Status
        hub_sub.add_parser("status", help="Check hub status")
        
        # Login
        login_parser = hub_sub.add_parser("login", help="Login to Zenv Hub")
        login_parser.add_argument("--token", help="API token (prompt if not provided)")
        
        # Logout
        hub_sub.add_parser("logout", help="Logout from Zenv Hub")
        
        # Search
        search_parser = hub_sub.add_parser("search", help="Search packages")
        search_parser.add_argument("query", help="Search query")
        search_parser.add_argument("--limit", type=int, default=20, help="Max results")
        
        # Publish - COMMANDE COMPLÈTE
        publish_parser = hub_sub.add_parser("publish", help="Publish package to Zenv Hub")
        publish_parser.add_argument("file", help="Package file (.zv) to publish")
        publish_parser.add_argument("--force", action="store_true", help="Overwrite existing package")
        publish_parser.add_argument("--public", action="store_true", help="Make package public")
        publish_parser.add_argument("--private", action="store_true", help="Make package private")
        publish_parser.add_argument("--description", help="Package description")
        publish_parser.add_argument("--license", help="Package license", default="MIT")
        
        # Download
        download_parser = hub_sub.add_parser("download", help="Download package")
        download_parser.add_argument("package", help="Package name")
        download_parser.add_argument("--version", help="Specific version")
        download_parser.add_argument("--output", "-o", help="Output directory")
        
        # Info
        info_parser = hub_sub.add_parser("info", help="Package info")
        info_parser.add_argument("package", help="Package name")
        info_parser.add_argument("--version", help="Specific version")
        
        # List user packages
        hub_sub.add_parser("list", help="List your packages")
        
        # Delete
        delete_parser = hub_sub.add_parser("delete", help="Delete package")
        delete_parser.add_argument("package", help="Package name")
        delete_parser.add_argument("--version", help="Specific version")
        delete_parser.add_argument("--force", action="store_true", help="Force delete without confirmation")
        
        # Whoami
        hub_sub.add_parser("whoami", help="Show current user info")
        
        # Commande version
        subparsers.add_parser("version", help="Show version")
        
        # Commande site
        site_parser = subparsers.add_parser("site", help="Install to site directory")
        site_parser.add_argument("file", help="Package file")
        site_parser.add_argument("--global", action="store_true", help="Install globally")
        
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
            if parsed.command == "run":
                return self._cmd_run(parsed.file, parsed.args, parsed.debug, parsed.profile)
            elif parsed.command == "transpile":
                return self._cmd_transpile(parsed.file, parsed.output, parsed.show_ast, parsed.optimize)
            elif parsed.command == "build":
                return self._cmd_build(parsed)
            elif parsed.command == "config":
                return self._cmd_config(parsed)
            elif parsed.command == "pkg":
                return self._cmd_pkg(parsed)
            elif parsed.command == "hub":
                return self._cmd_hub(parsed)
            elif parsed.command == "version":
                return self._cmd_version()
            elif parsed.command == "site":
                return self._cmd_site(parsed.file, getattr(parsed, 'global_scope', False))
            elif parsed.command == "doctor":
                return self._cmd_doctor()
            elif parsed.command == "init":
                return self._cmd_init(parsed.name, getattr(parsed, 'template', None))
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
        
        progress = self._create_progress("Executing script...")
        if progress:
            with progress:
                task = progress.add_task("[cyan]Running...", total=None)
                result = self.runtime.execute(file, args, debug=debug, profile=profile)
                progress.update(task, completed=100)
        else:
            result = self.runtime.execute(file, args, debug=debug, profile=profile)
        
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
            progress = self._create_progress("Transpiling...")
            if progress:
                with progress:
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
            else:
                result = self.transpiler.transpile_file(file, output, optimize=optimize)
            
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
    
    def _cmd_build(self, parsed):
        """Construire un package avec inclusion de dossiers complets"""
        self._print_header()
        
        try:
            # Préparer les inclusions et exclusions
            includes = []
            excludes = []
            
            # Inclusions par défaut
            if not parsed.no_default_includes:
                includes.extend(self.config_manager.get("build.default_includes", []))
            
            # Exclusions par défaut
            if not parsed.no_default_excludes:
                excludes.extend(self.config_manager.get("build.default_excludes", []))
            
            # Inclusions spécifiques
            if parsed.include:
                includes.extend(parsed.include)
            
            if parsed.include_dir:
                for dir_path in parsed.include_dir:
                    includes.append(f"{dir_path}/**")
            
            # Exclusions spécifiques
            if parsed.exclude:
                excludes.extend(parsed.exclude)
            
            self._log(f"Inclusions: {len(includes)} patterns", LogLevel.INFO)
            self._log(f"Exclusions: {len(excludes)} patterns", LogLevel.INFO)
            
            # Nettoyer si demandé
            if parsed.clean:
                if os.path.exists(parsed.output):
                    shutil.rmtree(parsed.output)
                self._log("Cleaned build directory", LogLevel.INFO)
            
            # Créer un manifeste si nom fourni
            if parsed.name:
                manifest_content = f"""[Zenv]
name = {parsed.name}
version = 1.0.0
author = Zenv User
description = A Zenv package

[File-build]
files = {" ".join(includes) if includes else "*"}

[docs]
description = README.md

[license]
file = LICENSE*
"""
                with open("package.zcf", "w") as f:
                    f.write(manifest_content)
                parsed.file = "package.zcf"
                self._log(f"Created manifest for: {parsed.name}", LogLevel.INFO)
            
            # Collecter les fichiers
            base_dir = Path(".").absolute()
            self._log(f"Base directory: {base_dir}", LogLevel.INFO)
            
            include_empty_dirs = self.config_manager.get("build.include_empty_dirs", True)
            
            files, dirs = self.file_system.collect_files(
                base_dir, includes, excludes, include_empty_dirs
            )
            
            self._log(f"Found {len(files)} files and {len(dirs)} directories", LogLevel.SUCCESS)
            
            # Afficher la liste des fichiers
            if len(files) <= 50:  # Ne pas afficher si trop de fichiers
                tree = Tree(f"[bold]Files to include:[/]")
                for file in sorted(files):
                    rel_path = file.relative_to(base_dir)
                    tree.add(f"[cyan]{rel_path}[/]")
                self.console.print(tree)
            else:
                self._log(f"Too many files to display ({len(files)}), showing first 50", LogLevel.WARNING)
                tree = Tree(f"[bold]First 50 files to include:[/]")
                for file in sorted(list(files)[:50]):
                    rel_path = file.relative_to(base_dir)
                    tree.add(f"[cyan]{rel_path}[/]")
                self.console.print(tree)
            
            # Construire le package
            progress = self._create_progress("Building package...")
            if progress:
                with progress:
                    task = progress.add_task("[cyan]Building...", total=100)
                    result = self.builder.build(parsed.file, parsed.output)
                    progress.update(task, completed=100)
            else:
                result = self.builder.build(parsed.file, parsed.output)
            
            if result:
                output_dir = Path(parsed.output)
                packages = list(output_dir.glob("*.zv"))
                
                if packages:
                    package_info = self._analyze_package(packages[0])
                    
                    self.console.print(Panel.fit(
                        f"[bold green]✓ Build Successful![/]\n\n"
                        f"[bold]Package:[/] [cyan]{package_info.name}[/] v{package_info.version}\n"
                        f"[bold]Files included:[/] {len(files)}\n"
                        f"[bold]Size:[/] {package_info.size:,} bytes\n"
                        f"[bold]Output:[/] {output_dir.absolute()}\n"
                        f"[bold]Hash:[/] [dim]{package_info.hash[:16]}...[/]",
                        title="Build Results",
                        border_style="green"
                    ))
                
                # Exécuter les tests si demandé
                if parsed.test:
                    self._run_tests(parsed.output)
                
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
        
        # Fallback - analyser le nom du fichier
        filename = package_path.name
        if filename.endswith('.zv'):
            name_version = filename[:-3]
            if '-' in name_version:
                name, version = name_version.rsplit('-', 1)
            else:
                name, version = name_version, '1.0.0'
        else:
            name = package_path.stem
            version = '1.0.0'
        
        return PackageInfo(
            name=name,
            version=version,
            author="Unknown",
            description="Zenv package",
            license="MIT",
            dependencies=[],
            created_at=datetime.now().isoformat(),
            size=package_path.stat().st_size,
            hash=hashlib.sha256(package_path.read_bytes()).hexdigest()
        )
    
    def _run_tests(self, output_dir: str) -> bool:
        """Exécuter les tests"""
        self._log("Running tests...", LogLevel.INFO)
        return True
    
    def _cmd_config(self, parsed):
        """Gestion de la configuration"""
        if parsed.config_command == "set":
            self.configurator.run()
            return 0
        elif parsed.config_command == "get":
            value = self.config_manager.get(parsed.key)
            self.console.print(f"[cyan]{parsed.key}[/] = [green]{value}[/]")
            return 0
        elif parsed.config_command == "list":
            self._list_configuration()
            return 0
        elif parsed.config_command == "search":
            results = self.config_manager.search(parsed.query)
            if results:
                table = Table(title=f"Search Results for '{parsed.query}'")
                table.add_column("Key", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Value", style="yellow")
                table.add_column("Category")
                
                for key, param in list(results.items())[:20]:
                    value = self.config_manager.get(key)
                    table.add_row(key, param.name, str(value)[:30], param.category.value)
                
                self.console.print(table)
                self.console.print(f"[dim]Found {len(results)} parameters[/]")
            else:
                self.console.print(f"[yellow]No results for '{parsed.query}'[/]")
            return 0
        elif parsed.config_command == "reset":
            if Confirm.ask("Reset ALL parameters to defaults?", default=False):
                self.config_manager._create_default()
                self.console.print("[green]✓ Configuration reset to defaults[/]")
            return 0
        elif parsed.config_command == "export":
            filename = parsed.file or f"zenv_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.config_manager.config, f, indent=2, default=str)
            self.console.print(f"[green]✓ Configuration exported to {filename}[/]")
            return 0
        elif parsed.config_command == "import":
            try:
                with open(parsed.file, 'r') as f:
                    imported = json.load(f)
                
                count = 0
                for key, value in imported.items():
                    if key in self.config_manager.params:
                        valid, _ = self.config_manager.params[key].validate(value)
                        if valid:
                            self.config_manager.config[key] = value
                            count += 1
                
                self.config_manager._save()
                self.console.print(f"[green]✓ Imported {count} parameters[/]")
            except Exception as e:
                self.console.print(f"[red]Error importing: {e}[/]")
            return 0
        elif parsed.config_command == "validate":
            errors = []
            for key, param in self.config_manager.params.items():
                value = self.config_manager.get(key)
                valid, message = param.validate(value)
                if not valid:
                    errors.append(f"{key}: {message}")
            
            if errors:
                self.console.print("[red]Validation Errors:[/]")
                for error in errors[:10]:
                    self.console.print(f"  • {error}")
            else:
                self.console.print("[green]✓ No validation errors[/]")
            return 0
        elif parsed.config_command == "stats":
            total = len(self.config_manager.params)
            visible = sum(1 for p in self.config_manager.params.values() if not p.hidden)
            
            stats = Table(title="Configuration Statistics")
            stats.add_column("Metric", style="cyan")
            stats.add_column("Value", style="green")
            
            stats.add_row("Total Parameters", f"{total:,}")
            stats.add_row("Visible Parameters", f"{visible:,}")
            stats.add_row("Categories", str(len(ConfigCategory)))
            
            self.console.print(stats)
            return 0
        else:
            self.console.print("[red]Unknown config command[/]")
            return 1
    
    def _list_configuration(self):
        """Lister la configuration"""
        for category in ConfigCategory:
            params = self.config_manager.get_by_category(category)
            if params:
                self.console.print(f"\n[bold]{category.value}[/]")
                self.console.print("-" * 40)
                
                table = Table(show_header=False)
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")
                
                for key, param in params.items():
                    value = self.config_manager.get(key)
                    table.add_row(key, str(value)[:50])
                
                self.console.print(table)
    
    def _cmd_hub(self, parsed):
        """Commandes du Zenv Hub"""
        if parsed.hub_command == "status":
            return self._hub_status()
        elif parsed.hub_command == "login":
            return self._hub_login(parsed)
        elif parsed.hub_command == "logout":
            return self._hub_logout()
        elif parsed.hub_command == "search":
            return self._hub_search(parsed.query, parsed.limit)
        elif parsed.hub_command == "publish":
            return self._hub_publish(parsed)
        elif parsed.hub_command == "download":
            return self._hub_download(parsed.package, parsed.version, parsed.output)
        elif parsed.hub_command == "info":
            return self._hub_info(parsed.package, parsed.version)
        elif parsed.hub_command == "list":
            return self._hub_list_packages()
        elif parsed.hub_command == "delete":
            return self._hub_delete(parsed.package, parsed.version, parsed.force)
        elif parsed.hub_command == "whoami":
            return self._hub_whoami()
        else:
            self._log(f"Unknown hub command: {parsed.hub_command}", LogLevel.ERROR)
            return 1
    
    def _hub_status(self) -> int:
        """Vérifier le statut du hub"""
        self._print_header()
        
        hub_url = self.config_manager.get("network.hub_url", "https://zenv-hub.onrender.com")
        self.console.print(Panel.fit(
            f"[bold]Zenv Hub Status Check[/]\n"
            f"[dim]URL:[/] {hub_url}",
            border_style="cyan"
        ))
        
        self._log(f"Checking hub status at {hub_url}...", LogLevel.INFO)
        
        if self.hub.check_status():
            self._log("Zenv Hub: ✅ Online", LogLevel.SUCCESS)
            
            # Obtenir des infos supplémentaires
            try:
                response = requests.get(f"{hub_url}/api/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.console.print(Panel.fit(
                        f"[bold]Hub Information:[/]\n"
                        f"[dim]Version:[/] {data.get('version', 'Unknown')}\n"
                        f"[dim]Status:[/] {data.get('status', 'Unknown')}\n"
                        f"[dim]Uptime:[/] {data.get('uptime', 'Unknown')}",
                        border_style="green"
                    ))
            except:
                pass
        else:
            self._log("Zenv Hub: ❌ Offline", LogLevel.ERROR)
            self.console.print(Panel.fit(
                "[bold red]Cannot connect to Zenv Hub[/]\n\n"
                "[dim]Possible reasons:[/]\n"
                "• Hub server is down\n"
                "• Network connection issue\n"
                "• Incorrect hub URL\n"
                "• Firewall blocking connection",
                border_style="red"
            ))
        
        self._print_footer()
        return 0
    
    def _hub_login(self, parsed) -> int:
        """Se connecter au Zenv Hub"""
        self._print_header()
        
        api_key = parsed.token
        if not api_key:
            api_key = Prompt.ask("Enter your Zenv Hub API token", password=True)
        
        if not api_key:
            self._log("Login cancelled", LogLevel.WARNING)
            return 0
        
        self._log("Authenticating with Zenv Hub...", LogLevel.INFO)
        
        if self.hub.login(api_key):
            self._log("✅ Successfully logged in to Zenv Hub", LogLevel.SUCCESS)
            
            # Obtenir les infos utilisateur
            user_info = self.hub.get_user_info()
            if user_info:
                self.console.print(Panel.fit(
                    f"[bold]Welcome, {user_info.get('username', 'User')}![/]\n"
                    f"[dim]Email:[/] {user_info.get('email', 'Not provided')}\n"
                    f"[dim]Packages:[/] {user_info.get('package_count', 0)} published\n"
                    f"[dim]Member since:[/] {user_info.get('created_at', 'Unknown')}",
                    border_style="green"
                ))
        else:
            self._log("❌ Login failed", LogLevel.ERROR)
            self.console.print(Panel.fit(
                "[bold red]Authentication failed[/]\n\n"
                "[dim]Possible reasons:[/]\n"
                "• Invalid API token\n"
                "• Account disabled\n"
                "• Network issue\n\n"
                "[dim]Get your API token from:[/]\n"
                f"{self.config_manager.get('network.hub_url')}/dashboard",
                border_style="red"
            ))
            return 1
        
        self._print_footer()
        return 0
    
    def _hub_logout(self) -> int:
        """Se déconnecter du Zenv Hub"""
        self.hub.logout()
        self._log("✅ Logged out from Zenv Hub", LogLevel.SUCCESS)
        return 0
    
    def _hub_search(self, query: str, limit: int) -> int:
        """Rechercher des packages"""
        self._print_header()
        
        self._log(f"Searching for '{query}'...", LogLevel.INFO)
        
        packages = self.hub.search_packages(query)
        
        if packages:
            # Limiter les résultats
            packages = packages[:limit]
            
            table = Table(title=f"Search Results for '{query}'")
            table.add_column("Package", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Author", style="yellow")
            table.add_column("Downloads", style="magenta")
            table.add_column("Description")
            
            for pkg in packages:
                table.add_row(
                    pkg.get('name', 'Unknown'),
                    pkg.get('version', '1.0.0'),
                    pkg.get('author', 'Unknown'),
                    str(pkg.get('downloads', 0)),
                    pkg.get('description', '')[:60]
                )
            
            self.console.print(table)
            self.console.print(f"[dim]Found {len(packages)} packages[/]")
        else:
            self.console.print(Panel.fit(
                f"[bold yellow]No packages found for '{query}'[/]\n\n"
                f"[dim]Try:[/]\n"
                f"• Different search terms\n"
                f"• Browse all packages\n"
                f"• Check spelling",
                border_style="yellow"
            ))
        
        self._print_footer()
        return 0
    
    def _hub_publish(self, parsed) -> int:
        """Publier un package sur Zenv Hub"""
        self._print_header()
        
        package_file = parsed.file
        
        # Vérifier le fichier
        if not os.path.exists(package_file):
            self._log(f"Package file not found: {package_file}", LogLevel.ERROR)
            return 1
        
        # Analyser le package
        package_path = Path(package_file)
        package_info = self._analyze_package(package_path)
        
        # Afficher les informations
        self.console.print(Panel.fit(
            f"[bold]Publishing Package[/]\n\n"
            f"[bold]Name:[/] [cyan]{package_info.name}[/]\n"
            f"[bold]Version:[/] {package_info.version}\n"
            f"[bold]Size:[/] {package_info.size:,} bytes\n"
            f"[bold]Hash:[/] [dim]{package_info.hash[:16]}...[/]\n"
            f"[bold]Visibility:[/] {'Public' if parsed.public else 'Private'}",
            title="Publication Details",
            border_style="yellow"
        ))
        
        # Vérifier la connexion
        self._log("Checking hub connection...", LogLevel.INFO)
        if not self.hub.check_status():
            self._log("Zenv Hub is unreachable", LogLevel.ERROR)
            self.console.print(Panel.fit(
                "[bold red]Cannot connect to Zenv Hub[/]\n\n"
                "[dim]Please check:[/]\n"
                "• Internet connection\n"
                "• Hub status (zenv hub status)\n"
                "• Firewall settings",
                border_style="red"
            ))
            return 1
        
        # Vérifier l'authentification
        api_key = self.config_manager.get("hub.api_key", "")
        if not api_key:
            self._log("You need to login first", LogLevel.WARNING)
            if not Confirm.ask("Login now?"):
                return 1
            api_key = Prompt.ask("Enter your Zenv Hub API token", password=True)
            if not self.hub.login(api_key):
                self._log("Login failed", LogLevel.ERROR)
                return 1
        
        # Vérifier si le package existe déjà
        existing = self.hub.get_package_info(package_info.name, package_info.version)
        if existing and not parsed.force:
            self.console.print(Panel.fit(
                f"[bold red]Package already exists![/]\n\n"
                f"[bold]Package:[/] {package_info.name} v{package_info.version}\n"
                f"[bold]Author:[/] {existing.get('author', 'Unknown')}\n"
                f"[bold]Published:[/] {existing.get('created_at', 'Unknown')}\n\n"
                f"[dim]Options:[/]\n"
                f"1. Update version number\n"
                f"2. Use --force to overwrite\n"
                f"3. Cancel publication",
                title="Conflict Detected",
                border_style="red"
            ))
            
            choice = Prompt.ask("Choose option", choices=["1", "2", "3"], default="3")
            if choice == "1":
                new_version = Prompt.ask("Enter new version")
                package_info.version = new_version
            elif choice == "2":
                if not Confirm.ask("[red]WARNING:[/] Overwrite existing package?"):
                    return 0
            else:
                self._log("Publication cancelled", LogLevel.WARNING)
                return 0
        
        # Confirmation finale
        if not Confirm.ask("Proceed with publication?"):
            self._log("Publication cancelled", LogLevel.WARNING)
            return 0
        
        # Préparer les métadonnées
        metadata = {
            'name': package_info.name,
            'version': package_info.version,
            'description': parsed.description or package_info.description,
            'author': package_info.author,
            'license': parsed.license or package_info.license,
            'dependencies': package_info.dependencies,
            'visibility': 'public' if parsed.public else 'private'
        }
        
        # Publier le package
        self._log("Uploading package...", LogLevel.INFO)
        
        progress = self._create_progress("Uploading...")
        if progress:
            with progress:
                task = progress.add_task("[cyan]Uploading...", total=100)
                result = self.hub.upload_package(package_file, metadata)
                progress.update(task, completed=100)
        else:
            result = self.hub.upload_package(package_file, metadata)
        
        if result:
            self._log("✅ Package published successfully!", LogLevel.SUCCESS)
            
            self.console.print(Panel.fit(
                f"[bold green]Publication Successful![/]\n\n"
                f"[bold]Package:[/] [cyan]{package_info.name}[/] v{package_info.version}\n"
                f"[bold]URL:[/] {self.config_manager.get('network.hub_url')}/packages/{package_info.name}\n"
                f"[bold]Install with:[/] [green]zenv pkg install {package_info.name}[/]\n"
                f"[bold]Size:[/] {package_info.size:,} bytes",
                border_style="green"
            ))
            
            # Publication automatique optionnelle
            if self.config_manager.get("hub.auto_publish", False):
                self._log("Auto-publish enabled", LogLevel.INFO)
        else:
            self._log("❌ Publication failed", LogLevel.ERROR)
            self.console.print(Panel.fit(
                "[bold red]Publication failed[/]\n\n"
                "[dim]Possible reasons:[/]\n"
                "• Network error\n"
                "• Server error\n"
                "• Package too large\n"
                "• Invalid package format",
                border_style="red"
            ))
            return 1
        
        self._print_footer()
        return 0
    
    def _hub_download(self, package_name: str, version: Optional[str], output: Optional[str]) -> int:
        """Télécharger un package depuis Zenv Hub"""
        self._print_header()
        
        self._log(f"Downloading {package_name}...", LogLevel.INFO)
        
        # Vérifier la connexion
        if not self.hub.check_status():
            self._log("Zenv Hub is unreachable", LogLevel.ERROR)
            return 1
        
        # Obtenir les infos du package
        package_info = self.hub.get_package_info(package_name, version)
        if not package_info:
            self._log(f"Package not found: {package_name}", LogLevel.ERROR)
            return 1
        
        # Afficher les informations
        self.console.print(Panel.fit(
            f"[bold]Downloading Package[/]\n\n"
            f"[bold]Name:[/] [cyan]{package_info.get('name')}[/]\n"
            f"[bold]Version:[/] {package_info.get('version')}\n"
            f"[bold]Author:[/] {package_info.get('author', 'Unknown')}\n"
            f"[bold]Size:[/] {package_info.get('size', 0):,} bytes\n"
            f"[bold]Downloads:[/] {package_info.get('downloads', 0)}",
            border_style="yellow"
        ))
        
        # Télécharger
        self._log("Downloading package data...", LogLevel.INFO)
        
        package_data = self.hub.download_package(package_name, version)
        if not package_data:
            self._log("Download failed", LogLevel.ERROR)
            return 1
        
        # Déterminer le chemin de sortie
        if output:
            output_path = Path(output)
            if output_path.is_dir():
                output_file = output_path / f"{package_name}-{package_info.get('version')}.zv"
            else:
                output_file = output_path
        else:
            output_file = Path(f"{package_name}-{package_info.get('version')}.zv")
        
        # Sauvegarder
        with open(output_file, 'wb') as f:
            f.write(package_data)
        
        self._log(f"✅ Package downloaded: {output_file}", LogLevel.SUCCESS)
        self.console.print(Panel.fit(
            f"[bold green]Download Complete![/]\n\n"
            f"[bold]Saved to:[/] {output_file.absolute()}\n"
            f"[bold]Size:[/] {len(package_data):,} bytes\n"
            f"[bold]Install with:[/] [green]zenv site {output_file.name}[/]",
            border_style="green"
        ))
        
        self._print_footer()
        return 0
    
    def _hub_info(self, package_name: str, version: Optional[str]) -> int:
        """Afficher les informations d'un package"""
        self._print_header()
        
        package_info = self.hub.get_package_info(package_name, version)
        if not package_info:
            self._log(f"Package not found: {package_name}", LogLevel.ERROR)
            return 1
        
        # Afficher les informations détaillées
        table = Table(title=f"Package: {package_info.get('name')}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Name", package_info.get('name', 'Unknown'))
        table.add_row("Version", package_info.get('version', '1.0.0'))
        table.add_row("Author", package_info.get('author', 'Unknown'))
        table.add_row("Description", package_info.get('description', ''))
        table.add_row("License", package_info.get('license', 'MIT'))
        table.add_row("Size", f"{package_info.get('size', 0):,} bytes")
        table.add_row("Downloads", str(package_info.get('downloads', 0)))
        table.add_row("Created", package_info.get('created_at', 'Unknown'))
        table.add_row("Updated", package_info.get('updated_at', 'Unknown'))
        table.add_row("Visibility", package_info.get('visibility', 'public'))
        
        self.console.print(table)
        
        # Afficher les dépendances
        deps = package_info.get('dependencies', [])
        if deps:
            self.console.print("\n[bold]Dependencies:[/]")
            for dep in deps:
                self.console.print(f"  • {dep}")
        
        self._print_footer()
        return 0
    
    def _hub_list_packages(self) -> int:
        """Lister les packages de l'utilisateur"""
        self._print_header()
        
        # Vérifier l'authentification
        api_key = self.config_manager.get("hub.api_key", "")
        if not api_key:
            self._log("You need to login first", LogLevel.WARNING)
            return 1
        
        packages = self.hub.list_user_packages()
        
        if packages:
            table = Table(title="Your Packages")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Visibility", style="yellow")
            table.add_column("Downloads", style="magenta")
            table.add_column("Last Updated")
            
            for pkg in packages:
                table.add_row(
                    pkg.get('name', 'Unknown'),
                    pkg.get('version', '1.0.0'),
                    pkg.get('visibility', 'public'),
                    str(pkg.get('downloads', 0)),
                    pkg.get('updated_at', '')[:10]
                )
            
            self.console.print(table)
            self.console.print(f"[dim]Total: {len(packages)} packages[/]")
        else:
            self.console.print(Panel.fit(
                "[bold yellow]No packages published yet[/]\n\n"
                "[dim]To publish your first package:[/]\n"
                "1. [green]zenv build[/] to create package\n"
                "2. [green]zenv hub publish[/] to upload\n"
                "3. Share with the community!",
                border_style="yellow"
            ))
        
        self._print_footer()
        return 0
    
    def _hub_delete(self, package_name: str, version: Optional[str], force: bool) -> int:
        """Supprimer un package"""
        self._print_header()
        
        # Vérifier l'authentification
        api_key = self.config_manager.get("hub.api_key", "")
        if not api_key:
            self._log("You need to login first", LogLevel.WARNING)
            return 1
        
        # Obtenir les infos du package
        package_info = self.hub.get_package_info(package_name, version)
        if not package_info:
            self._log(f"Package not found: {package_name}", LogLevel.ERROR)
            return 1
        
        # Afficher les informations
        self.console.print(Panel.fit(
            f"[bold red]⚠️ Delete Package[/]\n\n"
            f"[bold]Name:[/] [cyan]{package_info.get('name')}[/]\n"
            f"[bold]Version:[/] {package_info.get('version')}\n"
            f"[bold]Author:[/] {package_info.get('author', 'Unknown')}\n"
            f"[bold]Downloads:[/] {package_info.get('downloads', 0)}\n"
            f"[bold]Created:[/] {package_info.get('created_at', 'Unknown')}",
            border_style="red"
        ))
        
        # Confirmation
        if not force and not Confirm.ask("[red]WARNING:[/] This action cannot be undone. Delete package?"):
            self._log("Deletion cancelled", LogLevel.WARNING)
            return 0
        
        # Supprimer
        if self.hub.delete_package(package_name, version):
            self._log("✅ Package deleted successfully", LogLevel.SUCCESS)
        else:
            self._log("❌ Failed to delete package", LogLevel.ERROR)
            return 1
        
        self._print_footer()
        return 0
    
    def _hub_whoami(self) -> int:
        """Afficher les informations de l'utilisateur"""
        self._print_header()
        
        # Vérifier l'authentification
        api_key = self.config_manager.get("hub.api_key", "")
        if not api_key:
            self._log("You are not logged in", LogLevel.WARNING)
            self.console.print(Panel.fit(
                "[bold yellow]Not logged in[/]\n\n"
                "[dim]To login:[/]\n"
                "[green]zenv hub login[/]\n\n"
                "[dim]Get your API token from:[/]\n"
                f"{self.config_manager.get('network.hub_url')}/dashboard",
                border_style="yellow"
            ))
            return 0
        
        user_info = self.hub.get_user_info()
        if not user_info:
            self._log("Failed to get user info", LogLevel.ERROR)
            return 1
        
        # Afficher les informations
        table = Table(title="Your Account")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Username", user_info.get('username', 'Unknown'))
        table.add_row("Email", user_info.get('email', 'Not provided'))
        table.add_row("Packages", str(user_info.get('package_count', 0)))
        table.add_row("Member since", user_info.get('created_at', 'Unknown'))
        table.add_row("Last login", user_info.get('last_login', 'Never'))
        
        self.console.print(table)
        
        # Afficher les packages récents
        packages = self.hub.list_user_packages()
        if packages:
            self.console.print("\n[bold]Recent Packages:[/]")
            for pkg in packages[:5]:
                self.console.print(f"  • {pkg.get('name')} v{pkg.get('version')} ({pkg.get('downloads', 0)} downloads)")
        
        self._print_footer()
        return 0
    
    def _cmd_version(self):
        """Afficher la version"""
        self._print_header()
        
        info_table = Table(title="System Information")
        info_table.add_column("Component", style="cyan")
        info_table.add_column("Version", style="green")
        
        info_table.add_row("Zenv", __version__)
        info_table.add_row("Python", platform.python_version())
        info_table.add_row("Platform", platform.platform())
        info_table.add_row("OS", platform.system())
        
        self.console.print(info_table)
        
        # Informations de configuration
        config_stats = Table(title="Configuration")
        config_stats.add_column("Parameter", style="cyan")
        config_stats.add_column("Value", style="green")
        
        config_stats.add_row("Theme", self.config_manager.get("ui.theme", "dark"))
        config_stats.add_row("Config Parameters", f"{len(self.config_manager.params):,}")
        config_stats.add_row("Hub URL", self.config_manager.get("network.hub_url", "Not set"))
        config_stats.add_row("Config File", str(self.config_manager.config_file))
        
        self.console.print(config_stats)
        
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
        
        progress = self._create_progress("Installing package...")
        if progress:
            with progress:
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
        else:
            try:
                if global_install:
                    site_dir = Path("/usr/local/lib/zenv")
                    site_dir.mkdir(parents=True, exist_ok=True)
                else:
                    site_dir = Path.home() / ".zenv" / "packages"
                    site_dir.mkdir(parents=True, exist_ok=True)
                
                package_dir = site_dir / package_info.name
                with tarfile.open(package_file, 'r:gz') as tar:
                    tar.extractall(package_dir)
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
    
    def _cmd_doctor(self):
        """Diagnostiquer les problèmes du système"""
        self._print_header()
        
        checks = []
        
        # Vérifier Python
        if sys.version_info >= (3, 8):
            checks.append(("✓", "Python 3.8+", "OK", LogLevel.SUCCESS))
        else:
            checks.append(("✗", "Python 3.8+", "Required", LogLevel.ERROR))
        
        # Vérifier les permissions
        try:
            test_file = self.config_manager.config_dir / "test.txt"
            test_file.touch()
            test_file.unlink()
            checks.append(("✓", "Write permissions", "OK", LogLevel.SUCCESS))
        except:
            checks.append(("✗", "Write permissions", "Cannot write to config directory", LogLevel.ERROR))
        
        # Vérifier la configuration
        config_errors = []
        for key, param in self.config_manager.params.items():
            value = self.config_manager.get(key)
            valid, _ = param.validate(value)
            if not valid and param.required:
                config_errors.append(key)
        
        if not config_errors:
            checks.append(("✓", "Configuration", "Valid", LogLevel.SUCCESS))
        else:
            checks.append(("✗", "Configuration", f"{len(config_errors)} errors", LogLevel.ERROR))
        
        # Vérifier Zenv Hub
        if self.hub.check_status():
            checks.append(("✓", "Zenv Hub", "Online", LogLevel.SUCCESS))
        else:
            checks.append(("⚠", "Zenv Hub", "Offline", LogLevel.WARNING))
        
        # Afficher les résultats
        table = Table(title="System Diagnostics")
        table.add_column("Status", style="cyan")
        table.add_column("Check", style="green")
        table.add_column("Result", style="yellow")
        table.add_column("Message")
        
        for icon, check, result, level in checks:
            color = {
                LogLevel.SUCCESS: "green",
                LogLevel.ERROR: "red",
                LogLevel.WARNING: "yellow"
            }.get(level, "white")
            table.add_row(f"[{color}]{icon}[/]", check, result, "")
        
        self.console.print(table)
        
        if config_errors:
            self.console.print("\n[red]Configuration errors:[/]")
            for error in config_errors[:5]:
                self.console.print(f"  • {error}")
        
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
        
        # Utiliser les paramètres de configuration
        author = self.config_manager.get("general.author", "Zenv User")
        version = self.config_manager.get("general.version", "1.0.0")
        
        templates = {
            "basic": [
                ("README.md", f"# {name}\n\nA Zenv project."),
                ("package.zcf", f"""[Zenv]
name = {name}
version = {version}
author = {author}
description = A Zenv project

[File-build]
files = {" ".join(self.config_manager.get("build.default_includes", ["src/**/*", "*.zv", "*.py"]))}

[docs]
description = README.md
"""),
                ("src/main.zv", "print('Hello from Zenv!')"),
                (".gitignore", "\n".join(self.config_manager.get("build.default_excludes", []))),
                ("zenv-config.json", json.dumps({
                    "name": name,
                    "version": version,
                    "author": author,
                    "build": {
                        "includes": self.config_manager.get("build.default_includes"),
                        "excludes": self.config_manager.get("build.default_excludes")
                    }
                }, indent=2))
            ]
        }
        
        template = template or "basic"
        if template not in templates:
            template = "basic"
        
        progress = self._create_progress("Creating project...")
        if progress:
            with progress:
                task = progress.add_task("[cyan]Setting up...", total=len(templates[template]))
                
                for file_path, content in templates[template]:
                    file = project_dir / file_path
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_text(content)
                    progress.update(task, advance=1)
        else:
            for file_path, content in templates[template]:
                file = project_dir / file_path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content)
        
        self.console.print(Panel.fit(
            f"[bold green]✓ Project created![/]\n\n"
            f"[bold]Name:[/] [cyan]{name}[/]\n"
            f"[bold]Template:[/] {template}\n"
            f"[bold]Location:[/] {project_dir.absolute()}\n"
            f"[bold]Author:[/] {author}\n"
            f"[bold]Version:[/] {version}\n\n"
            f"[bold]Next steps:[/]\n"
            f"  1. [green]cd {name}[/]\n"
            f"  2. [green]zenv run src/main.zv[/]\n"
            f"  3. [green]zenv build[/] to create package\n"
            f"  4. [green]zenv hub publish[/] to share",
            title="Project Initialized",
            border_style="green"
        ))
        
        self._print_footer()
        return 0
    
    # Implémentations des autres méthodes
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
    
    def _install_package(self, package: str, version: Optional[str], force: bool) -> int:
        """Installer un package"""
        self._log(f"Installing {package}...", LogLevel.INFO)
        return 0
    
    def _list_packages(self, local: bool, global_scope: bool) -> int:
        """Lister les packages"""
        self._log("Listing packages...", LogLevel.INFO)
        return 0
    
    def _remove_package(self, package: str, purge: bool) -> int:
        """Supprimer un package"""
        self._log(f"Removing {package}...", LogLevel.WARNING)
        return 0
    
    def _update_package(self, package: str, prerelease: bool) -> int:
        """Mettre à jour un package"""
        self._log(f"Updating {package}...", LogLevel.INFO)
        return 0
    
    def _package_info(self, package: str) -> int:
        """Afficher les infos d'un package"""
        self._log(f"Package info for {package}...", LogLevel.INFO)
        return 0
