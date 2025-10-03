import streamlit as st
import re
import requests
import json
import time
from datetime import datetime

# --- CONFIGURATION ET LOGIQUE DE TRAITEMENT ---

# Cache global pour éviter les requêtes répétées
EVENT_ANALYSIS_CACHE = {}

STANDARD_EVENTS = {
    '#birt', '#bapt', '#deat', '#buri', '#crem', '#acco', '#acqu', '#adhe',
    '#bapl', '#barm', '#basm', '#bles', '#cens', '#chgn', '#circ', '#conf',
    '#conl', '#degr', '#awar', '#demm', '#dist', '#endl', '#dotl', '#educ',
    '#elec', '#emig', '#exco', '#flkl', '#fcom', '#fune', '#grad', '#hosp',
    '#illn', '#immi', '#lpas', '#mdis', '#mpro', '#mser', '#mobm', '#natu',
    '#occu', '#ordn', '#prop', '#resi', '#reti', '#slgc', '#slgp', '#slgs',
    '#vteb', '#will', '#strng'
}

def analyze_event_with_llm(event_name: str, api_key: str, model_name: str, site_url: str, request_delay: float = 1.0, max_retries: int = 3):
    """
    Interroge l'API OpenRouter pour déterminer si un nom d'événement est une organisation.
    Implémente un cache, un rate limiting et un système de retry.
    """
    # Vérifier le cache d'abord
    cache_key = f"{event_name}_{model_name}"
    if cache_key in EVENT_ANALYSIS_CACHE:
        return EVENT_ANALYSIS_CACHE[cache_key]
    
    prompt = f"""
    Analyse le nom d'événement suivant, issu d'un fichier de généalogie : "{event_name}".
    Cet événement représente-t-il une organisation (entreprise, association, groupe informel, etc.) ?

    Réponds uniquement avec un objet JSON valide contenant trois clés :
    1. "is_org": un booléen (true ou false).
    2. "name": une chaîne de caractères avec le nom propre de l'organisation si is_org est true, sinon null. Le nom doit être identique à celui de l'événement, sans le '#' initial.
    3. "type": une chaîne de caractères pour le type d'organisation (ex: "company", "association", "political_party", "informal_group") si is_org est true, sinon null.

    Exemple pour "#Société_des_Maisons_Risloises":
    {{
      "is_org": true,
      "name": "Société_des_Maisons_Risloises",
      "type": "company"
    }}

    Exemple pour "#Vacances_en_Bretagne":
    {{
      "is_org": false,
      "name": null,
      "type": null
    }}

    Ton objet JSON pour "{event_name}":
    """
    
    # Système de retry avec backoff exponentiel
    for attempt in range(max_retries):
        try:
            # Délai avant la requête (sauf pour la première tentative)
            if attempt > 0:
                backoff_delay = request_delay * (2 ** (attempt - 1))
                time.sleep(backoff_delay)
            elif len(EVENT_ANALYSIS_CACHE) > 0:  # Pas la première requête globale
                time.sleep(request_delay)
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": site_url, 
                    "X-Title": "GeneWeb GW Processor", 
                },
                data=json.dumps({
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }),
                timeout=30
            )
            
            if response.status_code in [429, 502, 503, 504]:  # Erreurs temporaires côté serveur
                error_names = {
                    429: "Rate limit",
                    502: "Bad Gateway", 
                    503: "Service Unavailable",
                    504: "Gateway Timeout"
                }
                error_name = error_names.get(response.status_code, f"Erreur {response.status_code}")
                
                if attempt < max_retries - 1:
                    wait_time = request_delay * (2 ** attempt)
                    st.warning(f"{error_name} d'OpenRouter. Attente de {wait_time:.1f}s avant retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    result = {"is_org": False, "error": f"{error_name} - échec après {max_retries} tentatives"}
                    EVENT_ANALYSIS_CACHE[cache_key] = result
                    return result
            
            response.raise_for_status()
            
            # Extrait la réponse JSON de la réponse du LLM
            llm_response_text = response.json()['choices'][0]['message']['content']
            # Nettoyage pour extraire uniquement le JSON
            json_match = re.search(r'\{.*\}', llm_response_text, re.DOTALL)
            if not json_match:
                result = {"is_org": False, "error": "Réponse du LLM non-JSON."}
                EVENT_ANALYSIS_CACHE[cache_key] = result
                return result
            
            parsed_json = json.loads(json_match.group(0))
            # Mettre en cache le résultat
            EVENT_ANALYSIS_CACHE[cache_key] = parsed_json
            return parsed_json

        except requests.Timeout:
            if attempt < max_retries - 1:
                st.warning(f"Timeout de la requête. Retry {attempt + 1}/{max_retries}...")
                continue
            else:
                result = {"is_org": False, "error": "Timeout de la requête après plusieurs tentatives"}
                EVENT_ANALYSIS_CACHE[cache_key] = result
                return result
                
        except requests.RequestException as e:
            # Vérifier si c'est une erreur temporaire worth retrying
            if attempt < max_retries - 1 and any(code in str(e) for code in ["429", "502", "503", "504"]):
                wait_time = request_delay * (2 ** attempt)
                st.warning(f"Erreur réseau temporaire. Retry dans {wait_time:.1f}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                st.error(f"Erreur de réseau lors de l'appel à OpenRouter : {e}")
                result = {"is_org": False, "error": str(e)}
                EVENT_ANALYSIS_CACHE[cache_key] = result
                return result
                
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"Erreur lors de l'analyse de la réponse du LLM : {e}")
            result = {"is_org": False, "error": "Réponse invalide du LLM."}
            EVENT_ANALYSIS_CACHE[cache_key] = result
            return result
    
    # Si on arrive ici, toutes les tentatives ont échoué
    result = {"is_org": False, "error": "Échec après tous les retries"}
    EVENT_ANALYSIS_CACHE[cache_key] = result
    return result

def create_org_pevt_block(org_name: str, org_type: str, original_person: str, original_event_text: str):
    lines = original_event_text.strip().split('\n')
    event_line = lines[0]
    
    # Préserver TOUTES les autres lignes (notes, sources, dates, lieux, etc.)
    other_lines = []
    witness_lines = []
    
    for line in lines[1:]:
        line = line.strip()
        if not line:  # Ignorer les lignes vides
            continue
        if line.startswith("wit"):
            witness_lines.append(line)
        else:
            # Préserver notes, sources, dates, lieux, etc.
            other_lines.append(line)
    
    # Transformer l'événement personnalisé en événement profession (#occu)
    details = event_line.replace(f"#{org_name}", "").strip()
    new_event_line = f"#occu {details}"
    
    # Construire le nouveau bloc avec TOUTES les informations
    header = f"pevt {org_name} ORG_{org_type}"
    content = [new_event_line]
    
    # Ajouter toutes les autres données (notes, sources, dates, etc.)
    content.extend(other_lines)
    
    # Ajouter les témoins (original person en premier, puis les autres)
    new_witnesses = [f"wit m: {original_person}"] + witness_lines
    content.extend(new_witnesses)
    
    return f"{header}\n" + "\n".join(f"  {line}" for line in content) + "\nend pevt"

def process_pevt_block(person_name: str, block_content: str, log_messages: list, api_config: dict):
    event_pattern = re.compile(r"(^#.*?)(?=\n#|\Z)", re.MULTILINE | re.DOTALL)
    events = event_pattern.findall(block_content)
    events_to_keep, newly_created_blocks = [], []

    for event_full_text in events:
        event_tag = event_full_text.strip().split('\n')[0].split(' ')[0]
        if event_tag in STANDARD_EVENTS:
            events_to_keep.append(event_full_text.strip())
            continue
        
        log_messages.append(f"  -> Événement personnalisé trouvé : '{event_tag}'. Analyse via OpenRouter...")
        llm_result = analyze_event_with_llm(
            event_tag, 
            api_config["api_key"], 
            api_config["model_name"], 
            api_config["site_url"],
            api_config.get("request_delay", 1.0),
            api_config.get("max_retries", 3)
        )
        
        if llm_result and llm_result.get("is_org"):
            org_name = llm_result["name"]
            org_type = llm_result["type"]
            log_messages.append(f"    [✓] Organisation identifiée : {org_name} (Type: {org_type}). Création du bloc.")
            new_block = create_org_pevt_block(org_name, org_type, person_name, event_full_text)
            newly_created_blocks.append(new_block)
        else:
            error_msg = f" Erreur: {llm_result.get('error')}" if llm_result.get('error') else ""
            log_messages.append(f"    [i] Pas une organisation.{error_msg}")
            events_to_keep.append(event_full_text.strip())

    return "\n".join(events_to_keep), newly_created_blocks

def process_gw_content(content: str, api_config: dict):
    log_messages, new_org_blocks = [], []
    pevt_pattern = re.compile(r"^(pevt .*?)\n(.*?)\n^(end pevt)", re.MULTILINE | re.DOTALL)
    matches = list(pevt_pattern.finditer(content))
    
    batch_size = api_config.get("batch_size", 5)
    batch_pause = api_config.get("batch_pause", 5.0)
    
    # Diviser les matches en lots
    batches = [matches[i:i + batch_size] for i in range(0, len(matches), batch_size)]
    total_batches = len(batches)
    
    # Compter le nombre total d'événements personnalisés à analyser
    total_custom_events = 0
    for match in matches:
        block_content = match.group(2).strip()
        event_pattern = re.compile(r"(^#.*?)(?=\n#|\Z)", re.MULTILINE | re.DOTALL)
        events = event_pattern.findall(block_content)
        for event_full_text in events:
            event_tag = event_full_text.strip().split('\n')[0].split(' ')[0]
            if event_tag not in STANDARD_EVENTS:
                total_custom_events += 1
    
    if total_custom_events > 0:
        progress_bar = st.progress(0)
        status_text = st.empty()
        batch_status = st.empty()
        current_event = 0
        
        log_messages.append(f"\n📊 Traitement en {total_batches} lot(s) de {batch_size} bloc(s) pevt maximum")
        log_messages.append(f"⏱️  Pause de {batch_pause}s entre chaque lot")
        log_messages.append(f"🎯 Total: {total_custom_events} événements personnalisés à analyser")
    
    # Traiter chaque lot
    for batch_index, batch_matches in enumerate(batches):
        current_batch = batch_index + 1
        
        if total_custom_events > 0:
            batch_status.info(f"📦 **Lot {current_batch}/{total_batches}** - Traitement de {len(batch_matches)} bloc(s) pevt...")
        
        log_messages.append(f"\n{'='*50}")
        log_messages.append(f"📦 DÉBUT DU LOT {current_batch}/{total_batches}")
        log_messages.append(f"{'='*50}")
        
        # Traiter chaque match du lot (en ordre inverse pour les modifications de texte)
        for match in reversed(batch_matches):
            person_header = match.group(1).strip()
            block_content = match.group(2).strip()
            person_name = person_header.replace("pevt ", "").strip()
            log_messages.append(f"\nTraitement du bloc 'pevt' pour : {person_name}")
            
            # Passer les informations de progression
            progress_info = {
                "total": total_custom_events,
                "current": current_event,
                "progress_bar": progress_bar if total_custom_events > 0 else None,
                "status_text": status_text if total_custom_events > 0 else None,
                "batch_info": f"Lot {current_batch}/{total_batches}"
            } if total_custom_events > 0 else None
            
            modified_content, created_blocks, current_event = process_pevt_block_with_progress(
                person_name, block_content, log_messages, api_config, progress_info, current_event
            )
            
            if created_blocks:
                if not modified_content.strip():
                     log_messages.append("  -> Le bloc 'pevt' original est maintenant vide et sera supprimé.")
                     content = content[:match.start()] + content[match.end():]
                else:
                    new_block_str = f"{person_header}\n{modified_content}\nend pevt"
                    content = content[:match.start()] + new_block_str + content[match.end():]
                new_org_blocks.extend(created_blocks)
        
        log_messages.append(f"\n✅ LOT {current_batch}/{total_batches} TERMINÉ")
        
        # Pause entre les lots (sauf pour le dernier)
        if current_batch < total_batches and batch_pause > 0:
            log_messages.append(f"⏸️  Pause de {batch_pause}s avant le prochain lot...")
            if total_custom_events > 0:
                batch_status.warning(f"⏸️ Pause de {batch_pause}s entre les lots... ({current_batch}/{total_batches} terminés)")
            time.sleep(batch_pause)

    if total_custom_events > 0:
        progress_bar.progress(1.0)
        status_text.text("✅ Analyse terminée!")
        batch_status.success(f"🎉 Tous les lots traités ! ({total_batches}/{total_batches})")
        time.sleep(1)  # Afficher le message de fin brièvement

    final_content = content.strip()
    if new_org_blocks:
        final_content += "\n\n# --- Blocs Organisations ajoutés par le script ---\n"
        final_content += "\n".join(new_org_blocks)
    return final_content, new_org_blocks, log_messages

def process_pevt_block_with_progress(person_name: str, block_content: str, log_messages: list, api_config: dict, progress_info: dict = None, current_event: int = 0):
    event_pattern = re.compile(r"(^#.*?)(?=\n#|\Z)", re.MULTILINE | re.DOTALL)
    events = event_pattern.findall(block_content)
    events_to_keep, newly_created_blocks = [], []

    for event_full_text in events:
        event_tag = event_full_text.strip().split('\n')[0].split(' ')[0]
        if event_tag in STANDARD_EVENTS:
            events_to_keep.append(event_full_text.strip())
            continue
        
        # Mettre à jour le progress
        if progress_info:
            current_event += 1
            progress = current_event / progress_info["total"]
            progress_info["progress_bar"].progress(progress)
            batch_info = f" - {progress_info.get('batch_info', '')}" if progress_info.get('batch_info') else ""
            progress_info["status_text"].text(f"Analyse de l'événement {current_event}/{progress_info['total']}: {event_tag}{batch_info}")
        
        log_messages.append(f"  -> Événement personnalisé trouvé : '{event_tag}'. Analyse via OpenRouter...")
        
        # Vérifier le cache d'abord
        cache_key = f"{event_tag}_{api_config['model_name']}"
        if cache_key in EVENT_ANALYSIS_CACHE:
            log_messages.append(f"    [📋] Résultat trouvé dans le cache")
            llm_result = EVENT_ANALYSIS_CACHE[cache_key]
        else:
            llm_result = analyze_event_with_llm(
                event_tag, 
                api_config["api_key"], 
                api_config["model_name"], 
                api_config["site_url"],
                api_config.get("request_delay", 1.0),
                api_config.get("max_retries", 3)
            )
        
        if llm_result and llm_result.get("is_org"):
            org_name = llm_result["name"]
            org_type = llm_result["type"]
            log_messages.append(f"    [✓] Organisation identifiée : {org_name} (Type: {org_type}). Création du bloc.")
            new_block = create_org_pevt_block(org_name, org_type, person_name, event_full_text)
            newly_created_blocks.append(new_block)
        else:
            error_msg = f" Erreur: {llm_result.get('error')}" if llm_result.get('error') else ""
            log_messages.append(f"    [i] Pas une organisation.{error_msg}")
            events_to_keep.append(event_full_text.strip())

    return "\n".join(events_to_keep), newly_created_blocks, current_event

def process_gw_content_with_control(content: str, api_config: dict):
    """
    Version avec contrôle manuel : traitement bloc par bloc avec possibilité d'arrêt
    """
    log_messages, new_org_blocks = [], []
    pevt_pattern = re.compile(r"^(pevt .*?)\n(.*?)\n^(end pevt)", re.MULTILINE | re.DOTALL)
    matches = list(pevt_pattern.finditer(content))
    
    max_blocks = api_config.get("max_blocks")
    if max_blocks:
        matches = matches[:max_blocks]
        log_messages.append(f"🔢 Limitation activée : traitement des {len(matches)} premiers blocs seulement")
    
    batch_size = api_config.get("batch_size", 5)
    batch_pause = api_config.get("batch_pause", 5.0)
    
    # Diviser les matches en lots
    batches = [matches[i:i + batch_size] for i in range(0, len(matches), batch_size)]
    total_batches = len(batches)
    
    # Compter le nombre total d'événements personnalisés à analyser
    total_custom_events = 0
    for match in matches:
        block_content = match.group(2).strip()
        event_pattern = re.compile(r"(^#.*?)(?=\n#|\Z)", re.MULTILINE | re.DOTALL)
        events = event_pattern.findall(block_content)
        for event_full_text in events:
            event_tag = event_full_text.strip().split('\n')[0].split(' ')[0]
            if event_tag not in STANDARD_EVENTS:
                total_custom_events += 1
    
    # Initialiser current_event dans tous les cas
    current_event = 0
    
    if total_custom_events > 0:
        progress_bar = st.progress(0)
        status_text = st.empty()
        batch_status = st.empty()
        control_container = st.empty()
        
        log_messages.append(f"\n🎛️  Mode contrôlé activé")
        log_messages.append(f"📊 Traitement en {total_batches} lot(s) de {batch_size} bloc(s) maximum")
        log_messages.append(f"⏱️  Pause de {batch_pause}s entre chaque lot")
        log_messages.append(f"🎯 Total: {total_custom_events} événements personnalisés à analyser")
    else:
        # Pas d'événements personnalisés, mais on doit quand même définir les variables
        progress_bar = None
        status_text = None
        batch_status = None
        control_container = None
    
    # Traiter chaque lot
    for batch_index, batch_matches in enumerate(batches):
        current_batch = batch_index + 1
        
        if total_custom_events > 0:
            batch_status.info(f"📦 **Lot {current_batch}/{total_batches}** - Traitement de {len(batch_matches)} bloc(s) pevt...")
            
            # Afficher le bouton d'arrêt
            with control_container.container():
                col1, col2, col3 = st.columns([2, 1, 2])
                with col2:
                    if st.button(f"⏹️ Arrêter après ce lot", key=f"stop_batch_{batch_index}", help="Termine le lot actuel puis s'arrête"):
                        st.session_state.processing_stopped = True
                        st.warning("🛑 Arrêt demandé. Fin du lot en cours...")
        
        log_messages.append(f"\n{'='*50}")
        log_messages.append(f"📦 DÉBUT DU LOT {current_batch}/{total_batches}")
        log_messages.append(f"{'='*50}")
        
        # Traiter chaque match du lot (en ordre inverse pour les modifications de texte)
        for match_index, match in enumerate(reversed(batch_matches)):
            person_header = match.group(1).strip()
            block_content = match.group(2).strip()
            person_name = person_header.replace("pevt ", "").strip()
            
            current_block = len(batch_matches) - match_index
            log_messages.append(f"\nTraitement du bloc 'pevt' {current_block}/{len(batch_matches)} pour : {person_name}")
            
            # Passer les informations de progression
            progress_info = {
                "total": total_custom_events,
                "current": current_event,
                "progress_bar": progress_bar if total_custom_events > 0 else None,
                "status_text": status_text if total_custom_events > 0 else None,
                "batch_info": f"Lot {current_batch}/{total_batches} - Bloc {current_block}/{len(batch_matches)}"
            } if total_custom_events > 0 else None
            
            modified_content, created_blocks, current_event = process_pevt_block_with_progress(
                person_name, block_content, log_messages, api_config, progress_info, current_event
            )
            
            if created_blocks:
                if not modified_content.strip():
                     log_messages.append("  -> Le bloc 'pevt' original est maintenant vide et sera supprimé.")
                     content = content[:match.start()] + content[match.end():]
                else:
                    new_block_str = f"{person_header}\n{modified_content}\nend pevt"
                    content = content[:match.start()] + new_block_str + content[match.end():]
                new_org_blocks.extend(created_blocks)
            
            # Vérifier si l'arrêt a été demandé
            if st.session_state.processing_stopped:
                log_messages.append(f"\n🛑 ARRÊT DEMANDÉ APRÈS LE BLOC {current_block}/{len(batch_matches)}")
                break
        
        log_messages.append(f"\n✅ LOT {current_batch}/{total_batches} TERMINÉ")
        
        # Si arrêt demandé, sortir de la boucle des lots
        if st.session_state.processing_stopped:
            log_messages.append(f"\n🛑 ARRÊT DU TRAITEMENT APRÈS LE LOT {current_batch}/{total_batches}")
            break
        
        # Pause entre les lots (sauf pour le dernier)
        if current_batch < total_batches and batch_pause > 0:
            log_messages.append(f"⏸️  Pause de {batch_pause}s avant le prochain lot...")
            if total_custom_events > 0:
                batch_status.warning(f"⏸️ Pause de {batch_pause}s entre les lots... ({current_batch}/{total_batches} terminés)")
            time.sleep(batch_pause)

    if total_custom_events > 0:
        progress_bar.progress(current_event / total_custom_events if total_custom_events > 0 else 1.0)
        control_container.empty()  # Enlever le bouton d'arrêt
        
        if st.session_state.processing_stopped:
            status_text.warning(f"🛑 Traitement arrêté ! ({current_event}/{total_custom_events} événements traités)")
            batch_status.warning(f"⏹️ Arrêt manuel après {current_event}/{total_custom_events} événements")
        else:
            status_text.success("✅ Analyse terminée!")
            batch_status.success(f"🎉 Tous les lots traités ! ({total_batches}/{total_batches})")
        
        time.sleep(2)  # Afficher le message de fin

    # Sauvegarder les résultats partiels
    st.session_state.partial_results = {
        "content": content.strip(),
        "new_blocks": new_org_blocks,
        "logs": log_messages,
        "stopped": st.session_state.processing_stopped,
        "processed_events": current_event,
        "total_events": total_custom_events
    }

    final_content = content.strip()
    if new_org_blocks:
        final_content += "\n\n# --- Blocs Organisations ajoutés par le script ---\n"
        final_content += "\n".join(new_org_blocks)
    
    return final_content, new_org_blocks, log_messages

# --- INTERFACE UTILISATEUR STREAMLIT ---

st.set_page_config(page_title="Processeur GeneWeb", layout="wide")

# -- SIDEBAR DE CONFIGURATION --
with st.sidebar:
    st.header("⚙️ Configuration OpenRouter")
    st.markdown("Entrez vos informations d'API pour interroger le LLM.")
    
    api_key = st.text_input("Clé API OpenRouter", type="password", help="Votre clé est utilisée pour les appels API et n'est pas stockée.")
    model_name = st.text_input("Modèle LLM", value="openai/gpt-4.1-nano", help="Ex: 'google/gemini-flash-1.5', 'anthropic/claude-3-haiku'")
    site_url = st.text_input("Votre URL de site (HTTP-Referer)", value="http://localhost:8501", help="Recommandé par OpenRouter. Laissez la valeur par défaut si vous exécutez localement.")
    
    st.subheader("🚦 Gestion du Rate Limiting")
    request_delay = st.slider("Délai entre les requêtes (secondes)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, help="Temps d'attente entre chaque requête pour éviter les erreurs 429")
    max_retries = st.number_input("Nombre maximum de tentatives", min_value=1, max_value=10, value=3, help="Nombre de fois qu'une requête sera retentée en cas d'erreur 429")
    
    st.subheader("📦 Traitement par lots")
    st.markdown("*Divise le fichier en petits groupes pour mieux gérer les gros volumes*")
    batch_size = st.number_input("Taille des lots (nombre de blocs pevt)", min_value=1, max_value=50, value=5, help="Nombre de blocs 'pevt' à traiter par lot")
    batch_pause = st.slider("Pause entre les lots (secondes)", min_value=1.0, max_value=30.0, value=5.0, step=1.0, help="Temps d'attente entre chaque lot pour réduire la charge sur l'API")
    
    st.subheader("🎛️ Contrôle avancé")
    limit_blocks = st.checkbox("Limiter le nombre de blocs à traiter", help="Permet de traiter seulement une partie du fichier")
    if limit_blocks:
        max_blocks = st.number_input("Nombre maximum de blocs pevt à traiter", min_value=1, max_value=1000, value=10, help="S'arrête après ce nombre de blocs")
    else:
        max_blocks = None
        
    process_block_by_block = st.checkbox("Mode bloc par bloc", value=True, help="Traite chaque bloc individuellement avec possibilité d'arrêt")
    
    with st.expander("ℹ️ Comment fonctionnent les modes de traitement"):
        st.markdown("""
        **🎛️ Mode bloc par bloc (recommandé) :**
        - Traite chaque bloc `pevt` individuellement
        - Bouton d'arrêt visible pendant le traitement
        - Possibilité de reprendre où vous vous êtes arrêté
        - Sauvegarde automatique des résultats partiels
        
        **📦 Mode par lots classique :**
        - Le fichier `.gw` est divisé en groupes de blocs `pevt`
        - Chaque groupe est traité séquentiellement
        - Une pause est appliquée entre chaque groupe
        - Plus rapide mais moins de contrôle
        
        **🔢 Limitation de blocs :**
        - Permet de traiter seulement une partie du fichier
        - Utile pour tester sur les premiers blocs
        - Économise les appels API
        
        **Recommandations :**
        - **Gros fichiers (>20 blocs)** : mode bloc par bloc, taille 3-5, pause 5-10s
        - **Fichiers moyens** : taille 5-10, pause 3-5s  
        - **Test/découverte** : limitez à 5-10 blocs
        """)
    
    
    # Cache management
    cache_size = len(EVENT_ANALYSIS_CACHE)
    if cache_size > 0:
        st.info(f"📝 Cache: {cache_size} événements analysés")
        if st.button("🗑️ Vider le cache"):
            EVENT_ANALYSIS_CACHE.clear()
            st.success("Cache vidé!")
            st.rerun()
    
    st.markdown("---")
    st.markdown("🔗 Liens utiles")
    st.markdown("[Trouver votre clé API](https://openrouter.ai/keys)")
    st.markdown("[Liste des modèles](https://openrouter.ai/models)")

# -- PAGE PRINCIPALE --
st.title("🤖 Processeur de Fichiers GeneWeb (via LLM)")
st.markdown("Cette application analyse un fichier `.gw`, identifie les événements personnalisés via **OpenRouter** et les transforme en nouvelles entités.")

st.info("""
🆕 **Contrôle total du traitement** :
- ⏰ **Délai configurable** entre les requêtes pour éviter les erreurs 429
- 🔄 **Système de retry automatique** avec backoff exponentiel 
- 📋 **Cache intelligent** : les événements déjà analysés ne sont pas re-traités
- 📊 **Indicateur de progression** en temps réel
- 📦 **Traitement par lots** avec pauses configurables
- 🎛️ **Mode bloc par bloc** : contrôle total avec bouton d'arrêt
- ⏹️ **Arrêt à tout moment** et reprise possible
- 🔢 **Limitation de blocs** pour traitement partiel
""")

uploaded_file = st.file_uploader("1. Choisissez votre fichier GeneWeb (.gw)", type=['gw', 'txt'])

if uploaded_file is not None:
    file_content = uploaded_file.getvalue().decode("utf-8")
    
    # Analyser le fichier pour donner des informations utiles
    pevt_pattern = re.compile(r"^(pevt .*?)\n(.*?)\n^(end pevt)", re.MULTILINE | re.DOTALL)
    pevt_matches = list(pevt_pattern.finditer(file_content))
    total_pevt_blocks = len(pevt_matches)
    
    # Compter les événements personnalisés
    custom_events_count = 0
    for match in pevt_matches:
        block_content = match.group(2).strip()
        event_pattern = re.compile(r"(^#.*?)(?=\n#|\Z)", re.MULTILINE | re.DOTALL)
        events = event_pattern.findall(block_content)
        for event_full_text in events:
            event_tag = event_full_text.strip().split('\n')[0].split(' ')[0]
            if event_tag not in STANDARD_EVENTS:
                custom_events_count += 1
    
    st.success(f"✅ Fichier téléversé avec succès ! **{total_pevt_blocks} blocs pevt** détectés, dont **{custom_events_count} événements personnalisés** à analyser.")
    
    if total_pevt_blocks > 0:
        recommended_batch_size = min(5, max(1, total_pevt_blocks // 4))
        recommended_pause = 3.0 if total_pevt_blocks <= 10 else 5.0 if total_pevt_blocks <= 30 else 8.0
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"💡 **Recommandation** : Taille de lot = {recommended_batch_size}, Pause = {recommended_pause}s")
        with col2:
            if custom_events_count > 0:
                estimated_time = (custom_events_count * 3) + (total_pevt_blocks // recommended_batch_size * recommended_pause)
                minutes = int(estimated_time // 60)
                seconds = int(estimated_time % 60)
                st.info(f"⏱️ **Temps estimé** : ~{minutes}m{seconds:02d}s")
    
    # Afficher les résultats partiels précédents s'il y en a
    if hasattr(st.session_state, 'partial_results') and st.session_state.partial_results:
        with st.expander("📋 Résultats partiels précédents"):
            partial = st.session_state.partial_results
            st.success(f"Dernière session : **{partial['processed_events']}/{partial['total_events']} événements** traités, **{len(partial['new_blocks'])} organisations** créées")
            if st.button("🗑️ Effacer les résultats précédents"):
                st.session_state.partial_results = None
                st.rerun()

    if st.button("🚀 Lancer l'analyse et la transformation"):
        if not api_key:
            st.error("❌ Veuillez entrer votre clé API OpenRouter dans le panneau de gauche.")
            st.stop()

        api_config = {
            "api_key": api_key, 
            "model_name": model_name, 
            "site_url": site_url,
            "request_delay": request_delay,
            "max_retries": int(max_retries),
            "batch_size": int(batch_size),
            "batch_pause": batch_pause,
            "max_blocks": max_blocks,
            "process_block_by_block": process_block_by_block
        }
        
        # Initialiser les états de session
        if 'processing_stopped' not in st.session_state:
            st.session_state.processing_stopped = False
        if 'partial_results' not in st.session_state:
            st.session_state.partial_results = None
        
        # Réinitialiser l'état d'arrêt
        st.session_state.processing_stopped = False
        
        if process_block_by_block:
            final_content, new_blocks, logs = process_gw_content_with_control(file_content, api_config)
        else:
            with st.spinner('Analyse en cours... Communication avec le LLM via OpenRouter...'):
                final_content, new_blocks, logs = process_gw_content(file_content, api_config)
        
        # Affichage des résultats (complets ou partiels)
        if st.session_state.processing_stopped:
            st.header("⏹️ Traitement arrêté - Résultats partiels")
            partial = st.session_state.partial_results
            st.warning(f"🛑 Traitement interrompu ! **{partial['processed_events']}/{partial['total_events']} événements** ont été analysés.")
        else:
            st.header("✅ Analyse terminée")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"{len(new_blocks)} nouvelles organisations à créer")
            if not new_blocks:
                st.info("Aucun événement personnalisé correspondant à une organisation n'a été identifié par le LLM.")
            else:
                st.code("\n\n".join(new_blocks), language="plaintext")
        with col2:
            st.subheader("Journal des opérations")
            st.text_area("Logs", "".join(log.replace("  ", "  - ").replace("\n", "\n- ") for log in logs), height=300, key="logs_area")

        # Options de téléchargement adaptées selon l'état
        if st.session_state.processing_stopped:
            st.header("3. Téléchargez vos résultats partiels")
            st.info("💾 Même si le traitement a été arrêté, vous pouvez télécharger les modifications déjà effectuées.")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"partial_{uploaded_file.name.replace('.gw', '')}_{timestamp}.gw"
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                   label="📥 Télécharger les résultats partiels",
                   data=final_content.encode('utf-8'),
                   file_name=output_filename,
                   mime='text/plain',
                )
            with col2:
                if st.button("🔄 Reprendre le traitement", help="Reprend là où vous vous êtes arrêté"):
                    st.session_state.processing_stopped = False
                    st.rerun()
        else:
            st.header("3. Téléchargez votre fichier transformé")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"processed_{uploaded_file.name.replace('.gw', '')}_{timestamp}.gw"
            st.download_button(
               label="📥 Télécharger le fichier .gw modifié",
               data=final_content.encode('utf-8'),
               file_name=output_filename,
               mime='text/plain',
            )