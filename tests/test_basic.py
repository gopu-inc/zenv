import os
from zenv_transpiler import transpile_string

def test_transpile_hello():
    src = "zncv.[('hello word')]"
    out = transpile_string(src)
    assert out.strip() == 'print(\'hello word\')'

def test_lists_and_interpolation():
    src = """
name ==> ['jone', 'leo', 'nat']
number ==> []
number:apend[(1)]
second~name = name{{1}}
zncv.[('the second name list is $s' $ second_name)]
    """.strip()
    py = transpile_string(src)
    assert "name = ['jone', 'leo', 'nat']" in py
    assert "number = []" in py
    assert "number.append(1)" in py
    assert "second_name = name[1]" in py
    assert 'print(f"the second name list is {second_name}")' in py
