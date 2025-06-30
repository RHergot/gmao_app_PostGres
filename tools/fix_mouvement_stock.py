#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger le problème de la table mouvement_stock
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def diagnose_and_fix():
    """Diagnostique et corrige le problème de la table mouvement_stock"""
    try:
        print("=== Diagnostic de la table mouvement_stock ===")
        
        # Test de connexion basique
        from app.data.database import get_connection
        print("✅ Import de get_connection réussi")
        
        conn = get_connection()
        print("✅ Connexion à la base de données établie")
        
        cursor = conn.cursor()
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%mouvement%'
        """)
        
        tables = cursor.fetchall()
        print(f"📋 Tables contenant 'mouvement': {[t[0] for t in tables]}")
        
        # Essayer de récupérer la structure de la table mouvement_stock
        try:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'mouvement_stock' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            if columns:
                print(f"\n📋 Colonnes de mouvement_stock:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                    
                # Vérifier si type_mouvement existe
                has_type_mouvement = any(col[0] == 'type_mouvement' for col in columns)
                
                if not has_type_mouvement:
                    print("\n❌ La colonne 'type_mouvement' manque!")
                    print("🔧 Ajout de la colonne type_mouvement...")
                    
                    # Ajouter la colonne manquante
                    cursor.execute("""
                        ALTER TABLE mouvement_stock 
                        ADD COLUMN type_mouvement TEXT 
                        CHECK(type_mouvement IN ('ENTREE', 'SORTIE', 'AJUSTEMENT', 'INVENTAIRE'))
                    """)
                    
                    # Mettre une valeur par défaut pour les enregistrements existants
                    cursor.execute("""
                        UPDATE mouvement_stock 
                        SET type_mouvement = 'AJUSTEMENT' 
                        WHERE type_mouvement IS NULL
                    """)
                    
                    # Rendre la colonne NOT NULL
                    cursor.execute("""
                        ALTER TABLE mouvement_stock 
                        ALTER COLUMN type_mouvement SET NOT NULL
                    """)
                    
                    conn.commit()
                    print("✅ Colonne type_mouvement ajoutée avec succès!")
                else:
                    print("✅ La colonne type_mouvement existe déjà")
            else:
                print("❌ Aucune colonne trouvée pour mouvement_stock")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de la structure: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_and_fix()
