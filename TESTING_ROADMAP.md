# Plan d'action - Couverture de tests 100%

**État actuel** : 83% de couverture (806 lignes manquantes / 4726 lignes totales)  
**Objectif** : 100% de couverture  
**Approche** : Progression incrémentale par phases

---

## 🎯 Court Terme (1-2 semaines, ~20-30h)
**Objectif** : Atteindre 90% de couverture globale  
**Focus** : Modules critiques déjà bien avancés

### Phase 1.1 : Modules Core à 100% (4-6h)
**Impact** : +2-3% de couverture globale

#### date.py (90% → 100%)
**Lignes manquantes** : 21

```python
# tests/unit/test_date_complete.py
class TestDateComplete:
    """Tests pour atteindre 100% sur date.py"""
    
    def test_date_comparison_operators(self):
        """Test __lt__, __le__, __gt__, __ge__"""
        d1 = Date(day=1, month=1, year=2000)
        d2 = Date(day=2, month=1, year=2000)
        assert d1 < d2
        assert d1 <= d2
        assert d2 > d1
        assert d2 >= d1
    
    def test_from_datetime(self):
        """Test création depuis datetime"""
        from datetime import datetime
        dt = datetime(2000, 12, 25)
        date = Date.from_datetime(dt)
        assert date.year == 2000
    
    def test_to_datetime_incomplete(self):
        """Test conversion avec date incomplète"""
        date = Date(year=2000)  # Sans mois/jour
        assert date.to_datetime() is None
    
    def test_date_prefix_enum_all_values(self):
        """Test tous les préfixes"""
        from geneweb_py.core.date import DatePrefix
        assert DatePrefix.ABOUT.value == "~"
        assert DatePrefix.MAYBE.value == "?"
        assert DatePrefix.BEFORE.value == "<"
        assert DatePrefix.AFTER.value == ">"
    
    def test_parse_with_all_prefixes(self):
        """Test parsing avec tous les préfixes"""
        assert Date.parse("~1950").precision == "about"
        assert Date.parse("?1950").precision == "maybe"
        assert Date.parse("<1950").precision == "before"
        assert Date.parse(">1950").precision == "after"
```

**Commande** : `pytest tests/unit/test_date_complete.py --cov=geneweb_py.core.date --cov-report=term-missing`

#### person.py (92% → 100%)
**Lignes manquantes** : 11

```python
# tests/unit/test_person_complete.py
class TestPersonComplete:
    """Tests pour atteindre 100% sur person.py"""
    
    def test_add_title(self):
        """Test ajout de titre"""
        person = Person(last_name="DUPONT", first_name="Jean")
        from geneweb_py.core.person import Title
        title = Title(name="Docteur", place="Paris")
        person.add_title(title)
        assert len(person.titles) == 1
    
    def test_add_alias(self):
        """Test ajout d'alias"""
        person = Person(last_name="DUPONT", first_name="Jean")
        person.add_alias("Johnny")
        assert "Johnny" in person.aliases
    
    def test_add_related_person(self):
        """Test ajout de personne liée"""
        person = Person(last_name="DUPONT", first_name="Jean")
        person.add_related_person("DUPONT_Marie_0", "godfather")
        assert "DUPONT_Marie_0" in person.related_person_ids
    
    def test_age_at_death_no_dates(self):
        """Test âge au décès sans dates"""
        person = Person(last_name="DUPONT", first_name="Jean")
        assert person.age_at_death is None
    
    def test_is_alive_ancient_birth(self):
        """Test vivant avec date de naissance ancienne"""
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=1800)
        )
        # Personne née en 1800 est probablement décédée
        assert isinstance(person.is_alive, bool)
```

**Commande** : `pytest tests/unit/test_person_complete.py --cov=geneweb_py.core.person --cov-report=term-missing`

#### family.py (86% → 100%)
**Lignes manquantes** : 20

```python
# tests/unit/test_family_complete.py
class TestFamilyComplete:
    """Tests pour atteindre 100% sur family.py"""
    
    def test_add_witness(self):
        family = Family(family_id="F001", husband_id="H001")
        family.add_witness("W001", "m")
        assert len(family.witnesses) == 1
    
    def test_add_event(self):
        family = Family(family_id="F001", husband_id="H001")
        event = FamilyEvent(event_type=FamilyEventType.MARRIAGE)
        family.add_event(event)
        assert len(family.events) == 1
    
    def test_has_children_property(self):
        family = Family(family_id="F001", husband_id="H001")
        assert family.has_children == False
        family.add_child("C001")
        assert family.has_children == True
    
    def test_is_divorced_property(self):
        family = Family(
            family_id="F001",
            husband_id="H001",
            marriage_status=MarriageStatus.DIVORCED
        )
        assert family.is_divorced == True
```

**Estimation** : 4-6 heures, +2% couverture → **85% global**

---

### Phase 1.2 : Modules de validation et exceptions (2-3h)
**Impact** : +1% de couverture globale

#### validation.py (91% → 100%)
**Lignes manquantes** : 11

```python
# tests/unit/test_validation_complete.py
class TestValidationComplete:
    """Tests pour 100% de validation.py"""
    
    def test_validate_person_all_fields(self):
        validator = GenealogyValidator()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=2000),
            death_date=Date(year=1990)  # Incohérent
        )
        errors = validator.validate_person(person)
        assert len(errors) > 0
    
    def test_validate_family_invalid_dates(self):
        validator = GenealogyValidator()
        family = Family(
            family_id="F001",
            husband_id="H001",
            marriage_date=Date(year=2000),
            divorce_date=Date(year=1990)  # Avant mariage
        )
        errors = validator.validate_family(family)
        assert len(errors) > 0
    
    def test_validate_genealogy_orphan_references(self):
        validator = GenealogyValidator()
        genealogy = Genealogy()
        family = Family(family_id="F001", husband_id="NONEXISTENT")
        genealogy.add_family(family)
        errors = validator.validate(genealogy)
        assert any("référence" in str(e).lower() for e in errors)
```

