"""
Configuration pytest pour geneweb-py

Ce fichier contient les fixtures et configurations partagées
pour tous les tests.
"""

import pytest
from typing import Dict, Any

from geneweb_py.core.models import (
    Person,
    Family,
    Date,
    Genealogy,
    Gender,
    MarriageStatus,
    CalendarType,
)


@pytest.fixture
def sample_date() -> Date:
    """Fixture pour une date d'exemple"""
    return Date.parse("25/12/1990")


@pytest.fixture
def sample_date_with_prefix() -> Date:
    """Fixture pour une date avec préfixe"""
    return Date.parse("~10/5/1990")


@pytest.fixture
def sample_text_date() -> Date:
    """Fixture pour une date textuelle"""
    return Date.parse("0(5_Mai_1990)")


@pytest.fixture
def sample_person() -> Person:
    """Fixture pour une personne d'exemple"""
    return Person(
        last_name="CORNO",
        first_name="Joseph",
        gender=Gender.MALE,
        birth_date=Date.parse("25/12/1990"),
        birth_place="Paris",
    )


@pytest.fixture
def sample_person_2() -> Person:
    """Fixture pour une deuxième personne d'exemple"""
    return Person(
        last_name="THOMAS",
        first_name="Marie",
        gender=Gender.FEMALE,
        birth_date=Date.parse("15/06/1992"),
        birth_place="Lyon",
    )


@pytest.fixture
def sample_family() -> Family:
    """Fixture pour une famille d'exemple"""
    return Family(
        family_id="FAM001",
        husband_id="CORNO_Joseph_0",
        wife_id="THOMAS_Marie_0",
        marriage_date=Date.parse("10/08/2015"),
        marriage_place="Paris",
    )


@pytest.fixture
def sample_genealogy(sample_person, sample_person_2, sample_family) -> Genealogy:
    """Fixture pour une généalogie d'exemple"""
    genealogy = Genealogy()

    # Ajouter les personnes
    genealogy.add_person(sample_person)
    genealogy.add_person(sample_person_2)

    # Ajouter la famille
    genealogy.add_family(sample_family)

    return genealogy


@pytest.fixture
def sample_gw_content() -> str:
    """Fixture pour du contenu .gw d'exemple"""
    return """
fam CORNO Joseph + THOMAS Marie
beg
- CORNO Jean
- THOMAS Sophie
end

notes CORNO Joseph
beg
Notes personnelles de Joseph CORNO
end notes
"""


@pytest.fixture
def sample_gwplus_content() -> str:
    """Fixture pour du contenu .gwplus d'exemple"""
    return """
gwplus
encoding: utf-8

fam CORNO Joseph + THOMAS Marie
beg
- CORNO Jean
- THOMAS Sophie
end

pevt CORNO Joseph
#birt 25/12/1990 #p Paris
end pevt

fevt CORNO Joseph + THOMAS Marie
#marr 10/08/2015 #p Paris
end fevt
"""
