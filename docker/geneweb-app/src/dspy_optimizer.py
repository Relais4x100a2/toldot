"""
Optimiseur DSPY pour l'amélioration des prompts
Supporte OpenRouter, OpenAI et Anthropic
"""
import dspy
from typing import List, Dict, Any, Optional
import json
import os
from .data_models import PEVTRaw, PEVTCleaned, AnnotationExample, PromptVersion


class PEVTCleanerSignature(dspy.Signature):
    """Signature DSPY pour nettoyer un événement PEVT personnalisé"""
    
    pevt_raw = dspy.InputField(
        desc="Événement PEVT brut au format GeneWeb avec toutes ses informations"
    )
    context = dspy.InputField(
        desc="Contexte et exemples de transformations réussies"
    )
    
    event_type = dspy.OutputField(
        desc="Type d'événement normalisé (éducation, occupation, résidence, etc.)"
    )
    date_iso = dspy.OutputField(
        desc="Date au format ISO YYYY-MM-DD ou vide si non applicable"
    )
    place_structured = dspy.OutputField(
        desc="Lieu structuré au format JSON avec ville, département, région, pays"
    )
    organization = dspy.OutputField(
        desc="Nom de l'organisation/institution concernée (école, entreprise, etc.)"
    )
    description = dspy.OutputField(
        desc="Description claire et concise de l'événement"
    )
    confidence = dspy.OutputField(
        desc="Score de confiance entre 0 et 1 pour cette transformation"
    )


class PEVTCleaner(dspy.Module):
    """Module DSPY pour nettoyer les PEVT"""
    
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(PEVTCleanerSignature)
    
    def forward(self, pevt_raw: str, context: str) -> dspy.Prediction:
        return self.generate(pevt_raw=pevt_raw, context=context)


