#!/usr/bin/env python3
"""
Script pour vérifier la structure de la table mouvement_stock
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_mouvement_stock_table():
    """Vérifie la structure de la table mouvement_stock"""
    try:
        from app.data.database import get_connection
        
        print("=== Vérification de la structure de la table mouvement_stock ===")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'mouvement_stock'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ La table mouvement_stock n'existe pas!")
            return
            
        print("✅ La table mouvement_stock existe")
        
        # Récupérer la structure de la table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mouvement_stock' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Structure de la table mouvement_stock ({len(columns)} colonnes):")
        print("-" * 60)
        
        for col in columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]:<20} {col[1]:<15} {nullable}{default}")
        
        # Vérifier spécifiquement la colonne type_mouvement
        type_mouvement_exists = any(col[0] == 'type_mouvement' for col in columns)
        
        if type_mouvement_exists:
            print("\n✅ La colonne 'type_mouvement' existe")
        else:
            print("\n❌ La colonne 'type_mouvement' n'existe PAS!")
            print("   Cette colonne est nécessaire pour le fonctionnement de l'application")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    check_mouvement_stock_table()
