#!/usr/bin/env python3
"""
Script simple pour vérifier les vues existantes dans la base de données.
"""

import sys
import os

# Ajouter la racine du projet au PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
app_path = os.path.join(project_root, 'app')
sys.path.insert(0, app_path)

from app.data.database import get_connection, close_connection

def check_views():
    """Vérifie les vues existantes dans la base de données."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Connexion établie, exécution de la requête...")
        
        # Récupérer toutes les vues
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print("Requête exécutée, récupération des résultats...")
        views = cursor.fetchall()
        
        print(f"Type de views: {type(views)}")
        print(f"Contenu de views: {views}")
        
        print("Vues disponibles dans la base de données:")
        print("=" * 50)
        
        if views and len(views) > 0:
            for view in views:
                print(f"✓ {view[0] if isinstance(view, tuple) else view}")
        else:
            print("Aucune vue trouvée dans le schéma 'public'")
            
            # Essayer une requête plus simple
            print("\nTentative avec une requête alternative...")
            cursor.execute("SELECT viewname FROM pg_views WHERE schemaname = 'public'")
            pg_views = cursor.fetchall()
            print(f"pg_views résultat: {pg_views}")
            
            if pg_views:
                print("Vues trouvées via pg_views:")
                for view in pg_views:
                    print(f"  ✓ {view[0]}")
        
        print(f"\nNombre total de vues dans 'public': {len(views) if views else 0}")
        
        close_connection()
        
    except Exception as e:
        print(f"Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_views()
