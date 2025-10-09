# Quick Start - Tests PyPI

**Pour démarrer rapidement avec les tests de préparation PyPI**

## ✅ Statut actuel

- ✅ **23 tests de packaging** - Tous passent
- ✅ **13 tests de compatibilité** - Tous passent
- ✅ **7 tests de sécurité** - Tous passent
- ✅ **~785 tests totaux** dans le projet

## 🚀 Commandes rapides

### Lancer les tests PyPI spécifiques

```bash
# Tous les tests de packaging
pytest tests/packaging/ -v

# Tous les tests de compatibilité
pytest tests/compatibility/ -v

# Tous les tests de sécurité
pytest tests/security/ -v

# Tous les nouveaux tests PyPI
pytest tests/packaging/ tests/compatibility/ tests/security/ -v
```

### Validation avant publication

```bash
# Validation bash (complète)
./scripts/validate_pypi.sh

# Validation Python (rapide)
python scripts/check_pypi_readiness.py

# Construction du package
python -m build

# Vérification twine
twine check dist/*
```

### Test d'installation locale

```bash
# Construire et installer localement
python -m build
pip install dist/*.whl --force-reinstall

# Tester l'import
python -c "from geneweb_py import GeneWebParser; print('OK')"
```

## 📋 Checklist rapide

Avant de publier sur PyPI :

1. ✅ Tous les tests passent : `pytest tests/`
2. ✅ Tests PyPI passent : `pytest tests/packaging/ tests/compatibility/ tests/security/`
3. ✅ Validation réussit : `./scripts/validate_pypi.sh`
4. ✅ Package se construit : `python -m build`
5. ✅ Twine valide : `twine check dist/*`
6. ✅ Installation locale fonctionne
7. ✅ Version mise à jour dans `__init__.py` et `pyproject.toml`
8. ✅ `CHANGELOG.md` mis à jour

## 📚 Documentation complète

Pour plus de détails :

- **Stratégie complète** : `doc/PYPI_TESTING_STRATEGY.md`
- **Guide de publication** : `doc/PYPI_PUBLICATION_GUIDE.md`  
- **Résumé de préparation** : `PYPI_READINESS_SUMMARY.md`

## 🎯 Prochaines étapes

### 1. Tester sur TestPyPI

```bash
# Upload vers TestPyPI
twine upload --repository testpypi dist/*

# Installer depuis TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    geneweb-py
```

### 2. Publier sur PyPI

```bash
# Upload vers PyPI (production)
twine upload dist/*
```

### 3. Automatisation GitHub Actions

La publication peut être automatisée :
- Push sur `dev` → TestPyPI
- Release GitHub → PyPI

Voir `.github/workflows/test-pypi.yml`

## 🛠️ Dépannage rapide

### Tests échouent

```bash
# Voir les détails
pytest tests/packaging/ -v --tb=long

# Relancer un test spécifique
pytest tests/packaging/test_public_api.py::test_main_imports -v
```

### Build échoue

```bash
# Nettoyer et reconstruire
rm -rf dist/ build/ *.egg-info
python -m build
```

### Imports ne marchent pas

```bash
# Vérifier les __init__.py
cat src/geneweb_py/__init__.py
cat src/geneweb_py/core/__init__.py
cat src/geneweb_py/formats/__init__.py
```

## 💡 Conseils

1. **Toujours commencer par TestPyPI**
2. **Vérifier chaque étape** avec les scripts
3. **Tester l'installation** dans un venv propre
4. **Lire les logs** en cas d'erreur

## 🎊 Résultat

Vous êtes prêt à publier geneweb-py sur PyPI ! 🚀

**Bon courage !**

