"""
Fichier centralisé de gestion des traductions pour l'application GMAO.
Inclut tous les dictionnaires multilingues et helpers Python pour les menus, statuts, priorités, types d'OT, etc.
Ceci est la référence unique pour la traduction Python côté application.
"""

from typing import Dict, Any, List
from app.config import app_config, Language

# Dictionnaire de traduction des noms de menus (français -> autres langues)
MENU_LABELS = {
    "Fichier": {
        Language.FRENCH: "Fichier",
        Language.ENGLISH: "File",
        Language.GERMAN: "Datei",
        Language.SPANISH: "Archivo",
        Language.ITALIAN: "File",
        Language.PORTUGUESE: "Arquivo"
    },
    "Gestion": {
        Language.FRENCH: "Gestion",
        Language.ENGLISH: "Management",
        Language.GERMAN: "Verwaltung",
        Language.SPANISH: "Gestión",
        Language.ITALIAN: "Gestione",
        Language.PORTUGUESE: "Gestão"
    },
    "Stock": {
        Language.FRENCH: "Stock",
        Language.ENGLISH: "Inventory",
        Language.GERMAN: "Bestand",
        Language.SPANISH: "Inventario",
        Language.ITALIAN: "Magazzino",
        Language.PORTUGUESE: "Estoque"
    },
    "Maintenance": {
        Language.FRENCH: "Maintenance",
        Language.ENGLISH: "Maintenance",
        Language.GERMAN: "Wartung",
        Language.SPANISH: "Mantenimiento",
        Language.ITALIAN: "Manutenzione",
        Language.PORTUGUESE: "Manutenção"
    },
    "Aide": {
        Language.FRENCH: "Aide",
        Language.ENGLISH: "Help",
        Language.GERMAN: "Hilfe",
        Language.SPANISH: "Ayuda",
        Language.ITALIAN: "Aiuto",
        Language.PORTUGUESE: "Ajuda"
    },
    # ... (autres menus)
}

# Labels pour les filtres génériques (utilisés dans les combos)
filter_labels = {
    "All": {
        Language.FRENCH: "Tous",
        Language.ENGLISH: "All",
        Language.GERMAN: "Alle",
        Language.SPANISH: "Todos",
        Language.ITALIAN: "Tutti",
        Language.PORTUGUESE: "Todos"
    },
    # ... (autres filtres)
}

# Dictionnaires multilingues pour les types d'entretien et priorités
ENTRETIEN_TYPE_LABELS = {
    Language.FRENCH: {
        "Préventif Systématique": "Préventif Systématique",
        "Préventif Conditionnel": "Préventif Conditionnel",
        "Contrôle Réglementaire": "Contrôle Réglementaire",
        "Nettoyage": "Nettoyage",
        "Lubrification": "Lubrification",
        "Remplacement": "Remplacement",
    },
    Language.ENGLISH: {
        "Préventif Systématique": "Systematic Preventive",
        "Préventif Conditionnel": "Conditional Preventive",
        "Contrôle Réglementaire": "Regulatory Check",
        "Nettoyage": "Cleaning",
        "Lubrification": "Lubrication",
        "Remplacement": "Replacement",
    },
    Language.GERMAN: {
        "Préventif Systématique": "Systematische Wartung",
        "Préventif Conditionnel": "Bedingte Wartung",
        "Contrôle Réglementaire": "Vorschriftsmäßige Kontrolle",
        "Nettoyage": "Reinigung",
        "Lubrification": "Schmierung",
        "Remplacement": "Austausch",
    },
    Language.SPANISH: {
        "Préventif Systématique": "Preventivo Sistemático",
        "Préventif Conditionnel": "Preventivo Condicional",
        "Contrôle Réglementaire": "Control Reglamentario",
        "Nettoyage": "Limpieza",
        "Lubrification": "Lubricación",
        "Remplacement": "Reemplazo",
    },
    Language.ITALIAN: {
        "Préventif Systématique": "Preventiva Sistemica",
        "Préventif Conditionnel": "Preventiva Condizionale",
        "Contrôle Réglementaire": "Controllo Normativo",
        "Nettoyage": "Pulizia",
        "Lubrification": "Lubrificazione",
        "Remplacement": "Sostituzione",
    },
    Language.PORTUGUESE: {
        "Préventif Systématique": "Preventiva Sistemática",
        "Préventif Conditionnel": "Preventiva Condicional",
        "Contrôle Réglementaire": "Controle Regulamentar",
        "Nettoyage": "Limpeza",
        "Lubrification": "Lubrificação",
        "Remplacement": "Substituição",
    },
}