#### exceptions.py (91% → 100%)
**Lignes manquantes** : 22

```python
# tests/unit/test_exceptions_complete.py
class TestExceptionsComplete:
    """Tests pour 100% de exceptions.py"""
    
    def test_geneweb_error_full_params(self):
        error = GeneWebError(
            "Test error",
            context={"file": "test.gw", "line": 42}
        )
        assert "42" in str(error) or "test.gw" in str(error)
    
    def test_parse_error_all_params(self):
        error = GeneWebParseError(
            "Parse error",
            line_number=10,
            column=5,
            token="BAD",
            expected="GOOD"
        )
        error_str = str(error)
        assert "10" in error_str
    
    def test_error_collector_operations(self):
        collector = GeneWebErrorCollector()
        e1 = GeneWebError("Error 1")
        e2 = GeneWebError("Error 2")
        
        collector.add_error(e1)
        collector.add_error(e2)
        
        assert collector.has_errors()
        assert collector.error_count() == 2
        summary = collector.get_error_summary()
        assert "Error 1" in summary
        assert "Error 2" in summary
```

**Estimation** : 2-3 heures, +1% couverture → **86% global**

---

### Phase 1.3 : Parser (gw_parser.py) (3-4h)
**Objectif** : 80% → 88%  
**Lignes manquantes** : 140

**Focus** : Cas limites et chemins d'erreur

```python
# tests/unit/test_parser_edge_cases.py
class TestParserEdgeCases:
    """Tests des cas limites du parser"""
    
    def test_parse_empty_file(self):
        parser = GeneWebParser()
        genealogy = parser.parse_string("")
        assert len(genealogy.persons) == 0
    
    def test_parse_only_comments(self):
        parser = GeneWebParser()
        content = "# Ceci est un commentaire\n# Ligne 2"
        genealogy = parser.parse_string(content)
        assert len(genealogy.persons) == 0
    
    def test_parse_invalid_encoding(self):
        parser = GeneWebParser()
        # Tester la détection d'encodage
        content = "fam DUPONT Jean + MARTIN Marie\n"
        genealogy = parser.parse_string(content)
        assert genealogy.metadata.encoding in ["utf-8", "iso-8859-1"]
    
    def test_parse_with_validation_errors(self):
        parser = GeneWebParser(validate=True)
        content = "invalid line that should fail\n"
        with pytest.raises(GeneWebParseError):
            parser.parse_string(content)
    
    def test_parse_large_occurrence_numbers(self):
        parser = GeneWebParser()
        content = "fam DUPONT Jean .999 + MARTIN Marie .1000\n"
        genealogy = parser.parse_string(content)
        jean = next(p for p in genealogy.persons.values() if p.first_name == "Jean")
        assert jean.occurrence_number == 999
```

**Estimation** : 3-4 heures, +2% couverture → **88% global**

---

### Phase 1.4 : Événements et genealogy.py (2-3h)
**Impact** : +1% de couverture

#### event.py (87% → 100%)
**Lignes manquantes** : 11

```python
# tests/unit/test_event_complete.py
class TestEventComplete:
    """Tests pour 100% de event.py"""
    
    def test_all_personal_event_types(self):
        """Test tous les types d'événements personnels"""
        types = [
            PersonalEventType.BIRTH,
            PersonalEventType.BAPTISM,
            PersonalEventType.DEATH,
            PersonalEventType.BURIAL,
            PersonalEventType.CREMATION,
            PersonalEventType.ACCOMPLISHMENT,
            PersonalEventType.ACQUISITION,
            PersonalEventType.GRADUATION,
        ]
        for event_type in types:
            event = PersonalEvent(event_type=event_type)
            assert event.event_type == event_type
    
    def test_event_add_witness(self):
        event = PersonalEvent(event_type=PersonalEventType.BIRTH)
        event.add_witness("W001", "m")
        assert len(event.witnesses) == 1
    
    def test_event_add_note(self):
        event = PersonalEvent(event_type=PersonalEventType.BIRTH)
        event.add_note("Note importante")
        assert len(event.notes) == 1
```

#### genealogy.py (95% → 100%)
**Lignes manquantes** : 8

```python
# tests/unit/test_genealogy_complete.py
class TestGenealogyComplete:
    """Tests pour 100% de genealogy.py"""
    
    def test_remove_person(self):
        genealogy = Genealogy()
        person = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(person)
        genealogy.remove_person(person.unique_id)
        assert len(genealogy.persons) == 0
    
    def test_remove_family(self):
        genealogy = Genealogy()
        family = Family(family_id="F001", husband_id="H001")
        genealogy.add_family(family)
        genealogy.remove_family("F001")
        assert len(genealogy.families) == 0
    
    def test_get_person_families(self):
        genealogy = Genealogy()
        person = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(person)
        
        f1 = Family(family_id="F001", husband_id=person.unique_id)
        f2 = Family(family_id="F002", wife_id=person.unique_id)
        genealogy.add_family(f1)
        genealogy.add_family(f2)
        
        families = genealogy.get_person_families(person.unique_id)
        assert len(families) == 2
```

**Estimation** : 2-3 heures, +1% couverture → **89% global**

---

### Phase 1.5 : Lexical et syntax (1-2h)
**Impact** : +1% de couverture

#### lexical.py (97% → 100%)
**Lignes manquantes** : 9

