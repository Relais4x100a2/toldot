"""
Tests de base pour vérifier que la configuration fonctionne

Ces tests vérifient que les imports et la structure de base
sont correctement configurés.
"""


def test_imports():
    """Test que tous les imports principaux fonctionnent"""
    from geneweb_py.core.exceptions import GeneWebError, GeneWebParseError
    from geneweb_py.core.models import Date, Family, Genealogy, Person

    # Vérifier que les classes sont bien importées
    assert Person is not None
    assert Family is not None
    assert Date is not None
    assert Genealogy is not None
    assert GeneWebError is not None
    assert GeneWebParseError is not None


def test_basic_functionality():
    """Test fonctionnalité de base"""
    from geneweb_py.core.models import Genealogy, Person
    from geneweb_py.core.person import Gender

    # Créer une personne simple
    person = Person(last_name="TEST", first_name="Person", gender=Gender.MALE)

    assert person.full_name == "TEST Person"
    assert person.gender == Gender.MALE

    # Créer une généalogie
    genealogy = Genealogy()
    genealogy.add_person(person)

    assert len(genealogy) == 1
    assert genealogy.find_person("TEST", "Person") == person


def test_date_parsing():
    """Test parsing de date simple"""
    from geneweb_py.core.models import Date

    date = Date.parse("25/12/1990")
    assert date.day == 25
    assert date.month == 12
    assert date.year == 1990
    assert date.display_text == "25/12/1990"
