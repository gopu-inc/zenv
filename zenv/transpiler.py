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
        # 1. Commentaires multi-lignes
        (r'/\*(.*?)\*/', r'"""\1"""', re.DOTALL),
        
        # 2. Commentaires simples
        (r'^\s*//\s*(.*)', r'# \1'),
        
        # 3. Structures de contrôle - CORRIGÉ: gérer "then:" et "do:"
        (r'if\s+(.+?)\s+then\s*:', r'if \1:'),
        (r'elif\s+(.+?)\s+then\s*:', r'elif \1:'),
        (r'else\s*:', r'else:'),
        (r'for\s+(\w+)\s+in\s+(.+?)\s+do\s*:', r'for \1 in \2:'),
        (r'while\s+(.+?)\s+do\s*:', r'while \1:'),
        
        # 4. Fonctions et classes
        (r'function\s+(\w+)\s*\((.*?)\)\s*:', r'def \1(\2):'),
        (r'function\s+(\w+)\s*\(\)\s*:', r'def \1():'),
        (r'class\s+(\w+)\s*:', r'class \1:'),
        
        # 5. Fonctions avec self
        (r'function\s+(\w+)\s*\(\s*self\s*,\s*(.*?)\)\s*:', r'def \1(self, \2):'),
        (r'function\s+(\w+)\s*\(\s*self\s*\)\s*:', r'def \1(self):'),
        
        # 6. Print et return
        (r'print\s+(.+)', r'print(\1)'),
        (r'return\s+(.+)', r'return \1'),
        
        # 7. Déclarations variables
        (r'var\s+(\w+)\s*=\s*(.+)', r'\1 = \2'),
        (r'let\s+(\w+)\s*=\s*(.+)', r'\1 = \2'),
        (r'const\s+(\w+)\s*=\s*(.+)', r'\1 = \2'),
        
        # 8. Structures de données
        (r'list\s*\(\s*\)', r'[]'),
        (r'list\s*\((.*?)\)', r'[\1]'),
        (r'dict\s*\(\s*\)', r'{}'),
        
        # 9. String interpolation
        (r'"([^"]*)#\{([^}]+)\}([^"]*)"', r'f"\1{\2}\3"'),
        (r'`(.*?)`', r"r'\1'"),
        
        # 10. __name__ == "__main__"
        (r'if\s+__name__\s*==\s*"__main__"\s*:', r'if __name__ == "__main__":'),
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
    }
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.rules: List[Tuple[Pattern, str]] = []
        self._setup_rules()
        
    def _setup_rules(self):
        for pattern, replacement, *flags in self.ZENV_SYNTAX:
            if flags:
                self.rules.append((re.compile(pattern, flags[0]), replacement))
            else:
                self.rules.append((re.compile(pattern), replacement))
    
    def transpile(self, zv_code: str) -> str:
        lines = zv_code.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            transpiled_line = line
            
            # Appliquer les règles de syntaxe
            for pattern, replacement in self.rules:
                transpiled_line = pattern.sub(replacement, transpiled_line)
            
            # Remplacer les mots-clés
            for zenv, python in self.ZENV_KEYWORDS.items():
                transpiled_line = re.sub(r'\b' + re.escape(zenv) + r'\b', python, transpiled_line)
            
            # Préserver l'indentation
            if transpiled_line != line:
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
