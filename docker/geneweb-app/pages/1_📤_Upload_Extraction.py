"""
Page 1: Upload du fichier .gw et extraction des PEVT personnalisés
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pevt_extractor import PEVTExtractor
from src.utils import init_session_state

init_session_state()

st.title("📤 Upload & Extraction des PEVT")

st.markdown("""
### Étape 1: Charger votre fichier .gw

Uploadez votre fichier GeneWeb (.gw) pour extraire les événements PEVT personnalisés.
""")

# Upload du fichier
uploaded_file = st.file_uploader(
    "Choisissez un fichier .gw",
    type=['gw'],
    help="Format GeneWeb natif"
)

if uploaded_file is not None:
    # Sauvegarder temporairement le fichier
    temp_path = Path("/tmp") / f"uploaded_{datetime.now().timestamp()}.gw"
    
    with open(temp_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"✅ Fichier chargé: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
    
    # Bouton pour lancer l'extraction
    if st.button("🔍 Extraire les PEVT personnalisés", type="primary"):
        with st.spinner("Extraction en cours..."):
            try:
                extractor = PEVTExtractor()
                extractor.load_from_file(str(temp_path))
                
                # Sauvegarder dans le session state
                st.session_state.uploaded_file_path = str(temp_path)
                st.session_state.all_pevts = extractor.all_pevts
                st.session_state.pevt_stats = extractor.stats
                
                st.success(f"✅ {extractor.stats['total_pevts']} PEVT extraits!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'extraction: {str(e)}")
                st.exception(e)

# Afficher les statistiques si extraction faite
if st.session_state.all_pevts:
    st.markdown("---")
    st.subheader("📊 Statistiques des PEVT extraits")
    
    stats = st.session_state.pevt_stats
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total PEVT personnalisés", stats['total_pevts'])
        st.metric("Avec date", stats['with_date'])
        st.metric("Avec lieu", stats['with_place'])
    
    with col2:
        st.metric("Types uniques", stats['unique_event_types'])
        st.metric("Avec témoins", stats['with_witnesses'])
        st.metric("Avec notes", stats['with_notes'])
    
    with col3:
        st.metric("Fichier", Path(st.session_state.uploaded_file_path).name)
    
    # Distribution des types d'événements
    st.markdown("### 📈 Distribution des types d'événements")
    
    import pandas as pd
    
    dist_df = pd.DataFrame(
        list(stats['event_type_distribution'].items()),
        columns=['Type', 'Count']
    ).sort_values('Count', ascending=False)
    
    st.dataframe(dist_df, use_container_width=True)
    
    # Visualisation
    import plotly.express as px
    
    fig = px.bar(
        dist_df.head(15),
        x='Type',
        y='Count',
        title="Top 15 des types d'événements",
        labels={'Type': "Type d'événement", 'Count': 'Nombre'},
        color='Count',
        color_continuous_scale='Viridis'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sélection d'un échantillon
    st.markdown("---")
    st.subheader("🎯 Sélection de l'échantillon pour annotation")
    
    sample_size = st.slider(
        "Nombre d'exemples à annoter",
        min_value=10,
        max_value=50,
        value=30,
        step=5,
        help="Recommandé: 20-30 exemples pour un bon entraînement"
    )
    
    if st.button("🎲 Générer un échantillon diversifié", type="primary"):
        extractor = PEVTExtractor()
        extractor.all_pevts = st.session_state.all_pevts
        extractor.stats = st.session_state.pevt_stats
        
        sample = extractor.get_diverse_sample(sample_size)
        st.session_state.sample_pevts = sample
        
        st.success(f"✅ {len(sample)} exemples sélectionnés!")
        st.info("👉 Passez à l'étape 2: Annotation dans la barre latérale")
        
        # Aperçu de l'échantillon
        st.markdown("### 👀 Aperçu de l'échantillon")
        
        sample_types = {}
        for pevt in sample:
            sample_types[pevt.event_tag] = sample_types.get(pevt.event_tag, 0) + 1
        
        preview_df = pd.DataFrame(
            list(sample_types.items()),
            columns=['Type', 'Count']
        ).sort_values('Count', ascending=False)
        
        st.dataframe(preview_df, use_container_width=True)

else:
    st.info("👆 Uploadez un fichier .gw pour commencer")

# Exemple de format
with st.expander("📖 Format d'un événement PEVT"):
    st.code("""
pevt CAYEUX Guillaume_Frédéric_Etienne
#Cours_peinture ~1988 #p Pernois,_80619,_Somme,_Picardie,_France
wit m: PHILIPPE Dominique #occu Artiste_peintre
note Champion de peinture
end pevt
    """, language="text")
    
    st.markdown("""
    **Éléments à extraire:**
    - Tag personnalisé: `#Cours_peinture`
    - Date: `~1988` (approximative)
    - Lieu: `Pernois, 80619, Somme, Picardie, France`
    - Témoin: `PHILIPPE Dominique` (Artiste peintre)
    - Note: `Champion de peinture`
    """)
