#!/usr/bin/env python3
"""
Script pour vérifier la structure de la base de données
"""

import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_db_connection():
    """Connexion directe à la base de données"""
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'gmao_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def check_database_structure():
    """Vérifie la structure de la base de données"""
    print("🔍 Vérification de la structure de la base de données...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Lister toutes les tables
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                
                tables = cur.fetchall()
                
                print(f"\n📋 Tables trouvées ({len(tables)} au total):")
                for table in tables:
                    print(f"  • {table['table_name']}")
                
                # Vérifier quelques tables importantes
                important_tables = ['site', 'machine', 'maintenance', 'equipe', 'type_machine']
                
                print(f"\n🔎 Vérification des tables importantes:")
                for table_name in important_tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                        result = cur.fetchone()
                        print(f"  ✓ {table_name.upper()}: {result['count']} lignes")
                    except Exception as e:
                        print(f"  ❌ {table_name.upper()}: {e}")
                
                # Vérifier les vues KPI
                print(f"\n📊 Vérification des vues KPI:")
                kpi_views = [
                    'vue_machines_kpi',
                    'vue_maintenance_kpi_machines', 
                    'vue_maintenance_kpi_sites',
                    'vue_maintenance_kpi_equipes'
                ]
                
                for view_name in kpi_views:
                    try:
                        cur.execute(f"SELECT COUNT(*) as count FROM {view_name}")
                        result = cur.fetchone()
                        print(f"  ✓ {view_name}: {result['count']} lignes")
                    except Exception as e:
                        print(f"  ❌ {view_name}: Vue non trouvée ou erreur")
                
    except Exception as e:
        print(f"❌ Erreur connexion DB: {e}")

if __name__ == "__main__":
    check_database_structure()
