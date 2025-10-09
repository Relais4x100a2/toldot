# Tests Skippés - Documentation

## 📋 Tests Temporairement Skippés

Cette section documente les tests qui sont actuellement skippés et les raisons pour lesquelles ils ne sont pas exécutés.

### 🔍 Raisons des Skips

#### 1. **Fixtures Manquantes** (`SKIPPED - Fixtures manquantes`)
- **Fichiers concernés** : Tests nécessitant des fichiers `.gw` spécifiques
- **Exemples** :
  - `test_complete_person_parsing.py` : Nécessite des fichiers de test `.gw`
  - `test_error_recovery.py` : Nécessite des fichiers de test pour la récupération d'erreurs
- **Action requise** : Créer les fixtures de test manquantes

#### 2. **Fonctionnalités Non Implémentées** (`SKIPPED - Fonctionnalité non implémentée`)
- **Fichiers concernés** : Tests pour des features en développement
- **Exemples** :
  - Parsing des témoins (`witnesses`)
  - Parsing des enfants avec sexe
  - Parsing des commentaires de famille
- **Action requise** : Implémenter les fonctionnalités manquantes

#### 3. **Tests d'Intégration Complexes** (`SKIPPED - Test d'intégration complexe`)
- **Fichiers concernés** : Tests nécessitant des données complètes
- **Exemples** :
  - Parsing de fichiers `.gw` réalistes
  - Tests avec métadonnées complètes
- **Action requise** : Créer des données de test représentatives

### 📊 Statistiques des Skips

```
Total des tests : 377
Tests passants : 349 (92.6%)
Tests skippés : 28 (7.4%)
```

### 🎯 Tests par Catégorie

#### Tests de Parser (`test_parser_*.py`)
- **Skippés** : 15 tests
- **Raisons principales** :
  - Parsing des témoins non implémenté
  - Parsing des enfants avec sexe non implémenté
  - Parsing des commentaires de famille non implémenté
  - Fixtures de fichiers `.gw` manquantes

#### Tests d'Intégration (`test_integration/*.py`)
- **Skippés** : 8 tests
- **Raisons principales** :
  - Fixtures de fichiers `.gw` manquantes
  - Tests nécessitant des données complètes

#### Tests de Récupération d'Erreurs (`test_error_recovery.py`)
- **Skippés** : 3 tests
- **Raisons principales** :
  - Fixtures de fichiers `.gw` manquantes
  - Tests nécessitant des données d'erreur spécifiques

#### Tests de Métadonnées (`test_parser_edge_cases.py`)
- **Skippés** : 2 tests
- **Raisons principales** :
  - Parsing des en-têtes de métadonnées non implémenté
  - Tests nécessitant des fichiers avec métadonnées

### 🚀 Plan de Résolution

#### Phase 1 : Fixtures Manquantes (Priorité Haute)
1. **Créer les fichiers de test `.gw`** :
   - `tests/fixtures/simple_test.gw`
   - `tests/fixtures/test_complete.gw`
   - `tests/fixtures/test_relations.gw`
   - `tests/fixtures/test_witnesses.gw`

2. **Créer les fixtures pytest** :
   - Fixtures pour les données de test
   - Fixtures pour les fichiers temporaires
   - Fixtures pour les données d'erreur

#### Phase 2 : Fonctionnalités Non Implémentées (Priorité Moyenne)
1. **Parsing des témoins** :
   - Implémenter le parsing des témoins masculins/féminins
   - Ajouter la gestion des numéros d'occurrence des témoins

2. **Parsing des enfants** :
   - Implémenter le parsing des enfants avec sexe
   - Ajouter la gestion des numéros d'occurrence des enfants

3. **Parsing des commentaires** :
   - Implémenter le parsing des commentaires de famille
   - Ajouter la gestion des commentaires multiples

#### Phase 3 : Tests d'Intégration (Priorité Basse)
1. **Données de test complètes** :
   - Créer des fichiers `.gw` représentatifs
   - Ajouter des tests avec métadonnées complètes

2. **Tests de performance** :
   - Ajouter des tests avec de gros fichiers
   - Tester les performances de parsing

### 🔧 Commandes Utiles

#### Lister les tests skippés
```bash
pytest --collect-only -q | grep SKIP
```

#### Exécuter seulement les tests passants
```bash
pytest -m "not slow" --no-cov
```

#### Exécuter un fichier spécifique
```bash
pytest tests/unit/test_parser_advanced.py -v
```

#### Voir les raisons des skips
```bash
pytest -rs
```

### 📝 Notes de Développement

- **Ne pas supprimer les tests skippés** : Ils documentent les fonctionnalités à implémenter
- **Maintenir les raisons de skip** : Toujours documenter pourquoi un test est skippé
- **Prioriser les fixtures** : Commencer par créer les fixtures manquantes
- **Tests progressifs** : Implémenter les fonctionnalités par ordre de priorité

### 🎯 Objectifs

- **Court terme** : Réduire les tests skippés de 28 à < 10
- **Moyen terme** : Implémenter toutes les fonctionnalités de parsing
- **Long terme** : Avoir une couverture de tests complète (100% des tests passants)
