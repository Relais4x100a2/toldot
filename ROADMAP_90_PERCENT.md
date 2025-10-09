# Roadmap 90% Couverture - Approche Perfectionniste

## 🎯 Objectif : 90%+ couverture, 0 tests skippés, v1.0.0

**État actuel :** 83.3% couverture, 596 tests, 48 skippés
**Objectif final :** 90%+ couverture, 650+ tests, 0 skippés critiques

## 📊 Priorisation par Impact

### Niveau 1 - CRITIQUE (Impact majeur : +61%)
- [ ] api/routers/genealogy.py : 29% → 90% (109 lignes, +61 points)
  - Import/export endpoints  
  - Search global
  - Health check
  - Stats complètes

### Niveau 2 - TRÈS IMPORTANT (Impact fort : +36%)
- [ ] api/services/genealogy_service.py : 54% → 90% (147 lignes, +36 points)
  - Méthodes CRUD non testées
  - Recherche avancée
  - Validation métier

### Niveau 3 - IMPORTANT (Impact moyen : +15-20%)
- [ ] formats/xml.py : 75% → 90% (94 lignes, +15 points)
- [ ] core/parser/gw_parser.py : 82% → 95% (126 lignes, +13 points)
- [ ] api/middleware/error_handler.py : 63% → 90% (17 lignes, +27 points)

### Niveau 4 - CONSOLIDATION (Impact faible : +5-10%)
- [ ] 10 modules entre 85-89% → 90%+
- [ ] Tests skippés : 48 → 0

## 📅 Planning

**Semaine 1 : Modules API (Niv 1-2)**
- Jour 1-2 : api/routers/genealogy.py
- Jour 3-4 : api/services (compléter)
- Jour 5 : api/middleware

**Semaine 2 : Formats et Parser (Niv 3)**  
- Jour 1-2 : formats/xml.py
- Jour 3-4 : core/parser/gw_parser.py
- Jour 5 : Consolidation 10 modules

**Semaine 3 : Tests skippés + v1.0.0**
- Jour 1-2 : Corriger tous tests skippés
- Jour 3 : CI/CD validation
- Jour 4 : Documentation v1.0.0
- Jour 5 : Publication PyPI v1.0.0

## 🎯 Métrique de succès

✅ Couverture ≥ 90%
✅ Tous modules critiques ≥ 95%
✅ 0 tests skippés (ou documentés "won't fix")
✅ 650+ tests passants
✅ Tous workflows CI verts
