import shutil
import json
import tarfile
import requests
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import sys

class PackageManager:
    
    def __init__(self):
        self.site_dir = Path("/usr/bin/zenv-site/c82")
        self.site_dir.mkdir(parents=True, exist_ok=True)
        self.hub_url = "https://zenv-hub.onrender.com"
    
    def install(self, package_name: str, version: str = "latest") -> bool:
        print(f"📦 Installing {package_name}@{version}...")
        
        try:
            # Download from hub
            package_file = self._download_package(package_name, version)
            if not package_file:
                return False
            
            # Extract to site directory
            package_dir = self.site_dir / package_name
            package_dir.mkdir(exist_ok=True)
            
            with tarfile.open(package_file, "r:gz") as tar:
                tar.extractall(package_dir)
            
            # Install Python dependencies
            self._install_python_deps(package_dir)
            
            print(f"✅ Installed: {package_name}@{version}")
            return True
            
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False
    
    def _download_package(self, package_name: str, version: str) -> Optional[Path]:
        try:
            url = f"{self.hub_url}/api/packages/download/{package_name}/{version}"
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                temp_file = Path(f"/tmp/{package_name}.zc.gs")
                with open(temp_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return temp_file
        except Exception as e:
            print(f"❌ Download error: {e}")
        
        return None
    
    def _install_python_deps(self, package_dir: Path):
        # Check for requirements.txt
        req_file = package_dir / "requirements.txt"
        if req_file.exists():
            print("📦 Installing Python dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        
        # Check for dependencies in metadata
        meta_file = package_dir / "metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                metadata = json.load(f)
                deps = metadata.get('dependencies', {}).get('py', {})
                if deps:
                    for dep, ver in deps.items():
                        if ver == "latest":
                            subprocess.run([sys.executable, "-m", "pip", "install", dep])
                        else:
                            subprocess.run([sys.executable, "-m", "pip", "install", f"{dep}=={ver}"])
    
    def list_packages(self) -> List[Dict]:
        packages = []
        for package_dir in self.site_dir.iterdir():
            if package_dir.is_dir():
                meta_file = package_dir / "metadata.json"
                if meta_file.exists():
                    with open(meta_file) as f:
                        metadata = json.load(f)
                        packages.append(metadata)
        return packages
    
    def remove(self, package_name: str) -> bool:
        package_dir = self.site_dir / package_name
        if package_dir.exists():
            shutil.rmtree(package_dir)
            print(f"✅ Removed: {package_name}")
            return True
        else:
            print(f"❌ Package not found: {package_name}")
            return False
    
    def search_hub(self, query: str) -> List[Dict]:
        try:
            url = f"{self.hub_url}/api/packages/search"
            response = requests.get(url, params={'q': query})
            
            if response.status_code == 200:
                return response.json().get('packages', [])
        except:
            pass
        
        return []
    
    def publish(self, package_file: str) -> bool:
        print(f"📤 Publishing {package_file}...")
        
        try:
            with open(package_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.hub_url}/api/packages/upload",
                    files=files
                )
                
                if response.status_code in [200, 201]:
                    print("✅ Published successfully!")
                    return True
                else:
                    print(f"❌ Publish failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Publish error: {e}")
            return False
