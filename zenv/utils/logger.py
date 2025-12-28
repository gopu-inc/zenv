import sys
from datetime import datetime
from typing import Any

class Logger:
    
    COLORS = {
        'info': '\033[94m',
        'success': '\033[92m',
        'warning': '\033[93m',
        'error': '\033[91m',
        'reset': '\033[0m'
    }
    
    def __init__(self, name: str = "zenv"):
        self.name = name
    
    def info(self, message: Any):
        self._log('info', message)
    
    def success(self, message: Any):
        self._log('success', message)
    
    def warning(self, message: Any):
        self._log('warning', message)
    
    def error(self, message: Any):
        self._log('error', message)
    
    def _log(self, level: str, message: Any):
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = self.COLORS.get(level, '')
        reset = self.COLORS['reset']
        
        if level == 'error':
            output = sys.stderr
        else:
            output = sys.stdout
        
        print(f"{color}[{timestamp}] [{level.upper()}] {message}{reset}", file=output)
