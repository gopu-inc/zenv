# zenv_transpiler/transpiler.py
# Transpileur .zv -> Python amélioré

import re
import ast
from typing import Optional, List, Tuple, Dict
import sys
import os

BRAND = "[ZENV]"

class ZvSyntaxError(Exception):
    pass

def _brand_error(message: str, line_no: int, line: str) -> ZvSyntaxError:
    return ZvSyntaxError(f"{BRAND} SyntaxError (line {line_no}): {message}\n--> {line}")

def _is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return s == "" or s.startswith("#")

# ============================================
# TRANSFORMERS AMÉLIORÉS
# ============================================

# --- IMPORTS ---
def _transform_import(line: str, line_no: int) -> Optional[str]:
    # Import simple: zen[import module]
    m1 = re.fullmatch(r"\s*zen\[\s*import\s+([A-Za-z_][\w.]*)\s*\]\s*", line)
    if m1:
        return f"import {m1.group(1)}"
    
    # Import avec alias: zen[import module from as alias]
    m2 = re.fullmatch(
        r"\s*zen\[\s*import\s+([A-Za-z_][\w]*)(?:\.([A-Za-z_][\w]*))?\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*",
        line,
    )
    if m2:
        module, attr, alias = m2.groups()
        if attr:
            return f"from {module} import {attr} as {alias}"
        else:
            return f"import {module} as {alias}"
    
    # Import multiple: zen[import a, b, c from module]
    m3 = re.fullmatch(
        r"\s*zen\[\s*import\s+([A-Za-z_][\w,\s]+)\s+from\s+([A-Za-z_][\w.]*)\s*\]\s*",
        line,
    )
    if m3:
        imports, module = m3.groups()
        imports_clean = re.sub(r"\s+", "", imports)
        return f"from {module} import {imports_clean}"
    
    return None

# --- ASSIGNMENTS ET DÉCLARATIONS ---
def _transform_assignment(line: str, line_no: int) -> Optional[str]:
    # Assignation simple: var ==> value
    m1 = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*==>\s*(.+)\s*", line)
    if m1:
        var, expr = m1.groups()
        expr = _convert_syntax(expr)
        return f"{var} = {expr}"
    
    # Assignation multiple: a, b, c ==> [1, 2, 3]
    m2 = re.fullmatch(r"\s*((?:[A-Za-z_][\w]*\s*,\s*)+[A-Za-z_][\w]*)\s*==>\s*(.+)\s*", line)
    if m2:
        vars_str, expr = m2.groups()
        vars_clean = re.sub(r"\s+", "", vars_str)
        expr = _convert_syntax(expr)
        return f"{vars_clean} = {expr}"
    
    # Typage: let var: type ==> value
    m3 = re.fullmatch(r"\s*let\s+([A-Za-z_][\w]*)\s*:\s*([A-Za-z_][\w]*)\s*==>\s*(.+)\s*", line)
    if m3:
        var, type_hint, expr = m3.groups()
        expr = _convert_syntax(expr)
        return f"{var}: {type_hint} = {expr}"
    
    return None

# --- STRUCTURES DE DONNÉES ---
def _transform_data_structures(line: str, line_no: int) -> Optional[str]:
    # Liste: [1, 2, 3]
    if re.search(r"\{.*\}", line):
        # Convertir {} en [] pour les listes
        line = line.replace("{", "[").replace("}", "]")
    
    # Dictionnaire: {"key": "value"}
    if re.search(r"«(.*?)»", line):
        line = re.sub(r"«(.*?)»", r'{"\1"}', line)
    
    return None

# --- LIST APPEND ---
def _transform_list_append(line: str, line_no: int) -> Optional[str]:
    # Append simple: list:apend[(value)]
    m1 = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*:\s*apend\[\((.+)\)\]\s*", line)
    if m1:
        lst, item = m1.groups()
        item = _convert_syntax(item)
        return f"{lst}.append({item})"
    
    # Extend: list:extend[(iterable)]
    m2 = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*:\s*extend\[\((.+)\)\]\s*", line)
    if m2:
        lst, items = m2.groups()
        items = _convert_syntax(items)
        return f"{lst}.extend({items})"
    
    # Insert: list:insert[(index, value)]
    m3 = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*:\s*insert\[\((.+),\s*(.+)\)\]\s*", line)
    if m3:
        lst, index, value = m3.groups()
        index = _convert_syntax(index)
        value = _convert_syntax(value)
        return f"{lst}.insert({index}, {value})"
    
    return None

