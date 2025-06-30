#!/usr/bin/env python3
"""
Script pour analyser la structure des types de mouvements dans la base de données
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.database import get_db_connection

def check_type_mouvement_structure():
    """Analyser la structure des types de mouvements"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== ANALYSE DES TYPES DE MOUVEMENTS ===\n")
        
        # 1. Vérifier les IDs existants dans mouvement_stock
        print("1. IDs de types de mouvements existants dans mouvement_stock:")
        cursor.execute('SELECT DISTINCT type_mouvement_id FROM mouvement_stock ORDER BY type_mouvement_id')
        type_ids = cursor.fetchall()
        for type_id in type_ids:
            print(f"   - ID: {type_id[0]}")
        
        # 2. Chercher une table de référence pour les types
        print("\n2. Recherche de tables de référence:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name ILIKE '%type%' OR table_name ILIKE '%mouvement%')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            print(f"   - Table trouvée: {table_name}")
            
            # Afficher la structure de chaque table trouvée
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print(f"     Colonnes: {[(col[0], col[1]) for col in columns]}")
            
            # Afficher le contenu si c'est une petite table de référence
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count <= 20:  # Seulement pour les petites tables
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                print(f"     Contenu ({count} lignes):")
                for row in rows:
                    print(f"       {row}")
        
        # 3. Vérifier s'il y a des contraintes ou des références
        print("\n3. Contraintes de clés étrangères sur type_mouvement_id:")
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'mouvement_stock'
            AND kcu.column_name = 'type_mouvement_id'
        """)
        
        fk_constraints = cursor.fetchall()
        if fk_constraints:
            for constraint in fk_constraints:
                print(f"   - FK: {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]}")
        else:
            print("   - Aucune contrainte de clé étrangère trouvée")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_type_mouvement_structure()
