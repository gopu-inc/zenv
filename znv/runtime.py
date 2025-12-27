"""
Runtime Zenv - Machine virtuelle pour exécution
"""

import sys
import os
import traceback
from pathlib import Path
from typing import List, Dict, Optional

class ZenvVirtualMachine:
    def __init__(self):
        self.version = "1.0.0"
        self.modules = {}
        
    def execute_file(self, filepath: str, args: List[str] = None) -> int:
        """Exécute un fichier .zv ou .py"""
        path = Path(filepath)
        
        if not path.exists():
            print(f"❌ Fichier non trouvé: {filepath}")
            return 1
            
        try:
            # Déterminer le type de fichier
            if path.suffix in ['.zv', '.zenv']:
                return self._execute_zv_file(path, args or [])
            else:
                return self._execute_py_file(path, args or [])
                
        except Exception as e:
            print(f"❌ Erreur d'exécution: {e}")
            if os.environ.get('ZENV_DEBUG'):
                traceback.print_exc()
            return 1
    
    def _execute_zv_file(self, path: Path, args: List[str]) -> int:
        """Exécute un fichier Zenv"""
        # Pour l'instant, exécute directement comme Python
        # Plus tard: transpiler puis exécuter
        
        with open(path, 'r') as f:
            code = f.read()
            
        # Préparer l'environnement
        globals_dict = {
            '__name__': '__main__',
            '__file__': str(path),
            'argv': args
        }
        
        try:
            exec(code, globals_dict)
            return 0
        except Exception as e:
            print(f"❌ Erreur dans {path.name}: {e}")
            return 1
    
    def _execute_py_file(self, path: Path, args: List[str]) -> int:
        """Exécute un fichier Python"""
        # Sauvegarder sys.argv
        old_argv = sys.argv.copy()
        sys.argv = [str(path)] + args
        
        try:
            # Exécuter avec runpy
            import runpy
            runpy.run_path(str(path), run_name="__main__")
            return 0
        except Exception as e:
            print(f"❌ Erreur dans {path.name}: {e}")
            return 1
        finally:
            # Restaurer sys.argv
            sys.argv = old_argv


class ZenvREPL:
    """REPL interactif Zenv"""
    
    def __init__(self):
        self.vm = ZenvVirtualMachine()
        self.history = []
        
    def start(self):
        print("""
╔═══════════════════════════════════════════════╗
║        Zenv REPL v1.0 - Mode Interactif      ║
║    Tapez du code (exit pour quitter)         ║
╚═══════════════════════════════════════════════╝
        """)
        
        line_num = 0
        while True:
            try:
                prompt = f"znv[{line_num}]> "
                line = input(prompt).strip()
                
                if line.lower() in ('exit', 'quit', 'q'):
                    break
                elif line == '':
                    continue
                    
                self.history.append(line)
                
                # Exécuter la ligne
                try:
                    exec(line)
                except Exception as e:
                    print(f"Erreur: {e}")
                    
                line_num += 1
                
            except KeyboardInterrupt:
                print("\n(Interrompu)")
            except EOFError:
                print("\nAu revoir!")
                break
