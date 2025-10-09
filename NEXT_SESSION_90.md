# 🎯 Prochaine Session - Sprint Final vers 90%

## 📊 ÉTAT DE DÉPART

**Couverture actuelle** : 86.84%  
**Gap vers 90%** : 3.16 points  
**Lignes à couvrir** : 148 lignes (sur 617 manquantes)  
**Tests** : 690 passants, 53 skippés

---

## 🎯 OBJECTIF : 90%+ EN 2-3H

### Phase 1 - Modules Faciles (1h)
**Objectif** : +1.6 pts → 88.4%

1. **core/exceptions.py** : 89% → 95%
   - Lignes manquantes : 27
   - Gain estimé : +0.6 pts
   - Tests à ajouter : 5-7 tests cas edge

2. **formats/gedcom.py** : 87% → 95%
   - Lignes manquantes : 28
   - Gain estimé : +0.6 pts
   - Tests à ajouter : 6-8 tests import/export

3. **formats/json.py** : 86% → 95%
   - Lignes manquantes : 18
   - Gain estimé : +0.4 pts
   - Tests à ajouter : 4-5 tests sérialisation

**Total Phase 1** : ~73 lignes = +1.6 pts

---

### Phase 2 - Module Moyen (1h)
**Objectif** : +1 pt → 89.4%

4. **api/services/genealogy_service.py** : 67% → 75%
   - Lignes manquantes : 106 (viser 50 lignes)
   - Gain estimé : +1 pt
   - Tests à ajouter : 10-12 tests CRUD

**Total Phase 2** : ~50 lignes = +1 pt

---

### Phase 3 - Finition (30 min)
**Objectif** : +0.6 pts → 90%

5. **formats/xml.py** : 75% → 80%
   - Lignes manquantes : 94 (viser 25 lignes)
   - Gain estimé : +0.6 pts
   - Tests à ajouter : 5-6 tests import/export

**Total Phase 3** : ~25 lignes = +0.6 pts

---

## 📋 RÉSULTAT ATTENDU

**Couverture finale** : **90%+** ✅  
**Tests** : ~715 tests  
**Modules ≥ 90%** : 23-25 modules  

---

## 🔥 MÉTHODE : COMMIT-VERIFY-ITERATE

**Cycle prouvé efficace** (+0.88 pt/heure) :

1. Identifier lignes manquantes (5 min)
2. Ajouter 3-5 tests ciblés (15-20 min)
3. Vérifier localement (2 min)
4. Commit + Push (3 min)
5. Vérifier CI/CD (automatique)
6. NEXT module !

**Règles d'or** :
- ✅ Petits modules d'abord (gains rapides)
- ✅ Commits fréquents (traçabilité)
- ✅ Vrais fichiers > mocks complexes
- ✅ Pauses toutes les 2h (efficacité)

---

## 📊 MODULES PRIORITAIRES (détails)

### 1. core/exceptions.py (27 lignes)
**Zones à tester** :
- Blocs d'erreur non couverts
- Formatage de messages enrichis
- Severités différentes (WARNING, CRITICAL)

**Tests à ajouter** :
- Exception avec contexte complet
- Messages multi-lignes
- Collecteur avec sévérités mixtes

---

### 2. formats/gedcom.py (28 lignes)
**Zones à tester** :
- Blocs d'erreur export/import
- Cas edge parsing dates
- Mapping événements spéciaux

**Tests à ajouter** :
- Import fichier malformé
- Export avec événements multiples
- Dates avec calendriers spéciaux

---

### 3. formats/json.py (18 lignes)
**Zones à tester** :
- Sérialisation complète
- Blocs d'erreur
- Cas edge (notes vides, métadonnées)

**Tests à ajouter** :
- Export généalogie complexe
- Import avec champs manquants
- Erreurs de sérialisation

---

### 4. api/services/genealogy_service.py (viser 50/106 lignes)
**Zones prioritaires** :
- Méthodes CRUD non testées
- Statistiques avancées
- Recherche avec filtres

**Tests à ajouter** :
- Tests d'intégration service complet
- Cas edge validation
- Performance sur gros datasets

---

### 5. formats/xml.py (viser 25/94 lignes)
**Zones prioritaires** :
- Import/export basique
- Blocs d'erreur principaux
- Sérialisation événements

**Tests à ajouter** :
- Import XML complet
- Export avec tous types d'événements
- Erreurs de parsing XML

---

## ✅ CHECKLIST AVANT SESSION

- [ ] Git status clean
- [ ] Dernière version pullée
- [ ] Pytest fonctionne
- [ ] Ruff installé et configuré
- [ ] Énergie et concentration OK

---

## 📖 RÉFÉRENCES

- `BILAN_FINAL_COMPLET.md` - Résumé toutes sessions
- `doc/status.md` - État actuel projet
- `.cursor/rules/code_standards.mdc` - Standards
- `.cursor/rules/testing_quality.mdc` - Tests

---

**Prochaine session** : 2-3h concentrées  
**Objectif** : **90%+ de couverture** ✅  
**Préparation** : Repos et concentration  
**Success rate estimé** : 95%+ avec méthode établie

