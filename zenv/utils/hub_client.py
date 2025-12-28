import requests
import json
import os
import time
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
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
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
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    # Sauvegarder le token
                    with open(self.token_file, 'w') as f:
                        json.dump({
                            'token': token,
                            'user': data.get('user', {}),
                            'login_time': time.time()
                        }, f, indent=2)
                    return True
                else:
                    print(f"Token invalide: {data.get('error', 'Unknown error')}")
            else:
                print(f"Erreur serveur: {response.status_code}")
        except Exception as e:
            print(f"Erreur connexion: {e}")
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
    
    def search_packages(self, query: str = "") -> List[Dict]:
        """Rechercher des packages"""
        try:
            response = requests.get(
                f"{self.base_url}/api/packages",
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                packages = data.get('packages', [])
                
                if query:
                    # Filtrer localement
                    query_lower = query.lower()
                    packages = [
                        pkg for pkg in packages 
                        if query_lower in pkg.get('name', '').lower() or 
                        query_lower in pkg.get('description', '').lower()
                    ]
                
                return packages
            else:
                print(f"Erreur: {response.status_code}")
        except Exception as e:
            print(f"Erreur recherche: {e}")
        return []
    
    def upload_package(self, package_file: str, name: str, version: str, description: str = "") -> bool:
        """Uploader un package"""
        if not self.is_logged_in():
            print("❌ Non connecté. Utilisez: zenv hub login <token>")
            return False
        
        try:
            print(f"📤 Publication de {name} v{version}...")
            
            with open(package_file, 'rb') as f:
                files = {'file': (os.path.basename(package_file), f, 'application/gzip')}
                data = {
                    'name': name,
                    'version': version,
                    'description': description or f"Package {name}"
                }
                
                response = requests.post(
                    f"{self.base_url}/api/packages/upload",
                    files=files,
                    data=data,
                    headers={'Authorization': f'Token {self.get_token()}'},
                    timeout=30
                )
                
                if response.status_code == 201:
                    print(f"✅ Package publié: {name} v{version}")
                    return True
                else:
                    print(f"❌ Échec publication: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   Erreur: {error_data.get('error', 'Unknown error')}")
                    except:
                        print(f"   Réponse: {response.text[:100]}")
                    return False
        except Exception as e:
            print(f"❌ Erreur publication: {e}")
            return False
    
    def download_package(self, package_name: str, version: str = "latest") -> Optional[bytes]:
        """Télécharger un package"""
        try:
            print(f"⬇️  Téléchargement {package_name}@{version}...")
            
            # D'abord chercher le package
            packages = self.search_packages(package_name)
            target_package = None
            
            for pkg in packages:
                if pkg['name'] == package_name:
                    target_package = pkg
                    break
            
            if not target_package:
                print(f"❌ Package non trouvé: {package_name}")
                return None
            
            # Télécharger
            download_url = f"{self.base_url}/api/packages/download/{package_name}/{target_package.get('version', version)}"
            response = requests.get(
                download_url,
                headers=self._get_headers(),
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                content = b''
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        content += chunk
                
                print(f"✅ Téléchargé: {len(content)} bytes")
                return content
            else:
                print(f"❌ Échec téléchargement: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Erreur téléchargement: {e}")
            return None
    
    def get_user_info(self) -> Optional[Dict]:
        """Obtenir les infos utilisateur"""
        if not self.is_logged_in():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/profile",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('user')
        except:
            pass
        return None
