"""
Page 4: Optimisation avec DSPY
"""
import streamlit as st
import sys
from pathlib import Path
import os

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import init_session_state
from src.dspy_optimizer import DSPYOptimizer
import random

init_session_state()

st.title("🔧 Optimisation DSPY")

st.markdown("""
### Étape 4: Optimiser le prompt avec DSPY

DSPY va automatiquement améliorer votre prompt en testant différentes variations
et en sélectionnant les meilleures stratégies de few-shot learning.
""")

# Vérifier qu'on a des annotations
if not st.session_state.annotations or len(st.session_state.annotations) < 10:
    st.warning("⚠️ Au moins 10 annotations sont nécessaires. Retournez à l'étape 2.")
    st.stop()

st.success(f"✅ {len(st.session_state.annotations)} exemples disponibles")

# Configuration
st.sidebar.markdown("### ⚙️ Configuration DSPY")

api_provider = st.sidebar.selectbox(
    "Fournisseur LLM",
    ["OpenAI", "Anthropic"],
    help="Fournisseur pour DSPY"
)

if api_provider == "OpenAI":
    model = st.sidebar.selectbox(
        "Modèle",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        index=0,
        help="gpt-4o-mini est recommandé pour l'optimisation (moins cher)"
    )
    api_key_env = "OPENAI_API_KEY"
else:
    model = st.sidebar.selectbox(
        "Modèle",
        ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        index=0
    )
    api_key_env = "ANTHROPIC_API_KEY"

api_key = st.sidebar.text_input(
    "Clé API",
    type="password",
    value=os.getenv(api_key_env, ""),
    help=f"Votre clé API {api_provider}"
)

# Split des données
st.markdown("### 📊 Split des données")

col1, col2, col3 = st.columns(3)

total_annotations = len(st.session_state.annotations)

with col1:
    train_pct = st.slider("% Entraînement", 50, 80, 60, 5)

with col2:
    val_pct = st.slider("% Validation", 10, 30, 20, 5)

with col3:
    test_pct = 100 - train_pct - val_pct
    st.metric("% Test", test_pct)

# Calculer les tailles
train_size = int(total_annotations * train_pct / 100)
val_size = int(total_annotations * val_pct / 100)
test_size = total_annotations - train_size - val_size

st.info(f"📈 **Split:** {train_size} train / {val_size} validation / {test_size} test")

# Configuration de l'optimisation
st.markdown("### ⚙️ Paramètres d'optimisation")

col1, col2 = st.columns(2)

with col1:
    max_bootstrapped = st.number_input(
        "Max demos bootstrapped",
        min_value=2,
        max_value=10,
        value=4,
        help="Nombre maximum d'exemples générés automatiquement"
    )

with col2:
    max_labeled = st.number_input(
        "Max demos labeled",
        min_value=4,
        max_value=16,
        value=8,
        help="Nombre maximum d'exemples annotés à utiliser"
    )

# Bouton d'optimisation
st.markdown("---")

if st.button("🚀 Lancer l'optimisation DSPY", type="primary", disabled=not api_key):
    if not api_key:
        st.error("❌ Veuillez configurer votre clé API dans la barre latérale")
    else:
        with st.spinner("🔧 Optimisation en cours... Cela peut prendre plusieurs minutes..."):
            try:
                # Mélanger et splitter les données
                annotations = st.session_state.annotations.copy()
                random.shuffle(annotations)
                
                train_examples = annotations[:train_size]
                val_examples = annotations[train_size:train_size + val_size]
                test_examples = annotations[train_size + val_size:]
                
                # Initialiser l'optimiseur
                os.environ[api_key_env] = api_key
                optimizer = DSPYOptimizer(llm_model=model, api_key=api_key)
                
                # Créer une barre de progression
                progress_bar = st.progress(0, text="Initialisation...")
                
                progress_bar.progress(20, text="Préparation des données...")
                
                # Optimisation
                progress_bar.progress(40, text="Optimisation du prompt (peut prendre du temps)...")
                
                results = optimizer.optimize(
                    training_examples=train_examples,
                    validation_examples=val_examples
                )
                
                progress_bar.progress(80, text="Évaluation des résultats...")
                
                # Sauvegarder l'optimiseur
                st.session_state.dspy_optimizer = optimizer
                st.session_state.dspy_results = {
                    **results,
                    'train_size': train_size,
                    'val_size': val_size,
                    'test_size': test_size,
                    'test_examples': test_examples,
                }
                
                progress_bar.progress(100, text="✅ Optimisation terminée!")
                
                st.success("🎉 Optimisation DSPY terminée avec succès!")
                st.balloons()
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'optimisation: {str(e)}")
                st.exception(e)

# Afficher les résultats si disponibles
if st.session_state.dspy_results:
    st.markdown("---")
    st.markdown("### 📊 Résultats de l'optimisation")
    
    results = st.session_state.dspy_results
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Train", results['train_size'])
    
    with col2:
        st.metric("Validation", results['val_size'])
    
    with col3:
        st.metric("Test", results['test_size'])
    
    with col4:
        if 'validation' in results:
            acc = results['validation'].get('accuracy', 0)
            st.metric("Accuracy Val", f"{acc:.1%}")
    
    # Détails
    with st.expander("📋 Détails de l'optimisation"):
        st.json(results)
    
    # Sauvegarder le modèle
    st.markdown("### 💾 Sauvegarder le modèle optimisé")
    
    model_name = st.text_input(
        "Nom du modèle",
        value=f"dspy_model_v{st.session_state.current_prompt_version}",
        help="Nom pour sauvegarder le modèle"
    )
    
    if st.button("💾 Sauvegarder le modèle"):
        try:
            model_path = f"/opt/geneweb/data/training/{model_name}.json"
            st.session_state.dspy_optimizer.save_model(model_path)
            st.success(f"✅ Modèle sauvegardé: {model_path}")
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
    
    # Test sur quelques exemples
    if results.get('test_examples'):
        st.markdown("---")
        st.markdown("### 🧪 Test sur des exemples")
        
        test_examples = results['test_examples']
        
        num_test = st.slider(
            "Nombre d'exemples à tester",
            min_value=1,
            max_value=min(10, len(test_examples)),
            value=min(3, len(test_examples))
        )
        
        if st.button("🧪 Tester le modèle optimisé"):
            for i, example in enumerate(test_examples[:num_test]):
                with st.expander(f"Test {i+1}: #{example.pevt_raw.event_tag}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Attendu (annotation manuelle):**")
                        st.write(f"Type: {example.pevt_cleaned.event_type.value}")
                        st.write(f"Date: {example.pevt_cleaned.date_iso}")
                        st.write(f"Org: {example.pevt_cleaned.organization}")
                        st.write(f"Desc: {example.pevt_cleaned.description}")
                    
                    with col2:
                        st.markdown("**Prédit (DSPY):**")
                        try:
                            predicted = st.session_state.dspy_optimizer.predict(
                                example.pevt_raw
                            )
                            st.write(f"Type: {predicted.event_type.value}")
                            st.write(f"Date: {predicted.date_iso}")
                            st.write(f"Org: {predicted.organization}")
                            st.write(f"Desc: {predicted.description}")
                            st.write(f"Confiance: {predicted.confidence_score:.2f}")
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")

# Bouton pour passer à l'étape suivante
if st.session_state.dspy_optimizer:
    st.markdown("---")
    if st.button("✅ Passer à la validation", type="primary"):
        st.switch_page("pages/5_✅_Validation.py")
