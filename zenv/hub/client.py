import requests
import json
from pathlib import Path
from typing import Dict, List, Optional

class ZenvHubClient:
    
    def __init__(self, base_url: str = "https://zenv-hub.onrender.com"):
        self.base_url = base_url
        self.token_file = Path.home() / ".zenv" / "token"
    
    def check_status(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def login(self, token: str) -> bool:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(token.strip())
        return True
    
    def logout(self):
        if self.token_file.exists():
            self.token_file.unlink()
    
    def _get_headers(self) -> Dict:
        headers = {}
        if self.token_file.exists():
            token = self.token_file.read_text().strip()
            headers['Authorization'] = f"Token {token}"
        return headers
    
    def search(self, query: str) -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/packages/search",
                params={'q': query},
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json().get('packages', [])
        except:
            pass
        return []
    
    def install_package(self, package_name: str, version: str = "latest") -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/packages/download/{package_name}/{version}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                packages_dir = Path.home() / ".zenv" / "packages" / package_name
                packages_dir.mkdir(parents=True, exist_ok=True)
                
                package_file = packages_dir / f"{package_name}.zcf.gz"
                with open(package_file, 'wb') as f:
                    f.write(response.content)
                
                import tarfile
                with tarfile.open(package_file, "r:gz") as tar:
                    tar.extractall(packages_dir)
                
                package_file.unlink()
                return True
        except:
            pass
        return False
    
    def publish_package(self, package_file: str) -> bool:
        try:
            with open(package_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/api/packages/upload",
                    files=files,
                    headers=self._get_headers()
                )
                return response.status_code in [200, 201]
        except:
            return False