# --- PRINT ---
def _transform_print(line: str, line_no: int) -> Optional[str]:
    # Print simple: zncv.[(expression)]
    m1 = re.fullmatch(r"\s*zncv\.\[\((.+)\)\]\s*", line)
    if m1:
        inner = m1.group(1).strip()
        inner = _convert_syntax(inner)
        
        # Gestion des f-strings avec interpolation
        if re.search(r'\$[A-Za-z_][\w]*', inner):
            # Remplacer $var par {var}
            inner = re.sub(r'\$([A-Za-z_][\w]*)', r'{\1}', inner)
            # Si c'est une chaîne, la transformer en f-string
            if inner.startswith(("'", '"')):
                quote = inner[0]
                content = inner[1:-1]
                return f'print(f{quote}{content}{quote})'
        
        return f"print({inner})"
    
    # Print avec séparateur: zncv.[(expression) sep " "]
    m2 = re.fullmatch(r'\s*zncv\.\[\((.+)\)\s+sep\s+(["\'])(.*?)\2\]\s*', line)
    if m2:
        expr, quote, sep = m2.groups()
        expr = _convert_syntax(expr)
        return f'print({expr}, sep="{sep}")'
    
    # Print sans retour à la ligne: zncv.[(expression) end=""]
    m3 = re.fullmatch(r'\s*zncv\.\[\((.+)\)\s+end\s+(["\'])(.*?)\2\]\s*', line)
    if m3:
        expr, quote, end = m3.groups()
        expr = _convert_syntax(expr)
        return f'print({expr}, end="{end}")'
    
    return None

# --- FONCTIONS ---
def _transform_function(line: str, line_no: int) -> Optional[str]:
    # Définition de fonction: func nom(args) => 
    m1 = re.fullmatch(r"\s*func\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*=>\s*(.*)", line)
    if m1:
        name, params, body = m1.groups()
        params = params.strip()
        body = body.strip()
        
        if body.endswith(":"):
            # Fonction multi-lignes
            return f"def {name}({params}):"
        else:
            # Fonction une ligne
            body = _convert_syntax(body)
            return f"def {name}({params}): return {body}"
    
    # Fonction anonyme: (args) => expression
    m2 = re.fullmatch(r"\s*\(([^)]*)\)\s*=>\s*(.+)\s*", line)
    if m2:
        params, expr = m2.groups()
        expr = _convert_syntax(expr)
        return f"lambda {params}: {expr}"
    
    return None

# --- STRUCTURES DE CONTRÔLE ---
def _transform_control_flow(line: str, line_no: int) -> Optional[str]:
    # If simple: if condition => 
    m1 = re.fullmatch(r"\s*if\s+(.+)\s*=>\s*(.*)", line)
    if m1:
        condition, body = m1.groups()
        condition = _convert_syntax(condition)
        body = body.strip()
        
        if body.endswith(":"):
            # Bloc multi-lignes
            return f"if {condition}:"
        elif body:
            # If one-liner
            body = _convert_syntax(body)
            return f"if {condition}: {body}"
        else:
            return f"if {condition}:"
    
    # Else: else => 
    m2 = re.fullmatch(r"\s*else\s*=>\s*(.*)", line)
    if m2:
        body = m2.group(1).strip()
        if body.endswith(":"):
            return "else:"
        elif body:
            body = _convert_syntax(body)
            return f"else: {body}"
        else:
            return "else:"
    
    # For loop: for item in iterable => 
    m3 = re.fullmatch(r"\s*for\s+([A-Za-z_][\w]*)\s+in\s+(.+)\s*=>\s*(.*)", line)
    if m3:
        var, iterable, body = m3.groups()
        iterable = _convert_syntax(iterable)
        body = body.strip()
        
        if body.endswith(":"):
            return f"for {var} in {iterable}:"
        elif body:
            body = _convert_syntax(body)
            return f"for {var} in {iterable}: {body}"
        else:
            return f"for {var} in {iterable}:"
    
    # While loop: while condition => 
    m4 = re.fullmatch(r"\s*while\s+(.+)\s*=>\s*(.*)", line)
    if m4:
        condition, body = m4.groups()
        condition = _convert_syntax(condition)
        body = body.strip()
        
        if body.endswith(":"):
            return f"while {condition}:"
        elif body:
            body = _convert_syntax(body)
            return f"while {condition}: {body}"
        else:
            return f"while {condition}:"
    
    return None

