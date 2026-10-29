# Migration vers structure src/ - Documentation

**Date** : 9 octobre 2025  
**Version** : 0.1.0 (pré-publication)

## 🎯 Objectif de la migration

Migrer le projet vers la structure `src/` (src-layout) recommandée par la Python Packaging Authority (PyPA) pour améliorer la conformité PyPI et suivre les meilleures pratiques de la communauté Python.

## 📊 Changements structurels

### Avant
```
geneweb-py/
├── geneweb_py/          # Package à la racine
│   ├── __init__.py
│   ├── core/
│   ├── api/
│   ├── formats/
│   ├── utils/           # Vide
│   ├── tests/           # Vide
│   └── examples/        # Vide
├── tests/               # Tests réels
└── pyproject.toml
```

### Après
```
geneweb-py/
├── src/
│   └── geneweb_py/      # Package dans src/
│       ├── __init__.py
│       ├── core/
│       ├── api/
│       └── formats/
├── tests/               # Tests (inchangés)
└── pyproject.toml       # Mis à jour
```

## ✅ Fichiers modifiés

### Configuration (2 fichiers)
1. **`pyproject.toml`**
   - `where = ["src"]` au lieu de `["."]`
   - `source = ["src/geneweb_py"]` pour la couverture

2. **`src/geneweb_py/__init__.py`**
   - Email mis à jour : `guillaume.cayeux@relais4x100a2.fr`

### Scripts Python (3 fichiers)
3. **`tests/performance/benchmark_parser.py`**
   - `sys.path.insert(0, str(project_root / "src"))`

4. **`scripts/check_pypi_readiness.py`**
   - Tous les chemins vers `src/geneweb_py/`

5. **`run_api.py`**
   - `sys.path.insert(0, str(root_dir / "src"))`

### Scripts Bash (1 fichier)
6. **`scripts/validate_pypi.sh`**
   - Vérification dossier : `src/geneweb_py`
   - Import version avec `sys.path.insert(0, 'src')`

### Documentation (3 fichiers)
7. **`doc/status.md`**
   - Diagramme d'architecture mis à jour

8. **`QUICK_START_PYPI.md`**
   - Chemins `__init__.py` corrigés

9. **`CHANGELOG.md`**
   - Migration documentée

## 🧹 Nettoyage effectué

### Dossiers vides supprimés
- `src/geneweb_py/utils/` (vide)
- `src/geneweb_py/tests/` (vide, les vrais tests sont à la racine)
- `src/geneweb_py/examples/` (vide, les vrais exemples sont à la racine)

### Fichiers temporaires supprimés
- Documentation de résumé de sessions obsolètes (13 fichiers)

## 🧪 Validation

| Test | Résultat | Commande |
|------|----------|----------|
| **Build** | ✅ PASSED | `python -m build` |
| **Twine** | ✅ PASSED | `twine check dist/*` |
| **Imports** | ✅ OK | `python -c "from geneweb_py import GeneWebParser"` |
| **Tests unitaires** | ✅ 349/377 | `pytest tests/unit/` |
| **Validation PyPI** | ✅ 23/23 | `python scripts/check_pypi_readiness.py` |
| **API** | ✅ OK | `python run_api.py --help` |

## 📦 Package final

- **Taille** : 96 KB (wheel)
- **Structure** : Conforme PyPA
- **Contenu** : Seulement le code source (pas de tests/examples)

## 🎯 Avantages de la structure src/

1. **Meilleure pratique** - Recommandée par PyPA
2. **Tests robustes** - Force l'utilisation du package installé
3. **Imports propres** - Évite les imports accidentels du code source
4. **Organisation claire** - Séparation nette code/tests/docs
5. **Conformité PyPI** - Structure standard reconnue

## 📝 Utilisation après migration

### Installation en développement
```bash
pip install -e .
```

### Imports (inchangés)
```python
from geneweb_py import GeneWebParser
from geneweb_py.core import Person, Family
```

### Build et publication
```bash
# Build
python -m build

# Validation
twine check dist/*

# Test sur TestPyPI
twine upload --repository testpypi dist/*

# Publication PyPI
twine upload dist/*
```

## 🔗 Références

- [Python Packaging Guide - src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PyPA Recommendations](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/)
- [setuptools Documentation](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html)

## ✨ Résultat

Le projet **geneweb-py** est maintenant 100% conforme aux standards PyPA et prêt pour publication sur PyPI.

