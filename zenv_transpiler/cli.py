# zenv_transpiler/cli.py
import argparse
import sys
import runpy
from .transpiler import transpile_file, BRAND, ZvSyntaxError

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="zenv",
        description="Transpileur .zv vers Python, avec exécution optionnelle."
    )
    parser.add_argument("input", help="Fichier source .zv")
    parser.add_argument("-o", "--output", help="Chemin du fichier .py généré")
    parser.add_argument("--run", action="store_true", help="Exécuter le Python généré après transpilation")
    args = parser.parse_args(argv)

    try:
        py_code = transpile_file(args.input, args.output)
    except ZvSyntaxError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"{BRAND} Fatal: {e}", file=sys.stderr)
        sys.exit(3)

    if args.output:
        print(f"{BRAND} Wrote: {args.output}")

    if args.run:
        # Exécuter en mémoire pour éviter d’écrire sur disque
        ns = {"__name__": "__main__"}
        try:
            exec(py_code, ns)
        except Exception as e:
            print(f"{BRAND} RuntimeError: {e}", file=sys.stderr)
            sys.exit(4)
        else:
            print(f"{BRAND} Done.")
    else:
        # Si pas de sortie fournie, afficher sur stdout pour pipe
        if not args.output:
            print(py_code, end="")

if __name__ == "__main__":
    main()
