import sqlite3
from datetime import datetime, date
from database import ajouter_facture_electricite, init_database

init_database()

def insert_unbalanced_invoice():
    print("--- Insertion d'une facture DÉSÉQUILIBRÉE ---")
    
    # Données de test
    numero = "TEST-UNBALANCED"
    date_f = "2025-02-01"
    
    # Consommations DÉSÉQUILIBRÉES
    c_p1 = 120.0  # +20% vs avg
    c_p2 = 80.0   # -20% vs avg
    c_p3 = 100.0  # = avg
    # Avg = 100
    
    # Autres
    c_jour = 300.0
    c_pte_ete = 0.0
    c_nuit = 0.0
    c_pte_hiver = 0.0
    
    ps_jour = 100.0
    ps_pte_ete = 100.0
    ps_nuit = 100.0
    ps_pte_hiver = 100.0
    
    pa_jour = 100.0
    pa_pte_ete = 100.0
    pa_nuit = 100.0
    pa_pte_hiver = 100.0
    
    cos_phi = 0.95
    p_react = 10.0
    facture_rectif = False
    
    t_jour = 0.200
    t_pte_ete = 0.0
    t_nuit = 0.0
    t_pte_hiver = 0.0
    
    avance = 0.0

    success = ajouter_facture_electricite(
        numero, date_f,
        c_p1, c_p2, c_p3,
        c_jour, c_pte_ete, c_nuit, c_pte_hiver,
        ps_jour, ps_pte_ete, ps_nuit, ps_pte_hiver,
        pa_jour, pa_pte_ete, pa_nuit, pa_pte_hiver,
        cos_phi, p_react, facture_rectif,
        t_jour, t_pte_ete, t_nuit, t_pte_hiver,
        avance
    )

    if success:
        print(f"✅ Facture {numero} ajoutée. Attendu: P1=+20%, P2=-20%, P3=0%")
    else:
        print(f"❌ Erreur ajout {numero}.")

if __name__ == "__main__":
    insert_unbalanced_invoice()
