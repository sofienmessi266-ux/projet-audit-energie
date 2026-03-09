import sqlite3
import sys

DB_NAME = "audit_energetique.db"

def delete_factures():
    print("⚠️ ATTENTION : Vous allez supprimer toutes les factures d'électricité.")
    confirm = input("Êtes-vous sûr ? (oui/non) : ")
    
    if confirm.lower() == "oui":
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Suppression des données (garde la structure de la table)
            cursor.execute("DELETE FROM factures_electricite")
            
            # Optionnel : remettre l'auto-increment des IDs à 0
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='factures_electricite'")
            
            conn.commit()
            print("✅ Toutes les factures d'électricité ont été supprimées.")
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la suppression : {e}")
        finally:
            if conn:
                conn.close()
    else:
        print("Opération annulée.")

if __name__ == "__main__":
    delete_factures()
