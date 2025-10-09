"""
Parser principal GeneWeb

Ce module implémente le parser principal qui orchestre le parsing lexical
et syntaxique pour créer une représentation complète des données généalogiques.
"""

import chardet
from pathlib import Path
from typing import Optional, Union, TextIO, List, Tuple

from .lexical import LexicalParser, Token, TokenType
from .syntax import SyntaxParser, SyntaxNode, BlockType
from .streaming import (
    StreamingGeneWebParser, 
    should_use_streaming, 
    estimate_memory_usage
)
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
    
    Optimisations de performance :
    - Mode streaming automatique pour les gros fichiers (>10MB)
    - Cache LRU pour les patterns regex
    - __slots__ pour réduire l'empreinte mémoire
    - Parsing ligne par ligne au lieu de tout charger en mémoire
    """
    
    def __init__(self, validate: bool = True, stream_mode: Optional[bool] = None, 
                 streaming_threshold_mb: float = 10.0, strict: bool = True):
        """Initialise le parser
        
        Args:
            validate: Si True, valide la cohérence des données après parsing
            stream_mode: Si True, force le mode streaming. Si None, détection automatique.
            streaming_threshold_mb: Seuil en MB pour activer le streaming automatiquement
            strict: Si True, lève une exception à la première erreur. Si False, parsing gracieux.
        """
        self.validate = validate
        self.stream_mode = stream_mode
        self.streaming_threshold_mb = streaming_threshold_mb
        self.strict = strict
        self.lexical_parser: Optional[LexicalParser] = None
        self.syntax_parser = SyntaxParser()
        self.tokens: List[Token] = []
        self.syntax_nodes: List[SyntaxNode] = []
        
        # Collecteur d'erreurs pour parsing gracieux
        from ..exceptions import GeneWebErrorCollector
        self.error_collector = GeneWebErrorCollector(strict=strict)
    
    def parse_file(self, file_path: Union[str, Path]) -> Genealogy:
        """Parse un fichier .gw avec optimisation automatique
        
        Détecte automatiquement la taille du fichier et choisit le mode approprié :
        - Mode normal pour les petits fichiers (<10MB)
        - Mode streaming pour les gros fichiers (>10MB)
        
        Args:
            file_path: Chemin vers le fichier .gw
            
        Returns:
            Instance de Genealogy avec toutes les données parsées
            
        Raises:
            GeneWebParseError: En cas d'erreur de parsing
            GeneWebEncodingError: En cas de problème d'encodage
        """
        file_path = Path(file_path)
        # Valider l'extension du fichier
        if file_path.suffix.lower() not in [".gw", ".gwplus"]:
            raise GeneWebParseError(f"Extension de fichier invalide: {file_path.suffix}")
        
        if not file_path.exists():
            raise GeneWebParseError(f"Fichier non trouvé: {file_path}")
        
        # Déterminer si on doit utiliser le mode streaming
        use_streaming = self.stream_mode
        if use_streaming is None:
            use_streaming = should_use_streaming(file_path, self.streaming_threshold_mb)
        
        try:
            if use_streaming:
                # Mode streaming pour gros fichiers
                return self._parse_file_streaming(file_path)
            else:
                # Mode normal pour petits fichiers
                # Lire le fichier avec détection d'encodage
                content, encoding = self._read_file_with_encoding(file_path)
                
                # Parser le contenu
                genealogy = self.parse_string(content, filename=str(file_path), encoding=encoding)
                
                # Ajouter les métadonnées du fichier
                genealogy.metadata.source_file = str(file_path)
                genealogy.metadata.encoding = encoding
                
                # Transférer les erreurs de parsing à la généalogie
                if self.error_collector.has_errors():
                    for error in self.error_collector.get_errors():
                        genealogy.add_validation_error(error)
                
                return genealogy
            
        except Exception as e:
            if isinstance(e, (GeneWebParseError, GeneWebEncodingError)):
                raise
            raise GeneWebParseError(f"Erreur lors du parsing de {file_path}: {e}")
    
    def _parse_file_streaming(self, file_path: Path) -> Genealogy:
        """Parse un fichier en mode streaming (pour gros fichiers)
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Instance de Genealogy
        """
        streaming_parser = StreamingGeneWebParser(validate=self.validate)
        
        # Collecter les tokens en streaming
        self.tokens = list(streaming_parser.parse_file_streaming(file_path))
        
        # Parsing syntaxique (identique)
        self.syntax_nodes = self.syntax_parser.parse(self.tokens)
        
        # Construction des modèles (identique)
        genealogy = self._build_genealogy()
        
        # Validation si demandée
        if self.validate:
            errors = genealogy.validate_consistency()
            if errors:
                error_messages = [str(error) for error in errors]
                raise GeneWebParseError(
                    f"Erreurs de validation détectées: {'; '.join(error_messages)}"
                )
        
        genealogy.metadata.source_file = str(file_path)
        return genealogy
    
    def parse_string(self, content: str, filename: Optional[str] = None, encoding: Optional[str] = None) -> Genealogy:
        """Parse une chaîne de caractères contenant du .gw
        
        Args:
            content: Contenu du fichier .gw
            filename: Nom du fichier (pour les erreurs)
            
        Returns:
            Instance de Genealogy avec toutes les données parsées
        """
        # Chaîne vide → généalogie vide
        if content is None or content.strip() == "":
            from ..genealogy import Genealogy
            genealogy = Genealogy()
            if filename:
                genealogy.metadata.source_file = filename
            if encoding:
                genealogy.metadata.encoding = encoding
            return genealogy

        # Validation de lignes en tête si validation active (détection de lignes non reconnues)
        if self.validate and content:
            allowed_starts = {"fam", "notes", "rel", "pevt", "fevt", "end", "beg", "wit", "src", "comm", "-", "#", "notes-db", "page-ext", "wizard-note", "encoding:", "gwplus", "husb", "wife", "cbp", "csrc", "marr", "div", "sep", "eng", "note"}
            inside_block = False
            current_block = None
            
            for line_num, raw_line in enumerate(content.splitlines(), 1):
                line = raw_line.strip()
                if not line:
                    continue
                
                # Autoriser les lignes enfants '-' et commentaires '#'
                if line.startswith('#') or line.startswith('-'):
                    continue
                
                word = line.split()[0].lower()
                
                # Gestion des blocs spéciaux
                if word in {"notes-db", "page-ext", "wizard-note", "notes"}:
                    inside_block = True
                    current_block = word
                    continue
                elif word == "end" and inside_block and current_block:
                    # Vérifier si c'est la fin du bloc actuel
                    if f"end {current_block}" in line.lower():
                        inside_block = False
                        current_block = None
                    continue
                
                # Si on est à l'intérieur d'un bloc, ne pas valider le contenu
                if inside_block:
                    continue
                
                # Validation seulement pour les lignes en dehors des blocs
                if word not in allowed_starts:
                    raise GeneWebParseError("Contenu .gw invalide: ligne non reconnue", line_number=line_num)

        # Tokenisation lexicale
        self.lexical_parser = LexicalParser(content, filename)
        self.tokens = self.lexical_parser.tokenize()
        
        # Parsing syntaxique
        self.syntax_nodes = self.syntax_parser.parse(self.tokens)
        
        # Contenu invalide: aucun bloc reconnu (sauf si seulement des commentaires)
        # Seulement quand la validation est activée
        if self.validate:
            has_content_blocks = any(node.type in [BlockType.FAMILY, BlockType.PERSON_EVENTS, BlockType.FAMILY_EVENTS, BlockType.NOTES, BlockType.RELATIONS, BlockType.DATABASE_NOTES, BlockType.EXTENDED_PAGE, BlockType.WIZARD_NOTE]
                                    for node in self.syntax_nodes)
            
            # Si pas de blocs de contenu, vérifier s'il y a des commentaires
            if not has_content_blocks:
                has_comments = any(token.type == TokenType.COMMENT for token in self.tokens)
                if not has_comments:
                    raise GeneWebParseError("Contenu .gw invalide: aucun bloc reconnu", line_number=1)
        
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
        
        # Encoder la métadonnée d'encodage si fourni
        if encoding:
            genealogy.metadata.encoding = encoding
        return genealogy
    
    def _get_or_create_person(self, last_name: str, first_name: str, occurrence_num: Optional[int], 
                             persons: dict, genealogy: Genealogy, gender: Gender = Gender.UNKNOWN) -> str:
        """Crée ou récupère une personne avec gestion intelligente des numéros d'occurrence
        
        Args:
            last_name: Nom de famille
            first_name: Prénom
            occurrence_num: Numéro d'occurrence (None si non spécifié)
            persons: Dictionnaire des personnes existantes
            genealogy: Objet Genealogy
            gender: Sexe de la personne
            
        Returns:
            ID de la personne créée ou récupérée
        """
        # Si occurrence_num est spécifié, l'utiliser directement
        if occurrence_num is not None:
            person_id = f"{last_name}_{first_name}_{occurrence_num}"
            if person_id not in persons:
                person = Person(
                    last_name=last_name,
                    first_name=first_name,
                    occurrence_number=occurrence_num,
                    gender=gender
                )
                persons[person_id] = person
                # Vérifier si la personne n'existe pas déjà dans la généalogie
                if person_id not in genealogy.persons:
                    genealogy.add_person(person)
            return person_id
        
        # Sinon, chercher une personne existante avec occurrence 0
        base_id = f"{last_name}_{first_name}_0"
        if base_id in persons:
            return base_id
        
        # Si aucune personne n'existe, créer avec occurrence 0
        person = Person(
            last_name=last_name,
            first_name=first_name,
            occurrence_number=0,
            gender=gender
        )
        # Déduplication stricte: si existe déjà côté persons ou genealogy, réutiliser
        if base_id not in persons:
            persons[base_id] = person
        if base_id not in genealogy.persons:
            try:
                genealogy.add_person(person)
            except Exception:
                pass
        return base_id
    
    def _read_file_with_encoding(self, file_path: Path) -> Tuple[str, str]:
        """Lit un fichier avec détection automatique d'encodage optimisée
        
        Optimisation: Essaye UTF-8 d'abord, utilise chardet seulement si nécessaire
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Tuple (contenu, encodage détecté)
        """
        try:
            # Lire le fichier en binaire pour détecter l'encodage
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # Essayer d'abord UTF-8 (plus commun maintenant, évite chardet)
            try:
                content = raw_data.decode('utf-8')
                return content, 'utf-8'
            except UnicodeDecodeError:
                pass
            
            # Détecter l'encodage avec chardet seulement si UTF-8 échoue
            result = chardet.detect(raw_data[:8192])  # Échantillon pour optimisation
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
    
    def get_memory_estimate(self, file_path: Union[str, Path]) -> dict:
        """Estime l'utilisation mémoire pour parser un fichier
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire avec les estimations de mémoire
        """
        return estimate_memory_usage(file_path)
    
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
            elif node.type == BlockType.RELATIONS:
                self._parse_relations_block(node, persons, genealogy)
            elif node.type == BlockType.PERSON_EVENTS:
                self._parse_person_events_block(node, persons, genealogy)
            elif node.type == BlockType.FAMILY_EVENTS:
                self._parse_family_events_block(node, families, genealogy)
            elif node.type == BlockType.DATABASE_NOTES:
                self._parse_database_notes_block(node, genealogy)
            elif node.type == BlockType.EXTENDED_PAGE:
                self._parse_extended_page_block(node, persons, genealogy)
            elif node.type == BlockType.WIZARD_NOTE:
                self._parse_wizard_note_block(node, persons, genealogy)
        
        # Mettre à jour les références croisées
        genealogy._update_cross_references()
        
        # Ajouter toutes les personnes créées (témoins, relations, etc.)
        for person in persons.values():
            try:
                genealogy.add_person(person)
            except Exception:
                # Ignorer les doublons silencieusement
                pass
        
        return genealogy
    
    def _parse_family_block(self, node: SyntaxNode, persons: dict, families: dict, genealogy: Genealogy) -> None:
        """Parse un bloc famille et construit les objets Person et Family"""
        
        # Extraire les informations du bloc
        tokens = node.tokens
        
        # Parser la ligne fam avec une approche plus robuste
        family_info = self._parse_family_line(tokens)
        
        # Créer les personnes si elles n'existent pas
        husband_id = None
        wife_id = None
        
        if family_info['husband_name'] and family_info['husband_firstname']:
            husband_id = self._get_or_create_person(
                family_info['husband_name'],
                family_info['husband_firstname'],
                family_info['husband_occurrence'],
                persons,
                genealogy,
                Gender.MALE
            )
            # Appliquer les informations personnelles du mari
            husband = persons[husband_id]
            if family_info['husband_birth_date']:
                husband.birth_date = family_info['husband_birth_date']
            if family_info['husband_death_date']:
                husband.death_date = family_info['husband_death_date']
            if family_info['husband_birth_place']:
                husband.birth_place = family_info['husband_birth_place']
            if family_info['husband_death_place']:
                husband.death_place = family_info['husband_death_place']
            if family_info['husband_occupation']:
                husband.occupation = family_info['husband_occupation']
        
        if family_info['wife_name'] and family_info['wife_firstname']:
            wife_id = self._get_or_create_person(
                family_info['wife_name'],
                family_info['wife_firstname'],
                family_info['wife_occurrence'],
                persons,
                genealogy,
                Gender.FEMALE
            )
            # Appliquer les informations personnelles de la femme
            wife = persons[wife_id]
            if family_info['wife_birth_date']:
                wife.birth_date = family_info['wife_birth_date']
            if family_info['wife_death_date']:
                wife.death_date = family_info['wife_death_date']
            if family_info['wife_birth_place']:
                wife.birth_place = family_info['wife_birth_place']
            if family_info['wife_death_place']:
                wife.death_place = family_info['wife_death_place']
            if family_info['wife_occupation']:
                wife.occupation = family_info['wife_occupation']
        
        # Créer la famille seulement si au moins un époux est défini
        if husband_id or wife_id:
            family_id = f"FAM_{len(families) + 1:03d}"
            family = Family(
                family_id=family_id,
                husband_id=husband_id,
                wife_id=wife_id,
                marriage_date=family_info['marriage_date'],
                marriage_place=family_info['marriage_place']
            )
            
            # Parser les enfants
            for child_node in node.children:
                self._parse_child(child_node, family, persons, genealogy)
            
            # Parser les témoins dans les tokens du nœud famille
            i = 0
            while i < len(tokens):
                if tokens[i].type == TokenType.WIT:
                    next_i, witness_id, witness_type = self._parse_witness_person(tokens, i, persons, genealogy)
                    i = next_i
                else:
                    i += 1
            
            families[family_id] = family
            genealogy.add_family(family)
    
    def _parse_family_line(self, tokens: List[Token]) -> dict:
        """Parse une ligne fam et extrait toutes les informations
        
        Format: fam LastName FirstName [infos personnelles] + LastName FirstName [infos personnelles]
        
        Returns:
            Dictionnaire avec toutes les informations extraites
        """
        result = {
            'husband_name': None,
            'husband_firstname': None,
            'husband_occurrence': None,
            'husband_birth_date': None,
            'husband_death_date': None,
            'husband_birth_place': None,
            'husband_death_place': None,
            'husband_occupation': None,
            'wife_name': None,
            'wife_firstname': None,
            'wife_occurrence': None,
            'wife_birth_date': None,
            'wife_death_date': None,
            'wife_birth_place': None,
            'wife_death_place': None,
            'wife_occupation': None,
            'marriage_date': None,
            'marriage_place': None,
        }
        
        i = 0
        current_person = 'husband'  # 'husband' ou 'wife'
        
        while i < len(tokens):
            token = tokens[i]
            
            # Passer le token 'fam'
            if token.type == TokenType.FAM:
                i += 1
                continue
            
            # Séparateur de mariage - passer à la femme
            elif token.type == TokenType.PLUS:
                current_person = 'wife'
                i += 1
                continue
            
            # Nom de famille
            elif token.type == TokenType.IDENTIFIER and not result[f'{current_person}_name']:
                result[f'{current_person}_name'] = token.value
                i += 1
                continue
            
            # Prénom
            elif (token.type == TokenType.IDENTIFIER and 
                  result[f'{current_person}_name'] and 
                  not result[f'{current_person}_firstname']):
                result[f'{current_person}_firstname'] = token.value
                i += 1
                continue

            # Si le mari est déjà défini (nom+prénom) et qu'on rencontre un nouvel IDENTIFIER,
            # l'interpréter comme début des infos de l'épouse (format inline sans '+').
            elif (token.type == TokenType.IDENTIFIER and current_person == 'husband' and 
                  result['husband_name'] and result['husband_firstname'] and not result['wife_name']):
                current_person = 'wife'
                # Ne pas consommer ici; la boucle reprendra et tombera sur le cas 'Nom de famille'
                continue
            
            # Numéro d'occurrence (après le prénom)
            elif (token.type == TokenType.NUMBER and 
                  result[f'{current_person}_firstname'] and 
                  result[f'{current_person}_occurrence'] is None):
                # Extraire le numéro du token (ex: ".1" -> 1)
                occurrence_str = token.value.lstrip('.')
                try:
                    result[f'{current_person}_occurrence'] = int(occurrence_str)
                except ValueError:
                    result[f'{current_person}_occurrence'] = 0
                i += 1
                continue
            
            # Date (peut être naissance ou décès selon le contexte)
            elif token.type == TokenType.DATE:
                # Si c'est la première date, c'est probablement la naissance
                if not result[f'{current_person}_birth_date']:
                    try:
                        result[f'{current_person}_birth_date'] = Date.parse_with_fallback(token.value)
                    except Exception:
                        pass
                # Sinon c'est probablement le décès
                elif not result[f'{current_person}_death_date']:
                    try:
                        result[f'{current_person}_death_date'] = Date.parse_with_fallback(token.value)
                    except Exception:
                        pass
                i += 1
                continue
            
            # Lieu de naissance (#bp)
            elif token.type == TokenType.BP:
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    result[f'{current_person}_birth_place'] = tokens[i].value
                    i += 1
                continue
            
            # Lieu de décès (#dp)
            elif token.type == TokenType.DP:
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    result[f'{current_person}_death_place'] = tokens[i].value
                    i += 1
                continue
            
            # Occupation (#occu)
            elif token.type == TokenType.OCCU:
                i += 1
                occupation_parts = []
                while i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING, TokenType.PAREN_OPEN, TokenType.PAREN_CLOSE, TokenType.UNKNOWN]:
                    # Remplacer les underscores par des espaces pour l'affichage
                    occupation_parts.append(tokens[i].value.replace('_', ' '))
                    i += 1
                if occupation_parts:
                    result[f'{current_person}_occupation'] = ''.join(occupation_parts)
                continue
            
            # Lieu de mariage (#mp)
            elif token.type == TokenType.MP:
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    result['marriage_place'] = tokens[i].value
                    i += 1
                continue
            
            # Date de mariage (après le séparateur +)
            elif (token.type == TokenType.DATE and current_person == 'wife' and 
                  not result['marriage_date']):
                try:
                    result['marriage_date'] = Date.parse_with_fallback(token.value)
                except Exception:
                    pass
                i += 1
                continue
            
            # Autres tokens
            else:
                i += 1
        
        return result
    
    def _parse_child(self, child_node: SyntaxNode, family: Family, persons: dict, genealogy: Genealogy) -> None:
        """Parse un enfant dans un bloc famille"""
        tokens = child_node.tokens
        
        if not tokens or tokens[0].type != TokenType.DASH:
            return
        
        # Extraire les informations de l'enfant
        sex = ChildSex.UNKNOWN
        last_name = None
        first_name = None
        occurrence_num = None
        
        i = 1  # Passer le tire
        
        # Sexe de l'enfant (h ou f comme identifiant ou token spécial)
        if i < len(tokens) and ((tokens[i].type == TokenType.IDENTIFIER and tokens[i].value in ['h', 'f']) or tokens[i].type in [TokenType.H, TokenType.F]):
            if tokens[i].type == TokenType.H or (tokens[i].type == TokenType.IDENTIFIER and tokens[i].value == 'h'):
                sex = ChildSex.MALE
            else:
                sex = ChildSex.FEMALE
            i += 1
        
        # Nom de famille de l'enfant (premier identifiant après le sexe)
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            last_name = tokens[i].value
            i += 1
        
        # Prénom de l'enfant (deuxième identifiant)
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            first_name = tokens[i].value
            i += 1
        
        # Numéro d'occurrence (après le prénom)
        if i < len(tokens) and tokens[i].type == TokenType.NUMBER:
            occurrence_str = tokens[i].value.lstrip('.')
            try:
                occurrence_num = int(occurrence_str)
            except ValueError:
                occurrence_num = 0
            i += 1
        
        if first_name:
            # Utiliser le nom de famille du père si pas spécifié
            if not last_name:
                husband = genealogy.find_person_by_id(family.husband_id)
                if husband:
                    last_name = husband.last_name
            
            # Utiliser la nouvelle méthode de déduplication
            child_id = self._get_or_create_person(
                last_name,
                first_name,
                occurrence_num,
                persons,
                genealogy,
                Gender.MALE if sex == ChildSex.MALE else 
                       Gender.FEMALE if sex == ChildSex.FEMALE else Gender.UNKNOWN
            )
            
            # Parser les informations personnelles supplémentaires (occupation, etc.)
            i = self._parse_inline_personal_info(tokens, i, persons[child_id])
            
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
            # Garder une référence au dernier événement construit pour y rattacher les témoins
            last_event = None
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
                            last_event = baptism_event
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
                
                elif token.type == TokenType.WIT:
                    # Parser les témoins avec informations complètes et les rattacher à l'événement courant
                    next_i, witness_id, witness_type = self._parse_witness_person(tokens, i, persons, genealogy)
                    if witness_id and last_event is not None:
                        try:
                            last_event.add_witness(witness_id, witness_type)
                        except Exception:
                            pass
                    i = next_i
                
                else:
                    i += 1
    
    def _parse_family_events_block(self, node: SyntaxNode, families: dict, genealogy: Genealogy) -> None:
        """Parse un bloc événements familiaux et met à jour la famille correspondante"""
        tokens = node.tokens
        
        # Créer un dictionnaire temporaire pour les personnes
        persons = {}
        
        i = 1  # Passer 'fevt'
        # Créer un événement familial générique courant si besoin (ex: MARR si présent)
        from ..event import Event, EventType
        current_event: Optional[Event] = None
        while i < len(tokens):
            token = tokens[i]
 
            # Témoins
            if token.type == TokenType.WIT:
                next_i, witness_id, witness_type = self._parse_witness_person(tokens, i, persons, genealogy)
                if witness_id and current_event is not None:
                    try:
                        current_event.add_witness(witness_id, witness_type)
                    except Exception:
                        pass
                i = next_i
                continue
             
            # Détecter un type d'événement familial simple (ex: #marr déjà géré en syntaxe autrement)
            if token.type in [TokenType.MARR, TokenType.DIV_EVENT, TokenType.SEP_EVENT, TokenType.ENGA]:
                mapped = {
                    TokenType.MARR: EventType.MARRIAGE,
                    TokenType.DIV_EVENT: EventType.DIVORCE,
                    TokenType.SEP_EVENT: EventType.SEPARATION,
                    TokenType.ENGA: EventType.ENGAGEMENT,
                }[token.type]
                current_event = Event(event_type=mapped)
                i += 1
                continue

            # Autres tokens
            i += 1
        
        # Stocker les témoins créés dans les métadonnées du nœud
        # Toujours initialiser la liste des témoins, même si elle est vide
        witnesses = []
        if persons:
            # Convertir les objets Person en dictionnaires pour les tests
            for person in persons.values():
                witness_dict = {
                    'person_id': person.unique_id,
                    'type': 'male' if person.gender == Gender.MALE else 'female',
                    'name': f"{person.last_name} {person.first_name}",
                    'person': person  # Garder l'objet Person pour référence
                }
                witnesses.append(witness_dict)
        node.metadata['witnesses'] = witnesses
    
    def get_tokens(self) -> List[Token]:
        """Retourne la liste des tokens du dernier parsing"""
        return self.tokens
    
    def get_syntax_nodes(self) -> List[SyntaxNode]:
        """Retourne la liste des nœuds syntaxiques du dernier parsing"""
        return self.syntax_nodes
    
    def _parse_relations_block(self, node: SyntaxNode, persons: dict, genealogy: Genealogy) -> None:
        """Parse un bloc relations et crée les Person référencées"""
        tokens = node.tokens
        
        # Extraire le nom de la personne concernée
        if len(tokens) >= 3 and tokens[1].type == TokenType.IDENTIFIER and tokens[2].type == TokenType.IDENTIFIER:
            person_last_name = tokens[1].value
            person_first_name = tokens[2].value
            
            person_id = f"{person_last_name}_{person_first_name}_0"
            
            # Créer la personne si elle n'existe pas
            if person_id not in persons:
                person = Person(
                    last_name=person_last_name,
                    first_name=person_first_name,
                    gender=Gender.UNKNOWN
                )
                persons[person_id] = person
                genealogy.add_person(person)
            
            # Parser les relations dans les enfants du nœud
            relations = []
            for child_node in node.children:
                if child_node.tokens and child_node.tokens[0].type == TokenType.DASH:
                    relation = self._parse_relation_line(child_node, persons, genealogy)
                    if relation:
                        relations.append(relation)
            
            # Stocker les relations dans les notes de la personne
            if relations:
                relations_text = "; ".join([f"{rel['type']} {rel['parent_type'] or ''}: {rel['person_name']}" for rel in relations])
                persons[person_id].add_note(f"Relations: {relations_text}")
    
    def _parse_relation_line(self, child_node: SyntaxNode, persons: dict, genealogy: Genealogy) -> dict:
        """Parse une ligne de relation et crée les Person référencées"""
        tokens = child_node.tokens
        
        if len(tokens) < 4:  # Au minimum: -, type, :, nom
            return None
        
        # Type de relation (adop, reco, cand, godp, fost)
        relation_type = None
        parent_type = None
        person_tokens = []
        
        i = 1  # Passer le tire
        
        # Type de relation
        if i < len(tokens) and tokens[i].type in [TokenType.ADOP, TokenType.RECO, TokenType.CAND, TokenType.GODP, TokenType.FOST]:
            relation_type = tokens[i].value
            i += 1
        
        # Type de parent (fath, moth) - optionnel
        if i < len(tokens) and tokens[i].type in [TokenType.FATH, TokenType.MOTH]:
            parent_type = tokens[i].value
            i += 1
        
        # Passer les deux points
        if i < len(tokens) and tokens[i].type == TokenType.COLON:
            i += 1
        
        # Collecter les tokens de la personne
        while i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            person_tokens.append(tokens[i].value)
            i += 1
        
        if len(person_tokens) >= 2:
            # Créer la personne référencée
            related_last_name = person_tokens[0]
            related_first_name = person_tokens[1]
            related_person_id = f"{related_last_name}_{related_first_name}_0"
            
            if related_person_id not in persons:
                related_person = Person(
                    last_name=related_last_name,
                    first_name=related_first_name,
                    gender=Gender.UNKNOWN
                )
                persons[related_person_id] = related_person
                # Ne pas appeler genealogy.add_person() ici pour éviter les doublons
            
            return {
                'type': relation_type,
                'parent_type': parent_type,
                'person_id': related_person_id,
                'person_name': f"{related_last_name} {related_first_name}"
            }
        
        return None
    
    def _parse_witness_person(self, tokens: List[Token], start_index: int, persons: dict, genealogy: Genealogy) -> Tuple[int, Optional[str], Optional[str]]:
        """Parse un témoin avec toutes ses informations personnelles
        
        Format: wit [m|f]: LastName FirstName [dates] [#bp place] [#occu occupation] ...
        
        Args:
            tokens: Liste des tokens
            start_index: Index de début du témoin
            persons: Dictionnaire des personnes existantes
            genealogy: Objet Genealogy
            
        Returns:
            Tuple (index_suivant, witness_id, witness_type)
        """
        i = start_index
        
        # Passer le token wit
        if i >= len(tokens) or tokens[i].type != TokenType.WIT:
            return i + 1, None, None
        i += 1
        
        # Type de témoin (m ou f) - optionnel
        witness_gender = Gender.UNKNOWN
        witness_type: Optional[str] = None
        if i < len(tokens) and tokens[i].type in [TokenType.H, TokenType.F]:
            witness_gender = Gender.MALE if tokens[i].type == TokenType.H else Gender.FEMALE
            witness_type = 'm' if tokens[i].type == TokenType.H else 'f'
            i += 1
        
        # Passer les deux points
        if i < len(tokens) and tokens[i].type == TokenType.COLON:
            i += 1
        
        # Extraire nom et prénom
        last_name = None
        first_name = None
        occurrence_num = None
        
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            last_name = tokens[i].value
            i += 1
        
        if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
            first_name = tokens[i].value
            i += 1
        
        # Numéro d'occurrence (après le prénom)
        if i < len(tokens) and tokens[i].type == TokenType.NUMBER:
            occurrence_str = tokens[i].value.lstrip('.')
            try:
                occurrence_num = int(occurrence_str)
            except ValueError:
                occurrence_num = 0
            i += 1
        
        if not last_name or not first_name:
            return i, None, None
        
        # Utiliser la nouvelle méthode de déduplication
        witness_id = self._get_or_create_person(
            last_name,
            first_name,
            occurrence_num,
            persons,
            genealogy,
            witness_gender
        )
        
        # Parser les informations personnelles supplémentaires
        i = self._parse_inline_personal_info(tokens, i, persons[witness_id])
        
        return i, witness_id, witness_type
    
    def _parse_inline_personal_info(self, tokens: List[Token], start_index: int, person: Person) -> int:
        """Parse les informations personnelles inline (dates, lieux, occupation, etc.)
        
        Args:
            tokens: Liste des tokens
            start_index: Index de début
            person: Objet Person à mettre à jour
            
        Returns:
            Index suivant après les informations
        """
        i = start_index
        
        while i < len(tokens):
            token = tokens[i]
            
            # Date de naissance
            if token.type == TokenType.DATE:
                try:
                    birth_date = Date.parse_with_fallback(token.value)
                    person.birth_date = birth_date
                except Exception:
                    pass
                i += 1
            
            # Lieu de naissance (#bp)
            elif token.type == TokenType.BP:
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    person.birth_place = tokens[i].value
                    i += 1
            
            # Lieu de décès (#dp)
            elif token.type == TokenType.DP:
                i += 1
                if i < len(tokens) and tokens[i].type == TokenType.IDENTIFIER:
                    person.death_place = tokens[i].value
                    i += 1
            
            # Occupation (#occu)
            elif token.type == TokenType.OCCU:
                i += 1
                occupation_parts = []
                while i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING, TokenType.PAREN_OPEN, TokenType.PAREN_CLOSE, TokenType.UNKNOWN]:
                    # Remplacer les underscores par des espaces pour l'affichage
                    # Garder les virgules et apostrophes telles quelles
                    value = tokens[i].value.replace('_', ' ')
                    occupation_parts.append(value)
                    i += 1
                if occupation_parts:
                    person.occupation = ''.join(occupation_parts)
            
            # Accès privé (#apriv)
            elif token.type == TokenType.APRIV:
                person.access_private = True
                i += 1
            
            # Accès public (#apubl)
            elif token.type == TokenType.APUBL:
                person.access_public = True
                i += 1
            
            # Notes (#note)
            elif token.type == TokenType.NOTE:
                i += 1
                note_content = []
                while i < len(tokens) and tokens[i].type not in [TokenType.NEWLINE, TokenType.WIT, TokenType.SRC, TokenType.COMM]:
                    note_content.append(tokens[i].value)
                    i += 1
                if note_content:
                    person.add_note(' '.join(note_content))
            
            # Sources (#src)
            elif token.type == TokenType.SRC:
                i += 1
                if i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING]:
                    # Par défaut, stocker en note pour compat; évitons de créer des personnes
                    source_value = tokens[i].value
                    person.add_note(f"Source: {source_value}")
                    i += 1
            
            # Commentaires (#comm)
            elif token.type == TokenType.COMM:
                i += 1
                if i < len(tokens) and tokens[i].type in [TokenType.IDENTIFIER, TokenType.STRING]:
                    person.add_note(f"Commentaire: {tokens[i].value}")
                    i += 1
            
            # Fin de ligne ou autre token non reconnu
            elif token.type in [TokenType.NEWLINE, TokenType.WIT, TokenType.SRC, TokenType.COMM]:
                break
            
            else:
                i += 1
        
        return i
    
    def _find_person_info_start(self, tokens: List[Token], last_name: str, first_name: str) -> int:
        """Trouve l'index où commencent les informations personnelles d'une personne
        
        Args:
            tokens: Liste des tokens
            last_name: Nom de famille de la personne
            first_name: Prénom de la personne
            
        Returns:
            Index de début des informations personnelles, ou -1 si non trouvé
        """
        i = 0
        while i < len(tokens) - 1:
            # Chercher le nom de famille
            if (tokens[i].type == TokenType.IDENTIFIER and tokens[i].value == last_name and
                i + 1 < len(tokens) and tokens[i + 1].type == TokenType.IDENTIFIER and 
                tokens[i + 1].value == first_name):
                
                # Vérifier que c'est bien cette personne (pas un autre avec le même nom)
                # En regardant le contexte (pas après 'fam', pas avant '+')
                if i > 0 and tokens[i - 1].type == TokenType.FAM:
                    # C'est le mari, les infos commencent après le prénom
                    return i + 2
                elif i > 0 and tokens[i - 1].type == TokenType.PLUS:
                    # C'est la femme, les infos commencent après le prénom
                    return i + 2
                elif i > 0 and tokens[i - 1].type == TokenType.IDENTIFIER:
                    # C'est probablement un enfant, les infos commencent après le prénom
                    return i + 2
            i += 1
        
        return -1
    
    def _parse_database_notes_block(self, node: SyntaxNode, genealogy: Genealogy) -> None:
        """Parse un bloc notes de base de données et l'ajoute aux métadonnées"""
        tokens = node.tokens
        
        # Extraire le contenu des notes
        notes_content = []
        in_content = False
        
        for token in tokens:
            if token.type == TokenType.NOTES_DB:
                in_content = True
                continue
            elif token.type == TokenType.END_NOTES_DB:
                break
            elif in_content and token.type not in [TokenType.NEWLINE, TokenType.WHITESPACE]:
                notes_content.append(token.value)
        
        if notes_content:
            # Stocker les notes de base de données dans les métadonnées
            if not hasattr(genealogy.metadata, 'database_notes'):
                genealogy.metadata.database_notes = []
            genealogy.metadata.database_notes.append(' '.join(notes_content))
    
    def _parse_extended_page_block(self, node: SyntaxNode, persons: dict, genealogy: Genealogy) -> None:
        """Parse un bloc page étendue et l'associe à la personne correspondante"""
        tokens = node.tokens
        
        # Extraire le nom de la personne
        if len(tokens) >= 3 and tokens[1].type == TokenType.IDENTIFIER and tokens[2].type == TokenType.IDENTIFIER:
            last_name = tokens[1].value
            first_name = tokens[2].value
            occurrence_num = 0
            
            # Vérifier s'il y a un numéro d'occurrence
            if len(tokens) >= 4 and tokens[3].type == TokenType.NUMBER:
                occurrence_str = tokens[3].value.lstrip('.')
                try:
                    occurrence_num = int(occurrence_str)
                except ValueError:
                    occurrence_num = 0
            
            person_id = self._get_or_create_person(
                last_name,
                first_name,
                occurrence_num,
                persons,
                genealogy
            )
            
            # Extraire le contenu de la page
            page_content = []
            in_content = False
            
            for token in tokens:
                if token.type == TokenType.PAGE_EXT:
                    in_content = True
                    continue
                elif token.type == TokenType.END_PAGE_EXT:
                    break
                elif in_content and token.type not in [TokenType.NEWLINE, TokenType.WHITESPACE]:
                    page_content.append(token.value)
            
            if page_content:
                # Stocker le contenu de la page dans les métadonnées de la personne
                person = persons[person_id]
                if 'extended_page' not in person.metadata:
                    person.metadata['extended_page'] = []
                person.metadata['extended_page'].append(' '.join(page_content))
    
    def _parse_wizard_note_block(self, node: SyntaxNode, persons: dict, genealogy: Genealogy) -> None:
        """Parse un bloc note de wizard et l'ajoute aux notes de la personne"""
        tokens = node.tokens
        
        # Extraire le nom de la personne
        if len(tokens) >= 3 and tokens[1].type == TokenType.IDENTIFIER and tokens[2].type == TokenType.IDENTIFIER:
            last_name = tokens[1].value
            first_name = tokens[2].value
            occurrence_num = 0
            
            # Vérifier s'il y a un numéro d'occurrence
            if len(tokens) >= 4 and tokens[3].type == TokenType.NUMBER:
                occurrence_str = tokens[3].value.lstrip('.')
                try:
                    occurrence_num = int(occurrence_str)
                except ValueError:
                    occurrence_num = 0
            
            person_id = self._get_or_create_person(
                last_name,
                first_name,
                occurrence_num,
                persons,
                genealogy
            )
            
            # Extraire le contenu des notes de wizard
            wizard_content = []
            in_content = False
            
            for token in tokens:
                if token.type == TokenType.WIZARD_NOTE:
                    in_content = True
                    continue
                elif token.type == TokenType.END_WIZARD_NOTE:
                    break
                elif in_content and token.type not in [TokenType.NEWLINE, TokenType.WHITESPACE]:
                    wizard_content.append(token.value)
            
            if wizard_content:
                # Ajouter les notes de wizard avec un tag spécial
                person = persons[person_id]
                wizard_note = f"[Wizard] {' '.join(wizard_content)}"
                person.add_note(wizard_note)
