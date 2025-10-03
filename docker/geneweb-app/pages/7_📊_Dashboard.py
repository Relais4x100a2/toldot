"""
Page 7: Dashboard et statistiques globales
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import init_session_state, calculate_metrics

init_session_state()

st.title("📊 Dashboard Global")

st.markdown("""
### Vue d'ensemble de votre projet

Statistiques complètes sur l'annotation, l'optimisation et la transformation.
""")

# Métriques principales
st.markdown("## 📈 Métriques Principales")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "PEVT Total",
        len(st.session_state.all_pevts),
        help="Nombre total de PEVT personnalisés extraits"
    )

with col2:
    st.metric(
        "Annotations",
        len(st.session_state.annotations),
        help="Exemples annotés manuellement"
    )

with col3:
    st.metric(
        "Validations",
        len(st.session_state.validations),
        help="Transformations validées"
    )

with col4:
    st.metric(
        "Transformés",
        len(st.session_state.mass_transformation_results),
        help="PEVT transformés automatiquement"
    )

with col5:
    progress_pct = (len(st.session_state.mass_transformation_results) / 
                   len(st.session_state.all_pevts) * 100 
                   if st.session_state.all_pevts else 0)
    st.metric(
        "Progression",
        f"{progress_pct:.0f}%",
        help="Pourcentage de PEVT traités"
    )

# Statistiques détaillées
st.markdown("---")
st.markdown("## 📊 Statistiques Détaillées")

tab1, tab2, tab3, tab4 = st.tabs(["📥 Extraction", "✏️ Annotation", "✅ Validation", "🚀 Transformation"])

with tab1:
    st.subheader("Statistiques d'extraction")
    
    if st.session_state.pevt_stats:
        stats = st.session_state.pevt_stats
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Types uniques", stats['unique_event_types'])
            st.metric("Avec date", stats['with_date'])
        
        with col2:
            st.metric("Avec lieu", stats['with_place'])
            st.metric("Avec témoins", stats['with_witnesses'])
        
        with col3:
            st.metric("Avec notes", stats['with_notes'])
            st.metric("Avec sources", stats.get('with_sources', 0))
        
        # Distribution des types
        st.markdown("### Distribution des types d'événements")
        
        dist_data = stats['event_type_distribution']
        df = pd.DataFrame(
            list(dist_data.items()),
            columns=['Type', 'Count']
        ).sort_values('Count', ascending=False)
        
        fig = px.bar(
            df.head(20),
            x='Type',
            y='Count',
            title='Top 20 des types d\'événements',
            color='Count',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Aucune donnée d'extraction disponible")

with tab2:
    st.subheader("Statistiques d'annotation")
    
    if st.session_state.annotations:
        annotations = st.session_state.annotations
        
        # Temps d'annotation
        avg_time = sum(a.annotation_time for a in annotations) / len(annotations)
        total_time = sum(a.annotation_time for a in annotations)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total annotations", len(annotations))
        
        with col2:
            st.metric("Temps moyen", f"{avg_time:.1f}s")
        
        with col3:
            st.metric("Temps total", f"{total_time/60:.1f}min")
        
        # Distribution par type
        type_counts = {}
        for ann in annotations:
            t = ann.pevt_cleaned.event_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        df_ann = pd.DataFrame(
            list(type_counts.items()),
            columns=['Type', 'Count']
        ).sort_values('Count', ascending=False)
        
        fig = px.pie(
            df_ann,
            values='Count',
            names='Type',
            title='Répartition des types d\'événements annotés'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Score de confiance
        conf_scores = [a.pevt_cleaned.confidence_score for a in annotations]
        
        fig_conf = go.Figure(data=[go.Histogram(x=conf_scores, nbinsx=10)])
        fig_conf.update_layout(
            title='Distribution des scores de confiance',
            xaxis_title='Score de confiance',
            yaxis_title='Nombre d\'annotations'
        )
        st.plotly_chart(fig_conf, use_container_width=True)
    
    else:
        st.info("Aucune annotation disponible")

with tab3:
    st.subheader("Statistiques de validation")
    
    if st.session_state.validations:
        metrics = calculate_metrics(st.session_state.validations)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total validations", metrics['total'])
        
        with col2:
            st.metric("Corrects", metrics['correct'], delta=f"+{metrics['accuracy']:.0%}")
        
        with col3:
            st.metric("Incorrects", metrics['incorrect'])
        
        with col4:
            st.metric("Accuracy", f"{metrics['accuracy']:.1%}")
        
        # Graphique de progression
        correct_per_validation = []
        total_correct = 0
        total_count = 0
        
        for val in st.session_state.validations:
            total_count += 1
            if val.is_correct:
                total_correct += 1
            correct_per_validation.append(total_correct / total_count)
        
        fig_progress = go.Figure()
        fig_progress.add_trace(go.Scatter(
            y=correct_per_validation,
            mode='lines+markers',
            name='Accuracy',
            line=dict(color='green', width=2)
        ))
        fig_progress.update_layout(
            title='Évolution de l\'accuracy au fil des validations',
            xaxis_title='Numéro de validation',
            yaxis_title='Accuracy',
            yaxis_range=[0, 1]
        )
        st.plotly_chart(fig_progress, use_container_width=True)
        
        # Types d'erreurs
        all_errors = []
        for val in st.session_state.validations:
            all_errors.extend(val.errors)
        
        if all_errors:
            from collections import Counter
            error_counts = Counter(all_errors)
            
            df_errors = pd.DataFrame(
                list(error_counts.items()),
                columns=['Type d\'erreur', 'Count']
            ).sort_values('Count', ascending=False)
            
            fig_errors = px.bar(
                df_errors,
                x='Type d\'erreur',
                y='Count',
                title='Types d\'erreurs détectées'
            )
            st.plotly_chart(fig_errors, use_container_width=True)
    
    else:
        st.info("Aucune validation disponible")

with tab4:
    st.subheader("Statistiques de transformation de masse")
    
    if st.session_state.mass_transformation_results:
        results = st.session_state.mass_transformation_results
        
        total = len(results)
        needs_review = sum(1 for r in results if r['needs_review'])
        high_conf = sum(1 for r in results if r['confidence_score'] >= 0.8)
        avg_conf = sum(r['confidence_score'] for r in results) / total
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total transformé", total)
        
        with col2:
            st.metric("Haute confiance", high_conf, delta=f"{high_conf/total*100:.0f}%")
        
        with col3:
            st.metric("À réviser", needs_review, delta=f"{needs_review/total*100:.0f}%")
        
        with col4:
            st.metric("Confiance moy.", f"{avg_conf:.0%}")
        
        # Distribution de confiance
        conf_ranges = {
            '90-100%': 0,
            '80-90%': 0,
            '70-80%': 0,
            '60-70%': 0,
            '<60%': 0
        }
        
        for r in results:
            conf = r['confidence_score']
            if conf >= 0.9:
                conf_ranges['90-100%'] += 1
            elif conf >= 0.8:
                conf_ranges['80-90%'] += 1
            elif conf >= 0.7:
                conf_ranges['70-80%'] += 1
            elif conf >= 0.6:
                conf_ranges['60-70%'] += 1
            else:
                conf_ranges['<60%'] += 1
        
        fig_conf_dist = px.bar(
            x=list(conf_ranges.keys()),
            y=list(conf_ranges.values()),
            title='Distribution des scores de confiance',
            labels={'x': 'Plage de confiance', 'y': 'Nombre'},
            color=list(conf_ranges.values()),
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_conf_dist, use_container_width=True)
        
        # Types d'événements transformés
        event_types = {}
        for r in results:
            t = r['event_type']
            event_types[t] = event_types.get(t, 0) + 1
        
        df_types = pd.DataFrame(
            list(event_types.items()),
            columns=['Type', 'Count']
        ).sort_values('Count', ascending=False)
        
        fig_types = px.pie(
            df_types,
            values='Count',
            names='Type',
            title='Répartition des types d\'événements transformés'
        )
        st.plotly_chart(fig_types, use_container_width=True)
    
    else:
        st.info("Aucune transformation de masse effectuée")

# Historique du projet
st.markdown("---")
st.markdown("## 📜 Historique du Projet")

if st.session_state.prompt_history:
    st.subheader("Versions de prompts")
    
    for prompt in reversed(st.session_state.prompt_history):
        with st.expander(f"Version {prompt.version} - {prompt.created_at[:19]}"):
            st.write(f"**Exemples:** {prompt.examples_count}")
            st.write(f"**Notes:** {prompt.notes}")
            if prompt.accuracy > 0:
                st.write(f"**Accuracy:** {prompt.accuracy:.1%}")

# Export complet du projet
st.markdown("---")
st.markdown("## 💾 Export Complet")

if st.button("📦 Générer un export complet du projet"):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_data = {
        'project_info': {
            'export_date': datetime.now().isoformat(),
            'total_pevts': len(st.session_state.all_pevts),
            'annotations_count': len(st.session_state.annotations),
            'validations_count': len(st.session_state.validations),
            'transformations_count': len(st.session_state.mass_transformation_results),
        },
        'stats': st.session_state.pevt_stats,
        'prompt_history': [
            {
                'version': p.version,
                'prompt_text': p.prompt_text,
                'examples_count': p.examples_count,
                'created_at': p.created_at,
                'notes': p.notes
            }
            for p in st.session_state.prompt_history
        ],
        'validation_metrics': calculate_metrics(st.session_state.validations) if st.session_state.validations else {}
    }
    
    export_path = f"/opt/geneweb/data/training/project_export_{timestamp}.json"
    
    import json
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    st.success(f"✅ Export complet sauvegardé: {export_path}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🌳 GeneWeb AI Processor - Propulsé par DSPY et Streamlit</p>
    <p>Développé avec ❤️ pour la généalogie</p>
</div>
""", unsafe_allow_html=True)
```

```

