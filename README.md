# geneweb-py

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/guillaumecayeux/geneweb-py/workflows/tests/badge.svg)](https://github.com/guillaumecayeux/geneweb-py/actions)

Librairie Python complète pour parser, manipuler et convertir les fichiers généalogiques au format GeneWeb (.gw).

## 🚀 Fonctionnalités

- **Parser complet** : Lecture et parsing des fichiers .gw avec support gwplus ✅
- **Modèles de données** : Représentation structurée des personnes, familles et événements ✅
- **API REST moderne** : FastAPI avec endpoints complets pour CRUD ✅
- **Validation** : Vérification de cohérence des données généalogiques ✅
- **Conversion** : Export/import vers GEDCOM, JSON, XML et autres formats ✅
- **Performance** : Optimisé pour les grandes bases de données ✅

## 📦 Installation

```bash
pip install geneweb-py
```

Pour le développement :

```bash
pip install geneweb-py[dev]
```

## 🎯 Utilisation rapide

### Parser un fichier .gw

```python
from geneweb_py import GeneWebParser

# Créer le parser
parser = GeneWebParser()

# Parser un fichier
genealogy = parser.parse_file("ma_famille.gw")

# Afficher des statistiques
print(f"Nombre de personnes : {len(genealogy.persons)}")
print(f"Nombre de familles : {len(genealogy.families)}")
```

### API REST avec FastAPI

```python
# Démarrer l'API
from geneweb_py.api import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)

# L'API sera disponible sur http://localhost:8000/docs
```

### Rechercher une personne

```python
# Rechercher par nom
person = genealogy.find_person("CORNO", "Joseph")

if person:
    print(f"Nom : {person.full_name}")
    print(f"Naissance : {person.birth_date}")
    print(f"Décès : {person.death_date}")
    
    # Obtenir les familles
    families = person.get_families()
    for family in families:
        print(f"Époux(se) : {family.spouse(person)}")
```

### Utiliser l'API REST

```python
# Via l'API REST
import requests

# Lister les personnes
response = requests.get("http://localhost:8000/api/v1/persons")
print(f"Personnes : {response.json()}")

# Obtenir une personne
person = requests.get("http://localhost:8000/api/v1/persons/1")
print(f"Personne : {person.json()}")
```

### Conversion de formats

```python
from geneweb_py.formats import GEDCOMExporter, JSONExporter, XMLExporter

# Export vers GEDCOM
gedcom_exporter = GEDCOMExporter()
gedcom_exporter.export(genealogy, "ma_famille.ged")

# Export vers JSON
json_exporter = JSONExporter()
json_exporter.export(genealogy, "ma_famille.json")

# Export vers XML
xml_exporter = XMLExporter()
xml_exporter.export(genealogy, "ma_famille.xml")

# Import depuis JSON
from geneweb_py.formats import JSONImporter
json_importer = JSONImporter()
imported_genealogy = json_importer.import_from_file("ma_famille.json")
```

## 📚 Documentation

- [Documentation complète](https://geneweb-py.readthedocs.io)
- [Documentation de l'API](http://localhost:8000/docs) (Swagger UI)
- [Exemples d'utilisation](examples/)
- [Format GeneWeb](doc/geneweb/gw_format_documentation.md)
- [Geneweb documentation by the community](https://web.archive.org/web/20250802144922/https://geneweb.tuxfamily.org/wiki/GeneWeb)

## 🧪 Tests

```bash
# Exécuter tous les tests
pytest

# Tests avec couverture (78% actuellement)
pytest --cov=geneweb_py

# Tests d'intégration seulement
pytest -m integration

# Tests de l'API
pytest tests/api/
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez [DEVELOPMENT.md](DEVELOPMENT.md) pour plus d'informations sur le développement.

## 📄 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

## 🔗 Liens utiles

- [GeneWeb GitHub repo](http://geneweb.org/)
- [Format .gw](doc/geneweb/gw_format_documentation.md)
- [Geneweb documentation by the community](https://web.archive.org/web/20250802144922/https://geneweb.tuxfamily.org/wiki/GeneWeb)
- [Issues](https://github.com/guillaumecayeux/geneweb-py/issues)
