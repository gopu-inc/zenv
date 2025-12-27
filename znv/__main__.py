#!/usr/bin/env python3
"""
Point d'entrée principal du runtime Zenv
"""

import sys
import os

# Ajouter le chemin courant pour le imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from znv.cli import main

if __name__ == "__main__":
    sys.exit(main())
