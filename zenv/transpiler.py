import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Pattern
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"
    PUNCTUATION = "PUNCTUATION"
    COMMENT = "COMMENT"
    WHITESPACE = "WHITESPACE"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class ZenvTranspiler:
    
    ZENV_SYNTAX = {
        # Print statements - CORRIGÉ
        r'print\s+(.+)': r'print(\1)',
        
        # Import statements
        r'^import\s+([\w\.\-]+)\s+as\s+(\w+)$': r'import \1 as \2',
        r'^from\s+([\w\.\-]+)\s+import\s+([\w\s,]+)$': r'from \1 import \2',
        r'^from\s+([\w\.\-]+)\s+import\s+all$': r'from \1 import *',
        
        # Control structures
        r'^if\s+(.+?)\s+then\s*$': r'if \1:',
        r'^elif\s+(.+?)\s+then\s*$': r'elif \1:',
        r'^else\s*$': r'else:',
        r'^for\s+(\w+)\s+in\s+(.+?)\s+do\s*$': r'for \1 in \2:',
        r'^while\s+(.+?)\s+do\s*$': r'while \1:',
        r'^repeat\s+(\d+)\s+times\s*:\s*$': r'for _ in range(\1):',
        
        # Function definitions - CORRIGÉ
        r'^function\s+(\w+)\((.+?)\)\s*:\s*$': r'def \1(\2):',
        r'^function\s+(\w+)\(\)\s*:\s*$': r'def \1():',
        r'^func\s+(\w+)\((.+?)\)\s*:\s*$': r'def \1(\2):',
        
        # Classes - CORRIGÉ
        r'^class\s+(\w+)\s*:\s*$': r'class \1:',
        r'^class\s+(\w+)\s+extends\s+(\w+)\s*:\s*$': r'class \1(\2):',
        
        # Return
        r'^return\s+(.+)$': r'return \1',
        
        # Variable declarations
        r'^var\s+(\w+)\s+=\s+(.+)$': r'\1 = \2',
        r'^const\s+(\w+)\s+=\s+(.+)$': r'\1 = \2',
        r'^let\s+(\w+)\s+=\s+(.+)$': r'\1 = \2',
        
        # Data types
        r'list\s*\(\s*\)': r'[]',
        r'list\s*\(\s*(.+?)\s*\)': r'[\1]',
        r'dict\s*\(\s*\)': r'{}',
        r'set\s*\(\s*\)': r'set()',
        
        # String interpolation
        r'`([^`]*)`': r"r'\1'",
        r'string\s*`([^`]*)`': r"'\1'",
        r'"([^"]*)#\{([^}]+)\}([^"]*)"': r'f"\1{\2}\3"',
        r"'([^']*)#\{([^}]+)\}([^']*)'": r"f'\1{\2}\3'",
        
        # Special operators
        r'(\w+)\s+is\s+(\w+)': r'\1 is \2',
        r'(\w+)\s+is\s+not\s+(\w+)': r'\1 is not \2',
        r'(\w+)\s+and\s+(\w+)': r'\1 and \2',
        r'(\w+)\s+or\s+(\w+)': r'\1 or \2',
        
        # Main function
        r'^main\s*\(\s*\)\s*:\s*$': r'def main():',
        
        # Error handling
        r'^try\s*:\s*$': r'try:',
        r'^catch\s+(\w+)\s*:\s*$': r'except \1:',
        r'^finally\s*:\s*$': r'finally:',
        r'^raise\s+(.+)$': r'raise \1',
        
        # Comments
        r'^//\s*(.+)$': r'# \1',
        r'^/\*\s*(.+?)\s*\*/$': r'"""\1"""',
        
        # Async
        r'^async\s+function\s+(\w+)\((.+?)\)\s*:\s*$': r'async def \1(\2):',
        r'^async\s+func\s+(\w+)\((.+?)\)\s*:\s*$': r'async def \1(\2):',
        r'^await\s+(.+)$': r'await \1',
    }
    
    ZENV_KEYWORDS = {
        'true': 'True',
        'false': 'False',
        'null': 'None',
        'none': 'None',
        'and': 'and',
        'or': 'or',
        'not': 'not',
        'is': 'is',
    }
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.rules: List[Tuple[Pattern, str]] = []
        self._setup_rules()
        
    def _setup_rules(self):
        for pattern, replacement in self.ZENV_SYNTAX.items():
            self.rules.append((re.compile(pattern), replacement))
    
    def transpile(self, zv_code: str) -> str:
        lines = zv_code.split('\n')
        result = []
        
        for line in lines:
            transpiled_line = line
            
            # Apply all syntax rules
            for pattern, replacement in self.rules:
                transpiled_line = pattern.sub(replacement, transpiled_line)
            
            # Replace keywords
            for zenv, python in self.ZENV_KEYWORDS.items():
                transpiled_line = re.sub(r'\b' + zenv + r'\b', python, transpiled_line)
            
            result.append(transpiled_line)
        
        return '\n'.join(result)
    
    def transpile_file(self, input_file: str, output_file: Optional[str] = None) -> str:
        with open(input_file, 'r', encoding='utf-8') as f:
            zv_code = f.read()
        
        python_code = self.transpile(zv_code)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(python_code)
        
        return python_code
    
    def validate(self, zv_code: str) -> Tuple[bool, Optional[str]]:
        try:
            python_code = self.transpile(zv_code)
            ast.parse(python_code)
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {e}"
