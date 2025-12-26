#!/usr/bin/env python3
"""
Script pour exécuter tous les tests Zenv
"""

import sys
import os
import subprocess
import argparse

def run_tests(test_path=None, verbose=False, coverage=False):
    """Exécuter les tests avec pytest"""
    
    # Ajouter le répertoire courant au PYTHONPATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ['PYTHONPATH'] = current_dir + ':' + os.environ.get('PYTHONPATH', '')
    
    # Commandes pytest
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=zenv_transpiler", "--cov-report=term-missing"])
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    print(f"Exécution: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Erreur: pytest non trouvé. Installez-le avec: pip install pytest")
        return 1
    except KeyboardInterrupt:
        print("\nTests interrompus par l'utilisateur")
        return 130

def main():
    parser = argparse.ArgumentParser(description="Exécuter les tests Zenv")
    parser.add_argument("path", nargs="?", help="Chemin des tests à exécuter")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    parser.add_argument("-c", "--coverage", action="store_true", help="Générer un rapport de couverture")
    parser.add_argument("--fast", action="store_true", help="Exécuter uniquement les tests rapides")
    
    args = parser.parse_args()
    
    if args.fast:
        os.environ["PYTEST_MARKERS"] = "not slow"
    
    return_code = run_tests(args.path, args.verbose, args.coverage)
    
    sys.exit(return_code)

if __name__ == "__main__":
    main()