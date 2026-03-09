import sqlite3
import os

DB_NAME = "audit_energetique.db"

def fix_schema():
    print(f"Connecting to {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("Attempting to add 'type_facture' column...")
        cursor.execute("ALTER TABLE factures_electricite ADD COLUMN type_facture TEXT DEFAULT 'Reel'")
        print("Column 'type_facture' added successfully.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e} (Column might already exist)")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.commit()
    conn.close()
    print("Schema update finished.")

if __name__ == "__main__":
    fix_schema()
