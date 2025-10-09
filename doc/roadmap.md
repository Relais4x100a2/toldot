# Roadmap geneweb-py

Ce document décrit la vision et les axes d'évolution à moyen/long terme. Les éléments ci-dessous peuvent évoluer selon les retours utilisateurs et les priorités du projet.

## Parser et compatibilité GeneWeb
- Support complet de tous les blocs GeneWeb restants (témoins familiaux, sources/commentaires avancés, événements familiaux complexes)
- Tolérance accrue aux formats incomplets (dates vides, champs partiels), avec erreurs contextualisées
- Parsing streaming pour très gros fichiers (>50MB)

## API et fonctionnalités avancées
- Recherche multi-critères et indexation (nom, dates, lieux)
- Statistiques généalogiques avancées (longévité, distribution géographique, tailles de familles, timeline)
- Export/Import personnalisables (filtres, options, plages de dates)

## Qualité, performance et DX
- Couverture de code élevée et stable (≥ 80–90%)
- Optimisations de performance (temps de parsing, mémoire)
- Messages d'erreur enrichis et validation gracieuse

## Extensibilité
- Plugins/points d'extension pour nouveaux formats ou enrichissements
- Hooks de parsing/validation

## Documentation et écosystème
- Documentation API générée automatiquement (Sphinx/OpenAPI) et exemples complets
- Guides d’intégration et best practices


