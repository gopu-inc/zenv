import os
import sys
import subprocess
import tempfile
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import venv

from .transpiler import ZenvTranspiler

class ZenvRuntime:
    
    def __init__(self, hub_url: str = "https://zenv-hub.onrender.com"):
        self.hub_url = hub_url
        self.version = "1.0.0"
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
    
    def execute_string(self, zv_code: str, args: list = None):
        python_code = self.transpiler.transpile(zv_code)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(python_code)
            tmp_path = tmp.name
        
        try:
            result = subprocess.run([sys.executable, tmp_path] + (args or []))
            return result.returncode
        finally:
            os.unlink(tmp_path)
    
    def create_virtualenv(self, name: str, python_version: str = None) -> int:
        env_path = Path(name)
        
        if env_path.exists():
            print(f"Error: Environment already exists: {name}")
            return 1
        
        print(f"Creating environment '{name}'...")
        
        try:
            builder = venv.EnvBuilder(
                system_site_packages=False,
                clear=True,
                symlinks=True,
                with_pip=True
            )
            builder.create(env_path)
            
            (env_path / "zenv-modules").mkdir(exist_ok=True)
            
            config = {
                "name": name,
                "python_version": python_version or f"{sys.version_info.major}.{sys.version_info.minor}",
                "zenv_version": self.version,
                "created_at": str(__import__('datetime').datetime.now())
            }
            
            with open(env_path / "zenv-config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"Environment created: {env_path}")
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            if env_path.exists():
                shutil.rmtree(env_path)
            return 1
