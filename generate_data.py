import random
from datetime import datetime, date
import calendar
from database import init_database, ajouter_facture_electricite, DB_NAME
import os

def generate_data():
    if os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} found.")
    else:
        print(f"Database {DB_NAME} not found, initializing...")
        init_database()

    years = [2022, 2023, 2024]
    
    # Base values for realistic variation
    base_cons_p1 = 3000
    base_cons_p2 = 3200
    base_cons_p3 = 2800
    
    print("Beginning data generation...")
    
    count = 0
    for year in years:
        for month in range(1, 13):
            # Create date for the 15th of each month
            facture_date = date(year, month, 15)
            date_str = facture_date.strftime("%Y-%m-%d")
            
            # Format: FACT-YYYY-MM
            numero_facture = f"FACT-{year}-{month:02d}"
            
            # Add some random variation (SEASONALITY)
            # More consumption in Summer (7, 8) and Winter (1, 2, 12)
            season_factor = 1.0
            if month in [7, 8]: # Summer peak
                season_factor = 1.3
            elif month in [1, 2, 12]: # Winter peak
                season_factor = 1.2
            else:
                season_factor = 0.9
                
            # Random flux +/- 10%
            random_factor = random.uniform(0.9, 1.1)
            
            total_factor = season_factor * random_factor
            
            # Phase consumption
            c_p1 = base_cons_p1 * total_factor
            c_p2 = base_cons_p2 * total_factor
            c_p3 = base_cons_p3 * total_factor
            
            # Time slot consumption (Approximate distribution)
            # Jour ~ 40%, Pointe ~ 20%, Nuit ~ 40%
            total_cons = c_p1 + c_p2 + c_p3
            c_jour = total_cons * 0.45
            c_pointe_ete = total_cons * 0.15 if month in [6, 7, 8, 9] else 0
            c_pointe_hiver = total_cons * 0.15 if month not in [6, 7, 8, 9] else 0
            c_nuit = total_cons - c_jour - c_pointe_ete - c_pointe_hiver
            
            # Power ratings (kW)
            ps_jour = 150
            ps_pointe = 150
            ps_nuit = 150
            
            # Called power (usually slightly less than subscribed)
            pa_jour = ps_jour * random.uniform(0.7, 0.95)
            pa_pointe_ete = ps_pointe * random.uniform(0.7, 0.95) if month in [6, 7, 8, 9] else 0
            pa_pointe_hiver = ps_pointe * random.uniform(0.7, 0.95) if month not in [6, 7, 8, 9] else 0
            pa_nuit = ps_nuit * random.uniform(0.4, 0.6)
            
            # Reactive & Cos Phi
            cos_phi = random.uniform(0.88, 0.98)
            # Q = P * tan(acos(cos_phi)) approximation or just random relation
            puissance_reactive = (total_cons / 720) * 0.4 # Rough estimate average power * ratio
            
            success = ajouter_facture_electricite(
                numero_facture=numero_facture,
                date_facture=date_str,
                consommation_phase1=round(c_p1, 2),
                consommation_phase2=round(c_p2, 2),
                consommation_phase3=round(c_p3, 2),
                consommation_jour=round(c_jour, 2),
                consommation_pointe_ete=round(c_pointe_ete, 2),
                consommation_nuit=round(c_nuit, 2),
                consommation_pointe_hiver=round(c_pointe_hiver, 2),
                puissance_souscrite_jour=ps_jour,
                puissance_souscrite_pointe_ete=ps_pointe,
                puissance_souscrite_nuit=ps_nuit,
                puissance_souscrite_pointe_hiver=ps_pointe,
                puissance_appelee_max_jour=round(pa_jour, 2),
                puissance_appelee_max_pointe_ete=round(pa_pointe_ete, 2),
                puissance_appelee_max_nuit=round(pa_nuit, 2),
                puissance_appelee_max_pointe_hiver=round(pa_pointe_hiver, 2),
                cos_phi=round(cos_phi, 3),
                puissance_reactive=round(puissance_reactive, 2),
                facture_rectificative=False
            )
            
            if success:
                print(f"[+] Facture {numero_facture} ajoutée.")
                count += 1
            else:
                print(f"[-] Erreur/Doublon pour {numero_facture}")

    print(f"Terminé! {count} factures générées.")

if __name__ == "__main__":
    generate_data()
