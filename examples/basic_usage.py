#!/usr/bin/env python3
"""
Exemple d'utilisation basique de geneweb-py

Ce script démontre comment créer et manipuler des données généalogiques
avec la librairie geneweb-py.
"""

from geneweb_py.core.family import ChildSex
from geneweb_py.core.models import Date, Family, Genealogy, Person
from geneweb_py.core.person import Gender


def main():
    """Fonction principale de l'exemple"""
    print("=== Exemple d'utilisation de geneweb-py ===\n")

    # Créer une généalogie
    genealogy = Genealogy()

    # Créer des personnes
    print("1. Création des personnes...")

    # Joseph CORNO
    joseph = Person(
        last_name="CORNO",
        first_name="Joseph_Marie_Vincent",
        gender=Gender.MALE,
        birth_date=Date.parse("25/12/1990"),
        birth_place="Paris",
        death_date=Date.parse("10/01/2020"),
        death_place="Paris",
    )

    # Marie THOMAS
    marie = Person(
        last_name="THOMAS",
        first_name="Marie_Julienne",
        gender=Gender.FEMALE,
        birth_date=Date.parse("15/06/1992"),
        birth_place="Lyon",
    )

    # Jean CORNO (fils)
    jean = Person(
        last_name="CORNO",
        first_name="Jean_Baptiste",
        gender=Gender.MALE,
        birth_date=Date.parse("10/03/2016"),
        birth_place="Paris",
    )

    # Sophie CORNO (fille)
    sophie = Person(
        last_name="CORNO",
        first_name="Sophie_Marie",
        gender=Gender.FEMALE,
        birth_date=Date.parse("05/07/2018"),
        birth_place="Paris",
    )

    # Ajouter les personnes à la généalogie
    genealogy.add_person(joseph)
    genealogy.add_person(marie)
    genealogy.add_person(jean)
    genealogy.add_person(sophie)

    print(
        f"   - {joseph.display_name} (né le {joseph.birth_date}, décédé le {joseph.death_date})"  # noqa: E501
    )
    print(f"   - {marie.display_name} (née le {marie.birth_date})")
    print(f"   - {jean.display_name} (né le {jean.birth_date})")
    print(f"   - {sophie.display_name} (née le {sophie.birth_date})")

    # Créer une famille
    print("\n2. Création de la famille...")

    family = Family(
        family_id="FAM001",
        husband_id=joseph.unique_id,
        wife_id=marie.unique_id,
        marriage_date=Date.parse("10/08/2015"),
        marriage_place="Paris",
    )

    # Ajouter les enfants
    family.add_child(jean.unique_id, ChildSex.MALE)
    family.add_child(sophie.unique_id, ChildSex.FEMALE)

    # Ajouter la famille à la généalogie
    genealogy.add_family(family)

    print(f"   - Famille {family.family_id}: {joseph.last_name} + {marie.last_name}")
    print(f"   - Mariage: {family.marriage_date} à {family.marriage_place}")
    print(f"   - Enfants: {len(family.children)}")

    # Afficher les statistiques
    print("\n3. Statistiques de la généalogie...")
    stats = genealogy.get_statistics()

    print(f"   - Total personnes: {stats['total_persons']}")
    print(f"   - Total familles: {stats['total_families']}")
    print(f"   - Personnes vivantes: {stats['living_persons']}")
    print(f"   - Personnes décédées: {stats['deceased_persons']}")
    print(f"   - Hommes: {stats['male_persons']}")
    print(f"   - Femmes: {stats['female_persons']}")

    # Rechercher des relations
    print("\n4. Recherche de relations...")

    # Parents de Jean
    parents = genealogy.get_parents(jean.unique_id)
    print(f"   - Parents de {jean.first_name}: {[p.display_name for p in parents]}")

    # Enfants de Joseph
    children = genealogy.get_children(joseph.unique_id)
    print(f"   - Enfants de {joseph.first_name}: {[c.display_name for c in children]}")

    # Conjoints de Marie
    spouses = genealogy.get_spouses(marie.unique_id)
    print(f"   - Conjoints de {marie.first_name}: {[s.display_name for s in spouses]}")

    # Frères et sœurs de Jean
    siblings = genealogy.get_siblings(jean.unique_id)
    print(
        f"   - Frères et sœurs de {jean.first_name}: {[s.display_name for s in siblings]}"  # noqa: E501
    )

    # Validation
    print("\n5. Validation de la cohérence...")
    errors = genealogy.validate_consistency()

    if errors:
        print(f"   - {len(errors)} erreurs trouvées:")
        for error in errors:
            print(f"     * {error}")
    else:
        print("   - Aucune erreur de cohérence détectée ✓")

    # Exemple de parsing de dates complexes
    print("\n6. Exemples de parsing de dates...")

    dates_examples = [
        "25/12/1990",
        "~10/5/1990",
        "?15/06/1992",
        "<01/01/2020",
        ">31/12/2019",
        "10/9/5750H",  # Calendrier hébreu
        "0(5_Mai_1990)",  # Date textuelle
        "0",  # Date inconnue
    ]

    for date_str in dates_examples:
        try:
            date = Date.parse(date_str)
            print(f"   - '{date_str}' → {date.display_text}")
        except Exception as e:
            print(f"   - '{date_str}' → ERREUR: {e}")

    print("\n=== Fin de l'exemple ===")


if __name__ == "__main__":
    main()
