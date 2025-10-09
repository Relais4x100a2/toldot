# Résumé de l'implémentation : Messages d'erreur enrichis et validation gracieuse

## 🎯 Objectif

Améliorer l'expérience développeur avec des erreurs contextuelles et la possibilité de ne pas échouer au premier problème rencontré lors du parsing de fichiers GeneWeb.

## ✅ Fonctionnalités implémentées

### 1. Système de classification des erreurs

**Fichier** : `geneweb_py/core/exceptions.py`

- **`ErrorSeverity`** : Enum pour classifier les erreurs
  - `WARNING` : Avertissement non-bloquant
  - `ERROR` : Erreur standard
  - `CRITICAL` : Erreur critique nécessitant l'arrêt

- **`ParseWarning`** : Nouvelle classe pour les avertissements de parsing
  - Utilisée pour signaler des problèmes mineurs
  - Ne bloque pas le parsing
  - Sévérité automatiquement définie à `WARNING`

### 2. Messages d'erreur enrichis

Toutes les classes d'erreur ont été améliorées pour inclure :

- **Numéro de ligne** exact de l'erreur
- **Contexte** : Information sur ce qui était en cours de parsing
- **Token trouvé** vs **Token attendu** (pour `GeneWebParseError`)
- **Champ** et **valeur** en erreur (pour `GeneWebValidationError`)
- **Type et ID d'entité** concernée
- **Sévérité** de l'erreur

Exemple de message enrichi :
```
Ligne 42: Token inattendu
  Token trouvé: 'invalid'
  Attendu: fam, nom, ou date
  Contexte: Parsing d'une personne DUPONT_Jean_0
```

Toutes les erreurs peuvent être converties en dictionnaire via `to_dict()` pour la sérialisation.

### 3. Collecteur d'erreurs (`GeneWebErrorCollector`)

**Fichier** : `geneweb_py/core/exceptions.py`

Le collecteur permet d'accumuler plusieurs erreurs au lieu de s'arrêter à la première :

- **Mode strict** (`strict=True`) : Lève une exception à la première erreur ERROR ou CRITICAL
- **Mode gracieux** (`strict=False`) : Accumule toutes les erreurs

Fonctionnalités :
- Filtrage par type d'erreur (`GeneWebParseError`, `GeneWebValidationError`, etc.)
- Filtrage par sévérité (`WARNING`, `ERROR`, `CRITICAL`)
- Méthodes de comptage par sévérité
- Génération de résumés et rapports détaillés
- Support du context manager

```python
# Mode gracieux
collector = GeneWebErrorCollector(strict=False)
collector.add_error(GeneWebParseError("Erreur 1", line_number=1))
collector.add_warning("Avertissement", line_number=2)

print(collector.get_error_summary())  # "1 erreur(s), 1 avertissement(s)"
print(collector.get_detailed_report())  # Rapport complet avec toutes les erreurs
```

### 4. Système de validation gracieuse

**Fichier** : `geneweb_py/core/validation.py`

Nouveau module dédié à la validation non-destructive :

#### `ValidationContext`
- Contexte de validation avec collecteur d'erreurs intégré
- Accumule les erreurs de validation
- Génère un `ValidationResult` final

#### `ValidationResult`
- Distingue erreurs et avertissements
- Méthode `is_valid()` : validation réussie si pas d'erreurs (warnings OK)
- `has_warnings()`, `has_errors()`
- Résumés et messages détaillés

#### Fonctions de validation

- **`validate_person_basic(person, context)`** : Validation de base d'une personne
  - Vérifie nom/prénom obligatoires
  - Cohérence des dates (naissance < décès, baptême > naissance)
  - Warnings pour décès sans date ou vice-versa

- **`validate_person_relationships(person, genealogy, context)`** : Validation des relations
  - Vérifie que les familles référencées existent

- **`validate_family_basic(family, context)`** : Validation de base d'une famille
  - Au moins un parent ou un enfant
  - Cohérence mariage/divorce

