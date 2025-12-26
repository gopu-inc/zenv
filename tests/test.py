"""
Tests pour le CLI Zenv
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

# Configurer les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from zenv_transpiler.cli import main
    from zenv_transpiler.transpiler import transpile_string
except ImportError:
    # Fallback pour imports
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cli",
        os.path.join(os.path.dirname(__file__), "..", "zenv_transpiler", "cli.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    main = module.main


class TestCLIBasic:
    """Tests de base du CLI"""
    
    def test_cli_help(self, capsys):
        """Test de l'aide du CLI"""
        try:
            sys.argv = ["zenv", "--help"]
            main()
            captured = capsys.readouterr()
            assert "usage:" in captured.out.lower() or "help" in captured.out.lower()
        except SystemExit:
            # --help provoque normalement SystemExit
            captured = capsys.readouterr()
            assert "usage:" in captured.out.lower() or "help" in captured.out.lower()
    
    def test_cli_version(self, capsys):
        """Test de la version"""
        try:
            sys.argv = ["zenv", "--version"]
            main()
            captured = capsys.readouterr()
            assert "zenv" in captured.out.lower() or "version" in captured.out.lower()
        except SystemExit:
            captured = capsys.readouterr()
            assert "zenv" in captured.out.lower() or "version" in captured.out.lower()
    
    def test_cli_missing_file(self, capsys):
        """Test avec fichier manquant"""
        try:
            sys.argv = ["zenv", "nonexistent.zv"]
            main()
        except SystemExit as e:
            # Devrait sortir avec code d'erreur
            assert e.code != 0
    
    def test_cli_success(self, tmp_path):
        """Test CLI réussi"""
        # Créer un fichier test
        test_file = tmp_path / "test.zv"
        test_file.write_text("x ==> 42\nzncv.[(x)]")
        
        # Créer un fichier de sortie
        output_file = tmp_path / "output.py"
        
        # Exécuter le CLI
        sys.argv = ["zenv", str(test_file), "-o", str(output_file)]
        
        try:
            main()
            # Vérifier que le fichier de sortie existe
            assert output_file.exists()
            content = output_file.read_text()
            assert "x = 42" in content
            assert "print(x)" in content or "print(42)" in content
        except SystemExit as e:
            if e.code != 0:
                raise AssertionError(f"CLI failed with exit code {e.code}")


class TestCLIAdvanced:
    """Tests avancés du CLI"""
    
    def test_cli_stdout(self, capsys, tmp_path):
        """Test de sortie stdout"""
        test_file = tmp_path / "test.zv"
        test_file.write_text("zncv.[('test')]")
        
        sys.argv = ["zenv", str(test_file)]
        
        try:
            main()
            captured = capsys.readouterr()
            assert "print" in captured.out
        except SystemExit as e:
            if e.code == 0:
                captured = capsys.readouterr()
                assert "print" in captured.out
    
    def test_cli_run(self, tmp_path):
        """Test d'exécution"""
        test_file = tmp_path / "test.zv"
        test_file.write_text("zncv.[('Hello from Zenv')]")
        
        sys.argv = ["zenv", str(test_file), "--run"]
        
        try:
            main()
            # Si nous arrivons ici, c'est que l'exécution a réussi
            assert True
        except SystemExit as e:
            # Vérifier que ce n'est pas une erreur
            if e.code != 0:
                import traceback
                traceback.print_exc()
                raise AssertionError(f"Run failed with code {e.code}")


def test_integration_transpile_and_execute(tmp_path):
    """Test d'intégration: transpiler et exécuter"""
    # Code Zenv simple
    zv_code = """# Programme de test
a ==> 10
b ==> 20
zncv.[(a + b)]"""
    
    # Écrire dans un fichier
    zv_file = tmp_path / "program.zv"
    zv_file.write_text(zv_code)
    
    # Fichier Python de sortie
    py_file = tmp_path / "program.py"
    
    # Transpiler
    try:
        from zenv_transpiler.transpiler import transpile_file
        transpile_file(str(zv_file), str(py_file))
    except ImportError:
        # Fallback: utiliser le CLI
        subprocess.run(
            [sys.executable, "-m", "zenv_transpiler.cli", str(zv_file), "-o", str(py_file)],
            check=True
        )
    
    # Vérifier le fichier généré
    assert py_file.exists()
    py_content = py_file.read_text()
    assert "a = 10" in py_content
    assert "b = 20" in py_content
    
    # Exécuter le Python généré
    result = subprocess.run(
        [sys.executable, str(py_file)],
        capture_output=True,
        text=True
    )
    
    # Vérifier la sortie
    assert result.returncode == 0
    assert "30" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])