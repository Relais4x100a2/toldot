# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support des apostrophes dans les identifiants (`d'Arc`, `O'Brien`, `L'Église`)
- Support des caractères spéciaux dans les occupations (virgules, parenthèses, apostrophes, tirets)
- Déduplication intelligente avec numéros d'occurrence (.1, .2, etc.)
- Support des nouveaux blocs GeneWeb : `notes-db`, `page-ext`, `wizard-note`
- Parsing des enfants avec sexes et occupations
- Parsing des témoins avec toutes leurs informations
- Tests complets pour toutes les nouvelles fonctionnalités (12 tests)

### Changed
- Amélioration du parser lexical pour reconnaître `h` comme token spécial `H`
- Modification du parser syntaxique pour consommer tous les tokens d'occupation
- Amélioration du parser principal pour reconstituer les occupations complètes
- Correction du parsing des sexes dans le parser lexical

### Fixed
- Parsing correct des noms français et internationaux avec apostrophes
- Parsing correct d'occupations complexes avec caractères spéciaux
- Aucune perte de données lors de la déduplication des personnes
- Parsing complet de toutes les informations des enfants et témoins
- Support complet des fonctionnalités avancées de GeneWeb

## [0.1.0] - 2024-01-XX

### Added
- Structure du projet avec `pyproject.toml`
- Modèles de données complets (Date, Person, Family, Event, Genealogy)
- Gestion d'erreurs professionnelle avec exceptions spécifiques
- Parser lexical pour tokenisation des fichiers .gw
- Parser syntaxique pour analyse des blocs structurés
- Parser principal avec API simple et robuste
- API REST avec FastAPI et endpoints complets
- Conversion de formats (GEDCOM, JSON, XML)
- Tests exhaustifs avec couverture de code
- Documentation complète et exemples d'utilisation

### Changed
- Architecture modulaire respectant les standards Python
- Type hints obligatoires pour toutes les fonctions publiques
- Docstrings en français pour les APIs publiques
- Formatage avec Black et ligne de 88 caractères

### Fixed
- Gestion gracieuse des erreurs de parsing
- Validation de cohérence des données généalogiques
- Support des formats de dates complexes GeneWeb
- Parsing efficace avec gestion mémoire optimisée
