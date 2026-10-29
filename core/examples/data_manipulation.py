#!/usr/bin/env python3
"""
Exemple de manipulation des données parsées par geneweb-py

Ce script montre comment accéder, rechercher et manipuler les données
généalogiques après parsing d'un fichier .gw
"""

from geneweb_py import GeneWebParser
from geneweb_py.core.person import Gender
from geneweb_py.core.family import MarriageStatus
from geneweb_py.core.event import EventType, PersonalEvent
from geneweb_py.core.date import Date


def main():
    """Exemple principal de manipulation des données"""
    
    # 1. Parser le fichier
    print("🔄 Parsing du fichier...")
    parser = GeneWebParser(use_multipass=True)
    genealogy = parser.parse_file('tests/fixtures/sample_tree.gw')
    
    print(f"✅ Fichier parsé: {len(genealogy.persons)} personnes, {len(genealogy.families)} familles")
    
    # 2. Statistiques générales
    print("\n📊 STATISTIQUES GÉNÉRALES")
    print("=" * 40)
    
    # Par sexe
    male_count = sum(1 for p in genealogy.persons.values() if p.gender == Gender.MALE)
    female_count = sum(1 for p in genealogy.persons.values() if p.gender == Gender.FEMALE)
    unknown_count = sum(1 for p in genealogy.persons.values() if p.gender == Gender.UNKNOWN)
    
    print(f"👥 Répartition par sexe:")
    print(f"   Hommes: {male_count} ({male_count/len(genealogy.persons)*100:.1f}%)")
    print(f"   Femmes: {female_count} ({female_count/len(genealogy.persons)*100:.1f}%)")
    print(f"   Inconnus: {unknown_count} ({unknown_count/len(genealogy.persons)*100:.1f}%)")
    
    # Familles
    families_with_children = [f for f in genealogy.families.values() if len(f.children) > 0]
    print(f"\n👨‍👩‍👧‍👦 Familles:")
    print(f"   Total: {len(genealogy.families)}")
    print(f"   Avec enfants: {len(families_with_children)} ({len(families_with_children)/len(genealogy.families)*100:.1f}%)")
    
    # 3. Recherches avancées
    print("\n🔍 RECHERCHES AVANCÉES")
    print("=" * 40)
    
    # Recherche par nom
    search_name = "MARTIN"
    name_persons = [p for p in genealogy.persons.values() if search_name in p.last_name]
    print(f"🔍 Personnes avec '{search_name}': {len(name_persons)}")
    
    # Afficher les 5 premiers
    for i, person in enumerate(name_persons[:5]):
        print(f"   {i+1}. {person.full_name} (ID: {person.unique_id})")
    
    # Recherche par prénom
    search_firstname = "Pierre"
    pierre_persons = [p for p in genealogy.persons.values() if search_firstname in p.first_name]
    print(f"\n🔍 Personnes avec prénom '{search_firstname}': {len(pierre_persons)}")
    
    # 4. Analyse des familles
    print("\n🏠 ANALYSE DES FAMILLES")
    print("=" * 40)
    
    # Familles avec le plus d'enfants
    families_by_children = sorted(
        genealogy.families.values(), 
        key=lambda f: len(f.children), 
        reverse=True
    )
    
    print("👶 Familles avec le plus d'enfants:")
    for i, family in enumerate(families_by_children[:5]):
        print(f"   {i+1}. {family.family_id}: {len(family.children)} enfants")
        
        # Afficher les enfants
        for j, child in enumerate(family.children[:3]):
            child_person = genealogy.persons.get(child.person_id)
            if child_person:
                print(f"      - {child_person.full_name}")
        if len(family.children) > 3:
            print(f"      ... et {len(family.children) - 3} autres")
    
    # 5. Accès par ID unique
    print("\n🎯 ACCÈS PAR ID UNIQUE")
    print("=" * 40)
    
    # Prendre une personne au hasard
    person_id = list(genealogy.persons.keys())[100]  # 100ème personne
    person = genealogy.persons[person_id]
    
    print(f"👤 Personne: {person.full_name}")
    print(f"   ID: {person.unique_id}")
    print(f"   Sexe: {person.gender.value}")
    print(f"   Occurrence: {person.occurrence_number}")
    print(f"   Niveau d'accès: {person.access_level.value}")
    
    # Informations sur les familles de cette personne
    print(f"\n👨‍👩‍👧‍👦 Familles de {person.first_name}:")
    print(f"   Comme enfant: {len(person.families_as_child)} familles")
    print(f"   Comme époux/épouse: {len(person.families_as_spouse)} familles")
    
    # 6. Manipulation des données
    print("\n🔧 MANIPULATION DES DONNÉES")
    print("=" * 40)
    
    # Ajouter un événement à une personne
    print("➕ Ajout d'un événement de naissance...")
    
    # Créer une date
    birth_date = Date(
        year=1950,
        month=3,
        day=15
    )
    
    # Créer un événement
    birth_event = PersonalEvent(
        event_type=EventType.BIRTH,
        date=birth_date,
        place="Paris, France",
        notes=["Naissance enregistrée"],
        source="Acte de naissance"
    )
    
    # Ajouter l'événement à la personne
    person.add_event(birth_event)
    person.birth_date = birth_date
    person.birth_place = "Paris, France"
    
    print(f"✅ Événement ajouté à {person.full_name}")
    print(f"   Date de naissance: {person.birth_date.display_text}")
    print(f"   Lieu: {person.birth_place}")
    print(f"   Événements: {len(person.events)}")
    
    # 7. Export des données
    print("\n📤 EXPORT DES DONNÉES")
    print("=" * 40)
    
    # Export vers dictionnaire
    data_dict = genealogy.to_dict()
    print(f"📊 Données exportées vers dictionnaire:")
    print(f"   Clés principales: {list(data_dict.keys())}")
    print(f"   Nombre de personnes: {len(data_dict['persons'])}")
    print(f"   Nombre de familles: {len(data_dict['families'])}")
    
    # 8. Recherche de patterns
    print("\n🔍 RECHERCHE DE PATTERNS")
    print("=" * 40)
    
    # Homonymes (même nom, occurrence différente)
    name_counts = {}
    for person in genealogy.persons.values():
        base_name = f"{person.last_name} {person.first_name}"
        name_counts[base_name] = name_counts.get(base_name, 0) + 1
    
    homonyms = {name: count for name, count in name_counts.items() if count > 1}
    print(f"👥 Homonymes trouvés: {len(homonyms)}")
    
    # Afficher les 5 premiers
    sorted_homonyms = sorted(homonyms.items(), key=lambda x: x[1], reverse=True)
    for i, (name, count) in enumerate(sorted_homonyms[:5]):
        print(f"   {i+1}. {name}: {count} occurrences")
    
    # 9. Validation des données
    print("\n✅ VALIDATION DES DONNÉES")
    print("=" * 40)
    
    # Vérifier la cohérence des références
    orphan_children = 0
    for family in genealogy.families.values():
        for child in family.children:
            if child.person_id not in genealogy.persons:
                orphan_children += 1
    
    print(f"🔗 Cohérence des références:")
    print(f"   Enfants orphelins: {orphan_children}")
    print(f"   Références valides: {'✅' if orphan_children == 0 else '❌'}")
    
    # 10. Résumé final
    print("\n🎉 RÉSUMÉ FINAL")
    print("=" * 40)
    print(f"✅ Fichier parsé avec succès")
    print(f"📊 {len(genealogy.persons)} personnes structurées")
    print(f"🏠 {len(genealogy.families)} familles organisées")
    print(f"🔗 Références croisées validées")
    print(f"💾 Données prêtes pour manipulation et export")


if __name__ == "__main__":
    main()
