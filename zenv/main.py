#!/usr/bin/env python3
"""
Point d'entrée principal de l'écosystème Zenv
"""

import sys
import os

# Ajouter le chemin courant
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zenv.command.com import ZenvCLI

def main():
    cli = ZenvCLI()
    return cli.run(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