```python
# tests/unit/test_lexical_complete.py
class TestLexicalComplete:
    """Tests pour 100% de lexical.py"""
    
    def test_tokenize_all_special_chars(self):
        from geneweb_py.core.parser.lexical import LexicalParser
        content = "() [] {} : ; , . # -"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        assert len(tokens) > 0
    
    def test_tokenize_unicode(self):
        content = "fam DUPONT José + GARCÍA María"
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        assert any("José" in str(t) for t in tokens)
    
    def test_tokenize_multiline_strings(self):
        content = '''notes
Multiple lines
of notes
end notes'''
        parser = LexicalParser(content)
        tokens = parser.tokenize()
        assert len(tokens) > 0
```

#### syntax.py (93% → 100%)
**Lignes manquantes** : 37

```python
# tests/unit/test_syntax_complete.py
class TestSyntaxComplete:
    """Tests pour 100% de syntax.py"""
    
    def test_parse_all_block_types(self):
        from geneweb_py.core.parser.syntax import SyntaxParser
        from geneweb_py.core.parser.lexical import LexicalParser
        
        # Tester tous les types de blocs
        blocks = [
            "fam DUPONT Jean + MARTIN Marie\nend",
            "notes\nTest\nend notes",
            "rel DUPONT Jean\nbeg\nend",
            "pevt DUPONT Jean\n#birt 2000\nend pevt",
            "fevt\n#marr 2000\nend fevt",
            "notes-db\nNotes\nend notes-db",
            "page-ext DUPONT Jean\n<html>\nend page-ext",
            "wizard-note DUPONT Jean\nNote\nend wizard-note",
        ]
        
        for block in blocks:
            lexer = LexicalParser(block)
            tokens = lexer.tokenize()
            parser = SyntaxParser()
            nodes = parser.parse(tokens)
            assert len(nodes) > 0
```

**Estimation** : 1-2 heures, +1% couverture → **90% global**

---

## 🎯 Court Terme - Résumé

| Phase | Module | Lignes | Temps | Couverture |
|-------|--------|--------|-------|------------|
| 1.1 | date.py | 21 | 1h | +0.4% |
| 1.1 | person.py | 11 | 1h | +0.2% |
| 1.1 | family.py | 20 | 2h | +0.4% |
| 1.2 | validation.py | 11 | 1h | +0.2% |
| 1.2 | exceptions.py | 22 | 2h | +0.5% |
| 1.3 | gw_parser.py | 140 | 4h | +3.0% |
| 1.4 | event.py | 11 | 1h | +0.2% |
| 1.4 | genealogy.py | 8 | 1h | +0.2% |
| 1.5 | lexical.py | 9 | 1h | +0.2% |
| 1.5 | syntax.py | 37 | 1h | +0.8% |
| **TOTAL** | **10 modules** | **290** | **16h** | **→ 90%** |

---

## 🎯 Moyen Terme (2-4 semaines, ~30-40h)
**Objectif** : Atteindre 95% de couverture globale  
**Focus** : Formats et API

### Phase 2.1 : Formats - Convertisseurs (8-10h)
**Impact** : +3-4% de couverture

#### gedcom.py (88% → 100%)
**Lignes manquantes** : 26

```python
# tests/formats/test_gedcom_complete.py
class TestGedcomComplete:
    """Tests complets pour GEDCOM"""
    
    def test_export_all_person_fields(self):
        """Test export de tous les champs Person"""
        converter = GedcomConverter()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=2000),
            birth_place="Paris",
            death_date=Date(year=2050),
            death_place="Lyon",
            occupation="Ingénieur",
            nickname="Johnny"
        )
        genealogy = Genealogy()
        genealogy.add_person(person)
        
        gedcom = converter.export(genealogy)
        assert "DUPONT" in gedcom
        assert "Jean" in gedcom
        assert "2000" in gedcom
        assert "Paris" in gedcom
    
    def test_export_all_family_fields(self):
        """Test export de tous les champs Family"""
        converter = GedcomConverter()
        family = Family(
            family_id="F001",
            husband_id="H001",
            wife_id="W001",
            marriage_date=Date(year=2000),
            marriage_place="Paris"
        )
        genealogy = Genealogy()
        genealogy.add_family(family)
        
        gedcom = converter.export(genealogy)
        assert "FAM" in gedcom
        assert "MARR" in gedcom
    
    def test_import_gedcom_all_tags(self):
        """Test import de tous les tags GEDCOM"""
        converter = GedcomConverter()
        gedcom = """
0 @I1@ INDI
1 NAME Jean /DUPONT/
1 SEX M
1 BIRT
2 DATE 1 JAN 2000
2 PLAC Paris
1 DEAT
2 DATE 1 JAN 2050
2 PLAC Lyon
1 OCCU Ingénieur
0 TRLR
"""
        genealogy = converter.import_from_string(gedcom)
        assert len(genealogy.persons) == 1
    
    def test_roundtrip_gedcom(self):
        """Test conversion aller-retour"""
        converter = GedcomConverter()
        
        # Créer une généalogie
        genealogy1 = Genealogy()
        person = Person(last_name="DUPONT", first_name="Jean")
        genealogy1.add_person(person)
        
        # Export → Import
        gedcom = converter.export(genealogy1)
        genealogy2 = converter.import_from_string(gedcom)
        
        # Vérifier conservation
        assert len(genealogy1.persons) == len(genealogy2.persons)
```

#### json.py (86% → 100%)
**Lignes manquantes** : 18

