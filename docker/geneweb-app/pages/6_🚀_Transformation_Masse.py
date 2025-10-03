"""
Page 6: Transformation de masse des PEVT
"""
import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import init_session_state, format_place_display

init_session_state()

st.title("🚀 Transformation de Masse")

st.markdown("""
### Étape 6: Transformer tous les PEVT automatiquement

Appliquez le modèle optimisé à tous vos événements PEVT personnalisés.
Les résultats seront exportés au format JSON et pourront être réintégrés dans GeneWeb.
""")

# Vérifier qu'on a un optimiseur
if not st.session_state.dspy_optimizer:
    st.warning("⚠️ Aucun modèle DSPY disponible. Retournez à l'étape 4.")
    st.stop()

# Statistiques
total_pevts = len(st.session_state.all_pevts)
already_processed = len(st.session_state.mass_transformation_results)

st.info(f"📊 **{total_pevts}** PEVT à transformer - **{already_processed}** déjà traités")

# Configuration
st.markdown("### ⚙️ Configuration")

col1, col2 = st.columns(2)

with col1:
    confidence_threshold = st.slider(
        "Seuil de confiance pour marquage de révision",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Les transformations avec un score inférieur seront marquées pour révision manuelle"
    )

with col2:
    batch_size = st.number_input(
        "Taille des batches",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Nombre de PEVT à traiter par batch"
    )

# Options d'export
export_format = st.selectbox(
    "Format d'export",
    ["JSON", "CSV", "JSONL"],
    help="Format pour exporter les résultats"
)

# Bouton de lancement
st.markdown("---")

if already_processed > 0:
    if st.button("🔄 Réinitialiser et recommencer"):
        st.session_state.mass_transformation_results = []
        st.rerun()

if st.button("🚀 Lancer la transformation de masse", type="primary", disabled=already_processed > 0):
    progress_bar = st.progress(0, text="Initialisation...")
    status_text = st.empty()
    
    results = []
    errors = []
    needs_review = []
    
    try:
        for i, pevt in enumerate(st.session_state.all_pevts):
            # Mise à jour de la progression
            progress = (i + 1) / total_pevts
            progress_bar.progress(progress, text=f"Transformation {i+1}/{total_pevts}")
            
            try:
                # Prédiction
                predicted = st.session_state.dspy_optimizer.predict(pevt)
                
                # Marquer pour révision si confiance faible
                if predicted.confidence_score < confidence_threshold:
                    predicted.needs_review = True
                    needs_review.append(predicted)
                
                results.append({
                    'person_name': pevt.person_name,
                    'person_surname': pevt.person_surname,
                    'original_tag': pevt.event_tag,
                    'original_date': pevt.date,
                    'original_place': pevt.place,
                    'event_type': predicted.event_type.value,
                    'date_iso': predicted.date_iso,
                    'place_structured': predicted.place_structured,
                    'organization': predicted.organization,
                    'description': predicted.description,
                    'confidence_score': predicted.confidence_score,
                    'needs_review': predicted.needs_review,
                    'transformed_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                errors.append({
                    'pevt': f"{pevt.person_surname} {pevt.person_name} - #{pevt.event_tag}",
                    'error': str(e)
                })
            
            # Afficher un status toutes les 50 transformations
            if (i + 1) % 50 == 0:
                status_text.text(f"✅ {i+1} transformations | ⚠️ {len(needs_review)} à réviser | ❌ {len(errors)} erreurs")
        
        progress_bar.progress(1.0, text="✅ Transformation terminée!")
        
        # Sauvegarder les résultats
        st.session_state.mass_transformation_results = results
        
        # Sauvegarder dans les métriques
        st.session_state.data_manager.save_metrics({
            'type': 'mass_transformation',
            'total': total_pevts,
            'success': len(results),
            'errors': len(errors),
            'needs_review': len(needs_review),
            'confidence_threshold': confidence_threshold,
        })
        
        st.success(f"🎉 Transformation terminée! {len(results)}/{total_pevts} PEVT transformés")
        st.balloons()
        
        if errors:
            st.warning(f"⚠️ {len(errors)} erreurs détectées")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la transformation: {str(e)}")
        st.exception(e)

