import pytest
from zenv_transpiler.transpiler import transpile_string, ZvSyntaxError

def test_simple_print():
    src = "zncv.[('hello word')]"
    py = transpile_string(src)
    assert py.strip() == "print('hello word')"

def test_import_simple():
    src = "zen[imoprt math]"
    py = transpile_string(src)
    assert py.strip() == "import math"

def test_import_from_as():
    src = "zen[import os.path from as path]"
    py = transpile_string(src)
    assert py.strip() == "from os.path import path"

def test_assignment_list():
    src = "numbers ==> [1, 2, 3]"
    py = transpile_string(src)
    assert "numbers = [1, 2, 3]" in py

def test_append_list():
    src = "numbers:apend[(4)]"
    py = transpile_string(src)
    assert "numbers.append(4)" in py

def test_variable_alias():
    src = "second~name = name{{1}}"
    py = transpile_string(src)
    assert "second_name = name[1]" in py

def test_interpolation():
    src = "zncv.[('the second name list is $s' $ second_name)]"
    py = transpile_string(src)
    # Vérifie que ça devient un f-string
    assert 'print(f"the second name list is {second_name}")' in py

def test_invalid_statement():
    src = "this is not valid"
    with pytest.raises(ZvSyntaxError):
        transpile_string(src)