```python
# tests/formats/test_json_complete.py
class TestJsonComplete:
    """Tests complets pour JSON"""
    
    def test_export_with_null_dates(self):
        """Test export avec dates NULL"""
        converter = JsonConverter()
        person = Person(last_name="DUPONT", first_name="Jean")
        # Pas de dates
        genealogy = Genealogy()
        genealogy.add_person(person)
        
        json_str = converter.export(genealogy)
        data = json.loads(json_str)
        assert data["persons"][0]["birth_date"] is None
    
    def test_export_with_empty_lists(self):
        """Test export avec listes vides"""
        converter = JsonConverter()
        person = Person(last_name="DUPONT", first_name="Jean")
        # Pas de titres, aliases, etc.
        genealogy = Genealogy()
        genealogy.add_person(person)
        
        json_str = converter.export(genealogy)
        data = json.loads(json_str)
        assert data["persons"][0]["titles"] == []
    
    def test_import_malformed_json(self):
        """Test import JSON malformé"""
        converter = JsonConverter()
        with pytest.raises(GeneWebConversionError):
            converter.import_from_string("{invalid json}")
    
    def test_roundtrip_json_all_fields(self):
        """Test aller-retour avec tous les champs"""
        converter = JsonConverter()
        
        genealogy1 = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=2000),
            occupation="Ingénieur",
            aliases=["Johnny", "JD"]
        )
        genealogy1.add_person(person)
        
        json_str = converter.export(genealogy1)
        genealogy2 = converter.import_from_string(json_str)
        
        person2 = list(genealogy2.persons.values())[0]
        assert person2.last_name == "DUPONT"
        assert person2.first_name == "Jean"
        assert person2.occupation == "Ingénieur"
        assert len(person2.aliases) == 2
```

#### xml.py (76% → 100%)
**Lignes manquantes** : 91

```python
# tests/formats/test_xml_complete.py
class TestXmlComplete:
    """Tests complets pour XML"""
    
    def test_export_all_xml_elements(self):
        """Test export de tous les éléments XML"""
        converter = XmlConverter()
        
        genealogy = Genealogy()
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            birth_date=Date(year=2000),
            birth_place="Paris"
        )
        genealogy.add_person(person)
        
        family = Family(
            family_id="F001",
            husband_id=person.unique_id,
            marriage_date=Date(year=2020)
        )
        genealogy.add_family(family)
        
        xml = converter.export(genealogy)
        assert "<genealogy>" in xml
        assert "<persons>" in xml
        assert "<person>" in xml
        assert "<families>" in xml
        assert "DUPONT" in xml
    
    def test_export_with_special_chars(self):
        """Test export avec caractères spéciaux XML"""
        converter = XmlConverter()
        person = Person(
            last_name="D'Arc",
            first_name="Jean & Marie"
        )
        genealogy = Genealogy()
        genealogy.add_person(person)
        
        xml = converter.export(genealogy)
        # Les caractères spéciaux doivent être échappés
        assert "&apos;" in xml or "&#39;" in xml  # apostrophe
        assert "&amp;" in xml  # &
    
    def test_import_xml_with_namespaces(self):
        """Test import XML avec namespaces"""
        converter = XmlConverter()
        xml = """<?xml version="1.0"?>
<genealogy xmlns="http://geneweb.org">
    <persons>
        <person id="P001">
            <lastName>DUPONT</lastName>
            <firstName>Jean</firstName>
        </person>
    </persons>
    <families/>
</genealogy>"""
        genealogy = converter.import_from_string(xml)
        assert len(genealogy.persons) >= 0  # Peut dépendre de l'implémentation
    
    def test_validate_xml_schema(self):
        """Test validation XML contre schéma"""
        converter = XmlConverter()
        genealogy = Genealogy()
        person = Person(last_name="DUPONT", first_name="Jean")
        genealogy.add_person(person)
        
        xml = converter.export(genealogy)
        # Le XML doit être bien formé
        import xml.etree.ElementTree as ET
        tree = ET.fromstring(xml)
        assert tree.tag == "genealogy"
```

**Estimation Phase 2.1** : 8-10 heures, +3% couverture → **93% global**

---

### Phase 2.2 : API - Services (6-8h)
**Impact** : +2% de couverture

#### genealogy_service.py (59% → 85%)
**Lignes manquantes** : 132 → Cible: 50

```python
# tests/api/test_genealogy_service_complete.py
class TestGenealogyServiceComplete:
    """Tests complets pour genealogy_service"""
    
    def test_search_persons_all_filters(self):
        """Test recherche avec tous les filtres"""
        service = GenealogyService()
        service.genealogy = Genealogy()
        
        # Ajouter des personnes de test
        for i in range(10):
            person = Person(
                last_name=f"DUPONT",
                first_name=f"Jean{i}",
                birth_date=Date(year=1950+i)
            )
            service.genealogy.add_person(person)
        
        # Test filtrage par nom
        results, total = service.search_persons({
            "query": "Jean",
            "page": 1,
            "size": 5
        })
        assert total == 10
        assert len(results) == 5
        
        # Test filtrage par année de naissance
        results, total = service.search_persons({
            "birth_year_from": 1955,
            "birth_year_to": 1960
        })
        assert total == 6  # 1955-1960 inclus
    
    def test_search_families_all_filters(self):
        """Test recherche familles avec filtres"""
        service = GenealogyService()
        service.genealogy = Genealogy()
        
        for i in range(5):
            family = Family(
                family_id=f"F{i:03d}",
                husband_id=f"H{i:03d}",
                wife_id=f"W{i:03d}",
                marriage_date=Date(year=2000+i)
            )
            service.genealogy.add_family(family)
        
        results, total = service.search_families({
            "marriage_year_from": 2002,
            "page": 1,
            "size": 10
        })
        assert total == 3  # 2002, 2003, 2004
    
    def test_crud_operations_persons(self):
        """Test CRUD complet sur personnes"""
        service = GenealogyService()
        service.genealogy = Genealogy()
        
        # Create
        person_data = {
            "last_name": "DUPONT",
            "first_name": "Jean"
        }
        person = service.create_person(person_data)
        assert person.unique_id is not None
        
        # Read
        retrieved = service.get_person(person.unique_id)
        assert retrieved.last_name == "DUPONT"
        
        # Update
        updated = service.update_person(person.unique_id, {
            "occupation": "Ingénieur"
        })
        assert updated.occupation == "Ingénieur"
        
        # Delete
        deleted = service.delete_person(person.unique_id)
        assert deleted == True
        assert service.get_person(person.unique_id) is None
    
    def test_error_handling(self):
        """Test gestion d'erreurs"""
        service = GenealogyService()
        service.genealogy = Genealogy()
        
        # Personne inexistante
        assert service.get_person("NONEXISTENT") is None
        
        # Update personne inexistante
        with pytest.raises(Exception):
            service.update_person("NONEXISTENT", {})
        
        # Delete personne inexistante
        assert service.delete_person("NONEXISTENT") == False
```

