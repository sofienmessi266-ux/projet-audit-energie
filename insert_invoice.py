import sqlite3
from datetime import datetime, date
from database import ajouter_facture_electricite, init_database

# Initialiser la base si nécessaire
init_database()

def insert_test_invoice():
    print("--- Insertion d'une facture de test ---")
    
    # Données de test
    numero = "TEST-2025-01"
    date_f = date.today().strftime("%Y-%m-%d")
    
    # Consommations
    c_p1 = 100.0
    c_p2 = 100.0
    c_p3 = 100.0
    c_jour = 150.0
    c_pte_ete = 50.0
    c_nuit = 80.0
    c_pte_hiver = 20.0
    
    # Puissances Souscrites
    ps_jour = 100.0
    ps_pte_ete = 100.0
    ps_nuit = 100.0
    ps_pte_hiver = 100.0
    
    # Puissances Appelées Max
    pa_jour = 80.0
    pa_pte_ete = 90.0
    pa_nuit = 40.0
    pa_pte_hiver = 30.0
    
    # Autres
    cos_phi = 0.95
    p_react = 10.0
    facture_rectif = False
    
    # Tarifs (Optionnel, sinon 0)
    t_jour = 0.200
    t_pte_ete = 0.300
    t_nuit = 0.150
    t_pte_hiver = 0.250
    
    # Avance (Nouveau champ)
    avance = 50.0

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
        print(f"✅ Facture {numero} ajoutée avec succès !")
    else:
        print(f"❌ Erreur lors de l'ajout de la facture {numero} (Existe peut-être déjà).")

if __name__ == "__main__":
    insert_test_invoice()
