#!/usr/bin/env python3
"""
Script pour ajouter la colonne type_mouvement manquante à la table mouvement_stock
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_missing_column():
    """Ajoute la colonne type_mouvement manquante"""
    try:
        print("=== Ajout de la colonne type_mouvement ===")
        
        from app.data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        print("✅ Connexion établie")
        
        # Vérifier d'abord si la colonne existe déjà
        try:
            cursor.execute("SELECT type_mouvement FROM mouvement_stock LIMIT 1")
            print("✅ La colonne type_mouvement existe déjà!")
            return
        except Exception as e:
            print(f"❌ La colonne type_mouvement n'existe pas: {e}")
            print("🔧 Ajout de la colonne...")
        
        # Ajouter la colonne type_mouvement
        try:
            # Étape 1: Ajouter la colonne comme nullable d'abord
            cursor.execute("""
                ALTER TABLE mouvement_stock 
                ADD COLUMN type_mouvement TEXT
            """)
            print("✅ Colonne type_mouvement ajoutée")
            
            # Étape 2: Mettre une valeur par défaut pour les enregistrements existants
            cursor.execute("""
                UPDATE mouvement_stock 
                SET type_mouvement = 'AJUSTEMENT' 
                WHERE type_mouvement IS NULL
            """)
            print("✅ Valeurs par défaut définies")
            
            # Étape 3: Ajouter la contrainte NOT NULL
            cursor.execute("""
                ALTER TABLE mouvement_stock 
                ALTER COLUMN type_mouvement SET NOT NULL
            """)
            print("✅ Contrainte NOT NULL ajoutée")
            
            # Étape 4: Ajouter la contrainte CHECK
            cursor.execute("""
                ALTER TABLE mouvement_stock 
                ADD CONSTRAINT chk_type_mouvement 
                CHECK(type_mouvement IN ('ENTREE', 'SORTIE', 'AJUSTEMENT', 'INVENTAIRE'))
            """)
            print("✅ Contrainte CHECK ajoutée")
            
            # Valider les changements
            conn.commit()
            print("✅ Toutes les modifications ont été appliquées avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
            conn.rollback()
            raise
        
        cursor.close()
        conn.close()
        
        print("\n🎉 La colonne type_mouvement a été ajoutée avec succès!")
        print("   Vous pouvez maintenant utiliser l'application normalement.")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_missing_column()
