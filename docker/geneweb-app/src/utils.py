"""
Utilitaires divers
"""
import json
import jsonlines
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st
import os
from .data_models import (
    PEVTRaw, PEVTCleaned, AnnotationExample, 
    PromptVersion, ValidationResult
)


def get_api_config() -> Dict[str, str]:
    """
    Récupère la configuration API depuis les variables d'environnement
    Supporte OpenRouter, OpenAI et Anthropic
    """
    config = {}
    
    # Charger le fichier .env s'il existe
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
    
    # Vérifier OpenRouter (priorité)
    if os.getenv("API_KEY_OPENROUTER"):
        config['provider'] = 'openrouter'
        config['api_key'] = os.getenv("API_KEY_OPENROUTER")
        config['base_url'] = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        config['default_model'] = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        config['app_name'] = os.getenv("OPENROUTER_APP_NAME", "geneweb-ai-processor")
        config['site_url'] = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8501")
    
    # Sinon OpenAI
    elif os.getenv("OPENAI_API_KEY"):
        config['provider'] = 'openai'
        config['api_key'] = os.getenv("OPENAI_API_KEY")
        config['default_model'] = "gpt-4o-mini"
    
    # Sinon Anthropic
    elif os.getenv("ANTHROPIC_API_KEY"):
        config['provider'] = 'anthropic'
        config['api_key'] = os.getenv("ANTHROPIC_API_KEY")
        config['default_model'] = "claude-3-5-sonnet-20241022"
    
    return config


def get_default_data_dir() -> str:
    """Détermine le répertoire de données par défaut selon l'environnement"""
    # Si DATA_DIR est défini, l'utiliser
    if os.getenv("DATA_DIR"):
        return os.getenv("DATA_DIR")
    
    # Sinon, utiliser un chemin local dans le projet
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data" / "training"
    
    # Créer le dossier s'il n'existe pas
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return str(data_dir)


