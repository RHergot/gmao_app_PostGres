#!/usr/bin/env python3
"""
Script simple pour vérifier la structure de la table mouvement_stock
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_check():
    """Vérification simple de la table mouvement_stock"""
    try:
        print("=== Vérification simple de mouvement_stock ===")
        
        from app.data.database import get_connection
        print("✅ Connexion à la base de données...")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Essayer une requête simple sur la table
        print("🔍 Test d'accès à la table mouvement_stock...")
        
        try:
            cursor.execute("SELECT * FROM mouvement_stock LIMIT 1")
            print("✅ La table mouvement_stock est accessible")
        except Exception as e:
            print(f"❌ Erreur d'accès à mouvement_stock: {e}")
            
        # Essayer de décrire la table avec une approche différente
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'mouvement_stock'
            """)
            
            columns = cursor.fetchall()
            print(f"📋 Colonnes trouvées: {len(columns)}")
            
            column_names = []
            for row in columns:
                column_names.append(row[0])
            
            print(f"📝 Liste des colonnes: {column_names}")
            
            if 'type_mouvement' in column_names:
                print("✅ La colonne 'type_mouvement' existe")
            else:
                print("❌ La colonne 'type_mouvement' n'existe PAS!")
                print("🔧 Cette colonne doit être ajoutée à la table")
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des colonnes: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_check()
