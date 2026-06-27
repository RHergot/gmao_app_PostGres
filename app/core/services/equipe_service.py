# gmao_app/app/core/services/equipe_service.py
"""
Service métier pour la gestion des Équipes.
Extrait de MaintenanceService (refactoring H11 - God Object).
"""
import logging
from typing import Optional, List, Dict, Any

from app.core.models.equipe import Equipe
from app.data.repositories import EquipeRepository, TechnicienRepository
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class EquipeService:
    """Orchestre les opérations CRUD sur les Équipes."""

    def __init__(self,
                 equipe_repo: EquipeRepository,
                 tech_repo: TechnicienRepository):
        """
        Initialise le service avec les repositories nécessaires.

        Args:
            equipe_repo: Repository des équipes.
            tech_repo: Repository des techniciens (pour validation du responsable).
        """
        self._equipe_repo = equipe_repo
        self._tech_repo = tech_repo
        logger.debug("EquipeService initialisé.")

    def get_all_equipes(self) -> List[Equipe]:
        """Récupère toutes les équipes."""
        try:
            return self._equipe_repo.get_all()
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_equipe_by_id(self, eq_id: int) -> Optional[Equipe]:
        """Récupère une équipe par son ID."""
        logger.debug(f"Recherche equipe ID: {eq_id}")
        try:
            return self._equipe_repo.get_by_id(eq_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def create_equipe(self, data: Dict[str, Any]) -> Equipe:
        """Crée une nouvelle équipe après validation."""
        logger.info(f"Tentative création equipe: {data.get('nom')}")
        if not data.get('nom'):
            raise BusinessLogicError("Nom équipe obligatoire.")
        if data.get('responsable_id') and not self._tech_repo.get_by_id(data['responsable_id']):
            raise NotFoundError(f"Technicien responsable ID {data['responsable_id']} non trouvé.")

        equipe = Equipe(**data)
        try:
            new_id = self._equipe_repo.add(equipe)
            if not new_id:
                raise BusinessLogicError("Echec création equipe.")
            logger.info(f"Equipe '{equipe.nom}' créée ID: {new_id}.")
            created = self.get_equipe_by_id(new_id)
            if not created:
                raise BusinessLogicError("Créée mais non retrouvée.")
            return created
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible créer equipe: {e}") from e

    def update_equipe(self, eq_id: int, data: Dict[str, Any]) -> Equipe:
        """Met à jour une équipe existante."""
        logger.info(f"Tentative màj equipe ID: {eq_id}")
        eq = self.get_equipe_by_id(eq_id)
        if not eq:
            raise NotFoundError(f"Equipe ID {eq_id} non trouvée.")
        if 'nom' in data and not data.get('nom'):
            raise BusinessLogicError("Nom obligatoire.")
        if data.get('responsable_id') and data['responsable_id'] != eq.responsable_id:
            if data['responsable_id'] is not None and not self._tech_repo.get_by_id(data['responsable_id']):
                raise NotFoundError(f"Nouveau responsable ID {data['responsable_id']} non trouvé.")

        has_changed = False
        for key, value in data.items():
            if hasattr(eq, key) and getattr(eq, key) != value:
                setattr(eq, key, value)
                has_changed = True
        if not has_changed:
            return eq

        try:
            if not self._equipe_repo.update(eq):
                raise BusinessLogicError("Echec màj.")
            logger.info(f"Equipe ID {eq_id} mise à jour.")
            updated = self.get_equipe_by_id(eq_id)
            if not updated:
                raise BusinessLogicError("Màj mais non retrouvée.")
            return updated
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible mettre à jour equipe: {e}") from e

    def delete_equipe(self, eq_id: int) -> bool:
        """Supprime une équipe."""
        logger.warning(f"Tentative suppression equipe ID: {eq_id}")
        if not self.get_equipe_by_id(eq_id):
            raise NotFoundError(f"Equipe ID {eq_id} non trouvée.")
        try:
            return self._equipe_repo.delete(eq_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible supprimer equipe: {e}") from e
