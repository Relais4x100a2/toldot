"""
Parser principal GeneWeb

Ce module implémente le parser principal qui orchestre le parsing lexical
et syntaxique pour créer une représentation complète des données généalogiques.
"""

import chardet
from pathlib import Path
from typing import Optional, Union, TextIO, List

from .lexical import LexicalParser, Token, TokenType
from .syntax import SyntaxParser, SyntaxNode, BlockType
from ..exceptions import GeneWebParseError, GeneWebEncodingError
from ..models import Genealogy, Person, Family, Date
from ..person import Gender
from ..family import ChildSex, MarriageStatus


class GeneWebParser:
    """Parser principal pour les fichiers .gw
    
    Ce parser orchestre le processus complet de parsing :
    1. Lecture et détection d'encodage
    2. Tokenisation lexicale
    3. Parsing syntaxique
    4. Construction des modèles de données
    """
    
    def __init__(self, validate: bool = True):
        """Initialise le parser
        
        Args:
            validate: Si True, valide la cohérence des données après parsing
        """
        self.validate = validate
        self.lexical_parser: Optional[LexicalParser] = None
        self.syntax_parser = SyntaxParser()
        self.tokens: List[Token] = []
        self.syntax_nodes: List[SyntaxNode] = []
    
    def parse_file(self, file_path: Union[str, Path]) -> Genealogy:
        """Parse un fichier .gw
        
        Args:
            file_path: Chemin vers le fichier .gw
            
        Returns:
            Instance de Genealogy avec toutes les données parsées
            
        Raises:
            GeneWebParseError: En cas d'erreur de parsing
            GeneWebEncodingError: En cas de problème d'encodage
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise GeneWebParseError(f"Fichier non trouvé: {file_path}")
        
        try:
            # Lire le fichier avec détection d'encodage
            content, encoding = self._read_file_with_encoding(file_path)
            
            # Parser le contenu
            genealogy = self.parse_string(content, filename=str(file_path))
            
            # Ajouter les métadonnées du fichier
            genealogy.metadata.source_file = str(file_path)
            genealogy.metadata.encoding = encoding
            
            return genealogy
            
        except Exception as e:
            if isinstance(e, (GeneWebParseError, GeneWebEncodingError)):
                raise
            raise GeneWebParseError(f"Erreur lors du parsing de {file_path}: {e}")
    
    def parse_string(self, content: str, filename: Optional[str] = None) -> Genealogy:
        """Parse une chaîne de caractères contenant du .gw
        
        Args:
            content: Contenu du fichier .gw
            filename: Nom du fichier (pour les erreurs)
            
        Returns:
            Instance de Genealogy avec toutes les données parsées
        """
        # Tokenisation lexicale
        self.lexical_parser = LexicalParser(content, filename)
        self.tokens = self.lexical_parser.tokenize()
        
        # Parsing syntaxique
        self.syntax_nodes = self.syntax_parser.parse(self.tokens)
        
        # Construction des modèles de données
        genealogy = self._build_genealogy()
        
        # Validation si demandée
        if self.validate:
            errors = genealogy.validate_consistency()
            if errors:
                error_messages = [str(error) for error in errors]
                raise GeneWebParseError(
                    f"Erreurs de validation détectées: {'; '.join(error_messages)}"
                )
        
        return genealogy
    
    def _read_file_with_encoding(self, file_path: Path) -> tuple[str, str]:
        """Lit un fichier avec détection automatique d'encodage
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Tuple (contenu, encodage détecté)
        """
        try:
            # Lire le fichier en binaire pour détecter l'encodage
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # Essayer d'abord UTF-8 (plus commun maintenant)
            try:
                content = raw_data.decode('utf-8')
                return content, 'utf-8'
            except UnicodeDecodeError:
                pass
            
            # Détecter l'encodage avec chardet
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']
            
            if confidence >= 0.7:
                # Si la confiance est élevée, utiliser l'encodage détecté
                try:
                    content = raw_data.decode(detected_encoding)
                    return content, detected_encoding
                except UnicodeDecodeError:
                    pass
            
            # Essayer ISO-8859-1 en dernier recours
            try:
                content = raw_data.decode('iso-8859-1')
                return content, 'iso-8859-1'
            except UnicodeDecodeError:
                pass
            
            # Si rien ne fonctionne, utiliser l'encodage détecté avec remplacement d'erreurs
            content = raw_data.decode(detected_encoding or 'utf-8', errors='replace')
            return content, detected_encoding or 'utf-8'
                
        except Exception as e:
            if isinstance(e, GeneWebEncodingError):
                raise
            raise GeneWebEncodingError(f"Erreur lors de la lecture du fichier: {e}")
    
    def _build_genealogy(self) -> Genealogy:
        """Construit l'objet Genealogy à partir des nœuds syntaxiques
        
        Returns:
            Instance de Genealogy complète
        """
        genealogy = Genealogy()
        
        # Dictionnaires pour stocker les entités pendant la construction
        persons = {}  # ID -> Person
        families = {}  # ID -> Family
        
        # Parser chaque bloc
        for node in self.syntax_nodes:
            if node.type == BlockType.FAMILY:
                self._parse_family_block(node, persons, families, genealogy)
            elif node.type == BlockType.NOTES:
                self._parse_notes_block(node, persons, genealogy)
            elif node.type == BlockType.PERSON_EVENTS:
                self._parse_person_events_block(node, persons, genealogy)
            elif node.type == BlockType.FAMILY_EVENTS:
                self._parse_family_events_block(node, families, genealogy)
            # TODO: Ajouter les autres types de blocs
        
        # Mettre à jour les références croisées
        genealogy._update_cross_references()
        
        return genealogy
    
    def _parse_family_block(self, node: SyntaxNode, persons: dict, families: dict, genealogy: Genealogy) -> None:
        """Parse un bloc famille et construit les objets Person et Family"""
        
        # Extraire les informations du bloc
        tokens = node.tokens
        
        # Identifier les tokens pertinents
        husband_name = None
        wife_name = None
        husband_firstname = None
        wife_firstname = None
        marriage_date = None
        marriage_place = None
        
        # Parser les tokens pour extraire les informations
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Nom du mari (après 'fam')
            if token.type == TokenType.FAM and i + 1 < len(tokens):
                i += 1
                if tokens[i].type == TokenType.IDENTIFIER:
                    husband_name = tokens[i].value
                    i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    husband_firstname = tokens[i].value
                    i += 1
            
            # Séparateur de mariage
            elif token.type == TokenType.PLUS:
                i += 1
                # Date de mariage (optionnelle)
                if i < len(tokens) and tokens[i].type == TokenType.DATE:
                    try:
                        marriage_date = Date.parse_with_fallback(tokens[i].value)
                    except Exception:
                        marriage_date = None
                    i += 1
            
            # Lieu de mariage
            elif token.type == TokenType.MP and i + 1 < len(tokens):
                i += 1
                if tokens[i].type == TokenType.IDENTIFIER:
                    marriage_place = tokens[i].value
                i += 1
            
            # Nom de la femme
            elif (husband_name and husband_firstname and 
                  token.type == TokenType.IDENTIFIER and 
                  token.value != husband_name and token.value != husband_firstname):
                wife_name = token.value
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    wife_firstname = tokens[i].value
                    i += 1
            
            else:
                i += 1
        
        # Créer les personnes si elles n'existent pas et si les noms sont définis
        if husband_name and husband_firstname:
            husband_id = f"{husband_name}_{husband_firstname}_0"
            if husband_id not in persons:
                husband = Person(
                    last_name=husband_name,
                    first_name=husband_firstname,
                    gender=Gender.MALE
                )
                persons[husband_id] = husband
                genealogy.add_person(husband)
        
        if wife_name and wife_firstname:
            wife_id = f"{wife_name}_{wife_firstname}_0"
            if wife_id not in persons:
                wife = Person(
                    last_name=wife_name,
                    first_name=wife_firstname,
                    gender=Gender.FEMALE
                )
                persons[wife_id] = wife
                genealogy.add_person(wife)
        
        # Créer la famille seulement si au moins un époux est défini
        if (husband_name and husband_firstname) or (wife_name and wife_firstname):
            family_id = f"FAM_{len(families) + 1:03d}"
            family = Family(
                family_id=family_id,
                husband_id=husband_id if (husband_name and husband_firstname) else None,
                wife_id=wife_id if (wife_name and wife_firstname) else None,
                marriage_date=marriage_date,
                marriage_place=marriage_place
            )
        
            # Parser les enfants
            for child_node in node.children:
                self._parse_child(child_node, family, persons, genealogy)
            
            families[family_id] = family
            genealogy.add_family(family)
    
    def _parse_child(self, child_node: SyntaxNode, family: Family, persons: dict, genealogy: Genealogy) -> None:
        """Parse un enfant dans un bloc famille"""
        tokens = child_node.tokens
        
        if not tokens or tokens[0].type.value != '-':
            return
        
        # Extraire les informations de l'enfant
        sex = ChildSex.UNKNOWN
        last_name = None
        first_name = None
        
        i = 1  # Passer le tire
        
        # Sexe de l'enfant (h ou f comme identifiant ou token spécial)
        if i < len(tokens) and ((tokens[i].type == TokenType.IDENTIFIER and tokens[i].value in ['h', 'f']) or tokens[i].type in [TokenType.H, TokenType.F]):
            if tokens[i].type == TokenType.H or (tokens[i].type == TokenType.IDENTIFIER and tokens[i].value == 'h'):
                sex = ChildSex.MALE
            else:
                sex = ChildSex.FEMALE
            i += 1
        
        # Nom de famille (si différent du père)
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            last_name = tokens[i].value
            i += 1
        
        # Prénom de l'enfant
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            first_name = tokens[i].value
            i += 1
        
        if first_name:
            # Utiliser le nom de famille du père si pas spécifié
            if not last_name:
                husband = genealogy.find_person_by_id(family.husband_id)
                if husband:
                    last_name = husband.last_name
            
            child_id = f"{last_name}_{first_name}_0"
            
            # Créer l'enfant s'il n'existe pas
            if child_id not in persons:
                child = Person(
                    last_name=last_name,
                    first_name=first_name,
                    gender=Gender.MALE if sex == ChildSex.MALE else 
                           Gender.FEMALE if sex == ChildSex.FEMALE else Gender.UNKNOWN
                )
                persons[child_id] = child
                genealogy.add_person(child)
            
            # Ajouter l'enfant à la famille
            family.add_child(child_id, sex)
    
    def _parse_notes_block(self, node: SyntaxNode, persons: dict, genealogy: Genealogy) -> None:
        """Parse un bloc notes et ajoute les notes à la personne correspondante"""
        tokens = node.tokens
        
        # Extraire le nom de la personne
        if len(tokens) >= 3 and tokens[1].type == TokenType.IDENTIFIER and tokens[2].type == TokenType.IDENTIFIER:
            last_name = tokens[1].value
            first_name = tokens[2].value
            
            person_id = f"{last_name}_{first_name}_0"
            
            # Créer la personne si elle n'existe pas
            if person_id not in persons:
                person = Person(
                    last_name=last_name,
                    first_name=first_name,
                    gender=Gender.UNKNOWN
                )
                persons[person_id] = person
                genealogy.add_person(person)
            
            # Extraire le contenu des notes
            notes_content = []
            in_content = False
            
            for token in tokens:
                if token.type == TokenType.BEG:
                    in_content = True
                    continue
                elif token.type == TokenType.END_NOTES:
                    break
                elif in_content and token.type not in [TokenType.NEWLINE, TokenType.WHITESPACE]:
                    notes_content.append(token.value)
            
            if notes_content:
                persons[person_id].add_note(' '.join(notes_content))
    
    def _parse_person_events_block(self, node: SyntaxNode, persons: dict, genealogy: Genealogy) -> None:
        """Parse un bloc événements personnels et met à jour la personne correspondante"""
        tokens = node.tokens
        
        # Extraire le nom de la personne
        if len(tokens) >= 3 and tokens[1].type == TokenType.IDENTIFIER and tokens[2].type == TokenType.IDENTIFIER:
            last_name = tokens[1].value
            first_name = tokens[2].value
            
            person_id = f"{last_name}_{first_name}_0"
            
            # Créer la personne si elle n'existe pas
            if person_id not in persons:
                person = Person(
                    last_name=last_name,
                    first_name=first_name,
                    gender=Gender.UNKNOWN  # Sera déterminé plus tard
                )
                persons[person_id] = person
                genealogy.add_person(person)
            
            person = persons[person_id]
            
            # Parser les événements
            i = 3  # Passer pevt, nom, prénom
            while i < len(tokens):
                token = tokens[i]
                
                # Événements avec dates
                if token.type == TokenType.BIRT:
                    i += 1
                    # Date de naissance (optionnelle)
                    if i < len(tokens) and tokens[i].type == TokenType.DATE:
                        try:
                            birth_date = Date.parse_with_fallback(tokens[i].value)
                            person.birth_date = birth_date
                        except Exception:
                            # En cas d'erreur, ignorer silencieusement
                            pass
                        i += 1
                    else:
                        # Pas de date -> date inconnue
                        person.birth_date = Date(is_unknown=True)
                    # Lieu de naissance (optionnel)
                    if i < len(tokens) and tokens[i].type == TokenType.P:
                        i += 1
                        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                            person.birth_place = tokens[i].value
                            i += 1
                
                elif token.type == TokenType.DEAT:
                    i += 1
                    # Date de décès (optionnelle)
                    if i < len(tokens) and tokens[i].type == TokenType.DATE:
                        try:
                            death_date = Date.parse_with_fallback(tokens[i].value)
                            person.death_date = death_date
                        except Exception:
                            # En cas d'erreur, ignorer silencieusement
                            pass
                        i += 1
                    else:
                        # Pas de date -> date inconnue
                        person.death_date = Date(is_unknown=True)
                    # Lieu de décès (optionnel)
                    if i < len(tokens) and tokens[i].type == TokenType.P:
                        i += 1
                        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                            person.death_place = tokens[i].value
                            i += 1
                
                elif token.type == TokenType.BAPT:
                    i += 1
                    # Date de baptême (optionnelle)
                    if i < len(tokens) and tokens[i].type == TokenType.DATE:
                        try:
                            baptism_date = Date.parse_with_fallback(tokens[i].value)
                            # Ajouter l'événement de baptême
                            from ..event import Event, EventType
                            baptism_event = Event(
                                event_type=EventType.BAPTISM,
                                date=baptism_date
                            )
                            person.add_event(baptism_event)
                        except Exception:
                            # En cas d'erreur, ignorer silencieusement
                            pass
                        i += 1
                    # Lieu de baptême (optionnel)
                    if i < len(tokens) and tokens[i].type == TokenType.P:
                        i += 1
                        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                            baptism_place = tokens[i].value
                            # Mettre à jour l'événement de baptême si il existe
                            for event in person.events:
                                if event.event_type == EventType.BAPTISM:
                                    event.place = baptism_place
                                    break
                            i += 1
                
                elif token.type == TokenType.NOTE:
                    i += 1
                    # Contenu de la note
                    note_content = []
                    while i < len(tokens) and tokens[i].type not in [TokenType.NEWLINE, TokenType.END_PEVT]:
                        note_content.append(tokens[i].value)
                        i += 1
                    if note_content:
                        person.add_note(' '.join(note_content))
                
                else:
                    i += 1
    
    def _parse_family_events_block(self, node: SyntaxNode, families: dict, genealogy: Genealogy) -> None:
        """Parse un bloc événements familiaux et met à jour la famille correspondante"""
        tokens = node.tokens
        
        # Pour l'instant, on ne fait que collecter les témoins
        # Dans une implémentation complète, on associerait les témoins à la famille
        witnesses = []
        
        i = 1  # Passer 'fevt'
        while i < len(tokens):
            token = tokens[i]
            
            # Témoins
            if token.type == TokenType.WIT:
                i += 1
                witness_type = None
                witness_name = []
                
                # Type de témoin (m ou f)
                if i < len(tokens) and tokens[i].type in [TokenType.H, TokenType.F]:
                    witness_type = "male" if tokens[i].type == TokenType.H else "female"
                    i += 1
                
                # Deux points
                if i < len(tokens) and tokens[i].type == TokenType.COLON:
                    i += 1
                
                # Nom du témoin
                while i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    witness_name.append(tokens[i].value)
                    i += 1
                
                if witness_name:
                    witnesses.append({
                        'type': witness_type,
                        'name': ' '.join(witness_name)
                    })
                continue
            
            # Autres tokens
            i += 1
        
        # Stocker les témoins dans les métadonnées du nœud
        node.metadata['witnesses'] = witnesses
    
    def get_tokens(self) -> List[Token]:
        """Retourne la liste des tokens du dernier parsing"""
        return self.tokens
    
    def get_syntax_nodes(self) -> List[SyntaxNode]:
        """Retourne la liste des nœuds syntaxiques du dernier parsing"""
        return self.syntax_nodes
