import configparser
import json
import tarfile
import hashlib
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional
import datetime

class ZenvManifest:
    
    def __init__(self, manifest_path: str):
        self.path = Path(manifest_path)
        self.config = configparser.ConfigParser()
        self.config.read(manifest_path)
    
    def parse(self) -> Dict:
        result = {}
        for section in self.config.sections():
            result[section] = dict(self.config[section])
        return result
    
    def get_name(self) -> str:
        return self.config.get('Zenv', 'name', fallback='unknown')
    
    def get_version(self) -> str:
        return self.config.get('Zenv', 'version', fallback='0.0.0')
    
    def get_dependencies(self) -> Dict:
        deps = {'zv': {}, 'py': {}}
        if self.config.has_section('dep.zv'):
            deps['zv'] = dict(self.config['dep.zv'])
        if self.config.has_section('dep.py'):
            deps['py'] = dict(self.config['dep.py'])
        return deps
    
    def get_files(self) -> List[str]:
        files = []
        if self.config.has_section('File-build'):
            for key in self.config['File-build']:
                value = self.config['File-build'][key]
                if '\n' in value:
                    files.extend([f.strip() for f in value.split('\n') if f.strip()])
                else:
                    files.append(value.strip())
        return files

class ZenvBuilder:
    
    def __init__(self):
        self.version = "1.0.0"
    
    def build(self, manifest_file: str = "package.zcf", output_dir: str = "dist") -> str:
        print(f"🔨 Building package from: {manifest_file}")
        
        try:
            manifest = ZenvManifest(manifest_file)
            package_name = manifest.get_name()
            package_version = manifest.get_version()
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create package file name - CORRIGÉ: .zv au lieu de .zc.gs
            package_file = output_path / f"{package_name}-{package_version}.zv"
            
            # Create temp directory
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                
                # Copy files from manifest
                files = manifest.get_files()
                print(f"📄 Files to include: {files}")
                
                for file_pattern in files:
                    if '*' in file_pattern:
                        # Glob pattern
                        for file_path in Path('.').glob(file_pattern.strip()):
                            if file_path.is_file():
                                dest_file = tmp_path / file_path.name
                                shutil.copy2(file_path, dest_file)
                                print(f"  ✓ Copied: {file_path}")
                    else:
                        # Single file
                        file_path = Path(file_pattern.strip())
                        if file_path.exists():
                            dest_file = tmp_path / file_path.name
                            shutil.copy2(file_path, dest_file)
                            print(f"  ✓ Copied: {file_path}")
                
                # Create metadata
                metadata = {
                    'name': package_name,
                    'version': package_version,
                    'dependencies': manifest.get_dependencies(),
                    'build_date': str(datetime.datetime.now()),
                    'builder_version': self.version,
                    'files': [f.name for f in tmp_path.iterdir() if f.is_file()]
                }
                
                with open(tmp_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
                
                # Create archive - CORRIGÉ: .gz simple au lieu de .zc.gs
                self._create_archive(tmp_path, package_file)
                
                # Calculate hash
                file_hash = self._calculate_hash(package_file)
                hash_file = package_file.with_suffix('.sha256')
                with open(hash_file, "w") as f:
                    f.write(f"{file_hash}  {package_file.name}")
            
            print(f"✅ Package built: {package_file}")
            print(f"📦 Size: {package_file.stat().st_size / 1024:.1f} KB")
            print(f"🔒 SHA256: {file_hash}")
            
            return str(package_file)
            
        except Exception as e:
            print(f"❌ Build error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _create_archive(self, source_dir: Path, output_path: Path):
        """Create .tar.gz archive"""
        with tarfile.open(output_path, "w:gz") as tar:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    tar.add(file_path, arcname=str(arcname))
    
    def _calculate_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
