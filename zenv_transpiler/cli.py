# zenv_transpiler/cli.py
"""
CLI pour le transpileur Zenv -> Python
Version améliorée avec plus de fonctionnalités et meilleure UX
"""

import argparse
import sys
import os
import time
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from .transpiler import transpile_file, transpile_string, BRAND, ZvSyntaxError

# Version du transpileur
VERSION = "1.2.0"
SUPPORTED_EXTENSIONS = {'.zv', '.zenv'}

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
    UNDERLINE = '\033[4m'

def print_colored(text: str, color: str, bold: bool = False) -> None:
    """Affiche du texte coloré dans le terminal"""
    if bold:
        text = Colors.BOLD + text
    print(color + text + Colors.END)

def print_header() -> None:
    """Affiche l'en-tête du transpileur"""
    print_colored(f"""
╔═══════════════════════════════════════════════════╗
║     {Colors.BOLD}Zenv Transpiler v{VERSION}{Colors.END}                    ║
║     Convertisseur .zv/.zenv → Python             ║
╚═══════════════════════════════════════════════════╝
    """, Colors.CYAN)

def print_success(message: str) -> None:
    """Affiche un message de succès"""
    print_colored(f"✓ {message}", Colors.GREEN)

def print_error(message: str) -> None:
    """Affiche un message d'erreur"""
    print_colored(f"✗ {message}", Colors.RED, bold=True)

def print_warning(message: str) -> None:
    """Affiche un message d'avertissement"""
    print_colored(f"⚠ {message}", Colors.YELLOW)

def print_info(message: str) -> None:
    """Affiche un message d'information"""
    print_colored(f"ℹ {message}", Colors.BLUE)

def validate_input_file(input_path: str) -> Path:
    """Valide le fichier d'entrée"""
    path = Path(input_path)
    
    if not path.exists():
        print_error(f"Fichier non trouvé: {input_path}")
        sys.exit(1)
    
    if not path.is_file():
        print_error(f"Le chemin n'est pas un fichier: {input_path}")
        sys.exit(1)
    
    if path.suffix not in SUPPORTED_EXTENSIONS:
        print_warning(f"Extension non standard: {path.suffix}. Utilisation: {', '.join(SUPPORTED_EXTENSIONS)}")
    
    return path

def get_output_path(input_path: Path, output_arg: Optional[str]) -> Path:
    """Détermine le chemin de sortie"""
    if output_arg:
        output_path = Path(output_arg)
        
        # Si c'est un répertoire, y placer le fichier avec même nom
        if output_path.is_dir():
            output_path = output_path / input_path.with_suffix('.py').name
        
        return output_path
    
    # Par défaut, même répertoire que l'entrée avec extension .py
    return input_path.with_suffix('.py')

