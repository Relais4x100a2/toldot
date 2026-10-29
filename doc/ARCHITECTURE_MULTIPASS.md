# Architecture Multi-passes pour le Parser GeneWeb

## 🎯 Vision

Passer d'une architecture **incrémentale** (parsing au fil de l'eau) à une architecture **multi-passes** (extraction → consolidation → construction).

---

## 🔄 Comparaison des approches

### ❌ Architecture actuelle (incrémentale)

```
fam DUPONT Jean + MARTIN Marie
  ↓ Créer Jean (sexe: MALE)
  ↓ Créer Marie (sexe: FEMALE)
  
notes DUPONT Jean
  ↓ Jean existe déjà ? → Fusion
  
wit f: DUPONT Jeanne
  ↓ Créer Jeanne (sexe: FEMALE)
```

**Problèmes :**
- ❌ L'ordre des blocs impacte le résultat
- ❌ Complexité de la fusion (6 endroits différents)
- ❌ Risque de doublons selon l'ordre
- ❌ Sexe difficile à inférer si témoin apparaît avant famille

### ✅ Architecture multi-passes (proposée)

```
PASSE 1: EXTRACTION
───────────────────
fam DUPONT Jean + MARTIN Marie
  → Référence: Jean (context=HUSBAND, gender=MALE)
  → Référence: Marie (context=WIFE, gender=FEMALE)

notes DUPONT Jean
  → Référence: Jean (context=NOTES, notes=[...])

wit f: DUPONT Jeanne
  → Référence: Jeanne (context=WITNESS, gender=FEMALE)

pevt DUPONT Jean
  → Référence: Jean (context=PEVT, events=[...])

PASSE 2: CONSOLIDATION
───────────────────────
Jean DUPONT:
  - Contextes: HUSBAND, NOTES, PEVT
  - Sexe: MALE (priorité HUSBAND)
  - Notes: fusionnées
  - Événements: fusionnés
  → Person(Jean, DUPONT, gender=MALE, ...)

PASSE 3: RELATIONS
──────────────────
Famille FAM_001:
  - Époux: Jean DUPONT
  - Épouse: Marie MARTIN
  - Enfants: [...]
```

**Avantages :**
- ✅ **Ordre indépendant** : peu importe l'ordre des blocs
- ✅ **Consolidation propre** : un seul endroit pour fusionner
- ✅ **Sexe intelligent** : priorité par contexte (HUSBAND > WITNESS)
- ✅ **Débogage facile** : chaque passe est isolée
- ✅ **Extensible** : ajouter de nouveaux contextes facilement

---

## 📊 Résultats attendus

### Sur une base de référence volumineuse (locale, hors dépôt)

Les chiffres exacts proviennent d'une base réelle conservée hors Git ; ils ne sont
pas reproduits ici. L'objectif est exprimé en proportions :

| Métrique | Actuel (incrémental) | Attendu (multi-passes) |
|----------|----------------------|------------------------|
| **Personnes retrouvées** | ~73 % | **100 %** ✅ |
| **Répartition H/F** | fortement biaisée | **~50 % / ~50 %** ✅ |
| **Inconnus** | ~18 % | **< 1 %** ✅ |
| **Familles avec enfants** | ~69 % | **~98 %** ✅ |

---

## 🏗️ Plan de migration

### Phase 1: Implémentation du squelette (1-2h)
- [x] Créer `MultiPassParser` de base
- [ ] Implémenter `_extract_from_family()` complet
- [ ] Implémenter `_extract_from_notes()`
- [ ] Implémenter `_extract_from_pevt()`
- [ ] Implémenter `_extract_from_relations()`
- [ ] Tests unitaires des extracteurs

### Phase 2: Consolidation (30min)
- [ ] Affiner `PersonAccumulator.build_person()`
- [ ] Tests de fusion avec différents contextes
- [ ] Tests de priorité du sexe

### Phase 3: Construction des relations (1h)
- [ ] Implémenter `_build_families()`
- [ ] Lier enfants → parents
- [ ] Lier témoins → événements
- [ ] Tests d'intégration complets

### Phase 4: Intégration (30min)
- [ ] Ajouter option `use_multipass=True` dans `GeneWebParser`
- [ ] Benchmarks de performance
- [ ] Documentation
- [ ] Migration progressive

**Total estimé : 4-5 heures de développement**

---

## 💡 Stratégie de migration progressive

### Option A: Migration immédiate
- Remplacer `_build_genealogy()` par `MultiPassParser`
- Avantages: Résultats immédiats (100 % des personnes)
- Risques: Possibles régressions à court terme

### Option B: Migration par feature flag  
```python
parser = GeneWebParser(use_multipass=True)  # Nouveau mode
parser = GeneWebParser(use_multipass=False) # Mode actuel (par défaut)
```
- Avantages: Transition en douceur, tests A/B
- Inconvénient: Maintenance de 2 parsers temporairement

### Option C: Migration hybride
- Garder l'approche actuelle pour les cas simples
- Utiliser multi-passes pour les fichiers complexes (>1000 personnes)
- Avantages: Meilleur des deux mondes
- Inconvénient: Complexité accrue

---

## 🎯 Recommandation

**Option B (feature flag)** pour :
- Valider que le multi-passes atteint 100% sur la base de référence locale
- Comparer les performances
- Migrer progressivement
- Garder un fallback en cas de problème

---

## 📝 Exemple d'utilisation future

```python
from geneweb_py import GeneWebParser

# Mode actuel (incrémental)
parser_v1 = GeneWebParser()
genealogy = parser_v1.parse_file("sample_tree.gw")
# → ~73 % des personnes

# Mode multi-passes (nouveau)
parser_v2 = GeneWebParser(use_multipass=True)
genealogy = parser_v2.parse_file("sample_tree.gw")
# → 100 % des personnes ✅
```

---

## 🔍 Analyse d'impact

### Code à modifier
1. `GeneWebParser.__init__()` - ajouter paramètre `use_multipass`
2. `GeneWebParser._build_genealogy()` - router vers MultiPassParser si actif
3. Tests existants - vérifier compatibilité

### Code à créer
1. `MultiPassParser` complet (~500 lignes)
2. Tests spécifiques multi-passes (~200 lignes)
3. Benchmarks comparatifs

### Risques
- 🟡 Changement majeur d'architecture
- 🟡 Possibles différences de comportement
- 🟢 Atténué par feature flag et tests

---

## 📈 Prochaines étapes

### Immédiat (si décision de continuer)
1. Implémenter `_extract_from_family()` complet
2. Tester sur la base de référence locale
3. Comparer les résultats

### Alternative (si on garde l'actuel)
1. Documenter les 73% de couverture actuelle
2. Identifier les 27% manquants précisément
3. Corriger incrémentalement

---

**Décision à prendre :** Voulez-vous que je continue l'implémentation du MultiPassParser maintenant, ou préférez-vous consolider l'état actuel (73% fonctionnel) et documenter ?

**État actuel :**
- ✅ API fonctionnelle
- ✅ ~73 % des personnes
- ✅ Tests passants
- ✅ Prêt pour utilisation

**État futur (multi-passes) :**
- ⏳ 4-5h de développement
- 🎯 100 % des personnes
- 🎯 Meilleure qualité de données
- 🎯 Architecture plus robuste

