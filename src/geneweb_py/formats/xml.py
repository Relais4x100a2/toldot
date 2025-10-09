"""
Convertisseur XML pour geneweb-py.

Ce module fournit les fonctionnalités d'export et d'import vers/depuis
le format XML pour faciliter l'intégration avec d'autres systèmes
et l'échange de données généalogiques.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Union

from ..core.date import Date
from ..core.event import Event
from ..core.family import Family
from ..core.genealogy import Genealogy
from ..core.person import Person
from .base import BaseExporter, BaseImporter, ConversionError


class XMLExporter(BaseExporter):
    """Exporteur vers le format XML."""

    def __init__(self, encoding: str = "utf-8", pretty_print: bool = True):
        """
        Initialise l'exporteur XML.

        Args:
            encoding: Encodage à utiliser (défaut: utf-8)
            pretty_print: Formatage avec indentation (défaut: True)
        """
        super().__init__(encoding)
        self.pretty_print = pretty_print

    def export(self, genealogy: Genealogy, output_path: Union[str, Path]) -> None:
        """
        Exporte une généalogie vers un fichier XML.

        Args:
            genealogy: Objet Genealogy à exporter
            output_path: Chemin du fichier de sortie

        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        self._validate_genealogy(genealogy)

        try:
            xml_content = self.export_to_string(genealogy)

            with open(output_path, "w", encoding=self.encoding) as f:
                f.write(xml_content)

        except Exception as e:
            raise ConversionError(f"Erreur lors de l'export XML : {e}") from e

    def export_to_string(self, genealogy: Genealogy) -> str:
        """
        Exporte une généalogie vers une chaîne XML.

        Args:
            genealogy: Objet Genealogy à exporter

        Returns:
            Chaîne XML formatée

        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        self._validate_genealogy(genealogy)

        try:
            root = self._serialize_genealogy(genealogy)

            if self.pretty_print:
                self._indent_xml(root)

            return ET.tostring(
                root, encoding=self.encoding, xml_declaration=True
            ).decode(self.encoding)

        except Exception as e:
            raise ConversionError(f"Erreur lors de la sérialisation XML : {e}") from e

    def _serialize_genealogy(self, genealogy: Genealogy) -> ET.Element:
        """Sérialise une généalogie en élément XML."""
        root = ET.Element("genealogy")
        root.set("version", "1.0.0")
        root.set("format", "geneweb-py-xml")

        # Métadonnées
        metadata = ET.SubElement(root, "metadata")
        if genealogy.metadata.created_date:
            metadata.set("created_at", genealogy.metadata.created_date.isoformat())

        stats = ET.SubElement(metadata, "statistics")
        stats.set("persons_count", str(len(genealogy.persons)))
        stats.set("families_count", str(len(genealogy.families)))

        events_count = sum(len(p.events) for p in genealogy.persons.values()) + sum(
            len(f.events) for f in genealogy.families.values()
        )
        stats.set("events_count", str(events_count))

        # Personnes
        persons_elem = ET.SubElement(root, "persons")
        for person in genealogy.persons.values():
            person_elem = self._serialize_person(person)
            persons_elem.append(person_elem)

        # Familles
        families_elem = ET.SubElement(root, "families")
        for family in genealogy.families.values():
            family_elem = self._serialize_family(family)
            families_elem.append(family_elem)

        return root

    def _serialize_person(self, person: Person) -> ET.Element:
        """Sérialise une personne en élément XML."""
        person_elem = ET.Element("person")
        person_elem.set("id", str(id(person)))

        # Noms
        if person.last_name:
            person_elem.set("last_name", person.last_name)
        if person.first_name:
            person_elem.set("first_name", person.first_name)
        if person.public_name:
            person_elem.set("public_name", person.public_name)

        # Sexe
        if person.gender:
            person_elem.set("gender", person.gender.value)

        # Dates
        if person.birth_date:
            birth_elem = self._serialize_date(person.birth_date, "birth")
            person_elem.append(birth_elem)

        if person.death_date:
            death_elem = self._serialize_date(person.death_date, "death")
            person_elem.append(death_elem)

        if person.baptism_date:
            baptism_elem = self._serialize_date(person.baptism_date, "baptism")
            person_elem.append(baptism_elem)

        # Lieux
        if person.birth_place:
            place_elem = ET.SubElement(person_elem, "birth_place")
            place_elem.text = person.birth_place

        if person.death_place:
            place_elem = ET.SubElement(person_elem, "death_place")
            place_elem.text = person.death_place

        if person.baptism_place:
            place_elem = ET.SubElement(person_elem, "baptism_place")
            place_elem.text = person.baptism_place

        # Titres et profession
        if person.titles:
            titles_elem = ET.SubElement(person_elem, "titles")
            for title in person.titles:
                title_elem = ET.SubElement(titles_elem, "title")
                title_elem.text = title.name

        if person.occupation:
            occ_elem = ET.SubElement(person_elem, "occupation")
            occ_elem.text = person.occupation

        # Notes
        if person.notes:
            notes_elem = ET.SubElement(person_elem, "notes")
            for note in person.notes:
                note_elem = ET.SubElement(notes_elem, "note")
                note_elem.text = note

        # Événements
        if person.events:
            events_elem = ET.SubElement(person_elem, "events")
            for event in person.events:
                event_elem = self._serialize_event(event)
                events_elem.append(event_elem)

        # Relations
        if person.relations:
            relations_elem = ET.SubElement(person_elem, "relations")
            for relation_type, relation_ids in person.relations.items():
                for relation_id in relation_ids:
                    rel_elem = ET.SubElement(relations_elem, "relation")
                    rel_elem.set("type", relation_type)
                    rel_elem.text = relation_id

        return person_elem

    def _serialize_family(self, family: Family) -> ET.Element:
        """Sérialise une famille en élément XML."""
        family_elem = ET.Element("family")
        family_elem.set("id", str(id(family)))

        # Époux
        if family.husband_id:
            family_elem.set("husband_id", family.husband_id)

        # Épouse
        if family.wife_id:
            family_elem.set("wife_id", family.wife_id)

        # Enfants
        if family.children:
            children_elem = ET.SubElement(family_elem, "children")
            for child in family.children:
                child_elem = ET.SubElement(children_elem, "child")
                child_elem.set("person_id", child.person_id)

        # Dates de mariage et divorce
        if family.marriage_date:
            marriage_elem = self._serialize_date(family.marriage_date, "marriage")
            family_elem.append(marriage_elem)

        if family.divorce_date:
            divorce_elem = self._serialize_date(family.divorce_date, "divorce")
            family_elem.append(divorce_elem)

        # Lieux
        if family.marriage_place:
            place_elem = ET.SubElement(family_elem, "marriage_place")
            place_elem.text = family.marriage_place

        # Événements
        if family.events:
            events_elem = ET.SubElement(family_elem, "events")
            for event in family.events:
                event_elem = self._serialize_event(event)
                events_elem.append(event_elem)

        # Sources et témoins
        if family.family_source:
            source_elem = ET.SubElement(family_elem, "family_source")
            source_elem.text = family.family_source

        if family.witnesses:
            witnesses_elem = ET.SubElement(family_elem, "witnesses")
            for witness in family.witnesses:
                witness_elem = ET.SubElement(witnesses_elem, "witness")
                witness_elem.text = witness

        return family_elem

    def _serialize_event(self, event: Event) -> ET.Element:
        """Sérialise un événement en élément XML."""
        event_elem = ET.Element("event")
        event_elem.set("type", event.event_type.value if event.event_type else "")

        if event.date:
            date_elem = self._serialize_date(event.date, "date")
            event_elem.append(date_elem)

        if event.place:
            place_elem = ET.SubElement(event_elem, "place")
            place_elem.text = event.place

        if event.source:
            source_elem = ET.SubElement(event_elem, "source")
            source_elem.text = event.source

        if event.witnesses:
            witnesses_elem = ET.SubElement(event_elem, "witnesses")
            for witness in event.witnesses:
                witness_elem = ET.SubElement(witnesses_elem, "witness")
                if isinstance(witness, dict):
                    witness_elem.text = str(witness.get("person_id", ""))
                else:
                    witness_elem.text = str(witness)

        if event.notes:
            notes_elem = ET.SubElement(event_elem, "notes")
            for note in event.notes:
                note_elem = ET.SubElement(notes_elem, "note")
                note_elem.text = note

        return event_elem

    def _serialize_date(self, date: Date, name: str) -> ET.Element:
        """Sérialise une date en élément XML."""
        date_elem = ET.Element(name)

        if date.year:
            date_elem.set("year", str(date.year))
        if date.month:
            date_elem.set("month", str(date.month))
        if date.day:
            date_elem.set("day", str(date.day))
        if date.calendar:
            date_elem.set("calendar", date.calendar.value)
        if date.prefix:
            date_elem.set("prefix", date.prefix.value)
        if date.text_date:
            date_elem.text = date.text_date

        # Attributs booléens (dérivés du préfixe)
        from ..core.date import DatePrefix

        if date.prefix == DatePrefix.ABOUT:
            date_elem.set("approximate", "true")
        if date.prefix == DatePrefix.BEFORE:
            date_elem.set("before", "true")
        if date.prefix == DatePrefix.AFTER:
            date_elem.set("after", "true")
        if date.prefix == DatePrefix.MAYBE:
            date_elem.set("uncertain", "true")
        if date.death_type:
            date_elem.set("death_type", date.death_type.value)

        return date_elem

    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Ajoute une indentation au XML pour le formatage."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


class XMLImporter(BaseImporter):
    """Importeur depuis le format XML."""

    def __init__(self, encoding: str = "utf-8"):
        """
        Initialise l'importeur XML.

        Args:
            encoding: Encodage à utiliser (défaut: utf-8)
        """
        super().__init__(encoding)
        self._person_map: Dict[int, Person] = {}
        self._family_map: Dict[int, Family] = {}

    def import_from_file(self, input_path: Union[str, Path]) -> Genealogy:
        """
        Importe une généalogie depuis un fichier XML.

        Args:
            input_path: Chemin du fichier à importer

        Returns:
            Objet Genealogy importé

        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        path = self._validate_file_path(input_path)

        try:
            with open(path, encoding=self.encoding) as f:
                content = f.read()

            return self.import_from_string(content)

        except Exception as e:
            raise ConversionError(f"Erreur lors de l'import XML : {e}") from e

    def import_from_string(self, data: str) -> Genealogy:
        """
        Importe une généalogie depuis une chaîne XML.

        Args:
            data: Chaîne XML à importer

        Returns:
            Objet Genealogy importé

        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        try:
            # Parser le XML
            root = ET.fromstring(data)

            # Réinitialiser les maps
            self._person_map.clear()
            self._family_map.clear()

            # Créer la généalogie
            genealogy = Genealogy()

            # Importer les personnes
            persons_elem = root.find("persons")
            if persons_elem is not None:
                for person_elem in persons_elem.findall("person"):
                    person = self._deserialize_person(person_elem)
                    if person:
                        genealogy.add_person(person)

            # Importer les familles
            families_elem = root.find("families")
            if families_elem is not None:
                for family_elem in families_elem.findall("family"):
                    family = self._deserialize_family(family_elem)
                    if family:
                        genealogy.add_family(family)

            return genealogy

        except Exception as e:
            raise ConversionError(f"Erreur lors du parsing XML : {e}") from e

    def _deserialize_person(self, elem: ET.Element) -> Optional[Person]:
        """Désérialise une personne depuis un élément XML."""
        try:
            # Genre
            gender_value = elem.get("gender")
            gender = None
            if gender_value:
                from ..core.person import Gender

                try:
                    gender = Gender(gender_value)
                except ValueError:
                    gender = Gender.UNKNOWN

            person = Person(
                last_name=elem.get("last_name", ""),
                first_name=elem.get("first_name", ""),
                public_name=elem.get("public_name"),
                gender=gender,
            )

            # Stocker dans la map pour les références
            person_id = elem.get("id")
            if person_id:
                self._person_map[int(person_id)] = person

            # Dates
            birth_elem = elem.find("birth")
            if birth_elem is not None:
                person.birth_date = self._deserialize_date(birth_elem)

            death_elem = elem.find("death")
            if death_elem is not None:
                person.death_date = self._deserialize_date(death_elem)

            baptism_elem = elem.find("baptism")
            if baptism_elem is not None:
                person.baptism_date = self._deserialize_date(baptism_elem)

            # Lieux
            birth_place_elem = elem.find("birth_place")
            if birth_place_elem is not None and birth_place_elem.text:
                person.birth_place = birth_place_elem.text.strip()

            death_place_elem = elem.find("death_place")
            if death_place_elem is not None and death_place_elem.text:
                person.death_place = death_place_elem.text.strip()

            baptism_place_elem = elem.find("baptism_place")
            if baptism_place_elem is not None and baptism_place_elem.text:
                person.baptism_place = baptism_place_elem.text.strip()

            # Titres
            titles_elem = elem.find("titles")
            if titles_elem is not None:
                from ..core.person import Title

                person.titles = [
                    Title(name=title_elem.text)
                    for title_elem in titles_elem.findall("title")
                    if title_elem.text
                ]

            # Profession
            occ_elem = elem.find("occupation")
            if occ_elem is not None and occ_elem.text:
                person.occupation = occ_elem.text.strip()

            # Notes
            notes_elem = elem.find("notes")
            if notes_elem is not None and notes_elem.text:
                person.notes = notes_elem.text.strip()

            # Événements
            events_elem = elem.find("events")
            if events_elem is not None:
                for event_elem in events_elem.findall("event"):
                    event = self._deserialize_event(event_elem)
                    if event:
                        person.add_event(event)

            # Relations
            relations_elem = elem.find("relations")
            if relations_elem is not None:
                person.relations = {}
                for rel_elem in relations_elem.findall("relation"):
                    rel_type = rel_elem.get("type", "unknown")
                    rel_id = rel_elem.text
                    if rel_id:
                        if rel_type not in person.relations:
                            person.relations[rel_type] = []
                        person.relations[rel_type].append(rel_id)

            return person

        except Exception as e:
            raise ConversionError(
                f"Erreur lors de la désérialisation de la personne : {e}"
            ) from e

    def _deserialize_family(self, elem: ET.Element) -> Optional[Family]:
        """Désérialise une famille depuis un élément XML."""
        try:
            family = Family(
                family_id=elem.get("id", "F001"),
                husband_id=elem.get("husband_id"),
                wife_id=elem.get("wife_id"),
            )

            # Stocker dans la map pour les références
            family_id = elem.get("id")
            if family_id:
                self._family_map[int(family_id)] = family

            # Dates de mariage et divorce
            marriage_elem = elem.find("marriage")
            if marriage_elem is not None:
                family.marriage_date = self._deserialize_date(marriage_elem)

            divorce_elem = elem.find("divorce")
            if divorce_elem is not None:
                family.divorce_date = self._deserialize_date(divorce_elem)

            # Lieux
            marriage_place_elem = elem.find("marriage_place")
            if marriage_place_elem is not None and marriage_place_elem.text:
                family.marriage_place = marriage_place_elem.text.strip()

            # Événements
            events_elem = elem.find("events")
            if events_elem is not None:
                for event_elem in events_elem.findall("event"):
                    event = self._deserialize_event(event_elem)
                    if event:
                        family.add_event(event)

            # Sources et témoins
            family_source_elem = elem.find("family_source")
            if family_source_elem is not None and family_source_elem.text:
                family.family_source = family_source_elem.text.strip()

            witnesses_elem = elem.find("witnesses")
            if witnesses_elem is not None:
                family.witnesses = [
                    witness_elem.text
                    for witness_elem in witnesses_elem.findall("witness")
                    if witness_elem.text
                ]

            return family

        except Exception as e:
            raise ConversionError(
                f"Erreur lors de la désérialisation de la famille : {e}"
            ) from e

    def _deserialize_event(self, elem: ET.Element) -> Optional[Event]:
        """Désérialise un événement depuis un élément XML."""
        try:
            event_type_str = elem.get("type", "")
            # Convertir le string en enum EventType
            from ..core.event import EventType

            try:
                event_type = EventType(event_type_str)
            except ValueError:
                # Si le type n'est pas reconnu, utiliser OTHER
                event_type = EventType.OTHER

            # Date
            date_elem = elem.find("date")
            date = None
            if date_elem is not None:
                date = self._deserialize_date(date_elem)

            # Lieu
            place_elem = elem.find("place")
            place = (
                place_elem.text.strip()
                if place_elem is not None and place_elem.text
                else None
            )

            # Source
            source = None
            source_elem = elem.find("source")
            if source_elem is not None and source_elem.text:
                source = source_elem.text.strip()

            # Témoins
            witnesses = []
            witnesses_elem = elem.find("witnesses")
            if witnesses_elem is not None:
                witnesses = [
                    witness_elem.text
                    for witness_elem in witnesses_elem.findall("witness")
                    if witness_elem.text
                ]

            # Notes
            notes = []
            notes_elem = elem.find("notes")
            if notes_elem is not None:
                notes = [
                    note_elem.text
                    for note_elem in notes_elem.findall("note")
                    if note_elem.text
                ]

            return Event(
                event_type=event_type,
                date=date,
                place=place,
                source=source,
                witnesses=witnesses,
                notes=notes,
            )

        except Exception as e:
            raise ConversionError(
                f"Erreur lors de la désérialisation de l'événement : {e}"
            ) from e

    def _deserialize_date(self, elem: ET.Element) -> Optional[Date]:
        """Désérialise une date depuis un élément XML."""
        try:
            year = elem.get("year")
            month = elem.get("month")
            day = elem.get("day")

            if not year and not month and not day and not elem.text:
                return None

            from ..core.date import CalendarType, DatePrefix, DeathType

            calendar = None
            if elem.get("calendar"):
                calendar = CalendarType(elem.get("calendar"))

            prefix = None
            if elem.get("prefix"):
                prefix = DatePrefix(elem.get("prefix"))

            death_type = None
            if elem.get("death_type"):
                death_type = DeathType(elem.get("death_type"))

            return Date(
                year=int(year) if year else None,
                month=int(month) if month else None,
                day=int(day) if day else None,
                calendar=calendar,
                prefix=prefix,
                text_date=elem.text.strip() if elem.text else None,
                death_type=death_type,
            )

        except Exception as e:
            raise ConversionError(f"Erreur lors de la désérialisation de la date : {e}") from e  # noqa: E501
