# zenv_transpiler/transpiler.py
# Transpileur .zv -> Python complet

import re
import os
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

BRAND = "[ZENV]"

class ZvSyntaxError(Exception):
    """Exception pour les erreurs de syntaxe Zenv"""
    pass

def _brand_error(message: str, line_no: int, line: str) -> ZvSyntaxError:
    """Crée une erreur de syntaxe formatée"""
    return ZvSyntaxError(f"{BRAND} SyntaxError (line {line_no}): {message}\n--> {line}")

def _is_blank_or_comment(line: str) -> bool:
    """Vérifie si la ligne est vide ou un commentaire"""
    s = line.strip()
    return s == "" or s.startswith("#")

# ============================================================================
# FONCTIONS D'AIDE POUR LA CONVERSION DE SYNTAXE
# ============================================================================

def _convert_braces_to_brackets(expr: str) -> str:
    """
    Convertit les accolades {} en crochets [] pour les listes.
    Gère les cas imbriqués et les chaînes.
    """
    if not expr:
        return expr
    
    result = []
    i = 0
    in_string = False
    string_char = None
    brace_depth = 0
    brace_start = -1
    
    while i < len(expr):
        char = expr[i]
        
        # Gestion des chaînes
        if char in ('"', "'") and (i == 0 or expr[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        
        if not in_string:
            if char == '{':
                if brace_depth == 0:
                    brace_start = i
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0 and brace_start != -1:
                    # Extraire le contenu entre les accolades
                    content = expr[brace_start + 1:i]
                    
                    # Vérifier si c'est un dictionnaire ou une liste
                    is_dict = False
                    if ':' in content:
                        # Vérifier plus précisément si c'est un dict
                        # Format dict: {key: value, key2: value2}
                        parts = re.split(r',\s*(?![^\[\]]*\])', content)
                        for part in parts:
                            if ':' in part and not part.strip().startswith("'"):
                                key_val = part.split(':', 1)
                                if len(key_val) == 2:
                                    key = key_val[0].strip()
                                    # Vérifier si la clé est une chaîne ou un identifiant
                                    if (key.startswith("'") and key.endswith("'")) or \
                                       (key.startswith('"') and key.endswith('"')) or \
                                       re.match(r'^[A-Za-z_][\w]*$', key):
                                        is_dict = True
                                        break
                    
                    if is_dict:
                        result.append('{' + content + '}')
                    else:
                        # C'est une liste, convertir les accolades
                        # et aussi convertir les accolades internes si nécessaire
                        converted_content = _convert_braces_to_brackets(content)
                        result.append('[' + converted_content + ']')
                    brace_start = -1
                    i += 1
                    continue
        
        if brace_depth == 0:
            result.append(char)
        
        i += 1
    
    # Si on a des accolades non fermées, les laisser telles quelles
    if brace_depth > 0:
        # Reconstruire l'expression originale
        return expr
    
    return ''.join(result)

def _convert_special_syntax(expr: str) -> str:
    """
    Convertit la syntaxe spéciale Zenv en syntaxe Python
    """
    if not expr:
        return expr
    
    # 1. Convertir les accolades pour les listes
    expr = _convert_braces_to_brackets(expr)
    
    # 2. Convertir les opérateurs logiques
    expr = expr.replace('&&', ' and ').replace('||', ' or ').replace('!', 'not ')
    
    # 3. Convertir l'opérateur null-coalescing (?? -> or)
    # Attention à ne pas toucher aux ?? dans les chaînes
    parts = []
    i = 0
    in_string = False
    string_char = None
    
    while i < len(expr):
        if i < len(expr) - 1 and expr[i:i+2] == '??' and not in_string:
            parts.append(' or ')
            i += 2
            continue
        
        char = expr[i]
        if char in ('"', "'") and (i == 0 or expr[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
        
        parts.append(char)
        i += 1
    
    expr = ''.join(parts)
    
    # 4. Convertir l'opérateur ternaire (condition ? a : b -> a if condition else b)
    # Cette conversion est complexe, on la fait seulement pour des cas simples
    if '?' in expr and ':' in expr and not any(c in expr for c in '\'"'):
        try:
            # Pattern simple: condition ? vrai : faux
            match = re.match(r'^(.*?)\s*\?\s*(.*?)\s*:\s*(.*)$', expr)
            if match:
                condition, true_expr, false_expr = match.groups()
                expr = f'{true_expr} if {condition} else {false_expr}'
        except:
            pass  # En cas d'erreur, garder l'expression originale
    
    return expr.strip()

# ============================================================================
# TRANSFORMATEURS DE SYNTAXE
# ============================================================================

def _transform_import(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les déclarations d'import Zenv en Python
    Formats supportés:
    - zen[import module]
    - zen[import module from as alias]
    - zen[import module.function from as alias]
    """
    
    # Import simple: zen[import module] ou zen[imoprt module] (tolère la faute)
    m1 = re.fullmatch(r'\s*zen\[\s*(?:imoprt|import)\s+([A-Za-z_][\w.]*)\s*\]\s*', line)
    if m1:
        return f"import {m1.group(1)}"
    
    # Import avec alias: zen[import module from as alias]
    m2 = re.fullmatch(
        r'\s*zen\[\s*import\s+([A-Za-z_][\w]*)\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*',
        line,
    )
    if m2:
        module, alias = m2.groups()
        return f"import {module} as {alias}"
    
    # Import spécifique avec alias: zen[import module.item from as alias]
    m3 = re.fullmatch(
        r'\s*zen\[\s*import\s+([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*',
        line,
    )
    if m3:
        module, item, alias = m3.groups()
        return f"from {module} import {item} as {alias}"
    
    # Import spécifique sans alias: zen[import module.item]
    m4 = re.fullmatch(
        r'\s*zen\[\s*import\s+([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\s*\]\s*',
        line,
    )
    if m4:
        module, item = m4.groups()
        return f"from {module} import {item}"
    
    return None

def _transform_assignment(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les assignations Zenv (var ==> valeur) en Python (var = valeur)
    """
    # Assignation simple: variable ==> expression
    m = re.fullmatch(r'\s*([A-Za-z_][\w]*)\s*==>\s*(.+)\s*', line)
    if m:
        var, expr = m.groups()
        expr = _convert_special_syntax(expr)
        return f"{var} = {expr}"
    
    # Vérifier les noms de variables invalides
    m_invalid = re.match(r'\s*([0-9]+[A-Za-z_]*)\s*==>', line)
    if m_invalid:
        raise _brand_error(f"Invalid variable name '{m_invalid.group(1)}'", line_no, line)
    
    # Assignation multiple (support basique): a, b ==> [1, 2]
    m_multi = re.fullmatch(r'\s*((?:[A-Za-z_][\w]*\s*,\s*)+[A-Za-z_][\w]*)\s*==>\s*(.+)\s*', line)
    if m_multi:
        vars_str, expr = m_multi.groups()
        vars_clean = re.sub(r'\s+', '', vars_str)
        expr = _convert_special_syntax(expr)
        return f"{vars_clean} = {expr}"
    
    return None

def _transform_list_append(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les opérations d'ajout de liste: list:apend[(value)]
    """
    m = re.fullmatch(r'\s*([A-Za-z_][\w]*)\s*:\s*apend\[\((.+)\)\]\s*', line)
    if m:
        lst, item = m.groups()
        item = _convert_special_syntax(item)
        return f"{lst}.append({item})"
    
    # Support pour extend: list:extend[(iterable)]
    m_extend = re.fullmatch(r'\s*([A-Za-z_][\w]*)\s*:\s*extend\[\((.+)\)\]\s*', line)
    if m_extend:
        lst, items = m_extend.groups()
        items = _convert_special_syntax(items)
        return f"{lst}.extend({items})"
    
    return None

def _transform_print(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les déclarations d'impression: zncv.[(expression)]
    """
    # Version basique: zncv.[(expression)]
    m = re.fullmatch(r'\s*zncv\.\[\((.+)\)\]\s*', line)
    if not m:
        # Vérifier si c'est un print mal formé
        if 'zncv.[(' in line and not line.strip().endswith(')]'):
            raise _brand_error("Malformed print statement - missing closing )]", line_no, line)
        return None
    
    inner = m.group(1).strip()
    
    # Gestion des f-strings avec $s
    if '$s' in inner or ('$' in inner and re.search(r'\$\s*[A-Za-z_]', inner)):
        # Extraire la chaîne de base
        str_match = re.search(r'[\'"]([^\'"]*?)[\'"]', inner)
        if str_match:
            string_content = str_match.group(1)
            string_quote = inner[str_match.start()]
            
            # Trouver toutes les variables après $
            rest = inner[str_match.end():].strip()
            variables = re.findall(r'\$\s*([A-Za-z_][\w]*)', rest)
            
            if variables:
                # Construire la f-string
                f_string = f'f{string_quote}{string_content}'
                for var in variables:
                    f_string += f' {{{var}}}'
                f_string += string_quote
                return f"print({f_string})"
    
    # Expression normale
    inner = _convert_special_syntax(inner)
    return f"print({inner})"

def _transform_access(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les accès: var~attr = other{{index}}
    """
    m = re.fullmatch(
        r'\s*([A-Za-z_][\w]*)~([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\{\{([0-9]+)\}\}\s*',
        line
    )
    if m:
        left_a, left_b, base, idx = m.groups()
        return f"{left_a}_{left_b} = {base}[{idx}]"
    
    # Conversion générique des {{index}} en [index]
    if '{{' in line and '}}' in line:
        line = re.sub(r'\{\{([^}]+)\}\}', r'[\1]', line)
        # Conversion générique de ~ en .
        line = line.replace('~', '.')
        return line
    
    return None

def _transform_function(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les définitions de fonctions: func name(params) => body
    """
    # Définition de fonction simple
    m = re.fullmatch(r'\s*func\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*=>\s*(.*)', line)
    if m:
        name, params, body = m.groups()
        params = params.strip()
        body = body.strip()
        
        if body.endswith(':'):
            # Fonction avec bloc
            return f"def {name}({params}):"
        elif body:
            # Fonction one-liner
            body = _convert_special_syntax(body)
            return f"def {name}({params}):\n    return {body}"
        else:
            return f"def {name}({params}):"
    
    # Fonction lambda
    m_lambda = re.fullmatch(r'\s*\(([^)]*)\)\s*=>\s*(.+)', line)
    if m_lambda:
        params, expr = m_lambda.groups()
        expr = _convert_special_syntax(expr)
        return f"lambda {params}: {expr}"
    
    return None

def _transform_control_flow(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les structures de contrôle
    """
    # If statement
    m_if = re.fullmatch(r'\s*if\s+(.+)\s*=>\s*(.*)', line)
    if m_if:
        condition, body = m_if.groups()
        condition = _convert_special_syntax(condition)
        body = body.strip()
        
        if body.endswith(':'):
            return f"if {condition}:"
        elif body:
            body = _convert_special_syntax(body)
            return f"if {condition}: {body}"
        else:
            return f"if {condition}:"
    
    # For loop
    m_for = re.fullmatch(r'\s*for\s+([A-Za-z_][\w]*)\s+in\s+(.+)\s*=>\s*(.*)', line)
    if m_for:
        var, iterable, body = m_for.groups()
        iterable = _convert_special_syntax(iterable)
        body = body.strip()
        
        if body.endswith(':'):
            return f"for {var} in {iterable}:"
        elif body:
            body = _convert_special_syntax(body)
            return f"for {var} in {iterable}: {body}"
        else:
            return f"for {var} in {iterable}:"
    
    # While loop
    m_while = re.fullmatch(r'\s*while\s+(.+)\s*=>\s*(.*)', line)
    if m_while:
        condition, body = m_while.groups()
        condition = _convert_special_syntax(condition)
        body = body.strip()
        
        if body.endswith(':'):
            return f"while {condition}:"
        elif body:
            body = _convert_special_syntax(body)
            return f"while {condition}: {body}"
        else:
            return f"while {condition}:"
    
    # Else/elif
    m_else = re.fullmatch(r'\s*(else|elif\s+.+)\s*=>\s*(.*)', line)
    if m_else:
        keyword, body = m_else.groups()
        body = body.strip()
        
        if 'elif' in keyword:
            # Extraire la condition de elif
            match = re.match(r'elif\s+(.+)', keyword)
            if match:
                condition = _convert_special_syntax(match.group(1))
                keyword = f"elif {condition}"
        
        if body.endswith(':'):
            return f"{keyword}:"
        elif body:
            body = _convert_special_syntax(body)
            return f"{keyword}: {body}"
        else:
            return f"{keyword}:"
    
    return None

def _transform_return(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les retours: retour expression
    """
    m = re.fullmatch(r'\s*retour\s+(.+)', line)
    if m:
        expr = m.group(1)
        expr = _convert_special_syntax(expr)
        return f"return {expr}"
    
    # Yield
    m_yield = re.fullmatch(r'\s*yield\s+(.+)', line)
    if m_yield:
        expr = m_yield.group(1)
        expr = _convert_special_syntax(expr)
        return f"yield {expr}"
    
    return None

def _transform_class(line: str, line_no: int) -> Optional[str]:
    """
    Transforme les définitions de classe: class Name => ou class Name(Parent) =>
    """
    m = re.fullmatch(r'\s*class\s+([A-Za-z_][\w]*)(?:\s*\(\s*([^)]+)\s*\))?\s*=>\s*(.*)', line)
    if m:
        name, parents, body = m.groups()
        body = body.strip()
        
        if parents:
            class_def = f"class {name}({parents}):"
        else:
            class_def = f"class {name}:"
        
        if body.endswith(':'):
            return class_def
        elif body:
            body = _convert_special_syntax(body)
            return f"{class_def}\n    {body}"
        else:
            return class_def
    
    return None

# Liste des transformateurs dans l'ordre de priorité
TRANSFORMERS = [
    _transform_import,
    _transform_function,
    _transform_class,
    _transform_control_flow,
    _transform_return,
    _transform_list_append,
    _transform_print,
    _transform_access,
    _transform_assignment,
]

# ============================================================================
# FONCTION PRINCIPALE DE TRANSPILATION
# ============================================================================

def transpile_string(zv_code: str) -> str:
    """
    Transpile du code Zenv en code Python
    
    Args:
        zv_code: Code source Zenv
        
    Returns:
        Code Python transpilé
        
    Raises:
        ZvSyntaxError: Si une erreur de syntaxe est détectée
    """
    py_lines = []
    lines = zv_code.splitlines()
    
    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        
        # Ignorer les lignes vides et les commentaires
        if _is_blank_or_comment(line):
            py_lines.append(line)
            continue
        
        # Essayer chaque transformateur
        transformed = None
        for transformer in TRANSFORMERS:
            try:
                transformed = transformer(line, i)
                if transformed is not None:
                    break
            except ZvSyntaxError:
                raise
            except Exception as e:
                # Si un transformateur échoue, continuer avec le suivant
                continue
        
        # Si aucun transformateur n'a fonctionné
        if transformed is None:
            # Vérifier si c'est une ligne qui ressemble à du Python
            # (pour permettre du code Python natif dans les fichiers .zv)
            stripped = line.strip()
            
            # Lignes qui pourraient être du Python pur
            python_keywords = ['import ', 'from ', 'def ', 'class ', 'if ', 
                             'for ', 'while ', 'try:', 'except:', 'finally:',
                             'with ', 'async ', 'await ', 'return ', 'yield ',
                             'raise ', 'assert ', 'pass ', 'break ', 'continue ']
            
            if any(stripped.startswith(kw) for kw in python_keywords):
                # C'est probablement du Python natif, le garder tel quel
                py_lines.append(line)
            else:
                # Syntaxe inconnue
                raise _brand_error("Unknown or invalid statement", i, line)
        else:
            py_lines.append(transformed)
    
    return "\n".join(py_lines) + ("\n" if py_lines else "")

def transpile_file(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Transpile un fichier Zenv en fichier Python
    
    Args:
        input_path: Chemin vers le fichier .zv
        output_path: Chemin vers le fichier .py de sortie (optionnel)
        
    Returns:
        Code Python transpilé
        
    Raises:
        ZvSyntaxError: Si une erreur de syntaxe est détectée
        FileNotFoundError: Si le fichier d'entrée n'existe pas
        IOError: Pour d'autres erreurs d'E/S
    """
    # Vérifier que le fichier existe
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Lire le fichier
    with open(input_path, 'r', encoding='utf-8') as f:
        zv_code = f.read()
    
    # Transpiler
    py_code = transpile_string(zv_code)
    
    # Écrire le fichier de sortie si demandé
    if output_path:
        # Créer les répertoires parents si nécessaire
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(py_code)
    
    return py_code

def transpile_directory(input_dir: str, output_dir: Optional[str] = None, 
                       recursive: bool = False) -> Dict[str, Any]:
    """
    Transpile tous les fichiers .zv d'un répertoire
    
    Args:
        input_dir: Répertoire source
        output_dir: Répertoire de sortie (optionnel)
        recursive: Traiter les sous-répertoires récursivement
        
    Returns:
        Dictionnaire avec les résultats
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {input_dir}")
    
    # Déterminer le répertoire de sortie
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = input_path / "transpiled"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Trouver les fichiers .zv
    pattern = "**/*.zv" if recursive else "*.zv"
    zv_files = list(input_path.glob(pattern))
    
    results = {
        "success": True,
        "total_files": len(zv_files),
        "transpiled": 0,
        "errors": 0,
        "error_messages": []
    }
    
    for zv_file in zv_files:
        try:
            # Déterminer le chemin de sortie
            if output_dir:
                rel_path = zv_file.relative_to(input_path)
                py_file = output_path / rel_path.with_suffix('.py')
                py_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                py_file = zv_file.with_suffix('.py')
            
            # Transpiler
            transpile_file(str(zv_file), str(py_file))
            results["transpiled"] += 1
            
        except Exception as e:
            results["errors"] += 1
            results["success"] = False
            results["error_messages"].append(f"{zv_file}: {str(e)}")
    
    return results

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def validate_zv_code(zv_code: str) -> Tuple[bool, Optional[str]]:
    """
    Valide du code Zenv sans le transpiler
    
    Args:
        zv_code: Code Zenv à valider
        
    Returns:
        Tuple (is_valid, error_message)
    """
    try:
        transpile_string(zv_code)
        return True, None
    except ZvSyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def get_zv_version() -> str:
    """Retourne la version du transpileur"""
    return "1.2.0"

def get_supported_features() -> List[str]:
    """Retourne la liste des fonctionnalités supportées"""
    return [
        "import statements",
        "variable assignments",
        "list operations (append, extend)",
        "print statements",
        "function definitions",
        "class definitions",
        "control flow (if, for, while)",
        "return and yield",
        "list and dict literals",
        "f-string interpolation",
        "logical operators",
        "ternary operator"
    ]

# ============================================================================
# POINT D'ENTRÉE POUR LES TESTS
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.zv> [output.py]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = transpile_file(input_file, output_file)
        if not output_file:
            print(result)
        else:
            print(f"Successfully transpiled to {output_file}")
    except ZvSyntaxError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"{BRAND} Error: {str(e)}", file=sys.stderr)
        sys.exit(3)