# --- CLASSES ---
def _transform_class(line: str, line_no: int) -> Optional[str]:
    # Définition de classe: class Nom =>
    m1 = re.fullmatch(r"\s*class\s+([A-Za-z_][\w]*)\s*=>\s*(.*)", line)
    if m1:
        name, body = m1.groups()
        body = body.strip()
        
        if body.endswith(":"):
            return f"class {name}:"
        elif body:
            body = _convert_syntax(body)
            return f"class {name}: {body}"
        else:
            return f"class {name}:"
    
    # Héritage: class Nom(Parent) =>
    m2 = re.fullmatch(r"\s*class\s+([A-Za-z_][\w]*)\s*\(\s*([^)]+)\s*\)\s*=>\s*(.*)", line)
    if m2:
        name, parent, body = m2.groups()
        body = body.strip()
        
        if body.endswith(":"):
            return f"class {name}({parent}):"
        elif body:
            body = _convert_syntax(body)
            return f"class {name}({parent}): {body}"
        else:
            return f"class {name}({parent}):"
    
    return None

# --- RETOUR ET YIELD ---
def _transform_return(line: str, line_no: int) -> Optional[str]:
    # Return: return expression
    m1 = re.fullmatch(r"\s*retour\s+(.+)\s*", line)
    if m1:
        expr = m1.group(1)
        expr = _convert_syntax(expr)
        return f"return {expr}"
    
    # Yield: yield expression
    m2 = re.fullmatch(r"\s*yield\s+(.+)\s*", line)
    if m2:
        expr = m2.group(1)
        expr = _convert_syntax(expr)
        return f"yield {expr}"
    
    return None

# --- ACCÈS ET INDEXATION ---
def _transform_access(line: str, line_no: int) -> Optional[str]:
    # Accès à un élément: var~key = dict{{index}}
    m1 = re.fullmatch(
        r"\s*([A-Za-z_][\w]*)~([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\{\{([0-9]+)\}\}\s*",
        line
    )
    if m1:
        left_a, left_b, base, idx = m1.groups()
        return f"{left_a}_{left_b} = {base}[{idx}]"
    
    # Indexation simple: list[index]
    if re.search(r"\{\{", line):
        line = re.sub(r"\{\{(.+?)\}\}", r"[\1]", line)
        return line
    
    # Accès par point: obj.attr
    if re.search(r"~", line):
        line = line.replace("~", ".")
        return line
    
    return None

# --- GESTION DES EXCEPTIONS ---
def _transform_try_catch(line: str, line_no: int) -> Optional[str]:
    # Try: try => 
    m1 = re.fullmatch(r"\s*try\s*=>\s*(.*)", line)
    if m1:
        body = m1.group(1).strip()
        if body.endswith(":"):
            return "try:"
        else:
            return "try:"
    
    # Except: except Exception as e => 
    m2 = re.fullmatch(r"\s*except\s+([A-Za-z_][\w]*)(?:\s+as\s+([A-Za-z_][\w]*))?\s*=>\s*(.*)", line)
    if m2:
        exc, alias, body = m2.groups()
        body = body.strip()
        
        if alias:
            if body.endswith(":"):
                return f"except {exc} as {alias}:"
            elif body:
                body = _convert_syntax(body)
                return f"except {exc} as {alias}: {body}"
            else:
                return f"except {exc} as {alias}:"
        else:
            if body.endswith(":"):
                return f"except {exc}:"
            elif body:
                body = _convert_syntax(body)
                return f"except {exc}: {body}"
            else:
                return f"except {exc}:"
    
    return None