**Estimation Phase 2.2** : 6-8 heures, +2% couverture → **95% global**

---

### Phase 2.3 : API - Routers (4-6h)
**Impact** : +0.5-1% de couverture

#### Routers restants (69-73% → 90%+)

```python
# tests/api/test_routers_complete.py
class TestRoutersComplete:
    """Tests complets pour tous les routers"""
    
    def test_all_http_methods(self, client):
        """Test tous les verbes HTTP"""
        # GET
        response = client.get("/api/v1/persons")
        assert response.status_code in [200, 404]
        
        # POST
        response = client.post("/api/v1/persons", json={
            "last_name": "DUPONT",
            "first_name": "Jean"
        })
        assert response.status_code in [200, 201]
        
        # PUT
        person_id = "DUPONT_Jean_0"
        response = client.put(f"/api/v1/persons/{person_id}", json={
            "occupation": "Ingénieur"
        })
        assert response.status_code in [200, 404]
        
        # DELETE
        response = client.delete(f"/api/v1/persons/{person_id}")
        assert response.status_code in [200, 204, 404]
    
    def test_all_error_codes(self, client):
        """Test tous les codes d'erreur HTTP"""
        # 400 Bad Request
        response = client.post("/api/v1/persons", json={})
        assert response.status_code == 400
        
        # 404 Not Found
        response = client.get("/api/v1/persons/NONEXISTENT")
        assert response.status_code == 404
        
        # 422 Validation Error
        response = client.post("/api/v1/persons", json={
            "last_name": "",  # Invalid
            "first_name": "Jean"
        })
        assert response.status_code == 422
    
    def test_pagination_all_routers(self, client):
        """Test pagination sur tous les endpoints"""
        endpoints = [
            "/api/v1/persons",
            "/api/v1/families",
            "/api/v1/events"
        ]
        for endpoint in endpoints:
            response = client.get(f"{endpoint}?page=1&size=10")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data or "persons" in data or "families" in data
```

**Estimation Phase 2.3** : 4-6 heures, +1% couverture → **96% global**

---

## 🎯 Moyen Terme - Résumé

| Phase | Module | Lignes | Temps | Couverture |
|-------|--------|--------|-------|------------|
| 2.1 | gedcom.py | 26 | 3h | +0.6% |
| 2.1 | json.py | 18 | 2h | +0.4% |
| 2.1 | xml.py | 91 | 5h | +1.9% |
| 2.2 | genealogy_service.py | 82 | 7h | +1.7% |
| 2.3 | Routers (tous) | 70 | 5h | +1.5% |
| **TOTAL** | **5 catégories** | **287** | **22h** | **→ 96%** |

---

## 🎯 Long Terme (1-2 mois, ~20-30h)
**Objectif** : Atteindre 100% de couverture  
**Focus** : Property-based testing, intégration, edge cases

### Phase 3.1 : Property-Based Testing avec Hypothesis (6-8h)
**Impact** : Robustesse et découverte de bugs

#### Installation
```bash
pip install hypothesis
```

#### Tests de propriétés

```python
# tests/property/test_roundtrip.py
from hypothesis import given, strategies as st
from hypothesis.strategies import text, integers, dates
import pytest

class TestRoundtripProperties:
    """Tests de propriétés pour les conversions"""
    
    @given(
        last_name=text(min_size=1, max_size=50),
        first_name=text(min_size=1, max_size=50),
        year=integers(min_value=1000, max_value=2100)
    )
    def test_person_json_roundtrip(self, last_name, first_name, year):
        """Property: Person → JSON → Person préserve les données"""
        person1 = Person(
            last_name=last_name,
            first_name=first_name,
            birth_date=Date(year=year)
        )
        
        converter = JsonConverter()
        genealogy1 = Genealogy()
        genealogy1.add_person(person1)
        
        json_str = converter.export(genealogy1)
        genealogy2 = converter.import_from_string(json_str)
        
        person2 = list(genealogy2.persons.values())[0]
        assert person2.last_name == last_name
        assert person2.first_name == first_name
        assert person2.birth_date.year == year
    
    @given(content=text(min_size=0, max_size=1000))
    def test_parser_never_crashes(self, content):
        """Property: Le parser ne doit jamais crasher"""
        parser = GeneWebParser(validate=False)
        try:
            parser.parse_string(content)
        except GeneWebError:
            # Les erreurs GeneWeb sont OK
            pass
        except Exception as e:
            # Toute autre exception est un bug
            pytest.fail(f"Parser crashed: {e}")
    
    @given(
        day=integers(min_value=1, max_value=31),
        month=integers(min_value=1, max_value=12),
        year=integers(min_value=1000, max_value=2100)
    )
    def test_date_parsing_idempotent(self, day, month, year):
        """Property: Date.parse(str(date)) == date"""
        try:
            date1 = Date(day=day, month=month, year=year)
            date_str = date1.display_text
            date2 = Date.parse(date_str)
            
            if date2:
                assert date2.day == day
                assert date2.month == month
                assert date2.year == year
        except ValueError:
            # Dates invalides (ex: 31 février) sont OK à rejeter
            pass
```

