#!/usr/bin/env python3
"""
Exemple d'utilisation du parser GeneWeb

Ce script démontre comment utiliser le parser pour lire des fichiers .gw
et construire des objets de données généalogiques.
"""

from geneweb_py import GeneWebParser


def main():
    """Fonction principale de l'exemple"""
    print("=== Exemple d'utilisation du parser GeneWeb ===\n")
    
    # Contenu .gw d'exemple
    gw_content = """fam CORNO Joseph_Marie_Vincent 25/12/1990 #bp Paris + 10/08/2015 #mp Paris THOMAS Marie_Julienne 15/06/1992 #bp Lyon
wit m: DUPONT Pierre
wit f: MARTIN Claire
src "Acte de mariage, mairie de Paris"
comm "Mariage célébré en présence de nombreux témoins"
beg
- h CORNO Jean_Baptiste 10/03/2016 #bp Paris
- f CORNO Sophie_Marie 05/07/2018 #bp Paris
end

notes CORNO Joseph_Marie_Vincent
beg
**Joseph Marie Vincent CORNO**

Né le 25 décembre 1990 à Paris, Joseph a grandi dans le 15ème arrondissement.
Il a étudié l'informatique à l'École Polytechnique et travaille comme ingénieur
dans une société de technologie.

**Hobbies:**
- Football
- Lecture
- Voyages
end notes

notes THOMAS Marie_Julienne
beg
**Marie Julienne THOMAS**

Née le 15 juin 1992 à Lyon, Marie a étudié la médecine à l'université de Lyon.
Elle travaille maintenant comme médecin généraliste à Paris.

**Passions:**
- Musique classique
- Cuisine française
- Voyages
end notes"""
    
    # Créer le parser
    print("1. Création du parser...")
    parser = GeneWebParser(validate=True)
    
    # Parser le contenu
    print("2. Parsing du contenu .gw...")
    genealogy = parser.parse_string(gw_content)
    
    # Afficher les résultats
    print("3. Résultats du parsing...")
    print(f"   - Nombre de personnes: {len(genealogy.persons)}")
    print(f"   - Nombre de familles: {len(genealogy.families)}")
    
    # Détails des personnes
    print("\n4. Détails des personnes...")
    for person in genealogy.persons.values():
        print(f"   - {person.display_name}")
        if person.birth_date:
            print(f"     * Naissance: {person.birth_date} à {person.birth_place or 'lieu inconnu'}")
        if person.gender.value != '?':
            print(f"     * Sexe: {person.gender.value}")
        if person.notes:
            print(f"     * Notes: {len(person.notes)} note(s)")
    
    # Détails des familles
    print("\n5. Détails des familles...")
    for family in genealogy.families.values():
        husband = genealogy.find_person_by_id(family.husband_id)
        wife = genealogy.find_person_by_id(family.wife_id)
        print(f"   - {husband.last_name} + {wife.last_name}")
        if family.marriage_date:
            print(f"     * Mariage: {family.marriage_date} à {family.marriage_place or 'lieu inconnu'}")
        if family.witnesses:
            print(f"     * Témoins: {len(family.witnesses)}")
        if family.children:
            print(f"     * Enfants: {len(family.children)}")
            for child in family.children:
                child_person = genealogy.find_person_by_id(child.person_id)
                sex_symbol = "♂" if child.sex.value == 'h' else "♀" if child.sex.value == 'f' else "?"
                print(f"       - {sex_symbol} {child_person.display_name}")
    
    # Relations familiales
    print("\n6. Relations familiales...")
    for person in genealogy.persons.values():
        if person.families_as_child:
            parents = genealogy.get_parents(person.unique_id)
            parent_names = [p.display_name for p in parents]
            print(f"   - {person.display_name} est enfant de: {', '.join(parent_names)}")
        
        if person.families_as_spouse:
            spouses = genealogy.get_spouses(person.unique_id)
            spouse_names = [s.display_name for s in spouses]
            print(f"   - {person.display_name} est conjoint de: {', '.join(spouse_names)}")
    
    # Statistiques
    print("\n7. Statistiques de la généalogie...")
    stats = genealogy.get_statistics()
    print(f"   - Personnes vivantes: {stats['living_persons']}")
    print(f"   - Personnes décédées: {stats['deceased_persons']}")
    print(f"   - Hommes: {stats['male_persons']}")
    print(f"   - Femmes: {stats['female_persons']}")
    print(f"   - Familles avec enfants: {stats['families_with_children']}")
    print(f"   - Total d'enfants: {stats['total_children']}")
    
    # Validation
    print("\n8. Validation de cohérence...")
    errors = genealogy.validate_consistency()
    if errors:
        print(f"   - {len(errors)} erreurs de validation détectées:")
        for error in errors:
            print(f"     * {error}")
    else:
        print("   - Aucune erreur de cohérence détectée ✓")
    
    # Informations sur le parsing
    print("\n9. Informations sur le parsing...")
    tokens = parser.get_tokens()
    nodes = parser.get_syntax_nodes()
    print(f"   - Nombre de tokens: {len(tokens)}")
    print(f"   - Nombre de nœuds syntaxiques: {len(nodes)}")
    
    # Exemple de tokens
    print("\n10. Exemples de tokens...")
    for i, token in enumerate(tokens[:10]):  # Premiers 10 tokens
        print(f"    {i+1:2d}: {token.type.value:12s} '{token.value}'")
    
    print("\n=== Fin de l'exemple ===")


if __name__ == "__main__":
    main()
