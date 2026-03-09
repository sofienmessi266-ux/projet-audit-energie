import sqlite3

DB_NAME = "audit_energetique.db"

def delete_production():
    print("⚠️ ATTENTION : Vous allez supprimer toutes les données de production/consommation de l'application.")
    confirm = input("Êtes-vous sûr ? (oui/non) : ")
    
    if confirm.lower() == "oui":
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Vérifier que la table existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='production'")
            if cursor.fetchone() is None:
                print("La table de production n'existe pas ou est vide.")
                return

            # Suppression des données
            cursor.execute("DELETE FROM production")
            
            # Optionnel : remettre l'auto-increment des IDs à 0
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='production'")
            
            conn.commit()
            print("✅ Toutes les données de production ont été supprimées.")
            
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la suppression : {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    else:
        print("Opération annulée.")

if __name__ == "__main__":
    delete_production()