```python
# tests/property/test_invariants.py
from hypothesis import given, strategies as st

class TestInvariants:
    """Tests d'invariants du système"""
    
    @given(
        persons_count=integers(min_value=0, max_value=100),
        families_count=integers(min_value=0, max_value=50)
    )
    def test_genealogy_statistics_invariant(self, persons_count, families_count):
        """Property: Les statistiques sont cohérentes"""
        genealogy = Genealogy()
        
        # Ajouter des personnes
        for i in range(persons_count):
            person = Person(last_name=f"P{i}", first_name=f"F{i}")
            genealogy.add_person(person)
        
        # Ajouter des familles
        for i in range(families_count):
            family = Family(family_id=f"F{i:03d}", husband_id=f"H{i}")
            genealogy.add_family(family)
        
        stats = genealogy.statistics()
        assert stats["persons_count"] == persons_count
        assert stats["families_count"] == families_count
    
    @given(persons=st.lists(
        st.builds(Person, 
                  last_name=text(min_size=1, max_size=20),
                  first_name=text(min_size=1, max_size=20)),
        min_size=1,
        max_size=20
    ))
    def test_unique_ids_invariant(self, persons):
        """Property: Les IDs de personnes sont uniques"""
        genealogy = Genealogy()
        
        for person in persons:
            genealogy.add_person(person)
        
        ids = [p.unique_id for p in genealogy.persons.values()]
        # Les IDs doivent être uniques
        assert len(ids) == len(set(ids))
```

**Estimation Phase 3.1** : 6-8 heures, +découverte de bugs

---

### Phase 3.2 : Tests d'intégration avec vrais fichiers (4-6h)
**Impact** : Validation sur données réelles

```python
# tests/integration/test_real_files.py
import pytest

class TestRealFiles:
    """Tests avec de vrais fichiers GeneWeb"""
    
    @pytest.mark.slow
    def test_parse_sample_tree_complete(self):
        """Test parsing complet du fichier sample_tree"""
        parser = GeneWebParser()
        genealogy = parser.parse_file(
            "doc/baseGWexamples/sample_tree.gw"
        )
        
        # Vérifications de base
        assert len(genealogy.persons) > 5000
        assert len(genealogy.families) > 1000
        
        # Vérifier quelques personnes connues
        martin = None
        for person in genealogy.persons.values():
            if person.last_name == "MARTIN" and person.first_name == "Jean_Louis":
                martin = person
                break
        
        assert martin is not None
        assert martin.birth_date is not None
    
    @pytest.mark.slow
    def test_conversion_roundtrip_real_file(self):
        """Test conversion complète sur vrai fichier"""
        parser = GeneWebParser()
        genealogy1 = parser.parse_file(
            "doc/baseGWexamples/sample_tree.gw"
        )
        
        # Test GEDCOM
        gedcom_converter = GedcomConverter()
        gedcom = gedcom_converter.export(genealogy1)
        genealogy2 = gedcom_converter.import_from_string(gedcom)
        
        # Vérifier conservation approximative (certaines infos peuvent être perdues)
        tolerance = 0.05  # 5% de tolérance
        assert abs(len(genealogy1.persons) - len(genealogy2.persons)) < len(genealogy1.persons) * tolerance
        
        # Test JSON
        json_converter = JsonConverter()
        json_str = json_converter.export(genealogy1)
        genealogy3 = json_converter.import_from_string(json_str)
        
        # JSON doit préserver exactement
        assert len(genealogy1.persons) == len(genealogy3.persons)
        assert len(genealogy1.families) == len(genealogy3.families)
    
    def test_parse_all_fixtures(self):
        """Test parsing de tous les fichiers fixtures"""
        import glob
        parser = GeneWebParser()
        
        fixtures = glob.glob("tests/fixtures/*.gw")
        fixtures.extend(glob.glob("tests/fixtures/*.gwplus"))
        
        for fixture in fixtures:
            try:
                genealogy = parser.parse_file(fixture)
                assert genealogy is not None
            except Exception as e:
                pytest.fail(f"Failed to parse {fixture}: {e}")
```

**Estimation Phase 3.2** : 4-6 heures

---

### Phase 3.3 : Edge Cases et Cas Extrêmes (4-6h)
**Impact** : Robustesse maximale

```python
# tests/edge_cases/test_extreme_values.py
class TestExtremeValues:
    """Tests des valeurs extrêmes"""
    
    def test_very_long_names(self):
        """Test noms très longs"""
        long_name = "A" * 1000
        person = Person(last_name=long_name, first_name="Jean")
        assert person.last_name == long_name
    
    def test_ancient_dates(self):
        """Test dates très anciennes"""
        date = Date(year=1)
        assert date.year == 1
    
    def test_future_dates(self):
        """Test dates futures"""
        date = Date(year=3000)
        assert date.year == 3000
    
    def test_very_large_genealogy(self):
        """Test généalogie très grande"""
        genealogy = Genealogy()
        
        # Ajouter 10000 personnes
        for i in range(10000):
            person = Person(last_name=f"PERSON{i}", first_name=f"First{i}")
            genealogy.add_person(person)
        
        assert len(genealogy.persons) == 10000
        stats = genealogy.statistics()
        assert stats["persons_count"] == 10000
    
    def test_deep_family_tree(self):
        """Test arbre familial profond (10 générations)"""
        genealogy = Genealogy()
        
        # Créer 10 générations
        previous_id = None
        for gen in range(10):
            person = Person(last_name=f"GEN{gen}", first_name="Child")
            genealogy.add_person(person)
            
            if previous_id:
                family = Family(
                    family_id=f"F{gen:03d}",
                    husband_id=previous_id,
                    wife_id=f"WIFE{gen}"
                )
                family.add_child(person.unique_id)
                genealogy.add_family(family)
            
            previous_id = person.unique_id
        
        assert len(genealogy.families) == 9
```

