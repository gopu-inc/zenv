import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ZenvTranspiler:
    
    SYNTAX_RULES = {
        r'print\s+(.+)': r'print(\1)',
        r'if\s+(.+?)\s*:\s*$': r'if \1:',
        r'for\s+(\w+)\s+in\s+(.+?)\s*:\s*$': r'for \1 in \2:',
        r'def\s+(\w+)\((.+?)\)\s*:\s*$': r'def \1(\2):',
        r'return\s+(.+)': r'return \1',
        r'"(.*?)#{(.+?)}(.*?)"': r'f"\1{\2}\3"',
    }
    
    def __init__(self):
        self.rules = []
        for pattern, replacement in self.SYNTAX_RULES.items():
            self.rules.append((re.compile(pattern), replacement))
    
    def transpile(self, zv_code: str) -> str:
        lines = zv_code.split('\n')
        result = []
        
        for line in lines:
            transpiled = line
            
            for pattern, replacement in self.rules:
                transpiled = pattern.sub(replacement, transpiled)
            
            result.append(transpiled)
        
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
            return False, f"Erreur de validation: {e}"
