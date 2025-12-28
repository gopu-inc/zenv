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
    
    ZENV_SYNTAX = [
        # IMPORTANT: L'ordre des règles est crucial!
        
        # 1. D'abord les commentaires multi-lignes
        (r'/\*(.*?)\*/', r'"""\1"""'),
        
        # 2. Les fonctions et classes (doivent venir AVANT les mots-clés simples)
        (r'^\s*function\s+(\w+)\s*\((.*?)\)\s*:', r'def \1(\2):'),
        (r'^\s*function\s+(\w+)\s*\(\)\s*:', r'def \1():'),
        (r'^\s*func\s+(\w+)\s*\((.*?)\)\s*:', r'def \1(\2):'),
        (r'^\s*class\s+(\w+)\s*:', r'class \1:'),
        (r'^\s*class\s+(\w+)\s+extends\s+(\w+)\s*:', r'class \1(\2):'),
        
        # 3. Les déclarations avec "self"
        (r'function\s+(\w+)\s*\(\s*self\s*,\s*(.*?)\)\s*:', r'def \1(self, \2):'),
        (r'function\s+(\w+)\s*\(\s*self\s*\)\s*:', r'def \1(self):'),
        
        # 4. Les structures de contrôle
        (r'if\s+(.+?)\s+then\s*:', r'if \1:'),
        (r'elif\s+(.+?)\s+then\s*:', r'elif \1:'),
        (r'else\s*:', r'else:'),
        (r'for\s+(\w+)\s+in\s+(.+?)\s+do\s*:', r'for \1 in \2:'),
        (r'while\s+(.+?)\s+do\s*:', r'while \1:'),
        
        # 5. Les print statements (doivent venir après les fonctions)
        (r'print\s+(.+)', r'print(\1)'),
        
        # 6. Les return
        (r'return\s+(.+)', r'return \1'),
        
        # 7. Les déclarations de variables
        (r'var\s+(\w+)\s*=\s*(.+)', r'\1 = \2'),
        (r'let\s+(\w+)\s*=\s*(.+)', r'\1 = \2'),
        (r'const\s+(\w+)\s*=\s*(.+)', r'\1 = \2'),
        
        # 8. Les structures de données
        (r'list\s*\(\s*\)', r'[]'),
        (r'list\s*\((.*?)\)', r'[\1]'),
        (r'dict\s*\(\s*\)', r'{}'),
        (r'set\s*\(\s*\)', r'set()'),
        
        # 9. Les string interpolation
        (r'`(.*?)`', r"r'\1'"),
        (r'"([^"]*)#\{([^}]+)\}([^"]*)"', r'f"\1{\2}\3"'),
        
        # 10. Les commentaires simples (doivent venir à la fin)
        (r'^\s*//\s*(.*)', r'# \1'),
    ]
    
    ZENV_KEYWORDS = {
        'true': 'True',
        'false': 'False',
        'null': 'None',
        'none': 'None',
        'and': 'and',
        'or': 'or',
        'not': 'not',
        'is': 'is',
        'in': 'in',
        'range': 'range',
        'len': 'len',
        'str': 'str',
        'int': 'int',
    }
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.rules: List[Tuple[Pattern, str]] = []
        self._setup_rules()
        
    def _setup_rules(self):
        for pattern, replacement in self.ZENV_SYNTAX:
            self.rules.append((re.compile(pattern, re.DOTALL), replacement))
    
    def transpile(self, zv_code: str) -> str:
        lines = zv_code.split('\n')
        result_lines = []
        
        for line in lines:
            original_line = line
            transpiled_line = line
            
            # Appliquer les règles de syntaxe
            for pattern, replacement in self.rules:
                transpiled_line = pattern.sub(replacement, transpiled_line)
            
            # Remplacer les mots-clés (seulement les mots entiers)
            for zenv, python in self.ZENV_KEYWORDS.items():
                transpiled_line = re.sub(r'\b' + re.escape(zenv) + r'\b', python, transpiled_line)
            
            # Préserver l'indentation
            if transpiled_line != line:
                # Garder l'indentation originale
                indent = len(original_line) - len(original_line.lstrip())
                if indent > 0:
                    transpiled_line = ' ' * indent + transpiled_line.lstrip()
            
            result_lines.append(transpiled_line)
        
        return '\n'.join(result_lines)
    
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
