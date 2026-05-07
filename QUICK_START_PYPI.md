# Démarrage rapide (installation PyPI)

Ce guide s’adresse aux utilisateurs qui installent **geneweb-py** depuis [PyPI](https://pypi.org/project/geneweb-py/). Objectif : parser un fichier GeneWeb, exporter en GEDCOM/JSON et lancer l’API en quelques minutes.

**Prérequis :** Python 3.8 à 3.12.

## 1. Installer la bibliothèque

```bash
pip install geneweb-py
```

- **Extras utiles :** `pip install geneweb-py[api]` pour l’API FastAPI (FastAPI, Uvicorn, Pydantic, etc.).
- **Développement :** `pip install geneweb-py[dev]` (tests, lint, types).

## 2. Parser un fichier `.gw`

L’encodage du fichier est détecté automatiquement (via `chardet`) : ne forcez pas d’encodage en dur pour des fichiers réels.

Remplacez `chemin/vers/fichier.gw` par votre fichier :

```python
from pathlib import Path

from geneweb_py import GeneWebParser

parser = GeneWebParser()
genealogy = parser.parse_file(Path("chemin/vers/fichier.gw"))

print(f"Personnes : {len(genealogy.persons)}")
print(f"Familles : {len(genealogy.families)}")
```

**Sans fichier sur le disque** (chaîne minimale valide, pratique pour un test) :

```python
from geneweb_py import GeneWebParser

gw_content = """fam DUPONT Jean MARTIN Marie
end fam
"""

parser = GeneWebParser(validate=False)
genealogy = parser.parse_string(gw_content)
print(len(genealogy.persons), len(genealogy.families))
```

## 3. Exporter en GEDCOM et JSON

Les exporteurs refusent une généalogie totalement vide (aucune personne ni famille). Parsez d’abord un `.gw` qui contient au moins une personne ou une famille.

```python
from pathlib import Path

from geneweb_py import GeneWebParser
from geneweb_py.formats import GEDCOMExporter, JSONExporter

genealogy = GeneWebParser(validate=False).parse_string(
    """fam DUPONT Jean MARTIN Marie
end fam
"""
)

GEDCOMExporter().export(genealogy, Path("sortie.ged"))
JSONExporter().export(genealogy, Path("sortie.json"))
```

## 4. Lancer l’API REST

Installez l’extra **api**, puis démarrez Uvicorn sur l’application FastAPI du package :

```bash
pip install "geneweb-py[api]"
uvicorn geneweb_py.api.main:app --host 127.0.0.1 --port 8000 --reload
```

- Documentation interactive : **http://127.0.0.1:8000/docs**
- Alternative équivalente en Python :

```python
import uvicorn

from geneweb_py.api import app

uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Note :** le script `run_api.py` à la racine du dépôt Git est surtout utile aux contributeurs qui clonent le repo. Depuis une installation PyPI pure, la commande `uvicorn geneweb_py.api.main:app` ci-dessus est la voie recommandée.

## 5. Exemple tout-en-un (copier-coller, exécutable)

Le script suivant n’a besoin d’aucun fichier externe (Python 3.8+) :

```python
import tempfile
from pathlib import Path

from geneweb_py import GeneWebParser
from geneweb_py.formats import GEDCOMExporter, JSONExporter

gw_content = """fam DUPONT Jean MARTIN Marie
end fam
"""

def main():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        gw_path = base / "sample.gw"
        gw_path.write_text(gw_content, encoding="utf-8")

        genealogy = GeneWebParser(validate=False).parse_file(gw_path)
        print("Personnes :", len(genealogy.persons))
        print("Familles :", len(genealogy.families))

        ged_path = base / "sortie.ged"
        json_path = base / "sortie.json"
        GEDCOMExporter().export(genealogy, ged_path)
        JSONExporter().export(genealogy, json_path)
        print("GEDCOM écrit :", ged_path.stat().st_size, "octets")
        print("JSON écrit :", json_path.stat().st_size, "octets")


if __name__ == "__main__":
    main()
```

## Pour aller plus loin

- Guide principal : [README.md](README.md)
- Index documentation : [DOCUMENTATION.md](DOCUMENTATION.md)
- Format `.gw` : [doc/geneweb/gw_format_documentation.md](doc/geneweb/gw_format_documentation.md)
