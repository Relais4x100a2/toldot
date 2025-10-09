#!/bin/bash
# Script de validation pré-publication PyPI
# Usage: ./scripts/validate_pypi.sh

set -e

echo "=================================================="
echo "  Validation pré-publication PyPI - geneweb-py"
echo "=================================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
PASSED=0
FAILED=0
WARNINGS=0

check() {
    echo -n "$1... "
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Erreur: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo "  Avertissement: $1"
    ((WARNINGS++))
}

echo "1. Vérifications préliminaires"
echo "================================"

# Vérifier qu'on est dans le bon dossier
check "Vérification du répertoire"
if [ -f "pyproject.toml" ] && [ -d "geneweb_py" ]; then
    pass
else
    fail "Pas dans le répertoire racine du projet"
    exit 1
fi

# Vérifier que git est propre
check "Vérification git status"
if [ -z "$(git status --porcelain)" ]; then
    pass
else
    warn "Des changements non commités existent"
fi

# Vérifier la branche
check "Vérification branche git"
BRANCH=$(git branch --show-current)
if [ "$BRANCH" == "main" ] || [ "$BRANCH" == "master" ]; then
    pass
else
    warn "Pas sur la branche main/master (branche actuelle: $BRANCH)"
fi

echo ""
echo "2. Tests unitaires et couverture"
echo "================================="

# Lancer les tests
check "Exécution des tests"
if pytest tests/ -v -m "not slow" --tb=short > /tmp/pytest_output.txt 2>&1; then
    pass
else
    fail "Des tests échouent"
    tail -n 20 /tmp/pytest_output.txt
fi

