
import pandas as pd

# DONNEES ENTREES
data = {
    # Puissances Souscrites (kW)
    'puissance_souscrite_jour': 800,
    'puissance_souscrite_pointe_ete': 800,
    'puissance_souscrite_nuit': 770,
    'puissance_souscrite_pointe_hiver': 790,
    
    # Puissances Max Appelées (kW)
    # Puissances Max Appelées (kW)
    # Puissances Max Appelées (kW)
    # Puissances Max Appelées (kW)
    # Puissances Max Appelées (kW)
    # Puissances Max Appelées (kW)
    # Facture 5
    'puissance_appelee_max_jour': 800, 
    'puissance_appelee_max_pointe_ete': 786,
    'puissance_appelee_max_nuit': 845,
    'puissance_appelee_max_pointe_hiver': 0,
    
    # Consommations (kWh)
    'consommation_jour': 63515,
    'consommation_pointe_ete': 28312,
    'consommation_nuit': 96027,
    'consommation_pointe_hiver': 20900, 
    
    # Autres
    'cos_phi': 1.0,
    'taux_tva': 19.0, # Standard
    'taxe_mun': 0.01, 
    'tarif_jour': 0.265,
    'tarif_pointe_ete': 0.351, # Correction (était 0.394)
    'tarif_nuit': 0.197,
    'tarif_pointe_hiver': 0.394 # Correction (était 0.351)
}

# --- LOGIQUE DE CALCUL (COPIE DE L'APP) ---

