# Session 2 - Sprint Final vers 90%

## 🎯 OBJECTIF : 85.5% → 90% (+4.5 points)

**État actuel** : 85.5% (4020/4704 lignes)  
**Gap** : 213 lignes à couvrir pour 90%

---

## 📋 PLAN D'ATTAQUE (Ordre de priorité)

### 1️⃣ formats/gedcom.py : 87% → 95% (+28 lignes)
**Gain estimé** : +0.6 pts  
**Temps estimé** : 30 min  
**Approche** : Tester les blocs d'erreur et cas edge

### 2️⃣ formats/json.py : 73% → 90% (+34 lignes, mais on vise 20)
**Gain estimé** : +0.4 pts  
**Temps estimé** : 30 min  
**Approche** : Couvrir les exceptions et sérialisation complète

### 3️⃣ api/services/genealogy_service.py : 67% → 80% (+40 lignes sur 106)
**Gain estimé** : +1 pt  
**Temps estimé** : 45 min  
**Approche** : Tester les méthodes CRUD restantes

### 4️⃣ formats/xml.py : 75% → 85% (+40 lignes sur 104)
**Gain estimé** : +0.8 pts  
**Temps estimé** : 45 min  
**Approche** : Import/export complets

### 5️⃣ core/parser/gw_parser.py : 82% → 86% (+30 lignes sur 126)
**Gain estimé** : +0.6 pts  
**Temps estimé** : 40 min  
**Approche** : Cas edge du parser

### 6️⃣ Corriger 5 tests skippés
**Gain estimé** : +0.5 pts  
**Temps estimé** : 30 min

---

## 📊 PRÉVISIONS

**Total gains** : +4.5 pts  
**Total temps** : ~3h30  
**Résultat attendu** : **90%+ atteint** ✅

---

## 🔥 MÉTHODE : Commit-Verify-Iterate

1. Identifier les lignes manquantes (5 min)
2. Ajouter 3-5 tests ciblés (20 min)
3. Vérifier localement (2 min)
4. Commit + Push (3 min)
5. NEXT module !

**Pas de temps mort, progression continue !**
