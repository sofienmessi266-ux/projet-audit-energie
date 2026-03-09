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