def transpile_directory(input_dir: str, output_dir: Optional[str], 
                       recursive: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """
    Transpile tous les fichiers .zv d'un répertoire
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path / "transpiled"
    
    if not input_path.exists():
        print_error(f"Répertoire non trouvé: {input_dir}")
        return {"success": False, "files": 0, "errors": 1}
    
    if not input_path.is_dir():
        print_error(f"Le chemin n'est pas un répertoire: {input_dir}")
        return {"success": False, "files": 0, "errors": 1}
    
    # Créer le répertoire de sortie
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Collecter les fichiers
    pattern = "**/*.zv" if recursive else "*.zv"
    zv_files = list(input_path.glob(pattern))
    
    if not zv_files:
        print_warning(f"Aucun fichier .zv trouvé dans {input_dir}")
        return {"success": True, "files": 0, "errors": 0}
    
    print_info(f"Transpilation de {len(zv_files)} fichiers...")
    
    results = {
        "success": True,
        "files": len(zv_files),
        "transpiled": 0,
        "errors": 0,
        "errors_list": []
    }
    
    for zv_file in zv_files:
        try:
            # Déterminer le chemin de sortie relatif
            if output_dir:
                rel_path = zv_file.relative_to(input_path)
                output_file = output_path / rel_path.with_suffix('.py')
                output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_file = zv_file.with_suffix('.py')
            
            if verbose:
                print_info(f"Transpilation: {zv_file} → {output_file}")
            
            # Transpiler
            transpile_file(str(zv_file), str(output_file))
            
            results["transpiled"] += 1
            if verbose:
                print_success(f"✓ {zv_file.name}")
            
        except ZvSyntaxError as e:
            results["errors"] += 1
            results["errors_list"].append(str(zv_file) + ": " + str(e))
            print_error(f"Erreur dans {zv_file.name}: {e}")
        except Exception as e:
            results["errors"] += 1
            results["success"] = False
            results["errors_list"].append(str(zv_file) + ": " + str(e))
            print_error(f"Erreur inattendue dans {zv_file.name}: {e}")
    
    # Résumé
    print_colored("\n" + "="*50, Colors.CYAN)
    print_info("Résumé de la transpilation:")
    print_success(f"Fichiers transpilés: {results['transpiled']}/{results['files']}")
    if results['errors'] > 0:
        print_error(f"Erreurs: {results['errors']}")
    else:
        print_success("Aucune erreur!")
    
    return results

def format_code(code: str, output_path: Optional[str] = None) -> bool:
    """
    Formate le code Python généré avec black ou yapf
    """
    try:
        if output_path:
            # Essayer black d'abord
            try:
                subprocess.run(
                    ["black", "--quiet", output_path],
                    check=True,
                    capture_output=True
                )
                if os.path.exists(output_path):
                    print_success("Code formaté avec black")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Essayer yapf sinon
            try:
                subprocess.run(
                    ["yapf", "-i", output_path],
                    check=True,
                    capture_output=True
                )
                if os.path.exists(output_path):
                    print_success("Code formaté avec yapf")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return False
    except Exception:
        return False

def generate_stats(py_code: str, input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Génère des statistiques sur la transpilation
    """
    zv_lines = 0
    with open(input_path, 'r', encoding='utf-8') as f:
        zv_lines = len(f.readlines())
    
    py_lines = len(py_code.splitlines())
    
    # Taille des fichiers
    zv_size = input_path.stat().st_size
    py_size = output_path.stat().st_size if output_path.exists() else len(py_code.encode())
    
    return {
        "zv_lines": zv_lines,
        "py_lines": py_lines,
        "zv_size_kb": round(zv_size / 1024, 2),
        "py_size_kb": round(py_size / 1024, 2),
        "compression_ratio": round(py_size / zv_size * 100, 2) if zv_size > 0 else 0,
        "lines_ratio": round(py_lines / zv_lines * 100, 2) if zv_lines > 0 else 0
    }

def interactive_mode() -> None:
    """
    Mode interactif pour tester la transpilation
    """
    print_colored("\n" + "="*50, Colors.CYAN)
    print_colored("Mode Interactif Zenv", Colors.BOLD + Colors.CYAN)
    print_colored("Entrez du code Zenv (CTRL+D pour quitter)", Colors.BLUE)
    print_colored("="*50 + "\n", Colors.CYAN)
    
    print("Exemples rapides:")
    print("  message ==> 'Hello'")
    print("  zncv.[(message)]")
    print("  numbers ==> {1, 2, 3}")
    print("  numbers:apend[(4)]")
    print()
    
    zv_code_lines = []
    try:
        while True:
            try:
                line = input("zenv> ")
                if line.strip().lower() == "exit":
                    break
                zv_code_lines.append(line)
            except EOFError:
                print()
                break
    except KeyboardInterrupt:
        print("\nInterruption.")
        return
    
    if not zv_code_lines:
        return
    
    zv_code = "\n".join(zv_code_lines)
    
    try:
        print_colored("\n" + "-"*50, Colors.YELLOW)
        print_colored("Code Python généré:", Colors.BOLD)
        print_colored("-"*50, Colors.YELLOW)
        
        py_code = transpile_string(zv_code)
        print(py_code)
        
        print_colored("-"*50, Colors.YELLOW)
        print_colored("Exécution du code:", Colors.BOLD)
        print_colored("-"*50, Colors.YELLOW)
        
        # Exécuter le code
        exec_globals = {}
        exec(py_code, exec_globals)
        
        print_colored("\n✓ Exécution réussie!", Colors.GREEN)
        
    except ZvSyntaxError as e:
        print_error(f"Erreur de syntaxe: {e}")
    except Exception as e:
        print_error(f"Erreur d'exécution: {e}")

def main(argv: Optional[List[str]] = None) -> int:
    """
    Fonction principale du CLI
    """
    parser = argparse.ArgumentParser(
        prog="zenv",
        description=f"{Colors.BOLD}Zenv Transpiler v{VERSION}{Colors.END} - Convertisseur .zv/.zenv → Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.CYAN}Exemples:{Colors.END}
  {Colors.GREEN}zenv programme.zv{Colors.END}            # Transpile et affiche
  {Colors.GREEN}zenv programme.zv -o output.py{Colors.END} # Transpile vers fichier
  {Colors.GREEN}zenv programme.zv --run{Colors.END}       # Transpile et exécute
  {Colors.GREEN}zenv dossier/ --recursive{Colors.END}     # Transpile récursivement
  {Colors.GREEN}zenv --interactive{Colors.END}           # Mode interactif
  {Colors.GREEN}zenv --version{Colors.END}              # Affiche la version
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
    parser.add_argument(
        "--exec", 
        metavar="ARGS",
        help="Arguments à passer au programme exécuté"
    )
    
    # Options de répertoire
    parser.add_argument(
        "--recursive", 
        action="store_true",
        help="Traiter les répertoires récursivement"
    )
    
    # Options de formatage
    parser.add_argument(
        "--format", 
        action="store_true",
        help="Formater le code généré (black/yapf requis)"
    )
    parser.add_argument(
        "--no-format", 
        action="store_true",
        help="Ne pas formater le code généré"
    )
    
    # Options d'information
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Afficher les statistiques de transpilation"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Mode verbeux"
    )
    parser.add_argument(
        "--quiet", "-q", 
        action="store_true",
        help="Mode silencieux (minimal output)"
    )
    
    # Modes spéciaux
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true",
        help="Mode interactif"
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
    
    # Mode interactif
    if args.interactive:
        print_header()
        interactive_mode()
        return 0
    
    # Validation de l'entrée
    if not args.input and not args.interactive:
        parser.print_help()
        print_error("Aucun fichier ou répertoire spécifié")
        return 1
    
    # Mode silencieux
    if not args.quiet and not args.stdout:
        print_header()
    
    # Valider le chemin d'entrée
    input_path = validate_input_file(args.input)
    
    # Si c'est un répertoire
    if input_path.is_dir():
        results = transpile_directory(
            str(input_path), 
            args.output, 
            args.recursive, 
            args.verbose
        )
        
        if args.stats and not args.quiet:
            print_info(f"Fichiers traités: {results['files']}")
            print_info(f"Transpilés avec succès: {results['transpiled']}")
            print_info(f"Erreurs: {results['errors']}")
        
        return 0 if results["success"] else 1
    
    # Si c'est un fichier
    start_time = time.time()
    
    try:
        # Déterminer le chemin de sortie
        if args.stdout:
            output_path = None
        else:
            output_path = get_output_path(input_path, args.output)
        
        # Transpiler
        if args.verbose and not args.quiet:
            print_info(f"Transpilation: {input_path} → {output_path or 'stdout'}")
        
        py_code = transpile_file(str(input_path), str(output_path) if output_path else None)
        
        if output_path and not args.quiet:
            print_success(f"Transpilé vers: {output_path}")
        
        # Formater le code
        if args.format and output_path and not args.no_format:
            if args.verbose and not args.quiet:
                print_info("Formatage du code...")
            format_code(py_code, str(output_path))
        
        # Exécuter le code
        if args.run:
            if not args.quiet:
                print_info("Exécution du code...")
                print_colored("-"*50, Colors.YELLOW)
            
            try:
                exec_args = args.exec.split() if args.exec else []
                
                if exec_args:
                    # Exécuter comme script séparé
                    cmd = [sys.executable, str(output_path)] + exec_args
                    if args.verbose:
                        print_info(f"Commande: {' '.join(cmd)}")
                    result = subprocess.run(cmd, check=True)
                    return result.returncode
                else:
                    # Exécuter dans le même processus
                    exec_globals = {"__name__": "__main__", "__file__": str(output_path)}
                    exec(py_code, exec_globals)
                    
                    if not args.quiet:
                        print_colored("-"*50, Colors.YELLOW)
                        print_success("Exécution terminée avec succès")
                    
            except Exception as e:
                print_error(f"Erreur d'exécution: {e}")
                return 4
        
        # Afficher les statistiques
        if args.stats and output_path:
            stats = generate_stats(py_code, input_path, Path(output_path))
            
            if not args.quiet:
                print_colored("\nStatistiques de transpilation:", Colors.BOLD + Colors.CYAN)
                print(f"  Lignes Zenv: {stats['zv_lines']}")
                print(f"  Lignes Python: {stats['py_lines']}")
                print(f"  Ratio: {stats['lines_ratio']}%")
                print(f"  Taille Zenv: {stats['zv_size_kb']} KB")
                print(f"  Taille Python: {stats['py_size_kb']} KB")
                print(f"  Compression: {stats['compression_ratio']}%")
                
                elapsed = time.time() - start_time
                print(f"  Temps écoulé: {elapsed:.3f}s")
        
        # Afficher sur stdout si demandé
        if args.stdout:
            print(py_code, end="")
        
        return 0
        
    except ZvSyntaxError as e:
        if not args.quiet:
            print_error(f"Erreur de syntaxe: {e}")
        return 2
    except Exception as e:
        if not args.quiet:
            print_error(f"Erreur inattendue: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
        return 3

if __name__ == "__main__":
    sys.exit(main())
