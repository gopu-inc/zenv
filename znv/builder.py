# znv/builder.py
"""
Builder/transpileur pour packages Zenv et Python
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

class ZenvBuilder:
    """Builder pour les packages Zenv"""
    
    def build(self, source_dir: str, output: Optional[str] = None, build_system: str = "zenv") -> int:
        """Builder un package"""
        source_path = Path(source_dir)
        
        if not source_path.exists():
            print(f"❌ Dossier source non trouvé: {source_dir}")
            return 1
        
        # Déterminer le type de build
        if build_system == "zenv":
            return self._build_zenv(source_path, output)
        else:
            return self._build_python(source_path, output)
    
    def _build_zenv(self, source_dir: Path, output: Optional[str]) -> int:
        """Builder un package Zenv natif"""
        print(f"🔨 Building package Zenv: {source_dir.name}")
        
        # Chercher les fichiers .zv
        zv_files = list(source_dir.rglob("*.zv"))
        if not zv_files:
            print("❌ Aucun fichier .zv trouvé")
            return 1
        
        # Transpiler
        from .transpiler import transpile_file
        for zv_file in zv_files:
            py_file = zv_file.with_suffix('.py')
            try:
                transpile_file(str(zv_file), str(py_file))
                print(f"  ✓ Transpilé: {zv_file.name}")
            except Exception as e:
                print(f"  ✗ Erreur: {zv_file.name} - {e}")
        
        # Créer l'archive de sortie
        if output:
            output_path = Path(output)
            self._create_archive(source_dir, output_path)
            print(f"✅ Package créé: {output}")
        
        return 0
    
    def _build_python(self, source_dir: Path, output: Optional[str]) -> int:
        """Builder un package Python standard"""
        print(f"🐍 Building package Python: {source_dir.name}")
        
        # Chercher setup.py ou pyproject.toml
        setup_py = source_dir / "setup.py"
        pyproject = source_dir / "pyproject.toml"
        
        if setup_py.exists():
            # Build avec setuptools
            cmd = [sys.executable, "setup.py", "sdist", "bdist_wheel"]
            result = subprocess.run(cmd, cwd=source_dir, capture_output=True)
            
            if result.returncode == 0:
                print("✅ Build réussi avec setuptools")
                # Copier les artefacts
                if output:
                    dist_dir = source_dir / "dist"
                    if dist_dir.exists():
                        for artefact in dist_dir.iterdir():
                            shutil.copy2(artefact, output)
            else:
                print(f"❌ Erreur build: {result.stderr.decode()}")
                return 1
                
        elif pyproject.exists():
            # Build avec build
            cmd = [sys.executable, "-m", "build"]
            result = subprocess.run(cmd, cwd=source_dir, capture_output=True)
            
            if result.returncode == 0:
                print("✅ Build réussi avec pyproject.toml")
            else:
                print(f"❌ Erreur build: {result.stderr.decode()}")
                return 1
        else:
            print("❌ Aucun système de build trouvé (setup.py ou pyproject.toml)")
            return 1
        
        return 0
    
    def _create_archive(self, source_dir: Path, output_path: Path):
        """Crée une archive du package"""
        import tarfile
        
        # Créer une archive .zenv
        with tarfile.open(output_path.with_suffix('.zenv'), "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)
