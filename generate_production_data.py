import random
from datetime import datetime
from database import init_database, ajouter_production

# Initialiser la base de données
init_database()

start_year = 2022
end_year = 2024

print("🚀 Démarrage de la génération de données de production...")

count = 0
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        # Date: 1er de chaque mois
        date_str = f"{year}-{month:02d}-01"
        
        # Données fixes demandées
        unite = "T (Tonnes)"
        scope_type = "Global"
        scope_value = "Usine"
        
        # Variation aléatoire entre 100 et 200
        quantite = random.uniform(100, 200)
        
        # Ajout
        if ajouter_production(
            date_production=date_str,
            unite_mesure=unite,
            scope_type=scope_type,
            scope_value=scope_value,
            quantite=quantite
        ):
            print(f"✅ Ajouté: {date_str} - {quantite:.2f} {unite}")
            count += 1
        else:
            print(f"❌ Erreur pour {date_str}")

print(f"\n✨ Terminé ! {count} entrées de production ont été ajoutées.")
