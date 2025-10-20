# Guide de la documentation geneweb-py

Ce document sert d'index central pour naviguer dans la documentation du projet.

## 📖 Structure de la documentation

La documentation de geneweb-py est organisée de manière claire et hiérarchique :

```
geneweb-py/
├── README.md                      # 👉 COMMENCER ICI - Guide principal
├── CHANGELOG.md                   # Historique des versions
├── LICENSE                        # Licence MIT
├── DOCUMENTATION.md              # Ce fichier - Index de navigation
│
├── doc/                          # Documentation technique
│   ├── status.md                 # État du projet et métriques
│   ├── roadmap.md                # Vision et évolution future
│   ├── PERFORMANCE.md            # Guide des optimisations
│   ├── PYPI_PUBLICATION_GUIDE.md # Guide publication PyPI
│   ├── PYPI_TESTING_STRATEGY.md  # Stratégie tests PyPI
│   └── geneweb/
│       └── gw_format_documentation.md  # Spécification format .gw
│
├── examples/                     # Scripts de démonstration
│   ├── basic_usage.py
│   ├── parser_usage.py
│   ├── api_usage.py
│   ├── conversion_usage.py
│   └── performance_demo.py
│
└── tests/                        # Tests et documentation associée
    ├── README.md                 # Guide des tests
    └── SKIPPED_TESTS.md          # Tests désactivés temporairement
```

## 🎯 Par objectif

### Je débute avec geneweb-py
→ Lisez **[README.md](README.md)** - Installation, utilisation rapide, exemples

### Je veux comprendre l'état du projet
→ Consultez **[doc/status.md](doc/status.md)** - Fonctionnalités, métriques, couverture

### Je veux contribuer
→ Lisez **[doc/status.md](doc/status.md)** puis **[doc/roadmap.md](doc/roadmap.md)**

### Je veux optimiser les performances
→ Consultez **[doc/PERFORMANCE.md](doc/PERFORMANCE.md)** - Benchmarks et optimisations

### Je veux publier sur PyPI
→ Suivez **[doc/PYPI_PUBLICATION_GUIDE.md](doc/PYPI_PUBLICATION_GUIDE.md)**

### Je veux comprendre le format GeneWeb
→ Lisez **[doc/geneweb/gw_format_documentation.md](doc/geneweb/gw_format_documentation.md)**

### Je veux lancer les tests
→ Consultez **[tests/README.md](tests/README.md)**

## 📚 Documentation par type

### Guides utilisateur
| Document | Description | Public |
|----------|-------------|--------|
| **[README.md](README.md)** | Guide principal et démarrage | Tous |
| **[examples/](examples/)** | Scripts de démonstration | Développeurs |

### Documentation technique
| Document | Description | Public |
|----------|-------------|--------|
| **[doc/status.md](doc/status.md)** | État, métriques, couverture | Contributeurs |
| **[doc/roadmap.md](doc/roadmap.md)** | Vision à long terme | Contributeurs |
| **[doc/PERFORMANCE.md](doc/PERFORMANCE.md)** | Optimisations et benchmarks | Développeurs avancés |
| **[doc/geneweb/gw_format_documentation.md](doc/geneweb/gw_format_documentation.md)** | Spécification format | Tous |

### Documentation PyPI
| Document | Description | Temps lecture |
|----------|-------------|---------------|
| **[doc/PYPI_PUBLICATION_GUIDE.md](doc/PYPI_PUBLICATION_GUIDE.md)** | Guide complet | 30 min |
| **[doc/PYPI_TESTING_STRATEGY.md](doc/PYPI_TESTING_STRATEGY.md)** | Stratégie de tests | 1h |

### Documentation tests
| Document | Description | Public |
|----------|-------------|--------|
| **[tests/README.md](tests/README.md)** | Structure et organisation | Contributeurs |
| **[tests/SKIPPED_TESTS.md](tests/SKIPPED_TESTS.md)** | Tests désactivés | Contributeurs |

## 🚀 Parcours recommandés

### Nouveau utilisateur (30 min)
1. **[README.md](README.md)** (15 min) - Installation et utilisation de base
2. **[examples/basic_usage.py](examples/basic_usage.py)** (5 min) - Exemple pratique
3. **[doc/geneweb/gw_format_documentation.md](doc/geneweb/gw_format_documentation.md)** (10 min) - Format GeneWeb

### Contributeur (1h)
1. **[README.md](README.md)** (10 min) - Vue d'ensemble
2. **[doc/status.md](doc/status.md)** (20 min) - État du projet
3. **[doc/roadmap.md](doc/roadmap.md)** (10 min) - Vision
4. **[tests/README.md](tests/README.md)** (10 min) - Tests
5. Exploration du code (10 min)

### Publication PyPI (40 min)
1. **[doc/PYPI_PUBLICATION_GUIDE.md](doc/PYPI_PUBLICATION_GUIDE.md)** (30 min) - Procédure
2. Validation et publication (10 min)

### Optimisation performance (1h30)
1. **[doc/PERFORMANCE.md](doc/PERFORMANCE.md)** (30 min) - Guide complet
2. **[examples/performance_demo.py](examples/performance_demo.py)** (15 min) - Démo
3. **[tests/performance/](tests/performance/)** (15 min) - Benchmarks
4. Expérimentation (30 min)

## 📊 Métriques clés

État actuel du projet (à jour) :

| Métrique | Valeur | État |
|----------|--------|------|
| **Tests** | 704 passants | ✅ Excellent |
| **Couverture** | 82% | ✅ Excellent |
| **Compatibilité** | Python 3.7-3.12 | ✅ Multi-versions |
| **Plateformes** | Linux, macOS, Windows | ✅ Multi-OS |
| **Performance** | ~80% économie mémoire (streaming) | ⚡ Optimisé |
| **Publication** | Prêt pour PyPI | ✅ Prêt |

Voir **[doc/status.md](doc/status.md)** pour les détails complets.

## 🔧 Outils et scripts

### Validation
```bash
# Validation complète avant publication
./scripts/validate_pypi.sh

# Vérification avancée
python scripts/check_pypi_readiness.py
```

### Tests
```bash
# Suite complète
pytest

# Tests unitaires seulement
pytest tests/unit/

# Tests avec couverture
pytest --cov=geneweb_py --cov-report=html

# Tests PyPI
pytest tests/packaging/ tests/compatibility/ tests/security/
```

### Documentation API
```bash
# Lancer l'API REST
python run_api.py

# Documentation Swagger UI
# → http://localhost:8000/docs
```

## 🆘 Besoin d'aide ?

- **Problème de parsing** → Voir [doc/geneweb/gw_format_documentation.md](doc/geneweb/gw_format_documentation.md)
- **Problème de performance** → Voir [doc/PERFORMANCE.md](doc/PERFORMANCE.md)
- **Problème de tests** → Voir [tests/README.md](tests/README.md)
- **Problème de publication** → Voir [doc/PYPI_PUBLICATION_GUIDE.md](doc/PYPI_PUBLICATION_GUIDE.md)

## 📝 Conventions

### Noms de fichiers
- `README.md` - Guides utilisateur en MAJUSCULES
- `doc/*.md` - Documentation technique en minuscules (sauf acronymes)
- `CHANGELOG.md` - Historique des versions

### Structure
- Documentation principale à la racine
- Documentation technique dans `doc/`
- Documentation de tests dans `tests/`
- Exemples dans `examples/`

## 🔄 Maintenance

Ce document est maintenu à jour à chaque modification majeure de la structure documentaire.

**Dernière mise à jour** : 9 janvier 2025

---

**Bon voyage dans la documentation ! 🚀**

