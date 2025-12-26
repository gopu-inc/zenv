"""
Configuration pour pytest avec structure zenv/zenv_transpiler
"""

import sys
import os
from pathlib import Path

# Obtenir le chemin du projet
project_root = Path(__file__).parent.parent
zenv_path = project_root / "zenv_transpiler"

# Ajouter les chemins nécessaires
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(zenv_path.parent))

# Définir PYTHONPATH
os.environ["PYTHONPATH"] = str(project_root) + ":" + str(zenv_path.parent)

# Fixtures communes
def pytest_configure(config):
    """Configuration pytest"""
    config.addinivalue_line(
        "markers",
        "slow: marque les tests lents (skip par défaut)"
    )