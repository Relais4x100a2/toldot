"""
Page 3: Enrichissement du prompt avec l'IA
"""
import streamlit as st
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import init_session_state, get_default_prompt
from src.data_models import PromptVersion
import os

init_session_state()

st.title("🤖 Enrichissement du Prompt")

st.markdown("""
### Étape 3: Améliorer le prompt avec l'IA

Utilisez vos exemples annotés pour demander à l'IA d'enrichir et d'améliorer le prompt de base.
""")

# Vérifier qu'on a des annotations
if not st.session_state.annotations:
    st.warning("⚠️ Aucune annotation disponible. Retournez à l'étape 2 pour annoter des exemples.")
    st.stop()

st.success(f"✅ {len(st.session_state.annotations)} exemples annotés disponibles")

# Configuration de l'API
st.sidebar.markdown("### ⚙️ Configuration API")

api_provider = st.sidebar.selectbox(
    "Fournisseur",
    ["OpenAI", "Anthropic"],
    help="Choisissez votre fournisseur d'API"
)

if api_provider == "OpenAI":
    model = st.sidebar.selectbox(
        "Modèle",
        ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=0
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

# Afficher le prompt actuel
st.markdown("### 📝 Prompt actuel")

current_prompt = st.session_state.current_prompt_text

st.text_area(
    "Prompt de base",
    value=current_prompt,
    height=300,
    disabled=True
)

# Afficher quelques exemples d'annotations
st.markdown("### 📚 Aperçu de vos exemples d'annotation")

num_examples_show = min(3, len(st.session_state.annotations))

for i, ann in enumerate(st.session_state.annotations[:num_examples_show]):
    with st.expander(f"Exemple {i+1}: #{ann.pevt_raw.event_tag}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original:**")
            st.code(f"Tag: #{ann.pevt_raw.event_tag}\nDate: {ann.pevt_raw.date}\nLieu: {ann.pevt_raw.place}")
        
        with col2:
            st.markdown("**Nettoyé:**")
            st.code(f"Type: {ann.pevt_cleaned.event_type.value}\nDate: {ann.pevt_cleaned.date_iso}\nOrg: {ann.pevt_cleaned.organization}\nDesc: {ann.pevt_cleaned.description[:50]}...")

st.caption(f"... et {len(st.session_state.annotations) - num_examples_show} autres exemples")

# Bouton pour enrichir
st.markdown("---")
st.markdown("### 🚀 Enrichir le prompt")

st.info("""
💡 **Comment ça marche ?**

L'IA va analyser vos exemples d'annotation et :
1. Identifier les patterns et règles que vous suivez
2. Détecter les cas spécifiques (abréviations, formats de dates, etc.)
3. Enrichir le prompt avec des instructions plus précises
4. Ajouter des exemples représentatifs
""")

if st.button("✨ Enrichir le prompt avec l'IA", type="primary", disabled=not api_key):
    if not api_key:
        st.error("❌ Veuillez configurer votre clé API dans la barre latérale")
    else:
        with st.spinner("🤖 L'IA analyse vos exemples et enrichit le prompt..."):
            try:
                # Préparer les exemples pour l'IA
                examples_text = ""
                for i, ann in enumerate(st.session_state.annotations[:10], 1):
                    examples_text += f"\n### Exemple {i}\n"
                    examples_text += f"**Input brut:**\n"
                    examples_text += f"- Tag: #{ann.pevt_raw.event_tag}\n"
                    examples_text += f"- Date: {ann.pevt_raw.date}\n"
                    examples_text += f"- Lieu: {ann.pevt_raw.place}\n"
                    examples_text += f"\n**Output attendu:**\n"
                    examples_text += f"- Type: {ann.pevt_cleaned.event_type.value}\n"
                    examples_text += f"- Date ISO: {ann.pevt_cleaned.date_iso}\n"
                    examples_text += f"- Organisation: {ann.pevt_cleaned.organization}\n"
                    examples_text += f"- Description: {ann.pevt_cleaned.description}\n"
                
                # Appel à l'API
                if api_provider == "OpenAI":
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Tu es un expert en prompt engineering et en généalogie."},
                            {"role": "user", "content": f"""Voici un prompt de base pour transformer des événements PEVT généalogiques :

{current_prompt}

Et voici {len(st.session_state.annotations)} exemples d'annotations réalisées par un humain :

{examples_text}

En analysant ces exemples, enrichis et améliore le prompt pour :
1. Ajouter des règles spécifiques identifiées dans les exemples
2. Documenter les patterns de transformation observés
3. Inclure des exemples concrets
4. Préciser les cas particuliers (abréviations, formats, etc.)

Fournis le prompt enrichi en français, prêt à être utilisé."""}
                        ],
                        temperature=0.7
                    )
                    
                    enriched_prompt = response.choices[0].message.content
                
                else:  # Anthropic
                    from anthropic import Anthropic
                    client = Anthropic(api_key=api_key)
                    
                    response = client.messages.create(
                        model=model,
                        max_tokens=4096,
                        messages=[
                            {"role": "user", "content": f"""Voici un prompt de base pour transformer des événements PEVT généalogiques :

{current_prompt}

Et voici {len(st.session_state.annotations)} exemples d'annotations réalisées par un humain :

{examples_text}

En analysant ces exemples, enrichis et améliore le prompt pour :
1. Ajouter des règles spécifiques identifiées dans les exemples
2. Documenter les patterns de transformation observés
3. Inclure des exemples concrets
4. Préciser les cas particuliers (abréviations, formats, etc.)

Fournis le prompt enrichi en français, prêt à être utilisé."""}
                        ]
                    )
                    
                    enriched_prompt = response.content[0].text
                
                # Sauvegarder la nouvelle version
                new_version = st.session_state.current_prompt_version + 1
                
                prompt_version = PromptVersion(
                    version=new_version,
                    prompt_text=enriched_prompt,
                    examples_count=len(st.session_state.annotations),
                    notes=f"Enrichi par {api_provider} {model}"
                )
                
                st.session_state.prompt_history.append(prompt_version)
                st.session_state.current_prompt_text = enriched_prompt
                st.session_state.current_prompt_version = new_version
                st.session_state.data_manager.save_prompt_version(prompt_version)
                
                st.success(f"✅ Prompt enrichi! Version {new_version} créée")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")
                st.exception(e)

# Afficher l'historique des versions
if st.session_state.prompt_history:
    st.markdown("---")
    st.markdown("### 📜 Historique des versions")
    
    for version in reversed(st.session_state.prompt_history):
        with st.expander(f"Version {version.version} - {version.created_at[:19]}"):
            st.markdown(f"**Exemples utilisés:** {version.examples_count}")
            st.markdown(f"**Notes:** {version.notes}")
            st.text_area(
                f"Prompt v{version.version}",
                value=version.prompt_text,
                height=200,
                disabled=True,
                label_visibility="collapsed"
            )
            
            if st.button(f"↩️ Restaurer cette version", key=f"restore_v{version.version}"):
                st.session_state.current_prompt_text = version.prompt_text
                st.success(f"✅ Version {version.version} restaurée")
                st.rerun()

# Bouton pour passer à l'étape suivante
if st.session_state.current_prompt_version > 1 or len(st.session_state.annotations) >= 20:
    st.markdown("---")
    if st.button("🔧 Passer à l'optimisation DSPY", type="primary"):
        st.switch_page("pages/4_🔧_Optimisation_DSPY.py")

