"""
Application Streamlit pour le traitement de données généalogiques avec IA
Workflow complet d'annotation et d'optimisation DSPY
"""
import streamlit as st
from pathlib import Path
import sys

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import init_session_state

# Configuration de la page
st.set_page_config(
    page_title="GeneWeb AI Processor",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialiser le session state
init_session_state()

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #2E7D32;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# En-tête principal
st.markdown('<p class="main-header">🌳 GeneWeb AI Processor</p>', unsafe_allow_html=True)

st.markdown("""
## 🎯 Bienvenue dans l'outil de nettoyage intelligent de données généalogiques

Cette application utilise l'IA et DSPY pour transformer vos événements PEVT personnalisés en données structurées et normalisées.

### 📋 Workflow complet

Suivez ces étapes dans l'ordre pour obtenir les meilleurs résultats :
""")

# Afficher les étapes du workflow
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="step-card">
        <h4>1️⃣ Upload & Extraction</h4>
        <p>Chargez votre fichier .gw et extrayez les PEVT personnalisés</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <h4>2️⃣ Annotation Exemples</h4>
        <p>Annotez 20-30 exemples manuellement pour créer les données d'entraînement</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <h4>3️⃣ Enrichissement Prompt</h4>
        <p>L'IA enrichit le prompt avec vos exemples</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="step-card">
        <h4>4️⃣ Optimisation DSPY</h4>
        <p>DSPY optimise le prompt automatiquement</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <h4>5️⃣ Validation</h4>
        <p>Validez les résultats sur de nouveaux exemples</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <h4>6️⃣ Transformation Masse</h4>
        <p>Transformez tous vos PEVT automatiquement</p>
    </div>
    """, unsafe_allow_html=True)

# Statistiques rapides si des données sont chargées
if st.session_state.all_pevts:
    st.markdown("---")
    st.subheader("📊 Statistiques du fichier chargé")
    
    col1, col2, col3, col4 = st.columns(4)
    
    stats = st.session_state.pevt_stats
    
    with col1:
        st.metric("Total PEVT", stats.get('total_pevts', 0))
    
    with col2:
        st.metric("Types uniques", stats.get('unique_event_types', 0))
    
    with col3:
        st.metric("Annotations", len(st.session_state.annotations))
    
    with col4:
        progress = len(st.session_state.annotations)
        target = 30
        pct = min(100, int(progress / target * 100))
        st.metric("Progression", f"{pct}%")

st.markdown("---")

# Navigation
st.info("👈 **Utilisez la barre latérale pour naviguer entre les différentes étapes**")

# Services disponibles
st.markdown("### 🔗 Services disponibles")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🌳 GeneWeb 7.0.0**")
    st.code("http://localhost:2317", language="text")

with col2:
    st.markdown("**📊 Cette application**")
    st.code("http://localhost:8501", language="text")

# Footer
st.markdown("---")
st.markdown("*Développé avec ❤️ pour la généalogie - Propulsé par DSPY et Streamlit*")