def run_diagnostic():
    lines = []
    def log(msg):
        lines.append(msg)
        print(msg)

    log("=== RAPPORT DIAGNOSTIC FACTURE ===")
    log("DONNEES ENTREES:")
    for k, v in data.items():
        log(f"  {k}: {v}")
    log("-" * 30)

    # 1. Puissance Réduite (PR)
    ps_j = data['puissance_souscrite_jour']
    ps_ete = data['puissance_souscrite_pointe_ete']
    ps_nuit = data['puissance_souscrite_nuit']
    ps_hiv = data['puissance_souscrite_pointe_hiver']
    
    pr_calc = 0.4*ps_hiv + 0.3*ps_ete + 0.2*ps_j + 0.1*ps_nuit
    log(f"1. Puissance Réduite (PR): {pr_calc:.3f} kW")
    log(f"   (Attendu: 793 kW -> {abs(pr_calc - 793) < 0.01})")
    
    # 2. Prime de Puissance
    prime = pr_calc * 11 # Hypothèse 11 DT/kW
    # Si tarif prime different: redevance fixe?
    # Code uses 11 currently.
    log(f"2. Prime de Puissance (Fixe): {prime:.3f} DT   (PR * 11)")

    # 3. Coût Consommation
    cout_j = data['consommation_jour'] * data['tarif_jour']
    cout_pe = data['consommation_pointe_ete'] * data['tarif_pointe_ete']
    cout_n = data['consommation_nuit'] * data['tarif_nuit']
    cout_ph = data['consommation_pointe_hiver'] * data['tarif_pointe_hiver']
    cout_conso_total = cout_j + cout_pe + cout_n + cout_ph
    
    log(f"3. Coût Consommation Hors Taxes: {cout_conso_total:.3f} DT")
    log(f"   - Jour: {cout_j:.3f}")
    log(f"   - Pointe Ete: {cout_pe:.3f}")
    log(f"   - Nuit: {cout_n:.3f}")
    log(f"   - Pointe Hiver: {cout_ph:.3f}")

    # 4. Impact Cos Phi (Bonus/Malus)
    cos_phi = data['cos_phi']
    impact_cos = 0.0
    if cos_phi > 0.9:
        # Bonus: (0.5 * cos - 0.45) * M
        impact_cos = (0.5 * cos_phi - 0.45) * cout_conso_total
        type_imp = "BONUS (A DEDUIRE)"
    elif cos_phi > 0.8:
        impact_cos = 0.0
        type_imp = "NEUTRE"
    else:
        # Malus calculation
        if cos_phi >= 0.74:
             impact_cos = -0.5 * (0.8 - cos_phi) * cout_conso_total
        else:
             impact_cos = -(0.775 - cos_phi) * cout_conso_total
        type_imp = "MALUS (A AJOUTER - Negatif ici)"
        
    log(f"4. Cos Phi ({cos_phi}): {type_imp}")
    log(f"   Impact Calculé: {impact_cos:.3f} DT")
    # Note: Dans code app, malus_bonus_cosphi est Positif pour Bonus, Negatif pour Malus.
    # Dans la formule HT: Prime + Penalite - Impact + Conso.
    # Si Bonus (Positif): - (+Impact) -> Déduction. Correct.
    
    # 5. Pénalités Dépassement
    pm_j = data['puissance_appelee_max_jour']
    pm_ete = data['puissance_appelee_max_pointe_ete']
    pm_nuit = data['puissance_appelee_max_nuit']
    pm_hiv = data['puissance_appelee_max_pointe_hiver']
    
    exceeds = (pm_nuit > pm_j) or (pm_ete > pm_j) or (pm_hiv > pm_j)
    penalite = 0.0
    
    log(f"5. Dépassement Puissance:")
    log(f"   Max Jour: {pm_j}, Max Pte: {max(pm_ete, pm_hiv)}, Max Nuit: {pm_nuit}")
    if exceeds:
        p_max_critique = max(pm_nuit, pm_ete, pm_hiv)
        log(f"   -> CAS 1: Dépassement Jour ({p_max_critique} > {pm_j})")
        # HYPOTHESE UTILISATEUR: On compare a la PS de la periode critique
        ps_critique = 0
        if pm_nuit == p_max_critique: ps_critique = ps_nuit
        elif pm_hiv == p_max_critique: ps_critique = ps_hiv
        elif pm_ete == p_max_critique: ps_critique = ps_ete
        
        log(f"      Calcul: (Max {p_max_critique} - PS_Periode {ps_critique}) * 39.6 (11*12/3.3333)")
        if p_max_critique > ps_critique:
             penalite = (p_max_critique - ps_critique) * 39.6
    else:
        log(f"   -> CAS 2: Pas de dépassement du Jour par les autres périodes")
        hiver_corr = max(pm_hiv, ps_hiv)
        ete_corr = max(pm_ete, ps_ete)
        jour_corr = max(pm_j, ps_j)
        nuit_corr = max(pm_nuit, ps_nuit)
        pr2 = 0.4*hiver_corr + 0.3*ete_corr + 0.2*jour_corr + 0.1*nuit_corr
        
        log(f"   PR2 Calculé (Base MaxvsSouscrite): {pr2:.3f}")
        if pr2 > pr_calc:
             penalite = (pr2 - pr_calc) * 39.6
             log(f"   Pénalité = ({pr2:.3f} - {pr_calc:.3f}) * 39.6")
        else:
             penalite = 0.0
             
    log(f"   Montant Pénalité: {penalite:.3f} DT")
    
    # 6. TOTAL HT
    montant_ht = prime + penalite - impact_cos + cout_conso_total
    log(f"6. TOTAL HT: {montant_ht:.3f} DT")
    log(f"   (Prime {prime:.2f} + Pen {penalite:.2f} - Bonus {impact_cos:.2f} + Conso {cout_conso_total:.2f})")
    
    
    # 7. TAXES
    tva_conso = cout_conso_total * (data['taux_tva'] / 100.0)
    tva_redevance = (prime + penalite) * (data['taux_tva'] / 100.0)
    
    conso_totale = data['consommation_jour'] + data['consommation_pointe_ete'] + data['consommation_nuit'] + data['consommation_pointe_hiver']
    taxe_mun = conso_totale * data['taxe_mun']
    fte = 3.500
    
    log(f"7. TAXES:")
    log(f"   TVA Consommation (19%): {tva_conso:.3f} DT")
    log(f"   TVA Redevance (19% sur Prime+Pen): {tva_redevance:.3f} DT")
    log(f"   Taxe Municipale (10 millimes/kWh): {taxe_mun:.3f} DT")
    log(f"   FTE: {fte:.3f} DT")
    
    # 8. TOTAL TTC
    # Formule app: HT + TVA_Conso + TVA_Redevance + Taxe_Mun + FTE - Avance (0)
    total_ttc = montant_ht + tva_conso + tva_redevance + taxe_mun + fte
    
    log(f"8. TOTAL TTC: {total_ttc:.3f} DT")
    
    # 9. FACTURE UNIFORME (Simulation)
    # Formule: (Total_Active * Tarif_Uniform) + ((PR/0.7)*(5/CosPhi)) + 5 + (Total_Active * 0.006) - Impact_CosPhi
    tarif_uni = 0.255
    terme_conso_uni = conso_totale * tarif_uni
    terme_puiss_uni = (pr_calc / 0.7) * (5 / cos_phi) if cos_phi > 0 else 0
    terme_fixe_uni = 5.0
    # Taxe Mun deja calculed (taxe_mun)
    
    # Impact Cos Phi sign: We use 'impact_cos'.
    # In main calc: HT = ... - impact_cos.
    # In Uniforme calc: Total = ... - impact_cos.
    # (If Bonus +, we deduct. If Malus -, we add cost? Wait. Malus is negative number in my code.
    # Base - (-Malus) -> Base + Cost. Correct.
    # Base - (+Bonus) -> Base - Cost. Correct.)
    
    facture_uniforme = terme_conso_uni + terme_puiss_uni + terme_fixe_uni + taxe_mun - impact_cos
    
    log(f"-" * 30)
    log(f"9. FACTURE UNIFORME (SIMULATION):")
    log(f"   Tarif Unique: {tarif_uni} DT/kWh")
    log(f"   Terme Conso: {terme_conso_uni:.3f} DT")
    log(f"   Terme Puissance ((PR/0.7)*(5/Cos)): {terme_puiss_uni:.3f} DT")
    log(f"   Terme Fixe: {terme_fixe_uni} DT")
    log(f"   -> TOTAL UNIFORME: {facture_uniforme:.3f} DT")
    log(f"   (Comparaison: TTC Reel = {total_ttc:.3f} DT)")
    
    if facture_uniforme < total_ttc:
        log("   ✅ LE TARIF UNIFORME SERAIT PLUS AVANTAGEUX !")
    else:
        log("   ❌ LE TARIF ACTUEL EST MEILLEUR.")

    with open("diagnostic_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    run_diagnostic()
