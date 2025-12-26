# zenv_transpiler/cli.py
"""
Interface en ligne de commande pour le transpileur Zenv
"""

import argparse
import sys
import os
from typing import Optional, List
from pathlib import Path

from .transpiler import (
    transpile_file,
    transpile_string,
    transpile_directory,
    validate_zv_code,
    get_zv_version,
    get_supported_features,
    ZvSyntaxError,
    BRAND
)

VERSION = get_zv_version()

class Colors:
    """Codes couleurs pour le terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_color(text: str, color: str = '', bold: bool = False) -> None:
    """Affiche du texte coloré"""
    if color:
        text = color + text
    if bold:
        text = Colors.BOLD + text
    if color or bold:
        text += Colors.END
    print(text)

def print_success(message: str) -> None:
    """Affiche un message de succès"""
    print_color(f"✓ {message}", Colors.GREEN)

def print_error(message: str) -> None:
    """Affiche un message d'erreur"""
    print_color(f"✗ {message}", Colors.RED, bold=True)

def print_warning(message: str) -> None:
    """Affiche un message d'avertissement"""
    print_color(f"⚠ {message}", Colors.YELLOW)

def print_info(message: str) -> None:
    """Affiche un message d'information"""
    print_color(f"ℹ {message}", Colors.BLUE)

def print_header() -> None:
    """Affiche l'en-tête de l'application"""
    print_color(f"""
╔═══════════════════════════════════════════════════╗
║     {Colors.BOLD}Zenv Transpiler v{VERSION}{Colors.END}                    ║
║     Convertisseur .zv/.zenv → Python             ║
╚═══════════════════════════════════════════════════╝
""", Colors.CYAN)

def interactive_mode() -> None:
    """Mode interactif REPL"""
    print_header()
    print_info("Mode Interactif (tapez 'exit' pour quitter)")
    print_info("Entrez du code Zenv ligne par ligne:")
    
    zv_lines = []
    line_number = 1
    
    while True:
        try:
            prompt = f"zenv:{line_number:03d}> "
            line = input(prompt).strip()
            
            if line.lower() in ('exit', 'quit', 'q'):
                break
            elif line == '':
                continue
            
            zv_lines.append(line)
            
            # Essayer de transpiler à chaque ligne
            zv_code = "\n".join(zv_lines)
            try:
                py_code = transpile_string(zv_code)
                print_color("Python:", Colors.GREEN)
                print(py_code.strip())
            except ZvSyntaxError as e:
                # Afficher l'erreur mais continuer
                print_error(str(e).split('\n')[0])  # Première ligne seulement
            
            line_number += 1
            
        except KeyboardInterrupt:
            print("\n\nInterrompu. Tapez 'exit' pour quitter.")
        except EOFError:
            print()
            break

