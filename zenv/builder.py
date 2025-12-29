
import os
import json
import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List

class ZenvBuilder:
    
    def build(self, manifest_path: str, output_dir: str = "dist") -> bool:
        """Construire un package Zenv"""
        try:
            if not os.path.exists(manifest_path):
                print(f"❌ Manifest file not found: {manifest_path}")
                return False
            
            # Lire le manifest
            manifest = self._parse_manifest(manifest_path)
            
            # Créer le répertoire de sortie
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Nom du package
            package_name = manifest.get('Zenv', {}).get('name', 'unknown')
            package_version = manifest.get('Zenv', {}).get('version', '1.0.0')
            
            # Créer un répertoire temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copier les fichiers selon le manifest
                files_section = manifest.get('File-build', {})
                files_patterns = files_section.get('files', '').split()
                
                # Collecter les fichiers
                collected_files = []
                for pattern in files_patterns:
                    for file in Path('.').glob(pattern):
                        if file.is_file():
                            # Créer la structure dans le temp dir
                            dest = temp_path / file.name
                            shutil.copy2(file, dest)
                            collected_files.append(file.name)
                
                # Ajouter des fichiers supplémentaires
                docs_file = manifest.get('docs', {}).get('description')
                if docs_file and os.path.exists(docs_file):
                    shutil.copy2(docs_file, temp_path / 'README.md')
                    collected_files.append('README.md')
                
                license_file = manifest.get('license', {}).get('file')
                if license_file and os.path.exists(license_file):
                    shutil.copy2(license_file, temp_path / 'LICENSE')
                    collected_files.append('LICENSE')
                
                # Créer metadata.json
                metadata = {
                    'name': package_name,
                    'version': package_version,
                    'author': manifest.get('Zenv', {}).get('author', ''),
                    'description': manifest.get('Zenv', {}).get('description', ''),
                    'files': collected_files,
                    'build_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with open(temp_path / 'metadata.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Créer l'archive .zv
                archive_name = f"{package_name}-{package_version}.zv"
                archive_path = output_path / archive_name
                
                with tarfile.open(archive_path, 'w:gz') as tar:
                    tar.add(temp_path, arcname='')
                
                print(f"✅ Package built: {archive_path}")
                print(f"📦 Files included: {len(collected_files)}")
                
                return True
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def _parse_manifest(self, manifest_path: str) -> Dict:
        """Parser le fichier manifest .zcf"""
        manifest = {}
        current_section = None
        
        with open(manifest_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    manifest[current_section] = {}
                elif '=' in line and current_section:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    manifest[current_section][key] = value
        
        return manifest
