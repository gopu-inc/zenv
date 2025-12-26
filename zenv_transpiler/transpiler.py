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

# --- IMPORTS ---
def _transform_import(line: str, line_no: int) -> Optional[str]:
    m1 = re.fullmatch(r"\s*zen\[\s*imoprt\s+([A-Za-z_][\w]*)\s*\]\s*", line)
    if m1:
        return f"import {m1.group(1)}"
    m2 = re.fullmatch(
        r"\s*zen\[\s*import\s+([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*",
        line,
    )
    if m2:
        a, b, alias = m2.groups()
        return f"from {a}.{b} import {alias}"
    return None

# --- ASSIGNMENTS ---
def _transform_assignment(line: str, line_no: int) -> Optional[str]:
    m = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*==>\s*(.+)\s*", line)
    if m:
        var, expr = m.groups()
        expr = expr.replace("{", "[").replace("}", "]")
        return f"{var} = {expr}"
    return None

# --- LIST APPEND ---
def _transform_list_append(line: str, line_no: int) -> Optional[str]:
    m = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*:\s*apend\[`\((.+)\)`\]\s*", line)
    if m:
        lst, item = m.groups()
        return f"{lst}.append({item})"
    return None

# --- PRINT ---
def _transform_print(line: str, line_no: int) -> Optional[str]:
    m = re.fullmatch(r"\s*zncv\.\[`\((.+)\)`\]\s*", line)
    if not m:
        return None
    inner = m.group(1).strip()

    # Chaîne simple
    if re.fullmatch(r"'[^']*'", inner) or re.fullmatch(r'"[^"]*"', inner):
        return f"print({inner})"

    # Identifiant
    if re.fullmatch(r"[A-Za-z_][\w]*", inner):
        return f"print({inner})"

    # Parenthèses
    paren = re.fullmatch(r"`\(\s*(.+)\s*\)`", inner)
    if paren:
        return f"print({paren.group(1)})"

    # Interpolation avec $s
    str_match = re.search(r"'([^']*?)\s*\$s'", inner)
    if str_match:
        base = str_match.group(1)
        after = inner[str_match.end():].strip()
        vars_ = re.findall(r"\$\s*([A-Za-z_][\w]*)", after)
        placeholders = " ".join("{" + v + "}" for v in vars_)
        return f'print(f"{base} {placeholders}")'

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
            result = t(line, i)
            if result is not None:
                break

        if result is None:
            raise _brand_error("Unknown or invalid statement", i, line)

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
