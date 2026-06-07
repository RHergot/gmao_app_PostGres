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
