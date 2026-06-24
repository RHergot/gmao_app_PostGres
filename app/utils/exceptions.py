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

# Ajouter d'autres exceptions spécifiques au besoin...
class ValidationError(BusinessLogicError):
     """Exception levée lorsqu'une ressource attendue n'est pas trouvée."""
     pass

class NotFoundError(DatabaseError):
     pass

class MaintenanceNotFoundError(NotFoundError):
    """Exception levée lorsqu'une maintenance attendue n'est pas trouvée."""
    pass

""" Exceptions personnalisées pour l'application. """

class DatabaseError(Exception):
    """ Erreur spécifique à la base de données. """
    pass

class PermissionError(Exception):
    """ Erreur spécifique aux droits d'accès. """
    pass

class BusinessLogicError(Exception):
     """ Erreur liée aux règles métier. """
     pass
