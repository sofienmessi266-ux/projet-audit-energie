import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_NAME = "audit_energetique.db"

def init_database():
    """Initialise la base de données et crée les tables nécessaires"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table pour les factures d'électricité
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factures_electricite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_facture TEXT UNIQUE NOT NULL,
            date_facture DATE NOT NULL,
            consommation_phase1 REAL,
            consommation_phase2 REAL,
            consommation_phase3 REAL,
            consommation_jour REAL,
            consommation_pointe_ete REAL,
            consommation_nuit REAL,
            consommation_pointe_hiver REAL,
            puissance_souscrite_jour REAL,
            puissance_souscrite_pointe_ete REAL,
            puissance_souscrite_nuit REAL,
            puissance_souscrite_pointe_hiver REAL,
            puissance_appelee_max_jour REAL,
            puissance_appelee_max_pointe_ete REAL,
            puissance_appelee_max_nuit REAL,
            puissance_appelee_max_pointe_hiver REAL,
            cos_phi REAL,
            puissance_reactive REAL,
            facture_rectificative INTEGER DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migration : Ajouter les nouvelles colonnes si elles n'existent pas
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_phase1 REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_phase2 REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_phase3 REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_reactive REAL')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN avance REAL')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE factures_electricite ADD COLUMN type_facture TEXT DEFAULT 'Reel'")
    except sqlite3.OperationalError:
        pass
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_jour REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_pointe_ete REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_nuit REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN consommation_pointe_hiver REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_souscrite_jour REAL')
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_souscrite_pointe_ete REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_souscrite_nuit REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_souscrite_pointe_hiver REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_appelee_max_jour REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_appelee_max_pointe_ete REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_appelee_max_nuit REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_appelee_max_pointe_hiver REAL')
    except sqlite3.OperationalError:
        pass
        
    # --- Tarification ---
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN tarif_jour REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN tarif_pointe_ete REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN tarif_nuit REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN tarif_pointe_hiver REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN cos_phi REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN puissance_reactive REAL')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE factures_electricite ADD COLUMN facture_rectificative INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    # Note: SQLite ne supporte pas DROP COLUMN directement
    # Les anciennes colonnes (puissance_souscrite, puissance_appelee) resteront mais ne seront plus utilisées
    
    # Table pour les factures de gaz (pour plus tard)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factures_gaz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_facture TEXT UNIQUE NOT NULL,
            date_facture DATE NOT NULL,
            consommation REAL NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table pour les factures de gazoil (pour plus tard)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factures_gazoil (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_facture TEXT UNIQUE NOT NULL,
            date_facture DATE NOT NULL,
            consommation REAL NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    

    # Table pour la production
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_production DATE NOT NULL,
            unite_mesure TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            scope_value TEXT NOT NULL,
            quantite REAL NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# ... existing electricity functions ...

def ajouter_production(
    date_production: str,
    unite_mesure: str,
    scope_type: str,
    scope_value: str,
    quantite: float
) -> bool:
    """Ajoute une entrée de production"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO production 
            (date_production, unite_mesure, scope_type, scope_value, quantite)
            VALUES (?, ?, ?, ?, ?)
        ''', (date_production, unite_mesure, scope_type, scope_value, quantite))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout de production: {e}")
        return False

def obtenir_toute_production() -> List[Dict]:
    """Récupère toutes les entrées de production"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM production 
        ORDER BY date_production DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def modifier_production(
    id: int,
    date_production: str,
    unite_mesure: str,
    scope_type: str,
    scope_value: str,
    quantite: float
) -> bool:
    """Modifie une entrée de production"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE production 
            SET date_production = ?, unite_mesure = ?, scope_type = ?, scope_value = ?, quantite = ?
            WHERE id = ?
        ''', (date_production, unite_mesure, scope_type, scope_value, quantite, id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la modification de production: {e}")
        return False

def supprimer_production(id: int) -> bool:
    """Supprime une entrée de production"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM production WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression de production: {e}")
        return False

def ajouter_facture_electricite(
    numero_facture: str,
    date_facture: str,
    consommation_phase1: float,
    consommation_phase2: float,
    consommation_phase3: float,
    consommation_jour: float,
    consommation_pointe_ete: float,
    consommation_nuit: float,
    consommation_pointe_hiver: float,
    puissance_souscrite_jour: float,
    puissance_souscrite_pointe_ete: float,
    puissance_souscrite_nuit: float,
    puissance_souscrite_pointe_hiver: float,
    puissance_appelee_max_jour: float,
    puissance_appelee_max_pointe_ete: float,
    puissance_appelee_max_nuit: float,
    puissance_appelee_max_pointe_hiver: float,
    cos_phi: float = None,
    puissance_reactive: float = None,
    facture_rectificative: bool = False,
    tarif_jour: float = 0.0,
    tarif_pointe_ete: float = 0.0,
    tarif_nuit: float = 0.0,
    tarif_pointe_hiver: float = 0.0,
    avance: float = 0.0,
    type_facture: str = 'Reel'
) -> bool:
    """Ajoute une nouvelle facture d'électricité"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO factures_electricite 
            (numero_facture, date_facture, 
             consommation_phase1, consommation_phase2, consommation_phase3,
             consommation_jour, consommation_pointe_ete, consommation_nuit, consommation_pointe_hiver,
             puissance_souscrite_jour, puissance_souscrite_pointe_ete, puissance_souscrite_nuit, puissance_souscrite_pointe_hiver,
             puissance_appelee_max_jour, puissance_appelee_max_pointe_ete, puissance_appelee_max_nuit, puissance_appelee_max_pointe_hiver,
             cos_phi, puissance_reactive, facture_rectificative,
             tarif_jour, tarif_pointe_ete, tarif_nuit, tarif_pointe_hiver, avance, type_facture)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero_facture, date_facture,
              consommation_phase1, consommation_phase2, consommation_phase3,
              consommation_jour, consommation_pointe_ete, consommation_nuit, consommation_pointe_hiver,
              puissance_souscrite_jour, puissance_souscrite_pointe_ete, puissance_souscrite_nuit, puissance_souscrite_pointe_hiver,
              puissance_appelee_max_jour, puissance_appelee_max_pointe_ete, puissance_appelee_max_nuit, puissance_appelee_max_pointe_hiver,
              cos_phi, puissance_reactive, 1 if facture_rectificative else 0,
              tarif_jour, tarif_pointe_ete, tarif_nuit, tarif_pointe_hiver, avance, type_facture))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Erreur d'intégrité lors de l'ajout: {e}")
        return False  # Numéro de facture déjà existant
    except Exception as e:
        print(f"Erreur lors de l'ajout: {e}")
        import traceback
        traceback.print_exc()
        return False

