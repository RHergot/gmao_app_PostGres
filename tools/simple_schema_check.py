#!/usr/bin/env python3
"""
Script simple pour identifier les colonnes de mouvement_stock
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_schema_check():
    """Vérification simple des colonnes"""
    try:
        print("=== Vérification simple des colonnes mouvement_stock ===")
        
        from app.data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Essayer de faire un SELECT * pour voir les colonnes
        try:
            cursor.execute("SELECT * FROM mouvement_stock LIMIT 0")
            column_names = [desc[0] for desc in cursor.description]
            
            print(f"📋 Colonnes trouvées ({len(column_names)}):")
            for i, col in enumerate(column_names, 1):
                print(f"  {i:2d}. {col}")
            
            # Vérifier les colonnes problématiques
            problematic_columns = ['type_mouvement', 'type_mouvement_id', 'raison']
            print(f"\n🔍 Vérification des colonnes problématiques:")
            for col in problematic_columns:
                if col in column_names:
                    print(f"  ✅ {col} - EXISTE")
                else:
                    print(f"  ❌ {col} - N'EXISTE PAS")
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des colonnes: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    simple_schema_check()
