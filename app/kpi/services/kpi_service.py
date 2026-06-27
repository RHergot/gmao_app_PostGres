import os
import pandas as pd
import warnings
from app.data.introspect_db_structure import get_db_connection, DB_CONFIG

class KPIService:
    def __init__(self):
        # Supprimer le warning pandas SQLAlchemy (on utilise psycopg2 comme le reste de l'app)
        warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy connectable')
        # Connexion psycopg2 standard (cohérent avec le reste de l'application)
        self.conn = get_db_connection()

    def get_kpi_all_machines_by_period(self, date_start, date_end):
        """
        Retourne un DataFrame agrégé par machine sur la période [date_start, date_end]
        La vue v_kpi_machine_jour contient déjà les données agrégées par jour et par machine.
        On agrège simplement par machine sur la période demandée.
        """
        query = """
            SELECT * FROM v_kpi_machine_jour
            WHERE jour >= %s AND jour <= %s
        """
        df = pd.read_sql_query(query, self.conn, params=(date_start, date_end))
        if df.empty:
            return df
        
        # Agrégation par machine uniquement (pas par toutes les colonnes d'identité)
        # car la vue contient déjà les bonnes données par jour
        group_cols = ['id_machine']
        agg_dict = {
            # Colonnes d'identité : prendre la première valeur (elles sont identiques pour une machine)
            'machine_nom': 'first',
            'machine_serial': 'first', 
            'machine_criticite': 'first',
            'site_nom': 'first',
            'type_nom': 'first',
            'type_categorie': 'first',
            'equipe_nom': 'first',
            # Métriques : agrégation appropriée
            'nb_interventions': 'sum',
            'nb_preventif': 'sum',
            'nb_correctif': 'sum',
            'nb_urgence': 'sum',
            'cout_total_jour': 'sum',
            'cout_mod_jour': 'sum',
            'cout_pieces_jour': 'sum',
            'cout_frais_externes_jour': 'sum',
            'cout_moyen_intervention': 'mean',
            'duree_totale': 'sum',  # Temps total des interventions
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
        df_grouped = df.groupby(group_cols).agg(agg_dict).reset_index()
        return df_grouped

    def get_kpi_for_machine_by_period(self, id_machine, date_start, date_end):
        """
        Retourne un DataFrame d'une seule ligne pour la machine sélectionnée sur la période
        La vue v_kpi_machine_jour contient déjà les données agrégées par jour et par machine.
        On agrège simplement les jours de la période pour cette machine.
        """
        query = """
            SELECT * FROM v_kpi_machine_jour
            WHERE id_machine = %s AND jour >= %s AND jour <= %s
        """
        df = pd.read_sql_query(query, self.conn, params=(id_machine, date_start, date_end))
        if df.empty:
            return df
        
        # Séparer les colonnes d'identité des métriques pour éviter l'erreur pandas 'first'
        identity_cols = ['machine_nom', 'machine_serial', 'machine_criticite', 'site_nom', 'type_nom', 'type_categorie', 'equipe_nom']
        
        # Agrégation des métriques numériques uniquement
        metrics_agg_dict = {
            'nb_interventions': 'sum',
            'nb_preventif': 'sum',
            'nb_correctif': 'sum',
            'nb_urgence': 'sum',
            'cout_total_jour': 'sum',
            'cout_mod_jour': 'sum',
            'cout_pieces_jour': 'sum',
            'cout_frais_externes_jour': 'sum',
            'cout_moyen_intervention': 'mean',
            'duree_totale': 'sum',  # Temps total des interventions
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
        
        # Agrégation des métriques
        df_agg = df.agg(metrics_agg_dict).to_frame().T
        
        # Ajouter manuellement les colonnes d'identité (prendre la première ligne)
        df_agg['id_machine'] = id_machine
        for col in identity_cols:
            if col in df.columns:
                df_agg[col] = df.iloc[0][col]
        
        # Réorganiser les colonnes pour lisibilité
        cols = ['id_machine', 'machine_nom', 'machine_serial', 'machine_criticite',
                'site_nom', 'type_nom', 'type_categorie', 'equipe_nom'] + [
                    'nb_interventions', 'nb_preventif', 'nb_correctif', 'nb_urgence',
                    'cout_total_jour', 'cout_mod_jour', 'cout_pieces_jour', 'cout_frais_externes_jour',
                    'cout_moyen_intervention', 'duree_moyenne_h', 'cout_moyen_par_heure',
                    'cout_min', 'cout_max', 'cout_median',
                    'pourcentage_moyen_mod', 'pourcentage_moyen_pieces', 'pourcentage_moyen_frais_externes',
                    'ratio_preventif_curatif'
                ]
        df_agg = df_agg[cols]
        return df_agg

    def get_all_machines(self):
        query = "SELECT id_machine, nom FROM machine ORDER BY nom;"
        return pd.read_sql(query, self.conn)

    def get_all_types(self):
        query = "SELECT id_type_machine, nom FROM type_machine ORDER BY nom;"
        return pd.read_sql(query, self.conn)

    def get_all_teams(self):
        query = "SELECT id_equipe, nom FROM equipe ORDER BY nom;"
        return pd.read_sql(query, self.conn)

    def get_all_sites(self):
        query = "SELECT id_site, nom FROM site ORDER BY nom;"
        return pd.read_sql(query, self.conn)

    def get_temporal_kpi_data(self, date_start, date_end):
        """
        Retourne les données KPI temporelles (par jour) depuis v_kpi_machine_jour
        pour les courbes temporelles (trends)
        """
        query = """
            SELECT 
                jour,
                machine_nom,
                type_nom,
                site_nom,
                equipe_nom,
                cout_total_jour,
                nb_interventions,
                duree_totale
            FROM v_kpi_machine_jour
            WHERE jour >= %s AND jour <= %s
            ORDER BY jour ASC
        """
        return pd.read_sql_query(query, self.conn, params=(date_start, date_end))

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
