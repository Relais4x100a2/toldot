"""
Page 5: Validation des transformations
"""
import streamlit as st
import sys
from pathlib import Path
import random

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import init_session_state, format_place_display, calculate_metrics
from src.data_models import ValidationResult

init_session_state()

st.title("✅ Validation des Transformations")

st.markdown("""
### Étape 5: Valider les résultats du modèle

Testez le modèle optimisé sur de nouveaux exemples et validez/corrigez les résultats.
En fonction des performances, vous pouvez :
- ✅ **Bonne performance** → Passer à la transformation de masse
- ⚠️ **Performance moyenne** → Annoter plus d'exemples et réoptimiser
- ❌ **Mauvaise performance** → Revoir les annotations et le prompt
""")

# Vérifier qu'on a un optimiseur
if not st.session_state.dspy_optimizer:
    st.warning("⚠️ Aucun modèle DSPY disponible. Retournez à l'étape 4 pour optimiser.")
    st.stop()

# Préparer un batch de validation si pas déjà fait
if not st.session_state.validation_batch:
    # Prendre des PEVT non encore annotés
    annotated_tags = {ann.pevt_raw.event_tag for ann in st.session_state.annotations}
    available_pevts = [
        p for p in st.session_state.all_pevts 
        if p.event_tag not in annotated_tags
    ]
    
    if available_pevts:
        # Prendre 20 exemples aléatoires
        num_to_validate = min(20, len(available_pevts))
        st.session_state.validation_batch = random.sample(available_pevts, num_to_validate)
    else:
        st.warning("⚠️ Tous les PEVT ont été annotés. Utilisez l'étape 6 pour la transformation de masse.")
        st.stop()

# Progression
total = len(st.session_state.validation_batch)
current = st.session_state.current_validation_index
validated = len(st.session_state.validations)

st.progress(validated / total, text=f"Progression: {validated}/{total} validations")

# Navigation
col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

with col1:
    if st.button("⬅️ Précédent", disabled=current == 0):
        st.session_state.current_validation_index = max(0, current - 1)
        st.rerun()

with col2:
    st.markdown(f"**Validation {current + 1} / {total}**")

with col3:
    val_selector = st.selectbox(
        "Aller à",
        range(total),
        index=current,
        format_func=lambda x: f"Validation {x + 1}",
        label_visibility="collapsed"
    )
    if val_selector != current:
        st.session_state.current_validation_index = val_selector
        st.rerun()

with col4:
    if st.button("Suivant ➡️", disabled=current >= total - 1):
        st.session_state.current_validation_index = min(total - 1, current + 1)
        st.rerun()

# PEVT courant
pevt = st.session_state.validation_batch[current]

st.markdown("---")

# Prédiction du modèle
with st.spinner("🤖 Prédiction en cours..."):
    try:
        predicted = st.session_state.dspy_optimizer.predict(pevt)
    except Exception as e:
        st.error(f"❌ Erreur de prédiction: {str(e)}")
        st.exception(e)
        st.stop()

# Affichage en 3 colonnes
col1, col2, col3 = st.columns([1, 1.5, 1])

with col1:
    st.subheader("📋 Original")
    st.markdown(f"**Personne:**")
    st.text(f"{pevt.person_surname} {pevt.person_name}")
    st.markdown(f"**Tag:**")
    st.code(f"#{pevt.event_tag}")
    st.markdown(f"**Date:**")
    st.text(pevt.date or "N/A")
    st.markdown(f"**Lieu:**")
    st.text(pevt.place or "N/A")
    
    with st.expander("📄 Texte brut"):
        st.text(pevt.raw_text)

with col2:
    st.subheader("🤖 Prédiction DSPY")
    
    # Indicateur de confiance
    conf_color = "🟢" if predicted.confidence_score >= 0.7 else "🟡" if predicted.confidence_score >= 0.5 else "🔴"
    st.markdown(f"**Confiance:** {conf_color} {predicted.confidence_score:.0%}")
    
    st.markdown(f"**Type:** {predicted.event_type.value}")
    st.markdown(f"**Date ISO:** {predicted.date_iso or 'N/A'}")
    st.markdown(f"**Lieu:** {format_place_display(predicted.place_structured)}")
    st.markdown(f"**Organisation:** {predicted.organization or 'N/A'}")
    st.markdown(f"**Description:**")
    st.info(predicted.description)

