# machine_kpi_chart_translations.py
#!/usr/bin/env python3
"""
Traductions spécifiques pour l'onglet graphiques des KPI machines.
Support multilingue avec l'anglais comme langue par défaut.
"""

from app.config import Language

# === TRADUCTIONS POUR L'ONGLET GRAPHIQUES ===
CHART_TRANSLATIONS = {
    Language.ENGLISH: {
        # Titre principal
        "charts_tab_title": "📈 Charts & Trends",
        
        # Filtres
        "site_filter": "🏢 Filter by Site",
        "all_sites": "🌐 All sites",
        "machine_filter_chart": "🔍 Filter by Machine", 
        "all_machines_chart": "🏭 All machines",
        "type_filter_chart": "⚙️ Machine Type",
        "all_types_chart": "📋 All types",
        
        # Contrôles de périodicité
        "period_controls": "📅 Period Controls",
        "period_type": "Period Type:",
        "daily": "📅 Daily",
        "weekly": "📆 Weekly", 
        "monthly": "🗓️ Monthly",
        "start_date": "Start Date:",
        "end_date": "End Date:",
        
        # Type de graphique
        "chart_type_controls": "📊 Chart Type",
        "chart_mode": "Visualization Mode:",
        "bars_mode": "📊 Bars",
        "lines_mode": "📈 Lines",
        
        # Graphique
        "chart_title": "Costs, Interventions and Duration Over Time",
        "costs_label": "Costs (€)",
        "interventions_label": "Interventions",
        "duration_label": "Duration (hours)",
        "no_data_chart": "No data available for the selected period",
        
        # Légende
        "legend_costs": "💰 Costs",
        "legend_interventions": "🔧 Interventions",
        "legend_duration": "⏱️ Duration",
        
        # Messages
        "loading_chart": "Loading chart data...",
        "chart_updated": "Chart updated successfully",
        "invalid_date_range": "Invalid date range selected",
        "no_data_period": "No data available for this period",
        
        # Boutons
        "refresh_chart": "🔄 Refresh Chart",
        "export_chart": "💾 Export Chart",
        "full_screen": "🔍 Full Screen",
        
        # Axes
        "x_axis_label": "Time Period",
        "y_axis_costs": "Costs (€)",
        "y_axis_interventions": "Number of Interventions",
        "y_axis_duration": "Duration (hours)",
        
        # Tooltips
        "tooltip_costs": "Costs: €{value}",
        "tooltip_interventions": "Interventions: {value}",
        "tooltip_duration": "Duration: {value}h",
        "tooltip_period": "Period: {period}",
        
        # Erreurs
        "error_loading_data": "Error loading chart data",
        "error_invalid_filters": "Invalid filter combination",
        "error_no_machines": "No machines found for selected filters"
    },
    
    Language.FRENCH: {
        # Titre principal
        "charts_tab_title": "📈 Graphiques & Tendances",
        
        # Filtres
        "site_filter": "🏢 Filtrer par Site",
        "all_sites": "🌐 Tous les sites",
        "machine_filter_chart": "🔍 Filtrer par Machine",
        "all_machines_chart": "🏭 Toutes les machines", 
        "type_filter_chart": "⚙️ Type de Machine",
        "all_types_chart": "📋 Tous les types",
        
        # Contrôles de périodicité
        "period_controls": "📅 Contrôles de Période",
        "period_type": "Type de Période:",
        "daily": "📅 Quotidien",
        "weekly": "📆 Hebdomadaire",
        "monthly": "🗓️ Mensuel",
        "start_date": "Date de Début:",
        "end_date": "Date de Fin:",
        
        # Type de graphique
        "chart_type_controls": "📊 Type de Graphique",
        "chart_mode": "Mode de Visualisation:",
        "bars_mode": "📊 Barres",
        "lines_mode": "📈 Courbes",
        
        # Graphique
        "chart_title": "Coûts, Interventions et Durée au Fil du Temps",
        "costs_label": "Coûts (€)",
        "interventions_label": "Interventions",
        "duration_label": "Durée (heures)",
        "no_data_chart": "Aucune donnée disponible pour la période sélectionnée",
        
        # Légende
        "legend_costs": "💰 Coûts",
        "legend_interventions": "🔧 Interventions",
        "legend_duration": "⏱️ Durée",
        
        # Messages
        "loading_chart": "Chargement des données du graphique...",
        "chart_updated": "Graphique mis à jour avec succès",
        "invalid_date_range": "Plage de dates invalide sélectionnée",
        "no_data_period": "Aucune donnée disponible pour cette période",
        
        # Boutons
        "refresh_chart": "🔄 Actualiser le Graphique",
        "export_chart": "💾 Exporter le Graphique",
        "full_screen": "🔍 Plein Écran",
        
        # Axes
        "x_axis_label": "Période de Temps",
        "y_axis_costs": "Coûts (€)",
        "y_axis_interventions": "Nombre d'Interventions",
        "y_axis_duration": "Durée (heures)",
        
        # Tooltips
        "tooltip_costs": "Coûts: {value}€",
        "tooltip_interventions": "Interventions: {value}",
        "tooltip_duration": "Durée: {value}h",
        "tooltip_period": "Période: {period}",
        
        # Erreurs
        "error_loading_data": "Erreur lors du chargement des données du graphique",
        "error_invalid_filters": "Combinaison de filtres invalide",
        "error_no_machines": "Aucune machine trouvée pour les filtres sélectionnés"
    },
    
    Language.GERMAN: {
        # Titre principal
        "charts_tab_title": "📈 Diagramme & Trends",
        
        # Filtres
        "site_filter": "🏢 Nach Standort filtern",
        "all_sites": "🌐 Alle Standorte",
        "machine_filter_chart": "🔍 Nach Maschine filtern",
        "all_machines_chart": "🏭 Alle Maschinen",
        "type_filter_chart": "⚙️ Maschinentyp",
        "all_types_chart": "📋 Alle Typen",
        
        # Contrôles de périodicité
        "period_controls": "📅 Zeitraum-Kontrollen",
        "period_type": "Zeitraum-Typ:",
        "daily": "📅 Täglich",
        "weekly": "📆 Wöchentlich",
        "monthly": "🗓️ Monatlich",
        "start_date": "Startdatum:",
        "end_date": "Enddatum:",
        
        # Type de graphique
        "chart_type_controls": "📊 Diagrammtyp",
        "chart_mode": "Visualisierungsmodus:",
        "bars_mode": "📊 Balken",
        "lines_mode": "📈 Linien",
        
        # Graphique
        "chart_title": "Kosten und Interventionen über Zeit",
        "costs_label": "Kosten (€)",
        "interventions_label": "Interventionen",
        "no_data_chart": "Keine Daten für den gewählten Zeitraum verfügbar",
        
        # Légende
        "legend_costs": "💰 Kosten",
        "legend_interventions": "🔧 Interventionen",
        
        # Messages
        "loading_chart": "Lade Diagrammdaten...",
        "chart_updated": "Diagramm erfolgreich aktualisiert",
        "invalid_date_range": "Ungültiger Datumsbereich ausgewählt",
        "no_data_period": "Keine Daten für diesen Zeitraum verfügbar",
        
        # Boutons
        "refresh_chart": "🔄 Diagramm Aktualisieren",
        "export_chart": "💾 Diagramm Exportieren",
        "full_screen": "🔍 Vollbild",
        
        # Axes
        "x_axis_label": "Zeitraum",
        "y_axis_costs": "Kosten (€)",
        "y_axis_interventions": "Anzahl Interventionen",
        
        # Tooltips
        "tooltip_costs": "Kosten: €{value}",
        "tooltip_interventions": "Interventionen: {value}",
        "tooltip_period": "Zeitraum: {period}",
        
        # Erreurs
        "error_loading_data": "Fehler beim Laden der Diagrammdaten",
        "error_invalid_filters": "Ungültige Filterkombination",
        "error_no_machines": "Keine Maschinen für gewählte Filter gefunden"
    }
}

def get_chart_text(key: str) -> str:
    """Récupère le texte traduit pour les graphiques selon la langue configurée.
    
    Args:
        key: Clé de traduction
        
    Returns:
        Texte traduit (anglais par défaut)
    """
    try:
        from app.config import app_config
        current_lang = app_config.language if 'app_config' in globals() else Language.ENGLISH
        return CHART_TRANSLATIONS.get(current_lang, CHART_TRANSLATIONS[Language.ENGLISH]).get(key, key)
    except:
        return CHART_TRANSLATIONS[Language.ENGLISH].get(key, key)