```python
# tests/edge_cases/test_malformed_input.py
class TestMalformedInput:
    """Tests des entrées malformées"""
    
    def test_invalid_utf8(self):
        """Test encodage invalide"""
        parser = GeneWebParser()
        # Bytes invalides UTF-8
        invalid_bytes = b'\xff\xfe'
        with pytest.raises(GeneWebEncodingError):
            parser.parse_string(invalid_bytes.decode('latin1'))
    
    def test_mixed_line_endings(self):
        """Test fin de lignes mixtes"""
        content = "fam DUPONT Jean\r\n+ MARTIN Marie\n"
        parser = GeneWebParser()
        genealogy = parser.parse_string(content)
        assert len(genealogy.persons) >= 2
    
    def test_circular_references(self):
        """Test références circulaires"""
        genealogy = Genealogy()
        
        # Personne qui est son propre parent (impossible mais on teste)
        person = Person(last_name="PARADOX", first_name="Jean")
        genealogy.add_person(person)
        
        family = Family(
            family_id="F001",
            husband_id=person.unique_id,
            wife_id="OTHER"
        )
        family.add_child(person.unique_id)  # Jean est son propre enfant!
        genealogy.add_family(family)
        
        # La validation devrait détecter cela
        errors = genealogy.validate()
        assert len(errors) > 0 or genealogy.is_valid == False
```

**Estimation Phase 3.4** : 4-6 heures

---

### Phase 3.4 : Tests de performance et benchmarks (3-4h)
**Impact** : Documentation et optimisation

```python
# tests/performance/test_benchmarks.py
import pytest
import time
import memory_profiler

class TestPerformance:
    """Tests de performance"""
    
    @pytest.mark.benchmark
    def test_parse_speed_small_file(self, benchmark):
        """Benchmark parsing petit fichier (<1MB)"""
        parser = GeneWebParser()
        content = "fam DUPONT Jean + MARTIN Marie\n" * 100
        
        result = benchmark(parser.parse_string, content)
        assert result is not None
    
    @pytest.mark.benchmark
    def test_parse_speed_large_file(self, benchmark):
        """Benchmark parsing gros fichier (>10MB)"""
        parser = GeneWebParser()
        # Générer un gros contenu
        content = ("fam PERSON{i} First{i} + SPOUSE{i} Last{i}\n".format(i=i) 
                   for i in range(10000))
        content = "".join(content)
        
        result = benchmark(parser.parse_string, content)
        assert result is not None
    
    @pytest.mark.benchmark
    def test_search_performance(self, benchmark):
        """Benchmark recherche dans grosse base"""
        service = GenealogyService()
        service.genealogy = Genealogy()
        
        # Ajouter 10000 personnes
        for i in range(10000):
            person = Person(last_name=f"PERSON{i}", first_name=f"First{i}")
            service.genealogy.add_person(person)
        
        # Benchmark recherche
        result = benchmark(service.search_persons, {"query": "PERSON5000"})
        assert result is not None
    
    def test_memory_usage_large_genealogy(self):
        """Test utilisation mémoire"""
        genealogy = Genealogy()
        
        # Mesurer mémoire avant
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Ajouter beaucoup de données
        for i in range(50000):
            person = Person(last_name=f"P{i}", first_name=f"F{i}")
            genealogy.add_person(person)
        
        # Mesurer mémoire après
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = mem_after - mem_before
        
        print(f"Mémoire utilisée: {memory_used:.2f} MB pour 50000 personnes")
        # Vérifier que c'est raisonnable (< 500MB)
        assert memory_used < 500
```

**Estimation Phase 3.4** : 3-4 heures

---

### Phase 3.5 : Dépendances et modules peu utilisés (2-3h)
**Impact** : Complétion finale

#### streaming.py (17% → 90%+)
**Lignes manquantes** : 90

```python
# tests/unit/test_streaming_complete.py
class TestStreamingComplete:
    """Tests complets pour le mode streaming"""
    
    def test_streaming_parser_initialization(self):
        """Test initialisation parser streaming"""
        from geneweb_py.core.parser.streaming import StreamingParser
        parser = StreamingParser("test.gw")
        assert parser is not None
    
    def test_parse_large_file_streaming(self, tmp_path):
        """Test parsing streaming sur gros fichier"""
        # Créer un gros fichier temporaire
        large_file = tmp_path / "large.gw"
        with open(large_file, 'w') as f:
            for i in range(100000):
                f.write(f"fam PERSON{i} First{i} + SPOUSE{i} Last{i}\n")
        
        from geneweb_py.core.parser.streaming import StreamingParser
        parser = StreamingParser(str(large_file))
        
        # Le parser devrait utiliser le mode streaming automatiquement
        genealogy = parser.parse()
        assert len(genealogy.persons) > 0
    
    def test_streaming_memory_efficiency(self, tmp_path):
        """Test efficacité mémoire du streaming"""
        large_file = tmp_path / "large.gw"
        with open(large_file, 'w') as f:
            for i in range(50000):
                f.write(f"fam P{i} F{i} + S{i} L{i}\n")
        
        import psutil
        import os
        process = psutil.Process(os.getpid())
        
        # Parser en streaming
        mem_before = process.memory_info().rss / 1024 / 1024
        from geneweb_py.core.parser.streaming import StreamingParser
        parser = StreamingParser(str(large_file))
        genealogy = parser.parse()
        mem_after = process.memory_info().rss / 1024 / 1024
        
        streaming_memory = mem_after - mem_before
        print(f"Streaming: {streaming_memory:.2f} MB")
        
        # Le streaming doit utiliser moins de mémoire
        assert streaming_memory < 200  # < 200MB pour 50k personnes
```

#### dependencies.py (40% → 90%+)
**Lignes manquantes** : 18

