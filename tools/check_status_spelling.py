#!/usr/bin/env python3
"""
Test pour vérifier l'exacte orthographe des statuts dans la base.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.data.database import get_connection

def check_exact_statuses():
    """Vérifie l'orthographe exacte des statuts dans la base."""
    
    try:
        # Connexion à la base
        conn = get_connection()
        
        with conn.cursor() as cursor:
            # Récupérer tous les statuts avec leur nombre
            cursor.execute("""
                SELECT statut, COUNT(*) as count 
                FROM ORDRE_TRAVAIL 
                GROUP BY statut 
                ORDER BY statut
            """)
            results = cursor.fetchall()
            
            print("=== STATUTS EXACTS DANS LA BASE ===")
            for row in results:
                status = row['statut']
                count = row['count']
                print(f"'{status}' ({len(status)} caractères, ord={[ord(c) for c in status[-5:] if not c.isalpha()]}) : {count} OTs")
                
                # Analyser les caractères spéciaux
                for i, char in enumerate(status):
                    if not char.isalnum() and char not in [' ', '-', '_']:
                        print(f"  Caractère spécial à position {i}: '{char}' (ord={ord(char)})")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_exact_statuses()