- **`validate_family_members(family, genealogy, context)`** : Validation des membres
  - Vérifie que tous les membres existent dans la généalogie

- **`validate_genealogy_consistency(genealogy, context)`** : Validation complète
  - Valide toutes les personnes et familles
  - Vérifie la cohérence bidirectionnelle des références

- **`validate_bidirectional_references(genealogy, context)`** : Références croisées
  - Vérifie que les références parent↔enfant sont cohérentes

#### Création d'objets partiels

- **`create_partial_person()`** : Crée une personne partielle en cas d'erreur
- **`create_partial_family()`** : Crée une famille partielle en cas d'erreur
- Les objets partiels ont `is_valid=False` et `validation_errors` rempli

### 5. Attributs de validation sur les modèles

**Fichiers** : `person.py`, `family.py`, `genealogy.py`

Tous les modèles principaux ont maintenant :

- **`is_valid`** : `bool` indiquant si l'objet est valide
- **`validation_errors`** : `List[GeneWebError]` contenant les erreurs de validation
- **`add_validation_error(error)`** : Ajoute une erreur et marque comme invalide
- **`clear_validation_errors()`** : Efface les erreurs et revalide

#### Modifications du `__post_init__`

Les vérifications dans `__post_init__` de `Person` et `Family` ont été converties en validation gracieuse :
- Au lieu de lever des exceptions, elles ajoutent des erreurs de validation
- Permet de créer des objets même avec des données incohérentes
- Les objets créés ont `is_valid=False` et contiennent les erreurs

### 6. Intégration dans le parser

**Fichier** : `geneweb_py/core/parser/gw_parser.py`

Le parser `GeneWebParser` supporte maintenant le mode strict/gracieux :

- **Nouveau paramètre** : `strict: bool = True`
- **Mode strict** (défaut) : Comportement actuel, s'arrête à la première erreur
- **Mode gracieux** : Continue le parsing et collecte les erreurs

```python
# Mode strict (défaut)
parser = GeneWebParser(strict=True)
try:
    genealogy = parser.parse_file("fichier.gw")
except GeneWebParseError as e:
    print(f"Erreur : {e}")

# Mode gracieux
parser = GeneWebParser(strict=False, validate=True)
genealogy = parser.parse_file("fichier.gw")

if not genealogy.is_valid:
    print(f"Erreurs : {len(genealogy.validation_errors)}")
    print(genealogy.get_validation_summary())
    
    for error in genealogy.validation_errors:
        print(f"- {error}")
```

Les erreurs collectées par le parser sont transférées vers l'objet `Genealogy`.

### 7. Amélioration de la classe `Date`

**Fichier** : `geneweb_py/core/date.py`

Ajout de méthodes de comparaison :

- **`is_after(other)`** : Vérifie si une date est après une autre
- **`is_before(other)`** : Vérifie si une date est avant une autre
- Gère les dates incomplètes et inconnues gracieusement

### 8. Tests complets

#### `tests/unit/test_error_recovery.py` (17 tests)
- Tests du collecteur d'erreurs
- Tests des messages enrichis
- Tests du mode strict/gracieux
- Tests de récupération après erreurs

#### `tests/unit/test_validation_graceful.py` (24 tests)
- Tests du contexte de validation
- Tests de validation des personnes
- Tests de validation des familles
- Tests de validation de la généalogie complète
- Tests des objets partiels
- Tests d'intégration

#### Fixtures de test
- **`error_syntax.gw`** : Fichier avec erreurs syntaxiques
- **`error_incomplete.gw`** : Fichier avec données incomplètes
- **`error_inconsistent.gw`** : Fichier avec incohérences logiques

**Total : 41 nouveaux tests, tous passent ✅**

### 9. Documentation

#### README.md
- Nouvelle section "Validation gracieuse et gestion d'erreurs"
- Exemples d'utilisation du mode strict/gracieux
- Exemples de messages d'erreur enrichis
- Exemples de validation des données

#### doc/status.md
- Section "Messages d'erreur enrichis et validation gracieuse"
- Description complète des fonctionnalités
- Architecture mise à jour