def validate_file(file_path: str) -> bool:
    """Valide un fichier Zenv"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            zv_code = f.read()
        
        is_valid, error = validate_zv_code(zv_code)
        
        if is_valid:
            print_success(f"{file_path} - Syntaxe valide")
            return True
        else:
            print_error(f"{file_path} - {error}")
            return False
            
    except Exception as e:
        print_error(f"{file_path} - Erreur: {str(e)}")
        return False

def main(argv: Optional[List[str]] = None) -> int:
    """Fonction principale du CLI"""
    parser = argparse.ArgumentParser(
        prog="zenv",
        description=f"Transpileur Zenv v{VERSION} - Convertit les fichiers .zv/.zenv en Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  zenv programme.zv                 # Transpile et affiche
  zenv programme.zv -o output.py    # Transpile vers un fichier
  zenv programme.zv --run           # Transpile et exécute
  zenv dossier/ --recursive         # Transpile un répertoire
  zenv --interactive                # Mode interactif
  zenv --validate fichier.zv        # Valide la syntaxe
  zenv --version                    # Affiche la version
        """
    )
    
    # Arguments principaux
    parser.add_argument(
        "input", 
        nargs="?", 
        help="Fichier source .zv ou répertoire"
    )
    
    # Options de sortie
    parser.add_argument(
        "-o", "--output", 
        help="Fichier de sortie .py"
    )
    parser.add_argument(
        "--stdout", 
        action="store_true",
        help="Afficher uniquement sur stdout (pas de fichier)"
    )
    
    # Options d'exécution
    parser.add_argument(
        "--run", 
        action="store_true",
        help="Exécuter le code après transpilation"
    )
    
    # Options de répertoire
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Traiter les répertoires récursivement"
    )
    
    # Options de validation
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valider la syntaxe sans transpiler"
    )
    
    # Options d'information
    parser.add_argument(
        "--features",
        action="store_true",
        help="Afficher les fonctionnalités supportées"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Mode verbeux"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true",
        help="Mode silencieux"
    )
    
    # Modes spéciaux
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true",
        help="Mode interactif REPL"
    )
    parser.add_argument(
        "--version", 
        action="store_true",
        help="Afficher la version"
    )
    
    args = parser.parse_args(argv)
    
    # Afficher la version
    if args.version:
        print(f"Zenv Transpiler v{VERSION}")
        return 0
    
    # Afficher les fonctionnalités
    if args.features:
        print_header()
        print_info("Fonctionnalités supportées:")
        for feature in get_supported_features():
            print(f"  • {feature}")
        return 0
    
    # Mode interactif
    if args.interactive:
        interactive_mode()
        return 0
    
    # Validation de fichier
    if args.validate and args.input:
        if not os.path.exists(args.input):
            print_error(f"Fichier non trouvé: {args.input}")
            return 1
        
        success = validate_file(args.input)
        return 0 if success else 1
    
    # Vérifier qu'un fichier/répertoire est fourni
    if not args.input and not args.interactive:
        parser.print_help()
        print_error("Erreur: Aucun fichier ou répertoire spécifié")
        return 1
    
    # Afficher l'en-tête (sauf en mode silencieux ou stdout)
    if not args.quiet and not args.stdout and os.isatty(0):
        print_header()
    
    # Vérifier que le fichier/répertoire existe
    if not os.path.exists(args.input):
        print_error(f"Fichier ou répertoire non trouvé: {args.input}")
        return 1
    
    # Traitement des répertoires
    if os.path.isdir(args.input):
        try:
            if args.verbose and not args.quiet:
                print_info(f"Transpilation du répertoire: {args.input}")
                if args.recursive:
                    print_info("Mode récursif activé")
            
            results = transpile_directory(args.input, args.output, args.recursive)
            
            # Afficher les résultats
            if not args.quiet:
                print_success(f"Transpilation terminée!")
                print_info(f"Fichiers traités: {results['total_files']}")
                print_info(f"Transpilés avec succès: {results['transpiled']}")
                print_info(f"Erreurs: {results['errors']}")
                
                if results['errors'] > 0 and args.verbose:
                    print_warning("Erreurs détaillées:")
                    for error in results['error_messages']:
                        print(f"  {error}")
            
            return 0 if results['success'] else 1
            
        except Exception as e:
            print_error(f"Erreur lors de la transpilation du répertoire: {str(e)}")
            return 1
    
    # Traitement d'un fichier unique
    try:
        input_path = Path(args.input)
        
        if args.verbose and not args.quiet:
            print_info(f"Transpilation de: {args.input}")
        
        # Transpiler
        if args.stdout or not args.output:
            # Afficher sur stdout
            py_code = transpile_file(args.input, None)
            print(py_code, end="")
        else:
            # Écrire dans un fichier
            py_code = transpile_file(args.input, args.output)
            if not args.quiet:
                print_success(f"Transpilé vers: {args.output}")
        
        # Exécuter si demandé
        if args.run:
            if args.verbose and not args.quiet:
                print_info("Exécution du code...")
            
            # Créer un fichier temporaire si nécessaire
            if args.stdout or not args.output:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(py_code)
                    tmp_file = tmp.name
                
                try:
                    # Exécuter le fichier temporaire
                    import subprocess
                    result = subprocess.run([sys.executable, tmp_file], check=False)
                    return result.returncode
                finally:
                    os.unlink(tmp_file)
            else:
                # Exécuter le fichier généré
                import subprocess
                result = subprocess.run([sys.executable, args.output], check=False)
                return result.returncode
        
        return 0
        
    except ZvSyntaxError as e:
        if not args.quiet:
            print_error(f"Erreur de syntaxe:\n{str(e)}")
        return 2
    except FileNotFoundError as e:
        if not args.quiet:
            print_error(f"Fichier non trouvé: {str(e)}")
        return 1
    except Exception as e:
        if not args.quiet:
            print_error(f"Erreur inattendue: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
        return 3

if __name__ == "__main__":
    sys.exit(main())
