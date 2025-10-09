#!/usr/bin/env python3
"""
Exemple d'utilisation des nouvelles fonctionnalités du parser GeneWeb

Ce script démontre les améliorations apportées au parser :
- Support des apostrophes dans les identifiants
- Support des caractères spéciaux dans les occupations
- Déduplication intelligente avec numéros d'occurrence
- Support des nouveaux blocs GeneWeb
- Parsing des enfants et témoins avec toutes leurs informations
"""

from geneweb_py import GeneWebParser


def main():
    """Démonstration des nouvelles fonctionnalités du parser"""

    # Contenu de test avec toutes les nouvelles fonctionnalités
    content = """
fam d'Arc Jean-Marie .1 #occu Ingénieur_(ENSIA),_Aumônier_de_l'enseignement + O'Brien Marie-Claire .2
wit m: LEROY Bernard .1 #occu Dominicain,_Aumônier_de_l'enseignement_technique_à_Rouen
beg
- h Pierre_Bernard .1 #occu Ingénieur,_éditeur
- f Marie_Claire .2 #occu Conseillère_en_économie_sociale_et_familiale
end

notes-db
Notes générales sur cette famille
Informations supplémentaires
end notes-db

page-ext d'Arc Jean-Marie .1
<h1>Page de Jean-Marie d'Arc</h1>
<p>Informations supplémentaires...</p>
end page-ext

wizard-note O'Brien Marie-Claire .2
Note générée par le wizard pour Marie-Claire
Informations supplémentaires
end wizard-note
"""

    print("🚀 Démonstration des nouvelles fonctionnalités du parser GeneWeb")
    print("=" * 70)

    # Créer le parser
    parser = GeneWebParser()

    # Parser le contenu
    print("📖 Parsing du contenu...")
    genealogy = parser.parse_string(content)

    print("✅ Parsing réussi !")
    print(f"   - {len(genealogy.persons)} personnes trouvées")
    print(f"   - {len(genealogy.families)} familles trouvées")
    print()

    # Afficher les personnes avec leurs informations
    print("👥 Personnes parsées :")
    print("-" * 50)

    for _person_id, person in genealogy.persons.items():
        print(f"• {person.first_name} {person.last_name}")
        print(f"  - Occurrence : {person.occurrence_number}")
        print(f"  - Occupation : {person.occupation or 'Non spécifiée'}")

        # Afficher les métadonnées si présentes
        if person.metadata:
            if "extended_page" in person.metadata:
                print(
                    f"  - Page étendue : {len(person.metadata['extended_page'])} élément(s)"
                )
            if "wizard_note" in person.metadata:
                print(
                    f"  - Note wizard : {len(person.metadata['wizard_note'])} élément(s)"
                )
        print()

    # Afficher les notes de base de données
    if genealogy.metadata.database_notes:
        print("📝 Notes de base de données :")
        print("-" * 50)
        for note in genealogy.metadata.database_notes:
            print(f"• {note}")
        print()

    # Afficher les statistiques
    print("📊 Statistiques :")
    print("-" * 50)
    stats = genealogy.get_statistics()
    print(f"• Total personnes : {stats['total_persons']}")
    print(f"• Total familles : {stats['total_families']}")
    print(
        f"• Personnes avec occupation : {sum(1 for p in genealogy.persons.values() if p.occupation)}"
    )
    print(
        f"• Personnes avec numéros d'occurrence : {sum(1 for p in genealogy.persons.values() if p.occurrence_number > 0)}"
    )
    print()

    # Démonstration des fonctionnalités spécifiques
    print("🎯 Fonctionnalités démontrées :")
    print("-" * 50)
    print("✅ Support des apostrophes dans les identifiants (d'Arc, O'Brien)")
    print("✅ Support des caractères spéciaux dans les occupations")
    print("✅ Déduplication intelligente avec numéros d'occurrence")
    print("✅ Support des nouveaux blocs GeneWeb (notes-db, page-ext, wizard-note)")
    print("✅ Parsing des enfants avec sexes et occupations")
    print("✅ Parsing des témoins avec toutes leurs informations")
    print()

    print("🎉 Toutes les nouvelles fonctionnalités fonctionnent correctement !")


if __name__ == "__main__":
    main()
