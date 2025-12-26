"""
Point d'entrée pour exécuter les tests avec python -m tests
"""

import sys
import os

# Ajouter le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main(["-v", "tests/"]))