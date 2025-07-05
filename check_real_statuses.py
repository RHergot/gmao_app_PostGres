#!/usr/bin/env python3
"""
Vérifier si tous les statuts des constantes existent réellement dans la base.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.data.database import get_connection
from app.core.services.maintenance_service import OT_STATUTS_OUVERT, OT_STATUTS_FERME

def check_status_existence():
    """Vérifie si tous les statuts des constantes existent dans la base."""
    
    try:
        conn = get_connection()
        
        with conn.cursor() as cursor:
            # Récupérer tous les statuts de la base
            cursor.execute("SELECT DISTINCT statut FROM ORDRE_TRAVAIL ORDER BY statut")
            results = cursor.fetchall()
            db_statuts = [row['statut'] for row in results]
            
            print("=== VÉRIFICATION DES STATUTS DANS LES CONSTANTES ===")
            print(f"Statuts en base: {db_statuts}")
            print()
            
            all_constantes_statuts = OT_STATUTS_OUVERT + OT_STATUTS_FERME
            print(f"Statuts dans constantes: {all_constantes_statuts}")
            print()
            
            print("--- STATUTS DES CONSTANTES QUI N'EXISTENT PAS EN BASE ---")
            for statut in all_constantes_statuts:
                if statut not in db_statuts:
                    print(f"❌ '{statut}' défini dans constantes mais ABSENT de la base")
                else:
                    print(f"✅ '{statut}' présent en base")
            
            print()
            print("--- RECOMMANDATIONS ---")
            # Proposer les constantes corrigées
            correct_open = [s for s in OT_STATUTS_OUVERT if s in db_statuts]
            correct_closed = [s for s in OT_STATUTS_FERME if s in db_statuts]
            
            print(f"OT_STATUTS_OUVERT corrigés: {correct_open}")
            print(f"OT_STATUTS_FERME corrigés: {correct_closed}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_status_existence()