def obtenir_toutes_factures_electricite() -> List[Dict]:
    """Récupère toutes les factures d'électricité"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM factures_electricite 
        ORDER BY date_facture DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def obtenir_facture_electricite(id: int) -> Optional[Dict]:
    """Récupère une facture d'électricité par son ID"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM factures_electricite WHERE id = ?', (id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def modifier_facture_electricite(
    id: int,
    numero_facture: str,
    date_facture: str,
    consommation_phase1: float,
    consommation_phase2: float,
    consommation_phase3: float,
    consommation_jour: float,
    consommation_pointe_ete: float,
    consommation_nuit: float,
    consommation_pointe_hiver: float,
    puissance_souscrite_jour: float,
    puissance_souscrite_pointe_ete: float,
    puissance_souscrite_nuit: float,
    puissance_souscrite_pointe_hiver: float,
    puissance_appelee_max_jour: float,
    puissance_appelee_max_pointe_ete: float,
    puissance_appelee_max_nuit: float,
    puissance_appelee_max_pointe_hiver: float,
    cos_phi: float = None,
    puissance_reactive: float = None,
    facture_rectificative: bool = False,
    tarif_jour: float = 0.0,
    tarif_pointe_ete: float = 0.0,
    tarif_nuit: float = 0.0,
    tarif_pointe_hiver: float = 0.0,
    avance: float = 0.0
) -> bool:
    """Modifie une facture d'électricité existante"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE factures_electricite 
            SET numero_facture = ?, date_facture = ?, 
                consommation_phase1 = ?, consommation_phase2 = ?, consommation_phase3 = ?,
                consommation_jour = ?, consommation_pointe_ete = ?, consommation_nuit = ?, consommation_pointe_hiver = ?,
                puissance_souscrite_jour = ?, puissance_souscrite_pointe_ete = ?, puissance_souscrite_nuit = ?, puissance_souscrite_pointe_hiver = ?,
                puissance_appelee_max_jour = ?, puissance_appelee_max_pointe_ete = ?, puissance_appelee_max_nuit = ?, puissance_appelee_max_pointe_hiver = ?,
                cos_phi = ?, puissance_reactive = ?, facture_rectificative = ?,
                tarif_jour = ?, tarif_pointe_ete = ?, tarif_nuit = ?, tarif_pointe_hiver = ?, avance = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (numero_facture, date_facture,
              consommation_phase1, consommation_phase2, consommation_phase3,
              consommation_jour, consommation_pointe_ete, consommation_nuit, consommation_pointe_hiver,
              puissance_souscrite_jour, puissance_souscrite_pointe_ete, puissance_souscrite_nuit, puissance_souscrite_pointe_hiver,
              puissance_appelee_max_jour, puissance_appelee_max_pointe_ete, puissance_appelee_max_nuit, puissance_appelee_max_pointe_hiver,
              cos_phi, puissance_reactive, 1 if facture_rectificative else 0,
              tarif_jour, tarif_pointe_ete, tarif_nuit, tarif_pointe_hiver, avance, id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Numéro de facture déjà existant
    except Exception as e:
        print(f"Erreur lors de la modification: {e}")
        return False

def supprimer_facture_electricite(id: int) -> bool:
    """Supprime une facture d'électricité"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM factures_electricite WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        return False

