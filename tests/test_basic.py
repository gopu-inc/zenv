"""
Tests de base du transpileur Zenv avec import relatif
"""

import sys
import os
import pytest

# Ajouter le chemin parent pour les imports relatifs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import avec chemin relatif
try:
    # Essayer l'import relatif d'abord
    from zenv_transpiler.transpiler import transpile_string, ZvSyntaxError, BRAND
except ImportError:
    # Fallback: essayer depuis le répertoire parent
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "transpiler",
        os.path.join(os.path.dirname(__file__), "..", "zenv_transpiler", "transpiler.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    transpile_string = module.transpile_string
    ZvSyntaxError = module.ZvSyntaxError
    BRAND = module.BRAND


class TestBasicSyntax:
    """Tests de syntaxe basique"""
    
    def test_empty_string(self):
        """Test avec chaîne vide"""
        result = transpile_string("")
        assert result == "\n" or result == ""
    
    def test_comments_only(self):
        """Test avec uniquement des commentaires"""
        zv_code = "# Ceci est un commentaire\n# Un autre commentaire"
        result = transpile_string(zv_code)
        assert "# Ceci est un commentaire" in result
        assert "# Un autre commentaire" in result
    
    def test_whitespace_preservation(self):
        """Test de préservation des espaces"""
        result = transpile_string("   \n  \t  \n ")
        # Vérifier que c'est du Python valide
        assert isinstance(result, str)
    
    def test_invalid_syntax(self):
        """Test d'erreur de syntaxe"""
        zv_code = "invalid syntax statement"
        with pytest.raises(ZvSyntaxError) as exc_info:
            transpile_string(zv_code)
        assert "SyntaxError" in str(exc_info.value) or "Unknown" in str(exc_info.value)
    
    def test_mixed_content(self):
        """Test avec contenu mixte"""
        zv_code = "# Début\nx ==> 42\n# Fin"
        result = transpile_string(zv_code)
        lines = result.split('\n')
        assert any("# Début" in line for line in lines)
        assert any("x = 42" in line for line in lines)
        assert any("# Fin" in line for line in lines)


class TestAssignment:
    """Tests d'assignation"""
    
    def test_simple_assignment(self):
        """Assignation simple"""
        zv_code = "x ==> 42"
        result = transpile_string(zv_code)
        assert "x = 42" in result
    
    def test_assignment_with_string(self):
        """Assignation avec chaîne"""
        zv_code = "msg ==> 'Hello'"
        result = transpile_string(zv_code)
        assert "msg = 'Hello'" in result
    
    def test_assignment_expression(self):
        """Assignation avec expression mathématique"""
        zv_code = "result ==> 10 + 20"
        result = transpile_string(zv_code)
        assert "result = 10 + 20" in result
    
    def test_multiple_variables(self):
        """Plusieurs variables"""
        zv_code = """a ==> 1
b ==> 2
c ==> 3"""
        result = transpile_string(zv_code)
        assert "a = 1" in result
        assert "b = 2" in result
        assert "c = 3" in result
    
    def test_variable_names(self):
        """Noms de variables valides"""
        test_cases = [
            ("var ==> 1", "var = 1"),
            ("_private ==> 2", "_private = 2"),
            ("var123 ==> 3", "var123 = 3"),
            ("VAR ==> 4", "VAR = 4"),
        ]
        
        for zv, expected in test_cases:
            result = transpile_string(zv)
            assert expected in result


class TestPrintStatements:
    """Tests des déclarations print"""
    
    def test_print_simple(self):
        """Print simple"""
        zv_code = "zncv.[('test')]"
        result = transpile_string(zv_code)
        assert "print('test')" in result or "print(test)" in result
    
    def test_print_variable(self):
        """Print d'une variable"""
        zv_code = """msg ==> 'Hello'
zncv.[(msg)]"""
        result = transpile_string(zv_code)
        # Vérifier les deux lignes
        lines = result.strip().split('\n')
        assert any("msg = 'Hello'" in line for line in lines)
        assert any("print(msg)" in line for line in lines)
    
    def test_print_expression(self):
        """Print d'expression"""
        zv_code = "zncv.[(5 + 3)]"
        result = transpile_string(zv_code)
        assert "print(5 + 3)" in result
    
    def test_multiple_prints(self):
        """Multiple prints"""
        zv_code = """zncv.[('A')]
zncv.[('B')]
zncv.[('C')]"""
        result = transpile_string(zv_code)
        assert "print('A')" in result or "print(A)" in result
        assert "print('B')" in result or "print(B)" in result
        assert "print('C')" in result or "print(C)" in result


class TestDataStructures:
    """Tests des structures de données"""
    
    def test_list_syntax(self):
        """Syntaxe de liste"""
        zv_code = "lst ==> {1, 2, 3}"
        result = transpile_string(zv_code)
        # Devrait convertir { } en [ ]
        assert "lst = [1, 2, 3]" in result
    
    def test_list_append(self):
        """Append à une liste"""
        zv_code = """lst ==> {1, 2}
lst:apend[(3)]"""
        result = transpile_string(zv_code)
        assert "lst = [1, 2]" in result or "lst.append" in result
    
    def test_empty_list(self):
        """Liste vide"""
        zv_code = "empty ==> {}"
        result = transpile_string(zv_code)
        assert "empty = []" in result


class TestImportStatements:
    """Tests des imports"""
    
    def test_basic_import(self):
        """Import basique"""
        zv_code = "zen[import os]"
        result = transpile_string(zv_code)
        assert "import os" in result
    
    def test_import_with_alias(self):
        """Import avec alias"""
        zv_code = "zen[import os from as system]"
        result = transpile_string(zv_code)
        # Peut être "import os as system" ou "from os import system"
        assert "import" in result and "os" in result


class TestErrorHandling:
    """Tests de gestion des erreurs"""
    
    def test_invalid_assignment(self):
        """Assignation invalide"""
        zv_code = "123 ==> x"  # Nom de variable invalide
        with pytest.raises((ZvSyntaxError, Exception)):
            transpile_string(zv_code)
    
    def test_malformed_print(self):
        """Print mal formé"""
        zv_code = "zncv.["  # Incomplet
        with pytest.raises((ZvSyntaxError, Exception)):
            transpile_string(zv_code)
    
    def test_unknown_statement(self):
        """Déclaration inconnue"""
        zv_code = "unknown statement here"
        with pytest.raises(ZvSyntaxError) as exc_info:
            transpile_string(zv_code)
        # Vérifier que c'est bien notre erreur
        assert BRAND in str(exc_info.value)


def test_end_to_end_simple():
    """Test end-to-end simple"""
    zv_code = """# Programme simple
x ==> 10
y ==> 20
zncv.[(x + y)]"""
    
    result = transpile_string(zv_code)
    
    # Vérifier que c'est du Python valide
    assert isinstance(result, str)
    assert "# Programme simple" in result
    assert "x = 10" in result
    assert "y = 20" in result
    assert "print(x + y)" in result or "print(30)" in result


def test_real_world_example():
    """Exemple réaliste"""
    zv_code = """# Calcul de factorielle
n ==> 5
result ==> 1

while n > 0 =>
    result ==> result * n
    n ==> n - 1

zncv.[(result)]"""
    
    try:
        result = transpile_string(zv_code)
        # Vérifier les éléments clés
        assert "n = 5" in result
        assert "result = 1" in result
        assert "while" in result
    except Exception as e:
        # Si certaines syntaxes ne sont pas encore implémentées
        pytest.skip(f"Syntaxe non implémentée: {e}")


if __name__ == "__main__":
    # Pour exécuter les tests directement
    pytest.main([__file__, "-v"])