# Vérifier la couverture
check "Vérification couverture (objectif: 90%+)"
COVERAGE=$(pytest tests/ --cov=geneweb_py --cov-report=term-missing -m "not slow" 2>&1 | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
if [ ! -z "$COVERAGE" ]; then
    if (( $(echo "$COVERAGE >= 90" | bc -l) )); then
        pass
        echo "  Couverture: ${COVERAGE}%"
    elif (( $(echo "$COVERAGE >= 80" | bc -l) )); then
        warn "Couverture ${COVERAGE}% < 90%"
    else
        fail "Couverture ${COVERAGE}% < 80%"
    fi
else
    warn "Impossible de déterminer la couverture"
fi

echo ""
echo "3. Qualité du code"
echo "=================="

# Black
check "Vérification formatage (black)"
if black --check geneweb_py/ tests/ > /dev/null 2>&1; then
    pass
else
    fail "Formatage incorrect, exécuter: black geneweb_py/ tests/"
fi

# Flake8
check "Vérification linting (flake8)"
if flake8 geneweb_py/ tests/ --count --statistics > /dev/null 2>&1; then
    pass
else
    warn "Quelques warnings flake8"
fi

# Mypy
check "Vérification types (mypy)"
if mypy geneweb_py/ --ignore-missing-imports > /dev/null 2>&1; then
    pass
else
    warn "Quelques erreurs de typage"
fi

echo ""
echo "4. Construction du package"
echo "=========================="

# Nettoyer les builds précédents
check "Nettoyage builds précédents"
rm -rf dist/ build/ *.egg-info
pass

# Construire le package
check "Construction (wheel + sdist)"
if python -m build > /tmp/build_output.txt 2>&1; then
    pass
else
    fail "Erreur de construction"
    cat /tmp/build_output.txt
fi

# Vérifier les artefacts
check "Vérification artefacts (dist/)"
if [ -f dist/*.whl ] && [ -f dist/*.tar.gz ]; then
    pass
    echo "  $(ls -lh dist/)"
else
    fail "Artefacts manquants dans dist/"
fi

echo ""
echo "5. Validation du package"
echo "========================"

# Twine check
check "Validation twine"
if twine check dist/* > /tmp/twine_output.txt 2>&1; then
    pass
else
    fail "Erreur de validation twine"
    cat /tmp/twine_output.txt
fi

# Check-manifest (optionnel)
check "Vérification manifest"
if command -v check-manifest &> /dev/null; then
    if check-manifest > /tmp/manifest_output.txt 2>&1; then
        pass
    else
        warn "Problèmes dans le manifest"
    fi
else
    warn "check-manifest non installé (pip install check-manifest)"
fi

echo ""
echo "6. Tests de packaging"
echo "====================="

# Tests d'import
check "Tests imports publics"
if pytest tests/packaging/test_public_api.py -v --tb=short > /tmp/packaging_output.txt 2>&1; then
    pass
else
    fail "Tests d'import échouent"
    tail -n 20 /tmp/packaging_output.txt
fi

# Tests de métadonnées
check "Tests métadonnées"
if pytest tests/packaging/test_metadata.py -v --tb=short > /tmp/metadata_output.txt 2>&1; then
    pass
else
    warn "Quelques tests de métadonnées échouent"
fi

echo ""
echo "7. Sécurité"
echo "==========="

# pip-audit
check "Audit de sécurité (pip-audit)"
if command -v pip-audit &> /dev/null; then
    if pip-audit --desc > /tmp/audit_output.txt 2>&1; then
        pass
    else
        warn "Vulnérabilités potentielles détectées"
        head -n 10 /tmp/audit_output.txt
    fi
else
    warn "pip-audit non installé (pip install pip-audit)"
fi

# Tests de sécurité
check "Tests de sécurité"
if pytest tests/security/ -v --tb=short > /tmp/security_output.txt 2>&1; then
    pass
else
    warn "Quelques tests de sécurité échouent"
fi

echo ""
echo "8. Documentation"
echo "================"

# README
check "Vérification README.md"
if [ -f "README.md" ] && [ $(wc -l < README.md) -gt 50 ]; then
    pass
else
    fail "README.md manquant ou trop court"
fi

# LICENSE
check "Vérification LICENSE"
if [ -f "LICENSE" ]; then
    pass
else
    fail "LICENSE manquant"
fi

# CHANGELOG
check "Vérification CHANGELOG.md"
if [ -f "CHANGELOG.md" ]; then
    pass
else
    warn "CHANGELOG.md manquant"
fi

# Docstrings
check "Vérification docstrings"
if python -c "from geneweb_py import GeneWebParser, Genealogy, Person; assert GeneWebParser.__doc__ and Genealogy.__doc__ and Person.__doc__" 2>&1; then
    pass
else
    fail "Docstrings manquantes sur classes principales"
fi

echo ""
echo "9. Version et tags"
echo "=================="

# Vérifier la version
check "Lecture version"
VERSION=$(python -c "import geneweb_py; print(geneweb_py.__version__)")
if [ ! -z "$VERSION" ]; then
    pass
    echo "  Version: $VERSION"
else
    fail "Impossible de lire la version"
fi

# Vérifier si le tag existe
check "Vérification tag git"
if git tag | grep -q "v$VERSION"; then
    pass
    echo "  Tag v$VERSION existe"
else
    warn "Tag v$VERSION n'existe pas encore"
    echo "  Créer avec: git tag v$VERSION && git push origin v$VERSION"
fi

echo ""
echo "=================================================="
echo "  RÉSUMÉ"
echo "=================================================="
echo ""
echo -e "${GREEN}Tests réussis:     $PASSED${NC}"
echo -e "${YELLOW}Avertissements:    $WARNINGS${NC}"
echo -e "${RED}Tests échoués:     $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ PRÊT POUR PUBLICATION PYPI!${NC}"
        echo ""
        echo "Prochaines étapes:"
        echo "  1. Publication TestPyPI:"
        echo "     twine upload --repository testpypi dist/*"
        echo ""
        echo "  2. Test installation depuis TestPyPI:"
        echo "     pip install --index-url https://test.pypi.org/simple/ geneweb-py"
        echo ""
        echo "  3. Si OK, publication PyPI:"
        echo "     twine upload dist/*"
        exit 0
    else
        echo -e "${YELLOW}⚠ PRÊT AVEC AVERTISSEMENTS${NC}"
        echo ""
        echo "Recommandation: Corriger les avertissements avant publication"
        exit 0
    fi
else
    echo -e "${RED}✗ PAS PRÊT POUR PUBLICATION${NC}"
    echo ""
    echo "Corriger les erreurs avant de publier"
    exit 1
fi

