# gmao_app/app/core/services/audit_service.py
"""
Service de piste d'audit (audit trail) pour les actions sensibles.

Stocke en mémoire les événements d'audit (préparation pour persistance DB).
La table AUDIT_TRAIL est définie dans app/data/schemas.py.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class AuditService:
    """Service de journalisation des actions sensibles (audit trail).

    À terme, ce service persistera les événements dans la table AUDIT_TRAIL.
    Pour l'instant, le stockage est en mémoire pour faciliter les tests
    et l'intégration progressive.
    """

    def __init__(self):
        """Initialise le service d'audit avec un stockage en mémoire."""
        self._audit_entries: List[Dict[str, Any]] = []
        self._next_id = 1
        logger.info("AuditService initialisé (mode mémoire).")

    def log_action(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: Any = None,
        details: str = "",
    ) -> int:
        """Enregistre une action sensible dans la piste d'audit.

        Args:
            user_id: ID de l'utilisateur ayant effectué l'action.
            action: Type d'action (ex: 'LOGIN', 'CREATE', 'UPDATE', 'DELETE',
                    'EXPORT', 'CHANGE_PASSWORD').
            entity_type: Type d'entité concernée (ex: 'UTILISATEUR', 'MACHINE',
                        'ORDRE_TRAVAIL', 'PIECE').
            entity_id: Identifiant de l'entité concernée (optionnel).
            details: Informations complémentaires (JSON ou texte libre).

        Returns:
            L'ID interne de l'entrée d'audit créée.
        """
        entry = {
            'id': self._next_id,
            'user_id': user_id,
            'action': action,
            'entity_type': entity_type,
            'entity_id': str(entity_id) if entity_id is not None else None,
            'details': details,
            'timestamp': datetime.now(),
        }
        self._audit_entries.append(entry)
        self._next_id += 1

        logger.info(
            f"AUDIT [{entry['id']}] user={user_id} action={action} "
            f"entity={entity_type}:{entity_id}"
        )
        if details:
            logger.debug(f"AUDIT [{entry['id']}] details: {details}")

        return entry['id']

    def get_audit_trail(
        self,
        entity_type: Optional[str] = None,
        entity_id: Any = None,
        user_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Récupère les entrées de la piste d'audit avec filtres optionnels.

        Args:
            entity_type: Filtrer par type d'entité (optionnel).
            entity_id: Filtrer par ID d'entité (optionnel).
            user_id: Filtrer par ID utilisateur (optionnel).
            limit: Nombre maximum d'entrées à retourner (défaut: 100).

        Returns:
            Liste des entrées d'audit correspondant aux critères,
            triées par timestamp décroissant (les plus récentes d'abord).
        """
        results = self._audit_entries.copy()

        # Appliquer les filtres
        if entity_type is not None:
            results = [e for e in results if e['entity_type'] == entity_type]
        if entity_id is not None:
            entity_id_str = str(entity_id)
            results = [e for e in results if e['entity_id'] == entity_id_str]
        if user_id is not None:
            results = [e for e in results if e['user_id'] == user_id]

        # Trier par timestamp décroissant (plus récent d'abord)
        results.sort(key=lambda e: e['timestamp'], reverse=True)

        # Limiter le nombre de résultats
        return results[:limit]

    def clear(self):
        """Vide toutes les entrées d'audit en mémoire (utile pour les tests)."""
        count = len(self._audit_entries)
        self._audit_entries.clear()
        self._next_id = 1
        logger.info(f"AuditService: {count} entrées d'audit effacées.")
