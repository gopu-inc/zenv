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