# Afficher les résultats si disponibles
if st.session_state.mass_transformation_results:
    results = st.session_state.mass_transformation_results
    
    st.markdown("---")
    st.subheader("📊 Résultats de la transformation")
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(results)
    needs_review_count = sum(1 for r in results if r['needs_review'])
    high_conf_count = sum(1 for r in results if r['confidence_score'] >= 0.8)
    avg_conf = sum(r['confidence_score'] for r in results) / total if total > 0 else 0
    
    with col1:
        st.metric("Total transformé", total)
    
    with col2:
        st.metric("Haute confiance (≥80%)", high_conf_count, delta=f"{high_conf_count/total*100:.0f}%")
    
    with col3:
        st.metric("À réviser", needs_review_count, delta=f"{needs_review_count/total*100:.0f}%")
    
    with col4:
        st.metric("Confiance moyenne", f"{avg_conf:.0%}")
    
    # Distribution par type d'événement
    st.markdown("### 📈 Distribution par type d'événement")
    
    import pandas as pd
    import plotly.express as px
    
    event_types = {}
    for r in results:
        event_types[r['event_type']] = event_types.get(r['event_type'], 0) + 1
    
    df_types = pd.DataFrame(
        list(event_types.items()),
        columns=['Type', 'Count']
    ).sort_values('Count', ascending=False)
    
    fig = px.pie(
        df_types,
        values='Count',
        names='Type',
        title='Répartition des types d\'événements'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau des résultats
    st.markdown("### 📋 Aperçu des résultats")
    
    # Filtre
    filter_option = st.selectbox(
        "Filtrer par",
        ["Tous", "Haute confiance (≥80%)", "À réviser (<70%)", "Confiance moyenne (70-80%)"]
    )
    
    filtered_results = results
    if filter_option == "Haute confiance (≥80%)":
        filtered_results = [r for r in results if r['confidence_score'] >= 0.8]
    elif filter_option == "À réviser (<70%)":
        filtered_results = [r for r in results if r['needs_review']]
    elif filter_option == "Confiance moyenne (70-80%)":
        filtered_results = [r for r in results if 0.7 <= r['confidence_score'] < 0.8]
    
    st.info(f"📊 {len(filtered_results)} résultats affichés")
    
    # Afficher sous forme de tableau
    df_results = pd.DataFrame(filtered_results)
    
    # Sélectionner les colonnes à afficher
    display_columns = [
        'person_surname', 'person_name', 'original_tag',
        'event_type', 'organization', 'description',
        'confidence_score', 'needs_review'
    ]
    
    df_display = df_results[display_columns].head(100)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400
    )
    
    if len(filtered_results) > 100:
        st.caption(f"Affichage limité aux 100 premiers résultats sur {len(filtered_results)}")
    
    # Export
    st.markdown("---")
    st.subheader("💾 Export des résultats")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_filename = st.text_input(
            "Nom du fichier",
            value=f"pevt_transformed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Sans extension"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
    
    # Boutons d'export
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Exporter en JSON", use_container_width=True):
            export_path = f"/opt/geneweb/data/training/{export_filename}.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            st.success(f"✅ Exporté: {export_path}")
    
    with col2:
        if st.button("💾 Exporter en CSV", use_container_width=True):
            export_path = f"/opt/geneweb/data/training/{export_filename}.csv"
            df_results.to_csv(export_path, index=False, encoding='utf-8')
            st.success(f"✅ Exporté: {export_path}")
    
    with col3:
        if st.button("💾 Exporter à réviser", use_container_width=True):
            to_review = [r for r in results if r['needs_review']]
            export_path = f"/opt/geneweb/data/training/{export_filename}_to_review.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(to_review, f, indent=2, ensure_ascii=False)
            st.success(f"✅ Exporté {len(to_review)} résultats à réviser: {export_path}")
    
    # Instructions de réintégration
    with st.expander("📖 Comment réintégrer dans GeneWeb ?"):
        st.markdown("""
        ### Réintégration dans GeneWeb
        
        Les données transformées peuvent être réintégrées dans votre fichier .gw :
        
        1. **Sauvegardez votre fichier .gw original**
        2. **Convertissez les résultats JSON** en format PEVT GeneWeb
        3. **Remplacez ou ajoutez** les événements transformés
        4. **Recompilez la base** avec `gwc`
        
        **Format PEVT GeneWeb:**
        ```
        pevt SURNAME Firstname
        #event_type date #p lieu
        note description
        end pevt
        ```
        
        Un script de conversion sera bientôt disponible pour automatiser ce processus.
        """)

else:
    st.info("👆 Cliquez sur 'Lancer la transformation de masse' pour commencer")

# Navigation vers le dashboard
st.markdown("---")
if st.button("📊 Voir le dashboard complet", type="primary"):
    st.switch_page("pages/7_📊_Dashboard.py")
