import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "audit_energetique.db"

def generate_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Start date: 3 years ago (2022, 2023, 2024)
    start_date = datetime(2022, 1, 1)
    
    print("Generating 36 simulated invoices (2022-2024)...")
    
    # Tarifs Validés
    tarifs = {
        "tarif_jour": 0.265,
        "tarif_pointe_ete": 0.351,
        "tarif_nuit": 0.197,
        "tarif_pointe_hiver": 0.394
    }

    for i in range(36):
        # Calculate date
        year = 2022 + (i // 12)
        month = (i % 12) + 1
        date_str = f"{year}-{month:02d}-28"
        
        # Seasonality (Summer peak)
        is_summer = month in [6, 7, 8, 9]
        seasonal_factor = 1.4 if is_summer else 1.0 # Adjusted factor
        
        # Base consumption
        base_conso = 60000 # More realistic industrial load (was 3000)
        
        # Data
        cons_jour = int(base_conso * (1.2 if is_summer else 1.0) * random.uniform(0.9, 1.1))
        cons_nuit = int(base_conso * 1.1 * random.uniform(0.95, 1.05))
        cons_pe = int(base_conso * 0.5 * seasonal_factor * random.uniform(0.9, 1.1)) if is_summer else 0
        cons_ph = int(base_conso * 0.4 * random.uniform(0.9, 1.1)) if not is_summer else 0
        
        # Power
        ps_base = 800
        pa_max = ps_base * random.uniform(0.7, 1.05)
        if is_summer: pa_max *= 1.15 # Peak overruns
        
        num_facture = f"SIM-3Y-{year}-{month:02d}"
        
        # Check duplicate
        cursor.execute("SELECT id FROM factures_electricite WHERE numero_facture = ?", (num_facture,))
        if cursor.fetchone():
            print(f"Skipping {num_facture} (Exists)")
            # Update content anyway? No, keeping it simple.
            continue
            
        sql = '''
            INSERT INTO factures_electricite (
                numero_facture, date_facture, 
                consommation_phase1, consommation_phase2, consommation_phase3,
                consommation_jour, consommation_pointe_ete, consommation_nuit, consommation_pointe_hiver,
                puissance_souscrite_jour, puissance_souscrite_pointe_ete, puissance_souscrite_nuit, puissance_souscrite_pointe_hiver,
                puissance_appelee_max_jour, puissance_appelee_max_pointe_ete, puissance_appelee_max_nuit, puissance_appelee_max_pointe_hiver,
                cos_phi, puissance_reactive, facture_rectificative,
                tarif_jour, tarif_pointe_ete, tarif_nuit, tarif_pointe_hiver,
                avance, type_facture
            ) VALUES (?, ?, 0,0,0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, 0, 'Simule')
        '''
        
        cursor.execute(sql, (
            num_facture, date_str,
            cons_jour, cons_pe, cons_nuit, cons_ph,
            ps_base, ps_base, int(ps_base*0.95), int(ps_base*0.98),
            round(pa_max, 1), round(pa_max if is_summer else 0, 1), round(pa_max*0.9, 1), round(pa_max if not is_summer else 0, 1),
            random.uniform(0.88, 0.99), # Cos Phi
            tarifs["tarif_jour"], tarifs["tarif_pointe_ete"], tarifs["tarif_nuit"], tarifs["tarif_pointe_hiver"]
        ))
        
    conn.commit()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    generate_data()
