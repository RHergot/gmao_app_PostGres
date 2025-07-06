#!/usr/bin/env python3
"""
Script pour corriger les rôles des utilisateurs dans la base GMAO
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

def fix_user_roles():
    """Corrige les rôles des utilisateurs pour qu'ils correspondent au système de contrôle d'accès"""
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
                
                # Mappings des rôles à corriger
                role_fixes = {
                    'admin': 'Admin',
                    'responsable': 'Responsable',
                    'technicien': 'Technicien',
                    'gestionnaire_stock': 'Gestionnaire Stock',
                    'lecteur': 'Lecteur'
                }
                
                logger.info("=== CORRECTION DES RÔLES UTILISATEURS ===")
                
                corrections_made = 0
                
                for old_role, new_role in role_fixes.items():
                    # Vérifier s'il y a des utilisateurs avec l'ancien rôle
                    cursor.execute("""
                        SELECT id_utilisateur, login, role 
                        FROM utilisateur 
                        WHERE role = %s
                    """, (old_role,))
                    
                    users_to_fix = cursor.fetchall()
                    
                    if users_to_fix:
                        logger.info(f"Correction du rôle '{old_role}' vers '{new_role}' pour {len(users_to_fix)} utilisateur(s)")
                        
                        for user in users_to_fix:
                            cursor.execute("""
                                UPDATE utilisateur 
                                SET role = %s, updated_at = CURRENT_TIMESTAMP 
                                WHERE id_utilisateur = %s
                            """, (new_role, user['id_utilisateur']))
                            
                            logger.info(f"  - Utilisateur '{user['login']}' (ID: {user['id_utilisateur']}) : '{old_role}' -> '{new_role}'")
                            corrections_made += 1
                
                # S'assurer qu'il y a au moins un utilisateur Admin actif
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM utilisateur 
                    WHERE role = 'Admin' AND actif = 1
                """)
                
                admin_count = cursor.fetchone()['count']
                
                if admin_count == 0:
                    logger.warning("Aucun utilisateur Admin actif trouvé. Activation du premier utilisateur Admin...")
                    
                    cursor.execute("""
                        UPDATE utilisateur 
                        SET actif = 1, updated_at = CURRENT_TIMESTAMP 
                        WHERE role = 'Admin' 
                        ORDER BY id_utilisateur 
                        LIMIT 1
                        RETURNING id_utilisateur, login
                    """)
                    
                    result = cursor.fetchone()
                    if result:
                        logger.info(f"Utilisateur Admin activé : {result['login']} (ID: {result['id_utilisateur']})")
                        corrections_made += 1
                
                # Valider les changements
                conn.commit()
                
                logger.info(f"=== CORRECTION TERMINÉE : {corrections_made} modification(s) ===")
                
                # Afficher l'état final
                cursor.execute("""
                    SELECT id_utilisateur, login, role, actif
                    FROM utilisateur 
                    ORDER BY role, login
                """)
                
                users = cursor.fetchall()
                logger.info("\n=== ÉTAT FINAL DES UTILISATEURS ===")
                
                for user in users:
                    status = "✓ ACTIF" if user['actif'] == 1 else "✗ INACTIF"
                    logger.info(f"ID: {user['id_utilisateur']:2d} | Login: {user['login']:15s} | "
                              f"Rôle: {user['role']:18s} | {status}")
                
                # Vérifier l'accès au menu "Gérer les OTs"
                ot_access_roles = ['Admin', 'Responsable', 'Technicien']
                accessible_users = [u for u in users if u['role'] in ot_access_roles and u['actif'] == 1]
                
                logger.info(f"\n=== ACCÈS AU MENU 'Gérer les OTs' ===")
                if accessible_users:
                    logger.info("Utilisateurs ayant accès au menu 'Gérer les OTs' :")
                    for user in accessible_users:
                        logger.info(f"  - {user['login']} (rôle: {user['role']})")
                else:
                    logger.error("AUCUN utilisateur actif n'a accès au menu 'Gérer les OTs' !")
                
                return corrections_made > 0
                
    except Exception as e:
        logger.error(f"Erreur lors de la correction des rôles : {e}")
        return False

def main():
    """Fonction principale"""
    logger.info("=== CORRECTION DES RÔLES UTILISATEURS GMAO ===")
    
    success = fix_user_roles()
    
    if success:
        logger.info("\n✓ Corrections appliquées avec succès !")
        logger.info("Vous pouvez maintenant redémarrer l'application et vous connecter avec :")
        logger.info("  - Login: admin")
        logger.info("  - Mot de passe: (selon votre configuration)")
    else:
        logger.error("\n✗ Aucune correction appliquée ou erreur rencontrée.")
    
    logger.info("\n=== FIN DE LA CORRECTION ===")

if __name__ == "__main__":
    main()