with col3:
    st.subheader("✅ Validation")
    
    # Formulaire de validation
    with st.form(key=f"validation_form_{current}"):
        is_correct = st.radio(
            "La transformation est-elle correcte ?",
            ["✅ Oui, parfaite", "⚠️ Partiellement (avec corrections)", "❌ Non, incorrecte"],
            index=1 if predicted.confidence_score < 0.7 else 0
        )
        
        errors = st.multiselect(
            "Erreurs détectées",
            [
                "Type d'événement incorrect",
                "Date incorrecte",
                "Lieu incorrect",
                "Organisation incorrecte",
                "Description imprécise",
                "Autres"
            ]
        )
        
        corrections_notes = st.text_area(
            "Notes de correction",
            placeholder="Décrivez les corrections nécessaires...",
            height=100
        )
        
        validator_name = st.text_input(
            "Validateur",
            value="validateur"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit = st.form_submit_button("✅ Valider et Suivant", type="primary", width='stretch')
        
        with col2:
            submit_stay = st.form_submit_button("💾 Valider et Rester", width='stretch')
        
        if submit or submit_stay:
            # Créer le résultat de validation
            validation_result = ValidationResult(
                pevt_cleaned=predicted,
                is_correct=(is_correct == "✅ Oui, parfaite"),
                errors=errors,
                corrections={'notes': corrections_notes},
                validator=validator_name
            )
            
            st.session_state.validations.append(validation_result)
            st.session_state.data_manager.save_validation(validation_result)
            
            st.success("✅ Validation enregistrée!")
            
            if submit and current < total - 1:
                st.session_state.current_validation_index += 1
            
            st.rerun()

# Statistiques de validation
st.markdown("---")
st.subheader("📊 Statistiques de validation")

metrics = calculate_metrics(st.session_state.validations)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Validés", metrics['total'])

with col2:
    st.metric("Corrects", metrics['correct'], delta=f"{metrics['accuracy']:.0%}")

with col3:
    st.metric("Incorrects", metrics['incorrect'])

with col4:
    if metrics['accuracy'] >= 0.8:
        st.success("✅ Excellent")
    elif metrics['accuracy'] >= 0.6:
        st.warning("⚠️ Moyen")
    else:
        st.error("❌ À améliorer")

# Recommandations
if validated >= 10:
    st.markdown("---")
    st.subheader("💡 Recommandations")
    
    if metrics['accuracy'] >= 0.8:
        st.success("""
        ✅ **Excellente performance!** (≥80% de précision)
        
        Vous pouvez passer à la transformation de masse en toute confiance.
        """)
        
        if st.button("🚀 Passer à la transformation de masse", type="primary"):
            st.switch_page("pages/6_🚀_Transformation_Masse.py")
    
    elif metrics['accuracy'] >= 0.6:
        st.warning("""
        ⚠️ **Performance moyenne** (60-80% de précision)
        
        Recommandations:
        1. Annotez 10-20 exemples supplémentaires des cas problématiques
        2. Ajustez le prompt pour être plus spécifique
        3. Réoptimisez avec DSPY
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Annoter plus d'exemples"):
                st.switch_page("pages/2_✏️_Annotation.py")
        with col2:
            if st.button("🔧 Réoptimiser"):
                st.switch_page("pages/4_🔧_Optimisation_DSPY.py")
    
    else:
        st.error("""
        ❌ **Performance insuffisante** (<60% de précision)
        
        Actions recommandées:
        1. Revoyez vos annotations initiales (cohérence?)
        2. Enrichissez à nouveau le prompt
        3. Annotez plus d'exemples variés (20-30 de plus)
        4. Réoptimisez complètement
        """)
        
        if st.button("🔄 Retour à l'annotation"):
            st.switch_page("pages/2_✏️_Annotation.py")

# Bouton pour générer un nouveau batch
if validated >= total:
    st.markdown("---")
    if st.button("🔄 Générer un nouveau batch de validation"):
        st.session_state.validation_batch = []
        st.session_state.current_validation_index = 0
        st.rerun()
