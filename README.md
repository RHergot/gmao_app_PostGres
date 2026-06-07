# GMAO Industrielle — Application Principale

Application de **Gestion de Maintenance Assistée par Ordinateur** (GMAO) développée avec **PySide6 (Qt)** et **PostgreSQL**.

## Fonctionnalités

- 🏭 **Gestion des machines** — Fiches machines, types, compteurs, historiques
- 🔧 **Maintenance** — Gammes, ordres de travail (OT), interventions, rapports PDF
- 📊 **KPI** — Indicateurs de performance, vues SQL financières, tableaux de bord
- 👥 **Utilisateurs & Équipes** — Contrôle d'accès, rôles, techniciens
- 🌍 **Multi-langue** — Français, Anglais, Espagnol, Italien (Qt Linguist)
- 📄 **Génération de documents** — Rapports de maintenance, OT en HTML/PDF

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Interface | PySide6 (Qt) |
| Base de données | PostgreSQL via un pool de connexions |
| Architecture | MVC + Repository pattern |
| Traductions | Qt Linguist (.ts/.qm) |
| PDF | Templates HTML + wkhtmltopdf |

## Modules compagnons

Cette application est le module principal de la suite. Les modules suivants partagent la même base de données :

| Module | Description |
|--------|-------------|
| [gestion_stocks_app_PostGres](https://github.com/RHergot/gestion_stocks_app_PostGres) | Gestion des stocks et pièces détachées |
| [Purchasing_Desk](https://github.com/RHergot/Purchasing_Desk) | Gestion des achats et appels d'offres |
| [meta_portail](https://github.com/RHergot/meta_portail) | Lanceur/portail (optionnel) |

## Structure

```
app/
├── core/           # Modèles métier, logique, services
├── data/           # Connexion DB, repositories, schémas
├── kpi/            # Module KPI (modèles, services, UI)
├── ui/             # Interface utilisateur (vues, dialogues, widgets)
├── utils/          # Helpers, i18n, PDF, exceptions
└── main.py         # Point d'entrée
```

## Prérequis

- Python ≥ 3.10
- PostgreSQL
- Paquets système : `wkhtmltopdf`

## Installation

```bash
pip install -r requirements.txt
python scripts/init_db.py
python app/main.py
```

## Licence

MIT — voir [LICENSE](LICENSE)
