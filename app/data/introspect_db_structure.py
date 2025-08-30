"""
Script Python pour introspecter la structure réelle d'une base PostgreSQL
et la comparer au schéma théorique (schemas.py).

Usage :
    - Configurez la connexion PostgreSQL via variables d'environnement ou .env
    - Lancez ce script pour obtenir la liste des tables, colonnes, types, clés primaires/étrangères
    - Compare automatiquement avec app/data/schemas.py si présent
"""
import os
from dotenv import load_dotenv, find_dotenv
import psycopg2
import psycopg2.extras
from pprint import pprint
from typing import Dict

# Chargement automatique du .env s'il existe (cherche dans les parents)
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)
    print(f"[INFO] .env chargé depuis : {dotenv_path}")
else:
    print("[WARNING] .env non trouvé, variables d'environnement système utilisées.")

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schemas.py")

# Chargement des variables d'environnement pour la connexion
DB_CONFIG = {
    'host': os.getenv('PGHOST', os.getenv('POSTGRES_HOST', 'localhost')),
    'port': int(os.getenv('PGPORT', os.getenv('POSTGRES_PORT', 5432))),
    'user': os.getenv('PGUSER', os.getenv('POSTGRES_USER', 'postgres')),
    'password': os.getenv('PGPASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'dbname': os.getenv('PGDATABASE', os.getenv('POSTGRES_DB', 'gmao')),
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_table_info(cur, table_name: str) -> Dict:
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name.lower(),))
    columns = cur.fetchall()
    return {col['column_name']: dict(col) for col in columns}

def list_tables(cur):
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    return [row['table_name'] for row in cur.fetchall()]

def fetch_foreign_keys(cur, table_name: str):
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
    """, (table_name.lower(),))
    return cur.fetchall()

def export_structure_to_file(structure: dict, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        for table, cols in structure.items():
            f.write(f"Table: {table}\n")
            for col, props in cols.items():
                f.write(f"  - {col}: {props['data_type']} (nullable={props['is_nullable']}, default={props['column_default']})\n")
            f.write("\n")


def compare_with_schema(real_structure: dict, schema_tables: dict, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        real_tables = set(real_structure.keys())
        schema_tables_set = set(schema_tables.keys())
        only_in_real = real_tables - schema_tables_set
        only_in_schema = schema_tables_set - real_tables
        f.write("Tables présentes uniquement dans la base réelle :\n")
        for t in sorted(only_in_real):
            f.write(f"  - {t}\n")
        f.write("\nTables présentes uniquement dans schemas.py :\n")
        for t in sorted(only_in_schema):
            f.write(f"  - {t}\n")
        f.write("\nComparaison détaillée des colonnes pour les tables communes :\n")
        for t in sorted(real_tables & schema_tables_set):
            real_cols = set(real_structure[t].keys())
            # Extraction grossière des colonnes du schéma théorique
            import re
            create_sql = schema_tables[t]
            cols_schema = set()
            for line in create_sql.splitlines():
                m = re.match(r"\s*([a-zA-Z0-9_]+) ", line)
                if m and not m.group(1).upper() in ("CREATE", "PRIMARY", "FOREIGN", "UNIQUE", "CONSTRAINT"):
                    cols_schema.add(m.group(1))
            only_in_real_cols = real_cols - cols_schema
            only_in_schema_cols = cols_schema - real_cols
            if only_in_real_cols or only_in_schema_cols:
                f.write(f"\nTable: {t}\n")
                if only_in_real_cols:
                    f.write(f"  Colonnes uniquement dans la base réelle : {sorted(only_in_real_cols)}\n")
                if only_in_schema_cols:
                    f.write(f"  Colonnes uniquement dans schemas.py : {sorted(only_in_schema_cols)}\n")


def main():
    import importlib.util
    import sys
    real_structure = {}
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            print("Tables présentes dans la base :")
            tables = list_tables(cur)
            pprint(tables)
            print("\nDétail des colonnes par table :")
            for table in tables:
                print(f"\nTable: {table}")
                cols = fetch_table_info(cur, table)
                pprint(cols)
                real_structure[table] = cols
                fks = fetch_foreign_keys(cur, table)
                if fks:
                    print("Foreign keys:")
                    pprint(fks)
    # Export structure réelle
    export_structure_to_file(real_structure, "structure_db_reelle.txt")
    print("[INFO] Structure réelle exportée dans structure_db_reelle.txt")
    # Comparaison automatique avec schemas.py
    if os.path.exists(SCHEMA_FILE):
        print("\n[INFO] Fichier schemas.py détecté. Génération du rapport de comparaison...")
        # Import dynamique de schemas.py pour récupérer TABLES
        spec = importlib.util.spec_from_file_location("schemas", SCHEMA_FILE)
        schemas = importlib.util.module_from_spec(spec)
        sys.modules["schemas"] = schemas
        spec.loader.exec_module(schemas)
        schema_tables = schemas.TABLES
        compare_with_schema(real_structure, schema_tables, "structure_db_comparaison.txt")
        print("[INFO] Rapport de comparaison généré dans structure_db_comparaison.txt")

if __name__ == "__main__":
    main()
