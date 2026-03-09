import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    init_database,
    ajouter_facture_electricite,
    obtenir_toutes_factures_electricite,
    obtenir_facture_electricite,
    modifier_facture_electricite,
    supprimer_facture_electricite,
    obtenir_toute_production
)

# ML Imports pour la Prédiction
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
# Imports pour l'OCR (Google GenAI)
HAS_OCR_LIBS = False


# Configuration de la page
st.set_page_config(
    page_title="Électricité - Audit Énergétique",
    page_icon="⚡",
    layout="wide"
)

# Initialiser la base de données
init_database()

# CSS personnalisé pour un design moderne
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
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .success-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Helper: Afficher le rapport détaillé (utilisé dans Tab 3 et Tab 4)
def afficher_calculs_detailles(facture):
    st.markdown("---")
    with st.expander("🧾 Rapport de Calcul Détaillé (Simulation & Explications)", expanded=True):
        st.info("Ce rapport détaille les calculs effectués pour aboutir au montant final, étape par étape.")
        
        # 1. Récupération des données (avec valeurs par défaut saines)
        c_j = float(facture.get('consommation_jour') or 0)
        c_pe = float(facture.get('consommation_pointe_ete') or 0)
        c_n = float(facture.get('consommation_nuit') or 0)
        c_ph = float(facture.get('consommation_pointe_hiver') or 0)
        
        p_j = float(facture.get('puissance_souscrite_jour') or 0)
        p_pe = float(facture.get('puissance_souscrite_pointe_ete') or 0)
        p_n = float(facture.get('puissance_souscrite_nuit') or 0)
        p_ph = float(facture.get('puissance_souscrite_pointe_hiver') or 0)
        
        pm_j = float(facture.get('puissance_appelee_max_jour') or 0)
        pm_pe = float(facture.get('puissance_appelee_max_pointe_ete') or 0)
        pm_n = float(facture.get('puissance_appelee_max_nuit') or 0)
        pm_ph = float(facture.get('puissance_appelee_max_pointe_hiver') or 0)
        
        # Tarifs par défaut si non fournis
        t_j = float(facture.get('tarif_jour') or 0.200)
        t_pe = float(facture.get('tarif_pointe_ete') or 0.350)
        t_n = float(facture.get('tarif_nuit') or 0.150)
        t_ph = float(facture.get('tarif_pointe_hiver') or 0.250)
        
        cos_phi_val = float(facture.get('cos_phi') or 0.9)
        avance_val = float(facture.get('avance') or 0.0)

        # 2. Coût Consommation (HT)
        cout_conso = (c_j * t_j) + (c_pe * t_pe) + (c_n * t_n) + (c_ph * t_ph)
        st.markdown(f"**1. Coût Consommation Energy (Millimes -> DT):**")
        st.code(f"Jour: {c_j} * {t_j:.3f} = {c_j * t_j:.3f}\n"
                f"Pte Été: {c_pe} * {t_pe:.3f} = {c_pe * t_pe:.3f}\n"
                f"Nuit: {c_n} * {t_n:.3f} = {c_n * t_n:.3f}\n"
                f"Pte Hiver: {c_ph} * {t_ph:.3f} = {c_ph * t_ph:.3f}\n"
                f"--- Total: {cout_conso:.3f} DT")

        # 3. Puissance Réduite (PR)
        pr = 0.4*p_ph + 0.3*p_pe + 0.2*p_j + 0.1*p_n
        st.markdown(f"**2. Puissance Réduite (PR):**")
        st.latex(r'''P_r = 0.4 \times P_{hiv} + 0.3 \times P_{ete} + 0.2 \times P_{jour} + 0.1 \times P_{nuit}''')
        st.code(f"PR = 0.4*{p_ph} + 0.3*{p_pe} + 0.2*{p_j} + 0.1*{p_n} = {pr:.3f} kW")
        
        # 4. Prime de Puissance
        prime = pr * 11
        st.markdown(f"**3. Prime de Puissance Fixe:**")
        st.code(f"Prime = PR * 11 DT = {pr:.3f} * 11 = {prime:.3f} DT")
        
        # 5. Pénalité Dépassement
        st.markdown(f"**4. Pénalité de Dépassement:**")
        exceeds = (pm_n > pm_j) or (pm_pe > pm_j) or (pm_ph > pm_j)
        penalite = 0.0
        if exceeds:
             p_max_critique = max(pm_n, pm_pe, pm_ph)
             penalite = (p_max_critique - pr) * 11 * 12 / 3.3333
             st.warning(f"⚠️ Dépassement détecté par rapport à Jour ({pm_j}) ! Max Critique: {p_max_critique}")
             st.code(f"Pénalité = ({p_max_critique} - {pr:.3f}) * 11 * 12 / 3.3333 = {penalite:.3f} DT")
        else:
            diff_h = max(0, pm_ph - p_ph)
            diff_e = max(0, pm_pe - p_pe)
            diff_j = max(0, pm_j - p_j)
            diff_n = max(0, pm_n - p_n)
            
            if diff_h > 0 or diff_e > 0 or diff_j > 0 or diff_n > 0:
                pr2 = 0.4 * max(pm_ph, p_ph) + 0.3 * max(pm_pe, p_pe) + 0.2 * max(pm_j, p_j) + 0.1 * max(pm_n, p_n)
                diff_pr = pr2 - pr
                if diff_pr > 0:
                    penalite = diff_pr * 11 * 12 / 3.3333
                    st.write("Détail calcul PR2 (Puissance Réduite Théorique):")
                    st.code(f"PR2 = 0.4*max({pm_ph},{p_ph}) \n"
                            f"    + 0.3*max({pm_pe},{p_pe}) \n"
                            f"    + 0.2*max({pm_j},{p_j}) \n"
                            f"    + 0.1*max({pm_n},{p_n})")
                    st.code(f"PR2 = {pr2:.3f} kW\n"
                            f"PR  = {pr:.3f} kW\n"
                            f"Diff = {diff_pr:.3f}\n"
                            f"Pénalité = {diff_pr:.3f} * (132/3.3333) = {penalite:.3f} DT")
                else:
                    st.write("Pas de pénalité (PR2 <= PR).")
            else:
                st.write("✅ Aucun dépassement de puissance souscrite.")

        # 6. Impact Cos Phi
        st.markdown(f"**5. Impact Cos Phi (Bonus/Malus):**")
        impact_cos = 0.0
        
        if cos_phi_val > 0.9:
             # Bonus: (0.5 * cos - 0.45) * Montant
             bonus_rate = (0.5 * cos_phi_val - 0.45)
             impact_cos = cout_conso * bonus_rate
             st.success(f"✅ Bon Cos Phi ({cos_phi_val}) -> Bonus de {bonus_rate*100:.2f}%")
             st.code(f"Bonus = {cout_conso:.3f} * (0.5 * {cos_phi_val} - 0.45) = {impact_cos:.3f} DT")
        elif cos_phi_val < 0.8:
             k = 0.0
             if cos_phi_val >= 0.7:
                 diff = 0.8 - cos_phi_val
                 k = (diff * 100) * 2
             else:
                 k = (10) * 2 + (0.7 - cos_phi_val) * 100 * 3
             
             impact_cos = - (cout_conso * (k/100.0))
             st.error(f"⚠️ Mauvais Cos Phi ({cos_phi_val}) -> Malus de {k:.2f}%")
             st.code(f"Malus = - {cout_conso:.3f} * {k/100:.4f} = {impact_cos:.3f} DT")
        else:
             st.write("Zone neutre (0.8 - 0.9). Pas de bonus ni malus.")
        
        # 7. Total HT
        montant_ht = cout_conso + prime + penalite - impact_cos
        st.markdown(f"**6. Montant HT:**")
        st.code(f"HT = Conso ({cout_conso:.3f}) \n"
                f"   + Prime ({prime:.3f}) \n"
                f"   + Pénalité ({penalite:.3f}) \n"
                f"   - Impact Cos ({impact_cos:.3f})\n"
                f"   = {montant_ht:.3f} DT")
        
        # 8. Taxes
        taux_tva = 19.0
        tva_conso = cout_conso * (taux_tva/100)
        tva_red = (prime + penalite) * (taux_tva/100)
        # TVA sur l'impact Cos Phi (Bonus réduit la TVA, Malus l'augmente)
        tva_cos_phi = - impact_cos * (taux_tva/100)
        
        total_energy = c_j + c_pe + c_n + c_ph
        taxe_mun = total_energy * 0.01 # 10 millimes / kWh (Modifié sur demande utilisateur)
        redevance_fte = 3.500 # Redevance Fixe (FTE)
        
        st.markdown(f"**7. Taxes:**")
        st.code(f"TVA Conso (19%): {tva_conso:.3f} DT\n"
                f"TVA Redevance (19%): {tva_red:.3f} DT\n"
                f"TVA / Bonus-Malus (19%): {tva_cos_phi:.3f} DT\n"
                f"Taxe Municipale (0.01 * {total_energy}): {taxe_mun:.3f} DT\n"
                f"FTE (Fixe): {redevance_fte:.3f} DT")
        
        # 9. Total TTC
        ttc = montant_ht + tva_conso + tva_red + tva_cos_phi + taxe_mun + redevance_fte - avance_val
        st.markdown(f"**8. Montant Total (TTC):**")
        st.code(f"TTC = HT ({montant_ht:.3f}) \n"
                f"      + TVA Conso ({tva_conso:.3f}) \n"
                f"      + TVA Redevance ({tva_red:.3f}) \n"
                f"      + TVA Bonus/Malus ({tva_cos_phi:.3f}) \n"
                f"      + Taxe Mun ({taxe_mun:.3f}) \n"
                f"      + FTE ({redevance_fte:.3f}) \n"
                f"      - Avance ({avance_val:.3f}) \n"
                f"      = {ttc:.3f} DT")

# Titre principal
st.markdown('<h1 class="main-title">⚡ Gestion des Factures d\'Électricité</h1>', unsafe_allow_html=True)

# Initialiser les variables de session
if 'mode_edition' not in st.session_state:
    st.session_state.mode_edition = False
if 'facture_edition' not in st.session_state:
    st.session_state.facture_edition = None

# Onglets pour organiser l'interface
tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Ajouter une facture", "📋 Liste des factures", "✏️ Modifier/Supprimer", "🔄 Simulation", "📈 Prédiction"])

