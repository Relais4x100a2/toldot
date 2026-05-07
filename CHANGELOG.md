# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **API** : Statistiques avancées dans `get_stats` (longévité, top lieux, histogramme enfants/famille).
- **API** : Filtres recherche personnes par plage d'année (naissance/décès) et par lieu.
- **API** : Endpoint `POST /genealogy/validate` branché sur `Genealogy.validate_consistency` avec option `strict`.
- **Core** : Méthode `Date.sort_year()` pour les filtres temporels.

### Changed
- **Core** : `Genealogy.validate_consistency(strict=True)` remplace les erreurs stockées à chaque passe (pas de cumul entre appels).
- **API** : Filtres année naissance/décès par chevauchement avec les segments OR/BETWEEN (`Date.filter_years_for_range`).
- **API** : Recherche lieu personnes avec NFKC + `casefold` ; exposition des query params année/lieu sur `GET /persons/`.
- **API** : Message HTTP de `POST /genealogy/validate` reflète `is_valid` ; doc OpenAPI du mode `strict` précisée.
- **Structure** : Migration vers structure `src/` (meilleure pratique PyPA)
  - Package déplacé de `geneweb_py/` vers `src/geneweb_py/`
  - Mise à jour de `pyproject.toml` pour pointer vers `src/`
  - Mise à jour de tous les scripts et tests
  - Suppression des dossiers vides (`utils/`, `tests/`, `examples/` dans le package)
- **Email** : Mise à jour vers `guillaume.cayeux@relais4x100a2.fr`

### Documentation
- 🧹 **Nettoyage documentation** : Suppression de 24 fichiers Markdown non conformes à la racine
- 📊 **Métriques de tests / couverture** : source unique **[doc/status.md](doc/status.md)** ; tendance CI sur [Codecov](https://codecov.io/gh/Relais4x100a2/geneweb-py) ; README et index sans pourcentages dupliqués divergents
- 📝 **Conformité structure** : Seuls README.md, CHANGELOG.md, DOCUMENTATION.md à la racine
- 🏗️ **Organisation** : Documentation conforme aux règles Cursor du projet
- Consolidation complète de la documentation
- Suppression des fichiers de résumés de sessions obsolètes
- Restructuration de la section documentation dans README
- Mise à jour du statut du projet et de l'architecture

## [0.1.0] - 2025-10-09

### Added
- ✨ **Parser avancé** : Support des apostrophes, caractères spéciaux, numéros d'occurrence
- ✨ **Nouveaux blocs** : Support `notes-db`, `page-ext`, `wizard-note`
- ✨ **Optimisations** : Mode streaming automatique pour fichiers >10MB (~80% réduction mémoire)
- ✨ **Validation gracieuse** : Mode strict/gracieux avec collecte d'erreurs
- ✨ **Messages enrichis** : Erreurs contextuelles avec ligne, token, suggestions
- ✨ **Tests PyPI** : 43 tests (packaging, compatibilité, sécurité)
- ✨ **CI/CD** : GitHub Actions pour tests et publication automatisée
- ✨ **Scripts** : Validation PyPI bash et Python
- 📚 **Documentation** : 7 guides complets (performance, publication, tests)

### Performance
- ⚡ **Streaming** : ~80% réduction mémoire sur gros fichiers
- ⚡ **CPU** : ~15-20% plus rapide sur petits fichiers
- ⚡ **Cache LRU** : Patterns regex mis en cache
- ⚡ **__slots__** : ~40% réduction mémoire par token

### Tests & Qualité
- ✅ **Suite de tests étendue** : à la v0.1.0, couverture et volumétrie conformes aux objectifs du projet (détail historique : tag de release, rapport d’époque)
- ✅ **Multi-versions** : Python 3.8-3.12
- ✅ **Multi-OS** : Linux, macOS, Windows
- ✅ **Structure consolidée** : 18 fichiers de tests unitaires

### API & Formats
- 🔌 **API REST** : FastAPI avec endpoints CRUD complets
- 🔄 **Conversions** : GEDCOM, JSON, XML (import/export)

### Architecture
- 📦 Structure modulaire complète (core, api, formats, utils)
- 🏗️ Modèles de données avec dataclasses et validation
- 🛡️ Gestion d'erreurs avec exceptions spécifiques
- 🎨 Type hints et docstrings françaises
- 🔧 Configuration via pyproject.toml
