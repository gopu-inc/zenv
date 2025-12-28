import json
from pathlib import Path
from typing import Dict, Any

class Config:
    
    def __init__(self, config_file: str = None):
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path.home() / ".zenv" / "config.json"
        
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()
    
    def delete(self, key: str):
        if key in self.data:
            del self.data[key]
            self.save()
