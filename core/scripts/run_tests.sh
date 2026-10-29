#!/bin/bash
# Script pour exécuter les tests avec ou sans couverture

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Script de tests geneweb-py${NC}"
echo "=================================="

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --coverage     Exécuter avec couverture de code"
    echo "  --unit         Exécuter seulement les tests unitaires"
    echo "  --integration  Exécuter seulement les tests d'intégration"
    echo "  --compatibility Exécuter seulement les tests de compatibilité"
    echo "  --packaging    Exécuter seulement les tests de packaging"
    echo "  --security     Exécuter seulement les tests de sécurité"
    echo "  --fast         Exécuter sans les tests lents"
    echo "  --core-only    Couverture seulement sur les modules core (plus réaliste)"
    echo "  --help         Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 --coverage --unit --core-only  # Tests unitaires avec couverture core"
    echo "  $0 --fast                         # Tests rapides sans couverture"
    echo "  $0 --unit --coverage              # Tests unitaires avec couverture complète"
}

# Variables par défaut
COVERAGE=false
UNIT=false
INTEGRATION=false
COMPATIBILITY=false
PACKAGING=false
SECURITY=false
FAST=false
CORE_ONLY=false

# Parse des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --unit)
            UNIT=true
            shift
            ;;
        --integration)
            INTEGRATION=true
            shift
            ;;
        --compatibility)
            COMPATIBILITY=true
            shift
            ;;
        --packaging)
            PACKAGING=true
            shift
            ;;
        --security)
            SECURITY=true
            shift
            ;;
        --fast)
            FAST=true
            shift
            ;;
        --core-only)
            CORE_ONLY=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Option inconnue: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Construction de la commande pytest
PYTEST_CMD="pytest"

# Ajout des chemins de tests
TEST_PATHS=()
if [[ "$UNIT" == true ]]; then
    TEST_PATHS+=("tests/unit/")
fi
if [[ "$INTEGRATION" == true ]]; then
    TEST_PATHS+=("tests/integration/")
fi
if [[ "$COMPATIBILITY" == true ]]; then
    TEST_PATHS+=("tests/compatibility/")
fi
if [[ "$PACKAGING" == true ]]; then
    TEST_PATHS+=("tests/packaging/")
fi
if [[ "$SECURITY" == true ]]; then
    TEST_PATHS+=("tests/security/")
fi

# Si aucun type spécifique n'est demandé, exécuter tous les tests
if [[ ${#TEST_PATHS[@]} -eq 0 ]]; then
    TEST_PATHS=("tests/")
fi

# Ajout des chemins à la commande
for path in "${TEST_PATHS[@]}"; do
    PYTEST_CMD="$PYTEST_CMD $path"
done

# Ajout des options
PYTEST_CMD="$PYTEST_CMD -v --tb=short"

# Ajout de l'option fast si demandée
if [[ "$FAST" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -m \"not slow\""
fi

# Ajout de la couverture si demandée
if [[ "$COVERAGE" == true ]]; then
    if [[ "$CORE_ONLY" == true ]]; then
        PYTEST_CMD="$PYTEST_CMD --cov=geneweb_py.core --cov-report=term-missing --cov-report=html --cov-fail-under=80"
        echo -e "${YELLOW}📊 Couverture de code activée (modules core seulement)${NC}"
    else
        PYTEST_CMD="$PYTEST_CMD --cov=geneweb_py --cov-report=term-missing --cov-report=html --cov-fail-under=60"
        echo -e "${YELLOW}📊 Couverture de code activée (tous modules)${NC}"
    fi
else
    PYTEST_CMD="$PYTEST_CMD --no-cov"
    echo -e "${YELLOW}⚡ Mode rapide (sans couverture)${NC}"
fi

# Affichage de la commande
echo -e "${GREEN}🚀 Commande: $PYTEST_CMD${NC}"
echo ""

# Exécution
echo -e "${GREEN}▶️  Exécution des tests...${NC}"
eval $PYTEST_CMD

# Vérification du résultat
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Tests réussis !${NC}"
    
    if [[ "$COVERAGE" == true ]]; then
        echo -e "${GREEN}📊 Rapport de couverture généré dans htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${RED}❌ Tests échoués !${NC}"
    exit 1
fi
