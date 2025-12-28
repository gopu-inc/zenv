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
        # Import statements
        r'^import\s+([\w\.]+)\s+as\s+(\w+)$': r'import \1 as \2',
        r'^from\s+([\w\.]+)\s+import\s+([\w\s,]+)$': r'from \1 import \2',
        r'^from\s+([\w\.]+)\s+import\s+all$': r'from \1 import *',
        
        # Control structures
        r'^if\s+(.+?)\s+then\s*$': r'if \1:',
        r'^elif\s+(.+?)\s+then\s*$': r'elif \1:',
        r'^else\s*$': r'else:',
        r'^for\s+(\w+)\s+in\s+(.+?)\s+do\s*$': r'for \1 in \2:',
        r'^while\s+(.+?)\s+do\s*$': r'while \1:',
        r'^repeat\s+(\d+)\s+times\s*:\s*$': r'for _ in range(\1):',
        
        # Function definitions
        r'^function\s+(\w+)\((.+?)\)\s*:\s*$': r'def \1(\2):',
        r'^function\s+(\w+)\(\)\s*:\s*$': r'def \1():',
        r'^func\s+(\w+)\((.+?)\)\s*:\s*$': r'def \1(\2):',
        r'^return\s+(.+)$': r'return \1',
        
        # Classes
        r'^class\s+(\w+)\s*:\s*$': r'class \1:',
        r'^class\s+(\w+)\s+extends\s+(\w+)\s*:\s*$': r'class \1(\2):',
        
        # Print and input
        r'^print\s+(.+)$': r'print(\1)',
        r'^input\(\)$': r'input()',
        r'^input\s+(.+)$': r'input(\1)',
        
        # Variable declarations
        r'^var\s+(\w+)\s+=\s+(.+)$': r'\1 = \2',
        r'^const\s+(\w+)\s+=\s+(.+)$': r'\1 = \2',
        r'^let\s+(\w+)\s+=\s+(.+)$': r'\1 = \2',
        
        # Data types
        r'^list\s*\(\s*\)$': r'[]',
        r'^list\s*\(\s*(.+?)\s*\)$': r'[\1]',
        r'^dict\s*\(\s*\)$': r'{}',
        r'^set\s*\(\s*\)$': r'set()',
        
        # String interpolation
        r'`([^`]*)`': r"r'\1'",
        r'string\s*`([^`]*)`': r"'\1'",
        r'"([^"]*)#\{([^}]+)\}([^"]*)"': r'f"\1{\2}\3"',
        
        # Special operators
        r'(\w+)\s+is\s+(\w+)': r'\1 is \2',
        r'(\w+)\s+is\s+not\s+(\w+)': r'\1 is not \2',
        r'(\w+)\s+and\s+(\w+)': r'\1 and \2',
        r'(\w+)\s+or\s+(\w+)': r'\1 or \2',
        
        # Special methods
        r'^main\s*\(\s*\)\s*:\s*$': r'def main():',
        
        # Error handling
        r'^try\s*:\s*$': r'try:',
        r'^catch\s+(\w+)\s*:\s*$': r'except \1:',
        r'^finally\s*:\s*$': r'finally:',
        r'^raise\s+(.+)$': r'raise \1',
        
        # Comments
        r'^//\s*(.+)$': r'# \1',
        r'^/\*\s*(.+?)\s*\*/$': r'"""\1"""',
        
        # Async/await
        r'^async\s+function\s+(\w+)\((.+?)\)\s*:\s*$': r'async def \1(\2):',
        r'^async\s+func\s+(\w+)\((.+?)\)\s*:\s*$': r'async def \1(\2):',
        r'^await\s+(.+)$': r'await \1',
        
        # Match statement
        r'^match\s+(.+?)\s*:\s*$': r'match \1:',
        r'^case\s+(.+?)\s+=>\s+(.+)$': r'case \1: \2',
        
        # Lambdas
        r'lambda\s+(\w+)\s*=>\s*(.+)$': r'lambda \1: \2',
        
        # Comprehensions
        r'\[for\s+(\w+)\s+in\s+(.+?)\s+if\s+(.+?)\]': r'[\1 for \1 in \2 if \3]',
    }
    
    ZENV_KEYWORDS = {
        'import': 'import',
        'from': 'from',
        'as': 'as',
        'if': 'if',
        'then': 'then',
        'elif': 'elif',
        'else': 'else',
        'for': 'for',
        'in': 'in',
        'do': 'do',
        'while': 'while',
        'function': 'function',
        'func': 'func',
        'return': 'return',
        'class': 'class',
        'extends': 'extends',
        'print': 'print',
        'input': 'input',
        'var': 'var',
        'const': 'const',
        'let': 'let',
        'true': 'True',
        'false': 'False',
        'null': 'None',
        'none': 'None',
        'and': 'and',
        'or': 'or',
        'not': 'not',
        'is': 'is',
        'main': 'main',
        'try': 'try',
        'catch': 'catch',
        'finally': 'finally',
        'raise': 'raise',
        'string': 'string',
        'list': 'list',
        'dict': 'dict',
        'set': 'set',
        'async': 'async',
        'await': 'await',
        'match': 'match',
        'case': 'case',
        'lambda': 'lambda',
        'repeat': 'repeat',
        'times': 'times',
    }
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.rules: List[Tuple[Pattern, str]] = []
        self._setup_rules()
        self.token_patterns = self._setup_token_patterns()
        self.in_multiline_comment = False
        
    def _setup_rules(self):
        for pattern, replacement in self.ZENV_SYNTAX.items():
            self.rules.append((re.compile(pattern), replacement))
    
    def _setup_token_patterns(self):
        return [
            (TokenType.COMMENT, r'//.*|/\*.*?\*/'),
            (TokenType.STRING, r'`[^`]*`|"[^"#]*"|\'[^\']*\''),
            (TokenType.NUMBER, r'\b\d+(\.\d+)?\b'),
            (TokenType.KEYWORD, r'\b(' + '|'.join(self.ZENV_KEYWORDS.keys()) + r')\b'),
            (TokenType.IDENTIFIER, r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
            (TokenType.OPERATOR, r'[+\-*/%=!<>]=?|&&|\|\||!|=>'),
            (TokenType.PUNCTUATION, r'[(),:;{}[\].]'),
            (TokenType.WHITESPACE, r'\s+'),
        ]
    
    def tokenize(self, code: str) -> List[Token]:
        tokens = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            pos = 0
            while pos < len(line):
                match = None
                for token_type, pattern in self.token_patterns:
                    regex = re.compile(pattern)
                    match = regex.match(line, pos)
                    if match:
                        value = match.group(0)
                        if token_type != TokenType.WHITESPACE:
                            tokens.append(Token(token_type, value, line_num, pos + 1))
                        pos = match.end()
                        break
                if not match:
                    if self.strict_mode:
                        raise SyntaxError(f"Invalid character at line {line_num}, position {pos + 1}")
                    pos += 1
        
        return tokens
    
    def transpile(self, zv_code: str) -> str:
        self.in_multiline_comment = False
        lines = zv_code.split('\n')
        result = []
        
        for line in lines:
            transpiled_line = self._transpile_line(line)
            result.append(transpiled_line)
        
        return '\n'.join(result)
    
    def _transpile_line(self, line: str) -> str:
        original_line = line
        line = line.rstrip()
        
        if self.in_multiline_comment:
            if '*/' in line:
                self.in_multiline_comment = False
                return line.replace('*/', '"""', 1)
            return '# ' + line
        
        if '/*' in line and '*/' in line:
            return line.replace('/*', '"""').replace('*/', '"""')
        elif '/*' in line:
            self.in_multiline_comment = True
            return line.replace('/*', '"""', 1)
        
        for pattern, replacement in self.rules:
            line = pattern.sub(replacement, line)
        
        for zenv, python in self.ZENV_KEYWORDS.items():
            line = re.sub(r'\b' + zenv + r'\b', python, line)
        
        indent = len(original_line) - len(original_line.lstrip())
        return ' ' * indent + line
    
    def transpile_file(self, input_file: str, output_file: Optional[str] = None) -> str:
        with open(input_file, 'r', encoding='utf-8') as f:
            zv_code = f.read()
        
        python_code = self.transpile(zv_code)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(python_code)
        
        return python_code
    
    def transpile_to_file(self, source: str, output_file: str) -> str:
        python_code = self.transpile(source)
        
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
    
    def format_code(self, zv_code: str) -> str:
        python_code = self.transpile(zv_code)
        return python_code
    
    def execute_string(self, zv_code: str, args: list = None):
        python_code = self.transpile(zv_code)
        exec_globals = {}
        exec(python_code, exec_globals)
        return exec_globals