# ========== ONGLET 1: AJOUTER UNE FACTURE ==========
with tab1:
    st.markdown('<h2 class="section-header">Nouvelle Facture d\'Électricité</h2>', unsafe_allow_html=True)
    
    # --- Section OCR (Placée avant le formulaire) ---
    # --- Section OCR (Désétactivée) ---
    if 'ocr_data' not in st.session_state:
        st.session_state.ocr_data = {}

    def get_ocr_val(key, default):
        return default


    with st.form("formulaire_ajout_facture", clear_on_submit=True):
        col1, col2 = st.columns(2)
        

            

        
        with col1:
            numero_facture = st.text_input("Numéro de facture *", placeholder="Ex: FACT-2024-001", value=get_ocr_val("numero_facture", ""))
            date_val = datetime.now().date()
            if 'ocr_data' in st.session_state and st.session_state.ocr_data.get("date_facture"):
                try:
                     date_val = datetime.strptime(st.session_state.ocr_data.get("date_facture"), "%Y-%m-%d").date()
                except:
                     pass
            date_facture = st.date_input("Date de la facture *", value=date_val)
        
        with col2:
            cos_phi = st.number_input("Cos Phi (Facteur de puissance) *", min_value=0.0, max_value=1.0, step=0.01, format="%.2f", value=float(get_ocr_val("cos_phi", 0.9)))
            puissance_reactive = st.number_input("Puissance réactive (kVAR) *", min_value=0.0, step=0.1, format="%.2f", key="puissance_reactive", value=float(get_ocr_val("puissance_reactive", 0.0)))
            facture_rectificative = st.checkbox("📝 Facture rectificative", value=False)
        
        st.markdown("### 💰 Tarification (Millimes/kWh ou DT)")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            tarif_jour = st.number_input("Tarif Jour", min_value=0.0, step=0.001, format="%.3f", key="t_jour")
        with col_t2:
            tarif_pointe_ete = st.number_input("Tarif Pointe Été", min_value=0.0, step=0.001, format="%.3f", key="t_p_ete")
        with col_t3:
            tarif_nuit = st.number_input("Tarif Nuit", min_value=0.0, step=0.001, format="%.3f", key="t_nuit")
        with col_t4:
            tarif_pointe_hiver = st.number_input("Tarif Pointe Hiver", min_value=0.0, step=0.001, format="%.3f", key="t_p_hiver")
        
        st.markdown("### Consommation par phase (kWh)")
        col_p1, col_p2, col_p3 = st.columns(3)
        
        with col_p1:
            consommation_phase1 = st.number_input("Phase 1 (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="p1", value=float(get_ocr_val("consommation_phase1", 0.0)))
        with col_p2:
            consommation_phase2 = st.number_input("Phase 2 (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="p2", value=float(get_ocr_val("consommation_phase2", 0.0)))
        with col_p3:
            consommation_phase3 = st.number_input("Phase 3 (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="p3", value=float(get_ocr_val("consommation_phase3", 0.0)))
        
        st.markdown("### Consommation totale par tranche horaire (kWh)")
        col_cons_j, col_cons_pe, col_cons_n, col_cons_ph = st.columns(4)
        
        with col_cons_j:
            consommation_jour = st.number_input("Jour total (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="cons_jour", value=float(get_ocr_val("consommation_jour", 0.0)))
        with col_cons_pe:
            consommation_pointe_ete = st.number_input("Pointe été total (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="cons_pointe_ete", value=float(get_ocr_val("consommation_pointe_ete", 0.0)))
        with col_cons_n:
            consommation_nuit = st.number_input("Nuit total (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="cons_nuit", value=float(get_ocr_val("consommation_nuit", 0.0)))
        with col_cons_ph:
            consommation_pointe_hiver = st.number_input("Pointe hiver total (kWh) *", min_value=0.0, step=0.1, format="%.2f", key="cons_pointe_hiver", value=float(get_ocr_val("consommation_pointe_hiver", 0.0)))
        
        st.markdown("### Puissance souscrite par période (kW)")
        col6, col7, col8, col9 = st.columns(4)
        
        with col6:
            puissance_souscrite_jour = st.number_input("Jour (kW) *", min_value=0.0, step=0.1, format="%.2f", key="ps_jour", value=float(get_ocr_val("puissance_souscrite_jour", 0.0)))
        with col7:
            puissance_souscrite_pointe_ete = st.number_input("Pointe été (kW) *", min_value=0.0, step=0.1, format="%.2f", key="ps_pointe_ete", value=float(get_ocr_val("puissance_souscrite_pointe_ete", 0.0)))
        with col8:
            puissance_souscrite_nuit = st.number_input("Nuit (kW) *", min_value=0.0, step=0.1, format="%.2f", key="ps_nuit", value=float(get_ocr_val("puissance_souscrite_nuit", 0.0)))
        with col9:
            puissance_souscrite_pointe_hiver = st.number_input("Pointe hiver (kW) *", min_value=0.0, step=0.1, format="%.2f", key="ps_pointe_hiver", value=float(get_ocr_val("puissance_souscrite_pointe_hiver", 0.0)))
        
        st.markdown("### Puissance appelée max par période (kW)")
        col10, col11, col12, col13 = st.columns(4)
        
        with col10:
            puissance_appelee_max_jour = st.number_input("Jour max (kW) *", min_value=0.0, step=0.1, format="%.2f", key="pa_jour", value=float(get_ocr_val("puissance_appelee_max_jour", 0.0)))
        with col11:
            puissance_appelee_max_pointe_ete = st.number_input("Pointe été max (kW) *", min_value=0.0, step=0.1, format="%.2f", key="pa_pointe_ete", value=float(get_ocr_val("puissance_appelee_max_pointe_ete", 0.0)))
        with col12:
            puissance_appelee_max_nuit = st.number_input("Nuit max (kW) *", min_value=0.0, step=0.1, format="%.2f", key="pa_nuit", value=float(get_ocr_val("puissance_appelee_max_nuit", 0.0)))
        with col13:
            puissance_appelee_max_pointe_hiver = st.number_input("Pointe hiver max (kW) *", min_value=0.0, step=0.1, format="%.2f", key="pa_pointe_hiver", value=float(get_ocr_val("puissance_appelee_max_pointe_hiver", 0.0)))
        
        st.markdown("### Avance (Optionnel)")
        avance = st.number_input("Avance (DT)", min_value=0.0, step=1.0, format="%.3f", key="avance_add")

        submitted = st.form_submit_button("💾 Enregistrer la facture", use_container_width=True)
        
        if submitted:
            if (numero_facture and date_facture and 
                consommation_phase1 is not None and consommation_phase2 is not None 
                and consommation_phase3 is not None
                and consommation_jour is not None and consommation_pointe_ete is not None 
                and consommation_nuit is not None and consommation_pointe_hiver is not None 
                and puissance_souscrite_jour is not None and puissance_souscrite_pointe_ete is not None 
                and puissance_souscrite_nuit is not None and puissance_souscrite_pointe_hiver is not None 
                and puissance_appelee_max_jour is not None and puissance_appelee_max_pointe_ete is not None 
                and puissance_appelee_max_nuit is not None and puissance_appelee_max_pointe_hiver is not None 
                and cos_phi is not None and puissance_reactive is not None):
                success = ajouter_facture_electricite(
                    numero_facture,
                    date_facture.strftime("%Y-%m-%d"),
                    consommation_phase1,
                    consommation_phase2,
                    consommation_phase3,
                    consommation_jour,
                    consommation_pointe_ete,
                    consommation_nuit,
                    consommation_pointe_hiver,
                    puissance_souscrite_jour,
                    puissance_souscrite_pointe_ete,
                    puissance_souscrite_nuit,
                    puissance_souscrite_pointe_hiver,
                    puissance_appelee_max_jour,
                    puissance_appelee_max_pointe_ete,
                    puissance_appelee_max_nuit,
                    puissance_appelee_max_pointe_hiver,
                    cos_phi,
                    puissance_reactive,
                    facture_rectificative,
                    tarif_jour,
                    tarif_pointe_ete,
                    tarif_nuit,
                    tarif_pointe_hiver,
                    avance
                )
                
                if success:
                    st.success("✅ Facture enregistrée avec succès!")
                    #st.balloons()
                else:
                    st.error("❌ Erreur lors de l'enregistrement. Vérifiez que le numéro de facture n'existe pas déjà et que tous les champs sont valides.")
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires (*)")

# ========== ONGLET 2: LISTE DES FACTURES ==========
with tab2:
    st.markdown('<h2 class="section-header">Liste des Factures</h2>', unsafe_allow_html=True)
    
    factures = obtenir_toutes_factures_electricite()
    
    if factures:
        # Récupérer les derniers tarifs connus (de la facture la plus récente)
        last_invoice = factures[0]
        def_t_jour = float(last_invoice.get('tarif_jour') or 0.0)
        def_t_pe = float(last_invoice.get('tarif_pointe_ete') or 0.0)
        def_t_nuit = float(last_invoice.get('tarif_nuit') or 0.0)
        def_t_ph = float(last_invoice.get('tarif_pointe_hiver') or 0.0)
        
        with st.expander("📊 Paramètres de Tarification (Simulation Globale)"):
            st.info("Modifiez ces valeurs pour simuler le coût total avec un tarif unique sur toutes les factures.")
            col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)
            with col_sim1:
                sim_t_jour = st.number_input("Tarif Jour (Sim)", value=def_t_jour, format="%.3f", key="sim_tj")
            with col_sim2:
                sim_t_pe = st.number_input("Tarif Pte Été (Sim)", value=def_t_pe, format="%.3f", key="sim_tpe")
            with col_sim3:
                sim_t_nuit = st.number_input("Tarif Nuit (Sim)", value=def_t_nuit, format="%.3f", key="sim_tn")
            with col_sim4:
                sim_t_ph = st.number_input("Tarif Pte Hiver (Sim)", value=def_t_ph, format="%.3f", key="sim_tph")
            
            st.markdown("---")
            st.subheader("Simulateur Tarif Unique (Test)")
            col_uni1, col_uni2 = st.columns(2)
            with col_uni1:
                # Valeur par défaut 0.255 demandée
                sim_tarif_unique = st.number_input("Tarif Unique (DT/kWh)", value=0.255, format="%.3f", key="sim_unique_kwh")
            with col_uni2:
                st.info("Ce tarif est utilisé pour calculer la colonne 'Facture Uniforme'.")
            
            st.markdown("---")
            st.markdown("##### 🪙 Taxes et Redevances")
            col_tax1, col_tax2, col_tax3 = st.columns(3)
            with col_tax1:
                taux_tva = st.number_input("TVA (%)", value=19.0, step=1.0, format="%.2f", key="sim_tva")
            with col_tax2:
                # Taxe municipale par kWh (?) ou montant fixe ? "tarif tax municipale prend par defaut 0,006"
                # Souvent c'est Millimes/kWh. 0.01 DT = 10 millime. (Modif User)
                taxe_mun = st.number_input("Taxe Municipale (DT/kWh)", value=0.01, step=0.001, format="%.4f", key="sim_mun")
            with col_tax3:
                # FTE "prend par defaut 3,(" -> Assuming 3.5
                # FTE is often per kWh or MWh? Or fixed?
                # Usually ~1 millime/kWh or 3.5 ?? 
                # I'll just use the number 3.5.
                redevance_fte = st.number_input("FTE (Redevance)", value=3.5, step=0.1, format="%.3f", key="sim_fte")
        
        # Calculer la consommation totale
        df = pd.DataFrame(factures)
        
        # Calcul de la consommation totale (Somme des postes horaires)
        cols_conso = ['consommation_jour', 'consommation_pointe_ete', 'consommation_nuit', 'consommation_pointe_hiver']
        # S'assurer que les colonnes existent et remplacer None par 0
        for c in cols_conso:
            if c not in df.columns:
                df[c] = 0
            df[c] = df[c].fillna(0)
            
        df['consommation_totale'] = df[cols_conso].sum(axis=1)
        
        # Calcul TEP (1 kWh = 0.000086 tep)
        df['tep'] = df['consommation_totale'] * 0.000086

        # Calcul du Coût Total (Consommation * Tarif Simulé)
        # On utilise les valeurs du simulateur pour l'affichage
        df['tarif_jour'] = sim_t_jour
        df['tarif_pointe_ete'] = sim_t_pe
        df['tarif_nuit'] = sim_t_nuit
        df['tarif_pointe_hiver'] = sim_t_ph
        
        # Passer le tarif uniforme au dataframe pour le calcul row-by-row
        # (sim_tarif_unique est défini dans le bloc expander ci-dessus)
        if 'sim_tarif_unique' in locals():
            df['tarif_uniforme_val'] = sim_tarif_unique
        else:
            df['tarif_uniforme_val'] = 0.255
            
        df['montant_jour'] = df['consommation_jour'] * sim_t_jour
        df['montant_pointe_ete'] = df['consommation_pointe_ete'] * sim_t_pe
        df['montant_nuit'] = df['consommation_nuit'] * sim_t_nuit
        df['montant_pointe_hiver'] = df['consommation_pointe_hiver'] * sim_t_ph

        df['cout_total'] = (
            df['montant_jour'] +
            df['montant_pointe_ete'] +
            df['montant_nuit'] +
            df['montant_pointe_hiver']
        )

        # Calcul Puissance Réduite (Pr)
        # Formule: 0.4*PH + 0.3*PE + 0.2*J + 0.1*N
        cols_ps = ['puissance_souscrite_pointe_hiver', 'puissance_souscrite_pointe_ete', 
                   'puissance_souscrite_jour', 'puissance_souscrite_nuit']
        for c in cols_ps:
            if c not in df.columns:
                df[c] = 0.0
            df[c] = df[c].fillna(0.0)
            
        df['puissance_reduite'] = (
            0.4 * df['puissance_souscrite_pointe_hiver'] +
            0.3 * df['puissance_souscrite_pointe_ete'] +
            0.2 * df['puissance_souscrite_jour'] +
            0.1 * df['puissance_souscrite_nuit']
        )

        # Calcul Prime de Puissance
        # Formule: Pr * 11
        df['prime_puissance'] = df['puissance_reduite'] * 11

        # Calcul Malus/Bonus Cos Phi
        def calcul_impact_cos_phi(row):
            try:
                # On essaie de convertir ce qu'il y a en nombre.
                # Si c'est None ou vide, on met 0 par défaut pour le calcul, ou on garde ce que l'utilisateur a mis.
                val = row.get('cos_phi')
                if val is None:
                    return 0.0
                
                cos_phi = float(val)
                
                M = row.get('cout_total')
                if M is None:
                    M = 0.0
                else:
                    M = float(M)
            except (ValueError, TypeError):
                # Si erreur de lecture, on retourne 0 (pas d'impact)
                return 0.0
                
            if cos_phi > 0.9:
                # Bonus: (0.5 * cos - 0.45) * M
                return (0.5 * cos_phi - 0.45) * M
            elif cos_phi > 0.8:
                # Zone Neutre
                return 0.0
            else:
                # Malus
                if cos_phi >= 0.74:
                    # Niveau 1: -0.5 * (0.8 - cos) * M
                    return -0.5 * (0.8 - cos_phi) * M
                else:
                    # Niveau 2: -(0.775 - cos) * M
                    return -(0.775 - cos_phi) * M

        df['malus_bonus_cosphi'] = df.apply(calcul_impact_cos_phi, axis=1)

        # Calcul Pénalité Dépassement Puissance
        def calcul_penalite_depassement(row):
            # Helper pour lire float safely
            def safe_float(key):
                try: 
                    return float(row.get(key) or 0.0)
                except: 
                    return 0.0

            # 1. Puissances Souscrites
            ps_j = safe_float('puissance_souscrite_jour')
            ps_ete = safe_float('puissance_souscrite_pointe_ete')
            ps_nuit = safe_float('puissance_souscrite_nuit')
            ps_hiv = safe_float('puissance_souscrite_pointe_hiver')

            # 2. Puissances Max Appelées
            pm_j = safe_float('puissance_appelee_max_jour')
            pm_ete = safe_float('puissance_appelee_max_pointe_ete')
            pm_nuit = safe_float('puissance_appelee_max_nuit')
            pm_hiv = safe_float('puissance_appelee_max_pointe_hiver')

            # PR1 (Calcul identique à puissance_reduite)
            PR1 = 0.4*ps_hiv + 0.3*ps_ete + 0.2*ps_j + 0.1*ps_nuit

            # 3. Logique Dépassement
            # Condition: Si un max (Nuit, Eté, Hiver) dépasse le Max Jour
            exceeds = (pm_nuit > pm_j) or (pm_ete > pm_j) or (pm_hiv > pm_j)

            if exceeds:
                # Cas 1: Dépassement direct par rapport au jour (Critique)
                p_max_critique = max(pm_nuit, pm_ete, pm_hiv)
                
                # NOUVELLE LOGIQUE VERIFIEE: Comparer à la PS de la période critique
                ps_critique = 0.0
                if pm_nuit == p_max_critique: ps_critique = ps_nuit
                elif pm_hiv == p_max_critique: ps_critique = ps_hiv
                elif pm_ete == p_max_critique: ps_critique = ps_ete
                
                # Si dépassement de sa propre souscrite
                if p_max_critique > ps_critique:
                    penalite = (p_max_critique - ps_critique) * 39.6 # 11*12/3.3333
                else:
                    # Fallback si pas de dépassement local (ne devrait pas arriver si exceeeds=True sauf si PS > MaxJour mais < MaxCritique?)
                    # Fallback si pas de dépassement local (ne devrait pas arriver si exceeeds=True sauf si PS > MaxJour mais < MaxCritique?)
                    # Dans le doute on garde l'ancienne formule si la nouvelle donne <= 0
                    penalite = (p_max_critique - PR1) * 39.6
            else:
                # Cas 2: Calcul corrigé via les MaxvsSouscrite
                hiver_corr = max(pm_hiv, ps_hiv)
                ete_corr = max(pm_ete, ps_ete)
                jour_corr = max(pm_j, ps_j)
                nuit_corr = max(pm_nuit, ps_nuit)
                
                PR2 = 0.4*hiver_corr + 0.3*ete_corr + 0.2*jour_corr + 0.1*nuit_corr
                penalite = (PR2 - PR1) * 39.6

            return max(0.0, penalite)

        df['penalite_depassement'] = df.apply(calcul_penalite_depassement, axis=1)

        # Calcul Montant Facture Hors Taxe
        # Formule: Prime + Pénalité - Bonus/Malus + Conso
        # Note: malus_bonus_cosphi est Positif pour Bonus (à déduire) et Négatif pour Malus (à ajouter via -(-malus))
        df['montant_ht'] = (
            df['prime_puissance'] + 
            df['penalite_depassement'] - 
            df['malus_bonus_cosphi'] + 
            df['cout_total']
        )
        
        # Calcul TVA (Part Taxe uniquement)
        # 1. Montant TVA Consommation
        df['montant_conso_tva'] = df['cout_total'] * (taux_tva/100.0)
        
        # 2. TVA Redevance (Prime + Pénalité)
        df['redevance_tva'] = (df['prime_puissance'] + df['penalite_depassement']) * (taux_tva/100.0)

        # 3. Taxe Municipale
        # Formule: Consommation Totale * Tarif Taxe Municipale
        # 3. Taxe Municipale
        # Formule: Consommation Totale * Tarif Taxe Municipale
        df['montant_taxe_mun'] = df['consommation_totale'] * taxe_mun
        
        # 3b. FTE (Fonds de Transition Energétique)
        # Fixe: 3.500 DT
        df['montant_fte'] = 3.500
        
        # 4. Montant Total Facture (TTC)
        # Formula: Tous les taxes + Bonus/Malus + HT - Avance
        
        # Ensure 'avance' is 0 if NaN
        if 'avance' not in df.columns:
            df['avance'] = 0.0
        df['avance'] = df['avance'].fillna(0.0)
        
        df['montant_total_ttc'] = (
            df['montant_ht'] + 
            df['montant_conso_tva'] + 
            df['redevance_tva'] + 
            df['montant_taxe_mun'] + 
            df['montant_fte'] - 
            df['avance']
        )
        
        # --- CALCUL FACTURE UNIFORME (Simulation ajoutée) ---
        # Equation: (Total_Active * Tarif_Uniform) + ((PR/0.7)*(5/CosPhi)) + 5 + (Total_Active * 0.006) - Impact_CosPhi
        def calcul_facture_uniforme_row(row):
             try:
                 conso_tot = float(row.get('consommation_totale') or 0)
                 pr = float(row.get('puissance_reduite') or 0)
                 cos_phi = float(row.get('cos_phi') or 1.0)
                 if cos_phi == 0: cos_phi = 1.0
                 
                 impact_cos_sign = float(row.get('malus_bonus_cosphi') or 0)
                 # Note: impact_cos_sign is (+) for Bonus (Revenue), (-) for Malus (Cost).
                 # To get "Cost Adjustment", we subtract Bonus (reduce bill) and subtract Malus (increase bill? Wait).
                 # Malus is Negative. Standard Formula: Base + Malus.
                 # If Malus is -50, adding it reduces bill? No.
                 # Let's check impact_cos calculation again.
                 # Line 615: Malus return NEGATIVE number.
                 # Line 692: montant_ht = ... - impact_cos.
                 # If Malus (-50): HT = ... - (-50) = ... + 50. (Increased Cost). Correct.
                 # If Bonus (+50): HT = ... - (+50) = ... - 50. (Decreased Cost). Correct.
                 # So we must SUBTRACT impact_cos in our formula too.
                 
                 # New Formula Components:
                 # 1. Energie: Conso * Tarif Unique
                 # Note: variable tarif_uniforme comes from sidebar, need to ensure access or use column if mapped.
                 # Since apply runs row-by-row, global 'tarif_uniforme' (float) is accessible if defined in scope.
                 # BUT sidebar is defined earlier. We need to make sure 'tarif_uniforme' is available.
                 # We will add it to DF first for safety or assume scope access (Streamlit runs script top-down).
                 
                 t_u = float(row.get('tarif_uniforme_val') or 0.255)
                 
                 terme_conso = conso_tot * t_u
                 
                 # 2. Puissance: (PR / 0.7) * (5 / CosPhi)
                 terme_puiss = (pr / 0.7) * (5 / cos_phi)
                 
                 # 3. Fixe: 5
                 terme_fixe = 5.0
                 
                 # 4. Taxe Mun: Conso * 0.01 (Modif User)
                 t_mun = conso_tot * 0.01
                 
                 # Total
                 total = terme_conso + terme_puiss + terme_fixe + t_mun - impact_cos_sign
                 return total
             except:
                 return 0.0

        # Injecter la valeur du tarif uniforme (récupéré du widget sidebar ou défaut)
        # We need to define tarif_uniforme widget BEFORE this.
        # It will be inserted in Tab 2 sidebar section.
        # But we create a column to be safe for apply function
        if 'tarif_uniforme_val' not in df.columns:
             df['tarif_uniforme_val'] = 0.255 # Default placeholder, will be updated by widget logic if possible or we use global
             
        df['facture_uniforme'] = df.apply(calcul_facture_uniforme_row, axis=1)

        # 5. Analyse des Phases (Pourcentage de différence par rapport à la moyenne)
        # Vérifier si les colonnes existent
        cols_phase = ['consommation_phase1', 'consommation_phase2', 'consommation_phase3']
        if all(col in df.columns for col in cols_phase):
            # Remplacer NaN par 0 pour le calcul
            p1 = df['consommation_phase1'].fillna(0.0)
            p2 = df['consommation_phase2'].fillna(0.0)
            p3 = df['consommation_phase3'].fillna(0.0)
            
            avg_phase = (p1 + p2 + p3) / 3.0
            
            # Éviter division par zéro
            # On utilise une petite astuce ou np.where, mais ici df.apply est simple ou calcul vectoriel avec mask.
            # Vectoriel:
            # Mask where avg != 0
            df['ecart_p1_pct'] = 0.0
            df['ecart_p2_pct'] = 0.0
            df['ecart_p3_pct'] = 0.0
            
            mask = avg_phase > 0
            df.loc[mask, 'ecart_p1_pct'] = ((p1[mask] - avg_phase[mask]) / avg_phase[mask]) * 100.0
            df.loc[mask, 'ecart_p2_pct'] = ((p2[mask] - avg_phase[mask]) / avg_phase[mask]) * 100.0
            df.loc[mask, 'ecart_p3_pct'] = ((p3[mask] - avg_phase[mask]) / avg_phase[mask]) * 100.0
        
        # --- FILTRES DE PRODUCTION ---
        st.markdown("### 🏭 Couplage Production")
        col_prod1, col_prod2 = st.columns(2)
        
        with col_prod1:
            unite_prod = st.selectbox("Unité de production à coupler", ["T (Tonnes)", "kg", "L (Litres)", "m3", "Pièces/Unités"], index=0)
            
        prod_data = obtenir_toute_production()
        prod_col_display = f"Production ({unite_prod.split(' ')[0]})"
        
        df['production_mensuelle'] = 0
        
        if prod_data:
            df_prod = pd.DataFrame(prod_data)
            with col_prod2:
                scopes_avail = df_prod['scope_value'].unique()
                selected_scopes = st.multiselect("Filtrer par Scope", options=scopes_avail, default=scopes_avail)
            
            mask_prod = (df_prod['unite_mesure'] == unite_prod)
            if selected_scopes:
                mask_prod &= df_prod['scope_value'].isin(selected_scopes)
                
            df_prod_filtered = df_prod[mask_prod].copy()
            
            if not df_prod_filtered.empty:
                df['date_dt'] = pd.to_datetime(df['date_facture'])
                df['Mois'] = df['date_dt'].dt.to_period('M')
                df_prod_filtered['date_prod_dt'] = pd.to_datetime(df_prod_filtered['date_production'])
                df_prod_filtered['Mois'] = df_prod_filtered['date_prod_dt'].dt.to_period('M')
                prod_monthly = df_prod_filtered.groupby('Mois')['quantite'].sum().reset_index()
                df = pd.merge(df, prod_monthly, on='Mois', how='left')
                if 'quantite' in df.columns:
                    df['production_mensuelle'] = df['quantite'].fillna(0)
                    df.drop(columns=['quantite', 'Mois', 'date_dt'], inplace=True, errors='ignore')
        
        # --- CALCULATEUR DE RATIO ---
        st.markdown("### ➗ Analyseur de Ratio (KPI)")
        with st.expander("Créer un indicateur de performance (Ex: kWh / Tonne)"):
            # Identifier les colonnes numériques
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            # Exclure les IDs ou colonnes non pertinentes si besoin
            numeric_cols = [c for c in numeric_cols if c not in ['id', 'facture_rectificative']]
            
            col_kpi1, col_kpi2, col_kpi3 = st.columns([2, 0.5, 2])
            with col_kpi1:
                col_a = st.selectbox("Numérateur (A)", numeric_cols, index=numeric_cols.index('consommation_jour') if 'consommation_jour' in numeric_cols else 0)
            with col_kpi2:
                st.markdown("<h2 style='text-align: center; margin-top: 0px;'>/</h2>", unsafe_allow_html=True)
            with col_kpi3:
                col_b = st.selectbox("Dénominateur (B)", numeric_cols, index=numeric_cols.index('production_mensuelle') if 'production_mensuelle' in numeric_cols else 0)
                
            col_kpi_act = st.columns(1)[0]
            if st.button("Calculer et Ajouter au Tableau"):
                st.session_state['ratio_a'] = col_a
                st.session_state['ratio_b'] = col_b
                st.success(f"Calcul activé : {col_a} / {col_b}")
                st.rerun()

        # Application du calcul si configuré
        if 'ratio_a' in st.session_state and 'ratio_b' in st.session_state:
            col_a = st.session_state['ratio_a']
            col_b = st.session_state['ratio_b']
            if col_a in df.columns and col_b in df.columns:
                ratio_name = f"Ratio {col_a}/{col_b}"
                df[ratio_name] = df.apply(lambda row: row[col_a] / row[col_b] if row[col_b] != 0 else 0, axis=1)
        
        if 'type_facture' not in df.columns:
            df['type_facture'] = 'Reel'
        df['type_facture'] = df['type_facture'].fillna('Reel')

        if 'facture_rectificative' in df.columns:
            # Combine Type and Rectificative info
            def get_status(row):
                 base_type = row.get('type_facture', 'Reel')
                 is_rect = row.get('facture_rectificative', 0)
                 if base_type == 'Simule':
                     return '🔄 Simulé'
                 elif is_rect == 1:
                     return '📝 Rectificative'
                 else:
                     return '✅ Réelle'
            
            df['Statut'] = df.apply(get_status, axis=1)
        
        # Préparer les colonnes pour l'affichage
        display_columns = ['Statut', 'numero_facture', 'date_facture', 'consommation_totale', 'cout_total', 'montant_jour', 'montant_pointe_ete', 'montant_nuit', 'montant_pointe_hiver', 'tep', 'puissance_reduite', 'prime_puissance', 'malus_bonus_cosphi', 'penalite_depassement', 'montant_ht', 'montant_conso_tva', 'redevance_tva', 'montant_taxe_mun', 'montant_fte', 'avance', 'montant_total_ttc', 'facture_uniforme', 'production_mensuelle']

        # Ajouter le ratio si présent
        for col in df.columns:
            if col.startswith("Ratio"):
                display_columns.append(col)
        
        # Ajouter les colonnes d'écart phase si elles existent
        if 'ecart_p1_pct' in df.columns:
            display_columns.extend(['ecart_p1_pct', 'ecart_p2_pct', 'ecart_p3_pct'])
            

        
        # Ajouter les colonnes de consommation par phase si elles existent
        if 'consommation_phase1' in df.columns:
            display_columns.extend(['consommation_phase1', 'consommation_phase2', 'consommation_phase3'])
        
        # Ajouter les colonnes de consommation par tranche horaire si elles existent
        if 'consommation_jour' in df.columns:
            display_columns.extend(['consommation_jour', 'consommation_pointe_ete', 
                                   'consommation_nuit', 'consommation_pointe_hiver'])
        
        display_columns.extend(['cos_phi', 'puissance_reactive'])
        
        # Ajouter les colonnes de puissance si elles existent
        if 'puissance_souscrite_jour' in df.columns:
            display_columns.extend(['puissance_souscrite_jour', 'puissance_souscrite_pointe_ete', 
                                   'puissance_souscrite_nuit', 'puissance_souscrite_pointe_hiver'])
        if 'puissance_appelee_max_jour' in df.columns:
            display_columns.extend(['puissance_appelee_max_jour', 'puissance_appelee_max_pointe_ete',
                                   'puissance_appelee_max_nuit', 'puissance_appelee_max_pointe_hiver'])
        
        # Filtrer les colonnes qui existent réellement
        available_columns = [col for col in display_columns if col in df.columns]
        
        # Afficher le tableau des factures
        rename_dict = {
            'numero_facture': 'Numéro',
            'date_facture': 'Date',
            'production_mensuelle': prod_col_display,
            'consommation_totale': 'Cons. Totale (kWh)',
            'cout_total': 'Montant Total Consommation (DT)',
            'montant_jour': 'Montant Jour (DT)',
            'montant_pointe_ete': 'Montant Pointe Été (DT)',
            'montant_nuit': 'Montant Nuit (DT)',
            'montant_pointe_hiver': 'Montant Pointe Hiver (DT)',
            'tep': 'TEP (Tonnes Équivalent Pétrole)',
            'puissance_reduite': 'Puissance Réduite (kW)',
            'prime_puissance': 'Prime de Puissance (DT)',
            'malus_bonus_cosphi': 'Bonus/Malus Cos Phi (DT)',
            'penalite_depassement': 'Pénalité Puissance (DT)',
            'montant_ht': 'Montant Facture HT (DT)',
            'montant_conso_tva': 'Montant TVA Consommation (DT)',
            'redevance_tva': 'TVA Redevance (DT)',
            'montant_taxe_mun': 'Montant Taxe Municipale (DT)',
            'montant_fte': 'Montant FTE (DT)',
            'avance': 'Avance (DT)',
            'montant_total_ttc': 'Montant Total Facture (DT)',
            'facture_uniforme': 'Facture Uniforme (DT)', # Label
            'Type': 'Type',
            'consommation_phase1': 'Phase 1 (kWh)',
            'consommation_phase2': 'Phase 2 (kWh)',
            'consommation_phase3': 'Phase 3 (kWh)',
            'ecart_p1_pct': 'Écart Ph1 (%)',
            'ecart_p2_pct': 'Écart Ph2 (%)',
            'ecart_p3_pct': 'Écart Ph3 (%)',
            'consommation_jour': 'Cons. Jour (kWh)',
            'consommation_pointe_ete': 'Cons. Pointe été (kWh)',
            'consommation_nuit': 'Cons. Nuit (kWh)',
            'consommation_pointe_hiver': 'Cons. Pointe hiver (kWh)',
            'cos_phi': 'Cos Phi',
            'puissance_reactive': 'Puissance réactive (kVAR)',
            'puissance_souscrite_jour': 'PS Jour (kW)',
            'puissance_souscrite_pointe_ete': 'PS Pointe été (kW)',
            'puissance_souscrite_nuit': 'PS Nuit (kW)',
            'puissance_souscrite_pointe_hiver': 'PS Pointe hiver (kW)',
            'puissance_appelee_max_jour': 'PA Max Jour (kW)',
            'puissance_appelee_max_pointe_ete': 'PA Max Pointe été (kW)',
            'puissance_appelee_max_nuit': 'PA Max Nuit (kW)',
            'puissance_appelee_max_pointe_hiver': 'PA Max Pointe hiver (kW)'
        }
        
        st.dataframe(
            df[available_columns].rename(columns=rename_dict),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown('<h3 class="section-header">📈 Générateur de graphiques</h3>', unsafe_allow_html=True)

        # Préparer les options pour les sélecteurs
        friendly_to_raw = {rename_dict.get(col, col): col for col in available_columns}
        options_cols = list(friendly_to_raw.keys())
        
        # Configuration du graphique
        # Configuration du graphique
        with st.form("graph_generator"):
            import plotly.express as px
            
            col_type, col_x, col_y = st.columns(3)
            
            with col_type:
                graph_type = st.selectbox(
                    "Type de graphique",
                    ["Ligne", "Barres", "Aire", "Nuage de points"],
                    index=0
                )
            
            with col_x:
                x_axis_friendly = st.selectbox(
                    "Axe X",
                    options_cols,
                    index=options_cols.index('Date') if 'Date' in options_cols else 0
                )
            
            with col_y:
                # Default Y to something interesting if available
                default_y_index = 0
                for i, opt in enumerate(options_cols):
                    if "Cons. Jour" in opt:
                        default_y_index = i
                        break
                
                # MULTI-SELECT pour permettre plusieurs courbes
                y_axis_friendly = st.multiselect(
                    "Axe Y (Plusieurs choix possibles)",
                    options_cols,
                    default=[options_cols[default_y_index]] if options_cols else None
                )
                
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                nb_points = st.number_input("Nombre de points à afficher (0 pour tous)", min_value=0, value=12, step=1)
            
            with col_filter2:
                # Add Date Range filter if X axis is Date
                date_filter = None
                if 'Date' in x_axis_friendly or 'date' in x_axis_friendly.lower():
                    st.info("Filtrage par période disponible.")
                    date_filter = st.date_input(
                        "Période (Début - Fin)",
                        value=[],
                        help="Sélectionnez une date de début et une date de fin"
                    )
                else:
                    st.info(f"Le filtrage par date est désactivé (Axe X: {x_axis_friendly})")
            
            # Option de comparaison annuelle
            comparison_mode = False
            selected_years = []
            if 'Date' in x_axis_friendly or 'date' in x_axis_friendly.lower():
                comparison_mode = st.checkbox("🔄 Comparaison Annuelle (Superposition des années)", 
                                            help="Cochez pour superposer les courbes de chaque année (Jan-Dec) sur le même graphique.")
                
                if comparison_mode:
                    # Extract available years from dataframe for selection
                    # Assuming 'date_facture' is always available or derived from X axis?
                    # Safer to use the Date column we know exists in DB: 'date_facture'
                    # But x_col might be different. Let's assume 'date_facture' is the source of truth for years.
                    try:
                        # Ensure date_facture is datetime
                        if 'date_facture' in df.columns:
                            all_years = sorted(pd.to_datetime(df['date_facture']).dt.year.unique(), reverse=True)
                            selected_years = st.multiselect("Choisir les années à comparer", all_years, default=all_years)
                    except Exception as e:
                        st.warning(f"Impossible de lister les années : {e}")

            # Titre Personnalisé
            graph_title = st.text_input("Titre du Graphique", value=f"Analyse de {', '.join(y_axis_friendly) if y_axis_friendly else '...'}")

            generate_btn = st.form_submit_button("📊 Générer le graphique", use_container_width=True)

        if generate_btn and y_axis_friendly:
            x_col = friendly_to_raw[x_axis_friendly]
            y_cols = [friendly_to_raw[y] for y in y_axis_friendly]
            
            # Create a view for plotting (Include X + all Ys)
            cols_to_keep = [x_col] + y_cols
            # Avoid duplicates if X is also in Y
            cols_to_keep = list(set(cols_to_keep))
            
            chart_data = df[cols_to_keep].copy()
            
            # Normalize Date
            if 'Date' in x_axis_friendly or 'date' in x_axis_friendly.lower():
                 chart_data[x_col] = pd.to_datetime(chart_data[x_col])
            
            # Sort by X axis
            try:
                chart_data = chart_data.sort_values(by=x_col)
            except:
                pass
            
            # Apply Date Filter Logic
            if 'date_filter' in locals() and date_filter and len(date_filter) == 2:
                start_date, end_date = date_filter
                try:
                    chart_data[x_col] = pd.to_datetime(chart_data[x_col])
                    mask = (chart_data[x_col].dt.date >= start_date) & (chart_data[x_col].dt.date <= end_date)
                    chart_data = chart_data.loc[mask]
                except Exception as e:
                    st.warning(f"Impossible d'appliquer le filtre de date : {e}")
            
            # Apply limit if set (Disable for comparison mode)
            if nb_points > 0 and not comparison_mode:
                chart_data = chart_data.tail(nb_points)
            
            # PLOTLY GENERATION
            if comparison_mode and ('Date' in x_axis_friendly or 'date' in x_axis_friendly.lower()):
                 # Mode Comparaison Annuelle
                try:
                    # Assurer que x_col est datetime locale
                    chart_data[x_col] = pd.to_datetime(chart_data[x_col])
                    
                    chart_data['Année'] = chart_data[x_col].dt.year
                    
                    # Filter by selected years if available
                    if 'selected_years' in locals() and selected_years:
                         chart_data = chart_data[chart_data['Année'].isin(selected_years)]
                    
                    chart_data['Année'] = chart_data['Année'].astype(str)
                    
                    # Align all dates to the same leap year (e.g. 2024) to compare Jan 1 vs Jan 1
                    chart_data['Date_Virtuelle'] = chart_data[x_col].apply(lambda d: d.replace(year=2024))
                    chart_data = chart_data.sort_values('Date_Virtuelle')
                    
                    # Melt data for multiple variables
                    # We want: Date_Virtuelle, Année, Variable, Value
                    melted_data = chart_data.melt(id_vars=['Date_Virtuelle', 'Année'], 
                                                  value_vars=y_cols, 
                                                  var_name='Variable', 
                                                  value_name='Valeur')
                    
                    # Map raw variable names back to friendly names for display if possible
                    raw_to_friendly = {v: k for k, v in friendly_to_raw.items()}
                    melted_data['Variable'] = melted_data['Variable'].map(lambda x: raw_to_friendly.get(x, x))

                    # Faceting: Row for each variable to handle different scales (e.g. kWh vs kW)
                    fig = px.line(melted_data, x='Date_Virtuelle', y='Valeur', color='Année', 
                                  facet_row='Variable',
                                  title=f"Comparaison Annuelle : {', '.join(y_axis_friendly)}",
                                  markers=True)
                    
                    # Allow independent Y axes
                    fig.update_yaxes(matches=None)
                    # Format X axis to show only Month names
                    fig.update_xaxes(tickformat="%B", title_text="Mois")
                    # Make legend cleaner
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                except Exception as e:
                    st.error(f"Erreur lors de la préparation de la comparaison : {e}")
                    fig = px.line(title="Erreur")
            else:
                # Mode Standard
                if graph_type == "Ligne":
                    fig = px.line(chart_data, x=x_col, y=y_cols, title=graph_title, markers=True)
                elif graph_type == "Barres":
                    fig = px.bar(chart_data, x=x_col, y=y_cols, title=graph_title, barmode='group')
                elif graph_type == "Aire":
                    fig = px.area(chart_data, x=x_col, y=y_cols, title=graph_title)
                elif graph_type == "Nuage de points":
                    fig = px.scatter(chart_data, x=x_col, y=y_cols, title=graph_title)
            
            # Display Plotly Chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Note for download
            st.caption("ℹ️ Pour télécharger le graphique, cliquez sur l'icône appareil photo 'Download plot as a png' apparaissant au survol du graphique.")
            
            st.markdown("### 📋 Données du graphique")
            
            if comparison_mode and ('Date' in x_axis_friendly or 'date' in x_axis_friendly.lower()):
                # Create a pivot table for each variable: Rows=Year, Cols=Month
                try:
                    # Add Month Name column for nicer display
                    # Using Date_Virtuelle is safe because it's aligned to 2024
                    melted_data['Mois'] = melted_data['Date_Virtuelle'].dt.strftime('%B')
                    # Ensure correct month order
                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                    # Attempt french mapping if locale is tricky
                    months_fr = {'January': 'Janvier', 'February': 'Février', 'March': 'Mars', 'April': 'Avril', 'May': 'Mai', 'June': 'Juin', 'July': 'Juillet', 'August': 'Août', 'September': 'Septembre', 'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'}
                    melted_data['Mois_Fr'] = melted_data['Mois'].map(months_fr).fillna(melted_data['Mois'])
                    
                    # Sort by Month Number
                    melted_data['MoisNum'] = melted_data['Date_Virtuelle'].dt.month
                    
                    unique_vars = melted_data['Variable'].unique()
                    
                    for var in unique_vars:
                         st.markdown(f"#### {var}")
                         var_data = melted_data[melted_data['Variable'] == var]
                         
                         # Pivot
                         pivot_table = var_data.pivot(index='Année', columns='MoisNum', values='Valeur')
                         
                         # Rename columns to names
                         # Get map from Num to Name
                         num_to_name = var_data[['MoisNum', 'Mois_Fr']].drop_duplicates().set_index('MoisNum')['Mois_Fr']
                         pivot_table.columns = [num_to_name.get(c, c) for c in pivot_table.columns]
                         
                         st.dataframe(pivot_table, use_container_width=True)
                         
                    # Download full melted data or pivoted? Melted is better for analysis, Pivoted for reading.
                    # Let's verify what 'csv' should be. Maybe the melted version?
                    csv = melted_data.to_csv(index=False).encode('utf-8')

                except Exception as e:
                     st.error(f"Erreur d'affichage du tableau croisé : {e}")
                     st.dataframe(chart_data, use_container_width=True)
                     csv = chart_data.to_csv().encode('utf-8')
            else:
                # Standard Mode
                st.dataframe(chart_data.T, use_container_width=True)
                csv = chart_data.to_csv().encode('utf-8')
            
            st.download_button(
                label="📥 Télécharger les données (CSV)",
                data=csv,
                file_name=f"graph_data.csv",
                mime="text/csv",
                key='download-csv'
            )
    else:
        st.info("📭 Aucune facture enregistrée pour le moment. Utilisez l'onglet 'Ajouter une facture' pour commencer.")

# ========== ONGLET 3: MODIFIER/SUPPRIMER ==========
with tab3:
    st.markdown('<h2 class="section-header">Modifier ou Supprimer une Facture</h2>', unsafe_allow_html=True)
    
    factures = obtenir_toutes_factures_electricite()
    
    if factures:
        # Sélectionner une facture à modifier/supprimer
        options = {f"{f['numero_facture']} - {f['date_facture']}": f['id'] for f in factures}
        facture_selectionnee = st.selectbox(
            "Sélectionnez une facture:",
            options=list(options.keys())
        )
        
        if facture_selectionnee:
            facture_id = options[facture_selectionnee]
            facture = obtenir_facture_electricite(facture_id)
            
            if facture:
                col_mod, col_sup = st.columns(2)
                
                with col_mod:
                    if st.button("✏️ Modifier cette facture", use_container_width=True):
                        st.session_state.mode_edition = True
                        st.session_state.facture_edition = facture
                        st.rerun()
                
                with col_sup:
                    if st.button("🗑️ Supprimer cette facture", use_container_width=True, type="primary"):
                        if supprimer_facture_electricite(facture_id):
                            st.success("✅ Facture supprimée avec succès!")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
                
                # Afficher les détails de la facture sélectionnée
                st.markdown("### 📄 Détails de la facture sélectionnée")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Numéro:** {facture['numero_facture']}")
                    st.write(f"**Date:** {facture['date_facture']}")
                    type_facture = "📝 Rectificative" if facture.get('facture_rectificative', 0) == 1 else "✅ Normale"
                    st.write(f"**Type:** {type_facture}")
                    st.write(f"**Cos Phi:** {facture.get('cos_phi', 'N/A')}")
                    st.write("**Consommation par tranche horaire:**")
                    st.write(f"  - Jour: {(facture.get('consommation_jour') or 0):.2f} kWh")
                    st.write(f"  - Pointe été: {(facture.get('consommation_pointe_ete') or 0):.2f} kWh")
                    st.write(f"  - Nuit: {(facture.get('consommation_nuit') or 0):.2f} kWh")
                    st.write(f"  - Pointe hiver: {(facture.get('consommation_pointe_hiver') or 0):.2f} kWh")
                    st.write("**Puissance souscrite:**")
                    st.write(f"  - Jour: {(facture.get('puissance_souscrite_jour') or 0):.2f} kW")
                    st.write(f"  - Pointe été: {(facture.get('puissance_souscrite_pointe_ete') or 0):.2f} kW")
                    st.write(f"  - Nuit: {(facture.get('puissance_souscrite_nuit') or 0):.2f} kW")
                    st.write(f"  - Pointe hiver: {(facture.get('puissance_souscrite_pointe_hiver') or 0):.2f} kW")
                
                with col2:
                    st.write("**Consommation par phase:**")
                    st.write(f"  - Phase 1: {(facture.get('consommation_phase1') or 0):.2f} kWh")
                    st.write(f"  - Phase 2: {(facture.get('consommation_phase2') or 0):.2f} kWh")
                    st.write(f"  - Phase 3: {(facture.get('consommation_phase3') or 0):.2f} kWh")
                    consommation_phases_totale = ((facture.get('consommation_phase1') or 0) + 
                                                 (facture.get('consommation_phase2') or 0) + 
                                                 (facture.get('consommation_phase3') or 0))
                    st.write(f"**Total phases:** {consommation_phases_totale:.2f} kWh")
                    consommation_tranche_totale = ((facture.get('consommation_jour') or 0) + 
                                                 (facture.get('consommation_pointe_ete') or 0) + 
                                                 (facture.get('consommation_nuit') or 0) + 
                                                 (facture.get('consommation_pointe_hiver') or 0))
                    st.write(f"**Consommation totale tranches:** {consommation_tranche_totale:.2f} kWh")
                    st.write(f"**Puissance réactive:** {(facture.get('puissance_reactive') or 0):.2f} kVAR")
                    st.write("**Puissance appelée max:**")
                    st.write(f"  - Jour: {(facture.get('puissance_appelee_max_jour') or 0):.2f} kW")
                    st.write(f"  - Pointe été: {(facture.get('puissance_appelee_max_pointe_ete') or 0):.2f} kW")
                    st.write(f"  - Nuit: {(facture.get('puissance_appelee_max_nuit') or 0):.2f} kW")
                    st.write(f"  - Pointe hiver: {(facture.get('puissance_appelee_max_pointe_hiver') or 0):.2f} kW")
                    st.write(f"**Avance:** {(facture.get('avance') or 0):.3f} DT")
                    

    
    # Formulaire de modification
    if st.session_state.mode_edition and st.session_state.facture_edition:
        st.markdown("---")
        st.markdown("### ✏️ Modifier la facture")
        
        facture = st.session_state.facture_edition
        
        with st.form("formulaire_modification_facture"):
            col1, col2 = st.columns(2)
            
            with col1:
                numero_facture_mod = st.text_input("Numéro de facture *", value=facture['numero_facture'])
                date_facture_mod = st.date_input("Date de la facture *", value=datetime.strptime(facture['date_facture'], "%Y-%m-%d").date())
            
            with col2:
                cos_phi_mod = st.number_input("Cos Phi (Facteur de puissance) *", min_value=0.0, max_value=1.0, step=0.01, format="%.2f", 
                                              value=float(facture.get('cos_phi', 0.9)) if facture.get('cos_phi') is not None else 0.9)
                puissance_reactive_mod = st.number_input("Puissance réactive (kVAR) *", min_value=0.0, step=0.1, format="%.2f", 
                                                        value=float(facture.get('puissance_reactive') or 0), key="puissance_reactive_mod")
                facture_rectificative_mod = st.checkbox("📝 Facture rectificative", 
                                                        value=bool(facture.get('facture_rectificative', 0) == 1),
                                                        key="rectif_mod")
                                                        
            st.markdown("### 💰 Tarification (Millimes/kWh ou DT)")
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                tarif_jour_mod = st.number_input("Tarif Jour", min_value=0.0, step=0.001, format="%.3f", 
                                                 value=float(facture.get('tarif_jour') or 0), key="t_jour_mod")
            with col_t2:
                tarif_pointe_ete_mod = st.number_input("Tarif Pointe Été", min_value=0.0, step=0.001, format="%.3f", 
                                                       value=float(facture.get('tarif_pointe_ete') or 0), key="t_p_ete_mod")
            with col_t3:
                tarif_nuit_mod = st.number_input("Tarif Nuit", min_value=0.0, step=0.001, format="%.3f", 
                                                 value=float(facture.get('tarif_nuit') or 0), key="t_nuit_mod")
            with col_t4:
                tarif_pointe_hiver_mod = st.number_input("Tarif Pointe Hiver", min_value=0.0, step=0.001, format="%.3f", 
                                                         value=float(facture.get('tarif_pointe_hiver') or 0), key="t_p_hiver_mod")
            
            st.markdown("### Consommation par phase (kWh)")
            col_p1_mod, col_p2_mod, col_p3_mod = st.columns(3)
            
            with col_p1_mod:
                consommation_phase1_mod = st.number_input("Phase 1 (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                          value=float(facture.get('consommation_phase1') or 0), key="p1_mod")
            with col_p2_mod:
                consommation_phase2_mod = st.number_input("Phase 2 (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                          value=float(facture.get('consommation_phase2') or 0), key="p2_mod")
            with col_p3_mod:
                consommation_phase3_mod = st.number_input("Phase 3 (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                          value=float(facture.get('consommation_phase3') or 0), key="p3_mod")
            
            st.markdown("### Consommation totale par tranche horaire (kWh)")
            col_cons_j_mod, col_cons_pe_mod, col_cons_n_mod, col_cons_ph_mod = st.columns(4)
            
            with col_cons_j_mod:
                consommation_jour_mod = st.number_input("Jour (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                        value=float(facture.get('consommation_jour') or 0), key="cons_jour_mod")
            with col_cons_pe_mod:
                consommation_pointe_ete_mod = st.number_input("Pointe été (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                             value=float(facture.get('consommation_pointe_ete') or 0), key="cons_pointe_ete_mod")
            with col_cons_n_mod:
                consommation_nuit_mod = st.number_input("Nuit (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                       value=float(facture.get('consommation_nuit') or 0), key="cons_nuit_mod")
            with col_cons_ph_mod:
                consommation_pointe_hiver_mod = st.number_input("Pointe hiver (kWh) *", min_value=0.0, step=0.1, format="%.2f", 
                                                                value=float(facture.get('consommation_pointe_hiver') or 0), key="cons_pointe_hiver_mod")
            
            st.markdown("### Puissance souscrite par période (kW)")
            col6, col7, col8, col9 = st.columns(4)
            
            with col6:
                puissance_souscrite_jour_mod = st.number_input("Jour (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                               value=float(facture.get('puissance_souscrite_jour') or 0), key="ps_jour_mod")
            with col7:
                puissance_souscrite_pointe_ete_mod = st.number_input("Pointe été (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                                value=float(facture.get('puissance_souscrite_pointe_ete') or 0), key="ps_pointe_ete_mod")
            with col8:
                puissance_souscrite_nuit_mod = st.number_input("Nuit (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                               value=float(facture.get('puissance_souscrite_nuit') or 0), key="ps_nuit_mod")
            with col9:
                puissance_souscrite_pointe_hiver_mod = st.number_input("Pointe hiver (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                               value=float(facture.get('puissance_souscrite_pointe_hiver') or 0), key="ps_pointe_hiver_mod")
            
            st.markdown("### Puissance appelée max par période (kW)")
            col10, col11, col12, col13 = st.columns(4)
            
            with col10:
                puissance_appelee_max_jour_mod = st.number_input("Jour max (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                                value=float(facture.get('puissance_appelee_max_jour') or 0), key="pa_jour_mod")
            with col11:
                puissance_appelee_max_pointe_ete_mod = st.number_input("Pointe été max (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                                    value=float(facture.get('puissance_appelee_max_pointe_ete') or 0), key="pa_pointe_ete_mod")
            with col12:
                puissance_appelee_max_nuit_mod = st.number_input("Nuit max (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                                 value=float(facture.get('puissance_appelee_max_nuit') or 0), key="pa_nuit_mod")
            with col13:
                puissance_appelee_max_pointe_hiver_mod = st.number_input("Pointe hiver max (kW) *", min_value=0.0, step=0.1, format="%.2f", 
                                                                  value=float(facture.get('puissance_appelee_max_pointe_hiver') or 0), key="pa_pointe_hiver_mod")
            
            st.markdown("### Avance")
            avance_mod = st.number_input("Avance (DT)", min_value=0.0, step=1.0, format="%.3f",
                                         value=float(facture.get('avance') or 0), key="avance_mod")
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                submitted_mod = st.form_submit_button("💾 Enregistrer les modifications", use_container_width=True)
            
            with col_cancel:
                if st.form_submit_button("❌ Annuler", use_container_width=True):
                    st.session_state.mode_edition = False
                    st.session_state.facture_edition = None
                    st.rerun()
            
            if submitted_mod:
                if (numero_facture_mod and date_facture_mod and 
                    consommation_phase1_mod is not None and consommation_phase2_mod is not None 
                    and consommation_phase3_mod is not None
                    and consommation_jour_mod is not None and consommation_pointe_ete_mod is not None 
                    and consommation_nuit_mod is not None and consommation_pointe_hiver_mod is not None 
                    and puissance_souscrite_jour_mod is not None and puissance_souscrite_pointe_ete_mod is not None 
                    and puissance_souscrite_nuit_mod is not None and puissance_souscrite_pointe_hiver_mod is not None 
                    and puissance_appelee_max_jour_mod is not None and puissance_appelee_max_pointe_ete_mod is not None 
                    and puissance_appelee_max_nuit_mod is not None and puissance_appelee_max_pointe_hiver_mod is not None 
                    and cos_phi_mod is not None and puissance_reactive_mod is not None):
                    success = modifier_facture_electricite(
                        facture['id'],
                        numero_facture_mod,
                        date_facture_mod.strftime("%Y-%m-%d"),
                        consommation_phase1_mod,
                        consommation_phase2_mod,
                        consommation_phase3_mod,
                        consommation_jour_mod,
                        consommation_pointe_ete_mod,
                        consommation_nuit_mod,
                        consommation_pointe_hiver_mod,
                        puissance_souscrite_jour_mod,
                        puissance_souscrite_pointe_ete_mod,
                        puissance_souscrite_nuit_mod,
                        puissance_souscrite_pointe_hiver_mod,
                        puissance_appelee_max_jour_mod,
                        puissance_appelee_max_pointe_ete_mod,
                        puissance_appelee_max_nuit_mod,
                        puissance_appelee_max_pointe_hiver_mod,
                        cos_phi_mod,
                        puissance_reactive_mod,
                        facture_rectificative_mod,
                        tarif_jour_mod,
                        tarif_pointe_ete_mod,
                        tarif_nuit_mod,
                        tarif_pointe_hiver_mod,
                        avance_mod
                    )
                    
                    if success:
                        st.success("✅ Facture modifiée avec succès!")
                        st.session_state.mode_edition = False
                        st.session_state.facture_edition = None
                        st.rerun()
                    else:
                        st.error("❌ Erreur: Le numéro de facture existe déjà dans la base de données.")
                else:
                    st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
    

# ========== ONGLET 4: SIMULATION ==========
with tab4:
    st.markdown('<h2 class="section-header">🔄 Simulation de Facture</h2>', unsafe_allow_html=True)
    st.info("Simulez le calcul d'une facture en modifiant les paramètres ci-dessous sans l'enregistrer dans la base de données.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1. Consommations (kWh)")
        sim_cj = st.number_input("Jour", 0.0, step=100.0, value=4000.0, key="s_cj")
        sim_cpe = st.number_input("Pointe Été", 0.0, step=100.0, value=2000.0, key="s_cpe")
        sim_cn = st.number_input("Nuit", 0.0, step=100.0, value=3000.0, key="s_cn")
        sim_cph = st.number_input("Pointe Hiver", 0.0, step=100.0, value=1000.0, key="s_cph")
        
        st.markdown("### 3. Puissance Appelée Max (kW) - Pour Pénalités")
        sim_paj = st.number_input("Max Jour", 0.0, step=10.0, value=1200.0, key="s_paj")
        sim_pape = st.number_input("Max Pte Été", 0.0, step=10.0, value=1000.0, key="s_pape")
        sim_pan = st.number_input("Max Nuit", 0.0, step=10.0, value=1000.0, key="s_pan")
        sim_paph = st.number_input("Max Pte Hiver", 0.0, step=10.0, value=1000.0, key="s_paph")

    with col2:
        st.markdown("### 2. Puissance Souscrite (kW)")
        sim_pj = st.number_input("PS Jour", 0.0, step=100.0, value=1200.0, key="s_pj")
        sim_ppe = st.number_input("PS Pte Été", 0.0, step=100.0, value=1200.0, key="s_ppe")
        sim_pn = st.number_input("PS Nuit", 0.0, step=100.0, value=1200.0, key="s_pn")
        sim_pph = st.number_input("PS Pte Hiver", 0.0, step=100.0, value=1200.0, key="s_pph")
        
        st.markdown("### 4. Paramètres")
        sim_cos_phi = st.number_input("Cos Phi", 0.0, 1.0, value=0.9, step=0.01, key="s_cos")
        
        st.markdown("##### Tarifs de Simulation (DT)")
        sim_tj = st.number_input("Tarif Jour", value=0.200, format="%.3f", key="s_tj")
        sim_tpe = st.number_input("Tarif Pte Été", value=0.350, format="%.3f", key="s_tpe")
        sim_tn = st.number_input("Tarif Nuit", value=0.150, format="%.3f", key="s_tn")
        sim_tph = st.number_input("Tarif Pte Hiver", value=0.250, format="%.3f", key="s_tph")

    # Construire le dictionnaire de "facture virtuelle"
    facture_sim = {
        'consommation_jour': sim_cj,
        'consommation_pointe_ete': sim_cpe,
        'consommation_nuit': sim_cn,
        'consommation_pointe_hiver': sim_cph,
        'puissance_souscrite_jour': sim_pj,
        'puissance_souscrite_pointe_ete': sim_ppe,
        'puissance_souscrite_nuit': sim_pn,
        'puissance_souscrite_pointe_hiver': sim_pph,
        'puissance_appelee_max_jour': sim_paj,
        'puissance_appelee_max_pointe_ete': sim_pape,
        'puissance_appelee_max_nuit': sim_pan,
        'puissance_appelee_max_pointe_hiver': sim_paph,
        "tarif_jour": sim_tj,
        "tarif_pointe_ete": sim_tpe,
        "tarif_nuit": sim_tn,
        "tarif_pointe_hiver": sim_tph,
        'cos_phi': sim_cos_phi,
        'avance': 0.0
    }
    
    st.markdown("---")
    st.success("✅ Résultats de la simulation (Mise à jour automatique)")
    afficher_calculs_detailles(facture_sim)
    
    st.markdown("---")
    if st.button("💾 Enregistrer cette Simulation au Journal"):
        try:
             # Generate unique simulation ID
             sim_id = f"SIM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
             today_str = datetime.now().strftime("%Y-%m-%d")
             
             success = ajouter_facture_electricite(
                sim_id,
                today_str,
                0, 0, 0, # Phases (Non simulated -> 0)
                sim_cj, sim_cpe, sim_cn, sim_cph,
                sim_pj, sim_ppe, sim_pn, sim_pph,
                sim_paj, sim_pape, sim_pan, sim_paph,
                sim_cos_phi,
                0.0, # Reactive Power (Default 0)
                False, # Not Rectificative (or should we mark it?)
                sim_tj, sim_tpe, sim_tn, sim_tph,
                0.0, # Avance
                type_facture='Simule' # Flag Simulation
             )
             if success:
                 st.success(f"✅ Simulation enregistrée avec le numéro **{sim_id}**")
                 st.rerun()
             else:
                 st.error("❌ Erreur lors de l'enregistrement.")
                 
        except Exception as e:
            st.error(f"Erreur: {e}")

    # ==========================================
    # 🔍 SECTION OPTIMISATION PUISSANCE SOUSCRITE
    # ==========================================
    st.markdown("---")
    st.markdown("### 🔍 Optimisation automatique Puissance Souscrite")
    st.info("Cet outil simule différentes modifications de votre puissance souscrite (basée sur une année de référence) pour trouver le meilleur équilibre entre le coût de la prime fixe et les pénalités de dépassement.")
    
    # 1. Sélection de l'année de référence (basée sur les factures réelles)
    # On récupère toutes les factures pour extraire les années
    opts_factures = obtenir_toutes_factures_electricite()
    if opts_factures:
        years_avail = sorted(list(set([datetime.strptime(f['date_facture'], "%Y-%m-%d").year for f in opts_factures])), reverse=True)
    else:
        years_avail = []
    
    if not years_avail:
        st.warning("⚠️ Aucune donnée historique pour l'optimisation.")
    else:
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            opt_year = st.selectbox("📅 Choisir l'année de référence", years_avail)
            
        with col_opt2:
            st.write("") # Spacer
            st.write("") 
            run_optim = st.button("🚀 Lancer l'itération & Optimisation", use_container_width=True)
            
        if run_optim:
            # Filtrer les factures de l'année
            year_invoices = [f for f in opts_factures if datetime.strptime(f['date_facture'], "%Y-%m-%d").year == opt_year]
            
            if not year_invoices:
                st.error("Aucune facture trouvée pour cette année.")
            else:
                # 1. Déterminer les Maximas Appelées pour l'année (Profil Réel)
                try:
                    max_paj = max([float(f.get('puissance_appelee_max_jour') or 0) for f in year_invoices])
                    # Gestion nom variable pointe ete parfois differente
                    max_pape = max([float(f.get('puissance_appelee_max_ointe_ete') or f.get('puissance_appelee_max_pointe_ete') or 0) for f in year_invoices])
                    max_pan = max([float(f.get('puissance_appelee_max_nuit') or 0) for f in year_invoices])
                    max_paph = max([float(f.get('puissance_appelee_max_pointe_hiver') or 0) for f in year_invoices])
                    
                    st.success(f"**Profil de consommation {opt_year} analysé.**")
                    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                    col_p1.metric("Max Jour Réel", f"{max_paj} kW")
                    col_p2.metric("Max Pte Été Réel", f"{max_pape} kW")
                    col_p3.metric("Max Nuit Réel", f"{max_pan} kW")
                    col_p4.metric("Max Pte Hiver Réel", f"{max_paph} kW")
                    
                    
                    # A. Courbe Monotone des Puissances
                    st.markdown("#### 1. Analyse de la Donnée d'Entrée (Courbe Monotone)")
                    
                    # Extraire toutes les puissances atteintes (tous mois confondus, toutes périodes)
                    all_powers = []
                    for inv in year_invoices:
                        all_powers.append(float(inv.get('puissance_appelee_max_jour') or 0))
                        all_powers.append(float(inv.get('puissance_appelee_max_pointe_ete') or inv.get('puissance_appelee_max_ointe_ete') or 0))
                        all_powers.append(float(inv.get('puissance_appelee_max_nuit') or 0))
                        all_powers.append(float(inv.get('puissance_appelee_max_pointe_hiver') or 0))
                    
                    # Filtrer les 0 et trier décroissant
                    all_powers = sorted([p for p in all_powers if p > 0], reverse=True)
                    
                    if not all_powers:
                        st.warning("Aucune puissance enregistrée.")
                    else:
                        df_mono = pd.DataFrame({'Puissance (kW)': all_powers, 'Rang': range(1, len(all_powers)+1)})
                        fig_mono = px.area(df_mono, x='Rang', y='Puissance (kW)', title=f"Courbe Monotone des Puissances Appelées ({opt_year})")
                        st.plotly_chart(fig_mono, use_container_width=True)
                        st.info("Cette courbe classe vos pics de puissance du plus haut au plus bas. L'optimisation cherche à 'couper' cette courbe au bon endroit.")

                    # B. Simulation Itérative (Algorithme du Point d'Inflexion)
                    st.markdown("#### 2. Simulation Itérative des Coûts")
                    
                    # Plage de test : De Min/2 à Max*1.2 par pas de 10kW
                    min_test = int(max(all_powers) * 0.4)
                    max_test = int(max(all_powers) * 1.3)
                    step_test = 10 
                    
                    results = []
                    import numpy as np
                    
                    # Fonction Coût Annuel (Logique Validée)
                    def calc_annual_cost(ps_target):
                        # On suppose une PS Uniforme sur les 4 périodes pour simplifier l'analyse graphique
                        # ou on garde la proportionnalité ?
                        # L'algo standard teste souvent une PS unique ou un profil type.
                        # Gardons l'hypothèse d'un profil PROPORTIONNEL au profil actuel des souscriptions
                        # Mais si on optimise, on veut souvent trouver la "PS Souscrite" unique idéale ou ajustée.
                        # Pour simplifier et coller à la demande "Equilibre", on va simuler que l'utilisateur souscrit 'ps_target' partout
                        # OU mieux: on applique un FACTEUR sur son contrat actuel, mais on affiche la PS Jour résultante.
                        
                        # Approche "Factor" (plus réaliste car garde les écarts J/N)
                        factor = ps_target / max_paj if max_paj > 0 else 1
                        
                        ps_j = max_paj * factor
                        ps_ete = max_pape * factor
                        ps_nuit = max_pan * factor
                        ps_hiv = max_paph * factor
                        
                        total_prime = 0
                        total_penalty = 0
                        
                        for inv in year_invoices:
                            # 1. Coût Abonnement (C_fixe)
                            pr = 0.4*ps_hiv + 0.3*ps_ete + 0.2*ps_j + 0.1*ps_nuit
                            prime = pr * 11 
                            
                            # 2. Coût Dépassement (C_depassement)
                            pm_j = float(inv.get('puissance_appelee_max_jour') or 0)
                            pm_ete = float(inv.get('puissance_appelee_max_pointe_ete') or 0)
                            pm_nuit = float(inv.get('puissance_appelee_max_nuit') or 0)
                            pm_hiv = float(inv.get('puissance_appelee_max_pointe_hiver') or 0)
                            
                            exceeds = (pm_nuit > pm_j) or (pm_ete > pm_j) or (pm_hiv > pm_j)
                            penalty_val = 0
                            
                            if exceeds:
                                p_max_critique = max(pm_nuit, pm_ete, pm_hiv)
                                ps_critique = 0.0
                                if pm_nuit == p_max_critique: ps_critique = ps_nuit
                                elif pm_hiv == p_max_critique: ps_critique = ps_hiv
                                elif pm_ete == p_max_critique: ps_critique = ps_ete
                                
                                if p_max_critique > ps_critique:
                                    penalty_val = (p_max_critique - ps_critique) * 28.8
                                else:
                                    penalty_val = (p_max_critique - pr) * 28.8
                            else:
                                hiver_corr = max(pm_hiv, ps_hiv)
                                ete_corr = max(pm_ete, ps_ete)
                                jour_corr = max(pm_j, ps_j)
                                nuit_corr = max(pm_nuit, ps_nuit)
                                pr2 = 0.4*hiver_corr + 0.3*ete_corr + 0.2*jour_corr + 0.1*nuit_corr
                                if pr2 > pr:
                                    penalty_val = (pr2 - pr) * 28.8
                                    
                            total_prime += prime
                            total_penalty += max(0, penalty_val)
                                
                        return total_prime, total_penalty
                    
                    # Boucle
                    ps_range = range(min_test, max_test, step_test)
                    progress_bar = st.progress(0)
                    
                    for i, val_kw in enumerate(ps_range):
                        prime, pen = calc_annual_cost(val_kw)
                        results.append({
                            "Puissance Testée (kW)": val_kw,
                            "Coût Abonnement (C_fixe)": round(prime, 2),
                            "Coût Dépassement (C_var)": round(pen, 2),
                            "Coût Total": round(prime + pen, 2)
                        })
                        progress_bar.progress((i + 1) / len(ps_range))
                    
                    df_res = pd.DataFrame(results)
                    
                    # Optimum
                    opt_row = df_res.loc[df_res['Coût Total'].idxmin()]
                    opt_kw = opt_row['Puissance Testée (kW)']
                    opt_total = opt_row['Coût Total']
                    
                    # Graphique
                    import plotly.express as px
                    df_melt = df_res.melt(id_vars=['Puissance Testée (kW)'], value_vars=['Coût Abonnement (C_fixe)', 'Coût Dépassement (C_var)', 'Coût Total'], var_name='Type de Coût', value_name='Montant Annuel (DT)')
                    
                    fig_opt = px.line(df_melt, x='Puissance Testée (kW)', y='Montant Annuel (DT)', color='Type de Coût', markers=True, 
                                      title=f"Optimisation Tarifaire : Point d'Inflexion ({opt_year})")
                    
                    fig_opt.add_vline(x=opt_kw, line_dash="dash", line_color="green", annotation_text="Optimum Économique")
                    st.plotly_chart(fig_opt, use_container_width=True)
                    
                    # Tableau
                    st.dataframe(df_res.style.highlight_min(subset=['Coût Total'], color='lightgreen'), use_container_width=True)
                    
                    st.success(f"✅ **Point d'Équilibre Optimal : {opt_kw} kW**")
                    st.info(f"En souscrivant cette puissance, vous minimisez la somme (Abonnement + Pénalités) à **{opt_total:,.2f} DT / an**.")
                    
                    # Conclusion
                    ratio_opt = (opt_kw / max_paj) if max_paj > 0 else 0
                    st.success(f"✅ **La Puissance Souscrite Optimale est à ~{int(ratio_opt*100)}% de votre Max Appelé Max Jour.**")
                    st.info(f"Cela représente un Budget Annuel Total de **{opt_total:,.2f} DT** (au lieu de payer plus cher en pénalités ou en prime inutile).")
                    
                except Exception as e:
                    st.error(f"Erreur lors de l'optimisation : {e}")



# ========== ONGLET 5: PREDICTION MACHINE LEARNING ==========
with tab5:
    st.markdown('<h2 class="section-header">📈 Modélisation & Prédiction (Machine Learning)</h2>', unsafe_allow_html=True)
    
    st.info("Cet outil utilise la Régression Linéaire pour modéliser le comportement de votre consommation électrique en fonction de vos variables de production.")
    
    # 1. Chargement et Préparation des Données
    factures = obtenir_toutes_factures_electricite()
    productions = obtenir_toute_production()
    
    if not factures or not productions:
        st.warning("⚠️ Données insuffisantes. Vous devez avoir à la fois des factures d'électricité et des données de production.")
    else:
        df_fac = pd.DataFrame(factures)
        df_prod = pd.DataFrame(productions)
        
        # Préparation Factures (Agréger par Mois/Année)
        df_fac['date_facture'] = pd.to_datetime(df_fac['date_facture'])
        df_fac['periode'] = df_fac['date_facture'].dt.to_period('M')
        # On calcule la consommation totale
        df_fac['cons_totale'] = df_fac.get('consommation_jour', 0) + df_fac.get('consommation_nuit', 0) + df_fac.get('consommation_pointe_ete', 0) + df_fac.get('consommation_pointe_hiver', 0)
        
        # Agréger s'il y a plusieurs factures par mois (normalement non, mais par sécurité)
        df_conso_mensuelle = df_fac.groupby('periode')['cons_totale'].sum().reset_index()
        df_conso_mensuelle = df_conso_mensuelle.rename(columns={'cons_totale': 'Consommation_Electrique_kWh'})
        
        # Préparation Production (Pivot par scope_value pour avoir P1, P2, etc. en colonnes)
        df_prod['date_production'] = pd.to_datetime(df_prod['date_production'])
        df_prod['periode'] = df_prod['date_production'].dt.to_period('M')
        
        # On somme les quantités par période et par produit/scope
        df_prod_grouped = df_prod.groupby(['periode', 'scope_value'])['quantite'].sum().reset_index()
        # Pivot
        df_prod_pivot = df_prod_grouped.pivot(index='periode', columns='scope_value', values='quantite').fillna(0).reset_index()
        
        # Fusion des deux datasets sur la période
        df_ml = pd.merge(df_conso_mensuelle, df_prod_pivot, on='periode', how='inner')
        
        if df_ml.empty or len(df_ml) < 3:
            st.error("Impossible de croiser les données d'Électricité avec la Production sur les mêmes mois.")
        else:
            with st.expander("👀 Voir les données croisées (Électricité & Production)"):
                st.dataframe(df_ml.astype(str)) # Convert to string to avoid arrow serialization issues with Period
            
            st.markdown("---")
            st.markdown("### 1️⃣ Entraînement du Modèle")
            
            col_ml1, col_ml2 = st.columns(2)
            
            # Sélection X et Y
            y_col = 'Consommation_Electrique_kWh'
            x_candidates = [col for col in df_prod_pivot.columns if col != 'periode']
            
            with col_ml1:
                regression_type = st.radio("Type de modèle:", ["Régression Simple (1 variable)", "Régression Multiple (Plusieurs variables)"])
                
            with col_ml2:
                if "Simple" in regression_type:
                    selected_x = st.selectbox("Variable explicative (X) :", x_candidates)
                    x_cols = [selected_x] if selected_x else []
                else:
                    selected_x = st.multiselect("Variables explicatives (X) :", x_candidates, default=x_candidates)
                    x_cols = selected_x
            
            if x_cols and st.button("🚀 Entraîner le Modèle", type="primary"):
                # Préparation Matrices
                X = df_ml[x_cols].values
                y = df_ml[y_col].values
                
                # Entraînement Scikit-Learn
                model = LinearRegression()
                model.fit(X, y)
                y_pred = model.predict(X)
                
                # Métriques
                r2 = r2_score(y, y_pred)
                rmse = np.sqrt(mean_squared_error(y, y_pred))
                
                # Calcul de la corrélation (Pearson)
                correlation_matrix = df_ml[[y_col] + x_cols].corr()
                
                # Sauvegarde en session
                st.session_state['trained_model'] = {
                    'model': model,
                    'features': x_cols,
                    'r2': r2,
                    'rmse': rmse,
                    'coefs': model.coef_,
                    'intercept': model.intercept_
                }
                
                st.success("Modèle entraîné avec succès !")
                
                # Affichage des KPIs
                m1, m2, m3 = st.columns(3)
                m1.metric("Score R² (Précision)", f"{r2*100:.1f} %")
                m2.metric("RMSE (Erreur moyenne)", f"{rmse:,.0f} kWh")
                if len(x_cols) == 1:
                    corr_val = correlation_matrix.loc[y_col, x_cols[0]]
                    m3.metric(f"Corrélation avec {x_cols[0]}", f"{corr_val*100:.1f} %")
                else:
                    m3.metric("Variables utilisées", len(x_cols))
                    
                # Détail de l'équation
                eq = f"Consommation = {model.intercept_:,.0f} "
                for i, col in enumerate(x_cols):
                    eq += f" + ({model.coef_[i]:.2f} × {col})"
                st.info(f"**Équation du modèle :**\n\n`{eq}`")
                
                # Graphiques
                import plotly.express as px
                import plotly.graph_objects as go
                
                st.markdown("#### Visualisation Rélatif vs Prédit")
                
                if len(x_cols) == 1:
                    # Pour la régression simple, on trace la droite de tendance
                    fig_ml = px.scatter(df_ml, x=x_cols[0], y=y_col, title=f"Consommation vs {x_cols[0]}")
                    
                    # Droite de régression
                    x_range = np.linspace(df_ml[x_cols[0]].min(), df_ml[x_cols[0]].max(), 100).reshape(-1, 1)
                    y_range = model.predict(x_range)
                    fig_ml.add_trace(go.Scatter(x=x_range.flatten(), y=y_range, mode='lines', name='Régression', line=dict(color='red')))
                    
                    st.plotly_chart(fig_ml, use_container_width=True)
                else:
                    # Pour la régression multiple, on trace Prédit vs Réel
                    df_viz = pd.DataFrame({'Riel': y, 'Prédit': y_pred})
                    fig_ml = px.scatter(df_viz, x='Riel', y='Prédit', title="Comparaison: Valeurs Réelles vs Prédictions Modèle")
                    # Droite parfaite y=x
                    min_val = min(y.min(), y_pred.min())
                    max_val = max(y.max(), y_pred.max())
                    fig_ml.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode='lines', line=dict(dash='dash', color='red'), name='Parfait'))
                    
                    st.plotly_chart(fig_ml, use_container_width=True)
                    
            # --- ACTION SAUVEGARDE MODEL ---
            if 'trained_model' in st.session_state:
                st.markdown("---")
                if st.button("💾 Enregistrer ce modèle pour usage futur"):
                    os.makedirs("models", exist_ok=True)
                    model_path = "models/electricity_pred_model.pkl"
                    joblib.dump(st.session_state['trained_model'], model_path)
                    st.success(f"Modèle sauvegardé dans `{model_path}` !")
            
            # --- SECTION 2: PREDICITION FUTURE ---
            st.markdown("---")
            st.markdown("### 2️⃣ Faire une Prédiction (Simulateur)")
            
            model_path = "models/electricity_pred_model.pkl"
            if os.path.exists(model_path):
                loaded_data = joblib.load(model_path)
                loaded_model = loaded_data['model']
                loaded_features = loaded_data['features']
                
                st.info(f"Modèle chargé. Variables nécessaires : **{', '.join(loaded_features)}** (Précision R²: {loaded_data['r2']*100:.1f}%)")
                
                with st.form("form_prediction"):
                    cols_pred = st.columns(len(loaded_features))
                    input_vals = {}
                    
                    for i, feat in enumerate(loaded_features):
                        with cols_pred[i]:
                            # Valeur par défaut basique: Moyenne histo
                            avg = df_ml[feat].mean() if feat in df_ml.columns else 0.0
                            input_vals[feat] = st.number_input(f"Production prévue {feat}", value=float(avg), step=1000.0)
                    
                    if st.form_submit_button("🔮 Lancer la Prédiction", use_container_width=True):
                        X_new = [[input_vals[f] for f in loaded_features]]
                        pred_y = loaded_model.predict(X_new)[0]
                        
                        st.success(f"#### ⚡ Consommation Électrique Estimée : **{pred_y:,.0f} kWh**")
                        
                        # Calcul rapido d'impact financier TTC basé sur tarif moyen ?
                        # Just a quick estimate
                        st.caption("Cette estimation est uniquement mathématique basée sur l'historique de vos productions.")
                        
            else:
                st.warning("Aucun modèle sauvegardé. Entraînez et sauvegardez un modèle ci-dessus d'abord.")

