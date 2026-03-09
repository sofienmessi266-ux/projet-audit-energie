
import sqlite3
from database import ajouter_facture_electricite

def insert_batch():
    print("Insertion des 5 factures du diagnostic...")
    
    # Paramètres Communs (Dernière version validée)
    params_communs = {
        # Tarifs
        "tarif_jour": 0.265,
        "tarif_pointe_ete": 0.351,
        "tarif_nuit": 0.197,
        "tarif_pointe_hiver": 0.394,
        # Taxes embedded in app logic often, but DB stores tariff. 
        # Note: Taxe mun is usually calculated, not stored per invoice in legacy schema unless 'avance' or similar used, 
        # but the app Logic uses the constants in the code. 
        # We just insert the raw data.
    }
    
    # PS (Contrat)
    ps = {
        "puissance_souscrite_jour": 800,
        "puissance_souscrite_pointe_ete": 800,
        "puissance_souscrite_nuit": 770,
        "puissance_souscrite_pointe_hiver": 790
    }
    
    # Factures
    invoices = [
        {
            "num": "FACT-DIAG-01", "date": "2024-01-28",
            "conso": (135475, 36784, 143017, 0), # J, PE, N, PH
            "power": (1393.91, 824, 744, 0), # Max J, PE, N, PH (Using verified logic)
            "cos": 0.91
        },
        {
            "num": "FACT-DIAG-02", "date": "2024-02-28",
            "conso": (117997, 31842, 119170, 0),
            "power": (748, 0, 0, 634),
            "cos": 0.90
        },
        {
            "num": "FACT-DIAG-03", "date": "2024-03-28",
            "conso": (75658, 41830, 119127, 33803),
            "power": (801, 775, 854, 0),
            "cos": 0.92
        },
        {
            "num": "FACT-DIAG-04", "date": "2024-04-28",
            "conso": (158249, 26886, 164658, 0),
            "power": (843, 0, 781, 0),
            "cos": 0.90
        },
        {
            "num": "FACT-DIAG-05", "date": "2024-05-28",
            "conso": (63515, 28312, 96027, 20900),
            "power": (800, 786, 845, 0),
            "cos": 1.0
        }
    ]
    
    for inv in invoices:
        cj, cpe, cn, cph = inv["conso"]
        pj, ppe, pn, pph = inv["power"]
        
        # We assume database.py handles the connection internally
        success = ajouter_facture_electricite(
            numero_facture=inv["num"],
            date_facture=inv["date"],
            # Phases (0)
            consommation_phase1=0, consommation_phase2=0, consommation_phase3=0,
            
            # Conso
            consommation_jour=cj,
            consommation_pointe_ete=cpe,
            consommation_nuit=cn,
            consommation_pointe_hiver=cph,
            
            # PS
            puissance_souscrite_jour=ps["puissance_souscrite_jour"],
            puissance_souscrite_pointe_ete=ps["puissance_souscrite_pointe_ete"],
            puissance_souscrite_nuit=ps["puissance_souscrite_nuit"],
            puissance_souscrite_pointe_hiver=ps["puissance_souscrite_pointe_hiver"],
            
            # Power Max
            puissance_appelee_max_jour=pj,
            puissance_appelee_max_pointe_ete=ppe,
            puissance_appelee_max_nuit=pn,
            puissance_appelee_max_pointe_hiver=pph,
            
            # Other
            cos_phi=inv["cos"],
            puissance_reactive=0,
            facture_rectificative=False,
            
            # Tarifs
            tarif_jour=params_communs["tarif_jour"],
            tarif_pointe_ete=params_communs["tarif_pointe_ete"],
            tarif_nuit=params_communs["tarif_nuit"],
            tarif_pointe_hiver=params_communs["tarif_pointe_hiver"],
            
            avance=0,
            type_facture='Simule' # Marqué comme Simulé pour ne pas polluer le Réel
        )
        
        if success:
            print(f"✅ Facture {inv['num']} insérée.")
        else:
            print(f"❌ Erreur insertion {inv['num']} (Existe déjà?)")

if __name__ == "__main__":
    insert_batch()
