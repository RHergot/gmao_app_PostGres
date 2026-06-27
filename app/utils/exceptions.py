# gmao_app/app/utils/exceptions.py
"""
Exceptions personnalisées pour l'application GMAO.
"""

class GmaoBaseError(Exception):
    """Classe de base pour les exceptions personnalisées de l'application."""
    pass

class DatabaseError(GmaoBaseError):
    """Exception liée aux opérations de base de données."""
    pass

class ConfigurationError(GmaoBaseError):
    """Exception liée à une configuration invalide."""
    pass

class BusinessLogicError(GmaoBaseError):
    """Exception liée à une violation des règles métier."""
    pass

class ValidationError(BusinessLogicError):
    """Exception levée lorsqu'une validation métier échoue."""
    pass

class NotFoundError(DatabaseError):
    """Exception levée lorsqu'une ressource attendue n'est pas trouvée."""
    pass

class MaintenanceNotFoundError(NotFoundError):
    """Exception levée lorsqu'une maintenance attendue n'est pas trouvée."""
    pass

class GmaoPermissionError(GmaoBaseError):
    """Exception levée lorsqu'un utilisateur n'a pas les droits nécessaires."""
    pass
