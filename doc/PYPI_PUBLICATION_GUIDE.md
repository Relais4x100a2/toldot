# Guide de Publication PyPI - geneweb-py

**Date** : 9 octobre 2025  
**Version** : 0.1.0  
**Auteur** : Guillaume Cayeux

## 📋 Résumé

Ce guide fournit toutes les instructions pour publier geneweb-py sur PyPI.

## ✅ Pré-requis

### Outils nécessaires

```bash
# Installation des outils de build et publication
pip install build twine check-manifest pip-audit pip-licenses

# Vérification versions
python --version  # ≥ 3.7
twine --version
```

### Comptes requis

1. **PyPI** : https://pypi.org/account/register/
2. **TestPyPI** : https://test.pypi.org/account/register/

### Tokens API

Créer des tokens API sur PyPI et TestPyPI :
- PyPI : https://pypi.org/manage/account/token/
- TestPyPI : https://test.pypi.org/manage/account/token/

Configurer dans `~/.pypirc` :

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZw...
```

## 🚀 Procédure de Publication

### Étape 1 : Préparation

```bash
# 1. Mettre à jour la version
# Éditer geneweb_py/__init__.py et pyproject.toml
vim geneweb_py/__init__.py  # __version__ = "0.1.0"
vim pyproject.toml          # version = "0.1.0"

# 2. Mettre à jour CHANGELOG.md
vim CHANGELOG.md

# 3. Commit les changements
git add .
git commit -m "chore: bump version to 0.1.0"
git push origin main
```

### Étape 2 : Validation

```bash
# Validation complète
./scripts/validate_pypi.sh

# Vérification avancée
python scripts/check_pypi_readiness.py

# Si tout est vert, continuer
```

### Étape 3 : Construction

```bash
# Nettoyer les builds précédents
rm -rf dist/ build/ *.egg-info

# Construire le package
python -m build

