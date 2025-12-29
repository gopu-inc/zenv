import requests
import json
import os
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

class ZenvHubClient:
    
    def __init__(self):
        self.base_url = "https://zenv-hub.onrender.com"
        self.config_dir = Path.home() / ".zenv"
        self.config_dir.mkdir(exist_ok=True)
        self.token_file = self.config_dir / "token.json"
        self.config_file = self.config_dir / "config.json"
        
    def check_status(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def login(self, token: str) -> bool:
        try:
            # Vérifier directement le format du token
            if token.startswith('zenv_'):
                # Sauvegarder le token
                with open(self.token_file, 'w') as f:
                    json.dump({
                        'token': token,
                        'user': {'id': '1', 'username': 'user', 'role': 'user'},
                        'login_time': time.time()
                    }, f, indent=2)
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def logout(self):
        if self.token_file.exists():
            self.token_file.unlink()
    
    def is_logged_in(self) -> bool:
        return self.token_file.exists()
    
    def get_token(self) -> Optional[str]:
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    return data.get('token')
            except:
                pass
        return None
    
    def _get_headers(self) -> Dict:
        headers = {'Content-Type': 'application/json'}
        token = self.get_token()
        if token:
            headers['Authorization'] = f'Token {token}'
        return headers
    
    def search_packages(self, query: str = "") -> List[Dict]:
        try:
            response = requests.get(
                f"{self.base_url}/api/packages",
                headers=self._get_headers(),
                timeout=200
            )
            
            if response.status_code == 200:
                data = response.json()
                packages = data.get('packages', [])
                
                if query:
                    query_lower = query.lower()
                    packages = [
                        pkg for pkg in packages 
                        if query_lower in pkg.get('name', '').lower() or 
                        query_lower in pkg.get('description', '').lower()
                    ]
                
                return packages
        except Exception as e:
            print(f"Search error: {e}")
        return []
    
    def upload_package(self, package_file: str) -> bool:
        if not self.is_logged_in():
            print("❌ Not logged in. Use: zenv hub login <token>")
            return False
        
        try:
            # Extraire le nom et la version du fichier
            filename = os.path.basename(package_file)
            if filename.endswith('.zv'):
                # Format: nom-version.zv
                name_version = filename[:-3]  # Enlever .zv
                if '-' in name_version:
                    parts = name_version.rsplit('-', 1)
                    name = parts[0]
                    version = parts[1] if len(parts) > 1 else '1.0.0'
                else:
                    name = name_version
                    version = '1.0.0'
            else:
                name = 'unknown'
                version = '1.0.0'
            
            print(f"📤 Uploading {name} v{version}...")
            
            with open(package_file, 'rb') as f:
                files = {'file': (filename, f, 'application/gzip')}
                data = {
                    'name': name,
                    'version': version,
                    'description': f'Package {name} v{version}'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/packages/upload",
                    files=files,
                    data=data,
                    headers={'Authorization': f'Token {self.get_token()}'},
                    timeout=30
                )
                
                if response.status_code == 201:
                    print(f"✅ Package published: {name} v{version}")
                    return True
                else:
                    print(f"❌ Upload failed: {response.status_code}")
                    if response.text:
                        try:
                            error_data = response.json()
                            print(f"   Error: {error_data.get('error', 'Unknown error')}")
                        except:
                            print(f"   Response: {response.text[:100]}")
                    return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def download_package(self, package_name: str, version: str = "latest") -> Optional[bytes]:
        try:
            print(f"⬇️  Downloading {package_name}...")
            
            # Chercher le package
            packages = self.search_packages(package_name)
            target_package = None
            
            for pkg in packages:
                if pkg['name'] == package_name:
                    if version == "latest":
                        target_package = pkg
                        break
                    elif pkg.get('version') == version:
                        target_package = pkg
                        break
            
            if not target_package:
                print(f"❌ Package not found: {package_name}")
                # Afficher les packages disponibles
                if packages:
                    print("📦 Available packages:")
                    for pkg in packages[:5]:  # Afficher les 5 premiers
                        print(f"  • {pkg['name']} v{pkg.get('version', '?')}")
                return None
            
            # Construire l'URL de téléchargement
            download_version = target_package.get('version', version)
            download_url = f"{self.base_url}/api/packages/download/{package_name}/{download_version}"
            
            print(f"🔗 Download URL: {download_url}")
            
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
                
                print(f"✅ Downloaded: {len(content)} bytes")
                return content
            else:
                print(f"❌ Download failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:100]}")
                return None
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def install_package(self, package_name: str, version: str = "latest") -> bool:
        """
        Install a package from Zenv Hub
        """
        try:
            # Télécharger le package
            package_data = self.download_package(package_name, version)
            if not package_data:
                return False
            
            # Extraire le package dans un répertoire temporaire
            import tarfile
            import gzip
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Écrire les données compressées
                compressed_file = os.path.join(tmpdir, f"{package_name}.tar.gz")
                with open(compressed_file, 'wb') as f:
                    f.write(package_data)
                
                # Extraire
                with gzip.open(compressed_file, 'rb') as f_gz:
                    with tarfile.open(fileobj=f_gz, mode='r') as tar:
                        tar.extractall(tmpdir)
                
                # Chercher le dossier extrait
                extracted_dir = None
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path) and item.startswith(package_name):
                        extracted_dir = item_path
                        break
                
                if not extracted_dir:
                    print(f"❌ Could not find extracted package directory")
                    return False
                
                # Vérifier s'il y a un setup.py ou pyproject.toml
                setup_py = os.path.join(extracted_dir, 'setup.py')
                pyproject_toml = os.path.join(extracted_dir, 'pyproject.toml')
                
                has_entry_points = False
                
                # Vérifier setup.py
                if os.path.exists(setup_py):
                    with open(setup_py, 'r') as f:
                        setup_content = f.read()
                        if 'entry_points' in setup_content or 'console_scripts' in setup_content:
                            has_entry_points = True
                
                # Vérifier pyproject.toml
                if os.path.exists(pyproject_toml):
                    with open(pyproject_toml, 'r') as f:
                        pyproject_content = f.read()
                        if 'entry_points' in pyproject_content or 'console_scripts' in pyproject_content or '[project.scripts]' in pyproject_content:
                            has_entry_points = True
                
                # Afficher le message de build
                print(f"build for Pack: {package_name}")
                
                # Installer avec pip install -e si entry points détectés
                if has_entry_points:
                    print(f"⚠️  Package {package_name} has entry points, installing with zenv --build --a {package_name} --netwell --toolstack --ej \ as bin/--get")
                    
                    # Créer le répertoire d'installation
                    install_dir = f"/usr/bin/zenv-site/c82/{package_name}"
                    os.makedirs(os.path.dirname(install_dir), exist_ok=True)
                    
                    # Copier les fichiers du package
                    import shutil
                    if os.path.exists(install_dir):
                        shutil.rmtree(install_dir)
                    shutil.copytree(extracted_dir, install_dir)
                    
                    # Installer avec pip install -e
                    print(f"Executing: pip install -e {install_dir}")
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-e", install_dir],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ Package {package_name} installed successfully with entry points")
                        print(result.stdout)
                    else:
                        print(f"❌ Failed to install package {package_name}")
                        print(result.stderr)
                        return False
                else:
                    # Installation normale
                    print(f"📦 Package {package_name} has no entry points, installing normally")
                    
                    # Créer le répertoire d'installation
                    install_dir = f"/usr/bin/zenv-site/c82/{package_name}"
                    os.makedirs(os.path.dirname(install_dir), exist_ok=True)
                    
                    # Copier les fichiers du package
                    import shutil
                    if os.path.exists(install_dir):
                        shutil.rmtree(install_dir)
                    shutil.copytree(extracted_dir, install_dir)
                    
                    # Installer avec pip install
                    print(f"Executing: pip install {install_dir}")
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", install_dir],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print(f"✅ Package {package_name} installed successfully")
                        print(result.stdout)
                    else:
                        print(f"❌ Failed to install package {package_name}")
                        print(result.stderr)
                        return False
                
                return True
                    
        except Exception as e:
            print(f"❌ Installation error: {e}")
            import traceback
            traceback.print_exc()
            return False
