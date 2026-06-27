# gmao_app/app/core/services/base_crud_service.py
"""
Service CRUD générique pour factoriser les patterns communs.
Utilisable par tous les services CRUD : validation -> création objet -> repo.add -> rechargement -> retour.

Refactoring H12 — Créé comme classe de base pour les futurs refactorings de machine_service.py
et autres services qui suivent le même pattern CRUD.
"""
import logging
from typing import Optional, List, Dict, Any, TypeVar, Generic, Type, Callable

from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type du modèle (ex: Site, Fabricant, TypeMachine)


class BaseCrudService(Generic[T]):
    """
    Service CRUD générique qui encapsule le pattern:
      validation -> création objet -> repo.add -> rechargement -> retour

    Les sous-classes doivent fournir:
      - _model_class: la classe du modèle (ex: Site)
      - _repo: le repository correspondant
      - _get_by_id(repo, id): méthode pour recharger un objet (peut être surchargée)
      - _validate_create(data): validation spécifique avant création
      - _validate_update(existing, data): validation spécifique avant mise à jour
      - _build_model(data): construction de l'objet modèle à partir du dict

    Usage:
        class SiteService(BaseCrudService[Site]):
            def __init__(self, site_repo):
                super().__init__(site_repo, Site)
    """

    def __init__(self, repository, model_class: Type[T]):
        """
        Args:
            repository: Le repository associé (doit avoir add, update, delete, get_by_id, get_all).
            model_class: La classe du modèle métier (ex: Site).
        """
        self._repo = repository
        self._model_class = model_class
        logger.debug(f"BaseCrudService[{model_class.__name__}] initialisé.")

    # --- Méthodes à surcharger par les sous-classes ---

    def _validate_create(self, data: Dict[str, Any]) -> None:
        """
        Validation spécifique avant création.
        Lève BusinessLogicError ou NotFoundError si invalide.
        Par défaut, vérifie juste que 'nom' est présent.
        """
        if not data.get('nom'):
            raise BusinessLogicError(f"Le nom du {self._model_class.__name__} est obligatoire.")

    def _validate_update(self, existing: T, data: Dict[str, Any]) -> None:
        """
        Validation spécifique avant mise à jour.
        Lève BusinessLogicError ou NotFoundError si invalide.
        Par défaut, vérifie que 'nom' n'est pas vide si présent.
        """
        if 'nom' in data and not data.get('nom'):
            raise BusinessLogicError(f"Le nom du {self._model_class.__name__} ne peut pas être vide.")

    def _build_model(self, data: Dict[str, Any]) -> T:
        """
        Construit un objet modèle à partir d'un dictionnaire de données.
        Par défaut, passe **data au constructeur du modèle.
        Surcharger si une transformation est nécessaire.
        """
        return self._model_class(**data)

    def _reload(self, obj_id: int) -> Optional[T]:
        """
        Recharge un objet depuis la base après création/modification.
        Par défaut utilise repo.get_by_id.
        """
        try:
            return self._repo.get_by_id(obj_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    # --- Méthodes CRUD génériques ---

    def get_all(self) -> List[T]:
        """Récupère tous les objets."""
        logger.debug(f"Récupération de tous les {self._model_class.__name__}s.")
        try:
            return self._repo.get_all()
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_by_id(self, obj_id: int) -> Optional[T]:
        """Récupère un objet par son ID."""
        logger.debug(f"Recherche {self._model_class.__name__} ID: {obj_id}")
        try:
            return self._repo.get_by_id(obj_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def create(self, data: Dict[str, Any]) -> T:
        """
        Crée un nouvel objet.
        Pattern: validation -> build model -> repo.add -> reload -> return.
        """
        logger.info(f"Tentative création {self._model_class.__name__}: {data.get('nom')}")

        # 1. Validation
        self._validate_create(data)

        # 2. Construction du modèle
        obj = self._build_model(data)

        # 3. Persistance
        try:
            new_id = self._repo.add(obj)
            if new_id is None:
                raise BusinessLogicError(f"Échec création {self._model_class.__name__}.")
            logger.info(f"{self._model_class.__name__} '{getattr(obj, 'nom', '?')}' créé ID: {new_id}.")
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible de créer le {self._model_class.__name__}: {e}") from e

        # 4. Rechargement
        created = self._reload(new_id)
        if not created:
            raise BusinessLogicError(f"{self._model_class.__name__} créé mais non retrouvé.")
        return created

    def update(self, obj_id: int, data: Dict[str, Any]) -> T:
        """
        Met à jour un objet existant.
        Pattern: get existing -> validate -> apply changes -> repo.update -> reload -> return.
        """
        logger.info(f"Tentative màj {self._model_class.__name__} ID: {obj_id}")

        # 1. Récupérer l'existant
        existing = self.get_by_id(obj_id)
        if existing is None:
            raise NotFoundError(f"{self._model_class.__name__} ID {obj_id} non trouvé pour màj.")

        # 2. Validation
        self._validate_update(existing, data)

        # 3. Appliquer les modifications
        has_changed = False
        for key, value in data.items():
            if hasattr(existing, key) and getattr(existing, key) != value:
                setattr(existing, key, value)
                has_changed = True
                logger.debug(f"{self._model_class.__name__} ID {obj_id}: Champ '{key}' modifié.")

        if not has_changed:
            return existing

        # 4. Persistance
        try:
            success = self._repo.update(existing)
            if not success:
                raise BusinessLogicError(f"Échec màj {self._model_class.__name__} (non trouvé?).")
            logger.info(f"{self._model_class.__name__} ID {obj_id} mis à jour.")
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible de mettre à jour le {self._model_class.__name__}: {e}") from e

        # 5. Rechargement
        updated = self._reload(obj_id)
        if not updated:
            raise BusinessLogicError(f"{self._model_class.__name__} màj mais non retrouvé.")
        return updated

    def delete(self, obj_id: int) -> bool:
        """
        Supprime un objet.
        Pattern: get existing -> confirm (optional) -> repo.delete.
        """
        logger.warning(f"Tentative suppression {self._model_class.__name__} ID: {obj_id}")
        if self.get_by_id(obj_id) is None:
            raise NotFoundError(f"{self._model_class.__name__} ID {obj_id} non trouvé pour suppression.")

        try:
            success = self._repo.delete(obj_id)
            if success:
                logger.info(f"{self._model_class.__name__} ID {obj_id} supprimé.")
            return success
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible de supprimer le {self._model_class.__name__}: {e}") from e
