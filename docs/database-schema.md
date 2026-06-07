# Schéma de la base de données GMAO

La base PostgreSQL `gmao_industrie_data` est partagée par tous les modules de la suite.

## Vue d'ensemble par domaine

### 🏭 Parc machines
| Table | Description |
|-------|-------------|
| `machine` | Fiche machine (n° série, site, type, date mise en service) |
| `type_machine` | Types/catégories de machines |
| `compteur` | Compteurs associés aux machines (heures, cycles…) |
| `historique_compteur` | Relevés historiques des compteurs |
| `site` | Sites/établissements |
| `fabricant` | Fabricants de machines |

### 🔧 Maintenance
| Table | Description |
|-------|-------------|
| `gamme_entretien` | Gammes de maintenance préventive |
| `gamme_etape` | Étapes d'une gamme |
| `gamme_piece_type` | Pièces associées aux étapes |
| `ordre_travail` | Ordres de travail (OT) |
| `maintenance` | Interventions de maintenance réalisées |
| `maintenance_frais_externe` | Frais externes liés à une maintenance |
| `maintenance_intervenant` | Intervenants sur une maintenance |
| `intervention_piece` | Pièces consommées lors d'une intervention |

### 👥 Ressources humaines
| Table | Description |
|-------|-------------|
| `utilisateur` / `inventory_users` | Utilisateurs de l'application |
| `technicien` | Techniciens de maintenance |
| `equipe` | Équipes de techniciens |

### 📦 Stocks & Pièces
| Table | Description |
|-------|-------------|
| `piece` | Catalogue des pièces détachées |
| `piece_category` | Catégories de pièces |
| `piece_unit` | Unités de mesure |
| `piece_statut` | Statuts des pièces |
| `piece_extension` | Informations étendues |
| `piece_fournisseur_info` | Infos fournisseur par pièce |
| `emplacement` | Emplacements de stockage |
| `emplacement_ext` | Extensions d'emplacement |
| `emplacement_stock` | Stock par emplacement |
| `stock_level` | Niveaux de stock |
| `stock_piece_extra` | Données de stock supplémentaires |
| `mouvement_stock` | Mouvements de stock (entrées/sorties) |
| `type_mouvement` | Types de mouvements |
| `lot_reception` | Lots de réception |
| `lot_serie` | Lots et numéros de série |
| `reception_detail` | Détail des réceptions |
| `mise_en_stock_detail` | Détail de mise en stock |
| `inventory_warehouse` | Entrepôts |

### 🛒 Achats
| Table | Description |
|-------|-------------|
| `commande` | Commandes fournisseur |
| `ligne_commande` | Lignes de commande |
| `fournisseur` | Fournisseurs |
| `appel_offre` | Appels d'offres |
| `ao_fournisseur_consulte` | Fournisseurs consultés par AO |
| `offre_recue` | Offres reçues |
| `offre_recue_ligne` | Lignes d'offre |
| `contrat_achat` | Contrats d'achat |
| `demandes_achat` | Demandes d'achat (PR) |
| `demandes_achat_lignes` | Lignes de demandes d'achat |
| `prestation_achat` | Prestations achetées |
| `purchased_items` | Articles achetés |
| `orders` | Commandes (table alternative) |

### 📊 Vues (KPI & rapports)
| Vue | Description |
|-----|-------------|
| `v_kpi_machine_mensuel` | KPI mensuels par machine |
| `v_kpi_type_machine_mensuel` | KPI mensuels par type de machine |
| `v_kpi_site_mensuel` | KPI mensuels par site |
| `v_kpi_equipe_mensuel` | KPI mensuels par équipe |
| `v_kpi_preventif_curatif` | Ratio préventif/curatif |
| `v_maintenance_couts_detaille` | Coûts détaillés de maintenance |
| `v_top_machines_couteuses` | Top machines les plus coûteuses |
| `v_stock_par_emplacement` | Stock par emplacement |
| `v_mouvements_en_attente` | Mouvements en attente |
| `v_historique_mouvements` | Historique des mouvements |
| `v_dashboard_reception` | Tableau de bord réception |
| `v_emplacement_detail` | Détail des emplacements |
| `v_emplacement_capacite` | Capacité des emplacements |

## Fichiers SQL de référence

| Fichier | Contenu |
|---------|---------|
| `gestion_stocks_app_PostGres/database/database_complete_consolidated.sql` | Schéma complet avec toutes les tables |
| `gestion_stocks_app_PostGres/database/mon_schema_complet.sql` | Schéma alternatif |
| `Purchasing_Desk/setup_tables.sql` | Tables achats (AO, offres) |

## Notes

- Les tables `auth_*` et `django_*` proviennent d'une migration partielle vers Django — elles ne sont pas utilisées par la version PySide6.
- Tous les modules partagent la même base : les tables `commande`, `fournisseur`, `piece`, `emplacement` sont utilisées à la fois par l'app principale, le module stocks et le module achats.
