#!/usr/bin/env python3
"""
Script pour vérifier les utilisateurs et leurs rôles dans la base de données GMAO
"""

import sys
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env_config():
    """Charge la configuration depuis le fichier .env"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Fichier .env non trouvé : {env_path}")
    
    config = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    return config

def check_users_and_roles():
    """Vérifie les utilisateurs et leurs rôles dans la base de données"""
    try:
        # Charger la configuration
        config = load_env_config()
        
        # Paramètres de connexion
        conn_params = {
            'host': config.get('POSTGRES_HOST'),
            'port': config.get('POSTGRES_PORT', '5432'),
            'database': config.get('POSTGRES_DB'),
            'user': config.get('POSTGRES_USER'),
            'password': config.get('POSTGRES_PASSWORD')
        }
        
        logger.info(f"Connexion à la base : {conn_params['database']} sur {conn_params['host']}:{conn_params['port']}")
        
        # Connexion à la base
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                # Vérifier si la table utilisateur existe
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'utilisateur'
                """)
                
                if not cursor.fetchone():
                    logger.error("Table 'utilisateur' non trouvée dans la base de données")
                    return
                
                # D'abord vérifier la structure de la table
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'utilisateur' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                logger.info("Structure de la table utilisateur :")
                for col in columns:
                    logger.info(f"  - {col['column_name']}: {col['data_type']}")
                
                # Récupérer tous les utilisateurs avec les colonnes qui existent vraiment
                cursor.execute("""
                    SELECT id_utilisateur, login, role, actif
                    FROM utilisateur 
                    ORDER BY role, login
                """)
                
                users = cursor.fetchall()
                
                if not users:
                    logger.warning("Aucun utilisateur trouvé dans la base de données")
                    return
                
                logger.info(f"\n=== UTILISATEURS DANS LA BASE ({len(users)} trouvés) ===")
                
                role_counts = {}
                for user in users:
                    role = user['role']
                    role_counts[role] = role_counts.get(role, 0) + 1
                    
                    status = "✓ ACTIF" if user['actif'] else "✗ INACTIF"
                    logger.info(f"ID: {user['id_utilisateur']:2d} | Login: {user['login']:15s} | "
                              f"Rôle: {user['role']:18s} | {status}")
                
                logger.info(f"\n=== RÉPARTITION PAR RÔLE ===")
                for role, count in role_counts.items():
                    logger.info(f"{role}: {count} utilisateur(s)")
                
                # Recommandations selon les rôles
                logger.info(f"\n=== ACCÈS AU MENU 'Gérer les OTs' ===")
                ot_access_roles = ['Admin', 'Responsable', 'Technicien']
                
                accessible_users = [u for u in users if u['role'] in ot_access_roles and u['actif']]
                
                if accessible_users:
                    logger.info("Utilisateurs ayant accès au menu 'Gérer les OTs' :")
                    for user in accessible_users:
                        logger.info(f"  - {user['login']} (rôle: {user['role']})")
                else:
                    logger.warning("AUCUN utilisateur actif n'a accès au menu 'Gérer les OTs' !")
                
                # Proposition de solution
                if not accessible_users:
                    logger.info(f"\n=== SOLUTION PROPOSÉE ===")
                    logger.info("Pour résoudre le problème du menu 'Gérer les OTs' grisé :")
                    logger.info("1. Connectez-vous avec un utilisateur ayant le rôle Admin, Responsable ou Technicien")
                    logger.info("2. Ou modifiez le rôle d'un utilisateur existant")
                    logger.info("3. Ou créez un nouvel utilisateur avec les bons droits")
                
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des utilisateurs : {e}")

def create_admin_user_if_needed():
    """Crée un utilisateur admin si aucun n'existe"""
    try:
        config = load_env_config()
        
        conn_params = {
            'host': config.get('POSTGRES_HOST'),
            'port': config.get('POSTGRES_PORT', '5432'),
            'database': config.get('POSTGRES_DB'),
            'user': config.get('POSTGRES_USER'),
            'password': config.get('POSTGRES_PASSWORD')
        }
        
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                # Vérifier s'il existe un admin actif
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM utilisateur 
                    WHERE role = 'Admin' AND actif = true
                """)
                
                admin_count = cursor.fetchone()['count']
                
                if admin_count == 0:
                    logger.info("Aucun utilisateur Admin actif trouvé. Création d'un utilisateur admin...")
                    
                    # Créer un utilisateur admin
                    cursor.execute("""
                        INSERT INTO utilisateur (login, role, actif, mot_de_passe_hash)
                        VALUES ('admin', 'Admin', true, 'admin123')
                        ON CONFLICT (login) DO UPDATE SET 
                            role = 'Admin',
                            actif = true
                        RETURNING id_utilisateur, login
                    """)
                    
                    result = cursor.fetchone()
                    logger.info(f"Utilisateur admin créé/mis à jour : ID {result['id_utilisateur']}, Login: {result['login']}")
                    logger.info("Mot de passe temporaire: admin123")
                    logger.info("ATTENTION: Changez ce mot de passe après la première connexion !")
                    
                    conn.commit()
                else:
                    logger.info(f"{admin_count} utilisateur(s) Admin actif(s) trouvé(s).")
                
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur admin : {e}")

def main():
    """Fonction principale"""
    logger.info("=== DIAGNOSTIC UTILISATEURS GMAO ===")
    
    check_users_and_roles()
    
    print("\nVoulez-vous créer un utilisateur admin si nécessaire ? (o/n): ", end="")
    response = input().lower().strip()
    
    if response in ['o', 'oui', 'y', 'yes']:
        create_admin_user_if_needed()
    
    logger.info("\n=== FIN DU DIAGNOSTIC ===")

if __name__ == "__main__":
    main()
