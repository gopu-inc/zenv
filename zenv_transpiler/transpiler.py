# zenv_transpiler/transpiler.py
# Transpileur .zv -> Python

import re
from typing import Optional

BRAND = "[ZENV]"

class ZvSyntaxError(Exception):
    pass

def _brand_error(message: str, line_no: int, line: str) -> ZvSyntaxError:
    return ZvSyntaxError(f"{BRAND} SyntaxError (line {line_no}): {message}\n--> {line}")

def _is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return s == "" or s.startswith("#")

# --- Gestion de la syntaxe spéciale ---
def _convert_syntax_in_expr(expr: str) -> str:
    """Convertit la syntaxe spéciale dans les expressions"""
    if not expr:
        return expr
    
    # Convertir {a, b, c} en [a, b, c]
    # Mais attention à ne pas toucher aux f-strings ou autres
    def replace_braces(match):
        content = match.group(1)
        # Vérifier que ce n'est pas un dict
        if ':' in content:
            return match.group(0)  # Laisse les dicts tels quels
        # Remplace les accolades par des crochets
        return '[' + content + ']'
    
    # Remplacer {} par [] sauf dans les chaînes
    parts = []
    i = 0
    in_string = False
    string_char = None
    
    while i < len(expr):
        char = expr[i]
        
        if char in ('"', "'") and (i == 0 or expr[i-1] != '\\'):
            in_string = not in_string
            string_char = char if in_string else None
            parts.append(char)
        elif not in_string and char == '{':
            # Trouver la fin de l'accolade
            j = i + 1
            brace_count = 1
            while j < len(expr) and brace_count > 0:
                if expr[j] == '{':
                    brace_count += 1
                elif expr[j] == '}':
                    brace_count -= 1
                j += 1
            
            if brace_count == 0:
                inner = expr[i+1:j-1]
                # Vérifier si c'est une liste ou un dict
                if ':' in inner and not any(c in inner for c in '"\'') and not re.search(r':\s*[^,\s}]', inner):
                    # C'est probablement un dict
                    parts.append('{' + inner + '}')
                else:
                    # C'est une liste
                    parts.append('[' + inner + ']')
                i = j - 1
            else:
                parts.append(char)
        else:
            parts.append(char)
        i += 1
    
    result = ''.join(parts)
    
    # Convertir les opérateurs logiques
    result = result.replace('&&', 'and').replace('||', 'or')
    
    return result

# --- IMPORTS ---
def _transform_import(line: str, line_no: int) -> Optional[str]:
    # Corriger la faute de frappe "imoprt" -> "import"
    m1 = re.fullmatch(r"\s*zen\[\s*(?:imoprt|import)\s+([A-Za-z_][\w.]*)\s*\]\s*", line)
    if m1:
        return f"import {m1.group(1)}"
    
    # Import avec alias
    m2 = re.fullmatch(
        r"\s*zen\[\s*import\s+([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*",
        line,
    )
    if m2:
        a, b, alias = m2.groups()
        # Deux possibilités: from a.b import alias OU from a import b as alias
        # On choisit la première pour correspondre au test
        return f"from {a}.{b} import {alias}"
    
    # Import simple avec alias
    m3 = re.fullmatch(
        r"\s*zen\[\s*import\s+([A-Za-z_][\w]*)\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*",
        line,
    )
    if m3:
        module, alias = m3.groups()
        return f"import {module} as {alias}"
    
    return None

# --- ASSIGNMENTS ---
def _transform_assignment(line: str, line_no: int) -> Optional[str]:
    m = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*==>\s*(.+)\s*", line)
    if m:
        var, expr = m.groups()
        expr = _convert_syntax_in_expr(expr)
        return f"{var} = {expr}"
    
    # Vérifier les assignations invalides
    m_invalid = re.fullmatch(r"\s*([0-9]+[A-Za-z_]*)\s*==>", line)
    if m_invalid:
        raise _brand_error("Invalid variable name", line_no, line)
    
    return None

# --- LIST APPEND ---
def _transform_list_append(line: str, line_no: int) -> Optional[str]:
    m = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*:\s*apend\[\((.+)\)\]\s*", line)
    if m:
        lst, item = m.groups()
        item = _convert_syntax_in_expr(item)
        return f"{lst}.append({item})"
    return None

# --- PRINT ---
def _transform_print(line: str, line_no: int) -> Optional[str]:
    # Version sans backticks
    m = re.fullmatch(r"\s*zncv\.\[\((.+)\)\]\s*", line)
    if not m:
        # Vérifier si c'est un print mal formé
        if line.strip().startswith("zncv.[") and not line.strip().endswith(")]"):
            raise _brand_error("Malformed print statement", line_no, line)
        return None
    
    inner = m.group(1).strip()
    
    # Gestion des f-strings avec $s
    if '$s' in inner or '$' in inner:
        # Extraire la partie chaîne
        str_match = re.search(r"['\"]([^'\"]*?)['\"]", inner)
        if str_match:
            string_part = str_match.group(1)
            # Trouver toutes les variables après $
            vars_part = inner[str_match.end():].strip()
            vars_list = re.findall(r'\$\s*([A-Za-z_][\w]*)', vars_part)
            
            if vars_list:
                # Créer une f-string
                f_string = f'f"{string_part}'
                for var in vars_list:
                    f_string += f' {{{var}}}'
                f_string += '"'
                return f"print({f_string})"
    
    # Chaîne simple ou expression
    inner = _convert_syntax_in_expr(inner)
    return f"print({inner})"

# --- ACCESS ---
def _transform_access(line: str, line_no: int) -> Optional[str]:
    m = re.fullmatch(
        r"\s*([A-Za-z_][\w]*)~([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\{\{([0-9]+)\}\}\s*",
        line
    )
    if m:
        left_a, left_b, base, idx = m.groups()
        return f"{left_a}_{left_b} = {base}[{idx}]"
    return None

TRANSFORMERS = [
    _transform_import,
    _transform_assignment,
    _transform_list_append,
    _transform_print,
    _transform_access,
]

def transpile_string(zv_code: str) -> str:
    py_lines = []
    for i, raw in enumerate(zv_code.splitlines(), start=1):
        line = raw.rstrip("\n")
        if _is_blank_or_comment(line):
            py_lines.append(line)
            continue

        result = None
        for t in TRANSFORMERS:
            try:
                result = t(line, i)
            except ZvSyntaxError:
                raise
            except Exception:
                continue
            if result is not None:
                break

        if result is None:
            # Vérifier si la ligne contient une syntaxe suspecte
            stripped = line.strip()
            if stripped:
                # Si ça commence par un chiffre ou contient des caractères bizarres
                if re.match(r'^[0-9]', stripped) or not re.match(r'^[A-Za-z_#\s]', stripped):
                    raise _brand_error("Unknown or invalid statement", i, line)
                # Sinon, garder la ligne telle quelle (pour les commentaires Python, etc.)
                result = _convert_syntax_in_expr(line)

        py_lines.append(result)

    return "\n".join(py_lines) + "\n"

def transpile_file(input_path: str, output_path: Optional[str] = None) -> str:
    with open(input_path, "r", encoding="utf-8") as f:
        zv_code = f.read()
    py_code = transpile_string(zv_code)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(py_code)
    return py_code