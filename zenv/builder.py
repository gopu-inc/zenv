import configparser
import json
import tarfile
import hashlib
import shutil
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
            for key, value in result[section].items():
                if '\n' in value:
                    items = [item.strip() for item in value.split('\n') if item.strip()]
                    result[section][key] = items
        return result
    
    def get_name(self) -> str:
        return self.config.get('Zenv', 'name', fallback='unknown')
    
    def get_version(self) -> str:
        return self.config.get('Zenv', 'version', fallback='0.0.0')
    
    def get_dependencies(self) -> Dict:
        deps = {'zv': {}, 'py': {}}
        if 'Dep.zv' in self.config:
            deps['zv'] = dict(self.config['Dep.zv'])
        if 'Dep.py' in self.config:
            deps['py'] = dict(self.config['Dep.py'])
        return deps

class ZenvBuilder:
    
    def __init__(self):
        self.version = "1.0.0"
    
    def build_from_manifest(self, manifest_file: str, output_file: Optional[str] = None, clean: bool = False) -> int:
        print(f"Building package from: {manifest_file}")
        
        try:
            manifest = ZenvManifest(manifest_file)
            package_name = manifest.get_name()
            package_version = manifest.get_version()
            
            if not output_file:
                output_file = f"dist/{package_name}-{package_version}.zcf.gz"
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if clean and output_path.exists():
                output_path.unlink()
            
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                self._copy_files(manifest.parse(), tmp_path)
                shutil.copy2(manifest_file, tmp_path / "package.zcf")
                
                metadata = {
                    'name': package_name,
                    'version': package_version,
                    'dependencies': manifest.get_dependencies(),
                    'build_date': str(datetime.datetime.now()),
                    'builder_version': self.version
                }
                
                with open(tmp_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
                
                self._create_archive(tmp_path, output_path)
                file_hash = self._calculate_hash(output_path)
                
                hash_file = output_path.parent / f"{output_path.name}.sha256"
                with open(hash_file, "w") as f:
                    f.write(f"{file_hash}  {output_path.name}")
            
            print(f"Package built: {output_path}")
            return 0
            
        except Exception as e:
            print(f"Build error: {e}")
            return 1
    
    def _copy_files(self, manifest_data: Dict, dest_path: Path):
        if 'File-build' not in manifest_data:
            return
        
        file_section = manifest_data['File-build']
        main_file = file_section.get('main')
        if main_file and Path(main_file).exists():
            shutil.copy2(main_file, dest_path / Path(main_file).name)
        
        include_patterns = file_section.get('include', [])
        if isinstance(include_patterns, str):
            include_patterns = [include_patterns]
        
        for pattern in include_patterns:
            if '*' in pattern:
                for file_path in Path('.').glob(pattern):
                    dest_file = dest_path / file_path.relative_to('.')
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_file)
            else:
                if Path(pattern).exists():
                    shutil.copy2(pattern, dest_path / pattern)
    
    def _create_archive(self, source_dir: Path, output_path: Path):
        with tarfile.open(output_path, "w:gz") as tar:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    tar.add(file_path, arcname=str(file_path.relative_to(source_dir)))
    
    def _calculate_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def install_package(self, package_file: str) -> int:
        print(f"Installing {package_file}")
        
        try:
            packages_dir = Path.home() / ".zenv" / "packages"
            packages_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(package_file, "r:gz") as tar:
                tar.extractall(packages_dir)
            
            print(f"Package installed")
            return 0
            
        except Exception as e:
            print(f"Install error: {e}")
            return 1
