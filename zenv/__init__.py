"""
Écosystème Zenv - Runtime, CLI et Package Manager complet
"""

__version__ = "1.0.0"
__author__ = "Zenv Team"
__license__ = "MIT"

import sys
import os

# Configuration globale
ZENV_HOME = os.path.join(os.path.expanduser("~"), ".zenv")
ZENV_CACHE = os.path.join(ZENV_HOME, "cache")
ZENV_PACKAGES = os.path.join(ZENV_HOME, "packages")

# Créer les dossiers nécessaires
for path in [ZENV_HOME, ZENV_CACHE, ZENV_PACKAGES]:
    os.makedirs(path, exist_ok=True)

# Exports publics
from .runtime.run import ZenvRuntime
from .command.com import ZenvCommand, ZenvCLI
from .transpiler.tra import ZenvTranspiler
from .builder.build import ZenvBuilder, ZenvManifest

__all__ = [
    'ZenvRuntime',
    'ZenvCommand', 
    'ZenvCLI',
    'ZenvTranspiler',
    'ZenvBuilder',
    'ZenvManifest',
]