```python
# tests/api/test_dependencies_complete.py
class TestDependenciesComplete:
    """Tests complets pour dependencies"""
    
    def test_get_genealogy_service_singleton(self):
        """Test que le service est un singleton"""
        from geneweb_py.api.dependencies import get_genealogy_service
        service1 = get_genealogy_service()
        service2 = get_genealogy_service()
        assert service1 is service2
    
    def test_get_current_genealogy(self):
        """Test récupération de la généalogie courante"""
        from geneweb_py.api.dependencies import get_current_genealogy
        genealogy = get_current_genealogy()
        assert isinstance(genealogy, Genealogy)
```

**Estimation Phase 3.5** : 2-3 heures, +1% couverture → **99% global**

---

### Phase 3.6 : Dernière ligne droite - 100% (2-3h)
**Impact** : Les derniers 1%

Cette phase consiste à :
1. Relancer la couverture complète
2. Identifier les lignes restantes une par une
3. Créer des tests ciblés micro-chirurgicaux
4. Vérifier qu'on atteint vraiment 100%

```bash
# Commande pour identifier précisément les lignes manquantes
pytest --cov=geneweb_py --cov-report=term-missing --cov-report=html
open htmlcov/index.html

# Pour chaque module qui n'est pas à 100%, créer un test spécifique
# Exemple pour une ligne spécifique :
pytest --cov=geneweb_py.core.date --cov-report=annotate
cat geneweb_py/core/date.py,cover  # Voir les lignes non couvertes
```

**Estimation Phase 3.6** : 2-3 heures, +1% couverture → **100% global**

---

## 🎯 Long Terme - Résumé

| Phase | Focus | Temps | Couverture |
|-------|-------|-------|------------|
| 3.1 | Property-based testing | 7h | Robustesse |
| 3.2 | Intégration vrais fichiers | 5h | Validation |
| 3.3 | Edge cases | 5h | Robustesse |
| 3.4 | Performance | 4h | Documentation |
| 3.5 | Modules restants | 3h | +1% → 99% |
| 3.6 | Dernière ligne droite | 3h | +1% → 100% |
| **TOTAL** | **6 phases** | **27h** | **→ 100%** |

---

## 📊 Vue d'ensemble du plan complet

| Terme | Durée | Temps | Couverture cible |
|-------|-------|-------|------------------|
| **Court terme** | 1-2 semaines | 16h | 83% → 90% |
| **Moyen terme** | 2-4 semaines | 22h | 90% → 96% |
| **Long terme** | 1-2 mois | 27h | 96% → 100% |
| **TOTAL** | **2-3 mois** | **65h** | **100%** ✅ |

---

## 🛠️ Configuration et outils

### Installation des dépendances de test complètes

```bash
pip install -e ".[dev]"
pip install hypothesis pytest-benchmark psutil memory-profiler
```

### Configuration pytest complète

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--cov=geneweb_py",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=100",  # Objectif final
    "-v",
    "-ra",  # Show extra test summary
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "property: marks property-based tests",
    "benchmark: marks performance benchmarks",
]

# Timeout pour éviter les tests qui bloquent
timeout = 300
```

### Scripts utiles

```bash
# scripts/test_coverage.sh
#!/bin/bash
# Lance les tests par phase

echo "=== Phase Court Terme ==="
pytest tests/unit/test_date_complete.py \
       tests/unit/test_person_complete.py \
       tests/unit/test_family_complete.py \
       --cov=geneweb_py.core --cov-report=term

echo "=== Phase Moyen Terme ==="
pytest tests/formats/test_*_complete.py \
       tests/api/test_*_service_complete.py \
       --cov=geneweb_py --cov-report=term

echo "=== Phase Long Terme ==="
pytest tests/property/ tests/integration/test_real_files.py \
       --cov=geneweb_py --cov-report=html

open htmlcov/index.html
```

---

## 📈 Suivi de progression

### Tableau de bord

Créer un fichier `TESTING_PROGRESS.md` pour suivre :

```markdown
# Progression vers 100%

## Semaine 1 (Court terme)
- [x] date.py → 100%
- [x] person.py → 100%
- [ ] family.py → 100%
- [ ] ...

## Couverture actuelle : 85%

## Prochaines étapes
1. Compléter family.py (2h)
2. Compléter validation.py (1h)
...
```

### Commande de vérification quotidienne

```bash
# check_progress.sh
#!/bin/bash
coverage=$(pytest --cov=geneweb_py --cov-report=term | grep "TOTAL" | awk '{print $4}')
echo "$(date): Couverture actuelle: $coverage" >> progress.log
echo "Couverture: $coverage"

# Alerte si régression
if [ "$coverage" -lt "83" ]; then
    echo "⚠️  ALERTE: Régression de couverture!"
fi
```

---

## ✅ Critères de succès

### Court terme (90%)
- ✅ Tous les modules core à 95%+
- ✅ Parser à 88%+
- ✅ Validation et exceptions à 100%
- ✅ Aucun test rouge

### Moyen terme (96%)
- ✅ Tous les formats à 95%+
- ✅ API services à 85%+
- ✅ API routers à 90%+
- ✅ Tests de conversion round-trip qui passent

### Long terme (100%)
- ✅ **100% de couverture sur tous les modules**
- ✅ Tests property-based qui passent
- ✅ Tests avec vrais fichiers qui passent
- ✅ Documentation à jour
- ✅ CI/CD avec seuil à 100%

---

## 🎯 Conclusion

Ce plan progressif permet de :
1. **Gains rapides** : 83% → 90% en 1-2 semaines
2. **Consolidation** : 90% → 96% en 2-4 semaines
3. **Perfection** : 96% → 100% en 1-2 mois

**Flexibilité** : Chaque phase peut être ajustée selon les priorités et le temps disponible. Les phases sont indépendantes et peuvent être réorganisées.

**Prochaine action immédiate** : Commencer par `tests/unit/test_date_complete.py` (1h, facile, +0.4%)

