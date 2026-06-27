# gmao_app/app/core/services/technicien_service.py
"""
Service métier pour la gestion des Techniciens.
Extrait de MaintenanceService (refactoring H11 - God Object).
"""
import logging
from typing import Optional, List, Dict, Any

from app.core.models.technicien import Technicien
from app.data.repositories import TechnicienRepository, EquipeRepository
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class TechnicienService:
    """Orchestre les opérations CRUD sur les Techniciens."""

    def __init__(self,
                 tech_repo: TechnicienRepository,
                 equipe_repo: EquipeRepository):
        """
        Initialise le service avec les repositories nécessaires.

        Args:
            tech_repo: Repository des techniciens.
            equipe_repo: Repository des équipes (pour validation des FK).
        """
        self._tech_repo = tech_repo
        self._equipe_repo = equipe_repo
        logger.debug("TechnicienService initialisé.")

    def get_all_techniciens(self, include_inactive: bool = False) -> List[Technicien]:
        """Récupère tous les techniciens, avec option d'inclure les inactifs."""
        logger.debug(f"Récupération techniciens (inactifs inclus: {include_inactive}).")
        try:
            return self._tech_repo.get_all(include_inactive=include_inactive)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_technicien_by_id(self, tech_id: int) -> Optional[Technicien]:
        """Récupère un technicien par son ID."""
        logger.debug(f"Recherche technicien ID: {tech_id}")
        try:
            return self._tech_repo.get_by_id(tech_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def create_technicien(self, data: Dict[str, Any]) -> Technicien:
        """Crée un nouveau technicien après validation."""
        logger.info(f"Tentative création technicien: {data.get('nom')}")
        if not data.get('nom'):
            raise BusinessLogicError("Nom technicien obligatoire.")
        if data.get('equipe_id') and not self._equipe_repo.get_by_id(data['equipe_id']):
            raise NotFoundError(f"Equipe ID {data['equipe_id']} non trouvée.")

        tech = Technicien(**data)
        try:
            new_id = self._tech_repo.add(tech)
            if not new_id:
                raise BusinessLogicError("Echec création technicien.")
            logger.info(f"Technicien '{tech.nom_complet}' créé ID: {new_id}.")
            created = self.get_technicien_by_id(new_id)
            if not created:
                raise BusinessLogicError("Créé mais non retrouvé.")
            return created
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible créer technicien: {e}") from e

    def update_technicien(self, tech_id: int, data: Dict[str, Any]) -> Technicien:
        """Met à jour un technicien existant."""
        logger.info(f"Tentative màj technicien ID: {tech_id}")
        tech = self.get_technicien_by_id(tech_id)
        if not tech:
            raise NotFoundError(f"Technicien ID {tech_id} non trouvé.")
        if 'nom' in data and not data.get('nom'):
            raise BusinessLogicError("Nom obligatoire.")
        if data.get('equipe_id') and data['equipe_id'] != tech.equipe_id:
            if data['equipe_id'] is not None and not self._equipe_repo.get_by_id(data['equipe_id']):
                raise NotFoundError(f"Nouvelle Equipe ID {data['equipe_id']} non trouvée.")

        has_changed = False
        for key, value in data.items():
            if hasattr(tech, key) and getattr(tech, key) != value:
                if key == 'cout_horaire':
                    value = float(value or 0.0)
                setattr(tech, key, value)
                has_changed = True
        if not has_changed:
            return tech

        try:
            if not self._tech_repo.update(tech):
                raise BusinessLogicError("Echec màj.")
            logger.info(f"Technicien ID {tech_id} mis à jour.")
            updated = self.get_technicien_by_id(tech_id)
            if not updated:
                raise BusinessLogicError("Màj mais non retrouvé.")
            return updated
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible mettre à jour: {e}") from e

    def delete_technicien(self, tech_id: int) -> bool:
        """Supprime un technicien."""
        logger.warning(f"Tentative suppression technicien ID: {tech_id}")
        if self.get_technicien_by_id(tech_id) is None:
            raise NotFoundError(f"Technicien ID {tech_id} non trouvé pour suppression.")
        try:
            success = self._tech_repo.delete(tech_id)
            if success:
                logger.info(f"Technicien ID {tech_id} supprimé.")
            return success
        except DatabaseError as e:
            logger.error(f"Échec DB suppression technicien ID {tech_id}: {e}")
            raise BusinessLogicError(f"Impossible de supprimer le technicien: {e}") from e
