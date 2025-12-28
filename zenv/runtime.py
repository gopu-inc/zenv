import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import List

from .transpiler import ZenvTranspiler

class ZenvRuntime:
    
    def __init__(self):
        self.transpiler = ZenvTranspiler()
    
    def execute(self, file_path: str, args: List[str] = None) -> int:
        path = Path(file_path)
        
        if not path.exists():
            print(f"Error: File not found: {file_path}")
            return 1
        
        if path.suffix in ['.zv', '.zenv']:
            return self._execute_zv(path, args or [])
        else:
            return self._execute_python(path, args or [])
    
    def _execute_zv(self, path: Path, args: List[str]) -> int:
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                python_code = self.transpiler.transpile_file(str(path))
                tmp.write(python_code)
                tmp_path = tmp.name
            
            result = subprocess.run([sys.executable, tmp_path] + args)
            os.unlink(tmp_path)
            return result.returncode
            
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _execute_python(self, path: Path, args: List[str]) -> int:
        try:
            result = subprocess.run([sys.executable, str(path)] + args)
            return result.returncode
        except Exception as e:
            print(f"Error: {e}")
            return 1
