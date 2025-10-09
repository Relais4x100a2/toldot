"""
Tests pour le parsing des témoins dans les blocs fevt
"""

import pytest
from geneweb_py.core.parser.gw_parser import GeneWebParser


class TestTemoins:
    """Tests pour le parsing des témoins"""

    def test_parser_fevt_avec_temoins_masculins(self):
        """Test le parsing d'un bloc fevt avec témoins masculins"""
        content = """fevt
#marr 7/8/1970 #p Conches-en-Ouche,_27165,_Eure,_Normandie,_France
wit m: FOURNIER Louis_André
wit m: BLANC Jacques
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
        assert "witnesses" in fevt_node.metadata

        witnesses = fevt_node.metadata["witnesses"]
        assert len(witnesses) == 2

        # Vérifier le premier témoin
        assert witnesses[0]["type"] == "male"
        assert witnesses[0]["name"] == "FOURNIER Louis_André"

        # Vérifier le deuxième témoin
        assert witnesses[1]["type"] == "male"
        assert witnesses[1]["name"] == "BLANC Jacques"

    def test_parser_fevt_avec_temoins_feminins(self):
        """Test le parsing d'un bloc fevt avec témoins féminins"""
        content = """fevt
#marr 2/7/1948 #p Arras,_62041,_Pas-de-Calais,_Nord-Pas-de-Calais,_France
wit f: DUBOIS Paule_Marie
wit f: ROUX Sophie_Marie
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
        assert "witnesses" in fevt_node.metadata

        witnesses = fevt_node.metadata["witnesses"]
        assert len(witnesses) == 2

        # Vérifier le premier témoin
        assert witnesses[0]["type"] == "female"
        assert witnesses[0]["name"] == "DUBOIS Paule_Marie"

        # Vérifier le deuxième témoin
        assert witnesses[1]["type"] == "female"
        assert witnesses[1]["name"] == "ROUX Sophie_Marie"

    def test_parser_fevt_avec_temoins_mixtes(self):
        """Test le parsing d'un bloc fevt avec témoins masculins et féminins"""
        content = """fevt
#marr 9/11/2012 #p Saint-Maur-des-Fossés,_94068,_Val_de_Marne,_Ile-de-France,_France
wit m: MARTIN Etienne_Paul
wit f: MARTIN Laure_Marie
wit f: GARCIA Sarah_Anne
wit f: GARCIA Daniela
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
        assert "witnesses" in fevt_node.metadata

        witnesses = fevt_node.metadata["witnesses"]
        assert len(witnesses) == 4

        # Vérifier les témoins
        expected_witnesses = [
            ("male", "MARTIN Etienne_Paul"),
            ("female", "MARTIN Laure_Marie"),
            ("female", "GARCIA Sarah_Anne"),
            ("female", "GARCIA Daniela"),
        ]

        for i, (expected_type, expected_name) in enumerate(expected_witnesses):
            assert witnesses[i]["type"] == expected_type
            assert witnesses[i]["name"] == expected_name

    def test_parser_fevt_sans_temoins(self):
        """Test le parsing d'un bloc fevt sans témoins"""
        content = """fevt
#marr 11/5/1932 #p Lanchères,_80464,_Somme,_Picardie,_France
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
        assert "witnesses" in fevt_node.metadata

        witnesses = fevt_node.metadata["witnesses"]
        assert len(witnesses) == 0
