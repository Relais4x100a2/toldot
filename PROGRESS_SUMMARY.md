# Résumé Session Perfectionniste - Vers 90%

## 📊 ÉTAT ACTUEL

**Couverture globale : 85.91%**  
**Objectif : 90%**  
**Gap : 4.09 points (193 lignes à couvrir)**

**Tests : 646 passants, 52 skippés**

## ✅ MODULES DÉJÀ À 90%+

1. ✅ api/main.py : 100% (parfait !)
2. ✅ api/models/event.py : 90% (nouveau)
3. ✅ core/date.py : 94% (nouveau)
4. ✅ api/routers/families.py : 95%
5. ✅ core/genealogy.py : 95%
6. ✅ core/person.py : 93%
7. ✅ api/models/family.py : 94%
8. ✅ api/models/person.py : 92%
9. ✅ core/parser/lexical.py : 96%
10. ✅ core/parser/streaming.py : 97%
11. ✅ core/parser/syntax.py : 90%

**Total : 11 modules ≥ 90%**

## 🎯 MODULES < 90% RESTANTS

### Priorité HAUTE (grosse impact, <30 lignes)
- api/routers/events.py : 86.4% (12 lignes)
- core/event.py : 85.1% (13 lignes)
- core/validation.py : 88.5% (14 lignes)
- formats/json.py : 85.7% (18 lignes)
- core/family.py : 85.4% (21 lignes)
- formats/gedcom.py : 87.2% (28 lignes)

**Total : 6 modules, 106 lignes** → Si couverture à 90%, gain ~2 points

### Priorité MOYENNE (gros gains possibles)
- api/routers/genealogy.py : 68.6% (48 lignes)
- api/services/genealogy_service.py : 67.1% (106 lignes)
- formats/xml.py : 73% (104 lignes)
- core/parser/gw_parser.py : 82.3% (126 lignes)

**Total : 4 modules, 384 lignes** → Si amélioration partielle, gain ~2-3 points

## 🎯 STRATÉGIE POUR ATTEINDRE 90%

### Option A - Accumulation petits gains (2h)
Améliorer les 6 modules priorité HAUTE vers 95%+
→ Gain estimé : +2-3 points = **88-89%**

### Option B - Gros module (4h)
Améliorer core/parser/gw_parser.py : 82% → 95%
→ Gain : ~3 points = **89%**

### Option C - Hybride (recommandé, 3h)
1. 6 modules faciles → 90%+ (1.5h) = +2 pts
2. api/services → 80%+ (1h) = +1.5 pts  
3. Quelques fonctions parser (0.5h) = +0.5 pt

**Total estimé : 90%+ atteint ! 🎯**

## 💡 RECOMMANDATION

**Suivre Option C** :
- Gains rapides et mesurables
- Risque faible
- Progression continue
- Objectif 90% atteignable en 3h