# --- OPÉRATEURS SPÉCIAUX ---
def _convert_syntax(expr: str) -> str:
    """Convertit la syntaxe Zenv vers Python"""
    if not expr:
        return expr
    
    # Opérateurs de comparaison
    expr = expr.replace("==", "==")
    expr = expr.replace("!=", "!=")
    expr = expr.replace("<==", "<=")
    expr = expr.replace(">==", ">=")
    
    # Opérateurs logiques
    expr = expr.replace("&&", "and")
    expr = expr.replace("||", "or")
    expr = expr.replace("!", "not ")
    
    # Opérateur null-coalescing
    expr = re.sub(r"\?\?", "or", expr)
    
    # Opérateur ternaire
    expr = re.sub(r"(\S+)\s*\?\s*(.+?)\s*:\s*(.+)$", r"\2 if \1 else \3", expr)
    
    # Flèches pour lambda
    expr = re.sub(r"=>", ":", expr)
    
    return expr

# ============================================
# TRANSFORMATION PRINCIPALE
# ============================================

TRANSFORMERS = [
    _transform_import,
    _transform_function,
    _transform_class,
    _transform_control_flow,
    _transform_try_catch,
    _transform_return,
    _transform_list_append,
    _transform_print,
    _transform_access,
    _transform_data_structures,
    _transform_assignment,
]

def transpile_string(zv_code: str) -> str:
    py_lines = []
    indent_level = 0
    
    for i, raw in enumerate(zv_code.splitlines(), start=1):
        line = raw.rstrip("\n")
        
        # Gestion de l'indentation
        stripped = line.lstrip()
        if stripped:
            current_indent = len(line) - len(stripped)
            indent_diff = current_indent - indent_level * 4
            
            # Ajuster l'indentation Python
            if indent_diff > 0:
                indent_level += 1
            elif indent_diff < 0:
                indent_level = max(0, indent_level - 1)
        
        if _is_blank_or_comment(line):
            py_lines.append(" " * (indent_level * 4) + line)
            continue
        
        result = None
        for transformer in TRANSFORMERS:
            result = transformer(stripped, i)
            if result is not None:
                break
        
        if result is None:
            # Si aucune transformation n'est trouvée, garder la ligne originale
            result = _convert_syntax(stripped)
        
        # Ajouter l'indentation
        py_lines.append(" " * (indent_level * 4) + result)
    
    return "\n".join(py_lines) + "\n"

def transpile_file(input_path: str, output_path: Optional[str] = None) -> str:
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            zv_code = f.read()
        
        py_code = transpile_string(zv_code)
        
        if output_path:
            # Créer les répertoires si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(py_code)
            
            # Ajouter un shebang si non présent
            if not py_code.startswith("#!"):
                with open(output_path, "r+", encoding="utf-8") as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write("#!/usr/bin/env python3\n" + content)
        
        return py_code
    
    except FileNotFoundError:
        raise ZvSyntaxError(f"{BRAND} FileNotFoundError: Cannot open {input_path}")
    except Exception as e:
        raise ZvSyntaxError(f"{BRAND} TranspilationError: {str(e)}")

# ============================================
# CLI AMÉLIORÉ
# ============================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zenv Transpiler - Convert .zv files to Python")
    parser.add_argument("input", help="Input .zv file")
    parser.add_argument("-o", "--output", help="Output Python file")
    parser.add_argument("--run", action="store_true", help="Run the transpiled code immediately")
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    
    args = parser.parse_args()
    
    try:
        if args.debug:
            print(f"{BRAND} Transpiling {args.input}...")
        
        py_code = transpile_file(args.input, args.output)
        
        if args.output and not args.run:
            print(f"{BRAND} Successfully transpiled to {args.output}")
        
        if args.run:
            if args.debug:
                print(f"{BRAND} Running transpiled code...")
                print("-" * 50)
            
            # Exécuter le code transpilé
            exec_globals = {}
            exec(py_code, exec_globals)
        
        elif not args.output:
            # Afficher le code transpilé
            print(py_code)
    
    except ZvSyntaxError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{BRAND} Error: {str(e)}", file=sys.stderr)
        sys.exit(1)