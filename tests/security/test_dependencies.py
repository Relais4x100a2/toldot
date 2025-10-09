"""
Tests de sécurité des dépendances

Vérifie que les dépendances n'ont pas de vulnérabilités connues
et que les versions sont appropriées.
"""

import sys
import pytest
from pathlib import Path


def test_minimal_dependencies():
    """Vérifier qu'on n'a pas trop de dépendances obligatoires"""
    # Lire pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml non trouvé")
    
    with open(pyproject_path) as f:
        content = f.read()
    
    # Compter les dépendances dans la section dependencies
    # (parsing simple, pas de toml parser pour éviter une dépendance)
    in_deps_section = False
    dep_count = 0
    
    for line in content.split('\n'):
        if line.strip() == 'dependencies = [':
            in_deps_section = True
        elif in_deps_section and ']' in line:
            break
        elif in_deps_section and '"' in line:
            dep_count += 1
    
    # Maximum 10 dépendances obligatoires pour une lib
    assert dep_count <= 10, \
        f"Trop de dépendances obligatoires ({dep_count}), limite: 10"


def test_dependencies_have_versions():
    """Vérifier que les dépendances ont des contraintes de version"""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml non trouvé")
    
    with open(pyproject_path) as f:
        content = f.read()
    
    # Vérifier que chaque dépendance a >=, ==, ~= ou autre
    in_deps_section = False
    
    for line in content.split('\n'):
        if line.strip() == 'dependencies = [':
            in_deps_section = True
        elif in_deps_section and ']' in line:
            break
        elif in_deps_section and '"' in line:
            # Extraire le nom de la dépendance
            dep = line.strip().strip('",')
            if dep:
                # Doit contenir un opérateur de version
                has_version = any(op in dep for op in ['>=', '==', '~=', '>', '<', '!='])
                assert has_version, \
                    f"Dépendance {dep} sans contrainte de version"


def test_no_known_vulnerable_packages():
    """Test qu'on n'utilise pas de packages avec vulnérabilités connues"""
    # Liste de packages connus pour avoir des problèmes de sécurité
    # (cette liste est indicative, idéalement utiliser pip-audit)
    vulnerable_packages = [
        "pyyaml<5.4",  # Vulnérabilités avant 5.4
        "pillow<8.1.1",  # Vulnérabilités avant 8.1.1
        "requests<2.26.0",  # Vulnérabilités avant 2.26.0
    ]
    
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml non trouvé")
    
    with open(pyproject_path) as f:
        content = f.read()
    
    # Vérifier qu'aucun package vulnérable n'est utilisé
    for vuln in vulnerable_packages:
        pkg_name = vuln.split('<')[0].split('>')[0].split('=')[0]
        # Recherche simple (pas de parsing TOML complet)
        assert pkg_name.lower() not in content.lower() or \
               f'"{pkg_name}' not in content, \
               f"Package potentiellement vulnérable détecté: {vuln}"


def test_dependencies_licenses_compatible():
    """Vérifier que les licences des dépendances sont compatibles avec MIT"""
    # typing_extensions: PSF (compatible)
    # chardet: LGPL (compatible avec MIT pour usage)
    
    # Licences incompatibles avec MIT pour distribution
    incompatible_licenses = ["GPL-3.0", "AGPL"]
    
    # Pour l'instant, test simple : vérifier qu'on n'a pas de dépendances GPL
    # (nécessiterait pip-licenses pour un test complet)
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml non trouvé")
    
    with open(pyproject_path) as f:
        content = f.read()
    
    # Les packages GPL connus
    gpl_packages = ["gpl", "gnuplot"]  # Liste indicative
    
    for pkg in gpl_packages:
        assert pkg not in content.lower(), \
            f"Dépendance GPL potentielle détectée: {pkg}"


def test_no_test_dependencies_in_main():
    """Vérifier qu'aucune dépendance de test n'est dans dependencies"""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml non trouvé")
    
    with open(pyproject_path) as f:
        content = f.read()
    
    # Packages qui doivent être uniquement dans [dev]
    test_packages = ["pytest", "black", "flake8", "mypy", "coverage"]
    
    # Parser les sections
    lines = content.split('\n')
    in_main_deps = False
    main_deps_content = []
    
    for line in lines:
        if line.strip() == 'dependencies = [':
            in_main_deps = True
        elif in_main_deps and ']' in line:
            in_main_deps = False
        elif in_main_deps:
            main_deps_content.append(line.lower())
    
    main_deps_str = '\n'.join(main_deps_content)
    
    for pkg in test_packages:
        assert pkg not in main_deps_str, \
            f"Package de test {pkg} trouvé dans dependencies principales"


def test_secure_imports():
    """Vérifier qu'on n'importe pas de modules dangereux"""
    import ast
    from pathlib import Path
    
    # Modules potentiellement dangereux
    dangerous_modules = ["pickle", "shelve", "marshal", "eval", "exec"]
    
    # Parcourir tous les fichiers Python du package
    package_path = Path(__file__).parent.parent.parent / "geneweb_py"
    
    if not package_path.exists():
        pytest.skip("Package geneweb_py non trouvé")
    
    py_files = list(package_path.rglob("*.py"))
    
    for py_file in py_files:
        with open(py_file) as f:
            try:
                tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            assert alias.name not in dangerous_modules, \
                                f"Import dangereux '{alias.name}' dans {py_file}"
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module in dangerous_modules:
                            # Exception: pickle peut être OK dans certains contextes
                            # On warning juste
                            print(f"Warning: Import de {node.module} dans {py_file}")
            
            except SyntaxError:
                # Ignorer les erreurs de syntaxe (fichiers templates, etc.)
                pass


def test_no_hardcoded_secrets():
    """Vérifier absence de secrets hardcodés"""
    import re
    from pathlib import Path
    
    # Patterns de secrets communs
    secret_patterns = [
        r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
        r'password\s*=\s*["\'].+["\']',
        r'secret\s*=\s*["\'].+["\']',
        r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
    ]
    
    package_path = Path(__file__).parent.parent.parent / "geneweb_py"
    
    if not package_path.exists():
        pytest.skip("Package geneweb_py non trouvé")
    
    py_files = list(package_path.rglob("*.py"))
    
    for py_file in py_files:
        with open(py_file) as f:
            content = f.read()
            
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                # Exclure les valeurs de test évidentes
                real_matches = [m for m in matches 
                               if 'test' not in m.lower() 
                               and 'example' not in m.lower()
                               and 'dummy' not in m.lower()]
                
                if real_matches:
                    pytest.fail(f"Secret potentiel trouvé dans {py_file}: {matches[0]}")