PRIORITE_LABELS = {
    Language.FRENCH: {
        "Basse": "Basse",
        "Moyenne": "Moyenne",
        "Haute": "Haute",
    },
    Language.ENGLISH: {
        "Basse": "Low",
        "Moyenne": "Medium",
        "Haute": "High",
    },
    Language.GERMAN: {
        "Basse": "Niedrig",
        "Moyenne": "Mittel",
        "Haute": "Hoch",
    },
    Language.SPANISH: {
        "Basse": "Baja",
        "Moyenne": "Media",
        "Haute": "Alta",
    },
    Language.ITALIAN: {
        "Basse": "Bassa",
        "Moyenne": "Media",
        "Haute": "Alta",
    },
    Language.PORTUGUESE: {
        "Basse": "Baixa",
        "Moyenne": "Média",
        "Haute": "Alta",
    },
}


def get_label_multi(d: dict, value: str, lang: Language) -> str:
    """
    Retourne la traduction pour la valeur donnée dans la langue cible (Language Enum).
    """
    return d.get(lang, {}).get(value, value)

def get_key_multi(d: dict, label: str, lang: Language) -> str:
    """
    Retourne la clé française à partir du label affiché dans la langue cible (pour stockage DB).
    """
    if lang == Language.FRENCH:
        return label
    inv = {v: k for k, v in d.get(lang, {}).items()}
    return inv.get(label, label)

# --- Fonctions de traduction centralisées ---
def translate_menu_label(label_key: str, language: Language = None) -> str:
    """
    Traduit un label de menu à partir du dictionnaire centralisé.
    Utilise la langue globale app_config.language si non précisée.
    Retourne la clé d'origine si non trouvé.
    """
    if language is None:
        language = app_config.language
    return MENU_LABELS.get(label_key, {}).get(language, label_key)

def translate_label(label_key: str, language: Language = None) -> str:
    """
    Traduit un label générique pour les filtres selon la langue globale app_config.language si non précisée.
    """
    if language is None:
        language = app_config.language
    return filter_labels.get(label_key, {}).get(language, label_key)

# --- Dictionnaires de traduction pour les types d'OT ---
type_translations = {
    "Preventif": {
        Language.FRENCH: "Préventif",
        Language.ENGLISH: "Preventive",
        Language.GERMAN: "Präventiv",
        Language.SPANISH: "Preventivo",
        Language.ITALIAN: "Preventivo",
        Language.PORTUGUESE: "Preventivo"
    },
    "Correctif": {
        Language.FRENCH: "Correctif",
        Language.ENGLISH: "Corrective",
        Language.GERMAN: "Korrektur",
        Language.SPANISH: "Correctivo",
        Language.ITALIAN: "Correttivo",
        Language.PORTUGUESE: "Corretivo"
    },
    "Amelioratif": {
        Language.FRENCH: "Amélioratif",
        Language.ENGLISH: "Improvement",
        Language.GERMAN: "Verbesserung",
        Language.SPANISH: "Mejora",
        Language.ITALIAN: "Miglioramento",
        Language.PORTUGUESE: "Melhoria"
    },
    "Demande": {
        Language.FRENCH: "Demande",
        Language.ENGLISH: "Request",
        Language.GERMAN: "Anfrage",
        Language.SPANISH: "Solicitud",
        Language.ITALIAN: "Richiesta",
        Language.PORTUGUESE: "Solicitação"
    },
    "Reglementaire": {
        Language.FRENCH: "Réglementaire",
        Language.ENGLISH: "Regulatory",
        Language.GERMAN: "Vorschriftsmäßig",
        Language.SPANISH: "Reglamentario",
        Language.ITALIAN: "Normativo",
        Language.PORTUGUESE: "Regulamentar"
    }
}