# Vérifier les artefacts
ls -lh dist/
# Doit contenir :
# - geneweb_py-0.1.0-py3-none-any.whl
# - geneweb_py-0.1.0.tar.gz
```

### Étape 4 : Validation du package

```bash
# Vérifier avec twine
twine check dist/*
# Doit afficher : PASSED

# Vérifier le manifest (optionnel)
check-manifest

# Tests de packaging
pytest tests/packaging/ -v
```

### Étape 5 : Publication sur TestPyPI

```bash
# Upload vers TestPyPI
twine upload --repository testpypi dist/*

# Vérifier sur le site
open https://test.pypi.org/project/geneweb-py/

# Test d'installation
python -m venv /tmp/test-env
source /tmp/test-env/bin/activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ geneweb-py

# Tester l'import
python -c "from geneweb_py import GeneWebParser; print('OK')"

# Nettoyer
deactivate
rm -rf /tmp/test-env
```

### Étape 6 : Validation finale

Si tout fonctionne sur TestPyPI :

```bash
# Lancer tous les tests une dernière fois
pytest tests/ -v --cov=geneweb_py

# Vérifier la couverture
# Doit être ≥ 90%
```

### Étape 7 : Publication sur PyPI

```bash
# Upload vers PyPI PRODUCTION
twine upload dist/*

# ATTENTION : Cette action est IRRÉVERSIBLE
# On ne peut pas supprimer une version publiée
```

### Étape 8 : Tag et Release GitHub

```bash
# Créer un tag git
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# Créer une release sur GitHub
# Aller sur https://github.com/guillaumecayeux/geneweb-py/releases/new
# - Tag version: v0.1.0
# - Release title: geneweb-py v0.1.0
# - Description: Copier depuis CHANGELOG.md
# - Attach binaries: dist/geneweb_py-0.1.0*
```

### Étape 9 : Vérification post-publication

```bash
# Vérifier sur PyPI
open https://pypi.org/project/geneweb-py/

# Test d'installation
python -m venv /tmp/final-test
source /tmp/final-test/bin/activate
pip install geneweb-py

# Vérifier version
python -c "import geneweb_py; print(geneweb_py.__version__)"

# Test rapide
python -c "
from geneweb_py import GeneWebParser
parser = GeneWebParser()
print('Installation réussie!')
"

# Nettoyer
deactivate
rm -rf /tmp/final-test
```

### Étape 10 : Communication

```bash
# Mettre à jour README avec le badge PyPI
# Annoncer sur les canaux appropriés
# Twitter, LinkedIn, forums, etc.
```

## 🔄 Publication automatisée (GitHub Actions)

Le workflow `.github/workflows/test-pypi.yml` automatise la publication :

### Publication automatique sur TestPyPI

**Déclencheur** : Push sur branche `dev`

```bash
git checkout dev
git merge main
git push origin dev
# → Publication automatique sur TestPyPI
```

### Publication automatique sur PyPI

**Déclencheur** : Création d'une release GitHub

```bash
# 1. Créer et pusher un tag
git tag v0.1.0
git push origin v0.1.0

# 2. Créer une release sur GitHub
# Via l'interface web ou avec gh CLI:
gh release create v0.1.0 --title "v0.1.0" --notes "Release notes"

# → Publication automatique sur PyPI
```

### Configuration des secrets GitHub

Ajouter dans Settings > Secrets and variables > Actions :

- `TEST_PYPI_API_TOKEN` : Token TestPyPI
- `PYPI_API_TOKEN` : Token PyPI

## 📊 Checklist complète

### Avant publication

- [ ] Version mise à jour dans `__init__.py` et `pyproject.toml`
- [ ] `CHANGELOG.md` mis à jour
- [ ] Tous les tests passent (858 tests)
- [ ] Couverture ≥ 90% (actuellement 84%)
- [ ] `./scripts/validate_pypi.sh` réussit
- [ ] `python scripts/check_pypi_readiness.py` réussit
- [ ] Documentation à jour (README, STATUS)
- [ ] LICENSE présent
- [ ] Pas de secrets hardcodés

### Construction

- [ ] `rm -rf dist/ build/ *.egg-info`
- [ ] `python -m build` réussit
- [ ] `twine check dist/*` PASSED
- [ ] Tests packaging réussissent
- [ ] Wheel et sdist créés

### TestPyPI

- [ ] Upload vers TestPyPI réussi
- [ ] Installation depuis TestPyPI fonctionne
- [ ] Imports fonctionnent
- [ ] Tests basiques passent

### PyPI Production

- [ ] Validation finale complète
- [ ] Upload vers PyPI réussi
- [ ] Vérification sur pypi.org
- [ ] Installation depuis PyPI fonctionne
- [ ] Tag git créé et pushé
- [ ] Release GitHub créée
- [ ] Documentation mise à jour

## 🚨 Troubleshooting

### Erreur "Package already exists"

```bash
# Incrémenter la version et reconstruire
vim geneweb_py/__init__.py  # Changer version
rm -rf dist/
python -m build
```

### Erreur "Invalid distribution"

```bash
# Vérifier twine
twine check dist/*

# Vérifier pyproject.toml
python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"
```

### Erreur d'authentification

```bash
# Vérifier ~/.pypirc
cat ~/.pypirc

# Régénérer le token API
# Aller sur PyPI > Account > API tokens
```

### Tests qui échouent

```bash
# Identifier les tests qui échouent
pytest tests/ -v --tb=short

# Corriger et re-tester
pytest tests/packaging/ -v
```

## 📚 Ressources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [TestPyPI](https://test.pypi.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)

## 🎯 Après publication

### Monitoring

- Surveiller les downloads : https://pypistats.org/packages/geneweb-py
- Surveiller les issues : https://github.com/guillaumecayeux/geneweb-py/issues
- Surveiller les stars/forks

### Maintenance

- Répondre aux issues
- Merger les PRs
- Publier des patches si nécessaire (0.1.1, 0.1.2, etc.)
- Préparer la v0.2.0 selon la roadmap

### Communication

- Annoncer sur les forums généalogie
- Écrire un article de blog
- Présenter dans des conférences Python
- Contribuer à la documentation GeneWeb

## ✅ Conclusion

La publication sur PyPI est maintenant automatisée et documentée. Suivez simplement cette checklist et les scripts de validation pour garantir une publication de qualité.

**Bonne publication! 🚀**