class DataManager:
    """Gestionnaire de sauvegarde/chargement des données"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = get_default_data_dir()
        
        self.data_dir = Path(data_dir)
        # Créer le dossier uniquement s'il n'existe pas et qu'on a les permissions
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Si pas de permissions, utiliser un dossier local
            local_data = Path.home() / ".geneweb_ai" / "training"
            local_data.mkdir(parents=True, exist_ok=True)
            self.data_dir = local_data
            print(f"⚠️  Utilisation du dossier local: {self.data_dir}")
        
        self.annotations_file = self.data_dir / "annotations.jsonl"
        self.prompts_file = self.data_dir / "prompts.json"
        self.validations_file = self.data_dir / "validations.jsonl"
        self.metrics_file = self.data_dir / "metrics.json"
    
    def save_annotation(self, example: AnnotationExample) -> None:
        """Sauvegarde une annotation"""
        with jsonlines.open(self.annotations_file, mode='a') as writer:
            writer.write(self._annotation_to_dict(example))
    
    def load_annotations(self) -> List[AnnotationExample]:
        """Charge toutes les annotations"""
        if not self.annotations_file.exists():
            return []
        
        annotations = []
        with jsonlines.open(self.annotations_file) as reader:
            for obj in reader:
                annotations.append(self._dict_to_annotation(obj))
        
        return annotations
    
    def save_prompt_version(self, prompt: PromptVersion) -> None:
        """Sauvegarde une version de prompt"""
        prompts = self.load_prompt_versions()
        prompts.append(prompt)
        
        with open(self.prompts_file, 'w') as f:
            json.dump(
                [self._prompt_to_dict(p) for p in prompts],
                f,
                indent=2,
                ensure_ascii=False
            )
    
    def load_prompt_versions(self) -> List[PromptVersion]:
        """Charge toutes les versions de prompts"""
        if not self.prompts_file.exists():
            return []
        
        with open(self.prompts_file) as f:
            data = json.load(f)
        
        return [self._dict_to_prompt(d) for d in data]
    
    def save_validation(self, result: ValidationResult) -> None:
        """Sauvegarde un résultat de validation"""
        with jsonlines.open(self.validations_file, mode='a') as writer:
            writer.write(self._validation_to_dict(result))
    
    def load_validations(self) -> List[ValidationResult]:
        """Charge tous les résultats de validation"""
        if not self.validations_file.exists():
            return []
        
        validations = []
        with jsonlines.open(self.validations_file) as reader:
            for obj in reader:
                validations.append(self._dict_to_validation(obj))
        
        return validations
    
    def save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Sauvegarde les métriques"""
        all_metrics = self.load_metrics()
        all_metrics.append({
            **metrics,
            'timestamp': datetime.now().isoformat()
        })
        
        with open(self.metrics_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
    
    def load_metrics(self) -> List[Dict[str, Any]]:
        """Charge les métriques"""
        if not self.metrics_file.exists():
            return []
        
        with open(self.metrics_file) as f:
            return json.load(f)
    
    # Méthodes de sérialisation
    def _annotation_to_dict(self, ann: AnnotationExample) -> Dict:
        return {
            'pevt_raw': {
                'person_name': ann.pevt_raw.person_name,
                'person_surname': ann.pevt_raw.person_surname,
                'event_tag': ann.pevt_raw.event_tag,
                'date': ann.pevt_raw.date,
                'place': ann.pevt_raw.place,
                'raw_text': ann.pevt_raw.raw_text,
                'witnesses': ann.pevt_raw.witnesses,
                'notes': ann.pevt_raw.notes,
                'sources': ann.pevt_raw.sources,
                'line_number': ann.pevt_raw.line_number,
            },
            'pevt_cleaned': {
                'event_type': ann.pevt_cleaned.event_type.value,
                'date_iso': ann.pevt_cleaned.date_iso,
                'date_uncertainty': ann.pevt_cleaned.date_uncertainty,
                'place_structured': ann.pevt_cleaned.place_structured,
                'organization': ann.pevt_cleaned.organization,
                'description': ann.pevt_cleaned.description,
                'confidence_score': ann.pevt_cleaned.confidence_score,
                'needs_review': ann.pevt_cleaned.needs_review,
                'cleaned_by': ann.pevt_cleaned.cleaned_by,
                'cleaned_at': ann.pevt_cleaned.cleaned_at,
            },
            'annotator': ann.annotator,
            'annotation_time': ann.annotation_time,
            'created_at': ann.created_at,
        }
    
    def _dict_to_annotation(self, d: Dict) -> AnnotationExample:
        from .data_models import EventType
        
        pevt_raw = PEVTRaw(**d['pevt_raw'])
        
        pevt_cleaned = PEVTCleaned(
            original=pevt_raw,
            event_type=EventType(d['pevt_cleaned']['event_type']),
            date_iso=d['pevt_cleaned']['date_iso'],
            date_uncertainty=d['pevt_cleaned'].get('date_uncertainty'),
            place_structured=d['pevt_cleaned']['place_structured'],
            organization=d['pevt_cleaned']['organization'],
            description=d['pevt_cleaned']['description'],
            confidence_score=d['pevt_cleaned']['confidence_score'],
            needs_review=d['pevt_cleaned']['needs_review'],
            cleaned_by=d['pevt_cleaned']['cleaned_by'],
            cleaned_at=d['pevt_cleaned']['cleaned_at'],
        )
        
        return AnnotationExample(
            pevt_raw=pevt_raw,
            pevt_cleaned=pevt_cleaned,
            annotator=d['annotator'],
            annotation_time=d['annotation_time'],
            created_at=d['created_at'],
        )
    
    def _prompt_to_dict(self, prompt: PromptVersion) -> Dict:
        return {
            'version': prompt.version,
            'prompt_text': prompt.prompt_text,
            'examples_count': prompt.examples_count,
            'accuracy': prompt.accuracy,
            'precision': prompt.precision,
            'recall': prompt.recall,
            'f1_score': prompt.f1_score,
            'created_at': prompt.created_at,
            'notes': prompt.notes,
        }
    
    def _dict_to_prompt(self, d: Dict) -> PromptVersion:
        return PromptVersion(**d)
    
    def _validation_to_dict(self, val: ValidationResult) -> Dict:
        # Simplification pour la validation
        return {
            'pevt_cleaned': self._annotation_to_dict(
                AnnotationExample(
                    pevt_raw=val.pevt_cleaned.original,
                    pevt_cleaned=val.pevt_cleaned,
                    annotator="system",
                    annotation_time=0.0
                )
            )['pevt_cleaned'],
            'is_correct': val.is_correct,
            'errors': val.errors,
            'corrections': val.corrections,
            'validator': val.validator,
            'validated_at': val.validated_at,
        }
    
    def _dict_to_validation(self, d: Dict) -> ValidationResult:
        # Reconstruction simplifiée
        from .data_models import EventType
        
        pevt_raw = PEVTRaw(
            person_name="", person_surname="", event_tag="", raw_text=""
        )
        
        pevt_cleaned = PEVTCleaned(
            original=pevt_raw,
            event_type=EventType(d['pevt_cleaned']['event_type']),
            **{k: v for k, v in d['pevt_cleaned'].items() if k != 'event_type' and k != 'original'}
        )
        
        return ValidationResult(
            pevt_cleaned=pevt_cleaned,
            is_correct=d['is_correct'],
            errors=d['errors'],
            corrections=d['corrections'],
            validator=d['validator'],
            validated_at=d['validated_at'],
        )


def init_session_state():
    """Initialise le session state de Streamlit"""
    
    # Configuration API
    if 'api_config' not in st.session_state:
        st.session_state.api_config = get_api_config()
    
    # Données du fichier
    if 'uploaded_file_path' not in st.session_state:
        st.session_state.uploaded_file_path = None
    if 'all_pevts' not in st.session_state:
        st.session_state.all_pevts = []
    if 'pevt_stats' not in st.session_state:
        st.session_state.pevt_stats = {}
    
    # Annotation
    if 'sample_pevts' not in st.session_state:
        st.session_state.sample_pevts = []
    if 'current_annotation_index' not in st.session_state:
        st.session_state.current_annotation_index = 0
    if 'annotations' not in st.session_state:
        st.session_state.annotations = []
    if 'annotation_start_time' not in st.session_state:
        st.session_state.annotation_start_time = None
    
    # Prompt
    if 'current_prompt_version' not in st.session_state:
        st.session_state.current_prompt_version = 1
    if 'prompt_history' not in st.session_state:
        st.session_state.prompt_history = []
    if 'current_prompt_text' not in st.session_state:
        st.session_state.current_prompt_text = get_default_prompt()
    
    # DSPY
    if 'dspy_optimizer' not in st.session_state:
        st.session_state.dspy_optimizer = None
    if 'dspy_results' not in st.session_state:
        st.session_state.dspy_results = {}
    
    # Validation
    if 'validation_batch' not in st.session_state:
        st.session_state.validation_batch = []
    if 'current_validation_index' not in st.session_state:
        st.session_state.current_validation_index = 0
    if 'validations' not in st.session_state:
        st.session_state.validations = []
    
    # Transformation de masse
    if 'mass_transformation_results' not in st.session_state:
        st.session_state.mass_transformation_results = []
    
    # Data manager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()


def get_default_prompt() -> str:
    """Retourne le prompt par défaut"""
    return """Tu es un expert en généalogie et en normalisation de données historiques.

Ta tâche est de transformer des événements personnalisés (PEVT) au format GeneWeb en données structurées et normalisées.

Pour chaque événement, tu dois :
1. Identifier le type d'événement (éducation, occupation, résidence, etc.)
2. Extraire et normaliser la date au format ISO (YYYY-MM-DD)
3. Structurer le lieu en composants (ville, code INSEE, département, région, pays)
4. Identifier l'organisation/institution concernée
5. Créer une description claire et concise
6. Évaluer ta confiance dans la transformation (0 à 1)

Sois attentif aux :
- Abréviations et acronymes (ex: ENSIAA, INSCIR, etc.)
- Dates approximatives (marquées avec ~)
- Lieux avec codes INSEE
- Noms d'institutions entre crochets [...]

Fournis toujours des réponses en français."""


def format_place_display(place_dict: Dict[str, str]) -> str:
    """Formate un dictionnaire de lieu pour l'affichage"""
    if not place_dict:
        return "N/A"
    
    parts = []
    for key in ['ville', 'code_insee', 'departement', 'region', 'pays']:
        if key in place_dict and place_dict[key]:
            parts.append(place_dict[key])
    
    return ', '.join(parts) if parts else str(place_dict)


def calculate_metrics(validations: List[ValidationResult]) -> Dict[str, float]:
    """Calcule les métriques de performance"""
    if not validations:
        return {
            'accuracy': 0.0,
            'total': 0,
            'correct': 0,
            'incorrect': 0,
        }
    
    correct = sum(1 for v in validations if v.is_correct)
    total = len(validations)
    
    return {
        'accuracy': correct / total if total > 0 else 0.0,
        'total': total,
        'correct': correct,
        'incorrect': total - correct,
    }