# --- Dictionnaires de traduction pour les priorités ---
priority_translations = {
    "Basse": {
        Language.FRENCH: "Basse",
        Language.ENGLISH: "Low",
        Language.GERMAN: "Niedrig",
        Language.SPANISH: "Baja",
        Language.ITALIAN: "Bassa",
        Language.PORTUGUESE: "Baixa"
    },
    "Moyenne": {
        Language.FRENCH: "Moyenne",
        Language.ENGLISH: "Medium",
        Language.GERMAN: "Mittel",
        Language.SPANISH: "Media",
        Language.ITALIAN: "Media",
        Language.PORTUGUESE: "Média"
    },
    "Haute": {
        Language.FRENCH: "Haute",
        Language.ENGLISH: "High",
        Language.GERMAN: "Hoch",
        Language.SPANISH: "Alta",
        Language.ITALIAN: "Alta",
        Language.PORTUGUESE: "Alta"
    },
    "Urgente": {
        Language.FRENCH: "Urgente",
        Language.ENGLISH: "Urgent",
        Language.GERMAN: "Dringend",
        Language.SPANISH: "Urgente",
        Language.ITALIAN: "Urgente",
        Language.PORTUGUESE: "Urgente"
    }
}

# --- Dictionnaires de traduction pour les statuts ---
status_translations = {
    "Créé": {
        Language.FRENCH: "Créé",
        Language.ENGLISH: "Created",
        Language.GERMAN: "Erstellt",
        Language.SPANISH: "Creado",
        Language.ITALIAN: "Creato",
        Language.PORTUGUESE: "Criado"
    },
    "Planifié": {
        Language.FRENCH: "Planifié",
        Language.ENGLISH: "Scheduled",
        Language.GERMAN: "Geplant",
        Language.SPANISH: "Planificado",
        Language.ITALIAN: "Pianificato",
        Language.PORTUGUESE: "Planejado"
    },
    "EnCours": {
        Language.FRENCH: "En Cours",
        Language.ENGLISH: "In Progress",
        Language.GERMAN: "In Bearbeitung",
        Language.SPANISH: "En Curso",
        Language.ITALIAN: "In Corso",
        Language.PORTUGUESE: "Em Andamento"
    },
    "Terminé": {
        Language.FRENCH: "Terminé",
        Language.ENGLISH: "Completed",
        Language.GERMAN: "Abgeschlossen",
        Language.SPANISH: "Terminado",
        Language.ITALIAN: "Completato",
        Language.PORTUGUESE: "Concluído"
    },
    "Annulé": {
        Language.FRENCH: "Annulé",
        Language.ENGLISH: "Cancelled",
        Language.GERMAN: "Abgebrochen",
        Language.SPANISH: "Cancelado",
        Language.ITALIAN: "Annullato",
        Language.PORTUGUESE: "Cancelado"
    },
    "Suspendu": {
        Language.FRENCH: "Suspendu",
        Language.ENGLISH: "Suspended",
        Language.GERMAN: "Ausgesetzt",
        Language.SPANISH: "Suspendido",
        Language.ITALIAN: "Sospeso",
        Language.PORTUGUESE: "Suspenso"
    },
    "AttentePieces": {
        Language.FRENCH: "Attente Pièces",
        Language.ENGLISH: "Waiting for Parts",
        Language.GERMAN: "Wartet auf Teile",
        Language.SPANISH: "En espera de piezas",
        Language.ITALIAN: "In attesa de pezzi",
        Language.PORTUGUESE: "Aguardando Peças"
    },
    "Pret": {
        Language.FRENCH: "Prêt",
        Language.ENGLISH: "Ready",
        Language.GERMAN: "Bereit",
        Language.SPANISH: "Listo",
        Language.ITALIAN: "Pronto",
        Language.PORTUGUESE: "Pronto"
    },
    "Realise": {
        Language.FRENCH: "Réalisé",
        Language.ENGLISH: "Completed",
        Language.GERMAN: "Erledigt",
        Language.SPANISH: "Realizado",
        Language.ITALIAN: "Eseguito",
        Language.PORTUGUESE: "Realizado"
    },
    "Cloture": {
        Language.FRENCH: "Clôturé",
        Language.ENGLISH: "Closed",
        Language.GERMAN: "Abgeschlossen",
        Language.SPANISH: "Cerrado",
        Language.ITALIAN: "Chiuso",
        Language.PORTUGUESE: "Encerrado"
    },
    # Purchase Order Statuses
    "Brouillon": {
        Language.FRENCH: "Brouillon",
        Language.ENGLISH: "Draft",
        Language.GERMAN: "Entwurf",
        Language.SPANISH: "Borrador",
        Language.ITALIAN: "Bozza",
        Language.PORTUGUESE: "Rascunho"
    },
    "Validee": {
        Language.FRENCH: "Validee",
        Language.ENGLISH: "Validated",
        Language.GERMAN: "Validiert",
        Language.SPANISH: "Validado",
        Language.ITALIAN: "Validato",
        Language.PORTUGUESE: "Validado"
    },
    "Envoyee": {
        Language.FRENCH: "Envoyee",
        Language.ENGLISH: "Sent",
        Language.GERMAN: "Gesendet",
        Language.SPANISH: "Enviado",
        Language.ITALIAN: "Inviato",
        Language.PORTUGUESE: "Enviado"
    },
    "Partielle": {
        Language.FRENCH: "Partielle",
        Language.ENGLISH: "Partial",
        Language.GERMAN: "Teilweise",
        Language.SPANISH: "Parcial",
        Language.ITALIAN: "Parziale",
        Language.PORTUGUESE: "Parcial"
    },
    "Livree": {
        Language.FRENCH: "Livree",
        Language.ENGLISH: "Delivered",
        Language.GERMAN: "Geliefert",
        Language.SPANISH: "Entregado",
        Language.ITALIAN: "Consegnato",
        Language.PORTUGUESE: "Entregue"
    },
    "Annulee": {
        Language.FRENCH: "Annulee",
        Language.ENGLISH: "Cancelled",
        Language.GERMAN: "Storniert",
        Language.SPANISH: "Cancelado",
        Language.ITALIAN: "Annullato",
        Language.PORTUGUESE: "Cancelado"
    }
}

