"""
Tests pour le parsing des sources et commentaires
"""

import pytest
from geneweb_py.core.parser.gw_parser import GeneWebParser


class TestSources:
    """Tests pour le parsing des sources et commentaires"""

    def test_parser_fevt_avec_sources(self):
        """Test le parsing d'un bloc fevt avec sources"""
        content = """fevt
#marr 7/8/1970 #p Conches-en-Ouche,_27165,_Eure,_Normandie,_France
src "Acte de mariage, mairie de Conches-en-Ouche"
src "Registre paroissial, église Saint-Martin"
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

        # Vérifier que les sources sont dans les tokens
        source_tokens = [
            token for token in fevt_node.tokens if token.type.value == "src"
        ]
        assert len(source_tokens) == 2

        # Vérifier les valeurs des sources
        source_values = [token.value for token in source_tokens]
        assert "src" in source_values[0]
        assert "src" in source_values[1]

    def test_parser_fevt_avec_commentaires(self):
        """Test le parsing d'un bloc fevt avec commentaires"""
        content = """fevt
#marr 7/8/1970 #p Conches-en-Ouche,_27165,_Eure,_Normandie,_France
comm "Mariage célébré en présence de nombreux témoins"
comm "Cérémonie religieuse suivie d'un repas de famille"
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

        # Vérifier que les commentaires sont dans les tokens
        comm_tokens = [
            token for token in fevt_node.tokens if token.type.value == "comm"
        ]
        assert len(comm_tokens) == 2

        # Vérifier les valeurs des commentaires
        comm_values = [token.value for token in comm_tokens]
        assert "comm" in comm_values[0]
        assert "comm" in comm_values[1]

    def test_parser_pevt_avec_sources(self):
        """Test le parsing d'un bloc pevt avec sources"""
        content = """pevt MARTIN Paul_Henri
#birt 8/3/1943 #p Lanchères,_80464,_Somme,_Picardie,_France
src "Acte de naissance, mairie de Lanchères"
src "Registre d'état civil, 1943"
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud pevt a été créé
        pevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "person_events"
        ]
        assert len(pevt_nodes) == 1

        pevt_node = pevt_nodes[0]

        # Vérifier que les sources sont dans les tokens
        source_tokens = [
            token for token in pevt_node.tokens if token.type.value == "src"
        ]
        assert len(source_tokens) == 2

        # Vérifier les valeurs des sources
        source_values = [token.value for token in source_tokens]
        assert "src" in source_values[0]
        assert "src" in source_values[1]

    def test_parser_pevt_avec_commentaires(self):
        """Test le parsing d'un bloc pevt avec commentaires"""
        content = """pevt MARTIN Paul_Henri
#birt 8/3/1943 #p Lanchères,_80464,_Somme,_Picardie,_France
comm "Naissance dans une famille d'agriculteurs"
comm "Baptême célébré le 15 mars 1943"
end pevt"""

        parser = GeneWebParser(validate=False)
        genealogy = parser.parse_string(content)

        # Vérifier qu'un nœud pevt a été créé
        pevt_nodes = [
            node
            for node in parser.get_syntax_nodes()
            if node.type.value == "person_events"
        ]
        assert len(pevt_nodes) == 1

        pevt_node = pevt_nodes[0]

        # Vérifier que les commentaires sont dans les tokens
        comm_tokens = [
            token for token in pevt_node.tokens if token.type.value == "comm"
        ]
        assert len(comm_tokens) == 2

        # Vérifier les valeurs des commentaires
        comm_values = [token.value for token in comm_tokens]
        assert "comm" in comm_values[0]
        assert "comm" in comm_values[1]
