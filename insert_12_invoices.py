
import sqlite3
import random
from datetime import datetime
from database import ajouter_facture_electricite

def generate_full_year_2023():
    print("Génération de 12 factures simulées pour l'année 2023...")
    
    # Configuration de base
    year = 2023
    ps_avg = 800 # Puissance Souscrite Moyenne
    conso_base = 80000 # Conso mensuelle moyenne hors pointe
    
    # Tarifs (Confirmés)
    tarifs = {
        "tarif_jour": 0.265,
        "tarif_pointe_ete": 0.351,
        "tarif_nuit": 0.197,
        "tarif_pointe_hiver": 0.394
    }
    
    # Contrat (Fixe sur l'année pour simplifier l'optimisation)
    contract = {
        "puissance_souscrite_jour": ps_avg,
        "puissance_souscrite_pointe_ete": ps_avg,
        "puissance_souscrite_nuit": int(ps_avg * 0.95), # Souvent un peu moins la nuit
        "puissance_souscrite_pointe_hiver": int(ps_avg * 0.98)
    }
    
    months = range(1, 13)
    
    for m in months:
        date_str = f"{year}-{m:02d}-28"
        num_fact = f"SIM-FULL-{year}-{m:02d}"
        
        # Facteurs Saisonniers
        is_summer = m in [6, 7, 8, 9]
        is_winter = m in [12, 1, 2]
        
        # 1. Consommation (Variation Saisonnière)
        # Eté: Grosse conso Clim (Pointe Eté + Jour)
        # Hiver: Chauffage/Process (Pointe Hiver)
        # Inter-saison: Plus calme
        
        if is_summer:
            factor = 1.4
            conso_j = conso_base * factor * random.uniform(0.9, 1.1)
            conso_pe = conso_base * 0.5 * factor * random.uniform(0.9, 1.1)
            conso_ph = 0
            conso_n = conso_base * 1.1 * random.uniform(0.95, 1.05)
        elif is_winter:
            factor = 1.2
            conso_j = conso_base * factor * random.uniform(0.9, 1.1)
            conso_pe = 0
            conso_ph = conso_base * 0.4 * factor * random.uniform(0.9, 1.1)
            conso_n = conso_base * 1.0 * random.uniform(0.95, 1.05)
        else:
            factor = 0.9
            conso_j = conso_base * factor * random.uniform(0.9, 1.0)
            conso_pe = 0
            conso_ph = 0
            conso_n = conso_base * 0.9 * random.uniform(0.9, 1.0)
            
        # 2. Puissance Appelée (Peaks)
        # On simule des dépassements aléatoires pour tester l'algo d'optimisation
        # Eté: Peak fort Jour/Pte Eté
        # Nuit: Peak constant (Machines?)
        
        pm = ps_avg * 0.8 # Base charge
        
        if is_summer:
            pm_j = ps_avg * random.uniform(0.9, 1.2) # Parfois dépasse
            pm_ete = ps_avg * random.uniform(0.8, 1.15)
            pm_ph = 0
        elif is_winter:
            pm_j = ps_avg * random.uniform(0.8, 1.0)
            pm_ete = 0
            pm_ph = ps_avg * random.uniform(0.7, 1.05)
        else:
            pm_j = ps_avg * random.uniform(0.6, 0.9)
            pm_ete = 0
            pm_ph = 0
            
        pm_nuit = ps_avg * random.uniform(0.7, 1.1) # La nuit peut dépasser toute l'année
        
        # Insertion
        success = ajouter_facture_electricite(
            numero_facture=num_fact,
            date_facture=date_str,
            consommation_phase1=0, consommation_phase2=0, consommation_phase3=0,
            
            consommation_jour=int(conso_j),
            consommation_pointe_ete=int(conso_pe),
            consommation_nuit=int(conso_n),
            consommation_pointe_hiver=int(conso_ph),
            
            puissance_souscrite_jour=contract["puissance_souscrite_jour"],
            puissance_souscrite_pointe_ete=contract["puissance_souscrite_pointe_ete"],
            puissance_souscrite_nuit=contract["puissance_souscrite_nuit"],
            puissance_souscrite_pointe_hiver=contract["puissance_souscrite_pointe_hiver"],
            
            puissance_appelee_max_jour=round(pm_j, 1),
            puissance_appelee_max_pointe_ete=round(pm_ete, 1),
            puissance_appelee_max_nuit=round(pm_nuit, 1),
            puissance_appelee_max_pointe_hiver=round(pm_ph, 1),
            
            cos_phi=random.uniform(0.88, 0.98),
            puissance_reactive=0,
            facture_rectificative=False,
            
            tarif_jour=tarifs["tarif_jour"],
            tarif_pointe_ete=tarifs["tarif_pointe_ete"],
            tarif_nuit=tarifs["tarif_nuit"],
            tarif_pointe_hiver=tarifs["tarif_pointe_hiver"],
            
            avance=0,
            type_facture='Simule'
        )
        
        if success:
            print(f"Mois {m:02d} : OK")
        else:
            print(f"Mois {m:02d} : Erreur/Existe")

if __name__ == "__main__":
    generate_full_year_2023()
