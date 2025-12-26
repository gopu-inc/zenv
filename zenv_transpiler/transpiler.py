# zenv_transpiler/transpiler.py
# Transpileur .zv -> Python, strict, sans dépendances externes

from __future__ import annotations
import re
from typing import List

BRAND = "[ZENV]"

class ZvSyntaxError(Exception):
    pass

def _brand_error(message: str, line_no: int, line: str) -> ZvSyntaxError:
    return ZvSyntaxError(f"{BRAND} SyntaxError (line {line_no}): {message}\n--> {line}")

def _is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return s == "" or s.startswith("#")

def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _transform_import(line: str, line_no: int) -> str | None:
    m1 = re.fullmatch(r"\s*zen\[\s*imoprt\s+([A-Za-z_][\w]*)\s*\]\s*", line)
    if m1:
        pkg = m1.group(1)
        return f"import {pkg}"
    m2 = re.fullmatch(
        r"\s*zen\[\s*import\s+([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)\s+from\s+as\s+([A-Za-z_][\w]*)\s*\]\s*",
        line,
    )
    if m2:
        a, b, alias = m2.groups()
        return f"from {a}.{b} import {alias}"
    return None

def _transform_assignment(line: str, line_no: int) -> str | None:
    # simple assignment: var ==> expr
    m = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*==>\s*(.+)\s*", line)
    if m:
        var, expr = m.groups()
        expr = _convert_literals(expr)
        return f"{var} = {expr}"
    # narrative form: [ y ==> x {a, x, =+ w} as var].flop.zen
    m2 = re.fullmatch(
        r"\s*\[\s*([A-Za-z_][\w]*)\s*==>\s*([A-Za-z_][\w]*)\s*\{\s*([A-Za-z_][\w]*)\s*,\s*([A-Za-z_][\w]*)\s*,\s*=\+\s*([A-Za-z_][\w]*)\s*\}\s*as\s*([A-Za-z_][\w]*)\s*\]\.flop\.zen\s*",
        line,
    )
    if m2:
        y, x, a, x2, w, var = m2.groups()
        # Brand decision: map to var = x (narrative ignored but preserved in comment)
        return f"{var} = {x}  # {BRAND} [{y} ==> {x} {{{a}, {x2}, =+ {w}}}]"
    return None

def _convert_literals(expr: str) -> str:
    # Replace {} indexers to [] inside identifiers
    expr = re.sub(r"\{\s*([0-9]+)\s*\}", r"[\1]", expr)
    # Basic quote normalization: keep as is
    return expr

def _transform_list_append(line: str, line_no: int) -> str | None:
    m = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*:\s*apend\[`\(\s*(.+?)\s*\)`\]\s*", line)
    if m:
        lst, item = m.groups()
        item = _convert_literals(item)
        return f"{lst}.append({item})"
    return None

def _transform_print(line: str, line_no: int) -> str | None:
    m = re.fullmatch(r"\s*zncv\.\[`\(\s*(.+)\s*\)`\]\s*", line)
    if not m:
        return None
    inner = m.group(1).strip()

    # Interpolation pattern: 'text $s' $ var [$ var2 ...]
    # Convert to f-string: f"text {var} {var2} ..."
    interp = re.fullmatch(r"`\(\s*^\prime(.+?)\s*\$s^\prime\s*\)`\s*\$\s*([A-Za-z_][\w]*(?:\s*\$\s*[A-Za-z_][\w]*)*)\s*", inner)
    if interp:
        # Not used due to extra parens; fallback below
        pass

    # More permissive approach:
    # Find "'...$s'" then sequence of $ identifiers
    str_match = re.search(r"'([^']*?)\s*\$s'", inner)
    if str_match:
        base = str_match.group(1)
        after = inner[str_match.end():].strip()
        vars_ = re.findall(r"\$\s*([A-Za-z_][\w]*)", after)
        if not vars_:
            raise _brand_error("Interpolation expects variables after $", line_no, line)
        placeholders = " ".join("{" + v + "}" for v in vars_)
        return f'print(f"{base} {placeholders}")'

    # If plain string or identifier
    if re.fullmatch(r"'[^']*'", inner) or re.fullmatch(r'"[^"]*"', inner):
        return f"print({inner})"
    if re.fullmatch(r"[A-Za-z_][\w]*", inner):
        return f"print({inner})"

    # If parentheses wrap like (expr)
    paren = re.fullmatch(r"`\(\s*(.+)\s*\)`", inner)
    if paren:
        content = paren.group(1)
        return f"print({content})"

    # Fallback: direct pass-through with index normalization
    return f"print({_convert_literals(inner)})"

def _transform_access(line: str, line_no: int) -> str | None:
    # second~name = name{{1}}  -> second_name = name[1]
    m = re.fullmatch(
        r"\s*([A-Za-z_][\w]*)\s*~\s*([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\s*\{\s*\{\s*([0-9]+)\s*\}\s*\}\s*",
        line
    )
    if m:
        left_a, left_b, base, idx = m.groups()
        left = f"{left_a}_{left_b}"
        return f"{left} = {base}[{idx}]"
    # variant: second~name = name[{1}]
    m2 = re.fullmatch(
        r"\s*([A-Za-z_][\w]*)\s*~\s*([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\s*\{\s*\{\s*?\s*?([0-9]+)\s*\}\s*\}\s*",
        line
    )
    # covered above; return None if no match
    return None

def _transform_general_indexing(line: str) -> str:
    # Replace occurrences of {n} with [n]
    return re.sub(r"\{\s*([0-9]+)\s*\}", r"[\1]", line)

TRANSFORMERS = [
    _transform_import,
    _transform_assignment,
    _transform_list_append,
    _transform_print,
    _transform_access,
]

def transpile_string(zv_code: str) -> str:
    """
    Transpile du code .zv vers Python.
    Préserve les commentaires ('# ...') et normalise les indexeurs {n} -> [n].
    """
    py_lines: List[str] = []
    for i, raw in enumerate(zv_code.splitlines(), start=1):
        line = raw.rstrip("\n")
        if _is_blank_or_comment(line):
            py_lines.append(line)
            continue

        # Try specific transformers
        result = None
        for t in TRANSFORMERS:
            result = t(line, i)
            if result is not None:
                break

        if result is None:
            # If it's a list literal assignment var ==> [ ... ]
            m_list = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*==>\s*(\[\s*.*\s*\])\s*", line)
            if m_list:
                var, lit = m_list.groups()
                result = f"{var} = {lit}"
            else:
                # Normalize indexing and pass through if looks like expression statement
                normalized = _transform_general_indexing(line)
                # Allow "identifier ==> value" covered earlier; otherwise error
                # If nothing matched, raise branded error
                raise _brand_error("Unknown or invalid statement", i, line)

        py_lines.append(result)

    return "\n".join(py_lines) + "\n"

def transpile_file(input_path: str, output_path: str | None = None) -> str:
    with open(input_path, "r", encoding="utf-8") as f:
        zv_code = f.read()
    py_code = transpile_string(zv_code)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(py_code)
    return py_code
