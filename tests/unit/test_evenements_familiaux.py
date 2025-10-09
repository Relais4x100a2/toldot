"""
Tests pour le parsing des événements familiaux avancés
"""

import pytest
from geneweb_py.core.parser.gw_parser import GeneWebParser


class TestEvenementsFamiliaux:
    """Tests pour le parsing des événements familiaux avancés"""

    def test_parser_fevt_avec_mariage(self):
        """Test le parsing d'un bloc fevt avec mariage"""
        content = """fevt
#marr 11/5/1932 #p Paris,_75001,_Paris,_Ile-de-France,_France
wit m: DUPONT Pierre
wit f: MARTIN Claire
end fevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud fevt a été créé
        fevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "family_events"
        ]
        assert len(fevt_nodes) == 1

        fevt_node = fevt_nodes[0]

        # Vérifier que l'événement de mariage est dans les tokens
        marr_tokens = [
            token for token in fevt_node.tokens if token.type.value == "marr"
        ]
        assert len(marr_tokens) == 1

        # Vérifier que les témoins sont parsés
        assert "witnesses" in fevt_node.metadata
        witnesses = fevt_node.metadata["witnesses"]
        assert len(witnesses) == 2

    def test_parser_fevt_avec_divorce(self):
        """Test le parsing d'un bloc fevt avec divorce"""
        content = """fevt
#marr 11/5/1932 #p Paris,_75001,_Paris,_Ile-de-France,_France
#div 15/8/1940 #p Lyon,_69001,_Rhône,_Auvergne-Rhône-Alpes,_France
end fevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud fevt a été créé
        fevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "family_events"
        ]
        assert len(fevt_nodes) == 1

        fevt_node = fevt_nodes[0]

        # Vérifier que les événements sont dans les tokens
        marr_tokens = [
            token for token in fevt_node.tokens if token.type.value == "marr"
        ]
        div_tokens = [token for token in fevt_node.tokens if token.type.value == "div"]

        assert len(marr_tokens) == 1
        assert len(div_tokens) == 1

    def test_parser_fevt_avec_separation(self):
        """Test le parsing d'un bloc fevt avec séparation"""
        content = """fevt
#marr 11/5/1932 #p Paris,_75001,_Paris,_Ile-de-France,_France
#sep 15/8/1940 #p Lyon,_69001,_Rhône,_Auvergne-Rhône-Alpes,_France
end fevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud fevt a été créé
        fevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "family_events"
        ]
        assert len(fevt_nodes) == 1

        fevt_node = fevt_nodes[0]

        # Vérifier que les événements sont dans les tokens
        marr_tokens = [
            token for token in fevt_node.tokens if token.type.value == "marr"
        ]
        sep_tokens = [token for token in fevt_node.tokens if token.type.value == "sep"]

        assert len(marr_tokens) == 1
        assert len(sep_tokens) == 1

    def test_parser_fevt_avec_fiancailles(self):
        """Test le parsing d'un bloc fevt avec fiançailles"""
        content = """fevt
#enga 1/1/1930 #p Paris,_75001,_Paris,_Ile-de-France,_France
#marr 11/5/1932 #p Paris,_75001,_Paris,_Ile-de-France,_France
end fevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud fevt a été créé
        fevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "family_events"
        ]
        assert len(fevt_nodes) == 1

        fevt_node = fevt_nodes[0]

        # Vérifier que les événements sont dans les tokens
        enga_tokens = [
            token for token in fevt_node.tokens if token.type.value == "enga"
        ]
        marr_tokens = [
            token for token in fevt_node.tokens if token.type.value == "marr"
        ]

        assert len(enga_tokens) == 1
        assert len(marr_tokens) == 1

    def test_parser_fevt_avec_dates_vides(self):
        """Test le parsing d'un bloc fevt avec dates vides"""
        content = """fevt
#marr
#div
end fevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud fevt a été créé
        fevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "family_events"
        ]
        assert len(fevt_nodes) == 1

        fevt_node = fevt_nodes[0]

        # Vérifier que les événements sont dans les tokens
        marr_tokens = [
            token for token in fevt_node.tokens if token.type.value == "marr"
        ]
        div_tokens = [token for token in fevt_node.tokens if token.type.value == "div"]

        assert len(marr_tokens) == 1
        assert len(div_tokens) == 1

    def test_parser_fevt_avec_lieux_vides(self):
        """Test le parsing d'un bloc fevt avec lieux vides"""
        content = """fevt
#marr 11/5/1932
#div 15/8/1940
end fevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud fevt a été créé
        fevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "family_events"
        ]
        assert len(fevt_nodes) == 1

        fevt_node = fevt_nodes[0]

        # Vérifier que les événements sont dans les tokens
        marr_tokens = [
            token for token in fevt_node.tokens if token.type.value == "marr"
        ]
        div_tokens = [token for token in fevt_node.tokens if token.type.value == "div"]

        assert len(marr_tokens) == 1
        assert len(div_tokens) == 1
