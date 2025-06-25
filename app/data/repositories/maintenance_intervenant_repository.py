# gmao_app/app/data/repositories/maintenance_intervenant_repository.py
"""Repository pour la gestion des intervenants sur les maintenances."""
import logging
import psycopg2
from typing import List, Optional, Dict
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.maintenance_intervenant import MaintenanceIntervenant

logger = logging.getLogger(__name__)

class MaintenanceIntervenantRepository:
    """Repository pour accéder et manipuler les données des intervenants sur les maintenances."""

    def add(self, intervenant: MaintenanceIntervenant) -> Optional[int]:
        """Ajoute un nouvel intervenant à une maintenance."""
        sql = """INSERT INTO MAINTENANCE_INTERVENANT (
                maintenance_id, technicien_id, heures_travaillees, cout_horaire,
                nom_intervenant_externe, notes
            ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_intervenant"""
        
        params = (
            intervenant.maintenance_id,
            intervenant.technicien_id,
            intervenant.heures_travaillees,
            intervenant.cout_horaire,
            intervenant.nom_intervenant_externe,
            intervenant.notes
        )
        
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_intervenant") if row else None
            logger.info(f"Nouvel intervenant ajouté avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.error(f"Erreur d'intégrité lors de l'ajout d'un intervenant: {e}")
            raise DatabaseError(f"Erreur d'intégrité: {e}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'un intervenant: {e}")
            raise DatabaseError(f"Erreur lors de l'ajout d'un intervenant: {e}")
    
    def get_by_id(self, intervenant_id: int) -> Optional[MaintenanceIntervenant]:
        """Récupère un intervenant par son ID."""
        sql = "SELECT * FROM MAINTENANCE_INTERVENANT WHERE id_intervenant = %s"
        
        try:
            row = fetch_one(sql, (intervenant_id,))
            if not row:
                return None
            
            return MaintenanceIntervenant(
                id_intervenant=row['id_intervenant'],
                maintenance_id=row['maintenance_id'],
                technicien_id=row['technicien_id'],
                heures_travaillees=row['heures_travaillees'],
                cout_horaire=row['cout_horaire'],
                nom_intervenant_externe=row['nom_intervenant_externe'],
                notes=row['notes']
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération d'un intervenant: {e}")
            raise DatabaseError(f"Erreur lors de la récupération d'un intervenant: {e}")
    
    def get_by_maintenance_id(self, maintenance_id: int) -> List[MaintenanceIntervenant]:
        """Récupère tous les intervenants pour une maintenance donnée."""
        sql = "SELECT * FROM MAINTENANCE_INTERVENANT WHERE maintenance_id = %s"
        
        try:
            rows = fetch_all(sql, (maintenance_id,))
            intervenants = []
            
            for row in rows:
                intervenants.append(MaintenanceIntervenant(
                    id_intervenant=row['id_intervenant'],
                    maintenance_id=row['maintenance_id'],
                    technicien_id=row['technicien_id'],
                    heures_travaillees=row['heures_travaillees'],
                    cout_horaire=row['cout_horaire'],
                    nom_intervenant_externe=row['nom_intervenant_externe'],
                    notes=row['notes']
                ))
            
            return intervenants
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des intervenants: {e}")
            raise DatabaseError(f"Erreur lors de la récupération des intervenants: {e}")
    
    def get_by_technicien_id(self, technicien_id: int) -> List[MaintenanceIntervenant]:
        """Récupère toutes les interventions d'un technicien."""
        sql = "SELECT * FROM MAINTENANCE_INTERVENANT WHERE technicien_id = %s"
        
        try:
            rows = fetch_all(sql, (technicien_id,))
            intervenants = []
            
            for row in rows:
                intervenants.append(MaintenanceIntervenant(
                    id_intervenant=row['id_intervenant'],
                    maintenance_id=row['maintenance_id'],
                    technicien_id=row['technicien_id'],
                    heures_travaillees=row['heures_travaillees'],
                    cout_horaire=row['cout_horaire'],
                    nom_intervenant_externe=row['nom_intervenant_externe'],
                    notes=row['notes']
                ))
            
            return intervenants
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des interventions d'un technicien: {e}")
            raise DatabaseError(f"Erreur lors de la récupération des interventions d'un technicien: {e}")
    
    def update(self, intervenant: MaintenanceIntervenant) -> bool:
        """Met à jour un intervenant existant."""
        if not intervenant.id_intervenant:
            logger.error("Tentative de mise à jour d'un intervenant sans ID")
            return False
        
        # Ne pas mettre à jour maintenance_id car c'est la clé de liaison qui ne doit pas changer
        sql = """UPDATE MAINTENANCE_INTERVENANT SET
                technicien_id = %s,
                heures_travaillees = %s,
                cout_horaire = %s,
                nom_intervenant_externe = %s,
                notes = %s
            WHERE id_intervenant = %s"""
        
        params = (
            intervenant.technicien_id,
            intervenant.heures_travaillees,
            intervenant.cout_horaire,
            intervenant.nom_intervenant_externe,
            intervenant.notes,
            intervenant.id_intervenant
        )
        
        try:
            cursor = execute_query(sql, params)
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Intervenant ID {intervenant.id_intervenant} mis à jour")
            else:
                logger.warning(f"Intervenant ID {intervenant.id_intervenant} non trouvé pour mise à jour")
            return updated
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'un intervenant: {e}")
            raise DatabaseError(f"Erreur lors de la mise à jour d'un intervenant: {e}")
    
    def delete(self, intervenant_id: int) -> bool:
        """Supprime un intervenant par son ID."""
        sql = "DELETE FROM MAINTENANCE_INTERVENANT WHERE id_intervenant = %s"
        
        try:
            cursor = execute_query(sql, (intervenant_id,))
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Intervenant ID {intervenant_id} supprimé")
            else:
                logger.warning(f"Intervenant ID {intervenant_id} non trouvé pour suppression")
            return deleted
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un intervenant: {e}")
            raise DatabaseError(f"Erreur lors de la suppression d'un intervenant: {e}")