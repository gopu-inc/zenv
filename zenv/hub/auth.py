import json
from pathlib import Path
from typing import Optional

class ZenvAuth:
    
    def __init__(self):
        self.config_file = Path.home() / ".zenv" / "config.json"
    
    def get_token(self) -> Optional[str]:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('token')
            except:
                pass
        return None
    
    def save_token(self, token: str):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        config = {'token': token}
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def clear_token(self):
        if self.config_file.exists():
            self.config_file.unlink()
