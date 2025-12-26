# zenv_transpiler/__init__.py
"""
Zenv Transpiler - Un transpileur de .zv/.zenv vers Python
"""

from .transpiler import (
    transpile_string,
    transpile_file,
    transpile_directory,
    validate_zv_code,
    get_zv_version,
    get_supported_features,
    ZvSyntaxError,
    BRAND
)

from .cli import main

__version__ = get_zv_version()
__author__ = "Votre Nom"
__description__ = "Transpileur Zenv vers Python"

__all__ = [
    'transpile_string',
    'transpile_file',
    'transpile_directory',
    'validate_zv_code',
    'get_zv_version',
    'get_supported_features',
    'ZvSyntaxError',
    'BRAND',
    'main',
    '__version__',
    '__author__',
    '__description__'
]