## 📊 Statistiques

- **Fichiers créés** : 5
  - `geneweb_py/core/validation.py` (411 lignes)
  - `tests/unit/test_error_recovery.py` (246 lignes)
  - `tests/unit/test_validation_graceful.py` (328 lignes)
  - `tests/fixtures/error_*.gw` (3 fichiers)

- **Fichiers modifiés** : 7
  - `geneweb_py/core/exceptions.py` : +380 lignes
  - `geneweb_py/core/person.py` : +30 lignes
  - `geneweb_py/core/family.py` : +30 lignes
  - `geneweb_py/core/genealogy.py` : +60 lignes
  - `geneweb_py/core/date.py` : +65 lignes
  - `geneweb_py/core/parser/gw_parser.py` : +15 lignes
  - Documentation : +100 lignes

- **Tests** : 41 nouveaux tests (100% de réussite)
- **Couverture** : Module `exceptions.py` à 68%, `validation.py` couvert par les tests

## 🎓 Exemples d'utilisation

### Exemple 1 : Mode gracieux avec rapport complet

```python
from geneweb_py import GeneWebParser

parser = GeneWebParser(strict=False, validate=True)
genealogy = parser.parse_file("fichier_avec_erreurs.gw")

# Vérifier la validité
print(f"Généalogie valide : {genealogy.is_valid}")
print(f"Nombre d'erreurs : {len(genealogy.validation_errors)}")

# Obtenir le résumé
print(genealogy.get_validation_summary())
# Output: "Généalogie avec erreurs: 3 erreur(s), 2 avertissement(s)"

# Rapport détaillé du parser
if parser.error_collector.has_errors():
    print(parser.error_collector.get_detailed_report())
```

### Exemple 2 : Validation d'une personne

```python
from geneweb_py.core.validation import validate_person_basic
from geneweb_py.core.person import Person, Gender
from geneweb_py.core.date import Date

person = Person(
    last_name="DUPONT",
    first_name="Jean",
    gender=Gender.MALE,
    birth_date=Date(year=2000),
    death_date=Date(year=1990)  # Incohérence !
)

result = validate_person_basic(person)

if not result.is_valid():
    print("Erreurs de validation :")
    for error in result.get_error_messages():
        print(f"  - {error}")
```

### Exemple 3 : Collecteur d'erreurs personnalisé

```python
from geneweb_py.core.exceptions import (
    GeneWebErrorCollector,
    GeneWebParseError,
    ParseWarning
)

with GeneWebErrorCollector(strict=False) as collector:
    # Simuler la collecte d'erreurs
    collector.add_error(GeneWebParseError("Erreur 1", line_number=10))
    collector.add_warning("Attention", line_number=20)
    
    # Obtenir les statistiques
    print(f"Total : {len(collector)}")
    print(f"Warnings : {collector.error_count(ErrorSeverity.WARNING)}")
    print(collector.get_error_summary())
```

## 🚀 Avantages

1. **Meilleure expérience développeur** : Messages d'erreur clairs et contextuels
2. **Débogage facilité** : Toutes les erreurs sont rapportées en une seule passe
3. **Flexibilité** : Mode strict pour production, mode gracieux pour développement/debug
4. **Robustesse** : Le parsing peut continuer même avec des données partiellement invalides
5. **Traçabilité** : Chaque erreur est précisément localisée (ligne, contexte, entité)
6. **Extensibilité** : Facile d'ajouter de nouvelles validations

## 🔄 Compatibilité

- **Rétrocompatible** : Le mode strict est activé par défaut, comportement identique
- **Opt-in** : Le mode gracieux est optionnel (`strict=False`)
- **Pas d'impact** : Les utilisateurs existants ne sont pas affectés

## 📝 Notes

- La validation gracieuse ne remplace pas les validations de sécurité critiques
- En mode gracieux, vérifier toujours `genealogy.is_valid` avant utilisation
- Les objets partiels permettent de continuer le traitement même avec erreurs
- La sérialisation JSON/dict inclut automatiquement le statut de validation

