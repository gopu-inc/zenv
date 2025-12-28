import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

class ZenvHubClient:
    
    def __init__(self):
        self.base_url = "https://zenv-hub.onrender.com"
        self.config_dir = Path.home() / ".zenv"
        self.config_dir.mkdir(exist_ok=True)
        self.token_file = self.config_dir / "token.json"
        self.config_file = self.config_dir / "config.json"
        
    def check_status(self) -> bool:
        """Vérifier si le hub est en ligne"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def login(self, token: str) -> bool:
        """Se connecter avec un token"""
        try:
            # Vérifier le token
            response = requests.get(
                f"{self.base_url}/api/tokens/verify",
                params={'token': token},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    # Sauvegarder le token
                    with open(self.token_file, 'w') as f:
                        json.dump({
                            'token': token,
                            'user': data.get('user', {})
                        }, f, indent=2)
                    return True
        except:
            pass
        return False
    
    def logout(self):
        """Se déconnecter"""
        if self.token_file.exists():
            self.token_file.unlink()
    
    def is_logged_in(self) -> bool:
        """Vérifier si connecté"""
        return self.token_file.exists()
    
    def get_token(self) -> Optional[str]:
        """Obtenir le token actuel"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    return data.get('token')
            except:
                pass
        return None
    
    def _get_headers(self) -> Dict:
        """Obtenir les headers avec authentification"""
        headers = {'Content-Type': 'application/json'}
        token = self.get_token()
        if token:
            headers['Authorization'] = f'Token {token}'
        return headers
    
    def search_packages(self, query: str) -> List[Dict]:
        """Rechercher des packages"""
        try:
            response = requests.get(
                f"{self.base_url}/api/packages",
                params={'q': query} if query else {},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('packages', [])
        except Exception as e:
            print(f"Search error: {e}")
        return []
    
    def upload_package(self, package_file: str, name: str, version: str, description: str = "") -> bool:
        """Uploader un package"""
        if not self.is_logged_in():
            print("❌ Not logged in. Use: zenv hub login <token>")
            return False
        
        try:
            with open(package_file, 'rb') as f:
                files = {'file': (os.path.basename(package_file), f, 'application/gzip')}
                data = {
                    'name': name,
                    'version': version,
                    'description': description
                }
                
                response = requests.post(
                    f"{self.base_url}/api/packages/upload",
                    files=files,
                    data=data,
                    headers={'Authorization': f'Token {self.get_token()}'}
                )
                
                if response.status_code == 201:
                    print(f"✅ Package published: {name} v{version}")
                    return True
                else:
                    print(f"❌ Upload failed: {response.status_code}")
                    if response.text:
                        print(f"   Error: {response.text[:100]}")
                    return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def download_package(self, package_name: str, version: str = "latest") -> Optional[bytes]:
        """Télécharger un package"""
        try:
            response = requests.get(
                f"{self.base_url}/api/packages/download/{package_name}/{version}",
                headers=self._get_headers(),
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"❌ Download failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Download error: {e}")
        return None
    
    def get_package_info(self, package_name: str) -> Optional[Dict]:
        """Obtenir les infos d'un package"""
        try:
            packages = self.search_packages(package_name)
            for pkg in packages:
                if pkg['name'] == package_name:
                    return pkg
        except:
            pass
        return None
    
    def get_badges(self) -> List[Dict]:
        """Obtenir la liste des badges"""
        try:
            response = requests.get(
                f"{self.base_url}/api/badges",
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('badges', [])
        except:
            pass
        return []
    
    def create_badge(self, name: str, label: str, value: str, color: str = "blue") -> bool:
        """Créer un badge"""
        if not self.is_logged_in():
            print("❌ Not logged in")
            return False
        
        try:
            data = {
                'name': name,
                'label': label,
                'value': value,
                'color': color
            }
            
            response = requests.post(
                f"{self.base_url}/api/badges",
                json=data,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                print(f"✅ Badge created: {name}")
                return True
        except Exception as e:
            print(f"❌ Badge creation error: {e}")
        return False
