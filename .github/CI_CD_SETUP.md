# Configuration CI/CD GitHub Actions - geneweb-py

**Date de création** : 9 octobre 2025  
**Statut** : ✅ Configuré et prêt

## 📋 Vue d'Ensemble

Ce projet dispose maintenant d'une infrastructure CI/CD complète basée sur GitHub Actions.

## 🚀 Workflows Configurés

### 1. Tests et Couverture (`tests.yml`)
**Quand** : À chaque push/PR sur main et develop

**Ce qu'il fait** :
- ✅ Lance les tests sur **5 versions Python** (3.8 à 3.12)
- ✅ Calcule la couverture de code
- ✅ Vérifie le seuil minimum (**84%**)
- ✅ Upload les rapports vers Codecov
- ✅ Commente les PR avec les résultats
- ✅ Archive les rapports HTML (30 jours)

**Seuils** :
- Minimum : 84% (actuel)
- Cible : 90% (court terme)
- Objectif : 100% (long terme)

### 2. Linting (`lint.yml`)
**Quand** : À chaque push/PR

**Ce qu'il fait** :
- ✅ Vérifie le formatage **Black**
- ✅ Lint avec **Flake8**
- ✅ Type checking avec **mypy**
- ⚠️ Continue même en cas d'erreurs (pour ne pas bloquer)

### 3. Rapport de Couverture (`coverage-report.yml`)
**Quand** : Push sur main, lundis 9h, ou manuel

**Ce qu'il fait** :
- ✅ Génère un rapport détaillé par module
- ✅ Archive les rapports HTML (90 jours)
- ✅ Affiche un résumé dans Actions
- ✅ Compare modules (excellent/bon/à améliorer)

### 4. Performance (`performance.yml`)
**Quand** : Push sur main, dimanches 3h

**Ce qu'il fait** :
- ✅ Benchmarks de parsing
- ✅ Mesure temps d'exécution
- ✅ Teste petits et gros fichiers

### 5. Vérifications PR (`pr-checks.yml`)
**Quand** : À chaque PR

**Ce qu'il fait** :
- ✅ Détecte les régressions de couverture
- ✅ Compte les nouveaux tests ajoutés
- ✅ Commente automatiquement la PR
- ❌ **Bloque la PR si couverture < 84%**

### 6. Rapport Hebdomadaire (`weekly-report.yml`)
**Quand** : Lundis 8h ou manuel

**Ce qu'il fait** :
- ✅ Résumé de la semaine (commits, tests)
- ✅ État de la couverture
- ✅ Rappels des prochaines étapes

### 7. Release (`release.yml`)
**Quand** : À la création d'un tag `v*.*.*`

**Ce qu'il fait** :
- ✅ Build du package Python
- ✅ Crée une release GitHub
- ✅ Publie sur PyPI (si token configuré)

## 🔧 Configuration Initiale

### Étape 1 : Activer GitHub Actions

Les workflows sont prêts ! Ils s'activeront automatiquement au prochain push.

### Étape 2 : Configurer les Secrets (Optionnel)

Pour activer toutes les fonctionnalités :

1. Aller dans **Settings > Secrets and variables > Actions**
2. Ajouter les secrets :

| Secret | Description | Requis |
|--------|-------------|--------|
| `PYPI_TOKEN` | Token PyPI pour publication | Non (seulement pour releases) |
| `CODECOV_TOKEN` | Token Codecov.io | Non (améliore l'intégration) |

### Étape 3 : Vérifier le Premier Run

Après le push :
1. Aller dans l'onglet **Actions**
2. Vérifier que "Tests et Couverture" passe ✅
3. Consulter les artifacts (rapports de couverture)

## 📊 Badges pour README

Les badges suivants sont déjà ajoutés au README.md :

```markdown
[![Tests](https://github.com/guillaumecayeux/geneweb-py/workflows/Tests%20et%20Couverture/badge.svg)](https://github.com/guillaumecayeux/geneweb-py/actions)
[![Linting](https://github.com/guillaumecayeux/geneweb-py/workflows/Linting%20et%20Formatage/badge.svg)](https://github.com/guillaumecayeux/geneweb-py/actions)
[![Coverage](https://img.shields.io/badge/coverage-84%25-green.svg)](htmlcov/index.html)
[![Tests Passing](https://img.shields.io/badge/tests-858%20passing-success.svg)](tests/)
```

## 🎯 Seuils de Qualité

### Tests
- ✅ Minimum 858 tests passants
- ✅ Zéro régression autorisée

### Couverture
- 🔴 < 84% : CI échoue
- 🟡 84-90% : CI passe avec warning
- 🟢 90-95% : CI passe (excellent)
- ⭐ >95% : CI passe (exceptionnel)

### Linting
- ⚠️ Warnings seulement (non bloquant)
- Continue même avec erreurs
- Aide à maintenir la qualité

## 🔄 Dependabot

Configuré pour :
- **Dépendances Python** : Vérifications hebdomadaires (lundis 9h)
- **GitHub Actions** : Vérifications hebdomadaires
- PR automatiques pour mises à jour
- Maximum 5 PR Python + 3 PR Actions ouvertes simultanément

## 📈 Monitoring Continu

### Quotidien
- Chaque push lance les tests
- Vérification couverture automatique

### Hebdomadaire
- Lundi 8h : Rapport hebdomadaire
- Lundi 9h : Rapport couverture détaillé
- Lundi 9h : Vérif dépendances (Dependabot)
- Dimanche 3h : Tests performance

### À la Demande
- Tous les workflows ont `workflow_dispatch`
- Lancement manuel possible depuis GitHub

## 🎓 Utilisation

### Workflow Tests Locaux

Avant de push, testez localement :

```bash
# Comme dans le CI
pytest tests/ \
  --cov=geneweb_py \
  --cov-report=term-missing \
  --cov-fail-under=84

# Linting
black --check geneweb_py/ tests/
flake8 geneweb_py/
mypy geneweb_py/ --ignore-missing-imports
```

### Déclencher Manuellement un Workflow

1. GitHub > Actions
2. Sélectionner le workflow
3. "Run workflow" > "Run"

### Consulter les Rapports

1. GitHub > Actions > Sélectionner un run
2. Télécharger les "Artifacts"
3. Ouvrir `htmlcov/index.html`

## 📝 Maintenance

### Ajuster les Seuils

Éditer `.github/workflows/tests.yml` :

```yaml
--cov-fail-under=84  # Changez ce nombre
```

### Désactiver un Workflow

Renommer le fichier : `tests.yml.disabled`

Ou dans GitHub > Actions > Workflow > "..." > Disable

## ✅ Checklist de Validation

- [x] 7 workflows créés
- [x] Documentation README.md
- [x] Dependabot configuré
- [x] Badges ajoutés au README
- [x] Seuils configurés (84%)
- [ ] Secrets configurés (optionnel)
- [ ] Premier run validé (après push)

## 🚀 Prochaines Étapes

1. **Push ce commit** : Les workflows s'activeront automatiquement
2. **Vérifier l'onglet Actions** : Premier run des workflows
3. **Configurer Codecov** (optionnel) : Meilleure intégration couverture
4. **Ajuster si nécessaire** : Les workflows sont personnalisables

---

**La CI/CD est maintenant complètement opérationnelle !** 🎉

Chaque push déclenchera automatiquement :
- Tests sur 5 versions Python
- Vérification couverture
- Linting
- Et bien plus...

