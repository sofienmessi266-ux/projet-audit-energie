import sqlite3
import datetime

DB_NAME = "audit_energetique.db"

def insert_scenario_invoice():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if invoice exists to avoid duplicates
    c.execute("SELECT id FROM factures_electricite WHERE numero_facture = ?", ('SCENARIO-TEST-001',))
    if c.fetchone():
        print("Facture de scénario existe déjà. Suppression...")
        c.execute("DELETE FROM factures_electricite WHERE numero_facture = ?", ('SCENARIO-TEST-001',))
        conn.commit()

    # Data based on User Request:
    # Cos Phi = 0.5
    # PS = 1200 everywhere
    # Depassement Jour = 100 => PM Jour = 1300
    # Calculations will handle the rest.
    
    data = {
        "numero_facture": "SCENARIO-TEST-001",
        "date_facture": datetime.date.today().strftime("%Y-%m-%d"),
        "consommation_phase1": 3000,
        "consommation_phase2": 3500,
        "consommation_phase3": 3500,
        "consommation_jour": 4000,
        "consommation_pointe_ete": 2000,
        "consommation_nuit": 3000,
        "consommation_pointe_hiver": 1000,
        "puissance_souscrite_jour": 1200,
        "puissance_souscrite_pointe_ete": 1200,
        "puissance_souscrite_nuit": 1200,
        "puissance_souscrite_pointe_hiver": 1200,
        "puissance_appelee_max_jour": 1300, # EXCEEDANCE Here (1300 > 1200)
        "puissance_appelee_max_pointe_ete": 1100,
        "puissance_appelee_max_nuit": 1000,
        "puissance_appelee_max_pointe_hiver": 1000,
        "cos_phi": 0.5, # MALUS
        "puissance_reactive": 5000, # High reactive power typically leads to low Cos Phi
        "facture_rectificative": 0,
        "avance": 0.0
    }
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    sql = f"INSERT INTO factures_electricite ({columns}) VALUES ({placeholders})"
    
    try:
        c.execute(sql, list(data.values()))
        conn.commit()
        print(f"Facture SCENARIO-TEST-001 insérée avec succès.")
        print(f"Données: CosPhi={data['cos_phi']}, PS={data['puissance_souscrite_jour']}, PM_Jour={data['puissance_appelee_max_jour']}")
    except Exception as e:
        print(f"Erreur insertion: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    insert_scenario_invoice()
