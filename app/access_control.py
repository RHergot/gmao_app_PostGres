"""
Module centralisé pour la gestion des droits d'accès aux menus.
À modifier UNIQUEMENT par l'administrateur principal.
"""

MENU_RIGHTS = {
    "Gérer les Utilisateurs":      {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer les OTs":               {"Admin": True, "Responsable": True, "Technicien": True,  "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer les Pièces Détachées":  {"Admin": True, "Responsable": True, "Technicien": True,  "Gestionnaire Stock": True,  "Lecteur": False},
    "Gérer les Machines":          {"Admin": True, "Responsable": True, "Technicien": False,  "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer les Fabricants":        {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer les Équipes":           {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer les Compteurs":         {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer le Stock":              {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": True,  "Lecteur": False},
    "Gérer les Fournisseurs":      {"Admin": True, "Responsable": True, "Technicien": True,  "Gestionnaire Stock": True,  "Lecteur": False},
    "Configuration":               {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer les Gammes d'Entretien": {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": False, "Lecteur": False},
    "Gérer Commandes":             {"Admin": True, "Responsable": True, "Technicien": False, "Gestionnaire Stock": True,  "Lecteur": False},
}

# Les menus/commentaires suivants sont supprimés ou désactivés car non présents dans la matrice métier :
# "Rapports de Maintenance", "Historique Interventions", "Exporter Données", "Gérer les Gammes d'Entretien"


ROLES = ["Admin", "Responsable", "Technicien", "Gestionnaire Stock", "Lecteur"]

# Mapping des synonymes de rôles (pour compatibilité base/droits)
ROLE_SYNONYMS = {
    "Responsable Maintenance": "Responsable",
    "Responsable maintenance": "Responsable",
    "Lecteur simple": "Lecteur",
    "lecteur": "Lecteur",
    "Gestionnaire Stock": "Gestionnaire Stock",  # exemple, mais déjà cohérent
    # Ajoute d'autres synonymes si besoin
}

import logging
logger = logging.getLogger(__name__)

def normalize_role(role: str) -> str:
    normalized = ROLE_SYNONYMS.get(role, role)
    logger.debug(f"[normalize_role] Rôle original: '{role}', Rôle normalisé: '{normalized}'")
    return normalized

def can_access(menu: str, role: str) -> bool:
    """
    Vérifie si un rôle donné a accès à un menu.
    :param menu: nom du menu (exact)
    :param role: rôle utilisateur (exact ou synonyme)
    :return: True si accès autorisé, False sinon
    """
    role = normalize_role(role)
    value = MENU_RIGHTS.get(menu, {}).get(role, False)
    logger.debug(f"[can_access] Menu: '{menu}', Rôle: '{role}', Accès: {value}, Droits: {MENU_RIGHTS.get(menu, {})}")
    return value


def get_accessible_menus(role: str):
    """
    Retourne la liste des menus accessibles pour un rôle donné.
    :param role: rôle utilisateur (exact ou synonyme)
    :return: liste des menus
    """
    role = normalize_role(role)
    return [menu for menu, rights in MENU_RIGHTS.items() if rights.get(role, False)]
