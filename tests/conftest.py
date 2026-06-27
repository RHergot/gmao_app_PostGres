# tests/conftest.py
"""
Fixtures pytest partagées pour les tests GMAO.
Utilise des mocks pour éviter toute dépendance à la base de données ou PySide6.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

# S'assurer que le répertoire racine du projet est dans sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Fixtures pour mocker la connexion DB
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db_connection():
    """Fixture retournant une connexion DB mockée."""
    conn = MagicMock(name='db_connection')
    cursor = MagicMock(name='db_cursor')
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
def mock_db_cursor(mock_db_connection):
    """Fixture retournant le curseur mocké de la connexion DB."""
    return mock_db_connection.cursor.return_value


@pytest.fixture
def mock_user_repository():
    """Fixture retournant un UserRepository mocké."""
    repo = MagicMock(name='user_repository')
    repo.has_users.return_value = False
    repo.get_by_id.return_value = None
    repo.get_by_login.return_value = None
    repo.get_all.return_value = []
    repo.add.return_value = 1
    repo.update.return_value = True
    repo.delete.return_value = True
    return repo


# ---------------------------------------------------------------------------
# Fixtures pour les modèles
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user_kwargs():
    """Fixture retournant les kwargs de base pour créer un Utilisateur."""
    return {
        'login': 'testuser',
        'role': 'Technicien',
        'nom_complet': 'Test User',
        'email': 'testuser@example.com',
        'mot_de_passe_hash': '$2b$12$hashedpasswordexample',
        'actif': True,
        'id_utilisateur': 42,
        'created_at': datetime(2024, 1, 15, 10, 30, 0),
        'updated_at': datetime(2024, 1, 15, 10, 30, 0),
        'technicien_id': None,
    }


@pytest.fixture
def sample_user(sample_user_kwargs):
    """Fixture retournant une instance Utilisateur complète prête à l'emploi."""
    from app.core.models.utilisateur import Utilisateur
    return Utilisateur(**sample_user_kwargs)


@pytest.fixture
def sample_user_minimal_kwargs():
    """Fixture retournant les kwargs minimaux pour un Utilisateur (champs obligatoires)."""
    return {
        'login': 'minuser',
        'role': 'Lecteur',
    }


# ---------------------------------------------------------------------------
# Fixtures pour les données temporelles
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_date():
    """Fixture retournant une date de référence."""
    return date(2024, 6, 15)


@pytest.fixture
def sample_datetime():
    """Fixture retournant un datetime de référence."""
    return datetime(2024, 6, 15, 14, 30, 45)


# ---------------------------------------------------------------------------
# Fixtures de hachage
# ---------------------------------------------------------------------------

@pytest.fixture
def plain_password():
    """Fixture retournant un mot de passe en clair de test."""
    return "S3cur3P@ssw0rd!"


@pytest.fixture
def hashed_password(plain_password):
    """Fixture retournant un hash bcrypt du mot de passe de test.
    
    Note: On utilise un vrai hash généré avec bcrypt pour que les tests
    de check_password fonctionnent correctement.
    """
    import bcrypt
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
