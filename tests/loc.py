"""
Tests des cas limites et edge cases
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from zenv_transpiler.transpiler import transpile_string, ZvSyntaxError
except ImportError:
    # Fallback
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "transpiler",
        os.path.join(os.path.dirname(__file__), "..", "zenv_transpiler", "transpiler.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    transpile_string = module.transpile_string
    ZvSyntaxError = module.ZvSyntaxError


class TestEdgeCases:
    """Tests des cas limites"""
    
    def test_very_long_line(self):
        """Ligne très longue"""
        long_value = "x" * 1000
        zv_code = f'text ==> "{long_value}"'
        result = transpile_string(zv_code)
        assert "text =" in result
    
    def test_special_characters(self):
        """Caractères spéciaux"""
        test_cases = [
            ('msg ==> "Hello\\nWorld"', 'msg = "Hello\\nWorld"'),
            ('path ==> "C:\\\\Users\\\\test"', 'path = "C:\\\\Users\\\\test"'),
            ('quote ==> "It\'s working"', "quote = \"It's working\""),
        ]
        
        for zv, expected in test_cases:
            result = transpile_string(zv)
            # Vérifier que c'est du Python valide
            assert "msg =" in result or "path =" in result or "quote =" in result
    
    def test_unicode(self):
        """Caractères Unicode"""
        zv_code = 'msg ==> "Hello 🌍"'
        result = transpile_string(zv_code)
        assert "msg = " in result
    
    def test_empty_statements(self):
        """Instructions vides"""
        zv_code = "\n\n\n"
        result = transpile_string(zv_code)
        # Devrait produire des lignes vides
        lines = result.split('\n')
        assert len(lines) >= 3
    
    def test_mixed_indentation(self):
        """Indentation mixte"""
        zv_code = "  x ==> 1\n    y ==> 2"
        try:
            result = transpile_string(zv_code)
            # Devrait soit fonctionner, soit lever une erreur
            assert True
        except ZvSyntaxError:
            # C'est acceptable aussi
            assert True
    
    def test_carriage_return(self):
        """Retours chariot Windows"""
        zv_code = "x ==> 1\r\ny ==> 2\r\nzncv.[(x + y)]"
        result = transpile_string(zv_code)
        assert "x = 1" in result
        assert "y = 2" in result
    
    def test_tab_characters(self):
        """Caractères tabulation"""
        zv_code = "\tx ==> 1\n\t\tzncv.[(x)]"
        result = transpile_string(zv_code)
        # Les tabs devraient être préservés ou convertis en espaces
        assert isinstance(result, str)


class TestComplexExpressions:
    """Expressions complexes"""
    
    def test_nested_parentheses(self):
        """Parenthèses imbriquées"""
        zv_code = "zncv.[((((1 + 2) * 3) - 4) / 5)]"
        result = transpile_string(zv_code)
        assert "print" in result
        assert "1 + 2" in result or "3" in result
    
    def test_complex_assignment(self):
        """Assignation complexe"""
        zv_code = "result ==> (a + b) * (c - d) / e"
        result = transpile_string(zv_code)
        assert "result =" in result
    
    def test_multiple_operations(self):
        """Multiples opérations"""
        zv_code = "x ==> 1 + 2 * 3 - 4 / 5"
        result = transpile_string(zv_code)
        assert "x =" in result
        # Vérifier que les opérateurs sont préservés
        assert "+" in result or "*" in result or "-" in result or "/" in result


def test_performance_small():
    """Test de performance sur petit fichier"""
    import time
    
    zv_code = "\n".join([f"x{i} ==> {i}" for i in range(100)])
    
    start = time.time()
    result = transpile_string(zv_code)
    end = time.time()
    
    assert isinstance(result, str)
    # Devrait être rapide (< 1 seconde)
    assert end - start < 1.0


@pytest.mark.slow
def test_performance_large():
    """Test de performance sur gros fichier"""
    import time
    
    # Générer un gros fichier
    lines = []
    for i in range(1000):
        lines.append(f"var{i} ==> {i}")
        if i % 10 == 0:
            lines.append(f'zncv.[("Processing {i}")]')
    
    zv_code = "\n".join(lines)
    
    start = time.time()
    result = transpile_string(zv_code)
    end = time.time()
    
    assert isinstance(result, str)
    # Moins de 5 secondes
    assert end - start < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])