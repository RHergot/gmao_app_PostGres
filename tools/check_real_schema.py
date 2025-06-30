#!/usr/bin/env python3
"""
Script pour vérifier la structure réelle de la table mouvement_stock
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_real_schema():
    """Vérifie la structure réelle de la table mouvement_stock"""
    try:
        print("=== Structure réelle de la table mouvement_stock ===")
        
        from app.data.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Récupérer toutes les informations sur les colonnes
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'mouvement_stock' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print(f"📋 Table mouvement_stock - {len(columns)} colonnes:")
            print("-" * 80)
            print(f"{'Nom':<25} {'Type':<15} {'Nullable':<10} {'Défaut':<20}")
            print("-" * 80)
            
            column_names = []
            for col in columns:
                name = col[0]
                data_type = col[1]
                nullable = "OUI" if col[2] == "YES" else "NON"
                default = col[3] if col[3] else ""
                
                column_names.append(name)
                print(f"{name:<25} {data_type:<15} {nullable:<10} {default:<20}")
            
            print("\n📝 Liste des colonnes disponibles:")
            print(", ".join(column_names))
            
            # Vérifier les colonnes attendues par le code
            expected_columns = [
                'piece_id', 'type_mouvement_id', 'quantite', 'date_mouvement', 
                'raison', 'ot_id', 'user_id', 'stock_avant', 'stock_apres'
            ]
            
            print("\n🔍 Vérification des colonnes attendues:")
            missing_columns = []
            for expected in expected_columns:
                if expected in column_names:
                    print(f"  ✅ {expected}")
                else:
                    print(f"  ❌ {expected} - MANQUANTE")
                    missing_columns.append(expected)
            
            if missing_columns:
                print(f"\n⚠️  Colonnes manquantes: {', '.join(missing_columns)}")
                print("   Ces colonnes doivent être ajoutées ou le code doit être adapté.")
            else:
                print("\n✅ Toutes les colonnes attendues sont présentes!")
                
        else:
            print("❌ Aucune colonne trouvée pour la table mouvement_stock")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_real_schema()
