"""
Page 2: Annotation manuelle des exemples
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import time

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_models import PEVTCleaned, AnnotationExample, EventType
from src.utils import init_session_state

init_session_state()

st.title("✏️ Annotation des Exemples")

st.markdown("""
### Étape 2: Annotez les exemples manuellement

Corrigez et nettoyez les PEVT pour créer des exemples d'entraînement de qualité.
Les valeurs originales sont affichées à gauche, et vous entrez les valeurs nettoyées à droite.
""")

# Vérifier qu'on a bien un échantillon
if not st.session_state.sample_pevts:
    st.warning("⚠️ Aucun échantillon disponible. Retournez à l'étape 1 pour générer un échantillon.")
    st.stop()

# Progression
total = len(st.session_state.sample_pevts)
current = st.session_state.current_annotation_index
annotated = len(st.session_state.annotations)

st.progress(annotated / total, text=f"Progression: {annotated}/{total} exemples annotés")

# Navigation entre les exemples
col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

with col1:
    if st.button("⬅️ Précédent", disabled=current == 0):
        st.session_state.current_annotation_index = max(0, current - 1)
        st.rerun()

with col2:
    st.markdown(f"**Exemple {current + 1} / {total}**")

with col3:
    example_selector = st.selectbox(
        "Aller à l'exemple",
        range(total),
        index=current,
        format_func=lambda x: f"Exemple {x + 1}",
        label_visibility="collapsed"
    )
    if example_selector != current:
        st.session_state.current_annotation_index = example_selector
        st.rerun()

with col4:
    if st.button("Suivant ➡️", disabled=current >= total - 1):
        st.session_state.current_annotation_index = min(total - 1, current + 1)
        st.rerun()

# PEVT courant
pevt = st.session_state.sample_pevts[current]

# Démarrer le chronomètre si pas déjà fait
if st.session_state.annotation_start_time is None:
    st.session_state.annotation_start_time = time.time()

st.markdown("---")

# Interface d'annotation en deux colonnes
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📋 Données Originales (Non transformées)")
    
    st.markdown("**Personne:**")
    st.code(f"{pevt.person_surname} {pevt.person_name}", language="text")
    
    st.markdown("**Tag événement:**")
    st.code(f"#{pevt.event_tag}", language="text")
    
    st.markdown("**Date brute:**")
    st.code(pevt.date or "N/A", language="text")
    
    st.markdown("**Lieu brut:**")
    st.code(pevt.place or "N/A", language="text")
    
    if pevt.witnesses:
        st.markdown("**Témoins:**")
        for wit in pevt.witnesses:
            st.text(wit)
    
    if pevt.notes:
        st.markdown("**Notes:**")
        for note in pevt.notes:
            st.text(note)
    
    st.markdown("**Texte brut complet:**")
    st.text_area(
        "raw_text",
        value=pevt.raw_text,
        height=200,
        disabled=True,
        label_visibility="collapsed"
    )

with col_right:
    st.subheader("✨ Données Nettoyées (À renseigner)")
    
    with st.form(key=f"annotation_form_{current}"):
        # Type d'événement
        event_type = st.selectbox(
            "Type d'événement normalisé *",
            options=[e.value for e in EventType],
            help="Catégorisez l'événement dans un type standard"
        )
        
        # Date ISO
        date_col1, date_col2 = st.columns([3, 1])
        with date_col1:
            date_iso = st.text_input(
                "Date ISO (YYYY-MM-DD)",
                placeholder="1988-06-15 ou 1988 ou vide",
                help="Format ISO ou année seule. Laissez vide si inconnu."
            )
        with date_col2:
            date_uncertainty = st.selectbox(
                "Incertitude",
                ["", "~", "before", "after"],
                help="~ = approximatif"
            )
        
        # Lieu structuré
        st.markdown("**Lieu structuré**")
        place_col1, place_col2 = st.columns(2)
        
        with place_col1:
            ville = st.text_input("Ville", placeholder="Pernois")
            departement = st.text_input("Département", placeholder="Somme")
            pays = st.text_input("Pays", placeholder="France")
        
        with place_col2:
            code_insee = st.text_input("Code INSEE", placeholder="80619")
            region = st.text_input("Région", placeholder="Picardie")
        
        # Organisation
        organization = st.text_input(
            "Organisation / Institution",
            placeholder="Ex: Lycée Montalembert, Goodyear, etc.",
            help="Nom de l'école, entreprise, association, etc."
        )
        
        # Description
        description = st.text_area(
            "Description claire de l'événement *",
            placeholder="Ex: Cours de peinture avec l'artiste Dominique Philippe",
            help="Décrivez l'événement de manière concise et compréhensible",
            height=100
        )
        
        # Score de confiance
        confidence_score = st.slider(
            "Score de confiance",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.1,
            help="Votre niveau de confiance dans cette annotation (1.0 = très confiant)"
        )
        
        # Annotateur
        annotator = st.text_input(
            "Votre nom / identifiant",
            value="annotateur",
            help="Pour tracer qui a fait l'annotation"
        )
        
        # Boutons de soumission
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            submit_button = st.form_submit_button(
                "✅ Valider et Suivant",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            submit_stay_button = st.form_submit_button(
                "💾 Valider et Rester",
                use_container_width=True
            )
        
        with col3:
            skip_button = st.form_submit_button(
                "⏭️ Passer",
                use_container_width=True
            )
        
        if submit_button or submit_stay_button:
            # Validation
            if not description:
                st.error("❌ La description est obligatoire")
            else:
                # Créer la structure de lieu
                place_structured = {}
                if ville:
                    place_structured['ville'] = ville
                if code_insee:
                    place_structured['code_insee'] = code_insee
                if departement:
                    place_structured['departement'] = departement
                if region:
                    place_structured['region'] = region
                if pays:
                    place_structured['pays'] = pays
                
                # Créer le PEVT nettoyé
                pevt_cleaned = PEVTCleaned(
                    original=pevt,
                    event_type=EventType(event_type),
                    date_iso=date_iso if date_iso else None,
                    date_uncertainty=date_uncertainty if date_uncertainty else None,
                    place_structured=place_structured,
                    organization=organization if organization else None,
                    description=description,
                    confidence_score=confidence_score,
                    needs_review=confidence_score < 0.7,
                    cleaned_by="manual",
                )
                
                # Calculer le temps d'annotation
                annotation_time = time.time() - st.session_state.annotation_start_time
                
                # Créer l'exemple d'annotation
                example = AnnotationExample(
                    pevt_raw=pevt,
                    pevt_cleaned=pevt_cleaned,
                    annotator=annotator,
                    annotation_time=annotation_time
                )
                
                # Sauvegarder
                st.session_state.annotations.append(example)
                st.session_state.data_manager.save_annotation(example)
                
                st.success(f"✅ Annotation {len(st.session_state.annotations)} sauvegardée!")
                
                # Réinitialiser le chronomètre
                st.session_state.annotation_start_time = time.time()
                
                # Passer au suivant si demandé
                if submit_button and current < total - 1:
                    st.session_state.current_annotation_index += 1
                
                st.rerun()
        
        if skip_button:
            if current < total - 1:
                st.session_state.current_annotation_index += 1
                st.session_state.annotation_start_time = time.time()
                st.rerun()

# Statistiques d'annotation
st.markdown("---")
st.subheader("📊 Statistiques d'annotation")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Annotés", annotated)

with col2:
    st.metric("Restants", total - annotated)

with col3:
    pct = int(annotated / total * 100) if total > 0 else 0
    st.metric("Progression", f"{pct}%")

with col4:
    if annotated >= 20:
        st.success("✅ Prêt pour DSPY")
    else:
        st.info(f"⏳ {20 - annotated} minimum")

# Afficher les annotations récentes
if st.session_state.annotations:
    with st.expander("📝 Voir les annotations récentes"):
        for i, ann in enumerate(reversed(st.session_state.annotations[-5:])):
            st.markdown(f"**{len(st.session_state.annotations) - i}.** `#{ann.pevt_raw.event_tag}` → {ann.pevt_cleaned.event_type.value}")
            st.caption(f"Par {ann.annotator} - Confiance: {ann.pevt_cleaned.confidence_score:.1f}")

# Bouton pour passer à l'étape suivante
if annotated >= 20:
    st.markdown("---")
    if st.button("🚀 Passer à l'enrichissement du prompt", type="primary"):
        st.switch_page("pages/3_🤖_Enrichissement_Prompt.py")
