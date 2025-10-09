#!/usr/bin/env python3
"""
Script de vérification de préparation pour PyPI

Effectue des vérifications avancées avant publication sur PyPI.
"""

import re
import subprocess
import sys
from pathlib import Path


class PyPIChecker:
    """Vérificateur de préparation PyPI"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.root = Path(__file__).parent.parent

    def check(self, description: str) -> None:
        """Affiche le message de vérification"""
        print(f"  {description}...", end=" ")

    def pass_check(self, message: str = "") -> None:
        """Marque une vérification comme réussie"""
        print("✓ PASS")
        if message:
            print(f"    {message}")
        self.passed += 1

    def fail_check(self, message: str) -> None:
        """Marque une vérification comme échouée"""
        print("✗ FAIL")
        print(f"    Erreur: {message}")
        self.failed += 1

    def warn_check(self, message: str) -> None:
        """Marque une vérification comme avertissement"""
        print("⚠ WARNING")
        print(f"    Avertissement: {message}")
        self.warnings += 1

    def run_command(self, cmd: list, check: bool = False) -> tuple:
        """Exécute une commande et retourne (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.root, check=check
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr

    def check_version_consistency(self) -> None:
        """Vérifie la cohérence de la version entre différents fichiers"""
        print("\n📋 Vérification cohérence version")
        print("=" * 50)

        # Lire version depuis __init__.py
        self.check("Version dans geneweb_py/__init__.py")
        init_file = self.root / "src" / "geneweb_py" / "__init__.py"
        try:
            with open(init_file) as f:
                content = f.read()
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version_init = match.group(1)
                    self.pass_check(f"Version: {version_init}")
                else:
                    self.fail_check("Version non trouvée dans __init__.py")
                    return
        except FileNotFoundError:
            self.fail_check("Fichier __init__.py non trouvé")
            return

        # Lire version depuis pyproject.toml
        self.check("Version dans pyproject.toml")
        pyproject = self.root / "pyproject.toml"
        try:
            with open(pyproject) as f:
                content = f.read()
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version_toml = match.group(1)
                    if version_toml == version_init:
                        self.pass_check(f"Version: {version_toml} (cohérente)")
                    else:
                        self.fail_check(
                            f"Incohérence: pyproject.toml={version_toml}, "
                            f"__init__.py={version_init}"
                        )
                else:
                    self.fail_check("Version non trouvée dans pyproject.toml")
        except FileNotFoundError:
            self.fail_check("Fichier pyproject.toml non trouvé")

    def check_required_files(self) -> None:
        """Vérifie la présence des fichiers requis"""
        print("\n📁 Vérification fichiers requis")
        print("=" * 50)

        required = {
            "README.md": "Documentation utilisateur",
            "LICENSE": "Licence du projet",
            "pyproject.toml": "Configuration package",
            "CHANGELOG.md": "Historique changements",
        }

        for filename, description in required.items():
            self.check(f"{filename} ({description})")
            filepath = self.root / filename
            if filepath.exists():
                # Vérifier taille minimale
                size = filepath.stat().st_size
                if size > 100:  # Au moins 100 bytes
                    self.pass_check(f"{size} bytes")
                else:
                    self.warn_check(f"Fichier trop petit ({size} bytes)")
            else:
                if filename == "CHANGELOG.md":
                    self.warn_check("Fichier manquant (recommandé)")
                else:
                    self.fail_check("Fichier manquant")

    def check_pyproject_toml(self) -> None:
        """Vérifie la configuration pyproject.toml"""
        print("\n⚙️  Vérification pyproject.toml")
        print("=" * 50)

        pyproject = self.root / "pyproject.toml"
        with open(pyproject) as f:
            content = f.read()

        required_fields = {
            "name": r'name\s*=\s*["\']geneweb-py["\']',
            "version": r'version\s*=\s*["\'][^"\']+["\']',
            "description": r'description\s*=\s*["\'].+["\']',
            "license": r"license\s*=\s*\{[^}]*\}",
            "authors": r"authors\s*=\s*\[",
            "requires-python": r'requires-python\s*=\s*["\']>=\d+\.\d+["\']',
            "dependencies": r"dependencies\s*=\s*\[",
        }

        for field, pattern in required_fields.items():
            self.check(f"Champ '{field}'")
            if re.search(pattern, content):
                self.pass_check()
            else:
                self.fail_check("Champ manquant ou mal formaté")

    def check_package_structure(self) -> None:
        """Vérifie la structure du package"""
        print("\n📦 Vérification structure package")
        print("=" * 50)

        package_dir = self.root / "src" / "geneweb_py"

        self.check("Dossier src/geneweb_py/")
        if package_dir.exists() and package_dir.is_dir():
            self.pass_check()
        else:
            self.fail_check("Dossier package manquant")
            return

        # Vérifier __init__.py
        self.check("geneweb_py/__init__.py")
        init_file = package_dir / "__init__.py"
        if init_file.exists():
            with open(init_file) as f:
                content = f.read()
                # Doit exposer les imports principaux
                if "GeneWebParser" in content or "from" in content:
                    self.pass_check()
                else:
                    self.warn_check("Pas d'imports publics dans __init__.py")
        else:
            self.fail_check("__init__.py manquant")

        # Vérifier sous-modules
        expected_modules = ["core", "formats", "api"]
        for module in expected_modules:
            self.check(f"Module {module}/")
            module_dir = package_dir / module
            if module_dir.exists() and (module_dir / "__init__.py").exists():
                self.pass_check()
            else:
                self.warn_check(f"Module {module}/ manquant ou incomplet")

    def check_tests(self) -> None:
        """Vérifie la présence et qualité des tests"""
        print("\n🧪 Vérification tests")
        print("=" * 50)

        tests_dir = self.root / "tests"

        self.check("Dossier tests/")
        if tests_dir.exists():
            self.pass_check()
        else:
            self.fail_check("Dossier tests/ manquant")
            return

        # Compter les fichiers de test
        test_files = list(tests_dir.rglob("test_*.py"))
        self.check(f"Fichiers de test ({len(test_files)} trouvés)")
        if len(test_files) > 50:
            self.pass_check(f"{len(test_files)} fichiers de test")
        elif len(test_files) > 20:
            self.warn_check(f"Seulement {len(test_files)} fichiers de test")
        else:
            self.fail_check(f"Trop peu de tests ({len(test_files)})")

        # Vérifier tests de packaging
        self.check("Tests de packaging (tests/packaging/)")
        if (tests_dir / "packaging").exists():
            self.pass_check()
        else:
            self.warn_check("Tests de packaging manquants")

    def check_dependencies(self) -> None:
        """Vérifie les dépendances"""
        print("\n📚 Vérification dépendances")
        print("=" * 50)

        pyproject = self.root / "pyproject.toml"
        with open(pyproject) as f:
            content = f.read()

        # Compter les dépendances obligatoires
        self.check("Nombre de dépendances obligatoires")
        deps_match = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if deps_match:
            deps_content = deps_match.group(1)
            deps = [
                line.strip()
                for line in deps_content.split("\n")
                if line.strip() and line.strip().startswith('"')
            ]
            dep_count = len(deps)

            if dep_count <= 5:
                self.pass_check(f"{dep_count} dépendances (minimal)")
            elif dep_count <= 10:
                self.warn_check(f"{dep_count} dépendances (acceptable)")
            else:
                self.fail_check(f"Trop de dépendances ({dep_count})")
        else:
            self.fail_check("Section dependencies non trouvée")

        # Vérifier versions épinglées
        self.check("Versions des dépendances épinglées")
        if deps_match:
            unversioned = [dep for dep in deps if ">=" not in dep and "==" not in dep]
            if not unversioned:
                self.pass_check("Toutes les dépendances ont des versions")
            else:
                self.warn_check(f"{len(unversioned)} dépendances sans version")

    def check_documentation(self) -> None:
        """Vérifie la documentation"""
        print("\n📖 Vérification documentation")
        print("=" * 50)

        # README
        self.check("README.md complet")
        readme = self.root / "README.md"
        if readme.exists():
            with open(readme) as f:
                content = f.read()

            required_sections = [
                "Installation",
                "Usage",
                "Features",
            ]

            missing = [s for s in required_sections if s.lower() not in content.lower()]

            if not missing:
                self.pass_check("Toutes les sections présentes")
            else:
                self.warn_check(f"Sections manquantes: {', '.join(missing)}")
        else:
            self.fail_check("README.md manquant")

        # Docstrings
        self.check("Docstrings sur classes publiques")
        code = """
import sys
sys.path.insert(0, 'src')
from geneweb_py import GeneWebParser, Genealogy, Person, Family, Date

classes = [GeneWebParser, Genealogy, Person, Family, Date]
missing = [c.__name__ for c in classes if not c.__doc__]

if missing:
    print(f"MISSING:{','.join(missing)}")
    sys.exit(1)
else:
    print("OK")
"""
        returncode, stdout, stderr = self.run_command([sys.executable, "-c", code])
        if returncode == 0:
            self.pass_check()
        else:
            if "MISSING:" in stdout:
                classes = stdout.split("MISSING:")[1].strip()
                self.warn_check(f"Docstrings manquantes: {classes}")
            else:
                self.fail_check("Erreur lors de la vérification")

    def print_summary(self) -> int:
        """Affiche le résumé et retourne le code de sortie"""
        print("\n" + "=" * 50)
        print("  RÉSUMÉ FINAL")
        print("=" * 50)
        print(f"  ✓ Tests réussis:     {self.passed}")
        print(f"  ⚠ Avertissements:    {self.warnings}")
        print(f"  ✗ Tests échoués:     {self.failed}")
        print()

        if self.failed == 0:
            if self.warnings == 0:
                print("✅ PRÊT POUR PUBLICATION PYPI!")
                return 0
            else:
                print("⚠️  PRÊT AVEC AVERTISSEMENTS")
                print("Recommandation: Corriger les avertissements")
                return 0
        else:
            print("❌ PAS PRÊT POUR PUBLICATION")
            print("Corriger les erreurs avant de publier")
            return 1

    def run(self) -> int:
        """Exécute toutes les vérifications"""
        print("\n" + "=" * 50)
        print("  Vérification préparation PyPI")
        print("  geneweb-py")
        print("=" * 50)

        self.check_version_consistency()
        self.check_required_files()
        self.check_pyproject_toml()
        self.check_package_structure()
        self.check_tests()
        self.check_dependencies()
        self.check_documentation()

        return self.print_summary()


if __name__ == "__main__":
    checker = PyPIChecker()
    sys.exit(checker.run())
