# GitHub Actions Workflows

Ce dossier contient les workflows CI/CD pour le projet geneweb-py.

## 📋 Workflows Disponibles

### 1. `tests.yml` - Tests et Couverture
**Déclenchement** : Push/PR sur main et develop

**Actions** :
- Lance les tests sur Python 3.8, 3.9, 3.10, 3.11, 3.12
- Génère les rapports de couverture
- Upload vers Codecov
- Vérifie le seuil minimum (`--cov-fail-under=80` dans le job de tests)
- Commente les PR avec les résultats

**Badges** :
```markdown
[![Tests](https://github.com/Relais4x100a2/geneweb-py/workflows/Tests%20et%20Couverture/badge.svg)](https://github.com/Relais4x100a2/geneweb-py/actions)
[![Coverage](https://codecov.io/gh/Relais4x100a2/geneweb-py/branch/main/graph/badge.svg)](https://codecov.io/gh/Relais4x100a2/geneweb-py)
```

### 2. `lint.yml` - Linting et Formatage
**Déclenchement** : Push/PR sur main et develop

**Actions** :
- Vérification du formatage et du lint avec **Ruff**
- Vérification des types avec **mypy**

### 3. `coverage-report.yml` - Rapport Détaillé
**Déclenchement** : Push sur main, tous les lundis à 9h, manuel

**Actions** :
- Génère un rapport de couverture détaillé
- Archive les rapports HTML
- Crée un résumé par module

### 4. `performance.yml` - Tests Performance
**Déclenchement** : Push sur main, tous les dimanches à 3h

**Actions** :
- Benchmarks de parsing
- Tests de performance
- Mesure temps d'exécution

### 5. `pr-checks.yml` - Vérifications PR
**Déclenchement** : Ouverture/mise à jour PR

**Actions** :
- Mesure la couverture au **merge-base** avec la base (`coverage_baseline.json`) puis sur la **tête de la PR** avec `--cov-report=json` et `--cov-fail-under=84`
- Compare la PR à la baseline (échec si la couverture baisse par rapport au merge-base)
- Met à jour **un seul** commentaire (bot) avec tableau + delta, évite le spam de commentaires

### 6. `weekly-report.yml` - Rapport Hebdomadaire
**Déclenchement** : Tous les lundis à 8h UTC, manuel

**Actions** :
- Vérifie la présence des fichiers de référence (`doc/status.md`, `README.md`, etc.)
- Lance `pytest` avec un résumé de couverture en logs (les chiffres « officiels » pour la doc restent dans `doc/status.md` et sur Codecov)

### 7. `release.yml` - Publication
**Déclenchement** : Tags v*.*.*

**Actions** :
- Build du package
- Création release GitHub
- Publication sur PyPI (si configuré)

### 8. `security.yml` - Audit des dépendances (pip-audit)
**Déclenchement** : Push/PR sur `main` et `develop`, planification hebdomadaire (lundi 6h UTC)

**Actions** :
- Agrège les contraintes des extras `api`, `validation` et `parsing` (aligné sur les dépendances d’exécution exposées aux utilisateurs)
- Exécute `pip-audit --strict` sur cette liste pour détecter les vulnérabilités connues des paquets PyPI

## 🔧 Configuration

### Secrets Requis

Pour activer toutes les fonctionnalités, configurez ces secrets dans GitHub :

1. `PYPI_TOKEN` - Token PyPI pour publication automatique
2. `CODECOV_TOKEN` - Token Codecov (optionnel)

### Seuils de Couverture

Actuellement :
- **Job tests (`tests.yml`)** : `--cov-fail-under=80`
- **Vérifications PR (`pr-checks.yml`)** : `--cov-fail-under=84`
- **Objectifs documentés** : voir `doc/status.md` et [Codecov](https://codecov.io/gh/Relais4x100a2/geneweb-py)

## 📊 Badges Disponibles

Ajoutez ces badges dans votre README.md :

```markdown
[![Tests](https://github.com/Relais4x100a2/geneweb-py/workflows/Tests%20et%20Couverture/badge.svg)](https://github.com/Relais4x100a2/geneweb-py/actions)
[![Linting](https://github.com/Relais4x100a2/geneweb-py/workflows/Linting%20et%20Formatage/badge.svg)](https://github.com/Relais4x100a2/geneweb-py/actions)
[![Coverage](https://codecov.io/gh/Relais4x100a2/geneweb-py/branch/main/graph/badge.svg)](https://codecov.io/gh/Relais4x100a2/geneweb-py)
[![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue)](https://www.python.org/downloads/)
```

## 🚀 Utilisation

Les workflows s'exécutent automatiquement. Vous pouvez aussi les déclencher manuellement :

1. Aller dans l'onglet "Actions" sur GitHub
2. Sélectionner le workflow
3. Cliquer "Run workflow"

## 📈 Monitoring

Les rapports sont disponibles dans :
- Artifacts de chaque workflow
- Résumés dans l'onglet Actions
- Commentaires automatiques sur les PR