# --- Fonctions utilitaires pour traduire types, priorités, statuts ---
def translate_type(ot_type: str, language: Language = None) -> str:
    """
    Traduit un type d'OT selon la langue globale app_config.language si non précisée.
    Args:
        ot_type: Le type d'OT à traduire
        language: Langue cible (optionnel, utilise app_config.language si non spécifié)
    """
    if language is None:
        language = app_config.language
    return type_translations.get(ot_type, {}).get(language, ot_type)

def translate_priority(priority: str, language: Language = None) -> str:
    """
    Traduit une priorité selon la langue globale app_config.language si non précisée.
    Args:
        priority: La priorité à traduire
        language: Langue cible (optionnel, utilise app_config.language si non spécifié)
    """
    if language is None:
        language = app_config.language
    return priority_translations.get(priority, {}).get(language, priority)

def translate_status(status: str, language: Language = None) -> str:
    """
    Traduit un statut selon la langue globale app_config.language si non précisée.
    Args:
        status: Le statut à traduire
        language: Langue cible (optionnel, utilise app_config.language si non spécifié)
    """
    if language is None:
        language = app_config.language
    return status_translations.get(status, {}).get(language, status)

def reverse_translate_status(translated_status: str, source_language: Language = None, prefer_keys: List[str] = None) -> str:
    """
    Retourne la clé française du statut à partir de sa traduction dans une langue donnée.
    Utilisé pour convertir les valeurs traduites de l'UI vers les valeurs françaises de la base.
    Args:
        translated_status: Le statut traduit affiché dans l'UI
        source_language: Langue source de la traduction (optionnel, utilise app_config.language si non spécifié)
        prefer_keys: Liste de clés préférées à rechercher en premier (pour résoudre les conflits)
    Returns:
        La clé française du statut pour la base de données
    """
    if source_language is None:
        source_language = app_config.language
    
    # Si c'est déjà en français, retourner tel quel
    if source_language == Language.FRENCH:
        return translated_status
    
    # Si des clés préférées sont spécifiées, les chercher en premier
    if prefer_keys:
        for french_key in prefer_keys:
            translations = status_translations.get(french_key, {})
            if translations.get(source_language) == translated_status:
                return french_key
    
    # Rechercher dans le dictionnaire de traductions
    for french_key, translations in status_translations.items():
        if translations.get(source_language) == translated_status:
            return french_key
    
    # Si pas trouvé, retourner la valeur originale
    return translated_status

# --- Helper functions for specific domains ---

def reverse_translate_purchase_order_status(translated_status: str, source_language: Language = None) -> str:
    """
    Helper function specifically for purchase order statuses.
    Prioritizes purchase order status keys to avoid conflicts with work order statuses.
    """
    purchase_order_keys = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
    return reverse_translate_status(translated_status, source_language, prefer_keys=purchase_order_keys)
