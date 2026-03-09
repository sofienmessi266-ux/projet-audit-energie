
import sqlite3
import pandas as pd
import numpy as np

DB_NAME = "audit_energetique.db"

def run_diagnostic_optimization():
    print("=== DIAGNOSTIC INDÉPENDANT : OPTIMISATION PUISSANCE ===")
    
    # 1. Charger les factures 2024 (Nos factures de test)
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # On récupère toutes les factures
    cursor.execute("SELECT * FROM factures_electricite")
    all_invoices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Filter Python (2023)
    invoices = []
    for f in all_invoices:
        d = f.get('date_facture') or ""
        if '2023' in d:
            invoices.append(f)
    
    if not invoices:
        print("❌ Aucune facture trouvée pour 2023.")
        return

    print(f"✅ {len(invoices)} factures analysées pour 2023.")
    
    # 2. Extraire Maximas Annuel
    max_paj = max([float(f.get('puissance_appelee_max_jour') or 0) for f in invoices])
    max_pe = max([float(f.get('puissance_appelee_max_pointe_ete') or 0) for f in invoices])
    max_pn = max([float(f.get('puissance_appelee_max_nuit') or 0) for f in invoices])
    max_ph = max([float(f.get('puissance_appelee_max_pointe_hiver') or 0) for f in invoices])
    
    max_global = max(max_paj, max_pe, max_pn, max_ph)
    
    print("-" * 40)
    print(f"Max Réels Observés:")
    print(f"  Jour: {max_paj} kW")
    print(f"  Pte Été: {max_pe} kW")
    print(f"  Nuit: {max_pn} kW")
    print(f"  Pte Hiver: {max_ph} kW")
    print(f"  -> Max Absolu: {max_global} kW")
    print("-" * 40)

    # 3. Simulation Itérative (Range Min -> Max)
    # Range similaire à l'app : 40% du Max à 130% du Max
    start_kw = int(max_global * 0.4)
    end_kw = int(max_global * 1.3)
    step_kw = 10
    
    results = []
    
    for ps_target in range(start_kw, end_kw + 1, step_kw):
        # Hypothèse: On souscrit ps_target * proportionnellement au profil
        # OU Hypothèse "Plate": On souscrit ps_target partout?
        # L'app fait: factor = ps_target / max_paj -> ps_sim = max_reel * factor
        # C'est l'approche "Homothétique".
        
        factor = ps_target / max_paj if max_paj > 0 else 1.0
        
        # Puissances Souscrites Simulées (Proportionnelles)
        ps_j = max_paj * factor
        ps_ete = max_pe * factor
        ps_nuit = max_pn * factor
        ps_hiv = max_ph * factor
        
        total_prime = 0
        total_pen = 0
        
        for inv in invoices:
            # A. Prime (C_fixe)
            pr = 0.4*ps_hiv + 0.3*ps_ete + 0.2*ps_j + 0.1*ps_nuit
            prime = pr * 11 # 11 DT/kW/An (Redevance)
            
            # B. Pénalités (C_var)
            pm_j = float(inv.get('puissance_appelee_max_jour') or 0)
            pm_ete = float(inv.get('puissance_appelee_max_pointe_ete') or 0)
            pm_nuit = float(inv.get('puissance_appelee_max_nuit') or 0)
            pm_hiv = float(inv.get('puissance_appelee_max_pointe_hiver') or 0)
            
            exceeds = (pm_nuit > pm_j) or (pm_ete > pm_j) or (pm_hiv > pm_j)
            penalite_val = 0
            
            if exceeds:
                # Cas Critique
                p_max_critique = max(pm_nuit, pm_ete, pm_hiv)
                ps_critique = 0.0
                if pm_nuit == p_max_critique: ps_critique = ps_nuit
                elif pm_hiv == p_max_critique: ps_critique = ps_hiv
                elif pm_ete == p_max_critique: ps_critique = ps_ete
                
                # Formule corrigée vérifiée
                if p_max_critique > ps_critique:
                    penalite_val = (p_max_critique - ps_critique) * 39.6
                else:
                    penalite_val = (p_max_critique - pr) * 39.6
            else:
                # Cas Classique (Dépassement Jour ou Mixte sans dépasser Jour)
                # En théorie si exceeeds=False, max(autres) <= pm_j.
                # Donc on regarde juste si pm_j > ps_j etc pour le PR calculé
                hiver_corr = max(pm_hiv, ps_hiv)
                ete_corr = max(pm_ete, ps_ete)
                jour_corr = max(pm_j, ps_j)
                nuit_corr = max(pm_nuit, ps_nuit)
                pr2 = 0.4*hiver_corr + 0.3*ete_corr + 0.2*jour_corr + 0.1*nuit_corr
                
                if pr2 > pr:
                    penalite_val = (pr2 - pr) * 39.6
            
            total_prime += prime
            total_pen += max(0, penalite_val)
            
        total_cost = total_prime + total_pen
        results.append({
            "kw": ps_target,
            "fixe": total_prime,
            "var": total_pen,
            "total": total_cost
        })
        
    # Trouver l'Optimum
    df = pd.DataFrame(results)
    opt_row = df.loc[df['total'].idxmin()]
    
    print("-" * 40)
    print("RÉSULTATS DE L'OPTIMISATION:")
    print(f"  Plage Testée: {start_kw} kW à {end_kw} kW")
    print(f"  Pas: {step_kw} kW")
    print(f"-> OPTIMUM TROUVÉ : {int(opt_row['kw'])} kW")
    print(f"   Coût Fixe (Abo): {opt_row['fixe']:.2f} DT")
    print(f"   Coût Var (Pen):  {opt_row['var']:.2f} DT")
    print(f"   COÛT TOTAL :     {opt_row['total']:.2f} DT")
    print("-" * 40)
    
    # Afficher quelques points autour (pour voir la courbe en U)
    idx_opt = df['total'].idxmin()
    subset = df.iloc[max(0, idx_opt-2): min(len(df), idx_opt+3)]
    print("Voisinage de l'Optimum:")
    print(subset.to_string(index=False))

if __name__ == "__main__":
    run_diagnostic_optimization()
