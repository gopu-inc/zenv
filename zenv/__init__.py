"""
Zenv Programming Language
A modern, expressive language that transpiles to Python
"""

__version__ = "1.0.0"
__author__ = "Zenv Team"
__license__ = "MIT"

from .transpiler import ZenvTranspiler
from .runtime import ZenvRuntime
from .builder import ZenvBuilder
from .cli import ZenvCLI

__all__ = [
    'ZenvTranspiler',
    'ZenvRuntime', 
    'ZenvBuilder',
    'ZenvCLI',
    'execute',
    'transpile',
    'compile'
]

def execute(source: str, args: list = None):
    """Execute Zenv code directly"""
    from .runtime import ZenvRuntime
    runtime = ZenvRuntime()
    return runtime.execute_string(source, args or [])

def transpile(source: str) -> str:
    """Transpile Zenv code to Python"""
    from .transpiler import ZenvTranspiler
    transpiler = ZenvTranspiler()
    return transpiler.transpile(source)

def compile(source: str, output_file: str = None):
    """Compile Zenv code to Python file"""
    from .transpiler import ZenvTranspiler
    transpiler = ZenvTranspiler()
    return transpiler.transpile_to_file(source, output_file)
