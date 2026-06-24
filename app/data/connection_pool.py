"""
Pool de connexions PostgreSQL pour l'application GMAO
"""

import psycopg2
import psycopg2.extras
import psycopg2.pool
import logging
import threading
from contextlib import contextmanager
from typing import Optional
from app.config import (
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
)
from app.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    Gestionnaire de pool de connexions PostgreSQL
    Thread-safe et optimisé pour l'utilisation dans une application multi-onglets
    """
    
    def __init__(self, minconn=2, maxconn=10):
        """
        Initialise le pool de connexions
        
        Args:
            minconn: Nombre minimum de connexions maintenues
            maxconn: Nombre maximum de connexions autorisées
        """
        self._pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._lock = threading.Lock()
        self.minconn = minconn
        self.maxconn = maxconn
        
    def initialize(self):
        """Initialise le pool de connexions"""
        with self._lock:
            if self._pool is None:
                try:
                    logger.info(f"Initialisation du pool de connexions PostgreSQL ({self.minconn}-{self.maxconn})")
                    logger.debug(f"Connexion à {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB} avec l'utilisateur {POSTGRES_USER}")
                    
                    self._pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=self.minconn,
                        maxconn=self.maxconn,
                        dbname=POSTGRES_DB,
                        user=POSTGRES_USER,
                        password=POSTGRES_PASSWORD,
                        host=POSTGRES_HOST,
                        port=POSTGRES_PORT,
                        cursor_factory=psycopg2.extras.RealDictCursor
                    )
                    logger.info("Pool de connexions PostgreSQL initialisé avec succès")
                    
                except psycopg2.Error as e:
                    logger.exception(f"Erreur lors de l'initialisation du pool: {e}")
                    raise DatabaseError(f"Impossible d'initialiser le pool de connexions: {e}") from e
    
    def get_connection(self):
        """
        Récupère une connexion du pool
        
        Returns:
            psycopg2.connection: Connexion PostgreSQL
        """
        if self._pool is None:
            self.initialize()
            
        try:
            conn = self._pool.getconn()
            if conn is None:
                raise DatabaseError("Impossible d'obtenir une connexion du pool")
            
            # Vérifier si la connexion est toujours valide
            if conn.closed != 0:
                logger.warning("Connexion fermée détectée, tentative de récupération")
                self._pool.putconn(conn, close=True)
                conn = self._pool.getconn()
                
            return conn
            
        except psycopg2.Error as e:
            logger.exception(f"Erreur lors de la récupération d'une connexion: {e}")
            raise DatabaseError(f"Erreur de connexion: {e}") from e
    
    def put_connection(self, conn, close=False):
        """
        Remet une connexion dans le pool
        
        Args:
            conn: Connexion à remettre
            close: Si True, ferme la connexion au lieu de la remettre
        """
        if self._pool and conn:
            try:
                self._pool.putconn(conn, close=close)
            except psycopg2.Error as e:
                logger.warning(f"Erreur lors de la remise de connexion dans le pool: {e}")
    
    @contextmanager
    def get_connection_context(self):
        """
        Context manager pour obtenir une connexion temporaire
        
        Usage:
            with pool.get_connection_context() as conn:
                # utiliser conn
                pass
        """
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            if conn:
                # En cas d'erreur, on marque la connexion comme fermée
                self.put_connection(conn, close=True)
            raise
        finally:
            if conn:
                self.put_connection(conn)
    
    def close_all(self):
        """Ferme toutes les connexions du pool"""
        with self._lock:
            if self._pool:
                try:
                    self._pool.closeall()
                    logger.info("Toutes les connexions du pool ont été fermées")
                except psycopg2.Error as e:
                    logger.warning(f"Erreur lors de la fermeture du pool: {e}")
                finally:
                    self._pool = None
    
    def get_stats(self):
        """Retourne les statistiques du pool"""
        if self._pool:
            # Ces attributs ne sont pas publics mais utiles pour le debug
            return {
                'minconn': self.minconn,
                'maxconn': self.maxconn,
                'closed': self._pool.closed if hasattr(self._pool, 'closed') else 'unknown'
            }
        return {'status': 'not_initialized'}


# Instance globale du pool
_connection_pool = ConnectionPool(minconn=2, maxconn=10)

def get_connection():
    """
    Fonction de compatibilité pour récupérer une connexion du pool
    
    Returns:
        psycopg2.connection: Connexion PostgreSQL du pool
    """
    return _connection_pool.get_connection()

def put_connection(conn, close=False):
    """
    Fonction de compatibilité pour remettre une connexion dans le pool
    
    Args:
        conn: Connexion à remettre
        close: Si True, ferme la connexion
    """
    _connection_pool.put_connection(conn, close=close)

@contextmanager
def get_connection_context():
    """
    Context manager pour obtenir une connexion temporaire du pool
    
    Usage:
        with get_connection_context() as conn:
            # utiliser conn
            pass
    """
    with _connection_pool.get_connection_context() as conn:
        yield conn

def initialize_pool():
    """Initialise le pool de connexions"""
    _connection_pool.initialize()

def close_all_connections():
    """Ferme toutes les connexions du pool"""
    _connection_pool.close_all()

def get_pool_stats():
    """Retourne les statistiques du pool"""
    return _connection_pool.get_stats()
