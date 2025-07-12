import pandas as pd
from app.data.introspect_db_structure import get_db_connection

def debug_kpi_data():
    conn = get_db_connection()
    
    # Test 1: Vérifier les colonnes de la vue
    query = "SELECT * FROM v_kpi_machine_jour WHERE jour >= '2024-10-01' AND jour <= '2025-01-12' LIMIT 5"
    df = pd.read_sql(query, conn)
    
    print("=== Colonnes disponibles dans v_kpi_machine_jour ===")
    print(df.columns.tolist())
    print()
    
    print("=== Échantillon de données (5 premières lignes) ===")
    print(df.head())
    print()
    
    print("=== Types de données ===")
    print(df.dtypes)
    print()
    
    # Test 2: Tester l'agrégation comme dans KPIService
    if not df.empty:
        group_cols = [
            'id_machine', 'machine_nom', 'machine_serial', 'machine_criticite',
            'site_nom', 'type_nom', 'type_categorie', 'equipe_nom'
        ]
        
        # Vérifier quelles colonnes existent vraiment
        existing_group_cols = [col for col in group_cols if col in df.columns]
        print(f"=== Colonnes de groupage existantes: {existing_group_cols} ===")
        
        agg_dict = {
            'nb_interventions': 'sum',
            'nb_preventif': 'sum',
            'nb_correctif': 'sum',
            'nb_urgence': 'sum',
            'cout_total_jour': 'sum',
            'cout_mod_jour': 'sum',
            'cout_pieces_jour': 'sum',
            'cout_frais_externes_jour': 'sum',
            'cout_moyen_intervention': 'mean',
            'duree_moyenne_h': 'mean',
            'cout_moyen_par_heure': 'mean',
            'cout_min': 'min',
            'cout_max': 'max',
            'cout_median': 'median',
            'pourcentage_moyen_mod': 'mean',
            'pourcentage_moyen_pieces': 'mean',
            'pourcentage_moyen_frais_externes': 'mean',
            'ratio_preventif_curatif': 'mean'
        }
        
        # Vérifier quelles colonnes d'agrégation existent
        existing_agg_cols = {k: v for k, v in agg_dict.items() if k in df.columns}
        print(f"=== Colonnes d'agrégation existantes: {list(existing_agg_cols.keys())} ===")
        
        if existing_group_cols and existing_agg_cols:
            try:
                df_grouped = df.groupby(existing_group_cols).agg(existing_agg_cols).reset_index()
                print("=== Résultat après agrégation ===")
                print(df_grouped.head())
            except Exception as e:
                print(f"Erreur lors de l'agrégation: {e}")
    
    conn.close()

if __name__ == "__main__":
    debug_kpi_data()