class DSPYOptimizer:
    """Gestionnaire d'optimisation DSPY avec support OpenRouter"""
    
    def __init__(self, llm_model: Optional[str] = None, api_key: Optional[str] = None, provider: str = "openrouter"):
        """
        Initialise l'optimiseur DSPY
        
        Args:
            llm_model: Modèle à utiliser (si None, utilise la config par défaut)
            api_key: Clé API (si None, utilise les variables d'environnement)
            provider: Provider (openrouter, openai, anthropic)
        """
        self.provider = provider
        self.llm_model = llm_model
        
        # Configuration du modèle
        if provider == "openrouter":
            # OpenRouter utilise l'API OpenAI mais avec une base_url différente
            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            if api_key is None:
                api_key = os.getenv("API_KEY_OPENROUTER")
            if llm_model is None:
                llm_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
            
            # Headers spécifiques à OpenRouter
            extra_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:8501"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "geneweb-ai-processor"),
            }
            
            lm = dspy.OpenAI(
                model=llm_model,
                api_key=api_key,
                api_base=base_url,
                model_type="chat",
                **{"default_headers": extra_headers}
            )
            
        elif provider == "openai" or "gpt" in (llm_model or ""):
            if api_key is None:
                api_key = os.getenv("OPENAI_API_KEY")
            if llm_model is None:
                llm_model = "gpt-4o-mini"
            lm = dspy.OpenAI(model=llm_model, api_key=api_key)
            
        elif provider == "anthropic" or "claude" in (llm_model or ""):
            if api_key is None:
                api_key = os.getenv("ANTHROPIC_API_KEY")
            if llm_model is None:
                llm_model = "claude-3-5-sonnet-20241022"
            lm = dspy.Claude(model=llm_model, api_key=api_key)
        else:
            raise ValueError(f"Provider non supporté: {provider}")
        
        self.llm_model = llm_model
        dspy.settings.configure(lm=lm)
        
        self.cleaner = PEVTCleaner()
        self.optimized_cleaner = None
    
    def prepare_training_data(
        self, 
        examples: List[AnnotationExample]
    ) -> List[dspy.Example]:
        """Prépare les données d'entraînement au format DSPY"""
        
        dspy_examples = []
        
        for ex in examples:
            # Formater le PEVT brut
            pevt_raw_str = self._format_pevt_raw(ex.pevt_raw)
            
            # Formater les données nettoyées
            place_json = json.dumps(ex.pevt_cleaned.place_structured, ensure_ascii=False)
            
            dspy_examples.append(
                dspy.Example(
                    pevt_raw=pevt_raw_str,
                    context="",  # Sera rempli lors de l'optimisation
                    event_type=ex.pevt_cleaned.event_type.value,
                    date_iso=ex.pevt_cleaned.date_iso or "",
                    place_structured=place_json,
                    organization=ex.pevt_cleaned.organization or "",
                    description=ex.pevt_cleaned.description,
                    confidence=str(ex.pevt_cleaned.confidence_score)
                ).with_inputs("pevt_raw", "context")
            )
        
        return dspy_examples
    
    def _format_pevt_raw(self, pevt: PEVTRaw) -> str:
        """Formate un PEVT brut pour l'entrée du modèle"""
        return f"""Personne: {pevt.person_surname} {pevt.person_name}
Tag événement: #{pevt.event_tag}
Date: {pevt.date or 'N/A'}
Lieu: {pevt.place or 'N/A'}
Témoins: {', '.join(pevt.witnesses) if pevt.witnesses else 'Aucun'}
Notes: {' | '.join(pevt.notes) if pevt.notes else 'Aucune'}
Sources: {', '.join(pevt.sources) if pevt.sources else 'Aucune'}
Texte brut:
{pevt.raw_text}"""
    
    def optimize(
        self, 
        training_examples: List[AnnotationExample],
        validation_examples: Optional[List[AnnotationExample]] = None,
        metric: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Optimise le prompt avec DSPY
        
        Args:
            training_examples: Exemples annotés pour l'entraînement
            validation_examples: Exemples pour la validation
            metric: Fonction de métrique personnalisée
        
        Returns:
            Dictionnaire avec les résultats de l'optimisation
        """
        
        # Préparer les données
        train_set = self.prepare_training_data(training_examples)
        
        # Métrique par défaut si non fournie
        if metric is None:
            metric = self._default_metric
        
        # Optimisation avec BootstrapFewShot
        from dspy.teleprompt import BootstrapFewShot
        
        optimizer = BootstrapFewShot(
            metric=metric,
            max_bootstrapped_demos=int(os.getenv("DSPY_MAX_BOOTSTRAPPED_DEMOS", 4)),
            max_labeled_demos=int(os.getenv("DSPY_MAX_LABELED_DEMOS", 8))
        )
        
        self.optimized_cleaner = optimizer.compile(
            self.cleaner,
            trainset=train_set
        )
        
        # Évaluation sur les données de validation si fournies
        results = {
            'training_size': len(training_examples),
            'model': self.llm_model,
            'provider': self.provider,
            'optimizer': 'BootstrapFewShot'
        }
        
        if validation_examples:
            val_set = self.prepare_training_data(validation_examples)
            val_results = self._evaluate(val_set, metric)
            results['validation'] = val_results
        
        return results
    
    def _default_metric(self, example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """Métrique par défaut pour évaluer la qualité de la transformation"""
        score = 0.0
        total_checks = 5
        
        # Vérifier si le type d'événement est correct
        if pred.event_type.lower() == example.event_type.lower():
            score += 1.0
        
        # Vérifier si l'organisation est mentionnée (si présente dans l'exemple)
        if example.organization and example.organization.lower() in pred.organization.lower():
            score += 1.0
        elif not example.organization:
            score += 1.0
        
        # Vérifier si la date est correcte (flexibilité sur le format)
        if example.date_iso in pred.date_iso or pred.date_iso in example.date_iso:
            score += 1.0
        elif not example.date_iso and not pred.date_iso:
            score += 1.0
        
        # Vérifier si la description contient des mots-clés de l'événement
        if pred.description and len(pred.description) > 10:
            score += 1.0
        
        # Vérifier le score de confiance (doit être > 0.3)
        try:
            conf = float(pred.confidence)
            if conf > 0.3:
                score += 1.0
        except:
            pass
        
        return score / total_checks
    
    def _evaluate(self, eval_set: List[dspy.Example], metric: callable) -> Dict[str, float]:
        """Évalue le modèle sur un ensemble de données"""
        from dspy.evaluate import Evaluate
        
        evaluator = Evaluate(
            devset=eval_set,
            metric=metric,
            num_threads=1,
            display_progress=True
        )
        
        score = evaluator(self.optimized_cleaner or self.cleaner)
        
        return {
            'accuracy': score,
            'examples_count': len(eval_set)
        }
    
    def predict(self, pevt_raw: PEVTRaw, context: str = "") -> PEVTCleaned:
        """
        Prédit la transformation d'un PEVT brut
        
        Args:
            pevt_raw: PEVT brut à transformer
            context: Contexte additionnel
        
        Returns:
            PEVT nettoyé
        """
        pevt_str = self._format_pevt_raw(pevt_raw)
        
        cleaner = self.optimized_cleaner or self.cleaner
        pred = cleaner(pevt_raw=pevt_str, context=context)
        
        # Convertir la prédiction en PEVTCleaned
        try:
            place_dict = json.loads(pred.place_structured)
        except:
            place_dict = {"raw": pred.place_structured}
        
        try:
            confidence = float(pred.confidence)
        except:
            confidence = 0.5
        
        from .data_models import EventType
        
        # Mapper le type d'événement
        event_type_map = {
            'éducation': EventType.EDUCATION,
            'education': EventType.EDUCATION,
            'profession': EventType.OCCUPATION,
            'occupation': EventType.OCCUPATION,
            'résidence': EventType.RESIDENCE,
            'residence': EventType.RESIDENCE,
            'naissance': EventType.BIRTH,
            'birth': EventType.BIRTH,
            'décès': EventType.DEATH,
            'death': EventType.DEATH,
            'mariage': EventType.MARRIAGE,
            'marriage': EventType.MARRIAGE,
        }
        
        event_type = event_type_map.get(
            pred.event_type.lower(),
            EventType.CUSTOM
        )
        
        return PEVTCleaned(
            original=pevt_raw,
            event_type=event_type,
            date_iso=pred.date_iso if pred.date_iso else None,
            place_structured=place_dict,
            organization=pred.organization if pred.organization else None,
            description=pred.description,
            confidence_score=confidence,
            needs_review=confidence < float(os.getenv("CONFIDENCE_THRESHOLD", 0.7)),
            cleaned_by="dspy"
        )
    
    def save_model(self, path: str) -> None:
        """Sauvegarde le modèle optimisé"""
        if self.optimized_cleaner:
            self.optimized_cleaner.save(path)
    
    def load_model(self, path: str) -> None:
        """Charge un modèle optimisé"""
        self.optimized_cleaner = PEVTCleaner()
        self.optimized_cleaner.load(path)
