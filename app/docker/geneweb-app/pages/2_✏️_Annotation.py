"""
Page 2: Annotation manuelle des événements non standardisés
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

st.title("✏️ Reformulation des Événements Non Standardisés")

st.markdown("""
### Étape 2: Reformulez les événements non standardisés

**Important :** Vous reformulez les événements qui n'appartiennent pas à la liste officielle GeneWeb.
- **Destin** : Choisissez d'abord si garder l'événement dans la fiche individuelle ou le transférer vers une fiche INDIVORG
- **Organisation** : Si transfert, précisez l'organisation concernée
- **Tag & Notes** : Améliorez la cohérence d'écriture

Les événements standardisés (#birt, #bapt, #deat, #occu, #educ, etc.) sont automatiquement ignorés.
""")

# Vérifier qu'on a bien un échantillon
if not st.session_state.sample_pevts:
    st.warning("⚠️ Aucun échantillon disponible. Retournez à l'étape 1 pour générer un échantillon.")
    st.stop()

# Progression
total = len(st.session_state.sample_pevts)
current = st.session_state.current_annotation_index
annotated = len(st.session_state.annotations)

st.progress(annotated / total, text=f"Progression: {annotated}/{total} événements reformulés")

# Navigation entre les exemples
col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

with col1:
    if st.button("⬅️ Précédent", disabled=current == 0):
        st.session_state.current_annotation_index = max(0, current - 1)
        st.rerun()

with col2:
    st.markdown(f"**Événement {current + 1} / {total}**")

with col3:
    example_selector = st.selectbox(
        "Aller à l'événement",
        range(total),
        index=current,
        format_func=lambda x: f"Événement {x + 1}",
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
    st.subheader("📋 Événement Original (Non standardisé)")
    
    st.markdown("**Personne:**")
    st.code(f"{pevt.person_surname} {pevt.person_name}", language="text")
    
    st.markdown("**Tag événement original:**")
    st.code(f"#{pevt.event_tag} ⚠️ Hors liste standard", language="text")
    st.caption("⚠️ Cet événement n'appartient pas à la liste officielle GeneWeb")
    
    if pevt.date:
        st.markdown("**Date:**")
        st.code(pevt.date, language="text")
    
    if pevt.place:
        st.markdown("**Lieu:**")
        st.code(pevt.place, language="text")
    
    if pevt.witnesses:
        st.markdown("**Témoins (pour cet événement):**")
        for wit in pevt.witnesses:
            st.code(wit, language="text")
    else:
        st.info("Aucun témoin pour cet événement")
    
    if pevt.sources:
        st.markdown("**Sources (pour cet événement):**")
        for src in pevt.sources:
            st.code(src, language="text")
    else:
        st.info("Aucune source pour cet événement")
    
    # Afficher les notes originales (celles à reformuler)
    st.markdown("**📝 Notes originales (à reformuler):**")
    if pevt.notes:
        for note in pevt.notes:
            st.text_area(
                "note_originale",
                value=note,
                height=100,
                disabled=True,
                label_visibility="collapsed"
            )
    else:
        st.info("Aucune note trouvée pour cet événement")

with col_right:
    st.subheader("✨ Reformulation et Destin de l'Événement")
    
    st.info("💡 **Objectif :** Déterminez d'abord le destin de l'événement, puis reformulez-le.")
    
    # Initialiser l'état de destination pour cet événement si pas déjà fait
    if f"event_destination_{current}" not in st.session_state:
        st.session_state[f"event_destination_{current}"] = "garder_individuel"
    
    # Choix du destin de l'événement (HORS du formulaire pour permettre la réactivité)
    st.markdown("**🎯 Destin de l'événement** *")
    event_destination = st.radio(
        "Que voulez-vous faire avec cet événement ?",
        options=[
            "garder_individuel",
            "transferer_org"
        ],
        format_func=lambda x: {
            "garder_individuel": "✅ Garder dans la fiche individuelle (événement personnel)",
            "transferer_org": "🏢 Transférer vers une fiche INDIVORG (événement organisationnel)"
        }[x],
        help="Choisissez si cet événement concerne la personne directement ou une organisation",
        key=f"radio_dest_{current}"
    )
    
    # Organisation / Institution (CONDITIONNEL - seulement si transfert vers INDIVORG)
    if event_destination == "transferer_org":
        st.markdown("**🏢 Organisation / Institution** *")
        organization = st.text_input(
            "Nom de l'organisation concernée",
            placeholder="Ex: Lycée Montalembert, Goodyear, École des Beaux-Arts, etc.",
            help="Nom de l'école, entreprise, association, institution liée à cet événement",
            label_visibility="collapsed",
            key=f"org_input_{current}"
        )
    else:
        # Si gardé dans la fiche individuelle, pas de champ organisation
        organization = None
    
    st.markdown("---")
    
    with st.form(key=f"annotation_form_{current}"):
        # Édition du tag événement
        st.markdown("**🏷️ Tag événement reformulé** *")
        new_event_tag = st.text_input(
            "Modifiez le tag événement pour le rendre plus descriptif",
            value=pevt.event_tag,
            placeholder="Ex: cours_peinture, formation_professionnelle, etc.",
            help="Modifiez le tag original pour le rendre plus descriptif et compréhensible",
            label_visibility="collapsed"
        )
        st.caption("⚠️ Ce nouveau tag remplacera l'ancien #{pevt.event_tag}")
        
        # Reformulation des notes (champ texte libre)
        st.markdown("**📝 Reformulation des notes** *")
        reformulated_notes = st.text_area(
            "Reformulez les notes de cet événement en texte libre",
            placeholder="Ex: Cours de peinture avec l'artiste Dominique Philippe",
            help="Reformulez les notes originales en texte libre, clair et compréhensible",
            height=150,
            label_visibility="collapsed"
        )
        st.caption("⚠️ Cette reformulation remplacera les notes originales de l'événement")
        
        # Date ISO (optionnelle)
        date_col1, date_col2 = st.columns([3, 1])
        with date_col1:
            date_iso = st.text_input(
                "Date ISO (optionnelle)",
                placeholder="1988-06-15 ou 1988 ou vide",
                help="Format ISO ou année seule. Laissez vide si inconnu."
            )
        with date_col2:
            date_uncertainty = st.selectbox(
                "Incertitude",
                ["", "~", "before", "after"],
                help="~ = approximatif"
            )
        
        # Lieu structuré (optionnel)
        st.markdown("**Lieu structuré (optionnel)**")
        place_col1, place_col2 = st.columns(2)
        
        with place_col1:
            ville = st.text_input("Ville", placeholder="Pernois")
            departement = st.text_input("Département", placeholder="Somme")
            pays = st.text_input("Pays", placeholder="France")
        
        with place_col2:
            code_insee = st.text_input("Code INSEE", placeholder="80619")
            region = st.text_input("Région", placeholder="Picardie")
        
        # Score de confiance
        confidence_score = st.slider(
            "Score de confiance",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.1,
            help="Votre niveau de confiance dans cette reformulation (1.0 = très confiant)"
        )
        
        # Annotateur
        annotator = st.text_input(
            "Votre nom / identifiant",
            value="annotateur",
            help="Pour tracer qui a fait la reformulation"
        )
        
        # Boutons de soumission
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            submit_button = st.form_submit_button(
                "✅ Valider et Suivant",
                type="primary",
                width='stretch'
            )
        
        with col2:
            submit_stay_button = st.form_submit_button(
                "💾 Valider et Rester",
                width='stretch'
            )
        
        with col3:
            skip_button = st.form_submit_button(
                "⏭️ Passer",
                width='stretch'
            )
        
        if submit_button or submit_stay_button:
            # Validation
            if not new_event_tag:
                st.error("❌ Le tag événement reformulé est obligatoire")
            elif not reformulated_notes:
                st.error("❌ La reformulation des notes est obligatoire")
            elif event_destination == "transferer_org" and not organization:
                st.error("❌ Le nom de l'organisation est obligatoire pour transférer l'événement")
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
                
                # Créer le PEVT nettoyé avec le tag et les notes reformulés
                pevt_cleaned = PEVTCleaned(
                    original=pevt,
                    event_type=EventType.OTHER,  # Type par défaut pour événements non standardisés
                    date_iso=date_iso if date_iso else None,
                    date_uncertainty=date_uncertainty if date_uncertainty else None,
                    place_structured=place_structured,
                    organization=organization if organization else None,
                    description=reformulated_notes,  # La reformulation des notes devient la description
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
                
                # Message de confirmation avec le destin
                if event_destination == "garder_individuel":
                    st.success(f"✅ Événement reformulé et gardé dans la fiche individuelle !")
                else:
                    st.success(f"✅ Événement reformulé et marqué pour transfert vers INDIVORG : {organization}")
                
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
st.subheader("📊 Statistiques de reformulation")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Reformulés", annotated)

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

# Afficher les reformulations récentes
if st.session_state.annotations:
    with st.expander("📝 Voir les reformulations récentes"):
        for i, ann in enumerate(reversed(st.session_state.annotations[-5:])):
            org_info = f" → {ann.pevt_cleaned.organization}" if ann.pevt_cleaned.organization else ""
            st.markdown(f"**{len(st.session_state.annotations) - i}.** `#{ann.pevt_raw.event_tag}` → `#{ann.pevt_cleaned.description[:30]}...`{org_info}")
            st.caption(f"Par {ann.annotator} - Confiance: {ann.pevt_cleaned.confidence_score:.1f}")

# Bouton pour passer à l'étape suivante
if annotated >= 20:
    st.markdown("---")
    if st.button("🚀 Passer à l'enrichissement du prompt", type="primary"):
        st.switch_page("pages/3_🤖_Enrichissement_Prompt.py")
