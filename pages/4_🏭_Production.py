import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    init_database,
    ajouter_production,
    obtenir_toute_production,
    modifier_production,
    supprimer_production
)

# Configuration de la page
st.set_page_config(
    page_title="Production - Audit Énergétique",
    page_icon="🏭",
    layout="wide"
)

# Initialiser la base de données
init_database()

# Variables de session pour l'édition
if 'prod_mode_edition' not in st.session_state:
    st.session_state.prod_mode_edition = False
if 'prod_edition' not in st.session_state:
    st.session_state.prod_edition = None

# CSS personnalisé
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🏭 Gestion de la Production</h1>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["➕ Ajouter Production", "📋 Liste & Graphiques", "✏️ Modifier/Supprimer"])

# ========== ONGLET 1: AJOUTER ==========
with tab1:
    st.markdown('<h2 class="section-header">Nouvelle Entrée de Production</h2>', unsafe_allow_html=True)
    
    with st.form("form_production", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date_prod = st.date_input("Date de production *", value=datetime.now().date())
            scope_type = st.selectbox("Type de Scope *", ["Global", "Ligne", "Produit"])
        
        with col2:
            unite = st.selectbox("Unité de mesure *", ["T (Tonnes)", "kg", "L (Litres)", "m3", "Pièces/Unités"])
            scope_value = st.text_input("Nom du Scope *", placeholder="Ex: Ligne 1, Lait 1L, Usine A...")
            
        quantite = st.number_input("Quantité produite *", min_value=0.0, step=0.1, format="%.2f")
        
        submitted = st.form_submit_button("💾 Enregistrer", use_container_width=True)
        
        if submitted:
            if date_prod and unite and scope_type and scope_value and quantite is not None:
                success = ajouter_production(
                    date_prod.strftime("%Y-%m-%d"),
                    unite,
                    scope_type,
                    scope_value,
                    quantite
                )
                if success:
                    st.success("✅ Production enregistrée avec succès!")
                else:
                    st.error("❌ Erreur lors de l'enregistrement.")
            else:
                st.error("❌ Veuillez remplir tous les champs.")

# ========== ONGLET 2: LISTE & GRAPHIQUES ==========
with tab2:
    st.markdown('<h2 class="section-header">Historique de Production</h2>', unsafe_allow_html=True)
    
    data = obtenir_toute_production()
    
    if data:
        df = pd.DataFrame(data)
        
        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtre_scope = st.multiselect("Filtrer par Type", options=df['scope_type'].unique())
        with col_f2:
            filtre_nom = st.multiselect("Filtrer par Nom", options=df['scope_value'].unique())
        with col_f3:
            filtre_unite = st.multiselect("Filtrer par Unité", options=df['unite_mesure'].unique())
            
        # Appliquer filtres
        df_filtered = df.copy()
        if filtre_scope:
            df_filtered = df_filtered[df_filtered['scope_type'].isin(filtre_scope)]
        if filtre_nom:
            df_filtered = df_filtered[df_filtered['scope_value'].isin(filtre_nom)]
        if filtre_unite:
            df_filtered = df_filtered[df_filtered['unite_mesure'].isin(filtre_unite)]
            
        st.dataframe(df_filtered, use_container_width=True)
        
        st.markdown("---")
        st.markdown('<h3 class="section-header">📈 Analyse Graphique</h3>', unsafe_allow_html=True)
        
        # Graphique
        if not df_filtered.empty:
            type_graph = st.selectbox("Type de visualisation", ["Évolution Temporelle (Ligne)", "Comparaison (Barres)"])
            
            chart_data = df_filtered.copy()
            chart_data['date_production'] = pd.to_datetime(chart_data['date_production'])
            chart_data = chart_data.sort_values('date_production')
            
            if type_graph == "Évolution Temporelle (Ligne)":
                st.line_chart(chart_data, x='date_production', y='quantite', color='scope_value')
            else:
                st.bar_chart(chart_data, x='scope_value', y='quantite', color='scope_type')
                
            # Export
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Télécharger les données filtrées (CSV)",
                data=csv,
                file_name="production_export.csv",
                mime="text/csv"
            )
    else:
        st.info("Aucune donnée de production.")

# ========== ONGLET 3: MODIFIER/SUPPRIMER ==========
with tab3:
    st.markdown('<h2 class="section-header">Modifier ou Supprimer</h2>', unsafe_allow_html=True)
    
    data = obtenir_toute_production()
    
    if data:
        # Sélection
        options = {f"{r['date_production']} - {r['scope_value']} ({r['quantite']} {r['unite_mesure']})": r for r in data}
        selection = st.selectbox("Sélectionnez une entrée", options=list(options.keys()))
        
        if selection:
            entry = options[selection]
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("✏️ Modifier cette entrée", use_container_width=True):
                    st.session_state.prod_mode_edition = True
                    st.session_state.prod_edition = entry
                    st.rerun()
            with col_act2:
                if st.button("🗑️ Supprimer cette entrée", use_container_width=True, type="primary"):
                    if supprimer_production(entry['id']):
                        st.success("Entrée supprimée.")
                        st.rerun()
            
            # Formulaire d'édition
            if st.session_state.prod_mode_edition and st.session_state.prod_edition:
                st.markdown("---")
                st.info(f"Modification de l'entrée : {selection}")
                
                with st.form("form_modif_prod"):
                    col_m1, col_m2 = st.columns(2)
                    
                    e = st.session_state.prod_edition
                    
                    with col_m1:
                        d_val = datetime.strptime(e['date_production'], "%Y-%m-%d").date()
                        new_date = st.date_input("Date", value=d_val)
                        new_type = st.selectbox("Type", ["Global", "Ligne", "Produit"], index=["Global", "Ligne", "Produit"].index(e['scope_type']))
                    
                    with col_m2:
                        new_unite = st.selectbox("Unité", ["T (Tonnes)", "kg", "L (Litres)", "m3", "Pièces/Unités"], index=["T (Tonnes)", "kg", "L (Litres)", "m3", "Pièces/Unités"].index(e['unite_mesure']))
                        new_name = st.text_input("Nom", value=e['scope_value'])
                        
                    new_q = st.number_input("Quantité", value=float(e['quantite']), step=0.1)
                    
                    col_sav, col_can = st.columns(2)
                    with col_sav:
                        if st.form_submit_button("💾 Sauvegarder"):
                            if modifier_production(e['id'], new_date.strftime("%Y-%m-%d"), new_unite, new_type, new_name, new_q):
                                st.success("Modifié avec succès!")
                                st.session_state.prod_mode_edition = False
                                st.rerun()
                            else:
                                st.error("Erreur à la modification.")
                                
                    with col_can:
                        if st.form_submit_button("❌ Annuler"):
                            st.session_state.prod_mode_edition = False
                            st.rerun()
