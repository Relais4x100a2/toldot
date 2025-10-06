#!/usr/bin/env python3
"""
Exemple d'utilisation des convertisseurs de formats de geneweb-py.

Ce script démontre comment utiliser les différents convertisseurs
pour exporter et importer des données généalogiques vers/depuis
différents formats (GEDCOM, JSON, XML).
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from geneweb_py import GeneWebParser
from geneweb_py.formats import GEDCOMExporter, JSONExporter, XMLExporter
from geneweb_py.formats import GEDCOMImporter, JSONImporter, XMLImporter


def main():
    """Fonction principale de démonstration."""
    print("=== Démonstration des convertisseurs de formats ===\n")
    
    # 1. Parser un fichier .gw existant
    print("1. Parsing d'un fichier .gw...")
    parser = GeneWebParser()
    
    # Utiliser le fichier d'exemple
    gw_file = Path(__file__).parent.parent / "doc" / "baseGWexamples" / "sample_tree.gw"
    
    if not gw_file.exists():
        print(f"❌ Fichier .gw non trouvé : {gw_file}")
        print("Création d'une généalogie d'exemple...")
        genealogy = create_example_genealogy()
    else:
        try:
            genealogy = parser.parse_file(str(gw_file))
            print(f"✅ Fichier .gw parsé : {len(genealogy.persons)} personnes, {len(genealogy.families)} familles")
        except Exception as e:
            print(f"❌ Erreur lors du parsing : {e}")
            print("Création d'une généalogie d'exemple...")
            genealogy = create_example_genealogy()
    
    print()
    
    # 2. Export vers GEDCOM
    print("2. Export vers GEDCOM...")
    gedcom_content = None
    try:
        gedcom_exporter = GEDCOMExporter()
        gedcom_content = gedcom_exporter.export_to_string(genealogy)
        
        # Sauvegarder le fichier GEDCOM
        gedcom_file = Path(__file__).parent / "output" / "genealogy.ged"
        gedcom_file.parent.mkdir(exist_ok=True)
        gedcom_exporter.export(genealogy, str(gedcom_file))
        
        print(f"✅ Export GEDCOM réussi : {gedcom_file}")
        print(f"   Taille : {len(gedcom_content)} caractères")
        print(f"   Lignes : {len(gedcom_content.splitlines())}")
    except Exception as e:
        print(f"❌ Erreur export GEDCOM : {e}")
    
    print()
    
    # 3. Export vers JSON
    print("3. Export vers JSON...")
    json_content = None
    try:
        json_exporter = JSONExporter(indent=2)
        json_content = json_exporter.export_to_string(genealogy)
        
        # Sauvegarder le fichier JSON
        json_file = Path(__file__).parent / "output" / "genealogy.json"
        json_exporter.export(genealogy, str(json_file))
        
        print(f"✅ Export JSON réussi : {json_file}")
        print(f"   Taille : {len(json_content)} caractères")
    except Exception as e:
        print(f"❌ Erreur export JSON : {e}")
    
    print()
    
    # 4. Export vers XML
    print("4. Export vers XML...")
    xml_content = None
    try:
        xml_exporter = XMLExporter(pretty_print=True)
        xml_content = xml_exporter.export_to_string(genealogy)
        
        # Sauvegarder le fichier XML
        xml_file = Path(__file__).parent / "output" / "genealogy.xml"
        xml_exporter.export(genealogy, str(xml_file))
        
        print(f"✅ Export XML réussi : {xml_file}")
        print(f"   Taille : {len(xml_content)} caractères")
    except Exception as e:
        print(f"❌ Erreur export XML : {e}")
    
    print()
    
    # 5. Test d'import depuis JSON
    print("5. Test d'import depuis JSON...")
    if json_content:
        try:
            json_importer = JSONImporter()
            imported_genealogy = json_importer.import_from_string(json_content)
            
            print(f"✅ Import JSON réussi : {len(imported_genealogy.persons)} personnes, {len(imported_genealogy.families)} familles")
            
            # Vérifier que les données sont identiques
            if len(imported_genealogy.persons) == len(genealogy.persons):
                print("   ✅ Nombre de personnes identique")
            else:
                print("   ⚠️  Nombre de personnes différent")
                
        except Exception as e:
            print(f"❌ Erreur import JSON : {e}")
    else:
        print("❌ Impossible de tester l'import JSON (export échoué)")
    
    print()
    
    # 6. Test d'import depuis XML
    print("6. Test d'import depuis XML...")
    if xml_content:
        try:
            xml_importer = XMLImporter()
            imported_genealogy = xml_importer.import_from_string(xml_content)
            
            print(f"✅ Import XML réussi : {len(imported_genealogy.persons)} personnes, {len(imported_genealogy.families)} familles")
            
            # Vérifier que les données sont identiques
            if len(imported_genealogy.persons) == len(genealogy.persons):
                print("   ✅ Nombre de personnes identique")
            else:
                print("   ⚠️  Nombre de personnes différent")
                
        except Exception as e:
            print(f"❌ Erreur import XML : {e}")
    else:
        print("❌ Impossible de tester l'import XML (export échoué)")
    
    print()
    
    # 7. Afficher un aperçu des fichiers générés
    print("7. Aperçu des fichiers générés...")
    output_dir = Path(__file__).parent / "output"
    
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            print(f"   📄 {file_path.name} ({file_path.stat().st_size} octets)")
    
    print("\n=== Démonstration terminée ===")


def create_example_genealogy():
    """Crée une généalogie d'exemple pour la démonstration."""
    from geneweb_py.core.genealogy import Genealogy
    from geneweb_py.core.person import Person, Gender
    from geneweb_py.core.family import Family
    from geneweb_py.core.date import Date
    from geneweb_py.core.event import Event
    
    # Créer la généalogie
    genealogy = Genealogy()
    
    # Créer des personnes
    jean = Person(
        last_name="DUPONT",
        first_name="Jean",
        gender=Gender.MALE,
        birth_date=Date(year=1950, month=3, day=15),
        birth_place="Paris, France",
        occupation="Ingénieur"
    )
    
    marie = Person(
        last_name="MARTIN",
        first_name="Marie",
        gender=Gender.FEMALE,
        birth_date=Date(year=1952, month=7, day=22),
        birth_place="Lyon, France",
        occupation="Médecin"
    )
    
    pierre = Person(
        last_name="DUPONT",
        first_name="Pierre",
        gender=Gender.MALE,
        birth_date=Date(year=1980, month=5, day=10),
        birth_place="Paris, France"
    )
    
    # Créer une famille
    family = Family(
        family_id="F001",
        husband_id="P001",  # ID de Jean
        wife_id="P002",     # ID de Marie
        marriage_date=Date(year=1975, month=6, day=14),
        marriage_place="Paris, France"
    )
    
    # Ajouter l'enfant
    from geneweb_py.core.family import Child, ChildSex
    child = Child(
        person_id="P003",  # ID de Pierre
        sex=ChildSex.MALE
    )
    family.children.append(child)
    
    # Ajouter des événements
    from geneweb_py.core.event import EventType
    jean.add_event(Event(
        event_type=EventType.GRADUATION,
        date=Date(year=1972, month=6),
        place="École Polytechnique, Paris"
    ))
    jean.events[0].add_note("Diplôme d'ingénieur")
    
    marie.add_event(Event(
        event_type=EventType.GRADUATION,
        date=Date(year=1976, month=6),
        place="Faculté de Médecine, Lyon"
    ))
    marie.events[0].add_note("Doctorat en médecine")
    
    # Ajouter à la généalogie
    genealogy.add_person(jean)
    genealogy.add_person(marie)
    genealogy.add_person(pierre)
    genealogy.add_family(family)
    
    return genealogy


if __name__ == "__main__":
    main()
